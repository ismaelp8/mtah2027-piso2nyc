"""Calcula los rasgos de B14 (possession/trayectorias2.py) en tres copias de cada partido de la DFL.

    python validation/trayectorias/exportar2.py [--partidos J03WMX ...]

Datos abiertos de otros partidos (DFL, CC BY 4.0). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime
agregados. Las etiquetas salen siempre del tracking limpio (`dfl.cargar`).

- **Copia 0:** el tracking del harness (`dfl.tracking_de`), en las dos condiciones que votan.
- **Copias 1 y 2 (dominio aleatorizado como el ATD):**
  - el balón con la condición y otra semilla, y además con un retraso entero de 0 a 6 frames por parte (el ATD lo
    trae unos 4 frames tarde, de +2 a +5); después se vuelve a tapar en los `D` y sus bordes, como en el harness;
  - los jugadores suavizados y con huecos como los del ATD (`validation/apuesta_b/jugadores.py`), con la variante
    que toca a cada partido y copia (al azar, en las aglomeraciones o lejos de la jugada);
  - los tracklets cortados y slots fantasma como los del ATD (`validation/investigacion_1116/slots_dfl.py`).

Guarda, fuera del repo (`rutas.carpeta()`), una entrada por partido, condición, copia y parte.
"""

import argparse
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "apuesta_b"),
                 os.path.join(ROOT, "validation", "investigacion_1116"), os.path.join(ROOT, "validation", "perfil_atd")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import jugadores  # noqa: E402
import rutas  # noqa: E402
import slots_dfl  # noqa: E402
from possession import ball, trayectorias2  # noqa: E402
from possession.tracking import A, H  # noqa: E402

SEMILLA = 20261118
COPIAS = (0, 1, 2)
RETRASO_MAX = 6  # frames


def fichero(partido, condicion, copia):
    return rutas.carpeta() / "rasgos2_{}_{}_c{}.npz".format(partido, rutas.CONDICIONES.index(condicion), copia)


def retrasar_y_tapar(parte_degradada, limpia, retraso):
    """El balón `retraso` frames tarde y tapado otra vez en los `D` y sus bordes (como `dfl.degradar_con`)."""
    x = np.asarray(parte_degradada["x"], dtype=float).copy()
    y = np.asarray(parte_degradada["y"], dtype=float).copy()
    if retraso:
        x = np.concatenate([np.full(retraso, np.nan), x[:-retraso]])
        y = np.concatenate([np.full(retraso, np.nan), y[:-retraso]])
    activo = np.asarray(limpia["estado"]) == 1
    tapado = np.convolve((~activo).astype(int), np.ones(2 * dfl.BORDE + 1, dtype=int), mode="same") > 0
    x[tapado], y[tapado] = np.nan, np.nan
    nueva = dict(parte_degradada)
    nueva["x"], nueva["y"] = x, y
    return nueva


def tracking_copia(cargado, condicion, copia):
    if copia == 0:
        return dfl.tracking_de(cargado, condicion), {}
    indice = cargado["indice"]
    variante = jugadores.VARIANTES[(indice + copia - 1) % len(jugadores.VARIANTES)]
    partes, retrasos = {}, []
    for k in (1, 2):
        limpia = cargado["partes"][k]
        rng = np.random.default_rng([SEMILLA, indice, k, copia])
        con_balon = dfl.degradar_parte(limpia, condicion, rng)
        retraso = int(rng.integers(0, RETRASO_MAX + 1))
        retrasos.append(retraso)
        con_balon = retrasar_y_tapar(con_balon, limpia, retraso)
        con_balon["equipos"] = jugadores.jugadores_degradados(
            limpia, variante, jugadores.CALIBRADO[variante], np.random.default_rng([SEMILLA, indice, k, copia, 7]),
            (cargado["partido"], k))
        partes[k] = con_balon
    trk = dfl.a_tracking(partes, cargado["campo"], np.random.default_rng([dfl.SEMILLA, indice, 99]))
    rng = np.random.default_rng([SEMILLA, indice, copia, 33])
    trk = slots_dfl.cortar_tracklets(trk, rng)
    trk, _ = slots_dfl.anadir_fantasmas(trk, rng)
    return trk, {"variante": variante, "retrasos": retrasos}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), choices=list(dfl.PARTIDOS))
    args = parser.parse_args()
    if tuple(dfl.VOTAN) != rutas.CONDICIONES:
        raise AssertionError("rutas.CONDICIONES no son las del harness")
    rutas.carpeta().mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    for partido in args.partidos:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        etiqueta = (gt["flag"] == H).astype(np.int8)
        mascara = (gt["flag"] == gt["control"]) & np.isin(gt["flag"], (H, A))
        for condicion in dfl.VOTAN:
            for copia in COPIAS:
                trk, info = tracking_copia(cargado, condicion, copia)
                trk = ball.clean(trk)
                guardar = {}
                for k, (a, b) in enumerate(trk.blocks):
                    r, hay_h, hay_a = trayectorias2.rasgos_tramo(trk, a, b)
                    for persp, nombre in ((H, "H"), (A, "A")):
                        for j, parte in enumerate(("propios", "rivales", "balon")):
                            guardar["{}_{}_{}".format(k, nombre, parte)] = r[persp][j].astype(np.float32)
                    guardar["{}_hay_h".format(k)] = hay_h
                    guardar["{}_hay_a".format(k)] = hay_a
                    guardar["{}_y".format(k)] = etiqueta[a:b]
                    guardar["{}_m".format(k)] = mascara[a:b]
                np.savez_compressed(fichero(partido, condicion, copia), **guardar)
                vivos = np.isin(gt["flag"], (H, A))
                print("{} · {} · copia {}{}: {} slots ({} H, {} A), balón visible en el {:.1f} % de los vivos · {:.0f} s"
                      .format(partido, condicion, copia, " ({}, retrasos {})".format(info["variante"], info["retrasos"])
                              if info else "", len(trk.team), int((trk.team == H).sum()), int((trk.team == A).sum()),
                              100.0 * float(np.mean(np.isfinite(trk.bx)[vivos])), time.time() - inicio), flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
