"""Cuánto pesa la evidencia de equipo en cada frame: N1 frente a la aprendida (apuesta B). Descriptivo.

    python validation/apuesta_b/escala.py

Con el `D` oráculo del harness, lo que una pieza de equipo puntúa en las paradas no cambia ninguna
etiqueta. En la entrega sí: la puntuación de `H` o `A` compite con la de `D` de `dead_state` y `dead_ball`,
y con los costes del decodificador, que se ajustan en la escala de N1 (1 por frame con balón). Este script
mide esa escala en la DFL con el balón «como el ATD», cada partido con el pliegue que no lo vio: la media
y el percentil 90 de la puntuación del equipo ganador (la diferencia con `D`) en los frames de juego con
balón, en los de juego sin balón y en los `D`.

Son datos abiertos de otros partidos: lo puede ejecutar cualquiera, Claude incluido. Solo imprime
agregados. No decide nada.

Límite: la DFL tapa el balón en todos los `D` y en sus bordes (README del harness), así que aquí N1 nunca
opina en un `D`. En el ATD el balón puede verse en las paradas, y entonces N1 también opinaría.
"""

import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
from possession import aprendida, candidates, tracking  # noqa: E402

CONDICION = "como el ATD"
PIEZAS = collections.OrderedDict([
    ("N1 (main)", lambda trk, partido: candidates.evidence(trk)),
    ("B1", lambda trk, partido: aprendida.evidence_b1(trk, fuera=partido)),
    ("B2", lambda trk, partido: aprendida.evidence_b2(trk, fuera=partido)),
])
GRUPOS = ("juego con balón", "juego sin balón", "`D`")


def main():
    valores = collections.defaultdict(list)
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]["flag"]
        trk = dfl.tracking_de(cargado, CONDICION)
        visible = ~np.isnan(trk.bx)
        vivo = (gt == tracking.H) | (gt == tracking.A)
        mascaras = {"juego con balón": vivo & visible, "juego sin balón": vivo & ~visible, "`D`": gt == tracking.D}
        for nombre, pieza in PIEZAS.items():
            score, _ = pieza(trk, partido)
            margen = np.max(score[:, :2], axis=1) - score[:, tracking.D]
            for grupo in GRUPOS:
                valores[(nombre, grupo)].append(margen[mascaras[grupo]])
        print("hecho {}".format(partido), file=sys.stderr)
    print("Puntuación del equipo ganador menos la de `D`, por frame (DFL, balón «{}», cada partido con el "
          "pliegue que no lo vio, los 7 juntos):".format(CONDICION))
    print()
    print("| pieza | " + " | ".join("{}: media / p90 / % > 0".format(g) for g in GRUPOS) + " |")
    print("|---|" + "---|" * len(GRUPOS))
    for nombre in PIEZAS:
        celdas = []
        for grupo in GRUPOS:
            v = np.concatenate(valores[(nombre, grupo)])
            celdas.append("{:.2f} / {:.2f} / {:.1f} %".format(
                float(np.mean(v)), float(np.percentile(v, 90)), 100.0 * float(np.mean(v > 0))).replace(".", ","))
        print("| {} | {} |".format(nombre, " | ".join(celdas)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
