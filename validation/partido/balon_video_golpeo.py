"""El golpeo de cada reinicio, con el balón del vídeo táctico: dónde acaba de verdad cada parada (pieza de `D`).

**Solo lo ejecuta una persona, en local** (regla nº 1 de `CLAUDE.md`): lee el vídeo, el ATD, la homografía y el Smart
Tagging del partido, y una entrega nuestra. Claude no lo ejecuta. La prueba sin datos es
`validation/scripts/prueba_balon_video_golpeo.py`. La regla (constantes, candidatos de la capa y criterios de daño) se
escribió antes de ejecutarlo: `docs/decisiones.md`, 16/11, «el final de cada parada en el golpeo del balón del vídeo».

**Las ventanas:** las `SET PIECES` del Smart Tagging que no son saques iniciales y empiezan en un tramo evaluado
(`dead_ball.restart_windows`, las mismas de la capa del hueco y del instante del reinicio).

**El seguidor** (uno por ventana), con la variante fijada del detector (`validation/balon_video/detector.py`: recorte de
320 px ampliado ×2, confianza 0,10, 4 hilos, CPU):
- recorre hacia delante los frames de `desde` a `hasta`. `desde` es la última posición del balón del ATD antes de la
  ventana, si está a `HUECO_MAX` frames o menos de su inicio (si no, el inicio). `hasta` es el `limite` del golpeo más
  `HUECO_FECHA` + `MOVER` frames, para poder confirmar un golpeo justo antes del límite;
- en cada frame centra el recorte en la última detección aceptada si tiene `RECENTRAR` frames o menos; si no, en el
  balón del ATD en t+4 (si lo ve: «captar»); si no, en la última detección aceptada si tiene `PERDIDO` frames o menos;
  si no, no detecta;
- **siguiendo**, acepta la detección más cercana (en píxeles) a la última aceptada, a `SALTO_PX` px por frame desde ella
  como mucho (con un tope de `SALTO_MAX` px); **captando**, la más cercana (en metros) al balón del ATD en t+4, a
  `RADIO_CAPTAR` m o menos. Empates: el orden del detector (más confianza, menor x, menor y);
- cada vez que capta el balón sin tenerlo (la primera vez, o tras más de `PERDIDO` frames sin detección aceptada),
  vuelve **hacia atrás** desde ese frame, siguiendo con las mismas reglas, hasta `ATRAS` frames como mucho, sin pasar de
  la última detección aceptada ni de `desde − ATRAS`, y se para si lleva más de `PERDIDO` frames sin aceptar. Así se
  cubren los dos arranques del encargo: la última posición del ATD antes del hueco (el primer frame del recorrido) y su
  reaparición (la captura que llega después del hueco), con el recorte siempre en la última detección.

**El golpeo** (`buscar_eventos`, sobre las detecciones aceptadas en metros del campo, con la inversa de la homografía):
el primer frame en que el balón, quieto 1 s o más, empieza a moverse. Un evento es un par de detecciones seguidas
(t_quieto, t_mov) con:
1. **quieto:** en los `QUIETO` frames que acaban en t_quieto hay `MIN_QUIETO` detecciones o más, todas a `RADIO_QUIETO`
   m o menos de su mediana;
2. **arranca:** t_mov − t_quieto ≤ `HUECO_FECHA` + 1, y la detección de t_mov está a más de `RADIO_QUIETO` de la mediana;
3. **se mueve:** en los `MOVER` frames desde t_mov hay `MIN_MOVER` detecciones o más, todas a más de `RADIO_QUIETO` de la
   mediana, y la más lejana a `RADIO_MOVER` m o más;
4. **sitio posible para el tipo** (reglamento, `posicion_posible`): córner, a `RADIO_CORNER` m de una esquina; saque de
   puerta, en el área pequeña más `MARGEN_AREA`; saque de banda, a `BANDA` m de una banda; lo demás, en el campo más
   `MARGEN_CAMPO`.

El golpeo es t_quieto + 1. Con todos los eventos de la ventana (`clasificar`): si no hay ninguno antes del `limite`
(el fin de la ventana menos `MARGEN_FIN`, el siguiente reinicio o el fin del tramo, lo que llegue antes), «sin golpeo»
(o «fuera de plazo» si lo hay después, o «sin balón» si nunca se aceptó una detección); si el primero cae antes del
inicio de la ventana, «antes de la ventana»; si hay dos o más entre el inicio y el límite, «ambiguo»; si hay uno,
«golpeo». **Solo los «golpeo» los usa la capa** (`possession/balon_video.py`, `golpeo_desde_hueco` y
`golpeo_desde_ventana`). La última posición del ATD solo cuenta si cae en el mismo tramo evaluado que el inicio de la
ventana, y el recorrido no pasa del fin de ese tramo.

**La caché:** `MTAH_DATA_DIR/tactical/BAR-ATH_tactical_golpeos.npz` (el nombre lo bloquea `.claude/settings.json`), una
fila por ventana en su orden, con `metadatos` (la variante, las constantes, el sha256 del modelo y del código, la
huella de las ventanas y del vídeo), `informativo` (commit y tiempos) y `huella` (sha256 de los arrays). Se escribe de
forma atómica. No es reanudable: si se corta, se vuelve a lanzar.

**Lo que imprime** (un JSON, solo agregados; las celdas de 1 a 4 ventanas de las tablas salen como «< 5», salvo los
totales por estado de `por_estado`, que van exactos porque el criterio 4 necesita el número de «golpeo»): cuántas
ventanas hay de cada tipo y en qué estado quedan; dónde cae el golpeo dentro de la ventana; frente a la reaparición del
balón del ATD; frente
al final de nuestro `D` en una entrega (`--entrega`, por defecto `equipo_v8`, con su sha256); cuánto dura el reposo;
la precisión de la fecha; los eventos descartados por el sitio; detecciones, capturas y tiempos; y la huella. Por
stderr, los pasos (sin cifras) y el % hecho. Si falla, solo el tipo de error y las líneas del código.

Uso, desde la raíz del repo, con el entorno del detector (torch, ultralytics, opencv, numpy y pandas):

    python validation/partido/balon_video_golpeo.py                       # busca los golpeos y escribe la caché
    python validation/partido/balon_video_golpeo.py --resumen             # los agregados de la caché ya hecha
    python validation/partido/balon_video_golpeo.py --resumen --entrega prueba_golpeo_ventana   # frente a otra entrega
    python validation/partido/balon_video_golpeo.py --forzar              # rehace la caché
"""

