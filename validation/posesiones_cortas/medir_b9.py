"""B9 fuera del harness: placebo, retraso del balón y SkillCorner (docs/decisiones.md, 15/11, B9). Solo agregados.

    python validation/posesiones_cortas/medir_b9.py placebo         # DFL: dirección desplazada 60 s (descriptivo)
    python validation/posesiones_cortas/medir_b9.py retraso         # DFL: el balón 12 frames tarde (descriptivo)
    python validation/posesiones_cortas/medir_b9.py entrenamiento   # SkillCorner, lector.ENTRENAMIENTO (paso 4)
    python validation/posesiones_cortas/medir_b9.py examen   # se niega: B9 está descartado (ver abajo)

Datos abiertos de otros partidos: la DFL (Bassek et al., 2025, CC BY 4.0) y SkillCorner (A-League 2024/25,
licencia MIT). Lo puede ejecutar cualquiera, Claude incluido. Todo con el `D` de las etiquetas (oráculo) y
frente a `main` (B5). En la DFL, B5 y B9 con los coeficientes que no vieron cada partido; en SkillCorner, con
los de los 7 partidos (los de la entrega), que nunca han visto SkillCorner.

**B9 está descartado** (docs/decisiones.md, 15/11): el paso 4 salió negativo, así que el modo `examen` se
niega a ejecutarse. El examen de SkillCorner lo comparten todos los candidatos y no se gasta en uno
descartado. Lo que sigue es la regla tal como se escribió: **el examen se ejecuta una sola vez,** con el
candidato cerrado y si el paso 4 sale positivo en las dos
condiciones que votan (regla de B9 en docs/decisiones.md). Por eso pide `--una-vez`.
"""

import argparse
import collections
import functools
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                 os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline  # noqa: E402

PLACEBO_S = 60
RETRASO = 12
N_B5 = len(aprendida.NOMBRES["b5"])
BOOTSTRAP = 1000


def b9_placebo(trk, fuera=None):
    """B9 con sus pesos y las columnas de la dirección desplazadas 60 s (circular) dentro de cada tramo."""
    juego = aprendida.coeficientes("b9", fuera)
    r = aprendida.rasgos(trk, "b9")
    paso = PLACEBO_S * int(trk.fps)
    for a, b in trk.blocks:
        r[a:b, N_B5:] = np.roll(r[a:b, N_B5:], paso, axis=0)
    z = aprendida.logit(r, juego["pesos"])
    todos = aprendida.equipo_mas_cercano(trk)
    cercano = np.full(len(trk.bx), -1, dtype=np.int8)
    for a, b in trk.blocks:
        cercano[a:b] = todos[a:b]
    return aprendida.puntuacion_de("b9", z, aprendida.balon_visible(trk), juego["alfa"], cercano)


def retrasar(trk, retraso=RETRASO):
    """El mismo `Tracking` con el balón `retraso` frames tarde dentro de cada tramo (al principio, sin balón)."""
    bx, by = np.full(len(trk.bx), np.nan), np.full(len(trk.by), np.nan)
    for a, b in trk.blocks:
        bx[a + retraso:b] = trk.bx[a:b - retraso]
        by[a + retraso:b] = trk.by[a:b - retraso]
    return trk._replace(bx=bx, by=by)


def comparar(recuentos, versiones, referencia, n_draws):
    """Por (condición, convención): spellF1 de cada versión y diferencia con la referencia."""
    lineas = ["| balón | etiquetas | versión | spellF1 | frente a {} [5–95 %] | gana en | posesiones predichas / "
              "reales |".format(referencia), "|---|---|---|---|---|---|---|"]
    veredictos = {}
    for (cond, conv) in sorted({(k[0], k[1]) for k in recuentos}):
        ref = recuentos[(cond, conv, referencia)]
        jr = puntuar.juntar(ref)
        f1r = [puntuar.spell_f1(r["flags"], r["n_pred"]) for r in ref]
        for v in versiones:
            rec = recuentos[(cond, conv, v)]
            j = puntuar.juntar(rec)
            f1 = puntuar.spell_f1(*j)
            if v == referencia:
                lineas.append("| {} | {} | {} | {:.3f} | – | – | {} / {} |".format(cond, conv, v, f1, j[1], j[0].shape[1]))
                continue
            dif = f1 - puntuar.spell_f1(*jr)
            ic = puntuar.diferencia_bootstrap(j, jr, n_draws)
            gana = int(sum(a > b for a, b in zip([puntuar.spell_f1(r["flags"], r["n_pred"]) for r in rec], f1r)))
            veredictos[(cond, conv, v)] = (dif, ic, gana, len(rec))
            lineas.append("| {} | {} | {} | {:.3f} | {:+.3f} [{:+.3f} a {:+.3f}] | {} de {} | {} / {} |".format(
                cond, conv, v, f1, dif, ic[0], ic[1], gana, len(rec), j[1], j[0].shape[1]))
    return "\n".join(lineas).replace(".", ","), veredictos


