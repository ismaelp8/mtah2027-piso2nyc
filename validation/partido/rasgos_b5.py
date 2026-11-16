"""Los rasgos de B5 en el partido frente a los de los datos abiertos (P2 de validation/investigacion_1116/BITACORA.md).

**Lee datos del partido (el ATD): lo ejecuta una persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/rasgos_b5.py

Es la idea 1.2 de `docs/investigacion_2026-11-16.md`, con la regla escrita antes de ejecutarlo. Calcula los 30 rasgos
de B5 en los frames de los tramos evaluados con el balón visible, igual que
`validation/investigacion_1116/referencia_rasgos_b5.py` en los 17 partidos abiertos, y compara la mediana y el p90 del
valor absoluto de cada rasgo con el rango de los abiertos (`referencia_rasgos_b5.json`, fijada antes).

- Imprime solo agregados del partido entero: medianas y percentiles de cada rasgo sobre decenas de miles de frames, y
  un porcentaje de acuerdo. Nada por frame: la salida se puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.

`comparar(cuantiles, acuerdo, referencia)` es una función pura: la prueba (`validation/scripts/prueba_rasgos_b5.py`)
la ejecuta con números inventados.
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
sys.path.insert(0, os.path.join(ROOT, "validation", "investigacion_1116"))
import games  # noqa: E402
import referencia_rasgos_b5 as ref  # noqa: E402  (validation/investigacion_1116/referencia_rasgos_b5.py)
from possession import tracking  # noqa: E402

FICHEROS = ["atd_raw", "atd_meta"]


def comparar(cuantiles, acuerdo, referencia):
    """Para cada rasgo: (nombre, ¿de los diez?, mediana, p90, rango de la referencia, ¿mediana fuera?, ¿p90 fuera?).
    Y la regla: los de los diez con la mediana fuera."""
    filas = []
    for nombre in sorted(referencia["rango"], key=lambda n: -referencia["importancia"][n]):
        mediana, p90 = cuantiles[nombre]
        lo, hi, lo90, hi90 = referencia["rango"][nombre]
        filas.append({"nombre": nombre, "top": nombre in referencia["top"], "mediana": mediana, "p90": p90,
                      "rango": (lo, hi, lo90, hi90), "fuera": not lo <= mediana <= hi,
                      "fuera_p90": not lo90 <= p90 <= hi90})
    acuerdos = list(referencia["acuerdo_b5_mas_cercano"].values())
    return {"filas": filas, "desplazados": [f["nombre"] for f in filas if f["top"] and f["fuera"]],
            "acuerdo": acuerdo, "acuerdo_rango": (min(acuerdos), max(acuerdos)), "commit": referencia["commit"]}


def para_imprimir(r):
    lineas = [
        "Rasgos de B5 en el partido frente a 17 partidos abiertos (validation/investigacion_1116/BITACORA.md, P2)",
        "Frames de los tramos evaluados con el balón visible. Mediana y p90 del valor absoluto de cada rasgo.",
        "Referencia calculada con el código en {}.".format(r["commit"]),
        "",
        "| rasgo | de los diez | mediana: partido / abiertos (mín–máx) | p90: partido / abiertos (mín–máx) |",
        "|---|---|---|---|",
    ]
    for f in r["filas"]:
        lo, hi, lo90, hi90 = f["rango"]
        lineas.append("| {} | {} | {:.3f}{} / {:.3f}–{:.3f} | {:.3f}{} / {:.3f}–{:.3f} |".format(
            f["nombre"], "sí" if f["top"] else "", f["mediana"], " FUERA" if f["fuera"] else "", lo, hi, f["p90"],
            " fuera" if f["fuera_p90"] else "", lo90, hi90))
    lineas += [
        "",
        "Acuerdo del signo de B5 con el del más cercano (descriptivo): partido {:.1f} %; abiertos de {:.1f} a {:.1f} %".format(
            100 * r["acuerdo"], 100 * r["acuerdo_rango"][0], 100 * r["acuerdo_rango"][1]),
        "",
        "Regla (BITACORA.md P2): ¿la mediana de alguno de los diez rasgos de más peso cae fuera del rango de los abiertos?",
    ]
    if r["desplazados"]:
        lineas.append("   → SÍ: desplazados {}. Siguiente paso: candidato de estandarización por partido, medido en datos "
                      "abiertos (avisar antes a la sesión principal).".format(", ".join(r["desplazados"])))
    else:
        lineas.append("   → NO: los diez caen dentro de lo que se ve en los datos abiertos. Se cierra.")
    return lineas


def leer_referencia():
    with open(ref.SALIDA, encoding="utf-8") as f:
        return json.load(f)


def medir(data_dir=None):
    """La comparación sobre el partido. Lee el ATD del partido: solo lo ejecuta una persona."""
    game = games.GAME
    games.require(FICHEROS, game, data_dir)
    referencia = leer_referencia()
    trk = tracking.from_atd(games.asset_paths(game, data_dir), game)
    matriz, acuerdo = ref.resumen_rasgos(trk)
    return comparar(ref.cuantiles(matriz), acuerdo, referencia)


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
        print("No encuentro el ATD del partido: revisa que MTAH_DATA_DIR (o --data-dir) apunte a la carpeta de los datos.")
        return 1
    if not os.path.isfile(ref.SALIDA):
        print("No encuentro validation/investigacion_1116/referencia_rasgos_b5.json: haz git pull.")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
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
