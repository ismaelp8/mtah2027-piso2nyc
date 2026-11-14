"""El perfil del balón (`perfil.py`) en los 7 partidos abiertos de la DFL, degradados como en el harness.

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del experimento 0: lo
puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

    python validation/perfil_atd/perfil_dfl.py --seco          # medida en seco (bitácora §5), antes del ATD
    python validation/perfil_atd/perfil_dfl.py --harness       # las tres condiciones de hoy del harness
    python validation/perfil_atd/perfil_dfl.py --condicion objetivo=0.15 disputas=0.5 suavizado=25

Con `--json` da la salida completa y con `--partidos J03WMX` mide un solo partido.

La degradación es la de `validation/harness/dfl.py` con sus cuatro constantes como parámetros:

- `objetivo`: fracción de los frames vivos sin balón (en el harness, 0,41);
- `disputas`: fracción de los episodios de disputa y de balón alto que se tapan (0,5);
- `media_bloque`: frames de media de los bloques al azar con que se completa el objetivo (25);
- `suavizado`: frames de la media móvil del balón; 1 es sin suavizar (en el harness, 25 en "huecos y
  suavizado").

Con los parámetros del harness da exactamente el mismo tracking que `dfl.tracking_de`: el script lo
comprueba con el primer partido antes de medir nada. Los jugadores no se degradan, como en el harness.
"""

import argparse
import collections
import json
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, AQUI)
sys.path.insert(0, ROOT)
import dfl  # noqa: E402  (añade experimento0, 1 y 2 al path)
import dfl_lector  # noqa: E402
import instrumento as ins  # noqa: E402
import perfil as pf  # noqa: E402

PARAMETROS = ("objetivo", "disputas", "media_bloque", "suavizado")
HARNESS = collections.OrderedDict([
    ("limpio", None),
    ("huecos", {"objetivo": dfl.OBJETIVO, "disputas": dfl.DISPUTAS, "media_bloque": dfl.MEDIA_BLOQUE,
                "suavizado": 1}),
    ("huecos y suavizado", {"objetivo": dfl.OBJETIVO, "disputas": dfl.DISPUTAS,
                            "media_bloque": dfl.MEDIA_BLOQUE, "suavizado": dfl.SUAVIZADO}),
])

# Medida en seco (bitácora §5): cada barrido mueve un parámetro desde la referencia.
REFERENCIA = {"objetivo": 0.2, "disputas": 0.5, "media_bloque": 25, "suavizado": 1}
BARRIDOS = (
    ("objetivo", (0.0, 0.1, 0.2, 0.3, 0.41), REFERENCIA),
    # Sin parte dirigida: la que tapa las disputas pone un suelo por debajo del cual `objetivo` no hace nada.
    ("objetivo", (0.0, 0.1, 0.2, 0.3, 0.41), dict(REFERENCIA, disputas=0.0)),
    ("disputas", (0.0, 0.25, 0.5, 0.75, 1.0), REFERENCIA),
    ("disputas", (0.0, 0.25, 0.5, 0.75, 1.0), dict(REFERENCIA, objetivo=0.1)),
    ("suavizado", (1, 5, 11, 25, 51), REFERENCIA),
)
# Qué medidas primarias mueve cada parámetro, y en qué sentido (+1 suben, −1 bajan al subir el parámetro).
RESPUESTA = {
    "objetivo": (("s_baja", +1), ("s_media", +1), ("s_alta", +1)),
    "disputas": (("disputa_pct", -1),),
    "suavizado": (("temblor_cm", -1), ("toques_por_min", -1), ("controles_por_min", -1)),
}
SUELO_TASA = 0.5  # R4: una tasa por debajo de 0,5 por minuto cuenta como 0,5


def tolerancia(clave):
    """La tolerancia de una medida primaria (bitácora §5): ("puntos", ±x) o ("cociente", factor, suelo)."""
    if clave in ("s_baja", "s_media", "s_alta"):
        return ("puntos", 5.0)
    if clave.startswith("reparto_"):
        return ("puntos", 10.0)
    if clave == "disputa_pct":
        return ("puntos", 3.0)
    if clave == "temblor_cm":
        return ("cociente", 2.0, 0.0)
    if clave in ("toques_por_min", "controles_por_min", "cambios_cercano_por_min"):
        return ("cociente", 2.0, SUELO_TASA)
    if clave.startswith("cercano_a_"):
        return ("puntos", 10.0)
    return None