def dfl_descriptivo(modo, retraso=RETRASO):
    nombres = ["main (B5)", "B9"] + (["B9 placebo (dirección desplazada 60 s)"] if modo == "placebo" else [])
    recuentos = collections.defaultdict(list)
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        for cond in dfl.VOTAN:
            trk = puntuar.solo_lectura(dfl.tracking_de(cargado, cond))
            if modo == "retraso":
                trk = retrasar(trk, retraso)
            piezas = {"main (B5)": functools.partial(aprendida.evidence_b5, fuera=partido),
                      "B9": functools.partial(aprendida.evidence_b9, fuera=partido),
                      "B9 placebo (dirección desplazada 60 s)": functools.partial(b9_placebo, fuera=partido)}
            for nombre in nombres:
                pred = pipeline.run(trk, extra=[puntuar.d_oraculo(gt["flag"])], pieces={"candidates": piezas[nombre]})
                for conv in dfl.CONVENCIONES:
                    recuentos[(cond, conv, nombre)].append(puntuar.contar(gt[conv], pred))
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    titulo = {"placebo": "Placebo: la dirección desplazada 60 s (descriptivo)",
              "retraso": "Sensibilidad: el balón {} frames tarde, para B9 y para main (descriptivo)".format(retraso)}[modo]
    print("# B9 en la DFL. {}\n".format(titulo))
    print(comparar(recuentos, nombres, "main (B5)", BOOTSTRAP)[0])


def skillcorner(mitad):
    import lector as lc
    if mitad == "entrenamiento":
        ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
        lc.exigir_solo_entrenamiento(ids)
    else:
        ids = [i for i in lc.partidos() if i in lc.EXAMEN]
    nombres = ["main (B5)", "B9"]
    recuentos = collections.defaultdict(list)
    for id_ in ids:
        crudo = lc.leer_crudo(id_)
        for cond in lc.VOTAN:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            trk = puntuar.solo_lectura(trk)
            for nombre, pieza in zip(nombres, (aprendida.evidence_b5, aprendida.evidence_b9)):
                pred = pipeline.run(trk, extra=[puntuar.d_oraculo(gt)], pieces={"candidates": pieza})
                recuentos[(cond, "SkillCorner", nombre)].append(puntuar.contar(gt, pred))
        print("hecho {}".format(id_), file=sys.stderr, flush=True)
    print("# B9 en SkillCorner, `lector.{}` ({} partidos), con el `D` oráculo\n".format(mitad.upper(), len(ids)))
    tabla, veredictos = comparar(recuentos, nombres, "main (B5)", BOOTSTRAP)
    print(tabla)
    difs = [veredictos[(c, "SkillCorner", "B9")] for c in lc.VOTAN]
    print()
    if mitad == "entrenamiento":
        print("Paso 4 (regla de B9): la diferencia frente a main es mayor que cero en las dos condiciones que votan: "
              "**{}**. Si es «no», el examen no se ejecuta.".format("sí" if all(d[0] > 0 for d in difs) else "no"))
    else:
        minimo = math.floor(0.8 * len(ids) + 1e-9)
        aguanta = all(d[0] >= 0 for d in difs)
        gana = all(d[0] >= 0.03 and d[1][0] > 0 and d[2] >= minimo for d in difs)
        positiva = all(d[0] > 0 and d[1][0] > 0 for d in difs)
        print("Paso 5 (regla de B9), en las dos condiciones que votan:")
        print("- aguanta (diferencia de 0 o más): **{}**".format("sí" if aguanta else "no"))
        print("- gana (+0,03 o más, intervalo por encima de cero y en {} de {} o más): **{}**".format(
            minimo, len(ids), "sí" if gana else "no"))
        print("- para la lectura 2 (diferencia mayor que cero con el intervalo por encima de cero): **{}**".format(
            "sí" if positiva else "no"))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("que", choices=("placebo", "retraso", "entrenamiento", "examen"))
    parser.add_argument("--una-vez", action="store_true", help="obligatorio con «examen»: se ejecuta una sola vez")
    parser.add_argument("--frames", type=int, default=RETRASO, help="con «retraso»: frames de retraso del balón")
    args = parser.parse_args()
    if args.que in ("placebo", "retraso"):
        dfl_descriptivo(args.que, args.frames)
    elif args.que == "examen":
        sys.exit("B9 está descartado: el paso 4 (SkillCorner, mitad de entrenamiento) salió negativo "
                 "(docs/decisiones.md, 15/11). El examen de SkillCorner no se gasta en él.")
    else:
        skillcorner(args.que)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
