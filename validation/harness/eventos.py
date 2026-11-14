"""Los eventos que anota una persona en la DFL, como puntos de control para el harness (sin circularidad).

Las etiquetas del harness salen del flag de la DFL ("flag") o de ese flag corregido con una regla de
proximidad ("control"). Una versión que se parezca a esa regla gana con ellas por construcción. Los
eventos humanos no dependen de nuestro tracking ni de nuestras reglas: un anotador los marcó viendo el
partido. Son la referencia del experimento 1 (`validation/experimento1/comparar_definiciones.py`), con sus
mismas guardas y retardos:

- **pase completado:** 5 frames después de que el receptor reciba, la etiqueta es del equipo del pasador;
- **recuperación:** 12 frames (0,5 s) después de la recuperación, es del equipo que recupera;
- **duelo con cambio** (`PossessionChange` = true, ganado con un toque, una recuperación o de primeras por
  el que no tenía el balón): 2 s después, es del que gana;
- **duelo sin cambio** (lo mismo con `PossessionChange` = false): 2 s después, sigue en el que lo tenía.

Los eventos se sitúan en el tracking limpio de la caché, nunca en el balón degradado, y una vez por partido.
Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0): lo puede ejecutar cualquiera.
"""

import glob
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
for _carpeta in ("experimento0", "experimento1"):
    sys.path.insert(0, os.path.join(AQUI, "..", _carpeta))
sys.path.insert(0, AQUI)
import dfl  # noqa: E402
import dfl_lector  # noqa: E402
from comparar_definiciones import VENTANA, cerca_del_balon, eventos_guardia  # noqa: E402
from duelos_dfl import duelos  # noqa: E402
from duelos_sincronizados import MAX_DIST, posiciones_por_persona, sincronizar  # noqa: E402
from parada3 import a_frame  # noqa: E402
from peso_correccion import RESULTADOS_TOQUE  # noqa: E402

FPS = 25
TIPOS = ("pase completado", "recuperación", "duelo con cambio", "duelo sin cambio")
RETARDO = {"pase completado": 5, "recuperación": 12, "duelo con cambio": 2 * FPS, "duelo sin cambio": 2 * FPS}
DIST_JUGADOR = 1.5  # m: pasador, receptor o recuperador junto al balón (experimento 1)


def fichero_de_eventos(partido):
    """Ruta del XML de eventos de la DFL. Da error claro si no está: el harness sin él sigue funcionando."""
    rutas = glob.glob(os.path.join(dfl_lector.carpeta_dfl(),
                                   "DFL_03_02_events_raw_*_DFL-MAT-{}.xml".format(partido)))
    if len(rutas) != 1:
        raise SystemExit("--eventos: no encuentro el XML de eventos de {} en {}. Se baja con "
                         "`python validation/scripts/descargar_datos_abiertos.py dfl`.".format(
                             partido, dfl_lector.carpeta_dfl()))
    return rutas[0]


def puntos_de_control(cargado, meta):
    """{"frame", "equipo", "tipo"}: arrays con un punto por evento situado, en el índice del harness.

    `cargado` es el de `dfl.cargar` (partes limpias); `meta`, el de la caché (`local_id`, `visitante_id`).
    El frame es el del `Tracking` de `dfl.tracking_de`: la 2ª parte empieza tras la 1ª y `dfl.HUECO`.
    """
    partes = cargado["partes"]
    desplazamiento = {1: 0, 2: len(partes[1]["estado"]) + dfl.HUECO}
    preparadas = {k: (partes[k], posiciones_por_persona(partes[k]), np.asarray(partes[k]["t_ms"], np.int64))
                  for k in (1, 2)}
    ruta = fichero_de_eventos(cargado["partido"])
    frames, equipos, tipos = [], [], []

    def buscar(ms):
        for k, (parte, pos, t_ms) in preparadas.items():
            if t_ms[0] <= ms <= t_ms[-1]:
                return k, parte, pos, t_ms
        return None

    def anotar(k, frame, equipo, tipo):
        frames.append(desplazamiento[k] + frame)
        equipos.append(equipo)
        tipos.append(TIPOS.index(tipo))

    for ms, x, a in duelos(ruta, meta):
        if x < 0 or a.get("WinnerRole") != "withoutBallControl" or a.get("WinnerResult") not in RESULTADOS_TOQUE:
            continue
        pc = a.get("PossessionChange")
        if pc not in ("true", "false"):
            continue
        hallado = buscar(ms)
        if hallado is None:
            continue
        k, parte, pos, t_ms = hallado
        f, dist = sincronizar(parte, pos, a_frame(t_ms, ms), a.get("Winner"), a.get("Loser"))
        if f is None or dist > MAX_DIST:
            continue
        estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
        f2 = f + RETARDO["duelo con cambio"]
        if f - 10 < 0 or f2 >= len(estado) or estado[f - 10] != 1 or poss[f - 10] - 1 != x or estado[f2] != 1:
            continue
        if pc == "true":
            anotar(k, f2, 1 - x, "duelo con cambio")
        else:
            anotar(k, f2, x, "duelo sin cambio")

    pases, recuperaciones = eventos_guardia(ruta, meta)
    for ms, pasador, receptor, equipo in pases:
        hallado = buscar(ms)
        if hallado is None:
            continue
        k, parte, pos, t_ms = hallado
        f0 = a_frame(t_ms, ms)
        fp, dp = cerca_del_balon(parte, pos, pasador, f0 - VENTANA, f0 + VENTANA + 1)
        if fp is None or dp > DIST_JUGADOR:
            continue
        fr, dr = cerca_del_balon(parte, pos, receptor, fp + 1, fp + VENTANA + 1)
        punto = None if fr is None else fr + RETARDO["pase completado"]
        if fr is None or dr > DIST_JUGADOR or punto >= len(parte["estado"]) or parte["estado"][punto] != 1:
            continue
        anotar(k, punto, equipo, "pase completado")
    for ms, jugador, equipo in recuperaciones:
        hallado = buscar(ms)
        if hallado is None:
            continue
        k, parte, pos, t_ms = hallado
        f0 = a_frame(t_ms, ms)
        fj, dj = cerca_del_balon(parte, pos, jugador, f0 - VENTANA, f0 + VENTANA + 1)
        punto = None if fj is None else fj + RETARDO["recuperación"]
        if fj is None or dj > DIST_JUGADOR or punto >= len(parte["estado"]) or parte["estado"][punto] != 1:
            continue
        anotar(k, punto, equipo, "recuperación")
    return {"frame": np.asarray(frames, dtype=np.int64), "equipo": np.asarray(equipos, dtype=np.int8),
            "tipo": np.asarray(tipos, dtype=np.int8)}


def aciertos(puntos, pred):
    """True donde la etiqueta predicha en el punto es el equipo esperado. Una `D` o una `X` es fallo."""
    return pred[puntos["frame"]] == puntos["equipo"]
