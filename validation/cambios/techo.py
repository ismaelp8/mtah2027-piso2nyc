"""El techo del detector de cambios: ¿cuánto daría uno perfecto? (docs/decisiones.md, 16/11, punto 1). Descriptivo.

    python validation/cambios/techo.py            # los 7 partidos de la DFL, unos minutos

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del harness. Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime agregados.

El detector perfecto vale 1 a 12 frames o menos de cada cambio directo real (los que cruzan un `D` no cuentan) hacia
el equipo nuevo, y 0 en el resto. Se le pasa a `temporal.decode_cambios` y a `cambios.capa` con las 14 combinaciones
de la rejilla, sobre la evidencia de `main` (B5 con el pliegue que no vio el partido). Tres lecturas:

- flag ← flag: los cambios del flag, puntuado con el flag;
- control ← control: los de control, puntuado con control;
- flag ← control: los de control, puntuado con el flag (un detector perfecto entrenado con control, si la GT
  fuera el flag).

No decide nada: es la cota de lo que puede dar la pieza, y elige la combinación mirando el resultado.
"""

import argparse
import concurrent.futures
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "scripts"))
import comun  # noqa: E402
import diagnostico_errores as de  # noqa: E402
from comun import dfl, puntuar  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LECTURAS = (("flag", "flag"), ("control", "control"), ("flag", "control"))  # (se puntúa con, cambios de)


def partido(nombre_partido):
    """Los recuentos de cada celda, las etiquetas predichas de «como el ATD» con el `D` oráculo y la GT."""
    cargado, _, bases = comun.cargar(nombre_partido)
    gt = cargado["gt"]
    perfecto = {c: comun.p_perfecto(gt[c]) for c in dfl.CONVENCIONES}
    recuentos, predichas = {}, {}
    for (condicion, modo), base in bases.items():
        main = comun.decodificar(base, None, comun.MAIN)
        for de_quien in dfl.CONVENCIONES:
            for config in comun.CONFIGS:
                pred = main if config == comun.MAIN else comun.decodificar(base, perfecto[de_quien], config)
                for puntua, origen in LECTURAS:
                    if origen != de_quien:
                        continue
                    recuentos[(condicion, modo, (puntua, origen), config)] = puntuar.contar(gt[puntua], pred)
                    if condicion == de.CONDICION_DFL and modo == "oraculo":
                        predichas[((puntua, origen), config)] = pred
    n_cambios = {c: len(comun.cambios_directos(gt[c])[0]) for c in dfl.CONVENCIONES}
    return nombre_partido, recuentos, predichas, gt, n_cambios


def main():
    parser = argparse.ArgumentParser(description="El techo del detector de cambios de posesión, en la DFL.")
    parser.add_argument("--partidos", nargs="*", default=list(dfl.PARTIDOS))
    parser.add_argument("--procesos", type=int, default=4)
    args = parser.parse_args()
    with concurrent.futures.ProcessPoolExecutor(args.procesos) as pool:
        resultados = {r[0]: r for r in pool.map(partido, args.partidos)}
    orden = args.partidos
    print("# El techo del detector de cambios: el detector perfecto (descriptivo)\n")
    print("Código: {} · partidos: {}\n".format(puntuar.version_del_codigo(), ", ".join(orden)))
    print("Cambios directos reales: {} con el flag y {} con control.".format(
        *[sum(resultados[p][4][c] for p in orden) for c in dfl.CONVENCIONES]))

    def lista(condicion, modo, lectura, config):
        return [resultados[p][1][(condicion, modo, lectura, config)] for p in orden]

    mejores = {}
    for modo in comun.MODOS_D:
        for condicion in dfl.VOTAN:
            print("\n## `D` {} · balón «{}»\n".format("de las etiquetas" if modo == "oraculo" else "propio", condicion))
            print("spellF1 de los {} partidos juntos; entre paréntesis, la diferencia con `main` y en cuántos gana.\n"
                  .format(len(orden)))
            print("| combinación | flag ← flag | control ← control | flag ← control |")
            print("|---|---|---|---|")
            for config in comun.CONFIGS:
                celdas = []
                for lectura in LECTURAS:
                    valor = comun.spell(lista(condicion, modo, lectura, config))
                    if config == comun.MAIN:
                        celdas.append("{:.3f}".format(valor))
                        continue
                    dif, _, gana = comun.frente_a(lista(condicion, modo, lectura, config),
                                                  lista(condicion, modo, lectura, comun.MAIN), 0)
                    celdas.append("{:.3f} ({:+.3f}, {} de {})".format(valor, dif, gana, len(orden)))
                    clave = (modo, condicion, lectura)
                    if valor > mejores.get(clave, (0, None))[0]:
                        mejores[clave] = (valor, config)
                print("| {} | {} |".format(comun.nombre(config), " | ".join(celdas)))

    print("\n## Por duración: `main` y la mejor combinación del techo («{}», `D` de las etiquetas)".format(
        de.CONDICION_DFL))
    for lectura in LECTURAS:
        _, mejor = mejores[("oraculo", de.CONDICION_DFL, lectura)]
        for config in (comun.MAIN, mejor):
            acc = de.nuevo()
            for p in orden:
                de.analizar(resultados[p][3][lectura[0]], resultados[p][2][(lectura, config)], acc)
            de.imprimir("{} ← {} · {}".format(lectura[0], lectura[1], comun.nombre(config)), acc,
                        de.CAUSAS_REALES[:3])


if __name__ == "__main__":
    main()
