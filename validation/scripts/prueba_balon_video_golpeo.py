"""Prueba `validation/partido/balon_video_golpeo.py` (el golpeo de cada reinicio con el balón del vídeo) sin datos de
ningún partido.

    python validation/scripts/prueba_balon_video_golpeo.py

Lo puede ejecutar cualquiera, Claude incluido. Todo es inventado y va a carpetas temporales (nunca a MTAH_DATA_DIR):

- un partido de 16.000 frames con dos tramos y ocho reinicios, uno por caso: un córner con hueco cuyo golpeo solo se
  ve volviendo hacia atrás desde la reaparición del ATD; una falta sin hueco, con el balón tapado justo en el golpeo y
  un objeto quieto en el recorte; un saque de banda sin reposo; un saque de puerta con el balón quieto en el centro del
  campo (sitio imposible); un córner con dos golpeos (ambiguo); un saque de banda con el golpeo antes de la ventana; un
  córner con el golpeo después del límite; y un córner cuyo ATD reaparece más de 10 s después del golpeo. Además, un
  saque inicial y una ventana entre los dos tramos, que no cuentan;
- una homografía afín; una fuente de frames cuya «imagen» lleva su número de frame, y un detector falso que mira esa
  imagen (si el seguidor le pasa la de otro frame, el balón sale en otro sitio) y solo ve lo que cae en el recorte.

Comprueba: las ventanas, sus límites y el arranque del recorrido; el estado y el frame exacto del golpeo en cada caso;
que la vuelta hacia atrás no pasa de ATRAS frames ni de la última detección; las reglas del evento en sus bordes
exactos (MIN_QUIETO, RADIO_QUIETO, HUECO_FECHA, MIN_MOVER, RADIO_MOVER) y el sitio por tipo; la elección de la detección
(puerta en píxeles con su tope, empates); la caché (arrays, tipos, huella canónica, escritura atómica, lectura); el
determinismo; los agregados (solo recuentos, celdas «< 5», sin ningún frame) y «frente a nuestro D»; `main` de punta a
punta con todo falso (búsqueda, --resumen, la caché que ya existe, --forzar), y que un error con valores no los imprime.
"""

import collections
import contextlib
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
import balon_video_golpeo as bvg  # noqa: E402
import detector as det  # noqa: E402  (balon_video_golpeo ya pone validation/balon_video en la ruta)
from possession import dead_ball  # noqa: E402
from possession.tracking import Tracking  # noqa: E402

FALLOS = []
LARGO, ANCHO = 105.3, 68.0
PITCH = (LARGO, ANCHO)
N = 16000
BLOQUES = ((100, 6000), (6100, 15900))
H_AFIN = np.array([[1800.0, 0.0, 60.0], [0.0, 1000.0, 40.0], [0.0, 0.0, 1.0]])


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def carpeta_segura():
    """Carpeta temporal para los ficheros inventados. Se niega a usar la de los datos del partido."""
    carpeta = os.path.realpath(tempfile.mkdtemp(prefix="mtah_prueba_golpeo_"))
    datos = os.path.realpath(games.DATA_DIR)
    if carpeta == datos or carpeta.startswith(datos + os.sep) or "mtah2027-data" in carpeta.lower():
        raise SystemExit("la carpeta temporal cae dentro de los datos del partido: no se ejecuta")
    return carpeta


# -- el partido inventado --------------------------------------------------------------------------------------------

class Partido:
    """El balón «de verdad» (metros; NaN donde no se ve en el vídeo), lo que ve el ATD y los objetos quietos."""

    def __init__(self, n=N):
        self.vx, self.vy = np.full(n, np.nan), np.full(n, np.nan)
        self.atd = np.zeros(n, dtype=bool)  # en tiempo del ATD: en el frame s enseña el balón del frame s − 4
        self.objetos = []  # (x, y, desde, hasta): objetos quietos que el detector confunde con el balón

    def quieto(self, a, b, x, y):
        self.vx[a:b], self.vy[a:b] = x, y

    def recta(self, a, b, p0, p1):
        t = (np.arange(a, b) - a) / float(b - a)
        self.vx[a:b] = p0[0] + (p1[0] - p0[0]) * t
        self.vy[a:b] = p0[1] + (p1[1] - p0[1]) * t

    def tapar(self, a, b):
        self.vx[a:b] = self.vy[a:b] = np.nan

    def tracking(self):
        n = len(self.vx)
        bx, by = np.full(n, np.nan), np.full(n, np.nan)
        s = np.arange(4, n)
        ok = self.atd[s] & np.isfinite(self.vx[s - 4])
        bx[s[ok]], by[s[ok]] = self.vx[s[ok] - 4], self.vy[s[ok] - 4]
        px = np.column_stack([np.full(n, 20.0), np.full(n, 80.0)])
        py = np.column_stack([np.full(n, 20.0), np.full(n, 50.0)])
        return Tracking(bx, by, px, py, np.array([0, 1], dtype=np.int8), PITCH, BLOQUES, 25)


def evento(tipo, inicio, fin, code="set pieces"):
    return {"code": code, "type": tipo, "start": inicio, "end": fin}


# Los ocho casos: (tipo, inicio, fin) de la ventana y lo que se espera.
CASOS = {
    "córner con hueco (hacia atrás desde la reaparición)": ("corner kick", 1500, 2375),
    "falta sin hueco, balón tapado en el golpeo y un objeto quieto en el recorte": ("free kick", 3000, 3875),
    "saque de banda sin reposo": ("throw-in", 4500, 5375),
    "saque de puerta con el balón quieto en el centro del campo": ("goal kick", 6600, 7475),
    "córner con dos golpeos": ("corner kick", 7800, 8675),
    "saque de banda con el golpeo antes de la ventana": ("throw-in", 9200, 10075),
    "córner con el golpeo después del límite": ("corner kick", 10500, 11375),
    "córner cuyo ATD reaparece más de 10 s después del golpeo": ("corner kick", 12000, 12875),
}


