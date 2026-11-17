"""Evidencia de equipo aprendida (apuesta B): regresión logística de `H` frente a `A`.

Es la apuesta B del plan (docs/PLAN_ENTREGA.md §3, «Ismael»; docs/investigacion_metodos.md §4.2), con las
decisiones de Ismael del 14/11 (docs/decisiones.md): una evidencia de equipo aprendida en la DFL que
compite con N1 (`candidates.evidence`) en el harness. Va en la entrega solo si gana con la regla de §5.8 al
control y a `main`, y con los criterios del `D` que se fijaron antes de medir (B5, 14/11).

- **Solo `H` frente a `A`.** La columna `D` va a cero, como en N1: el `D` es de `dead_state` y `dead_ball`.
- **Simétrica por construcción:** cada rasgo es «lo del local menos lo del visitante» y el modelo no tiene
  término independiente. Cambiar los equipos de lado cambia el signo del logit y nada más.
- **Sin identidad:** los rasgos no dependen del orden de los slots. Solo las velocidades de B2 suponen que
  un slot es el mismo objeto entre un frame y el siguiente (un tracklet); los saltos de más de `VEL_MAX`,
  que son cambios de slot, se descartan.
- **Por tramo evaluado:** ninguna ventana cruza el descanso. Fuera de los tramos, la puntuación es cero.
- **La puntuación** (`puntuacion_de`) depende del conjunto. En B1 y B2 es α·|z| a favor del equipo que el
  modelo da como poseedor (z es el logit) y cero para el otro y para `D`. En B4 es −α·|z| al que pierde, y
  B5 es B4 más el +1 de N1 donde se ve el balón. Va redondeada a `DECIMALES`. El logit se suma rasgo a
  rasgo, sin BLAS. El redondeo hace
  improbable, no imposible, que la entrega dependa del último bit de `np.exp` en otra máquina: la garantía
  es reproducir el CSV byte a byte en una máquina limpia.

Los coeficientes los escribe `validation/apuesta_b/entrenar.py` (numpy, sin azar) al final de este fichero.
Hay un juego por pliegue: el que se entrenó sin cada partido de la DFL, para que el harness puntúe cada
partido con un modelo que no lo vio (`fuera`), y el de los 7 partidos (`fuera=None`), que es el de la
entrega.

Interfaz: `evidence_b1(trk)` … `evidence_b5(trk)` devuelven `(score, allowed)`; ver possession/tracking.py.
Este módulo no importa ninguna otra pieza: el «más cercano» de B5 es una copia propia (`equipo_mas_cercano`),
para que B5 no cambie si cambia `candidates.py` y para que no haya importaciones circulares.
"""

import numpy as np

from possession.tracking import A, H, no_evidence

# -- rasgos (fijados en docs/decisiones.md el 14/11, antes de medir; sin ajustar) -----------------------
# Ninguna de estas constantes se ajustó: se escribieron antes de medir y no se tocaron al ver resultados.

SIGMAS = (1.0, 2.5, 6.0)  # m: anchura de los núcleos gaussianos de distancia al balón
TOPE = 15.0  # m: tope de la distancia del más cercano de cada equipo
VENTANAS_BALON = (1, 13, 51, 151)  # frames: ventanas centradas de los rasgos del balón
VEL_MAX = 12.0  # m/s: una velocidad mayor es un cambio de slot, no un jugador
VENTANA_CERCA = 25  # frames: «sin balón cerca» es ningún frame con balón en ±12
DECIMALES = 6
# B3, B4 y B5 (14/11) usan los rasgos y los pesos de B2; solo cambia cómo se convierte el logit en puntuación.
# B6, B7 y B8 (15/11, la ronda de reentrenamiento) puntúan como B5 con sus propios pesos: B6 sin las ventanas
# de 151 frames, B7 con los rasgos de B2 entrenados con peso cerca de los cambios y B8 con el evento de toque.
# B9 (15/11, posesiones cortas; docs/decisiones.md) puntúa como B5 con sus pesos: los rasgos de B2 más la
# dirección en que se mueve el balón.
CONJUNTOS = ("b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9")
COMO_B5 = ("b5", "b6", "b7", "b8", "b9")
RASGOS_DE = {"b1": "b1", "b2": "b2", "b3": "b2", "b4": "b2", "b5": "b2", "b6": "b6", "b7": "b2", "b8": "b8",
             "b9": "b9"}
# El evento de toque de B8 (anexo A.4 de la revisión externa; docs/decisiones.md, 15/11, antes de medir).
TOQUE_CERCA, TOQUE_LEJOS = 12, 25  # frames: velocidad del balón de t+12 a t+25 frente a la de t−25 a t−12
TOQUE_UMBRAL = 3.0  # m/s: cambio de velocidad mínimo (el umbral de toque del experimento 0)
TOQUE_MAXIMO = 12  # frames: el evento es el máximo del cambio en ±12
TOQUE_RADIO = 3.0  # m: el jugador más cercano tiene que estar a esta distancia o menos (el radio de ELASTIC)
VENTANAS_TOQUE = (13, 51)  # frames: ventanas centradas del rasgo
# La dirección del balón de B9 (validation/posesiones_cortas/BITACORA.md §6). Fijada antes de medir B9, pero la
# ventana y el umbral salen de un sondeo y de una puerta en los mismos 7 partidos de la DFL (se probaron 13,
# 25 y 51 frames): no son «sin ajustar» como las de arriba.
DIRECCION_MITAD = 6  # frames: la velocidad del balón se mide de t−6 a t+6 (13 frames)
DIRECCION_UMBRAL = 2.0  # m/s: por encima, el balón va hacia la portería del visitante (+1); por debajo de −2, al revés
VENTANAS_DIRECCION = (1, 13, 51)  # frames: ventanas centradas del rasgo
N1_PUNTOS = 1.0  # el +1 de N1 que suma B5 (candidates.NEAREST_SCORE el 14/11), escrito aquí para que no cambie con él
BLOQUE_CERCANO = 20000  # frames por bloque al buscar el más cercano (candidates.CHUNK el 14/11)
BASE_BALON = ["signo del más cercano"] + ["núcleo {} m".format(s) for s in SIGMAS] + ["distancia del más cercano"]
NOMBRES = {
    "b1": ["{}, ventana {}".format(r, v) for r in BASE_BALON for v in VENTANAS_BALON],
}
NOMBRES["b2"] = NOMBRES["b1"] + [
    "juego en la dirección de ataque",
    "balón en la dirección de ataque, ventana 1",
    "balón en la dirección de ataque, ventana 51",
    "velocidad en la dirección de ataque, ventana 25",
    "velocidad en la dirección de ataque, ventana 101",
    "dispersión, ventana 51",
    "juego en la dirección de ataque, sin balón cerca",
    "velocidad en la dirección de ataque, ventana 25, sin balón cerca",
    "velocidad en la dirección de ataque, ventana 101, sin balón cerca",
    "dispersión, ventana 51, sin balón cerca",
]
NOMBRES["b3"] = NOMBRES["b4"] = NOMBRES["b5"] = NOMBRES["b7"] = NOMBRES["b2"]
NOMBRES["b6"] = [nombre for nombre in NOMBRES["b2"] if not nombre.endswith("ventana 151")]
NOMBRES["b8"] = NOMBRES["b2"] + ["evento de toque, ventana {}".format(v) for v in VENTANAS_TOQUE]
NOMBRES["b9"] = NOMBRES["b2"] + ["dirección del balón, ventana {}".format(v) for v in VENTANAS_DIRECCION]


