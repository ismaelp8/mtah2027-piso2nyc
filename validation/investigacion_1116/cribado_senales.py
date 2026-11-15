"""Sondeo S7: cribado de señales del propio tracking, medidas todas igual, donde fallamos.

    python validation/investigacion_1116/cribado_senales.py            # DFL y SkillCorner
    python validation/investigacion_1116/cribado_senales.py --solo dfl

Datos abiertos de otros partidos: los 7 de la DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de
SkillCorner (licencia MIT). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. La regla de
lectura y la definición de cada señal están en BITACORA.md (S7), escritas antes de medir. Descriptivo.
"""

import argparse
import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"), ROOT,
                os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, carpeta)
import dfl  # noqa: E402
import lector as lc  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline  # noqa: E402

H, A, D, X = dfl.H, dfl.A, dfl.D, dfl.X
VERSIONES = os.path.join(ROOT, "validation", "harness", "versiones", "investigacion_costes_2026-11-16.json")
RETRASO = 4
PASO = 5  # uno de cada PASO frames de juego para entrenar la regresión
AREA_FONDO, AREA_MEDIA = 16.5, 20.16
EQUIPO = ["R1 más cercano (N1)", "R2 dirección del balón (B9)", "R3 signo de B5",
          "S1 diferencia de distancias > 1 m", "S2 los dos más cercanos, mismo equipo", "S3 mayoría a 3 m",
          "S4 mayoría a 5 m", "S5 mayoría a 10 m", "S6 llega antes (control del campo)", "S7 el que más se acerca",
          "S8 pegado 12 frames a 2 m (circular con control)", "S9 balón lento junto a un jugador",
          "S10 se mueve con el balón", "S11 el balón frena junto a un jugador", "S12 más cercano presionado",
          "S13 más cercano libre", "S14 dos contactos seguidos (circular con control)", "S15 el más ancho",
          "S16 el más largo", "S17 el de más área", "S18 línea defensiva más alta",
          "S19 por detrás del balón (el otro defiende)", "S20 sin balón: se queda el último",
          "S21 el balón desaparece junto al portero"]
MUERTO = ["D1 jugadores lentos", "D2 frenazo colectivo", "D3 arranque colectivo", "D4 jugador fuera junto a la línea",
          "D5 muchos en el área y quietos"]


# -- utilidades ------------------------------------------------------------------------------------------

def velocidad(x, y, lag, fps, vmax=None):
    """Velocidad centrada en ±lag frames (vx, vy), NaN en los bordes, donde falta algo o si pasa de vmax."""
    vx, vy = np.full(x.shape, np.nan), np.full(y.shape, np.nan)
    if len(x) <= 2 * lag:
        return vx, vy
    escala = fps / (2.0 * lag)
    vx[lag:-lag] = (x[2 * lag:] - x[:-2 * lag]) * escala
    vy[lag:-lag] = (y[2 * lag:] - y[:-2 * lag]) * escala
    if vmax is not None:
        with np.errstate(invalid="ignore"):
            malo = np.hypot(vx, vy) > vmax
        vx[malo], vy[malo] = np.nan, np.nan
    return vx, vy


def media_ventana(v, atras, delante):
    """Media de v (NaN no cuenta) entre t−atras y t+delante."""
    ok = np.isfinite(v)
    s = np.concatenate(([0.0], np.cumsum(np.where(ok, v, 0.0))))
    c = np.concatenate(([0], np.cumsum(ok)))
    i = np.arange(len(v))
    lo, hi = np.maximum(0, i - atras), np.minimum(len(v), i + delante + 1)
    n = c[hi] - c[lo]
    return np.where(n > 0, (s[hi] - s[lo]) / np.maximum(n, 1), np.nan)


def arrastrar(evento, largo):
    """Cada frame toma el último evento (≥ 0) de los `largo` frames anteriores, él incluido; −1 si no hay."""
    idx = np.where(evento >= 0, np.arange(len(evento)), -1)
    ultimo = np.maximum.accumulate(idx)
    ok = (ultimo >= 0) & (np.arange(len(evento)) - ultimo < largo)
    return np.where(ok, evento[np.maximum(ultimo, 0)], -1)


