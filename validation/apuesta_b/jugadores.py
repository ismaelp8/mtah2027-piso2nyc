"""Apuesta B con los jugadores degradados como los del ATD: medida de sensibilidad.

    python validation/apuesta_b/jugadores.py --calibrar   # calibra cada variante (no puntúa nada)
    python validation/apuesta_b/jugadores.py --perfil     # perfil de los jugadores de cada variante frente al ATD
    python validation/apuesta_b/jugadores.py              # puntúa apuesta_b.json con cada variante

Lo que se fijó antes de medir está en docs/decisiones.md (14/11, «apuesta B con los jugadores como el
ATD»). El harness no degrada a los jugadores, y la ventaja de B2 sobre B1 sale de ellos. Esto no cambia las
condiciones del harness: sustituye `dfl.tracking_de` solo dentro de este proceso.

- **El balón es idéntico al del harness.** Se degrada a partir de la parte limpia con su mismo generador;
  a los jugadores se les degrada aparte, con otro generador, y se juntan después.
- **Jugadores, antes de barajar los slots:**
  - suavizado con una media móvil de `SUAVIZADO` frames;
  - ausencias en una de las tres `VARIANTES`, con el parámetro de `CALIBRADO`, que sale de `--calibrar`
    (la media de localizados por equipo en los frames de juego, 10,25).
- **Qué variantes votan** lo decide `--perfil`, con `perfil._jugadores`, el mismo código que midió el ATD.

Son datos abiertos de la DFL: lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. Sin
azar fuera de los generadores con semilla.
"""

