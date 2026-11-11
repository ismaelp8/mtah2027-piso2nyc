"""Medidas de 2c, 2d, 2e y 2g del experimento 0 sobre una parte de un partido de la Bundesliga.

Funciones puras de numpy, para poder probarlas con datos sintéticos (`pruebas_sinteticas.py`) antes de
pasarles datos reales. Las definiciones son las fijadas en la bitácora antes de medir:

- toque: cambio de velocidad del balón de `umbral_toque` m/s o más entre la media de los frames
  t+1…t+4 y la de los t−3…t, en un máximo local de ±4 frames, atribuido al equipo del jugador más
  cercano si está a `radio_toque` m o menos;
- control: rachas de `frames_control` frames o más en las que el mismo jugador es el más cercano al
  balón y está a `radio` m o menos;
- retención: rachas de `frames_retencion` frames o más en las que el más cercano es del mismo equipo y
  está a `radio` m o menos.

Equipos: 0 = local (`BallPossession` 1), 1 = visitante (`BallPossession` 2).
"""

import numpy as np

FPS = 25
PARAMETROS = {
    "radio": 1.0, "frames_control": 12, "frames_retencion": 5, "umbral_toque": 3.0, "radio_toque": 1.5,
    "ventana_antes": 25, "ventana_despues": 50, "ventana_momento": 50, "radio_aire": 2.0,
    "velocidad_aire": 5.0, "margen_fuera": 0.5, "ventana_cobertura": 125, "ventana_reanudar": 75,
    "radio_cercania": 1.5, "ventana_cercania": 25, "ventana_toque": 50, "margen_placebo": 50,
    "max_placebo": 1000,  # por parte: hasta 2.000 por partido, como se fijó
    # Añadido en la parada 3 al ver que el balón se congela mientras el flag dice inactivo: si es True,
    # toques, controles, retenciones y contactos solo usan frames con el balón en juego.
    "solo_activos": False,
}


# -- preparación -----------------------------------------------------------------------------------

def preparar(parte):
    """Velocidades del balón y distancias a los jugadores de una parte (dict de la caché)."""
    x, y = np.asarray(parte["x"], float), np.asarray(parte["y"], float)
    n = len(x)
    vx = np.zeros(n)
    vy = np.zeros(n)
    vx[1:] = np.diff(x) * FPS
    vy[1:] = np.diff(y) * FPS
    if n > 1:
        vx[0], vy[0] = vx[1], vy[1]
    v = np.full(n, np.nan)
    if n > 4:
        v[2:-2] = np.hypot(x[4:] - x[:-4], y[4:] - y[:-4]) / (4.0 / FPS)
    cols_x = np.concatenate([parte["equipos"]["local"]["x"], parte["equipos"]["visitante"]["x"]], axis=1)
    cols_y = np.concatenate([parte["equipos"]["local"]["y"], parte["equipos"]["visitante"]["y"]], axis=1)
    equipo_col = np.concatenate([np.zeros(parte["equipos"]["local"]["x"].shape[1], int),
                                 np.ones(parte["equipos"]["visitante"]["x"].shape[1], int)])
    dist = np.hypot(cols_x - x[:, None], cols_y - y[:, None])
    dist = np.where(np.isnan(dist), np.inf, dist)
    orden = np.argsort(dist, axis=1, kind="stable")
    cercano = orden[:, 0]
    d1 = dist[np.arange(n), cercano]
    d2 = dist[np.arange(n), orden[:, 1]] if dist.shape[1] > 1 else np.full(n, np.inf)
    d_equipo = np.stack([np.min(np.where(equipo_col[None, :] == k, dist, np.inf), axis=1) for k in (0, 1)])
    return {"n": n, "x": x, "y": y, "z": np.asarray(parte.get("z", np.zeros(n)), float), "vx": vx, "vy": vy,
            "v": v, "cercano": cercano, "equipo_cercano": equipo_col[cercano], "d1": d1, "d2": d2,
            "d_equipo": d_equipo, "equipo_col": equipo_col}


