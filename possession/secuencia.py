"""Evidencia de equipo con un modelo de secuencia (B11 y B12): candidatos del 17/11, apagados.

Qué son, cómo se entrenan y la regla de entrada: docs/decisiones.md, 17/11, «B11 y B12, modelos de secuencia».
No están en `pipeline.PIECES`: se prueban con `aprendida.evidence_b11` y `aprendida.evidence_b12`, que llaman a
este módulo.

- **Canales por frame** (`canales`), sin promediar: 9 impares (local menos visitante) y 3 pares. Por tramo
  evaluado; a cero fuera.
- **Antisimétricos por construcción:** z = ½·(g(impares, pares) − g(−impares, pares)). Cambiar los equipos de lado
  cambia el signo de z y nada más.
- **B11** (`logit_b11`): convolucional temporal, 7 bloques residuales con núcleo 3 y dilaciones 1 a 64 (±127
  frames), con ceros fuera del tramo.
- **B12** (`logit_b12`): GRU bidireccional de 16 sobre los canales en medias de 5 frames, y z de vuelta a 25 Hz
  por interpolación lineal.
- **Puntuación como B5** (`aprendida.puntuacion_de("b5", ...)`): −α·|z| al que pierde y el +1 de N1 donde se ve
  el balón.

La predicción va en float64 y sin BLAS: cada salida se acumula canal a canal y toma a toma, en un orden fijo, con
multiplicaciones y sumas elemento a elemento (como `aprendida.logit`). Así no depende de cómo reparta las sumas
una biblioteca de álgebra. `np.exp` y `np.tanh` sí pueden diferir en el último bit entre máquinas, como el
`np.exp` de los rasgos de B5; la puntuación va redondeada a `aprendida.DECIMALES`.

Los pesos los escriben `validation/secuencia/entrenar_red.py` (torch, en float32) y `validation/secuencia/juntar.py`
(α y el fichero) en `secuencia_pesos.npz`, junto a este módulo: un juego por pliegue, el que se entrenó sin cada
partido de la DFL (`fuera`, para el harness) y el de los 7 (`fuera=None`, el de la entrega).
"""

import os

import numpy as np

from possession import aprendida
from possession.tracking import A, H

PESOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secuencia_pesos.npz")
MODELOS = ("b11", "b12")
# Fijados antes de medir (docs/decisiones.md, 17/11).
TOPE_CERCA = 15.0  # m: tope de la distancia al jugador más cercano (canal par)
TOPE_VEL_BALON = 40.0  # m/s: tope de la velocidad del balón (canal par)
IMPARES = ("signo del más cercano", "núcleo 1 m", "núcleo 2,5 m", "núcleo 6 m", "distancia del más cercano",
           "juego en la dirección de ataque", "balón en la dirección de ataque",
           "velocidad en la dirección de ataque", "dispersión")
PARES = ("balón visible", "distancia al más cercano de los dos", "velocidad del balón")
N_IMPARES = len(IMPARES)
N_CANALES = N_IMPARES + len(PARES)
DILACIONES = (1, 2, 4, 8, 16, 32, 64)  # B11
NUCLEO = 3  # B11
GRUPO = 5  # B12: frames por grupo (25 fps a 5 Hz)

_CACHE = {}


# -- canales -----------------------------------------------------------------------------------------------

def canales(trk):
    """Matriz (n, 12) de canales por frame, en float64, a cero fuera de los tramos. Ver `IMPARES` y `PARES`."""
    n = len(trk.bx)
    salida = np.zeros((n, N_CANALES))
    team = np.asarray(trk.team)
    columnas = [np.flatnonzero(team == equipo) for equipo in (H, A)]
    largo, fps = float(trk.pitch[0]), float(trk.fps)
    for inicio, fin in trk.blocks:
        bx = np.asarray(trk.bx[inicio:fin], dtype=np.float64)
        by = np.asarray(trk.by[inicio:fin], dtype=np.float64)
        equipos = [aprendida._por_equipo(trk.px[inicio:fin], trk.py[inicio:fin], c) for c in columnas]
        base, visible = aprendida._rasgos_balon(bx, by, equipos)
        # Las series de `aprendida._rasgos_forma` antes de sus medias, con la misma dirección de ataque.
        (xh, yh, hh), (xa, ya, ha) = equipos
        media_h = np.where(hh, xh, 0.0).sum() / max(int(hh.sum()), 1)
        media_a = np.where(ha, xa, 0.0).sum() / max(int(ha.sum()), 1)
        direccion = float(np.sign(media_a - media_h)) if hh.any() and ha.any() else 0.0
        mitad = largo / 2.0
        juego = direccion * aprendida._sin_nan(aprendida._media_filas(xh, hh) + aprendida._media_filas(xa, ha)
                                               - largo) / mitad
        balon = np.where(visible, direccion * (np.where(visible, bx, mitad) - mitad) / mitad, 0.0)
        vh, va = aprendida._velocidad_x(xh, yh, fps), aprendida._velocidad_x(xa, ya, fps)
        vel = direccion * (aprendida._sin_nan(aprendida._media_filas(vh, np.isfinite(vh)))
                           + aprendida._sin_nan(aprendida._media_filas(va, np.isfinite(va))))
        dispersion = aprendida._sin_nan(aprendida._dispersion(xh, yh, hh) - aprendida._dispersion(xa, ya, ha))
        # Pares: no cambian si se cambian los equipos.
        minimos = []
        for x, y, hay in equipos:
            d2 = (x - bx[:, None]) ** 2 + (y - by[:, None]) ** 2
            d2 = np.where(hay & visible[:, None], d2, np.inf)
            minimos.append(d2.min(axis=1) if d2.shape[1] else np.full(len(bx), np.inf))
        cerca = np.minimum(np.sqrt(np.minimum(minimos[0], minimos[1])), TOPE_CERCA)
        cerca = np.where(visible, cerca, TOPE_CERCA)
        vel_balon = np.zeros(len(bx))
        if len(bx) >= 3:
            with np.errstate(invalid="ignore"):
                v = np.hypot(bx[2:] - bx[:-2], by[2:] - by[:-2]) * fps / 2.0
            vel_balon[1:-1] = np.minimum(np.where(np.isfinite(v), v, 0.0), TOPE_VEL_BALON)
        lista = list(base) + [juego, balon, vel, dispersion, visible.astype(np.float64), cerca, vel_balon]
        salida[inicio:fin] = np.column_stack(lista)
    return salida


