"""Prueba del detector de cambios de posesión (`possession/cambios.py`, `temporal.decode_cambios` y el argumento
`cambios` de `pipeline.run`) con datos inventados. No lee ningún dato.

    python validation/scripts/prueba_cambios.py

Qué comprueba:

1. `viterbi_cambios` con la rebaja a cero da exactamente la salida de `viterbi`, y con rebaja da la misma puntuación
   que la búsqueda exhaustiva.
2. `decode_cambios` sin `bonus` es `decode`; con un `bonus` mal formado, negativo o no finito da error.
3. `pipeline.run` sin `cambios` da lo mismo que antes, y con una rebaja a cero también.
4. `cambios.capa`: con un detector perfecto empuja desde el frame del cambio durante `ventana` + 2·12 + 1 frames, solo
   al equipo nuevo, no puntúa `D` y no prohíbe nada.
5. `cambios.rasgos`: sin NaN inesperados en un tracking completo, la misma forma con y sin `fuente`, y al
   intercambiar los equipos las columnas de `H` y de `A` se intercambian y las diferencias cambian de signo.
6. `cambios.p_reglas`: en una jugada inventada con un pase interceptado, ve el cambio hacia el equipo que intercepta.

Imprime solo recuentos. Sale con código 1 si algo falla.
"""

import itertools
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from possession import cambios, pipeline, temporal, tracking  # noqa: E402
from possession.tracking import A, D, H, N_STATES  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEMILLA = 20261116
FALLOS = []


def comprobar(condicion, que):
    if not condicion:
        FALLOS.append(que)


def da_error(funcion):
    try:
        funcion()
    except (ValueError, KeyError):
        return True
    return False


def puntuacion(camino, emission, cost, bonus):
    total = emission[0][camino[0]]
    for t in range(1, len(camino)):
        i, j = camino[t - 1], camino[t]
        if i != j:
            c = cost[i][j]
            if i != D and j != D:
                c = max(0.0, c - bonus[t][j])
            total -= c
        total += emission[t][j]
    return total


def partido_inventado(rng, n=600, por_equipo=11):
    """Un tracking completo: jugadores que pasean y un balón que va de uno a otro."""
    largo, ancho = 105.0, 68.0
    px = np.cumsum(rng.normal(0, 0.1, (n, 2 * por_equipo)), axis=0) + rng.uniform(10, largo - 10, 2 * por_equipo)
    py = np.cumsum(rng.normal(0, 0.1, (n, 2 * por_equipo)), axis=0) + rng.uniform(10, ancho - 10, 2 * por_equipo)
    team = np.repeat(np.array([0, 1], dtype=np.int8), por_equipo)
    bx = np.cumsum(rng.normal(0, 0.3, n)) + largo / 2
    by = np.cumsum(rng.normal(0, 0.3, n)) + ancho / 2
    return tracking.Tracking(bx, by, px, py, team, (largo, ancho), ((0, n),), 25)


