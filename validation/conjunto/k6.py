"""K6a: la media de las z de los 8 juegos de pesos de K2 (los 7 pliegues y «todos»), sin entrenar, en Metrica.

    python validation/conjunto/k6.py                  # los 3 partidos de Metrica
    python validation/conjunto/k6.py --procesos 3

Datos abiertos de otros partidos (Metrica sample-data). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime
agregados. No lee la DFL ni SkillCorner: allí 7 de los 8 juegos de pesos vieron cada partido, y la media no se puede
puntuar sin que lo haya visto.

**Qué es** (docs/decisiones.md, 17/11, «K6a», escrita antes de medir). `possession/conjunto_pesos.npz` trae 8 juegos
de pesos de K2: uno por pliegue de la DFL (cada uno sin un partido de la DFL y uno o dos de SkillCorner) y el de
«todos», el de la entrega. Ninguno vio Metrica. K6a es la media de sus 8 z, con la α de «todos» (la de la entrega), y
se puntúa como K2. Es un filtro: dice si promediar modelos de K2 ayuda en un proveedor que ninguno vio, para decidir
si merece la pena entrenar semillas. No es un candidato a la entrega.

No toca `possession/conjunto.py`, sus pesos ni `refinar.py`: `conjunto.pesos(fuera)` ya da el juego de cada pliegue, y
`main`, K2, K3 y el `D` se montan con las mismas funciones que `refinar.py` (B5, `dead_state` y el decodificador de la
entrega). K2 y K3 tienen que salir iguales que en `salidas/2026-11-17_refinar_metrica.md`: es la comprobación del
instrumento.
"""

import argparse
import collections
import concurrent.futures
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import refinar  # noqa: E402  (importa medir, que pone en el camino harness/, cambios/ y la raíz)
import medir  # noqa: E402
import cj_comun as cj  # noqa: E402
import comun as cc  # noqa: E402
from comun import puntuar  # noqa: E402
from possession import aprendida, conjunto, pipeline  # noqa: E402
from possession import refinamientos as rf  # noqa: E402
from possession.tracking import A, H  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

JUEGOS = (None,) + cj.DFL  # «todos» y los 7 pliegues: los 8 juegos de conjunto_pesos.npz
NOMBRE_JUEGO = {None: "todos"}
VOTA = "K6a"
SIN_VOTO = ("K6a, 7 pliegues", "K6a, α de cada juego", "K3", "K6a con B5")
VERSIONES = ("K2", VOTA) + SIN_VOTO
MEDIA_MIN, PEOR_MIN = 0.003, -0.002  # K6a frente a K2: media de las 4 celdas y peor celda (docs/decisiones.md, 17/11)
MODOS = ("oraculo", "propio")
CONVENCION = "eventos"
# La comprobación del instrumento: (`main`, K2) en cada celda, a tres decimales, como salen en
# `validation/conjunto/salidas/2026-11-17_refinar_metrica.md` (código 74f3191, los mismos pesos).
PUBLICADAS = {("tal cual", "oraculo"): (0.668, 0.703), ("suavizado 25", "oraculo"): (0.652, 0.688),
              ("tal cual", "propio"): (0.542, 0.563), ("suavizado 25", "propio"): (0.527, 0.551)}


def media(valores):
    """La media de una lista de arrays, sumando en el orden de la lista."""
    total = 0.0
    for v in valores:
        total = total + v
    return total / float(len(valores))


def logits(limpio):
    """{versión: logit ya en su escala} y las z sin escalar de K2, K6a y la media de los 7 pliegues."""
    zs = {fuera: conjunto.salidas(limpio, fuera)[0] for fuera in JUEGOS}
    alfas = {fuera: float(conjunto.pesos(fuera)["alfa"]) for fuera in JUEGOS}
    alfa = alfas[None]
    z = {"K2": zs[None], "K6a": media([zs[f] for f in JUEGOS]), "K6a, 7 pliegues": media([zs[f] for f in cj.DFL])}
    s_b5 = rf.logit_b5(limpio)
    salida = {"K2": alfa * z["K2"], "K6a": alfa * z["K6a"], "K6a, 7 pliegues": alfa * z["K6a, 7 pliegues"],
              "K6a, α de cada juego": media([alfas[f] * zs[f] for f in JUEGOS]),
              "K3": rf.mezclar(alfa * z["K2"], s_b5), "K6a con B5": rf.mezclar(alfa * z["K6a"], s_b5)}
    return salida, z


