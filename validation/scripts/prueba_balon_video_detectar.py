"""Prueba `validation/partido/balon_video_detectar.py` (la detección del partido entero) sin datos de ningún partido.

    python validation/scripts/prueba_balon_video_detectar.py

Lo puede ejecutar cualquiera, Claude incluido. Todo es inventado y va a carpetas temporales (nunca a MTAH_DATA_DIR):

- un partido de 3.000 frames con dos tramos: el balón «de verdad» va y viene; el ATD lo da con 4 frames de retraso, con
  un hueco y con unos frames fuera del campo; unos pocos frames tienen la homografía no válida;
- una homografía con paneo (cambia con el frame: proyectar con la de otro frame se nota);
- una fuente de frames inventada cuya «imagen» lleva el píxel del balón, y un detector falso que mira el contenido de
  la imagen (si la imagen no es la de su frame, la detección sale en otro sitio), comprueba el centro del recorte,
  falla a bloques, añade una detección lejana y empates;
- si hay cv2, un MP4 diminuto con el número de frame pintado, leído con `detector.leer_frames` de verdad.

Comprueba: la lista de frames y sus centros; el formato de la caché (arrays, tipos, columnas, metros con la inversa
de la homografía, metadatos, estado, huella); que la huella es determinista y canónica; cortar a mitad y reanudar da la
misma huella y los mismos arrays, y el lector arranca donde toca, también con --forzar; el parcial se borra al acabar;
los tiempos se acumulan entre reanudaciones (fuera de la llave y de la huella); un parcial de otra llave (hilos,
versiones, modelo, código, ATD o vídeo) da error sin --forzar y no se toca, y con --forzar se tira; un parcial que no es
el principio de la lista no reanuda; la escritura es atómica y reintenta `os.replace`; los agregados salen del código
del sondeo (`medir`) y coinciden con medirlo en vivo, con `propio_pasa` del D propio; `main` de punta a punta con todo
falso (la caché ya hecha, --resumen, --forzar cortado y relanzado, una carpeta sin permiso de escritura, un error con
valores que no se imprimen, la reanudación); y que la salida solo lleva agregados y el stderr solo pasos sin cifras y
porcentajes.
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import types

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import games  # noqa: E402
import balon_video_detectar as bvd  # noqa: E402
import balon_video_sondeo as bs  # noqa: E402
import detector as det  # noqa: E402  (balon_video_detectar ya pone validation/balon_video en la ruta)
from possession.tracking import Tracking  # noqa: E402

try:
    import cv2
except ImportError:
    cv2 = None

FALLOS = []
LARGO, ANCHO = 105.3, 68.0
N = 3000
BLOQUES = ((101, 1451), (1601, 2951))
ADELANTO = 4
A_X, B_X, Y_BALON = 40.0, 48.0, 30.0
PASO = 0.4
HUECO = (701, 741)
FUERA = (1201, 1211)  # frames del ATD con el balón a 1 m fuera del campo (finito)
SIN_HOMOGRAFIA = (300, 303)  # frames sin homografía válida
H_AFIN = np.array([[1500.0, 0.0, 200.0], [0.0, 800.0, 150.0], [0.0, 0.0, 1.0]])
SX = 1500.0 / LARGO
CADA = 200
BASE = {"partido": games.GAME, "modelo_sha256": det.MODELO_SHA256, "versiones": {"python": "falso", "numpy": "falso"},
        "hilos": 4, "codigo_sha256": "c" * 64}
INFO = {"commit": "abc1234", "cambios_sin_commitear": False}


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def carpeta_segura():
    """Carpeta temporal para los ficheros inventados. Se niega a usar la de los datos del partido."""
    carpeta = os.path.realpath(tempfile.mkdtemp(prefix="mtah_prueba_detectar_"))
    datos = os.path.realpath(games.DATA_DIR)
    if carpeta == datos or carpeta.startswith(datos + os.sep) or "mtah2027-data" in carpeta.lower():
        raise SystemExit("la carpeta temporal cae dentro de los datos del partido: no se ejecuta")
    return carpeta


# -- el partido inventado --------------------------------------------------------------------------------------------

def balon_de_verdad():
    periodo = int(round(2 * (B_X - A_X) / PASO))
    fase = np.arange(N) % periodo
    mitad = periodo // 2
    x = np.where(fase <= mitad, A_X + PASO * fase, B_X - PASO * (fase - mitad))
    return x, np.full(N, Y_BALON), periodo


def partido(semilla=0):
    """(trk, matrices, validas). El ATD es el balón de verdad con 4 frames de retraso; `semilla` mueve a los
    jugadores y el paneo (para comparar dos partidos inventados distintos)."""
    vx, vy, periodo = balon_de_verdad()
    bx, by = np.full(N, np.nan), np.full(N, np.nan)
    bx[ADELANTO:], by[ADELANTO:] = vx[:-ADELANTO], vy[:-ADELANTO]
    bx[HUECO[0]:HUECO[1]] = by[HUECO[0]:HUECO[1]] = np.nan
    by[FUERA[0] + ADELANTO:FUERA[1] + ADELANTO] = -1.0
    fase = np.arange(N) % periodo
    cerca_a = np.minimum(fase, periodo - fase) <= 2
    cerca_b = np.abs(fase - periodo // 2) <= 2
    px = np.column_stack([np.full(N, A_X), np.full(N, B_X), np.full(N, 80.0 + semilla)])
    py = np.column_stack([np.where(cerca_a, Y_BALON, Y_BALON + 10.0), np.where(cerca_b, Y_BALON, Y_BALON + 10.0),
                          np.full(N, 50.0)])
    trk = Tracking(bx, by, px, py, np.array([0, 1, 0], dtype=np.int8), (LARGO, ANCHO), BLOQUES, 25)
    matrices = np.repeat(H_AFIN[None], N, axis=0)
    matrices[:, 0, 2] += (40.0 + semilla) * np.sin(2 * np.pi * np.arange(N) / 97.0)
    validas = np.ones(N, dtype=bool)
    validas[SIN_HOMOGRAFIA[0]:SIN_HOMOGRAFIA[1]] = False
    matrices[~validas] = np.nan
    return trk, matrices, validas


def pixel_pintado(trk, matrices, t):
    """El píxel del balón del ATD en t+4 pintado con la homografía del frame t (o None)."""
    s = t + ADELANTO
    if s >= N or not np.isfinite(trk.bx[s]) or not np.isfinite(matrices[t]).all():
        return None
    x, y = det.pixeles_desde_campo(matrices[t], trk.bx[s], trk.by[s], LARGO, ANCHO)
    return float(np.floor(x)) + 0.5, float(np.floor(y)) + 0.5


def fuente_falsa(trk, matrices, registro=None):
    """abrir_fuente(frames): (t, imagen) con la imagen = [t, x, y] del píxel pintado. Apunta el primer frame pedido."""
    def abrir(frames):
        frames = [int(f) for f in frames]
        if registro is not None:
            registro.append(frames[0] if frames else None)
        for t in frames:
            p = pixel_pintado(trk, matrices, t)
            yield t, np.array([t, np.nan, np.nan] if p is None else [t, p[0], p[1]], dtype=np.float64)
    return abrir


def detector_falso(trk, matrices, cortar_en=None, error=RuntimeError("corte"), salida=5):
    """Detector que mira la imagen: una [t, x, y] o un frame de vídeo con el número pintado (`leer_indice`).

    Falla en los frames con (t // 37) % 5 == 0; cada 7 frames añade una detección a 200 px (lejos); cada 11, un empate
    de confianza a 2 px. Comprueba que el centro del recorte cae en el balón pintado. `cortar_en`: en esa llamada lanza
    `error` (un corte a mitad)."""
    estado = {"llamadas": 0}

    def detectar(imagen, centro):
        estado["llamadas"] += 1
        if cortar_en is not None and estado["llamadas"] == cortar_en:
            raise error
        imagen = np.asarray(imagen)
        if imagen.ndim == 3:
            t = leer_indice(imagen)
            p = pixel_pintado(trk, matrices, t)
            x0, y0 = (np.nan, np.nan) if p is None else p
        else:
            t, x0, y0 = int(imagen[0]), float(imagen[1]), float(imagen[2])
        if not np.isfinite(x0):
            return np.zeros((0, salida))
        if np.hypot(centro[0] - x0, centro[1] - y0) > 1.0:
            raise AssertionError("el centro del recorte no está en el balón")
        if (t // 37) % 5 == 0:
            return np.zeros((0, salida))
        filas = [[x0, y0, 4.0, 4.0, 0.8]]
        if t % 7 == 0:
            filas.append([x0 + 200.0, y0, 4.0, 4.0, 0.3])
        if t % 11 == 0:
            filas.append([x0 + 2.0, y0, 4.0, 4.0, 0.8])
        filas = np.array(filas)
        return filas if salida == 5 else filas[:, [0, 1, 4]]
    return detectar, estado


BITS, ANCHO_VIDEO, ALTO_VIDEO = 12, 128, 48


def pintar_indice(i):
    img = np.zeros((ALTO_VIDEO, ANCHO_VIDEO, 3), dtype=np.uint8)
    for b in range(BITS):
        if (i >> b) & 1:
            img[8:40, b * 10 + 2:b * 10 + 9] = 255
    return img


def leer_indice(img):
    return sum(1 << b for b in range(BITS) if img[24, b * 10 + 5].mean() > 127)


def correr(carpeta, trk, matrices, validas, detector=None, registro=None, base=BASE, forzar=False, abrir=None):
    detector = detector or detector_falso(trk, matrices)[0]
    pasos = []
    res = bvd.ejecutar(trk, matrices, validas, BLOQUES, abrir or fuente_falsa(trk, matrices, registro), detector,
                       carpeta, base, INFO, forzar=forzar, cada=CADA, paso=pasos.append)
    res["pasos"] = pasos
    return res


# -- pruebas ---------------------------------------------------------------------------------------------------------

def prueba_constantes():
    print("constantes y nombres")
    check("la variante fijada (320 px, ×2, confianza 0,10, 4 hilos, adelanto 4)",
          (det.LADO, det.FACTOR, det.CONF, det.HILOS, bvd.BALL_LEAD) == (320, 2, 0.10, 4, 4))
    check("la caché, el parcial y el temporal empiezan por BAR-ATH_tactical_ (los bloquea settings.json)",
          all(n.startswith("BAR-ATH_tactical_") for n in (bvd.NOMBRE_CACHE, bvd.NOMBRE_PARCIAL,
                                                          bvd.NOMBRE_CACHE + bvd.SUFIJO_TEMPORAL)))
    with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as f:
        ajustes = f.read()
    check("settings.json bloquea BAR-ATH_tactical* en cualquier carpeta", "BAR-ATH_tactical*" in ajustes)
    check("cada 5.000 frames un parcial", bvd.CADA == 5000)


def prueba_objetivo():
    print("la lista de frames")
    trk, matrices, validas = partido()
    frames, centros, recuento = bvd.objetivo(trk, matrices, validas, BLOQUES)
    esperado = [t for a, b in BLOQUES for t in range(a, b)
                if t + ADELANTO < N and np.isfinite(trk.bx[t + ADELANTO]) and validas[t]]
    check("frames de los tramos con balón del ATD en t+4 (también fuera del campo) y homografía válida",
          frames.tolist() == esperado, (len(frames), len(esperado)))
    check("incluye los frames con el balón del ATD fuera del campo", all(t in set(frames.tolist())
                                                                         for t in range(*FUERA)))
    check("el recuento: frames de los tramos, con balón del ATD en t+4 y fuera por la homografía",
          recuento["en_los_tramos_con_juego"] == sum(b - a for a, b in BLOQUES)
          and recuento["fuera_por_homografia_no_valida"] == SIN_HOMOGRAFIA[1] - SIN_HOMOGRAFIA[0]
          and recuento["con_balon_del_atd_en_t_mas_4"] == len(esperado) + recuento["fuera_por_homografia_no_valida"],
          recuento)
    ok = all(np.allclose(centros[i], det.pixeles_desde_campo(matrices[t], trk.bx[t + 4], trk.by[t + 4], LARGO, ANCHO),
                         rtol=0, atol=0) for i, t in enumerate(frames.tolist()[:300]))
    check("los centros son la proyección del ATD en t+4 con la homografía de t", ok)


def prueba_cache_y_huella(carpeta):
    print("la caché: formato, huella y determinismo")
    trk, matrices, validas = partido()
    a, b = os.path.join(carpeta, "a"), os.path.join(carpeta, "b")
    os.makedirs(a)
    os.makedirs(b)
    detector, estado = detector_falso(trk, matrices)
    ra = correr(a, trk, matrices, validas, detector)
    final, parcial = bvd.rutas_cache(a)
    check("escribe la caché y no deja ni parcial ni temporal", os.path.isfile(final) and not os.path.exists(parcial)
          and not os.path.exists(final + bvd.SUFIJO_TEMPORAL), sorted(os.listdir(a)))
    frames, _, _ = bvd.objetivo(trk, matrices, validas, BLOQUES)
    check("el detector se llama una vez por frame de la lista", estado["llamadas"] == len(frames))
    with np.load(final, allow_pickle=False) as z:
        claves = sorted(z.files)
        tipos = {k: str(z[k].dtype) for k in ("frames", "offsets", "valores")}
    check("claves: frames, offsets, valores, metadatos, informativo, estado y huella (sin pickle)",
          claves == sorted(["frames", "offsets", "valores", "metadatos", "informativo", "estado", "huella"]), claves)
    check("tipos int64, int64 y float64", tipos == {"frames": "int64", "offsets": "int64", "valores": "float64"}, tipos)
    c = bvd.leer(final)
    check("frames = la lista; offsets de m+1; valores (k, 7)", np.array_equal(c["frames"], frames)
          and len(c["offsets"]) == len(frames) + 1 and c["valores"].shape == (c["offsets"][-1], 7))
    # Lo guardado frame a frame, contra lo que devuelve el detector.
    det2, _ = detector_falso(trk, matrices)
    bien = True
    for i, t in enumerate(frames.tolist()):
        p = pixel_pintado(trk, matrices, t)
        esperado = det2(np.array([t, p[0], p[1]]), p)
        filas = c["valores"][c["offsets"][i]:c["offsets"][i + 1]]
        if len(filas) != len(esperado) or not np.array_equal(filas[:, :5], esperado):
            bien = False
            break
        if len(filas):
            fx, fy = det.campo_desde_pixeles(matrices[t], esperado[:, 0], esperado[:, 1], LARGO, ANCHO)
            if not (np.array_equal(filas[:, 5], np.round(fx, 6)) and np.array_equal(filas[:, 6], np.round(fy, 6))):
                bien = False
                break
    check("todas las detecciones de cada frame, en píxeles y en metros (inversa de la homografía de ese frame)", bien)
    vx, _, _ = balon_de_verdad()
    elegidas = c["valores"][c["offsets"][:-1][np.diff(c["offsets"]) > 0]]
    t_con = c["frames"][np.diff(c["offsets"]) > 0]
    dentro = (t_con < FUERA[0]) | (t_con >= FUERA[1])
    check("la primera detección, en metros, cae en el balón de verdad (a menos de 1 px)",
          np.max(np.abs(elegidas[dentro, 5] - vx[t_con[dentro]])) < 1.0 / SX * 1.01)
    m = c["metadatos"]
    check("metadatos: modelo, variante, hilos, versiones, código y lista", m["modelo_sha256"] == det.MODELO_SHA256
          and m["variante"]["recorte_px"] == 320 and m["variante"]["factor"] == 2.0 and m["variante"]["conf"] == 0.10
          and m["variante"]["adelanto_atd"] == 4 and m["hilos"] == 4 and m["versiones"] == BASE["versiones"]
          and m["codigo_sha256"] == BASE["codigo_sha256"] and m["objetivo"]["frames"] == len(frames)
          and m["columnas"] == list(bvd.COLUMNAS) and m["frames_del_video"] == N, m)
    ta = c["informativo"].get("tiempos_acumulados", {})
    check("informativo: el commit y los tiempos acumulados (fuera de la llave)",
          all(c["informativo"].get(k) == v for k, v in INFO.items()) and ta.get("ejecuciones") == 1
          and ta.get("frames_procesados") == len(frames)
          and all(k in ta for k in ("segundos_detectando", "segundos_leyendo_video", "segundos_de_reloj"))
          and "tiempos_acumulados" not in c["metadatos"], c["informativo"])
    check("estado «completo» y huella = la de sus arrays", c["estado"] == "completo"
          and c["huella"] == bvd.huella(c["frames"], c["offsets"], c["valores"]) == ra["huella"])
    rb = correr(b, trk, matrices, validas)
    cb = bvd.leer(bvd.rutas_cache(b)[0])
    check("determinista: otra ejecución da la misma huella y los mismos arrays", rb["huella"] == ra["huella"]
          and all(np.array_equal(c[k], cb[k]) for k in ("frames", "offsets", "valores")))
    # Huella canónica.
    f, o, v = c["frames"], c["offsets"], c["valores"].copy()
    v2 = v.copy()
    v2[0, 0] = 1.0
    check("la huella cambia si cambia un valor", bvd.huella(f, o, v2) != ra["huella"])
    v3, v4 = np.zeros((2, 7)), np.zeros((2, 7))
    v4[0, 0] = -0.0
    v3[1, 1] = np.nan
    v4[1, 1] = np.frombuffer(np.array([0x7ff8000000000001], dtype="<u8").tobytes(), dtype="<f8")[0]
    o2 = np.array([0, 2])
    check("la huella no distingue −0,0 de 0,0 ni un NaN de otro", bvd.huella([5], o2, v3) == bvd.huella([5], o2, v4))
    check("la huella no depende del tipo de entrada (int32 frente a int64)",
          bvd.huella(f.astype(np.int32), o, v) == ra["huella"])
    big = v.astype(">f8")
    check("la huella no depende del orden de bytes", bvd.huella(f, o, big) == ra["huella"])
    return ra


def prueba_reanudar(carpeta, ref):
    print("cortar a mitad y reanudar")
    trk, matrices, validas = partido()
    frames, _, _ = bvd.objetivo(trk, matrices, validas, BLOQUES)
    c = os.path.join(carpeta, "c")
    os.makedirs(c)
    final, parcial = bvd.rutas_cache(c)
    corte = 1234  # no es múltiplo de CADA
    detector, _ = detector_falso(trk, matrices, cortar_en=corte)
    try:
        correr(c, trk, matrices, validas, detector)
        check("el corte se propaga", False)
    except RuntimeError:
        check("el corte se propaga", True)
    hechos = (corte - 1) // CADA * CADA
    p = bvd.leer(parcial) if os.path.exists(parcial) else None
    check("queda el parcial del último múltiplo de CADA, marcado «parcial», y no hay caché ni temporal",
          p is not None and len(p["frames"]) == hechos and p["estado"] == "parcial" and not os.path.exists(final)
          and not os.path.exists(parcial + bvd.SUFIJO_TEMPORAL), None if p is None else len(p["frames"]))
    # Un segundo corte, ya reanudado.
    corte2 = 777
    detector, _ = detector_falso(trk, matrices, cortar_en=corte2)
    registro = []
    try:
        correr(c, trk, matrices, validas, detector, registro=registro)
    except RuntimeError:
        pass
    p2 = bvd.leer(parcial)
    check("un segundo corte, ya reanudado: el parcial sigue creciendo", len(p2["frames"]) ==
          (hechos + corte2 - 1) // CADA * CADA and registro == [int(frames[hechos])], (len(p2["frames"]), registro))
    detector, estado = detector_falso(trk, matrices)
    registro = []
    r = correr(c, trk, matrices, validas, detector, registro=registro)
    k0 = len(p2["frames"])
    check("reanuda: el lector arranca en el primer frame que falta y el detector solo ve lo que falta",
          r["reanudado_desde"] == k0 and registro == [int(frames[k0])] and estado["llamadas"] == len(frames) - k0
          and r["nota"] == "reanuda desde el parcial", (r["reanudado_desde"], registro, estado["llamadas"], r["nota"]))
    cr = bvd.leer(final)
    check("misma huella y mismos arrays que la ejecución de un tirón", r["huella"] == ref["huella"]
          and all(np.array_equal(cr[k], ref[k]) for k in ("frames", "offsets", "valores")))
    check("al acabar borra el parcial", not os.path.exists(parcial))
    ta = cr["informativo"]["tiempos_acumulados"]
    check("los tiempos se acumulan entre las tres ejecuciones (frames de todas, sin contar dos veces)",
          ta["ejecuciones"] == 3 and ta["frames_procesados"] == len(frames) and r["tiempos_acumulados"] == ta, ta)
    check("y la última ejecución va aparte (solo sus frames)", cr["informativo"]["ultima_ejecucion"]
          ["frames_procesados"] == len(frames) - k0, cr["informativo"]["ultima_ejecucion"])
    # --forzar cortado y relanzado con --forzar: reanuda (la caché final de antes no se toca hasta acabar).
    antes = open(final, "rb").read()
    detector, _ = detector_falso(trk, matrices, cortar_en=650)
    try:
        correr(c, trk, matrices, validas, detector, forzar=True)
    except RuntimeError:
        pass
    check("un --forzar cortado deja el parcial y la caché de antes intacta", os.path.exists(parcial)
          and open(final, "rb").read() == antes)
    k1 = len(bvd.leer(parcial)["frames"])
    detector, estado = detector_falso(trk, matrices)
    r = correr(c, trk, matrices, validas, detector, forzar=True)
    check("relanzado con --forzar: reanuda desde el parcial y da la huella de referencia",
          r["reanudado_desde"] == k1 > 0 and estado["llamadas"] == len(frames) - k1 and r["huella"] == ref["huella"]
          and r["nota"] == "reanuda desde el parcial" and not os.path.exists(parcial),
          (r["reanudado_desde"], r["nota"]))


def prueba_no_reanudar(carpeta, ref):
    print("lo que no reanuda")
    trk, matrices, validas = partido()
    frames, _, _ = bvd.objetivo(trk, matrices, validas, BLOQUES)
    video = {"bytes": 123, "sha256_primer_mib": "a" * 64, "sha256_ultimo_mib": "b" * 64}
    casos = [("otros hilos", dict(BASE, hilos=2), "hilos"),
             ("otras versiones", dict(BASE, versiones={"python": "otro"}), "versiones"),
             ("otro modelo", dict(BASE, modelo_sha256="0" * 64), "modelo_sha256"),
             ("otro código", dict(BASE, codigo_sha256="d" * 64), "codigo_sha256"),
             ("otro vídeo", dict(BASE, video=video), "video")]
    for nombre, base, clave in casos:
        d = os.path.join(carpeta, "nr_" + nombre.replace(" ", "_"))
        os.makedirs(d)
        try:
            correr(d, trk, matrices, validas, detector_falso(trk, matrices, cortar_en=650)[0], base=base)
        except RuntimeError:
            pass
        parcial = bvd.rutas_cache(d)[1]
        guardado = open(parcial, "rb").read()
        detector, estado = detector_falso(trk, matrices)
        try:
            correr(d, trk, matrices, validas, detector)
            check("{}: sin --forzar, error".format(nombre), False)
        except bvd.ErrorDeteccion as e:
            check("{}: sin --forzar, error que dice qué clave difiere (sin valores) y el parcial no se toca".format(
                nombre), clave in str(e) and "--forzar" in str(e)
                and not re.search(r"\d", str(e).replace("sha256", ""))
                and estado["llamadas"] == 0 and open(parcial, "rb").read() == guardado, str(e))
        detector, estado = detector_falso(trk, matrices)
        r = correr(d, trk, matrices, validas, detector, forzar=True)
        check("{}: con --forzar, lo tira, empieza de cero y la huella es la misma".format(nombre),
              r["reanudado_desde"] == 0 and estado["llamadas"] == len(frames) and "otra configuración" in r["nota"]
              and r["huella"] == ref["huella"] and not os.path.exists(parcial), r["nota"])
    # Otra lista de frames (otro ATD): no reanuda.
    d = os.path.join(carpeta, "nr_lista")
    os.makedirs(d)
    otro, _, _ = partido()
    bx = np.array(otro.bx)
    bx[1000:1010] = np.nan
    otro = otro._replace(bx=bx)
    try:
        correr(d, otro, matrices, validas, detector_falso(otro, matrices, cortar_en=650)[0])
    except RuntimeError:
        pass
    try:
        correr(d, trk, matrices, validas)
        check("otro ATD (otra lista): sin --forzar, error", False)
    except bvd.ErrorDeteccion as e:
        check("otro ATD (otra lista): sin --forzar, error que nombra «objetivo»", "objetivo" in str(e), str(e))
    r = correr(d, trk, matrices, validas, forzar=True)
    check("otro ATD (otra lista): con --forzar, empieza de cero", r["reanudado_desde"] == 0
          and "objetivo" in r["nota"] and r["huella"] == ref["huella"], r["nota"])
    # Un parcial cuyos frames no son el principio de la lista (con la misma llave).
    d = os.path.join(carpeta, "nr_prefijo")
    os.makedirs(d)
    meta = bvd.metadatos_de(BASE["partido"], N, trk.pitch, BASE["modelo_sha256"], BASE["versiones"], BASE["hilos"],
                            BASE["codigo_sha256"], frames, bvd.objetivo(trk, matrices, validas, BLOQUES)[1])
    malos = frames[1:201]
    bvd.guardar(bvd.rutas_cache(d)[1], malos, np.zeros(201, dtype=np.int64), np.zeros((0, 7)), meta, INFO, "parcial")
    r = correr(d, trk, matrices, validas)
    check("un parcial que no es el principio de la lista: de cero", r["reanudado_desde"] == 0
          and "principio" in r["nota"] and r["huella"] == ref["huella"], r["nota"])
    # Un parcial ilegible.
    d = os.path.join(carpeta, "nr_roto")
    os.makedirs(d)
    with open(bvd.rutas_cache(d)[1], "wb") as f:
        f.write(b"no es un npz")
    r = correr(d, trk, matrices, validas)
    check("un parcial ilegible: de cero", r["reanudado_desde"] == 0 and "no se puede leer" in r["nota"], r["nota"])
    # --forzar con un parcial de la misma llave: reanuda (no lo tira).
    d = os.path.join(carpeta, "nr_forzar")
    os.makedirs(d)
    try:
        correr(d, trk, matrices, validas, detector_falso(trk, matrices, cortar_en=650)[0])
    except RuntimeError:
        pass
    detector, estado = detector_falso(trk, matrices)
    r = correr(d, trk, matrices, validas, detector, forzar=True)
    check("--forzar con un parcial de la misma configuración: lo reanuda y da la misma huella",
          r["reanudado_desde"] == 600 and estado["llamadas"] == len(frames) - 600 and r["huella"] == ref["huella"],
          (r["reanudado_desde"], r["nota"]))


def prueba_atomica(carpeta, ref):
    print("escritura atómica")
    d = os.path.join(carpeta, "atomica")
    os.makedirs(d)
    ruta = os.path.join(d, bvd.NOMBRE_CACHE)
    bvd.guardar(ruta, ref["frames"], ref["offsets"], ref["valores"], ref["metadatos"], INFO, "completo", ref["huella"])
    antes = open(ruta, "rb").read()
    real = np.savez

    def savez_que_falla(f, **arrays):
        f.write(b"medio fichero")
        raise OSError("disco lleno")
    np.savez = savez_que_falla
    try:
        bvd.guardar(ruta, ref["frames"][:3], ref["offsets"][:4], ref["valores"][:ref["offsets"][3]], ref["metadatos"],
                    INFO, "completo", "x")
        check("si la escritura falla, error", False)
    except OSError:
        check("si la escritura falla, error", True)
    finally:
        np.savez = real
    check("y la caché de antes sigue intacta, sin temporal", open(ruta, "rb").read() == antes
          and not os.path.exists(ruta + bvd.SUFIJO_TEMPORAL))
    # os.replace bloqueado un momento (Windows: antivirus o indexador): reintenta y acaba bien.
    real_replace, real_remove = os.replace, os.remove
    intentos = {"n": 0}

    def replace_que_falla_una_vez(a, b):
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise PermissionError(13, "bloqueado")
        return real_replace(a, b)
    otro = os.path.join(d, bvd.NOMBRE_PARCIAL)
    with parches([(os, "replace", replace_que_falla_una_vez), (bvd, "ESPERA_REEMPLAZO", 0.0)]):
        bvd.guardar(otro, ref["frames"], ref["offsets"], ref["valores"], ref["metadatos"], INFO, "parcial")
    check("os.replace falla una vez con PermissionError: reintenta y la escritura acaba bien",
          intentos["n"] == 2 and bvd.leer(otro)["estado"] == "parcial"
          and not os.path.exists(otro + bvd.SUFIJO_TEMPORAL))

    def replace_que_falla_siempre(a, b):
        raise PermissionError(13, "bloqueado siempre")

    def remove_que_falla(r):
        raise PermissionError(13, "no se puede borrar")
    with parches([(os, "replace", replace_que_falla_siempre), (os, "remove", remove_que_falla),
                  (bvd, "ESPERA_REEMPLAZO", 0.0)]):
        try:
            bvd.guardar(ruta, ref["frames"][:3], ref["offsets"][:4], ref["valores"][:ref["offsets"][3]],
                        ref["metadatos"], INFO, "completo", "x")
            check("os.replace falla siempre: error", False)
        except PermissionError as e:
            check("os.replace falla siempre: sale SU error (no el del borrado del temporal) y la caché sigue intacta",
                  "bloqueado siempre" in str(e) and open(ruta, "rb").read() == antes, str(e))
    real_remove(ruta + bvd.SUFIJO_TEMPORAL)


def cond5_falsa(propio_desde=None):
    """La condición 5 inventada: pasa con el D de las etiquetas desde p = 0,7; con `propio_desde`, cada celda trae
    también el D propio, que pasa desde esa p (sin él, las celdas no lo traen)."""
    rej = {"p": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0], "sigma": [0.03, 0.06, 0.12, 0.25], "L": [1, 12, 50]}
    celdas = {}
    for p in rej["p"]:
        for s in rej["sigma"]:
            for l in rej["L"]:
                celdas[(p, s, l)] = {"p": p, "sigma": s, "L": l,
                                     "racha_de_fallos_media_real": 1.0 / p if l == 1 else float(l),
                                     "oraculo": {"veredicto": {"pasa": p >= 0.7}}}
                if propio_desde is not None:
                    celdas[(p, s, l)]["propio"] = {"veredicto": {"pasa": p >= propio_desde}}
    return {"rejilla": rej, "celdas": celdas, "temblor_dfl": {0.03: 0.095, 0.06: 0.18, 0.12: 0.35, 0.25: 0.73}}


def prueba_agregados(ref):
    print("agregados: el código del sondeo, alimentado con la caché")
    trk, matrices, validas = partido()
    cond5 = cond5_falsa()
    agg = bvd.agregados(trk, matrices, validas, BLOQUES, ref["frames"], ref["offsets"], ref["valores"], cond5)
    # En vivo: medir con el detector falso (x, y, conf) sobre los mismos frames.
    detector, _ = detector_falso(trk, matrices, salida=3)

    def en_vivo(imagen, centro):
        return detector(imagen, centro)
    fuente = (t_img for t_img in fuente_falsa(trk, matrices)([t for a, b in BLOQUES for t in range(a, b)]))
    vivo = bs.medir(fuente, trk, matrices, validas, en_vivo, list(BLOQUES), roi=True, cond5=cond5)
    v = vivo["veredictos"]
    check("condiciones 1 y 2: las mismas que midiendo en vivo",
          agg["condicion_1_pct_frames_con_deteccion_a_3m"] == v["condicion_1"]
          and agg["condicion_2_pct_detecciones_a_mas_de_5m"] == v["condicion_2"],
          (agg["condicion_1_pct_frames_con_deteccion_a_3m"], v["condicion_1"]))
    check("temblor, rachas y toques: los mismos que en vivo", agg["temblor_y_rachas"] == vivo["medidas_de_la_condicion_5"]
          and agg["toques_descriptivos"]["toques_por_minuto_del_detector"]
          == v["condicion_3_descriptiva"]["toques_por_minuto_del_detector"])
    c5 = agg["condicion_5_descriptiva"]
    check("la condición 5 leída con leer_condicion_5 (la misma celda que en vivo) y marcada descriptiva",
          c5["celda"] == v["condicion_5"]["celda"] and c5["cumple"] == v["condicion_5"]["cumple"]
          and "descriptiva" in c5["nota"] and c5["celda"] is not None, c5)
    esperado_c1 = None
    base = [t for a, b in BLOQUES for t in range(a, b) if t + 4 < N and np.isfinite(trk.bx[t + 4])
            and 0 <= trk.by[t + 4] <= ANCHO and validas[t]]
    aciertos = sum(1 for t in base if (t // 37) % 5 != 0)
    esperado_c1 = (aciertos, len(base))
    check("condición 1: los frames que no fallan entre los de balón del ATD dentro del campo",
          (v["condicion_1"]["aciertos"], v["condicion_1"]["frames"]) == esperado_c1, esperado_c1)
    lejos = sum(1 for t in base if (t // 37) % 5 != 0 and t % 7 == 0)
    check("condición 2: las detecciones a 200 px cuentan como lejos", v["condicion_2"]["lejos"] == lejos,
          (v["condicion_2"]["lejos"], lejos))
    check("sin «global» (el SIGUE del sondeo no aplica aquí)", "global" not in json.dumps(agg))
    check("una emulación sin el D propio: propio_pasa es None (no rompe tras horas de detección)",
          c5["propio_pasa"] is None, c5.get("propio_pasa"))
    # La celda leída (p = 0,8 con el detector falso) pasa con un D y no con el otro.
    p_leida = c5["celda"]["p"]
    for desde, esperado in ((p_leida + 0.05, False), (p_leida, True)):
        agg2 = bvd.agregados(trk, matrices, validas, BLOQUES, ref["frames"], ref["offsets"], ref["valores"],
                             cond5_falsa(propio_desde=desde))
        c52 = agg2["condicion_5_descriptiva"]
        check("la celda pasa con el D de las etiquetas y {} con el propio: cumple True y propio_pasa {}".format(
            "también" if esperado else "no", esperado), c52["cumple"] is True and c52["propio_pasa"] is esperado
            and "propio_pasa" in c52["nota"], (c52["cumple"], c52["propio_pasa"]))
    check("propio_pasa: sin celda o sin emulación, None", bvd.propio_pasa(None, {"p": 0.7, "sigma": 0.03, "L": 1})
          is None and bvd.propio_pasa(cond5_falsa(0.8), None) is None)
    sin_uno = (ref["frames"][1:], ref["offsets"][1:] - ref["offsets"][1], ref["valores"][ref["offsets"][1]:])
    try:
        bvd.agregados(trk, matrices, validas, BLOQUES, *sin_uno)
        check("si a la caché le falta un frame que el sondeo detectaría, error", False)
    except bvd.ErrorDeteccion:
        check("si a la caché le falta un frame que el sondeo detectaría, error", True)


@contextlib.contextmanager
def parches(objetos):
    guardados = [(o, n, getattr(o, n, None), hasattr(o, n)) for o, n, _ in objetos]
    try:
        for o, n, v in objetos:
            setattr(o, n, v)
        yield
    finally:
        for o, n, v, tenia in reversed(guardados):
            if tenia:
                setattr(o, n, v)
            else:
                delattr(o, n)


def main_con_todo_falso(argv, carpeta, trk, matrices, validas, cortar_en=None, error=None, decodificados=199319):
    """`bvd.cli` de punta a punta con el modelo, el vídeo, el ATD y la homografía falsos y los datos en `carpeta`."""
    import starter
    tactical = os.path.join(carpeta, "tactical")
    os.makedirs(tactical, exist_ok=True)
    rutas = {k: os.path.join(tactical, "BAR-ATH_tactical" + s) for k, s in
             (("video", ".mp4"), ("atd_raw", "_atd.txt"), ("atd_meta", "_atd.xml"), ("homography", "_homography.csv"))}
    modelo = os.path.join(carpeta, "modelo.pt")
    with open(modelo, "wb") as f:
        f.write(b"falso")
    if not os.path.exists(rutas["video"]):
        with open(rutas["video"], "wb") as f:  # un «vídeo» de bytes inventados: solo para su huella (la llave)
            f.write(bytes(range(256)) * 9000)
    detector, _ = detector_falso(trk, matrices, cortar_en=cortar_en, error=error or RuntimeError("corte"))
    llamadas_detectar = []

    def detectar(modelo_, imagen, conf=None, factor=None, centro=None, lado=None, max_det=None):
        llamadas_detectar.append((conf, factor, lado))
        return detector(imagen, centro)

    def leer_frames(ruta, frames, n_esperado=None, tamano=None, estado=None, hasta_el_final=False):
        estado = {} if estado is None else estado
        estado["backend"] = "FALSO"
        estado["frames_declarados"] = 199319
        lista = [int(f) for f in frames]
        for i, (t, img) in enumerate(fuente_falsa(trk, matrices)(lista)):
            estado["frames_leidos"], estado["segundos_leyendo"] = i + 1, (i + 1) * 0.001
            yield t, img
        if hasta_el_final:
            estado["frames_decodificados"] = decodificados

    load_homography = types.ModuleType("starter.load_homography")
    load_homography.load = lambda game, data_dir=None: (matrices, None, validas)
    torch_falso = types.ModuleType("torch")
    torch_falso.get_num_threads = lambda: det.HILOS
    modulos = dict(sys.modules)
    sys.modules["torch"] = torch_falso
    sys.modules["starter.load_homography"] = load_homography
    salida, errores = io.StringIO(), io.StringIO()
    try:
        with parches([(importlib.util, "find_spec", lambda nombre, *a: object()),
                      (starter, "load_homography", load_homography),
                      (games, "require", lambda *a, **k: list(rutas.values())),
                      (games, "asset_paths", lambda *a, **k: dict(rutas)),
                      (games, "video_path", lambda *a, **k: rutas["video"]),
                      (bvd.tracking, "from_atd", lambda *a, **k: trk),
                      (bs, "bloques_con_juego", lambda game=None: list(BLOQUES)), (bvd, "CADA", CADA),
                      (det, "cargar", lambda *a, **k: "modelo"), (det, "detectar", detectar),
                      (det, "leer_frames", leer_frames), (det, "versiones", lambda: {"python": "falso"}),
                      (det, "sha256_de", lambda ruta: det.MODELO_SHA256),
                      (bvd, "commit_del_codigo", lambda rutas=None: dict(INFO))]), \
                contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
            codigo = bvd.cli(argv + ["--modelo", modelo, "--data-dir", carpeta])
    finally:
        for nombre in ("torch", "starter.load_homography"):
            if nombre in modulos:
                sys.modules[nombre] = modulos[nombre]
            else:
                sys.modules.pop(nombre, None)
    return codigo, salida.getvalue(), errores.getvalue(), llamadas_detectar


def claves(obj, prefijo=""):
    if isinstance(obj, dict):
        return sorted(sum([[prefijo + "/" + k] + claves(v, prefijo + "/" + k) for k, v in obj.items()], []))
    return []


def listas_largas(obj):
    if isinstance(obj, dict):
        return max([0] + [listas_largas(v) for v in obj.values()])
    if isinstance(obj, list):
        return max([len(obj)] + [listas_largas(v) for v in obj])
    return 0


def sin_porcentajes(texto):
    """El stderr sin los porcentajes de progreso ni las cifras fijas del texto de los pasos («sha256», «condición 5»)."""
    texto = re.sub(r"\s*\d{1,3}\.\d %", "", texto)
    for fijo in ("sha256", "condición 5"):
        texto = texto.replace(fijo, "")
    return texto


def stderr_limpio(texto):
    """Sin los porcentajes de progreso, el stderr no lleva ninguna cifra."""
    return not re.search(r"\d", sin_porcentajes(texto))


def prueba_main(carpeta, ref):
    print("main de punta a punta, con todo falso (sin datos ni modelo)")
    trk, matrices, validas = partido()
    emul = os.path.join(carpeta, "no_existe.json")
    argv = ["--emulacion", emul, "--temblor-dfl", emul]
    d = os.path.join(carpeta, "main1")
    codigo, texto, errores, llamadas = main_con_todo_falso(argv, d, trk, matrices, validas)
    try:
        s = json.loads(texto)
    except ValueError:
        check("sale un JSON", False, (codigo, texto[-400:], errores[-400:]))
        return
    final = os.path.join(d, "tactical", bvd.NOMBRE_CACHE)
    check("sale bien y escribe la caché en MTAH_DATA_DIR/tactical/ (la carpeta del ATD)", codigo == 0
          and os.path.isfile(final) and not os.path.exists(os.path.join(d, "tactical", bvd.NOMBRE_PARCIAL)))
    check("llama al detector con la variante fijada (confianza 0,10, ×2, 320 px)",
          set(llamadas) == {(det.CONF, det.FACTOR, det.LADO)}, set(llamadas))
    check("la huella es la de la caché y la de ejecutar() (no depende de los metadatos)",
          s["huella"] == ref["huella"] == bvd.leer(final)["huella"])
    check("imprime procesados, con detección, detecciones, condiciones 1 y 2, temblor y rachas, la celda 5, tiempos",
          all(k in s for k in ("cache", "como_la_puerta_1b", "tiempos", "huella", "lista", "variante"))
          and all(k in s["cache"] for k in ("frames_procesados", "frames_con_alguna_deteccion", "detecciones"))
          and all(k in s["como_la_puerta_1b"] for k in ("condicion_1_pct_frames_con_deteccion_a_3m",
                                                        "condicion_2_pct_detecciones_a_mas_de_5m",
                                                        "temblor_y_rachas", "condicion_5_descriptiva")), sorted(s))
    check("sin la emulación, la condición 5 sale sin leer y lo dice", s["como_la_puerta_1b"]["condicion_5_descriptiva"]
          ["cumple"] is None and "aviso" in errores)
    check("stderr: solo pasos sin cifras y porcentajes de progreso", stderr_limpio(errores) and "%" in errores,
          re.findall(r".{0,40}\d.{0,40}", sin_porcentajes(errores))[:3])
    check("ninguna lista larga en la salida (nada por frame)", listas_largas(s) <= 10, listas_largas(s))
    check("imprime los tiempos acumulados y las huellas para comparar máquinas (píxeles, lista y código)",
          s.get("tiempos_acumulados", {}).get("ejecuciones") == 1
          and s["tiempos_acumulados"]["frames_procesados"] == len(ref["frames"])
          and set(s.get("para_comparar_maquinas", {})) == {"huella_solo_pixeles", "lista_sha256", "codigo_sha256"}
          and s["para_comparar_maquinas"]["huella_solo_pixeles"] != s["huella"], s.get("tiempos_acumulados"))
    check("la llave lleva la huella del vídeo (tamaño y primer y último MiB)",
          bvd.leer(final)["metadatos"]["video"]["bytes"] == 256 * 9000)
    check("no deja el fichero de la prueba de escritura", not os.path.exists(os.path.join(d, "tactical",
                                                                                          bvd.NOMBRE_PRUEBA)))
    ue = bvd.leer(final)["informativo"]["ultima_ejecucion"]
    check("la caché guarda la última ejecución con el lector del vídeo (backend y frames decodificados)",
          ue["backend_video"] == "FALSO" and ue["frames_decodificados"] == 199319, ue)
    # Otro partido inventado: la salida tiene exactamente las mismas claves.
    trk2, matrices2, validas2 = partido(semilla=3)
    d2 = os.path.join(carpeta, "main2")
    codigo2, texto2, _, _ = main_con_todo_falso(argv, d2, trk2, matrices2, validas2)
    s2 = json.loads(texto2) if codigo2 == 0 else {}
    check("con otro partido, las mismas claves (la salida no crece con los datos)", claves(s) == claves(s2))
    # La caché ya existe.
    codigo, texto, _, _ = main_con_todo_falso(argv, d, trk, matrices, validas)
    check("si la caché ya existe y no hay --forzar ni --resumen: error que lo dice, sin tocarla",
          codigo == 1 and texto.startswith("ERROR:") and "--forzar" in texto and "--resumen" in texto, texto)
    codigo, texto, errores, llamadas = main_con_todo_falso(argv + ["--resumen"], d, trk, matrices, validas)
    r = json.loads(texto) if codigo == 0 else {}
    check("--resumen: no detecta y da los mismos agregados, la misma huella y los tiempos acumulados",
          codigo == 0 and not llamadas
          and r.get("como_la_puerta_1b") == s["como_la_puerta_1b"] and r.get("huella") == s["huella"]
          and r.get("metadatos_que_difieren_de_los_actuales") == [] and r.get("tiempos_acumulados")
          == s["tiempos_acumulados"] and r.get("para_comparar_maquinas") == s["para_comparar_maquinas"],
          "" if codigo == 0 else texto[-300:])
    codigo, texto, _, llamadas = main_con_todo_falso(argv + ["--forzar"], d, trk, matrices, validas)
    check("--forzar: la rehace, con la misma huella", codigo == 0 and len(llamadas) == len(ref["frames"])
          and json.loads(texto)["huella"] == ref["huella"])
    # Un --forzar que se corta: sin --forzar dice que ya existe (y cómo seguir); con --forzar reanuda.
    codigo, texto, _, _ = main_con_todo_falso(argv + ["--forzar"], d, trk, matrices, validas, cortar_en=900)
    codigo, texto, _, _ = main_con_todo_falso(argv, d, trk, matrices, validas)
    check("tras un --forzar cortado, sin --forzar: error que dice que se relance con --forzar", codigo == 1
          and "relánzala con --forzar" in texto, texto)
    codigo, texto, _, llamadas = main_con_todo_falso(argv + ["--forzar"], d, trk, matrices, validas)
    r = json.loads(texto) if codigo == 0 else {}
    check("tras un --forzar cortado, el mismo comando reanuda y da la misma huella", codigo == 0
          and r.get("frames_reanudados_del_parcial") == 800 and len(llamadas) == len(ref["frames"]) - 800
          and r.get("huella") == ref["huella"], "" if codigo == 0 else texto[-300:])
    # Una carpeta tactical/ sin permiso de escritura: error antes de leer nada.
    d5 = os.path.join(carpeta, "main5")
    os.makedirs(os.path.join(d5, "tactical"))
    main_con_todo_falso(argv + ["--resumen"], d5, trk, matrices, validas)  # crea el «vídeo» falso
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        os.chmod(os.path.join(d5, "tactical"), 0o500)
        try:
            codigo, texto, _, llamadas = main_con_todo_falso(argv, d5, trk, matrices, validas)
        finally:
            os.chmod(os.path.join(d5, "tactical"), 0o700)
        check("tactical/ sin permiso de escritura: error claro antes de detectar", codigo == 1 and not llamadas
              and "no se puede escribir" in texto, texto)
    else:
        print("  [SALTA] la carpeta sin permiso de escritura: no se puede probar en este sistema")
    # Un error con valores en el mensaje, a mitad: no se imprime el mensaje; y luego reanuda.
    d3 = os.path.join(carpeta, "main3")
    codigo, texto, errores, _ = main_con_todo_falso(argv, d3, trk, matrices, validas, cortar_en=900,
                                                    error=ValueError("valor secreto 41.2873"))
    check("un error ajeno: solo el tipo y las líneas, sin el mensaje", codigo == 1 and "ValueError" in texto
          and "41.2873" not in texto + errores and "secreto" not in texto + errores, texto)
    check("deja el parcial", os.path.exists(os.path.join(d3, "tactical", bvd.NOMBRE_PARCIAL)))
    codigo, texto, errores, llamadas = main_con_todo_falso(argv, d3, trk, matrices, validas)
    r = json.loads(texto) if codigo == 0 else {}
    check("y la siguiente ejecución reanuda y da la misma huella", codigo == 0 and r.get("reanudacion") ==
          "reanuda desde el parcial" and r.get("frames_reanudados_del_parcial") == 800
          and len(llamadas) == len(ref["frames"]) - 800 and r.get("huella") == ref["huella"],
          "" if codigo == 0 else texto[-300:])
    check("stderr al reanudar: también sin cifras", stderr_limpio(errores),
          re.findall(r".{0,40}\d.{0,40}", sin_porcentajes(errores))[:3])
    codigo, texto, _, _ = main_con_todo_falso(["--forzar", "--resumen"], d3, trk, matrices, validas)
    check("--forzar con --resumen: error", codigo == 1 and texto.startswith("ERROR:"))
    d4 = os.path.join(carpeta, "main4")
    codigo, texto, _, _ = main_con_todo_falso(argv, d4, trk, matrices, validas, decodificados=199318)
    check("si el vídeo no decodifica 199.319 frames: error y no escribe la caché", codigo == 1
          and texto.startswith("ERROR:") and "decodifica" in texto
          and not os.path.exists(os.path.join(d4, "tactical", bvd.NOMBRE_CACHE)), texto)


def prueba_video(carpeta, ref):
    print("un MP4 de verdad, leído con detector.leer_frames, cortado y reanudado")
    if cv2 is None:
        print("  [SALTA] no hay cv2 en este entorno")
        return
    trk, matrices, validas = partido()
    ruta = os.path.join(carpeta, "mini.mp4")
    w = cv2.VideoWriter(ruta, cv2.VideoWriter_fourcc(*"mp4v"), 25, (ANCHO_VIDEO, ALTO_VIDEO))
    for i in range(N):
        w.write(pintar_indice(i))
    w.release()
    d = os.path.join(carpeta, "video")
    os.makedirs(d)
    estados = []

    def abrir(frames):
        estado = {}
        estados.append(estado)
        return det.leer_frames(ruta, frames, n_esperado=N, tamano=(ANCHO_VIDEO, ALTO_VIDEO), estado=estado,
                               hasta_el_final=True)
    try:
        correr(d, trk, matrices, validas, detector_falso(trk, matrices, cortar_en=1500)[0], abrir=abrir)
    except RuntimeError:
        pass
    r = correr(d, trk, matrices, validas, abrir=abrir)
    check("con el vídeo de verdad, cortado y reanudado, la misma huella que con la fuente inventada",
          r["reanudado_desde"] == 1400 and r["huella"] == ref["huella"], (r["reanudado_desde"], r["huella"][:12]))
    check("el lector decodifica el vídeo entero al acabar", estados[-1].get("frames_decodificados") == N, estados[-1])


def main():
    print("Prueba de validation/partido/balon_video_detectar.py")
    carpeta = carpeta_segura()
    try:
        prueba_constantes()
        prueba_objetivo()
        ref = prueba_cache_y_huella(carpeta)
        prueba_reanudar(carpeta, ref)
        prueba_no_reanudar(carpeta, ref)
        prueba_atomica(carpeta, ref)
        prueba_agregados(ref)
        prueba_main(carpeta, ref)
        prueba_video(carpeta, ref)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    print("\nTODO BIEN" if not FALLOS else "\nFALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
    return 0 if not FALLOS else 1


if __name__ == "__main__":
    sys.exit(main())
