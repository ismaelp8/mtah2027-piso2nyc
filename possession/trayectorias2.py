"""Evidencia de equipo con la red de trayectorias, segunda versión (B14, 17/11; apagada).

Como B13 (`possession/trayectorias.py`), con tres cambios que atacan lo que más pesa en el partido:
- **Rasgos de control por jugador:** además de los 10 de B13, los núcleos de 1 y 3 m de distancia al balón, el
  co-movimiento con el balón (|v_jugador − v_balón|) y la velocidad de acercamiento al balón. Las velocidades, con
  diferencia de ±2 frames. Del balón, también su rapidez.
- **Atención conjunta** sobre los jugadores de los dos equipos, un «más cercano» aprendido y suave: además de la media
  y el máximo de cada equipo, la suma ponderada por la atención y la masa de atención de los propios.
- **Entrenada con dominio aleatorizado** (`validation/trayectorias/exportar2.py`): además del tracking del harness, dos
  copias de cada partido con los jugadores degradados como los del ATD, tracklets cortados y slots fantasma, el balón
  con otra semilla y con retraso, y espejo en y.

Antisimétrica por construcción, como B13: z = ½·(G([e_H, e_A]) − G([e_A, e_H])). Puntuada como B5. Predicción en
float64 y sin BLAS. Pesos en `trayectorias2_pesos.npz`.
"""

import os

import numpy as np

from possession import aprendida, secuencia
from possession.tracking import A, H
from possession.trayectorias import TOPE_BALON, TOPE_VECINO, TOPE_VEL_BALON, VEL_MAX, _lineal, _vecino, _velocidad, a_frames, \
    representantes

PESOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trayectorias2_pesos.npz")
# B15 (17/11): la misma red, entrenada con la etiqueta de control en todos los frames vivos. Sus pesos, aparte.
PESOS_B15 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trayectorias2_b15_pesos.npz")
# B16 (17/11): B15 entrenada también con SkillCorner ENTRENAMIENTO. Además de los pliegues de la DFL, «scA» y «scB» (sin
# cada mitad de SkillCorner), para comprobarla en SkillCorner fuera de muestra.
PESOS_B16 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trayectorias2_b16_pesos.npz")
N_JUGADOR = 14
N_BALON = 6
CANALES_DEL_BALON = (4, 5, 6, 7, 10, 11, 12, 13)
ESPEJO_JUGADOR = (1, 3, 5)  # canales del jugador que cambian de signo con el espejo en y
ESPEJO_BALON = (1, 3)
_CACHE = {}


