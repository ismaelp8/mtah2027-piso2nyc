"""B5 con el balón sacado del vídeo táctico, como capa de una entrega de prueba. APAGADA.

**Qué es.** La línea del balón del vídeo (`validation/balon_video/BITACORA.md`) detecta el balón en el vídeo táctico,
sin el suavizado de casi 1 s ni el retraso de 4 frames del balón del ATD. Si entra, ese balón solo lo ve la evidencia de
equipo (B5, `aprendida.evidence_b5`); las piezas de `D` siguen con el balón del ATD (bitácora, «Lo que no se hace»).

**El balón del vídeo que recibe B5**, exactamente la regla de la bitácora (fijada el 16/11, antes de medir):
- en cada frame con balón del ATD en t+4 (`ball.advance_ball`), la detección de más confianza a `RADIO` = 5 m o menos
  de ese balón (la distancia, en metros del campo, con la posición que guarda la caché). Empates: la de menor x, luego
  la de menor y (en metros) y luego la que va antes en la caché;
- si no hay ninguna (o el frame no está en la caché), el balón del ATD adelantado 4 frames, para que todo el balón vaya
  en el mismo tiempo que los jugadores;
- donde el ATD en t+4 no tiene balón, NaN.
`balon_del_video` devuelve el `Tracking` con ese balón; los jugadores no se tocan.

**Por qué es una capa y no una pieza.** La pieza de equipo de la entrega sigue siendo B5 con el balón de siempre
(`pipeline.PIECES`). Esta capa devuelve B5 con el balón del vídeo MENOS B5 con el balón que recibe, en las tres
columnas, y `allowed` todo True. El pipeline la suma a la B5 de siempre, así que queda B5 con el balón del vídeo sin
tocar `pipeline.py`. Las etiquetas salen las mismas que cambiando la pieza (lo comprueba
`validation/scripts/prueba_balon_video_capa.py`); las puntuaciones, iguales salvo el redondeo de a + (b − a). Se usa en
una entrega de prueba:

    python -m possession.pipeline --name prueba_balon_video --capa balon_video.ajuste_b5_video

**Abre un fichero del partido,** como `dead_ball` y `transiciones`, pero es una excepción NUEVA a la interfaz: la que
escriben `possession/tracking.py`, `docs/PLAN_ENTREGA.md` §2 y `CLAUDE.md` solo nombra a esas dos. Está pendiente
apuntarla en esos tres sitios (y, si se enciende, en el comentario de `pipeline.DELIVERY_LAYERS`). Lee la caché de
detecciones que escribe `validation/partido/balon_video_detectar.py` (`BAR-ATH_tactical_balon_video.npz`, junto al ATD
en `MTAH_DATA_DIR/tactical/`) solo cuando `pipeline.build` le pasa las rutas del partido. **Sin `paths` no abre
nada y devuelve ceros:** en la DFL y en `validation/scripts/prueba_pipeline.py` no cambia nada. Con `paths`, comprueba que la caché es de la variante fijada
(el sha256 del modelo, el recorte, la ampliación, la confianza y el adelanto de `CONSTANTES`, copiadas aquí y no
importadas de validation/), que está completa, que su huella cuadra con sus arrays y que es del mismo partido; si no,
da error sin valores.

**Está apagada** (no va en `pipeline.PIECES` ni en `pipeline.DELIVERY_LAYERS`) hasta que pase la puerta 2 de la
bitácora: la 2.1 (la emulación en la DFL con las cifras del partido entero), la 2.2 (los criterios de daño de la
entrega de prueba frente a `equipo_v8`, escritos antes de generarla), la reproducción byte a byte (2.3), el tiempo
(2.4) y las licencias (2.5).

**El final de cada parada en el golpeo** (16/11, pieza de `D`; regla en docs/decisiones.md, «el final de cada parada en
el golpeo del balón del vídeo»): `golpeo_desde_hueco` y `golpeo_desde_ventana`, dos capas APAGADAS, una por candidato.
Leen la caché de golpeos que escribe `validation/partido/balon_video_golpeo.py` (`BAR-ATH_tactical_golpeos.npz`, junto al
ATD) y el Smart Tagging, solo con `paths`; sin `paths`, ceros. En cada ventana `SET PIECES` con golpeo suman `PESO_D` a
`D` desde el arranque (el inicio del hueco o el de la ventana) hasta el golpeo, y restan `PESO_JUEGO` a `D` durante los
`TRAS_GOLPEO` frames siguientes. No tocan B5 ni prohíben nada. Si se encienden, son la misma excepción nueva a la
interfaz que `ajuste_b5_video`.
"""

