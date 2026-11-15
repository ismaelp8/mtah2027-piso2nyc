"""Fase 2: las posesiones que sobran, cuánto vale cada tipo de fallo y el retraso del balón. Descriptivo.

    python validation/posesiones_cortas/fase2.py
    python validation/posesiones_cortas/fase2.py --sin-skillcorner

Datos abiertos: la DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de SkillCorner
(`lector.ENTRENAMIENTO`; A-League 2024/25, licencia MIT). Lo puede ejecutar cualquiera, Claude incluido. Solo
agregados. **No decide nada** (BITACORA.md §9). Pipeline de `main` (B5, coste 25); en la DFL, B5 con los
coeficientes que no vieron cada partido.

1. **Las que sobran** (posesiones nuestras sin pareja a IoU ≥ 0,5), con el `D` de las etiquetas. Clase:
   - «inventada»: en la mayor parte de sus frames las etiquetas dan el otro equipo y no hay ninguna posesión
     real de su equipo a `CERCA` frames o menos;
   - «cambio real desplazado»: lo mismo, pero sí hay una posesión real de su equipo a `CERCA` frames o menos;
   - «trozo de una real partida»: las etiquetas dan su equipo, y la real es más larga (otra cosa la parte);
   - «fundida»: las etiquetas dan su equipo, y la nuestra es más larga que la real.

   De cada clase: duración, qué grupo de B5 empuja a su favor (el margen por frame de `diagnostico.py`), si
   está pegada a un `D` real, cuánto le falta el balón y a qué distancia está el cambio real más cercano.
2. **Cuánto vale cada tipo de fallo:** se ponen como en las etiquetas solo los frames de un tipo de fallo y se
   vuelve a puntuar (sin volver a decodificar). Tipos de equipo, con el `D` oráculo y con el propio: las
   posesiones reales que no encontramos porque decimos el otro equipo (por duración) y las nuestras que
   sobran por «inventada» o por «cambio real desplazado». Tipos de `D`, con el propio: los bordes de las
   paradas que vemos, las paradas falsas (un `D` nuestro sin ningún `D` real) y las paradas que no vemos.
3. **El balón con retraso** (DFL, `D` oráculo): `main` con el balón 0, 6, 12 y 25 frames tarde, las dos
   convenciones y las dos condiciones que votan. No es la medida del retraso del ATD (la hace Antonio): dice
   cuánto costaría.
"""

import argparse
import collections
import functools
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                 os.path.join(ROOT, "validation", "scripts"), os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import diagnostico as dg  # noqa: E402
import diagnostico_errores as de  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline, tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
CERCA = 50
HUECO_LARGO = 25
RETRASOS = (0, 6, 12, 25)
CLASES = ("inventada", "cambio real desplazado", "trozo de una real partida", "fundida", "cae en un D")
DUR = ((0, 50, "< 2 s"), (50, 125, "2–5 s"), (125, 250, "5–10 s"), (250, 10 ** 9, "≥ 10 s"))
TIPOS_EQUIPO = ("faltan, decimos el otro equipo, < 2 s", "faltan, decimos el otro equipo, 2–10 s",
                "faltan, decimos el otro equipo, ≥ 10 s", "sobran, inventadas", "sobran, cambio real desplazado")
TIPOS_D = ("bordes de las paradas que vemos", "paradas falsas", "paradas que no vemos")


def dur(n):
    return next(nombre for a, b, nombre in DUR if a <= n < b)


def rachas(mascara):
    bordes = np.diff(np.concatenate(([0], np.asarray(mascara, dtype=np.int8), [0])))
    return list(zip(np.flatnonzero(bordes == 1).tolist(), np.flatnonzero(bordes == -1).tolist()))


def clase_sobrante(nuestra, gt, reales_por_equipo):
    a, b, equipo = nuestra
    if np.mean(gt[a:b] == D) >= 0.5:
        return "cae en un D"  # solo con el `D` propio; no entra en los tipos de equipo
    if np.mean(gt[a:b] == equipo) >= 0.5:
        mejor = de.mejor_solape(nuestra, [r for r in reales_por_equipo[equipo]])
        return "fundida" if mejor is not None and (b - a) > (mejor[1] - mejor[0]) else "trozo de una real partida"
    cerca = any(r[0] < b + CERCA and r[1] > a - CERCA for r in reales_por_equipo[equipo])
    return "cambio real desplazado" if cerca else "inventada"


