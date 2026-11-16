"""Prueba la descripción de los slots sobrantes (validation/partido/slots_sobrantes.py) con un partido inventado.

    python validation/scripts/prueba_slots_sobrantes.py

Sin datos del partido: el tracking y la entrega son inventados, y abrir un fichero durante la descripción es un error
(`sin_ficheros`). Lo puede ejecutar cualquiera, Claude incluido. Prueba los tres casos de la regla (un slot quieto fuera
del campo, un duplicado pegado a un compañero y un slot nuevo en mitad del campo), la duración de las rachas, el `D`
de la entrega y que la salida no lleva ningún frame.
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
import slots_sobrantes as ss  # noqa: E402  (validation/partido/slots_sobrantes.py)
from possession.tracking import A, D, H, Tracking  # noqa: E402

FALLOS = []
N = 6000
TRAMO = (500, 5500)


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


def partido(caso):
    """11 jugadores por equipo que se mueven por el campo, y un slot 12.º del local en los frames 1000–1499 (20 s):
    quieto 5 m fuera de la banda («fuera»), pegado a 0,2 m de un compañero («duplicado») o en mitad del campo
    moviéndose («nuevo»)."""
    rng = np.random.default_rng(1)
    t = np.arange(N)[:, None]
    base_x = rng.uniform(10, 95, 22)[None, :] + 5 * np.sin(t / 100.0 + np.arange(22)[None, :])
    base_y = rng.uniform(5, 63, 22)[None, :] + 5 * np.cos(t / 120.0 + np.arange(22)[None, :])
    extra_x, extra_y = np.full((N, 1), np.nan), np.full((N, 1), np.nan)
    tramo = slice(1000, 1500)
    if caso == "fuera":
        extra_x[tramo], extra_y[tramo] = 50.0, -5.0
    elif caso == "duplicado":
        extra_x[tramo], extra_y[tramo] = base_x[tramo, :1] + 0.2, base_y[tramo, :1]
    else:
        extra_x[tramo] = 40.0 + 0.1 * np.arange(500)[:, None]
        extra_y[tramo] = 34.0
    px = np.hstack([base_x, extra_x]).astype(np.float32)
    py = np.hstack([base_y, extra_y]).astype(np.float32)
    team = np.array([H] * 11 + [A] * 11 + [H], dtype=np.int8)
    bx, by = np.full(N, 52.0), np.full(N, 34.0)
    etiquetas = np.full(N, H, dtype=np.int8)
    etiquetas[1000:1100] = D
    return Tracking(bx, by, px, py, team, (105.0, 68.0), (TRAMO,), 25), etiquetas


def main():
    print("Prueba de validation/partido/slots_sobrantes.py")
    for caso, esperado in (("fuera", ss.ARREGLOS[0]), ("duplicado", ss.ARREGLOS[1]), ("nuevo", ss.ARREGLOS[2])):
        trk, etiquetas = partido(caso)
        with sin_ficheros():
            r = ss.describir(trk, etiquetas)
            eleccion, _ = ss.arreglo(r)
            texto = "\n".join(ss.para_imprimir(r, sha="0" * 64))
        print("caso «{}»".format(caso))
        check("500 frames con sobrantes, todos del local con 12 slots",
              r["con_sobrantes"] == 500 and r["por_equipo"] == [500, 0, 0] and r["slots"] == [500, 0, 0],
              (r["con_sobrantes"], r["por_equipo"], r["slots"]))
        check("una racha de 5 a 30 s", r["rachas"] == [0, 0, 1, 0], r["rachas"])
        check("el sobrante es el slot nuevo: lleva visto de 5 a 30 s como mucho",
              r["edad"][3] == 0 and sum(r["edad"]) == 500, r["edad"])
        check("la entrega dice D en 100 de los 500", r["d_con_sobrantes"] == 100, r["d_con_sobrantes"])
        check("el arreglo es «{}»".format(esperado), eleccion == esperado, eleccion)
        check("la salida no lleva ningún frame", "1000" not in texto and "1499" not in texto)
        if caso == "fuera":
            check("está a más de 3 m fuera y quieto", r["sitio"][0] == 500 and r["velocidad"][0] >= 450,
                  (r["sitio"], r["velocidad"]))
            check("la comprobación ve slots fuera con sobrantes y no con 9–11",
                  r["comprobacion"]["sobra"][1] == 500 and r["comprobacion"]["normal"][1] == 0, r["comprobacion"])
        if caso == "duplicado":
            check("pegado a un compañero", r["companero"][0] == 500, r["companero"])
        if caso == "nuevo":
            check("dentro del campo", r["sitio"][4] == 500, r["sitio"])
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
