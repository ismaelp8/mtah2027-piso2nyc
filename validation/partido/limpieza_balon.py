"""Qué hace la limpieza del balón (`possession.ball.clean_v1`) con el ATD del partido. Solo agregados.

**Lee datos del partido: lo ejecuta una persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/limpieza_balon.py

Cuenta, en los frames evaluados y con las dos partes juntas, qué hace cada paso de `clean_v1`:

- cuántos puntos quita el paso 1 (saltos imposibles) y cómo son los pares de frames seguidos a más de
  40 m/s del perfil del ATD: picos de ida y vuelta, excursiones de hasta 1 s o saltos que se quedan;
- cuántos puntos quita el paso 2 (rachas aisladas);
- cuántos frames rellena el paso 3 (huecos cortos);
- cuántos frames cambian en total, y cuántos saltos imposibles quedan.

Cómo se lee está fijado antes de ejecutarlo, en `docs/decisiones.md` (entrada del 14/11 «balón · corrección
del paso 2 de la limpieza y recuento en el partido»). Después de ver los números no se retoca ningún umbral.

- El recuento usa las mismas funciones de `possession/ball.py` y comprueba que reproduce `clean_v1`
  exactamente: si no, da error en vez de contar otra cosa.
- Imprime solo recuentos y porcentajes del partido entero. Una celda de 1 a 4 casos sale como "< 5", como
  en el perfil del ATD. Nada por parte, por minuto ni por frame: la salida se puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero. Tarda unos segundos (4 s el 15/11), casi todo leyendo el ATD.

`recuento(trk)` es una función pura sobre un `Tracking`: la prueba (`validation/scripts/prueba_limpieza.py`)
la ejecuta con un tracking inventado de resultado conocido.
"""

import argparse
import os
import sys
import time
import traceback
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from possession import ball, candidates, tracking  # noqa: E402

FICHEROS = ["atd_raw", "atd_meta"]
MINIMO_CELDA = 5
# Una excursión: un salto que se va y otro que vuelve como mucho 1 s después (25 frames), con el balón de
# vuelta donde se le espera desde antes del primero (MAX_SPEED o menos). Fijado antes de ejecutar.
EXCURSION_MAX = 25
# Lo que se espera ver, fijado antes de ejecutar (docs/decisiones.md): los controles del perfil del ATD.
PERFIL_EVALUADOS, PERFIL_CON_BALON, PERFIL_PARES = 158857, 94214, 216


def ids_de_tramo(trk):
    """Por frame, el índice del tramo evaluado al que pertenece, o -1 fuera de los tramos."""
    bid = np.full(len(trk.bx), -1, dtype=np.int64)
    for k, (a, b) in enumerate(trk.blocks):
        bid[a:b] = k
    return bid


def pares_imposibles(bx, by, fps, bid):
    """Máscara (n − 1,) de los pares de frames seguidos, los dos con balón y en el mismo tramo evaluado, con
    el balón a más de MAX_SPEED. Es el agregado 6 del perfil del ATD."""
    visible = np.isfinite(bx) & np.isfinite(by)
    par = visible[:-1] & visible[1:] & (bid[:-1] == bid[1:]) & (bid[:-1] >= 0)
    with np.errstate(invalid="ignore"):
        return par & (np.hypot(np.diff(bx), np.diff(by)) * fps > ball.MAX_SPEED)


def saltos(bx, by, fps, bid):
    """Saltos imposibles entre dos puntos con balón seguidos (con un hueco en medio o sin él), dentro de un
    tramo evaluado. Sirve antes y después de limpiar: un salto que se queda sigue contando aunque la
    limpieza abra un hueco a su lado."""
    vistos = np.flatnonzero(np.isfinite(bx) & np.isfinite(by) & (bid >= 0))
    if len(vistos) < 2:
        return 0
    mismo = bid[vistos[1:]] == bid[vistos[:-1]]
    vel = np.hypot(np.diff(bx[vistos]), np.diff(by[vistos])) * fps / np.diff(vistos)
    return int(np.sum(mismo & (vel > ball.MAX_SPEED)))


