"""Mide un detector de cambios de posesión en SkillCorner frente a `main` (docs/decisiones.md, 16/11).

    python validation/cambios/medir_skillcorner.py --detector ninguno       # comprueba el instrumento
    python validation/cambios/medir_skillcorner.py --detector reglas --giro 45 --velocidad 0.6 --confirma 30 \\
        --w 0 --gamma 8 --ventana 50 --contra-d --balon sin-suavizar
    python validation/cambios/medir_skillcorner.py --detector aprendido [--umbral-avisos 0.5] \\
        --w 0 --gamma 4 --ventana 100 --contra-d --balon respaldo

Datos abiertos de otros partidos: SkillCorner (A-League 2024/25, licencia MIT; `validation/skillcorner/`) y, para
entrenar el detector aprendido, los 7 partidos de la DFL (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados. El detector aprendido usa scikit-learn, que no entra en
`requirements-entrega.txt`.

**Solo `lector.ENTRENAMIENTO`.** `lector.EXAMEN` no se lee en ningún camino por defecto: hace falta `--examen` y,
además, `--examen-con-permiso`, que se pone solo con la autorización explícita del equipo en el momento. Se abre una
vez por candidato y cada uso se apunta en `validation/skillcorner/BITACORA.md` («Usos del examen») y en
`docs/decisiones.md`.

**Aquí no se elige nada.** El detector, sus umbrales y la combinación (w, γ, W, contra el otro equipo) se eligen en
la DFL (`medir.py`, `ronda2.py`) y llegan por argumentos.

Qué compara, en las dos condiciones que votan de SkillCorner («detectado» y «detectado, suavizado», pasadas de 10 a
25 fps con `lector.tracking_de`, como `validation/skillcorner/medir.py`) y con el `D` de las etiquetas
(`puntuar.d_oraculo`) y el propio:

- **`main`:** la de `validation/resultados/2026-11-15_skillcorner.md` y la de las rondas de la DFL: B5 con los
  coeficientes de la entrega (nunca vio estos partidos), `dead_state` y el Viterbi de `temporal.decode` con coste
  25. No lleva «cortas a `D`»: así la comparan también las rondas de la DFL, y con el `D` de las etiquetas daría lo
  mismo.
- **El candidato:** la misma evidencia más `cambios.capa(p, γ, W, contra_d)`, decodificada con
  `temporal.decode_cambios` y la rebaja `cambios.rebaja(p, w)` (`ronda2.decodificar`).

Los detectores (`p`, de forma (n, 2)):

- **reglas:** `cambios.p_reglas` con `--giro`, `--velocidad` y `--confirma`, que son obligatorios: los elegidos en la
  DFL, no los de `cambios.py`;
- **aprendido:** un `HistGradientBoostingClassifier` con `medir.PARAMETROS` y un solo hilo, entrenado con los 7
  partidos de la DFL: etiquetas de control, balón «respaldo» (el de la condición «como el ATD») y uno de cada 5
  frames «sin cambio», como `medir.py`. Con `--umbral-avisos`, los avisos de la familia A de la segunda ronda
  (`ronda2.corregir` y `ronda2.avisos`); sin él, la probabilidad tal cual;
- **ninguno:** `p` a cero. Es la comprobación del instrumento: el candidato tiene que salir igual que `main` en
  todos los frames, y `main` tiene que repetir la medida del 15/11 en estos partidos.

Qué balón ve el detector (`--balon`); B5 y el `D` siguen con el de la condición:

- **respaldo:** el de la condición, como el «respaldo» de la DFL;
- **sin-suavizar:** el balón detectado de SkillCorner sin la media móvil de 25 frames, en las dos condiciones (en
  «detectado» es el mismo que el de respaldo). Es lo más parecido que hay aquí al «vídeo» de la DFL, un balón
  sacado del vídeo sin el suavizado de 1 s del ATD, pero no es una emulación del detector del vídeo.
"""

import argparse
import concurrent.futures
import multiprocessing
import os
import subprocess
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
SKILLCORNER = os.path.join(ROOT, "validation", "skillcorner")
sys.path.insert(0, AQUI)
import comun  # noqa: E402
import medir  # noqa: E402  (el de validation/cambios/, no el de validation/skillcorner/)
import ronda2  # noqa: E402
from comun import cambios, dfl, pipeline, puntuar, temporal  # noqa: E402

sys.path.append(SKILLCORNER)  # al final: hay otro `medir.py` en esa carpeta
import lector as lc  # noqa: E402

