"""Perfil del balón y de los jugadores de un `Tracking`, igual para el ATD del partido y para la DFL.

Es la medida de `validation/perfil_atd/BITACORA.md` (agregados de la sección 4, fijados antes de medir).
Funciones puras de numpy: reciben un `possession.tracking.Tracking` y no abren ficheros. Quien las llama
decide qué tracking les da:

- `validation/partido/perfil_atd.py`: el ATD del partido (solo lo ejecuta una persona);
- `validation/perfil_atd/perfil_dfl.py`: los partidos abiertos de la DFL, degradados como en el harness.

Solo se miran los frames de `trk.blocks` (en el partido, los evaluados). Hay dos capas:

- `medidas(trk)`: sumas, histogramas y muestras de un tracking. Es interna: lleva arrays y no se imprime;
- `resumir(parciales, minimo_celda)`: los agregados de uno o varios trackings juntos. Con `minimo_celda=5`,
  una celda con menos de 5 casos sale como "< 5", y lo que se calcula solo con ella, también. Los totales
  del partido siguen saliendo, así que a veces se puede deducir de ellos: es un recuento del partido
  entero, sin nada ligado a un frame ni a un instante (bitácora §7.6).

`perfil(trk)` es `resumir(medidas(trk))`; `para_imprimir` redondea la salida para pegarla, y `primarias`
saca las medidas que deciden (sección 5 de la bitácora).

Definiciones:

- **hueco:** racha de frames evaluados seguidos sin balón; **racha:** con balón. Ninguna cruza de un tramo
  evaluado a otro, y el balón se analiza del primer al último frame con balón de cada tramo: los huecos de
  los bordes no cuentan, porque están cortados y porque contarlos diría si el ATD ve el balón en el primer
  o en el último frame de cada parte (regla nº 1). Por lo mismo, los frames de los huecos de más de 15 s
  salen sumados con los de los bordes;
- **balón parado:** tramo en que el balón no sale de 2 m alrededor de su primer punto durante 3 s o más,
  con huecos de hasta 1 s dentro. Es `still_runs` de `validation/partido/diagnostico_coordenadas.py`;
- **dos denominadores:** `todo` (todo el balón visible) y `sin_parado` (sin los frames de balón parado ni
  los huecos que caen dentro de ellos). El ATD ve el balón colocado antes de un reinicio; el harness lo
  tapa;
- **toques, controles Ret-12 y temblor:** los del experimento 2 (`validation/experimento2/instrumento.py`),
  con sus umbrales.
"""

import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento2"))
import instrumento as ins  # noqa: E402
import medidas_cambios as mc  # noqa: E402

PRM = {
    # 1 y 2. Huecos y rachas: 5 intervalos de duración (≤ 0,5 s, 0,5–2 s, 2–5 s, 5–15 s, > 15 s).
    "cortes_s": (0.5, 2.0, 5.0, 15.0),
    # Cortes de las tres severidades (regla R1): tienen que ser cortes de `cortes_s`.
    "severidades": (("baja", 2.0), ("media", 5.0), ("alta", 15.0)),
    "cortes_salto_m": (3.0, 15.0),  # < 3 m, 3–15 m, ≥ 15 m
    # 3. Dónde se pierde.
    "radio_disputa": ins.PRM["radio_disputa"],  # 3 m: un jugador de cada equipo a esta distancia o menos
    "radio_densidad": 5.0,
    "cortes_densidad": (2, 4),  # 0–1, 2–3, 4 o más jugadores a 5 m
    "margen_linea": 5.0,
    "hueco_corto_s": 5.0,
    "semilla_placebo": 20261114,
    # Balón parado: el diagnóstico del 12/11, con radio 2 m.
    "parado_radio": 2.0,
    "parado_min_s": 3.0,
    "parado_hueco_max": 25,  # frames: MAX_GAP_FRAMES de validation/partido/comun.py
    # 4. Suavizado: el instrumento del experimento 2, sin cambiar nada. El primer umbral de toque es el
    # suyo (4a); los otros dos son los del 4b.
    "umbrales_toque": (ins.PRM["umbral_toque"], 2.0, 1.0),
    "radio_toque": ins.PRM["radio_toque"],
    "min_tramo": ins.PRM["min_tramo"],
    "radio_control": ins.PRM["radio"],
    "frames_control": ins.PRM["frames_control"],
    "retardos": (5, 12, 25),
    "ternas_m": (0.001, 0.005),
    # 5. Proximidad.
    "distancias_m": (1.0, 1.5, 3.0),
    "lejos_m": 5.0,
    "ventaja_rival_m": 1.0,
    # 6. Detecciones falsas.
    "salto_imposible_ms": 40.0,
    "racha_corta_max": 2,
    "cortes_identicas_s": (1.0, 5.0, 30.0),
    # 7. Jugadores.
    "vel_max_jugador": 12.0,  # m/s: MAX_PLAYER_SPEED_MS de validation/partido/comun.py
    "max_localizados": 63,
    # 8. SET PIECES.
    "antes_set_piece_s": 10.0,
    # Frames vacíos entre dos tramos evaluados al juntarlos. Más que la mayor ventana de las medidas (25
    # frames de retardo y de hueco dentro del balón parado), para que nada cruce de un tramo a otro.
    "separacion": 100,
}

