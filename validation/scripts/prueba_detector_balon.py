"""Prueba `validation/balon_video/detector.py` sin datos del partido.

    python validation/scripts/prueba_detector_balon.py

Lo puede ejecutar cualquiera, Claude incluido. Prueba:

- `campo_desde_pixeles`: ida y vuelta con `starter/load_homography.project` y tres homografías conocidas (afín,
  con zoom y en perspectiva);
- `detectar` con un modelo falso que devuelve una caja en el centroide de lo brillante de la imagen que recibe: el
  recorte, el recolocado en el borde, la ampliación ×2 (necesita cv2) y la vuelta a píxeles del frame salen exactos;
  lo que entra a la red se rellena con gris abajo y a la derecha hasta el múltiplo de 32 (sin mover las cajas) e
  `imgsz` es su lado largo; el orden (−conf, x, y) y el redondeo; tensores o arrays; la variante fijada (320 ×2);
- `escanear_pickle` acepta un pickle hecho solo con pares permitidos y los 29 del .pt de verdad, y rechaza os.system
  (protocolos 2 y 4), `torch.hub.load` con y sin punto en el nombre (protocolo 4 resuelve «torch» + «hub.load»),
  `torch.utils.collect_env.run`, `pathlib.Path.write_text`, `builtins.getattr`, cosas que la lista vieja dejaba
  pasar por prefijo, un fichero que no es un zip y un zip sin pickle. Los pickles malos se escriben en un temporal y
  nunca se cargan;
- si existen el .pt y ultralytics (y cv2), el escaneo del .pt de verdad y, en dos imágenes de test del dataset abierto
  del modelo (CC BY 4.0) con su etiqueta, que el detector real encuentra el balón cerca. Si no, salta esa parte y lo
  dice. Se puede indicar dónde están con DETECTOR_PT y DETECTOR_DATASET (la carpeta con test/images y test/labels).
"""

import glob
import os
import pickle
import sys
import tempfile
import zipfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "balon_video"))
import detector as det  # noqa: E402

try:
    from starter.load_homography import project
    ORIGEN_PROJECT = "starter/load_homography.project"
except ImportError:  # sin pandas (el entorno de torch): la misma fórmula, copiada
    def project(matrix, x, y):
        x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
        den = matrix[2, 0] * x + matrix[2, 1] * y + matrix[2, 2]
        return ((matrix[0, 0] * x + matrix[0, 1] * y + matrix[0, 2]) / den,
                (matrix[1, 0] * x + matrix[1, 1] * y + matrix[1, 2]) / den)
    ORIGEN_PROJECT = "copia de project (sin pandas no se importa starter/load_homography)"

try:
    import cv2
except ImportError:
    cv2 = None

FALLOS = []
LARGO, ANCHO = 105.3, 68.0
# Dónde buscar el modelo (por defecto, donde lo deja detector.py --descargar) y el dataset abierto del modelo.
CANDIDATOS_PT = [os.environ.get("DETECTOR_PT"), det.ruta_por_defecto()]
CANDIDATOS_DATASET = [os.environ.get("DETECTOR_DATASET")]


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


class Cajas:
    def __init__(self, xywh, conf):
        self.xywh, self.conf = xywh, conf


class Resultado:
    def __init__(self, xywh, conf):
        self.boxes = Cajas(xywh, conf)


class Tensor:
    """Imita un tensor de torch: .cpu().numpy()."""
    def __init__(self, valores):
        self.valores = np.asarray(valores, dtype=np.float32)

    def cpu(self):
        return self

    def numpy(self):
        return self.valores


