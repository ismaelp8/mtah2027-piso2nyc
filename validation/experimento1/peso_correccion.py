"""Experimento 1: cuánto cambian las etiquetas de la DFL al corregirlas con cada definición de control.

Aplica la corrección R(c) de `correccion.py` (fijada en la bitácora, sección 5) con varias definiciones
de control y da, por partido y con los 7 juntos, posesiones, cambios y frames que cambian, y el acuerdo
con los duelos anotados de los eventos (`PossessionChange`). Descriptivo: no elige nada. Datos abiertos
de otros partidos (Bassek et al., 2025). Solo imprime agregados.

Uso:
    python validation/experimento1/peso_correccion.py
"""

import collections
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
sys.path.insert(0, AQUI)
import correccion as cr  # noqa: E402
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
import medidas_cambios as mc  # noqa: E402
from duelos_dfl import duelos  # noqa: E402
from duelos_sincronizados import posiciones_por_persona, sincronizar, MAX_DIST  # noqa: E402
from parada3 import a_frame  # noqa: E402

FPS = 25
DEFINICIONES = ("flag tal cual", "C0-8", "C0-12", "C0-20", "C0-50", "Ret-5", "dos toques", "C0-12 o dos toques")
RESULTADOS_TOQUE = ("ballcontactSucceeded", "ballClaimed", "layoff")


def controles_parte(parte):
    """{definición: intervalos por equipo} con los frames D tapados (variante solo en juego)."""
    estado = np.asarray(parte["estado"])
    prep = dict(mc.preparar(parte))
    activo = estado == 1
    prep["d1"] = np.where(activo, prep["d1"], np.inf)
    prep["d_equipo"] = np.where(activo[None, :], prep["d_equipo"], np.inf)
    t, eq, _ = mc.toques(prep, 3.0, 1.5)
    t, eq = mc.toques_en_juego(t, eq, estado)
    c = {"C0-{}".format(k): cr.intervalos(mc.controles(prep, 1.0, k)) for k in (8, 12, 20, 50)}
    c["Ret-5"] = cr.intervalos(mc.retenciones(prep, 1.0, 5))
    c["dos toques"] = cr.intervalos(cr.dos_toques(t, eq))
    c["C0-12 o dos toques"] = cr.unir(c["C0-12"], c["dos toques"])
    return c


def perfil(lab, minutos):
    runs = mc.rachas(lab, 1)
    pos = [(a, b, v) for a, b, v in runs if v != 2]
    cambios = sum(1 for i in range(1, len(runs)) if runs[i][2] != 2 and runs[i - 1][2] != 2)
    return {"posesiones": len(pos), "cambios": cambios,
            "cortas_menos_1s": sum(1 for a, b, v in pos if b - a < FPS)}


def main():
    total = collections.defaultdict(collections.Counter)
    por_partido = {}
    acuerdo = collections.defaultdict(lambda: collections.defaultdict(list))
    quitadas = collections.defaultdict(list)
    for p in etiquetas_dfl.PARTIDOS:
        datos = dfl_lector.cargar_cache(p)
        meta = datos["meta"]
        por_partido[p] = collections.defaultdict(collections.Counter)
        etiquetas = {}
        for k in (1, 2):
            parte = datos["partes"][k]
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            lab = np.where(estado == 1, poss - 1, 2).astype(int)
            minutos = float(np.sum(estado == 1)) / FPS / 60
            ctrl = controles_parte(parte)
            etiquetas[k] = {"flag tal cual": lab}
            for d in DEFINICIONES[1:]:
                etiquetas[k][d] = cr.corregir(lab, ctrl[d])
            for d, l2 in etiquetas[k].items():
                pf = perfil(l2, minutos)
                cambiados = int(np.sum(l2 != lab))
                for c, v in list(pf.items()) + [("frames_cambiados", cambiados)]:
                    por_partido[p][d][c] += v
                    total[d][c] += v
                por_partido[p][d]["minutos_vivos_x100"] += int(round(minutos * 100))
                total[d]["minutos_vivos_x100"] += int(round(minutos * 100))
                if d != "flag tal cual":
                    for a, b, v in mc.rachas(lab, 1):
                        if v != 2 and np.all(l2[a:b] != v):
                            quitadas[d].append((b - a) / FPS)
        # acuerdo con los duelos anotados
        partes = {k: (datos["partes"][k], posiciones_por_persona(datos["partes"][k])) for k in (1, 2)}
        for ms, x, a in duelos(dfl_lector.rutas_partido(p)["eventos"], meta):
            if x < 0 or a.get("WinnerRole") != "withoutBallControl" or a.get("WinnerResult") not in RESULTADOS_TOQUE:
                continue
            sel = [k for k, (parte, _) in partes.items() if parte["t_ms"][0] <= ms <= parte["t_ms"][-1]]
            if not sel:
                continue
            k = sel[0]
            parte, pos = partes[k]
            f0 = a_frame(np.asarray(parte["t_ms"], np.int64), ms)
            f, dist = sincronizar(parte, pos, f0, a.get("Winner"), a.get("Loser"))
            if f is None or dist > MAX_DIST:
                continue
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            f3 = f + 2 * FPS
            if f - 10 < 0 or f3 >= len(estado) or estado[f - 10] != 1 or poss[f - 10] - 1 != x or estado[f3] != 1:
                continue
            pc = a.get("PossessionChange")
            for d, l2 in etiquetas[k].items():
                acuerdo[d][pc].append(bool(l2[f3] == 1 - x))
    salida = {"los_7": {}, "por_partido": {}, "acuerdo_duelos": {}, "rachas_quitadas_s": {}}
    for d in DEFINICIONES:
        t = total[d]
        mins = t["minutos_vivos_x100"] / 100.0
        salida["los_7"][d] = {"posesiones": t["posesiones"], "por_minuto_vivo": round(t["posesiones"] / mins, 2),
                              "cambios_HA": t["cambios"], "cortas_menos_1s": t["cortas_menos_1s"],
                              "frames_cambiados_pct_vivo": round(100.0 * t["frames_cambiados"] / (mins * 60 * FPS), 2)}
        salida["por_partido"][d] = {p: por_partido[p][d]["posesiones"] for p in etiquetas_dfl.PARTIDOS}
        si, no = acuerdo[d]["true"], acuerdo[d]["false"]
        rec = 100.0 * sum(si) / len(si)
        esp = 100.0 * (len(no) - sum(no)) / len(no)
        salida["acuerdo_duelos"][d] = {"n_true": len(si), "n_false": len(no), "Y_a_2s_si_true_pct": round(rec, 1),
                                       "X_a_2s_si_false_pct": round(esp, 1), "acierto_equilibrado_pct": round((rec + esp) / 2, 1)}
        if quitadas[d]:
            salida["rachas_quitadas_s"][d] = {"n": len(quitadas[d]),
                                              "p10_p50_p90": [round(float(v), 2) for v in np.percentile(quitadas[d], [10, 50, 90])]}
    print(json.dumps(salida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
