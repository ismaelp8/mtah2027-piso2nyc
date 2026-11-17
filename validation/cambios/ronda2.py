"""Segunda ronda del detector de cambios de posesión en la DFL (docs/decisiones.md, 16/11, «segunda ronda»).

    python validation/cambios/ronda2.py            # hace falta la caché de probabilidades de medir.py

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar cualquiera, Claude incluido.
Solo imprime agregados. Usa scikit-learn.

Cuatro familias sobre las probabilidades de la primera ronda (`medir.py`), sin reentrenar la primera etapa:

- C: los cuatro detectores de la primera ronda, con la rejilla nueva (la capa también contra el otro equipo solo);
- A: avisos (la probabilidad corregida, en máximos separados);
- B: confirmación (un segundo modelo decide qué avisos son cambios);
- D: las reglas con sus umbrales afinados.

Un candidato por familia y balón: elige lo suyo dejando un partido fuera, con la media del spellF1 de control en las
dos condiciones que votan y los dos modos del `D`.
"""

import argparse
import collections
import concurrent.futures
import itertools
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import comun  # noqa: E402
import medir  # noqa: E402
from comun import cambios, dfl, puntuar, temporal  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# (w, γ, W, contra_d). La de `main` no hace nada.
MAIN = (0.0, 0.0, 0, False)
CONFIGS = [(w, g, v, d) for w in (0.0, 25.0) for g in (4.0, 8.0, 16.0) for v in (50, 100) for d in (False, True)]
CONFIGS_D = [(0.0, g, 50, d) for g in (4.0, 8.0) for d in (False, True)]
UMBRALES_A = (0.5, 0.7, 0.85)
UMBRAL_AVISO_B = 0.3
UMBRALES_B = (0.3, 0.5, 0.7)
SEPARACION = 25
REGLAS = list(itertools.product((20.0, 30.0, 45.0), (0.3, 0.4, 0.6), (12, 20, 30)))
PARAMETROS_B = dict(medir.PARAMETROS, min_samples_leaf=20)


def nombre(config):
    w, g, v, d = config
    return "main" if config == MAIN else "w {:g} · γ {:g} · W {}{}".format(w, g, v, " · contra el otro" if d else "")


def decodificar(base, p, config):
    w, gamma, ventana, contra_d = config
    score = base.score + cambios.capa(p, gamma, ventana, contra_d=contra_d)[0]
    return temporal.decode_cambios(score, base.allowed, base.blocks, bonus=cambios.rebaja(p, w))


def corregir(p, uno_de_cada=medir.UNO_DE_CADA):
    """La probabilidad sin el efecto de haber entrenado con uno de cada 5 frames «sin cambio»."""
    sin = np.clip(1.0 - p.sum(axis=1), 0.0, 1.0)
    return p / (uno_de_cada * sin + p.sum(axis=1) + 1e-12)[:, None]


def avisos(p, umbral, separacion=SEPARACION):
    """[(frame, equipo, p)]: el máximo de cada racha con p ≥ umbral; a menos de `separacion` de otro del mismo equipo
    gana el más alto (en el empate, el primero)."""
    salida = []
    for x in (0, 1):
        alto = p[:, x] >= umbral
        bordes = np.flatnonzero(np.diff(np.concatenate(([0], alto.astype(np.int8), [0]))))
        picos = [(float(p[a:b, x].max()), int(a + np.argmax(p[a:b, x]))) for a, b in zip(bordes[0::2], bordes[1::2])]
        quedan = []
        for valor, t in sorted(picos, key=lambda par: (-par[0], par[1])):
            if all(abs(t - u) >= separacion for u in quedan):
                quedan.append(t)
                salida.append((t, x, valor))
    return sorted(salida)


def p_de_avisos(n, lista):
    p = np.zeros((n, 2))
    for t, x, _ in lista:
        p[max(0, t - cambios.SEMIANCHO):t + cambios.SEMIANCHO + 1, x] = 1.0
    return p


def rasgos_de_avisos(trk, lista):
    """Una fila por aviso: lo que pasa en los 50 y 75 frames siguientes y en los 50 anteriores."""
    d, _ = cambios.distancias(trk)
    frames, equipos = cambios.toques(trk)
    filas = []
    for t, x, valor in lista:
        fila = [valor]
        for largo in (50, 75):
            tramo = d[t + 1:t + 1 + largo]
            con = ~np.isnan(tramo).any(axis=1)
            fila += [np.mean(tramo[con, x] < tramo[con, 1 - x]) if con.any() else np.nan,
                     np.median(tramo[con, x]) if con.any() else np.nan,
                     np.median(tramo[con, 1 - x]) if con.any() else np.nan,
                     1.0 - np.mean(con) if len(con) else np.nan]
        antes = d[max(0, t - 50):t]
        con = ~np.isnan(antes).any(axis=1)
        fila.append(np.mean(antes[con, 1 - x] < antes[con, x]) if con.any() else np.nan)
        despues, previos = (frames > t) & (frames <= t + 75), (frames >= t - 50) & (frames < t)
        fila += [np.sum(despues & (equipos == x)), np.sum(despues & (equipos != x)),
                 np.sum(previos & (equipos == x)), np.sum(previos & (equipos != x))]
        filas.append(fila)
    return np.array(filas, dtype=np.float32).reshape(len(lista), 14)


