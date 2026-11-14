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

`measure` hace todas las cuentas de las secciones 1, 2 y 4 sin abrir ningún fichero, así que se puede
probar con un partido inventado: es la sección 9 de validation/scripts/comprobar_balon_muerto.py. Solo
`main` lee el partido.
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
# Balón «deprisa»: 5 m/s o más (fijado en esa entrada), con el desplazamiento suavizado a 1 s del agregado 5
# de agregados_balon_reinicios.py.
FAST_BALL_MS = 5.0
SMOOTH_HALF_WIDTH = 12  # ±0,5 s
PLAYERS_HALF_WIDTH = FPS  # ±1 s, como en agregados_jugadores.py
# Sección 2. Una prueba falla si la fracción de balón deprisa (de los frames con balón visto) pasa de
# FAST_LIMIT veces la del partido entero; decide solo con MIN_SEEN_FRAMES frames de balón visto o más.
FAST_LIMIT = 0.5
MIN_SEEN_FRAMES = FPS  # 1 s
# Los bordes se miran durante EDGE_S, empezando EDGE_SKIP_S dentro del tramo. La velocidad de un frame usa
# las posiciones de ±0,96 s a su alrededor (dos medias de ±0,5 s separadas 1 s), así que, desde 1 s dentro,
# ninguna velocidad mira frames de fuera del tramo.
EDGE_SKIP_S = 1
EDGE_S = 5
# Placebo: los tramos (y los inicios de ventana de la sección 4) desplazados estos segundos. Los tramos de
# gol a saque duran 180 s como mucho, así que desplazados 4 minutos o más no se pisan consigo mismos.
PLACEBO_SHIFTS_S = (-480, -360, -240, 240, 360, 480)
# Sección 4: intervalos de duración de los huecos (de 5 a 60 s), y grupos de tipos que se describen aparte.
GAP_LENGTH_EDGES_S = (10, 20, 40)
TYPE_GROUPS = (("córner y falta", ("corner kick", "free kick")),
               ("banda y saque de puerta", ("throw-in", "goal kick")))

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


def share(value):
    """Una fracción como porcentaje, o «—» si es NaN (no hay frames)."""
    return "—" if np.isnan(value) else "{:.1f} %".format(100 * value)


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