def clasificar(imposible, bx, by, fps, bid):
    """Recuentos de pares y de tramos de pares imposibles seguidos, por clase.

    Un tramo son pares imposibles seguidos: van del frame p (antes del primero) al q (después del último).
    - pico: dos pares o más, y de p a q el balón va a MAX_SPEED o menos. El paso 1 quita todo su interior;
    - excursión: un tramo que no es pico y otro que empieza como mucho EXCURSION_MAX frames después, en el
      mismo tramo evaluado, con el balón de vuelta donde se le espera (de p del primero a q del segundo, a
      MAX_SPEED o menos);
    - salto que se queda: el resto.
    En las excursiones y en los saltos que se quedan, el paso 1 quita el interior de cada tramo de dos pares
    o más (el tránsito), pero el salto queda.
    """
    inicios, fines = ball.runs(imposible)
    def vel(p, q):
        return np.hypot(bx[q] - bx[p], by[q] - by[p]) * fps / (q - p)

    clase = []
    for p, q in zip(inicios, fines):
        clase.append("pico" if q - p >= 2 and vel(p, q) <= ball.MAX_SPEED else None)
    i = 0
    while i < len(clase):
        if clase[i] is None:
            j = i + 1
            if (j < len(clase) and clase[j] is None and inicios[j] - fines[i] <= EXCURSION_MAX
                    and bid[inicios[j]] == bid[fines[i]] and vel(inicios[i], fines[j]) <= ball.MAX_SPEED):
                clase[i] = clase[j] = "excursión"
                i = j + 1
                continue
            clase[i] = "salto que se queda"
        i += 1
    salida = {}
    for nombre in ("pico", "excursión", "salto que se queda"):
        sel = np.array([c == nombre for c in clase], dtype=bool)
        salida[nombre] = {"pares": int(np.sum((fines - inicios)[sel])) if sel.any() else 0,
                          "tramos": int(sel.sum())}
    return salida


def recuento(trk):
    """Qué hace `clean_v1` con un tracking, paso a paso, en sus tramos evaluados. Recuentos sin suprimir."""
    fps = float(trk.fps)
    bid = ids_de_tramo(trk)
    ev = bid >= 0
    bx0, by0 = np.asarray(trk.bx, dtype=np.float64), np.asarray(trk.by, dtype=np.float64)
    visto0 = np.isfinite(bx0) & np.isfinite(by0)

    # Los mismos pasos que clean_v1, con sus funciones, para contar cada uno por separado.
    paso1 = ball.drop_jumps(bx0, by0, trk.fps)
    paso2 = ball.drop_isolated(visto0)
    bx1, by1 = bx0.copy(), by0.copy()
    bx1[paso1 | paso2], by1[paso1 | paso2] = np.nan, np.nan
    bx3, by3 = ball.fill_short_gaps(trk, bx1, by1)
    limpio = ball.clean_v1(trk)
    if not (np.array_equal(limpio.bx, bx3, equal_nan=True) and np.array_equal(limpio.by, by3, equal_nan=True)):
        raise AssertionError("el recuento no reproduce clean_v1: revisa el script antes de leer nada")
    visto1 = np.isfinite(bx1) & np.isfinite(by1)
    visto3 = np.isfinite(bx3) & np.isfinite(by3)

    imposible = pares_imposibles(bx0, by0, fps, bid)
    huecos_ini, huecos_fin = ball.runs(~visto1)
    cortos = (huecos_ini > 0) & (huecos_fin < len(bx1)) & (huecos_fin - huecos_ini <= ball.MAX_GAP) & \
        ev[np.minimum(huecos_ini, len(ev) - 1)]
    rellenos = np.array([visto3[a] for a in huecos_ini[cortos]], dtype=bool)
    with np.errstate(invalid="ignore"):
        movido = visto0 & visto3 & ((bx0 != bx3) | (by0 != by3))
    cambia = ev & ((visto0 != visto3) | movido)
    equipo0, equipo3 = candidates.nearest_team(trk), candidates.nearest_team(limpio)
    return {
        "frames_evaluados": int(ev.sum()),
        "frames_evaluados_con_balon": int((ev & visto0).sum()),
        "pares_a_mas_de_40_m_s": int(imposible.sum()),
        "clases_de_los_pares": clasificar(imposible, bx0, by0, fps, bid),
        "paso1_puntos_quitados": int((ev & paso1).sum()),
        "paso2_puntos_quitados": int((ev & paso2 & ~paso1).sum()),
        "paso2_rachas_quitadas": int(np.sum([ev[a] for a in ball.runs(paso2 & ~paso1)[0]])),
        "paso3_huecos_cortos": int(cortos.sum()),
        "paso3_huecos_rellenos": int(rellenos.sum()),
        "paso3_frames_rellenos": int((ev & ~visto1 & visto3).sum()),
        "frames_cambiados": int(cambia.sum()),
        "saltos_antes": saltos(bx0, by0, fps, bid),
        "saltos_despues": saltos(bx3, by3, fps, bid),
        "pares_a_mas_de_40_m_s_despues": int(pares_imposibles(bx3, by3, fps, bid).sum()),
        "frames_con_otro_equipo_mas_cercano": int((ev & (equipo0 != equipo3)).sum()),
    }


