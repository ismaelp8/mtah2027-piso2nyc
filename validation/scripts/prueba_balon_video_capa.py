"""Prueba `possession/balon_video.py` (B5 con el balón del vídeo, como capa apagada) sin datos de ningún partido.

    python validation/scripts/prueba_balon_video_capa.py

Lo puede ejecutar cualquiera, Claude incluido. El partido es el inventado de `prueba_pipeline.py` (más pequeño) y la
caché de detecciones la escribe el propio escritor de `validation/partido/balon_video_detectar.py` en una carpeta
temporal, junto a un «atd_raw» que no existe. Comprueba:

- sin `paths`, ceros y todo permitido, sin abrir ningún fichero;
- las constantes copiadas (modelo, recorte, ampliación, confianza, formato, columnas, nombre y huella) son las de
  `detector.py` y `balon_video_detectar.py`;
- la selección del balón del vídeo: la de más confianza a 5 m o menos (4,99 entra y 5,01 no), los empates (menor x,
  luego menor y), una detección sin metros, un frame sin detecciones o fuera de la caché (el ATD adelantado 4 frames),
  y NaN donde el ATD en t+4 no tiene balón (también en los 4 últimos frames);
- `pipeline.run` con la capa da EXACTAMENTE las mismas etiquetas que con la pieza de equipo cambiada por B5 sobre el
  balón del vídeo, y otras que sin la capa (la prueba no es vacía), también en el orden de `pipeline.build` (detrás de
  las anclas y de las dos capas de la entrega, con sus pesos); la capa se enchufa con `--capa` y no va en la entrega;
- una caché que falta, ilegible o que no cuadra (modelo, variante, adelanto, estado, partido, frames, huella o forma)
  da error sin valores, también en el traceback (sin la excepción original encadenada);
- determinismo.
"""

import os
import re
import shutil
import sys
import traceback

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import games  # noqa: E402
from possession import aprendida, balon_video as bv, dead_ball, pipeline, tracking, transiciones  # noqa: E402
from possession.ball import advance_ball  # noqa: E402
import balon_video_detectar as bvd  # noqa: E402
import detector as det  # noqa: E402
import prueba_pipeline as pp  # noqa: E402  (el partido inventado, la carpeta segura y no_files)

FALLOS = []
SEMILLA = 20261116
N = 6000
BLOQUES = ((500, 2900), (3200, 5800))
PITCH = tuple(games.GAMES[games.GAME]["pitch"])
GAME = games.GAME


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def partido():
    return pp.synthetic_tracking(N, BLOQUES, PITCH, np.random.default_rng(SEMILLA), slots_per_team=11)