def rachas(clave, minimo):
    """[(inicio, fin_exclusivo, valor)] de las rachas de un mismo valor >= 0 con al menos `minimo` frames."""
    clave = np.asarray(clave)
    if not len(clave):
        return []
    cortes = np.flatnonzero(clave[1:] != clave[:-1]) + 1
    inicios = np.concatenate(([0], cortes))
    fines = np.concatenate((cortes, [len(clave)]))
    return [(int(a), int(b), int(clave[a])) for a, b in zip(inicios, fines) if clave[a] >= 0 and b - a >= minimo]


def controles(prep, radio, minimo):
    """[(inicio, fin, equipo, columna)]: el mismo jugador, el más cercano, a `radio` m o menos."""
    clave = np.where(prep["d1"] <= radio, prep["cercano"], -1)
    return [(a, b, int(prep["equipo_col"][c]), c) for a, b, c in rachas(clave, minimo)]


def retenciones(prep, radio, minimo):
    """[(inicio, fin, equipo)]: el más cercano es del mismo equipo y está a `radio` m o menos."""
    clave = np.where(prep["d1"] <= radio, prep["equipo_cercano"], -1)
    return rachas(clave, minimo)


def toques(prep, umbral, radio):
    """(frames, equipo o -1, dv) de los toques: máximos locales del cambio de velocidad."""
    vx, vy, n = prep["vx"], prep["vy"], prep["n"]
    if n < 10:
        return np.array([], int), np.array([], int), np.array([])
    cx, cy = np.concatenate(([0.0], np.cumsum(vx))), np.concatenate(([0.0], np.cumsum(vy)))
    t = np.arange(3, n - 4)
    antes_x, antes_y = (cx[t + 1] - cx[t - 3]) / 4, (cy[t + 1] - cy[t - 3]) / 4
    despues_x, despues_y = (cx[t + 5] - cx[t + 1]) / 4, (cy[t + 5] - cy[t + 1]) / 4
    dv = np.zeros(n)
    dv[t] = np.hypot(despues_x - antes_x, despues_y - antes_y)
    rel = np.lib.stride_tricks.sliding_window_view(np.pad(dv, 4, constant_values=-1), 9).max(axis=1)
    candidatos = np.flatnonzero((dv >= umbral) & (dv >= rel))
    elegidos = []
    for c in candidatos:
        if not elegidos or c - elegidos[-1] > 4:
            elegidos.append(int(c))
    elegidos = np.array(elegidos, int)
    equipo = np.where(prep["d1"][elegidos] <= radio, prep["equipo_cercano"][elegidos], -1) if len(elegidos) else \
        np.array([], int)
    return elegidos, equipo.astype(int), dv[elegidos]


def toques_en_juego(t_toq, eq_toq, estado):
    """Quita los toques cuya ventana (t−4…t+5) toca algún frame con el balón inactivo.

    Con el balón congelado durante `D`, la parada y el salto al reanudar parecen toques.
    """
    estado = np.asarray(estado)
    n = len(estado)
    inactivos = np.concatenate(([0], np.cumsum(estado != 1)))
    lo, hi = np.clip(t_toq - 4, 0, n), np.clip(t_toq + 6, 0, n)
    ok = inactivos[hi] - inactivos[lo] == 0
    return t_toq[ok], eq_toq[ok]


def movimiento_jugadores(parte):
    """Por frame (desde el 1): si ningún jugador se ha movido respecto al anterior, y su velocidad media (m/s)."""
    px = np.concatenate([parte["equipos"]["local"]["x"], parte["equipos"]["visitante"]["x"]], axis=1).astype(float)
    py = np.concatenate([parte["equipos"]["local"]["y"], parte["equipos"]["visitante"]["y"]], axis=1).astype(float)
    d = np.hypot(np.diff(px, axis=0), np.diff(py, axis=0))
    validos = ~np.isnan(d)
    hay = validos.any(axis=1)
    d0 = np.where(validos, d, 0.0)
    quietos = hay & (d0.max(axis=1) == 0)
    vel = np.where(hay, d0.sum(axis=1) / np.maximum(validos.sum(axis=1), 1) * FPS, np.nan)
    return quietos, vel


