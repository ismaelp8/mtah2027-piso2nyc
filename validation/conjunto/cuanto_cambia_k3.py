"""¿Cuánto cambia la salida del pipeline al poner K3 (la mezcla de K2 y B5) en lugar de B5? Descriptivo.

    python validation/conjunto/cuanto_cambia_k3.py [--procesos 4]

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, mitad de entrenamiento, MIT). Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. No lee el examen de SkillCorner.

Es `cuanto_cambia.py` (el de K2) con K3: sirve para escribir, antes de generar la entrega de prueba de K3, qué cambios
caben esperar frente a la entrega vigente. Ejecuta el pipeline entero **con el `D` propio** (sin las capas del
partido, que aquí no existen) con las piezas de la entrega (`main`), con K2 y con K3, cada una con el pliegue que no
vio el partido, y cuenta lo mismo que `validation/partido/comparar_entregas.py` da en el partido: de `main` a K3 y,
para situarlo, de `main` a K2 y de K2 a K3. La α de K2 es la de `refinar.py`: en la DFL, la del pliegue; en
SkillCorner, la de todos.
"""

import argparse
import concurrent.futures
import functools
import hashlib
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import cuanto_cambia as base  # noqa: E402  (pone en el camino harness/, apuesta_b/, skillcorner/ y la raíz)
import cj_comun as cj  # noqa: E402
import d_propio  # noqa: E402
import dfl  # noqa: E402
import lector  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, conjunto, pipeline  # noqa: E402
from possession import refinamientos as rf  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PARES = (("main", "K3"), ("main", "K2"), ("K2", "K3"))


def _equipo(trk, pliegue_k2, alfa_k2, pliegue_b5, peso_k2):
    """La evidencia de equipo con `peso_k2` de K2 y el resto de B5: 1 es K2 y `rf.PESO_K2`, K3."""
    s = rf.mezclar(alfa_k2 * conjunto.salidas(trk, pliegue_k2)[0], rf.logit_b5(trk, pliegue_b5), peso_k2)
    return rf.puntuar(s, trk)


def de_un_tracking(trk, pliegue_b5, pliegue_k2, alfa_k2):
    trk = puntuar.solo_lectura(trk)
    b5 = functools.partial(aprendida.evidence_b5, fuera=pliegue_b5) if pliegue_b5 else aprendida.evidence_b5
    salidas = {"main": pipeline.run(trk, pieces={"candidates": b5})}
    for nombre, peso in (("K2", 1.0), ("K3", rf.PESO_K2)):
        salidas[nombre] = pipeline.run(trk, pieces={"candidates": functools.partial(
            _equipo, pliegue_k2=pliegue_k2, alfa_k2=alfa_k2, pliegue_b5=pliegue_b5, peso_k2=peso)})
    return {par: base.comparar(salidas[par[0]], salidas[par[1]], trk.blocks) for par in PARES}


def de_la_dfl(partido):
    cargado = dfl.cargar(partido)
    alfa = conjunto.pesos(partido)["alfa"]
    filas = {}
    for condicion in dfl.VOTAN:
        for nombre, hacer in (("balón tapado en los D", dfl.tracking_de),
                              ("balón a la vista en los D", d_propio.con_balon_en_d)):
            filas[("DFL", condicion, nombre)] = de_un_tracking(hacer(cargado, condicion), partido, partido, alfa)
    return filas


def de_skillcorner(id_):
    lector.exigir_solo_entrenamiento([id_])
    crudo = lector.leer_crudo(id_)
    alfa = conjunto.pesos(None)["alfa"]
    filas = {}
    for condicion in lector.VOTAN:
        trk, _ = lector.tracking_de(crudo, condicion, id_)
        filas[("SkillCorner", condicion, "")] = de_un_tracking(trk, None, cj.pliegue_de("sc", id_), alfa)
    return filas


def _trabajo(trabajo):
    dominio, partido = trabajo
    return (de_la_dfl if dominio == "dfl" else de_skillcorner)(partido)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--procesos", type=int, default=2)
    args = parser.parse_args()
    inicio = time.time()
    trabajos = [("dfl", p) for p in cj.DFL] + [("sc", p) for p in cj.SKILLCORNER]
    total = {}
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for trabajo, filas in zip(trabajos, pool.map(_trabajo, trabajos)):
            for clave, pares in filas.items():
                for par, recuento in pares.items():
                    total[(par, clave)] = total.get((par, clave), 0) + recuento
            print("# hecho {} ({:.0f} s)".format(trabajo[1], time.time() - inicio), file=sys.stderr, flush=True)

    print("# Cuánto cambia la salida con K3 (descriptivo, `D` propio, sin las capas del partido)\n")
    with open(os.path.abspath(__file__), "rb") as f:
        huella = hashlib.sha256(f.read()).hexdigest()[:16]
    print("Código: {} · este script: sha256 {}… · {} partidos de la DFL y {} de SkillCorner, cada uno con el pliegue que "
          "no lo vio.".format(puntuar.version_del_codigo(), huella, len(cj.DFL), len(cj.SKILLCORNER)))
    for antes, despues in PARES:
        print("\n## De {} a {}\n".format(antes, despues))
        print("| datos | condición | balón en los D | frames evaluados que cambian | {0} | posesiones: {1} → {2} | "
              "paradas: {1} → {2} | frames D: {1} → {2} | posesiones de menos de 12 frames: {1} → {2} | de menos de "
              "25: {1} → {2} |".format(" | ".join(base.CLASES), antes, despues))
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for (par, (datos, condicion, balon)), r in total.items():
            if par != (antes, despues):
                continue
            n = float(r[0])
            print("| {} | {} | {} | {:.1f} % | {:.1f} % | {:.2f} % | {:.2f} % | {} → {} ({:+.1f} %) | {} → {} "
                  "({:+.1f} %) | {:.1f} % → {:.1f} % | {} → {} | {} → {} |".format(
                      datos, condicion, balon or "–", 100.0 * (r[1] + r[2] + r[3]) / n, 100.0 * r[1] / n,
                      100.0 * r[2] / n, 100.0 * r[3] / n, r[4], r[5], 100.0 * (r[5] - r[4]) / r[4], r[6], r[7],
                      100.0 * (r[7] - r[6]) / r[6], 100.0 * r[8] / n, 100.0 * r[9] / n, r[10], r[11], r[12], r[13]))


if __name__ == "__main__":
    main()
