"""Prueba el estado de `D` (possession/dead_state.py) sin cargar ningún partido: que no mira fuera de los
tramos evaluados y que la opción de escala hace lo que dice.

    python validation/scripts/d_estado/prueba_d_estado.py

Con un partido inventado (jugadores con paseo aleatorio; nada sale del partido ni de la DFL) comprueba:

- `segments`: cada frame cae en su segmento y cada tramo evaluado es un segmento;
- `window_mean` con `bounds` da lo mismo que la media hecha a mano, frame a frame;
- **lo que hay fuera de los tramos no cuenta:** con los jugadores parados fuera (como antes del saque en
  el partido) y con nada fuera (como en la DFL del harness), las series por frame de dentro de los tramos
  son idénticas, y los rasgos y la puntuación, también (los rasgos, salvo el último bit de una suma);
- que la prueba distingue: con las ventanas sin recortar, los primeros frames de cada tramo sí cambian;
- **en la DFL no cambia nada:** si fuera de los tramos no hay datos, recortar da el mismo resultado bit a
  bit dentro de los tramos; y lejos de los bordes, con la misma serie, también cuando sí los hay. Fuera de
  los tramos, donde no se evalúa, un frame pegado a un tramo ya no ve los datos de dentro;
- las series por frame no dependen del tamaño de los trozos en que se calculan (`dead_state.CHUNK`);
- la interfaz de `evidence`;
- **la escala:** con 1 (el valor por defecto) la puntuación es la misma bit a bit; con 0,5 es la mitad,
  salvo el redondeo a la rejilla; con 2 se recorta a ±SCORE_CLIP; con 0 no opina; una escala que no sea un
  número finito y no negativo da error; y el harness la acepta como opción de la pieza
  (`"opciones": {"scale": 0.5}`) y el pipeline corre con ella.

No usa datos del partido ni de la DFL. Sale con código 1 si falla alguna comprobación. Claude puede
ejecutarlo.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import puntuar  # noqa: E402
from possession import dead_state, pipeline, tracking  # noqa: E402

SEMILLA = 20261115
N = 3000
BLOCKS = ((500, 1400), (1900, 2800))
PARADA = (800, 1100)  # frames del primer tramo en los que nadie se mueve
CAMPO = (105.0, 68.0)
FPS = 25
SLOTS_POR_EQUIPO = 13
TOLERANCIA = 1e-9  # los rasgos son diferencias de sumas acumuladas: lo de fuera mueve el último bit

fallos = []


def comprobar(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(nombre)


def partido_inventado(rng):
    """Jugadores con paseo aleatorio por todo el tracking, también fuera de los tramos; slots con huecos.

    Dentro del primer tramo se quedan quietos un rato (`PARADA`), para que la pieza puntúe a los dos lados.
    """
    largo, ancho = CAMPO
    slots = 2 * SLOTS_POR_EQUIPO
    px = np.cumsum(rng.normal(0.0, 0.12, (N, slots)), axis=0) + rng.uniform(0, largo, slots)
    py = np.cumsum(rng.normal(0.0, 0.12, (N, slots)), axis=0) + rng.uniform(0, ancho, slots)
    px = np.abs(px % (2 * largo) - largo).astype(np.float32)
    py = np.abs(py % (2 * ancho) - ancho).astype(np.float32)
    px[PARADA[0]:PARADA[1]], py[PARADA[0]:PARADA[1]] = px[PARADA[0]], py[PARADA[0]]
    for slot in range(slots):  # cada slot desaparece un rato
        inicio = int(rng.integers(0, N - 200))
        px[inicio:inicio + 150, slot], py[inicio:inicio + 150, slot] = np.nan, np.nan
    team = np.repeat(np.array([0, 1], dtype=np.int8), SLOTS_POR_EQUIPO)
    balon = np.full(N, np.nan)
    return tracking.Tracking(balon, balon.copy(), px, py, team, CAMPO, BLOCKS, FPS)


def dentro():
    mascara = np.zeros(N, dtype=bool)
    for inicio, fin in BLOCKS:
        mascara[inicio:fin] = True
    return mascara


def parados_fuera(trk):
    """El mismo partido con todos los jugadores quietos fuera de los tramos, como antes de un saque."""
    px, py = trk.px.copy(), trk.py.copy()
    fuera = ~dentro()
    px[fuera], py[fuera] = px[0], py[0]
    return trk._replace(px=px, py=py)


def nada_fuera(trk):
    """El mismo partido sin datos fuera de los tramos, como la DFL del harness."""
    px, py = trk.px.copy(), trk.py.copy()
    fuera = ~dentro()
    px[fuera], py[fuera] = np.nan, np.nan
    return trk._replace(px=px, py=py)


def media_a_mano(valores, atras, delante, blocks):
    """La media de la ventana recortada al segmento, con bucles: la referencia de la prueba."""
    cortes = sorted({0, len(valores)} | {borde for tramo in blocks for borde in tramo})
    salida = np.full(len(valores), np.nan)
    for t in range(len(valores)):
        bajo = max(c for c in cortes if c <= t)
        alto = min(c for c in cortes if c > t)
        trozo = valores[max(bajo, t - atras):min(alto, t + delante + 1)]
        trozo = trozo[~np.isnan(trozo)]
        if len(trozo):
            salida[t] = trozo.mean()
    return salida


def iguales(a, b):
    return bool(np.array_equal(a, b, equal_nan=True))


def da_error(llamada):
    try:
        llamada()
    except ValueError:
        return True
    return False


def comprobar_escala(trk):
    print("La escala")
    rejilla, tope = dead_state.SCORE_GRID, dead_state.SCORE_CLIP
    base = dead_state.evidence(trk)[0]
    columna = base[:, tracking.D]
    comprobar("el partido inventado puntúa a los dos lados y pasa de la mitad del tope",
              bool(columna.min() < 0 < columna.max()) and bool(np.abs(columna).max() > tope / 2.0),
              "{} valores distintos".format(len(np.unique(columna))))
    comprobar("escala 1: la misma puntuación bit a bit",
              dead_state.evidence(trk, scale=1.0)[0].tobytes() == base.tobytes()
              and dead_state.evidence(trk, scale=1)[0].tobytes() == base.tobytes())
    mitad = dead_state.evidence(trk, scale=0.5)[0][:, tracking.D]
    comprobar("escala 0,5: la mitad, salvo el redondeo a la rejilla",
              bool(np.abs(mitad - 0.5 * columna).max() <= 0.5 / rejilla)
              and iguales(mitad * rejilla, np.round(mitad * rejilla)),
              "diferencia máxima {:.6f}".format(float(np.abs(mitad - 0.5 * columna).max())))
    comprobar("escala 0,5: el mismo signo y nunca más de la mitad del tope",
              bool(np.all(mitad * columna >= 0)) and bool(np.abs(mitad).max() <= tope / 2.0))
    doble = dead_state.evidence(trk, scale=2.0)[0][:, tracking.D]
    comprobar("escala 2: el doble, recortado al tope", iguales(doble, np.clip(2.0 * columna, -tope, tope)))
    comprobar("escala 0: no opina", not dead_state.evidence(trk, scale=0.0)[0].any())
    comprobar("con cualquier escala solo opina en la columna D y no prohíbe nada",
              all(not dead_state.evidence(trk, scale=e)[0][:, [tracking.H, tracking.A]].any()
                  and bool(dead_state.evidence(trk, scale=e)[1].all()) for e in (0.5, 2.0)))
    malas = (-1.0, float("nan"), float("inf"), "0.5", None, True)
    comprobar("una escala negativa, no finita o que no es un número da error",
              all(da_error(lambda mala=mala: dead_state.evidence(trk, scale=mala)) for mala in malas))

    print("La escala desde el harness")
    funcion, dejar_fuera = puntuar.funcion_de(
        "dead_state", {"funcion": "evidence", "opciones": {"scale": 0.5}}, "prueba")
    comprobar("el harness acepta la opción y llama a la misma función",
              not dejar_fuera and iguales(funcion(trk)[0], dead_state.evidence(trk, scale=0.5)[0]))
    comprobar("el harness rechaza una opción que no existe",
              da_error(lambda: puntuar.funcion_de("dead_state", {"opciones": {"escala": 0.5}}, "prueba")))
    de_prueba = puntuar.partido_de_prueba()
    por_defecto = pipeline.run(de_prueba, report={})
    comprobar("el pipeline con la escala 1 da las etiquetas de siempre",
              iguales(pipeline.run(de_prueba, report={}, pieces={"dead_state": dead_state.evidence}),
                      por_defecto)
              and iguales(pipeline.run(de_prueba, report={}, pieces={"dead_state": puntuar.funcion_de(
                  "dead_state", {"opciones": {"scale": 1.0}}, "prueba")[0]}), por_defecto))
    con_mitad = pipeline.run(de_prueba, report={}, pieces={"dead_state": funcion})
    comprobar("el pipeline corre con la escala 0,5", con_mitad.shape == por_defecto.shape)


def parecidos(a, b):
    return bool(np.array_equal(np.isnan(a), np.isnan(b))
                and np.allclose(a, b, rtol=TOLERANCIA, atol=TOLERANCIA, equal_nan=True))


def main():
    rng = np.random.default_rng(SEMILLA)
    trk = partido_inventado(rng)
    en_tramo = dentro()
    nombres = sorted(dead_state.FEATURES)
    mas_larga = max(int(round(max(atras, delante) * FPS))
                    for _, atras, delante in dead_state.FEATURES.values())

    print("Segmentos")
    bajo, alto = dead_state.segments(N, BLOCKS)
    indice = np.arange(N)
    comprobar("cada frame cae dentro de su segmento", bool(np.all((bajo <= indice) & (indice < alto))))
    comprobar("cada tramo evaluado es un segmento",
              all(bool(np.all(bajo[a:b] == a) and np.all(alto[a:b] == b)) for a, b in BLOCKS))
    uno_bajo, uno_alto = dead_state.segments(N, ())
    comprobar("sin tramos hay un solo segmento", bool(np.all(uno_bajo == 0) and np.all(uno_alto == N)))

    print("La media por ventana")
    serie = rng.normal(0.0, 1.0, N)
    serie[rng.random(N) < 0.2] = np.nan
    for atras, delante in ((12, 12), (50, 50), (100, 0), (0, 100)):
        rapida = dead_state.window_mean(serie, atras, delante, (bajo, alto))
        comprobar("ventana de {} atrás y {} delante: como la hecha a mano".format(atras, delante),
                  parecidos(rapida, media_a_mano(serie, atras, delante, BLOCKS)))

    print("Lo que hay fuera de los tramos no cuenta")
    parados, vacio = parados_fuera(trk), nada_fuera(trk)
    variantes = (("tal cual", trk), ("parados", parados), ("vacío", vacio))
    series = {nombre: dead_state.raw_series(t) for nombre, t in variantes}
    comprobar("series por frame: idénticas dentro de los tramos",
              all(iguales(series["tal cual"][s][en_tramo], series[otro][s][en_tramo])
                  for s in dead_state.RAW for otro in ("parados", "vacío")))
    trozo = dead_state.CHUNK
    try:
        por_trozos = []
        for dead_state.CHUNK in (7, 500):  # el partido inventado cabe en un trozo: aquí se parte en varios
            por_trozos.append(dead_state.raw_series(trk))
    finally:
        dead_state.CHUNK = trozo
    comprobar("series por frame: las mismas calculadas en trozos de 7 y de 500 frames",
              all(iguales(series["tal cual"][s], otra[s]) for s in dead_state.RAW for otra in por_trozos))
    rasgos = {nombre: dead_state.features(t, nombres) for nombre, t in variantes}
    comprobar("rasgos: los mismos dentro de los tramos",
              all(parecidos(rasgos["tal cual"][r][en_tramo], rasgos[otro][r][en_tramo])
                  for r in nombres for otro in ("parados", "vacío")))
    puntos = {nombre: dead_state.log_odds(t) for nombre, t in variantes}
    comprobar("puntuación: idéntica dentro de los tramos",
              all(iguales(puntos["tal cual"][en_tramo], puntos[otro][en_tramo])
                  for otro in ("parados", "vacío")))

    print("La prueba distingue: sin recortar, el principio de cada tramo sí cambia")
    atras = delante = int(round(2.0 * FPS))
    sin_recortar = {nombre: dead_state.window_mean(series[nombre]["v_media"], atras, delante)
                    for nombre in ("parados", "vacío")}
    primeros = np.zeros(N, dtype=bool)
    for inicio, _ in BLOCKS:
        primeros[inicio:inicio + atras] = True
    distintos = int(np.sum(~np.isclose(sin_recortar["parados"][primeros], sin_recortar["vacío"][primeros],
                                       rtol=TOLERANCIA, atol=TOLERANCIA, equal_nan=True)))
    comprobar("la velocidad media en 4 s sin recortar depende de lo de fuera", distintos > 0,
              "{} de {} frames".format(distintos, int(primeros.sum())))

    print("Donde no hay nada que recortar, no cambia nada")
    limites = dead_state.segments(N, BLOCKS)
    mismos = True
    lejos = np.zeros(N, dtype=bool)
    for inicio, fin in BLOCKS:
        lejos[inicio + mas_larga:fin - mas_larga] = True
    lejos_igual = True
    for nombre in nombres:
        s, atras_s, delante_s = dead_state.FEATURES[nombre]
        atras, delante = int(round(atras_s * FPS)), int(round(delante_s * FPS))
        mismos = mismos and iguales(
            dead_state.window_mean(series["vacío"][s], atras, delante, limites)[en_tramo],
            dead_state.window_mean(series["vacío"][s], atras, delante)[en_tramo])
        lejos_igual = lejos_igual and iguales(
            dead_state.window_mean(series["tal cual"][s], atras, delante, limites)[lejos],
            dead_state.window_mean(series["tal cual"][s], atras, delante)[lejos])
    comprobar("sin datos fuera de los tramos (la DFL): dentro, recortar da lo mismo bit a bit", mismos)
    comprobar("lejos de los bordes: recortar da lo mismo bit a bit", lejos_igual,
              "{} frames a más de {} de un borde".format(int(lejos.sum()), mas_larga))

    print("Interfaz")
    score, allowed = dead_state.evidence(trk)
    comprobar("evidence devuelve (score, allowed) de forma (n, 3), finita y sin prohibir nada",
              score.shape == (N, 3) and allowed.shape == (N, 3) and bool(np.all(np.isfinite(score)))
              and bool(allowed.all()))
    comprobar("solo opina en la columna D",
              bool(np.all(score[:, tracking.H] == 0) and np.all(score[:, tracking.A] == 0)))
    comprobar("dos ejecuciones dan lo mismo", iguales(score, dead_state.evidence(trk)[0]))

    comprobar_escala(trk)

    print()
    if fallos:
        print("FALLAN {} comprobaciones".format(len(fallos)))
        sys.exit(1)
    print("TODO BIEN")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
