"""Calcula los canales de B11 y B12 en los 7 partidos de la DFL y los guarda para entrenar con torch.

    python validation/secuencia/exportar.py

Datos abiertos de otros partidos (DFL, CC BY 4.0), con la caché del harness. Lo puede ejecutar cualquiera,
Claude incluido. Solo imprime agregados. Usa el mismo código que la predicción (`secuencia.canales`) sobre el
mismo tracking que el harness (`dfl.tracking_de`, con la limpieza de `main`), en las dos condiciones que votan.

Guarda en `comun.carpeta_cache()`, fuera del repo, por partido y condición: los canales (float32), la etiqueta
(1 si el flag es `H`), la máscara de la pérdida (frames vivos donde el flag y control coinciden) y los tramos.
"""

import time

import numpy as np

import comun
import dfl
from possession import ball, secuencia
from possession.tracking import A, H


def main():
    comun.carpeta_cache().mkdir(parents=True, exist_ok=True)
    if tuple(dfl.PARTIDOS) != comun.PARTIDOS or tuple(dfl.VOTAN) != comun.CONDICIONES:
        raise AssertionError("comun.PARTIDOS o comun.CONDICIONES no son los del harness")
    inicio = time.time()
    for partido in comun.PARTIDOS:
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        etiqueta = (gt["flag"] == H).astype(np.int8)
        mascara = (gt["flag"] == gt["control"]) & np.isin(gt["flag"], (H, A))
        for condicion in comun.CONDICIONES:
            trk = ball.clean(dfl.tracking_de(cargado, condicion))
            x = secuencia.canales(trk)
            dentro = np.zeros(len(x), bool)
            for a, b in trk.blocks:
                dentro[a:b] = True
            np.savez_compressed(comun.fichero_canales(partido, condicion), canales=x.astype(np.float32),
                                etiqueta=etiqueta, mascara=mascara & dentro,
                                tramos=np.array(trk.blocks, dtype=np.int64))
            print("{} · {}: {} frames, {} en la pérdida ({:.1f} % H) · {:.0f} s".format(
                partido, condicion, len(x), int((mascara & dentro).sum()),
                100.0 * float(etiqueta[mascara & dentro].mean()), time.time() - inicio), flush=True)


if __name__ == "__main__":
    main()
