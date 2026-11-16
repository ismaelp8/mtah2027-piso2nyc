"""El detector de balón del vídeo táctico: descarga, comprobación, carga, detección y vuelta al campo.

Es el módulo compartido de la línea del balón del vídeo (`validation/balon_video/BITACORA.md`): lo usan el sondeo de la
puerta 1b (`validation/partido/balon_video_sondeo.py`) y, si se pasa la puerta 2, la detección del partido entero. Así
las dos miden con el mismo código.

- **El modelo:** `martinjolif/yolo-football-ball-detection` (YOLO11n, una sola clase, AGPL-3.0), entrenado con un
  dataset de Roboflow (CC BY 4.0) de clips de la Bundesliga. Se fija el fichero por su sha256 y la revisión de Hugging
  Face de la que se baja, para que todo el equipo use exactamente los mismos pesos.
- **Corre en local y sin red:** `cargar()` pone a ultralytics en modo sin conexión antes de importarlo (sin telemetría,
  sin comprobaciones en línea, sin instalar nada). La regla nº 1 prohíbe mandar frames del partido a ningún servicio.
- **Un .pt es un pickle:** cargarlo puede ejecutar código. La garantía es el sha256 fijado (`cargar()` lo comprueba
  siempre) más `ULTRALYTICS_SAFE_LOAD=1`, que carga con `weights_only` y una lista de clases permitidas. Una tercera
  red: `escanear_pickle()` repasa sin cargarlo qué nombra el pickle y solo acepta los 29 pares (módulo, nombre)
  exactos que nombra el .pt fijado (`PICKLE_PERMITIDOS`).
- **CPU y lo más determinista posible:** la entrega se tiene que regenerar byte a byte. Se fijan los hilos (`HILOS`,
  el mismo número en todas partes: con otro número de hilos la salida cambia en el último bit), los algoritmos
  deterministas de torch y el dispositivo, y `detectar()` redondea su salida. El redondeo reduce las diferencias
  entre máquinas, pero no las elimina; la reproducción entre máquinas se comprueba comparando la huella de la caché
  de detecciones (puerta 2, punto 3).
- **La variante fijada** (bitácora, 16/11 a las 16:00): un recorte de `LADO` = 320 px alrededor de la proyección del
  balón del ATD en t+4, ampliado `FACTOR` = 2 (la red recibe 640×640), con confianza `CONF` = 0,10.

Los imports pesados (cv2, torch, ultralytics) van dentro de las funciones: el módulo se importa con solo numpy, y la
descarga solo necesita la biblioteca estándar.

Uso como script (la descarga no necesita torch):

    python validation/balon_video/detector.py --descargar            # baja el .pt a ~/mtah2027-modelos/
    python validation/balon_video/detector.py --comprobar            # sha256, escaneo y una detección en blanco
"""

import argparse
import hashlib
import math
import os
import pickletools
import sys
import zipfile

import numpy as np

MODELO_REPO = "martinjolif/yolo-football-ball-detection"
MODELO_REVISION = "63666b30e2a4973e089c982769f146af54530750"  # campo "sha" de la API de Hugging Face (16/11)
MODELO_FICHERO = "yolo-football-ball-detection.pt"
MODELO_URL = "https://huggingface.co/{}/resolve/{}/{}".format(MODELO_REPO, MODELO_REVISION, MODELO_FICHERO)
# sha256 del .pt: el de la copia que bajó la sesión de la puerta 0, y el mismo que Hugging Face da como
# X-Linked-ETag de esa revisión (16/11).
MODELO_SHA256 = "fb37942448e7de08745e8aab148d0794f680a738ddd55e5f17abe9ab2d6313fb"
MODELO_BYTES = 5535706
CARPETA_MODELOS = os.path.join(os.path.expanduser("~"), "mtah2027-modelos")
CARPETA_CONFIG = os.path.join(CARPETA_MODELOS, "ultralytics_config")

CONF = 0.10  # confianza mínima por defecto (la de la puerta 0)
LADO = 320  # px: lado del recorte de la variante fijada (roi)
FACTOR = 2  # ampliación del recorte de la variante fijada: la red recibe 640×640
HILOS = 4  # hilos de torch: el mismo en el sondeo, en --comprobar y en la detección del partido entero
GRIS = 114  # valor del relleno hasta el múltiplo de 32 (el de ultralytics y el de la puerta 0)
MAX_DET = 10  # detecciones como mucho por imagen: hay un balón; más es ruido
DECIMALES_PX = 3  # x, y, w, h redondeados a 0,001 px
DECIMALES_CONF = 4  # confianza redondeada a 0,0001

