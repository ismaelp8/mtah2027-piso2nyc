"""¿Con cuánto retraso pasa el modelo de Ana de parado a juego al acabar una parada? En la DFL, por tipo de reinicio.

Es la medida de los dos números que Ana pidió restar al ancla del instante del reinicio (`DFL_DELAY` de
`validation/partido/agregados_instante_reinicio.py`; `docs/decisiones.md`, 15/11, «el instante del reinicio»,
añadidos de Ana). Solo lee los 7 partidos abiertos de la DFL, nunca el partido: lo puede ejecutar Claude.

    python validation/scripts/d_estado/retraso_transicion.py

Qué hace, partido a partido y dejando ese partido fuera al entrenar el modelo E2 (como `medir.py`):
- cada parada es una racha de `D` de la DFL que acaba dentro de un tramo; su tipo es el del reinicio de los eventos
  humanos de la DFL más cercano a su fin, entre 10 s antes y 3 s después (si no hay ninguno, «(ninguno)»);
- la transición es la misma señal que en el partido: el primer frame con log-odds > 0 en el anterior y < 0 durante
  los 2 s siguientes. Se busca desde el inicio de la parada hasta 10 s después de su fin (en el partido, desde el
  inicio de la ventana `SET PIECES`: es la salvedad de Ana);
- imprime, por tipo, la transición menos el fin real en frames (positivo: llega tarde) y cuántas caen a menos de
  1 s del fin real.

El retraso que se resta al ancla es la mediana de los tipos con 50 paradas o más con transición y la transición
tarde (mediana positiva). Una mediana negativa no es un retraso: la transición llega antes del fin real.

Solo imprime agregados de datos abiertos. Hace falta la caché de la DFL y `scikit-learn` (README de esta carpeta).
"""

import collections
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for folder in ("validation/scripts/d_estado", "validation/harness", "validation/experimento0", ""):
    sys.path.insert(0, os.path.join(ROOT, folder))
import dfl  # noqa: E402
import dfl_lector  # noqa: E402
import entrenar  # noqa: E402
import parada3  # noqa: E402
from possession import dead_state, tracking  # noqa: E402

D, FPS = tracking.D, 25
SUSTAIN = 2 * FPS  # el mismo sostén que agregados_instante_reinicio.SUSTAIN_S
BEFORE_END, AFTER_END = 10 * FPS, 3 * FPS  # dónde se busca el reinicio que da el tipo, desde el fin de la parada
SEARCH_AFTER = 10 * FPS  # hasta dónde se busca la transición después del fin real
NEAR = FPS  # «a menos de 1 s del fin real»
MIN_STOPS = 50  # paradas con transición para que el tipo tenga una medida propia
# Nombres de los eventos de la DFL frente a los tipos del Smart Tagging del partido (en minúsculas).
SMART_TAGGING = {"ThrowIn": "throw-in", "CornerKick": "corner kick", "FreeKick": "free kick", "GoalKick": "goal kick"}


def runs(mask):
    edges = np.diff(np.concatenate(([0], np.asarray(mask, np.int8), [0])))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def restarts_of(match):
    """[(tipo, frame)] de los reinicios de los eventos humanos de la DFL, en frames del tracking del harness."""
    loaded = dfl.cargar(match)
    meta = dfl_lector.cargar_cache(match)["meta"]
    events = parada3.leer_eventos(dfl_lector.rutas_partido(match)["eventos"], meta)
    halves = loaded["partes"]
    offset = {1: 0, 2: len(halves[1]["estado"]) + dfl.HUECO}
    out = []
    for half in (1, 2):
        for kind, frame, _ in parada3.reinicios_de_la_parte(events, np.asarray(halves[half]["t_ms"], np.int64)):
            out.append((kind, offset[half] + frame))
    return out


def first_transition(odds, start, stop):
    for t in range(start, stop):
        if odds[t - 1] > 0 and np.all(odds[t:t + SUSTAIN] < 0):
            return t
    return None


def measure():
    """{tipo: (paradas, sin transición, [transición − fin real, en frames])}."""
    stops, missing, offsets = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    loaded = [entrenar.cargar(match) for match in entrenar.PARTIDOS]
    for i, match in enumerate(loaded):
        model = entrenar.ajustar([m for j, m in enumerate(loaded) if j != i], dead_state.E2)
        odds = dead_state.log_odds(match["trk"], model)
        gt = match["gt"]["flag"]  # el `D` es el mismo en las dos convenciones
        restarts = restarts_of(match["partido"])
        frames = np.array([f for _, f in restarts])
        kinds = [k for k, _ in restarts]
        for a, b in match["trk"].blocks:
            for start, end in runs(gt[a:b] == D):
                start, end = a + start, a + end
                if end >= b:
                    continue  # la parada llega al final del tramo: no tiene fin
                near = np.flatnonzero((frames >= end - BEFORE_END) & (frames <= end + AFTER_END))
                kind = kinds[near[np.argmin(np.abs(frames[near] - end))]] if len(near) else "(ninguno)"
                stops[kind] += 1
                t = first_transition(odds, max(start, a + 1), min(b - SUSTAIN, end + SEARCH_AFTER))
                if t is None:
                    missing[kind] += 1
                else:
                    offsets[kind].append(t - end)
    return {kind: (stops[kind], missing[kind], offsets[kind]) for kind in stops}


def delays(result):
    """El retraso para el ancla, con los nombres del Smart Tagging: mediana redondeada de los tipos con MIN_STOPS
    paradas o más con transición y mediana positiva."""
    out = {}
    for kind, (_, _, values) in result.items():
        if kind in SMART_TAGGING and len(values) >= MIN_STOPS and np.median(values) > 0:
            out[SMART_TAGGING[kind]] = int(round(float(np.median(values))))
    return out


def main():
    result = measure()
    print("| reinicio | paradas | sin transición | transición − fin real: p10 / p25 / p50 / p75 / p90 (frames)"
          " | a < 1 s del fin real |")
    print("|---|---|---|---|---|")
    everything = []
    for kind in sorted(result, key=lambda k: -result[k][0]):
        n, none, values = result[kind]
        everything += values
        if len(values) < 5:
            print("| {} | {} | {} | (menos de 5) | |".format(kind, n, none))
            continue
        q = np.percentile(values, [10, 25, 50, 75, 90])
        print("| {} | {} | {} | {} | {:.0f} % |".format(kind, n, none, " / ".join("{:+.0f}".format(x) for x in q),
                                                      100 * np.mean(np.abs(values) < NEAR)))
    q = np.percentile(everything, [10, 25, 50, 75, 90])
    print("| todas | {} | {} | {} | {:.0f} % |".format(sum(r[0] for r in result.values()),
                                                      sum(r[1] for r in result.values()),
                                                      " / ".join("{:+.0f}".format(x) for x in q),
                                                      100 * np.mean(np.abs(everything) < NEAR)))
    print("\nretraso para el ancla (≥ {} paradas con transición y mediana positiva), con los nombres del Smart"
          " Tagging: {}".format(MIN_STOPS, delays(result)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
