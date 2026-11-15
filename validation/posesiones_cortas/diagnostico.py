"""Posesiones cortas: ¿convención o modelo?, y ¿cuánto margen da B5 dentro de cada posesión real? Descriptivo.

    python validation/posesiones_cortas/diagnostico.py
    python validation/posesiones_cortas/diagnostico.py --sin-skillcorner

Datos abiertos de otros partidos: los 7 de la Bundesliga (Bassek et al., 2025, CC BY 4.0) y la mitad de
entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`; A-League 2024/25, licencia MIT). Nada del partido: lo
puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. Unos 3 minutos.

**Es descriptivo: no decide nada** (BITACORA.md §2). Usa el pipeline de `main` como el harness: el `D` de las
etiquetas (oráculo) y, en la DFL, B5 con los coeficientes que no vieron cada partido.

1. **Convención o modelo** (DFL):
   - las etiquetas de una convención puntuadas como si fueran una predicción contra las de la otra: es el
     techo de un método perfecto en una convención si la GT fuera la otra;
   - las posesiones del flag partidas en dos: las que también son una posesión del control (IoU ≥ 0,5) y
     las que solo existen en el flag (un toque del rival sin control). Cuántas de cada una encuentra `main`.
2. **Margen de B5 dentro de cada posesión real** (DFL y SkillCorner). Con el `D` oráculo, el decodificador
   solo mira la diferencia `H` − `A`. Para el equipo bueno, en cada frame:
   `m = α·z·s + (N1 bueno) − (N1 malo)`, con `s` = +1 si el equipo bueno es `H` y −1 si es `A`.
   - `S`: la suma de `m` en la posesión; `mejor`: la suma del mejor trozo seguido (lo que el decodificador
     puede coger);
   - `coste`: lo que cuesta meter esa posesión con el decodificador de `main`: 25 por cada lado pegado al
     otro equipo (un lado pegado a un `D` o al borde no cuesta nada de más);
   - de qué partes de B5 sale `m`: N1 y el logit por grupos de rasgos (balón en ventanas de 1, 13, 51 y
     151 frames, y los de los jugadores).
"""

import argparse
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
from possession import aprendida, pipeline, temporal, tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
FPS = 25
COSTE = temporal.DEFAULTS["switch"]
TRAMOS = de.TRAMOS
CONDICION_SK = "detectado"
GRUPOS = ("N1", "balón v1", "balón v13", "balón v51", "balón v151", "jugadores")


def grupo_de_rasgo(j):
    """Grupo de la columna j de los rasgos de B2 (B5): 5 rasgos base del balón × 4 ventanas, y 10 de forma."""
    n_balon = len(aprendida.BASE_BALON) * len(aprendida.VENTANAS_BALON)
    if j < n_balon:
        return "balón v{}".format(aprendida.VENTANAS_BALON[j % len(aprendida.VENTANAS_BALON)])
    return "jugadores"


def desglose_b5(trk, fuera):
    """(m por frame a favor de H, {grupo: contribución por frame a favor de H}, visible) de B5 tal cual.

    Comprueba que la suma de los grupos es la diferencia H − A de `aprendida.evidence_b5`.
    """
    limpio = pipeline.default_piece("ball")(trk)
    juego = aprendida.coeficientes("b5", fuera)
    rasgos = aprendida.rasgos(limpio, "b5")
    alfa = juego["alfa"]
    partes = collections.OrderedDict((g, np.zeros(len(trk.bx))) for g in GRUPOS)
    for j, peso in enumerate(juego["pesos"]):
        partes[grupo_de_rasgo(j)] += alfa * float(peso) * rasgos[:, j]
    cercano = aprendida.equipo_mas_cercano(limpio)
    dentro = np.zeros(len(trk.bx), bool)
    for a, b in trk.blocks:
        dentro[a:b] = True
    cercano = np.where(dentro, cercano, -1)
    partes["N1"] = (cercano == H).astype(float) - (cercano == A).astype(float)
    score, _ = aprendida.evidence_b5(limpio, fuera=fuera)
    m = score[:, H] - score[:, A]
    suma = sum(partes.values())
    # El redondeo de `puntuacion_de` (DECIMALES) deja diferencias de 1e-6 por frame.
    if np.max(np.abs((suma - m)[dentro])) > 1e-4:
        raise AssertionError("el desglose de B5 no suma su evidencia: {}".format(np.max(np.abs(suma - m))))
    return m, partes, aprendida.balon_visible(limpio)


