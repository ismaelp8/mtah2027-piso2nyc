"""Mide el detector de cambios de posesión en la DFL, con la regla del 16/11 (docs/decisiones.md).

    python validation/cambios/medir.py                 # entrena (o lee la caché), mide y aplica la regla
    python validation/cambios/medir.py --reentrenar    # ignora la caché de probabilidades

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del harness. Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. Usa scikit-learn (no entra en requirements-entrega.txt).

Variantes (qué balón ve el detector; B5 y el `D` siguen con el balón «como el ATD» de la condición):

- «respaldo»: el balón de la condición del harness;
- «vídeo»: donde ese balón se ve, con probabilidad P_VIDEO es el balón limpio más un ruido gaussiano SIGMA_VIDEO, y
  si no, el de la condición; los fallos van en rachas de longitud media L_VIDEO (la emulación de
  validation/balon_video/BITACORA.md, condición 5, en la celda provisional de la decisión).

Detectores: el aprendido (`HistGradientBoostingClassifier`, un modelo por partido dejado fuera, entrenado con la
condición «como el ATD» de los otros seis) y la línea base con reglas (`cambios.p_reglas`).

El candidato de cada detector es uno: para cada partido, la combinación (w, γ, W) que más saca en los otros seis
(media del spellF1 de control en las dos condiciones que votan, con el `D` de las etiquetas y las probabilidades
fuera de muestra), puntuada en ese.
"""

import argparse
import collections
import concurrent.futures
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "scripts"))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
import comun  # noqa: E402
import diagnostico_errores as de  # noqa: E402
import dfl_lector  # noqa: E402
from comun import cambios, dfl, puntuar  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEMILLA = 20261116
P_VIDEO, SIGMA_VIDEO, L_VIDEO = 0.8, 0.06, 12  # la celda provisional, hasta que la puerta 1b mida el detector
CONDICION_ENTRENAMIENTO = "como el ATD"
UNO_DE_CADA = 5  # de los frames «sin cambio» entra uno de cada 5
PARAMETROS = {"learning_rate": 0.1, "max_iter": 200, "max_leaf_nodes": 31, "min_samples_leaf": 100,
              "l2_regularization": 1.0, "early_stopping": False, "random_state": 0}
BALONES = ("respaldo", "vídeo")
DETECTORES = ("aprendido", "reglas")
UMBRAL_ENTRADA, DANO, MIN_PARTIDOS = 0.005, 0.005, 6  # el límite de daño del 16/11


def carpeta_cache():
    return os.path.join(os.path.dirname(dfl_lector.carpeta_cache()), "cambios_cache")


def rachas_de_fallos(n, p, largo, rng):
    """(n,) bool: True donde el detector del vídeo acierta. Fallos en rachas geométricas de media `largo`; aciertos,
    en rachas de media `largo · p / (1 − p)`, para que acierte la fracción p."""
    if p >= 1.0:
        return np.ones(n, dtype=bool)
    acierta = np.ones(n, dtype=bool)
    media_acierto = max(1.0, largo * p / (1.0 - p))
    t = int(rng.geometric(1.0 / media_acierto)) if rng.random() < p else 0
    while t < n:
        fallo = int(rng.geometric(1.0 / largo))
        acierta[t:t + fallo] = False
        t += fallo + int(rng.geometric(1.0 / media_acierto))
    return acierta


def como_el_video(trk, limpio, rng, p=P_VIDEO, sigma=SIGMA_VIDEO, largo=L_VIDEO):
    """(tracking con el balón «como el vídeo», fuente): la emulación de la decisión. `trk` no cambia."""
    n = len(trk.bx)
    del_video = rachas_de_fallos(n, p, largo, rng) & ~np.isnan(trk.bx) & ~np.isnan(limpio.bx)
    bx = np.where(del_video, limpio.bx + rng.normal(0.0, sigma, n), trk.bx)
    by = np.where(del_video, limpio.by + rng.normal(0.0, sigma, n), trk.by)
    return trk._replace(bx=bx, by=by), del_video


def balones_de(cargado, condicion):
    """{balón: (tracking, fuente)} de un partido y una condición."""
    trk = dfl.tracking_de(cargado, condicion)
    limpio = dfl.tracking_de(cargado, "limpio")
    rng = np.random.default_rng([SEMILLA, cargado["indice"], dfl.CONDICIONES.index(condicion)])
    return {"respaldo": (trk, None), "vídeo": como_el_video(trk, limpio, rng)}


def rasgos_dobles(trk, fuente):
    """(X, X con los equipos intercambiados, nombres)."""
    x, nombres = cambios.rasgos(trk, fuente)
    girado, _ = cambios.rasgos(trk._replace(team=1 - np.asarray(trk.team)), fuente)
    return x.astype(np.float32), girado.astype(np.float32), nombres


