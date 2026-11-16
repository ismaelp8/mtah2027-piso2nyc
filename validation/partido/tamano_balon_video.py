"""¿Cuántos píxeles mide el balón en el vídeo táctico? La escala de la homografía donde el ATD ve el balón.

**Solo lo ejecuta una persona, en local** (regla nº 1 de `CLAUDE.md`). Claude no lo ejecuta: lee el ATD y la
homografía del partido.

Por qué: es la primera puerta de la línea del balón del vídeo (16/11, `validation/balon_video/BITACORA.md`).
Un detector de balón solo sirve si el balón mide en la imagen lo bastante para verlo. El repo decía «unos 4
píxeles», pero era una cuenta (0,22 m en un campo de 105 m que ocupa 1.920 px), no una medida: la homografía
cambia en cada frame, así que la cámara se mueve o hace zoom, y el campo puede no ocupar toda la imagen.

Qué mide, en los frames evaluados en que el ATD ve el balón dentro del campo y la homografía es válida, **solo
agregados** (percentiles y porcentajes de todo el partido, nada por frame):
- los píxeles por metro de la homografía en el punto del balón, a lo largo del campo (x) y a lo ancho (y);
- el diámetro del balón en píxeles: 0,22 m por la mayor de las dos escalas. El césped se acorta con la
  perspectiva y una esfera no, así que la escala sin acortar es la mayor [aproximación: un balón en el aire está
  más cerca o más lejos de la cámara que su proyección en el césped];
- lo mismo por zonas: tercios a lo largo y mitades a lo ancho (la mitad más cercana a la cámara saldrá con más
  píxeles por metro);
- cuánto campo entra en la imagen, en todos los frames evaluados con homografía válida: en qué % entran las
  cuatro esquinas y cuántos metros de campo caben de lado a lado de la imagen a media altura.

Uso, desde la raíz del repo y con el entorno de siempre (solo numpy y pandas):

    python validation/partido/tamano_balon_video.py

Tarda un par de minutos (lee el ATD entero). Si falla, imprime solo el tipo de error y las líneas del código,
sin valores de datos. La salida se puede pegar a Claude tal cual.
"""

import argparse
import json
import os
import sys
import traceback
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
import games  # noqa: E402
from possession import tracking  # noqa: E402

FICHEROS = ["atd_meta", "atd_raw", "homography"]
DIAMETRO_BALON = 0.22  # m: balón de talla 5 (circunferencia de 68 a 70 cm)
PASO = 0.5  # m: medio paso de la diferencia centrada con la que se mide la escala
ANCHO_IMAGEN, ALTO_IMAGEN = 1920, 1080  # px: el vídeo táctico (DATA.md)
PERCENTILES = (5, 25, 50, 75, 95)
CLASES_DIAMETRO = (4.0, 6.0, 8.0, 12.0)  # px: cortes del histograma del diámetro


def proyectar(matrices, u, v):
    """Coordenadas normalizadas del campo (0–1) -> píxeles, con una matriz por punto. Como
    starter/load_homography.project, pero con un array de matrices (n, 3, 3)."""
    den = matrices[:, 2, 0] * u + matrices[:, 2, 1] * v + matrices[:, 2, 2]
    x = (matrices[:, 0, 0] * u + matrices[:, 0, 1] * v + matrices[:, 0, 2]) / den
    y = (matrices[:, 1, 0] * u + matrices[:, 1, 1] * v + matrices[:, 1, 2]) / den
    return x, y


def escala(matrices, u, v, delta_u, delta_v):
    """Píxeles por metro en (u, v) a lo largo de un paso (delta_u, delta_v) normalizado de 2·PASO metros."""
    x0, y0 = proyectar(matrices, u - delta_u, v - delta_v)
    x1, y1 = proyectar(matrices, u + delta_u, v + delta_v)
    return np.hypot(x1 - x0, y1 - y0) / (2.0 * PASO)


def percentiles(valores):
    valores = valores[np.isfinite(valores)]
    if not len(valores):
        return None
    return {"p{}".format(p): round(float(np.percentile(valores, p)), 2) for p in PERCENTILES}


def histograma(diametros):
    """% de frames por clase de diámetro: < 4, 4–6, 6–8, 8–12 y ≥ 12 px."""
    diametros = diametros[np.isfinite(diametros)]
    if not len(diametros):
        return None
    bordes = (0.0,) + CLASES_DIAMETRO + (np.inf,)
    salida = {}
    for bajo, alto in zip(bordes[:-1], bordes[1:]):
        nombre = ("< {:g} px".format(alto) if bajo == 0 else
                  ">= {:g} px".format(bajo) if not np.isfinite(alto) else "{:g}-{:g} px".format(bajo, alto))
        salida[nombre] = round(100.0 * float(np.mean((diametros >= bajo) & (diametros < alto))), 2)
    return salida