def mejor_trozo(valores):
    """La suma del mejor trozo seguido (Kadane); 0 si todos son negativos."""
    mejor = actual = 0.0
    for v in valores:
        actual = max(0.0, actual + v)
        mejor = max(mejor, actual)
    return mejor


def lados_rivales(gt, a, b, runs):
    """Cuántos lados de la posesión [a, b) están pegados a una posesión del otro equipo (0, 1 o 2)."""
    inicio, fin = next((r for r in runs if r[0] <= a < r[1]))
    lados = 0
    if a > inicio and gt[a - 1] in (H, A) and gt[a - 1] != gt[a]:
        lados += 1
    if b < fin and gt[b] in (H, A) and gt[b] != gt[a]:
        lados += 1
    return lados


def nuevo_margen():
    return collections.defaultdict(list)


def margen_de_un_partido(gt, pred, m, partes, visible, acc):
    """Añade a `acc` una fila por posesión real: duración, encontrada, lados, S, mejor y contribuciones."""
    runs = pm.valid_runs(gt)
    reales = pm.possession_spells(gt, runs)
    predichas = pm.possession_spells(pm.fill_abstentions(pred, runs), runs)
    real_ok, _ = de.emparejar(reales, predichas)
    lleno = pm.fill_abstentions(pred, runs)
    for (a, b, equipo), ok in zip(reales, real_ok):
        s = 1.0 if equipo == H else -1.0
        mm = s * m[a:b]
        clave = (de.tramo(b - a), bool(ok))
        acc[clave].append({
            "L": b - a, "lados": lados_rivales(gt, a, b, runs), "S": float(mm.sum()), "mejor": mejor_trozo(mm),
            "partes": {g: float(s * partes[g][a:b].sum()) for g in GRUPOS},
            "visible": float(np.mean(visible[a:b])),
            "n1_bien": int(np.sum(s * partes["N1"][a:b] > 0)), "n1_mal": int(np.sum(s * partes["N1"][a:b] < 0)),
            "z_bien": int(np.sum(mm - s * partes["N1"][a:b] > 0)),
            "causa": None if ok else de.causa_real((a, b, equipo), lleno, predichas),
        })


