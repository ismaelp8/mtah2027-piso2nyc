"""¿Aguanta B5 con la convención de eventos de Metrica? Mide el pipeline en sus 3 partidos abiertos.

    python validation/metrica/medir.py [--partidos 1 2 3] [--bootstrap 1000]

Datos abiertos de otros partidos (ver `lector.py`): lo puede ejecutar cualquiera, Claude incluido. Solo
imprime agregados. Las versiones, las condiciones y la regla de lectura están fijadas en `BITACORA.md`
§4–§6 antes de medir. B5 y `dead_state` van con los coeficientes de la entrega: nunca han visto estos
partidos.
"""

import argparse
import collections
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "harness"))
sys.path.insert(0, str(AQUI.parent / "scripts"))
sys.path.insert(0, str(AQUI.parents[1]))
import lector as lc  # noqa: E402
import perfil_etiquetas as pe  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import candidates, io, pipeline  # noqa: E402
from starter.baseline import team_of_each_track  # noqa: E402

H, A, D, X = lc.H, lc.A, lc.D, lc.X
VERSIONES = ("control: voto ±50", "N1, coste 25", "main (B5, coste 25)")
MODOS = ("oraculo", "propio")
UMBRAL = 0.03


def ejecutar(version, trk, gt, modo):
    if version.startswith("control"):
        codes = puntuar.control(trk, 50)
        return puntuar.imponer_d(codes, gt, trk.blocks) if modo == "oraculo" else codes
    extra = [puntuar.d_oraculo(gt)] if modo == "oraculo" else []
    piezas = {"candidates": candidates.evidence} if version.startswith("N1") else None
    return pipeline.run(trk, extra=extra, pieces=piezas)


def descripcion_balon(trk, gt):
    hay = ~np.isnan(np.asarray(trk.bx))
    muerto, vivo = gt == D, (gt == H) | (gt == A)
    return np.array([muerto.sum(), (muerto & hay).sum(), vivo.sum(), (vivo & hay).sum()], dtype=np.int64)


def fila(recuentos, referencias, n_draws):
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


def gana(datos, candidato, referencia, minimo):
    """True si, en cada condición que vota, la diferencia cumple la regla con el `D` oráculo."""
    for cond in lc.VOTAN:
        f = datos[("oraculo", cond)][candidato]["frente"][referencia]
        if not (f["dif"] >= UMBRAL and f["intervalo"] and f["intervalo"][0] > 0 and f["gana"] >= minimo):
            return False
    return True


