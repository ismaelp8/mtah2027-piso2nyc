"""La puerta 2.1 con el `D` propio y réplicas: la misma emulación de `emular_dfl.py`, repetida 8 veces por celda.

Por qué (`validation/balon_video/BITACORA.md`, «Precisión de la puerta 2.1», escrita el 16/11 antes de leer ninguna
cifra del partido): la 2.1 pide pasar con el `D` de las etiquetas y con el propio. `emular_dfl.py` calcula el `D`
propio con una sola tirada por celda (la réplica 0), porque para la 1b era solo descriptivo; el ruido de una tirada es
del orden de la distancia al +0,01. Aquí se calcula con R = 8 réplicas en las celdas con p ≥ 0,7: las mismas semillas,
el mismo balón emulado y la misma forma de juntar que el `D` de las etiquetas.

No toca `emular_dfl.py` ni su JSON (lo leen por su nombre el sondeo y la detección): importa sus funciones. Se para si
el `emular_dfl.py` que importa no es el que escribió ese JSON (`script_sha256`).

**El decodificador va fijado** con `--temporal` (por defecto `decode`, el de `equipo_v8`), y no se toma de
`pipeline.PIECES`: así el resultado no cambia según el commit en que se ejecute. Desde que `main` usa
`decode_cortas_a_d` (`equipo_v9`), la 2.1 con el `D` propio se mide también con ese decodificador
(`--temporal decode_cortas_a_d`, con su propio fichero de salida). El JSON y el md apuntan el decodificador.

**Comprobación:** con `--temporal decode`, la réplica 0 tiene que dar, celda a celda, las cifras del `D` propio del JSON
de la emulación, que se midió con ese decodificador (spellF1, Δ, «gana en» y posesiones predichas, en las dos
condiciones que votan y las dos convenciones). El resultado va en `comprobacion_r0`. Si no coincide, con este fichero no
se lee nada y el script acaba con código 1. Con otro decodificador no hay con qué comparar la réplica 0: lo que lo
respalda es que el mismo script, con `--temporal decode`, reproduce la emulación.

**Solo las celdas con p ≥ 0,7,** como las réplicas de las 18:30 para el `D` de las etiquetas. Con p < 0,7 queda la
tirada única de `emular_dfl.py`, con los dos `D`.

**El fichero que decide no se pisa:** con `--partidos`, `--celdas` o `--replicas` distintos de los de por defecto hace
falta `--salida`.

Datos abiertos de otros partidos: los 7 de la Bundesliga (Bassek et al., 2025, CC BY 4.0), con la caché del
experimento 0 y el harness. Lo puede ejecutar cualquiera, Claude incluido. Solo escribe agregados.

Qué se mide en cada celda: `main` (`{}` del harness: B5 dejando fuera el partido que se puntúa) con el balón emulado
frente a `main` con el balón «como el ATD», los dos con el `D` propio, en las dos convenciones. El veredicto es el de
`emular_dfl.veredicto`: con control, +0,01 o más y 6 de 7 en las dos condiciones que votan; con el flag, no pierde más
de 0,005 en ninguna. «Sin decidir» (`emular_dfl.sin_decidir`) se imprime y no vota. El intervalo es el de la réplica 0
del JSON de la emulación (descriptivo); aquí no se recalcula.

Uso, desde la raíz del repo:

    python validation/balon_video/emular_dfl_propio.py                  # las 48 celdas con p ≥ 0,7, con decode
    python validation/balon_video/emular_dfl_propio.py --temporal decode_cortas_a_d     # lo mismo, con el de v9
    python validation/balon_video/emular_dfl_propio.py --partidos J03WMX --celdas 0.8,0.06,12 --salida /tmp/x
"""

import argparse
import collections
import hashlib
import json
import multiprocessing
import os
import platform
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import emular_dfl as em  # noqa: E402  (fija los hilos de BLAS a 1 y pone el harness en la ruta)

import numpy as np  # noqa: E402

dfl, pu = em.dfl, em.pu
MODO = "propio"
EMULACION = em.SALIDA + ".json"
SALIDA = em.SALIDA + "_propio"
TEMPORAL = "decode"  # el decodificador con que se midió el JSON de la emulación (el de equipo_v8)
CELDAS = tuple(c for c in em.REJILLA if c[0] >= em.P_REPLICAS)
TOLERANCIA = 1e-12  # la réplica 0 frente al JSON de la emulación: las mismas cuentas en otra máquina
CIFRAS = ("spell_f1", "spell_f1_main", "diferencia")
ENTERAS = ("gana_en", "posesiones_predichas", "posesiones_predichas_main", "posesiones_reales")