INTERVALOS = ("≤ 0,5 s", "0,5–2 s", "2–5 s", "5–15 s", "> 15 s")
DISTANCIAS = ("< 3 m", "3–15 m", "≥ 15 m")
DENSIDADES = ("0–1 jugadores a 5 m", "2–3 jugadores a 5 m", "4 o más jugadores a 5 m")
ZONAS = ("a 5 m o menos de una línea, o fuera del campo", "tercio central", "tercios de fondo")
IDENTICAS = ("< 1 s", "1–5 s", "5–30 s", "30 s o más")
VARIANTES = ("todo", "sin_parado")


# -- utilidades ----------------------------------------------------------------------------------------

def _rachas(mascara):
    """(inicios, fines) de las rachas de True de una máscara; el fin no se incluye."""
    borde = np.diff(np.concatenate(([0], np.asarray(mascara, dtype=np.int8), [0])))
    return np.flatnonzero(borde == 1), np.flatnonzero(borde == -1)


def _juntar_tramos(blocks, n, separacion):
    """Índice de frame de vídeo de cada posición al juntar los tramos (−1 en la separación), y los tramos
    en esas posiciones, como (inicio, fin) con el fin sin incluir."""
    trozos, tramos, inicio = [], [], 0
    for a, b in blocks:
        a, b = max(0, int(a)), min(n, int(b))
        if b <= a:
            continue
        if trozos:
            trozos.append(np.full(separacion, -1, dtype=np.int64))
            inicio += separacion
        trozos.append(np.arange(a, b, dtype=np.int64))
        tramos.append((inicio, inicio + b - a))
        inicio += b - a
    if not trozos:
        raise ValueError("el tracking no tiene ningún tramo evaluado")
    return np.concatenate(trozos), tramos


def _tomar(valores, indice):
    """valores[indice], con NaN en la separación (índice −1). Siempre es una copia."""
    salida = valores[np.maximum(indice, 0)]
    salida[indice < 0] = np.nan
    return salida


def balon_parado(x, y, visible, tramos, radio, minimo, hueco_max):
    """(máscara, cuántos) de los tramos de balón parado de `minimo` frames o más.

    Es `still_runs` de validation/partido/diagnostico_coordenadas.py, tramo a tramo: un tramo sigue mientras
    el balón está a `radio` m o menos de su primer punto; un hueco sin balón de hasta `hueco_max` frames no
    lo corta y uno más largo, sí. La máscara va del primer al último frame con balón del tramo, con sus
    huecos dentro.
    """
    mascara = np.zeros(len(x), dtype=bool)
    xs, ys, vs = x.tolist(), y.tolist(), visible.tolist()
    cuantos = 0

    def cerrar(inicio, fin):
        nonlocal cuantos
        if fin - inicio + 1 >= minimo:
            mascara[inicio:fin + 1] = True
            cuantos += 1

    for a, b in tramos:
        ancla, inicio, fin, hueco = None, 0, 0, 0
        for f in range(a, b):
            if not vs[f]:
                hueco += 1
                if ancla is not None and hueco > hueco_max:
                    cerrar(inicio, fin)
                    ancla = None
                continue
            hueco = 0
            if ancla is not None and math.hypot(xs[f] - ancla[0], ys[f] - ancla[1]) <= radio:
                fin = f
                continue
            if ancla is not None:
                cerrar(inicio, fin)
            ancla, inicio, fin = (xs[f], ys[f]), f, f
        if ancla is not None:
            cerrar(inicio, fin)
    return mascara, cuantos


def segunda_diferencia(x, y, valido):
    """|p[t+1] − 2·p[t] + p[t−1]| (m) en las ternas de frames seguidos con los tres válidos."""
    terna = valido[:-2] & valido[1:-1] & valido[2:]
    return np.hypot(x[2:] - 2 * x[1:-1] + x[:-2], y[2:] - 2 * y[1:-1] + y[:-2])[terna]


# -- medidas de un tracking (capa interna) -------------------------------------------------------------

