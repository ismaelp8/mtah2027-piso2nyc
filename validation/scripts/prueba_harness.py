"""Prueba el fichero de versiones del harness de la DFL (`puntuar.py --versiones`) sin cargar ningún partido.

    python validation/scripts/prueba_harness.py

Comprueba que el ejemplo (`validation/harness/versiones/ejemplo.json`) se lee bien y que cada errata del
fichero da error al leerlo, antes de medir nada. Que una versión del fichero dé los mismos números que la
misma versión escrita en `VERSIONES` se comprobó con la DFL (README del harness). También prueba la regla
de lectura de `--eventos` con intervalos inventados.

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

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import puntuar  # noqa: E402
from possession import aprendida, ball, candidates, dead_state, temporal, tracking  # noqa: E402

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
        crudo = handle.read()
    comprobar("la huella no depende de los saltos de línea, el BOM ni el sangrado",
              huella == puntuar.huella_de(json.loads(crudo.decode("utf-8")))
              and huella != hashlib.sha256(crudo).hexdigest() and _huella_retocada(crudo) == huella)


def _huella_retocada(crudo):
    """La huella del ejemplo guardado con CRLF, BOM y otro sangrado."""
    carpeta = tempfile.mkdtemp(prefix="mtah_prueba_harness_")
    try:
        texto = json.dumps(json.loads(crudo.decode("utf-8")), ensure_ascii=False, indent=4).replace("\n", "\r\n")
        return puntuar.leer_versiones(escribir(carpeta, texto, bom=True))[2]
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


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
        comprobar("y llegan a la función: la prueba con el partido inventado la llama una vez", llamadas == [3.0])
        ruta = escribir(carpeta, json.dumps({"solo opciones": {"piezas": {"candidates": {"opciones": {}}}}}))
        version = puntuar.leer_versiones(ruta)[0]["solo opciones"]
        comprobar("sin «funcion», la de siempre", version["piezas"]["candidates"] is candidates.evidence)
        ruta = escribir(carpeta, json.dumps({"x": {"piezas": {"candidates": {
            "funcion": "evidencia_prueba", "opciones": {"pesso": 3.0}}}}}))
        comprobar("una opción que la función no tiene da error", da_error(lambda: puntuar.leer_versiones(ruta)))
    finally:
        del candidates.evidencia_prueba


def comprobar_dejar_fuera(carpeta):
    print("Otro módulo (aprendida) y dejar fuera el partido que se puntúa")
    llamadas = []

    def evidencia_prueba(trk, fuera=None, peso=1.0):
        llamadas.append(fuera)
        score, allowed = tracking.no_evidence(len(trk.bx))
        return score * peso, allowed

    aprendida.evidencia_prueba = evidencia_prueba
    try:
        ruta = escribir(carpeta, json.dumps({"main": {}, "deja fuera": {"piezas": {"candidates": {
            "funcion": "aprendida.evidencia_prueba", "opciones": {"peso": 2.0}, "dejar_fuera": True}}},
            "sin dejar fuera": {"piezas": {"candidates": "aprendida.evidencia_prueba"}}}))
        versiones = puntuar.leer_versiones(ruta)[0]
        deja, sin = versiones["deja fuera"], versiones["sin dejar fuera"]
        comprobar("«modulo.funcion» toma la función de ese módulo, con sus opciones",
                  isinstance(deja["piezas"]["candidates"], functools.partial)
                  and deja["piezas"]["candidates"].func is evidencia_prueba
                  and deja["piezas"]["candidates"].keywords == {"peso": 2.0}
                  and sin["piezas"]["candidates"] is evidencia_prueba)
        comprobar("la versión dice qué piezas dejan fuera el partido; las demás no llevan «fuera»",
                  deja.get("fuera") == ["candidates"] and "fuera" not in sin and "fuera" not in versiones["main"])
        comprobar("al leer, la versión se prueba con fuera=None (la entrega) y con cada partido de la DFL",
                  llamadas == [None] + list(puntuar.dfl.PARTIDOS) + [None], str(llamadas))
        comprobar("la versión de main sigue siendo la vacía", puntuar.version_de_main(versiones) == "main")
        del llamadas[:]
        trk = puntuar.partido_de_prueba()
        gt = np.full(len(trk.bx), tracking.X, dtype=np.int8)
        for inicio, fin in trk.blocks:
            gt[inicio:fin] = tracking.H
        puntuar.ejecutar(deja, trk, gt, "oraculo", "J03WMX")
        puntuar.ejecutar(sin, trk, gt, "oraculo", "J03WMX")
        comprobar("al puntuar, solo la pieza que deja fuera recibe el partido", llamadas == ["J03WMX", None],
                  str(llamadas))
        ruta = escribir(carpeta, json.dumps({"v": {"piezas": {"candidates": {
            "funcion": "aprendida.evidencia_prueba", "opciones": {"fuera": "J03WMX"}, "dejar_fuera": True}}}}))
        comprobar("con «dejar_fuera», «fuera» en las opciones da error", da_error(lambda: puntuar.leer_versiones(ruta)))
    finally:
        del aprendida.evidencia_prueba


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
        ("«piezas» vacías que no son un objeto ([])", "{\"v\": {\"piezas\": []}}"),
        ("«piezas» a false", "{\"v\": {\"piezas\": false}}"),
        ("«opciones» a false", "{\"v\": {\"piezas\": {\"candidates\": {\"opciones\": false}}}}"),
        ("una versión que se llama como la fila de dejar uno fuera",
         json.dumps({puntuar.DEJAR_UNO_FUERA_FICHERO: {}})),
        ("la otra fila de dejar uno fuera", json.dumps({puntuar.DEJAR_UNO_FUERA: {}})),
        ("NaN como coste", "{\"v\": {\"params\": {\"switch\": NaN}}}"),
        ("Infinity como coste", "{\"v\": {\"params\": {\"switch\": Infinity}}}"),
        ("1e999 como coste (se leería como infinito)", "{\"v\": {\"params\": {\"switch\": 1e999}}}"),
        ("una función que el módulo importa pero no es una pieza (no_evidence)",
         "{\"v\": {\"piezas\": {\"candidates\": \"no_evidence\"}}}"),
        ("una función del módulo que devuelve otra cosa (nearest_team)",
         "{\"v\": {\"piezas\": {\"candidates\": \"nearest_team\"}}}"),
        ("algo que no es una función (__class__)", "{\"v\": {\"piezas\": {\"candidates\": \"__class__\"}}}"),
        ("una función de un módulo que la pieza no admite (temporal.decode)",
         "{\"v\": {\"piezas\": {\"candidates\": \"temporal.decode\"}}}"),
        ("un módulo que no existe", "{\"v\": {\"piezas\": {\"candidates\": \"otro.evidence\"}}}"),
        ("una función de aprendida en otra pieza",
         "{\"v\": {\"piezas\": {\"dead_state\": \"aprendida.evidence_b1\"}}}"),
        ("una función de aprendida que no existe", "{\"v\": {\"piezas\": {\"candidates\": \"aprendida.evidence_b9\"}}}"),
        ("«dejar_fuera» que no es true o false",
         "{\"v\": {\"piezas\": {\"candidates\": {\"funcion\": \"evidence\", \"dejar_fuera\": 1}}}}"),
        ("«dejar_fuera» con una función que no tiene «fuera» (candidates.evidence)",
         "{\"v\": {\"piezas\": {\"candidates\": {\"funcion\": \"evidence\", \"dejar_fuera\": true}}}}"),
    ]
    for nombre, texto in casos:
        ruta = escribir(carpeta, texto)
        comprobar(nombre, da_error(lambda: puntuar.leer_versiones(ruta)))

    def escribe_en_el_tracking(trk):
        trk.bx[0] = 0.0
        return tracking.no_evidence(len(trk.bx))

    def decodificador_corto(score, allowed, blocks, params):
        return np.zeros(10, dtype=np.int8)

    candidates.escribe_en_el_tracking = escribe_en_el_tracking
    temporal.decodificador_corto = decodificador_corto
    try:
        ruta = escribir(carpeta, "{\"v\": {\"piezas\": {\"candidates\": \"escribe_en_el_tracking\"}}}")
        comprobar("una pieza que escribe en el tracking (el harness se lo da a todas las versiones)",
                  da_error(lambda: puntuar.leer_versiones(ruta)))
        ruta = escribir(carpeta, "{\"v\": {\"piezas\": {\"temporal\": \"decodificador_corto\"}}}")
        comprobar("un decodificador que no da una etiqueta por frame", da_error(lambda: puntuar.leer_versiones(ruta)))
    finally:
        del candidates.escribe_en_el_tracking, temporal.decodificador_corto
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


def comprobar_lectura_eventos():
    print("Regla de lectura de los eventos humanos (README del harness)")

    def lectura(*intervalos):
        return puntuar.lectura_eventos({t: {"diferencia": 0.0, "intervalo": list(i) if i else None}
                                        for t, i in zip(puntuar.LEIDOS, intervalos)})

    comprobar("uno por encima de cero y ninguno por debajo: mejora", lectura((1, 5), (-2, 3), (-1, 1)) == "mejora")
    comprobar("uno por debajo y ninguno por encima: empeora", lectura((-5, -1), (-2, 3), (-1, 1)) == "empeora")
    comprobar("uno por encima y otro por debajo: compromiso", lectura((1, 5), (-2, 3), (-4, -1)) == "compromiso")
    comprobar("ninguno se separa de cero: no concluye", lectura((-1, 5), (-2, 3), (0, 1)) == "no concluye")
    comprobar("sin bootstrap no se lee", lectura(None, None, None) == "sin intervalo")
    tipos = np.repeat(np.arange(len(puntuar.TIPOS_EVENTO)), 50)
    a = np.ones(len(tipos), bool)
    b = a.copy()
    b[tipos == puntuar.TIPOS_EVENTO.index("duelo sin cambio")] = False
    difs = puntuar.diferencias_eventos(a, b, tipos, 200)
    comprobar("la diferencia y su intervalo salen en puntos y por tipo",
              difs["duelo sin cambio"]["diferencia"] == 100.0 and difs["duelo sin cambio"]["intervalo"] == [100.0, 100.0]
              and difs["recuperación"]["diferencia"] == 0.0 and puntuar.lectura_eventos(difs) == "mejora")
    comprobar("el bootstrap da lo mismo dos veces", difs == puntuar.diferencias_eventos(a, b, tipos, 200))
    versiones = puntuar.leer_versiones(EJEMPLO)[0]
    comprobar("la versión de main es la primera del pipeline sin params ni piezas",
              puntuar.version_de_main(versiones) == "Viterbi, coste 25 (v0)"
              and puntuar.version_de_main({"a": {"tipo": "pipeline", "params": {}, "piezas": {}}}) == "a"
              and puntuar.version_de_main(puntuar.VERSIONES) == "Viterbi, coste 25 (v0)")


MAX_BYTES = 20000  # un fichero de versiones ocupa unos cientos de bytes; un volcado por frame, megas


def comprobar_carpeta():
    print("Todo lo que hay en validation/harness/versiones/ es un fichero de versiones pequeño")
    carpeta = os.path.dirname(EJEMPLO)
    for nombre in sorted(os.listdir(carpeta)):
        ruta = os.path.join(carpeta, nombre)
        pequeño = nombre.endswith(".json") and os.path.getsize(ruta) <= MAX_BYTES
        comprobar(nombre, pequeño and not da_error(lambda: puntuar.leer_versiones(ruta)),
                  "" if pequeño else "no es un .json de menos de {} bytes".format(MAX_BYTES))


def main():
    carpeta = tempfile.mkdtemp(prefix="mtah_prueba_harness_")
    try:
        comprobar_carpeta()
        comprobar_ejemplo()
        comprobar_opciones(carpeta)
        comprobar_dejar_fuera(carpeta)
        comprobar_erratas(carpeta)
        comprobar_formato(carpeta)
        comprobar_lectura_eventos()
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
