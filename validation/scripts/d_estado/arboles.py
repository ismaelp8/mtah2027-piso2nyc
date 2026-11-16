"""Árboles con *boosting* para el estado de `D` (idea 2.4): los candidatos G2 y G3.

    python validation/scripts/d_estado/arboles.py              # entrena G2 y G3 con los 7 partidos: tamaño y versiones

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del harness
(validation/harness/README.md). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Los candidatos, lo que queda fijo y la regla de entrada se escribieron antes de medir: docs/decisiones.md, entrada del
16/11 «estado con árboles (idea 2.4)». La medida está en medir_arboles.py.

- G2: los 11 rasgos de E2; G3: los 19 de E3. Los rasgos son los del pipeline (`dead_state.features`) y las muestras,
  las de E2 (`entrenar.muestras`: uno de cada 5 frames con etiqueta y todos los rasgos).
- La salida es como la de E2 (`dead_state.log_odds`): el logaritmo de la razón de probabilidades de `D`, cero donde
  falta algún rasgo, recortado a ±SCORE_CLIP y redondeado a la rejilla de SCORE_GRID.
- Usa scikit-learn, en un entorno aparte que no entra en requirements-entrega.txt (entrada del 16/11). El ajuste va
  con un solo hilo: con varios, la suma de los gradientes de la raíz depende de cuántos haya, y dos máquinas podrían
  dar árboles distintos en las últimas cifras.
"""

import os
import sys

import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
sys.path.insert(0, AQUI)
sys.path.insert(0, ROOT)
import entrenar  # noqa: E402
from possession import dead_state, tracking  # noqa: E402

CANDIDATOS = {"G2": dead_state.E2, "G3": dead_state.E3}
# Fijados antes de medir y sin probar otros (docs/decisiones.md, 16/11).
PARAMETROS = {"learning_rate": 0.1, "max_iter": 200, "max_leaf_nodes": 15, "min_samples_leaf": 200,
              "l2_regularization": 1.0, "early_stopping": False, "random_state": 0}


def ajustar(cargados, nombres):
    """Los árboles ajustados con esos partidos (los de `entrenar.cargar`), `D` frente a juego."""
    partes = [entrenar.muestras(datos, nombres) for datos in cargados]
    matriz = np.vstack([p[0] for p in partes])
    y = np.concatenate([p[1] for p in partes])
    modelo = HistGradientBoostingClassifier(**PARAMETROS)
    with threadpool_limits(limits=1):
        modelo.fit(matriz, y)
    if list(modelo.classes_) != [0, 1]:
        raise ValueError("las clases tienen que ser juego (0) y `D` (1)")
    return modelo


def puntuacion(modelo, nombres, trk):
    """El logaritmo de la razón de probabilidades de `D` por frame, forma (n,), como `dead_state.log_odds`."""
    rasgos = dead_state.features(trk, nombres)
    matriz = np.column_stack([rasgos[nombre] for nombre in nombres])
    completos = ~np.isnan(matriz).any(axis=1)
    salida = np.zeros(len(matriz))
    if completos.any():
        salida[completos] = modelo.decision_function(matriz[completos])
    clip, rejilla = dead_state.SCORE_CLIP, dead_state.SCORE_GRID
    return np.round(np.clip(salida, -clip, clip) * rejilla) / rejilla


def dejando_fuera(cargados, nombres, ajuste=ajustar):
    """{partido: modelo entrenado con los demás}."""
    return {datos["partido"]: ajuste([otro for otro in cargados if otro is not datos], nombres)
            for datos in cargados}


def evidencia(trk, modelo, nombres):
    """`(score, allowed)` de la pieza con estos árboles: la puntuación en la columna `D`, sin prohibir nada."""
    score, allowed = tracking.no_evidence(len(trk.bx))
    score[:, tracking.D] = puntuacion(modelo, nombres, trk)
    return score, allowed


def tamano(modelo):
    """Árboles, nodos y hojas de un modelo ajustado."""
    nodos = [predictor[0].nodes for predictor in modelo._predictors]
    return {"arboles": len(nodos), "nodos": int(sum(len(n) for n in nodos)),
            "hojas": int(sum(int(n["is_leaf"].sum()) for n in nodos))}


def main():
    cargados = [entrenar.cargar(partido) for partido in entrenar.PARTIDOS]
    print("# scikit-learn {} · numpy {} · Python {}".format(sklearn.__version__, np.__version__,
                                                           sys.version.split()[0]))
    for nombre, rasgos in CANDIDATOS.items():
        t = tamano(ajustar(cargados, rasgos))
        print("# {}: {} rasgos · {} árboles · {} nodos · {} hojas".format(
            nombre, len(rasgos), t["arboles"], t["nodos"], t["hojas"]))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
