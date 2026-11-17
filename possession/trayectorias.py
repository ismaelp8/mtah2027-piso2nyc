"""Evidencia de equipo con una red sobre las trayectorias de jugadores y balón (B13, 17/11; apagada).

No está en `pipeline.PIECES`: se prueba con `aprendida.evidence_b13`. Ver docs/decisiones.md (17/11, «B13»).

Es la idea de los trabajos que infieren el balón y quién lo tiene a partir de las trayectorias (un codificador de
conjuntos por frame y una red recurrente bidireccional por encima), adaptada a la evidencia de equipo:

- **Por frame, un muestreo a 5 Hz** (`representantes`): el frame del medio de cada grupo de 5.
- **Cada equipo se codifica desde su dirección de ataque** (`rasgos`): las posiciones y velocidades se giran 180°
  para el equipo que ataca hacia la izquierda. De cada jugador presente (un slot con posición), 10 rasgos: posición,
  velocidad, posición relativa al balón, distancia al balón, si se ve el balón y las distancias al rival y al
  compañero más cercanos. Del balón, 5: posición, velocidad y si se ve. Sin identidad: los slots son un conjunto.
- **Codificador de conjuntos** (`incrustar`): una red de dos capas para los propios y otra para los rivales, con media y
  máximo sobre los presentes; con el balón y los recuentos, una incrustación `e` de 48 por equipo.
- **Encima, una GRU bidireccional de 32** sobre `[e_H, e_A]`, y z = ½·(G([e_H, e_A]) − G([e_A, e_H])):
  antisimétrico por construcción. z vuelve a 25 Hz por interpolación lineal entre los frames muestreados.
- **Puntuación como B5** (`aprendida.puntuacion_de("b5", ...)`).

La predicción va en float64 y sin BLAS: cada salida se acumula entrada a entrada, en orden fijo, con operaciones
elemento a elemento. Los pesos (`trayectorias_pesos.npz`) los escriben `validation/trayectorias/entrenar.py` (torch) y
`validation/trayectorias/juntar.py` (α), un juego por pliegue de la DFL y el de los 7 (`fuera=None`).
"""

import os

import numpy as np

from possession import aprendida, secuencia
from possession.tracking import A, H

PESOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trayectorias_pesos.npz")
GRUPO = 5  # frames por muestra (25 fps a 5 Hz)
VEL_MAX = 12.0  # m/s: más rápido es un cambio de slot, no un jugador (como aprendida.VEL_MAX)
TOPE_BALON = 30.0  # m
TOPE_VECINO = 20.0  # m
N_JUGADOR = 10
N_BALON = 5
CANALES_DEL_BALON = (4, 5, 6, 7)  # los rasgos del jugador que dependen del balón (se apagan sin balón)
_CACHE = {}


# -- rasgos ------------------------------------------------------------------------------------------------

def representantes(largo):
    """Índice (dentro del tramo) del frame que representa a cada grupo de `GRUPO`: el del medio, hacia abajo."""
    inicio = np.arange(0, largo, GRUPO)
    tam = np.minimum(GRUPO, largo - inicio)
    return inicio + (tam - 1) // 2


def a_frames(z5, largo):
    """z por muestra a z por frame: interpolación lineal entre los representantes; constante en los extremos."""
    return np.interp(np.arange(largo, dtype=np.float64), representantes(largo).astype(np.float64), z5)


def _velocidad(v, idx, fps, paso):
    """(v[idx + paso] − v[idx − paso]) · fps / (2·paso), con los índices recortados al tramo. `v` es (L, ...)."""
    antes = np.maximum(idx - paso, 0)
    despues = np.minimum(idx + paso, len(v) - 1)
    dt = np.maximum(despues - antes, 1).astype(np.float64)
    forma = (-1,) + (1,) * (v.ndim - 1)
    return (v[despues] - v[antes]) * fps / dt.reshape(forma)


def _vecino(x, y, hay, ox, oy, ohay, mismo):
    """Distancia (T, S) de cada jugador al más cercano del otro conjunto (o de su mismo conjunto, sin él)."""
    d2 = (x[:, :, None] - ox[:, None, :]) ** 2 + (y[:, :, None] - oy[:, None, :]) ** 2
    d2 = np.where(hay[:, :, None] & ohay[:, None, :], d2, np.inf)
    if mismo:
        s = x.shape[1]
        d2[:, np.arange(s), np.arange(s)] = np.inf
    minimo = d2.min(axis=2) if d2.shape[2] else np.full(x.shape, np.inf)
    return np.minimum(np.sqrt(minimo), TOPE_VECINO)


