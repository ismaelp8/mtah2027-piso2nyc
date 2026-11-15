"""Sondeo S7b: las señales de la lista de Ismael que S7 no cribó. Mismas zonas, números y regla que S7.

    python validation/investigacion_1116/cribado_senales_2.py [--solo dfl|skillcorner]

Datos abiertos de otros partidos (DFL y la mitad de entrenamiento de SkillCorner). Lo puede ejecutar cualquiera,
Claude incluido. Solo imprime agregados. La regla está en BITACORA.md (S7b), escrita antes de medir.
"""

import argparse
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import cribado_senales as cs  # noqa: E402

H, A = cs.H, cs.A
NUEVAS = ["S22 el que se abre", "S23 el que se alarga", "S24 el que gana área", "S25 el receptor frena",
          "S26 el balón dentro de un solo bloque"]
original = cs.senales_tramo


def extra_tramo(trk, a, b):
    fps = float(trk.fps)
    largo = float(trk.pitch[0])
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
    (xh, _, hh), (xa, _, ha) = eq
    direccion = float(np.sign(np.nanmean(np.where(ha, xa, np.nan)) - np.nanmean(np.where(hh, xh, np.nan)))) or 1.0
    propia = [lambda x: x if direccion > 0 else largo - x, lambda x: largo - x if direccion > 0 else x]
    out = {}
    forma = []
    for k, (x, y, hay) in zip((H, A), eq):
        dpro = np.where(hay, propia[k](x), np.inf)
        campo = hay.copy()
        if x.shape[1]:
            campo[np.arange(n), np.argmin(dpro, axis=1)] = False
        cnt = campo.sum(axis=1)

        def dt(v):
            m = np.where(campo, v, 0).sum(axis=1) / np.maximum(cnt, 1)
            return np.sqrt(np.where(campo, (v - m[:, None]) ** 2, 0).sum(axis=1) / np.maximum(cnt, 1))
        sx, sy = dt(np.nan_to_num(x)), dt(np.nan_to_num(y))
        ok = cnt >= 5
        with np.errstate(invalid="ignore"):
            qx = [np.nanpercentile(np.where(campo, x, np.nan), q, axis=1) if x.shape[1] else np.full(n, np.nan)
                  for q in (10, 90)]
            qy = [np.nanpercentile(np.where(campo, y, np.nan), q, axis=1) if x.shape[1] else np.full(n, np.nan)
                  for q in (10, 90)]
        forma.append({"sx": np.where(ok, sx, np.nan), "sy": np.where(ok, sy, np.nan), "qx": qx, "qy": qy, "ok": ok})
    L = 50

    def cambio(v):
        d = np.full(n, np.nan)
        d[L:] = v[L:] - v[:-L]
        return d
    with np.errstate(invalid="ignore", divide="ignore"):
        dw = cambio(forma[0]["sy"]) - cambio(forma[1]["sy"])
        out["S22 el que se abre"] = np.where(np.abs(dw) > 1, np.sign(dw), 0).astype(np.int8)
        dd = cambio(forma[0]["sx"]) - cambio(forma[1]["sx"])
        out["S23 el que se alarga"] = np.where(np.abs(dd) > 1, np.sign(dd), 0).astype(np.int8)
        area = [f["sx"] * f["sy"] for f in forma]
        razon = []
        for v in area:
            r = np.full(n, np.nan)
            r[L:] = v[L:] / v[:-L]
            razon.append(r)
        rr = razon[0] / razon[1]
        out["S24 el que gana área"] = np.where(rr > 1.2, 1, np.where(rr < 1 / 1.2, -1, 0)).astype(np.int8)
    # S25 el receptor frena
    mejor, quien = np.full(n, np.inf), np.full(n, -1)
    for k, (x, y, hay) in zip((H, A), eq):
        vx, vy = cs.velocidad(x, y, 2, fps, 12.0)
        rap = np.hypot(vx, vy)
        caida = np.full(rap.shape, np.nan)
        caida[12:] = rap[:-12] - rap[12:]
        d = np.hypot(x - bx[:, None], y - by[:, None])
        acerca = np.full(d.shape, np.nan)
        acerca[4:] = d[:-4] - d[4:]
        with np.errstate(invalid="ignore"):
            cand = hay & vis[:, None] & (d < 3) & (caida > 2) & (acerca > 0)
        dist = np.where(cand, d, np.inf)
        m = dist.min(axis=1) if dist.shape[1] else np.full(n, np.inf)
        cambia = m < mejor
        mejor = np.where(cambia, m, mejor)
        quien = np.where(cambia, k, quien)
    out["S25 el receptor frena"] = np.where(np.isfinite(mejor), cs.a_signo(quien), 0).astype(np.int8)
    # S26 el balón dentro de un solo bloque: ese equipo defiende
    dentro = []
    for f in forma:
        with np.errstate(invalid="ignore"):
            dentro.append(f["ok"] & vis & (bx >= f["qx"][0]) & (bx <= f["qx"][1]) & (by >= f["qy"][0]) & (by <= f["qy"][1]))
    out["S26 el balón dentro de un solo bloque"] = np.where(dentro[0] & ~dentro[1], -1,
                                                           np.where(dentro[1] & ~dentro[0], 1, 0)).astype(np.int8)
    return out


def senales_tramo(trk, a, b):
    equipo, muerto = original(trk, a, b)
    equipo = {k: equipo[k] for k in ("R1 más cercano (N1)",)}
    equipo.update(extra_tramo(trk, a, b))
    return equipo, muerto


def main():
    cs.EQUIPO = ["R1 más cercano (N1)", "R3 signo de B5"] + NUEVAS
    cs.senales_tramo = senales_tramo
    cs.tabla_muerto = lambda *args, **kwargs: None
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solo", choices=("dfl", "skillcorner"))
    args = parser.parse_args()
    if args.solo != "skillcorner":
        cs.medir_dfl()
    if args.solo != "dfl":
        cs.medir_skillcorner()


if __name__ == "__main__":
    main()
