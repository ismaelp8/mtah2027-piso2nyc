"""Una entrega de prueba con un solo comando: la genera, cuenta el balón fuera y la compara con la vigente.

**Lee el partido: lo ejecuta una persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`). Imprime solo
agregados: los de los tres scripts que llama, uno detrás de otro, para pegar una sola salida.

    python validation/partido/probar_entrega.py prueba_x --capa modulo.funcion
    python validation/partido/probar_entrega.py prueba_b9 --pieza candidates=aprendida.evidence_b9

1. `python -m possession.pipeline --name <nombre> [--pieza ...] [--capa ...]`: escribe la entrega de prueba en
   evaluation/results/ (con el nombre de la entrega da error) e imprime su resumen y su sha256;
2. `validation/partido/balon_fuera.py --entrega <nombre>`: el recuento del balón fuera (D7);
3. `validation/partido/comparar_entregas.py <vigente> <nombre>`: cuánto cambia y dónde, frente a la vigente
   (`--contra`, por defecto `equipo_v11`, la de K3, la vigente desde el 17/11 por la tarde).

Si el paso 1 falla, no sigue.
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIGENTE = "equipo_v11"  # la entrega vigente (CLAUDE.md, «Dónde estamos»)


def comandos(nombre, piezas=(), capas=(), contra=VIGENTE, python=sys.executable):
    """Los tres comandos, como listas para subprocess, con su título."""
    generar = [python, "-m", "possession.pipeline", "--name", nombre]
    for pieza in piezas:
        generar += ["--pieza", pieza]
    for capa in capas:
        generar += ["--capa", capa]
    return [
        ("1. La entrega de prueba", generar),
        ("2. El balón fuera (D7)", [python, os.path.join("validation", "partido", "balon_fuera.py"),
                                    "--entrega", nombre]),
        ("3. Frente a {}".format(contra), [python, os.path.join("validation", "partido", "comparar_entregas.py"),
                                          contra, nombre]),
    ]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("nombre", help="nombre de la entrega de prueba, sin .csv")
    ap.add_argument("--pieza", action="append", default=[], help="como en possession.pipeline")
    ap.add_argument("--capa", action="append", default=[], help="como en possession.pipeline")
    ap.add_argument("--contra", default=VIGENTE, help="la entrega con la que se compara (por defecto la vigente)")
    args = ap.parse_args(argv)
    for paso, (titulo, comando) in enumerate(comandos(args.nombre, args.pieza, args.capa, args.contra)):
        print("\n## {}\n".format(titulo), flush=True)
        codigo = subprocess.call(comando, cwd=ROOT)
        if codigo and paso == 0:
            print("\nEl paso 1 ha fallado: no sigo.")
            return codigo
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
