"""Prueba el esqueleto del pipeline (possession/) sin datos del partido: todo el tracking es inventado.

    python validation/scripts/prueba_pipeline.py

Comprueba la interfaz de las piezas, los tramos evaluados, el tramo antes del saque, el decodificador
(contra la búsqueda exhaustiva), los errores que no pueden pasar en silencio, el determinismo, el CSV, el
resumen (rachas cortas), que el comando no escribe el CSV si hay conflictos, y el lector del ATD con un
fichero sintético, también con líneas raras y frames que faltan.

Nunca llama a `pipeline.main()` tal cual, que lee el partido: solo con `pipeline.build` cambiado por uno
que devuelve las etiquetas del partido inventado, con `games.require` y `games.asset_paths` cambiados por
uno que da error y escribiendo en la carpeta temporal. A `pipeline.build()` solo lo llama con
`games.require` cambiado por uno que corta antes de leer nada, con una carpeta temporal vacía como datos y
sin poder abrir ficheros. Además, mientras ejecuta las piezas, abrir cualquier fichero es un error
(`no_files`).

Sale con código 1 si falla alguna comprobación. Claude puede ejecutarlo (validation/README.md).
"""

import builtins
import contextlib
import io
import itertools
import os
import shutil
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import games  # noqa: E402
import possession_metrics as pm  # noqa: E402
from possession import aprendida, ball, candidates, dead_ball, dead_state, pipeline, temporal, tracking  # noqa: E402
from possession import io as io_atd  # noqa: E402
from possession.io import COUNT_KEYS  # noqa: E402
from starter import baseline  # noqa: E402

SEED = 20261114
GAME = games.GAME
GRADED_FRAMES = 158857  # EVALUATION.md: frames evaluados de las dos partes
PRE_KICKOFF_FRAMES = 2934  # FAQ.md: frames `D` antes del saque de la 2ª parte
H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X

failures = []


