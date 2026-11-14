"""Estado de balón muerto (`D`) a partir del tracking: ¿está parado el juego en este frame?

Solo usa a los jugadores del `Tracking`, así que corre igual en el partido y en la DFL del harness. El
balón no entra: en la DFL va tapado durante el `D` y delataría la etiqueta, y en el ATD que falte no
significa `D`. Los instantes exactos (inicio y fin de cada parada) y lo que sale de los ficheros del
partido van en possession/dead_ball.py.

Versión 1: una regresión logística sobre rasgos de equipo sin identidad (velocidades de los jugadores,
cuántos van lentos, forma de los equipos), entrenada con los 7 partidos abiertos de la DFL (Bassek et
al., 2025, CC BY 4.0). Devuelve el logaritmo de la razón de probabilidades de `D` en la columna `D`.

- Los coeficientes de `MODEL` los calcula validation/scripts/d_estado/entrenar.py, que es el único sitio
  donde se usa scikit-learn. Aquí solo hay numpy.
- Qué se comparó, cómo se midió y qué salió: docs/decisiones.md (14/11) y
  validation/resultados/2026-11-14_d_estado.md.

Interfaz: `evidence(trk)` devuelve `(score, allowed)`; ver possession/tracking.py. La histéresis y la
duración mínima no van aquí: las pone el decodificador (possession/temporal.py).
"""

import numpy as np

from possession.tracking import D, no_evidence

# -- definición de los rasgos ---------------------------------------------------------------------------
# Ninguna constante sale del partido ni de la ventana pública: son medidas del campo o valores fijados
# antes de medir (docs/decisiones.md, 14/11).

# La velocidad de un slot es su desplazamiento entre el frame t - SPEED_LAG y el t + SPEED_LAG. Es la
# misma definición que validation/partido/comun.py, para que el agregado 4 del partido sea comparable.
SPEED_LAG = 2
# Por encima de esto el salto no es un jugador: es un slot que ha cambiado de persona.
MAX_PLAYER_SPEED = 12.0  # m/s
SLOW_SPEED = 1.0  # m/s: por debajo, el jugador va andando o está parado
OUTSIDE_MARGIN = 0.3  # m fuera de las líneas para contar a un jugador como fuera del campo
BOX_DEPTH, BOX_HALF_WIDTH = 16.5, 20.16  # m: el área grande, por reglamento

# Series por frame, antes de promediar en el tiempo.
RAW = ("v_media", "v_p75", "v_max", "frac_lentos", "fuera", "caja_max", "dist_centroides", "dispersion",
       "en_su_mitad")

# Rasgos: nombre -> (serie, segundos hacia atrás, segundos hacia delante) de la ventana en la que se
# promedia. Los tres candidatos que se compararon son subconjuntos de esta tabla (E1, E2 y E3).
FEATURES = {
    "v_media_1s": ("v_media", 0.5, 0.5),
    "v_media_2s": ("v_media", 1.0, 1.0),
    "v_media_4s": ("v_media", 2.0, 2.0),
    "frac_lentos_2s": ("frac_lentos", 1.0, 1.0),
    "v_p75_2s": ("v_p75", 1.0, 1.0),
    "v_max_2s": ("v_max", 1.0, 1.0),
    "fuera_2s": ("fuera", 1.0, 1.0),
    "caja_max_2s": ("caja_max", 1.0, 1.0),
    "dist_centroides_2s": ("dist_centroides", 1.0, 1.0),
    "dispersion_2s": ("dispersion", 1.0, 1.0),
    "en_su_mitad_2s": ("en_su_mitad", 1.0, 1.0),
    "v_media_antes_2s": ("v_media", 2.0, 0.0),
    "v_media_despues_2s": ("v_media", 0.0, 2.0),
    "v_media_antes_4s": ("v_media", 4.0, 0.0),
    "v_media_despues_4s": ("v_media", 0.0, 4.0),
    "frac_lentos_antes_2s": ("frac_lentos", 2.0, 0.0),
    "frac_lentos_despues_2s": ("frac_lentos", 0.0, 2.0),
    "frac_lentos_antes_4s": ("frac_lentos", 4.0, 0.0),
    "frac_lentos_despues_4s": ("frac_lentos", 0.0, 4.0),
}
E1 = ("v_media_2s",)
E2 = E1 + ("v_media_1s", "v_media_4s", "frac_lentos_2s", "v_p75_2s", "v_max_2s", "fuera_2s", "caja_max_2s",
           "dist_centroides_2s", "dispersion_2s", "en_su_mitad_2s")
E3 = E2 + ("v_media_antes_2s", "v_media_despues_2s", "v_media_antes_4s", "v_media_despues_4s",
           "frac_lentos_antes_2s", "frac_lentos_despues_2s", "frac_lentos_antes_4s",
           "frac_lentos_despues_4s")

