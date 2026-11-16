"""Cómo son los slots que sobran cuando un equipo tiene más de 11 a la vez (P3 de validation/investigacion_1116/BITACORA.md).

**Lee datos del partido (el ATD) y una entrega nuestra: lo ejecuta una persona, en local, nunca Claude** (regla nº 1
de `CLAUDE.md`).

    python validation/partido/slots_sobrantes.py --entrega evaluation/results/equipo_v8.csv

Es el paso 1 del candidato «quitar los slots sobrantes»: describe los sobrantes y, con la regla escrita antes en la
bitácora, dice qué arreglo se escribe («fuera del campo», «duplicado» o «el más nuevo»).

- Imprime solo agregados del partido entero: recuentos y porcentajes. Una celda de 1 a 4 casos sale como "< 5". Nada
  por frame, por slot ni por jugada: la salida se puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.

`describir(trk, etiquetas)` es una función pura: la prueba (`validation/scripts/prueba_slots_sobrantes.py`) la ejecuta
con un partido inventado.
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
import fases_smart_tagging as fst  # noqa: E402  (leer_entrega, celda, pct, informe_de_error)
import games  # noqa: E402
from possession import tracking  # noqa: E402
from possession.tracking import D  # noqa: E402

FICHEROS = ["atd_raw", "atd_meta"]
MINIMO_CELDA = 5
BLOQUE = 20000

# Fijados antes de ejecutar (BITACORA.md, P3); ninguno sale del partido ni de la ventana pública.
JUGADORES = 11
DURACIONES_S = (1, 5, 30)  # cortes: menos de 1 s, de 1 a 5, de 5 a 30, 30 o más
LINEA_M = ((3.0, "más de 3 m fuera"), (1.0, "de 1 a 3 m fuera"), (0.0, "a menos de 1 m por fuera"),
           (-2.0, "a menos de 2 m por dentro"))  # y si no, «más adentro»
VELOCIDAD_LAG = 25  # frames a cada lado: velocidad en 2 s
VELOCIDADES = (0.5, 2.0)
COMPANERO_M = (0.5, 1.0, 3.0)
LEJOS_M = (3.0, 15.0)
BALON_M = (3.0, 10.0, 30.0)
FUERA_COMPROBACION_M = 1.0
PAREJA_M = 0.5
UMBRAL = 0.5
ARREGLOS = ("fuera del campo", "duplicado", "el más nuevo")


def presencia(trk, columnas):
    return np.isfinite(trk.px[:, columnas]) & np.isfinite(trk.py[:, columnas])


def edades(presente):
    """Frames que lleva visto cada slot sin cortarse (0 en el primero), −1 donde no está."""
    n = len(presente)
    indice = np.arange(n, dtype=np.int32)[:, None]
    ausente = np.maximum.accumulate(np.where(~presente, indice, -1), axis=0)
    return np.where(presente, indice - ausente - 1, -1)


def rachas(m):
    borde = np.diff(np.concatenate(([0], m.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(borde == 1), np.flatnonzero(borde == -1)))


def caja(valores, cortes):
    """Índice del intervalo de cada valor con los cortes crecientes: 0 si < cortes[0], …, len(cortes) si ≥ el último."""
    return np.searchsorted(np.asarray(cortes), valores, side="right")


def describir(trk, etiquetas):
    """Los agregados de P3 con un `Tracking` y las etiquetas de una entrega (0 H, 1 A, 2 D, 3 X). Sin suprimir."""
    n = len(trk.bx)
    etiquetas = np.asarray(etiquetas)
    if len(etiquetas) != n:
        raise ValueError("la entrega no tiene tantas filas como frames tiene el tracking")
    fps = float(trk.fps)
    largo, ancho = float(trk.pitch[0]), float(trk.pitch[1])
    evaluado = fst.evaluados(trk)
    team = np.asarray(trk.team)
    px, py = np.asarray(trk.px, dtype=np.float64), np.asarray(trk.py, dtype=np.float64)
    columnas = [np.flatnonzero(team == k) for k in (0, 1)]
    presente = [presencia(trk, c) for c in columnas]
    cuenta = [p.sum(axis=1) for p in presente]
    sobra = [evaluado & (c > JUGADORES) for c in cuenta]
    alguno = sobra[0] | sobra[1]
    r = {"evaluados": int(evaluado.sum()), "con_sobrantes": int(alguno.sum()),
         "por_equipo": [int((sobra[0] & ~sobra[1]).sum()), int((sobra[1] & ~sobra[0]).sum()),
                        int((sobra[0] & sobra[1]).sum())]}
    maximo = np.maximum(np.where(sobra[0], cuenta[0], 0), np.where(sobra[1], cuenta[1], 0))
    r["slots"] = [int(np.sum(alguno & (maximo == 12))), int(np.sum(alguno & (maximo == 13))),
                  int(np.sum(alguno & (maximo >= 14)))]
    duraciones = np.array([b - a for a, b in rachas(alguno)], dtype=float) / fps
    r["rachas"] = np.bincount(caja(duraciones, DURACIONES_S), minlength=len(DURACIONES_S) + 1).tolist()
    r["rachas_frames"] = [int(sum(d * fps for d in duraciones if k == caja([d], DURACIONES_S)[0]))
                          for k in range(len(DURACIONES_S) + 1)]

    # el sobrante: el slot más nuevo del equipo que pasa de 11, en cada frame con sobrantes (uno por equipo)
    muestra_t, muestra_col, muestra_eq = [], [], []
    for k in (0, 1):
        t = np.flatnonzero(sobra[k])
        if not len(t):
            continue
        e = edades(presente[k])[t]
        e = np.where(e >= 0, e, np.iinfo(np.int32).max)
        j = np.argmin(e, axis=1)
        muestra_t.append(t)
        muestra_col.append(columnas[k][j])
        muestra_eq.append(np.full(len(t), k))
    if muestra_t:
        t, col, eq = (np.concatenate(v) for v in (muestra_t, muestra_col, muestra_eq))
    else:
        t = col = eq = np.zeros(0, dtype=int)
    x, y = px[t, col], py[t, col]
    margen = np.maximum.reduce([-x, x - largo, -y, y - ancho]) if len(t) else np.zeros(0)
    sitio = np.full(len(t), len(LINEA_M))
    for k, (corte, _) in reversed(list(enumerate(LINEA_M))):
        sitio = np.where(margen > corte, k, sitio)
    antes, despues = np.clip(t - VELOCIDAD_LAG, 0, n - 1), np.clip(t + VELOCIDAD_LAG, 0, n - 1)
    with np.errstate(invalid="ignore"):
        velocidad = np.hypot(px[despues, col] - px[antes, col], py[despues, col] - py[antes, col]) / (
            2.0 * VELOCIDAD_LAG / fps)
    velocidad[(t - VELOCIDAD_LAG < 0) | (t + VELOCIDAD_LAG >= n)] = np.nan
    companero, cualquiera = np.full(len(t), np.inf), np.full(len(t), np.inf)
    for k in (0, 1):
        cx, cy = px[t][:, columnas[k]], py[t][:, columnas[k]]
        d = np.hypot(cx - x[:, None], cy - y[:, None])
        d = np.where(np.isfinite(d) & (columnas[k][None, :] != col[:, None]), d, np.inf)
        minimo = d.min(axis=1) if d.shape[1] else np.full(len(t), np.inf)
        cualquiera = np.minimum(cualquiera, minimo)
        companero = np.where(eq == k, minimo, companero)
    bx, by = np.asarray(trk.bx, dtype=np.float64)[t], np.asarray(trk.by, dtype=np.float64)[t]
    al_balon = np.hypot(x - bx, y - by)
    edad = _edad_rapida(presente, columnas, t, col, eq) / fps
    r["muestras"] = int(len(t))
    r["sitio"] = np.bincount(sitio, minlength=len(LINEA_M) + 1).tolist()
    r["velocidad"] = np.bincount(caja(velocidad[np.isfinite(velocidad)], VELOCIDADES),
                                 minlength=len(VELOCIDADES) + 1).tolist() + [int(np.sum(~np.isfinite(velocidad)))]
    r["companero"] = np.bincount(caja(companero, COMPANERO_M), minlength=len(COMPANERO_M) + 1).tolist()
    r["cualquiera"] = np.bincount(caja(cualquiera, LEJOS_M), minlength=len(LEJOS_M) + 1).tolist()
    con_balon = np.isfinite(al_balon)
    r["balon"] = np.bincount(caja(al_balon[con_balon], BALON_M), minlength=len(BALON_M) + 1).tolist() + [
        int(np.sum(~con_balon))]
    r["edad"] = np.bincount(caja(edad, DURACIONES_S), minlength=len(DURACIONES_S) + 1).tolist()
    r["fuera_1m"] = int(np.sum(margen > 1.0))
    r["pareja_05"] = int(np.sum(companero < PAREJA_M))

    # comprobación sin elegir quién sobra: frames con sobrantes frente a frames con 9 a 11 del mismo equipo
    comp = {"sobra": [0, 0, 0], "normal": [0, 0, 0]}  # [frames, con algún slot a > 1 m fuera, con pareja a < 0,5 m]
    for k in (0, 1):
        for nombre, m in (("sobra", sobra[k]), ("normal", evaluado & (cuenta[k] >= 9) & (cuenta[k] <= JUGADORES))):
            idx = np.flatnonzero(m)
            comp[nombre][0] += len(idx)
            for a in range(0, len(idx), BLOQUE):
                f = idx[a:a + BLOQUE]
                cx, cy = px[f][:, columnas[k]], py[f][:, columnas[k]]
                with np.errstate(invalid="ignore"):
                    fuera = np.maximum.reduce([-cx, cx - largo, -cy, cy - ancho]) > FUERA_COMPROBACION_M
                comp[nombre][1] += int(np.sum(np.any(fuera, axis=1)))
                d2 = (cx[:, :, None] - cx[:, None, :]) ** 2 + (cy[:, :, None] - cy[:, None, :]) ** 2
                d2 = np.where(np.isfinite(d2), d2, np.inf)
                d2[:, np.arange(cx.shape[1]), np.arange(cx.shape[1])] = np.inf
                comp[nombre][2] += int(np.sum(d2.min(axis=(1, 2)) < PAREJA_M ** 2)) if cx.shape[1] > 1 else 0
    r["comprobacion"] = comp
    r["d_con_sobrantes"] = int(np.sum(alguno & (etiquetas == D)))
    r["d_evaluados"] = int(np.sum(evaluado & (etiquetas == D)))
    return r


def _edad_rapida(presente, columnas, t, col, eq):
    salida = np.zeros(len(t))
    for k in (0, 1):
        m = eq == k
        if not m.any():
            continue
        e = edades(presente[k])
        pos = np.searchsorted(columnas[k], col[m])
        salida[m] = e[t[m], pos]
    return salida


def arreglo(r):
    """(arreglo que toca, por qué), con la regla de la bitácora P3: el primero que se cumpla."""
    n = r["muestras"]
    if not n:
        return None, "no hay frames con sobrantes"
    fuera, pareja = r["fuera_1m"] / float(n), r["pareja_05"] / float(n)
    if fuera >= UMBRAL:
        return ARREGLOS[0], "el sobrante está a más de 1 m fuera en el {:.0f} %".format(100 * fuera)
    if pareja >= UMBRAL:
        return ARREGLOS[1], "el sobrante está a menos de 0,5 m de un compañero en el {:.0f} %".format(100 * pareja)
    return ARREGLOS[2], "fuera {:.0f} % y pareja {:.0f} %, los dos por debajo del 50 %".format(100 * fuera, 100 * pareja)


def para_imprimir(r, sha=None, minimo=MINIMO_CELDA):
    def celda(k):
        return fst.celda(int(k), minimo)

    def pct(a, b):
        return fst.pct(int(a), int(b), minimo)

    def bloque(titulo, nombres, valores, total):
        lineas = ["   " + titulo]
        for nombre, v in zip(nombres, valores):
            lineas.append("      {:<34} {:>7} ({})".format(nombre, celda(v), pct(v, total)))
        return lineas

    n = r["muestras"]
    eleccion, porque = arreglo(r)
    lineas = [
        "Slots sobrantes: un equipo con más de 11 slots a la vez (validation/investigacion_1116/BITACORA.md, P3)",
        "",
        "0. Controles",
        "   entrega: sha256 {}".format("—" if sha is None else "{}…{}".format(sha[:8], sha[-5:])),
        "   frames evaluados: {}   con sobrantes: {} ({})".format(r["evaluados"], celda(r["con_sobrantes"]),
                                                                pct(r["con_sobrantes"], r["evaluados"])),
        "",
        "1. Cuántos y cuánto duran",
        "   solo el local {}   solo el visitante {}   los dos {}".format(*[celda(v) for v in r["por_equipo"]]),
        "   el equipo tiene 12 slots {}   13 {}   14 o más {}".format(*[celda(v) for v in r["slots"]]),
        "   rachas seguidas con sobrantes (rachas / frames): " + "   ".join(
            "{} {} / {}".format(nombre, celda(a), celda(b)) for nombre, a, b in zip(
                ("< 1 s", "1–5 s", "5–30 s", "≥ 30 s"), r["rachas"], r["rachas_frames"])),
        "",
        "2. El sobrante (el slot más nuevo del equipo que pasa de 11), en {} muestras (frame × equipo)".format(celda(n)),
    ]
    lineas += bloque("dónde está respecto a las líneas", [nombre for _, nombre in LINEA_M] + ["más adentro"],
                     r["sitio"], n)
    lineas += bloque("velocidad en 2 s", ["menos de 0,5 m/s", "de 0,5 a 2 m/s", "más de 2 m/s", "sin dato"],
                     r["velocidad"], n)
    lineas += bloque("compañero más cercano", ["a menos de 0,5 m", "de 0,5 a 1 m", "de 1 a 3 m", "a más de 3 m"],
                     r["companero"], n)
    lineas += bloque("jugador más cercano, de cualquier equipo", ["a menos de 3 m", "de 3 a 15 m",
                                                                  "a más de 15 m (lejos de todos)"], r["cualquiera"], n)
    lineas += bloque("distancia al balón", ["a menos de 3 m", "de 3 a 10 m", "de 10 a 30 m", "a más de 30 m",
                                           "sin balón"], r["balon"], n)
    lineas += bloque("cuánto lleva visto", ["menos de 1 s", "de 1 a 5 s", "de 5 a 30 s", "30 s o más"], r["edad"], n)
    c = r["comprobacion"]
    lineas += [
        "",
        "3. Comprobación sin elegir quién sobra (frames × equipo)",
        "   con sobrantes: {} frames; algún slot a más de 1 m fuera {}; pareja a menos de 0,5 m {}".format(
            celda(c["sobra"][0]), pct(c["sobra"][1], c["sobra"][0]), pct(c["sobra"][2], c["sobra"][0])),
        "   con 9 a 11 slots: {} frames; algún slot a más de 1 m fuera {}; pareja a menos de 0,5 m {}".format(
            celda(c["normal"][0]), pct(c["normal"][1], c["normal"][0]), pct(c["normal"][2], c["normal"][0])),
        "",
        "4. El balón muerto: la entrega dice D en {} de los frames con sobrantes, y en {} de todos los evaluados".format(
            pct(r["d_con_sobrantes"], r["con_sobrantes"]), pct(r["d_evaluados"], r["evaluados"])),
        "",
        "5. Regla (BITACORA.md P3): qué arreglo se escribe",
        "   → {}: {}".format(eleccion.upper() if eleccion else "NINGUNO", porque),
    ]
    return lineas


def medir(entrega, data_dir=None):
    """La descripción sobre el partido. Lee el ATD y una entrega: solo lo ejecuta una persona."""
    game = games.GAME
    games.require(FICHEROS, game, data_dir)
    trk = tracking.from_atd(games.asset_paths(game, data_dir), game)
    etiquetas, sha = fst.leer_entrega(entrega, len(trk.bx))
    return describir(trk, etiquetas), sha


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entrega", required=True, help="CSV frame,label de la entrega vigente (equipo_v8)")
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    inicio = time.time()
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD del partido: revisa que MTAH_DATA_DIR (o --data-dir) apunte a la carpeta de los datos.")
        return 1
    if not os.path.isfile(args.entrega):
        print("No encuentro la entrega: pasa la ruta completa del CSV con --entrega.")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
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
