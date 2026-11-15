"""Limpieza del balón. Recibe un `Tracking` y devuelve otro con el balón limpio.

`clean` es la que usa el pipeline: hoy, la versión 0, que devuelve el balón tal cual. Si pasa a ser
`clean_v1` lo decide Ismael (docs/decisiones.md, 14 y 15/11), no el harness: en la DFL no hay saltos falsos
que quitar, así que ahí la limpieza solo puede no empeorar frente a main, y empata. El recuento del partido
(validation/partido/limpieza_balon.py) dice que cambiaría el 0,23 % de los frames con balón. Encenderla
exige reentrenar la evidencia B5, que se entrenó con `clean` tal cual (validation/apuesta_b/entrenar.py),
volver a medirla en el harness, repetir validation/partido/agregados_dead_ball.py (la capa del hueco de
dead_ball se midió con el balón sin limpiar) y regenerar y reproducir la entrega.

`clean_v1` (docs/investigacion_metodos.md §2.1, A1 + A2) es una sola versión, sin variantes. Los pasos 1 y 2
se calculan los dos sobre el balón de entrada y se quitan juntos; después va el 3:

1. Salto imposible: se quita un punto si, para llegar a él desde el punto visto anterior y para ir de él al
   siguiente, el balón tendría que ir a más de MAX_SPEED. Se exigen los dos lados para no borrar el primer
   punto bueno después de un salto.
2. Detección aislada: se quita una racha de ISOLATED_MAX frames con balón o menos que tiene huecos a los
   dos lados en el balón de entrada. Corrección del 14/11: antes se calculaba después del paso 1, y el
   agujero que abre un pico convertía en «aislada» la racha buena pegada a él.
3. Hueco corto: se interpola en línea recta un hueco de MAX_GAP frames o menos entre dos puntos vistos,
   salvo si el hueco obliga a ir a más de MAX_SPEED (el balón no reaparece donde se le espera) o si el
   balón reaparece junto a un jugador del otro equipo: en el primer frame tras el hueco el más cercano es
   del equipo contrario al más cercano del último frame antes del hueco, y está a NEAR_RIVAL o menos. Ahí
   puede haber un cambio de posesión, y decide el decodificador.

Solo cambia el balón; los jugadores no se tocan. Lo de fuera de los límites del campo no se toca aquí: es
señal para el `D` (possession/dead_ball.py).

`advance_ball` (15/11) es otra variante, tampoco encendida: adelanta el balón BALL_LEAD frames. La medida del
retraso del balón del ATD frente a los jugadores (validation/retraso_balon/BITACORA.md §8 a §10; tarea 1 de
Antonio en docs/PLAN_ENTREGA.md §3) da +4 frames: el candidato 2 de su regla, fijada antes de medir. Es un
agregado del tracking del partido entero, sin etiquetas, como pide el plan. Encenderla lo decide Ismael, con
las mismas consecuencias que `clean_v1` (reentrenar o medir B5 y repetir la medida de Manuel) y una más: la
degradación «como el ATD» del harness tendría que retrasar el balón BALL_LEAD frames. Hoy llega a su hora (media
centrada, validation/harness/dfl.py), así que con la pieza encendida el harness mediría un balón adelantado,
no una corrección. En el harness, ese retraso cuesta entre −0,007 y +0,002 de spellF1: empate (docs/decisiones.md,
15/11).

Límites conocidos:
- una detección falsa de 2 frames pegada a balón bueno sobrevive a los pasos 1 y 2, porque el paso 1 exige
  el salto a los dos lados de cada punto;
- en un salto grande suavizado (varios frames seguidos a más de MAX_SPEED), el paso 1 quita el tránsito,
  pero el salto queda: el balón sigue en el sitio de llegada. En el ATD del partido hay 15 así, y ningún
  pico de un frame (recuento del 14/11 en docs/decisiones.md).
"""

import numpy as np

from possession.candidates import NOBODY, proximity

# Sin ajustar; ninguno sale del partido ni de la ventana pública (docs/decisiones.md, 14/11). Los tres
# primeros son los cortes que mide el perfil del ATD (validation/perfil_atd/BITACORA.md §4, filas 1 y 6),
# para que su medida diga cuánto toca cada regla en el partido; NEAR_RIVAL sale del experimento 2.
MAX_SPEED = 40.0  # m/s; los golpeos más fuertes publicados rondan 18–35 m/s
ISOLATED_MAX = 2  # frames
MAX_GAP = 12  # frames: huecos de menos de 0,5 s
NEAR_RIVAL = 2.0  # m: el radio de toque «ampliado» del experimento 2

