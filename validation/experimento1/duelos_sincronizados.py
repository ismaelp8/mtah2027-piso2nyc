"""Experimento 1: duelos de los eventos DFL situados en su frame exacto con el tracking, frente al flag.

Medida afinada fijada en `validation/experimento1/BITACORA.md` (sección 3): cada `TacklingGame` se
sitúa, en ±3 s de su hora, en el frame activo en que el más lejano de sus dos jugadores (`Winner` y
`Loser`, por `PersonId`) está más cerca del balón. Después se mira el flag `BallPossession` alrededor.
Datos abiertos de otros partidos (Bassek et al., 2025). Solo imprime agregados.

Uso:
    python validation/experimento1/duelos_sincronizados.py
"""

import collections
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
sys.path.insert(0, AQUI)
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
from duelos_dfl import duelos  # noqa: E402
from parada3 import a_frame  # noqa: E402

FPS = 25
VENTANA = 3 * FPS
MAX_DIST = 3.0


def posiciones_por_persona(parte):
    """{PersonId: (x, y)} con las columnas de cada jugador en la parte."""
    salida = {}
    for eq in ("local", "visitante"):
        d = parte["equipos"][eq]
        for c, pid in enumerate(d["personas"]):
            salida[str(pid)] = (np.asarray(d["x"][:, c], float), np.asarray(d["y"][:, c], float))
    return salida


def sincronizar(parte, pos, f0, ganador, perdedor):
    """Frame del duelo y distancia del jugador más lejano al balón en ese frame (o None)."""
    if ganador not in pos or perdedor not in pos:
        return None, None
    n = len(parte["estado"])
    lo, hi = max(0, f0 - VENTANA), min(n, f0 + VENTANA + 1)
    bx, by = np.asarray(parte["x"][lo:hi], float), np.asarray(parte["y"][lo:hi], float)
    dw = np.hypot(pos[ganador][0][lo:hi] - bx, pos[ganador][1][lo:hi] - by)
    dl = np.hypot(pos[perdedor][0][lo:hi] - bx, pos[perdedor][1][lo:hi] - by)
    peor = np.fmax(dw, dl)
    peor = np.where(np.isnan(peor) | (np.asarray(parte["estado"][lo:hi]) != 1), np.inf, peor)
    i = int(np.argmin(peor))
    return (lo + i, float(peor[i])) if np.isfinite(peor[i]) else (None, None)


def grupo(a, gana_y):
    lado = "Y" if gana_y else "X"
    return "gana {} · {}".format(lado, a.get("WinnerResult"))


def main():
    m2 = collections.defaultdict(list)
    m3 = collections.defaultdict(list)
    cuenta = collections.Counter()
    dist_sync = []
    for p in etiquetas_dfl.PARTIDOS:
        datos = dfl_lector.cargar_cache(p)
        meta = datos["meta"]
        partes = {k: (datos["partes"][k], posiciones_por_persona(datos["partes"][k])) for k in (1, 2)}
        for ms, x, a in duelos(dfl_lector.rutas_partido(p)["eventos"], meta):
            if x < 0:
                cuenta["sin equipo con el balón"] += 1
                continue
            sel = [(parte, pos) for parte, pos in partes.values() if parte["t_ms"][0] <= ms <= parte["t_ms"][-1]]
            if not sel:
                cuenta["fuera de las partes"] += 1
                continue
            parte, pos = sel[0]
            f0 = a_frame(np.asarray(parte["t_ms"], np.int64), ms)
            f, d = sincronizar(parte, pos, f0, a.get("Winner"), a.get("Loser"))
            if f is None or d > MAX_DIST:
                cuenta["no sincronizado (> 3 m o sin posiciones)"] += 1
                continue
            dist_sync.append(d)
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            y = 1 - x
            if f - 10 < 0 or estado[f - 10] != 1 or poss[f - 10] - 1 != x:
                cuenta["flag no está en X 10 frames antes"] += 1
                continue
            cuenta["medidos"] += 1
            lo, hi = f - 5, min(len(estado), f + 26)
            marca = bool(np.any((estado[lo:hi] == 1) & (poss[lo:hi] - 1 == y)))
            f3 = min(len(estado) - 1, f + 2 * FPS)
            tras = None if estado[f3] != 1 else bool(poss[f3] - 1 == y)
            gana_y = a.get("WinnerRole") == "withoutBallControl"
            g = grupo(a, gana_y)
            for c in (g, g + " · PossessionChange=" + str(a.get("PossessionChange"))):
                m2[c].append(marca)
                if tras is not None:
                    m3[c].append(tras)
    print("Recuento:", dict(cuenta))
    print("Distancia del jugador más lejano al balón en el frame sincronizado (m), p10/p50/p90:",
          [round(float(v), 2) for v in np.percentile(dist_sync, [10, 50, 90])])
    filas = {}
    for c in sorted(m2, key=lambda k: (k.split(" · ")[0], k)):
        v, w = m2[c], m3.get(c, [])
        filas[c] = {"n": len(v), "M2_flag_en_Y_hasta_1s_pct": round(100.0 * sum(v) / len(v), 1),
                    "M3_flag_en_Y_a_2s_pct": round(100.0 * sum(w) / len(w), 1) if w else None}
    print(json.dumps(filas, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
