"""Detector sencillo de silbatos en el audio de un vídeo, alineado a sus frames.

Es una biblioteca: no abre nada por sí sola. Quien la llama decide qué fichero lee.
- `validation/scripts/prueba_silbato.py` la usa con audio sintético (lo puede ejecutar Claude).
- `validation/partido/silbato_audio.py` la usa con el vídeo del partido (solo una persona, en local).

Criterios fijados antes de medir: `validation/silbato/BITACORA.md` §1.

Cómo funciona:
1. ffmpeg decodifica la primera pista de audio a mono, 16 kHz, enteros de 16 bits.
2. Para cada frame de vídeo se toma una ventana de 1.024 muestras centrada en el centro del frame.
   La alineación sale de los `start_time` del vídeo y del audio que da ffprobe.
3. En cada ventana se mide cuánto sobresale el pico de la banda 2.000–4.500 Hz sobre la mediana de su
   entorno (±300 Hz, en dB) y en qué frecuencia está.
4. Un silbato es una racha de frames "tonales" con la frecuencia del pico estable.
"""

import json
import shutil
import subprocess

import numpy as np

FPS = 25
SR = 16000
HOP = SR // FPS            # 640 muestras por frame de vídeo
VENTANA = 1024             # 64 ms
BANDA_HZ = (2000.0, 4500.0)

UMBRAL_DB = 15.0
UMBRALES_SENSIBILIDAD = (10.0, 15.0, 20.0)
MIN_FRAMES = 4             # 0,16 s de frames tonales
HUECO_MAX = 2              # frames no tonales que se toleran dentro de un silbato
SALTO_MAX_HZ = 250.0       # salto máximo de la frecuencia del pico entre frames tonales seguidos

_EPS = 1e-12
_LOTE = 1024               # frames por lote al calcular el espectro (memoria acotada)


# --- ffmpeg -------------------------------------------------------------------------------------

def _herramienta(nombre):
    ruta = shutil.which(nombre)
    if ruta is None:
        raise RuntimeError("no encuentro {}: instala ffmpeg (Mac: `brew install ffmpeg`; Linux: el "
                           "paquete `ffmpeg`; Windows: `winget install ffmpeg`)".format(nombre))
    return ruta


def version_ffmpeg():
    """Primera línea de `ffmpeg -version`. Va en la salida: otra versión puede decodificar distinto."""
    salida = subprocess.run([_herramienta("ffmpeg"), "-version"],
                            check=True, capture_output=True, text=True).stdout
    return salida.splitlines()[0] if salida else "desconocida"


def metadatos(ruta):
    """Lo que ffprobe dice de la primera pista de vídeo y la primera de audio (o None si no hay)."""
    salida = subprocess.run(
        [_herramienta("ffprobe"), "-v", "error", "-show_entries",
         "stream=index,codec_type,codec_name,sample_rate,channels,start_time,duration,r_frame_rate",
         "-of", "json", ruta],
        check=True, capture_output=True, text=True).stdout
    pistas = json.loads(salida).get("streams", [])

    def primera(tipo):
        return next((p for p in pistas if p.get("codec_type") == tipo), None)

    return {"video": primera("video"), "audio": primera("audio")}


def _segundos(pista, clave):
    valor = (pista or {}).get(clave)
    return float(valor) if valor not in (None, "N/A") else None


def desfase_muestras(meta):
    """Muestra (a SR) del audio decodificado donde cae el centro del frame 0 del vídeo."""
    inicio_video = _segundos(meta["video"], "start_time") or 0.0
    inicio_audio = _segundos(meta["audio"], "start_time") or 0.0
    return int(round((inicio_video - inicio_audio) * SR)) + HOP // 2


