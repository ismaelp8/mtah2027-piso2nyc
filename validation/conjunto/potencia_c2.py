"""¿Habría saltado el criterio C2 donde sabemos que el modelo falla? Descriptivo, en los datos abiertos.

    python validation/conjunto/potencia_c2.py --pesos-sc <solo_sc.npz> --pesos-dfl <solo_dfl.npz>

Datos abiertos de otros partidos (la caché de `exportar.py`). Lo puede ejecutar cualquiera, Claude incluido. Solo
imprime agregados. No lee el examen de SkillCorner. La lectura está en docs/decisiones.md (17/11, «tres
comprobaciones más», punto 6), escrita antes de ejecutarlo.

El criterio C2 del punto 4 de K2 compara las seis salidas del modelo en el partido con su rango en los datos abiertos,
ensanchado un cuarto por cada lado (`validation/partido/conjunto_en_el_partido.py`). ¿Detecta algo? Los modelos
entrenados con un solo proveedor pierden frente a `main` en el otro (comprobación 1): son casos en los que se sabe que
el modelo falla. Aquí se hace con ellos lo mismo que C2 hace con el partido:

- **la referencia** de cada modelo son sus salidas en las vistas de su propio proveedor. Son dentro de muestra, porque
  esos modelos se entrenaron con todos los partidos de su proveedor: la referencia sale algo más estrecha de lo que
  saldría fuera de muestra, y eso hace que C2 salte más fácil aquí que en el partido;
- **la prueba** son sus salidas en las vistas del otro proveedor.

Los pesos de esos dos modelos se pasan como ficheros `.npz` (`juntar.py --pliegues todos --destino … --alfa 4`).
"""

import argparse
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
sys.path.insert(0, ROOT)
import agregados as ag  # noqa: E402
import cj_comun as cj  # noqa: E402
import conjunto_en_el_partido as cp  # noqa: E402  (solo `comparar` y `es_salida`, que son puras)
import paridad  # noqa: E402
from possession import conjunto  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VISTAS = {"dfl": [("dfl", p, j) for p in cj.DFL for j in ("0", "1", "d0", "d1")],
          "sc": [("sc", p, j) for p in cj.SKILLCORNER for j in ("0", "1")]}
NOMBRE = {"dfl": "la DFL", "sc": "SkillCorner"}


def salidas_de(vistas):
    """{vista: {salida: valor}} con los pesos que haya en `conjunto.PESOS` (el pliegue de todos)."""
    resultado = {}
    for dominio, partido, j in vistas:
        valores = ag.agregados(paridad.tracking_de(dominio, partido, j), fuera=None)
        resultado[(dominio, partido, j)] = {n: v for n, v in valores.items() if cp.es_salida(n)}
        print("# hecho {} {} {}".format(dominio, partido, j), file=sys.stderr, flush=True)
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pesos-sc", required=True, help="pesos del modelo entrenado solo con SkillCorner")
    parser.add_argument("--pesos-dfl", required=True, help="pesos del modelo entrenado solo con la DFL")
    args = parser.parse_args()
    print("# ¿Habría saltado C2 donde el modelo falla? (descriptivo)\n")
    print("| modelo entrenado solo con | vistas del otro proveedor | vistas en las que C2 salta | salidas que más saltan |")
    print("|---|---|---|---|")
    detalle = []
    for propio, otro, pesos in (("sc", "dfl", args.pesos_sc), ("dfl", "sc", args.pesos_dfl)):
        conjunto.PESOS = pesos
        conjunto._CACHE.clear()
        en_casa, fuera = salidas_de(VISTAS[propio]), salidas_de(VISTAS[otro])
        nombres = sorted(next(iter(en_casa.values())))
        referencia = {"rango": {n: [float(np.nanmin([v[n] for v in en_casa.values()])),
                                    float(np.nanmax([v[n] for v in en_casa.values()]))] for n in nombres}}
        saltan, cuenta = 0, {n: 0 for n in nombres}
        for valores in fuera.values():
            _, salidas_fuera, _ = cp.comparar(valores, referencia)
            saltan += bool(salidas_fuera)
            for n in salidas_fuera:
                cuenta[n] += 1
        mas = sorted(cuenta.items(), key=lambda par: -par[1])[:3]
        print("| {} | {} | {} | {} |".format(
            NOMBRE[propio], len(fuera), saltan,
            "; ".join("{} ({})".format(n.replace("salida · ", ""), c) for n, c in mas if c) or "ninguna"))
        for n in nombres:
            lejos = [v[n] for v in fuera.values()]
            detalle.append((NOMBRE[propio], n.replace("salida · ", ""), referencia["rango"][n], min(lejos), max(lejos)))
    print("\n## El detalle: el rango de cada salida en casa y en el otro proveedor\n")
    print("| modelo entrenado solo con | salida | en su proveedor: mínimo–máximo | en el otro: mínimo–máximo |")
    print("|---|---|---|---|")
    for modelo, salida, (lo, hi), lo2, hi2 in detalle:
        print("| {} | {} | {:.3f} – {:.3f} | {:.3f} – {:.3f} |".format(modelo, salida, lo, hi, lo2, hi2))


if __name__ == "__main__":
    main()
