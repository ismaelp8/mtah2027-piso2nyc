"""Guarda, para B15, la etiqueta de control de cada parte de la DFL junto a los paquetes de B14.

    python validation/trayectorias/etiquetas_control.py

B15 es B14 entrenada con la convención de control en todos los frames vivos (y = 1 si control dice `H`), en lugar de
solo en los frames donde el flag y control coinciden. Así aprende también que un toque breve del rival no es un cambio
(«exigir control», decisión del equipo del 12/11). Las etiquetas son las mismas en todas las copias y condiciones
(salen del tracking limpio). Datos abiertos de la DFL; fuera del repo. Solo imprime agregados.
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, AQUI, os.path.join(ROOT, "validation", "harness")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import paquetes  # noqa: E402
from possession.tracking import A, H  # noqa: E402


nombre = paquetes.nombre_control


def main():
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        control, flag = cargado["gt"]["control"], cargado["gt"]["flag"]
        trk = dfl.tracking_de(cargado, dfl.VOTAN[0])
        vivos = distintos = 0
        for k, (a, b) in enumerate(trk.blocks):
            c = control[a:b]
            m = np.isin(c, (H, A))
            np.save(nombre(partido, k, "y"), (c == H).astype(np.int8))
            np.save(nombre(partido, k, "m"), m)
            vivos += int(m.sum())
            distintos += int(np.sum(m & (flag[a:b] != c)))
        print("{}: {} frames vivos con control, {} ({:.1f} %) donde el flag dice otra cosa".format(
            partido, vivos, distintos, 100.0 * distintos / max(vivos, 1)), flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
