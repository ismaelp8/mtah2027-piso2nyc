"""Prueba `regenerar.py` (el comando único de la línea del balón del vídeo) sin datos de ningún partido.

    python validation/scripts/prueba_regenerar.py

Lo puede ejecutar cualquiera, Claude incluido. Todo va a una carpeta temporal que no puede caer en `MTAH_DATA_DIR`
(`prueba_pipeline.safe_tmp`): un «partido» de cinco ficheros falsos y una caché inventada, escrita con el escritor de
`validation/partido/balon_video_detectar.py`. El ATD y la homografía son arrays inventados en memoria
(`regenerar.cargar_partido` se cambia por uno falso), y la detección, el pipeline y el validador nunca se lanzan:
`regenerar.ejecutar` se cambia por uno falso que apunta los comandos y escribe lo que escribirían. Comprueba:

- `requirements-detector.txt`: las seis versiones de la línea del vídeo, las mismas que el `pip install` de
  `validation/balon_video/ESTA_NOCHE.md`, y numpy y pandas iguales que en `requirements-entrega.txt`;
- el lector de requirements: solo `paquete==versión`; y la comparación de versiones: la etiqueta local de torch
  (`+cpu`), un paquete que falta o que no es el fijado, dos opencv, otro python, y las versiones que guarda la caché;
- las dos sondas de versiones, de verdad, con este mismo python (la de `detector.versiones()`, solo si hay torch);
- la llave de ahora (`llave_actual`) es la que escribe la detección con el mismo partido;
- la caché: falta (sin leer el partido), vale, parcial, huella falsa, otra variante, otro código, otros hilos, otro
  vídeo, otra lista de frames, otras versiones o un fichero ilegible; los motivos no llevan cifras;
- los comandos: con la capa apagada va con `--capa` y no puede llamarse como la entrega; con ella encendida, sin `--capa`;
  la detección, siempre con `--forzar`;
- `main` de punta a punta, con todo falso: sin caché detecta y genera; con la caché buena no detecta; `--forzar`; una
  caché que no vale; el partido se lee una sola vez; un `--python-detector` relativo; `MTAH_DATA_DIR` absoluta y
  `PYTHONIOENCODING` para los hijos; sin python del detector; un detector o una entrega con otras versiones; un detector
  que guardaría otras versiones en la caché; un fichero del partido que falta; la detección que falla o que no deja una
  caché buena; el pipeline que falla; el validador que falla; un error inesperado que lleva valores, que no se
  imprimen. Y que la salida no lleva valores de la caché.
"""

import contextlib
import hashlib
import importlib.util
import io
import os
import re
import shutil
import sys
import types

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, AQUI)
import regenerar as rg  # noqa: E402
import games  # noqa: E402
from possession import balon_video as bv, pipeline  # noqa: E402
import balon_video_detectar as bvd  # noqa: E402
import detector as det  # noqa: E402
import prueba_pipeline as pp  # noqa: E402  (la carpeta temporal segura)

FALLOS = []
GAME = games.GAME
N = games.GAMES[GAME]["n_video_frames"]
PITCH = tuple(games.GAMES[GAME]["pitch"])
MARCA = 123.456  # un «valor» de la caché inventada: no puede salir en ninguna salida
# Las versiones de las instrucciones del 16/11 (paso 3 de la parte A).
ESPERADAS = {"torch": "2.15.0", "torchvision": "0.29.2", "ultralytics": "8.4.215", "opencv-python": "5.0.0.93",
             "numpy": "2.5.4", "pandas": "3.1.1"}
VERSIONES_CACHE = {"python": "3.13.9", "numpy": "2.5.4", "torch": "2.15.0+cpu", "opencv": "5.0.0",
                   "ultralytics": "8.4.215"}


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def lanza(error, llamada):
    try:
        llamada()
    except error:
        return True
    return False


# -- el partido falso y la caché -------------------------------------------------------------------------------------

def partido_falso(carpeta):
    """Los cinco ficheros del partido, vacíos salvo el «vídeo» (unos bytes, para su huella). Devuelve los paths."""
    paths = games.asset_paths(GAME, carpeta)
    os.makedirs(os.path.dirname(paths["atd_raw"]), exist_ok=True)
    for nombre in rg.FICHEROS:
        with open(paths[nombre], "wb") as f:
            f.write(b"video falso " * 1000 if nombre == "video" else b"")
    return paths


