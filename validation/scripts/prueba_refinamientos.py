"""Prueba los refinamientos de K2 (possession/refinamientos.py: K3, K4 y K5) sin cargar ningún partido.

    python validation/scripts/prueba_refinamientos.py

Con el partido inventado del harness (`puntuar.partido_de_prueba`) y los pesos al azar de `prueba_conjunto.py`,
comprueba:

- que no cambian las piezas que combinan: el logit de K2 puntuado aquí da `conjunto.evidence` bit a bit, y el de B5,
  `aprendida.evidence_b5` bit a bit;
- la mezcla: con todo el peso en K2 es el logit de K2, con todo en B5 es el de B5, y a partes iguales es su media;
- el espejo: no toca x, los equipos ni los tramos, conserva los huecos, y K4 no cambia al poner el campo en espejo
  (salvo el redondeo);
- la interfaz de K3, K4 y K5: arrays (n, 3), puntuación finita, columna `D` a cero, cero fuera de los tramos y todo
  permitido; dos ejecuciones dan lo mismo bit a bit; no escriben en el tracking; cambiar los equipos intercambia las
  columnas `H` y `A`;
- que K3 es la evidencia de equipo de la entrega (`pipeline.PIECES`) y K4 y K5 no, que la entrega sin opciones da lo
  mismo que pasando K3 a mano, y que el pipeline corre con cada una;
- si están los pesos de verdad, que las tres corren con los de la entrega.

No usa datos del partido ni de la DFL. Sale con código 1 si falla alguna comprobación. Claude puede ejecutarlo.
"""

import os
import sys
import tempfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import puntuar  # noqa: E402
from prueba_conjunto import pesos_al_azar  # noqa: E402
from possession import aprendida, conjunto, pipeline, tracking  # noqa: E402
from possession import refinamientos as rf  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

fallos = []
CANDIDATOS = (("K3", rf.evidence_k3), ("K4", rf.evidence_k4), ("K5", rf.evidence_k5))


def comprobar(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(nombre)


def iguales(a, b):
    return bool(np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]))


