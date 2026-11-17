"""Refinamientos de K2 que no reentrenan nada: K3 (la mezcla con B5), K4 (el espejo) y K5.

**K3 es la evidencia de equipo de la entrega desde el 17/11 por la tarde** (`pipeline.PIECES`, por
`aprendida.evidence_k3`; docs/decisiones.md, «se enciende K3»). K4 y K5 están apagadas.

**Por qué** (docs/decisiones.md, 17/11, «dos refinamientos de K2 sin reentrenar»). K2 (`possession/conjunto.py`)
gana a B5 con partidos de un proveedor que ha visto y no se traslada de un proveedor a otro; B5 sí se traslada. El
partido es de un tercer proveedor. Aquí no se entrena nada: se combinan dos logits que ya existen.

- **K3, la mezcla:** la media a partes iguales del logit de K2 y del de B5, cada uno con su α. Se puntúa como B5
  (−|s| al equipo que pierde y el +1 de N1 donde se ve el balón). Si K2 falla en un proveedor nuevo, B5 sigue
  opinando; si acierta, la mezcla se queda con parte de su ganancia.
- **K4, el espejo:** el logit de K2 promediado con el del mismo tracking con el campo en espejo (y → ancho − y). El
  modelo se entrenó con ese espejo como aumento, pero no es simétrico por construcción; el promedio le quita ese
  ruido.
- **K5:** K3 con el logit de K4. Solo se mide si K3 y K4 pasan los dos.

**No toca nada de K2 ni de B5.** `conjunto.evidence`, `aprendida.evidence_b5`, sus pesos y sus coeficientes no
cambian: este módulo solo los lee.

**Reproducible bit a bit, con un matiz.** La mezcla y el promedio son productos y sumas de numpy término a término, y
la puntuación va redondeada a `aprendida.DECIMALES`. K4 no pasa por ninguna exponencial, como K2. K3 y K5 heredan el
`np.exp` de los rasgos de B5: una entrega con ellas hay que reproducirla en otra máquina, como se hizo con B5. Con la
parte de K2 a 1 y sin espejo, la
puntuación es la de `conjunto.evidence` bit a bit; con la parte de K2 a 0, la de `aprendida.evidence_b5`
(`validation/scripts/prueba_refinamientos.py`).

`fuera` es el pliegue de K2 y `fuera_b5` el de B5, como en el harness: el partido de la DFL que se está puntuando.
En la entrega, los dos a `None` (los pesos de todos los partidos).
"""

import numpy as np

from possession import aprendida, conjunto

PESO_K2 = 0.5  # la parte de K2 en la mezcla. Fijada antes de medir: no se elige mirando resultados


def cercano_en_tramos(trk):
    """El equipo del jugador más cercano al balón, a −1 fuera de los tramos evaluados (como B5 y K2)."""
    todos = aprendida.equipo_mas_cercano(trk)
    cercano = np.full(len(trk.bx), -1, dtype=np.int8)
    for inicio, fin in trk.blocks:
        cercano[inicio:fin] = todos[inicio:fin]
    return cercano


def en_espejo(trk):
    """El mismo tracking con el campo en espejo (y → ancho − y). No cambian x, los equipos ni los tramos."""
    ancho = float(trk.pitch[1])
    return trk._replace(by=ancho - np.asarray(trk.by, dtype=np.float64),
                        py=ancho - np.asarray(trk.py, dtype=np.float64))


def logit_b5(trk, fuera_b5=None):
    """α·z de B5 por frame: el logit de la evidencia de la entrega, ya en su escala."""
    juego = aprendida.coeficientes("b5", fuera_b5)
    return float(juego["alfa"]) * aprendida.logit(aprendida.rasgos(trk, "b5"), juego["pesos"])


def logit_k2(trk, fuera=None, espejo=False):
    """α·z de K2 por frame. Con `espejo`, z es la media de la del tracking y la del tracking en espejo."""
    z = conjunto.salidas(trk, fuera)[0]
    if espejo:
        z = 0.5 * (z + conjunto.salidas(en_espejo(trk), fuera)[0])
    return float(conjunto.pesos(fuera)["alfa"]) * z


def mezclar(s_k2, s_b5, peso_k2=PESO_K2):
    """El logit de la mezcla: `peso_k2` de K2 y el resto de B5, los dos ya en su escala."""
    return float(peso_k2) * s_k2 + (1.0 - float(peso_k2)) * s_b5


def puntuar(s, trk):
    """(score, allowed) de un logit ya escalado, como B5: −|s| al que pierde y el +1 de N1 con balón."""
    return aprendida.puntuacion_de("b5", s, aprendida.balon_visible(trk), 1.0, cercano_en_tramos(trk))


def evidence_k3(trk, fuera=None, fuera_b5=None):
    """K3: la mezcla a partes iguales de K2 y B5."""
    return puntuar(mezclar(logit_k2(trk, fuera), logit_b5(trk, fuera_b5)), trk)


def evidence_k4(trk, fuera=None):
    """K4: K2 con el logit promediado con el del campo en espejo."""
    return puntuar(logit_k2(trk, fuera, espejo=True), trk)


def evidence_k5(trk, fuera=None, fuera_b5=None):
    """K5: la mezcla de K3 con el logit de K4."""
    return puntuar(mezclar(logit_k2(trk, fuera, espejo=True), logit_b5(trk, fuera_b5)), trk)