# -- el modelo ------------------------------------------------------------------------------------------

# La puntuación se recorta a ±SCORE_CLIP para que un rasgo disparatado en unos pocos frames (un slot que
# salta, por ejemplo) no pese más que varios segundos de evidencia normal. Fijado antes de medir.
SCORE_CLIP = 8.0
# La puntuación se redondea a múltiplos de 1/SCORE_GRID, que en binario son exactos. Así las sumas del
# decodificador también lo son: una diferencia en el último bit entre dos máquinas no cambia la salida, y
# esta pieza no altera cómo se deshacen los empates entre `H` y `A`.
SCORE_GRID = 1024.0

# El candidato E2, ajustado con los 7 partidos de la DFL (200.532 frames, 44,8 % `D`). Es la salida, tal
# cual, de validation/scripts/d_estado/entrenar.py; `--comprobar` dice si sigue saliendo lo mismo.
MODEL = {
    "intercept": 6.24631,
    "coef": {
        "v_media_2s": 3.92609,
        "v_media_1s": -1.37238,
        "v_media_4s": -5.15775,
        "frac_lentos_2s": -1.64454,
        "v_p75_2s": -0.273614,
        "v_max_2s": -0.680491,
        "fuera_2s": 3.31652,
        "caja_max_2s": 0.00296488,
        "dist_centroides_2s": 0.169896,
        "dispersion_2s": -0.170123,
        "en_su_mitad_2s": 1.61463,
    },
}

# Frames por bloque al calcular los rasgos, para no reservar varias matrices de todo el partido a la vez.
CHUNK = 20000


def _row_stats(values, valid, count):
    """Media de cada fila sobre las posiciones válidas; NaN en las filas sin ninguna."""
    total = np.where(valid, values, 0.0).sum(axis=1)
    return np.where(count > 0, total / np.maximum(count, 1), np.nan)


def _row_std(values, valid):
    """Desviación típica de cada fila sobre las posiciones válidas; NaN en las filas sin ninguna."""
    count = valid.sum(axis=1)
    mean = _row_stats(values, valid, count)
    spread = np.where(valid, (values - mean[:, None]) ** 2, 0.0).sum(axis=1)
    return np.where(count > 0, np.sqrt(spread / np.maximum(count, 1)), np.nan)


def _row_percentile(values, valid, count, q):
    """Percentil `q` de cada fila sobre las posiciones válidas, con interpolación lineal."""
    ordered = np.sort(np.where(valid, values, np.inf), axis=1)  # las no válidas quedan al final
    position = (q / 100.0) * np.maximum(count - 1, 0)
    low = np.floor(position).astype(np.int64)
    high = np.minimum(low + 1, np.maximum(count - 1, 0))
    rows = np.arange(len(values))
    a, b = ordered[rows, low], ordered[rows, high]
    return np.where(count > 0, a + (b - a) * (position - low), np.nan)


def raw_series(trk):
    """Las series de `RAW`, una por frame: {nombre: array (n,)}. NaN donde no se ve a nadie.

    Todo son agregados de los slots que se ven en cada frame. Nada depende del índice de un slot, salvo
    su velocidad entre dos frames a 0,16 s, que se descarta si el salto no es de un jugador.
    """
    with np.errstate(invalid="ignore", divide="ignore"):  # NaN y filas vacías: ya se tratan abajo
        return _raw_series(trk)


