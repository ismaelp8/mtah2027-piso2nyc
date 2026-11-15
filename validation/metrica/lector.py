"""Los 3 partidos abiertos de Metrica en el formato del pipeline, con etiquetas derivadas de sus eventos.

Datos abiertos de otros partidos (sample-data de Metrica; hay que citar la fuente). Lo puede ejecutar
cualquiera, Claude incluido. Las reglas están fijadas en `BITACORA.md` §3 y §4, antes de medir:

- el juego se para en `BALL OUT`, `FAULT RECEIVED`, un `SHOT` con `GOAL` en el subtipo, o un `BALL LOST`
  de `END HALF` u `OFFSIDE`, y se reanuda en el `SET PIECE` siguiente;
- el equipo es el del último `SET PIECE`, `PASS`, `RECOVERY`, `SHOT` o `CARRY` de esa parte;
- metros con el origen en una esquina, sin invertir `y`; un slot por jugador, barajado a trozos.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for _carpeta in (ROOT, AQUI.parent / "harness", AQUI.parent / "scripts"):
    sys.path.insert(0, str(_carpeta))
import descargar_datos_abiertos as dda  # noqa: E402
import dfl  # noqa: E402
from possession import io, tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
FPS = 25
PITCH = (105.0, 68.0)
HUECO = dfl.HUECO
SEMILLA = 20261115
CONDICIONES = ("tal cual", "suavizado 25")
VOTAN = ("tal cual",)
PARAMETROS = {"tal cual": 1, "suavizado 25": dfl.SUAVIZADO}
CONTROLES = {"SET PIECE", "PASS", "RECOVERY", "SHOT", "CARRY"}
# Prioridad dentro de un mismo frame: el saque manda sobre el evento que lo precede.
PRIORIDAD = {"SET PIECE": 2}


def carpeta():
    return dda.destino_por_defecto() / "metrica"


def partidos():
    """Ids de los partidos que están bajados, en orden."""
    raiz = carpeta() / "data"
    ids = []
    for i in (1, 2, 3):
        base = raiz / "Sample_Game_{}".format(i)
        if i < 3 and (base / "Sample_Game_{}_RawEventsData.csv".format(i)).is_file():
            ids.append(i)
        elif i == 3 and (base / "Sample_Game_3_tracking.txt").is_file():
            ids.append(i)
    return ids


def leer(id_, raiz=None):
    """Arrays de un partido, desde el fichero (lento) o desde su caché .npz."""
    raiz = Path(raiz) if raiz is not None else carpeta()
    cache = raiz.parent / "metrica_cache" / "{}.npz".format(id_)
    if cache.is_file():
        with np.load(cache, allow_pickle=False) as z:
            return {k: z[k] for k in z.files}
    datos = parsear(raiz, id_)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **datos)
    return datos


# -- etiquetas -----------------------------------------------------------------------------------------

def _es_parada(tipo, subtipo):
    sub = (subtipo or "").strip().upper()
    if tipo in ("BALL OUT", "FAULT RECEIVED"):
        return True
    if tipo == "SHOT" and "GOAL" in sub:
        return True
    return tipo == "BALL LOST" and sub in ("END HALF", "OFFSIDE")


def etiquetar(n, eventos):
    """Códigos H/A/D/X de una parte (BITACORA §3).

    `eventos` es una lista de (frame, tipo, subtipo, equipo), con el frame dentro de [0, n) y el equipo
    `H` o `A`. El orden de la lista no importa.
    """
    n = int(n)
    gt = np.full(n, D, dtype=np.int8)
    control = np.full(n, -1, dtype=np.int8)
    saques, paradas = [], []
    for frame, tipo, subtipo, equipo in sorted(eventos, key=lambda e: (e[0], PRIORIDAD.get(e[1], 1))):
        if not 0 <= int(frame) < n:
            continue
        frame = int(frame)
        if tipo == "SET PIECE":
            saques.append(frame)
        if _es_parada(tipo, subtipo):
            paradas.append(frame)
        if tipo in CONTROLES and equipo in (H, A):
            control[frame] = equipo
    paradas = np.array(sorted(set(paradas)), dtype=np.int64)
    for s in sorted(set(saques)):
        posteriores = paradas[paradas > s]
        fin = int(posteriores[0]) if len(posteriores) else n
        gt[s:fin] = H
    ultimo = -1
    for i in range(n):
        if control[i] >= 0:
            ultimo = int(control[i])
        if gt[i] != D:
            gt[i] = ultimo if ultimo >= 0 else X
    return gt


# -- juegos 1 y 2 (CSV) --------------------------------------------------------------------------------

def _csv(path):
    tabla = pd.read_csv(path, header=None, skiprows=3)
    if tabla.shape[1] < 5 or (tabla.shape[1] - 3) % 2:
        raise ValueError("el CSV de tracking no trae pares x, y: {}".format(Path(path).name))
    return tabla


def _pares(tabla):
    """(frames, periodo, xy de jugadores, xy del balón). El último par de columnas es el balón."""
    valores = tabla.to_numpy(dtype=float)
    frames = valores[:, 1].astype(np.int64)
    periodo = valores[:, 0].astype(np.int64)
    xy = valores[:, 3:]
    return frames, periodo, xy[:, :-2], xy[:, -2:]


def _eventos_csv(path, indice, parte):
    """Eventos de una parte, con el frame ya pasado al índice local (`indice`: frame del fichero -> índice)."""
    equipos = {"Home": H, "Away": A}
    out = []
    with open(path, encoding="utf-8") as handle:
        for fila in pd.read_csv(handle).itertuples(index=False):
            if int(fila[3]) != parte:
                continue
            frame = indice.get(int(fila[4]))
            if frame is None:
                continue
            out.append((frame, str(fila[1]), "" if pd.isna(fila[2]) else str(fila[2]), equipos[str(fila[0])]))
    return out


def _parsear_csv(raiz, id_):
    base = raiz / "data" / "Sample_Game_{}".format(id_)
    frames_h, periodo, jug_h, balon = _pares(_csv(base / "Sample_Game_{}_RawTrackingData_Home_Team.csv".format(id_)))
    frames_a, _, jug_a, _ = _pares(_csv(base / "Sample_Game_{}_RawTrackingData_Away_Team.csv".format(id_)))
    if len(frames_h) != len(frames_a) or not np.array_equal(frames_h, frames_a):
        raise ValueError("los dos CSV de tracking del juego {} no traen los mismos frames".format(id_))
    eventos_path = base / "Sample_Game_{}_RawEventsData.csv".format(id_)
    partes = []
    for parte in (1, 2):
        filas = np.flatnonzero(periodo == parte)
        if len(filas) == 0:
            raise ValueError("el juego {} no tiene la parte {}".format(id_, parte))
        indice = {int(frames_h[i]): k for k, i in enumerate(filas)}
        partes.append({
            "bx": balon[filas, 0] * PITCH[0], "by": balon[filas, 1] * PITCH[1],
            "px": np.concatenate([jug_h[filas, 0::2], jug_a[filas, 0::2]], axis=1) * PITCH[0],
            "py": np.concatenate([jug_h[filas, 1::2], jug_a[filas, 1::2]], axis=1) * PITCH[1],
            "gt": etiquetar(len(filas), _eventos_csv(eventos_path, indice, parte)),
            "n_local": jug_h.shape[1] // 2,
        })
    return _empaquetar(partes)


# -- juego 3 (EPTS, el formato del ATD) -----------------------------------------------------------------

def _limites_juego3(meta, raw):
    """(frame inicial, frame final) de cada parte, con los dos incluidos. El frame del fichero empieza en 1."""
    from kloppy import metrica

    dataset = metrica.load_tracking_epts(meta, raw, limit=1, coordinates="metrica")
    limites = []
    for parte in dataset.metadata.periods:
        inicio = int(round(parte.start_timestamp.total_seconds() * FPS))
        fin = int(round(parte.end_timestamp.total_seconds() * FPS))
        limites.append((inicio, fin))
    if limites != [(1, limites[0][1]), (limites[0][1] + 1, limites[1][1])]:
        raise ValueError("las dos partes del juego 3 no son contiguas: {}".format(limites))
    return limites, dataset


def _equipo_juego3(dataset, px0):
    """Equipo de cada slot, en el orden del fichero. Se comprueba contra el primer frame."""
    frame = dataset.frames[0]
    xs, equipo = [], []
    for jugador, datos in frame.players_data.items():
        if datos.coordinates is None:
            continue
        xs.append(datos.coordinates.x * PITCH[0])
        equipo.append(H if jugador.team.ground.name == "HOME" else A)
    if not np.allclose(px0, xs, equal_nan=True, atol=1e-3):
        raise ValueError("el orden de los slots del juego 3 no coincide con kloppy")
    return np.array(equipo, dtype=np.int8)


def _eventos_json(path, equipos):
    with open(path, encoding="utf-8") as handle:
        filas = json.load(handle)["data"]
    out = []
    for fila in filas:
        tipo = fila["type"]["name"] if isinstance(fila["type"], dict) else str(fila["type"])
        sub = fila.get("subtypes")
        if isinstance(sub, dict):
            sub = sub.get("name") or ""
        elif isinstance(sub, list):
            sub = " ".join((x.get("name") or "") if isinstance(x, dict) else str(x) for x in sub)
        elif sub is None:
            sub = ""
        out.append((int(fila["period"]), int(fila["start"]["frame"]), tipo, str(sub), equipos[fila["team"]["id"]]))
    return out


def _parsear_juego3(raiz):
    base = raiz / "data" / "Sample_Game_3"
    raw = base / "Sample_Game_3_tracking.txt"
    meta = base / "Sample_Game_3_metadata.xml"
    n = sum(1 for _ in open(raw, encoding="utf-8"))
    bx, by, _ = io.load_ball(raw, n, PITCH)
    px, py = io.load_players(raw, n, PITCH)
    limites, dataset = _limites_juego3(meta, raw)
    if limites[-1][1] != n:
        raise ValueError("el juego 3 declara {} frames y el tracking tiene {}".format(limites[-1][1], n))
    equipo = _equipo_juego3(dataset, px[0])
    local = ET.parse(meta).getroot()
    ids = [t.get("id") for t in local.iter("Team")]
    eventos = _eventos_json(base / "Sample_Game_3_events.json", {ids[0]: H, ids[1]: A})
    partes = []
    for k, (a, b) in enumerate(limites, start=1):
        sl = slice(a - 1, b)
        de_parte = [(frame - a, tipo, sub, eq) for parte, frame, tipo, sub, eq in eventos if parte == k]
        partes.append({"bx": bx[sl], "by": by[sl], "px": px[sl], "py": py[sl],
                       "gt": etiquetar(b - a + 1, de_parte), "n_local": int(np.sum(equipo == H))})
    return _empaquetar(partes, equipo)


def _empaquetar(partes, equipo=None):
    if equipo is None:
        n_local = partes[0]["n_local"]
        n_slots = partes[0]["px"].shape[1]
        equipo = np.array([H] * n_local + [A] * (n_slots - n_local), dtype=np.int8)
    return {
        "bx": [p["bx"].astype(np.float64) for p in partes],
        "by": [p["by"].astype(np.float64) for p in partes],
        "px": [p["px"].astype(np.float32) for p in partes],
        "py": [p["py"].astype(np.float32) for p in partes],
        "gt": [p["gt"].astype(np.int8) for p in partes],
        "team": equipo.astype(np.int8),
        "pitch": np.array(PITCH, dtype=np.float64),
    }


def parsear(raiz, id_):
    raiz = Path(raiz)
    if id_ == 3:
        datos = _parsear_juego3(raiz)
    elif id_ in (1, 2):
        datos = _parsear_csv(raiz, id_)
    else:
        raise ValueError("partido desconocido: {}".format(id_))
    # np.savez quiere arrays, no listas: se guardan las dos partes una detrás de otra, con sus longitudes.
    largos = np.array([len(datos["bx"][0]), len(datos["bx"][1])], dtype=np.int64)
    return {
        "bx": np.concatenate(datos["bx"]), "by": np.concatenate(datos["by"]),
        "px": np.concatenate(datos["px"]), "py": np.concatenate(datos["py"]),
        "gt": np.concatenate(datos["gt"]), "team": datos["team"], "pitch": datos["pitch"], "largos": largos,
    }


# -- el partido como `Tracking` -------------------------------------------------------------------------

def _suavizar(bx, by, ancho):
    if ancho <= 1:
        return bx, by
    hay = ~np.isnan(bx)
    bx, by = dfl.media_movil(bx, ancho), dfl.media_movil(by, ancho)
    bx[~hay], by[~hay] = np.nan, np.nan
    return bx, by


def tracking_de(crudo, condicion, id_=0):
    """(Tracking de las dos partes, etiquetas alineadas) en la condición dada."""
    if condicion not in PARAMETROS:
        raise ValueError("condición desconocida: {}".format(condicion))
    ancho = PARAMETROS[condicion]
    largo, ancho_campo = (float(v) for v in crudo["pitch"])
    cortes = np.cumsum(crudo["largos"])
    trozos = {"bx": [], "by": [], "px": [], "py": [], "gt": []}
    blocks, inicio = [], 0
    anterior = 0
    for k, fin in enumerate(cortes):
        sl = slice(int(anterior), int(fin))
        bx, by = _suavizar(crudo["bx"][sl].copy(), crudo["by"][sl].copy(), ancho)
        if k:
            trozos["bx"].append(np.full(HUECO, np.nan))
            trozos["by"].append(np.full(HUECO, np.nan))
            trozos["px"].append(np.full((HUECO, crudo["px"].shape[1]), np.nan, dtype=np.float32))
            trozos["py"].append(np.full((HUECO, crudo["py"].shape[1]), np.nan, dtype=np.float32))
            trozos["gt"].append(np.full(HUECO, X, dtype=np.int8))
            inicio += HUECO
        trozos["bx"].append(bx)
        trozos["by"].append(by)
        trozos["px"].append(crudo["px"][sl])
        trozos["py"].append(crudo["py"][sl])
        trozos["gt"].append(crudo["gt"][sl])
        blocks.append((inicio, inicio + (int(fin) - int(anterior))))
        inicio += int(fin) - int(anterior)
        anterior = fin
    px = np.concatenate(trozos["px"]).astype(np.float32)
    py = np.concatenate(trozos["py"]).astype(np.float32)
    rng = np.random.default_rng([SEMILLA, int(id_), 99])
    px, py, team = dfl.barajar_slots(px, py, crudo["team"].copy(), rng)
    trk = tracking.Tracking(np.concatenate(trozos["bx"]), np.concatenate(trozos["by"]), px, py, team,
                            (largo, ancho_campo), tuple(blocks), FPS)
    return trk, np.concatenate(trozos["gt"]).astype(np.int8)