class ModeloCentroide:
    """Un modelo falso: una caja en el centroide (ponderado por la intensidad) de lo que no es fondo, en la
    convención continua de ultralytics (el píxel i tiene su centro en i + 0,5). Apunta lo que recibe."""

    def __init__(self, como_tensor=False):
        self.como_tensor = como_tensor
        self.llamadas = []

    def predict(self, imagen, imgsz=None, conf=None, device=None, verbose=None, save=None, max_det=None):
        self.llamadas.append({"forma": imagen.shape, "imgsz": imgsz, "device": device, "max_det": max_det,
                              "imagen": imagen})
        relleno = (imagen[:, :, 0] == det.GRIS) & (imagen[:, :, 1] == det.GRIS) & (imagen[:, :, 2] == det.GRIS)
        peso = np.where(relleno, 0.0, imagen[:, :, 2].astype(np.float64))
        if peso.sum() == 0:
            xywh, cf = np.zeros((0, 4)), np.zeros(0)
        else:
            ys, xs = np.mgrid[0:imagen.shape[0], 0:imagen.shape[1]]
            cx = float((peso * (xs + 0.5)).sum() / peso.sum())
            cy = float((peso * (ys + 0.5)).sum() / peso.sum())
            xywh, cf = np.array([[cx, cy, 4.0, 4.0]]), np.array([0.9])
        if self.como_tensor:
            xywh, cf = Tensor(xywh), Tensor(cf)
        return [Resultado(xywh, cf)]


class ModeloFijo:
    """Un modelo falso que devuelve siempre las mismas cajas, en el orden en que se le dan."""

    def __init__(self, xywh, conf):
        self.xywh, self.conf = np.asarray(xywh, float), np.asarray(conf, float)

    def predict(self, imagen, **_):
        return [Resultado(self.xywh, self.conf)]


def imagen_con_punto(x, y, ancho=1920, alto=1080):
    img = np.zeros((alto, ancho, 3), dtype=np.uint8)
    img[y, x, 2] = 255
    return img


def prueba_campo():
    print("campo_desde_pixeles ({})".format(ORIGEN_PROJECT))
    rng = np.random.default_rng(1)
    mx, my = rng.uniform(0, LARGO, 500), rng.uniform(0, ANCHO, 500)
    homografias = {
        "afín": np.array([[1500.0, 0.0, 200.0], [0.0, 800.0, 150.0], [0.0, 0.0, 1.0]]),
        "zoom": np.array([[3840.0, 0.0, -960.0], [0.0, 2160.0, -540.0], [0.0, 0.0, 1.0]]),
        "perspectiva": np.array([[1920.0, 35.0, 10.0], [4.0, 700.0, 100.0], [0.02, -0.6, 1.0]]),
    }
    for nombre, H in homografias.items():
        px, py = project(H, mx / LARGO, my / ANCHO)
        vx, vy = det.campo_desde_pixeles(H, px, py, LARGO, ANCHO)
        error = float(np.max(np.hypot(vx - mx, vy - my)))
        check("ida y vuelta con project, {}: error < 1e-6 m".format(nombre), error < 1e-6, error)
        qx, qy = det.pixeles_desde_campo(H, mx, my, LARGO, ANCHO)
        check("pixeles_desde_campo = project, {}".format(nombre),
              np.allclose(qx, px, atol=1e-9) and np.allclose(qy, py, atol=1e-9))
    H = homografias["afín"]
    x, y = det.campo_desde_pixeles(H, 200.0 + 1500.0 * 0.5, 150.0 + 800.0 * 0.25, LARGO, ANCHO)
    check("un punto conocido: (0,5; 0,25) del campo -> (52,65 m; 17 m)",
          abs(float(x) - LARGO / 2) < 1e-9 and abs(float(y) - ANCHO / 4) < 1e-9, (float(x), float(y)))
    x, y = det.campo_desde_pixeles(np.full((3, 3), np.nan), 10.0, 10.0, LARGO, ANCHO)
    check("con una homografía NaN, NaN", np.isnan(x) and np.isnan(y))


