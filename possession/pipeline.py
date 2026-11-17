"""El pipeline de punta a punta: del tracking a la entrega.

    python -m possession.pipeline                    # escribe evaluation/results/equipo_v0.csv
    python -m possession.pipeline --name mi_prueba
    python -m possession.pipeline --name prueba_b9 --pieza candidates=aprendida.evidence_b9   # de prueba

Lee el ATD y el Smart Tagging del partido, así que **solo lo ejecuta una persona**. Imprime solo agregados:
las versiones de Python y numpy, el commit del código, las líneas del ATD leídas y saltadas, posesiones,
paradas y rachas cortas
por tramo, los conflictos entre piezas y el sha256. Si hay conflictos, no escribe el CSV.

    tracking -> limpieza del balón -> evidencias (equipo, estado de D, anclas de D) -> decodificador -> CSV

`run()` es la parte que no toca ficheros: recibe un `Tracking` y devuelve las etiquetas. Es la que usa el
harness de la DFL (validation/harness/), con el mismo código de las piezas.
"""

import argparse
import hashlib
import importlib
import inspect
import os
import platform
import subprocess
import sys

import numpy as np

import games
from possession import aprendida, ball, candidates, dead_ball, dead_state, temporal, tracking, transiciones

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "evaluation", "results")
DEFAULT_NAME = "equipo_v0"

# Las capas del partido que la entrega suma a las piezas, además de las anclas de `dead_ball.evidence`. Solo las
# suma `build`, con las rutas del partido (`with_paths`) a las que las piden, así que no corren en el harness:
# - desde el 15/11, el empujón al equipo de cada «Attacking Transition» del Smart Tagging
#   (`transiciones.evidence_equipo`): pasó sus cuatro criterios escritos antes y el equipo decidió encenderlo
#   (docs/decisiones.md, «se enciende la capa de los contraataques»);
# - desde el 16/11, el balón visto fuera del campo (`dead_ball.ball_out`, D7): Ismael decidió encenderlo aunque
#   falló su criterio 1, porque pasó los dos de daño (docs/decisiones.md, «se enciende la capa del balón fuera»).
#   Va la última: es el orden de suma de la entrega de prueba `prueba_d7_v5`, para que salga su misma huella.
DELIVERY_LAYERS = (transiciones.evidence_equipo, dead_ball.ball_out)

# Las piezas que `run` deja cambiar por otra función (argumento `pieces`) y la función de cada una que va
# en la entrega: «funcion» de su módulo o «modulo.funcion». El harness de la DFL las usa para comparar
# versiones sin tocar este fichero.
# Desde el 14/11 la evidencia de equipo es B5 de la apuesta B (`aprendida.evidence_b5`), que ganó con los
# criterios fijados antes de medir (docs/decisiones.md). Antes era N1 (`candidates.evidence`).
# Desde el 16/11 el decodificador es `temporal.decode_cortas_a_d` (idea 1.3, PR 20): el Viterbi de `decode` y,
# después, las posesiones cortas que vienen de un cambio directo y acaban en `D` pasan a `D`. Pasó las cuatro
# condiciones del límite de daño, con el examen de SkillCorner, e Ismael decidió encenderlo (docs/decisiones.md,
# «se enciende "cortas a D"»). Antes era `decode`.
# Desde el 17/11 la evidencia de equipo es K2, el modelo conjunto (`aprendida.evidence_k2`, `possession/conjunto.py`):
# cumplió los cuatro puntos de su regla, con el examen de SkillCorner y la entrega de prueba `prueba_k2`, y David decidió
# encenderlo (docs/decisiones.md, «se enciende K2»). Antes era B5 (`aprendida.evidence_b5`).
# Desde el 17/11 por la tarde es K3 (`aprendida.evidence_k3`, `possession/refinamientos.py`): la media a partes
# iguales del logit de K2 y del de B5, puntuada como B5. Pasó su entrega de prueba frente a `equipo_v10` (C0 a C6) e
# Ismael decidió encenderla (docs/decisiones.md, «se enciende K3»). Antes era K2 sola (`aprendida.evidence_k2`).
PIECES = {"ball": "clean", "candidates": "aprendida.evidence_k3", "dead_state": "evidence",
          "temporal": "decode_cortas_a_d"}
MODULES = {"ball": ball, "candidates": candidates, "dead_state": dead_state, "temporal": temporal,
           "aprendida": aprendida}


def default_piece(name):
    """La función de la entrega de una pieza, según `PIECES`."""
    spec = PIECES[name]
    module, function = spec.split(".", 1) if "." in spec else (name, spec)
    return getattr(MODULES[module], function)


