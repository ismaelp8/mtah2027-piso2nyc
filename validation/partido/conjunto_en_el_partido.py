"""Lo que ve y lo que dice el modelo conjunto en el partido, frente a los datos abiertos con los que se entrenó.

**Lee datos del partido (el ATD): lo ejecuta una persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/conjunto_en_el_partido.py

Es parte del punto 4 de la regla del candidato K2 (docs/decisiones.md, 17/11, «modelo conjunto»). El modelo se
entrenó con la DFL y con SkillCorner, y el harness no puede decir si el ATD se les parece. Este script calcula en el
ATD los mismos agregados que `validation/conjunto/referencia.py` calculó en las 48 vistas de los 17 partidos abiertos
(`validation/conjunto/referencia_abiertos.json`, fijada antes; 14 de ellas, con el balón a la vista en las paradas,
como en el ATD) y dice cuáles caen fuera de su rango.

- Imprime solo agregados del partido entero: medianas, percentiles, medias y porcentajes sobre decenas de miles de
  grupos de 5 frames. Nada por frame: la salida se puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.

La regla de lectura está en `docs/decisiones.md` y la aplica `comparar`, una función pura que
`validation/scripts/prueba_conjunto_en_el_partido.py` prueba con números inventados:

- el rango de cada agregado se ensancha un cuarto de su anchura por cada lado (`MARGEN`);
- **las salidas deciden:** si alguna de las seis cae fuera, el modelo no se comporta en el ATD como en los datos
  abiertos y K2 no se enciende sin mirarlo antes;
- **las entradas se enseñan:** las que caen fuera dicen en qué no se parece el ATD.
"""

import argparse
import json
import os
import sys
import time
import traceback
import warnings

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "conjunto"))
import games  # noqa: E402
from possession import pipeline, tracking  # noqa: E402

FICHEROS = ["atd_raw", "atd_meta"]
REFERENCIA = os.path.join(ROOT, "validation", "conjunto", "referencia_abiertos.json")
MARGEN = 0.25  # el rango de los abiertos se ensancha esta fracción de su anchura por cada lado


def es_salida(nombre):
    return nombre.startswith("salida ·")


def comparar(valores, referencia, margen=MARGEN):
    """Las filas de la comparación y el veredicto.

    `valores`: {agregado: número} del partido. `referencia`: el JSON de `referencia.py`. Devuelve
    `(filas, salidas_fuera, entradas_fuera)`; cada fila es (nombre, valor, mínimo, máximo, ¿fuera?). Un agregado que
    no es un número (un subconjunto vacío) cuenta como fuera.
    """
    filas, salidas_fuera, entradas_fuera = [], [], []
    for nombre, (minimo, maximo) in sorted(referencia["rango"].items()):
        if nombre not in valores:
            raise KeyError("falta el agregado «{}»".format(nombre))
        valor = valores[nombre]
        ancho = maximo - minimo
        fuera = not (minimo - margen * ancho <= valor <= maximo + margen * ancho)  # un NaN cuenta como fuera
        filas.append((nombre, valor, minimo, maximo, fuera))
        if fuera:
            (salidas_fuera if es_salida(nombre) else entradas_fuera).append(nombre)
    return filas, salidas_fuera, entradas_fuera


def para_imprimir(filas, salidas_fuera, entradas_fuera, referencia):
    lineas = ["# El modelo conjunto en el partido, frente a los datos abiertos",
              "",
              "Referencia: {} vistas de los partidos abiertos, commit {}. Rango ensanchado un {:.0f} % por cada "
              "lado.".format(referencia["vistas"], referencia["commit"], 100 * MARGEN),
              "",
              "| agregado | partido | abiertos: mínimo–máximo | ¿fuera? |",
              "|---|---|---|---|"]
    for nombre, valor, minimo, maximo, fuera in sorted(filas, key=lambda f: (not es_salida(f[0]), f[0])):
        lineas.append("| {} | {:.3f} | {:.3f} – {:.3f} | {} |".format(nombre, valor, minimo, maximo,
                                                                    "FUERA" if fuera else ""))
    lineas += ["",
               "Salidas fuera del rango: {} de {}{}.".format(
                   len(salidas_fuera), sum(es_salida(f[0]) for f in filas),
                   " ({})".format("; ".join(salidas_fuera)) if salidas_fuera else ""),
               "Entradas fuera del rango: {} de {}{}.".format(
                   len(entradas_fuera), sum(not es_salida(f[0]) for f in filas),
                   " ({})".format("; ".join(entradas_fuera)) if entradas_fuera else ""),
               "",
               "Regla: " + ("LAS SALIDAS SE SALEN del rango de los datos abiertos: K2 no se enciende sin mirarlo antes."
                            if salidas_fuera else
                            "las salidas caen dentro del rango de los datos abiertos: por este lado, K2 puede seguir.")]
    return lineas


def medir(data_dir=None):
    """Los agregados del modelo sobre el ATD del partido. Lee datos del partido: solo lo ejecuta una persona."""
    import agregados  # validation/conjunto/agregados.py
    game = games.GAME
    games.require(FICHEROS, game, data_dir)
    trk = pipeline.default_piece("ball")(tracking.from_atd(games.asset_paths(game, data_dir), game))
    return agregados.agregados(trk, fuera=None)


def informe_de_error(error):
    """Una línea con el tipo de error y dónde, sin el mensaje: el mensaje podría llevar valores de datos."""
    pila = traceback.extract_tb(error.__traceback__)
    donde = ", ".join("{}:{}".format(os.path.basename(p.filename), p.lineno) for p in pila[-4:])
    return "ERROR {} en {}. Sin valores de datos: se puede pegar tal cual.".format(type(error).__name__, donde)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    inicio = time.time()
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD del partido: revisa que MTAH_DATA_DIR (o --data-dir) apunte a la carpeta de los "
              "datos.")
        return 1
    if not os.path.isfile(REFERENCIA):
        print("No encuentro validation/conjunto/referencia_abiertos.json: haz git pull.")
        return 1
    with open(REFERENCIA, encoding="utf-8") as f:
        referencia = json.load(f)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        valores = medir(args.data_dir)
    print("\n".join(para_imprimir(*comparar(valores, referencia), referencia)))
    print("\n   tiempo {:.0f} s".format(time.time() - inicio))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
