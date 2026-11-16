"""Los cambios de equipo entre fases de ataque del Smart Tagging, frente a nuestra entrega.

**Lee datos del partido (ATD y Smart Tagging) y una entrega nuestra: lo ejecuta una persona, en local, nunca
Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/cambios_entre_fases.py --entrega evaluation/results/equipo_v5.csv

Es el agregado P1 de `validation/investigacion_1116/BITACORA.md` (la idea 1.1 de `docs/investigacion_2026-11-16.md`),
con la regla escrita antes de ejecutarlo. Mide si, en los inicios de fase de ataque en que cambia el equipo, nuestra
entrega va con el otro equipo y llega tarde, frente a un placebo con los inicios desplazados.

- Imprime solo agregados del partido entero: recuentos y porcentajes. Una celda de 1 a 4 casos sale como "< 5".
  Nada por frame, por minuto ni por jugada: la salida se puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.

`recuento(trk, eventos, etiquetas)` es una función pura: la prueba
(`validation/scripts/prueba_cambios_entre_fases.py`) la ejecuta con un partido inventado.
"""

import argparse
import os
import sys
import time
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, AQUI)
import fases_smart_tagging as fst  # noqa: E402  (validation/partido/fases_smart_tagging.py)
import games  # noqa: E402
from possession import tracking  # noqa: E402
from starter import load_smart_tagging  # noqa: E402

FICHEROS = ["atd_raw", "atd_meta", "smart_tagging"]
MINIMO_CELDA = 5

# Fijados antes de ejecutar (BITACORA.md, P1); ninguno sale del partido ni de la ventana pública.
FASES_ATAQUE = ("build up", "progression", "creating chances", "long ball", "attacking transition")
TRANSICION = "attacking transition"
REINICIOS = ("set pieces", "goals")
ANTES_S = 5  # s antes del final de la fase anterior en los que se buscan reinicios y huecos
HUECO_S = 5  # s: un hueco del balón de esta duración o más es una parada probable
VENTANA_S = 2  # s a cada lado del inicio (la clase de fases_smart_tagging.py §4)
TARDE_S = (2, 5, 10, 15)  # s: cortes de cuánto tarda la entrega en pasar al equipo de la fase
PLACEBO_S = fst.PLACEBO_S
MINIMO_CAMBIOS = 30
UMBRAL_TARDE = 0.50
FACTOR_PLACEBO = 0.5
CLASES = fst.CLASES
MOTIVOS = ("transición (ya en la capa de los contraataques)", "reinicio", "hueco del balón de 5 s o más")


def fases_de_ataque(eventos, mascara):
    """[(inicio, fin, equipo, código)] de las fases de ataque con equipo que empiezan en un frame evaluado."""
    salida = []
    for evento in eventos:
        codigo = fst.norm(evento["code"])
        if codigo not in FASES_ATAQUE:
            continue
        equipo = fst.EQUIPOS.get(fst.norm(evento["tags"].get("Team")))
        inicio = int(evento["start_frame"])
        if equipo is None or not (0 <= inicio < len(mascara)) or not mascara[inicio]:
            continue
        salida.append((inicio, int(evento["end_frame"]), equipo, codigo))
    return sorted(salida)


def tramo_de(blocks, frame):
    return next((k for k, (a, b) in enumerate(blocks) if a <= frame < b), None)


def hay_hueco(visto, a, b, largo):
    """¿Hay una racha de `largo` frames o más sin balón en [a, b)?"""
    a, b = max(0, a), max(0, b)
    if b - a < largo:
        return False
    sin = ~visto[a:b]
    borde = np.diff(np.concatenate(([0], sin.astype(np.int8), [0])))
    return bool(np.any(np.flatnonzero(borde == -1) - np.flatnonzero(borde == 1) >= largo))


def cambios(eventos, blocks, mascara, visto, fps):
    """(cambios que cuentan [(inicio, equipo, código)], apartados {motivo: n}, total de cambios entre fases)."""
    fases = fases_de_ataque(eventos, mascara)
    reinicios = [(int(e["start_frame"]), int(e["end_frame"])) for e in eventos if fst.norm(e["code"]) in REINICIOS]
    cuentan, apartados, total = [], {m: 0 for m in MOTIVOS}, 0
    for previa, actual in zip(fases[:-1], fases[1:]):
        if actual[2] == previa[2] or tramo_de(blocks, actual[0]) != tramo_de(blocks, previa[0]):
            continue
        total += 1
        inicio = actual[0]
        desde = min(previa[1], inicio) - int(ANTES_S * fps)
        if actual[3] == TRANSICION:
            apartados[MOTIVOS[0]] += 1
        elif any(a <= inicio < b or desde <= a <= inicio for a, b in reinicios):
            apartados[MOTIVOS[1]] += 1
        elif hay_hueco(visto, desde, inicio, int(HUECO_S * fps)):
            apartados[MOTIVOS[2]] += 1
        else:
            cuentan.append((inicio, actual[2], actual[3]))
    return cuentan, apartados, total


