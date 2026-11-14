"""Experimento 2: calibración del instrumento en la DFL (Bassek et al., 2025; datos abiertos de otros partidos).

Mide, con el mismo código que se ejecutará en la ventana pública del partido
(`validation/partido/recuento_ventana.py`), qué huella deja cada convención:

- **flag tal cual** (lectura 1: cambia en el primer toque del rival);
- **corregida "C0-12 o dos toques"** (lectura 3: el rival tiene que controlar; el cambio se queda fechado
  en su toque, como en `validation/experimento1/correccion.py`).

Las etiquetas se calculan siempre con el tracking limpio; el instrumento mide sobre tracking degradado
para parecerse al ATD (criterios en `BITACORA.md`, fijados antes de medir):

- limpia;
- el 41 % de los frames vivos sin balón. Se tapa una fracción (0, 25, 50, 75 o 100 %) de los episodios de
  disputa (los dos equipos a 3 m o menos) y de balón alto (más de 1,5 m), ±5 frames, y se completa con
  bloques al azar de 1 s de media. La fracción 0 son bloques al azar y la 100 %, la "dirigida";
- cada una con ruido gaussiano de 0, 10 o 25 cm en el balón (la mitad en los jugadores).

Solo imprime agregados. Semilla fija.

Uso:
    python validation/experimento2/calibrar_dfl.py [--partidos J03WMX ...] [--tabla]
"""

import argparse
import collections
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento1"))
sys.path.insert(0, AQUI)
import correccion as cr  # noqa: E402
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
import instrumento as ins  # noqa: E402
from peso_correccion import controles_parte  # noqa: E402

SEMILLA = 20261114
OBJETIVO = 0.41
MEDIA_BLOQUE = 25
FRACCIONES = (0.0, 0.25, 0.5, 0.75, 1.0)
RUIDOS = (0.0, 0.10, 0.25)
CONDICIONES = [("limpia", None, 0.0)] + [
    ("41 %, disputas tapadas {:.0f} %, ruido {:.0f} cm".format(100 * f, 100 * s), f, s)
    for f in FRACCIONES for s in RUIDOS]
VARIANTES = {
    "base": ins.PRM,
    "ampliada": dict(ins.PRM, radio=1.5, radio_toque=2.0),
}
ETIQUETAS = ("flag (lectura 1)", "corregida (lectura 3)")
DIFERENCIA_MINIMA = 0.40


def distingue(d1, d3, clave):
    """La sección 3 de la bitácora: r1 − r3 ≥ 0,40 con todos juntos y rangos por partido sin solapar."""
    r1, r3 = d1["tasas"][clave], d3["tasas"][clave]
    m1, m3 = d1["min_max_por_partido"][clave], d3["min_max_por_partido"][clave]
    if r1 is None or r3 is None or m1 is None or m3 is None:
        return False
    return bool(r1 - r3 >= DIFERENCIA_MINIMA and m1[0] > m3[1])


def calibrar(partidos):
    resultados = collections.defaultdict(list)
    por_partido = collections.defaultdict(list)
    for ip, p in enumerate(partidos):
        datos = dfl_lector.cargar_cache(p)
        for k in (1, 2):
            parte = datos["partes"][k]
            estado, poss = np.asarray(parte["estado"]), np.asarray(parte["poss"])
            activo = estado == 1
            lab = np.where(activo, poss - 1, 2).astype(int)
            corr = cr.corregir(lab, controles_parte(parte)["C0-12 o dos toques"])
            etiquetas = {ETIQUETAS[0]: poss, ETIQUETAS[1]: np.where(activo, corr + 1, poss)}
            prep_limpio = ins.preparar_en_juego(parte, estado)
            z = np.asarray(parte["z"], float)
            for ic, (cond, fraccion, sigma) in enumerate(CONDICIONES):
                rng = np.random.default_rng([SEMILLA, ip, k, ic])
                if fraccion is None:
                    prep = prep_limpio
                else:
                    masc, _ = ins.mascara_dirigida(prep_limpio, z, activo, OBJETIVO, rng, fraccion=fraccion,
                                                   media=MEDIA_BLOQUE)
                    prep = ins.preparar_en_juego(ins.degradar(parte, masc, sigma, rng), estado)
                for var, prm in VARIANTES.items():
                    for et, ps in etiquetas.items():
                        r = ins.medir(prep, estado, ps, prm)
                        resultados[(cond, var, et)].append(r)
                        por_partido[(cond, var, et, p)].append(r)
        print("hecho", p, file=sys.stderr)

    salida = {"partidos": len(partidos), "condiciones": {}}
    for cond, _, _ in CONDICIONES:
        for var in VARIANTES:
            d = salida["condiciones"].setdefault(cond, {}).setdefault(var, {})
            for et in ETIQUETAS:
                rangos = {"huecos_rival_que_cambian": [], "sueltos_rival_que_cambian": []}
                for p in partidos:
                    t = ins.tasas(ins.sumar(por_partido[(cond, var, et, p)]))
                    for c in rangos:
                        if t[c] is not None:
                            rangos[c].append(t[c])
                d[et] = {"tasas": ins.tasas(ins.sumar(resultados[(cond, var, et)])),
                         "min_max_por_partido": {c: [min(v), max(v)] if v else None for c, v in rangos.items()},
                         "recuentos": ins.sumar(resultados[(cond, var, et)])}
            d["distingue"] = {c: distingue(d[ETIQUETAS[0]], d[ETIQUETAS[1]], c)
                              for c in ("huecos_rival_que_cambian", "sueltos_rival_que_cambian")}
    return salida


def tabla(salida, var="base"):
    """La tabla de la bitácora (sección 6)."""
    def f(v):
        return "–" if v is None else "{:.2f}".format(v).replace(".", ",")

    def rango(m):
        return "" if m is None else " [{}–{}]".format(f(m[0]), f(m[1]))

    filas = ["| condición | balón visible | disputas entre los visibles | temblor (cm) | toques/min | controles/min "
             "| sueltos del rival/min | `r1` | `r3` | ¿distingue? | en el toque (flag) | cambios con toque visible |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for cond, d in salida["condiciones"].items():
        d1, d3 = d[var][ETIQUETAS[0]], d[var][ETIQUETAS[1]]
        t1, t3 = d1["tasas"], d3["tasas"]
        c = "sueltos_rival_que_cambian"
        filas.append("| {} | {} % | {} % | {} | {} | {} | {} | {}{} | {}{} | {} | {} | {} |".format(
            cond, t1["balon_visible_en_juego_pct"], t1["disputa_entre_frames_con_balon_pct"],
            t1["temblor_balon_mediana_cm"], t1["toques_con_equipo_por_minuto_vivo"],
            t1["controles_ret12_por_minuto_vivo"], t1["sueltos_rival_por_minuto_vivo"],
            f(t1[c]), rango(d1["min_max_por_partido"][c]), f(t3[c]), rango(d3["min_max_por_partido"][c]),
            "sí" if d[var]["distingue"][c] else "no", f(t1["en_el_toque_de_los_que_tienen_toque"]),
            f(t1["cambios_con_toque_visible"])))
    return "\n".join(filas)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--partidos", nargs="+", default=list(etiquetas_dfl.PARTIDOS))
    ap.add_argument("--tabla", action="store_true", help="imprime las tablas en markdown en vez del JSON")
    args = ap.parse_args()
    salida = calibrar(args.partidos)
    if args.tabla:
        for var in VARIANTES:
            print("variante", var)
            print(tabla(salida, var))
            print()
    else:
        print(json.dumps(salida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