import argparse
import collections
import hashlib
import importlib.util
import json
import os
import sys
import time
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "validation", "balon_video"))
sys.path.insert(0, os.path.join(RAIZ, "evaluation"))
sys.path.insert(0, AQUI)
import games  # noqa: E402
from possession import ball, dead_ball, tracking  # noqa: E402
from possession.ball import BALL_LEAD  # noqa: E402
import detector as det  # noqa: E402
import balon_video_sondeo as bs  # noqa: E402   (desplazado, informe_de_error)
import balon_video_detectar as bvd  # noqa: E402   (commit_del_codigo, huella_del_video, sha256_de_ficheros)

FICHEROS = ["video", "atd_meta", "atd_raw", "homography", "smart_tagging"]
NOMBRE_CACHE = "BAR-ATH_tactical_golpeos.npz"
NOMBRE_PRUEBA = NOMBRE_CACHE + ".prueba"  # la prueba de escritura en tactical/ (también con el prefijo)
SUFIJO_TEMPORAL = ".escribiendo"  # el temporal conserva el prefijo BAR-ATH_tactical_ (lo bloquea settings.json)
FORMATO = 1
RESULTADOS = os.path.join(RAIZ, "evaluation", "results")
ENTREGA = "equipo_v8"  # la vigente desde el 16/11 (CLAUDE.md, «Dónde estamos»)
CODIGO = (os.path.join(RAIZ, "validation", "balon_video", "detector.py"), os.path.abspath(__file__))
ANCHO_IMAGEN, ALTO_IMAGEN = bs.ANCHO_IMAGEN, bs.ALTO_IMAGEN
DECIMALES_M = 6  # metros redondeados a 1 µm, como la caché del partido entero (la inversa puede cambiar el último bit)
MINIMO_CELDA = 5

# -- las constantes de la regla (docs/decisiones.md, 16/11), fijadas antes de ejecutar nada del partido -------------
# Todas sin ajustar: a priori, del reglamento o, en el caso de MARGEN_FIN, de agregados de este partido sin etiquetas.
# El golpeo: «el primer frame en que el balón, quieto 1 s o más, empieza a moverse» (el encargo).
QUIETO = 25  # frames: 1 s quieto
MIN_QUIETO = 13  # detecciones aceptadas en esos 25 frames, como mínimo (más de la mitad: el que saca tapa el balón)
RADIO_QUIETO = 0.5  # m: todas a esto o menos de su mediana (el temblor del detector es de centímetros)
HUECO_FECHA = 12  # frames sin detección, como mucho, entre la última quieta y la primera en movimiento (0,5 s)
MOVER = 10  # frames desde la primera detección en movimiento (0,4 s)
MIN_MOVER = 3  # detecciones en esos 10 frames, como mínimo, todas a más de RADIO_QUIETO de la mediana
RADIO_MOVER = 2.0  # m: la más lejana, a esto o más de la mediana (un pase a 5 m/s recorre 2 m en 0,4 s)
# El seguidor.
PERDIDO = 25  # frames sin detección aceptada: el balón se da por perdido (1 s)
SALTO_PX = 40  # px por frame desde la última detección aceptada (40 m/s a unos 25 px/m)
SALTO_MAX = 120  # px: tope de esa puerta, para no saltar a otro objeto del recorte tras un fallo largo
RECENTRAR = 5  # frames: con la última detección más vieja, si el ATD ve el balón el recorte va al ATD
RADIO_CAPTAR = 3.0  # m: captar es una detección a esto o menos del balón del ATD en t+4 (RADIO_ACIERTO de la 1b)
ATRAS = 250  # frames (10 s): lo más que se vuelve hacia atrás desde cada captura (memoria: ~1,5 GB de frames)
# frames (5 s): el golpeo, antes del fin de la ventana menos esto. Sale de este partido, de agregados sin etiquetas
# (14/11: el detector de golpeo con el balón del ATD daba la reanudación más de 5 s antes del fin en las 53 ventanas).
MARGEN_FIN = 125
HUECO_MAX = 1500  # frames (60 s): el recorrido empieza en la última posición del ATD si está a esto o menos
# El sitio del golpeo según el tipo (reglamento; metros del campo, con el origen en una esquina).
RADIO_CORNER = 3.0  # m de una esquina
AREA_CHICA_FONDO, AREA_CHICA_MEDIO_ANCHO = 5.5, 9.16  # m: el área pequeña (5,5 m y 18,32 m de ancho)
MARGEN_AREA = 2.0  # m alrededor del área pequeña
BANDA = 5.0  # m de una banda, a un lado u otro (el balón va en las manos: su proyección se aparta de la línea)
MARGEN_CAMPO = 2.0  # m fuera de las líneas

CONSTANTES = {
    "QUIETO": QUIETO, "MIN_QUIETO": MIN_QUIETO, "RADIO_QUIETO": RADIO_QUIETO, "HUECO_FECHA": HUECO_FECHA,
    "MOVER": MOVER, "MIN_MOVER": MIN_MOVER, "RADIO_MOVER": RADIO_MOVER, "PERDIDO": PERDIDO, "SALTO_PX": SALTO_PX,
    "SALTO_MAX": SALTO_MAX, "RECENTRAR": RECENTRAR, "RADIO_CAPTAR": RADIO_CAPTAR, "ATRAS": ATRAS,
    "MARGEN_FIN": MARGEN_FIN, "HUECO_MAX": HUECO_MAX, "RADIO_CORNER": RADIO_CORNER,
    "AREA_CHICA_FONDO": AREA_CHICA_FONDO, "AREA_CHICA_MEDIO_ANCHO": AREA_CHICA_MEDIO_ANCHO,
    "MARGEN_AREA": MARGEN_AREA, "BANDA": BANDA, "MARGEN_CAMPO": MARGEN_CAMPO,
}

# Estados de cada ventana.
GOLPEO = "golpeo"
ANTES = "antes de la ventana"
AMBIGUO = "ambiguo"
SIN_GOLPEO = "sin golpeo"
FUERA_DE_PLAZO = "fuera de plazo"
SIN_BALON = "sin balón"
ESTADOS = (GOLPEO, ANTES, AMBIGUO, SIN_GOLPEO, FUERA_DE_PLAZO, SIN_BALON)

TIPOS = ("throw-in", "corner kick", "goal kick", "free kick")  # los de la tabla; otro tipo sale como «otros»

# Columnas de la caché: una fila por ventana.
ENTEROS = ("inicio", "fin", "corte", "limite", "desde", "hasta", "reaparicion", "golpeo", "ultimo_quieto",
           "primer_movimiento", "inicio_quieto", "intentos", "aceptadas", "capturas", "atras",
           "descartados_por_sitio")
REALES = ("x_m", "y_m")
TEXTOS = ("tipo", "estado", "estado_hueco")


