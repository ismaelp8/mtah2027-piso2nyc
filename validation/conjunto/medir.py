"""Mide los candidatos K1 y K2 del modelo conjunto frente a `main`, con la regla del 17/11 (docs/decisiones.md).

    python validation/conjunto/medir.py --etiqueta v1                       # los 7 partidos de la DFL
    python validation/conjunto/medir.py --etiqueta v1 --dominio sc          # SkillCorner, mitad de entrenamiento
    python validation/conjunto/medir.py --etiqueta v1 --comprobar           # el instrumento: tiene que dar `main`

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, MIT). Lo puede ejecutar cualquiera, Claude incluido.
Solo imprime agregados. **No lee el examen de SkillCorner** (`lector.exigir_solo_entrenamiento`).

Lee las salidas del modelo que guardó `entrenar.py` (z y las dos probabilidades de cambio a 25 Hz, de cada partido
con el pliegue que no lo vio) y monta los candidatos con las piezas de la entrega, como `pipeline.run`:

- **`main`:** B5 (en la DFL, con el pliegue que no vio el partido; en SkillCorner, con los coeficientes de la
  entrega), `dead_state` y el decodificador de la entrega (`decode_cortas_a_d`, coste 25);
- **K1:** `main` más `cambios.capa(p, γ, 50, contra_d=True)`;
- **K2:** `aprendida.puntuacion_de("b5", z, visible, α, cercano)` en lugar de B5.

Modos del `D`: el de las etiquetas (`puntuar.d_oraculo`), el propio y, solo en la DFL, el propio con el balón a la
vista en los `D` (`d_propio.con_balon_en_d`).

γ y α se eligen en la DFL dejando un partido fuera (media del `spellF1` de las dos convenciones, las dos condiciones
que votan y los dos primeros modos del `D`; en el empate, el valor más pequeño) y se guardan junto a las salidas;
en SkillCorner se usan los elegidos con los 7, sin elegir nada allí.
"""

import argparse
import collections
import concurrent.futures
import json
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (AQUI, os.path.join(AQUI, "..", "cambios"), os.path.join(AQUI, "..", "apuesta_b"),
                 os.path.join(AQUI, "..", "skillcorner")):
    sys.path.insert(0, _carpeta)
import cj_comun as cj  # noqa: E402
import comun as cc  # noqa: E402  (validation/cambios/comun.py: pone harness/ y la raíz en el camino)
import d_propio  # noqa: E402
import lector  # noqa: E402
from comun import dfl, puntuar  # noqa: E402
from possession import aprendida, cambios, pipeline  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GAMMAS = (2.0, 4.0, 8.0)
ALFAS = (0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)  # la rejilla de B5 (validation/apuesta_b/entrenar.py)
VENTANA = 50
MODOS = ("oraculo", "propio", "vista")
NOMBRE_MODO = {"oraculo": "etiquetas", "propio": "propio", "vista": "propio, balón a la vista en los D"}
CANDIDATOS = collections.OrderedDict([("K1", GAMMAS), ("K2", ALFAS)])
LETRA = {"K1": "γ", "K2": "α"}
UMBRAL, DANO = 0.005, 0.005  # el límite de daño del 16/11
MIN_DFL, MIN_SC = 6, 7


def _piezas(trk, gt, partido_b5):
    """Las piezas de la entrega sobre un tracking: (B5, estado de `D`, `D` de las etiquetas, visible, cercano)."""
    limpio = pipeline.default_piece("ball")(trk)
    b5 = (aprendida.evidence_b5(limpio, fuera=partido_b5) if partido_b5 else
          pipeline.default_piece("candidates")(limpio))
    estado = pipeline.default_piece("dead_state")(limpio)
    todos = aprendida.equipo_mas_cercano(limpio)
    cercano = np.full(len(limpio.bx), -1, dtype=np.int8)
    for a, b in limpio.blocks:
        cercano[a:b] = todos[a:b]
    return {"b5": b5, "estado": estado, "oraculo": puntuar.d_oraculo(gt), "visible": aprendida.balon_visible(limpio),
            "cercano": cercano, "blocks": limpio.blocks, "n": len(limpio.bx), "limpio": limpio}


