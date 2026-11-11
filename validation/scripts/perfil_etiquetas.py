"""Perfil de una secuencia de etiquetas por frame: cuántas posesiones hay, cuánto duran y su huella.

Lee un CSV `frame,label` (H/A/D/X, el mismo formato que una entrega) e imprime solo agregados.

Para qué sirve
--------------
Para comparar etiquetas de distinto origen con la misma vara:

- la GT pública de 5 minutos, para entender la métrica (nunca para elegir parámetros);
- etiquetas derivadas de datos abiertos de otros partidos (flags de la DFL, eventos de StatsBomb...);
- la tabla oficial de retrasos de EVALUATION.md, que suponemos que es la huella de la GT del partido
  completo (duda D1 de validation/PASOS.md). La comparación con ella es solo informativa: ningún
  parámetro ni la elección de dataset se deciden con ella (duda D21).

La **huella de retrasos** es el spellF1 de la secuencia contra sí misma retrasada `d` frames dentro
de cada tramo evaluado. No depende de ningún método: solo de cómo de cortas son las posesiones. Dos
fuentes con la misma huella tienen posesiones de la misma granularidad. La tabla oficial da, para
3 / 8 / 25 frames, 0,9818 / 0,8933 / 0,6539.

Regla nº 1
----------
Con la GT pública o con datos abiertos lo puede ejecutar cualquiera, Claude incluido. Con una entrega
nuestra (`evaluation/results/`) solo una persona, y se pega solo la salida.

Uso:
    python validation/scripts/perfil_etiquetas.py evaluation/gt/BAR-ATH_possession_gt_public.csv
    python validation/scripts/perfil_etiquetas.py <carpeta_datos_abiertos>/etiquetas.csv --fps 25

Los CSV de etiquetas derivadas se guardan en la carpeta de datos abiertos, fuera del repo.

Los tramos evaluados se deducen de dónde la secuencia no es X, igual que hace el scorer. Para
etiquetas propias con dos partes, separa las partes con al menos un frame X.

Desde otro script:
    from perfil_etiquetas import cargar, perfil, huella
"""

import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import possession_metrics as pm  # noqa: E402

# Huella publicada en EVALUATION.md: spellF1 de la GT del partido completo retrasada d frames.
HUELLA_OFICIAL = {1: 1.0, 3: 0.9818, 8: 0.8933, 25: 0.6539}
RETRASOS = (1, 3, 8, 25)
CORTES_S = (0.5, 1, 2, 3, 5)
NOMBRES = "HADX"


def cargar(ruta):
    """Códigos 0..3 (H, A, D, X) de un CSV frame,label con la columna frame contigua desde 0."""
    tabla = pm.read_label_csv(ruta)
    frames = tabla["frame"].values
    if not np.array_equal(frames, np.arange(len(frames))):
        raise ValueError("la columna frame no es 0..{} en orden".format(len(frames) - 1))
    return pm.label_codes(tabla)


def retrasar(codigos, d):
    """La misma secuencia con todas las etiquetas d frames tarde, dentro de cada tramo evaluado."""
    salida = codigos.copy()
    if d <= 0:
        return salida
    for inicio, fin in pm.valid_runs(codigos):
        tramo = codigos[inicio:fin]
        salida[inicio:fin] = np.concatenate((np.full(min(d, len(tramo)), tramo[0]), tramo[:-d]))
    return salida


def huella(codigos, retrasos=RETRASOS):
    """{d: spellF1 de la secuencia contra sí misma retrasada d frames}, con el scorer oficial."""
    return {d: pm.evaluate(codigos, retrasar(codigos, d))["spell_f1_mean"] for d in retrasos}


