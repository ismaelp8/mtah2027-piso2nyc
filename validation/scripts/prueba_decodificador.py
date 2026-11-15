"""Prueba del decodificador (`possession/temporal.py`) con evidencias inventadas. No lee ningún dato.

    python validation/scripts/prueba_decodificador.py

Qué comprueba (pendiente de la revisión de la PR 9, docs/PLAN_ENTREGA.md §3, «David»):

1. `viterbi` da la misma puntuación que la búsqueda exhaustiva, con frames prohibidos.
2. `viterbi_min` con todos los mínimos a 1 da exactamente la salida de `viterbi`.
3. `viterbi_min` da la misma puntuación que la búsqueda exhaustiva entre los caminos que cumplen los mínimos
   (con las excepciones de su docstring: la primera y la última racha, y la que corta lo prohibido), y su
   camino los cumple.
4. `prune`: no deja posesiones cortas que se puedan pasar al otro equipo, no toca el `D` y respeta lo
   prohibido.
5. `decode`, `decode_min` y `decode_prune` dan lo mismo con los tramos en una lista, en una tupla o en un
   generador (antes, con un generador, `decode` devolvía todo `X` sin error), escriben `X` fuera de los tramos
   y son deterministas.
6. Las erratas dan error: un parámetro desconocido, un coste negativo, una evidencia no finita en un tramo,
   un frame sin ningún estado permitido y una duración mínima de 0.

Imprime solo recuentos. Sale con código 1 si algo falla.
"""

import itertools
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from possession import temporal  # noqa: E402
from possession.tracking import A, D, H, N_STATES, X  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEMILLA = 20261115
FALLOS = []


def comprobar(condicion, que):
    if not condicion:
        FALLOS.append(que)


def puntuacion(path, emission, cost):
    total = sum(emission[t][s] for t, s in enumerate(path))
    total -= sum(cost[a][b] for a, b in zip(path[:-1], path[1:]) if a != b)
    return total


def rachas(path):
    """[(estado, inicio, fin sin incluir)]."""
    return temporal.runs(np.asarray(path, dtype=np.int8))


def cumple_minimos(path, allow, minimum):
    """Las reglas de `viterbi_min`: cada racha dura su mínimo, salvo la primera, la última y la que acaba
    porque su estado queda prohibido en el frame siguiente."""
    piezas = rachas(path)
    for k, (s, a, b) in enumerate(piezas):
        if k == 0 or k == len(piezas) - 1 or b - a >= minimum[s]:
            continue
        if allow[b][s]:
            return False
    return True


def exhaustiva(emission, cost, minimum=None):
    """Mejor puntuación entre todos los caminos permitidos (y que cumplen los mínimos, si se dan)."""
    n = len(emission)
    allow = np.isfinite(emission)
    mejor = -np.inf
    for path in itertools.product(range(N_STATES), repeat=n):
        if not all(allow[t][s] for t, s in enumerate(path)):
            continue
        if minimum is not None and not cumple_minimos(path, allow, minimum):
            continue
        mejor = max(mejor, puntuacion(path, emission, cost))
    return mejor


def evidencia(rng, n, prohibido=0.2):
    """Emisión (n, 3) con enteros pequeños (empates frecuentes) y algunos frames prohibidos; nunca un frame
    sin ningún estado permitido."""
    emission = rng.integers(-4, 5, size=(n, N_STATES)).astype(float)
    mask = rng.random((n, N_STATES)) < prohibido
    for t in range(n):
        if mask[t].all():
            mask[t, rng.integers(N_STATES)] = False
    emission[mask] = -np.inf
    return emission


def coste(rng):
    return temporal.cost_matrix({"switch": float(rng.integers(0, 8)), "to_dead": float(rng.integers(0, 8)),
                                 "from_dead": float(rng.integers(0, 8))})


def prueba_viterbi(rng, casos=400):
    for _ in range(casos):
        n = int(rng.integers(1, 8))
        emission, cost = evidencia(rng, n), coste(rng)
        path = temporal.viterbi(emission, cost)
        comprobar(len(path) == n, "viterbi: largo del camino")
        comprobar(abs(puntuacion(path, emission, cost) - exhaustiva(emission, cost)) < 1e-9,
                  "viterbi: no da la mejor puntuación")
    return casos


