"""¿Se oye el silbato del árbitro en el audio del vídeo táctico? Solo agregados del partido entero.

LEE DATOS DEL PARTIDO (el vídeo táctico, su Smart Tagging y el ATD): lo ejecuta solo una persona, en
local, y pega solo esta salida. Claude no lo ejecuta (regla nº 1 de CLAUDE.md).

    python validation/partido/silbato_audio.py

Criterios, fijados antes de medir: validation/silbato/BITACORA.md §1, con los cambios de §2 (14/11).
Tarda unos minutos: decodifica todo el audio del partido y lee el ATD.
"""

import os
import sys
import time
import warnings

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "validation", "scripts"))

import games  # noqa: E402
import silbato  # noqa: E402
from comun import (GOALS_CODE, KICKOFF_GROUP, grouped_by_type, mean_speed, moving_average,  # noqa: E402
                   norm, print_bins, quantiles, utf8_stdout)
from possession.io import load_players  # noqa: E402
from starter.load_smart_tagging import load as cargar_smart_tagging  # noqa: E402

FPS = silbato.FPS
DESPLAZAMIENTOS_PLACEBO_S = (-120, -90, -60, 60, 90, 120)
ANTES_REINICIO_S = 10          # §2.3: con 30 s el placebo se satura
FINAL_ANTES_S, FINAL_DESPUES_S = 5, 3
GOL_DESPUES_S = 10
BINS_DURACION_S = (0.16, 0.3, 0.6, 1.2, 3.0, np.inf)
BINS_FRECUENCIA_HZ = (2000, 2500, 3000, 3500, 4000, 4501)

# Silbato -> frenazo de los jugadores (§2.4)
SUAVIZADO_MEDIO_ANCHO = FPS // 2   # media móvil de ±0,5 s
PREVIA_S = 2
BUSQUEDA_S = 6
DESPUES_S = (3, 5)
YA_PARADOS_MS = 1.2                # SLOW_MS de agregados_jugadores.py
FRENAZO = 0.6
FRENAZO_SENSIBILIDAD = (0.5, 0.6, 0.7)
BINS_RETRASO_S = (0.5, 1, 2, 4)


def porcentaje(k, n):
    return 100.0 * k / n if n else float("nan")


def imprimir_histograma(nombre, valores, bordes, formato):
    conteo, _ = np.histogram(valores, bins=bordes)
    print("   {}".format(nombre))
    for a, b, c in zip(bordes[:-1], bordes[1:], conteo):
        print("      {:<16} {:>6}  ({:5.1f} %)".format(formato(a, b), c, porcentaje(c, len(valores))))


