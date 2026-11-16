"""Prueba `validation/partido/balon_video_sondeo.py` (puerta 1b) con un partido inventado y frames sintéticos.

    python validation/scripts/prueba_balon_video_sondeo.py

Sin datos de ningún partido. Lo puede ejecutar cualquiera, Claude incluido. El partido inventado tiene 3.000 frames y
dos tramos. El balón «de verdad» va y viene entre dos puntos a 10 m/s (un toque en cada vuelta); el ATD lo da con 4
frames de retraso, como el del partido, y con un hueco. Dos jugadores solo están junto al balón en los frames de cada
vuelta (si se toman los jugadores de otro frame, los toques pasan a ruido); un tercero, quieto y lejos. La homografía
cambia con el frame (un paneo periódico): proyectar con la de otro frame se nota. Cada frame sintético lleva el píxel
del balón de verdad (el del ATD en t+4) pintado con la homografía de ese frame, y el detector falso lo «encuentra»
ahí: así un frame de desfase entre la imagen y su índice se nota. Para que la prueba sea rápida, la imagen es un
objeto con ese píxel, no una matriz de 1920×1080 (el sondeo no mira dentro: se la pasa al detector).

Prueba la muestra (determinista, proporcional, empieza en el saque); las condiciones 1 y 2 con detectores que fallan
por poco a cada lado de los radios; que la 2 cuenta las detecciones de fuera del campo; que la trayectoria se queda
con la de más confianza; el temblor (≈ 2,88·σ con ruido gaussiano) y las rachas de fallos; la lectura de la celda de
la condición 5 y los veredictos; la alineación de uno en uno y por parte; los toques y el suelo de ruido; la variante
roi; que el progreso no depende del ATD; el mínimo de muestra de `main`; los errores de la fuente de frames; que nada
de la salida es por frame. Si hay cv2, escribe un MP4 diminuto y comprueba el lector secuencial y su recuento.
"""

import contextlib
import importlib.util
import io
import itertools
import json
import os
import re
import sys
import tempfile
import types

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
sys.path.insert(0, os.path.join(ROOT, "validation", "experimento2"))
import balon_video_sondeo as bs  # noqa: E402
import detector as det  # noqa: E402  (balon_video_sondeo ya pone validation/balon_video en la ruta)
import instrumento  # noqa: E402
import toques  # noqa: E402
from possession.ball import BALL_LEAD  # noqa: E402
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
A_X, B_X, Y_BALON = 40.0, 48.0, 30.0  # m: el balón va y viene entre estos dos puntos
PASO = 0.4  # m por frame: 10 m/s
HUECO = (701, 741)  # frames del ATD sin balón
H_AFIN = np.array([[1500.0, 0.0, 200.0], [0.0, 800.0, 150.0], [0.0, 0.0, 1.0]])
SX, SY = 1500.0 / LARGO, 800.0 / ANCHO  # px por metro en x e y (el paneo solo traslada)
TRAMOS, LARGO_TRAMO = 8, 150


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def balon_de_verdad():
    """x del balón de verdad en cada frame: una onda triangular entre A_X y B_X; y fija."""
    periodo = int(round(2 * (B_X - A_X) / PASO))  # 40 frames por ida y vuelta
    fase = np.arange(N) % periodo
    mitad = periodo // 2
    x = np.where(fase <= mitad, A_X + PASO * fase, B_X - PASO * (fase - mitad))
    return x, np.full(N, Y_BALON), periodo


def homografias():
    """Una por frame: H_AFIN con la traslación en x desplazada 40·sin(2πt/97) px (un paneo)."""
    matrices = np.repeat(H_AFIN[None], N, axis=0)
    matrices[:, 0, 2] += 40.0 * np.sin(2 * np.pi * np.arange(N) / 97.0)
    return matrices


