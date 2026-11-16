"""El comando único que regenera la entrega con la línea del balón del vídeo: la detección, si hace falta, y el pipeline.

**Lee el partido: lo ejecuta una persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`). Imprime solo
agregados: versiones, el commit, la huella de la caché de detecciones, la salida de los scripts que llama (también solo
agregados) y el sha256 de la entrega. La prueba sin datos es `validation/scripts/prueba_regenerar.py`, y cómo se
reproduce, en `validation/balon_video/BITACORA.md` («Cómo se reproduce»).

Se ejecuta desde la raíz del repo con el python del **entorno de la entrega** (`requirements-entrega.txt`), y se le
dice cuál es el del **entorno del detector** (`requirements-detector.txt`):

    <entorno de la entrega>/bin/python regenerar.py --python-detector <entorno del detector>/bin/python
    <entorno de la entrega>/bin/python regenerar.py --python-detector ... --name <NOMBRE_EQUIPO>
    <entorno de la entrega>/bin/python regenerar.py --python-detector ... --forzar     # rehace la detección

En Windows, el python de un entorno es `<entorno>\\Scripts\\python.exe`. `--python-detector` también puede ir en la
variable de entorno `MTAH_PYTHON_DETECTOR`, y solo hace falta si hay que detectar.

Qué hace, en orden. Todo lo que puede fallar va antes de las horas de detección:

1. Comprueba el entorno de la entrega: Python 3.13 y las versiones exactas de `requirements-entrega.txt`.
2. Comprueba que están los cinco ficheros del partido: vídeo, ATD, sus metadatos, homografía y Smart Tagging.
3. Comprueba la caché de la detección, `MTAH_DATA_DIR/tactical/BAR-ATH_tactical_balon_video.npz` (`estado_cache`).
   Vale si:
   - existe, está completa, es de este partido y de la variante fijada, y su huella cuadra con sus arrays: lo mismo
     que comprueba la capa al leerla (`possession.balon_video.leer_cache`);
   - su llave es la que escribiría la detección ahora (`llave_actual`): el mismo código que detecta, los mismos hilos,
     el mismo fichero de vídeo y la misma lista de frames y centros de los recortes, recalculada con el ATD y la
     homografía y el código de la detección (un par de minutos). Así ve también un cambio en `bloques_con_juego`, en
     `dead_ball.pre_kickoff`, en el lector del ATD o en el de la homografía;
   - las versiones que guarda son las de `requirements-detector.txt`.
4. Si no vale, o con `--forzar`:
   - comprueba el entorno del detector de dos formas: las versiones exactas de los paquetes de
     `requirements-detector.txt` (y un solo opencv), y las que guardaría en la caché (`detector.versiones()`), con la
     misma función con que después se comprueba la caché. Si esto pasa, la caché no se puede rechazar luego por
     versiones;
   - lanza `validation/partido/balon_video_detectar.py` con ese python, siempre con `--forzar`: este comando ya ha
     decidido que la caché no vale, así que se pisa al acabar y se tira un parcial de otra configuración. Un parcial
     de la misma configuración se reanuda igual: si se corta, relanzar `regenerar.py` sigue donde se quedó (guarda un
     parcial cada 5.000 frames);
   - al acabar, vuelve a comprobar la caché.
   Si no detecta y junto a la caché hay un parcial (un `--forzar` que se cortó), lo avisa aquí y en el resumen: la
   caché que usa es la de antes, no una recién hecha.
5. El pipeline: `python -m possession.pipeline --name <nombre> --capa balon_video.ajuste_b5_video`. Si la capa ya está
   en `pipeline.DELIVERY_LAYERS` (encendida), va sin `--capa`, que entonces daría error.
6. El validador oficial sobre el CSV escrito.
7. Un resumen: las versiones de los dos entornos, el commit, la huella de la caché, el sha256 de la entrega y los
   tiempos.

Los procesos hijos reciben `MTAH_DATA_DIR` como ruta absoluta (la misma carpeta que mira este comando) y
`PYTHONIOENCODING=utf-8`, para que un log redirigido a un fichero no mezcle codificaciones en Windows.

El nombre por defecto es `regenerada_balon_video` mientras la capa está apagada (una entrega de prueba no puede llevar
el nombre de la entrega) y `pipeline.DEFAULT_NAME` cuando esté encendida. Este comando no toca `pipeline.py` ni
`DELIVERY_LAYERS`: encender la capa lo decide el equipo con la puerta 2.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import warnings

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "validation", "partido"))
import games  # noqa: E402
from possession import balon_video, pipeline, tracking  # noqa: E402
import balon_video_detectar as bvd  # noqa: E402  (pone validation/balon_video en la ruta)
import balon_video_sondeo as bs  # noqa: E402
import detector as det  # noqa: E402

REQ_ENTREGA = os.path.join(RAIZ, "requirements-entrega.txt")
REQ_DETECTOR = os.path.join(RAIZ, "requirements-detector.txt")
PYTHON_FIJADO = "3.13"  # el de los dos entornos (requirements-entrega.txt: numpy 2.5.4 pide 3.12 o más)
CAPA = "balon_video.ajuste_b5_video"
NOMBRE_PRUEBA = "regenerada_balon_video"
DETECCION = os.path.join("validation", "partido", "balon_video_detectar.py")
VALIDADOR = os.path.join("evaluation", "validate_submission.py")
FICHEROS = ("video", "atd_meta", "atd_raw", "homography", "smart_tagging")
OPENCV_DUPLICADO = "opencv-python-headless"  # ultralytics arrastra opencv-python; si están los dos, se pisan
# Lo que decide la detección, además de lo que imprime `possession.pipeline` (sus DELIVERY_CODE): solo para la línea
# del commit. Con barras normales: git las entiende también en Windows.
CODIGO = ("regenerar.py", "requirements-detector.txt", "validation/balon_video/detector.py",
          "validation/partido/balon_video_detectar.py", "validation/partido/balon_video_sondeo.py")
# Las versiones que guarda la caché (`detector.versiones()`) y su paquete en requirements-detector.txt.
EN_LA_CACHE = {"numpy": "numpy", "torch": "torch", "ultralytics": "ultralytics", "opencv": "opencv-python"}
# Las claves de la llave de la caché (`balon_video_detectar.metadatos_de`), dichas sin cifras.
QUE_ES = {"formato": "el formato", "partido": "el partido", "frames_del_video": "los frames del vídeo",
          "campo": "el campo", "modelo_sha256": "el modelo", "variante": "la variante", "hilos": "los hilos",
          "codigo_sha256": "el código que detecta", "columnas": "las columnas",
          "objetivo": "la lista de frames que se detectan", "video": "el fichero de vídeo"}


class ErrorRegenerar(Exception):
    """Un error con un mensaje sin datos del partido (se puede imprimir tal cual)."""


# -- versiones -------------------------------------------------------------------------------------------------------

def normalizar(nombre):
    """El nombre de un paquete como lo compara pip: minúsculas y `-` en vez de `_` o `.`."""
    return re.sub(r"[-_.]+", "-", nombre.strip()).lower()


def leer_fijadas(ruta):
    """{paquete: versión} de un requirements con solo líneas `paquete==versión` y comentarios. Si no, error."""
    fijadas = {}
    with open(ruta, encoding="utf-8") as f:
        for numero, linea in enumerate(f, 1):
            linea = linea.split("#", 1)[0].strip()
            if not linea:
                continue
            nombre, separador, version = linea.partition("==")
            version = version.strip()
            if not separador or not nombre.strip() or not version or re.search(r"[<>=!~,;\s]", version):
                raise ErrorRegenerar("{}, línea {}: solo vale «paquete==versión»".format(os.path.basename(ruta),
                                                                                         numero))
            fijadas[normalizar(nombre)] = version
    return fijadas


def sin_local(version):
    """La versión sin la etiqueta local (PEP 440): el torch de la web de PyTorch dice «2.15.0+cpu»."""
    return None if version is None else str(version).split("+", 1)[0]


def mismo_python(version, fijado=PYTHON_FIJADO):
    return version is not None and str(version).split(".")[:2] == fijado.split(".")


# Se ejecuta con `python -I -c`: no importa ningún paquete (solo lee sus metadatos), así que tarda poco aunque esté torch.
SONDA = """import importlib.metadata as m, json, platform, sys
def version(nombre):
    try:
        return m.version(nombre)
    except m.PackageNotFoundError:
        return None