def dentro(valor, referencia, tol):
    """¿`valor` está dentro de la tolerancia alrededor de `referencia`? None si falta alguno."""
    if valor is None or referencia is None or tol is None:
        return None
    if tol[0] == "puntos":
        return abs(valor - referencia) <= tol[1]
    a, b = max(valor, tol[2]), max(referencia, tol[2])
    if a <= 0 or b <= 0:
        return a == b
    return 1.0 / tol[1] <= a / b <= tol[1]


# -- la degradación del harness, con sus constantes como parámetros ---------------------------------------

def cargar(partido):
    """Un partido de la caché, sin etiquetas: el perfil no las usa."""
    datos = dfl_lector.cargar_cache(partido)
    return {"partido": partido, "indice": dfl.PARTIDOS.index(partido), "partes": datos["partes"],
            "campo": tuple(datos["meta"]["campo"])}


def degradar_parte(parte, prm, rng):
    """(parte con el balón degradado, frames vivos, frames vivos tapados solo por la parte dirigida).

    Es `dfl.degradar_parte` con las constantes como parámetros, con los mismos pasos y el mismo orden de
    sorteos. `prm=None` es "limpio": solo se tapa el balón en los `D` y en sus bordes.
    """
    estado = np.asarray(parte["estado"])
    activo = estado == 1
    x, y = np.array(parte["x"], dtype=float), np.array(parte["y"], dtype=float)
    tapado = np.convolve((~activo).astype(int), np.ones(2 * dfl.BORDE + 1, dtype=int), mode="same") > 0
    dirigida_pct = 0.0
    if prm is not None:
        prep = ins.preparar_en_juego(parte, estado)
        huecos, dirigida_pct = ins.mascara_dirigida(prep, np.asarray(parte["z"], dtype=float), activo,
                                                    prm["objetivo"], rng, fraccion=prm["disputas"],
                                                    media=prm["media_bloque"])
        if prm["suavizado"] > 1:
            x[tapado], y[tapado] = np.nan, np.nan  # el balón congelado del `D` no entra en la media
            x, y = dfl.media_movil(x, prm["suavizado"]), dfl.media_movil(y, prm["suavizado"])
        tapado = tapado | huecos
    x[tapado], y[tapado] = np.nan, np.nan
    nueva = dict(parte)
    nueva["x"], nueva["y"] = x, y
    vivos = int(activo.sum())
    return nueva, vivos, dirigida_pct * vivos / 100.0


def tracking_con(cargado, prm):
    """(Tracking del partido con el balón degradado según `prm`, frames vivos, vivos tapados por la parte
    dirigida). Mismas semillas que `dfl.tracking_de`."""
    partes, vivos, dirigida = {}, 0, 0.0
    for k in (1, 2):
        partes[k], v, d = degradar_parte(cargado["partes"][k], prm,
                                         np.random.default_rng([dfl.SEMILLA, cargado["indice"], k]))
        vivos += v
        dirigida += d
    trk = dfl.a_tracking(partes, cargado["campo"], np.random.default_rng([dfl.SEMILLA, cargado["indice"], 99]))
    return trk, vivos, dirigida


def sin_barajar(cargado):
    """El tracking del partido sin degradar y sin barajar los slots, para el agregado 7: así cada slot es
    una persona. Con el barajado del harness, la duración de los tramos y los saltos medirían el barajado
    (`dfl.MEDIA_BARAJADO`), no el tracking. El resto del perfil sale igual con y sin barajar."""
    original = dfl.barajar_slots
    dfl.barajar_slots = lambda px, py, team, rng: (px, py, team)
    try:
        trk, _, _ = tracking_con(cargado, None)
    finally:
        dfl.barajar_slots = original
    return trk


def comprobar_igual_que_el_harness(cargado):
    """Con los parámetros del harness, el tracking tiene que ser el mismo que el de `dfl.tracking_de`."""
    for nombre, prm in HARNESS.items():
        suyo = dfl.tracking_de(cargado, nombre)
        mio, _, _ = tracking_con(cargado, prm)
        iguales = (all(np.array_equal(getattr(suyo, c), getattr(mio, c), equal_nan=True)
                       for c in ("bx", "by", "px", "py"))
                   and np.array_equal(suyo.team, mio.team) and suyo.blocks == mio.blocks
                   and suyo.pitch == mio.pitch and suyo.fps == mio.fps)
        if not iguales:
            raise AssertionError("la degradación parametrizada no reproduce la condición '{}' del harness".format(nombre))


# -- medir ---------------------------------------------------------------------------------------------

def nombre_de(prm):
    if prm is None:
        return "limpio"
    return "objetivo {:g} · disputas {:g} · bloques {:g} · suavizado {:g}".format(
        *(prm[p] for p in PARAMETROS))


