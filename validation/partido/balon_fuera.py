"""D7: cuando el ATD ve el balón fuera del campo, ¿decimos ya `D`? Recuentos del partido entero.

**Lee el ATD del partido y una entrega nuestra (etiquetas frame a frame): lo ejecuta una persona, en local,
nunca Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/balon_fuera.py                 # contra evaluation/results/equipo_v3.csv
    python validation/partido/balon_fuera.py --entrega equipo_v4

Para qué (`docs/decisiones.md`, 15/11, «D7, el balón fuera del campo: peso y regla del recuento, antes de
ejecutarlo»): saber cuánto premio hay en una capa que puntúe `D` donde el balón se ve fuera. Si casi siempre
decimos ya `D`, o llegamos tarde muy pocas veces, la pregunta se cierra.

- **Balón fuera:** visto a más de `MARGEN` m fuera de las líneas (la definición del plan, tarea 2 de Manuel),
  con el balón como lo ve el pipeline (`pipeline.default_piece("ball")`).
- **Solo los tramos evaluados,** sin el tramo antes del saque de la 2ª parte, que ya es `D` por construcción.
- **Racha de balón fuera:** frames seguidos con el balón visto fuera, de `RACHA_MINIMA` o más.
- **Llegamos tarde** a una racha si empieza con `H` o `A` y nuestro `D` empieza más de `TARDE` frames
  después de su inicio, o no llega en `HORIZONTE` frames.

**Imprime solo agregados:** frames con el balón fuera por etiqueta, rachas por lado (fondo o banda) y por
cuánto tarda nuestro `D`. Una celda de 1 a 4 casos sale como «< 5». Ni frames ni momentos. Si falla, imprime
solo el tipo de error y las líneas del código. No escribe ficheros.

**La regla, fijada antes de ejecutarlo:**
- **se cierra** si las rachas en que llegamos tarde son menos de 10 o menos del 15 % de las rachas;
- **queda abierta** si son 10 o más y el 25 % o más. Abierta no enciende nada: con el peso fijado antes
  (`validation/scripts/peso_balon_fuera.py`, W = 0) la capa no aporta, así que haría falta una decisión
  nueva sobre el peso;
- en medio, no concluye, y no se abre nada.
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
from possession import dead_ball, pipeline, tracking  # noqa: E402

RESULTADOS = os.path.join(ROOT, "evaluation", "results")
MARGEN = 1.0  # m fuera de las líneas (docs/PLAN_ENTREGA.md §3, tarea 2 de Manuel)
RACHA_MINIMA = 5  # frames: más corta, es temblor
TARDE = 12  # frames (0,5 s): en la tabla de retrasos de spellF1, 8 frames ya cuestan
HORIZONTE = 250  # frames (10 s)
INTERVALOS = ((1, 12), (13, 25), (26, 50), (51, 125), (126, 250))  # frames hasta nuestro `D`
MINIMO_CELDA = 5
POCAS, PARTE_CIERRA, PARTE_ABRE = 10, 0.15, 0.25


def celda(n, minimo=MINIMO_CELDA):
    return "< {}".format(minimo) if 0 < n < minimo else str(n)


def fuera_del_campo(bx, by, pitch, margen=MARGEN):
    """Frames con el balón visto a más de `margen` m fuera: (fuera, por el fondo)."""
    largo, ancho = pitch
    with np.errstate(invalid="ignore"):
        fondo = (bx < -margen) | (bx > largo + margen)
        banda = (by < -margen) | (by > ancho + margen)
    visto = np.isfinite(bx) & np.isfinite(by)
    return visto & (fondo | banda), visto & fondo


def rachas(mascara):
    """(inicio, fin) de cada racha de True, con el fin sin incluir."""
    bordes = np.diff(np.concatenate(([0], mascara.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(bordes == 1).tolist(), np.flatnonzero(bordes == -1).tolist()))


def medir(bx, by, etiquetas, blocks, pitch, excluidos):
    """Recuentos del balón fuera frente a una entrega. Solo enteros: no guarda frames."""
    fuera, fondo = fuera_del_campo(bx, by, pitch)
    out = {"vistos": 0, "fuera": 0, "por_etiqueta": {pm.H: 0, pm.A: 0, pm.D: 0, pm.X: 0},
           "rachas": 0, "rachas_cortas": 0, "por_lado": {"fondo": 0, "banda": 0},
           "ya_en_d": 0, "tarde": {k: 0 for k in INTERVALOS}, "sin_d": 0}
    for a, b in blocks:
        cuenta = ~excluidos[a:b]
        f, e = fuera[a:b] & cuenta, np.asarray(etiquetas[a:b])
        out["vistos"] += int(np.sum(np.isfinite(bx[a:b]) & np.isfinite(by[a:b]) & cuenta))
        out["fuera"] += int(f.sum())
        for codigo in out["por_etiqueta"]:
            out["por_etiqueta"][codigo] += int(np.sum(f & (e == codigo)))
        es_d = e == pm.D
        for inicio, fin in rachas(f):
            if fin - inicio < RACHA_MINIMA:
                out["rachas_cortas"] += 1
                continue
            out["rachas"] += 1
            out["por_lado"]["fondo" if fondo[a + inicio:a + fin].any() else "banda"] += 1
            if es_d[inicio]:
                out["ya_en_d"] += 1
                continue
            despues = np.flatnonzero(es_d[inicio:min(inicio + HORIZONTE + 1, b - a)])
            if not len(despues):
                out["sin_d"] += 1
                continue
            espera = int(despues[0])
            for bajo, alto in INTERVALOS:
                if bajo <= espera <= alto:
                    out["tarde"][(bajo, alto)] += 1
    return out


def llegamos_tarde(res):
    """Rachas que empiezan con `H` o `A` y en las que nuestro `D` llega más de TARDE frames después, o no llega."""
    return res["sin_d"] + sum(n for (bajo, _), n in res["tarde"].items() if bajo > TARDE)


def lectura(res):
    tarde, total = llegamos_tarde(res), res["rachas"]
    parte = tarde / float(total) if total else 0.0
    if tarde < POCAS or parte < PARTE_CIERRA:
        return "se cierra"
    if parte >= PARTE_ABRE:
        return "queda abierta (hace falta una decisión nueva sobre el peso)"
    return "no concluye: no se abre nada"


def lineas(res, nombre):
    total = res["rachas"]
    porcentaje = (lambda n: "–" if 0 < n < MINIMO_CELDA else "{:.1f} %".format(
        100.0 * n / max(total, 1)).replace(".", ","))
    salida = [
        "# D7: el balón visto fuera del campo frente a {}".format(nombre),
        "",
        "Frames evaluados con balón (sin el tramo antes del saque de la 2ª parte): {}. Con el balón a más de "
        "{:g} m fuera: {}.".format(res["vistos"], MARGEN, celda(res["fuera"])),
        "",
        "| etiqueta de la entrega en esos frames | frames |",
        "|---|---|",
    ]
    for codigo, letra in ((pm.D, "D"), (pm.H, "H"), (pm.A, "A"), (pm.X, "X")):
        salida.append("| {} | {} |".format(letra, celda(res["por_etiqueta"][codigo])))
    salida += [
        "",
        "Rachas de balón fuera de {} frames o más: {} ({} por el fondo y {} por la banda). Más cortas, que no "
        "cuentan: {}.".format(RACHA_MINIMA, total, celda(res["por_lado"]["fondo"]),
                              celda(res["por_lado"]["banda"]), celda(res["rachas_cortas"])),
        "",
        "| al empezar la racha | rachas | % |",
        "|---|---|---|",
        "| ya decimos `D` | {} | {} |".format(celda(res["ya_en_d"]), porcentaje(res["ya_en_d"])),
    ]
    for (bajo, alto), n in res["tarde"].items():
        salida.append("| decimos `H` o `A`, y nuestro `D` llega de {} a {} frames después | {} | {} |".format(
            bajo, alto, celda(n), porcentaje(n)))
    salida += [
        "| decimos `H` o `A`, y nuestro `D` no llega en {} frames | {} | {} |".format(
            HORIZONTE, celda(res["sin_d"]), porcentaje(res["sin_d"])),
        "",
        "Llegamos tarde (más de {} frames, o no llega): {} de {} rachas ({}).".format(
            TARDE, celda(llegamos_tarde(res)), total, porcentaje(llegamos_tarde(res))),
        "Lectura con la regla fijada antes: {}.".format(lectura(res)),
    ]
    return salida


def informe_de_error(error):
    """Tipo de error y líneas del código, sin el mensaje: podría llevar valores de datos."""
    pila = traceback.extract_tb(error.__traceback__)
    donde = " <- ".join("{}:{}".format(os.path.basename(f.filename), f.lineno) for f in reversed(pila[-4:]))
    return "ERROR {} en {}. Sin valores de datos: se puede pegar tal cual.".format(type(error).__name__, donde)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entrega", default="equipo_v3",
                    help="nombre en evaluation/results (sin .csv) o ruta a un CSV; por defecto, equipo_v3")
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    ruta = args.entrega if os.path.isfile(args.entrega) else os.path.join(RESULTADOS, args.entrega + ".csv")
    if not os.path.isfile(ruta):
        print("No encuentro la entrega: pasa su nombre en evaluation/results (sin .csv) o la ruta.")
        return 1
    game = games.GAME
    games.require(["atd_raw", "atd_meta"], game, args.data_dir)
    trk = pipeline.default_piece("ball")(tracking.from_atd(games.asset_paths(game, args.data_dir), game))
    etiquetas = pm.label_codes(pm.read_label_csv(ruta))
    if len(etiquetas) != len(trk.bx):
        print("La entrega y el ATD no tienen el mismo número de frames.")
        return 1
    res = medir(trk.bx, trk.by, etiquetas, trk.blocks, trk.pitch, dead_ball.pre_kickoff(game))
    print("\n".join(lineas(res, os.path.basename(ruta))))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
