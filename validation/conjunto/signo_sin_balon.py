"""¿Qué sabe K2 cuando no ve el balón? El acierto del signo de z en frames de juego, con balón y sin él.

    python validation/conjunto/signo_sin_balon.py              # la DFL (vota) y SkillCorner (sin voto)

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, MIT). Lo puede ejecutar cualquiera, Claude incluido.
Solo imprime agregados. **No lee el examen de SkillCorner:** la lista pasa por `lector.exigir_solo_entrenamiento`.

Por qué (docs/decisiones.md, 17/11, K7). En Metrica, K2 acierta el signo de z en el 44,7 % de los frames vivos sin
balón: menos que una moneda. O no sabe nada sin balón, o las etiquetas de eventos de Metrica no casan con el balón en
los bordes de las paradas. Se mira en la DFL «como el ATD», donde los huecos en juego son bloques de 5 a 15 s y
microcortes, con las etiquetas de control, que son las que aprende z.

Cada partido se puntúa con el pliegue que no lo vio: K2 con el de `conjunto_pesos.npz` y B5 con el suyo. El acierto
es la parte de los frames (de los tramos evaluados, con `H` o `A` en la etiqueta) en que el signo del logit dice el
equipo de la etiqueta. Solo se suman frames: no se elige nada.
"""

import collections
import concurrent.futures
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import refinar  # noqa: E402  (importa medir, que pone en el camino harness/, cambios/, skillcorner/ y la raíz)
import cj_comun as cj  # noqa: E402
import lector  # noqa: E402
from comun import dfl, puntuar  # noqa: E402
from possession import aprendida, conjunto, pipeline  # noqa: E402
from possession import refinamientos as rf  # noqa: E402
from possession.tracking import A, H  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

UMBRAL = 0.60  # docs/decisiones.md, 17/11, K7: si K2 acierta sin balón el 60 % o más en la DFL «como el ATD»


def contar(trk, gts, fuera_k2, fuera_b5):
    """{(versión, etiquetas, balón): (bien, frames)} de un tracking."""
    limpio = pipeline.default_piece("ball")(trk)
    logits = {"K2": conjunto.salidas(limpio, fuera_k2)[0], "B5": rf.logit_b5(limpio, fuera_b5)}
    dentro = np.zeros(len(limpio.bx), dtype=bool)
    for a, b in limpio.blocks:
        dentro[a:b] = True
    visible = np.asarray(aprendida.balon_visible(limpio), dtype=bool)
    salida = {}
    for convencion, gt in gts.items():
        gt = np.asarray(gt)
        vivo = dentro & ((gt == H) | (gt == A))
        for version, s in logits.items():
            bien = np.where(gt == H, s > 0, s < 0)
            for balon, mascara in (("con balón", vivo & visible), ("sin balón", vivo & ~visible)):
                salida[(version, convencion, balon)] = (int((bien & mascara).sum()), int(mascara.sum()))
    return salida


def de_dfl(partido):
    inicio = time.time()
    cargado = dfl.cargar(partido)
    salida = {}
    for condicion in dfl.VOTAN:
        trk = puntuar.solo_lectura(dfl.tracking_de(cargado, condicion))
        gts = {c: cargado["gt"][c] for c in ("control", "flag")}
        for clave, valor in contar(trk, gts, partido, partido).items():
            salida[(condicion,) + clave] = valor
    return ("dfl", partido), salida, time.time() - inicio


def de_sc(id_):
    inicio = time.time()
    lector.exigir_solo_entrenamiento([id_])
    crudo = lector.leer_crudo(id_)
    salida = {}
    for condicion in lector.VOTAN:
        trk, gt = lector.tracking_de(crudo, condicion, id_)
        for clave, valor in contar(puntuar.solo_lectura(trk), {"sc": gt}, cj.pliegue_de("sc", id_), None).items():
            salida[(condicion,) + clave] = valor
    return ("sc", id_), salida, time.time() - inicio


def tabla(resultados, claves, partidos):
    print("| condición | etiquetas | versión | balón | frames | acierto | peor partido | mejor partido |")
    print("|---|---|---|---|---|---|---|---|")
    for clave in claves:
        bien = sum(resultados[p][clave][0] for p in partidos)
        total = sum(resultados[p][clave][1] for p in partidos)
        por_partido = [resultados[p][clave][0] / max(resultados[p][clave][1], 1) for p in partidos]
        print("| {} | {} | {} | {} | {} | {:.1f} % | {:.1f} % | {:.1f} % |".format(
            clave[0], clave[2], clave[1], clave[3], total, 100.0 * bien / max(total, 1),
            100.0 * min(por_partido), 100.0 * max(por_partido)))


def main():
    refinar.exigir_b5_en_main()
    lector.exigir_solo_entrenamiento(list(cj.SKILLCORNER))
    trabajos = [(de_dfl, p) for p in cj.DFL] + [(de_sc, p) for p in cj.SKILLCORNER]
    resultados = {}
    with concurrent.futures.ProcessPoolExecutor(2) as pool:
        futuros = [pool.submit(f, p) for f, p in trabajos]
        for futuro in futuros:
            clave, valor, segundos = futuro.result()
            resultados[clave] = valor
            print("# hecho {} {} en {:.0f} s".format(clave[0], clave[1], segundos), file=sys.stderr, flush=True)

    print("# El signo de z sin balón: DFL (vota) y SkillCorner (sin voto)\n")
    print("Código: {} · pesos de K2: `conjunto_pesos.npz` (sha256 {}…), el pliegue que no vio cada partido · B5: el "
          "pliegue que no vio el partido en la DFL; los de la entrega en SkillCorner · este script: sha256 {}…".format(
              puntuar.version_del_codigo(), refinar.huella(conjunto.PESOS), refinar.huella(os.path.abspath(__file__))))
    dfl_partidos = [("dfl", p) for p in cj.DFL]
    sc_partidos = [("sc", p) for p in cj.SKILLCORNER]
    print("\n## DFL, 7 partidos\n")
    tabla(resultados, [(c, v, e, b) for c in dfl.VOTAN for e in ("control", "flag") for v in ("K2", "B5")
                       for b in ("con balón", "sin balón")], dfl_partidos)
    print("\n## SkillCorner, mitad de entrenamiento, 10 partidos (sin voto)\n")
    tabla(resultados, [(c, v, "sc", b) for c in lector.VOTAN for v in ("K2", "B5") for b in ("con balón", "sin balón")],
          sc_partidos)

    clave = (dfl.VOTAN[0], "K2", "control", "sin balón")
    bien = sum(resultados[p][clave][0] for p in dfl_partidos)
    total = sum(resultados[p][clave][1] for p in dfl_partidos)
    acierto = bien / max(total, 1)
    print("\n## La regla\n")
    print("- K2 sin balón, DFL «como el ATD», etiquetas de control: {:.1f} % (umbral {:.0f} %) → **{}**".format(
        100.0 * acierto, 100.0 * UMBRAL,
        "en los trozos de Metrica, los frames vivos sin balón crudo no cuentan en la pérdida" if acierto >= UMBRAL
        else "Metrica entra entera en la pérdida"))


if __name__ == "__main__":
    main()
