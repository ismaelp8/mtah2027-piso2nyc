"""¿Cuánto cambia la salida del pipeline al poner K2 en lugar de B5? Descriptivo, en los datos abiertos.

    python validation/conjunto/cuanto_cambia.py

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, mitad de entrenamiento, MIT). Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. No lee el examen de SkillCorner.

Sirve para escribir, antes de generar la entrega de prueba, qué cambios caben esperar frente a la entrega vigente
(punto 4 de la regla del 17/11): `validation/partido/comparar_entregas.py` da en el partido estos mismos recuentos.

Ejecuta el pipeline entero **con el `D` propio** (sin las capas del partido, que aquí no existen) dos veces por
partido y condición: con las piezas de la entrega (`main`) y con `aprendida.evidence_k2` en lugar de B5, cada una con
el pliegue que no vio el partido. Cuenta, sobre los frames evaluados: cuántos cambian de etiqueta y de qué a qué, las
posesiones y las paradas de cada salida, y las posesiones de menos de 12 y de 25 frames (las cotas de las rachas
cortas que imprime `possession.pipeline`).
"""

import functools
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (AQUI, os.path.join(AQUI, "..", "harness"), os.path.join(AQUI, "..", "apuesta_b"),
                 os.path.join(AQUI, "..", "skillcorner"), ROOT):
    sys.path.insert(0, _carpeta)
import cj_comun as cj  # noqa: E402
import d_propio  # noqa: E402
import dfl  # noqa: E402
import lector  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline, tracking  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

H, A, D = tracking.H, tracking.A, tracking.D
CLASES = ("de un equipo al otro", "de un equipo a D", "de D a un equipo")


def rachas(codes, blocks, valores):
    """Cuántas rachas de las etiquetas `valores` hay dentro de los tramos evaluados."""
    total = 0
    for a, b in blocks:
        w = codes[a:b]
        inicio = np.flatnonzero(np.concatenate(([True], w[1:] != w[:-1])))
        total += int(np.isin(w[inicio], valores).sum())
    return total


def cortas(codes, blocks, limite):
    """Cuántas posesiones (rachas de `H` o de `A`) duran menos de `limite` frames dentro de los tramos evaluados."""
    total = 0
    for a, b in blocks:
        w = codes[a:b]
        inicio = np.flatnonzero(np.concatenate(([True], w[1:] != w[:-1])))
        largo = np.diff(np.concatenate((inicio, [len(w)])))
        total += int(np.sum(np.isin(w[inicio], (H, A)) & (largo < limite)))
    return total


def comparar(antes, despues, blocks):
    """Recuentos de dos salidas sobre los frames evaluados."""
    dentro = np.zeros(len(antes), dtype=bool)
    for a, b in blocks:
        dentro[a:b] = True
    x, y = antes[dentro], despues[dentro]
    equipo_x, equipo_y = x != D, y != D
    return np.array([
        len(x),
        int(np.sum(equipo_x & equipo_y & (x != y))),
        int(np.sum(equipo_x & ~equipo_y)),
        int(np.sum(~equipo_x & equipo_y)),
        rachas(antes, blocks, (H, A)), rachas(despues, blocks, (H, A)),
        rachas(antes, blocks, (D,)), rachas(despues, blocks, (D,)),
        int(np.sum(x == D)), int(np.sum(y == D)),
        cortas(antes, blocks, 12), cortas(despues, blocks, 12), cortas(antes, blocks, 25), cortas(despues, blocks, 25),
    ], dtype=np.int64)


def de_un_tracking(trk, pliegue_b5, pliegue_k2):
    trk = puntuar.solo_lectura(trk)
    b5 = functools.partial(aprendida.evidence_b5, fuera=pliegue_b5) if pliegue_b5 else aprendida.evidence_b5
    main = pipeline.run(trk, pieces={"candidates": b5})
    k2 = pipeline.run(trk, pieces={"candidates": functools.partial(aprendida.evidence_k2, fuera=pliegue_k2)})
    return comparar(main, k2, trk.blocks)


def main():
    inicio = time.time()
    filas = {}
    for partido in cj.DFL:
        cargado = dfl.cargar(partido)
        for condicion in dfl.VOTAN:
            for nombre, hacer in (("balón tapado en los D", dfl.tracking_de), ("balón a la vista en los D",
                                                                               d_propio.con_balon_en_d)):
                clave = ("DFL", condicion, nombre)
                filas[clave] = filas.get(clave, 0) + de_un_tracking(hacer(cargado, condicion), partido, partido)
        print("# hecho {} ({:.0f} s)".format(partido, time.time() - inicio), file=sys.stderr, flush=True)
    lector.exigir_solo_entrenamiento(cj.SKILLCORNER)
    for id_ in cj.SKILLCORNER:
        crudo = lector.leer_crudo(id_)
        for condicion in lector.VOTAN:
            trk, _ = lector.tracking_de(crudo, condicion, id_)
            clave = ("SkillCorner", condicion, "")
            filas[clave] = filas.get(clave, 0) + de_un_tracking(trk, None, cj.pliegue_de("sc", id_))
        print("# hecho {} ({:.0f} s)".format(id_, time.time() - inicio), file=sys.stderr, flush=True)

    print("# Cuánto cambia la salida con K2 en lugar de B5 (descriptivo, `D` propio, sin las capas del partido)\n")
    print("Código: {} · {} partidos de la DFL y {} de SkillCorner, cada uno con el pliegue que no lo vio.\n".format(
        puntuar.version_del_codigo(), len(cj.DFL), len(cj.SKILLCORNER)))
    print("| datos | condición | balón en los D | frames evaluados que cambian | {} | posesiones: main → K2 | paradas: "
          "main → K2 | frames D: main → K2 | posesiones de menos de 12 frames: main → K2 | de menos de 25: main → K2 |"
          .format(" | ".join(CLASES)))
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for (datos, condicion, balon), r in filas.items():
        n = float(r[0])
        print("| {} | {} | {} | {:.1f} % | {:.1f} % | {:.2f} % | {:.2f} % | {} → {} ({:+.1f} %) | {} → {} ({:+.1f} %) | "
              "{:.1f} % → {:.1f} % | {} → {} | {} → {} |".format(
                  datos, condicion, balon or "–", 100.0 * (r[1] + r[2] + r[3]) / n, 100.0 * r[1] / n, 100.0 * r[2] / n,
                  100.0 * r[3] / n, r[4], r[5], 100.0 * (r[5] - r[4]) / r[4], r[6], r[7], 100.0 * (r[7] - r[6]) / r[6],
                  100.0 * r[8] / n, 100.0 * r[9] / n, r[10], r[11], r[12], r[13]))


if __name__ == "__main__":
    main()
