"""La condición 5 de la puerta 1b: B5 de `main` con un balón «del vídeo» emulado en la DFL, en una rejilla.

Por qué (`validation/balon_video/BITACORA.md`, «Corrección de la puerta 1b», condición 5, escrita antes de medir): la
1b se lee en la celda (cobertura p, temblor σ, rachas de fallos L) que mida el sondeo del partido, y pasa si en esa
celda, con el `D` de las etiquetas, B5 con el balón emulado gana a B5 con el balón «como el ATD»:
- con control: +0,01 o más en las dos condiciones que votan, ganando en 6 de 7 partidos;
- con el flag: no pierde más de 0,005 en ninguna.
Este script calcula la rejilla entera antes de que se ejecute la 1b. Su JSON lo lee el sondeo para dar el veredicto.

Cómo se lee la celda (la regla está en la bitácora, con la precisión del 16/11 a las 17:00; la aplica el sondeo): L es
la menor de la rejilla cuya racha media de fallos REAL en esta emulación (`racha_de_fallos_media_real`, en esa p y esa
σ) es igual o mayor que la que mide la 1b; la lectura literal (la etiqueta L redondeada hacia arriba) se imprime al
lado, sin voto. Fuera de la rejilla no pasa: cobertura por debajo de 0,5, temblor mayor que el de σ = 0,25 en la DFL o
una racha de fallos más larga que la mayor racha real de la emulación.

Datos abiertos de otros partidos: los 7 de la Bundesliga (Bassek et al., 2025, CC BY 4.0), con la caché del
experimento 0 y el harness (`validation/harness/dfl.py` y `puntuar.py`, sin tocarlos). Lo puede ejecutar cualquiera,
Claude incluido. Solo escribe agregados.

El balón emulado, en cada partido, condición que vota (`dfl.VOTAN`) y celda (p, σ, L):
- Solo en los frames donde el balón «como el ATD» de esa condición (`trk_atd`) se ve. En cada uno, «detectado» o
  «fallo»:
  - L = 1: independiente, detectado con probabilidad p. Su racha media real de fallos es 1/p (1,43 con p = 0,7), no 1;
    la bitácora (precisión del 16/11, 17:00) lo da por bueno y por eso la L se lee con la racha real de cada celda;
  - L = 12 y 50: una cadena de Markov de dos estados con fracción de fallos 1 − p y rachas de fallos de longitud media
    L: P(fallo→fallo) = 1 − 1/L y P(detectado→fallo) = (1 − p)/(L·p). Empieza en su estacionaria y se reinicia en cada
    tramo seguido de frames con balón. Se simula por rachas de longitud geométrica, que es la misma cadena. Pide
    p ≥ 1/(1 + L): en la rejilla siempre se cumple; con `--celdas` fuera de eso, el script da error.
- Detectado: el balón del harness `limpio` más N(0, σ²) en x y en y. Fallo: el balón de `trk_atd`. Donde `trk_atd` no
  ve el balón, NaN. Si el `limpio` no tiene balón en un frame detectado (fuera de los `D` no debería pasar), se usa el
  de `trk_atd` y se cuenta.
- Semilla fija por (partido, condición, celda, réplica r): `default_rng([SEMILLA, partido, condición, 100·p, 1000·σ,
  L])` en la réplica 0 y la misma lista con `r` al final en las demás.
- **Réplicas** (16/11, después de ver una rejilla de revisión con una sola tirada por celda y antes de ejecutar la 1b;
  la regla no cambia): una sola tirada por celda deja el veredicto a merced de la semilla, porque el ruido de Monte
  Carlo (desviación típica de 0,0009 a 0,0016 en el Δ de una celda, medida con 6 semillas) es del orden de la distancia
  al +0,01. Por eso, en las celdas con p ≥ 0,7 (la condición 1 ya exige el 70 %) se hacen R = 8 réplicas (r = 0…7);
  en las de p < 0,7 y en las de comprobación, una. En cada partido se juntan las R réplicas con `pu.juntar` (flags
  apilados, posesiones predichas sumadas): eso da el spellF1 del partido para «gana en» frente a `main`, y el Δ sale
  de los 7 × R recuentos juntos. El veredicto de la celda (el que lee el sondeo) sale de esos dos. El intervalo
  bootstrap es solo descriptivo y sale de la réplica 0 (con las réplicas apiladas trataría las copias como
  posesiones independientes). El `D` propio, que no decide, solo con la réplica 0.
- **«Sin decidir»** (solo informativo; el sondeo no lo lee): con R > 1, una celda queda sin decidir si en alguna de
  las dos condiciones que votan el Δ juntado está a menos de 2 errores estándar del umbral (+0,01 con control, −0,005
  con el flag; error estándar = desviación típica de los Δ de las R réplicas / √R), o si el «gana en» del control de
  las réplicas cruza el 6 (unas réplicas llegan y otras no).
- Los jugadores, los tramos y los frames son los de `trk_atd` (se comprueba que coinciden con los de `limpio`). Las
  piezas de `D` de `main` no miran el balón (`dead_state` solo usa los jugadores), así que el balón emulado solo lo ve
  B5, como pide la bitácora.

Qué se mide en cada celda: `main` (`{}` del harness: B5 dejando fuera el partido que se puntúa) con el balón emulado
frente a `main` con `trk_atd`, con el `D` de las etiquetas («oraculo», el que decide) y, solo descriptivo, con el `D`
propio; las dos convenciones. Con las funciones del harness: `contar`, `juntar`, `spell_f1`, «gana en» (estrictamente
mayor, partido a partido) y `diferencia_bootstrap` (pareado sobre las posesiones reales, 5–95 %).

Filas de comprobación: p = 0 (tiene que dar exactamente las etiquetas de `main`: el script lo comprueba en cada
partido, condición y `D`, y por eso sale «0 de 7») y p = 1 con σ = 0 (el detector perfecto, sin azar: una réplica).

El JSON no guarda el comando ni los tiempos (van en el md), así que dos ejecuciones con el mismo código y en el mismo
commit (el JSON lleva el commit y si hay cambios sin commitear) dan el mismo JSON byte a byte, con cualquier número de
procesos.

Uso, desde la raíz del repo:

    python validation/balon_video/emular_dfl.py                       # la rejilla entera, salidas en salidas/
    python validation/balon_video/emular_dfl.py --partidos J03WMX --celdas 0.8,0.06,12 1.0,0.03,1 --salida /tmp/x

`--procesos N` reparte (partido, condición) entre N procesos (por defecto, uno por tarea hasta el número de CPU); el
resultado es idéntico al de la ejecución en serie (cada tarea tiene su semilla y los hilos de BLAS van fijos a 1).
`--replicas N` cambia R solo para probar.
"""