def cambios(estado, poss):
    """(frames f, equipo nuevo, equipo anterior) de los cambios H↔A con el balón activo en f−1 y f."""
    estado, poss = np.asarray(estado), np.asarray(poss)
    f = np.flatnonzero((estado[1:] == 1) & (estado[:-1] == 1) & (poss[1:] != poss[:-1])) + 1
    return f, (poss[f] - 1).astype(int), (poss[f - 1] - 1).astype(int)


# -- medidas de una parte ----------------------------------------------------------------------------

def _por_equipo(segs):
    """{equipo: (inicios, fines)} como arrays, para buscar solapes rápido."""
    return {k: (np.array([s[0] for s in segs if s[2] == k], int), np.array([s[1] for s in segs if s[2] == k], int))
            for k in (0, 1)}


def _solapa(arrs, a, b):
    """¿Algún intervalo [inicio, fin) de `arrs` se solapa con [a, b)?"""
    ini, fin = arrs
    return bool(np.any((ini < b) & (fin > a)))


def grupos_cambio(f, nuevo, segs_control, d_equipo, radio, antes, despues):
    """'control', 'toque' o 'nada' para cada cambio, mirando del frame f−antes al f+despues."""
    por_equipo = _por_equipo(segs_control)
    n = d_equipo.shape[1]
    salida = []
    for fi, y_eq in zip(f, nuevo):
        a, b = max(0, fi - antes), min(n, fi + despues + 1)
        if _solapa(por_equipo[int(y_eq)], a, b):
            salida.append("control")
        elif np.any(d_equipo[y_eq, a:b] <= radio):
            salida.append("toque")
        else:
            salida.append("nada")
    return salida


def momento_control(f, nuevo, segs_control, ventana):
    """Desfase (frames) entre el cambio y el inicio del control del equipo nuevo más cercano en ±ventana."""
    por_equipo = {k: np.array([s[0] for s in segs_control if s[2] == k], int) for k in (0, 1)}
    salida = []
    for fi, y_eq in zip(f, nuevo):
        inicios = por_equipo[int(y_eq)]
        cerca = inicios[np.abs(inicios - fi) <= ventana]
        salida.append(int(cerca[np.argmin(np.abs(cerca - fi))] - fi) if len(cerca) else None)
    return salida


def frames_placebo(estado, poss, f_cambios, rng, maximo, antes, despues, margen=None):
    """Frames activos al azar, lejos de los cambios, con el balón activo y el mismo flag en su ventana.

    El balón está activo de g − antes a g + despues y no hay ningún cambio a ±margen frames.
    """
    n = len(estado)
    margen = max(antes, despues) if margen is None else margen
    borde = max(antes, despues, margen)
    g = np.arange(borde, n - borde)
    # balón activo en toda la ventana [g − antes, g + despues] y ningún cambio a ±margen
    muertos = np.concatenate(([0], np.cumsum(np.asarray(estado) != 1)))
    marcas = np.zeros(n, int)
    marcas[np.asarray(f_cambios, int)] = 1
    cambios_acum = np.concatenate(([0], np.cumsum(marcas)))
    ok = (muertos[g + despues + 1] - muertos[g - antes] == 0) & \
         (cambios_acum[g + margen + 1] - cambios_acum[g - margen] == 0)
    candidatos = g[ok]
    if len(candidatos) > maximo:
        candidatos = np.sort(rng.choice(candidatos, size=maximo, replace=False))
    return candidatos


