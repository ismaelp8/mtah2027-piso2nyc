"""Mide los refinamientos de K2 que no reentrenan nada (K3, K4 y K5) frente a `main` y frente a K2.

    python validation/conjunto/refinar.py                        # DFL: cada partido con el pliegue que no lo vio
    python validation/conjunto/refinar.py --dominio sc           # SkillCorner, mitad de entrenamiento, pliegues cruzados
    python validation/conjunto/refinar.py --dominio metrica      # Metrica, con los pesos de la entrega
    python validation/conjunto/refinar.py --dominio sc --pesos <fichero>.npz --entrenado-con dfl   # el otro proveedor
    python validation/conjunto/refinar.py --comprobar            # el instrumento: la mezcla con peso 1 y 0

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, MIT; Metrica sample-data). Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. **No lee el examen de SkillCorner:** la lista de partidos pasa
por `lector.exigir_solo_entrenamiento` y no hay ninguna bandera que lo abra.

Los candidatos y la regla están en docs/decisiones.md (17/11, «dos refinamientos de K2 sin reentrenar»), escritos
antes de medir. Todos salen de dos logits que ya existen, sin entrenar nada (`possession/refinamientos.py`):

- **K3:** la media a partes iguales del logit de K2 y del de B5, cada uno en su escala, puntuada como B5;
- **K4:** el logit de K2 promediado con el del campo en espejo;
- **K5:** K3 con el logit de K4;
- y, sin voto, la mezcla con 1/4 y con 3/4 de K2.

`main`, K2 y el `D` se montan como en `medir.py` (B5, `dead_state` y el decodificador de la entrega). La α de K2 y
la de B5 son las de `medir.py`: en la DFL, la del pliegue que no vio el partido; en SkillCorner y en Metrica, la de
todos.

Con `--pesos` (el otro proveedor), K2 va con los pesos de ese fichero (clave «todos», como los escribe
`juntar.py --alfa`) en todos los partidos, y `--entrenado-con` dice con qué proveedor se entrenó: el script se
niega a medirlo en ese mismo proveedor. B5 no cambia: nunca vio SkillCorner ni Metrica; en la DFL va con el pliegue
que no vio el partido, pero sí vio la DFL, y la tabla lo dice.
"""

import argparse
import collections
import concurrent.futures
import hashlib
import importlib.util
import os
import pickle
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import medir  # noqa: E402  (pone en el camino harness/, cambios/, apuesta_b/, skillcorner/ y la raíz)
import cj_comun as cj  # noqa: E402
import comun as cc  # noqa: E402
import d_propio  # noqa: E402
import lector  # noqa: E402  (validation/skillcorner/lector.py)
from comun import dfl, puntuar  # noqa: E402
from possession import aprendida, conjunto, pipeline  # noqa: E402
from possession import refinamientos as rf  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CANDIDATOS = ("K3", "K4", "K5")
SIN_VOTO = collections.OrderedDict([("K3 con 1/4 de K2", 0.25), ("K3 con 3/4 de K2", 0.75)])
UMBRAL, DANO = medir.UMBRAL, medir.DANO  # +0,005 y −0,005: el límite de daño del 16/11
MIN_DFL, MIN_SC = medir.MIN_DFL, medir.MIN_SC
GANA_K4, PIERDE_K4 = 0.003, 0.002  # K4 frente a K2: media con control y peor celda (docs/decisiones.md, 17/11)
NOMBRE_MODO = medir.NOMBRE_MODO
_METRICA = None


def lector_metrica():
    """`validation/metrica/lector.py`, que se llama igual que el de SkillCorner: se carga con otro nombre."""
    global _METRICA
    if _METRICA is None:
        ruta = os.path.join(AQUI, "..", "metrica", "lector.py")
        spec = importlib.util.spec_from_file_location("lector_metrica", ruta)
        _METRICA = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_METRICA)
    return _METRICA


def _usar_pesos(ruta):
    if ruta and conjunto.PESOS != ruta:
        conjunto.PESOS = ruta
        conjunto._CACHE.clear()


