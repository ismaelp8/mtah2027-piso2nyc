"""Mide G2 y G3 (árboles con *boosting* para el estado de `D`) frente a E2, con la regla del 16/11.

    python validation/scripts/d_estado/medir_arboles.py                    # todo, los 7 partidos
    python validation/scripts/d_estado/medir_arboles.py --sin-sensibilidad # sin placebo, escalas ni temblor
    python validation/scripts/d_estado/medir_arboles.py --partidos J03WMX J03WN1 --bootstrap 0   # para probar

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del harness. Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. Necesita scikit-learn (entorno aparte; ver arboles.py).

Los candidatos y la regla de entrada se escribieron antes de medir: docs/decisiones.md, entrada del 16/11 «estado con
árboles (idea 2.4)». Cada candidato puntúa un partido con los árboles entrenados en los otros seis.

1. **El criterio del 13/11** con las funciones de medir.py (la pieza sola por el decodificador de `main`), con E2
   dejando un partido fuera en la misma ejecución. También el `spellF1` con equipo oráculo, que no decide.
2. **El harness con el `D` propio:** el pipeline de `main` (`puntuar.ejecutar`, modo "propio") con su `dead_state`
   cambiado por el candidato, frente a `main` tal cual. Con el balón en los `D` tapado (`dfl.tracking_de`, como
   `puntuar.py --d propio`) y a la vista (`d_propio.con_balon_en_d`). Votan las dos convenciones × las dos condiciones
   de `dfl.VOTAN` × los dos modos: ocho celdas. Las otras condiciones, con el balón tapado, sin voto.
"""

import argparse
import collections
import hashlib
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(ROOT, "validation", "apuesta_b"))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import arboles  # noqa: E402
import d_propio  # noqa: E402
import dfl  # noqa: E402
import entrenar  # noqa: E402
import medir  # noqa: E402
import puntuar  # noqa: E402
from possession import dead_state, tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
CANDIDATOS = ("G2", "G3")
REFERENCIA = "E2"

# La regla de entrada (docs/decisiones.md, 16/11).
MEJORA_MIN = 0.010  # de spellF1 frente a main, con los 7 partidos juntos, en cada celda que vota
PARTIDOS_MIN = 6  # de 7: en cuántos tiene que ganar a main en cada celda
TOLERANCIA_PCT = 0.01  # el inicio y el fin a ≤ 25 frames no bajan más de 1 punto frente a E2
TOLERANCIA_SESGO = 1.0  # frames: el |sesgo mediano| de cada borde no sube más de esto frente a E2

MAIN = "main (E2 del módulo, en muestra)"
E2_FUERA = "E2 dejando un partido fuera (sin voto)"
MODOS = collections.OrderedDict([("tapado", dfl.tracking_de), ("a la vista", d_propio.con_balon_en_d)])


# -- 1. el criterio del 13/11 -----------------------------------------------------------------------------

