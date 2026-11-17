"""Empaqueta los rasgos de B14 (de `exportar2.py`) en .npy sin comprimir, para abrirlos con memmap al entrenar.

    python validation/trayectorias/paquetes.py

Los presentes de cada frame van al principio y todo se rellena hasta el mismo número de slots, en float16. Los
procesos de entrenamiento abren los .npy con memmap y comparten la caché del sistema, así que caben varios pliegues a
la vez. Datos abiertos de la DFL; fuera del repo. Solo imprime agregados.
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rutas  # noqa: E402

PARTIDOS = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
COPIAS = (0, 1, 2)
CLAVES = ("H_propios", "H_rivales", "A_propios", "A_rivales", "H_balon", "A_balon", "hay_h", "hay_a", "y", "m")


def fichero_npz(partido, condicion, copia):
    return rutas.carpeta() / "rasgos2_{}_{}_c{}.npz".format(partido, rutas.CONDICIONES.index(condicion), copia)


def carpeta():
    return rutas.carpeta() / "paquetes"


def nombre(partido, condicion, copia, parte, clave):
    return carpeta() / "{}_{}_c{}_{}_{}.npy".format(partido, rutas.CONDICIONES.index(condicion), copia, parte, clave)


def nombre_control(partido, parte, clave):
    """Las etiquetas de control de B15 (`etiquetas_control.py`): las mismas en todas las copias y condiciones."""
    return carpeta() / "{}_control_{}_{}.npy".format(partido, parte, clave)


def empaquetar(c, s):
    for mascara, claves in (("hay_h", ("H_propios", "A_rivales")), ("hay_a", ("A_propios", "H_rivales"))):
        m = c[mascara]
        orden = np.argsort(~m, axis=1, kind="stable")[:, :s]
        if orden.shape[1] < s:
            orden = np.concatenate([orden, np.full((len(m), s - orden.shape[1]), -1)], axis=1)
        valido = orden >= 0
        o = np.where(valido, orden, 0)
        c[mascara] = np.take_along_axis(m, o, axis=1) & valido
        for clave in claves:
            x = np.take_along_axis(c[clave], o[:, :, None], axis=1)
            c[clave] = np.where(valido[:, :, None], x, 0.0).astype(np.float16)
    for clave in ("H_balon", "A_balon"):
        c[clave] = c[clave].astype(np.float16)


def main():
    carpeta().mkdir(parents=True, exist_ok=True)
    s = 0
    for partido in PARTIDOS:
        for condicion in rutas.CONDICIONES:
            for copia in COPIAS:
                with np.load(fichero_npz(partido, condicion, copia)) as d:
                    for clave in d.files:
                        if clave.endswith("_hay_h") or clave.endswith("_hay_a"):
                            s = max(s, int(d[clave].sum(axis=1).max()))
    print("slots por equipo tras empaquetar: {}".format(s), flush=True)
    for partido in PARTIDOS:
        for condicion in rutas.CONDICIONES:
            for copia in COPIAS:
                with np.load(fichero_npz(partido, condicion, copia)) as d:
                    k = 0
                    while "{}_y".format(k) in d.files:
                        c = {clave: d["{}_{}".format(k, clave)] for clave in CLAVES}
                        empaquetar(c, s)
                        for clave in CLAVES:
                            np.save(nombre(partido, condicion, copia, k, clave), c[clave])
                        k += 1
        print("empaquetado {}".format(partido), flush=True)


if __name__ == "__main__":
    main()
