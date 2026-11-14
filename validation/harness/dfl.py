"""Los partidos abiertos de la Bundesliga (DFL) en el formato del pipeline, con etiquetas y balón degradado.

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del experimento 0
(`validation/experimento0/dfl_lector.py`). Lo puede ejecutar cualquiera, Claude incluido.

Qué hace con cada partido:

- **Etiquetas, siempre con el tracking limpio** y con las dos convenciones: el flag de la DFL tal cual
  ("flag", cambia en el primer toque del rival) y el corregido con control ("control", con la definición
  "C0-12 o dos toques" de `validation/experimento1/correccion.py`). El `D` es el mismo en las dos.
- **Tracking en el formato de `possession/tracking.py`:** metros con el origen en una esquina, las dos
  partes seguidas con un hueco sin datos en medio, y los slots de cada equipo barajados a trozos, para
  que ningún código pueda apoyarse en que un slot sea un jugador.
- **Balón degradado, en tres condiciones.** En las tres se tapa el balón en los frames `D` y en sus
  bordes, porque la DFL lo congela mientras está muerto y eso delataría la etiqueta (experimento 0).
  - "limpio": nada más;
  - "huecos": además falta en el 41 % de los frames vivos, con la mitad de las disputas y de los balones
    altos tapados y el resto en bloques al azar (la condición elegida en el experimento 2);
  - "huecos y suavizado": los mismos huecos, sobre un balón suavizado con una media móvil de 25 frames
    (lo que el experimento 2 apunta que hace el ATD; es una inferencia).

  La degradación es provisional: falta comprobarla contra la medida del balón del ATD en todo el partido.
  Los jugadores no se degradan.

Todo con semilla fija: dos ejecuciones dan lo mismo.
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in ("experimento0", "experimento1", "experimento2"):
    sys.path.insert(0, os.path.join(AQUI, "..", _carpeta))
sys.path.insert(0, ROOT)
import correccion as cr  # noqa: E402
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
import instrumento as ins  # noqa: E402
from peso_correccion import controles_parte  # noqa: E402
from possession import tracking  # noqa: E402

PARTIDOS = etiquetas_dfl.PARTIDOS
SEMILLA = 20261114
FPS = 25
HUECO = 500  # frames sin datos entre las dos partes, para que ninguna ventana cruce el descanso
BORDE = 5  # frames a cada lado de un `D` en los que también se tapa el balón
OBJETIVO = 0.41  # fracción de los frames vivos sin balón (DATA.md)
DISPUTAS = 0.5  # fracción de disputas y balones altos tapados (experimento 2)
MEDIA_BLOQUE = 25  # frames de media de los bloques al azar (experimento 2)
SUAVIZADO = 25  # frames de la media móvil del balón (experimento 2, inferencia)
MEDIA_BARAJADO = 750  # frames de media entre dos barajados de los slots
# La forma «atd» (perfil del ATD del 14/11, validation/resultados/2026-11-14_perfil_atd.md): el ATD casi no
# tiene huecos cortos. Los 15 de hasta 0,5 s suman 51 frames en 94.214 frames con balón; el 82,6 % de los
# de hasta 15 s dura de 5 a 15 s.
MICROCORTES = 1000.0 * 15 / 94214  # por cada 1.000 frames vivos
MEDIA_MICROCORTE = 51 / 15  # frames
MAX_MICROCORTE = 12  # frames (0,5 s)
BLOQUE_ATD = (125, 375)  # frames (de 5 a 15 s)
CONDICIONES = ("limpio", "huecos", "huecos y suavizado")
PARAMETROS_DE = {
    "limpio": None,
    "huecos": {"objetivo": OBJETIVO, "disputas": DISPUTAS, "media_bloque": MEDIA_BLOQUE, "suavizado": 1},
    "huecos y suavizado": {"objetivo": OBJETIVO, "disputas": DISPUTAS, "media_bloque": MEDIA_BLOQUE,
                           "suavizado": SUAVIZADO},
}
CONVENCIONES = ("flag", "control")
DEFINICION_CONTROL = "C0-12 o dos toques"
H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X


def etiquetas_parte(parte):
    """{convención: códigos por frame (0 `H`, 1 `A`, 2 `D`, 3 `X`)} de una parte, con el tracking limpio."""
    estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
    activo = estado == 1
    flag = np.full(len(estado), X, dtype=np.int8)
    flag[estado == 0] = D
    flag[activo & (poss == 1)] = H
    flag[activo & (poss == 2)] = A
    sin_dato = flag == X
    corregida = cr.corregir(np.where(sin_dato, D, flag), controles_parte(parte)[DEFINICION_CONTROL])
    corregida = corregida.astype(np.int8)
    corregida[sin_dato] = X
    return {"flag": flag, "control": corregida}


def media_movil(valores, ancho):
    """Media móvil centrada de `ancho` frames que ignora los NaN; NaN si no hay ningún dato en la ventana."""
    valores = np.asarray(valores, dtype=float)
    hay = ~np.isnan(valores)
    suma = np.concatenate(([0.0], np.cumsum(np.where(hay, valores, 0.0))))
    cuenta = np.concatenate(([0], np.cumsum(hay)))
    indice = np.arange(len(valores))
    bajo = np.maximum(0, indice - ancho // 2)
    alto = np.minimum(len(valores), indice + ancho // 2 + 1)
    n = cuenta[alto] - cuenta[bajo]
    return np.where(n > 0, (suma[alto] - suma[bajo]) / np.maximum(n, 1), np.nan)


def degradar_parte(parte, condicion, rng):
    """Copia de una parte de la caché con el balón como en `condicion`. Los jugadores no cambian."""
    if condicion not in CONDICIONES:
        raise ValueError("condición desconocida: {}".format(condicion))
    return degradar_con(parte, PARAMETROS_DE[condicion], rng)[0]


def mascara_como_el_atd(n, activo, objetivo, microcortes, rng, base=None):
    """Huecos con la ley del ATD (validation/resultados/2026-11-14_perfil_atd.md, forma «atd»).

    - Microcortes: `microcortes` por cada 1.000 frames vivos, de longitud geométrica de media
      `MEDIA_MICROCORTE` frames y como mucho `MAX_MICROCORTE` (0,5 s), que empiezan en un frame vivo.
    - Bloques de 5 a 15 s (longitud uniforme en `BLOQUE_ATD`) hasta tapar `objetivo` de los frames vivos,
      con el inicio al azar como en `instrumento.mascara_bloques`.
    """
    m = np.zeros(n, bool) if base is None else base.copy()
    vivos = np.flatnonzero(activo)
    if len(vivos) == 0:
        return m
    k = int(rng.poisson(microcortes * len(vivos) / 1000.0))
    for inicio, largo in zip(rng.choice(vivos, size=k),
                             np.minimum(rng.geometric(1.0 / MEDIA_MICROCORTE, size=k), MAX_MICROCORTE)):
        m[inicio:inicio + largo] = True
    tapados = int(np.sum(m & activo))
    while tapados < objetivo * len(vivos):
        inicio = int(rng.integers(0, n))
        largo = int(rng.integers(BLOQUE_ATD[0], BLOQUE_ATD[1] + 1))
        nuevo = ~m[inicio:inicio + largo]
        tapados += int(np.sum(nuevo & activo[inicio:inicio + largo]))
        m[inicio:inicio + largo] = True
    return m


def degradar_con(parte, prm, rng):
    """(parte con el balón degradado, frames vivos, % de vivos tapados solo por la parte dirigida).

    `prm=None` es "limpio": solo se tapa el balón en los `D` y en sus bordes. Si no, sus claves son
    `objetivo`, `disputas`, `media_bloque` y `suavizado` y, opcionales, `forma` ("dirigida", la de antes del
    perfil del ATD, o "atd") y `microcortes` (solo con la forma "atd").
    - "dirigida": la parte dirigida tapa `disputas` de los episodios de disputa y de balón alto, y bloques de
      longitud geométrica (media `media_bloque`) completan `objetivo`.
    - "atd": la misma parte dirigida, y luego `mascara_como_el_atd` con `objetivo` y `microcortes`.
    El balón se suaviza (media móvil de `suavizado` frames) antes de tapar, sin el balón congelado del `D`.
    """
    estado = np.asarray(parte["estado"])
    activo = estado == 1
    x, y = np.array(parte["x"], dtype=float), np.array(parte["y"], dtype=float)
    tapado = np.convolve((~activo).astype(int), np.ones(2 * BORDE + 1, dtype=int), mode="same") > 0
    dirigida_pct = 0.0
    if prm is not None:
        forma = prm.get("forma", "dirigida")
        if forma not in ("dirigida", "atd"):
            raise ValueError("forma desconocida: {}".format(forma))
        prep = ins.preparar_en_juego(parte, estado)
        huecos, dirigida_pct = ins.mascara_dirigida(
            prep, np.asarray(parte["z"], dtype=float), activo, prm["objetivo"] if forma == "dirigida" else 0.0,
            rng, fraccion=prm["disputas"], media=prm["media_bloque"])
        if forma == "atd":
            huecos = mascara_como_el_atd(len(activo), activo, prm["objetivo"], prm.get("microcortes", 0.0), rng,
                                         base=huecos)
        if prm["suavizado"] > 1:
            x[tapado], y[tapado] = np.nan, np.nan  # el balón congelado del `D` no entra en la media
            x, y = media_movil(x, prm["suavizado"]), media_movil(y, prm["suavizado"])
        tapado = tapado | huecos
    x[tapado], y[tapado] = np.nan, np.nan
    nueva = dict(parte)
    nueva["x"], nueva["y"] = x, y
    return nueva, int(activo.sum()), dirigida_pct


def barajar_slots(px, py, team, rng):
    """Reordena los slots dentro de cada equipo a trozos y, al final, las columnas enteras.

    Tras esto un slot sigue siendo de su equipo, pero ya no es la misma persona a lo largo del partido.
    """
    n, slots = px.shape
    por_equipo = [np.flatnonzero(team == k) for k in (0, 1)]
    t = 0
    while t < n:
        tramo = int(rng.geometric(1.0 / MEDIA_BARAJADO))
        orden = np.arange(slots)
        for columnas in por_equipo:
            orden[columnas] = rng.permutation(columnas)
        px[t:t + tramo] = px[t:t + tramo][:, orden]
        py[t:t + tramo] = py[t:t + tramo][:, orden]
        t += tramo
    orden = rng.permutation(slots)
    return px[:, orden], py[:, orden], team[orden]


def a_tracking(partes, campo, rng):
    """Las dos partes como un `Tracking`, con un hueco sin datos entre ellas."""
    largo, ancho = campo
    por_equipo = {e: max(partes[k]["equipos"][e]["x"].shape[1] for k in (1, 2)) for e in ("local", "visitante")}
    slots = por_equipo["local"] + por_equipo["visitante"]
    longitudes = [len(partes[k]["x"]) for k in (1, 2)]
    n = longitudes[0] + HUECO + longitudes[1]
    bx, by = np.full(n, np.nan), np.full(n, np.nan)
    px = np.full((n, slots), np.nan, dtype=np.float32)
    py = np.full((n, slots), np.nan, dtype=np.float32)
    inicio = 0
    blocks = []
    for k, longitud in zip((1, 2), longitudes):
        tramo = slice(inicio, inicio + longitud)
        bx[tramo] = np.asarray(partes[k]["x"], dtype=float) + largo / 2.0
        by[tramo] = np.asarray(partes[k]["y"], dtype=float) + ancho / 2.0
        columna = 0
        for equipo in ("local", "visitante"):
            ex, ey = partes[k]["equipos"][equipo]["x"], partes[k]["equipos"][equipo]["y"]
            px[tramo, columna:columna + ex.shape[1]] = ex + largo / 2.0
            py[tramo, columna:columna + ey.shape[1]] = ey + ancho / 2.0
            columna += por_equipo[equipo]
        blocks.append((inicio, inicio + longitud))
        inicio += longitud + HUECO
    team = np.repeat(np.array([0, 1], dtype=np.int8), [por_equipo["local"], por_equipo["visitante"]])
    px, py, team = barajar_slots(px, py, team, rng)
    return tracking.Tracking(bx, by, px, py, team, (float(largo), float(ancho)), tuple(blocks), FPS)


def cargar(partido):
    """Un partido de la caché con sus etiquetas: {"partido", "indice", "partes", "campo", "meta", "gt"}.

    `gt` es {convención: códigos por frame}, con `X` en el hueco entre las dos partes, alineado con el
    `Tracking` que devuelve `tracking_de`.
    """
    datos = dfl_lector.cargar_cache(partido)
    partes = datos["partes"]
    por_parte = {k: etiquetas_parte(partes[k]) for k in (1, 2)}
    hueco = np.full(HUECO, X, dtype=np.int8)
    gt = {c: np.concatenate([por_parte[1][c], hueco, por_parte[2][c]]) for c in CONVENCIONES}
    return {"partido": partido, "indice": PARTIDOS.index(partido), "partes": partes,
            "campo": tuple(datos["meta"]["campo"]), "meta": datos["meta"], "gt": gt}


def tracking_de(cargado, condicion):
    """El `Tracking` de un partido cargado, con el balón como en `condicion`.

    Los huecos son los mismos en "huecos" y en "huecos y suavizado", y los slots se barajan igual en las
    tres condiciones: lo único que cambia entre ellas es el balón.
    """
    partes = {k: degradar_parte(cargado["partes"][k], condicion,
                                np.random.default_rng([SEMILLA, cargado["indice"], k]))
              for k in (1, 2)}
    return a_tracking(partes, cargado["campo"], np.random.default_rng([SEMILLA, cargado["indice"], 99]))