def imprimir_margen(titulo, acc):
    print("\n### {}\n".format(titulo))
    print("Una fila por duración real y si `main` la encuentra (IoU ≥ 0,5). `S/coste`: la suma de `m` en la "
          "posesión dividida por lo que cuesta meterla (25 por lado pegado al otro equipo); solo las que tienen "
          "algún lado así. «paga»: `S` > coste. «el mejor trozo paga»: hay un trozo seguido con suma > coste.\n")
    print("| duración | ¿la encuentra? | posesiones | con 2 lados rivales | S/coste, mediana | paga | el mejor trozo "
          "paga | m por frame, media | N1 bien / mal por frame | z a favor por frame | balón visible |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, _, nombre in TRAMOS:
        for ok in (True, False):
            filas = acc.get((nombre, ok), [])
            if not filas:
                continue
            con_coste = [f for f in filas if f["lados"]]
            cociente = [f["S"] / (COSTE * f["lados"]) for f in con_coste]
            paga = [f["S"] > COSTE * f["lados"] for f in con_coste]
            trozo = [f["mejor"] > COSTE * f["lados"] for f in con_coste]
            frames = sum(f["L"] for f in filas)
            print("| {} | {} | {} | {:.0f} % | {} | {} | {} | {:+.2f} | {:.0f} % / {:.0f} % | {:.0f} % | {:.0f} % |".format(
                nombre, "sí" if ok else "no", len(filas), 100.0 * np.mean([f["lados"] == 2 for f in filas]),
                "{:+.2f}".format(np.median(cociente)) if cociente else "–",
                "{:.0f} %".format(100.0 * np.mean(paga)) if paga else "–",
                "{:.0f} %".format(100.0 * np.mean(trozo)) if trozo else "–",
                sum(f["S"] for f in filas) / frames,
                100.0 * sum(f["n1_bien"] for f in filas) / frames, 100.0 * sum(f["n1_mal"] for f in filas) / frames,
                100.0 * sum(f["z_bien"] for f in filas) / frames, 100.0 * sum(f["visible"] * f["L"] for f in filas) / frames
            ).replace(".", ","))
    print("\nDe dónde sale `m` (media por frame, a favor del equipo bueno), por grupo de B5:\n")
    print("| duración | ¿la encuentra? | " + " | ".join(GRUPOS) + " | total |")
    print("|---|---|" + "---|" * (len(GRUPOS) + 1))
    for _, _, nombre in TRAMOS:
        for ok in (True, False):
            filas = acc.get((nombre, ok), [])
            if not filas:
                continue
            frames = sum(f["L"] for f in filas)
            celdas = [sum(f["partes"][g] for f in filas) / frames for g in GRUPOS]
            print("| {} | {} | {} | {:+.2f} |".format(nombre, "sí" if ok else "no", " | ".join(
                "{:+.2f}".format(c) for c in celdas), sum(celdas)).replace(".", ","))
    perdidas = [f for k, filas in acc.items() if not k[1] for f in filas]
    if perdidas:
        causas = collections.Counter(f["causa"] for f in perdidas)
        print("\nDe las {} no encontradas: {}.".format(len(perdidas), "; ".join(
            "{} {:.0f} %".format(c, 100.0 * n / len(perdidas)) for c, n in causas.most_common())))
        for causa in ("otro equipo", "la nuestra es más larga"):
            sub = [f for f in perdidas if f["causa"] == causa and f["lados"]]
            if sub:
                print("- «{}»: {} con algún lado rival; paga el {:.0f} %, el mejor trozo paga el {:.0f} %; S/coste "
                      "mediana {:+.2f}.".format(causa, len(sub), 100.0 * np.mean([f["S"] > COSTE * f["lados"] for f in sub]),
                                               100.0 * np.mean([f["mejor"] > COSTE * f["lados"] for f in sub]),
                                               np.median([f["S"] / (COSTE * f["lados"]) for f in sub])).replace(".", ","))


# -- 1. convención o modelo --------------------------------------------------------------------------------

def convencion_o_modelo(partidos_dfl, preds):
    """Techos cruzados entre convenciones y las posesiones del flag que también son del control."""
    print("\n## 1. ¿Convención o modelo? (DFL, «{}», `D` de las etiquetas)\n".format(dfl.VOTAN[0]))
    cruzado = collections.defaultdict(list)
    por_minuto = collections.Counter()
    tabla = collections.Counter()
    for cargado, _ in partidos_dfl:
        gt = cargado["gt"]
        pred = preds[cargado["partido"]]
        for c_pred in dfl.CONVENCIONES:
            for c_gt in dfl.CONVENCIONES:
                if c_pred != c_gt:
                    cruzado[(c_pred, c_gt)].append(puntuar.contar(gt[c_gt], gt[c_pred]))
        for c in dfl.CONVENCIONES:
            runs = pm.valid_runs(gt[c])
            por_minuto[c] += len(pm.possession_spells(gt[c], runs))
            cruzado[("main", c)].append(puntuar.contar(gt[c], pred))
        runs = pm.valid_runs(gt["flag"])
        por_minuto["main"] += len(pm.possession_spells(pm.fill_abstentions(pred, runs), runs))
        por_minuto["minutos vivos"] += float(np.sum(np.isin(gt["flag"], (H, A)))) / FPS / 60.0
        flag = pm.possession_spells(gt["flag"], runs)
        control = pm.possession_spells(gt["control"], pm.valid_runs(gt["control"]))
        en_control, _ = de.emparejar(flag, control)
        nuestras = pm.possession_spells(pm.fill_abstentions(pred, runs), runs)
        encontrada, _ = de.emparejar(flag, nuestras)
        for (a, b, _), ctl, ok in zip(flag, en_control, encontrada):
            tabla[(de.tramo(b - a), bool(ctl), bool(ok))] += 1
    print("Posesiones por minuto vivo: flag {:.2f}, control {:.2f}, `main` {:.2f}.\n".format(
        por_minuto["flag"] / por_minuto["minutos vivos"], por_minuto["control"] / por_minuto["minutos vivos"],
        por_minuto["main"] / por_minuto["minutos vivos"]).replace(".", ","))
    print("| predicción | GT | spellF1 | posesiones predichas / reales |")
    print("|---|---|---|---|")
    for (p, g), recuentos in sorted(cruzado.items()):
        flags, n_pred = puntuar.juntar(recuentos)
        print("| {} | {} | {:.3f} | {} / {} |".format(
            "etiquetas «{}»".format(p) if p != "main" else "`main`", g, puntuar.spell_f1(flags, n_pred), n_pred,
            flags.shape[1]).replace(".", ","))
    print("\nLas posesiones del flag, partidas en dos: las que también son una posesión del control (IoU ≥ 0,5) y "
          "las que solo existen en el flag. «encontrada»: `main` la encuentra con IoU ≥ 0,5.\n")
    print("| duración (flag) | también en control | encontradas | solo en el flag | encontradas |")
    print("|---|---|---|---|---|")
    total = collections.Counter()
    for _, _, nombre in TRAMOS:
        ctl = tabla[(nombre, True, True)] + tabla[(nombre, True, False)]
        solo = tabla[(nombre, False, True)] + tabla[(nombre, False, False)]
        total.update({"ctl": ctl, "ctl_ok": tabla[(nombre, True, True)], "solo": solo,
                      "solo_ok": tabla[(nombre, False, True)]})
        print("| {} | {} | {} | {} | {} |".format(nombre, ctl, de.pct(tabla[(nombre, True, True)], ctl), solo,
                                                 de.pct(tabla[(nombre, False, True)], solo)))
    print("| **todas** | {} | {} | {} | {} |".format(total["ctl"], de.pct(total["ctl_ok"], total["ctl"]), total["solo"],
                                                    de.pct(total["solo_ok"], total["solo"])))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sin-skillcorner", action="store_true")
    args = parser.parse_args()
    print("# Posesiones cortas: convención o modelo, y margen de B5 (descriptivo)\n")
    print("Pipeline de `main` (B5, coste {:g}) con el `D` de las etiquetas. Duraciones a 25 fps.".format(COSTE))

    partidos_dfl, preds, desgloses = [], {}, {}
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        trk = puntuar.solo_lectura(dfl.tracking_de(cargado, dfl.VOTAN[0]))
        partidos_dfl.append((cargado, trk))
        piezas = {"candidates": functools.partial(aprendida.evidence_b5, fuera=partido)}
        preds[partido] = pipeline.run(trk, extra=[puntuar.d_oraculo(cargado["gt"]["flag"])], pieces=piezas)
        desgloses[partido] = desglose_b5(trk, partido)
        print("cargado {}".format(partido), file=sys.stderr, flush=True)

    convencion_o_modelo(partidos_dfl, preds)

    print("\n## 2. Margen de B5 dentro de cada posesión real")
    for conv in dfl.CONVENCIONES:
        acc = nuevo_margen()
        for cargado, _ in partidos_dfl:
            m, partes, visible = desgloses[cargado["partido"]]
            margen_de_un_partido(cargado["gt"][conv], preds[cargado["partido"]], m, partes, visible, acc)
        imprimir_margen("DFL, «{}», etiquetas «{}»".format(dfl.VOTAN[0], conv), acc)

    if not args.sin_skillcorner:
        import lector as lc
        ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
        lc.exigir_solo_entrenamiento(ids)
        acc = nuevo_margen()
        for id_ in ids:
            trk, gt = lc.tracking_de(lc.leer_crudo(id_), CONDICION_SK, id_)
            trk = puntuar.solo_lectura(trk)
            pred = pipeline.run(trk, extra=[puntuar.d_oraculo(gt)])
            m, partes, visible = desglose_b5(trk, None)
            margen_de_un_partido(gt, pred, m, partes, visible, acc)
            print("hecho {}".format(id_), file=sys.stderr, flush=True)
        imprimir_margen("SkillCorner, `lector.ENTRENAMIENTO` ({} partidos), «{}»".format(len(ids), CONDICION_SK), acc)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