# La excepción, para `advance_ball`: este valor SÍ sale del partido. Es el retraso del balón del ATD frente a
# los jugadores (d̂ = +4, del 5 al 95 % de +2 a +5), un agregado del tracking del partido entero sin ninguna
# etiqueta, que calcula un algoritmo (validation/partido/retraso_balon.py, con la regla fijada antes de medir
# en validation/retraso_balon/BITACORA.md §8). Es el candidato 2 de la tarea 1 de Antonio (docs/PLAN_ENTREGA.md
# §3) y entra en lo que RULES.md permite sobre el partido: «learning without human labels… provided no person
# decided any of them». No está ligado a frames concretos ni sale de la ventana pública. Apagado.
BALL_LEAD = 4  # frames


def runs(mask):
    """(inicios, fines) de las rachas de True de `mask`, con el fin sin incluir."""
    mask = np.asarray(mask, dtype=bool)
    edges = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    return np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)


def drop_jumps(bx, by, fps):
    """Máscara de los puntos vistos que son un salto imposible por los dos lados."""
    seen = np.flatnonzero(~np.isnan(bx) & ~np.isnan(by))
    bad = np.zeros(len(bx), dtype=bool)
    if len(seen) < 3:
        return bad
    speed = np.hypot(np.diff(bx[seen]), np.diff(by[seen])) * fps / np.diff(seen)
    jump = speed > MAX_SPEED
    bad[seen[1:-1][jump[:-1] & jump[1:]]] = True
    return bad


def drop_isolated(visible):
    """Máscara de las rachas con balón de ISOLATED_MAX frames o menos con huecos a los dos lados."""
    bad = np.zeros(len(visible), dtype=bool)
    starts, stops = runs(visible)
    short = (stops - starts <= ISOLATED_MAX) & (starts > 0) & (stops < len(visible))
    for start, stop in zip(starts[short], stops[short]):
        bad[start:stop] = True
    return bad


def fill_short_gaps(trk, bx, by):
    """Copias de bx y by con los huecos cortos interpolados, salvo donde el balón no reaparece donde se le
    espera o reaparece junto a un jugador del otro equipo."""
    bx, by = bx.copy(), by.copy()
    starts, stops = runs(np.isnan(bx) | np.isnan(by))
    inner = (starts > 0) & (stops < len(bx)) & (stops - starts <= MAX_GAP)
    before, after = starts[inner] - 1, stops[inner]
    if len(before) == 0:
        return bx, by
    jump = np.hypot(bx[after] - bx[before], by[after] - by[before]) * trk.fps / (after - before)
    probe = trk._replace(bx=bx, by=by)
    team_before, _ = proximity(probe, before)
    team_after, dist_after = proximity(probe, after)
    near_after = dist_after.min(axis=1)
    rival = (team_before != NOBODY) & (team_after != NOBODY) & (team_after != team_before) & \
        (near_after <= NEAR_RIVAL)
    for a, b in zip(before[(jump <= MAX_SPEED) & ~rival], after[(jump <= MAX_SPEED) & ~rival]):
        frac = np.arange(1, b - a) / float(b - a)
        bx[a + 1:b] = bx[a] + frac * (bx[b] - bx[a])
        by[a + 1:b] = by[a] + frac * (by[b] - by[a])
    return bx, by


def clean(trk):
    """El tracking que reciben las piezas. Versión 0: el balón tal cual."""
    return trk


def clean_v1(trk):
    """El tracking con el balón limpio: sin saltos imposibles ni detecciones aisladas, y con los huecos
    cortos interpolados. `trk` no cambia."""
    bx = np.array(trk.bx, dtype=np.float64)
    by = np.array(trk.by, dtype=np.float64)
    # Los pasos 1 y 2, sobre el balón de entrada: así el agujero de un pico no aísla al balón bueno de al lado.
    bad = drop_jumps(bx, by, trk.fps) | drop_isolated(~np.isnan(bx) & ~np.isnan(by))
    bx[bad], by[bad] = np.nan, np.nan
    bx, by = fill_short_gaps(trk, bx, by)
    # De solo lectura, como el tracking que reparte el harness: una pieza posterior no puede cambiarlo.
    bx.setflags(write=False)
    by.setflags(write=False)
    return trk._replace(bx=bx, by=by)


def advance_ball(trk, frames=BALL_LEAD):
    """El tracking con el balón adelantado `frames` frames (retrasado si es negativo): el balón del frame t pasa
    a ser el que el tracking trae en t + frames. Se quedan sin balón los últimos `frames` frames o, si es
    negativo, los primeros. Los jugadores no se tocan y `trk` no cambia."""
    frames = int(frames)
    out = []
    for values in (trk.bx, trk.by):
        values = np.asarray(values, dtype=np.float64)
        shifted = np.full(len(values), np.nan)
        if frames >= 0:
            shifted[:len(values) - frames] = values[frames:]
        else:
            shifted[-frames:] = values[:len(values) + frames]
        shifted.setflags(write=False)
        out.append(shifted)
    return trk._replace(bx=out[0], by=out[1])
