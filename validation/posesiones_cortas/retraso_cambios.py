"""¿Llegamos tarde a los cambios de equipo? Retraso con signo hasta ±4 s. Descriptivo, solo agregados.

    python validation/posesiones_cortas/retraso_cambios.py

DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`). Lo
puede ejecutar cualquiera, Claude incluido. **No decide nada** (BITACORA.md §12). Sale de una hipótesis del
visionado de la ventana pública (llegaríamos unos 2 s tarde): aquí se mira en datos abiertos, nunca en la
ventana.

`main` (B5, coste 25) con el `D` de las etiquetas. Cada cambio real directo de equipo (`H` a `A` o al revés) se
empareja con un cambio nuestro al mismo equipo a ±100 frames (emparejamiento del scorer oficial,
`match_transitions`). Se da el reparto del retraso con signo (positivo es tarde).
"""

import collections
import functools
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                 os.path.join(ROOT, "validation", "scripts"), os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import diagnostico_errores as de  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline  # noqa: E402

TOLERANCIA = 100
BANDAS = ((-100, -51, "pronto 2–4 s"), (-50, -26, "pronto 1–2 s"), (-25, 25, "a ±1 s"), (26, 50, "tarde 1–2 s"),
          (51, 100, "tarde 2–4 s"))


def retrasos(gt, pred):
    runs = pm.valid_runs(gt)
    reales = de.cambios_directos(gt, runs)
    nuestros = de.cambios_directos(pm.fill_abstentions(pred, runs), runs)
    parejas, _, _ = pm.match_transitions(reales, nuestros, TOLERANCIA, typed="to")
    return len(reales), [p[0] - r[0] for r, p in parejas]


def imprimir(nombre, n, r):
    r = np.asarray(r)
    celdas = ["{:.0f} %".format(100.0 * np.sum((r >= a) & (r <= b)) / n) for a, b, _ in BANDAS]
    print("| {} | {} | {} | {:.0f} % | {} |".format(nombre, n, " | ".join(celdas), 100.0 * (n - len(r)) / n,
                                                   "{:+.0f}".format(np.median(r)) if len(r) else "–"))


def main():
    print("# ¿Llegamos tarde a los cambios de equipo? (descriptivo; `D` de las etiquetas)\n")
    print("Cambios reales directos de equipo, con un cambio nuestro al mismo equipo a ±{} frames o sin él. Positivo es "
          "tarde.\n".format(TOLERANCIA))
    print("| fuente | cambios reales | " + " | ".join(n for _, _, n in BANDAS) + " | sin cambio nuestro a ±4 s | "
          "mediana de los emparejados (frames) |")
    print("|---|---|" + "---|" * len(BANDAS) + "---|---|")
    acc = collections.defaultdict(lambda: [0, []])
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        piezas = {"candidates": functools.partial(aprendida.evidence_b5, fuera=partido)}
        for cond in dfl.VOTAN:
            trk = puntuar.solo_lectura(dfl.tracking_de(cargado, cond))
            pred = pipeline.run(trk, extra=[puntuar.d_oraculo(gt["flag"])], pieces=piezas)
            for conv in dfl.CONVENCIONES:
                n, r = retrasos(gt[conv], pred)
                acc[("DFL, «{}», {}".format(cond, conv))][0] += n
                acc[("DFL, «{}», {}".format(cond, conv))][1] += r
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    import lector as lc
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    for id_ in ids:
        crudo = lc.leer_crudo(id_)
        for cond in lc.VOTAN:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            pred = pipeline.run(puntuar.solo_lectura(trk), extra=[puntuar.d_oraculo(gt)])
            n, r = retrasos(gt, pred)
            acc[("SkillCorner, «{}»".format(cond))][0] += n
            acc[("SkillCorner, «{}»".format(cond))][1] += r
        print("hecho {}".format(id_), file=sys.stderr, flush=True)
    for nombre, (n, r) in acc.items():
        imprimir(nombre, n, r)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