def espejo(x):
    """Los canales con los equipos cambiados: los impares cambian de signo, los pares no. `x` es (canales, ...)."""
    y = np.array(x, dtype=np.float64, copy=True)
    y[:N_IMPARES] = -y[:N_IMPARES]
    return y + 0.0  # sin ceros con signo


# -- B11: convolucional temporal ------------------------------------------------------------------------------

def _conv(h, w, b, dilacion):
    """Convolución 1D «same» con ceros fuera, como torch.nn.Conv1d(padding=dilacion, dilation=dilacion).

    `h` (lotes, cin, L), `w` (cout, cin, k), `b` (cout,). Suma toma a toma y canal a canal, en ese orden, y el
    sesgo al final.
    """
    lotes, cin, largo = h.shape
    cout, _, nucleo = w.shape
    medio = (nucleo - 1) // 2
    relleno = medio * dilacion
    hp = np.zeros((lotes, cin, largo + 2 * relleno))
    hp[:, :, relleno:relleno + largo] = h
    out = np.zeros((lotes, cout, largo))
    for k in range(nucleo):
        tramo = hp[:, :, k * dilacion:k * dilacion + largo]
        for i in range(cin):
            out += w[:, i, k][None, :, None] * tramo[:, i, None, :]
    return out + b[None, :, None]


def _g_b11(x, p):
    """g de B11 sobre (lotes, canales, L): la salida (lotes, L) antes de la antisimetría."""
    h = _conv(x, p["entrada_w"], p["entrada_b"], 1)
    for j, dilacion in enumerate(DILACIONES):
        h = h + _conv(np.maximum(h, 0.0), p["bloque{}_w".format(j)], p["bloque{}_b".format(j)], dilacion)
    return _conv(np.maximum(h, 0.0), p["salida_w"], p["salida_b"], 1)[:, 0, :]


def logit_b11(x, p):
    """z de B11 en un tramo: `x` (canales, L) ya normalizados."""
    salida = _g_b11(np.stack([x, espejo(x)]), p)
    return 0.5 * (salida[0] - salida[1])


# -- B12: GRU bidireccional -------------------------------------------------------------------------------------

