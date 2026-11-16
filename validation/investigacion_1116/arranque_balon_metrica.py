"""Sondeo S6: ¿fecha el arranque del balón el final de una parada? Metrica sample-data, 3 partidos.

    python validation/investigacion_1116/arranque_balon_metrica.py

Datos abiertos de otros partidos (https://github.com/metrica-sports/sample-data): lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. La regla de lectura está en BITACORA.md (S6), escrita
antes. El saque es el paso de `D` a juego de las etiquetas de `validation/metrica/lector.py`, que sale del
frame de cada evento `SET PIECE`.
"""

import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "metrica"))
import lector as lm  # noqa: E402

H, A, D, X = lm.H, lm.A, lm.D, lm.X
FPS = lm.FPS
VISTO = 0.8  # fracción de frames con balón en el segundo anterior al saque
QUIETO = 1.0  # m/s: mediana de la velocidad por debajo de esto es «quieto»
ARRANQUE = 3.0  # m/s
BUSCA = 75  # frames a cada lado del saque
SUAVIZADO = 25


def velocidad(bx, by):
    v = np.full(len(bx), np.nan)
    v[1:-1] = np.hypot(bx[2:] - bx[:-2], by[2:] - by[:-2]) * FPS / 2.0
    return v


def arranque(v, r, suavizado):
    """Frame estimado del golpeo cerca de `r`, o None. Primer frame en [r − BUSCA, r + BUSCA] con velocidad
    de ARRANQUE o más tras un segundo quieto (mediana por debajo de QUIETO en los frames t−30…t−5). Con el
    balón suavizado, la velocidad sube en rampa durante el ancho de la media: se corrige con la velocidad que
    alcanza un ancho después."""
    n = len(v)
    for t in range(max(31, r - BUSCA), min(n - suavizado - 1, r + BUSCA)):
        if not v[t] >= ARRANQUE:
            continue
        antes = v[t - 30:t - 4]
        antes = antes[np.isfinite(antes)]
        if len(antes) < 13 or np.median(antes) >= QUIETO:
            continue
        if suavizado <= 1:
            return t
        tope = v[t:t + suavizado + 1]
        tope = tope[np.isfinite(tope)]
        if not len(tope):
            return None
        pico = max(float(np.max(tope)), ARRANQUE)
        mitad = suavizado // 2
        return int(round(t + mitad - 2 * mitad * ARRANQUE / pico))
    return None


def main():
    ids = lm.partidos()
    if not ids:
        sys.exit("No hay partidos de Metrica bajados")
    for nombre, condicion, ancho in (("tal cual", "tal cual", 1), ("suavizado 25", "suavizado 25", SUAVIZADO)):
        n_saques = vistos = quietos = hallados = 0
        errores = []
        d_frames = d_con_balon = 0
        for id_ in ids:
            crudo = lm.leer(id_)
            trk, gt = lm.tracking_de(crudo, condicion, id_)
            bx, by = np.asarray(trk.bx, dtype=float), np.asarray(trk.by, dtype=float)
            v = velocidad(bx, by)
            hay = np.isfinite(bx) & np.isfinite(by)
            for a, b in trk.blocks:
                g = gt[a:b]
                d_frames += int(np.sum(g == D))
                d_con_balon += int(np.sum((g == D) & hay[a:b]))
                saques = np.flatnonzero((g[1:] != D) & (g[1:] != X) & (g[:-1] == D)) + 1
                for s in saques:
                    r = a + int(s)
                    if r - 30 < a or r + BUSCA + SUAVIZADO >= b:
                        continue
                    n_saques += 1
                    if hay[r - FPS:r].mean() < VISTO:
                        continue
                    vistos += 1
                    previa = v[r - FPS:r]
                    previa = previa[np.isfinite(previa)]
                    if len(previa) and np.median(previa) < QUIETO:
                        quietos += 1
                    t0 = arranque(v, r, ancho)
                    if t0 is not None:
                        hallados += 1
                        errores.append(t0 - r)
        e = np.array(errores, dtype=float)
        print("### Balón {}\n".format(nombre))
        print("- frames `D` con balón: {:.1f} %".format(100.0 * d_con_balon / max(d_frames, 1)))
        print("- saques: {} · con el balón visto en el segundo anterior: {} ({:.0f} %) · de esos, quieto: {} ({:.0f} %)".format(
            n_saques, vistos, 100.0 * vistos / max(n_saques, 1), quietos, 100.0 * quietos / max(vistos, 1)))
        if len(e):
            print("- arranque hallado en {} de los {} con balón ({:.0f} %); error en frames (arranque − saque): "
                  "p10 {:+.0f}, p25 {:+.0f}, mediana {:+.0f}, p75 {:+.0f}, p90 {:+.0f}".format(
                      hallados, vistos, 100.0 * hallados / max(vistos, 1), *np.percentile(e, [10, 25, 50, 75, 90])))
            print("- a ±12 frames del saque: {} ({:.0f} % de los que tienen balón; {:.0f} % de todos los saques) · "
                  "a ±25: {} ({:.0f} % y {:.0f} %)".format(
                      int(np.sum(np.abs(e) <= 12)), 100.0 * np.sum(np.abs(e) <= 12) / max(vistos, 1),
                      100.0 * np.sum(np.abs(e) <= 12) / max(n_saques, 1),
                      int(np.sum(np.abs(e) <= 25)), 100.0 * np.sum(np.abs(e) <= 25) / max(vistos, 1),
                      100.0 * np.sum(np.abs(e) <= 25) / max(n_saques, 1)))
        print()


if __name__ == "__main__":
    main()
