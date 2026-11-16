"""Detector de cambios de posesión: rasgos, línea base con reglas y cómo lo usa el decodificador. APAGADO.

**Qué es** (docs/decisiones.md, 16/11, «detector de cambios de posesión»). La evidencia de equipo (B5) contesta
«¿quién tiene el balón?» y, tras un cambio, sigue votando un rato al equipo anterior. Esta pieza contesta otra
pregunta: «¿acaba de cambiar la posesión en este frame, y hacia qué equipo?». Su salida es `p`, de forma (n, 2):
la probabilidad de un cambio hacia `H` (columna 0) y hacia `A` (columna 1) en cada frame. B5 no se toca.

**Cómo la usa el pipeline,** con las dos cosas apagadas por defecto:

- `rebaja(p, w)`: cuánto baja el coste de cambiar de equipo en cada frame. Va a `temporal.decode_cambios` por
  `pipeline.run(..., cambios=...)`.
- `capa(p, gamma, ventana)`: una evidencia `(score, allowed)` como las demás, que empuja hacia el equipo nuevo
  durante `ventana` frames después del cambio. Va en `extra`.

**De dónde sale `p`.** De un modelo entrenado en la DFL sobre `rasgos` (validation/cambios/), o de la línea base
con reglas de este fichero (`p_reglas`). La predicción del modelo en numpy se escribe aquí solo si el candidato
pasa su regla de entrada.

**Qué balón ve.** El de `trk`, en metros. Con el balón del vídeo táctico (validation/balon_video/), se le pasa el
`Tracking` con ese balón y `fuente`, que dice en qué frames el balón es del vídeo. El resto del pipeline sigue con
el balón de siempre. Como todas las piezas, no abre ficheros.
"""

import numpy as np

from possession.tracking import N_STATES, H, A

K = (6, 13, 25)  # frames: los desfases de los rasgos. Ninguno pasa de 25 (decisión del 16/11)
RADIO = 2.0  # m: «a menos de 2 m del balón»
SEMIANCHO = 12  # frames: la clase «cambio» cubre los frames a esta distancia o menos del cambio

# Línea base con reglas (paso 0 de la decisión). Sin ajustar.
PASO_TOQUE = 6  # frames antes y después del toque
GIRO_TOQUE = 30.0  # grados
CAMBIO_VELOCIDAD = 0.40  # cambio relativo de la velocidad
CONFIRMA = 20  # frames que el equipo nuevo tiene que seguir siendo el más cercano


def _desplazar(a, s):
    """a[t + s], con NaN donde t + s se sale."""
    out = np.full(a.shape, np.nan)
    if s == 0:
        out[:] = a
    elif s > 0:
        out[:-s] = a[s:]
    else:
        out[-s:] = a[:s]
    return out


def distancias(trk):
    """(d, cerca): la distancia del jugador más cercano de cada equipo al balón, forma (n, 2), con NaN sin balón o
    sin jugadores de ese equipo, y cuántos jugadores de cada equipo hay a `RADIO` o menos (NaN sin balón)."""
    bx, by = np.asarray(trk.bx, dtype=float), np.asarray(trk.by, dtype=float)
    n = len(bx)
    d = np.full((n, 2), np.nan)
    cerca = np.full((n, 2), np.nan)
    hay = ~np.isnan(bx)
    for e in (H, A):
        columnas = np.flatnonzero(np.asarray(trk.team) == e)
        if not len(columnas):
            continue
        dist = np.hypot(np.asarray(trk.px)[:, columnas] - bx[:, None], np.asarray(trk.py)[:, columnas] - by[:, None])
        visto = ~np.isnan(dist)
        algun = visto.any(axis=1)
        d[algun, e] = np.min(np.where(visto, dist, np.inf), axis=1)[algun]
        cerca[hay, e] = np.sum(visto & (dist <= RADIO), axis=1)[hay]
    return d, cerca


def _movimiento(bx, by, k, fps):
    """Velocidad del balón (m/s) entre t−k y t y entre t y t+k, y el ángulo de giro entre los dos tramos (grados)."""
    ax, ay = bx - _desplazar(bx, -k), by - _desplazar(by, -k)
    dx, dy = _desplazar(bx, k) - bx, _desplazar(by, k) - by
    antes, despues = np.hypot(ax, ay) * fps / k, np.hypot(dx, dy) * fps / k
    with np.errstate(invalid="ignore", divide="ignore"):
        coseno = (ax * dx + ay * dy) / (np.hypot(ax, ay) * np.hypot(dx, dy))
    giro = np.degrees(np.arccos(np.clip(coseno, -1.0, 1.0)))
    return antes, despues, giro


def _fraccion(mascara, k):
    """Fracción de True en [t − k, t + k], contando solo los frames que existen."""
    suma = np.concatenate(([0], np.cumsum(mascara.astype(np.int64))))
    i = np.arange(len(mascara))
    bajo, alto = np.maximum(0, i - k), np.minimum(len(mascara), i + k + 1)
    return (suma[alto] - suma[bajo]) / (alto - bajo)