def medidas(trk, set_pieces=None, jugadores=True, prm=PRM):
    """Sumas, histogramas y muestras de un tracking. Es la capa interna: lleva arrays y nunca se imprime.

    `set_pieces`: ventanas `SET PIECES` como (inicio, fin) en frames de vídeo, con el fin sin incluir. Solo
    en el partido: la DFL no tiene Smart Tagging. `jugadores=False` se salta el agregado 7, que no depende
    del balón.
    """
    if int(round(trk.fps)) != mc.FPS:
        raise ValueError("el instrumento del experimento 2 está fijado a {} fps".format(mc.FPS))
    fps = float(trk.fps)
    n_video = len(trk.bx)
    indice, tramos = _juntar_tramos(trk.blocks, n_video, prm["separacion"])
    evaluado = indice >= 0
    bx = _tomar(np.asarray(trk.bx, dtype=float), indice)
    by = _tomar(np.asarray(trk.by, dtype=float), indice)
    px = _tomar(np.asarray(trk.px, dtype=np.float32), indice)
    py = _tomar(np.asarray(trk.py, dtype=np.float32), indice)
    team = np.asarray(trk.team).astype(int)
    if team.shape != (px.shape[1],):
        raise ValueError("el tracking tiene {} slots y {} equipos".format(px.shape[1], team.size))
    largo, ancho = (float(v) for v in trk.pitch)
    visible = np.isfinite(bx) & np.isfinite(by)
    # El balón se analiza del primer al último frame con balón de cada tramo. Los huecos de los bordes
    # están cortados y no se sabe cuánto duran; además, contarlos diría si el ATD ve el balón en el primer
    # o en el último frame evaluado de cada parte, que son frames públicos (regla nº 1).
    tramos_balon = []
    for a, b in tramos:
        vistos = np.flatnonzero(visible[a:b])
        if vistos.size:
            tramos_balon.append((a + int(vistos[0]), a + int(vistos[-1]) + 1))
    en_tramo = np.zeros(len(indice), dtype=bool)
    for a, b in tramos_balon:
        en_tramo[a:b] = True
    parado, n_parado = balon_parado(bx, by, visible, tramos_balon, prm["parado_radio"],
                                    int(round(prm["parado_min_s"] * fps)), prm["parado_hueco_max"])

    m = {"fps": fps,
         "frames_evaluados": int(evaluado.sum()),
         "frames_con_balon": int(visible.sum()),
         "frames_con_balon_sp": int((visible & ~parado).sum()),
         "parado_tramos": int(n_parado),
         "parado_frames": int(parado.sum())}

    # 1. Huecos y rachas, en los 5 intervalos de duración. Todos los huecos tienen balón a los dos lados.
    cortes = np.asarray(prm["cortes_s"], dtype=float) * fps
    h_ini, h_fin = _rachas(en_tramo & ~visible)
    largo_h = h_fin - h_ini
    clase_h = np.searchsorted(cortes, largo_h, side="left")
    fuera_de_parado = ~parado[h_ini]  # un hueco o cae entero dentro de un tramo de balón parado o fuera
    m["huecos_n"] = np.bincount(clase_h, minlength=5)
    m["huecos_frames"] = np.bincount(clase_h, weights=largo_h, minlength=5).astype(np.int64)
    m["huecos_n_sp"] = np.bincount(clase_h[fuera_de_parado], minlength=5)
    m["huecos_frames_sp"] = np.bincount(clase_h[fuera_de_parado], weights=largo_h[fuera_de_parado],
                                        minlength=5).astype(np.int64)
    r_ini, r_fin = _rachas(en_tramo & visible)
    largo_r = r_fin - r_ini
    clase_r = np.searchsorted(cortes, largo_r, side="left")
    m["rachas_n"] = np.bincount(clase_r, minlength=5)
    m["rachas_frames"] = np.bincount(clase_r, weights=largo_r, minlength=5).astype(np.int64)

    # 2. Salto del balón a través de cada hueco, entre el último frame con balón y el primero después.
    salto = np.hypot(bx[h_fin] - bx[h_ini - 1], by[h_fin] - by[h_ini - 1])
    tabla = np.zeros((5, 3), dtype=np.int64)
    np.add.at(tabla, (clase_h, np.searchsorted(np.asarray(prm["cortes_salto_m"]), salto, side="right")), 1)
    m["salto"] = tabla

    # 3a, 4 y 5, con los dos denominadores.
    equipos = {"local": {"x": px[:, team == 0], "y": py[:, team == 0]},
               "visitante": {"x": px[:, team == 1], "y": py[:, team == 1]}}
    m["todo"], disputa = _medir_balon(bx, by, equipos, evaluado, fps, prm)
    xs, ys = bx.copy(), by.copy()
    xs[parado], ys[parado] = np.nan, np.nan
    m["sin_parado"], _ = _medir_balon(xs, ys, equipos, evaluado & ~parado, fps, prm)
    del equipos, xs, ys

    # 3b, 6, 7 y 8.
    m["perdidas"] = _perdidas(bx, by, px, py, visible, disputa, h_ini, largo_h, (largo, ancho), fps, prm)
    m["detecciones"] = _detecciones(bx, by, visible, largo_r, fps, prm)
    if jugadores:
        m["jugadores"] = _jugadores(px, py, team, evaluado, fps, prm)
    if set_pieces is not None:
        m["set_pieces"] = _set_pieces(set_pieces, indice, evaluado, visible, n_video, fps, prm)
    return m


