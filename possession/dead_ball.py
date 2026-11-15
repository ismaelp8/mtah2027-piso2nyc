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
- **El instante del reinicio** (15/11): ancla blanda del fin del `D` de cada ventana `SET PIECES`, en un
  desfase fijo desde su inicio, por tipo, con dos candidatos (alargar el `D` del hueco hasta el instante,
  o empujar a los dos lados del instante). Medida el 15/11 con su regla: no entra ninguno, porque ningún tipo
  de reinicio tiene un instante fijo (docs/decisiones.md, 15/11, «el instante del reinicio»). Queda fuera de
  `evidence`, programada y probada, para una repetición.
- **El juego vivo en el saque de cada parte** (tarea 4 del plan, 15/11): en el frame del saque no se permite
  `D`, porque desde ese frame el balón está en juego. Son los mismos frames de saque que el tramo antes del
  saque, así que las dos anclas se tocan sin pisarse: el tramo acaba en el frame anterior.
- **D7, el balón visto fuera del campo** (Ismael, 15/11; la tarea 2 del plan): `ball_out` y `ball_out_hold`,
  dos capas que `evidence` no llama. Se probaron con sus reglas y se quedaron apagadas (docs/decisiones.md,
  15/11, «D7»). Desde el 16/11, `ball_out` va en la entrega (`pipeline.DELIVERY_LAYERS`), por decisión de
  Ismael (docs/decisiones.md, 16/11, «se enciende la capa del balón fuera»); `ball_out_hold` sigue apagada.

**En `evidence` van la primera y la del saque** (anclas duras: en el tramo antes del saque solo se permite `D`,
y en el frame del saque, `D` no) **y la tercera** (GAP_SCORE en la columna `D`, sin ajustar), que pasó la regla
apuntada en docs/decisiones.md antes de medirla (`validation/partido/agregados_dead_ball.py`, ejecutado por
Manuel el 15/11). La del saque entra solo si pasa su propia regla, escrita antes de regenerar la entrega y
pendiente de ejecutar (docs/decisiones.md, 15/11, «juego vivo en el saque»;
`validation/partido/agregados_saque_juego_vivo.py`): esta rama no se mergea hasta aplicarla. De
gol a saque está programada y probada, pero no entra: con el Smart Tagging de este partido no ancla ningún gol
(las ventanas `GOALS` parecen llegar hasta el saque [inferencia]).

Lo que se probó y lo que se midió está en docs/decisiones.md y en validation/resultados/
(2026-11-12_balon_muerto_atd.md, 2026-11-13_revision_balon_muerto.md, 2026-11-14_agregados_balon_muerto.md
y 2026-11-15_agregados_dead_ball.md).
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


def kickoff_mask(game=games.GAME):
    """Máscara con el frame del saque de cada parte, donde el balón ya está en juego: los de FAQ.md
    (KICKOFF_VIDEO_FRAMES), solo los que caen en un tramo evaluado."""
    if game != KICKOFF_GAME:
        raise ValueError("los frames de saque solo son de {}, no de {}".format(KICKOFF_GAME, game))
    mask = np.zeros(games.GAMES[game]["n_video_frames"], dtype=bool)
    for half, first, last in games.half_video_blocks(game):
        kickoff = KICKOFF_VIDEO_FRAMES[HALF_NAMES[half]]
        if first <= kickoff <= last:
            mask[kickoff] = True
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
# perfil del ATD (validation/resultados/2026-11-14_perfil_atd.md), que es de este partido pero sin
# etiquetas. Un hueco de más de MAX_GAP_BEFORE_RESTART_S no cuenta: sería una parada larga (una lesión) o
# juego sin balón, y la capa no sabe distinguirlos; ese valor es a priori. Los dos, sin ajustar y fijados
# antes de medir (docs/decisiones.md, 14/11).
LONG_GAP_S = 5
MAX_GAP_BEFORE_RESTART_S = 60
# Puntuación de `D` por frame de hueco. Sin ajustar: la misma escala que el +1 del jugador más cercano
# (candidates.NEAREST_SCORE). Queda fija por la regla del 15/11: nadie puede medirla, porque la capa no
# corre en la DFL y el harness usa el `D` oráculo. Si cambian `to_dead` o `from_dead` cambia su efecto: hay
# que regenerar la entrega y mirar el % de `D` y las paradas.
GAP_SCORE = 1.0
# Estado de cada ventana frente a la capa.
GAP = "hueco"                       # hay hueco y se puntúa
BALL_SEEN = "balón visto"           # se ve el balón en los LONG_GAP_S segundos previos
GAP_TOO_LONG = "hueco largo"        # el hueco pasa de MAX_GAP_BEFORE_RESTART_S
RESTART_INSIDE = "reinicio dentro"  # otro GOALS o SET PIECES empieza dentro del hueco
GAP_STATES = (GAP, BALL_SEEN, GAP_TOO_LONG, RESTART_INSIDE)


