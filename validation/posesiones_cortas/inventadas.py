"""Las posesiones inventadas (fase 2): ¿tras un reinicio o antes de una parada? ¿existen con la otra convención?

    python validation/posesiones_cortas/inventadas.py

DFL (Bassek et al., 2025, CC BY 4.0), balón «como el ATD», `D` de las etiquetas. Lo puede ejecutar cualquiera,
Claude incluido. Solo agregados. **No decide nada** (BITACORA.md §9).

«Inventada» es la clase de `fase2.py`: una posesión nuestra sin pareja en la que las etiquetas dan el otro
equipo en la mayor parte de sus frames, sin ninguna posesión real de su equipo a 50 frames o menos. Se dice:
- si empieza justo tras un `D` real (tras un reinicio), si acaba justo antes de uno (antes de una parada),
  las dos cosas o ninguna;
- si con la otra convención también es inventada, o es real o desplazada (una apuesta de convención);
- cuánto vale quitar solo las que son inventadas con las dos convenciones (sus frames como en las etiquetas).
"""

import collections
import functools
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "scripts"),
                 os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import diagnostico_errores as de  # noqa: E402
import fase2  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
LADOS = ("tras un reinicio", "antes de una parada", "entre dos paradas", "en pleno juego")


def clases(gt, pred):
    """{(a, b, equipo): clase de fase2} de las posesiones nuestras sin pareja."""
    runs = pm.valid_runs(gt)
    lleno = pm.fill_abstentions(pred, runs)
    reales = pm.possession_spells(gt, runs)
    nuestras = pm.possession_spells(lleno, runs)
    _, ok = de.emparejar(reales, nuestras)
    por_equipo = {H: [r for r in reales if r[2] == H], A: [r for r in reales if r[2] == A]}
    return {n: fase2.clase_sobrante(n, gt, por_equipo) for n, k in zip(nuestras, ok) if not k}


def lado(gt, a, b):
    tras, antes = a > 0 and gt[a - 1] == D, b < len(gt) and gt[b] == D
    return LADOS[2] if tras and antes else LADOS[0] if tras else LADOS[1] if antes else LADOS[3]


def main():
    tabla = collections.Counter()
    valor = collections.defaultdict(list)
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        trk = puntuar.solo_lectura(dfl.tracking_de(cargado, dfl.VOTAN[0]))
        pred = pipeline.run(trk, extra=[puntuar.d_oraculo(gt["flag"])],
                            pieces={"candidates": functools.partial(aprendida.evidence_b5, fuera=partido)})
        por_conv = {c: clases(gt[c], pred) for c in dfl.CONVENCIONES}
        en_las_dos = [n for n, c in por_conv["control"].items() if c == "inventada"
                      and por_conv["flag"].get(n) == "inventada"]
        for conv in dfl.CONVENCIONES:
            otra = "flag" if conv == "control" else "control"
            for n, c in por_conv[conv].items():
                if c != "inventada":
                    continue
                en_otra = por_conv[otra].get(n, "encontrada (real)")
                tabla[(conv, lado(gt[conv], n[0], n[1]), en_otra)] += 1
            valor[(conv, "base")].append(puntuar.contar(gt[conv], pred))
            valor[(conv, "las dos")].append(puntuar.contar(gt[conv], fase2.con_oraculo(pred, gt[conv],
                                                                                        [(a, b) for a, b, _ in en_las_dos])))
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    print("# Las posesiones inventadas (DFL, «{}», `D` oráculo; descriptivo)\n".format(dfl.VOTAN[0]))
    otras = ("inventada", "cambio real desplazado", "trozo de una real partida", "fundida", "encontrada (real)")
    for conv in dfl.CONVENCIONES:
        otra = "flag" if conv == "control" else "control"
        print("\n### Inventadas con el {}: dónde están y qué son con el {}\n".format(conv, otra))
        print("| dónde | total | " + " | ".join(otras) + " |")
        print("|---|---|" + "---|" * len(otras))
        for l in LADOS:
            fila = [tabla[(conv, l, o)] for o in otras]
            print("| {} | {} | {} |".format(l, sum(fila), " | ".join(str(v) for v in fila)))
    print("\n### Cuánto vale quitar solo las inventadas con las dos convenciones\n")
    print("| etiquetas | ninguno | sin ellas |")
    print("|---|---|---|")
    for conv in dfl.CONVENCIONES:
        b = puntuar.spell_f1(*puntuar.juntar(valor[(conv, "base")]))
        s = puntuar.spell_f1(*puntuar.juntar(valor[(conv, "las dos")]))
        print("| {} | {:.3f} | {:.3f} ({:+.3f}) |".format(conv, b, s, s - b).replace(".", ","))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
