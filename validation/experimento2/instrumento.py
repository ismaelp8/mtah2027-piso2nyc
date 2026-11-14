"""Experimento 2: medir con el tracking qué convención siguen unas etiquetas de posesión.

El mismo instrumento se aplica a dos cosas:

- a la DFL (datos abiertos de otros partidos), con etiquetas cuya convención conocemos: el flag tal cual
  (último toque, lectura 1) y el flag corregido con "C0-12 o dos toques" (control, lectura 3). Así se ve
  qué "huella" deja cada convención y si el instrumento la distingue con un balón tan malo como el del
  ATD (`calibrar_dfl.py`, lo ejecuta Claude);
- a la ventana pública del partido, con el ATD y la GT pública (`validation/partido/recuento_ventana.py`,
  solo lo ejecuta una persona).

No se inventa ninguna medida: son las del experimento 0 (`validation/experimento0/medidas_cambios.py`)
con sus mismos umbrales. Lo único nuevo es que los toques se buscan por tramos de balón visible, porque
`medidas_cambios.toques` acumula velocidades con `cumsum` y un solo frame sin balón la deja sin toques
el resto de la parte. En los bordes de un hueco no se busca toque: ni se interpola ni se inventa.

Criterios fijados antes de medir en `validation/experimento2/BITACORA.md`. Funciones puras de numpy;
todo lo que devuelven son recuentos y porcentajes.
"""

import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
import medidas_cambios as mc  # noqa: E402

FPS = 25
PRM = {
    # toque y control: los del experimento 0, sin cambiar
    "umbral_toque": 3.0,  # m/s de cambio de velocidad del balón
    "radio_toque": 1.5,  # m al jugador más cercano para atribuir el toque a su equipo
    "radio": 1.0,  # m: control de equipo (retención)
    "frames_control": 12,  # Ret-12: el más cercano es del mismo equipo, a 1 m o menos, 12 frames
    "min_tramo": 10,  # frames de balón visible seguidos para buscar toques en ellos
    # cómo se clasifica cada cambio (protocolo de Antonio, sección 17 de la bitácora del experimento 1)
    "ventana": 50,  # ±2 s alrededor del cambio
    "tolerancia": 5,  # ±5 frames
    "poco_despues": 25,  # hasta 1 s después del toque
    "cobertura": 25,  # ±1 s para decir si hay balón alrededor del cambio
    "corta": 75,  # posesión corta: menos de 3 s
    # cómo pierde el balón el tracking (solo tracking, sin etiquetas)
    "radio_disputa": 3.0,  # m: disputa = un jugador de cada equipo a esta distancia del balón o menos
}
CLASES_FECHA = ("antes del toque", "en el toque", "poco después", "más tarde", "sin toque visible")
CLASES_CONTROL = ("antes del control", "en el inicio del control", "6-15 frames después del inicio",
                  "más de 15 después del inicio", "sin control")
CLASES_CORTAS = ("control", "solo toque", "sin balón", "nada")


# -- preparación -------------------------------------------------------------------------------------

def preparar_en_juego(parte, estado):
    """`medidas_cambios.preparar` con las distancias tapadas fuera del juego, como en el experimento 1."""
    prep = dict(mc.preparar(parte))
    activo = np.asarray(estado) == 1
    prep["d1"] = np.where(activo, prep["d1"], np.inf)
    prep["d_equipo"] = np.where(activo[None, :], prep["d_equipo"], np.inf)
    return prep


def toques_por_tramos(prep, umbral, radio, minimo):
    """`medidas_cambios.toques` en cada tramo de balón visible de `minimo` frames o más.

    Sin huecos da lo mismo que `medidas_cambios.toques` (lo comprueba `pruebas_sinteticas.py`).
    """
    visible = (np.isfinite(prep["x"]) & np.isfinite(prep["y"])).astype(int)
    ts, eqs, dvs = [], [], []
    for a, b, v in mc.rachas(visible, minimo):
        if v != 1:
            continue
        vx, vy = np.array(prep["vx"][a:b], float), np.array(prep["vy"][a:b], float)
        vx[0], vy[0] = vx[1], vy[1]  # el primero es la diferencia con un frame sin balón
        sub = {"n": b - a, "vx": vx, "vy": vy, "d1": prep["d1"][a:b], "equipo_cercano": prep["equipo_cercano"][a:b]}
        t, eq, dv = mc.toques(sub, umbral, radio)
        ts.append(t + a)
        eqs.append(eq)
        dvs.append(dv)
    if not ts:
        return np.array([], int), np.array([], int), np.array([])
    return np.concatenate(ts).astype(int), np.concatenate(eqs).astype(int), np.concatenate(dvs)


