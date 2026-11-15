"""¿Dónde se pierde el spellF1? Diagnóstico descriptivo en los 7 partidos de la DFL, solo agregados.

    python validation/scripts/diagnostico_spell.py

Cambia una pieza cada vez por la respuesta de las etiquetas y puntúa con el scorer oficial
(docs/decisiones.md, 15/11, «dónde se pierde el spellF1»). No decide nada: sirve para repartir el trabajo.
Tarda unos 3 minutos. Solo lee la caché de la DFL (validation/harness/README.md): nada del partido, así que
Claude puede ejecutarlo.

Versiones, todas con el balón «como el ATD» (la condición que vota):
- main: B5, Viterbi con coste 25 y `D` oráculo (lo que mide el harness);
- main con el `D` propio: el `D` lo pone `dead_state`, sin oráculo (no decide; plan §4);
- equipo perfecto donde se ve el balón: +5 al equipo de la etiqueta solo en los frames con balón visible y 0
  en el resto; coste 25 y `D` oráculo. Es el techo de una evidencia de equipo perfecta con el balón del ATD;
- equipo perfecto siempre: lo mismo en todos los frames de juego. Es el techo del decodificador con coste 25.

Además, las posesiones reales que encuentra main (IoU >= 0,5) según su duración, y los cambios de equipo.
"""
import collections
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
import dfl  # noqa: E402
import puntuar  # noqa: E402
import possession_metrics as pm  # noqa: E402
from possession import temporal  # noqa: E402
from possession.tracking import A, D, H  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):  # tildes y símbolos también en la consola de Windows
    sys.stdout.reconfigure(encoding="utf-8")

CONDICION = "como el ATD"
TRAMOS = [(0, 25, "< 1 s"), (25, 50, "1–2 s"), (50, 125, "2–5 s"), (125, 250, "5–10 s"), (250, 10 ** 9, "≥ 10 s")]


def emparejar(reales, predichas, umbral=0.5):
    solapes = pm.spell_overlaps(reales, predichas)
    r, p = set(), set()
    for iou, i, j in solapes:
        if iou < umbral:
            break
        if i in r or j in p:
            continue
        r.add(i)
        p.add(j)
    return r, p


def perfecta(gt_conv, gt_flag, visible, blocks, solo_visible, fuerza=5.0):
    score = np.zeros((len(gt_conv), 3))
    donde = visible if solo_visible else np.ones(len(gt_conv), dtype=bool)
    score[donde & (gt_conv == H), H] = fuerza
    score[donde & (gt_conv == A), A] = fuerza
    _, allowed = puntuar.d_oraculo(gt_flag)
    return temporal.decode(score, allowed, blocks)


main = puntuar.version_de({}, "main")
f1 = collections.defaultdict(list)  # (versión, convención) -> recuentos por partido
tramos_r = collections.defaultdict(lambda: np.zeros((len(TRAMOS), 2), dtype=int))  # (conv) -> [n, emparejadas]
tramos_p = collections.defaultdict(lambda: np.zeros((len(TRAMOS), 2), dtype=int))
cambios = collections.defaultdict(int)
for partido in dfl.PARTIDOS:
    cargado = dfl.cargar(partido)
    gt = cargado["gt"]
    trk = puntuar.solo_lectura(dfl.tracking_de(cargado, CONDICION))
    visible = ~np.isnan(trk.bx)
    preds = {
        "main (B5, coste 25, D oráculo)": puntuar.ejecutar(main, trk, gt["flag"], "oraculo", partido),
        "main con el D propio": puntuar.ejecutar(main, trk, gt["flag"], "propio", partido),
    }
    for conv in dfl.CONVENCIONES:
        conv_preds = dict(preds)
        conv_preds["equipo perfecto donde se ve el balón"] = perfecta(gt[conv], gt["flag"], visible, trk.blocks, True)
        conv_preds["equipo perfecto siempre"] = perfecta(gt[conv], gt["flag"], visible, trk.blocks, False)
        for nombre, pred in conv_preds.items():
            f1[(nombre, conv)].append(puntuar.contar(gt[conv], pred))
        # Desglose de main por duración de la posesión
        runs = pm.valid_runs(gt[conv])
        reales = pm.possession_spells(gt[conv], runs)
        predichas = pm.possession_spells(pm.fill_abstentions(preds["main (B5, coste 25, D oráculo)"], runs), runs)
        r, p = emparejar(reales, predichas)
        for k, (a, b, _) in enumerate(reales):
            for t, (lo, hi, _) in enumerate(TRAMOS):
                if lo <= b - a < hi:
                    tramos_r[conv][t] += (1, k in r)
        for k, (a, b, _) in enumerate(predichas):
            for t, (lo, hi, _) in enumerate(TRAMOS):
                if lo <= b - a < hi:
                    tramos_p[conv][t] += (1, k in p)
        # Cambios de equipo dentro del juego (H<->A sin D en medio)
        for nombre, codes in (("reales", gt[conv]), ("predichos", preds["main (B5, coste 25, D oráculo)"])):
            for a, b in runs:
                w = codes[a:b]
                cambios[(conv, nombre)] += int(np.sum(((w[1:] == H) & (w[:-1] == A)) | ((w[1:] == A) & (w[:-1] == H))))
    print("hecho", partido, flush=True)

print("\n## spellF1, 7 partidos juntos, balón «{}»\n".format(CONDICION))
print("| versión | flag | control |")
print("|---|---|---|")
nombres = []
for (nombre, conv) in f1:
    if nombre not in nombres:
        nombres.append(nombre)
for nombre in nombres:
    celdas = []
    for conv in dfl.CONVENCIONES:
        flags, n_pred = puntuar.juntar(f1[(nombre, conv)])
        celdas.append("{:.3f} ({} pred.)".format(puntuar.spell_f1(flags, n_pred), n_pred))
    print("| {} | {} | {} |".format(nombre, *celdas))

for conv in dfl.CONVENCIONES:
    print("\n## main por duración, etiquetas «{}» (emparejadas con IoU ≥ 0,5)\n".format(conv))
    print("| duración | posesiones reales | % encontradas | posesiones predichas | % que son reales |")
    print("|---|---|---|---|---|")
    for t, (_, _, nombre) in enumerate(TRAMOS):
        nr, er = tramos_r[conv][t]
        npp, ep = tramos_p[conv][t]
        print("| {} | {} | {:.0f} % | {} | {:.0f} % |".format(nombre, nr, 100.0 * er / max(nr, 1), npp, 100.0 * ep / max(npp, 1)))
    print("\ncambios de equipo en juego: reales {}, predichos {}".format(cambios[(conv, "reales")], cambios[(conv, "predichos")]))
