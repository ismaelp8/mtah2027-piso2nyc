"""La detección del balón en el vídeo táctico del partido entero, guardada en una caché (línea del balón del vídeo).

**Solo lo ejecuta una persona, en local, y solo si la puerta 1b ha dicho «SIGUE»** (regla nº 1 de `CLAUDE.md` y
`validation/balon_video/BITACORA.md`). Claude no lo ejecuta: lee el vídeo, el ATD y la homografía del partido. La
prueba sin datos es `validation/scripts/prueba_balon_video_detectar.py`.

Qué hace:

- **La variante fijada,** la misma que el sondeo de la puerta 1b (`validation/partido/balon_video_sondeo.py`) y con el
  mismo código (`validation/balon_video/detector.py`): un recorte de `LADO` = 320 px alrededor de la proyección del
  balón del ATD en t+4 (`BALL_LEAD`), ampliado `FACTOR` = 2, con confianza `CONF` = 0,10, `HILOS` = 4 y en CPU. No hay
  opciones para cambiarla.
- **Los frames:** todos los de `balon_video_sondeo.bloques_con_juego()` (los tramos evaluados desde el saque de cada
  parte) con balón del ATD en t+4, homografía válida y una proyección finita. También los que tienen el balón del ATD
  fuera del campo: la caché guarda de más y filtra quien la usa. La lista se fija al principio, y el progreso es un %
  de ella.
- **El vídeo se lee de forma secuencial** desde el frame 0 (`detector.leer_frames`), sin saltos, y hasta el final
  para contar sus frames. Si no decodifica 199.319, no escribe la caché (como el sondeo, que entonces no da veredicto).
- **La caché:** `MTAH_DATA_DIR/tactical/BAR-ATH_tactical_balon_video.npz` (el nombre lo bloquea
  `.claude/settings.json`). Guarda TODAS las detecciones de cada frame procesado:
  - `frames` (m,) int64: los frames procesados, en orden;
  - `offsets` (m+1,) int64: las detecciones del frame `frames[i]` son `valores[offsets[i]:offsets[i+1]]`;
  - `valores` (k, 7) float64, columnas `COLUMNAS`: x, y, w, h en píxeles del frame, la confianza, y x, y en metros del
    campo (inversa de la homografía de ese frame, redondeada a `DECIMALES_M`). En el orden de `detector.detectar`;
  - `metadatos` (JSON): formato, partido, frames del vídeo, campo, sha256 del modelo, variante, hilos, versiones,
    sha256 del código que detecta, sha256 de la lista de frames y de los centros de los recortes, y la huella del
    vídeo (tamaño y sha256 de su primer y su último MiB). **Es la llave para reanudar:** todo lo que puede cambiar los
    arrays;
  - `informativo` (JSON): el commit y si había cambios sin commitear en el código que detecta, y los tiempos
    acumulados entre reanudaciones (`tiempos_acumulados`: ejecuciones, frames procesados, segundos detectando, leyendo
    el vídeo y de reloj desde que arranca el script, contados hasta el último parcial o la caché). No entra en la
    llave ni en la huella: un commit de otra cosa entre dos noches no tiene que tirar horas de detección;
  - `estado` («parcial» o «completo») y `huella`.
- **Reanudable:** cada `CADA` = 5.000 frames procesados guarda `BAR-ATH_tactical_balon_video.parcial.npz`. Al
  arrancar, si hay un parcial con la misma llave y sus frames son el principio de la lista, sigue desde ahí (el
  lector decodifica con `grab` hasta ese punto), con `--forzar` o sin él. Un parcial de otra llave da error (solo
  los nombres de lo que difiere) y no se toca; con `--forzar` se tira y se empieza de cero. Todas las escrituras son
  atómicas (un temporal con el mismo prefijo y `os.replace`, que se reintenta si Windows lo bloquea un momento). Al
  acabar escribe la caché y borra el parcial. Antes de leer nada, prueba que puede escribir en `tactical/`.
- **La huella:** sha256 de `frames`, `offsets` y `valores`, en ese orden, con su nombre, tipo y forma, en
  little-endian y con los NaN y los −0,0 normalizados. No es el sha256 del zip, que lleva fechas. Una ejecución
  reanudada da la misma huella que una de un tirón. Es la que se compara entre máquinas (puerta 2, punto 3).

Qué imprime (un JSON, solo agregados): frames procesados, con alguna detección y detecciones; las cifras de la puerta
1b con las mismas funciones del sondeo (`balon_video_sondeo.medir`, alimentado con la caché): % de frames con una
detección a 3 m o menos del balón del ATD en t+4, % de detecciones a más de 5 m, temblor, rachas de fallos, toques;
la celda de la condición 5 leída con estas cifras (`leer_condicion_5`): **es descriptiva, la puerta 2.1 se lee con su
regla**, con `cumple` (D de las etiquetas) y `propio_pasa` (D propio); los tiempos de esta ejecución y los
acumulados; la huella, y para comparar máquinas sin enseñar datos, la huella de solo las columnas en píxeles, el
sha256 de la lista de frames y el del código. Por stderr, los pasos (sin cifras) y el % hecho. Si falla, solo el tipo
de error y las líneas del código.

Uso, desde la raíz del repo, con el entorno del balón (torch, ultralytics, opencv, numpy y pandas):

    python validation/partido/balon_video_detectar.py              # la detección (unas 3 horas en CPU)
    python validation/partido/balon_video_detectar.py --resumen    # los agregados de una caché ya hecha
    python validation/partido/balon_video_detectar.py --forzar     # rehace la caché (la pisa al acabar); si se
                                                                   # corta, el mismo comando sigue desde el parcial
"""

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "validation", "balon_video"))
sys.path.insert(0, AQUI)
import games  # noqa: E402
from possession import tracking  # noqa: E402
from possession.ball import BALL_LEAD  # noqa: E402
import detector as det  # noqa: E402
import balon_video_sondeo as bs  # noqa: E402

