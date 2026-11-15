"""Empujón al equipo de la fase al empezar cada «Attacking Transition» del Smart Tagging. Capa APAGADA.

No está en `pipeline.PIECES` ni la llama la entrega. Se prueba como capa añadida:

    python -m possession.pipeline --name prueba_transiciones --capa transiciones.evidence

Por qué (docs/decisiones.md, 15/11, «el empujón en los contraataques: peso 8 y tope de 5 s» y las dos entradas
anteriores de las fases del Smart Tagging). Son agregados del partido con `equipo_v3`
(validation/resultados/2026-11-15_fases_smart_tagging.md):
- en los frames de control claro, el equipo de las «Attacking Transition» coincide con el que tiene el balón
  en el 93,1 %;
- en 17 de los 24 contraataques nuestra etiqueta llega de 2 a 10 s tarde, y dentro de esas fases vamos con el
  otro equipo en el 36,2 % de los frames.

Qué hace:
- suma WEIGHT por frame a la columna del equipo de cada `ATTACKING TRANSITION` con `Team` `H` o `A`, desde su
  inicio y durante CAP_S segundos, sin pasar del final de la fase ni del tramo evaluado;
- **suma el mismo peso a la columna `D` en esos frames.** Solo cuentan las diferencias entre columnas, así que
  sin esto la capa también empujaría contra `D`. Con esto solo empuja contra el otro equipo, que es lo único
  que midió la cota de la DFL (con el `D` impuesto, la columna `D` no cambia nada allí). Así no puede borrar
  ni acortar una parada que caiga en esos 5 s;
- solo cuentan las fases que empiezan en un tramo evaluado;
- un frame cubierto por dos transiciones del mismo equipo recibe el peso una vez; si lo cubren dos de equipos
  distintos, lo reciben las tres columnas y la capa no opina;
- no prohíbe nada (`allowed` todo a True).
- **Con `paths` y sin ninguna transición con equipo, da error.** Si el texto de `Team` no coincidiera con TEAMS,
  la capa no haría nada sin avisar.

Las demás fases no entran, y menos las «de zona», que son las que se solapan con equipos distintos. Las
`DEFENSIVE TRANSITION` son el espejo exacto de las de ataque y no añaden nada.

Interfaz: la de possession/dead_ball.py, `evidence(trk, paths=None, game=games.GAME)` → `(score, allowed)`, de
forma (n, 3) y con las columnas `H`, `A`, `D`. Como dead_ball, es una pieza del partido: abre el Smart Tagging de
`paths`. **Sin `paths` no abre nada y no opina:** en la DFL y en validation/scripts/prueba_pipeline.py no cambia
nada. `None` nunca significa «usa games.asset_paths()».
"""

import xml.etree.ElementTree as ET

import numpy as np

import games
from possession.tracking import A, D, H, no_evidence

CODE = "attacking transition"
# Los valores de `Team` del Smart Tagging del partido (DATA.md: «Barcelona» y «Atletic Club», con esa errata).
TEAMS = {"barcelona": H, "atletic club": A, "athletic club": A}

# Fijados y razonados antes de generar ninguna entrega (docs/decisiones.md, 15/11); no salen del partido ni de
# la ventana pública, y no se retocan después:
# - WEIGHT, el mayor de la rejilla de la cota de la DFL (validation/posesiones_cortas/BITACORA.md §13), donde
#   ninguna combinación hizo daño ni con un 30 % de marcas falsas;
# - CAP_S, el tope de las marcas de esa misma cota.
WEIGHT = 8.0  # por frame, en la escala del decodificador (coste de cambio 25)
CAP_S = 5  # s desde el inicio de la fase


def _norm(text):
    return (text or "").strip().lower()


def transitions(path, fps):
    """[(equipo, inicio, fin)] de las ATTACKING TRANSITION con `Team` H o A, ordenadas.

    El mismo criterio que starter/load_smart_tagging.load() y dead_ball.smart_tagging_events(): segundos × fps,
    redondeado, es el frame de vídeo, y `fin` es el primer frame después de la fase. Ordenadas, para que el
    resultado no dependa del orden del fichero.
    """
    out = []
    for instance in ET.parse(path).iter("instance"):
        if _norm(instance.findtext("code")) != CODE:
            continue
        tags = {_norm(label.findtext("group")): label.findtext("text") for label in instance.findall("label")}
        team = TEAMS.get(_norm(tags.get("team")))
        if team is None:
            continue
        start = int(round(float(instance.findtext("start")) * fps))
        end = int(round(float(instance.findtext("end")) * fps))
        out.append((team, start, end))
    return sorted(out)


def push(n, blocks, transitions, fps, weight=WEIGHT, cap_s=CAP_S):
    """(score, allowed) con el empujón de `transitions` ([(equipo, inicio, fin)]) en un tracking de n frames.

    Función pura: no abre nada. `blocks` son los tramos evaluados, como (inicio, fin) con el fin sin incluir.
    """
    score, allowed = no_evidence(n)
    covered = np.zeros((2, n), dtype=bool)
    cap = int(round(cap_s * fps))
    for team, start, end in transitions:
        block = next(((first, stop) for first, stop in blocks if first <= start < stop), None)
        if block is None:
            continue
        stop = min(start + cap, end, block[1], n)
        if stop > start:
            covered[team, start:stop] = True
    score[covered[H], H] = weight
    score[covered[A], A] = weight
    score[covered.any(axis=0), D] = weight  # neutral entre jugar y parar: solo empuja contra el otro equipo
    return score, allowed


def evidence(trk, paths=None, game=games.GAME):
    """La capa con la interfaz común. Sin `paths`, no opina y no abre nada; con `paths`, lee su Smart Tagging."""
    n = len(trk.bx)
    if paths is None:
        return no_evidence(n)
    fps = games.GAMES[game]["fps"]
    if int(trk.fps) != int(fps):
        raise ValueError("el tracking va a {} fps y el partido a {}".format(trk.fps, fps))
    found = transitions(paths["smart_tagging"], fps)
    if not found:
        raise ValueError("el Smart Tagging no tiene ninguna ATTACKING TRANSITION con Team de los de TEAMS: "
                         "revisa los nombres de los equipos")
    return push(n, trk.blocks, found, fps)