def _decodificar(piezas, equipo, modo, extra=None):
    lista = [equipo, piezas["estado"]] + ([extra] if extra is not None else [])
    if modo == "oraculo":
        lista.append(piezas["oraculo"])
    score, allowed, conflicto = pipeline.combine(lista, piezas["n"])
    if any(conflicto[a:b].any() for a, b in piezas["blocks"]):
        raise ValueError("las piezas se contradicen")
    return pipeline.default_piece("temporal")(score, allowed, piezas["blocks"])


def _versiones(piezas, z, p, modo, comprobar=False):
    """{clave: etiquetas}: `main`, K1 con cada γ y K2 con cada α."""
    salida = {"main": _decodificar(piezas, piezas["b5"], modo)}
    if comprobar:
        # El instrumento: K1 con p a cero y K2 con el logit y la α de B5 tienen que dar `main` frame a frame.
        salida[("K1", 0.0)] = _decodificar(piezas, piezas["b5"], modo,
                                           cambios.capa(np.zeros_like(p), GAMMAS[-1], VENTANA, contra_d=True))
        return salida
    for gamma in GAMMAS:
        salida[("K1", gamma)] = _decodificar(piezas, piezas["b5"], modo,
                                             cambios.capa(p, gamma, VENTANA, contra_d=True))
    for alfa in ALFAS:
        mio = aprendida.puntuacion_de("b5", z, piezas["visible"], alfa, piezas["cercano"])
        salida[("K2", alfa)] = _decodificar(piezas, mio, modo)
    return salida


def _recuentos(versiones, gts):
    return {(clave, convencion): puntuar.contar(gt, pred) for clave, pred in versiones.items()
            for convencion, gt in gts.items()}


def _como_b5(piezas, partido_b5):
    """z y α de B5, para comprobar el camino de K2: con ellos tiene que salir `main`."""
    juego = aprendida.coeficientes("b5", partido_b5 or None)
    return aprendida.logit(aprendida.rasgos(piezas["limpio"], "b5"), juego["pesos"]), juego["alfa"]


def medir_dfl(trabajo):
    partido, etiqueta, comprobar = trabajo
    inicio = time.time()
    cargado = dfl.cargar(partido)
    gts = cargado["gt"]
    with np.load(cj.fichero_salida(etiqueta, "dfl", partido)) as d:
        salidas = {k: d[k] for k in d.files}
    if str(salidas["pliegue"]) != cj.pliegue_de("dfl", partido):
        raise ValueError("las salidas de {} no son del pliegue que no lo vio".format(partido))
    recuentos = {}
    for j, condicion in enumerate(dfl.VOTAN):
        for vista in (False, True):
            trk = puntuar.solo_lectura(d_propio.con_balon_en_d(cargado, condicion) if vista
                                       else dfl.tracking_de(cargado, condicion))
            piezas = _piezas(trk, gts["flag"], partido)
            sufijo = ("d" if vista else "") + str(j)
            z, p = salidas["z_" + sufijo], salidas["p_" + sufijo]
            for modo in (("vista",) if vista else ("oraculo", "propio")):
                versiones = _versiones(piezas, z, p, modo, comprobar)
                if comprobar:
                    zb, alfa = _como_b5(piezas, partido)
                    mio = aprendida.puntuacion_de("b5", zb, piezas["visible"], alfa, piezas["cercano"])
                    versiones[("K2", "B5")] = _decodificar(piezas, mio, modo)
                    for clave, pred in versiones.items():
                        recuentos[(clave, condicion, modo, "iguales")] = bool(np.array_equal(pred, versiones["main"]))
                    continue
                for (clave, convencion), valor in _recuentos(versiones, gts).items():
                    recuentos[(clave, condicion, modo, convencion)] = valor
    return partido, recuentos, time.time() - inicio