FICHEROS = ["video", "atd_meta", "atd_raw", "homography"]
NOMBRE_CACHE = "BAR-ATH_tactical_balon_video.npz"
NOMBRE_PARCIAL = "BAR-ATH_tactical_balon_video.parcial.npz"
SUFIJO_TEMPORAL = ".escribiendo"  # el temporal conserva el prefijo BAR-ATH_tactical_ (lo bloquea settings.json)
CADA = 5000  # frames procesados entre dos parciales
FORMATO = 1
DECIMALES_M = 6  # metros redondeados a 1 µm: la inversa de la homografía (LAPACK) puede cambiar el último bit
COLUMNAS = ("x_px", "y_px", "w_px", "h_px", "conf", "x_m", "y_m")
CODIGO = (os.path.join(RAIZ, "validation", "balon_video", "detector.py"), os.path.abspath(__file__))
ANCHO_IMAGEN, ALTO_IMAGEN = bs.ANCHO_IMAGEN, bs.ALTO_IMAGEN
PASOS_DE_PROGRESO = 200  # el % por stderr, cada 0,5 % de la lista
NOMBRE_PRUEBA = NOMBRE_PARCIAL + ".prueba"  # la prueba de escritura en tactical/ (también con el prefijo)
INTENTOS_REEMPLAZO, ESPERA_REEMPLAZO = 20, 0.5  # os.replace en Windows: el antivirus puede tener el temporal un momento
MIB = 2 ** 20


class ErrorDeteccion(Exception):
    """Un error con un mensaje sin datos del partido (se puede imprimir tal cual)."""


# -- la lista de frames ----------------------------------------------------------------------------------------------

def objetivo(trk, matrices, validas, bloques, adelanto=BALL_LEAD):
    """(frames, centros, recuento): los frames que se detectan y el píxel del centro de cada recorte.

    Un frame entra si está en `bloques`, el balón del ATD en t + `adelanto` es finito (dentro o fuera del campo), la
    homografía del frame es válida y la proyección de ese balón es finita. `centros` es (m, 2) en píxeles, con
    `detector.pixeles_desde_campo` y la homografía del frame t (como el sondeo). `recuento`: cuántos frames hay en los
    bloques, cuántos con balón del ATD en t + `adelanto`, y cuántos de esos se quedan fuera por la homografía o por una
    proyección no finita.
    """
    largo, ancho = trk.pitch
    rx, ry = bs.desplazado(trk.bx, adelanto), bs.desplazado(trk.by, adelanto)
    todos = np.concatenate([np.arange(int(a), int(b)) for a, b in bloques]).astype(np.int64)
    con_ref = todos[np.isfinite(rx[todos]) & np.isfinite(ry[todos])]
    validas = np.asarray(validas, dtype=bool) & np.isfinite(matrices).all(axis=(1, 2))
    frames, centros = [], []
    sin_homografia = sin_centro = 0
    for t in con_ref.tolist():
        if not validas[t]:
            sin_homografia += 1
            continue
        cx, cy = det.pixeles_desde_campo(matrices[t], rx[t], ry[t], largo, ancho)
        if not (np.isfinite(cx) and np.isfinite(cy)):
            sin_centro += 1
            continue
        frames.append(t)
        centros.append((float(cx), float(cy)))
    recuento = {"en_los_tramos_con_juego": int(len(todos)),
                "con_balon_del_atd_en_t_mas_{}".format(adelanto): int(len(con_ref)),
                "fuera_por_homografia_no_valida": int(sin_homografia),
                "fuera_por_proyeccion_no_finita": int(sin_centro)}
    return (np.asarray(frames, dtype=np.int64), np.asarray(centros, dtype=np.float64).reshape(-1, 2), recuento)


# -- la huella y el fichero ------------------------------------------------------------------------------------------

def _canonico(valores, tipo):
    a = np.ascontiguousarray(np.asarray(valores, dtype=tipo))
    if a.dtype.kind == "f":
        a = np.where(np.isnan(a), np.nan, a + 0.0)  # un solo NaN y sin −0,0
    return np.ascontiguousarray(a, dtype=tipo)


def huella(frames, offsets, valores):
    """sha256 de los tres arrays, en orden fijo, con su nombre, tipo y forma (copiada en possession/balon_video.py)."""
    h = hashlib.sha256()
    for nombre, valor, tipo in (("frames", frames, "<i8"), ("offsets", offsets, "<i8"), ("valores", valores, "<f8")):
        a = _canonico(valor, tipo)
        h.update("{}|{}|{}\n".format(nombre, tipo, ",".join(str(s) for s in a.shape)).encode("ascii"))
        h.update(a.tobytes())
    return h.hexdigest()


