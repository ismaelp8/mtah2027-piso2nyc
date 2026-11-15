"""Agregados del partido para el juego vivo en el saque de cada parte (possession/dead_ball.py). Solo imprime agregados.

Lee datos del partido: lo ejecuta una persona en local, nunca Claude (CLAUDE.md, regla nº 1). La salida se puede
pegar en el chat: recuentos de frames y de rachas, porcentajes, versiones y sha256. No da números de frame. Como solo
hay dos saques, lo que cambia describe como mucho dos tramos de nuestra propia entrega, junto a ellos: por eso no dice
de qué equipo a cuál, solo si es de `D` a juego, de juego a `D` o de un equipo al otro.

    python validation/partido/agregados_saque_juego_vivo.py

Responde, con la regla apuntada en docs/decisiones.md antes de ejecutarlo (15/11, «juego vivo en el saque»), si entra
el ancla de la tarea 4 del plan: `D` prohibido en el frame del saque de cada parte (dead_ball.kickoff_mask).

Corre el pipeline de la entrega dos veces, sin escribir ningún fichero: con dead_ball.evidence tal cual, que ya lleva
el ancla, y con el ancla quitada (`D` permitido otra vez en esos frames). Las dos veces van también las demás capas de
la entrega (pipeline.DELIVERY_LAYERS), como en pipeline.build. Así no hace falta la entrega de antes. Imprime:
- las versiones, el commit y el sha256 que tendría la entrega en los dos casos. Sin el ancla tiene que salir la
  entrega vigente (VIGENTE); si no, la regla no se aplica: avisa, no enseña nada más y sale con código 1;
- los conflictos entre piezas, el `D` en el frame del saque, el % de `D` y las paradas (la banda del plan), y las
  posesiones y las paradas de cada tramo, sin el ancla y con ella, con lo que sube;
- cuántos frames evaluados cambian, de qué clase y a qué distancia después del saque de su parte;
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
from agregados_instante_reinicio import (band_ok, BAND_D, cases, code_fingerprint, delivery_layers,  # noqa: E402
                                        layer_names, MAX_STOPS, model_fingerprint)
from comun import bins_s, graded_mask, utf8_stdout  # noqa: E402
from possession import dead_ball, dead_state, pipeline, temporal, tracking  # noqa: E402

D = tracking.D
# Todo fijado antes de ejecutarlo (docs/decisiones.md, 15/11, «juego vivo en el saque»).
# La entrega vigente cuando se escribió la regla: su nombre y el principio y el final de su sha256. «Sin el ancla»
# tiene que ser ella; si no, ha cambiado algo más (el código de `main` o el entorno) y la regla no se aplica.
VIGENTE = ("equipo_v5", "27dc8aa8", "efb7")
# Lo que cambia tiene que caer antes de 60 s después del saque de su parte. A priori: el mismo horizonte que
# dead_ball.MAX_GAP_BEFORE_RESTART_S y que el control de juego del instante del reinicio.
FAR_S = 60
DISTANCE_EDGES_S = (1, 5, 30, FAR_S)  # descriptivo: a qué distancia después del saque caen los frames que cambian
RULE = ("sin el ancla sale la entrega vigente ({}, sha256 {}…{})".format(*VIGENTE),
        "con el ancla, ningún frame evaluado con piezas en conflicto",
        "cada parte tiene su saque y en él no hay D", "dentro de la banda",
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


def is_current(sha, current=VIGENTE):
    """El sha256 es el de la entrega vigente: empieza y acaba como el de `current`."""
    return sha.startswith(current[1]) and sha.endswith(current[2])


def block_runs(window):
    """(posesiones, paradas) de un tramo: rachas de juego de un mismo equipo y rachas de `D`."""
    kinds = window[np.flatnonzero(np.concatenate(([True], window[1:] != window[:-1])))]
    return int(np.sum(kinds != D)), int(np.sum(kinds == D))


def rising(runs, short):
    """Lo que sube con el ancla en un tramo: posesiones, paradas o alguna racha corta. Es la condición 4 de la regla
    (kickoff_rule) y lo que imprime main."""
    (p0, s0), (p1, s1) = runs
    out = [name for name, before, after in (("posesiones", p0, p1), ("paradas", s0, s1)) if after > before]
    return out + ["rachas de {} de < {} frames".format(kind, limit) for kind, limit in sorted(short[0])
                  if short[1][kind, limit] > short[0][kind, limit]]


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
        runs = (block_runs(without[start:stop]), block_runs(with_layer[start:stop]))
        short = (pipeline.short_runs(without[start:stop]), pipeline.short_runs(with_layer[start:stop]))
        c["blocks"].append({"runs": runs, "short": short, "rises": rising(runs, short)})
    c["dead_share"] = (float(np.mean(without[graded] == D)), float(np.mean(with_layer[graded] == D)))
    c["stops"] = tuple(sum(b["runs"][i][1] for b in c["blocks"]) for i in (0, 1))
    return c


def change_kinds(pairs):
    """(de `D` a juego, de juego a `D`, de un equipo al otro): los frames que cambian, sin decir qué equipo."""
    to_play = sum(k for (u, v), k in pairs.items() if u == D and v != D)
    to_dead = sum(k for (u, v), k in pairs.items() if u != D and v == D)
    return to_play, to_dead, sum(pairs.values()) - to_play - to_dead


def kickoff_rule(c, conflicts, without_sha, current=VIGENTE):
    """{condición: se cumple} en el orden de RULE, y si entra (todas). `conflicts` son los frames con piezas en
    conflicto con el ancla; `without_sha`, el sha256 de la entrega sin el ancla; `current`, la entrega vigente."""
    checks = dict(zip(RULE, (
        is_current(without_sha, current),
        conflicts == 0,
        all(k == 1 for k in c["kick_frames"]) and c["kick_dead"] == 0,
        band_ok(c["dead_share"][1], c["stops"][1]),
        not any(b["rises"] for b in c["blocks"]),
        c["before"] == 0 and c["far"] == 0)))
    return checks, all(checks.values())


def measure_kickoff(trk, delivery_fn, game=games.GAME, pieces=None, layers=(), current=VIGENTE):
    """Las cuentas y la regla aplicada. `trk` es el tracking sin limpiar; `delivery_fn`, la evidencia de dead_ball de
    la entrega (con el ancla), como función del tracking limpio; `pieces` cambia piezas del pipeline (en el partido,
    None); `layers`, las demás capas de la entrega (delivery_layers), que van en las dos ejecuciones; `current`, la
    entrega vigente (en el partido, VIGENTE). No abre ningún fichero por sí misma."""
    n = len(trk.bx)
    reports = ({}, {})
    without = pipeline.run(trk, extra=[without_anchor(delivery_fn, game)] + list(layers), report=reports[0],
                           pieces=pieces)
    with_layer = pipeline.run(trk, extra=[delivery_fn] + list(layers), report=reports[1], pieces=pieces)
    c = kickoff_counts(without, with_layer, trk.blocks, dead_ball.kickoff_mask(game), graded_mask(game, n), trk.fps)
    c["conflicts"] = (reports[0]["conflictos"], reports[1]["conflictos"])
    c["sha256"] = (csv_sha256(without), csv_sha256(with_layer))
    c["checks"], c["entra"] = kickoff_rule(c, c["conflicts"][1], c["sha256"][0], current)
    return c


def yes(flag):
    return "sí" if flag else "no"


def main():
    utf8_stdout()
    game = games.GAME
    games.require(["atd_raw", "atd_meta", "smart_tagging"], game)
    paths = games.asset_paths(game)
    started = time.time()
    report = {}
    trk = tracking.from_atd(paths, game, report=report)
    pipeline.check_atd(report["atd"])  # como pipeline.build: una línea rara del ATD es un error
    c = measure_kickoff(trk, lambda clean: dead_ball.evidence(clean, paths, game), game,
                        layers=delivery_layers(paths, game))

    print(pipeline.versions())
    print(pipeline.code_version())
    print("pipeline: piezas {}   costes {}".format(json.dumps(pipeline.PIECES, sort_keys=True),
                                                   json.dumps(temporal.DEFAULTS, sort_keys=True)))
    print("capas de la entrega, además de dead_ball.evidence: {}".format(", ".join(layer_names()) or "ninguna"))
    print("huellas: modelo de Ana {}   código de possession/ {}".format(
        model_fingerprint(dead_state.MODEL), code_fingerprint(os.path.join(ROOT, "possession"))))
    print("regla: D prohibido en el frame del saque de cada parte; entra si " + "; ".join(RULE))
    print("\n1. La entrega, sin el ancla y con ella (sin escribir ningún fichero)")
    print("   sha256 sin el ancla {}   ¿es la vigente ({})? {}".format(c["sha256"][0], VIGENTE[0],
                                                                    yes(c["checks"][RULE[0]])))
    print("   sha256 con el ancla {}".format(c["sha256"][1]))
    if not c["checks"][RULE[0]]:
        print("   OJO: sin el ancla no sale la entrega vigente. La regla no se aplica y no se enseña nada más: no entra"
              " hasta explicarlo y volver a ejecutar (docs/decisiones.md, «juego vivo en el saque», condición 0).")
        return 1
    print("   frames evaluados con piezas en conflicto: sin el ancla {}   con ella {}".format(*c["conflicts"]))
    print("   saques en su tramo: {}   frames del saque con D, con el ancla: {}".format(
        " y ".join(str(k) for k in c["kick_frames"]), c["kick_dead"]))
    print("   D en lo evaluado: sin el ancla {:.2f} %   con ella {:.2f} %   paradas: {} y {}   dentro de la banda"
          " ({:g}–{:g} % y ≤ {} paradas): {}".format(100 * c["dead_share"][0], 100 * c["dead_share"][1], *c["stops"],
                                                    100 * BAND_D[0], 100 * BAND_D[1], MAX_STOPS,
                                                    yes(c["checks"][RULE[3]])))
    for number, b in enumerate(c["blocks"], 1):
        (p0, s0), (p1, s1) = b["runs"]
        print("   tramo {}: posesiones {} y {}   paradas {} y {}   sube con el ancla: {}".format(
            number, cases(p0), cases(p1), cases(s0), cases(s1), ", ".join(b["rises"]) or "nada"))
    print("\n2. Lo que cambia con el ancla (las dos partes juntas)")
    print("   frames evaluados que cambian de etiqueta: {}   antes del saque de su parte: {}   a {} s o más después:"
          " {}".format(c["changed"], c["before"], FAR_S, c["far"]))
    print("   de D a juego {}   de juego a D {}   de un equipo al otro {}".format(*change_kinds(c["pairs"])))
    print("   frames que cambian, por distancia después del saque de su parte:")
    for name, k in bins_s(c["distances_s"], DISTANCE_EDGES_S):
        print("      {:<14} {}".format(name.replace("< 1 s", "0 a 1 s"), k))
    print("\n3. La regla")
    for condition, ok in c["checks"].items():
        print("   {:<72} {}".format(condition, yes(ok)))
    print("\n-> entra el ancla del saque: {}".format(yes(c["entra"])))
    print("\n   tiempo {:.0f} s".format(time.time() - started))
    return 0


if __name__ == "__main__":
    sys.exit(main())
