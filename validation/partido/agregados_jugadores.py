"""Agregados de los jugadores del ATD para el detector de `D`. Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: cuantiles y porcentajes del partido entero o por tipo de reinicio (5 casos o
más), sin números de frame ni jugadas sueltas.

    python validation/partido/agregados_jugadores.py

Responde a (sección 7 de validation/resultados/2026-11-13_revision_balon_muerto.md, agregados 4 y 6):
4. Cómo se reparte la velocidad media de los jugadores en el ATD, en todo el partido, en los 10 s
   anteriores a cada reinicio, en los 5 s posteriores, en los 30 s iniciales del bloque evaluado de la
   2ª parte (que el FAQ da como `D`) y en los 30 s finales de cada bloque. Se compara con la DFL, donde
   el modelo de estado de `D` con jugadores se entrenaría. Dice si ese modelo se traslada al ATD y si
   el final de cada parte parece balón muerto.
6. Cuántos jugadores aparecen fuera de los límites del campo y si eso ocurre en los saques de banda.
   Decide si el jugador fuera de la banda sirve para saber qué equipo saca.
"""

import os
import sys
import time
import warnings

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import (FPS, SET_PIECES_CODE, graded_mask, grouped_by_type, mean_speed, moving_average,  # noqa: E402
                   norm, pct, quantiles, slot_speeds, utf8_stdout)
from possession.io import load_players  # noqa: E402
from starter import load_smart_tagging  # noqa: E402
from starter.baseline import team_of_each_track  # noqa: E402

SMOOTH_HALF_WIDTH = FPS  # ±1 s: la misma ventana de 2 s que se usó en la DFL
BEFORE_S, AFTER_S, EDGE_S = 10, 5, 30
LOOKBACK_S = 5  # las ventanas de reinicio se miran desde 5 s antes de su inicio (sección 6)
SLOW_MS = 1.2  # por debajo de esto la media de la DFL durante el D (p50 1,02) queda dentro; en juego (p10 1,38) fuera
OUTSIDE_MARGIN_M = 0.3
# Referencia medida en los 7 partidos de la DFL (validation/resultados/2026-11-11_experimento0.md):
# velocidad media de los jugadores p10 / p50 / p90, en D y en juego.
DFL_REFERENCE = {"D": (0.53, 1.02, 1.69), "juego": (1.38, 2.27, 3.62)}


def window(start, end, n):
    return slice(max(0, min(start, n)), max(0, min(end, n)))


def describe(label, values):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    slow = pct(int(np.sum(values < SLOW_MS)), values.size)
    print("   {:<58} {:>7} frames   {}   < {:g} m/s {}".format(label, values.size, quantiles(values), SLOW_MS, slow))


def main():
    utf8_stdout()
    game = games.GAME
    entry = games.GAMES[game]
    n_frames, pitch = entry["n_video_frames"], entry["pitch"]
    length, width = pitch
    atd_raw, atd_meta = games.require(["atd_raw", "atd_meta", "smart_tagging"], game)[:2]
    started = time.time()
    px, py = load_players(atd_raw, n_frames, pitch)
    team = team_of_each_track(atd_meta)
    if team.size != px.shape[1]:
        sys.exit("El XML tiene {} slots y el ATD {}.".format(team.size, px.shape[1]))
    events = load_smart_tagging.load(game)
    graded = graded_mask(game, n_frames)
    blocks = games.half_video_blocks(game)
    by_type = grouped_by_type(events)
    set_pieces = [e for e in events if norm(e["code"]) == SET_PIECES_CODE]

    v = moving_average(mean_speed(px, py), SMOOTH_HALF_WIDTH)
    tracked = np.sum(~np.isnan(px), axis=1)

    print("4. Velocidad media de los jugadores (m/s, media móvil de 2 s)")
    print("   slots vistos por frame en los evaluados: {}".format(quantiles(tracked[graded])))
    print("   referencia DFL (7 partidos)  en D p10/p50/p90 = {} / {} / {}   en juego = {} / {} / {}".format(
        *(DFL_REFERENCE["D"] + DFL_REFERENCE["juego"])))
    describe("todos los frames evaluados", v[graded])
    for half, first, last in blocks:
        describe("parte {}: 30 s iniciales del bloque evaluado".format(half), v[window(first, first + EDGE_S * FPS, n_frames)])
        describe("parte {}: 30 s finales del bloque evaluado".format(half), v[window(last - EDGE_S * FPS, last + 1, n_frames)])
    pooled_before, pooled_after = [], []
    for kind, group in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        before = np.concatenate([v[window(e["start_frame"] - BEFORE_S * FPS, e["start_frame"], n_frames)] for e in group])
        after = np.concatenate([v[window(e["end_frame"], e["end_frame"] + AFTER_S * FPS, n_frames)] for e in group])
        pooled_before.append(before)
        pooled_after.append(after)
        describe("{} (n={}): {} s antes de la ventana".format(kind, len(group), BEFORE_S), before)
        describe("{} (n={}): {} s después de la ventana".format(kind, len(group), AFTER_S), after)
    describe("todos los reinicios: {} s antes de la ventana".format(BEFORE_S), np.concatenate(pooled_before))
    describe("todos los reinicios: {} s después de la ventana".format(AFTER_S), np.concatenate(pooled_after))
    speeds = slot_speeds(px, py)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # comparar NaN con un número avisa; el NaN no cuenta
        slow_fraction = np.sum(speeds < 1.0, axis=1) / np.maximum(np.sum(~np.isnan(speeds), axis=1), 1)
    slow_fraction = moving_average(slow_fraction, SMOOTH_HALF_WIDTH)
    print("   fracción de jugadores a menos de 1 m/s (media de 2 s), en los evaluados: {}".format(quantiles(slow_fraction[graded])))

    print("\n6. Jugadores fuera de los límites del campo (más de {:g} m)".format(OUTSIDE_MARGIN_M))
    out_x = (px < -OUTSIDE_MARGIN_M) | (px > length + OUTSIDE_MARGIN_M)
    out_y = (py < -OUTSIDE_MARGIN_M) | (py > width + OUTSIDE_MARGIN_M)
    n_out = np.sum(out_x | out_y, axis=1)
    n_graded = int(graded.sum())
    for k, label in ((0, "ninguno"), (1, "uno"), (2, "dos")):
        n = int(np.sum(n_out[graded] == k))
        print("   frames evaluados con {} jugador(es) fuera: {:>7} ({})".format(label, n, pct(n, n_graded)))
    n = int(np.sum(n_out[graded] >= 3))
    print("   frames evaluados con tres o más fuera:       {:>7} ({})".format(n, pct(n, n_graded)))
    print("   de los frames con alguno fuera: por banda {}   por fondo {}".format(
        pct(int(np.sum(out_y.any(axis=1) & graded)), int(np.sum((n_out > 0) & graded))),
        pct(int(np.sum(out_x.any(axis=1) & graded)), int(np.sum((n_out > 0) & graded)))))
    for kind, group in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        with_outside, frames_outside = 0, []
        for e in group:
            w = window(e["start_frame"] - LOOKBACK_S * FPS, e["end_frame"], n_frames)
            count = int(np.sum(n_out[w] > 0))
            with_outside += count > 0
            frames_outside.append(count / FPS)
        print("   {:<22} n={:>3}   ventanas (desde {} s antes) con algún jugador fuera {} ({})   segundos con alguien fuera por ventana {}".format(
            kind, len(group), LOOKBACK_S, with_outside, pct(with_outside, len(group)), quantiles(frames_outside)))

    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