def construir():
    p = Partido()
    # 1. Córner con hueco: el balón sale cerca de una esquina, se coloca en el córner (el ATD no lo ve), se saca en el
    #    1650 y el ATD lo vuelve a ver en el 1720 (frame de vídeo 1716).
    p.recta(100, 1000, (30, 20), (90, 50))
    p.recta(1000, 1100, (90, 50), (104.0, 67.5))
    p.quieto(1550, 1651, 104.8, 67.3)
    p.recta(1650, 1700, (104.8, 67.3), (95, 40))
    p.recta(1700, 2600, (95, 40), (60, 30))
    p.atd[100:1100] = True
    p.atd[1720:2600] = True
    # 2. Falta sin hueco: quieto desde antes de la ventana, tapado del 3099 al 3103, sale a 0,6 m por frame; un objeto
    #    quieto a 9 m (dentro del recorte, fuera de la puerta).
    p.recta(2600, 2900, (40, 40), (60, 30))
    p.quieto(2900, 3101, 60, 30)
    p.recta(3100, 3130, (60, 30), (78, 30))
    p.recta(3130, 3700, (78, 30), (90, 20))
    p.tapar(3099, 3104)
    p.atd[2600:3700] = True
    p.objetos.append((69.0, 30.0, 2600, 3700))
    # 3. Saque de banda sin reposo: el balón no para nunca.
    p.recta(4300, 5500, (20, 5), (80, 60))
    p.atd[4300:5500] = True
    # 4. Saque de puerta con el balón quieto en el centro del campo: el evento se descarta por el sitio.
    p.recta(6200, 6650, (50, 50), (30, 34))
    p.quieto(6650, 6801, 30, 34)
    p.recta(6800, 6850, (30, 34), (60, 34))
    p.recta(6850, 7600, (60, 34), (70, 20))
    p.atd[6200:7600] = True
    # 5. Córner con dos golpeos (dos reposos en la esquina dentro de la ventana).
    p.recta(7600, 7850, (20, 20), (0.5, 0.5))
    p.quieto(7850, 7951, 0.5, 0.5)
    p.recta(7950, 7990, (0.5, 0.5), (20, 10))
    p.recta(7990, 8050, (20, 10), (0.3, 0.6))
    p.quieto(8050, 8151, 0.3, 0.6)
    p.recta(8150, 8190, (0.3, 0.6), (20, 12))
    p.recta(8190, 8800, (20, 12), (50, 30))
    p.atd[7600:8800] = True
    # 6. Saque de banda con un golpeo antes de la ventana (y otro dentro).
    p.recta(8900, 9000, (40, 20), (50, 0.5))
    p.quieto(9000, 9101, 50, 0.5)
    p.recta(9100, 9150, (50, 0.5), (50, 30))
    p.recta(9150, 9300, (50, 30), (52, 67.6))
    p.quieto(9300, 9401, 52, 67.6)
    p.recta(9400, 9450, (52, 67.6), (52, 38))
    p.recta(9450, 10200, (52, 38), (30, 30))
    p.atd[8900:10200] = True
    # 7. Córner con el golpeo en el 11256, después del límite (11.250).
    p.recta(10300, 11180, (50, 30), (104.9, 0.4))
    p.quieto(11180, 11256, 104.9, 0.4)
    p.recta(11255, 11300, (104.9, 0.4), (90, 20))
    p.recta(11300, 11500, (90, 20), (60, 30))
    p.atd[10300:11500] = True
    # 8. Córner cuyo ATD reaparece en el 12454 (vídeo 12450), 300 frames después del golpeo (12151).
    p.recta(11600, 11950, (60, 40), (100, 60))
    p.quieto(12050, 12151, 104.5, 67.5)
    p.recta(12150, 12200, (104.5, 67.5), (95, 40))
    p.recta(12200, 13000, (95, 40), (50, 30))
    p.atd[11600:11950] = True
    p.atd[12454:13000] = True
    events = [evento("kick off (start)", 150, 275)]
    events += [evento(tipo, a, b) for tipo, a, b in CASOS.values()]
    events.append(evento("throw-in", 6020, 6895))  # empieza entre los dos tramos: no cuenta
    events.sort(key=lambda e: (e["start"], e["end"], e["code"], e["type"]))
    return p, events


def homografias(n=N):
    matrices = np.repeat(H_AFIN[None], n, axis=0)
    return matrices, np.ones(n, dtype=bool)


def pixel(x, y):
    return det.pixeles_desde_campo(H_AFIN, x, y, LARGO, ANCHO)


def fuente_falsa(registro=None):
    def abrir(frames):
        anterior = None
        for t in [int(f) for f in frames]:
            if anterior is not None and t <= anterior:
                raise AssertionError("la lista de frames no va en orden")
            anterior = t
            if registro is not None:
                registro.append(t)
            yield t, np.array([float(t)])
    return abrir


def detector_falso(p, llamadas=None):
    """Mira la «imagen» (su frame) y devuelve el balón y los objetos que caen en el recorte, en el orden del detector."""
    def detectar(imagen, centro):
        t = int(imagen[0])
        if llamadas is not None:
            llamadas.append((t, centro))
        x0, y0, lx, ly = det.recorte(1920, 1080, centro, det.LADO)
        filas = []
        puntos = []
        if np.isfinite(p.vx[t]):
            puntos.append((p.vx[t], p.vy[t], 0.8))
        puntos += [(ox, oy, 0.3) for ox, oy, a, b in p.objetos if a <= t < b]
        for x, y, conf in puntos:
            px, py = pixel(x, y)
            if x0 <= px < x0 + lx and y0 <= py < y0 + ly:
                filas.append([round(float(px), 3), round(float(py), 3), 6.0, 6.0, conf])
        filas.sort(key=lambda f: (-f[4], f[0], f[1]))
        return np.array(filas, dtype=np.float64).reshape(-1, 5)
    return detectar


def correr(p, events, registro=None, llamadas=None):
    trk = p.tracking()
    ventanas = bvg.preparar_ventanas(trk, events)
    matrices, validas = homografias()
    filas, recuento = bvg.ejecutar(ventanas, fuente_falsa(registro), detector_falso(p, llamadas), trk, matrices,
                                   validas)
    return trk, ventanas, filas, recuento


# -- las pruebas -----------------------------------------------------------------------------------------------------