def avisos_de_partido(args):
    """Para la etapa B: {(balón, condición): (avisos, rasgos, si es bueno)} de un partido."""
    partido, ps = args
    cargado = dfl.cargar(partido)
    clase = comun.clases(cargado["gt"]["control"])
    salida = {}
    for condicion in dfl.VOTAN:
        for balon, (trk, _) in medir.balones_de(cargado, condicion).items():
            lista = avisos(corregir(ps[("aprendido", balon, condicion)]), UMBRAL_AVISO_B)
            bueno = np.array([bool((clase[max(0, t - cambios.SEMIANCHO):t + cambios.SEMIANCHO + 1] == 1 + x).any())
                              for t, x, _ in lista])
            salida[(balon, condicion)] = (lista, rasgos_de_avisos(trk, lista), bueno)
    return partido, salida


def puntuar_partido(args):
    """{(familia, balón, parámetro, config, condición, modo, convención): recuento} de un partido."""
    partido, ps, de_b = args
    cargado, _, bases = comun.cargar(partido)
    gt = cargado["gt"]
    n = len(gt["flag"])
    recuentos = {}
    for condicion in dfl.VOTAN:
        detectores = {}
        balones = medir.balones_de(cargado, condicion)
        for balon in medir.BALONES:
            for detector in medir.DETECTORES:
                detectores[("C " + detector, balon, None)] = (ps[(detector, balon, condicion)], CONFIGS)
            corregida = corregir(ps[("aprendido", balon, condicion)])
            for u in UMBRALES_A:
                detectores[("A avisos", balon, u)] = (p_de_avisos(n, avisos(corregida, u)), CONFIGS)
            lista, p2 = de_b[(balon, condicion)]
            for v in UMBRALES_B:
                quedan = [aviso for aviso, valor in zip(lista, p2) if valor >= v]
                detectores[("B confirmación", balon, v)] = (p_de_avisos(n, quedan), CONFIGS)
            for regla in REGLAS:
                detectores[("D reglas", balon, regla)] = (cambios.p_reglas(balones[balon][0], *regla), CONFIGS_D)
        for modo in comun.MODOS_D:
            base = bases[(condicion, modo)]
            main = temporal.decode(base.score, base.allowed, base.blocks)
            for convencion in dfl.CONVENCIONES:
                recuentos[("main", condicion, modo, convencion)] = puntuar.contar(gt[convencion], main)
            for (familia, balon, parametro), (p, configs) in detectores.items():
                for config in configs:
                    pred = decodificar(base, p, config)
                    for convencion in dfl.CONVENCIONES:
                        recuentos[(familia, balon, parametro, config, condicion, modo, convencion)] = puntuar.contar(
                            gt[convencion], pred)
    return partido, recuentos