# Lo único que puede nombrar el pickle del .pt: los 29 pares (módulo, nombre) exactos que nombra el .pt fijado
# (escaneado el 16/11). `__builtin__` es el nombre de Python 2 que escribe el protocolo 2: se normaliza a `builtins`.
# Nada por prefijo y ningún nombre con punto (con el protocolo 4, pickle resuelve «torch» + «hub.load»).
PICKLE_PERMITIDOS = frozenset([
    ("builtins", "set"),
    ("collections", "OrderedDict"),
    ("torch", "FloatStorage"), ("torch", "HalfStorage"), ("torch", "LongStorage"), ("torch", "Size"),
    ("torch._utils", "_rebuild_parameter"), ("torch._utils", "_rebuild_tensor_v2"),
    ("torch.nn.modules.activation", "SiLU"), ("torch.nn.modules.batchnorm", "BatchNorm2d"),
    ("torch.nn.modules.container", "ModuleList"), ("torch.nn.modules.container", "Sequential"),
    ("torch.nn.modules.conv", "Conv2d"), ("torch.nn.modules.linear", "Identity"),
    ("torch.nn.modules.pooling", "MaxPool2d"), ("torch.nn.modules.upsampling", "Upsample"),
    ("ultralytics.nn.modules.block", "Attention"), ("ultralytics.nn.modules.block", "Bottleneck"),
    ("ultralytics.nn.modules.block", "C2PSA"), ("ultralytics.nn.modules.block", "C3k"),
    ("ultralytics.nn.modules.block", "C3k2"), ("ultralytics.nn.modules.block", "DFL"),
    ("ultralytics.nn.modules.block", "PSABlock"), ("ultralytics.nn.modules.block", "SPPF"),
    ("ultralytics.nn.modules.conv", "Concat"), ("ultralytics.nn.modules.conv", "Conv"),
    ("ultralytics.nn.modules.conv", "DWConv"), ("ultralytics.nn.modules.head", "Detect"),
    ("ultralytics.nn.tasks", "DetectionModel"),
])

ENTORNO_SIN_RED = {
    "YOLO_OFFLINE": "1",  # ultralytics se cree sin conexión: ni telemetría ni comprobaciones en línea
    "YOLO_AUTOINSTALL": "false",  # nunca instala paquetes al vuelo
    "ULTRALYTICS_SAFE_LOAD": "1",  # torch.load con weights_only y las clases conocidas, donde la versión lo admite
    "YOLO_VERBOSE": "false",
}


class ErrorDetector(Exception):
    """Un error del detector con un mensaje sin datos del partido (se puede imprimir tal cual)."""


# -- el fichero del modelo -------------------------------------------------------------------------------------------