def medir_criterio(cargados, logit, modelos, base, n_draws, sensibilidad, avisar):
    """Lo que devuelve `medir.medir`, con E2, G2 y G3 (y su sensibilidad), para las tablas de medir.py."""
    indice = {datos["partido"]: k for k, datos in enumerate(cargados)}
    referencia = collections.defaultdict(list)  # el control: ningún `D`
    for datos in cargados:
        sin_d = np.zeros(len(datos["trk"].bx), dtype=bool)
        for clave, recuento in medir.recuentos_spell(datos, sin_d).items():
            referencia[clave].append(recuento)

    def temblor(nombre, sigma):
        if nombre == REFERENCIA:
            return lambda d: dead_state.log_odds(medir.con_temblor(d["trk"], sigma, indice[d["partido"]]),
                                                 logit[d["partido"]])
        return lambda d: arboles.puntuacion(modelos[nombre][d["partido"]], arboles.CANDIDATOS[nombre],
                                            medir.con_temblor(d["trk"], sigma, indice[d["partido"]]))

    versiones = collections.OrderedDict()
    for nombre in (REFERENCIA,) + CANDIDATOS:
        puntos = base[nombre]
        versiones[nombre] = medir.medir_version(cargados, lambda d: puntos[d["partido"]])
        avisar("criterio: medido {}".format(nombre))
        if not sensibilidad:
            continue
        if nombre != REFERENCIA:  # el placebo y las escalas de E2 ya están medidos (14/11)
            versiones[nombre + ", placebo: desplazada 60 s"] = medir.medir_version(
                cargados, lambda d: medir.desplazada(puntos[d["partido"]], d["trk"].blocks, medir.PLACEBO_FRAMES))
            for escala in medir.ESCALAS:
                versiones["{}, escala × {:g}".format(nombre, escala)] = medir.medir_version(
                    cargados, lambda d: np.clip(escala * puntos[d["partido"]],
                                                -dead_state.SCORE_CLIP, dead_state.SCORE_CLIP))
        for sigma in medir.TEMBLORES:
            versiones["{}, temblor de {:g} m".format(nombre, sigma)] = medir.medir_version(cargados, temblor(nombre, sigma))
        avisar("criterio: medida la sensibilidad de {}".format(nombre))

    frente_al_control = {nombre: {clave: medir.comparar(v["spell"][clave], referencia[clave], n_draws)
                                  for clave in referencia} for nombre, v in versiones.items()}
    control = {clave: medir.comparar(referencia[clave], referencia[clave], 0) for clave in referencia}
    entre = {(a, b): {clave: medir.comparar(versiones[a]["spell"][clave], versiones[b]["spell"][clave], n_draws)
                      for clave in referencia}
             for a, b in (("G2", REFERENCIA), ("G3", REFERENCIA), ("G3", "G2"))}
    return {"partidos": [d["partido"] for d in cargados], "versiones": versiones, "control": control,
            "frente_al_control": frente_al_control, "entre_candidatos": entre}


def no_empeora(fila, ref):
    """La parte 2 de la regla: [(texto, cumple)] de un candidato frente a E2 (filas de `medir.juntar_paradas`)."""
    return [
        ("espurios ≤ {:g} por minuto".format(medir.ESPURIOS_MAX), fila["espurios_min"] <= medir.ESPURIOS_MAX),
        ("ninguna racha de menos de {} frames".format(medir.RACHA_MIN), fila["d_cortas"] + fila["juego_cortas"] == 0),
        ("inicio a ≤ 25 frames no baja más de 1 punto", fila["inicio_ok"] >= ref["inicio_ok"] - TOLERANCIA_PCT),
        ("fin a ≤ 25 frames no baja más de 1 punto", fila["fin_ok"] >= ref["fin_ok"] - TOLERANCIA_PCT),
        ("|sesgo mediano del inicio| no sube más de 1 frame",
         abs(fila["inicio_p50"]) <= abs(ref["inicio_p50"]) + TOLERANCIA_SESGO),
        ("|sesgo mediano del fin| no sube más de 1 frame",
         abs(fila["fin_p50"]) <= abs(ref["fin_p50"]) + TOLERANCIA_SESGO),
    ]


# -- 2. el harness con el `D` propio ----------------------------------------------------------------------

class Piezas:
    """Las piezas de `dead_state` de cada versión, con `fuera` como las de la entrega que dejan fuera un partido.

    Los jugadores son los mismos en todas las condiciones y en los dos modos del balón (`dfl.tracking_de` baraja
    los slots igual en todas), así que la puntuación de un partido se calcula una vez. La clave lleva la huella de
    las posiciones de los jugadores: si cambiaran, se recalcularía.
    """

    def __init__(self, logit, modelos):
        self.logit, self.modelos, self.hechas = logit, modelos, {}

    def _memo(self, nombre, fuera, trk, calcular):
        huella = hashlib.sha1(np.ascontiguousarray(trk.px).tobytes() + np.ascontiguousarray(trk.py).tobytes())
        clave = (nombre, fuera, huella.hexdigest())
        if clave not in self.hechas:
            self.hechas[clave] = calcular()
        score, allowed = tracking.no_evidence(len(trk.bx))
        score[:, D] = self.hechas[clave]
        return score, allowed

    def e2(self):
        def evidence(trk, fuera=None):
            return self._memo(REFERENCIA, fuera, trk, lambda: dead_state.log_odds(trk, self.logit[fuera]))
        return evidence

    def arbol(self, nombre):
        def evidence(trk, fuera=None):
            return self._memo(nombre, fuera, trk, lambda: arboles.puntuacion(
                self.modelos[nombre][fuera], arboles.CANDIDATOS[nombre], trk))
        return evidence