def _medir_balon(x, y, equipos, activo, fps, prm):
    """3a, 4 y 5 de un balón: las dos variantes de denominador pasan por aquí. Devuelve (sumas, disputa)."""
    visible = np.isfinite(x) & np.isfinite(y)
    prep = mc.preparar({"x": x, "y": y, "equipos": equipos})
    d_local, d_visitante = prep["d_equipo"]
    radio = prm["radio_disputa"]
    disputa = visible & (d_local <= radio) & (d_visitante <= radio)
    r = {"frames": int(visible.sum()), "disputa": int(disputa.sum())}

    # 4a y 4b: temblor y ternas casi rectas.
    d2 = segunda_diferencia(x, y, visible)
    r["_muestra_d2"] = d2.astype(np.float32)
    r["ternas"] = np.array([d2.size] + [int(np.sum(d2 < u)) for u in prm["ternas_m"]], dtype=np.int64)

    # 4a y 4b: toques con los umbrales de toque y controles Ret-12, con el código del experimento 2.
    estado = activo.astype(np.int8)
    toques = []
    for umbral in prm["umbrales_toque"]:
        t, eq, _ = ins.toques_por_tramos(prep, umbral, prm["radio_toque"], prm["min_tramo"])
        t, eq = mc.toques_en_juego(t, eq, estado)
        toques.append(int(np.sum(eq >= 0)))
    r["toques"] = np.array(toques, dtype=np.int64)
    r["controles"] = len(mc.retenciones(prep, prm["radio_control"], prm["frames_control"]))

    # 4b: autocorrelación de la velocidad del balón (vector), como Σ v_t·v_{t+k} / √(Σ|v_t|² · Σ|v_{t+k}|²).
    par = visible[:-1] & visible[1:]
    with np.errstate(invalid="ignore"):
        vx = np.where(par, np.diff(x) * fps, 0.0)
        vy = np.where(par, np.diff(y) * fps, 0.0)
    acf = []
    for k in prm["retardos"]:
        juntos = par[:-k] & par[k:]
        ax, ay, bx_, by_ = vx[:-k][juntos], vy[:-k][juntos], vx[k:][juntos], vy[k:][juntos]
        acf.append([float(np.sum(ax * bx_ + ay * by_)), float(np.sum(ax * ax + ay * ay)),
                    float(np.sum(bx_ * bx_ + by_ * by_))])
    r["acf"] = np.array(acf)

    # 5. Proximidad.
    d1 = prep["d1"]
    con_jugador = visible & np.isfinite(d1)
    cercano = prep["equipo_cercano"]
    otro = np.where(cercano == 0, d_visitante, d_local)
    with np.errstate(invalid="ignore"):
        rival_lejos = con_jugador & (otro - d1 >= prm["ventaja_rival_m"])
    r["proximidad"] = np.array([int(np.sum(visible & (d1 <= c))) for c in prm["distancias_m"]]
                               + [int(np.sum(visible & (d1 > prm["lejos_m"]))), int(rival_lejos.sum())],
                               dtype=np.int64)
    r["cambios_cercano"] = int(np.sum(con_jugador[1:] & con_jugador[:-1] & (cercano[1:] != cercano[:-1])))
    return r, disputa


def _perdidas(bx, by, px, py, visible, disputa, h_ini, largo_h, pitch, fps, prm):
    """3b: frames con balón y pérdidas (inicios de hueco) según lo que había en el último frame visto.

    Todos los huecos tienen balón en el frame anterior: el análisis del balón empieza en el primer frame
    con balón de cada tramo.
    """
    largo, ancho = pitch
    n = len(bx)
    vidx = np.flatnonzero(visible)
    with np.errstate(invalid="ignore"):
        cerca = np.sum(np.hypot(px[vidx] - bx[vidx, None], py[vidx] - by[vidx, None]) <= prm["radio_densidad"],
                       axis=1)
    densidad = np.searchsorted(np.asarray(prm["cortes_densidad"]), cerca, side="right")
    x, y = bx[vidx], by[vidx]
    junto_a_linea = np.minimum(np.minimum(x, largo - x), np.minimum(y, ancho - y)) <= prm["margen_linea"]
    central = (x >= largo / 3.0) & (x <= 2.0 * largo / 3.0)
    zona = np.where(junto_a_linea, 0, np.where(central, 1, 2))
    estrato = np.full(n, -1, dtype=np.int64)
    estrato[vidx] = densidad * 3 + zona
    en_disputa = disputa.astype(np.int64)
    grupo = np.full(n, -1, dtype=np.int64)
    grupo[vidx] = (np.random.default_rng(prm["semilla_placebo"]).random(vidx.size) < 0.5).astype(np.int64)

    # Una pérdida es el inicio de un hueco; el último frame visto es el anterior.
    ultimo = h_ini - 1
    corto = largo_h <= prm["hueco_corto_s"] * fps
    r = {"frames_estrato": np.bincount(estrato[vidx], minlength=9),
         "frames_disputa": np.bincount(en_disputa[vidx], minlength=2),
         "frames_placebo": np.bincount(grupo[vidx], minlength=2),
         "placebo_cortos": np.bincount(grupo[ultimo[corto]], minlength=2)}
    for nombre, sel in (("cortos", corto), ("largos", ~corto)):
        r[nombre] = {"estrato": np.bincount(estrato[ultimo[sel]], minlength=9),
                     "disputa": np.bincount(en_disputa[ultimo[sel]], minlength=2)}
    return r


