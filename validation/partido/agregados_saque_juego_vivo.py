"""Agregados del partido para el juego vivo en el saque de cada parte (possession/dead_ball.py). Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida se puede
pegar en el chat: recuentos de frames y de rachas, porcentajes y sha256, sin números de frame ni jugadas sueltas.

    python validation/partido/agregados_saque_juego_vivo.py

Responde, con la regla apuntada en docs/decisiones.md antes de ejecutarlo (15/11, «juego vivo en el saque»), si entra
el ancla de la tarea 4 del plan: `D` prohibido en el frame del saque de cada parte (dead_ball.kickoff_mask).

Corre el pipeline de la entrega dos veces, sin escribir ningún fichero: con dead_ball.evidence tal cual, que ya lleva
el ancla, y con el ancla quitada (`D` permitido otra vez en esos frames). Así no hace falta la entrega de antes. Imprime:
- el sha256 que tendría la entrega en los dos casos. Sin el ancla tiene que salir el de la entrega vigente; si no,
  ha cambiado algo más y hay que mirarlo antes de leer lo demás;
- los conflictos entre piezas, el `D` en el frame del saque, el % de `D` y las paradas (la banda del plan), y las
  posesiones, las paradas y las rachas cortas de cada tramo, sin el ancla y con ella;
- cuántos frames evaluados cambian, de qué etiqueta a cuál y a qué distancia después del saque de su parte;
- la regla aplicada y si entra.

`measure_kickoff` y las funciones de la regla no abren ningún fichero; las prueba
validation/scripts/comprobar_balon_muerto.py (sección 12) con un partido inventado y la apertura de ficheros
prohibida. **Nada fuera de `main` puede abrir un fichero.**
"""

import hashlib
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from agregados_instante_reinicio import band_ok, BAND_D, cases, code_fingerprint, MAX_STOPS, model_fingerprint  # noqa: E402
from comun import bins_s, graded_mask, utf8_stdout  # noqa: E402
from possession import dead_ball, dead_state, pipeline, temporal, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
# Todo fijado antes de ejecutarlo (docs/decisiones.md, 15/11, «juego vivo en el saque»).
FAR_S = 60  # lo que cambia tiene que caer antes de 60 s después del saque de su parte
DISTANCE_EDGES_S = (1, 5, 30, FAR_S)  # descriptivo: a qué distancia después del saque caen los frames que cambian
RULE = ("sin conflictos", "cada parte tiene su saque y en él no hay D", "dentro de la banda",
        "en cada tramo no suben las posesiones, las paradas ni las rachas cortas",
        "lo que cambia cae en los 60 s después del saque de su parte")


def without_anchor(evidence_fn, game):
    """La misma evidencia con el ancla del saque quitada: `D` permitido otra vez en los frames del saque."""
    kick = dead_ball.kickoff_mask(game)

    def evidence(clean):
        score, allowed = evidence_fn(clean)
        allowed = allowed.copy()
        allowed[kick, D] = True
        return score, allowed

    return evidence


def csv_sha256(codes):
    """El sha256 que tendría la entrega con estas etiquetas: los mismos bytes que pipeline.write_submission."""
    labels = tracking.LETTERS[codes]
    text = "frame,label\n" + "".join("{},{}\n".format(frame, label) for frame, label in enumerate(labels))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def block_runs(window):
    """(posesiones, paradas) de un tramo: rachas de juego de un mismo equipo y rachas de `D`."""
    kinds = window[np.flatnonzero(np.concatenate(([True], window[1:] != window[:-1])))]
    return int(np.sum(kinds != D)), int(np.sum(kinds == D))


def kickoff_counts(without, with_layer, blocks, kick, graded, fps):
    """Las cuentas de la regla. `blocks` son los tramos evaluados (con el fin sin incluir); `kick`, la máscara de los
    frames del saque (dead_ball.kickoff_mask); `graded`, la de los frames evaluados. No abre ningún fichero."""
    c = {"blocks": [], "changed": 0, "before": 0, "far": 0, "distances_s": [], "pairs": {}, "kick_frames": [],
         "kick_dead": 0}
    for start, stop in blocks:
        kicks = np.flatnonzero(kick[start:stop]) + start
        c["kick_frames"].append(int(kicks.size))
        c["kick_dead"] += int(np.sum(with_layer[kicks] == D))
        changed = np.flatnonzero(without[start:stop] != with_layer[start:stop]) + start
        c["changed"] += int(changed.size)
        if kicks.size:
            after = changed - int(kicks[0])
            c["before"] += int(np.sum(after < 0))
            c["far"] += int(np.sum(after >= FAR_S * fps))
            c["distances_s"] += [d / fps for d in after[after >= 0].tolist()]
        else:
            c["far"] += int(changed.size)  # sin saque en el tramo, nada de lo que cambia puede venir de él
        for u, v in zip(without[changed].tolist(), with_layer[changed].tolist()):
            c["pairs"][(u, v)] = c["pairs"].get((u, v), 0) + 1
        c["blocks"].append({"runs": (block_runs(without[start:stop]), block_runs(with_layer[start:stop])),
                            "short": (pipeline.short_runs(without[start:stop]),
                                      pipeline.short_runs(with_layer[start:stop]))})
    c["dead_share"] = (float(np.mean(without[graded] == D)), float(np.mean(with_layer[graded] == D)))
    c["stops"] = tuple(sum(b["runs"][i][1] for b in c["blocks"]) for i in (0, 1))
    return c


