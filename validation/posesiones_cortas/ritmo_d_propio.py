"""Fase 4.1: ¿es real el déficit de posesiones del partido? `main` con nuestro `D`, igual que en el partido.

    python validation/posesiones_cortas/ritmo_d_propio.py

DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`;
A-League 2024/25, licencia MIT). Lo puede ejecutar cualquiera, Claude incluido. Solo agregados. La regla está
en BITACORA.md §11.1, con commit antes de ejecutar.

El partido (`equipo_v3`, con nuestro `D`): 215 posesiones de 16,2 s de media, 3,7 por minuto de juego
predicho. Aquí se mide lo mismo con `main` sin oráculo: posesiones predichas por minuto de juego predicho (los
frames `H` o `A` de los tramos evaluados), su reparto por duración y su duración media.
"""

import collections
import functools
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                 os.path.join(ROOT, "validation", "apuesta_b"), os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import d_propio  # noqa: E402
import dfl  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
PARTIDO = {"ritmo": 3.7, "media_s": 16.2}  # equipo_v3 (CLAUDE.md, «Dónde estamos»)
FACTOR = 0.85
DUR = ((0, 50, "< 2 s"), (50, 125, "2–5 s"), (125, 250, "5–10 s"), (250, 500, "10–20 s"), (500, 10 ** 9, "≥ 20 s"))
FPS = 25


def resumen(pred, blocks):
    """(posesiones predichas, minutos de juego predicho, duraciones en frames) en los tramos evaluados."""
    spells = pm.possession_spells(pred, [tuple(b) for b in blocks])
    vivo = sum(int(np.sum(np.isin(pred[a:b], (H, A)))) for a, b in blocks)
    return len(spells), vivo / FPS / 60.0, [b - a for a, b, _ in spells]


def fila(nombre, por_partido, decide):
    n = sum(x[0] for x in por_partido)
    minutos = sum(x[1] for x in por_partido)
    duraciones = np.concatenate([np.asarray(x[2], dtype=float) for x in por_partido])
    ritmos = [x[0] / x[1] for x in por_partido if x[1] > 0]
    reparto = [np.mean((duraciones >= a) & (duraciones < b)) for a, b, _ in DUR]
    t = n / minutos
    print("| {} | {} | {:.2f} | {:.2f}–{:.2f} | {:.1f} | {} |".format(
        nombre, "sí" if decide else "no", t, min(ritmos), max(ritmos), duraciones.mean() / FPS,
        " | ".join("{:.0f} %".format(100.0 * r) for r in reparto)).replace(".", ","))
    return {"ritmo": t, "minimo": min(ritmos)}


def main():
    print("# Fase 4.1: ¿es real el déficit del partido? `main` con nuestro `D` (BITACORA.md §11.1)\n")
    acc = collections.defaultdict(list)
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        piezas = {"candidates": functools.partial(aprendida.evidence_b5, fuera=partido)}
        for cond in dfl.VOTAN:
            for balon, hacer in (("balón tapado en los D", dfl.tracking_de), ("balón a la vista en los D",
                                                                                d_propio.con_balon_en_d)):
                trk = puntuar.solo_lectura(hacer(cargado, cond))
                acc[("DFL", cond, balon)].append(resumen(pipeline.run(trk, pieces=piezas), trk.blocks))
            if cond == dfl.VOTAN[0]:
                trk = puntuar.solo_lectura(dfl.tracking_de(cargado, cond))
                acc[("DFL, `D` de las etiquetas (como en la fase 1)", cond, "")].append(resumen(
                    pipeline.run(trk, extra=[puntuar.d_oraculo(cargado["gt"]["flag"])], pieces=piezas), trk.blocks))
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    import lector as lc
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    for id_ in ids:
        crudo = lc.leer_crudo(id_)
        for cond in lc.VOTAN:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            trk = puntuar.solo_lectura(trk)
            acc[("SkillCorner", cond, "")].append(resumen(pipeline.run(trk), trk.blocks))
        print("hecho {}".format(id_), file=sys.stderr, flush=True)

    print("Posesiones predichas por minuto de juego predicho, con nuestro `D` (sin oráculo), en los tramos evaluados.\n")
    print("| fuente | ¿decide? | ritmo, todos juntos | por partido, mín–máx | duración media (s) | " +
          " | ".join(n for _, _, n in DUR) + " |")
    print("|---|---|---|---|---|" + "---|" * len(DUR))
    print("| **partido (`equipo_v3`)** | – | {:.2f} | – | {:.1f} | – | – | – | – | – |".format(
        PARTIDO["ritmo"], PARTIDO["media_s"]).replace(".", ","))
    refs = {}
    orden = [("DFL", dfl.VOTAN[0], "balón tapado en los D", "R1"), ("DFL", dfl.VOTAN[0], "balón a la vista en los D", "R2"),
             ("SkillCorner", lc.VOTAN[0], "", "R3"), ("DFL", dfl.VOTAN[1], "balón tapado en los D", None),
             ("DFL", dfl.VOTAN[1], "balón a la vista en los D", None), ("SkillCorner", lc.VOTAN[1], "", None),
             ("DFL, `D` de las etiquetas (como en la fase 1)", dfl.VOTAN[0], "", None)]
    for fuente, cond, balon, ref in orden:
        nombre = "{}{}, «{}»{}".format("{}: ".format(ref) if ref else "", fuente, cond, ", " + balon if balon else "")
        r = fila(nombre, acc[(fuente, cond, balon)], ref is not None)
        if ref:
            refs[ref] = r

    print("\n## Regla de BITACORA.md §11.1\n")
    debajo = []
    for ref, r in refs.items():
        cumple = PARTIDO["ritmo"] < FACTOR * r["ritmo"] and PARTIDO["ritmo"] < r["minimo"]
        debajo.append(cumple)
        print("- {}: {:.2f} < {:.2f} ({:g} × {:.2f}) y {:.2f} < {:.2f} (mínimo por partido): **{}**".format(
            ref, PARTIDO["ritmo"], FACTOR * r["ritmo"], FACTOR, r["ritmo"], PARTIDO["ritmo"], r["minimo"],
            "sí" if cumple else "no").replace(".", ","))
    if sum(debajo) >= 2:
        print("\n**El partido va más corto** (en {} de 3 referencias): toca el script de `validation/partido/`.".format(
            sum(debajo)))
    else:
        print("\n**Cerca:** no hay un déficit propio del partido ({} de 3 referencias por debajo). La respuesta sigue "
              "siendo el signo de la evidencia.".format(sum(debajo)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