def rachas(m):
    b = np.diff(np.concatenate(([0], m.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(b == 1), np.flatnonzero(b == -1)))


def a_signo(equipo):
    """0 (`H`) → +1, 1 (`A`) → −1, otro → 0."""
    return np.where(equipo == H, 1, np.where(equipo == A, -1, 0)).astype(np.int8)


# -- las señales de un tramo -----------------------------------------------------------------------------

def senales_tramo(trk, a, b):
    """{nombre: opinión int8 (+1 `H`, −1 `A`, 0 nada)} para las de equipo, y {nombre: +1 `D`, −1 juego, 0} para
    las de balón muerto, en los frames [a, b)."""
    fps = float(trk.fps)
    largo, ancho = float(trk.pitch[0]), float(trk.pitch[1])
    bx = np.asarray(trk.bx[a:b], dtype=np.float64)
    by = np.asarray(trk.by[a:b], dtype=np.float64)
    vis = np.isfinite(bx) & np.isfinite(by)
    team = np.asarray(trk.team)
    n = b - a
    eq = []
    for k in (H, A):
        c = np.flatnonzero(team == k)
        x = trk.px[a:b][:, c].astype(np.float64)
        y = trk.py[a:b][:, c].astype(np.float64)
        eq.append((x, y, np.isfinite(x) & np.isfinite(y)))
    (xh, yh, hh), (xa, ya, ha) = eq
    direccion = float(np.sign(np.nanmean(np.where(ha, xa, np.nan)) - np.nanmean(np.where(hh, xh, np.nan))))
    if direccion == 0:
        direccion = 1.0
    # distancia a la portería propia: el local ataca hacia +x si direccion = +1
    propia = [lambda x: x if direccion > 0 else largo - x, lambda x: largo - x if direccion > 0 else x]
    out = {}

    # distancias al balón
    dist = []
    for x, y, hay in eq:
        d = np.hypot(x - bx[:, None], y - by[:, None])
        dist.append(np.where(hay & vis[:, None], d, np.inf))
    dh, da = dist
    mh = dh.min(axis=1) if dh.shape[1] else np.full(n, np.inf)
    ma = da.min(axis=1) if da.shape[1] else np.full(n, np.inf)
    cercano = np.where(np.isfinite(np.minimum(mh, ma)), np.where(mh <= ma, H, A), -1)
    dmin = np.minimum(mh, ma)
    out["R1 más cercano (N1)"] = a_signo(cercano)
    out["R2 dirección del balón (B9)"] = aprendida.direccion_del_balon(bx, eq, fps).astype(np.int8)
    with np.errstate(invalid="ignore"):
        out["S1 diferencia de distancias > 1 m"] = np.where(
            (dmin < 10) & (np.abs(ma - mh) > 1) & np.isfinite(dmin), np.where(mh < ma, 1, -1), 0).astype(np.int8)
    todos = np.concatenate([dh, da], axis=1)
    etiqueta = np.concatenate([np.zeros(dh.shape[1], int), np.ones(da.shape[1], int)])
    if todos.shape[1] >= 2:
        dos = np.argpartition(todos, 1, axis=1)[:, :2]
        d2 = np.take_along_axis(todos, dos, axis=1)
        e2 = etiqueta[dos]
        mismo = (e2[:, 0] == e2[:, 1]) & (d2.max(axis=1) < 5)
        out["S2 los dos más cercanos, mismo equipo"] = np.where(mismo, np.where(e2[:, 0] == H, 1, -1), 0).astype(np.int8)
    else:
        out["S2 los dos más cercanos, mismo equipo"] = np.zeros(n, np.int8)
    for nombre, r in (("S3 mayoría a 3 m", 3), ("S4 mayoría a 5 m", 5), ("S5 mayoría a 10 m", 10)):
        dif = (dh < r).sum(axis=1) - (da < r).sum(axis=1)
        out[nombre] = np.sign(dif).astype(np.int8)

    # velocidades de jugadores (±2 y ±12 frames) y del balón (±6 y ±12)
    vel2 = [velocidad(x, y, 2, fps, 12.0) for x, y, _ in eq]
    vel12 = [velocidad(x, y, 12, fps, 12.0) for x, y, _ in eq]
    bvx6, bvy6 = velocidad(bx, by, 6, fps)
    bvx12, bvy12 = velocidad(bx, by, 12, fps)

    # S6 quién llega antes
    llegada = []
    for (x, y, hay), (vx, vy) in zip(eq, vel2):
        px = x + 0.7 * np.nan_to_num(vx)
        py = y + 0.7 * np.nan_to_num(vy)
        t = 0.7 + np.hypot(px - bx[:, None], py - by[:, None]) / 5.0
        t = np.where(hay & vis[:, None], t, np.inf)
        llegada.append(t.min(axis=1) if t.shape[1] else np.full(n, np.inf))
    th, ta = llegada
    with np.errstate(invalid="ignore"):
        ok = np.isfinite(th) & np.isfinite(ta) & (np.abs(ta - th) > 0.5)
    out["S6 llega antes (control del campo)"] = np.where(ok, np.where(th < ta, 1, -1), 0).astype(np.int8)

    # S7 el que más rápido se acerca
    mejor, quien = np.full(n, -np.inf), np.full(n, -1)
    for k, d in ((H, dh), (A, da)):
        dd = np.where(np.isfinite(d), d, np.nan)
        cierre = np.full(d.shape, np.nan)
        if n > 4:
            cierre[2:-2] = -(dd[4:] - dd[:-4]) * fps / 4.0
        cierre = np.where(dd < 10, cierre, np.nan)
        m = np.nanmax(np.where(np.isfinite(cierre), cierre, -np.inf), axis=1) if d.shape[1] else np.full(n, -np.inf)
        cambia = m > mejor
        mejor = np.where(cambia, m, mejor)
        quien = np.where(cambia, k, quien)
    out["S7 el que más se acerca"] = np.where(mejor > 2, a_signo(quien), 0).astype(np.int8)

    # S8 pegado: el mismo equipo a menos de 2 m durante los 12 frames anteriores (él incluido)
    contacto = np.where(dmin < 2, cercano, -1)
    seguidos = np.zeros(n, int)
    for t in range(n):
        if contacto[t] >= 0 and t > 0 and contacto[t] == contacto[t - 1]:
            seguidos[t] = seguidos[t - 1] + 1
        elif contacto[t] >= 0:
            seguidos[t] = 1
    out["S8 pegado 12 frames a 2 m (circular con control)"] = np.where(seguidos >= 12, a_signo(contacto), 0).astype(np.int8)

    # S9 balón lento junto a un jugador
    with np.errstate(invalid="ignore"):
        lento = np.hypot(bvx6, bvy6) < 3
    out["S9 balón lento junto a un jugador"] = np.where(lento & (dmin < 3), a_signo(cercano), 0).astype(np.int8)

    # S10 se mueve con el balón
    bv12 = np.hypot(bvx12, bvy12)
    mejor, quien = np.full(n, np.inf), np.full(n, -1)
    for k, d, (vx, vy) in ((H, dh, vel12[0]), (A, da, vel12[1])):
        dif = np.hypot(vx - bvx12[:, None], vy - bvy12[:, None])
        dif = np.where((d < 5) & np.isfinite(dif), dif, np.inf)
        m = dif.min(axis=1) if dif.shape[1] else np.full(n, np.inf)
        cambia = m < mejor
        mejor = np.where(cambia, m, mejor)
        quien = np.where(cambia, k, quien)
    with np.errstate(invalid="ignore"):
        ok = (mejor < 1.5) & (bv12 > 2)
    out["S10 se mueve con el balón"] = np.where(ok, a_signo(quien), 0).astype(np.int8)

    # S11 el balón frena junto a un jugador: su equipo durante 1 s
    antes = np.full(n, np.nan)
    despues = np.full(n, np.nan)
    if n > 24:
        antes[12:] = np.hypot(bx[12:] - bx[:-12], by[12:] - by[:-12]) * fps / 12.0
        despues[:-12] = np.hypot(bx[12:] - bx[:-12], by[12:] - by[:-12]) * fps / 12.0
    with np.errstate(invalid="ignore"):
        frena = (antes - despues > 3) & (dmin < 3)
    out["S11 el balón frena junto a un jugador"] = a_signo(arrastrar(np.where(frena, cercano, -1), 25))

    # S12 y S13: rivales a 5 m del más cercano
    rivales = np.full(n, -1)
    for k, d, (xo, yo, ho) in ((H, dh, eq[1]), (A, da, eq[0])):
        sel = (cercano == k)
        if not d.shape[1] or not sel.any():
            continue
        j = np.argmin(np.where(np.isfinite(d), d, np.inf), axis=1)
        x, y, _ = eq[k]
        jx, jy = x[np.arange(n), j], y[np.arange(n), j]
        r = np.hypot(xo - jx[:, None], yo - jy[:, None])
        cuenta = np.sum(np.where(ho, r, np.inf) < 5, axis=1)
        rivales = np.where(sel, cuenta, rivales)
    out["S12 más cercano presionado"] = np.where(rivales >= 2, a_signo(cercano), 0).astype(np.int8)
    out["S13 más cercano libre"] = np.where(rivales == 0, a_signo(cercano), 0).astype(np.int8)

    # S14 dos contactos seguidos del mismo equipo a ≤ 2 s
    episodios = []
    for k in (H, A):
        for i, j in rachas(contacto == k):
            episodios.append((i, j, k))
    episodios.sort()
    ev = np.full(n, -1)
    for (i0, j0, k0), (i1, j1, k1) in zip(episodios[:-1], episodios[1:]):
        if k0 == k1 and 0 < i1 - j0 <= 50:
            ev[i1] = k1
    out["S14 dos contactos seguidos (circular con control)"] = a_signo(arrastrar(ev, 50))

    # formación, sin el más retrasado de cada equipo
    forma = []
    for k, (x, y, hay) in zip((H, A), eq):
        dpro = np.where(hay, propia[k](x), np.inf)
        orden = np.argsort(dpro, axis=1)
        portero = orden[:, 0] if x.shape[1] else np.zeros(n, int)
        campo = hay.copy()
        if x.shape[1]:
            campo[np.arange(n), portero] = False
        cnt = campo.sum(axis=1)
        def dt(v):
            m = np.where(campo, v, 0).sum(axis=1) / np.maximum(cnt, 1)
            return np.sqrt(np.where(campo, (v - m[:, None]) ** 2, 0).sum(axis=1) / np.maximum(cnt, 1))
        sx, sy = dt(np.nan_to_num(x)), dt(np.nan_to_num(y))
        segunda = np.take_along_axis(dpro, orden[:, 1:2], axis=1)[:, 0] if x.shape[1] > 1 else np.full(n, np.nan)
        detras = np.full(n, np.nan)
        bpro = propia[k](bx)
        with np.errstate(invalid="ignore"):
            detras = np.where(vis, np.sum(campo & (dpro < bpro[:, None]), axis=1), np.nan)
        valido = cnt >= 5
        forma.append({"sx": np.where(valido, sx, np.nan), "sy": np.where(valido, sy, np.nan),
                      "linea": np.where(valido, segunda, np.nan), "detras": np.where(valido, detras, np.nan),
                      "portero": portero, "dpro": dpro})
    fh, fa = forma
    with np.errstate(invalid="ignore"):
        out["S15 el más ancho"] = np.where(np.abs(fh["sy"] - fa["sy"]) > 2, np.sign(fh["sy"] - fa["sy"]), 0).astype(np.int8)
        out["S16 el más largo"] = np.where(np.abs(fh["sx"] - fa["sx"]) > 2, np.sign(fh["sx"] - fa["sx"]), 0).astype(np.int8)
        ah, aa = fh["sx"] * fh["sy"], fa["sx"] * fa["sy"]
        out["S17 el de más área"] = np.where(ah > 1.3 * aa, 1, np.where(aa > 1.3 * ah, -1, 0)).astype(np.int8)
        out["S18 línea defensiva más alta"] = np.where(np.abs(fh["linea"] - fa["linea"]) > 5,
                                                       np.sign(fh["linea"] - fa["linea"]), 0).astype(np.int8)
        dif = fh["detras"] - fa["detras"]
        out["S19 por detrás del balón (el otro defiende)"] = np.where(dif >= 3, -1, np.where(dif <= -3, 1, 0)).astype(np.int8)

    # S20 y S21: huecos del balón
    ultimo = arrastrar(np.where(vis, cercano, -1), n + 1)
    out["S20 sin balón: se queda el último"] = np.where(~vis, a_signo(ultimo), 0).astype(np.int8)
    gk = np.zeros(n, np.int8)
    for i, j in rachas(~vis):
        if i == 0 or j - i < 25:
            continue
        lx, ly = bx[i - 1], by[i - 1]
        for k, (x, y, hay) in zip((H, A), eq):
            if not x.shape[1]:
                continue
            p = forma[k]["portero"][i - 1]
            if not hay[i - 1, p]:
                continue
            cerca = np.hypot(x[i - 1, p] - lx, y[i - 1, p] - ly) < 3
            en_area = propia[k](lx) < AREA_FONDO and abs(ly - ancho / 2) < AREA_MEDIA
            if cerca and en_area:
                gk[i:j] = 1 if k == H else -1
    out["S21 el balón desaparece junto al portero"] = gk

    # balón muerto: solo jugadores
    rap = np.concatenate([np.hypot(*v) for v in vel2], axis=1)
    hay_v = np.isfinite(rap)
    cuenta_v = hay_v.sum(axis=1)
    vmed = np.where(cuenta_v > 0, np.where(hay_v, rap, 0.0).sum(axis=1) / np.maximum(cuenta_v, 1), np.nan)
    centrada = media_ventana(vmed, 12, 12)
    previa = media_ventana(vmed, 25, -1)
    siguiente = media_ventana(vmed, 0, 24)
    muerto = {}
    with np.errstate(invalid="ignore"):
        muerto["D1 jugadores lentos"] = np.where(centrada < 1.5, 1, np.where(centrada > 2.5, -1, 0)).astype(np.int8)
        cae = siguiente - previa < -1
        sube = siguiente - previa > 1
    muerto["D2 frenazo colectivo"] = np.where(arrastrar(np.where(cae, 1, -1), 50) == 1, 1, 0).astype(np.int8)
    muerto["D3 arranque colectivo"] = np.where(arrastrar(np.where(sube, 1, -1), 25) == 1, -1, 0).astype(np.int8)
    fuera = np.zeros(n, bool)
    en_area = np.zeros(n, int)
    for x, y, hay in eq:
        with np.errstate(invalid="ignore"):
            margen = np.maximum.reduce([-x, x - largo, -y, y - ancho])
            fuera |= np.any(hay & (margen > 0.5) & (margen < 3), axis=1)
            caja = np.abs(y - ancho / 2) < AREA_MEDIA
            en_area += np.sum(hay & caja & ((x < AREA_FONDO) | (x > largo - AREA_FONDO)), axis=1)
    muerto["D4 jugador fuera junto a la línea"] = fuera.astype(np.int8)
    with np.errstate(invalid="ignore"):
        muerto["D5 muchos en el área y quietos"] = ((en_area >= 8) & (centrada < 1.5)).astype(np.int8)
    return out, muerto


def senales(trk):
    n = len(trk.bx)
    equipo = {k: np.zeros(n, np.int8) for k in EQUIPO}
    muerto = {k: np.zeros(n, np.int8) for k in MUERTO}
    for a, b in trk.blocks:
        e, m = senales_tramo(trk, a, b)
        for k, v in e.items():
            equipo[k][a:b] = v
        for k, v in m.items():
            muerto[k][a:b] = v
    return equipo, muerto


# -- zonas -----------------------------------------------------------------------------------------------

def zonas(gt, pred, blocks, vis):
    n = len(gt)
    vivo = np.zeros(n, bool)
    z1 = np.zeros(n, bool)
    z2 = np.zeros(n, bool)
    z3 = np.zeros(n, bool)
    for a, b in blocks:
        g = gt[a:b]
        vivo[a:b] = (g == H) | (g == A)
        for k in (H, A):
            otro = A if k == H else H
            for i, j in rachas(g == k):
                if 50 <= j - i < 250 and np.mean(pred[a + i:a + j] == otro) > 0.5:
                    z1[a + i:a + j] = True
        t = np.flatnonzero(((g[1:] == H) & (g[:-1] == A)) | ((g[1:] == A) & (g[:-1] == H))) + 1
        for c in t:
            z2[a + max(0, c - 25):a + min(b - a, c + 25)] = True
        for i, j in rachas(g == D):
            for lo, hi in ((i - 25, i + 25), (j - 25, j + 25)):
                z3[a + max(0, lo):a + min(b - a, hi)] = True
    z2 &= vivo
    return {"vivo": vivo, "Z1": z1 & vivo, "Z2": z2, "Z1∪Z2": (z1 | z2) & vivo, "Z3": z3, "Z4": vivo & ~vis}


# -- regresión -------------------------------------------------------------------------------------------

def logistica(X, y, l2=1e-3, iteraciones=25):
    w = np.zeros(X.shape[1])
    for _ in range(iteraciones):
        z = X @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        g = X.T @ (p - y) + l2 * w
        Hs = (X * (p * (1 - p))[:, None]).T @ X + l2 * np.eye(X.shape[1])
        w -= np.linalg.solve(Hs, g)
    return w


def b5_dif(trk, fuera):
    score, _ = aprendida.evidence_b5(trk, fuera=fuera)
    return np.clip(score[:, H] - score[:, A], -30, 30) / 10.0


# -- medir -----------------------------------------------------------------------------------------------

def retrasar(trk, k):
    bx, by = np.full(len(trk.bx), np.nan), np.full(len(trk.by), np.nan)
    for a, b in trk.blocks:
        bx[a + k:b], by[a + k:b] = trk.bx[a:b - k], trk.by[a:b - k]
    return trk._replace(bx=bx, by=by)


def recoger(trk, gts, pred, fuera, pred_propio=None):
    """Lo que hace falta de un partido: señales, B5, zonas por convención, solo en los frames de los tramos."""
    equipo, muerto = senales(trk)
    vis = np.isfinite(np.asarray(trk.bx)) & np.isfinite(np.asarray(trk.by))
    d = b5_dif(trk, fuera)
    equipo["R3 signo de B5"] = np.sign(d).astype(np.int8)
    datos = {"equipo": equipo, "muerto": muerto, "d": d, "pred": pred, "propio": pred_propio, "conv": {}}
    for conv, gt in gts.items():
        datos["conv"][conv] = {"gt": gt, "z": zonas(gt, pred, trk.blocks, vis)}
    return datos


def tabla_equipo(partidos, conv, pliegues, titulo):
    """Imprime la tabla de las señales de equipo de una medida."""
    print("\n### {}\n".format(titulo))
    acum = collections.defaultdict(lambda: np.zeros(12))
    # acierto de la regresión: nombre -> [aciertos B5 solo, aciertos con señal, total] por zona
    reg = collections.defaultdict(lambda: np.zeros((3, 3)))
    nombres = EQUIPO + ["B5 + todas las señales de equipo"]
    for prueba, entrena in pliegues:
        X_e, y_e = collections.defaultdict(list), []
        for p in entrena:
            dt = partidos[p]
            c = dt["conv"][conv]
            vivo = np.flatnonzero(c["z"]["vivo"])[::PASO]
            y_e.append((c["gt"][vivo] == H).astype(float))
            X_e["d"].append(dt["d"][vivo])
            for k in EQUIPO:
                if k != "R3 signo de B5":
                    X_e[k].append(dt["equipo"][k][vivo].astype(float))
        y = np.concatenate(y_e)
        dcol = np.concatenate(X_e["d"])
        pesos = {}
        for k in EQUIPO:
            if k == "R3 signo de B5":
                continue
            pesos[k] = logistica(np.column_stack([dcol, np.concatenate(X_e[k])]), y)
        otras = [k for k in EQUIPO if k != "R3 signo de B5"]
        pesos["B5 + todas las señales de equipo"] = logistica(
            np.column_stack([dcol] + [np.concatenate(X_e[k]) for k in otras]), y)
        for p in prueba:
            dt = partidos[p]
            c = dt["conv"][conv]
            g = c["gt"]
            z = c["z"]
            mal = (dt["pred"] != g)
            for k in EQUIPO:
                s = dt["equipo"][k]
                eqs = np.where(s > 0, H, np.where(s < 0, A, -1))
                opina = s != 0
                bien = opina & (eqs == g)
                fila = acum[k]
                for i, zona in enumerate(("vivo", "Z1", "Z4")):
                    m = z[zona]
                    fila[3 * i:3 * i + 3] += [m.sum(), (m & opina).sum(), (m & bien).sum()]
                m = z["Z2"]
                fila[9:12] += [(m & mal).sum(), (m & mal & bien).sum(), 0]
                fila[11] += (m & ~mal & opina & ~bien).sum()
                acum[k + "#Z2ok"] += [(m & ~mal).sum()] + [0] * 11
            base = np.sign(dt["d"])
            for k in nombres:
                if k == "R3 signo de B5":
                    continue
                if k == "B5 + todas las señales de equipo":
                    Xp = np.column_stack([dt["d"]] + [dt["equipo"][o].astype(float) for o in otras])
                else:
                    Xp = np.column_stack([dt["d"], dt["equipo"][k].astype(float)])
                zz = Xp @ pesos[k]
                for i, zona in enumerate(("vivo", "Z1∪Z2", "Z4")):
                    m = z[zona]
                    reg[k][i] += [np.sum(m & (np.where(base > 0, H, A) == g) & (base != 0)),
                                  np.sum(m & (np.where(zz > 0, H, A) == g) & (zz != 0)), m.sum()]
    print("| señal | opina en juego | acierta en juego | Z1: opina / acierta | Z2: rescata / estropea | "
          "sin balón: opina / acierta | + B5: Δ acierto en juego | + B5: Δ en Z1∪Z2 | + B5: Δ sin balón |")
    print("|---|---|---|---|---|---|---|---|---|")
    pct = lambda a, b: 100.0 * a / b if b else float("nan")  # noqa: E731
    for k in nombres:
        celdas = [k]
        if k in acum:
            f = acum[k]
            z2ok = acum[k + "#Z2ok"][0]
            celdas += ["{:.0f} %".format(pct(f[1], f[0])), "{:.1f} %".format(pct(f[2], f[1])),
                       "{:.0f} % / {:.1f} %".format(pct(f[4], f[3]), pct(f[5], f[4])),
                       "{:.1f} % / {:.1f} %".format(pct(f[10], f[9]), pct(f[11], z2ok)),
                       "{:.0f} % / {:.1f} %".format(pct(f[7], f[6]), pct(f[8], f[7]))]
        else:
            celdas += ["–"] * 5
        if k in reg:
            r = reg[k]
            celdas += ["{:+.2f}".format(pct(r[i][1] - r[i][0], r[i][2])) for i in range(3)]
        else:
            celdas += ["–"] * 3
        print("| " + " | ".join(celdas) + " |")
    r = reg["R1 más cercano (N1)"]
    print("\nReferencia: el signo de B5 acierta el {:.1f} % de los frames de juego, el {:.1f} % en Z1∪Z2 y el {:.1f} % "
          "sin balón.".format(*(pct(r[i][0], r[i][2]) for i in range(3))))


def tabla_muerto(partidos, titulo):
    print("\n### {}\n".format(titulo))
    print("| señal | Z3: opina | Z3: acierta | Z3: rescata / estropea frente a `main` con su `D` | dice `D` en el juego |")
    print("|---|---|---|---|---|")
    for k in MUERTO:
        f = np.zeros(7)
        for dt in partidos.values():
            c = dt["conv"]["flag"]
            g, z = c["gt"], c["z"]
            m = z["Z3"] & (g != X)
            s = dt["muerto"][k]
            verdad = np.where(g == D, 1, -1)
            pm = np.where(dt["propio"] == D, 1, -1)
            mal = pm != verdad
            bien = (s != 0) & (s == verdad)
            f += [m.sum(), (m & (s != 0)).sum(), (m & bien).sum(), (m & mal).sum(), (m & mal & bien).sum(),
                  (m & ~mal).sum(), (m & ~mal & (s != 0) & ~bien).sum()]
            vivo = z["vivo"]
            dt.setdefault("_falsas", collections.Counter())
            dt["_falsas"][k] = (int((vivo & (s == 1)).sum()), int(vivo.sum()))
        falsas = sum(dt["_falsas"][k][0] for dt in partidos.values())
        juego = sum(dt["_falsas"][k][1] for dt in partidos.values())
        print("| {} | {:.0f} % | {:.1f} % | {:.1f} % / {:.1f} % | {:.1f} % |".format(
            k, 100 * f[1] / f[0], 100 * f[2] / max(f[1], 1), 100 * f[4] / max(f[3], 1), 100 * f[6] / max(f[5], 1),
            100 * falsas / max(juego, 1)))


def medir_dfl():
    version = puntuar.leer_versiones(VERSIONES)[0]["main: B5 y coste 25"]
    por_retraso = {0: {}, RETRASO: {}}
    for partido in dfl.PARTIDOS:
        t0 = time.time()
        cargado = dfl.cargar(partido)
        gts = {c: cargado["gt"][c] for c in dfl.CONVENCIONES}
        base = puntuar.solo_lectura(dfl.tracking_de(cargado, "como el ATD"))
        for retraso in (0, RETRASO):
            trk = base if retraso == 0 else puntuar.solo_lectura(retrasar(base, retraso))
            pred = puntuar.ejecutar(version, trk, gts["flag"], "oraculo", partido)
            propio = puntuar.ejecutar(version, trk, gts["flag"], "propio", partido) if retraso == 0 else None
            por_retraso[retraso][partido] = recoger(trk, gts, pred, partido, propio)
        print("DFL {} en {:.0f} s".format(partido, time.time() - t0), file=sys.stderr, flush=True)
    pliegues = [([p], [q for q in dfl.PARTIDOS if q != p]) for p in dfl.PARTIDOS]
    print("## DFL, 7 partidos, balón «como el ATD», `main` con el `D` de las etiquetas")
    for conv in dfl.CONVENCIONES:
        for retraso in (0, RETRASO):
            tabla_equipo(por_retraso[retraso], conv, pliegues, "DFL, {}, balón {}".format(
                conv, "a su hora" if retraso == 0 else "{} frames tarde".format(retraso)))
    tabla_muerto(por_retraso[0], "DFL, señales de balón muerto (Z3, frente a `main` con su `D` propio)")


def medir_skillcorner():
    ids = list(lc.ENTRENAMIENTO)
    lc.exigir_solo_entrenamiento(ids)
    partidos = {}
    for id_ in ids:
        t0 = time.time()
        crudo = lc.leer_crudo(id_)
        trk, gt = lc.tracking_de(crudo, "detectado", id_)
        trk = puntuar.solo_lectura(trk)
        pred = pipeline.run(trk, extra=[puntuar.d_oraculo(gt)])
        partidos[id_] = recoger(trk, {"skillcorner": gt}, pred, None)
        print("SkillCorner {} en {:.0f} s".format(id_, time.time() - t0), file=sys.stderr, flush=True)
    mitad = len(ids) // 2
    pliegues = [(ids[:mitad], ids[mitad:]), (ids[mitad:], ids[:mitad])]
    print("\n## SkillCorner, mitad de entrenamiento ({} partidos), «detectado», `main` con el `D` de las etiquetas".format(len(ids)))
    tabla_equipo(partidos, "skillcorner", pliegues, "SkillCorner (la regresión se entrena en una mitad y se mide en la otra)")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solo", choices=("dfl", "skillcorner"))
    args = parser.parse_args()
    print("Zonas: Z1 posesiones reales de 2 a 10 s en que `main` dice el otro equipo; Z2 ±1 s de los cambios reales; "
          "Z4 juego sin balón. «Rescata»: de los frames de Z2 que `main` falla, en cuántos la señal opina y acierta. "
          "«Estropea»: de los que `main` acierta, en cuántos opina y falla. «+ B5»: regresión con la diferencia de "
          "B5 y la señal, fuera de muestra, frente al signo de B5 solo, en puntos de acierto por frame.")
    if args.solo != "skillcorner":
        medir_dfl()
    if args.solo != "dfl":
        medir_skillcorner()


if __name__ == "__main__":
    main()
