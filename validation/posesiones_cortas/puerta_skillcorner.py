"""Puerta barata, antes de escribir un candidato: ¿entrenar con tracking automático mueve las posesiones de 2 a 5 s?

    python validation/posesiones_cortas/puerta_skillcorner.py

Solo la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`; A-League 2024/25, licencia MIT) y la
DFL (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar cualquiera, Claude incluido. Solo agregados.

**Es una puerta, no una medida** (BITACORA.md §4): se entrena y se mira **en los mismos partidos**, así que
es lo más optimista que puede salir. Si ni así se mueven las posesiones de 2 a 5 s frente a `main`, no se
gasta un candidato en esta idea.

Qué hace, con los rasgos de B2 (los de B5) y la regresión de `validation/apuesta_b/entrenar.py` (`ajustar`,
las mismas `LAMBDA`, `ITERACIONES` y `CIFRAS`):

- **SK**: filas de los 10 partidos de entrenamiento con el balón «detectado, suavizado» (el balón suavizado
  como el del ATD), uno de cada `PASO` frames vivos, todos (no solo donde coinciden dos convenciones: aquí
  hay una sola), con la etiqueta de SkillCorner;
- **DFL + SK**: las filas de B5 (las de `entrenar.preparar`, «como el ATD», donde flag = control) más las de SK.

Cada modelo se puntúa como B5 (`aprendida.puntuacion_de("b5", ...)`) con α de la rejilla de B5, con el `D` de
las etiquetas, en las dos condiciones de SkillCorner que votan, frente a `main` (B5 con los coeficientes de la
entrega). Se enseña el spellF1 y lo que encuentra por duración, con el script del diagnóstico de errores.
"""

import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                 os.path.join(ROOT, "validation", "scripts"), os.path.join(ROOT, "validation", "apuesta_b"),
                 os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import diagnostico_errores as de  # noqa: E402
import entrenar  # noqa: E402
import lector as lc  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
PASO = entrenar.PASO
CONDICION_FILAS = "detectado, suavizado"
ALFAS = (2.0, 4.0, 8.0)


def preparar_sk(id_):
    """Por condición que vota: rasgos de B2, N1, balón visible, tramos y etiquetas de un partido de SK."""
    crudo = lc.leer_crudo(id_)
    salida = {}
    for cond in lc.VOTAN:
        trk, gt = lc.tracking_de(crudo, cond, id_)
        limpio = pipeline.default_piece("ball")(puntuar.solo_lectura(trk))
        cercano = aprendida.equipo_mas_cercano(limpio)
        dentro = np.zeros(len(gt), bool)
        for a, b in trk.blocks:
            dentro[a:b] = True
        salida[cond] = {"trk": trk, "gt": gt, "rasgos": aprendida.rasgos(limpio, "b5"),
                        "visible": aprendida.balon_visible(limpio), "cercano": np.where(dentro, cercano, -1)}
    return salida


def filas_sk(datos):
    X, y = [], []
    for dato in datos.values():
        c = dato[CONDICION_FILAS]
        vivo = np.flatnonzero(np.isin(c["gt"], (H, A)))
        vivo = vivo[vivo % PASO == 0]
        X.append(c["rasgos"][vivo])
        y.append((c["gt"][vivo] == H).astype(float))
    return np.vstack(X), np.concatenate(y)


def filas_dfl():
    X, y = [], []
    cols = entrenar.columnas("b5")
    for partido in dfl.PARTIDOS:
        p = entrenar.preparar(partido)
        c = p["condiciones"][entrenar.CONDICION_ENTRENAMIENTO]
        X.append(c["rasgos"][p["filas"]][:, cols])
        y.append((p["gt"]["flag"][p["filas"]] == H).astype(float))
        print("filas DFL {}".format(partido), file=sys.stderr, flush=True)
    return np.vstack(X), np.concatenate(y)


def puntuar_modelo(datos, pesos, alfa, cond):
    acc = de.nuevo()
    for dato in datos.values():
        c = dato[cond]
        z = aprendida.logit(c["rasgos"], pesos)
        evidencia = aprendida.puntuacion_de("b5", z, c["visible"], alfa, c["cercano"])
        pred = pipeline.run(c["trk"], extra=[puntuar.d_oraculo(c["gt"])], pieces={"candidates": lambda _t: evidencia})
        de.analizar(c["gt"], pred, acc)
    return acc


def main():
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    datos = collections.OrderedDict()
    for id_ in ids:
        datos[id_] = preparar_sk(id_)
        print("preparado {}".format(id_), file=sys.stderr, flush=True)
    Xs, ys = filas_sk(datos)
    Xd, yd = filas_dfl()
    modelos = collections.OrderedDict()
    modelos["main (B5, coeficientes de la entrega)"] = [(aprendida.coeficientes("b5")["alfa"],
                                                        aprendida.coeficientes("b5")["pesos"])]
    pesos_sk, _, paso_sk = entrenar.ajustar(Xs, ys)
    pesos_mix, _, paso_mix = entrenar.ajustar(np.vstack([Xd, Xs]), np.concatenate([yd, ys]))
    modelos["SK, en los mismos partidos"] = [(a, pesos_sk) for a in ALFAS]
    modelos["DFL + SK, en los mismos partidos de SK"] = [(a, pesos_mix) for a in ALFAS]
    print("# Puerta: ¿entrenar con SkillCorner mueve las posesiones de 2 a 5 s? (en los mismos partidos)\n")
    print("Filas: SK {} ({} partidos, «{}»), DFL {}. Último paso de Newton: SK {:.1e}, DFL + SK {:.1e}.".format(
        len(ys), len(ids), CONDICION_FILAS, len(yd), paso_sk, paso_mix))
    for cond in lc.VOTAN:
        print("\n## Condición «{}»".format(cond))
        for nombre, variantes in modelos.items():
            for alfa, pesos in variantes:
                de.imprimir("{}, α = {:g}".format(nombre, alfa), puntuar_modelo(datos, pesos, alfa, cond),
                            de.CAUSAS_REALES[:3])
                print("hecho {} α {} {}".format(nombre, alfa, cond), file=sys.stderr, flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
