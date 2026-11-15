"""El desfase entre el balón y el jugador que lo lleva: la medida de `validation/retraso_balon/BITACORA.md` §2.

Funciones puras sobre un `Tracking` (`possession/tracking.py`): el mismo código mide la DFL
(`calibrar_dfl.py`) y el partido (`validation/partido/retraso_balon.py`). No abre ningún fichero y solo
devuelve agregados: recuentos, desfases y correlaciones del conjunto, nada por frame.

- `sumas(trk)`: las rachas de conducción de un tracking y, por racha y por desfase, las sumas con que se
  calcula la correlación. Son intermedias: no se imprimen.
- `resumen([sumas, ...])`: junta las rachas de uno o varios trackings y da el desfase, su intervalo y lo
  descriptivo.
- `lectura(resumen)`: la lectura de la bitácora §5 para el partido.

`L > 0` es que el balón llega tarde: la velocidad del balón en `t + L` es la que mejor se parece a la del
jugador en `t`.
"""

import numpy as np

from possession import ball

# Fijados antes de medir (bitácora §2); ninguno sale del partido ni de la ventana pública.
RADIO = 1.5  # m: el más cercano lleva el balón (plan §3, tarea 1 de Antonio)
MIN_RACHA = 25  # frames: 1 s o más
DESFASES = np.arange(-25, 26)  # frames
PASO_VEL = 2  # frames a cada lado en la diferencia centrada de la velocidad
MAX_VEL_JUGADOR = 12.0  # m/s: por encima es un intercambio de slot (validation/partido/comun.py)
MAX_VEL_BALON = ball.MAX_SPEED  # m/s
MIN_PARES = 10  # parejas válidas de una racha en un desfase para que cuente
REMUESTREOS = 200
SEMILLA = 20261115
CHUNK = 20000  # frames por bloque al calcular distancias
# Lectura del partido (bitácora §5)
CORTE = 3  # |L̂| ≤ CORTE: no se toca nada
MAX_DIFERENCIA_PARTES = 4  # frames
MAX_ANCHO_INTERVALO = 8  # frames, del percentil 5 al 95
NADA, DESPLAZAR, NO_CONCLUYENTE = "candidato 1", "candidato 2", "no concluyente"


def ids_de_tramo(trk):
    """Por frame, el índice del tramo evaluado al que pertenece, o -1 fuera de los tramos."""
    bid = np.full(len(trk.bx), -1, dtype=np.int64)
    for k, (a, b) in enumerate(trk.blocks):
        bid[a:b] = k
    return bid


def velocidad_balon(trk, bid):
    """(n, 2) con la velocidad del balón en m/s, diferencia centrada de ±PASO_VEL frames.

    NaN si falta un extremo, si los extremos no están en el mismo tramo evaluado que el frame o si pasa de
    MAX_VEL_BALON.
    """
    n, k = len(trk.bx), PASO_VEL
    v = np.full((n, 2), np.nan)
    if n <= 2 * k:
        return v
    bx, by = np.asarray(trk.bx, dtype=np.float64), np.asarray(trk.by, dtype=np.float64)
    escala = trk.fps / (2.0 * k)
    v[k:-k, 0] = (bx[2 * k:] - bx[:-2 * k]) * escala
    v[k:-k, 1] = (by[2 * k:] - by[:-2 * k]) * escala
    mismo = np.zeros(n, dtype=bool)
    mismo[k:-k] = (bid[2 * k:] == bid[k:-k]) & (bid[:-2 * k] == bid[k:-k]) & (bid[k:-k] >= 0)
    with np.errstate(invalid="ignore"):
        malo = ~mismo | ~(np.hypot(v[:, 0], v[:, 1]) <= MAX_VEL_BALON)
    v[malo] = np.nan
    return v


