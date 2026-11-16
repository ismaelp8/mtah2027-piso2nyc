"""Puerta 1b de la línea del balón del vídeo: ¿el detector ve el balón donde lo ve el ATD, y le sirve a B5?

**Solo lo ejecuta una persona, en local** (regla nº 1 de `CLAUDE.md`). Claude no lo ejecuta: lee el vídeo, el ATD y
la homografía del partido. La prueba sin datos es `validation/scripts/prueba_balon_video_sondeo.py`.

La regla es la de la puerta 1b de `validation/balon_video/BITACORA.md` con su corrección del 16/11 (15:50), fijada
antes de medir. **Deciden las condiciones 1, 2 y 5**; la 3 y la 4 son descriptivas:

1. donde el ATD ve el balón, el detector encuentra uno a 3 m o menos del balón del ATD adelantado 4 frames en el 70 %
   o más de los frames;
2. de las detecciones hechas donde el ATD ve el balón (todas: también las que caen fuera del campo, y las de
   proyección no finita cuentan como lejos), el 10 % o menos está a más de 5 m de él. Al lado, sin voto, la misma
   cifra solo con las detecciones dentro del campo ±3 m;
3. (descriptiva) toques del balón del detector por minuto (`validation/balon_video/toques.py`), al lado de los del
   balón del ATD en t+4 y en t;
4. (descriptiva) su «suelo de ruido» por minuto (los mismos cambios de velocidad sin ningún jugador a 3 m o menos),
   al lado del del balón del ATD en los mismos frames. Toques y ruido van por minuto de los frames en que se ve cada
   balón, y también por minuto de frames con balón del ATD;
5. la emulación en la DFL (`validation/balon_video/emular_dfl.py`, su JSON) leída en la celda que mide el sondeo:
   - p: la condición 1 redondeada hacia abajo a la rejilla;
   - σ: el menor de la rejilla cuyo temblor en la DFL (`salidas/2026-11-16_calibracion_temblor_dfl.json`, con la
     misma función) es igual o mayor que el temblor medido del detector (`instrumento.temblor`: mediana de
     |b[t+1] − 2·b[t] + b[t−1]| con los tres frames con detección);
   - L: la menor de la rejilla cuya racha de fallos media real en la emulación (en esa p y esa σ) es igual o mayor
     que la racha media de fallos medida (frames seguidos con balón del ATD y sin detección a 3 m o menos). Con L = 1
     los fallos son independientes y su racha media real es 1/p (precisión de la bitácora, 16/11 a las 17:00).
   Pasa si esa celda pasa con el `D` de las etiquetas. Fuera de la rejilla (cobertura menor que 0,5, temblor mayor
   que el de σ = 0,25 o racha mayor que la mayor de la emulación) no pasa. Al lado, sin voto, la celda que sale si L
   se compara con la etiqueta de la rejilla (la regla literal de las 15:50).

Global: «SIGUE» si cumplen la 1, la 2 y la 5; «NO SIGUE» si falla alguna; «sin veredicto» si falta la emulación, si
no es la variante fijada (recorte de 320 px ampliado ×2, confianza 0,10) o si el vídeo no decodifica 199.319 frames.

Cómo mide:

- **Muestra:** `--tramos` tramos de `--largo` frames seguidos (40 de 375 por defecto: 10 minutos de vídeo),
  repartidos de forma determinista y uniforme por los dos tramos evaluados empezando cada uno en su saque (antes del
  saque de la 2ª parte todo es `D`: FAQ y `possession.dead_ball.pre_kickoff`), en proporción a su largo, y dejando
  dentro los frames t+4 que se usan. Por debajo de `MINIMO_TRAMOS` tramos o `MINIMO_FRAMES` frames solo se admite
  `--ensayo`: con una muestra pequeña los «agregados» serían valores de unos pocos frames.
- **Vídeo:** lectura secuencial desde el frame 0 (`detector.leer_frames`): un salto con CAP_PROP_POS_FRAMES no
  garantiza el frame exacto. Se comprueba la resolución y, al final, cuántos frames decodifica el vídeo entero.
- **Desfase:** el balón del ATD llega `BALL_LEAD` = 4 frames tarde (`possession/ball.py`). La referencia del frame t
  es el balón del ATD en t+4; los jugadores, los de t. Como comprobación de la alineación se imprime el acuerdo con
  el ATD en t+d para d de −8 a +12, frame a frame, y el d de menor mediana en cada parte.
- **Variante:** por defecto, la fijada: `roi`, un recorte de `--lado` = 320 px alrededor de la proyección del balón
  del ATD en t+4, ampliado `--factor` = 2. Con `roi`, los frames sin balón del ATD no se detectan (se cuentan).
  `nativa` (imagen entera) y `x2` (imagen entera ×2; solo con `--ensayo` o `--forzar`: tarda de 6 a 8 horas) quedan
  para comparar, sin veredicto.
- **Al campo:** cada detección se lleva al campo con la homografía del frame t. La trayectoria del detector (la de B5
  en la bitácora): en cada frame con balón del ATD dentro del campo, la detección de más confianza a 5 m o menos de
  él, entre las que caen dentro del campo ±3 m (si no hay, sin balón).
- **Base:** los frames con balón del ATD en t+4 **dentro del campo** y homografía válida. Los de balón del ATD fuera
  del campo quedan fuera de las condiciones y se cuentan.
- **Por tramos:** toques, temblor y rachas se calculan tramo a tramo y se suman. Nunca se concatenan tramos.

Imprime un JSON con solo agregados: porcentajes con sus recuentos, percentiles, recuentos por minuto y tiempos. Nada
por frame, ningún número de frame ni ninguna posición. Por stderr, el paso en que está y el % de la muestra hecho
(solo depende del tamaño de la muestra, no de lo que hay en cada frame). Si falla, imprime solo el tipo de error y las
líneas del código.

Uso, desde la raíz del repo, con el entorno que tiene torch, ultralytics, opencv, numpy y pandas:

    python validation/balon_video/detector.py --descargar                          # una vez
    python validation/partido/balon_video_sondeo.py --ensayo --tramos 1 --largo 50 # ensayo corto
    python validation/partido/balon_video_sondeo.py                                # la medida

El ensayo solo imprime versiones, backend, hilos, ms por frame decodificado y detectado (cronometrado en imágenes
negras del tamaño real: no depende del ATD), horas estimadas y «ensayo correcto». Lee el ATD entero y decodifica el
vídeo hasta su tramo, hacia la mitad de la 1ª parte. La medida decodifica el vídeo entero (para contar sus frames).
"""