def rasgos_tramo(trk, inicio, fin):
    """Rasgos de un tramo a 5 Hz: {"H": (propios, rivales, balon), "A": (...)} y las máscaras.

    propios y rivales: (T, S, 10) en float64, a cero donde no hay jugador; balon: (T, 5). Máscaras (T, S) de bool.
    Cada perspectiva ve el campo con su equipo atacando hacia +x.
    """
    largo_campo, ancho_campo = float(trk.pitch[0]), float(trk.pitch[1])
    fps = float(trk.fps)
    idx = representantes(fin - inicio)
    team = np.asarray(trk.team)
    px = np.asarray(trk.px[inicio:fin], dtype=np.float64)
    py = np.asarray(trk.py[inicio:fin], dtype=np.float64)
    bx = np.asarray(trk.bx[inicio:fin], dtype=np.float64)
    by = np.asarray(trk.by[inicio:fin], dtype=np.float64)
    columnas = {H: np.flatnonzero(team == H), A: np.flatnonzero(team == A)}
    # Dirección de ataque del local en el tramo, como en B2: hacia donde está, en media, el visitante.
    hay_h = np.isfinite(px[:, columnas[H]]) & np.isfinite(py[:, columnas[H]])
    hay_a = np.isfinite(px[:, columnas[A]]) & np.isfinite(py[:, columnas[A]])
    media_h = np.where(hay_h, px[:, columnas[H]], 0.0).sum() / max(int(hay_h.sum()), 1)
    media_a = np.where(hay_a, px[:, columnas[A]], 0.0).sum() / max(int(hay_a.sum()), 1)
    direccion = float(np.sign(media_a - media_h)) if hay_h.any() and hay_a.any() and media_a != media_h else 1.0

    # Balón en los frames muestreados.
    bxs, bys = bx[idx], by[idx]
    visible = np.isfinite(bxs) & np.isfinite(bys)
    with np.errstate(invalid="ignore"):
        bvx, bvy = _velocidad(bx, idx, fps, 2), _velocidad(by, idx, fps, 2)
    bvx = np.where(np.isfinite(bvx) & visible, bvx, 0.0)
    bvy = np.where(np.isfinite(bvy) & visible, bvy, 0.0)

    equipos = {}
    for equipo in (H, A):
        c = columnas[equipo]
        x, y = px[idx][:, c], py[idx][:, c]
        hay = np.isfinite(x) & np.isfinite(y)
        with np.errstate(invalid="ignore"):
            vx, vy = _velocidad(px[:, c], idx, fps, 1), _velocidad(py[:, c], idx, fps, 1)
            valida = np.isfinite(vx) & np.isfinite(vy) & (np.hypot(vx, vy) <= VEL_MAX)
        equipos[equipo] = {"x": np.where(hay, x, 0.0), "y": np.where(hay, y, 0.0), "hay": hay,
                           "vx": np.where(valida & hay, vx, 0.0), "vy": np.where(valida & hay, vy, 0.0)}
    for equipo, otro in ((H, A), (A, H)):
        e, o = equipos[equipo], equipos[otro]
        e["rival"] = _vecino(e["x"], e["y"], e["hay"], o["x"], o["y"], o["hay"], False)
        e["companero"] = _vecino(e["x"], e["y"], e["hay"], e["x"], e["y"], e["hay"], True)

    salida = {}
    mitad_l, mitad_a = largo_campo / 2.0, ancho_campo / 2.0
    for equipo, otro in ((H, A), (A, H)):
        d = direccion if equipo == H else -direccion
        listas = []
        for quien in (equipo, otro):
            e = equipos[quien]
            dx = np.where(visible[:, None], bxs[:, None] - e["x"], 0.0)
            dy = np.where(visible[:, None], bys[:, None] - e["y"], 0.0)
            dist = np.where(visible[:, None], np.minimum(np.hypot(dx, dy), TOPE_BALON), 0.0)
            r = np.stack([d * (e["x"] - mitad_l) / mitad_l, d * (e["y"] - mitad_a) / mitad_a,
                          d * e["vx"] / 8.0, d * e["vy"] / 8.0,
                          d * dx / 20.0, d * dy / 20.0, dist / TOPE_BALON,
                          np.broadcast_to(visible[:, None].astype(np.float64), e["x"].shape),
                          e["rival"] / TOPE_VECINO, e["companero"] / TOPE_VECINO], axis=2)
            listas.append(np.where(e["hay"][:, :, None], r, 0.0) + 0.0)
        balon = np.stack([np.where(visible, d * (bxs - mitad_l) / mitad_l, 0.0),
                          np.where(visible, d * (bys - mitad_a) / mitad_a, 0.0),
                          d * bvx / 15.0, d * bvy / 15.0, visible.astype(np.float64)], axis=1) + 0.0
        salida[equipo] = (listas[0], listas[1], balon)
    return salida, equipos[H]["hay"], equipos[A]["hay"]


# -- red en numpy -----------------------------------------------------------------------------------------------

def _lineal(x, w, b):
    """W·x + b sobre la última dimensión de `x` (..., entradas), entrada a entrada: (..., salidas)."""
    out = np.zeros(x.shape[:-1] + (w.shape[0],))
    for i in range(w.shape[1]):
        out += x[..., i, None] * w[:, i]
    return out + b


