"""El peso de la capa «balón fuera» (D7), sacado de la escala del `D` de estado en la DFL, antes del recuento.

    python validation/scripts/peso_balon_fuera.py

Datos abiertos de otros partidos (DFL, Bassek et al., 2025, CC BY 4.0, con la caché del harness): lo puede
ejecutar Claude. Solo imprime agregados. No mira el partido.

**Para qué** (`docs/decisiones.md`, 15/11, «D7, el balón fuera del campo: regla y peso, antes del recuento»):
la capa suma `W` en la columna `D` en cada frame con el balón visto a más de 1 m fuera. En ese frame, el
equipo más cercano lleva el +1 de N1 dentro de B5 y el `D` lleva la puntuación de `dead_state` (`ds`, el
logaritmo de la razón de probabilidades, entre −8 y +8). El frame empuja hacia `D` si `W + ds > 1`.

**La fórmula, fijada antes de ejecutar esto:** `W = 1 − P95`, donde `P95` es el percentil 95 de `ds` en el
juego vivo lejos de cualquier parada (a 5 s o más de un `D`), en la DFL con los jugadores tal cual, y
redondeado hacia abajo a un entero. Así, un balón visto fuera por error en pleno juego (un balón de repuesto,
el temblor junto a la línea) empuja hacia `D` en como mucho el 5 % de esos frames, y además tendría que durar
lo bastante para pagar los dos costes de cambio (50) antes de crear una parada.

Enseña también, como descripción, cuántos frames del primer segundo de cada `D` real pasarían de `D` con ese
`W`: es para lo que sirve la capa. No cambia el peso.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
from possession import dead_state, tracking  # noqa: E402

LEJOS = 125  # frames: a 5 s o más de cualquier `D`
PRIMER_SEGUNDO = 25  # frames del principio de cada `D` real
N1 = 1.0  # el +1 de N1 dentro de B5 (aprendida.N1_PUNTOS)
CONDICION = "como el ATD"  # los jugadores son los de la DFL tal cual en todas las condiciones


def distancia_a_d(es_d):
    """Frames hasta el `D` más cercano (hacia delante o hacia atrás); muy grande si no hay ninguno."""
    n = len(es_d)
    indices = np.flatnonzero(es_d)
    if not len(indices):
        return np.full(n, 10 ** 9)
    posicion = np.arange(n)
    derecha = np.searchsorted(indices, posicion)
    siguiente = np.where(derecha < len(indices), indices[np.minimum(derecha, len(indices) - 1)] - posicion, 10 ** 9)
    anterior = np.where(derecha > 0, posicion - indices[np.maximum(derecha - 1, 0)], 10 ** 9)
    return np.minimum(siguiente, anterior)


def main():
    vivo, inicio = [], []
    for partido in dfl.PARTIDOS:
        cargado = dfl.cargar(partido)
        etiquetas = np.asarray(cargado["gt"]["flag"])  # el `D` es el mismo con las dos convenciones
        trk = dfl.tracking_de(cargado, CONDICION)
        ds = dead_state.evidence(trk)[0][:, tracking.D]
        for a, b in trk.blocks:
            es_d = etiquetas[a:b] == tracking.D
            lejos = (~es_d) & (distancia_a_d(es_d) >= LEJOS)
            vivo.append(ds[a:b][lejos])
            comienzo = np.flatnonzero(es_d & np.concatenate(([False], ~es_d[:-1])))
            for t in comienzo:
                inicio.append(ds[a:b][t:t + PRIMER_SEGUNDO])
        print("hecho {}".format(partido), file=sys.stderr)
    vivo, inicio = np.concatenate(vivo), np.concatenate(inicio)
    p95 = float(np.percentile(vivo, 95))
    peso = float(np.floor(N1 - p95))
    print("Peso de la capa «balón fuera», con la fórmula fijada antes (W = 1 − P95 del juego vivo, hacia abajo)")
    print()
    print("juego vivo a 5 s o más de un D: {} frames; ds: P5 {:.2f}, mediana {:.2f}, P95 {:.2f}".format(
        len(vivo), np.percentile(vivo, 5), np.median(vivo), p95).replace(".", ","))
    print("primer segundo de los D reales: {} frames; ds: P5 {:.2f}, mediana {:.2f}, P95 {:.2f}".format(
        len(inicio), np.percentile(inicio, 5), np.median(inicio), np.percentile(inicio, 95)).replace(".", ","))
    print()
    print("W = {:g}".format(peso))
    print("con W, empujan hacia D (W + ds > 1): {:.1f} % del juego vivo lejos de un D y {:.1f} % del primer "
          "segundo de los D reales (descriptivo)".format(100.0 * np.mean(peso + vivo > N1),
                                                         100.0 * np.mean(peso + inicio > N1)).replace(".", ","))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
