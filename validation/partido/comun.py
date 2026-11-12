"""Constantes y utilidades que comparten los diagnósticos de validation/partido/."""

import sys

import numpy as np

import games

FPS = games.GAMES[games.GAME]["fps"]
SET_PIECES_CODE = "set pieces"
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
