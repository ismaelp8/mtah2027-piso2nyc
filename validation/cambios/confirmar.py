"""El candidato de la segunda ronda frente al `main` de ahora, que decodifica con «cortas a D» (16/11).

    python validation/cambios/confirmar.py

Datos abiertos (DFL). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

La segunda ronda se midió con `temporal.decode`, que era el decodificador de `main` al lanzarla. Desde `1e71d72` la
entrega usa `temporal.decode_cortas_a_d`. Aquí se repite el candidato que pasó (las reglas afinadas con el balón
«como el vídeo»; w = 0, así que es solo una capa de estados) con el decodificador de la entrega, sin elegir nada: los
umbrales y la combinación son los que salieron en 6 de los 7 pliegues. La regla es la misma (puntos 1 y 3).
"""

import argparse
import concurrent.futures
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import comun  # noqa: E402
import medir  # noqa: E402
from comun import cambios, dfl, pipeline, puntuar  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REGLA = (45.0, 0.6, 30)  # giro, cambio de velocidad y frames de confirmación
GAMMA, VENTANA, CONTRA_D = 8.0, 50, True


# Las celdas de la decisión del 16/11 «el candidato en las celdas que midió la puerta 1b»:
# (fracción buena, fracción equivocada, σ en m, racha media de los frames no buenos).
CELDAS = {"provisional": None, "M1": (0.70, 0.0, 0.03, 12), "M2": (0.74, 0.17, 0.03, 6)}
LEJOS = (3.0, 5.0)  # m: a qué distancia del balón del ATD cae una detección equivocada


def balon_de_celda(cargado, condicion, celda):
    """El tracking con el balón «como el vídeo» de una celda. Con `None`, el de `medir` (la celda provisional)."""
    if celda is None:
        return medir.balones_de(cargado, condicion)["vídeo"][0]
    buena, equivocada, sigma, largo = celda
    trk, limpio = dfl.tracking_de(cargado, condicion), dfl.tracking_de(cargado, "limpio")
    rng = np.random.default_rng([medir.SEMILLA, cargado["indice"], dfl.CONDICIONES.index(condicion), 1])
    n = len(trk.bx)
    estado = np.zeros(n, dtype=np.int8)  # 0 buena, 1 equivocada, 2 sin detección
    dx, dy = np.zeros(n), np.zeros(n)
    media_buena = max(1.0, largo * buena / (1.0 - buena))
    t = int(rng.geometric(1.0 / media_buena))
    while t < n:
        fallo = int(rng.geometric(1.0 / largo))
        if rng.random() < equivocada / (1.0 - buena):
            radio, angulo = rng.uniform(*LEJOS), rng.uniform(0.0, 2.0 * np.pi)
            estado[t:t + fallo] = 1
            dx[t:t + fallo], dy[t:t + fallo] = radio * np.cos(angulo), radio * np.sin(angulo)
        else:
            estado[t:t + fallo] = 2
        t += fallo + int(rng.geometric(1.0 / media_buena))
    rx, ry = rng.normal(0.0, sigma, n), rng.normal(0.0, sigma, n)
    hay = ~np.isnan(trk.bx)
    es_buena = hay & (estado == 0) & ~np.isnan(limpio.bx)
    es_mala = hay & (estado == 1)
    bx = np.where(es_buena, limpio.bx + rx, np.where(es_mala, trk.bx + dx + rx, trk.bx))
    by = np.where(es_buena, limpio.by + ry, np.where(es_mala, trk.by + dy + ry, trk.by))
    return trk._replace(bx=bx, by=by)


def partido(args):
    nombre_partido, celda = args
    cargado, _, bases = comun.cargar(nombre_partido)
    gt = cargado["gt"]
    decode = pipeline.default_piece("temporal")
    recuentos = {}
    for condicion in dfl.VOTAN:
        trk = balon_de_celda(cargado, condicion, CELDAS[celda])
        capa = cambios.capa(cambios.p_reglas(trk, *REGLA), GAMMA, VENTANA, contra_d=CONTRA_D)[0]
        for modo in comun.MODOS_D:
            base = bases[(condicion, modo)]
            preds = {"main": decode(base.score, base.allowed, base.blocks),
                     "candidato": decode(base.score + capa, base.allowed, base.blocks)}
            for quien, pred in preds.items():
                for convencion in dfl.CONVENCIONES:
                    recuentos[(quien, condicion, modo, convencion)] = puntuar.contar(gt[convencion], pred)
    return nombre_partido, recuentos


def main():
    parser = argparse.ArgumentParser(description="El candidato de la segunda ronda con el decodificador de la entrega.")
    parser.add_argument("--celda", choices=sorted(CELDAS), default="provisional")
    celda = parser.parse_args().celda
    partidos = list(dfl.PARTIDOS)
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        recuentos = dict(pool.map(partido, [(p, celda) for p in partidos]))
    print("# El candidato de la segunda ronda con el decodificador de la entrega ({})\n".format(
        pipeline.PIECES["temporal"]))
    print("Código: {} · reglas {} · γ {:g}, W {}, contra el otro equipo · celda «{}»: {}\n".format(
        puntuar.version_del_codigo(), REGLA, GAMMA, VENTANA, celda,
        "p = {}, σ = {} m, L = {}".format(medir.P_VIDEO, medir.SIGMA_VIDEO, medir.L_VIDEO) if CELDAS[celda] is None
        else "buena {}, equivocada {}, σ = {} m, racha media {}".format(*CELDAS[celda])))
    print("| `D` | condición | etiquetas | main | candidato | diferencia [intervalo] | gana en | posesiones: main → "
          "candidato (reales) |")
    print("|---|---|---|---|---|---|---|---|")
    pasa_1, pasa_3 = True, True
    for modo in comun.MODOS_D:
        for condicion in dfl.VOTAN:
            for convencion in dfl.CONVENCIONES[::-1]:
                cand = [recuentos[p][("candidato", condicion, modo, convencion)] for p in partidos]
                ref = [recuentos[p][("main", condicion, modo, convencion)] for p in partidos]
                dif, intervalo, gana = comun.frente_a(cand, ref)
                if convencion == "control":
                    pasa_1 &= dif >= medir.UMBRAL_ENTRADA and gana >= medir.MIN_PARTIDOS
                else:
                    pasa_3 &= dif >= -medir.DANO
                print("| {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} [{:+.3f} a {:+.3f}] | {} de 7 | {} → {} ({}) |".format(
                    "etiquetas" if modo == "oraculo" else "propio", condicion, convencion, comun.spell(ref),
                    comun.spell(cand), dif, intervalo[0], intervalo[1], gana, sum(r["n_pred"] for r in ref),
                    sum(r["n_pred"] for r in cand), sum(r["n_gt"] for r in ref)))
    print("\nRegla: punto 1 **{}** · punto 3 **{}**.".format("pasa" if pasa_1 else "no pasa",
                                                              "pasa" if pasa_3 else "no pasa"))


if __name__ == "__main__":
    main()
