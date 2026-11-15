"""Dibuja la GT pública y una entrega nuestra, una encima de otra, para verlas junto al vídeo.

**Lee una entrega nuestra (etiquetas del partido frame a frame): lo ejecuta una persona, en local, nunca
Claude** (regla nº 1 de `CLAUDE.md`). La imagen que escribe tampoco se le enseña a Claude.

    python validation/partido/ver_ventana.py equipo_v3

Para qué: `RULES.md` permite mirar el vídeo y los datos para entender y depurar, y `CHALLENGE.md` dice que
la GT pública está para ver cómo se etiquetan los casos. Esta imagen dice en qué momentos de los 5 minutos
públicos la entrega y la GT no coinciden, para ir a esos momentos del vídeo.

**Lo que no se puede hacer con lo que se vea:** convertirlo en etiquetas, correcciones o constantes ligadas
a momentos del partido, ni ajustar nada con estos 5 minutos. Lo que se aprenda se convierte en una idea
general y se mide en los partidos abiertos (`validation/harness/`, `validation/skillcorner/`).

Qué dibuja: una fila por minuto, con tres tiras:
- `GT`: la etiqueta pública (azul `H`, naranja `A`, gris `D`);
- `nuestra`: la entrega;
- `difieren`: rojo donde no coinciden.

El eje es el tiempo del vídeo táctico (minuto:segundo), para buscarlo en el reproductor.

- No imprime ninguna etiqueta: solo la ruta de la imagen.
- No escribe en el repo: la imagen va a `~/mtah2027-salidas/` (o donde diga `--salida`).
- Si falla, imprime solo el tipo de error y la línea del código.
"""

import argparse
import os
import sys
import traceback

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import possession_metrics as pm  # noqa: E402

FPS = 25
GT_PUBLICA = os.path.join(ROOT, "evaluation", "gt", "BAR-ATH_possession_gt_public.csv")
RESULTADOS = os.path.join(ROOT, "evaluation", "results")
SALIDAS = os.path.join(os.path.expanduser("~"), "mtah2027-salidas")
SEGUNDOS_POR_FILA = 60
COLORES = {0: (0.12, 0.47, 0.71), 1: (1.0, 0.5, 0.05), 2: (0.6, 0.6, 0.6), 3: (1.0, 1.0, 1.0)}  # H, A, D, X
ROJO, BLANCO = (0.84, 0.15, 0.16), (1.0, 1.0, 1.0)


def codigos(ruta):
    return pm.label_codes(pm.read_label_csv(ruta))


def tira(valores, colores):
    """Imagen de 1 × n × 3 con el color de cada frame."""
    out = np.ones((1, len(valores), 3))
    for valor, color in colores.items():
        out[0, valores == valor] = color
    return out


def reloj(frame):
    segundos = int(frame // FPS)
    return "{}:{:02d}".format(segundos // 60, segundos % 60)


def dibujar(gt, pred, salida, titulo):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tramos = pm.valid_runs(gt)
    if not tramos:
        raise ValueError("la GT no tiene ningún frame evaluado")
    filas = []
    for inicio, fin in tramos:
        paso = SEGUNDOS_POR_FILA * FPS
        filas += [(a, min(a + paso, fin)) for a in range(inicio, fin, paso)]
    ancho = SEGUNDOS_POR_FILA * FPS
    figura, ejes = plt.subplots(len(filas), 1, figsize=(16, 1.5 * len(filas) + 1), squeeze=False)
    for eje, (a, b) in zip(ejes[:, 0], filas):
        g, p = gt[a:b], pred[a:b]
        imagen = np.ones((3, ancho, 3))
        imagen[0, :b - a] = tira(g, COLORES)[0]
        imagen[1, :b - a] = tira(p, COLORES)[0]
        imagen[2, :b - a] = tira((g != p).astype(int), {1: ROJO, 0: BLANCO})[0]
        eje.imshow(imagen, aspect="auto", interpolation="nearest", extent=(0, ancho, 3, 0))
        eje.set_yticks([0.5, 1.5, 2.5])
        eje.set_yticklabels(["GT", "nuestra", "difieren"])
        marcas = np.arange(0, ancho + 1, 5 * FPS)
        eje.set_xticks(marcas)
        eje.set_xticklabels([reloj(a + m) for m in marcas], fontsize=8)
        eje.set_xlim(0, ancho)
        for y in (1, 2):
            eje.axhline(y, color="white", linewidth=1)
    ejes[0, 0].set_title(titulo + " · azul H, naranja A, gris D · eje: tiempo del vídeo táctico", fontsize=10)
    figura.tight_layout()
    carpeta = os.path.dirname(salida)
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    figura.savefig(salida, dpi=130)
    plt.close(figura)


def main():
    parser = argparse.ArgumentParser(description="Dibuja la GT pública y una entrega, para verlas junto al vídeo.")
    parser.add_argument("entrega", help="nombre de la entrega en evaluation/results (sin .csv) o ruta a un CSV")
    parser.add_argument("--gt", default=GT_PUBLICA, help="CSV de la GT (por defecto, la pública)")
    parser.add_argument("--salida", default=None, help="ruta de la imagen (por defecto, en ~/mtah2027-salidas)")
    args = parser.parse_args()

    ruta = args.entrega if os.path.isfile(args.entrega) else os.path.join(RESULTADOS, args.entrega + ".csv")
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    salida = args.salida or os.path.join(SALIDAS, "ventana_{}.png".format(nombre))
    if os.path.abspath(salida).lower().startswith(os.path.abspath(ROOT).lower() + os.sep):
        sys.exit("La imagen no se escribe dentro del repo: elige otra ruta con --salida.")
    try:
        gt, pred = codigos(args.gt), codigos(ruta)
        if len(gt) != len(pred):
            raise ValueError("la GT y la entrega no tienen el mismo número de filas")
        dibujar(gt, pred, salida, nombre)
    except Exception as error:  # sin el mensaje: podría llevar valores de datos
        ultimo = traceback.extract_tb(sys.exc_info()[2])[-1]
        sys.exit("ERROR: {} en {}:{}".format(type(error).__name__, os.path.basename(ultimo.filename), ultimo.lineno))
    print("imagen escrita en {}".format(salida))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