def _detecciones(bx, by, visible, largo_r, fps, prm):
    """6: saltos imposibles, rachas de 1 o 2 frames y balón en la misma posición en frames seguidos."""
    par = visible[:-1] & visible[1:]
    dx, dy = np.diff(bx), np.diff(by)
    with np.errstate(invalid="ignore"):
        imposible = par & (np.hypot(dx, dy) * fps > prm["salto_imposible_ms"])
        identico = par & (dx == 0) & (dy == 0)
    i_ini, i_fin = _rachas(identico)
    frames_identicos = i_fin - i_ini + 1  # k pares idénticos seguidos son k + 1 frames
    clase = np.searchsorted(np.asarray(prm["cortes_identicas_s"]) * fps, frames_identicos, side="right")
    corta = largo_r <= prm["racha_corta_max"]
    return {"pares": int(par.sum()), "imposibles": int(imposible.sum()), "rachas": int(largo_r.size),
            "rachas_cortas": int(corta.sum()), "rachas_cortas_frames": int(largo_r[corta].sum()),
            "pares_identicos": int(identico.sum()), "identicas": np.bincount(clase, minlength=4)}


def _jugadores(px, py, team, evaluado, fps, prm):
    """7: jugadores localizados, tramos continuos de cada slot, su temblor y sus saltos imposibles."""
    tope = prm["max_localizados"]
    presente = np.isfinite(px) & np.isfinite(py)
    en_evaluados = presente[evaluado]
    localizados = np.stack([np.bincount(np.minimum(en_evaluados[:, team == k].sum(axis=1), tope),
                                        minlength=tope + 1) for k in (0, 1)])
    duraciones, d2, saltos = [], [], 0
    paso = 4.0 / fps  # velocidad centrada de ±2 frames, como slot_speeds de validation/partido/comun.py
    for j in range(px.shape[1]):
        ok = presente[:, j]
        a, b = _rachas(ok)
        duraciones.append((b - a).astype(np.int64))
        x, y = px[:, j].astype(float), py[:, j].astype(float)
        d2.append(segunda_diferencia(x, y, ok).astype(np.float32))
        with np.errstate(invalid="ignore"):
            alto = np.hypot(x[4:] - x[:-4], y[4:] - y[:-4]) / paso > prm["vel_max_jugador"]
        if alto.size:
            saltos += int(alto[0]) + int(np.sum(alto[1:] & ~alto[:-1]))
    return {"_muestra_slots": np.array([[int(np.sum(team == 0)), int(np.sum(team == 1))]], dtype=np.int64),
            "localizados": localizados,
            "_muestra_tramos": np.concatenate(duraciones) if duraciones else np.zeros(0, np.int64),
            "_muestra_d2": np.concatenate(d2) if d2 else np.zeros(0, np.float32),
            "saltos": saltos,
            "frames_evaluados": int(evaluado.sum())}


def _set_pieces(ventanas, indice, evaluado, visible, n_video, fps, prm):
    """8: frames con balón dentro de las ventanas `SET PIECES`, en los 10 s anteriores y en el resto."""
    dentro = np.zeros(n_video, dtype=bool)
    antes = np.zeros(n_video, dtype=bool)
    margen = int(round(prm["antes_set_piece_s"] * fps))
    for inicio, fin in ventanas:
        inicio, fin = int(inicio), int(fin)
        dentro[max(0, inicio):max(0, min(n_video, fin))] = True
        antes[max(0, inicio - margen):max(0, min(n_video, inicio))] = True
    antes &= ~dentro
    d = np.zeros(len(indice), dtype=bool)
    a = np.zeros(len(indice), dtype=bool)
    d[evaluado] = dentro[indice[evaluado]]
    a[evaluado] = antes[indice[evaluado]]
    resto = evaluado & ~d & ~a
    return {"ventanas": len(ventanas),
            "frames": np.array([d.sum(), a.sum(), resto.sum()], dtype=np.int64),
            "con_balon": np.array([(d & visible).sum(), (a & visible).sum(), (resto & visible).sum()],
                                  dtype=np.int64)}


# -- de las medidas a los agregados --------------------------------------------------------------------

def _sumar(a, b, clave=""):
    """Junta las medidas de dos trackings: suma recuentos, concatena muestras (claves `_muestra…`)."""
    if clave == "fps":
        if a != b:
            raise ValueError("no se pueden juntar trackings con distinto fps")
        return a
    if isinstance(a, dict):
        if set(a) != set(b):
            raise ValueError("los trackings no tienen las mismas medidas: {}".format(sorted(set(a) ^ set(b))))
        return {k: _sumar(a[k], b[k], k) for k in a}
    if clave.startswith("_muestra"):
        return np.concatenate([a, b])
    return a + b


