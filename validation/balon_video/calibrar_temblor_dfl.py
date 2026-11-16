"""Calibración en la DFL del temblor del balón: qué ruido gaussiano σ da cada valor de `instrumento.temblor`.

Por qué (`validation/balon_video/BITACORA.md`, «Corrección de la puerta 1b», condición 5): la celda de la emulación
que se lee tiene como σ «el menor de la rejilla cuyo temblor en la DFL (calibrado con la misma función) es igual o
mayor que el que mide la 1b». Este script da ese temblor en la DFL para cada σ, con la misma función que usa el
sondeo del partido: `validation/experimento2/instrumento.py: temblor(x, y, activo)`, la mediana de
|b[t+1] − 2·b[t] + b[t−1]| (norma en x e y) en los frames de juego con los tres frames con balón.

Datos abiertos de otros partidos: los 7 de la Bundesliga (Bassek et al., 2025, CC BY 4.0), con la caché del
experimento 0 y `validation/harness/dfl.py`. Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Qué hace, en cada partido y en cada parte por separado (las diferencias segundas nunca cruzan el descanso):
- **Frames de juego:** `H` o `A` en la convención «flag» del harness.
- **Balón:** la condición `limpio` del harness (tapado solo en los `D` y en sus bordes) y «limpio + σ», con ruido
  gaussiano independiente por eje y por frame. Una sola tirada de normales por partido (semilla fija), escalada por
  σ: los niveles van anidados. Como referencia, sin voto, el balón «como el ATD» del harness.
- **Temblor:** `instrumento.temblor` en cada parte. Por partido y con los 7 juntos, la mediana de **todos** los
  valores |b[t+1] − 2·b[t] + b[t−1]| que entran en la función (no la media de las medianas); el script comprueba
  que con esos mismos valores la mediana de cada parte es exactamente la de `instrumento.temblor`.

Uso, desde la raíz del repo:

    python validation/balon_video/calibrar_temblor_dfl.py            # imprime el informe en markdown
    python validation/balon_video/calibrar_temblor_dfl.py --json F   # además, la tabla de los 7 juntos en F

Con `--partidos J03WMX` mide uno solo, para probar.
"""

import argparse
import collections
import json
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "harness"))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento2"))
import dfl  # noqa: E402
import instrumento as ins  # noqa: E402

SEMILLA = 20261116
SIGMAS_REJILLA = (0.03, 0.06, 0.12, 0.25)  # m: los de la rejilla de la condición 5 (los de `emular_dfl.SIGMAS`)
SIGMAS_INTERPOLAR = (0.02, 0.045, 0.09, 0.18)  # m: solo para interpolar
# 0 = limpio: solo de referencia. No es una σ de la rejilla (la emulación no tiene celdas con σ = 0 salvo la fila de
# comprobación del detector perfecto), así que si la 1b tiembla 0,0224 m o menos la σ que se lee es 0,03, no 0.
SIGMAS = tuple(sorted((0.0,) + SIGMAS_REJILLA + SIGMAS_INTERPOLAR))
REFERENCIA = "como el ATD"  # sin voto: el balón suavizado del harness


