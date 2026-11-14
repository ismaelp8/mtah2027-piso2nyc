"""Entrena la evidencia aprendida de la apuesta B (possession/aprendida.py) con los 7 partidos de la DFL.

    python validation/apuesta_b/entrenar.py          # entrena y escribe los coeficientes en possession/aprendida.py
    python validation/apuesta_b/entrenar.py --seco   # entrena y enseña los agregados, sin escribir nada

Son datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), con la caché del harness: lo puede
ejecutar cualquiera, Claude incluido. Solo imprime agregados. No tiene azar: en la misma máquina, dos
ejecuciones escriben los mismos coeficientes (comprobado el 14/11). En otra máquina, el ajuste usa BLAS y
LAPACK y podría cambiar la sexta cifra; la entrega no se ve afectada, porque lee los coeficientes ya
escritos en el módulo. Tarda unos minutos.

Lo que hace es lo que se fijó antes de medir (docs/decisiones.md, 14/11, «apuesta B»):

- **Datos:** cada partido con el balón «como el ATD» (`dfl.tracking_de`, la misma degradación que vota en
  el harness). Se entrena con los frames vivos en los que las dos convenciones coinciden (`flag` =
  `control`), uno de cada `PASO`.
- **Modelo:** regresión logística de `H` frente a `A` sobre `aprendida.rasgos`, sin término independiente,
  con L2 (`LAMBDA`) sobre los rasgos divididos por su raíz cuadrática media. Newton con `ITERACIONES`
  fijas. Los pesos se escriben con `CIFRAS` cifras significativas.
- **Escala α:** de `ALFAS`, la que da más `spellF1` medio en las dos condiciones que votan y con las dos
  convenciones, sobre los partidos de entrenamiento del pliegue, con el decodificador de `main` y el `D`
  oráculo, igual que el harness. Si empatan, la más pequeña.
- **Pliegues:** uno por partido, entrenado y escalado sin él, y el de los 7, que es el de la entrega.

Además enseña, como descripción, el acierto por frame de cada pliegue en el partido que dejó fuera, frente
a N1 (el jugador más cercano). No decide nada: decide el harness.
"""

import argparse
import collections
import os
import re
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, candidates, temporal  # noqa: E402

H, A = puntuar.H, puntuar.A
# Fijados antes de medir y sin ajustar (docs/decisiones.md, 14/11): `PASO`, la condición y `ALFAS` en la
# entrada de los candidatos; `LAMBDA`, `ITERACIONES` y `CIFRAS` al escribir este código, antes de medir.
CONDICION_ENTRENAMIENTO = "como el ATD"
PASO = 5
LAMBDA = 1.0
ITERACIONES = 25
ALFAS = (1 / 16, 1 / 8, 1 / 4, 1 / 2, 1.0, 2.0)
CIFRAS = 6
MODULO = os.path.join(ROOT, "possession", "aprendida.py")
INICIO, FIN = "# >>> COEFICIENTES", "# <<< COEFICIENTES"


def preparar(partido):
    """Rasgos de B2 (los de B1 son las primeras columnas), etiquetas y N1 de un partido, por condición."""
    cargado = dfl.cargar(partido)
    gt = cargado["gt"]
    condiciones = {}
    for condicion in dfl.VOTAN:
        trk = dfl.tracking_de(cargado, condicion)
        condiciones[condicion] = {"rasgos": aprendida.rasgos(trk, "b2"), "blocks": trk.blocks,
                                  "visible": ~np.isnan(trk.bx), "n1": candidates.nearest_team(trk)}
        if partido == dfl.PARTIDOS[0] and condicion == CONDICION_ENTRENAMIENTO:
            # B1 son las primeras columnas de B2: se comprueba una vez con el código del módulo.
            b1 = aprendida.rasgos(trk, "b1")
            if aprendida.NOMBRES["b2"][:b1.shape[1]] != aprendida.NOMBRES["b1"] or not np.array_equal(
                    b1, condiciones[condicion]["rasgos"][:, :b1.shape[1]]):
                raise AssertionError("los rasgos de B1 no son las primeras columnas de los de B2")
    coinciden = (gt["flag"] == gt["control"]) & np.isin(gt["flag"], (H, A))
    filas = np.flatnonzero(coinciden & (np.arange(len(coinciden)) % PASO == 0))
    return {"gt": gt, "condiciones": condiciones, "filas": filas, "coinciden": coinciden}


