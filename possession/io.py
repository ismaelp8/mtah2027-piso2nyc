"""Lectores del ATD. Reciben la ruta y devuelven arrays por frame de vídeo, con las posiciones en metros."""

import numpy as np

FIELD_SEP = ":"
GROUP_SEP = ";"
VALUE_SEP = ","


def load_ball(atd_raw_path, n_frames, pitch):
    """(x, y, speed) del balón por frame de vídeo; x e y en metros, NaN donde no se ve.

    El frame_id del ATD empieza en 1 y el frame de vídeo en 0 (DATA.md). `speed` es la columna tal cual
    viene: no se comporta como m/s del balón (validation/resultados/2026-11-12_balon_muerto_atd.md).
    """
    length, width = pitch
    x = np.full(n_frames, np.nan)
    y = np.full(n_frames, np.nan)
    speed = np.full(n_frames, np.nan)
    with open(atd_raw_path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split(FIELD_SEP)
            if len(parts) != 3:
                continue
            frame = int(parts[0]) - 1
            if not 0 <= frame < n_frames:
                continue
            # float("NaN") ya da nan, así que un balón ausente queda como NaN sin caso especial.
            values = parts[2].split(VALUE_SEP)
            x[frame] = float(values[0]) * length
            y[frame] = float(values[1]) * width
            if len(values) > 2:
                speed[frame] = float(values[2])
    return x, y, speed


def load_players(atd_raw_path, n_frames, pitch):
    """(x, y) de cada slot de track por frame de vídeo, en metros; forma (n_frames, n_slots), NaN si falta.

    Un slot es un tracklet, no un jugador: no sigue a la misma persona todo el partido (DATA.md). Todas
    las líneas tienen que traer el mismo número de slots; si no, ValueError, porque una línea con slots
    de más o de menos descolocaría el equipo de cada uno.
    """
    length, width = pitch
    x = y = None
    with open(atd_raw_path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split(FIELD_SEP)
            if len(parts) != 3:
                continue
            frame = int(parts[0]) - 1
            if not 0 <= frame < n_frames:
                continue
            groups = parts[1].split(GROUP_SEP)
            if x is None:
                x = np.full((n_frames, len(groups)), np.nan, dtype=np.float32)
                y = np.full((n_frames, len(groups)), np.nan, dtype=np.float32)
            elif len(groups) != x.shape[1]:
                # Sin el frame_id: el mensaje se puede pegar a Claude (CLAUDE.md, regla nº 1).
                raise ValueError("una línea del ATD tiene {} slots y la primera tenía {}".format(
                    len(groups), x.shape[1]))
            for slot, group in enumerate(groups):
                values = group.split(VALUE_SEP)
                x[frame, slot] = float(values[0]) * length
                y[frame, slot] = float(values[1]) * width
    return x, y