def informe_io():
    """¿Lee `possession/io.py` el juego 3? Solo recuentos. El partido del reto no se toca."""
    base = lc.carpeta() / "data" / "Sample_Game_3"
    raw = base / "Sample_Game_3_tracking.txt"
    meta = base / "Sample_Game_3_metadata.xml"
    if not raw.is_file():
        print("\n### Lector del ATD sobre el juego 3\n\n- no está bajado")
        return
    n = sum(1 for _ in open(raw, encoding="utf-8"))
    counts = {}
    io.load_ball(raw, n, lc.PITCH, counts=counts)
    px, _ = io.load_players(raw, n, lc.PITCH)
    slots_meta = len(team_of_each_track(meta))
    print("\n### Lector del ATD sobre el juego 3 (descriptivo)\n")
    print("- líneas: {} · válidas: {} · vacías: {} · mal formadas: {} · fuera de rango: {} · repetidas: {} · frames sin línea: {}".format(
        counts["lineas"], counts["validas"], counts["vacias"], counts["mal_formadas"],
        counts["fuera_de_rango"], counts["repetidas"], counts["frames_sin_linea"]))
    print("- slots en el tracking: {} · jugadores en los metadatos: {}".format(px.shape[1], slots_meta))
    print("- `from_files` no llega a montar el partido: los metadatos listan un jugador por ficha (titulares y suplentes) y el tracking trae un slot por quien está en el campo")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--partidos", nargs="+", type=int, default=None)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    ids = args.partidos or lc.partidos()
    if not ids:
        sys.exit("No hay partidos de Metrica bajados, en {}".format(lc.carpeta()))

    recuentos = collections.defaultdict(list)
    balon = collections.defaultdict(lambda: np.zeros(4, dtype=np.int64))
    etiquetas_todas, sep = [], np.full(10, X, dtype=np.int8)
    for id_ in ids:
        t0 = time.time()
        crudo = lc.leer(id_)
        for cond in lc.CONDICIONES:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            trk = puntuar.solo_lectura(trk)
            balon[cond] += descripcion_balon(trk, gt)
            if cond == lc.CONDICIONES[0]:
                etiquetas_todas += [gt, sep]
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
    print("\n### Las etiquetas (eventos de Metrica: toque con impacto)\n")
    print("- posesiones: {} · {:.2f} por minuto vivo · frames `D`: {:.1f} %".format(
        n_pos, n_pos / max(vivos, 1e-9), 100.0 * np.mean(todas[todas != X] == D)))
    print("- huella de retrasos 1 / 3 / 8 / 25 frames: " + " / ".join("{:.4f}".format(huella[d]) for d in (1, 3, 8, 25)))
    print("  (DFL flag 0,5522 · oficial 0,6539 · DFL control 0,8082 a 25 frames; descriptivo, y la tabla oficial sigue en D21)")
    print("\n| condición | ¿vota? | balón visible en los frames vivos | balón visible en los `D` |")
    print("|---|---|---|---|")
    for cond in lc.CONDICIONES:
        m, mb, v, vb = balon[cond]
        print("| {} | {} | {:.1f} % | {:.1f} % |".format(
            cond, "sí" if cond in lc.VOTAN else "no", 100.0 * vb / max(v, 1), 100.0 * mb / max(m, 1)))

    datos = {}
    for modo in MODOS:
        print("\n### `D` {}{}\n".format(modo, " (decide)" if modo == "oraculo" else " (descriptivo)"))
        print("| balón | versión | spellF1, {} partidos | por partido, mín–máx | frente al control [5–95 %] · gana en | frente a N1 [5–95 %] · gana en | posesiones predichas / reales |".format(len(ids)))
        print("|---|---|---|---|---|---|---|")
        for cond in lc.CONDICIONES:
            ref = {"control": recuentos[(modo, cond, VERSIONES[0])], "N1": recuentos[(modo, cond, VERSIONES[1])]}
            datos[(modo, cond)] = {}
            for version in VERSIONES:
                refs = {k: v for k, v in ref.items() if not version.startswith(k)}
                f = fila(recuentos[(modo, cond, version)], refs, args.bootstrap)
                datos[(modo, cond)][version] = f

                def celda(nombre, actual=f):
                    if nombre not in actual["frente"]:
                        return "–"
                    g = actual["frente"][nombre]
                    i = g["intervalo"]
                    if not i:
                        return "{:+.3f} · {} de {}".format(g["dif"], g["gana"], len(ids))
                    return "{:+.3f} [{:+.3f} a {:+.3f}] · {} de {}".format(g["dif"], i[0], i[1], g["gana"], len(ids))

                print("| {}{} | {} | {:.3f} | {:.3f}–{:.3f} | {} | {} | {} / {} |".format(
                    cond, "" if cond in lc.VOTAN else " (sin voto)", version, f["spell"], f["min"], f["max"],
                    celda("control"), celda("N1"), f["pred"], f["reales"]))

    print("\n### Regla de BITACORA.md §6 (`D` oráculo, condición que vota: {})\n".format(", ".join(lc.VOTAN)))
    print("- «B5 aguanta con la convención de Metrica» (main frente al control, en 3 de 3): **{}**".format(
        "sí" if gana(datos, VERSIONES[2], "control", len(ids)) else "no"))
    print("- «La ventaja sobre N1 aguanta» (main frente a N1, en 2 de 3 o más): **{}**".format(
        "sí" if gana(datos, VERSIONES[2], "N1", max(1, len(ids) - 1)) else "no"))
    print("- (descriptivo) N1 frente al control, en 3 de 3: **{}**".format(
        "sí" if gana(datos, VERSIONES[1], "control", len(ids)) else "no"))
    print("  Gana: +{:.2f} o más con los partidos juntos y con el intervalo por encima de cero.".format(UMBRAL))
    print("  Con 3 partidos esto no sustituye al harness de la DFL ni a SkillCorner.")
    informe_io()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
