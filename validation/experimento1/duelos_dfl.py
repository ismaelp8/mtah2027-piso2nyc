"""Experimento 1: los duelos anotados en los eventos de la DFL frente al flag de posesión.

Cruza cada `TacklingGame` (con `PossessionChange`, `WinnerRole`/`LoserRole` y `WinnerResult`) con el
flag `BallPossession` de las posiciones, con la medida fijada en `validation/experimento1/BITACORA.md`
antes de mirar. Datos abiertos de otros partidos (Bassek et al., 2025). Solo imprime agregados.

Uso:
    python validation/experimento1/duelos_dfl.py
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
from parada3 import a_frame, _ms  # noqa: E402

FPS = 25
ANTES, DESPUES = 2 * FPS, 3 * FPS


def duelos(ruta, meta):
    """[(ms, equipo X (0/1), dict de atributos)] de los TacklingGame con hora y roles."""
    salida = []
    for e in etree.parse(ruta).getroot().findall("Event"):
        if not len(e) or e[0].tag != "TacklingGame" or e.get("EventTime") is None:
            continue
        a = dict(e[0].attrib)
        if a.get("WinnerRole") == "withBallControl":
            x = a.get("WinnerTeam")
        elif a.get("LoserRole") == "withBallControl":
            x = a.get("LoserTeam")
        else:
            x = None
        eq = {meta["local_id"]: 0, meta["visitante_id"]: 1}.get(x, -1)
        salida.append((_ms(e.get("EventTime")), eq, a))
    return salida


def grupo(a):
    if a.get("PossessionChange") == "true":
        return "G1 cambio de posesión"
    if a.get("WinnerRole") == "withoutBallControl":
        return "G2 sin cambio, gana el que no tenía el balón"
    return "G3 sin cambio, gana el que tenía el balón"


def main():
    tabla = collections.Counter()
    m1 = collections.defaultdict(list)
    por_partido = collections.defaultdict(lambda: collections.defaultdict(list))
    descartes = collections.Counter()
    for p in etiquetas_dfl.PARTIDOS:
        datos = dfl_lector.cargar_cache(p)
        meta = datos["meta"]
        for ms, x, a in duelos(dfl_lector.rutas_partido(p)["eventos"], meta):
            tabla[(a.get("PossessionChange"), a.get("WinnerRole"), a.get("WinnerResult"))] += 1
            if x < 0:
                descartes["sin equipo con el balón"] += 1
                continue
            parte = None
            for k in (1, 2):
                t = datos["partes"][k]["t_ms"]
                if t[0] <= ms <= t[-1]:
                    parte = datos["partes"][k]
            if parte is None:
                descartes["fuera de las partes"] += 1
                continue
            f = a_frame(np.asarray(parte["t_ms"], np.int64), ms)
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            if estado[f] != 1:
                descartes["balón inactivo en el frame del evento"] += 1
                continue
            lo, hi = max(0, f - ANTES), min(len(estado), f + DESPUES + 1)
            y = 1 - x
            marca_y = bool(np.any((estado[lo:hi] == 1) & (poss[lo:hi] - 1 == y)))
            g = grupo(a)
            claves = [g, g + " · " + str(a.get("WinnerResult")), g + " · " + str(a.get("Type"))]
            for c in claves:
                m1[c].append(marca_y)
            por_partido[p][g].append(marca_y)
    print("Duelos por PossessionChange, WinnerRole y WinnerResult (los 7):")
    for (pc, wr, res), n in sorted(tabla.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]), -kv[1])):
        print("  PossessionChange={} WinnerRole={} WinnerResult={}: {}".format(pc, wr, res, n))
    print("Descartes:", dict(descartes))
    salida = {c: {"n": len(v), "flag_marca_Y_pct": round(100.0 * sum(v) / len(v), 1)} for c, v in sorted(m1.items())}
    print("M1 (flag marca a Y entre −2 s y +3 s), los 7:")
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    print("M1 por partido (G1 / G2 / G3, %):")
    for p, gs in por_partido.items():
        print("  {}: {}".format(p, " | ".join("{} n={} {:.1f}".format(g[:2], len(v), 100.0 * sum(v) / len(v))
                                              for g, v in sorted(gs.items()))))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
