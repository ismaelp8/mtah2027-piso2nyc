"""¿Toca una entrega de prueba solo los bordes de las paradas de otra? Los números de los criterios de daño de una capa
de `D` (docs/decisiones.md, 16/11, «el final de cada parada en el golpeo del balón del vídeo»).

**Lee dos entregas nuestras (etiquetas del partido frame a frame): lo ejecuta una persona, en local, nunca Claude**
(regla nº 1 de `CLAUDE.md`).

    python validation/partido/comparar_paradas.py equipo_v8 prueba_golpeo_ventana

Cada entrega es su nombre en `evaluation/results/` (sin `.csv`) o la ruta a un CSV `frame,label`: la primera es la de
antes (la vigente) y la segunda, la de prueba. Solo cuentan los tramos evaluados. **Imprime solo agregados:**
- el sha256 de cada CSV (la de antes tiene que ser la vigente);
- cuántos frames evaluados cambian de etiqueta, cuántos caen a menos de `CERCA_BORDE` frames (10 s) de un borde
  (inicio o fin) de una parada de la de antes y cuántos más lejos, y de qué etiqueta a qué etiqueta;
- las paradas de cada una y cómo se emparejan por solape: nuevas (sin solape con ninguna de antes), que desaparecen,
  partidas (una de antes con dos o más de después) y juntadas (dos o más de antes con una de después);
- de las que se emparejan una a una, cuántas cambian el inicio o el fin, y cuánto (en intervalos gruesos);
- las rachas cortas de la de después (posesiones, juego y paradas de menos de 12 y de 25 frames, como el resumen del
  pipeline), el % de `D` en lo evaluado y las posesiones de cada una;
- la lectura de los criterios que no necesitan nada de fuera.

Los recuentos de frames de 1 a 4 salen como «< 5»; los de paradas y posesiones, tal cual (como el resumen del
pipeline). Ni frames ni momentos. Si falla, solo el tipo de error y las líneas del código. No escribe ficheros.
"""

import argparse
import hashlib
import os
import sys
import traceback

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import games  # noqa: E402
from possession import pipeline, tracking  # noqa: E402

RESULTADOS = os.path.join(ROOT, "evaluation", "results")
CERCA_BORDE = 250  # frames (10 s): un cambio está «en el borde» si cae en los 250 frames a un lado u otro de un borde
MINIMO_CELDA = 5
NOMBRES = {tracking.H: "H", tracking.A: "A", tracking.D: "D", tracking.X: "X"}
# Desplazamiento de un borde (después − antes), en frames: los intervalos de la tabla.
BORDES_DESPLAZAMIENTO = (-125, -25, 0, 1, 26, 126)
ETIQUETAS_DESPLAZAMIENTO = ("más de 5 s antes", "1-5 s antes", "hasta 1 s antes", "igual", "hasta 1 s después",
                            "1-5 s después", "más de 5 s después")
BANDA_D = (15, 60)  # % de `D` en lo evaluado: la banda del plan (§3, 15/11)
MAX_PARADAS = 250


def ruta_de(entrega):
    return entrega if os.path.isfile(entrega) else os.path.join(RESULTADOS, entrega + ".csv")


def celda(n, minimo=MINIMO_CELDA):
    n = int(n)
    return "< {}".format(minimo) if 0 < n < minimo else str(n)


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def paradas(codes, blocks):
    """[(inicio, fin)] de las rachas de `D` dentro de cada tramo (el fin sin incluir), en orden."""
    salida = []
    for a, b in blocks:
        trozo = (np.asarray(codes[a:b]) == tracking.D).astype(np.int8)
        bordes = np.diff(np.concatenate(([0], trozo, [0])))
        salida += [(int(s) + a, int(e) + a) for s, e in zip(np.flatnonzero(bordes == 1), np.flatnonzero(bordes == -1))]
    return salida


def distancia_a_un_borde(frames, rachas):
    """Para cada frame, cuántos frames hay hasta el borde más cercano de `rachas` (0: pegado a él, a un lado u otro).

    Un borde es la frontera de una racha [s, e): en s y en e. Un frame f ≥ borde está a f − borde; uno anterior, a
    borde − 1 − f. Sin rachas, infinito."""
    frames = np.asarray(frames, dtype=np.int64)
    bordes = np.unique(np.array([v for s, e in rachas for v in (s, e)], dtype=np.int64))
    if not len(bordes):
        return np.full(len(frames), np.inf)
    i = np.searchsorted(bordes, frames, side="right")
    izquierda = np.where(i > 0, frames - bordes[np.maximum(i - 1, 0)], np.inf)
    derecha = np.where(i < len(bordes), bordes[np.minimum(i, len(bordes) - 1)] - 1 - frames, np.inf)
    return np.minimum(izquierda, derecha)


