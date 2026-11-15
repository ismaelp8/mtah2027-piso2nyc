"""Agregados del partido para el instante del reinicio (possession/dead_ball.py). Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: recuentos, cuantiles y desfases desde el inicio de cada ventana, sin números de
frame ni jugadas sueltas. Los recuentos de ventanas por debajo de 5 se tapan con «< 5», como en el perfil
del ATD.

    python validation/partido/agregados_instante_reinicio.py

Responde, con la regla apuntada en docs/decisiones.md (15/11, «el instante del reinicio») antes de
ejecutarlo y sus cambios posteriores:
1. Dónde cae el reinicio dentro de cada ventana `SET PIECES` (no los saques iniciales), con dos señales
   que no son etiquetas: cuándo vuelve a verse el balón, si no se veía al empezar la ventana, y cuándo el
   modelo de jugadores de Ana pasa de parado a juego. Contado desde el inicio de la ventana; las ventanas
   duran lo mismo, así que desde el fin es restar esa duración.
2. La regla: qué tipos tienen un sitio fijo con poca dispersión, y su ancla.
3. Con esas anclas, los dos candidatos de la capa (dead_ball.BOTH_SIDES, «A», y dead_ball.BRIDGE, «B»):
   las condiciones de A, y cada candidato en el pipeline, sin la capa y con ella, con su condición de daño.
   Entra A si cumple todo; si no, B si cumple lo suyo; si no, ninguno.
4. Para la capa del hueco (PR #8), los agregados de la tarea 3 del plan: de los frames que cambian de
   etiqueta con ella, cuántos caen en los primeros 5 s de cada hueco, y un histograma grueso de la
   distancia entre el inicio de cada hueco y el inicio del D que sale del decodificador.

**Cambios a la regla para cualquier repetición** (decisión de Ana, 15/11; docs/decisiones.md, misma entrada,
«Cambios a la regla después de la ejecución del 15/11»). La ejecución del 15/11 no los llevaba:
1. (añadido de Ana) el script dice cuántos frames tiene el control de juego y, si son menos del 5 % de lo
   evaluado, A no se cumple;
2. (añadido de Ana) el ancla de la capa es la mediana de la transición menos el retraso de esa transición medido
   en la DFL (DFL_DELAY). El recorrido, «nítido», la coincidencia con el balón y «la mediana gana» siguen con la
   mediana sin corregir;
3. (decidido después de ver la salida del 15/11) el control de juego no incluye el tramo antes del saque de la 2ª
   parte, que es el control de D.

Corre el pipeline como la entrega (pipeline.build): con dead_ball.evidence y las demás capas de la entrega
(pipeline.DELIVERY_LAYERS), y lee el ATD como él. Imprime las versiones y el commit.

`measure_instant` y las funciones de la regla no abren ningún fichero; los importa
validation/scripts/comprobar_balon_muerto.py (sección 11), que ejecuta Claude con un partido inventado y
con la apertura de ficheros prohibida. Por eso **nada fuera de `main` puede abrir un fichero.**
"""

import hashlib
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
import agregados_dead_ball as agg  # noqa: E402  (dead_share, ball_speed y FAST_BALL_MS: el punto medio)
from comun import MIN_CASES_PER_TYPE, bins_s, graded_mask, utf8_stdout  # noqa: E402
from possession import dead_ball, dead_state, pipeline, temporal, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
# Todo fijado antes de medir (docs/decisiones.md, 15/11).
SUSTAIN_S = 2  # el modelo de Ana pasa a juego si ve juego (log-odds < 0) 2 s seguidos
SEARCH_AFTER_S = 10  # las señales se buscan hasta 10 s después del fin de la ventana (sin pasar del siguiente)
MIN_WINDOWS = 10  # un tipo tiene ancla solo con 10 ventanas o más con la transición del modelo de Ana
MAX_IQR_S = 2.0  # si el recorrido intercuartílico de esa transición es de 2 s o menos
MIN_BALL = 5  # con 5 ventanas o más en las que vuelve a verse el balón (y 5 o más con las dos señales)
MAX_AGREE_S = 1.0  # si la mediana de esa reaparición queda a 1 s o menos de la de la transición
NEAR_S = 1.0  # descriptivo: salidas del D a 1 s o menos del instante anclado
FIRST_SECONDS_S = 5  # sección 4: los primeros 5 s de cada hueco
OFF_DURATION_S = 1.0  # descriptivo: ventanas cuya duración se aparta más de 1 s de la mediana
# El placebo: las mismas ventanas desplazadas 4, 6 y 8 minutos, como el de la capa del hueco
# (agregados_dead_ball.PLACEBO_SHIFTS_S), lejos de cualquier reinicio real.
PLACEBO_SHIFTS_S = (-480, -360, -240, 240, 360, 480)
# La banda de la entrega (docs/PLAN_ENTREGA.md §3, 15/11): del 15 al 60 % de D y 250 paradas como mucho.
BAND_D = (0.15, 0.60)
MAX_STOPS = 250
GAP_D_EDGES_S = (0, 1, 3, 5)  # sección 4: intervalos del inicio del D desde el inicio del hueco
# El candidato A (mensaje de Ismael del 15/11) solo entra en un tipo si además:
# 1. el instante es nítido: el 80 % de las ventanas del tipo (también las que no tienen transición) tiene la
#    transición a menos de 1 s de la mediana del tipo;
SHARP_S = 1.0
SHARP_NUM, SHARP_DEN = 4, 5  # el 80 %, en enteros para que la frontera no dependa de la coma flotante
# 2. el modelo de Ana está de acuerdo a los dos lados del instante (dead_ball.PUSH_BEFORE_S antes y
#    dead_ball.PUSH_AFTER_S después), con el criterio del punto medio de la capa del hueco, por separado en
#    las ventanas con hueco y en las demás, con 5 ventanas o más en cada grupo. El control de D es el tramo
#    antes del saque de la 2ª parte (D según el FAQ); el de juego, los frames evaluados a más de PLAY_FAR_S de
#    cualquier GOALS o SET PIECES, el mismo horizonte que dead_ball.MAX_GAP_BEFORE_RESTART_S, sin el control de D
#    (esto último es el cambio 3, decidido después de ver la salida del 15/11, que lo incluía). El balón
#    deprisa no vale: no separa D de juego en este partido (docs/decisiones.md, 15/11, «fronteras»);
# 3. el placebo (los mismos instantes en las ventanas desplazadas, todas juntas y 5 o más) no pasa el
#    punto medio del punto 2.
PLAY_FAR_S = 60
# Los añadidos de Ana (cambios 1 y 2; pedidos para antes de ejecutar, llegaron después de la ejecución del 15/11;
# valen para cualquier repetición):
# - el control de juego tiene que tener por lo menos el 5 % de los frames evaluados; si no, el instrumento no
#   separa y A no se cumple. En enteros, para que la frontera no dependa de la coma flotante;
PLAY_MIN_NUM, PLAY_MIN_DEN = 1, 20
# - el ancla es la mediana de la transición menos su retraso mediano en la DFL, en frames, medido por Ana con
#   validation/scripts/d_estado/retraso_transicion.py: solo los tipos con 50 paradas o más en la DFL y la transición
#   tarde (mediana positiva). Las faltas y los saques de puerta pasan de 50 paradas, pero su mediana es negativa (la
#   transición llega antes del fin real): no es un retraso y no se corrigen. Es un número de la DFL, no del partido.
DFL_DELAY = {"throw-in": 20, "corner kick": 16}
GAP_GROUP, OTHER_GROUP = "con hueco", "sin hueco"
BACK, SEEN_AT_START, NOT_BACK = "vuelve a verse", "visto al empezar", "no vuelve"