class ErrorGolpeo(Exception):
    """Un error con un mensaje sin datos del partido (se puede imprimir tal cual)."""


# -- las ventanas ----------------------------------------------------------------------------------------------------

def preparar_ventanas(trk, events):
    """[dict] de las ventanas `SET PIECES` que no son saques iniciales y empiezan en un tramo evaluado, en su orden.

    Cada una lleva: `inicio` y `fin` (el fin sin incluir), `tipo`, `corte` (inicio del siguiente `GOALS` o `SET
    PIECES`, `dead_ball.next_restart`; −1 si no hay), `limite` (el golpeo tiene que ser anterior: el fin menos
    MARGEN_FIN, el corte o el fin del tramo), `desde` y `hasta` (lo que recorre el seguidor hacia delante),
    `reaparicion` (si el ATD no ve el balón en t+4 en el frame anterior al inicio, el primer frame desde el inicio en
    que lo ve; si no, −1; descriptiva) y `estado_hueco` (el de la capa del hueco, `dead_ball.gaps_before_restarts`).
    """
    fps = int(trk.fps)
    rx, ry = bs.desplazado(trk.bx, BALL_LEAD), bs.desplazado(trk.by, BALL_LEAD)
    visto = dead_ball.last_seen_before(rx, ry)
    huecos = {id(w): estado for w, estado, _ in dead_ball.gaps_before_restarts(trk.bx, trk.by, events, fps)}
    vistos = np.flatnonzero(np.isfinite(rx) & np.isfinite(ry))
    ventanas = []
    for w in dead_ball.restart_windows(events):
        w0, w1 = int(w["start"]), int(w["end"])
        bloque = [(a, b) for a, b in trk.blocks if a <= w0 < b]
        if not bloque:
            continue
        a, b = bloque[0]
        corte = dead_ball.next_restart(events, w)
        limite = int(min(w1 - MARGEN_FIN, corte, b))
        ultimo = int(visto[w0 - 1]) if w0 >= 1 else -1
        desde = ultimo if ultimo >= max(a, w0 - HUECO_MAX) else w0
        hasta = int(min(limite + HUECO_FECHA + MOVER, b))
        # La reaparición solo existe si el ATD no veía el balón en el frame anterior al inicio.
        j = int(np.searchsorted(vistos, w0))
        reaparicion = (int(vistos[j]) if ultimo < w0 - 1 and j < len(vistos) and vistos[j] < b else -1)
        ventanas.append({"inicio": w0, "fin": w1, "tipo": w["type"], "corte": -1 if not np.isfinite(corte) else
                         int(corte), "limite": limite, "desde": int(desde), "hasta": hasta, "bloque": (a, b),
                         "reaparicion": reaparicion, "estado_hueco": huecos.get(id(w), "")})
    return ventanas


def huella_ventanas(ventanas):
    """sha256 de la lista (inicio, fin, tipo) de las ventanas: la capa la recalcula con el Smart Tagging y la compara."""
    texto = "".join("{},{},{}\n".format(int(v["inicio"]), int(v["fin"]), v["tipo"]) for v in ventanas)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def fotogramas_a_leer(ventanas):
    """Los frames que se decodifican, en orden: la unión de [desde − ATRAS, hasta) de todas las ventanas."""
    marcas = set()
    for v in ventanas:
        marcas.update(range(max(0, v["desde"] - ATRAS), v["hasta"]))
    return np.array(sorted(marcas), dtype=np.int64)


# -- el sitio del golpeo según el tipo (reglamento) ------------------------------------------------------------------

def posicion_posible(tipo, x, y, pitch):
    """Si un balón quieto en (x, y) metros puede ser el de un reinicio de ese `tipo`. Reglamento, no el partido."""
    largo, ancho = float(pitch[0]), float(pitch[1])
    if not (np.isfinite(x) and np.isfinite(y)):
        return False
    en_campo = -MARGEN_CAMPO <= x <= largo + MARGEN_CAMPO and -MARGEN_CAMPO <= y <= ancho + MARGEN_CAMPO
    if tipo == "corner kick":
        esquinas = ((0.0, 0.0), (0.0, ancho), (largo, 0.0), (largo, ancho))
        return min(np.hypot(x - ex, y - ey) for ex, ey in esquinas) <= RADIO_CORNER
    if tipo == "goal kick":
        fondo = AREA_CHICA_FONDO + MARGEN_AREA
        cerca_de_un_fondo = (-MARGEN_CAMPO <= x <= fondo) or (largo - fondo <= x <= largo + MARGEN_CAMPO)
        return cerca_de_un_fondo and abs(y - ancho / 2.0) <= AREA_CHICA_MEDIO_ANCHO + MARGEN_AREA
    if tipo == "throw-in":
        return (-MARGEN_CAMPO <= x <= largo + MARGEN_CAMPO) and (abs(y) <= BANDA or abs(y - ancho) <= BANDA)
    return en_campo


# -- el golpeo -------------------------------------------------------------------------------------------------------

def buscar_eventos(frames, xm, ym, tipo, pitch):
    """(eventos, descartados_por_sitio): los eventos «quieto y arranca» de las detecciones aceptadas, en su orden.

    `frames` en orden creciente y sin repetir, con `xm`, `ym` en metros (finitos). Cada evento es un dict con `golpeo`
    (t_quieto + 1), `ultimo_quieto`, `primer_movimiento`, `inicio_quieto` (la primera detección de la racha quieta que
    acaba en t_quieto: todas a RADIO_QUIETO o menos de la mediana y sin más de HUECO_FECHA frames seguidos sin detección
    entre dos de ellas; solo es descriptivo) y `x_m`, `y_m` (la mediana del reposo). Los que cumplen 1 a 3 pero no el
    sitio (4) no son eventos: se cuentan en `descartados_por_sitio`.
    """
    f = np.asarray(frames, dtype=np.int64)
    x, y = np.asarray(xm, dtype=np.float64), np.asarray(ym, dtype=np.float64)
    eventos, descartados = [], 0
    for j in range(len(f) - 1):
        t_quieto, t_mov = int(f[j]), int(f[j + 1])
        if t_mov - t_quieto > HUECO_FECHA + 1:
            continue
        lo = int(np.searchsorted(f, t_quieto - QUIETO + 1))
        if j + 1 - lo < MIN_QUIETO:
            continue
        mx, my = float(np.median(x[lo:j + 1])), float(np.median(y[lo:j + 1]))
        if np.any(np.hypot(x[lo:j + 1] - mx, y[lo:j + 1] - my) > RADIO_QUIETO):
            continue
        if np.hypot(x[j + 1] - mx, y[j + 1] - my) <= RADIO_QUIETO:
            continue
        hi = int(np.searchsorted(f, t_mov + MOVER))
        dist = np.hypot(x[j + 1:hi] - mx, y[j + 1:hi] - my)
        if hi - (j + 1) < MIN_MOVER or np.any(dist <= RADIO_QUIETO) or float(np.max(dist)) < RADIO_MOVER:
            continue
        if not posicion_posible(tipo, mx, my, pitch):
            descartados += 1
            continue
        i = j
        while (i - 1 >= 0 and f[i] - f[i - 1] <= HUECO_FECHA + 1
               and np.hypot(x[i - 1] - mx, y[i - 1] - my) <= RADIO_QUIETO):
            i -= 1
        eventos.append({"golpeo": t_quieto + 1, "ultimo_quieto": t_quieto, "primer_movimiento": t_mov,
                        "inicio_quieto": int(f[i]), "x_m": mx, "y_m": my})
    return eventos, descartados