def restart_windows(events):
    """Ventanas `SET PIECES` que no son saques iniciales. Los saques iniciales quedaron fuera de la regla
    fijada antes de medir: antes del de cada parte ya está el tramo antes del saque. Los de después de un
    gol, como de gol a saque no ancla, se quedan sin capa de esta pieza (docs/decisiones.md, 15/11)."""
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
    permite `D`, y en el frame del saque de cada parte (`kickoff_mask`), `D` no. Con `paths`, además, suma
    GAP_SCORE en la columna `D` en el hueco sin balón antes de cada
    reinicio cuya ventana empieza en un tramo evaluado (gaps_before_restarts; las mismas ventanas que midió
    validation/partido/agregados_dead_ball.py), con el balón de `trk`, que el pipeline ya ha limpiado. No
    prohíbe nada más.

    Es la pieza del partido: usa las constantes de saque y los ficheros de `paths`
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
    allowed[kickoff_mask(game), D] = False  # en el saque el balón ya está en juego (no choca: el tramo acaba antes)
    if paths is not None:
        fps = games.GAMES[game]["fps"]
        events = smart_tagging_events(paths["smart_tagging"], fps)
        for window, _, span in gaps_before_restarts(trk.bx, trk.by, events, fps):
            # Solo las ventanas que empiezan en un tramo evaluado: las mismas que se midieron.
            if span is not None and any(first <= window["start"] < stop for first, stop in trk.blocks):
                score[span[0]:span[1], D] += GAP_SCORE
    return score, allowed


# -- D7: el balón visto fuera del campo (15/11). ENCENDIDA desde el 16/11 en `pipeline.DELIVERY_LAYERS` ------
# (docs/decisiones.md, 16/11, «se enciende la capa del balón fuera»). No la llama `evidence`: la suma la entrega,
# así que no corre en el harness. Reglas, peso y criterios, fijados antes de generar la primera entrega de
# prueba: docs/decisiones.md, 15/11, «D7». Las cuatro constantes van sin ajustar: se fijaron antes de medir y
# no se han tocado después.

BALL_OUT_MARGIN = 1.0  # m fuera de las líneas (docs/PLAN_ENTREGA.md §3, tarea 2 de Manuel)
BALL_OUT_MIN_RUN = 5  # frames: una racha más corta es temblor (como validation/partido/balon_fuera.py)
# Frames del final de cada racha que no se puntúan: el balón del ATD va suavizado unos 25 frames (la mitad,
# 12) y llega unos 4 tarde respecto a los jugadores (PR 11), así que tras un saque de banda se sigue viendo
# fuera unos 16 frames con el juego ya en marcha.
BALL_OUT_TAIL = 16
# Puntuación de `D` por frame. El entero más grande con el que, en el juego vivo típico (mediana de
# dead_state en la DFL, −3,42), un balón visto fuera tiene que durar 3 s o más para crear una parada él solo:
# cada frame gana W + ds − 1 (el −1 es el +1 de N1) y una parada nueva cuesta to_dead + from_dead = 50.
BALL_OUT_SCORE = 5.0


def ball_out(trk):
    """`(score, allowed)` de la capa D7: BALL_OUT_SCORE en la columna `D` donde el balón se ve fuera.

    Solo en las rachas de BALL_OUT_MIN_RUN frames o más con el balón visto a más de BALL_OUT_MARGIN m fuera
    de las líneas, sin sus últimos BALL_OUT_TAIL frames y dentro de los tramos evaluados. No prohíbe nada.
    Solo usa el tracking (con el balón ya limpio), así que también corre en la DFL.
    """
    n = len(trk.bx)
    score, allowed = no_evidence(n)
    length, width = trk.pitch
    bx, by = np.asarray(trk.bx, dtype=np.float64), np.asarray(trk.by, dtype=np.float64)
    with np.errstate(invalid="ignore"):
        out = ((bx < -BALL_OUT_MARGIN) | (bx > length + BALL_OUT_MARGIN)
               | (by < -BALL_OUT_MARGIN) | (by > width + BALL_OUT_MARGIN))
    out &= np.isfinite(bx) & np.isfinite(by)
    for first, stop in trk.blocks:
        edges = np.diff(np.concatenate(([0], out[first:stop].astype(np.int8), [0])))
        for start, end in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
            if end - start >= BALL_OUT_MIN_RUN and end - start > BALL_OUT_TAIL:
                score[first + start:first + end - BALL_OUT_TAIL, D] = BALL_OUT_SCORE
    return score, allowed


