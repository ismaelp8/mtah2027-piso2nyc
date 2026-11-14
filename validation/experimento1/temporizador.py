"""Experimento 1: la regla del "temporizador" (hipótesis de Antonio, 13/11) medida en la DFL.

Hipótesis (lectura 2 de la sección 3 del resultado): la posesión pasa al equipo que toca el balón con
intención, salvo que el equipo que la tenía lo vuelva a tocar antes de N frames. Sobre el flag de la DFL,
que cambia en cada toque, eso es quitar las rachas X → y → X de menos de N frames. La intención no se ve
en el tracking: aquí no se modela.

Fijado antes de ejecutar (14/11):

- **Duraciones:** histograma frame a frame (1–25) de las rachas X → y → X del flag, para ver si la DFL
  sugiere un N natural (un valle entre los toques que se recuperan enseguida y las posesiones de verdad).
- **Peso:** con N = 5, 8, 10, 12, 15, 20 y 25 frames, y el cambio fechado en el toque: posesiones,
  posesiones por minuto vivo, cambios H↔A y frames vivos que cambian de equipo.
- **Referencias humanas,** las mismas de `comparar_definiciones.py`: pases completados, recuperaciones y
  duelos con `PossessionChange` true/false a 2 s. Para el flag, para cada N y, como comparación, para la
  corrección de control "C0-12 o dos toques".
- Descriptivo: no elige N ni lectura. El N, si se adopta esta regla, se fijará con un protocolo escrito
  antes, con datos abiertos, nunca con la ventana pública.

Datos abiertos de otros partidos (Bassek et al., 2025). Solo imprime agregados.

Uso:
    python validation/experimento1/temporizador.py
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
from comparar_definiciones import cerca_del_balon, eventos_guardia  # noqa: E402
from duelos_dfl import duelos  # noqa: E402
from duelos_sincronizados import MAX_DIST, posiciones_por_persona, sincronizar  # noqa: E402
from parada3 import a_frame  # noqa: E402
from peso_correccion import RESULTADOS_TOQUE, controles_parte  # noqa: E402

FPS = 25
NS = (5, 8, 10, 12, 15, 20, 25)
VENTANA = 3 * FPS


def quitar_cortas(lab, n):
    """Quita las rachas X → y → X de menos de n frames (pasan a X). Se recorre en orden."""
    lab = np.asarray(lab).copy()
    runs = mc.rachas(lab, 1)
    for i in range(1, len(runs) - 1):
        a, b, v = runs[i]
        prev_v, sig_v = lab[runs[i - 1][1] - 1], runs[i + 1][2]
        if v != 2 and prev_v != 2 and sig_v == prev_v and prev_v != v and b - a < n:
            lab[a:b] = prev_v
    return lab


def perfil(lab):
    runs = mc.rachas(lab, 1)
    pos = sum(1 for a, b, v in runs if v != 2)
    cambios = sum(1 for i in range(1, len(runs)) if runs[i][2] != 2 and runs[i - 1][2] != 2)
    cortas = sum(1 for a, b, v in runs if v != 2 and b - a < 3 * FPS)
    return pos, cambios, cortas


def main():
    hist = collections.Counter()
    junto_a_d = 0
    tot = collections.defaultdict(collections.Counter)
    aciertos = collections.defaultdict(lambda: collections.defaultdict(list))
    minutos = 0.0
    for p in etiquetas_dfl.PARTIDOS:
        datos = dfl_lector.cargar_cache(p)
        meta = datos["meta"]
        partes = {}
        for k in (1, 2):
            parte = datos["partes"][k]
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            lab = np.where(estado == 1, poss - 1, 2).astype(int)
            minutos += float(np.sum(estado == 1)) / FPS / 60
            runs = mc.rachas(lab, 1)
            for i in range(1, len(runs) - 1):
                a, b, v = runs[i]
                if v == 2:
                    continue
                pv, sv = runs[i - 1][2], runs[i + 1][2]
                if pv != 2 and pv == sv and b - a <= 25:
                    hist[b - a] += 1
                elif (pv == 2 or sv == 2) and b - a <= 25:
                    junto_a_d += 1
            labs = {"flag tal cual": lab}
            for n in NS:
                labs["N={}".format(n)] = quitar_cortas(lab, n)
            labs["C0-12 o dos toques"] = cr.corregir(lab, controles_parte(parte)["C0-12 o dos toques"])
            for d, l2 in labs.items():
                pos, cam, cortas = perfil(l2)
                tot[d]["posesiones"] += pos
                tot[d]["cambios"] += cam
                tot[d]["menos_3s"] += cortas
                tot[d]["frames_cambiados"] += int(np.sum(l2 != lab))
            partes[k] = (parte, posiciones_por_persona(parte), labs)

        def buscar(ms):
            for v in partes.values():
                if v[0]["t_ms"][0] <= ms <= v[0]["t_ms"][-1]:
                    return v
            return None

        for ms, x, a in duelos(dfl_lector.rutas_partido(p)["eventos"], meta):
            if x < 0 or a.get("WinnerRole") != "withoutBallControl" or a.get("WinnerResult") not in RESULTADOS_TOQUE:
                continue
            v = buscar(ms)
            if v is None:
                continue
            parte, pos, labs = v
            f0 = a_frame(np.asarray(parte["t_ms"], np.int64), ms)
            f, dist = sincronizar(parte, pos, f0, a.get("Winner"), a.get("Loser"))
            if f is None or dist > MAX_DIST:
                continue
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            f3 = f + 2 * FPS
            if f - 10 < 0 or f3 >= len(estado) or estado[f - 10] != 1 or poss[f - 10] - 1 != x or estado[f3] != 1:
                continue
            pc = a.get("PossessionChange")
            for d, l2 in labs.items():
                ok = l2[f3] == (1 - x) if pc == "true" else l2[f3] == x
                aciertos[d]["duelo PC=" + str(pc)].append(bool(ok))
        pases, recs = eventos_guardia(dfl_lector.rutas_partido(p)["eventos"], meta)
        for ms, pasador, receptor, eq in pases:
            v = buscar(ms)
            if v is None:
                continue
            parte, pos, labs = v
            f0 = a_frame(np.asarray(parte["t_ms"], np.int64), ms)
            fp, dp = cerca_del_balon(parte, pos, pasador, f0 - VENTANA, f0 + VENTANA + 1)
            if fp is None or dp > 1.5:
                continue
            fr, dr = cerca_del_balon(parte, pos, receptor, fp + 1, fp + VENTANA + 1)
            if fr is None or dr > 1.5 or fr + 5 >= len(parte["estado"]) or parte["estado"][fr + 5] != 1:
                continue
            for d, l2 in labs.items():
                aciertos[d]["G-pase"].append(bool(l2[fr + 5] == eq))
        for ms, jugador, eq in recs:
            v = buscar(ms)
            if v is None:
                continue
            parte, pos, labs = v
            f0 = a_frame(np.asarray(parte["t_ms"], np.int64), ms)
            fj, dj = cerca_del_balon(parte, pos, jugador, f0 - VENTANA, f0 + VENTANA + 1)
            if fj is None or dj > 1.5 or fj + 12 >= len(parte["estado"]) or parte["estado"][fj + 12] != 1:
                continue
            for d, l2 in labs.items():
                aciertos[d]["G-recuperación"].append(bool(l2[fj + 12] == eq))
    salida = {
        "rachas_intercaladas_por_duracion_frames": {str(k): hist[k] for k in range(1, 26)},
        "cortas_junto_a_D_de_25_frames_o_menos": junto_a_d,
        "peso": {d: {"posesiones": t["posesiones"], "por_minuto_vivo": round(t["posesiones"] / minutos, 2),
                     "cambios_HA": t["cambios"],
                     "cambios_por_minuto_vivo": round(t["cambios"] / minutos, 2),
                     "posesiones_menos_3s_pct": round(100.0 * t["menos_3s"] / t["posesiones"], 1),
                     "frames_vivos_cambiados_pct": round(100.0 * t["frames_cambiados"] / (minutos * 60 * FPS), 2)}
                 for d, t in tot.items()},
        "referencias_pct": {d: {c: round(100.0 * float(np.mean(v)), 1) for c, v in sorted(r.items())}
                            for d, r in aciertos.items()},
        "referencias_n": {c: len(v) for c, v in aciertos["flag tal cual"].items()},
    }
    print(json.dumps(salida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
