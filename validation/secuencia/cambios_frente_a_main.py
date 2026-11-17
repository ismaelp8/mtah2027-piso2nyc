"""Cuánto cambia B12 (o B11) la salida frente a `main`, en datos abiertos: la base de los criterios de daño.

    python validation/secuencia/cambios_frente_a_main.py b12

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner `lector.ENTRENAMIENTO`, MIT). Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. Descriptivo: no decide nada. Sirve para razonar la banda de
los criterios de daño de una entrega de prueba frente a la vigente, que se escriben antes de generarla.

Con el `D` propio (como en el partido) y las dos condiciones que votan de cada fuente, frente a `main` (B5,
`dead_state` y `decode_cortas_a_d`):
- el % de frames evaluados con otra etiqueta y el % que entra o sale de `D`;
- las posesiones y las paradas de cada uno, y su cociente;
- las posesiones de menos de 12 y de 25 frames por cada 90 minutos de tramo evaluado (`pipeline.short_runs`).
"""

import argparse
import collections
import os
import sys

import numpy as np

import comun

sys.path.insert(0, os.path.join(comun.ROOT, "validation", "skillcorner"))
import dfl  # noqa: E402
import lector as lc  # noqa: E402
from possession import aprendida, pipeline, tracking  # noqa: E402

FUNCIONES = {"b11": aprendida.evidence_b11, "b12": aprendida.evidence_b12}


def comparar(acum, trk, candidato, fuera):
    # En la DFL, los dos con el pliegue que no vio el partido (como el harness); en SkillCorner, el de los 7.
    base = pipeline.run(trk, pieces={"candidates": lambda t: aprendida.evidence_b5(t, fuera=fuera)})
    nuevo = pipeline.run(trk, pieces={"candidates": lambda t: candidato(t, fuera=fuera)})
    for a, b in trk.blocks:
        v0, v1 = base[a:b], nuevo[a:b]
        acum["frames"] += b - a
        acum["distintos"] += int(np.sum(v0 != v1))
        acum["d_distinto"] += int(np.sum((v0 == tracking.D) != (v1 == tracking.D)))
        acum["d_main"] += int(np.sum(v0 == tracking.D))
        acum["d_cand"] += int(np.sum(v1 == tracking.D))
        for nombre, v in (("main", v0), ("cand", v1)):
            inicios = np.flatnonzero(np.concatenate(([True], v[1:] != v[:-1])))
            tipos = v[inicios]
            acum["posesiones_" + nombre] += int(np.sum(tipos != tracking.D))
            acum["paradas_" + nombre] += int(np.sum(tipos == tracking.D))
            cortas = pipeline.short_runs(v)
            acum["cortas12_" + nombre] += cortas[("posesiones", 12)]
            acum["cortas25_" + nombre] += cortas[("posesiones", 25)]


def informe(fuente, cond, acum):
    por90 = 90 * 60 * 25 / acum["frames"]
    print("| {} | {} | {:.2f} % | {:.2f} % | {:.1f} % → {:.1f} % | {} → {} ({:+.1f} %) | {} → {} | {:.1f} → {:.1f} | {:.1f} → {:.1f} |".format(
        fuente, cond, 100.0 * acum["distintos"] / acum["frames"], 100.0 * acum["d_distinto"] / acum["frames"],
        100.0 * acum["d_main"] / acum["frames"], 100.0 * acum["d_cand"] / acum["frames"],
        acum["posesiones_main"], acum["posesiones_cand"],
        100.0 * (acum["posesiones_cand"] / acum["posesiones_main"] - 1), acum["paradas_main"], acum["paradas_cand"],
        acum["cortas12_main"] * por90, acum["cortas12_cand"] * por90,
        acum["cortas25_main"] * por90, acum["cortas25_cand"] * por90).replace(".", ","))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("modelo", choices=sorted(FUNCIONES))
    args = parser.parse_args()
    candidato = FUNCIONES[args.modelo]
    print("{} frente a main, con el `D` propio (descriptivo). DFL: cada partido con el pliegue que no lo vio. "
          "SkillCorner: `lector.ENTRENAMIENTO`, con el modelo de los 7.\n".format(args.modelo.upper()))
    print("| fuente | condición | frames con otra etiqueta | frames que entran o salen de `D` | `D` | posesiones | "
          "paradas | posesiones de < 12 frames por 90 min | de < 25 frames por 90 min |")
    print("|---|---|---|---|---|---|---|---|---|")
    for cond in dfl.VOTAN:
        acum = collections.Counter()
        for partido in dfl.PARTIDOS:
            comparar(acum, dfl.tracking_de(dfl.cargar(partido), cond), candidato, partido)
        informe("DFL", cond, acum)
    lc.exigir_solo_entrenamiento(lc.ENTRENAMIENTO)
    for cond in lc.VOTAN:
        acum = collections.Counter()
        for id_ in lc.ENTRENAMIENTO:
            trk, _ = lc.tracking_de(lc.leer_crudo(id_), cond, id_)
            comparar(acum, trk, candidato, None)
        informe("SkillCorner", cond, acum)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
