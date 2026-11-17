"""Prueba B13 a B17 (possession/trayectorias.py y trayectorias2.py) sin cargar ningún partido.

    python validation/scripts/prueba_trayectorias.py

Con el partido inventado del harness (`puntuar.partido_de_prueba`) comprueba, para cada red con pesos en el repo:

- la interfaz: arrays (n, 3), puntuación finita, columna `D` a cero, cero fuera de los tramos y todo permitido;
- el determinismo: dos ejecuciones dan lo mismo;
- la antisimetría: cambiar los equipos intercambia `H` y `A` exactamente;
- que una permutación fija de los slots no cambia la puntuación (1e-6 como mucho);
- que todos los pliegues dan una puntuación finita;
- que un salto del balón de más de 42 m/s no entra como velocidad (`TOPE_VEL_BALON`).

La comparación con torch (la red del entrenamiento) la imprime cada entrenamiento al acabar (`entrenar.py`, `entrenar2.py`).
No usa datos del partido ni de la DFL. Sale con código 1 si falla alguna comprobación. Claude puede ejecutarlo.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import puntuar  # noqa: E402
from possession import aprendida, tracking, trayectorias, trayectorias2  # noqa: E402

PARTIDOS = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
REDES = (("B13", aprendida.evidence_b13, trayectorias.PESOS, PARTIDOS),
         ("B14", aprendida.evidence_b14, trayectorias2.PESOS, PARTIDOS),
         ("B15", aprendida.evidence_b15, trayectorias2.PESOS_B15, PARTIDOS),
         ("B16", aprendida.evidence_b16, trayectorias2.PESOS_B16, PARTIDOS + ("scA", "scB")),
         ("B17", aprendida.evidence_b17, trayectorias2.PESOS_B16, PARTIDOS))
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
    for nombre, funcion, ruta, pliegues in REDES:
        print(nombre)
        if not os.path.isfile(ruta):
            comprobar("hay pesos en {}".format(os.path.basename(ruta)), False)
            continue
        score, allowed = funcion(trk)
        comprobar("arrays (n, 3), puntuación finita y todo permitido",
                  score.shape == (len(trk.bx), 3) and allowed.shape == score.shape
                  and np.isfinite(score).all() and allowed.all())
        comprobar("la columna D a cero y cero fuera de los tramos",
                  (score[:, tracking.D] == 0).all() and (score[fuera_de_tramos] == 0).all())
        comprobar("opina en los tramos", bool((score[~fuera_de_tramos, :2] != 0).any()))
        comprobar("dos ejecuciones dan lo mismo", np.array_equal(score, funcion(trk)[0]))
        cambiado, _ = funcion(trk._replace(team=(1 - trk.team).astype(np.int8)))
        comprobar("cambiar los equipos intercambia H y A exactamente",
                  np.array_equal(cambiado[:, tracking.H], score[:, tracking.A])
                  and np.array_equal(cambiado[:, tracking.A], score[:, tracking.H]))
        orden = np.random.default_rng(7).permutation(trk.px.shape[1])
        permutado, _ = funcion(trk._replace(px=trk.px[:, orden], py=trk.py[:, orden], team=trk.team[orden]))
        dif = float(np.abs(permutado - score).max())
        comprobar("una permutación fija de los slots no cambia la puntuación (1e-6 como mucho)", dif <= 1e-6,
                  "máx. {:.1e}".format(dif))
        comprobar("todos los pliegues ({}) dan una puntuación finita".format(len(pliegues)),
                  all(np.isfinite(funcion(trk, fuera=p)[0]).all() for p in pliegues))
    print("El tope de la velocidad del balón")
    bx = np.array(trk.bx, copy=True)
    bx[200:205] += np.array([0.0, 10.0, 20.0, 30.0, 40.0])
    bx[205:] += 40.0
    con_salto = trk._replace(bx=np.clip(bx, 0.0, 105.0))
    for modulo in (trayectorias, trayectorias2):
        r, _, _ = modulo.rasgos_tramo(con_salto, *con_salto.blocks[0])
        b = r[tracking.H][2]
        maximo = float(15.0 * np.hypot(b[:, 2], b[:, 3]).max())
        comprobar("{}: un salto de 40 m en 4 frames no entra como velocidad".format(modulo.__name__.split(".")[-1]),
                  maximo <= trayectorias.TOPE_VEL_BALON, "máx. {:.1f} m/s".format(maximo))
    print("\n{}".format("Todo bien." if not fallos else "FALLAN {}: {}".format(len(fallos), "; ".join(fallos))))
    return 1 if fallos else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