def ajustar(X, y):
    """Pesos de la regresión logística (sin término independiente) en las unidades de los rasgos."""
    rms = np.sqrt(np.mean(X ** 2, axis=0))
    rms[rms == 0] = 1.0
    Z = X / rms
    w = np.zeros(Z.shape[1])
    paso = np.inf
    for _ in range(ITERACIONES):
        p = 1.0 / (1.0 + np.exp(-np.clip(Z @ w, -30, 30)))
        gradiente = Z.T @ (p - y) + LAMBDA * w
        hessiana = (Z * (p * (1 - p))[:, None]).T @ Z + LAMBDA * np.eye(len(w))
        delta = np.linalg.solve(hessiana, gradiente)
        w = w - delta
        paso = float(np.max(np.abs(delta)))
    pesos = tuple(float("{:.{}g}".format(v, CIFRAS)) for v in w / rms)
    return pesos, w, paso


def elegir_alfa(datos, partidos, pesos, k):
    """α de ALFAS con más spellF1 medio (dos condiciones que votan × dos convenciones) en `partidos`."""
    logits = {(p, c): aprendida.logit(datos[p]["condiciones"][c]["rasgos"][:, :k], pesos)
              for p in partidos for c in dfl.VOTAN}
    medias = []
    for alfa in ALFAS:
        recuentos = collections.defaultdict(list)
        for p in partidos:
            _, permitido = puntuar.d_oraculo(datos[p]["gt"]["flag"])
            for c in dfl.VOTAN:
                score, _ = aprendida.puntuacion(logits[(p, c)], alfa)
                pred = temporal.decode(score, permitido, datos[p]["condiciones"][c]["blocks"])
                for convencion in dfl.CONVENCIONES:
                    recuentos[(c, convencion)].append(puntuar.contar(datos[p]["gt"][convencion], pred))
        medias.append(float(np.mean([puntuar.spell_f1(*puntuar.juntar(r)) for r in recuentos.values()])))
    return ALFAS[int(np.argmax(medias))], medias


def acierto_fuera(dato, pesos, k):
    """Aciertos por frame en el partido que quedó fuera («como el ATD», frames vivos donde coinciden)."""
    c = dato["condiciones"][CONDICION_ENTRENAMIENTO]
    z = aprendida.logit(c["rasgos"][:, :k], pesos)
    verdad = dato["gt"]["flag"]
    vivos = dato["coinciden"]
    salida = {}
    for nombre, mascara in (("con balón", vivos & c["visible"]), ("sin balón", vivos & ~c["visible"])):
        acierta = np.where(z > 0, H, np.where(z < 0, A, -1)) == verdad
        salida[nombre] = (int(np.sum(acierta & mascara)), int(np.sum(mascara)),
                          int(np.sum((c["n1"] == verdad) & mascara)))
    return salida


def bloque_de_coeficientes(modelos):
    lineas = [INICIO,
              "# Los escribe validation/apuesta_b/entrenar.py. «todos»: los 7 partidos de la DFL (la entrega); cada",
              "# partido: el pliegue entrenado y escalado sin él (el harness, con «dejar_fuera»).",
              "COEFICIENTES = {"]
    for conjunto in aprendida.CONJUNTOS:
        lineas.append("    \"{}\": {{".format(conjunto))
        for clave, (alfa, pesos) in modelos[conjunto].items():
            lineas.append("        \"{}\": {{\"alfa\": {!r}, \"pesos\": (".format(clave, alfa))
            for i in range(0, len(pesos), 5):
                lineas.append("            " + " ".join("{!r},".format(p) for p in pesos[i:i + 5]))
            lineas.append("        )},")
        lineas.append("    },")
    lineas += ["}", FIN]
    return lineas


def escribir(modelos):
    with open(MODULO, encoding="utf-8", newline="") as handle:
        texto = handle.read()
    salto = "\r\n" if "\r\n" in texto else "\n"
    patron = re.compile(re.escape(INICIO) + ".*?" + re.escape(FIN), re.S)
    if len(patron.findall(texto)) != 1:
        raise AssertionError("no encuentro un único bloque de coeficientes en {}".format(MODULO))
    nuevo = patron.sub(lambda _: salto.join(bloque_de_coeficientes(modelos)), texto)
    compile(nuevo, MODULO, "exec")  # un módulo roto dejaría sin harness a todos: se comprueba antes
    temporal_ruta = MODULO + ".nuevo"
    with open(temporal_ruta, "w", encoding="utf-8", newline="") as handle:
        handle.write(nuevo)
    os.replace(temporal_ruta, MODULO)


