"""Prueba la evidencia aprendida de la apuesta B (possession/aprendida.py) sin cargar ningún partido.

    python validation/scripts/prueba_aprendida.py

Con el partido inventado del harness (`puntuar.partido_de_prueba`) comprueba:

- la interfaz: arrays (n, 3), puntuación finita, columna `D` a cero, cero fuera de los tramos y todo
  permitido;
- el determinismo: dos ejecuciones dan lo mismo;
- la simetría: cambiar los equipos intercambia `H` y `A` exactamente;
- que no depende del orden de los slots: una permutación fija da la misma puntuación tras redondear;
- los coeficientes: los 64 juegos (B1 a B8; los 7 partidos y un pliegue sin cada partido), con tantos
  pesos como rasgos, y el bloque del módulo es el que escribe `validation/apuesta_b/entrenar.py`;
- B3 y B4 (14/11): con la misma α, B3 con el balón a la vista en todos los frames es B2, B3 no opina sin
  balón, B4 da la misma diferencia `H` − `A` que B2 y su ganador nunca supera a `D`; B5 es B4 más N1;
  B3, B4 y B5 llevan los pesos de B2;
- la ronda de reentrenamiento (15/11): el detector de toques con un balón inventado, las columnas de B6 y
  B8, que B6 a B8 puntúan como B5, que B7 con peso 1 es el ajuste sin pesos y qué frames están cerca de un
  cambio.

No usa datos del partido ni de la DFL. Sale con código 1 si falla alguna comprobación. Claude puede
ejecutarlo.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, os.path.join(ROOT, "validation", "apuesta_b"))
sys.path.insert(0, ROOT)
import dfl  # noqa: E402
import entrenar  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, ball, tracking  # noqa: E402

fallos = []


def comprobar(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + detalle if detalle else ""))
    if not ok:
        fallos.append(nombre)


def mas_cercano_a_mano(trk):
    """El equipo del slot más cercano al balón, frame a frame y sin vectorizar: la referencia de la prueba."""
    salida = np.full(len(trk.bx), -1, dtype=np.int8)
    for t in range(len(trk.bx)):
        if np.isnan(trk.bx[t]) or np.isnan(trk.by[t]):
            continue
        mejor, distancia = -1, np.inf
        for slot in range(trk.px.shape[1]):
            d2 = (float(trk.px[t, slot]) - trk.bx[t]) ** 2 + (float(trk.py[t, slot]) - trk.by[t]) ** 2
            if np.isfinite(d2) and d2 < distancia:
                mejor, distancia = slot, d2
        if mejor >= 0:
            salida[t] = trk.team[mejor]
    return salida


def balon_con_un_toque(n=400, t0=200, fps=25.0):
    """Un balón inventado a 5 m/s en x que en `t0` pasa a 5 m/s en y, suavizado con una media de 25 frames."""
    vx = np.where(np.arange(n) < t0, 5.0, 0.0)
    vy = np.where(np.arange(n) < t0, 0.0, 5.0)
    media = np.ones(25) / 25
    x = np.convolve(np.pad(30 + np.cumsum(vx) / fps, 12, mode="edge"), media, "valid")
    y = np.convolve(np.pad(20 + np.cumsum(vy) / fps, 12, mode="edge"), media, "valid")
    return x, y


def jugadores_a(x, y, local, visitante):
    """Un jugador de cada equipo a `local` y `visitante` metros del balón en x, como `_por_equipo`."""
    hay = np.ones((len(x), 1), bool)
    return [((x + local)[:, None], y[:, None], hay), ((x + visitante)[:, None], y[:, None], hay)]


def comprobar_ronda(trk, z, visible, cercano, alfa):
    """La ronda de reentrenamiento (docs/decisiones.md, 15/11): las comprobaciones del instrumento."""
    print("Ronda de reentrenamiento (B6, B7 y B8): el instrumento")
    fps, t0 = 25.0, 200
    x, y = balon_con_un_toque(t0=t0, fps=fps)
    signo = aprendida.eventos_de_toque(x, y, jugadores_a(x, y, 2.0, 10.0), fps)
    eventos = np.flatnonzero(signo)
    comprobar("un cambio brusco de velocidad suavizado con 25 frames da un solo evento a ±2 frames de su sitio",
              len(eventos) == 1 and abs(int(eventos[0]) - t0) <= 2, "en {}".format(eventos.tolist()))
    comprobar("con el local a 2 m el signo es +1, con el visitante a 2 m es −1 y sin nadie a 3 m es 0",
              signo[eventos].tolist() == [1.0]
              and aprendida.eventos_de_toque(x, y, jugadores_a(x, y, 10.0, 2.0), fps)[eventos].tolist() == [-1.0]
              and not aprendida.eventos_de_toque(x, y, jugadores_a(x, y, 4.0, 6.0), fps).any())
    recto = 30 + np.arange(400) * 5 / fps
    comprobar("un balón a velocidad constante no da ningún evento",
              not aprendida.eventos_de_toque(recto, np.full(400, 20.0), jugadores_a(recto, recto, 2.0, 9.0), fps).any())
    b2, b6, b8 = (aprendida.rasgos(trk, c) for c in ("b2", "b6", "b8"))
    sin_151 = [j for j, nombre in enumerate(aprendida.NOMBRES["b2"]) if not nombre.endswith("ventana 151")]
    comprobar("B8 son los rasgos de B2 y dos más; B6, los de B2 sin los cinco de 151",
              np.array_equal(b8[:, :b2.shape[1]], b2) and b8.shape[1] == b2.shape[1] + 2
              and np.array_equal(b6, b2[:, sin_151]) and len(sin_151) == b2.shape[1] - 5)
    comprobar("las columnas que usa entrenar.py son las de cada conjunto",
              all(np.array_equal(b8[:, entrenar.columnas(c)], aprendida.rasgos(trk, c)) for c in ("b1", "b2", "b6", "b7")))
    b5, _ = aprendida.puntuacion_de("b5", z, visible, alfa, cercano)
    comprobar("B6, B7 y B8 puntúan como B5 con el mismo logit",
              all(np.array_equal(aprendida.puntuacion_de(c, z, visible, alfa, cercano)[0], b5) for c in ("b6", "b7", "b8")))
    rng = np.random.default_rng(3)
    X = rng.normal(size=(2000, 4))
    y = (X @ np.array([1.0, -0.5, 0.0, 2.0]) + rng.normal(size=2000) > 0).astype(float)
    comprobar("B7 con peso 1 en todas las filas da los pesos del ajuste sin pesos",
              entrenar.ajustar(X, y)[0] == entrenar.ajustar(X, y, np.ones(len(y)))[0])
    H, A, D = tracking.H, tracking.A, tracking.D
    # H hasta 99, A hasta 199, D hasta 219 (el H de después no es un cambio), H hasta 409 y A hasta el final.
    flag = np.array([H] * 100 + [A] * 100 + [D] * 20 + [H] * 190 + [A] * 190)
    control = flag.copy()
    control[100:130] = H  # en el control el cambio llega 30 frames tarde
    cerca = entrenar.cerca_de_un_cambio({"flag": flag, "control": control}, ((0, 400), (400, 600)))
    esperado = np.zeros(600, bool)
    esperado[80:181] = True  # el cambio del control, en 130, ±50 (el del flag en 100 no cuenta solo)
    esperado[400:461] = True  # cambio en 410, en el tramo que empieza en 400: no pasa al tramo anterior
    comprobar("cerca de un cambio: ±50 frames de un cambio del control, sin contar a través de D ni cruzar tramos",
              np.array_equal(cerca, esperado), "{} frames".format(int(cerca.sum())))


def main():
    trk = puntuar.partido_de_prueba()
    fuera_de_tramos = np.ones(len(trk.bx), bool)
    for inicio, fin in trk.blocks:
        fuera_de_tramos[inicio:fin] = False
    for nombre, funcion in (("B1", aprendida.evidence_b1), ("B2", aprendida.evidence_b2),
                            ("B3", aprendida.evidence_b3), ("B4", aprendida.evidence_b4),
                            ("B5", aprendida.evidence_b5), ("B6", aprendida.evidence_b6),
                            ("B7", aprendida.evidence_b7), ("B8", aprendida.evidence_b8)):
        print(nombre)
        score, allowed = funcion(trk)
        comprobar("arrays (n, 3), puntuación finita y todo permitido",
                  score.shape == (len(trk.bx), 3) and allowed.shape == score.shape
                  and np.isfinite(score).all() and allowed.all())
        comprobar("la columna D a cero y cero fuera de los tramos",
                  (score[:, tracking.D] == 0).all() and (score[fuera_de_tramos] == 0).all())
        comprobar("opina en los tramos", bool((score[~fuera_de_tramos, :2] != 0).any()))
        otra, _ = funcion(trk)
        comprobar("dos ejecuciones dan lo mismo", np.array_equal(score, otra))
        cambiado, _ = funcion(trk._replace(team=(1 - trk.team).astype(np.int8)))
        comprobar("cambiar los equipos intercambia H y A exactamente",
                  np.array_equal(cambiado[:, tracking.H], score[:, tracking.A])
                  and np.array_equal(cambiado[:, tracking.A], score[:, tracking.H]))
        orden = np.random.default_rng(7).permutation(trk.px.shape[1])
        permutado, _ = funcion(trk._replace(px=trk.px[:, orden], py=trk.py[:, orden], team=trk.team[orden]))
        comprobar("una permutación fija de los slots no cambia la puntuación (tras redondear)",
                  np.array_equal(permutado, score), "máx. {:.1e}".format(float(np.abs(permutado - score).max())))
        for partido in dfl.PARTIDOS:
            if not np.isfinite(funcion(trk, fuera=partido)[0]).all():
                comprobar("el pliegue sin {} da una puntuación finita".format(partido), False)
    print("B3, B4 y B5 frente a B2, con la misma α")
    juego = aprendida.coeficientes("b2")
    z = aprendida.logit(aprendida.rasgos(trk, "b2"), juego["pesos"])
    visible = aprendida.balon_visible(trk)
    b2, _ = aprendida.puntuacion_de("b2", z, visible, juego["alfa"])
    b3_todo, _ = aprendida.puntuacion_de("b3", z, np.ones(len(z), bool), juego["alfa"])
    b3, _ = aprendida.puntuacion_de("b3", z, visible, juego["alfa"])
    b4, _ = aprendida.puntuacion_de("b4", z, visible, juego["alfa"])
    comprobar("B3 con el balón a la vista en todos los frames es B2", np.array_equal(b3_todo, b2))
    comprobar("B3 no opina donde no se ve el balón y es B2 donde se ve",
              (b3[~visible] == 0).all() and np.array_equal(b3[visible], b2[visible]) and (~visible).any())
    comprobar("B4 da la misma diferencia H − A que B2",
              np.array_equal(b4[:, tracking.H] - b4[:, tracking.A], b2[:, tracking.H] - b2[:, tracking.A]))
    comprobar("el ganador de B4 nunca supera a D (margen cero)",
              (np.max(b4[:, :2], axis=1) == b4[:, tracking.D]).all() and (b4[:, tracking.D] == 0).all())
    cercano = aprendida.equipo_mas_cercano(trk)
    comprobar("el más cercano de B5 es el de una búsqueda a fuerza bruta (N1, desempate al índice más bajo)",
              np.array_equal(cercano, mas_cercano_a_mano(trk)))
    b5, _ = aprendida.puntuacion_de("b5", z, visible, juego["alfa"], cercano)
    n1 = np.zeros((len(trk.bx), 3))  # N1 escrito a mano: N1_PUNTOS al equipo del más cercano
    n1[cercano == tracking.H, tracking.H] = aprendida.N1_PUNTOS
    n1[cercano == tracking.A, tracking.A] = aprendida.N1_PUNTOS
    tramos = ~fuera_de_tramos
    b5_modulo, _ = aprendida.evidence_b5(trk)
    b4_con_alfa_de_b5, _ = aprendida.puntuacion_de("b4", z, visible, aprendida.coeficientes("b5")["alfa"])
    comprobar("B5 es exactamente B4 más la puntuación de N1", np.array_equal(b5, b4 + n1))
    comprobar("evidence_b5 es B4 más N1 en los tramos y cero fuera",
              np.array_equal(b5_modulo[tramos], (b4_con_alfa_de_b5 + n1)[tramos]) and (b5_modulo[~tramos] == 0).all())
    comprobar("la diferencia H − A de B5 es la de B2 más la de N1",
              np.allclose(b5[:, tracking.H] - b5[:, tracking.A],
                          (b2[:, tracking.H] - b2[:, tracking.A]) + (n1[:, tracking.H] - n1[:, tracking.A]), atol=1e-9))
    comprobar("B3, B4 y B5 llevan los pesos de B2 en todos los pliegues",
              all(aprendida.COEFICIENTES[c][k]["pesos"] == aprendida.COEFICIENTES["b2"][k]["pesos"]
                  for c in ("b3", "b4", "b5") for k in aprendida.COEFICIENTES["b2"]))
    limpio = ball.clean(trk)
    comprobar("ball.clean devuelve el balón tal cual (si cambia, hay que reentrenar la apuesta B con entrenar.py)",
              np.array_equal(limpio.bx, trk.bx, equal_nan=True) and np.array_equal(limpio.by, trk.by, equal_nan=True))
    comprobar_ronda(trk, z, visible, cercano, juego["alfa"])
    print("Coeficientes")
    claves = {"todos"} | set(dfl.PARTIDOS)
    for conjunto in aprendida.CONJUNTOS:
        juegos = aprendida.COEFICIENTES.get(conjunto, {})
        comprobar("{}: los 7 partidos y un pliegue sin cada uno".format(conjunto), set(juegos) == claves)
        comprobar("{}: tantos pesos como rasgos y α positiva".format(conjunto),
                  all(len(j["pesos"]) == len(aprendida.NOMBRES[conjunto]) and j["alfa"] > 0 for j in juegos.values()))
    modelos = {c: {k: (j["alfa"], j["pesos"]) for k, j in aprendida.COEFICIENTES[c].items()}
               for c in aprendida.CONJUNTOS}
    with open(entrenar.MODULO, encoding="utf-8") as handle:
        texto = handle.read()
    comprobar("el bloque del módulo es el que escribe entrenar.py",
              "\n".join(entrenar.bloque_de_coeficientes(modelos)) in texto)
    try:
        aprendida.coeficientes("b1", "J00000")
        sin_pliegue = False
    except KeyError:
        sin_pliegue = True
    comprobar("un pliegue que no existe da error", sin_pliegue)
    print()
    if fallos:
        print("FALLAN {} comprobaciones".format(len(fallos)))
        sys.exit(1)
    print("TODO BIEN")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
