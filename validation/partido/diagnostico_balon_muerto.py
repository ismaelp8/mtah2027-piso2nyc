"""Diagnóstico del balón muerto en el ATD del partido. Solo imprime agregados del partido entero.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La
salida se puede pegar en el chat: son recuentos y porcentajes por tipo de reinicio, sin números de
frame ni jugadas sueltas.

    python validation/partido/diagnostico_balon_muerto.py

Mide si el balón del ATD sirve para el detector de `D`:
1. ¿El ATD sigue viendo el balón fuera del campo (coordenadas fuera de 0–1) o lo pierde?
2. En los reinicios del Smart Tagging, ¿se ve el balón, se ve quieto y estaba fuera justo antes?
3. En los saques iniciales, todos juntos, ¿se ve el balón quieto en el centro?
4. Cuántos frames marca la máscara de possession/dead_ball.py.
5. Experimento descartado: fechar cada reanudación con "balón quieto que empieza a moverse".

El experimento 5 vive aquí y no en possession/ porque se descartó: se guarda para poder repetir la
medida. Resultado y lectura en validation/resultados/2026-11-12_balon_muerto_atd.md.
"""

import os
import sys
import time
from collections import Counter, deque

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import (CENTRE_RADIUS_M, FPS, KICKOFF_TYPES, MAX_GAP_FRAMES, SET_PIECES_CODE,  # noqa: E402
                   graded_mask, norm, pct, utf8_stdout)
from possession.dead_ball import dead_mask  # noqa: E402
from possession.io import load_ball  # noqa: E402
from starter import load_smart_tagging  # noqa: E402

LOOKBACK_FRAMES = 10 * FPS  # 10 s antes de cada reinicio
OUTSIDE_MARGINS_M = (0, 1, 3)
OFFSET_BINS_S = ((0, 1), (1, 2.5), (2.5, 5), (5, None))
STILL_BINS_S = ((0, 1), (1, 3), (3, 10), (10, None))
# Los saques iniciales se cuentan siempre juntos: por separado son dos o cuatro jugadas que se pueden
# identificar, y validation/PASOS.md (paso 5) pide solo totales del partido entero.
KICKOFF_GROUP = "kick off (todos)"

# Umbrales del experimento, fijados antes de medir.
# Frames vistos con el balón quieto antes de aceptar un golpeo (0,2 s).
MIN_REST_FRAMES = 5
# Desplazamiento que separa "quieto" de "golpeado".
STRIKE_DISPLACEMENT_M = 0.5


def kind_of(event):
    kind = norm(event["tags"].get("Type"))
    return KICKOFF_GROUP if kind in KICKOFF_TYPES else (kind or "(sin tipo)")


def bin_name(value, bins, unit):
    for low, high in bins:
        if high is None:
            if value >= low:
                return "≥{} {}".format(low, unit)
        elif low <= value < high:
            return "{}–{} {}".format(low, high, unit)
    return "fuera de rango"


def print_bins(title, counter, bins, unit, total):
    print("      {}".format(title))
    for low, _ in bins:
        name = bin_name(low, bins, unit)
        print("         {:<12} {:>3}  ({})".format(name, counter[name], pct(counter[name], total)))
    if counter["ninguno"]:
        print("         {:<12} {:>3}  ({})".format(
            "ninguno", counter["ninguno"], pct(counter["ninguno"], total)))


def outside_by(x, y, pitch, margin):
    length, width = pitch
    return (x < -margin) | (x > length + margin), (y < -margin) | (y > width + margin)


def first_still_position(x, y, start, end):
    """Posición mediana de los primeros MIN_REST_FRAMES frames vistos seguidos con el balón quieto.

    "Seguidos" cuenta solo los frames con balón: aquí los huecos no tienen límite, al contrario que en
    find_strike. Es la columna "quieto en la ventana" de la sección 2, que no sostiene ninguna
    conclusión.
    """
    recent = deque(maxlen=MIN_REST_FRAMES)
    for frame in range(max(start, 0), min(end, len(x))):
        if np.isnan(x[frame]):
            continue
        recent.append((x[frame], y[frame]))
        if len(recent) == recent.maxlen:
            points = np.array(recent)
            centre = np.median(points, axis=0)
            if np.hypot(*(points - centre).T).max() <= STRIKE_DISPLACEMENT_M:
                return centre
    return None


