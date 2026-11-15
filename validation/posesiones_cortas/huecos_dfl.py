"""Referencia de la DFL para `validation/partido/huecos_y_cambios.py`: dónde caen nuestros cambios respecto a los
huecos del balón, con los huecos puestos al azar. Solo agregados.

    python validation/posesiones_cortas/huecos_dfl.py

DFL (Bassek et al., 2025, CC BY 4.0): lo puede ejecutar cualquiera, Claude incluido. `main` (B5 con el pliegue que
no vio cada partido) **con nuestro `D`** (sin oráculo), con el balón «como el ATD», igual que en el partido.
En la DFL los huecos del balón caen al azar respecto a los cambios (`dfl.mascara_como_el_atd`), salvo los que
tapan los `D` y sus bordes. Regla de lectura en `validation/posesiones_cortas/BITACORA.md` §14.
"""

import functools
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import huecos  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, ball, pipeline  # noqa: E402

CONDICION = "como el ATD"


def referencia_dfl(avisar=None):
    """Los recuentos de `huecos.medir` en los 7 partidos de la DFL, con nuestro `D`."""
    acc = huecos.nuevo()
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        trk = puntuar.solo_lectura(dfl.tracking_de(cargado, CONDICION))
        pred = pipeline.run(trk, pieces={"candidates": functools.partial(aprendida.evidence_b5, fuera=partido)})
        huecos.medir(pred, aprendida.balon_visible(ball.clean(trk)), trk.blocks, acc)
        if avisar:
            avisar("hecho {}".format(partido))
    return acc


def main():
    acc = referencia_dfl(lambda t: print(t, file=sys.stderr, flush=True))
    print("# Referencia de la DFL: nuestros cambios y los huecos del balón (`main` con nuestro `D`, «{}»)\n".format(
        CONDICION))
    print("\n".join(huecos.lineas("DFL, 7 partidos (huecos al azar)", acc, suprimir=False)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
