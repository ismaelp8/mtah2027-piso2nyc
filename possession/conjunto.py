"""Modelo conjunto: evidencia de equipo aprendida mirando a los jugadores uno a uno. APAGADO.

**Qué es** (docs/decisiones.md, 17/11, «modelo conjunto»). B5 resume cada frame en unos pocos agregados y los pesa
con una recta. Este modelo recibe a cada jugador (dónde está respecto al balón, cómo se mueve, dónde está en el
campo), los junta por equipo y mira ±12,6 s con una convolucional temporal. Se entrenó con las etiquetas de control
en los 7 partidos abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0) y con las de SkillCorner en 10 de sus
partidos abiertos (A-League 2024/25, MIT), con el balón «como el ATD». No sustituye al `D`: solo dice `H` o `A`.

**Cómo entra en el pipeline.** `evidence(trk, fuera=None)` devuelve `(score, allowed)` como B5: el logit z del
modelo, puntuado con `aprendida.puntuacion_de("b5", …)` (−α·|z| al equipo que pierde y el +1 de N1 donde se ve el
balón). Es el candidato K2. No está en `pipeline.PIECES`: una entrega de prueba lo usa con
`--pieza candidates=aprendida.evidence_k2`. `capa_cambios(trk)` es el candidato K1: una capa `(score, allowed)` que
se suma a las piezas de la entrega (`--capa conjunto.capa_cambios`) y empuja hacia el equipo nuevo después de cada
cambio que ve el modelo, con el mecanismo de `cambios.capa`.

**Reproducible bit a bit.** Las entradas usan sumas, productos, divisiones, raíces, máximos y comparaciones, y la
red solo tiene ReLU: z no pasa por ninguna exponencial. (Las probabilidades de cambio de K1 sí pasan por una, y por
eso van redondeadas a 6 decimales.) Todo se suma término a término y en un orden fijo, sin BLAS, como
`aprendida.logit`. La red se entrenó con torch en float32 (`validation/conjunto/`); aquí se evalúa en float64 con
esos mismos pesos, así que z difiere del de torch en el redondeo.

**Los pesos** están en `conjunto_pesos.npz`, junto a este fichero: un juego por pliegue (el que se entrenó sin cada
partido de la DFL, para el harness) y el de todos (`fuera=None`, la entrega). Los escribe
`validation/conjunto/juntar.py`.
"""

import os

import numpy as np

from possession import aprendida, cambios
from possession.tracking import A, H

GRUPO = 5  # frames por grupo: el modelo va a 5 Hz
PASO_VEL = 2  # frames: la velocidad es la diferencia entre t+2 y t−2
VEL_MAX = 12.0  # m/s: por encima es un cambio de slot (aprendida.VEL_MAX)
VEL_BALON_MAX = 40.0  # m/s: tope de la velocidad del balón
RADIOS2 = (1.0, 6.25, 36.0)  # m²: 1, 2,5 y 6 m, los radios de B1 (aprendida.SIGMAS)
TOPE = 15.0  # m: tope de la distancia al balón (aprendida.TOPE)
N_SLOT, N_IMPAR, N_PAR = 14, 4, 3
JUGADORES = 11.0  # la suma por equipo se divide por 11
TROZO = 4000  # grupos por trozo al pasar la red por jugador: solo limita la memoria, no cambia el resultado
VENTANA_CAPA = 50  # frames que empuja la capa de cambios de K1 (la W de la segunda ronda del detector de cambios)
DECIMALES = 6  # las probabilidades de cambio van redondeadas, como las puntuaciones de `aprendida`
PESOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conjunto_pesos.npz")
_CACHE = {}


# -- entradas -------------------------------------------------------------------------------------------

def _suma5(valores):
    """Suma de cada grupo de `GRUPO` frames, en orden fijo. El largo tiene que ser múltiplo de `GRUPO`."""
    total = valores[0::GRUPO].astype(np.float64)
    for k in range(1, GRUPO):
        total = total + valores[k::GRUPO]
    return total


