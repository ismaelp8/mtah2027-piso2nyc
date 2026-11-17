"""Compara la predicción en numpy (`possession/conjunto.py`) con la de torch que guardó `entrenar.py`.

    python validation/conjunto/paridad.py --etiqueta v1                      # un partido de cada dominio
    python validation/conjunto/paridad.py --etiqueta piloto1 --pesos <ruta>.npz --partidos dfl:J03WMX

Datos abiertos de otros partidos (la caché de `exportar.py`). Lo puede ejecutar cualquiera, Claude incluido, con el
entorno del equipo (solo numpy). Solo imprime agregados.

De cada partido toma el balón de su primera condición que vota y compara, frame a frame de los tramos evaluados, el
z y las probabilidades de cambio de numpy (float64, con los pesos del pliegue que no vio el partido) con los de torch
(float32). Enseña la diferencia máxima y en cuántos frames cambia el signo de z. No tienen que ser idénticos: torch
va en float32. Lo que importa para la entrega es que numpy dé lo mismo en dos máquinas, y eso lo da el código.
"""

import argparse
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
sys.path.insert(0, ROOT)
import cj_comun as cj  # noqa: E402
from possession import conjunto, tracking  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def tracking_de(dominio, partido, sufijo="0"):
    """El `Tracking` de un partido de la caché con el balón de la condición `sufijo`."""
    with np.load(cj.fichero_partido(dominio, partido)) as d:
        claves = ("bxd_", "byd_") if sufijo.startswith("d") else ("bx_", "by_")
        j = sufijo[-1]
        return tracking.Tracking(d[claves[0] + j].astype(np.float64), d[claves[1] + j].astype(np.float64),
                                 d["px"], d["py"], d["team"], tuple(float(v) for v in d["pitch"]),
                                 tuple((int(a), int(b)) for a, b in d["blocks"]), 25)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--etiqueta", required=True)
    parser.add_argument("--pesos", default=None, help="otro fichero de pesos (por defecto, el de possession/)")
    parser.add_argument("--partidos", nargs="*", default=["dfl:" + cj.DFL[0], "sc:" + str(cj.SKILLCORNER[0])])
    args = parser.parse_args()
    if args.pesos:
        conjunto.PESOS = args.pesos
    print("| partido | pliegue | frames | dif. máx. de z | signo de z distinto | dif. máx. de p | s |")
    print("|---|---|---|---|---|---|---|")
    peor = 0.0
    for nombre in args.partidos:
        dominio, partido = nombre.split(":")
        pliegue = cj.pliegue_de(dominio, partido)
        trk = tracking_de(dominio, partido)
        with np.load(cj.fichero_salida(args.etiqueta, dominio, partido)) as d:
            z_torch, p_torch = d["z_0"], d["p_0"]
        inicio = time.time()
        z, hacia_h, hacia_a = conjunto.salidas(trk, fuera=pliegue)
        p = 1.0 / (1.0 + np.exp(-np.column_stack((hacia_h, hacia_a))))
        dentro = np.zeros(len(z), dtype=bool)
        for a, b in trk.blocks:
            dentro[a:b] = True
        dif_z = float(np.max(np.abs(z - z_torch)[dentro]))
        peor = max(peor, dif_z)
        print("| {} {} | {} | {} | {:.2e} | {} | {:.2e} | {:.0f} |".format(
            dominio, partido, pliegue, int(dentro.sum()), dif_z,
            int(np.sum((np.sign(z) != np.sign(z_torch)) & dentro)), float(np.max(np.abs(p - p_torch)[dentro])),
            time.time() - inicio), flush=True)
    sys.exit(0 if peor < 1e-2 else 1)


if __name__ == "__main__":
    main()
