"""B15, B16 y B17 frente a `main` en los 3 partidos abiertos de Metrica, un proveedor que no han visto. Descriptivo.

    python validation/secuencia/metrica.py [--bootstrap 1000] [--candidatos b15 b16 b17]

Datos abiertos de otros partidos (Metrica sample-data; ver `validation/metrica/lector.py`). Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados.

Es el mismo instrumento con que se midió K2 (`validation/conjunto/metrica.py` en la rama `exp/modelo-conjunto`): las
condiciones y los modos del `D` de `validation/metrica/medir.py`, `main` y los candidatos con los pesos de la entrega
(B15: los 7 de la DFL; B16: los 7 de la DFL y los 10 de SkillCorner `ENTRENAMIENTO`; B17: la media de los dos). Ninguno
ha visto estos partidos ni este proveedor. Así sus cifras se pueden poner junto a las de K2.

Dos avisos que ya estaban medidos (`validation/metrica/BITACORA.md`): las etiquetas salen de los eventos de Metrica (un
toque con impacto, no control), y el balón de Metrica va pegado al jugador en casi la mitad de los frames, así que
favorece a cualquier evidencia de proximidad. Metrica son 3 partidos: es una señal, no una prueba.
"""

import argparse
import collections
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (os.path.join(ROOT, "validation", "cambios"), os.path.join(ROOT, "validation", "metrica")):
    sys.path.insert(0, _carpeta)
import comun as cc  # noqa: E402  (validation/cambios/comun.py: pone harness/ y la raíz en el camino)
import lector as lc  # noqa: E402  (validation/metrica/lector.py)
from comun import puntuar  # noqa: E402
from possession import aprendida, pipeline  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MODOS = ("oraculo", "propio")
CANDIDATOS = {"b15": aprendida.evidence_b15, "b16": aprendida.evidence_b16, "b17": aprendida.evidence_b17}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--candidatos", nargs="+", choices=sorted(CANDIDATOS), default=sorted(CANDIDATOS))
    args = parser.parse_args()
    ids = lc.partidos()
    if not ids:
        sys.exit("No hay partidos de Metrica bajados, en {}".format(lc.carpeta()))
    versiones = [("main", None)] + [(c, {"candidates": CANDIDATOS[c]}) for c in args.candidatos]
    recuentos = collections.defaultdict(list)
    for id_ in ids:
        crudo = lc.leer(id_)
        for condicion in lc.CONDICIONES:
            trk, gt = lc.tracking_de(crudo, condicion, id_)
            trk = puntuar.solo_lectura(trk)
            for modo in MODOS:
                extra = [puntuar.d_oraculo(gt)] if modo == "oraculo" else []
                for nombre, piezas in versiones:
                    recuentos[(nombre, condicion, modo)].append(
                        puntuar.contar(gt, pipeline.run(trk, extra=extra, pieces=piezas)))
        print("# hecho {}".format(id_), file=sys.stderr, flush=True)

    print("# B15, B16 y B17 frente a `main` en Metrica ({} partidos; descriptivo)\n".format(len(ids)))
    print("Código: {} · bootstrap pareado de {} · todos con los pesos de la entrega.\n".format(
        puntuar.version_del_codigo(), args.bootstrap))
    print("| `D` | condición | ¿vota en Metrica? | versión | main | versión | diferencia [5–95 %] | gana en | posesiones: "
          "versión / main / reales |")
    print("|---|---|---|---|---|---|---|---|---|")
    for modo in MODOS:
        for condicion in lc.CONDICIONES:
            ref = recuentos[("main", condicion, modo)]
            for nombre in args.candidatos:
                cand = recuentos[(nombre, condicion, modo)]
                dif, intervalo, gana = cc.frente_a(cand, ref, args.bootstrap)
                print("| {} | {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} [{:+.3f} a {:+.3f}] | {} de {} | {} / {} / {} |".format(
                    "etiquetas" if modo == "oraculo" else "propio", condicion, "sí" if condicion in lc.VOTAN else "no",
                    nombre.upper(), cc.spell(ref), cc.spell(cand), dif, intervalo[0], intervalo[1], gana, len(ids),
                    sum(r["n_pred"] for r in cand), sum(r["n_pred"] for r in ref), sum(r["n_gt"] for r in ref)))


if __name__ == "__main__":
    main()