def partido_en_memoria(balon_en=(20004, 20005, 20009, 150004, 150010)):
    """(trk, matrices, validas) inventados con 199.319 frames: el balón del ATD solo en `balon_en` (así la lista de
    frames que se detectan son esos menos 4) y una homografía de escala fija, válida en todos."""
    bx, by = np.full(N, np.nan), np.full(N, np.nan)
    for i, t in enumerate(balon_en):
        bx[t], by[t] = 20.0 + i, 30.0 + 0.5 * i
    trk = types.SimpleNamespace(bx=bx, by=by, pitch=PITCH)
    matrices = np.tile(np.diag([1920.0, 1080.0, 1.0]), (N, 1, 1))
    return trk, matrices, np.ones(N, dtype=bool)


PARTIDO = partido_en_memoria()


def escribir_cache(paths, **cambios):
    """Una caché completa y buena, con el escritor de balon_video_detectar y la llave que escribiría la detección con
    `PARTIDO`; `cambios` la estropea."""
    meta = rg.llave_actual(PARTIDO, paths)
    frames, _, _ = bvd.objetivo(PARTIDO[0], PARTIDO[1], PARTIDO[2], rg.bs.bloques_con_juego(GAME))
    cuantas = [(2, 0, 1)[i % 3] for i in range(len(frames))]
    offsets = np.concatenate(([0], np.cumsum(cuantas))).astype(np.int64)
    valores = np.array([[960.5 + j, 540.5, 4.0, 4.0, 0.81, MARCA, 30.0] for j in range(int(offsets[-1]))],
                       dtype=np.float64).reshape(-1, 7)
    meta["versiones"] = dict(VERSIONES_CACHE, **cambios.get("versiones", {}))
    if "hilos" in cambios:
        meta["hilos"] = cambios["hilos"]
    if "codigo" in cambios:
        meta["codigo_sha256"] = cambios["codigo"]
    if "conf" in cambios:
        meta["variante"]["conf"] = cambios["conf"]
    ruta = bv.ruta_cache(paths)
    huella = cambios.get("huella") or bvd.huella(frames, offsets, valores)
    informativo = {"commit": "abc1234", "cambios_sin_commitear": False,
                   "tiempos_acumulados": {"ejecuciones": 2, "segundos_de_reloj": 12600.0}}
    bvd.guardar(ruta, frames, offsets, valores, meta, informativo, cambios.get("estado", "completo"), huella)
    return bvd.huella(frames, offsets, valores)


def borrar_cache(paths):
    for ruta in (bv.ruta_cache(paths), os.path.join(os.path.dirname(paths["atd_raw"]), bvd.NOMBRE_PARCIAL)):
        if os.path.exists(ruta):
            os.remove(ruta)


# -- las pruebas -----------------------------------------------------------------------------------------------------

