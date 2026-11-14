"""Prueba la evidencia aprendida de la apuesta B (possession/aprendida.py) sin cargar ningún partido.

    python validation/scripts/prueba_aprendida.py

Con el partido inventado del harness (`puntuar.partido_de_prueba`) comprueba:

- la interfaz: arrays (n, 3), puntuación finita, columna `D` a cero, cero fuera de los tramos y todo
  permitido;
- el determinismo: dos ejecuciones dan lo mismo;
- la simetría: cambiar los equipos intercambia `H` y `A` exactamente;
- que no depende del orden de los slots: una permutación fija da la misma puntuación tras redondear;
- los coeficientes: los 16 juegos (B1 y B2; los 7 partidos y un pliegue sin cada partido), con tantos
  pesos como rasgos, y el bloque del módulo es el que escribe `validation/apuesta_b/entrenar.py`.

No usa datos del partido ni de la DFL. Sale con código 1 si falla alguna comprobación. Claude puede
ejecutarlo.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, os.path.join(ROOT, "validation", "apuesta_b"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import entrenar  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, tracking  # noqa: E402

fallos = []


def comprobar(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(nombre)


def main():
    trk = puntuar.partido_de_prueba()
    fuera_de_tramos = np.ones(len(trk.bx), bool)
    for inicio, fin in trk.blocks:
        fuera_de_tramos[inicio:fin] = False
    for nombre, funcion in (("B1", aprendida.evidence_b1), ("B2", aprendida.evidence_b2)):
        print(nombre)
        score, allowed = funcion(trk)
        comprobar("arrays (n, 3), puntuación finita y todo permitido",
                  score.shape == (len(trk.bx), 3) and allowed.shape == score.shape
                  and np.isfinite(score).all() and allowed.all())
        comprobar("la columna D a cero y cero fuera de los tramos",
                  (score[:, tracking.D] == 0).all() and (score[fuera_de_tramos] == 0).all())
        comprobar("opina en los tramos", bool((score[~fuera_de_tramos, :2] > 0).any()))
        otra, _ = funcion(trk)
        comprobar("dos ejecuciones dan lo mismo", np.array_equal(score, otra))
        cambiado, _ = funcion(trk._replace(team=(1 - trk.team).astype(np.int8)))
        comprobar("cambiar los equipos intercambia H y A exactamente",
                  np.array_equal(cambiado[:, tracking.H], score[:, tracking.A])
                  and np.array_equal(cambiado[:, tracking.A], score[:, tracking.H]))
        orden = np.random.default_rng(7).permutation(trk.px.shape[1])
        permutado, _ = funcion(trk._replace(px=trk.px[:, orden], py=trk.py[:, orden], team=trk.team[orden]))
        comprobar("una permutación fija de los slots no cambia la puntuación (tras redondear)",
                  np.array_equal(permutado, score), "máx. {:.1e}".format(float(np.abs(permutado - score).max())))
        for partido in dfl.PARTIDOS:
            if not np.isfinite(funcion(trk, fuera=partido)[0]).all():
                comprobar("el pliegue sin {} da una puntuación finita".format(partido), False)
    print("Coeficientes")
    claves = {"todos"} | set(dfl.PARTIDOS)
    for conjunto in aprendida.CONJUNTOS:
        juegos = aprendida.COEFICIENTES.get(conjunto, {})
        comprobar("{}: los 7 partidos y un pliegue sin cada uno".format(conjunto), set(juegos) == claves)
        comprobar("{}: tantos pesos como rasgos y α positiva".format(conjunto),
                  all(len(j["pesos"]) == len(aprendida.NOMBRES[conjunto]) and j["alfa"] > 0 for j in juegos.values()))
    modelos = {c: {k: (j["alfa"], j["pesos"]) for k, j in aprendida.COEFICIENTES[c].items()}
               for c in aprendida.CONJUNTOS}
    with open(entrenar.MODULO, encoding="utf-8") as handle:
        texto = handle.read()
    comprobar("el bloque del módulo es el que escribe entrenar.py",
              "\n".join(entrenar.bloque_de_coeficientes(modelos)) in texto)
    try:
        aprendida.coeficientes("b1", "J00000")
        sin_pliegue = False
    except KeyError:
        sin_pliegue = True
    comprobar("un pliegue que no existe da error", sin_pliegue)
    print()
    if fallos:
        print("FALLAN {} comprobaciones".format(len(fallos)))
        sys.exit(1)
    print("TODO BIEN")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
