"""¿Llega el balón del ATD con retraso respecto a los jugadores? La versión 2 de `validation/retraso_balon/BITACORA.md`.

**Lee datos del partido: lo ejecuta una persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`). Y solo
si la calibración de la versión 2 en la DFL ha pasado (bitácora §8.3). La versión 1 no pasó la suya (§7) y
nunca se ejecutó en el partido.

    python validation/partido/retraso_balon.py

- Primero calcula, desde la caché de la DFL (datos abiertos), la familia de curvas de los 7 partidos y el
  residuo de referencia (`validation/retraso_balon/calibrar_dfl_v2.py`). Necesita la DFL bajada.
- Después lee el ATD con `possession/tracking.py`, el mismo lector que el pipeline, con el balón tal cual (el
  de la entrega, `ball.clean` v0). Mide los frames evaluados con `validation/retraso_balon/retraso.py`, el
  mismo código que mide la DFL.
- Imprime solo agregados del partido entero: recuentos de rachas y de frames, el desfase, su intervalo, el
  desfase de cada parte, los residuos, el máximo de la versión 1, correlaciones del conjunto y la lectura de
  la bitácora §8.5. Una celda de 1 a 4 casos sale como "< 5". Nada por minuto, por jugada ni por frame: la
  salida se puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero. Tarda un par de minutos, casi todo con la DFL.

Cómo se lee está fijado antes de ejecutarlo, en la bitácora §8.5. Después de ver los números no se retoca
nada.

`para_imprimir(resumen)` es una función pura: la prueba (`validation/scripts/prueba_retraso_balon.py`) la
ejecuta con un tracking inventado.
"""

import argparse
import os
import sys
import time
import traceback
import warnings

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "retraso_balon"))
import calibrar_dfl_v2 as cal  # noqa: E402  (validation/retraso_balon/: la familia de la DFL)
import games  # noqa: E402
import retraso as rt  # noqa: E402
from possession import tracking  # noqa: E402

FICHEROS = ["atd_raw", "atd_meta"]
MINIMO_CELDA = 5
# Lo que se espera ver, fijado antes de ejecutar: los controles del perfil del ATD.
PERFIL_EVALUADOS, PERFIL_CON_BALON = 158857, 94214
# Desfases de la curva que se imprimen (además del pico).
CURVA = (-24, -18, -12, -6, -3, 0, 3, 6, 9, 12, 15, 18, 24)


def celda(n, minimo=MINIMO_CELDA):
    """Un recuento para imprimir: de 1 a minimo − 1 casos sale como "< 5"."""
    return "< {}".format(minimo) if 0 < n < minimo else str(n)


def numero(valor, decimales=3):
    return "—" if valor is None else "{:.{}f}".format(valor, decimales).replace(".", ",")


def desfase(valor):
    return "—" if valor is None else "{:+d}".format(valor)


def para_imprimir(res, minimo=MINIMO_CELDA):
    """Las líneas de la salida, con las celdas pequeñas suprimidas. Los controles salen siempre.

    `res` es un `retraso.resumen_v2` con, además, `residuo_referencia` y `partidos_familia`.
    """
    candidato, porque = rt.lectura_v2(res, res["residuo_referencia"])
    p5, p95 = res["intervalo"]
    lineas = [
        "Retraso del balón del ATD, versión 2 (validation/retraso_balon/BITACORA.md §8): frames evaluados, las dos "
        "partes juntas",
        "",
        "0. Controles (el perfil del ATD dice {} y {}; la familia, 7 partidos de la DFL)".format(
            PERFIL_EVALUADOS, PERFIL_CON_BALON),
        "   frames evaluados: {}".format(res["frames_evaluados"]),
        "   frames evaluados con balón: {}".format(res["frames_con_balon"]),
        "   partidos de la DFL en la familia: {}".format(res["partidos_familia"]),
        "   ¿cuadran los tres? {}".format("sí" if (res["frames_evaluados"], res["frames_con_balon"],
                                                   res["partidos_familia"]) ==
                                           (PERFIL_EVALUADOS, PERFIL_CON_BALON, 7) else "NO"),
        "",
        "1. Rachas de conducción (mismo slot a {:g} m o menos, {} frames o más)".format(rt.RADIO, rt.MIN_RACHA),
        "   rachas: {}   frames en rachas: {}".format(celda(res["rachas"], minimo),
                                                      celda(res["frames_en_rachas"], minimo)),
        "   rachas por parte: {}".format(", ".join(celda(n, minimo) for n in res["rachas_por_tramo"])),
        "",
        "2. Desfase d̂ (d̂ > 0: el balón llega tarde)",
        "   d̂ = {} frames   intervalo del 5 al 95 %: [{}, {}]".format(desfase(res["desfase"]), numero(p5, 1),
                                                                    numero(p95, 1)),
        "   d̂ por parte: {}".format(", ".join(desfase(d) for d in res["desfase_por_tramo"])),
        "   residuo: {}   de referencia (DFL): {}   (no concluye si pasa de {:g} veces)".format(
            numero(res["residuo"]), numero(res["residuo_referencia"]), rt.MAX_RESIDUO_RELATIVO),
        "",
        "3. Descriptivo, no decide",
        "   L̂ de la versión 1 (máximo de la curva): {}   por parte: {}   con el módulo: {}".format(
            desfase(res["desfase_maximo"]), ", ".join(desfase(d) for d in res["desfase_maximo_por_tramo"]),
            desfase(res["desfase_modulo"])),
        "   correlación por desfase:",
        "      " + "  ".join("{:+d}: {}".format(d, numero(res["correlacion"].get(d))) for d in CURVA),
        "",
        "4. Lectura (bitácora §8.5): {}".format(candidato),
        "   " + porque,
    ]
    return lineas


def hay_dfl():
    """¿Están los 7 partidos de la DFL en la caché? Solo mira si existen los ficheros."""
    carpeta = cal.dfl.dfl_lector.carpeta_cache()
    return all(os.path.isfile(os.path.join(carpeta, "{}.npz".format(p))) for p in cal.dfl.PARTIDOS)


def medir(data_dir=None):
    """La medida sobre el ATD del partido. Lee datos del partido: solo lo ejecuta una persona."""
    games.require(FICHEROS, games.GAME, data_dir)
    familia, referencia, partidos = cal.familia_y_referencia()
    trk = tracking.from_atd(games.asset_paths(games.GAME, data_dir), games.GAME)
    res = rt.resumen_v2([rt.sumas(trk)], familia)
    res.update({"residuo_referencia": referencia, "partidos_familia": partidos})
    return res


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
        print("No encuentro el ATD del partido: revisa que MTAH_DATA_DIR apunte a la carpeta de los datos.")
        return 1
    if not hay_dfl():
        print("Falta la caché de la DFL: baja los datos abiertos (validation/PASOS.md, paso 1) y vuelve a probar.")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # los avisos de numpy no llevan datos, pero ensucian la salida
        lineas = para_imprimir(medir(args.data_dir))
    print("\n".join(lineas))
    print("\n   tiempo {:.0f} s".format(time.time() - inicio))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
