"""Detector de balón muerto (`D`): fronteras y anclas de cada parada. Es la pieza del partido.

Capas, en el orden de docs/decisiones.md (14/11, «fronteras y anclas»):

- **Tramo antes del saque de cada parte** (v1): en la 2ª parte son los 2.934 frames que van del primer
  frame evaluado (110.808) al saque (113.742), todos `D` según FAQ.md. En la 1ª parte el primer frame
  evaluado ya es el saque, así que no hay tramo. Los frames de saque son los que publica FAQ.md, tal como
  los guarda el código oficial (starter/load_smart_tagging.py). No se fechan con el balón del ATD: con la
  regla probada (balón quieto en el centro que empieza a moverse) no se encontró el golpeo en ninguno de
  los 6 saques iniciales.
- **De cada gol a su saque:** desde el fin de la ventana `GOALS` del Smart Tagging hasta el inicio de la
  ventana de su `Kick Off (After Goal)`. Entre el gol y el saque el balón está muerto por reglamento, así
  que ese tramo es todo `D` si se cumplen tres cosas, las tres **[sin verificar]**: que la ventana `GOALS`
  acaba con el balón ya en la portería, que la del saque empieza en el reinicio o antes, y que cada `GOALS`
  es un gol válido (el Smart Tagging es automático). Si falla cualquiera de las tres, se fuerza `D` en
  juego. Si se cumplen, lo único que se pierde es el `D` entre el gol y el fin de su ventana, que no se
  ancla y decide el decodificador.
- **El hueco sin balón antes de cada reinicio** (idea de Ismael): puntuación blanda de `D` desde que se
  pierde el balón hasta el inicio de la ventana `SET PIECES`.

**En `evidence` van la primera** (un ancla dura: en esos frames solo se permite `D`) **y la tercera**
(GAP_SCORE en la columna `D`, sin ajustar), que pasó la regla apuntada en docs/decisiones.md antes de
medirla (`validation/partido/agregados_dead_ball.py`, ejecutado por Manuel el 15/11). De gol a saque está
programada y probada, pero no entra: con el Smart Tagging de este partido no ancla ningún gol (las ventanas
`GOALS` parecen llegar hasta el saque [inferencia]).

Lo que se probó y lo que se midió está en docs/decisiones.md y en validation/resultados/
(2026-11-12_balon_muerto_atd.md y 2026-11-13_revision_balon_muerto.md).
"""

import xml.etree.ElementTree as ET

import numpy as np

import games
from possession.tracking import A, D, H, no_evidence
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
    """Máscara de `D` de 199.319 posiciones, indexada por frame de vídeo.

    Recibe las rutas de games.asset_paths() por la interfaz común del pipeline, aunque esta versión no
    lee ningún fichero. De gol a saque no entra aquí: no pasó su regla el 15/11 (docs/decisiones.md).
    """
    return pre_kickoff(game)


def spans_mask(spans, n):
    """Máscara de `n` posiciones con True en los tramos (inicio, fin), con el fin sin incluir, recortados a
    [0, n)."""
    mask = np.zeros(n, dtype=bool)
    for start, stop in spans:
        mask[max(start, 0):max(min(stop, n), 0)] = True
    return mask


def goal_to_kickoff_mask(paths, game=games.GAME):
    """Máscara de los tramos de cada gol a su saque, que salen del Smart Tagging de `paths`.

    Medida y fuera de dead_mask y de `evidence`: en este partido no ancla ningún gol (15/11).
    validation/partido/agregados_dead_ball.py mide los mismos tramos con spans_mask(goal_to_kickoff(...)).
    """
    fps = games.GAMES[game]["fps"]
    events = smart_tagging_events(paths["smart_tagging"], fps)
    return spans_mask(goal_to_kickoff(events, fps), games.GAMES[game]["n_video_frames"])


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
    aún no ha empezado. El tramo no se ancla:
    - si otro `GOALS` u otro `SET PIECES` empieza entre los dos, con los extremos incluidos (un gol sin su
      saque, un gol falso, un reinicio por medio o un saque repetido harían que el tramo tapara juego);
    - si otro `GOALS` se solapa con el tramo, aunque empiece antes (dos ventanas `GOALS` que se pisan no
      pueden ser dos goles de verdad);
    - si el saque llega más de MAX_GOAL_TO_KICKOFF_S después del fin del gol.
    Así cada gol y cada saque entran, como mucho, en un tramo.
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
        others = [e for e in restarts if e is not goal and e is not kickoff]
        if any(start <= e["start"] <= stop for e in others):
            continue
        if any(e["code"] == GOALS_CODE and e["start"] < stop and e["end"] > start for e in others):
            continue
        spans.append((start, stop))
    return spans


# -- El hueco sin balón antes de cada reinicio (idea de Ismael, 14/11). En `evidence` desde el 15/11.