def rasgos_tramo(trk, inicio, fin):
    """Como `trayectorias.rasgos_tramo`, con 14 rasgos por jugador y 6 del balón."""
    largo_campo, ancho_campo = float(trk.pitch[0]), float(trk.pitch[1])
    fps = float(trk.fps)
    idx = representantes(fin - inicio)
    team = np.asarray(trk.team)
    px = np.asarray(trk.px[inicio:fin], dtype=np.float64)
    py = np.asarray(trk.py[inicio:fin], dtype=np.float64)
    bx = np.asarray(trk.bx[inicio:fin], dtype=np.float64)
    by = np.asarray(trk.by[inicio:fin], dtype=np.float64)
    columnas = {H: np.flatnonzero(team == H), A: np.flatnonzero(team == A)}
    hay_h = np.isfinite(px[:, columnas[H]]) & np.isfinite(py[:, columnas[H]])
    hay_a = np.isfinite(px[:, columnas[A]]) & np.isfinite(py[:, columnas[A]])
    media_h = np.where(hay_h, px[:, columnas[H]], 0.0).sum() / max(int(hay_h.sum()), 1)
    media_a = np.where(hay_a, px[:, columnas[A]], 0.0).sum() / max(int(hay_a.sum()), 1)
    direccion = float(np.sign(media_a - media_h)) if hay_h.any() and hay_a.any() and media_a != media_h else 1.0

    bxs, bys = bx[idx], by[idx]
    visible = np.isfinite(bxs) & np.isfinite(bys)
    with np.errstate(invalid="ignore"):
        bvx, bvy = _velocidad(bx, idx, fps, 2), _velocidad(by, idx, fps, 2)
    with np.errstate(invalid="ignore"):
        valida_b = np.isfinite(bvx) & np.isfinite(bvy) & visible & (np.hypot(bvx, bvy) <= TOPE_VEL_BALON)
    bvx = np.where(valida_b, bvx, 0.0)
    bvy = np.where(valida_b, bvy, 0.0)

    equipos = {}
    for equipo in (H, A):
        c = columnas[equipo]
        x, y = px[idx][:, c], py[idx][:, c]
        hay = np.isfinite(x) & np.isfinite(y)
        with np.errstate(invalid="ignore"):
            vx, vy = _velocidad(px[:, c], idx, fps, 2), _velocidad(py[:, c], idx, fps, 2)
            valida = np.isfinite(vx) & np.isfinite(vy) & (np.hypot(vx, vy) <= VEL_MAX)
        equipos[equipo] = {"x": np.where(hay, x, 0.0), "y": np.where(hay, y, 0.0), "hay": hay,
                           "vx": np.where(valida & hay, vx, 0.0), "vy": np.where(valida & hay, vy, 0.0)}
    for equipo, otro in ((H, A), (A, H)):
        e, o = equipos[equipo], equipos[otro]
        e["rival"] = _vecino(e["x"], e["y"], e["hay"], o["x"], o["y"], o["hay"], False)
        e["companero"] = _vecino(e["x"], e["y"], e["hay"], e["x"], e["y"], e["hay"], True)

    salida = {}
    mitad_l, mitad_a = largo_campo / 2.0, ancho_campo / 2.0
    vis = visible[:, None]
    for equipo, otro in ((H, A), (A, H)):
        d = direccion if equipo == H else -direccion
        listas = []
        for quien in (equipo, otro):
            e = equipos[quien]
            dx = np.where(vis, bxs[:, None] - e["x"], 0.0)
            dy = np.where(vis, bys[:, None] - e["y"], 0.0)
            r = np.where(vis, np.hypot(dx, dy), 0.0)
            rv_x, rv_y = e["vx"] - bvx[:, None], e["vy"] - bvy[:, None]
            comov = np.where(vis, np.minimum(np.hypot(rv_x, rv_y) / 10.0, 1.0), 0.0)
            with np.errstate(invalid="ignore", divide="ignore"):
                acerca = np.where(vis & (r > 0.1), (rv_x * dx + rv_y * dy) / np.maximum(r, 0.1), 0.0)
            ra = np.stack([d * (e["x"] - mitad_l) / mitad_l, d * (e["y"] - mitad_a) / mitad_a,
                           d * e["vx"] / 8.0, d * e["vy"] / 8.0,
                           d * dx / 20.0, d * dy / 20.0, np.minimum(r, TOPE_BALON) / TOPE_BALON,
                           np.broadcast_to(vis.astype(np.float64), e["x"].shape),
                           e["rival"] / TOPE_VECINO, e["companero"] / TOPE_VECINO,
                           np.where(vis, np.exp(-r * r / 2.0), 0.0), np.where(vis, np.exp(-r * r / 18.0), 0.0),
                           comov, np.clip(acerca / 8.0, -2.0, 2.0)], axis=2)
            listas.append(np.where(e["hay"][:, :, None], ra, 0.0) + 0.0)
        balon = np.stack([np.where(visible, d * (bxs - mitad_l) / mitad_l, 0.0),
                          np.where(visible, d * (bys - mitad_a) / mitad_a, 0.0),
                          d * bvx / 15.0, d * bvy / 15.0, np.hypot(bvx, bvy) / 15.0,
                          visible.astype(np.float64)], axis=1) + 0.0
        salida[equipo] = (listas[0], listas[1], balon)
    return salida, equipos[H]["hay"], equipos[A]["hay"]


# -- red en numpy -----------------------------------------------------------------------------------------------

