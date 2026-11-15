"""¿Cuenta la GT los toques sin control? Posesiones cortas entre dos del otro equipo, por convención. Solo agregados.

    python validation/posesiones_cortas/sandwiches.py                 # las referencias (DFL y SkillCorner)
    python validation/posesiones_cortas/sandwiches.py --gt-publica    # además, la GT pública y la regla

Datos abiertos (la DFL, Bassek et al., 2025, CC BY 4.0, y la mitad de entrenamiento de SkillCorner) y, con
`--gt-publica`, los 5 minutos de GT pública (`evaluation/gt/`), que Claude sí puede leer. Nada del partido. La
regla está en BITACORA.md §15, con commit antes de mirar la GT pública.

**La estadística:** un «sándwich» es una posesión (`H` o `A`) de menos de `CORTA` frames cuyas posesiones
vecinas, la de antes y la de después, son las dos del otro equipo, sin un `D` en medio. Separa las convenciones:
un toque del rival sin control da un sándwich con el flag y no con el control. Las posesiones cortas en general
no sirven, porque un saque rápido es corto con cualquier etiqueta. Las que corta el borde de una ventana no
cuentan: les falta una vecina.

**Las referencias,** en ventanas de `VENTANA` frames seguidos (lo que dura la ventana pública) desde el inicio de
cada parte, sin solaparse: sándwiches por minuto de juego en cada ventana con 2 minutos de juego o más. Con el
flag y el control de la DFL y con las etiquetas de SkillCorner.
"""

import argparse
import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                 os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import possession_metrics as pm  # noqa: E402

H, A, D, X = 0, 1, 2, 3
FPS = 25
VENTANA = 7500
CORTA = 50  # frames: el sándwich de la regla dura menos de 2 s
DESCRIPTIVAS = (25, 125)  # menos de 1 s y menos de 5 s: solo se enseñan
MINIMO_JUEGO = 2.0  # minutos de juego para que una ventana cuente
CUANTILES = (10, 25, 50, 75, 90)
CUENTA_TOQUES = 3  # sándwiches en la ventana pública: con 3 o más, «cuenta toques»; con 0, «exige control»
GT_PUBLICA = os.path.join(ROOT, "evaluation", "gt", "BAR-ATH_possession_gt_public.csv")


def sandwiches(codes, inicio, fin, corta):
    """Cuántos sándwiches de menos de `corta` frames hay en codes[inicio:fin], con las dos vecinas dentro."""
    segs = pm.segments(codes, [(inicio, fin)])
    n = 0
    for i in range(1, len(segs) - 1):
        a, b, k = segs[i]
        antes, despues = segs[i - 1][2], segs[i + 1][2]
        if k in (H, A) and antes in (H, A) and despues in (H, A) and antes == despues != k and b - a < corta:
            n += 1
    return n


def minutos_de_juego(codes, inicio, fin):
    return float(np.sum(np.isin(codes[inicio:fin], (H, A)))) / FPS / 60.0


def ventanas(codes):
    """[(inicio, fin)] de VENTANA frames desde el inicio de cada tramo válido, sin solaparse."""
    salida = []
    for a, b in pm.valid_runs(codes):
        t = a
        while t + VENTANA <= b:
            salida.append((t, t + VENTANA))
            t += VENTANA
    return salida


def por_ventana(codes, acc):
    for a, b in ventanas(codes):
        minutos = minutos_de_juego(codes, a, b)
        if minutos < MINIMO_JUEGO:
            continue
        acc["ritmos"].append(sandwiches(codes, a, b, CORTA) / minutos)
        for c in DESCRIPTIVAS:
            acc["ritmos_{}".format(c)].append(sandwiches(codes, a, b, c) / minutos)
        acc["k"] += sandwiches(codes, a, b, CORTA)
        acc["minutos"] += minutos


def referencias():
    import dfl
    import lector as lc
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for fuente in ("flag", "control", "SkillCorner"):
        acc[fuente]["k"] = 0
        acc[fuente]["minutos"] = 0.0
    for partido in dfl.PARTIDOS:
        gt = dfl.cargar(partido)["gt"]
        for conv in dfl.CONVENCIONES:
            por_ventana(gt[conv], acc[conv])
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    for id_ in ids:
        _, gt = lc.tracking_de(lc.leer_crudo(id_), "detectado", id_)
        por_ventana(gt, acc["SkillCorner"])
        print("hecho {}".format(id_), file=sys.stderr, flush=True)
    return acc


def coma(x, cifras=2):
    return "{:.{}f}".format(x, cifras).replace(".", ",")


def imprimir_referencias(acc):
    print("Sándwiches por minuto de juego en ventanas de {} frames (≥ {:g} min de juego).\n".format(VENTANA, MINIMO_JUEGO))
    print("| etiquetas | ventanas | todas juntas | " + " | ".join("p{}".format(q) for q in CUANTILES) +
          " | < 1 s, mediana | < 5 s, mediana |")
    print("|---|---|---|" + "---|" * len(CUANTILES) + "---|---|")
    cuantiles = {}
    for fuente in ("flag", "control", "SkillCorner"):
        r = np.array(acc[fuente]["ritmos"])
        cuantiles[fuente] = {q: float(np.percentile(r, q)) for q in CUANTILES}
        print("| {} | {} | {} | {} | {} | {} |".format(
            fuente, len(r), coma(acc[fuente]["k"] / acc[fuente]["minutos"]),
            " | ".join(coma(cuantiles[fuente][q]) for q in CUANTILES),
            coma(np.median(acc[fuente]["ritmos_25"])), coma(np.median(acc[fuente]["ritmos_125"]))))
    return cuantiles


def gt_publica(cuantiles):
    codes = pm.label_codes(pm.read_label_csv(GT_PUBLICA))
    runs = pm.valid_runs(codes)
    k = sum(sandwiches(codes, a, b, CORTA) for a, b in runs)
    k_desc = {c: sum(sandwiches(codes, a, b, c) for a, b in runs) for c in DESCRIPTIVAS}
    minutos = sum(minutos_de_juego(codes, a, b) for a, b in runs)
    r = k / minutos
    print("\n## GT pública\n")
    print("Sándwiches de menos de 2 s: {} en {} minutos de juego: {} por minuto. (Menos de 1 s: {}; menos de 5 s: {}.)".format(
        k, coma(minutos), coma(r), k_desc[25], k_desc[125]))
    print("\n## Regla de BITACORA.md §15 (en recuentos de la ventana pública)\n")
    print("Referencias de esta ejecución: flag p10 {} y p25 {}; control p90 {}; SkillCorner mediana {}.".format(
        coma(cuantiles["flag"][10]), coma(cuantiles["flag"][25]), coma(cuantiles["control"][90]),
        coma(cuantiles["SkillCorner"][50])))
    if k == 0:
        print("\n**k = 0: la GT exige control** (se parece al control).")
    elif k >= CUENTA_TOQUES:
        print("\n**k = {}: la GT cuenta los toques sin control** (se parece al flag o a SkillCorner, no al "
              "control).".format(k))
    else:
        print("\n**k = {}: no concluye.**".format(k))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gt-publica", action="store_true", help="además, la GT pública y la regla de BITACORA.md §15")
    args = ap.parse_args()
    print("# ¿Cuenta la GT los toques sin control? Sándwiches de menos de 2 s (BITACORA.md §15)\n")
    cuantiles = imprimir_referencias(referencias())
    if args.gt_publica:
        gt_publica(cuantiles)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
