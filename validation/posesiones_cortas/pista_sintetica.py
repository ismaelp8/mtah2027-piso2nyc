"""Fase 4.2: ¿cuánto valdría una pista de equipo de fuera, como las fases del Smart Tagging? Pista sintética.

    python validation/posesiones_cortas/pista_sintetica.py

DFL (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar cualquiera, Claude incluido. Solo agregados. La pista,
la rejilla y la lectura están en BITACORA.md §11.2, con commit antes de ejecutar. **No decide nada:** es una
cota superior (los fallos sintéticos son independientes de los de B5).

`main` (B5 con el pliegue que no vio cada partido, coste 25) más la pista, con el `D` de las etiquetas. Se
decodifica directamente con `temporal.decode` sobre la evidencia de B5 y de `dead_state` calculada una vez (el
mismo camino de `puerta_no_lineal.py`, que repite los números del harness).
"""

import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, ball, dead_state, temporal, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
SEMILLA = 20261116
MEDIA_FASE = 188  # frames: las 575 fases del partido cubren el 68,1 % de 158.857 frames
ACIERTOS = (0.7, 0.8, 0.9, 0.95)
COBERTURAS = (0.3, 0.5, 0.68)
PESOS = (0.25, 0.5, 1.0, 2.0, 4.0)
ALCANCES = ("sin balón", "todos")
UMBRAL = 0.01


def fases(gt_control, blocks, c, rng):
    """[(inicio, fin, equipo mayoritario, u)] de la pista con cobertura `c`, alternando trozo y hueco."""
    hueco_medio = MEDIA_FASE * (1.0 - c) / c
    salida = []
    for a, b in blocks:
        t = a + int(rng.geometric(1.0 / max(hueco_medio, 1.0)))
        while t < b:
            largo = int(rng.geometric(1.0 / MEDIA_FASE))
            fin = min(b, t + largo)
            trozo = gt_control[t:fin]
            nh, na = int(np.sum(trozo == H)), int(np.sum(trozo == A))
            u = float(rng.random())
            if nh + na:
                salida.append((t, fin, H if nh >= na else A, u))
            t = fin + int(rng.geometric(1.0 / max(hueco_medio, 1.0)))
    return salida


def pista(n, trozos, p, w, mascara):
    score = np.zeros((n, 3))
    for a, b, mayoritario, u in trozos:
        equipo = mayoritario if u < p else 1 - mayoritario
        score[a:b, equipo] += w * mascara[a:b]
    return score


