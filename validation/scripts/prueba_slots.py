"""Prueba `ball.clean_slots` y `ball.surplus_slots` (quitar los slots sobrantes, P4) con un tracking inventado.

    python validation/scripts/prueba_slots.py

Sin datos de ningún partido. Lo puede ejecutar cualquiera, Claude incluido. Prueba que sin sobrantes no cambia nada,
que quita al más nuevo y solo los que sobran, cómo se equivoca cuando un jugador de verdad tiene el slot más nuevo, el
empate, que no cambia el tracking de entrada, que es determinista y que entra en el pipeline como la pieza `ball`.
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
from possession import ball, pipeline  # noqa: E402
from possession.tracking import A, H, Tracking  # noqa: E402

FALLOS = []
N = 3000


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def tracking(extra=()):
    """22 jugadores que se mueven, más los slots de `extra`: [(equipo, inicio, fin, x, y)] con x, y constantes o
    arrays."""
    rng = np.random.default_rng(2)
    t = np.arange(N)[:, None]
    px = rng.uniform(10, 95, 22)[None, :] + 3 * np.sin(t / 80.0 + np.arange(22)[None, :])
    py = rng.uniform(5, 63, 22)[None, :] + 3 * np.cos(t / 90.0 + np.arange(22)[None, :])
    team = [H] * 11 + [A] * 11
    cols_x, cols_y = [px], [py]
    for equipo, a, b, x, y in extra:
        cx, cy = np.full((N, 1), np.nan), np.full((N, 1), np.nan)
        cx[a:b, 0], cy[a:b, 0] = x, y
        cols_x.append(cx)
        cols_y.append(cy)
        team.append(equipo)
    px = np.hstack(cols_x).astype(np.float32)
    py = np.hstack(cols_y).astype(np.float32)
    bx, by = np.full(N, 52.0), np.full(N, 34.0)
    return Tracking(bx, by, px, py, np.array(team, dtype=np.int8), (105.0, 68.0), ((100, 2900),), 25)


def main():
    print("Prueba de ball.clean_slots")
    limpio = tracking()
    check("sin sobrantes no cambia nada (devuelve el mismo tracking)", ball.clean_slots(limpio) is limpio)

    trk = tracking([(H, 1000, 1500, 50.0, 30.0)])
    sobra = ball.surplus_slots(trk)
    check("un fantasma del local en 500 frames: sobra justo él", sobra[:, 22].sum() == 500 and sobra[:, :22].sum() == 0,
          (int(sobra[:, 22].sum()), int(sobra[:, :22].sum())))
    limpio = ball.clean_slots(trk)
    check("y se queda en NaN", np.isnan(limpio.px[1000:1500, 22]).all() and np.isnan(limpio.py[1000:1500, 22]).all())
    check("el resto del tracking no cambia",
          np.array_equal(limpio.px[:, :22], trk.px[:, :22]) and np.array_equal(limpio.bx, trk.bx))
    check("el de entrada no cambia", not np.isnan(trk.px[1000:1500, 22]).any())
    check("de solo lectura", not limpio.px.flags.writeable and not limpio.py.flags.writeable)

    # el jugador 0 del local corta su tracklet en el 1200: desde ahí está en un slot nuevo, más nuevo que el fantasma
    trk = tracking([(H, 1000, 1500, 50.0, 30.0), (H, 1200, N, 0.0, 0.0)])
    px, py = np.array(trk.px), np.array(trk.py)
    px[1200:, 23], py[1200:, 23] = px[1200:, 0], py[1200:, 0]
    px[1200:, 0], py[1200:, 0] = np.nan, np.nan
    trk = trk._replace(px=px, py=py)
    sobra = ball.surplus_slots(trk)
    check("cuando un jugador de verdad tiene el slot más nuevo, lo quita a él (el fallo conocido)",
          sobra[1000:1200, 22].all() and sobra[1200:1500, 23].all() and not sobra[1200:1500, 22].any(),
          (int(sobra[:, 22].sum()), int(sobra[:, 23].sum())))

    trk = tracking([(A, 1000, 1500, 50.0, 30.0), (A, 1100, 1300, 60.0, 30.0)])
    sobra = ball.surplus_slots(trk)
    check("con 13, quita los dos más nuevos", sobra[1100:1300, 22:24].all() and sobra[1000:1100, 22].all()
          and sobra[:, :22].sum() == 0)
    check("y fuera de los frames con sobrantes, nada", not sobra[:1000].any() and not sobra[1500:].any())

    trk = tracking([(H, 1000, 1500, 50.0, 30.0), (H, 1000, 1500, 55.0, 30.0)])
    sobra = ball.surplus_slots(trk)
    check("empate (los dos igual de nuevos, 13 slots): quita los dos", sobra[1000:1500, 22:24].all())
    trk = tracking([(H, 1000, 1500, 50.0, 30.0), (H, 1000, 1500, 55.0, 30.0)])
    px, py = np.array(trk.px), np.array(trk.py)
    px[1000:1500, 0], py[1000:1500, 0] = np.nan, np.nan  # el local tiene 12: sobra uno de los dos empatados
    sobra = ball.surplus_slots(trk._replace(px=px, py=py))
    check("empate con 12: sobra el de índice más alto", sobra[1000:1500, 23].all() and not sobra[:, 22].any())

    a, b = ball.surplus_slots(tracking([(H, 1000, 1500, 50.0, 30.0)])), ball.surplus_slots(
        tracking([(H, 1000, 1500, 50.0, 30.0)]))
    check("determinista", np.array_equal(a, b))

    trk = tracking([(H, 1000, 1500, 50.0, 30.0)])
    codigos = pipeline.run(trk, pieces={"ball": ball.clean_slots})
    check("entra en el pipeline como la pieza ball", len(codigos) == N)
    print()
    if FALLOS:
        print("FALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
        return 1
    print("Todo bien.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