def medir_sc(trabajo):
    id_, etiqueta, elegidos, comprobar = trabajo
    inicio = time.time()
    lector.exigir_solo_entrenamiento([id_])
    crudo = lector.leer_crudo(id_)
    with np.load(cj.fichero_salida(etiqueta, "sc", id_)) as d:
        salidas = {k: d[k] for k in d.files}
    if str(salidas["pliegue"]) != cj.pliegue_de("sc", id_):
        raise ValueError("las salidas de {} no son del pliegue que no lo vio".format(id_))
    recuentos = {}
    for j, condicion in enumerate(lector.VOTAN):
        trk, gt = lector.tracking_de(crudo, condicion, id_)
        piezas = _piezas(puntuar.solo_lectura(trk), gt, None)
        z, p = salidas["z_{}".format(j)], salidas["p_{}".format(j)]
        for modo in ("oraculo", "propio"):
            versiones = _versiones(piezas, z, p, modo, comprobar)
            if comprobar:
                zb, alfa = _como_b5(piezas, None)
                mio = aprendida.puntuacion_de("b5", zb, piezas["visible"], alfa, piezas["cercano"])
                versiones[("K2", "B5")] = _decodificar(piezas, mio, modo)
                for clave, pred in versiones.items():
                    recuentos[(clave, condicion, modo, "iguales")] = bool(np.array_equal(pred, versiones["main"]))
                continue
            if elegidos is not None:  # en SkillCorner no se elige: solo los valores que salieron de la DFL
                versiones = {k: v for k, v in versiones.items()
                             if k == "main" or float(elegidos[k[0]]["todos"]) == float(k[1])}
            for (clave, _), valor in _recuentos(versiones, {"sc": gt}).items():
                recuentos[(clave, condicion, modo, "sc")] = valor
    return id_, recuentos, time.time() - inicio


def fichero_elegidos(etiqueta):
    return cj.carpeta() / "salidas" / etiqueta / "elegidos.json"


def nota(recuentos, partidos, clave, celdas):
    return float(np.mean([cc.spell([recuentos[p][(clave,) + celda] for p in partidos]) for celda in celdas]))


def elegir(recuentos, partidos, familia, celdas):
    """{partido o «todos»: valor}: el que más saca en los demás (o en todos); en el empate, el más pequeño."""
    elegidos = {}
    for fuera in list(partidos) + ["todos"]:
        resto = [p for p in partidos if p != fuera] or list(partidos)  # con un solo partido (piloto), con él
        elegidos[fuera] = max(CANDIDATOS[familia], key=lambda v: (nota(recuentos, resto, (familia, v), celdas), -v))
    return elegidos


def fila(recuentos, partidos, clave_de, celda, n_draws):
    cand = [recuentos[p][(clave_de(p),) + celda] for p in partidos]
    ref = [recuentos[p][("main",) + celda] for p in partidos]
    dif, intervalo, gana = cc.frente_a(cand, ref, n_draws)
    predichas = sum(r["n_pred"] for r in cand)
    return cc.spell(ref), cc.spell(cand), dif, intervalo, gana, predichas, sum(r["n_pred"] for r in ref), \
        sum(r["n_gt"] for r in ref)


def rango(intervalo):
    """El intervalo del bootstrap como texto; sin bootstrap, un guion."""
    return "[–]" if intervalo is None else "[{:+.3f} a {:+.3f}]".format(*intervalo)


