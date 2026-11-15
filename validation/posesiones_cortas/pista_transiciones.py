"""Fase 4: ¿cuánto valdría una pista que marque dónde cambia la posesión? Pista sintética de transiciones.

    python validation/posesiones_cortas/pista_transiciones.py

DFL (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar cualquiera, Claude incluido. Solo agregados. La pista,
la rejilla y la lectura están en BITACORA.md §13, con commit antes de ejecutar. **No decide nada:** es una cota
superior.

`main` (B5 con el pliegue que no vio cada partido, coste 25) más la pista, con el `D` de las etiquetas,
decodificado directamente con `temporal.decode` sobre la evidencia de B5 y de `dead_state` calculada una vez
(el camino de `pista_sintetica.py`, que repite los números del harness).
"""

import collections
import math
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "scripts"),
                 os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import diagnostico_errores as de  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, ball, dead_state, temporal, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
SEMILLA = 20261117
TOPE = 125  # frames: duración máxima de una marca (5 s)
LEJOS = 125  # frames: una marca falsa no tiene ningún cambio real a esta distancia o menos
CERCA = 25  # frames: «un cambio nuestro a menos de 1 s»
FRACCIONES = (0.10, 0.16, 0.30)
ERRORES = (0, 12, 25, 50)
PRECISIONES = (0.7, 0.9, 1.0)
PESOS = (1.0, 2.0, 4.0, 8.0)
FORMAS = ("al azar", "solo las que main no encuentra")
LLEGA, DANO = 0.03, 0.01


def tramo_de(blocks, t):
    for a, b in blocks:
        if a <= t < b:
            return a, b
    return None


def largo_posesion(gt, t, fin):
    """Frames desde t hasta que cambia la etiqueta (o acaba el tramo)."""
    cambia = np.flatnonzero(gt[t:fin] != gt[t])
    return int(cambia[0]) if len(cambia) else fin - t


def cerca_de(reales, nuestros):
    """Para cada cambio real (t, de, a), ¿hay uno nuestro al mismo equipo a CERCA frames o menos?"""
    por_equipo = {e: np.array([c[0] for c in nuestros if c[2] == e], dtype=np.int64) for e in (H, A)}
    salida = np.zeros(len(reales), bool)
    for i, (t, _, a) in enumerate(reales):
        f = por_equipo[a]
        salida[i] = len(f) > 0 and int(np.min(np.abs(f - t))) <= CERCA
    return salida


def cobertura(gt, pred):
    runs = pm.valid_runs(gt)
    reales = de.cambios_directos(gt, runs)
    nuestros = de.cambios_directos(pm.fill_abstentions(pred, runs), runs)
    return np.array([int(cerca_de(reales, nuestros).sum()), len(reales)])


