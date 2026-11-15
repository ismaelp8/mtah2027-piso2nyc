"""Agregados del partido para la capa del equipo que reanuda (possession/dead_ball.py). Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: recuentos y porcentajes, sin números de frame ni jugadas sueltas. Los tipos de
reinicio se desglosan solo con 5 casos o más.

    python validation/partido/agregados_equipo_reanuda.py

Responde, con la regla apuntada en docs/decisiones.md (15/11, «el equipo que reanuda») antes de ejecutarlo:
1. Si el `Team` del Smart Tagging es el equipo que saca: en córners y saques de puerta, con la física
   (en qué fondo estaba el balón antes de la ventana y qué lado defiende cada equipo), sin etiquetas.
2. Si la capa aporta algo: con qué equipo sale el pipeline de cada parada, sin la capa y con ella, frente
   al `Team`.
3. Si la capa hace daño: paradas y posesiones, sin la capa y con ella, y qué frames cambian.

`measure_teams` y las funciones de la regla no abren ningún fichero; los importa
validation/scripts/comprobar_balon_muerto.py (sección 10), que ejecuta Claude con un partido inventado y
con la apertura de ficheros prohibida. `measure_teams` llama al pipeline con la evidencia `anchors` que le
pasa quien llama: en `main`, la de dead_ball con las rutas del partido. Solo `main` lee el partido.
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import MIN_CASES_PER_TYPE, graded_mask, pct, utf8_stdout  # noqa: E402
from possession import dead_ball, pipeline, tracking  # noqa: E402
from starter.baseline import team_names  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
# Todo fijado antes de medir (docs/decisiones.md, 15/11).
# El punto del reinicio es el último balón visto antes del inicio de la ventana, con esta antigüedad como
# mucho (el tope de la capa del hueco, dead_ball.MAX_GAP_BEFORE_RESTART_S).
MAX_AGE_S = dead_ball.MAX_GAP_BEFORE_RESTART_S
# Decide si cae a un cuarto del largo o más de la línea de medio campo (el cuarto final de un lado).
QUARTER = 0.25
MIN_AGREEMENT = 0.9  # condición 1: coinciden el 90 % o más de las que deciden
MIN_DECIDING = 10  # y deciden 10 o más
# Qué equipo saca, según el fondo del reinicio: en un córner, el que ataca ese lado; en un saque de
# puerta, el que lo defiende (reglas 17 y 16).
CHECKED = {"corner kick": "ataca", "goal kick": "defiende"}
AGREE, DISAGREE, NO_BALL, NOT_IN_QUARTER = "coincide", "no coincide", "sin balón visto", "fuera del cuarto final"
CHECK_STATES = (AGREE, DISAGREE, NO_BALL, NOT_IN_QUARTER)
SAME, OTHER, NO_STOP, NO_EXIT = "el del Team", "el otro", "sin parada", "sin salida"
EXIT_STATES = (SAME, OTHER, NO_STOP, NO_EXIT)


def other(team):
    return A if team == H else H


def half_of(frame, blocks):
    """Número de la parte (1, 2, …) cuyo tramo evaluado contiene `frame`; None si ninguno."""
    for half, (first, stop) in enumerate(blocks, 1):
        if first <= frame < stop:
            return half
    return None


def left_defender(trk):
    """({parte: equipo (H o A) que defiende el lado izquierdo, el de x pequeña}, {parte: separación en m}):
    el de menor media de la x de sus jugadores en los frames evaluados de esa parte. Da error si falta un
    equipo en una parte."""
    out, gaps = {}, {}
    for half, (first, stop) in enumerate(trk.blocks, 1):
        means = [np.nanmean(trk.px[first:stop][:, trk.team == team]) if np.any(trk.team == team) else np.nan
                 for team in (H, A)]
        if np.isnan(means).any():
            raise ValueError("en la parte {} no hay jugadores de los dos equipos".format(half))
        out[half] = H if means[0] < means[1] else A
        gaps[half] = abs(means[1] - means[0])
    return out, gaps


def restart_spot(last_seen, bx, by, window, fps):
    """(x, y) del último balón visto antes del inicio de la ventana; None si no hay o si es más antiguo que
    MAX_AGE_S. `last_seen` es dead_ball.last_seen_before(bx, by)."""
    start = window["start"]
    if start <= 0:
        return None
    seen = int(last_seen[start - 1])
    if seen < 0 or start - seen > MAX_AGE_S * fps:
        return None
    return float(bx[seen]), float(by[seen])


def physics_check(spot, kind, team, half, left, length):
    """Estado de una ventana de córner o saque de puerta (`kind`) frente a su `Team` (`team`, H o A)."""
    if spot is None:
        return NO_BALL
    if abs(spot[0] - length / 2) < QUARTER * length:
        return NOT_IN_QUARTER
    defender = left[half] if spot[0] < length / 2 else other(left[half])
    expected = defender if CHECKED[kind] == "defiende" else other(defender)
    return AGREE if expected == team else DISAGREE


def exit_team(codes, start, end, block_stop):
    """(equipo, frame) con los que el pipeline sale de la última parada de la ventana [start, end): el primer
    H o A después del último D de la ventana, buscado hasta el fin del tramo. (None, None) si la ventana no
    tiene ningún D o si no sale antes del fin del tramo."""
    dead = np.flatnonzero(codes[start:end] == D)
    if dead.size == 0:
        return None, None
    first = start + int(dead[-1]) + 1
    play = np.flatnonzero(codes[first:block_stop] != D)
    if play.size == 0:
        return None, None
    frame = first + int(play[0])
    return int(codes[frame]), frame


def exit_state(codes, window, team, block_stop):
    """(estado frente al `Team`, ¿se sale con el equipo del `Team` y después, dentro de la ventana, aparece
    el otro?). Lo segundo es el riesgo de la capa: un cambio al otro equipo que la capa podría retrasar."""
    dead = np.flatnonzero(codes[window["start"]:window["end"]] == D)
    if dead.size == 0:
        return NO_STOP, False
    exit_code, frame = exit_team(codes, window["start"], window["end"], block_stop)
    if exit_code is None:
        return NO_EXIT, False
    later = exit_code == team and bool(np.any(codes[frame:window["end"]] == other(team)))
    return (SAME if exit_code == team else OTHER), later


def runs(codes, blocks):
    """(posesiones, paradas) en los tramos evaluados."""
    possessions = stops = 0
    for first, stop in blocks:
        window = codes[first:stop]
        kinds = window[np.flatnonzero(np.concatenate(([True], window[1:] != window[:-1])))]
        possessions += int(np.sum(kinds != D))
        stops += int(np.sum(kinds == D))
    return possessions, stops


def changes(without, with_layer, graded):
    """Frames evaluados que cambian, por tipo: (de un equipo al otro, de juego a D, de D a juego)."""
    play_before, play_after = without != D, with_layer != D
    team = graded & play_before & play_after & (without != with_layer)
    to_dead = graded & play_before & ~play_after
    to_play = graded & ~play_before & play_after
    return int(team.sum()), int(to_dead.sum()), int(to_play.sum())


def physics_rule(agree, deciding):
    """Condición 1: deciden MIN_DECIDING o más y coinciden MIN_AGREEMENT o más de las que deciden."""
    return deciding >= MIN_DECIDING and agree >= MIN_AGREEMENT * deciding


def contributes_rule(other_without, other_with):
    """Condición 2: sin la capa se sale con el otro equipo en al menos una ventana, y con ella en menos."""
    return other_without >= 1 and other_with < other_without


def harm_rule(runs_without, runs_with):
    """Condición 3: con la capa, ni más posesiones ni más paradas en los tramos evaluados."""
    return runs_with[0] <= runs_without[0] and runs_with[1] <= runs_without[1]


def measure_teams(trk, events, home, away, anchors, game=games.GAME, pieces=None):
    """Las cuentas de las tres secciones y la regla aplicada. No abre ningún fichero por sí misma.

    `trk` es el tracking sin limpiar (el pipeline lo limpia); `events`, los de
    dead_ball.smart_tagging_events; `home` y `away`, los nombres de los metadatos del ATD; `anchors`, la
    evidencia de dead_ball que va siempre en la entrega (una función del tracking limpio). `pieces` cambia
    piezas del pipeline (pipeline.run); en el partido es None, y van las de la entrega.
    """
    n = len(trk.bx)
    length = trk.pitch[0]
    fps = trk.fps
    graded = graded_mask(game, n)
    clean = pipeline.default_piece("ball")(trk) if not pieces or "ball" not in pieces else pieces["ball"](trk)
    teams = [(w, t) for w, t in dead_ball.restart_teams(events, home, away) if half_of(w["start"], trk.blocks)]
    m = {"windows": len(teams), "by_type": {}}
    for window, _ in teams:
        m["by_type"][window["type"]] = m["by_type"].get(window["type"], 0) + 1
    left, separation = left_defender(clean)
    m.update(left_defender=left, separation=separation)

    # 1. El Team es el equipo que saca
    last_seen = dead_ball.last_seen_before(clean.bx, clean.by)
    checks = {kind: {state: 0 for state in CHECK_STATES} for kind in CHECKED}
    for window, team in teams:
        if window["type"] in CHECKED:
            spot = restart_spot(last_seen, clean.bx, clean.by, window, fps)
            state = physics_check(spot, window["type"], team, half_of(window["start"], trk.blocks), left, length)
            checks[window["type"]][state] += 1
    agree = sum(c[AGREE] for c in checks.values())
    deciding = agree + sum(c[DISAGREE] for c in checks.values())
    m.update(checks=checks, agree=agree, deciding=deciding, physics_ok=physics_rule(agree, deciding))

    # 2 y 3. Con qué equipo se sale de cada parada, y el daño
    layer = lambda c: dead_ball.team_restart_evidence(c, events, home, away)  # noqa: E731
    reports = ({}, {})
    without = pipeline.run(trk, extra=[anchors], report=reports[0], pieces=pieces)
    with_layer = pipeline.run(trk, extra=[anchors, layer], report=reports[1], pieces=pieces)
    exits = []
    for codes in (without, with_layer):
        states, later = {state: 0 for state in EXIT_STATES}, []
        for window, team in teams:
            stop = trk.blocks[half_of(window["start"], trk.blocks) - 1][1]
            state, appears = exit_state(codes, window, team, stop)
            states[state] += 1
            later.append(appears)
        exits.append((states, later))
    m.update(conflicts=(reports[0]["conflictos"], reports[1]["conflictos"]),
             exits=(exits[0][0], exits[1][0]),
             changed=changes(without, with_layer, graded),
             runs=(runs(without, trk.blocks), runs(with_layer, trk.blocks)),
             later=(sum(exits[0][1]), sum(exits[1][1])),
             later_removed=sum(a and not b for a, b in zip(exits[0][1], exits[1][1])))
    m["contributes"] = contributes_rule(m["exits"][0][OTHER], m["exits"][1][OTHER])
    m["harm_ok"] = harm_rule(*m["runs"])
    m["entra"] = m["physics_ok"] and m["contributes"] and m["harm_ok"]
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
    home, away = team_names(paths["atd_meta"])
    anchors = lambda clean: dead_ball.evidence(clean, paths, game)  # noqa: E731
    m = measure_teams(trk, events, home, away, anchors, game)

    print("limpieza del balón: ball.{} (pipeline.PIECES)".format(pipeline.PIECES["ball"]))
    print("\n1. ¿El Team es el equipo que saca? (física, sin etiquetas)")
    shown = {kind: k for kind, k in m["by_type"].items() if k >= MIN_CASES_PER_TYPE}
    rest = sum(k for kind, k in m["by_type"].items() if kind not in shown)
    kinds = "   ".join("{} {}".format(kind, k) for kind, k in sorted(shown.items()))
    print("   ventanas con el Team de un equipo, en lo evaluado: {}   {}{}".format(
        m["windows"], kinds, "   otros {}".format(rest) if rest else ""))
    print("   lado izquierdo (x pequeña), lo defiende: " + "   ".join(
        "parte {}: {} (medias de x separadas {:.1f} m)".format(
            half, "el local" if team == H else "el visitante", m["separation"][half])
        for half, team in sorted(m["left_defender"].items())))
    for kind, states in m["checks"].items():
        n_kind = sum(states.values())
        if n_kind >= MIN_CASES_PER_TYPE:
            print("   {:<14} ".format(kind) + "   ".join("{} {}".format(s, k) for s, k in states.items()))
    print("   córner y saque de puerta juntos: coinciden {} de {} que deciden ({})".format(
        m["agree"], m["deciding"], pct(m["agree"], m["deciding"])))
    print("   regla: deciden ≥ {} y coinciden ≥ {:.0f} % -> se cumple: {}".format(
        MIN_DECIDING, 100 * MIN_AGREEMENT, yes(m["physics_ok"])))

    print("\n2. ¿Aporta algo? Equipo con el que sale el pipeline de la parada de cada ventana, frente al Team")
    print("   frames con piezas en conflicto: sin la capa {}   con ella {}".format(*m["conflicts"]))
    for label, states in zip(("sin la capa", "con la capa"), m["exits"]):
        print("   {:<12} ".format(label) + "   ".join("{} {}".format(s, k) for s, k in states.items()))
    print("   regla: sin la capa sale con el otro en ≥ 1 y con ella en menos -> se cumple: {}".format(
        yes(m["contributes"])))

    print("\n3. ¿Hace daño?")
    print("   posesiones y paradas: sin la capa {} y {}   con ella {} y {}".format(*m["runs"][0], *m["runs"][1]))
    print("   frames evaluados que cambian: de un equipo al otro {}   de juego a D {}   de D a juego {}".format(
        *m["changed"]))
    print("   ventanas que salen con el del Team y cambian al otro dentro: sin la capa {}   con ella {}"
          "   las que quita la capa {}".format(*m["later"], m["later_removed"]))
    print("   regla: con la capa, ni más posesiones ni más paradas -> se cumple: {}".format(yes(m["harm_ok"])))

    print("\n-> la capa entra: {}".format(yes(m["entra"])))
    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
