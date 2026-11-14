"""Agregados del partido para las capas de possession/dead_ball.py. Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: recuentos, porcentajes y cuantiles, sin números de frame ni jugadas sueltas.
- **Los goles van siempre juntos, sin desglose por gol:** con 4, cualquier desglose identifica cada
  parada. Las pruebas de cada tramo se hacen dentro del script, y solo se imprime cuántos pasan y cuántos
  fallan.
- **Los reinicios se desglosan por tipo solo con 5 casos o más;** los demás van juntos en «otros».

    python validation/partido/agregados_dead_ball.py

Usa el tracking como lo ve el pipeline: tracking.from_atd y después ball.clean, que hoy lo deja igual. Si
cambia ball.clean, cambian estas medidas. Como instrumento independiente del balón usa el modelo de
jugadores de Ana (possession/dead_state.py), que se entrenó en la DFL, no en este partido.

Responde, con la regla apuntada en docs/decisiones.md (14/11, «fronteras y anclas») antes de ejecutarlo:
1. Cuántos goles anclan en la capa «de cada gol a su saque» y cuántos frames suman.
2. Si cada tramo anclado se comporta como balón muerto: el balón deprisa en el tramo entero y en sus dos
   bordes, con un control (el tramo antes del saque de la 2ª parte, que el FAQ da como `D`) y un placebo
   (los mismos tramos desplazados 4, 6 y 8 minutos).
3. Para la capa del equipo que reanuda: cuántos `SET PIECES` traen equipo y cuántos coinciden con el
   nombre del local o del visitante de los metadatos del ATD.
4. La capa del hueco sin balón antes de cada reinicio (idea de Ismael): cuántas ventanas lo tienen,
   frente a un placebo, y si ahí dentro el modelo de jugadores de Ana ve el juego parado.
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import (FPS, MIN_CASES_PER_TYPE, SET_PIECES_CODE, graded_mask, mean_speed,  # noqa: E402
                   moving_average, norm, pct, print_bins, quantiles, utf8_stdout)
from possession import ball, dead_ball, dead_state, tracking  # noqa: E402
from starter import load_smart_tagging  # noqa: E402
from starter.baseline import team_names  # noqa: E402

# Todo fijado antes de medir (docs/decisiones.md, 14/11).
# Balón «deprisa»: desplazamiento suavizado a 1 s de 5 m/s o más; el suavizado es el del agregado 5 de
# agregados_balon_reinicios.py.
FAST_BALL_MS = 5.0
SMOOTH_HALF_WIDTH = 12  # ±0,5 s
PLAYERS_HALF_WIDTH = FPS  # ±1 s, como en agregados_jugadores.py
# Sección 2. Una prueba falla si la fracción de balón deprisa (de los frames con balón visto) pasa de
# FAST_LIMIT veces la del partido entero; decide solo con MIN_SEEN_FRAMES frames de balón visto o más.
FAST_LIMIT = 0.5
MIN_SEEN_FRAMES = FPS  # 1 s
# Los bordes se miran durante EDGE_S, empezando EDGE_SKIP_S dentro del tramo: el suavizado de 1 s
# arrastra ±0,5 s de lo que pasa fuera.
EDGE_SKIP_S = 1
EDGE_S = 5
# Placebo: los tramos (y los inicios de ventana de la sección 4) desplazados estos segundos. Los tramos de
# gol a saque duran 180 s como mucho, así que desplazados 4 minutos o más no se pisan consigo mismos.
PLACEBO_SHIFTS_S = (-480, -360, -240, 240, 360, 480)
# Sección 4: intervalos de duración de los huecos (de 5 a 60 s).
GAP_LENGTH_EDGES_S = (10, 20, 40)

PASS, FAIL, UNDECIDED = "pasa", "falla", "no decide"


def ball_speed(x, y):
    """Desplazamiento del balón suavizado a 1 s, en m/s; NaN donde no se ve."""
    h = SMOOTH_HALF_WIDTH
    sx, sy = moving_average(x, h), moving_average(y, h)
    v = np.full(len(x), np.nan)
    v[h:-h] = np.hypot(sx[2 * h:] - sx[:-2 * h], sy[2 * h:] - sy[:-2 * h]) / (2.0 * h / FPS)
    v[np.isnan(x) | np.isnan(y)] = np.nan
    return v


def runs(mask):
    """Tramos (inicio, fin) de True seguidos, con el fin sin incluir."""
    edges = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(edges == 1).tolist(), np.flatnonzero(edges == -1).tolist()))


def fast_test(lo, hi, visible, fast, limit):
    """PASS, FAIL o UNDECIDED para los frames [lo, hi)."""
    lo, hi = max(lo, 0), min(hi, len(visible))
    seen = int(visible[lo:hi].sum()) if hi > lo else 0
    if seen < MIN_SEEN_FRAMES:
        return UNDECIDED
    return FAIL if int(fast[lo:hi].sum()) > limit * seen else PASS


def span_verdict(start, stop, visible, fast, limit):
    """(veredicto, (tramo entero, borde inicial, borde final)). Falla si falla alguna de las tres pruebas;
    no decide si no decide ninguna; si no, pasa."""
    skip, edge = EDGE_SKIP_S * FPS, EDGE_S * FPS
    tests = (fast_test(start, stop, visible, fast, limit),
             fast_test(start + skip, min(start + skip + edge, stop), visible, fast, limit),
             fast_test(max(stop - skip - edge, start), stop - skip, visible, fast, limit))
    if FAIL in tests:
        return FAIL, tests
    return (PASS if PASS in tests else UNDECIDED), tests


def inside_blocks(lo, hi, blocks):
    return any(first <= lo and hi <= stop for first, stop in blocks)


def shifted_spans(spans, blocks, blocked, fps):
    """Los tramos desplazados PLACEBO_SHIFTS_S que caen enteros en un tramo evaluado sin tocar ninguna ancla."""
    out = []
    for start, stop in spans:
        for shift in PLACEBO_SHIFTS_S:
            lo, hi = start + shift * fps, stop + shift * fps
            if inside_blocks(lo, hi, blocks) and not blocked[lo:hi].any():
                out.append((lo, hi))
    return out


def dead_share(odds, region):
    """Fracción de los frames de `region` en que el modelo de Ana da `D` más probable que juego, entre los
    que opina (log-odds distinto de cero). NaN si no opina en ninguno."""
    opinion = region & (odds != 0)
    n = int(opinion.sum())
    return float((opinion & (odds > 0)).sum()) / n if n else float("nan")


def describe(label, region, visible, fast, players, odds):
    n = int(region.sum())
    seen = int((region & visible).sum())
    quick = int((region & fast).sum())
    print("   {:<46} {:>7} frames   balón visto {}   deprisa {} de los vistos".format(
        label, n, pct(seen, n), pct(quick, seen)))
    print("   {:<46} jugadores (m/s) {}   modelo de Ana: D en el {:.1f} %".format(
        "", quantiles(players[region]), 100 * dead_share(odds, region)))


def yes(flag):
    return "sí" if flag else "no"


def by_type(windows):
    """{tipo: [ventanas]}, con los tipos de menos de MIN_CASES_PER_TYPE ventanas juntos en «otros»."""
    groups = {}
    for window in windows:
        groups.setdefault(window["type"] or "(sin tipo)", []).append(window)
    out = {}
    for kind, group in groups.items():
        out.setdefault(kind if len(group) >= MIN_CASES_PER_TYPE else "otros", []).extend(group)
    return out


def main():
    utf8_stdout()
    game = games.GAME
    entry = games.GAMES[game]
    n_frames, fps = entry["n_video_frames"], entry["fps"]
    games.require(["atd_raw", "atd_meta", "smart_tagging"], game)
    paths = games.asset_paths(game)
    started = time.time()
    trk = ball.clean(tracking.from_atd(paths, game))  # el balón como lo ve el pipeline
    graded = graded_mask(game, n_frames)
    events = dead_ball.smart_tagging_events(paths["smart_tagging"], fps)
    visible = ~np.isnan(trk.bx) & ~np.isnan(trk.by)
    fast = visible & (ball_speed(trk.bx, trk.by) >= FAST_BALL_MS)
    players = moving_average(mean_speed(trk.px, trk.py), PLAYERS_HALF_WIDTH)
    odds = dead_state.log_odds(trk)
    hard = dead_ball.dead_mask(paths, game)
    pre = dead_ball.pre_kickoff(game) & graded
    n_graded = int(graded.sum())

    print("1. De cada gol a su saque")
    goals = [e for e in events if e["code"] == dead_ball.GOALS_CODE]
    kickoffs = [e for e in events if e["code"] == dead_ball.SET_PIECES_CODE
                and e["type"] == dead_ball.AFTER_GOAL_KICKOFF]
    spans = dead_ball.goal_to_kickoff(events, fps)
    anchored = np.zeros(n_frames, dtype=bool)
    for start, stop in spans:
        anchored[max(start, 0):max(min(stop, n_frames), 0)] = True
    n_anchored = int((anchored & graded).sum())
    print("   goles {}   saques tras gol {}   goles que anclan {} de {}".format(
        len(goals), len(kickoffs), len(spans), len(goals)))
    print("   frames anclados (evaluados), sumados: {} ({} de los evaluados)".format(
        n_anchored, pct(n_anchored, n_graded)))
    if spans:
        print("   duración de los tramos anclados, mediana: {:.0f} s".format(
            np.median([(stop - start) / fps for start, stop in spans])))
    if goals:
        print("   duración de las ventanas GOALS, mediana: {:.0f} s".format(
            np.median([(g["end"] - g["start"]) / fps for g in goals])))
    n_hard = int((hard & graded).sum())
    print("   todas las anclas duras (también el tramo antes del saque): {} frames ({} de los evaluados)"
          "   fuera de los evaluados {}".format(n_hard, pct(n_hard, n_graded), int((hard & ~graded).sum())))

    print("\n2. ¿Cada tramo anclado se comporta como balón muerto?")
    f_match = (fast & graded).sum() / max(int((visible & graded).sum()), 1)
    limit = FAST_LIMIT * f_match
    print("   balón deprisa (≥ {:g} m/s a 1 s) en el partido: {:.1f} % de los frames con balón visto;"
          " un tramo falla por encima del {:.1f} %".format(FAST_BALL_MS, 100 * f_match, 100 * limit))
    print("   pruebas: tramo entero, y {} s desde {} s dentro de cada borde; deciden con ≥ {} frames de balón"
          " visto".format(EDGE_S, EDGE_SKIP_S, MIN_SEEN_FRAMES))
    verdicts = [span_verdict(start, stop, visible, fast, limit) for start, stop in spans]
    n_pass = sum(v == PASS for v, _ in verdicts)
    n_fail = sum(v == FAIL for v, _ in verdicts)
    print("   tramos anclados {}   pasan {}   fallan {}   no deciden {}".format(
        len(spans), n_pass, n_fail, len(spans) - n_pass - n_fail))
    print("   fallos por prueba: tramo entero {}   borde inicial {}   borde final {}".format(
        *(sum(tests[i] == FAIL for _, tests in verdicts) for i in range(3))))
    control = [span_verdict(start, stop, visible, fast, limit)[0] for start, stop in runs(pre)]
    control_ok = bool(control) and all(v == PASS for v in control)
    print("   control (tramo antes del saque de la 2ª parte): {}".format(", ".join(control) or "no hay"))
    placebo = [span_verdict(lo, hi, visible, fast, limit)[0]
               for lo, hi in shifted_spans(spans, trk.blocks, hard, fps)]
    deciding = [v for v in placebo if v != UNDECIDED]
    placebo_fail = sum(v == FAIL for v in deciding)
    power = len(deciding) >= 2 * len(spans) and placebo_fail >= 0.5 * len(deciding)
    print("   placebo (desplazados {} s): {} tramos, deciden {}, fallan {} ({} de los que deciden)".format(
        "/".join("{:+d}".format(s) for s in PLACEBO_SHIFTS_S), len(placebo), len(deciding), placebo_fail,
        pct(placebo_fail, len(deciding))))
    describe("partido entero (evaluados)", graded, visible, fast, players, odds)
    describe("tramo antes del saque de la 2ª parte (D, FAQ)", pre, visible, fast, players, odds)
    describe("de gol a saque (anclado)", anchored & graded, visible, fast, players, odds)
    spans_ok = bool(spans) and n_fail == 0 and n_pass >= 0.5 * len(spans)
    print("   regla: el control pasa {}   el placebo tiene potencia {}   ningún tramo falla y la mitad o más"
          " pasan {}   -> la capa entra: {}".format(yes(control_ok), yes(power), yes(spans_ok),
                                                     yes(control_ok and power and spans_ok)))

    print("\n3. Equipo de los SET PIECES frente a los nombres de los metadatos del ATD")
    home, away = (norm(name) for name in team_names(paths["atd_meta"]))
    set_pieces = [e for e in load_smart_tagging.load(game) if norm(e["code"]) == SET_PIECES_CODE]
    teams = [norm({norm(k): v for k, v in e["tags"].items()}.get("team")) for e in set_pieces]
    with_team = [t for t in teams if t not in ("", "n/a")]
    print("   SET PIECES {}   con equipo {}   igual al local {}   igual al visitante {}   sin coincidir {}".format(
        len(set_pieces), len(with_team), sum(t == home for t in with_team), sum(t == away for t in with_team),
        sum(t not in (home, away) for t in with_team)))

    print("\n4. El hueco sin balón antes de cada reinicio (no se cuentan los saques iniciales)")
    results = [r for r in dead_ball.gaps_before_restarts(trk.bx, trk.by, events, fps)
               if inside_blocks(r[0]["start"], r[0]["start"] + 1, trk.blocks)]
    n_windows = len(results)
    with_gap = [r for r in results if r[1] == dead_ball.GAP]
    coverage = len(with_gap) / n_windows if n_windows else 0.0
    print("   ventanas que empiezan en frames evaluados: {}".format(n_windows))
    print("   " + "   ".join("{} {} ({})".format(state, sum(r[1] == state for r in results),
                                                 pct(sum(r[1] == state for r in results), n_windows))
                             for state in dead_ball.GAP_STATES))
    for kind, group in sorted(by_type([r[0] for r in results]).items(), key=lambda kv: (-len(kv[1]), kv[0])):
        ids = {id(w) for w in group}
        k = sum(id(r[0]) in ids for r in with_gap)
        print("      {:<22} n={:>3}   con hueco {} ({})".format(kind, len(group), k, pct(k, len(group))))
    last_seen = dead_ball.last_seen_before(trk.bx, trk.by)
    restart_starts = [e["start"] for e in events if e["code"] in (dead_ball.GOALS_CODE, dead_ball.SET_PIECES_CODE)]
    shifted = [r[0]["start"] + shift * fps for r in results for shift in PLACEBO_SHIFTS_S]
    shifted = [s for s in shifted if inside_blocks(s, s + 1, trk.blocks)]
    placebo_gaps = sum(dead_ball.gap_before(last_seen, s, restart_starts, fps)[0] == dead_ball.GAP for s in shifted)
    coverage_placebo = placebo_gaps / len(shifted) if shifted else float("nan")
    print("   placebo (inicios desplazados {} s): {} inicios, con hueco {} ({})".format(
        "/".join("{:+d}".format(s) for s in PLACEBO_SHIFTS_S), len(shifted), placebo_gaps,
        pct(placebo_gaps, len(shifted))))
    gap_region = np.zeros(n_frames, dtype=bool)
    first_seconds = np.zeros(n_frames, dtype=bool)
    for _, _, (start, stop) in with_gap:
        gap_region[start:stop] = True
        first_seconds[start:min(start + EDGE_S * fps, stop)] = True
    print_bins("duración de los huecos", [(stop - start) / fps for _, _, (start, stop) in with_gap],
               GAP_LENGTH_EDGES_S, indent="   ")
    n_gap = int((gap_region & graded).sum())
    print("   frames de hueco (evaluados), sumados: {} ({} de los evaluados)".format(n_gap, pct(n_gap, n_graded)))
    g_match, g_ctrl = dead_share(odds, graded), dead_share(odds, pre)
    g_gap = dead_share(odds, gap_region & graded)
    print("   modelo de Ana, D en: partido {:.1f} %   control {:.1f} %   huecos {:.1f} %   primeros {} s de los"
          " huecos {:.1f} %".format(100 * g_match, 100 * g_ctrl, 100 * g_gap, EDGE_S,
                                    100 * dead_share(odds, first_seconds & graded)))
    print("   jugadores (m/s) en los huecos: {}".format(quantiles(players[gap_region & graded])))
    covers = coverage >= 0.5
    beats_placebo = coverage >= 2 * coverage_placebo  # False si el placebo es NaN
    instrument = g_ctrl > g_match
    looks_dead = instrument and g_gap >= (g_match + g_ctrl) / 2
    print("   regla: cobertura ≥ 50 % {}   ≥ 2 veces el placebo {}   el modelo de Ana separa el control del"
          " partido {}   los huecos, más cerca del control que del partido {}   -> la capa entra: {}".format(
              yes(covers), yes(beats_placebo), yes(instrument), yes(looks_dead),
              yes(covers and beats_placebo and looks_dead)))

    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