def main():
    inicio = time.time()
    rec = collections.defaultdict(list)
    cob = collections.defaultdict(lambda: np.zeros(2, dtype=np.int64))
    conteo = collections.Counter()
    for k, partido in enumerate(dfl.PARTIDOS):
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        gtc = gt["control"]
        _, permitido = puntuar.d_oraculo(gt["flag"])
        for ci, cond in enumerate(dfl.VOTAN):
            trk = ball.clean(puntuar.solo_lectura(dfl.tracking_de(cargado, cond)))
            base = aprendida.evidence_b5(trk, fuera=partido)[0] + dead_state.evidence(trk)[0]
            n = len(trk.bx)
            pred0 = temporal.decode(base, permitido, trk.blocks)
            for conv in dfl.CONVENCIONES:
                rec[(cond, conv, "main")].append(puntuar.contar(gt[conv], pred0))
                cob[(cond, conv, "main")] += cobertura(gt[conv], pred0)
            runs = pm.valid_runs(gtc)
            reales = de.cambios_directos(gtc, runs)
            nuestros0 = de.cambios_directos(pm.fill_abstentions(pred0, runs), runs)
            no_encontrado = ~cerca_de(reales, nuestros0)
            rng = np.random.default_rng([SEMILLA, k, ci])
            orden = rng.permutation(len(reales))
            u = rng.uniform(-1.0, 1.0, len(reales))
            # candidatas a marca falsa: juego, sin cambio real a LEJOS o menos, con sitio para la marca en el tramo
            lejos = np.ones(n, bool)
            for t, _, _ in reales:
                lejos[max(0, t - LEJOS):t + LEJOS + 1] = False
            hay_sitio = np.zeros(n, bool)
            for a, b in trk.blocks:
                hay_sitio[a:max(a, b - TOPE)] = True
            candidatas = np.flatnonzero(lejos & hay_sitio & np.isin(gtc, (H, A)))
            n_max_falsas = int(math.ceil(max(FRACCIONES) * len(reales) * (1 - min(PRECISIONES)) / min(PRECISIONES))) + 1
            falsas = rng.permutation(candidatas)[:n_max_falsas]
            conteo["reales"] += len(reales)
            conteo["no encontrados"] += int(no_encontrado.sum())
            for forma in FORMAS:
                pool = [i for i in orden if forma == FORMAS[0] or no_encontrado[i]]
                for r in FRACCIONES:
                    elegidos = pool[:int(round(r * len(reales)))]
                    for j in ERRORES:
                        for q in PRECISIONES:
                            pista = np.zeros((n, 3))
                            for i in elegidos:
                                t, _, nuevo = reales[i]
                                bloque = tramo_de(trk.blocks, t)
                                largo = min(TOPE, largo_posesion(gtc, t, bloque[1]))
                                s = min(max(bloque[0], t + int(round(u[i] * j))), bloque[1] - 1)
                                pista[s:min(bloque[1], s + largo), nuevo] += 1.0
                            n_falsas = int(round(len(elegidos) * (1 - q) / q))
                            for pos in falsas[:n_falsas]:
                                pista[pos:pos + TOPE, 1 - int(gtc[pos])] += 1.0
                            for w in PESOS:
                                pred = temporal.decode(base + w * pista, permitido, trk.blocks)
                                for conv in dfl.CONVENCIONES:
                                    clave = (cond, conv, (forma, r, j, q, w))
                                    rec[clave].append(puntuar.contar(gt[conv], pred))
                                    cob[clave] += cobertura(gt[conv], pred)
            print("hecho {} {} en {:.0f} s".format(partido, cond, time.time() - inicio), file=sys.stderr, flush=True)

    print("# Fase 4: una pista sintética que marca dónde cambia la posesión (DFL; BITACORA.md §13; descriptivo)\n")
    print("Cambios directos reales con el control (las dos condiciones juntas): {}; sin un cambio de `main` al mismo "
          "equipo a ≤ 1 s: {} ({:.0f} %).".format(conteo["reales"], conteo["no encontrados"],
                                                 100.0 * conteo["no encontrados"] / conteo["reales"]).replace(".", ","))
    base_f1 = {(c, v): puntuar.spell_f1(*puntuar.juntar(rec[(c, v, "main")])) for c in dfl.VOTAN for v in dfl.CONVENCIONES}
    print("`main` sin pista: " + "; ".join("{}, {}: {:.3f}".format(k[1], k[0], v) for k, v in base_f1.items())
          .replace(".", ",") + ".")
    print("Cambios reales con uno nuestro a ≤ 1 s, `main` sin pista («como el ATD»): " + "; ".join(
        "{} {:.0f} %".format(v, 100.0 * cob[(dfl.VOTAN[0], v, "main")][0] / cob[(dfl.VOTAN[0], v, "main")][1])
        for v in dfl.CONVENCIONES) + ".")

    veredicto = {}
    for forma in FORMAS:
        for conv in dfl.CONVENCIONES:
            print("\n### Marcas elegidas «{}», etiquetas «{}»: spellF1 frente a `main` («como el ATD» / «sin bloques») y "
                  "cambios reales con uno nuestro a ≤ 1 s («como el ATD»)\n".format(forma, conv))
            print("| r | j | q | " + " | ".join("w = {:g}".format(w) for w in PESOS) + " |")
            print("|---|---|---|" + "---|" * len(PESOS))
            for r in FRACCIONES:
                for j in ERRORES:
                    for q in PRECISIONES:
                        celdas = []
                        for w in PESOS:
                            difs = []
                            for cond in dfl.VOTAN:
                                clave = (cond, conv, (forma, r, j, q, w))
                                jj, jr = puntuar.juntar(rec[clave]), puntuar.juntar(rec[(cond, conv, "main")])
                                difs.append((puntuar.spell_f1(*jj) - base_f1[(cond, conv)],
                                             puntuar.diferencia_bootstrap(jj, jr, 1000)))
                            veredicto[(forma, conv, r, j, q, w)] = difs
                            c = cob[(dfl.VOTAN[0], conv, (forma, r, j, q, w))]
                            marca = ("▲" if all(d >= LLEGA and ic[0] > 0 for d, ic in difs)
                                     else "▼" if all(d <= -DANO and ic[1] < 0 for d, ic in difs) else "")
                            celdas.append("{} · {:.0f} % {}".format(
                                " / ".join("{:+.3f}".format(d) for d, _ in difs), 100.0 * c[0] / c[1], marca).strip())
                        print("| {:g} | {} | {:g} | {} |".format(r, j, q, " | ".join(celdas)).replace(".", ","))
    print("\n▲ llega: +0,03 o más con el intervalo por encima de cero en las dos condiciones. ▼ hace daño: −0,01 o menos "
          "con el intervalo por debajo de cero en las dos condiciones.")

    print("\n## Lectura de BITACORA.md §13\n")
    for forma in FORMAS:
        for conv in dfl.CONVENCIONES:
            llegan = [(r, j, q, w) for r in FRACCIONES for j in ERRORES for q in PRECISIONES for w in PESOS
                      if all(d >= LLEGA and ic[0] > 0 for d, ic in veredicto[(forma, conv, r, j, q, w)])]
            danan = [(r, j, q, w) for r in FRACCIONES for j in ERRORES for q in PRECISIONES for w in PESOS
                     if all(d <= -DANO and ic[1] < 0 for d, ic in veredicto[(forma, conv, r, j, q, w)])]
            if llegan:
                r_min = min(x[0] for x in llegan)
                texto = "la menor r que llega es **{:g}**, con (j, q, w) = {}".format(r_min, ", ".join(
                    "({}, {:g}, {:g})".format(j, q, w) for r, j, q, w in llegan if r == r_min))
            else:
                texto = "**ninguna** combinación llega a +0,03"
            print("- «{}», {}: {}; hacen daño {} de {} combinaciones{}.".format(
                forma, conv, texto, len(danan), len(FRACCIONES) * len(ERRORES) * len(PRECISIONES) * len(PESOS),
                "" if not danan else " (por ejemplo: " + ", ".join("r {:g}, j {}, q {:g}, w {:g}".format(*x)
                                                                  for x in danan[:4]) + ")").replace(".", ","))
    print("tiempo: {:.0f} s".format(time.time() - inicio), file=sys.stderr)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