def prueba_requirements():
    print("requirements")
    detector = rg.leer_fijadas(rg.REQ_DETECTOR)
    entrega = rg.leer_fijadas(rg.REQ_ENTREGA)
    check("requirements-detector.txt fija exactamente las seis versiones de la línea del vídeo",
          detector == ESPERADAS, detector)
    with open(os.path.join(ROOT, "validation", "balon_video", "ESTA_NOCHE.md"), encoding="utf-8") as f:
        linea = [l for l in f if "pip install torch==" in l and "--index-url" not in l]
    fichas = linea[0].split() if linea else []
    guia = {rg.normalizar(t.split("==")[0]): t.split("==")[1] for t in fichas if "==" in t}
    check("son las mismas que el pip install del paso 4 de ESTA_NOCHE.md", guia == detector, guia)
    check("numpy y pandas, las mismas que en requirements-entrega.txt",
          all(detector[p] == entrega.get(p) for p in ("numpy", "pandas")))
    carpeta = pp.safe_tmp()
    try:
        for malo in ("numpy>=2.5\n", "numpy\n", "numpy==2.5.4 ; python_version>'3'\n", "==2.5.4\n"):
            ruta = os.path.join(carpeta, "req.txt")
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("# un comentario\n\n" + malo)
            check("el lector rechaza «{}»".format(malo.strip()), lanza(rg.ErrorRegenerar, lambda: rg.leer_fijadas(ruta)))
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("Opencv_Python==5.0.0.93  # comentario al final\n")
        check("el lector normaliza el nombre y quita los comentarios",
              rg.leer_fijadas(ruta) == {"opencv-python": "5.0.0.93"})
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def prueba_versiones():
    print("versiones")
    fijadas = dict(ESPERADAS)
    buenas = dict(ESPERADAS, python="3.13.7")
    check("un entorno con las fijadas cuadra", rg.no_cuadran(fijadas, buenas) == [])
    check("torch con «+cpu» cuadra", rg.no_cuadran(fijadas, dict(buenas, torch="2.15.0+cpu")) == [])
    for nombre, vistas in (("otro ultralytics", dict(buenas, ultralytics="8.4.216")),
                           ("torch sin instalar", dict(buenas, torch=None)),
                           ("python 3.12", dict(buenas, python="3.12.9")),
                           ("python 3.14", dict(buenas, python="3.14.0")),
                           ("dos opencv", dict(buenas, **{rg.OPENCV_DUPLICADO: "5.0.0.93"}))):
        malas = rg.no_cuadran(fijadas, vistas)
        check("{}: no cuadra, y lo dice".format(nombre), len(malas) == 1, malas)
    check("las de la caché (det.versiones) cuadran, con torch «+cpu» y opencv sin el cuarto número",
          rg.no_cuadran_en_la_cache(fijadas, VERSIONES_CACHE) == [])
    for clave, valor, paquete in (("opencv", "4.10.0", "opencv-python"), ("opencv", None, "opencv-python"),
                                  ("torch", "2.14.0", "torch"), ("numpy", "2.4.6", "numpy"),
                                  ("python", "3.11.18", "python")):
        malas = rg.no_cuadran_en_la_cache(fijadas, dict(VERSIONES_CACHE, **{clave: valor}))
        check("caché con {} {}: no cuadra ({})".format(clave, valor, paquete), malas == [paquete], malas)
    import platform
    vistas = rg.versiones_de(sys.executable, ["numpy", "un-paquete-que-no-existe"])
    check("la sonda, de verdad con este python: su versión, la de numpy y None si no está",
          vistas == {"python": platform.python_version(), "numpy": np.__version__, "un-paquete-que-no-existe": None},
          vistas)
    check("la sonda con un python que no existe da un error claro",
          lanza(rg.ErrorRegenerar, lambda: rg.versiones_de(os.path.join(ROOT, "no-existe-python"), ["numpy"])))
    if importlib.util.find_spec("torch") is None:
        print("  [SALTA] la sonda de detector.versiones(), de verdad: en este entorno no hay torch")
    else:
        guardaria = rg.versiones_del_detector(sys.executable)
        check("la sonda de detector.versiones(), de verdad: sus cinco claves, y este python y este numpy",
              sorted(guardaria) == sorted(["python", "numpy", "torch", "opencv", "ultralytics"])
              and guardaria["python"] == platform.python_version() and guardaria["numpy"] == np.__version__,
              guardaria)


def detector_falso(imagen, centro):
    """Para `bvd.ejecutar`: una detección en el centro del recorte (la «imagen» es el número de frame)."""
    return np.array([[float(centro[0]), float(centro[1]), 4.0, 4.0, 0.8]])


def fuente_falsa(frames):
    for t in frames:
        yield int(t), int(t)


