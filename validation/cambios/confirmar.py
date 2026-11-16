"""El candidato de la segunda ronda frente al `main` de ahora, que decodifica con «cortas a D» (16/11).

    python validation/cambios/confirmar.py

Datos abiertos (DFL). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

La segunda ronda se midió con `temporal.decode`, que era el decodificador de `main` al lanzarla. Desde `1e71d72` la
entrega usa `temporal.decode_cortas_a_d`. Aquí se repite el candidato que pasó (las reglas afinadas con el balón
«como el vídeo»; w = 0, así que es solo una capa de estados) con el decodificador de la entrega, sin elegir nada: los
umbrales y la combinación son los que salieron en 6 de los 7 pliegues. La regla es la misma (puntos 1 y 3).
"""

import concurrent.futures
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import comun  # noqa: E402
import medir  # noqa: E402
from comun import cambios, dfl, pipeline, puntuar  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REGLA = (45.0, 0.6, 30)  # giro, cambio de velocidad y frames de confirmación
GAMMA, VENTANA, CONTRA_D = 8.0, 50, True


def partido(nombre_partido):
    cargado, _, bases = comun.cargar(nombre_partido)
    gt = cargado["gt"]
    decode = pipeline.default_piece("temporal")
    recuentos = {}
    for condicion in dfl.VOTAN:
        trk = medir.balones_de(cargado, condicion)["vídeo"][0]
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
    partidos = list(dfl.PARTIDOS)
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        recuentos = dict(pool.map(partido, partidos))
    print("# El candidato de la segunda ronda con el decodificador de la entrega ({})\n".format(
        pipeline.PIECES["temporal"]))
    print("Código: {} · reglas {} · γ {:g}, W {}, contra el otro equipo · emulación p = {}, σ = {} m, L = {}\n".format(
        puntuar.version_del_codigo(), REGLA, GAMMA, VENTANA, medir.P_VIDEO, medir.SIGMA_VIDEO, medir.L_VIDEO))
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
