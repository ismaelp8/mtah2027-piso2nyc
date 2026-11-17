"""Elige α de B11 y B12 en cada pliegue y junta los pesos en `possession/secuencia_pesos.npz`.

    python validation/secuencia/juntar.py b11          # elige α de los 8 pliegues de B11
    python validation/secuencia/juntar.py b12
    python validation/secuencia/juntar.py escribir     # junta pesos y α en possession/secuencia_pesos.npz
    python validation/secuencia/juntar.py escribir --modelos b11   # solo B11 (para medirlo antes)
    python validation/secuencia/juntar.py b13          # B13 (possession/trayectorias.py), rejilla hasta 32
    python validation/secuencia/juntar.py escribir --modelos b13   # en possession/trayectorias_pesos.npz

Datos abiertos de otros partidos (DFL, CC BY 4.0), con la caché del harness y los pesos de `entrenar_red.py`. Lo
puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

α, como la de B5 (docs/decisiones.md, 17/11; `validation/apuesta_b/entrenar.py`, `elegir_alfa_d_propio`): de
`comun.ALFAS`, la que da más `spellF1` medio con las dos convenciones y las dos condiciones que votan en los
partidos de entrenamiento del pliegue (dentro de muestra), con la pieza de `D` de `main` dentro, sin oráculo, y el
decodificador de `main`. Si empatan, la más pequeña. z sale de `possession.secuencia`, el código de la predicción.
"""

import argparse
import collections
import json
import multiprocessing
import sys
import time

import numpy as np

import comun
import dfl
import puntuar
from possession import aprendida, ball, pipeline, secuencia, trayectorias, trayectorias2

# B13 (17/11, possession/trayectorias.py): la misma elección, con la rejilla ampliada a 16 y 32 (B12 cayó en el borde, 8).
ALFAS_B13 = comun.ALFAS + (16.0, 32.0)
MODELOS = secuencia.MODELOS + ("b13", "b14", "b15")
PROPIOS = {"b13": trayectorias, "b14": trayectorias2, "b15": trayectorias2}  # los modelos con módulo y pesos propios
FICHERO_DE = {"b13": trayectorias.PESOS, "b14": trayectorias2.PESOS, "b15": trayectorias2.PESOS_B15}


def alfas_de(modelo):
    return ALFAS_B13 if modelo in PROPIOS else comun.ALFAS


def logit_de(modelo, trk, pesos):
    return PROPIOS[modelo].logit(trk, pesos) if modelo in PROPIOS else secuencia.logit(trk, modelo, pesos)


def fichero_alfa(modelo, pliegue):
    return comun.carpeta_cache() / "pesos" / "{}_{}_alfa.json".format(modelo, pliegue)


def pesos_entrenados(modelo, pliegue):
    with np.load(comun.fichero_pesos(modelo, pliegue)) as d:
        return {k: np.asarray(d[k], dtype=np.float64) for k in d.files}


def recuentos_de_un_partido(args):
    """Para un partido: {(pliegue, α, condición, convención): recuento} de los pliegues que lo entrenaron."""
    modelo, partido, seleccion = args
    cargado = dfl.cargar(partido)
    gt = cargado["gt"]
    decodificar = pipeline.default_piece("temporal")
    estado = pipeline.default_piece("dead_state")
    pliegues = [p for p in seleccion if p != partido]
    salida = {}
    for condicion in comun.CONDICIONES:
        trk = ball.clean(dfl.tracking_de(cargado, condicion))
        de_estado = estado(trk)
        visible = aprendida.balon_visible(trk)
        todos = aprendida.equipo_mas_cercano(trk)
        cercano = np.full(len(trk.bx), -1, dtype=np.int8)
        for a, b in trk.blocks:
            cercano[a:b] = todos[a:b]
        for pliegue in pliegues:
            z = logit_de(modelo, trk, pesos_entrenados(modelo, pliegue))
            for alfa in alfas_de(modelo):
                de_equipo = aprendida.puntuacion_de("b5", z, visible, alfa, cercano)
                score, allowed, _ = pipeline.combine([de_equipo, de_estado], len(trk.bx))
                pred = decodificar(score, allowed, trk.blocks)
                for convencion in dfl.CONVENCIONES:
                    salida[(pliegue, alfa, condicion, convencion)] = puntuar.contar(gt[convencion], pred)
    return partido, salida