import hashlib
import json
import os

import numpy as np

import games
from possession import aprendida, dead_ball
from possession.ball import BALL_LEAD, advance_ball
from possession.tracking import D, N_STATES, no_evidence

NOMBRE_CACHE = "BAR-ATH_tactical_balon_video.npz"
RADIO = 5.0  # m: la detección tiene que estar a esta distancia o menos del balón del ATD en t+4 (bitácora)

# Copias de validation/balon_video/detector.py (la variante fijada el 16/11 a las 16:00) y del formato de la caché de
# validation/partido/balon_video_detectar.py. possession/ no importa nada de validation/: la prueba comprueba que son
# las mismas.
MODELO_SHA256 = "fb37942448e7de08745e8aab148d0794f680a738ddd55e5f17abe9ab2d6313fb"
LADO = 320  # px del recorte
FACTOR = 2.0  # ampliación del recorte
CONF = 0.10  # confianza mínima
FORMATO = 1
COLUMNAS = ("x_px", "y_px", "w_px", "h_px", "conf", "x_m", "y_m")
COL_CONF, COL_X, COL_Y = COLUMNAS.index("conf"), COLUMNAS.index("x_m"), COLUMNAS.index("y_m")


class ErrorCache(ValueError):
    """La caché del balón del vídeo falta o no cuadra. El mensaje no lleva valores (se puede pegar a Claude)."""


def ruta_cache(paths):
    """La caché, junto al ATD del partido (en `MTAH_DATA_DIR/tactical/`)."""
    return os.path.join(os.path.dirname(paths["atd_raw"]), NOMBRE_CACHE)


def huella(frames, offsets, valores):
    """sha256 de los tres arrays de la caché. Copia de `balon_video_detectar.huella` (la prueba lo comprueba)."""
    h = hashlib.sha256()
    for nombre, valor, tipo in (("frames", frames, "<i8"), ("offsets", offsets, "<i8"), ("valores", valores, "<f8")):
        a = np.ascontiguousarray(np.asarray(valor, dtype=tipo))
        if a.dtype.kind == "f":
            a = np.where(np.isnan(a), np.nan, a + 0.0)
        a = np.ascontiguousarray(a, dtype=tipo)
        h.update("{}|{}|{}\n".format(nombre, tipo, ",".join(str(s) for s in a.shape)).encode("ascii"))
        h.update(a.tobytes())
    return h.hexdigest()


