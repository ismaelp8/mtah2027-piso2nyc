"""Referencia de `validation/partido/slots_duplicados.py` en los datos abiertos: los mismos porcentajes.

    python validation/investigacion_1116/slots_abiertos.py

Datos abiertos de otros partidos: los 7 de la DFL (Bassek et al., 2025, CC BY 4.0; sus jugadores no se degradan, así
que no tienen duplicados) y los 10 de `lector.ENTRENAMIENTO` de SkillCorner (licencia MIT), con todos los jugadores y
solo con los detectados. Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. Descriptivo: dice
cuántas parejas a 0,3, 0,5 y 1 m son jugadores de verdad juntos, para leer la salida del partido (BITACORA.md, P2).
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                os.path.join(ROOT, "validation", "partido"), ROOT):
    sys.path.insert(0, carpeta)
import dfl  # noqa: E402
import lector as lc  # noqa: E402
import slots_duplicados as sd  # noqa: E402  (validation/partido/slots_duplicados.py: medir y resumen son puras)


def sumar(total, cuentas):
    for k, v in cuentas.items():
        total[k] = total.get(k, 0) + v
    return total


def main():
    grupos = {"DFL, 7 partidos": {}, "SkillCorner, todos los jugadores": {},
              "SkillCorner, solo los jugadores detectados": {}}
    for partido in dfl.PARTIDOS:
        sumar(grupos["DFL, 7 partidos"], sd.medir(dfl.tracking_de(dfl.cargar(partido), "como el ATD")))
        print("DFL {}".format(partido), file=sys.stderr, flush=True)
    ids = list(lc.ENTRENAMIENTO)
    lc.exigir_solo_entrenamiento(ids)
    for id_ in ids:
        crudo = lc.leer_crudo(id_)
        sumar(grupos["SkillCorner, todos los jugadores"], sd.medir(lc.tracking_de(crudo, "detectado", id_)[0]))
        sumar(grupos["SkillCorner, solo los jugadores detectados"],
              sd.medir(lc.tracking_de(crudo, "solo jugadores detectados", id_)[0]))
        print("SkillCorner {}".format(id_), file=sys.stderr, flush=True)
    claves = list(sd.resumen(grupos["DFL, 7 partidos"]).keys())
    print("Los porcentajes de validation/partido/slots_duplicados.py en los datos abiertos (frames de los tramos).\n")
    print("| medida | " + " | ".join(grupos) + " |")
    print("|---|" + "---|" * len(grupos))
    resumenes = {g: sd.resumen(c) for g, c in grupos.items()}
    for clave in claves:
        print("| {} | {} |".format(clave, " | ".join(str(resumenes[g][clave]) for g in grupos)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    np.seterr(all="ignore")
    main()