def prueba_detectar():
    print("detectar con un modelo falso")
    m = ModeloCentroide()
    r = det.detectar(m, imagen_con_punto(1234, 567))
    check("imagen entera: la caja vuelve al píxel exacto (1234,5; 567,5)",
          r.shape == (1, 5) and r[0, 0] == 1234.5 and r[0, 1] == 567.5, r.tolist())
    ll = m.llamadas[-1]
    check("imagen entera: entra 1920×1088 (rellena con gris abajo), imgsz 1920, CPU, max_det 10",
          ll["forma"][:2] == (1088, 1920) and ll["imgsz"] == 1920 and ll["device"] == "cpu" and ll["max_det"] == 10
          and bool(np.all(ll["imagen"][1080:] == det.GRIS)) and ll["imagen"][567, 1234, 2] == 255,
          {k: v for k, v in ll.items() if k != "imagen"})

    r = det.detectar(m, imagen_con_punto(1234, 567), centro=(1200.0, 600.0), lado=640)
    check("recorte de 640 alrededor del centro: entra 640×640 con imgsz 640, sin relleno",
          m.llamadas[-1]["forma"][:2] == (640, 640) and m.llamadas[-1]["imgsz"] == 640
          and not bool(np.any(m.llamadas[-1]["imagen"] == det.GRIS)), m.llamadas[-1]["forma"])
    check("recorte: la caja vuelve al píxel exacto del frame", r[0, 0] == 1234.5 and r[0, 1] == 567.5, r.tolist())
    check("recorte: origen redondeado al píxel más cercano", det.recorte(1920, 1080, (1200.4, 600.6), 640) == (
        880, 281, 640, 640), det.recorte(1920, 1080, (1200.4, 600.6), 640))

    for centro, origen in (((5.0, 5.0), (0, 0)), ((1915.0, 1075.0), (1280, 440)), ((-50.0, 2000.0), (0, 440))):
        check("borde: centro {} -> recorte en {}".format(centro, origen),
              det.recorte(1920, 1080, centro, 640)[:2] == origen, det.recorte(1920, 1080, centro, 640))
    r = det.detectar(m, imagen_con_punto(3, 1077), centro=(5.0, 1075.0), lado=640)
    check("borde: un punto en la esquina vuelve exacto (3,5; 1077,5)", r[0, 0] == 3.5 and r[0, 1] == 1077.5,
          r.tolist())
    check("una imagen más pequeña que el lado: se recorta a la imagen", det.recorte(300, 200, (150, 100), 640) == (
        0, 0, 300, 200))
    r = det.detectar(m, imagen_con_punto(40, 20, ancho=100, alto=50))
    ll = m.llamadas[-1]
    check("100×50: entra 128×64 rellena con gris abajo y a la derecha, imgsz 128, y la caja no se mueve",
          ll["imgsz"] == 128 and ll["forma"][:2] == (64, 128) and bool(np.all(ll["imagen"][50:] == det.GRIS))
          and bool(np.all(ll["imagen"][:, 100:] == det.GRIS)) and r[0, 0] == 40.5 and r[0, 1] == 20.5,
          (ll["forma"], ll["imgsz"], r.tolist()))
    check("variante fijada: LADO 320, FACTOR 2, CONF 0,10, HILOS 4",
          (det.LADO, det.FACTOR, det.CONF, det.HILOS) == (320, 2, 0.10, 4))

    if cv2 is None:
        print("  [SALTA] ampliación ×2: no hay cv2 en este entorno")
    else:
        r = det.detectar(m, imagen_con_punto(1234, 567), factor=2)
        check("×2 de la imagen entera: 3840×2160 rellena hasta 3840×2176, con imgsz 3840",
              m.llamadas[-1]["forma"][:2] == (2176, 3840) and m.llamadas[-1]["imgsz"] == 3840, m.llamadas[-1]["forma"])
        check("×2: la caja vuelve al píxel del frame (a 0,001 px)",
              abs(r[0, 0] - 1234.5) <= 1e-3 and abs(r[0, 1] - 567.5) <= 1e-3, r.tolist())
        r = det.detectar(m, imagen_con_punto(1900, 15), factor=2, centro=(1910.0, 10.0), lado=640)
        check("×2 con recorte en el borde: entra 1280×1280 y vuelve exacta",
              m.llamadas[-1]["forma"][:2] == (1280, 1280) and abs(r[0, 0] - 1900.5) <= 1e-3
              and abs(r[0, 1] - 15.5) <= 1e-3, r.tolist())
        check("×2: el ancho de la caja se divide por el factor", r[0, 2] == 2.0, r.tolist())
        r = det.detectar(m, imagen_con_punto(700, 400), factor=det.FACTOR, centro=(690.0, 410.0), lado=det.LADO)
        check("variante fijada (320 ×2): entra 640×640 con imgsz 640 y vuelve exacta",
              m.llamadas[-1]["forma"][:2] == (640, 640) and m.llamadas[-1]["imgsz"] == 640
              and abs(r[0, 0] - 700.5) <= 1e-3 and abs(r[0, 1] - 400.5) <= 1e-3, r.tolist())
        r = det.detectar(m, imagen_con_punto(700, 400), factor=1.33, centro=(690.0, 410.0), lado=640)
        # La ampliación no entera (851/640) con INTER_CUBIC mueve el centroide unas centésimas: no es el relleno.
        check("640 ×1,33 (851 px): rellena hasta 864, imgsz 864, y la caja vuelve a 0,1 px",
              m.llamadas[-1]["forma"][:2] == (864, 864) and m.llamadas[-1]["imgsz"] == 864
              and abs(r[0, 0] - 700.5) <= 0.1 and abs(r[0, 1] - 400.5) <= 0.1,
              (m.llamadas[-1]["forma"], r.tolist()))

    r = det.detectar(ModeloCentroide(como_tensor=True), imagen_con_punto(10, 20))
    check("acepta tensores (.cpu().numpy())", r.dtype == np.float64 and r[0, 0] == 10.5, r.tolist())

    cajas = [[10.123456, 5.0, 3.0, 3.0], [8.0, 7.0, 3.0, 3.0], [8.0, 2.0, 3.0, 3.0], [50.0, 50.0, 3.0, 3.0]]
    confs = [0.3, 0.5, 0.5, 0.123456789]
    r = det.detectar(ModeloFijo(cajas, confs), np.zeros((100, 100, 3), np.uint8))
    check("orden (−conf, x, y): empates de confianza por x y luego por y",
          r[:, :2].tolist() == [[8.0, 2.0], [8.0, 7.0], [10.123, 5.0], [50.0, 50.0]], r[:, :2].tolist())
    check("redondeo: x a 0,001 px y conf a 0,0001", r[2, 0] == 10.123 and r[3, 4] == 0.1235, r[:, [0, 4]].tolist())
    r = det.detectar(ModeloFijo(np.zeros((0, 4)), np.zeros(0)), np.zeros((100, 100, 3), np.uint8))
    check("sin detecciones: array (0, 5)", r.shape == (0, 5), r.shape)
    muchas = [[float(i), 1.0, 2.0, 2.0] for i in range(15)]
    r = det.detectar(ModeloFijo(muchas, [0.5] * 15), np.zeros((100, 100, 3), np.uint8))
    check("como mucho max_det (10)", len(r) == 10, len(r))


