"""Comprobación del detector de toques de B8 frente al anexo A.4 de la revisión externa: eventos por minuto.

    python validation/apuesta_b/eventos_toque.py

El detector (`aprendida.eventos_de_toque`) reescribe el del anexo A.4 de `docs/revision_externa_2026-11-15.md`.
Ese anexo es una medida de fuera que nadie del equipo ha repetido. La regla, fijada antes de entrenar
(`docs/decisiones.md`, 15/11, «una sola ronda de reentrenamiento de B5»): los eventos por minuto de juego
tienen que quedar a ±20 % de los de la revisión, 24,2 «como el ATD» y 27,6 «sin bloques». Si no cuadra, se
para y se dice; no se ajusta el detector.

Cuenta los eventos (con signo o sin él: con nadie a 3 m el signo es 0, pero el evento existe) en los frames
de juego (`H` o `A` en el flag) de los tramos evaluados, en las condiciones del balón del harness.

Datos abiertos de la DFL: lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
from possession import aprendida, ball, tracking  # noqa: E402

REVISION = {"como el ATD": 24.2, "como el ATD, sin bloques": 27.6, "limpio": 31.8}
TOLERANCIA = 0.20


def eventos(trk):
    """(frames con evento, frames con evento y signo) del detector de B8, tramo a tramo."""
    es_evento = np.zeros(len(trk.bx), bool)
    con_signo = np.zeros(len(trk.bx), bool)
    team = np.asarray(trk.team)
    columnas = [np.flatnonzero(team == equipo) for equipo in (tracking.H, tracking.A)]
    for inicio, fin in trk.blocks:
        bx = np.asarray(trk.bx[inicio:fin], dtype=np.float64)
        by = np.asarray(trk.by[inicio:fin], dtype=np.float64)
        equipos = [aprendida._por_equipo(trk.px[inicio:fin], trk.py[inicio:fin], c) for c in columnas]
        con_signo[inicio:fin] = aprendida.eventos_de_toque(bx, by, equipos, float(trk.fps)) != 0
        cambio = aprendida.cambio_de_velocidad(bx, by, float(trk.fps))
        valor = np.where(np.isnan(cambio), -np.inf, cambio)
        maximo = valor >= aprendida.TOQUE_UMBRAL
        n = len(valor)
        for k in range(1, aprendida.TOQUE_MAXIMO + 1):
            anterior = np.concatenate((np.full(k, -np.inf), valor[:-k])) if k < n else np.full(n, -np.inf)
            siguiente = np.concatenate((valor[k:], np.full(k, -np.inf))) if k < n else np.full(n, -np.inf)
            maximo &= (valor > anterior) & (valor >= siguiente)
        es_evento[inicio:fin] = maximo
    return es_evento, con_signo


def main():
    totales = {c: np.zeros(3) for c in REVISION}
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        vivo = np.isin(cargado["gt"]["flag"], (tracking.H, tracking.A))
        for condicion in REVISION:
            trk = ball.clean(dfl.tracking_de(cargado, condicion))
            es_evento, con_signo = eventos(trk)
            totales[condicion] += [np.sum(es_evento & vivo), np.sum(con_signo & vivo), np.sum(vivo)]
        print("hecho {}".format(partido), file=sys.stderr)
    print("| balón | eventos por minuto de juego | con signo (alguien a 3 m) | revisión (A.4) | ±20 % | ¿cuadra? |")
    print("|---|---|---|---|---|---|")
    for condicion, (n_eventos, n_signo, frames) in totales.items():
        minutos = frames / dfl.FPS / 60.0
        por_minuto = n_eventos / minutos
        objetivo = REVISION[condicion]
        cuadra = abs(por_minuto - objetivo) <= TOLERANCIA * objetivo
        print("| {} | {:.1f} | {:.1f} | {:.1f} | {:.1f}–{:.1f} | {} |".format(
            condicion if condicion in dfl.VOTAN else condicion + " (sin voto)", por_minuto, n_signo / minutos,
            objetivo, (1 - TOLERANCIA) * objetivo, (1 + TOLERANCIA) * objetivo,
            ("sí" if cuadra else "NO") if condicion in dfl.VOTAN else "–").replace(".", ","))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