def sha_lf(ruta):
    """sha256 del fichero con los finales de línea de git (LF): en un Windows con `core.autocrlf` el fichero en disco
    lleva CRLF y su sha256 tal cual no es el del commit."""
    with open(ruta, "rb") as handle:
        return hashlib.sha256(handle.read().replace(bytes([13, 10]), bytes([10]))).hexdigest()


def salida_por_defecto(temporal):
    return SALIDA if temporal == TEMPORAL else "{}_{}".format(SALIDA, temporal)


_VERSIONES = {}


def version(temporal):
    """`main` del harness con el decodificador `temporal` fijado (el resto de piezas, las de `pipeline.PIECES`)."""
    if temporal not in _VERSIONES:
        _VERSIONES[temporal] = pu.version_de({"piezas": {"temporal": temporal}}, "main con temporal={}".format(temporal))
    return _VERSIONES[temporal]


def tarea(args):
    """Recuentos con el `D` propio de la referencia y de cada réplica de cada celda, en un partido y una condición."""
    partido, condicion, celdas, replicas, temporal = args
    inicio = time.time()
    main = version(temporal)
    cargado = dfl.cargar(partido)
    gt = cargado["gt"]
    atd = pu.solo_lectura(dfl.tracking_de(cargado, condicion))
    limpio = dfl.tracking_de(cargado, "limpio")
    em.comprobar_iguales(atd, limpio)
    pred_ref = pu.ejecutar(main, atd, gt["flag"], MODO, partido)
    referencia = {c: em.recuento(gt[c], pred_ref) for c in dfl.CONVENCIONES}
    por_celda = collections.OrderedDict()
    for celda in celdas:
        fila = []
        for r in range(replicas):
            rng = np.random.default_rng(em.semilla_de(cargado["indice"], dfl.CONDICIONES.index(condicion), celda, r))
            bx, by, _ = em.emular(atd, limpio, celda, rng)
            emulado = pu.solo_lectura(atd._replace(bx=bx, by=by))
            pred = pu.ejecutar(main, emulado, gt["flag"], MODO, partido)
            fila.append({c: em.recuento(gt[c], pred) for c in dfl.CONVENCIONES})
        por_celda[celda] = fila
    return partido, condicion, referencia, por_celda, time.time() - inicio


def comparar_todo(resultados, partidos, celda, replicas, intervalos):
    """Por condición y convención, `em.comparar` con las réplicas de `replicas` (una lista de índices)."""
    por_condicion = collections.OrderedDict()
    for condicion in dfl.VOTAN:
        por_condicion[condicion] = collections.OrderedDict()
        for conv in dfl.CONVENCIONES:
            emulados = [[resultados[(p, condicion)][1][celda][r][conv] for r in replicas] for p in partidos]
            referencias = [resultados[(p, condicion)][0][conv] for p in partidos]
            por_condicion[condicion][conv] = em.comparar(emulados, referencias, partidos, 0,
                                                         intervalo=intervalos[condicion][conv])
    return por_condicion


def comprobar_r0(r0, guardado):
    """Nombres de las cifras de la réplica 0 que no coinciden con el `D` propio del JSON de la emulación."""
    distintas = []
    for condicion in dfl.VOTAN:
        for conv in dfl.CONVENCIONES:
            mio, suyo = r0[condicion][conv], guardado[condicion][conv]
            for k in CIFRAS:
                if abs(float(mio[k]) - float(suyo[k])) > TOLERANCIA:
                    distintas.append("{} / {} / {}".format(condicion, conv, k))
            for k in ENTERAS:
                if int(mio[k]) != int(suyo[k]):
                    distintas.append("{} / {} / {}".format(condicion, conv, k))
    return distintas


