"""Limpieza del balón. Recibe un `Tracking` y devuelve otro con el balón limpio.

Versión 0: lo devuelve tal cual.

Lo previsto (docs/investigacion_metodos.md §2.1, A1 + A2): descartar saltos físicamente imposibles y
detecciones aisladas, e interpolar los huecos cortos en los que el balón reaparece donde se le espera.
No se interpola a través de un hueco si el balón reaparece junto a un jugador del otro equipo: ahí puede
haber un cambio de posesión y decide el decodificador.
"""


def clean(trk):
    """El tracking con el balón limpio.

    `trk._replace(bx=..., by=...)` devuelve la copia con el balón nuevo.
    """
    return trk