def prueba_cache(carpeta):
    print("la caché")
    paths = partido_falso(carpeta)
    fijadas = dict(ESPERADAS)
    lecturas = []

    def llave():
        lecturas.append(1)
        return rg.llave_actual(PARTIDO, paths)

    estado = rg.estado_cache(paths, fijadas, llave)
    check("sin caché: falta, y no lee el partido", not estado["vale"] and estado["motivo"] == "falta" and not lecturas)
    # Una caché escrita por la detección de verdad (`bvd.ejecutar`), con la fuente y el detector falsos y la `base` que
    # arma su main.
    base = {"partido": GAME, "modelo_sha256": det.MODELO_SHA256, "versiones": VERSIONES_CACHE, "hilos": det.HILOS,
            "codigo_sha256": bvd.sha256_de_ficheros(bvd.CODIGO), "video": bvd.huella_del_video(paths["video"])}
    res = bvd.ejecutar(PARTIDO[0], PARTIDO[1], PARTIDO[2], rg.bs.bloques_con_juego(GAME), fuente_falsa,
                       detector_falso, os.path.dirname(paths["atd_raw"]), base,
                       {"commit": "abc1234", "cambios_sin_commitear": False})
    check("la llave de ahora (llave_actual) es la que escribe la detección, salvo las versiones",
          bvd.diferencias(res["metadatos"], rg.llave_actual(PARTIDO, paths)) == ["versiones"])
    estado = rg.estado_cache(paths, fijadas, llave)
    check("una caché escrita por la detección vale, con su huella y su informativo",
          estado["vale"] and estado["huella"] == res["huella"] and estado["informativo"]["commit"] == "abc1234",
          estado["motivo"])
    huella = escribir_cache(paths)
    estado = rg.estado_cache(paths, fijadas, llave)
    check("la caché inventada buena vale, con su huella y sus versiones",
          estado["vale"] and estado["huella"] == huella and estado["versiones"] == VERSIONES_CACHE, estado["motivo"])
    casos = (("parcial", {"estado": "parcial"}), ("huella falsa", {"huella": "f" * 64}),
             ("otra confianza", {"conf": 0.25}), ("otro código", {"codigo": "c" * 64}),
             ("otros hilos", {"hilos": det.HILOS + 1}), ("otro torch", {"versiones": {"torch": "2.14.0"}}),
             ("otro python", {"versiones": {"python": "3.12.1"}}))
    for nombre, cambios in casos:
        escribir_cache(paths, **cambios)
        estado = rg.estado_cache(paths, fijadas, llave)
        check("{}: no vale, sin cifras en el motivo".format(nombre),
              not estado["vale"] and not re.search(r"\d", estado["motivo"]), estado["motivo"])
    escribir_cache(paths)
    otro = partido_en_memoria(balon_en=(20004, 20005, 20009, 150004, 150010, 160000))
    estado = rg.estado_cache(paths, fijadas, lambda: rg.llave_actual(otro, paths))
    check("otra lista de frames (un cambio en el ATD, la homografía o el código que la saca): no vale",
          not estado["vale"] and "lista de frames" in estado["motivo"], estado["motivo"])
    with open(paths["video"], "ab") as f:
        f.write(b"otro final")
    estado = rg.estado_cache(paths, fijadas, llave)
    check("otro fichero de vídeo: no vale", not estado["vale"] and "vídeo" in estado["motivo"], estado["motivo"])
    partido_falso(carpeta)
    escribir_cache(paths)
    check("con el vídeo de antes, vuelve a valer", rg.estado_cache(paths, fijadas, llave)["vale"])
    with open(bv.ruta_cache(paths), "wb") as f:
        f.write(b"no es un npz")
    antes = len(lecturas)
    estado = rg.estado_cache(paths, fijadas, llave)
    check("un fichero ilegible: no vale, sin cifras y sin leer el partido",
          not estado["vale"] and not re.search(r"\d", estado["motivo"]) and len(lecturas) == antes, estado["motivo"])
    borrar_cache(paths)


def prueba_comandos():
    print("los comandos")
    original = pipeline.DELIVERY_LAYERS
    try:
        check("hoy la capa está apagada (regenerar no toca DELIVERY_LAYERS)", not rg.capa_encendida())
        cmd = rg.comando_pipeline("x", "/tmp/salida", python="py")
        check("con la capa apagada: el pipeline con --capa {} y --out".format(rg.CAPA),
              cmd == ["py", "-m", "possession.pipeline", "--name", "x", "--out", "/tmp/salida", "--capa", rg.CAPA])
        check("con la capa apagada, el nombre por defecto es el de prueba", rg.nombre_por_defecto() == rg.NOMBRE_PRUEBA)
        check("con la capa apagada, el nombre de la entrega da error",
              lanza(rg.ErrorRegenerar, lambda: rg.comando_pipeline(pipeline.DEFAULT_NAME, "/tmp/salida")))
        check("la capa existe y pipeline la sabe resolver", pipeline.resolve(rg.CAPA, pipeline.LAYER_MODULES,
                                                                              True) is bv.ajuste_b5_video)
        pipeline.DELIVERY_LAYERS = tuple(original) + (bv.ajuste_b5_video,)
        cmd = rg.comando_pipeline(pipeline.DEFAULT_NAME, "/tmp/salida", python="py")
        check("con la capa encendida: sin --capa (daría error) y con el nombre de la entrega",
              "--capa" not in cmd and rg.nombre_por_defecto() == pipeline.DEFAULT_NAME)
    finally:
        pipeline.DELIVERY_LAYERS = original
    check("la detección, siempre con --forzar", rg.comando_deteccion("py") == ["py", rg.DETECCION, "--forzar"])


