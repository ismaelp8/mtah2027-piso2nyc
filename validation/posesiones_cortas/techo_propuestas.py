"""Techo de «proponer y clasificar» trozos del rival: ¿cuánto se ganaría con un clasificador perfecto? Descriptivo.

    python validation/posesiones_cortas/techo_propuestas.py

DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`).
Lo puede ejecutar cualquiera, Claude incluido. Solo agregados. **No decide nada** (BITACORA.md §5): dice si
merece la pena construir un candidato así.

La idea:
1. **Propuestas, sin etiquetas:** dentro de cada posesión que predice `main` (con el `D` de las etiquetas),
   los trozos seguidos en los que el jugador más cercano al balón es del otro equipo, a `RADIO` m o menos,
   durante `MINIMO` frames o más (los frames sin balón no cortan el trozo ni cuentan).
2. **Oráculo:** se aceptan solo las propuestas que coinciden con una posesión real del otro equipo (IoU ≥
   0,5). Es lo que haría un clasificador perfecto.
3. Se fuerzan en la evidencia y se decodifica otra vez. El spellF1 resultante es el techo de la idea con
   esas propuestas.

Se dan también cuántas propuestas hay y qué parte son buenas: si son pocas las buenas, el clasificador real
lo tendrá difícil.
"""

import collections
import functools
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                 os.path.join(ROOT, "validation", "scripts"), os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, candidates, pipeline, tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
VARIANTES = ((2.0, 12), (2.0, 25), (3.0, 12))  # (RADIO en m, MINIMO en frames)
FUERZA = 1000.0


def propuestas(pred, team, dist, blocks, radio, minimo):
    """[(inicio, fin, equipo propuesto)] dentro de las posesiones predichas, sin mirar etiquetas."""
    salida = []
    cerca = np.where(dist.min(axis=1) <= radio, team, -1)
    for a, b in blocks:
        for inicio, fin, equipo in pm.possession_spells(pred[a:b], [(0, b - a)]):
            rival = 1 - equipo
            trozo = cerca[a + inicio:a + fin]
            k = 0
            while k < len(trozo):
                if trozo[k] != rival:
                    k += 1
                    continue
                j, ultimo, n = k, k, 0
                while j < len(trozo) and trozo[j] != equipo:  # el balón ausente (-1) no corta
                    if trozo[j] == rival:
                        ultimo, n = j, n + 1
                    j += 1
                if n >= minimo:
                    salida.append((a + inicio + k, a + inicio + ultimo + 1, rival))
                k = ultimo + 1
    return salida


def iou(p, q):
    inter = max(0, min(p[1], q[1]) - max(p[0], q[0]))
    return inter / float(max(p[1], q[1]) - min(p[0], q[0]))


def buenas(props, gt):
    """Las propuestas con IoU ≥ 0,5 con una posesión real del mismo equipo."""
    reales = pm.possession_spells(gt, pm.valid_runs(gt))
    inicios = np.array([r[0] for r in reales])
    salida = []
    for p in props:
        k = np.searchsorted(inicios, p[1])
        cand = reales[max(0, k - 5):k + 1]
        salida.append(any(r[2] == p[2] and iou(p, r) >= 0.5 for r in cand))
    return np.array(salida, dtype=bool)


def forzar(evidencia, props, aceptadas):
    score, allowed = evidencia
    score = score.copy()
    for (a, b, equipo), ok in zip(props, aceptadas):
        if ok:
            score[a:b, equipo] += FUERZA
    return score, allowed


def medir(trk, gt_por_conv, pieza, acc, clave):
    limpio = pipeline.default_piece("ball")(trk)
    evidencia = pieza(limpio)
    gt0 = next(iter(gt_por_conv.values()))
    pred = pipeline.run(trk, extra=[puntuar.d_oraculo(gt0)], pieces={"candidates": lambda _t: evidencia})
    team, dist = candidates.proximity(limpio)
    for conv, gt in gt_por_conv.items():
        acc[(clave, conv, "main")].append(puntuar.contar(gt, pred))
    for radio, minimo in VARIANTES:
        props = propuestas(pred, team, dist, trk.blocks, radio, minimo)
        for conv, gt in gt_por_conv.items():
            ok = buenas(props, gt)
            nuevo = forzar(evidencia, props, ok)
            pred2 = pipeline.run(trk, extra=[puntuar.d_oraculo(gt0)], pieces={"candidates": lambda _t, e=nuevo: e})
            v = (radio, minimo)
            acc[(clave, conv, v)].append(puntuar.contar(gt, pred2))
            acc[("propuestas", clave, conv, v)].append((len(props), int(ok.sum())))


def imprimir(acc, clave, convenciones):
    print("\n### {}\n".format(clave))
    print("| etiquetas | versión | propuestas | buenas | spellF1 | posesiones predichas / reales |")
    print("|---|---|---|---|---|---|")
    for conv in convenciones:
        flags, n = puntuar.juntar(acc[(clave, conv, "main")])
        print("| {} | `main` | – | – | {:.3f} | {} / {} |".format(conv, puntuar.spell_f1(flags, n), n, flags.shape[1]))
        for v in VARIANTES:
            flags, n = puntuar.juntar(acc[(clave, conv, v)])
            tot = np.sum(acc[("propuestas", clave, conv, v)], axis=0)
            print("| {} | oráculo, ≤ {:g} m durante ≥ {} frames | {} | {} ({:.0f} %) | {:.3f} | {} / {} |".format(
                conv, v[0], v[1], tot[0], tot[1], 100.0 * tot[1] / max(tot[0], 1), puntuar.spell_f1(flags, n), n,
                flags.shape[1]).replace(".", ","))


def main():
    print("# Techo de «proponer y clasificar» trozos del rival (descriptivo)")
    acc = collections.defaultdict(list)
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        trk = puntuar.solo_lectura(dfl.tracking_de(cargado, dfl.VOTAN[0]))
        medir(trk, cargado["gt"], functools.partial(aprendida.evidence_b5, fuera=partido), acc, "DFL, «como el ATD»")
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    imprimir(acc, "DFL, «como el ATD»", dfl.CONVENCIONES)
    import lector as lc
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    for id_ in ids:
        trk, gt = lc.tracking_de(lc.leer_crudo(id_), "detectado", id_)
        medir(puntuar.solo_lectura(trk), {"SkillCorner": gt}, aprendida.evidence_b5, acc, "SkillCorner, «detectado»")
        print("hecho {}".format(id_), file=sys.stderr, flush=True)
    imprimir(acc, "SkillCorner, «detectado»", ("SkillCorner",))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