def versiones_harness(piezas):
    pieza = lambda f: {"tipo": "pipeline", "params": None, "piezas": {"dead_state": f}, "fuera": ["dead_state"]}  # noqa: E731
    versiones = collections.OrderedDict([(MAIN, {"tipo": "pipeline", "params": None, "piezas": {}}),
                                         (E2_FUERA, pieza(piezas.e2()))])
    for nombre in CANDIDATOS:
        versiones[nombre] = pieza(piezas.arbol(nombre))
    return versiones


def celdas():
    """(modo, condición, vota) en el orden de las tablas."""
    out = [(modo, c, True) for modo in MODOS for c in dfl.VOTAN]
    out += [("tapado", c, False) for c in dfl.CONDICIONES if c not in dfl.VOTAN]
    return out


def medir_harness(partidos, versiones, avisar):
    """Recuentos del scorer y cobertura del `D` por (modo, condición, convención, versión) y partido."""
    recuentos = collections.defaultdict(list)
    cobertura = collections.defaultdict(lambda: np.zeros(5, dtype=np.int64))
    for partido in partidos:
        inicio = time.time()
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        for modo, condicion, _ in celdas():
            trk = puntuar.solo_lectura(MODOS[modo](cargado, condicion))
            evaluado = np.zeros(len(trk.bx), bool)
            for a, b in trk.blocks:
                evaluado[a:b] = True
            reales = d_propio.paradas(gt["flag"], trk.blocks)
            real_d = (gt["flag"] == D) & evaluado
            for nombre, version in versiones.items():
                pred = puntuar.ejecutar(version, trk, gt["flag"], "propio", partido)
                es_d = (pred == D) & evaluado
                vistas = sum(np.mean(pred[i:j] == D) >= d_propio.MITAD for i, j in reales)
                cobertura[(modo, condicion, nombre)] += [int(np.sum(es_d & real_d)), int(real_d.sum()),
                                                         int(es_d.sum()), vistas, len(reales)]
                for convencion in dfl.CONVENCIONES:
                    recuentos[(modo, condicion, convencion, nombre)].append(puntuar.contar(gt[convencion], pred))
        avisar("harness: hecho {} en {:.0f} s".format(partido, time.time() - inicio))
    return recuentos, cobertura


def frente_a(candidato, referencia, n_draws):
    f1_c = [puntuar.spell_f1(r["flags"], r["n_pred"]) for r in candidato]
    f1_r = [puntuar.spell_f1(r["flags"], r["n_pred"]) for r in referencia]
    junto_c, junto_r = puntuar.juntar(candidato), puntuar.juntar(referencia)
    return {"spell_f1": puntuar.spell_f1(*junto_c),
            "diferencia": puntuar.spell_f1(*junto_c) - puntuar.spell_f1(*junto_r),
            "intervalo": puntuar.diferencia_bootstrap(junto_c, junto_r, n_draws),
            "gana_en": int(sum(c > r for c, r in zip(f1_c, f1_r))), "n": len(f1_c)}