def leer_cache(ruta, n, pitch, game=games.GAME):
    """(frames, offsets, valores) de la caché, comprobada. Error sin valores si falta o no cuadra."""
    if not os.path.isfile(ruta):
        raise ErrorCache("falta la caché del balón del vídeo ({}): la escribe "
                         "validation/partido/balon_video_detectar.py".format(NOMBRE_CACHE))
    try:
        with np.load(ruta, allow_pickle=False) as z:
            frames = np.asarray(z["frames"])
            offsets = np.asarray(z["offsets"])
            valores = np.asarray(z["valores"], dtype=np.float64)
            meta = json.loads(str(z["metadatos"]))
            estado, guardada = str(z["estado"]), str(z["huella"])
        variante = meta["variante"]
        no_cuadra = [nombre for nombre, ok in (
            ("formato", meta["formato"] == FORMATO),
            ("partido", meta["partido"] == game),
            ("modelo", meta["modelo_sha256"] == MODELO_SHA256),
            ("recorte", int(variante["recorte_px"]) == LADO),
            ("ampliación", float(variante["factor"]) == FACTOR),
            ("confianza", float(variante["conf"]) == CONF),
            ("adelanto del balón del ATD", int(variante["adelanto_atd"]) == BALL_LEAD),
            ("columnas", list(meta["columnas"]) == list(COLUMNAS)),
            ("frames del vídeo", int(meta["frames_del_video"]) == int(n)),
            ("campo", [float(v) for v in meta["campo"]] == [float(v) for v in pitch]),
            ("estado completo", estado == "completo")) if not ok]
    except ErrorCache:
        raise
    except Exception:
        # `from None`: sin la excepción original encadenada, que podría llevar valores de la caché en su mensaje
        # (`python -m possession.pipeline` no captura errores y el traceback sale entero).
        mensaje = "no se puede leer la caché del balón del vídeo ({}) o le falta algo".format(NOMBRE_CACHE)
        raise ErrorCache(mensaje) from None
    if no_cuadra:
        raise ErrorCache("la caché del balón del vídeo no es la de la variante fijada o de este partido; no cuadra: "
                         "{}".format(", ".join(no_cuadra)))
    forma = (frames.ndim == 1 and offsets.ndim == 1 and valores.ndim == 2 and valores.shape[1] == len(COLUMNAS)
             and frames.dtype.kind == "i" and offsets.dtype.kind == "i" and len(offsets) == len(frames) + 1
             and offsets[0] == 0 and offsets[-1] == len(valores) and bool(np.all(np.diff(offsets) >= 0))
             and bool(np.all(np.diff(frames) > 0)) and (not len(frames) or (frames[0] >= 0 and frames[-1] < n)))
    if not forma:
        raise ErrorCache("la caché del balón del vídeo no tiene la forma esperada")
    if huella(frames, offsets, valores) != guardada:
        raise ErrorCache("la huella de la caché del balón del vídeo no cuadra con sus arrays")
    return frames.astype(np.int64), offsets.astype(np.int64), valores


def balon_del_video(trk, frames, offsets, valores, radio=RADIO):
    """El `Tracking` con el balón del vídeo (la regla de la bitácora; ver el docstring del módulo). `trk` no cambia."""
    ref = advance_ball(trk, BALL_LEAD)
    rx, ry = np.asarray(ref.bx, dtype=np.float64), np.asarray(ref.by, dtype=np.float64)
    bx, by = rx.copy(), ry.copy()
    frames = np.asarray(frames, dtype=np.int64)
    valores = np.asarray(valores, dtype=np.float64)
    del_frame = np.repeat(frames, np.diff(np.asarray(offsets, dtype=np.int64)))
    if len(del_frame):
        with np.errstate(invalid="ignore"):
            dist = np.hypot(valores[:, COL_X] - rx[del_frame], valores[:, COL_Y] - ry[del_frame])
            cerca = np.flatnonzero(dist <= radio)  # NaN (sin balón del ATD o sin proyección): fuera
        if len(cerca):
            # Por frame; dentro, más confianza, menor x, menor y y el orden de la caché. La primera de cada frame.
            orden = np.lexsort((cerca, valores[cerca, COL_Y], valores[cerca, COL_X], -valores[cerca, COL_CONF],
                                del_frame[cerca]))
            elegidas = cerca[orden]
            _, primera = np.unique(del_frame[elegidas], return_index=True)
            j = elegidas[primera]
            bx[del_frame[j]] = valores[j, COL_X]
            by[del_frame[j]] = valores[j, COL_Y]
    bx.setflags(write=False)
    by.setflags(write=False)
    return trk._replace(bx=bx, by=by)


def ajuste_b5_video(trk, paths=None, game=games.GAME):
    """(score, allowed): B5 con el balón del vídeo menos B5 con el balón de `trk`; `allowed` todo True.

    Sin `paths`, ceros (no abre nada). Con `paths` (los de `games.asset_paths`), lee la caché junto a `paths["atd_raw"]`.
    """
    n = len(trk.bx)
    if paths is None:
        return no_evidence(n)
    frames, offsets, valores = leer_cache(ruta_cache(paths), n, trk.pitch, game)
    con_video, _ = aprendida.evidence_b5(balon_del_video(trk, frames, offsets, valores))
    sin_video, _ = aprendida.evidence_b5(trk)
    return con_video - sin_video, np.ones((n, N_STATES), dtype=bool)