def main():
    rng = np.random.default_rng(SEMILLA)
    cost = temporal.cost_matrix({"switch": 3.0, "to_dead": 2.0, "from_dead": 2.5})

    # 1. viterbi_cambios
    casos = 0
    for _ in range(40):
        n = 7
        emission = rng.normal(0, 2, (n, N_STATES))
        cero = np.zeros((n, 2))
        comprobar(np.array_equal(temporal.viterbi(emission, cost), temporal.viterbi_cambios(emission, cost, cero)),
                  "viterbi_cambios con rebaja a cero no es viterbi")
        bonus = rng.uniform(0, 5, (n, 2)) * (rng.random((n, 2)) < 0.4)
        camino = temporal.viterbi_cambios(emission, cost, bonus)
        mejor = max(puntuacion(c, emission.tolist(), cost, bonus.tolist())
                    for c in itertools.product(range(N_STATES), repeat=n))
        comprobar(abs(puntuacion(camino.tolist(), emission.tolist(), cost, bonus.tolist()) - mejor) < 1e-9,
                  "viterbi_cambios no da la mejor puntuación")
        casos += 1
    largo = rng.normal(0, 2, (3000, N_STATES))
    comprobar(np.array_equal(temporal.viterbi(largo, cost), temporal.viterbi_cambios(largo, cost, np.zeros((3000, 2)))),
              "viterbi_cambios con rebaja a cero no es viterbi (tramo largo)")

    # 2. decode_cambios
    n = 500
    score, allowed = rng.normal(0, 3, (n, N_STATES)), np.ones((n, N_STATES), dtype=bool)
    blocks = ((20, 240), (260, 480))
    comprobar(np.array_equal(temporal.decode(score, allowed, blocks), temporal.decode_cambios(score, allowed, blocks)),
              "decode_cambios sin bonus no es decode")
    comprobar(np.array_equal(temporal.decode(score, allowed, blocks),
                             temporal.decode_cambios(score, allowed, blocks, bonus=np.zeros((n, 2)))),
              "decode_cambios con bonus a cero no es decode")
    malos = {"forma": np.zeros((n, 3)), "negativo": np.full((n, 2), -1.0), "no finito": np.full((n, 2), np.nan)}
    for que, bonus in malos.items():
        comprobar(da_error(lambda b=bonus: temporal.decode_cambios(score, allowed, blocks, bonus=b)),
                  "decode_cambios no da error con un bonus {}".format(que))

    # 3. pipeline.run
    trk = partido_inventado(rng)
    antes = pipeline.run(trk)
    comprobar(np.array_equal(antes, pipeline.run(trk, cambios=None)), "pipeline.run cambia con cambios=None")
    comprobar(np.array_equal(antes, pipeline.run(trk, cambios=np.zeros((len(trk.bx), 2)))),
              "pipeline.run cambia con una rebaja a cero")
    comprobar(np.array_equal(antes, pipeline.run(trk, cambios=lambda t: cambios.rebaja(np.zeros((len(t.bx), 2)), 25))),
              "pipeline.run cambia con una función que da una rebaja a cero")

    # 4. la capa
    n, t0, ventana = 400, 150, 50
    p = np.zeros((n, 2))
    p[t0 - cambios.SEMIANCHO:t0 + cambios.SEMIANCHO + 1, A] = 1.0
    capa, permitido = cambios.capa(p, 4.0, ventana)
    con = np.flatnonzero(capa[:, A] > 0)
    comprobar(len(con) and con[0] == t0 and con[-1] == t0 + 2 * cambios.SEMIANCHO + ventana,
              "la capa no empuja desde el cambio durante ventana + 2·12 + 1 frames")
    comprobar(np.all(capa[con, A] == 4.0) and not capa[:, H].any() and not capa[:, D].any() and permitido.all(),
              "la capa puntúa lo que no debe o prohíbe algo")
    comprobar(not cambios.capa(p, 0.0, ventana)[0].any(), "la capa con gamma 0 puntúa")
    comprobar(da_error(lambda: cambios.capa(np.full((n, 2), 2.0), 1.0, 5)) and da_error(lambda: cambios.rebaja(p, -1)),
              "la capa o la rebaja no dan error con valores imposibles")

    # 5. los rasgos
    x, nombres = cambios.rasgos(trk)
    fuente = rng.random(len(trk.bx)) < 0.5
    x_video, nombres_video = cambios.rasgos(trk, fuente)
    centro = slice(max(cambios.K), len(trk.bx) - max(cambios.K))
    comprobar(x.shape == x_video.shape == (len(trk.bx), len(nombres)) and nombres == nombres_video,
              "los rasgos cambian de forma con la fuente")
    comprobar(not np.isnan(x[centro]).any(), "hay NaN en los rasgos de un tracking completo")
    girado, _ = cambios.rasgos(trk._replace(team=1 - trk.team))
    for i, nombre in enumerate(nombres):
        if "_H_" in nombre:
            otro = nombres.index(nombre.replace("_H_", "_A_"))
            comprobar(np.allclose(x[centro, i], girado[centro, otro]) and np.allclose(x[centro, otro], girado[centro, i]),
                      "al intercambiar los equipos no se intercambia {}".format(nombre))
        elif nombre.startswith(("dif_", "cambio_dif_")):
            comprobar(np.allclose(x[centro, i], -girado[centro, i]), "{} no cambia de signo".format(nombre))
        elif "_A_" not in nombre:
            comprobar(np.allclose(x[centro, i], girado[centro, i]), "{} cambia al intercambiar los equipos".format(nombre))
    comprobar(max(int(nombre.rsplit("_", 1)[1].lstrip("mp")) for nombre in nombres) <= 25,
              "hay un rasgo con una ventana de más de 25 frames")

    # 6. las reglas: H pasa (balón recto), A intercepta en el frame 100 y se lo lleva en otra dirección.
    n = 220
    t = np.arange(n, dtype=float)
    bx = np.where(t < 40, 30.0, np.where(t < 100, 30.0 + (t - 40) * 0.4, 54.0))
    by = np.where(t < 100, 30.0, 30.0 + (t - 100) * 0.2)
    # Un toque de H al salir el pase (frame 40) y el de A al interceptarlo (frame 100).
    px = np.column_stack((np.full(n, 29.5), np.full(n, 54.5)))
    py = np.column_stack((np.full(n, 30.0), by.copy()))
    py[:100, 1] = 30.0
    jugada = tracking.Tracking(bx, by, px, py, np.array([0, 1], dtype=np.int8), (105.0, 68.0), ((0, n),), 25)
    frames, equipos = cambios.toques(jugada)
    p = cambios.p_reglas(jugada)
    hacia_a = np.flatnonzero(p[:, A] > 0)
    comprobar(len(frames) >= 2 and equipos[0] == H and equipos[-1] == A, "las reglas no ven los dos toques")
    comprobar(len(hacia_a) and hacia_a[0] <= 100 <= hacia_a[-1] and not p[:, H].any(),
              "las reglas no ven el cambio hacia A en la intercepción")

    print("viterbi_cambios: {} casos contra la búsqueda exhaustiva · rasgos: {} · toques de la jugada inventada: {}".format(
        casos, len(nombres), len(frames)))
    if FALLOS:
        print("\nFALLOS ({}):".format(len(FALLOS)))
        for fallo in sorted(set(FALLOS)):
            print("- " + fallo)
        sys.exit(1)
    print("Todo OK.")


if __name__ == "__main__":
    main()