class _Celdas:
    """Supresión de las celdas con pocos casos (bitácora §4 y §7.6): con `minimo` > 0, un recuento por
    debajo sale como "< minimo", y lo que se calcula solo con él, también. Los frames no son casos."""

    def __init__(self, minimo):
        self.minimo = int(minimo or 0)
        self.texto = "< {}".format(self.minimo)

    def caso(self, n):
        return self.texto if self.minimo and int(n) < self.minimo else int(n)

    def si(self, n, valor):
        return self.texto if self.minimo and int(n) < self.minimo else valor


def _pct(parte, total):
    return 100.0 * parte / total if total else None


def _por_minuto(n, frames, fps):
    return n / (frames / fps / 60.0) if frames else None


def _cuantiles(muestra, escala=1.0):
    muestra = np.asarray(muestra, dtype=float)
    if muestra.size == 0:
        return None
    return {"p{}".format(q): float(v) * escala for q, v in zip((10, 50, 90), np.percentile(muestra, (10, 50, 90)))}


def _mediana(muestra, escala=1.0):
    return float(np.median(muestra)) * escala if len(muestra) else None


def etiqueta_severidad(nombre, segundos):
    return "{} (huecos de hasta {:g} s)".format(nombre, segundos)


def _severidades(huecos_n, huecos_frames, con_balon, prm, c):
    """s(T) = M(T) / (V + M(T)) de cada severidad (R1), y el reparto de sus huecos por intervalos (R2)."""
    cortes = list(prm["cortes_s"])
    s, reparto = {}, {}
    for nombre, segundos in prm["severidades"]:
        k = cortes.index(segundos)
        n = int(huecos_n[:k + 1].sum())
        faltan = int(huecos_frames[:k + 1].sum())
        etiqueta = etiqueta_severidad(nombre, segundos)
        s[etiqueta] = c.si(n, _pct(faltan, con_balon + faltan))
        reparto[etiqueta] = {INTERVALOS[i]: c.si(int(huecos_n[i]), _pct(int(huecos_n[i]), n)) for i in range(k + 1)}
    return s, reparto


def _bloque_balon(r, fps, prm, c):
    minutos = r["frames"] / fps / 60.0
    ternas = r["ternas"]
    acf = {}
    for k, (num, da, db) in zip(prm["retardos"], r["acf"]):
        acf["{} frames".format(k)] = num / math.sqrt(da * db) if da > 0 and db > 0 else None
    prox = r["proximidad"]
    d = prm["distancias_m"]
    return {
        "3a": {"frames_con_balon": r["frames"], "disputa_pct": _pct(r["disputa"], r["frames"])},
        "4": {"minutos_con_balon": minutos,
              "temblor_cm": _mediana(r["_muestra_d2"], 100.0),
              "toques_por_min": {"umbral {:g} m/s".format(u): c.si(int(n), _por_minuto(int(n), r["frames"], fps))
                                 for u, n in zip(prm["umbrales_toque"], r["toques"])},
              "controles_ret12_por_min": c.si(r["controles"], _por_minuto(r["controles"], r["frames"], fps)),
              "autocorrelacion_velocidad": acf,
              "ternas": {"segunda_diferencia_menor_de_1_mm_pct": _pct(int(ternas[1]), int(ternas[0])),
                         "segunda_diferencia_menor_de_5_mm_pct": _pct(int(ternas[2]), int(ternas[0]))}},
        "5": {"mas_cercano_a_{:g}_m_o_menos_pct".format(d[0]): _pct(int(prox[0]), r["frames"]),
              "mas_cercano_a_{:g}_m_o_menos_pct".format(d[1]): _pct(int(prox[1]), r["frames"]),
              "mas_cercano_a_{:g}_m_o_menos_pct".format(d[2]): _pct(int(prox[2]), r["frames"]),
              "mas_cercano_a_mas_de_{:g}_m_pct".format(prm["lejos_m"]): _pct(int(prox[3]), r["frames"]),
              "rival_{:g}_m_mas_lejos_pct".format(prm["ventaja_rival_m"]): _pct(int(prox[4]), r["frames"]),
              "cambios_de_equipo_mas_cercano_por_min": c.si(r["cambios_cercano"],
                                                            _por_minuto(r["cambios_cercano"], r["frames"], fps))},
    }


def _bloque_perdidas(p, prm, c):
    def celda(perdidas, frames):
        return {"frames_con_balon": int(frames), "perdidas_n": c.caso(perdidas),
                "por_1000_frames": c.si(perdidas, 1000.0 * perdidas / frames if frames else None)}

    corte = "{:g} s".format(prm["hueco_corto_s"])
    salida = {}
    for clave, nombre in (("cortos", "huecos de hasta " + corte), ("largos", "huecos de más de " + corte)):
        q = p[clave]
        bloque = {"fuera de disputa": celda(int(q["disputa"][0]), int(p["frames_disputa"][0])),
                  "en disputa": celda(int(q["disputa"][1]), int(p["frames_disputa"][1]))}
        for i, densidad in enumerate(DENSIDADES):
            for j, zona in enumerate(ZONAS):
                bloque["{} · {}".format(densidad, zona)] = celda(int(q["estrato"][3 * i + j]),
                                                                 int(p["frames_estrato"][3 * i + j]))
        salida[nombre] = bloque
    salida["placebo: dos mitades al azar, huecos de hasta " + corte] = {
        "mitad A": celda(int(p["placebo_cortos"][0]), int(p["frames_placebo"][0])),
        "mitad B": celda(int(p["placebo_cortos"][1]), int(p["frames_placebo"][1]))}
    return salida