def preparar(partido):
    """De un partido: las filas de entrenamiento de cada balón (condición de entrenamiento), la línea base con
    reglas en cada balón y condición, y sus clases (control). Los rasgos enteros no se guardan: `predecir_partido`
    los vuelve a calcular (misma semilla, mismo balón)."""
    cargado = dfl.cargar(partido)
    clase = comun.clases(cargado["gt"]["control"])
    salida = {"clase": clase, "filas": {}, "reglas": {}}
    for condicion in dfl.VOTAN:
        for balon, (trk, fuente) in balones_de(cargado, condicion).items():
            if condicion == CONDICION_ENTRENAMIENTO:
                salida["filas"][balon] = filas_de_entrenamiento(clase, *rasgos_dobles(trk, fuente)[:2])
            salida["reglas"][(balon, condicion)] = cambios.p_reglas(trk)
    return partido, salida


def predecir_partido(args):
    """{(balón, condición): p} de un partido con sus modelos (los que no lo vieron)."""
    partido, modelos = args
    from threadpoolctl import threadpool_limits
    cargado = dfl.cargar(partido)
    salida = {}
    with threadpool_limits(limits=1):
        for condicion in dfl.VOTAN:
            for balon, (trk, fuente) in balones_de(cargado, condicion).items():
                dentro = np.zeros(len(trk.bx), dtype=bool)
                for a, b in trk.blocks:
                    dentro[a:b] = True
                salida[(balon, condicion)] = predecir(modelos[balon], *rasgos_dobles(trk, fuente)[:2], dentro)
    return partido, salida


def filas_de_entrenamiento(clase, x, girado):
    """(X, y) de un partido: todos los frames de cambio y uno de cada `UNO_DE_CADA` de los demás vivos, dos veces
    (la segunda, con los equipos intercambiados y «hacia H» por «hacia A»)."""
    sin = np.flatnonzero(clase == 0)[::UNO_DE_CADA]
    filas = np.sort(np.concatenate((np.flatnonzero(clase > 0), sin)))
    y = clase[filas].astype(np.int64)
    y_girada = np.where(y > 0, 3 - y, 0)
    return np.vstack((x[filas], girado[filas])), np.concatenate((y, y_girada))


def predecir(modelo, x, girado, dentro):
    """`p` (n, 2): la media de la predicción y de la del partido con los equipos intercambiados; 0 fuera."""
    p = np.zeros((len(x), 2))
    directa, girada = modelo.predict_proba(x[dentro]), modelo.predict_proba(girado[dentro])
    p[dentro, 0] = 0.5 * (directa[:, 1] + girada[:, 2])
    p[dentro, 1] = 0.5 * (directa[:, 2] + girada[:, 1])
    return np.clip(p, 0.0, 1.0)


