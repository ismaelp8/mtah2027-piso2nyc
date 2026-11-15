"""Fase 3: ¿limitan los rasgos o limita la forma lineal? Puerta con una red de una capa, fuera de muestra.

    python validation/posesiones_cortas/puerta_no_lineal.py

DFL (Bassek et al., 2025, CC BY 4.0) y la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`;
A-League 2024/25, licencia MIT). Lo puede ejecutar cualquiera, Claude incluido. Solo agregados. Solo numpy.
La red, los rasgos y la regla están fijados en BITACORA.md §10, con commit antes de ejecutar. No abre el
examen de SkillCorner.

Versiones, todas puntuadas como B5 (`aprendida.puntuacion_de("b5", ...)`) con el `D` de las etiquetas:
- `main`: B5, con los coeficientes del módulo;
- «lineal, 33»: B9, con los coeficientes del módulo;
- «red, 33»: la red con los rasgos de B9 (brazo 1);
- «lineal, 39» y «red, 39»: con los rasgos de B9 más los 6 de los jugadores alrededor de un cambio (brazo 2).

En la DFL cada partido se puntúa con el pliegue que no lo vio; en SkillCorner, con el de los 7 partidos.
"""

import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                 os.path.join(ROOT, "validation", "scripts"), os.path.join(ROOT, "validation", "apuesta_b"),
                 os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import diagnostico_errores as de  # noqa: E402
import entrenar  # noqa: E402
import possession_metrics as pm  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, ball, dead_state, temporal, tracking  # noqa: E402

H, A, D = tracking.H, tracking.A, tracking.D
# La red (BITACORA.md §10, fijada antes de ejecutar).
OCULTAS = 32
ITERACIONES_RED = 1500
PASO_ADAM = 0.01
L2 = 1e-4
SEMILLA = 20261115
# Los rasgos de los jugadores alrededor de un cambio: (serie, ventana).
VENTANAS_JUGADORES = (("velocidad", 25), ("velocidad", 75), ("dispersión", 50))
N9 = len(aprendida.NOMBRES["b9"])
VERSIONES = ("main (B5)", "lineal, 33 (B9)", "red, 33", "lineal, 39", "red, 39")
REFERENCIA_LINEAL = {"red, 33": "lineal, 33 (B9)", "red, 39": "lineal, 39"}
CORTAS = (50, 250)  # frames: posesiones de 2 a 10 s
SK_CONDICIONES = ("detectado", "detectado, suavizado")


# -- rasgos ----------------------------------------------------------------------------------------------

def media_hacia(valores, w, delante):
    """Media de [t, t+w) (hacia delante) o de (t−w, t] (hacia atrás), recortada en los bordes."""
    v = np.asarray(valores, dtype=np.float64)
    n = len(v)
    acumulada = np.concatenate(([0.0], np.cumsum(v)))
    i = np.arange(n)
    bajo, alto = (i, np.minimum(n, i + w)) if delante else (np.maximum(0, i - w + 1), i + 1)
    return (acumulada[alto] - acumulada[bajo]) / (alto - bajo)


def rasgos_jugadores(trk):
    """(n, 6): las dos series de B2 (velocidad del juego y diferencia de dispersión), hacia delante y atrás."""
    salida = np.zeros((len(trk.bx), 2 * len(VENTANAS_JUGADORES)))
    team = np.asarray(trk.team)
    columnas = [np.flatnonzero(team == e) for e in (H, A)]
    fps = float(trk.fps)
    for a, b in trk.blocks:
        (xh, yh, hh), (xa, ya, ha) = [aprendida._por_equipo(trk.px[a:b], trk.py[a:b], c) for c in columnas]
        media_h = np.where(hh, xh, 0.0).sum() / max(int(hh.sum()), 1)
        media_a = np.where(ha, xa, 0.0).sum() / max(int(ha.sum()), 1)
        direccion = float(np.sign(media_a - media_h)) if hh.any() and ha.any() else 0.0
        vh, va = aprendida._velocidad_x(xh, yh, fps), aprendida._velocidad_x(xa, ya, fps)
        series = {
            "velocidad": direccion * (aprendida._sin_nan(aprendida._media_filas(vh, np.isfinite(vh)))
                                      + aprendida._sin_nan(aprendida._media_filas(va, np.isfinite(va)))),
            "dispersión": aprendida._sin_nan(aprendida._dispersion(xh, yh, hh) - aprendida._dispersion(xa, ya, ha)),
        }
        lista = []
        for serie, w in VENTANAS_JUGADORES:
            lista += [media_hacia(series[serie], w, True), media_hacia(series[serie], w, False)]
        salida[a:b] = np.column_stack(lista)
    return salida


