"""Diagnóstico de las coordenadas y del temblor del balón en el ATD del partido.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). Solo
imprime agregados del partido entero (los saques iniciales, todos juntos): cuantiles, recuentos y
porcentajes, sin números de frame ni jugadas sueltas.

    python validation/partido/diagnostico_coordenadas.py

Responde a dos preguntas:
1. ¿Separa x = 0,5 a los dos equipos? Antes de un saque inicial cada equipo está entero en su mitad
   (reglamento), así que si x = 0,5 es la línea de medio campo los equipos ocupan lados opuestos.
2. ¿Cuánto tiembla el balón y se llega a ver quieto varios segundos?

Resultado y lectura en validation/resultados/2026-11-12_balon_muerto_atd.md.
"""

import os
import sys
import time
from collections import Counter

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import (CENTRE_RADIUS_M, FPS, KICKOFF_TYPES, MAX_GAP_FRAMES, SET_PIECES_CODE,  # noqa: E402
                   graded_mask, norm, pct, utf8_stdout)
from possession.io import load_ball, load_players  # noqa: E402
from starter import load_smart_tagging  # noqa: E402
from starter.baseline import team_of_each_track  # noqa: E402

QUANTILES = (0.5, 5, 50, 95, 99.5)
JUMP_QUANTILES = (10, 25, 50, 75, 90, 99)
BEFORE_KICKOFF = FPS  # 1 s antes del inicio de la etiqueta del saque
STILL_RADII_M = (0.5, 1.0, 2.0)
STILL_DURATIONS_S = (1, 3, 10)
TEAM_NAMES = ("local (H)", "visitante (A)")


def quantile_row(values, quantiles):
    values = values[~np.isnan(values)]
    if values.size == 0:
        return "sin datos"
    return "   ".join("p{}={:.3f}".format(q, v) for q, v in zip(quantiles, np.percentile(values, quantiles)))


def still_runs(x, y, first, last, radius):
    """Duración en frames, del primer al último frame con balón, de cada tramo de [first, last] en que
    el balón está a menos de `radius` del primer punto del tramo. Un hueco sin balón de hasta
    MAX_GAP_FRAMES no corta el tramo; uno más largo, sí."""
    lengths = []
    anchor = start = end = None
    gap = 0
    for frame in range(first, last + 1):
        if np.isnan(x[frame]):
            gap += 1
            if anchor is not None and gap > MAX_GAP_FRAMES:
                lengths.append(end - start + 1)
                anchor = None
            continue
        gap = 0
        if anchor is not None and np.hypot(x[frame] - anchor[0], y[frame] - anchor[1]) <= radius:
            end = frame
            continue
        if anchor is not None:
            lengths.append(end - start + 1)
        anchor, start, end = (x[frame], y[frame]), frame, frame
    if anchor is not None:
        lengths.append(end - start + 1)
    return lengths


def main():
    utf8_stdout()
    game = games.GAME
    entry = games.GAMES[game]
    n_frames, pitch = entry["n_video_frames"], entry["pitch"]
    length, width = pitch
    centre = np.array([length / 2, width / 2])
    atd_raw, atd_meta = games.require(["atd_raw", "atd_meta", "smart_tagging"], game)[:2]

    started = time.time()
    ball_x, ball_y, ball_speed = load_ball(atd_raw, n_frames, pitch)
    players_x, players_y = load_players(atd_raw, n_frames, pitch)
    team = team_of_each_track(atd_meta)
    if team.size != players_x.shape[1]:
        sys.exit("El XML tiene {} slots y el ATD {}: no se puede saber el equipo de cada slot.".format(
            team.size, players_x.shape[1]))
    events = load_smart_tagging.load(game)
    graded = graded_mask(game, n_frames)

    print("1. Coordenadas normalizadas (0–1) en los frames evaluados")
    print("   balón x      ", quantile_row(ball_x[graded] / length, QUANTILES))
    print("   balón y      ", quantile_row(ball_y[graded] / width, QUANTILES))
    print("   jugadores x  ", quantile_row(players_x[graded].ravel() / length, QUANTILES))
    print("   jugadores y  ", quantile_row(players_y[graded].ravel() / width, QUANTILES))
    seen = graded & ~np.isnan(ball_x)
    near = seen & (np.hypot(ball_x - centre[0], ball_y - centre[1]) <= CENTRE_RADIUS_M)
    print("   frames con el balón a menos de {:g} m de (0,5; 0,5): {} ({} de los vistos)".format(
        CENTRE_RADIUS_M, int(near.sum()), pct(int(near.sum()), int(seen.sum()))))

    print("\n2. En el segundo anterior al inicio de cada etiqueta de saque inicial, todas juntas")
    kickoffs = [event for event in events if norm(event["code"]) == SET_PIECES_CODE
                and norm(event["tags"].get("Type")) in KICKOFF_TYPES]
    own_half, observed_total, opposite = Counter(), Counter(), 0
    for event in kickoffs:
        window = slice(max(event["start_frame"] - BEFORE_KICKOFF, 0), max(event["start_frame"], 0))
        sides = []
        for code in range(len(TEAM_NAMES)):
            px = players_x[window][:, team == code] / length
            observed = px[~np.isnan(px)]
            # La mitad de cada equipo es el lado de x = 0,5 donde está la mayoría de sus jugadores.
            left = bool(observed.size) and bool(np.mean(observed < 0.5) >= 0.5)
            sides.append(left if observed.size else None)
            own_half[code] += int((observed < 0.5).sum() if left else (observed >= 0.5).sum())
            observed_total[code] += observed.size
        opposite += None not in sides and sides[0] != sides[1]
    print("   saques iniciales: {}   con los dos equipos a lados opuestos de x = 0,5: {} de {}".format(
        len(kickoffs), opposite, len(kickoffs)))
    for code, name in enumerate(TEAM_NAMES):
        print("   {:<14} jugadores vistos por frame {:4.1f}   en su lado: {}".format(
            name, observed_total[code] / (BEFORE_KICKOFF * len(kickoffs)) if kickoffs else 0.0,
            pct(own_half[code], observed_total[code])))

    print("\n3. Temblor del balón entre frames seguidos, los dos con balón, en los evaluados")
    both = graded[:-1] & graded[1:] & ~np.isnan(ball_x[:-1]) & ~np.isnan(ball_x[1:])
    jump = np.hypot(np.diff(ball_x), np.diff(ball_y))[both]
    print("   pares de frames {}".format(int(both.sum())))
    print("   salto (m)              ", quantile_row(jump, JUMP_QUANTILES))
    print("   salto × 25 (m/s)       ", quantile_row(jump * FPS, JUMP_QUANTILES))
    print("   velocidad del ATD      ", quantile_row(ball_speed[graded], JUMP_QUANTILES))

    print("\n4. Tramos con el balón quieto en los evaluados (cada parte por separado; un hueco sin")
    print("   balón de hasta {:g} s no corta el tramo)".format(MAX_GAP_FRAMES / FPS))
    n_graded = int(graded.sum())
    for radius in STILL_RADII_M:
        runs = np.array([run for _, first, last in games.half_video_blocks(game)
                         for run in still_runs(ball_x, ball_y, first, last, radius)])
        counts = "   ".join("≥{} s: {:>4}".format(seconds, int((runs >= seconds * FPS).sum()))
                           for seconds in STILL_DURATIONS_S)
        long_frames = int(runs[runs >= 3 * FPS].sum())
        print("   radio {} m   {}   frames en tramos ≥3 s: {} ({} de los evaluados)".format(
            radius, counts, long_frames, pct(long_frames, n_graded)))

    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