def cases(k):
    """Un recuento de ventanas para imprimir: «< 5» si es menor que 5, también el 0."""
    return "< 5" if k < MIN_CASES_PER_TYPE else str(k)


def model_fingerprint(model):
    """Huella corta del modelo de Ana (dead_state.MODEL), para saber con cuál se midió."""
    return hashlib.sha256(json.dumps(model, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def code_fingerprint(folder):
    """Huella corta del código de `folder` (los .py, en orden y con los finales de línea de Unix), para
    saber con qué pipeline se midió. Solo lee código del repo, nunca datos."""
    digest = hashlib.sha256()
    for name in sorted(f for f in os.listdir(folder) if f.endswith(".py")):
        with open(os.path.join(folder, name), "rb") as handle:
            digest.update(name.encode("utf-8") + b"\0" + handle.read().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()[:12]


def search_stop(window, cut, fps):
    """Fin, sin incluir, de la búsqueda de las señales en una ventana: SEARCH_AFTER_S después de su fin, sin
    pasar de `cut` (el inicio del siguiente reinicio, dead_ball.next_restart)."""
    return int(min(cut, window["end"] + SEARCH_AFTER_S * fps))


def harm_stop(window, cut, layer_stop, fps):
    """Fin, sin incluir, del tramo en que se cuentan los D de una ventana con ancla: SEARCH_AFTER_S después del
    fin de la ventana o del de la capa (`layer_stop`), lo que llegue más tarde, sin pasar de `cut`."""
    return int(min(cut, max(window["end"], layer_stop) + SEARCH_AFTER_S * fps))


def placebo_windows(events, blocks, fps):
    """Las ventanas de restart_windows(events) que empiezan en un tramo evaluado, desplazadas PLACEBO_SHIFTS_S,
    con su tipo y su duración. Solo las que empiezan en un tramo evaluado y no tienen ningún `GOALS` ni
    `SET PIECES` real (de cualquier tipo) a menos de su duración más SEARCH_AFTER_S, antes o después: así
    su búsqueda no ve ningún reinicio de verdad."""
    restarts = [e["start"] for e in events if e["code"] in (dead_ball.GOALS_CODE, dead_ball.SET_PIECES_CODE)]
    out = []
    for w in dead_ball.restart_windows(events):
        if not any(first <= w["start"] < stop for first, stop in blocks):
            continue
        clear = (w["end"] - w["start"]) + SEARCH_AFTER_S * fps
        for shift in PLACEBO_SHIFTS_S:
            start = w["start"] + shift * fps
            if (any(first <= start < stop for first, stop in blocks)
                    and not any(abs(r - start) < clear for r in restarts)):
                out.append(dict(w, start=start, end=w["end"] + shift * fps))
    return out


def tight(transitions, fps):
    """10 transiciones o más con recorrido intercuartílico de 2 s o menos (en frames)."""
    return bool(len(transitions) >= MIN_WINDOWS and spread(transitions)[5] <= MAX_IQR_S * fps)


def band_ok(dead_share, stops):
    """La entrega dentro de la banda del plan: del 15 al 60 % de D en lo evaluado y 250 paradas como mucho."""
    return BAND_D[0] <= dead_share <= BAND_D[1] and stops <= MAX_STOPS


def gap_d_offsets(codes, spans):
    """Para cada hueco [g0, g1): frames desde g0 hasta el inicio del tramo de D de `codes` que lo toca
    primero (negativo si ese D ya venía de antes del hueco); None si ningún D toca el hueco."""
    out = []
    for g0, g1 in spans:
        dead = np.flatnonzero(codes[g0:g1] == D)
        if dead.size == 0:
            out.append(None)
            continue
        first = g0 + int(dead[0])
        while first > 0 and codes[first - 1] == D:
            first -= 1
        out.append(first - g0)
    return out


def play_transition(odds, start, stop, sustain):
    """Primer frame f en [start, stop) en que el modelo de Ana pasa de parado a juego: log-odds > 0 en f − 1
    y < 0 en los `sustain` frames desde f (que pueden pasar de `stop`). None si no hay."""
    negative = odds < 0
    for f in range(max(start, 1), min(stop, len(odds) - sustain + 1)):
        if odds[f - 1] > 0 and negative[f:f + sustain].all():
            return f
    return None


def ball_back(seen, start, stop):
    """(estado, frame): si el balón no se veía en el frame anterior al inicio de la ventana, el primero en
    [start, stop) en que vuelve a verse (BACK) o (NOT_BACK, None); si se veía, (SEEN_AT_START, None)."""
    if start > 0 and seen[start - 1]:
        return SEEN_AT_START, None
    back = np.flatnonzero(seen[start:stop])
    return (BACK, start + int(back[0])) if back.size else (NOT_BACK, None)


def spread(values):
    """(p10, p25, p50, p75, p90, recorrido intercuartílico) de una lista no vacía."""
    p10, p25, p50, p75, p90 = np.percentile(values, (10, 25, 50, 75, 90))
    return p10, p25, p50, p75, p90, p75 - p25


def anchor_of(transitions):
    """La mediana de la transición de un tipo, en frames desde el inicio de la ventana. Con ella se calcula «la
    mediana gana» (anchor_rule); el ancla de la capa es layer_anchor."""
    return int(round(float(np.median(transitions))))


def layer_anchor(kind, transitions, delays):
    """El ancla de la capa (añadido de Ana): la mediana de la transición menos el retraso del tipo en la DFL
    (`delays`, en frames; un tipo que no está no se corrige)."""
    return anchor_of(transitions) - int(delays.get(kind, 0))


def enough_play(play_frames, graded_frames):
    """El control de juego tiene por lo menos el 5 % de los frames evaluados (añadido de Ana)."""
    return play_frames * PLAY_MIN_DEN >= PLAY_MIN_NUM * graded_frames


def anchor_rule(transitions, ball, pairs, fps):
    """La regla de un tipo. Recibe desfases en frames desde el inicio de la ventana: los de la transición del
    modelo de Ana, los de la reaparición del balón y, en las ventanas con las dos, los pares (transición,
    balón). Se compara en frames, para que una frontera exacta (25 o 50 frames) no falle por la coma flotante.
    Devuelve (enough, tight, agree, beats, entra)."""
    enough = len(transitions) >= MIN_WINDOWS
    tight = bool(enough and spread(transitions)[5] <= MAX_IQR_S * fps)
    agree = bool(enough and len(ball) >= MIN_BALL
                 and abs(float(np.median(ball)) - float(np.median(transitions))) <= MAX_AGREE_S * fps)
    beats = False
    if enough and len(pairs) >= MIN_BALL:
        anchor = anchor_of(transitions)
        fixed = float(np.median([abs(b - anchor) for _, b in pairs]))
        own = float(np.median([abs(b - t) for t, b in pairs]))
        beats = fixed < own
    return enough, tight, agree, beats, enough and tight and agree and beats


def sharp_count(transitions, fps):
    """Cuántas transiciones caen a menos de SHARP_S de su mediana."""
    if not transitions:
        return 0
    median = float(np.median(transitions))
    return int(sum(abs(t - median) < SHARP_S * fps for t in transitions))


def sharp(transitions, n_windows, fps):
    """El instante es nítido: 10 ventanas o más, y el 80 % de las `n_windows` ventanas del tipo (las que no
    tienen transición cuentan como lejos) con la transición a menos de SHARP_S de la mediana."""
    return bool(n_windows >= MIN_WINDOWS and sharp_count(transitions, fps) * SHARP_DEN >= SHARP_NUM * n_windows)


def side_shares(odds, instants, n, fps):
    """(antes, después): proporción de D del modelo de Ana (agg.dead_share) en los PUSH_BEFORE_S anteriores a
    cada instante y en los PUSH_AFTER_S siguientes, juntando todos los frames de las ventanas."""
    before, after = np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)
    for i in instants:
        before[max(i - dead_ball.PUSH_BEFORE_S * fps, 0):max(min(i, n), 0)] = True
        after[max(i, 0):max(min(i + dead_ball.PUSH_AFTER_S * fps, n), 0)] = True
    return agg.dead_share(odds, before), agg.dead_share(odds, after)


def ana_agrees(before, after, g_match, g_dead, g_play):
    """El modelo de Ana ve parado antes del instante y juego después, con el criterio del punto medio de la capa
    del hueco: el instrumento separa (control de D por encima del partido y control de juego por debajo),
    `before` queda en el punto medio entre el partido y el control de D o por encima, y `after` en el punto
    medio entre el partido y el control de juego o por debajo. Un NaN lo hace falso."""
    return bool(g_dead > g_match > g_play and before >= (g_match + g_dead) / 2
                and after <= (g_match + g_play) / 2)


def far_from_restarts(events, graded, fps):
    """Frames de `graded` a más de PLAY_FAR_S de cualquier ventana `GOALS` o `SET PIECES` (antes de su inicio
    o después de su fin): el control de juego del punto medio de A."""
    far = graded.copy()
    for e in events:
        if e["code"] in (dead_ball.GOALS_CODE, dead_ball.SET_PIECES_CODE):
            far[max(e["start"] - PLAY_FAR_S * fps, 0):max(e["end"] + PLAY_FAR_S * fps, 0)] = False
    return far


def a_conditions(t, kind, anchor, spans, gap_windows, shifted, odds, n, fps, controls, play_enough):
    """Las tres condiciones del candidato A en un tipo con ancla. `t` es su entrada de by_type; `anchor`, el ancla
    de la capa (layer_anchor); `spans`, los de dead_ball.restart_anchor_spans con esas anclas; `gap_windows`, las
    ventanas que puntúa la capa del hueco; `shifted`, las de placebo_windows; `controls`, las proporciones de D
    del modelo de Ana (partido, control de D, control de juego). Sin `play_enough` (enough_play), el instrumento
    no separa y A no se cumple."""
    instants = {GAP_GROUP: [], OTHER_GROUP: []}
    for window, _, instant, _ in spans:
        if window["type"] == kind:
            instants[GAP_GROUP if any(w is window for w in gap_windows) else OTHER_GROUP].append(instant)
    sides = {}
    for group, group_instants in instants.items():
        before, after = side_shares(odds, group_instants, n, fps)
        sides[group] = {"n": len(group_instants), "before": before, "after": after,
                        "ok": len(group_instants) >= MIN_CASES_PER_TYPE and ana_agrees(before, after, *controls)}
    shifted_instants = [w["start"] + anchor for w in shifted if w["type"] == kind]
    before, after = side_shares(odds, shifted_instants, n, fps)
    placebo = {"n": len(shifted_instants), "before": before, "after": after,
               "passes": ana_agrees(before, after, *controls)}
    a = {"sharp": sharp(t["transitions"], t["n"], fps), "sharp_count": sharp_count(t["transitions"], fps),
         "sides": sides, "placebo": placebo, "play_enough": bool(play_enough)}
    a["ok"] = (a["play_enough"] and a["sharp"] and all(s["ok"] for s in sides.values())
               and placebo["n"] >= MIN_CASES_PER_TYPE and not placebo["passes"])
    return a


def runs(codes, blocks):
    """(posesiones, paradas) en los tramos evaluados."""
    possessions = stops = 0
    for first, stop in blocks:
        window = codes[first:stop]
        kinds = window[np.flatnonzero(np.concatenate(([True], window[1:] != window[:-1])))]
        possessions += int(np.sum(kinds != D))
        stops += int(np.sum(kinds == D))
    return possessions, stops


def dead_runs(codes, start, stop):
    """Cuántos tramos seguidos de D hay en codes[start:stop]."""
    dead = (codes[start:stop] == D).astype(np.int8)
    return int(np.sum(np.diff(np.concatenate(([0], dead))) == 1))


def last_exit(codes, start, stop):
    """Frame en que se sale del último D de codes[start:stop] (el primero después de él); None si no hay
    ningún D o si el D llega hasta `stop`."""
    dead = np.flatnonzero(codes[start:stop] == D)
    if dead.size == 0 or start + dead[-1] + 1 >= stop:
        return None
    return start + int(dead[-1]) + 1


def worse(without, with_layer, start, stop):
    """La capa parte la parada de [start, stop): con ella hay dos tramos de D o más, y más que sin ella. Pasar
    de ninguno a uno no cuenta: es lo que la capa quiere hacer cuando alarga un D hasta el instante."""
    return dead_runs(with_layer, start, stop) > max(dead_runs(without, start, stop), 1)


def changes(without, with_layer, mask):
    """Frames de `mask` que cambian, por tipo: (de un equipo al otro, de juego a D, de D a juego)."""
    play_before, play_after = without != D, with_layer != D
    team = mask & play_before & play_after & (without != with_layer)
    to_dead = mask & play_before & ~play_after
    to_play = mask & ~play_before & play_after
    return int(team.sum()), int(to_dead.sum()), int(to_play.sum())


def harm_rule(runs_without, runs_with, split_windows):
    """Condición de daño: ninguna ventana con ancla queda partida por la capa (`split_windows`, con worse()
    en harm_stop), y las posesiones no suben más que las paradas (cada posesión
    nueva tiene que venir de una parada nueva que la parte)."""
    return split_windows == 0 and runs_with[0] - runs_without[0] <= runs_with[1] - runs_without[1]


def candidates_for(anchors, a_ok):
    """[(nombre, {tipo: modo})] en el orden en que se prueban: A (A en los tipos que lo cumplen y B en los
    demás) si algún tipo con ancla cumple A, y después B en todos los tipos con ancla. Vacía sin anclas."""
    out = []
    if any(a_ok.get(kind) for kind in anchors):
        out.append((dead_ball.BOTH_SIDES, {kind: dead_ball.BOTH_SIDES if a_ok.get(kind) else dead_ball.BRIDGE
                                           for kind in anchors}))
    if anchors:
        out.append((dead_ball.BRIDGE, {kind: dead_ball.BRIDGE for kind in anchors}))
    return out


def delivery_layers(paths, game):
    """Las capas que la entrega suma además de dead_ball.evidence (pipeline.DELIVERY_LAYERS), con las rutas del
    partido, como en pipeline.build. Así el pipeline de estas medidas es el de la entrega. No abre nada al crearlas."""
    return [pipeline.with_paths(layer, paths, game) for layer in pipeline.DELIVERY_LAYERS]


def layer_names():
    """Los nombres de pipeline.DELIVERY_LAYERS («modulo.funcion»), para imprimir con qué se midió."""
    return [layer.__module__.split(".")[-1] + "." + layer.__name__ for layer in pipeline.DELIVERY_LAYERS]


def try_layer(trk, clean, events, anchors, modes, without, conflicts_without, delivery_fn, pieces, graded, layers):
    """Un candidato en el pipeline: las cuentas de la sección 3 y si cumple su condición de daño («ok»)."""
    n, fps = len(trk.bx), trk.fps
    layer = lambda c: dead_ball.restart_anchor_evidence(c, events, anchors, modes)  # noqa: E731
    report = {}
    with_layer = pipeline.run(trk, extra=[delivery_fn, layer] + list(layers), report=report, pieces=pieces)
    pushes = dead_ball.restart_anchor_pushes(clean.bx, clean.by, events, anchors, modes, trk.blocks, fps)
    before, after = np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)
    near, split = [0, 0], 0
    for window, _, first, instant, stop in pushes:
        cut = dead_ball.next_restart(events, window)
        before[first:instant] = True
        # el «después» que se describe es el mismo tramo en los dos modos, aunque B no empuje ahí
        after[instant:int(min(instant + dead_ball.PUSH_AFTER_S * fps, cut))] = True
        end = harm_stop(window, cut, stop, fps)
        split += worse(without, with_layer, window["start"], end)
        for i, codes in enumerate((without, with_layer)):
            frame = last_exit(codes, window["start"], end)
            near[i] += frame is not None and abs(frame - instant) <= NEAR_S * fps
    r = {"pushes": len(pushes), "with_gap": sum(p[1] for p in pushes),
         "conflicts": (conflicts_without, report["conflictos"]),
         "runs": (runs(without, trk.blocks), runs(with_layer, trk.blocks)), "split": split, "near": tuple(near),
         "changed_before": changes(without, with_layer, graded & before),
         "changed_after": changes(without, with_layer, graded & after),
         "changed_outside": changes(without, with_layer, graded & ~before & ~after),
         "dead_share": (float(np.mean(without[graded] == D)), float(np.mean(with_layer[graded] == D)))}
    r["band_ok"] = band_ok(r["dead_share"][1], r["runs"][1][1])
    r["harm_ok"] = (harm_rule(r["runs"][0], r["runs"][1], split) and r["conflicts"] == (0, 0)
                    and r["band_ok"])
    r["ok"] = r["pushes"] >= 1 and r["harm_ok"]
    return r


def measure_instant(trk, events, delivery_fn, no_gap_fn, game=games.GAME, pieces=None, odds_fn=None, delays=None,
                    layers=()):
    """Las cuentas de las cuatro secciones y la regla aplicada. No abre ningún fichero por sí misma.

    `trk` es el tracking sin limpiar; `events`, los de dead_ball.smart_tagging_events. `delivery_fn` es la
    evidencia de dead_ball de la entrega (con la capa del hueco) y `no_gap_fn` la misma sin la capa del hueco;
    las dos son funciones del tracking limpio. `pieces` cambia piezas del pipeline (en el partido, None) y
    `odds_fn` el instrumento (por defecto, dead_state.log_odds, el modelo de Ana). `delays` son los retrasos que
    se restan a la mediana para el ancla de la capa (por defecto, DFL_DELAY; las pruebas de antes de los
    añadidos pasan {}). `layers` son las demás capas de la entrega (delivery_layers), que van en todas las
    ejecuciones del pipeline, como en pipeline.build.
    """
    n, fps = len(trk.bx), trk.fps
    graded = graded_mask(game, n)
    pieces = pieces or {}
    delays = DFL_DELAY if delays is None else delays
    clean = (pieces["ball"] if "ball" in pieces else pipeline.default_piece("ball"))(trk)  # como pipeline.run
    odds = (odds_fn or dead_state.log_odds)(clean)
    seen = ~np.isnan(clean.bx) & ~np.isnan(clean.by)
    windows = [w for w in dead_ball.restart_windows(events)
               if any(first <= w["start"] < stop for first, stop in trk.blocks)]
    durations = [w["end"] - w["start"] for w in windows]
    median_duration = float(np.median(durations)) if durations else 0.0
    m = {"windows": len(windows), "duration_median_s": median_duration / fps,
         "off_duration": sum(abs(d - median_duration) > OFF_DURATION_S * fps for d in durations)}

    # 1. Las dos señales, por tipo, en frames desde el inicio de la ventana
    groups = {}
    for window in windows:
        groups.setdefault(window["type"], []).append(window)
    small = sorted(kind for kind, group in groups.items() if len(group) < MIN_CASES_PER_TYPE)
    if small:
        groups["otros"] = [w for kind in small for w in groups.pop(kind)]
    by_type = {}
    for kind, group in sorted(groups.items()):
        transitions, ball, pairs, states = [], [], [], {BACK: 0, SEEN_AT_START: 0, NOT_BACK: 0}
        for w in group:
            limit = search_stop(w, dead_ball.next_restart(events, w), fps)
            t = play_transition(odds, w["start"], limit, SUSTAIN_S * fps)
            state, b = ball_back(seen, w["start"], limit)
            states[state] += 1
            if t is not None:
                transitions.append(t - w["start"])
            if b is not None:
                ball.append(b - w["start"])
            if t is not None and b is not None:
                pairs.append((t - w["start"], b - w["start"]))
        rule = anchor_rule(transitions, ball, pairs, fps) if kind != "otros" else (False,) * 5
        by_type[kind] = {"n": len(group), "transitions": transitions, "ball": ball, "pairs": pairs,
                         "states": states, "rule": rule}
    placebo = {}
    for w in placebo_windows(events, trk.blocks, fps):
        t = play_transition(odds, w["start"], search_stop(w, np.inf, fps), SUSTAIN_S * fps)
        if t is not None:
            placebo.setdefault(w["type"], []).append(t - w["start"])
    m["placebo_windows"] = len(placebo_windows(events, trk.blocks, fps))
    for kind, t in by_type.items():
        t["placebo"] = placebo.get(kind, []) if kind != "otros" else []
        t["placebo_ok"] = not tight(t["placebo"], fps)
    anchored = [kind for kind, t in by_type.items() if t["rule"][4] and t["placebo_ok"]]
    # El ancla de la capa es la mediana menos el retraso de la DFL (añadido de Ana); la mediana se imprime aparte.
    medians = {kind: anchor_of(by_type[kind]["transitions"]) for kind in anchored}
    anchors = {kind: layer_anchor(kind, by_type[kind]["transitions"], delays) for kind in anchored}
    m.update(by_type=by_type, anchors=anchors, medians=medians, delays=dict(delays))

    # 3a. Las condiciones del candidato A, por tipo con ancla. El control de juego no incluye el tramo antes del
    # saque de la 2ª parte, que es el control de D (cambio 3, decidido después de ver la salida del 15/11).
    pre = dead_ball.pre_kickoff(game)
    g_match, g_dead = agg.dead_share(odds, graded), agg.dead_share(odds, pre & graded)
    play = far_from_restarts(events, graded & ~pre, fps)
    g_play = agg.dead_share(odds, play)
    m.update(g_match=g_match, g_dead=g_dead, g_play=g_play, play_frames=int(play.sum()),
             graded_frames=int(graded.sum()))
    m["play_enough"] = enough_play(m["play_frames"], m["graded_frames"])
    gap_windows = [w for w, _, span in dead_ball.gaps_before_restarts(clean.bx, clean.by, events, fps)
                   if span is not None]
    spans = dead_ball.restart_anchor_spans(events, anchors, trk.blocks)
    shifted = placebo_windows(events, trk.blocks, fps)
    for kind, anchor in anchors.items():
        by_type[kind]["a"] = a_conditions(by_type[kind], kind, anchor, spans, gap_windows, shifted, odds, n, fps,
                                         (g_match, g_dead, g_play), m["play_enough"])

    # 3b. Los candidatos en el pipeline: A (con A en los tipos que lo cumplen y B en los demás) si algún tipo
    # cumple A; si no entra, B en todos los tipos con ancla; si no, ninguno.
    report = {}
    without = pipeline.run(trk, extra=[delivery_fn] + list(layers), report=report, pieces=pieces)
    candidates = candidates_for(anchors, {kind: by_type[kind]["a"]["ok"] for kind in anchors})
    m.update(conflicts_without=report["conflictos"], tested={}, chosen=None, modes={})
    for name, modes in candidates:
        result = try_layer(trk, clean, events, anchors, modes, without, report["conflictos"], delivery_fn,
                           pieces, graded, layers)
        m["tested"][name] = dict(result, modes=modes)
        if result["ok"]:
            m.update(chosen=name, modes=modes)
            break
    m["entra"] = m["chosen"] is not None

    # 4. La capa del hueco (lo que pidió el revisor)
    report = {}
    no_gap = pipeline.run(trk, extra=[no_gap_fn] + list(layers), report=report, pieces=pieces)
    m["gap_conflicts"] = report["conflictos"]
    first = np.zeros(n, dtype=bool)
    gap_spans = []
    for window, _, span in dead_ball.gaps_before_restarts(clean.bx, clean.by, events, fps):
        if span is not None and any(a <= window["start"] < b for a, b in trk.blocks):
            first[span[0]:min(span[0] + FIRST_SECONDS_S * fps, span[1])] = True
            gap_spans.append(span)
    m["gap_d_offsets"] = gap_d_offsets(without, gap_spans)
    changed = graded & (no_gap != without)
    m.update(gap_changed=int(changed.sum()), gap_changed_first=int((changed & first).sum()))
    return m


def masked_share(value, k):
    """Una proporción para imprimir, o «—» si sale de menos de 5 ventanas: serían paradas sueltas."""
    return "—" if k < MIN_CASES_PER_TYPE else agg.share(value)


def yes(flag):
    return "sí" if flag else "no"


def seconds(values, fps):
    """Cuantiles (p10 / p25 / p50 / p75 / p90) y recorrido intercuartílico, en segundos."""
    s = spread(values)
    return " / ".join("{:+.1f}".format(v / fps) for v in s[:5]) + "  ({:.1f})".format(s[5] / fps)


def main():
    utf8_stdout()
    game = games.GAME
    games.require(["atd_raw", "atd_meta", "smart_tagging"], game)
    paths = games.asset_paths(game)
    started = time.time()
    report = {}
    trk = tracking.from_atd(paths, game, report=report)
    pipeline.check_atd(report["atd"])  # como pipeline.build: una línea rara del ATD es un error
    events = dead_ball.smart_tagging_events(paths["smart_tagging"], games.GAMES[game]["fps"])
    delivery_fn = lambda clean: dead_ball.evidence(clean, paths, game)  # noqa: E731
    no_gap_fn = lambda clean: dead_ball.evidence(clean, None, game)  # noqa: E731
    m = measure_instant(trk, events, delivery_fn, no_gap_fn, game, layers=delivery_layers(paths, game))
    fps = trk.fps

    print(pipeline.versions())
    print(pipeline.code_version())
    print("pipeline: piezas {}   costes {}".format(json.dumps(pipeline.PIECES, sort_keys=True),
                                                   json.dumps(temporal.DEFAULTS, sort_keys=True)))
    print("capas de la entrega, además de dead_ball.evidence: {}".format(", ".join(layer_names()) or "ninguna"))
    print("huellas: modelo de Ana {}   código de possession/ {}".format(
        model_fingerprint(dead_state.MODEL), code_fingerprint(os.path.join(ROOT, "possession"))))
    print("regla: sostén {} s   búsqueda hasta {} s tras el fin de la ventana   capa ±{:g} en D: {} s antes del"
          " instante (sin hueco) y {} s después (A)".format(SUSTAIN_S, SEARCH_AFTER_S, dead_ball.ANCHOR_SCORE,
                                                       dead_ball.PUSH_BEFORE_S, dead_ball.PUSH_AFTER_S))
    print("cambios a la regla después del 15/11: ancla = mediana − retraso de la DFL en frames {} (los demás tipos, 0)"
          " y control de juego con ≥ {} % de lo evaluado (añadidos de Ana); control de juego sin el tramo antes del"
          " saque de la 2ª parte (decidido después de ver la salida)".format(
              json.dumps(m["delays"], sort_keys=True), 100 * PLAY_MIN_NUM // PLAY_MIN_DEN))
    print("\n1. Dónde cae el reinicio dentro de cada ventana SET PIECES (no los saques iniciales)")
    print("   ventanas en lo evaluado: {}   duración mediana {:.1f} s   a más de {:g} s de esa mediana: {}".format(
        cases(m["windows"]), m["duration_median_s"], OFF_DURATION_S, cases(m["off_duration"])))
    print("   desfases en s desde el INICIO de la ventana (desde el fin: réstale la duración): p10 / p25 / p50 /"
          " p75 / p90 (recorrido intercuartílico)")
    for kind, t in m["by_type"].items():
        print("   {:<22} n={}".format(kind, cases(t["n"])))
        for label, values in (("modelo de Ana, de parado a juego", t["transitions"]),
                              ("el balón vuelve a verse", t["ball"])):
            if len(values) >= MIN_WINDOWS:  # los cuantiles, solo con 10 o más: con menos son ventanas sueltas
                print("      {:<34} n={:<3} {}".format(label, len(values), seconds(values, fps)))
            else:
                print("      {:<34} n={}".format(label, cases(len(values))))
        print("      balón: " + "   ".join("{} {}".format(s, cases(k)) for s, k in t["states"].items()))
        pairs = t["pairs"]
        if len(pairs) >= MIN_CASES_PER_TYPE and len(t["transitions"]) >= MIN_WINDOWS:
            median = anchor_of(t["transitions"])
            print("      con las dos señales (n={}): distancia mediana entre ellas {:.1f} s; del balón a la mediana fija"
                  " {:.1f} s".format(len(pairs), float(np.median([abs(a - b) for a, b in pairs])) / fps,
                                     float(np.median([abs(b - median) for _, b in pairs])) / fps))
        elif len(pairs) >= MIN_CASES_PER_TYPE:
            print("      con las dos señales (n={}): distancia mediana entre ellas {:.1f} s".format(
                len(pairs), float(np.median([abs(a - b) for a, b in pairs])) / fps))

    print("\n2. La regla, por tipo (≥ {} con transición, recorrido ≤ {:g} s, ≥ {} con balón y medianas a ≤ {:g} s,"
          " y la mediana fija más cerca del balón que la transición de cada ventana)".format(
              MIN_WINDOWS, MAX_IQR_S, MIN_BALL, MAX_AGREE_S))
    print("   placebo: las ventanas desplazadas {} min, lejos de reinicios reales: {}; un tipo no tiene ancla si"
          " su placebo también tiene poca dispersión".format(
              "/".join("{:+g}".format(s / 60) for s in PLACEBO_SHIFTS_S), cases(m["placebo_windows"])))
    for kind, t in m["by_type"].items():
        enough, narrow, agree, beats, _ = t["rule"]
        ok = kind in m["anchors"]
        anchor = ("   ancla a {:+.2f} s ({} frames) del inicio: la mediana ({} frames) menos el retraso de la DFL ({}"
                  " frames)".format(m["anchors"][kind] / fps, m["anchors"][kind], m["medians"][kind],
                                    m["delays"].get(kind, 0)) if ok else "")
        print("   {:<22} suficientes {}   poca dispersión {}   el balón coincide {}   la mediana gana {}   el placebo"
              " no se concentra {} (n={})   -> ancla: {}{}".format(
                  kind, yes(enough), yes(narrow), yes(agree), yes(beats), yes(t["placebo_ok"]),
                  cases(len(t["placebo"])), yes(ok), anchor))

    print("\n3. Los dos candidatos de la capa")
    print("   modelo de Ana, D en: partido {}   control de D (antes del saque de la 2ª parte) {}   control de juego"
          " (a más de {} s de cualquier reinicio, sin el tramo antes del saque) {}".format(
              agg.share(m["g_match"]), agg.share(m["g_dead"]), PLAY_FAR_S, agg.share(m["g_play"])))
    print("   control de juego: {} frames (todos, opine o no el modelo), el {:.1f} % de los {} evaluados; hacen falta"
          " {} (el {} %) -> suficiente {}".format(
              m["play_frames"], 100.0 * m["play_frames"] / max(m["graded_frames"], 1), m["graded_frames"],
              -(-m["graded_frames"] * PLAY_MIN_NUM // PLAY_MIN_DEN), 100 * PLAY_MIN_NUM // PLAY_MIN_DEN,
              yes(m["play_enough"])))
    print("   puntos medios: parado antes si ≥ {}   juego después si ≤ {}".format(
        agg.share((m["g_match"] + m["g_dead"]) / 2), agg.share((m["g_match"] + m["g_play"]) / 2)))
    for kind in m["anchors"]:
        a = m["by_type"][kind]["a"]
        print("   {:<22} A: nítido {} ({} de {} a < {:g} s; hace falta el {} %)".format(
            kind, yes(a["sharp"]), cases(a["sharp_count"]), cases(m["by_type"][kind]["n"]), SHARP_S,
            100 * SHARP_NUM // SHARP_DEN))
        for group, s in a["sides"].items():
            print("      Ana, ventanas {} (n={}): antes {}   después {}   -> de acuerdo {}".format(
                group, cases(s["n"]), masked_share(s["before"], s["n"]), masked_share(s["after"], s["n"]),
                yes(s["ok"])))
        p = a["placebo"]
        print("      placebo (n={}): antes {}   después {}   -> pasa {}".format(
            cases(p["n"]), masked_share(p["before"], p["n"]), masked_share(p["after"], p["n"]), yes(p["passes"])))
        print("      control de juego suficiente {}   -> cumple A: {}".format(yes(a["play_enough"]), yes(a["ok"])))
    if not m["anchors"]:
        print("   ningún tipo tiene ancla: no se prueba ningún candidato")
    for name, r in m["tested"].items():
        print("\n   candidato {} ({}):".format(name, ", ".join("{} {}".format(k, v) for k, v in sorted(r["modes"].items()))))
        print("   ventanas con la capa: {} (con hueco {})   frames con piezas en conflicto: sin la capa {}   con ella"
              " {}".format(cases(r["pushes"]), cases(r["with_gap"]), *r["conflicts"]))
        print("   posesiones y paradas: sin la capa {} y {}   con ella {} y {}".format(*r["runs"][0], *r["runs"][1]))
        print("   D en lo evaluado: sin la capa {:.1f} %   con ella {:.1f} %   dentro de la banda ({:g}–{:g} % y ≤ {}"
              " paradas): {}".format(100 * r["dead_share"][0], 100 * r["dead_share"][1], 100 * BAND_D[0],
                                     100 * BAND_D[1], MAX_STOPS, yes(r["band_ok"])))
        print("   ventanas partidas por la capa (2 tramos de D o más, y más que sin ella): {}   ninguna: {}".format(
            cases(r["split"]), yes(r["split"] == 0)))
        print("   salidas del D a ≤ {:g} s del instante: sin la capa {}   con ella {}".format(
            NEAR_S, *(cases(k) for k in r["near"])))
        for label, key in (("antes del instante", "changed_before"), ("después del instante", "changed_after"),
                           ("fuera de la capa", "changed_outside")):
            print("   frames evaluados que cambian, {}: de un equipo al otro {}   de juego a D {}   de D a juego"
                  " {}".format(label, *r[key]))
        print("   regla: sin conflictos, ninguna ventana partida, las posesiones no suben más que las paradas y"
              " dentro de la banda -> se cumple: {}".format(yes(r["ok"])))
    print("\n-> entra: {}".format("el candidato " + m["chosen"] if m["entra"] else "ninguno"))
    if m["entra"]:
        print("   para copiar a dead_ball (frames desde el inicio de la ventana, y modo por tipo): {}   {}".format(
            json.dumps(m["anchors"], sort_keys=True), json.dumps(m["modes"], sort_keys=True)))

    print("\n4. La capa del hueco (PR #8): frames evaluados que cambian de etiqueta con ella: {}   de ellos, en los"
          " primeros {} s de cada hueco: {}".format(m["gap_changed"], FIRST_SECONDS_S, m["gap_changed_first"]))
    print("   frames con piezas en conflicto sin la capa del hueco: {}".format(m["gap_conflicts"]))
    offsets = [o / fps for o in m["gap_d_offsets"] if o is not None]
    print("   inicio del D de la entrega desde el inicio de cada hueco (huecos: {}; negativo si el D ya venía de"
          " antes):".format(cases(len(m["gap_d_offsets"]))))
    for name, k in bins_s(offsets, GAP_D_EDGES_S):
        print("      {:<14} {}".format(name, cases(k)))
    print("      {:<14} {}".format("sin D", cases(sum(o is None for o in m["gap_d_offsets"]))))
    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