# -- El final de cada parada en el golpeo del balón del vídeo (16/11). DOS CAPAS APAGADAS. ---------------------------
# Regla, candidatos y criterios de daño: docs/decisiones.md, 16/11, «el final de cada parada en el golpeo del balón del
# vídeo», escritos antes de ejecutar nada del partido. Son capas de `D`: no tocan B5. Para probarlas:
#     python validation/partido/probar_entrega.py prueba_golpeo_hueco --capa balon_video.golpeo_desde_hueco
#     python validation/partido/probar_entrega.py prueba_golpeo_ventana --capa balon_video.golpeo_desde_ventana

NOMBRE_GOLPEOS = "BAR-ATH_tactical_golpeos.npz"
FORMATO_GOLPEOS = 1
# Copias de validation/partido/balon_video_golpeo.py (possession/ no importa nada de validation/; la prueba comprueba
# que son las mismas). La capa solo acepta una caché hecha con estas constantes y la variante fijada del detector. Todas
# sin ajustar; MARGEN_FIN (5 s antes del fin de la ventana) sale de este partido, de agregados sin etiquetas (14/11).
CONSTANTES_GOLPEO = {
    "QUIETO": 25, "MIN_QUIETO": 13, "RADIO_QUIETO": 0.5, "HUECO_FECHA": 12, "MOVER": 10, "MIN_MOVER": 3,
    "RADIO_MOVER": 2.0, "PERDIDO": 25, "SALTO_PX": 40, "SALTO_MAX": 120, "RECENTRAR": 5, "RADIO_CAPTAR": 3.0,
    "ATRAS": 250, "MARGEN_FIN": 125, "HUECO_MAX": 1500, "RADIO_CORNER": 3.0, "AREA_CHICA_FONDO": 5.5,
    "AREA_CHICA_MEDIO_ANCHO": 9.16, "MARGEN_AREA": 2.0, "BANDA": 5.0, "MARGEN_CAMPO": 2.0,
}
ENTEROS_GOLPEO = ("inicio", "fin", "corte", "limite", "desde", "hasta", "reaparicion", "golpeo", "ultimo_quieto",
                  "primer_movimiento", "inicio_quieto", "intentos", "aceptadas", "capturas", "atras",
                  "descartados_por_sitio")
REALES_GOLPEO = ("x_m", "y_m")
TEXTOS_GOLPEO = ("tipo", "estado", "estado_hueco")
ESTADO_GOLPEO = "golpeo"  # el único estado que usa la capa
# Los pesos de las dos capas, fijados antes de generar ninguna entrega de prueba (sin ajustar):
# - PESO_D, en `D` desde el arranque hasta el golpeo: la escala de dead_ball.BALL_OUT_SCORE (5). En el juego vivo típico
#   (dead_state −3,42 de mediana en la DFL, y el +1 de N1 en B5) cada frame gana 5 − 3,42 − 1 > 0 para `D`;
# - PESO_JUEGO, restado a `D` durante los TRAS_GOLPEO frames que siguen al golpeo (3 s, el PUSH_AFTER_S de la regla del
#   instante del reinicio, 15/11), para que la parada no siga después del golpeo.
PESO_D = 5.0
PESO_JUEGO = 5.0
TRAS_GOLPEO = 75


def ruta_golpeos(paths):
    """La caché de golpeos, junto al ATD del partido (en `MTAH_DATA_DIR/tactical/`)."""
    return os.path.join(os.path.dirname(paths["atd_raw"]), NOMBRE_GOLPEOS)


