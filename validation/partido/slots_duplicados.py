"""¿Cuántas veces duplica el ATD a un jugador? Dos slots del mismo equipo casi en el mismo sitio.

**Solo lo ejecuta una persona, en local** (regla nº 1 de `CLAUDE.md`). Claude no lo ejecuta: lee el
tracking del partido.

Por qué: B5, la evidencia de equipo de la entrega (`possession/aprendida.py`), suma núcleos gaussianos de
las distancias de cada slot al balón. Si el tracker duplica a un jugador, ese jugador cuenta doble. `DATA.md`
dice que a veces pasa; la DFL del harness no tiene duplicados, así que allí no se ve (revisión externa del
15/11, punto 15; `docs/decisiones.md`, «una sola ronda de reentrenamiento de B5»).

Qué mide, en los frames evaluados de las dos partes juntas, **solo agregados**:
- el % de frames con dos slots del mismo equipo a 0,3, 0,5 y 1 m o menos;
- lo mismo solo en los frames con balón y con esa pareja a 6 m o menos del balón (donde pesan los núcleos);
- el % de frames en que un equipo tiene más de 11 slots a la vez.

No decide nada en esta ronda: arreglarlo cambiaría los rasgos de B5 y la entrega, y sería un candidato nuevo.
Nada por frame, por jugada ni por jugador, así que la salida se puede pegar a Claude tal cual.

Uso, desde la raíz del repo y con el entorno de siempre:

    python validation/partido/slots_duplicados.py

Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
"""

import argparse
import json
import os
import sys
import traceback
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
import games  # noqa: E402
from possession import tracking  # noqa: E402

FICHEROS = ["atd_meta", "atd_raw"]
DISTANCIAS = (0.3, 0.5, 1.0)  # m
CERCA_DEL_BALON = 6.0  # m: el núcleo más ancho de B5
JUGADORES = 11
BLOQUE = 20000  # frames por bloque


def medir(trk):
    """Recuentos de frames evaluados con parejas del mismo equipo cerca, y con más de 11 slots."""
    evaluado = np.zeros(len(trk.bx), bool)
    for inicio, fin in trk.blocks:
        evaluado[inicio:fin] = True
    frames = np.flatnonzero(evaluado)
    team = np.asarray(trk.team)
    cuentas = {"frames_evaluados": int(len(frames)), "frames_con_balon": 0, "mas_de_11": 0}
    for d in DISTANCIAS:
        cuentas["pareja_a_{:g}_m".format(d)] = 0
        cuentas["pareja_a_{:g}_m_cerca_del_balon".format(d)] = 0
    for inicio in range(0, len(frames), BLOQUE):
        idx = frames[inicio:inicio + BLOQUE]
        bx, by = trk.bx[idx].astype(np.float64), trk.by[idx].astype(np.float64)
        con_balon = np.isfinite(bx) & np.isfinite(by)
        cuentas["frames_con_balon"] += int(con_balon.sum())
        minimo = np.full(len(idx), np.inf)
        minimo_cerca = np.full(len(idx), np.inf)
        mas_de_11 = np.zeros(len(idx), bool)
        for equipo in (0, 1):
            columnas = np.flatnonzero(team == equipo)
            x = trk.px[idx][:, columnas].astype(np.float64)
            y = trk.py[idx][:, columnas].astype(np.float64)
            hay = np.isfinite(x) & np.isfinite(y)
            mas_de_11 |= hay.sum(axis=1) > JUGADORES
            d2 = (x[:, :, None] - x[:, None, :]) ** 2 + (y[:, :, None] - y[:, None, :]) ** 2
            d2 = np.where(hay[:, :, None] & hay[:, None, :], d2, np.inf)
            d2[:, np.arange(len(columnas)), np.arange(len(columnas))] = np.inf
            minimo = np.minimum(minimo, d2.min(axis=(1, 2)) if len(columnas) > 1 else np.inf)
            al_balon = (x - bx[:, None]) ** 2 + (y - by[:, None]) ** 2 <= CERCA_DEL_BALON ** 2
            cerca = np.where(al_balon[:, :, None] & al_balon[:, None, :], d2, np.inf)
            minimo_cerca = np.minimum(minimo_cerca, cerca.min(axis=(1, 2)) if len(columnas) > 1 else np.inf)
        cuentas["mas_de_11"] += int(mas_de_11.sum())
        for d in DISTANCIAS:
            cuentas["pareja_a_{:g}_m".format(d)] += int(np.sum(minimo <= d * d))
            cuentas["pareja_a_{:g}_m_cerca_del_balon".format(d)] += int(np.sum(con_balon & (minimo_cerca <= d * d)))
    return cuentas


def resumen(c):
    pct = lambda a, b: round(100.0 * a / b, 2) if b else None  # noqa: E731
    salida = {"frames_evaluados": c["frames_evaluados"],
              "pct_frames_con_un_equipo_de_mas_de_11_slots": pct(c["mas_de_11"], c["frames_evaluados"])}
    for d in DISTANCIAS:
        salida["pct_frames_con_pareja_del_mismo_equipo_a_{:g}_m".format(d)] = pct(
            c["pareja_a_{:g}_m".format(d)], c["frames_evaluados"])
        salida["pct_frames_con_balon_con_esa_pareja_a_{:g}_m_del_balon_a_6_m".format(d)] = pct(
            c["pareja_a_{:g}_m_cerca_del_balon".format(d)], c["frames_con_balon"])
    return salida


def informe_de_error(error):
    pila = traceback.extract_tb(error.__traceback__)
    lineas = ["{}:{} ({})".format(os.path.basename(f.filename), f.lineno, f.name) for f in pila]
    return "ERROR {} en {}".format(type(error).__name__, " <- ".join(reversed(lineas)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD del partido: revisa que MTAH_DATA_DIR apunte a la carpeta de los datos.")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        trk = tracking.from_atd(games.asset_paths(games.GAME, args.data_dir), games.GAME)
        salida = resumen(medir(trk))
    print(json.dumps(dict({"medida": "slots del mismo equipo casi en el mismo sitio, frames evaluados"}, **salida),
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
