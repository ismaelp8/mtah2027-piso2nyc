"""Prueba `validation/partido/comparar_paradas.py` (los números de los criterios de daño de una capa de `D`) sin datos.

    python validation/scripts/prueba_comparar_paradas.py

Lo puede ejecutar cualquiera, Claude incluido. Las entregas son inventadas. Comprueba la distancia a un borde en sus
límites exactos (249 frames es «cerca», 250 no), y en seis casos inventados: solo se mueven bordes (dentro de 10 s), una
parada nueva lejos de todo, una partida, dos juntadas, una que desaparece y una racha corta; los desplazamientos por
intervalos; la lectura de los criterios; que lo impreso no lleva ningún frame; y `main` con dos CSV de 199.319 filas.
"""

import contextlib
import io
import os
import re
import shutil
import sys
import tempfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import games  # noqa: E402
import comparar_paradas as cp  # noqa: E402
from possession import tracking  # noqa: E402
from possession.tracking import A, D, H, X  # noqa: E402

FALLOS = []
N = 10000
BLOQUES = ((100, 5000), (5100, 10000))
PARADAS = ((1000, 1500), (3000, 3200), (6000, 6400), (8000, 8100), (9000, 9300))


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def base():
    c = np.full(N, X)
    for a, b in BLOQUES:
        c[a:b] = H
    c[2000:2600] = A
    for a, b in PARADAS:
        c[a:b] = D
    return c


def prueba_distancia():
    print("\n1. La distancia a un borde")
    d = cp.distancia_a_un_borde([99, 100, 150, 199, 200, 449, 450, 2000], [(100, 200)])
    check("pegados al borde, 0; dentro, al más cercano; a 249, cerca; a 250, lejos",
          d.tolist() == [0, 0, 49, 0, 0, 249, 250, 1800], d.tolist())
    check("sin paradas, infinito", np.isinf(cp.distancia_a_un_borde([5], [])).all())


def prueba_casos():
    print("\n2. Seis casos inventados")
    antes = base()

    # Solo bordes: el fin de la primera, 100 frames más tarde; el inicio de la segunda, 50 antes.
    despues = antes.copy()
    despues[1500:1600] = D
    despues[2950:3000] = D
    r = cp.comparar(antes, despues, BLOQUES)
    check("solo bordes: 150 frames, todos cerca", r["distintos"] == 150 and r["cerca"] == 150 and r["lejos"] == 0)
    check("ninguna nueva, partida, juntada ni que desaparece", r["nuevas"] == r["partidas"] == r["juntadas"]
          == r["desaparecen"] == 0 and r["paradas"] == [5, 5])
    check("cambian dos: una con otro fin y otra con otro inicio", r["cambian"] == 2 and r["cambia_el_fin"] == 1
          and r["cambia_el_inicio"] == 1)
    check("el fin se mueve 1-5 s después y el inicio 1-5 s antes",
          r["desplazamiento_fin"]["1-5 s después"] == 1 and r["desplazamiento_fin"]["igual"] == 1
          and r["desplazamiento_inicio"]["1-5 s antes"] == 1 and r["desplazamiento_inicio"]["igual"] == 1)
    check("de qué a qué", r["pares"] == {(H, D): 150}, r["pares"])
    check("la lectura: cumple los cuatro", all(ok for _, ok in cp.lectura(r)))
    texto = "\n".join(cp.lineas(r, ["a.csv", "b.csv"], ["0" * 64, "f" * 64]))
    numeros = {str(v) for a, b in PARADAS for v in (a, b)} | {"1600", "2950"}
    check("lo impreso no lleva ningún frame", not any(re.search(r"\b{}\b".format(n), texto) for n in numeros))

    despues = antes.copy()
    despues[2100:2200] = D
    r = cp.comparar(antes, despues, BLOQUES)
    check("una parada nueva lejos de todo: lejos y nueva", r["lejos"] > 0 and r["nuevas"] == 1
          and [ok for _, ok in cp.lectura(r)] == [True, False, False, True])

    despues = antes.copy()
    despues[6150:6200] = H
    r = cp.comparar(antes, despues, BLOQUES)
    check("una partida", r["partidas"] == 1 and r["paradas"] == [5, 6] and r["una_a_una"] == 4)

    despues = antes.copy()
    despues[8100:9000] = D
    r = cp.comparar(antes, despues, BLOQUES)
    check("dos juntadas (y cambios lejos de un borde)", r["juntadas"] == 1 and r["lejos"] > 0
          and r["paradas"] == [5, 4])

    despues = antes.copy()
    despues[8000:8100] = H
    r = cp.comparar(antes, despues, BLOQUES)
    check("una que desaparece", r["desaparecen"] == 1 and r["paradas"] == [5, 4])

    despues = antes.copy()
    despues[3300:3310] = D
    r = cp.comparar(antes, despues, BLOQUES)
    lectura = [ok for _, ok in cp.lectura(r)]
    check("una racha corta (10 frames de D a 100 del borde): cerca, pero corta y nueva",
          r["lejos"] == 0 and r["cortas"][("paradas", 25)] == 1 and lectura == [False, True, False, True], lectura)
    check("fuera de los tramos no cuenta", cp.comparar(antes, np.where(np.arange(N) < 100, D, antes),
                                                       BLOQUES)["distintos"] == 0)
    despues = antes.copy()
    despues[1749:1751] = D  # a 249 y a 250 frames del fin de la primera parada (1500)
    r = cp.comparar(antes, despues, BLOQUES)
    check("a 249 frames de un borde es «cerca»; a 250, «lejos»", r["cerca"] == 1 and r["lejos"] == 1,
          (r["cerca"], r["lejos"]))


