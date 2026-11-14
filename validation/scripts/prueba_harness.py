"""Prueba el fichero de versiones del harness de la DFL (`puntuar.py --versiones`) sin cargar ningún partido.

    python validation/scripts/prueba_harness.py

Comprueba que el ejemplo (`validation/harness/versiones/ejemplo.json`) se lee bien y que cada errata del
fichero da error al leerlo, antes de medir nada. Que una versión del fichero dé los mismos números que la
misma versión escrita en `VERSIONES` se comprobó con la DFL (README del harness).

No usa datos del partido ni de la DFL. Sale con código 1 si falla alguna comprobación. Claude puede
ejecutarlo (validation/README.md).
"""

import functools
import hashlib
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import puntuar  # noqa: E402
from possession import ball, candidates, dead_state, temporal, tracking  # noqa: E402

EJEMPLO = os.path.join(ROOT, "validation", "harness", "versiones", "ejemplo.json")
fallos = []


def comprobar(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(nombre)


def da_error(llamada):
    try:
        llamada()
    except ValueError:
        return True
    return False


def escribir(carpeta, texto, nombre="versiones.json", bom=False):
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "w", encoding="utf-8-sig" if bom else "utf-8", newline="\n") as handle:
        handle.write(texto)
    return ruta


def comprobar_ejemplo():
    print("El ejemplo")
    versiones, contenido, huella = puntuar.leer_versiones(EJEMPLO)
    comprobar("el control va siempre delante y luego las del fichero, en su orden",
              list(versiones) == [puntuar.CONTROL] + list(contenido)
              and versiones[puntuar.CONTROL] is puntuar.VERSIONES[puntuar.CONTROL])
    v0 = versiones["Viterbi, coste 25 (v0)"]
    comprobar("una versión vacía es el pipeline tal cual", v0 == {"tipo": "pipeline", "params": None, "piezas": {}})
    comprobar("«params» pasa al decodificador tal cual",
              versiones["Viterbi, coste 50"]["params"] == {"switch": 50, "to_dead": 50, "from_dead": 50})
    comprobar("las piezas escritas una a una son las funciones de la entrega",
              versiones["v0 pieza a pieza"]["piezas"] == {"ball": ball.clean, "candidates": candidates.evidence,
                                                         "dead_state": dead_state.evidence,
                                                         "temporal": temporal.decode})
    with open(EJEMPLO, "rb") as handle:
        comprobar("la huella es el sha256 del fichero", huella == hashlib.sha256(handle.read()).hexdigest())


def comprobar_opciones(carpeta):
    print("Opciones de una función")
    llamadas = []

    def evidencia_prueba(trk, peso=1.0):
        llamadas.append(peso)
        score, allowed = tracking.no_evidence(len(trk.bx))
        return score * peso, allowed

    candidates.evidencia_prueba = evidencia_prueba
    try:
        ruta = escribir(carpeta, json.dumps({"con peso": {"piezas": {"candidates": {
            "funcion": "evidencia_prueba", "opciones": {"peso": 3.0}}}}}))
        version = puntuar.leer_versiones(ruta)[0]["con peso"]
        funcion = version["piezas"]["candidates"]
        comprobar("las opciones se fijan con la función", isinstance(funcion, functools.partial)
                  and funcion.func is evidencia_prueba and funcion.keywords == {"peso": 3.0})
        funcion(tracking.Tracking(*([None] * len(tracking.Tracking._fields)))._replace(bx=[0.0] * 5))
        comprobar("y llegan a la función al llamarla", llamadas == [3.0])
        ruta = escribir(carpeta, json.dumps({"x": {"piezas": {"candidates": {
            "funcion": "evidencia_prueba", "opciones": {"pesso": 3.0}}}}}))
        comprobar("una opción que la función no tiene da error", da_error(lambda: puntuar.leer_versiones(ruta)))
    finally:
        del candidates.evidencia_prueba