def resumir(resultados, partidos, celdas, replicas, emulacion, comparar=True):
    """`comparar`: si la réplica 0 se compara con el `D` propio del JSON de la emulación (solo con su mismo
    decodificador, `TEMPORAL`). Sin comparar, de ese JSON solo se toma el veredicto con el `D` de las etiquetas, que no
    depende del decodificador: con el `D` de las etiquetas, `cortas_a_d` no puede convertir nada (`D` no está
    permitido en el juego)."""
    salida = collections.OrderedDict()
    for celda in celdas:
        guardada = emulacion["celdas"].get(em.clave(celda)) if emulacion else None
        if guardada is not None and comparar:
            intervalos = {c: {conv: guardada[MODO]["condiciones"][c][conv]["intervalo"] for conv in dfl.CONVENCIONES}
                          for c in dfl.VOTAN}
        else:
            intervalos = {c: {conv: "sin calcular" for conv in dfl.CONVENCIONES} for c in dfl.VOTAN}
        por_replica = [comparar_todo(resultados, partidos, celda, [r], intervalos) for r in range(replicas)]
        juntado = comparar_todo(resultados, partidos, celda, list(range(replicas)), intervalos)
        veredictos = [em.veredicto(r, len(partidos)) for r in por_replica]
        veredicto = em.veredicto(juntado, len(partidos))
        motivos = em.sin_decidir(juntado, por_replica, len(partidos))
        veredicto["sin_decidir"] = bool(motivos)
        veredicto["motivos_sin_decidir"] = motivos
        fila = {"p": celda[0], "sigma": celda[1], "L": celda[2], "replicas": replicas,
                "propio": {"condiciones": juntado, "veredicto": veredicto,
                           "replicas": {
                               "pasan": int(sum(v["pasa"] for v in veredictos)), "de": replicas,
                               "por_condicion": {c: {conv: {
                                   "diferencia_min": float(min(r[c][conv]["diferencia"] for r in por_replica)),
                                   "diferencia_max": float(max(r[c][conv]["diferencia"] for r in por_replica)),
                                   "diferencia_desviacion": (float(np.std([r[c][conv]["diferencia"]
                                                                           for r in por_replica], ddof=1))
                                                             if replicas > 1 else None),
                                   "gana_en_min": int(min(r[c][conv]["gana_en"] for r in por_replica)),
                                   "gana_en_max": int(max(r[c][conv]["gana_en"] for r in por_replica))}
                                   for conv in dfl.CONVENCIONES} for c in dfl.VOTAN}}},
                "propio_r0": {"condiciones": por_replica[0], "veredicto": veredictos[0]}}
        if guardada is None:
            fila["comprobacion_r0"] = {"coincide": None, "no_coinciden": ["la celda no está en el JSON de la emulación"]}
        elif not comparar:
            fila["comprobacion_r0"] = {"coincide": None, "no_coinciden": [
                "no se compara: el JSON de la emulación se midió con temporal={}".format(TEMPORAL)]}
            fila["pasa_con_el_d_de_las_etiquetas"] = bool(guardada["oraculo"]["veredicto"]["pasa"])
        else:
            distintas = comprobar_r0(por_replica[0], guardada[MODO]["condiciones"])
            fila["comprobacion_r0"] = {"coincide": not distintas, "no_coinciden": distintas}
            fila["pasa_en_la_emulacion_con_una_tirada"] = bool(guardada[MODO]["veredicto"]["pasa"])
            fila["pasa_con_el_d_de_las_etiquetas"] = bool(guardada["oraculo"]["veredicto"]["pasa"])
        salida[em.clave(celda)] = fila
    return salida


def comprobacion_global(resumen, comparar=True):
    con_json = [f for f in resumen.values() if f["comprobacion_r0"]["coincide"] is not None]
    bien = sum(f["comprobacion_r0"]["coincide"] for f in con_json)
    return {"aplica": bool(comparar), "celdas": len(resumen), "celdas_en_la_emulacion": len(con_json),
            "coinciden": int(bien), "coincide_todo": bool(con_json) and bien == len(con_json) == len(resumen),
            "tolerancia": TOLERANCIA}