def check(name, ok, detail=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", name, "   " + detail if detail else ""))
    if not ok:
        failures.append(name)


def safe_tmp():
    """Carpeta temporal para los ficheros inventados. Se niega a usar la de los datos del partido."""
    folder = os.path.realpath(tempfile.mkdtemp(prefix="mtah_prueba_"))
    data = os.path.realpath(games.DATA_DIR)
    if folder == data or folder.startswith(data + os.sep) or "mtah2027-data" in folder.lower():
        raise SystemExit("la carpeta temporal cae dentro de los datos del partido: no se ejecuta")
    return folder


@contextlib.contextmanager
def no_files():
    """Dentro de este bloque, abrir un fichero es un error: las piezas trabajan con arrays.

    Es la guarda de la regla nº 1 para esta prueba. Si una pieza acabara leyendo un fichero del partido
    al llamarla sin rutas, fallaría aquí en vez de leerlo.
    """
    real_open, real_io_open = builtins.open, io.open

    def refuse(*args, **kwargs):
        raise AssertionError("una pieza ha intentado abrir un fichero")

    builtins.open = io.open = refuse
    try:
        yield
    finally:
        builtins.open, io.open = real_open, real_io_open


def raises(error, call):
    try:
        call()
    except error:
        return True
    return False


def synthetic_tracking(n, blocks, pitch, rng, slots_per_team=23):
    """Jugadores con paseo aleatorio y un balón que va de un jugador a otro. Nada sale del partido."""
    length, width = pitch
    slots = 2 * slots_per_team
    px = np.cumsum(rng.normal(0.0, 0.15, (n, slots)), axis=0, dtype=np.float32)
    py = np.cumsum(rng.normal(0.0, 0.15, (n, slots)), axis=0, dtype=np.float32)
    px = np.abs((px + rng.uniform(0, length, slots).astype(np.float32)) % (2 * length) - length)
    py = np.abs((py + rng.uniform(0, width, slots).astype(np.float32)) % (2 * width) - width)
    team = np.repeat(np.array([0, 1], dtype=np.int8), slots_per_team)

    # El balón sigue a un slot durante un rato y salta a otro.
    holder = np.empty(n, dtype=np.int64)
    t = 0
    while t < n:
        span = int(rng.geometric(1.0 / 120))
        holder[t:t + span] = rng.integers(0, slots)
        t += span
    rows = np.arange(n)
    bx = px[rows, holder].astype(np.float64) + rng.normal(0.0, 0.3, n)
    by = py[rows, holder].astype(np.float64) + rng.normal(0.0, 0.3, n)

    # Huecos: el balón falta a ratos y cada slot desaparece a ratos.
    def gaps(rate, mean):
        hidden = np.zeros(n, dtype=bool)
        t = 0
        while t < n:
            visible = int(rng.geometric(rate))
            t += visible
            span = int(rng.geometric(1.0 / mean))
            hidden[t:t + span] = True
            t += span
        return hidden

    lost = gaps(1.0 / 60, 40)
    bx[lost], by[lost] = np.nan, np.nan
    for slot in range(slots):
        gone = gaps(1.0 / 400, 300)
        px[gone, slot], py[gone, slot] = np.nan, np.nan
    return tracking.Tracking(bx, by, px, py, team, tuple(pitch), tuple(blocks), 25)


def check_interface(trk):
    print("Interfaz de las piezas")
    n = len(trk.bx)
    for name, piece in (("candidates", candidates.evidence(trk)), ("aprendida (B5, la de la entrega)",
                         aprendida.evidence_b5(trk)), ("dead_state", dead_state.evidence(trk)),
                        ("dead_ball", dead_ball.evidence(trk, None, GAME))):
        score, allowed = piece
        check("{}.evidence devuelve (score, allowed) de forma (n, 3)".format(name),
              score.shape == (n, 3) and allowed.shape == (n, 3) and allowed.dtype == bool
              and np.issubdtype(score.dtype, np.floating) and bool(np.all(np.isfinite(score))))


def check_pipeline(trk):
    print("Pipeline sobre un partido inventado del tamaño del real")
    n = len(trk.bx)
    graded = np.zeros(n, dtype=bool)
    for start, stop in trk.blocks:
        graded[start:stop] = True
    report = {}
    extra = [dead_ball.evidence(trk, None, GAME)]
    codes = pipeline.run(trk, extra=extra, report=report)
    check("una etiqueta por frame de vídeo", codes.shape == (n,) and codes.dtype == np.int8,
          "{} frames".format(len(codes)))
    check("frames evaluados = {}".format(GRADED_FRAMES), int(graded.sum()) == GRADED_FRAMES,
          "{}".format(int(graded.sum())))
    check("X fuera de los tramos evaluados y nunca dentro", bool(np.array_equal(codes == X, ~graded)))
    before = dead_ball.pre_kickoff(GAME)
    check("el tramo antes del saque de la 2ª parte sale `D`",
          int(before.sum()) == PRE_KICKOFF_FRAMES and bool(np.all(codes[before] == D)),
          "{} frames".format(int(before.sum())))
    check("ninguna pieza se contradice con otra", report["conflictos"] == 0)
    again = pipeline.run(trk, extra=extra)
    check("dos ejecuciones dan lo mismo", bool(np.array_equal(codes, again)))
    return codes


def objective(path, emission, cost):
    total = emission[0][path[0]]
    for t in range(1, len(path)):
        total += emission[t][path[t]] - cost[path[t - 1]][path[t]]
    return total


def check_decoder(rng):
    print("Decodificador")
    worst = 0.0
    for _ in range(200):
        n = int(rng.integers(2, 8))
        score = rng.normal(0.0, 2.0, (n, 3))
        allowed = rng.random((n, 3)) > 0.2
        allowed[np.arange(n), rng.integers(0, 3, n)] = True
        params = {"switch": float(rng.uniform(0, 4)), "to_dead": float(rng.uniform(0, 4)),
                  "from_dead": float(rng.uniform(0, 4))}
        cost = temporal.cost_matrix(params)
        emission = np.where(allowed, score, -np.inf)
        got = temporal.decode(score, allowed, [(0, n)], params)
        best = max(objective(p, emission, cost) for p in itertools.product(range(3), repeat=n))
        worst = max(worst, abs(best - objective(got, emission, cost)))
    check("da el mismo total que la búsqueda exhaustiva (200 casos)", worst < 1e-9,
          "dif. máx. {:.1e}".format(worst))

    def team_score(spans):
        rows = []
        for state, span in spans:
            row = np.zeros((span, 3))
            row[:, state] = 1.0
            rows.append(row)
        return np.vstack(rows)

    score = team_score([(H, 200), (A, 10), (H, 200)])
    out = temporal.decode(score, np.ones(score.shape, bool), [(0, len(score))], {"switch": 25.0})
    check("una isla de 10 frames con coste 25 no crea una posesión", bool(np.all(out == H)))
    score = team_score([(H, 200), (A, 80), (H, 200)])
    out = temporal.decode(score, np.ones(score.shape, bool), [(0, len(score))], {"switch": 25.0})
    expected = np.concatenate([np.full(200, H), np.full(80, A), np.full(200, H)])
    check("una racha de 80 frames sí, y con las fronteras en su frame", bool(np.array_equal(out, expected)))
    allowed = np.ones((100, 3), bool)
    allowed[40:60, :2] = False
    out = temporal.decode(team_score([(H, 100)]), allowed, [(0, 100)])
    check("lo prohibido se respeta", bool(np.all(out[40:60] == D)) and bool(np.all(out[:40] == H)))
    out = temporal.decode(np.zeros((50, 3)), np.ones((50, 3), bool), [(10, 40)])
    check("sin evidencia, el empate se resuelve siempre igual y fuera del tramo va X",
          bool(np.all(out[10:40] == H)) and bool(np.all(out[:10] == X)) and bool(np.all(out[40:] == X)))


def check_guards(rng):
    print("Errores que no pueden pasar en silencio")
    free = np.ones((50, 3), bool)
    broken = np.zeros((50, 3))
    broken[20, A] = np.nan
    check("un NaN en la evidencia de un frame evaluado da error",
          raises(ValueError, lambda: temporal.decode(broken, free, [(0, 50)])))
    check("fuera de los tramos evaluados no importa",
          bool(np.all(temporal.decode(broken, free, [(30, 50)])[30:] == H)))
    check("un parámetro mal escrito da error",
          raises(KeyError, lambda: temporal.decode(np.zeros((50, 3)), free, [(0, 50)], {"swich": 1.0})))
    check("un coste negativo da error",
          raises(ValueError, lambda: temporal.decode(np.zeros((50, 3)), free, [(0, 50)], {"switch": -1.0})))

    trk = synthetic_tracking(400, [(50, 350)], (105.0, 68.0), rng, slots_per_team=5)
    n = len(trk.bx)
    narrow = (np.zeros((n, 1)), np.ones((n, 1), bool))
    check("una pieza que no devuelve arrays de forma (n, 3) da error",
          raises(ValueError, lambda: pipeline.run(trk, extra=[narrow])))
    only_dead = tracking.no_evidence(n)
    only_dead[1][100:140, :2] = False
    never_dead = tracking.no_evidence(n)
    never_dead[1][120:130, D] = False
    check("dos piezas que se contradicen dan error",
          raises(ValueError, lambda: pipeline.run(trk, extra=[only_dead, never_dead])))
    report = {}
    pipeline.run(trk, extra=[only_dead, never_dead], report=report)
    check("con `report` se cuentan los frames en conflicto en vez de dar error", report["conflictos"] == 10,
          "{} frames".format(report["conflictos"]))
    direct = pipeline.run(trk, extra=[only_dead])
    lazy = pipeline.run(trk, extra=[lambda clean: only_dead])
    check("una evidencia extra vale igual ya calculada que como función",
          bool(np.array_equal(direct, lazy)) and bool(np.all(direct[100:140] == D)))


def check_pieces(rng):
    print("Cambiar una pieza por otra función (lo que usa el harness para comparar versiones)")
    trk = synthetic_tracking(400, [(50, 350)], (105.0, 68.0), rng, slots_per_team=5)
    block = slice(50, 350)
    explicit = {name: pipeline.default_piece(name) for name in pipeline.PIECES}
    check("PIECES nombra las funciones que usa `run` por defecto (la de equipo, B5 desde el 14/11)",
          explicit == {"ball": ball.clean, "candidates": aprendida.evidence_b5,
                       "dead_state": dead_state.evidence, "temporal": temporal.decode})
    base = pipeline.run(trk)
    check("sin `pieces`, con {} y con las de PIECES una a una sale lo mismo",
          bool(np.array_equal(base, pipeline.run(trk, pieces={})))
          and bool(np.array_equal(base, pipeline.run(trk, pieces=explicit))))

    seen = []

    def no_ball(t):
        seen.append(len(t.bx))
        return t._replace(bx=np.full_like(t.bx, np.nan), by=np.full_like(t.by, np.nan))

    # Cada comprobación cambia una pieza y deja callada la de `D` de estado: así prueba solo lo que dice,
    # opine lo que opine `dead_state.evidence` (con un modelo, el partido inventado puede salir todo `D`).
    def silent(t):
        return tracking.no_evidence(len(t.bx))

    # N1 a mano: sin balón se calla, así que todo sale `H`. B5, la de la entrega, opina también con los jugadores.
    out = pipeline.run(trk, pieces={"ball": no_ball, "dead_state": silent, "candidates": candidates.evidence})
    check("la limpieza cambiada se usa, y las demás piezas reciben su tracking",
          seen == [len(trk.bx)] and bool(np.all(out[block] == H)))

    def always_a(t):
        score, allowed = tracking.no_evidence(len(t.bx))
        score[:, A] = 1.0
        return score, allowed

    out = pipeline.run(trk, pieces={"candidates": always_a, "dead_state": silent})
    check("la evidencia de equipo cambiada se usa", bool(np.all(out[block] == A)) and bool(np.all(out[:50] == X)))
    out = pipeline.run(trk, pieces={"temporal": lambda score, allowed, blocks, params: np.full(len(score), D)})
    check("el decodificador cambiado se usa", bool(np.all(out == D)))
    check("una pieza que no existe da error",
          raises(ValueError, lambda: pipeline.run(trk, pieces={"decoder": temporal.decode})))


def check_build_requires(folder):
    print("Ficheros que pide la entrega")
    asked = []

    class Stop(Exception):
        pass

    def cut(names, *args, **kwargs):
        asked.extend(names)
        raise Stop()

    real = games.require
    games.require = cut
    try:
        with no_files():  # aunque build cambiara de orden, no podría abrir nada
            stopped = raises(Stop, lambda: pipeline.build(data_dir=folder))
    finally:
        games.require = real
    wanted = {"atd_meta", "atd_raw", "smart_tagging"}
    check("pipeline.build pide el ATD y el Smart Tagging (dead_ball) antes de leer nada",
          stopped and wanted <= set(asked), "pide {}".format(sorted(asked)))

    # Un ATD con algo raro: build da error antes de seguir. tracking.from_atd cambiado por uno que solo rellena
    # el recuento, y games.require por uno que no hace nada: no se lee ningún fichero.
    reached = []

    def fake_from_atd(paths, game, report=None):
        report["atd"] = dict(counts, frames_sin_linea=3, frames_evaluados_sin_linea=1)
        return None

    def must_not_run(*args, **kwargs):
        reached.append(True)
        raise AssertionError("build ha seguido con un ATD raro")

    counts = dict.fromkeys(COUNT_KEYS, 0)
    counts.update(lineas=10, validas=10, frames_evaluados_sin_linea=0)
    real = games.require, games.asset_paths, tracking.from_atd, pipeline.run
    games.require = lambda *args, **kwargs: None
    games.asset_paths = lambda *args, **kwargs: {}
    tracking.from_atd, pipeline.run = fake_from_atd, must_not_run
    message = ""
    try:
        with no_files():
            pipeline.build(data_dir=folder)
    except ValueError as error:
        message = str(error)
    finally:
        games.require, games.asset_paths, tracking.from_atd, pipeline.run = real
    check("con frames sin línea en el ATD, build da error con el recuento y no sigue",
          "no se genera la entrega" in message and "frames sin línea: 3" in message and not reached)
    bad = [key for key in pipeline.ATD_MUST_BE_ZERO
           if not raises(ValueError, lambda key=key: pipeline.check_atd(dict(counts, **{key: 1})))]
    check("cualquier línea vacía, mal formada, fuera de rango o repetida, o frame sin línea, da error",
          not bad and not raises(ValueError, lambda: pipeline.check_atd(counts)),
          "no da error: {}".format(bad) if bad else "")

    # Con un ATD sin nada raro, build pasa a run la pieza cambiada y la capa añadida, detrás de las anclas.
    seen = {}
    trk_without_blocks = tracking.Tracking(*([None] * 6), (), 25)

    def clean_from_atd(paths, game, report=None):
        report["atd"] = dict(counts)
        return trk_without_blocks

    def record(trk, extra=(), params=None, report=None, pieces=None):
        seen.update(extra=list(extra), pieces=pieces)
        return None

    def layer(trk):
        return None

    real = games.require, games.asset_paths, tracking.from_atd, pipeline.run
    games.require = lambda *args, **kwargs: None
    games.asset_paths = lambda *args, **kwargs: {}
    tracking.from_atd, pipeline.run = clean_from_atd, record
    try:
        with no_files():
            pipeline.build(data_dir=folder, pieces={"candidates": candidates.evidence}, layers=[layer])
    finally:
        games.require, games.asset_paths, tracking.from_atd, pipeline.run = real
    check("build pasa a run la pieza cambiada y la capa, además de las anclas de dead_ball",
          seen.get("pieces") == {"candidates": candidates.evidence} and len(seen.get("extra", [])) == 2
          and seen["extra"][1] is layer)


def check_csv(codes, folder):
    print("CSV de la entrega")
    path = pipeline.write_submission(os.path.join(folder, "prueba.csv"), codes)
    with open(path, "rb") as handle:
        raw = handle.read()
    check("saltos de línea \\n, sin \\r", b"\r" not in raw and raw.count(b"\n") == len(codes) + 1)
    reason = pm.validate_submission(pm.read_label_csv(path), len(codes))
    check("pasa la validación oficial", reason is None, reason or "")
    first = pipeline.sha256(path)
    pipeline.write_submission(path, codes)
    check("el fichero se regenera byte a byte", first == pipeline.sha256(path))


def check_reader(folder, rng):
    print("Lector del ATD con un fichero inventado")
    n, slots, pitch = 60, 6, (100.0, 60.0)
    raw = os.path.join(folder, "inventado_atd.txt")
    meta = os.path.join(folder, "inventado_atd.xml")
    xs, ys = rng.random((n, slots)), rng.random((n, slots))
    ball = rng.random((n, 2))
    no_ball = rng.random(n) < 0.3
    no_slot = rng.random((n, slots)) < 0.3
    with open(raw, "w", newline="\n") as handle:
        for f in range(n):
            groups = ["NaN" if (no_slot[f, s] and s % 2) else "NaN,NaN,NaN" if no_slot[f, s]
                      else "{:.6f},{:.6f},1.0".format(xs[f, s], ys[f, s]) for s in range(slots)]
            b = ("NaN" if f % 2 else "NaN,NaN,NaN") if no_ball[f] else "{:.6f},{:.6f},2.0".format(*ball[f])
            handle.write("{}:{}:{}\n".format(f + 1, ";".join(groups), b))
    with open(meta, "w", newline="\n") as handle:
        handle.write("<Root><Teams><Team id=\"L\"><Name>Local</Name></Team>"
                     "<Team id=\"V\"><Name>Visitante</Name></Team></Teams><Players>")
        handle.write("".join("<Player teamId=\"{}\"/>".format("L" if s < slots // 2 else "V")
                             for s in range(slots)))
        handle.write("</Players></Root>")
    trk = tracking.from_files(raw, meta, n, pitch, [(0, n)], 25)
    check("balón: NaN donde falta y metros donde no",
          bool(np.array_equal(np.isnan(trk.bx), no_ball))
          and bool(np.allclose(trk.bx[~no_ball], ball[~no_ball, 0] * pitch[0], atol=1e-3)))
    check("jugadores: NaN donde falta el slot y metros donde no",
          bool(np.array_equal(np.isnan(trk.px), no_slot))
          and bool(np.allclose(trk.py[~no_slot], (ys * pitch[1])[~no_slot], atol=1e-3)))
    check("equipo de cada slot según los metadatos", trk.team.tolist() == [0, 0, 0, 1, 1, 1])
    ours = candidates.nearest_team(trk)
    theirs = baseline.nearest_player_labels(raw, baseline.team_of_each_track(meta), n, pitch)
    check("el candidato v0 coincide con el jugador más cercano del baseline oficial",
          bool(np.array_equal(ours, theirs)), "{} frames con balón".format(int(np.sum(ours >= 0))))
    check("la copia del más cercano que usa B5 (la entrega) también coincide con el baseline oficial",
          bool(np.array_equal(aprendida.equipo_mas_cercano(trk), theirs)))

    report = {}
    counted = tracking.from_files(raw, meta, n, pitch, [(0, n)], 25, report=report)
    check("con el recuento, el lector lee lo mismo", same_tracking(trk, counted))
    clean = dict.fromkeys(COUNT_KEYS, 0)
    clean.update(lineas=n, validas=n, frames_evaluados_sin_linea=0)
    check("ATD sin nada raro: todas las líneas válidas y ningún frame sin línea", report["atd"] == clean,
          "{}".format(report["atd"]))
    check("el resumen no avisa si no hay nada raro", "OJO" not in pipeline.atd_lines(report["atd"]))

    # El mismo ATD con un caso de cada: falta un frame evaluado y el último (no evaluado), un frame repetido
    # (la misma línea), una línea vacía, una mal formada y un frame fuera de rango.
    with open(raw) as handle:
        rows = handle.read().splitlines()
    missing = (9, n - 1)
    kept = [row for frame, row in enumerate(rows) if frame not in missing]
    kept.insert(30, rows[19])
    kept += ["", "esto no es una línea del ATD", "{}:{}".format(n + 7, rows[0].split(":", 1)[1])]
    odd = os.path.join(folder, "inventado_atd_raro.txt")
    with open(odd, "w", newline="\n") as handle:
        handle.write("\n".join(kept) + "\n")
    report = {}
    got = tracking.from_files(odd, meta, n, pitch, [(0, n - 5)], 25, report=report)
    expected = dict(lineas=n + 2, validas=n - 1, vacias=1, mal_formadas=1, fuera_de_rango=1, repetidas=1,
                    frames_sin_linea=2, frames_evaluados_sin_linea=1)
    check("ATD con un caso raro de cada tipo: los cuenta todos", report["atd"] == expected,
          "{}".format(report["atd"]))
    blank = trk._replace(bx=trk.bx.copy(), by=trk.by.copy(), px=trk.px.copy(), py=trk.py.copy())
    for array in (blank.bx, blank.by, blank.px, blank.py):
        array[list(missing)] = np.nan
    check("y lee lo mismo que antes: los frames sin línea quedan sin balón ni jugadores",
          same_tracking(blank, got))
    check("el resumen avisa", "OJO" in pipeline.atd_lines(report["atd"]))
    check("el recuento solo lleva enteros (se puede pegar a Claude)",
          all(type(value) is int for value in report["atd"].values()))

    # Un frame_id que no es un entero y un valor que no es un número: error, sin el texto del ATD.
    raro = "0z517"  # el valor que no es un número, en un jugador y en el balón
    for label, row, shown in (("frame_id", "x{}".format(rows[0]), "x1"),
                              ("valor", "1:{},0.5,1.0;{}:{},0.5,2.0".format(raro, ";".join(["NaN"] * (slots - 1)),
                                                                           raro), raro)):
        bad = os.path.join(folder, "inventado_atd_{}.txt".format(label))
        with open(bad, "w", newline="\n") as handle:
            handle.write(row + "\n")
        messages = []
        for load in (io_atd.load_ball, io_atd.load_players):
            try:
                load(bad, n, pitch)
                messages.append("")
            except ValueError as error:
                messages.append(str(error))
        check("un {} que no es un número da error en los dos lectores, sin enseñar el valor".format(label),
              all(message and shown not in message for message in messages), " | ".join(messages))


def same_tracking(one, other):
    """Mismo balón y mismos jugadores, NaN incluidos."""
    return all(bool(np.array_equal(a, b, equal_nan=True))
               for a, b in ((one.bx, other.bx), (one.by, other.by), (one.px, other.px), (one.py, other.py)))


def check_summary():
    print("Resumen de la entrega: rachas cortas")
    # Posesiones de 5, 30, 20, 11, 12, 25 y 40; juego (entre paradas) de 35, 20, 48 y 40; paradas de 10, 35
    # y 25. Las de 12 y 25 justos no cuentan como «de menos de».
    window = np.array([H] * 5 + [A] * 30 + [D] * 10 + [H] * 20 + [D] * 35 + [A] * 11 + [H] * 12 + [A] * 25
                      + [D] * 25 + [H] * 40, dtype=np.int8)
    found = pipeline.short_runs(window)
    wanted = {("posesiones", 12): 2, ("posesiones", 25): 4, ("juego", 12): 0, ("juego", 25): 1,
              ("paradas", 12): 1, ("paradas", 25): 1}
    check("cuenta las posesiones, el juego entre paradas y las paradas de menos de 12 y de 25 frames",
          found == wanted, "{}".format(found))
    edge = pipeline.short_runs(np.array([A] * 7 + [H] * 60 + [D] * 3, dtype=np.int8))
    check("la primera y la última racha cuentan con lo que queda dentro del tramo",
          edge[("posesiones", 12)] == 1 and edge[("paradas", 12)] == 1 and edge[("juego", 12)] == 0)
    lines = pipeline.summary(np.concatenate(([X] * 4, window, [X] * 3)).astype(np.int8), [(4, 4 + len(window))])
    check("el resumen trae una línea de rachas cortas por tramo",
          sum(line.startswith("tramo 1, rachas cortas") for line in lines) == 1)


def check_main(codes, folder):
    print("Comando de la entrega (pipeline.main) con pipeline.build cambiado por uno inventado")
    blocks = tracking.evaluated_blocks(GAME)
    counts = dict.fromkeys(COUNT_KEYS, 0)
    counts.update(lineas=len(codes), validas=len(codes), frames_evaluados_sin_linea=0)

    def refuse(*args, **kwargs):
        raise AssertionError("pipeline.main ha intentado buscar los ficheros del partido")

    asked = {}

    def fake_build(**kwargs):
        asked.clear()
        asked.update(kwargs)
        return codes, blocks, {"atd": counts, "conflictos": conflicts_now[0]}

    conflicts_now = [0]

    def run_main(name, conflicts, extra_args=()):
        # build cambiado por uno inventado, y games.require y games.asset_paths por uno que da error: aunque
        # alguien añada a main una lectura del partido, esta prueba no la haría.
        real = pipeline.build, sys.argv, games.require, games.asset_paths
        conflicts_now[0] = conflicts
        pipeline.build = fake_build
        sys.argv = ["pipeline", "--out", folder, "--name", name] + list(extra_args)
        games.require = games.asset_paths = refuse
        shown, status = io.StringIO(), 0
        try:
            with contextlib.redirect_stdout(shown):
                pipeline.main()
        except SystemExit as stop:
            status = stop.code
        finally:
            pipeline.build, sys.argv, games.require, games.asset_paths = real
        return status, shown.getvalue()

    path = os.path.join(folder, "buena.csv")
    status, shown = run_main("buena", 0)
    reason = pm.validate_submission(pm.read_label_csv(path), len(codes)) if os.path.exists(path) else "no está"
    check("sin conflictos: escribe el CSV, que pasa la validación oficial", status == 0 and reason is None,
          reason or "")
    check("e imprime las versiones de Python y numpy, el código, las líneas del ATD, el resumen y el sha256",
          "python " in shown and "numpy " + np.__version__ in shown and "código: " in shown
          and "líneas del ATD: " in shown and "tramo 2, rachas cortas" in shown
          and "sha256: " + pipeline.sha256(path) in shown)
    check("sin --pieza ni --capa, build recibe las piezas de la entrega y lo dice",
          not asked.get("pieces") and not asked.get("layers") and "piezas: las de la entrega (PIECES)" in shown)

    # Entregas de prueba: otra pieza o una capa más, sin tocar PIECES.
    trial = ["--pieza", "candidates=aprendida.evidence_b9", "--capa", "dead_state.evidence"]
    status, shown = run_main(pipeline.DEFAULT_NAME, 0, trial)
    check("una entrega de prueba con el nombre de la entrega: no se escribe",
          status == 2 and not os.path.exists(os.path.join(folder, pipeline.DEFAULT_NAME + ".csv")))
    status, shown = run_main("prueba_b9", 0, trial)
    check("con su propio nombre: build recibe la pieza cambiada y la capa, y la salida lo dice",
          status == 0 and asked.get("pieces") == {"candidates": aprendida.evidence_b9}
          and asked.get("layers") == [dead_state.evidence]
          and "candidates cambiada por aprendida.evidence_b9" in shown
          and "capa añadida dead_state.evidence" in shown
          and os.path.exists(os.path.join(folder, "prueba_b9.csv")))
    check("una pieza o una función que no existen dan error claro",
          raises(ValueError, lambda: pipeline.overrides(["decoder=temporal.decode"]))
          and raises(ValueError, lambda: pipeline.overrides(["candidates=aprendida.no_existe"]))
          and raises(ValueError, lambda: pipeline.overrides((), ["os.remove"]))
          and pipeline.PIECES["candidates"] == "aprendida.evidence_b5")
    real_root = pipeline.ROOT
    pipeline.ROOT = folder  # una carpeta que no es un repositorio de git
    try:
        outside = pipeline.code_version()
    finally:
        pipeline.ROOT = real_root
    inside = pipeline.code_version()
    check("el código: el commit en el repo, y «sin git» fuera de un repositorio",
          outside == "código: sin git" and (inside.startswith("código: commit ") or inside == "código: sin git"),
          "{} | {}".format(inside, outside))
    status, shown = run_main("con_conflictos", 3)
    check("con conflictos: sale con error y no escribe nada", status == 1 and not any(
        name.startswith("con_conflictos") for name in os.listdir(folder)))
    other = codes.copy()
    other[codes == H], other[codes == A] = A, H  # un CSV de antes con otras etiquetas
    pipeline.write_submission(path, other)
    before = pipeline.sha256(path)
    status, shown = run_main("buena", 3)
    check("con conflictos y un CSV de antes con ese nombre: no lo toca y avisa",
          status == 1 and pipeline.sha256(path) == before and "Ojo" in shown)
    check("no deja ficheros a medias", not any(".a_medias" in name for name in os.listdir(folder)))

    def cut(*args, **kwargs):
        raise OSError("corte inventado al renombrar")

    real_replace = pipeline.os.replace
    pipeline.os.replace = cut
    try:
        stopped = raises(OSError, lambda: pipeline.write_submission(path, codes))
    finally:
        pipeline.os.replace = real_replace
    check("si la escritura se corta antes de renombrar, el CSV de antes con ese nombre sigue igual",
          stopped and pipeline.sha256(path) == before)
    for name in os.listdir(folder):
        if ".a_medias" in name:
            os.remove(os.path.join(folder, name))


def main():
    rng = np.random.default_rng(SEED)
    info = games.GAMES[GAME]
    folder = safe_tmp()
    try:
        trk = synthetic_tracking(info["n_video_frames"], tracking.evaluated_blocks(GAME), info["pitch"], rng)
        with no_files():
            check_interface(trk)
            codes = check_pipeline(trk)
            check_decoder(rng)
            check_guards(rng)
            check_pieces(np.random.default_rng(SEED + 1))  # su propio azar: no cambia el de las demás
        check_csv(codes, folder)
        check_summary()
        check_main(codes, folder)
        check_reader(folder, rng)
        check_build_requires(folder)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    print()
    if failures:
        print("FALLAN {} comprobaciones".format(len(failures)))
        sys.exit(1)
    print("TODO BIEN")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