def prueba_ventanas(p, events):
    print("\n1. Las ventanas")
    trk = p.tracking()
    ventanas = bvg.preparar_ventanas(trk, events)
    check("solo las 8 ventanas que no son saques iniciales y empiezan en un tramo", len(ventanas) == 8,
          [v["inicio"] for v in ventanas])
    por_inicio = {v["inicio"]: v for v in ventanas}
    v1 = por_inicio[1500]
    check("el límite es el fin menos MARGEN_FIN (o el siguiente reinicio, o el fin del tramo)",
          v1["limite"] == 2375 - bvg.MARGEN_FIN and v1["corte"] == 3000, (v1["limite"], v1["corte"]))
    check("el recorrido empieza en la última posición del ATD antes de la ventana (en t+4)", v1["desde"] == 1095,
          v1["desde"])
    check("y acaba en el límite más HUECO_FECHA + MOVER", v1["hasta"] == v1["limite"] + bvg.HUECO_FECHA + bvg.MOVER)
    check("la ventana con hueco tiene el estado de la capa del hueco", v1["estado_hueco"] == dead_ball.GAP,
          v1["estado_hueco"])
    check("la reaparición del ATD es el primer frame con su balón en t+4", v1["reaparicion"] == 1716,
          v1["reaparicion"])
    v2 = por_inicio[3000]
    check("sin hueco, el recorrido empieza en el frame anterior a la ventana y no hay reaparición",
          v2["desde"] == 2999 and v2["reaparicion"] == -1, (v2["desde"], v2["reaparicion"]))
    trk_lejos = p.tracking()
    bx = np.array(trk_lejos.bx)
    bx[:1100] = np.nan  # sin ATD antes de la ventana: no hay última posición y el recorrido arranca en el inicio
    trk_lejos = trk_lejos._replace(bx=bx, by=np.where(np.isfinite(bx), trk_lejos.by, np.nan))
    v_lejos = [v for v in bvg.preparar_ventanas(trk_lejos, events) if v["inicio"] == 1500][0]
    check("sin una posición del ATD antes de la ventana, el recorrido empieza en el inicio",
          v_lejos["desde"] == 1500, v_lejos["desde"])
    trk0 = p.tracking()
    desdes = []
    for ultima in (3000 - bvg.HUECO_MAX - 1, 3000 - bvg.HUECO_MAX):
        bx, by = np.array(trk0.bx), np.array(trk0.by)
        bx[ultima + 5:3004] = np.nan  # el ATD (en t+4) no ve el balón entre `ultima` y la ventana del 3000
        bx[ultima + 4], by[ultima + 4] = 50.0, 30.0
        trk_borde = trk0._replace(bx=bx, by=np.where(np.isfinite(bx), by, np.nan))
        desdes.append([v for v in bvg.preparar_ventanas(trk_borde, events) if v["inicio"] == 3000][0]["desde"])
    check("ni si está a más de HUECO_MAX frames (a HUECO_MAX justos, sí)",
          desdes == [3000, 3000 - bvg.HUECO_MAX], desdes)
    otro = [evento("goal kick", 1500, 2375), evento("free kick", 1700, 2575)]
    v_corte = bvg.preparar_ventanas(trk, otro)[0]
    check("el siguiente reinicio corta el límite", v_corte["limite"] == 1700 and v_corte["corte"] == 1700,
          v_corte["limite"])
    frames = bvg.fotogramas_a_leer(ventanas)
    check("los frames a leer son la unión de [desde − ATRAS, hasta), en orden y sin repetir",
          np.all(np.diff(frames) > 0) and frames[0] == 1095 - bvg.ATRAS and 2999 - bvg.ATRAS in set(frames.tolist()))
    check("la huella de las ventanas cambia si cambia una ventana",
          bvg.huella_ventanas(ventanas) != bvg.huella_ventanas(ventanas[1:]))


def prueba_casos(p, events):
    print("\n2. Los ocho casos, de punta a punta")
    registro, llamadas = [], []
    trk, ventanas, filas, recuento = correr(p, events, registro, llamadas)
    por_inicio = {f["inicio"]: f for f in filas}
    f1 = por_inicio[1500]
    check("córner con hueco: golpeo en el 1651, visto volviendo hacia atrás desde la captura del 1716",
          f1["estado"] == bvg.GOLPEO and f1["golpeo"] == 1651 and f1["inicio_quieto"] == 1550 and f1["capturas"] == 2,
          (f1["estado"], f1["golpeo"], f1["inicio_quieto"], f1["capturas"]))
    # Las detecciones van redondeadas a 0,001 px: en metros, unas decenas de micras.
    check("su reposo está en la esquina", abs(f1["x_m"] - 104.8) < 1e-3 and abs(f1["y_m"] - 67.3) < 1e-3,
          (f1["x_m"], f1["y_m"]))
    f2 = por_inicio[3000]
    # El reposo empieza donde la llegada ya queda a 0,5 m o menos del sitio: en el 2894 (la llegada va a 0,075 m por
    # frame, así que los 6 frames anteriores al 2900 ya cuentan como quietos).
    llegada = np.hypot(p.vx[2800:2901] - 60.0, p.vy[2800:2901] - 30.0)
    inicio_esperado = 2800 + int(np.flatnonzero(llegada > bvg.RADIO_QUIETO)[-1]) + 1
    check("falta: golpeo en la última quieta + 1 (3099), con la primera en movimiento en el 3104",
          f2["estado"] == bvg.GOLPEO and f2["golpeo"] == 3099 and f2["ultimo_quieto"] == 3098
          and f2["primer_movimiento"] == 3104 and f2["inicio_quieto"] == inicio_esperado == 2894,
          (f2["estado"], f2["golpeo"], f2["ultimo_quieto"], f2["primer_movimiento"], f2["inicio_quieto"]))
    check("el objeto quieto del recorte no se cuela en la pista", abs(f2["x_m"] - 60.0) < 1e-6)
    check("saque de banda sin reposo: sin golpeo", por_inicio[4500]["estado"] == bvg.SIN_GOLPEO,
          por_inicio[4500]["estado"])
    f4 = por_inicio[6600]
    check("saque de puerta en el centro del campo: sin golpeo, con un evento descartado por el sitio",
          f4["estado"] == bvg.SIN_GOLPEO and f4["descartados_por_sitio"] == 1, (f4["estado"],
                                                                                f4["descartados_por_sitio"]))
    f5 = por_inicio[7800]
    check("córner con dos golpeos: ambiguo (guarda el primero)", f5["estado"] == bvg.AMBIGUO and f5["golpeo"] == 7951,
          (f5["estado"], f5["golpeo"]))
    f6 = por_inicio[9200]
    check("saque de banda con un golpeo antes de la ventana: «antes de la ventana»",
          f6["estado"] == bvg.ANTES and f6["golpeo"] == 9101, (f6["estado"], f6["golpeo"]))
    f7 = por_inicio[10500]
    check("córner con el golpeo después del límite: fuera de plazo", f7["estado"] == bvg.FUERA_DE_PLAZO
          and f7["golpeo"] == 11256, (f7["estado"], f7["golpeo"]))
    f8 = por_inicio[12000]
    check("córner cuyo ATD reaparece 300 frames después: la vuelta atrás no llega al reposo (sin golpeo)",
          f8["estado"] == bvg.SIN_GOLPEO and f8["capturas"] >= 2, (f8["estado"], f8["capturas"]))
    leidos = np.array(registro)
    check("la fuente da exactamente los frames de la lista", np.array_equal(leidos, bvg.fotogramas_a_leer(ventanas)))
    check("el recuento cuadra con las llamadas al detector", recuento["intentos"] == len(llamadas)
          == sum(f["intentos"] for f in filas))
    # La vuelta hacia atrás del caso 8 (desde la captura del 12.450) baja justo hasta el 12.200 (12.450 − ATRAS): el
    # balón se ve todo el rato, así que solo la para el tope.
    atras8 = [t for t, _ in llamadas if 11980 <= t < 12450]
    check("la vuelta hacia atrás llega justo a ATRAS frames y no pasa", min(atras8) == 12450 - bvg.ATRAS, min(atras8))
    return trk, ventanas, filas


