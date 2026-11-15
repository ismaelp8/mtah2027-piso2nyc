"""¿Por qué fallamos? Diagnóstico descriptivo de los errores del pipeline, en datos abiertos. Solo agregados.

    python validation/scripts/diagnostico_errores.py
    python validation/scripts/diagnostico_errores.py --sin-skillcorner

Datos abiertos de otros partidos: los 7 de la Bundesliga (Bassek et al., 2025, CC BY 4.0) y los de SkillCorner
(A-League 2024/25, licencia MIT; `validation/skillcorner/`). Nada del partido: lo puede ejecutar cualquiera,
Claude incluido. Tarda unos 5 minutos.

**Es descriptivo: no decide nada.** Sirve para saber dónde se pierde la nota y repartir el trabajo. Usa las
funciones del scorer oficial (`evaluation/possession_metrics.py`) para emparejar posesiones y cambios.

**SkillCorner está partido en dos** (`validation/skillcorner/BITACORA.md` §8): este script solo analiza
`lector.ENTRENAMIENTO` y se niega a leer `lector.EXAMEN`, que queda intacto. Si una idea sale de aquí, se
comprueba en el examen.

Qué mide, con el pipeline de `main`. En la DFL, B5 puntúa cada partido con los coeficientes que no lo han
visto, como en el harness; en SkillCorner, con los de la entrega, que nunca han visto esos partidos:

1. **Cada posesión real que no encontramos** (IoU < 0,5), con una sola causa:
   - `otro equipo`: en la mayor parte de sus frames decimos el otro equipo (no cambiamos);
   - `la nuestra es más larga`: decimos el equipo bueno, pero nuestra posesión se funde con lo de al lado;
   - `la nuestra es más corta o va partida`: decimos el equipo bueno, pero a trozos o solo en parte;
   - `la tapamos con D` (solo con el `D` propio).
2. **Cada posesión nuestra que sobra,** con una sola causa, del mismo modo.
3. **Los cambios directos de equipo** (`H` a `A` o al revés): cuántos reales tienen un cambio nuestro al
   mismo equipo a ±12, ±25 y ±50 frames, frente a un placebo (nuestros cambios desplazados 60 s), y el
   retraso con signo de los que caen a ±25 frames. Positivo es tarde.
4. **Qué borde del `D` cuesta más** (solo en la DFL, con el `D` propio): se corrige con la verdad el inicio
   de las paradas detectadas, o el final, o los dos, y se vuelve a puntuar. El `D` de SkillCorner no se
   analiza: son sobre todo repeticiones sin tracking.
"""

import argparse
import collections
import functools
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, os.path.join(ROOT, "validation", "skillcorner"))
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline, tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
FPS = 25
UMBRAL = 0.5
TOLERANCIA_CAMBIO = 50  # frames: hasta dónde se busca nuestro cambio alrededor del real
PLACEBO = 60 * FPS  # frames: los mismos cambios nuestros, desplazados 60 s dentro de cada parte
TRAMOS = ((0, 25, "< 1 s"), (25, 50, "1–2 s"), (50, 125, "2–5 s"), (125, 250, "5–10 s"), (250, 10 ** 9, "≥ 10 s"))
CONDICION_DFL = "como el ATD"
CONDICION_SK = "detectado"

CAUSAS_REALES = ("otro equipo", "la nuestra es más larga", "la nuestra es más corta o va partida",
                 "la tapamos con D")
CAUSAS_NUESTRAS = ("otro equipo", "más larga que la real", "más corta que la real", "cae en D")


def piezas_dfl(partido):
    """Como el harness: en la DFL, B5 puntúa cada partido con los coeficientes que no lo han visto."""
    return {"candidates": functools.partial(aprendida.evidence_b5, fuera=partido)}


def tramo(frames):
    for a, b, nombre in TRAMOS:
        if a <= frames < b:
            return nombre
    raise ValueError(frames)


def emparejar(reales, predichas):
    """(real emparejada, predicha emparejada) a IoU ≥ UMBRAL, con el mismo voraz que el scorer oficial."""
    solapes = pm.spell_overlaps(reales, predichas)
    real_ok = np.zeros(len(reales), dtype=bool)
    pred_ok = np.zeros(len(predichas), dtype=bool)
    for iou, i, j in solapes:
        if iou < UMBRAL:
            break
        if real_ok[i] or pred_ok[j]:
            continue
        real_ok[i] = pred_ok[j] = True
    oficial = pm.matched_gt_flags(solapes, len(reales), UMBRAL)
    if not np.array_equal(real_ok, oficial):
        raise AssertionError("el emparejamiento no coincide con el del scorer oficial")
    return real_ok, pred_ok