def sha256_de(ruta):
    """sha256 en hexadecimal de un fichero, leído por bloques."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def ruta_por_defecto(destino=None):
    """Dónde va el .pt: fuera del repo (no se sube a git y no es dato del partido)."""
    return os.path.join(destino or CARPETA_MODELOS, MODELO_FICHERO)


def descargar_modelo(destino=None, url=MODELO_URL, sha256=MODELO_SHA256):
    """Baja el .pt a `destino` (por defecto ~/mtah2027-modelos/) si no está, y comprueba su sha256.

    Si ya está con el sha256 bueno, no baja nada. Si está con otro, da error y no lo pisa: puede ser otro modelo.
    Baja a un temporal y solo lo renombra cuando el sha256 cuadra. Devuelve la ruta.
    """
    import urllib.request
    ruta = ruta_por_defecto(destino)
    if os.path.exists(ruta):
        if sha256_de(ruta) != sha256:
            raise ErrorDetector("{} ya existe con otro sha256: bórralo y vuelve a descargar".format(ruta))
        return ruta
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    temporal = ruta + ".descargando"
    peticion = urllib.request.Request(url, headers={"User-Agent": "python-urllib"})
    with urllib.request.urlopen(peticion, timeout=120) as r, open(temporal, "wb") as f:
        for bloque in iter(lambda: r.read(1 << 20), b""):
            f.write(bloque)
    obtenido = sha256_de(temporal)
    if obtenido != sha256:
        os.remove(temporal)
        raise ErrorDetector("el fichero bajado no tiene el sha256 fijado ({}…)".format(obtenido[:12]))
    os.replace(temporal, ruta)
    return ruta


def _permitido(modulo, nombre):
    """Solo los pares exactos de PICKLE_PERMITIDOS; un nombre con punto, nunca."""
    if "." in nombre:
        return False
    if modulo == "__builtin__":
        modulo = "builtins"
    return (modulo, nombre) in PICKLE_PERMITIDOS


def globales_de_pickle(datos):
    """[(módulo, nombre)] de todos los GLOBAL, INST y STACK_GLOBAL de un pickle, sin cargarlo.

    STACK_GLOBAL toma el módulo y el nombre de la pila: se siguen las cadenas que se apilan y las que se guardan y se
    recuperan de la memo. Si no se puede saber qué nombra (algo que no es una cadena), da error: mejor rechazar un
    fichero raro que dejarlo pasar. Las extensiones de copyreg (EXT1/2/4) también se rechazan.
    """
    globales, pila, memo = [], [], {}
    for op, arg, _ in pickletools.genops(datos):
        nombre = op.name
        if nombre in ("GLOBAL", "INST"):
            modulo, attr = arg.split(" ", 1)
            globales.append((modulo, attr))
            pila.append(None)
        elif nombre == "STACK_GLOBAL":
            if len(pila) < 2 or not isinstance(pila[-1], str) or not isinstance(pila[-2], str):
                raise ErrorDetector("STACK_GLOBAL con módulo o nombre que no se puede resolver sin cargar")
            globales.append((pila[-2], pila[-1]))
            del pila[-2:]
            pila.append(None)
        elif nombre in ("EXT1", "EXT2", "EXT4"):
            raise ErrorDetector("el pickle usa extensiones de copyreg ({})".format(nombre))
        elif nombre in ("SHORT_BINUNICODE", "BINUNICODE", "BINUNICODE8", "UNICODE", "SHORT_BINSTRING",
                        "BINSTRING", "STRING"):
            pila.append(arg if isinstance(arg, str) else None)
        elif nombre in ("BINPUT", "LONG_BINPUT", "PUT"):
            memo[arg] = pila[-1] if pila else None
        elif nombre == "MEMOIZE":
            memo[len(memo)] = pila[-1] if pila else None
        elif nombre in ("BINGET", "LONG_BINGET", "GET"):
            pila.append(memo.get(arg))
        else:
            # El resto no deja una cadena útil en la cima: basta con que no se confunda con una.
            pila.append(None)
    return globales


def escanear_pickle(ruta):
    """Repasa el pickle (o los pickles) de un .pt sin cargarlo; da error si nombra algo fuera de la lista permitida.

    Un .pt de torch es un zip con un `data.pkl`. Lo permitido: solo los 29 pares exactos de PICKLE_PERMITIDOS, los
    que nombra el .pt fijado; ningún nombre con punto. Devuelve la lista ordenada de lo que nombra. No sustituye al
    sha256 ni a `ULTRALYTICS_SAFE_LOAD`: es una tercera red.
    """
    if not os.path.isfile(ruta):
        raise ErrorDetector("no encuentro el modelo: bájalo con  python validation/balon_video/detector.py "
                            "--descargar")
    if not zipfile.is_zipfile(ruta):
        raise ErrorDetector("el .pt no es un zip de torch.save")
    with zipfile.ZipFile(ruta) as z:
        pickles = sorted(n for n in z.namelist() if n.endswith(".pkl"))
        if not pickles:
            raise ErrorDetector("el .pt no tiene ningún .pkl dentro")
        nombrados = set()
        for nombre in pickles:
            nombrados.update(globales_de_pickle(z.read(nombre)))
    malos = sorted("{}.{}".format(m, n) for m, n in nombrados if not _permitido(m, n))
    if malos:
        raise ErrorDetector("el pickle nombra cosas fuera de la lista permitida: {}".format(", ".join(malos[:10])))
    return sorted(nombrados)


# -- carga -----------------------------------------------------------------------------------------------------------

def preparar_entorno(carpeta_config=None):
    """Variables de entorno de ultralytics para trabajar sin red; antes de importarlo (las lee al importarse)."""
    for clave, valor in ENTORNO_SIN_RED.items():
        os.environ[clave] = valor
    carpeta = carpeta_config or CARPETA_CONFIG
    os.makedirs(carpeta, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = carpeta


def cargar(ruta=None, hilos=HILOS, sha256=MODELO_SHA256, carpeta_config=None):
    """El modelo listo para `detectar`, en CPU, con `hilos` hilos y lo más determinista que deja torch.

    Antes de cargar: el sha256 y `escanear_pickle`. Orden importante: ultralytics vuelve a fijar los hilos de torch al
    preparar el predictor (en el primer `predict`), así que se hace una detección de calentamiento con una imagen en
    negro de 64×64 y **después** se fijan los hilos, y se comprueba. `use_deterministic_algorithms(True)` no rompe la
    inferencia en CPU (probado el 16/11 con torch 2.15 y ultralytics 8.4.215).
    """
    ruta = ruta or ruta_por_defecto()
    if not os.path.exists(ruta):
        raise ErrorDetector("no encuentro el modelo: bájalo con  python validation/balon_video/detector.py "
                            "--descargar")
    if sha256 is not None and sha256_de(ruta) != sha256:
        raise ErrorDetector("el modelo no tiene el sha256 fijado: bórralo y vuelve a descargarlo")
    escanear_pickle(ruta)
    if "ultralytics" in sys.modules:
        raise ErrorDetector("ultralytics ya estaba importado: cargar() lo tiene que importar ella, sin red")
    preparar_entorno(carpeta_config)
    import torch
    try:
        torch.set_num_interop_threads(max(1, int(hilos)))
    except RuntimeError:  # solo se puede una vez por proceso y antes de cualquier operación en paralelo
        pass
    torch.use_deterministic_algorithms(True)
    from ultralytics import YOLO
    from ultralytics.utils import ONLINE, SETTINGS
    if ONLINE:
        raise ErrorDetector("ultralytics se cree con conexión: no se sigue (debería estar en YOLO_OFFLINE)")
    if SETTINGS.get("sync", False):
        SETTINGS.update(sync=False)
    modelo = YOLO(ruta, task="detect")
    detectar(modelo, np.zeros((64, 64, 3), dtype=np.uint8))  # calentamiento: aquí ultralytics toca los hilos
    torch.set_num_threads(max(1, int(hilos)))
    if torch.get_num_threads() != max(1, int(hilos)):
        raise ErrorDetector("torch no deja fijar {} hilos".format(hilos))
    return modelo


# -- detección -------------------------------------------------------------------------------------------------------

def _a_numpy(valores):
    """Un tensor de torch o un array cualquiera como np.ndarray float64."""
    if hasattr(valores, "cpu"):
        valores = valores.cpu()
    if hasattr(valores, "numpy"):
        valores = valores.numpy()
    return np.asarray(valores, dtype=np.float64)


def multiplo_32(valor):
    """El entero múltiplo de 32 igual o mayor que `valor` (el paso de la red)."""
    return int(math.ceil(float(valor) / 32.0) * 32)


def recorte(ancho, alto, centro, lado=LADO):
    """(x0, y0, lado_x, lado_y): el cuadrado de `lado` px centrado en `centro`, recolocado dentro de la imagen.

    Si la imagen es más pequeña que `lado` en un eje, el recorte es la imagen entera en ese eje. El origen se redondea
    al píxel más cercano (`math.floor(c - lado/2 + 0.5)`), igual en todas las máquinas.
    """
    cx, cy = float(centro[0]), float(centro[1])
    if not (math.isfinite(cx) and math.isfinite(cy)):
        raise ValueError("el centro del recorte no es finito")
    lx, ly = min(int(lado), int(ancho)), min(int(lado), int(alto))
    x0 = int(math.floor(cx - lx / 2.0 + 0.5))
    y0 = int(math.floor(cy - ly / 2.0 + 0.5))
    x0 = min(max(x0, 0), int(ancho) - lx)
    y0 = min(max(y0, 0), int(alto) - ly)
    return x0, y0, lx, ly


def detectar(modelo, imagen_bgr, conf=CONF, factor=1, centro=None, lado=LADO, max_det=MAX_DET):
    """Detecciones de balón en una imagen BGR (como la da cv2), en píxeles del frame original.

    - Sin `centro`: la imagen entera. Con `centro` (x, y en píxeles del frame): un recorte cuadrado de `lado` px
      alrededor, recolocado dentro de la imagen si toca un borde (`recorte`).
    - Con `factor` > 1, lo que entra a la red se amplía antes con cv2.INTER_CUBIC (el balón mide pocos píxeles).
    - Después se rellena abajo y a la derecha con gris `GRIS` hasta el múltiplo de 32 en cada eje, como `rellenar32`
      de la puerta 0; no cambia las coordenadas. Así `imgsz` (el lado largo, ya múltiplo de 32) es exactamente lo que
      entra, y el `LetterBox` de ultralytics no reescala: la red ve la escala de `factor`. Sin ese relleno, con un
      lado largo que no es múltiplo de 32, `LetterBox` (scaleup) amplía un poco la imagen (851 px pasan a 864).

    Devuelve un np.ndarray (k, 5) float64 con [x, y, w, h, conf]: el centro y el tamaño de la caja en píxeles del
    frame original, en la convención continua de ultralytics (el píxel de índice i ocupa [i, i+1), así que su centro
    es i + 0,5). La vuelta es x = x0 + x_red / escala. Ordenado por (−conf, x, y), con x, y, w, h redondeados a 0,001
    px y conf a 0,0001. El redondeo reduce las diferencias del último bit, pero no las elimina: la puerta 0 midió
    hasta 0,005 px entre números de hilos distintos, y el umbral de confianza y el NMS se aplican antes de redondear.
    Entre máquinas está sin medir; se comprueba con la huella de la caché de detecciones. Como mucho `max_det`.

    `modelo` es cualquier objeto con el `predict` de ultralytics (las pruebas le pasan uno falso): se llama con
    (imagen, imgsz=, conf=, device="cpu", verbose=False, save=False, max_det=) y se lee `[0].boxes.xywh` y
    `[0].boxes.conf`, como tensores o como arrays.
    """
    imagen = np.asarray(imagen_bgr)
    alto, ancho = imagen.shape[:2]
    if centro is None:
        x0, y0, lx, ly = 0, 0, ancho, alto
        entrada = imagen
    else:
        x0, y0, lx, ly = recorte(ancho, alto, centro, lado)
        entrada = imagen[y0:y0 + ly, x0:x0 + lx]
    escala_x = escala_y = 1.0
    if factor is not None and float(factor) != 1.0:
        if float(factor) < 1.0:
            raise ValueError("el factor de ampliación tiene que ser 1 o más")
        import cv2
        nuevo_x, nuevo_y = int(round(lx * float(factor))), int(round(ly * float(factor)))
        entrada = cv2.resize(entrada, (nuevo_x, nuevo_y), interpolation=cv2.INTER_CUBIC)
        escala_x, escala_y = nuevo_x / float(lx), nuevo_y / float(ly)
    alto_red, ancho_red = entrada.shape[:2]
    alto_32, ancho_32 = multiplo_32(alto_red), multiplo_32(ancho_red)
    if (alto_32, ancho_32) != (alto_red, ancho_red):
        relleno = np.full((alto_32, ancho_32) + entrada.shape[2:], GRIS, dtype=entrada.dtype)
        relleno[:alto_red, :ancho_red] = entrada
        entrada = relleno
    entrada = np.ascontiguousarray(entrada)
    imgsz = max(alto_32, ancho_32)
    resultado = modelo.predict(entrada, imgsz=imgsz, conf=float(conf), device="cpu", verbose=False, save=False,
                               max_det=int(max_det))[0]
    cajas = _a_numpy(resultado.boxes.xywh).reshape(-1, 4)
    confianzas = _a_numpy(resultado.boxes.conf).reshape(-1)
    if len(cajas) != len(confianzas):
        raise ErrorDetector("el modelo devuelve distinto número de cajas y de confianzas")
    salida = np.empty((len(cajas), 5), dtype=np.float64)
    salida[:, 0] = x0 + cajas[:, 0] / escala_x
    salida[:, 1] = y0 + cajas[:, 1] / escala_y
    salida[:, 2] = cajas[:, 2] / escala_x
    salida[:, 3] = cajas[:, 3] / escala_y
    salida[:, :4] = np.round(salida[:, :4], DECIMALES_PX)
    salida[:, 4] = np.round(confianzas, DECIMALES_CONF)
    salida = salida[np.isfinite(salida).all(axis=1)]
    orden = np.lexsort((salida[:, 1], salida[:, 0], -salida[:, 4]))
    return salida[orden][:int(max_det)]


# -- del vídeo al campo ----------------------------------------------------------------------------------------------

def campo_desde_pixeles(H, x, y, largo, ancho):
    """Píxeles del frame -> metros del campo, con origen en una esquina (como `possession/tracking.py`).

    `H` es la homografía del frame (`starter/load_homography`), que va de coordenadas normalizadas del campo (0–1) a
    píxeles; aquí se usa su inversa y se escala por (largo, ancho). Escalares o arrays. Con una matriz no válida (NaN
    o singular) devuelve NaN.
    """
    H = np.asarray(H, dtype=np.float64)
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if not np.isfinite(H).all():
        nan = np.full(np.broadcast(x, y).shape, np.nan)
        return nan, nan.copy()
    try:
        inversa = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        nan = np.full(np.broadcast(x, y).shape, np.nan)
        return nan, nan.copy()
    with np.errstate(invalid="ignore", divide="ignore"):
        den = inversa[2, 0] * x + inversa[2, 1] * y + inversa[2, 2]
        u = (inversa[0, 0] * x + inversa[0, 1] * y + inversa[0, 2]) / den
        v = (inversa[1, 0] * x + inversa[1, 1] * y + inversa[1, 2]) / den
    return u * float(largo), v * float(ancho)


def pixeles_desde_campo(H, x, y, largo, ancho):
    """Metros del campo -> píxeles del frame: la homografía tal cual (`starter/load_homography.project`)."""
    H = np.asarray(H, dtype=np.float64)
    u = np.asarray(x, dtype=np.float64) / float(largo)
    v = np.asarray(y, dtype=np.float64) / float(ancho)
    with np.errstate(invalid="ignore", divide="ignore"):
        den = H[2, 0] * u + H[2, 1] * v + H[2, 2]
        return (H[0, 0] * u + H[0, 1] * v + H[0, 2]) / den, (H[1, 0] * u + H[1, 1] * v + H[1, 2]) / den


# -- vídeo -----------------------------------------------------------------------------------------------------------

def leer_frames(ruta, frames, n_esperado=None, tamano=(1920, 1080), estado=None, hasta_el_final=False):
    """(frame, imagen BGR) de los `frames` pedidos, leyendo el vídeo de forma SECUENCIAL desde el frame 0.

    Nada de saltar con CAP_PROP_POS_FRAMES: en H.264 no garantiza caer en el frame exacto, y un frame de desfase lo
    estropea todo. Se hace `grab()` en los frames que no se usan y `retrieve()` en los pedidos, y se para al acabar la
    muestra. Se abre con el backend de FFmpeg (en Windows el de por defecto puede ser otro).

    Antes de leer comprueba la resolución (`tamano` = (ancho, alto)). El número de frames que declara el contenedor
    no es el que sale al decodificar (el FAQ define la referencia por los decodificados; un MP4 con lista de edición
    declara de más): se apunta en `estado["frames_declarados"]` y, si no es `n_esperado`, se avisa por stderr, pero
    no se para. Con `hasta_el_final`, después del último frame pedido sigue con `grab()` hasta el final y apunta en
    `estado["frames_decodificados"]` cuántos frames ha decodificado en total: quien llama decide qué hacer si no son
    `n_esperado` (unos 9.000 frames más de decodificar con la muestra del sondeo). Si el vídeo se acaba antes del
    último frame pedido, da error. En `estado` apunta también el backend, los frames leídos y los segundos leyendo.
    Los mensajes no llevan datos.
    """
    import time
    import cv2
    pedidos = np.asarray(frames, dtype=np.int64)
    if len(pedidos) and (np.any(np.diff(pedidos) <= 0) or pedidos[0] < 0):
        raise ValueError("los frames pedidos tienen que ir en orden creciente y sin repetir")
    cap = cv2.VideoCapture(ruta, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        raise ErrorDetector("no se puede abrir el vídeo con FFmpeg")
    estado = {} if estado is None else estado
    try:
        estado["backend"] = cap.getBackendName()
        ancho, alto = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if tamano is not None and (ancho, alto) != tuple(tamano):
            raise ErrorDetector("el vídeo no tiene la resolución esperada ({}x{})".format(*tamano))
        declarados = int(round(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        estado["frames_declarados"] = declarados
        if n_esperado is not None and declarados != int(n_esperado):
            sys.stderr.write("  aviso: el contenedor declara {} frames y se esperan {}; manda lo que se decodifica\n"
                             .format(declarados, int(n_esperado)))
        actual, leidos, segundos = 0, 0, 0.0
        for objetivo in pedidos.tolist():
            inicio = time.perf_counter()
            while actual < objetivo:
                if not cap.grab():
                    raise ErrorDetector("el vídeo se acaba antes de la muestra")
                actual += 1
                leidos += 1
            if not cap.grab():
                raise ErrorDetector("el vídeo se acaba antes de la muestra")
            ok, imagen = cap.retrieve()
            actual += 1
            leidos += 1
            segundos += time.perf_counter() - inicio
            estado["frames_leidos"], estado["segundos_leyendo"] = leidos, segundos
            if not ok or imagen is None:
                raise ErrorDetector("no se puede decodificar un frame de la muestra")
            if tamano is not None and (imagen.shape[1], imagen.shape[0]) != tuple(tamano):
                raise ErrorDetector("un frame no tiene la resolución esperada")
            yield objetivo, imagen
        estado["frames_leidos"], estado["segundos_leyendo"] = leidos, segundos
        if hasta_el_final:
            while cap.grab():
                actual += 1
            estado["frames_decodificados"] = actual
    finally:
        cap.release()


def versiones():
    """Versiones de python, numpy, torch, ultralytics y opencv (las que estén instaladas)."""
    salida = {"python": sys.version.split()[0], "numpy": np.__version__}
    for nombre, modulo in (("torch", "torch"), ("opencv", "cv2")):
        try:
            salida[nombre] = __import__(modulo).__version__
        except Exception:  # no instalado, o roto: se dice y se sigue
            salida[nombre] = None
    # ultralytics, sin importarlo: importarlo antes de `cargar` lo dejaría con la red puesta.
    try:
        from importlib import metadata
        salida["ultralytics"] = metadata.version("ultralytics")
    except Exception:
        salida["ultralytics"] = None
    return salida


def main(argv=None):
    ap = argparse.ArgumentParser(description="El modelo del detector de balón: descarga y comprobación.")
    ap.add_argument("--descargar", action="store_true", help="baja el .pt (si no está) y comprueba su sha256")
    ap.add_argument("--comprobar", action="store_true",
                    help="sha256, escaneo del pickle y una detección en una imagen en negro (necesita torch)")
    ap.add_argument("--destino", default=None, help="carpeta del .pt (por defecto ~/mtah2027-modelos/)")
    args = ap.parse_args(argv)
    if not (args.descargar or args.comprobar):
        ap.print_help()
        return 1
    ruta = ruta_por_defecto(args.destino)
    if args.descargar:
        ruta = descargar_modelo(args.destino)
        print("modelo en {}  sha256 {}…  revisión {}".format(ruta, MODELO_SHA256[:12], MODELO_REVISION[:12]))
    if args.comprobar:
        import importlib.util
        faltan = [m for m in ("torch", "ultralytics", "cv2") if importlib.util.find_spec(m) is None]
        if faltan:
            raise ErrorDetector("faltan {}: ejecuta con el venv del balón (torch, ultralytics y opencv)".format(
                ", ".join(faltan)))
        nombrados = escanear_pickle(ruta)
        print("escaneo del pickle: {} clases o funciones, todas permitidas".format(len(nombrados)))
        modelo = cargar(ruta, hilos=HILOS)
        det = detectar(modelo, np.zeros((360, 640, 3), dtype=np.uint8))
        import torch
        print("cargado en CPU con {} hilos; detecciones en una imagen en negro: {}".format(
            torch.get_num_threads(), len(det)))
        print(versiones())
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except ErrorDetector as e:
        print("ERROR: {}".format(e))
        sys.exit(1)
