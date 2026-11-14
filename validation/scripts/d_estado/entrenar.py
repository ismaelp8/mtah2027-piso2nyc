"""Entrena el modelo de estado de `D` de possession/dead_state.py con los partidos abiertos de la DFL.

    python validation/scripts/d_estado/entrenar.py                 # imprime el MODEL del candidato elegido
    python validation/scripts/d_estado/entrenar.py --candidato E3  # el de otro candidato
    python validation/scripts/d_estado/entrenar.py --comprobar     # ¿el MODEL del módulo sale de aquí?

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del harness
(validation/harness/README.md). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados y
coeficientes.

Qué hace: calcula los rasgos con el mismo código que usa el pipeline (`dead_state.features`), ajusta una
regresión logística (`D` frente a juego) y devuelve los coeficientes ya en las unidades de los rasgos,
para escribirlos en `dead_state.MODEL`. Es el único sitio donde se usa scikit-learn.

Sin azar: los frames de entrenamiento son uno de cada `PASO`, y el ajuste (Newton, hasta el óptimo) es
determinista. Dos ejecuciones dan los mismos coeficientes.

Para medir un candidato sin trampa, validation/scripts/d_estado/medir.py llama a `ajustar` dejando un
partido fuera cada vez.
"""

import argparse
import os
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
from possession import dead_state  # noqa: E402

PARTIDOS = tuple(dfl.PARTIDOS)
CANDIDATOS = {"E1": dead_state.E1, "E2": dead_state.E2, "E3": dead_state.E3}
ELEGIDO = "E2"  # el candidato cuyos coeficientes están en dead_state.MODEL (docs/decisiones.md)
PASO = 5  # se entrena con uno de cada 5 frames: los frames seguidos son casi iguales
C = 1.0  # regularización de la regresión logística (el valor por defecto de scikit-learn)
CIFRAS = 6  # cifras significativas con las que se escriben los coeficientes
TOLERANCIA = 1e-5  # diferencia relativa admitida entre el MODEL del módulo y el recalculado
D, X = dfl.D, dfl.X


def cargar(partido):
    """Un partido de la DFL listo para entrenar y medir.

    {"partido", "trk", "gt" (por convención), "rasgos" (todos los de dead_state.FEATURES)}. El tracking
    es el de la condición "limpio" del harness: los jugadores son los mismos en las tres y esta pieza no
    usa el balón.
    """
    cargado = dfl.cargar(partido)
    trk = dfl.tracking_de(cargado, "limpio")
    return {"partido": partido, "trk": trk, "gt": cargado["gt"],
            "rasgos": dead_state.features(trk, sorted(dead_state.FEATURES))}


def muestras(datos, nombres):
    """(X, y) de un partido: los rasgos de `nombres` y si el frame es `D`, uno de cada `PASO` frames.

    Solo entran los frames con etiqueta (ni el hueco entre partes ni los frames sin dato) y con todos los
    rasgos.
    """
    gt = datos["gt"]["flag"]  # el `D` es el mismo en las dos convenciones
    matriz = np.column_stack([datos["rasgos"][nombre] for nombre in nombres])
    validos = np.flatnonzero((gt != X) & ~np.isnan(matriz).any(axis=1))[::PASO]
    return matriz[validos], (gt[validos] == D).astype(np.int8)


def redondear(valor):
    return float("{:.{}g}".format(float(valor), CIFRAS))


def ajustar(partidos_cargados, nombres):
    """El modelo ajustado con esos partidos: {"intercept": float, "coef": {rasgo: peso}}.

    Los rasgos se estandarizan para ajustar, y los pesos se devuelven ya deshechos, en las unidades de
    cada rasgo, que es como los usa `dead_state.log_odds`.
    """
    partes = [muestras(datos, nombres) for datos in partidos_cargados]
    matriz = np.vstack([p[0] for p in partes])
    y = np.concatenate([p[1] for p in partes])
    media, desviacion = matriz.mean(axis=0), matriz.std(axis=0)
    if np.any(desviacion == 0):
        raise ValueError("un rasgo no varía en los datos de entrenamiento")
    # Newton llega al óptimo en pocas iteraciones aunque haya rasgos muy parecidos entre sí (la velocidad
    # media en 1, 2 y 4 s); con lbfgs los coeficientes dependían de cuándo se paraba.
    ajuste = LogisticRegression(C=C, solver="newton-cholesky", max_iter=200, tol=1e-10)
    ajuste.fit((matriz - media) / desviacion, y)
    pesos = ajuste.coef_[0] / desviacion
    corte = float(ajuste.intercept_[0]) - float(np.sum(pesos * media))
    return {"intercept": redondear(corte), "coef": {n: redondear(p) for n, p in zip(nombres, pesos)},
            "frames": int(len(y)), "frames_D": int(y.sum())}


def como_codigo(modelo):
    """El modelo como el literal de Python que va en possession/dead_state.py."""
    lineas = ["MODEL = {", '    "intercept": {!r},'.format(modelo["intercept"]), '    "coef": {']
    lineas += ['        "{}": {!r},'.format(nombre, modelo["coef"][nombre]) for nombre in modelo["coef"]]
    lineas += ["    },", "}"]
    return "\n".join(lineas)


def diferencia_con_el_modulo(modelo):
    """Mayor diferencia relativa entre `modelo` y dead_state.MODEL; infinito si los rasgos no son los mismos."""
    actual = dead_state.MODEL
    if set(actual["coef"]) != set(modelo["coef"]):
        return float("inf")
    pares = [(actual["intercept"], modelo["intercept"])]
    pares += [(actual["coef"][n], modelo["coef"][n]) for n in modelo["coef"]]
    return max(abs(a - b) / max(1.0, abs(b)) for a, b in pares)


def main():
    parser = argparse.ArgumentParser(description="Entrena el modelo de estado de D con la DFL.")
    parser.add_argument("--candidato", choices=sorted(CANDIDATOS), default=ELEGIDO)
    parser.add_argument("--partidos", nargs="+", default=list(PARTIDOS), choices=list(PARTIDOS))
    parser.add_argument("--comprobar", action="store_true",
                        help="comprueba que dead_state.MODEL es el que sale de este script")
    args = parser.parse_args()

    cargados = [cargar(partido) for partido in args.partidos]
    modelo = ajustar(cargados, CANDIDATOS[args.candidato])
    print("# candidato {} · {} partidos · {} frames de entrenamiento ({:.1f} % D)".format(
        args.candidato, len(cargados), modelo["frames"], 100.0 * modelo["frames_D"] / modelo["frames"]))
    if args.comprobar:
        dif = diferencia_con_el_modulo(modelo)
        igual = dif <= TOLERANCIA
        print("# dead_state.MODEL {} el recalculado (diferencia máxima {:.1e})".format(
            "coincide con" if igual else "NO coincide con", dif))
        sys.exit(0 if igual else 1)
    print(como_codigo(modelo))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
