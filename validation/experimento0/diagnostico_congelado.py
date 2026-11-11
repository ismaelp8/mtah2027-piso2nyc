"""Diagnóstico de la parada 3: cuánto afecta el balón congelado durante los `D` a toques, controles y 2g.

Reproduce los recuentos que llevaron a añadir la variante "solo en juego" (bitácora, sección 7) y la
comprobación de que el flag no cambia dentro de las paradas que acaban en un reinicio. Usa los
parámetros principales con todos los frames, como la variante original. Solo imprime agregados.

Uso:
    python validation/experimento0/diagnostico_congelado.py
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
import medidas_cambios as mc  # noqa: E402


def main():
    prm = mc.PARAMETROS
    tot = dict(toques=0, toques_en_borde_de_D=0, controles=0, controles_con_frames_D=0, cambios=0,
               cambios_con_D_en_ventana_2b=0, casos_2g=0, casos_2g_con_D_antes=0,
               paradas_con_reinicio=0, paradas_flag_constante=0)
    for p in etiquetas_dfl.PARTIDOS:
        d = dfl_lector.cargar_cache(p)
        for k in (1, 2):
            parte = d["partes"][k]
            e = np.asarray(parte["estado"])
            poss = np.asarray(parte["poss"])
            n = len(e)
            inact = np.concatenate(([0], np.cumsum(e != 1)))
            prep = mc.preparar(parte)
            tt, eq, _ = mc.toques(prep, prm["umbral_toque"], prm["radio_toque"])
            lo, hi = np.clip(tt - 4, 0, n), np.clip(tt + 6, 0, n)
            tot["toques"] += len(tt)
            tot["toques_en_borde_de_D"] += int(np.sum(inact[hi] - inact[lo] > 0))
            segs = mc.controles(prep, prm["radio"], prm["frames_control"])
            tot["controles"] += len(segs)
            tot["controles_con_frames_D"] += sum(1 for a, b, *_ in segs if inact[b] - inact[a] > 0)
            f, _, _ = mc.cambios(e, poss)
            tot["cambios"] += len(f)
            tot["cambios_con_D_en_ventana_2b"] += int(sum(
                inact[min(n, fi + prm["ventana_despues"] + 1)] - inact[max(0, fi - prm["ventana_antes"])] > 0 for fi in f))
            casos = mc.toques_sin_control(tt, eq, segs, e, poss, prep["z"])
            fines = np.array(sorted(s[1] for s in segs))
            for c in casos:
                tot["casos_2g"] += 1
                pe = fines[fines <= c["t"]].max()
                tot["casos_2g_con_D_antes"] += int(inact[c["t"] + 1] - inact[pe] > 0)
            ini = np.flatnonzero((e[1:] == 0) & (e[:-1] == 1)) + 1
            fin = np.flatnonzero((e[1:] == 1) & (e[:-1] == 0)) + 1
            for a in ini:
                b = fin[fin > a]
                if len(b):
                    tot["paradas_con_reinicio"] += 1
                    tot["paradas_flag_constante"] += int(np.all(poss[a:b[0]] == poss[a]))
    print(json.dumps(tot, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
