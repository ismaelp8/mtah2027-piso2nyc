"""Prueba del detector de silbatos (silbato.py) con audio sintético. No lee nada de ningún partido.

    python validation/scripts/prueba_silbato.py

1. Ruido de fondo con tres silbatos colocados en momentos conocidos y tres señuelos que no deben
   detectarse (un tono grave, un chasquido corto y un barrido rápido).
2. Lo mismo leído en bloques irregulares: tiene que dar exactamente lo mismo.
3. Lo mismo metido en un mp4 con ffmpeg (AAC), con el audio empezando a la vez que el vídeo y 0,4 s
   después: comprueba la decodificación y la alineación con los frames.
"""

import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silbato  # noqa: E402

SR, FPS = silbato.SR, silbato.FPS
DURACION_S = 40
TOLERANCIA = 2  # frames

# (inicio en s, fin en s) de los silbatos que se colocan
SILBATOS = [(5.0, 5.5), (10.0, 10.48), (20.0, 21.5)]

fallos = []


def comprobar(condicion, texto, detalle=""):
    print("  [{}] {}{}".format("OK" if condicion else "FALLO", texto,
                               "   " + detalle if detalle else ""))
    if not condicion:
        fallos.append(texto)


def tono(t, inicio, fin, hz, amplitud, trino_hz=0.0, vibrato_hz=0.0, vibrato_ancho=0.0):
    dentro = (t >= inicio) & (t < fin)
    fase = 2 * np.pi * hz * t
    if vibrato_hz:
        fase += (vibrato_ancho / vibrato_hz) * np.sin(2 * np.pi * vibrato_hz * t)
    envolvente = 1.0 if not trino_hz else 0.75 + 0.25 * np.sin(2 * np.pi * trino_hz * t)
    return np.where(dentro, amplitud * envolvente * np.sin(fase), 0.0)


def senal():
    rng = np.random.default_rng(20261113)
    n = DURACION_S * SR
    t = np.arange(n) / SR
    # ruido rosa aproximado, con subidas y bajadas lentas como una grada
    espectro = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    espectro[1:] /= np.sqrt(f[1:] / 100.0)
    espectro[0] = 0
    ruido = np.fft.irfft(espectro, n)
    ruido *= 0.1 / ruido.std()
    ruido *= 1.0 + 0.3 * np.sin(2 * np.pi * 0.1 * t)

    x = ruido
    x += tono(t, 5.0, 5.5, 3100, 0.05, trino_hz=25)                      # silbato con trino
    x += tono(t, 10.0, 10.2, 2800, 0.05) + tono(t, 10.28, 10.48, 2800, 0.05)  # dos pitidos
    x += tono(t, 20.0, 21.5, 2600, 0.05, vibrato_hz=5, vibrato_ancho=40)  # silbato largo
    # señuelos
    x += tono(t, 14.0, 15.0, 500, 0.1)                                    # grave, fuera de banda
    x += tono(t, 26.0, 26.04, 3000, 0.1)                                  # chasquido de 40 ms
    barrido = (t >= 30.0) & (t < 30.25)
    fase = 2 * np.pi * (2000 * (t - 30.0) + 0.5 * (2500 / 0.25) * (t - 30.0) ** 2)
    x += np.where(barrido, 0.05 * np.sin(fase), 0.0)                      # 2–4,5 kHz en 0,25 s
    return np.clip(x, -1, 1).astype(np.float32)


def esperados(desplazamiento_frames=0):
    return [(int(round(a * FPS)) + desplazamiento_frames, int(round(b * FPS)) - 1 + desplazamiento_frames)
            for a, b in SILBATOS]


def comparar(detectados, desplazamiento_frames, nombre):
    esp = esperados(desplazamiento_frames)
    comprobar(len(detectados) == len(esp), "{}: {} silbatos".format(nombre, len(esp)),
              "detectados {}".format(len(detectados)))
    for (a, b), fila in zip(esp, detectados):
        ok = abs(fila[0] - a) <= TOLERANCIA and abs(fila[1] - b) <= TOLERANCIA
        comprobar(ok, "{}: silbato de los frames {}–{}".format(nombre, a, b),
                  "detectado {:.0f}–{:.0f} a {:.0f} Hz".format(fila[0], fila[1], fila[3]))


def a_wav(x, ruta):
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def main():
    x = senal()
    n_frames = DURACION_S * FPS

    print("1. Audio sintético, de una vez")
    prom, frec = silbato.rasgos_por_frame([x], n_frames, silbato.HOP // 2)
    sin_silbato = np.ones(n_frames, dtype=bool)
    for a, b in esperados():
        sin_silbato[a - 3:b + 4] = False
    print("  prominencia sin silbato (dB): p50={:.1f} p99={:.1f} max={:.1f}".format(
        *np.nanpercentile(prom[sin_silbato], [50, 99, 100])))
    detectados = silbato.detectar(prom, frec)
    comparar(detectados, 0, "directo")

    print("\n2. El mismo audio en bloques irregulares")
    cortes = np.cumsum(np.resize([7777, 123, 50000, 1], 400))
    cortes = cortes[cortes < len(x)]
    prom2, frec2 = silbato.rasgos_por_frame(np.split(x, cortes), n_frames, silbato.HOP // 2)
    comprobar(np.array_equal(prom, prom2, equal_nan=True) and np.array_equal(frec, frec2, equal_nan=True),
              "mismos rasgos que de una vez")

    print("\n3. Dentro de un mp4 (AAC), pasando por ffmpeg")
    with tempfile.TemporaryDirectory() as carpeta:
        ruta_wav = os.path.join(carpeta, "sintetico.wav")
        a_wav(x, ruta_wav)
        for retraso_s in (0.0, 0.4):
            ruta_mp4 = os.path.join(carpeta, "sintetico_{}.mp4".format(retraso_s))
            subprocess.run(
                ["ffmpeg", "-nostdin", "-y", "-v", "error",
                 "-f", "lavfi", "-i", "color=c=black:s=64x64:r={}:d={}".format(FPS, DURACION_S + 1),
                 "-itsoffset", str(retraso_s), "-i", ruta_wav,
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                 "-shortest", ruta_mp4],
                check=True)
            meta, prom3, frec3 = silbato.rasgos_video(ruta_mp4, n_frames)
            dif = float(meta["audio"]["start_time"]) - float(meta["video"]["start_time"])
            print("  audio {:.1f} s después del vídeo (ffprobe: {:+.3f} s)".format(retraso_s, dif))
            comparar(silbato.detectar(prom3, frec3), int(round(retraso_s * FPS)),
                     "mp4 +{:.1f} s".format(retraso_s))

    print("\n" + ("TODO BIEN" if not fallos else "{} FALLOS".format(len(fallos))))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
