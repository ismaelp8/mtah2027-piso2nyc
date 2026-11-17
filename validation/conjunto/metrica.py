"""K2 frente a `main` en los 3 partidos abiertos de Metrica, un proveedor que el modelo no ha visto. Descriptivo.

    python validation/conjunto/metrica.py [--bootstrap 1000]

Datos abiertos de otros partidos (Metrica sample-data; ver `validation/metrica/lector.py`). Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. La lectura está en docs/decisiones.md (17/11, «tres
comprobaciones más», punto 4), escrita antes de ejecutarlo.

`main` y K2 van con los pesos de la entrega (B5 y el modelo conjunto de los 17 partidos): ninguno ha visto estos
partidos ni este proveedor. Las condiciones y los modos del `D` son los de `validation/metrica/medir.py`.

Dos avisos que ya estaban medidos y que limitan lo que dice esta tabla (`validation/metrica/BITACORA.md` y el sondeo
S10 del 16/11): las etiquetas salen de los eventos de Metrica (un toque con impacto, no control), y el balón de
Metrica va pegado al jugador en casi la mitad de los frames, así que favorece a cualquier evidencia de proximidad.
"""

import argparse
import collections
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (os.path.join(AQUI, "..", "cambios"), os.path.join(AQUI, "..", "metrica")):
    sys.path.insert(0, _carpeta)
import comun as cc  # noqa: E402  (validation/cambios/comun.py: pone harness/ y la raíz en el camino)
import lector as lc  # noqa: E402  (validation/metrica/lector.py)
from comun import puntuar  # noqa: E402
from possession import aprendida, conjunto, pipeline  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MODOS = ("oraculo", "propio")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--pesos", default=None, help="otros pesos para K2 (comprobación 5: un solo proveedor)")
    args = parser.parse_args()
    if args.pesos:
        conjunto.PESOS = args.pesos
        conjunto._CACHE.clear()
    ids = lc.partidos()
    if not ids:
        sys.exit("No hay partidos de Metrica bajados, en {}".format(lc.carpeta()))
    recuentos = collections.defaultdict(list)
    for id_ in ids:
        crudo = lc.leer(id_)
        for condicion in lc.CONDICIONES:
            trk, gt = lc.tracking_de(crudo, condicion, id_)
            trk = puntuar.solo_lectura(trk)
            for modo in MODOS:
                extra = [puntuar.d_oraculo(gt)] if modo == "oraculo" else []
                for nombre, piezas in (("main", None), ("K2", {"candidates": aprendida.evidence_k2})):
                    recuentos[(nombre, condicion, modo)].append(
                        puntuar.contar(gt, pipeline.run(trk, extra=extra, pieces=piezas)))
        print("# hecho {}".format(id_), file=sys.stderr, flush=True)

    print("# K2 frente a `main` en Metrica ({} partidos; descriptivo)\n".format(len(ids)))
    print("Código: {} · bootstrap pareado de {} · los dos con los pesos de la entrega.\n".format(
        puntuar.version_del_codigo(), args.bootstrap))
    print("| `D` | condición | ¿vota en Metrica? | main | K2 | diferencia [5–95 %] | gana en | posesiones: K2 / main / "
          "reales |")
    print("|---|---|---|---|---|---|---|---|")
    for modo in MODOS:
        for condicion in lc.CONDICIONES:
            ref, cand = recuentos[("main", condicion, modo)], recuentos[("K2", condicion, modo)]
            dif, intervalo, gana = cc.frente_a(cand, ref, args.bootstrap)
            print("| {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} [{:+.3f} a {:+.3f}] | {} de {} | {} / {} / {} |".format(
                "etiquetas" if modo == "oraculo" else "propio", condicion, "sí" if condicion in lc.VOTAN else "no",
                cc.spell(ref), cc.spell(cand), dif, intervalo[0], intervalo[1], gana, len(ids),
                sum(r["n_pred"] for r in cand), sum(r["n_pred"] for r in ref), sum(r["n_gt"] for r in ref)))


if __name__ == "__main__":
    main()
