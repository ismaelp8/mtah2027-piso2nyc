"""Prueba la limpieza del balón y la evidencia de equipo con casos inventados de resultado conocido.

    python validation/scripts/prueba_limpieza.py

Sin datos del partido: todo el tracking es inventado, y abrir un fichero durante las pruebas es un error
(`sin_ficheros` intercepta `builtins.open` e `io.open`, no las lecturas de numpy o de otras librerías).
Lo puede ejecutar cualquiera, Claude incluido. Prueba:

- `possession/ball.py`: los tres pasos de `clean_v1`, sus bordes y la corrección del 14/11 (el paso 2 se
  calcula sobre el balón de entrada, así que un pico no aísla al balón bueno de al lado);
- `possession/candidates.py`: N1 igual que la versión 0, N2 y Ret;
- `validation/partido/limpieza_balon.py`: `recuento` con un tracking de resultado conocido.
"""

import builtins
import contextlib
import io
import os
import re
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import limpieza_balon as lb  # noqa: E402
from possession import ball, candidates  # noqa: E402
from possession.tracking import Tracking  # noqa: E402

FALLOS = []


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


@contextlib.contextmanager
def sin_ficheros():
    """Abrir un fichero dentro del bloque es un error: las piezas y el recuento no leen nada."""
    abrir, abrir_io = builtins.open, io.open

    def niega(*args, **kwargs):
        raise AssertionError("una prueba ha intentado abrir un fichero")

    builtins.open = io.open = niega
    try:
        yield
    finally:
        builtins.open, io.open = abrir, abrir_io


def pista(n, bx, by, px, py, team, blocks=None):
    return Tracking(np.asarray(bx, float), np.asarray(by, float), np.asarray(px, float), np.asarray(py, float),
                    np.asarray(team, np.int8), (105.0, 68.0), blocks or ((0, n),), 25)


def jugadores(n, h=(50.0, 30.0), a=(60.0, 40.0)):
    px = np.tile([h[0], a[0]], (n, 1)).astype(float)
    py = np.tile([h[1], a[1]], (n, 1)).astype(float)
    return px, py, [0, 1]


def nearest_v0(trk):
    """La versión 0 de candidates.nearest_team, copiada tal cual, para comparar."""
    out = np.full(len(trk.bx), -1, dtype=np.int8)
    seen = np.flatnonzero(~np.isnan(trk.bx) & ~np.isnan(trk.by))
    for start in range(0, len(seen), 20000):
        idx = seen[start:start + 20000]
        dx = trk.px[idx].astype(np.float64) - trk.bx[idx, None]
        dy = trk.py[idx].astype(np.float64) - trk.by[idx, None]
        d2 = dx * dx + dy * dy
        d2 = np.where(np.isnan(d2), np.inf, d2)
        best = np.argmin(d2, axis=1)
        found = np.isfinite(d2[np.arange(len(idx)), best])
        out[idx[found]] = trk.team[best[found]]
    return out


