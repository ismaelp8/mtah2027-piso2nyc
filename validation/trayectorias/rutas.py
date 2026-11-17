"""Dónde guardan los scripts de B13 los rasgos de la DFL: junto a los datos abiertos, fuera del repo.

Sin dependencias del harness, para que el entorno de torch (sin lxml) pueda leerlos.
"""

import os
from pathlib import Path

CONDICIONES = ("como el ATD", "como el ATD, sin bloques")  # = dfl.VOTAN


def carpeta():
    base = Path(os.environ.get("MTAH_OPEN_DATA_DIR") or (Path.home() / "mtah2027-datos-abiertos"))
    return base / "trayectorias_cache"


def fichero(partido, condicion):
    return carpeta() / "rasgos_{}_{}.npz".format(partido, CONDICIONES.index(condicion))
