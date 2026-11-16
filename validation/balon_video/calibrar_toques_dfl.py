"""Calibración en la DFL de la condición 4 de la puerta 1b: el suelo de ruido del detector de toques.

Por qué (`validation/balon_video/BITACORA.md`, puerta 1b, condición 4): el balón del detector del vídeo puede
temblar, y con temblor el detector de toques del experimento 0 fabrica cambios de velocidad. La condición 4 pide
que los cambios de velocidad sin ningún jugador a 3 m o menos («suelo de ruido», `toques.contar`) no pasen, por
minuto, del doble de los que da la DFL con su balón limpio con el mismo código. Este script da esa cifra, y cómo
crecen toques y ruido si se añade temblor a la posición del balón.

Datos abiertos de otros partidos: los 7 de la Bundesliga (Bassek et al., 2025, CC BY 4.0), con la caché del
experimento 0 y `validation/harness/dfl.py`. Lo puede ejecutar cualquiera, Claude incluido. Solo imprime
agregados por partido y con los 7 juntos.

Qué hace, en cada partido y en cada parte por separado (nunca se juntan las dos partes):
- **Frames de juego:** los que tienen `H` o `A` en la convención «flag» del harness (la `D` es la misma en las
  dos convenciones; la `X` del hueco entre partes y de los frames sin flag no cuenta).
- **Versiones del balón:**
  - «limpio»: la condición `limpio` del harness (el balón tapado solo en los `D` y en sus bordes);
  - «limpio + σ»: lo mismo con ruido gaussiano independiente por frame y por eje, de σ = 0,03, 0,05, 0,10 y
    0,20 m. Una sola tirada de normales por partido (semilla fija) escalada por σ: los niveles van anidados;
  - «como el ATD»: la condición del harness, con microcortes, bloques y el suavizado de 25 frames.
- **Recuento:** `toques.contar(..., mascara=juego)` por parte: toques (jugador a 1,5 m o menos), ruido (nadie a
  3 m o menos) y eventos (todos; los de 1,5 a 3 m no son ni toque ni ruido).
- **Por minuto:** de frames de juego con el balón de esa versión visible. Con los 7 juntos, suma de recuentos
  entre suma de minutos (no la media de las tasas por partido).

Lo que pide la bitácora: el suelo de ruido por minuto con el balón limpio (los 7 juntos) y su doble, que es el
umbral de la condición 4. Desde la corrección de la puerta 1b (16/11, 15:50) la condición 4 es descriptiva: esa cifra
ya no es un umbral que decida, y no se debe usar como tal (con los jugadores incompletos del ATD y muestras de 10
minutos, un balón perfecto la pasa a menudo).

**Desglose del ruido por distancia al `D` más cercano** (solo descriptivo; no cambia ninguna cifra de las tablas):
el harness tapa el balón en los `D` y en sus `BORDE` frames antes de la media móvil de «como el ATD», así que la
media deja de usar un solo lado a `BORDE` + media ventana + 1 frames de un `D` (`ARTEFACTO` = 18) y el balón da ahí
un quiebro artificial. Para «limpio» y «como el ATD», los eventos de ruido justo a esa distancia, a esa distancia o
menos, y el ruido por minuto lejos de los `D` (a `LEJOS_D` frames o más, por minuto de frames de juego con balón a
esa distancia). La distancia se mide dentro de cada parte.

Ojo al leer los σ altos: cerca de la saturación el detector dispara en casi cualquier sitio, y el reparto entre
toques y ruido solo dice con qué frecuencia hay un jugador a 1,5 m o nadie a 3 m del balón; no es una propiedad
del detector.

Uso, desde la raíz del repo (necesita la caché de la DFL: pasos 1 y 2 de `validation/PASOS.md`):

    python validation/balon_video/calibrar_toques_dfl.py

Con `--partidos J03WMX` mide uno solo, para probar. Si falla, imprime solo el tipo de error y las líneas del
código.
"""

import argparse
import os
import sys
import time
import traceback

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "harness"))
sys.path.insert(0, AQUI)
import dfl  # noqa: E402
import toques  # noqa: E402