def _logits(limpio, fuera_k2, alfa_k2, fuera_b5, pesos=()):
    """Los tres logits ya en su escala: K2, K2 con el espejo y B5. Con varios ficheros de `pesos` (el promedio de
    semillas), la z de K2 es la media de las de cada fichero."""
    en_espejo = rf.en_espejo(limpio)
    if len(pesos) > 1:
        z, espejo = 0.0, 0.0
        for ruta in pesos:
            _usar_pesos(ruta)
            z = z + conjunto.salidas(limpio, fuera_k2)[0]
            espejo = espejo + conjunto.salidas(en_espejo, fuera_k2)[0]
        z, espejo = z / float(len(pesos)), espejo / float(len(pesos))
    else:
        z = conjunto.salidas(limpio, fuera_k2)[0]
        espejo = conjunto.salidas(en_espejo, fuera_k2)[0]
    return {"k2": alfa_k2 * z, "k2e": alfa_k2 * (0.5 * (z + espejo)), "b5": rf.logit_b5(limpio, fuera_b5)}


def _versiones(piezas, logits, modo, comprobar):
    def decodificar(s):
        mio = aprendida.puntuacion_de("b5", s, piezas["visible"], 1.0, piezas["cercano"])
        return medir._decodificar(piezas, mio, modo)

    main = medir._decodificar(piezas, piezas["b5"], modo)
    k2 = decodificar(logits["k2"])
    if comprobar:
        return {"la mezcla con todo el peso en K2 da K2":
                bool(np.array_equal(decodificar(rf.mezclar(logits["k2"], logits["b5"], 1.0)), k2)),
                "la mezcla con todo el peso en B5 da `main`":
                bool(np.array_equal(decodificar(rf.mezclar(logits["k2"], logits["b5"], 0.0)), main))}
    salida = {"main": main, "K2": k2,
              "K3": decodificar(rf.mezclar(logits["k2"], logits["b5"])),
              "K4": decodificar(logits["k2e"]),
              "K5": decodificar(rf.mezclar(logits["k2e"], logits["b5"]))}
    for nombre, peso in SIN_VOTO.items():
        salida[nombre] = decodificar(rf.mezclar(logits["k2"], logits["b5"], peso))
    return salida


def _apuntar(recuentos, versiones, gts, celda, comprobar):
    if comprobar:
        for nombre, igual in versiones.items():
            recuentos[(nombre,) + celda + ("iguales",)] = igual
        return
    for (clave, convencion), valor in medir._recuentos(versiones, gts).items():
        recuentos[(clave,) + celda + (convencion,)] = valor


def medir_dfl(trabajo):
    partido, pesos, comprobar = trabajo
    inicio = time.time()
    _usar_pesos(pesos[0] if pesos else None)
    fuera_k2 = None if pesos else partido
    alfa_k2 = conjunto.pesos(fuera_k2)["alfa"]
    cargado = dfl.cargar(partido)
    recuentos = {}
    for condicion in dfl.VOTAN:
        for vista in (False, True):
            trk = puntuar.solo_lectura(d_propio.con_balon_en_d(cargado, condicion) if vista
                                       else dfl.tracking_de(cargado, condicion))
            piezas = medir._piezas(trk, cargado["gt"]["flag"], partido)
            logits = _logits(piezas["limpio"], fuera_k2, alfa_k2, partido, pesos)
            for modo in (("vista",) if vista else ("oraculo", "propio")):
                _apuntar(recuentos, _versiones(piezas, logits, modo, comprobar), cargado["gt"], (condicion, modo),
                         comprobar)
    return partido, recuentos, time.time() - inicio