def measure(trk, events, game=games.GAME):
    """Las cuentas de las secciones 1, 2 y 4, y la regla aplicada. No abre ningún fichero.

    `trk` es el tracking con el balón como lo ve el pipeline; `events`, los de dead_ball.smart_tagging_events.
    Devuelve un diccionario de agregados; «gol_entra» y «hueco_entra» son la regla de docs/decisiones.md.
    """
    entry = games.GAMES[game]
    n_frames, fps = entry["n_video_frames"], entry["fps"]
    graded = graded_mask(game, n_frames)
    visible = ~np.isnan(trk.bx) & ~np.isnan(trk.by) & graded  # todo, sobre los frames evaluados
    fast = visible & (ball_speed(trk.bx, trk.by) >= FAST_BALL_MS)
    players = moving_average(mean_speed(trk.px, trk.py), PLAYERS_HALF_WIDTH)
    odds = dead_state.log_odds(trk)
    pre = dead_ball.pre_kickoff(game) & graded
    m = {"n_graded": int(graded.sum())}

    def region(label, mask):
        mask = mask & graded
        n, seen = int(mask.sum()), int((mask & visible).sum())
        return {"label": label, "frames": n, "seen": pct(seen, n), "fast": pct(int((mask & fast).sum()), seen),
                "players": quantiles(players[mask]), "ana": share(dead_share(odds, mask))}

    # 1. De cada gol a su saque
    goals = [e for e in events if e["code"] == dead_ball.GOALS_CODE]
    spans = dead_ball.goal_to_kickoff(events, fps)
    anchored = np.zeros(n_frames, dtype=bool)
    for start, stop in spans:
        anchored[max(start, 0):max(min(stop, n_frames), 0)] = True
    hard = dead_ball.pre_kickoff(game) | anchored  # las anclas duras si entrara la capa
    m.update(goals=len(goals), spans=len(spans),
             kickoffs=sum(e["code"] == dead_ball.SET_PIECES_CODE and e["type"] == dead_ball.AFTER_GOAL_KICKOFF
                          for e in events),
             anchored_frames=int((anchored & graded).sum()), hard_frames=int((hard & graded).sum()),
             hard_outside=int((hard & ~graded).sum()),
             span_median_s=float(np.median([(b - a) / fps for a, b in spans])) if spans else float("nan"),
             goal_median_s=float(np.median([(g["end"] - g["start"]) / fps for g in goals])) if goals
             else float("nan"))

    # 2. ¿Cada tramo anclado se comporta como balón muerto?
    f_match = int(fast.sum()) / max(int(visible.sum()), 1)
    limit = FAST_LIMIT * f_match
    verdicts = [span_verdict(start, stop, visible, fast, limit) for start, stop in spans]
    control = [span_verdict(start, stop, visible, fast, limit)[0] for start, stop in runs(pre)]
    placebo = [span_verdict(lo, hi, visible, fast, limit)[0]
               for lo, hi in shifted_spans(spans, trk.blocks, hard, fps)]
    deciding = [v for v in placebo if v != UNDECIDED]
    n_pass = sum(v == PASS for v, _ in verdicts)
    n_fail = sum(v == FAIL for v, _ in verdicts)
    placebo_fail = sum(v == FAIL for v in deciding)
    control_ok = bool(control) and all(v == PASS for v in control)
    power = bool(spans) and len(deciding) >= 2 * len(spans) and placebo_fail >= 0.5 * len(deciding)
    spans_ok = bool(spans) and n_fail == 0 and n_pass >= 0.5 * len(spans)
    m.update(f_match=f_match, limit=limit, n_pass=n_pass, n_fail=n_fail,
             fails_by_test=tuple(sum(tests[i] == FAIL for _, tests in verdicts) for i in range(3)),
             control=control, placebo=len(placebo), placebo_deciding=len(deciding), placebo_fail=placebo_fail,
             control_ok=control_ok, power=power, spans_ok=spans_ok, gol_entra=control_ok and power and spans_ok,
             regions=[region("partido entero (evaluados)", graded),
                      region("tramo antes del saque de la 2ª parte (D, FAQ)", pre),
                      region("de gol a saque (anclado)", anchored)])

    # 4. El hueco sin balón antes de cada reinicio
    results = [r for r in dead_ball.gaps_before_restarts(trk.bx, trk.by, events, fps)
               if inside_blocks(r[0]["start"], r[0]["start"] + 1, trk.blocks)]
    with_gap = [r for r in results if r[1] == dead_ball.GAP]
    last_seen = dead_ball.last_seen_before(trk.bx, trk.by)
    restart_starts = [e["start"] for e in events if e["code"] in (dead_ball.GOALS_CODE, dead_ball.SET_PIECES_CODE)]
    shifted = [r[0]["start"] + shift * fps for r in results for shift in PLACEBO_SHIFTS_S]
    shifted = [s for s in shifted if inside_blocks(s, s + 1, trk.blocks)]
    placebo_gaps = sum(dead_ball.gap_before(last_seen, s, restart_starts, fps)[0] == dead_ball.GAP
                       for s in shifted)
    gap_region = np.zeros(n_frames, dtype=bool)
    first_seconds = np.zeros(n_frames, dtype=bool)
    group_regions = {label: np.zeros(n_frames, dtype=bool) for label, _ in TYPE_GROUPS}
    for window, _, (start, stop) in with_gap:
        gap_region[start:stop] = True
        first_seconds[start:min(start + EDGE_S * fps, stop)] = True
        for label, kinds in TYPE_GROUPS:
            if window["type"] in kinds:
                group_regions[label][start:stop] = True
    gap_ids = {id(r[0]) for r in with_gap}
    coverage = len(with_gap) / len(results) if results else 0.0
    coverage_placebo = placebo_gaps / len(shifted) if shifted else float("nan")
    g_match, g_ctrl = dead_share(odds, graded), dead_share(odds, pre)
    g_gap = dead_share(odds, gap_region & graded)
    covers = coverage >= 0.5
    beats_placebo = coverage >= 2 * coverage_placebo  # False si el placebo es NaN
    instrument = g_ctrl > g_match  # False si alguno es NaN
    looks_dead = instrument and g_gap >= (g_match + g_ctrl) / 2  # False si g_gap es NaN
    m.update(windows=len(results), states={s: sum(r[1] == s for r in results) for s in dead_ball.GAP_STATES},
             by_type=[(kind, len(group), sum(id(w) in gap_ids for w in group))
                      for kind, group in sorted(by_type([r[0] for r in results]).items(),
                                                key=lambda kv: (-len(kv[1]), kv[0]))],
             shifted=len(shifted), placebo_gaps=placebo_gaps, coverage=coverage,
             coverage_placebo=coverage_placebo,
             gap_lengths_s=[(stop - start) / fps for _, _, (start, stop) in with_gap],
             gap_frames=int((gap_region & graded).sum()), g_match=g_match, g_ctrl=g_ctrl, g_gap=g_gap,
             g_first=dead_share(odds, first_seconds & graded),
             g_groups=[(label, sum(w["type"] in kinds for w, _, _ in with_gap),
                        dead_share(odds, group_regions[label] & graded)) for label, kinds in TYPE_GROUPS],
             gap_players=quantiles(players[gap_region & graded]),
             covers=covers, beats_placebo=beats_placebo, instrument=instrument, looks_dead=looks_dead,
             hueco_entra=covers and beats_placebo and looks_dead)
    return m


