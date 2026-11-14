"""Constantes y utilidades que comparten los diagnósticos de validation/partido/."""

import sys
import warnings

import numpy as np

import games

FPS = games.GAMES[games.GAME]["fps"]
SET_PIECES_CODE = "set pieces"
GOALS_CODE = "goals"
KICKOFF_TYPES = ("kick off (start)", "kick off (after goal)")
# Radio alrededor del punto central: el balón está colocado en él, con margen para el ruido.
CENTRE_RADIUS_M = 2.0
# Un hueco sin balón de más de 1 s corta un tramo de balón quieto. Con huecos más cortos el tramo
# sigue: al ATD le falta el balón en el 41 % de los frames evaluados, a ratos sueltos.
MAX_GAP_FRAMES = FPS


def utf8_stdout():
    """Salida en UTF-8 también al redirigirla a un fichero: en Windows, sin esto, usa la página de
    códigos regional (cp1252) y se rompe con caracteres como "≥". Si quien llama ha cambiado la salida
    por un objeto que no se puede reconfigurar (un StringIO en un test, por ejemplo), se deja como
    está."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def norm(text):
    return (text or "").strip().lower()


def pct(part, whole):
    return "{:5.1f} %".format(100.0 * part / whole) if whole else "  —  "


def graded_mask(game, n_frames):
    """True en los frames evaluados de las dos partes."""
    mask = np.zeros(n_frames, dtype=bool)
    for _, first, last in games.half_video_blocks(game):
        mask[first:last + 1] = True
    return mask


# -- jugadores y agrupación por tipo de reinicio (agregados_*.py) ---------------------------------------

# Velocidad por encima de la cual un salto de un slot entre frames es un intercambio de identidad, no un
# jugador (los jugadores no pasan de ~12 m/s).
MAX_PLAYER_SPEED_MS = 12.0
# Tipos de reinicio con menos casos se juntan en "otros": un tipo con pocos casos identifica jugadas.
MIN_CASES_PER_TYPE = 5
KICKOFF_GROUP = "kick off (todos)"


def slot_speeds(px, py):
    """Velocidad (m/s) de cada slot por frame, con diferencia centrada de ±2 frames; NaN si falta algún
    extremo o si el salto es imposible (intercambio de slot)."""
    v = np.full(px.shape, np.nan, dtype=np.float32)
    v[2:-2] = np.hypot(px[4:] - px[:-4], py[4:] - py[:-4]) / (4.0 / FPS)
    v[v > MAX_PLAYER_SPEED_MS] = np.nan
    return v


def mean_speed(px, py):
    """Velocidad media de los slots vistos en cada frame (m/s); NaN si no hay ninguno."""
    v = slot_speeds(px, py)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # frames sin ningún slot: nanmean avisa y da NaN
        return np.nanmean(v, axis=1)


def moving_average(values, half_width):
    """Media móvil centrada de 2·half_width + 1 frames que ignora los NaN."""
    values = np.asarray(values, dtype=float)
    ok = ~np.isnan(values)
    total = np.concatenate(([0.0], np.cumsum(np.where(ok, values, 0.0))))
    count = np.concatenate(([0.0], np.cumsum(ok.astype(float))))
    index = np.arange(len(values))
    low = np.maximum(0, index - half_width)
    high = np.minimum(len(values), index + half_width + 1)
    n = count[high] - count[low]
    with np.errstate(all="ignore"):
        return np.where(n > 0, (total[high] - total[low]) / np.maximum(n, 1), np.nan)


def restart_type(event):
    """Tipo de un SET PIECE, con los dos saques iniciales siempre juntos."""
    kind = norm(event["tags"].get("Type"))
    return KICKOFF_GROUP if kind in KICKOFF_TYPES else (kind or "(sin tipo)")


def grouped_by_type(events):
    """{tipo: [eventos]} de los SET PIECES; los tipos con menos de MIN_CASES_PER_TYPE casos van a "otros"."""
    groups = {}
    for event in events:
        if norm(event["code"]) == SET_PIECES_CODE:
            groups.setdefault(restart_type(event), []).append(event)
    out = {}
    for kind, group in groups.items():
        key = kind if len(group) >= MIN_CASES_PER_TYPE or kind == KICKOFF_GROUP else "otros"
        out.setdefault(key, []).extend(group)
    return out


def bins_s(values_s, edges):
    """Recuento en intervalos gruesos de segundos. `edges` son los cortes; devuelve [(nombre, n)]."""
    values_s = np.asarray(values_s, dtype=float)
    names, counts = [], []
    lows = [-np.inf] + list(edges)
    highs = list(edges) + [np.inf]
    for low, high in zip(lows, highs):
        if low == -np.inf:
            name = "< {:g} s".format(high)
        elif high == np.inf:
            name = "≥ {:g} s".format(low)
        else:
            name = "{:g} a {:g} s".format(low, high)
        names.append(name)
        counts.append(int(np.sum((values_s >= low) & (values_s < high))))
    return list(zip(names, counts))


def print_bins(title, values_s, edges, indent="      "):
    values_s = [v for v in values_s if v is not None and not np.isnan(v)]
    print("{}{} (n={})".format(indent, title, len(values_s)))
    for name, n in bins_s(values_s, edges):
        print("{}   {:<14} {:>3}  ({})".format(indent, name, n, pct(n, len(values_s))))


def quantiles(values, qs=(10, 50, 90)):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if values.size == 0:
        return "sin datos"
    return "  ".join("p{}={:.2f}".format(q, v) for q, v in zip(qs, np.percentile(values, qs)))
