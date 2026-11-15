"""Agregados del partido para el instante del reinicio (possession/dead_ball.py). Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: recuentos, cuantiles y desfases en segundos, sin números de frame ni jugadas
sueltas. Los recuentos de ventanas por debajo de 5 se tapan con «< 5», como en el perfil del ATD.

    python validation/partido/agregados_instante_reinicio.py

Responde, con la regla apuntada en docs/decisiones.md (15/11, «el instante del reinicio») antes de
ejecutarlo:
1. Dónde cae el reinicio dentro de cada ventana `SET PIECES` (no los saques iniciales), con dos señales
   que no son etiquetas: cuándo vuelve a verse el balón, si no se veía al empezar la ventana, y cuándo el
   modelo de jugadores de Ana pasa de parado a juego. Contado desde el inicio de la ventana y desde su fin.
2. La regla: qué tipos tienen un sitio fijo con poca dispersión, y su ancla.
3. Con esas anclas, la capa en el pipeline: sin ella y con ella, y su condición de daño.
4. Para la capa del hueco (PR #8), el agregado que pidió el revisor: de los frames que cambian de
   etiqueta con ella, cuántos caen en los primeros 5 s de cada hueco.

`measure_instant` y las funciones de la regla no abren ningún fichero; los importa
validation/scripts/comprobar_balon_muerto.py (sección 11), que ejecuta Claude con un partido inventado y
con la apertura de ficheros prohibida. Por eso **nada fuera de `main` puede abrir un fichero.**
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import MIN_CASES_PER_TYPE, graded_mask, utf8_stdout  # noqa: E402
from possession import dead_ball, dead_state, pipeline, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
# Todo fijado antes de medir (docs/decisiones.md, 15/11).
SUSTAIN_S = 2  # el modelo de Ana pasa a juego si ve juego (log-odds < 0) 2 s seguidos
SEARCH_AFTER_S = 10  # las señales se buscan desde el inicio de la ventana hasta 10 s después de su fin
MIN_WINDOWS = 10  # un tipo tiene ancla solo con 10 ventanas o más con la transición del modelo de Ana
MAX_IQR_S = 2.0  # y si el recorrido intercuartílico de esa transición es de 2 s o menos
MIN_BALL = 5  # con 5 ventanas o más en las que vuelve a verse el balón
MAX_AGREE_S = 1.0  # y si la mediana de esa reaparición queda a 1 s o menos de la de la transición
NEAR_S = 1.0  # descriptivo: salidas del D a 1 s o menos del instante anclado
FIRST_SECONDS_S = 5  # sección 4: los primeros 5 s de cada hueco
BACK, SEEN_AT_START, NOT_BACK = "vuelve a verse", "visto al empezar", "no vuelve"


def cases(k):
    """Un recuento de ventanas para imprimir: «< 5» si es menor que 5, también el 0."""
    return "< 5" if k < MIN_CASES_PER_TYPE else str(k)


def play_transition(odds, start, stop, sustain):
    """Primer frame f en [start, stop) en que el modelo de Ana pasa de parado a juego: log-odds > 0 en f − 1
    y < 0 en los `sustain` frames desde f. None si no hay."""
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


def anchor_rule(transitions_s, ball_s):
    """La regla de un tipo, con los desfases (s, desde el inicio de la ventana) de la transición del modelo
    de Ana y de la reaparición del balón. Devuelve (enough, tight, agree, entra)."""
    enough = len(transitions_s) >= MIN_WINDOWS
    tight = bool(enough and spread(transitions_s)[5] <= MAX_IQR_S)
    agree = bool(len(ball_s) >= MIN_BALL and enough
                 and abs(float(np.median(ball_s)) - float(np.median(transitions_s))) <= MAX_AGREE_S)
    return enough, tight, agree, enough and tight and agree


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


def changes(without, with_layer, mask):
    """Frames de `mask` que cambian, por tipo: (de un equipo al otro, de juego a D, de D a juego)."""
    play_before, play_after = without != D, with_layer != D
    team = mask & play_before & play_after & (without != with_layer)
    to_dead = mask & play_before & ~play_after
    to_play = mask & ~play_before & play_after
    return int(team.sum()), int(to_dead.sum()), int(to_play.sum())


def harm_rule(runs_without, runs_with, split_windows):
    """Condición de daño: ninguna ventana con ancla acaba con más de un tramo de D dentro, y las posesiones
    no suben más que las paradas (cada posesión nueva tiene que venir de una parada nueva que la parte)."""
    return split_windows == 0 and runs_with[0] - runs_without[0] <= runs_with[1] - runs_without[1]


def measure_instant(trk, events, anchors_fn, no_gap_fn, game=games.GAME, pieces=None, odds_fn=None):
    """Las cuentas de las cuatro secciones y la regla aplicada. No abre ningún fichero por sí misma.

    `trk` es el tracking sin limpiar; `events`, los de dead_ball.smart_tagging_events. `anchors_fn` es la
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
    m = {"windows": len(windows), "durations": sorted({(w["end"] - w["start"]) / fps for w in windows})}

    # 1. Las dos señales, por tipo
    groups = {}
    for window in windows:
        groups.setdefault(window["type"], []).append(window)
    small = sorted(kind for kind, group in groups.items() if len(group) < MIN_CASES_PER_TYPE)
    if small:
        groups["otros"] = [w for kind in small for w in groups.pop(kind)]
    by_type = {}
    for kind, group in sorted(groups.items()):
        transitions, ball, states, gaps = [], [], {BACK: 0, SEEN_AT_START: 0, NOT_BACK: 0}, []
        for w in group:
            limit = w["end"] + SEARCH_AFTER_S * fps
            t = play_transition(odds, w["start"], limit, SUSTAIN_S * fps)
            state, b = ball_back(seen, w["start"], limit)
            states[state] += 1
            if t is not None:
                transitions.append((t - w["start"]) / fps)
            if b is not None:
                ball.append((b - w["start"]) / fps)
            if t is not None and b is not None:
                gaps.append(abs(t - b) / fps)
        rule = anchor_rule(transitions, ball) if kind != "otros" else (False, False, False, False)
        by_type[kind] = {"n": len(group), "transitions": transitions, "ball": ball, "states": states,
                         "both": gaps, "rule": rule}
    anchors = {kind: int(round(float(np.median(t["transitions"])) * fps))
               for kind, t in by_type.items() if t["rule"][3]}
    m.update(by_type=by_type, anchors=anchors)

    # 3. La capa en el pipeline
    if anchors:
        layer = lambda c: dead_ball.restart_anchor_evidence(c, events, anchors)  # noqa: E731
        reports = ({}, {})
        without = pipeline.run(trk, extra=[anchors_fn], report=reports[0], pieces=pieces)
        with_layer = pipeline.run(trk, extra=[anchors_fn, layer], report=reports[1], pieces=pieces)
        spans = dead_ball.restart_anchor_spans(events, anchors, trk.blocks, fps)
        inside = np.zeros(n, dtype=bool)
        near = [0, 0]
        for _, start, instant, stop in spans:
            inside[start:stop] = True
            for i, codes in enumerate((without, with_layer)):
                frame = last_exit(codes, start, stop)
                near[i] += frame is not None and abs(frame - instant) <= NEAR_S * fps
        split = sum(dead_runs(with_layer, start, stop) > 1 for _, start, _, stop in spans)
        m.update(spans=len(spans), conflicts=(reports[0]["conflictos"], reports[1]["conflictos"]),
                 runs=(runs(without, trk.blocks), runs(with_layer, trk.blocks)), split=split, near=tuple(near),
                 changed_inside=changes(without, with_layer, graded & inside),
                 changed_outside=changes(without, with_layer, graded & ~inside))
        m["harm_ok"] = harm_rule(m["runs"][0], m["runs"][1], split) and m["conflicts"] == (0, 0)
    else:
        report = {}
        without = pipeline.run(trk, extra=[anchors_fn], report=report, pieces=pieces)
        m.update(conflicts=(report["conflictos"], None), harm_ok=False)
    m["entra"] = bool(anchors) and m["harm_ok"]

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


