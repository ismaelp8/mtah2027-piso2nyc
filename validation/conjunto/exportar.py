"""Exporta los partidos abiertos como arrays crudos por jugador, para entrenar el modelo conjunto.

    python validation/conjunto/exportar.py            # los 7 de la DFL y los 10 de entrenamiento de SkillCorner
    python validation/conjunto/exportar.py --solo dfl

Datos abiertos de otros partidos (DFL: Bassek et al., 2025, CC BY 4.0; SkillCorner: A-League 2024/25, MIT). Lo puede
ejecutar cualquiera, Claude incluido. Solo imprime recuentos. **No lee `lector.EXAMEN`:** la lista de partidos de
SkillCorner pasa por `lector.exigir_solo_entrenamiento`.

De cada partido guarda, fuera del repo (`comun.fichero_partido`), lo que ve el pipeline en el harness:

- `px`, `py`: los slots del `Tracking` (los mismos en todas las condiciones), en metros, con NaN donde faltan;
- `team`, `pitch`, `blocks`;
- `bx_j`, `by_j`: el balón de la condición que vota j (`comun.CONDICIONES_*`);
- solo en la DFL, `bxd_j`, `byd_j`: el mismo balón con el limpio (congelado) a la vista en los `D` y sus bordes
  (`validation/apuesta_b/d_propio.con_balon_en_d`);
- `gt_control` y, en la DFL, `gt_flag`: las etiquetas alineadas con el tracking. En SkillCorner, `gt_control` son
  sus propias etiquetas (`lector.etiquetas`).
"""

import argparse
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (AQUI, os.path.join(AQUI, "..", "harness"), os.path.join(AQUI, "..", "apuesta_b"),
                 os.path.join(AQUI, "..", "skillcorner"), ROOT):
    sys.path.insert(0, _carpeta)
import cj_comun as comun  # noqa: E402
import d_propio  # noqa: E402
import dfl  # noqa: E402
import lector  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

assert comun.DFL == tuple(dfl.PARTIDOS) and comun.CONDICIONES_DFL == tuple(dfl.VOTAN)
assert comun.SKILLCORNER == tuple(lector.ENTRENAMIENTO) and comun.CONDICIONES_SC == tuple(lector.VOTAN)


def _mismos(a, b):
    return a.shape == b.shape and bool(np.all((a == b) | (np.isnan(a) & np.isnan(b))))


def exportar_dfl(partido):
    cargado = dfl.cargar(partido)
    datos = {"gt_control": cargado["gt"]["control"], "gt_flag": cargado["gt"]["flag"]}
    for j, condicion in enumerate(comun.CONDICIONES_DFL):
        trk = dfl.tracking_de(cargado, condicion)
        a_la_vista = d_propio.con_balon_en_d(cargado, condicion)
        if j == 0:
            datos.update(px=trk.px.astype(np.float32), py=trk.py.astype(np.float32), team=np.asarray(trk.team),
                         pitch=np.asarray(trk.pitch, dtype=np.float64), blocks=np.asarray(trk.blocks, dtype=np.int64))
        if not (_mismos(trk.px, datos["px"]) and _mismos(a_la_vista.px, datos["px"])
                and np.array_equal(trk.team, datos["team"]) and np.array_equal(a_la_vista.team, datos["team"])):
            raise AssertionError("los slots no son los mismos en todas las condiciones")
        datos["bx_{}".format(j)], datos["by_{}".format(j)] = trk.bx.astype(np.float32), trk.by.astype(np.float32)
        datos["bxd_{}".format(j)] = a_la_vista.bx.astype(np.float32)
        datos["byd_{}".format(j)] = a_la_vista.by.astype(np.float32)
    return datos


def exportar_skillcorner(id_):
    lector.exigir_solo_entrenamiento([id_])
    crudo = lector.leer_crudo(id_)
    datos = {}
    for j, condicion in enumerate(comun.CONDICIONES_SC):
        trk, gt = lector.tracking_de(crudo, condicion, id_)
        if j == 0:
            datos.update(px=trk.px.astype(np.float32), py=trk.py.astype(np.float32), team=np.asarray(trk.team),
                         pitch=np.asarray(trk.pitch, dtype=np.float64), blocks=np.asarray(trk.blocks, dtype=np.int64),
                         gt_control=gt)
        if not (_mismos(trk.px, datos["px"]) and np.array_equal(trk.team, datos["team"])
                and np.array_equal(gt, datos["gt_control"])):
            raise AssertionError("los slots o las etiquetas no son los mismos en todas las condiciones")
        datos["bx_{}".format(j)], datos["by_{}".format(j)] = trk.bx.astype(np.float32), trk.by.astype(np.float32)
    return datos


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solo", choices=("dfl", "sc"), default=None)
    parser.add_argument("--rehacer", action="store_true", help="vuelve a exportar lo que ya está en la caché")
    args = parser.parse_args()
    trabajos = []
    if args.solo in (None, "dfl"):
        trabajos += [("dfl", p, exportar_dfl) for p in comun.DFL]
    if args.solo in (None, "sc"):
        trabajos += [("sc", p, exportar_skillcorner) for p in comun.SKILLCORNER]
    comun.carpeta().mkdir(parents=True, exist_ok=True)
    print("| dominio | partido | frames | slots | frames vivos | balón visible en los vivos (cond. 0 / 1) | s |")
    print("|---|---|---|---|---|---|---|")
    for dominio, partido, funcion in trabajos:
        destino = comun.fichero_partido(dominio, partido)
        if destino.is_file() and not args.rehacer:
            print("| {} | {} | ya estaba en la caché | | | | |".format(dominio, partido), flush=True)
            continue
        inicio = time.time()
        datos = funcion(partido)
        np.savez(destino, **datos)
        vivo = datos["gt_control"] < 2
        visible = ["{:.1f} %".format(100.0 * float(np.mean(~np.isnan(datos["bx_{}".format(j)][vivo]))))
                   for j in (0, 1)]
        print("| {} | {} | {} | {} | {} | {} | {:.0f} |".format(
            dominio, partido, len(vivo), datos["px"].shape[1], int(vivo.sum()), " / ".join(visible),
            time.time() - inicio), flush=True)


if __name__ == "__main__":
    main()