def medir(partidos, condiciones, avisar=None):
    """Perfil de cada condición, con los partidos juntos y uno a uno, y el de los jugadores (sin degradar ni
    barajar: cada slot es una persona).

    `condiciones` es {nombre: prm}. Devuelve {"condiciones": {nombre: {...}}, "jugadores": {...}}.
    """
    parciales = collections.defaultdict(list)
    por_partido = collections.defaultdict(dict)
    dirigida = collections.defaultdict(lambda: [0, 0.0])
    jugadores = []
    for i, partido in enumerate(partidos):
        inicio = time.time()
        cargado = cargar(partido)
        if i == 0:
            comprobar_igual_que_el_harness(cargado)
        for nombre, prm in condiciones.items():
            trk, vivos, tapados = tracking_con(cargado, prm)
            m = pf.medidas(trk, jugadores=False)
            parciales[nombre].append(m)
            por_partido[nombre][partido] = pf.primarias(pf.resumir([m]))
            dirigida[nombre][0] += vivos
            dirigida[nombre][1] += tapados
        jugadores.append(pf.medidas(sin_barajar(cargado), jugadores=True))
        if avisar:
            avisar("hecho {} en {:.0f} s".format(partido, time.time() - inicio))
    salida = {"partidos": list(partidos), "condiciones": collections.OrderedDict()}
    for nombre, prm in condiciones.items():
        juntos = pf.resumir(parciales[nombre])
        vivos, tapados = dirigida[nombre]
        salida["condiciones"][nombre] = {
            "parametros": prm, "juntos": juntos, "primarias": pf.primarias(juntos),
            "primarias_por_partido": por_partido[nombre],
            "vivos_tapados_por_la_parte_dirigida_pct": 100.0 * tapados / vivos if vivos else None}
    juntos = pf.resumir(jugadores)
    salida["jugadores"] = {"7_jugadores": juntos["7_jugadores"], "primarias": {
        k: v for k, v in pf.primarias(juntos).items() if k.startswith(("localizados", "tramo", "temblor_jug"))}}
    return salida


# -- salida --------------------------------------------------------------------------------------------

def num(valor, decimales=1):
    return "–" if valor is None else "{:.{}f}".format(valor, decimales).replace(".", ",")


def con_rango(cond, clave, decimales=1):
    """Valor de los partidos juntos y, entre corchetes, el mínimo y el máximo por partido."""
    valor = cond["primarias"].get(clave)
    por = [p.get(clave) for p in cond["primarias_por_partido"].values()]
    por = [v for v in por if v is not None]
    if valor is None:
        return "–"
    if len(por) > 1:
        return "{} [{}–{}]".format(num(valor, decimales), num(min(por), decimales), num(max(por), decimales))
    return num(valor, decimales)


def ordenada(valores, sentido):
    """¿Los valores suben (sentido +1) o bajan (−1) en cada paso? None si falta alguno."""
    if any(v is None for v in valores):
        return None
    return all((b - a) * sentido > 0 for a, b in zip(valores, valores[1:]))


COLUMNAS = (("s_baja", "s baja (%)", 1), ("s_media", "s media (%)", 1), ("s_alta", "s alta (%)", 1),
            ("disputa_pct", "disputas (%)", 1), ("temblor_cm", "temblor (cm)", 2),
            ("toques_por_min", "toques/min", 1), ("controles_por_min", "controles/min", 1),
            ("cercano_a_1_m_pct", "a 1 m (%)", 1), ("cercano_a_3_m_pct", "a 3 m (%)", 1),
            ("cambios_cercano_por_min", "cambios del más cercano/min", 1))


def tabla_condiciones(salida, nombres):
    lineas = ["| condición | parte dirigida (% de los vivos) | " + " | ".join(t for _, t, _ in COLUMNAS) + " |",
              "|---" * (len(COLUMNAS) + 2) + "|"]
    for nombre in nombres:
        cond = salida["condiciones"][nombre]
        lineas.append("| {} | {} | {} |".format(nombre, num(cond["vivos_tapados_por_la_parte_dirigida_pct"]),
                                                 " | ".join(con_rango(cond, c, d) for c, _, d in COLUMNAS)))
    return "\n".join(lineas)