import argparse
import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, os.path.join(ROOT, "validation", "perfil_atd"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import perfil  # noqa: E402
import puntuar  # noqa: E402

VERSIONES = os.path.join(ROOT, "validation", "harness", "versiones", "apuesta_b.json")
SEMILLA = 20261115  # el generador de los jugadores, aparte del del balón
VARIANTES = ("al azar", "en las aglomeraciones", "lejos de la jugada")

# El ATD (validation/resultados/2026-11-14_perfil_atd.md, agregado 7) [medido].
ATD = {"media": 10.25, "p10": 9.0, "p50": 11.0, "p90": 11.0, "tramo_p50_s": 35.52, "temblor_cm": 0.136,
       "saltos_por_minuto": 0.689}
OBJETIVO_EN_JUEGO = 10.25  # localizados por equipo en los frames de juego, ±TOLERANCIA_CALIBRADO
TOLERANCIA_CALIBRADO = 0.1
SUAVIZADOS = (1, 5, 9, 13, 25)
# «al azar»: rachas presentes de media tal que la mediana de un tramo sea la del ATD (geométrica: mediana
# ≈ media·ln 2).
MEDIA_PRESENTE = ATD["tramo_p50_s"] * dfl.FPS / np.log(2.0)
# «en las aglomeraciones»
AGLOMERACION_M = 1.5
CERCA_DEL_BALON_M = 15.0
MEDIA_AUSENCIA_AGLOMERACION = 25  # frames (1 s); ver AUSENCIAS_AGLOMERACION
AUSENCIAS_AGLOMERACION = (50, 75, 100)  # el ajuste del 14/11 (docs/decisiones.md): 2, 3 o 4 s
BLOQUE = 10000  # frames por bloque al calcular distancias entre jugadores

# Lo que sale de --calibrar (con commit antes de puntuar). Temblor: 1,000 / 0,200 / 0,157 / 0,154 / 0,089 cm
# con 1 / 5 / 9 / 13 / 25 frames. Localizados por equipo en juego: 10,92 sin ausencias; con estos
# parámetros, 10,269 / 10,244 / 10,256, con el 55,9 / 57,0 / 33,1 % de las ausencias en juego.
SUAVIZADO = 13
CALIBRADO = {
    "al azar": 78.12,  # frames de media de cada ausencia
    "en las aglomeraciones": 0.1875,  # probabilidad por frame en una aglomeración
    "lejos de la jugada": 44.38,  # m a lo largo del campo
}


# -- degradación ---------------------------------------------------------------------------------------

def suavizar(x, ancho):
    """Media móvil centrada de cada columna, sin rellenar los frames en que el jugador no está."""
    if ancho <= 1:
        return x
    salida = np.column_stack([dfl.media_movil(x[:, j], ancho) for j in range(x.shape[1])]) if x.shape[1] else x
    return np.where(np.isfinite(x), salida, np.nan)


def ausencias_al_azar(presente, media_ausente, rng):
    """Rachas presentes y ausentes alternas, geométricas, por columna. Solo donde el jugador está."""
    n, columnas = presente.shape
    fuera = np.zeros((n, columnas), bool)
    if media_ausente <= 0:
        return fuera
    p_ausente = media_ausente / (media_ausente + MEDIA_PRESENTE)
    for j in range(columnas):
        t = 0
        ausente = bool(rng.random() < p_ausente)
        while t < n:
            largo = int(rng.geometric(1.0 / (media_ausente if ausente else MEDIA_PRESENTE)))
            if ausente:
                fuera[t:t + largo, j] = True
            t += largo
            ausente = not ausente
    return fuera & presente


def _marcar(inicios, largos, n):
    cambio = np.zeros(n + 1, np.int64)
    np.add.at(cambio, inicios, 1)
    np.add.at(cambio, np.minimum(inicios + largos, n), -1)
    return np.cumsum(cambio[:n]) > 0


_CANDIDATOS = {}


def en_aglomeracion(parte, clave=None):
    """{equipo: máscara (n, columnas)}: el jugador está a AGLOMERACION_M o menos de otro (de cualquier
    equipo) y a CERCA_DEL_BALON_M o menos del balón, con las posiciones limpias. Se guarda por `clave`."""
    if clave is not None and clave in _CANDIDATOS:
        return _CANDIDATOS[clave]
    bx, by = np.asarray(parte["x"], float), np.asarray(parte["y"], float)
    xs = [np.asarray(parte["equipos"][e]["x"], float) for e in ("local", "visitante")]
    ys = [np.asarray(parte["equipos"][e]["y"], float) for e in ("local", "visitante")]
    x, y = np.hstack(xs), np.hstack(ys)
    n, columnas = x.shape
    candidato = np.zeros((n, columnas), bool)
    with np.errstate(invalid="ignore"):
        for inicio in range(0, n, BLOQUE):
            tramo = slice(inicio, inicio + BLOQUE)
            d2 = (x[tramo, :, None] - x[tramo, None, :]) ** 2 + (y[tramo, :, None] - y[tramo, None, :]) ** 2
            d2 = np.where(np.isnan(d2), np.inf, d2)
            d2[:, np.arange(columnas), np.arange(columnas)] = np.inf
            cerca_de_otro = d2.min(axis=2) <= AGLOMERACION_M ** 2
            cerca_del_balon = (x[tramo] - bx[tramo, None]) ** 2 + (y[tramo] - by[tramo, None]) ** 2 <= CERCA_DEL_BALON_M ** 2
            candidato[tramo] = cerca_de_otro & cerca_del_balon
    corte = xs[0].shape[1]
    salida = {"local": candidato[:, :corte], "visitante": candidato[:, corte:]}
    if clave is not None:
        _CANDIDATOS[clave] = salida
    return salida


def ausencias_en_aglomeraciones(candidato, presente, probabilidad, rng):
    """Un jugador en una aglomeración (`en_aglomeracion`) desaparece con `probabilidad` por frame, durante
    una racha geométrica de media MEDIA_AUSENCIA_AGLOMERACION."""
    n, columnas = presente.shape
    candidato = candidato & presente
    sorteo = rng.random((n, columnas))
    fuera = np.zeros((n, columnas), bool)
    for j in range(columnas):
        inicios = np.flatnonzero(candidato[:, j] & (sorteo[:, j] < probabilidad))
        largos = rng.geometric(1.0 / MEDIA_AUSENCIA_AGLOMERACION, size=len(inicios))
        fuera[:, j] = _marcar(inicios, largos, n)
    return fuera & presente


def ausencias_lejos(x, bx, distancia):
    """Falta todo jugador a más de `distancia` m del balón a lo largo del campo."""
    with np.errstate(invalid="ignore"):
        return np.abs(x - bx[:, None]) > distancia


def jugadores_degradados(parte, variante, parametro, rng, clave=None):
    """{equipo: {"x", "y"}} de una parte limpia con los jugadores suavizados y con ausencias."""
    bx = np.asarray(parte["x"], float)
    aglomeracion = en_aglomeracion(parte, clave) if variante == "en las aglomeraciones" else None
    equipos = {}
    for equipo in ("local", "visitante"):
        x = suavizar(np.asarray(parte["equipos"][equipo]["x"], float), SUAVIZADO or 1)
        y = suavizar(np.asarray(parte["equipos"][equipo]["y"], float), SUAVIZADO or 1)
        presente = np.isfinite(x) & np.isfinite(y)
        if variante is None:
            fuera = np.zeros_like(presente)
        elif variante == "al azar":
            fuera = ausencias_al_azar(presente, parametro, rng)
        elif variante == "en las aglomeraciones":
            fuera = ausencias_en_aglomeraciones(aglomeracion[equipo], presente, parametro, rng)
        elif variante == "lejos de la jugada":
            fuera = ausencias_lejos(x, bx, parametro) & presente
        else:
            raise ValueError("variante desconocida: {}".format(variante))
        x, y = x.copy(), y.copy()
        x[fuera], y[fuera] = np.nan, np.nan
        equipos[equipo] = dict(parte["equipos"][equipo], x=x.astype(np.float32), y=y.astype(np.float32))
    return equipos


def generador(cargado, k, variante):
    return np.random.default_rng([SEMILLA, cargado["indice"], k, VARIANTES.index(variante) if variante else 9])


def tracking_jugadores(cargado, condicion, variante, parametro=None):
    """Como `dfl.tracking_de`, con los jugadores degradados. Sin variante y sin suavizado, es el mismo."""
    if variante is not None and parametro is None:
        parametro = CALIBRADO[variante]
    partes = {}
    for k in (1, 2):
        limpia = cargado["partes"][k]
        con_balon = dfl.degradar_parte(limpia, condicion, np.random.default_rng([dfl.SEMILLA, cargado["indice"], k]))
        con_balon["equipos"] = jugadores_degradados(limpia, variante, parametro, generador(cargado, k, variante),
                                                    (cargado["partido"], k))
        partes[k] = con_balon
    return dfl.a_tracking(partes, cargado["campo"], np.random.default_rng([dfl.SEMILLA, cargado["indice"], 99]))


# -- calibración ---------------------------------------------------------------------------------------

def temblor_cm(cargados, ancho):
    """Mediana de la segunda diferencia de los jugadores suavizados (como perfil.segunda_diferencia), en cm."""
    muestras = []
    for cargado in cargados:
        for k in (1, 2):
            for equipo in ("local", "visitante"):
                x = suavizar(np.asarray(cargado["partes"][k]["equipos"][equipo]["x"], float), ancho)
                y = suavizar(np.asarray(cargado["partes"][k]["equipos"][equipo]["y"], float), ancho)
                for j in range(x.shape[1]):
                    ok = np.isfinite(x[:, j]) & np.isfinite(y[:, j])
                    muestras.append(perfil.segunda_diferencia(x[:, j], y[:, j], ok))
    return 100.0 * float(np.median(np.concatenate(muestras)))


def localizados_en_juego(cargados, variante, parametro):
    """Media de localizados por equipo en los frames de juego, y qué parte de las ausencias cae en juego."""
    suma, frames, ausencias, en_juego = 0.0, 0, 0, 0
    for cargado in cargados:
        for k in (1, 2):
            parte = cargado["partes"][k]
            vivo = np.asarray(parte["estado"]) == 1
            equipos = jugadores_degradados(parte, variante, parametro, generador(cargado, k, variante),
                                           (cargado["partido"], k))
            for equipo in ("local", "visitante"):
                presente = np.isfinite(equipos[equipo]["x"])
                original = np.isfinite(np.asarray(parte["equipos"][equipo]["x"], float))
                suma += float(presente[vivo].sum())
                frames += int(vivo.sum())
                quitadas = original & ~presente
                ausencias += int(quitadas.sum())
                en_juego += int(quitadas[vivo].sum())
    return suma / max(frames, 1), en_juego / max(ausencias, 1)


def calibrar(cargados, variante):
    """Bisección del parámetro de la variante hasta OBJETIVO_EN_JUEGO ± TOLERANCIA_CALIBRADO."""
    if variante == "al azar":
        bajo, alto, crece = 0.0, 2000.0, False  # media de las ausencias (frames): más, menos localizados
    elif variante == "en las aglomeraciones":
        bajo, alto, crece = 0.0, 1.0, False
    else:
        bajo, alto, crece = 5.0, 110.0, True  # distancia (m): más, más localizados
    for _ in range(30):
        medio = (bajo + alto) / 2.0
        media, _ = localizados_en_juego(cargados, variante, medio)
        if abs(media - OBJETIVO_EN_JUEGO) <= TOLERANCIA_CALIBRADO / 4:
            break
        if (media < OBJETIVO_EN_JUEGO) == crece:
            bajo = medio
        else:
            alto = medio
    media, parte_en_juego = localizados_en_juego(cargados, variante, medio)
    return float("{:.4g}".format(medio)), media, parte_en_juego


# -- perfil y puntuación -------------------------------------------------------------------------------

def perfil_de(cargados, variante, parametro=None):
    """Agregado 7 del perfil (el mismo código que midió el ATD) con los 7 partidos juntos."""
    parciales = []
    for cargado in cargados:
        trk = tracking_jugadores(cargado, dfl.VOTAN[0], variante, parametro)
        evaluado = np.zeros(len(trk.bx), bool)
        for inicio, fin in trk.blocks:
            evaluado[inicio:fin] = True
        parciales.append({"jugadores": perfil._jugadores(trk.px, trk.py, trk.team, evaluado, trk.fps, perfil.PRM)})
    j = {"_muestra_slots": np.vstack([p["jugadores"]["_muestra_slots"] for p in parciales]),
         "localizados": sum(p["jugadores"]["localizados"] for p in parciales),
         "_muestra_tramos": np.concatenate([p["jugadores"]["_muestra_tramos"] for p in parciales]),
         "_muestra_d2": np.concatenate([p["jugadores"]["_muestra_d2"] for p in parciales]),
         "saltos": sum(p["jugadores"]["saltos"] for p in parciales),
         "frames_evaluados": sum(p["jugadores"]["frames_evaluados"] for p in parciales)}
    minutos = j["frames_evaluados"] / dfl.FPS / 60.0
    salida = {}
    for k, equipo in enumerate(("local", "visitante")):
        valores = np.repeat(np.arange(j["localizados"][k].size), j["localizados"][k])
        salida[equipo] = dict({"media": float(valores.mean())}, **perfil._cuantiles(valores))
    salida["tramo_p50_s"] = perfil._cuantiles(j["_muestra_tramos"], 1.0 / dfl.FPS)["p50"]
    salida["temblor_cm"] = perfil._mediana(j["_muestra_d2"], 100.0)
    salida["saltos_por_minuto"] = j["saltos"] / minutos
    return salida


def vota(p):
    """La regla fijada antes de medir: media ±0,5, p50 = 11, p10 de 8 a 10, p90 = 11, tramo de ×½ a ×2."""
    medias = (p["local"]["media"] + p["visitante"]["media"]) / 2.0
    cuantiles = all(p[e]["p50"] == 11 and 8 <= p[e]["p10"] <= 10 and p[e]["p90"] == 11
                    for e in ("local", "visitante"))
    tramo = ATD["tramo_p50_s"] / 2 <= p["tramo_p50_s"] <= ATD["tramo_p50_s"] * 2
    return abs(medias - ATD["media"]) <= 0.5 and cuantiles and tramo


def puntuar_variante(variante, partidos, n_draws, fichero=VERSIONES):
    versiones = puntuar.leer_versiones(fichero)[0]
    original = dfl.tracking_de, dfl.CONDICIONES
    dfl.tracking_de = lambda cargado, condicion: tracking_jugadores(cargado, condicion, variante)
    dfl.CONDICIONES = dfl.VOTAN
    try:
        salida, _, _ = puntuar.medir(partidos, "oraculo", n_draws, versiones=versiones)
    finally:
        dfl.tracking_de, dfl.CONDICIONES = original
    return salida, versiones


def main():
    global SUAVIZADO
    parser = argparse.ArgumentParser(description="Apuesta B con los jugadores degradados como los del ATD.")
    parser.add_argument("--calibrar", action="store_true", help="calibra el suavizado y cada variante")
    parser.add_argument("--perfil", action="store_true", help="perfil de los jugadores de cada variante")
    parser.add_argument("--sin-degradar", action="store_true",
                        help="comprobación: sin degradar a los jugadores, el tracking y la tabla del harness")
    parser.add_argument("--ajustar-aglomeraciones", action="store_true",
                        help="el ajuste del 14/11: ausencias de 2, 3 o 4 s en las aglomeraciones, la primera que "
                             "pase el perfil")
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--versiones", default=VERSIONES,
                        help="fichero de versiones del harness que se puntúa (por defecto, apuesta_b.json)")
    args = parser.parse_args()
    partidos = list(dfl.PARTIDOS)

    if args.ajustar_aglomeraciones:
        global MEDIA_AUSENCIA_AGLOMERACION
        cargados = [dfl.cargar(p) for p in partidos]
        variante = "en las aglomeraciones"
        print("### «{}»: ausencias de 2, 3 o 4 s (la primera que pase el perfil)".format(variante))
        print()
        for media in AUSENCIAS_AGLOMERACION:
            MEDIA_AUSENCIA_AGLOMERACION = media
            parametro, en_juego, parte = calibrar(cargados, variante)
            p = perfil_de(cargados, variante, parametro)
            pasa = vota(p)
            print("- {} frames: probabilidad {} → {:.3f} en juego ({:.1f} % de las ausencias en juego); "
                  "local {:.2f} / {:g} / {:g} / {:g}; visitante {:.2f} / {:g} / {:g} / {:g}; tramo p50 {:.1f} s; "
                  "saltos {:.1f}/min; vota: {}".format(
                      media, parametro, en_juego, 100.0 * parte,
                      p["local"]["media"], p["local"]["p10"], p["local"]["p50"], p["local"]["p90"],
                      p["visitante"]["media"], p["visitante"]["p10"], p["visitante"]["p50"], p["visitante"]["p90"],
                      p["tramo_p50_s"], p["saltos_por_minuto"], "sí" if pasa else "no"))
            if pasa:
                break
        return

    if args.sin_degradar:
        SUAVIZADO = None  # ni suavizado ni ausencias: tiene que ser el tracking del harness
        cargado = dfl.cargar(partidos[0])
        iguales = all(all(np.array_equal(np.asarray(a), np.asarray(b), equal_nan=a.dtype.kind == "f")
                          if isinstance(a, np.ndarray) else a == b
                          for a, b in zip(dfl.tracking_de(cargado, c), tracking_jugadores(cargado, c, None)))
                      for c in dfl.VOTAN)
        print("sin degradar, el tracking es idéntico al de dfl.tracking_de ({}): {}".format(
            partidos[0], "sí" if iguales else "NO"))
        salida, versiones = puntuar_variante(None, partidos, 0)
        main_ = puntuar.version_de_main(versiones)
        for condicion in dfl.VOTAN:
            print("main con el flag, «{}»: {:.3f}".format(condicion, salida["flag"][condicion][main_]["spell_f1"]))
        return

    cargados = [dfl.cargar(p) for p in partidos]
    if args.calibrar:
        print("### Suavizado de los jugadores (temblor del ATD: {} cm)".format(ATD["temblor_cm"]))
        print()
        temblores = {k: temblor_cm(cargados, k) for k in SUAVIZADOS}
        for k, valor in temblores.items():
            print("- {} frames: {:.3f} cm".format(k, valor))
        SUAVIZADO = min(SUAVIZADOS, key=lambda k: (abs(temblores[k] - ATD["temblor_cm"]), k))
        print("\nelegido: {} frames".format(SUAVIZADO))
        print()
        print("### Ausencias: localizados por equipo en los frames de juego (objetivo {} ± {})".format(
            OBJETIVO_EN_JUEGO, TOLERANCIA_CALIBRADO))
        print()
        base, _ = localizados_en_juego(cargados, None, None)
        print("- sin ausencias: {:.2f}".format(base))
        for variante in VARIANTES:
            parametro, media, en_juego = calibrar(cargados, variante)
            print("- {}: parámetro {} → {:.3f}; ausencias que caen en juego: {:.1f} %".format(
                variante, parametro, media, 100.0 * en_juego))
        return

    if SUAVIZADO is None or set(CALIBRADO) != set(VARIANTES):
        sys.exit("faltan SUAVIZADO y CALIBRADO: ejecuta --calibrar y escríbelos en este fichero")
    perfiles = {v: perfil_de(cargados, v) for v in VARIANTES}
    del cargados
    if args.perfil:
        print("### Perfil de los jugadores frente al ATD (agregado 7, frames evaluados, 7 partidos)")
        print()
        print("| variante | localizados local: media / p10 / p50 / p90 | visitante | tramo p50 (s) | temblor (cm) "
              "| saltos > 12 m/s por min | vota |")
        print("|---|---|---|---|---|---|---|")
        print("| ATD | 10,20 / 9 / 11 / 11 | 10,29 / 9 / 11 / 11 | 35,5 | 0,136 | 0,689 | – |")
        for variante, p in perfiles.items():
            celdas = ["{:.2f} / {:g} / {:g} / {:g}".format(p[e]["media"], p[e]["p10"], p[e]["p50"], p[e]["p90"])
                      for e in ("local", "visitante")]
            print("| {} | {} | {} | {:.1f} | {:.3f} | {:.3f} | {} |".format(
                variante, celdas[0], celdas[1], p["tramo_p50_s"], p["temblor_cm"], p["saltos_por_minuto"],
                "sí" if vota(p) else "no").replace(".", ","))
        return

    for variante in VARIANTES:
        print("## Jugadores «{}» ({}; parámetro {}, suavizado {})".format(
            variante, "vota" if vota(perfiles[variante]) else "sin voto", CALIBRADO[variante], SUAVIZADO))
        print()
        salida, versiones = puntuar_variante(variante, partidos, args.bootstrap, args.versiones)
        print(puntuar.tablas(salida, partidos, versiones))
        print()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
