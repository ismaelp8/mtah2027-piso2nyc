"""Agregados del partido para el instante del reinicio (possession/dead_ball.py). Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: recuentos, cuantiles y desfases desde el inicio de cada ventana, sin números de
frame ni jugadas sueltas. Los recuentos de ventanas por debajo de 5 se tapan con «< 5», como en el perfil
del ATD.

    python validation/partido/agregados_instante_reinicio.py

Responde, con la regla apuntada en docs/decisiones.md (15/11, «el instante del reinicio») antes de
ejecutarlo:
1. Dónde cae el reinicio dentro de cada ventana `SET PIECES` (no los saques iniciales), con dos señales
   que no son etiquetas: cuándo vuelve a verse el balón, si no se veía al empezar la ventana, y cuándo el
   modelo de jugadores de Ana pasa de parado a juego. Contado desde el inicio de la ventana; las ventanas
   duran lo mismo, así que desde el fin es restar esa duración.
2. La regla: qué tipos tienen un sitio fijo con poca dispersión, y su ancla.
3. Con esas anclas, la capa en el pipeline: sin ella y con ella, y su condición de daño.
4. Para la capa del hueco (PR #8), el agregado que pidió el revisor: de los frames que cambian de
   etiqueta con ella, cuántos caen en los primeros 5 s de cada hueco.

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
from comun import MIN_CASES_PER_TYPE, graded_mask, utf8_stdout  # noqa: E402
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
    """El ancla de un tipo: la mediana de la transición, en frames desde el inicio de la ventana."""
    return int(round(float(np.median(transitions))))


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


def measure_instant(trk, events, delivery_fn, no_gap_fn, game=games.GAME, pieces=None, odds_fn=None):
    """Las cuentas de las cuatro secciones y la regla aplicada. No abre ningún fichero por sí misma.

    `trk` es el tracking sin limpiar; `events`, los de dead_ball.smart_tagging_events. `delivery_fn` es la
    evidencia de dead_ball de la entrega (con la capa del hueco) y `no_gap_fn` la misma sin la capa del hueco;
    las dos son funciones del tracking limpio. `pieces` cambia piezas del pipeline (en el partido, None) y
    `odds_fn` el instrumento (por defecto, dead_state.log_odds, el modelo de Ana).
    """
    n, fps = len(trk.bx), trk.fps
    graded = graded_mask(game, n)
    pieces = pieces or {}
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
    anchors = {kind: anchor_of(t["transitions"]) for kind, t in by_type.items() if t["rule"][4]}
    m.update(by_type=by_type, anchors=anchors)

    # 3. La capa en el pipeline
    if anchors:
        layer = lambda c: dead_ball.restart_anchor_evidence(c, events, anchors)  # noqa: E731
        reports = ({}, {})
        without = pipeline.run(trk, extra=[delivery_fn], report=reports[0], pieces=pieces)
        with_layer = pipeline.run(trk, extra=[delivery_fn, layer], report=reports[1], pieces=pieces)
        spans = dead_ball.restart_anchor_spans(events, anchors, trk.blocks, fps)
        inside = np.zeros(n, dtype=bool)
        near, split = [0, 0], 0
        for window, start, instant, stop in spans:
            inside[start:stop] = True
            end = harm_stop(window, dead_ball.next_restart(events, window), stop, fps)
            split += worse(without, with_layer, start, end)
            for i, codes in enumerate((without, with_layer)):
                frame = last_exit(codes, start, end)
                near[i] += frame is not None and abs(frame - instant) <= NEAR_S * fps
        m.update(spans=len(spans), conflicts=(reports[0]["conflictos"], reports[1]["conflictos"]),
                 runs=(runs(without, trk.blocks), runs(with_layer, trk.blocks)), split=split, near=tuple(near),
                 changed_inside=changes(without, with_layer, graded & inside),
                 changed_outside=changes(without, with_layer, graded & ~inside))
        m["harm_ok"] = harm_rule(m["runs"][0], m["runs"][1], split) and m["conflicts"] == (0, 0)
    else:
        report = {}
        without = pipeline.run(trk, extra=[delivery_fn], report=report, pieces=pieces)
        m.update(spans=0, conflicts=(report["conflictos"], None), harm_ok=False)
    m["entra"] = bool(anchors) and m["spans"] >= 1 and m["harm_ok"]

    # 4. La capa del hueco (lo que pidió el revisor)
    report = {}
    no_gap = pipeline.run(trk, extra=[no_gap_fn], report=report, pieces=pieces)
    m["gap_conflicts"] = report["conflictos"]
    first = np.zeros(n, dtype=bool)
    for window, _, span in dead_ball.gaps_before_restarts(clean.bx, clean.by, events, fps):
        if span is not None and any(a <= window["start"] < b for a, b in trk.blocks):
            first[span[0]:min(span[0] + FIRST_SECONDS_S * fps, span[1])] = True
    changed = graded & (no_gap != without)
    m.update(gap_changed=int(changed.sum()), gap_changed_first=int((changed & first).sum()))
    return m


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
    trk = tracking.from_atd(paths, game)
    events = dead_ball.smart_tagging_events(paths["smart_tagging"], games.GAMES[game]["fps"])
    delivery_fn = lambda clean: dead_ball.evidence(clean, paths, game)  # noqa: E731
    no_gap_fn = lambda clean: dead_ball.evidence(clean, None, game)  # noqa: E731
    m = measure_instant(trk, events, delivery_fn, no_gap_fn, game)
    fps = trk.fps

    print("pipeline: piezas {}   costes {}".format(json.dumps(pipeline.PIECES, sort_keys=True),
                                                   json.dumps(temporal.DEFAULTS, sort_keys=True)))
    print("huellas: modelo de Ana {}   código de possession/ {}".format(
        model_fingerprint(dead_state.MODEL), code_fingerprint(os.path.join(ROOT, "possession"))))
    print("regla: sostén {} s   búsqueda hasta {} s tras el fin de la ventana   capa ±{:g} en D, {} s tras el"
          " instante".format(SUSTAIN_S, SEARCH_AFTER_S, dead_ball.ANCHOR_SCORE, dead_ball.ANCHOR_AFTER_S))
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
            anchor = anchor_of(t["transitions"])
            print("      con las dos señales (n={}): distancia mediana entre ellas {:.1f} s; del balón al ancla fija"
                  " {:.1f} s".format(len(pairs), float(np.median([abs(a - b) for a, b in pairs])) / fps,
                                     float(np.median([abs(b - anchor) for _, b in pairs])) / fps))
        elif len(pairs) >= MIN_CASES_PER_TYPE:
            print("      con las dos señales (n={}): distancia mediana entre ellas {:.1f} s".format(
                len(pairs), float(np.median([abs(a - b) for a, b in pairs])) / fps))

    print("\n2. La regla, por tipo (≥ {} con transición, recorrido ≤ {:g} s, ≥ {} con balón y medianas a ≤ {:g} s,"
          " y el ancla fija más cerca del balón que la transición de cada ventana)".format(
              MIN_WINDOWS, MAX_IQR_S, MIN_BALL, MAX_AGREE_S))
    for kind, t in m["by_type"].items():
        enough, tight, agree, beats, ok = t["rule"]
        anchor = "   ancla a {:+.2f} s ({} frames) del inicio".format(
            m["anchors"][kind] / fps, m["anchors"][kind]) if ok else ""
        print("   {:<22} suficientes {}   poca dispersión {}   el balón coincide {}   el ancla gana {}   -> ancla:"
              " {}{}".format(kind, yes(enough), yes(tight), yes(agree), yes(beats), yes(ok), anchor))

    print("\n3. La capa con esas anclas")
    if m["anchors"]:
        print("   ventanas con ancla: {}   frames con piezas en conflicto: sin la capa {}   con ella {}".format(
            cases(m["spans"]), *m["conflicts"]))
        print("   posesiones y paradas: sin la capa {} y {}   con ella {} y {}".format(
            *m["runs"][0], *m["runs"][1]))
        print("   ventanas con ancla partidas por la capa (2 tramos de D o más, y más que sin ella): {}   ninguna: {}"
              .format(cases(m["split"]), yes(m["split"] == 0)))
        print("   salidas del D a ≤ {:g} s del instante anclado: sin la capa {}   con ella {}".format(
            NEAR_S, *(cases(k) for k in m["near"])))
        print("   frames evaluados que cambian, dentro de las ventanas con ancla: de un equipo al otro {}"
              "   de juego a D {}   de D a juego {}".format(*m["changed_inside"]))
        print("   y fuera de ellas: de un equipo al otro {}   de juego a D {}   de D a juego {}".format(
            *m["changed_outside"]))
        print("   regla: sin conflictos, ninguna ventana partida y las posesiones no suben más que las paradas"
              " -> se cumple: {}".format(yes(m["harm_ok"])))
    else:
        print("   ningún tipo tiene ancla: la capa no se prueba")
    print("\n-> la capa del instante entra: {}".format(yes(m["entra"])))
    if m["entra"]:
        print("   para copiar a dead_ball (frames desde el inicio de la ventana): {}".format(
            json.dumps(m["anchors"], sort_keys=True)))

    print("\n4. La capa del hueco (PR #8): frames evaluados que cambian de etiqueta con ella: {}   de ellos, en los"
          " primeros {} s de cada hueco: {}".format(m["gap_changed"], FIRST_SECONDS_S, m["gap_changed_first"]))
    print("   frames con piezas en conflicto sin la capa del hueco: {}".format(m["gap_conflicts"]))
    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
