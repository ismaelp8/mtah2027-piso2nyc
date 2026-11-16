"""Sondeo S11: encoger nuestras paradas (acabar antes, empezar después), porque alargar una posesión es el error barato.

    python validation/investigacion_1116/encoger_paradas.py

DFL (7 partidos abiertos, Bassek et al., 2025, CC BY 4.0), `main` con su `D` propio. Lo puede ejecutar cualquiera,
Claude incluido. Solo imprime agregados. La regla está en BITACORA.md (S11), escrita antes de medir.
"""

import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "apuesta_b"), ROOT,
                os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, carpeta)
import cambio_antes_de_parada as cap  # noqa: E402
import dfl  # noqa: E402
import puntuar  # noqa: E402
from possession import temporal  # noqa: E402

H, A, D = dfl.H, dfl.A, dfl.D
VERSIONES = ((6, 0), (12, 0), (17, 0), (12, 6), (17, 12))
MINIMO = 25


def encoger(pred, blocks, fin, inicio):
    out = pred.copy()
    for a, b in blocks:
        r = temporal.runs(pred[a:b])
        for k, (etiqueta, i, j) in enumerate(r):
            if etiqueta != D or k == 0 or k == len(r) - 1:
                continue
            antes, despues = r[k - 1][0], r[k + 1][0]
            sobra = max(0, (j - i) - MINIMO)
            f = min(fin, sobra) if despues in (H, A) else 0
            s = min(inicio, sobra - f) if antes in (H, A) else 0
            if f:
                out[a + j - f:a + j] = despues
            if s:
                out[a + i:a + i + s] = antes
    return out


def main():
    version = puntuar.leer_versiones(cap.VERSIONES)[0]["main: B5 y coste 25"]
    rec = collections.defaultdict(list)
    for partido in dfl.PARTIDOS:
        t0 = time.time()
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        for modo, hacer in cap.MODOS.items():
            for cond in dfl.VOTAN:
                trk = puntuar.solo_lectura(hacer(cargado, cond))
                pred = puntuar.ejecutar(version, trk, gt["flag"], "propio", partido)
                for conv in dfl.CONVENCIONES:
                    rec[(conv, modo, cond, "main")].append(puntuar.contar(gt[conv], pred))
                    for f, i in VERSIONES:
                        rec[(conv, modo, cond, (f, i))].append(puntuar.contar(gt[conv], encoger(pred, trk.blocks, f, i)))
        print("DFL {} en {:.0f} s".format(partido, time.time() - t0), file=sys.stderr, flush=True)
    print("`spellF1` con el `D` propio; entre paréntesis, la diferencia frente a `main` y en cuántos de 7 gana. "
          "(f, i): frames que se adelanta el final y que se retrasa el inicio de cada parada nuestra.\n")
    print("| etiquetas | balón en los `D` | condición | `main` | " + " | ".join("({}, {})".format(*v) for v in VERSIONES) + " |")
    print("|---|---|---|---|" + "---|" * len(VERSIONES))
    for conv in dfl.CONVENCIONES:
        for modo in cap.MODOS:
            for cond in dfl.VOTAN:
                base = rec[(conv, modo, cond, "main")]
                f0 = puntuar.spell_f1(*puntuar.juntar(base))
                celdas = []
                for v in VERSIONES:
                    r = rec[(conv, modo, cond, v)]
                    f = puntuar.spell_f1(*puntuar.juntar(r))
                    gana = sum(puntuar.spell_f1(x["flags"], x["n_pred"]) > puntuar.spell_f1(y["flags"], y["n_pred"])
                               for x, y in zip(r, base))
                    celdas.append("{:+.3f} ({})".format(f - f0, gana))
                print("| {} | {} | {} | {:.3f} | {} |".format(conv, modo, cond, f0, " | ".join(celdas)))


if __name__ == "__main__":
    main()