def prueba_minimos_a_uno(rng, casos=300):
    for _ in range(casos):
        n = int(rng.integers(1, 40))
        emission, cost = evidencia(rng, n), coste(rng)
        comprobar(np.array_equal(temporal.viterbi_min(emission, cost, [1, 1, 1]), temporal.viterbi(emission, cost)),
                  "viterbi_min con mínimos 1 no da lo mismo que viterbi")
    return casos


def prueba_minimos(rng, casos=400):
    for _ in range(casos):
        n = int(rng.integers(1, 9))
        emission, cost = evidencia(rng, n, prohibido=0.15), coste(rng)
        minimum = [int(rng.integers(1, 5)), int(rng.integers(1, 5)), int(rng.integers(1, 5))]
        path = temporal.viterbi_min(emission, cost, minimum)
        allow = np.isfinite(emission)
        comprobar(all(allow[t][s] for t, s in enumerate(path)), "viterbi_min: camino por un estado prohibido")
        comprobar(cumple_minimos(path, allow, minimum), "viterbi_min: el camino no cumple los mínimos")
        comprobar(abs(puntuacion(path, emission, cost) - exhaustiva(emission, cost, minimum)) < 1e-9,
                  "viterbi_min: no da la mejor puntuación entre los caminos con mínimos")
    return casos


def prueba_poda(rng, casos=300):
    for _ in range(casos):
        n = int(rng.integers(1, 80))
        # Rachas de largo aleatorio: muchas cortas, para que haya qué podar.
        codes, allowed = [], np.ones((n, N_STATES), dtype=bool)
        while len(codes) < n:
            codes += [int(rng.choice([H, A, D], p=[0.45, 0.45, 0.1]))] * int(rng.integers(1, 15))
        codes = np.array(codes[:n], dtype=np.int8)
        allowed[rng.random(n) < 0.05, A] = False
        allowed[np.arange(n)[codes == A], A] = True  # lo que ya es A está permitido
        allowed[rng.random(n) < 0.05, H] = False
        allowed[np.arange(n)[codes == H], H] = True
        minimo = int(rng.integers(0, 15))
        podado = temporal.prune(codes, allowed, minimo)
        comprobar(np.array_equal(podado == D, codes == D), "poda: ha tocado el D")
        comprobar(all(allowed[t, s] for t, s in enumerate(podado)), "poda: ha puesto un estado prohibido")
        comprobar(np.array_equal(temporal.prune(podado, allowed, minimo), podado), "poda: no es idempotente")
        for s, a, b in rachas(podado):
            if s == D or b - a >= minimo:
                continue
            otro = A if s == H else H
            vecinas = [p for p in rachas(podado) if p[0] == otro and (p[2] == a or p[1] == b)]
            comprobar(not (vecinas and allowed[a:b, otro].all()),
                      "poda: queda una posesión corta que se podía pasar al otro equipo")
    # Un caso a mano: H×20, A×3, H×20 con mínimo 12 → todo H; con H prohibido en un frame de la racha de A,
    # no cambia nada.
    codes = np.array([H] * 20 + [A] * 3 + [H] * 20, dtype=np.int8)
    comprobar(np.all(temporal.prune(codes, np.ones((43, 3), bool), 12) == H), "poda: el caso a mano H A H")
    sin_h = np.ones((43, 3), bool)
    sin_h[21, H] = False
    comprobar(np.array_equal(temporal.prune(codes, sin_h, 12), codes), "poda: cambia aunque el otro equipo esté prohibido")
    entre_d = np.array([D] * 5 + [H] * 3 + [D] * 5, dtype=np.int8)
    comprobar(np.array_equal(temporal.prune(entre_d, np.ones((13, 3), bool), 12), entre_d),
              "poda: toca una posesión entre dos D")
    return casos + 3


def partido(rng, n=600):
    """Evidencia de un «partido» inventado con dos tramos y frames fuera de ellos."""
    score = rng.normal(0, 1, size=(n, N_STATES))
    allowed = rng.random((n, N_STATES)) > 0.05
    allowed[~allowed.any(axis=1), H] = True
    blocks = [(30, 280), (320, 580)]
    return score, allowed, blocks


