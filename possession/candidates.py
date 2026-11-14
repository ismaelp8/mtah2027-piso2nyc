"""Evidencia de equipo (`H` o `A`) por frame, con el balón visible.

Versión 0 (N1 de docs/investigacion_metodos.md §2.3): el equipo del slot más cercano al balón, que es lo
que hace starter/baseline.py. Es el control: cualquier candidato tiene que superarlo en el harness.

Interfaz: `evidence(trk)` devuelve `(score, allowed)`; ver possession/tracking.py.
"""

import numpy as np

from possession.tracking import A, H, no_evidence

# Puntuación a favor del equipo del jugador más cercano. Sin ajustar: es la unidad en la que se miden los
# costes del decodificador, y se fija en la DFL, no en el partido.
NEAREST_SCORE = 1.0
# Frames por bloque al calcular distancias, para no reservar una matriz de todo el partido de una vez.
CHUNK = 20000
NOBODY = -1


def nearest_team(trk):
    """Equipo del slot más cercano al balón por frame: 0, 1, o -1 si no hay balón o no hay jugadores.

    Con dos slots a la misma distancia gana el de índice más bajo, como en el baseline.
    """
    out = np.full(len(trk.bx), NOBODY, dtype=np.int8)
    seen = np.flatnonzero(~np.isnan(trk.bx) & ~np.isnan(trk.by))
    for start in range(0, len(seen), CHUNK):
        idx = seen[start:start + CHUNK]
        dx = trk.px[idx].astype(np.float64) - trk.bx[idx, None]
        dy = trk.py[idx].astype(np.float64) - trk.by[idx, None]
        d2 = dx * dx + dy * dy
        d2 = np.where(np.isnan(d2), np.inf, d2)
        best = np.argmin(d2, axis=1)
        found = np.isfinite(d2[np.arange(len(idx)), best])
        out[idx[found]] = trk.team[best[found]]
    return out


def evidence(trk):
    """NEAREST_SCORE a favor del equipo del jugador más cercano al balón. Sin balón, no opina."""
    score, allowed = no_evidence(len(trk.bx))
    team = nearest_team(trk)
    score[team == H, H] = NEAREST_SCORE
    score[team == A, A] = NEAREST_SCORE
    return score, allowed