def toques_sin_control(t_toques, eq_toques, segs_control, estado, poss, z, ventana=125, propio=False):
    """2g: toques del rival sin control y si el flag pasa a ese rival antes del siguiente control propio.

    Devuelve una lista de dicts, uno por toque:
    - `t`, `equipo`: frame y equipo del toque; `aereo`: balón a más de 1,5 m de altura;
    - `cambia`: el flag marca al otro equipo (el que no tiene los controles) entre el toque y el siguiente
      control; `desfase`: frames desde el toque hasta el primer frame así (None si no lo hay);
    - `x_antes`: el flag marca al equipo de los controles 3 frames antes del toque;
    - `duracion`: frames seguidos con el flag en el otro equipo desde ese primer frame;
    - `hueco`: inicio del control anterior, para contar por hueco entre controles y no por toque.

    Con `propio=True` es el placebo: toques sin control del mismo equipo que tiene los dos controles, y
    si el flag pasa al otro equipo entre el toque y el siguiente control.
    """
    segs = sorted(segs_control)
    inicios = np.array([s[0] for s in segs], int)
    fines = np.array([s[1] for s in segs], int)
    salida = []
    for t, y_eq in zip(t_toques, eq_toques):
        if y_eq < 0 or estado[t] != 1:
            continue
        if np.any((inicios <= t) & (fines > t)):
            continue  # el toque está dentro de un control
        prev = np.flatnonzero(fines <= t)
        sig = np.flatnonzero(inicios > t)
        if not len(prev) or not len(sig):
            continue
        p, s = segs[prev[-1]], segs[sig[0]]
        if t - p[1] > ventana or s[0] - t > ventana:
            continue
        if p[2] != s[2] or (p[2] == y_eq) != propio:
            continue
        if np.any(np.asarray(estado[t:s[0] + 1]) != 1):
            continue  # hay un D entre medias: va a "posesiones cortas antes de un D"
        otro = 1 - p[2]
        marca = np.flatnonzero(np.asarray(poss[t:s[0] + 1]) - 1 == otro)
        duracion = None
        if len(marca):
            m = t + int(marca[0])
            fin = m
            while fin < len(poss) and poss[fin] - 1 == otro and estado[fin] == 1:
                fin += 1
            duracion = int(fin - m)
        salida.append({"t": int(t), "equipo": int(y_eq), "cambia": bool(len(marca)), "aereo": bool(z[t] > 1.5),
                       "desfase": int(marca[0]) if len(marca) else None,
                       "x_antes": bool(poss[max(0, t - 3)] - 1 == p[2]), "duracion": duracion, "hueco": int(p[0])})
    return salida


def por_hueco(casos):
    """Un valor por hueco entre controles: si algún toque del hueco cambió el flag."""
    huecos = {}
    for c in casos:
        huecos[c["hueco"]] = huecos.get(c["hueco"], False) or c["cambia"]
    return list(huecos.values())


def fuera(x, y, margen, largo=105.0, ancho=68.0):
    return (np.abs(x) > largo / 2 + margen) | (np.abs(y) > ancho / 2 + margen)


def emparejar(eventos, fines, ventana):
    """Emparejamiento uno a uno y en orden: cada evento con el fin libre más cercano en ±ventana."""
    usados = set()
    desfases = []
    for e in sorted(eventos):
        mejor = None
        for j, fi in enumerate(fines):
            if j in usados or abs(e - fi) > ventana:
                continue
            if mejor is None or abs(e - fi) < abs(e - fines[mejor]):
                mejor = j
        if mejor is None:
            desfases.append(None)
        else:
            usados.add(mejor)
            desfases.append(int(e - fines[mejor]))
    return desfases, usados