def prueba_tramos(rng):
    score, allowed, blocks = partido(rng)
    fuera = np.ones(len(score), dtype=bool)
    for a, b in blocks:
        fuera[a:b] = False
    funciones = [("decode", temporal.decode, {}), ("decode_min", temporal.decode_min, {}),
                 ("decode_prune", temporal.decode_prune, {})]
    n = 0
    for nombre, funcion, opciones in funciones:
        de_lista = funcion(score, allowed, blocks, None, **opciones)
        for forma in (tuple(blocks), (tramo for tramo in blocks), iter(blocks)):
            comprobar(np.array_equal(funcion(score, allowed, forma, None, **opciones), de_lista),
                      "{}: cambia según cómo lleguen los tramos".format(nombre))
            n += 1
        comprobar(np.all(de_lista[fuera] == X), "{}: no escribe X fuera de los tramos".format(nombre))
        comprobar(not np.any(de_lista[~fuera] == X), "{}: escribe X dentro de un tramo".format(nombre))
        comprobar(np.array_equal(funcion(score, allowed, blocks, None, **opciones), de_lista),
                  "{}: no es determinista".format(nombre))
        n += 3
    # Con todos los mínimos a 1 y poda 0, las variantes son el decodificador de main.
    base = temporal.decode(score, allowed, blocks)
    comprobar(np.array_equal(temporal.decode_min(score, allowed, blocks, min_live=1, min_dead=1), base),
              "decode_min con mínimos 1 no es decode")
    comprobar(np.array_equal(temporal.decode_prune(score, allowed, blocks, min_len=0), base),
              "decode_prune con poda 0 no es decode")
    return n + 2


def prueba_erratas(rng):
    score, allowed, blocks = partido(rng)
    casos = [
        ("parámetro desconocido", lambda: temporal.decode(score, allowed, blocks, {"swich": 10}), KeyError),
        ("coste negativo", lambda: temporal.decode(score, allowed, blocks, {"switch": -1}), ValueError),
        ("mínimo 0", lambda: temporal.decode_min(score, allowed, blocks, min_live=0), ValueError),
        ("poda negativa", lambda: temporal.decode_prune(score, allowed, blocks, min_len=-1), ValueError),
        ("forma", lambda: temporal.decode(score[:, :2], allowed[:, :2], blocks), ValueError),
    ]
    no_finito = score.copy()
    no_finito[100, A] = np.nan
    casos.append(("no finito", lambda: temporal.decode(no_finito, allowed, blocks), ValueError))
    sin_estado = allowed.copy()
    sin_estado[100] = False
    casos.append(("sin estado permitido", lambda: temporal.decode(score, sin_estado, blocks), ValueError))
    for que, llamada, error in casos:
        try:
            llamada()
            FALLOS.append("errata sin error: " + que)
        except error:
            pass
    # Fuera de los tramos, lo no finito no importa.
    fuera = score.copy()
    fuera[5] = np.nan
    try:
        temporal.decode(fuera, allowed, blocks)
    except ValueError:
        FALLOS.append("da error por una evidencia no finita fuera de los tramos")
    return len(casos) + 1


def main():
    rng = np.random.default_rng(SEMILLA)
    pruebas = [
        ("viterbi frente a la búsqueda exhaustiva", prueba_viterbi),
        ("viterbi_min con mínimos 1 frente a viterbi", prueba_minimos_a_uno),
        ("viterbi_min frente a la búsqueda exhaustiva con mínimos", prueba_minimos),
        ("poda", prueba_poda),
        ("tramos en lista, tupla y generador; X fuera; determinismo", prueba_tramos),
        ("erratas", prueba_erratas),
    ]
    for nombre, prueba in pruebas:
        antes = len(FALLOS)
        casos = prueba(rng)
        print("{}: {} casos, {}".format(nombre, casos, "OK" if len(FALLOS) == antes else
                                        "{} FALLOS".format(len(FALLOS) - antes)))
    if FALLOS:
        print("\nFALLA:")
        for que in sorted(set(FALLOS)):
            print("  - {} ({} veces)".format(que, FALLOS.count(que)))
        sys.exit(1)
    print("\nTodo OK.")


if __name__ == "__main__":
    main()