def preparar(trk, gt_flag=None):
    limpio = ball.clean(puntuar.solo_lectura(trk))
    dentro = np.zeros(len(trk.bx), bool)
    for a, b in trk.blocks:
        dentro[a:b] = True
    cercano = aprendida.equipo_mas_cercano(limpio)
    return {"rasgos": np.hstack([aprendida.rasgos(limpio, "b9"), rasgos_jugadores(limpio)]),
            "visible": aprendida.balon_visible(limpio), "cercano": np.where(dentro, cercano, -1),
            "n1": cercano, "estado_d": dead_state.evidence(limpio)[0][:, D], "blocks": trk.blocks}


# -- la red ----------------------------------------------------------------------------------------------

def ajustar_red(X, y):
    rms = np.sqrt(np.mean(X ** 2, axis=0))
    rms[rms == 0] = 1.0
    Z = X / rms
    rng = np.random.default_rng(SEMILLA)
    k, n = Z.shape[1], len(y)
    pesos = [rng.normal(0.0, 1.0 / np.sqrt(k), (k, OCULTAS)), rng.normal(0.0, 1.0 / np.sqrt(OCULTAS), OCULTAS)]
    m = [np.zeros_like(p) for p in pesos]
    v = [np.zeros_like(p) for p in pesos]
    b1, b2, eps = 0.9, 0.999, 1e-8
    for it in range(1, ITERACIONES_RED + 1):
        oculta = np.tanh(Z @ pesos[0])
        z = oculta @ pesos[1]
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        g = (p - y) / n
        grad = [Z.T @ (np.outer(g, pesos[1]) * (1.0 - oculta ** 2)) + L2 * pesos[0], oculta.T @ g + L2 * pesos[1]]
        for j in range(2):
            m[j] = b1 * m[j] + (1 - b1) * grad[j]
            v[j] = b2 * v[j] + (1 - b2) * grad[j] ** 2
            pesos[j] = pesos[j] - PASO_ADAM * (m[j] / (1 - b1 ** it)) / (np.sqrt(v[j] / (1 - b2 ** it)) + eps)
    perdida = float(np.mean(np.logaddexp(0.0, -np.where(y > 0.5, 1.0, -1.0) * z)))
    return {"rms": rms, "W1": pesos[0], "w2": pesos[1], "perdida": perdida}


def logit_red(modelo, X):
    return np.tanh((X / modelo["rms"]) @ modelo["W1"]) @ modelo["w2"]


def logit_de(version, modelo, rasgos):
    if version.startswith("red"):
        k = N9 if version == "red, 33" else rasgos.shape[1]
        return logit_red(modelo, rasgos[:, :k])
    k = len(aprendida.NOMBRES["b5"]) if version == "main (B5)" else N9 if version == "lineal, 33 (B9)" else rasgos.shape[1]
    return aprendida.logit(rasgos[:, :k], modelo)


# -- puntuar ---------------------------------------------------------------------------------------------