def texto_comprobacion(global_, temporal):
    if not global_["aplica"]:
        return ("- **Comprobación de la réplica 0:** no aplica. El JSON de la emulación se midió con `temporal={}` y "
                "aquí va `temporal={}`. Lo que respalda este fichero es que el mismo script, con `--temporal {}`, "
                "reproduce la emulación (`2026-11-16_emulacion_dfl_propio.json`, 48 de 48 celdas).".format(
                    TEMPORAL, temporal, TEMPORAL))
    return ("- **Comprobación de la réplica 0** frente al `D` propio del JSON de la emulación: coinciden {} de {} "
            "celdas (tolerancia {:g}). {}".format(
                global_["coinciden"], global_["celdas"], TOLERANCIA,
                "**Coincide todo.**" if global_["coincide_todo"]
                else "**NO COINCIDE TODO: con este fichero no se lee nada.**"))


def texto_veredicto(v):
    if v["pasa"]:
        base = "**pasa**"
    else:
        base = "no pasa ({})".format(" y ".join(n for n, ok in (("control", v["control"]), ("flag", v["flag"]))
                                               if not ok))
    return base + (" · sin decidir" if v.get("sin_decidir") else "")


def informe(resumen, partidos, args, tiempos, comando, global_):
    n = len(partidos)
    corto = em.CORTO
    lineas = [
        "# Puerta 2.1 del balón del vídeo: la emulación en la DFL con el `D` propio y réplicas · {} · Claude (sesión "
        "de Ismael)".format(em.FECHA), "",
        "- **Para qué:** la pata del `D` propio de la puerta 2.1 (`validation/balon_video/BITACORA.md`, «Precisión de "
        "la puerta 2.1», escrita antes de leer ninguna cifra del partido). La 2.1 se lee en la celda que dé la "
        "detección del partido entero: con el `D` de las etiquetas, en `{}`; con el propio, aquí.".format(
            os.path.basename(EMULACION)),
        "- **Datos:** {} partidos abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0), caché del experimento 0, "
        "con `validation/harness/dfl.py`. Nada del partido.".format(n),
        "- **Comando:** `{}` (Python {}, numpy {}; {} procesos, hilos de BLAS a 1).".format(
            comando, platform.python_version(), np.__version__, args.procesos),
        "- **Código:** repo en {}; `emular_dfl.py` sha256 `{}`{}; `emular_dfl_propio.py` sha256 `{}`.".format(
            em.commit(), sha_lf(em.__file__)[:16],
            " (el que escribió el JSON de la emulación)" if global_["celdas_en_la_emulacion"] else "",
            sha_lf(os.path.abspath(__file__))[:16]),
        "- **Decodificador:** `temporal={}` (fijado con `--temporal`; el resto de piezas, las de `pipeline.PIECES`)."
        .format(args.temporal),
        "- **Réplicas:** {} por celda (r = 0…{}), con las semillas de `emular_dfl.py`. En cada partido se juntan con "
        "`pu.juntar` (su spellF1 da «gana»); el Δ sale de todas juntas, y el veredicto, de esos dos.".format(
            args.replicas, args.replicas - 1),
        texto_comprobacion(global_, args.temporal),
        "- **Tiempo:** {:.0f} s de pared; {:.0f} s de CPU sumando las tareas.".format(tiempos["pared"],
                                                                                      tiempos["tareas"]),
        "", "## Qué celdas pasan con el `D` propio", "",
        "«sí» pasa; «no» con ᶜ falla la parte del control y con ᶠ la del flag; « ?», sin decidir. Entre paréntesis, lo "
        "que decía la tirada única del JSON de la emulación, si era distinto.", ""]
    sigmas_ls = sorted({(f["sigma"], f["L"]) for f in resumen.values()})
    lineas += ["| p \\ σ, L | " + " | ".join("{}, {}".format(em.dec(s), l) for s, l in sigmas_ls) + " |",
               "|---|" + "---|" * len(sigmas_ls)]
    for p in sorted({f["p"] for f in resumen.values()}):
        celdas = []
        for s, l in sigmas_ls:
            fila = resumen.get(em.clave((p, s, l)))
            if fila is None:
                celdas.append("–")
                continue
            v = fila["propio"]["veredicto"]
            texto = "**sí**" if v["pasa"] else "no" + ("" if v["control"] else "ᶜ") + ("" if v["flag"] else "ᶠ")
            texto += " ?" if v["sin_decidir"] else ""
            antes = fila.get("pasa_en_la_emulacion_con_una_tirada")
            if antes is not None and antes != v["pasa"]:
                texto += " (antes, {})".format("sí" if antes else "no")
            celdas.append(texto)
        lineas.append("| {} | ".format(em.dec(p)) + " | ".join(celdas) + " |")
    cambian = [k for k, f in resumen.items()
               if f.get("pasa_en_la_emulacion_con_una_tirada") not in (None, f["propio"]["veredicto"]["pasa"])]
    lineas += ["", "- Celdas cuyo veredicto con réplicas es distinto del de la tirada única: {} de {}.".format(
        len(cambian), len(resumen)),
        "- Celdas que pasan con el `D` propio: {} de {}. De ellas, también con el de las etiquetas: {}.".format(
            sum(f["propio"]["veredicto"]["pasa"] for f in resumen.values()), len(resumen),
            sum(f["propio"]["veredicto"]["pasa"] and bool(f.get("pasa_con_el_d_de_las_etiquetas"))
                for f in resumen.values())),
        "", "## La rejilla con el `D` propio", "",
        "Δ = spellF1 emulado − spellF1 de `main`, con las réplicas juntas; «gana» = partidos en que el emulado saca "
        "más. Entre corchetes, el mínimo y el máximo del Δ entre réplicas.", ""]
    cabecera = ["p", "σ (m)", "L"]
    for conv in ("control", "flag"):
        for c in dfl.VOTAN:
            cabecera.append("Δ {} · {} [mín a máx] · gana".format(conv, corto.get(c, c)))
    cabecera += ["réplicas que pasan", "veredicto", "con el `D` de las etiquetas"]
    lineas += ["| " + " | ".join(cabecera) + " |", "|" + "---|" * len(cabecera)]
    for fila in resumen.values():
        celdas = [em.dec(fila["p"]), em.dec(fila["sigma"]), str(fila["L"])]
        for conv in ("control", "flag"):
            for c in dfl.VOTAN:
                x = fila["propio"]["condiciones"][c][conv]
                rep = fila["propio"]["replicas"]["por_condicion"][c][conv]
                celdas.append("{} [{} a {}] · {}/{}".format(em.num(x["diferencia"], signo=True),
                                                           em.num(rep["diferencia_min"], signo=True),
                                                           em.num(rep["diferencia_max"], signo=True),
                                                           x["gana_en"], n))
        celdas.append("{} de {}".format(fila["propio"]["replicas"]["pasan"], fila["propio"]["replicas"]["de"]))
        celdas.append(texto_veredicto(fila["propio"]["veredicto"]))
        etiquetas = fila.get("pasa_con_el_d_de_las_etiquetas")
        celdas.append("–" if etiquetas is None else "pasa" if etiquetas else "no pasa")
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas) + "\n"


