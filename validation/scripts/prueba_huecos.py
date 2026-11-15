"""Prueba `validation/posesiones_cortas/huecos.py` y la regla de `validation/partido/huecos_y_cambios.py` con datos
inventados de resultado conocido. No lee nada del partido.

    python validation/scripts/prueba_huecos.py
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "posesiones_cortas"), os.path.join(ROOT, "validation", "partido"),
                 os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import huecos  # noqa: E402
import huecos_y_cambios as hc  # noqa: E402

H, A, D = huecos.H, huecos.A, huecos.D
fallos = []


def comprobar(texto, condicion):
    print("  [{}] {}".format("OK" if condicion else "FALLA", texto))
    if not condicion:
        fallos.append(texto)


def main():
    # 1.000 frames: H hasta 399, A de 400 a 699, D de 700 a 749, A de 750 a 851 y H desde 852.
    codes = np.full(1000, H, dtype=np.int8)
    codes[400:700] = A
    codes[700:750] = D
    codes[750:852] = A
    visible = np.ones(1000, bool)
    for s, e in ((380, 410), (600, 620), (690, 705), (830, 848), (900, 905)):
        visible[s:e] = False
    acc = huecos.medir(codes, visible, ((0, 1000),))
    print("Recuentos")
    comprobar("un hueco de 30 frames con el cambio dentro", acc[("hueco", "0,5–2 s", "huecos")] == 3
              and acc[("hueco", "0,5–2 s", "con cambio")] == 2 and acc[("hueco", "0,5–2 s", "cambio dentro")] == 1)
    comprobar("un hueco de 18 frames con el cambio 4 frames después de reaparecer",
              acc[("hueco", "0,5–2 s", "cambio al reaparecer")] == 1)
    comprobar("un hueco de 5 frames sin cambio", acc[("hueco", "≤ 0,5 s", "huecos")] == 1
              and acc[("hueco", "≤ 0,5 s", "con cambio")] == 0)
    comprobar("el hueco que toca un D no cuenta", acc["huecos pegados a un D o al borde"] == 1)
    comprobar("dos cambios H↔A (el de D a A no cuenta): uno dentro y otro al reaparecer",
              acc["cambios"] == 2 and acc["cambios dentro de un hueco"] == 1 and acc["cambios al reaparecer"] == 1
              and acc["cambios en otro sitio"] == 0)
    comprobar("frames de juego y al azar: 950, 68 dentro y 39 al reaparecer",
              acc["frames de juego"] == 950 and acc["frames de juego dentro de un hueco"] == 68
              and acc["frames de juego al reaparecer"] == 39)
    m, azar, r = huecos.razon(acc)
    comprobar("M = 100 %, al azar = 107/950 y R = M / azar", abs(m - 100.0) < 1e-9 and abs(azar - 100.0 * 107 / 950) < 1e-9
              and abs(r - m / azar) < 1e-9)
    comprobar("la salida del partido suprime las celdas de 1 a 4", any("< 5" in l for l in huecos.lineas("x", acc, True))
              and not any("< 5" in l for l in huecos.lineas("x", acc, False)))
    print("Regla")

    def acc_con(cambios, dentro, frames, frames_dentro, n_huecos, con_cambio):
        a = huecos.nuevo()
        a.update({"cambios": cambios, "cambios dentro de un hueco": dentro, "frames de juego": frames,
                  "frames de juego dentro de un hueco": frames_dentro, ("hueco", "0,5–2 s", "huecos"): n_huecos,
                  ("hueco", "0,5–2 s", "con cambio"): con_cambio})
        return a

    def dice(partido):
        return "\n".join(hc.veredicto(partido, dfl))
    dfl = acc_con(1000, 100, 100000, 5000, 1000, 100)  # R = 10 / 5 = 2; F = 10 %
    comprobar("se cierra con el mismo R y la misma F", "Se cierra" in dice(acc_con(200, 20, 10000, 500, 100, 10)))
    comprobar("queda abierta con 1,5 veces R", "Queda abierta" in dice(acc_con(200, 30, 10000, 500, 100, 10)))
    comprobar("queda abierta con 1,5 veces F", "Queda abierta" in dice(acc_con(200, 20, 10000, 500, 100, 15)))
    comprobar("no concluye con R entre 1,25 y 1,5", "No concluye" in dice(acc_con(200, 27, 10000, 500, 100, 10)))
    comprobar("no concluye con menos de 20 casos", "menos de 20" in dice(acc_con(100, 19, 10000, 100, 100, 10)))
    pequeno = acc_con(200, 20, 10000, 500, 23, 4)  # 4 huecos con cambio de 23: F dejaría ver la celda
    comprobar("F del partido no se imprime con 1 a 4 huecos con cambio",
              any("F: menos de 5 casos" in l for l in huecos.lineas("x", pequeno, True))
              and "no se imprime" in dice(pequeno) and "17,4" not in dice(pequeno))
    print()
    if fallos:
        print("FALLAN {} comprobaciones".format(len(fallos)))
        sys.exit(1)
    print("TODO BIEN")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