def tabla_barrido(salida, parametro, valores, base):
    nombres = [nombre_de(dict(base, **{parametro: v})) for v in valores]
    respuesta = RESPUESTA[parametro]
    lineas = ["**{}**, desde {}".format(parametro, nombre_de(base)), "",
              "| {} | ".format(parametro) + " | ".join(c for c, _ in respuesta) + " | parte dirigida (% de los vivos) |",
              "|---" * (len(respuesta) + 2) + "|"]
    for v, nombre in zip(valores, nombres):
        cond = salida["condiciones"][nombre]
        lineas.append("| {:g} | {} | {} |".format(v, " | ".join(con_rango(cond, c, 2) for c, _ in respuesta),
                                                  num(cond["vivos_tapados_por_la_parte_dirigida_pct"])))
    veredictos = []
    for clave, sentido in respuesta:
        serie = [salida["condiciones"][n]["primarias"][clave] for n in nombres]
        ok = ordenada(serie, sentido)
        veredictos.append("sí" if ok else "no" if ok is not None else "–")
    lineas.append("| ¿ordenada? | " + " | ".join(veredictos) + " | |")
    return "\n".join(lineas)


def tabla_tolerancia(salida, nombre):
    """¿Algún partido queda fuera de la tolerancia alrededor de los 7 juntos? Entonces la medida no
    distingue al ATD de un partido cualquiera y pasa a descriptiva (bitácora §5)."""
    cond = salida["condiciones"][nombre]
    lineas = ["| medida | 7 juntos [mín–máx] | tolerancia | partidos fuera | ¿decide? |", "|---|---|---|---|---|"]
    for clave, valor in cond["primarias"].items():
        tol = tolerancia(clave)
        if tol is None or clave.endswith("_todo"):
            continue
        fuera = [p for p, x in cond["primarias_por_partido"].items() if dentro(x.get(clave), valor, tol) is False]
        texto = "±{:g} puntos".format(tol[1]) if tol[0] == "puntos" else "de ×1/{0:g} a ×{0:g}".format(tol[1])
        decide = "–" if valor is None else ("no: pasa a descriptiva" if fuera else "sí")
        lineas.append("| {} | {} | {} | {} | {} |".format(clave, con_rango(cond, clave, 2), texto, len(fuera), decide))
    return "\n".join(lineas)


def condiciones_en_seco():
    condiciones = collections.OrderedDict()
    for parametro, valores, base in BARRIDOS:
        for v in valores:
            prm = dict(base, **{parametro: v})
            condiciones[nombre_de(prm)] = prm
    return condiciones


def leer_condicion(textos):
    prm = dict(REFERENCIA)
    for texto in textos:
        clave, _, valor = texto.partition("=")
        if clave not in PARAMETROS:
            raise SystemExit("parámetro desconocido: {} (son {})".format(clave, ", ".join(PARAMETROS)))
        prm[clave] = float(valor) if clave in ("objetivo", "disputas") else int(valor)
    return prm


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), choices=list(dfl.PARTIDOS))
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--seco", action="store_true", help="la medida en seco de la bitácora (§5)")
    grupo.add_argument("--harness", action="store_true", help="las tres condiciones de hoy del harness")
    grupo.add_argument("--condicion", nargs="+", metavar="PARAMETRO=VALOR",
                       help="una condición; lo que no se dé, como la referencia ({})".format(nombre_de(REFERENCIA)))
    ap.add_argument("--json", action="store_true", help="la salida completa en JSON")
    args = ap.parse_args()

    if args.seco:
        condiciones = condiciones_en_seco()
    elif args.harness:
        condiciones = collections.OrderedDict((n, p) for n, p in HARNESS.items())
    else:
        prm = leer_condicion(args.condicion)
        condiciones = collections.OrderedDict([(nombre_de(prm), prm)])
    inicio = time.time()
    salida = medir(args.partidos, condiciones, avisar=lambda t: print(t, file=sys.stderr))
    if args.json:
        print(json.dumps(pf.para_imprimir(salida), ensure_ascii=False, indent=1))
        return
    print("partidos: {} · tiempo: {:.0f} s · la degradación parametrizada reproduce las tres condiciones del "
          "harness (comprobado con {})".format(len(args.partidos), time.time() - inicio, args.partidos[0]))
    print()
    if args.seco:
        for parametro, valores, base in BARRIDOS:
            print(tabla_barrido(salida, parametro, valores, base))
            print()
        print("**Tolerancia por partido**, en la referencia ({})".format(nombre_de(REFERENCIA)))
        print()
        print(tabla_tolerancia(salida, nombre_de(REFERENCIA)))
    else:
        print(tabla_condiciones(salida, list(condiciones)))
        for nombre in condiciones:
            print()
            print("**Tolerancia por partido**, en {}".format(nombre))
            print()
            print(tabla_tolerancia(salida, nombre))
    print()
    print("**Jugadores** (sin degradar ni barajar los slots, los 7 juntos): "
          + json.dumps(pf.para_imprimir(salida["jugadores"]["primarias"]), ensure_ascii=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
