"""Prueba possession/io.py con un ATD SINTÉTICO (no es el del partido): alineación, NaN, escala, tiempo."""
import os
import shutil
import sys
import tempfile
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from possession.io import load_ball, load_players  # noqa: E402


def main():

    PITCH = (105.3, 68.0)
    rng = np.random.RandomState(0)

    # 1) fichero pequeño con casos límite
    tmp = tempfile.mkdtemp()
    small = os.path.join(tmp, "atd_small.txt")
    with open(small, "w") as f:
        # frame 1 -> índice 0: balón en (0.5, 0.5, 3.2), 3 slots
        f.write("1:0.1,0.2,1.0;NaN,NaN,NaN;0.9,0.8,2.0:0.5,0.5,3.2\n")
        # frame 2: balón ausente como NaN,NaN,NaN
        f.write("2:0.1,0.2,1.0;0.3,0.3,0.5;0.9,0.8,2.0:NaN,NaN,NaN\n")
        # frame 3: balón ausente como un solo token NaN (lo que el baseline tolera con ball[0]=='N')
        f.write("3:0.1,0.2,1.0;0.3,0.3,0.5;0.9,0.8,2.0:NaN\n")
        # frame 4: balón con solo x,y (sin velocidad)
        f.write("4:0.1,0.2,1.0;0.3,0.3,0.5;0.9,0.8,2.0:0.25,0.75\n")
        # línea basura
        f.write("\n")
        # frame fuera de rango (ignorado)
        f.write("99:0.1,0.2,1.0;0.3,0.3,0.5;0.9,0.8,2.0:0.5,0.5,1.0\n")
    try:
        x, y, s = load_ball(small, 5, PITCH)
        print("load_ball casos límite: OK")
        print("  frame_id 1 -> índice 0: x={:.2f} m (esperado 52.65) y={:.2f} m (esperado 34.00) s={}".format(x[0], y[0], s[0]))
        print("  frame_id 2 (NaN,NaN,NaN): x nan? {}".format(np.isnan(x[1])))
        print("  frame_id 3 (solo 'NaN'): x nan? {}".format(np.isnan(x[2])))
        print("  frame_id 4 (sin velocidad): x={:.2f} s nan? {}".format(x[3], np.isnan(s[3])))
        print("  índice 4 (sin línea): nan? {}".format(np.isnan(x[4])))
    except Exception as e:
        print("load_ball casos límite: FALLA ->", type(e).__name__, e)
    try:
        px, py = load_players(small, 5, PITCH)
        print("load_players: forma {}  slot NaN en frame 1 -> nan? {}  slot 2 x={:.2f} m".format(px.shape, np.isnan(px[0, 1]), px[0, 2]))
    except Exception as e:
        print("load_players casos límite: FALLA ->", type(e).__name__, e)

    # 2) número de slots variable entre líneas
    var = os.path.join(tmp, "atd_var.txt")
    with open(var, "w") as f:
        f.write("1:0.1,0.2,1.0;0.3,0.3,0.5:0.5,0.5,1.0\n")
        f.write("2:0.1,0.2,1.0;0.3,0.3,0.5;0.9,0.8,2.0:0.5,0.5,1.0\n")
    try:
        load_players(var, 2, PITCH); print("slots variables: no avisa")
    except ValueError as e:
        print("slots variables: ValueError ->", e)

    # 3) tamaño real: 199319 líneas x 46 slots, 41 % sin balón, 55 % de slots vacíos
    N, S = 199319, 46
    big = os.path.join(tmp, "atd_big.txt")
    t0 = time.time()
    with open(big, "w") as f:
        for i in range(1, N + 1):
            groups = []
            for sl in range(S):
                if rng.rand() < 0.55:
                    groups.append("NaN,NaN,NaN")
                else:
                    groups.append("{:.4f},{:.4f},{:.2f}".format(rng.rand(), rng.rand(), rng.rand() * 8))
            ball = "NaN,NaN,NaN" if rng.rand() < 0.41 else "{:.4f},{:.4f},{:.2f}".format(rng.rand(), rng.rand(), rng.rand() * 20)
            f.write("{}:{}:{}\n".format(i, ";".join(groups), ball))
    print("\nfichero sintético grande escrito en {:.0f} s ({:.0f} MB)".format(time.time() - t0, os.path.getsize(big) / 1e6))
    t0 = time.time(); x, y, s = load_ball(big, N, PITCH); tb = time.time() - t0
    print("load_ball:    {:.1f} s   balón presente {:.1f} %".format(tb, 100 * np.mean(~np.isnan(x))))
    t0 = time.time(); px, py = load_players(big, N, PITCH); tp = time.time() - t0
    print("load_players: {:.1f} s   forma {}  slots presentes por frame {:.1f}   memoria {:.0f} MB".format(
        tp, px.shape, np.mean(np.sum(~np.isnan(px), axis=1)), (px.nbytes + py.nbytes) / 1e6))
    # alternativa vectorizada con numpy para comparar
    t0 = time.time()
    with open(big) as f:
        raw = f.read()
    # sustituir separadores por comas y leer todo como una matriz
    flat = np.fromstring(raw.replace(":", ",").replace(";", ",").replace("\n", ","), sep=",")
    mat = flat.reshape(N, 1 + 3 * S + 3)
    tv = time.time() - t0
    print("lectura vectorizada (fromstring): {:.1f} s   coincide con load_ball: {}".format(
        tv, np.allclose(np.nan_to_num(mat[:, -3] * PITCH[0], nan=-1), np.nan_to_num(x, nan=-1))))
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
