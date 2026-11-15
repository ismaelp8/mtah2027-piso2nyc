"""Sondeo S3: ¿dice algo el encuadre de la cámara que no diga ya el centroide de los jugadores?

    python validation/investigacion_1116/camara_skillcorner.py

Datos abiertos de otros partidos (4 de la mitad de entrenamiento de SkillCorner, licencia MIT): lo puede
ejecutar cualquiera, Claude incluido. Solo imprime agregados. La regla de lectura está en BITACORA.md (S3),
escrita antes de ejecutar. Es una cámara de retransmisión, no la táctica del reto: puede exagerar.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "skillcorner"))
import lector as lc  # noqa: E402

PARTIDOS = lc.ENTRENAMIENTO[:4]
DESFASES = range(-20, 21)  # muestras a 10 fps


def leer(id_):
    """Por frame a 10 fps: centro del encuadre, balón detectado, centroide de los jugadores detectados y si
    el frame cae en una fase de juego."""
    carpeta = lc.carpeta() / str(id_)
    filas = []
    with open(carpeta / "{}_tracking_extrapolated.jsonl".format(id_), encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                filas.append(json.loads(linea))
    filas.sort(key=lambda r: r["frame"])
    n = filas[-1]["frame"] + 1
    out = {k: np.full(n, np.nan) for k in ("cx", "cy", "bx", "by", "jx", "jy")}
    for r in filas:
        t = r["frame"]
        c = r.get("image_corners_projection") or {}
        xs = [c.get(k) for k in ("x_top_left", "x_bottom_left", "x_bottom_right", "x_top_right")]
        ys = [c.get(k) for k in ("y_top_left", "y_bottom_left", "y_bottom_right", "y_top_right")]
        if all(v is not None for v in xs + ys):
            out["cx"][t], out["cy"][t] = float(np.mean(xs)), float(np.mean(ys))
        b = r.get("ball_data") or {}
        if b.get("is_detected") and b.get("x") is not None and b.get("y") is not None:
            out["bx"][t], out["by"][t] = b["x"], b["y"]
        det = [(p["x"], p["y"]) for p in (r.get("player_data") or [])
               if p.get("is_detected") and p.get("x") is not None and p.get("y") is not None]
        if len(det) >= 4:
            out["jx"][t], out["jy"][t] = float(np.mean([d[0] for d in det])), float(np.mean([d[1] for d in det]))
    fases = np.zeros(n, bool)
    tabla = pd.read_csv(carpeta / "{}_phases_of_play.csv".format(id_))
    for a, b in zip(tabla["frame_start"].astype(int), tabla["frame_end"].astype(int)):
        fases[max(a, 0):min(b + 1, n)] = True
    out["juego"] = fases
    return out


def recta(X, y):
    A = np.column_stack([X, np.ones(len(X))])
    return np.linalg.lstsq(A, y, rcond=None)[0]


def rmse(X, y, w):
    A = np.column_stack([X, np.ones(len(X))])
    return float(np.sqrt(np.mean((A @ w - y) ** 2)))


def main():
    lc.exigir_solo_entrenamiento(PARTIDOS)
    datos = [leer(i) for i in PARTIDOS]
    validos = []
    for d in datos:
        ok = d["juego"] & np.isfinite(d["cx"]) & np.isfinite(d["bx"]) & np.isfinite(d["jx"])
        validos.append(ok)
    print("partidos: {} · frames de juego con encuadre, balón detectado y 4 jugadores detectados o más: {}".format(
        len(PARTIDOS), ", ".join(str(int(v.sum())) for v in validos)))
    print("frames de juego con encuadre: {:.1f} % · de ellos con el balón detectado: {:.1f} %".format(
        100.0 * np.mean(np.concatenate([np.isfinite(d["cx"][d["juego"]]) for d in datos])),
        100.0 * np.mean(np.concatenate([np.isfinite(d["bx"][d["juego"] & np.isfinite(d["cx"])]) for d in datos]))))
    print()
    print("| eje | entrena en | mide en | solo balón medio | (a) centroide | (b) encuadre | (c) los dos | (c) frente a (a) |")
    print("|---|---|---|---|---|---|---|---|")
    mitades = ((0, 1), (2, 3))
    for eje, b, j, c in (("x", "bx", "jx", "cx"), ("y", "by", "jy", "cy")):
        for ent, med in (mitades, mitades[::-1]):
            def junta(grupo, clave):
                return np.concatenate([datos[i][clave][validos[i]] for i in grupo])
            yb_e, yb_m = junta(ent, b), junta(med, b)
            filas = []
            for columnas in ((j,), (c,), (j, c)):
                Xe = np.column_stack([junta(ent, k) for k in columnas])
                Xm = np.column_stack([junta(med, k) for k in columnas])
                filas.append(rmse(Xm, yb_m, recta(Xe, yb_e)))
            base = float(np.sqrt(np.mean((yb_m - yb_e.mean()) ** 2)))
            print("| {} | {} | {} | {:.2f} m | {:.2f} m | {:.2f} m | {:.2f} m | {:+.0f} % |".format(
                eje, "1.º y 2.º" if ent == mitades[0] else "3.º y 4.º",
                "3.º y 4.º" if ent == mitades[0] else "1.º y 2.º", base, filas[0], filas[1], filas[2],
                100.0 * (filas[2] / filas[0] - 1.0)))
    # desfase entre la velocidad del encuadre y la del balón
    corr = {}
    for k in DESFASES:
        xs, ys = [], []
        for d, ok in zip(datos, validos):
            vb = d["bx"][2:] - d["bx"][:-2]
            vc = d["cx"][2:] - d["cx"][:-2]
            bien = ok[1:-1] & np.isfinite(vb) & np.isfinite(vc)
            idx = np.flatnonzero(bien)
            idx = idx[(idx + k >= 0) & (idx + k < len(vc))]
            idx = idx[np.isfinite(vc[idx + k])]
            xs.append(vb[idx])
            ys.append(vc[idx + k])
        corr[k] = float(np.corrcoef(np.concatenate(xs), np.concatenate(ys))[0, 1])
    mejor = max(corr, key=lambda k: corr[k])
    print("\nCorrelación entre la velocidad en x del balón y la del centro del encuadre: {:.2f} sin desfase; "
          "máxima {:.2f} con el encuadre {} muestras de 0,1 s {} (positivo: la cámara va detrás del balón).".format(
              corr[0], corr[mejor], abs(mejor), "después" if mejor > 0 else "antes" if mejor < 0 else "a la vez"))


if __name__ == "__main__":
    main()
