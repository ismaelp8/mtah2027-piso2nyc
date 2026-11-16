"""Prueba el agregado de los cambios entre fases (validation/partido/cambios_entre_fases.py) con un partido inventado.

    python validation/scripts/prueba_cambios_entre_fases.py

Sin datos del partido: el tracking, las fases y la entrega son inventados, y abrir un fichero durante el recuento es
un error (`sin_ficheros`). Lo puede ejecutar cualquiera, Claude incluido. Prueba los cambios que cuentan y los
apartados (transición, reinicio, hueco del balón), las clases y lo que tarda la entrega, la regla con sus tres
salidas y que la salida no lleva ningún frame.
"""

import builtins
import contextlib
import io
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import cambios_entre_fases as cef  # noqa: E402  (validation/partido/cambios_entre_fases.py)
from possession.tracking import A, H, X, Tracking  # noqa: E402

FALLOS = []
FPS = 25
N = 45000
PERIODO = 700  # frames entre dos fases normales
RETRASO = 100  # frames que tarda la entrega en pasar al equipo de cada fase normal (4 s)
NORMALES = 41  # fases normales: 40 cambios


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


def evento(codigo, equipo, inicio, fin):
    nombre = {H: "Barcelona", A: "Atletic Club", None: "N/A"}[equipo]
    return {"code": codigo, "start_frame": inicio, "end_frame": fin, "tags": {"Team": nombre}}


def partido():
    """(trk, eventos, etiquetas, inicios de las fases): 41 fases normales que alternan de equipo y en las que la
    entrega llega 4 s tarde, y después cuatro casos especiales (bitácora P1):
    - una ATTACKING TRANSITION (se aparta: ya está en la capa de los contraataques);
    - una fase que empieza dentro de una ventana SET PIECES (se aparta: reinicio);
    - una con un hueco del balón de 160 frames justo antes (se aparta: hueco);
    - una en la que la entrega ya va con ese equipo (cuenta, clase «ya era ese equipo»)."""
    bx, by = np.full(N, 50.0), np.full(N, 34.0)
    px, py = np.tile([30.0, 70.0], (N, 1)), np.tile([34.0, 34.0], (N, 1))
    etiquetas = np.full(N, A, dtype=np.int8)
    eventos, inicios = [], []
    for k in range(NORMALES):
        s = 1000 + PERIODO * k
        equipo = H if k % 2 == 0 else A
        eventos.append(evento("BUILD UP" if k % 3 else "Progression", equipo, s, s + 600))
        etiquetas[s + RETRASO:s + PERIODO + RETRASO] = equipo
        inicios.append(s)
    eventos.append(evento("ATTACKING TRANSITION", A, 29700, 30300))
    eventos.append(evento("PROGRESSION", H, 30400, 31000))
    eventos.append(evento("SET PIECES", None, 30350, 31225))
    eventos.append(evento("BUILD UP", A, 31300, 31900))
    bx[31100:31260], by[31100:31260] = np.nan, np.nan
    eventos.append(evento("PROGRESSION", H, 32000, 32600))
    etiquetas[29800:31700] = A
    etiquetas[31700:] = H
    # fases que no entran: de zona y de defensa, y una sin equipo
    eventos.append(evento("PLAYERS IN THE BOX", A, 5000, 5400))
    eventos.append(evento("DEFENDING IN MIDDLE THIRD", A, 7000, 7400))
    eventos.append(evento("LONG BALL", None, 9000, 9200))
    inicios += [29700, 30400, 31300, 32000]
    trk = Tracking(bx, by, px.astype(np.float32), py.astype(np.float32), np.array([H, A], dtype=np.int8),
                   (105.0, 68.0), ((0, N),), FPS)
    return trk, eventos, etiquetas, inicios


def main():
    print("Prueba de validation/partido/cambios_entre_fases.py")
    trk, eventos, etiquetas, inicios = partido()
    with sin_ficheros():
        r = cef.recuento(trk, eventos, etiquetas)
        lineas = cef.para_imprimir(r, sha="0" * 64)
    print("1. Cambios que cuentan y apartados")
    check("fases de ataque (41 normales y 4 especiales)", r["fases_ataque"] == NORMALES + 4, r["fases_ataque"])
    check("cambios entre fases: 40 normales y 4 especiales", r["cambios_total"] == 44, r["cambios_total"])
    check("se aparta la transición", r["apartados"][cef.MOTIVOS[0]] == 1, r["apartados"])
    check("se aparta la fase dentro de la ventana de saque", r["apartados"][cef.MOTIVOS[1]] == 1)
    check("se aparta la fase con un hueco del balón antes", r["apartados"][cef.MOTIVOS[2]] == 1)
    check("cuentan 41", r["reales"]["inicios"] == 41, r["reales"]["inicios"])
    print("2. Clases y lo que tarda la entrega")
    check("40 «era el otro equipo» y 1 «ya era ese equipo»", r["reales"]["clases"] == [0, 1, 40, 0],
          r["reales"]["clases"])
    check("los 40 tardan de 2 a 5 s", r["reales"]["tarda"] == [0, 40, 0, 0, 0], r["reales"]["tarda"])
    check("el placebo cuenta inicios", sum(p["inicios"] for p in r["placebo"]) > 0)
    print("3. La regla")
    sigue, tarde, tarde_p, _ = cef.veredicto(r)
    check("con este partido: la proporción real es 40/41", abs(tarde - 40 / 41.0) < 1e-12, tarde)
    check("y sigue si y solo si el placebo está en la mitad o menos", sigue == (tarde_p <= 0.5 * tarde),
          (sigue, tarde_p))
    pocos = {"reales": {"inicios": 20, "clases": [0, 0, 20, 0], "tarda": [0] * 5},
             "placebo": [{"inicios": 100, "clases": [0, 100, 0, 0], "tarda": [0] * 5}]}
    check("con menos de 30 no sigue", cef.veredicto(pocos)[0] is False and "menos de 30" in cef.veredicto(pocos)[3])
    bien = {"reales": {"inicios": 40, "clases": [0, 5, 30, 5], "tarda": [0] * 5},
            "placebo": [{"inicios": 100, "clases": [10, 50, 20, 20], "tarda": [0] * 5}]}
    check("75 % frente al 20 % del placebo: sigue", cef.veredicto(bien)[0] is True)
    mal = {"reales": {"inicios": 40, "clases": [0, 5, 30, 5], "tarda": [0] * 5},
           "placebo": [{"inicios": 100, "clases": [10, 10, 50, 30], "tarda": [0] * 5}]}
    check("75 % frente al 50 % del placebo: no sigue", cef.veredicto(mal)[0] is False)
    flojo = {"reales": {"inicios": 40, "clases": [10, 10, 15, 5], "tarda": [0] * 5},
             "placebo": [{"inicios": 100, "clases": [10, 80, 5, 5], "tarda": [0] * 5}]}
    check("37,5 % de reales: no sigue", cef.veredicto(flojo)[0] is False)
    print("4. La salida solo lleva agregados")
    texto = "\n".join(lineas)
    check("ningún inicio de fase en la salida", not any(str(s) in texto for s in inicios))
    check("dice qué decide la regla", "SIGUE" in texto)
    print()
    if FALLOS:
        print("FALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
        return 1
    print("Todo bien.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