SEMILLA = 20261116
SIGMAS = (0.03, 0.05, 0.10, 0.20)  # m: temblor por frame y por eje
VERSIONES = ("limpio",) + tuple("limpio + {:.2f} m".format(s) for s in SIGMAS) + ("como el ATD",)
CAMPOS = ("frames", "toques", "ruido", "eventos")
ARTEFACTO = dfl.BORDE + 25 // 2 + 1  # 18: primer frame en que la media móvil de 25 del harness usa los dos lados
LEJOS_D = 50  # frames: «lejos de los D»
DESGLOSE = ("ruido_a_{}".format(ARTEFACTO), "ruido_a_{}_o_menos".format(ARTEFACTO), "ruido_lejos",
            "frames_lejos")


def juego_de(cargado):
    """Frames de juego: `H` o `A` en la convención «flag» (la `D` es la misma en las dos)."""
    gt = cargado["gt"]["flag"]
    return (gt == dfl.H) | (gt == dfl.A)


def con_ruido(trk, unidad_x, unidad_y, sigma):
    """El `Tracking` con el balón movido `sigma` veces las normales dadas; donde no hay balón sigue sin haberlo."""
    return trk._replace(bx=trk.bx + sigma * unidad_x, by=trk.by + sigma * unidad_y)


def distancia_a_d(es_d):
    """Frames hasta el `D` más cercano en cada frame de un tramo (inf si en el tramo no hay ningún `D`)."""
    posiciones = np.flatnonzero(es_d)
    n = len(es_d)
    if not len(posiciones):
        return np.full(n, np.inf)
    t = np.arange(n)
    j = np.searchsorted(posiciones, t)
    antes = np.where(j > 0, t - posiciones[np.maximum(j - 1, 0)], np.inf)
    despues = np.where(j < len(posiciones), posiciones[np.minimum(j, len(posiciones) - 1)] - t, np.inf)
    return np.minimum(antes, despues)


def contar_tracking(trk, juego, es_d):
    """{campo: suma de las partes} de los recuentos de `toques.contar` parte a parte (los mismos, con
    `toques.eventos`), los frames de juego con balón visible y el desglose por distancia al `D` más cercano."""
    total = dict.fromkeys(CAMPOS + DESGLOSE, 0)
    for a, b in trk.blocks:
        bx, by, m = trk.bx[a:b], trk.by[a:b], juego[a:b]
        frames, d1 = toques.eventos(bx, by, trk.px[a:b], trk.py[a:b], trk.team, trk.fps, mascara=m)
        visible = m & np.isfinite(bx) & np.isfinite(by)
        total["frames"] += int(np.sum(visible))
        total["toques"] += int(np.sum(d1 <= toques.RADIO))
        total["ruido"] += int(np.sum(d1 > toques.RADIO_RUIDO))
        total["eventos"] += int(len(d1))
        dist = distancia_a_d(es_d[a:b])
        ruido = d1 > toques.RADIO_RUIDO
        dr = dist[frames[ruido]] if len(frames) else np.zeros(0)
        total[DESGLOSE[0]] += int(np.sum(dr == ARTEFACTO))
        total[DESGLOSE[1]] += int(np.sum(dr <= ARTEFACTO))
        total["ruido_lejos"] += int(np.sum(dr >= LEJOS_D))
        total["frames_lejos"] += int(np.sum(visible & (dist >= LEJOS_D)))
    return total


def medir_partido(partido):
    """{versión: recuentos} de un partido."""
    cargado = dfl.cargar(partido)
    juego = juego_de(cargado)
    es_d = cargado["gt"]["flag"] == dfl.D
    limpio = dfl.tracking_de(cargado, "limpio")
    rng = np.random.default_rng([SEMILLA, cargado["indice"], 7])
    unidad_x, unidad_y = rng.standard_normal(len(limpio.bx)), rng.standard_normal(len(limpio.by))
    salida = {"limpio": contar_tracking(limpio, juego, es_d)}
    for sigma, version in zip(SIGMAS, VERSIONES[1:-1]):
        salida[version] = contar_tracking(con_ruido(limpio, unidad_x, unidad_y, sigma), juego, es_d)
    salida["como el ATD"] = contar_tracking(dfl.tracking_de(cargado, "como el ATD"), juego, es_d)
    return salida