def temblor(x, y, activo):
    """Mediana (m) de |x[t+1] − 2·x[t] + x[t−1]| del balón en frames de juego con los tres frames visibles."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3:
        return None
    ok = np.isfinite(x[:-2]) & np.isfinite(x[1:-1]) & np.isfinite(x[2:]) & np.asarray(activo)[1:-1]
    if not np.any(ok):
        return None
    d2 = np.hypot(x[2:] - 2 * x[1:-1] + x[:-2], y[2:] - 2 * y[1:-1] + y[:-2])
    return float(np.median(d2[ok]))


# -- clasificación de cada cambio --------------------------------------------------------------------

def fecha_cambio(f, nuevo, viejo, t, eq, prm=PRM):
    """(clase, T): cuándo cambia la etiqueta respecto al primer toque del equipo nuevo.

    T es el primer toque del equipo nuevo después del último toque del equipo anterior que no pasa de f,
    buscando en f ± ventana. Δ = f − T, con las clases del protocolo de la sección 17.
    """
    w, tol = prm["ventana"], prm["tolerancia"]
    sel = (t >= f - w) & (t <= f + w)
    tt, ee = t[sel], eq[sel]
    viejos = tt[(ee == viejo) & (tt <= f)]
    desde = viejos[-1] if len(viejos) else f - w - 1
    nuevos = tt[(ee == nuevo) & (tt > desde)]
    if not len(nuevos):
        return "sin toque visible", None
    T = int(nuevos[0])
    d = f - T
    if d < -tol:
        return "antes del toque", T
    if d <= tol:
        return "en el toque", T
    if d <= prm["poco_despues"]:
        return "poco después", T
    return "más tarde", T


def control_cambio(f, nuevo, T, inicios_por_equipo, prm=PRM):
    """Cuándo cambia la etiqueta respecto al inicio del primer control (Ret-12) del equipo nuevo."""
    w, tol = prm["ventana"], prm["tolerancia"]
    desde = (T - tol) if T is not None else f - w
    ini = inicios_por_equipo[int(nuevo)]
    c = ini[(ini >= desde) & (ini <= f + w)]
    if not len(c):
        return "sin control"
    d = f - int(c[0])
    if d < -tol:
        return "antes del control"
    if d <= tol:
        return "en el inicio del control"
    if d <= 15:
        return "6-15 frames después del inicio"
    return "más de 15 después del inicio"


def toques_sueltos(t, eq, lab, inicios, propio=False, prm=PRM):
    """Pregunta 3 con más casos: toques del rival sin control después y si la etiqueta pasa a él.

    Un toque del equipo y en t cuenta si:
    - la etiqueta marca al otro equipo x tres frames antes, y el balón está vivo de t − 5 a t + 50;
    - abre episodio: el toque anterior con equipo no es de y a 25 frames o menos;
    - y no tiene control después: ni un Ret-12 suyo que empiece de t − 5 a t + 50, ni su siguiente toque
      (sin uno de x en medio) a 50 frames o menos, que sería "dos toques".

    `cambia`: la etiqueta marca y en algún frame de t a t + 25. Con `propio=True` es el placebo: toques
    sueltos del equipo que tiene la etiqueta, y si pasa al otro en ese tiempo. Devuelve una lista de bools.
    """
    sel = np.flatnonzero(np.asarray(eq) >= 0)
    t, eq = np.asarray(t)[sel], np.asarray(eq)[sel]
    n, w = len(lab), prm["ventana"]
    salida = []
    for i in range(len(t)):
        ti, y = int(t[i]), int(eq[i])
        if ti - 5 < 0 or ti + w >= n or np.any(lab[ti - 5:ti + w + 1] == 2):
            continue
        x = int(lab[ti - 3])
        if (x == y) != propio:
            continue
        if i > 0 and eq[i - 1] == y and ti - t[i - 1] <= 25:
            continue
        if i + 1 < len(t) and eq[i + 1] == y and t[i + 1] - ti <= w:
            continue
        ini = inicios[y]
        if np.any((ini >= ti - prm["tolerancia"]) & (ini <= ti + w)):
            continue
        otro = 1 - x
        salida.append(bool(np.any(lab[ti:ti + prm["poco_despues"] + 1] == (otro if propio else y))))
    return salida


def cortas_intercaladas(lab, rets, t, eq, visible, prm=PRM):
    """Clase de cada posesión corta X → y → X (y de menos de `corta` frames, todo con balón vivo)."""
    por_equipo = mc._por_equipo(rets)
    runs = mc.rachas(lab, 1)
    salida = []
    for i in range(1, len(runs) - 1):
        a, b, v = runs[i]
        pv, sv = runs[i - 1][2], runs[i + 1][2]
        if v == 2 or pv == 2 or sv == 2 or pv != sv or b - a >= prm["corta"]:
            continue
        if mc._solapa(por_equipo[v], a, b):
            salida.append("control")
        elif np.any((t >= a - prm["tolerancia"]) & (t < b) & (eq == v)):
            salida.append("solo toque")
        elif visible[a:b].mean() < 0.5:
            salida.append("sin balón")
        else:
            salida.append("nada")
    return salida


# -- el instrumento ----------------------------------------------------------------------------------

def medir(prep, estado, poss, prm=PRM):
    """Todos los agregados del instrumento para unas etiquetas (`estado` 1 = vivo; `poss` 1/2 = equipo 0/1).

    Devuelve solo recuentos: nada por frame ni por jugada.
    """
    estado, poss = np.asarray(estado), np.asarray(poss)
    n = len(estado)
    activo = estado == 1
    visible = np.isfinite(prep["x"]) & np.isfinite(prep["y"])
    t, eq, _ = toques_por_tramos(prep, prm["umbral_toque"], prm["radio_toque"], prm["min_tramo"])
    t, eq = mc.toques_en_juego(t, eq, estado)
    rets = mc.retenciones(prep, prm["radio"], prm["frames_control"])
    inicios = {k: np.array([s[0] for s in rets if s[2] == k], int) for k in (0, 1)}
    lab = np.where(activo, poss - 1, 2).astype(int)

    disputa = (prep["d_equipo"][0] <= prm["radio_disputa"]) & (prep["d_equipo"][1] <= prm["radio_disputa"])
    r = {"frames_vivos": int(activo.sum()),
         "frames_vivos_con_balon": int(np.sum(visible & activo)),
         "frames_vivos_con_balon_en_disputa": int(np.sum(visible & activo & disputa)),
         "toques_con_equipo": int(np.sum(eq >= 0)),
         "controles_ret12": len([s for s in rets if activo[s[0]]]),
         "temblor_balon_mediana_m": temblor(prep["x"], prep["y"], activo)}

    # pregunta 2: los cambios directos H↔A
    f, nuevo, viejo = mc.cambios(estado, poss)
    fechas, controles = collections.Counter(), collections.Counter()
    con_balon = 0
    for fi, y_eq, x_eq in zip(f, nuevo, viejo):
        clase, T = fecha_cambio(int(fi), int(y_eq), int(x_eq), t, eq, prm)
        fechas[clase] += 1
        controles[control_cambio(int(fi), int(y_eq), T, inicios, prm)] += 1
        a, b = max(0, fi - prm["cobertura"]), min(n, fi + prm["cobertura"] + 1)
        con_balon += int(visible[a:b].mean() >= 0.5)
    r["cambios_directos"] = int(len(f))
    r["cambios_con_balon_visible_la_mitad_de_±1s"] = con_balon
    r["fecha_respecto_al_toque"] = {c: fechas[c] for c in CLASES_FECHA}
    r["fecha_respecto_al_control"] = {c: controles[c] for c in CLASES_CONTROL}

    # pregunta 1: posesiones cortas entre dos del rival
    cortas = collections.Counter(cortas_intercaladas(lab, rets, t, eq, visible, prm))
    r["cortas_intercaladas"] = {c: cortas[c] for c in CLASES_CORTAS}

    # pregunta 3: toques del rival sin control entre dos controles del mismo equipo (2g del experimento 0)
    z = np.asarray(prep.get("z", np.zeros(n)), float)
    casos = mc.toques_sin_control(t, eq, rets, estado, poss, z)
    plac = mc.toques_sin_control(t, eq, rets, estado, poss, z, propio=True)
    h, hp = mc.por_hueco(casos), mc.por_hueco(plac)
    r["toques_rival_sin_control"] = {"toques": len(casos), "toques_que_cambian": int(sum(c["cambia"] for c in casos)),
                                     "huecos": len(h), "huecos_que_cambian": int(sum(h))}
    r["placebo_toques_propios"] = {"toques": len(plac), "toques_que_cambian": int(sum(c["cambia"] for c in plac)),
                                   "huecos": len(hp), "huecos_que_cambian": int(sum(hp))}

    # pregunta 3 con más casos: toques sueltos del rival, sin control después
    sueltos = toques_sueltos(t, eq, lab, inicios, False, prm)
    sueltos_pl = toques_sueltos(t, eq, lab, inicios, True, prm)
    r["toques_sueltos_rival"] = {"episodios": len(sueltos), "cambian": int(sum(sueltos))}
    r["placebo_toques_sueltos_propios"] = {"episodios": len(sueltos_pl), "cambian": int(sum(sueltos_pl))}
    return r


def sumar(resultados):
    """Suma los recuentos de varios `medir` (los porcentajes y medianas se rehacen fuera)."""
    total = {}
    for r in resultados:
        for k, v in r.items():
            if isinstance(v, dict):
                d = total.setdefault(k, {})
                for k2, v2 in v.items():
                    d[k2] = d.get(k2, 0) + v2
            elif k == "temblor_balon_mediana_m":
                total.setdefault("temblores", []).append(v)
            else:
                total[k] = total.get(k, 0) + v
    temblores = [v for v in total.pop("temblores", []) if v is not None]
    total["temblor_balon_mediana_m"] = float(np.median(temblores)) if temblores else None
    return total


def tasas(r):
    """Proporciones legibles de un resultado (o de una suma)."""
    def p(a, b):
        return round(a / b, 2) if b else None
    q3, pl = r["toques_rival_sin_control"], r["placebo_toques_propios"]
    con_toque = sum(v for k, v in r["fecha_respecto_al_toque"].items() if k != "sin toque visible")
    minutos = r["frames_vivos"] / FPS / 60.0
    return {
        "balon_visible_en_juego_pct": round(100.0 * r["frames_vivos_con_balon"] / r["frames_vivos"], 1)
        if r["frames_vivos"] else None,
        "disputa_entre_frames_con_balon_pct": round(100.0 * r["frames_vivos_con_balon_en_disputa"]
                                                    / r["frames_vivos_con_balon"], 1)
        if r["frames_vivos_con_balon"] else None,
        "temblor_balon_mediana_cm": round(100.0 * r["temblor_balon_mediana_m"], 1)
        if r["temblor_balon_mediana_m"] is not None else None,
        "toques_con_equipo_por_minuto_vivo": round(r["toques_con_equipo"] / minutos, 1) if minutos else None,
        "controles_ret12_por_minuto_vivo": round(r["controles_ret12"] / minutos, 1) if minutos else None,
        "cortas_intercaladas_por_minuto_vivo": round(sum(r["cortas_intercaladas"].values()) / minutos, 2)
        if minutos else None,
        "huecos_rival_que_cambian": p(q3["huecos_que_cambian"], q3["huecos"]),
        "huecos_placebo_que_cambian": p(pl["huecos_que_cambian"], pl["huecos"]),
        "sueltos_rival_que_cambian": p(r["toques_sueltos_rival"]["cambian"], r["toques_sueltos_rival"]["episodios"]),
        "sueltos_placebo_que_cambian": p(r["placebo_toques_sueltos_propios"]["cambian"],
                                         r["placebo_toques_sueltos_propios"]["episodios"]),
        "sueltos_rival_por_minuto_vivo": round(r["toques_sueltos_rival"]["episodios"] / minutos, 2) if minutos else None,
        "cambios_con_toque_visible": p(con_toque, r["cambios_directos"]),
        "en_el_toque_de_los_que_tienen_toque": p(r["fecha_respecto_al_toque"]["en el toque"], con_toque),
        "poco_despues_o_mas_tarde_de_los_que_tienen_toque":
            p(r["fecha_respecto_al_toque"]["poco después"] + r["fecha_respecto_al_toque"]["más tarde"], con_toque),
    }


# -- degradación de la DFL para que se parezca al ATD (solo calibración) ------------------------------

def mascara_bloques(n, activo, objetivo, media, rng, base=None):
    """Tapa bloques de longitud geométrica (media `media` frames) hasta tapar `objetivo` de los frames vivos."""
    m = np.zeros(n, bool) if base is None else base.copy()
    vivos = max(1, int(np.sum(activo)))
    tapados = int(np.sum(m & activo))
    while tapados < objetivo * vivos:
        s = int(rng.integers(0, n))
        L = int(rng.geometric(1.0 / media))
        nuevo = ~m[s:s + L]
        tapados += int(np.sum(nuevo & activo[s:s + L]))
        m[s:s + L] = True
    return m


def mascara_dirigida(prep_limpio, z, activo, objetivo, rng, fraccion=1.0, radio=3.0, aire=1.5, dilatar=5, media=25):
    """Tapa disputas (los dos equipos a `radio` m o menos) y balones altos, ±`dilatar` frames; si no llega a
    `objetivo`, completa con bloques al azar. Con `fraccion` < 1 solo tapa esa fracción de los episodios,
    elegidos al azar. Devuelve (máscara, % vivo tapado solo por la parte dirigida)."""
    d = prep_limpio["d_equipo"]
    m = ((d[0] <= radio) & (d[1] <= radio)) | (np.asarray(z, float) > aire)
    m = np.convolve(m.astype(int), np.ones(2 * dilatar + 1, int), mode="same") > 0
    if fraccion < 1.0:
        episodios = [(a, b) for a, b, v in mc.rachas(m.astype(int), 1) if v == 1]
        elegidos = rng.random(len(episodios)) < fraccion
        m = np.zeros(len(m), bool)
        for (a, b), e in zip(episodios, elegidos):
            m[a:b] = e
    dirigida = 100.0 * float(np.mean(m[activo])) if np.any(activo) else 0.0
    return mascara_bloques(len(m), activo, objetivo, media, rng, base=m), round(dirigida, 1)


def degradar(parte, mascara, sigma_balon, rng):
    """Copia de la parte con el balón tapado en `mascara` y ruido gaussiano (balón σ, jugadores σ/2)."""
    nueva = dict(parte)
    x, y = np.array(parte["x"], float), np.array(parte["y"], float)
    if sigma_balon:
        x += rng.normal(0.0, sigma_balon, len(x))
        y += rng.normal(0.0, sigma_balon, len(y))
    x[mascara], y[mascara] = np.nan, np.nan
    nueva["x"], nueva["y"] = x, y
    nueva["z"] = np.array(parte.get("z", np.zeros(len(x))), float)
    equipos = {}
    for k, v in parte["equipos"].items():
        ex, ey = np.array(v["x"], float), np.array(v["y"], float)
        if sigma_balon:
            ex += rng.normal(0.0, sigma_balon / 2, ex.shape)
            ey += rng.normal(0.0, sigma_balon / 2, ey.shape)
        equipos[k] = {"x": ex, "y": ey}
    nueva["equipos"] = equipos
    return nueva
