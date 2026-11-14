"""Agregados del partido para las anclas de possession/dead_ball.py. Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: recuentos, porcentajes y cuantiles, sin números de frame ni jugadas sueltas.
Los goles van siempre juntos: con 4, cualquier desglose identifica cada parada.

    python validation/partido/agregados_dead_ball.py

Responde a (docs/decisiones.md, 14/11, «fronteras y anclas»):
1. Cuántos goles anclan en la capa «de cada gol a su saque» y cuántos frames suman.
2. Si lo anclado se comporta como balón muerto: cuánto se ve el balón y cuánto se mueve deprisa ahí
   dentro, frente al partido entero y frente al tramo antes del saque de la 2ª parte, que el FAQ da
   como `D`. También la velocidad media de los jugadores.
3. Para la capa del equipo que reanuda: cuántos `SET PIECES` traen equipo y cuántos coinciden con el
   nombre del local o del visitante de los metadatos del ATD.
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import (FPS, SET_PIECES_CODE, graded_mask, mean_speed, moving_average, norm, pct,  # noqa: E402
                   quantiles, utf8_stdout)
from possession import dead_ball  # noqa: E402
from possession.io import load_ball, load_players  # noqa: E402
from starter import load_smart_tagging  # noqa: E402
from starter.baseline import team_names  # noqa: E402

# Balón «deprisa»: desplazamiento suavizado a 1 s de 5 m/s o más. Fijado antes de medir
# (docs/decisiones.md, 14/11); el suavizado es el del agregado 5 de agregados_balon_reinicios.py.
FAST_BALL_MS = 5.0
SMOOTH_HALF_WIDTH = 12  # ±0,5 s
PLAYERS_HALF_WIDTH = FPS  # ±1 s, como en agregados_jugadores.py


def ball_speed(x, y):
    """Desplazamiento del balón suavizado a 1 s, en m/s; NaN donde no se ve."""
    h = SMOOTH_HALF_WIDTH
    sx, sy = moving_average(x, h), moving_average(y, h)
    v = np.full(len(x), np.nan)
    v[h:-h] = np.hypot(sx[2 * h:] - sx[:-2 * h], sy[2 * h:] - sy[:-2 * h]) / (2.0 * h / FPS)
    v[np.isnan(x)] = np.nan
    return v


def describe(label, region, visible, fast, players):
    n = int(region.sum())
    seen = int((region & visible).sum())
    quick = int((region & fast).sum())
    print("   {:<44} {:>7} frames   balón visto {}   deprisa {} de los vistos   jugadores {}".format(
        label, n, pct(seen, n), pct(quick, seen), quantiles(players[region])))


def main():
    utf8_stdout()
    game = games.GAME
    entry = games.GAMES[game]
    n_frames, pitch, fps = entry["n_video_frames"], entry["pitch"], entry["fps"]
    games.require(["atd_raw", "atd_meta", "smart_tagging"], game)
    paths = games.asset_paths(game)
    started = time.time()
    x, y, _ = load_ball(paths["atd_raw"], n_frames, pitch)
    px, py = load_players(paths["atd_raw"], n_frames, pitch)
    graded = graded_mask(game, n_frames)
    events = dead_ball.smart_tagging_events(paths["smart_tagging"], fps)

    print("1. De cada gol a su saque")
    goals = [e for e in events if e["code"] == dead_ball.GOALS_CODE]
    kickoffs = [e for e in events if e["code"] == dead_ball.SET_PIECES_CODE
                and e["type"] == dead_ball.AFTER_GOAL_KICKOFF]
    spans = dead_ball.goal_to_kickoff(events, fps)
    anchored = np.zeros(n_frames, dtype=bool)
    for start, stop in spans:
        anchored[max(start, 0):max(min(stop, n_frames), 0)] = True
    n_graded = int(graded.sum())
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
    mask = dead_ball.dead_mask(paths, game)
    n_mask = int((mask & graded).sum())
    print("   todas las anclas duras (también el tramo antes del saque): {} frames ({} de los evaluados)"
          "   fuera de los evaluados {}".format(n_mask, pct(n_mask, n_graded), int((mask & ~graded).sum())))

    print("\n2. ¿Se comporta como balón muerto? (balón deprisa: ≥ {:g} m/s a 1 s; jugadores: m/s, media de 2 s)"
          .format(FAST_BALL_MS))
    visible = ~np.isnan(x)
    fast = visible & (ball_speed(x, y) >= FAST_BALL_MS)
    players = moving_average(mean_speed(px, py), PLAYERS_HALF_WIDTH)
    describe("partido entero (evaluados)", graded, visible, fast, players)
    describe("tramo antes del saque de la 2ª parte (D, FAQ)", dead_ball.pre_kickoff(game) & graded,
             visible, fast, players)
    describe("de gol a saque (anclado)", anchored & graded, visible, fast, players)

    print("\n3. Equipo de los SET PIECES frente a los nombres de los metadatos del ATD")
    home, away = (norm(name) for name in team_names(paths["atd_meta"]))
    set_pieces = [e for e in load_smart_tagging.load(game) if norm(e["code"]) == SET_PIECES_CODE]
    teams = [norm(e["tags"].get("Team")) for e in set_pieces]
    with_team = [t for t in teams if t not in ("", "n/a")]
    print("   SET PIECES {}   con equipo {}   igual al local {}   igual al visitante {}   sin coincidir {}".format(
        len(set_pieces), len(with_team), sum(t == home for t in with_team), sum(t == away for t in with_team),
        sum(t not in (home, away) for t in with_team)))

    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