def velocidad_jugador(trk, bid, frames, slots):
    """(k, 2) con la velocidad en m/s del slot `slots[i]` en el frame `frames[i]`, como la del balón, con
    MAX_VEL_JUGADOR."""
    n, k = len(trk.bx), PASO_VEL
    frames, slots = np.asarray(frames, dtype=np.int64), np.asarray(slots, dtype=np.int64)
    v = np.full((len(frames), 2), np.nan)
    ok = (frames - k >= 0) & (frames + k < n)
    f, s = frames[ok], slots[ok]
    escala = trk.fps / (2.0 * k)
    vx = (trk.px[f + k, s].astype(np.float64) - trk.px[f - k, s].astype(np.float64)) * escala
    vy = (trk.py[f + k, s].astype(np.float64) - trk.py[f - k, s].astype(np.float64)) * escala
    mismo = (bid[f + k] == bid[f]) & (bid[f - k] == bid[f]) & (bid[f] >= 0)
    with np.errstate(invalid="ignore"):
        bueno = mismo & (np.hypot(vx, vy) <= MAX_VEL_JUGADOR)
    v[np.flatnonzero(ok)[bueno]] = np.column_stack((vx, vy))[bueno]
    return v


def mas_cercano(trk):
    """(slot, distancia) del slot más cercano al balón en cada frame; slot -1 y distancia infinita si no hay
    balón o no hay jugadores. Con dos a la misma distancia gana el de índice más bajo."""
    n = len(trk.bx)
    slot = np.full(n, -1, dtype=np.int64)
    dist = np.full(n, np.inf)
    vistos = np.flatnonzero(np.isfinite(trk.bx) & np.isfinite(trk.by))
    for inicio in range(0, len(vistos), CHUNK):
        idx = vistos[inicio:inicio + CHUNK]
        dx = trk.px[idx].astype(np.float64) - np.asarray(trk.bx, dtype=np.float64)[idx, None]
        dy = trk.py[idx].astype(np.float64) - np.asarray(trk.by, dtype=np.float64)[idx, None]
        d2 = dx * dx + dy * dy
        d2 = np.where(np.isnan(d2), np.inf, d2)
        mejor = np.argmin(d2, axis=1)
        d = d2[np.arange(len(idx)), mejor]
        hay = np.isfinite(d)
        slot[idx[hay]] = mejor[hay]
        dist[idx[hay]] = np.sqrt(d[hay])
    return slot, dist


def rachas(trk, bid=None):
    """(inicios, fines, slots) de las rachas de conducción (bitácora §2, punto 1), con el fin sin incluir."""
    bid = ids_de_tramo(trk) if bid is None else bid
    slot, dist = mas_cercano(trk)
    clave = np.where((dist <= RADIO) & (bid >= 0), slot, -1)
    n = len(clave)
    if n == 0:
        vacio = np.zeros(0, dtype=np.int64)
        return vacio, vacio, vacio
    corte = np.flatnonzero((clave[1:] != clave[:-1]) | (bid[1:] != bid[:-1])) + 1
    inicios = np.concatenate(([0], corte))
    fines = np.concatenate((corte, [n]))
    buenas = (clave[inicios] >= 0) & (fines - inicios >= MIN_RACHA)
    return inicios[buenas], fines[buenas], clave[inicios[buenas]]


def _sumas_centradas(a, b, racha, n_rachas):
    """Por racha, las sumas centradas (Sab, Saa, Sbb) de las parejas (a, b) de una componente; 0 en las
    rachas con menos de MIN_PARES parejas."""
    cuenta = np.bincount(racha, minlength=n_rachas).astype(np.float64)
    sa = np.bincount(racha, weights=a, minlength=n_rachas)
    sb = np.bincount(racha, weights=b, minlength=n_rachas)
    sab = np.bincount(racha, weights=a * b, minlength=n_rachas)
    saa = np.bincount(racha, weights=a * a, minlength=n_rachas)
    sbb = np.bincount(racha, weights=b * b, minlength=n_rachas)
    con = cuenta >= MIN_PARES
    n = np.where(con, cuenta, 1.0)
    salida = []
    for s2, s1, s1b in ((sab, sa, sb), (saa, sa, sa), (sbb, sb, sb)):
        salida.append(np.where(con, s2 - s1 * s1b / n, 0.0))
    return salida


