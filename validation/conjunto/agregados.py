"""Agregados de las entradas y de las salidas del modelo conjunto sobre un `Tracking`. Sin etiquetas.

No se ejecuta solo. Lo usan `referencia.py` (los 17 partidos abiertos, lo ejecuta cualquiera) y
`validation/partido/conjunto_en_el_partido.py` (el ATD del partido, **lo ejecuta una persona**), para comparar lo
que ve y lo que dice el modelo en el partido con lo que ve y dice en los datos con los que se entrenó.

`agregados(trk, fuera)` devuelve un diccionario {nombre: número}: solo medianas, percentiles, medias y porcentajes
sobre decenas de miles de grupos o frames. Nada por frame.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from possession import aprendida, conjunto  # noqa: E402
from possession.tracking import A, H  # noqa: E402

POR_SLOT = ("x respecto al balón", "y respecto al balón", "núcleo 1 m", "núcleo 2,5 m", "núcleo 6 m",
            "distancia al balón con tope", "velocidad x", "velocidad y", "velocidad x respecto al balón",
            "velocidad y respecto al balón", "x en el campo", "y en el campo", "se acerca al balón",
            "parte del grupo presente")
IMPARES = ("balón: x en la dirección de ataque", "balón: velocidad x", "balón: y", "balón: velocidad y")
PARES = ("balón visible", "balón: rapidez", "balón: distancia al eje")
UMBRAL_CAMBIO = 0.5


def _cuantiles(valores):
    if len(valores) == 0:
        return float("nan"), float("nan")
    return float(np.percentile(valores, 50)), float(np.percentile(valores, 90))


def agregados(trk, fuera=None):
    """{nombre: número} de un tracking, con los pesos del pliegue `fuera` (`None`: el de todos, la entrega)."""
    salida = {}
    team = np.asarray(trk.team)
    por_slot = [[] for _ in POR_SLOT]
    por_grupo = [[] for _ in IMPARES + PARES]
    presentes = {H: [], A: []}
    for inicio, fin in trk.blocks:
        entradas, hay, impares, pares = conjunto.entradas(
            trk.bx[inicio:fin], trk.by[inicio:fin], trk.px[inicio:fin], trk.py[inicio:fin], trk.team,
            trk.pitch[0], trk.pitch[1], trk.fps)
        for k, valores in enumerate(entradas):
            por_slot[k].append(np.abs(valores[hay]))
        for k, valores in enumerate(impares + pares):
            por_grupo[k].append(np.abs(valores))
        for equipo in (H, A):
            presentes[equipo].append(hay[:, team == equipo].sum(axis=1))
    for nombre, trozos in zip(POR_SLOT, por_slot):
        mediana, p90 = _cuantiles(np.concatenate(trozos))
        salida["entrada por jugador · {} · mediana".format(nombre)] = mediana
        salida["entrada por jugador · {} · p90".format(nombre)] = p90
    for nombre, trozos in zip(IMPARES + PARES, por_grupo):
        mediana, p90 = _cuantiles(np.concatenate(trozos))
        salida["entrada por grupo · {} · mediana".format(nombre)] = mediana
        salida["entrada por grupo · {} · p90".format(nombre)] = p90
    cuenta = {equipo: np.concatenate(presentes[equipo]) for equipo in (H, A)}
    salida["slots presentes por equipo · media"] = float(np.mean(np.concatenate(list(cuenta.values()))))
    salida["grupos con un equipo de más de 11 slots · %"] = float(100.0 * np.mean(
        (cuenta[H] > 11) | (cuenta[A] > 11)))

    z, _, _ = conjunto.salidas(trk, fuera)
    p = conjunto.probabilidades_de_cambio(trk, fuera)
    dentro = np.zeros(len(z), dtype=bool)
    for inicio, fin in trk.blocks:
        dentro[inicio:fin] = True
    visible = aprendida.balon_visible(trk) & dentro
    cercano = aprendida.equipo_mas_cercano(trk)
    salida["frames evaluados con balón · %"] = float(100.0 * visible.sum() / max(int(dentro.sum()), 1))
    mediana, p90 = _cuantiles(np.abs(z[visible]))
    salida["salida · |z| con balón · mediana"], salida["salida · |z| con balón · p90"] = mediana, p90
    salida["salida · |z| sin balón · mediana"] = _cuantiles(np.abs(z[dentro & ~visible]))[0]
    opina = visible & (cercano >= 0) & (z != 0)
    acuerdo = (np.where(z > 0, H, A) == cercano)[opina]
    salida["salida · z de acuerdo con el más cercano, con balón · %"] = float(100.0 * np.mean(acuerdo)) if len(
        acuerdo) else float("nan")
    cambios_de_signo = 0
    for inicio, fin in trk.blocks:
        signo = np.sign(z[inicio:fin])
        cambios_de_signo += int(np.sum((signo[1:] != signo[:-1]) & (signo[1:] != 0) & (signo[:-1] != 0)))
    minutos = float(dentro.sum()) / float(trk.fps) / 60.0
    salida["salida · cambios de signo de z por minuto evaluado"] = cambios_de_signo / max(minutos, 1e-9)
    salida["salida · frames con aviso de cambio (p ≥ 0,5) · %"] = float(100.0 * np.mean(
        p[dentro].max(axis=1) >= UMBRAL_CAMBIO))
    return salida
