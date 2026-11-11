"""Experimento 1: los dos fallos de cada corrección R(c), medidos con eventos anotados de la DFL.

Medidas fijadas en `validation/experimento1/BITACORA.md` (sección 7) antes de calcularlas:

- fallo de no quitar: duelos ganados por Y con toque, recuperación o `layoff`, con `PossessionChange` =
  false, que siguen en Y 2 s después;
- fallo de quitar posesiones reales: pases completados cuya etiqueta 5 frames después de la recepción
  no es del equipo del pasador (G-pase), y recuperaciones cuya etiqueta 0,5 s después no es del equipo
  que recupera (G-recuperación);
- diferencias entre definiciones con bootstrap emparejado (1.000 remuestreos, semilla 20261112).

Datos abiertos de otros partidos (Bassek et al., 2025). Solo imprime agregados.

Uso:
    python validation/experimento1/comparar_definiciones.py
"""

import collections
import json
import os
import sys

import numpy as np
from lxml import etree

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
sys.path.insert(0, AQUI)
import correccion as cr  # noqa: E402
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
from duelos_dfl import duelos  # noqa: E402
from duelos_sincronizados import posiciones_por_persona, sincronizar, MAX_DIST  # noqa: E402
from parada3 import a_frame, _ms  # noqa: E402
from peso_correccion import DEFINICIONES, RESULTADOS_TOQUE, controles_parte  # noqa: E402

FPS = 25
VENTANA = 3 * FPS
SEMILLA = 20261112


def cerca_del_balon(parte, pos, pid, lo, hi):
    """Frame activo de [lo, hi) en que el jugador está más cerca del balón, y esa distancia."""
    if pid not in pos:
        return None, None
    n = len(parte["estado"])
    lo, hi = max(0, lo), min(n, hi)
    if hi <= lo:
        return None, None
    d = np.hypot(pos[pid][0][lo:hi] - np.asarray(parte["x"][lo:hi], float),
                 pos[pid][1][lo:hi] - np.asarray(parte["y"][lo:hi], float))
    d = np.where(np.isnan(d) | (np.asarray(parte["estado"][lo:hi]) != 1), np.inf, d)
    i = int(np.argmin(d))
    return (lo + i, float(d[i])) if np.isfinite(d[i]) else (None, None)


def eventos_guardia(ruta, meta):
    """Pases completados (pasador, receptor, equipo) y recuperaciones (jugador, equipo), con su hora."""
    eq = {meta["local_id"]: 0, meta["visitante_id"]: 1}
    pases, recuperaciones = [], []
    for e in etree.parse(ruta).getroot().findall("Event"):
        if not len(e) or e.get("EventTime") is None:
            continue
        h = e[0]
        if h.tag == "Play" and h.get("Evaluation") == "successfullyCompleted" and h.get("Recipient") \
                and h.get("Team") in eq:
            pases.append((_ms(e.get("EventTime")), h.get("Player"), h.get("Recipient"), eq[h.get("Team")]))
        elif h.tag == "BallClaiming" and h.get("Team") in eq and h.get("Player"):
            recuperaciones.append((_ms(e.get("EventTime")), h.get("Player"), eq[h.get("Team")]))
    return pases, recuperaciones


def bootstrap_dif(a, b, rng, veces=1000):
    """Intervalo del 95 % de la diferencia de medias de dos vectores emparejados de aciertos (0/1)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    idx = rng.integers(0, len(a), size=(veces, len(a)))
    d = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    return [round(100 * float(np.percentile(d, 2.5)), 1), round(100 * float(np.percentile(d, 97.5)), 1)]


def main():
    aciertos = {d: collections.defaultdict(list) for d in DEFINICIONES}
    cuenta = collections.Counter()
    en_el_pase = {d: [] for d in DEFINICIONES}
    for p in etiquetas_dfl.PARTIDOS:
        datos = dfl_lector.cargar_cache(p)
        meta = datos["meta"]
        partes = {}
        for k in (1, 2):
            parte = datos["partes"][k]
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            lab = np.where(estado == 1, poss - 1, 2).astype(int)
            ctrl = controles_parte(parte)
            labs = {"flag tal cual": lab}
            for d in DEFINICIONES[1:]:
                labs[d] = cr.corregir(lab, ctrl[d])
            partes[k] = (parte, posiciones_por_persona(parte), labs)

        def buscar(ms):
            for k, v in partes.items():
                if v[0]["t_ms"][0] <= ms <= v[0]["t_ms"][-1]:
                    return v
            return None

        # fallo de no quitar: duelos con PossessionChange = false
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
            clave = "duelo PC=" + str(a.get("PossessionChange"))
            cuenta[clave] += 1
            for d in DEFINICIONES:
                ok = labs[d][f3] == (1 - x) if a.get("PossessionChange") == "true" else labs[d][f3] == x
                aciertos[d][clave].append(bool(ok))
        # fallo de quitar: pases completados y recuperaciones
        pases, recs = eventos_guardia(dfl_lector.rutas_partido(p)["eventos"], meta)
        for ms, pasador, receptor, eq in pases:
            v = buscar(ms)
            if v is None:
                cuenta["pase fuera de las partes"] += 1
                continue
            parte, pos, labs = v
            f0 = a_frame(np.asarray(parte["t_ms"], np.int64), ms)
            fp, dp = cerca_del_balon(parte, pos, pasador, f0 - VENTANA, f0 + VENTANA + 1)
            if fp is None or dp > 1.5:
                cuenta["pase sin situar"] += 1
                continue
            fr, dr = cerca_del_balon(parte, pos, receptor, fp + 1, fp + VENTANA + 1)
            if fr is None or dr > 1.5 or fr + 5 >= len(parte["estado"]) or parte["estado"][fr + 5] != 1:
                cuenta["recepción sin situar"] += 1
                continue
            cuenta["G-pase"] += 1
            for d in DEFINICIONES:
                aciertos[d]["G-pase"].append(bool(labs[d][fr + 5] == eq))
                en_el_pase[d].append(bool(labs[d][fp] == eq))
        for ms, jugador, eq in recs:
            v = buscar(ms)
            if v is None:
                continue
            parte, pos, labs = v
            f0 = a_frame(np.asarray(parte["t_ms"], np.int64), ms)
            fj, dj = cerca_del_balon(parte, pos, jugador, f0 - VENTANA, f0 + VENTANA + 1)
            if fj is None or dj > 1.5 or fj + 12 >= len(parte["estado"]) or parte["estado"][fj + 12] != 1:
                cuenta["recuperación sin situar"] += 1
                continue
            cuenta["G-recuperación"] += 1
            for d in DEFINICIONES:
                aciertos[d]["G-recuperación"].append(bool(labs[d][fj + 12] == eq))
    rng = np.random.default_rng(SEMILLA)
    salida = {"recuento": dict(cuenta), "acierto_pct": {}, "en_el_frame_del_pase_pct": {},
              "diferencias_con_C0-12_IC95": {}}
    for d in DEFINICIONES:
        salida["acierto_pct"][d] = {c: round(100.0 * float(np.mean(v)), 1) for c, v in sorted(aciertos[d].items())}
        salida["en_el_frame_del_pase_pct"][d] = round(100.0 * float(np.mean(en_el_pase[d])), 1)
    ref = "C0-12"
    for d in DEFINICIONES:
        if d == ref:
            continue
        salida["diferencias_con_C0-12_IC95"][d] = {c: bootstrap_dif(aciertos[d][c], aciertos[ref][c], rng)
                                                   for c in sorted(aciertos[d])}
    print(json.dumps(salida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
