"""Comprobación del instrumento: N1 por el camino nuevo del harness da lo mismo que la versión de `main`.

    python validation/apuesta_b/comprobar_camino_nuevo.py

El camino nuevo es una función de otro módulo («aprendida.…») con «dejar_fuera». Aquí esa función es N1
(`candidates.evidence`), así que las 8 celdas (dos convenciones × cuatro condiciones del balón) tienen que
ser idénticas a las de `{}`, y la pieza tiene que recibir los 7 partidos de la DFL al puntuar. Se ejecutó
el 14/11 antes de medir la apuesta B.

Desde el 15/11 comprueba también que B4 con la α de B2 y el `D` oráculo da las mismas etiquetas que B2:
solo cambia cuánto pesa cada equipo frente a `D`, y con el oráculo eso no cambia ninguna etiqueta.

Datos abiertos de la DFL: lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. Tarda un
minuto.
"""

import json
import os
import shutil
import sys
import tempfile

import numpy as np

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
    b4_igual = comprobar_b4()
    if iguales != len(celdas) or not todos or not b4_igual:
        sys.exit(1)


def comprobar_b4():
    """B4 (15/11) con la α de B2 y el `D` oráculo da las mismas etiquetas que B2 en los 7 partidos."""
    def b4_con_alfa_de_b2(trk, fuera=None):
        juego = aprendida.coeficientes("b2", fuera)
        z = aprendida.logit(aprendida.rasgos(trk, "b2"), juego["pesos"])
        return aprendida.puntuacion_de("b4", z, aprendida.balon_visible(trk), juego["alfa"])

    iguales, total = 0, 0
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        for condicion in dfl.VOTAN:
            trk = puntuar.solo_lectura(dfl.tracking_de(cargado, condicion))
            extra = [puntuar.d_oraculo(cargado["gt"]["flag"])]
            b2 = puntuar.pipeline.run(trk, extra=extra, pieces={
                "candidates": lambda t, p=partido: aprendida.evidence_b2(t, fuera=p)})
            b4 = puntuar.pipeline.run(trk, extra=extra, pieces={
                "candidates": lambda t, p=partido: b4_con_alfa_de_b2(t, fuera=p)})
            iguales += int(np.array_equal(b2, b4))
            total += 1
    print("B4 con la α de B2 y el D oráculo da las mismas etiquetas que B2: {} de {} (partido × condición)".format(
        iguales, total))
    return iguales == total


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