def prueba_atras_y_ultima(p, events):
    print("\n3. La vuelta hacia atrás, en sus límites")
    llamadas = []
    trk, ventanas, filas, _ = correr(p, events, llamadas=llamadas)
    # En el caso 1, entre la captura del 1095 y la del 1716 el seguidor pierde el balón en el 1100; la vuelta desde el
    # 1716 no puede bajar del 1466 (1716 − 250) ni pedir frames ya cubiertos (≤ 1099).
    adelante = [t for t, _ in llamadas if 1100 <= t < 1125]
    check("tras la última detección aceptada (1099) sigue buscando PERDIDO frames más", adelante == list(range(1100,
                                                                                                          1125)))
    vuelta = [t for t, _ in llamadas if 1125 <= t < 1716]
    check("la vuelta desde la captura del 1716 empieza en el 1715 y no baja del 1466 (ni pide frames ≤ 1099)",
          max(vuelta) == 1715 and min(vuelta) >= 1716 - bvg.ATRAS, (min(vuelta), max(vuelta)))
    check("y se para tras PERDIDO frames sin aceptar (el balón no se ve antes del 1550)",
          min(vuelta) == 1550 - bvg.PERDIDO, min(vuelta))
    sin_ver = [t for t, _ in llamadas if 1125 <= t < 1525]
    check("mientras no hay ATD ni detección reciente, el seguidor no detecta", not sin_ver, len(sin_ver))
    # Otro partido, con un saque de banda en el 3000: el ATD ve el balón hasta el 3009 y el seguidor lo acepta hasta
    # ahí; en el 3010 aparece otro balón, quieto junto a la banda y fuera del recorte del seguidor, que el ATD ve desde
    # el vídeo 3200. La vuelta desde esa captura podría bajar hasta el 2950 (ATRAS), pero no pasa del 3010: la última
    # detección aceptada hacia delante es la del 3009.
    llamadas_ultima = []
    p2 = Partido()
    p2.recta(2700, 3010, (40, 40), (60, 30))
    p2.quieto(3010, 3301, 60, 66)
    p2.recta(3300, 3340, (60, 66), (60, 40))
    p2.recta(3340, 3600, (60, 40), (40, 30))
    p2.atd[2700:3014] = True
    p2.atd[3204:3600] = True
    _, _, filas2, _ = correr(p2, [evento("throw-in", 3000, 3875)], llamadas=llamadas_ultima)
    veces = collections.Counter(t for t, _ in llamadas_ultima)
    check("la vuelta hacia atrás no pide frames ya cubiertos hacia delante (el 3009 se detecta una vez; el 3010, dos)",
          veces[3009] == 1 and veces[3010] == 2 and min(veces) == 2999 - bvg.ATRAS, (veces[3009], veces[3010]))
    check("y encuentra el golpeo de ese balón", filas2[0]["estado"] == bvg.GOLPEO and filas2[0]["golpeo"] == 3301,
          (filas2[0]["estado"], filas2[0]["golpeo"]))