def resumir_harness(recuentos, versiones, n_draws):
    """{(modo, condición, convención): {"main": spellF1, versión: comparación frente a main}}."""
    out = collections.OrderedDict()
    for modo, condicion, _ in celdas():
        for convencion in dfl.CONVENCIONES:
            de_main = recuentos[(modo, condicion, convencion, MAIN)]
            fila = {"main": puntuar.spell_f1(*puntuar.juntar(de_main))}
            for nombre in versiones:
                if nombre != MAIN:
                    fila[nombre] = frente_a(recuentos[(modo, condicion, convencion, nombre)], de_main, n_draws)
            out[(modo, condicion, convencion)] = fila
    return out


def gana_en_harness(resumen, nombre, n_partidos, contra=None):
    """La parte 1 de la regla en las ocho celdas que votan: [(celda, cumple)]."""
    out = []
    for (modo, condicion, convencion), fila in resumen.items():
        if condicion not in dfl.VOTAN:
            continue
        c = fila[nombre] if contra is None else contra[(modo, condicion, convencion)]
        ok = c["diferencia"] >= MEJORA_MIN and c["gana_en"] >= min(PARTIDOS_MIN, n_partidos)
        out.append(("{}, {}, {}".format(modo, condicion, convencion), ok))
    return out


# -- salida -----------------------------------------------------------------------------------------------

def tabla_harness(resumen, versiones, n):
    otras = [nombre for nombre in versiones if nombre != MAIN]
    lineas = ["### Harness con el `D` propio, {} partidos juntos, frente a `main`".format(n), "",
              "Cada celda: `spellF1` · diferencia con `main` [intervalo del 5 al 95 % del bootstrap pareado] · en "
              "cuántos partidos gana a `main`. Votan las filas con «sí».", "",
              "| balón en los `D` | condición | convención | vota | `main` | " + " | ".join(otras) + " |",
              "|---|---|---|---|---|" + "---|" * len(otras)]
    for (modo, condicion, convencion), fila in resumen.items():
        celdas_v = []
        for nombre in otras:
            c = fila[nombre]
            texto = "{} · {}".format(medir.num(c["spell_f1"]), medir.num(c["diferencia"], True))
            if c["intervalo"]:
                texto += " [{} a {}]".format(medir.num(c["intervalo"][0], True), medir.num(c["intervalo"][1], True))
            celdas_v.append(texto + " · {} de {}".format(c["gana_en"], c["n"]))
        lineas.append("| {} | {} | {} | {} | {} | {} |".format(
            modo, condicion, convencion, "sí" if condicion in dfl.VOTAN else "no", medir.num(fila["main"]),
            " | ".join(celdas_v)))
    lineas.append("")
    return "\n".join(lineas)


def tabla_cobertura(cobertura, versiones):
    lineas = ["### Cuánto `D` ve cada versión en el harness (descriptivo)", "",
              "| balón en los `D` | condición | versión | frames `D` reales vistos como `D` | de lo que dice `D`, es `D` "
              "| paradas vistas (≥ mitad de sus frames) |", "|---|---|---|---|---|---|"]
    for modo, condicion, _ in celdas():
        for nombre in versiones:
            bien, reales, dichos, vistas, n = cobertura[(modo, condicion, nombre)]
            lineas.append("| {} | {} | {} | {} | {} | {} de {} ({}) |".format(
                modo, condicion, nombre, medir.pct(bien / max(reales, 1)), medir.pct(bien / max(dichos, 1)),
                vistas, n, medir.pct(vistas / max(n, 1))))
    lineas.append("")
    return "\n".join(lineas)