# Los módulos de los que `--capa` puede tomar una evidencia extra (ver `resolve`). Además, cualquier otro
# módulo de possession/ (`possession.<modulo>`), para enchufar una capa nueva sin tocar este fichero.
LAYER_MODULES = dict(MODULES, dead_ball=dead_ball)


def resolve(spec, modules=MODULES, any_possession_module=False):
    """La función «modulo.funcion» de `modules` (o de possession/, si se permite). Error claro si no existe."""
    module, _, function = spec.partition(".")
    found = modules.get(module)
    if found is None and any_possession_module and module.isidentifier():
        try:
            found = importlib.import_module("possession." + module)
        except ImportError:
            found = None
    if found is None or not function or not callable(getattr(found, function, None)):
        raise ValueError("no encuentro «{}»: tiene que ser modulo.funcion, con modulo uno de {}{}".format(
            spec, sorted(modules), " o de possession/" if any_possession_module else ""))
    return getattr(found, function)


def with_paths(layer, paths, game):
    """La capa tal cual si solo recibe el tracking; si tiene `paths` (como dead_ball.evidence), con las rutas.

    Así una capa que lee el Smart Tagging se enchufa con `--capa` igual que una que solo mira el tracking.
    """
    names = inspect.signature(layer).parameters
    if "paths" not in names:
        return layer
    if "game" in names:
        return lambda clean: layer(clean, paths=paths, game=game)
    return lambda clean: layer(clean, paths=paths)


def overrides(piece_specs=(), layer_specs=()):
    """Las piezas cambiadas (`--pieza nombre=modulo.funcion`) y las capas añadidas (`--capa modulo.funcion`).

    Devuelve `(pieces, layers)`: el diccionario para `run(pieces=...)` y la lista de evidencias extra, que
    reciben el tracking con el balón ya limpio. Sirve para escribir una entrega de prueba con otra pieza o
    con una capa encendida sin tocar `PIECES`.
    """
    pieces = {}
    for spec in piece_specs:
        name, _, function = spec.partition("=")
        if name not in PIECES:
            raise ValueError("pieza desconocida en --pieza: «{}» (valen: {})".format(name, sorted(PIECES)))
        pieces[name] = resolve(function)
    return pieces, [resolve(spec, LAYER_MODULES, any_possession_module=True) for spec in layer_specs]


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