def _capas(x, w1, b1, w2, b2):
    return np.maximum(_lineal(np.maximum(_lineal(x, w1, b1), 0.0), w2, b2), 0.0)


def incrustar(propios, rivales, balon, hay_p, hay_r, p):
    """Incrustación (T, 48) de un equipo desde su perspectiva, con atención conjunta sobre los dos equipos."""
    hp = _capas(propios, p["propios1_w"], p["propios1_b"], p["propios2_w"], p["propios2_b"])
    hr = _capas(rivales, p["rivales1_w"], p["rivales1_b"], p["rivales2_w"], p["rivales2_b"])
    mp, mr = hay_p.astype(np.float64), hay_r.astype(np.float64)
    sp = _lineal(hp, p["atp_w"], p["atp_b"])[..., 0]
    sr = _lineal(hr, p["atr_w"], p["atr_b"])[..., 0]
    todos = np.concatenate([np.where(hay_p, sp, -np.inf), np.where(hay_r, sr, -np.inf)], axis=1)
    hay = np.concatenate([hay_p, hay_r], axis=1)
    alguno = hay.any(axis=1)
    tope = np.where(alguno, np.max(np.where(hay, todos, -np.inf), axis=1, initial=-np.inf), 0.0)
    ex = np.where(hay, np.exp(np.where(hay, todos - tope[:, None], 0.0)), 0.0)
    peso = ex / np.maximum(ex.sum(axis=1, keepdims=True), 1e-300)
    wp, wr = peso[:, :hay_p.shape[1]], peso[:, hay_p.shape[1]:]
    partes = []
    for h, m, w in ((hp, mp, wp), (hr, mr, wr)):
        hm = h * m[:, :, None]
        cuenta = np.maximum(m.sum(axis=1, keepdims=True), 1.0)
        partes += [hm.sum(axis=1) / cuenta, hm.max(axis=1) if hm.shape[1] else np.zeros((len(h), h.shape[2])),
                   (h * w[:, :, None]).sum(axis=1)]
    c = np.maximum(_lineal(balon, p["balon_w"], p["balon_b"]), 0.0)
    n = np.stack([wp.sum(axis=1), mp.sum(axis=1) / 11.0, mr.sum(axis=1) / 11.0], axis=1)
    return np.maximum(_lineal(np.concatenate(partes + [c, n], axis=1), p["marco_w"], p["marco_b"]), 0.0)


def logit_muestras(rasgos, hay_h, hay_a, p):
    """z por muestra (5 Hz) de un tramo: la GRU de B13 sobre las incrustaciones de B14."""
    ph, rh, bh = rasgos[H]
    pa, ra, ba = rasgos[A]
    e_h = incrustar(ph, rh, bh, hay_h, hay_a, p)
    e_a = incrustar(pa, ra, ba, hay_a, hay_h, p)
    entradas = (np.concatenate([e_h, e_a], axis=1).T, np.concatenate([e_a, e_h], axis=1).T)
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


def cargar(ruta=PESOS):
    if ruta not in _CACHE:
        if not os.path.isfile(ruta):
            raise FileNotFoundError("no hay pesos en {}: validation/trayectorias/entrenar2.py y juntar".format(ruta))
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
    z = np.zeros(len(trk.bx))
    for inicio, fin in trk.blocks:
        if fin > inicio:
            r, hay_h, hay_a = rasgos_tramo(trk, inicio, fin)
            z[inicio:fin] = a_frames(logit_muestras(r, hay_h, hay_a, p), fin - inicio)
    return z


def evidencia(trk, modelo="b14", fuera=None, ruta=PESOS):
    p = pesos_de(modelo, fuera, ruta)
    z = logit(trk, p)
    todos = aprendida.equipo_mas_cercano(trk)
    cercano = np.full(len(trk.bx), -1, dtype=np.int8)
    for inicio, fin in trk.blocks:
        cercano[inicio:fin] = todos[inicio:fin]
    return aprendida.puntuacion_de("b5", z, aprendida.balon_visible(trk), float(p["alfa"]), cercano)