def rasgos(trk, fuente=None, ks=K):
    """(X, nombres): los rasgos del detector, una fila por frame. NaN donde falta el balón o el dato.

    `fuente`: (n,) bool, True donde el balón de `trk` es el del vídeo; sin ella, todo False (balón del ATD).
    Los rasgos de cada equipo van en columnas `..._H` y `..._A`; los que comparan los dos son H menos A. Para
    intercambiar los equipos basta con llamarla con `trk._replace(team=1 - trk.team)`.
    """
    bx, by = np.asarray(trk.bx, dtype=float), np.asarray(trk.by, dtype=float)
    n = len(bx)
    fuente = np.zeros(n, dtype=bool) if fuente is None else np.asarray(fuente, dtype=bool)
    d, cerca = distancias(trk)
    dif = d[:, H] - d[:, A]
    falta = np.isnan(bx)
    columnas, nombres = [d[:, H], d[:, A], dif], ["d_H_0", "d_A_0", "dif_0"]
    for k in ks:
        for s, marca in ((-k, "m"), (k, "p")):
            columnas += [_desplazar(d[:, H], s), _desplazar(d[:, A], s), _desplazar(dif, s),
                         _desplazar(cerca[:, H], s), _desplazar(cerca[:, A], s)]
            nombres += ["{}_{}{}".format(x, marca, k) for x in ("d_H", "d_A", "dif", "cerca_H", "cerca_A")]
        antes, despues, giro = _movimiento(bx, by, k, float(trk.fps))
        columnas += [_desplazar(dif, k) - _desplazar(dif, -k), antes, despues, giro, despues - antes,
                     _fraccion(falta, k), _fraccion(fuente, k)]
        nombres += ["{}_{}".format(x, k) for x in ("cambio_dif", "v_antes", "v_despues", "giro", "aceleracion",
                                                    "sin_balon", "del_video")]
    return np.column_stack(columnas), nombres


# -- la línea base con reglas ---------------------------------------------------------------------------

def toques(trk):
    """(frames, equipos) de los toques: el balón gira más de `GIRO_TOQUE` o cambia su velocidad más de
    `CAMBIO_VELOCIDAD` entre los `PASO_TOQUE` frames de antes y los de después, con un jugador a menos de `RADIO`.
    De cada racha de frames seguidos que lo cumplen queda el del medio. El equipo es el del más cercano."""
    bx, by = np.asarray(trk.bx, dtype=float), np.asarray(trk.by, dtype=float)
    d, _ = distancias(trk)
    antes, despues, giro = _movimiento(bx, by, PASO_TOQUE, float(trk.fps))
    with np.errstate(invalid="ignore", divide="ignore"):
        relativo = np.abs(despues - antes) / np.maximum(antes, despues)
        es = ((giro > GIRO_TOQUE) | (relativo > CAMBIO_VELOCIDAD)) & (np.fmin(d[:, H], d[:, A]) < RADIO)
    es = np.where(np.isnan(antes) | np.isnan(despues), False, es)
    bordes = np.flatnonzero(np.diff(np.concatenate(([0], es.astype(np.int8), [0]))))
    frames = (bordes[0::2] + bordes[1::2] - 1) // 2
    with np.errstate(invalid="ignore"):
        equipos = np.where(d[frames, A] < d[frames, H], A, H)
    return frames.astype(np.int64), equipos.astype(np.int8)


def p_reglas(trk):
    """La línea base: `p` (n, 2) con 1 a `SEMIANCHO` frames o menos de cada cambio que ven las reglas.

    Hay cambio hacia X en un toque de X si el toque anterior era del otro equipo y, además, el toque siguiente es
    de X o X es el más cercano al balón en todos los frames con balón de los `CONFIRMA` siguientes (y hay alguno).
    """
    n = len(trk.bx)
    p = np.zeros((n, 2))
    frames, equipos = toques(trk)
    d, _ = distancias(trk)
    for i in range(1, len(frames)):
        t, x = int(frames[i]), int(equipos[i])
        if equipos[i - 1] == x:
            continue
        sigue = i + 1 < len(frames) and equipos[i + 1] == x
        if not sigue:
            tramo = d[t + 1:t + 1 + CONFIRMA]
            con = ~np.isnan(tramo).any(axis=1)
            sigue = bool(con.any() and np.all(tramo[con, x] < tramo[con, 1 - x]))
        if sigue:
            p[max(0, t - SEMIANCHO):t + SEMIANCHO + 1, x] = 1.0
    return p


# -- cómo lo usa el decodificador -------------------------------------------------------------------------

def _comprobar(p, n=None):
    p = np.asarray(p, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2 or (n is not None and len(p) != n):
        raise ValueError("`p` tiene que ser de forma (n, 2)")
    if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
        raise ValueError("`p` tiene que estar entre 0 y 1")
    return p


def rebaja(p, w):
    """La rebaja del coste de cambiar de equipo, `w · p`, de forma (n, 2): el `bonus` de `temporal.decode_cambios`."""
    if w < 0:
        raise ValueError("`w` no puede ser negativo")
    return float(w) * _comprobar(p)


def capa(p, gamma, ventana, retraso=SEMIANCHO):
    """Evidencia `(score, allowed)`: `score_X(t) = gamma · max de p_X(τ)` con τ en [t − retraso − ventana, t − retraso].

    Empuja hacia el equipo nuevo durante `ventana` frames después de un cambio. `retraso` es el semiancho de la
    clase: con un detector perfecto (`p` = 1 a `SEMIANCHO` frames o menos del cambio), el empujón empieza en el
    cambio y no antes. No prohíbe nada y no puntúa `D`.
    """
    p = _comprobar(p)
    if gamma < 0 or ventana < 0 or retraso < 0:
        raise ValueError("`gamma`, `ventana` y `retraso` no pueden ser negativos")
    n = len(p)
    score = np.zeros((n, N_STATES))
    if n and gamma > 0:
        relleno = np.concatenate((np.zeros((int(ventana) + int(retraso), 2)), p))
        ventanas = np.lib.stride_tricks.sliding_window_view(relleno, int(ventana) + 1, axis=0)
        score[:, :2] = float(gamma) * ventanas[:n].max(axis=2)
    return score, np.ones((n, N_STATES), dtype=bool)
