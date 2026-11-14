"""Apuesta B frente al `D` de la pieza de estado: cuántas paradas se pierden con B2 y con N1. Descriptivo.

    python validation/apuesta_b/d_propio.py

Con el `D` oráculo del harness, lo que la pieza de equipo puntúa en las paradas no cambia nada. Aquí cada
versión pone su `D` con las piezas de `main` (`dead_state.evidence`, el modelo E2 de Ana, que puntúa hasta
±8 en la columna `D`). Se mira cuánto de cada parada real ve como `D` cada versión, con el decodificador
de `main`.

**No decide nada** (README del harness): la DFL tapa el balón en todos los `D`, así que N1 nunca opina en
una parada y le deja el sitio a la pieza de `D`. En el ATD el balón puede verse en las paradas, y entonces
N1 también empujaría contra el `D`. B2 opina con los jugadores, haya balón o no. La comparación favorece a
N1.

Datos abiertos de la DFL: lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.
"""

import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import puntuar  # noqa: E402
from possession import tracking  # noqa: E402

VERSIONES = os.path.join(ROOT, "validation", "harness", "versiones", "apuesta_b.json")
MITAD = 0.5  # una parada «se ve» si la versión pone `D` en al menos la mitad de sus frames


def paradas(gt, blocks):
    """(inicio, fin) de cada racha de `D` real dentro de los tramos evaluados."""
    salida = []
    for a, b in blocks:
        es_d = np.concatenate(([False], gt[a:b] == tracking.D, [False]))
        cambio = np.flatnonzero(np.diff(es_d.astype(np.int8)))
        salida += [(a + i, a + j) for i, j in zip(cambio[::2], cambio[1::2])]
    return salida


def main():
    versiones = puntuar.leer_versiones(VERSIONES)[0]
    nombres = [n for n, v in versiones.items() if v["tipo"] == "pipeline"]
    acumulado = collections.defaultdict(lambda: np.zeros(5, dtype=np.int64))
    recuentos = collections.defaultdict(list)
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        for condicion in dfl.VOTAN:
            trk = puntuar.solo_lectura(dfl.tracking_de(cargado, condicion))
            evaluado = np.zeros(len(trk.bx), bool)
            for a, b in trk.blocks:
                evaluado[a:b] = True
            reales = paradas(gt["flag"], trk.blocks)
            for nombre in nombres:
                pred = puntuar.ejecutar(versiones[nombre], trk, gt["flag"], "propio", partido)
                es_d, real_d = (pred == tracking.D) & evaluado, (gt["flag"] == tracking.D) & evaluado
                vistas = sum(np.mean(pred[i:j] == tracking.D) >= MITAD for i, j in reales)
                acumulado[(nombre, condicion)] += [int(np.sum(es_d & real_d)), int(real_d.sum()),
                                                   int(es_d.sum()), vistas, len(reales)]
                for convencion in dfl.CONVENCIONES:
                    recuentos[(nombre, condicion, convencion)].append(puntuar.contar(gt[convencion], pred))
        print("hecho {}".format(partido), file=sys.stderr)
    print("Con el `D` de las piezas de main (dead_state E2), sin oráculo. DFL, 7 partidos juntos. Descriptivo: "
          "la DFL tapa el balón en los `D`, y eso favorece a N1.")
    print()
    print("| balón | versión | frames `D` reales vistos como `D` | de lo que dice `D`, es `D` | paradas vistas "
          "(≥ mitad de sus frames) | spellF1 flag / control |")
    print("|---|---|---|---|---|---|")
    for condicion in dfl.VOTAN:
        for nombre in nombres:
            bien, reales, dichos, vistas, n = acumulado[(nombre, condicion)]
            f1 = [puntuar.spell_f1(*puntuar.juntar(recuentos[(nombre, condicion, c)])) for c in dfl.CONVENCIONES]
            print("| {} | {} | {:.1f} % | {:.1f} % | {} de {} ({:.1f} %) | {:.3f} / {:.3f} |".format(
                condicion, nombre, 100.0 * bien / max(reales, 1), 100.0 * bien / max(dichos, 1), vistas, n,
                100.0 * vistas / max(n, 1), f1[0], f1[1]).replace(".", ","))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