class Malo:
    """Al despicklarse llamaría a os.system. Aquí solo se serializa: nunca se carga."""

    def __reduce__(self):
        return (os.system, ("echo esto no se ejecuta",))


class MaloGetattr:
    def __reduce__(self):
        return (getattr, ("cadena", "upper"))


def zip_con_pickle(carpeta, nombre, datos):
    ruta = os.path.join(carpeta, nombre)
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("archive/data.pkl", datos)
        z.writestr("archive/version", "3\n")
    return ruta


def rechaza(ruta):
    try:
        det.escanear_pickle(ruta)
    except det.ErrorDetector as e:
        return True, str(e)
    return False, "aceptado"


def global_proto2(modulo, nombre):
    """Un pickle de protocolo 2 que solo nombra modulo.nombre (GLOBAL) y lo llama con una cadena."""
    return (b"\x80\x02c" + modulo.encode() + b"\n" + nombre.encode() + b"\nq\x00X\x03\x00\x00\x00abcq\x01\x85q\x02R"
            b"q\x03.")


def global_proto4(modulo, nombre):
    """Un pickle de protocolo 4 con STACK_GLOBAL: módulo y nombre como cadenas en la pila (el nombre puede llevar
    punto: el unpickler de verdad lo resolvería con getattr encadenado)."""
    def cadena(t):
        b = t.encode()
        return b"\x8c" + bytes([len(b)]) + b + b"\x94"
    return b"\x80\x04" + cadena(modulo) + cadena(nombre) + b"\x93\x94\x8c\x03abc\x94\x85\x94R\x94."