def media(valores):
    """Media que ignora los NaN; NaN si no queda ninguno (sin el aviso de numpy)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return float(np.nanmean(valores)) if len(valores) else float("nan")


def ventanas_partido(etiquetas):
    """Saques iniciales, goles y demás reinicios por tipo, como (inicio, fin) en frames.

    Los reinicios van por tipo con 5 casos o más (comun.grouped_by_type); los saques iniciales, siempre
    juntos y aparte.
    """
    por_tipo = {}
    for tipo, grupo in grouped_by_type(etiquetas).items():
        por_tipo[tipo] = [(e["start_frame"], e["end_frame"]) for e in grupo]
    saques = por_tipo.pop(KICKOFF_GROUP, [])
    goles = [(e["start_frame"], e["end_frame"] + GOL_DESPUES_S * FPS)
             for e in etiquetas if norm(e["code"]) == GOALS_CODE]
    return saques, goles, por_tipo


def mascara(ventanas, n):
    salida = np.zeros(n, dtype=bool)
    for a, b in ventanas:
        salida[max(a, 0):max(min(b + 1, n), 0)] = True
    return salida


def desplazar(ventanas, segundos):
    return [(a + segundos * FPS, b + segundos * FPS) for a, b in ventanas]


def cuantas_con_silbato(silbatos, ventanas, evaluado):
    """Ventanas dentro de los frames evaluados y cuántas tienen silbato."""
    dentro = [(a, b) for a, b in ventanas if evaluado[max(a, 0):b + 1].any()]
    return sum(silbato.solapan(silbatos, a, b) for a, b in dentro), len(dentro)


def tasa_placebo(silbatos, ventanas, evaluado):
    """(media, mínimo, máximo) del % de ventanas con silbato, con las ventanas desplazadas."""
    tasas = [porcentaje(*cuantas_con_silbato(silbatos, desplazar(ventanas, d), evaluado))
             for d in DESPLAZAMIENTOS_PLACEBO_S]
    return np.nanmean(tasas), np.nanmin(tasas), np.nanmax(tasas)


def densidad(silbatos, zona):
    """Silbatos por minuto que empiezan dentro de `zona` (máscara booleana de frames)."""
    minutos = zona.sum() / FPS / 60
    if len(silbatos) == 0 or minutos == 0:
        return float("nan")
    return zona[silbatos[:, 0].astype(int)].sum() / minutos


def imprimir_comprobacion(nombre, silbatos, ventanas, evaluado):
    k, m = cuantas_con_silbato(silbatos, ventanas, evaluado)
    p, pmin, pmax = tasa_placebo(silbatos, ventanas, evaluado)
    print("      {:<44} {:>3} de {:<3} ({:5.1f} %)   placebo {:5.1f} % (de {:.1f} a {:.1f} %)".format(
        nombre, k, m, porcentaje(k, m), p, pmin, pmax))


def frenazos(inicios, v, evaluado):
    """Respuesta de los jugadores a cada silbato (§2.4).

    Devuelve los recuentos de silbatos sin jugadores vistos y con jugadores ya parados, y, para los
    silbatos con jugadores en movimiento, el retraso hasta el frenazo (s, NaN si no lo hay) con cada
    umbral de FRENAZO_SENSIBILIDAD y el cociente entre la velocidad de 3 a 5 s después y la previa.
    """
    n = len(v)
    previa_f, busqueda_f = PREVIA_S * FPS, BUSQUEDA_S * FPS
    sin_jugadores = ya_parados = 0
    retrasos = {u: [] for u in FRENAZO_SENSIBILIDAD}
    cocientes = []
    for inicio in inicios:
        if not (previa_f <= inicio < n - busqueda_f - 1) or not evaluado[inicio]:
            continue
        previa = media(v[inicio - previa_f:inicio])
        if np.isnan(previa):
            sin_jugadores += 1
            continue
        if previa < YA_PARADOS_MS:
            ya_parados += 1
            continue
        tramo = v[inicio + 1:inicio + busqueda_f + 1]
        for u in FRENAZO_SENSIBILIDAD:
            with np.errstate(invalid="ignore"):
                debajo = np.flatnonzero(tramo < u * previa)
            retrasos[u].append((debajo[0] + 1) / FPS if debajo.size else np.nan)
        cocientes.append(media(v[inicio + DESPUES_S[0] * FPS:inicio + DESPUES_S[1] * FPS]) / previa)
    return sin_jugadores, ya_parados, {u: np.array(r) for u, r in retrasos.items()}, np.array(cocientes)


def con_frenazo(retrasos):
    return int(np.sum(~np.isnan(retrasos)))


def main():
    utf8_stdout()
    t0 = time.time()
    video, smart_tagging, atd_raw = games.require(["video", "smart_tagging", "atd_raw"])
    entrada = games.GAMES[games.GAME]
    n = entrada["n_video_frames"]
    bloques = games.half_video_blocks(games.GAME)
    evaluado = np.zeros(n, dtype=bool)
    for _, a, b in bloques:
        evaluado[a:b + 1] = True
    n_eval = int(evaluado.sum())

    meta, prominencia, frecuencia = silbato.rasgos_video(video, n)
    v, a = meta["video"], meta["audio"]
    print("1. Audio del vídeo táctico")
    print("   {}".format(silbato.version_ffmpeg()))
    print("   códec {}   muestreo {} Hz   canales {}".format(
        a.get("codec_name"), a.get("sample_rate"), a.get("channels")))
    dif_inicio = (silbato._segundos(a, "start_time") or 0) - (silbato._segundos(v, "start_time") or 0)
    print("   inicio del audio - inicio del vídeo: {:+.3f} s".format(dif_inicio))
    dur_v, dur_a = silbato._segundos(v, "duration"), silbato._segundos(a, "duration")
    if dur_v and dur_a:
        print("   duración del audio - duración del vídeo: {:+.3f} s".format(dur_a - dur_v))
    print("   frames evaluados con audio analizado: {} de {} ({:.1f} %)".format(
        int(np.isfinite(prominencia[evaluado]).sum()), n_eval,
        porcentaje(np.isfinite(prominencia[evaluado]).sum(), n_eval)))
    p = prominencia[evaluado & np.isfinite(prominencia)]
    print("   prominencia en la banda (dB)  p50={:.1f}  p90={:.1f}  p99={:.1f}  p99.9={:.1f}".format(
        *np.percentile(p, [50, 90, 99, 99.9])))

    saques, goles, por_tipo = ventanas_partido(cargar_smart_tagging())
    finales = [(b - FINAL_ANTES_S * FPS, b + FINAL_DESPUES_S * FPS) for _, _, b in bloques]
    ventanas_saque = [(s - 2 * FPS, e + FPS) for s, e in saques]
    antes = {tipo: [(s - ANTES_REINICIO_S * FPS, s - 1) for s, _ in ventanas]
             for tipo, ventanas in por_tipo.items()}
    # Fuera de toda ventana de reinicio, gol o saque: la densidad de fondo.
    todas = ventanas_saque + goles + [w for t in por_tipo for w in por_tipo[t] + antes[t]]
    fondo = evaluado & ~mascara(todas, n)

    principales = None
    for umbral in silbato.UMBRALES_SENSIBILIDAD:
        todos = silbato.detectar(prominencia, frecuencia, umbral_db=umbral)
        en_eval = np.array([fila for fila in todos if evaluado[int(fila[0]):int(fila[1]) + 1].any()])
        en_eval = en_eval.reshape(-1, 4)
        if umbral == silbato.UMBRAL_DB:
            principales = en_eval
        marca = "  <- criterio principal" if umbral == silbato.UMBRAL_DB else ""
        print("\n2. Silbatos con umbral {:.0f} dB{}".format(umbral, marca))
        minutos = n_eval / FPS / 60
        print("   en los frames evaluados: {}   ({:.2f} por minuto)".format(
            len(en_eval), len(en_eval) / minutos))
        if len(en_eval):
            frames = int((en_eval[:, 1] - en_eval[:, 0] + 1).sum())
            print("   frames dentro de un silbato: {} ({:.2f} % de los evaluados)".format(
                frames, porcentaje(frames, n_eval)))
            duracion = (en_eval[:, 1] - en_eval[:, 0] + 1) / FPS
            imprimir_histograma("duración", duracion, BINS_DURACION_S,
                                lambda a, b: "{:.2f}–{} s".format(a, "" if np.isinf(b) else b))
            imprimir_histograma("frecuencia mediana", en_eval[:, 3], BINS_FRECUENCIA_HZ,
                                lambda a, b: "{}–{} Hz".format(a, min(b, 4500)))

        print("   comprobaciones")
        k, m = cuantas_con_silbato(todos, finales, np.ones(n, dtype=bool))
        print("      final de parte (de -{} s a +{} s)                 {} de {}".format(
            FINAL_ANTES_S, FINAL_DESPUES_S, k, m))
        k, m = cuantas_con_silbato(todos, ventanas_saque, evaluado)
        print("      saques iniciales, todos juntos                  {} de {}".format(k, m))
        imprimir_comprobacion("goles (etiqueta y {} s después)".format(GOL_DESPUES_S), todos, goles, evaluado)
        print("      reinicios por tipo: silbato en los {} s antes | dentro de la etiqueta".format(
            ANTES_REINICIO_S))
        for tipo in sorted(por_tipo, key=lambda t: -len(por_tipo[t])):
            imprimir_comprobacion("{} (n={}), antes".format(tipo, len(por_tipo[tipo])),
                                  todos, antes[tipo], evaluado)
            imprimir_comprobacion("{} (n={}), dentro".format(tipo, len(por_tipo[tipo])),
                                  todos, por_tipo[tipo], evaluado)
        print("      densidad (silbatos por minuto que empiezan en cada zona)")
        print("         fondo, fuera de toda ventana                 {:.2f}".format(densidad(en_eval, fondo)))
        print("         goles                                        {:.2f}".format(
            densidad(en_eval, evaluado & mascara(goles, n))))
        for tipo in sorted(por_tipo, key=lambda t: -len(por_tipo[t])):
            print("         {:<22} antes {:.2f}   dentro {:.2f}".format(
                tipo, densidad(en_eval, evaluado & mascara(antes[tipo], n)),
                densidad(en_eval, evaluado & mascara(por_tipo[tipo], n))))

    print("\n3. Silbato -> frenazo de los jugadores (umbral {:.0f} dB)".format(silbato.UMBRAL_DB))
    px, py = load_players(atd_raw, n, entrada["pitch"])
    velocidad = moving_average(mean_speed(px, py), SUAVIZADO_MEDIO_ANCHO)
    del px, py
    print("   velocidad media de los jugadores (media de 1 s), frames evaluados: {}".format(
        quantiles(velocidad[evaluado])))
    inicios = principales[:, 0].astype(int)
    sin_jug, parados, retrasos, cocientes = frenazos(inicios, velocidad, evaluado)
    moviendo = len(cocientes)
    print("   silbatos: {} en movimiento, {} con los jugadores ya parados (< {:g} m/s en los {} s previos),"
          " {} sin jugadores vistos".format(moviendo, parados, YA_PARADOS_MS, PREVIA_S, sin_jug))

    placebo = {u: [] for u in FRENAZO_SENSIBILIDAD}
    cocientes_placebo = []
    for d in DESPLAZAMIENTOS_PLACEBO_S:
        _, _, r, c = frenazos(inicios + d * FPS, velocidad, evaluado)
        for u in FRENAZO_SENSIBILIDAD:
            placebo[u].append(porcentaje(con_frenazo(r[u]), len(c)))
        cocientes_placebo.append(c)
    for u in FRENAZO_SENSIBILIDAD:
        marca = "  <- criterio principal" if u == FRENAZO else ""
        k = con_frenazo(retrasos[u])
        print("   frenazo (< {:.0f} % de la previa en {} s): {} de {} ({:5.1f} %)   placebo {:5.1f} % "
              "(de {:.1f} a {:.1f} %){}".format(100 * u, BUSQUEDA_S, k, moviendo, porcentaje(k, moviendo),
                                               np.nanmean(placebo[u]), np.nanmin(placebo[u]),
                                               np.nanmax(placebo[u]), marca))
    print_bins("retraso hasta el frenazo ({:.0f} %)".format(100 * FRENAZO),
               list(retrasos[FRENAZO]), BINS_RETRASO_S, indent="   ")
    print("      cuantiles del retraso (s): {}".format(quantiles(retrasos[FRENAZO])))
    print("   velocidad de {} a {} s después / previa: {}   placebo: {}".format(
        DESPUES_S[0], DESPUES_S[1], quantiles(cocientes), quantiles(np.concatenate(cocientes_placebo))))

    print("\n   tiempo {:.0f} s".format(time.time() - t0))


if __name__ == "__main__":
    main()
