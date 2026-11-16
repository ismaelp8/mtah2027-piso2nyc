"""Decodificador temporal: de la evidencia por frame a una etiqueta por frame.

Versión 0 (T3 de docs/investigacion_metodos.md §2.5): Viterbi sobre {`H`, `A`, `D`} con un coste por cada
cambio de estado. Busca la secuencia de etiquetas con más puntuación total, descontando los cambios. Mira
el tramo entero, así que coloca cada cambio donde lo pide la evidencia de los dos lados, sin retraso.

Cada tramo evaluado (una parte) se decodifica por separado. Fuera de los tramos se escribe `X`.

Variantes para el harness (candidatos del 15/11 en docs/decisiones.md), con la misma firma que `decode`:

- `decode_min`: el mismo Viterbi con una duración mínima por racha, como restricción dura (b);
- `decode_prune`: el Viterbi de `decode` y después la poda de las posesiones cortas (c, T7 sin el ajuste de
  fronteras);
- `decode_cortas_a_d`: el Viterbi de `decode` y después las posesiones cortas que vienen de un cambio
  directo desde el otro equipo y acaban en `D` pasan a `D` (idea 1.3 de
  `docs/investigacion_2026-11-16.md` §2.1; la variante «a D» de los sondeos S5 y S9).

La entrega usa `decode` (`pipeline.PIECES`). Las variantes solo entran si ganan en el harness.
"""

import heapq

import numpy as np

from possession.tracking import A, D, H, N_STATES, X

# Costes de cada cambio, en las unidades de la evidencia. Sin ajustar: se fijan en la DFL dejando un
# partido fuera, nunca en el partido ni en la ventana pública. Con el `D` oráculo del harness, `to_dead` y
# `from_dead` no cambian nada (todos los caminos cruzan los mismos `D`): solo se mide `switch`.
DEFAULTS = {
    "switch": 25.0,  # H <-> A
    "to_dead": 25.0,  # H o A -> D
    "from_dead": 25.0,  # D -> H o A
}

# Duraciones mínimas de `decode_min` y de la poda de `decode_prune`, en frames. Sin ajustar: escritas antes
# de medir (docs/decisiones.md, 15/11). 12 frames son 0,5 s, el control de la convención «control»; la GT
# tiene posesiones reales de menos de 1 s. 25 frames de `D` no se pueden medir con el `D` oráculo.
MIN_LIVE = 12
MIN_DEAD = 25
PRUNE = 12

# Corte de `decode_cortas_a_d`, en frames. Sin ajustar: escrito antes de medir, en la regla de S5
# (`validation/investigacion_1116/BITACORA.md`). 125 frames son 5 s a 25 fps, la frecuencia del partido, de la
# DFL y de SkillCorner (que se interpola de 10 a 25). Es una duración, no un frame concreto de este partido.
CORTE_CORTAS = 125

NEG = float("-inf")


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


