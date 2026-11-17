"""Junta los pesos de los pliegues del modelo conjunto en el fichero que lee `possession/conjunto.py`.

    python validation/conjunto/juntar.py --etiqueta v1                         # los 8 pliegues, con su α
    python validation/conjunto/juntar.py --etiqueta piloto1 --pliegues J03WMX --destino <ruta>.npz --alfa 1

Hace falta el entorno `mtah2027-conjunto` (torch), solo para leer los `.pt` de `entrenar.py`. No lee ningún dato.

Escribe `possession/conjunto_pesos.npz` (o `--destino`): por cada pliegue, los pesos en float32, tal como salieron
de torch, las dilaciones y `alfa`. La α de cada pliegue es la que eligió `medir.py` para el partido que ese pliegue
no vio (con los otros seis), y la del pliegue de todos, la elegida con los 7 (`elegidos.json`, junto a las salidas).
"""

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import torch

import cj_comun as cj

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESTINO = os.path.join(ROOT, "possession", "conjunto_pesos.npz")


def a_numpy(estado, config):
    """Los pesos de `red.Conjunto` con los nombres que usa `possession/conjunto.py`."""
    def valor(nombre):
        return estado[nombre].detach().cpu().numpy().astype(np.float32)
    pesos = {"jugador_w0": valor("jugador.0.weight"), "jugador_b0": valor("jugador.0.bias"),
             "jugador_w1": valor("jugador.2.weight"), "jugador_b1": valor("jugador.2.bias"),
             "entrada_w": valor("entrada.weight")[:, :, 0], "entrada_b": valor("entrada.bias"),
             "salida_w": valor("salida.weight")[:, :, 0], "salida_b": valor("salida.bias"),
             "dilaciones": np.asarray(config["dilaciones"], dtype=np.int64)}
    for k in range(len(config["dilaciones"])):
        pesos["bloque{}_w".format(k)] = valor("bloques.{}.weight".format(k))
        pesos["bloque{}_b".format(k)] = valor("bloques.{}.bias".format(k))
    return pesos


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--etiqueta", required=True)
    parser.add_argument("--pliegues", nargs="*", default=list(cj.PLIEGUES))
    parser.add_argument("--destino", default=DESTINO)
    parser.add_argument("--alfa", type=float, default=None,
                        help="solo para pruebas: la misma α en todos los pliegues, sin leer `elegidos.json`")
    args = parser.parse_args()
    if args.alfa is None:
        with open(cj.carpeta() / "salidas" / args.etiqueta / "elegidos.json", encoding="utf-8") as f:
            alfas = json.load(f)["K2"]
    salida = {}
    print("| pliegue | pesos | α | semilla |")
    print("|---|---|---|---|")
    for pliegue in args.pliegues:
        guardado = torch.load(cj.fichero_pesos(args.etiqueta, pliegue), map_location="cpu", weights_only=False)
        if guardado["pliegue"] != pliegue:
            raise ValueError("el fichero de {} dice que es de {}".format(pliegue, guardado["pliegue"]))
        pesos = a_numpy(guardado["pesos"], guardado["config"])
        alfa = float(args.alfa if args.alfa is not None else alfas[pliegue])
        pesos["alfa"] = np.asarray(alfa, dtype=np.float64)
        for nombre, valor in pesos.items():
            salida["{}/{}".format(pliegue, nombre)] = valor
        print("| {} | {} | {:g} | {} |".format(
            pliegue, sum(int(v.size) for k, v in pesos.items() if k not in ("alfa", "dilaciones")), alfa,
            guardado["semilla"]))
    np.savez(args.destino, **salida)
    with open(args.destino, "rb") as f:
        huella = hashlib.sha256(f.read()).hexdigest()
    print("\nEscrito {} ({:.1f} MB), sha256 {}.".format(os.path.basename(args.destino),
                                                       os.path.getsize(args.destino) / 1e6, huella[:16]))


if __name__ == "__main__":
    main()