def main():
    inicio = time.time()
    rec = collections.defaultdict(list)
    cubierto = collections.defaultdict(lambda: np.zeros(2))
    acierto_real = collections.defaultdict(lambda: np.zeros(2))
    sin_balon_vivo = collections.defaultdict(lambda: np.zeros(2))
    for k, partido in enumerate(dfl.PARTIDOS):
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        _, permitido = puntuar.d_oraculo(gt["flag"])
        for cond in dfl.VOTAN:
            trk = ball.clean(puntuar.solo_lectura(dfl.tracking_de(cargado, cond)))
            base, _ = aprendida.evidence_b5(trk, fuera=partido)
            base = base + dead_state.evidence(trk)[0]
            evaluado = np.zeros(len(trk.bx), bool)
            for a, b in trk.blocks:
                evaluado[a:b] = True
            vivo = np.isin(gt["control"], (H, A)) & evaluado
            sin_balon = ~aprendida.balon_visible(trk)
            sin_balon_vivo[cond] += (np.sum(sin_balon & vivo), np.sum(vivo))
            mascaras = {"sin balón": sin_balon.astype(float), "todos": np.ones(len(trk.bx))}
            pred0 = temporal.decode(base, permitido, trk.blocks)
            for conv in dfl.CONVENCIONES:
                rec[(cond, conv, "main")].append(puntuar.contar(gt[conv], pred0))
            for c in COBERTURAS:
                rng = np.random.default_rng([SEMILLA, k, int(round(100 * c))])
                trozos = fases(gt["control"], trk.blocks, c, rng)
                cubierto[c] += (sum(b - a for a, b, _, _ in trozos), int(evaluado.sum()))
                for p in ACIERTOS:
                    acierto_real[(c, p)] += (sum(u < p for _, _, _, u in trozos), len(trozos))
                    for alcance in ALCANCES:
                        for w in PESOS:
                            pred = temporal.decode(base + pista(len(trk.bx), trozos, p, w, mascaras[alcance]),
                                                   permitido, trk.blocks)
                            for conv in dfl.CONVENCIONES:
                                rec[(cond, conv, (alcance, c, p, w))].append(puntuar.contar(gt[conv], pred))
            print("hecho {} {} en {:.0f} s".format(partido, cond, time.time() - inicio), file=sys.stderr, flush=True)

    print("# Fase 4.2: una pista de equipo sintética encima de `main` (DFL; BITACORA.md §11.2; descriptivo)\n")
    print("Cobertura conseguida de los frames evaluados: " + "; ".join(
        "c = {:g}: {:.1f} %".format(c, 100.0 * v[0] / v[1]) for c, v in cubierto.items()).replace(".", ",") + ".")
    print("Frames vivos sin balón: " + "; ".join("«{}» {:.1f} %".format(c, 100.0 * v[0] / v[1])
                                                for c, v in sin_balon_vivo.items()).replace(".", ",") + ".")
    print("Trozos que aciertan (sorteo): " + "; ".join("c = {:g}, p = {:g}: {:.1f} %".format(c, p, 100.0 * v[0] / v[1])
                                                     for (c, p), v in acierto_real.items() if c == COBERTURAS[-1]
                                                     ).replace(".", ",") + ".\n")
    base_f1 = {(cond, conv): puntuar.spell_f1(*puntuar.juntar(rec[(cond, conv, "main")]))
               for cond in dfl.VOTAN for conv in dfl.CONVENCIONES}
    print("`main` sin pista: " + "; ".join("{}, {}: {:.3f}".format(k[1], k[0], v) for k, v in base_f1.items())
          .replace(".", ",") + ".")
    veredicto = {}
    for alcance in ALCANCES:
        for conv in dfl.CONVENCIONES:
            print("\n### Alcance «{}», etiquetas «{}»: spellF1 frente a `main` («como el ATD» / «sin bloques»)\n".format(
                alcance, conv))
            print("| c | p | " + " | ".join("w = {:g}".format(w) for w in PESOS) + " |")
            print("|---|---|" + "---|" * len(PESOS))
            for c in COBERTURAS:
                for p in ACIERTOS:
                    celdas = []
                    for w in PESOS:
                        difs = []
                        for cond in dfl.VOTAN:
                            j = puntuar.juntar(rec[(cond, conv, (alcance, c, p, w))])
                            jr = puntuar.juntar(rec[(cond, conv, "main")])
                            ic = puntuar.diferencia_bootstrap(j, jr, 1000)
                            difs.append((puntuar.spell_f1(*j) - base_f1[(cond, conv)], ic))
                        veredicto[(alcance, c, p, w, conv)] = difs
                        marca = ("▲" if all(d >= UMBRAL and ic[0] > 0 for d, ic in difs)
                                 else "▼" if all(d <= -UMBRAL and ic[1] < 0 for d, ic in difs) else "")
                        celdas.append("{:+.3f} / {:+.3f} {}".format(difs[0][0], difs[1][0], marca).strip())
                    print("| {:g} | {:g} | {} |".format(c, p, " | ".join(celdas)).replace(".", ","))
    print("\n▲: +0,01 o más con el intervalo por encima de cero en las dos condiciones. ▼: −0,01 o menos con el "
          "intervalo por debajo de cero en las dos condiciones.")

    print("\n## Lectura de BITACORA.md §11.2\n")
    for alcance in ALCANCES:
        print("**Alcance «{}»**\n".format(alcance))
        for c in COBERTURAS:
            ayuda = [(p, w) for p in ACIERTOS for w in PESOS
                     if all(all(d >= UMBRAL and ic[0] > 0 for d, ic in veredicto[(alcance, c, p, w, conv)])
                            for conv in dfl.CONVENCIONES)]
            dano = [w for w in PESOS if any(all(d <= -UMBRAL and ic[1] < 0 for d, ic in veredicto[(alcance, c, ACIERTOS[0], w, conv)])
                                              for conv in dfl.CONVENCIONES)]
            p_min = min(p for p, _ in ayuda) if ayuda else None
            print("- c = {:g}: el menor acierto con el que algún peso ayuda con las dos convenciones: **{}**{}; con "
                  "p = 0,7 hace daño desde w = **{}**.".format(
                      c, "ninguno" if p_min is None else "{:g}".format(p_min),
                      "" if p_min is None else " (pesos que ayudan con ese acierto: {})".format(
                          ", ".join("{:g}".format(w) for p, w in ayuda if p == p_min)),
                      "ninguno" if not dano else "{:g}".format(min(dano))).replace(".", ","))
        print()
    print("tiempo: {:.0f} s".format(time.time() - inicio), file=sys.stderr)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