def medir_parte(parte, prm, rng, eventos_parte=None, prep=None, campo=(105.0, 68.0)):
    """Todas las medidas de una parte. `eventos_parte`: [(tipo, frame)] de reinicios (para 1a).

    `prep` (lo que devuelve `preparar`) no depende de los parámetros: se puede calcular una vez y pasarlo.
    """
    estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
    prep = preparar(parte) if prep is None else prep
    n = prep["n"]
    largo, ancho = campo
    t_toq, eq_toq, _ = toques(prep, prm["umbral_toque"], prm["radio_toque"])
    if prm.get("solo_activos"):
        activo = estado == 1
        prep = dict(prep)
        prep["d1"] = np.where(activo, prep["d1"], np.inf)
        prep["d_equipo"] = np.where(activo[None, :], prep["d_equipo"], np.inf)
        t_toq, eq_toq = toques_en_juego(t_toq, eq_toq, estado)
    segs = controles(prep, prm["radio"], prm["frames_control"])
    rets = retenciones(prep, prm["radio"], prm["frames_retencion"])
    f, nuevo, viejo = cambios(estado, poss)
    r = {"cambios": int(len(f)), "toques": int(len(t_toq)), "toques_atribuidos": int(np.sum(eq_toq >= 0)),
         "controles": int(len(segs)), "minutos_vivos": float(np.sum(estado == 1)) / FPS / 60}
    # 2b: grupos y retención
    r["grupos"] = grupos_cambio(f, nuevo, segs, prep["d_equipo"], prm["radio"], prm["ventana_antes"],
                                prm["ventana_despues"])
    rets_eq = _por_equipo(rets)
    segs_eq = _por_equipo(segs)
    r["con_retencion"] = [g != "nada" and _solapa(rets_eq[int(y)], max(0, fi - prm["ventana_antes"]),
                                                   min(n, fi + prm["ventana_despues"] + 1))
                          for fi, y, g in zip(f, nuevo, r["grupos"])]
    # 2c: momento (con el control, criterio vigente; con la retención, criterio original)
    r["momento"] = momento_control(f, nuevo, segs, prm["ventana_momento"])
    r["momento_retencion"] = momento_control(f, nuevo, rets, prm["ventana_momento"])
    # medidas de PASOS.md 2c
    r["d_nuevo_en_cambio"] = [float(prep["d_equipo"][y, fi]) for fi, y in zip(f, nuevo)]
    r["d_viejo_en_cambio"] = [float(prep["d_equipo"][x, fi]) for fi, x in zip(f, viejo)]
    w = prm["ventana_cercania"]
    r["nuevo_cerca_1s"] = [bool(np.any(prep["d_equipo"][y, max(0, fi - w):fi + w + 1] <= prm["radio_cercania"]))
                           for fi, y in zip(f, nuevo)]
    wt = prm["ventana_toque"]

    def desfase_toque(fi, eq):
        sel = t_toq[(eq_toq == eq) & (np.abs(t_toq - fi) <= wt)]
        return int(sel[np.argmin(np.abs(sel - fi))] - fi) if len(sel) else None
    r["desfase_toque"] = [desfase_toque(fi, y) for fi, y in zip(f, nuevo)]
    # 3a: en el aire
    r["en_el_aire"] = [bool(prep["d1"][fi] > prm["radio_aire"] and prep["v"][fi] > prm["velocidad_aire"])
                       for fi in f]
    # placebo
    g_pl = frames_placebo(estado, poss, f, rng, prm["max_placebo"], max(prm["ventana_antes"], prm["ventana_momento"], wt),
                          max(prm["ventana_despues"], prm["ventana_momento"], wt), prm["margen_placebo"])
    flag_pl = (poss[g_pl] - 1).astype(int) if len(g_pl) else np.array([], int)
    otro_pl = 1 - flag_pl
    r["placebo_n"] = int(len(g_pl))
    r["placebo_control_otro"] = [g == "control" for g in grupos_cambio(g_pl, otro_pl, segs, prep["d_equipo"], prm["radio"],
                                                                       prm["ventana_antes"], prm["ventana_despues"])]
    r["placebo_control_flag"] = [g == "control" for g in grupos_cambio(g_pl, flag_pl, segs, prep["d_equipo"], prm["radio"],
                                                                       prm["ventana_antes"], prm["ventana_despues"])]
    r["placebo_retencion_otro"] = [_solapa(rets_eq[int(o)], max(0, g - prm["ventana_antes"]), g + prm["ventana_despues"] + 1)
                                   for g, o in zip(g_pl, otro_pl)]
    r["placebo_retencion_flag"] = [_solapa(rets_eq[int(k)], max(0, g - prm["ventana_antes"]), g + prm["ventana_despues"] + 1)
                                   for g, k in zip(g_pl, flag_pl)]
    r["placebo_cerca_otro"] = [bool(np.any(prep["d_equipo"][o, max(0, g - w):g + w + 1] <= prm["radio_cercania"]))
                               for g, o in zip(g_pl, otro_pl)]
    r["placebo_cerca_flag"] = [bool(np.any(prep["d_equipo"][k, max(0, g - w):g + w + 1] <= prm["radio_cercania"]))
                               for g, k in zip(g_pl, flag_pl)]
    r["placebo_desfase_toque_otro"] = [desfase_toque(g, o) for g, o in zip(g_pl, otro_pl)]
    # 2g
    r["toques_sin_control"] = toques_sin_control(t_toq, eq_toq, segs, estado, poss, prep["z"])
    r["toques_propios_sin_control"] = toques_sin_control(t_toq, eq_toq, segs, estado, poss, prep["z"], propio=True)
    r["huecos_2g"] = por_hueco(r["toques_sin_control"])
    r["huecos_2g_placebo"] = por_hueco(r["toques_propios_sin_control"])
    # 1b: balón fuera durante 1 s o más
    fu = fuera(prep["x"], prep["y"], prm["margen_fuera"], largo, ancho)
    frames_fuera = [(a, b) for a, b, val in rachas(fu.astype(int), FPS) if val == 1]
    total_fuera = sum(b - a for a, b in frames_fuera)
    activos_fuera = sum(int(np.sum(estado[a:b] == 1)) for a, b in frames_fuera)
    r["fuera_frames"], r["fuera_activos"] = int(total_fuera), int(activos_fuera)
    # lo mismo sin depender del balón congelado en D: frames activos fuera y episodios de 1 s o más
    fuera_y_activo = fu & (estado == 1)
    r["fuera_activo_frames_todos"] = int(np.sum(fuera_y_activo))
    r["fuera_activo_episodios"] = [b - a for a, b, val in rachas(fuera_y_activo.astype(int), FPS) if val == 1]
    # 2d: pasos a inactivo
    inicios_d = np.flatnonzero((estado[1:] == 0) & (estado[:-1] == 1)) + 1
    fines_d = np.flatnonzero((estado[1:] == 1) & (estado[:-1] == 0)) + 1
    fu0 = fuera(prep["x"], prep["y"], 0.0, largo, ancho)
    pasos = []
    for o in inicios_d:
        a = max(0, o - prm["ventana_reanudar"])
        ventana_fuera = np.flatnonzero(fu0[a:o + 1])
        if len(ventana_fuera):
            # inicio de la última racha fuera dentro de la ventana
            ult = a + ventana_fuera[-1]
            c = ult
            while c - 1 >= a and fu0[c - 1]:
                c -= 1
            desfase = int(o - c)
            ref = c
        else:
            desfase, ref = None, o
        ex, ey = abs(prep["x"][ref]) - largo / 2, abs(prep["y"][ref]) - ancho / 2
        tipo = "dentro" if (ex <= 0 and ey <= 0) else ("fondo" if ex > ey else "banda")
        fin = fines_d[fines_d > o]
        dur = int(fin[0] - o) if len(fin) else None
        # en el inicio del D: > 0 fuera; < 0 dentro, a esa distancia de la línea más cercana
        dist_linea = float(max(abs(prep["x"][o]) - largo / 2, abs(prep["y"][o]) - ancho / 2))
        # flag durante el D: si es constante y si es el mismo que en el último frame activo
        flag_d = poss[o:fin[0]] if len(fin) else poss[o:]
        pasos.append({"fuera_en_inicio": bool(fu0[o]), "dist_linea": dist_linea, "desfase_cruce": desfase,
                      "tipo": tipo, "duracion": dur, "flag_constante": bool(np.all(flag_d == flag_d[0])),
                      "flag_igual_al_anterior": bool(poss[o] == poss[o - 1])})
    r["pasos_a_inactivo"] = pasos
    # balón congelado en D: frames inactivos con la misma posición que el frame anterior
    quieto = np.zeros(n, bool)
    quieto[1:] = (np.diff(prep["x"]) == 0) & (np.diff(prep["y"]) == 0)
    r["frames_d"] = int(np.sum(estado[1:] != 1))
    r["frames_d_quietos"] = int(np.sum(quieto[1:] & (estado[1:] != 1)))
    # 2e: pasos a activo
    reanudar = []
    for e in fines_d:
        a, b = max(0, e - prm["ventana_reanudar"]), min(n, e + prm["ventana_reanudar"] + 1)
        mov = np.flatnonzero(np.nan_to_num(prep["v"][a:b]) > 2.0)
        lag = int(a + mov[0] - e) if len(mov) else None
        # con el balón congelado en D, la velocidad centrada salta siempre en e − 2; esta otra solo usa
        # frames activos: primer t >= e con (p[t+1] − p[t]) · 25 > 2 m/s
        avance = np.hypot(np.diff(prep["x"][e:b]), np.diff(prep["y"][e:b])) * FPS
        mov2 = np.flatnonzero(avance > 2.0)
        reanudar.append({"desfase_movimiento": lag, "desfase_movimiento_activo": int(mov2[0]) if len(mov2) else None,
                         "mismo_equipo": bool(poss[e - 1] == poss[e]),
                         "salto": float(np.hypot(prep["x"][e] - prep["x"][e - 1], prep["y"][e] - prep["y"][e - 1])),
                         # jugador del equipo del flag más cercano al balón en el primer frame activo
                         "d_flag": float(prep["d_equipo"][int(poss[e]) - 1, e])})
    r["pasos_a_activo"] = reanudar
    # posesiones cortas junto a un D
    lab = np.where(estado == 0, 2, poss - 1)  # 0 local, 1 visitante, 2 D
    runs = rachas(lab, 1)
    antes_d, despues_d, entre_dos_d = [], [], 0
    for i, (a, b, val) in enumerate(runs):
        if val == 2 or b - a >= FPS or i == 0 or i == len(runs) - 1:
            continue
        prev_v, sig_v = runs[i - 1][2], runs[i + 1][2]
        if prev_v == 2 and sig_v == 2:
            entre_dos_d += 1
            continue
        toq = bool(np.any((t_toq >= a - 5) & (t_toq < b) & (eq_toq == val)))
        ctrl = _solapa(segs_eq[val], a, b)
        if sig_v == 2 and prev_v != 2:
            o = b
            c0 = max(0, o - prm["ventana_reanudar"])
            salio = bool(fu0[o] or np.any(fu0[c0:o + 1]))
            reanuda = runs[i + 2][2] if i + 2 < len(runs) and runs[i + 2][2] != 2 else None
            antes_d.append({"toque": toq, "control": ctrl, "fuera": salio,
                            "reanuda_el_otro": None if reanuda is None else bool(reanuda != val)})
        elif prev_v == 2 and sig_v != 2:
            toq2 = bool(np.any((t_toq >= a - 5) & (t_toq <= a + FPS) & (eq_toq == val)))
            despues_d.append({"toque": toq2, "control": ctrl})
    r["cortas_antes_de_D"], r["cortas_despues_de_D"] = antes_d, despues_d
    r["cortas_entre_dos_D"] = entre_dos_d
    # 1a: cobertura de reinicios
    if eventos_parte is not None:
        cob = {}
        frames_ev = [ev[1] for ev in eventos_parte]
        desf, usados = emparejar(frames_ev, list(fines_d), prm["ventana_cobertura"])
        orden = sorted(range(len(eventos_parte)), key=lambda i: eventos_parte[i][1])
        emparejados = []
        for k, i in enumerate(orden):
            cob.setdefault(eventos_parte[i][0], []).append(desf[k])
            if desf[k] is not None:
                fin = int(eventos_parte[i][1] - desf[k])
                eq_ev = eventos_parte[i][2] if len(eventos_parte[i]) > 2 else -1
                flag = int(poss[fin]) - 1
                emparejados.append({"tipo": eventos_parte[i][0], "d_flag": float(prep["d_equipo"][flag, fin]),
                                    "equipo_coincide": None if eq_ev < 0 else bool(eq_ev == flag)})
        r["reinicios_emparejados"] = emparejados
        r["cobertura"] = cob
        r["fines_d"] = int(len(fines_d))
        r["fines_d_emparejados"] = int(len(usados))
        r["fines_d_sin_reinicio"] = [int(fines_d[j]) for j in range(len(fines_d)) if j not in usados]
        # placebo: el mismo número de instantes, al azar en la parte
        aleatorios = list(rng.integers(0, n, size=len(frames_ev)))
        desf_pl, _ = emparejar(aleatorios, list(fines_d), prm["ventana_cobertura"])
        r["cobertura_placebo"] = [d is not None for d in desf_pl]
    return r
