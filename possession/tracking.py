"""El tracking en el formato común del pipeline, y el contrato de las piezas.

Todas las piezas reciben un `Tracking` y devuelven arrays por frame de vídeo. El mismo código corre con el
ATD del partido y con los partidos abiertos de la Bundesliga que prepara `validation/harness/`. Por eso
ninguna pieza abre ficheros por su cuenta, salvo `dead_ball.py`, que usa los ficheros del partido.

Contrato de las piezas de evidencia (`candidates`, `dead_state`, `dead_ball`): cada una tiene una función
`evidence(trk, ...)` que devuelve `(score, allowed)`. La pieza de equipo de la entrega es, desde el 14/11,
`aprendida.evidence_b5` (la apuesta B; `pipeline.PIECES`), con la misma interfaz:

- `score`: array (n, 3) de float, una columna por estado en el orden `H`, `A`, `D`. Es aditiva: el pipeline
  suma las de todas las piezas. Más alto es más probable. Solo cuentan las diferencias entre las columnas
  de un mismo frame; una fila a cero es "no opino".
- `allowed`: array (n, 3) de bool. `False` prohíbe ese estado en ese frame. El pipeline cruza (AND) las de
  todas las piezas. Sirve para lo que se sabe seguro, como el tramo antes del saque.

`n` es el número de frames del tracking: 199.319 en el partido.
"""

import collections

import numpy as np

import games
from possession import io
from starter.baseline import team_of_each_track

# Códigos de las etiquetas, en el mismo orden que evaluation/possession_metrics.LABELS.
H, A, D, X = 0, 1, 2, 3
LETTERS = np.array(["H", "A", "D", "X"])
N_STATES = 3

Tracking = collections.namedtuple("Tracking", ["bx", "by", "px", "py", "team", "pitch", "blocks", "fps"])
Tracking.__doc__ = """Tracking de un partido, indexado por frame de vídeo.

bx, by   balón en metros, forma (n,). NaN donde no se ve.
px, py   slots de jugadores en metros, forma (n, n_slots). NaN donde falta el slot.
team     equipo de cada slot, forma (n_slots,): 0 local (`H`), 1 visitante (`A`).
pitch    (largo, ancho) del campo en metros. El origen está en una esquina: x va de 0 a largo.
blocks   tramos evaluados, como tuplas (inicio, fin) con el fin sin incluir. Uno por parte.
fps      frames por segundo.

Un slot es un tracklet, no un jugador: su índice no identifica a la misma persona a lo largo del partido.
Ninguna pieza puede apoyarse en que un slot sea alguien.
"""


def evaluated_blocks(game=games.GAME):
    """Tramos evaluados de cada parte, con el fin sin incluir (games.half_video_blocks lo incluye)."""
    return tuple((first, last + 1) for _, first, last in games.half_video_blocks(game))


def no_evidence(n):
    """Evidencia vacía: puntuación a cero y todo permitido."""
    return np.zeros((n, N_STATES)), np.ones((n, N_STATES), dtype=bool)


def from_files(atd_raw, atd_meta, n_frames, pitch, blocks, fps, report=None):
    """Un `Tracking` a partir de un ATD y sus metadatos.

    Con `report` (un diccionario), apunta en `report["atd"]` cuántas líneas del ATD se leyeron y cuántas se
    saltaron (`io.COUNT_KEYS`), más `frames_evaluados_sin_linea`: los frames de los tramos evaluados sin
    ninguna línea válida, que es lo que dejaría un fichero cortado. Solo recuentos.
    """
    counts, seen = {}, np.zeros(n_frames, dtype=bool)
    bx, by, _ = io.load_ball(atd_raw, n_frames, pitch, counts=counts, seen=seen)
    px, py = io.load_players(atd_raw, n_frames, pitch)
    team = team_of_each_track(atd_meta)
    if len(team) != px.shape[1]:
        raise ValueError("los metadatos reparten {} slots y el ATD trae {}".format(len(team), px.shape[1]))
    if report is not None:
        counts["frames_evaluados_sin_linea"] = int(sum(np.sum(~seen[start:stop]) for start, stop in blocks))
        report["atd"] = counts
    return Tracking(bx, by, px, py, team, tuple(pitch), tuple(blocks), fps)


def from_atd(paths, game=games.GAME, report=None):
    """El ATD del partido como `Tracking`. Lee datos del partido: solo lo ejecuta una persona.

    `paths` es el diccionario de games.asset_paths(). `report`, como en `from_files`.
    """
    info = games.GAMES[game]
    return from_files(paths["atd_raw"], paths["atd_meta"], info["n_video_frames"], info["pitch"],
                      evaluated_blocks(game), info["fps"], report=report)
