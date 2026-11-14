"""Experimento 2 en el partido: qué convención sigue la GT pública, medida con el tracking automático (ATD).

**Solo lo ejecuta una persona, en local** (regla nº 1 de `CLAUDE.md`). Claude no lo ejecuta: lee el
tracking del partido.

Sustituye al recuento a ojo del vídeo (sección 17 de la bitácora del experimento 1) por el mismo
instrumento que se calibró en la DFL (`validation/experimento2/instrumento.py`):

- lee el ATD solo en la ventana pública (los frames que cubre la GT pública, con 1 s de margen) y la GT
  pública de `evaluation/gt/`;
- busca toques y controles con los umbrales de los experimentos 0 y 1, sin ajustar nada aquí;
- imprime **solo agregados**: recuentos por clase y proporciones. Nada por frame, por jugada ni por
  jugador, así que la salida se puede pegar a Claude tal cual.

Cómo se lee la salida está fijado antes de ejecutarlo en `validation/experimento2/BITACORA.md`. De aquí no
sale ninguna etiqueta, constante ni parámetro para el pipeline: solo qué convención sigue la GT.

Uso, desde la raíz del repo y con el entorno de siempre (tarda unos segundos: solo lee la ventana):

    python validation/partido/recuento_ventana.py

Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
"""

import argparse
import csv
import json
import os
import sys
import traceback

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "starter"))
sys.path.insert(0, os.path.join(RAIZ, "validation", "experimento2"))
import games  # noqa: E402
import instrumento as ins  # noqa: E402
from baseline import team_of_each_track  # noqa: E402

MARGEN = 25  # frames de tracking a cada lado de la ventana (1 s)
VARIANTES = {
    "base": ins.PRM,
    "ampliada": dict(ins.PRM, radio=1.5, radio_toque=2.0),
}


def ventana_publica(game=games.GAME):
    """(primer, último) frame de vídeo que cubre la GT pública, leído de su fichero de metadatos."""
    ruta = os.path.join(RAIZ, "evaluation", "gt", "{}_possession_gt_public_meta.json".format(game))
    with open(ruta, encoding="utf-8") as fh:
        meta = json.load(fh)
    tramos = meta["covered_video_frames"]
    if len(tramos) != 1:
        raise ValueError("la GT pública debería cubrir un solo tramo")
    return int(tramos[0][0]), int(tramos[0][1])


def leer_gt(inicio, fin, game=games.GAME):
    """(estado, poss) de los frames de vídeo inicio…fin: estado 1 con H/A; poss 1 = H, 2 = A, 0 si no."""
    ruta = os.path.join(RAIZ, "evaluation", "gt", "{}_possession_gt_public.csv".format(game))
    n = fin - inicio + 1
    estado, poss = np.zeros(n, int), np.zeros(n, int)
    with open(ruta, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            f = int(fila["frame"])
            if inicio <= f <= fin and fila["label"] in ("H", "A"):
                estado[f - inicio] = 1
                poss[f - inicio] = 1 if fila["label"] == "H" else 2
    return estado, poss


def _xy(grupo, largo, ancho):
    """(x, y) en metros de un grupo `x,y,velocidad`; NaN si falta, como el lector de `starter/baseline.py`."""
    v = grupo.split(",")
    if len(v) < 2 or not v[0] or not v[1] or v[0][0] == "N" or v[1][0] == "N":
        return np.nan, np.nan
    return float(v[0]) * largo, float(v[1]) * ancho


def leer_atd(raw_path, meta_path, inicio, fin, campo):
    """(parte, calidad): balón y jugadores (m) de los frames de vídeo inicio…fin, como una `parte` de la DFL.

    Formato de cada línea (`DATA.md`): `<frame_id>:<slot>;<slot>;...:<balón>`, cada grupo `x,y,velocidad`,
    con `NaN` si falta; coordenadas de 0 a 1; frame de vídeo = frame_id − 1. Tolera lo mismo que el lector
    de `starter/baseline.py` (líneas raras, grupos vacíos) y lo cuenta en `calidad`.
    """
    equipo_slot = np.asarray(team_of_each_track(meta_path))
    largo, ancho = campo
    n = fin - inicio + 1
    bx, by = np.full(n, np.nan), np.full(n, np.nan)
    px, py = np.full((n, len(equipo_slot)), np.nan), np.full((n, len(equipo_slot)), np.nan)
    visto = np.zeros(n, bool)
    otros_slots = 0
    with open(raw_path) as fh:
        for linea in fh:
            partes = linea.rstrip("\r\n").split(":")
            if len(partes) != 3:
                continue
            f = int(partes[0]) - 1
            if f < inicio:
                continue
            if f > fin:
                break  # el ATD va en orden, uno por frame (starter/load_atd.py lo comprueba)
            i = f - inicio
            grupos = partes[1].split(";")
            otros_slots += int(len(grupos) != len(equipo_slot))
            for j, g in enumerate(grupos[:len(equipo_slot)]):
                px[i, j], py[i, j] = _xy(g, largo, ancho)
            bx[i], by[i] = _xy(partes[2], largo, ancho)
            visto[i] = True
    if not visto.any():
        raise ValueError("no hay frames del ATD en la ventana")
    parte = {"x": bx, "y": by, "z": np.zeros(n),
             "equipos": {"local": {"x": px[:, equipo_slot == 0], "y": py[:, equipo_slot == 0]},
                         "visitante": {"x": px[:, equipo_slot == 1], "y": py[:, equipo_slot == 1]}}}
    calidad = {"frames_que_faltan": int(n - visto.sum()), "lineas_con_otro_numero_de_slots": otros_slots,
               "slots": int(len(equipo_slot))}
    return parte, calidad


def medir_ventana(parte, estado, poss):
    """Agregados del instrumento con las dos variantes fijadas de antemano."""
    salida = {}
    for nombre, prm in VARIANTES.items():
        prep = ins.preparar_en_juego(parte, estado)
        r = ins.medir(prep, estado, poss, prm)
        salida[nombre] = {"tasas": ins.tasas(r), "recuentos": r}
    return salida


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    try:
        meta_path, raw_path = games.require(["atd_meta", "atd_raw"], games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD del partido: revisa que MTAH_DATA_DIR apunte a la carpeta de los datos.")
        sys.exit(1)
    primero, ultimo = ventana_publica()
    inicio, fin = primero - MARGEN, ultimo + MARGEN
    estado, poss = leer_gt(inicio, fin)
    parte, calidad = leer_atd(raw_path, meta_path, inicio, fin, games.GAMES[games.GAME]["pitch"])
    salida = {"experimento": "2 · recuento con el tracking en la ventana pública",
              "frames_de_la_ventana": ultimo - primero + 1,
              "calidad_del_atd": calidad,
              "variantes": medir_ventana(parte, estado, poss)}
    print(json.dumps(salida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        pila = traceback.extract_tb(e.__traceback__)
        donde = ", ".join("{}:{}".format(os.path.basename(p.filename), p.lineno) for p in pila[-4:])
        print("ERROR {} en {}. Sin valores de datos: se puede pegar tal cual.".format(type(e).__name__, donde))
        sys.exit(1)