def informe_dfl(recuentos, partidos, etiqueta, n_draws):
    celdas_eleccion = [(c, m, v) for c in dfl.VOTAN for m in ("oraculo", "propio") for v in dfl.CONVENCIONES]
    veredictos, elegidos_todos = [], {}
    for familia in CANDIDATOS:
        elegidos = elegir(recuentos, partidos, familia, celdas_eleccion)
        elegidos_todos[familia] = elegidos
        cuenta = collections.Counter(elegidos[p] for p in partidos)
        print("\n## Candidato {}\n".format(familia))
        print("{} elegida para cada partido con los otros: {}. Con los {}: {:g}.\n".format(
            LETRA[familia], "; ".join("{:g} en {}".format(v, n) for v, n in sorted(cuenta.items())), len(partidos),
            elegidos["todos"]))
        print("| `D` | condición | etiquetas | main | candidato | diferencia [5–95 %] | gana en | posesiones: "
              "candidato / main / reales |")
        print("|---|---|---|---|---|---|---|---|")
        pasa = {"1": True, "3": True, "vista": True}
        sin_piloto = []
        for modo in MODOS:
            for condicion in dfl.VOTAN:
                for convencion in dfl.CONVENCIONES[::-1]:
                    celda = (condicion, modo, convencion)
                    ref, cand, dif, intervalo, gana, n_cand, n_main, n_gt = fila(
                        recuentos, partidos, lambda p: (familia, elegidos[p]), celda, n_draws)
                    if modo == "vista":
                        pasa["vista"] &= dif >= -DANO
                    elif convencion == "control":
                        pasa["1"] &= dif >= UMBRAL and gana >= min(MIN_DFL, len(partidos))
                    else:
                        pasa["3"] &= dif >= -DANO
                    print("| {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} {} | {} de {} | {} / {} / {} |".format(
                        NOMBRE_MODO[modo], condicion, convencion, ref, cand, dif, rango(intervalo), gana,
                        len(partidos), n_cand, n_main, n_gt))
                    if cj.PILOTO in partidos and len(partidos) > 1:
                        resto = [p for p in partidos if p != cj.PILOTO]
                        _, _, dif6, _, gana6, _, _, _ = fila(recuentos, resto, lambda p: (familia, elegidos[p]),
                                                           celda, 0)
                        sin_piloto.append("{} · {} · {}: {:+.3f} ({} de {})".format(
                            NOMBRE_MODO[modo], condicion, convencion, dif6, gana6, len(resto)))
        veredictos.append((familia, pasa))
        print("\nRegla: punto 1 (control, +{} y {} de {} en las 4 celdas): **{}** · punto 3 (flag, no pierde más de "
              "{}): **{}** · balón a la vista en los `D` (no pierde más de {} con ninguna convención): **{}**.".format(
                  UMBRAL, min(MIN_DFL, len(partidos)), len(partidos), "pasa" if pasa["1"] else "no pasa", DANO,
                  "pasa" if pasa["3"] else "no pasa", DANO, "pasa" if pasa["vista"] else "no pasa"))
        if sin_piloto:
            print("\nSin el partido del piloto ({}), descriptivo: {}.".format(cj.PILOTO, "; ".join(sin_piloto)))
        print("\nLos valores de {}, uno a uno (descriptivo; diferencia con `main` y en cuántos gana):\n".format(
            LETRA[familia]))
        columnas = [(c, m, v) for m in ("oraculo", "propio") for c in dfl.VOTAN for v in dfl.CONVENCIONES[::-1]]
        print("| {} | {} |".format(LETRA[familia], " | ".join(
            "{}, {}, `D` {}".format(v, c, NOMBRE_MODO[m]) for c, m, v in columnas)))
        print("|---|" + "---|" * len(columnas))
        for valor in CANDIDATOS[familia]:
            celdas = []
            for celda in columnas:
                _, _, dif, _, gana, _, _, _ = fila(recuentos, partidos, lambda p: (familia, valor), celda, 0)
                celdas.append("{:+.3f} ({})".format(dif, gana))
            print("| {:g} | {} |".format(valor, " | ".join(celdas)))
    print("\n## Veredicto con la regla (puntos 1 y 3; el 2, SkillCorner, solo se abre si pasan)\n")
    for familia, pasa in veredictos:
        todo = all(pasa.values())
        print("- {}: punto 1 {}, punto 3 {}, balón a la vista {} → **{}**".format(
            familia, *("pasa" if pasa[k] else "no pasa" for k in ("1", "3", "vista")),
            "sigue a SkillCorner" if todo else "no sigue"))
    if set(partidos) == set(cj.DFL):
        destino = fichero_elegidos(etiqueta)
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(elegidos_todos, f)
        print("\nElegidos con los 7, guardados para SkillCorner: {}.".format(
            ", ".join("{} de {} = {:g}".format(LETRA[k], k, v) for k, v in elegidos_todos.items())))


