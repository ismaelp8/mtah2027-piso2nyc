"""K7: un modelo entrenado sin SkillCorner (con la DFL y Metrica), puntuado en SkillCorner frente a los de solo la DFL.

    python validation/conjunto/k7.py --candidatos K7c=pesos_k7c.npz
    python validation/conjunto/k7.py --candidatos K7s=pesos_k7s_media.npz "K7s, z de la DFL=pesos_k7s_dfl.npz" ...

Datos abiertos de otros partidos (SkillCorner, A-League 2024/25, MIT). Lo puede ejecutar cualquiera, Claude incluido.
Solo imprime agregados. **No lee el examen de SkillCorner:** la lista pasa por `lector.exigir_solo_entrenamiento` y no
hay ninguna bandera que lo abra. Los ficheros de pesos se buscan en `conjunto_cache/` (los escribe `juntar_k7.py`).

La regla está en docs/decisiones.md (17/11, K7), escrita antes de entrenar. Cada candidato es K2 con otros pesos
(clave «todos», α = 4), puntuado como K2; `main` es la entrega con B5, `dead_state` y el decodificador de la entrega,
como en `refinar.py`. Se compara con los tres modelos de solo la DFL:

- **el original** del 17/11 (GPU): sus pesos no están en esta máquina, así que solo entra con sus cifras publicadas
  (`validation/resultados/2026-11-17_modelo_conjunto.md`), sin intervalo pareado;
- **las réplicas 1 y 2** (CPU, `pesos_r_solo_dfl.npz` y `pesos_r2_solo_dfl.npz`): se puntúan otra vez aquí. Tienen
  que dar lo publicado (`salidas/2026-11-17_refinar_replica_solo_dfl_en_skillcorner.md` y
  `…_refinar_semilla2_solo_dfl_en_skillcorner.md`): es la comprobación del instrumento.
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
import refinar  # noqa: E402  (importa medir, que pone en el camino harness/, cambios/, skillcorner/ y la raíz)
import medir  # noqa: E402
import cj_comun as cj  # noqa: E402
import comun as cc  # noqa: E402
import lector  # noqa: E402  (validation/skillcorner/lector.py)
from comun import puntuar  # noqa: E402
from possession import aprendida, conjunto, pipeline  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MODOS = ("oraculo", "propio")
CONVENCION = "sc"
REFERENCIAS = collections.OrderedDict([("réplica 1", "pesos_r_solo_dfl.npz"), ("réplica 2", "pesos_r2_solo_dfl.npz")])
# Frente a `main`, a tres decimales, en el orden de las celdas (`D` de las etiquetas: detectado, detectado y
# suavizado; `D` propio: los mismos). El original, de `resultados/2026-11-17_modelo_conjunto.md` y de la tabla de
# refinamientos; las réplicas, de sus salidas. `main`: 0,519, 0,514, 0,391 y 0,388.
PUBLICADAS = {"original": (-0.015, -0.010, -0.007, -0.004), "réplica 1": (-0.005, 0.001, -0.000, 0.003),
              "réplica 2": (-0.007, -0.003, -0.003, -0.001)}
MAIN_PUBLICADO = (0.519, 0.514, 0.391, 0.388)
MEDIA_MIN = 0.004  # la media de las 4 celdas frente a `main` que se pide (docs/decisiones.md, 17/11, K7)


def ruta(fichero):
    return fichero if os.path.isabs(fichero) else str(cj.carpeta() / fichero)


def medir_sc(trabajo):
    id_, versiones = trabajo
    inicio = time.time()
    lector.exigir_solo_entrenamiento([id_])
    crudo = lector.leer_crudo(id_)
    recuentos = {}
    for condicion in lector.VOTAN:
        trk, gt = lector.tracking_de(crudo, condicion, id_)
        piezas = medir._piezas(puntuar.solo_lectura(trk), gt, None)
        logits = {}
        for nombre, fichero in versiones:
            refinar._usar_pesos(ruta(fichero))
            logits[nombre] = float(conjunto.pesos(None)["alfa"]) * conjunto.salidas(piezas["limpio"], None)[0]
        for modo in MODOS:
            salida = {"main": medir._decodificar(piezas, piezas["b5"], modo)}
            for nombre, s in logits.items():
                mio = aprendida.puntuacion_de("b5", s, piezas["visible"], 1.0, piezas["cercano"])
                salida[nombre] = medir._decodificar(piezas, mio, modo)
            for (clave, convencion), valor in medir._recuentos(salida, {CONVENCION: gt}).items():
                recuentos[(clave, condicion, modo, convencion)] = valor
    return id_, recuentos, time.time() - inicio


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--candidatos", nargs="+", required=True, help="nombre=fichero de pesos (clave «todos»)")
    parser.add_argument("--vota", default=None, help="el nombre del candidato al que se le aplica la regla "
                                                      "(por defecto, el primero)")
    parser.add_argument("--procesos", type=int, default=2)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    refinar.exigir_b5_en_main()
    candidatos = collections.OrderedDict(c.split("=", 1) for c in args.candidatos)
    vota = args.vota or next(iter(candidatos))
    for nombre, fichero in list(REFERENCIAS.items()) + list(candidatos.items()):
        if not os.path.isfile(ruta(fichero)):
            sys.exit("no está {}".format(ruta(fichero)))
        if refinar.alfa_de_todos(ruta(fichero)) != 4.0:
            sys.exit("{} no trae α = 4".format(fichero))
    partidos = list(cj.SKILLCORNER)
    lector.exigir_solo_entrenamiento(partidos)
    versiones = tuple(list(REFERENCIAS.items()) + list(candidatos.items()))
    recuentos = {}
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for partido, valor, segundos in pool.map(medir_sc, [(p, versiones) for p in partidos]):
            recuentos[partido] = valor
            print("# hecho {} en {:.0f} s".format(partido, segundos), file=sys.stderr, flush=True)

    celdas = [(c, m, CONVENCION) for m in MODOS for c in lector.VOTAN]
    print("# K7: entrenado sin SkillCorner, puntuado en SkillCorner · mitad de entrenamiento · {} partidos\n".format(
        len(partidos)))
    print("Código: {} · bootstrap pareado de {} · `main` = B5, `dead_state` y `{}` · α = 4 en todos · este script: "
          "sha256 {}…".format(puntuar.version_del_codigo(), args.bootstrap, pipeline.PIECES["temporal"],
                              refinar.huella(os.path.abspath(__file__))))
    print("Pesos: {}.".format("; ".join("{}, `{}` (sha256 {}…)".format(n, f, refinar.huella(ruta(f)))
                                         for n, f in versiones)))

    def frente(clave, contra, celda):
        return refinar.comparar(recuentos, partidos, clave, celda, contra, args.bootstrap)

    print("\n## Comprobación del instrumento (antes de leer nada)\n")
    print("| `D` | condición | `main` publicado / ahora | réplica 1 − main publicado / ahora | réplica 2 − main publicado "
          "/ ahora | ¿coincide? |")
    print("|---|---|---|---|---|---|")
    instrumento = True
    for k, celda in enumerate(celdas):
        condicion, modo, _ = celda
        nota_main = round(cc.spell([recuentos[p][("main",) + celda] for p in partidos]), 3)
        r1, r2 = (round(frente(r, "main", celda)[2], 3) for r in REFERENCIAS)
        igual = (nota_main == MAIN_PUBLICADO[k] and abs(r1 - PUBLICADAS["réplica 1"][k]) < 1e-9
                 and abs(r2 - PUBLICADAS["réplica 2"][k]) < 1e-9)
        instrumento = instrumento and igual
        print("| {} | {} | {:.3f} / {:.3f} | {:+.3f} / {:+.3f} | {:+.3f} / {:+.3f} | {} |".format(
            medir.NOMBRE_MODO[modo], condicion, MAIN_PUBLICADO[k], nota_main, PUBLICADAS["réplica 1"][k], r1,
            PUBLICADAS["réplica 2"][k], r2, "sí" if igual else "**no**"))
    if not instrumento:
        print("\n**El instrumento no da lo publicado: no se lee nada de lo que sigue.**")
        sys.exit(1)

    resumen = {}
    for nombre in candidatos:
        print("\n## {}{}\n".format(nombre, "" if nombre == vota else " (sin voto)"))
        print("| `D` | condición | main | {0} | {0} − main [5–95 %] | gana a main en | − original (publicado) | − réplica 1 "
              "[5–95 %] | gana a la réplica 1 en | − réplica 2 [5–95 %] | gana a la réplica 2 en |".format(nombre))
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        resumen[nombre] = []
        for k, celda in enumerate(celdas):
            condicion, modo, _ = celda
            ref, cand, dif, intervalo, gana = frente(nombre, "main", celda)
            partes = []
            for r in REFERENCIAS:
                _, _, d, i, g = frente(nombre, r, celda)
                partes.append("{:+.3f} {} | {} de {}".format(d, medir.rango(i), g, len(partidos)))
            resumen[nombre].append(dif)
            print("| {} | {} | {:.3f} | {:.3f} | {:+.3f} {} | {} de {} | {:+.3f} | {} |".format(
                medir.NOMBRE_MODO[modo], condicion, ref, cand, dif, medir.rango(intervalo), gana, len(partidos),
                dif - PUBLICADAS["original"][k], " | ".join(partes)))
        predichas = sum(recuentos[p][(nombre,) + celdas[0]]["n_pred"] for p in partidos)
        print("\nPosesiones predichas en la primera celda: {}, {} · réplica 1, {} · réplica 2, {} · `main`, {} "
              "(reales: {}).".format(nombre, predichas, *(sum(recuentos[p][(v,) + celdas[0]]["n_pred"]
                                                                for p in partidos)
                                                            for v in ("réplica 1", "réplica 2", "main")),
                                     sum(recuentos[p][("main",) + celdas[0]]["n_gt"] for p in partidos)))

    print("\n## La regla\n")
    mejor = []
    for k, celda in enumerate(celdas):
        mejor.append(max([PUBLICADAS["original"][k]] + [frente(r, "main", celda)[2] for r in REFERENCIAS]))
    print("Lo mejor de los tres modelos de solo la DFL en cada celda, frente a `main`: {}.\n".format(
        ", ".join("{:+.4f}".format(m) for m in mejor)))
    for nombre, difs in resumen.items():
        en_todas = all(d >= m for d, m in zip(difs, mejor))
        media = float(np.mean(difs))
        print("- {}{}: frente a `main` {} · media {:+.4f} · en lo mejor de los tres o por encima en las 4 celdas: {} · "
              "media de +{} o más: {} → **{}**".format(
                  nombre, "" if nombre == vota else " (sin voto)", ", ".join("{:+.4f}".format(d) for d in difs), media,
                  "sí" if en_todas else "no", MEDIA_MIN, "sí" if media >= MEDIA_MIN else "no",
                  "se traslada mejor" if en_todas and media >= MEDIA_MIN else "no se traslada mejor"))


if __name__ == "__main__":
    main()
