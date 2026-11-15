"""Entrena B9 (possession/aprendida.py): los rasgos de B2 más la dirección del balón, puntuada como B5.

    python validation/posesiones_cortas/entrenar_b9.py          # comprueba, entrena y escribe los coeficientes de B9
    python validation/posesiones_cortas/entrenar_b9.py --seco   # comprueba y entrena, sin escribir nada

DFL (Bassek et al., 2025, CC BY 4.0): lo puede ejecutar cualquiera, Claude incluido. Solo agregados. Sin azar.

Lo que hace es lo de B6, B7 y B8 en `validation/apuesta_b/entrenar.py` (docs/decisiones.md, 15/11), con los
rasgos de B9 (`aprendida.NOMBRES["b9"]`), y lo fija la entrada de B9 en docs/decisiones.md:

- **Filas:** los frames vivos en los que el flag y el control coinciden, uno de cada `entrenar.PASO`, con el
  balón «como el ATD» y `ball.clean`.
- **Regresión:** `entrenar.ajustar` (las mismas `LAMBDA`, `ITERACIONES` y `CIFRAS`).
- **Pliegues:** el de los 7 partidos («todos», el de la entrega) y uno sin cada partido (el del harness).
- **α:** de `entrenar.ALFAS_D_PROPIO`, la de más spellF1 medio en las dos condiciones que votan y con las dos
  convenciones, en los partidos de entrenamiento del pliegue, con la pieza de `D` de `main` dentro y sin
  oráculo. Si empatan, la más pequeña. Es `entrenar.elegir_alfa_d_propio`, reescrita para los rasgos de B9.
- **Escribe** el bloque de coeficientes con `entrenar.escribir`: B1 a B8 se copian del módulo tal cual.

**Comprobación del instrumento, antes de entrenar** (si falla, se para):
- los rasgos de B9 son los de B5 más tres columnas, y esas tres son las de la puerta
  (`puerta_direccion.rasgos_direccion`);
- la elección de α de este script, con los pesos de B2 y los rasgos de B5, devuelve la α de B5 de cada
  pliegue.
"""

import argparse
import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "apuesta_b"),
                 os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import dfl  # noqa: E402
import entrenar  # noqa: E402
import puerta_direccion  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, ball, dead_state, temporal  # noqa: E402

H, A, D = puntuar.H, puntuar.A, puntuar.D
CONJUNTO = "b9"
N_B5 = len(aprendida.NOMBRES["b5"])


def preparar(partido, comprobar):
    cargado = dfl.cargar(partido)
    gt = cargado["gt"]
    condiciones = {}
    for cond in dfl.VOTAN:
        trk = ball.clean(puntuar.solo_lectura(dfl.tracking_de(cargado, cond)))
        rasgos = aprendida.rasgos(trk, CONJUNTO)
        if comprobar:
            if not np.array_equal(rasgos[:, :N_B5], aprendida.rasgos(trk, "b5")):
                raise AssertionError("las primeras columnas de B9 no son los rasgos de B5 ({}, {})".format(partido, cond))
            if not np.array_equal(rasgos[:, N_B5:], puerta_direccion.rasgos_direccion(trk)):
                raise AssertionError("la dirección de B9 no es la de la puerta ({}, {})".format(partido, cond))
        condiciones[cond] = {"rasgos": rasgos, "blocks": trk.blocks, "visible": aprendida.balon_visible(trk),
                             "n1": aprendida.equipo_mas_cercano(trk), "estado_d": dead_state.evidence(trk)[0][:, D]}
    coinciden = (gt["flag"] == gt["control"]) & np.isin(gt["flag"], (H, A))
    filas = np.flatnonzero(coinciden & (np.arange(len(coinciden)) % entrenar.PASO == 0))
    return {"gt": gt, "condiciones": condiciones, "filas": filas}