def sobrantes(gt, pred, m, partes, visible, acc):
    """Añade a `acc` una fila por posesión nuestra sin pareja. Devuelve {clase: frames} para el punto 2."""
    runs = pm.valid_runs(gt)
    lleno = pm.fill_abstentions(pred, runs)
    reales = pm.possession_spells(gt, runs)
    nuestras = pm.possession_spells(lleno, runs)
    _, pred_ok = de.emparejar(reales, nuestras)
    por_equipo = {H: [r for r in reales if r[2] == H], A: [r for r in reales if r[2] == A]}
    cambios = np.array([t[0] for t in pm.transitions(gt, runs) if t[2] in (H, A)], dtype=np.int64)
    sin_balon = ~visible
    frames = collections.defaultdict(list)
    for (a, b, equipo), ok in zip(nuestras, pred_ok):
        if ok:
            continue
        clase = clase_sobrante((a, b, equipo), gt, por_equipo)
        frames[clase].append((a, b))
        s = 1.0 if equipo == H else -1.0
        huecos = rachas(sin_balon[a:b])
        acc[clase].append({
            "L": b - a, "partes": {g: float(s * partes[g][a:b].sum()) for g in dg.GRUPOS},
            "junto_a_D": bool((a > 0 and gt[a - 1] == D) or (b < len(gt) and gt[b] == D)),
            "sin_balon": float(np.mean(sin_balon[a:b])),
            "hueco_largo": any(e - s0 >= HUECO_LARGO for s0, e in huecos),
            "cambio": int(np.min(np.abs(cambios - a))) if len(cambios) else 10 ** 9,
        })
    return frames, nuestras


def imprimir_sobrantes(titulo, acc):
    total = sum(len(v) for v in acc.values())
    print("\n### {}\n".format(titulo))
    print("Posesiones nuestras sin pareja: {}. «cambio real a ≤ 25»: un cambio real (a `H` o `A`) a 25 frames o menos "
          "del inicio de la nuestra.\n".format(total))
    print("| clase | cuántas | " + " | ".join(n for _, _, n in DUR) + " | pegada a un `D` real | sin balón (media) | con un "
          "hueco de balón de ≥ 1 s | cambio real a ≤ 25 frames |")
    print("|---|---|" + "---|" * len(DUR) + "---|---|---|---|")
    for clase in CLASES:
        filas = acc.get(clase, [])
        if not filas:
            continue
        n = len(filas)
        por_dur = collections.Counter(dur(f["L"]) for f in filas)
        print("| {} | {} ({:.0f} %) | {} | {:.0f} % | {:.0f} % | {:.0f} % | {:.0f} % |".format(
            clase, n, 100.0 * n / total, " | ".join("{:.0f} %".format(100.0 * por_dur[d] / n) for _, _, d in DUR),
            100.0 * np.mean([f["junto_a_D"] for f in filas]), 100.0 * np.mean([f["sin_balon"] for f in filas]),
            100.0 * np.mean([f["hueco_largo"] for f in filas]), 100.0 * np.mean([f["cambio"] <= 25 for f in filas])
        ).replace(".", ","))
    print("\nQué empuja a favor del equipo de la nuestra (margen medio por frame, por grupo de B5):\n")
    print("| clase | " + " | ".join(dg.GRUPOS) + " | total |")
    print("|---|" + "---|" * (len(dg.GRUPOS) + 1))
    for clase in CLASES:
        filas = acc.get(clase, [])
        if not filas:
            continue
        frames = sum(f["L"] for f in filas)
        celdas = [sum(f["partes"][g] for f in filas) / frames for g in dg.GRUPOS]
        print("| {} | {} | {:+.2f} |".format(clase, " | ".join("{:+.2f}".format(c) for c in celdas),
                                            sum(celdas)).replace(".", ","))


# -- 2. cuánto vale cada tipo de fallo --------------------------------------------------------------------