def emparejar(antes, despues):
    """(socios_de_antes, socios_de_despues): para cada racha, los índices de las del otro lado con las que se solapa."""
    de_antes = [[j for j, (s2, e2) in enumerate(despues) if s2 < e and e2 > s] for s, e in antes]
    de_despues = [[i for i, (s1, e1) in enumerate(antes) if s1 < e and e1 > s] for s, e in despues]
    return de_antes, de_despues


def repartir_desplazamientos(valores):
    cortes = np.searchsorted(np.array(BORDES_DESPLAZAMIENTO), np.asarray(valores, dtype=np.int64), side="right")
    return {e: int(np.sum(cortes == k)) for k, e in enumerate(ETIQUETAS_DESPLAZAMIENTO)}


def rachas_de(codes, valores):
    if len(codes) == 0:
        return 0
    inicio = np.concatenate(([True], codes[1:] != codes[:-1]))
    return int(np.sum(inicio & np.isin(codes, valores)))


def comparar(antes, despues, blocks):
    """Los recuentos de la comparación (solo enteros: no guarda frames)."""
    antes, despues = np.asarray(antes), np.asarray(despues)
    if len(antes) != len(despues):
        raise ValueError("las dos entregas no tienen el mismo número de frames")
    p_antes, p_despues = paradas(antes, blocks), paradas(despues, blocks)
    distintos = np.concatenate([a + np.flatnonzero(antes[a:b] != despues[a:b]) for a, b in blocks])
    dist = distancia_a_un_borde(distintos, p_antes)
    pares = {}
    for u, v in zip(antes[distintos].tolist(), despues[distintos].tolist()):
        pares[(u, v)] = pares.get((u, v), 0) + 1
    de_antes, de_despues = emparejar(p_antes, p_despues)
    una_a_una = [(i, socios[0]) for i, socios in enumerate(de_antes)
                 if len(socios) == 1 and len(de_despues[socios[0]]) == 1]
    cambian = [(i, j) for i, j in una_a_una if p_antes[i] != p_despues[j]]
    evaluados = int(sum(b - a for a, b in blocks))
    cortas = {}
    for a, b in blocks:
        for clave, n in pipeline.short_runs(despues[a:b]).items():
            cortas[clave] = cortas.get(clave, 0) + n
    return {
        "evaluados": evaluados, "distintos": int(len(distintos)),
        "cerca": int(np.sum(dist < CERCA_BORDE)), "lejos": int(np.sum(dist >= CERCA_BORDE)), "pares": pares,
        "paradas": [len(p_antes), len(p_despues)],
        "nuevas": sum(1 for socios in de_despues if not socios),
        "desaparecen": sum(1 for socios in de_antes if not socios),
        "partidas": sum(1 for socios in de_antes if len(socios) >= 2),
        "juntadas": sum(1 for socios in de_despues if len(socios) >= 2),
        "una_a_una": len(una_a_una), "cambian": len(cambian),
        "cambia_el_fin": sum(1 for i, j in cambian if p_antes[i][1] != p_despues[j][1]),
        "cambia_el_inicio": sum(1 for i, j in cambian if p_antes[i][0] != p_despues[j][0]),
        "desplazamiento_fin": repartir_desplazamientos([p_despues[j][1] - p_antes[i][1] for i, j in cambian]),
        "desplazamiento_inicio": repartir_desplazamientos([p_despues[j][0] - p_antes[i][0] for i, j in cambian]),
        "pct_d": [100.0 * sum(int(np.sum(c[a:b] == tracking.D)) for a, b in blocks) / evaluados
                  for c in (antes, despues)],
        "posesiones": [sum(rachas_de(c[a:b], (tracking.H, tracking.A)) for a, b in blocks) for c in (antes, despues)],
        "cortas": cortas,
    }


def lectura(res):
    """Los criterios de la regla que se leen solo con esta comparación (el de los conflictos y el de las paradas que
    cambian frente a los golpeos se leen con las otras salidas)."""
    cortas_25 = sum(n for (tipo, limite), n in res["cortas"].items() if limite == 25)
    return [
        ("ninguna racha de menos de 25 frames en la de después (posesiones, juego y paradas)", cortas_25 == 0),
        ("ningún cambio a {} frames o más de un borde de una parada de la de antes".format(CERCA_BORDE),
         res["lejos"] == 0),
        ("ninguna parada nueva, ninguna que desaparece, ninguna partida y ninguna juntada",
         res["nuevas"] == res["desaparecen"] == res["partidas"] == res["juntadas"] == 0),
        ("la banda del plan: del {} al {} % de D en lo evaluado y {} paradas como mucho".format(
            BANDA_D[0], BANDA_D[1], MAX_PARADAS),
         BANDA_D[0] <= res["pct_d"][1] <= BANDA_D[1] and res["paradas"][1] <= MAX_PARADAS),
    ]