def partido(atd_fuera_por_tramo=0, tramos=None, tapar=()):
    """El Tracking inventado: el ATD es el balón de verdad con ADELANTO frames de retraso (atd[t+4] = verdad[t]).

    Los jugadores 0 y 1 están en el punto de cada vuelta solo a 2 frames o menos de ella; si no, 10 m más allá.
    `atd_fuera_por_tramo`: en los primeros frames de cada tramo de `tramos`, el ATD en t+4 a 1 m fuera del campo.
    `tapar`: frames t de la muestra cuyo balón del ATD en t+4 se borra.
    """
    vx, vy, periodo = balon_de_verdad()
    bx, by = np.full(N, np.nan), np.full(N, np.nan)
    bx[ADELANTO:], by[ADELANTO:] = vx[:-ADELANTO], vy[:-ADELANTO]
    bx[HUECO[0]:HUECO[1]] = np.nan
    by[HUECO[0]:HUECO[1]] = np.nan
    for a, _ in (tramos or [])[:]:
        if atd_fuera_por_tramo:
            by[a + ADELANTO:a + ADELANTO + atd_fuera_por_tramo] = -1.0
    for t in tapar:
        bx[t + ADELANTO] = by[t + ADELANTO] = np.nan
    fase = np.arange(N) % periodo
    cerca_a = np.minimum(fase, periodo - fase) <= 2
    cerca_b = np.abs(fase - periodo // 2) <= 2
    px = np.column_stack([np.full(N, A_X), np.full(N, B_X), np.full(N, 80.0)])
    py = np.column_stack([np.where(cerca_a, Y_BALON, Y_BALON + 10.0), np.where(cerca_b, Y_BALON, Y_BALON + 10.0),
                          np.full(N, 50.0)])
    team = np.array([0, 1, 0], dtype=np.int8)
    trk = Tracking(bx, by, px, py, team, (LARGO, ANCHO), BLOQUES, 25)
    return trk, homografias(), np.ones(N, dtype=bool), periodo


class Imagen:
    """Lo que el sondeo le pasa al detector: el frame y el píxel del balón pintado (o None)."""

    def __init__(self, t, blanco):
        self.t, self.blanco = t, blanco


def fuente(trk, matrices, tramos, desfase_imagen=0):
    """(frame, imagen) de la muestra: el balón del ATD en t + ADELANTO + desfase_imagen pintado con la homografía
    del frame t, en un bloque de 3×3 px; el detector «ve» su centro, en la convención de ultralytics (i + 0,5)."""
    for a, b in tramos:
        for t in range(a, b):
            s = t + ADELANTO + desfase_imagen
            blanco = None
            if 0 <= s < N and np.isfinite(trk.bx[s]):
                x, y = det.pixeles_desde_campo(matrices[t], trk.bx[s], trk.by[s], LARGO, ANCHO)
                blanco = (float(np.floor(x)) + 0.5, float(np.floor(y)) + 0.5)
            yield t, Imagen(t, blanco)


def detector_falso(temblor_m=0.0, desplazado_m=0.0, extras=(), conf=0.8, falla_cada=None, comprobar_centro=None):
    """Detector falso. `extras`: detecciones de más, como (dx, dy, conf) en píxeles desde el balón. `falla_cada`: no
    devuelve nada en los bloques impares de ese largo (frames t // falla_cada impares)."""
    estado = {"llamadas": 0, "centros": 0}

    def detectar(imagen, centro):
        estado["llamadas"] += 1
        if imagen.blanco is None:
            return np.zeros((0, 3))
        x0, y0 = imagen.blanco
        if centro is not None:
            estado["centros"] += 1
            if comprobar_centro is not None and np.hypot(centro[0] - x0, centro[1] - y0) > comprobar_centro:
                raise AssertionError("el centro del recorte no está en el balón")
        if falla_cada and (imagen.t // falla_cada) % 2 == 1:
            return np.zeros((0, 3))
        x, y = x0 + desplazado_m * SX, y0
        if temblor_m:
            rng = np.random.default_rng([20261116, imagen.t])
            x, y = x + rng.normal(0, temblor_m) * SX, y + rng.normal(0, temblor_m) * SY
        filas = [[x, y, conf]] + [[x0 + dx, y0 + dy, c] for dx, dy, c in extras]
        return np.array(filas)
    return detectar, estado


def toques_esperados(tramos, periodo, trk):
    """Vueltas del balón de verdad dentro de las rachas visibles de cada tramo, lejos de sus bordes."""
    total = 0
    vx, _, _ = balon_de_verdad()
    for a, b in tramos:
        t = np.arange(a, b)
        visible = np.isfinite(trk.bx[t + ADELANTO])
        for i0, i1, v in toques.mc.rachas(visible.astype(int), toques.MINIMO):
            if v != 1:
                continue
            for k in range(i0, i1):
                f = a + k
                if 0 < f < N - 1 and (vx[f] == A_X or vx[f] == B_X) and (k - i0) >= 3 and k < i1 - 4:
                    total += 1
    return total


def claves(obj, prefijo=""):
    """Las rutas de todas las claves de un diccionario anidado: si la salida creciera con los frames, cambiarían."""
    if isinstance(obj, dict):
        return sorted(sum([[prefijo + "/" + k] + claves(v, prefijo + "/" + k) for k, v in obj.items()], []))
    return []


def cond5_falsa(pasa, racha_real=None):
    """Una emulación inventada con la rejilla de la bitácora y un temblor de la DFL ≈ 3·σ."""
    rej = {"p": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0], "sigma": [0.03, 0.06, 0.12, 0.25], "L": [1, 12, 50]}
    celdas = {}
    for p in rej["p"]:
        for s in rej["sigma"]:
            for l in rej["L"]:
                celdas[(p, s, l)] = {"p": p, "sigma": s, "L": l,
                                     "racha_de_fallos_media_real": (racha_real or {}).get(l, 1.0 / p if l == 1 else l),
                                     "oraculo": {"veredicto": {"pasa": pasa(p, s, l)}}}
    return {"rejilla": rej, "celdas": celdas, "temblor_dfl": {0.03: 0.095, 0.06: 0.18, 0.12: 0.35, 0.25: 0.73}}


def prueba_muestra():
    print("muestra")
    t1 = bs.muestra(BLOQUES, TRAMOS, LARGO_TRAMO, ADELANTO)
    t2 = bs.muestra(BLOQUES, TRAMOS, LARGO_TRAMO, ADELANTO)
    check("determinista", t1 == t2)
    check("{} tramos de {} frames, la mitad en cada bloque (mismo largo)".format(TRAMOS, LARGO_TRAMO),
          len(t1) == TRAMOS and all(b - a == LARGO_TRAMO for a, b in t1)
          and sum(1 for a, _ in t1 if a < BLOQUES[0][1]) == TRAMOS // 2, t1)
    juego = bs.bloques_con_juego()
    check("los bloques del partido empiezan en su saque (constantes del FAQ)",
          juego == [(11185, 90652), (113742, 190198)], juego)
    for nombre, bloques, tramos, largo in (("inventados", BLOQUES, TRAMOS, LARGO_TRAMO),
                                           ("los del partido", juego, 40, 375)):
        tr = bs.muestra(bloques, tramos, largo, ADELANTO)
        dentro = all(any(a0 <= a and b - 1 + ADELANTO < b0 for a0, b0 in bloques) for a, b in tr)
        sin_solape = all(tr[i][1] <= tr[i + 1][0] for i in range(len(tr) - 1))
        check("{}: dentro de los tramos con t+4, en orden y sin solapes".format(nombre),
              dentro and sin_solape and len(tr) == tramos)
    tr = bs.muestra(juego, 40, 375, ADELANTO)
    por_bloque = [sum(1 for a, _ in tr if a0 <= a < b0) for a0, b0 in juego]
    check("los del partido: 20 y 20, ninguno antes del saque de la 2ª parte",
          por_bloque == [20, 20] and not any(110808 <= a < 113742 for a, _ in tr), por_bloque)
    tr = bs.muestra(((0, 1000), (1000, 4000)), 4, 100, ADELANTO)
    check("proporcional al largo: 1 y 3 con bloques de 1.000 y 3.000",
          [sum(1 for a, _ in tr if a < 1000), sum(1 for a, _ in tr if a >= 1000)] == [1, 3], tr)
    try:
        bs.muestra(BLOQUES, 40, 375, ADELANTO)
        check("si no caben, error", False)
    except bs.ErrorSondeo:
        check("si no caben, error", True)


def prueba_constantes_y_lectura():
    print("constantes y lectura de la condición 5")
    check("constantes de la bitácora: 70 %, 10 %, 3 m, 5 m, adelanto 4, desfases de −8 a +12 de uno en uno",
          (bs.UMBRAL_C1, bs.UMBRAL_C2, bs.RADIO_ACIERTO, bs.RADIO_LEJOS, BALL_LEAD) == (70, 10, 3.0, 5.0, 4)
          and bs.DESFASES == tuple(range(-8, 13)))
    check("variante fijada por defecto: 320 px ×2, confianza 0,10", (det.LADO, det.FACTOR, det.CONF) == (320, 2, 0.10))
    check("«cumple» con enteros: 6302 de 9003 (69,9989 %) no llega a 70 aunque se imprima 70,0",
          bs.al_menos(6302, 9003, 70) is False and bs._pct(6302, 9003) == 70.0 and bs.al_menos(7, 10, 70) is True
          and bs.como_mucho(1, 10, 10) is True and bs.como_mucho(11, 100, 10) is False)
    c5 = cond5_falsa(lambda p, s, l: (p, s, l) == (0.6, 0.06, 12))
    r = bs.leer_condicion_5(6302, 9003, 0.18, 12.0, c5)
    check("celda: p 69,99 % -> 0,6; temblor igual al de σ = 0,06 -> 0,06; racha 12,0 -> 12; y pasa",
          r["celda"] == {"p": 0.6, "sigma": 0.06, "L": 12} and r["cumple"] is True, r)
    r = bs.leer_condicion_5(6302, 9003, 0.1801, 12.01, c5)
    check("un poco más de temblor y de racha: σ 0,12 y L 50, y no pasa",
          r["celda"] == {"p": 0.6, "sigma": 0.12, "L": 50} and r["cumple"] is False, r)
    for nombre, args in (("temblor mayor que el de σ = 0,25", (90, 100, 0.8, 5.0)),
                         ("racha mayor que 50", (90, 100, 0.05, 51.0)),
                         ("cobertura menor que 0,5", (49, 100, 0.05, 5.0))):
        r = bs.leer_condicion_5(*(args + (cond5_falsa(lambda p, s, l: True),)))
        check("fuera de la rejilla ({}): no pasa".format(nombre), r["cumple"] is False and r["celda"] is None, r)
    r = bs.leer_condicion_5(90, 100, 0.05, None, c5)
    check("sin fallos: L es la menor de la rejilla", r["celda"]["L"] == 1, r["celda"])
    r = bs.leer_condicion_5(70, 100, 0.05, 1.3, c5)
    check("racha 1,3 con p 0,7: la regla (racha real, 1/p = 1,43) lee L = 1; sin voto, por la etiqueta, L = 12",
          r["celda"]["L"] == 1 and r["sin_voto_L_por_etiqueta"]["celda"]["L"] == 12, r)
    r = bs.leer_condicion_5(70, 100, 0.05, 1.5, c5)
    check("racha 1,5 con p 0,7: ya no cabe en la de L = 1 (1,43) y lee L = 12", r["celda"]["L"] == 12, r)
    r = bs.leer_condicion_5(70, 100, 0.05, 11.0, cond5_falsa(lambda p, s, l: True, racha_real={12: 10.5, 50: 48.0}))
    check("la regla usa la racha real de la emulación, no la etiqueta: con racha real de 10,5 en L = 12, 11 lee L = 50",
          r["celda"]["L"] == 50, r)
    r = bs.leer_condicion_5(70, 100, 0.05, 1.3, None)
    check("sin la emulación: la condición 5 sale sin leer", r["cumple"] is None and r["celda"] is None, r)


def prueba_medir():
    print("medir")
    trk, matrices, validas, periodo = partido()
    tramos = bs.muestra(BLOQUES, TRAMOS, LARGO_TRAMO, ADELANTO)
    detectar, estado = detector_falso()
    lectura = {"frames_leidos": tramos[-1][1], "segundos_leyendo": 1.0}  # como lo deja detector.leer_frames

    def medir(det_, trk_=trk, mat=matrices, desfase_imagen=0, tr=tramos, **kw):
        return bs.medir(fuente(trk_, mat, tr, desfase_imagen), trk_, mat, validas, det_, tr, **kw)

    s = medir(detectar, estado_lectura=lectura)
    clave_base = "frames_con_balon_del_atd_en_t_mas_4_dentro_del_campo"
    esperado_base = sum(int(np.sum(np.isfinite(trk.bx[np.arange(a, b) + ADELANTO]))) for a, b in tramos)
    check("frames con balón del ATD = los de la muestra menos el hueco", s[clave_base] == esperado_base,
          (s[clave_base], esperado_base, s["frames_muestreados"]))
    check("condición 1 = 100 %", s["condicion_1_pct_con_deteccion_a_3m"] == 100.0,
          s["condicion_1_pct_con_deteccion_a_3m"])
    check("condición 2 = 0 %", s["condicion_2_pct_detecciones_a_mas_de_5m"] == 0.0,
          s["condicion_2_pct_detecciones_a_mas_de_5m"])
    check("distancia al ATD en t+4 con la homografía de cada frame: p95 < 0,06 m (medio píxel)",
          s["distancia_a_la_deteccion_mas_cercana_m"]["p95"] < 0.06, s["distancia_a_la_deteccion_mas_cercana_m"])
    ali = s["alineacion_por_desfase"]
    check("alineación: la menor mediana está en +4, también en cada parte",
          ali["desfase_con_menor_mediana"] == 4
          and ali["desfase_con_menor_mediana_por_parte"] == {"parte_1": 4, "parte_2": 4},
          (ali["desfase_con_menor_mediana"], ali["desfase_con_menor_mediana_por_parte"]))
    check("alineación: con +3 y +5 la mediana ya sube (de uno en uno se ve un frame)",
          ali["por_desfase"]["+3"]["mediana_distancia_m"] > 0.3 and ali["por_desfase"]["+5"]["mediana_distancia_m"] > 0.3,
          {d: ali["por_desfase"][d]["mediana_distancia_m"] for d in ("+3", "+4", "+5")})
    check("sin balón del ATD no hay nada que detectar (0 %)",
          s["pct_frames_sin_balon_del_atd_con_alguna_deteccion_en_el_campo"] == 0.0,
          s["pct_frames_sin_balon_del_atd_con_alguna_deteccion_en_el_campo"])
    check("con nativa se detecta en todos los frames muestreados",
          s["frames_detectados"] == s["frames_muestreados"] == estado["llamadas"])
    check("ningún frame con el balón del ATD fuera del campo", s[clave_base.replace("dentro", "fuera")] == 0)

    tq = s["toques_por_tramos"]
    esperados = toques_esperados(tramos, periodo, trk)
    check("toques del detector = las vueltas del balón dentro de los tramos ({})".format(esperados),
          tq["detector"]["toques"] == esperados and esperados > 0, tq["detector"])
    check("toques del ATD en t+4 = los mismos", tq["atd_en_t_mas_4"]["toques"] == esperados, tq["atd_en_t_mas_4"])
    check("suelo de ruido 0 con el balón limpio", tq["detector"]["ruido"] == 0 and tq["atd_en_t_mas_4"]["ruido"] == 0,
          (tq["detector"]["ruido"], tq["atd_en_t_mas_4"]["ruido"]))
    check("el ATD en t (4 frames tarde) ve las vueltas cuando los jugadores ya se han ido: todo ruido",
          tq["atd_en_t"]["toques"] == 0 and tq["atd_en_t"]["ruido"] > 0, tq["atd_en_t"])
    minutos = esperado_base / 25.0 / 60.0
    check("toques por minuto de su balón visible (aquí, los frames con balón del ATD)",
          abs(tq["detector"]["toques_por_minuto_de_su_balon_visible"] - round(esperados / minutos, 2)) < 0.011
          and tq["detector"]["toques_por_minuto_de_frames_con_balon_del_atd"]
          == tq["detector"]["toques_por_minuto_de_su_balon_visible"],
          (tq["detector"], round(esperados / minutos, 2)))
    unidos = toques.contar(np.concatenate([trk.bx[np.arange(a, b) + ADELANTO] for a, b in tramos]),
                           np.concatenate([trk.by[np.arange(a, b) + ADELANTO] for a, b in tramos]),
                           np.concatenate([trk.px[a:b] for a, b in tramos]),
                           np.concatenate([trk.py[a:b] for a, b in tramos]), trk.team, 25)
    check("por tramos no es lo mismo que concatenar (el salto entre tramos fabrica eventos)",
          unidos["eventos"] != tq["atd_en_t_mas_4"]["eventos"], (unidos, tq["atd_en_t_mas_4"]))
    m5 = s["medidas_de_la_condicion_5"]
    ternas = 0
    for a, b in tramos:
        vis = np.isfinite(trk.bx[np.arange(a, b) + ADELANTO])
        ternas += int(np.sum(vis[:-2] & vis[1:-1] & vis[2:]))
    check("ternas del temblor: exactamente las de cada tramo por separado ({}; cruzar tramos añadiría 2 por "
          "frontera)".format(ternas), m5["ternas_del_temblor"] == ternas, m5["ternas_del_temblor"])
    check("sin fallos: ninguna racha; temblor del balón limpio < 0,1 m (solo la cuantización del píxel, 0,07 m)",
          m5["rachas_de_fallos"] == 0 and m5["racha_media_de_fallos"] is None and m5["temblor_del_detector_m"] < 0.1,
          m5)

    v = s["veredictos"]
    check("veredictos: 1 y 2 cumplen, 3 y 4 descriptivas, 5 sin leer; global sin veredicto (falta la 5)",
          v["condicion_1"]["cumple"] is True and v["condicion_2"]["cumple"] is True
          and "cumple" not in v["condicion_3_descriptiva"] and "cumple" not in v["condicion_4_descriptiva"]
          and v["condicion_5"]["cumple"] is None and v["global"].startswith("sin veredicto: falta la condición 5"),
          v["global"])
    s2 = medir(detector_falso()[0], cond5=cond5_falsa(lambda p, s_, l: True))
    check("con la emulación y la celda que pasa: SIGUE (celda p 1, σ 0,03, L 1)",
          s2["veredictos"]["global"] == "SIGUE"
          and s2["veredictos"]["condicion_5"]["celda"] == {"p": 1.0, "sigma": 0.03, "L": 1}, s2["veredictos"])
    s2 = medir(detector_falso()[0], cond5=cond5_falsa(lambda p, s_, l: False))
    check("con la celda que no pasa: NO SIGUE", s2["veredictos"]["global"] == "NO SIGUE", s2["veredictos"]["global"])
    s2 = medir(detector_falso()[0], cond5=cond5_falsa(lambda p, s_, l: True), variante_fijada=False)
    check("otra variante: sin veredicto", s2["veredictos"]["global"].startswith("sin veredicto: no es la variante"),
          s2["veredictos"]["global"])
    s2 = medir(detector_falso()[0], cond5=cond5_falsa(lambda p, s_, l: True), n_total=N,
               estado_lectura={"frames_leidos": 10, "segundos_leyendo": 1.0, "frames_decodificados": N - 33})
    check("el vídeo decodifica otro número de frames: sin veredicto",
          s2["veredictos"]["global"].startswith("sin veredicto: el vídeo"), s2["veredictos"]["global"])

    # Solo agregados.
    texto = json.dumps(s, ensure_ascii=False)
    numeros = {float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", texto)}
    inicios = {float(a) for a, _ in tramos} | {float(b) for _, b in tramos}
    pocos = bs.muestra(BLOQUES, TRAMOS // 2, LARGO_TRAMO, ADELANTO)
    s_pocos = bs.medir(fuente(trk, matrices, pocos), trk, matrices, validas, detector_falso()[0], pocos,
                       estado_lectura={"frames_leidos": pocos[-1][1], "segundos_leyendo": 1.0})
    check("la salida solo lleva agregados: ninguna lista, las mismas claves con la mitad de tramos, ningún inicio "
          "ni fin de tramo", "[" not in texto and claves(s) == claves(s_pocos) and not (numeros & inicios)
          and len(texto) < 9000 and "horas_estimadas_partido_entero" in s["tiempos"],
          (len(claves(s)), len(texto), sorted(numeros & inicios)))

    # Un frame de desfase entre la imagen y su índice se nota, también por parte.
    s = medir(detector_falso()[0], desfase_imagen=1)
    ali = s["alineacion_por_desfase"]
    check("un frame de desfase en la imagen: la mediana a +4 pasa de 0 a ≈ 0,4 m y el mínimo se va a +5 en las dos "
          "partes", ali["por_desfase"]["+4"]["mediana_distancia_m"] > 0.3 and ali["desfase_con_menor_mediana"] == 5
          and ali["desfase_con_menor_mediana_por_parte"] == {"parte_1": 5, "parte_2": 5},
          (ali["por_desfase"]["+4"], ali["desfase_con_menor_mediana_por_parte"]))
    s = medir(detector_falso()[0], desfase_imagen=-ADELANTO)
    check("una imagen sin el retraso del ATD: la menor mediana se va a 0",
          s["alineacion_por_desfase"]["desfase_con_menor_mediana"] == 0, s["alineacion_por_desfase"])

    # Condición 1: a cada lado del radio de 3 m.
    s = medir(detector_falso(desplazado_m=2.5)[0])
    check("detector desplazado 2,5 m: la condición 1 da 100 % y la trayectoria tiene 100 % a menos de 3 m",
          s["condicion_1_pct_con_deteccion_a_3m"] == 100.0
          and s["trayectoria_del_detector"]["pct_con_la_deteccion_elegida_a_mas_de_3m"] == 0.0,
          (s["condicion_1_pct_con_deteccion_a_3m"], s["trayectoria_del_detector"]))
    s = medir(detector_falso(desplazado_m=3.5)[0], cond5=cond5_falsa(lambda p, s_, l: True))
    check("desplazado 3,5 m: la condición 1 da 0 %, no cumple, NO SIGUE; la trayectoria, 100 % a más de 3 m",
          s["condicion_1_pct_con_deteccion_a_3m"] == 0.0 and s["veredictos"]["condicion_1"]["cumple"] is False
          and s["veredictos"]["global"] == "NO SIGUE"
          and s["trayectoria_del_detector"]["pct_con_la_deteccion_elegida_a_mas_de_3m"] == 100.0,
          (s["condicion_1_pct_con_deteccion_a_3m"], s["veredictos"]["global"], s["trayectoria_del_detector"]))

    # Condición 1 con fallos a bloques de 30 frames: 50 %, no cumple; rachas de unos 30 frames.
    s = medir(detector_falso(falla_cada=30)[0], cond5=cond5_falsa(lambda p, s_, l: True))
    m5 = s["medidas_de_la_condicion_5"]
    c1 = s["condicion_1_pct_con_deteccion_a_3m"]
    check("falla a bloques de 30: condición 1 ≈ 50 % y no cumple; NO SIGUE",
          40.0 <= c1 <= 60.0 and s["veredictos"]["condicion_1"]["cumple"] is False
          and s["veredictos"]["global"] == "NO SIGUE", (c1, s["veredictos"]["global"]))
    check("falla a bloques de 30: rachas de fallos de 30 lejos de los bordes, algo menos con los bordes",
          m5["racha_media_sin_las_que_tocan_un_borde_de_tramo"] is not None
          and 25.0 <= m5["racha_media_sin_las_que_tocan_un_borde_de_tramo"] <= 30.0
          and 15.0 <= m5["racha_media_de_fallos"] <= 30.0
          and m5["frames_de_fallo"] == m5["frames_con_balon_del_atd"] - m5["aciertos"], m5)
    check("falla a bloques de 30: la celda lee L = 50", s["veredictos"]["condicion_5"]["celda"]["L"] == 50,
          s["veredictos"]["condicion_5"])

    # Condición 2: a cada lado del radio de 5 m, y con detecciones fuera del campo.
    s = medir(detector_falso(extras=[(5.5 * SX, 0.0, 0.3)])[0])
    check("una detección de más a 5,5 m: la condición 2 da 50 % y no cumple",
          s["condicion_2_pct_detecciones_a_mas_de_5m"] == 50.0 and s["veredictos"]["condicion_2"]["cumple"] is False,
          s["veredictos"]["condicion_2"])
    s = medir(detector_falso(extras=[(4.5 * SX, 0.0, 0.3)])[0])
    check("a 4,5 m: la condición 2 da 0 % y cumple",
          s["condicion_2_pct_detecciones_a_mas_de_5m"] == 0.0 and s["veredictos"]["condicion_2"]["cumple"] is True,
          s["veredictos"]["condicion_2"])
    fuera_y = -(Y_BALON + 6.0) * SY  # del balón a 6 m más allá de la banda de y = 0
    s = medir(detector_falso(extras=[(0.0, fuera_y, 0.3)])[0])
    c2 = s["veredictos"]["condicion_2"]
    check("una detección de más 6 m fuera del campo: la condición 2 la cuenta (50 %, no cumple); la de solo "
          "dentro del campo, sin voto, da 0 %", c2["valor_pct"] == 50.0 and c2["cumple"] is False
          and c2["sin_voto_solo_dentro_del_campo_pct"] == 0.0, c2)

    # La trayectoria se queda con la de más confianza a 5 m o menos.
    s = medir(detector_falso(extras=[(30.0, 0.0, 0.3)])[0])
    check("segunda detección a 2,1 m con menos confianza: la trayectoria sigue al balón (confianza 0,8, toques)",
          s["confianza"]["trayectoria_del_detector"]["p50"] == 0.8
          and s["toques_por_tramos"]["detector"]["toques"] == esperados,
          (s["confianza"]["trayectoria_del_detector"], s["toques_por_tramos"]["detector"]["toques"]))
    s = medir(detector_falso(extras=[(30.0, 0.0, 0.9)])[0])
    check("segunda detección a 2,1 m con más confianza: la trayectoria la sigue (confianza 0,9, 0 toques)",
          s["confianza"]["trayectoria_del_detector"]["p50"] == 0.9
          and s["toques_por_tramos"]["detector"]["toques"] == 0,
          (s["confianza"]["trayectoria_del_detector"], s["toques_por_tramos"]["detector"]["toques"]))

    # Temblor: con ruido gaussiano isótropo σ, la mediana es ≈ 2,88·σ; y la función es la de instrumento.temblor.
    sigma = 0.2
    s = medir(detector_falso(temblor_m=sigma)[0], cond5=cond5_falsa(lambda p, s_, l: True))
    m5 = s["medidas_de_la_condicion_5"]
    tq = s["toques_por_tramos"]["detector"]
    check("temblor de σ = 0,2 m: el temblor medido es ≈ 2,88·σ (±10 %)",
          abs(m5["temblor_del_detector_m"] / (2.884 * sigma) - 1.0) < 0.10, m5["temblor_del_detector_m"])
    check("y la celda lee σ = 0,25: en la DFL inventada, 0,35 (σ = 0,12) < 0,58 ≤ 0,73 (σ = 0,25)",
          s["veredictos"]["condicion_5"]["celda"]["sigma"] == 0.25, s["veredictos"]["condicion_5"]["celda"])
    check("con temblor el suelo de ruido sube", tq["ruido"] > 0, tq)
    rng = np.random.default_rng(3)
    x, y = rng.normal(0, 1, 500), rng.normal(0, 1, 500)
    activo = rng.random(500) > 0.2
    x[rng.random(500) < 0.1] = np.nan
    check("valores_temblor: su mediana es la de instrumento.temblor",
          float(np.median(bs.valores_temblor(x, y, activo))) == instrumento.temblor(x, y, activo))

    # El ATD fuera del campo: fuera de la base, y se cuenta.
    trk_f, mat_f, _, _ = partido(atd_fuera_por_tramo=30, tramos=tramos)
    s = medir(detector_falso()[0], trk_=trk_f, mat=mat_f)
    check("balón del ATD 1 m fuera del campo en 30 frames por tramo: salen de la base y se cuentan",
          s[clave_base] == esperado_base - 30 * TRAMOS
          and s[clave_base.replace("dentro", "fuera")] == 30 * TRAMOS,
          (s[clave_base], s[clave_base.replace("dentro", "fuera")]))

    # roi: solo donde el ATD ve el balón, con el centro en su proyección (con la homografía de cada frame).
    detectar, estado = detector_falso(comprobar_centro=1.0)
    s = medir(detectar, roi=True)
    sin = s["frames_muestreados"] - s[clave_base]
    check("roi: se detecta solo con balón del ATD, con el centro a 1 px del balón; el resto se cuenta",
          estado["llamadas"] == s[clave_base] == estado["centros"]
          and s["frames_sin_detectar_por_roi_sin_balon_del_atd"] == sin and sin > 0,
          (estado, s["frames_sin_detectar_por_roi_sin_balon_del_atd"], sin))

    # El progreso no depende de lo que hay en cada frame.
    frames = np.concatenate([np.arange(a, b) for a, b in tramos])
    cada = max(1, len(frames) // 20)
    control = [int(frames[k]) for k in range(len(frames)) if (k + 1) % cada == 0]
    trk_t, mat_t, _, _ = partido(tapar=control[2:5])
    con, sin_ = [], []
    medir(detector_falso()[0], roi=True, progreso=con.append)
    medir(detector_falso()[0], trk_=trk_t, mat=mat_t, roi=True, progreso=sin_.append)
    check("roi: los puntos de progreso son los mismos con y sin balón del ATD en los frames de control (20)",
          con == sin_ and len(con) == 20, (len(con), len(sin_)))

    # La fuente de frames tiene que dar exactamente la muestra.
    for nombre, f in (("se acaba antes", lambda: (x for i, x in enumerate(fuente(trk, matrices, tramos)) if i < 10)),
                      ("da otro frame", lambda: ((t + 1, img) for t, img in fuente(trk, matrices, tramos))),
                      ("da frames de más", lambda: itertools.chain(fuente(trk, matrices, tramos), [(0, None)]))):
        try:
            bs.medir(f(), trk, matrices, validas, detector_falso()[0], tramos)
            check("fuente que {}: error".format(nombre), False)
        except bs.ErrorSondeo:
            check("fuente que {}: error".format(nombre), True)


def prueba_main():
    print("main: lo que se comprueba antes de buscar los datos")
    for nombre, argv, texto in (("--tramos 1 --largo 1 sin --ensayo", ["--tramos", "1", "--largo", "1"], "--ensayo"),
                                ("--tramos 9 sin --ensayo", ["--tramos", "9"], "--ensayo"),
                                ("x2 sin --ensayo ni --forzar", ["--variante", "x2"], "x2"),
                                ("--factor con nativa", ["--variante", "nativa", "--factor", "2"], "--factor")):
        try:
            bs.main(argv)
            check("{}: error".format(nombre), False)
        except bs.ErrorSondeo as e:
            check("{}: error antes de buscar los datos".format(nombre), texto in str(e), str(e))
    import importlib.util
    faltan = [m for m in ("torch", "ultralytics", "cv2", "pandas") if importlib.util.find_spec(m) is None]
    if not faltan:
        print("  [SALTA] el aviso de paquetes que faltan: en este entorno están todos")
        return
    try:
        bs.main(["--ensayo", "--tramos", "1", "--largo", "50"])
        check("ensayo corto sin {}: error que lo dice".format(", ".join(faltan)), False)
    except bs.ErrorSondeo as e:
        check("ensayo corto sin {}: error que lo dice, antes de buscar los datos".format(", ".join(faltan)),
              str(e).startswith("faltan ") and all(m in str(e) for m in faltan), str(e))


def emulacion_json(partidos=7, d="oraculo", quitar=None, pasa=True):
    """Una emulación con el esquema de `emular_dfl.a_json` (las claves que lee el sondeo) y la rejilla entera."""
    rej = {"p": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0], "sigma": [0.03, 0.06, 0.12, 0.25], "L": [1, 12, 50]}
    celdas = {}
    for p in rej["p"]:
        for s_ in rej["sigma"]:
            for l in rej["L"]:
                if (p, s_, l) == quitar:
                    continue
                celdas["p={:g} σ={:g} L={:d}".format(p, s_, l)] = {
                    "p": p, "sigma": s_, "L": l, "comprobacion": None, "cuentas": {},
                    "cobertura_real": p, "racha_de_fallos_media_real": 1.0 / p if l == 1 else float(l),
                    "oraculo": {"condiciones": {}, "veredicto": {"control": pasa, "flag": True, "pasa": pasa}},
                    "propio": {"condiciones": {}, "veredicto": {"control": False, "flag": True, "pasa": False}}}
    return {"fecha": "2026-11-16", "partidos": ["P{}".format(i) for i in range(partidos)], "rejilla": rej,
            "regla": {"d": d, "control_minimo": 0.01, "gana_en_minimo": 6, "flag_minimo": -0.005}, "celdas": celdas}


def prueba_cargar_condicion_5(carpeta):
    print("cargar_condicion_5")
    temblor = bs.TEMBLOR_DFL
    if not os.path.isfile(temblor):
        print("  [SALTA] no está salidas/2026-11-16_calibracion_temblor_dfl.json")
        return None
    rutas = {}
    for nombre, kw in (("buena", {}), ("un_partido", {"partidos": 1}), ("propio", {"d": "propio"}),
                       ("sin_celda", {"quitar": (0.7, 0.06, 12)})):
        rutas[nombre] = os.path.join(carpeta, nombre + ".json")
        with open(rutas[nombre], "w", encoding="utf-8") as f:
            json.dump(emulacion_json(**kw), f, ensure_ascii=False)
    c5 = bs.cargar_condicion_5(rutas["buena"], temblor)
    check("carga la emulación (esquema de emular_dfl) con la calibración del temblor de verdad: 72 celdas y el "
          "temblor de la DFL de cada σ de la rejilla, creciente",
          len(c5["celdas"]) == 72 and sorted(c5["temblor_dfl"]) == [0.03, 0.06, 0.12, 0.25]
          and all(c5["temblor_dfl"][a] < c5["temblor_dfl"][b] for a, b in ((0.03, 0.06), (0.06, 0.12), (0.12, 0.25))),
          c5["temblor_dfl"])
    for nombre, texto in (("un_partido", "7 partidos"), ("propio", "D de las etiquetas"), ("sin_celda", "celda")):
        try:
            bs.cargar_condicion_5(rutas[nombre], temblor)
            check("emulación «{}»: error".format(nombre), False)
        except bs.ErrorSondeo as e:
            check("emulación «{}»: error ({})".format(nombre, texto), texto in str(e), str(e))
    if os.path.isfile(bs.EMULACION):
        c5 = bs.cargar_condicion_5(bs.EMULACION, temblor)
        # Sin contar celdas: el JSON puede traer celdas de referencia además de las de la rejilla (p. ej. p=0 y p=1).
        rej = c5["rejilla"]
        check("carga la emulación de verdad (salidas/2026-11-16_emulacion_dfl.json): rejilla de 6×4×3 y sus celdas",
              (len(rej["p"]), len(rej["sigma"]), len(rej["L"])) == (6, 4, 3)
              and all((p, s, l) in c5["celdas"] for p in rej["p"] for s in rej["sigma"] for l in rej["L"]))
    else:
        print("  [SALTA] la emulación de verdad: todavía no está en salidas/")
    return rutas["buena"]


@contextlib.contextmanager
def parches(objetos):
    """Sustituye atributos [(objeto, nombre, valor)] y los devuelve a su sitio al salir."""
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


def main_con_todo_falso(argv, trk, matrices, validas):
    """`bs.main` de punta a punta sobre el partido inventado, con el modelo, el vídeo, el ATD y la homografía
    falsos: lo que hay después del bucle (la cabecera, el ensayo, el JSON) también se ejecuta en la prueba."""
    detectar_falso = detector_falso()[0]
    import games
    import starter

    def detectar(modelo, imagen, conf=None, factor=None, centro=None, lado=None, max_det=None):
        return np.zeros((0, 5)) if isinstance(imagen, np.ndarray) else detectar_falso(imagen, centro)

    def leer_frames(ruta, frames, n_esperado=None, tamano=None, estado=None, hasta_el_final=False):
        estado = {} if estado is None else estado
        estado["backend"] = "FALSO"
        frames = [int(f) for f in frames]
        tramos = []
        for f in frames:
            if tramos and tramos[-1][1] == f:
                tramos[-1][1] = f + 1
            else:
                tramos.append([f, f + 1])
        for i, (t, img) in enumerate(fuente(trk, matrices, [tuple(x) for x in tramos])):
            estado["frames_leidos"], estado["segundos_leyendo"] = (i + 1) * 3, (i + 1) * 0.003
            yield t, img
        if hasta_el_final:
            estado["frames_decodificados"] = n_esperado

    load_homography = types.ModuleType("starter.load_homography")
    load_homography.load = lambda game, data_dir=None: (matrices, None, validas)
    torch_falso = types.ModuleType("torch")
    torch_falso.get_num_threads = lambda: 2
    modulos = dict(sys.modules)
    sys.modules["torch"] = torch_falso
    sys.modules["starter.load_homography"] = load_homography
    salida, errores = io.StringIO(), io.StringIO()
    try:
        with parches([(importlib.util, "find_spec", lambda nombre, *a: object()),
                      (starter, "load_homography", load_homography),
                      (games, "require", lambda *a, **k: None), (games, "video_path", lambda *a, **k: "falso.mp4"),
                      (games, "asset_paths", lambda *a, **k: {}), (bs.tracking, "from_atd", lambda *a, **k: trk),
                      (bs, "bloques_con_juego", lambda game=None: list(BLOQUES)), (bs, "MINIMO_FRAMES", 1000),
                      (det, "cargar", lambda *a, **k: "modelo"), (det, "detectar", detectar),
                      (det, "leer_frames", leer_frames), (det, "versiones", lambda: {"python": "falso"}),
                      (det, "sha256_de", lambda ruta: "0" * 64)]), \
                contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
            codigo = bs.main(argv)
    finally:
        for nombre in ("torch", "starter.load_homography"):
            if nombre in modulos:
                sys.modules[nombre] = modulos[nombre]
            else:
                sys.modules.pop(nombre, None)
    return codigo, salida.getvalue(), errores.getvalue()


def prueba_main_entero(ruta_emulacion):
    print("main de punta a punta, con todo falso (sin datos ni modelo)")
    trk, matrices, validas, _ = partido()
    sin_atd, _, _, _ = partido(tapar=[t for t in range(N - ADELANTO)])
    salidas = []
    for nombre, t in (("con balón del ATD", trk), ("sin balón del ATD", sin_atd)):
        codigo, texto, errores = main_con_todo_falso(["--ensayo", "--tramos", "1", "--largo", "50"], t, matrices,
                                                     validas)
        salidas.append(json.loads(texto) if codigo == 0 else None)
        check("ensayo {}: sale bien".format(nombre), codigo == 0 and salidas[-1]["resultado"] == "ensayo correcto",
              (codigo, texto[-300:], errores[-300:]))
    if None in salidas:
        return
    esperado = {"medida", "versiones", "backend_video", "hilos_torch", "parametros", "ms_por_frame_decodificado",
                "ms_por_frame_detectado_en_imagen_negra", "horas_estimadas_partido_entero_techo", "resultado"}
    tiempos = {"ms_por_frame_detectado_en_imagen_negra", "horas_estimadas_partido_entero_techo"}
    check("ensayo: solo versiones, backend, hilos, parámetros, tiempos y «ensayo correcto»",
          set(salidas[0]) == esperado, sorted(set(salidas[0]) ^ esperado))
    check("ensayo: lo mismo con y sin balón del ATD en su ventana (salvo los tiempos cronometrados)",
          {k: v for k, v in salidas[0].items() if k not in tiempos}
          == {k: v for k, v in salidas[1].items() if k not in tiempos})
    argv = ["--tramos", "10", "--largo", "100"]
    if ruta_emulacion:
        argv += ["--emulacion", ruta_emulacion]
    codigo, texto, errores = main_con_todo_falso(argv, trk, matrices, validas)
    try:
        s = json.loads(texto)
    except ValueError:
        check("la medida: sale un JSON", False, (codigo, texto[-300:], errores[-300:]))
        return
    v = s["veredictos"]
    esperado_global = "SIGUE" if ruta_emulacion else "sin veredicto: falta la condición 5"
    check("la medida: sale bien, con la variante fijada, los frames decodificados y el veredicto «{}»".format(
        esperado_global), codigo == 0 and s["parametros"]["variante_fijada"] is True
          and s["frames_decodificados"] == 199319 and v["global"].startswith(esperado_global)
          and (not ruta_emulacion or v["condicion_5"]["celda"] == {"p": 1.0, "sigma": 0.03, "L": 1}),
          (codigo, v["global"], v["condicion_5"]))
    check("la medida: por stderr, la estimación previa y solo porcentajes de progreso",
          "estimado:" in errores and not re.search(r"\d+\.\d+ %.*\d+ s", errores), errores[-200:])


def prueba_video():
    print("lector secuencial de vídeo")
    if cv2 is None:
        print("  [SALTA] no hay cv2 en este entorno")
        return
    n, ancho, alto, bits = 40, 64, 48, 6

    def pintar(i):
        img = np.zeros((alto, ancho, 3), dtype=np.uint8)
        for b in range(bits):
            if (i >> b) & 1:
                img[8:24, b * 10:b * 10 + 8] = 255
        return img

    def leer(img):
        return sum(1 << b for b in range(bits) if img[16, b * 10 + 4].mean() > 127)

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, "mini.mp4")
        w = cv2.VideoWriter(ruta, cv2.VideoWriter_fourcc(*"mp4v"), 25, (ancho, alto))
        for i in range(n):
            w.write(pintar(i))
        w.release()
        pedidos = [0, 3, 4, 17, 38, 39]
        estado = {}
        salida = [(f, leer(img)) for f, img in det.leer_frames(ruta, pedidos, n_esperado=n, tamano=(ancho, alto),
                                                               estado=estado)]
        check("da exactamente los frames pedidos (el índice pintado en la imagen)",
              salida == [(f, f) for f in pedidos], salida)
        check("cuenta los frames leídos y para al acabar la muestra", estado["frames_leidos"] == 40
              and "frames_decodificados" not in estado, estado)
        estado = {}
        list(det.leer_frames(ruta, [3, 5], n_esperado=n, tamano=(ancho, alto), estado=estado, hasta_el_final=True))
        check("hasta_el_final: sigue hasta el final y cuenta los frames decodificados (40)",
              estado["frames_decodificados"] == 40 and estado["frames_leidos"] == 6, estado)
        try:
            list(det.leer_frames(ruta, [5, 45], n_esperado=None, tamano=(ancho, alto)))
            check("si el vídeo se acaba antes, error", False)
        except det.ErrorDetector:
            check("si el vídeo se acaba antes, error", True)
        try:
            list(det.leer_frames(ruta, [1], tamano=(1920, 1080)))
            check("otra resolución: error antes de leer", False)
        except det.ErrorDetector:
            check("otra resolución: error antes de leer", True)
        estado = {}
        lista = list(det.leer_frames(ruta, [1], tamano=(ancho, alto), n_esperado=199319, estado=estado,
                                     hasta_el_final=True))
        check("otro número de frames declarados: no para; apunta los declarados y los decodificados",
              len(lista) == 1 and estado["frames_declarados"] == 40 and estado["frames_decodificados"] == 40, estado)


def main():
    print("Prueba de validation/partido/balon_video_sondeo.py")
    prueba_muestra()
    prueba_constantes_y_lectura()
    prueba_medir()
    prueba_main()
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = prueba_cargar_condicion_5(carpeta)
        prueba_main_entero(ruta)
    prueba_video()
    print("\nTODO BIEN" if not FALLOS else "\nFALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
    return 0 if not FALLOS else 1


if __name__ == "__main__":
    sys.exit(main())