class Falso:
    """`ejecutar`, las sondas de versiones y `cargar_partido` falsos: apuntan los comandos y las lecturas del partido,
    y escriben lo que escribiría cada comando."""

    def __init__(self, paths, **escenario):
        self.paths, self.escenario, self.comandos, self.lecturas, self.entorno = paths, escenario, [], 0, None

    def cargar_partido(self, data_dir=None, game=GAME):
        self.lecturas += 1
        return PARTIDO

    def versiones_del_detector(self, python):
        return dict(VERSIONES_CACHE, opencv="4.10.0") if self.escenario.get("guardaria_mal") else dict(VERSIONES_CACHE)

    def ejecutar(self, comando, entorno=None):
        self.comandos.append(list(comando))
        self.entorno = entorno
        if comando[1] == rg.DETECCION:
            if self.escenario.get("deteccion_falla"):
                return 1
            escribir_cache(self.paths, **self.escenario.get("cache_tras_detectar", {}))
            return 0
        if comando[1:3] == ["-m", "possession.pipeline"]:
            if self.escenario.get("pipeline_falla"):
                return 1
            carpeta, nombre = comando[comando.index("--out") + 1], comando[comando.index("--name") + 1]
            with open(os.path.join(carpeta, nombre + ".csv"), "w", newline="\n") as f:
                f.write("frame,label\n0,X\n")
            return 0
        if comando[1] == rg.VALIDADOR:
            return self.escenario.get("validador", 0)
        raise AssertionError("un comando inesperado")

    def versiones_de(self, python, paquetes):
        vistas = {"python": "3.13.7"}
        vistas.update({p: ESPERADAS.get(p) for p in paquetes})
        vistas.update({"python-dateutil": "4.0.0", "tzdata": "2026.6"} if python == sys.executable else {})
        if python != sys.executable and self.escenario.get("detector_mal"):
            vistas["torch"] = "2.14.0"
        if python == sys.executable and self.escenario.get("entrega_mal"):
            vistas["numpy"] = "2.4.6"
        return {p: vistas.get(p) for p in ["python"] + list(paquetes)}

    def lanzados(self, que):
        return [c for c in self.comandos if (c[1] == rg.DETECCION if que == "deteccion" else
                                             c[1:3] == ["-m", "possession.pipeline"] if que == "pipeline" else
                                             c[1] == rg.VALIDADOR)]


def correr(paths, carpeta, argv, **escenario):
    """`regenerar.cli` con todo falso. Devuelve (código, salida, falso)."""
    falso = Falso(paths, **escenario)
    nombres = ("ejecutar", "versiones_de", "versiones_del_detector", "cargar_partido", "main")
    originales = {n: getattr(rg, n) for n in nombres}
    for n in nombres[:-1]:
        setattr(rg, n, getattr(falso, n))
    rg.main = lambda argv_=None: originales["main"](argv_, data_dir=carpeta)
    salida = io.StringIO()
    try:
        with contextlib.redirect_stdout(salida):
            codigo = rg.cli(argv)
    finally:
        for n, f in originales.items():
            setattr(rg, n, f)
    return codigo, salida.getvalue(), falso


