"""Sondeo S1 en SkillCorner: el coste de cambio que más conviene, con el `D` de las etiquetas y con el propio.

    python validation/investigacion_1116/costes_skillcorner.py

Datos abiertos de otros partidos (mitad de entrenamiento de SkillCorner, licencia MIT): lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. La regla de lectura está en BITACORA.md (S1), escrita
antes de ejecutar. Descriptivo: no decide nada.
"""

import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "skillcorner"))
sys.path.insert(0, str(AQUI.parent / "harness"))
import lector as lc  # noqa: E402
import puntuar  # noqa: E402
from possession import pipeline  # noqa: E402

COSTES = (6.0, 12.0, 18.0, 25.0, 40.0)
MODOS = ("oraculo", "propio")


def main():
    ids = list(lc.ENTRENAMIENTO)
    lc.exigir_solo_entrenamiento(ids)
    recuentos = {}
    for id_ in ids:
        t0 = time.time()
        crudo = lc.leer_crudo(id_)
        for cond in lc.VOTAN:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            trk = puntuar.solo_lectura(trk)
            for modo in MODOS:
                extra = [puntuar.d_oraculo(gt)] if modo == "oraculo" else []
                for coste in COSTES:
                    pred = pipeline.run(trk, extra=extra, params={"switch": coste})
                    recuentos.setdefault((modo, cond, coste), []).append(puntuar.contar(gt, pred))
        print("hecho {} en {:.0f} s".format(id_, time.time() - t0), file=sys.stderr, flush=True)
    print("SkillCorner, {} partidos de entrenamiento. spellF1 juntos (posesiones predichas / reales)".format(len(ids)))
    print()
    print("| `D` | balón | " + " | ".join("coste {:g}".format(c) for c in COSTES) + " |")
    print("|---|---|" + "---|" * len(COSTES))
    for modo in MODOS:
        for cond in lc.VOTAN:
            celdas = []
            for coste in COSTES:
                flags, n_pred = puntuar.juntar(recuentos[(modo, cond, coste)])
                celdas.append("{:.3f} ({} / {})".format(puntuar.spell_f1(flags, n_pred), n_pred, flags.shape[1]))
            print("| {} | {} | {} |".format(modo, cond, " | ".join(celdas)))


if __name__ == "__main__":
    main()