def viterbi_min(emission, cost, minimum):
    """Como `viterbi`, pero ninguna racha del estado s dura menos de `minimum[s]` frames.

    Excepciones, para que siempre haya un camino posible:
    - la primera racha del tramo y la última, que el borde del tramo corta;
    - una racha que lo prohibido obliga a cortar: se puede salir antes del mínimo de un estado solo si en el
      frame siguiente ese estado está prohibido (el juego vivo entre dos `D` del oráculo, el tramo antes
      del saque).

    Cómo (un semi-Markov con duraciones de al menos m, en O(n · 3²) y sin estados de más):
    - `M[s]`: mejor camino que acaba en t en s con una racha ya madura (m frames o más, o la primera del
      tramo);
    - `G[s][t]`: mejor valor, sin la emisión de t, de empezar una racha de s en t;
    - una racha madura en t, o venía madura en t-1 (se queda), o empezó en t-m+1 (G más las emisiones de
      en medio, con sumas acumuladas).

    Empates como en `viterbi`: quedarse gana a empezar; entre orígenes, el de índice más bajo; al final, el
    estado de índice más bajo. Con todos los mínimos a 1 da exactamente la salida de `viterbi`.
    """
    rows = emission.tolist()
    n = len(rows)
    if n == 0:
        return np.zeros(0, dtype=np.int8)
    states = range(N_STATES)
    minimum = [max(1, int(m)) for m in minimum]
    ok = np.isfinite(emission)
    # Sumas acumuladas de la emisión (0 en lo prohibido) y de los frames prohibidos, por estado. La suma de
    # e[s][a..b] es la diferencia de las acumuladas, o -inf si hay algo prohibido en medio.
    cum = np.concatenate([np.zeros((1, N_STATES)), np.cumsum(np.where(ok, emission, 0.0), axis=0)]).T.tolist()
    bad = np.concatenate([np.zeros((1, N_STATES), dtype=np.int64),
                          np.cumsum(~ok, axis=0)]).T.tolist()
    allow = ok.tolist()

    def span(s, a, b):  # suma de e[s][a..b], ambos incluidos; 0 si el tramo está vacío
        if b < a:
            return 0.0
        if bad[s][b + 1] - bad[s][a]:
            return NEG
        return cum[s][b + 1] - cum[s][a]

    G = [[NEG] * n for _ in states]  # G[s][t]
    gsrc = [[None] * n for _ in states]  # de dónde viene G[s][t]: (s', inicio de su racha o -1 si madura)
    mstart = [[-1] * n for _ in states]  # -1: la racha madura en t viene de t-1; si no, empezó en ese frame
    M = list(rows[0])  # la primera racha del tramo cuenta como madura

    def immature(s, t):
        """Mejor camino que acaba en t en s con una racha más corta que el mínimo: (valor, inicio)."""
        value, where = NEG, -1
        for start in range(max(1, t - minimum[s] + 2), t + 1):  # rachas de 1 a m-1 frames
            g = G[s][start]
            if g == NEG:
                continue
            v = g + span(s, start, t)
            if v > value:
                value, where = v, start
        return value, where

    for t in range(1, n):
        # Desde qué se puede salir de cada estado en t-1: la racha madura y, si s queda prohibido en t, también
        # una inmadura.
        leave = []
        for s in states:
            value, where = M[s], -1
            if allow[t - 1][s] and not allow[t][s] and minimum[s] > 1:
                v, w = immature(s, t - 1)
                if v > value:
                    value, where = v, w
            leave.append((value, where))
        new = [0.0] * N_STATES
        for j in states:
            arg, value = None, NEG
            for i in states:
                if i != j:
                    v = leave[i][0] - cost[i][j]
                    if v > value:
                        arg, value = i, v
            G[j][t] = value
            if arg is not None:
                gsrc[j][t] = (arg, leave[arg][1])
            start = t - minimum[j] + 1  # con mínimo 1, la racha empieza en t y no hay emisiones en medio
            entered = NEG
            if start >= 1:
                g = G[j][start]
                if g != NEG:
                    entered = g + span(j, start, t - 1)
            if entered > M[j]:
                mstart[j][t] = start
                new[j] = entered + rows[t][j]
            else:
                new[j] = M[j] + rows[t][j]
        M = new

    # Al final vale también una racha inmadura: la corta el borde del tramo.
    final = []
    for s in states:
        value, where = M[s], -1
        v, w = immature(s, n - 1)
        if v > value:
            value, where = v, w
        final.append((value, where))
    state = max(states, key=lambda s: (final[s][0], -s))
    path = np.empty(n, dtype=np.int8)
    t, where = n - 1, final[state][1]
    while t >= 0:
        if where == -1:  # racha madura en t
            begin = mstart[state][t]
            if begin == -1:
                path[t] = state
                t -= 1
                continue
        else:  # racha inmadura que empezó en `where`
            begin = where
        path[begin:t + 1] = state
        state, where = gsrc[state][begin]
        t = begin - 1
    return path