def main():
    utf8_stdout()
    game = games.GAME
    games.require(["atd_raw", "atd_meta", "smart_tagging"], game)
    paths = games.asset_paths(game)
    started = time.time()
    trk = ball.clean(tracking.from_atd(paths, game))  # el balón como lo ve el pipeline
    events = dead_ball.smart_tagging_events(paths["smart_tagging"], games.GAMES[game]["fps"])
    m = measure(trk, events, game)
    n_graded = m["n_graded"]

    print("1. De cada gol a su saque")
    print("   goles {}   saques tras gol {}   goles que anclan {} de {}".format(
        m["goals"], m["kickoffs"], m["spans"], m["goals"]))
    print("   frames anclados (evaluados), sumados: {} ({} de los evaluados)".format(
        m["anchored_frames"], pct(m["anchored_frames"], n_graded)))
    if m["spans"]:
        print("   duración de los tramos anclados, mediana: {:.0f} s".format(m["span_median_s"]))
    if m["goals"]:
        print("   duración de las ventanas GOALS, mediana: {:.0f} s".format(m["goal_median_s"]))
    print("   anclas duras si entrara la capa (también el tramo antes del saque): {} frames ({} de los"
          " evaluados)   fuera de los evaluados {}".format(m["hard_frames"], pct(m["hard_frames"], n_graded),
                                                           m["hard_outside"]))

    print("\n2. ¿Cada tramo anclado se comporta como balón muerto?")
    print("   balón deprisa (≥ {:g} m/s a 1 s) en el partido: {:.1f} % de los frames con balón visto;"
          " un tramo falla por encima del {:.1f} %".format(FAST_BALL_MS, 100 * m["f_match"], 100 * m["limit"]))
    print("   pruebas: tramo entero, y {} s desde {} s dentro de cada borde; deciden con ≥ {} frames de balón"
          " visto".format(EDGE_S, EDGE_SKIP_S, MIN_SEEN_FRAMES))
    print("   tramos anclados {}   pasan {}   fallan {}   no deciden {}".format(
        m["spans"], m["n_pass"], m["n_fail"], m["spans"] - m["n_pass"] - m["n_fail"]))
    print("   fallos por prueba: tramo entero {}   borde inicial {}   borde final {}".format(*m["fails_by_test"]))
    print("   control (tramo antes del saque de la 2ª parte): {}".format(", ".join(m["control"]) or "no hay"))
    print("   placebo (desplazados {} s): {} tramos, deciden {}, fallan {} ({} de los que deciden)".format(
        "/".join("{:+d}".format(s) for s in PLACEBO_SHIFTS_S), m["placebo"], m["placebo_deciding"],
        m["placebo_fail"], pct(m["placebo_fail"], m["placebo_deciding"])))
    for r in m["regions"]:
        print("   {:<46} {:>7} frames   balón visto {}   deprisa {} de los vistos".format(
            r["label"], r["frames"], r["seen"], r["fast"]))
        print("   {:<46} jugadores (m/s) {}   modelo de Ana: D en el {}".format("", r["players"], r["ana"]))
    print("   regla: el control pasa {}   el placebo tiene potencia {}   ningún tramo falla y la mitad o más"
          " pasan {}   -> la capa entra: {}".format(yes(m["control_ok"]), yes(m["power"]), yes(m["spans_ok"]),
                                                     yes(m["gol_entra"])))

    print("\n3. Equipo de los SET PIECES frente a los nombres de los metadatos del ATD")
    home, away = (norm(name) for name in team_names(paths["atd_meta"]))
    set_pieces = [e for e in load_smart_tagging.load(game) if norm(e["code"]) == SET_PIECES_CODE]
    teams = [norm({norm(k): v for k, v in e["tags"].items()}.get("team")) for e in set_pieces]
    with_team = [t for t in teams if t not in ("", "n/a")]
    print("   SET PIECES {}   con equipo {}   igual al local {}   igual al visitante {}   sin coincidir {}".format(
        len(set_pieces), len(with_team), sum(t == home for t in with_team), sum(t == away for t in with_team),
        sum(t not in (home, away) for t in with_team)))

    print("\n4. El hueco sin balón antes de cada reinicio (no se cuentan los saques iniciales)")
    print("   ventanas que empiezan en frames evaluados: {}".format(m["windows"]))
    print("   " + "   ".join("{} {} ({})".format(state, k, pct(k, m["windows"]))
                             for state, k in m["states"].items()))
    for kind, n, k in m["by_type"]:
        print("      {:<22} n={:>3}   con hueco {} ({})".format(kind, n, k, pct(k, n)))
    print("   placebo (inicios desplazados {} s): {} inicios, con hueco {} ({})".format(
        "/".join("{:+d}".format(s) for s in PLACEBO_SHIFTS_S), m["shifted"], m["placebo_gaps"],
        pct(m["placebo_gaps"], m["shifted"])))
    print_bins("duración de los huecos", m["gap_lengths_s"], GAP_LENGTH_EDGES_S, indent="   ")
    print("   frames de hueco (evaluados), sumados: {} ({} de los evaluados)".format(
        m["gap_frames"], pct(m["gap_frames"], n_graded)))
    print("   modelo de Ana, D en: partido {}   control {}   punto medio {}   huecos {}   primeros {} s de los"
          " huecos {}".format(share(m["g_match"]), share(m["g_ctrl"]), share((m["g_match"] + m["g_ctrl"]) / 2),
                              share(m["g_gap"]), EDGE_S, share(m["g_first"])))
    print("   modelo de Ana en los huecos, por grupo (descriptivo): " + "   ".join(
        "{} (n={}) {}".format(label, n, share(g)) for label, n, g in m["g_groups"]))
    print("   jugadores (m/s) en los huecos: {}".format(m["gap_players"]))
    print("   regla: cobertura ≥ 50 % {}   ≥ 2 veces el placebo {}   el modelo de Ana separa el control del"
          " partido {}   huecos ≥ punto medio {}   -> la capa entra: {}".format(
              yes(m["covers"]), yes(m["beats_placebo"]), yes(m["instrument"]), yes(m["looks_dead"]),
              yes(m["hueco_entra"])))

    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