def medir_sc(trabajo):
    id_, pesos, comprobar = trabajo
    inicio = time.time()
    lector.exigir_solo_entrenamiento([id_])
    _usar_pesos(pesos[0] if pesos else None)
    fuera_k2 = None if pesos else cj.pliegue_de("sc", id_)
    alfa_k2 = conjunto.pesos(None)["alfa"]  # la de todos, como `medir.py` en SkillCorner
    crudo = lector.leer_crudo(id_)
    recuentos = {}
    for condicion in lector.VOTAN:
        trk, gt = lector.tracking_de(crudo, condicion, id_)
        piezas = medir._piezas(puntuar.solo_lectura(trk), gt, None)
        logits = _logits(piezas["limpio"], fuera_k2, alfa_k2, None, pesos)
        for modo in ("oraculo", "propio"):
            _apuntar(recuentos, _versiones(piezas, logits, modo, comprobar), {"sc": gt}, (condicion, modo), comprobar)
    return id_, recuentos, time.time() - inicio


def medir_metrica(trabajo):
    id_, pesos, comprobar = trabajo
    inicio = time.time()
    _usar_pesos(pesos[0] if pesos else None)
    lc = lector_metrica()
    alfa_k2 = conjunto.pesos(None)["alfa"]
    crudo = lc.leer(id_)
    recuentos = {}
    for condicion in lc.CONDICIONES:
        trk, gt = lc.tracking_de(crudo, condicion, id_)
        piezas = medir._piezas(puntuar.solo_lectura(trk), gt, None)
        logits = _logits(piezas["limpio"], None, alfa_k2, None, pesos)
        for modo in ("oraculo", "propio"):
            _apuntar(recuentos, _versiones(piezas, logits, modo, comprobar), {"eventos": gt}, (condicion, modo),
                     comprobar)
    return id_, recuentos, time.time() - inicio


def comparar(recuentos, partidos, clave, celda, contra, n_draws):
    """(nota de `contra`, nota de `clave`, diferencia, intervalo, en cuántos gana)."""
    cand = [recuentos[p][(clave,) + celda] for p in partidos]
    ref = [recuentos[p][(contra,) + celda] for p in partidos]
    dif, intervalo, gana = cc.frente_a(cand, ref, n_draws)
    return cc.spell(ref), cc.spell(cand), dif, intervalo, gana


def informe(recuentos, partidos, celdas, n_draws):
    """Las tablas de cada versión y, para cada celda, {versión: (diferencia con `main`, gana, diferencia con K2)}."""
    resumen = collections.defaultdict(dict)
    for clave in ("K2",) + CANDIDATOS + tuple(SIN_VOTO):
        print("\n## {}{}\n".format(clave, " (sin voto)" if clave in SIN_VOTO else ""))
        print("| `D` | condición | etiquetas | main | K2 | {0} | {0} − main [5–95 %] | gana a main en | {0} − K2 "
              "[5–95 %] | gana a K2 en |".format(clave))
        print("|---|---|---|---|---|---|---|---|---|---|")
        for celda in celdas:
            condicion, modo, convencion = celda
            ref, cand, dif, intervalo, gana = comparar(recuentos, partidos, clave, celda, "main", n_draws)
            k2, _, dif_k2, intervalo_k2, gana_k2 = comparar(recuentos, partidos, clave, celda, "K2", n_draws)
            resumen[celda][clave] = (dif, gana, dif_k2)
            print("| {} | {} | {} | {:.3f} | {:.3f} | {:.3f} | {:+.3f} {} | {} de {} | {:+.3f} {} | {} de {} |".format(
                NOMBRE_MODO[modo], condicion, convencion, ref, k2, cand, dif, medir.rango(intervalo), gana,
                len(partidos), dif_k2, medir.rango(intervalo_k2), gana_k2, len(partidos)))
        predichas = {v: sum(recuentos[p][(v,) + celdas[0]]["n_pred"] for p in partidos) for v in ("main", "K2", clave)}
        print("\nPosesiones predichas en la primera celda: {} · K2, {} · `main`, {} (reales: {}).".format(
            predichas[clave], predichas["K2"], predichas["main"],
            sum(recuentos[p][("main",) + celdas[0]]["n_gt"] for p in partidos)))
    return resumen


