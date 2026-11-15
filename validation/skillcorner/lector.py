"""Los partidos abiertos de SkillCorner en el formato del pipeline, con sus etiquetas.

Datos abiertos de otros partidos (A-League 2024/25, licencia MIT; ver `descargar.py`). Lo puede ejecutar
cualquiera, Claude incluido. Las reglas que aplica están fijadas en `BITACORA.md` §3 y §4, antes de medir:

- etiquetas: `D` fuera de las fases de juego; dentro, el `possession.group` del frame, rellenado con el
  último conocido del mismo tramo de juego (al principio del tramo, con el siguiente). Un tramo sin ningún
  `group` queda en `X`;
- de 10 a 25 fps: posiciones interpoladas entre las dos muestras que rodean cada instante (solo si existen
  las dos) y etiquetas en escalón (la muestra anterior);
- metros con el origen en una esquina, un slot por `player_id`, barajados a trozos como en el harness;
- las dos partes, con un hueco de `X` en medio.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for _carpeta in (ROOT, AQUI.parent / "harness", AQUI.parent / "scripts"):
    sys.path.insert(0, str(_carpeta))
import descargar_datos_abiertos as dda  # noqa: E402
import dfl  # noqa: E402
from possession import tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
FPS_ORIGEN = 10
FPS = 25
HUECO = dfl.HUECO
SEMILLA = 20261115
GRUPOS = {"home team": H, "away team": A}
CONDICIONES = ("detectado", "detectado, suavizado", "con el estimado", "solo jugadores detectados")
VOTAN = ("detectado", "detectado, suavizado")
# condición -> (balón: «detectado» o «todo», suavizado en frames, jugadores: «todos» o «detectados»)
PARAMETROS = {
    "detectado": ("detectado", 1, "todos"),
    "detectado, suavizado": ("detectado", dfl.SUAVIZADO, "todos"),
    "con el estimado": ("todo", 1, "todos"),
    "solo jugadores detectados": ("detectado", 1, "detectados"),
}


def carpeta():
    return dda.destino_por_defecto() / "skillcorner"


# BITACORA §8. La medida del 15/11 usó los 20, antes de este corte. Entrenar o mirar errores
# solo con ENTRENAMIENTO. EXAMEN no se lee en ningún script nuevo.
ENTRENAMIENTO = (1874553, 1899585, 1927964, 1959846, 1996435, 2006229, 2007448, 2010085, 2013725, 2016236)
EXAMEN = (1886347, 1925299, 1953632, 1986691, 1996436, 2006363, 2007721, 2011166, 2015213, 2017461)


def partidos():
    """Ids de los partidos bajados, en orden. Incluye el examen: lo usa la medida ya hecha, no un entrenamiento."""
    raiz = carpeta()
    if not raiz.is_dir():
        return []
    return sorted(int(p.name) for p in raiz.iterdir() if p.is_dir() and p.name.isdigit()
                  and (p / "{}_tracking_extrapolated.jsonl".format(p.name)).is_file())


def exigir_solo_entrenamiento(ids):
    """Corta si algún id es del examen. Hay que llamarla antes de entrenar o de mirar errores."""
    colados = sorted(set(ids) & set(EXAMEN))
    if colados:
        raise ValueError("estos partidos son el examen y no se tocan: {}".format(colados))


# -- lectura a 10 fps, con caché ----------------------------------------------------------------------

def leer_crudo(id_, raiz=None):
    """Arrays a 10 fps de un partido, desde el JSONL (lento) o desde su caché .npz."""
    raiz = Path(raiz) if raiz is not None else carpeta()
    cache = raiz.parent / "skillcorner_cache" / "{}.npz".format(id_)
    if cache.is_file():
        with np.load(cache, allow_pickle=False) as z:
            return {k: z[k] for k in z.files}
    datos = parsear(raiz / str(id_), id_)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **datos)
    return datos


def parsear(carpeta_partido, id_):
    """Lee match.json y el JSONL de tracking. Coordenadas tal cual vienen (metros, origen en el centro)."""
    carpeta_partido = Path(carpeta_partido)
    with open(carpeta_partido / "{}_match.json".format(id_), encoding="utf-8") as f:
        meta = json.load(f)
    local = meta["home_team"]["id"]
    equipo_de = {p["id"]: (H if p["team_id"] == local else A) for p in meta["players"]}
    with open(carpeta_partido / "{}_tracking_extrapolated.jsonl".format(id_), encoding="utf-8") as f:
        filas = [json.loads(linea) for linea in f if linea.strip()]
    filas.sort(key=lambda r: r["frame"])
    n = filas[-1]["frame"] + 1
    slots = sorted({p["player_id"] for r in filas for p in (r.get("player_data") or []) if p["player_id"] in equipo_de})
    columna = {pid: k for k, pid in enumerate(slots)}
    bx, by = np.full(n, np.nan), np.full(n, np.nan)
    bdet = np.zeros(n, bool)
    px = np.full((n, len(slots)), np.nan, dtype=np.float32)
    py = np.full((n, len(slots)), np.nan, dtype=np.float32)
    pdet = np.zeros((n, len(slots)), bool)
    grupo = np.full(n, -1, dtype=np.int8)
    for r in filas:
        t = r["frame"]
        b = r.get("ball_data") or {}
        if b.get("x") is not None and b.get("y") is not None:
            bx[t], by[t] = b["x"], b["y"]
            bdet[t] = bool(b.get("is_detected"))
        for p in r.get("player_data") or []:
            k = columna.get(p["player_id"])
            if k is None or p.get("x") is None or p.get("y") is None:
                continue
            px[t, k], py[t, k] = p["x"], p["y"]
            pdet[t, k] = bool(p.get("is_detected"))
        grupo[t] = GRUPOS.get((r.get("possession") or {}).get("group"), -1)
    fases = np.zeros(n, bool)
    tabla = pd.read_csv(carpeta_partido / "{}_phases_of_play.csv".format(id_))
    for a, b in zip(tabla["frame_start"].astype(int), tabla["frame_end"].astype(int)):
        fases[max(a, 0):min(b + 1, n)] = True
    partes = np.array([(int(p["start_frame"]), int(p["end_frame"])) for p in meta["match_periods"]], dtype=np.int64)
    return {"bx": bx, "by": by, "bdet": bdet, "px": px, "py": py, "pdet": pdet, "grupo": grupo, "fases": fases,
            "team": np.array([equipo_de[pid] for pid in slots], dtype=np.int8), "partes": partes,
            "campo": np.array([float(meta["pitch_length"]), float(meta["pitch_width"])])}


# -- etiquetas -----------------------------------------------------------------------------------------

def tramos(mascara):
    """(inicios, fines) de las rachas de True, con el fin sin incluir."""
    bordes = np.diff(np.concatenate(([0], np.asarray(mascara, dtype=np.int8), [0])))
    return np.flatnonzero(bordes == 1), np.flatnonzero(bordes == -1)


def etiquetas(fases, grupo):
    """Códigos H/A/D/X a 10 fps (BITACORA §3)."""
    out = np.full(len(fases), D, dtype=np.int8)
    for a, b in zip(*tramos(fases)):
        g = grupo[a:b]
        conocidos = np.flatnonzero(g >= 0)
        if len(conocidos) == 0:
            out[a:b] = X
            continue
        ultimo = np.maximum.accumulate(np.where(g >= 0, np.arange(b - a), -1))
        ultimo[ultimo < 0] = conocidos[0]
        out[a:b] = g[ultimo]
    return out


# -- de 10 a 25 fps --------------------------------------------------------------------------------------

def instantes(n10):
    """Para cada frame a 25 fps, (muestra anterior a 10 fps, peso de la siguiente)."""
    n25 = (n10 - 1) * FPS // FPS_ORIGEN + 1
    t = np.arange(n25) * (FPS_ORIGEN / FPS)
    i0 = np.minimum(np.floor(t + 1e-9).astype(np.int64), n10 - 1)
    return i0, t - i0


def interpolar(valores, i0, w):
    """Interpolación lineal; NaN si falta alguna de las dos muestras que hacen falta."""
    v = np.asarray(valores, dtype=np.float64)
    i1 = np.minimum(i0 + 1, len(v) - 1)
    peso = w.reshape((-1,) + (1,) * (v.ndim - 1))
    out = (1.0 - peso) * v[i0] + peso * v[i1]
    exacto = (w < 1e-9).reshape(peso.shape)
    return np.where(exacto, v[i0], out)


def escalon(valores, i0):
    return np.asarray(valores)[i0]


# -- el partido como `Tracking` ---------------------------------------------------------------------------

def tracking_de(crudo, condicion, id_=0):
    """(Tracking a 25 fps de las dos partes, etiquetas alineadas con él) en la condición dada."""
    if condicion not in PARAMETROS:
        raise ValueError("condición desconocida: {}".format(condicion))
    balon, suavizado, jugadores = PARAMETROS[condicion]
    largo, ancho = (float(v) for v in crudo["campo"])
    lab10 = etiquetas(crudo["fases"], crudo["grupo"])
    piezas = {"bx": [], "by": [], "px": [], "py": [], "gt": []}
    blocks, inicio = [], 0
    for k, (a, b) in enumerate(crudo["partes"]):
        sl = slice(int(a), int(b) + 1)
        bx, by = crudo["bx"][sl].copy(), crudo["by"][sl].copy()
        if balon == "detectado":
            bx[~crudo["bdet"][sl]] = np.nan
            by[~crudo["bdet"][sl]] = np.nan
        px, py = crudo["px"][sl].astype(np.float64), crudo["py"][sl].astype(np.float64)
        if jugadores == "detectados":
            px[~crudo["pdet"][sl]] = np.nan
            py[~crudo["pdet"][sl]] = np.nan
        i0, w = instantes(len(bx))
        bx25, by25 = interpolar(bx, i0, w) + largo / 2, interpolar(by, i0, w) + ancho / 2
        if suavizado > 1:
            hay = ~np.isnan(bx25)
            bx25, by25 = dfl.media_movil(bx25, suavizado), dfl.media_movil(by25, suavizado)
            bx25[~hay], by25[~hay] = np.nan, np.nan
        if k:
            for clave, relleno in (("bx", np.nan), ("by", np.nan), ("gt", X)):
                piezas[clave].append(np.full(HUECO, relleno))
            for clave in ("px", "py"):
                piezas[clave].append(np.full((HUECO, px.shape[1]), np.nan))
            inicio += HUECO
        piezas["bx"].append(bx25)
        piezas["by"].append(by25)
        piezas["px"].append(interpolar(px, i0, w) + largo / 2)
        piezas["py"].append(interpolar(py, i0, w) + ancho / 2)
        piezas["gt"].append(escalon(lab10[sl], i0))
        blocks.append((inicio, inicio + len(i0)))
        inicio += len(i0)
    gt = np.concatenate(piezas["gt"]).astype(np.int8)
    px = np.concatenate(piezas["px"]).astype(np.float32)
    py = np.concatenate(piezas["py"]).astype(np.float32)
    rng = np.random.default_rng([SEMILLA, int(id_), 99])
    px, py, team = dfl.barajar_slots(px, py, crudo["team"].copy(), rng)
    trk = tracking.Tracking(np.concatenate(piezas["bx"]), np.concatenate(piezas["by"]), px, py, team,
                            (largo, ancho), tuple(blocks), FPS)
    return trk, gt
