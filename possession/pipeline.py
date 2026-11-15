"""El pipeline de punta a punta: del tracking a la entrega.

    python -m possession.pipeline                    # escribe evaluation/results/equipo_v0.csv
    python -m possession.pipeline --name mi_prueba

Lee el ATD y el Smart Tagging del partido, así que **solo lo ejecuta una persona**. Imprime solo agregados.

    tracking -> limpieza del balón -> evidencias (equipo, estado de D, anclas de D) -> decodificador -> CSV

`run()` es la parte que no toca ficheros: recibe un `Tracking` y devuelve las etiquetas. Es la que usa el
harness de la DFL (validation/harness/), con el mismo código de las piezas.
"""

import argparse
import hashlib
import os
import sys

import numpy as np

import games
from possession import aprendida, ball, candidates, dead_ball, dead_state, temporal, tracking

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "evaluation", "results")
DEFAULT_NAME = "equipo_v0"

# Las piezas que `run` deja cambiar por otra función (argumento `pieces`) y la función de cada una que va
# en la entrega: «funcion» de su módulo o «modulo.funcion». El harness de la DFL las usa para comparar
# versiones sin tocar este fichero.
# Desde el 14/11 la evidencia de equipo es B5 de la apuesta B (`aprendida.evidence_b5`), que ganó con los
# criterios fijados antes de medir (docs/decisiones.md). Antes era N1 (`candidates.evidence`).
PIECES = {"ball": "clean", "candidates": "aprendida.evidence_b5", "dead_state": "evidence", "temporal": "decode"}
MODULES = {"ball": ball, "candidates": candidates, "dead_state": dead_state, "temporal": temporal,
           "aprendida": aprendida}


def default_piece(name):
    """La función de la entrega de una pieza, según `PIECES`."""
    spec = PIECES[name]
    module, function = spec.split(".", 1) if "." in spec else (name, spec)
    return getattr(MODULES[module], function)


def combine(pieces, n):
    """Suma las puntuaciones y cruza lo permitido. Devuelve (score, allowed, conflict).

    `conflict` marca los frames en los que, entre todas las piezas, no queda ningún estado permitido: dos
    piezas dicen cosas incompatibles sobre lo que «se sabe seguro». Ahí se vuelve a permitir todo y decide
    la puntuación, pero es un fallo de alguna pieza y `run` no lo deja pasar en silencio.
    """
    for score, allowed in pieces:
        if np.shape(score) != (n, tracking.N_STATES) or np.shape(allowed) != (n, tracking.N_STATES):
            raise ValueError("una pieza no devuelve (score, allowed) de forma ({}, 3)".format(n))
    score = sum(piece[0] for piece in pieces)
    allowed = np.logical_and.reduce([piece[1] for piece in pieces])
    conflict = ~allowed.any(axis=1)
    allowed[conflict] = True
    return score, allowed, conflict


def run(trk, extra=(), params=None, report=None, pieces=None):
    """Etiquetas por frame (códigos de possession/tracking.py) a partir de un `Tracking`.

    `extra`: evidencias que se suman a las del tracking. Cada una es `(score, allowed)` ya calculada, o
    una función que recibe el tracking **con el balón ya limpio** y la devuelve. En el partido es
    `dead_ball.evidence`; en el harness, por ejemplo, el `D` copiado de las etiquetas.

    `params` son los del decodificador.

    `pieces` cambia alguna pieza por otra función con la misma firma, para comparar versiones en el
    harness: un diccionario con claves de `PIECES` ("ball", "candidates", "dead_state" y "temporal"). Sin
    él van las de `PIECES` (`default_piece`), que son las de la entrega.

    Si en algún frame evaluado las piezas se contradicen, da error. Con `report` (un diccionario) no da
    error: apunta el recuento en `report["conflictos"]` y sigue.
    """
    pieces = pieces or {}
    unknown = sorted(set(pieces) - set(PIECES))
    if unknown:
        raise ValueError("piezas desconocidas: {} (valen: {})".format(unknown, sorted(PIECES)))
    clean = pieces["ball"] if "ball" in pieces else default_piece("ball")
    team = pieces["candidates"] if "candidates" in pieces else default_piece("candidates")
    state = pieces["dead_state"] if "dead_state" in pieces else default_piece("dead_state")
    decode = pieces["temporal"] if "temporal" in pieces else default_piece("temporal")

    trk = clean(trk)
    evidences = [team(trk), state(trk)]
    evidences += [piece(trk) if callable(piece) else piece for piece in extra]
    score, allowed, conflict = combine(evidences, len(trk.bx))
    conflicts = int(sum(conflict[start:stop].sum() for start, stop in trk.blocks))
    if report is not None:
        report["conflictos"] = conflicts
    elif conflicts:
        raise ValueError("las piezas se contradicen en {} frames evaluados".format(conflicts))
    return decode(score, allowed, trk.blocks, params)


