"""Prueba la capa de los contraataques (`possession/transiciones.py`) con un Smart Tagging inventado.

    python validation/scripts/prueba_transiciones.py

Sin datos del partido: el tracking es inventado y el Smart Tagging se escribe en una carpeta temporal que se
borra. Sin `paths`, abrir cualquier fichero es un error (`sin_ficheros`). Lo puede ejecutar cualquiera, Claude
incluido. Prueba:
- que sin `paths` no opina y no abre nada;
- el peso, el tope de 5 s, el final de la fase y del tramo, las fases que empiezan fuera de los tramos, los
  solapes del mismo equipo y de equipos distintos, y que solo entran las ATTACKING TRANSITION con Team H o A;
- la interfaz (forma, columnas, `allowed`, que no toca `D`), el determinismo y el orden del fichero;
- que encaja con `--capa` del pipeline sin estar en `PIECES`.
"""

import builtins
import contextlib
import io
import os
import random
import shutil
import sys
import tempfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from possession import pipeline, transiciones  # noqa: E402
from possession.tracking import A, D, H, Tracking  # noqa: E402

FALLOS = []
FPS = 25
N = 9500
TRAMOS = ((200, 5000), (5500, 9000))


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


@contextlib.contextmanager
def sin_ficheros():
    abrir, abrir_io = builtins.open, io.open

    def niega(*args, **kwargs):
        raise AssertionError("una prueba ha intentado abrir un fichero")

    builtins.open = io.open = niega
    try:
        yield
    finally:
        builtins.open, io.open = abrir, abrir_io


def tracking(fps=FPS):
    vacio = np.full(N, np.nan)
    jugadores = np.full((N, 2), np.nan)
    return Tracking(vacio, vacio.copy(), jugadores, jugadores.copy(), np.array([0, 1], np.int8), (105.0, 68.0),
                    TRAMOS, fps)


def xml(carpeta, instancias, semilla=None):
    """Un Smart Tagging inventado con `instancias` = [(código, equipo o None, inicio_s, fin_s)]."""
    filas = list(instancias)
    if semilla is not None:
        random.Random(semilla).shuffle(filas)
    cuerpo = []
    for i, (codigo, equipo, inicio, fin) in enumerate(filas):
        etiqueta = "" if equipo is None else "<label><group>Team</group><text>{}</text></label>".format(equipo)
        cuerpo.append("<instance><ID>{}</ID><start>{}</start><end>{}</end><code>{}</code>{}"
                      "<label><group>Half</group><text>1st Half</text></label></instance>".format(
                          i, inicio, fin, codigo, etiqueta))
    ruta = os.path.join(carpeta, "smart_tagging_{}.xml".format(semilla))
    with open(ruta, "w") as f:
        f.write("<file><ALL_INSTANCES>{}</ALL_INSTANCES></file>".format("".join(cuerpo)))
    return ruta


# (código, Team, inicio en s, fin en s). En frames: × 25.
INSTANCIAS = [
    ("ATTACKING TRANSITION", "Barcelona", 10.0, 30.0),     # 250 a 375 (tope de 5 s)
    ("Attacking Transition", "Atletic Club", 40.0, 42.0),  # 1000 a 1050 (la fase dura menos que el tope)
    ("ATTACKING TRANSITION", "N/A", 50.0, 70.0),           # sin equipo: no entra
    ("ATTACKING TRANSITION", None, 52.0, 70.0),            # sin etiqueta Team: no entra
    ("DEFENSIVE TRANSITION", "Barcelona", 80.0, 100.0),    # otra fase: no entra
    ("PLAYERS IN THE BOX", "Barcelona", 80.0, 100.0),      # fase de zona: no entra
    ("BUILD UP", "Atletic Club", 80.0, 100.0),             # otra fase: no entra
    ("ATTACKING TRANSITION", "Barcelona", 4.0, 20.0),      # empieza a 100, fuera de los tramos: no entra
    ("ATTACKING TRANSITION", "Barcelona", 199.6, 230.0),   # 4990, el tramo acaba en 5000: 10 frames
    ("ATTACKING TRANSITION", "barcelona", 120.0, 140.0),   # 3000 a 3125
    ("ATTACKING TRANSITION", "Barcelona", 122.0, 140.0),   # 3050 a 3175: con la anterior, 3000 a 3175, una vez
    ("ATTACKING TRANSITION", "Athletic Club", 160.0, 180.0),  # 4000 a 4125, A (bien escrito también vale)
    ("ATTACKING TRANSITION", "Barcelona", 162.0, 180.0),   # 4050 a 4175, H: de 4050 a 4125, las dos
    ("ATTACKING TRANSITION", "Atletic Club", 240.0, 260.0),  # 6000 a 6125, en el segundo tramo
]


def esperado():
    h = np.zeros(N, dtype=bool)
    a = np.zeros(N, dtype=bool)
    h[250:375] = True
    a[1000:1050] = True
    h[4990:5000] = True
    h[3000:3175] = True
    a[4000:4125] = True
    h[4050:4175] = True
    a[6000:6125] = True
    return h, a