def decodificar(c, z, alfa, permitido=None):
    score, allowed = aprendida.puntuacion_de("b5", z, c["visible"], alfa, c["cercano"] if permitido is not None else c["n1"])
    score[:, D] += c["estado_d"]
    if permitido is not None:
        allowed = allowed & permitido
    return temporal.decode(score, allowed, c["blocks"])


def elegir_alfa(datos, partidos, version, modelo):
    """Como `entrenar.elegir_alfa_d_propio`: α de la rejilla de B5 con el `D` de main dentro, en `partidos`."""
    logits = {(p, c): logit_de(version, modelo, datos[p]["cond"][c]["rasgos"]) for p in partidos for c in dfl.VOTAN}
    medias = []
    for alfa in entrenar.ALFAS_D_PROPIO:
        recuentos = collections.defaultdict(list)
        for p in partidos:
            for c in dfl.VOTAN:
                pred = decodificar(datos[p]["cond"][c], logits[(p, c)], alfa)
                for conv in dfl.CONVENCIONES:
                    recuentos[(c, conv)].append(puntuar.contar(datos[p]["gt"][conv], pred))
        medias.append(float(np.mean([puntuar.spell_f1(*puntuar.juntar(r)) for r in recuentos.values()])))
    return entrenar.ALFAS_D_PROPIO[int(np.argmax(medias))]


def cortas_encontradas(gt, pred):
    runs = pm.valid_runs(gt)
    reales = pm.possession_spells(gt, runs)
    ok, _ = de.emparejar(reales, pm.possession_spells(pm.fill_abstentions(pred, runs), runs))
    sel = [CORTAS[0] <= b - a < CORTAS[1] for a, b, _ in reales]
    return np.array([int(np.sum(ok[sel])), int(np.sum(sel))])


def tabla(titulo, rec, cortas, claves):
    """rec[(clave, version)] = [recuentos por partido]; cortas[(clave, version)] = [encontradas, reales]."""
    print("\n### {}\n".format(titulo))
    print("| balón y etiquetas | versión | spellF1 | frente a main [5–95 %] · gana en | frente a su lineal [5–95 %] | "
          "2–10 s encontradas | posesiones predichas / reales |")
    print("|---|---|---|---|---|---|---|")
    veredicto = {}
    for clave in claves:
        ref = rec[(clave, VERSIONES[0])]
        jref = puntuar.juntar(ref)
        f1ref = [puntuar.spell_f1(r["flags"], r["n_pred"]) for r in ref]
        cref = cortas[(clave, VERSIONES[0])]
        for version in VERSIONES:
            r = rec[(clave, version)]
            j = puntuar.juntar(r)
            f1 = puntuar.spell_f1(*j)
            cc = cortas[(clave, version)]
            celda_main, celda_lin = "–", "–"
            if version != VERSIONES[0]:
                dif = f1 - puntuar.spell_f1(*jref)
                ic = puntuar.diferencia_bootstrap(j, jref, 1000)
                gana = int(sum(a > b for a, b in zip([puntuar.spell_f1(x["flags"], x["n_pred"]) for x in r], f1ref)))
                celda_main = "{:+.3f} [{:+.3f} a {:+.3f}] · {} de {}".format(dif, ic[0], ic[1], gana, len(r))
                veredicto[(clave, version)] = {"dif": dif, "ic": ic,
                                               "cortas": 100.0 * (cc[0] / max(cc[1], 1) - cref[0] / max(cref[1], 1))}
            if version in REFERENCIA_LINEAL:
                jl = puntuar.juntar(rec[(clave, REFERENCIA_LINEAL[version])])
                dl = f1 - puntuar.spell_f1(*jl)
                icl = puntuar.diferencia_bootstrap(j, jl, 1000)
                celda_lin = "{:+.3f} [{:+.3f} a {:+.3f}]".format(dl, icl[0], icl[1])
                veredicto[(clave, version)].update({"dif_lineal": dl, "ic_lineal": icl})
            print("| {} | {} | {:.3f} | {} | {} | {:.0f} % ({} de {}) | {} / {} |".format(
                clave, version, f1, celda_main, celda_lin, 100.0 * cc[0] / max(cc[1], 1), cc[0], cc[1], j[1],
                j[0].shape[1]).replace(".", ","))
    return veredicto