# -- D7, segunda versión (15/11): mantener la parada hasta que el balón vuelva a verse dentro. APAGADA. -----
# Diseñada después de ver la primera (prueba_d7: tarde en 12 de 47 rachas, y en 7 nuestro `D` no llega).
# Ojo: con `ball_out` ya en la entrega (16/11), `--capa dead_ball.ball_out_hold` la sumaría dos veces, porque esta
# la lleva dentro. Para probarla habría que quitar antes `ball_out` de `pipeline.DELIVERY_LAYERS`. Reglas fijadas antes de generar la entrega: docs/decisiones.md,
# 15/11, «D7, segunda versión».

# Racha visible mínima para mantener la parada en el hueco que la sigue: con 1 s, en SkillCorner (mitad de
# entrenamiento) hay 0,7 rachas por partido enteras en juego, menos de una aunque todas acabaran con el balón
# perdido (validation/scripts/balon_fuera_abiertos.py).
BALL_OUT_HOLD_MIN_RUN = 25
# Tope del hueco: si el balón no vuelve a verse dentro en 60 s, no se mantiene (el de la capa del hueco).
BALL_OUT_HOLD_MAX_S = 60


def ball_out_hold(trk):
    """`(score, allowed)` de la segunda versión de D7: `ball_out` y, además, mantiene la parada en el hueco.

    Lo de `ball_out`, y en cada racha visible de BALL_OUT_HOLD_MIN_RUN frames o más con el balón fuera, sigue
    puntuando BALL_OUT_SCORE en `D` mientras el balón no se ve o se ve fuera, hasta BALL_OUT_TAIL frames antes
    de que vuelva a verse dentro (a BALL_OUT_MARGIN m o menos de las líneas). Si no vuelve a verse dentro en
    BALL_OUT_HOLD_MAX_S segundos, o se acaba el tramo, no se mantiene. No prohíbe nada.
    """
    score, allowed = ball_out(trk)
    length, width = trk.pitch
    bx, by = np.asarray(trk.bx, dtype=np.float64), np.asarray(trk.by, dtype=np.float64)
    seen = np.isfinite(bx) & np.isfinite(by)
    with np.errstate(invalid="ignore"):
        out = seen & ((bx < -BALL_OUT_MARGIN) | (bx > length + BALL_OUT_MARGIN)
                      | (by < -BALL_OUT_MARGIN) | (by > width + BALL_OUT_MARGIN))
    inside = seen & ~out
    limit = int(round(BALL_OUT_HOLD_MAX_S * trk.fps))
    for first, stop in trk.blocks:
        edges = np.diff(np.concatenate(([0], out[first:stop].astype(np.int8), [0])))
        for start, end in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
            if end - start < BALL_OUT_HOLD_MIN_RUN:
                continue
            back = np.flatnonzero(inside[first + end:min(first + end + limit + 1, stop)])
            if not len(back):
                continue
            hold_end = first + end + int(back[0]) - BALL_OUT_TAIL
            if hold_end > first + start:
                score[first + start:hold_end, D] = BALL_OUT_SCORE
    return score, allowed


# -- El instante del reinicio (15/11). Medido con su regla el 15/11: no entra ninguno. Fuera de `evidence`.

