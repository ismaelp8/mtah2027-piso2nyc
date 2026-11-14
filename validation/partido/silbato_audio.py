"""¿Se oye el silbato del árbitro en el audio del vídeo táctico? Solo agregados del partido entero.

LEE DATOS DEL PARTIDO (el vídeo táctico y su Smart Tagging): lo ejecuta solo una persona, en local, y
pega solo esta salida. Claude no lo ejecuta (regla nº 1 de CLAUDE.md).

    python validation/partido/silbato_audio.py

Criterios, fijados antes de medir: validation/silbato/BITACORA.md §1. Tarda unos minutos: decodifica
todo el audio del partido.
"""

import os
import sys
import time

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "validation", "scripts"))

import games  # noqa: E402
import silbato  # noqa: E402
from starter.load_smart_tagging import load as cargar_smart_tagging  # noqa: E402

FPS = silbato.FPS
DESPLAZAMIENTOS_PLACEBO_S = (-120, -90, -60, 60, 90, 120)
ANTES_REINICIO_S = 30
BINS_DURACION_S = (0.16, 0.3, 0.6, 1.2, 3.0, np.inf)
BINS_FRECUENCIA_HZ = (2000, 2500, 3000, 3500, 4000, 4501)


def porcentaje(k, n):
    return 100.0 * k / n if n else float("nan")


def imprimir_histograma(nombre, valores, bordes, formato):
    conteo, _ = np.histogram(valores, bins=bordes)
    print("   {}".format(nombre))
    for a, b, c in zip(bordes[:-1], bordes[1:], conteo):
        print("      {:<16} {:>6}  ({:5.1f} %)".format(formato(a, b), c, porcentaje(c, len(valores))))


def ventanas_reinicios(etiquetas):
    """Saques iniciales y demás reinicios del Smart Tagging, como (inicio, fin) en frames."""
    saques, otros = [], []
    for e in etiquetas:
        if (e["code"] or "").strip().lower() != "set pieces":
            continue
        tipo = (e["tags"].get("Type") or "").strip().lower()
        (saques if tipo.startswith("kick off") else otros).append((e["start_frame"], e["end_frame"]))
    return saques, otros


def cuantas_con_silbato(silbatos, ventanas, evaluado):
    """Ventanas dentro de los frames evaluados y cuántas tienen silbato."""
    dentro = [(a, b) for a, b in ventanas if evaluado[max(a, 0):b + 1].any()]
    return sum(silbato.solapan(silbatos, a, b) for a, b in dentro), len(dentro)


def main():
    t0 = time.time()
    video, smart_tagging = games.require(["video", "smart_tagging"])
    n = games.GAMES[games.GAME]["n_video_frames"]
    bloques = games.half_video_blocks(games.GAME)
    evaluado = np.zeros(n, dtype=bool)
    for _, a, b in bloques:
        evaluado[a:b + 1] = True
    n_eval = int(evaluado.sum())

    meta, prominencia, frecuencia = silbato.rasgos_video(video, n)
    v, a = meta["video"], meta["audio"]
    print("1. Audio del vídeo táctico")
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

    saques, otros = ventanas_reinicios(cargar_smart_tagging())
    finales = [(b - FPS, b + 3 * FPS) for _, _, b in bloques]
    ventanas_saque = [(s - 2 * FPS, e + FPS) for s, e in saques]
    paradas = [(s - ANTES_REINICIO_S * FPS, s - 1) for s, _ in otros]
    reanudaciones = list(otros)

    for umbral in silbato.UMBRALES_SENSIBILIDAD:
        todos = silbato.detectar(prominencia, frecuencia, umbral_db=umbral)
        en_eval = np.array([fila for fila in todos if evaluado[int(fila[0]):int(fila[1]) + 1].any()])
        en_eval = en_eval.reshape(-1, 4)
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
        print("      final de parte (de -1 s a +3 s)                 {} de {}".format(k, m))
        k, m = cuantas_con_silbato(todos, ventanas_saque, evaluado)
        print("      saques iniciales, todos juntos                  {} de {}".format(k, m))
        k, m = cuantas_con_silbato(todos, paradas, evaluado)
        print("      reinicios: silbato en los {} s antes           {} de {} ({:5.1f} %)".format(
            ANTES_REINICIO_S, k, m, porcentaje(k, m)))
        tasas = []
        for d in DESPLAZAMIENTOS_PLACEBO_S:
            kd, md = cuantas_con_silbato(todos, [(a + d * FPS, b + d * FPS) for a, b in paradas],
                                         evaluado)
            tasas.append(porcentaje(kd, md))
        print("      placebo de esa ventana (±60/90/120 s)           {:5.1f} %  (de {:.1f} a {:.1f} %)".format(
            np.mean(tasas), min(tasas), max(tasas)))
        k, m = cuantas_con_silbato(todos, reanudaciones, evaluado)
        print("      reinicios: silbato dentro de la etiqueta        {} de {} ({:5.1f} %)".format(
            k, m, porcentaje(k, m)))
        tasas = []
        for d in DESPLAZAMIENTOS_PLACEBO_S:
            kd, md = cuantas_con_silbato(
                todos, [(a + d * FPS, b + d * FPS) for a, b in reanudaciones], evaluado)
            tasas.append(porcentaje(kd, md))
        print("      placebo de esa ventana (±60/90/120 s)           {:5.1f} %  (de {:.1f} a {:.1f} %)".format(
            np.mean(tasas), min(tasas), max(tasas)))

    print("\n   tiempo {:.0f} s".format(time.time() - t0))


if __name__ == "__main__":
    main()