def cuanto_tarda(etiquetas, inicio, equipo, fps):
    """Índice del corte de TARDE_S en que la entrega pasa a ser `equipo` tras `inicio` (len(TARDE_S) si no llega
    en el último), o None si ya lo era en el inicio."""
    if etiquetas[inicio] == equipo:
        return None
    tope = min(len(etiquetas), inicio + int(TARDE_S[-1] * fps) + 1)
    llega = np.flatnonzero(etiquetas[inicio:tope] == equipo)
    if not len(llega):
        return len(TARDE_S)
    segundos = llega[0] / float(fps)
    return next(k for k, corte in enumerate(TARDE_S) if segundos <= corte)


def clasificar(lista, etiquetas, mascara, fps, desplazamiento=0):
    """Clases (las de CLASES) y cuánto tarda, de los inicios de `lista` desplazados, en frames evaluados."""
    ventana = int(VENTANA_S * fps)
    clases, tarda = [0] * len(CLASES), [0] * (len(TARDE_S) + 1)
    for inicio, equipo, _ in lista:
        t = inicio + desplazamiento
        if not (1 <= t < len(etiquetas) - 1) or not mascara[t]:
            continue
        clase, _, _ = fst.clase_transicion(etiquetas, t, equipo, ventana)
        clases[clase] += 1
        k = cuanto_tarda(etiquetas, t, equipo, fps)
        if k is not None:
            tarda[k] += 1
    return {"inicios": sum(clases), "clases": clases, "tarda": tarda}


def recuento(trk, eventos, etiquetas):
    """El agregado P1 con un `Tracking`, los eventos del Smart Tagging (como los da starter/load_smart_tagging.load)
    y las etiquetas de una entrega (0 H, 1 A, 2 D, 3 X). Sin suprimir celdas."""
    n = len(trk.bx)
    etiquetas = np.asarray(etiquetas)
    if len(etiquetas) != n:
        raise ValueError("la entrega no tiene tantas filas como frames tiene el tracking")
    fps = int(trk.fps)
    mascara = fst.evaluados(trk)
    visto = np.isfinite(trk.bx) & np.isfinite(trk.by)
    lista, apartados, total = cambios(eventos, trk.blocks, mascara, visto, fps)
    codigos = {}
    for _, _, codigo in lista:
        codigos[codigo] = codigos.get(codigo, 0) + 1
    return {
        "fases_ataque": len(fases_de_ataque(eventos, mascara)),
        "cambios_total": total,
        "apartados": apartados,
        "codigos": codigos,
        "reales": clasificar(lista, etiquetas, mascara, fps),
        "placebo": [clasificar(lista, etiquetas, mascara, fps, s * fps) for s in PLACEBO_S],
    }


def veredicto(r):
    """(sigue, proporción tarde real, proporción tarde del placebo, por qué), con la regla de la bitácora P1."""
    reales = r["reales"]
    n = reales["inicios"]
    tarde = reales["clases"][2] / float(n) if n else None
    inicios_p = sum(p["inicios"] for p in r["placebo"])
    tarde_p = sum(p["clases"][2] for p in r["placebo"]) / float(inicios_p) if inicios_p else None
    if n < MINIMO_CAMBIOS:
        return False, tarde, tarde_p, "hay menos de {} cambios: no sigue y se cierra".format(MINIMO_CAMBIOS)
    uno = tarde >= UMBRAL_TARDE
    dos = tarde_p is not None and tarde_p <= FACTOR_PLACEBO * tarde
    porque = "«era el otro equipo» {} el 50 %; el placebo {} la mitad de los reales".format(
        "llega a" if uno else "NO llega a", "no pasa de" if dos else "PASA de")
    return uno and dos, tarde, tarde_p, porque


def porcentaje(valor):
    return "—" if valor is None else "{:.1f} %".format(100 * valor).replace(".", ",")


