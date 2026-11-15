"""Prueba del lector de Metrica con etiquetas y un partido inventados. No lee ningún partido real.

    python validation/metrica/prueba_lector.py
"""

import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "harness"))
import lector as lc  # noqa: E402

H, A, D, X = lc.H, lc.A, lc.D, lc.X
FALLOS = []


def comprobar(condicion, texto):
    print("{}  {}".format("ok   " if condicion else "FALLA", texto))
    if not condicion:
        FALLOS.append(texto)


def codigos(n, eventos):
    return lc.etiquetar(n, eventos)


def test_etiquetas():
    # Saque local en el 10, balón fuera en el 20: vivo solo en medio, y es del local.
    gt = codigos(30, [(10, "SET PIECE", "KICK OFF", H), (20, "BALL OUT", "", H)])
    comprobar(np.all(gt[:10] == D) and np.all(gt[10:20] == H) and np.all(gt[20:] == D),
              "el vivo va del saque a la salida, sin incluir la salida")

    # Un pase del visitante cambia el equipo; un duelo no.
    gt = codigos(20, [(0, "SET PIECE", "KICK OFF", H), (5, "PASS", "", A), (8, "CHALLENGE", "TACKLE-WON", H),
                      (12, "BALL OUT", "", A)])
    comprobar(np.all(gt[:5] == H) and np.all(gt[5:12] == A) and np.all(gt[12:] == D),
              "el pase cambia el equipo y el duelo no")

    # Falta y saque de falta. El gol para el juego.
    gt = codigos(25, [(0, "SET PIECE", "KICK OFF", H), (6, "FAULT RECEIVED", "", A),
                      (10, "SET PIECE", "FREE KICK", A), (15, "SHOT", "ON TARGET-GOAL", A)])
    comprobar(np.all(gt[:6] == H) and np.all(gt[6:10] == D) and np.all(gt[10:15] == A) and np.all(gt[15:] == D),
              "la falta y el gol paran, y el saque reanuda")

    # Fuera de juego y fin de parte. Una conducción sí es control.
    gt = codigos(16, [(0, "SET PIECE", "THROW IN", A), (4, "CARRY", "", H), (9, "BALL LOST", "OFFSIDE", H),
                      (12, "BALL LOST", "END HALF", A)])
    comprobar(np.all(gt[:4] == A) and np.all(gt[4:9] == H) and np.all(gt[9:] == D),
              "la conducción cambia el equipo; el fuera de juego y el fin de parte paran")

    # Vivo antes de cualquier evento de control: X. No pasa con un saque, que es control.
    gt = codigos(5, [])
    comprobar(np.all(gt == D), "sin eventos, todo es balón muerto")


def partido_inventado():
    """Dos partes de 8 frames, un hueco de balón en la primera, 2 jugadores por equipo."""
    n = 8
    bx = np.array([0.0, 1, 2, np.nan, 4, 5, 6, 7], dtype=float)
    by = bx + 10
    px = np.zeros((n, 4), dtype=np.float32)
    py = np.zeros((n, 4), dtype=np.float32)
    px[:, 0] = 1
    gt = np.array([D, H, H, H, A, A, D, D], dtype=np.int8)
    crudo = {
        "bx": np.concatenate([bx, bx]), "by": np.concatenate([by, by + 1]),
        "px": np.concatenate([px, px]), "py": np.concatenate([py, py]),
        "gt": np.concatenate([gt, gt[::-1]]),
        "team": np.array([H, H, A, A], dtype=np.int8),
        "pitch": np.array([100.0, 60.0]),
        "largos": np.array([n, n]),
    }
    return crudo


def test_tracking():
    crudo = partido_inventado()
    trk, gt = lc.tracking_de(crudo, "tal cual", id_=7)
    comprobar(trk.blocks == ((0, 8), (8 + lc.HUECO, 16 + lc.HUECO)), "las dos partes quedan separadas por el hueco")
    comprobar(np.all(gt[8:8 + lc.HUECO] == X) and np.all(np.isnan(trk.bx[8:8 + lc.HUECO])),
              "el descanso no tiene etiqueta ni balón")
    comprobar(np.all(gt[:8] == crudo["gt"][:8]) and np.all(gt[8 + lc.HUECO:] == crudo["gt"][8:]),
              "las etiquetas de cada parte no se mezclan")
    comprobar(np.isnan(trk.bx[3]) and np.isfinite(trk.bx[2]) and np.isfinite(trk.bx[4]),
              "tal cual conserva el hueco del balón")

    trk_s, _ = lc.tracking_de(crudo, "suavizado 25", id_=7)
    comprobar(np.isnan(trk_s.bx[3]), "el suavizado no rellena un frame sin balón")
    comprobar(np.isfinite(trk_s.bx[2]) and abs(trk_s.bx[2] - 2) > 1e-6, "el suavizado mueve un frame con balón")
    comprobar(int(np.sum(trk.team == H)) == 2 and int(np.sum(trk.team == A)) == 2,
              "el barajado conserva cuántos slots tiene cada equipo")
    comprobar(trk.pitch == (100.0, 60.0) and trk.fps == 25, "el campo y los fps se conservan")


if __name__ == "__main__":
    test_etiquetas()
    test_tracking()
    if FALLOS:
        sys.exit("FALLA: {}".format("; ".join(FALLOS)))
    print("TODO BIEN")