def prueba_evento():
    print("\n4. Las reglas del evento, en sus bordes")
    tipo, pitch = "free kick", PITCH

    def pista(n_quieto=25, hueco=1, n_mover=10, paso=0.6, desv=0.0, quieto_desde=0):
        frames = list(range(quieto_desde, quieto_desde + n_quieto))
        xs = [50.0 + (desv if i == 0 else 0.0) for i in range(n_quieto)]
        t_mov = frames[-1] + hueco
        for k in range(n_mover):
            frames.append(t_mov + k)
            xs.append(50.0 + paso * (k + 1))
        return np.array(frames), np.array(xs), np.full(len(xs), 30.0)

    def golpeos(*args, **kwargs):
        f, x, y = pista(*args, **kwargs)
        ev, _ = bvg.buscar_eventos(f, x, y, tipo, pitch)
        return [e["golpeo"] for e in ev]

    check("con 25 detecciones quietas y 10 en movimiento hay un evento, en la última quieta + 1",
          golpeos() == [25], golpeos())
    f, x, y = pista()
    keep = np.r_[np.arange(12, 25), np.arange(25, 35)]  # 13 quietas en los 25 frames
    check("13 detecciones quietas (MIN_QUIETO) valen", len(bvg.buscar_eventos(f[keep], x[keep], y[keep], tipo,
                                                                              pitch)[0]) == 1)
    keep = np.r_[np.arange(13, 25), np.arange(25, 35)]
    check("12 no", not bvg.buscar_eventos(f[keep], x[keep], y[keep], tipo, pitch)[0])
    check("una quieta a 0,5 m de la mediana vale; a 0,51, no",
          golpeos(desv=0.5) == [25] and golpeos(desv=0.51) == [])
    check("13 frames entre la última quieta y la primera en movimiento valen; 14, no",
          golpeos(hueco=13) == [25] and golpeos(hueco=14) == [])
    check("3 detecciones en movimiento valen; 2, no", golpeos(n_mover=3, paso=0.9) == [25]
          and golpeos(n_mover=2, paso=1.5) == [])

    def lejana(ultima):
        f = np.arange(29)
        x = np.r_[np.full(25, 50.0), 50.0 + np.array([0.6, 1.0, 1.5, ultima])]
        return [e["golpeo"] for e in bvg.buscar_eventos(f, x, np.full(29, 30.0), tipo, pitch)[0]]

    check("la más lejana a 2,0 m vale; a 1,99, no", lejana(2.0) == [25] and lejana(1.99) == [], (lejana(2.0),
                                                                                                lejana(1.99)))
    check("a 0,5 m justos todavía está quieta: el golpeo sale en el frame siguiente", golpeos(paso=0.5) == [26],
          golpeos(paso=0.5))
    f, x, y = pista()
    ev, desc = bvg.buscar_eventos(f, x, y, "corner kick", pitch)
    check("el mismo reposo, en el centro, no vale como córner (se descarta por el sitio)", not ev and desc == 1)
    f, x, y = pista(quieto_desde=40)
    f = np.r_[np.arange(0, 27), f]  # otro reposo en el mismo sitio, con 13 frames sin detección (27 a 39) entre medias
    x, y = np.r_[np.full(27, 50.0), x], np.r_[np.full(27, 30.0), y]
    ev, _ = bvg.buscar_eventos(f, x, y, tipo, pitch)
    check("el inicio del reposo no salta un hueco de más de HUECO_FECHA frames sin detección", len(ev) == 1
          and ev[0]["inicio_quieto"] == 40, [e["inicio_quieto"] for e in ev])
    f, x, y = pista(quieto_desde=39)
    f = np.r_[np.arange(0, 27), f]  # con 12 frames sin detección (27 a 38), sí
    x, y = np.r_[np.full(27, 50.0), x], np.r_[np.full(27, 30.0), y]
    ev, _ = bvg.buscar_eventos(f, x, y, tipo, pitch)
    check("y sí uno de HUECO_FECHA justos", len(ev) == 1 and ev[0]["inicio_quieto"] == 0,
          [e["inicio_quieto"] for e in ev])


def prueba_sitio():
    print("\n5. El sitio del golpeo según el tipo (reglamento)")
    pp = bvg.posicion_posible
    check("córner a 3,0 m de una esquina sí; a 3,01, no",
          pp("corner kick", 3.0, 0.0, PITCH) and not pp("corner kick", 3.01, 0.0, PITCH)
          and pp("corner kick", LARGO, ANCHO - 3.0, PITCH))
    check("saque de puerta en el área pequeña más 2 m sí; fuera, no",
          pp("goal kick", 7.5, 34.0 + 11.16, PITCH) and not pp("goal kick", 7.51, 34.0, PITCH)
          and not pp("goal kick", 3.0, 34.0 + 11.17, PITCH) and pp("goal kick", LARGO - 7.5, 34.0, PITCH)
          and not pp("goal kick", -2.01, 34.0, PITCH))
    check("saque de banda a 5 m de una banda, a un lado u otro, sí; a 5,01, no",
          pp("throw-in", 50.0, 5.0, PITCH) and pp("throw-in", 50.0, -5.0, PITCH) and pp("throw-in", 50.0, ANCHO + 5,
                                                                                         PITCH)
          and not pp("throw-in", 50.0, 5.01, PITCH) and not pp("throw-in", LARGO + 2.01, 0.0, PITCH))
    check("falta (y otros tipos) en el campo más 2 m", pp("free kick", -2.0, ANCHO + 2.0, PITCH)
          and not pp("free kick", -2.01, 10.0, PITCH) and pp("penalty", 11.0, 34.0, PITCH))
    check("sin posición, nunca", not pp("free kick", np.nan, 10.0, PITCH))


