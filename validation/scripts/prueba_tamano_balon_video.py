"""Prueba `validation/partido/tamano_balon_video.py` con un tracking y unas homografías inventadas.

    python validation/scripts/prueba_tamano_balon_video.py

Sin datos de ningún partido. Lo puede ejecutar cualquiera, Claude incluido. Prueba que la escala y el diámetro
salen bien con dos cámaras de escala conocida (el campo entero en 1.920 px y un zoom ×2), qué frames entran
(fuera de los tramos, sin balón, balón fuera del campo, homografía no válida), que la mitad más cercana a una
cámara en perspectiva sale con más píxeles, cuánto campo entra en la imagen, y que la salida solo lleva agregados.
"""

import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import tamano_balon_video as tb  # noqa: E402
from possession.tracking import Tracking  # noqa: E402

FALLOS = []
LARGO, ANCHO = 105.3, 68.0
N = 2000


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def tracking(bx, by, bloques=((0, N),)):
    vacio = np.full((len(bx), 2), np.nan, dtype=np.float32)
    return Tracking(np.asarray(bx, float), np.asarray(by, float), vacio, vacio.copy(), np.array([0, 1], np.int8),
                    (LARGO, ANCHO), tuple(bloques), 25)


def camara_entera():
    """El campo entero en la imagen: (u, v) -> (1920·u, 1080·v)."""
    return np.array([[1920.0, 0.0, 0.0], [0.0, 1080.0, 0.0], [0.0, 0.0, 1.0]])


def camara_zoom():
    """Zoom ×2 sobre el centro: (u, v) -> (3840·u − 960, 2160·v − 540)."""
    return np.array([[3840.0, 0.0, -960.0], [0.0, 2160.0, -540.0], [0.0, 0.0, 1.0]])


def main():
    print("Prueba de validation/partido/tamano_balon_video.py")
    rng = np.random.default_rng(0)
    bx = rng.uniform(20, 85, N)
    by = rng.uniform(10, 58, N)

    # 1. El campo entero en 1.920 px: 18,23 px/m a lo largo, 15,88 a lo ancho, balón de 4,01 px.
    mats = np.repeat(camara_entera()[None], N, axis=0)
    s = tb.medir(tracking(bx, by), mats, np.ones(N, bool))
    p50 = s["diametro_balon_px"]["p50"]
    check("campo entero: balón de 0,22 × 1920/105,3 = 4,01 px", abs(p50 - 0.22 * 1920 / LARGO) < 0.01, p50)
    check("campo entero: px por metro a lo largo y a lo ancho",
          abs(s["px_por_metro_a_lo_largo"]["p50"] - 1920 / LARGO) < 0.01
          and abs(s["px_por_metro_a_lo_ancho"]["p50"] - 1080 / ANCHO) < 0.01,
          (s["px_por_metro_a_lo_largo"]["p50"], s["px_por_metro_a_lo_ancho"]["p50"]))
    check("campo entero: entran las 4 esquinas en el 100 % y caben 105,3 m de lado a lado",
          s["pct_frames_con_las_4_esquinas_en_la_imagen"] == 100.0
          and abs(s["metros_de_campo_de_lado_a_lado_a_media_altura"]["p50"] - LARGO) < 0.01,
          (s["pct_frames_con_las_4_esquinas_en_la_imagen"], s["metros_de_campo_de_lado_a_lado_a_media_altura"]))
    check("campo entero: todos en la clase 4–6 px", s["pct_frames_por_diametro"]["4-6 px"] == 100.0,
          s["pct_frames_por_diametro"])

    # 2. Mitad con zoom ×2: el balón mide el doble y el campo ya no entra entero.
    mitad = N // 2
    mats = np.concatenate([np.repeat(camara_entera()[None], mitad, axis=0),
                           np.repeat(camara_zoom()[None], N - mitad, axis=0)])
    s = tb.medir(tracking(bx, by), mats, np.ones(N, bool))
    check("con zoom: p95 del diámetro de 8,02 px y las 4 esquinas solo en la mitad",
          abs(s["diametro_balon_px"]["p95"] - 2 * 0.22 * 1920 / LARGO) < 0.01
          and s["pct_frames_con_las_4_esquinas_en_la_imagen"] == 50.0,
          (s["diametro_balon_px"], s["pct_frames_con_las_4_esquinas_en_la_imagen"]))
    check("con zoom: caben 52,65 m de lado a lado en esos frames",
          abs(s["metros_de_campo_de_lado_a_lado_a_media_altura"]["p5"] - LARGO / 2) < 0.01,
          s["metros_de_campo_de_lado_a_lado_a_media_altura"])

    # 3. Qué frames entran: fuera de los tramos, sin balón, balón fuera del campo y homografía no válida, no.
    bx2, by2 = bx.copy(), by.copy()
    bx2[100:200] = np.nan  # sin balón
    bx2[200:300] = -3.0  # balón fuera del campo
    validas = np.ones(N, bool)
    validas[300:400] = False
    mats = np.repeat(camara_entera()[None], N, axis=0)
    mats[400:450] = np.nan  # matriz no válida aunque la columna diga que sí
    s = tb.medir(tracking(bx2, by2, bloques=((0, 1500),)), mats, validas)
    esperados = 1500 - 100 - 100 - 100 - 50
    check("solo cuentan los frames evaluados con balón dentro y homografía válida",
          s["frames_medidos_con_balon_del_atd_dentro_del_campo"] == esperados
          and s["frames_evaluados"] == 1500 and s["frames_evaluados_con_homografia_valida"] == 1350,
          (s["frames_medidos_con_balon_del_atd_dentro_del_campo"], esperados, s["frames_evaluados"],
           s["frames_evaluados_con_homografia_valida"]))

    # 4. Cámara en perspectiva (en la banda de y = 68 m, mirando al campo): la mitad cercana, más píxeles.
    persp = np.array([[1920.0, 0.0, 0.0], [0.0, 700.0, 100.0], [0.0, -0.6, 1.0]])
    mats = np.repeat(persp[None], N, axis=0)
    s = tb.medir(tracking(bx, by), mats, np.ones(N, bool))
    lejos = s["por_zona"]["y < mitad del ancho"]["diametro_balon_px"]["p50"]
    cerca = s["por_zona"]["y >= mitad del ancho"]["diametro_balon_px"]["p50"]
    check("perspectiva: la mitad cercana a la cámara sale con el balón más grande", cerca > lejos, (lejos, cerca))
    reparto = sum(s["por_zona"][z]["pct_frames"] for z in ("x en el primer tercio", "x en el tercio central",
                                                            "x en el último tercio"))
    check("los tercios a lo largo suman el 100 %", abs(reparto - 100.0) < 0.05, reparto)

    # 5. Solo agregados: nada de la salida tiene una entrada por frame.
    texto = json.dumps(s, ensure_ascii=False)
    def tamanos(obj):
        if isinstance(obj, dict):
            return max([len(obj)] + [tamanos(x) for x in obj.values()])
        if isinstance(obj, list):
            return max([len(obj)] + [tamanos(x) for x in obj])
        return 0
    check("la salida solo lleva agregados (ninguna lista ni diccionario de más de 12 entradas)",
          tamanos(s) <= 12 and len(texto) < 3000, (tamanos(s), len(texto)))

    print("\nTODO BIEN" if not FALLOS else "\nFALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
    return 0 if not FALLOS else 1


if __name__ == "__main__":
    sys.exit(main())
