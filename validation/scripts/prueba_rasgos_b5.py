"""Prueba la comparación de los rasgos de B5 (validation/partido/rasgos_b5.py) con números y un tracking inventados.

    python validation/scripts/prueba_rasgos_b5.py

Sin datos del partido ni de nadie: la referencia, los cuantiles y el tracking son inventados, y abrir un fichero
durante la comparación es un error (`sin_ficheros`). Lo puede ejecutar cualquiera, Claude incluido. Prueba que los
rasgos se calculan sobre un `Tracking`, que la regla mira solo los diez de más peso y solo la mediana, y que la salida
dice qué decide.
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
import rasgos_b5 as rb  # noqa: E402  (validation/partido/rasgos_b5.py)
from possession import aprendida  # noqa: E402
from possession.tracking import A, H, Tracking  # noqa: E402

FALLOS = []
NOMBRES = aprendida.NOMBRES["b2"]


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


def referencia():
    """Rango [1, 2] para la mediana y [3, 4] para el p90 en todos los rasgos; los diez primeros son el top."""
    return {"commit": "prueba", "top": NOMBRES[:10], "importancia": {n: float(30 - j) for j, n in enumerate(NOMBRES)},
            "rango": {n: [1.0, 2.0, 3.0, 4.0] for n in NOMBRES},
            "acuerdo_b5_mas_cercano": {"a": 0.8, "b": 0.9}}


def tracking_inventado():
    rng = np.random.default_rng(3)
    n = 3000
    px = rng.uniform(0, 105, (n, 22)).astype(np.float32)
    py = rng.uniform(0, 68, (n, 22)).astype(np.float32)
    bx, by = rng.uniform(0, 105, n), rng.uniform(0, 68, n)
    bx[1000:1500] = np.nan
    team = np.array([H] * 11 + [A] * 11, dtype=np.int8)
    return Tracking(bx, by, px, py, team, (105.0, 68.0), ((100, 2900),), 25)


def main():
    print("Prueba de validation/partido/rasgos_b5.py")
    print("1. Los rasgos se calculan sobre un Tracking")
    with sin_ficheros():
        matriz, acuerdo = rb.ref.resumen_rasgos(tracking_inventado())
        cuantiles = rb.ref.cuantiles(matriz)
    check("una fila por frame de los tramos con balón (2.300) y 30 rasgos", matriz.shape == (2300, 30), matriz.shape)
    check("un acuerdo entre 0 y 1", 0.0 <= acuerdo <= 1.0, acuerdo)
    check("mediana y p90 de los 30", set(cuantiles) == set(NOMBRES) and all(len(v) == 2 for v in cuantiles.values()))
    print("2. La regla")
    dentro = {n: [1.5, 3.5] for n in NOMBRES}
    with sin_ficheros():
        r = rb.comparar(dentro, 0.85, referencia())
    check("todo dentro: nada desplazado", r["desplazados"] == [])
    fuera_bajo = dict(dentro)
    fuera_bajo[NOMBRES[20]] = [9.0, 3.5]  # fuera, pero no es de los diez
    fuera_bajo[NOMBRES[0]] = [1.5, 9.0]  # de los diez, pero solo el p90 fuera
    r = rb.comparar(fuera_bajo, 0.85, referencia())
    check("un rasgo fuera de los diez, o solo el p90 fuera: nada desplazado", r["desplazados"] == [])
    fuera = dict(dentro)
    fuera[NOMBRES[3]] = [0.5, 3.5]
    r = rb.comparar(fuera, 0.85, referencia())
    check("la mediana de uno de los diez fuera: desplazado", r["desplazados"] == [NOMBRES[3]], r["desplazados"])
    print("3. La salida")
    texto = "\n".join(rb.para_imprimir(r))
    check("dice que hay uno desplazado", "→ SÍ" in texto and NOMBRES[3] in texto)
    texto = "\n".join(rb.para_imprimir(rb.comparar(dentro, 0.85, referencia())))
    check("y que no lo hay", "→ NO" in texto)
    print("4. Los frames con un equipo de más de 11 slots, aparte")
    trk = tracking_inventado()
    px, py = trk.px.copy(), trk.py.copy()
    extra = np.full((len(px), 1), np.nan, dtype=np.float32)
    extra[200:700] = 50.0  # un slot 12.º del local en 500 frames de los tramos con balón
    trk = trk._replace(px=np.hstack([px, extra]), py=np.hstack([py, extra]),
                       team=np.concatenate([trk.team, [H]]).astype(np.int8))
    with sin_ficheros():
        check("cuenta los frames con más de 11", int(rb.mas_de_11(trk).sum()) == 500, int(rb.mas_de_11(trk).sum()))
        matriz, acuerdo = rb.ref.resumen_rasgos(trk)
        grupos = rb.por_grupo(trk, matriz)
    check("los separa: 500 y 1.800 frames con balón",
          [grupos[g][1] for g in rb.GRUPOS] == [500, 1800], [grupos[g][1] for g in rb.GRUPOS])
    solo_mas = {rb.GRUPOS[0]: (fuera, 500), rb.GRUPOS[1]: (dentro, 1800)}
    r = rb.comparar(dentro, 0.85, referencia(), solo_mas)
    check("la regla sigue mirando todos los frames", r["desplazados"] == [])
    check("y por separado dice dónde se sale", r["grupos"][rb.GRUPOS[0]]["desplazados"] == [NOMBRES[3]]
          and r["grupos"][rb.GRUPOS[1]]["desplazados"] == [])
    texto = "\n".join(rb.para_imprimir(r))
    check("la salida lo enseña", "más de 11 slots" in texto and "FUERA" in texto)
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