def mejor_solape(tramo_ref, otras):
    """La posesión de `otras` del mismo equipo que más frames comparte con `tramo_ref`, o None."""
    a, b, equipo = tramo_ref
    mejor, comun = None, 0
    for c, d, e in otras:
        if e != equipo or d <= a or b <= c:
            continue
        n = min(b, d) - max(a, c)
        if n > comun:
            mejor, comun = (c, d, e), n
    return mejor


def causa_real(real, pred, predichas):
    a, b, equipo = real
    dentro = pred[a:b]
    if np.mean(dentro == D) >= 0.5:
        return "la tapamos con D"
    if np.mean(dentro == equipo) < 0.5:
        return "otro equipo"
    mejor = mejor_solape(real, predichas)
    if mejor is not None and (mejor[1] - mejor[0]) > (b - a):
        return "la nuestra es más larga"
    return "la nuestra es más corta o va partida"


def causa_nuestra(nuestra, gt, reales):
    a, b, equipo = nuestra
    dentro = gt[a:b]
    if np.mean(dentro == D) >= 0.5:
        return "cae en D"
    if np.mean(dentro == equipo) < 0.5:
        return "otro equipo"
    mejor = mejor_solape(nuestra, reales)
    if mejor is not None and (b - a) > (mejor[1] - mejor[0]):
        return "más larga que la real"
    return "más corta que la real"


def cambios_directos(codes, runs):
    return [t for t in pm.transitions(codes, runs) if t[1] in (H, A) and t[2] in (H, A)]


def desplazar(cambios, runs, frames):
    """Los mismos cambios, `frames` más tarde dentro de su parte, dando la vuelta al llegar al final."""
    out = []
    for t, de, a in cambios:
        for inicio, fin in runs:
            if inicio <= t < fin:
                out.append((inicio + (t - inicio + frames) % (fin - inicio), de, a))
                break
    return sorted(out)


def analizar(gt, pred, acumulado):
    """Añade a `acumulado` las cuentas de un partido."""
    runs = pm.valid_runs(gt)
    lleno = pm.fill_abstentions(pred, runs)
    reales = pm.possession_spells(gt, runs)
    predichas = pm.possession_spells(lleno, runs)
    real_ok, pred_ok = emparejar(reales, predichas)
    for real, ok in zip(reales, real_ok):
        dur = tramo(real[1] - real[0])
        acumulado["reales"][dur] += 1
        if ok:
            acumulado["encontradas"][dur] += 1
        else:
            acumulado["causa_real"][(dur, causa_real(real, lleno, predichas))] += 1
    acumulado["predichas"] += len(predichas)
    for nuestra, ok in zip(predichas, pred_ok):
        if not ok:
            acumulado["causa_nuestra"][causa_nuestra(nuestra, gt, reales)] += 1
    reales_c, nuestros_c = cambios_directos(gt, runs), cambios_directos(lleno, runs)
    parejas, _, _ = pm.match_transitions(reales_c, nuestros_c, TOLERANCIA_CAMBIO, typed="to")
    acumulado["cambios_reales"] += len(reales_c)
    acumulado["cambios_nuestros"] += len(nuestros_c)
    acumulado["retrasos"] += [p[0] - r[0] for r, p in parejas]
    falsas, _, _ = pm.match_transitions(reales_c, desplazar(nuestros_c, runs, PLACEBO), TOLERANCIA_CAMBIO,
                                        typed="to")
    acumulado["retrasos_placebo"] += [p[0] - r[0] for r, p in falsas]
    acumulado["recuentos"].append(puntuar.contar(gt, pred))


def nuevo():
    return {"reales": collections.Counter(), "encontradas": collections.Counter(),
            "causa_real": collections.Counter(), "causa_nuestra": collections.Counter(), "predichas": 0,
            "cambios_reales": 0, "cambios_nuestros": 0, "retrasos": [], "retrasos_placebo": [],
            "recuentos": []}


def pct(a, b):
    return "{:.0f} %".format(100.0 * a / b) if b else "–"


