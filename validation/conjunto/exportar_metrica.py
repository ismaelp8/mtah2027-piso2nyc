"""Exporta los 3 partidos abiertos de Metrica a la caché del modelo conjunto, para entrenar K7.

    python validation/conjunto/exportar_metrica.py

Datos abiertos de otros partidos (sample-data de Metrica; hay que citar la fuente). Lo puede ejecutar cualquiera,
Claude incluido. Solo imprime recuentos.

Mismo formato que `exportar.py` para SkillCorner, en `conjunto_cache/metrica_<id>.npz`: `px`, `py`, `team`, `pitch`,
`blocks`, el balón de las dos condiciones de `validation/metrica/lector.py` (`bx_0`, `by_0`: «tal cual»;
`bx_1`, `by_1`: «suavizado 25») y `gt_control`, que aquí son las etiquetas sacadas de sus eventos
(`lector.etiquetar`), no las de control. No hay flag. `exportar.py` y la caché de la DFL y de SkillCorner no cambian.

**Exportar Metrica para entrenar la gasta como tercer proveedor:** un modelo entrenado con ella ya no se puede
puntuar en Metrica (docs/decisiones.md, 17/11, K7).
"""

import argparse
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import refinar  # noqa: E402  (pone en el camino harness/, cambios/ y la raíz, y carga el lector de Metrica)
import cj_comun as comun  # noqa: E402
from exportar import _mismos  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DOMINIO = "metrica"


def exportar_metrica(id_):
    lc = refinar.lector_metrica()
    crudo = lc.leer(id_)
    datos = {}
    for j, condicion in enumerate(lc.CONDICIONES):
        trk, gt = lc.tracking_de(crudo, condicion, id_)
        if j == 0:
            datos.update(px=trk.px.astype(np.float32), py=trk.py.astype(np.float32), team=np.asarray(trk.team),
                         pitch=np.asarray(trk.pitch, dtype=np.float64), blocks=np.asarray(trk.blocks, dtype=np.int64),
                         gt_control=np.asarray(gt, dtype=np.int8))
        if not (_mismos(trk.px, datos["px"]) and np.array_equal(trk.team, datos["team"])
                and np.array_equal(gt, datos["gt_control"])):
            raise AssertionError("los slots o las etiquetas no son los mismos en todas las condiciones")
        datos["bx_{}".format(j)], datos["by_{}".format(j)] = trk.bx.astype(np.float32), trk.by.astype(np.float32)
    return datos


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rehacer", action="store_true", help="vuelve a exportar lo que ya está en la caché")
    args = parser.parse_args()
    lc = refinar.lector_metrica()
    partidos = [int(p) for p in lc.partidos()]
    if not partidos:
        sys.exit("No hay partidos de Metrica bajados, en {}".format(lc.carpeta()))
    comun.carpeta().mkdir(parents=True, exist_ok=True)
    print("| dominio | partido | frames | slots | frames vivos | balón visible en los vivos (cond. 0 / 1) | s |")
    print("|---|---|---|---|---|---|---|")
    for partido in partidos:
        destino = comun.fichero_partido(DOMINIO, partido)
        if destino.is_file() and not args.rehacer:
            print("| {} | {} | ya estaba en la caché | | | | |".format(DOMINIO, partido), flush=True)
            continue
        inicio = time.time()
        datos = exportar_metrica(partido)
        np.savez(destino, **datos)
        vivo = datos["gt_control"] < 2
        visible = ["{:.1f} %".format(100.0 * float(np.mean(~np.isnan(datos["bx_{}".format(j)][vivo]))))
                   for j in (0, 1)]
        print("| {} | {} | {} | {} | {} | {} | {:.0f} |".format(
            DOMINIO, partido, len(vivo), datos["px"].shape[1], int(vivo.sum()), " / ".join(visible),
            time.time() - inicio), flush=True)


if __name__ == "__main__":
    main()