def resumir(parciales, minimo_celda=0, prm=PRM):
    """Los agregados de uno o varios trackings juntos (las medidas de `medidas`, sumadas).

    Con `minimo_celda` > 0, cada celda con menos casos sale como "< minimo_celda" y lo que se calcula solo
    con ella, también; los totales del partido siguen saliendo. Los recuentos de casos llevan claves que
    acaban en `_n`.
    """
    if isinstance(parciales, dict):
        parciales = [parciales]
    m = parciales[0]
    for otra in parciales[1:]:
        m = _sumar(m, otra)
    c = _Celdas(minimo_celda)
    fps = m["fps"]
    evaluados, con_balon, con_balon_sp = m["frames_evaluados"], m["frames_con_balon"], m["frames_con_balon_sp"]

    salida = {"0_control": {
        "frames_evaluados": evaluados,
        "frames_con_balon": con_balon,
        "balon_visible_pct": _pct(con_balon, evaluados),
        "balon_parado": {"tramos_n": c.caso(m["parado_tramos"]),
                         "frames": c.si(m["parado_tramos"], m["parado_frames"]),
                         "frames_pct": c.si(m["parado_tramos"], _pct(m["parado_frames"], evaluados)),
                         "frames_con_balon_fuera_de_ellos": con_balon_sp}}}

    def lista(ns, valores=None):
        valores = ns if valores is None else valores
        return [c.si(int(n), int(v)) for n, v in zip(ns, valores)]

    def sin_el_ultimo(ns, frames):
        """Los frames de cada intervalo de huecos menos el último (> 15 s): con él se sabría cuánto suman los
        bordes de los tramos, que no se analizan. Sale aparte, sumado con los bordes."""
        salida = lista(ns, frames)
        salida[-1] = None
        return salida

    s_todo, _ = _severidades(m["huecos_n"], m["huecos_frames"], con_balon, prm, c)
    s_sp, reparto_sp = _severidades(m["huecos_n_sp"], m["huecos_frames_sp"], con_balon_sp, prm, c)
    salida["1_huecos_y_rachas"] = {
        "intervalos": list(INTERVALOS),
        "todo": {"huecos_n": [c.caso(n) for n in m["huecos_n"]],
                 "huecos_frames": sin_el_ultimo(m["huecos_n"], m["huecos_frames"]),
                 "frames_sin_balon_en_huecos_de_mas_de_15_s_o_en_los_bordes":
                     evaluados - con_balon - int(m["huecos_frames"][:4].sum()),
                 "rachas_n": [c.caso(n) for n in m["rachas_n"]], "rachas_frames": lista(m["rachas_n"], m["rachas_frames"])},
        "sin_parado": {"huecos_n": [c.caso(n) for n in m["huecos_n_sp"]],
                       "huecos_frames": sin_el_ultimo(m["huecos_n_sp"], m["huecos_frames_sp"])},
        "s_pct": {"todo": s_todo, "sin_parado": s_sp},
        "reparto_de_los_huecos_pct": {"sin_parado": reparto_sp},
    }
    salida["2_salto_tras_hueco"] = {
        "distancias": list(DISTANCIAS),
        "huecos_n": {INTERVALOS[i]: [c.caso(n) for n in m["salto"][i]] for i in range(5)}}

    bloques = {v: _bloque_balon(m[v], fps, prm, c) for v in VARIANTES}
    salida["3a_disputas"] = {v: bloques[v]["3a"] for v in VARIANTES}
    salida["3b_perdidas_por_1000_frames_con_balon"] = _bloque_perdidas(m["perdidas"], prm, c)
    salida["4_suavizado"] = {v: bloques[v]["4"] for v in VARIANTES}
    salida["5_proximidad"] = {v: bloques[v]["5"] for v in VARIANTES}

    d = m["detecciones"]
    salida["6_detecciones"] = {
        "pares_de_frames_con_balon": d["pares"],
        "saltos_de_mas_de_{:g}_m_s_n".format(prm["salto_imposible_ms"]): c.caso(d["imposibles"]),
        "saltos_de_mas_de_{:g}_m_s_pct".format(prm["salto_imposible_ms"]): c.si(d["imposibles"], _pct(d["imposibles"], d["pares"])),
        "rachas_con_balon": d["rachas"],
        "rachas_de_1_o_2_frames_n": c.caso(d["rachas_cortas"]),
        "rachas_de_1_o_2_frames_pct": c.si(d["rachas_cortas"], _pct(d["rachas_cortas"], d["rachas"])),
        "pares_con_la_misma_posicion_n": c.caso(d["pares_identicos"]),
        "pares_con_la_misma_posicion_pct": c.si(d["pares_identicos"], _pct(d["pares_identicos"], d["pares"])),
        "rachas_con_la_misma_posicion_n": {IDENTICAS[i]: c.caso(n) for i, n in enumerate(d["identicas"])}}

    if "jugadores" in m:
        j = m["jugadores"]
        minutos = j["frames_evaluados"] / fps / 60.0
        localizados = {}
        for k, equipo in enumerate(("local", "visitante")):
            h = j["localizados"][k]
            valores = np.repeat(np.arange(h.size), h)
            localizados[equipo] = dict({"media": float(valores.mean()) if valores.size else None},
                                       **(_cuantiles(valores) or {}))
        slots = j["_muestra_slots"]  # una fila por tracking; con varios juntos, la media
        salida["7_jugadores"] = {
            "slots_por_equipo": {"local": float(slots[:, 0].mean()), "visitante": float(slots[:, 1].mean())},
            "localizados_por_frame": localizados,
            "tramos_de_un_slot_s": _cuantiles(j["_muestra_tramos"], 1.0 / fps),
            "tramos_por_minuto": c.si(len(j["_muestra_tramos"]), len(j["_muestra_tramos"]) / minutos if minutos else None),
            "temblor_cm": _mediana(j["_muestra_d2"], 100.0),
            "saltos_de_mas_de_{:g}_m_s_por_minuto".format(prm["vel_max_jugador"]):
                c.si(j["saltos"], j["saltos"] / minutos if minutos else None)}

    if "set_pieces" in m:
        sp = m["set_pieces"]
        nombres = ("dentro de las ventanas", "{:g} s antes".format(prm["antes_set_piece_s"]), "resto de los evaluados")
        salida["8_set_pieces"] = {"ventanas": int(sp["ventanas"])}
        for i, nombre in enumerate(nombres):
            salida["8_set_pieces"][nombre] = {"frames": int(sp["frames"][i]),
                                              "con_balon_pct": _pct(int(sp["con_balon"][i]), int(sp["frames"][i]))}
    return salida