def write_submission(path, codes):
    """CSV `frame,label`. Siempre con saltos de línea `\\n`, para que salga igual en cualquier sistema."""
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    labels = tracking.LETTERS[codes]
    with open(path, "w", newline="\n") as handle:
        handle.write("frame,label\n")
        handle.writelines("{},{}\n".format(frame, label) for frame, label in enumerate(labels))
    return path


def summary(codes, blocks):
    """Agregados de una salida: frames por etiqueta, y posesiones y paradas por tramo evaluado."""
    lines = ["frames por etiqueta: " + "  ".join(
        "{} {}".format(letter, int(np.sum(codes == code))) for code, letter in enumerate(tracking.LETTERS))]
    for number, (start, stop) in enumerate(blocks, 1):
        window = codes[start:stop]
        starts = np.flatnonzero(np.concatenate(([True], window[1:] != window[:-1])))
        kinds = window[starts]
        lines.append("tramo {}: {} frames, {} posesiones ({} H, {} A), {} paradas".format(
            number, len(window), int(np.sum(kinds != tracking.D)), int(np.sum(kinds == tracking.H)),
            int(np.sum(kinds == tracking.A)), int(np.sum(kinds == tracking.D))))
    return lines


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(game=games.GAME, data_dir=None, params=None):
    """Las etiquetas del partido. Lee el ATD y el Smart Tagging: solo lo ejecuta una persona.

    Pide los ficheros antes de leer nada. El Smart Tagging lo usa dead_ball.evidence desde el 15/11, y sin
    él no hay entrega: el error dice qué falta y dónde se esperaba.
    """
    games.require(["atd_meta", "atd_raw", "smart_tagging"], game, data_dir)
    paths = games.asset_paths(game, data_dir)
    trk = tracking.from_atd(paths, game)
    report = {}
    anchors = lambda clean: dead_ball.evidence(clean, paths, game)  # noqa: E731
    codes = run(trk, extra=[anchors], params=params, report=report)
    return codes, trk.blocks, report


def shown(path):
    """La ruta relativa al repo, o la absoluta si está en otra unidad (en Windows relpath falla)."""
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return os.path.abspath(path)


def main():
    parser = argparse.ArgumentParser(description="Genera la entrega a partir del ATD del partido.")
    parser.add_argument("--name", default=DEFAULT_NAME, help="nombre del CSV, sin extensión")
    parser.add_argument("--out", default=RESULTS_DIR, help="carpeta de salida")
    args = parser.parse_args()

    codes, blocks, report = build()
    path = write_submission(os.path.join(args.out, args.name + ".csv"), codes)
    print("escrito {}".format(shown(path)))
    for line in summary(codes, blocks):
        print(line)
    print("frames con piezas en conflicto: {}".format(report["conflictos"]))
    print("sha256: {}".format(sha256(path)))
    if report["conflictos"]:
        print("\nHAY PIEZAS QUE SE CONTRADICEN: esta entrega no vale hasta arreglarlo.")
        sys.exit(1)
    print("\nAhora: python evaluation/validate_submission.py {}".format(shown(path)))


if __name__ == "__main__":
    main()