def elegir(modelo, procesos, seleccion=comun.PLIEGUES):
    inicio = time.time()
    with multiprocessing.Pool(procesos) as pool:
        por_partido = dict(pool.map(recuentos_de_un_partido, [(modelo, p, tuple(seleccion)) for p in comun.PARTIDOS]))
    print("### α de {} (spellF1 medio dentro de muestra: dos convenciones × dos condiciones que votan, `D` propio, "
          "decodificador de main)\n".format(modelo.upper()))
    alfas = alfas_de(modelo)
    print("| pliegue | α | spellF1 medio por α ({}) |".format(", ".join("{:g}".format(a) for a in alfas)))
    print("|---|---|---|")
    for pliegue in seleccion:
        entrena = [p for p in comun.PARTIDOS if p != pliegue]
        medias = []
        for alfa in alfas:
            celdas = []
            for condicion in comun.CONDICIONES:
                for convencion in dfl.CONVENCIONES:
                    r = [por_partido[p][(pliegue, alfa, condicion, convencion)] for p in entrena]
                    celdas.append(puntuar.spell_f1(*puntuar.juntar(r)))
            medias.append(float(np.mean(celdas)))
        alfa = alfas[int(np.argmax(medias))]  # el primero de los empatados: la más pequeña
        with open(fichero_alfa(modelo, pliegue), "w", encoding="utf-8") as f:
            json.dump({"alfa": alfa, "medias": medias}, f)
        print("| {} | {:g} | {} |".format("los 7" if pliegue == "todos" else "sin " + pliegue, alfa,
                                          " / ".join("{:.3f}".format(m).replace(".", ",") for m in medias)))
    print("\ntiempo: {:.0f} s".format(time.time() - inicio), file=sys.stderr)


def escribir(modelos=secuencia.MODELOS):
    datos = collections.OrderedDict()
    for modelo in modelos:
        for pliegue in comun.PLIEGUES:
            with np.load(comun.fichero_pesos(modelo, pliegue)) as d:
                for k in sorted(d.files):
                    datos["{}/{}/{}".format(modelo, pliegue, k)] = np.asarray(d[k])
            with open(fichero_alfa(modelo, pliegue), encoding="utf-8") as f:
                datos["{}/{}/alfa".format(modelo, pliegue)] = np.array(float(json.load(f)["alfa"]))
    propios = [m for m in modelos if m in PROPIOS]
    if propios and len(modelos) != 1:
        raise ValueError("B13 y B14 van cada uno en su propio fichero: --modelos con uno solo")
    destino = FICHERO_DE[modelos[0]] if propios else secuencia.PESOS
    np.savez_compressed(destino, **datos)
    print("escritos {} arrays en {}".format(len(datos), destino))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("que", choices=MODELOS + ("escribir",))
    parser.add_argument("--procesos", type=int, default=7)
    parser.add_argument("--modelos", nargs="+", choices=MODELOS, default=list(secuencia.MODELOS),
                        help="con «escribir»: los modelos que se juntan (por defecto, B11 y B12; B13 va solo)")
    parser.add_argument("--pliegues", nargs="+", choices=comun.PLIEGUES, default=list(comun.PLIEGUES),
                        help="al elegir α: solo estos pliegues (por defecto, los 8); cada uno se elige igual")
    args = parser.parse_args()
    if args.que == "escribir":
        escribir(tuple(args.modelos))
    else:
        elegir(args.que, args.procesos, [p for p in comun.PLIEGUES if p in args.pliegues])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
