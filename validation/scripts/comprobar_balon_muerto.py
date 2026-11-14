"""Comprueba possession/dead_ball.py sin datos del partido: solo el código, la GT pública y un Smart Tagging
inventado, que se escribe en una carpeta temporal y se borra al terminar.

    python validation/scripts/comprobar_balon_muerto.py

Sale con código 1 si falla alguna comprobación. Claude puede ejecutarlo (validation/README.md).
"""

import builtins
import csv
import hashlib
import io
import os
import random
import shutil
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from possession import dead_ball, tracking  # noqa: E402
from starter.load_smart_tagging import KICKOFF_VIDEO_FRAMES  # noqa: E402

GT_PATH = os.path.join(ROOT, "evaluation", "gt", "BAR-ATH_possession_gt_public.csv")
FAQ_SECOND_HALF_DEAD_FRAMES = 2934  # FAQ.md: "Those 2,934 frames are graded and all of them are D"
ANCHOR_KEYS = {1: "kickoff", 2: "kickoff_2nd"}

failures = []


def check(name, ok, detail=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", name, "   " + detail if detail else ""))
    if not ok:
        failures.append(name)


def mask_without_opening_files(game):
    """La máscara y los ficheros que se intentaron abrir al calcularla."""
    opened = []
    real_open, real_io_open = builtins.open, io.open

    def spy(path, *args, **kwargs):
        opened.append(str(path))
        return real_open(path, *args, **kwargs)

    builtins.open = io.open = spy
    try:
        mask = dead_ball.dead_mask(game=game)
    finally:
        builtins.open, io.open = real_open, real_io_open
    return mask, opened


def smart_tagging_xml(folder, name, instances, shuffle_seed=None):
    """Un Smart Tagging inventado con `instances` = [(código, inicio_s, fin_s, Type o None)]. Devuelve la ruta."""
    rows = list(instances)
    if shuffle_seed is not None:
        random.Random(shuffle_seed).shuffle(rows)
    body = []
    for i, (code, start_s, end_s, kind) in enumerate(rows):
        labels = "<label><group>Team</group><text>N/A</text></label>"
        if kind:
            labels += "<label><group>Type</group><text>{}</text></label>".format(kind)
        body.append("<instance><ID>{}</ID><start>{}</start><end>{}</end><code>{}</code>{}</instance>".format(
            i, start_s, end_s, code, labels))
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("<file><ALL_INSTANCES>{}</ALL_INSTANCES></file>".format("".join(body)))
    return path


def check_goal_to_kickoff(game, folder):
    """La capa «de cada gol a su saque» con casos inventados, también los que anclarían juego vivo."""
    fps = games.GAMES[game]["fps"]
    n_frames = games.GAMES[game]["n_video_frames"]
    ko = "Kick Off (After Goal)"

    def spans(instances, seed=None):
        path = smart_tagging_xml(folder, "caso.xml", instances, seed)
        return dead_ball.goal_to_kickoff(dead_ball.smart_tagging_events(path, fps), fps)

    def at(seconds):
        return int(round(seconds * fps))

    check("gol con su saque: de fin del gol a inicio del saque",
          spans([("GOALS", 1000, 1010, None), ("SET PIECES", 1100, 1105, ko)]) == [(at(1010), at(1100))])
    check("códigos y tipos sin distinguir mayúsculas",
          spans([("goals", 1000, 1010, None), ("set pieces", 1100, 1105, "kick off (after goal)")])
          == [(at(1010), at(1100))])
    check("a 180 s justos del fin del gol entra; un frame más, no",
          len(spans([("GOALS", 100, 110, None), ("SET PIECES", 290, 295, ko)])) == 1
          and spans([("GOALS", 100, 110, None), ("SET PIECES", 290.04, 295, ko)]) == [])
    check("gol sin saque y otro gol con saque: solo ancla el segundo",
          spans([("GOALS", 100, 110, None), ("GOALS", 150, 160, None), ("SET PIECES", 200, 205, ko)])
          == [(at(160), at(200))])
    check("un reinicio entre el gol y el saque: no ancla",
          spans([("GOALS", 100, 110, None), ("SET PIECES", 150, 185, "Throw-in"), ("SET PIECES", 200, 205, ko)])
          == [])
    check("un gol que empieza entre otro gol y su saque: no ancla",
          spans([("GOALS", 100, 110, None), ("GOALS", 150, 215, None), ("SET PIECES", 200, 205, ko)]) == [])
    check("saque dentro de su ventana GOALS: no ancla ni se lleva el gol siguiente",
          spans([("GOALS", 100, 110, None), ("SET PIECES", 105, 110, ko),
                 ("GOALS", 300, 310, None), ("SET PIECES", 350, 355, ko)]) == [(at(310), at(350))])
    check("dos saques tras un gol: solo el primero",
          spans([("GOALS", 100, 110, None), ("SET PIECES", 150, 155, ko), ("SET PIECES", 200, 205, ko)])
          == [(at(110), at(150))])
    several = [("GOALS", 1000, 1010, None), ("SET PIECES", 1100, 1105, ko), ("GOALS", 2000, 2010, None),
               ("GOALS", 3000, 3010, None), ("SET PIECES", 3210, 3215, ko), ("SET PIECES", 4000, 4035, "Throw-in"),
               ("BUILD UP", 4100, 4140, None), ("GOALS", 6000, 6012.5, None), ("SET PIECES", 6080, 6085, ko)]
    expected = [(at(1010), at(1100)), (at(6012.5), at(6080))]
    check("varios goles: solo los que tienen su saque cerca y sin nada por medio", spans(several) == expected,
          str(spans(several)))
    check("no depende del orden del fichero", all(spans(several, seed) == expected for seed in range(10)))

    path = smart_tagging_xml(folder, "partido_inventado.xml", several)
    trk = tracking.Tracking(np.full(n_frames, np.nan), np.full(n_frames, np.nan), np.empty((n_frames, 0)),
                            np.empty((n_frames, 0)), np.empty(0, dtype=np.int8), games.GAMES[game]["pitch"],
                            tracking.evaluated_blocks(game), fps)
    pre = dead_ball.pre_kickoff(game)
    anchored = pre.copy()
    for start, stop in expected:
        anchored[start:stop] = True
    mask = dead_ball.dead_mask({"smart_tagging": path}, game)
    score, allowed = dead_ball.evidence(trk, {"smart_tagging": path}, game)
    check("con rutas, la máscara es el tramo antes del saque más los de gol a saque",
          bool(np.array_equal(mask, anchored)), "{} frames".format(int(mask.sum())))
    check("evidence: en lo anclado solo D, fuera todo permitido, y no puntúa",
          bool(np.array_equal(~allowed[:, tracking.H], anchored))
          and bool(np.array_equal(~allowed[:, tracking.A], anchored))
          and bool(allowed[:, tracking.D].all()) and not score.any())
    _, allowed_none = dead_ball.evidence(trk, None, game)
    check("evidence sin rutas: solo el tramo antes del saque",
          bool(np.array_equal(~allowed_none[:, tracking.H], pre)))


def main():
    game = games.GAME
    n_frames = games.GAMES[game]["n_video_frames"]
    blocks = games.half_video_blocks(game)

    print("1. Interfaz común")
    mask, opened = mask_without_opening_files(game)
    check("es un np.ndarray", isinstance(mask, np.ndarray))
    check("199.319 posiciones", mask.shape == (n_frames,), str(mask.shape))
    check("booleana", mask.dtype == bool, str(mask.dtype))
    check("no abre ningún fichero", not opened, "{} abiertos".format(len(opened)))

    print("\n2. Dónde marca D")
    graded = np.zeros(n_frames, dtype=bool)
    for _, first, last in blocks:
        graded[first:last + 1] = True
    check("nada fuera de los frames evaluados", not (mask & ~graded).any(),
          "{} frames".format(int((mask & ~graded).sum())))
    for half, first, last in blocks:
        kickoff = KICKOFF_VIDEO_FRAMES[dead_ball.HALF_NAMES[half]]
        dead = np.flatnonzero(mask[first:last + 1]) + first
        expected = max(0, kickoff - first)
        check("parte {}: {} frames D".format(half, expected), dead.size == expected,
              "tiene {}".format(dead.size))
        if dead.size:
            contiguous = dead[0] == first and dead[-1] == kickoff - 1 and dead.size == dead[-1] - dead[0] + 1
            check("parte {}: un solo tramo, del primer frame evaluado al anterior al saque".format(half),
                  contiguous)
    second_first = blocks[1][1]
    second_dead = int(mask[second_first:blocks[1][2] + 1].sum())
    check("2ª parte: los {} frames que da FAQ.md".format(FAQ_SECOND_HALF_DEAD_FRAMES),
          second_dead == FAQ_SECOND_HALF_DEAD_FRAMES, "tiene {}".format(second_dead))

    # La GT pública solo cubre el principio de la 1ª parte y esta versión solo marca la 2ª, así que
    # "ninguna contradicción" sale casi por construcción: no es una validación del detector. La que
    # aporta es la del primer frame evaluado, que confirma que la 1ª parte no tiene tramo previo.
    print("\n3. Frente a la GT pública (solo para comprobar que no se contradicen; no valida el detector)")
    with open(GT_PATH, newline="") as handle:
        rows = list(csv.reader(handle))[1:]
    labels = np.array([label for _, label in rows])
    check("la GT pública tiene 199.319 filas", labels.size == n_frames, str(labels.size))
    scored = labels != "X"
    contradictions = int((mask & scored & (labels != "D")).sum())
    check("ningún D nuestro donde la GT pública dice H o A", contradictions == 0,
          "{} frames".format(contradictions))
    first_graded = blocks[0][1]
    check("la GT pública no tiene D en el primer frame evaluado (no hay tramo antes del saque)",
          labels[first_graded] != "D")
    print("  (informativo) D de la GT pública que cubre esta versión: {} de {}".format(
        int((mask & (labels == "D")).sum()), int((labels == "D").sum())))

    print("\n4. Determinismo")
    again, _ = mask_without_opening_files(game)
    check("dos llamadas dan la misma máscara byte a byte", mask.tobytes() == again.tobytes())
    print("  sha256 {}".format(hashlib.sha256(mask.tobytes()).hexdigest()[:16]))

    print("\n5. Las dos fuentes de los frames de saque")
    for half, _, _ in blocks:
        published = KICKOFF_VIDEO_FRAMES[dead_ball.HALF_NAMES[half]]
        anchor = games.anchor_video_frame(games.GAMES[game][ANCHOR_KEYS[half]])
        check("parte {}: FAQ.md y el ancla de games.py difieren en 1 frame como mucho".format(half),
              abs(published - anchor) <= 1, "diferencia {:+d}".format(anchor - published))

    print("\n6. Otro partido")
    try:
        dead_ball.dead_mask(game="OTRO-PARTIDO")
        check("con otro partido da un error en vez de una máscara", False)
    except ValueError:
        check("con otro partido da un error en vez de una máscara", True)

    print("\n7. De cada gol a su saque, con un Smart Tagging inventado")
    folder = tempfile.mkdtemp(prefix="comprobar_balon_muerto_")
    try:
        check_goal_to_kickoff(game, folder)
    finally:
        shutil.rmtree(folder, ignore_errors=True)

    print("\n{}".format("TODO BIEN" if not failures else "FALLAN {}: {}".format(
        len(failures), "; ".join(failures))))
    return 1 if failures else 0


if __name__ == "__main__":
    # En Windows, al redirigir la salida a un fichero se usaría cp1252 en vez de UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