def agrupar(x):
    """(canales, L) a (canales, ⌈L/5⌉): medias de `GRUPO` frames; el último grupo, con los que haya."""
    largo = x.shape[1]
    grupos = -(-largo // GRUPO)
    suma = np.zeros((x.shape[0], grupos))
    cuenta = np.zeros(grupos)
    for k in range(GRUPO):
        trozo = x[:, k::GRUPO]
        suma[:, :trozo.shape[1]] += trozo
        cuenta[:trozo.shape[1]] += 1.0
    return suma / cuenta


def centros(largo):
    """Frame central de cada grupo (puede ser medio frame)."""
    inicio = np.arange(0, largo, GRUPO, dtype=np.float64)
    fin = np.minimum(inicio + GRUPO, largo) - 1.0
    return 0.5 * (inicio + fin)


def desagrupar(z5, largo):
    """z por grupo a z por frame: interpolación lineal entre los centros; constante en los extremos."""
    return np.interp(np.arange(largo, dtype=np.float64), centros(largo), z5)


def _sigmoide(v):
    return 1.0 / (1.0 + np.exp(-v))


def _gru(gi, whh, bhh):
    """Recorre las secuencias a la vez. `gi` (S, 3H, T) ya con W_ih·x + b_ih; `whh` (S, 3H, H); `bhh` (S, 3H).

    Ecuaciones de torch.nn.GRU (puertas r, z, n en ese orden). Devuelve los estados (S, H, T).
    """
    secuencias, tres, pasos = gi.shape
    oculto = tres // 3
    h = np.zeros((secuencias, oculto))
    estados = np.zeros((secuencias, oculto, pasos))
    for t in range(pasos):
        gh = np.zeros((secuencias, tres))
        for j in range(oculto):
            gh += whh[:, :, j] * h[:, j, None]
        gh += bhh
        r = _sigmoide(gi[:, :oculto, t] + gh[:, :oculto])
        u = _sigmoide(gi[:, oculto:2 * oculto, t] + gh[:, oculto:2 * oculto])
        nuevo = np.tanh(gi[:, 2 * oculto:, t] + r * gh[:, 2 * oculto:])
        h = (1.0 - u) * nuevo + u * h
        estados[:, :, t] = h
    return estados


def _entrada(x, w, b):
    """W·x + b sobre (canales, T), canal a canal: (salidas, T)."""
    out = np.zeros((w.shape[0], x.shape[1]))
    for i in range(w.shape[1]):
        out += w[:, i, None] * x[i][None, :]
    return out + b[:, None]


def logit_b12_grupos(x5, p):
    """z de B12 por grupo: `x5` (canales, T) ya normalizados y agrupados."""
    entradas = (x5, espejo(x5))
    # Cuatro secuencias a la vez: hacia delante con x y con su espejo, y hacia atrás con los dos.
    gi = np.stack([_entrada(e, p["w_ih"], p["b_ih"]) for e in entradas]
                  + [_entrada(e[:, ::-1], p["w_ih_r"], p["b_ih_r"]) for e in entradas])
    whh = np.stack([p["w_hh"], p["w_hh"], p["w_hh_r"], p["w_hh_r"]])
    bhh = np.stack([p["b_hh"], p["b_hh"], p["b_hh_r"], p["b_hh_r"]])
    estados = _gru(gi, whh, bhh)
    oculto = estados.shape[1]
    w = p["salida_w"][0]
    salidas = []
    for e in range(2):
        delante, detras = estados[e], estados[2 + e][:, ::-1]
        z = np.zeros(estados.shape[2])
        for j in range(oculto):
            z = z + w[j] * delante[j]
        for j in range(oculto):
            z = z + w[oculto + j] * detras[j]
        salidas.append(z + p["salida_b"][0])
    return 0.5 * (salidas[0] - salidas[1])


def logit_b12(x, p):
    """z de B12 por frame en un tramo: `x` (canales, L) ya normalizados."""
    return desagrupar(logit_b12_grupos(agrupar(x), p), x.shape[1])


# -- pesos y evidencia ------------------------------------------------------------------------------------------

def cargar(ruta=PESOS):
    """{modelo: {pliegue: {nombre: array}}} del fichero de pesos. Los pliegues: «todos» y cada partido."""
    if ruta not in _CACHE:
        if not os.path.isfile(ruta):
            raise FileNotFoundError("no hay pesos de B11 y B12 en {}: hay que ejecutar validation/secuencia/"
                                    "entrenar.py y juntar.py".format(ruta))
        juegos = {}
        with np.load(ruta, allow_pickle=False) as datos:
            for clave in datos.files:
                modelo, pliegue, nombre = clave.split("/", 2)
                juegos.setdefault(modelo, {}).setdefault(pliegue, {})[nombre] = np.asarray(
                    datos[clave], dtype=np.float64)
        _CACHE[ruta] = juegos
    return _CACHE[ruta]


def pesos_de(modelo, fuera=None, ruta=PESOS):
    """El juego de un modelo: el de los 7 partidos (`fuera=None`) o el del pliegue sin `fuera`."""
    clave = "todos" if fuera is None else fuera
    juego = cargar(ruta).get(modelo, {}).get(clave)
    if juego is None:
        raise KeyError("no hay pesos de «{}» para «{}» en {}".format(modelo, clave, ruta))
    return juego


def logit(trk, modelo, p):
    """z por frame del modelo con el juego `p` (pesos, `rms` y `alfa`); cero fuera de los tramos."""
    x = canales(trk)
    z = np.zeros(len(trk.bx))
    una = logit_b11 if modelo == "b11" else logit_b12
    for inicio, fin in trk.blocks:
        if fin > inicio:
            z[inicio:fin] = una(x[inicio:fin].T / p["rms"][:, None], p)
    return z


def evidencia(trk, modelo, fuera=None, ruta=PESOS):
    """(score, allowed) del modelo, puntuado como B5."""
    if modelo not in MODELOS:
        raise ValueError("modelo desconocido: {} (valen: {})".format(modelo, MODELOS))
    p = pesos_de(modelo, fuera, ruta)
    z = logit(trk, modelo, p)
    todos = aprendida.equipo_mas_cercano(trk)
    cercano = np.full(len(trk.bx), -1, dtype=np.int8)
    for inicio, fin in trk.blocks:
        cercano[inicio:fin] = todos[inicio:fin]
    return aprendida.puntuacion_de("b5", z, aprendida.balon_visible(trk), float(p["alfa"]), cercano)
