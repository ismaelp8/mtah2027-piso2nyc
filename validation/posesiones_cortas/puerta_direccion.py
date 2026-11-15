"""Puerta barata, antes de escribir un candidato: ¿la dirección del balón mueve las posesiones de 2 a 10 s?

    python validation/posesiones_cortas/puerta_direccion.py

DFL (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar cualquiera, Claude incluido. Solo agregados.

**Es una puerta, no una medida** (BITACORA.md §6): se entrena con los 7 partidos y se mira en los mismos
7, así que es optimista. Para que sea justa, se compara con B2 reentrenada igual en los mismos 7 (no con
los coeficientes de B5, que se puntúan dejando fuera cada partido). Si la dirección no mueve las posesiones
de 2 a 10 s frente a esa referencia, no se gasta un candidato.

Rasgos de dirección (los mismos que llevaría el candidato):
- `dice(t)`: +1 si la velocidad del balón en la dirección de ataque del local, medida de t−6 a t+6
  (13 frames), pasa de 2 m/s; −1 si baja de −2 m/s; 0 si no, o si falta el balón en alguno de los dos
  extremos;
- sus medias centradas en 1, 13 y 51 frames (`aprendida.media_centrada`).
"""

import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "scripts"),
                 os.path.join(ROOT, "validation", "apuesta_b"), os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import diagnostico_errores as de  # noqa: E402
import entrenar  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, ball, pipeline, tracking  # noqa: E402

H, A = tracking.H, tracking.A
MITAD = 6
UMBRAL = 2.0
VENTANAS = (1, 13, 51)
ALFAS = (2.0, 4.0, 8.0)


def rasgos_direccion(trk):
    """(n, 3): las medias centradas de `dice` en `VENTANAS`, a cero fuera de los tramos."""
    team = np.asarray(trk.team)
    salida = np.zeros((len(trk.bx), len(VENTANAS)))
    for a, b in trk.blocks:
        xh = trk.px[a:b][:, team == H].astype(np.float64)
        xa = trk.px[a:b][:, team == A].astype(np.float64)
        hay_h, hay_a = np.isfinite(xh), np.isfinite(xa)
        signo = 0.0
        if hay_h.any() and hay_a.any():
            signo = float(np.sign(np.where(hay_a, xa, 0).sum() / hay_a.sum() - np.where(hay_h, xh, 0).sum() / hay_h.sum()))
        bx = np.asarray(trk.bx[a:b], dtype=np.float64)
        dice = np.zeros(b - a)
        if b - a > 2 * MITAD:
            v = (bx[2 * MITAD:] - bx[:-2 * MITAD]) * trk.fps / (2.0 * MITAD) * signo
            v = np.where(np.isfinite(v), v, 0.0)
            dice[MITAD:-MITAD] = np.where(v > UMBRAL, 1.0, np.where(v < -UMBRAL, -1.0, 0.0))
        salida[a:b] = np.column_stack([aprendida.media_centrada(dice, w) for w in VENTANAS])
    return salida


def preparar(partido):
    cargado = dfl.cargar(partido)
    gt = cargado["gt"]
    condiciones = {}
    for cond in dfl.VOTAN:
        trk = ball.clean(puntuar.solo_lectura(dfl.tracking_de(cargado, cond)))
        cercano = aprendida.equipo_mas_cercano(trk)
        dentro = np.zeros(len(gt["flag"]), bool)
        for a, b in trk.blocks:
            dentro[a:b] = True
        condiciones[cond] = {"trk": trk, "b2": aprendida.rasgos(trk, "b5"), "dir": rasgos_direccion(trk),
                             "visible": aprendida.balon_visible(trk), "cercano": np.where(dentro, cercano, -1)}
    coinciden = (gt["flag"] == gt["control"]) & np.isin(gt["flag"], (H, A))
    filas = np.flatnonzero(coinciden & (np.arange(len(coinciden)) % entrenar.PASO == 0))
    return {"gt": gt, "condiciones": condiciones, "filas": filas}


def main():
    datos = collections.OrderedDict()
    for partido in dfl.PARTIDOS:
        datos[partido] = preparar(partido)
        print("preparado {}".format(partido), file=sys.stderr, flush=True)
    c0 = entrenar.CONDICION_ENTRENAMIENTO
    y = np.concatenate([(d["gt"]["flag"][d["filas"]] == H).astype(float) for d in datos.values()])
    X2 = np.vstack([d["condiciones"][c0]["b2"][d["filas"]] for d in datos.values()])
    Xd = np.vstack([d["condiciones"][c0]["dir"][d["filas"]] for d in datos.values()])
    pesos_b2, _, _ = entrenar.ajustar(X2, y)
    pesos_b9, w9, _ = entrenar.ajustar(np.hstack([X2, Xd]), y)
    print("# Puerta: ¿la dirección del balón mueve las posesiones de 2 a 10 s? (DFL, en los mismos 7 partidos)\n")
    print("Filas: {}. Pesos de dirección (rasgos divididos por su raíz cuadrática media): {}.".format(
        len(y), ", ".join("{:+.2f}".format(v) for v in w9[-len(VENTANAS):])))
    modelos = [("B2 reentrenada en los 7 (referencia justa)", "b2", pesos_b2),
               ("B2 + dirección del balón, en los 7", "b9", pesos_b9)]
    for cond in dfl.VOTAN:
        print("\n## Condición «{}»".format(cond))
        for conv in dfl.CONVENCIONES:
            for nombre, tipo, pesos in modelos:
                for alfa in ALFAS:
                    acc = de.nuevo()
                    for d in datos.values():
                        c = d["condiciones"][cond]
                        X = c["b2"] if tipo == "b2" else np.hstack([c["b2"], c["dir"]])
                        evidencia = aprendida.puntuacion_de("b5", aprendida.logit(X, pesos), c["visible"], alfa,
                                                            c["cercano"])
                        pred = pipeline.run(c["trk"], extra=[puntuar.d_oraculo(d["gt"]["flag"])],
                                            pieces={"candidates": lambda _t, e=evidencia: e})
                        de.analizar(d["gt"][conv], pred, acc)
                    de.imprimir("{}, α = {:g}, etiquetas «{}»".format(nombre, alfa, conv), acc, de.CAUSAS_REALES[:3])
            print("hecho {} {}".format(cond, conv), file=sys.stderr, flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
