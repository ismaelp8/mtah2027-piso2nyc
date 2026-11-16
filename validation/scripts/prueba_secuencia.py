"""Prueba B11 y B12 (possession/secuencia.py) sin cargar ningún partido.

    python validation/scripts/prueba_secuencia.py

Con el partido inventado del harness (`puntuar.partido_de_prueba`) y con datos al azar comprueba:

- los pesos: los 16 juegos (B11 y B12; los 7 partidos y un pliegue sin cada partido), con sus formas, α de la
  rejilla y `rms` positivo;
- la interfaz: arrays (n, 3), puntuación finita, columna `D` a cero, cero fuera de los tramos y todo permitido;
- el determinismo, que cambiar los equipos intercambia `H` y `A` exactamente y que una permutación fija de los
  slots no cambia la puntuación;
- que z es antisimétrico (el espejo de los canales cambia el signo de z, exacto), que aguanta tramos más cortos que
  el campo de la convolución y que la convolución y la GRU de numpy coinciden con una versión a mano, frame a frame;
- si hay torch (el entorno `mtah2027-balon`), que numpy da lo mismo que torch con los pesos guardados. Sin torch lo
  dice y no lo cuenta como fallo: la misma comparación con datos de la DFL la imprime `entrenar_red.py`.

No usa datos del partido ni de la DFL. Sale con código 1 si falla alguna comprobación. Claude puede ejecutarlo.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _carpeta in (os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "secuencia"), ROOT):
    sys.path.insert(0, _carpeta)
import comun  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, secuencia, tracking  # noqa: E402

fallos = []


def comprobar(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(nombre)


def conv_a_mano(h, w, b, d):
    """La convolución de `secuencia._conv`, frame a frame, con un solo lote."""
    cout, cin, k = w.shape
    largo = h.shape[1]
    out = np.zeros((cout, largo))
    for t in range(largo):
        for o in range(cout):
            v = b[o]
            for i in range(cin):
                for j in range(k):
                    s = t + (j - (k - 1) // 2) * d
                    if 0 <= s < largo:
                        v += w[o, i, j] * h[i, s]
            out[o, t] = v
    return out


def gru_a_mano(x, wih, bih, whh, bhh):
    """Una GRU de un sentido con las ecuaciones de torch, paso a paso con productos de matrices."""
    oculto = whh.shape[1]
    h = np.zeros(oculto)
    salida = []
    for t in range(x.shape[1]):
        gi, gh = wih @ x[:, t] + bih, whh @ h + bhh
        r = 1 / (1 + np.exp(-(gi[:oculto] + gh[:oculto])))
        u = 1 / (1 + np.exp(-(gi[oculto:2 * oculto] + gh[oculto:2 * oculto])))
        n = np.tanh(gi[2 * oculto:] + r * gh[2 * oculto:])
        h = (1 - u) * n + u * h
        salida.append(h)
    return np.array(salida).T


def comprobar_pesos():
    print("Pesos")
    juegos = secuencia.cargar()
    formas = {"b11": {"entrada_w": (24, 12, 1), "bloque6_w": (24, 24, 3), "salida_w": (1, 24, 1)},
              "b12": {"w_ih": (48, 12), "w_hh": (48, 16), "w_ih_r": (48, 12), "salida_w": (1, 32)}}
    for modelo in secuencia.MODELOS:
        ok = sorted(juegos.get(modelo, {})) == sorted(comun.PLIEGUES)
        for pliegue in comun.PLIEGUES:
            p = juegos.get(modelo, {}).get(pliegue, {})
            ok = ok and all(p.get(k, np.zeros(0)).shape == f for k, f in formas[modelo].items())
            ok = ok and float(p.get("alfa", np.nan)) in comun.ALFAS
            ok = ok and p.get("rms", np.zeros(0)).shape == (secuencia.N_CANALES,) and bool((p["rms"] > 0).all())
            ok = ok and all(np.isfinite(v).all() for v in p.values())
        comprobar("{}: 8 pliegues con sus formas, α de la rejilla y rms positivo".format(modelo), ok,
                  "α: " + ", ".join("{:g}".format(float(juegos[modelo][p]["alfa"])) for p in comun.PLIEGUES
                                    if p in juegos.get(modelo, {})))


def comprobar_numpy():
    print("La predicción en numpy")
    rng = np.random.default_rng(11)
    p11 = secuencia.pesos_de("b11")
    p12 = secuencia.pesos_de("b12")
    for largo in (1, 2, 7, 300):
        x = rng.normal(size=(secuencia.N_CANALES, largo))
        for nombre, una, p in (("B11", secuencia.logit_b11, p11), ("B12", secuencia.logit_b12, p12)):
            z = una(x, p)
            comprobar("{}, tramo de {} frames: z finito y antisimétrico exacto".format(nombre, largo),
                      z.shape == (largo,) and np.isfinite(z).all()
                      and np.array_equal(una(secuencia.espejo(x), p), -z + 0.0))
    h = rng.normal(size=(3, 40))
    w, b = rng.normal(size=(4, 3, 3)), rng.normal(size=4)
    comprobar("la convolución con dilación 4 es la de una versión a mano",
              np.allclose(secuencia._conv(h[None], w, b, 4)[0], conv_a_mano(h, w, b, 4), rtol=0, atol=1e-12))
    x5 = rng.normal(size=(secuencia.N_CANALES, 30))
    gi = secuencia._entrada(x5, p12["w_ih"], p12["b_ih"])[None]
    propia = secuencia._gru(gi, p12["w_hh"][None], p12["b_hh"][None])[0]
    comprobar("la GRU es la de una versión a mano con las ecuaciones de torch",
              np.allclose(propia, gru_a_mano(x5, p12["w_ih"], p12["b_ih"], p12["w_hh"], p12["b_hh"]), rtol=0,
                          atol=1e-12))
    rampa = np.tile(np.arange(23, dtype=np.float64), (2, 1))
    comprobar("agrupar y desagrupar: medias de 5 frames y una rampa vuelve a ser la rampa",
              np.array_equal(secuencia.agrupar(rampa)[0], [2.0, 7.0, 12.0, 17.0, 21.0])
              and np.allclose(secuencia.desagrupar(secuencia.agrupar(rampa)[0], 23), np.r_[[2.0, 2.0],
                              np.arange(2, 22, dtype=np.float64), [21.0]]))


def comprobar_torch():
    try:
        import torch
        import entrenar_red
    except ImportError:
        print("Sin torch en este entorno: la comparación con torch no se hace aquí (la imprime entrenar_red.py).")
        return
    print("numpy frente a torch, con los pesos guardados")
    rng = np.random.default_rng(5)
    x = rng.normal(size=(secuencia.N_CANALES, 700))
    for modelo in secuencia.MODELOS:
        p = secuencia.pesos_de(modelo)
        if modelo == "b11":
            red = entrenar_red.B11(secuencia.N_CANALES, comun.B11["canales"])
            estado = {"entrada.weight": p["entrada_w"], "entrada.bias": p["entrada_b"],
                      "salida.weight": p["salida_w"], "salida.bias": p["salida_b"]}
            for j in range(len(secuencia.DILACIONES)):
                estado["bloques.{}.weight".format(j)] = p["bloque{}_w".format(j)]
                estado["bloques.{}.bias".format(j)] = p["bloque{}_b".format(j)]
        else:
            red = entrenar_red.B12(secuencia.N_CANALES, comun.B12["oculto"])
            estado = {"salida.weight": p["salida_w"], "salida.bias": p["salida_b"]}
            for nombre, sufijo in (("delante", ""), ("detras", "_r")):
                for parte in ("ih", "hh"):
                    estado["{}.weight_{}_l0".format(nombre, parte)] = p["w_{}{}".format(parte, sufijo)]
                    estado["{}.bias_{}_l0".format(nombre, parte)] = p["b_{}{}".format(parte, sufijo)]
        red.load_state_dict({k: torch.tensor(v, dtype=torch.float32) for k, v in estado.items()})
        s = {"x": x, "y": np.zeros(700, np.float32), "m": np.zeros(700, bool)}
        z_t = entrenar_red.z_torch(modelo, red, s)
        z_n = (secuencia.logit_b11 if modelo == "b11" else secuencia.logit_b12)(x, p)
        dif = float(np.max(np.abs(z_t - z_n)))
        comprobar("{}: numpy (float64) da lo mismo que torch (float32)".format(modelo), dif < 1e-4,
                  "diferencia máxima de z {:.1e}".format(dif))


def comprobar_evidencia():
    trk = puntuar.partido_de_prueba()
    fuera_de_tramos = np.ones(len(trk.bx), bool)
    for inicio, fin in trk.blocks:
        fuera_de_tramos[inicio:fin] = False
    for nombre, funcion, modelo in (("B11", aprendida.evidence_b11, "b11"), ("B12", aprendida.evidence_b12, "b12")):
        print(nombre)
        score, allowed = funcion(trk)
        comprobar("arrays (n, 3), puntuación finita y todo permitido",
                  score.shape == (len(trk.bx), 3) and allowed.shape == score.shape
                  and np.isfinite(score).all() and allowed.all())
        comprobar("la columna D a cero y cero fuera de los tramos",
                  (score[:, tracking.D] == 0).all() and (score[fuera_de_tramos] == 0).all())
        comprobar("opina en los tramos", bool((score[~fuera_de_tramos, :2] != 0).any()))
        comprobar("aprendida.evidence_{} es secuencia.evidencia".format(modelo),
                  np.array_equal(score, secuencia.evidencia(trk, modelo)[0]))
        otra, _ = funcion(trk)
        comprobar("dos ejecuciones dan lo mismo", np.array_equal(score, otra))
        cambiado, _ = funcion(trk._replace(team=(1 - trk.team).astype(np.int8)))
        comprobar("cambiar los equipos intercambia H y A exactamente",
                  np.array_equal(cambiado[:, tracking.H], score[:, tracking.A])
                  and np.array_equal(cambiado[:, tracking.A], score[:, tracking.H]))
        orden = np.random.default_rng(7).permutation(trk.px.shape[1])
        permutado, _ = funcion(trk._replace(px=trk.px[:, orden], py=trk.py[:, orden], team=trk.team[orden]))
        dif = float(np.abs(permutado - score).max())
        comprobar("una permutación fija de los slots no cambia la puntuación (1e-6 como mucho)", dif <= 1e-6,
                  "máx. {:.1e}".format(dif))
        comprobar("los 7 pliegues dan una puntuación finita",
                  all(np.isfinite(funcion(trk, fuera=p)[0]).all() for p in comun.PARTIDOS))


def main():
    comprobar_pesos()
    comprobar_numpy()
    comprobar_torch()
    comprobar_evidencia()
    print("\n{}".format("Todo bien." if not fallos else "FALLAN {}: {}".format(len(fallos), "; ".join(fallos))))
    return 1 if fallos else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
