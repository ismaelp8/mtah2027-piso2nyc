"""Comprueba que reanudar un entrenamiento desde su punto de control da los mismos pesos, bit a bit, que no pararse.

    python validation/conjunto/comprobar_puntos.py k7 --hilos 4
    python validation/conjunto/comprobar_puntos.py k8 --hilos 4

Datos abiertos de otros partidos (la caché de `exportar.py` y de `exportar_metrica.py`). Lo puede ejecutar cualquiera,
Claude incluido. Solo imprime agregados. Hace falta torch. Tarda unos segundos de entrenamiento (6 pasos), más la carga
de los partidos.

Hace dos entrenamientos con la misma semilla y `{"pasos": 6}`, en la CPU:

- **A:** los 6 pasos de una vez, sin puntos de control;
- **B:** se para tras el paso 3 (`--hasta 3`, que deja su punto) y se vuelve a lanzar igual, así que reanuda y termina.

Pasa si los pesos finales de A y B son iguales, tensor a tensor, y el punto de B se ha borrado al terminar. En K7 es la
variante s, porque es la que tiene más estado (la z por proveedor); en K8, el pliegue de `J03WMX` con el CRF.
"""

import argparse
import os
import subprocess
import sys

import torch

import cj_comun as cj
import puntos

AQUI = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def lanzar(base, etiqueta, extra):
    orden = [sys.executable, os.path.join(AQUI, base[0])] + base[1:] + ["--etiqueta", etiqueta] + extra
    salida = subprocess.run(orden, cwd=AQUI, capture_output=True, text=True)
    if salida.returncode:
        print(salida.stdout[-2000:], salida.stderr[-2000:])
        raise SystemExit("falló: {}".format(" ".join(orden[1:])))
    return [linea for linea in salida.stdout.splitlines() if "Reanuda" in linea or "Parado" in linea]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("que", choices=("k7", "k8"))
    parser.add_argument("--hilos", type=int, default=4)
    args = parser.parse_args()
    comun = ["--dispositivo", "cpu", "--columnas", "33", "--hilos", str(args.hilos), "--config", '{"pasos": 6}']
    if args.que == "k7":
        base, pliegue = ["entrenar_k7.py", "s"], "todos"
        comun = comun + ["--sin-describir"]
    else:
        base, pliegue = ["entrenar_k8.py", cj.PILOTO], cj.PILOTO
    a, b = "comprobar_puntos_{}_a".format(args.que), "comprobar_puntos_{}_b".format(args.que)
    for etiqueta in (a, b):  # empezar limpio
        puntos.borrar(puntos.ruta(etiqueta, pliegue))
    lanzar(base, a, comun + ["--cada", "0", "--desde-cero"])
    mensajes = lanzar(base, b, comun + ["--hasta", "3", "--desde-cero"])
    hubo_punto = puntos.ruta(b, pliegue).is_file()
    mensajes += lanzar(base, b, comun)
    print("\n".join("- " + m for m in mensajes))
    pa = torch.load(cj.fichero_pesos(a, pliegue), map_location="cpu", weights_only=False)["pesos"]
    pb = torch.load(cj.fichero_pesos(b, pliegue), map_location="cpu", weights_only=False)["pesos"]
    distintos = [k for k in sorted(set(pa) | set(pb)) if k not in pa or k not in pb or not torch.equal(pa[k], pb[k])]
    borrado = not puntos.ruta(b, pliegue).is_file()
    print("Punto de control tras el paso 3: {} · reanudó: {} · tensores comparados: {} · distintos: {} · punto borrado "
          "al terminar: {}".format("sí" if hubo_punto else "no", "sí" if any("Reanuda" in m for m in mensajes) else "no",
                                   len(set(pa) | set(pb)), ", ".join(distintos) or "ninguno", "sí" if borrado else "no"))
    bien = hubo_punto and not distintos and borrado and any("Reanuda" in m for m in mensajes)
    print("\nComprobación de los puntos de control ({}): **{}**".format(args.que, "pasa" if bien else "NO PASA"))
    sys.exit(0 if bien else 1)


if __name__ == "__main__":
    main()
