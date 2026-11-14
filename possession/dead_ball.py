"""Detector de balón muerto (`D`). Devuelve una máscara booleana por frame de vídeo.

Versión 1: solo el tramo de cada parte anterior a su saque inicial (el inicio de la 2ª parte de B5 en
docs/investigacion_metodos.md §2.2). En la 2ª parte son los 2.934 frames que van del primer frame
evaluado (110.808) al saque (113.742), todos `D` según FAQ.md. En la 1ª parte el primer frame evaluado
ya es el saque, así que no hay tramo.

Los frames de saque son los que publica FAQ.md, tal como los guarda el código oficial
(starter/load_smart_tagging.py). No se fechan con el balón del ATD: con la regla probada (balón quieto
en el centro que empieza a moverse) no se encontró el golpeo en ninguno de los 6 saques iniciales. Lo
que se probó y lo que se midió está en validation/resultados/2026-11-12_balon_muerto_atd.md y en
docs/decisiones.md.
"""

import numpy as np

import games
from starter.load_smart_tagging import KICKOFF_VIDEO_FRAMES

HALF_NAMES = {1: "1st Half", 2: "2nd Half"}
# KICKOFF_VIDEO_FRAMES son los saques de este partido y de ningún otro.
KICKOFF_GAME = "BAR-ATH"


def pre_kickoff(game=games.GAME):
    """Máscara con `D` desde el primer frame de cada parte hasta su saque, sin incluirlo."""
    if game != KICKOFF_GAME:
        raise ValueError("los frames de saque solo son de {}, no de {}".format(KICKOFF_GAME, game))
    mask = np.zeros(games.GAMES[game]["n_video_frames"], dtype=bool)
    for half, first, _ in games.half_video_blocks(game):
        kickoff = KICKOFF_VIDEO_FRAMES[HALF_NAMES[half]]
        if kickoff > first:
            mask[first:kickoff] = True
    return mask


def dead_mask(paths=None, game=games.GAME):
    """Máscara de `D` de 199.319 posiciones, indexada por frame de vídeo.

    Recibe las rutas de games.asset_paths() por la interfaz común del pipeline, aunque esta versión no
    lee ningún fichero.
    """
    return pre_kickoff(game)
