"""Calibración de la versión 2 de la medida del retraso del balón en la DFL (bitácora §8.3).

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), con el tracking del harness. Lo puede
ejecutar cualquiera, Claude incluido. Solo imprime agregados.

    python validation/retraso_balon/calibrar_dfl_v2.py

- **La familia:** en cada partido, el balón `centrado` de la versión 1 (media centrada de 25 y huecos «como
  el ATD») retrasado `d` frames, de −18 a +18 (`retraso.FAMILIA`).
- **Las pruebas,** dejando cada partido fuera (su familia es la de los otros 6): el balón `centrado`
  retrasado −9, −6, −3, 0, +3, +6 y +9 frames, y `hacia atrás` (media de los 25 anteriores), que debe dar
  +12. Pasa si en cada prueba el `d̂` cae a ±2 en 6 de los 7 partidos o más.
- **Descriptivo:** una media exponencial hacia atrás de retraso medio 8 frames, que no está en la familia.
- **El residuo de referencia** es el mayor de las 8 pruebas en los 7 partidos.

`familia_y_referencia()` es lo que usa el script del partido (`validation/partido/retraso_balon.py`): la
familia de los 7 partidos juntos y el residuo de referencia.
"""

import argparse
import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import calibrar_dfl as v1  # noqa: E402  (añade el harness y la raíz al path)
import retraso as rt  # noqa: E402

