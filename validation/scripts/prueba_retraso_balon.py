"""Prueba la medida del retraso del balón con un tracking inventado de resultado conocido.

    python validation/scripts/prueba_retraso_balon.py

Sin datos del partido: todo el tracking es inventado, y abrir un fichero durante la medida es un error
(`sin_ficheros` intercepta `builtins.open` e `io.open`). Lo puede ejecutar cualquiera, Claude incluido. Prueba:

- `validation/retraso_balon/retraso.py`: que recupera desfases conocidos (0, +12 con la media hacia atrás,
  ±6 desplazando), las rachas, el filtro de los intercambios de slot, los empates, el determinismo y la
  lectura de la bitácora §5;
- `possession/ball.py`: la variante del candidato 2, `advance_ball`;
- `validation/partido/retraso_balon.py`: que la salida solo lleva agregados y que sin datos avisa y sale.
"""

import builtins
import contextlib
import io
import os
import sys
import tempfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "retraso_balon"))
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import retraso as rt  # noqa: E402
import retraso_balon as script_partido  # noqa: E402  (validation/partido/retraso_balon.py)
from possession import ball  # noqa: E402
from possession.tracking import Tracking  # noqa: E402

FALLOS = []
FPS = 25
LARGO, ANCHO = 105.0, 68.0
TRAMO, HUECO = 6000, 500
CADA, CORTE = 120, 10  # cada 120 frames, el balón se pierde 10: rachas de unos 110 frames
PORTADOR = 3


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


@contextlib.contextmanager
def sin_ficheros():
    """Abrir un fichero dentro del bloque es un error: la medida no lee nada."""
    abrir, abrir_io = builtins.open, io.open

    def niega(*args, **kwargs):
        raise AssertionError("una prueba ha intentado abrir un fichero")

    builtins.open = io.open = niega
    try:
        yield
    finally:
        builtins.open, io.open = abrir, abrir_io


def reflejar(x, bajo, alto):
    """x doblado dentro de [bajo, alto], como si rebotara en las paredes."""
    periodo = 2.0 * (alto - bajo)
    y = np.mod(x - bajo, periodo)
    return bajo + np.where(y > alto - bajo, periodo - y, y)


def partido_inventado(semilla=7):
    """(Tracking con el balón en el pie del portador, balón sin huecos ni ruido, máscara de los huecos).

    Un solo slot (el PORTADOR, del local) lleva el balón todo el rato, con una velocidad suave al azar de
    3 m/s como mucho. Los otros 21 están quietos y lejos. El balón se pierde 10 frames de cada 120.
    """
    rng = np.random.default_rng(semilla)
    n = 2 * TRAMO + HUECO
    v = np.zeros((n, 2))
    for t in range(1, n):
        v[t] = 0.96 * v[t - 1] + rng.normal(0.0, 0.12, 2)
    rapidez = np.hypot(v[:, 0], v[:, 1])
    v *= np.minimum(1.0, 3.0 / np.maximum(rapidez, 1e-9))[:, None]
    pos = np.array([LARGO / 2, ANCHO / 2]) + np.cumsum(v, axis=0) / FPS
    x, y = reflejar(pos[:, 0], 5.0, LARGO - 5.0), reflejar(pos[:, 1], 5.0, ANCHO - 5.0)
    slots = 22
    px = np.tile(-200.0 - np.arange(slots, dtype=float), (n, 1))
    py = np.full((n, slots), -200.0)
    px[:, PORTADOR], py[:, PORTADOR] = x, y
    bx, by = x + rng.normal(0.0, 0.05, n), y + rng.normal(0.0, 0.05, n)
    hueco = np.zeros(n, dtype=bool)
    hueco[TRAMO:TRAMO + HUECO] = True
    hueco[(np.arange(n) % CADA) < CORTE] = True
    px[TRAMO:TRAMO + HUECO], py[TRAMO:TRAMO + HUECO] = np.nan, np.nan
    team = np.array([0] * 11 + [1] * 11, dtype=np.int8)
    blocks = ((0, TRAMO), (TRAMO + HUECO, n))
    trk = Tracking(np.where(hueco, np.nan, bx), np.where(hueco, np.nan, by), px.astype(np.float32),
                   py.astype(np.float32), team, (LARGO, ANCHO), blocks, FPS)
    return trk, (bx, by), hueco