def bloques_pcm(ruta, muestras_por_bloque=SR * 60):
    """Genera el audio decodificado en bloques de float32 en [-1, 1)."""
    proceso = subprocess.Popen(
        [_herramienta("ffmpeg"), "-nostdin", "-v", "error", "-i", ruta, "-map", "0:a:0",
         "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        stdout=subprocess.PIPE)
    try:
        while True:
            crudo = proceso.stdout.read(muestras_por_bloque * 2)
            if not crudo:
                break
            crudo = crudo[: len(crudo) - len(crudo) % 2]
            yield np.frombuffer(crudo, dtype="<i2").astype(np.float32) / 32768.0
    finally:
        proceso.stdout.close()
        if proceso.wait() != 0:
            raise RuntimeError("ffmpeg terminó con error al decodificar el audio")


# --- rasgos por frame ---------------------------------------------------------------------------

ENTORNO_HZ = 300.0         # cada bin se compara con la mediana de los bins a ±300 Hz

_HANN = np.hanning(VENTANA).astype(np.float32)
_FRECS = np.fft.rfftfreq(VENTANA, 1.0 / SR)
_ENTORNO = int(round(ENTORNO_HZ / (SR / VENTANA)))         # 19 bins a cada lado
_BANDA = np.flatnonzero((_FRECS >= BANDA_HZ[0]) & (_FRECS <= BANDA_HZ[1]))
_DESDE, _HASTA = _BANDA[0] - _ENTORNO, _BANDA[-1] + _ENTORNO + 1
_FRECS_BANDA = _FRECS[_BANDA]


def rasgos(ventanas):
    """(prominencia en dB, frecuencia del pico en Hz) de cada fila de `ventanas` (n × VENTANA).

    La prominencia de cada bin de la banda es su potencia en dB menos la mediana de los bins de su
    entorno (±300 Hz). Así un tono puro sobresale y la pendiente del ruido de fondo (más energía en
    los graves) no se confunde con un tono en el borde de la banda.
    """
    espectro = np.abs(np.fft.rfft(ventanas * _HANN, axis=1)) ** 2
    db = 10.0 * np.log10(espectro[:, _DESDE:_HASTA] + _EPS)
    entorno = np.median(np.lib.stride_tricks.sliding_window_view(db, 2 * _ENTORNO + 1, axis=1),
                        axis=2)
    prominencia = db[:, _ENTORNO:-_ENTORNO] - entorno
    pico = prominencia.argmax(axis=1)
    return (prominencia[np.arange(len(pico)), pico].astype(np.float32),
            _FRECS_BANDA[pico].astype(np.float32))


def rasgos_por_frame(bloques, n_frames, desfase):
    """Rasgos de cada frame de vídeo a partir de bloques de audio.

    `desfase` es la muestra donde cae el centro del frame 0 (ver `desfase_muestras`). Los frames sin
    audio suficiente quedan en NaN, que nunca cuenta como tonal.
    """
    prominencia = np.full(n_frames, np.nan, dtype=np.float32)
    frecuencia = np.full(n_frames, np.nan, dtype=np.float32)
    inicio0 = desfase - VENTANA // 2          # primera muestra de la ventana del frame 0

    # Si la ventana del frame 0 empieza antes del audio, se rellena con silencio.
    relleno = max(0, -inicio0)
    buf = np.zeros(relleno, dtype=np.float32)
    buf_inicio = -relleno                     # índice absoluto de la muestra buf[0]
    f = 0
    for bloque in bloques:
        buf = np.concatenate([buf, bloque])
        fin_buf = buf_inicio + len(buf)
        f_max = min(n_frames, (fin_buf - VENTANA - inicio0) // HOP + 1)
        if f_max > f:
            vistas = np.lib.stride_tricks.sliding_window_view(buf, VENTANA)
            for a in range(f, f_max, _LOTE):
                b = min(f_max, a + _LOTE)
                idx = inicio0 + HOP * np.arange(a, b) - buf_inicio
                prominencia[a:b], frecuencia[a:b] = rasgos(vistas[idx])
            f = f_max
        recorte = inicio0 + HOP * f - buf_inicio
        if recorte > 0:
            buf = buf[recorte:]
            buf_inicio += recorte
        if f >= n_frames:
            break
    return prominencia, frecuencia


def rasgos_video(ruta, n_frames):
    """Metadatos y rasgos por frame del audio de un vídeo."""
    meta = metadatos(ruta)
    if meta["audio"] is None:
        raise RuntimeError("el vídeo no tiene pista de audio")
    prominencia, frecuencia = rasgos_por_frame(bloques_pcm(ruta), n_frames, desfase_muestras(meta))
    return meta, prominencia, frecuencia


# --- silbatos -----------------------------------------------------------------------------------

def detectar(prominencia, frecuencia, umbral_db=UMBRAL_DB, min_frames=MIN_FRAMES,
             hueco_max=HUECO_MAX, salto_max_hz=SALTO_MAX_HZ):
    """Silbatos como array (n × 4): primer frame, último frame, frames tonales, frecuencia mediana."""
    tonales = np.flatnonzero(np.nan_to_num(prominencia, nan=-np.inf) >= umbral_db)
    salida = []
    if len(tonales):
        grupo = [tonales[0]]
        for i in tonales[1:]:
            previo = grupo[-1]
            if i - previo - 1 > hueco_max or abs(frecuencia[i] - frecuencia[previo]) > salto_max_hz:
                salida.append(grupo)
                grupo = []
            grupo.append(i)
        salida.append(grupo)
    filas = [(g[0], g[-1], len(g), float(np.median(frecuencia[g])))
             for g in salida if len(g) >= min_frames]
    return np.array(filas, dtype=float).reshape(-1, 4)


def solapan(silbatos, inicio, fin):
    """¿Algún silbato toca el intervalo de frames [inicio, fin]?"""
    if len(silbatos) == 0:
        return False
    return bool(np.any((silbatos[:, 0] <= fin) & (silbatos[:, 1] >= inicio)))