def con_oraculo(pred, gt, tramos):
    out = pred.copy()
    for a, b in tramos:
        out[a:b] = gt[a:b]
    return out


def tramos_de_tipo(gt, pred, frames_sobran):
    """{tipo: [(a, b)]} con los frames de cada tipo de fallo de equipo."""
    runs = pm.valid_runs(gt)
    lleno = pm.fill_abstentions(pred, runs)
    reales = pm.possession_spells(gt, runs)
    nuestras = pm.possession_spells(lleno, runs)
    real_ok, _ = de.emparejar(reales, nuestras)
    tipos = collections.defaultdict(list)
    for (a, b, equipo), ok in zip(reales, real_ok):
        if ok or de.causa_real((a, b, equipo), lleno, nuestras) != "otro equipo":
            continue
        n = b - a
        tipo = TIPOS_EQUIPO[0] if n < 50 else TIPOS_EQUIPO[1] if n < 250 else TIPOS_EQUIPO[2]
        tipos[tipo].append((a, b))
    tipos[TIPOS_EQUIPO[3]] = frames_sobran.get("inventada", [])
    tipos[TIPOS_EQUIPO[4]] = frames_sobran.get("cambio real desplazado", [])
    return tipos


def tramos_de_d(gt, pred):
    """{tipo: [(a, b)]} con los frames de cada tipo de fallo de `D` (con el `D` propio)."""
    tipos = collections.defaultdict(list)
    for inicio, fin in pm.valid_runs(gt):
        g, p = gt[inicio:fin], pred[inicio:fin]
        for s, e in rachas(p == D):  # paradas falsas: un D nuestro sin ningún D real dentro
            if not np.any(g[s:e] == D):
                tipos[TIPOS_D[1]].append((inicio + s, inicio + e))
        for s, e in rachas(g == D):  # paradas que no vemos: un D real sin ningún D nuestro
            if not np.any(p[s:e] == D):
                tipos[TIPOS_D[2]].append((inicio + s, inicio + e))
    return tipos


def valor(acc, clave, gt, pred, tipos, base_d=None):
    acc[(clave, "base")].append(puntuar.contar(gt, pred))
    for tipo, tramos in tipos.items():
        acc[(clave, tipo)].append(puntuar.contar(gt, con_oraculo(pred, gt, tramos)))
    if base_d is not None:
        corregida, _ = de.corregir_bordes(gt, pred, True, True)
        acc[(clave, TIPOS_D[0])].append(puntuar.contar(gt, corregida))


def imprimir_valor(titulo, acc, claves, tipos):
    print("\n### {}\n".format(titulo))
    print("spellF1 si se arregla solo ese tipo de fallo (sus frames como en las etiquetas). La subida no se suma "
          "entre tipos.\n")
    print("| arreglo | " + " | ".join(claves) + " |")
    print("|---|" + "---|" * len(claves) + "")
    def f1(c, t):
        r = acc.get((c, t))
        return puntuar.spell_f1(*puntuar.juntar(r)) if r else None
    print("| ninguno | " + " | ".join("{:.3f}".format(f1(c, "base")) for c in claves).replace(".", ",") + " |")
    for tipo in tipos:
        celdas = []
        for c in claves:
            v = f1(c, tipo)
            celdas.append("–" if v is None else "{:.3f} ({:+.3f})".format(v, v - f1(c, "base")))
        print("| {} | {} |".format(tipo, " | ".join(celdas)).replace(".", ","))


# -- 3. el balón con retraso ------------------------------------------------------------------------------