def prueba_eleccion():
    print("\n6. La elección de la detección")
    dets = np.array([[100.0, 100.0, 6, 6, 0.9], [130.0, 100.0, 6, 6, 0.5], [70.0, 100.0, 6, 6, 0.4]])
    xm, ym = np.array([1.0, 2.0, 3.0]), np.array([1.0, 1.0, 1.0])
    check("siguiendo, la más cercana al centro (no la de más confianza)",
          bvg.elegir_siguiendo(dets, xm, ym, (128.0, 100.0), 1) == 1)
    check("empate de distancia: la primera en el orden del detector",
          bvg.elegir_siguiendo(dets, xm, ym, (115.0, 100.0), 1) == 0)
    check("la puerta es SALTO_PX por frame de edad",
          bvg.elegir_siguiendo(dets[:1], xm[:1], ym[:1], (100.0 + 41, 100.0), 1) is None
          and bvg.elegir_siguiendo(dets[:1], xm[:1], ym[:1], (100.0 + 40, 100.0), 1) == 0
          and bvg.elegir_siguiendo(dets[:1], xm[:1], ym[:1], (100.0 + 79, 100.0), 2) == 0)
    check("con su tope SALTO_MAX", bvg.elegir_siguiendo(dets[:1], xm[:1], ym[:1], (100.0 + 121, 100.0), 10) is None
          and bvg.elegir_siguiendo(dets[:1], xm[:1], ym[:1], (100.0 + 120, 100.0), 10) == 0)
    check("sin metros, no", bvg.elegir_siguiendo(dets[:1], np.array([np.nan]), ym[:1], (100.0, 100.0), 1) is None)
    check("captando, la más cercana en metros al ATD, a 3 m o menos",
          bvg.elegir_captando(xm, ym, 2.9, 1.0) == 2 and bvg.elegir_captando(xm, ym, 6.0, 1.0) == 2
          and bvg.elegir_captando(xm, ym, 6.01, 1.0) is None)
    check("sin detecciones, nada", bvg.elegir_siguiendo(np.zeros((0, 5)), np.zeros(0), np.zeros(0), (0, 0), 1) is None
          and bvg.elegir_captando(np.zeros(0), np.zeros(0), 0.0, 0.0) is None)
    # Dónde va el recorte: el ATD ve el balón en (50, 30) todo el rato; el detector solo lo ve en el frame 10, en
    # (52, 30). Del 11 al 15 (edad ≤ RECENTRAR) el recorte va a la última detección; en el 16, al ATD; y sin ATD, a la
    # última detección mientras tenga PERDIDO frames o menos.
    centros = []

    def detector(imagen, centro):
        centros.append((int(imagen[0]), centro))
        if int(imagen[0]) != 10:
            return np.zeros((0, 5))
        px, py = pixel(52.0, 30.0)
        return np.array([[px, py, 6.0, 6.0, 0.8]])

    n = 60
    rx, ry = np.full(n, 50.0), np.full(n, 30.0)
    rx[40:], ry[40:] = np.nan, np.nan
    ventana = {"desde": 10, "hasta": n, "tipo": "free kick", "inicio": 10, "limite": n}
    s = bvg.Seguidor(ventana, rx, ry, np.repeat(H_AFIN[None], n, axis=0), np.ones(n, dtype=bool), PITCH, detector)
    for t in range(10, n):
        s.paso(t, np.array([float(t)]), collections.deque([(t, np.array([float(t)]))]))
    centro = dict(centros)
    ultima, atd = pixel(52.0, 30.0), pixel(50.0, 30.0)
    check("con la última detección a RECENTRAR frames o menos, el recorte va a ella",
          all(np.allclose(centro[t], ultima) for t in range(11, 16)))
    check("con más, si el ATD ve el balón, al ATD", all(np.allclose(centro[t], atd) for t in range(16, 40)))
    check("sin ATD y con la última a más de PERDIDO frames, no detecta", not any(t >= 40 for t in centro))
    s2 = bvg.Seguidor(dict(ventana), np.where(np.arange(n) < 11, 50.0, np.nan), np.where(np.arange(n) < 11, 30.0,
                                                                                          np.nan),
                      np.repeat(H_AFIN[None], n, axis=0), np.ones(n, dtype=bool), PITCH, detector)
    centros.clear()
    for t in range(10, n):
        s2.paso(t, np.array([float(t)]), collections.deque([(t, np.array([float(t)]))]))
    centro = dict(centros)
    check("sin ATD, a la última detección hasta PERDIDO frames después, y luego nada",
          sorted(centro) == list(range(10, 10 + bvg.PERDIDO + 1))
          and all(np.allclose(centro[t], ultima) for t in range(11, 10 + bvg.PERDIDO + 1)))


def prueba_clasificar():
    print("\n7. Qué se hace con los eventos de una ventana")
    e = lambda k: {"golpeo": k}  # noqa: E731
    c = bvg.clasificar
    check("sin balón", c([], 100, 200, con_balon=False)[0] == bvg.SIN_BALON)
    check("sin eventos", c([], 100, 200)[0] == bvg.SIN_GOLPEO)
    check("uno dentro: golpeo", c([e(150)], 100, 200) == (bvg.GOLPEO, e(150)))
    check("el inicio de la ventana vale; el límite, no", c([e(100)], 100, 200)[0] == bvg.GOLPEO
          and c([e(200)], 100, 200)[0] == bvg.FUERA_DE_PLAZO)
    check("el primero antes de la ventana manda", c([e(99), e(150)], 100, 200) == (bvg.ANTES, e(99)))
    check("dos dentro: ambiguo", c([e(120), e(150)], 100, 200)[0] == bvg.AMBIGUO)
    check("uno dentro y otro después del límite: golpeo", c([e(150), e(230)], 100, 200)[0] == bvg.GOLPEO)


def prueba_cache(filas, ventanas, carpeta):
    print("\n8. La caché")
    arrays = bvg.arrays_de(filas)
    check("tipos fijos", all(arrays[k].dtype == np.int64 for k in bvg.ENTEROS)
          and all(arrays[k].dtype == np.float64 for k in bvg.REALES)
          and all(arrays[k].dtype.kind == "U" for k in bvg.TEXTOS))
    def igual(a, b):
        return all((np.isnan(a[k]) and np.isnan(b[k])) if k in bvg.REALES and np.isnan(a[k]) else a[k] == b[k]
                   for k in bvg.ENTEROS + bvg.REALES + bvg.TEXTOS)

    vuelta = bvg.filas_de(arrays)
    check("ida y vuelta de las filas", len(vuelta) == len(filas) and all(igual(a, b) for a, b in zip(vuelta, filas)))
    hu = bvg.huella(arrays)
    otro = {k: v.copy() for k, v in arrays.items()}
    otro_nan = np.frombuffer(np.array([0x7FF8000000000001], dtype=np.uint64).tobytes(), dtype=np.float64)[0]
    otro["x_m"] = np.where(np.isnan(otro["x_m"]), otro_nan, otro["x_m"])
    otro["y_m"] = np.where(np.isnan(otro["y_m"]), otro["y_m"], otro["y_m"])
    otro["y_m"][0] = -0.0 if otro["y_m"][0] == 0 else otro["y_m"][0]
    check("la huella no cambia con otro NaN", bvg.huella(otro) == hu and np.isnan(otro["x_m"]).any())
    cero = {k: v.copy() for k, v in arrays.items()}
    cero["x_m"] = np.where(np.isnan(cero["x_m"]), 0.0, cero["x_m"])
    menos_cero = {k: v.copy() for k, v in cero.items()}
    menos_cero["x_m"] = np.where(cero["x_m"] == 0.0, -0.0, cero["x_m"])
    check("ni con −0,0", bvg.huella(cero) == bvg.huella(menos_cero))
    otro = {k: v.copy() for k, v in arrays.items()}
    otro["golpeo"][0] += 1
    check("la huella cambia si cambia un golpeo", bvg.huella(otro) != hu)
    otro = {k: v.copy() for k, v in arrays.items()}
    otro["estado"] = np.array([bvg.SIN_GOLPEO] + list(otro["estado"][1:]), dtype=np.str_)
    check("y si cambia un estado", bvg.huella(otro) != hu)
    meta = bvg.metadatos_de(games.GAME, N, PITCH, det.MODELO_SHA256, {"python": "falso"}, 4, "c" * 64, ventanas)
    ruta = os.path.join(carpeta, bvg.NOMBRE_CACHE)
    bvg.guardar(ruta, arrays, meta, {"commit": "abc"}, hu)
    leida = bvg.leer(ruta)
    check("se lee lo que se escribe", leida["huella"] == hu == bvg.huella(leida["arrays"])
          and leida["metadatos"] == json.loads(json.dumps(meta, sort_keys=True)))
    check("sin temporal al acabar", not os.path.exists(ruta + bvg.SUFIJO_TEMPORAL))
    check("los metadatos llevan la variante, las constantes y la huella de las ventanas",
          meta["variante"]["recorte_px"] == det.LADO and meta["constantes"] == bvg.CONSTANTES
          and meta["ventanas"]["sha256"] == bvg.huella_ventanas(ventanas))
    with open(os.path.join(carpeta, "roto.npz"), "wb") as f:
        f.write(b"esto no es un npz")
    try:
        bvg.leer(os.path.join(carpeta, "roto.npz"))
        check("una caché rota da error", False)
    except bvg.ErrorGolpeo as e:
        check("una caché rota da error sin valores", "roto.npz" in str(e))
    bvg.probar_escritura(carpeta)
    check("la prueba de escritura no deja nada", not os.path.exists(os.path.join(carpeta, bvg.NOMBRE_PRUEBA)))