def run(trk, extra=(), params=None, report=None, pieces=None, cambios=None):
    """Etiquetas por frame (códigos de possession/tracking.py) a partir de un `Tracking`.

    `extra`: evidencias que se suman a las del tracking. Cada una es `(score, allowed)` ya calculada, o
    una función que recibe el tracking **con el balón ya limpio** y la devuelve. En el partido es
    `dead_ball.evidence`; en el harness, por ejemplo, el `D` copiado de las etiquetas.

    `params` son los del decodificador.

    `pieces` cambia alguna pieza por otra función con la misma firma, para comparar versiones en el
    harness: un diccionario con claves de `PIECES` ("ball", "candidates", "dead_state" y "temporal"). Sin
    él van las de `PIECES` (`default_piece`), que son las de la entrega.

    `cambios` (candidato del 16/11, apagado: docs/decisiones.md) es la rebaja del coste de cambiar de equipo en
    cada frame, de forma (n, 2), o una función que recibe el tracking con el balón ya limpio y la devuelve
    (`cambios.rebaja`). Con ella decodifica `temporal.decode_cambios`, salvo que `pieces` nombre otro
    decodificador, que tiene que aceptar `bonus`. Con `None`, el valor por defecto, nada cambia.

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
    if cambios is None:
        return decode(score, allowed, trk.blocks, params)
    if "temporal" not in pieces:
        decode = temporal.decode_cambios
    return decode(score, allowed, trk.blocks, params, bonus=cambios(trk) if callable(cambios) else cambios)


def write_submission(path, codes):
    """CSV `frame,label`. Siempre con saltos de línea `\\n`, para que salga igual en cualquier sistema.

    Escribe primero `<nombre>.a_medias.csv` y después lo renombra: si se corta a medias, no queda un CSV a
    medias con el nombre bueno. El de a medias acaba en `.csv` para que, si queda en la carpeta por defecto
    (evaluation/results/), git lo ignore y Claude no lo pueda leer, como cualquier entrega (.gitignore y
    .claude/settings.json). En otra carpeta no vale, igual que con la propia entrega.
    """
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    labels = tracking.LETTERS[codes]
    root, extension = os.path.splitext(path)
    partial = root + ".a_medias" + extension
    with open(partial, "w", newline="\n") as handle:
        handle.write("frame,label\n")
        handle.writelines("{},{}\n".format(frame, label) for frame, label in enumerate(labels))
    os.replace(partial, path)
    return path


# Cotas de las rachas cortas del resumen: la duración mínima de posesión que probó David (12 frames) y la
# del criterio del 13/11, «ninguna racha de `D` ni de juego de menos de 25 frames» (1 s).
SHORT_RUNS = (12, 25)


def _runs(mask):
    """Largo de cada racha de True de `mask`."""
    edges = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    return np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)


def short_runs(window):
    """Rachas cortas de una salida: {(tipo, cota): cuántas}.

    - "posesiones": rachas de `H` o de `A` (una posesión de `H` entre dos de `A` es una racha);
    - "juego": rachas de juego, `H` y `A` juntos, entre paradas (las del criterio del 13/11);
    - "paradas": rachas de `D`.

    Se cuentan dentro de `window`, como las ve el scorer en un tramo evaluado: la primera y la última quedan
    cortadas por el borde y cuentan con lo que queda dentro.
    """
    lengths = {"posesiones": np.concatenate((_runs(window == tracking.H), _runs(window == tracking.A))),
               "juego": _runs((window == tracking.H) | (window == tracking.A)),
               "paradas": _runs(window == tracking.D)}
    return {(kind, limit): int(np.sum(lengths[kind] < limit)) for kind in lengths for limit in SHORT_RUNS}


def summary(codes, blocks):
    """Agregados de una salida: frames por etiqueta, posesiones y paradas por tramo evaluado, y rachas cortas."""
    lines = ["frames por etiqueta: " + "  ".join(
        "{} {}".format(letter, int(np.sum(codes == code))) for code, letter in enumerate(tracking.LETTERS))]
    for number, (start, stop) in enumerate(blocks, 1):
        window = codes[start:stop]
        starts = np.flatnonzero(np.concatenate(([True], window[1:] != window[:-1])))
        kinds = window[starts]
        lines.append("tramo {}: {} frames, {} posesiones ({} H, {} A), {} paradas".format(
            number, len(window), int(np.sum(kinds != tracking.D)), int(np.sum(kinds == tracking.H)),
            int(np.sum(kinds == tracking.A)), int(np.sum(kinds == tracking.D))))
        short = short_runs(window)
        lines.append("tramo {}, rachas cortas: {}".format(number, "; ".join(
            "de menos de {} frames, {} posesiones, {} de juego y {} paradas".format(
                limit, short["posesiones", limit], short["juego", limit], short["paradas", limit])
            for limit in SHORT_RUNS)))
    return lines


def atd_lines(counts):
    """Las líneas del ATD que se leyeron y las que se saltaron (tracking.from_files). Solo recuentos."""
    text = ("líneas del ATD: {lineas} leídas, {validas} válidas; saltadas: {vacias} vacías, {mal_formadas} mal "
            "formadas y {fuera_de_rango} con el frame fuera de rango; {repetidas} líneas repetidas; frames sin "
            "línea: {frames_sin_linea}, {frames_evaluados_sin_linea} de ellos evaluados").format(**counts)
    odd = sum(counts[key] for key in ("vacias", "mal_formadas", "fuera_de_rango", "repetidas",
                                      "frames_evaluados_sin_linea"))
    if odd:
        text += "\nOJO: el lector se ha saltado o repetido líneas, o faltan frames evaluados. Apúntalo."
    return text


# Lo que el ATD del partido no puede tener: el 15/11, con d6bd128, Ismael midió todo a 0 (docs/decisiones.md).
# Si cambia (un fichero cortado, otro ATD), la entrega no se genera en silencio.
ATD_MUST_BE_ZERO = ("vacias", "mal_formadas", "fuera_de_rango", "repetidas", "frames_sin_linea")


def check_atd(counts):
    """Error si el ATD tiene alguna línea saltada o repetida, o algún frame sin línea. El error lleva solo
    recuentos (`atd_lines`), así que se puede pegar a Claude."""
    if any(counts[key] for key in ATD_MUST_BE_ZERO):
        raise ValueError("el ATD no es como el del 15/11 (ninguna línea saltada ni frame sin línea), así que "
                         "no se genera la entrega.\n" + atd_lines(counts))


# Lo que genera la entrega: si cambia algo aquí sin commitear, el CSV no sale del commit que se imprime.
DELIVERY_CODE = ("possession", "games.py", "starter", "requirements-entrega.txt")


def code_version():
    """El commit con el que se genera y si el código de la entrega tiene cambios sin commitear. Sin git, lo dice."""
    def git(*args):
        return subprocess.run(["git", "-C", ROOT] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=30)
    try:
        head = git("rev-parse", "--short", "HEAD")
        local = git("status", "--porcelain", "--", *DELIVERY_CODE)
    except (OSError, subprocess.SubprocessError):
        return "código: sin git"
    if head.returncode or local.returncode:
        return "código: sin git"
    estado = ("CON CAMBIOS SIN COMMITEAR en el código de la entrega" if local.stdout.strip()
              else "sin cambios locales en el código de la entrega")
    return "código: commit {}, {}".format(head.stdout.strip(), estado)


def versions():
    """Python y numpy con los que se ha generado. La huella solo se repite con los mismos (requirements.txt)."""
    return "python {}, numpy {}".format(platform.python_version(), np.__version__)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(game=games.GAME, data_dir=None, params=None, pieces=None, layers=()):
    """Las etiquetas del partido. Lee el ATD y el Smart Tagging: solo lo ejecuta una persona.

    Pide los ficheros antes de leer nada. El Smart Tagging lo usa dead_ball.evidence desde el 15/11, y sin
    él no hay entrega: el error dice qué falta y dónde se esperaba. Si el ATD tiene alguna línea saltada o
    repetida, o algún frame sin línea, también da error (`check_atd`).

    Suma las anclas de `dead_ball.evidence` y las capas de DELIVERY_LAYERS, con las rutas del partido a las que
    las piden (`with_paths`). `pieces` y `layers` son para entregas de prueba (`overrides`): sin ellos, la
    entrega. Una capa de `layers` que ya está en DELIVERY_LAYERS da error: se sumaría dos veces sin avisar.
    """
    repeated = [layer for layer in layers if layer in DELIVERY_LAYERS]
    if repeated:
        raise ValueError("la capa {} ya va en la entrega (DELIVERY_LAYERS): con --capa se sumaría dos veces".format(
            ", ".join(layer.__module__.split(".")[-1] + "." + layer.__name__ for layer in repeated)))
    games.require(["atd_meta", "atd_raw", "smart_tagging"], game, data_dir)
    paths = games.asset_paths(game, data_dir)
    report = {}
    trk = tracking.from_atd(paths, game, report=report)
    check_atd(report["atd"])
    anchors = lambda clean: dead_ball.evidence(clean, paths, game)  # noqa: E731
    layers = [with_paths(layer, paths, game) for layer in tuple(DELIVERY_LAYERS) + tuple(layers)]
    codes = run(trk, extra=[anchors] + layers, params=params, report=report, pieces=pieces)
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
    parser.add_argument("--pieza", action="append", default=[], metavar="NOMBRE=MODULO.FUNCION",
                        help="entrega de prueba: cambia una pieza de PIECES (candidates=aprendida.evidence_b9)")
    parser.add_argument("--capa", action="append", default=[], metavar="MODULO.FUNCION",
                        help="entrega de prueba: suma una evidencia, que recibe el tracking con el balón limpio")
    args = parser.parse_args()

    pieces, layers = overrides(args.pieza, args.capa)
    if (pieces or layers) and args.name == DEFAULT_NAME:
        print("Una entrega de prueba (--pieza o --capa) necesita su propio --name: así no se confunde con la "
              "entrega.")
        sys.exit(2)
    codes, blocks, report = build(pieces=pieces, layers=layers)
    path = os.path.join(args.out, args.name + ".csv")
    print(versions())
    print(code_version())
    print("piezas: {}".format("; ".join(["{} cambiada por {}".format(*spec.split("=", 1)) for spec in args.pieza]
                                        + ["capa añadida {}".format(spec) for spec in args.capa])
                              or "las de la entrega (PIECES y DELIVERY_LAYERS), sin capas añadidas"))
    print(atd_lines(report["atd"]))
    for line in summary(codes, blocks):
        print(line)
    print("frames con piezas en conflicto: {}".format(report["conflictos"]))
    if report["conflictos"]:
        # Se decide antes de escribir: un CSV con piezas en conflicto no se queda con el nombre bueno.
        print("\nHAY PIEZAS QUE SE CONTRADICEN: no se escribe {}. Esta salida no vale hasta arreglarlo.".format(
            shown(path)))
        if os.path.exists(path):
            print("Ojo: ya había un {} de antes, y no es esta salida.".format(shown(path)))
        sys.exit(1)
    write_submission(path, codes)
    print("escrito {}".format(shown(path)))
    print("sha256: {}".format(sha256(path)))
    print("\nAhora: python evaluation/validate_submission.py {}".format(shown(path)))


if __name__ == "__main__":
    main()
