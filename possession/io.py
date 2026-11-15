"""Lectores del ATD. Reciben la ruta y devuelven arrays por frame de vídeo, con las posiciones en metros."""

import numpy as np

FIELD_SEP = ":"
GROUP_SEP = ";"
VALUE_SEP = ","

# Lo que `counts` apunta de un ATD (`lines`). Solo enteros, sin ningún frame_id ni nada por frame: se pueden
# pegar a Claude (CLAUDE.md, regla nº 1).
COUNT_KEYS = ("lineas", "validas", "vacias", "mal_formadas", "fuera_de_rango", "repetidas", "frames_sin_linea")
# Los errores de lectura no llevan el texto del ATD, para que se puedan pegar a Claude (regla nº 1).
NOT_A_FRAME = "una línea del ATD tiene un frame_id que no es un entero (no se enseña el valor: regla nº 1)"
NOT_A_NUMBER = "una línea del ATD tiene un valor que no es un número (no se enseña el valor: regla nº 1)"


def lines(handle, n_frames, counts=None, seen=None):
    """Las líneas `<frame_id>:<jugadores>:<balón>` del ATD, como (frame de vídeo, campos).

    Se salta las líneas que no tienen tres campos y las de un frame fuera de [0, n_frames).

    - `counts` (un diccionario): apunta cuántas hay de cada tipo (`COUNT_KEYS`), solo enteros.
    - `seen` (un array de bool de n_frames): marca los frames que han tenido una línea válida. Es por frame:
      no se imprime.

    Una línea repetida se lee las dos veces y gana la última, salvo en los grupos escritos como un solo
    `NaN`, que dejan el valor de la primera. Un fichero cortado se ve sobre todo en `frames_sin_linea`.
    """
    tally = dict.fromkeys(COUNT_KEYS, 0)
    if seen is None:
        seen = np.zeros(n_frames, dtype=bool)
    for line in handle:
        tally["lineas"] += 1
        text = line.rstrip("\n")
        parts = text.split(FIELD_SEP)
        if len(parts) != 3:
            tally["mal_formadas" if text.strip() else "vacias"] += 1
            continue
        try:
            frame = int(parts[0]) - 1
        except ValueError:
            raise ValueError(NOT_A_FRAME) from None
        if not 0 <= frame < n_frames:
            tally["fuera_de_rango"] += 1
            continue
        tally["validas"] += 1
        tally["repetidas"] += int(seen[frame])
        seen[frame] = True
        yield frame, parts
    if counts is not None:
        tally["frames_sin_linea"] = int(n_frames - seen.sum())
        counts.update(tally)


def load_ball(atd_raw_path, n_frames, pitch, counts=None, seen=None):
    """(x, y, speed) del balón por frame de vídeo; x e y en metros, NaN donde no se ve.

    El frame_id del ATD empieza en 1 y el frame de vídeo en 0 (DATA.md). `speed` es la columna tal cual
    viene: no se comporta como m/s del balón (validation/resultados/2026-11-12_balon_muerto_atd.md).

    Un balón ausente puede venir como `NaN,NaN,NaN` o como un solo `NaN`; las dos formas quedan como NaN,
    igual que en starter/baseline.py, que solo mira el primer carácter del grupo.

    `counts` y `seen`: las líneas leídas y saltadas, y los frames con línea (`lines`).
    """
    length, width = pitch
    x = np.full(n_frames, np.nan)
    y = np.full(n_frames, np.nan)
    speed = np.full(n_frames, np.nan)
    with open(atd_raw_path) as handle:
        for frame, parts in lines(handle, n_frames, counts, seen):
            # float("NaN") ya da nan, así que "NaN,NaN,NaN" queda como NaN sin caso especial; el caso
            # especial es el balón escrito como un solo "NaN", que se deja en el NaN ya reservado.
            values = parts[2].split(VALUE_SEP)
            if len(values) < 2:
                continue
            try:
                x[frame] = float(values[0]) * length
                y[frame] = float(values[1]) * width
                if len(values) > 2:
                    speed[frame] = float(values[2])
            except ValueError:
                raise ValueError(NOT_A_NUMBER) from None
    return x, y, speed


def load_players(atd_raw_path, n_frames, pitch, counts=None, seen=None):
    """(x, y) de cada slot de track por frame de vídeo, en metros; forma (n_frames, n_slots), NaN si falta.

    Un slot es un tracklet, no un jugador: no sigue a la misma persona todo el partido (DATA.md). Todas
    las líneas tienen que traer el mismo número de slots; si no, ValueError, porque una línea con slots
    de más o de menos descolocaría el equipo de cada uno.

    `counts` y `seen`: las líneas leídas y saltadas, y los frames con línea (`lines`).
    """
    length, width = pitch
    x = y = None
    with open(atd_raw_path) as handle:
        for frame, parts in lines(handle, n_frames, counts, seen):
            groups = parts[1].split(GROUP_SEP)
            if x is None:
                x = np.full((n_frames, len(groups)), np.nan, dtype=np.float32)
                y = np.full((n_frames, len(groups)), np.nan, dtype=np.float32)
            elif len(groups) != x.shape[1]:
                # Sin el frame_id: el mensaje se puede pegar a Claude (CLAUDE.md, regla nº 1).
                raise ValueError("una línea del ATD tiene {} slots y la primera tenía {}".format(
                    len(groups), x.shape[1]))
            try:
                for slot, group in enumerate(groups):
                    values = group.split(VALUE_SEP)
                    if len(values) < 2:
                        continue  # un solo "NaN": slot vacío
                    x[frame, slot] = float(values[0]) * length
                    y[frame, slot] = float(values[1]) * width
            except ValueError:
                raise ValueError(NOT_A_NUMBER) from None
    return x, y