def prueba_main(carpeta):
    print("main, de punta a punta con todo falso")
    paths = partido_falso(carpeta)
    salidas = os.path.join(carpeta, "salidas")
    os.makedirs(salidas)
    py_det = os.path.join(carpeta, "python-del-detector")  # existe, pero nunca se lanza (ejecutar es falso)
    with open(py_det, "w") as f:
        f.write("")
    base = ["--python-detector", py_det, "--out", salidas]
    os.environ.pop("MTAH_PYTHON_DETECTOR", None)
    todas = []

    borrar_cache(paths)
    codigo, salida, falso = correr(paths, carpeta, base)
    todas.append(salida)
    det_ = falso.lanzados("deteccion")
    csv = os.path.join(salidas, rg.NOMBRE_PRUEBA + ".csv")
    with open(csv, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    huella = rg.estado_cache(paths, dict(ESPERADAS), lambda: rg.llave_actual(PARTIDO, paths))["huella"]
    check("sin caché: detecta (con --forzar), genera con --capa y valida; código 0",
          codigo == 0 and det_ == [[py_det, rg.DETECCION, "--forzar"]] and len(falso.lanzados("pipeline")) == 1
          and rg.CAPA in falso.lanzados("pipeline")[0] and len(falso.lanzados("validador")) == 1, codigo)
    check("sin caché: lee el partido una sola vez, después de detectar", falso.lecturas == 1, falso.lecturas)
    completos = "huella {}".format(huella) in salida and "sha256: {}".format(sha) in salida
    check("el resumen trae la huella de la caché y el sha256 de la entrega, enteros", completos,
          "" if completos else salida[-400:])
    check("el resumen trae las versiones de los dos entornos",
          "entorno de la entrega: python 3.13.7, numpy 2.5.4" in salida and "torch 2.15.0+cpu" in salida)
    check("los hijos reciben MTAH_DATA_DIR absoluta (la carpeta de los datos) y PYTHONIOENCODING=utf-8",
          falso.entorno is not None and falso.entorno.get("MTAH_DATA_DIR") == os.path.abspath(carpeta)
          and falso.entorno.get("PYTHONIOENCODING") == "utf-8")

    codigo, salida, falso = correr(paths, carpeta, base)
    todas.append(salida)
    check("con la caché buena: no detecta, pero genera y valida; lee el partido una vez",
          codigo == 0 and not falso.lanzados("deteccion") and len(falso.lanzados("pipeline")) == 1
          and "no hace falta detectar" in salida and falso.lecturas == 1)
    codigo, salida, falso = correr(paths, carpeta, ["--out", salidas])
    todas.append(salida)
    check("con la caché buena no hace falta el python del detector", codigo == 0 and not falso.lanzados("deteccion"))

    codigo, salida, falso = correr(paths, carpeta, base + ["--forzar"])
    todas.append(salida)
    check("--forzar: detecta con --forzar aunque la caché valga, y lee el partido una sola vez",
          codigo == 0 and falso.lanzados("deteccion") == [[py_det, rg.DETECCION, "--forzar"]]
          and falso.lecturas == 1)

    check("sin parcial: ni al usar la caché ni al detectar sale el aviso del parcial",
          not any("AVISO" in s for s in todas))
    parcial = os.path.join(os.path.dirname(paths["atd_raw"]), bvd.NOMBRE_PARCIAL)
    with open(parcial, "w") as f:  # un --forzar que se cortó: el parcial queda junto a la caché de antes
        f.write("")
    codigo, salida, falso = correr(paths, carpeta, base)
    todas.append(salida)
    check("la caché vale y hay un parcial (un --forzar cortado): no detecta, y lo avisa dos veces, la segunda en el "
          "resumen", codigo == 0 and not falso.lanzados("deteccion") and salida.count(rg.AVISO_PARCIAL) == 2
          and salida.index("## Resumen") < salida.rindex(rg.AVISO_PARCIAL)
          and "detección en este comando: no" in salida)
    codigo, salida, falso = correr(paths, carpeta, base + ["--forzar"])
    todas.append(salida)
    check("con el parcial y --forzar: detecta, sin aviso, y el resumen dice que ha detectado",
          codigo == 0 and len(falso.lanzados("deteccion")) == 1 and "AVISO" not in salida
          and "detección en este comando: sí" in salida)
    os.remove(parcial)

    escribir_cache(paths, estado="parcial")
    codigo, salida, falso = correr(paths, carpeta, base)
    todas.append(salida)
    check("una caché que no vale: detecta con --forzar (si no, la detección se niega a pisarla)",
          codigo == 0 and falso.lanzados("deteccion") == [[py_det, rg.DETECCION, "--forzar"]])

    borrar_cache(paths)
    relativo = os.path.relpath(py_det)
    codigo, salida, falso = correr(paths, carpeta, ["--python-detector", relativo, "--out", salidas])
    todas.append(salida)
    check("un --python-detector relativo se lanza con su ruta absoluta",
          codigo == 0 and falso.lanzados("deteccion") == [[os.path.abspath(relativo), rg.DETECCION, "--forzar"]])

    for nombre, argv, escenario, antes_de_detectar in (
            ("sin python del detector", ["--out", salidas], {}, True),
            ("con un python del detector que no existe", ["--python-detector", os.path.join(carpeta, "no"),
                                                          "--out", salidas], {}, True),
            ("con otro torch en el entorno del detector", base, {"detector_mal": True}, True),
            ("con un detector que guardaría otras versiones en la caché", base, {"guardaria_mal": True}, True),
            ("con otro numpy en el entorno de la entrega", base, {"entrega_mal": True}, True),
            ("con la detección que falla", base, {"deteccion_falla": True}, False),
            ("con la detección que deja una caché que no vale", base,
             {"cache_tras_detectar": {"codigo": "d" * 64}}, False),
            ("con el pipeline que falla", base, {"pipeline_falla": True}, False)):
        borrar_cache(paths)
        codigo, salida, falso = correr(paths, carpeta, argv, **escenario)
        todas.append(salida)
        llega = not falso.lanzados("deteccion") if antes_de_detectar else True
        sin_entrega = "pipeline" in nombre or not falso.lanzados("pipeline")
        check("{}: código 1, ERROR claro y {}".format(nombre, "nada lanzado" if antes_de_detectar
                                                      else "sin entrega ni sha256"),
              codigo == 1 and "ERROR:" in salida and llega and sin_entrega and "sha256:" not in salida,
              salida.strip().splitlines()[-1] if salida.strip() else "")

    borrar_cache(paths)
    os.remove(paths["smart_tagging"])
    codigo, salida, falso = correr(paths, carpeta, base)
    todas.append(salida)
    check("sin el Smart Tagging: error antes de detectar (el pipeline lo pide)",
          codigo == 1 and not falso.comandos and "smart_tagging" in salida)
    partido_falso(carpeta)

    escribir_cache(paths)
    codigo, salida, falso = correr(paths, carpeta, base, validador=1)
    todas.append(salida)
    check("el validador que falla: código 1 y lo dice el resumen", codigo == 1 and "validador: FALLA" in salida)

    codigo, salida, falso = correr(paths, carpeta, base + ["--name", pipeline.DEFAULT_NAME])
    todas.append(salida)
    check("con la capa apagada, --name {}: error antes de nada".format(pipeline.DEFAULT_NAME),
          codigo == 1 and not falso.comandos)

    original = rg.estado_cache
    rg.estado_cache = lambda *a, **k: (_ for _ in ()).throw(ValueError("valor {}".format(MARCA)))
    try:
        codigo, salida, falso = correr(paths, carpeta, base)
    finally:
        rg.estado_cache = original
    todas.append(salida)
    check("un error inesperado: solo el tipo y las líneas, sin su mensaje",
          codigo == 1 and "ValueError" in salida and str(MARCA) not in salida, salida.strip().splitlines()[-1])
    check("ninguna salida lleva valores de la caché", not any(str(MARCA) in s for s in todas))
    borrar_cache(paths)


def main():
    print("Prueba de regenerar.py")
    pesados = [m for m in ("torch", "cv2", "ultralytics") if m in sys.modules]
    check("regenerar.py se importa sin torch, opencv ni ultralytics (corre en el entorno de la entrega)",
          not pesados, pesados)
    carpeta = pp.safe_tmp()
    try:
        prueba_requirements()
        prueba_versiones()
        prueba_cache(carpeta)
        prueba_comandos()
        prueba_main(carpeta)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    print("\nTODO BIEN" if not FALLOS else "\nFALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
    return 0 if not FALLOS else 1


if __name__ == "__main__":
    sys.exit(main())