def huella_golpeos(arrays):
    """sha256 de las columnas de la caché de golpeos. Copia de `balon_video_golpeo.huella` (la prueba lo comprueba)."""
    h = hashlib.sha256()
    for nombre in ENTEROS_GOLPEO + REALES_GOLPEO:
        tipo = "<i8" if nombre in ENTEROS_GOLPEO else "<f8"
        a = np.ascontiguousarray(np.asarray(arrays[nombre], dtype=tipo))
        if a.dtype.kind == "f":
            a = np.ascontiguousarray(np.where(np.isnan(a), np.nan, a + 0.0), dtype=tipo)
        h.update("{}|{}|{}\n".format(nombre, tipo, ",".join(str(s) for s in a.shape)).encode("ascii"))
        h.update(a.tobytes())
    for nombre in TEXTOS_GOLPEO:
        valores = [str(v) for v in np.asarray(arrays[nombre]).tolist()]
        h.update("{}|texto|{}\n".format(nombre, len(valores)).encode("ascii"))
        h.update("".join(v + "\n" for v in valores).encode("utf-8"))
    return h.hexdigest()


def ventanas_golpeo(events, blocks):
    """Las ventanas de la capa: las de `dead_ball.restart_windows` que empiezan en un tramo evaluado, en su orden."""
    return [w for w in dead_ball.restart_windows(events) if any(a <= w["start"] < b for a, b in blocks)]


def huella_ventanas_golpeo(ventanas):
    """sha256 de la lista (inicio, fin, tipo). Copia de `balon_video_golpeo.huella_ventanas` (la prueba lo comprueba)."""
    texto = "".join("{},{},{}\n".format(int(w["start"]), int(w["end"]), w["type"]) for w in ventanas)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def leer_golpeos(ruta, n, pitch, ventanas, game=games.GAME):
    """[golpeo o None] para cada ventana de `ventanas`, en su orden: el golpeo si su estado es «golpeo»; si no, None.

    Comprueba el formato, el partido, el modelo, la variante, las constantes, los frames del vídeo, el campo, que las
    ventanas son las de `ventanas` (las del Smart Tagging de `paths`), la forma y la huella. Error sin valores si falta
    o no cuadra (`ErrorCache`)."""
    if not os.path.isfile(ruta):
        raise ErrorCache("falta la caché de golpeos ({}): la escribe validation/partido/balon_video_golpeo.py".format(
            NOMBRE_GOLPEOS))
    try:
        with np.load(ruta, allow_pickle=False) as z:
            arrays = {k: np.asarray(z[k]) for k in ENTEROS_GOLPEO + REALES_GOLPEO + TEXTOS_GOLPEO}
            meta = json.loads(str(z["metadatos"]))
            guardada = str(z["huella"])
        variante = meta["variante"]
        no_cuadra = [nombre for nombre, ok in (
            ("formato", meta["formato"] == FORMATO_GOLPEOS),
            ("partido", meta["partido"] == game),
            ("modelo", meta["modelo_sha256"] == MODELO_SHA256),
            ("recorte", int(variante["recorte_px"]) == LADO),
            ("ampliación", float(variante["factor"]) == FACTOR),
            ("confianza", float(variante["conf"]) == CONF),
            ("adelanto del balón del ATD", int(variante["adelanto_atd"]) == BALL_LEAD),
            ("constantes del golpeo", meta["constantes"] == CONSTANTES_GOLPEO),
            ("frames del vídeo", int(meta["frames_del_video"]) == int(n)),
            ("campo", [float(v) for v in meta["campo"]] == [float(v) for v in pitch]),
            ("ventanas del Smart Tagging", int(meta["ventanas"]["n"]) == len(ventanas)
             and meta["ventanas"]["sha256"] == huella_ventanas_golpeo(ventanas))) if not ok]
    except Exception:
        # `from None`: sin la excepción original, que podría llevar valores de la caché en su mensaje.
        raise ErrorCache("no se puede leer la caché de golpeos ({}) o le falta algo".format(NOMBRE_GOLPEOS)) from None
    if no_cuadra:
        raise ErrorCache("la caché de golpeos no es de la variante fijada, de estas constantes o de este partido; no "
                         "cuadra: {}".format(", ".join(no_cuadra)))
    largos = {len(arrays[k]) for k in arrays}
    if largos != {len(ventanas)} or any(arrays[k].ndim != 1 for k in arrays) or [
            int(v) for v in arrays["inicio"]] != [int(w["start"]) for w in ventanas]:
        raise ErrorCache("la caché de golpeos no tiene la forma esperada")
    if huella_golpeos(arrays) != guardada:
        raise ErrorCache("la huella de la caché de golpeos no cuadra con sus arrays")
    return [int(arrays["golpeo"][i]) if str(arrays["estado"][i]) == ESTADO_GOLPEO else None
            for i in range(len(ventanas))]


