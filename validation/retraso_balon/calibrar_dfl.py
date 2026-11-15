"""Calibración de la medida del retraso del balón en los 7 partidos abiertos de la DFL (bitácora §3).

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del experimento 0, con el
tracking del harness (`validation/harness/dfl.py`). Lo puede ejecutar cualquiera, Claude incluido. Solo
imprime agregados.

    python validation/retraso_balon/calibrar_dfl.py
    python validation/retraso_balon/calibrar_dfl.py --partidos J03WMX     # un solo partido

Cinco condiciones del balón (bitácora §3); las cuatro últimas deciden:

- `limpio`: el balón del harness sin suavizar (descriptiva: el desfase físico);
- `centrado`: «como el ATD» del harness, media centrada de 25 frames y huecos del ATD. Se espera 0 ± 2;
- `hacia atrás`: media de los 25 frames anteriores, con los mismos huecos. Se espera +12 ± 2;
- `centrado +6` y `centrado −6`: el de `centrado`, retrasado o adelantado 6 frames. Se espera ±6 ± 2.

Antes de medir comprueba, en cada partido, que la media centrada sobre el balón `limpio` con la máscara de
«como el ATD» reproduce el balón de «como el ATD» del harness, y que los jugadores son los mismos. Si no, da
error y no mide.
"""

import argparse
import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, AQUI)
sys.path.insert(0, ROOT)
import dfl  # noqa: E402  (añade experimento0, 1 y 2 al path)
import retraso as rt  # noqa: E402

SUAVIZADO = dfl.SUAVIZADO  # 25 frames, como en el harness
DESPLAZAMIENTO = 6
BANDA = 2
# condición: desfase esperado, o None si es descriptiva (bitácora §3)
ESPERADO = collections.OrderedDict([
    ("limpio", None),
    ("centrado", 0),
    ("hacia atrás", (SUAVIZADO - 1) // 2),
    ("centrado +6", DESPLAZAMIENTO),
    ("centrado −6", -DESPLAZAMIENTO),
])
MIN_PARTIDOS = 6  # de los 7, en la banda


def condiciones(cargado):
    """{condición: Tracking} de un partido, con los jugadores iguales en todas."""
    limpio = dfl.tracking_de(cargado, "limpio")
    atd = dfl.tracking_de(cargado, "como el ATD")
    if not (np.array_equal(limpio.px, atd.px, equal_nan=True) and np.array_equal(limpio.py, atd.py, equal_nan=True)):
        raise AssertionError("los jugadores de «limpio» y «como el ATD» no son los mismos: revisa el script")
    mascara = np.isnan(atd.bx) | np.isnan(atd.by)
    centrado = [dfl.media_movil(v, SUAVIZADO) for v in (limpio.bx, limpio.by)]
    reproducido = [np.where(mascara, np.nan, v) for v in centrado]
    if not all(np.allclose(r, h, rtol=0.0, atol=1e-9, equal_nan=True) for r, h in zip(reproducido, (atd.bx, atd.by))):
        raise AssertionError("la media centrada sobre «limpio» no reproduce «como el ATD»: revisa el script")

    def con_balon(bx, by):
        return limpio._replace(bx=np.where(mascara, np.nan, bx), by=np.where(mascara, np.nan, by))

    return collections.OrderedDict([
        ("limpio", limpio),
        ("centrado", atd),
        ("hacia atrás", con_balon(*(rt.media_atras(v, SUAVIZADO) for v in (limpio.bx, limpio.by)))),
        ("centrado +6", con_balon(*(rt.desplazar(v, DESPLAZAMIENTO) for v in centrado))),
        ("centrado −6", con_balon(*(rt.desplazar(v, -DESPLAZAMIENTO) for v in centrado))),
    ])


def en_banda(valor, esperado):
    return valor is not None and abs(valor - esperado) <= BANDA


def fila(nombre, res, esperado):
    p5, p95 = res["intervalo"]
    marca = "" if esperado is None else ("  ok" if en_banda(res["desfase"], esperado) else "  FUERA")
    partes = "/".join("—" if d is None else "{:+d}".format(d) for d in res["desfase_por_tramo"])
    return "   {:<9} L̂ {:>4}  [{:>5}, {:>5}]  r {:>6}  partes {:<8} módulo {:>4}  rachas {:>5}{}".format(
        nombre, "—" if res["desfase"] is None else "{:+d}".format(res["desfase"]),
        "—" if p5 is None else "{:+.1f}".format(p5), "—" if p95 is None else "{:+.1f}".format(p95),
        "—" if res["correlacion_pico"] is None else "{:.3f}".format(res["correlacion_pico"]), partes,
        "—" if res["desfase_modulo"] is None else "{:+d}".format(res["desfase_modulo"]), res["rachas"], marca)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--partidos", nargs="*", default=None, help="por defecto, los 7")
    args = ap.parse_args(argv)
    partidos = args.partidos or list(dfl.PARTIDOS)
    inicio = time.time()
    sumas = collections.OrderedDict((c, collections.OrderedDict()) for c in ESPERADO)
    for partido in partidos:
        for c, trk in condiciones(dfl.cargar(partido)).items():
            sumas[c][partido] = rt.sumas(trk)
        print("  leído {} ({:.0f} s)".format(partido, time.time() - inicio), flush=True)

    print("\nRetraso del balón: calibración en la DFL (bitácora §3). L̂ > 0: el balón llega tarde.")
    print("Por condición: cada partido y los {} juntos. [p5, p95] es el bootstrap por rachas.".format(len(partidos)))
    pasa = True
    for c, esperado in ESPERADO.items():
        print("\n{}  (se espera {})".format(c, "— descriptiva" if esperado is None else "{:+d} ± {}".format(
            esperado, BANDA)))
        dentro = 0
        for partido, s in sumas[c].items():
            res = rt.resumen([s])
            dentro += int(esperado is not None and en_banda(res["desfase"], esperado))
            print(fila(partido, res, esperado))
        junto = rt.resumen(list(sumas[c].values()))
        print(fila("juntos", junto, esperado))
        if esperado is not None:
            necesarios = min(MIN_PARTIDOS, len(partidos))
            ok = dentro >= necesarios and en_banda(junto["desfase"], esperado)
            pasa &= ok
            print("   → {} de {} partidos en la banda (hacen falta {}) y juntos {}: {}".format(
                dentro, len(partidos), necesarios, "dentro" if en_banda(junto["desfase"], esperado) else "fuera",
                "pasa" if ok else "NO PASA"))
    print("\nCalibración: {}".format(
        "PASA, la medida se puede ejecutar en el partido" if pasa else "NO PASA, no se ejecuta en el partido"))
    if len(partidos) < len(dfl.PARTIDOS):
        print("(con {} de {} partidos: no es la calibración de la bitácora)".format(len(partidos), len(dfl.PARTIDOS)))
    print("tiempo {:.0f} s".format(time.time() - inicio))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
