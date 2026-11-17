"""Mide un candidato entrenado en los 8 pliegues frente a K2 y a `main`, dentro del proveedor. Para después de una ronda.

    python validation/conjunto/medir_pliegues.py --pesos pesos_k8.npz --nombre K8
    python validation/conjunto/medir_pliegues.py --pesos repo --nombre K2 --comprobar     # el instrumento

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, mitad de entrenamiento, MIT). Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. **No lee el examen de SkillCorner:** la lista pasa por
`lector.exigir_solo_entrenamiento` y no hay ninguna bandera que lo abra.

Cada partido se puntúa con el pliegue que no lo vio: en la DFL, el suyo; en SkillCorner, el cruzado
(`cj_comun.pliegue_de`). Las versiones:

- **`main`:** B5 (en la DFL, el pliegue de B5 que no vio el partido; en SkillCorner, los coeficientes de la entrega),
  `dead_state` y el decodificador de la entrega, como en `refinar.py`;
- **K2:** `possession/conjunto_pesos.npz`, con la α de cada pliegue en la DFL y la de «todos» en SkillCorner, como se
  publicó. Con `--comprobar` tiene que dar la tabla publicada de K2 (`validation/resultados/2026-11-17_modelo_conjunto.md`);
- **K2 con α = 4** (sin voto): la misma K2 con la α del candidato, para comparar sin la ventaja de que K2 eligió su α;
- **el candidato:** los pesos de `--pesos` (los escribe `ronda_pliegues.py`), con su α (4) en todos los partidos.

Las tablas: el spellF1 frente a `main` y frente a K2 en cada celda (DFL: control y flag, las dos condiciones que votan,
el `D` de las etiquetas, el propio y el propio con el balón a la vista en los `D`; SkillCorner: las dos condiciones y
los dos `D`), con el intervalo pareado y en cuántos partidos gana; y las cuentas de `detalle_abiertos.py` (V, S y P) por
proveedor. La regla de cada candidato va en docs/decisiones.md; este script no decide nada por sí solo.
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
import refinar  # noqa: E402
import medir  # noqa: E402
import detalle_abiertos as da  # noqa: E402
import cj_comun as cj  # noqa: E402
import comun as cc  # noqa: E402
import d_propio  # noqa: E402
import lector  # noqa: E402
from comun import dfl, puntuar  # noqa: E402
from possession import aprendida, conjunto  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "possession", "conjunto_pesos.npz")
DOS_A_CINCO = 2
# K2 frente a `main` en la DFL con control, «como el ATD», `D` de las etiquetas: la primera celda publicada
PUBLICADA = (0.728, 0.780)


def ruta(fichero):
    if fichero == "repo":
        return REPO
    return fichero if os.path.isabs(fichero) else str(cj.carpeta() / fichero)


def logits(limpio, pliegue, candidato, alfa_k2_de):
    """{versión: α·z} con el pliegue dado. `alfa_k2_de` es el pliegue del que K2 toma su α (None: «todos»)."""
    salida = {}
    refinar._usar_pesos(REPO)
    z_k2 = conjunto.salidas(limpio, pliegue)[0]
    salida["K2"] = float(conjunto.pesos(alfa_k2_de)["alfa"]) * z_k2
    salida["K2 con α = 4"] = 4.0 * z_k2
    if candidato:
        refinar._usar_pesos(ruta(candidato))
        salida["candidato"] = float(conjunto.pesos(pliegue)["alfa"]) * conjunto.salidas(limpio, pliegue)[0]
    return salida


def puntuar_tracking(trk, gts, pliegue, candidato, alfa_k2_de, pliegue_b5, modos, detalle_de):
    piezas = medir._piezas(puntuar.solo_lectura(trk), next(iter(gts.values())), pliegue_b5)
    escalados = logits(piezas["limpio"], pliegue, candidato, alfa_k2_de)
    recuentos, detalles = {}, {}
    for modo in modos:
        preds = {"main": medir._decodificar(piezas, piezas["b5"], modo)}
        for nombre, s in escalados.items():
            mio = aprendida.puntuacion_de("b5", s, piezas["visible"], 1.0, piezas["cercano"])
            preds[nombre] = medir._decodificar(piezas, mio, modo)
        for nombre, pred in preds.items():
            for convencion, gt in gts.items():
                recuentos[(nombre, modo, convencion)] = puntuar.contar(gt, pred)
                if detalle_de:
                    detalles[(nombre, modo, convencion)] = da.detalle(gt, pred)[0]
    return recuentos, detalles


def trabajo(t):
    dominio, partido, candidato = t
    inicio = time.time()
    recuentos, detalles = {}, {}
    if dominio == "dfl":
        cargado = dfl.cargar(partido)
        gts = collections.OrderedDict((c, cargado["gt"][c]) for c in ("control", "flag"))
        for j, condicion in enumerate(dfl.VOTAN):
            for vista in (False, True):
                trk = d_propio.con_balon_en_d(cargado, condicion) if vista else dfl.tracking_de(cargado, condicion)
                modos = ("vista",) if vista else ("oraculo", "propio")
                r, d = puntuar_tracking(trk, gts, partido, candidato, partido, partido, modos, j == 0 and not vista)
                recuentos.update({(k[0], condicion, k[1], k[2]): v for k, v in r.items()})
                detalles.update({(k[0], condicion, k[1], k[2]): v for k, v in d.items()})
    else:
        lector.exigir_solo_entrenamiento([partido])
        crudo = lector.leer_crudo(partido)
        for j, condicion in enumerate(lector.VOTAN):
            trk, gt = lector.tracking_de(crudo, condicion, partido)
            r, d = puntuar_tracking(trk, {"sc": gt}, cj.pliegue_de("sc", partido), candidato, None, None,
                                    ("oraculo", "propio"), j == 0)
            recuentos.update({(k[0], condicion, k[1], k[2]): v for k, v in r.items()})
            detalles.update({(k[0], condicion, k[1], k[2]): v for k, v in d.items()})
    return (dominio, partido), recuentos, detalles, time.time() - inicio


def tabla_spell(recuentos, partidos, celdas, versiones, n_draws):
    print("| `D` | condición | etiquetas | main | K2 | {} |".format(" | ".join(
        "{0} | {0} − main [5–95 %] · gana | {0} − K2 [5–95 %] · gana".format(v) for v in versiones)))
    print("|---|---|---|---|---|" + "---|---|---|" * len(versiones))
    for celda in celdas:
        condicion, modo, convencion = celda
        partes = []
        for v in versiones:
            _, cand, dif, i, g = refinar.comparar(recuentos, partidos, v, celda, "main", n_draws)
            _, _, dk, ik, gk = refinar.comparar(recuentos, partidos, v, celda, "K2", n_draws)
            partes.append("{:.3f} | {:+.3f} {} · {} | {:+.3f} {} · {}".format(cand, dif, medir.rango(i), g, dk,
                                                                          medir.rango(ik), gk))
        print("| {} | {} | {} | {:.3f} | {:.3f} | {} |".format(
            medir.NOMBRE_MODO[modo], condicion, convencion,
            cc.spell([recuentos[p][("main",) + celda] for p in partidos]),
            cc.spell([recuentos[p][("K2",) + celda] for p in partidos]), " | ".join(partes)))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pesos", default=None, help="los pesos del candidato, con las claves de los 8 pliegues")
    parser.add_argument("--nombre", default="candidato")
    parser.add_argument("--comprobar", action="store_true", help="solo `main` y K2: tienen que dar lo publicado")
    parser.add_argument("--procesos", type=int, default=2)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    refinar.exigir_b5_en_main()
    lector.exigir_solo_entrenamiento(list(cj.SKILLCORNER))
    candidato = None if args.comprobar else args.pesos
    if not args.comprobar:
        if not args.pesos:
            parser.error("hace falta --pesos (o --comprobar)")
        with np.load(ruta(args.pesos), allow_pickle=False) as f:
            claves = {k.split("/")[0] for k in f.files}
            faltan = [p for p in cj.PLIEGUES if p not in claves]
            if faltan:
                sys.exit("a {} le faltan los pliegues {}".format(args.pesos, faltan))
    trabajos = [("dfl", p, candidato) for p in cj.DFL] + [("sc", p, candidato) for p in cj.SKILLCORNER]
    recuentos, detalles = {}, {}
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for clave, r, d, segundos in pool.map(trabajo, trabajos):
            recuentos[clave], detalles[clave] = r, d
            print("# hecho {} {} en {:.0f} s".format(clave[0], clave[1], segundos), file=sys.stderr, flush=True)

    versiones = ["K2 con α = 4"] + ([] if args.comprobar else ["candidato"])
    print("# {} en los 8 pliegues, dentro del proveedor, frente a K2 y a `main`\n".format(
        "Comprobación del instrumento" if args.comprobar else args.nombre))
    print("Código: {} · bootstrap pareado de {} · este script: sha256 {}… · K2: `conjunto_pesos.npz` (sha256 {}…){}."
          .format(puntuar.version_del_codigo(), args.bootstrap, refinar.huella(os.path.abspath(__file__)),
                  refinar.huella(REPO), "" if args.comprobar else " · {}: `{}` (sha256 {}…)".format(
                      args.nombre, os.path.basename(ruta(args.pesos)), refinar.huella(ruta(args.pesos)))))
    print("«candidato» es {}. Cada partido, con el pliegue que no lo vio.".format(args.nombre))

    dfl_p = [("dfl", p) for p in cj.DFL]
    sc_p = [("sc", p) for p in cj.SKILLCORNER]
    rec_dfl = {p: recuentos[p] for p in dfl_p}
    rec_sc = {p: recuentos[p] for p in sc_p}
    celdas_dfl = [(c, m, v) for m in ("oraculo", "propio", "vista") for c in dfl.VOTAN for v in ("control", "flag")]
    celdas_sc = [(c, m, "sc") for m in ("oraculo", "propio") for c in lector.VOTAN]
    print("\n## DFL, 7 partidos\n")
    tabla_spell(rec_dfl, dfl_p, celdas_dfl, versiones, args.bootstrap)
    print("\n## SkillCorner, mitad de entrenamiento, 10 partidos\n")
    tabla_spell(rec_sc, sc_p, celdas_sc, versiones, args.bootstrap)

    primera = (dfl.VOTAN[0], "oraculo", "control")
    ahora = (round(cc.spell([rec_dfl[p][("main",) + primera] for p in dfl_p]), 3),
             round(cc.spell([rec_dfl[p][("K2",) + primera] for p in dfl_p]), 3))
    print("\nInstrumento: `main` y K2 en la DFL con control, «como el ATD», `D` de las etiquetas: {:.3f} → {:.3f} "
          "(publicado: {:.3f} → {:.3f}): **{}**".format(ahora[0], ahora[1], PUBLICADA[0], PUBLICADA[1],
                                                        "coincide" if ahora == PUBLICADA else "NO COINCIDE"))

    print("\n## Lo que ataca (cuentas de `detalle_abiertos.py`; `D` de las etiquetas, primera condición)\n")
    print("| datos | versión | V: cambios entre equipos vistos | nuestros | S: nos sobran | P: posesiones de 2 a 5 s "
          "encontradas | de menos de 2 s |")
    print("|---|---|---|---|---|---|---|")
    for nombre_datos, partidos, condicion, convencion in (("DFL, control", dfl_p, dfl.VOTAN[0], "control"),
                                                          ("DFL, flag", dfl_p, dfl.VOTAN[0], "flag"),
                                                          ("SkillCorner", sc_p, lector.VOTAN[0], "sc")):
        for nombre in ["main", "K2"] + versiones:
            c = collections.Counter()
            for p in partidos:
                c.update(detalles[p][(nombre, condicion, "oraculo", convencion)])
            cortas = c["tramo", 0, "reales"] + c["tramo", 1, "reales"]
            print("| {} | {} | {:.1f} % de {} | {} | {} | {:.1f} % de {} | {:.1f} % |".format(
                nombre_datos, nombre, 100.0 * c["vistos", "equipos"] / max(c["cambios reales", "equipos"], 1),
                c["cambios reales", "equipos"], c["cambios nuestros", "equipos"], c["nos sobran", "equipos"],
                100.0 * c["tramo", DOS_A_CINCO, "encontrada"] / max(c["tramo", DOS_A_CINCO, "reales"], 1),
                c["tramo", DOS_A_CINCO, "reales"],
                100.0 * (c["tramo", 0, "encontrada"] + c["tramo", 1, "encontrada"]) / max(cortas, 1)))
    if args.comprobar:
        sys.exit(0 if ahora == PUBLICADA else 1)


if __name__ == "__main__":
    main()