def perfil(codigos, fps=25):
    """Agregados de la secuencia: reparto de etiquetas, posesiones, paradas y transiciones."""
    tramos = pm.valid_runs(codigos)
    segmentos = pm.segments(codigos, tramos)
    posesiones = np.array([b - a for a, b, k in segmentos if k in (pm.H, pm.A)])
    paradas = np.array([b - a for a, b, k in segmentos if k == pm.D])
    evaluados = int(sum(b - a for a, b in tramos))
    vivos = int(np.sum((codigos == pm.H) | (codigos == pm.A)))
    transiciones = {}
    for _, de, a in pm.transitions(codigos, tramos):
        clave = NOMBRES[de] + ">" + NOMBRES[a]
        transiciones[clave] = transiciones.get(clave, 0) + 1
    return {
        "tramos": len(tramos),
        "frames_evaluados": evaluados,
        "reparto": {n: float(np.sum(codigos == k)) / evaluados if evaluados else 0.0
                    for k, n in ((pm.H, "H"), (pm.A, "A"), (pm.D, "D"))},
        "minutos_vivos": vivos / float(fps) / 60.0,
        "posesiones": posesiones,
        "paradas": paradas,
        "transiciones": transiciones,
    }


def _cuantiles_s(longitudes, fps):
    if not len(longitudes):
        return "sin datos"
    q = np.percentile(longitudes, [10, 25, 50, 75, 90]) / float(fps)
    return "p10 {:.1f} | p25 {:.1f} | mediana {:.1f} | p75 {:.1f} | p90 {:.1f} | media {:.1f}".format(
        q[0], q[1], q[2], q[3], q[4], np.mean(longitudes) / float(fps))


def imprimir(ruta, fps, con_huella=True):
    codigos = cargar(ruta)
    p = perfil(codigos, fps)
    posesiones, paradas = p["posesiones"], p["paradas"]
    print("fichero: {}".format(os.path.basename(ruta)))
    print("frames: {}  evaluados (no X): {}  tramos evaluados: {}".format(
        len(codigos), p["frames_evaluados"], p["tramos"]))
    print("reparto de frames evaluados: H {:.1%}  A {:.1%}  D {:.1%}".format(
        p["reparto"]["H"], p["reparto"]["A"], p["reparto"]["D"]))
    print("\nposesiones (rachas de H o de A): {}  |  {:.2f} por minuto de balón vivo".format(
        len(posesiones), len(posesiones) / p["minutos_vivos"] if p["minutos_vivos"] else 0.0))
    print("  duración (s): {}".format(_cuantiles_s(posesiones, fps)))
    if len(posesiones):
        print("  más cortas que: " + "  ".join(
            "{} s {:.0%}".format(c, float(np.mean(posesiones < c * fps))) for c in CORTES_S))
        print("  las tres más cortas (frames): {}".format(sorted(posesiones.tolist())[:3]))
    print("\nparadas (rachas de D): {}".format(len(paradas)))
    print("  duración (s): {}".format(_cuantiles_s(paradas, fps)))
    print("\ntransiciones por tipo: {}".format(
        "  ".join("{} {}".format(k, v) for k, v in sorted(p["transiciones"].items()))))
    if not con_huella:
        return
    print("\nhuella de retrasos (spellF1 de la secuencia contra sí misma retrasada d frames)")
    print("  {:>8}  {:>9}  {:>9}  {:>10}".format("retraso", "esta", "oficial", "diferencia"))
    for d, valor in huella(codigos).items():
        oficial = HUELLA_OFICIAL.get(d)
        print("  {:>8}  {:>9.4f}  {:>9.4f}  {:>+10.4f}".format(d, valor, oficial, valor - oficial))
    print("  (oficial = tabla de EVALUATION.md; solo informativa, no decide nada: dudas D1 y D21)")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # tildes bien también al redirigir a un fichero
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", help="fichero frame,label con etiquetas H/A/D/X")
    parser.add_argument("--fps", type=float, default=25.0, help="frames por segundo (25)")
    parser.add_argument("--sin-huella", action="store_true", help="no calcula la huella de retrasos")
    args = parser.parse_args()
    imprimir(args.csv, args.fps, con_huella=not args.sin_huella)