def sumas(trk):
    """Las rachas de un tracking y sus sumas por racha y desfase. Intermedias: no se imprimen.

    Devuelve un diccionario con:
    - `bloque` (r,): tramo evaluado de cada racha; `largo` (r,): frames de cada racha;
    - `vector` y `modulo`: (Sab, Saa, Sbb), cada una (r, len(DESFASES)), con la velocidad como vector (x e y
      sumadas) o con su módulo;
    - `frames_evaluados`, `frames_con_balon` y `tramos`: recuentos del tracking.
    """
    bid = ids_de_tramo(trk)
    inicios, fines, slots = rachas(trk, bid)
    r = len(inicios)
    largo = fines - inicios
    racha = np.repeat(np.arange(r), largo)
    t = np.concatenate([np.arange(a, b) for a, b in zip(inicios, fines)]) if r else np.zeros(0, np.int64)
    vp = velocidad_jugador(trk, bid, t, np.repeat(slots, largo))
    vb = velocidad_balon(trk, bid)
    forma = (r, len(DESFASES))
    vector = [np.zeros(forma) for _ in range(3)]
    modulo = [np.zeros(forma) for _ in range(3)]
    for j, desfase in enumerate(DESFASES):
        t2 = t + desfase
        dentro = (t2 >= inicios[racha]) & (t2 < fines[racha]) if r else np.zeros(0, bool)
        a = vp[dentro]
        b = vb[t2[dentro]]
        bien = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
        a, b, cual = a[bien], b[bien], racha[dentro][bien]
        for comp in (0, 1):
            for total, parte in zip(vector, _sumas_centradas(a[:, comp], b[:, comp], cual, r)):
                total[:, j] += parte
        for total, parte in zip(modulo, _sumas_centradas(np.hypot(a[:, 0], a[:, 1]), np.hypot(b[:, 0], b[:, 1]),
                                                         cual, r)):
            total[:, j] = parte
    visto = np.isfinite(trk.bx) & np.isfinite(trk.by)
    return {"bloque": bid[inicios] if r else np.zeros(0, np.int64), "largo": largo,
            "vector": tuple(vector), "modulo": tuple(modulo), "tramos": len(trk.blocks),
            "frames_evaluados": int(np.sum(bid >= 0)), "frames_con_balon": int(np.sum(visto & (bid >= 0)))}


def curva(trio, pesos):
    """Correlación por desfase con las rachas pesadas por `pesos`; NaN donde no hay parejas."""
    sab, saa, sbb = (pesos @ m for m in trio)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where((saa > 0) & (sbb > 0), sab / np.sqrt(saa * sbb), np.nan)


def elegir(correlacion):
    """El desfase de la correlación más alta; en un empate, el de menor |L| y después el menor. None si no
    hay ninguna correlación."""
    correlacion = np.asarray(correlacion, dtype=float)
    if not np.isfinite(correlacion).any():
        return None
    maximo = np.nanmax(correlacion)
    orden = np.lexsort((DESFASES, np.abs(DESFASES)))
    for j in orden:
        if correlacion[j] == maximo:
            return int(DESFASES[j])
    return None


def _juntar(lista):
    """Las rachas de varios trackings como si fueran de uno; el bloque se numera aparte en cada tracking."""
    bloque = np.concatenate([s["bloque"] for s in lista])
    trackings = np.concatenate([np.full(len(s["bloque"]), i) for i, s in enumerate(lista)])
    junto = {"bloque": bloque, "tracking": trackings, "largo": np.concatenate([s["largo"] for s in lista])}
    for clave in ("vector", "modulo"):
        junto[clave] = tuple(np.concatenate([s[clave][i] for s in lista]) for i in range(3))
    return junto