def valores_temblor(x, y, activo):
    """Los valores que entran en `instrumento.temblor`, con su mismo criterio, para hacer la mediana de varios tramos."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3:
        return np.empty(0)
    ok = np.isfinite(x[:-2]) & np.isfinite(x[1:-1]) & np.isfinite(x[2:]) & np.asarray(activo)[1:-1]
    d2 = np.hypot(x[2:] - 2 * x[1:-1] + x[:-2], y[2:] - 2 * y[1:-1] + y[:-2])
    return d2[ok]


def por_partes(bx, by, juego, blocks):
    """Los valores de todas las partes juntos, comprobando parte a parte que su mediana es `instrumento.temblor`."""
    trozos = []
    for a, b in blocks:
        v = valores_temblor(bx[a:b], by[a:b], juego[a:b])
        oficial = ins.temblor(bx[a:b], by[a:b], juego[a:b])
        if (oficial is None) != (len(v) == 0) or (oficial is not None and float(np.median(v)) != oficial):
            raise AssertionError("la mediana propia no coincide con instrumento.temblor")
        trozos.append(v)
    return np.concatenate(trozos)


def medir_partido(partido):
    """{nombre del balón: valores del temblor}, y los frames de juego con balón limpio, de un partido."""
    cargado = dfl.cargar(partido)
    gt = cargado["gt"]["flag"]
    juego = (gt == dfl.H) | (gt == dfl.A)
    limpio = dfl.tracking_de(cargado, "limpio")
    rng = np.random.default_rng([SEMILLA, cargado["indice"]])
    ux, uy = rng.standard_normal(len(limpio.bx)), rng.standard_normal(len(limpio.bx))
    valores = collections.OrderedDict()
    for sigma in SIGMAS:
        valores[sigma] = por_partes(limpio.bx + sigma * ux, limpio.by + sigma * uy, juego, limpio.blocks)
    atd = dfl.tracking_de(cargado, REFERENCIA)
    valores[REFERENCIA] = por_partes(atd.bx, atd.by, juego, atd.blocks)
    con_balon = int(np.sum(juego & np.isfinite(limpio.bx)))
    return valores, con_balon


def nombre(clave):
    return clave if isinstance(clave, str) else "limpio" if clave == 0 else "limpio + {:g} m".format(clave).replace(".", ",")


def m(valor):
    return "{:.4f}".format(valor).replace(".", ",")


def informe(resultados, partidos):
    claves = list(resultados[partidos[0]][0])
    juntos = {k: float(np.median(np.concatenate([resultados[p][0][k] for p in partidos]))) for k in claves}
    n_juntos = {k: int(sum(len(resultados[p][0][k]) for p in partidos)) for k in claves}
    lineas = ["## σ → temblor (m), los {} juntos".format(len(partidos)), "",
              "Mediana de todos los valores |b[t+1] − 2·b[t] + b[t−1]| de las dos partes de todos los partidos.", "",
              "| balón | σ (m) | en la rejilla | temblor (m) | temblor / σ | valores |", "|---|---|---|---|---|---|"]
    for k in claves:
        if isinstance(k, str):
            lineas.append("| {} (referencia, sin voto) | – | – | {} | – | {} |".format(k, m(juntos[k]), n_juntos[k]))
            continue
        lineas.append("| {} | {} | {} | {} | {} | {} |".format(
            nombre(k), "{:g}".format(k).replace(".", ","),
            "sí" if k in SIGMAS_REJILLA else "no (referencia: limpio)" if k == 0 else "no (interpolar)",
            m(juntos[k]), "–" if k == 0 else "{:.2f}".format(juntos[k] / k).replace(".", ","), n_juntos[k]))
    lineas += ["", "## Por partido (m)", "",
               "| σ (m) | " + " | ".join(partidos) + " |", "|---|" + "---|" * len(partidos)]
    for k in claves:
        lineas.append("| {} | {} |".format(
            nombre(k), " | ".join(m(float(np.median(resultados[p][0][k]))) for p in partidos)))
    lineas += ["", "Frames de juego con el balón limpio visible: " + ", ".join(
        "{} {}".format(p, resultados[p][1]) for p in partidos) + "."]
    return "\n".join(lineas), juntos, n_juntos


def main():
    parser = argparse.ArgumentParser(description="σ → temblor del balón en la DFL (condición 5 de la puerta 1b).")
    parser.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), choices=list(dfl.PARTIDOS))
    parser.add_argument("--json", metavar="FICHERO", help="escribe la tabla de los partidos juntos en JSON")
    args = parser.parse_args()
    inicio = time.time()
    resultados = collections.OrderedDict()
    for partido in args.partidos:
        resultados[partido] = medir_partido(partido)
        print("hecho {} ({:.0f} s)".format(partido, time.time() - inicio), file=sys.stderr)
    texto, juntos, n_juntos = informe(resultados, args.partidos)
    print("# Temblor del balón en la DFL según σ ({} partidos)".format(len(args.partidos)))
    print()
    print("Función: `validation/experimento2/instrumento.py: temblor`, parte a parte, en los frames de juego (`H` o `A`"
          " en el flag). Semilla {}; ruido N(0, σ²) por eje y frame sobre el balón `limpio` del harness.".format(SEMILLA))
    print()
    print(texto)
    print()
    print("Tiempo: {:.0f} s.".format(time.time() - inicio))
    if args.json:
        salida = {"funcion": "validation/experimento2/instrumento.py:temblor", "semilla": SEMILLA,
                  "partidos": args.partidos, "sigmas_rejilla": list(SIGMAS_REJILLA),
                  "temblor_por_sigma": [{"sigma": k, "temblor": juntos[k], "valores": n_juntos[k]}
                                        for k in juntos if not isinstance(k, str)],
                  "referencia": {"balon": REFERENCIA, "temblor": juntos[REFERENCIA], "valores": n_juntos[REFERENCIA]},
                  "por_partido": {p: {nombre(k): float(np.median(v)) for k, v in resultados[p][0].items()}
                                  for p in args.partidos}}
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(salida, handle, ensure_ascii=False, indent=1)
            handle.write("\n")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
