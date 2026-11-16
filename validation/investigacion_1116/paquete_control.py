"""Sondeo S9: el coste de cambio 40 y las posesiones cortas antes de una parada a `D`, solos y juntos.

    python validation/investigacion_1116/paquete_control.py

Datos abiertos de otros partidos: los 7 de la DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de
SkillCorner (licencia MIT). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. La regla de
lectura está en BITACORA.md (S9), escrita antes de medir. `D` propio siempre.
"""

import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                os.path.join(ROOT, "validation", "apuesta_b"), ROOT, os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, carpeta)
import cambio_antes_de_parada as cap  # noqa: E402
import dfl  # noqa: E402
import lector as lc  # noqa: E402
import puntuar  # noqa: E402
from possession import pipeline  # noqa: E402

D = dfl.D
VERSIONES = ("main", "coste 40", "cortas a D", "coste 40 y cortas a D")


def variantes(trk, ejecutar):
    """{versión: etiquetas}. `ejecutar(params)` devuelve las etiquetas del pipeline con esos params."""
    base, c40 = ejecutar(None), ejecutar({"switch": 40.0})
    out = {"main": base, "coste 40": c40}
    for nombre, pred in (("cortas a D", base), ("coste 40 y cortas a D", c40)):
        nuevo = pred.copy()
        for i, j, _ in cap.candidatas(pred, trk.blocks, 125):
            nuevo[i:j] = D
        out[nombre] = nuevo
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
                def ejecutar(params):
                    v = dict(version)
                    v["params"] = params
                    return puntuar.ejecutar(v, trk, gt["flag"], "propio", partido)
                for nombre, pred in variantes(trk, ejecutar).items():
                    for conv in dfl.CONVENCIONES:
                        rec[("DFL " + conv, modo, cond, nombre)].append(puntuar.contar(gt[conv], pred))
        print("DFL {} en {:.0f} s".format(partido, time.time() - t0), file=sys.stderr, flush=True)
    ids = list(lc.ENTRENAMIENTO)
    lc.exigir_solo_entrenamiento(ids)
    for id_ in ids:
        crudo = lc.leer_crudo(id_)
        for cond in lc.VOTAN:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            trk = puntuar.solo_lectura(trk)
            for nombre, pred in variantes(trk, lambda params: pipeline.run(trk, params=params)).items():
                rec[("SkillCorner", "–", cond, nombre)].append(puntuar.contar(gt, pred))
        print("SkillCorner {}".format(id_), file=sys.stderr, flush=True)
    print("`spellF1` con el `D` propio; entre paréntesis, la diferencia frente a `main` y en cuántos partidos gana.\n")
    print("| etiquetas | balón en los `D` | condición | `main` | " + " | ".join(VERSIONES[1:]) + " |")
    print("|---|---|---|---|" + "---|" * (len(VERSIONES) - 1))
    claves = sorted({k[:3] for k in rec}, key=lambda k: (k[0] != "DFL flag", k[0] != "DFL control", k[1], k[2]))
    for clave in claves:
        base = rec[clave + ("main",)]
        f0 = puntuar.spell_f1(*puntuar.juntar(base))
        celdas = []
        for nombre in VERSIONES[1:]:
            r = rec[clave + (nombre,)]
            f = puntuar.spell_f1(*puntuar.juntar(r))
            gana = sum(puntuar.spell_f1(a["flags"], a["n_pred"]) > puntuar.spell_f1(b["flags"], b["n_pred"])
                       for a, b in zip(r, base))
            celdas.append("{:.3f} ({:+.3f}, {} de {})".format(f, f - f0, gana, len(r)))
        print("| {} | {} | {} | {:.3f} | {} |".format(clave[0], clave[1], clave[2], f0, " | ".join(celdas)))


if __name__ == "__main__":
    main()