def sin_paths():
    print("Sin paths: no opina")
    trk = tracking()
    with sin_ficheros():
        score, allowed = transiciones.evidence(trk)
        score2, allowed2 = transiciones.evidence(trk, paths=None, game=games.GAME)
    check("forma (n, 3), todo a cero y todo permitido", score.shape == (N, 3) and allowed.shape == (N, 3) and
          not score.any() and allowed.all())
    check("igual con paths=None explícito", np.array_equal(score, score2) and np.array_equal(allowed, allowed2))


def con_smart_tagging(carpeta):
    print("Con un Smart Tagging inventado")
    trk = tracking()
    paths = {"smart_tagging": xml(carpeta, INSTANCIAS)}
    score, allowed = transiciones.evidence(trk, paths=paths)
    h, a = esperado()
    check("el peso es 8 y el tope 5 s", transiciones.WEIGHT == 8.0 and transiciones.CAP_S == 5)
    check("H recibe 8 justo en los frames esperados", np.array_equal(score[:, H] == 8.0, h) and
          set(np.unique(score[:, H])) <= {0.0, 8.0}, int(h.sum()))
    check("A recibe 8 justo en los frames esperados", np.array_equal(score[:, A] == 8.0, a) and
          set(np.unique(score[:, A])) <= {0.0, 8.0}, int(a.sum()))
    check("el tope corta a los 5 s (125 frames) una fase de 20 s", (score[250:375, H] == 8).all() and score[375, H] == 0)
    check("una fase de 2 s recibe el peso solo 2 s", (score[1000:1050, A] == 8).all() and score[1050, A] == 0)
    check("el peso no pasa del final del tramo evaluado", (score[4990:5000, H] == 8).all() and score[5000, H] == 0)
    check("una fase que empieza fuera de los tramos no entra", not score[100:250, H].any())
    check("dos transiciones del mismo equipo que se solapan dan 8, no 16", score[3050:3125, H].max() == 8.0)
    check("dos de equipos distintos a la vez: 8 en las tres columnas (la capa no opina)",
          (score[4050:4125] == 8).all())
    check("N/A, sin Team, DEFENSIVE TRANSITION, PLAYERS IN THE BOX y BUILD UP no entran",
          not score[1250:1750].any() and not score[2000:2500].any())
    check("D recibe el mismo 8 en los frames cubiertos: neutral entre jugar y parar",
          np.array_equal(score[:, D] == 8.0, h | a) and set(np.unique(score[:, D])) <= {0.0, 8.0})
    check("donde empuja, el equipo de la fase queda 8 por encima del otro y empatado con D",
          (score[250:375, H] - score[250:375, A] == 8).all() and (score[250:375, H] == score[250:375, D]).all())
    check("no prohíbe nada", allowed.all())
    check("todo finito", np.isfinite(score).all())
    otro = transiciones.evidence(trk, paths={"smart_tagging": xml(carpeta, INSTANCIAS, semilla=7)})
    check("no depende del orden del fichero", np.array_equal(score, otro[0]))
    check("dos ejecuciones dan lo mismo", np.array_equal(score, transiciones.evidence(trk, paths=paths)[0]))
    try:
        transiciones.evidence(tracking(fps=30), paths=paths)
        check("con otro fps da error", False)
    except ValueError:
        check("con otro fps da error", True)
    sin_transiciones = xml(carpeta, [("ATTACKING TRANSITION", "N/A", 10.0, 20.0),
                                     ("ATTACKING TRANSITION", "Real Madrid", 30.0, 40.0),
                                     ("BUILD UP", "Barcelona", 50.0, 60.0)], semilla=3)
    try:
        transiciones.evidence(trk, paths={"smart_tagging": sin_transiciones})
        check("sin ninguna transición con un equipo conocido, da error en vez de no hacer nada", False)
    except ValueError as e:
        check("sin ninguna transición con un equipo conocido, da error en vez de no hacer nada",
              "Real Madrid" not in str(e))
    return paths


def con_el_pipeline(paths):
    print("Encaje con el pipeline")
    capa = pipeline.resolve("transiciones.evidence", any_possession_module=True)
    check("--capa transiciones.evidence se resuelve", capa is transiciones.evidence)
    piezas, capas = pipeline.overrides([], ["transiciones.evidence"])
    check("por el camino real de --capa (pipeline.overrides), también", piezas == {} and capas == [transiciones.evidence])
    enchufada = pipeline.with_paths(capa, paths, games.GAME)
    trk = tracking()
    check("with_paths le pasa las rutas, como a dead_ball", np.array_equal(enchufada(trk)[0],
                                                                        transiciones.evidence(trk, paths)[0]))
    check("no está en pipeline.PIECES: la entrega no cambia",
          not any("transiciones" in str(v) for v in pipeline.PIECES.values()))


def main():
    sin_paths()
    carpeta = tempfile.mkdtemp(prefix="prueba_transiciones_")
    try:
        paths = con_smart_tagging(carpeta)
        con_el_pipeline(paths)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    print()
    if FALLOS:
        print("FALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
        return 1
    print("TODO BIEN")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