def prueba_escaneo():
    print("escanear_pickle")
    import collections
    check("PICKLE_PERMITIDOS: los 29 pares del .pt fijado, sin ningún nombre con punto",
          len(det.PICKLE_PERMITIDOS) == 29 and not any("." in n for _, n in det.PICKLE_PERMITIDOS),
          len(det.PICKLE_PERMITIDOS))
    with tempfile.TemporaryDirectory() as carpeta:
        # Solo nombra collections.OrderedDict y (con el protocolo 2) __builtin__.set: los dos están en la lista.
        inocuo = {"pesos": collections.OrderedDict(a=1.0, b=[1, 2, 3]), "conjunto": {1, 2}, "tupla": (1, 2.5, "x")}
        for proto in (2, 4):
            ruta = zip_con_pickle(carpeta, "inocuo{}.pt".format(proto), pickle.dumps(inocuo, protocol=proto))
            try:
                nombrados = det.escanear_pickle(ruta)
                check("acepta un pickle inocuo (protocolo {})".format(proto), True, nombrados)
            except det.ErrorDetector as e:
                check("acepta un pickle inocuo (protocolo {})".format(proto), False, e)
        for proto in (2, 4):
            ruta = zip_con_pickle(carpeta, "malo{}.pt".format(proto), pickle.dumps({"x": Malo()}, protocol=proto))
            ok, msg = rechaza(ruta)
            check("rechaza os.system (protocolo {}, {})".format(proto, "GLOBAL" if proto == 2 else "STACK_GLOBAL"),
                  ok and "system" in msg, msg)
        ok, msg = rechaza(zip_con_pickle(carpeta, "getattr.pt", pickle.dumps(MaloGetattr(), protocol=4)))
        check("rechaza builtins.getattr", ok and "getattr" in msg, msg)
        ok, msg = rechaza(zip_con_pickle(carpeta, "hub.pt", global_proto2("torch.hub", "load")))
        check("rechaza torch.hub.load aunque empiece por torch", ok and "torch.hub" in msg, msg)
        for modulo, nombre in (("torch", "hub.load"), ("torch", "os.system"), ("torch.utils.collect_env", "run"),
                               ("pathlib", "Path.write_text"), ("numpy.lib", "npyio.load"),
                               ("torch.storage", "_load_from_bytes"), ("ultralytics.utils", "subprocess.run"),
                               ("torch", "Size.__reduce__")):
            ok, msg = rechaza(zip_con_pickle(carpeta, "punto.pt", global_proto4(modulo, nombre)))
            check("rechaza {} + {} (protocolo 4)".format(modulo, nombre), ok, msg)
        ok, msg = rechaza(zip_con_pickle(carpeta, "pathlib.pt", pickle.dumps(__import__("pathlib").PurePosixPath("a"),
                                                                              protocol=4)))
        check("rechaza pathlib (la lista vieja lo dejaba pasar por prefijo)", ok, msg)
        trampa = b"\x80\x02ctorchvision\nx\nq\x00."
        ok, msg = rechaza(zip_con_pickle(carpeta, "prefijo.pt", trampa))
        check("rechaza un módulo que solo empieza por el texto de uno permitido (torchvision)", ok, msg)
        bueno = b"\x80\x02ctorch._utils\n_rebuild_tensor_v2\nq\x00c__builtin__\nset\nq\x01."
        try:
            det.escanear_pickle(zip_con_pickle(carpeta, "bueno.pt", bueno))
            check("acepta torch._utils y __builtin__.set (los del .pt de verdad)", True)
        except det.ErrorDetector as e:
            check("acepta torch._utils y __builtin__.set (los del .pt de verdad)", False, e)
        todos = b"\x80\x02" + b"".join(b"c" + m.encode() + b"\n" + n.encode() + b"\n0"
                                       for m, n in sorted(det.PICKLE_PERMITIDOS)) + b"N."
        try:
            nombrados = det.escanear_pickle(zip_con_pickle(carpeta, "todos.pt", todos))
            check("acepta los 29 pares permitidos", len(nombrados) == 29, len(nombrados))
        except det.ErrorDetector as e:
            check("acepta los 29 pares permitidos", False, e)
        ruta = os.path.join(carpeta, "nozip.pt")
        with open(ruta, "wb") as f:
            f.write(pickle.dumps(inocuo, protocol=2))
        ok, msg = rechaza(ruta)
        check("rechaza un fichero que no es un zip", ok, msg)
        ruta = os.path.join(carpeta, "sinpkl.pt")
        with zipfile.ZipFile(ruta, "w") as z:
            z.writestr("archive/version", "3\n")
        ok, msg = rechaza(ruta)
        check("rechaza un zip sin pickle", ok, msg)
        ok, msg = rechaza(zip_con_pickle(carpeta, "malo_y_bueno.pt", pickle.dumps([inocuo, Malo()], protocol=4)))
        check("rechaza un pickle inocuo con algo malo dentro", ok, msg)


