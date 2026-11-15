"""Prueba el esqueleto del pipeline (possession/) sin datos del partido: todo el tracking es inventado.

    python validation/scripts/prueba_pipeline.py

Comprueba la interfaz de las piezas, los tramos evaluados, el tramo antes del saque, el decodificador
(contra la búsqueda exhaustiva), los errores que no pueden pasar en silencio, el determinismo, el CSV y
el lector del ATD con un fichero sintético.

Nunca llama a `pipeline.main()`, que lee el partido. A `pipeline.build()`, que también lo lee, solo lo
llama con `games.require` cambiado por uno que corta antes de leer nada, con una carpeta temporal vacía
como datos y sin poder abrir ficheros. Además, mientras ejecuta las piezas, abrir cualquier fichero es un
error (`no_files`).

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
