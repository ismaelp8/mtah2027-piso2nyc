"""Rasgos de B14/B15 (possession/trayectorias2.py) en la mitad de entrenamiento de SkillCorner, para B16.

    python validation/trayectorias/exportar_sc.py

Datos abiertos de otros partidos (SkillCorner, A-League 2024/25, licencia MIT). Solo `lector.ENTRENAMIENTO`: la
mitad de examen no se toca. Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

B16 es B15 entrenada también con estos 10 partidos. Sus etiquetas son las de SkillCorner (`possession.group`, que exige
control), en todos los frames vivos. Se guardan empaquetadas como las de la DFL (`paquetes.py`): los presentes de cada
frame al principio y en float16, en las dos condiciones que votan en SkillCorner.
"""

import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, AQUI, os.path.join(ROOT, "validation", "skillcorner")):
    sys.path.insert(0, _carpeta)
import lector as lc  # noqa: E402
import paquetes  # noqa: E402
from possession import ball, trayectorias2  # noqa: E402
from possession.tracking import A, H  # noqa: E402


def nombre(id_, condicion, parte, clave):
    return paquetes.carpeta() / "sc_{}_{}_{}_{}.npy".format(id_, lc.VOTAN.index(condicion), parte, clave)


def main():
    lc.exigir_solo_entrenamiento(lc.ENTRENAMIENTO)
    paquetes.carpeta().mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    maximo = 0
    for id_ in lc.ENTRENAMIENTO:
        crudo = lc.leer_crudo(id_)
        for condicion in lc.VOTAN:
            trk, gt = lc.tracking_de(crudo, condicion, id_)
            trk = ball.clean(trk)
            for k, (a, b) in enumerate(trk.blocks):
                r, hay_h, hay_a = trayectorias2.rasgos_tramo(trk, a, b)
                c = {"H_propios": r[H][0], "H_rivales": r[H][1], "H_balon": r[H][2],
                     "A_propios": r[A][0], "A_rivales": r[A][1], "A_balon": r[A][2], "hay_h": hay_h, "hay_a": hay_a,
                     "y": (gt[a:b] == H).astype(np.int8), "m": np.isin(gt[a:b], (H, A))}
                s = int(max(hay_h.sum(axis=1).max(), hay_a.sum(axis=1).max()))
                maximo = max(maximo, s)
                paquetes.empaquetar(c, s)
                for clave in paquetes.CLAVES:
                    np.save(nombre(id_, condicion, k, clave), c[clave])
            print("{} · {}: {} partes, {} slots, hasta {} presentes por equipo, {} frames vivos · {:.0f} s".format(
                id_, condicion, len(trk.blocks), len(trk.team), s, int(np.isin(gt, (H, A)).sum()),
                time.time() - inicio), flush=True)
    print("máximo de presentes por equipo en SkillCorner: {}".format(maximo))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