def limpieza():
    print("Limpieza del balón (clean_v1)")
    n = 60
    px, py, team = jugadores(n)
    # balón quieto y lejos de todos: sin jugadores a 2 m, así la protección no actúa
    bx, by = np.full(n, 20.0), np.full(n, 20.0)
    bx[10] = 40.0  # un pico: 20 m en un frame (500 m/s) a la ida y a la vuelta
    out = ball.clean_v1(pista(n, bx, by, px, py, team))
    check("quita un pico imposible y lo rellena con sus vecinos", out.bx[10] == 20.0, out.bx[10])

    bx, by = np.full(n, 20.0), np.full(n, 20.0)
    bx[30:] = 45.0  # un salto que se queda: no es un pico
    out = ball.clean_v1(pista(n, bx, by, px, py, team))
    check("no borra el primer punto bueno tras un salto", out.bx[30] == 45.0 and out.bx[29] == 20.0)

    bx, by = np.full(n, np.nan), np.full(n, np.nan)
    bx[0:5], by[0:5] = 20.0, 20.0
    bx[20], by[20] = 20.5, 20.0  # racha de 1 entre huecos largos
    bx[40:42], by[40:42] = 21.0, 20.0  # racha de 2
    bx[50:53], by[50:53] = 21.0, 20.0  # racha de 3: se queda
    out = ball.clean_v1(pista(n, bx, by, px, py, team))
    check("quita una racha aislada de 1 frame", np.isnan(out.bx[20]))
    check("quita una racha aislada de 2 frames", np.isnan(out.bx[40:42]).all())
    check("deja una racha de 3 frames", not np.isnan(out.bx[50:53]).any())
    check("no toca una racha al principio sin hueco antes", not np.isnan(out.bx[0:5]).any())

    for hueco, esperado in ((12, True), (13, False)):
        bx, by = np.linspace(10, 30, n), np.full(n, 20.0)
        bx[20:20 + hueco], by[20:20 + hueco] = np.nan, np.nan
        out = ball.clean_v1(pista(n, bx, by, px, py, team))
        relleno = not np.isnan(out.bx[20:20 + hueco]).any()
        check("hueco de {} frames {}".format(hueco, "se interpola" if esperado else "no se interpola"),
              relleno == esperado)
        if esperado:
            check("la interpolación es la recta", np.allclose(out.bx, np.linspace(10, 30, n)))

    bx, by = np.full(n, 20.0), np.full(n, 20.0)
    bx[10:30], by[10:30] = np.nan, np.nan  # hueco largo, no se toca
    bx[40:45], by[40:45] = np.nan, np.nan
    bx[45:] = 20.0 + 60.0  # reaparece a 60 m tras 6 frames: 250 m/s
    out = ball.clean_v1(pista(n, bx, by, px, py, team))
    check("no interpola un hueco largo", np.isnan(out.bx[10:30]).all())
    check("no interpola si el hueco obliga a más de 40 m/s", np.isnan(out.bx[40:45]).all())

    # protección: antes del hueco el más cercano es H; al reaparecer, A a menos de 2 m
    px, py, team = jugadores(n, h=(50.0, 30.0), a=(52.0, 30.0))
    bx, by = np.full(n, 50.5), np.full(n, 30.0)
    bx[30:], by[30:] = 51.5, 30.0  # 0,5 m de A
    bx[25:30], by[25:30] = np.nan, np.nan
    out = ball.clean_v1(pista(n, bx, by, px, py, team))
    check("no interpola si reaparece junto a un rival", np.isnan(out.bx[25:30]).all())
    bx[30:] = 50.8  # sigue más cerca de H
    out = ball.clean_v1(pista(n, bx, by, px, py, team))
    check("sí interpola si reaparece con el mismo equipo", not np.isnan(out.bx[25:30]).any())
    px2, py2, _ = jugadores(n, h=(50.0, 30.0), a=(54.0, 30.0))
    bx[30:] = 51.6  # el más cercano es A, pero a 2,4 m
    out = ball.clean_v1(pista(n, bx, by, px2, py2, team))
    check("sí interpola si el rival está a más de 2 m", not np.isnan(out.bx[25:30]).any())

    px, py, team = jugadores(n)
    bx, by = np.full(n, 20.0), np.full(n, 20.0)
    bx[:3], by[:3] = np.nan, np.nan
    bx[-3:], by[-3:] = np.nan, np.nan
    entrada = pista(n, bx, by, px, py, team)
    out = ball.clean_v1(entrada)
    check("no extrapola en los bordes", np.isnan(out.bx[:3]).all() and np.isnan(out.bx[-3:]).all())
    copia = entrada.bx.copy()
    ball.clean_v1(entrada)
    check("no cambia el tracking de entrada", np.array_equal(entrada.bx, copia, equal_nan=True))
    check("devuelve el balón de solo lectura", not out.bx.flags.writeable and not out.by.flags.writeable)
    check("la de siempre (clean) devuelve el tracking tal cual", ball.clean(entrada) is entrada)


def correccion_paso2():
    print("Corrección del paso 2 (14/11): un pico no aísla al balón bueno de al lado")
    n = 60
    px, py, team = jugadores(n)
    # hueco largo + 2 frames buenos + pico de 1 frame + balón bueno
    bx, by = np.full(n, 20.0), np.full(n, 20.0)
    bx[:20], by[:20] = np.nan, np.nan
    bx[22] = 45.0
    out = ball.clean_v1(pista(n, bx, by, px, py, team))
    check("se queda con los 2 frames buenos tras el hueco", (out.bx[20:22] == 20.0).all())
    check("quita el pico y lo rellena", out.bx[22] == 20.0)
    check("solo cambia el frame del pico", int(np.sum(out.bx[20:] != np.asarray(bx)[20:])) == 1)
    # lo mismo en espejo: balón bueno + pico + 2 frames buenos + hueco largo
    bx, by = np.full(n, 20.0), np.full(n, 20.0)
    bx[40:], by[40:] = np.nan, np.nan
    bx[37] = 45.0
    out = ball.clean_v1(pista(n, bx, by, px, py, team))
    check("en espejo, se queda con los 2 frames buenos antes del hueco", (out.bx[38:40] == 20.0).all())
    check("en espejo, quita el pico y lo rellena", out.bx[37] == 20.0)


