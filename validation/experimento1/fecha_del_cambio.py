"""Experimento 1: cuánto se movería cada cambio si se fechara al empezar el control y no en el primer toque.

Para cada cambio H↔A que se queda tras la corrección R(c), mide cuántos frames hay entre el cambio (el
frame en que el flag pasa al equipo nuevo, su primer toque) y el primer frame de control del equipo
nuevo según c dentro de su racha. Descriptivo (bitácora, sección 9). Datos abiertos de otros partidos
(Bassek et al., 2025). Solo imprime agregados.

Uso:
    python validation/experimento1/fecha_del_cambio.py
"""

import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
sys.path.insert(0, AQUI)
import correccion as cr  # noqa: E402
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
import medidas_cambios as mc  # noqa: E402
from peso_correccion import controles_parte  # noqa: E402

DEFS = ("C0-12", "dos toques", "C0-12 o dos toques")


def main():
    desfases = {d: [] for d in DEFS}
    for p in etiquetas_dfl.PARTIDOS:
        datos = dfl_lector.cargar_cache(p)
        for k in (1, 2):
            parte = datos["partes"][k]
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            lab = np.where(estado == 1, poss - 1, 2).astype(int)
            ctrl = controles_parte(parte)
            for d in DEFS:
                l2 = cr.corregir(lab, ctrl[d])
                runs = mc.rachas(l2, 1)
                for i in range(1, len(runs)):
                    a, b, v = runs[i]
                    if v == 2 or runs[i - 1][2] == 2:
                        continue
                    ini, fin = ctrl[d][v]
                    sel = (ini < b) & (fin > a)
                    if np.any(sel):
                        desfases[d].append(int(max(a, ini[sel].min()) - a))
    salida = {}
    for d, v in desfases.items():
        v = np.asarray(v)
        salida[d] = {"cambios": int(len(v)), "p50_p75_p90_frames": [float(x) for x in np.percentile(v, [50, 75, 90])],
                     "a_0_frames_pct": round(100.0 * float(np.mean(v == 0)), 1),
                     "mas_de_8_frames_pct": round(100.0 * float(np.mean(v > 8)), 1),
                     "mas_de_25_frames_pct": round(100.0 * float(np.mean(v > 25)), 1)}
    print(json.dumps(salida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