def celda(n, minimo=MINIMO_CELDA):
    """Un recuento para imprimir: de 1 a minimo − 1 casos sale como "< 5"."""
    return "< {}".format(minimo) if 0 < n < minimo else str(n)


def pct(n, total, minimo=MINIMO_CELDA):
    if 0 < n < minimo or not total:
        return "–"
    return "{:.2f} %".format(100.0 * n / total).replace(".", ",")


def para_imprimir(r, minimo=MINIMO_CELDA):
    """Las líneas de la salida, con las celdas pequeñas suprimidas. Los controles salen siempre."""
    con_balon = r["frames_evaluados_con_balon"]
    pares = r["pares_a_mas_de_40_m_s"]
    lineas = [
        "Limpieza del balón (clean_v1) en el ATD del partido: frames evaluados, las dos partes juntas",
        "",
        "0. Controles (el perfil del ATD dice {}, {} y {})".format(PERFIL_EVALUADOS, PERFIL_CON_BALON, PERFIL_PARES),
        "   frames evaluados: {}".format(r["frames_evaluados"]),
        "   frames evaluados con balón: {}".format(con_balon),
        "   pares de frames seguidos a más de 40 m/s: {}".format(pares),
        "   ¿cuadran los tres? {}".format("sí" if (r["frames_evaluados"], con_balon, pares) ==
                                           (PERFIL_EVALUADOS, PERFIL_CON_BALON, PERFIL_PARES) else "NO"),
        "",
        "1. Paso 1, saltos imposibles",
        "   puntos quitados: {}".format(celda(r["paso1_puntos_quitados"], minimo)),
        "   los pares a más de 40 m/s, por clase (pares / tramos):",
    ]
    for nombre, c in r["clases_de_los_pares"].items():
        lineas.append("      {:<20} {:>6} / {:<6}  ({} de los pares)".format(
            nombre, celda(c["pares"], minimo), celda(c["tramos"], minimo), pct(c["pares"], pares, minimo)))
    lineas += [
        "",
        "2. Paso 2, rachas aisladas de 1 o 2 frames",
        "   puntos quitados: {}   rachas: {}".format(celda(r["paso2_puntos_quitados"], minimo),
                                                   celda(r["paso2_rachas_quitadas"], minimo)),
        "",
        "3. Paso 3, huecos de hasta {} frames".format(ball.MAX_GAP),
        "   huecos cortos tras los pasos 1 y 2: {}   rellenos: {}".format(
            celda(r["paso3_huecos_cortos"], minimo), celda(r["paso3_huecos_rellenos"], minimo)),
        "   frames rellenos: {}".format(celda(r["paso3_frames_rellenos"], minimo)),
        "",
        "4. En total",
        "   frames que cambian: {}   ({} de los frames evaluados con balón)".format(
            celda(r["frames_cambiados"], minimo), pct(r["frames_cambiados"], con_balon, minimo)),
        "   saltos imposibles entre puntos con balón seguidos: {} antes, {} después".format(
            celda(r["saltos_antes"], minimo), celda(r["saltos_despues"], minimo)),
        "   pares de frames seguidos a más de 40 m/s después: {}".format(
            celda(r["pares_a_mas_de_40_m_s_despues"], minimo)),
        "   frames con otro equipo como el más cercano (descriptivo): {}".format(
            celda(r["frames_con_otro_equipo_mas_cercano"], minimo)),
    ]
    return lineas


def medir(data_dir=None):
    """El recuento sobre el ATD del partido. Lee datos del partido: solo lo ejecuta una persona."""
    games.require(FICHEROS, games.GAME, data_dir)
    return recuento(tracking.from_atd(games.asset_paths(games.GAME, data_dir), games.GAME))


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
        print("No encuentro el ATD del partido: revisa que MTAH_DATA_DIR apunte a la carpeta de los datos.")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # los avisos de numpy no llevan datos, pero ensucian la salida
        lineas = para_imprimir(medir(args.data_dir))
    print("\n".join(lineas))
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
