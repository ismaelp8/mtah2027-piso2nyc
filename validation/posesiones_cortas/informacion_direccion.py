"""¿Dice la dirección en que se mueve el balón quién lo tiene? Sondeo descriptivo, solo agregados.

    python validation/posesiones_cortas/informacion_direccion.py

DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`).
Lo puede ejecutar cualquiera, Claude incluido. **No decide nada** (BITACORA.md §6).

B5 usa dónde está el balón en el campo, pero no hacia dónde se mueve. La idea: cada equipo mueve el balón
sobre todo hacia la portería rival. Una velocidad medida en `VENTANA` frames o más sobrevive a un suavizado
de 25 (es una diferencia de posiciones lejanas).

Por frame vivo con balón en `t − VENTANA/2` y `t + VENTANA/2`: la velocidad del balón en la dirección de
ataque del local (la de `aprendida._rasgos_forma`: el local ataca hacia donde está, en media, el visitante).
Si pasa de `UMBRAL` m/s, «dice» `H`; si baja de −`UMBRAL`, `A`. Se compara con la etiqueta, por duración de
la posesión real, frente al más cercano (N1) en los mismos frames.
"""

import collections
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
import informacion as inf  # noqa: E402
from possession import aprendida, tracking  # noqa: E402

H, A = tracking.H, tracking.A
VENTANAS = (13, 25, 51)
UMBRAL = 2.0


def direccion_local(trk, a, b):
    team = np.asarray(trk.team)
    xh = trk.px[a:b][:, team == H].astype(np.float64)
    xa = trk.px[a:b][:, team == A].astype(np.float64)
    if not (np.isfinite(xh).any() and np.isfinite(xa).any()):
        return 0.0
    return float(np.sign(np.nanmean(xa) - np.nanmean(xh)))


def dice_direccion(trk, ventana):
    """Por frame: H, A o -1 según la velocidad del balón en la dirección de ataque del local."""
    salida = np.full(len(trk.bx), -1, dtype=np.int8)
    m = ventana // 2
    for a, b in trk.blocks:
        signo = direccion_local(trk, a, b)
        bx = np.asarray(trk.bx[a:b], dtype=np.float64)
        v = np.full(b - a, np.nan)
        if b - a > 2 * m:
            v[m:-m] = (bx[2 * m:] - bx[:-2 * m]) * trk.fps / (2.0 * m) * signo
        salida[a:b] = np.where(v > UMBRAL, H, np.where(v < -UMBRAL, A, -1))
    return salida


def acumular(acc, clave, gt, dice, duracion):
    vivo = np.isin(gt, (H, A))
    for _, _, nombre in de.TRAMOS + ((0, 0, "todas"),):
        m = vivo & ((duracion == nombre) if nombre != "todas" else True)
        opina = m & (dice >= 0)
        acc[(clave, nombre)] += np.array([m.sum(), opina.sum(), np.sum(opina & (dice == gt))], dtype=np.int64)


def imprimir(titulo, acc, claves):
    print("\n### {}\n".format(titulo))
    print("Frames vivos dentro de posesiones reales. «opina»: la señal da un equipo; «bien»: de los que opina, el "
          "equipo bueno.\n")
    print("| señal | " + " | ".join(n for _, _, n in de.TRAMOS) + " | todas |")
    print("|---|" + "---|" * (len(de.TRAMOS) + 1))
    for clave in claves:
        celdas = []
        for _, _, nombre in de.TRAMOS + ((0, 0, "todas"),):
            total, opina, bien = acc[(clave, nombre)]
            celdas.append("opina {:.0f} %, bien {:.0f} %".format(100.0 * opina / max(total, 1),
                                                                100.0 * bien / max(opina, 1)))
        print("| {} | {} |".format(clave, " | ".join(celdas)).replace(".", ","))


def claves():
    return ["N1 (más cercano)"] + ["dirección del balón, {} frames, > {:g} m/s".format(v, UMBRAL) for v in VENTANAS]


def medir(trk, gt, acc):
    duracion = inf.duracion_por_frame(gt)
    acumular(acc, claves()[0], gt, aprendida.equipo_mas_cercano(trk), duracion)
    for clave, v in zip(claves()[1:], VENTANAS):
        acumular(acc, clave, gt, dice_direccion(trk, v), duracion)


def main():
    print("# ¿Dice la dirección del balón quién lo tiene? (descriptivo)")
    acc = {c: collections.defaultdict(lambda: np.zeros(3, dtype=np.int64)) for c in dfl.CONVENCIONES}
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        trk = dfl.tracking_de(cargado, dfl.VOTAN[0])
        for conv in dfl.CONVENCIONES:
            medir(trk, cargado["gt"][conv], acc[conv])
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    for conv in dfl.CONVENCIONES:
        imprimir("DFL, «{}», etiquetas «{}»".format(dfl.VOTAN[0], conv), acc[conv], claves())
    import lector as lc
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    acc_sk = collections.defaultdict(lambda: np.zeros(3, dtype=np.int64))
    for id_ in ids:
        trk, gt = lc.tracking_de(lc.leer_crudo(id_), "detectado", id_)
        medir(trk, gt, acc_sk)
        print("hecho {}".format(id_), file=sys.stderr, flush=True)
    imprimir("SkillCorner, «detectado»", acc_sk, claves())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