def prueba_determinismo(p, events, filas):
    print("\n9. Determinismo")
    _, _, otra, _ = correr(p, events)
    check("dos ejecuciones dan la misma huella", bvg.huella(bvg.arrays_de(otra)) == bvg.huella(bvg.arrays_de(filas)))


def prueba_agregados(filas, ventanas):
    print("\n10. Los agregados")
    codes = np.zeros(N, dtype=np.int64)
    codes[1100:1500] = 2  # caso 1: nuestro D acaba 151 frames antes del golpeo (1651)
    codes[2950:3110] = 2  # caso 2: acaba 11 frames después del golpeo (3099)
    check("el fin de nuestro D en cada ventana", bvg.fin_de_nuestro_d(codes, BLOQUES[0], 1500, 1651, 25) == 1500
          and bvg.fin_de_nuestro_d(codes, BLOQUES[0], 3000, 3099, 25) == 3110
          and bvg.fin_de_nuestro_d(codes, BLOQUES[0], 4500, 4600, 25) is None)
    agg = bvg.agregados(filas, 25, codes, BLOQUES)
    texto = json.dumps(agg, ensure_ascii=False)
    check("los estados suman las ventanas", sum(agg["por_estado"].values()) == len(filas) == 8
          and agg["por_estado"][bvg.GOLPEO] == 2)
    check("las celdas de 1 a 4 salen como «< 5»", agg["por_tipo"]["corner kick"]["ventanas"] == "< 5")
    frente = agg["frente_a_nuestro_d"]["todos"]
    check("frente a nuestro D: uno acaba más de 5 s antes y otro a 1 s o menos",
          frente["acaba >5 s antes"] == "< 5" and frente["a 1 s o menos"] == "< 5" and frente["sin D"] == 0, frente)
    sin_recuentos = json.dumps({k: v for k, v in agg.items() if k != "detecciones"}, ensure_ascii=False)
    frames = set(re.findall(r"\d{4,}", sin_recuentos))
    check("ningún frame en la salida (fuera del recuento de detecciones)", not frames, sorted(frames)[:5])
    check("es JSON", isinstance(json.loads(texto), dict))
    try:
        bvg.agregados(filas, 25, codes[:100], BLOQUES)
        check("una entrega corta da error", False)
    except bvg.ErrorGolpeo:
        check("una entrega corta da error", True)


# -- main de punta a punta, con todo falso ---------------------------------------------------------------------------

def xml_smart_tagging(ruta, events):
    cuerpo = []
    for i, e in enumerate(events):
        cuerpo.append("<instance><ID>{}</ID><start>{}</start><end>{}</end><code>{}</code><label><group>Type</group>"
                      "<text>{}</text></label></instance>".format(i, e["start"] / 25.0, e["end"] / 25.0,
                                                                  e["code"].upper(), e["type"].title()))
    with open(ruta, "w") as f:
        f.write("<file><ALL_INSTANCES>{}</ALL_INSTANCES></file>".format("".join(cuerpo)))


