"""¿Se traslada al ATD el modelo de estado de `D`? La referencia de la DFL para leer los agregados del partido.

    python validation/scripts/d_estado/traslado_atd.py

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del harness. Lo puede
ejecutar cualquiera, Claude incluido. Solo imprime agregados. Como los demás scripts de esta carpeta,
necesita `scikit-learn` (lo importan `entrenar.py` y `medir.py`).

Para qué: `validation/partido/agregados_jugadores.py`, que ejecuta una persona, imprime en sus puntos 4 y 6
cómo se mueven los jugadores del ATD, cuántos se ven y cuántos aparecen fuera del campo. Este script da:

A. Esas mismas medidas en la DFL, **partido a partido** (mínimo, mediana y máximo entre los 7). Es con lo
   que se fijaron los umbrales de la regla de lectura
   (validation/resultados/2026-11-14_agregados_jugadores_atd.md).
B. Qué hace la pieza si faltan jugadores a ratos. En la DFL están todos; en el ATD, no. Usa el `MODEL` del
   módulo, que ha visto estos partidos al entrenar: vale para comparar filas entre sí, no como nota.
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import entrenar  # noqa: E402
import medir  # noqa: E402
import puntuar  # noqa: E402
from possession import dead_state  # noqa: E402

D, X = entrenar.D, entrenar.X
SEMILLA = 20261114
LENTO = 1.2  # m/s: el corte de validation/partido/agregados_jugadores.py (SLOW_MS)
# (fracción del tiempo que falta cada slot, frames de media de cada hueco)
OCULTOS = (("están todos (como en la medida de la pieza)", None),
           ("falta el 7 % del tiempo, en bloques de 2 s", (0.07, 50)),
           ("falta el 7 % del tiempo, en bloques de 0,4 s", (0.07, 10)),
           ("falta el 20 % del tiempo, en bloques de 2 s", (0.20, 50)))


def num(valor, decimales=2):
    return ("{:." + str(decimales) + "f}").format(valor).replace(".", ",")


def referencias(cargados):
    print("A. Referencia de la DFL por partido ({} partidos, frames con etiqueta)".format(len(cargados)))
    print()
    filas = []
    for datos in cargados:
        trk, gt = datos["trk"], datos["gt"]["flag"]
        ok = gt != X
        velocidad = datos["rasgos"]["v_media_2s"][ok]
        lentos = datos["rasgos"]["frac_lentos_2s"][ok]
        fuera = dead_state.raw_series(trk)["fuera"][ok]
        vivo = gt[ok] != D
        filas.append({
            "p10": np.nanpercentile(velocidad, 10), "p50": np.nanpercentile(velocidad, 50),
            "p90": np.nanpercentile(velocidad, 90), "lento": 100.0 * np.nanmean(velocidad < LENTO),
            "frac_p50": np.nanpercentile(lentos, 50),
            "fuera1": 100.0 * np.mean(fuera >= 1), "fuera3": 100.0 * np.mean(fuera >= 3),
            "fuera1_vivo": 100.0 * np.mean(fuera[vivo] >= 1), "fuera1_d": 100.0 * np.mean(fuera[~vivo] >= 1),
            "vistos": float(np.median((~np.isnan(trk.px[ok])).sum(axis=1))), "d": 100.0 * np.mean(~vivo)})
    medidas = (("p10", "velocidad media en 2 s, p10 (m/s)"), ("p50", "velocidad media en 2 s, p50 (m/s)"),
               ("p90", "velocidad media en 2 s, p90 (m/s)"), ("lento", "% de frames por debajo de 1,2 m/s"),
               ("frac_p50", "fracción de jugadores a menos de 1 m/s, p50"),
               ("fuera1", "% de frames con 1 jugador o más fuera (más de 0,3 m)"),
               ("fuera3", "% de frames con 3 o más fuera"),
               ("fuera1_vivo", "% con 1 o más fuera, solo con el balón en juego"),
               ("fuera1_d", "% con 1 o más fuera, solo en `D`"),
               ("vistos", "slots vistos por frame, mediana"), ("d", "% de frames en `D`"))
    print("| medida | mínimo entre partidos | mediana | máximo |")
    print("|---|---|---|---|")
    for clave, texto in medidas:
        valores = np.array([fila[clave] for fila in filas])
        print("| {} | {} | {} | {} |".format(texto, num(valores.min()), num(np.median(valores)), num(valores.max())))
    print()


def ocultar(trk, fraccion, media, rng):
    """El tracking con cada slot desaparecido a ratos: huecos de `media` frames de media, `fraccion` del tiempo."""
    n, slots = trk.px.shape
    px, py = trk.px.copy(), trk.py.copy()
    visible = media * (1.0 - fraccion) / fraccion
    for slot in range(slots):
        oculto = np.zeros(n, dtype=bool)
        t = 0
        while t < n:
            t += int(rng.geometric(1.0 / visible))
            largo = int(rng.geometric(1.0 / media))
            oculto[t:t + largo] = True
            t += largo
        px[oculto, slot] = np.nan
        py[oculto, slot] = np.nan
    return trk._replace(px=px, py=py)


def faltan_jugadores(cargados):
    print("B. La pieza (el `MODEL` del módulo) si faltan jugadores a ratos, {} partidos juntos".format(len(cargados)))
    print()
    print("| jugadores | vistos por frame, mediana | frames que el modelo ve más `D` que juego | `D` real | paradas "
          "detectadas | inicio a ≤ 25 frames | fin a ≤ 25 frames | `D` espurios por minuto de juego | `spellF1` con "
          "equipo oráculo (flag, previo) | sin `D` |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for texto, prm in OCULTOS:
        paradas, con_d, sin_d, dice, es_d, vistos = [], [], [], [], [], []
        for indice, datos in enumerate(cargados):
            trk = datos["trk"]
            if prm:
                rng = np.random.default_rng([SEMILLA, indice, int(round(1000 * prm[0])), prm[1]])
                trk = ocultar(trk, prm[0], prm[1], rng)
            gt = datos["gt"]["flag"]
            ok = gt != X
            puntuacion = dead_state.log_odds(trk)
            mascara = medir.mascara_d(trk, puntuacion)
            paradas.append(medir.medir_paradas(gt, mascara, trk.blocks))
            con_d.append(medir.recuentos_spell(datos, mascara)[("flag", "previo")])
            sin_d.append(medir.recuentos_spell(datos, np.zeros(len(gt), dtype=bool))[("flag", "previo")])
            dice.append(puntuacion[ok] > 0)
            es_d.append(gt[ok] == D)
            vistos.append((~np.isnan(trk.px[ok])).sum(axis=1))
        fila = medir.juntar_paradas(paradas)
        print("| {} | {:.0f} | {} % | {} % | {} de {} ({:.0f} %) | {:.0f} % | {:.0f} % | {} | {} | {} |".format(
            texto, float(np.median(np.concatenate(vistos))), num(100.0 * np.mean(np.concatenate(dice)), 1),
            num(100.0 * np.mean(np.concatenate(es_d)), 1), fila["detectadas"], fila["paradas"],
            100.0 * fila["detectadas"] / max(fila["paradas"], 1), 100.0 * fila["inicio_ok"], 100.0 * fila["fin_ok"],
            num(fila["espurios_min"]), num(puntuar.spell_f1(*puntuar.juntar(con_d)), 3),
            num(puntuar.spell_f1(*puntuar.juntar(sin_d)), 3)))
    print()


def main():
    cargados = [entrenar.cargar(partido) for partido in entrenar.PARTIDOS]
    referencias(cargados)
    faltan_jugadores(cargados)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