def con_balon(trk, bx, by, hueco):
    return trk._replace(bx=np.where(hueco, np.nan, bx), by=np.where(hueco, np.nan, by))


def media_centrada(v, ancho):
    """Media centrada de `ancho` frames (para la prueba; la de la calibración es dfl.media_movil)."""
    return rt.desplazar(rt.media_atras(v, ancho), -((ancho - 1) // 2))


def desfases_conocidos():
    print("Desfases conocidos en un partido inventado")
    trk, (bx, by), hueco = partido_inventado()
    casos = [
        ("sin suavizar", con_balon(trk, bx, by, hueco), 0),
        ("media centrada de 25", con_balon(trk, media_centrada(bx, 25), media_centrada(by, 25), hueco), 0),
        ("media hacia atrás de 25", con_balon(trk, rt.media_atras(bx, 25), rt.media_atras(by, 25), hueco), 12),
        ("retrasado 6", con_balon(trk, rt.desplazar(bx, 6), rt.desplazar(by, 6), hueco), 6),
        ("adelantado 6", con_balon(trk, rt.desplazar(bx, -6), rt.desplazar(by, -6), hueco), -6),
        ("centrado y retrasado 6", con_balon(trk, rt.desplazar(media_centrada(bx, 25), 6),
                                             rt.desplazar(media_centrada(by, 25), 6), hueco), 6),
    ]
    for nombre, caso, esperado in casos:
        with sin_ficheros():
            res = rt.resumen([rt.sumas(caso)])
        check("{}: L̂ = {:+d}".format(nombre, esperado),
              res["desfase"] is not None and abs(res["desfase"] - esperado) <= 1,
              "L̂ {}, partes {}, intervalo {}, rachas {}".format(res["desfase"], res["desfase_por_tramo"],
                                                               res["intervalo"], res["rachas"]))
    return trk, (bx, by), hueco


def rachas_y_filtros(trk, bola, hueco):
    print("Rachas y filtros")
    caso = con_balon(trk, bola[0], bola[1], hueco)
    inicios, fines, slots = rt.rachas(caso)
    check("hay rachas, todas del portador y de 25 frames o más",
          len(inicios) > 50 and np.all(slots == PORTADOR) and np.all(fines - inicios >= rt.MIN_RACHA),
          "{} rachas".format(len(inicios)))
    bid = rt.ids_de_tramo(caso)
    check("ninguna racha cruza el hueco entre tramos ni sale de los tramos",
          np.all(bid[inicios] == bid[fines - 1]) and np.all(bid[inicios] >= 0))
    # un balón lejos de todos (a más de RADIO) no da rachas
    lejos = caso._replace(bx=caso.bx + 2.0)
    check("con el balón a 2 m del portador no hay rachas", len(rt.rachas(lejos)[0]) == 0)
    # un salto de 10 m del slot en un frame es un intercambio: su velocidad no cuenta
    px = np.array(caso.px, dtype=np.float32)
    px[300:, PORTADOR] += 10.0
    v = rt.velocidad_jugador(caso._replace(px=px), bid, np.arange(296, 305), np.full(9, PORTADOR))
    check("un intercambio de slot (10 m en un frame) deja la velocidad en NaN alrededor",
          np.isnan(v[2:6]).all() and np.isfinite(v[0]).all() and np.isfinite(v[-1]).all())
    vb = rt.velocidad_balon(caso, bid)
    check("la velocidad del balón es NaN en los huecos y en sus bordes",
          np.isnan(vb[TRAMO - 1]).all() and np.isnan(vb[CADA + CORTE + 1]).all() and np.isfinite(vb[CADA + CORTE + 2]).all())


def empates_y_lectura():
    print("Empates, determinismo y lectura")
    check("con todo empatado gana 0", rt.elegir(np.zeros(len(rt.DESFASES))) == 0)
    c = np.zeros(len(rt.DESFASES))
    c[list(rt.DESFASES).index(-3)] = c[list(rt.DESFASES).index(3)] = 1.0
    check("entre −3 y +3 empatados gana −3", rt.elegir(c) == -3)
    check("sin correlaciones no hay desfase", rt.elegir(np.full(len(rt.DESFASES), np.nan)) is None)

    def res(d, intervalo, partes):
        return {"desfase": d, "intervalo": intervalo, "desfase_por_tramo": partes}

    casos = [
        (res(2, (1.0, 3.0), [2, 1]), rt.NADA),
        (res(-3, (-4.0, -2.0), [-3, -2]), rt.NADA),
        (res(4, (3.0, 6.0), [4, 5]), rt.DESPLAZAR),
        (res(-7, (-9.0, -5.0), [-7, -6]), rt.NEGATIVO),  # cambio de Ismael (15/11): el negativo se apunta
        (res(-4, (-5.0, -3.0), [-4, -4]), rt.NEGATIVO),
        (res(12, (10.0, 14.0), [11, 12]), rt.DESPLAZAR),
        (res(5, (3.0, 6.0), [1, 7]), rt.NO_CONCLUYENTE),  # partes a 6 frames
        (res(5, (0.0, 9.0), [5, 5]), rt.NO_CONCLUYENTE),  # intervalo de 9 frames
        (res(None, (None, None), [None, None]), rt.NO_CONCLUYENTE),
        (res(3, (2.0, 4.0), [3, None]), rt.NO_CONCLUYENTE),
    ]
    for r, esperado in casos:
        check("lectura de L̂ {}, intervalo {}, partes {}: {}".format(r["desfase"], r["intervalo"],
                                                                    r["desfase_por_tramo"], esperado),
              rt.lectura(r)[0] == esperado, rt.lectura(r)[1])
    check("en el límite: |L̂ − L̂| = 4 y ancho 8 todavía concluyen",
          rt.lectura(res(4, (1.0, 9.0), [2, 6]))[0] == rt.DESPLAZAR)

    trk, bola, hueco = partido_inventado(semilla=11)
    caso = con_balon(trk, rt.media_atras(bola[0], 25), rt.media_atras(bola[1], 25), hueco)
    a, b = rt.resumen([rt.sumas(caso)]), rt.resumen([rt.sumas(caso)])
    check("dos ejecuciones dan exactamente lo mismo", a == b)
    junto = rt.resumen([rt.sumas(caso), rt.sumas(caso)])
    check("juntar dos trackings iguales da el mismo desfase", junto["desfase"] == a["desfase"] and
          junto["rachas"] == 2 * a["rachas"])


def herramientas():
    print("Herramientas de la calibración")
    v = np.array([0.0, 1.0, 2.0, np.nan, 4.0, 5.0])
    check("media hacia atrás de 3 ignora los NaN", np.allclose(rt.media_atras(v, 3), [0.0, 0.5, 1.0, 1.5, 3.0, 4.5]))
    check("retrasar 2", np.allclose(rt.desplazar(v, 2), [np.nan, np.nan, 0.0, 1.0, 2.0, np.nan], equal_nan=True))
    check("adelantar 2", np.allclose(rt.desplazar(v, -2), [2.0, np.nan, 4.0, 5.0, np.nan, np.nan], equal_nan=True))
    check("desplazar 0 no cambia nada", np.allclose(rt.desplazar(v, 0), v, equal_nan=True))


def sumas_familia(semilla, desfases=None):
    """{d: sumas} de un partido inventado con el balón centrado (media de 25) y retrasado d frames."""
    trk, (bx, by), hueco = partido_inventado(semilla)
    cx, cy = media_centrada(bx, 25), media_centrada(by, 25)
    desfases = rt.FAMILIA if desfases is None else desfases
    with sin_ficheros():
        return {int(d): rt.sumas(con_balon(trk, rt.desplazar(cx, int(d)), rt.desplazar(cy, int(d)), hueco))
                for d in desfases}, (trk, bx, by, hueco)


def version_2():
    print("Versión 2: la curva entera frente a una familia")
    fam_a, _ = sumas_familia(21)
    fam_b, _ = sumas_familia(22)
    familia = {d: rt.curva_de([fam_a[d], fam_b[d]]) for d in rt.FAMILIA}
    prueba, (trk, bx, by, hueco) = sumas_familia(23, desfases=(-9, -3, 0, 5, 9))
    for d, s in prueba.items():
        with sin_ficheros():
            res = rt.resumen_v2([s], familia)
        check("un partido que no está en la familia, retrasado {:+d}: d̂ = {:+d}".format(d, d),
              res["desfase"] is not None and abs(res["desfase"] - d) <= 1,
              "d̂ {}, partes {}, intervalo {}, residuo {:.3f}".format(res["desfase"], res["desfase_por_tramo"],
                                                                    res["intervalo"], res["residuo"]))
    atras = rt.resumen_v2([rt.sumas(con_balon(trk, rt.media_atras(bx, 25), rt.media_atras(by, 25), hueco))], familia)
    check("la media hacia atrás de 25 da d̂ = +12", atras["desfase"] is not None and abs(atras["desfase"] - 12) <= 1,
          atras["desfase"])
    check("resumen_v2 guarda el máximo de la versión 1 aparte",
          atras["desfase_maximo"] == rt.resumen([rt.sumas(con_balon(trk, rt.media_atras(bx, 25),
                                                                     rt.media_atras(by, 25), hueco))])["desfase"])
    check("dos ejecuciones de resumen_v2 dan lo mismo", rt.resumen_v2([prueba[0]], familia) ==
          rt.resumen_v2([prueba[0]], familia))

    base = np.sin(np.linspace(0, 3, len(rt.DESFASES)))
    check("una curva idéntica a la de d = +4 da d̂ = +4 y residuo 0", rt.ajustar(base, {0: -base, 4: base}) == (4, 0.0))
    check("la escala y el nivel no cuentan (curvas normalizadas)", rt.ajustar(3 * base + 1, {0: -base, 4: base})[0] == 4)
    check("en un empate entre −2 y +2 gana −2", rt.ajustar(base, {-2: base, 2: base})[0] == -2)
    check("en un empate entre 0 y +1 gana 0", rt.ajustar(base, {1: base, 0: base})[0] == 0)
    check("sin curva no hay d̂", rt.ajustar(np.full(len(rt.DESFASES), np.nan), {0: base}) == (None, None))
    check("una curva plana no se puede normalizar", rt.normalizar(np.ones(len(rt.DESFASES))) is None)

    def res(residuo, d=2):
        return {"residuo": residuo, "desfase": d, "intervalo": (1.0, 3.0), "desfase_por_tramo": [d, d]}

    check("residuo de más del doble del de referencia: no concluyente",
          rt.lectura_v2(res(0.21), 0.1)[0] == rt.NO_CONCLUYENTE)
    check("residuo justo el doble: se lee como en §5", rt.lectura_v2(res(0.2), 0.1)[0] == rt.NADA)
    check("con el residuo bien, un d̂ de +6 es el candidato 2", rt.lectura_v2(res(0.05, 6), 0.1)[0] == rt.DESPLAZAR)
    check("sin residuo de referencia: no concluyente", rt.lectura_v2(res(0.05), None)[0] == rt.NO_CONCLUYENTE)

    rampa = np.arange(400, dtype=float)
    check("la media exponencial con α = 1/9 va 8 frames por detrás en una rampa",
          abs(rampa[300] - rt.media_exponencial(rampa, 1.0 / 9.0)[300] - 8.0) < 1e-6)
    v = np.array([np.nan, 2.0, np.nan, 2.0])
    check("la media exponencial ignora los NaN", np.allclose(rt.media_exponencial(v, 0.5), [np.nan, 2.0, 2.0, 2.0],
                                                            equal_nan=True))
    return familia


def script_del_partido(familia):
    print("Script del partido (validation/partido/retraso_balon.py)")
    trk, bola, hueco = partido_inventado(semilla=3)
    caso = con_balon(trk, rt.media_atras(bola[0], 25), rt.media_atras(bola[1], 25), hueco)
    with sin_ficheros():
        res = rt.resumen_v2([rt.sumas(caso)], familia)
    res.update({"residuo_referencia": max(res["residuo"], 1e-6), "partidos_familia": 2})
    lineas = script_partido.para_imprimir(res)
    texto = "\n".join(lineas)
    check("imprime el desfase, el intervalo, las partes, los residuos y la lectura",
          "d̂ = +12 frames" in texto and "intervalo del 5 al 95 %" in texto and "d̂ por parte" in texto and
          "de referencia (DFL)" in texto and "Lectura (bitácora §8.5): candidato 2" in texto, lineas[-2:])
    check("y el máximo de la versión 1 como descriptivo", "L̂ de la versión 1" in texto)
    check("los controles salen, y no cuadran con un partido inventado", "¿cuadran los tres? NO" in texto)
    check("una salida de pocas líneas, sin nada por frame", len(lineas) < 30 and str(TRAMO + HUECO) not in texto,
          "{} líneas".format(len(lineas)))
    check("una celda de 1 a 4 casos sale como «< 5»", script_partido.celda(3) == "< 5" and
          script_partido.celda(0) == "0" and script_partido.celda(5) == "5")
    with tempfile.TemporaryDirectory() as vacia:
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = script_partido.main(["--data-dir", vacia])
        check("sin los datos del partido avisa y sale con 1", codigo == 1 and "No encuentro el ATD" in salida.getvalue())
        # con el partido «encontrado» (require no hace nada) y la caché de la DFL vacía: avisa antes de leer nada.
        # Con --data-dir a una carpeta que no existe: aunque cambie el orden de las comprobaciones de main(), no
        # hay partido que leer (nunca la MTAH_DATA_DIR de verdad).
        require, cache = script_partido.games.require, script_partido.cal.dfl.dfl_lector.carpeta_cache
        script_partido.games.require = lambda *a, **k: []
        script_partido.cal.dfl.dfl_lector.carpeta_cache = lambda: vacia
        try:
            salida = io.StringIO()
            with contextlib.redirect_stdout(salida), sin_ficheros():
                codigo = script_partido.main(["--data-dir", os.path.join(vacia, "no-existe")])
        finally:
            script_partido.games.require, script_partido.cal.dfl.dfl_lector.carpeta_cache = require, cache
        check("sin la caché de la DFL avisa y sale con 1, sin abrir nada",
              codigo == 1 and "Falta la caché de la DFL" in salida.getvalue())


def variante_del_balon(familia):
    print("La variante del candidato 2 (possession/ball.py, advance_ball)")
    n = 8
    bx, by = np.arange(n, dtype=float), 10.0 + np.arange(n, dtype=float)
    px, py = np.zeros((n, 2)), np.ones((n, 2))
    trk = Tracking(bx.copy(), by.copy(), px, py, np.array([0, 1], np.int8), (LARGO, ANCHO), ((0, n),), FPS)
    adelantado = ball.advance_ball(trk, 2)
    check("adelanta 2: el balón de t es el de t + 2 y los dos últimos quedan sin balón",
          np.allclose(adelantado.bx, [2, 3, 4, 5, 6, 7, np.nan, np.nan], equal_nan=True) and
          np.allclose(adelantado.by, [12, 13, 14, 15, 16, 17, np.nan, np.nan], equal_nan=True))
    check("con un número negativo, retrasa",
          np.allclose(ball.advance_ball(trk, -2).bx, [np.nan, np.nan, 0, 1, 2, 3, 4, 5], equal_nan=True))
    check("con 0 no cambia nada", np.array_equal(ball.advance_ball(trk, 0).bx, bx))
    check("por defecto adelanta BALL_LEAD = 4", ball.BALL_LEAD == 4 and
          np.allclose(ball.advance_ball(trk).bx[:4], [4, 5, 6, 7]))
    check("no cambia el tracking de entrada ni los jugadores, y el balón nuevo es de solo lectura",
          np.array_equal(trk.bx, bx) and adelantado.px is trk.px and adelantado.py is trk.py and
          not adelantado.bx.flags.writeable)
    check("es lo contrario de retrasar con la herramienta de la calibración",
          np.array_equal(ball.advance_ball(trk, 3).bx, rt.desplazar(bx, -3), equal_nan=True))
    # con el balón del partido inventado retrasado 4, la variante lo devuelve a su sitio: d̂ vuelve a 0
    trk2, bola, hueco = partido_inventado(24)
    cx, cy = media_centrada(bola[0], 25), media_centrada(bola[1], 25)
    tarde = con_balon(trk2, rt.desplazar(cx, 4), rt.desplazar(cy, 4), hueco)
    antes = rt.resumen_v2([rt.sumas(tarde)], familia)["desfase"]
    despues = rt.resumen_v2([rt.sumas(ball.advance_ball(tarde, 4))], familia)["desfase"]
    check("un balón 4 frames tarde da d̂ = +4, y con advance_ball vuelve a 0", antes == 4 and despues == 0,
          "antes {}, después {}".format(antes, despues))


def main():
    trk, bola, hueco = desfases_conocidos()
    rachas_y_filtros(trk, bola, hueco)
    empates_y_lectura()
    herramientas()
    familia = version_2()
    variante_del_balon(familia)
    script_del_partido(familia)
    print()
    if FALLOS:
        print("FALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
        return 1
    print("TODO BIEN")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
