"""«Cortas a `D`» (idea 1.3) en SkillCorner: reproduce S9 en la mitad de entrenamiento y, con permiso, abre el
examen una sola vez.

    python validation/scripts/cortas_a_d_skillcorner.py --versiones validation/harness/versiones/cortas_a_d_2026-11-16.json
    python validation/scripts/cortas_a_d_skillcorner.py --versiones <fichero> --examen

Datos abiertos de otros partidos (A-League 2024/25, licencia MIT; ver `validation/skillcorner/descargar.py`).
Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Por qué hace falta este script: `validation/skillcorner/medir.py` no acepta `--versiones` (sus versiones están
fijas en el código) y por defecto usa los 20 partidos, **examen incluido**. Aquí la mitad de examen solo se lee
con `--examen`, y el `D` es siempre el propio, como en S9.

**El examen (`lector.EXAMEN`) solo se abre con el permiso de Ismael y se usa una sola vez.** El umbral está
escrito antes en `docs/decisiones.md` (16/11, «la idea 1.3 se desaparca»): entra si gana a `main` por +0,005 o
más y gana en 7 de 10 partidos, en las dos condiciones que votan. Cada uso se apunta en ese fichero.
"""

import argparse
import collections
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                ROOT, os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, carpeta)
import lector as lc  # noqa: E402
import puntuar  # noqa: E402
from possession import pipeline  # noqa: E402

VERSIONES = os.path.join(ROOT, "validation", "harness", "versiones", "cortas_a_d_2026-11-16.json")
UMBRAL = 0.005  # el del límite de daño (docs/decisiones.md, 16/11)
GANA_DE = 7  # de 10 partidos, en el examen


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--versiones", default=VERSIONES, help="fichero de versiones del harness")
    parser.add_argument("--examen", action="store_true",
                        help="abre la mitad de examen (lector.EXAMEN). Solo con el permiso de Ismael y UNA vez")
    args = parser.parse_args()

    versiones, contenido, huella = puntuar.leer_versiones(args.versiones)
    nombres = [n for n in contenido if versiones[n]["tipo"] != "control"]
    if len(nombres) < 2:
        print("hacen falta al menos dos versiones en el fichero (main y la variante)")
        return 1
    base_nombre = nombres[0]

    mitad = "EXAMEN" if args.examen else "ENTRENAMIENTO"
    ids = list(lc.EXAMEN if args.examen else lc.ENTRENAMIENTO)
    if args.examen:
        print("### ATENCION: se esta abriendo la mitad de EXAMEN de SkillCorner.")
        print("Es el unico uso permitido (permiso de Ismael, 16/11). Apuntalo en docs/decisiones.md.\n")
    else:
        lc.exigir_solo_entrenamiento(ids)

    print("Fichero de versiones: {}".format(os.path.relpath(args.versiones, ROOT)))
    print("Huella: {}".format(huella))
    print("Mitad: {} ({} partidos). `D` propio. Versiones: {}\n".format(mitad, len(ids), ", ".join(nombres)))

    rec = collections.defaultdict(list)
    for id_ in ids:
        t0 = time.time()
        crudo = lc.leer_crudo(id_)
        for cond in lc.VOTAN:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            trk = puntuar.solo_lectura(trk)
            for nombre in nombres:
                version = versiones[nombre]
                pred = pipeline.run(trk, params=version["params"], pieces=version.get("piezas") or None)
                rec[(cond, nombre)].append(puntuar.contar(gt, pred))
        print("partido {} en {:.0f} s".format(id_, time.time() - t0), file=sys.stderr, flush=True)

    print("`spellF1` en SkillCorner, mitad de {}, con el `D` propio.\n".format(mitad.lower()))
    print("| condición | " + " | ".join(nombres) + " |")
    print("|---|" + "---|" * len(nombres))
    veredicto = []
    for cond in lc.VOTAN:
        base = rec[(cond, base_nombre)]
        f0 = puntuar.spell_f1(*puntuar.juntar(base))
        celdas = ["{:.3f}".format(f0)]
        for nombre in nombres[1:]:
            r = rec[(cond, nombre)]
            f = puntuar.spell_f1(*puntuar.juntar(r))
            gana = sum(puntuar.spell_f1(a["flags"], a["n_pred"]) > puntuar.spell_f1(b["flags"], b["n_pred"])
                       for a, b in zip(r, base))
            celdas.append("{:.3f} ({:+.3f}, {} de {})".format(f, f - f0, gana, len(r)))
            veredicto.append((cond, nombre, f - f0, gana, len(r)))
        print("| {} | {} |".format(cond, " | ".join(celdas)))

    if args.examen:
        print("\n**Umbral escrito antes de abrir el examen:** +{:.3f} o mas y ganar en {} de 10.".format(
            UMBRAL, GANA_DE))
        for cond, nombre, dif, gana, total in veredicto:
            ok = dif >= UMBRAL and gana >= GANA_DE
            print("- {} / {}: {:+.3f} y {} de {} -> {}".format(
                cond, nombre, dif, gana, total, "PASA" if ok else "NO PASA"))
        pasa = all(dif >= UMBRAL and gana >= GANA_DE for _, _, dif, gana, _ in veredicto)
        print("\n**Veredicto del examen: {}**".format("PASA en las dos condiciones" if pasa else "NO PASA"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
