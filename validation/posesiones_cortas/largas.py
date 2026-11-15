"""Fase 2: las posesiones de 2 a 5, de 5 a 10 y de 10 s o más que no encontramos. ¿Por qué? Descriptivo.

    python validation/posesiones_cortas/largas.py

Datos abiertos de otros partidos: la DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de
SkillCorner (`lector.ENTRENAMIENTO`; A-League 2024/25, licencia MIT). Lo puede ejecutar cualquiera, Claude
incluido. Solo agregados. **No decide nada** (BITACORA.md §8).

Pipeline de `main` (B5, coste 25). En la DFL, con el `D` de las etiquetas (oráculo) y con el `D` propio (las
piezas de `D` de `main`; con el balón tapado en los `D` de la DFL, que delata la etiqueta: no decide); en
SkillCorner, solo con el oráculo.

Por cada posesión real no encontrada (IoU < 0,5 con el emparejamiento del scorer oficial) se prueban
arreglos locales, sin tocar el resto del partido, y se mira si la posesión nuestra del mismo equipo que mejor
la solapa llega a IoU ≥ 0,5:

- **vecina:** las posesiones reales pegadas a ella (la anterior y la siguiente) que son del otro equipo se
  ponen como en las etiquetas;
- **borde con un `D`:** si a un lado tiene un `D` real, ese `D` entero se pone como `D`, y los frames de `D`
  nuestro pegados a ese borde, dentro de la posesión, pasan a su equipo;
- **`D` dentro:** los trozos de `D` nuestro dentro de la posesión que no tocan sus bordes pasan a su equipo.

Causa, la primera que vale:
1. **emparejamiento:** ya llega a IoU ≥ 0,5 sin arreglar nada (otra posesión real se quedó la nuestra);
2. **una vecina del otro equipo** (solo con el arreglo «vecina»);
3. **el borde con un `D`**;
4. **un `D` nuestro dentro**;
5. **varias a la vez:** solo con los tres arreglos juntos;
6. **el resto:** ni con los tres. Se parte en «decimos el otro equipo» (más de la mitad de sus frames) y
   «otra cosa».

Con el `D` oráculo, 3 y 4 no pueden salir: el `D` nuestro es el de las etiquetas. Con el flag se dice además
cuántas existen también con el control (IoU ≥ 0,5 con una posesión del control), y al revés.
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
import diagnostico_errores as de  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline, tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
TRAMOS = (("2–5 s", 50, 125), ("5–10 s", 125, 250), ("≥ 10 s", 250, 10 ** 9))
CAUSAS = ("emparejamiento", "una vecina del otro equipo", "el borde con un D", "un D nuestro dentro",
          "varias a la vez", "el resto: decimos el otro equipo", "el resto: otra cosa")


def tramo(n):
    for nombre, a, b in TRAMOS:
        if a <= n < b:
            return nombre
    return None


def mejor_iou(lab, a, b, equipo, inicio, fin):
    """El mayor IoU de [a, b) con una racha de `equipo` en lab[inicio:fin]."""
    seg = lab[inicio:fin] == equipo
    bordes = np.diff(np.concatenate(([0], seg.astype(np.int8), [0])))
    s, e = np.flatnonzero(bordes == 1), np.flatnonzero(bordes == -1)
    aa, bb = a - inicio, b - inicio
    sel = (s < bb) & (e > aa)
    if not sel.any():
        return 0.0
    s, e = s[sel], e[sel]
    return float(((np.minimum(e, bb) - np.maximum(s, aa)) / (np.maximum(e, bb) - np.minimum(s, aa))).max())


def vecinos(por_fin, por_inicio, a, b):
    """(segmento anterior, segmento siguiente) de las etiquetas, o None, dentro del mismo tramo."""
    return por_fin.get(a), por_inicio.get(b)


def arreglar(lab, a, b, equipo, antes, despues, que):
    out = lab.copy()
    if "vecina" in que:
        for s in (antes, despues):
            if s is not None and s[2] in (H, A) and s[2] != equipo:
                out[s[0]:s[1]] = s[2]
    if "borde" in que:
        if antes is not None and antes[2] == D:
            out[antes[0]:antes[1]] = D
            k = a
            while k < b and out[k] == D:
                out[k] = equipo
                k += 1
        if despues is not None and despues[2] == D:
            out[despues[0]:despues[1]] = D
            k = b - 1
            while k >= a and out[k] == D:
                out[k] = equipo
                k -= 1
    if "dentro" in que:
        r = out[a:b]
        es_d = np.concatenate(([0], (r == D).astype(np.int8), [0]))
        bordes = np.diff(es_d)
        for s, e in zip(np.flatnonzero(bordes == 1), np.flatnonzero(bordes == -1)):
            if s > 0 and e < len(r):
                r[s:e] = equipo
    return out


def analizar(gt, pred, acc, otra=None):
    """Añade a `acc` la causa de cada posesión real no encontrada de 2 s o más. `otra`: las etiquetas de la
    otra convención (para decir si la posesión existe con las dos)."""
    runs = pm.valid_runs(gt)
    lab = pm.fill_abstentions(pred, runs)
    reales = pm.possession_spells(gt, runs)
    real_ok, _ = de.emparejar(reales, pm.possession_spells(lab, runs))
    en_otra = None
    if otra is not None:
        en_otra, _ = de.emparejar(reales, pm.possession_spells(otra, pm.valid_runs(otra)))
    segmentos = pm.segments(gt, runs)  # los tramos están separados por un hueco: ningún borde se repite
    por_fin, por_inicio = {s[1]: s for s in segmentos}, {s[0]: s for s in segmentos}
    for k, ((a, b, equipo), ok) in enumerate(zip(reales, real_ok)):
        nombre = tramo(b - a)
        if nombre is None:
            continue
        clave = (nombre, None if en_otra is None else bool(en_otra[k]))
        acc[("reales",) + clave] += 1
        if ok:
            continue
        inicio, fin = next(r for r in runs if r[0] <= a < r[1])
        antes, despues = vecinos(por_fin, por_inicio, a, b)
        def vale(que):
            return mejor_iou(arreglar(lab, a, b, equipo, antes, despues, que), a, b, equipo, inicio, fin) >= 0.5
        if mejor_iou(lab, a, b, equipo, inicio, fin) >= 0.5:
            causa = CAUSAS[0]
        elif vale(("vecina",)):
            causa = CAUSAS[1]
            largos = [s[1] - s[0] for s in (antes, despues) if s is not None and s[2] in (H, A) and s[2] != equipo]
            acc[("vecina corta",) + clave] += int(min(largos) < 50)
        elif vale(("borde",)):
            causa = CAUSAS[2]
        elif vale(("dentro",)):
            causa = CAUSAS[3]
        elif vale(("vecina", "borde", "dentro")):
            causa = CAUSAS[4]
        elif np.mean(lab[a:b] == 1 - equipo) > 0.5:
            causa = CAUSAS[5]
        else:
            causa = CAUSAS[6]
        acc[(causa,) + clave] += 1


def imprimir(titulo, acc, con_otra, nombre_otra=None):
    print("\n### {}\n".format(titulo))
    grupos = [None] if not con_otra else [True, False, "todas"]
    print("| duración real | {}reales | no encontradas | {} | de las de «vecina», con la vecina de menos de 2 s |".format(
        "¿existe con {}? | ".format(nombre_otra) if con_otra else "", " | ".join(CAUSAS)))
    print("|---|" + ("---|" if con_otra else "") + "---|---|" + "---|" * len(CAUSAS) + "---|")
    for nombre, _, _ in TRAMOS:
        for g in grupos:
            claves = [(nombre, x) for x in ((True, False) if g == "todas" else (g,))]
            def n(c):
                return sum(acc[(c,) + cl] for cl in claves)
            perdidas = sum(n(c) for c in CAUSAS)
            reales = n("reales")
            celdas = ["{:.0f} %".format(100.0 * n(c) / perdidas) if perdidas else "–" for c in CAUSAS]
            vec = n(CAUSAS[1])
            etiqueta = {True: "sí", False: "no", "todas": "todas", None: ""}[g]
            print("| {} | {}{} | {} ({:.0f} %) | {} | {} |".format(
                nombre, etiqueta + " | " if con_otra else "", reales, perdidas, 100.0 * perdidas / max(reales, 1),
                " | ".join(celdas), "{:.0f} %".format(100.0 * n("vecina corta") / vec) if vec else "–"))


def main():
    print("# Fase 2: por qué no encontramos las posesiones de 2 s o más (descriptivo)")
    print("\nPipeline de `main` (B5, coste 25). Causa: el primer arreglo local que basta para llegar a IoU ≥ 0,5 "
          "(ver el docstring). Porcentajes sobre las no encontradas de cada fila.")
    acc = collections.defaultdict(lambda: collections.Counter())
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        trk = puntuar.solo_lectura(dfl.tracking_de(cargado, dfl.VOTAN[0]))
        piezas = {"candidates": functools.partial(aprendida.evidence_b5, fuera=partido)}
        preds = {"oráculo": pipeline.run(trk, extra=[puntuar.d_oraculo(gt["flag"])], pieces=piezas),
                 "propio": pipeline.run(trk, pieces=piezas)}
        for modo, pred in preds.items():
            for conv in dfl.CONVENCIONES:
                otra = gt["control" if conv == "flag" else "flag"]
                analizar(gt[conv], pred, acc[(conv, modo)], otra)
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    for modo in ("oráculo", "propio"):
        for conv in dfl.CONVENCIONES:
            otra = "control" if conv == "flag" else "flag"
            imprimir("DFL, «{}», etiquetas «{}», `D` {}".format(dfl.VOTAN[0], conv, modo), acc[(conv, modo)], True,
                     "el {}".format(otra))
    import lector as lc
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    acc_sk = collections.Counter()
    for id_ in ids:
        trk, gt = lc.tracking_de(lc.leer_crudo(id_), "detectado", id_)
        pred = pipeline.run(puntuar.solo_lectura(trk), extra=[puntuar.d_oraculo(gt)])
        analizar(gt, pred, acc_sk)
        print("hecho {}".format(id_), file=sys.stderr, flush=True)
    imprimir("SkillCorner, `lector.ENTRENAMIENTO` ({} partidos), «detectado», `D` oráculo".format(len(ids)), acc_sk,
             False)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
