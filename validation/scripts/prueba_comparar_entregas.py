"""Prueba de validation/partido/comparar_entregas.py con dos entregas inventadas. No lee nada del partido.

    python validation/scripts/prueba_comparar_entregas.py

Los dos CSV inventados se escriben en una carpeta temporal, fuera del repo.
"""

import os
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA = tempfile.mkdtemp(prefix="entregas_inventadas_")
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import comparar_entregas as ce  # noqa: E402

blocks = ce.tracking.evaluated_blocks(ce.games.GAME)
N = blocks[-1][1] + 500  # unos frames de más después del último tramo, como en el partido
fallos = []


def comprobar(ok, texto):
    print("{}  {}".format("ok   " if ok else "FALLA", texto))
    if not ok:
        fallos.append(texto)


rng = np.random.default_rng(7)
antes = np.full(N, ce.pm.X, dtype=np.int8)
for a, b in blocks:
    t = a
    while t < b:
        largo = int(rng.integers(50, 600))
        antes[t:min(b, t + largo)] = int(rng.integers(0, 3))
        t += largo
despues = antes.copy()
(a1, b1), (a2, b2) = blocks
despues[a1:a1 + 30] = (antes[a1:a1 + 30] + 1) % 3  # 30 frames pegados al primer borde
despues[b2 - 10:b2] = (antes[b2 - 10:b2] + 1) % 3  # 10 pegados al último
despues[a1 + 100:a1 + 107] = (antes[a1 + 100:a1 + 107] + 1) % 3  # 7 a 100–106 frames del borde
despues[a1 + 5000:a1 + 5003] = (antes[a1 + 5000:a1 + 5003] + 1) % 3  # 3 lejos: celda pequeña
despues[5:9] = ce.pm.D  # 4 fuera de los tramos

res = ce.comparar(antes, despues, blocks)
comprobar(res["evaluados"] == (b1 - a1) + (b2 - a2), "cuenta los frames evaluados de los dos tramos")
comprobar(res["distintos"] == 50, "cuenta los 50 frames evaluados que cambian")
comprobar((res["cerca"], res["medio"], res["lejos"]) == (40, 7, 3), "los reparte por distancia al borde: 40, 7 y 3")
comprobar(res["fuera"] == 4, "cuenta aparte los 4 que cambian fuera de los tramos")
comprobar(sum(res["pares"].values()) == 50, "los pares de etiquetas suman lo mismo")
texto = "\n".join(ce.lineas(res, ["a.csv", "b.csv"]))
comprobar("| más de 250 | < 5 |" in texto, "una celda de 3 casos sale como «< 5»")
comprobar("no cuentan para la nota): < 5." in texto, "los 4 de fuera salen como «< 5»")
comprobar(not any(str(v) in texto for v in (a1 + 5000, a1 + 100, b2 - 10)), "no imprime ningún número de frame")
igual = ce.comparar(antes, antes, blocks)
comprobar(igual["distintos"] == 0 and igual["pares"] == {} and igual["posesiones"][0] == igual["posesiones"][1],
          "dos entregas iguales no difieren en nada")

# De punta a punta, con dos CSV inventados.
os.makedirs(CARPETA, exist_ok=True)
letras = np.array(["H", "A", "D", "X"])
rutas = []
for nombre, codigos in (("inventada_a.csv", antes), ("inventada_b.csv", despues)):
    ruta = os.path.join(CARPETA, nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("frame,label\n")
        f.write("\n".join("{},{}".format(i, l) for i, l in enumerate(letras[codigos])) + "\n")
    rutas.append(ruta)
proc = subprocess.run([sys.executable, os.path.join(ROOT, "validation", "partido", "comparar_entregas.py")] + rutas,
                      capture_output=True, text=True, encoding="utf-8")
comprobar(proc.returncode == 0 and "Con etiqueta distinta: 50" in proc.stdout, "el comando entero da los 50 frames")
proc = subprocess.run([sys.executable, os.path.join(ROOT, "validation", "partido", "comparar_entregas.py"),
                       rutas[0], os.path.join(CARPETA, "no_existe.csv")], capture_output=True, text=True, encoding="utf-8")
comprobar(proc.returncode == 1 and "No encuentro" in proc.stdout, "sin una de las entregas avisa y sale con 1")
if fallos:
    sys.exit("FALLA: " + "; ".join(fallos))
print("TODO BIEN")