def _conjunto(x, hay, w1, b1, w2, b2):
    """Media y máximo sobre los presentes de la red de dos capas: (T, 2·salidas). El máximo es ≥ 0 (ReLU)."""
    h = np.maximum(_lineal(np.maximum(_lineal(x, w1, b1), 0.0), w2, b2), 0.0)
    m = hay[:, :, None].astype(np.float64)
    hm = h * m
    cuenta = np.maximum(m.sum(axis=1), 1.0)
    return np.concatenate([hm.sum(axis=1) / cuenta, hm.max(axis=1) if hm.shape[1] else np.zeros(hm.shape[:1] + hm.shape[2:])],
                          axis=1)


def incrustar(propios, rivales, balon, hay_p, hay_r, p):
    """Incrustación (T, 48) de un equipo desde su perspectiva."""
    a = _conjunto(propios, hay_p, p["propios1_w"], p["propios1_b"], p["propios2_w"], p["propios2_b"])
    b = _conjunto(rivales, hay_r, p["rivales1_w"], p["rivales1_b"], p["rivales2_w"], p["rivales2_b"])
    c = np.maximum(_lineal(balon, p["balon_w"], p["balon_b"]), 0.0)
    n = np.stack([hay_p.sum(axis=1) / 11.0, hay_r.sum(axis=1) / 11.0], axis=1)
    return np.maximum(_lineal(np.concatenate([a, b, c, n], axis=1), p["marco_w"], p["marco_b"]), 0.0)


def logit_muestras(rasgos, hay_h, hay_a, p):
    """z por muestra (5 Hz) de un tramo."""
    ph, rh, bh = rasgos[H]
    pa, ra, ba = rasgos[A]
    e_h = incrustar(ph, rh, bh, hay_h, hay_a, p)
    e_a = incrustar(pa, ra, ba, hay_a, hay_h, p)
    entradas = (np.concatenate([e_h, e_a], axis=1).T, np.concatenate([e_a, e_h], axis=1).T)  # (96, T)
    gi = np.stack([secuencia._entrada(e, p["w_ih"], p["b_ih"]) for e in entradas]
                  + [secuencia._entrada(e[:, ::-1], p["w_ih_r"], p["b_ih_r"]) for e in entradas])
    whh = np.stack([p["w_hh"], p["w_hh"], p["w_hh_r"], p["w_hh_r"]])
    bhh = np.stack([p["b_hh"], p["b_hh"], p["b_hh_r"], p["b_hh_r"]])
    estados = secuencia._gru(gi, whh, bhh)
    oculto = estados.shape[1]
    w = p["salida_w"][0]
    salidas = []
    for k in range(2):
        delante, detras = estados[k], estados[2 + k][:, ::-1]
        z = np.zeros(estados.shape[2])
        for j in range(oculto):
            z = z + w[j] * delante[j]
        for j in range(oculto):
            z = z + w[oculto + j] * detras[j]
        salidas.append(z + p["salida_b"][0])
    return 0.5 * (salidas[0] - salidas[1])


# -- pesos y evidencia ------------------------------------------------------------------------------------------

def cargar(ruta=PESOS):
    """{modelo: {pliegue: {nombre: array}}} del fichero de pesos."""
    if ruta not in _CACHE:
        if not os.path.isfile(ruta):
            raise FileNotFoundError("no hay pesos en {}: validation/trayectorias/entrenar.py y juntar.py".format(ruta))
        juegos = {}
        with np.load(ruta, allow_pickle=False) as datos:
            for clave in datos.files:
                modelo, pliegue, nombre = clave.split("/", 2)
                juegos.setdefault(modelo, {}).setdefault(pliegue, {})[nombre] = np.asarray(
                    datos[clave], dtype=np.float64)
        _CACHE[ruta] = juegos
    return _CACHE[ruta]


def pesos_de(modelo, fuera=None, ruta=PESOS):
    clave = "todos" if fuera is None else fuera
    juego = cargar(ruta).get(modelo, {}).get(clave)
    if juego is None:
        raise KeyError("no hay pesos de «{}» para «{}» en {}".format(modelo, clave, ruta))
    return juego


def logit(trk, p):
    """z por frame (25 Hz) con el juego `p`; cero fuera de los tramos."""
    z = np.zeros(len(trk.bx))
    for inicio, fin in trk.blocks:
        if fin > inicio:
            r, hay_h, hay_a = rasgos_tramo(trk, inicio, fin)
            z[inicio:fin] = a_frames(logit_muestras(r, hay_h, hay_a, p), fin - inicio)
    return z


def evidencia(trk, modelo="b13", fuera=None, ruta=PESOS):
    """(score, allowed) del modelo, puntuado como B5."""
    p = pesos_de(modelo, fuera, ruta)
    z = logit(trk, p)
    todos = aprendida.equipo_mas_cercano(trk)
    cercano = np.full(len(trk.bx), -1, dtype=np.int8)
    for inicio, fin in trk.blocks:
        cercano[inicio:fin] = todos[inicio:fin]
    return aprendida.puntuacion_de("b5", z, aprendida.balon_visible(trk), float(p["alfa"]), cercano)