def _prepare(score, allowed, blocks, params):
    """Comprobaciones comunes de los decodificadores. Devuelve (blocks, cost, emission, codes vacío).

    `blocks` vuelve como tupla: si llega un generador, la comprobación de abajo lo gastaría y el decodificador
    no vería ningún tramo (todo `X`, sin error).
    """
    blocks = tuple((int(start), int(stop)) for start, stop in blocks)
    unknown = sorted(set(params or {}) - set(DEFAULTS))
    if unknown:
        raise KeyError("parámetros desconocidos del decodificador: {}".format(unknown))
    merged = dict(DEFAULTS)
    merged.update(params or {})
    if any(float(value) < 0 for value in merged.values()):
        raise ValueError("los costes del decodificador no pueden ser negativos")
    if np.shape(score) != np.shape(allowed) or np.ndim(score) != 2 or np.shape(score)[1] != N_STATES:
        raise ValueError("la evidencia tiene que ser de forma (n, 3)")
    for start, stop in blocks:
        finite = np.isfinite(score[start:stop])
        if not finite.all():
            raise ValueError("la evidencia tiene {} valores no finitos en un tramo evaluado".format(
                int((~finite).sum())))
        if not allowed[start:stop].any(axis=1).all():
            raise ValueError("hay frames evaluados sin ningún estado permitido")
    return blocks, cost_matrix(merged), np.where(allowed, score, -np.inf), np.full(len(score), X, dtype=np.int8)


def decode(score, allowed, blocks, params=None):
    """Etiqueta por frame: 0 `H`, 1 `A`, 2 `D`, y 3 `X` fuera de los tramos evaluados.

    `score` y `allowed` son la evidencia combinada, de forma (n, 3). En cada frame evaluado la puntuación
    tiene que ser finita y tiene que haber al menos un estado permitido. `blocks` son los tramos (inicio,
    fin) con el fin sin incluir. `params` cambia los costes de `DEFAULTS`; una clave que no esté ahí o un
    coste negativo dan error, para que una errata no pase por un ajuste.
    """
    blocks, cost, emission, codes = _prepare(score, allowed, blocks, params)
    for start, stop in blocks:
        codes[start:stop] = viterbi(emission[start:stop], cost)
    return codes


def decode_min(score, allowed, blocks, params=None, min_live=MIN_LIVE, min_dead=MIN_DEAD):
    """Candidato (b): como `decode`, sin rachas de `H` o `A` de menos de `min_live` frames ni de `D` de menos
    de `min_dead`, salvo las que cortan el borde del tramo o lo prohibido (`viterbi_min`)."""
    if int(min_live) < 1 or int(min_dead) < 1:
        raise ValueError("las duraciones mínimas son de 1 frame o más")
    blocks, cost, emission, codes = _prepare(score, allowed, blocks, params)
    minimum = [0] * N_STATES
    minimum[H] = minimum[A] = int(min_live)
    minimum[D] = int(min_dead)
    for start, stop in blocks:
        codes[start:stop] = viterbi_min(emission[start:stop], cost, minimum)
    return codes


def runs(codes):
    """Rachas de un array de etiquetas: lista de (etiqueta, inicio, fin sin incluir)."""
    if len(codes) == 0:
        return []
    starts = np.flatnonzero(np.concatenate(([True], codes[1:] != codes[:-1])))
    stops = np.concatenate((starts[1:], [len(codes)]))
    return [(int(codes[a]), int(a), int(b)) for a, b in zip(starts, stops)]