def clasificar(eventos, inicio, limite, con_balon=True):
    """(estado, evento): qué se hace con los eventos de una ventana (ver el docstring del módulo)."""
    if not con_balon:
        return SIN_BALON, None
    if not eventos:
        return SIN_GOLPEO, None
    validos = [e for e in eventos if e["golpeo"] < limite]
    if not validos:
        return FUERA_DE_PLAZO, eventos[0]
    if validos[0]["golpeo"] < inicio:
        return ANTES, validos[0]
    if len(validos) >= 2:
        return AMBIGUO, validos[0]
    return GOLPEO, validos[0]


# -- el seguidor -----------------------------------------------------------------------------------------------------

def elegir_siguiendo(dets, xm, ym, centro, edad):
    """Índice de la detección más cercana (px) a `centro`, a min(SALTO_PX·edad, SALTO_MAX) px o menos y con metros
    finitos; None si no hay. Empates: la primera en el orden del detector."""
    if not len(dets):
        return None
    dist = np.hypot(dets[:, 0] - centro[0], dets[:, 1] - centro[1])
    ok = np.flatnonzero((dist <= min(SALTO_PX * edad, SALTO_MAX)) & np.isfinite(xm) & np.isfinite(ym))
    return None if not len(ok) else int(ok[np.argmin(dist[ok])])


def elegir_captando(xm, ym, ax, ay):
    """Índice de la detección más cercana (m) al balón del ATD (ax, ay), a RADIO_CAPTAR m o menos; None si no hay."""
    if not len(xm):
        return None
    with np.errstate(invalid="ignore"):
        dist = np.hypot(xm - ax, ym - ay)
        ok = np.flatnonzero(np.isfinite(dist) & (dist <= RADIO_CAPTAR))
    return None if not len(ok) else int(ok[np.argmin(dist[ok])])


class Seguidor:
    """El seguidor de una ventana: recorre sus frames hacia delante y vuelve hacia atrás en cada captura."""

    def __init__(self, ventana, rx, ry, matrices, validas, pitch, detector):
        self.v = ventana
        self.rx, self.ry = rx, ry
        self.matrices, self.validas = matrices, validas
        self.largo, self.ancho = float(pitch[0]), float(pitch[1])
        self.detector = detector
        self.pista = {}  # frame -> (x_px, y_px, x_m, y_m, conf), solo las aceptadas
        self.ultimo = None  # (frame, x_px, y_px) de la última aceptada hacia delante
        self.intentos = self.capturas = self.atras = 0
        self.segundos = 0.0

    def activo(self, t):
        return self.v["desde"] <= t < self.v["hasta"]

    def _detectar(self, t, imagen, centro):
        self.intentos += 1
        inicio = time.perf_counter()
        dets = np.asarray(self.detector(imagen, (float(centro[0]), float(centro[1]))), dtype=np.float64)
        self.segundos += time.perf_counter() - inicio
        if dets.size == 0:
            return np.zeros((0, 5)), np.zeros(0), np.zeros(0)
        if dets.ndim != 2 or dets.shape[1] != 5:
            raise ErrorGolpeo("el detector no devuelve un array (k, 5)")
        xm, ym = det.campo_desde_pixeles(self.matrices[t], dets[:, 0], dets[:, 1], self.largo, self.ancho)
        return dets, np.round(np.asarray(xm, float), DECIMALES_M), np.round(np.asarray(ym, float), DECIMALES_M)

    def _valida(self, t):
        return bool(self.validas[t]) and bool(np.isfinite(self.matrices[t]).all())

    def paso(self, t, imagen, memoria):
        """Un frame hacia delante. `memoria`: los frames anteriores seguidos, como (frame, imagen), el último el t."""
        if not self.activo(t) or not self._valida(t):
            return
        edad = None if self.ultimo is None else t - self.ultimo[0]
        captando = False
        if edad is not None and edad <= RECENTRAR:
            centro = self.ultimo[1:]
        elif np.isfinite(self.rx[t]) and np.isfinite(self.ry[t]):
            cx, cy = det.pixeles_desde_campo(self.matrices[t], self.rx[t], self.ry[t], self.largo, self.ancho)
            if np.isfinite(cx) and np.isfinite(cy):
                centro, captando = (float(cx), float(cy)), True
            elif edad is not None and edad <= PERDIDO:
                centro = self.ultimo[1:]
            else:
                return
        elif edad is not None and edad <= PERDIDO:
            centro = self.ultimo[1:]
        else:
            return
        dets, xm, ym = self._detectar(t, imagen, centro)
        i = (elegir_captando(xm, ym, self.rx[t], self.ry[t]) if captando
             else elegir_siguiendo(dets, xm, ym, centro, edad))
        if i is None:
            return
        self.pista[t] = (float(dets[i, 0]), float(dets[i, 1]), float(xm[i]), float(ym[i]), float(dets[i, 4]))
        anterior = self.ultimo
        self.ultimo = (t, float(dets[i, 0]), float(dets[i, 1]))
        if anterior is None or t - anterior[0] > PERDIDO:
            self.capturas += 1
            self._hacia_atras(t, None if anterior is None else anterior[0], memoria)

    def _hacia_atras(self, t, ultimo_aceptado, memoria):
        """Desde la captura en t, hacia atrás por `memoria`, con las reglas de seguir."""
        tope = max(t - ATRAS, self.v["desde"] - ATRAS, -1 if ultimo_aceptado is None else ultimo_aceptado + 1)
        ultimo = (t, self.pista[t][0], self.pista[t][1])
        for s, imagen in reversed(memoria):
            if s >= t:
                continue
            if s < tope or ultimo[0] - s > PERDIDO:
                break
            if not self._valida(s):
                continue
            self.atras += 1
            dets, xm, ym = self._detectar(s, imagen, ultimo[1:])
            i = elegir_siguiendo(dets, xm, ym, ultimo[1:], ultimo[0] - s)
            if i is None:
                continue
            self.pista[s] = (float(dets[i, 0]), float(dets[i, 1]), float(xm[i]), float(ym[i]), float(dets[i, 4]))
            ultimo = (s, float(dets[i, 0]), float(dets[i, 1]))

    def resultado(self, pitch):
        """La fila de la caché de esta ventana (sin `tipo` ni los datos de la ventana, que añade `ejecutar`)."""
        frames = np.array(sorted(self.pista), dtype=np.int64)
        xm = np.array([self.pista[int(t)][2] for t in frames], dtype=np.float64)
        ym = np.array([self.pista[int(t)][3] for t in frames], dtype=np.float64)
        eventos, descartados = buscar_eventos(frames, xm, ym, self.v["tipo"], pitch)
        estado, ev = clasificar(eventos, self.v["inicio"], self.v["limite"], con_balon=len(frames) > 0)
        fila = {"estado": estado, "golpeo": -1, "ultimo_quieto": -1, "primer_movimiento": -1, "inicio_quieto": -1,
                "x_m": np.nan, "y_m": np.nan, "intentos": self.intentos, "aceptadas": int(len(frames)),
                "capturas": self.capturas, "atras": self.atras, "descartados_por_sitio": descartados}
        if ev is not None:
            fila.update({k: ev[k] for k in ("golpeo", "ultimo_quieto", "primer_movimiento", "inicio_quieto",
                                             "x_m", "y_m")})
        return fila