def tasas(c, fps=dfl.FPS):
    """(minutos, toques/min, ruido/min, eventos/min, ruido/toques) de unos recuentos."""
    minutos = c["frames"] / float(fps) / 60.0
    return (minutos, toques.por_minuto(c["toques"], c["frames"], fps), toques.por_minuto(c["ruido"], c["frames"], fps),
            toques.por_minuto(c["eventos"], c["frames"], fps),
            round(c["ruido"] / c["toques"], 3) if c["toques"] else None)


def fila(nombre, c):
    m, t, r, e, rt = tasas(c)
    return "| {} | {:.1f} | {} | {} | {} | {} | {} | {} |".format(nombre, m, c["toques"], c["ruido"], t, r, e, rt)


CABECERA = ("| {} | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |\n"
            "|---|---|---|---|---|---|---|---|")


def informe_de_error(error):
    pila = traceback.extract_tb(error.__traceback__)
    lineas = ["{}:{} ({})".format(os.path.basename(f.filename), f.lineno, f.name) for f in pila]
    return "ERROR {} en {}".format(type(error).__name__, " <- ".join(reversed(lineas)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), help="partidos de la DFL (por defecto, los 7)")
    args = ap.parse_args(argv)
    inicio = time.time()
    por_partido = {}
    try:
        for partido in args.partidos:
            por_partido[partido] = medir_partido(partido)
    except Exception as error:  # noqa: BLE001
        print(informe_de_error(error))
        return 1
    juntos = {v: {c: sum(por_partido[p][v][c] for p in por_partido) for c in CAMPOS + DESGLOSE} for v in VERSIONES}

    print("# Toques y suelo de ruido del detector de toques en la DFL ({} partidos)".format(len(por_partido)))
    print()
    print("Detector: `validation/balon_video/toques.py` (umbral {} m/s, toque con jugador a {} m o menos, ruido sin "
          "nadie a {} m o menos, tramos de {} frames o más), parte a parte.".format(
              toques.UMBRAL, toques.RADIO, toques.RADIO_RUIDO, toques.MINIMO))
    print("Por minuto de frames de juego (`H` o `A` en el flag) con el balón de esa versión visible.")
    print()
    print("## Los {} juntos".format(len(por_partido)))
    print()
    print(CABECERA.format("versión del balón"))
    for v in VERSIONES:
        print(fila(v, juntos[v]))
    print()
    suelo = tasas(juntos["limpio"])[2]
    suelos = [tasas(por_partido[p]["limpio"])[2] for p in por_partido]
    print("**Suelo de ruido con el balón limpio ({} juntos): {} por minuto** (por partido, de {} a {}).".format(
        len(por_partido), suelo, min(suelos), max(suelos)))
    print("El doble, {} por minuto, era el umbral de la condición 4 antes de la corrección de la puerta 1b; desde "
          "entonces la condición 4 es descriptiva y esta cifra no decide nada.".format(round(2 * suelo, 2)))
    print()
    print("## Ruido por distancia al D más cercano (los {} juntos; descriptivo)".format(len(por_partido)))
    print()
    print("| versión del balón | ruido | ruido a {a} frames de un D | ruido a {a} o menos | ruido/min sin los de {a} o "
          "menos | ruido/min a {l} frames o más de un D (min) |".format(a=ARTEFACTO, l=LEJOS_D))
    print("|---|---|---|---|---|---|")
    for v in ("limpio", "como el ATD"):
        c = juntos[v]
        print("| {} | {} | {} | {} | {} | {} ({:.1f}) |".format(
            v, c["ruido"], c[DESGLOSE[0]], c[DESGLOSE[1]],
            toques.por_minuto(c["ruido"] - c[DESGLOSE[1]], c["frames"], dfl.FPS),
            toques.por_minuto(c["ruido_lejos"], c["frames_lejos"], dfl.FPS), c["frames_lejos"] / dfl.FPS / 60.0))
    print()
    print("## Por partido")
    for p in por_partido:
        print()
        print(CABECERA.format(p))
        for v in VERSIONES:
            print(fila(v, por_partido[p][v]))
    print()
    print("Tiempo: {:.0f} s.".format(time.time() - inicio))
    return 0


if __name__ == "__main__":
    sys.exit(main())
