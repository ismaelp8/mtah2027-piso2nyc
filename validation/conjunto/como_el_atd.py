"""¿Aguanta K2 los slots y el balón como los del partido? Descriptivo, en la DFL.

    python validation/conjunto/como_el_atd.py [--bootstrap 1000] [--procesos 2]

Datos abiertos de otros partidos: los 7 de la DFL (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar cualquiera,
Claude incluido. Solo imprime agregados. La lectura está en docs/decisiones.md (17/11, «tres comprobaciones más»),
escrita antes de ejecutarlo.

K2 se entrenó con slots que faltan, un slot duplicado y el balón hasta 5 frames tarde, pero esos dos rasgos medidos
del ATD no se habían puntuado. Aquí se puntúan `main` y K2 (cada partido, con el pliegue que no lo vio) con tres
degradaciones que ya existen y están calibradas con agregados del partido:

- **slots:** los de P4 (`validation/investigacion_1116/slots_dfl.degradar`): los tracklets cortados en trozos de 35,5 s
  de mediana y un slot de más en el 12,9 % de los frames;
- **balón:** el balón 4 frames tarde (`ball.advance_ball(trk, -4)`, el retraso medido el 15/11);
- **las dos juntas.**

En las dos condiciones del balón que votan, con el `D` de las etiquetas y con el propio, y con las dos convenciones.
"""

import argparse
import collections
import concurrent.futures
import functools
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (AQUI, os.path.join(AQUI, "..", "cambios"), os.path.join(AQUI, "..", "investigacion_1116")):
    sys.path.insert(0, _carpeta)
import comun as cc  # noqa: E402  (validation/cambios/comun.py: pone harness/ y la raíz en el camino)
import slots_dfl  # noqa: E402  (validation/investigacion_1116/slots_dfl.py: `degradar`)
from comun import dfl, puntuar  # noqa: E402
from possession import aprendida, ball, pipeline  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEGRADACIONES = ("sin degradar", "slots como los del partido", "balón 4 frames tarde", "las dos juntas")
RETRASO = -4  # frames: `ball.advance_ball` con un número negativo retrasa el balón
MODOS = ("oraculo", "propio")
NOMBRE_MODO = {"oraculo": "etiquetas", "propio": "propio"}
UMBRAL = 0.005


def trackings_de(base, indice):
    """{degradación: tracking} de un tracking de la DFL."""
    _, con_slots, _ = slots_dfl.degradar(base, indice)
    return {"sin degradar": base, "slots como los del partido": con_slots,
            "balón 4 frames tarde": puntuar.solo_lectura(ball.advance_ball(base, RETRASO)),
            "las dos juntas": puntuar.solo_lectura(ball.advance_ball(con_slots, RETRASO))}


def medir(partido):
    inicio = time.time()
    cargado = dfl.cargar(partido)
    gts = cargado["gt"]
    versiones = {"main": functools.partial(aprendida.evidence_b5, fuera=partido),
                 "K2": functools.partial(aprendida.evidence_k2, fuera=partido)}
    recuentos = {}
    for condicion in dfl.VOTAN:
        base = puntuar.solo_lectura(dfl.tracking_de(cargado, condicion))
        for degradacion, trk in trackings_de(base, cargado["indice"]).items():
            for modo in MODOS:
                extra = [puntuar.d_oraculo(gts["flag"])] if modo == "oraculo" else []
                for nombre, pieza in versiones.items():
                    pred = pipeline.run(trk, extra=extra, pieces={"candidates": pieza})
                    for convencion in dfl.CONVENCIONES:
                        recuentos[(nombre, degradacion, condicion, modo, convencion)] = puntuar.contar(
                            gts[convencion], pred)
    return partido, recuentos, time.time() - inicio


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--procesos", type=int, default=2)
    args = parser.parse_args()
    partidos = list(dfl.PARTIDOS)
    recuentos = {}
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for partido, valor, segundos in pool.map(medir, partidos):
            recuentos[partido] = valor
            print("# hecho {} en {:.0f} s".format(partido, segundos), file=sys.stderr, flush=True)

    def lista(nombre, degradacion, celda):
        return [recuentos[p][(nombre, degradacion) + celda] for p in partidos]

    print("# K2 y `main` con los slots y el balón como los del partido (DFL, 7 partidos; descriptivo)\n")
    print("Código: {} · bootstrap pareado de {} · cada partido, con el pliegue que no lo vio.\n".format(
        puntuar.version_del_codigo(), args.bootstrap))
    print("## K2 frente a `main`, con la misma degradación los dos\n")
    print("| degradación | `D` | condición | etiquetas | main | K2 | diferencia [5–95 %] | gana en |")
    print("|---|---|---|---|---|---|---|---|")
    aguanta = collections.OrderedDict((d, True) for d in DEGRADACIONES)
    for degradacion in DEGRADACIONES:
        for modo in MODOS:
            for condicion in dfl.VOTAN:
                for convencion in dfl.CONVENCIONES[::-1]:
                    celda = (condicion, modo, convencion)
                    ref, cand = lista("main", degradacion, celda), lista("K2", degradacion, celda)
                    dif, intervalo, gana = cc.frente_a(cand, ref, args.bootstrap)
                    aguanta[degradacion] &= dif >= (UMBRAL if convencion == "control" else 0.0)
                    print("| {} | {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} [{:+.3f} a {:+.3f}] | {} de {} |".format(
                        degradacion, NOMBRE_MODO[modo], condicion, convencion, cc.spell(ref), cc.spell(cand), dif,
                        intervalo[0], intervalo[1], gana, len(partidos)))
    print("\nLectura (docs/decisiones.md, 17/11): con cada degradación, ¿sigue K2 ganando a `main` por +{} o más con "
          "control en las cuatro celdas, sin perder con el flag?\n".format(UMBRAL))
    for degradacion, ok in aguanta.items():
        print("- {}: **{}**".format(degradacion, "sí" if ok else "no"))

    print("\n## Lo que cuesta cada degradación a cada versión (frente a sí misma sin degradar)\n")
    print("| versión | degradación | " + " | ".join(
        "{}, {}, `D` {}".format(v, c, NOMBRE_MODO[m]) for m in MODOS for c in dfl.VOTAN
        for v in dfl.CONVENCIONES[::-1]) + " |")
    print("|---|---|" + "---|" * 8)
    for nombre in ("main", "K2"):
        for degradacion in DEGRADACIONES[1:]:
            celdas = []
            for modo in MODOS:
                for condicion in dfl.VOTAN:
                    for convencion in dfl.CONVENCIONES[::-1]:
                        celda = (condicion, modo, convencion)
                        celdas.append("{:+.3f}".format(cc.spell(lista(nombre, degradacion, celda))
                                                       - cc.spell(lista(nombre, "sin degradar", celda))))
            print("| {} | {} | {} |".format(nombre, degradacion, " | ".join(celdas)))


if __name__ == "__main__":
    main()