def acierto_por_frame(z, gt, piezas):
    """{(versión, con o sin balón): (frames en que el signo de z dice el equipo de la etiqueta, frames)}, en los
    frames de juego de los tramos con equipo en la etiqueta."""
    dentro = np.zeros(len(gt), dtype=bool)
    for a, b in piezas["blocks"]:
        dentro[a:b] = True
    gt = np.asarray(gt)
    vivo = dentro & ((gt == H) | (gt == A))
    visible = np.asarray(piezas["visible"], dtype=bool)
    salida = {}
    for nombre, valores in z.items():
        bien = np.where(gt == H, valores > 0, valores < 0)
        for balon, mascara in (("con balón", vivo & visible), ("sin balón", vivo & ~visible)):
            salida[(nombre, balon)] = (int((bien & mascara).sum()), int(mascara.sum()))
    return salida


def medir_metrica(id_):
    inicio = time.time()
    lc = refinar.lector_metrica()
    crudo = lc.leer(id_)
    recuentos, aciertos = {}, collections.Counter()
    for condicion in lc.CONDICIONES:
        trk, gt = lc.tracking_de(crudo, condicion, id_)
        piezas = medir._piezas(puntuar.solo_lectura(trk), gt, None)
        escalados, z = logits(piezas["limpio"])
        for modo in MODOS:
            versiones = {"main": medir._decodificar(piezas, piezas["b5"], modo)}
            for nombre in VERSIONES:
                mio = aprendida.puntuacion_de("b5", escalados[nombre], piezas["visible"], 1.0, piezas["cercano"])
                versiones[nombre] = medir._decodificar(piezas, mio, modo)
            for (clave, convencion), valor in medir._recuentos(versiones, {CONVENCION: gt}).items():
                recuentos[(clave, condicion, modo, convencion)] = valor
        for (nombre, balon), (bien, total) in acierto_por_frame(z, gt, piezas).items():
            aciertos[(nombre, condicion, balon, "bien")] += bien
            aciertos[(nombre, condicion, balon, "total")] += total
    return id_, recuentos, dict(aciertos), time.time() - inicio


