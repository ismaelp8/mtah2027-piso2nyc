"""K7: pasa los pesos de `entrenar_k7.py` al formato de `possession/conjunto.py`, fuera del repo.

    python validation/conjunto/juntar_k7.py --etiqueta k7c
    python validation/conjunto/juntar_k7.py --etiqueta k7s

Hace falta torch, solo para leer el `.pt`. No lee ningún dato. Escribe en `conjunto_cache/` un `.npz` por versión, con
la clave «todos» y α = 4, la de la entrega y la de las réplicas de un solo proveedor (docs/decisiones.md, 17/11, K7):

- variante `c`: `pesos_<etiqueta>.npz`, tal cual;
- variante `s`: `pesos_<etiqueta>_media.npz` (la que vota: la media de las dos z, escrita como una sola fila de la
  última capa, que es lineal), y sin voto `pesos_<etiqueta>_dfl.npz` y `pesos_<etiqueta>_metrica.npz` (cada z por
  separado).

`possession/conjunto.py` lee cualquiera de ellos sin cambiar nada (`conjunto.PESOS`, como `refinar.py --pesos`).
"""

import argparse
import hashlib
import sys

import numpy as np
import torch

import cj_comun as cj
from juntar import a_numpy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ALFA = 4.0  # fijada antes de entrenar: la de «todos» en la entrega y la de las réplicas de un solo proveedor


def escribir(pesos, destino):
    salida = {"todos/{}".format(k): v for k, v in pesos.items()}
    salida["todos/alfa"] = np.asarray(ALFA, dtype=np.float64)
    np.savez(destino, **salida)
    with open(destino, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def con_fila(pesos, fila_w, fila_b):
    """Los pesos con la fila 0 de la última capa (la z) cambiada y sin la quinta salida."""
    nuevos = dict(pesos)
    w = np.asarray(pesos["salida_w"], dtype=np.float64)
    b = np.asarray(pesos["salida_b"], dtype=np.float64)
    nuevos["salida_w"] = np.vstack([fila_w[None, :], w[1:4]])
    nuevos["salida_b"] = np.concatenate([[fila_b], b[1:4]])
    return nuevos


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--etiqueta", required=True)
    args = parser.parse_args()
    guardado = torch.load(cj.fichero_pesos(args.etiqueta, "todos"), map_location="cpu", weights_only=False)
    config = guardado["config"]
    pesos = a_numpy(guardado["pesos"], config)
    salidas = pesos["salida_w"].shape[0]
    print("# K7{} · tanda «{}» · semilla {} · {} salidas en la última capa\n".format(
        config["variante"], args.etiqueta, guardado["semilla"], salidas))
    base = cj.carpeta()
    if config["variante"] == "c":
        if salidas != 4:
            raise ValueError("la variante c tiene 4 salidas")
        print("- `pesos_{}.npz`: sha256 {}…".format(args.etiqueta, escribir(pesos, base / "pesos_{}.npz".format(
            args.etiqueta))))
        return
    if salidas != 5:
        raise ValueError("la variante s tiene 5 salidas")
    w = np.asarray(pesos["salida_w"], dtype=np.float64)
    b = np.asarray(pesos["salida_b"], dtype=np.float64)
    versiones = {"media": (0.5 * (w[0] + w[4]), 0.5 * (b[0] + b[4])), "dfl": (w[0], b[0]), "metrica": (w[4], b[4])}
    for nombre, (fila_w, fila_b) in versiones.items():
        destino = base / "pesos_{}_{}.npz".format(args.etiqueta, nombre)
        print("- `{}`{}: sha256 {}…".format(destino.name, " (vota)" if nombre == "media" else " (sin voto)",
                                          escribir(con_fila(pesos, fila_w, fila_b), destino)))


if __name__ == "__main__":
    main()
