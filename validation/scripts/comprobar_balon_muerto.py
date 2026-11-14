"""Comprueba possession/dead_ball.py sin datos del partido: solo el código y la GT pública.

    python validation/scripts/comprobar_balon_muerto.py

Sale con código 1 si falla alguna comprobación. Claude puede ejecutarlo (validation/README.md).
"""

import builtins
import csv
import hashlib
import io
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from possession import dead_ball  # noqa: E402
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

    print("\n{}".format("TODO BIEN" if not failures else "FALLAN {}: {}".format(
        len(failures), "; ".join(failures))))
    return 1 if failures else 0


if __name__ == "__main__":
    # En Windows, al redirigir la salida a un fichero se usaría cp1252 en vez de UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
