"""Toques del balón con el detector del experimento 0, para cualquier trayectoria del balón, y su «suelo de ruido».

Es el mismo código para las tres cosas que se comparan en la puerta 1b de `validation/balon_video/BITACORA.md`: el
balón del detector del vídeo y el del ATD en el partido (lo ejecuta una persona), y el balón de la DFL, limpio o con
ruido, para calibrar (datos abiertos). Así las cifras son comparables.

- **Toque:** un máximo local del cambio de velocidad del balón de 3 m/s o más (`medidas_cambios.toques`, el del
  experimento 0, sin cambiar nada) con un jugador a 1,5 m o menos. Se busca por tramos de balón visible de 10 frames o
  más, como el experimento 2 (`instrumento.toques_por_tramos`): en los bordes de un hueco no se inventa nada.
- **Suelo de ruido:** los mismos máximos locales sin ningún jugador a 3 m o menos. Un toque de verdad necesita a
  alguien cerca; si el temblor de la posición fabrica cambios de velocidad, salen sobre todo aquí.

Funciones puras de numpy. Devuelven recuentos.
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
import medidas_cambios as mc  # noqa: E402

UMBRAL = 3.0  # m/s: cambio de velocidad mínimo (experimento 0)
RADIO = 1.5  # m: jugador a esta distancia o menos para que cuente como toque (experimento 0)
RADIO_RUIDO = 3.0  # m: sin ningún jugador a esta distancia, el cambio de velocidad cuenta como ruido
MINIMO = 10  # frames de balón visible seguidos para buscar toques (experimento 2)


def preparar(bx, by, px, py, team, fps):
    """Lo que necesita `medidas_cambios.toques` de un tramo: velocidades del balón y el jugador más cercano.

    `bx`, `by`: balón en metros, forma (n,), sin NaN (un tramo visible). `px`, `py`: jugadores, forma (n, slots), NaN
    donde falta el slot. `team`: equipo de cada slot. La velocidad es la diferencia entre frames por `fps`, como en
    `medidas_cambios.preparar`; la del primer frame copia la del segundo, como en `toques_por_tramos`.
    """
    x, y = np.asarray(bx, dtype=np.float64), np.asarray(by, dtype=np.float64)
    n = len(x)
    vx, vy = np.zeros(n), np.zeros(n)
    vx[1:], vy[1:] = np.diff(x) * fps, np.diff(y) * fps
    if n > 1:
        vx[0], vy[0] = vx[1], vy[1]
    dist = np.hypot(np.asarray(px, dtype=np.float64) - x[:, None], np.asarray(py, dtype=np.float64) - y[:, None])
    dist = np.where(np.isnan(dist), np.inf, dist)
    if dist.shape[1]:
        cercano = np.argmin(dist, axis=1)
        d1 = dist[np.arange(n), cercano]
        equipo = np.asarray(team)[cercano]
    else:
        d1, equipo = np.full(n, np.inf), np.full(n, -1)
    return {"n": n, "vx": vx, "vy": vy, "d1": d1, "equipo_cercano": equipo}


def eventos(bx, by, px, py, team, fps, mascara=None):
    """(frames, distancia al jugador más cercano) de los máximos locales del cambio de velocidad de UMBRAL o más.

    Por tramos de MINIMO frames o más con el balón visible (y dentro de `mascara`, si se da: por ejemplo, solo los
    frames en que el ATD ve el balón). Sin filtrar por jugador: lo hace `contar`.
    """
    bx, by = np.asarray(bx, dtype=np.float64), np.asarray(by, dtype=np.float64)
    visible = np.isfinite(bx) & np.isfinite(by)
    if mascara is not None:
        visible &= np.asarray(mascara, dtype=bool)
    frames, distancias = [], []
    for a, b, v in mc.rachas(visible.astype(int), MINIMO):
        if v != 1:
            continue
        prep = preparar(bx[a:b], by[a:b], px[a:b], py[a:b], team, fps)
        t, _, _ = mc.toques(prep, UMBRAL, RADIO)
        frames.append(t + a)
        distancias.append(prep["d1"][t])
    if not frames:
        return np.array([], dtype=int), np.array([])
    return np.concatenate(frames).astype(int), np.concatenate(distancias)


def contar(bx, by, px, py, team, fps, mascara=None):
    """{"toques": con un jugador a RADIO m o menos, "ruido": sin nadie a RADIO_RUIDO m o menos, "eventos": todos}."""
    _, d1 = eventos(bx, by, px, py, team, fps, mascara)
    return {"toques": int(np.sum(d1 <= RADIO)), "ruido": int(np.sum(d1 > RADIO_RUIDO)), "eventos": int(len(d1))}


def por_minuto(cuenta, frames, fps):
    """Una cuenta por minuto de `frames` frames; None si no hay frames."""
    return round(cuenta / (frames / float(fps) / 60.0), 2) if frames else None
