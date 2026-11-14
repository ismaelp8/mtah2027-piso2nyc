"""Agregados del Smart Tagging del partido para diseñar el detector de `D`. Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida
se puede pegar en el chat: recuentos, porcentajes y cuantiles por tipo de reinicio, sin números de frame.

    python validation/partido/agregados_smart_tagging.py

Responde a (sección 7 de validation/resultados/2026-11-13_revision_balon_muerto.md, agregado 1):
1. Cuánto duran las ventanas `SET PIECES` por tipo y cuántas llevan `Team = N/A`. Decide cómo usarlas
   como fin del `D` (B2).
2. Qué fracción de los frames evaluados cubre alguna fase que no sea `SET PIECES`, y cuánto duran los
   huecos sin ninguna fase. Dice si "sin fase" sirve como indicio de balón muerto.
3. Cuánto pasa entre cada `GOALS` y el siguiente `Kick Off (After Goal)`, todos los goles juntos. Es el
   `D` largo que sigue a cada gol.
4. Dónde empieza la primera fase posterior a cada ventana `SET PIECES`, respecto al fin de la ventana.
   Es una de las señales independientes con las que cruzar las "reanudaciones" del balón.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from comun import (FPS, GOALS_CODE, SET_PIECES_CODE, graded_mask, grouped_by_type, norm, pct,  # noqa: E402
                   print_bins, quantiles, utf8_stdout)
from starter import load_smart_tagging  # noqa: E402

AFTER_GOAL_TYPE = "kick off (after goal)"
DURATION_EDGES_S = (2, 5, 10, 20)
GAP_EDGES_S = (2, 5, 10, 30)
NEXT_PHASE_EDGES_S = (-5, -2.5, -1, 0, 1, 2.5, 5)
MAX_NEXT_PHASE_S = 30


def clip(frame, n_frames):
    return max(0, min(frame, n_frames))


def main():
    utf8_stdout()
    game = games.GAME
    n_frames = games.GAMES[game]["n_video_frames"]
    events = load_smart_tagging.load(game)
    graded = graded_mask(game, n_frames)
    set_pieces = [e for e in events if norm(e["code"]) == SET_PIECES_CODE]
    phases = [e for e in events if norm(e["code"]) not in (SET_PIECES_CODE, GOALS_CODE)]
    goals = [e for e in events if norm(e["code"]) == GOALS_CODE]
    print("instancias {}   SET PIECES {}   GOALS {}   otras fases {}".format(
        len(events), len(set_pieces), len(goals), len(phases)))

    print("\n1. Ventanas SET PIECES por tipo: duración y Team N/A")
    for kind, group in sorted(grouped_by_type(events).items(), key=lambda kv: -len(kv[1])):
        durations = [(e["end_frame"] - e["start_frame"]) / FPS for e in group]
        n_na = sum(norm(e["tags"].get("Team")) in ("n/a", "") for e in group)
        print("   {:<22} n={:>3}   duración (s) {}   Team N/A {} ({})".format(
            kind, len(group), quantiles(durations), n_na, pct(n_na, len(group))))
        print_bins("duración en intervalos", durations, DURATION_EDGES_S)

    print("\n2. Cobertura de los frames evaluados por las fases")
    covered_phase = np.zeros(n_frames, dtype=bool)
    for e in phases:
        covered_phase[clip(e["start_frame"], n_frames):clip(e["end_frame"], n_frames)] = True
    covered_sp = np.zeros(n_frames, dtype=bool)
    for e in set_pieces:
        covered_sp[clip(e["start_frame"], n_frames):clip(e["end_frame"], n_frames)] = True
    n_graded = int(graded.sum())
    for label, mask in (("alguna fase (no SET PIECES)", covered_phase), ("alguna ventana SET PIECES", covered_sp),
                        ("fase o ventana", covered_phase | covered_sp), ("ninguna etiqueta", ~(covered_phase | covered_sp))):
        n = int((graded & mask).sum())
        print("   {:<30} {:>7} frames ({})".format(label, n, pct(n, n_graded)))
    # huecos sin ninguna etiqueta dentro de los frames evaluados
    empty = graded & ~(covered_phase | covered_sp)
    edges = np.diff(np.concatenate(([0], empty.astype(np.int8), [0])))
    gaps = (np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)) / FPS
    print_bins("huecos sin ninguna etiqueta, duración", gaps, GAP_EDGES_S, indent="   ")
    print("   frames en huecos de ≥ 5 s: {} ({} de los evaluados)".format(
        int(np.sum(gaps[gaps >= 5]) * FPS), pct(int(np.sum(gaps[gaps >= 5]) * FPS), n_graded)))

    print("\n3. GOALS → siguiente Kick Off (After Goal), todos los goles juntos")
    after_goal = sorted(e["start_frame"] for e in set_pieces if norm(e["tags"].get("Type")) == AFTER_GOAL_TYPE)
    distances = []
    for g in goals:
        later = [s for s in after_goal if s >= g["start_frame"]]
        if later:
            distances.append((later[0] - g["start_frame"]) / FPS)
    print("   goles {}   con saque posterior etiquetado {}   saques tras gol etiquetados {}".format(
        len(goals), len(distances), len(after_goal)))
    # Solo la suma y la mediana: con 4 goles, cualquier desglose identifica cada parada (regla de los 5 casos).
    if distances:
        print("   frames entre gol y saque, sumados: {} ({} de los evaluados)   mediana {:.0f} s".format(
            int(sum(distances) * FPS), pct(int(sum(distances) * FPS), n_graded), np.median(distances)))

    print("\n4. Primera fase posterior a cada ventana SET PIECES: inicio de la fase − fin de la ventana")
    phase_starts = np.array(sorted(e["start_frame"] for e in phases))
    for kind, group in sorted(grouped_by_type(events).items(), key=lambda kv: -len(kv[1])):
        offsets = []
        for e in group:
            later = phase_starts[phase_starts >= e["start_frame"]]
            if later.size and (later[0] - e["end_frame"]) / FPS <= MAX_NEXT_PHASE_S:
                offsets.append((later[0] - e["end_frame"]) / FPS)
        print("   {:<22} n={:>3}   con fase en los {} s siguientes {}".format(kind, len(group), MAX_NEXT_PHASE_S, len(offsets)))
        print_bins("desfase (negativo: la fase empieza dentro de la ventana)", offsets, NEXT_PHASE_EDGES_S)


if __name__ == "__main__":
    main()