# Sin balón en los LONG_GAP_S segundos antes del inicio de la ventana: es el umbral de los huecos largos del
# perfil del ATD (validation/resultados/2026-11-14_perfil_atd.md). Un hueco de más de
# MAX_GAP_BEFORE_RESTART_S no cuenta: sería una parada larga (una lesión) o juego sin balón, y la capa no
# sabe distinguirlos. Los dos, fijados antes de medir (docs/decisiones.md, 14/11).
LONG_GAP_S = 5
MAX_GAP_BEFORE_RESTART_S = 60
# Puntuación de `D` por frame de hueco. Sin ajustar: la misma escala que el +1 del jugador más cercano
# (candidates.NEAREST_SCORE); la escala la decide David con los costes del decodificador.
GAP_SCORE = 1.0
# Estado de cada ventana frente a la capa.
GAP = "hueco"                       # hay hueco y se puntúa
BALL_SEEN = "balón visto"           # se ve el balón en los LONG_GAP_S segundos previos
GAP_TOO_LONG = "hueco largo"        # el hueco pasa de MAX_GAP_BEFORE_RESTART_S
RESTART_INSIDE = "reinicio dentro"  # otro GOALS o SET PIECES empieza dentro del hueco
GAP_STATES = (GAP, BALL_SEEN, GAP_TOO_LONG, RESTART_INSIDE)


def restart_windows(events):
    """Ventanas `SET PIECES` que no son saques iniciales. Antes de un saque inicial ya hay otras capas: el
    tramo antes del saque de cada parte y el de cada gol a su saque."""
    return [e for e in events if e["code"] == SET_PIECES_CODE and not e["type"].startswith("kick off")]


def last_seen_before(bx, by):
    """Para cada frame i, el último frame <= i con el balón visto (x e y); -1 si todavía no se ha visto."""
    seen = ~np.isnan(bx) & ~np.isnan(by)
    return np.maximum.accumulate(np.where(seen, np.arange(len(bx)), -1))


def gap_before(last_seen, start, restart_starts, fps):
    """(estado, inicio del hueco) de un reinicio cuya ventana empieza en el frame `start`.

    El hueco son los frames [inicio, start), todos sin balón; el frame inicio − 1 tiene balón, o inicio es 0.
    El inicio es None salvo con el estado GAP. `restart_starts` son los inicios de los demás `GOALS` y
    `SET PIECES`: si alguno cae dentro del hueco, con los extremos incluidos, el hueco no es de este reinicio.
    """
    if not 0 < start <= len(last_seen):
        # Sin el frame: el mensaje se puede pegar a Claude (CLAUDE.md, regla nº 1).
        raise ValueError("el inicio de la ventana cae fuera del tracking ({} frames)".format(len(last_seen)))
    gap_start = int(last_seen[start - 1]) + 1
    length = start - gap_start
    if length < LONG_GAP_S * fps:
        return BALL_SEEN, None
    if length > MAX_GAP_BEFORE_RESTART_S * fps:
        return GAP_TOO_LONG, None
    if any(gap_start <= s <= start for s in restart_starts):
        return RESTART_INSIDE, None
    return GAP, gap_start


def gaps_before_restarts(bx, by, events, fps):
    """[(ventana, estado, tramo)] para cada ventana de restart_windows(events), en su orden.

    `tramo` es (inicio, fin), con el fin sin incluir y igual al inicio de la ventana, solo con el estado GAP;
    si no, None. Las ventanas que empiezan fuera del tracking no entran.
    """
    last_seen = last_seen_before(bx, by)
    restarts = [e for e in events if e["code"] in (GOALS_CODE, SET_PIECES_CODE)]
    out = []
    for window in restart_windows(events):
        if not 0 < window["start"] <= len(bx):
            continue
        others = [e["start"] for e in restarts if e is not window]
        state, gap_start = gap_before(last_seen, window["start"], others, fps)
        out.append((window, state, None if gap_start is None else (gap_start, window["start"])))
    return out


def evidence(trk, paths=None, game=games.GAME):
    """Lo que este módulo aporta al pipeline, con la interfaz común: `(score, allowed)`, de forma (n, 3).

    Columnas en el orden `H`, `A`, `D` (possession/tracking.py). En los frames de `dead_mask` solo se
    permite `D`. Con `paths`, además, suma GAP_SCORE en la columna `D` en el hueco sin balón antes de cada
    reinicio cuya ventana empieza en un tramo evaluado (gaps_before_restarts; las mismas ventanas que midió
    validation/partido/agregados_dead_ball.py), con el balón de `trk`, que el pipeline ya ha limpiado. No
    prohíbe nada más.

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
    if paths is not None:
        fps = games.GAMES[game]["fps"]
        events = smart_tagging_events(paths["smart_tagging"], fps)
        for window, _, span in gaps_before_restarts(trk.bx, trk.by, events, fps):
            # Solo las ventanas que empiezan en un tramo evaluado: las mismas que se midieron.
            if span is not None and any(first <= window["start"] < stop for first, stop in trk.blocks):
                score[span[0]:span[1], D] += GAP_SCORE
    return score, allowed
