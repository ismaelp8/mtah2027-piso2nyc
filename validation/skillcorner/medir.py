"""¿Aguanta B5 con un tracking automático? Mide el pipeline en los partidos abiertos de SkillCorner.

    python validation/skillcorner/medir.py [--partidos ID ...] [--bootstrap 1000]

Datos abiertos de otros partidos (ver `descargar.py`): lo puede ejecutar cualquiera, Claude incluido. Solo
imprime agregados. Las versiones, las condiciones y la regla de lectura están fijadas en `BITACORA.md` §4–§6
antes de medir. B5 y `dead_state` van con los coeficientes de la entrega: nunca han visto estos partidos.

Reproduce la medida del 15/11, hecha con los 20 partidos antes del corte de `BITACORA.md` §8. No sirve
para entrenar ni para mirar errores: eso solo usa `lector.ENTRENAMIENTO`.
"""

import argparse
import collections
import math
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "harness"))
sys.path.insert(0, str(AQUI.parent / "scripts"))
import lector as lc  # noqa: E402
import perfil_etiquetas as pe  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import candidates, pipeline  # noqa: E402

H, A, D, X = lc.H, lc.A, lc.D, lc.X
VERSIONES = ("control: voto ±50", "N1, coste 25", "main (B5, coste 25)")
MODOS = ("oraculo", "propio")
UMBRAL = 0.03
PROPORCION = 6 / 7  # la de «6 de 7» del harness


def ejecutar(version, trk, gt, modo):
    if version.startswith("control"):
        codes = puntuar.control(trk, 50)
        return puntuar.imponer_d(codes, gt, trk.blocks) if modo == "oraculo" else codes
    extra = [puntuar.d_oraculo(gt)] if modo == "oraculo" else []
    piezas = {"candidates": candidates.evidence} if version.startswith("N1") else None
    return pipeline.run(trk, extra=extra, pieces=piezas)


def descripcion_balon(trk, gt):
    """(frames D, de ellos con balón, frames vivos, de ellos con balón)."""
    hay = ~np.isnan(np.asarray(trk.bx))
    muerto, vivo = gt == D, (gt == H) | (gt == A)
    return np.array([muerto.sum(), (muerto & hay).sum(), vivo.sum(), (vivo & hay).sum()], dtype=np.int64)


def fila(recuentos, referencias, n_draws):
    """spellF1 juntos, por partido, y diferencia frente a cada referencia."""
    f1s = [puntuar.spell_f1(r["flags"], r["n_pred"]) for r in recuentos]
    junto = puntuar.juntar(recuentos)
    out = {"spell": puntuar.spell_f1(*junto), "min": min(f1s), "max": max(f1s), "pred": junto[1],
           "reales": int(junto[0].shape[1]), "frente": {}}
    for nombre, ref in referencias.items():
        f1r = [puntuar.spell_f1(r["flags"], r["n_pred"]) for r in ref]
        jr = puntuar.juntar(ref)
        out["frente"][nombre] = {
            "dif": out["spell"] - puntuar.spell_f1(*jr),
            "intervalo": puntuar.diferencia_bootstrap(junto, jr, n_draws),
            "gana": int(sum(a > b for a, b in zip(f1s, f1r))),
        }
    return out


def minimo_partidos(n_partidos):
    """17 de 20, como dice BITACORA.md §6 (6 de 7 redondeado hacia abajo)."""
    return math.floor(PROPORCION * n_partidos + 1e-9)


