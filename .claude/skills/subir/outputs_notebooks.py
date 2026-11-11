"""Cuenta (y, si se pide, borra) los outputs de los notebooks sin enseñar nunca su contenido.

Los outputs de un notebook guardan datos del partido: tablas, coordenadas, gráficos del tracking.
Este script imprime solo recuentos, así que Claude puede comprobar un notebook antes de leerlo, de
mirar su diff o de hacer commit, sin ver nada de lo que hay dentro.

    python .claude/skills/subir/outputs_notebooks.py                       # todos los .ipynb del repo
    python .claude/skills/subir/outputs_notebooks.py notebooks/exploracion.ipynb
    python .claude/skills/subir/outputs_notebooks.py --limpiar notebooks/exploracion.ipynb

Sin --limpiar, sale con código 1 si algún notebook tiene outputs y con 0 si ninguno tiene.
Con --limpiar, deja todas las celdas sin outputs y sin número de ejecución, y sale con 0.
Solo usa la biblioteca estándar; si nbformat está instalado (viene con `notebook`), lo usa para
escribir el fichero con el mismo formato que Jupyter.
"""

import argparse
import glob
import json
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SALTAR = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", ".ipynb_checkpoints", "data"}


def buscar(rutas):
    """Los .ipynb indicados (ficheros, carpetas o patrones) o, si no hay ninguno, todos los del repo."""
    encontrados = []
    for ruta in rutas or [RAIZ]:
        if os.path.isdir(ruta):
            for carpeta, subcarpetas, ficheros in os.walk(ruta):
                subcarpetas[:] = sorted(d for d in subcarpetas if d not in SALTAR)
                encontrados += [os.path.join(carpeta, f) for f in sorted(ficheros) if f.endswith(".ipynb")]
        else:
            encontrados += sorted(glob.glob(ruta)) or [ruta]
    return [f for f in encontrados if f.endswith(".ipynb")]


def contar(notebook):
    """(outputs, celdas con número de ejecución) de un notebook ya cargado."""
    celdas = [c for c in notebook.get("cells", []) if c.get("cell_type") == "code"]
    outputs = sum(len(c.get("outputs") or []) for c in celdas)
    ejecutadas = sum(1 for c in celdas if c.get("execution_count") is not None)
    return outputs, ejecutadas


def limpiar(ruta):
    try:
        import nbformat
    except ImportError:
        nbformat = None
    if nbformat is not None:
        notebook = nbformat.read(ruta, as_version=nbformat.NO_CONVERT)
        for celda in notebook.cells:
            if celda.cell_type == "code":
                celda.outputs = []
                celda.execution_count = None
        nbformat.write(notebook, ruta)
        return
    with open(ruta, encoding="utf-8") as f:
        notebook = json.load(f)
    for celda in notebook.get("cells", []):
        if celda.get("cell_type") == "code":
            celda["outputs"] = []
            celda["execution_count"] = None
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(notebook, indent=1, sort_keys=True, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rutas", nargs="*", help="notebooks, carpetas o patrones (por defecto, todo el repo)")
    parser.add_argument("--limpiar", action="store_true", help="borra los outputs y los números de ejecución")
    args = parser.parse_args()

    notebooks = buscar(args.rutas)
    if not notebooks:
        print("No hay notebooks que revisar.")
        return 0

    con_outputs = 0
    for ruta in notebooks:
        nombre = os.path.relpath(ruta, RAIZ) if os.path.abspath(ruta).startswith(RAIZ) else ruta
        try:
            with open(ruta, encoding="utf-8") as f:
                outputs, ejecutadas = contar(json.load(f))
        except (OSError, ValueError) as error:
            # Solo el tipo de error: el mensaje podría citar contenido del fichero.
            print("ERROR  {}  no se puede leer ({})".format(nombre, type(error).__name__))
            con_outputs += 1
            continue
        if args.limpiar and (outputs or ejecutadas):
            limpiar(ruta)
            print("LIMPIO {}  se han borrado {} outputs".format(nombre, outputs))
        elif outputs:
            con_outputs += 1
            print("SUCIO  {}  {} outputs en {} celdas ejecutadas".format(nombre, outputs, ejecutadas))
        else:
            print("OK     {}  sin outputs".format(nombre))

    if con_outputs and not args.limpiar:
        print("\n{} notebook(s) con outputs. No los leas ni los subas: límpialos con --limpiar "
              "(o en Jupyter: Kernel > Restart & Clear Output).".format(con_outputs))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
