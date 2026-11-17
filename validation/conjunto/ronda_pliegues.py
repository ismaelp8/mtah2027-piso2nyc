"""Entrena los 8 pliegues de un candidato del modelo conjunto, uno detrás de otro, y junta sus pesos. Para la GPU.

    python validation/conjunto/ronda_pliegues.py entrenar_k8.py --etiqueta k8                     # en la GPU, ~21 min
    python validation/conjunto/ronda_pliegues.py entrenar_k8.py --etiqueta k8 -- --dispositivo cpu --columnas 33

Datos abiertos de otros partidos (la caché de `exportar.py`). Lo puede ejecutar cualquiera, Claude incluido. Solo
imprime agregados.

Ejecuta `<script> <pliegue> --etiqueta <etiqueta> [lo que vaya después de --]` para los 7 pliegues de la DFL y el de
«todos», con el mismo python, y después `juntar.py --etiqueta <etiqueta> --alfa 4 --destino
<conjunto_cache>/pesos_<etiqueta>.npz`. La α queda en 4, la de la entrega: un candidato nuevo no elige su α. Los pesos se
quedan fuera del repo. Si un pliegue ya tiene sus pesos (`conjunto_cache/pesos/<etiqueta>_<pliegue>.pt`), no se vuelve
a entrenar: así se puede retomar una ronda cortada.

Lo mide después `medir_pliegues.py --pesos pesos_<etiqueta>.npz`.
"""

import argparse
import os
import subprocess
import sys
import time

import cj_comun as cj

AQUI = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    if "--" in sys.argv:
        corte = sys.argv.index("--")
        propios, extra = sys.argv[1:corte], sys.argv[corte + 1:]
    else:
        propios, extra = sys.argv[1:], []
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("script", help="el script de entrenamiento, en validation/conjunto/ (p. ej. entrenar_k8.py)")
    parser.add_argument("--etiqueta", required=True)
    parser.add_argument("--pliegues", nargs="*", default=list(cj.PLIEGUES))
    args = parser.parse_args(propios)
    inicio = time.time()
    for pliegue in args.pliegues:
        if cj.fichero_pesos(args.etiqueta, pliegue).is_file():
            print("# {}: ya estaba entrenado".format(pliegue), flush=True)
            continue
        orden = [sys.executable, os.path.join(AQUI, args.script), pliegue, "--etiqueta", args.etiqueta] + extra
        print("# {}: {}".format(pliegue, " ".join(os.path.basename(o) if o.endswith(".py") else o for o in orden[1:])),
              flush=True)
        subprocess.run(orden, check=True, cwd=AQUI)
        print("# {} hecho, {:.0f} min desde el principio".format(pliegue, (time.time() - inicio) / 60.0), flush=True)
    destino = cj.carpeta() / "pesos_{}.npz".format(args.etiqueta)
    subprocess.run([sys.executable, os.path.join(AQUI, "juntar.py"), "--etiqueta", args.etiqueta, "--alfa", "4",
                    "--destino", str(destino), "--pliegues"] + list(args.pliegues), check=True, cwd=AQUI)
    print("\nRonda «{}» hecha en {:.0f} min: {}".format(args.etiqueta, (time.time() - inicio) / 60.0, destino))


if __name__ == "__main__":
    main()
