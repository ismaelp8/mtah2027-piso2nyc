"""Prueba el recuento de las fases del Smart Tagging con un partido inventado de resultado conocido.

    python validation/scripts/prueba_fases_smart_tagging.py

Sin datos del partido: el tracking, las fases y la entrega son inventados, y abrir un fichero durante el
recuento es un error (`sin_ficheros`). Lo puede ejecutar cualquiera, Claude incluido. Prueba
`validation/partido/fases_smart_tagging.py`: la tabla de códigos, los solapes, el acuerdo y su placebo, la
regla, las transiciones, el alcance, la lectura de la entrega y que la salida solo lleva agregados.
"""

import builtins
import contextlib
import io
import os
import sys
import tempfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import fases_smart_tagging as fst  # noqa: E402  (validation/partido/fases_smart_tagging.py)
from possession.tracking import A, D, H, X, Tracking  # noqa: E402

FALLOS = []
FPS = 25
N = 30000  # 20 minutos: los desplazamientos del placebo (±240 a ±480 s) caen dentro
SIN_BALON = 200  # los últimos frames de cada tramo, sin balón


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


@contextlib.contextmanager
def sin_ficheros():
    abrir, abrir_io = builtins.open, io.open

    def niega(*args, **kwargs):
        raise AssertionError("una prueba ha intentado abrir un fichero")

    builtins.open = io.open = niega
    try:
        yield
    finally:
        builtins.open, io.open = abrir, abrir_io


def evento(codigo, equipo, inicio, fin):
    return {"code": codigo, "start_frame": inicio, "end_frame": fin, "tags": {"Team": equipo}}


def partido():
    """(trk, eventos, etiquetas, tramos): tramos al azar de un equipo con el balón pegado a su jugador, y sin
    balón al final de cada tramo; fases que dicen la verdad; la entrega, igual que la verdad."""
    rng = np.random.default_rng(5)
    tramos, t, equipo = [], 0, H
    while t < N:
        largo = int(rng.integers(500, 1500))
        tramos.append((equipo, t, min(N, t + largo)))
        t += largo
        equipo = int(rng.integers(0, 2))
    px = np.tile([30.0, 70.0], (N, 1))
    py = np.tile([34.0, 34.0], (N, 1))
    bx, by = np.full(N, np.nan), np.full(N, np.nan)
    verdad = np.full(N, D, dtype=np.int8)
    eventos = []
    for equipo, a, b in tramos:
        bx[a:b - SIN_BALON], by[a:b - SIN_BALON] = px[0, equipo], 34.0
        verdad[a:b] = equipo
        # una fase de ataque del que tiene el balón o una de defensa del otro, alternando
        if len(eventos) % 2 == 0:
            eventos.append(evento("BUILD UP", "Barcelona" if equipo == H else "Atletic Club", a, b))
        else:
            eventos.append(evento("Defending in Middle Third", "Atletic Club" if equipo == H else "Barcelona", a, b))
    trk = Tracking(bx, by, px, py, np.array([0, 1], np.int8), (105.0, 68.0), ((0, N),), FPS)
    return trk, eventos, verdad.copy(), tramos