import os

for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_variable] = "1"  # mismos hilos en serie y en paralelo: mismas cuentas, bit a bit

import argparse  # noqa: E402
import collections  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import multiprocessing  # noqa: E402
import platform  # noqa: E402
try:  # noqa: E402
    import resource  # solo en Unix: la memoria máxima del informe
except ImportError:  # Windows
    resource = None
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(AQUI, "..", "harness"))
import dfl  # noqa: E402
import puntuar as pu  # noqa: E402

SEMILLA = 20261116
PS = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
SIGMAS = (0.03, 0.06, 0.12, 0.25)  # m
LS = (1, 12, 50)  # frames
REJILLA = tuple((p, s, l) for p in PS for s in SIGMAS for l in LS)
COMPROBACION = {(0.0, 0.03, 1): "p = 0: tiene que ser main", (1.0, 0.0, 1): "p = 1, σ = 0: el detector perfecto"}
MODOS = ("oraculo", "propio")
UMBRAL_CONTROL = 0.01
UMBRAL_FLAG = -0.005
MIN_GANA = 6
REPLICAS = 8  # réplicas por celda con p ≥ P_REPLICAS
P_REPLICAS = 0.7
ERRORES_ESTANDAR = 2.0  # «sin decidir» a menos de esto del umbral
LEJOS = 5.0  # m: un detector real descartaría la detección a más de esto del balón del ATD (bitácora)
FECHA = "2026-11-16"
SALIDA = os.path.join(AQUI, "salidas", FECHA + "_emulacion_dfl")


def clave(celda):
    p, s, l = celda
    return "p={:g} σ={:g} L={:d}".format(p, s, l)


def semilla_de(indice_partido, indice_condicion, celda, replica=0):
    p, s, l = celda
    base = [SEMILLA, indice_partido, indice_condicion, int(round(100 * p)), int(round(1000 * s)), int(l)]
    return base + ([int(replica)] if replica else [])


def replicas_de(celda, replicas=REPLICAS):
    """R de una celda: las de comprobación y las de p < P_REPLICAS, una; las demás, `replicas`."""
    return 1 if celda in COMPROBACION or celda[0] < P_REPLICAS else int(replicas)


# -- el balón emulado ----------------------------------------------------------------------------------

