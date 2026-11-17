"""Lo común de las medidas del detector de cambios de posesión (docs/decisiones.md, 16/11). Datos abiertos (DFL).

No se ejecuta solo. Lo usan `techo.py` (el detector perfecto) y `medir.py` (el detector aprendido y las reglas).

- `cargar(partido)`: la evidencia combinada de `main` en cada condición del balón y cada modo del `D`, calculada
  una vez, como en `pipeline.run` y en el harness (B5 con el pliegue que no vio el partido).
- `decodificar(base, p, config)`: las etiquetas con el detector `p` y una combinación (w, γ, W) de la rejilla.
- `clases(gt)`: las etiquetas del detector (0 sin cambio, 1 hacia `H`, 2 hacia `A`, −1 fuera).
"""

import collections
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(AQUI, "..", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, cambios, pipeline, temporal  # noqa: E402
from possession.tracking import A, H  # noqa: E402

MODOS_D = ("oraculo", "propio")
# La rejilla de la decisión del 16/11, con γ = 8 añadida antes de medir ningún detector: (w, γ, W). Con γ = 0 no hay capa y W no cuenta. La primera es `main`.
MAIN = (0.0, 0.0, 0)
CONFIGS = [MAIN] + [(w, 0.0, 0) for w in (12.5, 25.0)] + [
    (w, g, v) for w in (0.0, 12.5, 25.0) for g in (2.0, 4.0, 8.0) for v in (25, 50)]

Base = collections.namedtuple("Base", ["score", "allowed", "blocks"])


def nombre(config):
    w, g, v = config
    if config == MAIN:
        return "main"
    return "w {:g} · γ {:g}{}".format(w, g, " · W {}".format(v) if g else "")


def base_de(trk, gt, modo_d, partido):
    """La evidencia combinada de `main`, como `pipeline.run` hasta justo antes de decodificar."""
    limpio = pipeline.default_piece("ball")(trk)
    piezas = [aprendida.evidence_b5(limpio, fuera=partido), pipeline.default_piece("dead_state")(limpio)]
    if modo_d == "oraculo":
        piezas.append(puntuar.d_oraculo(gt))
    score, allowed, conflicto = pipeline.combine(piezas, len(limpio.bx))
    if any(conflicto[a:b].any() for a, b in limpio.blocks):
        raise ValueError("las piezas se contradicen")
    return Base(score, allowed, limpio.blocks)


def decodificar(base, p, config):
    """Etiquetas con el detector `p` (n, 2) y la combinación `config` = (w, γ, W). Con `MAIN`, las de `main`."""
    w, gamma, ventana = config
    if config == MAIN or p is None:
        return temporal.decode(base.score, base.allowed, base.blocks)
    score = base.score + cambios.capa(p, gamma, ventana)[0] if gamma else base.score
    return temporal.decode_cambios(score, base.allowed, base.blocks, bonus=cambios.rebaja(p, w))


def cambios_directos(gt):
    """(frames, hacia): los frames en que la posesión viva pasa de un equipo al otro, y a cuál."""
    vivo = (gt == H) | (gt == A)
    t = np.flatnonzero(vivo[1:] & vivo[:-1] & (gt[1:] != gt[:-1])) + 1
    return t, gt[t]


def clases(gt, semiancho=cambios.SEMIANCHO):
    """Por frame: 1 «hacia H» y 2 «hacia A» a `semiancho` frames o menos de un cambio directo (el más cercano; en
    el empate, el primero), 0 en el resto de los vivos y −1 en los `D` y fuera de los tramos."""
    n = len(gt)
    clase = np.zeros(n, dtype=np.int8)
    lejos = np.full(n, np.iinfo(np.int32).max, dtype=np.int32)
    frames, hacia = cambios_directos(gt)
    for t, x in zip(frames, hacia):
        a, b = max(0, t - semiancho), min(n, t + semiancho + 1)
        dist = np.abs(np.arange(a, b) - t)
        gana = dist < lejos[a:b]
        clase[a:b][gana] = 1 + int(x)
        lejos[a:b][gana] = dist[gana]
    clase[~((gt == H) | (gt == A))] = -1
    return clase


def p_perfecto(gt):
    """El detector perfecto: `p` (n, 2) con 1 en los frames de su clase."""
    clase = clases(gt)
    return np.column_stack((clase == 1, clase == 2)).astype(float)


def cargar(partido, condiciones=dfl.VOTAN, modos=MODOS_D):
    """(cargado, {condición: tracking}, {(condición, modo): Base}) de un partido."""
    cargado = dfl.cargar(partido)
    trks = {c: puntuar.solo_lectura(dfl.tracking_de(cargado, c)) for c in condiciones}
    bases = {(c, m): base_de(trks[c], cargado["gt"]["flag"], m, partido) for c in condiciones for m in modos}
    return cargado, trks, bases


def spell(recuentos):
    return puntuar.spell_f1(*puntuar.juntar(recuentos))


def frente_a(candidato, referencia, n_draws=1000):
    """(diferencia, intervalo, gana en) de dos listas de recuentos por partido, en el mismo orden."""
    dif = spell(candidato) - spell(referencia)
    intervalo = puntuar.diferencia_bootstrap(puntuar.juntar(candidato), puntuar.juntar(referencia), n_draws)
    gana = int(sum(spell([a]) > spell([b]) for a, b in zip(candidato, referencia)))
    return dif, intervalo, gana