def prueba_desplazamientos():
    print("\n3. Los intervalos del desplazamiento")
    r = cp.repartir_desplazamientos([-126, -125, -26, -25, -1, 0, 1, 25, 26, 125, 126])
    check("en sus bordes exactos", [r[e] for e in cp.ETIQUETAS_DESPLAZAMIENTO] == [1, 2, 2, 1, 2, 2, 1],
          [r[e] for e in cp.ETIQUETAS_DESPLAZAMIENTO])


def prueba_main():
    print("\n4. main con dos CSV")
    carpeta = os.path.realpath(tempfile.mkdtemp(prefix="mtah_prueba_paradas_"))
    datos = os.path.realpath(games.DATA_DIR)
    if carpeta.startswith(datos + os.sep) or "mtah2027-data" in carpeta.lower():
        raise SystemExit("la carpeta temporal cae dentro de los datos del partido: no se ejecuta")
    try:
        n = games.GAMES[games.GAME]["n_video_frames"]
        letras = np.full(n, "X", dtype=object)
        for a, b in tracking.evaluated_blocks(games.GAME):
            letras[a:b] = "H"
        letras[11185:60000] = "D"  # un 31 % de D en lo evaluado: dentro de la banda del plan
        antes = letras.copy()
        letras[60000:60100] = "D"
        rutas = []
        for nombre, valores in (("antes", antes), ("despues", letras)):
            ruta = os.path.join(carpeta, nombre + ".csv")
            with open(ruta, "w") as f:
                f.write("frame,label\n" + "".join("{},{}\n".format(i, v) for i, v in enumerate(valores)))
            rutas.append(ruta)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = cp.main(rutas)
        texto = salida.getvalue()
        check("acaba bien e imprime el sha256 de las dos", codigo == 0 and cp.sha256(rutas[0]) in texto
              and cp.sha256(rutas[1]) in texto)
        check("y la lectura (cumple)", "NO CUMPLE" not in texto and texto.count(": cumple") == 4, texto[-400:])
        check("sin frames", not re.search(r"\b(11185|60000|60100)\b", texto))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def main():
    print("Prueba de comparar_paradas (sin datos de ningún partido)")
    prueba_distancia()
    prueba_casos()
    prueba_desplazamientos()
    prueba_main()
    print("\n" + ("TODO BIEN" if not FALLOS else "FALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS))))
    return 1 if FALLOS else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