def retrasar(trk, k):
    if k == 0:
        return trk
    bx, by = np.full(len(trk.bx), np.nan), np.full(len(trk.by), np.nan)
    for a, b in trk.blocks:
        bx[a + k:b] = trk.bx[a:b - k]
        by[a + k:b] = trk.by[a:b - k]
    return trk._replace(bx=bx, by=by)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sin-skillcorner", action="store_true")
    args = parser.parse_args()
    print("# Fase 2: las que sobran, cuánto vale cada fallo y el balón con retraso (descriptivo)")
    sob = {c: collections.defaultdict(list) for c in dfl.CONVENCIONES}
    val = collections.defaultdict(list)
    ret = collections.defaultdict(list)
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        piezas = {"candidates": functools.partial(aprendida.evidence_b5, fuera=partido)}
        for cond in dfl.VOTAN:
            trk = puntuar.solo_lectura(dfl.tracking_de(cargado, cond))
            oraculo = pipeline.run(trk, extra=[puntuar.d_oraculo(gt["flag"])], pieces=piezas)
            propio = pipeline.run(trk, pieces=piezas)
            m, partes, visible = dg.desglose_b5(trk, partido)
            for conv in dfl.CONVENCIONES:
                g = gt[conv]
                destino = sob[conv] if cond == dfl.VOTAN[0] else collections.defaultdict(list)
                frames_o, _ = sobrantes(g, oraculo, m, partes, visible, destino)
                valor(val, (cond, conv, "oráculo"), g, oraculo, tramos_de_tipo(g, oraculo, frames_o))
                frames_p, _ = sobrantes(g, propio, m, partes, visible, collections.defaultdict(list))
                tipos_propio = tramos_de_tipo(g, propio, frames_p)
                tipos_propio.update(tramos_de_d(g, propio))
                valor(val, (cond, conv, "propio"), g, propio, tipos_propio, base_d=True)
            for k in RETRASOS:
                pred = oraculo if k == 0 else pipeline.run(retrasar(trk, k), extra=[puntuar.d_oraculo(gt["flag"])],
                                                           pieces=piezas)
                for conv in dfl.CONVENCIONES:
                    ret[(cond, conv, k)].append(puntuar.contar(gt[conv], pred))
        print("hecho {}".format(partido), file=sys.stderr, flush=True)

    print("\n## 1. Las que sobran (DFL, «{}», `D` oráculo)".format(dfl.VOTAN[0]))
    for conv in dfl.CONVENCIONES:
        imprimir_sobrantes("Etiquetas «{}»".format(conv), sob[conv])

    print("\n## 2. Cuánto vale cada tipo de fallo (DFL)")
    for modo in ("oráculo", "propio"):
        claves = ["{}, {}".format(c, k) for k in dfl.VOTAN for c in dfl.CONVENCIONES]
        acc = {("{}, {}".format(k[1], k[0]), t): v for (k, t), v in val.items() if k[2] == modo}
        imprimir_valor("`D` {}".format(modo), acc, claves, TIPOS_EQUIPO + (TIPOS_D if modo == "propio" else ()))

    print("\n## 3. `main` con el balón tarde (DFL, `D` oráculo; descriptivo)\n")
    print("| balón | etiquetas | " + " | ".join("{} frames".format(k) for k in RETRASOS) + " |")
    print("|---|---|" + "---|" * len(RETRASOS))
    for cond in dfl.VOTAN:
        for conv in dfl.CONVENCIONES:
            f = [puntuar.spell_f1(*puntuar.juntar(ret[(cond, conv, k)])) for k in RETRASOS]
            print("| {} | {} | {} |".format(cond, conv, " | ".join(
                "{:.3f}".format(v) if i == 0 else "{:.3f} ({:+.3f})".format(v, v - f[0]) for i, v in enumerate(f))
            ).replace(".", ","))

    if args.sin_skillcorner:
        return
    import lector as lc
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    sob_sk = collections.defaultdict(list)
    val_sk = collections.defaultdict(list)
    for id_ in ids:
        trk, gt = lc.tracking_de(lc.leer_crudo(id_), "detectado", id_)
        trk = puntuar.solo_lectura(trk)
        pred = pipeline.run(trk, extra=[puntuar.d_oraculo(gt)])
        frames_sobran, _ = sobrantes(gt, pred, *dg.desglose_b5(trk, None), sob_sk)
        valor(val_sk, "SkillCorner", gt, pred, tramos_de_tipo(gt, pred, frames_sobran))
        print("hecho {}".format(id_), file=sys.stderr, flush=True)
    print("\n## SkillCorner, `lector.ENTRENAMIENTO` ({} partidos), «detectado», `D` oráculo".format(len(ids)))
    imprimir_sobrantes("Las que sobran", sob_sk)
    imprimir_valor("Cuánto vale cada tipo de fallo", val_sk, ["SkillCorner"], TIPOS_EQUIPO)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