def evidencia():
    print("Evidencia de equipo")
    rng = np.random.RandomState(7)
    n, slots = 3000, 10
    px = rng.uniform(0, 105, (n, slots))
    py = rng.uniform(0, 68, (n, slots))
    px[rng.rand(n, slots) < 0.2] = np.nan
    bx, by = rng.uniform(0, 105, n), rng.uniform(0, 68, n)
    bx[rng.rand(n) < 0.3] = np.nan
    px[5] = np.nan  # un frame sin jugadores
    team = np.array([0] * 5 + [1] * 5, np.int8)
    trk = pista(n, bx, by, px, py, team)
    check("N1 da lo mismo que la versión 0", np.array_equal(candidates.nearest_team(trk), nearest_v0(trk)))
    score, _ = candidates.evidence(trk)
    check("por defecto es N1", np.array_equal(score[:, 0] > 0, nearest_v0(trk) == 0))
    for metodo in candidates.METHODS:
        s, a = candidates.evidence(trk, metodo)
        ok = s.shape == (n, 3) and a.shape == (n, 3) and a.all() and np.isfinite(s).all() and (s[:, 2] == 0).all()
        check("{}: (n, 3), finita, todo permitido y nada en D".format(metodo), ok)
        check("{}: sin balón no opina".format(metodo), (s[np.isnan(bx)] == 0).all())
        check("{}: determinista".format(metodo), np.array_equal(s, candidates.evidence(trk, metodo)[0]))
    try:
        candidates.evidence(trk, "N9")
        check("una versión mal escrita da error", False)
    except ValueError:
        check("una versión mal escrita da error", True)

    m = 40
    px, py, team = jugadores(m, h=(50.0, 30.0), a=(53.0, 30.0))
    bx, by = np.full(m, 50.0), np.full(m, 30.0)
    # 0: H a 1 m, A a 2 m → opina H; 1: H a 1,6 m → no; 3: H a 1,4, A a 1,6 → no; 4: lejos → no
    for k, x in {0: 51.0, 1: 51.6, 3: 51.4, 4: 60.0}.items():
        bx[k] = x
    trk = pista(m, bx, by, px, py, team)
    eq = candidates.margin_team(trk)
    check("N2 opina con el más cercano a 1,5 m y el rival 1 m más lejos", eq[0] == 0)
    check("N2 no opina con el más cercano a más de 1,5 m", eq[1] == -1 and eq[4] == -1)
    check("N2 no opina si el rival no está 1 m más lejos", eq[3] == -1)
    sola = pista(m, bx, by, px[:, :1], py[:, :1], team[:1])
    check("N2 opina si el otro equipo no tiene a nadie", candidates.margin_team(sola)[0] == 0)

    m = 60
    px, py, team = jugadores(m, h=(50.0, 30.0), a=(70.0, 30.0))
    bx, by = np.full(m, 60.0), np.full(m, 30.0)  # lejos de los dos: no hay racha
    bx[5:17] = 50.5  # 12 frames a 0,5 m de H: racha
    bx[25:36] = 50.5  # 11 frames: no
    bx[40:52] = 70.5  # 12 frames con A
    bx[45] = np.nan  # pero falta el balón en medio: dos rachas de 5 y 6
    eq = candidates.retention_team(pista(m, bx, by, px, py, team))
    check("Ret opina en una racha de 12 frames", (eq[5:17] == 0).all() and eq[4] == -1 and eq[17] == -1)
    check("Ret no opina en una racha de 11 frames", (eq[25:36] == -1).all())
    check("Ret corta la racha donde falta el balón", (eq[40:52] == -1).all())
    check("Ret no opina lejos de todos", (eq[:5] == -1).all())