def comprobar_erratas(carpeta):
    print("Erratas que dan error al leer el fichero, antes de medir")
    casos = [
        ("no es JSON", "{\"v\": {}"),
        ("no es un objeto", "[1, 2]"),
        ("no tiene versiones", "{}"),
        ("una versión repetida", "{\"v\": {}, \"v\": {}}"),
        ("una clave repetida dentro de una versión", "{\"v\": {\"params\": {\"switch\": 1, \"switch\": 2}}}"),
        ("una versión que se llama como el control", json.dumps({puntuar.CONTROL: {}})),
        ("una versión que no es un objeto", "{\"v\": 3}"),
        ("una clave desconocida", "{\"v\": {\"parametros\": {\"switch\": 50}}}"),
        ("un tipo desconocido", "{\"v\": {\"tipo\": \"viterbi\"}}"),
        ("un tipo que no es un texto", "{\"v\": {\"tipo\": [\"control\"]}}"),
        ("una nota que no es un texto", "{\"v\": {\"nota\": 3}}"),
        ("un control sin ventana", "{\"v\": {\"tipo\": \"control\"}}"),
        ("un control con ventana negativa", "{\"v\": {\"tipo\": \"control\", \"ventana\": -1}}"),
        ("un control con params", "{\"v\": {\"tipo\": \"control\", \"ventana\": 50, \"params\": {}}}"),
        ("una ventana en una versión del pipeline", "{\"v\": {\"ventana\": 50}}"),
        ("«params» que no es un objeto", "{\"v\": {\"params\": [50]}}"),
        ("un parámetro del decodificador mal escrito", "{\"v\": {\"params\": {\"swich\": 50}}}"),
        ("un coste negativo", "{\"v\": {\"params\": {\"switch\": -1}}}"),
        ("un coste que no es un número", "{\"v\": {\"params\": {\"switch\": \"alto\"}}}"),
        ("«piezas» que no es un objeto", "{\"v\": {\"piezas\": [\"candidates\"]}}"),
        ("una pieza que no existe", "{\"v\": {\"piezas\": {\"decoder\": \"decode\"}}}"),
        ("una función que no existe", "{\"v\": {\"piezas\": {\"candidates\": \"evidence_n9\"}}}"),
        ("una función de otro módulo", "{\"v\": {\"piezas\": {\"candidates\": \"decode\"}}}"),
        ("una función que no es un texto", "{\"v\": {\"piezas\": {\"candidates\": {\"funcion\": 3}}}}"),
        ("una clave rara en una pieza", "{\"v\": {\"piezas\": {\"candidates\": {\"function\": \"evidence\"}}}}"),
        ("opciones que no son un objeto",
         "{\"v\": {\"piezas\": {\"candidates\": {\"funcion\": \"evidence\", \"opciones\": [1]}}}}"),
        ("opciones que la función no acepta",
         "{\"v\": {\"piezas\": {\"candidates\": {\"funcion\": \"evidence\", \"opciones\": {\"radio\": 2}}}}}"),
        ("«params» como opción del decodificador",
         "{\"v\": {\"piezas\": {\"temporal\": {\"opciones\": {\"params\": {}}}}}}"),
    ]
    for nombre, texto in casos:
        ruta = escribir(carpeta, texto)
        comprobar(nombre, da_error(lambda: puntuar.leer_versiones(ruta)))
    comprobar("un fichero que no existe da error",
              not os.path.exists(os.path.join(carpeta, "no_existe.json"))
              and _da_oserror(lambda: puntuar.leer_versiones(os.path.join(carpeta, "no_existe.json"))))


def _da_oserror(llamada):
    try:
        llamada()
    except OSError:
        return True
    return False


def comprobar_formato(carpeta):
    print("Formato")
    ruta = escribir(carpeta, "{\"v\": {\"tipo\": \"control\", \"ventana\": 125, \"nota\": \"baseline\"}}", bom=True)
    versiones = puntuar.leer_versiones(ruta)[0]
    comprobar("se lee con BOM (como lo guarda el Bloc de notas)", versiones["v"] == {"tipo": "control", "ventana": 125})
    ruta = escribir(carpeta, "{\"v\": {\"tipo\": \"pipeline\", \"params\": {\"switch\": 40.5}}}")
    comprobar("«tipo»: «pipeline» se puede escribir", puntuar.leer_versiones(ruta)[0]["v"]["params"] == {"switch": 40.5})


def main():
    carpeta = tempfile.mkdtemp(prefix="mtah_prueba_harness_")
    try:
        comprobar_ejemplo()
        comprobar_opciones(carpeta)
        comprobar_erratas(carpeta)
        comprobar_formato(carpeta)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    print()
    if fallos:
        print("FALLAN {} comprobaciones".format(len(fallos)))
        sys.exit(1)
    print("TODO BIEN")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
