"""¿Cuánto cambia una entrega nuestra respecto a otra, y dónde? Recuentos del partido entero.

**Lee dos entregas nuestras (etiquetas del partido frame a frame): lo ejecuta una persona, en local, nunca
Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/comparar_entregas.py equipo_v3 equipo_v4

- Cada entrega es su nombre en `evaluation/results/` (sin `.csv`) o la ruta a un CSV `frame,label`. La primera
  es la de antes y la segunda, la nueva.

Para qué: cuando una pieza cambia y la entrega se regenera, decir cuánto cambia y dónde sin enseñar ninguna
etiqueta. Por ejemplo, un cambio que solo debería tocar los bordes de los tramos evaluados
(`docs/decisiones.md`, 15/11, «el estado con jugadores no mira fuera de los tramos evaluados»).

**Imprime solo agregados del partido entero:**
- cuántos frames evaluados cambian de etiqueta, y cuántos de ellos caen a 52 frames o menos del borde de un
  tramo evaluado, de 53 a 250, o más lejos;
- de qué etiqueta a qué etiqueta cambian;
- cuántos frames cambian fuera de los tramos evaluados;
- las posesiones y las paradas de cada entrega.

Una celda de 1 a 4 casos sale como «< 5». Ni frames ni momentos. Si falla, imprime solo el tipo de error y las
líneas del código. No escribe ficheros.
"""

import argparse
import os
import sys
import traceback

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import games  # noqa: E402
import possession_metrics as pm  # noqa: E402
from possession import tracking  # noqa: E402

RESULTADOS = os.path.join(ROOT, "evaluation", "results")
CERCA = 52  # frames: la ventana más larga de la pieza de estado (50) más el desfase de su velocidad (2)
MEDIO = 250  # frames: 10 s
MINIMO_CELDA = 5
NOMBRES = {pm.H: "H", pm.A: "A", pm.D: "D", pm.X: "X"}


def ruta_de(entrega):
    return entrega if os.path.isfile(entrega) else os.path.join(RESULTADOS, entrega + ".csv")


def celda(n, minimo=MINIMO_CELDA):
    return "< {}".format(minimo) if 0 < n < minimo else str(n)


def rachas(codigos, valores):
    """Cuántas rachas seguidas hay de cada valor de `valores` en `codigos`."""
    if len(codigos) == 0:
        return 0
    inicio = np.concatenate(([True], codigos[1:] != codigos[:-1]))
    return int(np.sum(inicio & np.isin(codigos, valores)))


def comparar(antes, despues, blocks):
    """Recuentos de la comparación. Solo enteros: no guarda frames."""
    antes, despues = np.asarray(antes), np.asarray(despues)
    if len(antes) != len(despues):
        raise ValueError("las dos entregas no tienen el mismo número de frames")
    dentro = np.zeros(len(antes), dtype=bool)
    out = {"evaluados": 0, "distintos": 0, "cerca": 0, "medio": 0, "lejos": 0, "pares": {},
           "posesiones": [0, 0], "paradas": [0, 0]}
    for a, b in blocks:
        dentro[a:b] = True
        x, y = antes[a:b], despues[a:b]
        distinto = np.flatnonzero(x != y)
        distancia = np.minimum(distinto, (b - a - 1) - distinto)
        out["evaluados"] += b - a
        out["distintos"] += len(distinto)
        out["cerca"] += int(np.sum(distancia <= CERCA))
        out["medio"] += int(np.sum((distancia > CERCA) & (distancia <= MEDIO)))
        out["lejos"] += int(np.sum(distancia > MEDIO))
        for u, v in zip(x[distinto].tolist(), y[distinto].tolist()):
            out["pares"][(u, v)] = out["pares"].get((u, v), 0) + 1
        for k, codigos in enumerate((x, y)):
            out["posesiones"][k] += rachas(codigos, (pm.H, pm.A))
            out["paradas"][k] += rachas(codigos, (pm.D,))
    out["fuera"] = int(np.sum((antes != despues) & ~dentro))
    return out


def lineas(res, nombres):
    """Las líneas de la salida, con las celdas pequeñas suprimidas."""
    total = res["distintos"]
    porcentaje = "–" if 0 < total < MINIMO_CELDA else "{:.3f} %".format(
        100.0 * total / max(res["evaluados"], 1)).replace(".", ",")
    salida = [
        "# Comparación de dos entregas: {} (antes) y {} (después)".format(*nombres),
        "",
        "Frames evaluados: {}. Con etiqueta distinta: {} ({}).".format(res["evaluados"], celda(total), porcentaje),
        "",
        "| distancia al borde del tramo evaluado más cercano | frames con etiqueta distinta |",
        "|---|---|",
        "| {} frames o menos | {} |".format(CERCA, celda(res["cerca"])),
        "| de {} a {} | {} |".format(CERCA + 1, MEDIO, celda(res["medio"])),
        "| más de {} | {} |".format(MEDIO, celda(res["lejos"])),
        "",
        "| antes → después | frames |",
        "|---|---|",
    ]
    for (u, v), n in sorted(res["pares"].items()):
        salida.append("| {} → {} | {} |".format(NOMBRES[u], NOMBRES[v], celda(n)))
    if not res["pares"]:
        salida.append("| (ninguno) | 0 |")
    salida += [
        "",
        "Frames con etiqueta distinta fuera de los tramos evaluados (no cuentan para la nota): {}.".format(
            celda(res["fuera"])),
        "",
        "| | antes | después |",
        "|---|---|---|",
        "| posesiones (rachas de `H` o de `A`) | {} | {} |".format(*res["posesiones"]),
        "| paradas (rachas de `D`) | {} | {} |".format(*res["paradas"]),
    ]
    return salida


def informe_de_error(error):
    """Tipo de error y líneas del código, sin el mensaje: podría llevar valores de datos."""
    pila = traceback.extract_tb(error.__traceback__)
    donde = " <- ".join("{}:{}".format(os.path.basename(f.filename), f.lineno) for f in reversed(pila[-4:]))
    return "ERROR {} en {}. Sin valores de datos: se puede pegar tal cual.".format(type(error).__name__, donde)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("antes", help="la entrega de antes: nombre en evaluation/results (sin .csv) o ruta a un CSV")
    ap.add_argument("despues", help="la entrega nueva, igual")
    args = ap.parse_args(argv)
    rutas = [ruta_de(args.antes), ruta_de(args.despues)]
    for ruta in rutas:
        if not os.path.isfile(ruta):
            print("No encuentro una de las entregas: pasa su nombre en evaluation/results (sin .csv) o la ruta.")
            return 1
    codigos = [pm.label_codes(pm.read_label_csv(ruta)) for ruta in rutas]
    res = comparar(codigos[0], codigos[1], tracking.evaluated_blocks(games.GAME))
    print("\n".join(lineas(res, [os.path.basename(r) for r in rutas])))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