def main():
    parser = argparse.ArgumentParser(description="Segunda ronda del detector de cambios de posesión, en la DFL.")
    parser.add_argument("--procesos", type=int, default=6)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    partidos = list(dfl.PARTIDOS)
    ruta = os.path.join(medir.carpeta_cache(), "p_{}_{}_{}.npz".format(medir.P_VIDEO, medir.SIGMA_VIDEO, medir.L_VIDEO))
    with np.load(ruta, allow_pickle=False) as z:
        todas = {tuple(k.split("|")): z[k] for k in z.files if "|" in k}
    ps = {p: {(d, b, c): v for (d, b, q, c), v in todas.items() if q == p} for p in partidos}

    # La etapa B: un modelo por partido dejado fuera y balón, entrenado con los avisos de «como el ATD» de los otros.
    from sklearn.ensemble import HistGradientBoostingClassifier
    from threadpoolctl import threadpool_limits
    with concurrent.futures.ProcessPoolExecutor(args.procesos) as pool:
        de_avisos = dict(pool.map(avisos_de_partido, [(p, ps[p]) for p in partidos]))
    de_b = collections.defaultdict(dict)
    print("# La etapa B: avisos de la primera etapa (u = {}) y cuántos son buenos\n".format(UMBRAL_AVISO_B),
          file=sys.stderr)
    with threadpool_limits(limits=1):
        for balon in medir.BALONES:
            for fuera in partidos:
                x = np.vstack([de_avisos[p][(balon, medir.CONDICION_ENTRENAMIENTO)][1] for p in partidos if p != fuera])
                y = np.concatenate([de_avisos[p][(balon, medir.CONDICION_ENTRENAMIENTO)][2] for p in partidos
                                    if p != fuera])
                modelo = HistGradientBoostingClassifier(**PARAMETROS_B).fit(x, y)
                for condicion in dfl.VOTAN:
                    lista, rasgos, _ = de_avisos[fuera][(balon, condicion)]
                    de_b[fuera][(balon, condicion)] = (lista, modelo.predict_proba(rasgos)[:, 1])
                print("# B «{}» sin {}: {} avisos, {} buenos".format(balon, fuera, len(y), int(y.sum())),
                      file=sys.stderr, flush=True)

    with concurrent.futures.ProcessPoolExecutor(args.procesos) as pool:
        recuentos = dict(pool.map(puntuar_partido, [(p, ps[p], dict(de_b[p])) for p in partidos]))

    print("# Segunda ronda del detector de cambios de posesión en la DFL\n")
    print("Código: {} · emulación del vídeo: p = {}, σ = {} m, L = {}\n".format(
        puntuar.version_del_codigo(), medir.P_VIDEO, medir.SIGMA_VIDEO, medir.L_VIDEO))
    print("Avisos de la etapa B (u = {}), «como el ATD», los 7 partidos: {}.\n".format(UMBRAL_AVISO_B, "; ".join(
        "{}: {} avisos, {:.0f} % buenos".format(
            b, sum(len(de_avisos[p][(b, medir.CONDICION_ENTRENAMIENTO)][0]) for p in partidos),
            100.0 * np.mean(np.concatenate([de_avisos[p][(b, medir.CONDICION_ENTRENAMIENTO)][2] for p in partidos])))
        for b in medir.BALONES)))

    familias = collections.OrderedDict()
    for clave in recuentos[partidos[0]]:
        if clave[0] != "main":
            familias.setdefault((clave[0], clave[1]), set()).add((clave[2], clave[3]))
    veredictos = []
    for (familia, balon), opciones in familias.items():
        opciones = sorted(opciones, key=repr)

        def nota(opcion, resto):
            return np.mean([comun.spell([recuentos[p][(familia, balon) + opcion + (c, m, "control")] for p in resto])
                            for c in dfl.VOTAN for m in comun.MODOS_D])
        elegidas = {fuera: max(opciones, key=lambda o: (nota(o, [p for p in partidos if p != fuera]),
                                                       -opciones.index(o))) for fuera in partidos}
        print("\n## {} · balón «{}»\n".format(familia, balon))
        print("Elegido para cada partido con los otros seis: {}.\n".format("; ".join(
            "{}{} en {}".format("" if o[0] is None else "{} · ".format(o[0]), nombre(o[1]), k)
            for o, k in collections.Counter(elegidas.values()).most_common())))
        print("| `D` | condición | etiquetas | main | candidato | diferencia [intervalo] | gana en |")
        print("|---|---|---|---|---|---|---|")
        pasa_1, pasa_3 = True, True
        for modo in comun.MODOS_D:
            for condicion in dfl.VOTAN:
                for convencion in dfl.CONVENCIONES[::-1]:
                    cand = [recuentos[p][(familia, balon) + elegidas[p] + (condicion, modo, convencion)]
                            for p in partidos]
                    ref = [recuentos[p][("main", condicion, modo, convencion)] for p in partidos]
                    dif, intervalo, gana = comun.frente_a(cand, ref, args.bootstrap)
                    if convencion == "control":
                        pasa_1 &= dif >= medir.UMBRAL_ENTRADA and gana >= medir.MIN_PARTIDOS
                    else:
                        pasa_3 &= dif >= -medir.DANO
                    print("| {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} [{:+.3f} a {:+.3f}] | {} de {} |".format(
                        "etiquetas" if modo == "oraculo" else "propio", condicion, convencion, comun.spell(ref),
                        comun.spell(cand), dif, intervalo[0], intervalo[1], gana, len(partidos)))
        veredictos.append((familia, balon, pasa_1, pasa_3))
        mejor = max(opciones, key=lambda o: nota(o, partidos))
        print("\nRegla: punto 1 **{}** · punto 3 **{}**. La mejor opción con los 7 a la vez (descriptivo): {}{}, "
              "media de control {:+.3f} frente a `main`.".format(
                  "pasa" if pasa_1 else "no pasa", "pasa" if pasa_3 else "no pasa",
                  "" if mejor[0] is None else "{} · ".format(mejor[0]), nombre(mejor[1]),
                  nota(mejor, partidos) - np.mean([comun.spell([recuentos[p][("main", c, m, "control")]
                                                                for p in partidos])
                                                   for c in dfl.VOTAN for m in comun.MODOS_D])))

    print("\n## Veredicto con la regla (puntos 1 y 3)\n")
    for familia, balon, pasa_1, pasa_3 in veredictos:
        print("- {} · balón «{}»: punto 1 {}, punto 3 {} → **{}**".format(
            familia, balon, "pasa" if pasa_1 else "no pasa", "pasa" if pasa_3 else "no pasa",
            "sigue a SkillCorner" if pasa_1 and pasa_3 else "no entra"))


if __name__ == "__main__":
    main()