def direccion_de_ataque(px, team):
    """+1 si el local ataca hacia x creciente en el tramo, −1 si no, 0 si falta un equipo.

    El local ataca hacia donde está, en media, el visitante, como en `aprendida._rasgos_forma`.
    """
    medias = []
    for equipo in (H, A):
        x = np.asarray(px[:, np.asarray(team) == equipo], dtype=np.float64)
        hay = np.isfinite(x)
        if not hay.any():
            return 0.0
        medias.append(np.where(hay, x, 0.0).sum() / int(hay.sum()))
    return float(np.sign(medias[1] - medias[0]))


def entradas(bx, by, px, py, team, largo, ancho, fps):
    """Las entradas a 5 Hz de un tramo evaluado.

    Devuelve `(por_slot, hay, impares, pares)`: una lista de 14 arrays (G, S) por jugador, la máscara (G, S) de los
    slots presentes en el grupo, y las listas de 4 y 3 arrays (G,) por grupo (las impares cambian de signo al
    cambiar los equipos; las pares, no). G es el número de grupos de 5 frames; el último puede ir incompleto.
    """
    n, slots = px.shape
    grupos = -(-n // GRUPO)
    frames = grupos * GRUPO
    p = PASO_VEL

    def rellenar(valores):  # p frames sin datos delante, y detrás los que faltan hasta el grupo entero más p
        salida = np.full((frames + 2 * p,) + valores.shape[1:], np.nan)
        salida[p:p + n] = valores
        return salida

    x_t, y_t = rellenar(np.asarray(px, dtype=np.float64)), rellenar(np.asarray(py, dtype=np.float64))
    bx_t, by_t = rellenar(np.asarray(bx, dtype=np.float64)), rellenar(np.asarray(by, dtype=np.float64))
    presente_t = np.isfinite(x_t) & np.isfinite(y_t)
    visible_t = np.isfinite(bx_t) & np.isfinite(by_t)
    x_t, y_t = np.where(np.isfinite(x_t), x_t, 0.0), np.where(np.isfinite(y_t), y_t, 0.0)
    bx_t, by_t = np.where(np.isfinite(bx_t), bx_t, 0.0), np.where(np.isfinite(by_t), by_t, 0.0)
    centro = slice(p, p + frames)
    presente, visible = presente_t[centro], visible_t[centro]
    x, y, bxc, byc = x_t[centro], y_t[centro], bx_t[centro], by_t[centro]
    k = float(fps) / (2.0 * p)

    vx, vy = (x_t[2 * p:] - x_t[:-2 * p]) * k, (y_t[2 * p:] - y_t[:-2 * p]) * k
    v_ok = presente_t[2 * p:] & presente_t[:-2 * p] & presente & (vx * vx + vy * vy <= VEL_MAX * VEL_MAX)
    vx, vy = np.where(v_ok, vx, 0.0), np.where(v_ok, vy, 0.0)
    vbx, vby = (bx_t[2 * p:] - bx_t[:-2 * p]) * k, (by_t[2 * p:] - by_t[:-2 * p]) * k
    b_ok = visible_t[2 * p:] & visible_t[:-2 * p] & visible
    rapidez = np.sqrt(vbx * vbx + vby * vby)
    escala = np.where(rapidez > VEL_BALON_MAX, VEL_BALON_MAX / np.maximum(rapidez, 1.0), 1.0)
    vbx, vby = np.where(b_ok, vbx * escala, 0.0), np.where(b_ok, vby * escala, 0.0)
    rapidez = np.where(b_ok, np.minimum(rapidez, VEL_BALON_MAX), 0.0)

    direccion = direccion_de_ataque(px, team)
    team = np.asarray(team)
    o = np.where(team == H, direccion, np.where(team == A, -direccion, 0.0))[None, :]
    medio_l, medio_a = float(largo) / 2.0, float(ancho) / 2.0
    dx, dy = x - bxc[:, None], y - byc[:, None]
    con_balon = presente & visible[:, None]
    d2 = dx * dx + dy * dy
    d = np.sqrt(d2)
    rvx, rvy = vx - vbx[:, None], vy - vby[:, None]
    rel_ok = con_balon & v_ok & b_ok[:, None]
    cuenta = _suma5(presente)
    divisor = np.maximum(cuenta, 1.0)

    def grupo(valores):  # la media del grupo sobre los frames en que el slot está presente
        return _suma5(np.where(presente, valores, 0.0)) / divisor

    por_slot = [
        grupo(np.where(con_balon, np.clip(o * dx / 10.0, -6.0, 6.0), 0.0)),
        grupo(np.where(con_balon, np.clip(o * dy / 10.0, -6.0, 6.0), 0.0)),
        grupo(np.where(con_balon, 1.0 / (1.0 + d2 / RADIOS2[0]), 0.0)),
        grupo(np.where(con_balon, 1.0 / (1.0 + d2 / RADIOS2[1]), 0.0)),
        grupo(np.where(con_balon, 1.0 / (1.0 + d2 / RADIOS2[2]), 0.0)),
        grupo(np.where(con_balon, np.minimum(d, TOPE) / TOPE, 1.0)),
        grupo(o * vx / 5.0),
        grupo(o * vy / 5.0),
        grupo(np.where(rel_ok, o * rvx / 5.0, 0.0)),
        grupo(np.where(rel_ok, o * rvy / 5.0, 0.0)),
        grupo(o * (x - medio_l) / medio_l),
        grupo(o * (y - medio_a) / medio_a),
        grupo(np.where(rel_ok, np.clip(-(dx * rvx + dy * rvy) / np.maximum(d, 0.5) / 5.0, -4.0, 4.0), 0.0)),
        cuenta / float(GRUPO),
    ]
    impares = [
        _suma5(np.where(visible, direccion * (bxc - medio_l) / medio_l, 0.0)) / GRUPO,
        _suma5(direccion * vbx / 10.0) / GRUPO,
        _suma5(np.where(visible, direccion * (byc - medio_a) / medio_a, 0.0)) / GRUPO,
        _suma5(direccion * vby / 10.0) / GRUPO,
    ]
    pares = [
        _suma5(visible) / GRUPO,
        _suma5(rapidez / 10.0) / GRUPO,
        _suma5(np.where(visible, np.abs(byc - medio_a) / medio_a, 0.0)) / GRUPO,
    ]
    return por_slot, cuenta > 0, impares, pares


# -- la red, en numpy y sin BLAS --------------------------------------------------------------------------

def _lineal(entradas_, w, b, relu):
    """Una capa lineal sobre una lista de arrays: salida_j = b_j + Σ_i w_ji · entrada_i, sumando en orden."""
    if len(entradas_) != w.shape[1]:
        raise ValueError("{} entradas y {} pesos".format(len(entradas_), w.shape[1]))
    salidas = []
    for j in range(w.shape[0]):
        acumulado = np.full(entradas_[0].shape, float(b[j]))
        for i in range(w.shape[1]):
            acumulado += float(w[j, i]) * entradas_[i]
        salidas.append(np.maximum(acumulado, 0.0) if relu else acumulado)
    return salidas


def _equipos(por_slot, hay, team, pesos):
    """(u_local, u_visitante): por equipo, la suma (entre 11) y el máximo de sus jugadores, y cuántos hay."""
    oculto = _lineal(_lineal(por_slot, pesos["jugador_w0"], pesos["jugador_b0"], True),
                     pesos["jugador_w1"], pesos["jugador_b1"], True)
    salida = []
    for equipo in (H, A):
        columnas = np.flatnonzero(np.asarray(team) == equipo)
        sumas, maximos = [], []
        for h in oculto:
            suma, maximo = np.zeros(h.shape[0]), np.zeros(h.shape[0])
            for s in columnas:  # h ≥ 0: el máximo sobre los presentes, o 0 si no hay ninguno
                valor = np.where(hay[:, s], h[:, s], 0.0)
                suma = suma + valor
                maximo = np.maximum(maximo, valor)
            sumas.append(suma / JUGADORES)
            maximos.append(maximo)
        cuantos = np.zeros(hay.shape[0])
        for s in columnas:
            cuantos = cuantos + hay[:, s]
        salida.append(sumas + maximos + [cuantos / JUGADORES])
    return salida


def _g(u_a, u_b, impares, pares, pesos):
    """La convolucional temporal residual sobre los grupos de un tramo. Devuelve las 4 salidas crudas."""
    h = _lineal(u_a + u_b + impares + pares, pesos["entrada_w"], pesos["entrada_b"], False)
    grupos = len(h[0])
    for k, dilacion in enumerate(pesos["dilaciones"]):
        d = int(dilacion)
        w, b = pesos["bloque{}_w".format(k)], pesos["bloque{}_b".format(k)]
        borde = np.zeros(d)
        activo = [np.concatenate((borde, np.maximum(v, 0.0), borde)) for v in h]
        nuevo = []
        for j in range(w.shape[0]):
            acumulado = np.full(grupos, float(b[j]))
            for i in range(w.shape[1]):
                for toma in range(3):
                    acumulado += float(w[j, i, toma]) * activo[i][toma * d:toma * d + grupos]
            nuevo.append(h[j] + acumulado)
        h = nuevo
    return _lineal([np.maximum(v, 0.0) for v in h], pesos["salida_w"], pesos["salida_b"], False)


def _por_grupo(bx, by, px, py, team, largo, ancho, fps, pesos):
    """(z, logit hacia `H`, logit hacia `A`) por grupo de un tramo."""
    por_slot, hay, impares, pares = entradas(bx, by, px, py, team, largo, ancho, fps)
    u_h, u_a = None, None
    for inicio in range(0, hay.shape[0], TROZO):
        trozo = slice(inicio, inicio + TROZO)
        parte_h, parte_a = _equipos([v[trozo] for v in por_slot], hay[trozo], team, pesos)
        u_h = parte_h if u_h is None else [np.concatenate(par) for par in zip(u_h, parte_h)]
        u_a = parte_a if u_a is None else [np.concatenate(par) for par in zip(u_a, parte_a)]
    directa = _g(u_h, u_a, impares, pares, pesos)
    cambiada = _g(u_a, u_h, [-v for v in impares], pares, pesos)
    z = 0.5 * (directa[0] - cambiada[0])
    par = 0.5 * (directa[1] + cambiada[1])
    impar = 0.5 * (directa[2] - cambiada[2])
    return z, par + impar, par - impar


def _a_frames(valores, n):
    """De grupos a frames, por interpolación lineal entre los centros de los grupos.

    Antes del primer centro y después del último vale el del extremo. Va escrita con operaciones de numpy una a
    una (`a + w·(b − a)`) y no con `np.interp`, cuyo bucle en C puede fundir el producto y la suma en una sola
    operación según la máquina: así el último bit no depende de ella.
    """
    grupos = len(valores)
    inicio = np.arange(grupos) * GRUPO
    centros = (inicio + np.minimum(inicio + GRUPO - 1, n - 1)) / 2.0
    t = np.arange(n, dtype=np.float64)
    anterior = np.clip(np.searchsorted(centros, t, side="right") - 1, 0, grupos - 1)
    siguiente = np.minimum(anterior + 1, grupos - 1)
    hueco = centros[siguiente] - centros[anterior]
    peso = np.clip((t - centros[anterior]) / np.where(hueco > 0, hueco, 1.0), 0.0, 1.0)
    return valores[anterior] + peso * (valores[siguiente] - valores[anterior])


def salidas(trk, fuera=None):
    """(z, hacia_h, hacia_a) por frame: el logit de `H` frente a `A` y los dos logits de cambio. Cero fuera de los
    tramos evaluados. `fuera`: el partido de la DFL que el harness está puntuando (el pliegue que no lo vio)."""
    juego = pesos(fuera)
    n = len(trk.bx)
    z, hacia_h, hacia_a = np.zeros(n), np.zeros(n), np.zeros(n)
    for inicio, fin in trk.blocks:
        if fin - inicio < 1:
            continue
        por_grupo = _por_grupo(trk.bx[inicio:fin], trk.by[inicio:fin], trk.px[inicio:fin], trk.py[inicio:fin],
                               trk.team, trk.pitch[0], trk.pitch[1], trk.fps, juego)
        for destino, valores in zip((z, hacia_h, hacia_a), por_grupo):
            destino[inicio:fin] = _a_frames(valores, fin - inicio)
    return z, hacia_h, hacia_a


# -- pesos y evidencia ------------------------------------------------------------------------------------

def pesos(fuera=None):
    """Los pesos de un pliegue como diccionario de arrays en float64, con `alfa`, `gamma` y `dilaciones`."""
    clave = "todos" if fuera is None else str(fuera)
    if clave not in _CACHE:
        if not os.path.isfile(PESOS):
            raise KeyError("no están los pesos del modelo conjunto ({}): los escribe "
                           "validation/conjunto/juntar.py".format(os.path.basename(PESOS)))
        with np.load(PESOS, allow_pickle=False) as fichero:
            prefijo = clave + "/"
            juego = {nombre[len(prefijo):]: np.asarray(fichero[nombre], dtype=np.float64)
                     for nombre in fichero.files if nombre.startswith(prefijo)}
        if not juego:
            raise KeyError("no hay pesos del modelo conjunto para «{}»".format(clave))
        juego["alfa"] = float(juego["alfa"])
        juego["gamma"] = float(juego["gamma"]) if "gamma" in juego else None
        _CACHE[clave] = juego
    return _CACHE[clave]


def evidence(trk, fuera=None):
    """K2: el logit del modelo conjunto, puntuado como B5 (−α·|z| al que pierde y el +1 de N1 con balón)."""
    juego = pesos(fuera)
    z, _, _ = salidas(trk, fuera)
    todos = aprendida.equipo_mas_cercano(trk)
    cercano = np.full(len(trk.bx), -1, dtype=np.int8)
    for inicio, fin in trk.blocks:  # como B5: a cero fuera de los tramos
        cercano[inicio:fin] = todos[inicio:fin]
    return aprendida.puntuacion_de("b5", z, aprendida.balon_visible(trk), juego["alfa"], cercano)


def probabilidades_de_cambio(trk, fuera=None):
    """`p` (n, 2): la probabilidad de un cambio hacia `H` y hacia `A` en cada frame, a cero fuera de los tramos."""
    _, hacia_h, hacia_a = salidas(trk, fuera)
    p = np.zeros((len(trk.bx), 2))
    for inicio, fin in trk.blocks:
        for columna, logit in enumerate((hacia_h, hacia_a)):
            p[inicio:fin, columna] = np.round(1.0 / (1.0 + np.exp(-logit[inicio:fin])), DECIMALES)
    return p


def capa_cambios(trk, fuera=None):
    """K1: `cambios.capa` con las probabilidades de cambio del modelo, contra el otro equipo (no empuja contra `D`)."""
    juego = pesos(fuera)
    if juego["gamma"] is None:
        raise KeyError("los pesos del modelo conjunto no traen la γ de la capa de cambios")
    return cambios.capa(probabilidades_de_cambio(trk, fuera), juego["gamma"], VENTANA_CAPA, contra_d=True)