def sha256_de_ficheros(rutas):
    h = hashlib.sha256()
    for ruta in sorted(rutas, key=os.path.basename):
        h.update(os.path.basename(ruta).encode("utf-8") + b"\n")
        with open(ruta, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def commit_del_codigo(rutas=CODIGO):
    """{"commit", "cambios_sin_commitear"} del código que detecta; None si no hay git."""
    def git(*args):
        return subprocess.run(["git", "-C", RAIZ] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=30)
    try:
        cabeza = git("rev-parse", "--short", "HEAD")
        local = git("status", "--porcelain", "--", *rutas)
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "cambios_sin_commitear": None}
    if cabeza.returncode or local.returncode:
        return {"commit": None, "cambios_sin_commitear": None}
    return {"commit": cabeza.stdout.strip(), "cambios_sin_commitear": bool(local.stdout.strip())}


def huella_del_video(ruta):
    """{"bytes", "sha256_primer_mib", "sha256_ultimo_mib"} del vídeo: otra copia u otro fichero cambia la llave. Son
    unos milisegundos (no hace falta el sha256 de los 4,9 GB). Con menos de 1 MiB, los dos son el fichero entero."""
    tam = os.path.getsize(ruta)
    with open(ruta, "rb") as f:
        primero = hashlib.sha256(f.read(MIB)).hexdigest()
        f.seek(max(0, tam - MIB))
        ultimo = hashlib.sha256(f.read(MIB)).hexdigest()
    return {"bytes": int(tam), "sha256_primer_mib": primero, "sha256_ultimo_mib": ultimo}


def metadatos_de(game, n_frames, pitch, modelo_sha256, versiones, hilos, codigo_sha256, frames, centros, video=None):
    """La llave de la caché: todo lo que puede cambiar los arrays. Nada de tiempos ni de commits. `video`: lo de
    `huella_del_video` (None en las pruebas sin vídeo)."""
    lista = hashlib.sha256()
    lista.update(_canonico(frames, "<i8").tobytes())
    lista.update(_canonico(centros, "<f8").tobytes())
    return {"formato": FORMATO, "partido": game, "frames_del_video": int(n_frames),
            "campo": [float(pitch[0]), float(pitch[1])], "modelo_sha256": modelo_sha256,
            "variante": {"recorte_px": int(det.LADO), "factor": float(det.FACTOR), "conf": float(det.CONF),
                         "adelanto_atd": int(BALL_LEAD), "max_det": int(det.MAX_DET),
                         "decimales_px": int(det.DECIMALES_PX), "decimales_conf": int(det.DECIMALES_CONF),
                         "decimales_m": int(DECIMALES_M), "dispositivo": "cpu"},
            "hilos": int(hilos), "versiones": versiones, "codigo_sha256": codigo_sha256, "columnas": list(COLUMNAS),
            "objetivo": {"frames": int(len(frames)), "sha256": lista.hexdigest()}, "video": video}


def rutas_cache(carpeta):
    return os.path.join(carpeta, NOMBRE_CACHE), os.path.join(carpeta, NOMBRE_PARCIAL)


def _reemplazar(origen, destino):
    """`os.replace` con reintentos ante PermissionError (en Windows, el antivirus o el indexador pueden tener abierto
    un momento el temporal recién escrito). Si no lo consigue, relanza el último error."""
    for intento in range(INTENTOS_REEMPLAZO):
        try:
            os.replace(origen, destino)
            return
        except PermissionError:
            if intento == INTENTOS_REEMPLAZO - 1:
                raise
            time.sleep(ESPERA_REEMPLAZO)


def _borrar_si_se_puede(ruta):
    """Borra `ruta` si existe; si no se puede, lo deja (nunca tapa otro error ni tumba el proceso)."""
    try:
        if os.path.exists(ruta):
            os.remove(ruta)
    except OSError:
        pass


def guardar(ruta, frames, offsets, valores, metadatos, informativo, estado, huella_=""):
    """Escritura atómica: un temporal en la misma carpeta (con el mismo prefijo) y `os.replace` (con reintentos)."""
    temporal = ruta + SUFIJO_TEMPORAL
    try:
        with open(temporal, "wb") as f:
            np.savez(f, frames=_canonico(frames, "<i8"), offsets=_canonico(offsets, "<i8"),
                     valores=_canonico(valores, "<f8").reshape(-1, len(COLUMNAS)),
                     metadatos=np.array(json.dumps(metadatos, sort_keys=True)),
                     informativo=np.array(json.dumps(informativo, sort_keys=True)),
                     estado=np.array(estado), huella=np.array(huella_))
            f.flush()
            os.fsync(f.fileno())
        _reemplazar(temporal, ruta)
    finally:
        _borrar_si_se_puede(temporal)
    return ruta


def probar_escritura(carpeta):
    """Antes de las horas de detección: escribe (con `guardar`, también `os.replace`) y borra un fichero de prueba en
    `carpeta`. En Windows, `os.access` no sirve para esto (solo mira el atributo de solo lectura)."""
    ruta = os.path.join(carpeta, NOMBRE_PRUEBA)
    try:
        guardar(ruta, np.zeros(0, np.int64), np.zeros(1, np.int64), np.zeros((0, len(COLUMNAS))), {}, {}, "prueba")
    except OSError:
        _borrar_si_se_puede(ruta)
        raise ErrorDeteccion("no se puede escribir en la carpeta de los datos del partido (tactical/)") from None
    _borrar_si_se_puede(ruta)  # la escritura ha ido bien; si el borrado falla un momento, el fichero no estorba


