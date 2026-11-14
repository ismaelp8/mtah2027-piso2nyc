"""Con qué comparar el agregado 4 del partido: cómo se mueven los jugadores en la DFL, con y sin temblor.

    python validation/scripts/d_estado/referencia_agregado4.py

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0). Lo puede ejecutar cualquiera, Claude
incluido. Solo imprime agregados.

Para qué: el modelo de estado de `D` (possession/dead_state.py) se entrena con los jugadores de la DFL, que
están revisados. Los del ATD son automáticos. `validation/partido/agregados_jugadores.py`, que ejecuta una
persona, imprime en su punto 4 dos líneas del partido entero:

- «todos los frames evaluados»: p10, p50 y p90 de la velocidad media de los jugadores en 2 s, y qué
  fracción queda por debajo de 1,2 m/s;
- «fracción de jugadores a menos de 1 m/s (media de 2 s)»: p10, p50 y p90.

Este script da esas mismas dos líneas en la DFL, calculadas con el código del pipeline
(`dead_state.features`, que usa la misma definición de velocidad), tal cual y con un temblor añadido a
las posiciones de los jugadores. Al lado va lo que el modelo del módulo diría en cada caso. Así, cuando
llegue la salida del partido, se ve a qué fila se parece y si el modelo se traslada.
"""

import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import entrenar  # noqa: E402
import medir  # noqa: E402
from possession import dead_state  # noqa: E402

D, X = entrenar.D, entrenar.X
TEMBLORES = (0.0, 0.05, 0.1, 0.2)  # desviación típica en metros, por frame y por eje
LENTO = 1.2  # m/s: el corte de agregados_jugadores.py (SLOW_MS)
RASGOS = ("v_media_2s", "frac_lentos_2s")


def cuantiles(valores):
    return " / ".join("{:.2f}".format(q).replace(".", ",") for q in np.percentile(valores, [10, 50, 90]))


def main():
    cargados = [entrenar.cargar(partido) for partido in entrenar.PARTIDOS]
    hay_modelo = bool(dead_state.MODEL["coef"])
    print("Referencia de la DFL para el agregado 4 del partido ({} partidos, frames con etiqueta)".format(
        len(cargados)))
    print()
    print("| temblor añadido a los jugadores | velocidad media en 2 s, p10 / p50 / p90 (m/s) | por debajo de "
          "{:g} m/s | fracción de jugadores a menos de 1 m/s, p10 / p50 / p90 | frames que el modelo ve más "
          "`D` que juego | `D` real |".format(LENTO).replace(".", ","))
    print("|---|---|---|---|---|---|")
    for sigma in TEMBLORES:
        velocidad, lentos, dice_d, es_d = [], [], [], []
        for indice, datos in enumerate(cargados):
            trk = datos["trk"] if sigma == 0 else medir.con_temblor(datos["trk"], sigma, indice)
            rasgos = dead_state.features(trk, RASGOS)
            con_etiqueta = datos["gt"]["flag"] != X
            velocidad.append(rasgos["v_media_2s"][con_etiqueta])
            lentos.append(rasgos["frac_lentos_2s"][con_etiqueta])
            es_d.append(datos["gt"]["flag"][con_etiqueta] == D)
            if hay_modelo:
                dice_d.append(dead_state.log_odds(trk)[con_etiqueta] > 0)
        velocidad, lentos = np.concatenate(velocidad), np.concatenate(lentos)
        velocidad, lentos = velocidad[~np.isnan(velocidad)], lentos[~np.isnan(lentos)]
        print("| {} | {} | {:.1f} % | {} | {} | {:.1f} % |".format(
            "ninguno" if sigma == 0 else "{:g} m".format(sigma), cuantiles(velocidad),
            100.0 * float(np.mean(velocidad < LENTO)), cuantiles(lentos),
            "{:.1f} %".format(100.0 * float(np.mean(np.concatenate(dice_d)))) if hay_modelo else "sin modelo",
            100.0 * float(np.mean(np.concatenate(es_d)))).replace(".", ","))
    print()
    print("Cómo leerlo: si las dos líneas del partido se parecen a la fila «ninguno», los jugadores del ATD se "
          "mueven como los de la DFL. Si se parecen a una fila con temblor, el modelo verá menos `D` del que hay.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
