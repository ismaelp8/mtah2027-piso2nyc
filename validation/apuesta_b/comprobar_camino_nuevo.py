"""Comprobación del instrumento: N1 por el camino nuevo del harness da lo mismo que la versión de `main`.

    python validation/apuesta_b/comprobar_camino_nuevo.py

El camino nuevo es una función de otro módulo («aprendida.…») con «dejar_fuera». Aquí esa función es N1
(`candidates.evidence`), así que las 8 celdas (dos convenciones × cuatro condiciones del balón) tienen que
ser idénticas a las de `{}`, y la pieza tiene que recibir los 7 partidos de la DFL al puntuar. Se ejecutó
el 14/11 antes de medir la apuesta B.

Datos abiertos de la DFL: lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. Tarda un
minuto.
"""

import json
import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, candidates  # noqa: E402

CLAVES = ("spell_f1", "spell_f1_por_partido", "macro_f1_medio", "acierto_de_equipo_medio",
          "posesiones_predichas", "posesiones_reales")


def main():
    recibidos = []

    def n1_por_aprendida(trk, fuera=None):
        recibidos.append(fuera)
        return candidates.evidence(trk)

    aprendida.n1_por_aprendida = n1_por_aprendida
    carpeta = tempfile.mkdtemp(prefix="mtah_camino_nuevo_")
    try:
        ruta = os.path.join(carpeta, "n1.json")
        with open(ruta, "w", encoding="utf-8") as handle:
            json.dump({"main": {}, "N1 por el camino nuevo": {"piezas": {"candidates": {
                "funcion": "aprendida.n1_por_aprendida", "dejar_fuera": True}}}}, handle)
        versiones = puntuar.leer_versiones(ruta)[0]
        del recibidos[:]
        salida, _, _ = puntuar.medir(list(dfl.PARTIDOS), "oraculo", 0, versiones=versiones)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
        del aprendida.n1_por_aprendida
    celdas = [(filas["main"], filas["N1 por el camino nuevo"])
              for por_condicion in salida.values() for filas in por_condicion.values()]
    iguales = sum(all(a[k] == b[k] for k in CLAVES) for a, b in celdas)
    print("celdas (convención × condición): {}, idénticas: {}".format(len(celdas), iguales))
    todos = sorted(set(recibidos)) == sorted(dfl.PARTIDOS)
    print("la pieza recibió los {} partidos al puntuar: {} ({} llamadas)".format(
        len(dfl.PARTIDOS), "sí" if todos else "no", len(recibidos)))
    if iguales != len(celdas) or not todos:
        sys.exit(1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
