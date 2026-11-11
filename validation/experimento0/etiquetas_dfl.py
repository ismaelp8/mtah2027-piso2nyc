"""Etiquetas H/A/D por frame de un partido de la Bundesliga, a partir de sus flags (paso 2a).

Regla mecánica, la misma que `CHALLENGE.md` describe para la GT del reto:
- `D` si `BallStatus` = 0;
- si no, `H` si `BallPossession` = 1 (local) y `A` si `BallPossession` = 2 (visitante);
- `X` si falta algún flag (en la DFL no falta ninguno, pero se cuenta).

Escribe un CSV `frame,label` FUERA del repo (junto a los datos abiertos), con un frame `X` entre las
dos partes para que el scorer no una posesiones a través del descanso. Imprime solo agregados:
reparto, cambios de etiqueta y rachas cortas (parpadeos).

Uso:
    python validation/experimento0/etiquetas_dfl.py J03WMX
    python validation/experimento0/etiquetas_dfl.py todos
"""

import argparse
import collections
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfl_lector  # noqa: E402

PARTIDOS = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
FPS = 25


def carpeta_etiquetas():
    return os.path.join(os.path.dirname(dfl_lector.carpeta_dfl()), "dfl_etiquetas")


def etiquetas_parte(estado, poss):
    lab = np.full(len(estado), "X", dtype="<U1")
    lab[estado == 0] = "D"
    vivo = estado == 1
    lab[vivo & (poss == 1)] = "H"
    lab[vivo & (poss == 2)] = "A"
    return lab


def etiquetas_partido(datos):
    """Array de etiquetas de las dos partes, con un 'X' entre ellas."""
    p1 = etiquetas_parte(datos["partes"][1]["estado"], datos["partes"][1]["poss"])
    p2 = etiquetas_parte(datos["partes"][2]["estado"], datos["partes"][2]["poss"])
    return np.concatenate([p1, np.array(["X"]), p2])


def rachas(lab):
    """[(etiqueta, longitud)] de las rachas de un array de etiquetas."""
    cortes = np.flatnonzero(lab[1:] != lab[:-1]) + 1
    bordes = np.concatenate(([0], cortes, [len(lab)]))
    return [(str(lab[bordes[i]]), int(bordes[i + 1] - bordes[i])) for i in range(len(bordes) - 1)]


def resumen(datos):
    salida = {}
    for parte in (1, 2):
        lab = etiquetas_parte(datos["partes"][parte]["estado"], datos["partes"][parte]["poss"])
        r = rachas(lab)
        cambios = collections.Counter(a + ">" + b for (a, _), (b, _) in zip(r[:-1], r[1:]))
        cortas = collections.Counter(e for e, n in r if n < FPS)
        muy_cortas = collections.Counter(e for e, n in r if n <= 2)
        salida[parte] = {
            "frames": int(len(lab)),
            "reparto": {k: int(v) for k, v in sorted(collections.Counter(lab.tolist()).items())},
            "cambios_de_etiqueta": dict(sorted(cambios.items())),
            "rachas_de_menos_de_1s_por_etiqueta": dict(sorted(cortas.items())),
            "rachas_de_2_frames_o_menos_por_etiqueta": dict(sorted(muy_cortas.items())),
        }
    return salida


def escribir_csv(lab, ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("frame,label\n")
        f.writelines("{},{}\n".format(i, e) for i, e in enumerate(lab))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("partido", help="id del partido o 'todos'")
    args = parser.parse_args()
    partidos = PARTIDOS if args.partido == "todos" else (args.partido,)
    for partido in partidos:
        datos = dfl_lector.cargar_cache(partido)
        lab = etiquetas_partido(datos)
        ruta = os.path.join(carpeta_etiquetas(), "{}.csv".format(partido))
        escribir_csv(lab, ruta)
        print(json.dumps({"partido": partido, "csv": "dfl_etiquetas/{}.csv".format(partido),
                          "frames_con_separador": int(len(lab)), "partes": resumen(datos)}, ensure_ascii=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