def leer(ruta):
    """{"frames", "offsets", "valores", "metadatos", "informativo", "estado", "huella"} de una caché o un parcial.

    Se cierra antes de devolver (en Windows, un .npz abierto no se puede reemplazar ni borrar)."""
    try:
        with np.load(ruta, allow_pickle=False) as z:
            datos = {k: z[k] for k in z.files}
        salida = {"frames": datos["frames"], "offsets": datos["offsets"], "valores": datos["valores"],
                  "metadatos": json.loads(str(datos["metadatos"])), "informativo": json.loads(str(datos["informativo"])),
                  "estado": str(datos["estado"]), "huella": str(datos["huella"])}
    except Exception:
        raise ErrorDeteccion("no se puede leer {} o le falta algo".format(os.path.basename(ruta)))
    comprobar_estructura(salida["frames"], salida["offsets"], salida["valores"], os.path.basename(ruta))
    return salida


def comprobar_estructura(frames, offsets, valores, nombre="la caché"):
    """Error (sin valores) si los arrays no son una caché bien formada."""
    frames, offsets, valores = np.asarray(frames), np.asarray(offsets), np.asarray(valores)
    ok = (frames.ndim == 1 and offsets.ndim == 1 and valores.ndim == 2 and valores.shape[1] == len(COLUMNAS)
          and frames.dtype.kind == "i" and offsets.dtype.kind == "i" and len(offsets) == len(frames) + 1
          and offsets[0] == 0 and offsets[-1] == len(valores) and np.all(np.diff(offsets) >= 0)
          and np.all(np.diff(frames) > 0) and (not len(frames) or frames[0] >= 0))
    if not ok:
        raise ErrorDeteccion("{} no tiene la forma esperada (frames, offsets y valores)".format(nombre))


def diferencias(uno, otro):
    """Las claves de primer nivel en que difieren dos metadatos (solo los nombres)."""
    return sorted(k for k in set(uno) | set(otro) if uno.get(k) != otro.get(k))


def reanudacion(ruta_parcial, metadatos, frames, forzar=False):
    """(previo, nota): lo ya hecho del parcial, si se puede seguir desde ahí, o None. La nota no lleva valores.

    - Un parcial con la misma llave cuyos frames son el principio de la lista se reanuda, con `forzar` o sin él (la
      reanudación da la misma huella que empezar de cero). Así, relanzar el mismo comando siempre sigue.
    - Un parcial legible, marcado «parcial» y de otra llave: sin `forzar`, error (solo los nombres de las claves que
      difieren) y el parcial no se toca; con `forzar`, se borra y se empieza de cero.
    """
    if not os.path.exists(ruta_parcial):
        return None, "de cero: no hay parcial"
    try:
        previo = leer(ruta_parcial)
    except ErrorDeteccion:
        return None, "de cero: el parcial no se puede leer"
    if previo["estado"] != "parcial":
        return None, "de cero: el parcial no está marcado como parcial"
    distintas = diferencias(previo["metadatos"], metadatos)
    if distintas:
        if not forzar:
            raise ErrorDeteccion("hay un parcial de otra configuración (difiere: {}): vuelve al código y al entorno "
                                 "con que se hizo, o usa --forzar para tirarlo".format(", ".join(distintas)))
        os.remove(ruta_parcial)
        return None, "de cero: --forzar tira el parcial de otra configuración (difiere: {})".format(
            ", ".join(distintas))
    k = len(previo["frames"])
    if k > len(frames) or not np.array_equal(previo["frames"], frames[:k]):
        return None, "de cero: los frames del parcial no son el principio de la lista"
    return previo, "reanuda desde el parcial"


# -- la detección ----------------------------------------------------------------------------------------------------