@contextlib.contextmanager
def parches(p, carpeta, trk):
    """Sustituye en el script lo que lee el partido (ATD, homografía, vídeo, modelo) por lo inventado."""
    tactical = os.path.join(carpeta, "tactical")
    os.makedirs(tactical, exist_ok=True)
    paths = {k: os.path.join(tactical, "falso_" + k) for k in ("video", "atd_meta", "atd_raw", "homography",
                                                              "smart_tagging")}
    with open(paths["video"], "wb") as f:
        f.write(b"video falso")
    modelo = os.path.join(carpeta, "modelo.pt")
    with open(modelo, "wb") as f:
        f.write(b"modelo falso")
    _, events = construir()
    xml_smart_tagging(paths["smart_tagging"], events)
    import starter.load_homography as lh
    guardados = {"require": games.require, "asset_paths": games.asset_paths, "from_atd": bvg.tracking.from_atd,
                 "load": lh.load, "cargar": det.cargar, "detectar": det.detectar, "leer_frames": det.leer_frames,
                 "sha256_de": det.sha256_de, "importlib": bvg.importlib, "versiones": det.versiones,
                 "ruta_por_defecto": det.ruta_por_defecto}
    detector = detector_falso(p)

    def leer_frames(ruta, frames, n_esperado=None, tamano=None, estado=None, hasta_el_final=False):
        for t, imagen in fuente_falsa()(frames):
            yield t, imagen
        if estado is not None:
            estado["frames_decodificados"] = games.GAMES[games.GAME]["n_video_frames"]
            estado["backend"] = "FALSO"

    def cargar(ruta, hilos=4, **kwargs):
        import torch
        torch.set_num_threads(det.HILOS)
        return "modelo"

    real_sha = det.sha256_de
    guardados["resultados"] = bvg.RESULTADOS
    bvg.RESULTADOS = carpeta  # regla nº 1: ni por defecto puede leer una entrega nuestra de evaluation/results
    games.require = lambda *a, **k: None
    games.asset_paths = lambda *a, **k: dict(paths)
    bvg.tracking.from_atd = lambda paths, game=None, report=None: trk
    lh.load = lambda *a, **k: (homografias()[0], None, homografias()[1])
    det.cargar = cargar
    det.detectar = lambda modelo, imagen, conf, factor, centro, lado: detector(imagen, centro)
    det.leer_frames = leer_frames
    det.sha256_de = lambda ruta: det.MODELO_SHA256 if ruta == modelo else real_sha(ruta)
    det.versiones = lambda: {"python": "falso"}
    det.ruta_por_defecto = lambda destino=None: modelo
    bvg.importlib = types.SimpleNamespace(util=types.SimpleNamespace(find_spec=lambda m: object()))
    try:
        yield paths
    finally:
        games.require, games.asset_paths = guardados["require"], guardados["asset_paths"]
        bvg.tracking.from_atd, lh.load = guardados["from_atd"], guardados["load"]
        det.cargar, det.detectar, det.leer_frames = guardados["cargar"], guardados["detectar"], guardados["leer_frames"]
        det.sha256_de, det.versiones = guardados["sha256_de"], guardados["versiones"]
        det.ruta_por_defecto, bvg.importlib = guardados["ruta_por_defecto"], guardados["importlib"]
        bvg.RESULTADOS = guardados["resultados"]


def ejecutar_main(argv):
    salida = io.StringIO()
    errores = io.StringIO()
    with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
        codigo = bvg.cli(argv)
    return codigo, salida.getvalue(), errores.getvalue()


def prueba_main(p, filas_esperadas):
    print("\n11. main de punta a punta, con todo falso")
    carpeta = carpeta_segura()
    try:
        trk = p.tracking()
        entrega = os.path.join(carpeta, "entrega.csv")
        codes = np.array(["H"] * N, dtype=object)
        codes[1100:1500] = "D"
        with open(entrega, "w") as f:
            f.write("frame,label\n" + "".join("{},{}\n".format(i, c) for i, c in enumerate(codes)))
        with parches(p, carpeta, trk) as paths:
            codigo, out, err = ejecutar_main(["--entrega", entrega])
            check("la búsqueda acaba bien", codigo == 0, out[-300:])
            res = json.loads(out)
            ruta = os.path.join(os.path.dirname(paths["atd_raw"]), bvg.NOMBRE_CACHE)
            check("escribe la caché junto al ATD", os.path.isfile(ruta))
            check("su huella es la de la ejecución directa",
                  res["huella"] == bvg.huella(bvg.arrays_de(filas_esperadas)), res["huella"][:12])
            check("dice con qué entrega compara y su sha256", res["entrega_comparada"]["sha256"] == det.sha256_de(
                entrega))
            agg = {k: v for k, v in res["golpeos"].items() if k != "detecciones"}
            check("la salida no lleva ningún frame", not re.findall(r"\d{4,}", json.dumps(agg)))
            check("por stderr, solo pasos y porcentajes", not re.search(r"\d", re.sub(r"\d+\.\d %|sha256", "", err)),
                  err[-200:])
            codigo, out, _ = ejecutar_main(["--entrega", entrega])
            check("con la caché hecha, sin --forzar, da error", codigo == 1 and "ya existe la caché" in out, out)
            codigo, out, _ = ejecutar_main(["--resumen", "--entrega", entrega])
            res2 = json.loads(out)
            check("--resumen da los mismos agregados sin leer el vídeo", codigo == 0
                  and res2["golpeos"] == res["golpeos"] and res2["huella"] == res["huella"])
            codigo, out, _ = ejecutar_main(["--forzar", "--entrega", entrega])
            check("--forzar la rehace con la misma huella", codigo == 0 and json.loads(out)["huella"] == res["huella"])
            codigo, out, _ = ejecutar_main(["--forzar", "--resumen", "--entrega", entrega])
            check("--forzar y --resumen no van juntos", codigo == 1 and "no van juntos" in out)
            codigo, out, _ = ejecutar_main(["--resumen"])
            check("sin --entrega busca equipo_v8 en la carpeta de resultados (aquí, la temporal): no la encuentra y lo dice",
                  codigo == 0 and "no encuentro la entrega" in json.loads(out)["entrega_comparada"])
            meta_original = bvg.CONSTANTES["QUIETO"]
            bvg.CONSTANTES["QUIETO"] = meta_original + 1
            try:
                codigo, out, _ = ejecutar_main(["--resumen", "--entrega", entrega])
            finally:
                bvg.CONSTANTES["QUIETO"] = meta_original
            check("--resumen con una caché de otras constantes da error", codigo == 1 and "constantes" in out, out)
            original = bvg.preparar_ventanas
            bvg.preparar_ventanas = lambda trk, events: (_ for _ in ()).throw(ValueError("frame 123456 x=1,234"))
            try:
                codigo, out, _ = ejecutar_main(["--resumen", "--entrega", entrega])
            finally:
                bvg.preparar_ventanas = original
            check("un error con valores imprime solo el tipo y las líneas", codigo == 1 and "123456" not in out
                  and "ValueError" in out, out)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def main():
    print("Prueba del golpeo de cada reinicio con el balón del vídeo (sin datos de ningún partido)")
    p, events = construir()
    prueba_ventanas(p, events)
    trk, ventanas, filas = prueba_casos(p, events)
    prueba_atras_y_ultima(p, events)
    prueba_evento()
    prueba_sitio()
    prueba_eleccion()
    prueba_clasificar()
    carpeta = carpeta_segura()
    try:
        prueba_cache(filas, ventanas, carpeta)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    prueba_determinismo(p, events, filas)
    prueba_agregados(filas, ventanas)
    prueba_main(p, filas)
    print("\n" + ("TODO BIEN" if not FALLOS else "FALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS))))
    return 1 if FALLOS else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
