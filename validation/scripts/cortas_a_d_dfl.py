"""«Cortas a `D`» (idea 1.3) en la DFL: reproduce las ocho celdas de S9 con el `D` propio y los dos modos del
balón en los `D`.

    python validation/scripts/cortas_a_d_dfl.py --versiones validation/harness/versiones/cortas_a_d_2026-11-16.json

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar cualquiera, Claude
incluido. Solo imprime agregados.

**Siempre con el `D` propio, y por eso no hay opción de oráculo.** Con el `D` oráculo, `puntuar.d_oraculo`
prohíbe `D` en los frames donde las etiquetas tienen juego; `pipeline.combine` cruza los `allowed` con un AND,
así que la puerta `allowed[start:stop, D].all()` de `cortas_a_d` solo dejaría pasar las candidatas que ya son
`D` de verdad. La regla saldría correcta por construcción y el número vendría del oráculo, no de la señal.
`docs/PLAN_ENTREGA.md` §4 ya pone esa fila en «todavía no».

Por qué hace falta este script y no basta con `validation/harness/puntuar.py --d propio`: ese mide solo el
modo «tapado», y las condiciones 1 y 3 del límite de daño piden también «a la vista», que vive en
`validation/apuesta_b/d_propio.py`. Y `validation/investigacion_1116/paquete_control.py` no sirve para esto,
porque mide su propia copia de la lógica en vez de `temporal.decode_cortas_a_d`.

Las cifras que tiene que reproducir (S9, `validation/investigacion_1116/BITACORA.md`) y el umbral están en
`docs/decisiones.md` (16/11, «la idea 1.3 se desaparca»).
"""

import argparse
import collections
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "apuesta_b"),
                ROOT, os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, carpeta)
import d_propio  # noqa: E402
import dfl  # noqa: E402
import puntuar  # noqa: E402

VERSIONES = os.path.join(ROOT, "validation", "harness", "versiones", "cortas_a_d_2026-11-16.json")
MODOS = collections.OrderedDict([("a la vista", d_propio.con_balon_en_d), ("tapado", dfl.tracking_de)])
UMBRAL_CONTROL = 0.005  # condición 1 del límite de daño
GANA_DE = 6  # de 7 partidos, en cada celda del control
PERDIDA_MAXIMA_FLAG = 0.005  # condición 3


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--versiones", default=VERSIONES, help="fichero de versiones del harness")
    parser.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), choices=list(dfl.PARTIDOS))
    args = parser.parse_args()

    versiones, contenido, huella = puntuar.leer_versiones(args.versiones)
    nombres = [n for n in contenido if versiones[n]["tipo"] != "control"]
    base_nombre = puntuar.version_de_main(collections.OrderedDict((n, versiones[n]) for n in nombres))
    if base_nombre is None:
        print("el fichero de versiones no trae la versión de `main` (una sin `params` ni `piezas`)")
        return 1
    variantes = [n for n in nombres if n != base_nombre]
    if not variantes:
        print("el fichero de versiones no trae ninguna variante además de `main`")
        return 1

    print("Fichero de versiones: {}".format(os.path.relpath(args.versiones, ROOT)))
    print("Huella: {}".format(huella))
    print("DFL, {} partidos. `D` propio (nunca oráculo). `main`: {}. Variantes: {}\n".format(
        len(args.partidos), base_nombre, ", ".join(variantes)))

    rec = collections.defaultdict(list)
    for partido in args.partidos:
        t0 = time.time()
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        for modo, hacer in MODOS.items():
            for cond in dfl.VOTAN:
                trk = puntuar.solo_lectura(hacer(cargado, cond))
                for nombre in nombres:
                    pred = puntuar.ejecutar(versiones[nombre], trk, gt["flag"], "propio", partido)
                    for conv in dfl.CONVENCIONES:
                        rec[(conv, modo, cond, nombre)].append(puntuar.contar(gt[conv], pred))
        print("DFL {} en {:.0f} s".format(partido, time.time() - t0), file=sys.stderr, flush=True)

    for variante in variantes:
        print("`spellF1` de «{}» frente a «{}», con el `D` propio. Entre paréntesis, en cuántos partidos "
              "gana.\n".format(variante, base_nombre))
        print("| etiquetas | balón en los `D` | " + " | ".join(dfl.VOTAN) + " |")
        print("|---|---|" + "---|" * len(dfl.VOTAN))
        celdas = {}
        for conv in dfl.CONVENCIONES:
            for modo in MODOS:
                fila = []
                for cond in dfl.VOTAN:
                    base = rec[(conv, modo, cond, base_nombre)]
                    r = rec[(conv, modo, cond, variante)]
                    f0 = puntuar.spell_f1(*puntuar.juntar(base))
                    f = puntuar.spell_f1(*puntuar.juntar(r))
                    gana = sum(puntuar.spell_f1(a["flags"], a["n_pred"]) > puntuar.spell_f1(b["flags"], b["n_pred"])
                               for a, b in zip(r, base))
                    fila.append("{:+.3f} ({} de {})".format(f - f0, gana, len(r)))
                    celdas[(conv, modo, cond)] = (f - f0, gana, len(r))
                print("| DFL {} | {} | {} |".format(conv, modo, " | ".join(fila)))

        print("\n**Condición 1 (control):** +{:.3f} o más y ganar en {} de 7 en cada celda.".format(
            UMBRAL_CONTROL, GANA_DE))
        uno = []
        for modo in MODOS:
            for cond in dfl.VOTAN:
                dif, gana, total = celdas[("control", modo, cond)]
                ok = dif >= UMBRAL_CONTROL and gana >= GANA_DE
                uno.append(ok)
                print("- control / {} / {}: {:+.3f} y {} de {} -> {}".format(
                    modo, cond, dif, gana, total, "PASA" if ok else "NO PASA"))
        print("\n**Condición 3 (flag):** no perder más de {:.3f} en ninguna celda.".format(PERDIDA_MAXIMA_FLAG))
        tres = []
        for modo in MODOS:
            for cond in dfl.VOTAN:
                dif, _, _ = celdas[("flag", modo, cond)]
                ok = dif >= -PERDIDA_MAXIMA_FLAG
                tres.append(ok)
                print("- flag / {} / {}: {:+.3f} -> {}".format(modo, cond, dif, "PASA" if ok else "NO PASA"))
        print("\n**Condición 1: {}. Condición 3: {}.**\n".format(
            "PASA" if all(uno) else "NO PASA", "PASA" if all(tres) else "NO PASA"))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