import argparse
import importlib.util
import json
import os
import sys
import time
import traceback
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "validation", "balon_video"))
import games  # noqa: E402
from possession import dead_ball, tracking  # noqa: E402
from possession.ball import BALL_LEAD  # noqa: E402
import detector as det  # noqa: E402
import toques  # noqa: E402

FICHEROS = ["video", "atd_meta", "atd_raw", "homography"]
ANCHO_IMAGEN, ALTO_IMAGEN = 1920, 1080  # px: el vídeo táctico (DATA.md)
SALIDAS = os.path.join(RAIZ, "validation", "balon_video", "salidas")
EMULACION = os.path.join(SALIDAS, "2026-11-16_emulacion_dfl.json")
TEMBLOR_DFL = os.path.join(SALIDAS, "2026-11-16_calibracion_temblor_dfl.json")
PARTIDOS_DFL = 7

TRAMOS, LARGO = 40, 375  # 40 tramos de 15 s: 10 minutos de vídeo
MINIMO_TRAMOS, MINIMO_FRAMES = 10, 3000  # por debajo, solo --ensayo (2 minutos repartidos en 10 sitios)
MARGEN_CAMPO = 3.0  # m: para la trayectoria, detecciones fuera del campo más de esto, fuera
RADIO_ACIERTO = 3.0  # m: condición 1, y un fallo de las rachas
RADIO_LEJOS = 5.0  # m: condición 2, y radio para elegir la detección de la trayectoria
DESFASES = tuple(range(-8, 13))  # frames: comprobación de la alineación, de uno en uno
UMBRAL_C1 = 70  # % de frames con balón del ATD con una detección a RADIO_ACIERTO m o menos (o más)
UMBRAL_C2 = 10  # % de detecciones a más de RADIO_LEJOS m (o menos)
UMBRAL_C3 = 10  # toques por minuto (descriptiva desde la corrección del 16/11)
PERCENTILES = (5, 25, 50, 75, 95)
# Variante B (bitácora, «Variante B», 16/11, 22:10): la misma 1b con confianza 0,25, el otro umbral que midió la puerta 0.
# No se admite ningún otro valor.
CONF_B = 0.25


class ErrorSondeo(Exception):
    """Un error con un mensaje sin datos del partido (se puede imprimir tal cual)."""


# -- muestra ---------------------------------------------------------------------------------------------------------

def bloques_con_juego(game=games.GAME):
    """Los tramos evaluados, cada uno empezando en su saque: antes del de la 2ª parte todo es `D` (FAQ)."""
    vivo = ~dead_ball.pre_kickoff(game)
    return [(a + int(np.argmax(vivo[a:b])), b) for a, b in tracking.evaluated_blocks(game)]


def muestra(bloques, tramos=TRAMOS, largo=LARGO, adelanto=BALL_LEAD):
    """[(inicio, fin)] de `tramos` tramos de `largo` frames seguidos, con el fin sin incluir.

    Se reparten entre los `bloques` en proporción a su largo, por el método del mayor resto (empates, al bloque
    anterior). Dentro de cada bloque, los inicios posibles son los que dejan dentro también los frames t + `adelanto`;
    se reparten de forma uniforme: el j-ésimo de k empieza en el punto (j + 0,5)/k de ese rango. Determinista y sin
    solapes (si no caben, da error). El mínimo de muestra no va aquí sino en `main`: la prueba usa muestras pequeñas.
    """
    bloques = [(int(a), int(b)) for a, b in bloques]
    tramos, largo, adelanto = int(tramos), int(largo), max(0, int(adelanto))
    if tramos < 1 or largo < 1:
        raise ErrorSondeo("hace falta al menos un tramo de al menos un frame")
    largos = np.array([b - a for a, b in bloques], dtype=np.float64)
    cuota = tramos * largos / largos.sum()
    k = np.floor(cuota).astype(int)
    resto = cuota - k
    for i in sorted(range(len(bloques)), key=lambda i: (-resto[i], i))[:tramos - int(k.sum())]:
        k[i] += 1
    salida = []
    for (a, b), ki in zip(bloques, k):
        if ki == 0:
            continue
        posibles = (b - a) - largo - adelanto + 1
        paso = posibles / float(ki)
        if posibles < 1 or paso < largo:
            raise ErrorSondeo("los tramos pedidos no caben sin solaparse en los tramos evaluados")
        for j in range(ki):
            inicio = a + int(np.floor((j + 0.5) * paso))
            salida.append((inicio, inicio + largo))
    return salida


def desplazado(valores, d):
    """valores[t + d] en cada t, NaN donde t + d se sale del array. Sobre el array entero, antes de cortar tramos."""
    valores = np.asarray(valores, dtype=np.float64)
    salida = np.full(len(valores), np.nan)
    if d >= 0:
        salida[:len(valores) - d] = valores[d:]
    else:
        salida[-d:] = valores[:len(valores) + d]
    return salida


# -- agregados -------------------------------------------------------------------------------------------------------

def _percentiles(valores, decimales=2):
    valores = np.asarray(valores, dtype=np.float64)
    valores = valores[np.isfinite(valores)]
    if not len(valores):
        return None
    return {"p{}".format(p): round(float(np.percentile(valores, p)), decimales) for p in PERCENTILES}


def _pct(parte, total, decimales=2):
    """Solo para imprimir: los «cumple» se calculan con enteros (`al_menos`, `como_mucho`)."""
    return round(100.0 * float(parte) / float(total), decimales) if total else None


def al_menos(parte, total, pct):
    """parte/total ≥ pct %, con enteros (sin redondear): 6302 de 9003 es 69,9989 % y no llega a 70."""
    return None if not total else bool(100 * int(parte) >= int(pct) * int(total))


