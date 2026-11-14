"""Perfil del ATD en todo el partido: la medida de `validation/perfil_atd/BITACORA.md`. Solo agregados.

**Lee datos del partido: lo ejecuta una persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/perfil_atd.py

- Lee el ATD con `possession/tracking.py`, el mismo lector que el pipeline, y las ventanas `SET PIECES` del
  Smart Tagging. Mide los frames evaluados con `validation/perfil_atd/perfil.py`, el mismo código que mide
  la DFL en `validation/perfil_atd/perfil_dfl.py`.
- Imprime un JSON con recuentos, porcentajes y cuantiles del partido entero, con las dos partes juntas.
  Nada por parte, por minuto, por jugada ni por frame, y una celda con menos de 5 casos sale como "< 5".
  La salida se puede pegar a Claude tal cual.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.

Tarda alrededor de un minuto, casi todo leyendo el ATD. Cómo se lee la salida está fijado antes de medir,
en la sección 5 de la bitácora.
"""

import argparse
import json
import os
import sys
import time
import traceback
import warnings

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "perfil_atd"))
import games  # noqa: E402
import perfil as pf  # noqa: E402
from possession import tracking  # noqa: E402
from starter import load_smart_tagging  # noqa: E402

MINIMO_CELDA = 5
SET_PIECES_CODE = "set pieces"
FICHEROS = ["atd_raw", "atd_meta", "smart_tagging"]


def ventanas_set_pieces(eventos):
    """(inicio, fin) en frames de vídeo de cada ventana `SET PIECES`, con el fin sin incluir."""
    return [(e["start_frame"], e["end_frame"]) for e in eventos
            if (e["code"] or "").strip().lower() == SET_PIECES_CODE]


def medir(data_dir=None):
    """El perfil del ATD en los frames evaluados, ya con las celdas de menos de 5 casos suprimidas."""
    game = games.GAME
    info = games.GAMES[game]
    raw, meta, _ = games.require(FICHEROS, game, data_dir)
    trk = tracking.from_files(raw, meta, info["n_video_frames"], info["pitch"], tracking.evaluated_blocks(game),
                              info["fps"])
    eventos = load_smart_tagging.load(game, data_dir)
    return pf.perfil(trk, set_pieces=ventanas_set_pieces(eventos), minimo_celda=MINIMO_CELDA)


def informe_de_error(error):
    """Una línea con el tipo de error y dónde, sin el mensaje: el mensaje podría llevar valores de datos."""
    pila = traceback.extract_tb(error.__traceback__)
    donde = ", ".join("{}:{}".format(os.path.basename(p.filename), p.lineno) for p in pila[-4:])
    return "ERROR {} en {}. Sin valores de datos: se puede pegar tal cual.".format(type(error).__name__, donde)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    inicio = time.time()
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD o el Smart Tagging del partido: revisa que MTAH_DATA_DIR apunte a la carpeta "
              "de los datos.")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # los avisos de numpy no llevan datos, pero ensucian la salida
        salida = pf.para_imprimir(medir(args.data_dir))
    salida = dict({"perfil": "ATD del partido, frames evaluados, las dos partes juntas",
                   "segundos": round(time.time() - inicio)}, **salida)
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