def detecciones(trk, rng):
    """{frame: filas (k, 7)} inventadas alrededor del balón del ATD en t+4, más unos frames preparados a mano.

    Devuelve también los frames preparados y lo que se espera en cada uno."""
    ref = advance_ball(trk)
    rx, ry = np.asarray(ref.bx), np.asarray(ref.by)
    porframe = {}
    con_ref = [t for a, b in BLOQUES for t in range(a, b) if np.isfinite(rx[t])]
    for t in con_ref:
        if rng.random() < 0.3:
            porframe[t] = np.zeros((0, 7))
            continue
        filas = []
        ang, r = rng.uniform(0, 2 * np.pi), rng.uniform(0.0, 4.5)
        filas.append([0, 0, 4, 4, round(rng.uniform(0.1, 1.0), 4), rx[t] + r * np.cos(ang), ry[t] + r * np.sin(ang)])
        if rng.random() < 0.3:  # una lejana con mucha confianza: no entra
            filas.append([0, 0, 4, 4, 0.99, rx[t] + 8.0, ry[t]])
        porframe[t] = np.array(filas, dtype=np.float64)
    usados = iter([t for t in con_ref[40::97]])
    casos = {}
    t = next(usados)
    porframe[t] = np.array([[0, 0, 4, 4, 0.6, rx[t] + 1.0, ry[t]], [0, 0, 4, 4, 0.9, rx[t] - 2.0, ry[t] + 1.0]])
    casos["la de más confianza de las dos cercanas"] = (t, (rx[t] - 2.0, ry[t] + 1.0))
    t = next(usados)
    porframe[t] = np.array([[0, 0, 4, 4, 0.95, rx[t] + 5.01, ry[t]], [0, 0, 4, 4, 0.5, rx[t] - 4.99, ry[t]]])
    casos["a 4,99 m entra y a 5,01 m no, aunque tenga más confianza"] = (t, (rx[t] - 4.99, ry[t]))
    t = next(usados)
    porframe[t] = np.array([[0, 0, 4, 4, 0.7, rx[t] + 1.0, ry[t]], [0, 0, 4, 4, 0.7, rx[t] - 1.0, ry[t] + 0.5]])
    casos["empate de confianza: la de menor x"] = (t, (rx[t] - 1.0, ry[t] + 0.5))
    t = next(usados)
    porframe[t] = np.array([[0, 0, 4, 4, 0.7, rx[t] + 1.0, ry[t] + 1.0], [0, 0, 4, 4, 0.7, rx[t] + 1.0, ry[t] - 1.0]])
    casos["empate de confianza y de x: la de menor y"] = (t, (rx[t] + 1.0, ry[t] - 1.0))
    t = next(usados)
    porframe[t] = np.array([[0, 0, 4, 4, 0.99, np.nan, np.nan]])
    casos["una detección sin metros (NaN): el ATD adelantado"] = (t, (rx[t], ry[t]))
    t = next(usados)
    porframe[t] = np.zeros((0, 7))
    casos["un frame sin detecciones: el ATD adelantado"] = (t, (rx[t], ry[t]))
    t = next(usados)
    porframe.pop(t, None)
    casos["un frame que no está en la caché: el ATD adelantado"] = (t, (rx[t], ry[t]))
    sin_ref = [t for a, b in BLOQUES for t in range(a, b) if not np.isfinite(rx[t])][5]
    porframe[sin_ref] = np.array([[0, 0, 4, 4, 0.9, 10.0, 10.0]])
    casos["sin balón del ATD en t+4: NaN aunque haya detección"] = (sin_ref, (np.nan, np.nan))
    return porframe, casos


def escribir_cache(carpeta, porframe, **cambios):
    """La caché con el escritor de balon_video_detectar. `cambios`: claves de los metadatos (o de la variante) que se
    cambian, `estado`, `huella` (una huella falsa) y `frames_mas` (un frame de más fuera del partido)."""
    frames = np.array(sorted(porframe), dtype=np.int64)
    if cambios.get("frames_mas"):
        frames = np.append(frames, N + 10)
        porframe = dict(porframe)
        porframe[N + 10] = np.zeros((0, 7))
    filas = [porframe[int(t)] for t in frames]
    offsets = np.concatenate(([0], np.cumsum([len(f) for f in filas]))).astype(np.int64)
    valores = np.concatenate(filas + [np.zeros((0, 7))])
    meta = bvd.metadatos_de(GAME, N, PITCH, det.MODELO_SHA256, {"python": "falso"}, det.HILOS, "c" * 64, frames,
                            np.zeros((len(frames), 2)))
    for clave in ("recorte_px", "factor", "conf", "adelanto_atd"):
        if clave in cambios:
            meta["variante"][clave] = cambios[clave]
    for clave in ("modelo_sha256", "partido", "frames_del_video", "formato", "campo"):
        if clave in cambios:
            meta[clave] = cambios[clave]
    tactical = os.path.join(carpeta, "tactical")
    os.makedirs(tactical, exist_ok=True)
    ruta = os.path.join(tactical, bvd.NOMBRE_CACHE)
    huella = cambios.get("huella") or bvd.huella(frames, offsets, valores)
    bvd.guardar(ruta, frames, offsets, valores, meta, {"commit": None}, cambios.get("estado", "completo"), huella)
    return {"atd_raw": os.path.join(tactical, "BAR-ATH_tactical_atd.txt")}, (frames, offsets, valores)