def tramos(mascara):
    """(inicio, fin) de cada tramo seguido de True."""
    borde = np.diff(np.concatenate(([0], mascara.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(borde == 1), np.flatnonzero(borde == -1)))


def cadena(largo, p, l, rng):
    """Fallos (True) de una cadena de dos estados en un tramo: estacionaria al empezar, rachas geométricas."""
    fallo = np.zeros(largo, bool)
    a_fallo = (1.0 - p) / (l * p)  # P(detectado→fallo)
    if a_fallo > 1.0:
        raise ValueError("con L = {} hace falta p ≥ {:g} (p = {:g})".format(l, 1.0 / (1 + l), p))
    a_detectado = 1.0 / l  # P(fallo→detectado)
    estado = bool(rng.random() < 1.0 - p)
    pos = 0
    while pos < largo:
        racha = int(rng.geometric(a_detectado if estado else a_fallo))
        if estado:
            fallo[pos:pos + racha] = True
        pos += racha
        estado = not estado
    return fallo


def fallos(visible, p, l, rng):
    """Frames con balón del ATD en los que el detector emulado falla."""
    n = len(visible)
    if p >= 1.0:
        return np.zeros(n, bool)
    if p <= 0.0:
        return visible.copy()
    if l == 1:
        return visible & (rng.random(n) < 1.0 - p)
    fallo = np.zeros(n, bool)
    for a, b in tramos(visible):
        fallo[a:b] = cadena(b - a, p, l, rng)
    return fallo


def emular(atd, limpio, celda, rng):
    """(bx, by, recuentos) del balón emulado de una celda."""
    p, sigma, l = celda
    visible = np.isfinite(atd.bx) & np.isfinite(atd.by)
    fallo = fallos(visible, p, l, rng)
    ux, uy = rng.standard_normal(len(visible)), rng.standard_normal(len(visible))
    detectado = visible & ~fallo
    hay_limpio = np.isfinite(limpio.bx) & np.isfinite(limpio.by)
    usa_limpio = detectado & hay_limpio
    bx, by = np.full(len(visible), np.nan), np.full(len(visible), np.nan)
    bx[visible], by[visible] = atd.bx[visible], atd.by[visible]
    bx[usa_limpio] = limpio.bx[usa_limpio] + sigma * ux[usa_limpio]
    by[usa_limpio] = limpio.by[usa_limpio] + sigma * uy[usa_limpio]
    distancia = np.hypot(limpio.bx[usa_limpio] - atd.bx[usa_limpio], limpio.by[usa_limpio] - atd.by[usa_limpio])
    rachas = tramos(fallo)
    return bx, by, {"visibles": int(visible.sum()), "detectados": int(usa_limpio.sum()),
                    "detectados_sin_limpio": int(np.sum(detectado & ~hay_limpio)),
                    "rachas_de_fallos": len(rachas), "frames_de_fallo": int(fallo.sum()),
                    "detectados_a_mas_de_5m_del_atd": int(np.sum(distancia > LEJOS))}


def comprobar_iguales(atd, limpio):
    """Jugadores, tramos y frames iguales en los dos `Tracking`: solo cambia el balón."""
    iguales = (len(atd.bx) == len(limpio.bx) and atd.blocks == limpio.blocks and atd.fps == limpio.fps
               and tuple(atd.pitch) == tuple(limpio.pitch) and np.array_equal(atd.team, limpio.team)
               and np.array_equal(atd.px, limpio.px, equal_nan=True)
               and np.array_equal(atd.py, limpio.py, equal_nan=True))
    if not iguales:
        raise AssertionError("trk_atd y trk_limpio no tienen los mismos jugadores, tramos o frames")


# -- una tarea: un partido y una condición -------------------------------------------------------------

_MAIN = None


def version_main():
    global _MAIN
    if _MAIN is None:
        _MAIN = pu.version_de({}, "main ({})")
    return _MAIN


def recuento(gt, pred):
    r = pu.contar(gt, pred)
    return {"flags": r["flags"], "n_pred": r["n_pred"], "macro_f1": r["macro_f1"]}


def tarea(args):
    """Recuentos de la referencia y de cada celda en un partido y una condición.

    En cada celda: `cuentas` sumadas sobre las réplicas, `oraculo` = una lista con los recuentos de cada réplica y
    `propio` = los recuentos de la réplica 0.
    """
    partido, condicion, celdas, replicas = args
    inicio = time.time()
    main = version_main()
    cargado = dfl.cargar(partido)
    gt = cargado["gt"]
    atd = pu.solo_lectura(dfl.tracking_de(cargado, condicion))
    limpio = dfl.tracking_de(cargado, "limpio")
    comprobar_iguales(atd, limpio)
    referencia, preds_ref = {}, {}
    for modo in MODOS:
        preds_ref[modo] = pu.ejecutar(main, atd, gt["flag"], modo, partido)
        referencia[modo] = {c: recuento(gt[c], preds_ref[modo]) for c in dfl.CONVENCIONES}
    por_celda = collections.OrderedDict()
    for celda in celdas:
        fila = {"cuentas": collections.Counter(), "oraculo": []}
        for r in range(replicas_de(celda, replicas)):
            rng = np.random.default_rng(semilla_de(cargado["indice"], dfl.CONDICIONES.index(condicion), celda, r))
            bx, by, cuentas = emular(atd, limpio, celda, rng)
            fila["cuentas"].update(cuentas)
            emulado = pu.solo_lectura(atd._replace(bx=bx, by=by))
            for modo in (MODOS if r == 0 else ("oraculo",)):
                pred = pu.ejecutar(main, emulado, gt["flag"], modo, partido)
                if celda[0] == 0.0 and not np.array_equal(pred, preds_ref[modo]):
                    raise AssertionError("p = 0 no da las etiquetas de main en {} / {} / {}".format(
                        partido, condicion, modo))
                recuentos = {c: recuento(gt[c], pred) for c in dfl.CONVENCIONES}
                if modo == "oraculo":
                    fila["oraculo"].append(recuentos)
                else:
                    fila[modo] = recuentos
        fila["cuentas"] = dict(fila["cuentas"])
        por_celda[celda] = fila
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 if resource is not None else None
    return partido, condicion, referencia, por_celda, time.time() - inicio, rss


# -- agregados -----------------------------------------------------------------------------------------

def comparar(emulados, referencias, partidos, n_draws, intervalo=None):
    """Lo que el harness da a un candidato frente a main, con los partidos juntos.

    `emulados`: por partido, la lista de recuentos de sus réplicas (una o más). En cada partido se juntan las réplicas
    con `pu.juntar` (su spellF1 da «gana en»), y el Δ sale de todos los recuentos juntos. El intervalo bootstrap sale
    de la réplica 0 (o se pasa ya hecho en `intervalo`, que es el de la réplica 0).
    """
    replicas = len(emulados[0])
    if any(len(e) != replicas for e in emulados):
        raise AssertionError("no todos los partidos tienen las mismas réplicas")
    f1_e = [pu.spell_f1(*pu.juntar(e)) for e in emulados]
    f1_r = [pu.spell_f1(r["flags"], r["n_pred"]) for r in referencias]
    junto_e, junto_r = pu.juntar([x for e in emulados for x in e]), pu.juntar(referencias)
    total_e, total_r = pu.spell_f1(*junto_e), pu.spell_f1(*junto_r)
    if intervalo is None:
        intervalo = pu.diferencia_bootstrap(pu.juntar([e[0] for e in emulados]), junto_r, n_draws)
    return {"spell_f1": total_e, "spell_f1_main": total_r, "diferencia": total_e - total_r,
            "gana_en": int(sum(a > b for a, b in zip(f1_e, f1_r))), "intervalo": intervalo,
            "diferencia_por_partido": dict(zip(partidos, [a - b for a, b in zip(f1_e, f1_r)])),
            "posesiones_predichas": junto_e[1] / replicas if replicas > 1 else junto_e[1],
            "posesiones_predichas_main": junto_r[1], "posesiones_reales": int(junto_r[0].shape[1])}


def veredicto(por_condicion, n_partidos):
    """La condición 5 en una celda: control ≥ +0,01 y 6 de 7 en las dos que votan; flag ≥ −0,005 en las dos."""
    minimo = min(MIN_GANA, n_partidos)
    control = all(por_condicion[c]["control"]["diferencia"] >= UMBRAL_CONTROL
                  and por_condicion[c]["control"]["gana_en"] >= minimo for c in dfl.VOTAN)
    flag = all(por_condicion[c]["flag"]["diferencia"] >= UMBRAL_FLAG for c in dfl.VOTAN)
    return {"control": control, "flag": flag, "pasa": control and flag}


def sin_decidir(juntado, por_replica, n_partidos):
    """Motivos por los que el veredicto juntado de una celda queda sin decidir (lista vacía si no hay ninguno)."""
    replicas = len(por_replica)
    if replicas < 2:
        return []
    minimo = min(MIN_GANA, n_partidos)
    motivos = []
    for c in dfl.VOTAN:
        for conv, umbral in (("control", UMBRAL_CONTROL), ("flag", UMBRAL_FLAG)):
            d = np.array([r[c][conv]["diferencia"] for r in por_replica])
            error = float(np.std(d, ddof=1)) / np.sqrt(replicas)
            if abs(juntado[c][conv]["diferencia"] - umbral) < ERRORES_ESTANDAR * error:
                motivos.append("Δ {} en «{}» a menos de {:g} errores estándar del umbral".format(
                    conv, c, ERRORES_ESTANDAR))
        gana = [r[c]["control"]["gana_en"] for r in por_replica]
        if min(gana) < minimo <= max(gana):
            motivos.append("«gana en» del control en «{}» de {} a {} según la réplica".format(c, min(gana), max(gana)))
    return motivos


def resumir(resultados, partidos, celdas, n_draws):
    salida = collections.OrderedDict()
    for celda in celdas:
        fila = {"p": celda[0], "sigma": celda[1], "L": celda[2], "comprobacion": COMPROBACION.get(celda)}
        cuentas = collections.defaultdict(int)
        for partido in partidos:
            for condicion in dfl.VOTAN:
                for k, v in resultados[(partido, condicion)][1][celda]["cuentas"].items():
                    cuentas[k] += v
        fila["cuentas"] = dict(cuentas)
        fila["cobertura_real"] = cuentas["detectados"] / max(cuentas["visibles"], 1)
        fila["racha_de_fallos_media_real"] = (cuentas["frames_de_fallo"] / cuentas["rachas_de_fallos"]
                                              if cuentas["rachas_de_fallos"] else None)
        replicas = len(resultados[(partidos[0], dfl.VOTAN[0])][1][celda]["oraculo"])
        fila["replicas"] = replicas

        def de(modo, r=None):
            """Por condición y convención: por partido, la lista de recuentos (todas las réplicas, o solo la r)."""
            salida_modo = {}
            for condicion in dfl.VOTAN:
                for conv in dfl.CONVENCIONES:
                    por_partido = []
                    for p in partidos:
                        guardado = resultados[(p, condicion)][1][celda][modo]
                        if modo == "oraculo":
                            elegidas = guardado if r is None else [guardado[r]]
                            por_partido.append([x[conv] for x in elegidas])
                        else:
                            por_partido.append([guardado[conv]])
                    salida_modo[(condicion, conv)] = por_partido
            return salida_modo

        def comparar_todo(emulados, intervalos=None):
            por_condicion = collections.OrderedDict()
            for condicion in dfl.VOTAN:
                por_condicion[condicion] = collections.OrderedDict()
                for conv in dfl.CONVENCIONES:
                    referencias = [resultados[(p, condicion)][0][modo_ref][conv] for p in partidos]
                    por_condicion[condicion][conv] = comparar(
                        emulados[(condicion, conv)], referencias, partidos, n_draws,
                        None if intervalos is None else intervalos[condicion][conv]["intervalo"])
            return por_condicion

        modo_ref = "oraculo"
        r0 = comparar_todo(de("oraculo", 0))
        por_replica = [r0] + [comparar_todo(de("oraculo", r), intervalos=r0) for r in range(1, replicas)]
        juntado = comparar_todo(de("oraculo"), intervalos=r0) if replicas > 1 else r0
        fila["oraculo"] = {"condiciones": juntado, "veredicto": veredicto(juntado, len(partidos))}
        if replicas > 1:
            veredictos = [veredicto(r, len(partidos)) for r in por_replica]
            motivos = sin_decidir(juntado, por_replica, len(partidos))
            fila["oraculo"]["veredicto"]["sin_decidir"] = bool(motivos)
            fila["oraculo"]["veredicto"]["motivos_sin_decidir"] = motivos
            fila["oraculo"]["replicas"] = {
                "pasan": int(sum(v["pasa"] for v in veredictos)), "de": replicas,
                "por_condicion": {c: {conv: {
                    "diferencia_min": float(min(r[c][conv]["diferencia"] for r in por_replica)),
                    "diferencia_max": float(max(r[c][conv]["diferencia"] for r in por_replica)),
                    "diferencia_desviacion": float(np.std([r[c][conv]["diferencia"] for r in por_replica], ddof=1)),
                    "gana_en_min": int(min(r[c][conv]["gana_en"] for r in por_replica)),
                    "gana_en_max": int(max(r[c][conv]["gana_en"] for r in por_replica))}
                    for conv in dfl.CONVENCIONES} for c in dfl.VOTAN}}
            fila["oraculo_r0"] = {"condiciones": r0, "veredicto": veredicto(r0, len(partidos))}
        modo_ref = "propio"
        propio = comparar_todo(de("propio"))
        fila["propio"] = {"condiciones": propio, "veredicto": veredicto(propio, len(partidos))}
        salida[clave(celda)] = fila
    return salida


def referencia_absoluta(resultados, partidos):
    """spellF1 de main con `trk_atd`, los partidos juntos: el ancla frente a lo que da puntuar.py con `{}`."""
    salida = collections.OrderedDict()
    for modo in MODOS:
        for condicion in dfl.VOTAN:
            for conv in dfl.CONVENCIONES:
                junto = pu.juntar([resultados[(p, condicion)][0][modo][conv] for p in partidos])
                salida["{} / {} / {}".format(modo, condicion, conv)] = pu.spell_f1(*junto)
    return salida


# -- salida --------------------------------------------------------------------------------------------

def num(valor, signo=False):
    if valor is None:
        return "–"
    return ("{:+.3f}" if signo else "{:.3f}").format(valor).replace(".", ",")


def dec(valor):
    return "{:g}".format(valor).replace(".", ",")


def intervalo(c):
    i = c["intervalo"]
    return "–" if i is None else "[{} a {}]".format(num(i[0], True), num(i[1], True))


CORTO = {"como el ATD": "ATD", "como el ATD, sin bloques": "sin bloques"}


def tabla(resumen, modo, n_partidos, comprobacion=False):
    cab = ["p", "σ (m)", "L"]
    for conv in ("control", "flag"):
        for cond in dfl.VOTAN:
            cab.append("Δ {} · {} [5–95 %] · gana".format(conv, CORTO[cond]))
    cab += ["cobertura real", "racha de fallos real", "réplicas que pasan", "veredicto"]
    lineas = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for fila in resumen.values():
        if bool(fila["comprobacion"]) != comprobacion:
            continue
        celdas = [dec(fila["p"]), dec(fila["sigma"]), str(fila["L"])]
        for conv in ("control", "flag"):
            for cond in dfl.VOTAN:
                c = fila[modo]["condiciones"][cond][conv]
                celdas.append("{} {} · {}/{}".format(num(c["diferencia"], True), intervalo(c), c["gana_en"], n_partidos))
        v = fila[modo]["veredicto"]
        racha = fila["racha_de_fallos_media_real"]
        rep_ = fila[modo].get("replicas")
        celdas += ["{:.3f}".format(fila["cobertura_real"]).replace(".", ","),
                   "–" if racha is None else "{:.2f}".format(racha).replace(".", ","),
                   "–" if rep_ is None else "{}/{}".format(rep_["pasan"], rep_["de"]),
                   ("**pasa**" if v["pasa"] else "no pasa ({})".format(
                       ", ".join(k for k in ("control", "flag") if not v[k])))
                   + (" · sin decidir" if v.get("sin_decidir") else "")]
        if comprobacion:
            celdas[-1] += " · " + fila["comprobacion"]
        lineas.append("| " + " | ".join(celdas) + " |")
    return lineas


def mapa(resumen, modo):
    """Qué celdas pasan, en una tabla p × (σ, L)."""
    columnas = [(s, l) for s in SIGMAS for l in LS]
    lineas = ["| p \\ σ, L | " + " | ".join("{}, {}".format(dec(s), l) for s, l in columnas) + " |",
              "|---|" + "---|" * len(columnas)]
    for p in PS:
        celdas = []
        for s, l in columnas:
            fila = resumen.get(clave((p, s, l)))
            if fila is None:
                celdas.append("·")
                continue
            v = fila[modo]["veredicto"]
            celdas.append(("**sí**" if v["pasa"] else "no" + ("" if v["control"] else "ᶜ") + ("" if v["flag"] else "ᶠ"))
                          + (" ?" if v.get("sin_decidir") else ""))
        lineas.append("| {} | {} |".format(dec(p), " | ".join(celdas)))
    return lineas


def avisos(resumen, modo):
    """Lo que hay que mirar al leer: el ruido de semilla a p = 1 y las zonas que pasan sin ser monótonas en p."""
    lineas = []
    for s in SIGMAS:
        filas = [resumen.get(clave((1.0, s, l))) for l in LS]
        if any(f is None for f in filas):
            continue
        for conv in ("control", "flag"):
            for cond in dfl.VOTAN:
                d = [f[modo]["condiciones"][cond][conv]["diferencia"] for f in filas]
                lineas.append("- p = 1, σ = {}: Δ {} en «{}» con las tres semillas de L: de {} a {} (rango {}).".format(
                    dec(s), conv, cond, num(min(d), True), num(max(d), True), num(max(d) - min(d))))
    for s in SIGMAS:
        for l in LS:
            pasa = [resumen[clave((p, s, l))][modo]["veredicto"]["pasa"] for p in PS if clave((p, s, l)) in resumen]
            if len(pasa) == len(PS) and any(a and not b for a, b in zip(pasa, pasa[1:])):
                lineas.append("- **No monótona en p** con σ = {}, L = {}: {}.".format(
                    dec(s), l, " ".join("{}:{}".format(dec(p), "sí" if x else "no") for p, x in zip(PS, pasa))))
    dudosas = [k for k, f in resumen.items() if f[modo]["veredicto"].get("sin_decidir")]
    con_replicas = [k for k, f in resumen.items() if f.get("replicas", 1) > 1]
    if con_replicas:
        lineas.append("- **Sin decidir:** {} de las {} celdas con réplicas{}".format(
            len(dudosas), len(con_replicas), (": " + "; ".join(dudosas) + ".") if dudosas else "."))
    return lineas


def sha(ruta):
    with open(ruta, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def commit():
    try:
        corto = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                               check=True).stdout.strip()
        sucio = subprocess.run(["git", "status", "--porcelain", "--", "possession", "validation/harness",
                                "validation/experimento0", "validation/experimento1", "validation/experimento2"],
                               cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"
    return corto + (" (con cambios sin commit en el código que se usa)" if sucio else
                    " (possession/, el harness y los experimentos 0–2 sin cambios)")


REGLA = """**Pasa si, en esa celda y con el `D` de las etiquetas:**
  - con control: +0,01 o más en las dos condiciones que votan, ganando en 6 de 7 partidos;
  - con el flag: no pierde más de 0,005 en ninguna.

La celda que se lee: p, la condición 1 redondeada hacia abajo a la rejilla; σ, el menor de la rejilla cuyo temblor en
la DFL (calibrado con la misma función) es igual o mayor que el que mide la 1b; L, la medida en la 1b redondeada hacia
arriba a la rejilla."""

LECTURA = ("Precisión de la bitácora (16/11, 17:00, antes de medir; la aplica el sondeo): L es la menor de la rejilla "
           "cuya racha media de fallos real en esta emulación (columna «racha de fallos real», en esa p y esa σ, con "
           "todas las réplicas juntas) es igual o mayor que la que mide la 1b; la lectura literal (la etiqueta L "
           "redondeada hacia arriba) se imprime al lado, sin voto. Con L = 1 los fallos son independientes y su racha "
           "media es 1/p. Fuera de la rejilla no pasa: cobertura por debajo de 0,5, temblor mayor que el de σ = 0,25 "
           "en la DFL o una racha de fallos más larga que la mayor racha real de la emulación.")


def informe(resumen, ancla, partidos, args, tiempos, rss, comando):
    n = len(partidos)
    lineas = [
        "# Emulación en la DFL del balón del vídeo (condición 5 de la puerta 1b) · {} · Claude (sesión de Ismael)".format(
            FECHA), "",
        "- **Para qué:** la rejilla de la condición 5 de la puerta 1b (`validation/balon_video/BITACORA.md`, «Corrección "
        "de la puerta 1b»), calculada en datos abiertos antes de que se ejecute la 1b. El sondeo lee de aquí la celda "
        "que mida y da el veredicto (`{}.json`).".format(os.path.basename(SALIDA)),
        "- **Datos:** {} partidos abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0), caché del experimento 0, "
        "con `validation/harness/dfl.py` (condiciones que votan: {}; el balón detectado sale de `limpio`). Nada del "
        "partido.".format(n, ", ".join("«{}»".format(c) for c in dfl.VOTAN)),
        "- **Comando:** `{}` (Python {}, numpy {}; {} procesos, hilos de BLAS a 1).".format(
            comando, platform.python_version(), np.__version__, args.procesos),
        "- **Código:** repo en {}; `emular_dfl.py` sha256 `{}`.".format(commit(), sha(os.path.abspath(__file__))[:16]),
        "- **Qué se compara:** `main` (`{{}}` del harness: B5 dejando fuera el partido que se puntúa) con el balón "
        "emulado, frente a `main` con el balón «como el ATD». spellF1 con los {} partidos juntos, «gana» = partidos en "
        "que el emulado saca más (estrictamente), intervalo 5–95 % del bootstrap pareado del harness con {} sorteos."
        .format(n, args.bootstrap),
        "- **Réplicas:** {} por celda con p ≥ {} (r = 0…{}), una en las demás y en las de comprobación. En cada partido "
        "se juntan las réplicas con `pu.juntar` (su spellF1 da «gana en»); el Δ sale de todas juntas, y el veredicto, "
        "de esos dos. El intervalo es el de la réplica 0 (descriptivo). «Réplicas que pasan»: cuántas pasarían solas. "
        "«Sin decidir» (solo informativo, no lo lee el sondeo): el Δ juntado a menos de {:g} errores estándar del "
        "umbral en alguna condición que vota, o el «gana en» del control de las réplicas a los dos lados del {}. El "
        "`D` propio, solo con la réplica 0.".format(args.replicas, dec(P_REPLICAS), args.replicas - 1,
                                                    ERRORES_ESTANDAR, min(MIN_GANA, n)),
        "- **Tiempo:** {:.0f} s de pared; {:.0f} s de CPU sumando las tareas; memoria máxima por proceso {}."
        .format(tiempos["pared"], tiempos["tareas"], "–" if rss is None else "{:.0f} MB".format(rss)),
        "- **Reproducible:** el JSON no lleva ni el comando ni los tiempos, así que sale igual byte a byte con el mismo "
        "código y en el mismo commit (lleva la línea «codigo»), con cualquier número de procesos.",
        "", "## La regla (copiada de la bitácora, condición 5)", "", REGLA, "",
        "Aquí, «6 de 7» es «{} de {}» si se miden menos partidos.".format(min(MIN_GANA, n), n), "", LECTURA, "",
        "## Referencia: `main` con el balón «como el ATD» (spellF1, los partidos juntos)", "",
        "| D / condición / etiquetas | spellF1 |", "|---|---|"]
    lineas += ["| {} | {} |".format(k, num(v)) for k, v in ancla.items()]
    lineas += ["", "## Filas de comprobación (D de las etiquetas)", ""]
    lineas += tabla(resumen, "oraculo", n, comprobacion=True)
    lineas += ["", "p = 0 da exactamente las etiquetas de `main` en cada partido, condición y `D` (el script lo comprueba "
               "y se pararía si no); por eso «gana» es 0 de {}.".format(n), "",
               "## Qué celdas pasan (D de las etiquetas)", "",
               "«sí» pasa; «no» con ᶜ falla la parte del control y con ᶠ la del flag; « ?», sin decidir.", ""]
    lineas += mapa(resumen, "oraculo")
    lineas += ["", "## La rejilla con el `D` de las etiquetas (decide)", "",
               "Δ = spellF1 emulado − spellF1 de `main`; «ATD» = «como el ATD», «sin bloques» = «como el ATD, sin "
               "bloques». Δ y «gana» con las réplicas juntas. Cobertura real: detectados / frames con balón del ATD. "
               "Racha de fallos real: frames de fallo / rachas de fallos, con todas las réplicas juntas; es la que vota "
               "al leer L (con L = 1 los fallos son independientes y la racha media es 1/p, no 1; con L = 50 los "
               "tramos con balón cortan rachas, y sale menos de 50).", ""]
    lineas += tabla(resumen, "oraculo", n)
    lineas += ["", "## Avisos de lectura (D de las etiquetas)", ""]
    lineas += avisos(resumen, "oraculo") or ["- ninguno"]
    cuentas = collections.defaultdict(int)
    for fila in resumen.values():
        for k, v in fila["cuentas"].items():
            cuentas[k] += v
    lineas += ["", "- En todas las celdas juntas: {} frames detectados sin balón `limpio` (se usó el del ATD); {} de {} "
               "frames detectados ({} %) con el balón limpio a más de 5 m del balón «como el ATD» [medido]. El "
               "detector real descartaría esas detecciones (busca a 5 m o menos del balón del ATD en t+4), así que la "
               "emulación las da por buenas y puede ser optimista ahí [inferencia].".format(
                   cuentas["detectados_sin_limpio"], cuentas["detectados_a_mas_de_5m_del_atd"], cuentas["detectados"],
                   "{:.1f}".format(100.0 * cuentas["detectados_a_mas_de_5m_del_atd"]
                                   / max(cuentas["detectados"], 1)).replace(".", ","))]
    lineas += ["", "## La rejilla con el `D` propio (solo descriptiva, no decide)", ""]
    lineas += mapa(resumen, "propio")
    lineas += [""] + tabla(resumen, "propio", n) + [""] + tabla(resumen, "propio", n, comprobacion=True)
    return "\n".join(lineas) + "\n"


def a_json(resumen, ancla, partidos, args):
    """Sin el comando ni los tiempos (van en el md): el mismo código da el mismo JSON byte a byte."""
    def limpiar(fila):
        return {k: v for k, v in fila.items()}
    return {"fecha": FECHA, "codigo": commit(), "script_sha256": sha(os.path.abspath(__file__)),
            "python": platform.python_version(), "numpy": np.__version__, "partidos": partidos,
            "condiciones_que_votan": list(dfl.VOTAN), "bootstrap": args.bootstrap, "semilla": SEMILLA,
            "rejilla": {"p": list(PS), "sigma": list(SIGMAS), "L": list(LS)},
            "replicas": {"R": args.replicas, "p_minima": P_REPLICAS, "errores_estandar_sin_decidir": ERRORES_ESTANDAR,
                         "semilla": "[SEMILLA, partido, condición, 100·p, 1000·σ, L] (+ [r] si r ≥ 1)"},
            "lectura": LECTURA,
            "regla": {"d": "oraculo", "control_minimo": UMBRAL_CONTROL, "gana_en_minimo": min(MIN_GANA, len(partidos)),
                      "flag_minimo": UMBRAL_FLAG},
            "referencia_main": ancla,
            "celdas": {k: limpiar(v) for k, v in resumen.items()}}


def celda_de(texto):
    p, s, l = texto.split(",")
    return (float(p), float(s), int(l))


def main():
    parser = argparse.ArgumentParser(description="Rejilla de la condición 5 de la puerta 1b en la DFL.")
    parser.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), choices=list(dfl.PARTIDOS))
    parser.add_argument("--celdas", nargs="+", type=celda_de, default=None,
                        help="solo estas celdas «p,σ,L» (para probar); por defecto la rejilla y las comprobaciones")
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--procesos", type=int, default=None,
                        help="por defecto, uno por tarea (partido × condición) hasta el número de CPU")
    parser.add_argument("--replicas", type=int, default=REPLICAS, help="R en las celdas con p ≥ 0,7 (para probar)")
    parser.add_argument("--salida", default=SALIDA, help="prefijo de los ficheros .md y .json")
    args = parser.parse_args()
    celdas = list(args.celdas) if args.celdas else list(COMPROBACION) + list(REJILLA)
    comando = " ".join(["python validation/balon_video/emular_dfl.py"] + sys.argv[1:])
    tareas = [(p, c, celdas, args.replicas) for p in args.partidos for c in dfl.VOTAN]
    if args.procesos is None:
        args.procesos = max(1, min(len(tareas), os.cpu_count() or 1))
    inicio = time.time()
    resultados, segundos, rss = {}, 0.0, None
    if args.procesos > 1:
        with multiprocessing.Pool(args.procesos) as pool:
            salidas = list(pool.imap_unordered(tarea, tareas))
    else:
        salidas = [tarea(t) for t in tareas]
    for partido, condicion, referencia, por_celda, t, memoria in salidas:
        resultados[(partido, condicion)] = (referencia, por_celda)
        segundos += t
        rss = memoria if rss is None else rss if memoria is None else max(rss, memoria)
        print("hecho {} / {} ({:.0f} s)".format(partido, condicion, t), file=sys.stderr)
    pared_tareas = time.time() - inicio
    resumen = resumir(resultados, args.partidos, celdas, args.bootstrap)
    ancla = referencia_absoluta(resultados, args.partidos)
    tiempos = {"pared": time.time() - inicio, "pared_tareas": pared_tareas, "tareas": segundos}
    with open(args.salida + ".md", "w", encoding="utf-8", newline="\n") as handle:
        handle.write(informe(resumen, ancla, args.partidos, args, tiempos, rss, comando))
    with open(args.salida + ".json", "w", encoding="utf-8", newline="\n") as handle:
        json.dump(a_json(resumen, ancla, args.partidos, args), handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    print("escrito {}.md y .json en {:.0f} s".format(args.salida, tiempos["pared"]), file=sys.stderr)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
