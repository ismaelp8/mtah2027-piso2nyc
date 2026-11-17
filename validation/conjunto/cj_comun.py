"""Lo común del modelo conjunto (docs/decisiones.md, 17/11): partidos, pliegues, condiciones y rutas de la caché.

No se ejecuta solo y no importa torch ni las piezas del pipeline: lo usan `exportar.py` y `medir.py` (entorno del
equipo, solo numpy) y `entrenar.py` (entorno `mtah2027-conjunto`, con torch). Todo son datos abiertos de otros
partidos; la caché vive fuera del repo, junto a las otras (`<datos abiertos>/conjunto_cache`).
"""

import os
from pathlib import Path

DFL = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")  # = validation/harness/dfl.PARTIDOS
# = validation/skillcorner/lector.ENTRENAMIENTO. El examen (lector.EXAMEN) no aparece en este fichero a propósito.
SKILLCORNER = (1874553, 1899585, 1927964, 1959846, 1996435, 2006229, 2007448, 2010085, 2013725, 2016236)
CONDICIONES_DFL = ("como el ATD", "como el ATD, sin bloques")  # = dfl.VOTAN
CONDICIONES_SC = ("detectado", "detectado, suavizado")  # = lector.VOTAN
PLIEGUES = DFL + ("todos",)
PILOTO = "J03WMX"
SEMILLA = 20261117
GRUPO = 5  # frames por grupo: el modelo va a 5 Hz
SEMIANCHO = 12  # frames: la clase «cambio» (possession/cambios.SEMIANCHO)


def fuera_de(pliegue):
    """(partidos de la DFL, partidos de SkillCorner) que el pliegue no ve. El de todos no deja fuera ninguno."""
    if pliegue == "todos":
        return (), ()
    k = DFL.index(pliegue)
    return (pliegue,), tuple(SKILLCORNER[i] for i in (k, k + len(DFL)) if i < len(SKILLCORNER))


def pliegue_de(dominio, partido):
    """El pliegue que no vio el partido: con él se puntúa."""
    if dominio == "dfl":
        return partido
    return DFL[SKILLCORNER.index(int(partido)) % len(DFL)]


def carpeta():
    base = os.environ.get("MTAH_OPEN_DATA_DIR") or (Path.home() / "mtah2027-datos-abiertos")
    return Path(base) / "conjunto_cache"


def fichero_partido(dominio, partido):
    return carpeta() / "{}_{}.npz".format(dominio, partido)


def fichero_pesos(etiqueta, pliegue):
    return carpeta() / "pesos" / "{}_{}.pt".format(etiqueta, pliegue)


def fichero_salida(etiqueta, dominio, partido):
    """Las salidas del modelo (z y p a 25 Hz) de un partido, con el pliegue que dice el propio fichero."""
    return carpeta() / "salidas" / etiqueta / "{}_{}.npz".format(dominio, partido)