def para_imprimir(r, sha=None, minimo=MINIMO_CELDA):
    """Las líneas de la salida, con las celdas pequeñas suprimidas."""
    def celda(k):
        return fst.celda(k, minimo)

    def pct(a, b):
        return fst.pct(a, b, minimo)

    sigue, tarde, tarde_p, porque = veredicto(r)
    reales = r["reales"]
    inicios_p = sum(p["inicios"] for p in r["placebo"])
    lineas = [
        "Cambios de equipo entre fases de ataque del Smart Tagging (validation/investigacion_1116/BITACORA.md, P1): "
        "las dos partes juntas",
        "",
        "0. Controles",
        "   entrega: sha256 {}".format("—" if sha is None else "{}…{}".format(sha[:8], sha[-5:])),
        "   fases de ataque con Team H o A en tramos evaluados: {}".format(celda(r["fases_ataque"])),
        "   cambios de equipo entre fases de ataque seguidas: {}".format(celda(r["cambios_total"])),
    ]
    for motivo in MOTIVOS:
        lineas.append("   apartados por {}: {}".format(motivo, celda(r["apartados"][motivo])))
    lineas += [
        "   cambios que cuentan: {}".format(celda(reales["inicios"])),
        "   por código de la fase nueva: " + "   ".join(
            "{} {}".format(c, celda(k)) for c, k in sorted(r["codigos"].items())),
        "",
        "1. La entrega en el inicio de cada cambio (±{} s)".format(VENTANA_S),
    ]
    for k, nombre in enumerate(CLASES):
        placebo_k = sum(p["clases"][k] for p in r["placebo"])
        lineas.append("   {:<32} reales {:>4} ({:>7})   placebo {:>4} de {} ({})".format(
            nombre, celda(reales["clases"][k]), pct(reales["clases"][k], reales["inicios"]), celda(placebo_k),
            inicios_p, pct(placebo_k, inicios_p)))
    cortes = ["hasta {} s".format(TARDE_S[0])]
    cortes += ["de {} a {} s".format(a, b) for a, b in zip(TARDE_S[:-1], TARDE_S[1:])]
    cortes.append("más de {} s o nunca".format(TARDE_S[-1]))
    tarda_p = [sum(p["tarda"][k] for p in r["placebo"]) for k in range(len(cortes))]
    lineas += ["", "2. Cuánto tarda la entrega en pasar al equipo de la fase (si no lo era ya en el inicio)"]
    for k, nombre in enumerate(cortes):
        lineas.append("   {:<22} reales {:>4}   placebo {:>4}".format(nombre, celda(reales["tarda"][k]),
                                                                   celda(tarda_p[k])))
    lineas += [
        "",
        "3. Regla (BITACORA.md P1): {} cambios o más, «era el otro equipo» en el {:.0f} % o más, y el placebo en la "
        "mitad o menos".format(MINIMO_CAMBIOS, 100 * UMBRAL_TARDE),
        "   «era el otro equipo»: reales {}   placebo {}".format(porcentaje(tarde), porcentaje(tarde_p)),
        "   → {}: {}".format("SIGUE (se programa la capa, apagada)" if sigue else "NO SIGUE", porque),
    ]
    return lineas


def medir(entrega, data_dir=None):
    """El agregado sobre el partido. Lee datos del partido y una entrega: solo lo ejecuta una persona."""
    game = games.GAME
    games.require(FICHEROS, game, data_dir)
    trk = tracking.from_atd(games.asset_paths(game, data_dir), game)
    eventos = load_smart_tagging.load(game, data_dir)
    etiquetas, sha = fst.leer_entrega(entrega, len(trk.bx))
    return recuento(trk, eventos, etiquetas), sha


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entrega", required=True, help="CSV frame,label de la entrega vigente (equipo_v5 o equipo_v8)")
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    inicio = time.time()
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD o el Smart Tagging del partido: revisa que MTAH_DATA_DIR (o --data-dir) apunte "
              "a la carpeta de los datos.")
        return 1
    if not os.path.isfile(args.entrega):
        print("No encuentro la entrega: genérala con  python -m possession.pipeline --name <nombre>")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # los avisos de numpy no llevan datos, pero ensucian la salida
        resultado, sha = medir(args.entrega, args.data_dir)
        lineas = para_imprimir(resultado, sha)
    print("\n".join(lineas))
    print("\n   tiempo {:.0f} s".format(time.time() - inicio))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(fst.informe_de_error(e))
        sys.exit(1)
