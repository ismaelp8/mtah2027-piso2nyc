"""Estado de balón muerto (`D`) a partir del tracking: ¿está parado el juego en este frame?

Solo usa el `Tracking` (jugadores y balón), así que corre igual en el partido y en la DFL del harness.
Los instantes exactos (inicio y fin de cada parada) y lo que sale de los ficheros del partido van en
possession/dead_ball.py.

Versión 0: no opina.

Lo previsto (validation/resultados/2026-11-13_revision_balon_muerto.md §5.3 y §6): la probabilidad de `D`
por frame de un modelo con rasgos de equipo sin identidad, entrenado con los 7 partidos de la DFL.

Interfaz: `evidence(trk)` devuelve `(score, allowed)`; ver possession/tracking.py. La histéresis y la
duración mínima no van aquí: las pone el decodificador (possession/temporal.py).
"""

from possession.tracking import no_evidence


def evidence(trk):
    """Sin opinión: puntuación a cero y todo permitido."""
    return no_evidence(len(trk.bx))
