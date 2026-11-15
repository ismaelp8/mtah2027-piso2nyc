"""¿Llega el balón del ATD con retraso respecto a los jugadores? La medida de `validation/retraso_balon/BITACORA.md`.

**Lee datos del partido: lo ejecuta una persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`). Y solo
si la calibración en la DFL ha pasado (bitácora §3).

    python validation/partido/retraso_balon.py

- Lee el ATD con `possession/tracking.py`, el mismo lector que el pipeline, con el balón tal cual (el de la
  entrega, `ball.clean` v0). Mide los frames evaluados con `validation/retraso_balon/retraso.py`, el mismo
  código que mide la DFL en `validation/retraso_balon/calibrar_dfl.py`.
- Imprime solo agregados del partido entero: recuentos de rachas y de frames, el desfase, su intervalo, el
  desfase de cada parte, correlaciones del conjunto y la lectura de la bitácora §5. Una celda de 1 a 4 casos
  sale como "< 5". Nada por minuto, por jugada ni por frame: la salida se puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero. Tarda unos segundos, casi todo leyendo el ATD.

Cómo se lee está fijado antes de ejecutarlo, en la bitácora §5. Después de ver los números no se retoca nada.

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
    """Las líneas de la salida, con las celdas pequeñas suprimidas. Los controles salen siempre."""
    candidato, porque = rt.lectura(res)
    p5, p95 = res["intervalo"]
    lineas = [
        "Retraso del balón del ATD (validation/retraso_balon/BITACORA.md): frames evaluados, las dos partes juntas",
        "",
        "0. Controles (el perfil del ATD dice {} y {})".format(PERFIL_EVALUADOS, PERFIL_CON_BALON),
        "   frames evaluados: {}".format(res["frames_evaluados"]),
        "   frames evaluados con balón: {}".format(res["frames_con_balon"]),
        "   ¿cuadran los dos? {}".format("sí" if (res["frames_evaluados"], res["frames_con_balon"]) ==
                                          (PERFIL_EVALUADOS, PERFIL_CON_BALON) else "NO"),
        "",
        "1. Rachas de conducción (mismo slot a {:g} m o menos, {} frames o más)".format(rt.RADIO, rt.MIN_RACHA),
        "   rachas: {}   frames en rachas: {}".format(celda(res["rachas"], minimo),
                                                      celda(res["frames_en_rachas"], minimo)),
        "   rachas por parte: {}".format(", ".join(celda(n, minimo) for n in res["rachas_por_tramo"])),
        "",
        "2. Desfase L̂ (L̂ > 0: el balón llega tarde)",
        "   L̂ = {} frames   intervalo del 5 al 95 %: [{}, {}]   correlación en el pico: {}".format(
            desfase(res["desfase"]), numero(p5, 1), numero(p95, 1), numero(res["correlacion_pico"])),
        "   L̂ por parte: {}".format(", ".join(desfase(d) for d in res["desfase_por_tramo"])),
        "   con el módulo de la velocidad (descriptivo): {}".format(desfase(res["desfase_modulo"])),
        "   correlación por desfase (descriptivo):",
        "      " + "  ".join("{:+d}: {}".format(d, numero(res["correlacion"].get(d))) for d in CURVA),
        "",
        "3. Lectura (bitácora §5): {}".format(candidato),
        "   " + porque,
    ]
    return lineas


def medir(data_dir=None):
    """La medida sobre el ATD del partido. Lee datos del partido: solo lo ejecuta una persona."""
    games.require(FICHEROS, games.GAME, data_dir)
    trk = tracking.from_atd(games.asset_paths(games.GAME, data_dir), games.GAME)
    return rt.resumen([rt.sumas(trk)])


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