def medir(trk, matrices, validas, ancho_imagen=ANCHO_IMAGEN, alto_imagen=ALTO_IMAGEN):
    """Agregados de la escala de la imagen en el punto del balón y de cuánto campo se ve. Solo agregados."""
    n = len(trk.bx)
    if len(matrices) != n or len(validas) != n:
        raise ValueError("la homografía no tiene un frame por frame de vídeo")
    largo, ancho = trk.pitch
    evaluado = np.zeros(n, dtype=bool)
    for inicio, fin in trk.blocks:
        evaluado[inicio:fin] = True
    validas = np.asarray(validas, dtype=bool) & np.isfinite(matrices).all(axis=(1, 2))
    bx, by = np.asarray(trk.bx, dtype=np.float64), np.asarray(trk.by, dtype=np.float64)
    with np.errstate(invalid="ignore"):
        dentro = (bx >= 0) & (bx <= largo) & (by >= 0) & (by <= ancho)
    usar = evaluado & validas & np.isfinite(bx) & np.isfinite(by) & dentro
    idx = np.flatnonzero(usar)

    salida = {"frames_evaluados": int(evaluado.sum()),
              "frames_evaluados_con_homografia_valida": int((evaluado & validas).sum()),
              "frames_medidos_con_balon_del_atd_dentro_del_campo": int(len(idx))}
    if len(idx):
        mats = matrices[idx]
        u, v = bx[idx] / largo, by[idx] / ancho
        with np.errstate(invalid="ignore", divide="ignore"):
            sx = escala(mats, u, v, PASO / largo, 0.0)
            sy = escala(mats, u, v, 0.0, PASO / ancho)
            diametro = DIAMETRO_BALON * np.fmax(sx, sy)
        salida["px_por_metro_a_lo_largo"] = percentiles(sx)
        salida["px_por_metro_a_lo_ancho"] = percentiles(sy)
        salida["diametro_balon_px"] = percentiles(diametro)
        salida["pct_frames_por_diametro"] = histograma(diametro)
        zonas = {}
        tercio = largo / 3.0
        for i, nombre in enumerate(("x en el primer tercio", "x en el tercio central", "x en el último tercio")):
            en = (bx[idx] >= i * tercio) & (bx[idx] <= (i + 1) * tercio)
            zonas[nombre] = {"pct_frames": round(100.0 * float(en.mean()), 2),
                             "diametro_balon_px": percentiles(diametro[en])}
        for nombre, en in (("y < mitad del ancho", by[idx] < ancho / 2.0),
                           ("y >= mitad del ancho", by[idx] >= ancho / 2.0)):
            zonas[nombre] = {"pct_frames": round(100.0 * float(en.mean()), 2),
                             "diametro_balon_px": percentiles(diametro[en])}
        salida["por_zona"] = zonas

    # Cuánto campo entra en la imagen, en todos los frames evaluados con homografía válida.
    todos = np.flatnonzero(evaluado & validas)
    if len(todos):
        mats = matrices[todos]
        esquinas = []
        for u, v in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
            with np.errstate(invalid="ignore", divide="ignore"):
                x, y = proyectar(mats, np.full(len(todos), u), np.full(len(todos), v))
            esquinas.append((x >= 0) & (x <= ancho_imagen) & (y >= 0) & (y <= alto_imagen))
        salida["pct_frames_con_las_4_esquinas_en_la_imagen"] = round(
            100.0 * float(np.logical_and.reduce(esquinas).mean()), 2)
        with np.errstate(invalid="ignore", divide="ignore"):
            inversas = np.linalg.inv(mats)
            mitad = np.full(len(todos), alto_imagen / 2.0)
            # Los bordes izquierdo y derecho de la imagen, a media altura, llevados al campo (en metros).
            ui, vi = proyectar(inversas, np.zeros(len(todos)), mitad)
            ud, vd = proyectar(inversas, np.full(len(todos), float(ancho_imagen)), mitad)
            metros = np.hypot((ud - ui) * largo, (vd - vi) * ancho)
        salida["metros_de_campo_de_lado_a_lado_a_media_altura"] = percentiles(metros)
    return salida


def informe_de_error(error):
    pila = traceback.extract_tb(error.__traceback__)
    lineas = ["{}:{} ({})".format(os.path.basename(f.filename), f.lineno, f.name) for f in pila]
    return "ERROR {} en {}".format(type(error).__name__, " <- ".join(reversed(lineas)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD o la homografía del partido: revisa que MTAH_DATA_DIR apunte a la carpeta "
              "de los datos.")
        return 1
    from starter import load_homography  # aquí, para que la prueba sin datos no necesite pandas
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        trk = tracking.from_atd(games.asset_paths(games.GAME, args.data_dir), games.GAME)
        matrices, _, validas = load_homography.load(games.GAME, args.data_dir)
        salida = medir(trk, matrices, validas)
    print(json.dumps(dict({"medida": "tamaño del balón en el vídeo táctico (escala de la homografía en el punto "
                                     "del balón del ATD), frames evaluados"}, **salida),
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
