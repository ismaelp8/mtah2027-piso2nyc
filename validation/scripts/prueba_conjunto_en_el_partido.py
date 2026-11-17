"""Prueba la comparación de `validation/partido/conjunto_en_el_partido.py` con números inventados.

    python validation/scripts/prueba_conjunto_en_el_partido.py

No abre ningún fichero del partido: solo ejecuta `comparar`, que es una función pura, `agregados.agregados` sobre el
partido inventado del harness (con los pesos del modelo, si están) y el texto que imprimiría el script. Claude puede
ejecutarlo. Sale con código 1 si falla alguna comprobación.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "conjunto"),
                 os.path.join(ROOT, "validation", "partido")):
    sys.path.insert(0, _carpeta)
import agregados  # noqa: E402
import conjunto_en_el_partido as cp  # noqa: E402
import puntuar  # noqa: E402
from possession import conjunto  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

fallos = []


def comprobar(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(nombre)


def main():
    referencia = {"commit": "abc1234", "vistas": 34, "rango": {
        "entrada por jugador · velocidad x · mediana": [1.0, 2.0],
        "entrada por grupo · balón visible · mediana": [0.4, 0.8],
        "salida · |z| con balón · mediana": [2.0, 4.0],
        "salida · cambios de signo de z por minuto evaluado": [3.0, 5.0]}}
    dentro = {"entrada por jugador · velocidad x · mediana": 1.5, "entrada por grupo · balón visible · mediana": 0.4,
              "salida · |z| con balón · mediana": 4.4, "salida · cambios de signo de z por minuto evaluado": 2.6}
    filas, salidas, entradas = cp.comparar(dentro, referencia)
    comprobar("dentro del rango ensanchado no hay nada fuera", not salidas and not entradas and len(filas) == 4)
    fuera = dict(dentro, **{"salida · |z| con balón · mediana": 4.6, "entrada por jugador · velocidad x · mediana": 0.7})
    filas, salidas, entradas = cp.comparar(fuera, referencia)
    comprobar("una salida fuera y una entrada fuera se separan",
              salidas == ["salida · |z| con balón · mediana"]
              and entradas == ["entrada por jugador · velocidad x · mediana"])
    _, salidas, _ = cp.comparar(dict(dentro, **{"salida · |z| con balón · mediana": float("nan")}), referencia)
    comprobar("un agregado que no es un número cuenta como fuera", salidas == ["salida · |z| con balón · mediana"])
    try:
        cp.comparar({"salida · |z| con balón · mediana": 3.0}, referencia)
        comprobar("un agregado que falta da error", False)
    except KeyError:
        comprobar("un agregado que falta da error", True)
    texto = "\n".join(cp.para_imprimir(*cp.comparar(fuera, referencia), referencia))
    comprobar("el texto dice que las salidas se salen", "LAS SALIDAS SE SALEN" in texto and "FUERA" in texto)
    texto = "\n".join(cp.para_imprimir(*cp.comparar(dentro, referencia), referencia))
    comprobar("y que puede seguir si caen dentro", "K2 puede seguir" in texto and "FUERA" not in texto)

    if os.path.isfile(conjunto.PESOS):
        valores = agregados.agregados(puntuar.partido_de_prueba(), fuera=None)
        comprobar("los agregados del partido inventado son números", all(isinstance(v, float) for v in valores.values()),
                  "{} agregados".format(len(valores)))
        comprobar("hay seis salidas y el resto son entradas",
                  sum(cp.es_salida(n) for n in valores) == 6 and len(valores) > 40)
        if os.path.isfile(cp.REFERENCIA):
            import json
            with open(cp.REFERENCIA, encoding="utf-8") as f:
                de_verdad = json.load(f)
            comprobar("la referencia tiene los mismos agregados que calcula el script",
                      set(de_verdad["rango"]) == set(valores))
            comprobar("los rangos de la referencia son finitos y ordenados",
                      all(np.isfinite(a) and np.isfinite(b) and a <= b for a, b in de_verdad["rango"].values()))
        else:
            print("  no está referencia_abiertos.json: se salta su comprobación")
    else:
        print("  no están los pesos del modelo: se saltan los agregados del partido inventado")

    print("\n{} comprobaciones fallan".format(len(fallos)) if fallos else "\nTodo bien.")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
