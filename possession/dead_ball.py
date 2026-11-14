"""Detector de balón muerto (`D`): fronteras y anclas de cada parada. Es la pieza del partido.

Capas, en el orden de docs/decisiones.md (14/11, «fronteras y anclas»):

- **Tramo antes del saque de cada parte** (v1): en la 2ª parte son los 2.934 frames que van del primer
  frame evaluado (110.808) al saque (113.742), todos `D` según FAQ.md. En la 1ª parte el primer frame
  evaluado ya es el saque, así que no hay tramo. Los frames de saque son los que publica FAQ.md, tal como
  los guarda el código oficial (starter/load_smart_tagging.py).
- **De cada gol a su saque:** desde el fin de la ventana `GOALS` del Smart Tagging hasta el inicio de la
  ventana de su `Kick Off (After Goal)`. Entre el gol y el saque el balón está muerto por reglamento, así
  que ese tramo es todo `D` si se cumplen tres cosas, las tres **[sin verificar]**: que la ventana `GOALS`
  acaba con el balón ya en la portería, que la del saque empieza en el reinicio o antes, y que cada `GOALS`
  es un gol válido (el Smart Tagging es automático). Si falla la primera se pierden unos frames de `D`; si
  fallan las otras, se fuerza `D` en juego.

Las dos son anclas duras: en esos frames solo se permite `D`. Lo que se probó y lo que se midió está en
docs/decisiones.md y en validation/resultados/ (2026-11-12_balon_muerto_atd.md y
2026-11-13_revision_balon_muerto.md).
"""

import xml.etree.ElementTree as ET

import numpy as np

import games
from possession.tracking import A, H, no_evidence
from starter.load_smart_tagging import KICKOFF_VIDEO_FRAMES

HALF_NAMES = {1: "1st Half", 2: "2nd Half"}
# KICKOFF_VIDEO_FRAMES son los saques de este partido y de ningún otro.
KICKOFF_GAME = "BAR-ATH"

# Smart Tagging: los códigos vienen en mayúsculas y los valores en formato título (DATA.md); se comparan
# en minúsculas.
GOALS_CODE = "goals"
SET_PIECES_CODE = "set pieces"
AFTER_GOAL_KICKOFF = "kick off (after goal)"
# Un saque que llega más tarde que esto después del fin de su gol no ancla nada: el tramo cruzaría el
# descanso o una parada que no es la del gol. Fijado antes de medir (docs/decisiones.md, 14/11).
MAX_GOAL_TO_KICKOFF_S = 180


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
    """Máscara de `D` de 199.319 posiciones, indexada por frame de vídeo, con todas las anclas duras.

    `paths` son las rutas de games.asset_paths(). Con `None` no se abre ningún fichero y solo va el tramo
    antes del saque; con rutas, también los tramos de cada gol a su saque, que salen del Smart Tagging.
    """
    mask = pre_kickoff(game)
    if paths is not None:
        n = len(mask)
        fps = games.GAMES[game]["fps"]
        for start, stop in goal_to_kickoff(smart_tagging_events(paths["smart_tagging"], fps), fps):
            mask[max(start, 0):max(min(stop, n), 0)] = True
    return mask


def _norm(text):
    return (text or "").strip().lower()


def smart_tagging_events(path, fps):
    """Instancias del Smart Tagging: [{code, type, start, end}], con el código y el tipo en minúsculas.

    Mismo criterio que starter/load_smart_tagging.load(): segundos × fps redondeado es el frame de vídeo, y
    `end` es el primer frame después del intervalo. Ordenadas por (start, end, code, type), para que el
    resultado no dependa del orden del fichero.
    """
    events = []
    for instance in ET.parse(path).iter("instance"):
        tags = {_norm(label.findtext("group")): label.findtext("text") for label in instance.findall("label")}
        events.append({
            "code": _norm(instance.findtext("code")),
            "type": _norm(tags.get("type")),
            "start": int(round(float(instance.findtext("start")) * fps)),
            "end": int(round(float(instance.findtext("end")) * fps)),
        })
    return sorted(events, key=lambda e: (e["start"], e["end"], e["code"], e["type"]))


def goal_to_kickoff(events, fps):
    """Tramos (inicio, fin), con el fin sin incluir, desde el fin de cada `GOALS` hasta el inicio de su saque.

    Se empareja hacia atrás: cada `Kick Off (After Goal)` con el último `GOALS` que acaba cuando el saque
    aún no ha empezado. El tramo no se ancla si entre los dos empieza otro `GOALS` u otro `SET PIECES`
    (un gol sin su saque, un gol falso o un reinicio por medio harían que el tramo tapara juego), ni si el
    saque llega más de MAX_GOAL_TO_KICKOFF_S después del fin del gol. Así cada gol y cada saque entran,
    como mucho, en un tramo.
    """
    goals = [e for e in events if e["code"] == GOALS_CODE]
    restarts = [e for e in events if e["code"] in (GOALS_CODE, SET_PIECES_CODE)]
    spans = []
    for kickoff in events:
        if kickoff["code"] != SET_PIECES_CODE or kickoff["type"] != AFTER_GOAL_KICKOFF:
            continue
        before = [g for g in goals if g["end"] <= kickoff["start"]]
        if not before:
            continue
        goal = max(before, key=lambda g: (g["end"], g["start"]))
        start, stop = goal["end"], kickoff["start"]
        if stop <= start or stop - start > MAX_GOAL_TO_KICKOFF_S * fps:
            continue
        if any(start <= e["start"] < stop for e in restarts if e is not goal and e is not kickoff):
            continue
        spans.append((start, stop))
    return spans


def evidence(trk, paths=None, game=games.GAME):
    """Lo que este módulo aporta al pipeline, con la interfaz común: `(score, allowed)`, de forma (n, 3).

    Columnas en el orden `H`, `A`, `D` (possession/tracking.py). Por ahora solo hay anclas duras: en sus
    frames solo se permite `D`, y no se puntúa nada.

    **Con `paths=None` no se abre ningún fichero:** solo entran las capas que no los necesitan, es decir,
    el tramo antes del saque. Así la llama `validation/scripts/prueba_pipeline.py`, que ejecuta Claude y no
    puede leer el partido. `None` nunca significa «usa games.asset_paths()».
    """
    n = len(trk.bx)
    score, allowed = no_evidence(n)
    mask = dead_mask(paths, game)
    if len(mask) != n:
        raise ValueError("la máscara de D tiene {} frames y el tracking {}".format(len(mask), n))
    allowed[mask, H] = False
    allowed[mask, A] = False  # ni H ni A: solo D
    return score, allowed