def media_centrada(valores, ancho):
    """Media centrada de `ancho` frames (impar), recortada en los extremos. Los NaN cuentan como cero."""
    v = np.where(np.isnan(valores), 0.0, np.asarray(valores, dtype=np.float64))
    if ancho == 1:
        return v
    acumulada = np.concatenate(([0.0], np.cumsum(v)))
    indice = np.arange(len(v))
    bajo = np.maximum(0, indice - ancho // 2)
    alto = np.minimum(len(v), indice + ancho // 2 + 1)
    return (acumulada[alto] - acumulada[bajo]) / (alto - bajo)


def _sin_nan(valores):
    return np.where(np.isfinite(valores), valores, 0.0)


def _por_equipo(px, py, columnas):
    """Posiciones de un equipo en float64 y la máscara de las que existen."""
    x = px[:, columnas].astype(np.float64)
    y = py[:, columnas].astype(np.float64)
    return x, y, np.isfinite(x) & np.isfinite(y)


def _media_filas(valores, hay):
    """Media por fila de lo que hay; NaN si no hay nada."""
    cuenta = hay.sum(axis=1)
    suma = np.where(hay, valores, 0.0).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cuenta > 0, suma / np.maximum(cuenta, 1), np.nan)


def _rasgos_balon(bx, by, equipos):
    """Los 5 rasgos base del balón (local menos visitante), a cero sin balón."""
    visible = np.isfinite(bx) & np.isfinite(by)
    cerca, nucleos = [], []
    for x, y, hay in equipos:
        d2 = (x - bx[:, None]) ** 2 + (y - by[:, None]) ** 2
        d2 = np.where(hay & visible[:, None], d2, np.inf)
        minimo = d2.min(axis=1) if d2.shape[1] else np.full(len(bx), np.inf)
        cerca.append(np.sqrt(minimo))
        nucleos.append([np.exp(-d2 / (2.0 * s * s)).sum(axis=1) for s in SIGMAS])
    with np.errstate(invalid="ignore"):
        signo = _sin_nan(np.sign(cerca[1] - cerca[0]))
    base = [signo] + [nucleos[0][i] - nucleos[1][i] for i in range(len(SIGMAS))]
    base.append(np.minimum(cerca[1], TOPE) - np.minimum(cerca[0], TOPE))
    return [np.where(visible, r, 0.0) for r in base], visible


def _velocidad_x(x, y, fps):
    """Velocidad en x de cada slot (diferencia centrada), NaN si falta o si pasa de VEL_MAX."""
    vx = np.full(x.shape, np.nan)
    if len(x) < 3:
        return vx
    dx = (x[2:] - x[:-2]) * fps / 2.0
    dy = (y[2:] - y[:-2]) * fps / 2.0
    with np.errstate(invalid="ignore"):
        rapido = np.hypot(dx, dy) > VEL_MAX
    vx[1:-1] = np.where(rapido, np.nan, dx)
    return vx


def _dispersion(x, y, hay):
    """Raíz de la varianza en x más la varianza en y del equipo; NaN con menos de dos slots."""
    mx, my = _media_filas(x, hay), _media_filas(y, hay)
    var = _media_filas((x - mx[:, None]) ** 2 + (y - my[:, None]) ** 2, hay)
    return np.where(hay.sum(axis=1) >= 2, np.sqrt(var), np.nan)


def _rasgos_forma(bx, by, visible, equipos, largo, fps):
    """Los 10 rasgos de los jugadores de B2, con la dirección de ataque del local en el tramo."""
    (xh, yh, hh), (xa, ya, ha) = equipos
    media_h = np.where(hh, xh, 0.0).sum() / max(int(hh.sum()), 1)
    media_a = np.where(ha, xa, 0.0).sum() / max(int(ha.sum()), 1)
    # El local ataca hacia donde está, en media, el visitante. Sin uno de los dos, no hay dirección.
    direccion = float(np.sign(media_a - media_h)) if hh.any() and ha.any() else 0.0
    mitad = largo / 2.0
    juego = direccion * _sin_nan(_media_filas(xh, hh) + _media_filas(xa, ha) - largo) / mitad
    balon = np.where(visible, direccion * (np.where(visible, bx, mitad) - mitad) / mitad, 0.0)
    vh, va = _velocidad_x(xh, yh, fps), _velocidad_x(xa, ya, fps)
    vel = direccion * (_sin_nan(_media_filas(vh, np.isfinite(vh))) + _sin_nan(_media_filas(va, np.isfinite(va))))
    dispersion = _sin_nan(_dispersion(xh, yh, hh) - _dispersion(xa, ya, ha))
    sin_balon = media_centrada(visible.astype(np.float64), VENTANA_CERCA) == 0.0
    forma = [juego, media_centrada(balon, 1), media_centrada(balon, 51), media_centrada(vel, 25),
             media_centrada(vel, 101), media_centrada(dispersion, 51)]
    return forma + [np.where(sin_balon, r, 0.0) for r in (forma[0], forma[3], forma[4], forma[5])]


def cambio_de_velocidad(bx, by, fps):
    """Cambio de velocidad del balón en cada frame de un tramo (m/s), a la escala del suavizado del ATD.

    La norma de la diferencia entre la velocidad media de t+12 a t+25 y la de t−25 a t−12 (anexo A.4 de la
    revisión externa). NaN si falta el balón en alguno de esos cuatro frames o si alguno cae fuera del tramo.
    """
    n = len(bx)
    salida = np.full(n, np.nan)
    if n <= 2 * TOQUE_LEJOS:
        return salida
    t = np.arange(TOQUE_LEJOS, n - TOQUE_LEJOS)
    escala = fps / float(TOQUE_LEJOS - TOQUE_CERCA)
    antes_x = (bx[t - TOQUE_CERCA] - bx[t - TOQUE_LEJOS]) * escala
    antes_y = (by[t - TOQUE_CERCA] - by[t - TOQUE_LEJOS]) * escala
    despues_x = (bx[t + TOQUE_LEJOS] - bx[t + TOQUE_CERCA]) * escala
    despues_y = (by[t + TOQUE_LEJOS] - by[t + TOQUE_CERCA]) * escala
    salida[t] = np.hypot(despues_x - antes_x, despues_y - antes_y)
    return salida


def eventos_de_toque(bx, by, equipos, fps):
    """Signo del evento de toque en cada frame de un tramo: +1 local, −1 visitante, 0 sin evento o sin nadie.

    Evento: un frame con un cambio de velocidad (`cambio_de_velocidad`) de `TOQUE_UMBRAL` o más que es el
    máximo en ±`TOQUE_MAXIMO` frames; si hay empate, cuenta el primero. Su signo es el equipo del jugador más
    cercano al balón en ese frame si está a `TOQUE_RADIO` o menos.
    """
    cambio = cambio_de_velocidad(bx, by, fps)
    valor = np.where(np.isnan(cambio), -np.inf, cambio)
    n = len(valor)
    es_evento = valor >= TOQUE_UMBRAL
    for k in range(1, TOQUE_MAXIMO + 1):
        anterior = np.concatenate((np.full(k, -np.inf), valor[:-k])) if k < n else np.full(n, -np.inf)
        siguiente = np.concatenate((valor[k:], np.full(k, -np.inf))) if k < n else np.full(n, -np.inf)
        es_evento &= (valor > anterior) & (valor >= siguiente)
    signo = np.zeros(n)
    t = np.flatnonzero(es_evento)
    if not len(t):
        return signo
    cercanos = []
    for x, y, hay in equipos:
        d2 = (x[t] - bx[t, None]) ** 2 + (y[t] - by[t, None]) ** 2
        d2 = np.where(hay[t], d2, np.inf)
        cercanos.append(d2.min(axis=1) if d2.shape[1] else np.full(len(t), np.inf))
    local, visitante = cercanos
    radio = TOQUE_RADIO * TOQUE_RADIO
    signo[t] = np.where((local <= visitante) & (local <= radio), 1.0,
                        np.where((visitante < local) & (visitante <= radio), -1.0, 0.0))
    return signo


def direccion_del_balon(bx, equipos, fps):
    """Hacia qué portería va el balón en cada frame de un tramo: +1, −1 o 0 (B9, 15/11).

    La velocidad del balón en x de t−`DIRECCION_MITAD` a t+`DIRECCION_MITAD`, con el signo de la dirección de
    ataque del local (la de `_rasgos_forma`: el local ataca hacia donde está, en media, el visitante). +1 si
    pasa de `DIRECCION_UMBRAL` (va hacia la portería del visitante), −1 si baja de −`DIRECCION_UMBRAL`, y 0 si
    no, si falta el balón en alguno de los dos extremos, si alguno cae fuera del tramo o si no hay dirección.
    Una velocidad medida en 13 frames aguanta el suavizado de unos 25 del balón del ATD.
    """
    (xh, _, hh), (xa, _, ha) = equipos
    n = len(bx)
    salida = np.zeros(n)
    if not (hh.any() and ha.any()) or n <= 2 * DIRECCION_MITAD:
        return salida
    media_h = np.where(hh, xh, 0.0).sum() / int(hh.sum())
    media_a = np.where(ha, xa, 0.0).sum() / int(ha.sum())
    direccion = float(np.sign(media_a - media_h))
    m = DIRECCION_MITAD
    with np.errstate(invalid="ignore"):
        v = (bx[2 * m:] - bx[:-2 * m]) * fps / (2.0 * m) * direccion
        salida[m:n - m] = np.where(v > DIRECCION_UMBRAL, 1.0, np.where(v < -DIRECCION_UMBRAL, -1.0, 0.0))
    return salida


def rasgos(trk, conjunto):
    """Matriz (n, k) de rasgos del conjunto (`NOMBRES[conjunto]`), en float64, a cero fuera de los tramos."""
    if conjunto not in CONJUNTOS:
        raise ValueError("conjunto desconocido: {} (valen: {})".format(conjunto, CONJUNTOS))
    n = len(trk.bx)
    salida = np.zeros((n, len(NOMBRES[conjunto])))
    team = np.asarray(trk.team)
    columnas = [np.flatnonzero(team == equipo) for equipo in (H, A)]
    tipo = RASGOS_DE[conjunto]
    for inicio, fin in trk.blocks:
        bx = np.asarray(trk.bx[inicio:fin], dtype=np.float64)
        by = np.asarray(trk.by[inicio:fin], dtype=np.float64)
        equipos = [_por_equipo(trk.px[inicio:fin], trk.py[inicio:fin], c) for c in columnas]
        base, visible = _rasgos_balon(bx, by, equipos)
        lista = [media_centrada(r, v) for r in base for v in VENTANAS_BALON]
        if tipo in ("b2", "b6", "b8", "b9"):
            lista += _rasgos_forma(bx, by, visible, equipos, float(trk.pitch[0]), float(trk.fps))
        if tipo == "b6":
            lista = [r for r, nombre in zip(lista, NOMBRES["b2"]) if nombre in NOMBRES["b6"]]
        if tipo == "b8":
            signo = eventos_de_toque(bx, by, equipos, float(trk.fps))
            lista += [media_centrada(signo, v) for v in VENTANAS_TOQUE]
        if tipo == "b9":
            hacia = direccion_del_balon(bx, equipos, float(trk.fps))
            lista += [media_centrada(hacia, v) for v in VENTANAS_DIRECCION]
        salida[inicio:fin] = np.column_stack(lista)
    return salida


def logit(matriz, pesos):
    """z = Σ peso·rasgo, sumando en el orden de los rasgos (sin BLAS, para que no dependa de la máquina)."""
    if matriz.shape[1] != len(pesos):
        raise ValueError("{} rasgos y {} pesos".format(matriz.shape[1], len(pesos)))
    z = np.zeros(len(matriz))
    for j, peso in enumerate(pesos):
        z = z + float(peso) * matriz[:, j]
    return z


def puntuacion(z, alfa):
    """(score, allowed) a partir del logit: α·z a favor del poseedor, cero para el otro y para `D`."""
    score, allowed = no_evidence(len(z))
    score[:, H] = np.round(alfa * np.maximum(z, 0.0), DECIMALES)
    score[:, A] = np.round(alfa * np.maximum(-z, 0.0), DECIMALES)
    return score, allowed


def puntuacion_de(conjunto, z, visible, alfa, cercano=None):
    """(score, allowed) de un conjunto a partir del logit `z` y de dónde se ve el balón (`visible`).

    - b1 y b2: `puntuacion` (α·|z| a favor del poseedor).
    - b3: lo mismo, pero solo donde se ve el balón en ese frame (donde N1 opina); cero en el resto, para
      que no pese en las paradas.
    - b4: −α·|z| para el equipo que no da el modelo y cero para el que da y para `D`. La diferencia
      `H` − `A` es la de b2, y el margen del ganador sobre `D` es siempre cero: el `D` lo deciden las piezas
      de `D`.
    - b5: b4 más N1 (`N1_PUNTOS` al equipo de `cercano`, el equipo del jugador más cercano al balón de
      `equipo_mas_cercano`, −1 donde nadie). Frente a `D` empuja como N1.
    - b6, b7, b8 y b9: como b5, con su propio logit (15/11).
    """
    if conjunto in COMO_B5[1:]:
        conjunto = "b5"
    if conjunto in ("b1", "b2"):
        return puntuacion(z, alfa)
    if conjunto == "b3":
        return puntuacion(np.where(visible, z, 0.0), alfa)
    if conjunto == "b4":
        score, allowed = no_evidence(len(z))
        score[:, H] = -np.round(alfa * np.maximum(-z, 0.0), DECIMALES)
        score[:, A] = -np.round(alfa * np.maximum(z, 0.0), DECIMALES)
        return score + 0.0, allowed  # + 0.0: sin ceros con signo
    if conjunto == "b5":
        if cercano is None:
            raise ValueError("b5 necesita `cercano`, el equipo del jugador más cercano al balón")
        score, allowed = puntuacion_de("b4", z, visible, alfa)
        score[cercano == H, H] += N1_PUNTOS
        score[cercano == A, A] += N1_PUNTOS
        return score, allowed
    raise ValueError("conjunto desconocido: {} (valen: {})".format(conjunto, CONJUNTOS))


def equipo_mas_cercano(trk):
    """Equipo del slot más cercano al balón por frame: 0, 1, o -1 si no hay balón o no hay jugadores.

    Copia de `candidates.nearest_team` del 14/11 (N1, lo que hace starter/baseline.py): con dos slots a la
    misma distancia gana el de índice más bajo. Es la que usó el entrenamiento de B5.
    """
    out = np.full(len(trk.bx), -1, dtype=np.int8)
    seen = np.flatnonzero(~np.isnan(trk.bx) & ~np.isnan(trk.by))
    team = np.asarray(trk.team)
    for start in range(0, len(seen), BLOQUE_CERCANO):
        idx = seen[start:start + BLOQUE_CERCANO]
        dx = trk.px[idx].astype(np.float64) - trk.bx[idx, None]
        dy = trk.py[idx].astype(np.float64) - trk.by[idx, None]
        d2 = dx * dx + dy * dy
        d2 = np.where(np.isnan(d2), np.inf, d2)
        best = np.argmin(d2, axis=1)
        found = np.isfinite(d2[np.arange(len(idx)), best])
        out[idx[found]] = team[best[found]]
    return out


def balon_visible(trk):
    return np.isfinite(np.asarray(trk.bx, dtype=np.float64)) & np.isfinite(np.asarray(trk.by, dtype=np.float64))


def coeficientes(conjunto, fuera=None):
    """{"alfa", "pesos"} del conjunto: los de los 7 partidos, o los del pliegue sin el partido `fuera`."""
    clave = "todos" if fuera is None else fuera
    juego = COEFICIENTES.get(conjunto, {}).get(clave)
    if juego is None:
        raise KeyError("no hay coeficientes de «{}» para «{}»: hay que ejecutar validation/apuesta_b/entrenar.py "
                       "(B9: validation/posesiones_cortas/entrenar_b9.py)".format(conjunto, clave))
    return juego


def _evidencia(trk, conjunto, fuera):
    juego = coeficientes(conjunto, fuera)
    z = logit(rasgos(trk, conjunto), juego["pesos"])
    cercano = None
    if conjunto in COMO_B5:
        # Como N1, pero a cero fuera de los tramos, como el resto de este módulo (ahí se escribe `X`).
        todos = equipo_mas_cercano(trk)
        cercano = np.full(len(trk.bx), -1, dtype=np.int8)
        for inicio, fin in trk.blocks:
            cercano[inicio:fin] = todos[inicio:fin]
    return puntuacion_de(conjunto, z, balon_visible(trk), juego["alfa"], cercano)


def evidence_b1(trk, fuera=None):
    """B1: proximidad al balón aprendida. `fuera`: el partido de la DFL que el harness está puntuando."""
    return _evidencia(trk, "b1", fuera)


def evidence_b2(trk, fuera=None):
    """B2: B1 más rasgos de los jugadores, que opinan también sin balón."""
    return _evidencia(trk, "b2", fuera)


def evidence_b3(trk, fuera=None):
    """B3: B2 con puerta de balón. Solo opina donde se ve el balón en ese frame (14/11)."""
    return _evidencia(trk, "b3", fuera)


def evidence_b4(trk, fuera=None):
    """B4: B2 que castiga al perdedor. El ganador y `D` a cero (14/11)."""
    return _evidencia(trk, "b4", fuera)


def evidence_b5(trk, fuera=None):
    """B5: B4 más el +1 de N1 donde se ve el balón (14/11)."""
    return _evidencia(trk, "b5", fuera)


def evidence_b6(trk, fuera=None):
    """B6: B5 sin las ventanas de 151 frames, con sus pesos (15/11, ronda de reentrenamiento)."""
    return _evidencia(trk, "b6", fuera)


def evidence_b7(trk, fuera=None):
    """B7: B5 con los pesos entrenados con peso 5 a ±2 s de un cambio de equipo (15/11)."""
    return _evidencia(trk, "b7", fuera)


def evidence_b8(trk, fuera=None):
    """B8: B5 con el evento de toque a la escala del suavizado, con sus pesos (15/11)."""
    return _evidencia(trk, "b8", fuera)


def evidence_b9(trk, fuera=None):
    """B9: B5 con la dirección en que se mueve el balón, con sus pesos (15/11, posesiones cortas)."""
    return _evidencia(trk, "b9", fuera)


def evidence_b11(trk, fuera=None):
    """B11: convolucional temporal sobre canales por frame, puntuada como B5 (17/11; possession/secuencia.py).

    Apagada: no está en `pipeline.PIECES`. Se importa aquí dentro para que B1–B9 no dependan de ese módulo.
    """
    from possession import secuencia
    return secuencia.evidencia(trk, "b11", fuera)


def evidence_b12(trk, fuera=None):
    """B12: GRU bidireccional sobre los mismos canales a 5 Hz, puntuada como B5 (17/11; possession/secuencia.py).

    Apagada, como B11.
    """
    from possession import secuencia
    return secuencia.evidencia(trk, "b12", fuera)


def evidence_b13(trk, fuera=None):
    """B13: red sobre las trayectorias de jugadores y balón, puntuada como B5 (17/11; possession/trayectorias.py).

    Apagada, como B11 y B12.
    """
    from possession import trayectorias
    return trayectorias.evidencia(trk, "b13", fuera)


def evidence_b14(trk, fuera=None):
    """B14: la red de trayectorias con rasgos de control, atención conjunta y dominio aleatorizado como el ATD
    (17/11; possession/trayectorias2.py). Apagada."""
    from possession import trayectorias2
    return trayectorias2.evidencia(trk, "b14", fuera)


def evidence_b15(trk, fuera=None):
    """B15: la red de B14 entrenada con la etiqueta de control en todos los frames vivos (17/11). Apagada."""
    from possession import trayectorias2
    return trayectorias2.evidencia(trk, "b15", fuera, ruta=trayectorias2.PESOS_B15)


# -- coeficientes: los escribe validation/apuesta_b/entrenar.py; no se editan a mano --------------------
# >>> COEFICIENTES
# Los escribe validation/apuesta_b/entrenar.py. «todos»: los 7 partidos de la DFL (la entrega); cada
# partido: el pliegue entrenado y escalado sin él (el harness, con «dejar_fuera»).
COEFICIENTES = {
    "b1": {
        "todos": {"alfa": 2.0, "pesos": (
            0.015849, 0.0396237, -0.118552, 0.844238, -0.0370134,
            0.96778, 1.62156, 3.26677, 0.105757, -0.737179,
            1.13013, 2.74527, -0.0178349, 0.548347, -1.13124,
            -2.2605, -0.0240528, 0.0037239, -0.082326, 0.411018,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.00844998, 0.0310774, -0.113953, 1.15379, -0.0325204,
            0.985406, 1.47035, 2.67844, 0.0592573, -0.663211,
            1.11673, 2.84984, 0.0229323, 0.436025, -0.984654,
            -2.36922, -0.0265686, 0.0136749, -0.0930549, 0.395963,
        )},
        "J03WN1": {"alfa": 2.0, "pesos": (
            0.0131502, 0.0521605, -0.0976352, 0.450504, -0.0075356,
            0.90215, 1.70962, 4.14516, 0.107093, -0.752027,
            1.01543, 3.14196, 0.0356043, 0.496342, -1.06615,
            -2.44771, -0.0269637, 0.00454526, -0.0790139, 0.416897,
        )},
        "J03WOH": {"alfa": 2.0, "pesos": (
            0.00878288, 0.0614111, -0.138145, 1.03055, -0.0428085,
            0.984227, 1.62408, 2.92447, 0.0913831, -0.734043,
            1.11807, 2.81329, 0.0101609, 0.482388, -1.08748,
            -2.36218, -0.0273109, 0.00970331, -0.0847348, 0.397339,
        )},
        "J03WOY": {"alfa": 2.0, "pesos": (
            0.0157976, 0.0457948, -0.138855, 0.747598, -0.0583174,
            0.985892, 1.71437, 3.94571, 0.0863745, -0.710772,
            1.0457, 2.32384, -0.0459378, 0.618217, -1.20773,
            -2.16476, -0.0202434, -0.00781757, -0.0689492, 0.432034,
        )},
        "J03WPY": {"alfa": 2.0, "pesos": (
            0.0260962, 0.0244347, -0.0947872, 0.744362, -0.0390545,
            0.953369, 1.63629, 3.30893, 0.138883, -0.782632,
            1.28075, 2.46505, -0.0618356, 0.608351, -1.25878,
            -2.02164, -0.0274402, 0.0116027, -0.0970543, 0.421578,
        )},
        "J03WQQ": {"alfa": 2.0, "pesos": (
            0.00623527, 0.0538441, -0.1316, 0.818469, -0.0386886,
            0.983016, 1.74966, 2.68606, 0.091564, -0.712675,
            1.08935, 2.97413, -0.0156813, 0.555053, -1.0981,
            -2.2957, -0.0108921, -0.0147692, -0.0805567, 0.42094,
        )},
        "J03WR9": {"alfa": 2.0, "pesos": (
            0.0316531, 0.0108566, -0.121972, 0.936823, -0.0262062,
            0.963132, 1.45734, 3.33704, 0.122235, -0.745133,
            1.2221, 2.63997, -0.0422083, 0.606997, -1.21307,
            -2.15841, -0.0271379, 0.00538057, -0.0677795, 0.390551,
        )},
    },
    "b2": {
        "todos": {"alfa": 2.0, "pesos": (
            0.0375125, 0.0020608, -0.034728, 1.44394, -0.0946537,
            1.13776, 1.04194, 2.63023, 0.089502, -0.670045,
            1.52721, 0.707258, 0.0652266, 0.307699, -0.81681,
            -0.324124, -0.0252869, -0.0192872, -0.107059, 0.0476549,
            1.20284, 0.274543, -4.15035, 0.451477, -0.0199163,
            0.264126, -4.44177, -0.29112, 0.15269, 0.330578,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.0306064, -0.0132135, -0.0363003, 1.8232, -0.0641295,
            1.10994, 0.936099, 1.90953, 0.0458039, -0.585642,
            1.53234, 0.804738, 0.106398, 0.199702, -0.673065,
            -0.444768, -0.0376022, 0.00247349, -0.120856, 0.0288019,
            1.27987, 0.206883, -4.10402, 0.455597, -0.0203781,
            0.260675, -4.17706, -0.309728, 0.16441, 0.307329,
        )},
        "J03WN1": {"alfa": 2.0, "pesos": (
            0.0391198, 0.0187248, -0.0289436, 0.958647, -0.0799917,
            1.1096, 1.11257, 3.72668, 0.0268155, -0.599567,
            1.41384, 1.00614, 0.176867, 0.160735, -0.722547,
            -0.529223, -0.0218076, -0.0299679, -0.0966192, 0.0442844,
            0.989736, 0.378259, -4.3254, 0.431773, -0.00576854,
            0.287203, -4.70049, -0.243125, 0.115645, 0.361429,
        )},
        "J03WOH": {"alfa": 2.0, "pesos": (
            0.0328053, 0.018972, -0.0417908, 1.67521, -0.100255,
            1.16293, 1.00428, 2.08624, 0.0589483, -0.644623,
            1.54583, 0.833648, -0.0108504, 0.367805, -0.839527,
            -0.352537, -0.0198761, -0.023367, -0.111479, 0.0375936,
            1.27324, 0.259194, -4.07429, 0.43984, -0.00712229,
            0.26294, -4.28517, -0.321361, 0.186251, 0.320223,
        )},
        "J03WOY": {"alfa": 2.0, "pesos": (
            0.0402686, 0.000490481, -0.0330194, 1.30555, -0.108522,
            1.14414, 1.06745, 3.25309, 0.0834922, -0.658029,
            1.3938, 0.555298, 0.020055, 0.400167, -0.903382,
            -0.270938, -0.0320217, -0.0160338, -0.0903902, 0.0617012,
            1.2415, 0.243983, -4.03703, 0.458586, -0.0463463,
            0.252876, -4.55296, -0.220501, 0.0775531, 0.342635,
        )},
        "J03WPY": {"alfa": 2.0, "pesos": (
            0.0418441, -0.00453044, -0.0369182, 1.34945, -0.10494,
            1.12952, 1.04305, 3.06005, 0.129654, -0.716623,
            1.73741, 0.250132, 0.0259182, 0.372111, -0.941517,
            -0.051487, -0.0267058, -0.0158839, -0.124915, 0.0476765,
            1.20488, 0.303368, -4.24285, 0.477104, -0.04729,
            0.267426, -4.53381, -0.319138, 0.192047, 0.320392,
        )},
        "J03WQQ": {"alfa": 2.0, "pesos": (
            0.0230818, 0.0245812, -0.0307349, 1.45329, -0.101606,
            1.14875, 1.21742, 1.93066, 0.0947507, -0.678838,
            1.40736, 0.898022, 0.0978462, 0.278064, -0.7785,
            -0.308609, -0.0119348, -0.0369917, -0.101012, 0.0557967,
            1.22534, 0.270801, -4.16733, 0.439929, 0.00965233,
            0.258966, -4.2923, -0.344712, 0.197429, 0.32487,
        )},
        "J03WR9": {"alfa": 2.0, "pesos": (
            0.0529509, -0.0286386, -0.0377898, 1.50243, -0.0814839,
            1.12967, 0.951319, 2.59616, 0.12796, -0.716306,
            1.60295, 0.615601, 0.0597802, 0.331595, -0.826551,
            -0.313793, -0.0248903, -0.0194702, -0.0986982, 0.0570066,
            1.15001, 0.226786, -4.0326, 0.453503, -0.018045,
            0.264411, -4.51977, -0.279009, 0.137234, 0.336248,
        )},
    },
    "b3": {
        "todos": {"alfa": 4.0, "pesos": (
            0.0375125, 0.0020608, -0.034728, 1.44394, -0.0946537,
            1.13776, 1.04194, 2.63023, 0.089502, -0.670045,
            1.52721, 0.707258, 0.0652266, 0.307699, -0.81681,
            -0.324124, -0.0252869, -0.0192872, -0.107059, 0.0476549,
            1.20284, 0.274543, -4.15035, 0.451477, -0.0199163,
            0.264126, -4.44177, -0.29112, 0.15269, 0.330578,
        )},
        "J03WMX": {"alfa": 4.0, "pesos": (
            0.0306064, -0.0132135, -0.0363003, 1.8232, -0.0641295,
            1.10994, 0.936099, 1.90953, 0.0458039, -0.585642,
            1.53234, 0.804738, 0.106398, 0.199702, -0.673065,
            -0.444768, -0.0376022, 0.00247349, -0.120856, 0.0288019,
            1.27987, 0.206883, -4.10402, 0.455597, -0.0203781,
            0.260675, -4.17706, -0.309728, 0.16441, 0.307329,
        )},
        "J03WN1": {"alfa": 4.0, "pesos": (
            0.0391198, 0.0187248, -0.0289436, 0.958647, -0.0799917,
            1.1096, 1.11257, 3.72668, 0.0268155, -0.599567,
            1.41384, 1.00614, 0.176867, 0.160735, -0.722547,
            -0.529223, -0.0218076, -0.0299679, -0.0966192, 0.0442844,
            0.989736, 0.378259, -4.3254, 0.431773, -0.00576854,
            0.287203, -4.70049, -0.243125, 0.115645, 0.361429,
        )},
        "J03WOH": {"alfa": 4.0, "pesos": (
            0.0328053, 0.018972, -0.0417908, 1.67521, -0.100255,
            1.16293, 1.00428, 2.08624, 0.0589483, -0.644623,
            1.54583, 0.833648, -0.0108504, 0.367805, -0.839527,
            -0.352537, -0.0198761, -0.023367, -0.111479, 0.0375936,
            1.27324, 0.259194, -4.07429, 0.43984, -0.00712229,
            0.26294, -4.28517, -0.321361, 0.186251, 0.320223,
        )},
        "J03WOY": {"alfa": 4.0, "pesos": (
            0.0402686, 0.000490481, -0.0330194, 1.30555, -0.108522,
            1.14414, 1.06745, 3.25309, 0.0834922, -0.658029,
            1.3938, 0.555298, 0.020055, 0.400167, -0.903382,
            -0.270938, -0.0320217, -0.0160338, -0.0903902, 0.0617012,
            1.2415, 0.243983, -4.03703, 0.458586, -0.0463463,
            0.252876, -4.55296, -0.220501, 0.0775531, 0.342635,
        )},
        "J03WPY": {"alfa": 8.0, "pesos": (
            0.0418441, -0.00453044, -0.0369182, 1.34945, -0.10494,
            1.12952, 1.04305, 3.06005, 0.129654, -0.716623,
            1.73741, 0.250132, 0.0259182, 0.372111, -0.941517,
            -0.051487, -0.0267058, -0.0158839, -0.124915, 0.0476765,
            1.20488, 0.303368, -4.24285, 0.477104, -0.04729,
            0.267426, -4.53381, -0.319138, 0.192047, 0.320392,
        )},
        "J03WQQ": {"alfa": 8.0, "pesos": (
            0.0230818, 0.0245812, -0.0307349, 1.45329, -0.101606,
            1.14875, 1.21742, 1.93066, 0.0947507, -0.678838,
            1.40736, 0.898022, 0.0978462, 0.278064, -0.7785,
            -0.308609, -0.0119348, -0.0369917, -0.101012, 0.0557967,
            1.22534, 0.270801, -4.16733, 0.439929, 0.00965233,
            0.258966, -4.2923, -0.344712, 0.197429, 0.32487,
        )},
        "J03WR9": {"alfa": 2.0, "pesos": (
            0.0529509, -0.0286386, -0.0377898, 1.50243, -0.0814839,
            1.12967, 0.951319, 2.59616, 0.12796, -0.716306,
            1.60295, 0.615601, 0.0597802, 0.331595, -0.826551,
            -0.313793, -0.0248903, -0.0194702, -0.0986982, 0.0570066,
            1.15001, 0.226786, -4.0326, 0.453503, -0.018045,
            0.264411, -4.51977, -0.279009, 0.137234, 0.336248,
        )},
    },
    "b4": {
        "todos": {"alfa": 2.0, "pesos": (
            0.0375125, 0.0020608, -0.034728, 1.44394, -0.0946537,
            1.13776, 1.04194, 2.63023, 0.089502, -0.670045,
            1.52721, 0.707258, 0.0652266, 0.307699, -0.81681,
            -0.324124, -0.0252869, -0.0192872, -0.107059, 0.0476549,
            1.20284, 0.274543, -4.15035, 0.451477, -0.0199163,
            0.264126, -4.44177, -0.29112, 0.15269, 0.330578,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.0306064, -0.0132135, -0.0363003, 1.8232, -0.0641295,
            1.10994, 0.936099, 1.90953, 0.0458039, -0.585642,
            1.53234, 0.804738, 0.106398, 0.199702, -0.673065,
            -0.444768, -0.0376022, 0.00247349, -0.120856, 0.0288019,
            1.27987, 0.206883, -4.10402, 0.455597, -0.0203781,
            0.260675, -4.17706, -0.309728, 0.16441, 0.307329,
        )},
        "J03WN1": {"alfa": 8.0, "pesos": (
            0.0391198, 0.0187248, -0.0289436, 0.958647, -0.0799917,
            1.1096, 1.11257, 3.72668, 0.0268155, -0.599567,
            1.41384, 1.00614, 0.176867, 0.160735, -0.722547,
            -0.529223, -0.0218076, -0.0299679, -0.0966192, 0.0442844,
            0.989736, 0.378259, -4.3254, 0.431773, -0.00576854,
            0.287203, -4.70049, -0.243125, 0.115645, 0.361429,
        )},
        "J03WOH": {"alfa": 2.0, "pesos": (
            0.0328053, 0.018972, -0.0417908, 1.67521, -0.100255,
            1.16293, 1.00428, 2.08624, 0.0589483, -0.644623,
            1.54583, 0.833648, -0.0108504, 0.367805, -0.839527,
            -0.352537, -0.0198761, -0.023367, -0.111479, 0.0375936,
            1.27324, 0.259194, -4.07429, 0.43984, -0.00712229,
            0.26294, -4.28517, -0.321361, 0.186251, 0.320223,
        )},
        "J03WOY": {"alfa": 4.0, "pesos": (
            0.0402686, 0.000490481, -0.0330194, 1.30555, -0.108522,
            1.14414, 1.06745, 3.25309, 0.0834922, -0.658029,
            1.3938, 0.555298, 0.020055, 0.400167, -0.903382,
            -0.270938, -0.0320217, -0.0160338, -0.0903902, 0.0617012,
            1.2415, 0.243983, -4.03703, 0.458586, -0.0463463,
            0.252876, -4.55296, -0.220501, 0.0775531, 0.342635,
        )},
        "J03WPY": {"alfa": 4.0, "pesos": (
            0.0418441, -0.00453044, -0.0369182, 1.34945, -0.10494,
            1.12952, 1.04305, 3.06005, 0.129654, -0.716623,
            1.73741, 0.250132, 0.0259182, 0.372111, -0.941517,
            -0.051487, -0.0267058, -0.0158839, -0.124915, 0.0476765,
            1.20488, 0.303368, -4.24285, 0.477104, -0.04729,
            0.267426, -4.53381, -0.319138, 0.192047, 0.320392,
        )},
        "J03WQQ": {"alfa": 8.0, "pesos": (
            0.0230818, 0.0245812, -0.0307349, 1.45329, -0.101606,
            1.14875, 1.21742, 1.93066, 0.0947507, -0.678838,
            1.40736, 0.898022, 0.0978462, 0.278064, -0.7785,
            -0.308609, -0.0119348, -0.0369917, -0.101012, 0.0557967,
            1.22534, 0.270801, -4.16733, 0.439929, 0.00965233,
            0.258966, -4.2923, -0.344712, 0.197429, 0.32487,
        )},
        "J03WR9": {"alfa": 2.0, "pesos": (
            0.0529509, -0.0286386, -0.0377898, 1.50243, -0.0814839,
            1.12967, 0.951319, 2.59616, 0.12796, -0.716306,
            1.60295, 0.615601, 0.0597802, 0.331595, -0.826551,
            -0.313793, -0.0248903, -0.0194702, -0.0986982, 0.0570066,
            1.15001, 0.226786, -4.0326, 0.453503, -0.018045,
            0.264411, -4.51977, -0.279009, 0.137234, 0.336248,
        )},
    },
    "b5": {
        "todos": {"alfa": 4.0, "pesos": (
            0.0375125, 0.0020608, -0.034728, 1.44394, -0.0946537,
            1.13776, 1.04194, 2.63023, 0.089502, -0.670045,
            1.52721, 0.707258, 0.0652266, 0.307699, -0.81681,
            -0.324124, -0.0252869, -0.0192872, -0.107059, 0.0476549,
            1.20284, 0.274543, -4.15035, 0.451477, -0.0199163,
            0.264126, -4.44177, -0.29112, 0.15269, 0.330578,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.0306064, -0.0132135, -0.0363003, 1.8232, -0.0641295,
            1.10994, 0.936099, 1.90953, 0.0458039, -0.585642,
            1.53234, 0.804738, 0.106398, 0.199702, -0.673065,
            -0.444768, -0.0376022, 0.00247349, -0.120856, 0.0288019,
            1.27987, 0.206883, -4.10402, 0.455597, -0.0203781,
            0.260675, -4.17706, -0.309728, 0.16441, 0.307329,
        )},
        "J03WN1": {"alfa": 4.0, "pesos": (
            0.0391198, 0.0187248, -0.0289436, 0.958647, -0.0799917,
            1.1096, 1.11257, 3.72668, 0.0268155, -0.599567,
            1.41384, 1.00614, 0.176867, 0.160735, -0.722547,
            -0.529223, -0.0218076, -0.0299679, -0.0966192, 0.0442844,
            0.989736, 0.378259, -4.3254, 0.431773, -0.00576854,
            0.287203, -4.70049, -0.243125, 0.115645, 0.361429,
        )},
        "J03WOH": {"alfa": 4.0, "pesos": (
            0.0328053, 0.018972, -0.0417908, 1.67521, -0.100255,
            1.16293, 1.00428, 2.08624, 0.0589483, -0.644623,
            1.54583, 0.833648, -0.0108504, 0.367805, -0.839527,
            -0.352537, -0.0198761, -0.023367, -0.111479, 0.0375936,
            1.27324, 0.259194, -4.07429, 0.43984, -0.00712229,
            0.26294, -4.28517, -0.321361, 0.186251, 0.320223,
        )},
        "J03WOY": {"alfa": 4.0, "pesos": (
            0.0402686, 0.000490481, -0.0330194, 1.30555, -0.108522,
            1.14414, 1.06745, 3.25309, 0.0834922, -0.658029,
            1.3938, 0.555298, 0.020055, 0.400167, -0.903382,
            -0.270938, -0.0320217, -0.0160338, -0.0903902, 0.0617012,
            1.2415, 0.243983, -4.03703, 0.458586, -0.0463463,
            0.252876, -4.55296, -0.220501, 0.0775531, 0.342635,
        )},
        "J03WPY": {"alfa": 4.0, "pesos": (
            0.0418441, -0.00453044, -0.0369182, 1.34945, -0.10494,
            1.12952, 1.04305, 3.06005, 0.129654, -0.716623,
            1.73741, 0.250132, 0.0259182, 0.372111, -0.941517,
            -0.051487, -0.0267058, -0.0158839, -0.124915, 0.0476765,
            1.20488, 0.303368, -4.24285, 0.477104, -0.04729,
            0.267426, -4.53381, -0.319138, 0.192047, 0.320392,
        )},
        "J03WQQ": {"alfa": 4.0, "pesos": (
            0.0230818, 0.0245812, -0.0307349, 1.45329, -0.101606,
            1.14875, 1.21742, 1.93066, 0.0947507, -0.678838,
            1.40736, 0.898022, 0.0978462, 0.278064, -0.7785,
            -0.308609, -0.0119348, -0.0369917, -0.101012, 0.0557967,
            1.22534, 0.270801, -4.16733, 0.439929, 0.00965233,
            0.258966, -4.2923, -0.344712, 0.197429, 0.32487,
        )},
        "J03WR9": {"alfa": 8.0, "pesos": (
            0.0529509, -0.0286386, -0.0377898, 1.50243, -0.0814839,
            1.12967, 0.951319, 2.59616, 0.12796, -0.716306,
            1.60295, 0.615601, 0.0597802, 0.331595, -0.826551,
            -0.313793, -0.0248903, -0.0194702, -0.0986982, 0.0570066,
            1.15001, 0.226786, -4.0326, 0.453503, -0.018045,
            0.264411, -4.51977, -0.279009, 0.137234, 0.336248,
        )},
    },
    "b6": {
        "todos": {"alfa": 4.0, "pesos": (
            0.0404691, 0.0502709, 0.584843, -0.0141848, 0.456653,
            3.22999, 0.650874, -1.23696, 1.78201, 0.108128,
            -0.197529, -0.427342, 0.0244732, -0.137698, 0.0305683,
            1.9062, 0.591306, -5.9058, 0.356964, 0.157585,
            0.300433, -5.25617, -0.193525, -0.0197561, 0.32174,
        )},
        "J03WMX": {"alfa": 1.0, "pesos": (
            0.0419482, 0.00591851, 0.761194, 0.0127286, 0.428271,
            2.83672, 0.606885, -1.12319, 1.78472, 0.15766,
            -0.308131, -0.363937, 0.0102287, -0.113401, 0.00734049,
            1.99807, 0.510595, -5.82044, 0.355904, 0.158679,
            0.293424, -5.01303, -0.199434, -0.0183508, 0.302885,
        )},
        "J03WN1": {"alfa": 2.0, "pesos": (
            0.0372139, 0.0947497, 0.386601, 0.00681781, 0.394385,
            3.71366, 0.659632, -1.32391, 1.95217, 0.18964,
            -0.217409, -0.557102, 0.0230227, -0.142204, 0.0333425,
            1.64164, 0.6858, -6.0149, 0.320561, 0.194112,
            0.32892, -5.47568, -0.136934, -0.0707009, 0.347006,
        )},
        "J03WOH": {"alfa": 2.0, "pesos": (
            0.039374, 0.0478268, 0.688104, -0.0163217, 0.489974,
            2.97956, 0.590553, -1.18347, 1.83968, 0.0387616,
            -0.181429, -0.421004, 0.029351, -0.133097, 0.0141255,
            2.01984, 0.595782, -5.91271, 0.346239, 0.170085,
            0.295996, -5.12937, -0.232879, 0.0226884, 0.314606,
        )},
        "J03WOY": {"alfa": 1.0, "pesos": (
            0.0404728, 0.0654194, 0.506884, -0.0107758, 0.386898,
            3.54867, 0.671539, -1.25257, 1.62806, 0.0545122,
            -0.096705, -0.479866, 0.0185821, -0.14021, 0.0599128,
            1.97378, 0.567314, -5.88409, 0.350566, 0.151642,
            0.292321, -5.38146, -0.113032, -0.109579, 0.329955,
        )},
        "J03WPY": {"alfa": 4.0, "pesos": (
            0.0418402, 0.0574005, 0.542827, -0.0103627, 0.411508,
            3.46807, 0.659407, -1.20942, 1.70627, 0.071748,
            -0.175988, -0.361933, 0.0230612, -0.137343, 0.0159811,
            1.9044, 0.626821, -5.96479, 0.393792, 0.114303,
            0.300061, -5.34358, -0.223801, 0.0255416, 0.314734,
        )},
        "J03WQQ": {"alfa": 2.0, "pesos": (
            0.0295503, 0.0638126, 0.595108, -0.0495036, 0.58835,
            3.03543, 0.623729, -1.22369, 1.72426, 0.16512,
            -0.299863, -0.29856, 0.0337933, -0.148504, 0.0358546,
            1.91201, 0.551434, -5.83045, 0.366227, 0.163386,
            0.293124, -5.09161, -0.268238, 0.0486274, 0.318772,
        )},
        "J03WR9": {"alfa": 4.0, "pesos": (
            0.0538476, 0.0160762, 0.602124, -0.00457291, 0.454342,
            3.09552, 0.698847, -1.27452, 1.79557, 0.0849344,
            -0.132735, -0.473348, 0.027271, -0.14229, 0.0492909,
            1.84285, 0.529345, -5.79873, 0.362202, 0.153665,
            0.303491, -5.3342, -0.181865, -0.0324516, 0.324102,
        )},
    },
    "b7": {
        "todos": {"alfa": 2.0, "pesos": (
            0.0494415, -0.0038846, -0.00275515, 1.13477, -0.0775694,
            1.3571, 1.33042, 0.325263, 0.0254878, -0.539923,
            1.43934, 0.437432, -0.118634, 0.436407, -0.421067,
            -0.587678, -0.0137724, -0.0577931, -0.0912509, 0.0857342,
            1.05075, -0.100369, -2.87184, 0.573574, -0.279541,
            0.151917, -3.46304, -0.223839, 0.122168, 0.206106,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.0512183, -0.041346, -0.0524927, 1.4615, -0.0783853,
            1.40409, 1.27607, -0.233797, -0.0426037, -0.416017,
            1.39981, 0.576707, -0.0408959, 0.260627, -0.269199,
            -0.6951, -0.0259889, -0.0371615, -0.090712, 0.0654266,
            1.0394, -0.0956983, -2.82169, 0.580812, -0.287587,
            0.152864, -3.18067, -0.228297, 0.121989, 0.185211,
        )},
        "J03WN1": {"alfa": 2.0, "pesos": (
            0.0389246, 0.0306692, 0.0250076, 0.729079, -0.0468261,
            1.32884, 1.33541, 1.2564, -0.0334208, -0.519248,
            1.44306, 0.643292, 0.0305551, 0.265001, -0.3425,
            -0.761547, -0.000793251, -0.0749144, -0.0934168, 0.0901659,
            0.939548, 0.0456418, -3.11867, 0.568473, -0.274167,
            0.164217, -3.54545, -0.230585, 0.136634, 0.21726,
        )},
        "J03WOH": {"alfa": 2.0, "pesos": (
            0.0439644, 0.0186948, -0.0226808, 1.32954, -0.0566606,
            1.37806, 1.35748, -0.127684, -0.00867336, -0.526771,
            1.42167, 0.536869, -0.303212, 0.636497, -0.491713,
            -0.549239, -0.0097946, -0.0605453, -0.0821913, 0.0609177,
            1.13017, -0.184895, -2.76961, 0.547634, -0.249314,
            0.15367, -3.38535, -0.249944, 0.143984, 0.19863,
        )},
        "J03WOY": {"alfa": 2.0, "pesos": (
            0.0485284, 0.00563139, -0.0187063, 1.05057, -0.0892758,
            1.32998, 1.27455, 0.869174, 0.023559, -0.511618,
            1.36129, 0.381813, -0.0781875, 0.426937, -0.490843,
            -0.610861, -0.0177346, -0.0629691, -0.0685191, 0.090367,
            1.07683, -0.0216514, -2.90328, 0.595271, -0.316299,
            0.140896, -3.49603, -0.157685, 0.0445981, 0.213259,
        )},
        "J03WPY": {"alfa": 2.0, "pesos": (
            0.0669513, -0.0338992, 0.0177253, 1.06348, -0.103582,
            1.37568, 1.27184, 0.765944, 0.0898554, -0.585768,
            1.73151, -0.0751689, -0.204929, 0.514336, -0.531473,
            -0.312012, -0.0193238, -0.0493713, -0.117492, 0.0881672,
            1.09746, -0.165138, -2.91561, 0.61325, -0.319851,
            0.155451, -3.6181, -0.227105, 0.14004, 0.199237,
        )},
        "J03WQQ": {"alfa": 4.0, "pesos": (
            0.0268531, 0.0295738, 0.027391, 1.1158, -0.0582768,
            1.30505, 1.61841, -0.417431, 0.0526662, -0.56977,
            1.28463, 0.613364, -0.112515, 0.467908, -0.387786,
            -0.614663, -0.00356785, -0.0700819, -0.107451, 0.11468,
            1.07522, -0.0779652, -2.90117, 0.541521, -0.231645,
            0.145618, -3.41382, -0.26058, 0.15127, 0.205597,
        )},
        "J03WR9": {"alfa": 4.0, "pesos": (
            0.0675463, -0.034192, -0.00649658, 1.16574, -0.0998918,
            1.37748, 1.21016, 0.302045, 0.0671136, -0.613548,
            1.43309, 0.373298, -0.118859, 0.472829, -0.42183,
            -0.566892, -0.0161626, -0.0539793, -0.0766372, 0.0898288,
            0.974234, -0.200916, -2.67747, 0.567828, -0.275076,
            0.155007, -3.59378, -0.225919, 0.131705, 0.223168,
        )},
    },
    "b8": {
        "todos": {"alfa": 2.0, "pesos": (
            0.0432226, 0.00979531, -0.322975, 1.44234, -0.0976327,
            1.15535, 0.70883, 2.60311, 0.0662229, -0.604102,
            1.31108, 0.708563, 0.0546563, 0.295955, -0.736659,
            -0.277183, -0.0257919, -0.0142308, -0.083924, 0.0316819,
            1.15642, 0.365338, -4.13601, 0.45344, -0.0277075,
            0.26358, -4.3977, -0.29332, 0.160936, 0.331959,
            -1.10536, 23.7908,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.0351305, -0.00488014, -0.296561, 1.81794, -0.0685014,
            1.13669, 0.618928, 1.88738, 0.0250798, -0.516515,
            1.33098, 0.805622, 0.100484, 0.183803, -0.603632,
            -0.39931, -0.0382002, 0.0066199, -0.0995309, 0.0144704,
            1.24414, 0.310634, -4.12205, 0.452911, -0.0224985,
            0.259796, -4.14384, -0.307567, 0.1672, 0.309037,
            -1.24524, 22.0006,
        )},
        "J03WN1": {"alfa": 4.0, "pesos": (
            0.0454471, 0.0272914, -0.304866, 0.946348, -0.0755839,
            1.12093, 0.794529, 3.6813, 0.00678767, -0.534741,
            1.1637, 1.06484, 0.166736, 0.156932, -0.650059,
            -0.493622, -0.0238579, -0.0249655, -0.0722352, 0.027046,
            0.935132, 0.461647, -4.29093, 0.432561, -0.0148615,
            0.286552, -4.64811, -0.24395, 0.124864, 0.362808,
            -1.25217, 23.638,
        )},
        "J03WOH": {"alfa": 1.0, "pesos": (
            0.038764, 0.0244444, -0.340121, 1.67749, -0.111244,
            1.18786, 0.666313, 2.08322, 0.0375919, -0.587366,
            1.35822, 0.773582, -0.0272617, 0.360318, -0.749786,
            -0.30497, -0.0198647, -0.0169443, -0.0917134, 0.0248977,
            1.21664, 0.342305, -4.04433, 0.445607, -0.0193321,
            0.263663, -4.23096, -0.327821, 0.199414, 0.320361,
            -1.00811, 24.1969,
        )},
        "J03WOY": {"alfa": 4.0, "pesos": (
            0.0456107, 0.0145246, -0.32953, 1.32917, -0.107606,
            1.15304, 0.745516, 3.23159, 0.050427, -0.566837,
            1.15007, 0.529325, 0.00867351, 0.38276, -0.80943,
            -0.227569, -0.0302189, -0.0146572, -0.0648951, 0.0446221,
            1.1859, 0.341379, -4.02276, 0.461265, -0.0548694,
            0.251937, -4.49912, -0.223553, 0.0867242, 0.3443,
            -1.38457, 23.9373,
        )},
        "J03WPY": {"alfa": 2.0, "pesos": (
            0.0464467, 0.00291101, -0.344746, 1.33979, -0.11023,
            1.14649, 0.685916, 3.02175, 0.103631, -0.65698,
            1.54568, 0.226939, 0.0165539, 0.363788, -0.865333,
            0.0098204, -0.0271147, -0.0101697, -0.103547, 0.0357135,
            1.17287, 0.396357, -4.23348, 0.47853, -0.0538365,
            0.266062, -4.50326, -0.319918, 0.198138, 0.322553,
            -0.759676, 24.9104,
        )},
        "J03WQQ": {"alfa": 4.0, "pesos": (
            0.0291543, 0.0278913, -0.329831, 1.455, -0.102621,
            1.16453, 0.888765, 1.90837, 0.0675285, -0.612176,
            1.17694, 0.92202, 0.0798674, 0.27538, -0.699175,
            -0.261973, -0.0118713, -0.0314017, -0.0777069, 0.0377827,
            1.18354, 0.365919, -4.16652, 0.446374, -0.00254635,
            0.258254, -4.25303, -0.351466, 0.210232, 0.326488,
            -0.971741, 24.5674,
        )},
        "J03WR9": {"alfa": 8.0, "pesos": (
            0.0597324, -0.0207906, -0.319268, 1.49156, -0.0865065,
            1.14795, 0.606432, 2.56443, 0.116893, -0.668447,
            1.4001, 0.636757, 0.0554269, 0.307232, -0.748563,
            -0.26128, -0.027511, -0.0117397, -0.0733575, 0.0374833,
            1.10073, 0.305181, -4.00223, 0.453279, -0.022494,
            0.264604, -4.47353, -0.279007, 0.142159, 0.336985,
            -1.14066, 23.3698,
        )},
    },
    "b9": {
        "todos": {"alfa": 2.0, "pesos": (
            0.0248344, 0.0740258, 0.306622, 1.29556, -0.0784222,
            1.12275, 0.710779, 2.85105, 0.0292616, -0.655769,
            1.59011, 0.329948, 0.0194359, 0.448331, -1.10803,
            0.00019182, -0.0242304, -0.0398015, -0.10409, 0.112681,
            1.47189, 0.237191, -4.32444, 0.274059, -0.00514532,
            0.265707, -4.69382, -0.116231, 0.140765, 0.327212,
            0.048555, 0.546326, 0.985652,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.0181951, 0.0592142, 0.296572, 1.68184, -0.0459791,
            1.08888, 0.623231, 2.14636, -0.0296597, -0.54066,
            1.56699, 0.460461, 0.0582571, 0.337182, -0.957817,
            -0.126979, -0.0366786, -0.0187889, -0.109146, 0.0826655,
            1.54357, 0.17242, -4.26838, 0.278213, -0.0107448,
            0.262006, -4.42407, -0.134267, 0.156739, 0.304283,
            0.0583782, 0.564285, 0.969787,
        )},
        "J03WN1": {"alfa": 4.0, "pesos": (
            0.0221773, 0.0932322, 0.291794, 0.843965, -0.0578681,
            1.08143, 0.746313, 3.89818, -0.0319725, -0.59639,
            1.58372, 0.593042, 0.123742, 0.310094, -1.0306,
            -0.201078, -0.0229333, -0.0453525, -0.106034, 0.119968,
            1.29312, 0.289206, -4.45472, 0.267212, 0.00322221,
            0.284615, -4.98585, -0.0807155, 0.109217, 0.361874,
            0.101321, 0.468832, 0.984877,
        )},
        "J03WOH": {"alfa": 2.0, "pesos": (
            0.0229013, 0.0915775, 0.330472, 1.51352, -0.0781625,
            1.13348, 0.651643, 2.33168, -0.00812638, -0.609683,
            1.62678, 0.380989, -0.0470851, 0.481854, -1.16572,
            0.0283859, -0.0189191, -0.043327, -0.108315, 0.0983797,
            1.5048, 0.255978, -4.30612, 0.244337, 0.0255991,
            0.270624, -4.50216, -0.129073, 0.15717, 0.311202,
            0.0582856, 0.507263, 1.02767,
        )},
        "J03WOY": {"alfa": 4.0, "pesos": (
            0.0265548, 0.0744194, 0.300367, 1.17825, -0.0880162,
            1.13131, 0.751986, 3.61178, -0.000344642, -0.607015,
            1.43067, 0.026861, -0.0191354, 0.524599, -1.16689,
            0.0701541, -0.0316142, -0.0393799, -0.0867908, 0.133532,
            1.48849, 0.187973, -4.16265, 0.294996, -0.0523083,
            0.255103, -4.78434, -0.0598191, 0.0867288, 0.33877,
            0.0161269, 0.572874, 1.01966,
        )},
        "J03WPY": {"alfa": 4.0, "pesos": (
            0.02816, 0.0687362, 0.291246, 1.19097, -0.101692,
            1.13902, 0.734977, 3.17627, 0.0748625, -0.721045,
            1.75215, -0.0135217, -0.0310597, 0.530719, -1.20812,
            0.20481, -0.022661, -0.040375, -0.112649, 0.10897,
            1.49211, 0.239098, -4.37778, 0.302261, -0.0337659,
            0.264278, -4.80449, -0.147614, 0.182126, 0.321592,
            0.0275044, 0.570511, 0.952702,
        )},
        "J03WQQ": {"alfa": 2.0, "pesos": (
            0.0176293, 0.0894984, 0.333467, 1.29535, -0.0897829,
            1.13339, 0.872526, 2.13055, 0.041105, -0.693028,
            1.45707, 0.623403, 0.0522428, 0.458339, -1.08769,
            -0.0180508, -0.0114443, -0.056686, -0.102127, 0.126267,
            1.50538, 0.268407, -4.3704, 0.248283, 0.0344559,
            0.25892, -4.55034, -0.155558, 0.175483, 0.322431,
            0.0542063, 0.57786, 0.998704,
        )},
        "J03WR9": {"alfa": 2.0, "pesos": (
            0.0377865, 0.0422626, 0.298607, 1.33532, -0.0583347,
            1.11331, 0.624903, 2.82396, 0.085614, -0.712399,
            1.65472, 0.229284, 0.0389246, 0.425364, -1.09424,
            0.0346038, -0.0252062, -0.0367692, -0.0982437, 0.119776,
            1.42468, 0.210638, -4.25287, 0.281009, -0.000703268,
            0.269117, -4.77913, -0.108616, 0.122367, 0.330309,
            0.0225781, 0.57644, 0.935828,
        )},
    },
}
# <<< COEFICIENTES
