"""Sondeo S2: ¿sirve decodificar a riesgo mínimo con la evidencia de B5?

    python validation/investigacion_1116/riesgo_minimo.py

DFL (7 partidos abiertos, Bassek et al., 2025, CC BY 4.0), balón «como el ATD», `D` de las etiquetas y B5 con
los coeficientes que no vieron cada partido, como el harness. Lo puede ejecutar cualquiera, Claude incluido.
Solo imprime agregados. La regla de lectura está en BITACORA.md (S2), escrita antes de ejecutar.

Qué hace:
1. convierte la cadena del decodificador en una distribución, p(secuencia) ∝ exp(puntuación / T), y elige T
   por la verosimilitud por frame en los otros seis partidos;
2. mira si la anchura de la duda alrededor de cada cambio de `main` tiene que ver con su error real;
3. saca muestras, elige en cada parte el Viterbi (de seis costes) con más spellF1 medio frente a ellas, y
   puntúa esa elección con las etiquetas de verdad.
"""

import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import pipeline, temporal  # noqa: E402

H, A, D, X = dfl.H, dfl.A, dfl.D, dfl.X
CONDICION = "como el ATD"
TEMPERATURAS = (1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
COSTES = (8.0, 12.0, 18.0, 25.0, 35.0, 50.0)
MUESTRAS = 24
SEMILLA = 20261116
CERCA = 50  # frames: un cambio nuestro tiene pareja si hay uno real hacia el mismo equipo a esta distancia
DUDA = (0.2, 0.8)


def evidencia(trk, gt, partido):
    """La evidencia sumada de `main` con el `D` de las etiquetas, como `pipeline.run` antes de decodificar."""
    piezas = puntuar.piezas_para(None, None, partido)
    clean = piezas.get("ball") or pipeline.default_piece("ball")
    team = piezas.get("candidates") or pipeline.default_piece("candidates")
    state = piezas.get("dead_state") or pipeline.default_piece("dead_state")
    limpio = clean(trk)
    score, allowed, _ = pipeline.combine([team(limpio), state(limpio), puntuar.d_oraculo(gt)], len(limpio.bx))
    return score, allowed


def adelante_atras(emision, coste, temperatura):
    """(alfa, logaritmo de las marginales) de un tramo. `emision`: (n, 3) con -inf en lo prohibido."""
    e = emision / temperatura
    c = np.asarray(coste) / temperatura
    n = len(e)
    alfa = np.empty((n, 3))
    beta = np.zeros((n, 3))
    alfa[0] = e[0]
    for t in range(1, n):
        alfa[t] = e[t] + np.logaddexp.reduce(alfa[t - 1][:, None] - c, axis=0)
    for t in range(n - 2, -1, -1):
        beta[t] = np.logaddexp.reduce(-c + (e[t + 1] + beta[t + 1])[None, :], axis=1)
    log_z = np.logaddexp.reduce(alfa[-1])
    return alfa, alfa + beta - log_z


def muestrear(alfa, coste, temperatura, k, rng):
    """`k` secuencias de la distribución (hacia delante se filtra, hacia atrás se sortea). (k, n) int8."""
    c = np.asarray(coste) / temperatura
    n = len(alfa)
    salida = np.empty((k, n), dtype=np.int8)
    ruido = rng.gumbel(size=(k, 3))
    salida[:, -1] = np.argmax(alfa[-1][None, :] + ruido, axis=1)
    for t in range(n - 2, -1, -1):
        logits = alfa[t][None, :] - c[:, salida[:, t + 1]].T
        salida[:, t] = np.argmax(logits + rng.gumbel(size=(k, 3)), axis=1)
    return salida


def cambios_directos(codes, a, b):
    """[(frame, equipo nuevo)] de los cambios directos de equipo dentro del tramo [a, b)."""
    w = codes[a:b]
    t = np.flatnonzero((w[1:] != w[:-1]) & (w[1:] != D) & (w[:-1] != D) & (w[1:] != X) & (w[:-1] != X)) + 1
    return [(a + int(i), int(w[i])) for i in t]


def rangos(v):
    orden = np.argsort(v, kind="mergesort")
    r = np.empty(len(v))
    r[orden] = np.arange(len(v))
    # empates: rango medio
    v = np.asarray(v)
    for valor in np.unique(v):
        m = v == valor
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    rx, ry = rangos(x), rangos(y)
    return float(np.corrcoef(rx, ry)[0, 1])


def auc(positivos, negativos):
    """Probabilidad de que un positivo tenga más valor que un negativo (los empates cuentan la mitad)."""
    if not len(positivos) or not len(negativos):
        return float("nan")
    todos = np.concatenate([positivos, negativos])
    r = rangos(todos) + 1
    suma = r[:len(positivos)].sum()
    return float((suma - len(positivos) * (len(positivos) + 1) / 2.0) / (len(positivos) * len(negativos)))


def spell_de_tramo(gt, pred, a, b):
    return pm.spell_scores(gt, pred, [(a, b)])["mean_f1"]


def main():
    rng = np.random.default_rng(SEMILLA)
    coste = temporal.cost_matrix(temporal.DEFAULTS)
    datos = {}
    for partido in dfl.PARTIDOS:
        t0 = time.time()
        cargado = dfl.cargar(partido)
        trk = puntuar.solo_lectura(dfl.tracking_de(cargado, CONDICION))
        gt = cargado["gt"]
        score, allowed = evidencia(trk, gt["flag"], partido)  # el `D` es el mismo con las dos convenciones
        emision = np.where(allowed, score, -np.inf)
        viterbis = {c: temporal.decode(score, allowed, trk.blocks, {"switch": c}) for c in COSTES}
        tramos = []
        for a, b in trk.blocks:
            porT = {}
            for T in TEMPERATURAS:
                alfa, logm = adelante_atras(emision[a:b], coste, T)
                porT[T] = (alfa, logm)
            tramos.append(((a, b), porT))
        # verosimilitud por frame de cada convención y temperatura
        nll = {}
        for conv in dfl.CONVENCIONES:
            for T in TEMPERATURAS:
                total, cuenta = 0.0, 0
                for (a, b), porT in tramos:
                    g = gt[conv][a:b]
                    vivo = (g == H) | (g == A)
                    lp = porT[T][1][np.flatnonzero(vivo), g[vivo]]
                    total += float(-np.maximum(lp, -50.0).sum())
                    cuenta += int(vivo.sum())
                nll[(conv, T)] = (total, cuenta)
        datos[partido] = {"gt": gt, "blocks": trk.blocks, "viterbis": viterbis, "tramos": tramos, "nll": nll}
        print("preparado {} en {:.0f} s".format(partido, time.time() - t0), file=sys.stderr, flush=True)

    print("## 1. Temperatura\n")
    print("Verosimilitud negativa media por frame vivo (menos es mejor), los 7 partidos juntos:\n")
    print("| T | flag | control |")
    print("|---|---|---|")
    for T in TEMPERATURAS:
        fila = []
        for conv in dfl.CONVENCIONES:
            tot = sum(datos[p]["nll"][(conv, T)][0] for p in dfl.PARTIDOS)
            cnt = sum(datos[p]["nll"][(conv, T)][1] for p in dfl.PARTIDOS)
            fila.append("{:.3f}".format(tot / cnt))
        print("| {:g} | {} |".format(T, " | ".join(fila)))
    elegida = {}
    for partido in dfl.PARTIDOS:
        otros = [p for p in dfl.PARTIDOS if p != partido]
        mejor = None
        for T in TEMPERATURAS:
            medias = []
            for conv in dfl.CONVENCIONES:
                tot = sum(datos[p]["nll"][(conv, T)][0] for p in otros)
                cnt = sum(datos[p]["nll"][(conv, T)][1] for p in otros)
                medias.append(tot / cnt)
            valor = float(np.mean(medias))
            if mejor is None or valor < mejor[0]:
                mejor = (valor, T)
        elegida[partido] = mejor[1]
    print("\nT elegida para cada partido con los otros seis: {}".format(
        ", ".join("{:g}".format(elegida[p]) for p in dfl.PARTIDOS)))

    print("\n## 2. La anchura de la duda frente al error de cada cambio de `main`\n")
    print("| etiquetas | cambios de `main` | con pareja a ±{} | Spearman anchura–error (con pareja) | AUC: anchura separa los sin pareja | anchura mediana con / sin pareja |".format(CERCA))
    print("|---|---|---|---|---|---|")
    for conv in dfl.CONVENCIONES:
        anchuras, errores, sin_pareja = [], [], []
        for partido in dfl.PARTIDOS:
            d = datos[partido]
            pred = d["viterbis"][25.0]
            T = elegida[partido]
            for (a, b), porT in d["tramos"]:
                p = np.exp(porT[T][1])  # (n, 3)
                reales = cambios_directos(d["gt"][conv], a, b)
                for frame, equipo in cambios_directos(pred, a, b):
                    pn = p[:, equipo]
                    i = frame - a
                    dentro = (pn > DUDA[0]) & (pn < DUDA[1])
                    izq = i
                    while izq > 0 and dentro[izq - 1]:
                        izq -= 1
                    der = i
                    while der < len(pn) - 1 and dentro[der]:
                        der += 1
                    anchura = der - izq
                    cerca = [abs(f - frame) for f, e in reales if e == equipo and abs(f - frame) <= CERCA]
                    if cerca:
                        anchuras.append(anchura)
                        errores.append(min(cerca))
                    else:
                        sin_pareja.append(anchura)
        anchuras, errores, sin_pareja = np.array(anchuras), np.array(errores), np.array(sin_pareja)
        print("| {} | {} | {} | {:.2f} | {:.2f} | {:.0f} / {:.0f} |".format(
            conv, len(anchuras) + len(sin_pareja), len(anchuras), spearman(anchuras, errores),
            auc(sin_pareja, anchuras), np.median(anchuras) if len(anchuras) else float("nan"),
            np.median(sin_pareja) if len(sin_pareja) else float("nan")))

    print("\n## 3. Elegir por parte el Viterbi con más spellF1 esperado\n")
    elecciones = {p: [] for p in dfl.PARTIDOS}
    esperado = {p: [] for p in dfl.PARTIDOS}
    for partido in dfl.PARTIDOS:
        t0 = time.time()
        d = datos[partido]
        T = elegida[partido]
        for (a, b), porT in d["tramos"]:
            muestras = muestrear(porT[T][0], coste, T, MUESTRAS, rng)
            falsa = np.full(len(d["gt"]["flag"]), X, dtype=np.int8)
            medias = {}
            for c in COSTES:
                valores = []
                for k in range(MUESTRAS):
                    falsa[a:b] = muestras[k]
                    valores.append(spell_de_tramo(falsa, d["viterbis"][c], a, b))
                medias[c] = float(np.mean(valores))
            # posesiones por muestra, para ver si la distribución fragmenta
            falsa[a:b] = muestras[0]
            n_muestra = len(pm.possession_spells(falsa, [(a, b)]))
            mejor = max(COSTES, key=lambda c: (medias[c], -abs(c - 25.0)))
            elecciones[partido].append(mejor)
            esperado[partido].append((medias, n_muestra))
        print("muestreado {} en {:.0f} s".format(partido, time.time() - t0), file=sys.stderr, flush=True)

    print("Coste elegido en cada una de las 14 partes: {}".format(
        ", ".join("{:g}".format(c) for p in dfl.PARTIDOS for c in elecciones[p])))
    n_muestras = [m for p in dfl.PARTIDOS for _, m in esperado[p]]
    print("Posesiones en una muestra, por parte: mediana {:.0f} (mín {} – máx {})\n".format(
        np.median(n_muestras), min(n_muestras), max(n_muestras)))
    print("| etiquetas | " + " | ".join("coste {:g}".format(c) for c in COSTES)
          + " | elegido por parte (riesgo mínimo) | mejor por parte (oráculo) |")
    print("|---|" + "---|" * (len(COSTES) + 2))
    for conv in dfl.CONVENCIONES:
        fila = []
        for c in COSTES:
            rec = [puntuar.contar(datos[p]["gt"][conv], datos[p]["viterbis"][c]) for p in dfl.PARTIDOS]
            fila.append("{:.3f}".format(puntuar.spell_f1(*puntuar.juntar(rec))))
        rec_mbr, rec_or = [], []
        for partido in dfl.PARTIDOS:
            d = datos[partido]
            g = d["gt"][conv]
            pred_mbr = np.full(len(g), X, dtype=np.int8)
            pred_or = np.full(len(g), X, dtype=np.int8)
            for k, (a, b) in enumerate(d["blocks"]):
                pred_mbr[a:b] = d["viterbis"][elecciones[partido][k]][a:b]
                mejor = max(COSTES, key=lambda c: spell_de_tramo(g, d["viterbis"][c], a, b))
                pred_or[a:b] = d["viterbis"][mejor][a:b]
            rec_mbr.append(puntuar.contar(g, pred_mbr))
            rec_or.append(puntuar.contar(g, pred_or))
        fila.append("{:.3f}".format(puntuar.spell_f1(*puntuar.juntar(rec_mbr))))
        fila.append("{:.3f}".format(puntuar.spell_f1(*puntuar.juntar(rec_or))))
        print("| {} | {} |".format(conv, " | ".join(fila)))
    print("\nspellF1 esperado frente a las muestras, media de las 14 partes: "
          + ", ".join("coste {:g}: {:.3f}".format(
              c, np.mean([m[c] for p in dfl.PARTIDOS for m, _ in esperado[p]])) for c in COSTES))


if __name__ == "__main__":
    main()