def resumen(lista):
    """El desfase de las rachas de uno o varios trackings juntos (bitácora §2). Solo agregados.

    `desfase_por_tramo` va por número de tramo (0, la 1ª parte; 1, la 2ª), con las rachas de todos los
    trackings de ese tramo.
    """
    j = _juntar(lista)
    r = len(j["bloque"])
    unos = np.ones(r)
    cv = curva(j["vector"], unos)
    desfase = elegir(cv)
    rng = np.random.default_rng(SEMILLA)
    remuestreo = []
    if r:
        for _ in range(REMUESTREOS):
            d = elegir(curva(j["vector"], rng.multinomial(r, unos / r).astype(np.float64)))
            if d is not None:
                remuestreo.append(d)
    intervalo = tuple(float(v) for v in np.percentile(remuestreo, [5, 95])) if remuestreo else (None, None)
    tramos = max(s["tramos"] for s in lista)
    por_tramo = [elegir(curva(j["vector"], (j["bloque"] == k).astype(np.float64))) for k in range(tramos)]
    pico = float(cv[list(DESFASES).index(desfase)]) if desfase is not None else None
    return {
        "trackings": len(lista),
        "frames_evaluados": sum(s["frames_evaluados"] for s in lista),
        "frames_con_balon": sum(s["frames_con_balon"] for s in lista),
        "rachas": r,
        "frames_en_rachas": int(j["largo"].sum()),
        "rachas_por_tramo": [int(np.sum(j["bloque"] == k)) for k in range(tramos)],
        "desfase": desfase,
        "intervalo": intervalo,
        "correlacion_pico": pico,
        "correlacion": {int(d): (float(c) if np.isfinite(c) else None) for d, c in zip(DESFASES, cv)},
        "desfase_por_tramo": por_tramo,
        "desfase_modulo": elegir(curva(j["modulo"], unos)),
    }


def lectura(res):
    """(candidato, por qué) según la bitácora §5. Para el partido: sus dos partes son los dos tramos."""
    d, (p5, p95), partes = res["desfase"], res["intervalo"], res["desfase_por_tramo"]
    if d is None or p5 is None or any(p is None for p in partes):
        return NO_CONCLUYENTE, "no hay rachas suficientes para medir el desfase (en el total o en alguna parte)"
    if partes and max(partes) - min(partes) > MAX_DIFERENCIA_PARTES:
        return NO_CONCLUYENTE, "las partes se separan {} frames, más de {}".format(
            max(partes) - min(partes), MAX_DIFERENCIA_PARTES)
    if p95 - p5 > MAX_ANCHO_INTERVALO:
        return NO_CONCLUYENTE, "el intervalo del 5 al 95 % mide {:g} frames, más de {}".format(
            p95 - p5, MAX_ANCHO_INTERVALO)
    if abs(d) <= CORTE:
        return NADA, "|L̂| = {} ≤ {}: no se toca nada".format(abs(d), CORTE)
    return DESPLAZAR, "|L̂| = {} ≥ {}: variante en possession/ball.py que {} el balón {} frames".format(
        abs(d), CORTE + 1, "adelanta" if d > 0 else "retrasa", abs(d))


# -- herramientas de la calibración (calibrar_dfl.py y la prueba) ----------------------------------------

def media_atras(valores, ancho):
    """Media de los `ancho` frames que acaban en cada frame (el suyo incluido), ignorando los NaN; NaN si no
    hay ninguno. Con 25 frames, su centro queda 12 frames atrás."""
    valores = np.asarray(valores, dtype=float)
    hay = ~np.isnan(valores)
    suma = np.concatenate(([0.0], np.cumsum(np.where(hay, valores, 0.0))))
    cuenta = np.concatenate(([0], np.cumsum(hay)))
    indice = np.arange(len(valores))
    bajo = np.maximum(0, indice - ancho + 1)
    alto = indice + 1
    n = cuenta[alto] - cuenta[bajo]
    return np.where(n > 0, (suma[alto] - suma[bajo]) / np.maximum(n, 1), np.nan)


def desplazar(valores, frames):
    """Copia de `valores` retrasada `frames` frames (adelantada si es negativo): salida[t] = valores[t − frames],
    con NaN donde no hay de dónde sacar el valor."""
    valores = np.asarray(valores, dtype=float)
    salida = np.full(len(valores), np.nan)
    if frames >= 0:
        salida[frames:] = valores[:len(valores) - frames]
    else:
        salida[:frames] = valores[-frames:]
    return salida
