"""Sobre la GT pública (permitida): qué pasa con el spellF1 si el equipo es perfecto pero el D no.
Solo lectura de la métrica; imprime agregados."""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import possession_metrics as pm  # noqa: E402

GT_PATH = os.path.join(ROOT, "evaluation", "gt", "BAR-ATH_possession_gt_public.csv")


def main():
    gt = pm.label_codes(pm.read_label_csv(GT_PATH))
    runs = pm.valid_runs(gt)
    dsegs = [(a, b) for a, b, k in pm.segments(gt, runs) if k == pm.D]

    def ev(p):
        r = pm.evaluate(gt, p)
        return "spellF1 {:.3f}   macroF1 {:.3f}   posesiones pred/real {}/{}".format(
            r["spell_f1_mean"], r["macro_f1"], r["n_pred_spells"], r["n_gt_spells"])

    print("GT pública: {} frames puntuados, {} paradas D".format(int(np.sum(gt != pm.X)), len(dsegs)))
    print("  equipo perfecto, D perfecto                      ", ev(gt))
    p = gt.copy()
    for a, b in dsegs:
        p[a:b] = gt[a - 1]
    print("  equipo perfecto, SIN ningún D (hereda el previo) ", ev(p))
    p = gt.copy()
    for a, b in dsegs:
        p[a:b] = gt[b]
    print("  equipo perfecto, SIN D (adelanta el siguiente)   ", ev(p))
    for k in (12, 25, 50, 125):
        p = gt.copy()
        for a, b in dsegs:
            p[a:min(a + k, b)] = gt[a - 1]
        print("  D empieza {:>3} frames tarde                      ".format(k), ev(p))
    for k in (12, 25, 50, 125):
        p = gt.copy()
        for a, b in dsegs:
            p[b:min(b + k, len(p))] = pm.D
        print("  D acaba {:>3} frames tarde                        ".format(k), ev(p))
    for n in (50, 125):
        p = gt.copy()
        for a, b in dsegs:
            if b - a > n:
                p[a + n:b] = gt[a - 1]
        print("  D dura solo {:>3} frames y vuelve al previo        ".format(n), ev(p))
    p = gt.copy()
    for a, b, k in pm.segments(gt, runs):
        if k != pm.D and b - a > 250:
            m = (a + b) // 2
            p[m:m + 50] = pm.D
    print("  D inventado de 2 s en cada posesión de >10 s     ", ev(p))


if __name__ == "__main__":
    main()