def prune(codes, allowed, min_len):
    """Poda (c): cada racha de `H` o `A` de menos de `min_len` frames pasa al otro equipo si tiene al lado
    una racha de ese equipo y el otro equipo está permitido en toda ella. Una racha entre dos `D` no se toca,
    ni el `D`.

    Primero la más corta (si empatan, la primera en el tiempo). Al pasar al otro equipo se fusiona con sus
    vecinas, y la racha fusionada vuelve a la cola si sigue siendo corta. Así una sola pasada no «rebota»
    (una racha corta que cambia no hace cambiar a la siguiente). Termina porque cada cambio quita al menos
    una racha. Devuelve una copia.
    """
    out = np.array(codes, copy=True)
    pieces = runs(out)
    label = [p[0] for p in pieces]
    begin = [p[1] for p in pieces]
    end = [p[2] for p in pieces]
    left = list(range(-1, len(pieces) - 1))
    right = list(range(1, len(pieces) + 1))
    right[-1:] = [-1] if pieces else []
    alive = [True] * len(pieces)
    queue = [(end[k] - begin[k], begin[k], k) for k in range(len(pieces))
             if label[k] in (H, A) and end[k] - begin[k] < min_len]
    heapq.heapify(queue)
    while queue:
        length, start, k = heapq.heappop(queue)
        if not alive[k] or end[k] - begin[k] != length or begin[k] != start:
            continue  # entrada vieja: la racha ya se fusionó o cambió
        other = A if label[k] == H else H
        neighbours = [j for j in (left[k], right[k]) if j != -1 and label[j] == other]
        if not neighbours or not allowed[begin[k]:end[k], other].all():
            continue
        label[k] = other
        for j in neighbours:  # se fusiona con las vecinas del otro equipo
            alive[j] = False
            begin[k], end[k] = min(begin[k], begin[j]), max(end[k], end[j])
            if j == left[k]:
                left[k] = left[j]
                if left[j] != -1:
                    right[left[j]] = k
            else:
                right[k] = right[j]
                if right[j] != -1:
                    left[right[j]] = k
        if end[k] - begin[k] < min_len:
            heapq.heappush(queue, (end[k] - begin[k], begin[k], k))
    for k in range(len(pieces)):
        if alive[k]:
            out[begin[k]:end[k]] = label[k]
    return out


def decode_prune(score, allowed, blocks, params=None, min_len=PRUNE):
    """Candidato (c): el Viterbi de `decode` y después `prune` en cada tramo evaluado."""
    if int(min_len) < 0:
        raise ValueError("la poda es de 0 frames o más")
    blocks = tuple(blocks)  # se recorre dos veces: en `decode` y aquí
    codes = decode(score, allowed, blocks, params)
    for start, stop in blocks:
        codes[start:stop] = prune(codes[start:stop], allowed[start:stop], int(min_len))
    return codes


def cortas_a_d(codes, allowed, corte):
    """Idea 1.3: las posesiones cortas que acaban en una parada nuestra pasan a `D`. Devuelve una copia.

    Una candidata es una racha de `H` o `A` de menos de `corte` frames cuya racha anterior es del otro
    equipo (un cambio directo, sin `D` en medio) y cuya racha siguiente es `D`. La primera racha del tramo
    y la última nunca son candidatas: les falta uno de los dos lados.

    Las rachas se calculan una sola vez, antes de escribir nada, y los vecinos de cada candidata se leen
    siempre de esa lista: convertir una no cambia el vecindario de otra, aunque se vayan escribiendo dentro
    del mismo bucle. Con las condiciones de arriba dos candidatas nunca son contiguas ni están a dos rachas
    (a la segunda le quedaría un `D` por vecino de la izquierda), pero leer los vecinos de la lista deja la
    salida fijada e independiente del orden.

    Una candidata en cuyos frames `D` no esté permitido se queda como está: la evidencia manda sobre la
    regla, como en `prune`. En el partido eso pasa en el frame del saque de cada parte, donde
    `dead_ball.evidence` prohíbe `D`.
    """
    out = np.array(codes, copy=True)
    pieces = runs(out)
    for k in range(1, len(pieces) - 1):
        label, start, stop = pieces[k]
        before = pieces[k - 1][0]
        if label not in (H, A) or pieces[k + 1][0] != D:
            continue
        if before not in (H, A) or before == label:
            continue
        if stop - start >= corte:
            continue
        if not allowed[start:stop, D].all():
            continue
        out[start:stop] = D
    return out


def decode_cortas_a_d(score, allowed, blocks, params=None, corte=CORTE_CORTAS):
    """Candidato (idea 1.3): el Viterbi de `decode` y después `cortas_a_d` en cada tramo evaluado."""
    if int(corte) < 1:
        raise ValueError("el corte de las posesiones cortas es de 1 frame o más")
    blocks = tuple(blocks)  # se recorre dos veces: en `decode` y aquí
    codes = decode(score, allowed, blocks, params)
    for start, stop in blocks:
        codes[start:stop] = cortas_a_d(codes[start:stop], allowed[start:stop], int(corte))
    return codes