def pct(a, b):
    return "{:.1f}".format(100.0 * a / max(b, 1)).replace(".", ",")


def main():
    parser = argparse.ArgumentParser(description="Entrena la evidencia aprendida de la apuesta B en la DFL.")
    parser.add_argument("--seco", action="store_true", help="no escribe los coeficientes en el módulo")
    args = parser.parse_args()
    inicio = time.time()
    datos = collections.OrderedDict()
    for partido in dfl.PARTIDOS:
        datos[partido] = preparar(partido)
        print("preparado {} ({} filas de entrenamiento) en {:.0f} s".format(
            partido, len(datos[partido]["filas"]), time.time() - inicio), file=sys.stderr)

    modelos = {}
    print("Apuesta B: entrenamiento en la DFL ({} partidos, balón «{}», uno de cada {} frames vivos en los "
          "que coinciden las dos convenciones)".format(len(datos), CONDICION_ENTRENAMIENTO, PASO))
    for conjunto in aprendida.CONJUNTOS:
        k = len(aprendida.NOMBRES[conjunto])
        modelos[conjunto] = collections.OrderedDict()
        print()
        print("### {} ({} rasgos)".format(conjunto.upper(), k))
        print()
        print("| pliegue | filas | último paso de Newton | α | spellF1 medio en entrenamiento por α ({}) |".format(
            ", ".join("{:g}".format(a) for a in ALFAS)))
        print("|---|---|---|---|---|")
        aciertos = collections.defaultdict(lambda: np.zeros(3, dtype=np.int64))
        estandarizados = None
        for clave in ["todos"] + list(dfl.PARTIDOS):
            entrena = [p for p in dfl.PARTIDOS if p != clave]
            c = CONDICION_ENTRENAMIENTO
            X = np.vstack([datos[p]["condiciones"][c]["rasgos"][datos[p]["filas"], :k] for p in entrena])
            y = np.concatenate([(datos[p]["gt"]["flag"][datos[p]["filas"]] == H).astype(float) for p in entrena])
            pesos, w, paso = ajustar(X, y)
            del X
            alfa, medias = elegir_alfa(datos, entrena, pesos, k)
            modelos[conjunto][clave] = (alfa, pesos)
            print("| {} | {} | {:.1e} | {:g} | {} |".format(
                "los 7" if clave == "todos" else "sin " + clave, len(y), paso, alfa,
                " / ".join("{:.3f}".format(m).replace(".", ",") for m in medias)))
            if clave == "todos":
                estandarizados = w
            else:
                for nombre, valores in acierto_fuera(datos[clave], pesos, k).items():
                    aciertos[nombre] += valores
            print("  hecho {} {} en {:.0f} s".format(conjunto, clave, time.time() - inicio), file=sys.stderr)
        print()
        print("Acierto por frame en el partido que quedó fuera (descriptivo; «{}», frames vivos donde coinciden "
              "las convenciones, los 7 pliegues juntos):".format(CONDICION_ENTRENAMIENTO))
        print()
        print("| frames | cuántos | aprendida | N1 |")
        print("|---|---|---|---|")
        for nombre, (bien, total, n1) in aciertos.items():
            print("| {} | {} | {} % | {} % |".format(nombre, total, pct(bien, total), pct(n1, total)))
        print()
        print("Pesos del modelo de los 7, con los rasgos divididos por su raíz cuadrática media (los 5 mayores):")
        print()
        for j in np.argsort(-np.abs(estandarizados))[:5]:
            print("- {}: {:+.2f}".format(aprendida.NOMBRES[conjunto][j], estandarizados[j]).replace(".", ","))
    if args.seco:
        print("\n--seco: no se escribe nada.")
    else:
        escribir(modelos)
        print("\nescritos los coeficientes en possession/aprendida.py")
    print("tiempo: {:.0f} s".format(time.time() - inicio), file=sys.stderr)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