def main():
    trk = puntuar.partido_de_prueba()
    n = len(trk.bx)
    dentro = np.zeros(n, dtype=bool)
    for a, b in trk.blocks:
        dentro[a:b] = True

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, "pesos.npz")
        juego = pesos_al_azar()
        np.savez(ruta, **{"todos/{}".format(k): v for k, v in juego.items()})
        de_verdad = conjunto.PESOS
        conjunto.PESOS = ruta
        conjunto._CACHE.clear()
        try:
            print("Con pesos al azar (semilla fija):")
            s_k2, s_b5 = rf.logit_k2(trk), rf.logit_b5(trk)
            comprobar("el logit de K2 puntuado aquí da `conjunto.evidence`, bit a bit",
                      iguales(rf.puntuar(s_k2, trk), conjunto.evidence(trk)))
            comprobar("el logit de B5 puntuado aquí da `aprendida.evidence_b5`, bit a bit",
                      iguales(rf.puntuar(s_b5, trk), aprendida.evidence_b5(trk)))
            comprobar("los dos logits opinan y no coinciden", bool(np.any(s_k2 != 0) and np.any(s_b5 != 0)
                                                                  and np.any(s_k2 != s_b5)))
            comprobar("la mezcla con todo el peso en K2 es el logit de K2",
                      np.array_equal(rf.mezclar(s_k2, s_b5, 1.0), s_k2))
            comprobar("la mezcla con todo el peso en B5 es el logit de B5",
                      np.array_equal(rf.mezclar(s_k2, s_b5, 0.0), s_b5))
            comprobar("la mezcla a partes iguales es la media", rf.PESO_K2 == 0.5
                      and np.array_equal(rf.mezclar(s_k2, s_b5), 0.5 * s_k2 + 0.5 * s_b5))

            espejo = rf.en_espejo(trk)
            ancho = trk.pitch[1]
            comprobar("el espejo no toca x, los equipos, el campo ni los tramos",
                      espejo.px is trk.px and espejo.bx is trk.bx and espejo.team is trk.team
                      and espejo.pitch == trk.pitch and espejo.blocks == trk.blocks and espejo.fps == trk.fps)
            comprobar("el espejo conserva los huecos y refleja y",
                      np.array_equal(np.isnan(espejo.py), np.isnan(trk.py))
                      and np.array_equal(np.isnan(espejo.by), np.isnan(trk.by))
                      and bool(np.allclose(np.nan_to_num(espejo.py) + np.nan_to_num(trk.py),
                                           np.where(np.isnan(trk.py), 0.0, ancho))))
            comprobar("el espejo cambia el logit de K2 (el modelo no es simétrico por construcción)",
                      bool(np.any(conjunto.salidas(espejo)[0] != conjunto.salidas(trk)[0])))
            k4, k4_espejo = rf.evidence_k4(trk), rf.evidence_k4(espejo)
            comprobar("K4 no cambia al poner el campo en espejo (salvo el redondeo)",
                      bool(np.allclose(k4[0], k4_espejo[0], atol=1e-5)),
                      "diferencia máxima {:.1e}".format(float(np.abs(k4[0] - k4_espejo[0]).max())))
            comprobar("K4 no es K2", not iguales(k4, conjunto.evidence(trk)))

            cambiado = trk._replace(team=(1 - np.asarray(trk.team)).astype(np.int8))
            for nombre, funcion in CANDIDATOS:
                score, allowed = funcion(trk)
                comprobar("{}: (n, 3), finita y todo permitido".format(nombre),
                          score.shape == (n, 3) and allowed.shape == (n, 3) and bool(np.isfinite(score).all())
                          and bool(allowed.all()))
                comprobar("{}: la columna D va a cero y no opina fuera de los tramos".format(nombre),
                          bool(np.all(score[:, tracking.D] == 0.0)) and bool(np.all(score[~dentro] == 0.0))
                          and bool(np.any(score[dentro, :2] != 0.0)))
                comprobar("{}: dos ejecuciones dan lo mismo, bit a bit".format(nombre), iguales(funcion(trk), (score, allowed)))
                otro, _ = funcion(cambiado)
                comprobar("{}: cambiar los equipos intercambia `H` y `A`".format(nombre),
                          bool(np.allclose(otro[:, [tracking.A, tracking.H, tracking.D]], score, atol=1e-5)),
                          "diferencia máxima {:.1e}".format(
                              float(np.abs(otro[:, [tracking.A, tracking.H, tracking.D]] - score).max())))
                codigos = pipeline.run(trk, pieces={"candidates": funcion})
                comprobar("{}: el pipeline entero corre con ella".format(nombre), len(codigos) == n)
            comprobar("K3 no es ni K2 ni B5", not iguales(rf.evidence_k3(trk), conjunto.evidence(trk))
                      and not iguales(rf.evidence_k3(trk), aprendida.evidence_b5(trk)))
            comprobar("K3 es la evidencia de equipo de la entrega (`pipeline.PIECES`), y K4 y K5 no están",
                      pipeline.PIECES["candidates"] == "aprendida.evidence_k3"
                      and pipeline.default_piece("candidates") is aprendida.evidence_k3
                      and all("k4" not in valor and "k5" not in valor for valor in pipeline.PIECES.values()))
            comprobar("el envoltorio `aprendida.evidence_k3` es `refinamientos.evidence_k3`",
                      iguales(aprendida.evidence_k3(trk), rf.evidence_k3(trk)))
            comprobar("la entrega sin opciones da lo mismo que pasando K3 a mano (como en `--pieza`)",
                      np.array_equal(pipeline.run(trk),
                                     pipeline.run(trk, pieces={"candidates": aprendida.evidence_k3})))
        finally:
            conjunto.PESOS = de_verdad
            conjunto._CACHE.clear()

    if os.path.isfile(conjunto.PESOS):
        print("Con los pesos de verdad (los de la entrega):")
        for nombre, funcion in CANDIDATOS:
            score, _ = funcion(trk)
            comprobar("{} corre con los pesos de la entrega".format(nombre),
                      bool(np.isfinite(score).all()) and bool(np.any(score[dentro, :2] != 0.0)))
        comprobar("con los pesos de verdad, K2 puntuado aquí sigue dando `conjunto.evidence`, bit a bit",
                  iguales(rf.puntuar(rf.logit_k2(trk), trk), conjunto.evidence(trk)))
    else:
        print("No están los pesos de verdad ({}): esa parte no se comprueba.".format(os.path.basename(conjunto.PESOS)))

    if fallos:
        print("\nFALLAN {}: {}".format(len(fallos), "; ".join(fallos)))
        sys.exit(1)
    print("\nTodo bien.")


if __name__ == "__main__":
    main()