def tabla_y_regla():
    print("La tabla, los solapes, el acuerdo y la regla")
    trk, eventos, etiquetas, tramos = partido()
    equipo0, a0, b0 = tramos[0]
    # un solape que contradice: 100 frames del primer tramo con una fase del otro equipo
    extra = [evento("PROGRESSION", "Atletic Club" if equipo0 == H else "Barcelona", a0, a0 + 100),
             evento("PROGRESSION", "N/A", 0, N), evento("SET PIECES", "Barcelona", 0, N),
             evento("GOALS", "Barcelona", 0, N), evento("FOO", "Barcelona", 0, N)]
    with sin_ficheros():
        r = fst.recuento(trk, eventos + extra, etiquetas)
    check("las fases con Team N/A, SET PIECES, GOALS y los códigos fuera de la tabla no entran",
          r["fases_validas"] == len(eventos) + 1 and r["fases"] == len(eventos) + 5)
    check("la tabla separa ataque, defensa, fuera, sin tabla y N/A",
          r["tabla"]["build up"]["clase"] == "ataque" and r["tabla"]["defending in middle third"]["clase"] == "defensa"
          and r["tabla"]["set pieces"]["clase"] == "fuera" and r["tabla"]["foo"]["clase"] == "sin tabla"
          and r["tabla"]["progression"]["clase"] == "ataque" and r["tabla"]["progression"]["team_na"] == 1)
    check("cuenta los 100 frames solapados con equipos distintos", r["frames_solapados"] == 100, r["frames_solapados"])
    check("el control claro (mismo equipo a 1 m durante 1 s) ve todo el balón",
          r["frames_control"] == int(np.isfinite(trk.bx).sum()), r["frames_control"])
    check("con las fases de verdad y sin los solapados, el acuerdo es del 100 %",
          r["control_coinciden"] == r["control_con_fase"] > 0)
    tasas = [c / float(t) for t, c in r["placebo"] if t]
    check("el placebo desplazado acierta por casualidad, cerca del 50 %",
          len(tasas) == 6 and 0.3 < np.mean(tasas) < 0.7, ["{:.2f}".format(x) for x in tasas])
    entra, acuerdo_real, desacuerdo_placebo, porque = fst.veredicto(r)
    check("con eso, entra", entra and acuerdo_real == 1.0, porque)
    check("por código, la de defensa acierta como la de ataque (la tabla da la vuelta al equipo)",
          r["tabla"]["defending in middle third"]["coinciden"] == r["tabla"]["defending in middle third"]["control"] > 0)

    # con las fases al revés, el acuerdo es 0 y no entra
    al_reves = [dict(e, tags={"Team": "Barcelona" if e["tags"]["Team"] == "Atletic Club" else "Atletic Club"})
                for e in eventos]
    entra, acuerdo_real, _, porque = fst.veredicto(fst.recuento(trk, al_reves, etiquetas))
    check("con las fases al revés: acuerdo 0 y no entra", not entra and acuerdo_real == 0.0, porque)

    def r_de(acuerdo_real, placebo):
        return {"control_con_fase": 1000, "control_coinciden": int(round(1000 * acuerdo_real)),
                "placebo": [(1000, int(round(1000 * p))) for p in placebo]}

    check("80 % y placebo al 50 %: entra (desacuerdo 20 % ≤ 25 %)", fst.veredicto(r_de(0.80, [0.5] * 6))[0])
    check("79 %: no entra", not fst.veredicto(r_de(0.79, [0.5] * 6))[0])
    check("85 % con el placebo al 75 %: no entra (15 % > 12,5 %)", not fst.veredicto(r_de(0.85, [0.75] * 6))[0])
    check("90 % con el placebo al 75 %: entra (10 % ≤ 12,5 %)", fst.veredicto(r_de(0.90, [0.75] * 6))[0])
    check("sin frames de control con fase: no entra", not fst.veredicto(r_de(0.0, [0.5] * 6) | {"control_con_fase": 0})[0])
    return trk, eventos, etiquetas, tramos


def transiciones_y_alcance(trk, eventos, verdad, tramos):
    print("Transiciones y alcance")
    etiquetas = verdad.copy()
    cambios = [(e, a) for (e, a, _), (e0, _, _) in zip(tramos[1:], tramos[:-1]) if e != e0]
    nombre = {H: "Barcelona", A: "Atletic Club"}
    (e1, a1), (e2, a2), (e3, a3) = cambios[0], cambios[1], cambios[2]
    # 1: el inicio cae justo en nuestro cambio. 2: nuestro cambio llega 30 frames (1,2 s) después.
    etiquetas[a2:a2 + 30] = 1 - e2
    # 3: la etiqueta ya era ese equipo desde hace mucho (inicio en mitad de un tramo, sin cambio cerca).
    eq_m, am, bm = next((e, a, b) for e, a, b in tramos if b - a > 600 and a > 0)
    medio = (am + bm) // 2
    # 4: nuestra etiqueta es el otro equipo en todo el entorno (inicio en mitad de un tramo con el equipo contrario).
    # 5: el inicio cae en una racha de D de la entrega.
    eq_o, ao, bo = next((e, a, b) for e, a, b in tramos if b - a > 600 and a > medio)
    medio_o = (ao + bo) // 2
    eq_d, ad, bd = next((e, a, b) for e, a, b in tramos if b - a > 600 and a > medio_o)
    medio_d = (ad + bd) // 2
    etiquetas[medio_d - 100:medio_d + 100] = D
    trans = [evento("ATTACKING TRANSITION", nombre[e1], a1, a1 + 100),
             evento("ATTACKING TRANSITION", nombre[e2], a2, a2 + 100),
             evento("ATTACKING TRANSITION", nombre[eq_m], medio, medio + 100),
             evento("ATTACKING TRANSITION", nombre[1 - eq_o], medio_o, medio_o + 100),
             evento("ATTACKING TRANSITION", nombre[eq_d], medio_d, medio_d + 100),
             evento("ATTACKING TRANSITION", "N/A", a3, a3 + 100)]
    with sin_ficheros():
        r = fst.recuento(trk, eventos + trans, etiquetas)
    t = r["transiciones"]
    check("5 inicios (el de N/A no cuenta)", t["inicios"] == 5, t["inicios"])
    check("clases: 2 con cambio a ±2 s, 1 que ya era, 1 del otro equipo, 1 en D", t["clases"] == [2, 1, 1, 1],
          t["clases"])
    check("los dos cambios vienen del otro equipo", t["origenes"] == {"otro equipo": 2, "D": 0}, t["origenes"])
    check("desfases: 0 y +1,2 s", sorted(round(d, 2) for d in t["desfases"]) == [0.0, 1.2], t["desfases"])
    check("el placebo desplaza los inicios y los clasifica", len(r["transiciones_placebo"]) == 6 and
          all(p["inicios"] <= 5 for p in r["transiciones_placebo"]))
    sin_balon = int(np.sum(~np.isfinite(trk.bx) & (etiquetas != D)))
    check("alcance: los frames sin balón que no son D, todos con fase", r["sin_balon_vivo"] == sin_balon and
          r["sin_balon_con_fase"] == sin_balon, (r["sin_balon_vivo"], r["sin_balon_con_fase"]))
    check("y en ninguno nuestra etiqueta es del otro equipo (ahí la entrega es la verdad)",
          r["sin_balon_otro_equipo"] == 0, r["sin_balon_otro_equipo"])
    return r, [e["start_frame"] for e in trans]


