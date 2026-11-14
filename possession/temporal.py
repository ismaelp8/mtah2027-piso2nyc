"""Decodificador temporal: de la evidencia por frame a una etiqueta por frame.

Versión 0 (T3 de docs/investigacion_metodos.md §2.5): Viterbi sobre {`H`, `A`, `D`} con un coste por cada
cambio de estado. Busca la secuencia de etiquetas con más puntuación total, descontando los cambios. Mira
el tramo entero, así que coloca cada cambio donde lo pide la evidencia de los dos lados, sin retraso.

Cada tramo evaluado (una parte) se decodifica por separado. Fuera de los tramos se escribe `X`.
"""

import numpy as np

from possession.tracking import A, D, H, N_STATES, X

# Costes de cada cambio, en las unidades de la evidencia. Sin ajustar: se fijan en la DFL dejando un
# partido fuera, nunca en el partido ni en la ventana pública.
DEFAULTS = {
    "switch": 25.0,  # H <-> A
    "to_dead": 25.0,  # H o A -> D
    "from_dead": 25.0,  # D -> H o A
}


def cost_matrix(params):
    """cost[i][j]: coste de pasar del estado i al j."""
    cost = [[0.0] * N_STATES for _ in range(N_STATES)]
    cost[H][A] = cost[A][H] = float(params["switch"])
    cost[H][D] = cost[A][D] = float(params["to_dead"])
    cost[D][H] = cost[D][A] = float(params["from_dead"])
    return cost


def viterbi(emission, cost):
    """Camino de más puntuación. `emission`: (n, 3), con -inf en lo prohibido. Devuelve (n,) int8.

    Empates: quedarse en el mismo estado gana a cambiar; entre dos cambios gana el estado de índice más
    bajo; al final gana el estado de índice más bajo. Así la salida no depende de la máquina.
    """
    rows = emission.tolist()
    n = len(rows)
    if n == 0:
        return np.zeros(0, dtype=np.int8)
    states = range(N_STATES)
    best = list(rows[0])
    back = []
    for t in range(1, n):
        row = rows[t]
        new = [0.0] * N_STATES
        pointers = [0] * N_STATES
        for j in states:
            arg, value = j, best[j]
            for i in states:
                if i != j:
                    v = best[i] - cost[i][j]
                    if v > value:
                        arg, value = i, v
            new[j] = value + row[j]
            pointers[j] = arg
        best = new
        back.append(pointers)
    state = max(states, key=lambda s: (best[s], -s))
    path = np.empty(n, dtype=np.int8)
    path[n - 1] = state
    for t in range(n - 2, -1, -1):
        state = back[t][state]
        path[t] = state
    return path


def decode(score, allowed, blocks, params=None):
    """Etiqueta por frame: 0 `H`, 1 `A`, 2 `D`, y 3 `X` fuera de los tramos evaluados.

    `score` y `allowed` son la evidencia combinada, de forma (n, 3). En cada frame evaluado la puntuación
    tiene que ser finita y tiene que haber al menos un estado permitido. `blocks` son los tramos (inicio,
    fin) con el fin sin incluir. `params` cambia los costes de `DEFAULTS`; una clave que no esté ahí o un
    coste negativo dan error, para que una errata no pase por un ajuste.
    """
    unknown = sorted(set(params or {}) - set(DEFAULTS))
    if unknown:
        raise KeyError("parámetros desconocidos del decodificador: {}".format(unknown))
    merged = dict(DEFAULTS)
    merged.update(params or {})
    if any(float(value) < 0 for value in merged.values()):
        raise ValueError("los costes del decodificador no pueden ser negativos")
    if np.shape(score) != np.shape(allowed) or np.ndim(score) != 2 or np.shape(score)[1] != N_STATES:
        raise ValueError("la evidencia tiene que ser de forma (n, 3)")
    cost = cost_matrix(merged)
    emission = np.where(allowed, score, -np.inf)
    codes = np.full(len(score), X, dtype=np.int8)
    for start, stop in blocks:
        finite = np.isfinite(score[start:stop])
        if not finite.all():
            raise ValueError("la evidencia tiene {} valores no finitos en un tramo evaluado".format(
                int((~finite).sum())))
        if not allowed[start:stop].any(axis=1).all():
            raise ValueError("hay frames evaluados sin ningún estado permitido")
        codes[start:stop] = viterbi(emission[start:stop], cost)
    return codes
