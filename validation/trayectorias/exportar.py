"""Calcula los rasgos de B13 (possession/trayectorias.py) en los 7 partidos de la DFL y los guarda para entrenar.

    python validation/trayectorias/exportar.py

Datos abiertos de otros partidos (DFL, CC BY 4.0), con la caché del harness. Lo puede ejecutar cualquiera, Claude
incluido. Solo imprime agregados. Usa el mismo código que la predicción (`trayectorias.rasgos_tramo`) sobre el
mismo tracking que el harness (`dfl.tracking_de` y la limpieza de `main`), en las dos condiciones que votan.

Guarda, fuera del repo, una entrada por partido, condición y parte: los rasgos a 5 Hz de las dos perspectivas (float32),
las máscaras de jugadores, y a 25 Hz la etiqueta (1 si el flag es `H`) y la máscara de la pérdida (frames vivos donde
el flag y control coinciden).
"""

import os
import sys
import time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness")):
    sys.path.insert(0, _carpeta)
sys.path.insert(0, AQUI)
import dfl  # noqa: E402
from possession import ball, trayectorias  # noqa: E402
from possession.tracking import A, H  # noqa: E402
from rutas import CONDICIONES, carpeta, fichero  # noqa: E402


def rutas_condiciones():
    return CONDICIONES


def main():
    if tuple(dfl.VOTAN) != rutas_condiciones():
        raise AssertionError("rutas.CONDICIONES no son las del harness")
    carpeta().mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        etiqueta = (gt["flag"] == H).astype(np.int8)
        mascara = (gt["flag"] == gt["control"]) & np.isin(gt["flag"], (H, A))
        for condicion in dfl.VOTAN:
            trk = ball.clean(dfl.tracking_de(cargado, condicion))
            guardar = {}
            for k, (a, b) in enumerate(trk.blocks):
                r, hay_h, hay_a = trayectorias.rasgos_tramo(trk, a, b)
                for persp, nombre in ((H, "H"), (A, "A")):
                    for j, parte in enumerate(("propios", "rivales", "balon")):
                        guardar["{}_{}_{}".format(k, nombre, parte)] = r[persp][j].astype(np.float32)
                guardar["{}_hay_h".format(k)] = hay_h
                guardar["{}_hay_a".format(k)] = hay_a
                guardar["{}_y".format(k)] = etiqueta[a:b]
                guardar["{}_m".format(k)] = mascara[a:b]
            np.savez_compressed(fichero(partido, condicion), **guardar)
            print("{} · {}: {} partes, {} slots ({} H, {} A), {} frames en la pérdida · {:.0f} s".format(
                partido, condicion, len(trk.blocks), len(trk.team), int((trk.team == H).sum()),
                int((trk.team == A).sum()), int(sum(mascara[a:b].sum() for a, b in trk.blocks)),
                time.time() - inicio), flush=True)


if __name__ == "__main__":
    main()
