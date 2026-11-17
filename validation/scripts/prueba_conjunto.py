"""Prueba la pieza del modelo conjunto (possession/conjunto.py) sin cargar ningún partido.

    python validation/scripts/prueba_conjunto.py

Con el partido inventado del harness (`puntuar.partido_de_prueba`) y unos pesos al azar con semilla fija, comprueba:

- la interfaz: arrays (n, 3), puntuación finita, columna `D` a cero, cero fuera de los tramos y todo permitido;
- el determinismo: dos ejecuciones dan lo mismo, bit a bit;
- la antisimetría exacta: cambiar los equipos cambia el signo de z e intercambia los dos logits de cambio, bit a bit;
- que no escribe en el tracking (el del harness es de solo lectura) y que lo de fuera de los tramos no cuenta;
- los slots: añadir columnas vacías no cambia nada (bit a bit) y barajar las columnas, solo el redondeo;
- un tramo cuyo largo no es múltiplo de 5;
- la red: las sumas término a término de `conjunto.py` dan lo mismo que una versión con matrices escrita aparte;
- el envoltorio `aprendida.evidence_k2` y que la pieza no está en la entrega (`pipeline.PIECES`);
- si están los pesos de verdad (`possession/conjunto_pesos.npz`): los 8 pliegues, sus formas y su α.

No usa datos del partido ni de la DFL. Sale con código 1 si falla alguna comprobación. Claude puede ejecutarlo.
"""

import os
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import puntuar  # noqa: E402
from possession import aprendida, conjunto, pipeline, tracking  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

fallos = []
PLIEGUES = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9", "todos")
ALFAS = (0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)