def recuento():
    print("Recuento del partido (validation/partido/limpieza_balon.py) con un tracking inventado")
    n = 400
    bx = 10.0 + 0.05 * np.arange(n)  # balón lento por la banda, lejos de todos
    by = np.full(n, 30.0)
    bx[50] += 20.0  # pico de 1 frame: 2 pares, el paso 1 lo quita y el 3 lo rellena
    bx[110:130] = np.nan  # hueco largo + 2 frames buenos + pico: el caso de la corrección
    bx[132] += 20.0
    bx[150:156] += 25.0  # excursión de 6 frames: un par a la ida y otro a la vuelta; el paso 1 no la toca
    bx[230:240] = np.nan  # racha aislada de 1 frame (240) entre huecos: la quita el paso 2
    bx[241:260] = np.nan
    bx[270:275] = np.nan  # hueco de 5 frames: lo rellena el paso 3
    bx[300] += 15.0  # rampa que se queda: 3 pares; el paso 1 quita 300 y 301, y el hueco no se rellena
    bx[301] += 30.0
    bx[302:] += 45.0
    bx[350:] += 30.0  # salto que se queda: 1 par
    by[np.isnan(bx)] = np.nan
    px = np.array([[0.0, 105.0]] * n)  # un jugador en cada portería, a más de 2 m del balón siempre
    py = np.array([[0.0, 68.0]] * n)
    trk = pista(n, bx, by, px, py, [0, 1])
    with sin_ficheros():
        r = lb.recuento(trk)
        lineas = lb.para_imprimir(r)
    esperado = {
        "frames_evaluados": 400, "pares_a_mas_de_40_m_s": 10, "paso1_puntos_quitados": 4,
        "paso2_puntos_quitados": 1, "paso2_rachas_quitadas": 1, "paso3_huecos_cortos": 4,
        "paso3_huecos_rellenos": 3, "paso3_frames_rellenos": 7, "frames_cambiados": 10, "saltos_antes": 10,
        "saltos_despues": 4, "pares_a_mas_de_40_m_s_despues": 3,
    }
    for clave, valor in esperado.items():
        check("{} = {}".format(clave, valor), r[clave] == valor, "sale {}".format(r[clave]))
    clases = r["clases_de_los_pares"]
    check("picos: 4 pares en 2 tramos", clases["pico"] == {"pares": 4, "tramos": 2}, clases["pico"])
    check("excursiones: 2 pares en 2 tramos", clases["excursión"] == {"pares": 2, "tramos": 2}, clases["excursión"])
    check("saltos que se quedan: 4 pares en 2 tramos",
          clases["salto que se queda"] == {"pares": 4, "tramos": 2}, clases["salto que se queda"])
    check("las clases suman todos los pares", sum(c["pares"] for c in clases.values()) == r["pares_a_mas_de_40_m_s"])
    check("la salida suprime las celdas de 1 a 4 casos", any("< 5" in linea for linea in lineas))
    check("la salida no tiene números con decimales, salvo porcentajes con coma",
          not any(re.search(r"\d\.\d", linea) for linea in lineas))
    # Frontera entre tramos: un salto o una excursión que cruzan de un tramo a otro no cuentan como tales.
    m = 100
    fx, fy = 10.0 + 0.05 * np.arange(m), np.full(m, 30.0)
    fx[50:] += 30.0  # salto que se queda justo en la frontera 49/50
    fpx, fpy = np.array([[0.0, 105.0]] * m), np.array([[0.0, 68.0]] * m)
    uno = lb.recuento(pista(m, fx, fy, fpx, fpy, [0, 1]))
    dos = lb.recuento(pista(m, fx, fy, fpx, fpy, [0, 1], blocks=((0, 50), (50, m))))
    check("un salto en la frontera cuenta con un tramo", uno["pares_a_mas_de_40_m_s"] == 1 and uno["saltos_antes"] == 1)
    check("y no cuenta con dos tramos", dos["pares_a_mas_de_40_m_s"] == 0 and dos["saltos_antes"] == 0)
    ex = 10.0 + 0.05 * np.arange(m)
    ex[45:55] += 30.0  # excursión: se va en 44/45 y vuelve en 54/55
    uno = lb.recuento(pista(m, ex, fy, fpx, fpy, [0, 1]))["clases_de_los_pares"]
    dos = lb.recuento(pista(m, ex, fy, fpx, fpy, [0, 1], blocks=((0, 50), (50, m))))["clases_de_los_pares"]
    check("una excursión dentro de un tramo es excursión", uno["excursión"] == {"pares": 2, "tramos": 2}, uno)
    check("una excursión que cruza la frontera son dos saltos que se quedan",
          dos["excursión"]["tramos"] == 0 and dos["salto que se queda"] == {"pares": 2, "tramos": 2}, dos)


def main():
    with sin_ficheros():
        limpieza()
        correccion_paso2()
        evidencia()
        recuento()
    print("\nTODO BIEN" if not FALLOS else "\nFALLAN {}: {}".format(len(FALLOS), FALLOS))
    return 1 if FALLOS else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
