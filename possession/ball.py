"""Limpieza del balón. Recibe un `Tracking` y devuelve otro con el balón limpio.

`clean` es la que usa el pipeline: hoy, la versión 0, que devuelve el balón tal cual. Pasa a ser `clean_v1`
con el recuento del partido (validation/partido/limpieza_balon.py), y no por ganar en el harness: en la DFL
no hay saltos falsos que quitar, así que el harness no los ve. Ahí solo tiene que no empeorar frente a
main. La limpieza entra fija, sin competir (docs/PLAN_ENTREGA.md §3 y §8; docs/decisiones.md, 14/11). El
recuento salió como se esperaba; para hacer el cambio falta reentrenar la evidencia B5, que se entrenó con
`clean` tal cual (validation/apuesta_b/entrenar.py, la pieza de Ismael).

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

Límite conocido: una detección falsa de 2 frames pegada a balón bueno sobrevive a los pasos 1 y 2, porque
el paso 1 exige el salto a los dos lados de cada punto.
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