def kickoff_rule(c, conflicts):
    """{condición: se cumple} en el orden de RULE, y si entra (todas). `conflicts` son los frames con piezas en
    conflicto con el ancla."""
    runs_ok = all(after <= before for b in c["blocks"] for before, after in zip(*b["runs"]))
    short_ok = all(b["short"][1][key] <= b["short"][0][key] for b in c["blocks"] for key in b["short"][0])
    checks = dict(zip(RULE, (
        conflicts == 0,
        all(k == 1 for k in c["kick_frames"]) and c["kick_dead"] == 0,
        band_ok(c["dead_share"][1], c["stops"][1]),
        runs_ok and short_ok,
        c["before"] == 0 and c["far"] == 0)))
    return checks, all(checks.values())


def measure_kickoff(trk, delivery_fn, game=games.GAME, pieces=None):
    """Las cuentas y la regla aplicada. `trk` es el tracking sin limpiar; `delivery_fn`, la evidencia de dead_ball de
    la entrega (con el ancla), como función del tracking limpio; `pieces` cambia piezas del pipeline (en el partido,
    None). No abre ningún fichero por sí misma."""
    n = len(trk.bx)
    reports = ({}, {})
    without = pipeline.run(trk, extra=[without_anchor(delivery_fn, game)], report=reports[0], pieces=pieces)
    with_layer = pipeline.run(trk, extra=[delivery_fn], report=reports[1], pieces=pieces)
    c = kickoff_counts(without, with_layer, trk.blocks, dead_ball.kickoff_mask(game), graded_mask(game, n), trk.fps)
    c["conflicts"] = (reports[0]["conflictos"], reports[1]["conflictos"])
    c["sha256"] = (csv_sha256(without), csv_sha256(with_layer))
    c["checks"], c["entra"] = kickoff_rule(c, c["conflicts"][1])
    return c


def yes(flag):
    return "sí" if flag else "no"


def main():
    utf8_stdout()
    game = games.GAME
    games.require(["atd_raw", "atd_meta", "smart_tagging"], game)
    paths = games.asset_paths(game)
    started = time.time()
    trk = tracking.from_atd(paths, game)
    c = measure_kickoff(trk, lambda clean: dead_ball.evidence(clean, paths, game), game)

    print("pipeline: piezas {}   costes {}".format(json.dumps(pipeline.PIECES, sort_keys=True),
                                                   json.dumps(temporal.DEFAULTS, sort_keys=True)))
    print("huellas: modelo de Ana {}   código de possession/ {}".format(
        model_fingerprint(dead_state.MODEL), code_fingerprint(os.path.join(ROOT, "possession"))))
    print("regla: D prohibido en el frame del saque de cada parte; entra si " + "; ".join(RULE))
    print("\n1. La entrega, sin el ancla y con ella (sin escribir ningún fichero)")
    print("   sha256 sin el ancla {}".format(c["sha256"][0]))
    print("   sha256 con el ancla {}".format(c["sha256"][1]))
    print("   frames con piezas en conflicto: sin el ancla {}   con ella {}".format(*c["conflicts"]))
    print("   saques en su tramo: {}   frames del saque con D, con el ancla: {}".format(
        " y ".join(str(k) for k in c["kick_frames"]), c["kick_dead"]))
    print("   D en lo evaluado: sin el ancla {:.2f} %   con ella {:.2f} %   paradas: {} y {}   dentro de la banda"
          " ({:g}–{:g} % y ≤ {} paradas): {}".format(100 * c["dead_share"][0], 100 * c["dead_share"][1], *c["stops"],
                                                    100 * BAND_D[0], 100 * BAND_D[1], MAX_STOPS,
                                                    yes(band_ok(c["dead_share"][1], c["stops"][1]))))
    for number, b in enumerate(c["blocks"], 1):
        (p0, s0), (p1, s1) = b["runs"]
        rises = p1 > p0 or s1 > s0 or any(b["short"][1][key] > b["short"][0][key] for key in b["short"][0])
        print("   tramo {}: posesiones {} y {}   paradas {} y {}   sube algo (también las rachas cortas): {}".format(
            number, cases(p0), cases(p1), cases(s0), cases(s1), yes(rises)))
        print("      rachas cortas (sin el ancla y con ella): " + "; ".join(
            "{} de < {} frames {} y {}".format(kind, limit, cases(b["short"][0][kind, limit]),
                                               cases(b["short"][1][kind, limit]))
            for kind, limit in sorted(b["short"][0])))
    print("\n2. Lo que cambia con el ancla")
    print("   frames evaluados que cambian de etiqueta: {}   antes del saque de su parte: {}   a {} s o más después:"
          " {}".format(c["changed"], c["before"], FAR_S, c["far"]))
    print("   frames que cambian, por distancia después del saque de su parte:")
    for name, k in bins_s(c["distances_s"], DISTANCE_EDGES_S):
        print("      {:<14} {}".format(name.replace("< 1 s", "0 a 1 s"), k))
    print("   de qué etiqueta a cuál: " + ("   ".join(
        "{} → {} {}".format(tracking.LETTERS[u], tracking.LETTERS[v], k) for (u, v), k in sorted(c["pairs"].items()))
        or "ninguno"))
    print("\n3. La regla")
    for condition, ok in c["checks"].items():
        print("   {:<72} {}".format(condition, yes(ok)))
    print("\n-> entra el ancla del saque: {}".format(yes(c["entra"])))
    print("\n   tiempo {:.0f} s".format(time.time() - started))


if __name__ == "__main__":
    main()
