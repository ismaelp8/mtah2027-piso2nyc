"""Evidencia de equipo (`H` o `A`) por frame, con el balón visible.

Tres versiones, escritas antes de medir (docs/decisiones.md, 14/11). Las tres dan NEAREST_SCORE a favor de
un equipo en los frames en que opinan y 0 («no opino») en el resto:

- N1 (docs/investigacion_metodos.md §2.3): el equipo del slot más cercano al balón. Es lo que hace
  starter/baseline.py y es la referencia: cualquier candidato tiene que superarlo en el harness.
- N2, más cercano con radio y margen: opina solo si el más cercano está a RADIUS o menos y el más cercano
  del otro equipo está al menos MARGIN más lejos.
- Ret, control por retención: opina en los frames de una racha de MIN_FRAMES seguidos o más en la que el
  más cercano es siempre del mismo equipo y está a RADIUS o menos. Va por equipo y no por slot, porque un
  slot no es un jugador. Es la traducción de «un toque sin control no cambia la posesión».

`METHOD` es la que usa el pipeline. Solo cambia cuando un candidato gane en el harness de la DFL al control y
a la versión de main (docs/PLAN_ENTREGA.md §4).

Interfaz: `evidence(trk)` devuelve `(score, allowed)`; ver possession/tracking.py.
"""

import numpy as np

from possession.tracking import A, H, no_evidence

N1, N2, RET = "N1", "N2", "Ret"
METHODS = (N1, N2, RET)
METHOD = N1

# Puntuación a favor del equipo cuando una versión opina. Sin ajustar: es la unidad en la que se miden los
# costes del decodificador, y se fija en la DFL, no en el partido.
NEAREST_SCORE = 1.0
# Sin ajustar; ninguno sale del partido ni de la ventana pública (docs/decisiones.md, 14/11):
RADIUS = 1.5  # m, N2 y Ret: el radio de control «ampliado» del experimento 2
MARGIN = 1.0  # m, N2: el margen sobre el rival que mide el perfil del ATD (fila 5)
MIN_FRAMES = 12  # frames, Ret: Ret-12, la retención que mide el perfil del ATD (fila 4a)
# Frames por bloque al calcular distancias, para no reservar una matriz de todo el partido de una vez.
CHUNK = 20000
NOBODY = -1


def proximity(trk, frames=None):
    """Quién está cerca del balón en cada frame de `frames` (todos, si es None).

    Devuelve `(team, dist)`:
    - `team`: equipo del slot más cercano, 0 o 1, o -1 si no hay balón o no hay jugadores. Con dos slots a
      la misma distancia gana el de índice más bajo, como en el baseline;
    - `dist`: forma (k, 2), la distancia en metros del balón al slot más cercano de cada equipo (columna 0
      `H`, columna 1 `A`), o infinito si no hay balón o ese equipo no tiene slots en el frame.

    La usa también possession/ball.py (la protección del relleno de huecos): si cambia, cambia la limpieza.
    """
    frames = np.arange(len(trk.bx)) if frames is None else np.asarray(frames, dtype=np.int64)
    team = np.full(len(frames), NOBODY, dtype=np.int8)
    dist = np.full((len(frames), 2), np.inf)
    slot_team = np.asarray(trk.team)
    columns = [np.flatnonzero(slot_team == k) for k in (H, A)]
    seen = np.flatnonzero(~np.isnan(trk.bx[frames]) & ~np.isnan(trk.by[frames]))
    for start in range(0, len(seen), CHUNK):
        pos = seen[start:start + CHUNK]
        idx = frames[pos]
        dx = trk.px[idx].astype(np.float64) - trk.bx[idx, None]
        dy = trk.py[idx].astype(np.float64) - trk.by[idx, None]
        d2 = dx * dx + dy * dy
        d2 = np.where(np.isnan(d2), np.inf, d2)
        best = np.argmin(d2, axis=1)
        found = np.isfinite(d2[np.arange(len(idx)), best])
        team[pos[found]] = slot_team[best[found]]
        for k, cols in zip((H, A), columns):
            if len(cols):
                dist[pos, k] = np.sqrt(d2[:, cols].min(axis=1))
    return team, dist


def nearest_team(trk):
    """Equipo del slot más cercano al balón por frame: 0, 1, o -1 si no hay balón o no hay jugadores.

    Con dos slots a la misma distancia gana el de índice más bajo, como en el baseline.
    """
    return proximity(trk)[0]


def margin_team(trk, radius=RADIUS, margin=MARGIN):
    """N2: el equipo del más cercano si está a `radius` o menos y el rival, `margin` más lejos; si no, -1."""
    _, dist = proximity(trk)
    own = np.argmin(dist, axis=1)  # con la misma distancia, el margen es 0 y no opina
    near = dist[np.arange(len(dist)), own]
    far = dist[np.arange(len(dist)), 1 - own]
    with np.errstate(invalid="ignore"):  # inf − inf, cuando no hay balón: no opina
        opina = (near <= radius) & (far - near >= margin)
    return np.where(opina, own, NOBODY).astype(np.int8)


def retention_team(trk, radius=RADIUS, min_frames=MIN_FRAMES):
    """Ret: el equipo en los frames de rachas de `min_frames` o más con el más cercano a `radius` o menos.

    La racha es del equipo, no del slot: se corta cuando el más cercano pasa a ser del otro equipo, cuando
    se aleja más de `radius` o cuando falta el balón.
    """
    team, dist = proximity(trk)
    key = np.where(dist.min(axis=1) <= radius, team, NOBODY).astype(np.int8)
    out = np.full(len(key), NOBODY, dtype=np.int8)
    if len(key) == 0:
        return out
    edges = np.flatnonzero(key[1:] != key[:-1]) + 1
    starts = np.concatenate(([0], edges))
    stops = np.concatenate((edges, [len(key)]))
    for start, stop in zip(starts, stops):
        if key[start] != NOBODY and stop - start >= min_frames:
            out[start:stop] = key[start]
    return out


def evidence(trk, method=None):
    """NEAREST_SCORE a favor del equipo que señala la versión `method` (por defecto, METHOD).

    Donde la versión no opina (sin balón, o sin cumplir su condición), la fila queda a cero.
    """
    method = METHOD if method is None else method
    if method == N1:
        team = nearest_team(trk)
    elif method == N2:
        team = margin_team(trk)
    elif method == RET:
        team = retention_team(trk)
    else:
        raise ValueError("versión de la evidencia desconocida: {!r}; son {}".format(method, METHODS))
    score, allowed = no_evidence(len(trk.bx))
    score[team == H, H] = NEAREST_SCORE
    score[team == A, A] = NEAREST_SCORE
    return score, allowed