def near_centre(x, y, start, end, centre):
    """¿Hay MIN_REST_FRAMES frames vistos (no hace falta que seguidos) a menos de CENTRE_RADIUS_M
    del centro en [start, end)?"""
    window = slice(max(start, 0), max(min(end, len(x)), 0))
    distance = np.hypot(x[window] - centre[0], y[window] - centre[1])
    return int(np.sum(distance <= CENTRE_RADIUS_M)) >= MIN_REST_FRAMES


def find_strike(x, y, start, end, centre=None):
    """Primer frame en [start, end) en que el balón, visto quieto justo antes, empieza a moverse.

    El balón quieto se busca desde LOOKBACK_FRAMES antes de `start`. Un hueco sin balón de más de
    MAX_GAP_FRAMES lo olvida: sin eso, un balón que desaparece y reaparece lejos contaría como golpeo.
    Con `centre`, solo cuenta el balón quieto a menos de CENTRE_RADIUS_M de ese punto. None si no se
    encuentra.
    """
    rest = deque(maxlen=MIN_REST_FRAMES)
    gap = 0
    for frame in range(max(start - LOOKBACK_FRAMES, 0), min(end, len(x))):
        if np.isnan(x[frame]) or np.isnan(y[frame]):
            gap += 1
            if gap > MAX_GAP_FRAMES:
                rest.clear()
            continue
        gap = 0
        position = np.array([x[frame], y[frame]])
        if len(rest) == MIN_REST_FRAMES:
            anchor = np.median(np.array(rest), axis=0)
            spread = max(np.hypot(*(point - anchor)) for point in rest)
            if spread <= STRIKE_DISPLACEMENT_M and np.hypot(*(position - anchor)) > STRIKE_DISPLACEMENT_M:
                if frame >= start:
                    return frame
                rest.clear()
        if centre is None or np.hypot(*(position - centre)) <= CENTRE_RADIUS_M:
            rest.append(position)
        else:
            rest.clear()
    return None


def still_since(x, y, strike):
    """Primer frame del tramo en que el balón estaba quieto justo antes de `strike`."""
    first_points, anchor, earliest, gap = [], None, None, 0
    for frame in range(strike - 1, -1, -1):
        if np.isnan(x[frame]) or np.isnan(y[frame]):
            gap += 1
            if gap > MAX_GAP_FRAMES:
                break
            continue
        gap = 0
        position = np.array([x[frame], y[frame]])
        if anchor is None:
            first_points.append(position)
            earliest = frame
            if len(first_points) == MIN_REST_FRAMES:
                anchor = np.median(np.array(first_points), axis=0)
        elif np.hypot(*(position - anchor)) <= STRIKE_DISPLACEMENT_M:
            earliest = frame
        else:
            break
    return earliest