def entrenar(preparados, partidos, avisar):
    """{partido: {balón: modelo}}: para cada partido, el modelo entrenado con los otros seis."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from threadpoolctl import threadpool_limits
    modelos = collections.defaultdict(dict)
    with threadpool_limits(limits=1):
        for balon in BALONES:
            for fuera in partidos:
                datos = [preparados[p]["filas"][balon] for p in dfl.PARTIDOS if p != fuera]
                x, y = np.vstack([d[0] for d in datos]), np.concatenate([d[1] for d in datos])
                modelos[fuera][balon] = HistGradientBoostingClassifier(**PARAMETROS).fit(x, y)
                avisar("entrenado «{}» sin {}: {} filas, {} de cambio".format(balon, fuera, len(y), int(np.sum(y > 0))))
    return modelos


def calidad(p, clase, gt, umbral=0.5):
    """Recuentos del detector frente a los cambios reales de control: (cambios reales, vistos, avisos, buenos, frames
    vivos). Visto: algún frame a 12 o menos con p hacia ese equipo ≥ umbral. Aviso: racha de frames con p ≥ umbral
    hacia un equipo; bueno si pisa un frame de su clase."""
    frames, hacia = comun.cambios_directos(gt)
    vistos = sum(bool((p[max(0, t - cambios.SEMIANCHO):t + cambios.SEMIANCHO + 1, x] >= umbral).any())
                 for t, x in zip(frames, hacia))
    avisos = buenos = 0
    for x in (0, 1):
        alto = p[:, x] >= umbral
        bordes = np.flatnonzero(np.diff(np.concatenate(([0], alto.astype(np.int8), [0]))))
        for a, b in zip(bordes[0::2], bordes[1::2]):
            avisos += 1
            buenos += bool((clase[a:b] == 1 + x).any())
    return np.array([len(frames), vistos, avisos, buenos, int(np.sum(clase >= 0))])


def puntuar_partido(args):
    """Los recuentos de un partido: {(detector, balón, condición, modo, convención, config): recuento}."""
    partido, ps = args
    cargado, _, bases = comun.cargar(partido)
    gt = cargado["gt"]
    recuentos, predichas = {}, {}
    for (condicion, modo), base in bases.items():
        main = comun.decodificar(base, None, comun.MAIN)
        for (detector, balon, cond_p), p in ps.items():
            if cond_p != condicion:
                continue
            for config in comun.CONFIGS:
                pred = main if config == comun.MAIN else comun.decodificar(base, p, config)
                for convencion in dfl.CONVENCIONES:
                    recuentos[(detector, balon, condicion, modo, convencion, config)] = puntuar.contar(
                        gt[convencion], pred)
                if condicion == de.CONDICION_DFL and modo == "oraculo":
                    predichas[(detector, balon, config)] = pred
    return partido, recuentos, predichas, gt


def elegir(recuentos, partidos, detector, balon):
    """{partido: config}: la que más saca en los otros (control, `D` de las etiquetas, las dos que votan)."""
    elegidas = {}
    for fuera in partidos:
        resto = [p for p in partidos if p != fuera]

        def nota(config):
            return np.mean([comun.spell([recuentos[p][(detector, balon, c, "oraculo", "control", config)]
                                         for p in resto]) for c in dfl.VOTAN])
        elegidas[fuera] = max(comun.CONFIGS, key=lambda c: (nota(c), -comun.CONFIGS.index(c)))
    return elegidas


def main():
    parser = argparse.ArgumentParser(description="Mide el detector de cambios de posesión en la DFL.")
    parser.add_argument("--procesos", type=int, default=4)
    parser.add_argument("--reentrenar", action="store_true", help="no leer la caché de probabilidades")
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    partidos = list(dfl.PARTIDOS)

    def avisar(texto):
        print("# " + texto, file=sys.stderr, flush=True)

    ruta = os.path.join(carpeta_cache(), "p_{}_{}_{}.npz".format(P_VIDEO, SIGMA_VIDEO, L_VIDEO))
    if os.path.isfile(ruta) and not args.reentrenar:
        with np.load(ruta, allow_pickle=False) as z:
            ps = {tuple(k.split("|")): z[k] for k in z.files if "|" in k}
            cal = z["calidad"]
        avisar("probabilidades leídas de la caché")
    else:
        with concurrent.futures.ProcessPoolExecutor(args.procesos) as pool:
            preparados = dict(pool.map(preparar, partidos))
        avisar("rasgos calculados")
        modelos = entrenar(preparados, partidos, avisar)
        ps = {}
        with concurrent.futures.ProcessPoolExecutor(args.procesos) as pool:
            for p, salida in pool.map(predecir_partido, [(p, modelos[p]) for p in partidos]):
                for (balon, condicion), valor in salida.items():
                    ps[("aprendido", balon, p, condicion)] = valor
        avisar("probabilidades fuera de muestra calculadas")
        for p in partidos:
            for clave, valor in preparados[p]["reglas"].items():
                ps[("reglas", clave[0], p, clave[1])] = valor
        gts = {p: dfl.cargar(p)["gt"]["control"] for p in partidos}
        cal = np.array([[[sum(calidad(ps[(d, b, p, c)], preparados[p]["clase"], gts[p]) for p in partidos)
                          for c in dfl.VOTAN] for b in BALONES] for d in DETECTORES])
        os.makedirs(carpeta_cache(), exist_ok=True)
        np.savez_compressed(ruta, calidad=cal, **{"|".join(k): v for k, v in ps.items()})

    trabajos = [(p, {(d, b, c): v for (d, b, q, c), v in ps.items() if q == p}) for p in partidos]
    with concurrent.futures.ProcessPoolExecutor(args.procesos) as pool:
        resultados = {r[0]: r for r in pool.map(puntuar_partido, trabajos)}
    recuentos = {p: resultados[p][1] for p in partidos}

    print("# El detector de cambios de posesión en la DFL (regla del 16/11)\n")
    print("Código: {} · emulación del vídeo: p = {}, σ = {} m, L = {} · {} combinaciones\n".format(
        puntuar.version_del_codigo(), P_VIDEO, SIGMA_VIDEO, L_VIDEO, len(comun.CONFIGS) - 1))

    print("## Cómo de bueno es el detector por sí solo (cambios de control, umbral 0,5; descriptivo)\n")
    print("| detector | balón | condición | cambios reales | vistos | avisos por minuto vivo | avisos buenos |")
    print("|---|---|---|---|---|---|---|")
    for i, d in enumerate(DETECTORES):
        for j, b in enumerate(BALONES):
            for k, c in enumerate(dfl.VOTAN):
                reales, vistos, avisos, buenos, vivos = cal[i, j, k]
                print("| {} | {} | {} | {} | {} | {:.1f} | {} |".format(
                    d, b, c, reales, de.pct(vistos, reales), avisos / (vivos / 25.0 / 60.0), de.pct(buenos, avisos)))

    veredictos = []
    for detector in DETECTORES:
        for balon in BALONES:
            elegidas = elegir(recuentos, partidos, detector, balon)
            print("\n## Candidato: detector {} · balón «{}»\n".format(detector, balon))
            print("Combinación elegida para cada partido con los otros seis: {}.\n".format("; ".join(
                "{} en {}".format(comun.nombre(c), n) for c, n in collections.Counter(elegidas.values()).items())))
            print("| `D` | condición | etiquetas | main | candidato | diferencia [intervalo] | gana en |")
            print("|---|---|---|---|---|---|---|")
            pasa_1, pasa_3 = True, True
            for modo in comun.MODOS_D:
                for condicion in dfl.VOTAN:
                    for convencion in dfl.CONVENCIONES[::-1]:
                        cand = [recuentos[p][(detector, balon, condicion, modo, convencion, elegidas[p])]
                                for p in partidos]
                        ref = [recuentos[p][(detector, balon, condicion, modo, convencion, comun.MAIN)]
                               for p in partidos]
                        dif, intervalo, gana = comun.frente_a(cand, ref, args.bootstrap)
                        if convencion == "control":
                            pasa_1 &= dif >= UMBRAL_ENTRADA and gana >= MIN_PARTIDOS
                        else:
                            pasa_3 &= dif >= -DANO
                        print("| {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} [{:+.3f} a {:+.3f}] | {} de {} |".format(
                            "etiquetas" if modo == "oraculo" else "propio", condicion, convencion, comun.spell(ref),
                            comun.spell(cand), dif, intervalo[0], intervalo[1], gana, len(partidos)))
            veredictos.append((detector, balon, pasa_1, pasa_3))
            print("\nRegla: punto 1 (control, +{} y {} de 7 en las 4 celdas): **{}** · punto 3 (flag, no pierde más de "
                  "{}): **{}**.".format(UMBRAL_ENTRADA, MIN_PARTIDOS, "pasa" if pasa_1 else "no pasa", DANO,
                                        "pasa" if pasa_3 else "no pasa"))

            print("\nLas combinaciones, una a una (descriptivo; `D` de las etiquetas; diferencia con `main` y en "
                  "cuántos gana):\n")
            print("| combinación | " + " | ".join("{}, {}".format(v, c) for c in dfl.VOTAN
                                                   for v in dfl.CONVENCIONES[::-1]) + " |")
            print("|---|---|---|---|---|")
            for config in comun.CONFIGS[1:]:
                celdas = []
                for condicion in dfl.VOTAN:
                    for convencion in dfl.CONVENCIONES[::-1]:
                        dif, _, gana = comun.frente_a(
                            [recuentos[p][(detector, balon, condicion, "oraculo", convencion, config)]
                             for p in partidos],
                            [recuentos[p][(detector, balon, condicion, "oraculo", convencion, comun.MAIN)]
                             for p in partidos], 0)
                        celdas.append("{:+.3f} ({})".format(dif, gana))
                print("| {} | {} |".format(comun.nombre(config), " | ".join(celdas)))

            for convencion in dfl.CONVENCIONES[::-1]:
                acc = de.nuevo()
                for p in partidos:
                    de.analizar(resultados[p][3][convencion], resultados[p][2][(detector, balon, elegidas[p])], acc)
                de.imprimir("Por duración · {} · «{}», `D` de las etiquetas · candidato {} «{}»".format(
                    convencion, de.CONDICION_DFL, detector, balon), acc, de.CAUSAS_REALES[:3])

    print("\n## Veredicto con la regla (puntos 1 y 3; el 2, SkillCorner, solo se abre si pasan)\n")
    for detector, balon, pasa_1, pasa_3 in veredictos:
        print("- detector {} · balón «{}»: punto 1 {}, punto 3 {} → **{}**".format(
            detector, balon, "pasa" if pasa_1 else "no pasa", "pasa" if pasa_3 else "no pasa",
            "sigue a SkillCorner" if pasa_1 and pasa_3 else "no entra"))


if __name__ == "__main__":
    main()
