"""Agregados del balón del ATD alrededor de los reinicios, para el detector de `D`. Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: recuentos y porcentajes por tipo de reinicio (5 casos o más; los saques
iniciales siempre juntos) en intervalos gruesos, sin números de frame ni jugadas sueltas.

    python validation/partido/agregados_balon_reinicios.py

Responde a (sección 7 de validation/resultados/2026-11-13_revision_balon_muerto.md, agregados 2, 3 y 5):
2. Las "reanudaciones" que encuentra el detector de golpeo de diagnostico_balon_muerto.py (balón visto
   quieto que empieza a moverse), ¿caen donde acaba la ventana `SET PIECES`, donde empieza la primera
   fase posterior y donde sube la velocidad media de los jugadores? Si las tres señales independientes
   coinciden con ellas, son los reinicios reales y sirven para fechar el fin del `D`.
3. El balón que desaparece saliendo del campo: huecos largos sin balón cuyo último punto visto está
   junto a una línea y se mueve hacia fuera. ¿Cuántos hay, cuántos van seguidos de un `SET PIECE` y
   qué fracción de los saques de banda, córners y saques de puerta tiene uno justo antes? Decide el
   disparo del inicio del `D`.
5. La columna de velocidad del balón del ATD frente al desplazamiento suavizado a 0,5 y 1 s. Si se
   parece a la velocidad suavizada, se puede usar; si no, no.
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import (FPS, GOALS_CODE, SET_PIECES_CODE, graded_mask, grouped_by_type, mean_speed,  # noqa: E402
                   moving_average, norm, pct, print_bins, quantiles, utf8_stdout)
from diagnostico_balon_muerto import find_strike  # noqa: E402
from possession.io import load_ball, load_players  # noqa: E402
from starter import load_smart_tagging  # noqa: E402

# 2. cruce de las reanudaciones
OFFSET_EDGES_S = (-5, -2.5, -1, 0, 1, 2.5, 5)
RISE_SEARCH_S = 5          # la subida de velocidad se busca desde 5 s antes de la ventana hasta 5 s después
PLAYERS_SMOOTH_HALF_WIDTH = 12  # ±0,5 s para la velocidad media de los jugadores
NEXT_PHASE_MAX_S = 30
# 3. salidas del balón
LONG_GAP_S = 2
NEAR_LINE_M = 2.0
OUTWARD_MS = 1.0           # componente de velocidad hacia la línea más cercana
LOOKBACK_EXIT_S = 15       # ventana previa a cada SET PIECE en la que se busca una salida
FOLLOWUP_S = 30            # tras una salida, ¿hay una ventana SET PIECES en los 30 s siguientes?
EXIT_AFTER_START_S = 2     # una salida cuenta para una ventana si cae hasta 2 s después de su inicio
# 5. velocidad
SMOOTH_HALF_WIDTHS = {"0,5 s": 6, "1 s": 12}


def clip_slice(start, end, n):
    return slice(max(0, min(start, n)), max(0, min(end, n)))


def speed_rise(v, start, end, n):
    """Primer frame, desde el mínimo de la velocidad media en [start − 5 s, end + 5 s), en que supera el punto
    medio entre ese mínimo y el máximo de la ventana. None si no hay datos."""
    w = clip_slice(start - RISE_SEARCH_S * FPS, end + RISE_SEARCH_S * FPS, n)
    values = v[w]
    if values.size == 0 or np.all(np.isnan(values)):
        return None
    i_min = int(np.nanargmin(values))
    mid = (np.nanmin(values) + np.nanmax(values)) / 2.0
    after = np.flatnonzero(values[i_min:] >= mid)
    return None if after.size == 0 else w.start + i_min + int(after[0])


def exits(x, y, visible, graded, pitch):
    """Frames en que empieza un hueco largo cuyo último balón visto está junto a una línea y va hacia fuera.
    Devuelve (inicios de todos los huecos largos, inicios de los que son salidas, lado de cada salida)."""
    length, width = pitch
    edges = np.diff(np.concatenate(([0], (~visible).astype(np.int8), [0])))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    long_gaps = [s for s, e in zip(starts, ends) if e - s >= LONG_GAP_S * FPS and graded[s]]
    exit_frames, sides = [], []
    for s in long_gaps:
        if s < 3 or not (visible[s - 1] and visible[s - 2] and visible[s - 3]):
            continue
        vx = (x[s - 1] - x[s - 3]) / (2.0 / FPS)
        vy = (y[s - 1] - y[s - 3]) / (2.0 / FPS)
        candidates = (  # (distancia a la línea, velocidad hacia ella, lado)
            (x[s - 1], -vx, "fondo"), (length - x[s - 1], vx, "fondo"),
            (y[s - 1], -vy, "banda"), (width - y[s - 1], vy, "banda"))
        distance, outward, side = min(candidates, key=lambda c: c[0])
        if distance <= NEAR_LINE_M and outward >= OUTWARD_MS:
            exit_frames.append(s)
            sides.append(side)
    return long_gaps, exit_frames, sides


def main():
    utf8_stdout()
    game = games.GAME
    entry = games.GAMES[game]
    n_frames, pitch = entry["n_video_frames"], entry["pitch"]
    atd_raw, atd_meta, _ = games.require(["atd_raw", "atd_meta", "smart_tagging"], game)
    started = time.time()
    x, y, atd_speed = load_ball(atd_raw, n_frames, pitch)
    px, py = load_players(atd_raw, n_frames, pitch)
    events = load_smart_tagging.load(game)
    graded = graded_mask(game, n_frames)
    visible = ~np.isnan(x)
    by_type = grouped_by_type(events)
    phase_starts = np.array(sorted(e["start_frame"] for e in events
                                   if norm(e["code"]) not in (SET_PIECES_CODE, GOALS_CODE)))
    v_players = moving_average(mean_speed(px, py), PLAYERS_SMOOTH_HALF_WIDTH)

    print("2. Las reanudaciones del detector de golpeo frente a tres señales independientes")
    print("   (desfase = reanudación − señal, en segundos; negativo: la reanudación cae antes)")
    for kind, group in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        vs_end, vs_phase, vs_rise, found = [], [], [], 0
        for e in group:
            strike = find_strike(x, y, e["start_frame"], e["end_frame"])
            if strike is None:
                continue
            found += 1
            vs_end.append((strike - e["end_frame"]) / FPS)
            later = phase_starts[phase_starts >= e["start_frame"]]
            if later.size and (later[0] - e["end_frame"]) / FPS <= NEXT_PHASE_MAX_S:
                vs_phase.append((strike - later[0]) / FPS)
            rise = speed_rise(v_players, e["start_frame"], e["end_frame"], n_frames)
            if rise is not None:
                vs_rise.append((strike - rise) / FPS)
        print("   {:<22} n={:>3}   reanudación encontrada {} ({})".format(kind, len(group), found, pct(found, len(group))))
        print_bins("frente al FIN de la ventana SET PIECES", vs_end, OFFSET_EDGES_S)
        print_bins("frente al inicio de la primera fase posterior", vs_phase, OFFSET_EDGES_S)
        print_bins("frente a la subida de velocidad de los jugadores", vs_rise, OFFSET_EDGES_S)

    print("\n3. El balón que desaparece saliendo del campo")
    long_gaps, exit_frames, sides = exits(x, y, visible, graded, pitch)
    print("   huecos sin balón de ≥ {} s que empiezan en frames evaluados: {}".format(LONG_GAP_S, len(long_gaps)))
    print("   de ellos, con el último punto a ≤ {:g} m de una línea y ≥ {:g} m/s hacia fuera (salidas): {} ({})"
          "   por banda {}   por fondo {}".format(NEAR_LINE_M, OUTWARD_MS, len(exit_frames),
                                                 pct(len(exit_frames), len(long_gaps)),
                                                 sides.count("banda"), sides.count("fondo")))
    sp_starts = np.array(sorted(e["start_frame"] for e in events if norm(e["code"]) == SET_PIECES_CODE))
    exit_frames = np.array(exit_frames, dtype=np.int64)
    if exit_frames.size and sp_starts.size:
        idx = np.searchsorted(sp_starts, exit_frames)
        has_next = idx < sp_starts.size
        gap_s = np.where(has_next, (sp_starts[np.minimum(idx, sp_starts.size - 1)] - exit_frames) / FPS, np.inf)
        n_follow = int(np.sum(gap_s <= FOLLOWUP_S))
        print("   salidas seguidas de una ventana SET PIECES en ≤ {} s: {} ({})   ".format(
            FOLLOWUP_S, n_follow, pct(n_follow, exit_frames.size)))
        print_bins("segundos de la salida al inicio de esa ventana", gap_s[gap_s <= FOLLOWUP_S], (2, 5, 10, 20), indent="   ")
    for kind, group in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        with_exit = 0
        for e in group:
            lo, hi = e["start_frame"] - LOOKBACK_EXIT_S * FPS, e["start_frame"] + EXIT_AFTER_START_S * FPS
            with_exit += bool(np.any((exit_frames >= lo) & (exit_frames < hi)))
        print("   {:<22} n={:>3}   con una salida en los {} s previos: {} ({})".format(
            kind, len(group), LOOKBACK_EXIT_S, with_exit, pct(with_exit, len(group))))

    print("\n5. Columna de velocidad del balón del ATD frente al desplazamiento suavizado")
    raw = np.full(n_frames, np.nan)
    raw[1:] = np.hypot(np.diff(x), np.diff(y)) * FPS
    ok = graded & ~np.isnan(atd_speed) & ~np.isnan(raw)
    print("   frames comparables {}".format(int(ok.sum())))
    print("   columna del ATD        {}".format(quantiles(atd_speed[ok])))
    print("   salto entre frames ×25 {}   correlación con la columna {:.2f}".format(
        quantiles(raw[ok]), np.corrcoef(atd_speed[ok], raw[ok])[0, 1]))
    for label, half in SMOOTH_HALF_WIDTHS.items():
        sx, sy = moving_average(x, half), moving_average(y, half)
        smooth = np.full(n_frames, np.nan)
        smooth[half:-half] = np.hypot(sx[2 * half:] - sx[:-2 * half], sy[2 * half:] - sy[:-2 * half]) / (2.0 * half / FPS)
        ok2 = ok & ~np.isnan(smooth)
        print("   desplazamiento a {:<5} {}   correlación {:.2f}   cociente de medianas columna/suavizado {:.2f}".format(
            label, quantiles(smooth[ok2]), np.corrcoef(atd_speed[ok2], smooth[ok2])[0, 1],
            np.nanmedian(atd_speed[ok2]) / max(np.nanmedian(smooth[ok2]), 1e-9)))

    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