def tramos_golpeo(trk, events, golpeos, desde_hueco, game=games.GAME):
    """[(desde, golpeo, hasta)] de la capa: +PESO_D en `D` en [desde, golpeo) y −PESO_JUEGO en [golpeo, hasta).

    `golpeos` es la lista de `leer_golpeos`, una entrada por ventana de `ventanas_golpeo(events, trk.blocks)`, en su
    orden (por posición: dos ventanas con el mismo inicio no se pisan).

    - `desde` es el inicio de la ventana; con `desde_hueco`, el inicio del hueco de la capa del hueco si la ventana lo
      tiene (`dead_ball.gaps_before_restarts`, con el balón de `trk`). Nunca antes del tramo evaluado.
    - `hasta` es el golpeo más TRAS_GOLPEO, sin pasar del siguiente `GOALS` o `SET PIECES` ni del fin del tramo.
    - Un golpeo fuera de [inicio, límite) da error: la caché no es de este tracking o de este Smart Tagging. El límite
      es el del script: el fin de la ventana menos MARGEN_FIN, el siguiente reinicio o el fin del tramo.
    """
    fps = games.GAMES[game]["fps"]
    huecos = {id(w): span for w, _, span in dead_ball.gaps_before_restarts(trk.bx, trk.by, events, fps)}
    margen = CONSTANTES_GOLPEO["MARGEN_FIN"]
    ventanas = ventanas_golpeo(events, trk.blocks)
    if len(golpeos) != len(ventanas):
        raise ErrorCache("la caché de golpeos no tiene una fila por ventana")
    tramos = []
    for w, k in zip(ventanas, golpeos):
        inicio = int(w["start"])
        if k is None:
            continue
        a, b = [(a, b) for a, b in trk.blocks if a <= inicio < b][0]
        corte = dead_ball.next_restart(events, w)
        if not inicio <= k < min(int(w["end"]) - margen, corte, b):
            raise ErrorCache("la caché de golpeos tiene un golpeo fuera de su ventana: no es de este partido")
        desde = inicio
        span = huecos.get(id(w))
        if desde_hueco and span is not None:
            desde = min(desde, int(span[0]))
        tramos.append((max(desde, a), k, int(min(k + TRAS_GOLPEO, corte, b))))
    return tramos


def _golpeo(trk, paths, game, desde_hueco):
    n = len(trk.bx)
    score, allowed = no_evidence(n)
    if paths is None:
        return score, allowed
    events = dead_ball.smart_tagging_events(paths["smart_tagging"], games.GAMES[game]["fps"])
    golpeos = leer_golpeos(ruta_golpeos(paths), n, trk.pitch, ventanas_golpeo(events, trk.blocks), game)
    for desde, k, hasta in tramos_golpeo(trk, events, golpeos, desde_hueco, game):
        score[desde:k, D] += PESO_D
        score[k:hasta, D] -= PESO_JUEGO
    return score, allowed


def golpeo_desde_hueco(trk, paths=None, game=games.GAME):
    """(score, allowed) del candidato «desde el hueco»: `D` desde el inicio del hueco (o de la ventana, si no tiene)
    hasta el golpeo, y juego después. Sin `paths`, ceros (no abre nada). APAGADA."""
    return _golpeo(trk, paths, game, desde_hueco=True)


def golpeo_desde_ventana(trk, paths=None, game=games.GAME):
    """(score, allowed) del candidato «desde la ventana»: `D` desde el inicio de la ventana hasta el golpeo, y juego
    después. No toca el hueco antes de la ventana. Sin `paths`, ceros (no abre nada). APAGADA."""
    return _golpeo(trk, paths, game, desde_hueco=False)