def main():
    utf8_stdout()
    game = games.GAME
    games.require(["atd_raw", "atd_meta", "smart_tagging"], game)
    paths = games.asset_paths(game)
    started = time.time()
    trk = tracking.from_atd(paths, game)
    events = dead_ball.smart_tagging_events(paths["smart_tagging"], games.GAMES[game]["fps"])
    anchors_fn = lambda clean: dead_ball.evidence(clean, paths, game)  # noqa: E731
    no_gap_fn = lambda clean: dead_ball.evidence(clean, None, game)  # noqa: E731
    m = measure_instant(trk, events, anchors_fn, no_gap_fn, game)
    fps = trk.fps

    print("limpieza del balón: ball.{} (pipeline.PIECES)".format(pipeline.PIECES["ball"]))
    print("\n1. Dónde cae el reinicio dentro de cada ventana SET PIECES (no los saques iniciales)")
    print("   ventanas en lo evaluado: {}   duración de las ventanas (s): {}".format(
        m["windows"], ", ".join("{:g}".format(d) for d in m["durations"])))
    print("   desfases en s desde el INICIO de la ventana (desde el fin: réstale la duración): p10 / p25 / p50 /"
          " p75 / p90 (recorrido intercuartílico)")
    for kind, t in m["by_type"].items():
        print("   {:<22} n={}".format(kind, cases(t["n"])))
        for label, values in (("modelo de Ana, de parado a juego", t["transitions"]),
                              ("el balón vuelve a verse", t["ball"])):
            if len(values) >= MIN_CASES_PER_TYPE:
                print("      {:<34} n={:<3} {}".format(label, len(values), " / ".join(
                    "{:+.1f}".format(v) for v in spread(values)[:5]) + "  ({:.1f})".format(spread(values)[5])))
            else:
                print("      {:<34} n=< 5".format(label))
        print("      balón: " + "   ".join("{} {}".format(s, cases(k)) for s, k in t["states"].items()))
        if len(t["both"]) >= MIN_CASES_PER_TYPE:
            print("      con las dos señales (n={}): distancia entre ellas, mediana {:.1f} s".format(
                len(t["both"]), float(np.median(t["both"]))))

    print("\n2. La regla, por tipo (≥ {} con transición, recorrido ≤ {:g} s, ≥ {} con balón y medianas"
          " a ≤ {:g} s)".format(MIN_WINDOWS, MAX_IQR_S, MIN_BALL, MAX_AGREE_S))
    for kind, t in m["by_type"].items():
        enough, tight, agree, ok = t["rule"]
        anchor = "   ancla a {:+.2f} s del inicio".format(m["anchors"][kind] / fps) if ok else ""
        print("   {:<22} suficientes {}   poca dispersión {}   el balón coincide {}   -> ancla: {}{}".format(
            kind, yes(enough), yes(tight), yes(agree), yes(ok), anchor))

    print("\n3. La capa con esas anclas")
    if m["anchors"]:
        print("   ventanas con ancla: {}   frames con piezas en conflicto: sin la capa {}   con ella {}".format(
            m["spans"], *m["conflicts"]))
        print("   posesiones y paradas: sin la capa {} y {}   con ella {} y {}".format(
            *m["runs"][0], *m["runs"][1]))
        print("   ventanas con ancla y más de un tramo de D con la capa: {}".format(m["split"]))
        print("   salidas del D a ≤ {:g} s del instante anclado: sin la capa {}   con ella {}".format(
            NEAR_S, *m["near"]))
        print("   frames evaluados que cambian, dentro de las ventanas con ancla: de un equipo al otro {}"
              "   de juego a D {}   de D a juego {}".format(*m["changed_inside"]))
        print("   y fuera de ellas: de un equipo al otro {}   de juego a D {}   de D a juego {}".format(
            *m["changed_outside"]))
        print("   regla: sin conflictos, ninguna ventana partida y las posesiones no suben más que las paradas"
              " -> se cumple: {}".format(yes(m["harm_ok"])))
    else:
        print("   ningún tipo tiene ancla: la capa no se prueba")
    print("\n-> la capa del instante entra: {}".format(yes(m["entra"])))

    print("\n4. La capa del hueco (PR #8): frames evaluados que cambian de etiqueta con ella: {}   de ellos, en los"
          " primeros {} s de cada hueco: {}".format(m["gap_changed"], FIRST_SECONDS_S, m["gap_changed_first"]))
    print("   frames con piezas en conflicto sin la capa del hueco: {}".format(m["gap_conflicts"]))
    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