def perfil(trk, set_pieces=None, minimo_celda=0, jugadores=True, prm=PRM):
    """Los agregados de un tracking: `resumir(medidas(trk))`."""
    return resumir([medidas(trk, set_pieces, jugadores, prm)], minimo_celda, prm)


def para_imprimir(valor, decimales=3):
    """La salida de `resumir` con tipos de Python y los decimales redondeados, lista para json.dumps."""
    if isinstance(valor, dict):
        return {str(k): para_imprimir(v, decimales) for k, v in valor.items()}
    if isinstance(valor, (list, tuple, np.ndarray)):
        return [para_imprimir(v, decimales) for v in list(valor)]
    if isinstance(valor, (bool, np.bool_)):
        return bool(valor)
    if isinstance(valor, (int, np.integer)):
        return int(valor)
    if isinstance(valor, (float, np.floating)):
        return round(float(valor), decimales) if math.isfinite(valor) else None
    return valor


def primarias(salida, prm=PRM):
    """Las medidas que deciden (bitácora §5), en un diccionario plano. None si falta o está suprimida.

    Todas con el denominador `sin_parado`, salvo las `s_…_todo`, que se apuntan para comparar.
    """
    def num(v):
        return float(v) if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool) else None

    h = salida["1_huecos_y_rachas"]
    p = {}
    for nombre, segundos in prm["severidades"]:
        etiqueta = etiqueta_severidad(nombre, segundos)
        p["s_" + nombre] = num(h["s_pct"]["sin_parado"][etiqueta])
        p["s_" + nombre + "_todo"] = num(h["s_pct"]["todo"][etiqueta])
        for intervalo, valor in h["reparto_de_los_huecos_pct"]["sin_parado"][etiqueta].items():
            p["reparto_{} {}".format(nombre, intervalo)] = num(valor)
    p["disputa_pct"] = num(salida["3a_disputas"]["sin_parado"]["disputa_pct"])
    s = salida["4_suavizado"]["sin_parado"]
    p["temblor_cm"] = num(s["temblor_cm"])
    p["toques_por_min"] = num(s["toques_por_min"]["umbral {:g} m/s".format(prm["umbrales_toque"][0])])
    p["controles_por_min"] = num(s["controles_ret12_por_min"])
    x = salida["5_proximidad"]["sin_parado"]
    for d in prm["distancias_m"]:
        p["cercano_a_{:g}_m_pct".format(d)] = num(x["mas_cercano_a_{:g}_m_o_menos_pct".format(d)])
    p["cambios_cercano_por_min"] = num(x["cambios_de_equipo_mas_cercano_por_min"])
    if "7_jugadores" in salida:
        j = salida["7_jugadores"]
        p["localizados_local_media"] = num(j["localizados_por_frame"]["local"]["media"])
        p["localizados_visitante_media"] = num(j["localizados_por_frame"]["visitante"]["media"])
        p["tramo_de_slot_p50_s"] = num((j["tramos_de_un_slot_s"] or {}).get("p50"))
        p["temblor_jugadores_cm"] = num(j["temblor_cm"])
    return p