def elegir_alfa(datos, partidos, pesos, conjunto, columnas):
    """Como `entrenar.elegir_alfa_d_propio`: α de ALFAS_D_PROPIO con más spellF1 medio, con el `D` de main."""
    logits = {(p, c): aprendida.logit(datos[p]["condiciones"][c]["rasgos"][:, columnas], pesos)
              for p in partidos for c in dfl.VOTAN}
    medias = []
    for alfa in entrenar.ALFAS_D_PROPIO:
        recuentos = collections.defaultdict(list)
        for p in partidos:
            for c in dfl.VOTAN:
                cond = datos[p]["condiciones"][c]
                score, permitido = aprendida.puntuacion_de(conjunto, logits[(p, c)], cond["visible"], alfa, cond["n1"])
                score[:, D] += cond["estado_d"]
                pred = temporal.decode(score, permitido, cond["blocks"])
                for convencion in dfl.CONVENCIONES:
                    recuentos[(c, convencion)].append(puntuar.contar(datos[p]["gt"][convencion], pred))
        medias.append(float(np.mean([puntuar.spell_f1(*puntuar.juntar(r)) for r in recuentos.values()])))
    return entrenar.ALFAS_D_PROPIO[int(np.argmax(medias))], medias


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seco", action="store_true", help="no escribe los coeficientes en el módulo")
    args = parser.parse_args()
    inicio = time.time()
    datos = collections.OrderedDict()
    for partido in dfl.PARTIDOS:
        datos[partido] = preparar(partido, comprobar=True)
        print("preparado {} en {:.0f} s".format(partido, time.time() - inicio), file=sys.stderr, flush=True)
    claves = ["todos"] + list(dfl.PARTIDOS)
    print("# B9: entrenamiento en la DFL\n")
    print("Comprobado: los rasgos de B9 son los de B5 más las tres columnas de la dirección de la puerta.\n")

    print("## Comprobación: la elección de α de este script, con los pesos de B2, da la α de B5\n")
    print("| pliegue | α de B5 en el módulo | α elegida aquí |")
    print("|---|---|---|")
    distintas = []
    for clave in claves:
        entrena = [p for p in dfl.PARTIDOS if p != clave]
        alfa, _ = elegir_alfa(datos, entrena, aprendida.coeficientes("b2", None if clave == "todos" else clave)["pesos"],
                              "b5", slice(0, N_B5))
        esperada = aprendida.coeficientes("b5", None if clave == "todos" else clave)["alfa"]
        print("| {} | {:g} | {:g} |".format(clave, esperada, alfa))
        if alfa != esperada:
            distintas.append(clave)
        print("  comprobado {} en {:.0f} s".format(clave, time.time() - inicio), file=sys.stderr, flush=True)
    if distintas:
        sys.exit("\nLa elección de α no repite la de B5 en {}: se para sin entrenar.".format(distintas))

    print("\n## B9 ({} rasgos; pesos propios y α como B5, con la pieza de `D` de main dentro)\n".format(
        len(aprendida.NOMBRES[CONJUNTO])))
    print("| pliegue | filas | último paso de Newton | α | spellF1 medio en entrenamiento por α ({}) |".format(
        ", ".join("{:g}".format(a) for a in entrenar.ALFAS_D_PROPIO)))
    print("|---|---|---|---|---|")
    nuevo = collections.OrderedDict()
    estandarizados = None
    c0 = entrenar.CONDICION_ENTRENAMIENTO
    for clave in claves:
        entrena = [p for p in dfl.PARTIDOS if p != clave]
        X = np.vstack([datos[p]["condiciones"][c0]["rasgos"][datos[p]["filas"]] for p in entrena])
        y = np.concatenate([(datos[p]["gt"]["flag"][datos[p]["filas"]] == H).astype(float) for p in entrena])
        pesos, w, paso = entrenar.ajustar(X, y)
        del X
        alfa, medias = elegir_alfa(datos, entrena, pesos, CONJUNTO, slice(None))
        nuevo[clave] = (alfa, pesos)
        if clave == "todos":
            estandarizados = w
        print("| {} | {} | {:.1e} | {:g} | {} |".format(
            "los 7" if clave == "todos" else "sin " + clave, len(y), paso, alfa,
            " / ".join("{:.3f}".format(m).replace(".", ",") for m in medias)))
        print("  hecho {} en {:.0f} s".format(clave, time.time() - inicio), file=sys.stderr, flush=True)
    print("\nPesos del modelo de los 7, con los rasgos divididos por su raíz cuadrática media (los 5 mayores y los "
          "de la dirección):\n")
    nombres = aprendida.NOMBRES[CONJUNTO]
    for j in list(np.argsort(-np.abs(estandarizados))[:5]) + list(range(N_B5, len(nombres))):
        print("- {}: {:+.2f}".format(nombres[j], estandarizados[j]).replace(".", ","))

    modelos = {c: collections.OrderedDict((k, (j["alfa"], j["pesos"])) for k, j in aprendida.COEFICIENTES[c].items())
               for c in aprendida.CONJUNTOS if c != CONJUNTO}
    modelos[CONJUNTO] = nuevo
    if args.seco:
        print("\n--seco: no se escribe nada.")
    else:
        entrenar.escribir(modelos)
        print("\nescritos los coeficientes de B9 en possession/aprendida.py (B1 a B8 copiados tal cual)")
    print("tiempo: {:.0f} s".format(time.time() - inicio), file=sys.stderr)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