def comprobar(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(nombre)


def pesos_al_azar(oculto=6, canales=7, dilaciones=(1, 2, 4), semilla=20261117):
    """Un juego de pesos pequeño, con semilla fija, con las formas de `validation/conjunto/juntar.py`."""
    rng = np.random.default_rng(semilla)
    entrada = 2 * (2 * oculto + 1) + conjunto.N_IMPAR + conjunto.N_PAR
    pesos = {"jugador_w0": rng.normal(0, 0.5, (oculto, conjunto.N_SLOT)), "jugador_b0": rng.normal(0, 0.2, oculto),
             "jugador_w1": rng.normal(0, 0.5, (oculto, oculto)), "jugador_b1": rng.normal(0, 0.2, oculto),
             "entrada_w": rng.normal(0, 0.3, (canales, entrada)), "entrada_b": rng.normal(0, 0.2, canales),
             "salida_w": rng.normal(0, 0.5, (4, canales)), "salida_b": rng.normal(0, 0.2, 4),
             "dilaciones": np.asarray(dilaciones, dtype=np.int64), "alfa": np.asarray(0.5)}
    for k in range(len(dilaciones)):
        pesos["bloque{}_w".format(k)] = rng.normal(0, 0.3, (canales, canales, 3))
        pesos["bloque{}_b".format(k)] = rng.normal(0, 0.2, canales)
    return {k: (v.astype(np.float32) if v.dtype == np.float64 and k != "alfa" else v) for k, v in pesos.items()}


def con_matrices(trk, inicio, fin, pesos):
    """z y los dos logits de cambio por grupo de un tramo, con productos de matrices: la referencia de la prueba."""
    por_slot, hay, impares, pares = conjunto.entradas(trk.bx[inicio:fin], trk.by[inicio:fin], trk.px[inicio:fin],
                                                      trk.py[inicio:fin], trk.team, trk.pitch[0], trk.pitch[1],
                                                      trk.fps)
    p = {k: np.asarray(v, dtype=np.float64) for k, v in pesos.items()}
    x = np.stack(por_slot, axis=-1)
    h = np.maximum(x @ p["jugador_w0"].T + p["jugador_b0"], 0.0)
    h = np.maximum(h @ p["jugador_w1"].T + p["jugador_b1"], 0.0)
    u = []
    for equipo in (tracking.H, tracking.A):
        mio = hay & (np.asarray(trk.team) == equipo)[None, :]
        hm = h * mio[:, :, None]
        u.append(np.concatenate([hm.sum(1) / 11.0, hm.max(1), mio.sum(1, keepdims=True) / 11.0], axis=1))
    impares, pares = np.stack(impares, axis=1), np.stack(pares, axis=1)

    def g(u_a, u_b, imp):
        v = np.concatenate([u_a, u_b, imp, pares], axis=1) @ p["entrada_w"].T + p["entrada_b"]
        grupos = len(v)
        for k, d in enumerate(int(d) for d in p["dilaciones"]):
            r = np.pad(np.maximum(v, 0.0), ((d, d), (0, 0)))
            w = p["bloque{}_w".format(k)]
            v = v + p["bloque{}_b".format(k)] + sum(r[t * d:t * d + grupos] @ w[:, :, t].T for t in range(3))
        return np.maximum(v, 0.0) @ p["salida_w"].T + p["salida_b"]

    directa, cambiada = g(u[0], u[1], impares), g(u[1], u[0], -impares)
    par, impar = 0.5 * (directa[:, 1] + cambiada[:, 1]), 0.5 * (directa[:, 2] - cambiada[:, 2])
    return 0.5 * (directa[:, 0] - cambiada[:, 0]), par + impar, par - impar


def main():
    trk = puntuar.partido_de_prueba()
    n = len(trk.bx)
    dentro = np.zeros(n, dtype=bool)
    for a, b in trk.blocks:
        dentro[a:b] = True

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, "pesos.npz")
        juego = pesos_al_azar()
        np.savez(ruta, **{"{}/{}".format(pliegue, k): v for pliegue in ("todos", "J03WMX") for k, v in juego.items()})
        de_verdad = conjunto.PESOS
        conjunto.PESOS = ruta
        conjunto._CACHE.clear()
        try:
            print("Con pesos al azar (semilla fija):")
            score, allowed = conjunto.evidence(trk)
            comprobar("interfaz: (n, 3), finita y todo permitido",
                      score.shape == (n, 3) and allowed.shape == (n, 3) and bool(np.isfinite(score).all())
                      and bool(allowed.all()))
            comprobar("la columna D va a cero", bool(np.all(score[:, tracking.D] == 0.0)))
            comprobar("cero fuera de los tramos evaluados", bool(np.all(score[~dentro] == 0.0)))
            comprobar("opina dentro de los tramos", bool(np.any(score[dentro, :2] != 0.0)))
            otra, _ = conjunto.evidence(trk)
            comprobar("determinista: dos ejecuciones dan lo mismo, bit a bit", np.array_equal(score, otra))
            con_pliegue, _ = conjunto.evidence(trk, fuera="J03WMX")
            comprobar("el pliegue se elige con `fuera`", np.array_equal(score, con_pliegue))

            z, hacia_h, hacia_a = conjunto.salidas(trk)
            cambiado = trk._replace(team=(1 - np.asarray(trk.team)).astype(np.int8))
            zc, hc, ac = conjunto.salidas(cambiado)
            comprobar("antisimetría exacta de z al cambiar los equipos", np.array_equal(zc, -z) and bool(np.any(z != 0)))
            comprobar("los logits de cambio se intercambian exactamente",
                      np.array_equal(hc, hacia_a) and np.array_equal(ac, hacia_h))
            sc, _ = conjunto.evidence(cambiado)
            comprobar("la evidencia intercambia H y A exactamente", np.array_equal(sc[:, [1, 0, 2]], score))

            fuera = trk._replace(bx=np.where(dentro, trk.bx, 50.0), by=np.where(dentro, trk.by, 30.0),
                                 px=np.where(dentro[:, None], trk.px, 10.0).astype(np.float32),
                                 py=np.where(dentro[:, None], trk.py, 20.0).astype(np.float32))
            comprobar("lo de fuera de los tramos no cuenta", np.array_equal(conjunto.salidas(fuera)[0], z))

            vacias = np.full((n, 3), np.nan, dtype=np.float32)
            mas = trk._replace(px=np.hstack([trk.px, vacias]), py=np.hstack([trk.py, vacias]),
                               team=np.concatenate([trk.team, np.array([0, 1, 0], dtype=np.int8)]))
            comprobar("añadir slots vacíos no cambia nada, bit a bit", np.array_equal(conjunto.salidas(mas)[0], z))
            orden = np.random.default_rng(3).permutation(trk.px.shape[1])
            barajado = trk._replace(px=trk.px[:, orden], py=trk.py[:, orden], team=np.asarray(trk.team)[orden])
            dif = float(np.max(np.abs(conjunto.salidas(barajado)[0] - z)))
            comprobar("barajar los slots solo cambia el redondeo", dif < 1e-9, "diferencia máxima {:.1e}".format(dif))

            a, b = trk.blocks[0]
            corto = trk._replace(blocks=((a, b - 2), trk.blocks[1]))
            zk = conjunto.salidas(corto)[0]
            comprobar("un tramo que no es múltiplo de 5", bool(np.isfinite(zk).all()) and bool(np.all(zk[b - 2:b] == 0.0))
                      and bool(np.any(zk[a:b - 2] != 0.0)))
            sin_nada = trk._replace(bx=np.full(n, np.nan), by=np.full(n, np.nan))
            comprobar("sin balón también da una salida finita", bool(np.isfinite(conjunto.salidas(sin_nada)[0]).all()))

            peor = 0.0
            for a, b in trk.blocks:
                propio = conjunto._por_grupo(trk.bx[a:b], trk.by[a:b], trk.px[a:b], trk.py[a:b], trk.team,
                                             trk.pitch[0], trk.pitch[1], trk.fps, conjunto.pesos())
                for mio, ref in zip(propio, con_matrices(trk, a, b, juego)):
                    peor = max(peor, float(np.max(np.abs(mio - ref))))
            comprobar("la red término a término da lo mismo que con matrices", peor < 1e-9,
                      "diferencia máxima {:.1e}".format(peor))

            envoltorio, _ = aprendida.evidence_k2(trk)
            comprobar("aprendida.evidence_k2 es conjunto.evidence", np.array_equal(envoltorio, score))
        finally:
            conjunto.PESOS = de_verdad
            conjunto._CACHE.clear()

    print("La entrega:")
    comprobar("la pieza no está en pipeline.PIECES",
              not any("conjunto" in v or "k2" in v for v in pipeline.PIECES.values()))
    comprobar("ni en DELIVERY_LAYERS", not any(capa.__module__.endswith("conjunto") for capa in
                                               pipeline.DELIVERY_LAYERS))

    print("Los pesos de verdad ({}):".format(os.path.basename(conjunto.PESOS)))
    if not os.path.isfile(conjunto.PESOS):
        print("  no están: se salta (la pieza está apagada y solo los necesita una entrega de prueba)")
    else:
        juegos = {}
        try:
            juegos = {pliegue: conjunto.pesos(None if pliegue == "todos" else pliegue) for pliegue in PLIEGUES}
        except KeyError as error:
            comprobar("están los 8 pliegues", False, str(error))
        if juegos:
            comprobar("están los 8 pliegues", True)
            formas = [{k: np.shape(v) for k, v in juego.items()} for juego in juegos.values()]
            comprobar("todos los pliegues tienen las mismas formas", all(f == formas[0] for f in formas))
            comprobar("α sale de la rejilla de B5", all(juego["alfa"] in ALFAS for juego in juegos.values()),
                      ", ".join("{} {:g}".format(p, juego["alfa"]) for p, juego in juegos.items()))
            comprobar("los pesos son finitos", all(bool(np.isfinite(v).all()) for juego in juegos.values()
                                                  for k, v in juego.items() if k != "alfa"))
            score, _ = conjunto.evidence(trk)
            comprobar("la pieza corre con los pesos de la entrega", bool(np.isfinite(score).all())
                      and bool(np.any(score[dentro, :2] != 0.0)))
            codes = pipeline.run(trk, pieces={"candidates": aprendida.evidence_k2})
            comprobar("el pipeline entero corre con la pieza", len(codes) == n and bool(np.all(codes[~dentro] == 3)))
        conjunto._CACHE.clear()

    print("\n{} comprobaciones fallan".format(len(fallos)) if fallos else "\nTodo bien.")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