dfl = v1.dfl
BANDA = 2
MIN_PARTIDOS = 6
# prueba: retraso de verdad (bitácora §8.3)
PRUEBAS = collections.OrderedDict([("−9", -9), ("−6", -6), ("−3", -3), ("0", 0), ("+3", 3), ("+6", 6), ("+9", 9),
                                   ("hacia atrás", (v1.SUAVIZADO - 1) // 2)])
EXPONENCIAL = "exponencial"
ALFA = 1.0 / 9.0  # retraso medio (1 − α) / α = 8 frames
RETRASO_EXPONENCIAL = 8


def sumas_partido(cargado):
    """({d: sumas} de la familia, {"hacia atrás": sumas, EXPONENCIAL: sumas}) de un partido."""
    cond = v1.condiciones(cargado)  # con sus comprobaciones: los jugadores y la media centrada del harness
    limpio, atd = cond["limpio"], cond["centrado"]
    mascara = np.isnan(atd.bx) | np.isnan(atd.by)
    centrado = [dfl.media_movil(v, v1.SUAVIZADO) for v in (limpio.bx, limpio.by)]

    def con_balon(bx, by):
        return limpio._replace(bx=np.where(mascara, np.nan, bx), by=np.where(mascara, np.nan, by))

    familia = collections.OrderedDict(
        (int(d), rt.sumas(con_balon(*(rt.desplazar(v, int(d)) for v in centrado)))) for d in rt.FAMILIA)
    extra = {"hacia atrás": rt.sumas(cond["hacia atrás"]),
             EXPONENCIAL: rt.sumas(con_balon(*(rt.media_exponencial(v, ALFA) for v in (limpio.bx, limpio.by))))}
    return familia, extra


def cargar_todo(partidos, eco=None):
    sumas = collections.OrderedDict()
    inicio = time.time()
    for partido in partidos:
        sumas[partido] = sumas_partido(dfl.cargar(partido))
        if eco:
            eco("  leído {} ({:.0f} s)".format(partido, time.time() - inicio))
    return sumas


def familia_de(sumas, partidos):
    """{d: curva} con las rachas de `partidos` juntas."""
    return {int(d): rt.curva_de([sumas[p][0][int(d)] for p in partidos]) for d in rt.FAMILIA}


def pruebas(sumas):
    """({prueba: {partido: resumen_v2}}, residuo de referencia), con cada partido medido con la familia de los
    demás."""
    salida = collections.OrderedDict((nombre, collections.OrderedDict()) for nombre in list(PRUEBAS) + [EXPONENCIAL])
    for partido in sumas:
        familia = familia_de(sumas, [q for q in sumas if q != partido])
        for nombre, d in PRUEBAS.items():
            prueba = sumas[partido][1]["hacia atrás"] if nombre == "hacia atrás" else sumas[partido][0][d]
            salida[nombre][partido] = rt.resumen_v2([prueba], familia)
        salida[EXPONENCIAL][partido] = rt.resumen_v2([sumas[partido][1][EXPONENCIAL]], familia)
    residuos = [res["residuo"] for nombre in PRUEBAS for res in salida[nombre].values() if res["residuo"] is not None]
    return salida, (max(residuos) if residuos else None)


def familia_y_referencia(eco=None):
    """(familia de los 7 partidos juntos, residuo de referencia, partidos): lo que usa el script del partido."""
    sumas = cargar_todo(list(dfl.PARTIDOS), eco)
    _, referencia = pruebas(sumas)
    return familia_de(sumas, list(sumas)), referencia, len(sumas)


def en_banda(valor, esperado):
    return valor is not None and abs(valor - esperado) <= BANDA


def fila(partido, res, esperado, decide=True):
    p5, p95 = res["intervalo"]
    marca = ("  ok" if en_banda(res["desfase"], esperado) else "  FUERA") if decide else ""
    partes = "/".join("—" if d is None else "{:+d}".format(d) for d in res["desfase_por_tramo"])
    return "   {:<7} d̂ {:>4}  [{:>5}, {:>5}]  residuo {:>6}  partes {:<8} L̂ v1 {:>4}  rachas {:>4}{}".format(
        partido, "—" if res["desfase"] is None else "{:+d}".format(res["desfase"]),
        "—" if p5 is None else "{:+.1f}".format(p5), "—" if p95 is None else "{:+.1f}".format(p95),
        "—" if res["residuo"] is None else "{:.3f}".format(res["residuo"]), partes,
        "—" if res["desfase_maximo"] is None else "{:+d}".format(res["desfase_maximo"]), res["rachas"], marca)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.parse_args(argv)
    inicio = time.time()
    sumas = cargar_todo(list(dfl.PARTIDOS), eco=lambda texto: print(texto, flush=True))
    salida, referencia = pruebas(sumas)
    print("\nRetraso del balón, versión 2: calibración en la DFL (bitácora §8.3). d̂ > 0: el balón llega tarde.")
    print("Cada partido, con la familia de los otros {}. [p5, p95] es el bootstrap por rachas.".format(len(sumas) - 1))
    pasa = True
    for nombre, esperado in PRUEBAS.items():
        print("\n{}  (se espera {:+d} ± {})".format(nombre if nombre == "hacia atrás" else "centrado " + nombre,
                                                   esperado, BANDA))
        dentro = 0
        for partido, res in salida[nombre].items():
            dentro += int(en_banda(res["desfase"], esperado))
            print(fila(partido, res, esperado))
        ok = dentro >= MIN_PARTIDOS
        pasa &= ok
        print("   → {} de {} partidos en la banda (hacen falta {}): {}".format(
            dentro, len(sumas), MIN_PARTIDOS, "pasa" if ok else "NO PASA"))
    print("\n{} hacia atrás, α = 1/9 (descriptiva: retraso medio {:+d}; no está en la familia)".format(
        EXPONENCIAL, RETRASO_EXPONENCIAL))
    for partido, res in salida[EXPONENCIAL].items():
        print(fila(partido, res, RETRASO_EXPONENCIAL, decide=False))
    print("\nResiduo de referencia (el mayor de las 8 pruebas): {}".format(
        "—" if referencia is None else "{:.3f}".format(referencia)))
    print("\nCalibración v2: {}".format(
        "PASA, la medida se puede ejecutar en el partido" if pasa else "NO PASA, no se ejecuta en el partido"))
    print("tiempo {:.0f} s".format(time.time() - inicio))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
