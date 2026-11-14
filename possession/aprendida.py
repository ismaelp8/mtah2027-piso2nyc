"""Evidencia de equipo aprendida (apuesta B): regresión logística de `H` frente a `A`.

Es la apuesta B del plan (docs/PLAN_ENTREGA.md §3, «Ismael»; docs/investigacion_metodos.md §4.2), con las
decisiones de Ismael del 14/11 (docs/decisiones.md): una evidencia de equipo aprendida en la DFL que
compite con N1 (`candidates.evidence`) en el harness. **No va en la entrega** salvo que gane con la regla
de §5.8 al control y a `main`.

- **Solo `H` frente a `A`.** La columna `D` va a cero, como en N1: el `D` es de `dead_state` y `dead_ball`.
- **Simétrica por construcción:** cada rasgo es «lo del local menos lo del visitante» y el modelo no tiene
  término independiente. Cambiar los equipos de lado cambia el signo del logit y nada más.
- **Sin identidad:** los rasgos no dependen del orden de los slots. Solo las velocidades de B2 suponen que
  un slot es el mismo objeto entre un frame y el siguiente (un tracklet); los saltos de más de `VEL_MAX`,
  que son cambios de slot, se descartan.
- **Por tramo evaluado:** ninguna ventana cruza el descanso. Fuera de los tramos, la puntuación es cero.
- **La puntuación:** α·z a favor del equipo que el modelo da como poseedor (z es el logit) y cero para el
  otro y para `D`, redondeada a `DECIMALES`. El logit se suma rasgo a rasgo, sin BLAS. El redondeo hace
  improbable, no imposible, que la entrega dependa del último bit de `np.exp` en otra máquina: la garantía
  es reproducir el CSV byte a byte en una máquina limpia.

Los coeficientes los escribe `validation/apuesta_b/entrenar.py` (numpy, sin azar) al final de este fichero.
Hay un juego por pliegue: el que se entrenó sin cada partido de la DFL, para que el harness puntúe cada
partido con un modelo que no lo vio (`fuera`), y el de los 7 partidos (`fuera=None`), que es el de la
entrega.

Interfaz: `evidence_b1(trk)` y `evidence_b2(trk)` devuelven `(score, allowed)`; ver possession/tracking.py.
"""

import numpy as np

from possession.tracking import A, H, no_evidence

# -- rasgos (fijados en docs/decisiones.md el 14/11, antes de medir; sin ajustar) -----------------------
# Ninguna de estas constantes se ajustó: se escribieron antes de medir y no se tocaron al ver resultados.

SIGMAS = (1.0, 2.5, 6.0)  # m: anchura de los núcleos gaussianos de distancia al balón
TOPE = 15.0  # m: tope de la distancia del más cercano de cada equipo
VENTANAS_BALON = (1, 13, 51, 151)  # frames: ventanas centradas de los rasgos del balón
VEL_MAX = 12.0  # m/s: una velocidad mayor es un cambio de slot, no un jugador
VENTANA_CERCA = 25  # frames: «sin balón cerca» es ningún frame con balón en ±12
DECIMALES = 6
CONJUNTOS = ("b1", "b2")
BASE_BALON = ["signo del más cercano"] + ["núcleo {} m".format(s) for s in SIGMAS] + ["distancia del más cercano"]
NOMBRES = {
    "b1": ["{}, ventana {}".format(r, v) for r in BASE_BALON for v in VENTANAS_BALON],
}
NOMBRES["b2"] = NOMBRES["b1"] + [
    "juego en la dirección de ataque",
    "balón en la dirección de ataque, ventana 1",
    "balón en la dirección de ataque, ventana 51",
    "velocidad en la dirección de ataque, ventana 25",
    "velocidad en la dirección de ataque, ventana 101",
    "dispersión, ventana 51",
    "juego en la dirección de ataque, sin balón cerca",
    "velocidad en la dirección de ataque, ventana 25, sin balón cerca",
    "velocidad en la dirección de ataque, ventana 101, sin balón cerca",
    "dispersión, ventana 51, sin balón cerca",
]