def imprimir(titulo, acc, causas_reales):
    spell = puntuar.spell_f1(*puntuar.juntar(acc["recuentos"]))
    total = sum(acc["reales"].values())
    halladas = sum(acc["encontradas"].values())
    print("\n### {}\n".format(titulo))
    print("spellF1 {:.3f} · posesiones reales {} · nuestras {} · encontradas con IoU ≥ 0,5: {} ({})\n".format(
        spell, total, acc["predichas"], halladas, pct(halladas, total)))
    print("| duración real | reales | encontradas | " + " | ".join(causas_reales) + " |")
    print("|---|---|---|" + "---|" * len(causas_reales))
    for _, _, nombre in TRAMOS:
        n = acc["reales"][nombre]
        celdas = [pct(acc["causa_real"][(nombre, c)], n) for c in causas_reales]
        print("| {} | {} | {} | {} |".format(nombre, n, pct(acc["encontradas"][nombre], n), " | ".join(celdas)))
    perdidas = total - halladas
    celdas = [pct(sum(acc["causa_real"][(t[2], c)] for t in TRAMOS), perdidas) for c in causas_reales]
    print("| **de las {} no encontradas** | | | {} |".format(perdidas, " | ".join(celdas)))
    sobran = sum(acc["causa_nuestra"].values())
    print("\nPosesiones nuestras que sobran: {} de {} ({}). Por causa: {}.".format(
        sobran, acc["predichas"], pct(sobran, acc["predichas"]),
        "; ".join("{} {}".format(c, pct(acc["causa_nuestra"][c], sobran)) for c in CAUSAS_NUESTRAS
                  if acc["causa_nuestra"][c])))
    r = np.array(acc["retrasos"], dtype=float)
    f = np.array(acc["retrasos_placebo"], dtype=float)
    n = acc["cambios_reales"]
    if n:
        def dentro(valores, margen):
            return pct(int(np.sum(np.abs(valores) <= margen)), n)
        print("\nCambios directos de equipo: {} reales y {} nuestros.\n".format(n, acc["cambios_nuestros"]))
        print("| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |")
        print("|---|---|---|---|")
        print("| nuestros cambios | {} | {} | {} |".format(dentro(r, 12), dentro(r, 25), dentro(r, 50)))
        print("| placebo: los mismos, desplazados 60 s | {} | {} | {} |".format(
            dentro(f, 12), dentro(f, 25), dentro(f, 50)))
        cerca = r[np.abs(r) <= 25]
        if len(cerca):
            print("\nRetraso con signo de los que caen a ±25 frames (positivo es tarde): mediana {:+.0f}, "
                  "p25 {:+.0f}, p75 {:+.0f}; {} parejas.".format(
                      np.median(cerca), np.percentile(cerca, 25), np.percentile(cerca, 75), len(cerca)))


# -- qué borde del D cuesta más ---------------------------------------------------------------------------

def rachas(mascara):
    bordes = np.diff(np.concatenate(([0], np.asarray(mascara, dtype=np.int8), [0])))
    return list(zip(np.flatnonzero(bordes == 1).tolist(), np.flatnonzero(bordes == -1).tolist()))


def corregir_bordes(gt, pred, inicio, fin):
    """Copia de `pred` con el inicio y/o el final de cada parada real **detectada** puesto donde dice `gt`.

    Detectada: hay algún frame nuestro de `D` dentro de la parada real. Solo se tocan los frames pegados a
    ese borde: el `D` nuestro que se adelanta o se alarga fuera de la parada pasa al equipo que decíamos al
    otro lado, y el juego nuestro al principio o al final de la parada pasa a `D`. Las paradas que no vemos
    y las que inventamos se quedan como están.
    """
    out = pred.copy()
    detectadas = 0
    for a, b in pm.valid_runs(gt):
        g, p = gt[a:b], out[a:b]
        original = pred[a:b]
        reales = rachas(g == D)
        for k, (s, e) in enumerate(reales):
            nuestro = np.flatnonzero(original[s:e] == D)
            if len(nuestro) == 0:
                continue
            detectadas += 1
            primero, ultimo = s + int(nuestro[0]), s + int(nuestro[-1]) + 1
            anterior = reales[k - 1][1] if k else 0
            siguiente = reales[k + 1][0] if k + 1 < len(reales) else len(g)
            if inicio:
                p[s:primero] = D
                c = s
                while c > anterior and original[c - 1] == D:
                    c -= 1
                if c < s:
                    p[c:s] = original[c - 1] if c > 0 and original[c - 1] in (H, A) else g[s - 1]
            if fin:
                p[ultimo:e] = D
                d = e
                while d < siguiente and original[d] == D:
                    d += 1
                if d > e:
                    p[e:d] = original[d] if d < len(g) and original[d] in (H, A) else g[e]
    return out, detectadas