def a_json(resumen, partidos, args, global_):
    """Sin el comando ni los tiempos (van en el md): el mismo código da el mismo JSON byte a byte."""
    return {"fecha": em.FECHA, "codigo": em.commit(), "script_sha256": sha_lf(os.path.abspath(__file__)),
            "emular_dfl_sha256": sha_lf(em.__file__), "emulacion": os.path.basename(EMULACION),
            "temporal": args.temporal,
            "python": platform.python_version(), "numpy": np.__version__, "partidos": partidos,
            "condiciones_que_votan": list(dfl.VOTAN), "semilla": em.SEMILLA,
            "replicas": {"R": args.replicas, "p_minima": em.P_REPLICAS,
                         "errores_estandar_sin_decidir": em.ERRORES_ESTANDAR,
                         "semilla": "[SEMILLA, partido, condición, 100·p, 1000·σ, L] (+ [r] si r ≥ 1)"},
            "regla": {"d": MODO, "control_minimo": em.UMBRAL_CONTROL,
                      "gana_en_minimo": min(em.MIN_GANA, len(partidos)), "flag_minimo": em.UMBRAL_FLAG},
            "comprobacion_r0": global_, "celdas": resumen}


def main():
    parser = argparse.ArgumentParser(description="La puerta 2.1 con el D propio y réplicas, en la DFL.")
    parser.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), choices=list(dfl.PARTIDOS))
    parser.add_argument("--celdas", nargs="+", type=em.celda_de, default=None,
                        help="solo estas celdas «p,σ,L» (para probar); por defecto, las de p ≥ 0,7")
    parser.add_argument("--procesos", type=int, default=None,
                        help="por defecto, uno por tarea (partido × condición) hasta el número de CPU")
    parser.add_argument("--replicas", type=int, default=em.REPLICAS, help="R (para probar)")
    parser.add_argument("--temporal", default=TEMPORAL,
                        help="el decodificador, una función de possession/temporal.py (por defecto {}, el de "
                             "equipo_v8; decode_cortas_a_d es el de equipo_v9)".format(TEMPORAL))
    parser.add_argument("--salida", default=None,
                        help="prefijo de los ficheros .md y .json (por defecto, el fichero que decide; obligatorio "
                             "con --partidos, --celdas o --replicas distintos de los de por defecto)")
    args = parser.parse_args()
    celdas = list(args.celdas) if args.celdas else list(CELDAS)
    bajas = [em.clave(c) for c in celdas if c[0] < em.P_REPLICAS]
    if bajas:
        sys.exit("ERROR: con p < {} la 2.1 se lee con la tirada única de emular_dfl.py, no aquí: {}".format(
            em.dec(em.P_REPLICAS), ", ".join(bajas)))
    de_prueba = (list(args.partidos) != list(dfl.PARTIDOS) or celdas != list(CELDAS) or args.replicas != em.REPLICAS)
    if args.salida is None:
        if de_prueba:
            sys.exit("ERROR: con --partidos, --celdas o --replicas distintos de los de por defecto, pasa --salida "
                     "(si no, se pisaría el fichero que decide)")
        args.salida = salida_por_defecto(args.temporal)
    version(args.temporal)  # una errata en --temporal falla aquí, antes de medir
    comparar = args.temporal == TEMPORAL
    emulacion = None
    if os.path.isfile(EMULACION):
        with open(EMULACION, encoding="utf-8") as handle:
            emulacion = json.load(handle)
        # El sha256 del JSON puede ser el de los bytes con LF (el de git) o con CRLF (un checkout de Windows).
        if emulacion.get("script_sha256") not in (sha_lf(em.__file__), em.sha(em.__file__)):
            sys.exit("ERROR: emular_dfl.py no es el que escribió el JSON de la emulación (script_sha256 distinto)")
        if list(emulacion.get("partidos", [])) != list(args.partidos):
            emulacion = None  # con menos partidos (una prueba) no hay con qué comparar la réplica 0
    comando = " ".join(["python validation/balon_video/emular_dfl_propio.py"] + sys.argv[1:])
    tareas = [(p, c, celdas, args.replicas, args.temporal) for p in args.partidos for c in dfl.VOTAN]
    if args.procesos is None:
        args.procesos = max(1, min(len(tareas), os.cpu_count() or 1))
    inicio = time.time()
    resultados, segundos = {}, 0.0
    if args.procesos > 1:
        with multiprocessing.Pool(args.procesos) as pool:
            salidas = []
            for hecho in pool.imap_unordered(tarea, tareas):
                salidas.append(hecho)
                print("hecho {} / {} ({:.0f} s)".format(hecho[0], hecho[1], hecho[4]), file=sys.stderr)
    else:
        salidas = [tarea(t) for t in tareas]
    for partido, condicion, referencia, por_celda, t in salidas:
        resultados[(partido, condicion)] = (referencia, por_celda)
        segundos += t
    resumen = resumir(resultados, args.partidos, celdas, args.replicas, emulacion, comparar)
    global_ = comprobacion_global(resumen, comparar)
    tiempos = {"pared": time.time() - inicio, "tareas": segundos}
    with open(args.salida + ".md", "w", encoding="utf-8", newline="\n") as handle:
        handle.write(informe(resumen, args.partidos, args, tiempos, comando, global_))
    with open(args.salida + ".json", "w", encoding="utf-8", newline="\n") as handle:
        json.dump(a_json(resumen, args.partidos, args, global_), handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    print("escrito {}.md y .json en {:.0f} s".format(args.salida, tiempos["pared"]), file=sys.stderr)
    if not comparar:
        print("réplica 0: no se compara (temporal={}; la emulación se midió con {})".format(args.temporal, TEMPORAL),
              file=sys.stderr)
        return 0
    print("réplica 0 frente a la emulación: coinciden {} de {} celdas".format(global_["coinciden"], global_["celdas"]),
          file=sys.stderr)
    if emulacion is not None and not global_["coincide_todo"]:
        print("ERROR: la réplica 0 no reproduce la emulación: con este fichero no se lee nada", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
