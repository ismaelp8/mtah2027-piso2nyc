"""Harness de la DFL: puntúa el pipeline (possession/) en los 7 partidos abiertos de la Bundesliga.

    python validation/harness/puntuar.py                      # los 7 partidos: medio minuto
    python validation/harness/puntuar.py --partidos J03WMX    # un partido, para probar
    python validation/harness/puntuar.py --json               # la salida completa, en JSON
    python validation/harness/puntuar.py --versiones validation/harness/versiones/ejemplo.json
    python validation/harness/puntuar.py --eventos            # además, los eventos humanos (descriptivo)

Ejecuta las mismas piezas que el partido (`possession.pipeline.run`) sobre el tracking de la DFL en el
formato común (`dfl.py`) y las puntúa con el scorer oficial (`evaluation/possession_metrics.py`). Son
datos abiertos de otros partidos: lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Cómo se mide:

- con las dos convenciones de etiquetas ("flag" y "control") y en tres condiciones del balón;
- frente al control, que es el baseline oficial: jugador más cercano y voto por mayoría de ±50 frames;
- con el `D` copiado de las etiquetas (`D` oráculo) para todos, el control incluido. La DFL congela el
  balón mientras está muerto y hay que taparlo; así «no hay balón» casi equivale a «`D`», cosa que en el
  ATD no pasa. Con `--d propio` cada versión pone su `D`, pero ese número no sirve para decidir;
- `spellF1` con los 7 partidos juntos (sumando los recuentos de posesiones de cada uno), por partido, y
  la diferencia con el control con un intervalo por bootstrap pareado sobre las posesiones reales.

Cuándo gana un candidato (docs/investigacion_metodos.md §5.8): gana en 6 de 7 partidos o más, la
diferencia es de 0,03 o más y su intervalo no incluye el cero, y todo eso se mantiene en las tres
condiciones y con las dos convenciones.

Las versiones que se puntúan son las de `VERSIONES`, o las de un fichero JSON con `--versiones` (el
README dice cómo se escribe). Para probar una versión nueva no hace falta tocar este fichero.
"""

import argparse
import collections
import functools
import hashlib
import inspect
import json
import os
import subprocess
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import dfl  # noqa: E402
import possession_metrics as pm  # noqa: E402
from possession import aprendida, ball, candidates, dead_state, pipeline, temporal, tracking  # noqa: E402
from starter import baseline  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
SEMILLA_BOOTSTRAP = 0
PERCENTILES = (5, 95)
EMPATE = 0.03  # por debajo de esta diferencia de spellF1, empate (§5.8)
MIN_PARTIDOS = 6  # de 7: en cuántos tiene que ganar un candidato
CONTROL = "control: voto ±50"

# Versiones que se puntúan. "control" es el baseline oficial; "pipeline" es possession.pipeline.run con
# esos parámetros del decodificador (None son los que trae por defecto).
VERSIONES = collections.OrderedDict([
    (CONTROL, {"tipo": "control", "ventana": 50}),
    ("Viterbi, coste 12", {"tipo": "pipeline", "params": {"switch": 12.0, "to_dead": 12.0, "from_dead": 12.0}}),
    ("Viterbi, coste 25 (v0)", {"tipo": "pipeline", "params": None}),
    ("Viterbi, coste 50", {"tipo": "pipeline", "params": {"switch": 50.0, "to_dead": 50.0, "from_dead": 50.0}}),
    ("Viterbi, coste 100", {"tipo": "pipeline", "params": {"switch": 100.0, "to_dead": 100.0, "from_dead": 100.0}}),
])
DEJAR_UNO_FUERA = "Viterbi, coste elegido dejando un partido fuera"  # la fila con las versiones de arriba
DEJAR_UNO_FUERA_FICHERO = "elegida dejando un partido fuera"  # la misma fila con las de `--versiones`


# -- versiones de un fichero (--versiones) -------------------------------------------------------------

MODULOS = {"ball": ball, "candidates": candidates, "dead_state": dead_state, "temporal": temporal}
# Otros módulos de los que una pieza puede tomar su función, escrita "modulo.funcion" (decisión de Ismael,
# 14/11): la apuesta B vive en possession/aprendida.py para no tocar candidates.py, que es de Antonio.
OTROS_MODULOS = {"candidates": {"aprendida": aprendida}}
CLAVES = {"pipeline": {"tipo", "nota", "params", "piezas"}, "control": {"tipo", "nota", "ventana"}}
RESERVADOS = (CONTROL, DEJAR_UNO_FUERA, DEJAR_UNO_FUERA_FICHERO)  # nombres de filas que pone el harness
FRAMES_PRUEBA = 1500  # el partido inventado con el que se prueba cada versión al leer el fichero (1 min)
SEMILLA_PRUEBA = 20261114


def leer_versiones(ruta):
    """Las versiones de un fichero JSON, con el control delante. Devuelve (versiones, contenido, huella).

    Comprueba todo lo que puede antes de cargar ningún partido: claves, piezas, funciones y opciones, y
    ejecuta cada versión sobre un partido inventado (`partido_de_prueba`). Cualquier errata da error con la
    ruta y la versión.
    """
    def sin_repetidas(pares):
        objeto = collections.OrderedDict()
        for clave, valor in pares:
            if clave in objeto:
                raise ValueError("{}: la clave «{}» está repetida".format(ruta, clave))
            objeto[clave] = valor
        return objeto

    def sin_constantes(texto):  # json de Python acepta NaN e Infinity; el JSON de verdad, no
        raise ValueError("{}: «{}» no vale en el fichero".format(ruta, texto))

    with open(ruta, "rb") as handle:
        crudo = handle.read()
    def numero_finito(texto):  # 1e999 se leería como infinito sin pasar por parse_constant
        valor = float(texto)
        if not np.isfinite(valor):
            raise ValueError("{}: «{}» no es un número finito".format(ruta, texto))
        return valor

    contenido = json.loads(crudo.decode("utf-8-sig"), object_pairs_hook=sin_repetidas,
                           parse_constant=sin_constantes, parse_float=numero_finito)
    if not isinstance(contenido, dict) or not contenido:
        raise ValueError("{}: tiene que ser un objeto JSON con al menos una versión".format(ruta))
    versiones = collections.OrderedDict([(CONTROL, VERSIONES[CONTROL])])
    for nombre, spec in contenido.items():
        if nombre in RESERVADOS:
            raise ValueError("{}: «{}» es el nombre de una fila del harness; ponle otro".format(ruta, nombre))
        versiones[nombre] = version_de(spec, "{}, versión «{}»".format(ruta, nombre))
    return versiones, contenido, huella_de(contenido)


