"""Referencia de los rasgos de B5 en los datos abiertos, para compararla con el partido (P2 de BITACORA.md).

    python validation/investigacion_1116/referencia_rasgos_b5.py

Datos abiertos de otros partidos: los 7 de la DFL (Bassek et al., 2025, CC BY 4.0), «como el ATD», y los 10 de
`lector.ENTRENAMIENTO` de SkillCorner (licencia MIT), «detectado». Lo puede ejecutar cualquiera, Claude incluido. Solo
imprime agregados y escribe `referencia_rasgos_b5.json` junto a este fichero. La regla está en BITACORA.md (P2), escrita
antes de ejecutarlo.
"""

import json
import os
import subprocess
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"), ROOT,
                os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, carpeta)
import dfl  # noqa: E402
import lector as lc  # noqa: E402
from possession import aprendida, ball  # noqa: E402

SALIDA = os.path.join(AQUI, "referencia_rasgos_b5.json")
TOP = 10


def resumen_rasgos(trk):
    """(matriz de rasgos en los frames de los tramos con el balón visible, signo de B5 frente al del más cercano).

    Es la función que usa también validation/partido/rasgos_b5.py, para que el partido y la referencia se calculen
    igual."""
    trk = ball.clean(trk)
    rasgos = aprendida.rasgos(trk, "b2")
    en_tramos = np.zeros(len(trk.bx), dtype=bool)
    for a, b in trk.blocks:
        en_tramos[a:b] = True
    visible = en_tramos & np.isfinite(np.asarray(trk.bx, dtype=float)) & np.isfinite(np.asarray(trk.by, dtype=float))
    z = aprendida.logit(rasgos, aprendida.coeficientes("b5")["pesos"])
    cercano = aprendida.equipo_mas_cercano(trk)
    signo = np.where(z > 0, 0, np.where(z < 0, 1, -1))
    opina = visible & (cercano >= 0) & (signo >= 0)
    acuerdo = float(np.mean(signo[opina] == cercano[opina])) if opina.any() else float("nan")
    return rasgos[visible], acuerdo


def cuantiles(matriz):
    """{nombre: [mediana, p90]} del valor absoluto de cada rasgo."""
    absoluto = np.abs(matriz)
    return {nombre: [round(float(np.median(absoluto[:, j])), 6), round(float(np.percentile(absoluto[:, j], 90)), 6)]
            for j, nombre in enumerate(aprendida.NOMBRES["b2"])}


def commit():
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE,
                              universal_newlines=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "sin git"


def main():
    por_partido, acuerdos, dfl_juntas = {}, {}, []
    for partido in dfl.PARTIDOS:
        matriz, acuerdo = resumen_rasgos(dfl.tracking_de(dfl.cargar(partido), "como el ATD"))
        por_partido["DFL " + partido] = cuantiles(matriz)
        acuerdos["DFL " + partido] = round(acuerdo, 4)
        dfl_juntas.append(matriz)
        print("DFL {}".format(partido), file=sys.stderr, flush=True)
    ids = list(lc.ENTRENAMIENTO)
    lc.exigir_solo_entrenamiento(ids)
    for id_ in ids:
        trk, _ = lc.tracking_de(lc.leer_crudo(id_), "detectado", id_)
        matriz, acuerdo = resumen_rasgos(trk)
        por_partido["SkillCorner {}".format(id_)] = cuantiles(matriz)
        acuerdos["SkillCorner {}".format(id_)] = round(acuerdo, 4)
        print("SkillCorner {}".format(id_), file=sys.stderr, flush=True)
    nombres = aprendida.NOMBRES["b2"]
    pesos = np.asarray(aprendida.coeficientes("b5")["pesos"], dtype=float)
    desviacion = np.concatenate(dfl_juntas).std(axis=0)
    importancia = np.abs(pesos) * desviacion
    orden = [nombres[j] for j in np.argsort(-importancia)]
    top = orden[:TOP]
    rango = {}
    for nombre in nombres:
        medianas = [por_partido[p][nombre][0] for p in por_partido]
        p90 = [por_partido[p][nombre][1] for p in por_partido]
        rango[nombre] = [min(medianas), max(medianas), min(p90), max(p90)]
    salida = {"commit": commit(), "conjunto": "b2 (los rasgos de B5)", "frames": "tramos evaluados con el balón visible",
              "top": top, "importancia": {n: round(float(importancia[nombres.index(n)]), 6) for n in nombres},
              "rango": rango, "por_partido": por_partido, "acuerdo_b5_mas_cercano": acuerdos}
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print("Referencia de los rasgos de B5 ({} partidos abiertos). Mediana del valor absoluto: mínimo–máximo entre "
          "partidos.\n".format(len(por_partido)))
    print("| rasgo | importancia | mediana: mín–máx | p90: mín–máx |")
    print("|---|---|---|---|")
    for nombre in orden:
        r = rango[nombre]
        print("| {}{} | {:.3f} | {:.3f}–{:.3f} | {:.3f}–{:.3f} |".format(
            "**" if nombre in top else "", nombre + ("**" if nombre in top else ""), importancia[nombres.index(nombre)],
            r[0], r[1], r[2], r[3]))
    valores = list(acuerdos.values())
    print("\nAcuerdo del signo de B5 con el más cercano (frames con balón): de {:.1f} a {:.1f} %".format(
        100 * min(valores), 100 * max(valores)))
    print("Escrito {}".format(os.path.relpath(SALIDA, ROOT)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