def lineas(res, nombres, huellas):
    total = res["distintos"]
    salida = [
        "# Paradas de dos entregas: {} (antes) y {} (después)".format(*nombres),
        "",
        "sha256 de antes: {}".format(huellas[0]),
        "sha256 de después: {}".format(huellas[1]),
        "",
        "Frames evaluados: {}. Con etiqueta distinta: {}.".format(res["evaluados"], celda(total)),
        "",
        "| dónde caen los frames que cambian | frames |",
        "|---|---|",
        "| a menos de {} frames (10 s) de un borde de una parada de antes | {} |".format(CERCA_BORDE,
                                                                                     celda(res["cerca"])),
        "| más lejos | {} |".format(celda(res["lejos"])),
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
        "| paradas | |",
        "|---|---|",
        "| antes | {} |".format(res["paradas"][0]),
        "| después | {} |".format(res["paradas"][1]),
        "| nuevas (sin solape con ninguna de antes) | {} |".format(res["nuevas"]),
        "| que desaparecen (sin solape con ninguna de después) | {} |".format(res["desaparecen"]),
        "| partidas (una de antes con dos o más de después) | {} |".format(res["partidas"]),
        "| juntadas (dos o más de antes con una de después) | {} |".format(res["juntadas"]),
        "| emparejadas una a una | {} |".format(res["una_a_una"]),
        "| de ellas, que cambian | {} |".format(res["cambian"]),
        "| de ellas, con otro fin | {} |".format(res["cambia_el_fin"]),
        "| de ellas, con otro inicio | {} |".format(res["cambia_el_inicio"]),
        "",
        "| cuánto se mueve el borde (después − antes), en las que cambian | fin | inicio |",
        "|---|---|---|",
    ]
    for e in ETIQUETAS_DESPLAZAMIENTO:
        salida.append("| {} | {} | {} |".format(e, res["desplazamiento_fin"][e], res["desplazamiento_inicio"][e]))
    salida += [
        "",
        "| | antes | después |",
        "|---|---|---|",
        "| % de D en lo evaluado | {:.1f} | {:.1f} |".format(*res["pct_d"]).replace(".", ","),
        "| posesiones (rachas de `H` o de `A`) | {} | {} |".format(*res["posesiones"]),
        "",
        "Rachas cortas de la de después, en los dos tramos: " + "; ".join(
            "de menos de {} frames, {} posesiones, {} de juego y {} paradas".format(
                limite, res["cortas"][("posesiones", limite)], res["cortas"][("juego", limite)],
                res["cortas"][("paradas", limite)]) for limite in pipeline.SHORT_RUNS) + ".",
        "",
        "Lectura de los criterios que se leen aquí:",
    ]
    salida += ["- {}: {}".format(texto, "cumple" if ok else "NO CUMPLE") for texto, ok in lectura(res)]
    salida.append("- las paradas que cambian ({}) se comparan con los golpeos que usa la capa (salida de "
                  "balon_video_golpeo.py); los conflictos, con la salida del pipeline.".format(res["cambian"]))
    return salida


def informe_de_error(error):
    """Tipo de error y líneas del código, sin el mensaje: podría llevar valores de datos."""
    pila = traceback.extract_tb(error.__traceback__)
    donde = " <- ".join("{}:{}".format(os.path.basename(f.filename), f.lineno) for f in reversed(pila[-4:]))
    return "ERROR {} en {}. Sin valores de datos: se puede pegar tal cual.".format(type(error).__name__, donde)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("antes", help="la entrega de antes (la vigente): nombre en evaluation/results (sin .csv) o ruta")
    ap.add_argument("despues", help="la entrega de prueba, igual")
    args = ap.parse_args(argv)
    rutas = [ruta_de(args.antes), ruta_de(args.despues)]
    for ruta in rutas:
        if not os.path.isfile(ruta):
            print("No encuentro una de las entregas: pasa su nombre en evaluation/results (sin .csv) o la ruta.")
            return 1
    import possession_metrics as pm  # aquí: necesita pandas
    codigos = [np.asarray(pm.label_codes(pm.read_label_csv(ruta))) for ruta in rutas]
    res = comparar(codigos[0], codigos[1], tracking.evaluated_blocks(games.GAME))
    print("\n".join(lineas(res, [os.path.basename(r) for r in rutas], [sha256(r) for r in rutas])))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