def main():
    utf8_stdout()
    game = games.GAME
    entry = games.GAMES[game]
    n_frames, pitch = entry["n_video_frames"], entry["pitch"]
    centre = np.array([pitch[0] / 2, pitch[1] / 2])
    paths = games.require(["atd_raw", "smart_tagging"], game)

    started = time.time()
    x, y, _ = load_ball(paths[0], n_frames, pitch)
    events = load_smart_tagging.load(game)
    graded = graded_mask(game, n_frames)
    visible = ~np.isnan(x)
    set_pieces = [event for event in events if norm(event["code"]) == SET_PIECES_CODE]

    print("1. Balón en los frames evaluados")
    n_graded = int(graded.sum())
    n_visible = int((graded & visible).sum())
    print("   frames evaluados {:>7}   con balón {:>7} ({})".format(
        n_graded, n_visible, pct(n_visible, n_graded)))
    for margin in OUTSIDE_MARGINS_M:
        out_x, out_y = outside_by(x, y, pitch, margin)
        n_x = int((graded & visible & out_x).sum())
        n_y = int((graded & visible & out_y).sum())
        n_any = int((graded & visible & (out_x | out_y)).sum())
        print("   fuera del campo por más de {} m: {:>6} ({} de los vistos)   por fondo {:>6}   "
              "por banda {:>6}".format(margin, n_any, pct(n_any, n_visible), n_x, n_y))

    print("\n2. Reinicios del Smart Tagging (SET PIECES), por tipo")
    out_x, out_y = outside_by(x, y, pitch, 0)
    out_any = visible & (out_x | out_y)
    rows = {}
    for event in set_pieces:
        start, end = event["start_frame"], event["end_frame"]
        window = visible[max(start, 0):max(min(end, n_frames), 0)]
        before = slice(max(start - LOOKBACK_FRAMES, 0), max(start, 0))
        row = rows.setdefault(kind_of(event), Counter())
        row["n"] += 1
        row["visto en la ventana"] += bool(window.any())
        row["visto >50 % de la ventana"] += bool(window.size and window.mean() > 0.5)
        row["quieto en la ventana"] += first_still_position(x, y, start, end) is not None
        row["visto en los 10 s previos"] += bool(visible[before].any())
        row["fuera del campo en los 10 s previos"] += bool(out_any[before].any())
    columns = ["visto en la ventana", "visto >50 % de la ventana", "quieto en la ventana",
               "visto en los 10 s previos", "fuera del campo en los 10 s previos"]
    for kind in sorted(rows, key=lambda k: -rows[k]["n"]):
        row = rows[kind]
        print("   {:<22} n={:>3}".format(kind, row["n"]))
        for column in columns:
            print("      {:<38} {:>3}  ({})".format(column, row[column], pct(row[column], row["n"])))

    restarts = []
    for event in set_pieces:
        strike = find_strike(x, y, event["start_frame"], event["end_frame"],
                             centre if kind_of(event) == KICKOFF_GROUP else None)
        restarts.append({"kind": kind_of(event), "start_frame": event["start_frame"],
                         "restart_frame": strike,
                         "still_from": None if strike is None else still_since(x, y, strike)})

    print("\n3. Saques iniciales, todos juntos: ¿se ve el balón quieto en el centro?")
    kickoffs = [event for event in set_pieces if kind_of(event) == KICKOFF_GROUP]
    seen, near, seen_not_near = 0, 0, 0
    for event in kickoffs:
        start, end = event["start_frame"] - LOOKBACK_FRAMES, event["end_frame"]
        any_ball = bool(visible[max(start, 0):max(min(end, n_frames), 0)].any())
        at_centre = near_centre(x, y, start, end, centre)
        seen += any_ball
        near += at_centre
        seen_not_near += any_ball and not at_centre
    found = sum(row["kind"] == KICKOFF_GROUP and row["restart_frame"] is not None for row in restarts)
    n = len(kickoffs)
    where = "a menos de {:g} m del centro".format(CENTRE_RADIUS_M)
    lines = [
        ("con balón visto en los 10 s previos o en la ventana", seen),
        ("con el balón {} frames o más {}".format(MIN_REST_FRAMES, where), near),
        ("con balón visto, pero menos de {} frames {}".format(MIN_REST_FRAMES, where), seen_not_near),
        ("reanudación encontrada con el balón quieto en el centro", found),
    ]
    print("   saques iniciales (de inicio de parte y tras gol): {}".format(n))
    for label, count in lines:
        print("      {:<68} {} de {}".format(label, count, n))
    check = load_smart_tagging.check_time_base(events)
    print("   ¿las etiquetas Kick Off (Start) contienen los saques publicados en FAQ.md? {}".format(
        "sí" if check["agrees"] else "NO"))

    print("\n4. Máscara D de possession/dead_ball.py")
    mask = dead_mask(game=game)
    n_dead = int((mask & graded).sum())
    print("   frames D {:>6} de {:>6} evaluados ({})   fuera de los evaluados {}".format(
        n_dead, n_graded, pct(n_dead, n_graded), int((mask & ~graded).sum())))

    print("\n5. Experimento descartado: reanudación como balón quieto que empieza a moverse")
    by_kind = {}
    for row in restarts:
        by_kind.setdefault(row["kind"], []).append(row)
    still_frames_total = 0
    for kind in sorted(by_kind, key=lambda k: -len(by_kind[k])):
        group = by_kind[kind]
        found = [row for row in group if row["restart_frame"] is not None]
        print("   {:<22} n={:>3}   encontrada {:>3} ({})".format(
            kind, len(group), len(found), pct(len(found), len(group))))
        offsets = Counter(bin_name((row["restart_frame"] - row["start_frame"]) / FPS,
                                   OFFSET_BINS_S, "s") for row in found)
        print_bins("segundos desde el inicio de la etiqueta hasta la reanudación",
                   offsets, OFFSET_BINS_S, "s", len(found))
        still = Counter("ninguno" if row["still_from"] is None
                        else bin_name((row["restart_frame"] - row["still_from"]) / FPS,
                                      STILL_BINS_S, "s") for row in found)
        print_bins("cuánto llevaba quieto el balón antes de la reanudación",
                   still, STILL_BINS_S, "s", len(found))
        still_frames_total += sum(row["restart_frame"] - row["still_from"]
                                  for row in found if row["still_from"] is not None)
    print("   frames con el balón quieto antes de una reanudación: {} ({} de los evaluados)".format(
        still_frames_total, pct(still_frames_total, n_graded)))

    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
