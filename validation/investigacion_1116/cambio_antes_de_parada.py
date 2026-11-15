"""Sondeo S5: posesiones cortas del otro equipo justo antes de una parada nuestra. ¿Sobran?

    python validation/investigacion_1116/cambio_antes_de_parada.py

DFL (7 partidos abiertos, Bassek et al., 2025, CC BY 4.0), `D` propio (las piezas de `main`), las dos
condiciones que votan y dos modos del balón en los `D`: tapado y a la vista. Lo puede ejecutar cualquiera,
Claude incluido. Solo imprime agregados. La regla de lectura está en BITACORA.md (S5), escrita antes.
"""

import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, os.path.join(ROOT, "validation", "apuesta_b"))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import d_propio  # noqa: E402
import dfl  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import temporal  # noqa: E402

H, A, D, X = dfl.H, dfl.A, dfl.D, dfl.X
VERSIONES = os.path.join(ROOT, "validation", "harness", "versiones", "investigacion_costes_2026-11-16.json")
CORTES = (75, 125, 250)  # frames: 3, 5 y 10 s. El de la regla es 125
MODOS = {"tapado": dfl.tracking_de, "a la vista": d_propio.con_balon_en_d}


def candidatas(pred, blocks, corte):
    """[(inicio, fin, equipo de antes)] de las posesiones de menos de `corte` frames que acaban en un `D`
    nuestro y vienen de un cambio directo desde el otro equipo."""
    out = []
    for a, b in blocks:
        r = temporal.runs(pred[a:b])
        for k in range(1, len(r) - 1):
            etiqueta, i, j = r[k]
            if etiqueta in (H, A) and r[k + 1][0] == D and r[k - 1][0] in (H, A) and r[k - 1][0] != etiqueta \
                    and j - i < corte:
                out.append((a + i, a + j, r[k - 1][0]))
    return out


def emparejada(gt, blocks, inicio, fin, equipo):
    """¿Hay una posesión real del mismo equipo con IoU ≥ 0,5 con [inicio, fin)?"""
    for a, b in blocks:
        if not a <= inicio < b:
            continue
        for etiqueta, i, j in temporal.runs(gt[a:b]):
            i, j = a + i, a + j
            if etiqueta != equipo or j <= inicio or fin <= i:
                continue
            inter = min(j, fin) - max(i, inicio)
            union = max(j, fin) - min(i, inicio)
            if inter / float(union) >= 0.5:
                return True
    return False


def main():
    main_version = puntuar.leer_versiones(VERSIONES)[0]["main: B5 y coste 25"]
    recuentos = collections.defaultdict(list)
    cuenta = collections.defaultdict(lambda: np.zeros(6, dtype=np.int64))
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        for modo, hacer in MODOS.items():
            for cond in dfl.VOTAN:
                trk = puntuar.solo_lectura(hacer(cargado, cond))
                pred = puntuar.ejecutar(main_version, trk, gt["flag"], "propio", partido)
                for conv in dfl.CONVENCIONES:
                    recuentos[(modo, cond, conv, "main", 0)].append(puntuar.contar(gt[conv], pred))
                for corte in CORTES:
                    lista = candidatas(pred, trk.blocks, corte)
                    a_d, a_antes = pred.copy(), pred.copy()
                    for i, j, antes in lista:
                        a_d[i:j] = D
                        a_antes[i:j] = antes
                    for conv in dfl.CONVENCIONES:
                        recuentos[(modo, cond, conv, "a D", corte)].append(puntuar.contar(gt[conv], a_d))
                        recuentos[(modo, cond, conv, "al de antes", corte)].append(puntuar.contar(gt[conv], a_antes))
                        if corte == 125:
                            g = gt[conv]
                            c = cuenta[(modo, cond, conv)]
                            for i, j, antes in lista:
                                equipo = int(pred[i])
                                c += [1, int(emparejada(g, trk.blocks, i, j, equipo)), j - i,
                                      int(np.sum(g[i:j] == D)), int(np.sum(g[i:j] == equipo)),
                                      int(np.sum(g[i:j] == antes))]
        print("hecho {}".format(partido), file=sys.stderr, flush=True)

    print("## Las posesiones candidatas (corte de 5 s), 7 partidos juntos\n")
    print("| balón en los `D` | condición | etiquetas | candidatas | emparejadas con una real (IoU ≥ 0,5) | sus frames son, de verdad: `D` / su equipo / el de antes |")
    print("|---|---|---|---|---|---|")
    for modo in MODOS:
        for cond in dfl.VOTAN:
            for conv in dfl.CONVENCIONES:
                n, emp, frames, fd, fe, fa = cuenta[(modo, cond, conv)]
                print("| {} | {} | {} | {} | {} ({:.0f} %) | {:.0f} % / {:.0f} % / {:.0f} % |".format(
                    modo, cond, conv, n, emp, 100.0 * emp / max(n, 1), 100.0 * fd / max(frames, 1),
                    100.0 * fe / max(frames, 1), 100.0 * fa / max(frames, 1)))
    print("\n## spellF1 con el `D` propio: `main` y las dos variantes (diferencia frente a `main`)\n")
    print("| balón en los `D` | condición | etiquetas | `main` | " + " | ".join(
        "{} s, {}".format(c // 25, v) for c in CORTES for v in ("a D", "al de antes")) + " |")
    print("|---|---|---|---|" + "---|" * (2 * len(CORTES)))
    for modo in MODOS:
        for cond in dfl.VOTAN:
            for conv in dfl.CONVENCIONES:
                base = puntuar.spell_f1(*puntuar.juntar(recuentos[(modo, cond, conv, "main", 0)]))
                celdas = []
                for corte in CORTES:
                    for variante in ("a D", "al de antes"):
                        rec = recuentos[(modo, cond, conv, variante, corte)]
                        f1 = puntuar.spell_f1(*puntuar.juntar(rec))
                        gana = sum(puntuar.spell_f1(r["flags"], r["n_pred"]) > puntuar.spell_f1(m["flags"], m["n_pred"])
                                   for r, m in zip(rec, recuentos[(modo, cond, conv, "main", 0)]))
                        celdas.append("{:+.3f} ({} de 7)".format(f1 - base, gana))
                print("| {} | {} | {} | {:.3f} | {} |".format(modo, cond, conv, base, " | ".join(celdas)))


if __name__ == "__main__":
    main()