def veredicto(datos, cond_votan, modo, candidato, referencia, n_partidos):
    minimo = minimo_partidos(n_partidos)
    for cond in cond_votan:
        f = datos[(modo, cond)][candidato]["frente"][referencia]
        if not (f["dif"] >= UMBRAL and f["intervalo"] and f["intervalo"][0] > 0 and f["gana"] >= minimo):
            return "no"
    return "sí"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--partidos", nargs="+", type=int, default=None)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    ids = args.partidos or lc.partidos()
    if not ids:
        sys.exit("No hay partidos de SkillCorner bajados: python validation/skillcorner/descargar.py")

    recuentos = collections.defaultdict(list)  # (modo, condición, versión) -> por partido
    balon = collections.defaultdict(lambda: np.zeros(4, dtype=np.int64))
    etiquetas_todas, sep = [], np.full(10, X, dtype=np.int8)
    en_bloques = np.zeros(2, dtype=np.int64)  # frames dentro de las partes, de ellos sin etiqueta
    for id_ in ids:
        t0 = time.time()
        crudo = lc.leer_crudo(id_)
        for cond in lc.CONDICIONES:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            trk = puntuar.solo_lectura(trk)
            balon[cond] += descripcion_balon(trk, gt)
            if cond == lc.CONDICIONES[0]:
                etiquetas_todas += [gt, sep]
                for a, b in trk.blocks:
                    en_bloques += (b - a, int(np.sum(gt[a:b] == X)))
            for modo in MODOS:
                for version in VERSIONES:
                    recuentos[(modo, cond, version)].append(puntuar.contar(gt, ejecutar(version, trk, gt, modo)))
        print("hecho {} en {:.0f} s".format(id_, time.time() - t0), file=sys.stderr, flush=True)

    todas = np.concatenate(etiquetas_todas)
    runs = pm.valid_runs(todas)
    n_pos = len(pm.possession_spells(todas, runs))
    vivos = float(np.sum((todas == H) | (todas == A))) / lc.FPS / 60.0
    huella = pe.huella(todas, (1, 3, 8, 25))
    print("partidos: {} · bootstrap: {} · código: pipeline de main, B5 y dead_state con los coeficientes de la entrega".format(
        len(ids), args.bootstrap))
    print("\n### Las etiquetas (convención de SkillCorner)\n")
    print("- posesiones: {} · {:.2f} por minuto vivo · frames `D`: {:.1f} % · frames de las partes sin etiqueta: {:.2f} %".format(
        n_pos, n_pos / vivos, 100.0 * np.mean(todas[todas != X] == D), 100.0 * en_bloques[1] / max(1, en_bloques[0])))
    print("- huella de retrasos 1 / 3 / 8 / 25 frames: " + " / ".join("{:.4f}".format(huella[d]) for d in (1, 3, 8, 25)))
    print("  (DFL flag 0,5522 · oficial 0,6539 · DFL control 0,8082 a 25 frames; descriptivo)")
    print("\n| condición | ¿vota? | balón visible en los frames vivos | balón visible en los `D` |")
    print("|---|---|---|---|")
    for cond in lc.CONDICIONES:
        m, mb, v, vb = balon[cond]
        print("| {} | {} | {:.1f} % | {:.1f} % |".format(cond, "sí" if cond in lc.VOTAN else "no",
                                                      100.0 * vb / max(v, 1), 100.0 * mb / max(m, 1)))

    datos = {}
    for modo in MODOS:
        print("\n### `D` {}{}\n".format(modo, " (decide)" if modo == "oraculo" else " (descriptivo)"))
        print("| balón y jugadores | versión | spellF1, {} partidos | por partido, mín–máx | frente al control [5–95 %] · gana en | frente a N1 [5–95 %] · gana en | posesiones predichas / reales |".format(len(ids)))
        print("|---|---|---|---|---|---|---|")
        for cond in lc.CONDICIONES:
            ref = {"control": recuentos[(modo, cond, VERSIONES[0])], "N1": recuentos[(modo, cond, VERSIONES[1])]}
            datos[(modo, cond)] = {}
            for version in VERSIONES:
                refs = {k: v for k, v in ref.items() if not version.startswith(k)}
                f = fila(recuentos[(modo, cond, version)], refs, args.bootstrap)
                datos[(modo, cond)][version] = f

                def celda(nombre):
                    if nombre not in f["frente"]:
                        return "–"
                    g = f["frente"][nombre]
                    i = g["intervalo"]
                    return "{:+.3f} [{:+.3f} a {:+.3f}] · {} de {}".format(g["dif"], i[0], i[1], g["gana"], len(ids)) if i else \
                        "{:+.3f} · {} de {}".format(g["dif"], g["gana"], len(ids))
                print("| {}{} | {} | {:.3f} | {:.3f}–{:.3f} | {} | {} | {} / {} |".format(
                    cond, "" if cond in lc.VOTAN else " (sin voto)", version, f["spell"], f["min"], f["max"],
                    celda("control"), celda("N1"), f["pred"], f["reales"]))

    print("\n### Regla de BITACORA.md §6 (`D` oráculo, condiciones que votan: {})\n".format(", ".join(lc.VOTAN)))
    print("- «B5 aguanta con tracking automático» (main frente al control): **{}**".format(
        veredicto(datos, lc.VOTAN, "oraculo", VERSIONES[2], "control", len(ids))))
    print("- «La ventaja de B5 sobre N1 aguanta» (main frente a N1): **{}**".format(
        veredicto(datos, lc.VOTAN, "oraculo", VERSIONES[2], "N1", len(ids))))
    print("- (descriptivo) N1 frente al control: **{}**".format(
        veredicto(datos, lc.VOTAN, "oraculo", VERSIONES[1], "control", len(ids))))
    print("  Gana: +{:.2f} o más con los partidos juntos, en {} de {} o más y con el intervalo por encima de cero, "
          "en las dos condiciones que votan.".format(UMBRAL, minimo_partidos(len(ids)), len(ids)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