def por_partido(recuentos, partidos, celdas):
    """Sin voto: la diferencia con `main` partido a partido. El reto es un solo partido, así que importa cuántas
    veces pierde cada versión y cuánto, no solo la media. Añadido después de ver el bloque A (17/11)."""
    print("\n## Partido a partido, frente a `main` (descriptivo, sin voto)\n")
    versiones = ("K2",) + CANDIDATOS + tuple(SIN_VOTO)
    print("Cada casilla: peor partido / mediana / mejor partido, y en cuántos partidos queda por debajo de `main`.\n")
    print("| `D` | condición | etiquetas | {} |".format(" | ".join(versiones)))
    print("|---|---|---|" + "---|" * len(versiones))
    pierde = collections.Counter()
    for celda in celdas:
        condicion, modo, convencion = celda
        casillas = []
        for clave in versiones:
            difs = np.array([cc.spell([recuentos[p][(clave,) + celda]]) - cc.spell([recuentos[p][("main",) + celda]])
                             for p in partidos])
            pierde[clave] += int(np.sum(difs < 0))
            casillas.append("{:+.3f} / {:+.3f} / {:+.3f} ({})".format(difs.min(), float(np.median(difs)), difs.max(),
                                                                    int(np.sum(difs < 0))))
        print("| {} | {} | {} | {} |".format(NOMBRE_MODO[modo], condicion, convencion, " | ".join(casillas)))
    total = len(celdas) * len(partidos)
    print("\nVeces que queda por debajo de `main`, de {} (partido y celda): {}.".format(
        total, "; ".join("{}, {}".format(clave, pierde[clave]) for clave in versiones)))