def main():
    inicio = time.time()
    datos = collections.OrderedDict()
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        datos[partido] = {"gt": gt, "cond": {c: preparar(dfl.tracking_de(cargado, c)) for c in dfl.VOTAN}}
        coinciden = (gt["flag"] == gt["control"]) & np.isin(gt["flag"], (H, A))
        datos[partido]["filas"] = np.flatnonzero(coinciden & (np.arange(len(coinciden)) % entrenar.PASO == 0))
        print("preparado {} en {:.0f} s".format(partido, time.time() - inicio), file=sys.stderr, flush=True)

    # Comprobación: la red es impar.
    prueba = datos[dfl.PARTIDOS[0]]["cond"][dfl.VOTAN[0]]["rasgos"][:2000]
    rng = np.random.default_rng(1)
    falsa = {"rms": np.ones(prueba.shape[1]), "W1": rng.normal(size=(prueba.shape[1], 8)), "w2": rng.normal(size=8)}
    if not np.allclose(logit_red(falsa, -prueba), -logit_red(falsa, prueba), atol=1e-12):
        raise AssertionError("la red no es impar")

    c0 = entrenar.CONDICION_ENTRENAMIENTO
    modelos = {}  # (pliegue, versión) -> (modelo, α)
    for clave in ["todos"] + list(dfl.PARTIDOS):
        fuera = None if clave == "todos" else clave
        entrena = [p for p in dfl.PARTIDOS if p != clave]
        X = np.vstack([datos[p]["cond"][c0]["rasgos"][datos[p]["filas"]] for p in entrena])
        y = np.concatenate([(datos[p]["gt"]["flag"][datos[p]["filas"]] == H).astype(float) for p in entrena])
        modelos[(clave, "main (B5)")] = (aprendida.coeficientes("b5", fuera)["pesos"], aprendida.coeficientes("b5", fuera)["alfa"])
        modelos[(clave, "lineal, 33 (B9)")] = (aprendida.coeficientes("b9", fuera)["pesos"],
                                               aprendida.coeficientes("b9", fuera)["alfa"])
        lineal39, _, _ = entrenar.ajustar(X, y)
        red33 = ajustar_red(X[:, :N9], y)
        red39 = ajustar_red(X, y)
        for version, modelo in (("lineal, 39", lineal39), ("red, 33", red33), ("red, 39", red39)):
            modelos[(clave, version)] = (modelo, elegir_alfa(datos, entrena, version, modelo))
        print("pliegue {}: α {} / {} / {}; pérdida de la red {:.4f} / {:.4f}; {:.0f} s".format(
            clave, modelos[(clave, "lineal, 39")][1], modelos[(clave, "red, 33")][1], modelos[(clave, "red, 39")][1],
            red33["perdida"], red39["perdida"], time.time() - inicio), file=sys.stderr, flush=True)

    print("# Fase 3: ¿limitan los rasgos o la forma lineal? (puerta, BITACORA.md §10)\n")
    print("α por pliegue (los 7 y sin cada partido), lineal 39 / red 33 / red 39: " + "; ".join(
        "{}: {:g} / {:g} / {:g}".format(k, modelos[(k, "lineal, 39")][1], modelos[(k, "red, 33")][1],
                                         modelos[(k, "red, 39")][1]) for k in ["todos"] + list(dfl.PARTIDOS)))

    rec, cortas = collections.defaultdict(list), collections.defaultdict(lambda: np.zeros(2, dtype=np.int64))
    for partido, d in datos.items():
        for cond in dfl.VOTAN:
            c = d["cond"][cond]
            _, permitido = puntuar.d_oraculo(d["gt"]["flag"])
            for version in VERSIONES:
                modelo, alfa = modelos[(partido, version)]
                pred = decodificar(c, logit_de(version, modelo, c["rasgos"]), alfa, permitido)
                for conv in dfl.CONVENCIONES:
                    clave = "{}, {}".format(cond, conv)
                    rec[(clave, version)].append(puntuar.contar(d["gt"][conv], pred))
                    cortas[(clave, version)] += cortas_encontradas(d["gt"][conv], pred)
    claves_dfl = ["{}, {}".format(cond, conv) for conv in ("control", "flag") for cond in dfl.VOTAN]
    v_dfl = tabla("DFL, cada partido con el pliegue que no lo vio, `D` oráculo", rec, cortas, claves_dfl)
    print("\nComprobación: `main` y B9 por este camino (spellF1 de arriba) tienen que ser 0,728 / 0,748 / 0,498 / 0,512 "
          "y 0,722 / 0,743 / 0,537 / 0,560.")
    del datos

    import lector as lc
    ids = [i for i in lc.partidos() if i in lc.ENTRENAMIENTO]
    lc.exigir_solo_entrenamiento(ids)
    rec_sk, cortas_sk = collections.defaultdict(list), collections.defaultdict(lambda: np.zeros(2, dtype=np.int64))
    for id_ in ids:
        crudo = lc.leer_crudo(id_)
        for cond in SK_CONDICIONES:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            c = preparar(trk)
            _, permitido = puntuar.d_oraculo(gt)
            for version in VERSIONES:
                modelo, alfa = modelos[("todos", version)]
                pred = decodificar(c, logit_de(version, modelo, c["rasgos"]), alfa, permitido)
                rec_sk[(cond, version)].append(puntuar.contar(gt, pred))
                cortas_sk[(cond, version)] += cortas_encontradas(gt, pred)
        print("hecho {} en {:.0f} s".format(id_, time.time() - inicio), file=sys.stderr, flush=True)
    v_sk = tabla("SkillCorner, `lector.ENTRENAMIENTO` ({} partidos), con el modelo de los 7 de la DFL, `D` oráculo".format(
        len(ids)), rec_sk, cortas_sk, list(SK_CONDICIONES))

    print("\n## Regla de BITACORA.md §10\n")
    abre = []
    for brazo in ("red, 33", "red, 39"):
        a = all(v_dfl[("{}, control".format(c), brazo)]["dif"] >= 0.010 and v_dfl[("{}, control".format(c), brazo)]["ic"][0] > 0
                for c in dfl.VOTAN)
        b = all(v_dfl[("{}, control".format(c), brazo)]["cortas"] >= 3.0 for c in dfl.VOTAN)
        cc = all(v_sk[(c, brazo)]["dif"] > 0 and v_sk[(c, brazo)]["ic"][0] > 0 for c in SK_CONDICIONES)
        lineal = all(v_dfl[("{}, control".format(c), brazo)]["dif_lineal"] >= 0.010
                     and v_dfl[("{}, control".format(c), brazo)]["ic_lineal"][0] > 0 for c in dfl.VOTAN)
        print("- {}: a) control +0,010 con intervalo > 0: **{}** · b) 2–10 s +3 puntos: **{}** · c) SkillCorner > 0 con "
              "intervalo > 0: **{}** · (descriptivo) gana a su lineal: **{}**".format(
                  brazo, *["sí" if x else "no" for x in (a, b, cc, lineal)]))
        if a and b and cc:
            abre.append(brazo)
    if abre:
        print("\n**Abre un candidato:** {} (el más simple si son los dos).".format(abre[0]))
    else:
        print("\n**Se cierra la pregunta:** con estos rasgos no hay más, ni con un modelo flexible (una red de una capa "
              "de 32).")
    print("tiempo: {:.0f} s".format(time.time() - inicio), file=sys.stderr)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