def salida_y_ficheros(r, inicios):
    print("Salida y lectura de la entrega")
    lineas = fst.para_imprimir(r, sha="9539ce42" + "0" * 51 + "cc17a")
    texto = "\n".join(lineas)
    check("imprime las cinco secciones", all(s in texto for s in ("0. Controles", "1. La tabla", "2. Frames solapados",
                                                                  "3. La regla del plan", "4. Transiciones",
                                                                  "5. Alcance")))
    check("reconoce el sha256 de equipo_v3", "¿es equipo_v3? sí" in texto)
    check("los recuentos de 1 a 4 salen como «< 5»", "< 5" in texto and fst.celda(4) == "< 5" and fst.celda(5) == "5")
    check("un porcentaje de menos de 5 casos sale como «–»", fst.pct(3, 10) == "–" and fst.pct(5, 10) == "50,0 %")
    check("una salida corta, sin ningún frame concreto (ni los inicios de las transiciones)",
          len(lineas) < 60 and not any(str(i) in texto for i in inicios), "{} líneas".format(len(lineas)))
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, "entrega.csv")
        with open(ruta, "w", newline="") as f:
            f.write("frame,label\n" + "".join("{},{}\n".format(i, "HADX"[i % 4]) for i in range(8)))
        etiquetas, sha = fst.leer_entrega(ruta, 8)
        check("lee la entrega y su sha256", list(etiquetas) == [H, A, D, X] * 2 and len(sha) == 64)
        for malo, nombre in (("frame,label\n0,H\n2,A\n", "un frame que falta"), ("frame,label\n0,H\n1,Z\n", "una etiqueta rara"),
                             ("frame;label\n0,H\n1,A\n", "otra cabecera")):
            with open(ruta, "w", newline="") as f:
                f.write(malo)
            try:
                fst.leer_entrega(ruta, 2)
                check("{}: da error".format(nombre), False)
            except ValueError as e:
                check("{}: da error sin enseñar valores".format(nombre), "Z" not in str(e) and "2,A" not in str(e))
        with open(ruta, "w", newline="") as f:
            f.write("frame,label\n0,H\n1,A\n")
        try:
            fst.leer_entrega(ruta, 3)
            check("una entrega con filas de menos: da error", False)
        except ValueError:
            check("una entrega con filas de menos: da error", True)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = fst.main(["--entrega", ruta, "--data-dir", os.path.join(carpeta, "no-existe")])
        check("sin los datos del partido avisa y sale con 1", codigo == 1 and "No encuentro el ATD" in salida.getvalue())
        require = fst.games.require
        fst.games.require = lambda *a, **k: []
        try:
            salida = io.StringIO()
            with contextlib.redirect_stdout(salida), sin_ficheros():
                codigo = fst.main(["--entrega", os.path.join(carpeta, "no-hay.csv"),
                                   "--data-dir", os.path.join(carpeta, "no-existe")])
        finally:
            fst.games.require = require
        check("sin la entrega avisa cómo generarla y sale con 1, sin abrir nada",
              codigo == 1 and "possession.pipeline --name equipo_v3" in salida.getvalue())


def main():
    trk, eventos, etiquetas, tramos = tabla_y_regla()
    r, inicios = transiciones_y_alcance(trk, eventos, etiquetas, tramos)
    salida_y_ficheros(r, inicios)
    print()
    if FALLOS:
        print("FALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS)))
        return 1
    print("TODO BIEN")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
