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
from possession.tracking import A, H, no_evidence
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


def evidence(trk, paths=None, game=games.GAME):
    """Lo que este módulo aporta al pipeline, con la interfaz común: `(score, allowed)`, de forma (n, 3).

    Columnas en el orden `H`, `A`, `D` (possession/tracking.py). Versión 0: en los frames de `dead_mask`
    solo se permite `D`, y no se puntúa nada más.

    Es la pieza del partido: usa las constantes de saque y, cuando los necesite, los ficheros de `paths`
    (Smart Tagging), así que no corre en la DFL. Lo que solo necesita el tracking va en
    possession/dead_state.py.

    **Con `paths=None` no se abre ningún fichero:** solo entran las capas que no los necesitan. Así la
    llama `validation/scripts/prueba_pipeline.py`, que ejecuta Claude y no puede leer el partido. `None`
    nunca significa «usa games.asset_paths()».
    """
    n = len(trk.bx)
    score, allowed = no_evidence(n)
    mask = dead_mask(paths, game)
    if len(mask) != n:
        raise ValueError("la máscara de D tiene {} frames y el tracking {}".format(len(mask), n))
    allowed[mask, H] = False
    allowed[mask, A] = False  # ni H ni A: solo D
    return score, allowed