def partido_de_prueba():
    """Un `Tracking` inventado de 1 minuto, 11 contra 11 y el balón con huecos, de solo lectura.

    Cada versión del fichero se ejecuta sobre él al leerlo: una errata en `params`, una función que no es
    una pieza o una pieza que escribe en el tracking fallan aquí, antes de medir nada.
    """
    rng = np.random.default_rng(SEMILLA_PRUEBA)
    largo, ancho = 105.0, 68.0
    n, por_equipo = FRAMES_PRUEBA, 11
    px = np.clip(rng.uniform(5, largo - 5, 2 * por_equipo) + np.cumsum(rng.normal(0, 0.15, (n, 2 * por_equipo)), 0),
                 0, largo).astype(np.float32)
    py = np.clip(rng.uniform(5, ancho - 5, 2 * por_equipo) + np.cumsum(rng.normal(0, 0.15, (n, 2 * por_equipo)), 0),
                 0, ancho).astype(np.float32)
    bx = np.clip(largo / 2 + np.cumsum(rng.normal(0, 0.4, n)), 0, largo)
    by = np.clip(ancho / 2 + np.cumsum(rng.normal(0, 0.4, n)), 0, ancho)
    sin_balon = np.repeat(rng.random(n // 25) < 0.4, 25)
    bx[sin_balon], by[sin_balon] = np.nan, np.nan
    # Como en la DFL y el ATD: slots vacíos (suplentes) y un tramo sin nada (el hueco entre partes).
    vacios = np.full((n, 2), np.nan, dtype=np.float32)
    px, py = np.hstack([px, vacios]), np.hstack([py, vacios])
    px[700:800], py[700:800], bx[700:800], by[700:800] = np.nan, np.nan, np.nan, np.nan
    team = np.repeat(np.array([0, 1, 0, 1], dtype=np.int8), [por_equipo, por_equipo, 1, 1])
    trk = tracking.Tracking(bx, by, px, py, team, (largo, ancho), ((100, 650), (850, n - 100)), 25)
    return solo_lectura(trk)


def solo_lectura(trk):
    """El mismo `Tracking`, con sus arrays de solo lectura: una pieza que escriba en él da error."""
    for array in (trk.bx, trk.by, trk.px, trk.py, trk.team):
        array.setflags(write=False)
    return trk


def huella_de(contenido):
    """sha256 del contenido sin espacios: no cambia con los saltos de línea de Windows, el BOM ni el sangrado."""
    canonico = json.dumps(contenido, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def version_de(spec, donde):
    """Una versión del fichero, lista para `ejecutar`."""
    if not isinstance(spec, dict):
        raise ValueError("{}: tiene que ser un objeto JSON".format(donde))
    tipo = spec.get("tipo", "pipeline")
    if not isinstance(tipo, str) or tipo not in CLAVES:
        raise ValueError("{}: «tipo» tiene que ser {}".format(donde, " o ".join(sorted(CLAVES))))
    raras = sorted(set(spec) - CLAVES[tipo])
    if raras:
        raise ValueError("{}: claves que no valen con «tipo» {}: {} (valen: {})".format(
            donde, tipo, raras, sorted(CLAVES[tipo])))
    if "nota" in spec and not isinstance(spec["nota"], str):
        raise ValueError("{}: «nota» tiene que ser un texto".format(donde))
    if tipo == "control":
        ventana = spec.get("ventana")
        if not isinstance(ventana, int) or isinstance(ventana, bool) or ventana < 0:
            raise ValueError("{}: el control necesita «ventana», un entero de 0 o más".format(donde))
        return {"tipo": "control", "ventana": ventana}

    params = spec.get("params")
    if params is not None and not isinstance(params, dict):
        raise ValueError("{}: «params» tiene que ser un objeto".format(donde))
    piezas = spec.get("piezas")
    piezas = {} if piezas is None else piezas
    if not isinstance(piezas, dict):
        raise ValueError("{}: «piezas» tiene que ser un objeto".format(donde))
    funciones, fuera = {}, []
    for pieza, valor in piezas.items():
        funciones[pieza], deja = funcion_de(pieza, valor, donde)
        if deja:
            fuera.append(pieza)
    # La versión entera sobre un partido inventado: así una errata falla aquí y no a mitad de medir. Si deja
    # fuera el partido, también con cada partido de la DFL: así falla aquí un pliegue que no existe.
    prueba = partido_de_prueba()
    try:
        deja_alguna = bool(fuera) or bool(de_la_entrega_que_dejan_fuera(funciones))
        for partido in [None] + (list(dfl.PARTIDOS) if deja_alguna else []):
            salida = pipeline.run(prueba, params=params, pieces=piezas_para(funciones, fuera, partido), report={})
            if np.shape(salida) != (FRAMES_PRUEBA,):
                raise ValueError("devuelve {} etiquetas en vez de una por frame".format(np.shape(salida)))
            evaluado = np.zeros(FRAMES_PRUEBA, bool)
            for inicio, fin in prueba.blocks:
                evaluado[inicio:fin] = True
            if not np.isin(salida, (H, A, D, X)).all() or not np.array_equal(salida == X, ~evaluado):
                raise ValueError("las etiquetas tienen que ser H, A o D dentro de los tramos evaluados y X fuera")
    except Exception as error:  # cualquier fallo, con su tipo y su mensaje: no se ha medido nada
        raise ValueError("{}: falla en la prueba con un partido inventado de {} frames, antes de medir: "
                         "{}: {}".format(donde, FRAMES_PRUEBA, type(error).__name__, error))
    version = {"tipo": "pipeline", "params": params, "piezas": funciones}
    if fuera:
        version["fuera"] = fuera
    return version


def funcion_de(pieza, valor, donde):
    """La función de una pieza y si deja fuera el partido que se puntúa: (función, dejar_fuera).

    `valor` es "nombre" o {"funcion": "nombre", "opciones": {...}, "dejar_fuera": true}. La función está en
    el módulo de la pieza o, escrita "modulo.nombre", en uno de `OTROS_MODULOS` de esa pieza. Con
    `dejar_fuera`, el harness le pasa `fuera=<partido>` al puntuar cada partido de la DFL, para que use
    los coeficientes que se entrenaron sin él; fuera del harness (la entrega), `fuera` vale None.
    """
    if pieza not in pipeline.PIECES:
        raise ValueError("{}: la pieza «{}» no existe (valen: {})".format(donde, pieza, sorted(pipeline.PIECES)))
    if isinstance(valor, str):
        valor = {"funcion": valor}
    if not isinstance(valor, dict) or set(valor) - {"funcion", "opciones", "dejar_fuera"}:
        raise ValueError("{}: la pieza «{}» tiene que ser el nombre de una función o un objeto con "
                         "«funcion», «opciones» y «dejar_fuera»".format(donde, pieza))
    nombre = valor.get("funcion", pipeline.PIECES[pieza])
    opciones = valor.get("opciones")
    opciones = {} if opciones is None else opciones
    dejar_fuera = valor.get("dejar_fuera", False)
    if not isinstance(dejar_fuera, bool):
        raise ValueError("{}: «dejar_fuera» de «{}» tiene que ser true o false".format(donde, pieza))
    modulo = MODULOS[pieza]
    if isinstance(nombre, str) and "." in nombre:
        nombre_modulo, nombre = nombre.split(".", 1)
        modulo = OTROS_MODULOS.get(pieza, {}).get(nombre_modulo)
        if modulo is None:
            raise ValueError("{}: la pieza «{}» no puede usar funciones de «{}» (valen: {})".format(
                donde, pieza, nombre_modulo, sorted(OTROS_MODULOS.get(pieza, {}))))
    funcion = getattr(modulo, nombre, None) if isinstance(nombre, str) else None
    if not callable(funcion):
        raise ValueError("{}: no hay ninguna función «{}» en {}".format(donde, nombre, modulo.__name__))
    if not isinstance(opciones, dict):
        raise ValueError("{}: las «opciones» de «{}» tienen que ser un objeto".format(donde, pieza))
    if dejar_fuera and "fuera" in opciones:
        raise ValueError("{}: con «dejar_fuera», «fuera» lo pone el harness; no va en las «opciones»".format(donde))
    # Una función con `fuera` sin «dejar_fuera» usaría los coeficientes de los 7 partidos: se puntuaría sobre
    # partidos que ya vio, contra §5.8, sin que nadie lo notara.
    if not dejar_fuera and "fuera" in inspect.signature(funcion).parameters:
        raise ValueError("{}: {}.{} deja fuera un partido (tiene «fuera»): hace falta «dejar_fuera»: true".format(
            donde, modulo.__name__, nombre))
    # La misma llamada que hace pipeline.run: el tracking (o la evidencia, los tramos y los params).
    posicionales = (None,) * (4 if pieza == "temporal" else 1)
    try:
        inspect.signature(funcion).bind(*posicionales, **dict(opciones, **({"fuera": None} if dejar_fuera else {})))
    except TypeError as error:
        raise ValueError("{}: {}.{} no se puede llamar con esas opciones{}: {}".format(
            donde, modulo.__name__, nombre, " y «fuera»" if dejar_fuera else "", error))
    return (functools.partial(funcion, **opciones) if opciones else funcion), dejar_fuera


def con_partido(funciones, fuera, partido):
    """Las piezas de una versión, con `fuera=partido` en las que dejan fuera el partido que se puntúa."""
    if not fuera:
        return funciones
    return {pieza: functools.partial(funcion, fuera=partido) if pieza in fuera else funcion
            for pieza, funcion in funciones.items()}


def de_la_entrega_que_dejan_fuera(funciones):
    """Las piezas que la versión no nombra y cuya función de la entrega deja fuera un partido (tiene `fuera`).

    Desde el 14/11 la evidencia de equipo de la entrega es B5 (`aprendida.evidence_b5`): sin esto, la versión
    de `main` (`{}`) la usaría con los coeficientes de los 7 partidos, sobre partidos que ya vio.
    """
    return [pieza for pieza in pipeline.PIECES if pieza not in (funciones or {})
            and "fuera" in inspect.signature(pipeline.default_piece(pieza)).parameters]


def piezas_para(funciones, fuera, partido):
    """Las piezas con que se puntúa `partido`: las de la versión y, si dejan fuera un partido, también las
    de la entrega que la versión no nombra, todas con `fuera=partido`."""
    piezas = dict(funciones or {})
    defecto = de_la_entrega_que_dejan_fuera(funciones)
    for pieza in defecto:
        piezas[pieza] = pipeline.default_piece(pieza)
    return con_partido(piezas, list(fuera or []) + defecto, partido)


# -- el `D` oráculo y el control -----------------------------------------------------------------------

def d_oraculo(gt):
    """Evidencia con el `D` de las etiquetas: solo `D` donde hay `D`, y nunca `D` donde hay juego."""
    score, allowed = tracking.no_evidence(len(gt))
    allowed[gt == D, :2] = False
    allowed[(gt == H) | (gt == A), D] = False
    return score, allowed


def imponer_d(codes, gt, blocks):
    """El `D` de las etiquetas sobre una salida ya hecha, para tratar al control como a los candidatos.

    Donde la etiqueta es `D`, `D`. Donde hay juego y la salida decía `D`, el último equipo que había
    dicho (o el siguiente, al principio del tramo): es lo que hace el scorer con una `X`.
    """
    out = codes.copy()
    for a, b in blocks:
        w, g = out[a:b], gt[a:b]
        vivo = (g == H) | (g == A)
        w[g == D] = D
        falta = vivo & (w == D)
        conocido = vivo & (w != D)
        primeros = np.flatnonzero(conocido)
        if len(primeros) == 0:
            w[falta] = H
            continue
        ultimo = np.maximum.accumulate(np.where(conocido, np.arange(b - a), -1))
        ultimo[ultimo < 0] = primeros[0]
        w[falta] = w[ultimo[falta]]
    return out


def control(trk, ventana):
    """El baseline oficial: equipo del jugador más cercano y voto por mayoría de ±`ventana` frames."""
    letras = baseline.smooth(candidates.nearest_team(trk), ventana)
    codes = np.full(len(letras), X, dtype=np.int8)
    for a, b in trk.blocks:
        for code, letra in ((H, "H"), (A, "A"), (D, "D")):
            codes[a:b][letras[a:b] == letra] = code
    return codes


def ejecutar(version, trk, gt, modo_d, partido=None):
    """Etiquetas de una versión sobre un `Tracking` de la DFL. `partido` va a las piezas que lo dejan fuera."""
    if version["tipo"] == "control":
        codes = control(trk, version["ventana"])
        return imponer_d(codes, gt, trk.blocks) if modo_d == "oraculo" else codes
    extra = [d_oraculo(gt)] if modo_d == "oraculo" else []
    if (version.get("fuera") or de_la_entrega_que_dejan_fuera(version.get("piezas"))) and partido is None:
        raise ValueError("esta versión deja fuera el partido que se puntúa: hace falta `partido`")
    piezas = piezas_para(version.get("piezas"), version.get("fuera"), partido)
    return pipeline.run(trk, extra=extra, params=version["params"], pieces=piezas)


# -- puntuación ----------------------------------------------------------------------------------------

def contar(gt, pred):
    """Recuentos de un partido con el scorer oficial.

    `flags` tiene una fila por umbral de IoU y una columna por posesión real: True si se emparejó.
    """
    runs = pm.valid_runs(gt)
    filled = pm.fill_abstentions(pred, runs)
    reales = pm.possession_spells(gt, runs)
    predichas = pm.possession_spells(filled, runs)
    solapes = pm.spell_overlaps(reales, predichas)
    flags = np.vstack([pm.matched_gt_flags(solapes, len(reales), umbral) for umbral in pm.SPELL_IOUS])
    cm3 = pm.scored_confusion(pm.confusion(gt, pred))
    return {"flags": flags, "n_pred": len(predichas), "n_gt": len(reales),
            "macro_f1": float(pm.macro_f1(cm3)), "team_acc": float(pm.team_accuracy(cm3)[0])}


def spell_f1(flags, n_pred):
    """spellF1 medio sobre los umbrales, a partir de los emparejamientos. Igual que pm.spell_scores."""
    f1s = []
    for fila in flags:
        tp = int(fila.sum())
        fp, fn = n_pred - tp, len(fila) - tp
        f1s.append(2.0 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return float(np.mean(f1s))


def juntar(recuentos):
    """Los recuentos de varios partidos como si fueran uno. Vale porque ninguna posesión cruza partidos."""
    return np.hstack([r["flags"] for r in recuentos]), int(sum(r["n_pred"] for r in recuentos))


def diferencia_bootstrap(candidato, referencia, n_draws):
    """Intervalo de la diferencia de spellF1 (candidato − control), remuestreando las posesiones reales.

    Pareado: los dos se puntúan sobre el mismo remuestreo. Sigue el esquema de pm.bootstrap_spell_f1: el
    número de posesiones predichas se deja fijo y los falsos positivos no bajan de cero.
    """
    if not n_draws:
        return None
    (flags_c, pred_c), (flags_r, pred_r) = candidato, referencia
    n_gt = flags_c.shape[1]
    rng = np.random.RandomState(SEMILLA_BOOTSTRAP)

    def f1(flags, n_pred, picks):
        tp = flags[:, picks].sum(axis=1).astype(float)
        fp = np.maximum(0.0, n_pred - tp)
        fn = n_gt - tp
        return float(np.mean(np.where(tp > 0, 2.0 * tp / np.maximum(2 * tp + fp + fn, 1.0), 0.0)))

    difs = np.empty(n_draws)
    for draw in range(n_draws):
        picks = rng.randint(0, n_gt, n_gt)
        difs[draw] = f1(flags_c, pred_c, picks) - f1(flags_r, pred_r, picks)
    bajo, alto = np.percentile(difs, PERCENTILES)
    return [float(bajo), float(alto)]


def comprobar_formula(gt, pred, recuento):
    """El spellF1 de este fichero tiene que ser el del scorer oficial."""
    runs = pm.valid_runs(gt)
    oficial = pm.spell_scores(gt, pm.fill_abstentions(pred, runs), runs)["mean_f1"]
    propio = spell_f1(recuento["flags"], recuento["n_pred"])
    if abs(oficial - propio) > 1e-12:
        raise AssertionError("el spellF1 del harness ({}) no coincide con el oficial ({})".format(propio, oficial))


def resumir(por_partido, partidos, n_draws, versiones=VERSIONES, dejar_uno=DEJAR_UNO_FUERA):
    """Agregados de cada versión en una condición y una convención, a partir de los recuentos por partido."""
    filas = collections.OrderedDict()
    referencia = [por_partido[(CONTROL, p)] for p in partidos]
    f1_ref = [spell_f1(r["flags"], r["n_pred"]) for r in referencia]
    for nombre in versiones:
        recuentos = [por_partido[(nombre, p)] for p in partidos]
        f1s = [spell_f1(r["flags"], r["n_pred"]) for r in recuentos]
        flags, n_pred = juntar(recuentos)
        fila = {
            "spell_f1": spell_f1(flags, n_pred),
            "spell_f1_por_partido": dict(zip(partidos, f1s)),
            "macro_f1_medio": float(np.mean([r["macro_f1"] for r in recuentos])),
            "acierto_de_equipo_medio": float(np.mean([r["team_acc"] for r in recuentos])),
            "posesiones_predichas": n_pred,
            "posesiones_reales": int(flags.shape[1]),
        }
        if nombre != CONTROL:
            fila["diferencia"] = fila["spell_f1"] - filas[CONTROL]["spell_f1"]
            fila["diferencia_intervalo"] = diferencia_bootstrap((flags, n_pred), juntar(referencia), n_draws)
            fila["gana_en"] = int(sum(a > b for a, b in zip(f1s, f1_ref)))
        filas[nombre] = fila
    frente_a_main(filas, por_partido, partidos, n_draws, versiones)
    filas[dejar_uno] = dejar_uno_fuera(por_partido, partidos, filas, versiones)
    return filas


def frente_a_main(filas, por_partido, partidos, n_draws, versiones):
    """Lo mismo que frente al control, pero frente a la versión de main: lo que decide entre candidatos."""
    main = version_de_main(versiones)
    if main is None:
        return
    de_main = [por_partido[(main, p)] for p in partidos]
    f1_main = [spell_f1(r["flags"], r["n_pred"]) for r in de_main]
    for nombre, version in versiones.items():
        if nombre in (CONTROL, main) or version["tipo"] != "pipeline":
            continue
        recuentos = [por_partido[(nombre, p)] for p in partidos]
        f1s = [spell_f1(r["flags"], r["n_pred"]) for r in recuentos]
        filas[nombre]["frente_a_main"] = {
            "referencia": main,
            "diferencia": filas[nombre]["spell_f1"] - filas[main]["spell_f1"],
            "diferencia_intervalo": diferencia_bootstrap(juntar(recuentos), juntar(de_main), n_draws),
            "gana_en": int(sum(a > b for a, b in zip(f1s, f1_main))),
        }


def dejar_uno_fuera(por_partido, partidos, filas, versiones=VERSIONES):
    """Para cada partido, la versión del pipeline que más saca en los otros; se puntúa en el que queda fuera."""
    candidatas = [n for n, v in versiones.items() if v["tipo"] == "pipeline"]
    if len(partidos) < 2 or not candidatas:
        return None
    elegidas, recuentos = [], []
    for fuera in partidos:
        resto = [p for p in partidos if p != fuera]
        mejor = max(candidatas, key=lambda n: (spell_f1(*juntar([por_partido[(n, p)] for p in resto])),
                                               -candidatas.index(n)))
        elegidas.append(mejor)
        recuentos.append(por_partido[(mejor, fuera)])
    flags, n_pred = juntar(recuentos)
    f1 = spell_f1(flags, n_pred)
    return {"spell_f1": f1, "diferencia": f1 - filas[CONTROL]["spell_f1"],
            "elegidas": dict(collections.Counter(elegidas)),
            "posesiones_predichas": n_pred, "posesiones_reales": int(flags.shape[1])}


def medir(partidos, modo_d, n_draws, avisar=None, versiones=None, con_eventos=False):
    """{convención: {condición: {versión: agregados}}}, los recuentos de etiquetas de cada partido y, con
    `con_eventos`, los aciertos en los eventos humanos (si no, None).

    Sin `versiones`, las de `VERSIONES`; con ellas (las de `leer_versiones`), esas.
    """
    dejar_uno = DEJAR_UNO_FUERA if versiones is None else DEJAR_UNO_FUERA_FICHERO
    versiones = VERSIONES if versiones is None else versiones
    recuentos = collections.defaultdict(dict)  # (convención, condición) -> {(versión, partido): recuento}
    perfil = collections.OrderedDict()
    comprobado = False
    if con_eventos:
        import eventos  # solo con --eventos: necesita los XML de eventos de la DFL
        for partido in partidos:  # todos al principio: si falta uno, el error sale antes de medir nada
            eventos.fichero_de_eventos(partido)
    en_eventos = collections.defaultdict(list)  # versión o etiquetas, y condición -> aciertos por partido
    tipos = []
    for partido in partidos:
        inicio = time.time()
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        puntos = eventos.puntos_de_control(cargado, cargado["meta"]) if con_eventos else None
        if puntos is not None:
            tipos.append(puntos["tipo"])
            for convencion in dfl.CONVENCIONES:
                en_eventos[("etiquetas «{}»".format(convencion), None)].append(eventos.aciertos(puntos, gt[convencion]))
        perfil[partido] = {c: {"frames_H": int(np.sum(gt[c] == H)), "frames_A": int(np.sum(gt[c] == A)),
                               "frames_D": int(np.sum(gt[c] == D)),
                               "posesiones": len(pm.possession_spells(gt[c], pm.valid_runs(gt[c])))}
                           for c in dfl.CONVENCIONES}
        for condicion in dfl.CONDICIONES:
            # De solo lectura: todas las versiones reciben el mismo tracking, y una pieza que escribiera en
            # él cambiaría lo que ven las siguientes.
            trk = solo_lectura(dfl.tracking_de(cargado, condicion))
            visible = ~np.isnan(trk.bx)
            vivo = (gt["flag"] == H) | (gt["flag"] == A)
            perfil[partido].setdefault("balon_visible_en_juego_pct", {})[condicion] = round(
                100.0 * float(np.mean(visible[vivo])), 1)
            for nombre, version in versiones.items():
                # El `D` es el mismo en las dos convenciones: una sola ejecución sirve para las dos.
                pred = ejecutar(version, trk, gt["flag"], modo_d, partido)
                if puntos is not None:
                    en_eventos[(nombre, condicion)].append(eventos.aciertos(puntos, pred))
                for convencion in dfl.CONVENCIONES:
                    recuento = contar(gt[convencion], pred)
                    if not comprobado:
                        comprobar_formula(gt[convencion], pred, recuento)
                        comprobado = True
                    recuentos[(convencion, condicion)][(nombre, partido)] = recuento
        if avisar:
            avisar("hecho {} en {:.0f} s".format(partido, time.time() - inicio))
    salida = collections.OrderedDict()
    for convencion in dfl.CONVENCIONES:
        salida[convencion] = collections.OrderedDict(
            (condicion, resumir(recuentos[(convencion, condicion)], partidos, n_draws, versiones, dejar_uno))
            for condicion in dfl.CONDICIONES)
    resumen = resumir_eventos(en_eventos, tipos, versiones, n_draws) if con_eventos else None
    return salida, perfil, resumen


# -- eventos humanos (--eventos; regla de lectura en el README) ----------------------------------------

TIPOS_EVENTO = ("pase completado", "recuperación", "duelo con cambio", "duelo sin cambio")  # = eventos.TIPOS
LEIDOS = ("recuperación", "duelo con cambio", "duelo sin cambio")  # los pases se enseñan pero no se leen


def version_de_main(versiones):
    """La primera versión del pipeline sin `params` ni `piezas` (o vacíos): la de `main`. None si no hay."""
    for nombre, version in versiones.items():
        if version["tipo"] == "pipeline" and not version.get("params") and not version.get("piezas"):
            return nombre
    return None


def tasas(aciertos, tipos):
    return collections.OrderedDict((tipo, round(100.0 * float(np.mean(aciertos[tipos == i])), 1))
                                   for i, tipo in enumerate(TIPOS_EVENTO) if np.any(tipos == i))


def diferencias_eventos(a, b, tipos, n_draws):
    """Por tipo: diferencia de aciertos (a − b, en puntos) e intervalo por bootstrap pareado sobre los puntos."""
    salida = collections.OrderedDict()
    for i, tipo in enumerate(TIPOS_EVENTO):
        x, y = a[tipos == i].astype(float), b[tipos == i].astype(float)
        if not len(x):
            continue
        fila = {"diferencia": round(100.0 * float(x.mean() - y.mean()), 1), "intervalo": None}
        if n_draws:
            rng = np.random.RandomState([SEMILLA_BOOTSTRAP, i])
            picks = rng.randint(0, len(x), (n_draws, len(x)))
            difs = x[picks].mean(axis=1) - y[picks].mean(axis=1)
            fila["intervalo"] = [round(100.0 * float(v), 1) for v in np.percentile(difs, PERCENTILES)]
        salida[tipo] = fila
    return salida


def lectura_eventos(difs):
    """El veredicto de una condición con la regla del README: mejora, empeora, compromiso o no concluye."""
    intervalos = [difs[t]["intervalo"] for t in LEIDOS if t in difs]
    if not intervalos or any(v is None for v in intervalos):
        return "sin intervalo"
    arriba = any(bajo > 0 for bajo, _ in intervalos)
    abajo = any(alto < 0 for _, alto in intervalos)
    return {(True, False): "mejora", (False, True): "empeora", (True, True): "compromiso"}.get(
        (arriba, abajo), "no concluye")


def resumir_eventos(en_eventos, tipos, versiones, n_draws):
    """Aciertos en los eventos humanos de cada versión, por condición, y sus diferencias con el control y main."""
    import eventos
    if tuple(eventos.TIPOS) != TIPOS_EVENTO:  # los códigos de tipo de eventos.py son índices de esta tupla
        raise AssertionError("TIPOS_EVENTO no coincide con eventos.TIPOS")
    tipos = np.concatenate(tipos)
    juntos = {clave: np.concatenate(partes) for clave, partes in en_eventos.items()}
    main = version_de_main(versiones)
    salida = collections.OrderedDict()
    salida["puntos"] = collections.OrderedDict((t, int(np.sum(tipos == i))) for i, t in enumerate(TIPOS_EVENTO))
    salida["etiquetas"] = collections.OrderedDict(
        (c, tasas(juntos[("etiquetas «{}»".format(c), None)], tipos)) for c in dfl.CONVENCIONES)
    salida["condiciones"] = collections.OrderedDict()
    for condicion in dfl.CONDICIONES:
        filas = collections.OrderedDict()
        for nombre in versiones:
            a = juntos[(nombre, condicion)]
            fila = {"acierto_pct": tasas(a, tipos), "frente_a": collections.OrderedDict()}
            for referencia in (CONTROL, main):
                if nombre == CONTROL or referencia in (None, nombre) or referencia in fila["frente_a"]:
                    continue
                difs = diferencias_eventos(a, juntos[(referencia, condicion)], tipos, n_draws)
                fila["frente_a"][referencia] = {"por_tipo": difs, "lectura": lectura_eventos(difs)}
            filas[nombre] = fila
        salida["condiciones"][condicion] = filas
    salida["veredictos"] = collections.OrderedDict()
    for nombre in versiones:
        for referencia in salida["condiciones"][dfl.CONDICIONES[0]][nombre]["frente_a"]:
            lecturas = {salida["condiciones"][c][nombre]["frente_a"][referencia]["lectura"]
                        for c in dfl.VOTAN}
            salida["veredictos"].setdefault(nombre, collections.OrderedDict())[referencia] = (
                lecturas.pop() if len(lecturas) == 1 else "depende del balón")
    return salida


def pts(valor, signo=False):
    if valor is None:
        return "–"
    return ("{:+.1f}" if signo else "{:.1f}").format(valor).replace(".", ",")


def tablas_eventos(resumen):
    """Las tablas de --eventos: aciertos por tipo de punto y diferencias leídas con la regla del README."""
    lineas = ["### Eventos humanos (descriptivo; regla de lectura en validation/harness/README.md)", "",
              "Puntos, con los partidos medidos juntos: " + ", ".join(
                  "{} {}".format(n, t) for t, n in resumen["puntos"].items()) + ".", "",
              "| balón | versión | " + " | ".join(TIPOS_EVENTO) + " |",
              "|---|---|" + "---|" * len(TIPOS_EVENTO)]
    for convencion, fila in resumen["etiquetas"].items():
        lineas.append("| (todas) | etiquetas «{}» como predicción | {} |".format(
            convencion, " | ".join(pts(fila.get(t)) for t in TIPOS_EVENTO)))
    for condicion, filas in resumen["condiciones"].items():
        for nombre, fila in filas.items():
            lineas.append("| {} | {} | {} |".format(balon(condicion), nombre, " | ".join(
                pts(fila["acierto_pct"].get(t)) for t in TIPOS_EVENTO)))
    lineas += ["", "Diferencias en puntos, [5–95 %]:", "",
               "| balón | versión | frente a | " + " | ".join(LEIDOS) + " | lectura |",
               "|---|---|---|" + "---|" * len(LEIDOS) + "---|"]
    for condicion, filas in resumen["condiciones"].items():
        for nombre, fila in filas.items():
            for referencia, comparacion in fila["frente_a"].items():
                celdas = []
                for tipo in LEIDOS:
                    d = comparacion["por_tipo"].get(tipo)
                    if d is None:
                        celdas.append("–")
                        continue
                    intervalo = d["intervalo"]
                    celdas.append(pts(d["diferencia"], True) + (
                        " [{} a {}]".format(pts(intervalo[0], True), pts(intervalo[1], True)) if intervalo else ""))
                lineas.append("| {} | {} | {} | {} | {} |".format(
                    balon(condicion), nombre, referencia, " | ".join(celdas), comparacion["lectura"]))
    lineas += ["", "Veredicto en {} (descriptivo, no entra en §5.8):".format(que_votan(False)), ""]
    for nombre, por_referencia in resumen["veredictos"].items():
        lineas.append("- {}: {}".format(nombre, "; ".join(
            "frente a {}, **{}**".format(r, v) for r, v in por_referencia.items())))
    return "\n".join(lineas)


# -- salida --------------------------------------------------------------------------------------------

def num(valor, signo=False):
    if valor is None:
        return "–"
    return ("{:+.3f}" if signo else "{:.3f}").format(valor).replace(".", ",")


def veredicto(salida, nombre, n_partidos, campo=None):
    """¿Gana `nombre` al control con la regla de §5.8? Mira todas las condiciones y convenciones.

    Con `campo="frente_a_main"`, la misma regla frente a la versión de main. Solo cuentan las condiciones
    que votan (`dfl.VOTAN`); las demás se puntúan sin voto.
    """
    filas = [salida[c][k][nombre] for c in salida for k in salida[c] if k in dfl.VOTAN]
    if campo is not None:
        filas = [f[campo] for f in filas]
    gana = all(f["diferencia"] >= EMPATE and f["gana_en"] >= min(MIN_PARTIDOS, n_partidos)
               and (f["diferencia_intervalo"] is None or f["diferencia_intervalo"][0] > 0) for f in filas)
    pierde = all(f["diferencia"] <= -EMPATE for f in filas)
    return "gana" if gana else "pierde" if pierde else "empate o no concluye"


def que_votan(todas=True):
    """Con qué condiciones se aplica la regla, dicho para la salida."""
    if set(dfl.VOTAN) == set(dfl.CONDICIONES):
        return "todas las condiciones" if todas else "las tres condiciones"
    return "las condiciones que votan: {}".format(", ".join("«{}»".format(c) for c in dfl.VOTAN))


def balon(condicion):
    """El nombre de la condición en las tablas, marcado si no vota."""
    return condicion if condicion in dfl.VOTAN else condicion + " (sin voto)"


def tabla_perfil(perfil):
    """Cómo son las etiquetas y el balón de los partidos medidos, todos juntos."""
    lineas = ["### Con qué se mide", "", "| etiquetas | posesiones | frames `D` |", "|---|---|---|"]
    for convencion in dfl.CONVENCIONES:
        filas = [p[convencion] for p in perfil.values()]
        frames = sum(f["frames_H"] + f["frames_A"] + f["frames_D"] for f in filas)
        lineas.append("| {} | {} | {:.1f} % |".format(
            convencion, sum(f["posesiones"] for f in filas),
            100.0 * sum(f["frames_D"] for f in filas) / max(frames, 1)).replace(".", ","))
    lineas += ["", "| balón | visible en los frames de juego (media de los partidos) |", "|---|---|"]
    for condicion in dfl.CONDICIONES:
        media = float(np.mean([p["balon_visible_en_juego_pct"][condicion] for p in perfil.values()]))
        lineas.append("| {} | {:.1f} % |".format(balon(condicion), media).replace(".", ","))
    lineas.append("")
    return "\n".join(lineas)


def tablas(salida, partidos, versiones=VERSIONES):
    lineas = []
    for convencion, por_condicion in salida.items():
        lineas.append("### Etiquetas: {}".format(convencion))
        lineas.append("")
        lineas.append("| balón | versión | spellF1, {} partidos | por partido, mín–máx | frente al control "
                      "[5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |".format(len(partidos)))
        lineas.append("|---|---|---|---|---|---|---|---|")
        for condicion, filas in por_condicion.items():
            for nombre, f in filas.items():
                if f is None:
                    continue
                if "elegidas" in f:
                    lineas.append("| {} | {} | {} | – | {} | – | {} / {} | – |".format(
                        balon(condicion), nombre, num(f["spell_f1"]), num(f["diferencia"], True),
                        f["posesiones_predichas"], f["posesiones_reales"]))
                    continue
                valores = list(f["spell_f1_por_partido"].values())
                if nombre == CONTROL:
                    frente, gana = "–", "–"
                else:
                    intervalo = f["diferencia_intervalo"]
                    frente = num(f["diferencia"], True) + (
                        " [{} a {}]".format(num(intervalo[0], True), num(intervalo[1], True)) if intervalo else "")
                    gana = "{} de {}".format(f["gana_en"], len(partidos))
                lineas.append("| {} | {} | {} | {}–{} | {} | {} | {} / {} | {} |".format(
                    balon(condicion), nombre, num(f["spell_f1"]), num(min(valores)), num(max(valores)), frente, gana,
                    f["posesiones_predichas"], f["posesiones_reales"], num(f["acierto_de_equipo_medio"])))
        lineas.append("")
    lineas.append("### Regla de §5.8 ({} y las dos convenciones)".format(que_votan()))
    lineas.append("")
    for nombre, version in versiones.items():
        if version["tipo"] == "pipeline":
            lineas.append("- {}: **{}**".format(nombre, veredicto(salida, nombre, len(partidos))))
    lineas += tabla_frente_a_main(salida, partidos, versiones)
    return "\n".join(lineas)


def tabla_frente_a_main(salida, partidos, versiones):
    """Cada candidato frente a la versión de main, con la misma regla de §5.8: lo que decide si entra."""
    main = version_de_main(versiones)
    candidatas = [n for n, v in versiones.items() if v["tipo"] == "pipeline" and n != main]
    if main is None or not candidatas:
        return []
    lineas = ["", "### Frente a la versión de main («{}»)".format(main), "",
              "| etiquetas | balón | versión | frente a main [5–95 %] | gana en |", "|---|---|---|---|---|"]
    for convencion, por_condicion in salida.items():
        for condicion, filas in por_condicion.items():
            for nombre in candidatas:
                f = filas[nombre]["frente_a_main"]
                intervalo = f["diferencia_intervalo"]
                lineas.append("| {} | {} | {} | {} | {} de {} |".format(
                    convencion, balon(condicion), nombre, num(f["diferencia"], True) + (
                        " [{} a {}]".format(num(intervalo[0], True), num(intervalo[1], True)) if intervalo else ""),
                    f["gana_en"], len(partidos)))
    lineas += ["", "Regla de §5.8 frente a main ({} y las dos convenciones):".format(que_votan()), ""]
    for nombre in candidatas:
        lineas.append("- {}: **{}**".format(nombre, veredicto(salida, nombre, len(partidos), "frente_a_main")))
    return lineas


def version_del_codigo():
    """El commit del repo y si hay cambios sin commit: la huella del fichero no identifica el código."""
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                                text=True, check=True).stdout.strip()
        sucio = bool(subprocess.run(["git", "status", "--porcelain", "--", "possession", "validation/harness"],
                                    cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return "desconocido (sin git)"
    return commit + (", con cambios sin commit en possession/ o validation/harness/" if sucio else "")


def cabecera_versiones(ruta, contenido, huella, codigo):
    """Qué versiones se midieron, para que la tabla pegada en una PR se explique sola."""
    lineas = ["versiones: {} (huella {}) · código: {}".format(ruta, huella[:12], codigo)]
    for nombre, spec in contenido.items():
        lineas.append("- {}: {}".format(nombre, json.dumps(spec, ensure_ascii=False, sort_keys=True)))
    return "\n".join(lineas)


def main():
    parser = argparse.ArgumentParser(description="Puntúa el pipeline en los partidos abiertos de la DFL.")
    parser.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), choices=list(dfl.PARTIDOS))
    parser.add_argument("--d", choices=("oraculo", "propio"), default="oraculo",
                        help="de dónde sale el D: de las etiquetas (por defecto) o de cada versión")
    parser.add_argument("--bootstrap", type=int, default=1000, help="remuestreos del intervalo; 0 lo quita")
    parser.add_argument("--json", action="store_true", help="imprime la salida completa en JSON")
    parser.add_argument("--versiones", metavar="FICHERO.json",
                        help="las versiones que se puntúan, en lugar de las de VERSIONES (ver el README)")
    parser.add_argument("--eventos", action="store_true",
                        help="añade los aciertos en los eventos humanos de la DFL (descriptivo; ver el README)")
    args = parser.parse_args()

    versiones, contenido, huella = None, None, None
    if args.versiones:
        try:
            versiones, contenido, huella = leer_versiones(args.versiones)
        except (OSError, ValueError) as error:  # json.JSONDecodeError es un ValueError
            sys.exit("--versiones: {}".format(error))
        if version_de_main(versiones) is None:
            print("AVISO: {} no trae la versión de main ({{}}): no habrá comparación frente a main.".format(
                args.versiones), file=sys.stderr)
    salida, perfil, en_eventos = medir(args.partidos, args.d, args.bootstrap,
                                       avisar=lambda texto: print(texto, file=sys.stderr), versiones=versiones,
                                       con_eventos=args.eventos)
    if args.json:
        completa = {"d": args.d, "partidos": args.partidos, "perfil": perfil, "resultados": salida}
        if versiones is not None:
            completa["versiones"] = {"fichero": args.versiones, "huella": huella, "codigo": version_del_codigo(),
                                     "contenido": contenido}
        if en_eventos is not None:
            completa["eventos"] = en_eventos
        print(json.dumps(completa, ensure_ascii=False, indent=1))
        return
    print("D: {} · partidos: {} · bootstrap: {}".format(args.d, len(args.partidos), args.bootstrap))
    if versiones is not None:
        print(cabecera_versiones(args.versiones, contenido, huella, version_del_codigo()))
    if args.d == "propio":
        print("AVISO: con el D propio, el balón tapado en los D de la DFL delata la etiqueta. No decide nada.")
    print()
    print(tabla_perfil(perfil))
    print(tablas(salida, args.partidos, VERSIONES if versiones is None else versiones))
    if en_eventos is not None:
        print()
        print(tablas_eventos(en_eventos))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