def prueba_sin_paths(trk):
    print("sin paths")
    with pp.no_files():
        score, allowed = bv.ajuste_b5_video(trk)
    check("ceros y todo permitido, de forma (n, 3), sin abrir ningún fichero", score.shape == (N, 3)
          and not score.any() and allowed.shape == (N, 3) and allowed.all())


def prueba_constantes():
    print("constantes copiadas")
    check("sha256 del modelo, recorte, ampliación y confianza: los de detector.py",
          (bv.MODELO_SHA256, bv.LADO, bv.FACTOR, bv.CONF) == (det.MODELO_SHA256, det.LADO, float(det.FACTOR), det.CONF))
    check("nombre, formato y columnas de la caché: los de balon_video_detectar.py",
          (bv.NOMBRE_CACHE, bv.FORMATO, bv.COLUMNAS) == (bvd.NOMBRE_CACHE, bvd.FORMATO, bvd.COLUMNAS))
    rng = np.random.default_rng(1)
    f, o, v = np.arange(5) * 3, np.array([0, 1, 1, 3, 4, 6]), rng.normal(size=(6, 7))
    v[2, 3], v[4, 1] = np.nan, -0.0
    check("la huella copiada da lo mismo que la del detector", bv.huella(f, o, v) == bvd.huella(f, o, v))
    check("adelanto: el de possession.ball (4) y el radio, 5 m", bv.BALL_LEAD == 4 and bv.RADIO == 5.0)
    with open(os.path.join(ROOT, "possession", "balon_video.py"), encoding="utf-8") as fh:
        fuente = fh.read()
    importa = [l for l in fuente.splitlines() if re.match(r"\s*(import|from)\s", l)]
    check("possession/balon_video.py no importa nada de validation/ (solo numpy, games y possession)",
          not any("validation" in l for l in importa)
          and all(re.match(r"\s*(import (hashlib|json|os|games)|import numpy as np|from possession[ .])", l)
                  for l in importa), importa)
    check("apagada: no va en pipeline.PIECES ni en DELIVERY_LAYERS",
          not any("balon_video" in v for v in pipeline.PIECES.values())
          and bv.ajuste_b5_video not in pipeline.DELIVERY_LAYERS)
    _, capas = pipeline.overrides([], ["balon_video.ajuste_b5_video"])
    check("se enchufa con --capa balon_video.ajuste_b5_video", capas == [bv.ajuste_b5_video])


def prueba_seleccion(trk, carpeta):
    print("el balón del vídeo")
    porframe, casos = detecciones(trk, np.random.default_rng(SEMILLA + 1))
    paths, cache = escribir_cache(carpeta, porframe)
    leida = bv.leer_cache(bv.ruta_cache(paths), N, trk.pitch, GAME)
    check("leer_cache devuelve los arrays escritos", all(np.array_equal(a, b, equal_nan=True)
                                                         for a, b in zip(leida, cache)))
    video = bv.balon_del_video(trk, *leida)
    for nombre, (t, (ex, ey)) in casos.items():
        bx, by = video.bx[t], video.by[t]
        ok = (np.isnan(ex) and np.isnan(bx) and np.isnan(by)) or (bx == ex and by == ey)
        check(nombre, ok)
    ref = advance_ball(trk)
    check("los 4 últimos frames, sin balón (el ATD en t+4 no existe)", np.isnan(video.bx[-4:]).all())
    rx = np.asarray(ref.bx)
    check("NaN exactamente donde el ATD en t+4 no tiene balón", np.array_equal(np.isnan(video.bx), np.isnan(rx)))
    # Frame a frame, contra una cuenta directa con bucles.
    malos = 0
    for t, filas in porframe.items():
        if not np.isfinite(rx[t]):
            continue
        d = np.hypot(filas[:, 5] - rx[t], filas[:, 6] - ref.by[t]) if len(filas) else np.zeros(0)
        cerca = [i for i in range(len(filas)) if d[i] <= 5.0]
        if cerca:
            i = sorted(cerca, key=lambda i: (-filas[i, 4], filas[i, 5], filas[i, 6], i))[0]
            esperado = (filas[i, 5], filas[i, 6])
        else:
            esperado = (rx[t], ref.by[t])
        malos += (video.bx[t], video.by[t]) != esperado
    check("en todos los frames de la caché, la elegida es la de una cuenta directa", malos == 0, malos)
    fuera = [t for t in range(N) if t not in porframe]
    check("fuera de la caché, el balón del ATD adelantado 4 frames",
          np.array_equal(video.bx[fuera], rx[fuera], equal_nan=True))
    check("los jugadores no se tocan y trk no cambia", video.px is trk.px and video.py is trk.py
          and np.array_equal(trk.bx, partido().bx, equal_nan=True))
    cambiados = int(np.sum(np.isfinite(rx) & (video.bx != rx)))
    check("el balón del vídeo cambia en muchos frames (la prueba no es vacía)", cambiados > 1000, cambiados)
    return paths, leida


