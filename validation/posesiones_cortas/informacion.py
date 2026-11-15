"""¿Queda información del equipo en los frames de las posesiones cortas? Sondeo descriptivo, solo agregados.

    python validation/posesiones_cortas/informacion.py

Datos abiertos de la DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de SkillCorner
(`lector.ENTRENAMIENTO`). Lo puede ejecutar cualquiera, Claude incluido. **No decide nada** (BITACORA.md §3).

Por frame vivo con balón, el equipo del jugador más cercano frente a la etiqueta, con tres balones y dos
formas de mirar a los jugadores:

- balón «como el ATD» (suavizado con una media centrada de 25 frames) frente a los jugadores tal cual: es
  N1, lo que ve hoy B5;
- el mismo balón frente a los jugadores **suavizados igual** (la misma media de 25 frames por slot): si el
  balón va pegado a un jugador, la media del balón es la media del jugador;
- el balón limpio frente a los jugadores tal cual: el techo, sin suavizado.

En SkillCorner, el balón «detectado» (sin suavizar) y «detectado, suavizado» (la misma media de 25), con los
jugadores tal cual y suavizados.

Se da el acierto (más cercano del equipo bueno), el fallo (del otro) y lo mismo exigiendo que el más cercano
esté a 2 m o menos, por duración de la posesión real que contiene el frame.
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
import possession_metrics as pm  # noqa: E402
from possession import tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
ANCHO = dfl.SUAVIZADO
RADIO = 2.0
BLOQUE = 20000


def suavizar_jugadores(px, py, blocks, ancho=ANCHO):
    """La media móvil centrada de `ancho` frames de cada slot, por tramo, ignorando los NaN (como dfl.media_movil).

    Un frame sin el slot sigue sin él: solo se suaviza lo que existe.
    """
    sx, sy = np.full(px.shape, np.nan), np.full(py.shape, np.nan)
    for a, b in blocks:
        for origen, destino in ((px, sx), (py, sy)):
            v = origen[a:b].astype(np.float64)
            hay = np.isfinite(v)
            suma = np.concatenate([np.zeros((1, v.shape[1])), np.cumsum(np.where(hay, v, 0.0), axis=0)])
            cuenta = np.concatenate([np.zeros((1, v.shape[1])), np.cumsum(hay, axis=0)])
            i = np.arange(b - a)
            bajo, alto = np.maximum(0, i - ancho // 2), np.minimum(b - a, i + ancho // 2 + 1)
            n = cuenta[alto] - cuenta[bajo]
            media = (suma[alto] - suma[bajo]) / np.maximum(n, 1)
            destino[a:b] = np.where(hay & (n > 0), media, np.nan)
    return sx, sy


def mas_cercano(bx, by, px, py, team):
    """(equipo del más cercano, distancia) por frame; -1 e inf sin balón o sin jugadores."""
    n = len(bx)
    equipo, distancia = np.full(n, -1, dtype=np.int8), np.full(n, np.inf)
    vistos = np.flatnonzero(np.isfinite(bx) & np.isfinite(by))
    for inicio in range(0, len(vistos), BLOQUE):
        idx = vistos[inicio:inicio + BLOQUE]
        d2 = (px[idx] - bx[idx, None]) ** 2 + (py[idx] - by[idx, None]) ** 2
        d2 = np.where(np.isfinite(d2), d2, np.inf)
        k = np.argmin(d2, axis=1)
        mejor = d2[np.arange(len(idx)), k]
        ok = np.isfinite(mejor)
        equipo[idx[ok]] = team[k[ok]]
        distancia[idx[ok]] = np.sqrt(mejor[ok])
    return equipo, distancia


def duracion_por_frame(gt):
    """El nombre del tramo de duración de la posesión real que contiene cada frame ('' fuera de posesiones)."""
    salida = np.full(len(gt), "", dtype=object)
    runs = pm.valid_runs(gt)
    for a, b, _ in pm.possession_spells(gt, runs):
        salida[a:b] = de.tramo(b - a)
    return salida


def acumular(acc, clave, gt, equipo, distancia, duracion):
    vivo = np.isin(gt, (H, A)) & (equipo >= 0)
    for _, _, nombre in de.TRAMOS + ((0, 0, "todas"),):
        m = vivo & ((duracion == nombre) if nombre != "todas" else True)
        cerca = m & (distancia <= RADIO)
        acc[(clave, nombre)] += np.array([m.sum(), np.sum(m & (equipo == gt)), cerca.sum(),
                                          np.sum(cerca & (equipo == gt))], dtype=np.int64)


def imprimir(titulo, acc, claves):
    print("\n### {}\n".format(titulo))
    print("Frames vivos con balón dentro de posesiones reales. «bien»: el más cercano es del equipo bueno. "
          "«a ≤ {:g} m»: solo los frames con el más cercano a esa distancia o menos.\n".format(RADIO))
    print("| balón y jugadores | " + " | ".join(n for _, _, n in de.TRAMOS) + " | todas |")
    print("|---|" + "---|" * (len(de.TRAMOS) + 1))
    for clave in claves:
        celdas = []
        for _, _, nombre in de.TRAMOS + ((0, 0, "todas"),):
            total, bien, cerca, cerca_bien = acc[(clave, nombre)]
            celdas.append("{:.0f} % bien · a ≤ {:g} m: {:.0f} % de los frames, {:.0f} % bien".format(
                100.0 * bien / max(total, 1), RADIO, 100.0 * cerca / max(total, 1), 100.0 * cerca_bien / max(cerca, 1)))
        print("| {} | {} |".format(clave, " | ".join(celdas)).replace(".", ","))


def main():
    print("# ¿Queda información del equipo en las posesiones cortas? (descriptivo)")
    acc = {c: collections.defaultdict(lambda: np.zeros(4, dtype=np.int64)) for c in dfl.CONVENCIONES}
    claves_dfl = ("como el ATD, jugadores tal cual (N1)", "como el ATD, jugadores suavizados igual",
                  "limpio, jugadores tal cual (techo)")
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        atd = dfl.tracking_de(cargado, "como el ATD")
        limpio = dfl.tracking_de(cargado, "limpio")
        team = np.asarray(atd.team)
        px, py = atd.px.astype(np.float64), atd.py.astype(np.float64)
        sx, sy = suavizar_jugadores(px, py, atd.blocks)
        variantes = {claves_dfl[0]: mas_cercano(atd.bx, atd.by, px, py, team),
                     claves_dfl[1]: mas_cercano(atd.bx, atd.by, sx, sy, team),
                     claves_dfl[2]: mas_cercano(limpio.bx, limpio.by, px, py, team)}
        for conv in dfl.CONVENCIONES:
            gt = cargado["gt"][conv]
            duracion = duracion_por_frame(gt)
            for clave, (equipo, distancia) in variantes.items():
                acumular(acc[conv], clave, gt, equipo, distancia, duracion)
        print("hecho {}".format(partido), file=sys.stderr, flush=True)
    for conv in dfl.CONVENCIONES:
        imprimir("DFL, etiquetas «{}»".format(conv), acc[conv], claves_dfl)

    import lector as lc
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    acc_sk = collections.defaultdict(lambda: np.zeros(4, dtype=np.int64))
    claves_sk = ("detectado, jugadores tal cual (N1)", "detectado, jugadores suavizados",
                 "detectado y suavizado, jugadores tal cual (N1)", "detectado y suavizado, jugadores suavizados igual")
    for id_ in ids:
        crudo = lc.leer_crudo(id_)
        for cond, claves in (("detectado", claves_sk[:2]), ("detectado, suavizado", claves_sk[2:])):
            trk, gt = lc.tracking_de(crudo, cond, id_)
            team = np.asarray(trk.team)
            px, py = trk.px.astype(np.float64), trk.py.astype(np.float64)
            sx, sy = suavizar_jugadores(px, py, trk.blocks)
            duracion = duracion_por_frame(gt)
            acumular(acc_sk, claves[0], gt, *mas_cercano(trk.bx, trk.by, px, py, team), duracion)
            acumular(acc_sk, claves[1], gt, *mas_cercano(trk.bx, trk.by, sx, sy, team), duracion)
        print("hecho {}".format(id_), file=sys.stderr, flush=True)
    imprimir("SkillCorner, `lector.ENTRENAMIENTO` ({} partidos)".format(len(ids)), acc_sk, claves_sk)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
