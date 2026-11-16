"""Sondeo S8: ¿fecha la geometría del saque (banda, córner) el final de la parada mejor que la pieza de estado?

    python validation/investigacion_1116/fin_por_geometria.py

DFL (7 partidos abiertos, Bassek et al., 2025, CC BY 4.0), «como el ATD», `main` con su `D` propio. Solo jugadores:
el balón no se usa. Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. La regla de lectura está
en BITACORA.md (S8), escrita antes de medir.
"""

import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (os.path.join(ROOT, "validation", "harness"), ROOT, os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, carpeta)
import dfl  # noqa: E402
import puntuar  # noqa: E402

H, A, D, X = dfl.H, dfl.A, dfl.D, dfl.X
VERSIONES = os.path.join(ROOT, "validation", "harness", "versiones", "investigacion_costes_2026-11-16.json")
ANTES, DESPUES = 125, 50  # frames: la ventana [Ê − 5 s, Ê + 2 s]
MIN_PARADA = 50


def rachas(m):
    b = np.diff(np.concatenate(([0], m.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(b == 1), np.flatnonzero(b == -1)))


def main():
    version = puntuar.leer_versiones(VERSIONES)[0]["main: B5 y coste 25"]
    errores = collections.defaultdict(list)  # tipo -> [(error Ê, error ancla)]
    total = collections.Counter()
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]["flag"]
        trk = puntuar.solo_lectura(dfl.tracking_de(cargado, "como el ATD"))
        pred = puntuar.ejecutar(version, trk, gt, "propio", partido)
        largo, ancho = trk.pitch
        px, py = np.asarray(trk.px, dtype=np.float64), np.asarray(trk.py, dtype=np.float64)
        with np.errstate(invalid="ignore"):
            fuera_y = np.maximum(-py, py - ancho)
            banda = np.any((fuera_y > 0.5) & (fuera_y < 5) & (px > 0) & (px < largo), axis=1)
            esquinas = [(0, 0), (0, ancho), (largo, 0), (largo, ancho)]
            corner = np.zeros(len(px), bool)
            for ex, ey in esquinas:
                corner |= np.any(np.hypot(px - ex, py - ey) < 2.5, axis=1)
        for a, b in trk.blocks:
            g, p = gt[a:b], pred[a:b]
            nuestras = rachas(p == D)
            for i, j in rachas(g == D):
                if j - i < MIN_PARADA or i == 0 or j >= b - a:
                    continue
                total["reales"] += 1
                toca = [(u, v) for u, v in nuestras if u < j and v > i]
                if not toca:
                    continue
                total["detectadas"] += 1
                fin = max(v for _, v in toca)
                lo, hi = max(0, fin - ANTES), min(b - a, fin + DESPUES)
                if banda[a + lo:a + hi].any():
                    tipo, marca = "banda", banda[a + lo:a + hi]
                elif corner[a + lo:a + hi].any():
                    tipo, marca = "córner", corner[a + lo:a + hi]
                else:
                    tipo, marca = "otro", None
                ancla = None if marca is None else lo + int(np.flatnonzero(marca)[-1]) + 1
                errores[tipo].append((fin - j, None if ancla is None else ancla - j))
    print("Paradas reales de 2 s o más: {} · detectadas por `main` con su `D` propio: {}\n".format(
        total["reales"], total["detectadas"]))
    print("| tipo (por geometría) | paradas | Ê: mediana del error | Ê a ±12 / ±25 | ancla: mediana del error | ancla a ±12 / ±25 |")
    print("|---|---|---|---|---|---|")
    grupos = [("banda", ["banda"]), ("córner", ["córner"]), ("banda y córner", ["banda", "córner"]), ("otro", ["otro"])]
    for nombre, tipos in grupos:
        filas = [e for t in tipos for e in errores[t]]
        if not filas:
            continue
        e_hat = np.array([f[0] for f in filas], dtype=float)
        celdas = [nombre, str(len(filas)), "{:+.0f}".format(np.median(e_hat)),
                  "{:.0f} % / {:.0f} %".format(100 * np.mean(np.abs(e_hat) <= 12), 100 * np.mean(np.abs(e_hat) <= 25))]
        anclas = np.array([f[1] for f in filas if f[1] is not None], dtype=float)
        if len(anclas):
            celdas += ["{:+.0f}".format(np.median(anclas)), "{:.0f} % / {:.0f} %".format(
                100 * np.mean(np.abs(anclas) <= 12), 100 * np.mean(np.abs(anclas) <= 25))]
        else:
            celdas += ["–", "–"]
        print("| " + " | ".join(celdas) + " |")


if __name__ == "__main__":
    main()