def _raw_series(trk):
    n, slots = trk.px.shape
    length, width = trk.pitch
    lag = SPEED_LAG
    seconds = 2.0 * lag / trk.fps
    home, away = trk.team == 0, trk.team == 1
    out = {name: np.full(n, np.nan) for name in RAW}
    for start in range(0, n, CHUNK):
        stop = min(n, start + CHUNK)
        lo, hi = max(0, start - lag), min(n, stop + lag)
        x = trk.px[lo:hi].astype(np.float64)
        y = trk.py[lo:hi].astype(np.float64)
        rows = slice(start - lo, stop - lo)
        here_x, here_y = x[rows], y[rows]
        seen = ~np.isnan(here_x) & ~np.isnan(here_y)

        # Velocidad de cada slot, con NaN donde falta un extremo, en los bordes del tracking o si salta.
        speed = np.full(here_x.shape, np.nan)
        first, last = max(start, lag), min(stop, n - lag)
        if last > first:
            before = slice(first - lag - lo, last - lag - lo)
            after = slice(first + lag - lo, last + lag - lo)
            step = np.hypot(x[after] - x[before], y[after] - y[before]) / seconds
            speed[first - start:last - start] = step
        moving = ~np.isnan(speed) & (speed <= MAX_PLAYER_SPEED)
        slow = moving & (speed < SLOW_SPEED)
        count = moving.sum(axis=1)
        block = slice(start, stop)
        out["v_media"][block] = _row_stats(speed, moving, count)
        out["v_p75"][block] = _row_percentile(speed, moving, count, 75.0)
        out["v_max"][block] = np.where(count > 0, np.where(moving, speed, -np.inf).max(axis=1), np.nan)
        out["frac_lentos"][block] = np.where(count > 0, slow.sum(axis=1) / np.maximum(count, 1), np.nan)

        # Posiciones: jugadores fuera del campo y dentro de cada área.
        any_seen = seen.any(axis=1)
        outside = seen & ((here_x < -OUTSIDE_MARGIN) | (here_x > length + OUTSIDE_MARGIN)
                          | (here_y < -OUTSIDE_MARGIN) | (here_y > width + OUTSIDE_MARGIN))
        in_width = seen & (np.abs(here_y - width / 2.0) < BOX_HALF_WIDTH)
        box_low = (in_width & (here_x < BOX_DEPTH)).sum(axis=1)
        box_high = (in_width & (here_x > length - BOX_DEPTH)).sum(axis=1)
        out["fuera"][block] = np.where(any_seen, outside.sum(axis=1), np.nan)
        out["caja_max"][block] = np.where(any_seen, np.maximum(box_low, box_high), np.nan)

        # Forma de los equipos: centroides, dispersión y cuánto está cada uno en una sola mitad.
        centroid, spread, one_half = [], [], []
        for members in (home, away):
            tx, ty, tseen = here_x[:, members], here_y[:, members], seen[:, members]
            tcount = tseen.sum(axis=1)
            centroid.append((_row_stats(tx, tseen, tcount), _row_stats(ty, tseen, tcount)))
            spread.append((_row_std(tx, tseen), _row_std(ty, tseen)))
            low_half = (tseen & (tx < length / 2.0)).sum(axis=1)
            fraction = np.where(tcount > 0, low_half / np.maximum(tcount, 1), np.nan)
            one_half.append(np.maximum(fraction, 1.0 - fraction))
        (hx, hy), (ax, ay) = centroid
        out["dist_centroides"][block] = np.hypot(hx - ax, hy - ay)
        out["dispersion"][block] = (spread[0][0] + spread[0][1] + spread[1][0] + spread[1][1]) / 4.0
        out["en_su_mitad"][block] = np.minimum(one_half[0], one_half[1])
    return out


def window_mean(values, back, ahead):
    """Media de `values` entre el frame t - back y el t + ahead, los dos incluidos, sin contar los NaN.

    NaN donde no hay ningún dato en la ventana.
    """
    values = np.asarray(values, dtype=np.float64)
    ok = ~np.isnan(values)
    total = np.concatenate(([0.0], np.cumsum(np.where(ok, values, 0.0))))
    count = np.concatenate(([0], np.cumsum(ok)))
    index = np.arange(len(values))
    low = np.maximum(0, index - back)
    high = np.minimum(len(values), index + ahead + 1)
    seen = count[high] - count[low]
    return np.where(seen > 0, (total[high] - total[low]) / np.maximum(seen, 1), np.nan)


def features(trk, names):
    """Los rasgos de `names` (claves de `FEATURES`): {nombre: array (n,)}. NaN donde no se ve a nadie."""
    unknown = sorted(set(names) - set(FEATURES))
    if unknown:
        raise KeyError("rasgos desconocidos: {}".format(unknown))
    raw = raw_series(trk)
    out = {}
    for name in names:
        series, back_s, ahead_s = FEATURES[name]
        out[name] = window_mean(raw[series], int(round(back_s * trk.fps)), int(round(ahead_s * trk.fps)))
    return out


def log_odds(trk, model=None):
    """Logaritmo de la razón de probabilidades de `D` por frame, forma (n,). Cero donde falta algún rasgo.

    `model` es {"intercept": float, "coef": {rasgo: peso}}; por defecto, `MODEL`. Un modelo sin rasgos
    no opina.
    """
    model = MODEL if model is None else model
    n = len(trk.bx)
    names = sorted(model["coef"])
    if not names:
        return np.zeros(n)
    values = features(trk, names)
    total = np.full(n, float(model["intercept"]))
    for name in names:  # en orden alfabético: la suma sale igual en cualquier máquina
        total = total + float(model["coef"][name]) * values[name]
    total = np.where(np.isnan(total), 0.0, total)
    return np.round(np.clip(total, -SCORE_CLIP, SCORE_CLIP) * SCORE_GRID) / SCORE_GRID


def evidence(trk):
    """El logaritmo de la razón de probabilidades de `D` en la columna `D`. No prohíbe nada.

    Positivo: el juego parece parado. Negativo: parece vivo. Cero: no opina (no se ve a ningún jugador).
    """
    score, allowed = no_evidence(len(trk.bx))
    score[:, D] = log_odds(trk)
    return score, allowed
