"""Prueba el perfil del ATD (validation/perfil_atd/perfil.py) sin datos del partido: todo es inventado.

    python validation/scripts/prueba_perfil_atd.py

Comprueba cada agregado con trackings inventados de resultado conocido: huecos y rachas, severidades,
salto tras el hueco, balón parado (contra `still_runs` del diagnóstico del 12/11), disputas, proximidad,
toques y controles del experimento 2, pérdidas por estrato, detecciones falsas, jugadores, SET PIECES y la
supresión de las celdas con menos de 5 casos. Además, que lo que cae fuera de los tramos evaluados no
cuenta, que juntar dos trackings suma bien, el determinismo, que `perfil` no abre ficheros (`no_files`) y
que el script del partido no imprime valores de datos cuando falla.

Nunca lee el partido: el script de `validation/partido/` solo se llama con una carpeta vacía. Sale con
código 1 si falla alguna comprobación. Claude puede ejecutarlo (validation/README.md).
"""

import contextlib
import io
import json
import os
import shutil
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(ROOT, "validation", "perfil_atd"))
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import perfil as pf  # noqa: E402
import prueba_pipeline as pp  # noqa: E402  (no_files y safe_tmp)
from possession import tracking  # noqa: E402

import comun  # noqa: E402  (validation/partido/comun.py: la media móvil)
import diagnostico_coordenadas as dc  # noqa: E402  (still_runs: la definición de balón parado del 12/11)
import instrumento as ins  # noqa: E402
import medidas_cambios as mc  # noqa: E402
import perfil_atd as script_partido  # noqa: E402  (validation/partido/perfil_atd.py)

SEED = 20261114
PITCH = (105.0, 68.0)
failures = []