print(json.dumps(dict([("python", platform.python_version())] + [(n, version(n)) for n in sys.argv[1:]])))
"""
# Las versiones como las guardaría la detección en la caché: `detector.versiones()` (importa torch y cv2; segundos).
SONDA_DETECTOR = """import json, sys
sys.path.insert(0, sys.argv[1])
import detector
print(json.dumps(detector.versiones()))
"""


def _sondear(python, argumentos):
    try:
        r = subprocess.run([python, "-I", "-c"] + list(argumentos), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=300)
        if r.returncode:
            raise ErrorRegenerar("no puedo preguntar sus versiones a {}".format(python))
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        raise ErrorRegenerar("no puedo preguntar sus versiones a {}".format(python)) from None


def versiones_de(python, paquetes):
    """{"python": "3.13.7", paquete: versión o None} del entorno de `python`, por los metadatos de los paquetes."""
    return _sondear(python, [SONDA] + list(paquetes))


def versiones_del_detector(python):
    """Lo que guardaría la detección en la caché con el entorno de `python`: `detector.versiones()`."""
    return _sondear(python, [SONDA_DETECTOR, os.path.join(RAIZ, "validation", "balon_video")])


def no_cuadran(fijadas, vistas, fijado=PYTHON_FIJADO):
    """Lo que no cuadra de un entorno (`versiones_de`) con lo fijado: textos con lo visto y lo fijado."""
    malas = []
    if not mismo_python(vistas.get("python"), fijado):
        malas.append("python {} (se fija {})".format(vistas.get("python"), fijado))
    for paquete, version in sorted(fijadas.items()):
        if sin_local(vistas.get(paquete)) != version:
            malas.append("{} {} (se fija {})".format(paquete, vistas.get(paquete) or "sin instalar", version))
    if vistas.get(OPENCV_DUPLICADO) is not None:
        malas.append("también está {}: deja solo opencv-python".format(OPENCV_DUPLICADO))
    return malas


def no_cuadran_en_la_cache(fijadas, versiones, fijado=PYTHON_FIJADO):
    """Los paquetes cuya versión, como la guarda la caché (`detector.versiones()`), no es la fijada. Solo nombres."""
    malas = [] if mismo_python(versiones.get("python"), fijado) else ["python"]
    for clave, paquete in sorted(EN_LA_CACHE.items()):
        if paquete not in fijadas:
            continue
        vista, fijada = sin_local(versiones.get(clave)), fijadas[paquete]
        if clave == "opencv":
            # cv2.__version__ no lleva el cuarto número del paquete: 5.0.0 para opencv-python 5.0.0.93 (medido en
            # macOS el 16/11 con `detector.py --comprobar`).
            bien = vista is not None and fijada.split(".")[:3] == vista.split(".")
        else:
            bien = vista == fijada
        if not bien:
            malas.append(paquete)
    return malas


def texto(versiones):
    """«python 3.13.7, numpy 2.5.4, …», con python delante."""
    claves = ["python"] + [k for k in versiones if k not in ("python", OPENCV_DUPLICADO)]
    return ", ".join("{} {}".format(k, versiones.get(k) or "sin instalar") for k in claves)


# -- el código, el partido y la caché --------------------------------------------------------------------------------

def estado_del_codigo(rutas=CODIGO):
    """«commit X, sin cambios locales …» de este comando y del código que detecta; o «sin git»."""
    def git(*args):
        return subprocess.run(["git", "-C", RAIZ] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=30)
    try:
        cabeza = git("rev-parse", "--short", "HEAD")
        local = git("status", "--porcelain", "--", *rutas)
    except (OSError, subprocess.SubprocessError):
        return "código de la detección y de este comando: sin git"
    if cabeza.returncode or local.returncode:
        return "código de la detección y de este comando: sin git"
    return "código de la detección y de este comando: commit {}, {}".format(
        cabeza.stdout.strip(), "CON CAMBIOS SIN COMMITEAR" if local.stdout.strip() else "sin cambios locales")


def cargar_partido(data_dir=None, game=games.GAME):
    """(trk, matrices, validas): el ATD y la homografía del partido, leídos como los lee la detección. Lee datos del
    partido: solo lo ejecuta una persona (un par de minutos)."""
    from starter import load_homography  # aquí: pandas solo hace falta si se lee el partido
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        trk = tracking.from_atd(games.asset_paths(game, data_dir), game)
        matrices, _, validas = load_homography.load(game, data_dir)
    return trk, matrices, validas


def llave_actual(partido, paths, game=games.GAME):
    """La llave que escribiría la detección ahora (`balon_video_detectar.metadatos_de`), salvo las versiones, que se
    comparan aparte con las fijadas. Con el mismo código que la detección: la lista de frames de `objetivo` sobre
    `bloques_con_juego`, el sha256 del código que detecta, los hilos, el modelo fijado y la huella del vídeo."""
    trk, matrices, validas = partido
    frames, centros, _ = bvd.objetivo(trk, matrices, validas, bs.bloques_con_juego(game))
    return bvd.metadatos_de(game, len(trk.bx), trk.pitch, det.MODELO_SHA256, None, det.HILOS,
                            bvd.sha256_de_ficheros(bvd.CODIGO), frames, centros,
                            video=bvd.huella_del_video(paths["video"]))


def estado_cache(paths, fijadas_detector, llave_de_ahora, game=games.GAME):
    """{"vale", "motivo", "huella", "versiones", "informativo"} de la caché de la detección. Sin valores ni cifras.

    `paths`: los de `games.asset_paths`; la caché va junto al ATD (`balon_video.ruta_cache`). `llave_de_ahora()`
    devuelve `llave_actual`: solo se llama si la caché existe y la capa la leería, porque lee el partido."""
    ruta = balon_video.ruta_cache(paths)
    estado = {"vale": False, "motivo": None, "huella": None, "versiones": None, "informativo": None}
    if not os.path.isfile(ruta):
        return dict(estado, motivo="falta")
    info = games.GAMES[game]
    try:
        # Lo mismo que hará la capa en el pipeline: si aquí vale, allí también.
        balon_video.leer_cache(ruta, info["n_video_frames"], info["pitch"], game)
        cache = bvd.leer(ruta)
    except (balon_video.ErrorCache, bvd.ErrorDeteccion) as e:
        return dict(estado, motivo=str(e))
    meta = cache["metadatos"]
    distinto = [QUE_ES.get(clave, "otra clave de la llave")
                for clave in bvd.diferencias(meta, llave_de_ahora()) if clave != "versiones"]
    paquetes = no_cuadran_en_la_cache(fijadas_detector, meta.get("versiones") or {})
    if paquetes:
        distinto.append("las versiones del detector ({})".format(", ".join(paquetes)))
    estado.update(huella=cache["huella"], versiones=meta.get("versiones"), informativo=cache["informativo"])
    if distinto:
        return dict(estado, motivo="es de otra configuración; cambia {}".format(", ".join(distinto)))
    return dict(estado, vale=True, motivo="vale")


def hay_parcial(paths):
    """Si junto a la caché hay una detección a medias: el parcial de `balon_video_detectar`. Solo mira si existe."""
    return os.path.isfile(bvd.rutas_cache(os.path.dirname(balon_video.ruta_cache(paths)))[1])


AVISO_PARCIAL = ("AVISO: junto a la caché hay una detección a medias (un parcial): una ejecución con --forzar se "
                 "cortó. Este comando NO ha detectado: usa la caché que ya había. Para acabar aquella detección, "
                 "relánzalo con --forzar (sigue desde el parcial).")


# -- los comandos ----------------------------------------------------------------------------------------------------

def capa_encendida():
    """Si la capa del balón del vídeo ya va en la entrega (`pipeline.DELIVERY_LAYERS`)."""
    return balon_video.ajuste_b5_video in pipeline.DELIVERY_LAYERS


def nombre_por_defecto():
    return pipeline.DEFAULT_NAME if capa_encendida() else NOMBRE_PRUEBA


def comando_pipeline(nombre, carpeta, python=None):
    """El pipeline con la capa: con `--capa` si está apagada; sin él si ya va en DELIVERY_LAYERS."""
    comando = [python or sys.executable, "-m", "possession.pipeline", "--name", nombre, "--out", carpeta]
    if not capa_encendida():
        if nombre == pipeline.DEFAULT_NAME:
            raise ErrorRegenerar("con la capa apagada, esto es una entrega de prueba y no puede llamarse {}: usa "
                                 "otro --name".format(pipeline.DEFAULT_NAME))
        comando += ["--capa", CAPA]
    return comando


def comando_deteccion(python):
    """Siempre con `--forzar`: pisa la caché que no vale y tira un parcial de otra configuración; uno de la misma se
    reanuda igual (`balon_video_detectar.reanudacion`)."""
    return [python, DETECCION, "--forzar"]


def ejecutar(comando, entorno=None):
    """Un comando desde la raíz del repo, con su salida directa a la consola. Devuelve su código de salida."""
    sys.stdout.flush()
    return subprocess.call(comando, cwd=RAIZ, env=entorno)


def titulo(texto_):
    print("\n## {}\n".format(texto_), flush=True)


def horas(segundos):
    return "{:.2f} h".format(segundos / 3600.0) if segundos >= 3600 else "{:.1f} min".format(segundos / 60.0)


# -- el comando ------------------------------------------------------------------------------------------------------

def main(argv=None, data_dir=None):
    """`data_dir` es para la prueba sin datos; en uso normal, None (MTAH_DATA_DIR, como el pipeline)."""
    reloj = time.perf_counter()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--python-detector", default=os.environ.get("MTAH_PYTHON_DETECTOR"),
                    help="el python del entorno del detector (requirements-detector.txt); solo hace falta si hay que "
                         "detectar. Por defecto, MTAH_PYTHON_DETECTOR")
    ap.add_argument("--name", default=None, help="nombre del CSV, sin extensión (por defecto {} con la capa apagada y "
                                                 "{} con ella encendida)".format(NOMBRE_PRUEBA, pipeline.DEFAULT_NAME))
    ap.add_argument("--out", default=pipeline.RESULTS_DIR, help="carpeta del CSV (por defecto evaluation/results)")
    ap.add_argument("--forzar", action="store_true", help="rehace la detección aunque la caché valga")
    args = ap.parse_args(argv)
    nombre = args.name or nombre_por_defecto()
    carpeta = os.path.abspath(args.out)
    # Los hijos miran la misma carpeta de datos que este comando, aunque MTAH_DATA_DIR sea relativa.
    entorno = dict(os.environ, MTAH_DATA_DIR=os.path.abspath(data_dir or games.DATA_DIR), PYTHONIOENCODING="utf-8")
    cmd_pipeline = comando_pipeline(nombre, carpeta)  # un --name que no vale, antes de nada

    titulo("Regenerar la entrega con el balón del vídeo")
    print("capa del balón del vídeo: {}".format("encendida (va en DELIVERY_LAYERS)" if capa_encendida()
                                                 else "apagada: va con --capa, en una entrega de prueba"))
    print(estado_del_codigo())
    fijadas_entrega, fijadas_detector = leer_fijadas(REQ_ENTREGA), leer_fijadas(REQ_DETECTOR)
    vistas_entrega = versiones_de(sys.executable, sorted(fijadas_entrega))
    print("entorno de la entrega: {}".format(texto(vistas_entrega)))
    malas = no_cuadran(fijadas_entrega, vistas_entrega)
    if malas:
        raise ErrorRegenerar("el entorno de la entrega no es el fijado (requirements-entrega.txt): {}".format(
            "; ".join(malas)))

    paths = games.asset_paths(games.GAME, data_dir)
    faltan = [nombre_ for nombre_ in FICHEROS if not os.path.isfile(paths[nombre_])]
    if faltan:
        raise ErrorRegenerar("faltan ficheros del partido ({}): revisa que MTAH_DATA_DIR apunte a la carpeta de los "
                             "datos".format(", ".join(faltan)))

    llave = {}

    def llave_de_ahora():
        """`llave_actual`, una sola vez por ejecución (lee el ATD y la homografía)."""
        if "valor" not in llave:
            print("leyendo el ATD y la homografía para recalcular la lista de frames de la caché (un par de minutos)",
                  flush=True)
            llave["valor"] = llave_actual(cargar_partido(data_dir), paths)
        return llave["valor"]

    cache = estado_cache(paths, fijadas_detector, llave_de_ahora)
    print("caché de la detección: {}".format(cache["motivo"]))
    tiempos = {}
    versiones_detector, de_donde = cache["versiones"], "las de la caché"
    if args.forzar or not cache["vale"]:
        if not args.python_detector:
            raise ErrorRegenerar("hay que detectar y no sé con qué python: pasa --python-detector con el python del "
                                 "entorno del detector (o ponlo en MTAH_PYTHON_DETECTOR)")
        python_detector = os.path.abspath(os.path.expanduser(args.python_detector))
        if not os.path.isfile(python_detector):
            raise ErrorRegenerar("no encuentro el python del detector: {}".format(python_detector))
        vistas_detector = versiones_de(python_detector, sorted(fijadas_detector) + [OPENCV_DUPLICADO])
        print("entorno del detector: {}".format(texto(vistas_detector)))
        malas = no_cuadran(fijadas_detector, vistas_detector)
        if malas:
            raise ErrorRegenerar("el entorno del detector no es el fijado (requirements-detector.txt): {}".format(
                "; ".join(malas)))
        guardaria = versiones_del_detector(python_detector)
        malas = no_cuadran_en_la_cache(fijadas_detector, guardaria)
        if malas:
            raise ErrorRegenerar("la detección guardaría en la caché unas versiones que no son las fijadas ({}): la "
                                 "caché no valdría".format(", ".join(malas)))
        titulo("1. La detección del balón en el vídeo (horas; si se corta, relanza este mismo comando y sigue donde "
               "se quedó)")
        inicio = time.perf_counter()
        codigo = ejecutar(comando_deteccion(python_detector), entorno)
        tiempos["detección"] = time.perf_counter() - inicio
        if codigo:
            raise ErrorRegenerar("la detección ha fallado (código de salida {}). Mira el ERROR de arriba; si se cortó, "
                                 "relanza este mismo comando: sigue desde el último parcial".format(codigo))
        cache = estado_cache(paths, fijadas_detector, llave_de_ahora)
        if not cache["vale"]:
            raise ErrorRegenerar("la detección ha acabado, pero la caché no vale: {}".format(cache["motivo"]))
        print("\ncaché de la detección: vale")
        versiones_detector, de_donde = cache["versiones"], "las de la caché, recién hecha"
    else:
        print("no hace falta detectar (con --forzar se rehace)")
    # Un --forzar cortado deja un parcial junto a la caché de antes, que sigue valiendo: sin este aviso, relanzar sin
    # --forzar daría la caché vieja por recién hecha (la «segunda ejecución» de la puerta 2.3 no compararía nada).
    aviso = AVISO_PARCIAL if "detección" not in tiempos and hay_parcial(paths) else None
    if aviso:
        print(aviso)

    titulo("2. La entrega")
    inicio = time.perf_counter()
    codigo = ejecutar(cmd_pipeline, entorno)
    tiempos["entrega"] = time.perf_counter() - inicio
    ruta = os.path.join(carpeta, nombre + ".csv")
    if codigo or not os.path.isfile(ruta):
        raise ErrorRegenerar("el pipeline ha fallado (código de salida {}): no hay entrega".format(codigo))
    sha = pipeline.sha256(ruta)

    titulo("3. El validador oficial")
    validador = ejecutar([sys.executable, VALIDADOR, ruta], entorno)

    titulo("Resumen")
    print("entorno de la entrega: {}".format(texto(vistas_entrega)))
    print("entorno del detector ({}): {}".format(de_donde, texto(versiones_detector or {})))
    print(estado_del_codigo())
    informativo = cache["informativo"] or {}
    acumulados = informativo.get("tiempos_acumulados") or {}
    print("caché de la detección: huella {}".format(cache["huella"]))
    print("  detectada con el commit {}{}; {} ejecuciones, {} de reloj en total".format(
        informativo.get("commit"), " (con cambios sin commitear)" if informativo.get("cambios_sin_commitear") else "",
        acumulados.get("ejecuciones"), horas(float(acumulados.get("segundos_de_reloj") or 0.0))))
    print("entrega: {}".format(pipeline.shown(ruta)))
    print("sha256: {}".format(sha))
    print("validador: {}".format("OK" if validador == 0 else "FALLA (código de salida {})".format(validador)))
    print("detección en este comando: {}".format("sí, {}".format(horas(tiempos["detección"])) if "detección" in tiempos
                                                  else "no: se ha usado la caché que ya había"))
    if aviso:
        print(aviso)
    print("tiempo de este comando: {}; en total, {}".format(
        "; ".join("{}, {}".format(k, horas(v)) for k, v in tiempos.items()), horas(time.perf_counter() - reloj)))
    return 0 if validador == 0 else 1


def cli(argv=None):
    """`main` con los errores sin valores: los nuestros con su mensaje; cualquier otro, solo el tipo y las líneas."""
    try:
        return main(argv)
    except ErrorRegenerar as e:
        print("\nERROR: {}".format(e))
        return 1
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print("\n" + bs.informe_de_error(e))
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(cli())
