"""Prueba de validation/partido/balon_fuera.py (D7) con un balón y unas etiquetas inventados. No lee nada del partido.

    python validation/scripts/prueba_balon_fuera.py

Comprueba `medir` y la lectura de la regla con casos de cada tipo: una racha que ya es `D`, otras con nuestro
`D` a distintas esperas, una sin `D`, una demasiado corta, el balón dentro del margen de 1 m, el tramo excluido
y las celdas pequeñas suprimidas. Sale con código 1 si falla algo.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import balon_fuera as bf  # noqa: E402

H, A, D, X = bf.pm.H, bf.pm.A, bf.pm.D, bf.pm.X
PITCH = (105.0, 68.0)
fallos = []


def comprobar(ok, texto, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", texto, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(texto)


def partido_inventado():
    """Un tramo de 3000 frames con el balón en el centro y seis salidas, y otro de 1000 excluido."""
    n = 4000
    bx, by = np.full(n, 50.0), np.full(n, 30.0)
    etiquetas = np.full(n, H, dtype=np.int8)
    # 1) por la banda, 30 frames, ya en D
    by[100:130] = 70.0
    etiquetas[90:200] = D
    # 2) por el fondo, 40 frames, nuestro D llega 8 frames después (a tiempo)
    bx[400:440] = 107.0
    etiquetas[408:500] = D
    # 3) por la banda, 60 frames, nuestro D llega 40 frames después (tarde)
    by[700:760] = -3.0
    etiquetas[740:800] = D
    # 4) por la banda, 20 frames, nuestro D no llega
    by[1000:1020] = 72.0
    # 5) demasiado corta: 3 frames
    by[1500:1503] = 75.0
    # 6) dentro del margen de 1 m: no cuenta
    by[1800:1900] = 68.5
    # 7) por el fondo, 30 frames, con A y nuestro D a 200 frames
    bx[2200:2230] = -2.0
    etiquetas[2200:2400] = A
    etiquetas[2400:2500] = D
    # sin balón en unos frames
    bx[2600:2700] = np.nan
    # 8) en el tramo excluido (como el de antes del saque): no cuenta
    by[3200:3260] = 70.0
    excluidos = np.zeros(n, dtype=bool)
    excluidos[3000:4000] = True
    return bx, by, etiquetas, ((0, 3000), (3000, 4000)), excluidos


def main():
    print("D7: recuento del balón fuera con un partido inventado")
    bx, by, etiquetas, blocks, excluidos = partido_inventado()
    res = bf.medir(bx, by, etiquetas, blocks, PITCH, excluidos)
    comprobar(res["fuera"] == 30 + 40 + 60 + 20 + 3 + 30, "frames con el balón a más de 1 m fuera",
              str(res["fuera"]))
    comprobar(res["vistos"] == 3000 - 100, "frames con balón, sin los excluidos", str(res["vistos"]))
    comprobar(res["por_etiqueta"][D] == 30 + 32 + 20 and res["por_etiqueta"][A] == 30,
              "frames fuera por etiqueta", str(res["por_etiqueta"]))
    comprobar(res["rachas"] == 5 and res["rachas_cortas"] == 1, "rachas de 5 frames o más, y la corta aparte")
    comprobar(res["por_lado"] == {"fondo": 2, "banda": 3}, "rachas por lado", str(res["por_lado"]))
    comprobar(res["ya_en_d"] == 1 and res["sin_d"] == 1, "una ya en D y una sin D")
    comprobar(res["tarde"] == {(1, 12): 1, (13, 25): 0, (26, 50): 1, (51, 125): 0, (126, 250): 1},
              "espera hasta nuestro D, en intervalos", str(res["tarde"]))
    comprobar(bf.llegamos_tarde(res) == 3, "llegamos tarde en 3 de 5 (40, 200 y sin D)")
    comprobar(bf.lectura(res) == "se cierra", "con menos de 10 rachas tarde, la regla cierra")
    texto = "\n".join(bf.lineas(res, "inventada.csv"))
    comprobar("| A | < 5 |" not in texto and "| X | 0 |" in texto and "< 5" in texto,
              "celdas de 1 a 4 casos como «< 5»")
    sin_tarde = {(1, 12): 0, (13, 25): 0, (26, 50): 0, (51, 125): 0, (126, 250): 0}
    abierta = dict(res, rachas=40, sin_d=6,
                   tarde={(1, 12): 4, (13, 25): 4, (26, 50): 6, (51, 125): 0, (126, 250): 0})
    comprobar(bf.llegamos_tarde(abierta) == 16 and bf.lectura(abierta).startswith("queda abierta"),
              "16 de 40 tarde (40 %): queda abierta")
    medio = dict(res, rachas=50, sin_d=4, tarde={(1, 12): 4, (13, 25): 0, (26, 50): 6, (51, 125): 0,
                                                 (126, 250): 0})
    comprobar(bf.llegamos_tarde(medio) == 10 and bf.lectura(medio).startswith("no concluye"),
              "10 de 50 tarde (20 %): no concluye")
    pocas = dict(res, rachas=20, sin_d=9, tarde=sin_tarde)
    comprobar(bf.lectura(pocas) == "se cierra", "9 tarde, aunque sean el 45 %: se cierra (menos de 10)")
    comprobar_capa()
    print()
    if fallos:
        print("FALLAN {} comprobaciones".format(len(fallos)))
        sys.exit(1)
    print("TODO BIEN")


def comprobar_capa():
    """La capa apagada `dead_ball.ball_out` con el mismo partido inventado."""
    print("D7: la capa apagada (dead_ball.ball_out) con un tracking inventado")
    from possession import dead_ball, pipeline, tracking
    bx, by, _, blocks, _ = partido_inventado()
    vacio = np.full((len(bx), 2), np.nan, dtype=np.float32)
    trk = tracking.Tracking(bx, by, vacio, vacio, np.array([0, 1], dtype=np.int8), PITCH, ((0, 3000),), 25)
    score, allowed = dead_ball.ball_out(trk)
    puntuados = np.flatnonzero(score[:, tracking.D])
    cola = dead_ball.BALL_OUT_TAIL
    esperados = np.concatenate([np.arange(a, b - cola) for a, b in
                                ((100, 130), (400, 440), (700, 760), (1000, 1020), (2200, 2230)) if b - a > cola])
    comprobar(np.array_equal(puntuados, esperados),
              "puntúa las rachas de 5 frames o más sin sus últimos {} frames, y nada más".format(cola),
              "{} frames".format(len(puntuados)))
    comprobar(bool(np.all(score[puntuados, tracking.D] == dead_ball.BALL_OUT_SCORE))
              and not score[:, :2].any() and bool(allowed.all()),
              "solo la columna D, con su peso, y no prohíbe nada")
    comprobar(not score[3000:, tracking.D].any(), "fuera de los tramos evaluados no puntúa (la racha de 3200)")
    comprobar(pipeline.PIECES["candidates"] == "aprendida.evidence_b5" and "ball_out" not in str(pipeline.PIECES),
              "está apagada: no es una pieza de la entrega")
    import inspect
    comprobar("ball_out" not in inspect.getsource(dead_ball.evidence),
              "dead_ball.evidence (la de la entrega) no la llama")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