def informe_sc(recuentos, partidos, elegidos, n_draws):
    for familia in CANDIDATOS:
        if elegidos is None:
            valores = CANDIDATOS[familia]
            print("\n## Candidato {} (descriptivo: todos los valores de {}, sin elegir)\n".format(familia,
                                                                                               LETRA[familia]))
        else:
            valores = (float(elegidos[familia]["todos"]),)
            print("\n## Candidato {} · {} = {:g}, elegida en la DFL con los 7\n".format(familia, LETRA[familia],
                                                                                    valores[0]))
        print("| {} | `D` | condición | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / "
              "main / reales |".format(LETRA[familia]))
        print("|---|---|---|---|---|---|---|---|")
        for valor in valores:
            pasa = True
            for modo in ("oraculo", "propio"):
                for condicion in lector.VOTAN:
                    ref, cand, dif, intervalo, gana, n_cand, n_main, n_gt = fila(
                        recuentos, partidos, lambda p: (familia, valor), (condicion, modo, "sc"), n_draws)
                    pasa &= dif >= UMBRAL and gana >= min(MIN_SC, len(partidos))
                    print("| {:g} | {} | {} | {:.3f} | {:.3f} | {:+.3f} {} | {} de {} | {} / {} / {} |".format(
                        valor, NOMBRE_MODO[modo], condicion, ref, cand, dif, rango(intervalo), gana, len(partidos),
                        n_cand, n_main, n_gt))
            if elegidos is not None:
                print("\nRegla (+{} y {} de {} en las cuatro celdas): **{}**.".format(
                    UMBRAL, min(MIN_SC, len(partidos)), len(partidos), "pasa" if pasa else "no pasa"))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--etiqueta", required=True, help="la tanda de `entrenar.py` cuyas salidas se miden")
    parser.add_argument("--dominio", choices=("dfl", "sc"), default="dfl")
    parser.add_argument("--partidos", nargs="*", default=None, help="por defecto, todos los del dominio")
    parser.add_argument("--procesos", type=int, default=2)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--comprobar", action="store_true",
                        help="el instrumento: K1 con p a cero y K2 con el logit de B5 tienen que dar `main`")
    parser.add_argument("--sin-elegidos", action="store_true",
                        help="SkillCorner, solo para el piloto: enseña todos los valores, sin regla")
    args = parser.parse_args()
    if args.dominio == "dfl":
        partidos = list(args.partidos or cj.DFL)
        trabajos, funcion = [(p, args.etiqueta, args.comprobar) for p in partidos], medir_dfl
        elegidos = None
    else:
        partidos = [int(p) for p in (args.partidos or cj.SKILLCORNER)]
        lector.exigir_solo_entrenamiento(partidos)
        elegidos = None
        if not args.sin_elegidos and not args.comprobar:
            with open(fichero_elegidos(args.etiqueta), encoding="utf-8") as f:
                elegidos = json.load(f)
        trabajos, funcion = [(p, args.etiqueta, elegidos, args.comprobar) for p in partidos], medir_sc

    recuentos = {}
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for partido, valor, segundos in pool.map(funcion, trabajos):
            recuentos[partido] = valor
            print("# hecho {} en {:.0f} s".format(partido, segundos), file=sys.stderr, flush=True)

    print("# Modelo conjunto frente a `main` · tanda «{}» · {} · {} partidos\n".format(
        args.etiqueta, "DFL" if args.dominio == "dfl" else "SkillCorner, mitad de entrenamiento", len(partidos)))
    print("Código: {} · bootstrap pareado de {} · `main` = B5, `dead_state` y `{}`.".format(
        puntuar.version_del_codigo(), args.bootstrap, pipeline.PIECES["temporal"]))
    if args.comprobar:
        distintos = sorted({str(k[0]) for r in recuentos.values() for k, igual in r.items() if not igual})
        total = sum(len(r) for r in recuentos.values())
        print("\nComprobación del instrumento: {} salidas comparadas con `main` frame a frame; distintas: {}.".format(
            total, ", ".join(distintos) or "ninguna"))
        sys.exit(1 if distintos else 0)
    if args.dominio == "dfl":
        informe_dfl(recuentos, partidos, args.etiqueta, args.bootstrap)
    else:
        informe_sc(recuentos, partidos, elegidos, args.bootstrap)


if __name__ == "__main__":
    main()
