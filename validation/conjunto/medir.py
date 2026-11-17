"""Mide los candidatos K1 y K2 del modelo conjunto frente a `main`, con la regla del 17/11 (docs/decisiones.md).

    python validation/conjunto/medir.py --etiqueta v1                       # los 7 partidos de la DFL
    python validation/conjunto/medir.py --etiqueta v1 --dominio sc          # SkillCorner, mitad de entrenamiento
    python validation/conjunto/medir.py --etiqueta v1 --comprobar           # el instrumento: tiene que dar `main`
    python validation/conjunto/medir.py --etiqueta v1 --con-la-pieza        # con la predicción en numpy

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, MIT). Lo puede ejecutar cualquiera, Claude incluido.
Solo imprime agregados.

**El examen de SkillCorner no se lee en ningún camino por defecto.** Solo con `--examen --examen-con-permiso
--candidato K1|K2`, una vez y para un solo candidato, cuando ya ha pasado todo lo demás (regla del 17/11). Cada uso
se apunta en `validation/skillcorner/BITACORA.md` («Usos del examen») y en `docs/decisiones.md`.

De dónde salen z y las dos probabilidades de cambio del modelo, de cada partido con el pliegue que no lo vio:

- por defecto, de las salidas que guardó `entrenar.py` (torch, float32);
- con `--con-la-pieza`, de `possession/conjunto.py` (numpy, float64), con los pesos de `conjunto_pesos.npz`. Es la
  pieza que usaría la entrega. En el examen siempre va la pieza, con los pesos del pliegue de todos.

Con ellas monta los candidatos con las piezas de la entrega, como `pipeline.run`:

- **`main`:** B5 (en la DFL, con el pliegue que no vio el partido; en SkillCorner, con los coeficientes de la
  entrega), `dead_state` y el decodificador de la entrega (`decode_cortas_a_d`, coste 25);
- **K1:** `main` más `cambios.capa(p, γ, 50, contra_d=True)`;
- **K2:** `aprendida.puntuacion_de("b5", z, visible, α, cercano)` en lugar de B5.

Modos del `D`: el de las etiquetas (`puntuar.d_oraculo`), el propio y, solo en la DFL, el propio con el balón a la
vista en los `D` (`d_propio.con_balon_en_d`).

γ y α se eligen en la DFL dejando un partido fuera (media del `spellF1` de las dos convenciones, las dos condiciones
que votan y los dos primeros modos del `D`; en el empate, el valor más pequeño) y se guardan junto a las salidas
(`elegidos.json`); en SkillCorner se usan los elegidos con los 7, sin elegir nada allí.
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
from possession import aprendida, cambios, conjunto, pipeline  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GAMMAS = (2.0, 4.0, 8.0)
ALFAS = (0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)  # la rejilla de B5 (validation/apuesta_b/entrenar.py)
VENTANA = conjunto.VENTANA_CAPA
MODOS = ("oraculo", "propio", "vista")
NOMBRE_MODO = {"oraculo": "etiquetas", "propio": "propio", "vista": "propio, balón a la vista en los D"}
CANDIDATOS = collections.OrderedDict([("K1", GAMMAS), ("K2", ALFAS)])
LETRA = {"K1": "γ", "K2": "α"}
UMBRAL, DANO = 0.005, 0.005  # el límite de daño del 16/11
MIN_DFL, MIN_SC = 6, 7


def _piezas(trk, gt, partido_b5):
    """Las piezas de la entrega sobre un tracking: B5, el estado de `D`, el `D` de las etiquetas y lo que hace
    falta para puntuar un logit como B5."""
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


def _versiones(piezas, z, p, modo, valores):
    """{clave: etiquetas}: `main`, K1 con cada γ y K2 con cada α de `valores` ({familia: valores})."""
    salida = {"main": _decodificar(piezas, piezas["b5"], modo)}
    for gamma in valores.get("K1", ()):
        salida[("K1", gamma)] = _decodificar(piezas, piezas["b5"], modo,
                                             cambios.capa(p, gamma, VENTANA, contra_d=True))
    for alfa in valores.get("K2", ()):
        mio = aprendida.puntuacion_de("b5", z, piezas["visible"], alfa, piezas["cercano"])
        salida[("K2", alfa)] = _decodificar(piezas, mio, modo)
    return salida


def _de_comprobacion(piezas, p, modo, partido_b5):
    """El instrumento: K1 con `p` a cero y K2 con el logit y la α de B5 tienen que dar `main` frame a frame."""
    juego = aprendida.coeficientes("b5", partido_b5 or None)
    zb = aprendida.logit(aprendida.rasgos(piezas["limpio"], "b5"), juego["pesos"])
    como_b5 = aprendida.puntuacion_de("b5", zb, piezas["visible"], juego["alfa"], piezas["cercano"])
    main = _decodificar(piezas, piezas["b5"], modo)
    otras = {"K1 con p a cero": _decodificar(piezas, piezas["b5"], modo,
                                              cambios.capa(np.zeros_like(p), GAMMAS[-1], VENTANA, contra_d=True)),
             "K2 con el logit de B5": _decodificar(piezas, como_b5, modo)}
    return {nombre: bool(np.array_equal(pred, main)) for nombre, pred in otras.items()}


def _recuentos(versiones, gts):
    return {(clave, convencion): puntuar.contar(gt, pred) for clave, pred in versiones.items()
            for convencion, gt in gts.items()}


def _del_modelo(guardadas, sufijo, limpio, pliegue):
    """(z, p) de un tracking: de las salidas de torch guardadas o, sin ellas, de la pieza en numpy."""
    if guardadas is not None:
        return guardadas["z_" + sufijo], guardadas["p_" + sufijo]
    return conjunto.salidas(limpio, fuera=pliegue)[0], conjunto.probabilidades_de_cambio(limpio, fuera=pliegue)


def _guardadas(etiqueta, dominio, partido, con_la_pieza):
    if con_la_pieza:
        return None
    with np.load(cj.fichero_salida(etiqueta, dominio, partido)) as d:
        guardadas = {k: d[k] for k in d.files}
    if "solo" in guardadas:  # la comprobación del otro proveedor: el modelo solo vio partidos del otro
        if str(guardadas["solo"]) == dominio:
            raise ValueError("las salidas de {} son de un modelo que vio este proveedor".format(partido))
    elif str(guardadas["pliegue"]) != cj.pliegue_de(dominio, partido):
        raise ValueError("las salidas de {} no son del pliegue que no lo vio".format(partido))
    return guardadas


def medir_dfl(trabajo):
    partido, etiqueta, comprobar, con_la_pieza, valores = trabajo
    inicio = time.time()
    cargado = dfl.cargar(partido)
    gts = cargado["gt"]
    guardadas = _guardadas(etiqueta, "dfl", partido, con_la_pieza)
    recuentos = {}
    for j, condicion in enumerate(dfl.VOTAN):
        for vista in (False, True):
            trk = puntuar.solo_lectura(d_propio.con_balon_en_d(cargado, condicion) if vista
                                       else dfl.tracking_de(cargado, condicion))
            piezas = _piezas(trk, gts["flag"], partido)
            z, p = _del_modelo(guardadas, ("d" if vista else "") + str(j), piezas["limpio"], partido)
            for modo in (("vista",) if vista else ("oraculo", "propio")):
                if comprobar:
                    for nombre, igual in _de_comprobacion(piezas, p, modo, partido).items():
                        recuentos[(nombre, condicion, modo, "iguales")] = igual
                    continue
                for (clave, convencion), valor in _recuentos(_versiones(piezas, z, p, modo, valores), gts).items():
                    recuentos[(clave, condicion, modo, convencion)] = valor
    return partido, recuentos, time.time() - inicio


def medir_sc(trabajo):
    id_, etiqueta, valores, comprobar, con_la_pieza, examen = trabajo
    inicio = time.time()
    if examen:
        if id_ not in lector.EXAMEN:
            raise ValueError("{} no es del examen".format(id_))
        guardadas, pliegue = None, None  # el examen va con la pieza y los pesos del pliegue de todos
    else:
        lector.exigir_solo_entrenamiento([id_])
        guardadas, pliegue = _guardadas(etiqueta, "sc", id_, con_la_pieza), cj.pliegue_de("sc", id_)
    crudo = lector.leer_crudo(id_)
    recuentos = {}
    for j, condicion in enumerate(lector.VOTAN):
        trk, gt = lector.tracking_de(crudo, condicion, id_)
        piezas = _piezas(puntuar.solo_lectura(trk), gt, None)
        z, p = _del_modelo(guardadas, str(j), piezas["limpio"], pliegue)
        for modo in ("oraculo", "propio"):
            if comprobar:
                for nombre, igual in _de_comprobacion(piezas, p, modo, None).items():
                    recuentos[(nombre, condicion, modo, "iguales")] = igual
                continue
            for (clave, _), valor in _recuentos(_versiones(piezas, z, p, modo, valores), {"sc": gt}).items():
                recuentos[(clave, condicion, modo, "sc")] = valor
    return id_, recuentos, time.time() - inicio


def fichero_elegidos(etiqueta):
    return cj.carpeta() / "salidas" / etiqueta / "elegidos.json"


def nota(recuentos, partidos, clave, celdas):
    return float(np.mean([cc.spell([recuentos[p][(clave,) + celda] for p in partidos]) for celda in celdas]))


def elegir(recuentos, partidos, familia, celdas, lista):
    """{partido o «todos»: valor}: el de `lista` que más saca en los demás (o en todos); en el empate, el más
    pequeño."""
    elegidos = {}
    for fuera in list(partidos) + ["todos"]:
        resto = [p for p in partidos if p != fuera] or list(partidos)  # con un solo partido (piloto), con él
        elegidos[fuera] = max(lista, key=lambda v: (nota(recuentos, resto, (familia, v), celdas), -v))
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


def informe_dfl(recuentos, partidos, etiqueta, n_draws, guardar, valores):
    celdas_eleccion = [(c, m, v) for c in dfl.VOTAN for m in ("oraculo", "propio") for v in dfl.CONVENCIONES]
    veredictos, elegidos_todos = [], {}
    for familia, lista in valores.items():
        elegidos = elegir(recuentos, partidos, familia, celdas_eleccion, lista)
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
        sin_piloto, ganancia = [], []
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
                        ganancia.append(dif)
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
        veredictos.append((familia, pasa, float(np.mean(ganancia))))
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
        for valor in lista:
            celdas = []
            for celda in columnas:
                _, _, dif, _, gana, _, _, _ = fila(recuentos, partidos, lambda p: (familia, valor), celda, 0)
                celdas.append("{:+.3f} ({})".format(dif, gana))
            print("| {:g} | {} |".format(valor, " | ".join(celdas)))
    print("\n## Veredicto con la regla (puntos 1 y 3; el 2, SkillCorner, solo se abre si pasan)\n")
    for familia, pasa, media in veredictos:
        todo = all(pasa.values())
        print("- {}: punto 1 {}, punto 3 {}, balón a la vista {} → **{}** (ganancia media con control en las 4 "
              "celdas: {:+.3f})".format(familia, *("pasa" if pasa[k] else "no pasa" for k in ("1", "3", "vista")),
                                        "sigue a SkillCorner" if todo else "no sigue", media))
    if guardar and set(partidos) == set(cj.DFL):
        with open(fichero_elegidos(etiqueta), "w", encoding="utf-8") as f:
            json.dump(elegidos_todos, f)
        print("\nElegidos con los 7, guardados para SkillCorner y para la entrega: {}.".format(
            ", ".join("{} de {} = {:g}".format(LETRA[k], k, v["todos"]) for k, v in elegidos_todos.items())))


def informe_sc(recuentos, partidos, valores, n_draws, con_regla):
    for familia, lista in valores.items():
        if con_regla:
            print("\n## Candidato {} · {} = {:g}, fijada desde la DFL\n".format(familia, LETRA[familia], lista[0]))
        else:
            print("\n## Candidato {} (descriptivo: todos los valores de {}, sin elegir)\n".format(familia,
                                                                                               LETRA[familia]))
        print("| {} | `D` | condición | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / "
              "main / reales |".format(LETRA[familia]))
        print("|---|---|---|---|---|---|---|---|")
        for valor in lista:
            pasa = True
            for modo in ("oraculo", "propio"):
                for condicion in lector.VOTAN:
                    ref, cand, dif, intervalo, gana, n_cand, n_main, n_gt = fila(
                        recuentos, partidos, lambda p: (familia, valor), (condicion, modo, "sc"), n_draws)
                    pasa &= dif >= UMBRAL and gana >= min(MIN_SC, len(partidos))
                    print("| {:g} | {} | {} | {:.3f} | {:.3f} | {:+.3f} {} | {} de {} | {} / {} / {} |".format(
                        valor, NOMBRE_MODO[modo], condicion, ref, cand, dif, rango(intervalo), gana, len(partidos),
                        n_cand, n_main, n_gt))
            if con_regla:
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
    parser.add_argument("--con-la-pieza", action="store_true",
                        help="z y p salen de possession/conjunto.py (numpy), no de las salidas de torch")
    parser.add_argument("--sin-elegidos", action="store_true",
                        help="SkillCorner, solo para el piloto: enseña todos los valores, sin regla")
    parser.add_argument("--no-guardar", action="store_true", help="DFL: no escribe `elegidos.json`")
    parser.add_argument("--alfa", type=float, default=None,
                        help="mide K2 solo con esta α, sin elegir ni leer `elegidos.json` (comprobaciones)")
    parser.add_argument("--gamma", type=float, default=None, help="lo mismo para la γ de K1")
    parser.add_argument("--examen", action="store_true", help="SkillCorner: la mitad de examen (ver arriba)")
    parser.add_argument("--examen-con-permiso", action="store_true",
                        help="confirma que este es el único uso del examen para este candidato")
    parser.add_argument("--candidato", choices=tuple(CANDIDATOS), default=None,
                        help="el único candidato que se mide en el examen")
    args = parser.parse_args()

    elegidos, examen = None, False
    fijos = collections.OrderedDict()
    if args.gamma is not None:
        fijos["K1"] = (float(args.gamma),)
    if args.alfa is not None:
        fijos["K2"] = (float(args.alfa),)
    if fijos and args.examen:
        parser.error("el examen va con los valores elegidos en la DFL, no con --alfa ni --gamma")
    if args.dominio == "dfl":
        if args.examen:
            parser.error("el examen es de SkillCorner: --dominio sc")
        partidos = list(args.partidos or cj.DFL)
        valores = fijos or CANDIDATOS
        trabajos = [(p, args.etiqueta, args.comprobar, args.con_la_pieza, valores) for p in partidos]
        funcion = medir_dfl
    else:
        valores = fijos or dict(CANDIDATOS)
        if args.examen:
            if not (args.examen_con_permiso and args.candidato) or args.partidos or args.comprobar \
                    or args.sin_elegidos:
                parser.error("el examen se abre una vez y para un solo candidato: hacen falta --examen-con-permiso y "
                             "--candidato, y no admite --partidos, --comprobar ni --sin-elegidos")
            examen, partidos = True, list(lector.EXAMEN)
        else:
            partidos = [int(p) for p in (args.partidos or cj.SKILLCORNER)]
            lector.exigir_solo_entrenamiento(partidos)
        if not args.sin_elegidos and not args.comprobar and not fijos:
            with open(fichero_elegidos(args.etiqueta), encoding="utf-8") as f:
                elegidos = json.load(f)
            familias = (args.candidato,) if args.candidato else tuple(CANDIDATOS)
            valores = {familia: (float(elegidos[familia]["todos"]),) for familia in familias}
        trabajos = [(p, args.etiqueta, valores, args.comprobar, args.con_la_pieza or examen, examen)
                    for p in partidos]
        funcion = medir_sc

    recuentos = {}
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for partido, valor, segundos in pool.map(funcion, trabajos):
            recuentos[partido] = valor
            print("# hecho {} en {:.0f} s".format(partido, segundos), file=sys.stderr, flush=True)

    donde = "DFL" if args.dominio == "dfl" else ("SkillCorner, MITAD DE EXAMEN" if examen else
                                                 "SkillCorner, mitad de entrenamiento")
    print("# Modelo conjunto frente a `main` · tanda «{}» · {} · {} partidos\n".format(
        args.etiqueta, donde, len(partidos)))
    print("Código: {} · bootstrap pareado de {} · `main` = B5, `dead_state` y `{}` · salidas del modelo: {}.".format(
        puntuar.version_del_codigo(), args.bootstrap, pipeline.PIECES["temporal"],
        "la pieza en numpy (possession/conjunto.py)" if args.con_la_pieza or examen else "las de torch"))
    if args.comprobar:
        distintos = sorted({k[0] for r in recuentos.values() for k, igual in r.items() if not igual})
        total = sum(len(r) for r in recuentos.values())
        print("\nComprobación del instrumento: {} salidas comparadas con `main` frame a frame; distintas: {}.".format(
            total, ", ".join(distintos) or "ninguna"))
        sys.exit(1 if distintos else 0)
    if args.dominio == "dfl":
        informe_dfl(recuentos, partidos, args.etiqueta, args.bootstrap, not args.no_guardar and not fijos, valores)
    else:
        informe_sc(recuentos, partidos, valores, args.bootstrap, elegidos is not None or bool(fijos))


if __name__ == "__main__":
    main()
