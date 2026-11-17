"""El sondeo S2 del 16/11 (decodificar a riesgo mínimo), repetido con la evidencia de K2 en lugar de la de B5.

    python validation/conjunto/riesgo_minimo_k2.py

DFL (7 partidos abiertos, Bassek et al., 2025, CC BY 4.0), balón «como el ATD», `D` de las etiquetas y K2 con los
pesos del pliegue que no vio cada partido. Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Es el punto 3 del análisis del 17/11 («decodificar para la métrica»). S2 midió que con la evidencia de B5 no sirve:
las muestras se fragmentan y la duda del modelo no dice dónde falla. Aquí se repite el mismo instrumento
(`validation/investigacion_1116/riesgo_minimo.py`, sin tocarlo) cambiando solo la evidencia de equipo: K2
(`aprendida.evidence_k2`) en lugar de B5. Lo que el instrumento llama `main` es aquí el Viterbi de coste 25 sobre la
evidencia de K2.

La regla de lectura es la de S2, tal cual, y está escrita antes de ejecutar esto (docs/decisiones.md, 17/11).
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "investigacion_1116"))
sys.path.insert(0, ROOT)
import riesgo_minimo as s2  # noqa: E402  (validation/investigacion_1116/riesgo_minimo.py)
from possession import aprendida, pipeline  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def evidencia(trk, gt, partido):
    """La evidencia sumada con K2 en lugar de B5 y el `D` de las etiquetas, como `pipeline.run` antes de decodificar."""
    limpio = pipeline.default_piece("ball")(trk)
    score, allowed, _ = pipeline.combine(
        [aprendida.evidence_k2(limpio, fuera=partido), pipeline.default_piece("dead_state")(limpio),
         s2.puntuar.d_oraculo(gt)], len(limpio.bx))
    return score, allowed


if __name__ == "__main__":
    print("# Riesgo mínimo con la evidencia de K2 (el sondeo S2 del 16/11, con K2 en lugar de B5)\n")
    print("Código: {}. Lo que el instrumento llama `main` es aquí el Viterbi de coste 25 sobre K2.\n".format(
        s2.puntuar.version_del_codigo()))
    s2.evidencia = evidencia
    s2.main()