def media_centrada(valores, ancho):
    """Media centrada de `ancho` frames (impar), recortada en los extremos. Los NaN cuentan como cero."""
    v = np.where(np.isnan(valores), 0.0, np.asarray(valores, dtype=np.float64))
    if ancho == 1:
        return v
    acumulada = np.concatenate(([0.0], np.cumsum(v)))
    indice = np.arange(len(v))
    bajo = np.maximum(0, indice - ancho // 2)
    alto = np.minimum(len(v), indice + ancho // 2 + 1)
    return (acumulada[alto] - acumulada[bajo]) / (alto - bajo)


def _sin_nan(valores):
    return np.where(np.isfinite(valores), valores, 0.0)


def _por_equipo(px, py, columnas):
    """Posiciones de un equipo en float64 y la máscara de las que existen."""
    x = px[:, columnas].astype(np.float64)
    y = py[:, columnas].astype(np.float64)
    return x, y, np.isfinite(x) & np.isfinite(y)


def _media_filas(valores, hay):
    """Media por fila de lo que hay; NaN si no hay nada."""
    cuenta = hay.sum(axis=1)
    suma = np.where(hay, valores, 0.0).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cuenta > 0, suma / np.maximum(cuenta, 1), np.nan)


def _rasgos_balon(bx, by, equipos):
    """Los 5 rasgos base del balón (local menos visitante), a cero sin balón."""
    visible = np.isfinite(bx) & np.isfinite(by)
    cerca, nucleos = [], []
    for x, y, hay in equipos:
        d2 = (x - bx[:, None]) ** 2 + (y - by[:, None]) ** 2
        d2 = np.where(hay & visible[:, None], d2, np.inf)
        minimo = d2.min(axis=1) if d2.shape[1] else np.full(len(bx), np.inf)
        cerca.append(np.sqrt(minimo))
        nucleos.append([np.exp(-d2 / (2.0 * s * s)).sum(axis=1) for s in SIGMAS])
    with np.errstate(invalid="ignore"):
        signo = _sin_nan(np.sign(cerca[1] - cerca[0]))
    base = [signo] + [nucleos[0][i] - nucleos[1][i] for i in range(len(SIGMAS))]
    base.append(np.minimum(cerca[1], TOPE) - np.minimum(cerca[0], TOPE))
    return [np.where(visible, r, 0.0) for r in base], visible


def _velocidad_x(x, y, fps):
    """Velocidad en x de cada slot (diferencia centrada), NaN si falta o si pasa de VEL_MAX."""
    vx = np.full(x.shape, np.nan)
    if len(x) < 3:
        return vx
    dx = (x[2:] - x[:-2]) * fps / 2.0
    dy = (y[2:] - y[:-2]) * fps / 2.0
    with np.errstate(invalid="ignore"):
        rapido = np.hypot(dx, dy) > VEL_MAX
    vx[1:-1] = np.where(rapido, np.nan, dx)
    return vx


def _dispersion(x, y, hay):
    """Raíz de la varianza en x más la varianza en y del equipo; NaN con menos de dos slots."""
    mx, my = _media_filas(x, hay), _media_filas(y, hay)
    var = _media_filas((x - mx[:, None]) ** 2 + (y - my[:, None]) ** 2, hay)
    return np.where(hay.sum(axis=1) >= 2, np.sqrt(var), np.nan)


def _rasgos_forma(bx, by, visible, equipos, largo, fps):
    """Los 10 rasgos de los jugadores de B2, con la dirección de ataque del local en el tramo."""
    (xh, yh, hh), (xa, ya, ha) = equipos
    media_h = np.where(hh, xh, 0.0).sum() / max(int(hh.sum()), 1)
    media_a = np.where(ha, xa, 0.0).sum() / max(int(ha.sum()), 1)
    # El local ataca hacia donde está, en media, el visitante. Sin uno de los dos, no hay dirección.
    direccion = float(np.sign(media_a - media_h)) if hh.any() and ha.any() else 0.0
    mitad = largo / 2.0
    juego = direccion * _sin_nan(_media_filas(xh, hh) + _media_filas(xa, ha) - largo) / mitad
    balon = np.where(visible, direccion * (np.where(visible, bx, mitad) - mitad) / mitad, 0.0)
    vh, va = _velocidad_x(xh, yh, fps), _velocidad_x(xa, ya, fps)
    vel = direccion * (_sin_nan(_media_filas(vh, np.isfinite(vh))) + _sin_nan(_media_filas(va, np.isfinite(va))))
    dispersion = _sin_nan(_dispersion(xh, yh, hh) - _dispersion(xa, ya, ha))
    sin_balon = media_centrada(visible.astype(np.float64), VENTANA_CERCA) == 0.0
    forma = [juego, media_centrada(balon, 1), media_centrada(balon, 51), media_centrada(vel, 25),
             media_centrada(vel, 101), media_centrada(dispersion, 51)]
    return forma + [np.where(sin_balon, r, 0.0) for r in (forma[0], forma[3], forma[4], forma[5])]


def rasgos(trk, conjunto):
    """Matriz (n, k) de rasgos del conjunto (`NOMBRES[conjunto]`), en float64, a cero fuera de los tramos."""
    if conjunto not in CONJUNTOS:
        raise ValueError("conjunto desconocido: {} (valen: {})".format(conjunto, CONJUNTOS))
    n = len(trk.bx)
    salida = np.zeros((n, len(NOMBRES[conjunto])))
    team = np.asarray(trk.team)
    columnas = [np.flatnonzero(team == equipo) for equipo in (H, A)]
    for inicio, fin in trk.blocks:
        bx = np.asarray(trk.bx[inicio:fin], dtype=np.float64)
        by = np.asarray(trk.by[inicio:fin], dtype=np.float64)
        equipos = [_por_equipo(trk.px[inicio:fin], trk.py[inicio:fin], c) for c in columnas]
        base, visible = _rasgos_balon(bx, by, equipos)
        lista = [media_centrada(r, v) for r in base for v in VENTANAS_BALON]
        if conjunto == "b2":
            lista += _rasgos_forma(bx, by, visible, equipos, float(trk.pitch[0]), float(trk.fps))
        salida[inicio:fin] = np.column_stack(lista)
    return salida


def logit(matriz, pesos):
    """z = Σ peso·rasgo, sumando en el orden de los rasgos (sin BLAS, para que no dependa de la máquina)."""
    if matriz.shape[1] != len(pesos):
        raise ValueError("{} rasgos y {} pesos".format(matriz.shape[1], len(pesos)))
    z = np.zeros(len(matriz))
    for j, peso in enumerate(pesos):
        z = z + float(peso) * matriz[:, j]
    return z


def puntuacion(z, alfa):
    """(score, allowed) a partir del logit: α·z a favor del poseedor, cero para el otro y para `D`."""
    score, allowed = no_evidence(len(z))
    score[:, H] = np.round(alfa * np.maximum(z, 0.0), DECIMALES)
    score[:, A] = np.round(alfa * np.maximum(-z, 0.0), DECIMALES)
    return score, allowed


def coeficientes(conjunto, fuera=None):
    """{"alfa", "pesos"} del conjunto: los de los 7 partidos, o los del pliegue sin el partido `fuera`."""
    clave = "todos" if fuera is None else fuera
    juego = COEFICIENTES.get(conjunto, {}).get(clave)
    if juego is None:
        raise KeyError("no hay coeficientes de «{}» para «{}»: hay que ejecutar "
                       "validation/apuesta_b/entrenar.py".format(conjunto, clave))
    return juego


def _evidencia(trk, conjunto, fuera):
    juego = coeficientes(conjunto, fuera)
    return puntuacion(logit(rasgos(trk, conjunto), juego["pesos"]), juego["alfa"])


def evidence_b1(trk, fuera=None):
    """B1: proximidad al balón aprendida. `fuera`: el partido de la DFL que el harness está puntuando."""
    return _evidencia(trk, "b1", fuera)


def evidence_b2(trk, fuera=None):
    """B2: B1 más rasgos de los jugadores, que opinan también sin balón."""
    return _evidencia(trk, "b2", fuera)


# -- coeficientes: los escribe validation/apuesta_b/entrenar.py; no se editan a mano --------------------
# >>> COEFICIENTES
# Los escribe validation/apuesta_b/entrenar.py. «todos»: los 7 partidos de la DFL (la entrega); cada
# partido: el pliegue entrenado y escalado sin él (el harness, con «dejar_fuera»).
COEFICIENTES = {
    "b1": {
        "todos": {"alfa": 2.0, "pesos": (
            0.015849, 0.0396237, -0.118552, 0.844238, -0.0370134,
            0.96778, 1.62156, 3.26677, 0.105757, -0.737179,
            1.13013, 2.74527, -0.0178349, 0.548347, -1.13124,
            -2.2605, -0.0240528, 0.0037239, -0.082326, 0.411018,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.00844998, 0.0310774, -0.113953, 1.15379, -0.0325204,
            0.985406, 1.47035, 2.67844, 0.0592573, -0.663211,
            1.11673, 2.84984, 0.0229323, 0.436025, -0.984654,
            -2.36922, -0.0265686, 0.0136749, -0.0930549, 0.395963,
        )},
        "J03WN1": {"alfa": 2.0, "pesos": (
            0.0131502, 0.0521605, -0.0976352, 0.450504, -0.0075356,
            0.90215, 1.70962, 4.14516, 0.107093, -0.752027,
            1.01543, 3.14196, 0.0356043, 0.496342, -1.06615,
            -2.44771, -0.0269637, 0.00454526, -0.0790139, 0.416897,
        )},
        "J03WOH": {"alfa": 2.0, "pesos": (
            0.00878288, 0.0614111, -0.138145, 1.03055, -0.0428085,
            0.984227, 1.62408, 2.92447, 0.0913831, -0.734043,
            1.11807, 2.81329, 0.0101609, 0.482388, -1.08748,
            -2.36218, -0.0273109, 0.00970331, -0.0847348, 0.397339,
        )},
        "J03WOY": {"alfa": 2.0, "pesos": (
            0.0157976, 0.0457948, -0.138855, 0.747598, -0.0583174,
            0.985892, 1.71437, 3.94571, 0.0863745, -0.710772,
            1.0457, 2.32384, -0.0459378, 0.618217, -1.20773,
            -2.16476, -0.0202434, -0.00781757, -0.0689492, 0.432034,
        )},
        "J03WPY": {"alfa": 2.0, "pesos": (
            0.0260962, 0.0244347, -0.0947872, 0.744362, -0.0390545,
            0.953369, 1.63629, 3.30893, 0.138883, -0.782632,
            1.28075, 2.46505, -0.0618356, 0.608351, -1.25878,
            -2.02164, -0.0274402, 0.0116027, -0.0970543, 0.421578,
        )},
        "J03WQQ": {"alfa": 2.0, "pesos": (
            0.00623527, 0.0538441, -0.1316, 0.818469, -0.0386886,
            0.983016, 1.74966, 2.68606, 0.091564, -0.712675,
            1.08935, 2.97413, -0.0156813, 0.555053, -1.0981,
            -2.2957, -0.0108921, -0.0147692, -0.0805567, 0.42094,
        )},
        "J03WR9": {"alfa": 2.0, "pesos": (
            0.0316531, 0.0108566, -0.121972, 0.936823, -0.0262062,
            0.963132, 1.45734, 3.33704, 0.122235, -0.745133,
            1.2221, 2.63997, -0.0422083, 0.606997, -1.21307,
            -2.15841, -0.0271379, 0.00538057, -0.0677795, 0.390551,
        )},
    },
    "b2": {
        "todos": {"alfa": 2.0, "pesos": (
            0.0375125, 0.0020608, -0.034728, 1.44394, -0.0946537,
            1.13776, 1.04194, 2.63023, 0.089502, -0.670045,
            1.52721, 0.707258, 0.0652266, 0.307699, -0.81681,
            -0.324124, -0.0252869, -0.0192872, -0.107059, 0.0476549,
            1.20284, 0.274543, -4.15035, 0.451477, -0.0199163,
            0.264126, -4.44177, -0.29112, 0.15269, 0.330578,
        )},
        "J03WMX": {"alfa": 2.0, "pesos": (
            0.0306064, -0.0132135, -0.0363003, 1.8232, -0.0641295,
            1.10994, 0.936099, 1.90953, 0.0458039, -0.585642,
            1.53234, 0.804738, 0.106398, 0.199702, -0.673065,
            -0.444768, -0.0376022, 0.00247349, -0.120856, 0.0288019,
            1.27987, 0.206883, -4.10402, 0.455597, -0.0203781,
            0.260675, -4.17706, -0.309728, 0.16441, 0.307329,
        )},
        "J03WN1": {"alfa": 2.0, "pesos": (
            0.0391198, 0.0187248, -0.0289436, 0.958647, -0.0799917,
            1.1096, 1.11257, 3.72668, 0.0268155, -0.599567,
            1.41384, 1.00614, 0.176867, 0.160735, -0.722547,
            -0.529223, -0.0218076, -0.0299679, -0.0966192, 0.0442844,
            0.989736, 0.378259, -4.3254, 0.431773, -0.00576854,
            0.287203, -4.70049, -0.243125, 0.115645, 0.361429,
        )},
        "J03WOH": {"alfa": 2.0, "pesos": (
            0.0328053, 0.018972, -0.0417908, 1.67521, -0.100255,
            1.16293, 1.00428, 2.08624, 0.0589483, -0.644623,
            1.54583, 0.833648, -0.0108504, 0.367805, -0.839527,
            -0.352537, -0.0198761, -0.023367, -0.111479, 0.0375936,
            1.27324, 0.259194, -4.07429, 0.43984, -0.00712229,
            0.26294, -4.28517, -0.321361, 0.186251, 0.320223,
        )},
        "J03WOY": {"alfa": 2.0, "pesos": (
            0.0402686, 0.000490481, -0.0330194, 1.30555, -0.108522,
            1.14414, 1.06745, 3.25309, 0.0834922, -0.658029,
            1.3938, 0.555298, 0.020055, 0.400167, -0.903382,
            -0.270938, -0.0320217, -0.0160338, -0.0903902, 0.0617012,
            1.2415, 0.243983, -4.03703, 0.458586, -0.0463463,
            0.252876, -4.55296, -0.220501, 0.0775531, 0.342635,
        )},
        "J03WPY": {"alfa": 2.0, "pesos": (
            0.0418441, -0.00453044, -0.0369182, 1.34945, -0.10494,
            1.12952, 1.04305, 3.06005, 0.129654, -0.716623,
            1.73741, 0.250132, 0.0259182, 0.372111, -0.941517,
            -0.051487, -0.0267058, -0.0158839, -0.124915, 0.0476765,
            1.20488, 0.303368, -4.24285, 0.477104, -0.04729,
            0.267426, -4.53381, -0.319138, 0.192047, 0.320392,
        )},
        "J03WQQ": {"alfa": 2.0, "pesos": (
            0.0230818, 0.0245812, -0.0307349, 1.45329, -0.101606,
            1.14875, 1.21742, 1.93066, 0.0947507, -0.678838,
            1.40736, 0.898022, 0.0978462, 0.278064, -0.7785,
            -0.308609, -0.0119348, -0.0369917, -0.101012, 0.0557967,
            1.22534, 0.270801, -4.16733, 0.439929, 0.00965233,
            0.258966, -4.2923, -0.344712, 0.197429, 0.32487,
        )},
        "J03WR9": {"alfa": 2.0, "pesos": (
            0.0529509, -0.0286386, -0.0377898, 1.50243, -0.0814839,
            1.12967, 0.951319, 2.59616, 0.12796, -0.716306,
            1.60295, 0.615601, 0.0597802, 0.331595, -0.826551,
            -0.313793, -0.0248903, -0.0194702, -0.0986982, 0.0570066,
            1.15001, 0.226786, -4.0326, 0.453503, -0.018045,
            0.264411, -4.51977, -0.279009, 0.137234, 0.336248,
        )},
    },
}
# <<< COEFICIENTES