def como_mucho(parte, total, pct):
    """parte/total ≤ pct %, con enteros."""
    return None if not total else bool(100 * int(parte) <= int(pct) * int(total))


def _dentro(x, y, largo, ancho, margen=0.0):
    with np.errstate(invalid="ignore"):
        return (np.isfinite(x) & np.isfinite(y) & (x >= -margen) & (x <= largo + margen)
                & (y >= -margen) & (y <= ancho + margen))


def _mas_cercana(dets, x, y):
    """Distancia de (x, y) a la detección más cercana de `dets` (m, 3); inf si no hay."""
    if not len(dets) or not np.isfinite(x) or not np.isfinite(y):
        return np.inf
    return float(np.min(np.hypot(dets[:, 0] - x, dets[:, 1] - y)))


def valores_temblor(x, y, activo):
    """Los valores que entran en `instrumento.temblor` (experimento 2), con su mismo criterio: |b[t+1] − 2·b[t] +
    b[t−1]| (norma en x e y) donde los tres frames tienen balón y el del medio está activo. Copia de
    `validation/balon_video/calibrar_temblor_dfl.valores_temblor` (importarla arrastraría el harness); la prueba
    comprueba que su mediana es la de `instrumento.temblor`. Por tramo: la mediana se hace de todos los tramos juntos."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3:
        return np.empty(0)
    ok = np.isfinite(x[:-2]) & np.isfinite(x[1:-1]) & np.isfinite(x[2:]) & np.asarray(activo, dtype=bool)[1:-1]
    d2 = np.hypot(x[2:] - 2 * x[1:-1] + x[:-2], y[2:] - 2 * y[1:-1] + y[:-2])
    return d2[ok]


def rachas(mascara):
    """[(inicio, fin)] de cada racha seguida de True, con el fin sin incluir."""
    borde = np.diff(np.concatenate(([0], np.asarray(mascara, dtype=np.int8), [0])))
    return list(zip(np.flatnonzero(borde == 1).tolist(), np.flatnonzero(borde == -1).tolist()))


# -- condición 5 -----------------------------------------------------------------------------------------------------

def cargar_condicion_5(ruta_emulacion, ruta_temblor):
    """(emulación, temblor de la DFL por σ) de los JSON de `emular_dfl.py` y `calibrar_temblor_dfl.py --json`.

    Comprueba que son de los 7 partidos, que la emulación decide con el `D` de las etiquetas («oraculo») y que el
    temblor está calibrado para cada σ de la rejilla. Da error si no: mejor saberlo antes del bucle largo.
    """
    with open(ruta_emulacion, encoding="utf-8") as f:
        emulacion = json.load(f)
    with open(ruta_temblor, encoding="utf-8") as f:
        temblor = json.load(f)
    if len(emulacion.get("partidos", [])) != PARTIDOS_DFL or len(temblor.get("partidos", [])) != PARTIDOS_DFL:
        raise ErrorSondeo("la emulación o la calibración del temblor no son de los {} partidos".format(PARTIDOS_DFL))
    if emulacion.get("regla", {}).get("d") != "oraculo":
        raise ErrorSondeo("la emulación no decide con el D de las etiquetas")
    por_sigma = {float(f["sigma"]): float(f["temblor"]) for f in temblor["temblor_por_sigma"]}
    rejilla = emulacion["rejilla"]
    if any(float(s) not in por_sigma for s in rejilla["sigma"]):
        raise ErrorSondeo("falta el temblor de la DFL de algún σ de la rejilla")
    celdas = {}
    for fila in emulacion["celdas"].values():
        celdas[(float(fila["p"]), float(fila["sigma"]), int(fila["L"]))] = fila
    for p in rejilla["p"]:
        for s in rejilla["sigma"]:
            for l in rejilla["L"]:
                if (float(p), float(s), int(l)) not in celdas:
                    raise ErrorSondeo("a la emulación le falta alguna celda de la rejilla")
    return {"rejilla": {"p": sorted(float(p) for p in rejilla["p"]), "sigma": sorted(float(s) for s in rejilla["sigma"]),
                        "L": sorted(int(l) for l in rejilla["L"])},
            "celdas": celdas, "temblor_dfl": {float(s): por_sigma[float(s)] for s in rejilla["sigma"]}}


def leer_condicion_5(aciertos, n_base, temblor, racha, cond5):
    """La celda (p, σ, L) que se lee y si pasa, con la regla de la bitácora; y, sin voto, la celda con la racha real.

    - p: la mayor de la rejilla con aciertos/n_base ≥ p (con enteros: p va en milésimas);
    - σ: la menor de la rejilla cuyo temblor en la DFL es igual o mayor que `temblor`;
    - L: la menor de la rejilla cuya racha de fallos media REAL en la emulación (en esa p y esa σ) es igual o mayor que
      `racha` (sin fallos, la menor). Precisión de la bitácora del 16/11 a las 17:00, antes de medir: con L = 1 los
      fallos son independientes y su racha media es 1/p, no 1, así que comparar con la etiqueta no dejaba salir nunca L = 1.
      La lectura con la etiqueta se imprime al lado, sin voto.
    Fuera de la rejilla no pasa. Sin `cond5` (no se cargó la emulación), «pasa» es None.
    """
    salida = {"cumple": None, "celda": None, "motivo": None}
    if cond5 is None:
        salida["motivo"] = "falta la emulación (salidas/2026-11-16_emulacion_dfl.json o --emulacion)"
        return salida
    rej = cond5["rejilla"]
    if not n_base or temblor is None:
        salida["motivo"] = "no hay frames con balón del ATD o no hay ternas para el temblor"
        return salida
    ps = [p for p in rej["p"] if 1000 * int(aciertos) >= int(round(1000 * p)) * int(n_base)]
    sigmas = [s for s in rej["sigma"] if cond5["temblor_dfl"][s] >= temblor]
    fuera = []
    if not ps:
        fuera.append("cobertura por debajo de {:g}".format(rej["p"][0]))
    if not sigmas:
        fuera.append("temblor mayor que el de σ = {:g} en la DFL".format(rej["sigma"][-1]))
    if fuera:
        salida.update(cumple=False, motivo="fuera de la rejilla: " + "; ".join(fuera))
        return salida
    p, s = max(ps), min(sigmas)
    reales = {l2: cond5["celdas"][(p, s, l2)].get("racha_de_fallos_media_real") for l2 in rej["L"]}
    salida["racha_real_de_la_emulacion_por_L"] = {str(l2): None if v is None else round(float(v), 2)
                                                  for l2, v in reales.items()}
    ls = [l2 for l2 in rej["L"] if reales[l2] is not None and (racha is None or reales[l2] >= racha)]
    # Sin voto: la regla literal de las 15:50 (L comparada con la etiqueta de la rejilla).
    por_etiqueta = [l2 for l2 in rej["L"] if racha is None or l2 >= racha]
    salida["sin_voto_L_por_etiqueta"] = (
        {"celda": {"p": p, "sigma": s, "L": min(por_etiqueta)},
         "pasa": bool(cond5["celdas"][(p, s, min(por_etiqueta))]["oraculo"]["veredicto"]["pasa"])}
        if por_etiqueta else {"celda": None, "pasa": False})
    if not ls:
        salida.update(cumple=False, motivo="fuera de la rejilla: racha de fallos mayor que la mayor de la emulación")
        return salida
    l = min(ls)
    fila = cond5["celdas"][(p, s, l)]
    salida.update(cumple=bool(fila["oraculo"]["veredicto"]["pasa"]), celda={"p": p, "sigma": s, "L": l},
                  motivo="regla de la bitácora (L por la racha real de la emulación)")
    if "sin_decidir" in fila["oraculo"]["veredicto"]:  # con réplicas: solo informativo (emular_dfl.py), no vota
        salida["sin_decidir_informativo"] = bool(fila["oraculo"]["veredicto"]["sin_decidir"])
    return salida


# -- la medida -------------------------------------------------------------------------------------------------------

def medir(fuente_de_frames, trk, matrices, validas, detector, tramos_muestra, roi=False, adelanto=BALL_LEAD,
          desfases=DESFASES, estado_lectura=None, progreso=None, n_total=None, bloques=None, cond5=None,
          variante_fijada=True):
    """Los agregados de la puerta 1b. Pura salvo por los tiempos: no abre nada.

    - `fuente_de_frames`: iterable de (frame, imagen), con exactamente los frames de `tramos_muestra` en orden. Si da
      otro frame o se acaba antes, error.
    - `trk`: el `Tracking` (balón y jugadores en metros, por frame de vídeo). `matrices`, `validas`: la homografía
      por frame (`starter/load_homography.load`).
    - `detector(imagen, centro)`: devuelve un array (k, ≥3) con x, y en píxeles del frame en las dos primeras
      columnas y la confianza en la última; `centro` es None o el píxel (x, y) alrededor del que recortar.
    - `roi`: si es True, solo se detecta en los frames con balón del ATD en t + `adelanto` dentro del campo, con
      `centro` en su proyección.
    - `estado_lectura`: el diccionario de `detector.leer_frames` (frames leídos, segundos y, si leyó hasta el final,
      frames decodificados). `progreso(fracción)`, si se da, se llama cada 1/20 de la muestra: solo depende de su
      tamaño. `n_total`: frames del partido. `bloques`: las partes (por defecto `trk.blocks`), para la alineación.
    - `cond5`: lo de `cargar_condicion_5`, o None. `variante_fijada`: si es False, el global sale sin veredicto.
    """
    n = len(trk.bx)
    if len(matrices) != n or len(validas) != n:
        raise ErrorSondeo("la homografía no tiene un frame por frame de vídeo")
    largo, ancho = trk.pitch
    fps = trk.fps
    n_total = n if n_total is None else int(n_total)
    bloques = list(trk.blocks if bloques is None else bloques)
    validas = np.asarray(validas, dtype=bool) & np.isfinite(matrices).all(axis=(1, 2))
    bx, by = np.asarray(trk.bx, dtype=np.float64), np.asarray(trk.by, dtype=np.float64)
    ref_x, ref_y = desplazado(bx, adelanto), desplazado(by, adelanto)
    frames = np.concatenate([np.arange(a, b) for a, b in tramos_muestra]).astype(np.int64)
    m = len(frames)
    ref_finita = np.isfinite(ref_x[frames]) & np.isfinite(ref_y[frames])
    hay_ref = _dentro(ref_x[frames], ref_y[frames], largo, ancho) & validas[frames]

    detecciones = [np.zeros((0, 3))] * m  # (x, y, conf) en metros, dentro del campo ± MARGEN_CAMPO
    crudas = np.zeros(m, dtype=np.int64)  # detecciones antes de quitar las de fuera del campo
    intentado = np.zeros(m, dtype=bool)
    n_det_todas = n_lejos_todas = 0  # condición 2: todas las detecciones de los frames base, sin filtrar
    sin_homografia = sin_centro = 0
    seg_leyendo = seg_detectando = 0.0
    iterador = iter(fuente_de_frames)
    cada = max(1, m // 20)
    for k in range(m):
        inicio = time.perf_counter()
        try:
            frame, imagen = next(iterador)
        except StopIteration:
            raise ErrorSondeo("la fuente de frames se acaba antes de la muestra")
        seg_leyendo += time.perf_counter() - inicio
        if int(frame) != int(frames[k]):
            raise ErrorSondeo("la fuente de frames no da los frames de la muestra en orden")
        t = int(frames[k])
        # Aquí, antes de cualquier `continue`: los puntos de progreso solo dependen de m, no de lo que hay en t.
        if progreso is not None and (k + 1) % cada == 0:
            progreso((k + 1) / float(m))
        if not validas[t]:
            sin_homografia += 1
            continue
        centro = None
        if roi:
            if not hay_ref[k]:
                continue
            cx, cy = det.pixeles_desde_campo(matrices[t], ref_x[t], ref_y[t], largo, ancho)
            if not (np.isfinite(cx) and np.isfinite(cy)):
                sin_centro += 1
                continue
            centro = (float(cx), float(cy))
        inicio = time.perf_counter()
        d = np.asarray(detector(imagen, centro), dtype=np.float64)
        if d.ndim == 1 and d.size == 0:
            d = d.reshape(0, 3)
        seg_detectando += time.perf_counter() - inicio
        intentado[k] = True
        if d.ndim != 2 or (len(d) and d.shape[1] < 3):
            raise ErrorSondeo("el detector no devuelve un array (k, ≥3)")
        crudas[k] = len(d)
        if len(d):
            fx, fy = det.campo_desde_pixeles(matrices[t], d[:, 0], d[:, 1], largo, ancho)
            if hay_ref[k]:
                with np.errstate(invalid="ignore"):
                    cerca = np.hypot(fx - ref_x[t], fy - ref_y[t]) <= RADIO_LEJOS  # NaN: lejos
                n_det_todas += len(d)
                n_lejos_todas += int(np.sum(~cerca))
            dentro = _dentro(fx, fy, largo, ancho, MARGEN_CAMPO)
            detecciones[k] = np.column_stack([fx[dentro], fy[dentro], d[dentro, -1]])
    try:
        next(iterador)  # con `hasta_el_final`, aquí el lector decodifica el resto del vídeo y cuenta sus frames
        raise ErrorSondeo("la fuente de frames da más frames que la muestra")
    except StopIteration:
        pass

    # Condiciones 1 y 2, la trayectoria del detector y la confianza: en los frames base.
    base = hay_ref & intentado
    dmin = np.full(m, np.inf)
    tray_x, tray_y, tray_conf = np.full(m, np.nan), np.full(m, np.nan), np.full(m, np.nan)
    tray_dist = np.full(m, np.nan)
    n_det_base = n_lejos = 0
    for k in np.flatnonzero(base):
        t = frames[k]
        dk = detecciones[k]
        if not len(dk):
            continue
        dist = np.hypot(dk[:, 0] - ref_x[t], dk[:, 1] - ref_y[t])
        dmin[k] = float(dist.min())
        n_det_base += len(dk)
        n_lejos += int(np.sum(dist > RADIO_LEJOS))
        cerca = np.flatnonzero(dist <= RADIO_LEJOS)
        if len(cerca):
            # Más confianza primero; empates, la de menor x y luego menor y (el orden de `detector.detectar`).
            j = cerca[np.lexsort((dk[cerca, 1], dk[cerca, 0], -dk[cerca, 2]))[0]]
            tray_x[k], tray_y[k], tray_conf[k], tray_dist[k] = dk[j, 0], dk[j, 1], dk[j, 2], dist[j]
    n_base = int(base.sum())
    aciertos = int(np.sum(dmin[base] <= RADIO_ACIERTO))
    con_det = base & np.isfinite(dmin)
    n_tray = int(np.isfinite(tray_x[base]).sum())

    # Alineación: el acuerdo con el ATD en t+d, en un mismo conjunto de frames para todos los d; y por parte.
    comun = base.copy()
    refs = {}
    for dd in desfases:
        rx, ry = desplazado(bx, dd)[frames], desplazado(by, dd)[frames]
        refs[dd] = (rx, ry)
        comun &= _dentro(rx, ry, largo, ancho)
    distancias = {dd: np.full(m, np.inf) for dd in desfases}
    for dd in desfases:
        rx, ry = refs[dd]
        for k in np.flatnonzero(comun):
            distancias[dd][k] = _mas_cercana(detecciones[k], rx[k], ry[k])

    def mejor_desfase(mascara):
        candidatos = []
        for dd in desfases:
            dist = distancias[dd][mascara]
            if np.isfinite(dist).any():
                candidatos.append((float(np.median(dist[np.isfinite(dist)])), -float(np.mean(dist <= RADIO_ACIERTO)),
                                   int(dd)))
        return min(candidatos)[2] if candidatos else None

    alineacion = {}
    for dd in desfases:
        dist = distancias[dd][comun]
        alineacion["{:+d}".format(dd)] = {
            "pct_con_deteccion_a_3m": _pct(np.sum(dist <= RADIO_ACIERTO), len(dist)),
            "mediana_distancia_m": round(float(np.median(dist[np.isfinite(dist)])), 3)
            if np.isfinite(dist).any() else None}
    parte = np.full(m, -1)
    for i, (a0, b0) in enumerate(bloques):
        parte[(frames >= a0) & (frames < b0)] = i
    por_parte = {"parte_{}".format(i + 1): mejor_desfase(comun & (parte == i)) for i in range(len(bloques))}

    # Detecciones por frame y frames sin balón del ATD.
    n_int = int(intentado.sum())
    por_frame = np.array([len(detecciones[k]) for k in range(m)])
    sin_ref = intentado & ~hay_ref
    todas_conf = np.concatenate([detecciones[k][:, 2] for k in np.flatnonzero(base)] + [np.zeros(0)])

    # Tramo a tramo y sumados (nunca se concatenan tramos): toques y ruido (3 y 4), temblor y rachas de fallos (5).
    nombre_t4 = "atd_en_t_mas_{}".format(adelanto)
    cuentas = {nombre: {"toques": 0, "ruido": 0, "eventos": 0, "frames_visibles": 0}
               for nombre in ("detector", nombre_t4, "atd_en_t")}
    trozos_temblor = []
    n_rachas = frames_fallo = n_rachas_interior = frames_fallo_interior = 0
    pos = 0
    for a, b in tramos_muestra:
        sl = slice(pos, pos + (b - a))
        fr = frames[sl]
        mascara = base[sl]
        px, py = trk.px[fr], trk.py[fr]
        for nombre, (x, y) in (("detector", (tray_x[sl], tray_y[sl])),
                               (nombre_t4, (ref_x[fr], ref_y[fr])),
                               ("atd_en_t", (bx[fr], by[fr]))):
            c = toques.contar(x, y, px, py, trk.team, fps, mascara=mascara)
            for clave in c:
                cuentas[nombre][clave] += c[clave]
            cuentas[nombre]["frames_visibles"] += int(np.sum(mascara & np.isfinite(x) & np.isfinite(y)))
        trozos_temblor.append(valores_temblor(tray_x[sl], tray_y[sl], mascara))
        fallo = mascara & ~(dmin[sl] <= RADIO_ACIERTO)
        for i0, i1 in rachas(fallo):
            n_rachas += 1
            frames_fallo += i1 - i0
            if i0 > 0 and i1 < b - a:
                n_rachas_interior += 1
                frames_fallo_interior += i1 - i0
        pos += b - a
    toques_salida = {}
    for nombre, c in cuentas.items():
        toques_salida[nombre] = {
            "toques_por_minuto_de_su_balon_visible": toques.por_minuto(c["toques"], c["frames_visibles"], fps),
            "ruido_por_minuto_de_su_balon_visible": toques.por_minuto(c["ruido"], c["frames_visibles"], fps),
            "toques_por_minuto_de_frames_con_balon_del_atd": toques.por_minuto(c["toques"], n_base, fps),
            "ruido_por_minuto_de_frames_con_balon_del_atd": toques.por_minuto(c["ruido"], n_base, fps),
            "toques": c["toques"], "ruido": c["ruido"], "eventos": c["eventos"],
            "minutos_de_su_balon_visible": round(c["frames_visibles"] / float(fps) / 60.0, 2)}
    toques_salida["minutos_con_balon_del_atd"] = round(n_base / float(fps) / 60.0, 2)
    valores_t = np.concatenate(trozos_temblor) if trozos_temblor else np.empty(0)
    temblor = float(np.median(valores_t)) if len(valores_t) else None
    racha = frames_fallo / float(n_rachas) if n_rachas else None
    medidas_5 = {
        "aciertos": aciertos, "frames_con_balon_del_atd": n_base,
        "temblor_del_detector_m": None if temblor is None else round(temblor, 4),
        "ternas_del_temblor": int(len(valores_t)),
        "racha_media_de_fallos": None if racha is None else round(racha, 2),
        "rachas_de_fallos": int(n_rachas), "frames_de_fallo": int(frames_fallo),
        "racha_media_sin_las_que_tocan_un_borde_de_tramo":
            round(frames_fallo_interior / float(n_rachas_interior), 2) if n_rachas_interior else None,
        "rachas_sin_las_que_tocan_un_borde_de_tramo": int(n_rachas_interior)}

    # Veredictos: deciden la 1, la 2 y la 5; la 3 y la 4 son descriptivas.
    v1 = al_menos(aciertos, n_base, UMBRAL_C1)
    v2 = como_mucho(n_lejos_todas, n_det_todas, UMBRAL_C2)
    c5 = leer_condicion_5(aciertos, n_base, temblor, racha, cond5)
    det_tq = toques_salida["detector"]
    atd_tq = toques_salida[nombre_t4]
    decodificados = (estado_lectura or {}).get("frames_decodificados")
    veredictos = {
        "condicion_1": {"valor_pct": _pct(aciertos, n_base), "aciertos": aciertos, "frames": n_base,
                        "umbral": ">= {} %".format(UMBRAL_C1), "cumple": v1},
        "condicion_2": {"valor_pct": _pct(n_lejos_todas, n_det_todas), "lejos": int(n_lejos_todas),
                        "detecciones": int(n_det_todas), "umbral": "<= {} %".format(UMBRAL_C2), "cumple": v2,
                        "sin_voto_solo_dentro_del_campo_pct": _pct(n_lejos, n_det_base)},
        "condicion_3_descriptiva": {
            "toques_por_minuto_del_detector": det_tq["toques_por_minuto_de_su_balon_visible"],
            "toques_por_minuto_del_atd_en_t_mas_{}".format(adelanto): atd_tq["toques_por_minuto_de_su_balon_visible"],
            "referencia_escrita": ">= {} (ya no decide)".format(UMBRAL_C3)},
        "condicion_4_descriptiva": {
            "ruido_por_minuto_del_detector": det_tq["ruido_por_minuto_de_su_balon_visible"],
            "ruido_por_minuto_del_atd_en_t_mas_{}".format(adelanto): atd_tq["ruido_por_minuto_de_su_balon_visible"]},
        "condicion_5": c5,
    }
    if not variante_fijada:
        veredictos["global"] = "sin veredicto: no es la variante fijada (roi, 320 px, ×2, confianza 0,10 o 0,25)"
    elif decodificados is not None and int(decodificados) != n_total:
        veredictos["global"] = "sin veredicto: el vídeo no decodifica el número de frames esperado"
    elif v1 is None or v2 is None:
        veredictos["global"] = "sin veredicto: la condición 1 o la 2 no se puede calcular"
    elif not (v1 and v2):
        veredictos["global"] = "NO SIGUE"
    elif c5["cumple"] is None:
        veredictos["global"] = "sin veredicto: falta la condición 5 ({})".format(c5["motivo"])
    else:
        veredictos["global"] = "SIGUE" if c5["cumple"] else "NO SIGUE"

    # Tiempos.
    leidos = (estado_lectura or {}).get("frames_leidos")
    seg_lectura = (estado_lectura or {}).get("segundos_leyendo", seg_leyendo)
    tiempos = {"segundos_leyendo_video": round(seg_leyendo, 1),
               "ms_por_frame_decodificado": round(1000.0 * seg_lectura / leidos, 3) if leidos else None,
               "segundos_detectando": round(seg_detectando, 1),
               "ms_por_frame_detectado": round(1000.0 * seg_detectando / n_int, 2) if n_int else None}
    if leidos and n_int:
        horas = n_total * (seg_lectura / leidos + seg_detectando / n_int) / 3600.0
        tiempos["horas_estimadas_partido_entero"] = round(horas, 2)
        tiempos["frames_partido_entero"] = n_total
        if roi:
            tiempos["nota"] = "con roi se detecta solo donde el ATD ve el balón: la estimación es un techo"

    return {
        "frames_muestreados": m,
        "tramos": len(tramos_muestra),
        "frames_sin_homografia_valida": int(sin_homografia),
        "frames_con_balon_del_atd_en_t_mas_{}_dentro_del_campo".format(adelanto): n_base,
        "frames_con_balon_del_atd_en_t_mas_{}_fuera_del_campo".format(adelanto):
            int(np.sum(ref_finita & ~_dentro(ref_x[frames], ref_y[frames], largo, ancho) & validas[frames])),
        "frames_detectados": n_int,
        "frames_sin_detectar_por_roi_sin_balon_del_atd": int(np.sum(~hay_ref & validas[frames])) if roi else 0,
        "frames_roi_con_centro_no_finito": int(sin_centro),
        "condicion_1_pct_con_deteccion_a_3m": _pct(aciertos, n_base),
        "distancia_a_la_deteccion_mas_cercana_m": _percentiles(dmin[con_det]),
        "pct_frames_con_balon_del_atd_sin_ninguna_deteccion": _pct(np.sum(base & ~np.isfinite(dmin)), n_base),
        "condicion_2_pct_detecciones_a_mas_de_5m": _pct(n_lejos_todas, n_det_todas),
        "detecciones_en_frames_con_balon_del_atd": int(n_det_todas),
        "trayectoria_del_detector": {
            "pct_de_frames_con_balon_del_atd": _pct(n_tray, n_base),
            "pct_con_la_deteccion_elegida_a_mas_de_3m": _pct(np.sum(tray_dist[base] > RADIO_ACIERTO), n_tray)},
        "alineacion_por_desfase": {"frames_comunes": int(comun.sum()), "por_desfase": alineacion,
                                   "desfase_con_menor_mediana": mejor_desfase(comun),
                                   "desfase_con_menor_mediana_por_parte": por_parte, "esperado": adelanto},
        "detecciones_por_frame": {
            "media_dentro_del_campo": round(float(por_frame[intentado].mean()), 3) if n_int else None,
            "media_antes_de_quitar_las_de_fuera": round(float(crudas[intentado].mean()), 3) if n_int else None,
            "pct_frames_con_0": _pct(np.sum(intentado & (por_frame == 0)), n_int),
            "pct_frames_con_1": _pct(np.sum(intentado & (por_frame == 1)), n_int),
            "pct_frames_con_2_o_mas": _pct(np.sum(intentado & (por_frame >= 2)), n_int)},
        "confianza": {"todas_las_detecciones_con_balon_del_atd": _percentiles(todas_conf, 4),
                      "trayectoria_del_detector": _percentiles(tray_conf, 4)},
        "pct_frames_sin_balon_del_atd_con_alguna_deteccion_en_el_campo":
            None if roi else _pct(np.sum(sin_ref & (por_frame > 0)), int(sin_ref.sum())),
        "toques_por_tramos": toques_salida,
        "medidas_de_la_condicion_5": medidas_5,
        "tiempos": tiempos,
        "veredictos": veredictos,
    }


# -- lo real ---------------------------------------------------------------------------------------------------------

def informe_de_error(error):
    pila = traceback.extract_tb(error.__traceback__)
    lineas = ["{}:{} ({})".format(os.path.basename(f.filename), f.lineno, f.name) for f in pila]
    return "ERROR {} en {}".format(type(error).__name__, " <- ".join(reversed(lineas)))


def _paso(texto):
    sys.stderr.write("  {}\n".format(texto))
    sys.stderr.flush()


def _progreso(fraccion):
    # Solo el %: el tiempo por punto de control diría, con roi, cuántos frames de ese trozo tenían balón del ATD.
    sys.stderr.write("\r  {:5.1f} %".format(100.0 * fraccion))
    sys.stderr.flush()


def comprobar_argumentos(args):
    """(factor, roi, variante_fijada). Todo lo que no necesita ni los datos ni torch: va antes de nada."""
    if args.factor is not None and args.variante != "roi":
        raise ErrorSondeo("--factor solo vale con --variante roi (nativa es ×1 y x2 es ×2)")
    if not args.ensayo and (args.tramos < MINIMO_TRAMOS or args.tramos * args.largo < MINIMO_FRAMES):
        raise ErrorSondeo("una muestra de menos de {} tramos o de menos de {} frames solo vale con --ensayo: sus "
                          "agregados serían valores de unos pocos frames".format(MINIMO_TRAMOS, MINIMO_FRAMES))
    if args.variante == "x2" and not (args.ensayo or args.forzar):
        raise ErrorSondeo("x2 (la imagen entera ×2) tarda de 6 a 8 horas con la muestra: solo con --ensayo o --forzar")
    factor = {"nativa": 1.0, "x2": 2.0}.get(args.variante, args.factor if args.factor is not None else det.FACTOR)
    roi = args.variante == "roi"
    fijada = (roi and args.lado == det.LADO and float(factor) == float(det.FACTOR)
              and float(args.conf) in (det.CONF, CONF_B))
    return float(factor), roi, fijada


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--variante", choices=("nativa", "x2", "roi"), default="roi",
                    help="roi (la fijada), nativa o x2 (estas dos, sin veredicto)")
    ap.add_argument("--tramos", type=int, default=TRAMOS, help="tramos de frames seguidos (40)")
    ap.add_argument("--largo", type=int, default=LARGO, help="frames de cada tramo (375)")
    ap.add_argument("--lado", type=int, default=det.LADO, help="px del recorte de roi (320)")
    ap.add_argument("--factor", type=float, default=None, help="ampliación del recorte de roi (2)")
    ap.add_argument("--modelo", default=None, help="el .pt (por defecto, el de detector.py --descargar)")
    ap.add_argument("--conf", type=float, default=det.CONF, help="confianza mínima (0,10)")
    ap.add_argument("--hilos", type=int, default=det.HILOS, help="hilos de torch ({})".format(det.HILOS))
    ap.add_argument("--emulacion", default=EMULACION, help="el JSON de emular_dfl.py (condición 5)")
    ap.add_argument("--temblor-dfl", default=TEMBLOR_DFL, help="el JSON de calibrar_temblor_dfl.py --json")
    ap.add_argument("--ensayo", action="store_true", help="prueba corta: solo versiones, tiempos y «ensayo correcto»")
    ap.add_argument("--forzar", action="store_true", help="admite x2 sin --ensayo")
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    factor, roi, fijada = comprobar_argumentos(args)
    faltan = [m for m in ("torch", "ultralytics", "cv2", "pandas") if importlib.util.find_spec(m) is None]
    if faltan:
        raise ErrorSondeo("faltan {}: ejecuta con el venv del balón (torch, ultralytics, opencv, numpy y pandas)"
                          .format(", ".join(faltan)))
    cond5 = None
    if not args.ensayo:
        if os.path.isfile(args.emulacion) and os.path.isfile(args.temblor_dfl):
            cond5 = cargar_condicion_5(args.emulacion, args.temblor_dfl)
        else:
            _paso("aviso: no encuentro la emulación o la calibración del temblor; la condición 5 saldrá sin leer")
    info = games.GAMES[games.GAME]

    # Todo lo que puede fallar, antes del bucle largo: ficheros, modelo, vídeo y muestra.
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el vídeo, el ATD o la homografía del partido: revisa que MTAH_DATA_DIR apunte a la "
              "carpeta de los datos.")
        return 1
    bloques = bloques_con_juego(games.GAME)
    tramos_muestra = muestra(bloques, args.tramos, args.largo, BALL_LEAD)
    ruta_modelo = args.modelo or det.ruta_por_defecto()
    _paso("cargando el modelo (sha256, escaneo y calentamiento)")
    modelo = det.cargar(ruta_modelo, hilos=args.hilos)
    import torch
    hilos_reales = torch.get_num_threads()
    ruta_video = games.video_path(games.GAME, args.data_dir)
    comprobacion = {}
    for _ in det.leer_frames(ruta_video, [], n_esperado=info["n_video_frames"], tamano=(ANCHO_IMAGEN, ALTO_IMAGEN),
                             estado=comprobacion):
        pass
    # Calentamiento a tamaño real y tiempo de detección en imágenes negras: no depende del ATD.
    negra = np.zeros((ALTO_IMAGEN, ANCHO_IMAGEN, 3), dtype=np.uint8)
    centro_fijo = (ANCHO_IMAGEN / 2.0, ALTO_IMAGEN / 2.0) if roi else None
    det.detectar(modelo, negra, args.conf, factor, centro_fijo, args.lado)
    inicio = time.perf_counter()
    for _ in range(3):
        det.detectar(modelo, negra, args.conf, factor, centro_fijo, args.lado)
    ms_detectar = 1000.0 * (time.perf_counter() - inicio) / 3.0
    frames = np.concatenate([np.arange(a, b) for a, b in tramos_muestra])
    lado_red = (args.lado, args.lado) if roi else (ANCHO_IMAGEN, ALTO_IMAGEN)
    _paso("estimado: {:.2f} h como mucho para {} detecciones de {}×{} (más leer el vídeo)".format(
        len(frames) * ms_detectar / 3.6e6, len(frames), int(round(lado_red[0] * factor)),
        int(round(lado_red[1] * factor))))

    from starter import load_homography  # aquí: la prueba sin datos no necesita pandas
    _paso("leyendo el ATD y la homografía (un par de minutos)")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        trk = tracking.from_atd(games.asset_paths(games.GAME, args.data_dir), games.GAME)
        matrices, _, validas = load_homography.load(games.GAME, args.data_dir)

    def detector(imagen, centro):
        return det.detectar(modelo, imagen, args.conf, factor, centro, args.lado)

    estado = {}
    _paso("leyendo el vídeo desde el principio y detectando en la muestra" +
          ("" if args.ensayo else "; después, el resto del vídeo para contar sus frames"))
    fuente = det.leer_frames(ruta_video, frames, n_esperado=info["n_video_frames"],
                             tamano=(ANCHO_IMAGEN, ALTO_IMAGEN), estado=estado, hasta_el_final=not args.ensayo)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        salida = medir(fuente, trk, matrices, validas, detector, tramos_muestra, roi=roi, estado_lectura=estado,
                       progreso=_progreso, n_total=info["n_video_frames"], bloques=bloques, cond5=cond5,
                       variante_fijada=fijada)
    sys.stderr.write("\n")
    parametros = {"variante": args.variante, "variante_fijada": fijada, "factor": factor,
                  "lado_roi": args.lado if roi else None, "conf": args.conf, "tramos": args.tramos,
                  "largo": args.largo}
    if args.ensayo:
        ms_dec = (1000.0 * estado["segundos_leyendo"] / estado["frames_leidos"]) if estado.get("frames_leidos") else None
        horas = None if ms_dec is None else info["n_video_frames"] * (ms_dec + ms_detectar) / 3.6e6
        print(json.dumps({
            "medida": "ensayo del sondeo de la puerta 1b: solo versiones y tiempos",
            "versiones": det.versiones(), "backend_video": estado.get("backend"), "hilos_torch": hilos_reales,
            "parametros": parametros,
            "ms_por_frame_decodificado": None if ms_dec is None else round(ms_dec, 3),
            "ms_por_frame_detectado_en_imagen_negra": round(ms_detectar, 2),
            "horas_estimadas_partido_entero_techo": None if horas is None else round(horas, 2),
            "resultado": "ensayo correcto"}, ensure_ascii=False, indent=1))
        return 0
    cabecera = {
        "medida": "puerta 1b del balón del vídeo (validation/balon_video/BITACORA.md), solo agregados",
        "versiones": det.versiones(),
        "modelo_sha256": det.sha256_de(ruta_modelo)[:12],
        "modelo_revision": det.MODELO_REVISION[:12],
        "hilos_torch": hilos_reales,
        "backend_video": estado.get("backend"),
        "frames_declarados_por_el_contenedor": estado.get("frames_declarados"),
        "frames_decodificados": estado.get("frames_decodificados"),
        "ms_por_frame_detectado_en_imagen_negra": round(ms_detectar, 2),
        "parametros": dict(parametros, adelanto_atd=BALL_LEAD, radio_acierto_m=RADIO_ACIERTO,
                           radio_lejos_m=RADIO_LEJOS, margen_campo_m=MARGEN_CAMPO,
                           emulacion=os.path.basename(args.emulacion) if cond5 else None),
    }
    print(json.dumps(dict(cabecera, **salida), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except (ErrorSondeo, det.ErrorDetector) as e:  # mensajes escritos sin datos del partido
        print("ERROR: {}".format(e))
        sys.exit(1)
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
