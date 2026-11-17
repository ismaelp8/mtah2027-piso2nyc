"""Las entradas y las salidas del modelo conjunto en los 17 partidos abiertos: la referencia para el partido.

    python validation/conjunto/referencia.py

Datos abiertos de otros partidos (la caché de `exportar.py`). Lo puede ejecutar cualquiera, Claude incluido, con el
entorno del equipo. Solo imprime agregados. No lee el examen de SkillCorner.

Calcula `agregados.agregados` en 48 vistas, cada partido con el pliegue que no lo vio, y guarda el mínimo y el máximo
de cada agregado en `referencia_abiertos.json`. Las vistas: los 17 partidos con sus dos condiciones del balón que
votan (34) y, en los 7 de la DFL, las mismas dos con el balón a la vista en los `D` (14), porque en el ATD el balón se
ve en la mayoría de los frames de las paradas.
`validation/partido/conjunto_en_el_partido.py` compara con ese rango lo que sale en el ATD del partido.
"""

import json
import os
import subprocess
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import agregados as ag  # noqa: E402
import cj_comun as cj  # noqa: E402
import paridad  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SALIDA = os.path.join(AQUI, "referencia_abiertos.json")


def commit():
    try:
        return subprocess.run(["git", "-C", AQUI, "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE,
                              universal_newlines=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "sin git"


def main():
    vistas = {}
    inicio = time.time()
    for dominio, partidos in (("dfl", cj.DFL), ("sc", cj.SKILLCORNER)):
        for partido in partidos:
            # En la DFL, también el balón a la vista en los `D` (d0, d1): en el ATD se ve en las paradas (enmienda
            # del 17/11 al criterio C2, antes de ejecutar nada sobre el partido).
            for j in (("0", "1", "d0", "d1") if dominio == "dfl" else ("0", "1")):
                trk = paridad.tracking_de(dominio, partido, j)
                vistas["{}:{}:{}".format(dominio, partido, j)] = ag.agregados(trk, fuera=cj.pliegue_de(dominio, partido))
            print("# hecho {} {} ({:.0f} s)".format(dominio, partido, time.time() - inicio), file=sys.stderr, flush=True)
    nombres = list(next(iter(vistas.values())))
    rango = {n: [float(np.nanmin([v[n] for v in vistas.values()])), float(np.nanmax([v[n] for v in vistas.values()]))]
             for n in nombres}
    por_dominio = {d: {n: [float(np.nanmin([v[n] for k, v in vistas.items() if k.startswith(d)])),
                           float(np.nanmax([v[n] for k, v in vistas.items() if k.startswith(d)]))] for n in nombres}
                   for d in ("dfl", "sc")}
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"commit": commit(), "vistas": len(vistas), "rango": rango, "por_dominio": por_dominio}, f,
                  ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print("# Referencia del modelo conjunto en los datos abiertos ({} vistas)\n".format(len(vistas)))
    print("| agregado | DFL: mínimo–máximo | SkillCorner: mínimo–máximo |")
    print("|---|---|---|")
    for n in nombres:
        print("| {} | {:.3f} – {:.3f} | {:.3f} – {:.3f} |".format(n, *por_dominio["dfl"][n], *por_dominio["sc"][n]))
    print("\nEscrito {}.".format(os.path.basename(SALIDA)))


if __name__ == "__main__":
    main()