def veredictos(criterio, resumen, n):
    lineas = ["### Lectura con la regla fijada antes de medir (docs/decisiones.md, 16/11)", ""]
    ref = criterio["versiones"][REFERENCIA]["paradas"]
    ganan = []
    for nombre in CANDIDATOS:
        harness = gana_en_harness(resumen, nombre, n)
        fallos_h = [celda for celda, ok in harness if not ok]
        partes = no_empeora(criterio["versiones"][nombre]["paradas"], ref)
        fallos_c = [texto for texto, ok in partes if not ok]
        lineas.append("- **{}, harness (+{:.3f} y {} de {} en las ocho celdas):** {}".format(
            nombre, MEJORA_MIN, min(PARTIDOS_MIN, n), n,
            "**cumple**" if not fallos_h else "**no cumple** en {} de 8 ({})".format(len(fallos_h), "; ".join(fallos_h))))
        lineas.append("- **{}, criterio del 13/11 frente a E2:** {}".format(
            nombre, "**no empeora**" if not fallos_c else "**empeora** ({})".format("; ".join(fallos_c))))
        if not fallos_h and not fallos_c:
            ganan.append(nombre)
    if not ganan:
        lineas.append("- **Ningún candidato gana: la idea 2.4 se cierra.**")
    elif len(ganan) == 1:
        lineas.append("- **Gana {}.**".format(ganan[0]))
    else:
        g3_sobre_g2 = gana_en_harness(resumen, "G3", n, contra={k: v["G3_frente_a_G2"] for k, v in resumen.items()})
        entra = "G3" if all(ok for _, ok in g3_sobre_g2) else "G2"
        lineas.append("- **Ganan los dos; G3 frente a G2 en las ocho celdas: {}. Entra {}.**".format(
            "gana" if entra == "G3" else "no gana", entra))
    return "\n".join(lineas)


def main():
    parser = argparse.ArgumentParser(description="Mide G2 y G3 frente a E2 con la regla del 16/11.")
    parser.add_argument("--partidos", nargs="+", default=list(entrenar.PARTIDOS), choices=list(entrenar.PARTIDOS))
    parser.add_argument("--bootstrap", type=int, default=1000, help="remuestreos del intervalo; 0 lo quita")
    parser.add_argument("--sin-sensibilidad", action="store_true", help="sin el placebo, las escalas ni el temblor")
    args = parser.parse_args()
    if len(args.partidos) < 2:
        sys.exit("Hacen falta al menos dos partidos: los modelos se entrenan dejando uno fuera.")

    inicio = time.time()

    def avisar(texto):
        print("{} ({:.0f} s)".format(texto, time.time() - inicio), file=sys.stderr)

    cargados = []
    for partido in args.partidos:
        cargados.append(entrenar.cargar(partido))
        avisar("cargado {}".format(partido))
    logit = arboles.dejando_fuera(cargados, dead_state.E2, entrenar.ajustar)
    modelos = {}
    for nombre in CANDIDATOS:
        modelos[nombre] = arboles.dejando_fuera(cargados, arboles.CANDIDATOS[nombre])
        avisar("entrenado {} dejando un partido fuera".format(nombre))
    base = {REFERENCIA: {d["partido"]: dead_state.log_odds(d["trk"], logit[d["partido"]]) for d in cargados}}
    for nombre in CANDIDATOS:
        base[nombre] = {d["partido"]: arboles.puntuacion(modelos[nombre][d["partido"]], arboles.CANDIDATOS[nombre],
                                                         d["trk"]) for d in cargados}

    criterio = medir_criterio(cargados, logit, modelos, base, args.bootstrap, not args.sin_sensibilidad, avisar)
    del cargados

    versiones = versiones_harness(Piezas(logit, modelos))
    recuentos, cobertura = medir_harness(args.partidos, versiones, avisar)
    resumen = resumir_harness(recuentos, versiones, args.bootstrap)
    for (modo, condicion, convencion), fila in resumen.items():  # G3 frente a G2, para el desempate
        fila["G3_frente_a_G2"] = frente_a(recuentos[(modo, condicion, convencion, "G3")],
                                         recuentos[(modo, condicion, convencion, "G2")], 0)

    n = len(args.partidos)
    print("partidos: {} · bootstrap: {} · árboles: {} · scikit-learn en un entorno aparte".format(
        n, args.bootstrap, arboles.PARAMETROS))
    print()
    print(medir.tabla_criterio(criterio))
    print(medir.tabla_spell(criterio))
    print(tabla_harness(resumen, versiones, n))
    print(tabla_cobertura(cobertura, versiones))
    print(veredictos(criterio, resumen, n))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