# La capa lleva el fin del `D` de cada ventana `SET PIECES` a un instante fijo desde su inicio, uno por tipo de
# reinicio, que sale de validation/partido/agregados_instante_reinicio.py con la regla de docs/decisiones.md
# (15/11, «el instante del reinicio»). Hay dos candidatos, y la regla decide cuál entra, o ninguno:
# - BRIDGE (el candidato 1, «B»): solo en las ventanas con hueco (las que puntúa la capa del hueco),
#   +ANCHOR_SCORE en `D` desde el inicio de la ventana hasta el instante. Alarga el `D` del hueco.
# - BOTH_SIDES (el candidato 2, «A»): en todas las ventanas del tipo. En las que tienen hueco, lo mismo que
#   BRIDGE; en las demás, el empuje a `D` no empieza en el inicio de la ventana, sino PUSH_BEFORE_S antes del
#   instante. Y en todas, −ANCHOR_SCORE en `D` durante los PUSH_AFTER_S siguientes.
# Blandos y cortos, para que un instante mal puesto cueste poco: la escala que tenía GAP_SCORE el 15/11 (1 por
# frame) y nada prohibido. Sin ajustar y fijos por la regla: la capa no corre en la DFL, así que nadie puede medir su
# escala.
ANCHOR_SCORE = 1.0  # la escala de GAP_SCORE el 15/11; fijada por la regla: si cambia GAP_SCORE, esta no cambia
PUSH_BEFORE_S = 3
PUSH_AFTER_S = 3
BRIDGE, BOTH_SIDES = "B", "A"


def next_restart(events, window):
    """Inicio del siguiente `GOALS` o `SET PIECES` de cualquier tipo, contando los que empiezan en el mismo
    frame que `window` (sin contarla a ella); np.inf si no hay ninguno."""
    return min([e["start"] for e in events if e["code"] in (GOALS_CODE, SET_PIECES_CODE)
                and e is not window and e["start"] >= window["start"]] + [np.inf])


def restart_anchor_spans(events, anchors, blocks):
    """[(ventana, inicio, instante, corte)] para las ventanas de restart_windows(events) (nunca los saques
    iniciales) cuyo tipo tiene ancla y que empiezan en un tramo evaluado (`blocks`, con el fin sin incluir).
    `anchors` es {tipo: frames desde el inicio de la ventana}.

    El instante es inicio + anchors[tipo]. El corte es el inicio del siguiente `GOALS` o `SET PIECES`, de
    cualquier tipo (next_restart); si el instante no cae antes de él, la ventana no entra."""
    spans = []
    for window in restart_windows(events):
        start = window["start"]
        if window["type"] not in anchors or not any(first <= start < stop for first, stop in blocks):
            continue
        cut = next_restart(events, window)
        instant = start + int(anchors[window["type"]])
        if not start <= instant < cut:
            continue
        spans.append((window, start, instant, cut))
    return spans


def restart_anchor_pushes(bx, by, events, anchors, modes, blocks, fps):
    """[(ventana, con hueco, desde, instante, hasta)] de la capa: +ANCHOR_SCORE en `D` en [desde, instante) y
    −ANCHOR_SCORE en [instante, hasta), que con BRIDGE está vacío.

    `modes` es {tipo: BRIDGE o BOTH_SIDES}; un tipo con ancla y sin modo no entra. «Con hueco» es que la capa
    del hueco puntúa esa ventana (gaps_before_restarts, con el balón `bx`, `by`). El empuje después del
    instante se corta en el siguiente reinicio."""
    unknown = set(modes.values()) - {BRIDGE, BOTH_SIDES}
    if unknown:
        raise ValueError("modos desconocidos: {}".format(sorted(unknown)))
    gap_windows = [w for w, _, span in gaps_before_restarts(bx, by, events, fps) if span is not None]
    pushes = []
    for window, start, instant, cut in restart_anchor_spans(events, anchors, blocks):
        mode = modes.get(window["type"])
        has_gap = any(w is window for w in gap_windows)
        if mode is None or (mode == BRIDGE and not has_gap):
            continue
        first = start if has_gap else max(start, instant - PUSH_BEFORE_S * fps)
        stop = int(min(instant + PUSH_AFTER_S * fps, cut)) if mode == BOTH_SIDES else instant
        pushes.append((window, has_gap, first, instant, stop))
    return pushes


def restart_anchor_evidence(trk, events, anchors, modes):
    """`(score, allowed)` de la capa, con los tramos de restart_anchor_pushes. No prohíbe nada."""
    n = len(trk.bx)
    score, allowed = no_evidence(n)
    for _, _, first, instant, stop in restart_anchor_pushes(trk.bx, trk.by, events, anchors, modes, trk.blocks,
                                                             trk.fps):
        score[max(first, 0):max(min(instant, n), 0), D] += ANCHOR_SCORE
        score[max(instant, 0):max(min(stop, n), 0), D] -= ANCHOR_SCORE
    return score, allowed
