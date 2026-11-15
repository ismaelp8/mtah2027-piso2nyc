"""Sondeo S10: ¿está el balón de Metrica sample-data pegado al jugador más cercano? Frente a la DFL limpia.

    python validation/investigacion_1116/balon_metrica.py

Datos abiertos de otros partidos. Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. La regla
está en BITACORA.md (S10), escrita antes de medir.
"""

import os
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for carpeta in (AQUI.parent / "metrica", AQUI.parent / "harness", ROOT):
    sys.path.insert(0, str(carpeta))
import dfl  # noqa: E402
import lector as lm  # noqa: E402

H, A = dfl.H, dfl.A


def distancias(trk, gt):
    bx, by = np.asarray(trk.bx, dtype=float), np.asarray(trk.by, dtype=float)
    vivo = ((gt == H) | (gt == A)) & np.isfinite(bx) & np.isfinite(by)
    idx = np.flatnonzero(vivo)
    d = np.hypot(np.asarray(trk.px[idx], dtype=float) - bx[idx, None], np.asarray(trk.py[idx], dtype=float) - by[idx, None])
    return np.nanmin(np.where(np.isfinite(d), d, np.inf), axis=1)


def resumen(nombre, d):
    d = d[np.isfinite(d)]
    print("| {} | {} | {:.2f} m | {:.1f} % | {:.1f} % | {:.1f} % |".format(
        nombre, len(d), np.median(d), 100 * np.mean(d < 0.3), 100 * np.mean(d < 1.0), 100 * np.mean(d < 2.0)))


def main():
    print("| datos | frames de juego con balón | mediana al más cercano | a < 0,3 m | a < 1 m | a < 2 m |")
    print("|---|---|---|---|---|---|")
    todas = []
    for id_ in lm.partidos():
        trk, gt = lm.tracking_de(lm.leer(id_), "tal cual", id_)
        d = distancias(trk, gt)
        todas.append(d)
        resumen("Metrica, partido {}".format(id_), d)
    resumen("Metrica, los 3", np.concatenate(todas))
    todas = []
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        todas.append(distancias(dfl.tracking_de(cargado, "limpio"), cargado["gt"]["flag"]))
    resumen("DFL limpia, los 7", np.concatenate(todas))


if __name__ == "__main__":
    main()