if os.path.dirname(os.path.abspath(lc.__file__)) != SKILLCORNER:
    raise ImportError("se ha cargado otro `lector`: {}".format(lc.__file__))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DETECTORES = ("ninguno", "reglas", "aprendido")
BALONES = ("respaldo", "sin-suavizar")
SIN_SUAVIZAR = "detectado"  # la condición de `lector` cuyo balón es el detectado, sin media móvil
UMBRAL = 0.005  # +0,005 o más con los 10 juntos: el punto 2 del límite de daño (docs/decisiones.md, 16/11)
GANA_DE = 7  # ganando en 7 de 10 partidos
PARTIDOS_DE_LA_REGLA = 10
NOMBRE_D = {"oraculo": "de las etiquetas", "propio": "propio"}


# -- el detector ----------------------------------------------------------------------------------------

def entrenar_aprendido(avisar):
    """(modelo, filas, filas de cambio): el detector aprendido con los 7 partidos de la DFL, como un pliegue de
    `medir.py` sin dejar ninguno fuera (etiquetas de control, balón «respaldo», `medir.PARAMETROS`, un hilo)."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from threadpoolctl import threadpool_limits
    xs, ys = [], []
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        clase = comun.clases(cargado["gt"]["control"])
        trk = dfl.tracking_de(cargado, medir.CONDICION_ENTRENAMIENTO)
        x, girado, _ = medir.rasgos_dobles(trk, None)
        x, y = medir.filas_de_entrenamiento(clase, x, girado)
        xs.append(x)
        ys.append(y)
        avisar("rasgos de {} calculados".format(partido))
    x, y = np.vstack(xs), np.concatenate(ys)
    with threadpool_limits(limits=1):
        modelo = HistGradientBoostingClassifier(**medir.PARAMETROS).fit(x, y)
    avisar("detector aprendido entrenado: {} filas, {} de cambio".format(len(y), int(np.sum(y > 0))))
    return modelo, len(y), int(np.sum(y > 0))


def p_del_detector(detector, trk):
    """`p` (n, 2) del detector sobre `trk`. `detector`: ("ninguno",), ("reglas", giro, velocidad, confirma) o
    ("aprendido", modelo, umbral de los avisos o None)."""
    n = len(trk.bx)
    if detector[0] == "ninguno":
        return np.zeros((n, 2))
    if detector[0] == "reglas":
        _, giro, velocidad, confirma = detector
        return cambios.p_reglas(trk, giro, velocidad, confirma)
    from threadpoolctl import threadpool_limits
    _, modelo, umbral = detector
    x, girado, _ = medir.rasgos_dobles(trk, None)  # sin `fuente`: se entrenó con el balón «respaldo»
    dentro = np.zeros(n, dtype=bool)
    for a, b in trk.blocks:
        dentro[a:b] = True
    with threadpool_limits(limits=1):
        p = medir.predecir(modelo, x, girado, dentro)
    if umbral is not None:
        p = ronda2.p_de_avisos(n, ronda2.avisos(ronda2.corregir(p), umbral))
    return p


# -- un partido -------------------------------------------------------------------------------------------

def base_de(trk, gt, modo_d):
    """La evidencia combinada de `main`, como `pipeline.run` justo antes de decodificar: las piezas de
    `pipeline.PIECES` (B5 con los coeficientes de la entrega) y, con el `D` de las etiquetas, `puntuar.d_oraculo`."""
    limpio = pipeline.default_piece("ball")(trk)
    piezas = [pipeline.default_piece("candidates")(limpio), pipeline.default_piece("dead_state")(limpio)]
    if modo_d == "oraculo":
        piezas.append(puntuar.d_oraculo(gt))
    score, allowed, conflicto = pipeline.combine(piezas, len(limpio.bx))
    if any(conflicto[a:b].any() for a, b in limpio.blocks):
        raise ValueError("las piezas se contradicen")
    return comun.Base(score, allowed, limpio.blocks)


def mismos_jugadores(a, b):
    return (np.array_equal(a.px, b.px, equal_nan=True) and np.array_equal(a.py, b.py, equal_nan=True)
            and np.array_equal(a.team, b.team) and tuple(a.blocks) == tuple(b.blocks))


def puntuar_partido(trabajo):
    """(id, recuentos {(modo, condición, "main" o "candidato"): recuento}, calidad {condición: recuentos del
    detector}, iguales {(modo, condición): si el candidato sale igual que `main` en todos los frames})."""
    id_, detector, config, balon = trabajo
    t0 = time.time()
    crudo = lc.leer_crudo(id_)
    trks = {c: lc.tracking_de(crudo, c, id_) for c in lc.VOTAN}
    sin_suavizar = puntuar.solo_lectura(trks[SIN_SUAVIZAR][0])
    recuentos, calidad, iguales = {}, {}, {}
    for condicion in lc.VOTAN:
        trk, gt = trks[condicion]
        trk = puntuar.solo_lectura(trk)
        visto = trk
        if balon == "sin-suavizar":
            if not mismos_jugadores(sin_suavizar, trk):
                raise ValueError("las condiciones no tienen los mismos jugadores")
            visto = sin_suavizar
        p = p_del_detector(detector, visto)
        calidad[condicion] = medir.calidad(p, comun.clases(gt), gt)
        for modo in comun.MODOS_D:
            base = base_de(trk, gt, modo)
            ref = temporal.decode(base.score, base.allowed, base.blocks)
            pred = ronda2.decodificar(base, p, config)
            recuentos[(modo, condicion, "main")] = puntuar.contar(gt, ref)
            recuentos[(modo, condicion, "candidato")] = puntuar.contar(gt, pred)
            iguales[(modo, condicion)] = bool(np.array_equal(ref, pred))
    print("# partido {} en {:.0f} s".format(id_, time.time() - t0), file=sys.stderr, flush=True)
    return id_, recuentos, calidad, iguales


# -- lo que se imprime ------------------------------------------------------------------------------------

def version_del_codigo():
    """El commit y si hay cambios sin commit en el código que interviene."""
    rutas = ["possession", "validation/harness", "validation/skillcorner", "validation/cambios/*.py"]
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                                text=True, check=True).stdout.strip()
        sucio = subprocess.run(["git", "status", "--porcelain", "--"] + rutas, cwd=ROOT, capture_output=True,
                               text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconocido (sin git)"
    return commit + (", con cambios sin commit en el código que interviene" if sucio else "")


def describir(detector, filas):
    if detector[0] == "ninguno":
        return "ninguno (`p` a cero: comprobación del instrumento)"
    if detector[0] == "reglas":
        return "reglas: giro de {:g}°, cambio de velocidad de {:g}, confirmación de {} frames".format(*detector[1:])
    texto = ("aprendido, entrenado con los 7 partidos de la DFL ({} filas, {} de cambio; etiquetas de control, balón "
             "«respaldo», `medir.PARAMETROS`)".format(*filas))
    umbral = detector[2]
    return texto + ("; avisos con u = {:g}".format(umbral) if umbral is not None else "; la probabilidad tal cual")


def nombre_combinacion(config):
    w, gamma, ventana, contra_d = config
    return "w {:g} · γ {:g} · W {}{}".format(w, gamma, ventana, " · contra el otro equipo" if contra_d else "")


def pct(a, b):
    return "{:.0f} %".format(100.0 * a / b) if b else "–"


def imprimir(args, ids, mitad, detector, filas, config, resultados):
    recuentos = {id_: r for id_, r, _, _ in resultados}
    calidad = {id_: c for id_, _, c, _ in resultados}
    iguales = {id_: g for id_, _, _, g in resultados}

    print("# El detector de cambios de posesión en SkillCorner frente a `main`\n")
    print("- código: {} · SkillCorner, mitad de {} ({} partidos) · bootstrap: {}".format(
        version_del_codigo(), mitad, len(ids), args.bootstrap))
    print("- detector: {}".format(describir(detector, filas)))
    if detector[0] != "ninguno":
        print("- balón del detector: «{}» (B5 y el `D` van con el de la condición)".format(args.balon))
    print("- combinación: {}".format(nombre_combinacion(config)))
    print("- `main`: B5, `dead_state` y `temporal.decode` (coste 25), sin «cortas a `D`»")

    if detector[0] != "ninguno":
        print("\n## El detector por sí solo (descriptivo; cambios directos de las etiquetas de SkillCorner, umbral 0,5)\n")
        print("| condición | cambios reales | vistos | avisos por minuto vivo | avisos buenos |")
        print("|---|---|---|---|---|")
        for condicion in lc.VOTAN:
            reales, vistos, avisos, buenos, vivos = sum(calidad[i][condicion] for i in ids)
            print("| {} | {} | {} | {:.1f} | {} |".format(condicion, reales, pct(vistos, reales),
                                                        avisos / (vivos / float(lc.FPS) / 60.0), pct(buenos, avisos)))

    print("\n## `spellF1` frente a `main`\n")
    print("| `D` | condición | `main` | candidato | diferencia [5–95 %] | gana en | posesiones predichas "
          "(`main` / candidato) / reales |")
    print("|---|---|---|---|---|---|---|")
    celdas = []
    for modo in comun.MODOS_D:
        for condicion in lc.VOTAN:
            ref = [recuentos[i][(modo, condicion, "main")] for i in ids]
            cand = [recuentos[i][(modo, condicion, "candidato")] for i in ids]
            dif, intervalo, gana = comun.frente_a(cand, ref, args.bootstrap)
            celdas.append((modo, condicion, dif, gana))
            texto = "{:+.3f}".format(dif) + (" [{:+.3f} a {:+.3f}]".format(*intervalo) if intervalo else "")
            print("| {} | {} | {:.3f} | {:.3f} | {} | {} de {} | {} / {} / {} |".format(
                NOMBRE_D[modo], condicion, comun.spell(ref), comun.spell(cand), texto, gana, len(ids),
                sum(r["n_pred"] for r in ref), sum(r["n_pred"] for r in cand), sum(r["n_gt"] for r in ref)))

    if detector[0] == "ninguno":
        print("\n## Comprobación del instrumento\n")
        total = sum(len(g) for g in iguales.values())
        print("- El candidato sin detector sale igual que `main` en todos los frames en {} de {} salidas "
              "(partido × condición × `D`).".format(sum(sum(g.values()) for g in iguales.values()), total))
        print("- `main` partido a partido, para compararlo con `validation/skillcorner/medir.py` del 15/11 en estos "
              "partidos:\n")
        print("| `D` | condición | `main` | por partido, mín–máx | posesiones predichas / reales |")
        print("|---|---|---|---|---|")
        for modo in comun.MODOS_D:
            for condicion in lc.VOTAN:
                ref = [recuentos[i][(modo, condicion, "main")] for i in ids]
                f1s = [comun.spell([r]) for r in ref]
                print("| {} | {} | {:.3f} | {:.3f}–{:.3f} | {} / {} |".format(
                    NOMBRE_D[modo], condicion, comun.spell(ref), min(f1s), max(f1s),
                    sum(r["n_pred"] for r in ref), sum(r["n_gt"] for r in ref)))
        return

    print("\n## Regla (docs/decisiones.md, 16/11, escrita antes de medir)\n")
    if len(ids) != PARTIDOS_DE_LA_REGLA:
        print("Con {} partidos la regla no se aplica: pide los {} de la mitad.".format(len(ids), PARTIDOS_DE_LA_REGLA))
        return
    for modo, condicion, dif, gana in celdas:
        print("- `D` {}, {}: {:+.3f} y {} de {} → {}".format(
            NOMBRE_D[modo], condicion, dif, gana, len(ids),
            "cumple" if dif >= UMBRAL and gana >= GANA_DE else "no cumple"))
    pasa = all(dif >= UMBRAL and gana >= GANA_DE for _, _, dif, gana in celdas)
    print("\n+{} o más con los {} juntos y ganando en {} de {}, en las cuatro celdas: **{}**".format(
        UMBRAL, len(ids), GANA_DE, len(ids), "pasa" if pasa else "no pasa"))


# -- argumentos -------------------------------------------------------------------------------------------

def leer_argumentos():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--detector", choices=DETECTORES, required=True,
                        help="«ninguno» comprueba el instrumento (el candidato tiene que salir igual que `main`)")
    parser.add_argument("--giro", type=float, help="reglas: grados de giro del balón para un toque")
    parser.add_argument("--velocidad", type=float, help="reglas: cambio relativo de la velocidad para un toque")
    parser.add_argument("--confirma", type=int, help="reglas: frames en que el equipo nuevo sigue siendo el más cercano")
    parser.add_argument("--umbral-avisos", type=float, dest="umbral_avisos",
                        help="aprendido: los avisos de la familia A con este umbral (sin él, la probabilidad tal cual)")
    parser.add_argument("--w", type=float, help="rebaja del coste de cambiar de equipo")
    parser.add_argument("--gamma", type=float, help="peso de la capa")
    parser.add_argument("--ventana", type=int, help="W: frames que empuja la capa")
    parser.add_argument("--contra-d", action="store_true", dest="contra_d",
                        help="la capa suma lo mismo a `D`: solo empuja contra el otro equipo")
    parser.add_argument("--balon", choices=BALONES, help="qué balón ve el detector")
    parser.add_argument("--partidos", nargs="+", type=int,
                        help="para probar: algunos de lector.ENTRENAMIENTO (la regla pide los 10)")
    parser.add_argument("--procesos", type=int, default=4)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--examen", action="store_true",
                        help="abre lector.EXAMEN; da error salvo con --examen-con-permiso")
    parser.add_argument("--examen-con-permiso", action="store_true", dest="examen_con_permiso",
                        help="con --examen: hay autorización explícita del equipo y es el primer uso de este candidato")
    args = parser.parse_args()

    if args.examen_con_permiso and not args.examen:
        parser.error("--examen-con-permiso solo va con --examen")
    reglas = (args.giro, args.velocidad, args.confirma)
    if args.detector == "reglas" and None in reglas:
        parser.error("las reglas necesitan --giro, --velocidad y --confirma: los elegidos en la DFL")
    if args.detector != "reglas" and any(v is not None for v in reglas):
        parser.error("--giro, --velocidad y --confirma son solo para las reglas")
    if args.detector != "aprendido" and args.umbral_avisos is not None:
        parser.error("--umbral-avisos es solo para el detector aprendido")
    if args.detector == "ninguno":
        args.w = 0.0 if args.w is None else args.w
        args.gamma = 0.0 if args.gamma is None else args.gamma
        args.ventana = 0 if args.ventana is None else args.ventana
    elif None in (args.w, args.gamma, args.ventana, args.balon):
        parser.error("con un detector hacen falta --w, --gamma, --ventana y --balon: los elegidos en la DFL")
    if args.w < 0 or args.gamma < 0 or args.ventana < 0:
        parser.error("--w, --gamma y --ventana no pueden ser negativos")
    if args.examen:
        if args.detector == "ninguno":
            parser.error("el examen no se abre para comprobar el instrumento")
        if args.partidos:
            parser.error("con --examen van los 10 partidos del examen, sin --partidos")
    return args


def partidos_que_faltan(ids):
    raiz = lc.carpeta()
    cache = raiz.parent / "skillcorner_cache"
    return [i for i in ids if not (cache / "{}.npz".format(i)).is_file()
            and not (raiz / str(i) / "{}_tracking_extrapolated.jsonl".format(i)).is_file()]


def main():
    args = leer_argumentos()

    if args.examen and not args.examen_con_permiso:
        print("El examen de SkillCorner (lector.EXAMEN) no se abre por defecto. CLAUDE.md lo permite una vez POR")
        print("CANDIDATO, con la autorización explícita del equipo en el momento. Mira antes la sección «Usos del")
        print("examen» de validation/skillcorner/BITACORA.md: si este candidato ya lo gastó, no se vuelve a abrir.")
        print("Si tienes la autorización y es su primer uso, repite el comando añadiendo --examen-con-permiso.")
        return 1
    if args.examen:
        mitad, ids = "examen", list(lc.EXAMEN)
        print("### ATENCIÓN: se está abriendo la mitad de EXAMEN de SkillCorner (lector.EXAMEN).")
        print("Gasta el único uso de ESTE candidato. Apúntalo en validation/skillcorner/BITACORA.md («Usos del")
        print("examen») y en docs/decisiones.md, con la fecha, el candidato y quién lo autorizó.\n")
    else:
        mitad, ids = "entrenamiento", list(dict.fromkeys(args.partidos or lc.ENTRENAMIENTO))
        lc.exigir_solo_entrenamiento(ids)
        ajenos = sorted(set(ids) - set(lc.ENTRENAMIENTO))
        if ajenos:
            print("Estos partidos no son de lector.ENTRENAMIENTO: {}".format(ajenos))
            return 1

    faltan = partidos_que_faltan(ids)
    if faltan:
        print("Faltan {} partidos de SkillCorner. Bájalos antes de medir (unos 1,8 GB):".format(len(faltan)))
        print("    python validation/skillcorner/descargar.py")
        print("Si los tienes en otra carpeta, apunta MTAH_OPEN_DATA_DIR a ella.")
        return 1

    def avisar(texto):
        print("# " + texto, file=sys.stderr, flush=True)

    filas = None
    if args.detector == "ninguno":
        detector = ("ninguno",)
    elif args.detector == "reglas":
        detector = ("reglas", args.giro, args.velocidad, args.confirma)
    else:
        modelo, n_filas, n_cambio = entrenar_aprendido(avisar)
        detector, filas = ("aprendido", modelo, args.umbral_avisos), (n_filas, n_cambio)
    config = (args.w, args.gamma, args.ventana, args.contra_d)

    trabajos = [(id_, detector, config, args.balon) for id_ in ids]
    # «spawn» también en Linux: el modelo ya se entrenó en este proceso, y un `fork` después de OpenMP puede colgarse.
    contexto = multiprocessing.get_context("spawn")
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos), mp_context=contexto) as pool:
        resultados = list(pool.map(puntuar_partido, trabajos))
    imprimir(args, ids, mitad, detector, filas, config, resultados)
    return 0


if __name__ == "__main__":
    sys.exit(main())
