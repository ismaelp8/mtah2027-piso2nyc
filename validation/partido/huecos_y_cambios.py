"""¿Caen los huecos del balón del ATD en los cambios de posesión más que al azar? Agregados del partido.

**Lee el partido (el ATD) y una entrega nuestra: lo ejecuta una persona, en local.** Claude no lo ejecuta.

    python validation/partido/huecos_y_cambios.py equipo_v3
    python validation/partido/huecos_y_cambios.py <ruta.csv> --data-dir <carpeta>

- `entrega`: el nombre de una entrega en `evaluation/results/` (sin `.csv`) o la ruta a un CSV `frame,label`.
- Tarda unos minutos: además del partido, calcula la misma medida en los 7 partidos de la DFL (datos abiertos),
  que es la referencia. Con `--sin-dfl` se la salta.

Sale de la hipótesis H3 del visionado de la ventana pública (y de la H5): en el partido, el balón puede
desaparecer justo en los cambios (el portero lo coge, un despeje por el aire), y en el harness los huecos caen al
azar. Se mide sin etiquetas: dónde caen **nuestros** cambios de equipo respecto a los huecos del balón en el juego
(definiciones en `validation/posesiones_cortas/huecos.py`). La regla de lectura está en
`validation/posesiones_cortas/BITACORA.md` §14, con commit antes de que se ejecute esto.

**Imprime solo agregados del partido entero:** recuentos y porcentajes por duración del hueco, sin partes, frames
ni momentos. Una celda de 1 a 4 casos sale como «< 5», y su porcentaje como «–». Si falla, imprime solo el tipo de
error y las líneas del código. No escribe ficheros.
"""

import argparse
import os
import sys
import traceback
import warnings

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for _carpeta in (ROOT, os.path.join(ROOT, "validation", "posesiones_cortas"), os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, _carpeta)
import games  # noqa: E402
import huecos  # noqa: E402
import possession_metrics as pm  # noqa: E402
from possession import aprendida, ball, tracking  # noqa: E402

FICHEROS = ["atd_meta", "atd_raw"]
RESULTADOS = os.path.join(ROOT, "evaluation", "results")
CIERRA, ABRE = 1.25, 1.5  # cocientes de R del partido entre R de la DFL (regla de BITACORA.md §14)
MINIMO_CAMBIOS = 20


def medir_partido(ruta, data_dir):
    games.require(FICHEROS, games.GAME, data_dir)
    trk = tracking.from_atd(games.asset_paths(games.GAME, data_dir), games.GAME)
    codes = pm.label_codes(pm.read_label_csv(ruta))
    if len(codes) != len(trk.bx):
        raise ValueError("la entrega y el ATD no tienen el mismo número de frames")
    return huecos.medir(codes, aprendida.balon_visible(ball.clean(trk)), tracking.evaluated_blocks(games.GAME))


def veredicto(acc_partido, acc_dfl):
    """La regla de BITACORA.md §14 con los dos cocientes: R (cambios junto a huecos) y F (huecos con cambio)."""
    rp, rd = huecos.razon(acc_partido), huecos.razon(acc_dfl)
    (fp, np_), (fd, _) = huecos.fraccion_con_cambio(acc_partido), huecos.fraccion_con_cambio(acc_dfl)
    casos = acc_partido["cambios dentro de un hueco"] + acc_partido["cambios al reaparecer"]
    lineas = ["## Regla de BITACORA.md §14", ""]
    cocientes = []
    def coma(x, cifras):
        return "{:.{}f}".format(x, cifras).replace(".", ",")
    if rp is not None and rd is not None and rp[2] is not None and rd[2]:
        cocientes.append(rp[2] / rd[2])
        lineas.append("R del partido = {}; R de la DFL = {}; cociente = {}.".format(
            coma(rp[2], 2), coma(rd[2], 2), coma(rp[2] / rd[2], 2)))
    if fp is not None and fd:
        cocientes.append(fp / fd)
        if huecos.oculta_f(acc_partido):  # el cociente se usa, pero F del partido dejaría ver una celda pequeña
            lineas.append("F del partido: menos de 5 casos, no se imprime; F de la DFL = {} %; el cociente {} 1,25.".format(
                coma(fd, 1), "no pasa de" if fp / fd <= CIERRA else "pasa de"))
        else:
            lineas.append("F del partido = {} %; F de la DFL = {} %; cociente = {}.".format(
                coma(fp, 1), coma(fd, 1), coma(fp / fd, 2)))
    if len(cocientes) < 2:
        return lineas + ["**No concluye:** falta R o F (no hay cambios o no hay huecos)."]
    if casos < MINIMO_CAMBIOS or np_ < MINIMO_CAMBIOS:
        lineas.append("**No concluye:** menos de {} casos (cambios junto a un hueco, o huecos de 0,5 a 15 s).".format(
            MINIMO_CAMBIOS))
    elif max(cocientes) >= ABRE:
        lineas.append("**Queda abierta:** en el partido los huecos del balón se juntan con los cambios bastante más que "
                      "en la DFL. Hace falta pensar una degradación calibrada con este agregado.")
    elif max(cocientes) <= CIERRA:
        lineas.append("**Se cierra:** en el partido los huecos no caen en los cambios más que en la DFL, donde caen al "
                      "azar.")
    else:
        lineas.append("**No concluye:** algún cociente entre {:g} y {:g}. No se abre nada antes de la entrega.".format(
            CIERRA, ABRE).replace(".", ","))
    return lineas


def informe_de_error(error):
    """Tipo de error y líneas del código, sin el mensaje: podría llevar valores de datos."""
    pila = traceback.extract_tb(error.__traceback__)
    lineas = ["{}:{} ({})".format(os.path.basename(f.filename), f.lineno, f.name) for f in pila]
    return "ERROR {} en {}".format(type(error).__name__, " <- ".join(reversed(lineas)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("entrega", help="nombre de la entrega en evaluation/results (sin .csv) o ruta a un CSV")
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    ap.add_argument("--sin-dfl", action="store_true", help="no calcula la referencia de la DFL")
    args = ap.parse_args(argv)
    ruta = args.entrega if os.path.isfile(args.entrega) else os.path.join(RESULTADOS, args.entrega + ".csv")
    if not os.path.isfile(ruta):
        print("No encuentro la entrega: pasa su nombre en evaluation/results (sin .csv) o la ruta a un CSV.")
        return 1
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD del partido: revisa que MTAH_DATA_DIR apunte a la carpeta de los datos.")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        acc_partido = medir_partido(ruta, args.data_dir)
    print("# Nuestros cambios de equipo y los huecos del balón (H3; regla en validation/posesiones_cortas/BITACORA.md §14)\n")
    print("Entrega: {}".format(os.path.basename(ruta)))
    print()
    print("\n".join(huecos.lineas("Partido (ATD y la entrega)", acc_partido, suprimir=True)))
    if args.sin_dfl:
        return 0
    import huecos_dfl
    acc_dfl = huecos_dfl.referencia_dfl()
    print()
    print("\n".join(huecos.lineas("Referencia: DFL, 7 partidos, «como el ATD», `main` con nuestro `D` (huecos al azar)",
                                  acc_dfl, suprimir=False)))
    print()
    print("\n".join(veredicto(acc_partido, acc_dfl)))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
