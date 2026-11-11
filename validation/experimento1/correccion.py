"""Corrección R(c) de las etiquetas de equipo de la DFL con una definición de control c.

Definida en `validation/experimento1/BITACORA.md` (sección 5) antes de calcularla:

1. rachas del flag (equipo 0, equipo 1 y `D` = 2);
2. una racha de equipo que sigue a un `D` o abre la parte se queda (tras un reinicio hay un poseedor
   claro);
3. una racha del equipo Y que sigue a una del equipo X se queda solo si Y tiene control según c en algún
   frame de la racha; si no, pasa a X (la posesión sigue con el último equipo que la tuvo);
4. se recorre en orden; el `D` no cambia.

Funciones puras de numpy: las definiciones de control llegan como intervalos [inicio, fin) por equipo.
"""

import numpy as np

import medidas_cambios as mc


def corregir(lab, control):
    """lab: array con 0, 1 o 2 (`D`) por frame. control: {equipo: (inicios, fines)}. Devuelve una copia."""
    lab = np.asarray(lab).copy()
    runs = mc.rachas(lab, 1)
    actual = None  # equipo en posesión tras corregir
    for i, (a, b, v) in enumerate(runs):
        if v == 2:
            actual = None
            continue
        if actual is None or v == actual:
            actual = v
            continue
        ini, fin = control.get(v, (np.array([], int), np.array([], int)))
        if mc._solapa((ini, fin), a, b):
            actual = v
        else:
            lab[a:b] = actual
    return lab


def intervalos(segs):
    """[(inicio, fin, equipo, ...)] → {equipo: (inicios, fines)}."""
    return mc._por_equipo(segs)


def dos_toques(t, eq, ventana=50):
    """Intervalos [t_i, t_j + 1) de dos toques seguidos del mismo equipo a ≤ ventana frames sin toque del otro."""
    segs = []
    sel = np.flatnonzero(np.asarray(eq) >= 0)
    t, eq = np.asarray(t)[sel], np.asarray(eq)[sel]
    for i in range(len(t) - 1):
        if eq[i] == eq[i + 1] and t[i + 1] - t[i] <= ventana:
            segs.append((int(t[i]), int(t[i + 1]) + 1, int(eq[i])))
    return segs


def unir(*dicts):
    """Unión de varias definiciones de control (intervalos por equipo)."""
    salida = {}
    for k in (0, 1):
        ini = np.concatenate([d[k][0] for d in dicts]) if dicts else np.array([], int)
        fin = np.concatenate([d[k][1] for d in dicts]) if dicts else np.array([], int)
        salida[k] = (ini, fin)
    return salida


def prueba():
    """Prueba sintética: una racha corta del rival sin control desaparece; con control o tras un D, se queda."""
    lab = np.array([0] * 10 + [1] * 3 + [0] * 10 + [1] * 6 + [2] * 4 + [1] * 5 + [0] * 3 + [1] * 4)
    # control del equipo 1 solo en la racha de 6 (frames 23–28); ninguno en las de 3 y 4 ni en la de 3 del 0
    control = {0: (np.array([], int), np.array([], int)), 1: (np.array([24]), np.array([27]))}
    r = corregir(lab, control)
    esperado = np.array([0] * 10 + [0] * 3 + [0] * 10 + [1] * 6 + [2] * 4 + [1] * 5 + [1] * 3 + [1] * 4)
    assert (r == esperado).all(), r
    assert dos_toques([10, 20, 30, 90, 95], [1, 1, 0, 0, 0]) == [(10, 21, 1), (90, 96, 0)]
    print("corrección: OK")


if __name__ == "__main__":
    prueba()