def tabla(recuentos, partidos, celdas, clave, contras, n_draws):
    """Una tabla de `clave` frente a cada versión de `contras`. Devuelve {celda: {contra: diferencia}}."""
    print("\n## {}{}\n".format(clave, "" if clave == VOTA or clave == "K2" else " (sin voto)"))
    cabecera = " | ".join("{0} − {1} [5–95 %] | gana a {1} en".format(clave, c) for c in contras)
    print("| `D` | condición | {} | {} |".format(" | ".join(("main", "K2", clave) if clave != "K2" else ("main", "K2")),
                                              cabecera))
    print("|---|---|" + "---|" * (3 if clave != "K2" else 2) + "---|---|" * len(contras))
    salida = {}
    for celda in celdas:
        condicion, modo, _ = celda
        notas = [cc.spell([recuentos[p][(v,) + celda] for p in partidos]) for v in
                 (("main", "K2", clave) if clave != "K2" else ("main", "K2"))]
        partes, salida[celda] = [], {}
        for contra in contras:
            _, _, dif, intervalo, gana = refinar.comparar(recuentos, partidos, clave, celda, contra, n_draws)
            salida[celda][contra] = dif
            partes.append("{:+.3f} {} | {} de {}".format(dif, medir.rango(intervalo), gana, len(partidos)))
        print("| {} | {} | {} | {} |".format(medir.NOMBRE_MODO[modo], condicion,
                                             " | ".join("{:.3f}".format(v) for v in notas), " | ".join(partes)))
    predichas = {v: sum(recuentos[p][(v,) + celdas[0]]["n_pred"] for p in partidos) for v in ("main", "K2", clave)}
    print("\nPosesiones predichas en la primera celda: {}, {} · K2, {} · `main`, {} (reales: {}).".format(
        clave, predichas[clave], predichas["K2"], predichas["main"],
        sum(recuentos[p][("main",) + celdas[0]]["n_gt"] for p in partidos)))
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--partidos", nargs="*", default=None, help="por defecto, los 3 de Metrica")
    parser.add_argument("--procesos", type=int, default=3)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    refinar.exigir_b5_en_main()
    lc = refinar.lector_metrica()
    partidos = [int(p) for p in (args.partidos or lc.partidos())]
    if not partidos:
        sys.exit("No hay partidos de Metrica bajados, en {}".format(lc.carpeta()))
    alfas = {NOMBRE_JUEGO.get(f, f): float(conjunto.pesos(f)["alfa"]) for f in JUEGOS}

    recuentos, aciertos = {}, collections.Counter()
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for partido, valor, acierto, segundos in pool.map(medir_metrica, partidos):
            recuentos[partido] = valor
            aciertos.update(acierto)
            print("# hecho {} en {:.0f} s".format(partido, segundos), file=sys.stderr, flush=True)

    celdas = [(c, m, CONVENCION) for m in MODOS for c in lc.CONDICIONES]
    print("# K6a: la media de los 8 juegos de pesos de K2, sin entrenar · Metrica · {} partidos\n".format(len(partidos)))
    print("Código: {} · bootstrap pareado de {} · `main` = B5, `dead_state` y `{}` · pesos: `conjunto_pesos.npz` "
          "(sha256 {}…), los 8 juegos · este script: sha256 {}…".format(
              puntuar.version_del_codigo(), args.bootstrap, pipeline.PIECES["temporal"], refinar.huella(conjunto.PESOS),
              refinar.huella(os.path.abspath(__file__))))
    print("α de K2, K6a y la media de los 7 pliegues: {:g}, la de «todos». α de cada juego: {}.".format(
        alfas["todos"], ", ".join("{} {:g}".format(k, v) for k, v in alfas.items())))
    print("Votan las cuatro celdas: «tal cual» y «suavizado 25», con el `D` de las etiquetas y con el propio.")

    print("\n## Comprobación del instrumento (antes de leer nada)\n")
    print("Con un solo juego, «todos», K2 y `main` tienen que dar lo publicado en "
          "`salidas/2026-11-17_refinar_metrica.md`.\n")
    print("| `D` | condición | `main` publicado / ahora | K2 publicado / ahora | ¿coincide? |")
    print("|---|---|---|---|---|")
    instrumento = True
    for celda in celdas:
        condicion, modo, _ = celda
        ahora = tuple(round(cc.spell([recuentos[p][(v,) + celda] for p in partidos]), 3) for v in ("main", "K2"))
        igual = ahora == PUBLICADAS[(condicion, modo)] if len(partidos) == 3 else False
        instrumento = instrumento and igual
        print("| {} | {} | {:.3f} / {:.3f} | {:.3f} / {:.3f} | {} |".format(
            medir.NOMBRE_MODO[modo], condicion, PUBLICADAS[(condicion, modo)][0], ahora[0],
            PUBLICADAS[(condicion, modo)][1], ahora[1], "sí" if igual else "**no**"))
    if not instrumento:
        print("\n**El instrumento no da lo publicado: no se lee nada de lo que sigue.**")
        sys.exit(1)

    tabla(recuentos, partidos, celdas, "K2", ("main",), args.bootstrap)
    resumen = tabla(recuentos, partidos, celdas, VOTA, ("main", "K2"), args.bootstrap)
    for clave in SIN_VOTO:
        contras = ("main", "K3") if clave == "K6a con B5" else ("main", "K2")
        tabla(recuentos, partidos, celdas, clave, contras, args.bootstrap)

    print("\n## K6a − K2 partido a partido (descriptivo, sin voto)\n")
    print("| `D` | condición | {} |".format(" | ".join("partido {}".format(p) for p in partidos)))
    print("|---|---|" + "---|" * len(partidos))
    for celda in celdas:
        condicion, modo, _ = celda
        print("| {} | {} | {} |".format(medir.NOMBRE_MODO[modo], condicion, " | ".join(
            "{:+.3f}".format(cc.spell([recuentos[p][(VOTA,) + celda]]) - cc.spell([recuentos[p][("K2",) + celda]]))
            for p in partidos)))

    print("\n## Acierto por frame del signo de z (descriptivo, sin voto)\n")
    print("Frames de juego con equipo en la etiqueta, de los 3 partidos juntos.\n")
    print("| condición | balón | frames | K2 | K6a | K6a, 7 pliegues |")
    print("|---|---|---|---|---|---|")
    for condicion in lc.CONDICIONES:
        for balon in ("con balón", "sin balón"):
            total = aciertos[("K2", condicion, balon, "total")]
            print("| {} | {} | {} | {} |".format(condicion, balon, total, " | ".join(
                "{:.2f} %".format(100.0 * aciertos[(v, condicion, balon, "bien")] / max(total, 1))
                for v in ("K2", "K6a", "K6a, 7 pliegues"))))

    difs = [resumen[c]["K2"] for c in celdas]
    pasa = float(np.mean(difs)) >= MEDIA_MIN and min(difs) >= PEOR_MIN
    print("\n## La regla (K6a frente a K2, las 4 celdas)\n")
    print("- Media {:+.4f} (se pide {:+.3f} o más) · peor celda {:+.4f} (se pide {:+.3f} o más): **{}**".format(
        float(np.mean(difs)), MEDIA_MIN, min(difs), PEOR_MIN,
        "apunta bien: el piloto de semillas del pliegue J03WMX" if pasa
        else "no apunta: K6 no se cierra, baja detrás de K7 y K8"))


if __name__ == "__main__":
    main()