def ejecutar(ventanas, abrir_fuente, detector, trk, matrices, validas, progreso=None):
    """La búsqueda de punta a punta sobre datos ya cargados. Devuelve (filas, recuento).

    - `abrir_fuente(frames)`: un iterable de (frame, imagen) con exactamente esos frames, en orden (en el partido,
      `detector.leer_frames` sobre el vídeo, que empieza a leer en el frame 0).
    - `detector(imagen, centro)`: un array (k, 5) [x, y, w, h, conf] en píxeles del frame (`detector.detectar`).
    - `progreso(fraccion)`: se llama cada 1 % de los frames leídos (solo depende de cuántos son).
    La memoria guarda los ATRAS + 1 últimos frames seguidos; un salto en la lista la vacía. Es una defensa (y libera
    memoria): la vuelta hacia atrás nunca baja de `desde − ATRAS`, así que solo usa frames del tramo seguido de su ventana.
    """
    n = len(trk.bx)
    if len(matrices) != n or len(validas) != n:
        raise ErrorGolpeo("la homografía no tiene un frame por frame de vídeo")
    rx, ry = bs.desplazado(trk.bx, BALL_LEAD), bs.desplazado(trk.by, BALL_LEAD)
    seguidores = [Seguidor(v, rx, ry, matrices, validas, trk.pitch, detector) for v in ventanas]
    frames = fotogramas_a_leer(ventanas)
    memoria = collections.deque(maxlen=ATRAS + 1)
    paso_progreso = max(1, len(frames) // 100)
    leidos, anterior = 0, None
    iterador = iter(abrir_fuente(frames))
    for esperado in frames.tolist():
        try:
            t, imagen = next(iterador)
        except StopIteration:
            raise ErrorGolpeo("la fuente de frames se acaba antes de la lista")
        if int(t) != esperado:
            raise ErrorGolpeo("la fuente de frames no da los frames de la lista en orden")
        if anterior is not None and esperado != anterior + 1:
            memoria.clear()
        memoria.append((esperado, imagen))
        for s in seguidores:
            if s.activo(esperado):
                s.paso(esperado, imagen, memoria)
        anterior = esperado
        leidos += 1
        if progreso is not None and (leidos % paso_progreso == 0 or leidos == len(frames)):
            progreso(leidos / float(len(frames)))
    try:
        next(iterador)  # con `hasta_el_final`, aquí el lector decodifica el resto del vídeo y cuenta sus frames
        raise ErrorGolpeo("la fuente de frames da más frames que la lista")
    except StopIteration:
        pass
    filas = []
    for v, s in zip(ventanas, seguidores):
        fila = s.resultado(trk.pitch)
        fila.update({k: v[k] for k in ("inicio", "fin", "tipo", "corte", "limite", "desde", "hasta", "reaparicion",
                                       "estado_hueco")})
        filas.append(fila)
    recuento = {"frames_leidos": leidos, "intentos": int(sum(s.intentos for s in seguidores)),
                "segundos_detectando": round(sum(s.segundos for s in seguidores), 1)}
    return filas, recuento


# -- la caché --------------------------------------------------------------------------------------------------------

def arrays_de(filas):
    """{columna: array} de las filas, con los tipos fijos de la caché."""
    salida = {k: np.array([int(f[k]) for f in filas], dtype=np.int64) for k in ENTEROS}
    salida.update({k: np.array([float(f[k]) for f in filas], dtype=np.float64) for k in REALES})
    salida.update({k: np.array([str(f[k]) for f in filas], dtype=np.str_) for k in TEXTOS})
    return salida


def filas_de(arrays):
    """Las filas de unos arrays de la caché (lo contrario de `arrays_de`)."""
    n = len(arrays["inicio"])
    return [dict({k: int(arrays[k][i]) for k in ENTEROS}, **{k: float(arrays[k][i]) for k in REALES},
                 **{k: str(arrays[k][i]) for k in TEXTOS}) for i in range(n)]


def huella(arrays):
    """sha256 de las columnas, en orden fijo, con su nombre, tipo y forma; los textos en UTF-8, uno por línea. Los NaN
    y los −0,0 se normalizan. Copiada en possession/balon_video.py (la prueba lo comprueba)."""
    h = hashlib.sha256()
    for nombre in ENTEROS + REALES:
        tipo = "<i8" if nombre in ENTEROS else "<f8"
        a = np.ascontiguousarray(np.asarray(arrays[nombre], dtype=tipo))
        if a.dtype.kind == "f":
            a = np.ascontiguousarray(np.where(np.isnan(a), np.nan, a + 0.0), dtype=tipo)
        h.update("{}|{}|{}\n".format(nombre, tipo, ",".join(str(s) for s in a.shape)).encode("ascii"))
        h.update(a.tobytes())
    for nombre in TEXTOS:
        valores = [str(v) for v in np.asarray(arrays[nombre]).tolist()]
        h.update("{}|texto|{}\n".format(nombre, len(valores)).encode("ascii"))
        h.update("".join(v + "\n" for v in valores).encode("utf-8"))
    return h.hexdigest()


def metadatos_de(game, n_frames, pitch, modelo_sha256, versiones, hilos, codigo_sha256, ventanas, video=None):
    """La llave de la caché: todo lo que puede cambiar los arrays. Nada de tiempos ni de commits."""
    return {"formato": FORMATO, "partido": game, "frames_del_video": int(n_frames),
            "campo": [float(pitch[0]), float(pitch[1])], "modelo_sha256": modelo_sha256,
            "variante": {"recorte_px": int(det.LADO), "factor": float(det.FACTOR), "conf": float(det.CONF),
                         "adelanto_atd": int(BALL_LEAD), "max_det": int(det.MAX_DET),
                         "decimales_px": int(det.DECIMALES_PX), "decimales_conf": int(det.DECIMALES_CONF),
                         "decimales_m": int(DECIMALES_M), "dispositivo": "cpu"},
            "constantes": dict(CONSTANTES), "hilos": int(hilos), "versiones": versiones,
            "codigo_sha256": codigo_sha256, "ventanas": {"n": len(ventanas), "sha256": huella_ventanas(ventanas)},
            "video": video}


def guardar(ruta, arrays, metadatos, informativo, huella_):
    """Escritura atómica: un temporal en la misma carpeta (con el mismo prefijo) y `os.replace` (con reintentos)."""
    temporal = ruta + SUFIJO_TEMPORAL
    try:
        with open(temporal, "wb") as f:
            np.savez(f, metadatos=np.array(json.dumps(metadatos, sort_keys=True)),
                     informativo=np.array(json.dumps(informativo, sort_keys=True)), huella=np.array(huella_),
                     **{k: arrays[k] for k in ENTEROS + REALES + TEXTOS})
            f.flush()
            os.fsync(f.fileno())
        bvd._reemplazar(temporal, ruta)
    finally:
        bvd._borrar_si_se_puede(temporal)
    return ruta


def leer(ruta):
    """{"arrays", "metadatos", "informativo", "huella"} de una caché. Se cierra antes de devolver."""
    try:
        with np.load(ruta, allow_pickle=False) as z:
            arrays = {k: np.asarray(z[k]) for k in ENTEROS + REALES + TEXTOS}
            salida = {"arrays": arrays, "metadatos": json.loads(str(z["metadatos"])),
                      "informativo": json.loads(str(z["informativo"])), "huella": str(z["huella"])}
    except Exception:
        raise ErrorGolpeo("no se puede leer {} o le falta algo".format(os.path.basename(ruta))) from None
    largos = {len(salida["arrays"][k]) for k in ENTEROS + REALES + TEXTOS}
    if len(largos) != 1:
        raise ErrorGolpeo("{} no tiene la forma esperada".format(os.path.basename(ruta)))
    return salida


def probar_escritura(carpeta):
    """Antes de leer el vídeo: escribe (con `guardar`) y borra un fichero de prueba en `carpeta`."""
    ruta = os.path.join(carpeta, NOMBRE_PRUEBA)
    vacio = arrays_de([])
    try:
        guardar(ruta, vacio, {}, {}, "")
    except OSError:
        bvd._borrar_si_se_puede(ruta)
        raise ErrorGolpeo("no se puede escribir en la carpeta de los datos del partido (tactical/)") from None
    bvd._borrar_si_se_puede(ruta)


# -- los agregados ---------------------------------------------------------------------------------------------------

def celda(n, minimo=MINIMO_CELDA):
    """Un recuento de ventanas: de 1 a 4 sale como «< 5»."""
    n = int(n)
    return "< {}".format(minimo) if 0 < n < minimo else n


def repartir(valores, bordes, etiquetas):
    """{etiqueta: «celda»} de cuántos `valores` caen en cada intervalo [bordes[i], bordes[i+1]). Los bordes de los
    extremos pueden ser infinitos; un valor fuera de todos los intervalos no se cuenta (los de aquí los cubren)."""
    cuenta = np.histogram(np.asarray(valores, dtype=np.float64), bins=np.asarray(bordes, dtype=np.float64))[0]
    return {e: celda(c) for e, c in zip(etiquetas, cuenta)}


def tipo_de_tabla(tipo):
    return tipo if tipo in TIPOS else "otros"


def mediana_s(valores, fps):
    """La mediana en segundos (1 decimal) con 5 valores o más; si no, None."""
    valores = np.asarray(valores, dtype=np.float64)
    return round(float(np.median(valores)) / fps, 1) if len(valores) >= MINIMO_CELDA else None


INF = float("inf")


def fin_de_nuestro_d(codes, bloque, inicio, golpeo, fps):
    """El final (sin incluir) de nuestra parada en esa ventana, o None: el de la última racha de `D` que empieza antes
    del golpeo + 10 s y acaba después del inicio de la ventana − 10 s, dentro del tramo."""
    a, b = bloque
    margen = 10 * fps
    trozo = (np.asarray(codes[a:b]) == tracking.D).astype(np.int8)
    bordes = np.diff(np.concatenate(([0], trozo, [0])))
    empiezan, acaban = np.flatnonzero(bordes == 1) + a, np.flatnonzero(bordes == -1) + a
    elegidas = [(s, e) for s, e in zip(empiezan.tolist(), acaban.tolist())
                if s < golpeo + margen and e > inicio - margen]
    return None if not elegidas else max(elegidas)[1]


def agregados(filas, fps, codes=None, bloques=None):
    """Los agregados de la búsqueda (solo recuentos y medianas; ningún frame). Con `codes` (una entrega), también
    `frente_a_nuestro_d`, en los tramos `bloques` (por defecto, los evaluados del partido)."""
    por_tipo = collections.OrderedDict()
    for f in filas:
        t = tipo_de_tabla(f["tipo"])
        por_tipo.setdefault(t, collections.Counter())[f["estado"]] += 1
    tabla = {t: dict({"ventanas": celda(sum(c.values()))}, **{e: celda(c[e]) for e in ESTADOS})
             for t, c in por_tipo.items()}
    total = collections.Counter(f["estado"] for f in filas)
    con = [f for f in filas if f["estado"] == GOLPEO]
    salida = {
        "ventanas": len(filas),
        "por_estado": {e: int(total[e]) for e in ESTADOS},
        "por_tipo": tabla,
        "golpeo_desde_el_inicio_de_la_ventana_s": repartir(
            [(f["golpeo"] - f["inicio"]) / fps for f in con], [0, 2, 4, 6, 8, 10, 15, 20, INF],
            ["0-2", "2-4", "4-6", "6-8", "8-10", "10-15", "15-20", ">=20"]),
        "golpeo_hasta_el_fin_de_la_ventana_s": repartir(
            [(f["fin"] - f["golpeo"]) / fps for f in con], [-INF, 5, 10, 20, INF], ["<5", "5-10", "10-20", ">=20"]),
        "golpeo_frente_a_la_reaparicion_del_atd_s": repartir(
            [(f["golpeo"] - f["reaparicion"]) / fps for f in con if f["reaparicion"] >= 0],
            [-INF, -5, -1, 0, 1, 5, INF], ["<-5 (reaparece >5 s después)", "-5 a -1", "-1 a 0", "0 a 1", "1 a 5",
                                          ">=5 (reaparece >5 s antes)"]),
        "golpeo_con_hueco_antes_de_la_ventana": celda(sum(f["estado_hueco"] == dead_ball.GAP for f in con)),
        "reposo_antes_del_golpeo_s": repartir(
            [(f["golpeo"] - f["inicio_quieto"]) / fps for f in con], [0, 2, 5, 10, 30, INF],
            ["<2", "2-5", "5-10", "10-30", ">=30"]),
        "frames_entre_la_ultima_quieta_y_la_primera_en_movimiento": repartir(
            [f["primer_movimiento"] - f["ultimo_quieto"] for f in con], [1, 2, 6, HUECO_FECHA + 2],
            ["1", "2-5", "6-{}".format(HUECO_FECHA + 1)]),
        "mediana_golpeo_desde_el_inicio_s": {t: mediana_s([f["golpeo"] - f["inicio"] for f in con
                                                           if tipo_de_tabla(f["tipo"]) == t], fps) for t in por_tipo},
        "eventos_descartados_por_el_sitio": int(sum(f["descartados_por_sitio"] for f in filas)),
        "detecciones": {"intentos": int(sum(f["intentos"] for f in filas)),
                        "aceptadas": int(sum(f["aceptadas"] for f in filas)),
                        "capturas": int(sum(f["capturas"] for f in filas)),
                        "hacia_atras": int(sum(f["atras"] for f in filas))},
    }
    if codes is not None:
        salida["frente_a_nuestro_d"] = frente_a_nuestro_d(filas, codes, fps, bloques)
    return salida


ETIQUETAS_D = ("sin D", "acaba >5 s antes", "1-5 s antes", "a 1 s o menos", "1-5 s después", "acaba >5 s después")


def frente_a_nuestro_d(filas, codes, fps, bloques=None):
    """Dónde acaba nuestro `D` respecto al golpeo, por tipo: (fin de nuestra parada) − golpeo, con `fin_de_nuestro_d`."""
    bloques = tuple(bloques or tracking.evaluated_blocks(games.GAME))
    if len(codes) < max(b for _, b in bloques):
        raise ErrorGolpeo("la entrega no tiene los frames del partido")
    porte = collections.OrderedDict()
    for f in filas:
        if f["estado"] != GOLPEO:
            continue
        bloque = [(a, b) for a, b in bloques if a <= f["inicio"] < b]
        if not bloque:
            raise ErrorGolpeo("una ventana con golpeo no empieza en un tramo evaluado")
        fin = fin_de_nuestro_d(codes, bloque[0], f["inicio"], f["golpeo"], fps)
        if fin is None:
            clave = ETIQUETAS_D[0]
        else:
            d = fin - f["golpeo"]
            clave = (ETIQUETAS_D[1] if d < -5 * fps else ETIQUETAS_D[2] if d < -fps else ETIQUETAS_D[3]
                     if d <= fps else ETIQUETAS_D[4] if d <= 5 * fps else ETIQUETAS_D[5])
        porte.setdefault(tipo_de_tabla(f["tipo"]), collections.Counter())[clave] += 1
        porte.setdefault("todos", collections.Counter())[clave] += 1
    return {t: {e: celda(c[e]) for e in ETIQUETAS_D} for t, c in porte.items()}


# -- lo real ---------------------------------------------------------------------------------------------------------

def _paso(texto):
    sys.stderr.write("  {}\n".format(texto))
    sys.stderr.flush()


def _progreso(fraccion):
    sys.stderr.write("\r  {:5.1f} %".format(100.0 * fraccion))
    sys.stderr.flush()


def ruta_entrega(entrega):
    return entrega if os.path.isfile(entrega) else os.path.join(RESULTADOS, entrega + ".csv")


def leer_entrega(entrega):
    """(códigos por frame, sha256) de una entrega nuestra, o (None, None) si no está."""
    ruta = ruta_entrega(entrega)
    if not os.path.isfile(ruta):
        return None, None
    import possession_metrics as pm  # aquí: necesita pandas
    return np.asarray(pm.label_codes(pm.read_label_csv(ruta))), det.sha256_de(ruta)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="El golpeo de cada reinicio con el balón del vídeo táctico (variante fijada: recorte de {} px "
                    "×{}, confianza {:g}, {} hilos, CPU), con caché en MTAH_DATA_DIR/tactical/{}. Solo lo ejecuta una "
                    "persona.".format(det.LADO, det.FACTOR, det.CONF, det.HILOS, NOMBRE_CACHE))
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    ap.add_argument("--modelo", default=None, help="el .pt (por defecto, el de detector.py --descargar)")
    ap.add_argument("--entrega", default=ENTREGA,
                    help="la entrega con la que se compara el golpeo (nombre en evaluation/results sin .csv, o ruta)")
    ap.add_argument("--resumen", action="store_true", help="no lee el vídeo: los agregados de la caché ya hecha")
    ap.add_argument("--forzar", action="store_true", help="rehace la caché aunque exista (la pisa al acabar)")
    args = ap.parse_args(argv)
    reloj0 = time.perf_counter()
    if args.forzar and args.resumen:
        raise ErrorGolpeo("--forzar y --resumen no van juntos")
    necesarios = ("pandas",) if args.resumen else ("torch", "ultralytics", "cv2", "pandas")
    faltan = [m for m in necesarios if importlib.util.find_spec(m) is None]
    if faltan:
        raise ErrorGolpeo("faltan {}: ejecuta con el entorno del detector (torch, ultralytics, opencv, numpy y "
                          "pandas)".format(", ".join(faltan)))
    info = games.GAMES[games.GAME]
    fps = int(info["fps"])
    try:
        games.require(FICHEROS if not args.resumen else ["atd_meta", "atd_raw", "smart_tagging"], games.GAME,
                      args.data_dir)
    except (IOError, OSError):
        print("No encuentro el vídeo, el ATD, la homografía o el Smart Tagging del partido: revisa que MTAH_DATA_DIR "
              "apunte a la carpeta de los datos.")
        return 1
    paths = games.asset_paths(games.GAME, args.data_dir)
    carpeta = os.path.dirname(paths["atd_raw"])
    ruta_cache = os.path.join(carpeta, NOMBRE_CACHE)
    if args.resumen and not os.path.exists(ruta_cache):
        raise ErrorGolpeo("no hay caché ({}): lanza primero la búsqueda".format(NOMBRE_CACHE))
    if not args.resumen and not args.forzar and os.path.exists(ruta_cache):
        raise ErrorGolpeo("ya existe la caché ({}): --resumen para ver sus agregados, --forzar para rehacerla".format(
            NOMBRE_CACHE))
    modelo_sha256 = None
    if not args.resumen:
        probar_escritura(carpeta)
        ruta_modelo = args.modelo or det.ruta_por_defecto()
        if not os.path.isfile(ruta_modelo):
            raise ErrorGolpeo("no encuentro el modelo: bájalo con  python validation/balon_video/detector.py "
                              "--descargar")
        modelo_sha256 = det.sha256_de(ruta_modelo)
        if modelo_sha256 != det.MODELO_SHA256:
            raise ErrorGolpeo("el modelo no tiene el sha256 fijado: bórralo y vuelve a descargarlo")

    _paso("leyendo el ATD y el Smart Tagging (un par de minutos)")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        trk = ball.clean(tracking.from_atd(paths, games.GAME))
    events = dead_ball.smart_tagging_events(paths["smart_tagging"], fps)
    ventanas = preparar_ventanas(trk, events)

    if args.resumen:
        cache = leer(ruta_cache)
        if cache["huella"] != huella(cache["arrays"]):
            raise ErrorGolpeo("la huella de la caché no cuadra con sus arrays")
        if cache["metadatos"].get("ventanas", {}).get("sha256") != huella_ventanas(ventanas):
            raise ErrorGolpeo("la caché no es de estas ventanas del Smart Tagging")
        meta, variante = cache["metadatos"], cache["metadatos"].get("variante", {})
        distintas = [nombre for nombre, ok in (
            ("constantes", meta.get("constantes") == CONSTANTES),
            ("modelo", meta.get("modelo_sha256") == det.MODELO_SHA256),
            ("variante", (variante.get("recorte_px"), variante.get("factor"), variante.get("conf"),
                          variante.get("adelanto_atd")) == (det.LADO, float(det.FACTOR), float(det.CONF), BALL_LEAD)))
            if not ok]
        if distintas:
            raise ErrorGolpeo("la caché se hizo con otras {}: rehazla con --forzar".format(", ".join(distintas)))
        filas = filas_de(cache["arrays"])
        cabecera = {"medida": "golpeo de cada reinicio con el balón del vídeo (--resumen de la caché), solo agregados",
                    "versiones_de_la_cache": cache["metadatos"].get("versiones"),
                    "informativo": cache["informativo"], "huella": cache["huella"]}
    else:
        from starter import load_homography  # aquí: la prueba sin datos no necesita pandas
        _paso("leyendo la homografía")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            matrices, _, validas = load_homography.load(games.GAME, args.data_dir)
        ruta_video = games.video_path(games.GAME, args.data_dir)
        versiones = det.versiones()
        codigo = bvd.sha256_de_ficheros(CODIGO)
        metadatos = metadatos_de(games.GAME, len(trk.bx), trk.pitch, modelo_sha256, versiones, det.HILOS, codigo,
                                 ventanas, video=bvd.huella_del_video(ruta_video))
        _paso("cargando el modelo (sha256, escaneo y calentamiento)")
        modelo = det.cargar(ruta_modelo, hilos=det.HILOS)
        import torch
        if torch.get_num_threads() != det.HILOS:
            raise ErrorGolpeo("torch no se ha quedado con los hilos fijados")
        estado = {}

        def abrir_fuente(frames):
            return det.leer_frames(ruta_video, frames, n_esperado=info["n_video_frames"],
                                   tamano=(ANCHO_IMAGEN, ALTO_IMAGEN), estado=estado, hasta_el_final=True)

        def detector(imagen, centro):
            return det.detectar(modelo, imagen, det.CONF, det.FACTOR, centro, det.LADO)

        _paso("leyendo el vídeo desde el principio y siguiendo el balón en cada ventana; después, el resto del vídeo "
              "para contar sus frames")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            filas, recuento = ejecutar(ventanas, abrir_fuente, detector, trk, matrices, validas, progreso=_progreso)
        sys.stderr.write("\n")
        if estado.get("frames_decodificados") != info["n_video_frames"]:
            raise ErrorGolpeo("el vídeo no decodifica el número de frames esperado: no se escribe la caché")
        arrays = arrays_de(filas)
        hu = huella(arrays)
        informativo = dict(bvd.commit_del_codigo(CODIGO), tiempos={
            "frames_leidos": recuento["frames_leidos"], "detecciones": recuento["intentos"],
            "segundos_detectando": recuento["segundos_detectando"],
            "ms_por_deteccion": (round(1000.0 * recuento["segundos_detectando"] / recuento["intentos"], 2)
                                 if recuento["intentos"] else None),
            "segundos_leyendo_video": round(float(estado.get("segundos_leyendo") or 0.0), 1),
            "minutos_de_reloj": round((time.perf_counter() - reloj0) / 60.0, 1)})
        guardar(ruta_cache, arrays, metadatos, informativo, hu)
        cabecera = {"medida": "golpeo de cada reinicio con el balón del vídeo (docs/decisiones.md, 16/11), solo "
                              "agregados",
                    "versiones": versiones, "modelo_sha256": modelo_sha256[:12], "hilos_torch": int(torch.get_num_threads()),
                    "backend_video": estado.get("backend"), "frames_decodificados": estado.get("frames_decodificados"),
                    "informativo": informativo, "escrita": "MTAH_DATA_DIR/tactical/{}".format(NOMBRE_CACHE),
                    "huella": hu}

    codes, sha = leer_entrega(args.entrega)
    salida = dict(cabecera)
    salida["entrega_comparada"] = ({"nombre": os.path.basename(ruta_entrega(args.entrega)), "sha256": sha}
                                   if codes is not None else "no encuentro la entrega: sin «frente a nuestro D»")
    salida["golpeos"] = agregados(filas, fps, codes, trk.blocks)
    salida["constantes"] = CONSTANTES
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    return 0


def cli(argv=None):
    """`main` con los errores sin valores: los nuestros, con su mensaje; cualquier otro, solo el tipo y las líneas."""
    try:
        return main(argv)
    except (ErrorGolpeo, bs.ErrorSondeo, det.ErrorDetector, bvd.ErrorDeteccion) as e:  # mensajes sin datos
        print("ERROR: {}".format(e))
        return 1
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(bs.informe_de_error(e))
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(cli())