def encontradas(recuentos, partidos, celdas):
    """Sin voto: cuántas posesiones reales encuentra cada versión (emparejadas con una predicha con un solape de 0,5 o
    más, el umbral central del `spellF1`) y cuántas de las predichas casan con una real. Añadido el 17/11 después de
    ver el bloque A, para decir si se ven más cambios de posesión o solo se colocan mejor."""
    print("\n## Posesiones reales encontradas (descriptivo, sin voto; solape de 0,5 o más)\n")
    print("| `D` | condición | etiquetas | versión | reales | predichas | encontradas | de las reales | de las predichas "
          "|")
    print("|---|---|---|---|---|---|---|---|---|")
    for celda in celdas:
        condicion, modo, convencion = celda
        for clave in ("main", "K2") + CANDIDATOS:
            flags = np.hstack([recuentos[p][(clave,) + celda]["flags"] for p in partidos])
            predichas = sum(recuentos[p][(clave,) + celda]["n_pred"] for p in partidos)
            casan = int(flags[flags.shape[0] // 2].sum())
            print("| {} | {} | {} | {} | {} | {} | {} | {:.1f} % | {:.1f} % |".format(
                NOMBRE_MODO[modo], condicion, convencion, clave, flags.shape[1], predichas, casan,
                100.0 * casan / max(flags.shape[1], 1), 100.0 * casan / max(predichas, 1)))


def si_o_no(valor):
    return "pasa" if valor else "no pasa"


def regla_dfl(resumen, n):
    print("\n## La regla en la DFL (límite de daño del 16/11, frente a `main`)\n")
    minimo = min(MIN_DFL, n)
    for clave in ("K2",) + CANDIDATOS:
        control = [v[clave] for c, v in resumen.items() if c[2] == "control" and c[1] != "vista"]
        flag = [v[clave] for c, v in resumen.items() if c[2] == "flag" and c[1] != "vista"]
        vista = [v[clave] for c, v in resumen.items() if c[1] == "vista"]
        print("- {}: punto 1 (control, +{} y {} de {} en las 4 celdas) **{}** · punto 3 (flag, no pierde más de {}) "
              "**{}** · balón a la vista en los `D` (no pierde más de {}) **{}** · media con control {:+.4f}".format(
                  clave, UMBRAL, minimo, n, si_o_no(all(d >= UMBRAL and g >= minimo for d, g, _ in control)), DANO,
                  si_o_no(all(d >= -DANO for d, _, _ in flag)), DANO, si_o_no(all(d >= -DANO for d, _, _ in vista)),
                  float(np.mean([d for d, _, _ in control]))))
    regla_k4(resumen, lambda c: c[2] == "control" and c[1] != "vista")


def regla_sc(resumen, n):
    print("\n## La regla en SkillCorner (+{} y {} de {} en las cuatro celdas, frente a `main`)\n".format(
        UMBRAL, min(MIN_SC, n), n))
    for clave in ("K2",) + CANDIDATOS:
        valores = [v[clave] for v in resumen.values()]
        print("- {}: **{}** · peor celda {:+.4f} · media {:+.4f}".format(
            clave, si_o_no(all(d >= UMBRAL and g >= min(MIN_SC, n) for d, g, _ in valores)),
            min(d for d, _, _ in valores), float(np.mean([d for d, _, _ in valores]))))
    regla_k4(resumen, lambda c: True)


def regla_k4(resumen, de_control):
    """K4 frente a K2: gana si la media con control llega a +0,003 y ninguna celda baja de −0,002."""
    frente_a_k2 = {c: v["K4"][2] for c, v in resumen.items()}
    media = float(np.mean([d for c, d in frente_a_k2.items() if de_control(c)]))
    peor = min(frente_a_k2.values())
    print("- K4 frente a K2: media en las celdas que cuentan {:+.4f} (se pide +{}) y peor celda {:+.4f} (se pide "
          "−{} o más): **{}**".format(media, GANA_K4, peor, PIERDE_K4, si_o_no(media >= GANA_K4 and peor >= -PIERDE_K4)))


def lectura_otro_proveedor(resumen):
    print("\n## El otro proveedor (frente a `main`; «quita la pérdida» es −{} o más en todas las celdas)\n".format(
        DANO))
    for clave in ("K2",) + CANDIDATOS + tuple(SIN_VOTO):
        valores = [v[clave][0] for v in resumen.values()]
        print("- {}: peor celda {:+.4f} · media {:+.4f} · {}".format(
            clave, min(valores), float(np.mean(valores)),
            "gana en todas (+{} o más)".format(UMBRAL) if min(valores) >= UMBRAL else
            ("**quita la pérdida**" if min(valores) >= -DANO else "**pierde más de {} en alguna celda**".format(DANO))))


def huella(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dominio", choices=("dfl", "sc", "metrica"), default="dfl")
    parser.add_argument("--partidos", nargs="*", default=None, help="por defecto, todos los del dominio")
    parser.add_argument("--procesos", type=int, default=2)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--pesos", nargs="+", default=None,
                        help="otros pesos para K2 (clave «todos»): los de un modelo entrenado con un solo proveedor. "
                             "Con varios ficheros, la z de K2 es la media de las de todos (el promedio de semillas)")
    parser.add_argument("--entrenado-con", choices=("dfl", "sc"), default=None,
                        help="con --pesos: el único proveedor que vio ese modelo")
    parser.add_argument("--comprobar", action="store_true",
                        help="el instrumento: la mezcla con todo el peso en K2 da K2, y con todo en B5, `main`")
    parser.add_argument("--solo-por-partido", action="store_true",
                        help="enseña solo las tablas descriptivas (partido a partido y posesiones encontradas)")
    parser.add_argument("--recuentos", default=None,
                        help="fichero donde guardar los recuentos (o del que leerlos, si existe), fuera del repo")
    args = parser.parse_args()
    if bool(args.pesos) != bool(args.entrenado_con):
        parser.error("--pesos y --entrenado-con van juntos")
    if args.pesos and args.entrenado_con == args.dominio:
        parser.error("esos pesos vieron partidos de este proveedor: no es una medida del otro proveedor")

    if args.dominio == "dfl":
        partidos = list(args.partidos or cj.DFL)
        funcion, convenciones, condiciones = medir_dfl, dfl.CONVENCIONES[::-1], dfl.VOTAN
        modos = ("oraculo", "propio", "vista")
    elif args.dominio == "sc":
        partidos = [int(p) for p in (args.partidos or cj.SKILLCORNER)]
        lector.exigir_solo_entrenamiento(partidos)
        funcion, convenciones, condiciones, modos = medir_sc, ("sc",), lector.VOTAN, ("oraculo", "propio")
    else:
        lc = lector_metrica()
        partidos = [int(p) for p in (args.partidos or lc.partidos())]
        if not partidos:
            sys.exit("No hay partidos de Metrica bajados, en {}".format(lc.carpeta()))
        funcion, convenciones, condiciones, modos = medir_metrica, ("eventos",), lc.CONDICIONES, ("oraculo", "propio")
    celdas = [(c, m, v) for m in modos for c in condiciones for v in convenciones]

    if args.recuentos and os.path.isfile(args.recuentos) and not args.comprobar:
        with open(args.recuentos, "rb") as f:
            recuentos = pickle.load(f)
        if sorted(recuentos) != sorted(partidos):
            sys.exit("los recuentos guardados son de otros partidos")
    else:
        recuentos = {}
        trabajos = [(p, tuple(args.pesos or ()), args.comprobar) for p in partidos]
        with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
            for partido, valor, segundos in pool.map(funcion, trabajos):
                recuentos[partido] = valor
                print("# hecho {} en {:.0f} s".format(partido, segundos), file=sys.stderr, flush=True)
        if args.recuentos and not args.comprobar:
            os.makedirs(os.path.dirname(os.path.abspath(args.recuentos)), exist_ok=True)
            with open(args.recuentos, "wb") as f:
                pickle.dump(recuentos, f)

    donde = {"dfl": "DFL", "sc": "SkillCorner, mitad de entrenamiento", "metrica": "Metrica"}[args.dominio]
    print("# Refinamientos de K2 sin reentrenar · {} · {} partidos\n".format(donde, len(partidos)))
    if args.pesos:
        de_k2 = "{}{}, de {} que solo vio {}".format(
            "la media de las z de " if len(args.pesos) > 1 else "los de ",
            " y ".join("`{}` (sha256 {}…)".format(os.path.basename(r), huella(r)) for r in args.pesos),
            "modelos" if len(args.pesos) > 1 else "un modelo", {"dfl": "la DFL", "sc": "SkillCorner"}[args.entrenado_con])
    else:
        de_k2 = "los de `conjunto_pesos.npz` (sha256 {}…): {}".format(huella(conjunto.PESOS), {
            "dfl": "cada partido con el pliegue que no lo vio", "sc": "cada partido con el pliegue que no lo vio",
            "metrica": "los de la entrega (todos los partidos)"}[args.dominio])
    print("Código: {} · bootstrap pareado de {} · `main` = B5, `dead_state` y `{}` · pesos de K2: {}. B5: {}.".format(
        puntuar.version_del_codigo(), args.bootstrap, pipeline.PIECES["temporal"], de_k2,
        "el pliegue que no vio el partido (sí vio otros de la DFL)" if args.dominio == "dfl"
        else "los coeficientes de la entrega (nunca vio este proveedor)"))
    if args.comprobar:
        distintos = sorted({k[0] for r in recuentos.values() for k, igual in r.items() if not igual})
        print("\nComprobación del instrumento: {} salidas comparadas frame a frame; distintas: {}.".format(
            sum(len(r) for r in recuentos.values()), ", ".join(distintos) or "ninguna"))
        sys.exit(1 if distintos else 0)

    if args.solo_por_partido:
        por_partido(recuentos, partidos, celdas)
        encontradas(recuentos, partidos, celdas)
        return
    resumen = informe(recuentos, partidos, celdas, args.bootstrap)
    if args.pesos:
        lectura_otro_proveedor(resumen)
    elif args.dominio == "dfl":
        regla_dfl(resumen, len(partidos))
    elif args.dominio == "sc":
        regla_sc(resumen, len(partidos))
    else:
        lectura_otro_proveedor(resumen)


if __name__ == "__main__":
    main()