def check(name, ok, detail=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", name, "   " + detail if detail else ""))
    if not ok:
        failures.append(name)


def cerca(a, b, tol=1e-9):
    return a is not None and b is not None and abs(a - b) <= tol


def hacer(bx, by, px, py, team, blocks, fps=25):
    return tracking.Tracking(np.asarray(bx, float), np.asarray(by, float), np.asarray(px, np.float32),
                             np.asarray(py, np.float32), np.asarray(team, np.int8), PITCH, tuple(blocks), fps)


def lejos(n, slots):
    """Jugadores quietos en las esquinas: no opinan de nada."""
    esquinas = [(3.0, 3.0), (102.0, 65.0), (3.0, 65.0), (102.0, 3.0)]
    px = np.tile(np.array([esquinas[j % 4][0] for j in range(slots)], dtype=np.float32), (n, 1))
    py = np.tile(np.array([esquinas[j % 4][1] for j in range(slots)], dtype=np.float32), (n, 1))
    return px, py


def camino(t):
    """Un balón que no para: nunca queda 3 s dentro de 2 m."""
    t = np.asarray(t, dtype=float)
    return 52.5 + 30.0 * np.sin(t / 40.0), 34.0 + 20.0 * np.cos(t / 55.0)


# -- 1 y 2: huecos, rachas, severidades y salto --------------------------------------------------------

HUECOS = [(200, 210), (300, 313), (400, 450), (500, 551), (600, 726), (1300, 1305), (1400, 1780)]
BLOQUES = [(100, 1100), (1300, 1900)]


def caso_huecos(fuera="nan"):
    n = 2000
    bx, by = camino(np.arange(n))
    rng = np.random.default_rng(SEED)
    fuera_de_bloques = np.ones(n, bool)
    for a, b in BLOQUES:
        fuera_de_bloques[a:b] = False
    if fuera == "nan":
        bx[fuera_de_bloques], by[fuera_de_bloques] = np.nan, np.nan
    else:  # basura que no puede contar: posiciones al azar y saltos imposibles
        bx[fuera_de_bloques] = rng.uniform(0, 105, fuera_de_bloques.sum())
        by[fuera_de_bloques] = rng.uniform(0, 68, fuera_de_bloques.sum())
    for a, b in HUECOS:
        bx[a:b], by[a:b] = np.nan, np.nan
    px, py = lejos(n, 2)
    return hacer(bx, by, px, py, [0, 1], BLOQUES)


def comprobar_huecos():
    print("1 y 2. Huecos, rachas, severidades y salto")
    trk = caso_huecos()
    s = pf.perfil(trk)
    c0, h = s["0_control"], s["1_huecos_y_rachas"]
    check("frames evaluados y con balón", c0["frames_evaluados"] == 1600 and c0["frames_con_balon"] == 965,
          "{} y {}".format(c0["frames_evaluados"], c0["frames_con_balon"]))
    check("sin balón parado en un balón que no para", c0["balon_parado"]["tramos_n"] == 0)
    check("huecos por intervalo (el de 5 frames al inicio del tramo es un borde y no cuenta)",
          h["todo"]["huecos_n"] == [1, 2, 1, 1, 1], str(h["todo"]["huecos_n"]))
    check("frames de los huecos por intervalo, sin los de más de 15 s",
          h["todo"]["huecos_frames"] == [10, 63, 51, 126, None], str(h["todo"]["huecos_frames"]))
    check("los de más de 15 s salen sumados con los bordes (380 + 5)",
          h["todo"]["frames_sin_balon_en_huecos_de_mas_de_15_s_o_en_los_bordes"] == 385)
    check("rachas por intervalo, con los bordes exactos (50 frames es 0,5–2 s)",
          h["todo"]["rachas_n"] == [0, 2, 5, 1, 0] and h["todo"]["rachas_frames"] == [0, 99, 492, 374, 0],
          "{} {}".format(h["todo"]["rachas_n"], h["todo"]["rachas_frames"]))
    esperado = {"baja": 100.0 * 73 / (965 + 73), "media": 100.0 * 124 / (965 + 124), "alta": 100.0 * 250 / (965 + 250)}
    ok = all(cerca(h["s_pct"][v][pf.etiqueta_severidad(k, seg)], esperado[k])
             for v in pf.VARIANTES for k, seg in pf.PRM["severidades"])
    check("s(T) = M(T) / (V + M(T)) en las tres severidades y las dos variantes", ok)
    rep = h["reparto_de_los_huecos_pct"]["sin_parado"][pf.etiqueta_severidad("media", 5.0)]
    check("reparto de los huecos de hasta 5 s", cerca(rep["≤ 0,5 s"], 25.0) and cerca(rep["0,5–2 s"], 50.0)
          and cerca(rep["2–5 s"], 25.0), str(rep))

    x, y = camino(np.arange(2000))
    tabla = np.zeros((5, 3), int)
    for a, b in HUECOS:
        if a in (100, 1300) or b in (1100, 1900):
            continue
        clase = int(np.searchsorted(np.array(pf.PRM["cortes_s"]) * 25, b - a, side="left"))
        d = float(np.hypot(x[b] - x[a - 1], y[b] - y[a - 1]))
        tabla[clase, 0 if d < 3 else 1 if d < 15 else 2] += 1
    obtenida = np.array([s["2_salto_tras_hueco"]["huecos_n"][i] for i in pf.INTERVALOS])
    check("salto tras el hueco: solo huecos con balón a los dos lados del mismo tramo",
          np.array_equal(obtenida, tabla) and obtenida.sum() == 6, str(obtenida.tolist()))

    otra = pf.perfil(caso_huecos(fuera="basura"))
    check("lo que cae fuera de los tramos evaluados no cuenta",
          json.dumps(pf.para_imprimir(otra), sort_keys=True) == json.dumps(pf.para_imprimir(s), sort_keys=True))


# -- balón parado --------------------------------------------------------------------------------------

def balon_con_paradas(rng, n):
    """Balón que alterna tramos parados (dentro de 1,5 m), tramos en movimiento y huecos de 1 a 40 frames."""
    x, y = np.empty(n), np.empty(n)
    t, px_, py_ = 0, 50.0, 34.0
    while t < n:
        largo = int(rng.integers(20, 200))
        if rng.random() < 0.5:
            r, a = 1.5 * np.sqrt(rng.random(largo)), rng.uniform(0, 2 * np.pi, largo)
            x[t:t + largo] = px_ + r[:n - t] * np.cos(a[:n - t])
            y[t:t + largo] = py_ + r[:n - t] * np.sin(a[:n - t])
        else:
            pasos = np.cumsum(rng.normal(0, 0.5, (largo, 2)), axis=0)
            x[t:t + largo] = px_ + pasos[:n - t, 0]
            y[t:t + largo] = py_ + pasos[:n - t, 1]
            px_, py_ = x[min(n, t + largo) - 1], y[min(n, t + largo) - 1]
        t += largo
    t = 0
    while t < n:
        t += int(rng.integers(10, 120))
        hueco = int(rng.integers(1, 41))
        x[t:t + hueco], y[t:t + hueco] = np.nan, np.nan
        t += hueco
    return x, y


def comprobar_parado():
    print("Balón parado y la variante sin_parado")
    rng = np.random.default_rng(SEED)
    iguales = True
    for _ in range(20):
        n = 3000
        x, y = balon_con_paradas(rng, n)
        largos = [l for l in dc.still_runs(x, y, 0, n - 1, 2.0) if l >= 75]
        visible = np.isfinite(x) & np.isfinite(y)
        mascara, cuantos = pf.balon_parado(x, y, visible, [(0, n)], 2.0, 75, 25)
        iguales &= cuantos == len(largos) and int(mascara.sum()) == int(sum(largos))
    check("los tramos de balón parado son los de still_runs (12/11), en 20 balones al azar", iguales)

    n = 600
    bx, by = camino(np.arange(n))
    bx[200:300], by[200:300] = 40.0, 30.0  # parado 4 s
    bx[240:250], by[240:250] = np.nan, np.nan  # hueco de 10 frames dentro: no corta el tramo
    bx[400:410], by[400:410] = np.nan, np.nan  # hueco fuera
    px, py = lejos(n, 2)
    s = pf.perfil(hacer(bx, by, px, py, [0, 1], [(0, n)]))
    h = s["1_huecos_y_rachas"]
    check("un tramo parado de 4 s con un hueco dentro", s["0_control"]["balon_parado"]["tramos_n"] == 1
          and s["0_control"]["balon_parado"]["frames"] == 100)
    check("el hueco de dentro cuenta en todo y no en sin_parado",
          h["todo"]["huecos_n"][0] == 2 and h["sin_parado"]["huecos_n"][0] == 1)
    check("sin_parado quita del denominador los frames con balón del tramo parado",
          s["0_control"]["balon_parado"]["frames_con_balon_fuera_de_ellos"] == 600 - 20 - 90)


# -- 3a, 4 y 5: disputas, instrumento y proximidad ----------------------------------------------------

def comprobar_disputas_y_proximidad():
    print("3a y 5. Disputas y proximidad (todo se mueve junto a 3 m/s)")
    n = 400
    t = np.arange(n)
    bx, by = 20.0 + 0.12 * t, np.full(n, 34.0)
    desplazamiento = np.zeros((n, 4, 2))
    desplazamiento[:200] = [(0.5, 0), (0, 30), (0, 2.5), (0, -30)]
    desplazamiento[200:300] = [(4, 0), (0, 30), (0, 10), (0, -30)]
    desplazamiento[300:] = [(6, 0), (0, 30), (0, 4.5), (0, -30)]
    px = bx[:, None] + desplazamiento[:, :, 0]
    py = by[:, None] + desplazamiento[:, :, 1]
    s = pf.perfil(hacer(bx, by, px, py, [0, 0, 1, 1], [(0, n)]))
    check("disputa: un jugador de cada equipo a 3 m o menos", cerca(s["3a_disputas"]["todo"]["disputa_pct"], 50.0))
    p = s["5_proximidad"]["todo"]
    check("más cercano a 1, 1,5 y 3 m, y a más de 5 m",
          cerca(p["mas_cercano_a_1_m_o_menos_pct"], 50.0) and cerca(p["mas_cercano_a_1.5_m_o_menos_pct"], 50.0)
          and cerca(p["mas_cercano_a_3_m_o_menos_pct"], 50.0) and cerca(p["mas_cercano_a_mas_de_5_m_pct"], 0.0))
    check("el rival a 1 m o más que el más cercano", cerca(p["rival_1_m_mas_lejos_pct"], 100.0))
    check("un cambio de equipo más cercano en 16 s: 3,75 por minuto",
          cerca(p["cambios_de_equipo_mas_cercano_por_min"], 3.75))


def comprobar_instrumento():
    print("4. Toques, controles y temblor: el instrumento del experimento 2")
    n = 600
    t = np.arange(n)
    ida = 10.0 + 0.2 * np.minimum(t, 300)
    bx = np.where(t <= 300, ida, 70.0 - 0.2 * (t - 300))  # 5 m/s hasta el frame 300 y vuelta
    by = np.full(n, 34.0)
    px = np.zeros((n, 3))
    py = np.zeros((n, 3))
    px[:, 0], py[:, 0] = 5.0, 5.0  # local, lejos ...
    px[50:90, 0], py[50:90, 0] = bx[50:90] + 0.5, 34.0  # ... salvo 40 frames pegado al balón: un control
    px[:, 1], py[:, 1] = 70.0, 34.5  # visitante en el punto de la vuelta, a 0,5 m: el toque es suyo
    px[:, 2], py[:, 2] = 100.0, 60.0
    team = [0, 1, 1]
    s = pf.perfil(hacer(bx, by, px, py, team, [(0, n)]))
    v = s["4_suavizado"]["todo"]
    minutos = n / 25.0 / 60.0
    toques = [round(v["toques_por_min"]["umbral {:g} m/s".format(u)] * minutos) for u in pf.PRM["umbrales_toque"]]
    check("un toque en la vuelta con los tres umbrales", toques == [1, 1, 1], str(toques))
    check("un control Ret-12 (el visitante solo está 9 frames a 1 m o menos)",
          round(v["controles_ret12_por_min"] * minutos) == 1)
    suave = pf.perfil(hacer(comun.moving_average(bx, 12), comun.moving_average(by, 12), px, py, team, [(0, n)]))
    check("con el balón suavizado 25 frames, el toque ya no llega a 3 m/s",
          suave["4_suavizado"]["todo"]["toques_por_min"]["umbral 3 m/s"] == 0)

    rng = np.random.default_rng(SEED)
    x, y = balon_con_paradas(rng, 3000)
    activo = np.ones(3000, bool)
    propio = pf.perfil(hacer(x, y, *lejos(3000, 2), [0, 1], [(0, 3000)]))["4_suavizado"]["todo"]["temblor_cm"]
    check("el temblor es el de instrumento.temblor", cerca(propio, 100.0 * ins.temblor(x, y, activo), 1e-5),
          "{:.4f} cm".format(propio))


# -- 3b: pérdidas por estrato --------------------------------------------------------------------------

def comprobar_perdidas():
    print("3b. Pérdidas por 1.000 frames con balón, por estrato")
    n = 1000
    t = np.arange(n)
    bx, by = 50.0 + 5.0 * np.sin(t / 30.0), 34.0 + 5.0 * np.cos(t / 30.0)  # tercio central, lejos de las líneas
    px = np.stack([bx + 1.0, bx], axis=1)
    py = np.stack([by, by + np.where(t < 500, 2.0, 20.0)], axis=1)  # disputa en la primera mitad
    for a, b in ((100, 110), (200, 330), (600, 605), (700, 710), (800, 950)):
        bx[a:b], by[a:b] = np.nan, np.nan
    m = pf.medidas(hacer(bx, by, px, py, [0, 1], [(0, n)]))
    p = m["perdidas"]
    check("frames con balón fuera y dentro de disputa", p["frames_disputa"].tolist() == [335, 360])
    check("pérdidas de huecos de hasta 5 s: 2 fuera y 1 en disputa", p["cortos"]["disputa"].tolist() == [2, 1])
    check("pérdidas de huecos de más de 5 s: 1 y 1", p["largos"]["disputa"].tolist() == [1, 1])
    esperado = np.zeros(9, int)
    esperado[1], esperado[4] = 335, 360  # 0–1 y 2–3 jugadores a 5 m, tercio central
    check("frames por densidad y zona", p["frames_estrato"].tolist() == esperado.tolist(), str(p["frames_estrato"]))
    check("pérdidas por densidad y zona", p["cortos"]["estrato"][1] == 2 and p["cortos"]["estrato"][4] == 1
          and p["largos"]["estrato"][1] == 1 and p["largos"]["estrato"][4] == 1)
    check("el placebo reparte todos los frames y las pérdidas cortas",
          int(p["frames_placebo"].sum()) == 695 and int(p["placebo_cortos"].sum()) == 3)
    celda = pf.resumir(m)["3b_perdidas_por_1000_frames_con_balon"]["huecos de hasta 5 s"]["en disputa"]
    check("por 1.000 frames", cerca(celda["por_1000_frames"], 1000.0 / 360))


# -- 6: detecciones ------------------------------------------------------------------------------------

def comprobar_detecciones():
    print("6. Detecciones falsas y balón congelado")
    n = 600
    congelado = np.zeros(n, bool)
    congelado[451:481] = True  # 31 frames iguales (450–480)
    congelado[501:510] = True  # 10 frames iguales (500–509)
    tau = np.cumsum(~congelado) - 1
    bx, by = 20.0 + 0.1 * tau, 30.0 + 0.05 * tau
    by[100:105] += 3.0  # salto de 3 m en un frame (75 m/s) y vuelta: 2 pares imposibles
    bx[300:400], by[300:400] = np.nan, np.nan
    bx[330], by[330] = 20.0 + 0.1 * tau[330], 30.0 + 0.05 * tau[330]  # detección suelta
    bx[360:362], by[360:362] = 20.0 + 0.1 * tau[360:362], 30.0 + 0.05 * tau[360:362]  # dos seguidas
    d = pf.perfil(hacer(bx, by, *lejos(n, 2), [0, 1], [(0, n)]))["6_detecciones"]
    check("pares de frames con balón", d["pares_de_frames_con_balon"] == 499, str(d["pares_de_frames_con_balon"]))
    check("2 saltos de más de 40 m/s", d["saltos_de_mas_de_40_m_s_n"] == 2)
    check("rachas de 1 o 2 frames: 2 de 4", d["rachas_de_1_o_2_frames_n"] == 2 and d["rachas_con_balon"] == 4)
    check("misma posición: 39 pares, una racha de menos de 1 s y otra de 1–5 s",
          d["pares_con_la_misma_posicion_n"] == 39
          and d["rachas_con_la_misma_posicion_n"] == {"< 1 s": 1, "1–5 s": 1, "5–30 s": 0, "30 s o más": 0})


# -- 7: jugadores --------------------------------------------------------------------------------------

def comprobar_jugadores():
    print("7. Jugadores")
    n = 300
    t = np.arange(n)
    px = np.full((n, 3), np.nan)
    py = np.full((n, 3), np.nan)
    px[:, 0], py[:, 0] = 10.0 + 0.1 * t, 20.0  # local, siempre, en línea recta
    for a, b in ((20, 60), (200, 230)):
        px[a:b, 1], py[a:b, 1] = 60.0 - 0.1 * t[a:b], 40.0  # local, a ratos
    px[40:60, 1] += 10.0  # cambio de identidad: un salto de 10 m
    px[160:170, 2], py[160:170, 2] = 80.0, 50.0  # visitante, 10 frames
    bx, by = camino(t)
    j = pf.perfil(hacer(bx, by, px, py, [0, 0, 1], [(0, 100), (150, 300)]))["7_jugadores"]
    check("slots por equipo", j["slots_por_equipo"] == {"local": 2.0, "visitante": 1.0})
    check("localizados por frame: media de 1,28 y 0,04",
          cerca(j["localizados_por_frame"]["local"]["media"], 320 / 250) and
          cerca(j["localizados_por_frame"]["visitante"]["media"], 10 / 250))
    q = np.percentile(np.array([100, 150, 40, 30, 10]) / 25.0, (10, 50, 90))
    check("tramos de un slot (el salto no corta el tramo; el paso de un tramo evaluado a otro, sí)",
          all(cerca(j["tramos_de_un_slot_s"]["p{}".format(k)], v) for k, v in zip((10, 50, 90), q)),
          str(j["tramos_de_un_slot_s"]))
    check("tramos por minuto: 5 tramos en 10 s", cerca(j["tramos_por_minuto"], 30.0))
    check("un salto de más de 12 m/s", cerca(j["saltos_de_mas_de_12_m_s_por_minuto"], 6.0))
    check("temblor de jugadores en línea recta, casi cero", j["temblor_cm"] < 0.01, "{:.5f} cm".format(j["temblor_cm"]))


# -- 8: SET PIECES -------------------------------------------------------------------------------------

def comprobar_set_pieces():
    print("8. SET PIECES")
    n = 1000
    bx, by = camino(np.arange(n))
    bx[500:], by[500:] = np.nan, np.nan
    s = pf.perfil(hacer(bx, by, *lejos(n, 2), [0, 1], [(100, 900)]),
                  set_pieces=[(300, 350), (600, 700), (50, 120)])["8_set_pieces"]
    check("frames dentro, 10 s antes y en el resto", (s["dentro de las ventanas"]["frames"], s["10 s antes"]["frames"],
                                                      s["resto de los evaluados"]["frames"]) == (170, 430, 200))
    check("% con balón en cada uno", cerca(s["dentro de las ventanas"]["con_balon_pct"], 100.0 * 70 / 170)
          and cerca(s["10 s antes"]["con_balon_pct"], 100.0 * 330 / 430)
          and cerca(s["resto de los evaluados"]["con_balon_pct"], 0.0))


# -- supresión, juntar, determinismo y guardas ---------------------------------------------------------

def hojas(valor, clave=""):
    """(clave, valor) de cada hoja; dentro de una clave que acaba en `_n`, todas sus hojas llevan esa clave."""
    if isinstance(valor, dict):
        for k, v in valor.items():
            yield from hojas(v, clave if clave.endswith("_n") else k)
    elif isinstance(valor, list):
        for v in valor:
            yield from hojas(v, clave)
    else:
        yield clave, valor


def comprobar_supresion():
    print("Supresión de las celdas con menos de 5 casos")
    s = pf.para_imprimir(pf.perfil(caso_huecos(), minimo_celda=5))
    malos = [(k, v) for k, v in hojas(s) if k.endswith("_n") and v != "< 5" and not (isinstance(v, int) and v >= 5)]
    check("todo recuento de casos (claves _n) es '< 5' o 5 o más", not malos, str(malos[:3]))
    h = s["1_huecos_y_rachas"]["todo"]
    check("los frames de un intervalo suprimido también se suprimen",
          all(f in ("< 5", None) for n, f in zip(h["huecos_n"], h["huecos_frames"]) if n == "< 5"))
    sev = s["1_huecos_y_rachas"]["s_pct"]["todo"]
    check("una severidad con menos de 5 huecos se suprime", sev[pf.etiqueta_severidad("baja", 2.0)] == "< 5")

    def celdas(valor):
        if isinstance(valor, dict):
            if "perdidas_n" in valor:
                yield valor
            for v in valor.values():
                yield from celdas(v)
    perd = list(celdas(s["3b_perdidas_por_1000_frames_con_balon"]))
    check("las tasas de una celda suprimida también se suprimen",
          all(c["por_1000_frames"] == "< 5" for c in perd if c["perdidas_n"] == "< 5") and perd)


def comprobar_bordes():
    """Nada de la salida dice si el balón se ve en el primer o en el último frame de un tramo evaluado."""
    print("Bordes de los tramos evaluados (regla nº 1)")
    n = 1200
    bloques = [(100, 500), (600, 1100)]
    variantes = {}
    for nombre, borde in (("con balón en los bordes", 0), ("sin balón en los bordes", 30)):
        bx, by = camino(np.arange(n))
        for a, b in bloques:
            bx[a:a + borde], by[a:a + borde] = np.nan, np.nan
            bx[b - borde:b], by[b - borde:b] = np.nan, np.nan
        for a, b in ((200, 210), (300, 360), (700, 705), (800, 1000)):
            bx[a:b], by[a:b] = np.nan, np.nan
        variantes[nombre] = pf.perfil(hacer(bx, by, *lejos(n, 2), [0, 1], bloques))
    for nombre, s in variantes.items():
        huecos = sum(s["1_huecos_y_rachas"]["todo"]["huecos_n"])
        rachas = s["6_detecciones"]["rachas_con_balon"]
        saltos = sum(sum(fila) for fila in s["2_salto_tras_hueco"]["huecos_n"].values())
        p = s["3b_perdidas_por_1000_frames_con_balon"]
        perdidas = sum(p[k][z]["perdidas_n"] for k in ("huecos de hasta 5 s", "huecos de más de 5 s")
                       for z in ("fuera de disputa", "en disputa"))
        check("{}: rachas − huecos = tramos, y cada hueco tiene salto y pérdida".format(nombre),
              rachas - huecos == 2 and saltos == huecos and perdidas == huecos,
              "huecos {} · rachas {} · saltos {} · pérdidas {}".format(huecos, rachas, saltos, perdidas))
    a, b = (variantes[k]["1_huecos_y_rachas"]["todo"] for k in variantes)
    check("los huecos de dentro son los mismos con y sin balón en los bordes",
          a["huecos_n"] == b["huecos_n"] and a["huecos_frames"] == b["huecos_frames"])


def comprobar_lectura():
    """La regla como código (validation/perfil_atd/leer_atd.py), en lo que no necesita la DFL."""
    print("La regla como código, sin la DFL")
    import leer_atd as la
    s = pf.para_imprimir(pf.perfil(caso_huecos(), minimo_celda=5))
    informe = la.leer(s, dfl=None)
    check("si R0 no cuadra, la lectura se para antes de medir nada en la DFL", informe["parar"])
    valor, cota = la.s_del_atd(s, "baja", 2.0)
    con_balon = s["0_control"]["balon_parado"]["frames_con_balon_fuera_de_ellos"]
    check("una s(T) suprimida es una cota: 4 huecos de T segundos", valor is None
          and cerca(cota, 100.0 * 200 / (con_balon + 200)), "{:.2f}".format(cota))
    reparto = la.reparto_del_atd(s, "media", 5.0)
    check("un reparto suprimido es una cota", all(v is None and c > 0 for v, c in reparto.values()), str(reparto))
    check("la interpolación de OBJETIVO respeta el suelo y la rejilla",
          la.interpolar((0, 0.1, 0.2), (5.0, 5.0, 15.0), 3.0) == (0, "por debajo del suelo")
          and cerca(la.interpolar((0, 0.1, 0.2), (5.0, 5.0, 15.0), 10.0)[0], 0.15)
          and la.interpolar((0, 0.1, 0.2), (5.0, 5.0, 15.0), 20.0) == (0.2, "por encima de la rejilla"))


def comprobar_juntar():
    print("Juntar varios trackings")
    m = pf.medidas(caso_huecos())
    uno, dos = pf.resumir(m), pf.resumir([m, m])
    check("los recuentos se suman", dos["0_control"]["frames_evaluados"] == 2 * uno["0_control"]["frames_evaluados"]
          and dos["1_huecos_y_rachas"]["todo"]["huecos_n"] == [2 * k for k in uno["1_huecos_y_rachas"]["todo"]["huecos_n"]])
    check("las proporciones, medianas y tasas no cambian",
          json.dumps(pf.para_imprimir(pf.primarias(uno))) == json.dumps(pf.para_imprimir(pf.primarias(dos))))


def comprobar_guardas():
    print("Guardas: ficheros, determinismo, fps y el script del partido")
    trk = caso_huecos()
    try:
        with pp.no_files():
            a = json.dumps(pf.para_imprimir(pf.perfil(trk, set_pieces=[(300, 350)])), sort_keys=True)
            b = json.dumps(pf.para_imprimir(pf.perfil(trk, set_pieces=[(300, 350)])), sort_keys=True)
        abre = False
    except AssertionError:
        abre, a, b = True, "", "x"
    check("perfil no abre ningún fichero", not abre)
    check("dos ejecuciones dan lo mismo", a == b)
    check("las primarias son números", all(isinstance(v, float) for v in pf.primarias(pf.perfil(trk)).values()
                                           if v is not None) and pf.primarias(pf.perfil(trk))["s_media"] is not None)
    otro = trk._replace(fps=30)
    check("con otro fps da error en vez de medir mal", pp.raises(ValueError, lambda: pf.perfil(otro)))

    try:
        raise ValueError("x=12.345678 en el frame 4321")
    except ValueError as e:
        texto = script_partido.informe_de_error(e)
    check("el error del script del partido no lleva el mensaje", "12.345678" not in texto and "4321" not in texto
          and "ValueError" in texto, texto)
    carpeta = pp.safe_tmp()
    try:
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = script_partido.main(["--data-dir", carpeta])
        check("sin datos, el script del partido avisa y sale con 1 sin medir nada",
              codigo == 1 and "No encuentro" in salida.getvalue())
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def comprobar_script_de_punta_a_punta():
    """El script del partido con ficheros inventados de nombre neutro: lee, mide e imprime un JSON válido.

    `games.require` se sustituye para que devuelva estos ficheros: nunca se busca nada en MTAH_DATA_DIR.
    """
    print("El script del partido de punta a punta, con un ATD inventado")
    import games
    from starter import load_smart_tagging
    rng = np.random.default_rng(SEED)
    info = games.GAMES[games.GAME]
    n, slots = info["n_video_frames"], 4
    carpeta = pp.safe_tmp()
    rutas = {"atd_raw": os.path.join(carpeta, "inventado_atd.txt"),
             "atd_meta": os.path.join(carpeta, "inventado_atd.xml"),
             "smart_tagging": os.path.join(carpeta, "inventado_tagging.xml")}
    bx, by = camino(np.arange(n))
    falta = rng.random(n) < 0.4
    with open(rutas["atd_raw"], "w", newline="\n") as h:
        for f in range(n):
            jugadores = ";".join("{:.6f},{:.6f},1.0".format((bx[f] + 3 * s) / PITCH[0] % 1, by[f] / PITCH[1] % 1)
                                 for s in range(slots))
            balon = "NaN,NaN,NaN" if falta[f] else "{:.6f},{:.6f},2.0".format(bx[f] / PITCH[0], by[f] / PITCH[1])
            h.write("{}:{}:{}\n".format(f + 1, jugadores, balon))
    with open(rutas["atd_meta"], "w", newline="\n") as h:
        h.write("<Root><Teams><Team id=\"L\"><Name>Local</Name></Team><Team id=\"V\"><Name>Visitante</Name></Team>"
                "</Teams><Players>" + "".join("<Player teamId=\"{}\"/>".format("L" if s < 2 else "V")
                                              for s in range(slots)) + "</Players></Root>")
    inicios = rng.integers(12000, 189000, 30)
    with open(rutas["smart_tagging"], "w", newline="\n") as h:
        h.write("<file><ALL_INSTANCES>")
        for k, s in enumerate(inicios):
            codigo = "SET PIECES" if k % 2 == 0 else "BUILD UP"
            h.write("<instance><ID>{}</ID><start>{:.2f}</start><end>{:.2f}</end><code>{}</code>"
                    "<label><group>Team</group><text>N/A</text></label></instance>".format(k, s / 25.0, s / 25.0 + 5, codigo))
        h.write("</ALL_INSTANCES></file>")

    def requerir(nombres, game=None, data_dir=None, source=None):
        return [rutas[nombre] for nombre in nombres]

    originales = (script_partido.games.require, load_smart_tagging.require)
    script_partido.games.require = load_smart_tagging.require = requerir
    try:
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = script_partido.main([])
        datos = json.loads(salida.getvalue())
        evaluado = np.zeros(n, bool)
        for a, b in tracking.evaluated_blocks():
            evaluado[a:b] = True
        check("sale con 0 e imprime un JSON con todos los agregados", codigo == 0 and all(
            k in datos for k in ("0_control", "1_huecos_y_rachas", "3b_perdidas_por_1000_frames_con_balon",
                                 "7_jugadores", "8_set_pieces")))
        check("mide los frames evaluados del partido y los que tienen balón",
              datos["0_control"]["frames_evaluados"] == 158857
              and datos["0_control"]["frames_con_balon"] == int(np.sum(evaluado & ~falta)))
        check("toma las ventanas SET PIECES y no las demás fases", datos["8_set_pieces"]["ventanas"] == 15)
        check("no escribe nada en la carpeta de los datos", sorted(os.listdir(carpeta)) == sorted(
            os.path.basename(r) for r in rutas.values()))
    finally:
        script_partido.games.require, load_smart_tagging.require = originales
        shutil.rmtree(carpeta, ignore_errors=True)


def main():
    comprobar_huecos()
    comprobar_parado()
    comprobar_disputas_y_proximidad()
    comprobar_instrumento()
    comprobar_perdidas()
    comprobar_detecciones()
    comprobar_jugadores()
    comprobar_set_pieces()
    comprobar_supresion()
    comprobar_bordes()
    comprobar_lectura()
    comprobar_juntar()
    comprobar_guardas()
    comprobar_script_de_punta_a_punta()
    print()
    if failures:
        print("FALLAN {} comprobaciones".format(len(failures)))
        sys.exit(1)
    print("TODO BIEN")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