def ejecutar(trk, matrices, validas, bloques, abrir_fuente, detector, carpeta, base, informativo, forzar=False,
             cada=None, progreso=None, paso=None, antes_de_guardar=None, reloj0=None, estado_lectura=None):
    """La detección de punta a punta sobre datos ya cargados. Escribe la caché (y los parciales) en `carpeta`.

    - `abrir_fuente(frames)`: un iterable de (frame, imagen) con exactamente esos frames, en orden (en el partido,
      `detector.leer_frames` sobre el vídeo, que empieza a leer en el frame 0).
    - `detector(imagen, centro)`: un array (k, 5) [x, y, w, h, conf] en píxeles del frame (`detector.detectar`).
    - `base`: lo de la llave que no sale de los datos: partido, sha256 del modelo, versiones, hilos y sha256 del código.
    - `progreso(fraccion)`: se llama cada 1/`PASOS_DE_PROGRESO` de la lista (solo depende de su tamaño).
    - `antes_de_guardar()`: se llama después de agotar la fuente y antes de escribir la caché; si da error, no se
      escribe (en el partido, comprueba que el vídeo decodifica todos sus frames). El parcial se queda.
    - `reloj0`: el `time.perf_counter()` del arranque del script (por defecto, el de esta llamada); `estado_lectura`:
      el diccionario del lector (`segundos_leyendo`). Solo para los tiempos acumulados de `informativo`.

    Devuelve un diccionario con los arrays, la huella, el recuento de la lista, de dónde se reanudó y los tiempos.
    """
    paso = paso or (lambda texto: None)
    cada = CADA if cada is None else int(cada)
    n = len(trk.bx)
    if len(matrices) != n or len(validas) != n:
        raise ErrorDeteccion("la homografía no tiene un frame por frame de vídeo")
    frames, centros, recuento = objetivo(trk, matrices, validas, bloques)
    m = len(frames)
    reloj0 = time.perf_counter() if reloj0 is None else reloj0
    estado_lectura = {} if estado_lectura is None else estado_lectura
    metadatos = metadatos_de(base["partido"], n, trk.pitch, base["modelo_sha256"], base["versiones"], base["hilos"],
                             base["codigo_sha256"], frames, centros, video=base.get("video"))
    ruta_final, ruta_parcial = rutas_cache(carpeta)
    previo, nota = reanudacion(ruta_parcial, metadatos, frames, forzar)
    paso(nota)
    if previo is None:
        k0, cuentas, trozos = 0, [], []
        antes = {}
    else:
        k0 = len(previo["frames"])
        cuentas = np.diff(previo["offsets"]).astype(np.int64).tolist()
        trozos = [np.asarray(previo["valores"], dtype=np.float64)]
        antes = dict(previo["informativo"].get("tiempos_acumulados") or {})
    largo, ancho = trk.pitch
    seg_detectando = 0.0

    def info_con_tiempos(hasta):
        """`informativo` con los tiempos acumulados hasta `hasta` frames (los de antes del parcial, más esta)."""
        esta = {"frames_procesados": int(hasta - k0), "segundos_detectando": seg_detectando,
                "segundos_leyendo_video": float(estado_lectura.get("segundos_leyendo") or 0.0),
                "segundos_de_reloj": time.perf_counter() - reloj0}
        total = {"ejecuciones": int(antes.get("ejecuciones", 0)) + 1,
                 "frames_procesados": int(antes.get("frames_procesados", 0)) + esta.pop("frames_procesados")}
        ultima = {"frames_procesados": int(hasta - k0)}
        for clave, valor in esta.items():
            total[clave] = round(float(antes.get(clave, 0.0)) + float(valor), 1)
            ultima[clave] = round(float(valor), 1)
        salida = dict(informativo)
        salida["tiempos_acumulados"] = total
        salida["ultima_ejecucion"] = dict(ultima, backend_video=estado_lectura.get("backend"),
                                          frames_decodificados=estado_lectura.get("frames_decodificados"))
        return salida

    def arrays(hasta):
        offsets = np.concatenate(([0], np.cumsum(np.asarray(cuentas, dtype=np.int64)))).astype(np.int64)
        valores = np.concatenate(trozos + [np.zeros((0, len(COLUMNAS)))]) if trozos else np.zeros((0, len(COLUMNAS)))
        return frames[:hasta].copy(), offsets, valores

    paso_progreso = max(1, m // PASOS_DE_PROGRESO)
    inicio_total = time.perf_counter()
    iterador = iter(abrir_fuente(frames[k0:]))
    for i in range(k0, m):
        try:
            frame, imagen = next(iterador)
        except StopIteration:
            raise ErrorDeteccion("la fuente de frames se acaba antes de la lista")
        if int(frame) != int(frames[i]):
            raise ErrorDeteccion("la fuente de frames no da los frames de la lista en orden")
        inicio = time.perf_counter()
        d = np.asarray(detector(imagen, (centros[i, 0], centros[i, 1])), dtype=np.float64)
        seg_detectando += time.perf_counter() - inicio
        if d.size == 0:
            d = d.reshape(0, 5)
        if d.ndim != 2 or d.shape[1] != 5:
            raise ErrorDeteccion("el detector no devuelve un array (k, 5)")
        t = int(frames[i])
        fx, fy = det.campo_desde_pixeles(matrices[t], d[:, 0], d[:, 1], largo, ancho)
        filas = np.column_stack([d, np.round(fx, DECIMALES_M), np.round(fy, DECIMALES_M)])
        trozos.append(filas)
        cuentas.append(len(filas))
        hechos = i + 1
        if hechos % cada == 0 and hechos < m:
            f_, o_, v_ = arrays(hechos)
            guardar(ruta_parcial, f_, o_, v_, metadatos, info_con_tiempos(hechos), "parcial")
            trozos[:] = [v_]
        if progreso is not None and (hechos % paso_progreso == 0 or hechos == m):
            progreso(hechos / float(m))
    try:
        next(iterador)  # con `hasta_el_final`, aquí el lector decodifica el resto del vídeo y cuenta sus frames
        raise ErrorDeteccion("la fuente de frames da más frames que la lista")
    except StopIteration:
        pass
    segundos_total = time.perf_counter() - inicio_total
    if antes_de_guardar is not None:
        antes_de_guardar()
    frames_, offsets, valores = arrays(m)
    frames_, offsets, valores = _canonico(frames_, "<i8"), _canonico(offsets, "<i8"), _canonico(valores, "<f8")
    valores = valores.reshape(-1, len(COLUMNAS))
    comprobar_estructura(frames_, offsets, valores)
    hu = huella(frames_, offsets, valores)
    info_final = info_con_tiempos(m)
    guardar(ruta_final, frames_, offsets, valores, metadatos, info_final, "completo", hu)
    _borrar_si_se_puede(ruta_parcial)  # si no se puede, no hace daño: con la caché hecha no se vuelve a leer
    return {"frames": frames_, "offsets": offsets, "valores": valores, "huella": hu, "recuento": recuento,
            "metadatos": metadatos, "reanudado_desde": int(k0), "nota": nota,
            "tiempos_acumulados": info_final["tiempos_acumulados"],
            "tiempos": {"frames_procesados_en_esta_ejecucion": int(m - k0),
                        "segundos_detectando": round(seg_detectando, 1),
                        "ms_por_frame_detectado": round(1000.0 * seg_detectando / (m - k0), 2) if m > k0 else None,
                        "horas_de_esta_ejecucion": round(segundos_total / 3600.0, 3)}}


# -- los agregados ---------------------------------------------------------------------------------------------------

def detector_de_cache(frames, offsets, valores):
    """Un «detector» para `balon_video_sondeo.medir` que devuelve lo guardado: la imagen es el número de frame.

    Devuelve (x, y, conf) en píxeles, como el detector de verdad. Si `medir` pide un frame que no está en la caché, es
    un error: la caché tiene que cubrir todo lo que el sondeo detectaría."""
    frames = np.asarray(frames, dtype=np.int64)

    def detectar(t, centro):
        i = int(np.searchsorted(frames, int(t)))
        if i >= len(frames) or frames[i] != int(t):
            raise ErrorDeteccion("la caché no tiene un frame que el sondeo detectaría")
        filas = valores[offsets[i]:offsets[i + 1]]
        return filas[:, [0, 1, 4]]
    return detectar


def propio_pasa(cond5, celda):
    """Si la celda leída pasa también con el D propio (la emulación lo trae en cada celda), o None si no hay celda o
    la emulación no lo trae. Tolerante: se llama después de horas de detección."""
    if cond5 is None or celda is None:
        return None
    try:
        fila = cond5["celdas"][(float(celda["p"]), float(celda["sigma"]), int(celda["L"]))]
        return bool(fila["propio"]["veredicto"]["pasa"])
    except (KeyError, TypeError, ValueError):
        return None


def para_comparar_maquinas(frames, offsets, valores, metadatos):
    """Huellas para diagnosticar, sin datos, por qué dos cachés difieren: solo las columnas en píxeles (el detector),
    la lista de frames y centros, y el código que detecta."""
    return {"huella_solo_pixeles": huella(frames, offsets, np.asarray(valores, dtype=np.float64)[:, :5]),
            "lista_sha256": metadatos["objetivo"]["sha256"], "codigo_sha256": metadatos["codigo_sha256"]}


def agregados(trk, matrices, validas, bloques, frames, offsets, valores, cond5=None):
    """Las cifras de la puerta 1b con el código del sondeo (`medir`, con roi), sobre todos los frames de `bloques`.

    Se pasa la caché como si fuera el detector: las definiciones (base, condiciones 1 y 2, temblor, rachas, toques y
    la lectura de la condición 5) son exactamente las del sondeo. `medir` solo pide los frames con balón del ATD en
    t+4 dentro del campo y proyección finita, y la caché los tiene todos (si no, error)."""
    fuente = ((t, t) for a, b in bloques for t in range(int(a), int(b)))
    r = bs.medir(fuente, trk, matrices, validas, detector_de_cache(frames, offsets, valores), list(bloques),
                 roi=True, cond5=cond5, variante_fijada=True)
    v = r["veredictos"]
    adel = "atd_en_t_mas_{}".format(BALL_LEAD)
    c5 = dict(v["condicion_5"])
    c5["propio_pasa"] = propio_pasa(cond5, c5.get("celda"))
    c5["nota"] = ("descriptiva: la celda de la condición 5 con las cifras del partido entero; `cumple` va solo con "
                  "el D de las etiquetas y `propio_pasa` con el D propio; la 2.1 pide los dos y se decide con su "
                  "regla (BITACORA.md), no aquí")
    return {
        "frames_con_balon_del_atd_en_t_mas_{}_dentro_del_campo".format(BALL_LEAD):
            r["frames_con_balon_del_atd_en_t_mas_{}_dentro_del_campo".format(BALL_LEAD)],
        "frames_con_balon_del_atd_en_t_mas_{}_fuera_del_campo".format(BALL_LEAD):
            r["frames_con_balon_del_atd_en_t_mas_{}_fuera_del_campo".format(BALL_LEAD)],
        "condicion_1_pct_frames_con_deteccion_a_3m": v["condicion_1"],
        "condicion_2_pct_detecciones_a_mas_de_5m": v["condicion_2"],
        "distancia_a_la_deteccion_mas_cercana_m": r["distancia_a_la_deteccion_mas_cercana_m"],
        "pct_frames_con_balon_del_atd_sin_ninguna_deteccion": r["pct_frames_con_balon_del_atd_sin_ninguna_deteccion"],
        "trayectoria_del_detector": r["trayectoria_del_detector"],
        "detecciones_por_frame": r["detecciones_por_frame"],
        "confianza": r["confianza"],
        "alineacion": {"desfase_con_menor_mediana": r["alineacion_por_desfase"]["desfase_con_menor_mediana"],
                       "por_parte": r["alineacion_por_desfase"]["desfase_con_menor_mediana_por_parte"],
                       "esperado": BALL_LEAD},
        "temblor_y_rachas": r["medidas_de_la_condicion_5"],
        "toques_descriptivos": {
            "toques_por_minuto_del_detector": v["condicion_3_descriptiva"]["toques_por_minuto_del_detector"],
            "toques_por_minuto_del_{}".format(adel):
                v["condicion_3_descriptiva"]["toques_por_minuto_del_{}".format(adel)],
            "ruido_por_minuto_del_detector": v["condicion_4_descriptiva"]["ruido_por_minuto_del_detector"],
            "ruido_por_minuto_del_{}".format(adel): v["condicion_4_descriptiva"]["ruido_por_minuto_del_{}".format(adel)]},
        "condicion_5_descriptiva": c5,
    }


def resumen_de_la_cache(frames, offsets, valores):
    cuantas = np.diff(offsets)
    return {"frames_procesados": int(len(frames)), "frames_con_alguna_deteccion": int(np.sum(cuantas > 0)),
            "pct_frames_con_alguna_deteccion": bs._pct(np.sum(cuantas > 0), len(frames)),
            "detecciones": int(len(valores)),
            "detecciones_por_frame_procesado": round(len(valores) / float(len(frames)), 3) if len(frames) else None}


# -- lo real ---------------------------------------------------------------------------------------------------------

def _paso(texto):
    sys.stderr.write("  {}\n".format(texto))
    sys.stderr.flush()


def _progreso(fraccion):
    sys.stderr.write("\r  {:5.1f} %".format(100.0 * fraccion))
    sys.stderr.flush()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Detección del balón en el vídeo táctico del partido entero (variante fijada: recorte de {} px "
                    "×{}, confianza {:g}, {} hilos, CPU), con caché reanudable en MTAH_DATA_DIR/tactical/{}. Solo la "
                    "ejecuta una persona.".format(det.LADO, det.FACTOR, det.CONF, det.HILOS, NOMBRE_CACHE))
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    ap.add_argument("--modelo", default=None, help="el .pt (por defecto, el de detector.py --descargar)")
    ap.add_argument("--forzar", action="store_true",
                    help="rehace la caché aunque exista (la pisa al acabar) y tira un parcial de otra configuración; "
                         "un parcial de esta misma configuración se reanuda (relanza el mismo comando si se corta)")
    ap.add_argument("--resumen", action="store_true",
                    help="no detecta: imprime los agregados de la caché ya hecha")
    ap.add_argument("--emulacion", default=bs.EMULACION, help="el JSON de emular_dfl.py (condición 5, descriptiva)")
    ap.add_argument("--temblor-dfl", default=bs.TEMBLOR_DFL, help="el JSON de calibrar_temblor_dfl.py --json")
    args = ap.parse_args(argv)
    reloj0 = time.perf_counter()
    if args.forzar and args.resumen:
        raise ErrorDeteccion("--forzar y --resumen no van juntos")
    faltan = [m for m in ("torch", "ultralytics", "cv2", "pandas") if importlib.util.find_spec(m) is None]
    if faltan:
        raise ErrorDeteccion("faltan {}: ejecuta con el venv del balón (torch, ultralytics, opencv, numpy y pandas)"
                             .format(", ".join(faltan)))
    info = games.GAMES[games.GAME]

    # Todo lo que puede fallar, antes del bucle largo: ficheros, carpeta, modelo, emulación y caché.
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el vídeo, el ATD o la homografía del partido: revisa que MTAH_DATA_DIR apunte a la "
              "carpeta de los datos.")
        return 1
    paths = games.asset_paths(games.GAME, args.data_dir)
    carpeta = os.path.dirname(paths["atd_raw"])
    ruta_final, _ = rutas_cache(carpeta)
    if args.resumen and not os.path.exists(ruta_final):
        raise ErrorDeteccion("no hay caché ({}): lanza primero la detección".format(NOMBRE_CACHE))
    if not args.resumen and not args.forzar and os.path.exists(ruta_final):
        raise ErrorDeteccion("ya existe la caché ({}): --resumen para ver sus agregados, --forzar para rehacerla (si "
                             "se cortó una ejecución con --forzar, relánzala con --forzar: sigue desde el parcial)"
                             .format(NOMBRE_CACHE))
    if not args.resumen:
        probar_escritura(carpeta)
    ruta_modelo = args.modelo or det.ruta_por_defecto()
    if not os.path.isfile(ruta_modelo):
        raise ErrorDeteccion("no encuentro el modelo: bájalo con  python validation/balon_video/detector.py "
                             "--descargar")
    modelo_sha256 = det.sha256_de(ruta_modelo)
    if modelo_sha256 != det.MODELO_SHA256:
        raise ErrorDeteccion("el modelo no tiene el sha256 fijado: bórralo y vuelve a descargarlo")
    cond5 = None
    if os.path.isfile(args.emulacion) and os.path.isfile(args.temblor_dfl):
        cond5 = bs.cargar_condicion_5(args.emulacion, args.temblor_dfl)
    else:
        _paso("aviso: no encuentro la emulación o la calibración del temblor; la condición 5 saldrá sin leer")
    ruta_video = games.video_path(games.GAME, args.data_dir)
    base = {"partido": games.GAME, "modelo_sha256": modelo_sha256, "versiones": det.versiones(),
            "hilos": int(det.HILOS), "codigo_sha256": sha256_de_ficheros(CODIGO), "video": huella_del_video(ruta_video)}
    informativo = commit_del_codigo()

    from starter import load_homography  # aquí: la prueba sin datos no necesita pandas
    _paso("leyendo el ATD y la homografía (un par de minutos)")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        trk = tracking.from_atd(paths, games.GAME)
        matrices, _, validas = load_homography.load(games.GAME, args.data_dir)
    bloques = bs.bloques_con_juego(games.GAME)

    if args.resumen:
        cache = leer(ruta_final)
        frames, centros, recuento = objetivo(trk, matrices, validas, bloques)
        if cache["estado"] != "completo" or cache["huella"] != huella(cache["frames"], cache["offsets"],
                                                                      cache["valores"]):
            raise ErrorDeteccion("la caché no está completa o su huella no cuadra con sus arrays")
        actuales = metadatos_de(games.GAME, len(trk.bx), trk.pitch, modelo_sha256, base["versiones"], base["hilos"],
                                base["codigo_sha256"], frames, centros, video=base["video"])
        _paso("calculando los agregados de la caché")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            agg = agregados(trk, matrices, validas, bloques, cache["frames"], cache["offsets"], cache["valores"],
                            cond5)
        print(json.dumps({
            "medida": "detección del balón del vídeo, partido entero (--resumen de la caché), solo agregados",
            "metadatos_que_difieren_de_los_actuales": diferencias(cache["metadatos"], actuales),
            "versiones_de_la_cache": cache["metadatos"].get("versiones"),
            "hilos_de_la_cache": cache["metadatos"].get("hilos"),
            "informativo": cache["informativo"],
            "tiempos_acumulados": cache["informativo"].get("tiempos_acumulados"), "lista": recuento,
            "cache": resumen_de_la_cache(cache["frames"], cache["offsets"], cache["valores"]),
            "como_la_puerta_1b": agg, "huella": cache["huella"],
            "para_comparar_maquinas": para_comparar_maquinas(cache["frames"], cache["offsets"], cache["valores"],
                                                             cache["metadatos"])}, ensure_ascii=False, indent=1))
        return 0

    _paso("cargando el modelo (sha256, escaneo y calentamiento)")
    modelo = det.cargar(ruta_modelo, hilos=det.HILOS)
    import torch
    if torch.get_num_threads() != det.HILOS:
        raise ErrorDeteccion("torch no se ha quedado con los hilos fijados")
    estado = {}

    def abrir_fuente(frames):
        return det.leer_frames(ruta_video, frames, n_esperado=info["n_video_frames"],
                               tamano=(ANCHO_IMAGEN, ALTO_IMAGEN), estado=estado, hasta_el_final=True)

    def detector(imagen, centro):
        return det.detectar(modelo, imagen, det.CONF, det.FACTOR, centro, det.LADO)

    def decodifica_todo():
        if estado.get("frames_decodificados") != info["n_video_frames"]:
            raise ErrorDeteccion("el vídeo no decodifica el número de frames esperado: no se escribe la caché")

    _paso("leyendo el vídeo desde el principio y detectando; después, el resto del vídeo para contar sus frames")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = ejecutar(trk, matrices, validas, bloques, abrir_fuente, detector, carpeta, base, informativo,
                       forzar=args.forzar, progreso=_progreso, paso=_paso, antes_de_guardar=decodifica_todo,
                       reloj0=reloj0, estado_lectura=estado)
    sys.stderr.write("\n")
    _paso("caché escrita; calculando los agregados")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        agg = agregados(trk, matrices, validas, bloques, res["frames"], res["offsets"], res["valores"], cond5)
    decodificados = estado.get("frames_decodificados")
    tiempos = dict(res["tiempos"])
    leidos = estado.get("frames_leidos")
    tiempos["ms_por_frame_decodificado"] = (round(1000.0 * estado["segundos_leyendo"] / leidos, 3)
                                            if leidos else None)
    print(json.dumps({
        "medida": "detección del balón del vídeo, partido entero (validation/balon_video/BITACORA.md), solo agregados",
        "versiones": base["versiones"], "modelo_sha256": modelo_sha256[:12], "modelo_revision": det.MODELO_REVISION[:12],
        "hilos_torch": int(torch.get_num_threads()), "informativo": informativo,
        "backend_video": estado.get("backend"), "frames_declarados_por_el_contenedor": estado.get("frames_declarados"),
        "frames_decodificados": decodificados,
        "variante": res["metadatos"]["variante"], "reanudacion": res["nota"],
        "frames_reanudados_del_parcial": res["reanudado_desde"], "lista": res["recuento"],
        "cache": resumen_de_la_cache(res["frames"], res["offsets"], res["valores"]),
        "como_la_puerta_1b": agg, "tiempos": tiempos, "tiempos_acumulados": res["tiempos_acumulados"],
        "escrita": "MTAH_DATA_DIR/tactical/{}".format(NOMBRE_CACHE), "huella": res["huella"],
        "para_comparar_maquinas": para_comparar_maquinas(res["frames"], res["offsets"], res["valores"],
                                                         res["metadatos"])},
        ensure_ascii=False, indent=1))
    return 0


def cli(argv=None):
    """`main` con los errores sin valores: los nuestros, con su mensaje; cualquier otro, solo el tipo y las líneas."""
    try:
        return main(argv)
    except (ErrorDeteccion, bs.ErrorSondeo, det.ErrorDetector) as e:  # mensajes escritos sin datos del partido
        print("ERROR: {}".format(e))
        return 1
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(bs.informe_de_error(e))
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(cli())