def bordes_del_d(partidos_dfl):
    print("\n## 4. Qué borde del `D` cuesta más (DFL, «{}», con el `D` propio)\n".format(CONDICION_DFL))
    variantes = (("`D` propio, tal cual", False, False), ("+ inicio de las paradas detectadas, el real", True, False),
                 ("+ final de las paradas detectadas, el real", False, True),
                 ("+ los dos bordes, los reales", True, True))
    filas = collections.defaultdict(lambda: collections.defaultdict(list))
    paradas = collections.Counter()
    for cargado, trk in partidos_dfl:
        piezas = piezas_dfl(cargado["partido"])
        propio = pipeline.run(trk, pieces=piezas)
        for conv in dfl.CONVENCIONES:
            gt = cargado["gt"][conv]
            oraculo = pipeline.run(trk, extra=[puntuar.d_oraculo(gt)], pieces=piezas)
            for nombre, ini, fin in variantes:
                pred, detectadas = corregir_bordes(gt, propio, ini, fin)
                filas[nombre][conv].append(puntuar.contar(gt, pred))
                if conv == dfl.CONVENCIONES[0] and not (ini or fin):
                    paradas["detectadas"] += detectadas
                    paradas["reales"] += sum(len(rachas(gt[a:b] == D)) for a, b in pm.valid_runs(gt))
            filas["`D` de las etiquetas (oráculo)"][conv].append(puntuar.contar(gt, oraculo))
    print("Paradas reales: {} · con algún frame nuestro de `D` dentro: {} ({}). Es un criterio más laxo que el "
          "de la pieza de estado, que pide cubrir la mitad de la parada.\n".format(
        paradas["reales"], paradas["detectadas"], pct(paradas["detectadas"], paradas["reales"])))
    print("| versión | " + " | ".join("spellF1, {}".format(c) for c in dfl.CONVENCIONES) + " |")
    print("|---|" + "---|" * len(dfl.CONVENCIONES))
    for nombre in [v[0] for v in variantes] + ["`D` de las etiquetas (oráculo)"]:
        print("| {} | {} |".format(nombre, " | ".join(
            "{:.3f}".format(puntuar.spell_f1(*puntuar.juntar(filas[nombre][c]))) for c in dfl.CONVENCIONES)))
    print("\nLo que queda entre «los dos bordes» y el oráculo: las paradas que no vemos, las que inventamos y "
          "los huecos de juego que dejamos dentro de una parada detectada.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sin-skillcorner", action="store_true")
    args = parser.parse_args()

    print("# Diagnóstico de errores del pipeline de main (descriptivo)\n")
    print("Posesión encontrada: emparejada con IoU ≥ 0,5 por el scorer oficial. Duraciones a 25 fps.")

    partidos_dfl = []
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        partidos_dfl.append((cargado, puntuar.solo_lectura(dfl.tracking_de(cargado, CONDICION_DFL))))
        print("cargado {}".format(partido), file=sys.stderr, flush=True)

    print("\n## 1–3. DFL, 7 partidos, «{}», con el `D` de las etiquetas".format(CONDICION_DFL))
    for conv in dfl.CONVENCIONES:
        acc = nuevo()
        for cargado, trk in partidos_dfl:
            gt = cargado["gt"][conv]
            analizar(gt, pipeline.run(trk, extra=[puntuar.d_oraculo(gt)], pieces=piezas_dfl(cargado["partido"])), acc)
        imprimir("Etiquetas: {}".format(conv), acc, CAUSAS_REALES[:3])

    if not args.sin_skillcorner:
        import lector as lc
        diagnostico = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
        lc.exigir_solo_entrenamiento(diagnostico)
        examen = lc.EXAMEN
        print("\n## 1–3. SkillCorner, «{}», con el `D` de las etiquetas".format(CONDICION_SK))
        print("\nPartidos para diagnosticar (`lector.ENTRENAMIENTO`): {}. Los otros {} (`lector.EXAMEN`) quedan "
              "intactos, como examen.".format(len(diagnostico), len(examen)))
        acc = nuevo()
        for id_ in diagnostico:
            trk, gt = lc.tracking_de(lc.leer_crudo(id_), CONDICION_SK, id_)
            trk = puntuar.solo_lectura(trk)
            analizar(gt, pipeline.run(trk, extra=[puntuar.d_oraculo(gt)]), acc)
            print("hecho {}".format(id_), file=sys.stderr, flush=True)
        imprimir("Etiquetas de SkillCorner", acc, CAUSAS_REALES[:3])

    bordes_del_d(partidos_dfl)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