def prueba_pipeline(trk, paths, cache):
    print("la capa en el pipeline")
    score, allowed = bv.ajuste_b5_video(trk, paths, GAME)
    b5, _ = aprendida.evidence_b5(trk)
    b5v, _ = aprendida.evidence_b5(bv.balon_del_video(trk, *cache))
    check("devuelve (n, 3) con allowed todo True", score.shape == (N, 3) and allowed.all())
    check("B5 + capa = B5 con el balón del vídeo (salvo el redondeo de a + (b − a))",
          np.allclose(b5 + score, b5v, rtol=0, atol=1e-9), float(np.max(np.abs(b5 + score - b5v))))
    capa = pipeline.with_paths(bv.ajuste_b5_video, paths, GAME)
    con_capa = pipeline.run(trk, extra=[capa])
    con_pieza = pipeline.run(trk, pieces={"candidates": lambda t: aprendida.evidence_b5(bv.balon_del_video(t, *cache))})
    sin_capa = pipeline.run(trk)
    distintos = int(np.sum(con_capa != sin_capa))
    check("pipeline.run con la capa = con la pieza de equipo cambiada por B5 sobre el balón del vídeo (etiquetas)",
          np.array_equal(con_capa, con_pieza), int(np.sum(con_capa != con_pieza)))
    check("y distinto de sin la capa (no es una prueba vacía)", distintos > 0, "{} frames".format(distintos))
    # El orden de pipeline.build: las piezas, las anclas, las capas de la entrega y después las de --capa. Con arrays
    # inventados y los pesos de la entrega (B5 + (B5v − B5) no es B5v bit a bit: tienen que salir las mismas etiquetas).
    rng = np.random.default_rng(SEMILLA + 7)
    vacio = np.zeros((N, 3))
    anclas_s, trans_s, fuera_s = vacio.copy(), vacio.copy(), vacio.copy()
    anclas_s[rng.random(N) < 0.05, 2] = dead_ball.GAP_SCORE
    anclas_ok = np.ones((N, 3), dtype=bool)
    anclas_ok[[BLOQUES[0][0] + 300, BLOQUES[1][0] + 300], 2] = False  # el juego vivo en un saque: sin D
    bloque = np.zeros(N, dtype=bool)
    for ini in range(BLOQUES[0][0] + 100, BLOQUES[1][1] - 200, 700):
        bloque[ini:ini + 125] = True
    trans_s[bloque & (np.arange(N) % 1400 < 700), 0] = transiciones.WEIGHT
    trans_s[bloque & (np.arange(N) % 1400 >= 700), 1] = transiciones.WEIGHT
    fuera_s[rng.random(N) < 0.03, 2] = dead_ball.BALL_OUT_SCORE
    todo = np.ones((N, 3), dtype=bool)
    capas_entrega = [(anclas_s, anclas_ok), (trans_s, todo), (fuera_s, todo)]
    orden_build = pipeline.run(trk, extra=capas_entrega + [capa])
    pieza_build = pipeline.run(trk, extra=capas_entrega,
                               pieces={"candidates": lambda t: aprendida.evidence_b5(bv.balon_del_video(t, *cache))})
    sin_build = pipeline.run(trk, extra=capas_entrega)
    check("en el orden de pipeline.build (anclas, contraataques y balón fuera delante): las mismas etiquetas que con "
          "la pieza cambiada", np.array_equal(orden_build, pieza_build), int(np.sum(orden_build != pieza_build)))
    check("y las capas de la entrega cambian algo (la prueba del orden no es vacía)",
          int(np.sum(sin_build != sin_capa)) > 0 and int(np.sum(orden_build != sin_build)) > 0,
          (int(np.sum(sin_build != sin_capa)), int(np.sum(orden_build != sin_build))))
    again = pipeline.run(trk, extra=[pipeline.with_paths(bv.ajuste_b5_video, paths, GAME)])
    s2, _ = bv.ajuste_b5_video(trk, paths, GAME)
    check("determinista: la misma puntuación bit a bit y las mismas etiquetas", np.array_equal(score, s2)
          and np.array_equal(con_capa, again))


