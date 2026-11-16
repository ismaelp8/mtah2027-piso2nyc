"""Lo común de los scripts de B11 y B12 (docs/decisiones.md, 17/11, «B11 y B12, modelos de secuencia»).

Datos abiertos de otros partidos (DFL: Bassek et al., 2025, CC BY 4.0). Nada del partido.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "scripts"),
                 os.path.join(ROOT, "validation", "apuesta_b"), os.path.join(ROOT, "evaluation")):
    if _carpeta not in sys.path:
        sys.path.insert(0, _carpeta)

from pathlib import Path  # noqa: E402

PARTIDOS = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")  # = dfl.PARTIDOS
CONDICIONES = ("como el ATD", "como el ATD, sin bloques")  # = dfl.VOTAN
PLIEGUES = ("todos",) + PARTIDOS
SEMILLA = 20261117
ALFAS = (1 / 16, 1 / 8, 1 / 4, 1 / 2, 1.0, 2.0, 4.0, 8.0)
# Lo que se fijó antes de medir para cada modelo.
B11 = {"canales": 24, "pasos": 1500, "tasa": 1e-3, "trozo": 1536, "lote": 16, "margen": 128}
B12 = {"oculto": 16, "pasos": 250, "tasa": 3e-3}
DECAIMIENTO = 1e-4


def carpeta_cache():
    """Donde se guardan los canales y los pesos de cada pliegue: junto a los datos abiertos, fuera del repo."""
    base = Path(os.environ.get("MTAH_OPEN_DATA_DIR") or (Path.home() / "mtah2027-datos-abiertos"))
    return base / "secuencia_cache"


def fichero_canales(partido, condicion):
    return carpeta_cache() / "canales_{}_{}.npz".format(partido, CONDICIONES.index(condicion))


def fichero_pesos(modelo, pliegue):
    return carpeta_cache() / "pesos" / "{}_{}.npz".format(modelo, pliegue)


def indice_pliegue(pliegue):
    return PLIEGUES.index(pliegue)
