"""Experimento 1: cuánto se separan "toque con impacto significativo" (Metrica) y "control establecido".

Casos de 2g (toque del rival sin control entre dos controles del mismo equipo, ≤ 5 s, sin `D`;
variante original del experimento 0), clasificados con los pases de los eventos (bitácora, sección 12):
mismo jugador, pase que llega (desvío que no corta el pase) y balón suelto recuperado. Datos abiertos
de otros partidos (Bassek et al., 2025). Solo imprime agregados.

Uso:
    python validation/experimento1/lecturas_toque.py
"""

import collections
import json
import os
import sys

import numpy as np
from lxml import etree

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
import medidas_cambios as mc  # noqa: E402
from parada3 import _ms  # noqa: E402

FPS = 25
VENTANA_MS = 3000


def pases_completados(ruta):
    """[(ms, pasador, receptor)] de los pases completados con receptor."""
    salida = []
    for e in etree.parse(ruta).getroot().findall("Event"):
        if not len(e) or e.get("EventTime") is None:
            continue
        h = e[0]
        if h.tag == "Play" and h.get("Evaluation") == "successfullyCompleted" and h.get("Recipient"):
            salida.append((_ms(e.get("EventTime")), h.get("Player"), h.get("Recipient")))
    return salida


def main():
    clases = collections.defaultdict(list)
    por_partido = collections.defaultdict(collections.Counter)
    for p in etiquetas_dfl.PARTIDOS:
        datos = dfl_lector.cargar_cache(p)
        pases = pases_completados(dfl_lector.rutas_partido(p)["eventos"])
        for k in (1, 2):
            parte = datos["partes"][k]
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            t_ms = np.asarray(parte["t_ms"], np.int64)
            personas = [str(x) for x in parte["equipos"]["local"]["personas"]] + \
                       [str(x) for x in parte["equipos"]["visitante"]["personas"]]
            prep = mc.preparar(parte)
            segs = sorted(mc.controles(prep, 1.0, 12))
            t, eq, _ = mc.toques(prep, 3.0, 1.5)
            casos = mc.toques_sin_control(t, eq, segs, estado, poss, prep["z"])
            fines = np.array([s[1] for s in segs])
            inicios = np.array([s[0] for s in segs])
            for c in casos:
                ant = segs[int(np.flatnonzero(fines <= c["t"])[-1])]
                sig = segs[int(np.flatnonzero(inicios > c["t"])[0])]
                j1, j2 = personas[ant[3]], personas[sig[3]]
                if j1 == j2:
                    clase = "mismo jugador"
                else:
                    ms = t_ms[c["t"]]
                    llega = any(abs(m - ms) <= VENTANA_MS and pa == j1 and re == j2 for m, pa, re in pases)
                    clase = "pase que llega" if llega else "balón suelto recuperado"
                clases[clase].append(c["cambia"])
                por_partido[p][clase] += 1
    total = sum(len(v) for v in clases.values())
    salida = {k: {"casos": len(v), "reparto_pct": round(100.0 * len(v) / total, 1),
                  "flag_pasa_al_rival_pct": round(100.0 * sum(v) / len(v), 1)} for k, v in sorted(clases.items())}
    print(json.dumps({"casos": total, "clases": salida,
                      "por_partido": {p: dict(c) for p, c in por_partido.items()}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