def prueba_errores(trk, carpeta, porframe):
    print("errores sin valores")
    casos = [("falta la caché", None),
             ("otro modelo", {"modelo_sha256": "0" * 64}), ("otro recorte", {"recorte_px": 640}),
             ("otra ampliación", {"factor": 1.0}), ("otra confianza", {"conf": 0.25}),
             ("otro adelanto", {"adelanto_atd": 3}), ("un parcial", {"estado": "parcial"}),
             ("otro partido", {"partido": "OTRO-PARTIDO"}), ("otros frames del vídeo", {"frames_del_video": N + 1}),
             ("otro formato", {"formato": 2}), ("otro campo", {"campo": [100.0, 60.0]}),
             ("huella que no cuadra", {"huella": "e" * 64}), ("un frame fuera del partido", {"frames_mas": True}),
             ("fichero ilegible", "roto")]
    for i, (nombre, cambios) in enumerate(casos):
        d = os.path.join(carpeta, "error{}".format(i))
        if cambios is None:
            paths = {"atd_raw": os.path.join(d, "tactical", "BAR-ATH_tactical_atd.txt")}
        elif cambios == "roto":
            os.makedirs(os.path.join(d, "tactical"))
            with open(os.path.join(d, "tactical", bv.NOMBRE_CACHE), "wb") as f:
                f.write(b"PK no es un npz 123.456")
            paths = {"atd_raw": os.path.join(d, "tactical", "BAR-ATH_tactical_atd.txt")}
        else:
            paths, _ = escribir_cache(d, porframe, **cambios)
        try:
            bv.ajuste_b5_video(trk, paths, GAME)
            check("{}: error".format(nombre), False)
        except bv.ErrorCache as e:
            check("{}: error claro y sin valores ni cifras".format(nombre), not re.search(r"\d", str(e)), str(e))
            completo = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            check("{}: el traceback no encadena la excepción original (que podría llevar valores)".format(nombre),
                  e.__cause__ is None and (e.__context__ is None or e.__suppress_context__)
                  and "During handling" not in completo and "123.456" not in completo)


def main():
    print("Prueba de possession/balon_video.py")
    trk = partido()
    carpeta = pp.safe_tmp()
    try:
        prueba_sin_paths(trk)
        prueba_constantes()
        paths, cache = prueba_seleccion(trk, carpeta)
        prueba_pipeline(trk, paths, cache)
        porframe, _ = detecciones(trk, np.random.default_rng(SEMILLA + 1))
        prueba_errores(trk, carpeta, porframe)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    print("\nTODO BIEN" if not FALLOS else "\nFALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
    return 0 if not FALLOS else 1


if __name__ == "__main__":
    sys.exit(main())