def primero(candidatos, prueba):
    for c in candidatos:
        if c and prueba(c):
            return c
    return None


def prueba_modelo_real():
    print("el modelo de verdad")
    pt = primero(CANDIDATOS_PT, os.path.isfile)
    if pt is None:
        print("  [SALTA] no encuentro el .pt (python validation/balon_video/detector.py --descargar)")
        return
    check("sha256 del .pt = MODELO_SHA256 y tamaño fijado",
          det.sha256_de(pt) == det.MODELO_SHA256 and os.path.getsize(pt) == det.MODELO_BYTES)
    try:
        nombrados = det.escanear_pickle(pt)
        check("el escaneo acepta el .pt de verdad", True, "{} clases o funciones".format(len(nombrados)))
    except det.ErrorDetector as e:
        check("el escaneo acepta el .pt de verdad", False, e)
    import importlib.util
    if importlib.util.find_spec("torch") is None or importlib.util.find_spec("ultralytics") is None:
        print("  [SALTA] detección real: no hay torch o ultralytics en este entorno")
        return
    import torch  # ultralytics no: lo importa `cargar` después de ponerlo sin red
    if cv2 is None:
        print("  [SALTA] detección real: no hay cv2 en este entorno")
        return
    datos = primero(CANDIDATOS_DATASET, lambda c: os.path.isdir(os.path.join(c, "test", "images")))
    if datos is None:
        print("  [SALTA] detección real: no encuentro el dataset abierto (DETECTOR_DATASET)")
        return
    elegidas = []
    for img in sorted(glob.glob(os.path.join(datos, "test", "images", "*.jpg"))):
        etiqueta = os.path.join(datos, "test", "labels", os.path.splitext(os.path.basename(img))[0] + ".txt")
        if os.path.isfile(etiqueta):
            with open(etiqueta) as f:
                filas = [l.split() for l in f if l.strip()]
            if len(filas) == 1:
                elegidas.append((img, [float(v) for v in filas[0][1:5]]))
        if len(elegidas) == 2:
            break
    with tempfile.TemporaryDirectory() as config:
        modelo = det.cargar(pt, hilos=2, carpeta_config=config)
        check("cargar deja torch con 2 hilos", torch.get_num_threads() == 2, torch.get_num_threads())
        for img, (u, v, w, h) in elegidas:
            imagen = cv2.imread(img)
            alto, ancho = imagen.shape[:2]
            r = det.detectar(modelo, imagen, conf=0.10)
            ex, ey = u * ancho, v * alto
            dist = float(np.min(np.hypot(r[:, 0] - ex, r[:, 1] - ey))) if len(r) else np.inf
            tolerancia = max(4.0, w * ancho, h * alto)
            check("detector real en una imagen de test: balón a {:.1f} px de la etiqueta (≤ {:.1f})".format(
                dist, tolerancia), dist <= tolerancia, "{} detecciones".format(len(r)))
        check("después de detectar, torch sigue con 2 hilos", torch.get_num_threads() == 2, torch.get_num_threads())


def main():
    print("Prueba de validation/balon_video/detector.py")
    prueba_campo()
    prueba_detectar()
    prueba_escaneo()
    prueba_modelo_real()
    print("\nTODO BIEN" if not FALLOS else "\nFALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
    return 0 if not FALLOS else 1


if __name__ == "__main__":
    sys.exit(main())
