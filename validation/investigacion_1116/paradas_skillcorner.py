"""Sondeo S4: ¿quedan en SkillCorner bastantes paradas con tracking para validar sus bordes?

    python validation/investigacion_1116/paradas_skillcorner.py

Datos abiertos de otros partidos (mitad de entrenamiento de SkillCorner, licencia MIT): lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. La regla de lectura está en BITACORA.md (S4), escrita
antes de contar.
"""

import collections
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "skillcorner"))
import lector as lc  # noqa: E402

FPS = lc.FPS_ORIGEN  # 10
CON_TRACKING = 0.8
TRAMOS_DURACION = ((0, 5), (5, 15), (15, 40), (40, 1e9))  # segundos


def rachas(mascara):
    borde = np.diff(np.concatenate(([0], mascara.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(borde == 1), np.flatnonzero(borde == -1)))


def main():
    ids = list(lc.ENTRENAMIENTO)
    lc.exigir_solo_entrenamiento(ids)
    por_duracion = collections.Counter()
    con_tracking = collections.Counter()
    balon_fin = collections.Counter()
    balon_despues = collections.Counter()
    tipos = collections.Counter()
    tipos_con = collections.Counter()
    interrupciones = collections.Counter()
    total = 0
    for id_ in ids:
        crudo = lc.leer_crudo(id_)
        detectado = crudo["pdet"].any(axis=1)
        balon = crudo["bdet"] & np.isfinite(crudo["bx"])
        eventos = pd.read_csv(lc.carpeta() / str(id_) / "{}_dynamic_events.csv".format(id_), low_memory=False)
        pp = eventos[eventos["event_type"] == "player_possession"].sort_values("frame_start")
        inicio_pp = pp["frame_start"].to_numpy()
        tipo_pp = pp["start_type"].fillna("sin dato").astype(str).to_numpy()
        for col in ("game_interruption_before", "game_interruption_after"):
            if col in eventos:
                for valor, n in eventos[col].dropna().astype(str).value_counts().items():
                    interrupciones[(col, valor)] += int(n)
        for a, b in crudo["partes"]:
            a, b = int(a), int(b) + 1
            for i, j in rachas(~crudo["fases"][a:b]):
                if i == 0 or j == b - a:
                    continue  # antes del saque y después del final: no es una parada entre dos jugadas
                i, j = a + i, a + j
                total += 1
                seg = (j - i) / FPS
                tramo = next(k for k, (lo, hi) in enumerate(TRAMOS_DURACION) if lo <= seg < hi)
                por_duracion[tramo] += 1
                k = int(np.searchsorted(inicio_pp, j - 5))
                tipo = tipo_pp[k] if k < len(tipo_pp) and inicio_pp[k] <= j + 5 * FPS else "sin posesión detrás"
                tipos[tipo] += 1
                if detectado[i:j].mean() >= CON_TRACKING:
                    con_tracking[tramo] += 1
                    tipos_con[tipo] += 1
                    balon_fin[tramo] += int(balon[max(i, j - FPS):j].any())
                    balon_despues[tramo] += int(balon[j:min(j + FPS, b)].any())
    print("partidos: {} · paradas entre dos fases de juego: {} ({:.0f} por partido)".format(len(ids), total, total / len(ids)))
    print()
    print("| duración | paradas | con jugadores detectados en el 80 % de sus frames | de esas, balón visto en su último segundo | de esas, balón visto en el primer segundo de juego |")
    print("|---|---|---|---|---|")
    for k, (lo, hi) in enumerate(TRAMOS_DURACION):
        nombre = "{:g}–{:g} s".format(lo, hi) if hi < 1e9 else "≥ {:g} s".format(lo)
        print("| {} | {} | {} | {} | {} |".format(nombre, por_duracion[k], con_tracking[k], balon_fin[k], balon_despues[k]))
    print("| **todas** | {} | {} | {} | {} |".format(sum(por_duracion.values()), sum(con_tracking.values()),
                                                 sum(balon_fin.values()), sum(balon_despues.values())))
    print("\n`start_type` de la primera posesión de jugador tras cada parada (todas / con tracking):\n")
    print("| tipo | paradas | con tracking |")
    print("|---|---|---|")
    for tipo, n in tipos.most_common():
        print("| {} | {} | {} |".format(tipo, n, tipos_con[tipo]))
    print("\nValores de `game_interruption_*` en los eventos (recuento de filas):\n")
    for (col, valor), n in sorted(interrupciones.items(), key=lambda kv: -kv[1])[:24]:
        print("- {} = {}: {}".format(col, valor, n))


if __name__ == "__main__":
    main()
