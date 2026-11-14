"""Pruebas del instrumento y del lector del ATD con datos inventados. No lee nada del partido.

- El lector del ATD se prueba con un fichero sintético en una carpeta temporal, con rutas explícitas: nunca
  con las rutas por defecto de `games.py`.
- La GT pública sí se lee (es pública): se comprueba que el lector da los mismos recuentos que sus
  metadatos.

Uso:
    python validation/experimento2/pruebas_sinteticas.py
"""

import json
import os
import sys
import tempfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(AQUI, "..", "experimento0"))
sys.path.insert(0, os.path.join(RAIZ, "validation", "partido"))
sys.path.insert(0, AQUI)
import instrumento as ins  # noqa: E402
import medidas_cambios as mc  # noqa: E402
import recuento_ventana as rv  # noqa: E402

FPS = 25


def trayectoria(tramos, x0, y0):
    """Posiciones del balón por tramos de velocidad constante: [(frames, vx, vy)] en m/s."""
    xs, ys = [x0], [y0]
    for frames, vx, vy in tramos:
        for _ in range(frames):
            xs.append(xs[-1] + vx / FPS)
            ys.append(ys[-1] + vy / FPS)
    return np.array(xs), np.array(ys)


def jugada():
    """Conduce P0 (equipo 0), pasa, toca R1 (equipo 1) sin controlar y recibe y conduce P1 (equipo 0).

    Frames: conducción 0–100, pase 100–130, desvío de R1 en 130, vuelo 130–160, conducción de P1 desde 160.
    """
    s = 12.0 / np.sqrt(2)
    x, y = trayectoria([(100, 2.0, 0.0), (30, 12.0, 0.0), (30, s, s), (140, 2.0, 0.0)], 10.0, 30.0)
    n = len(x)
    p0x, p0y = x.copy(), y.copy()
    p0x[100:], p0y[100:] = x[100], y[100]
    p1x, p1y = np.full(n, x[160]), np.full(n, y[160])
    p1x[160:], p1y[160:] = x[160:], y[160:]
    r1x, r1y = np.full(n, x[130]), np.full(n, y[130])
    r2x, r2y = np.full(n, 90.0), np.full(n, 10.0)
    parte = {"x": x, "y": y, "z": np.zeros(n),
             "equipos": {"local": {"x": np.stack([p0x, p1x], 1), "y": np.stack([p0y, p1y], 1)},
                         "visitante": {"x": np.stack([r1x, r2x], 1), "y": np.stack([r1y, r2y], 1)}}}
    estado = np.ones(n, int)
    lectura1 = np.ones(n, int)
    lectura1[130:160] = 2  # el flag pasa a R1 en su toque y vuelve en la recepción de P1
    lectura3 = np.ones(n, int)  # sin control de R1 no cambia
    return parte, estado, lectura1, lectura3


def hojas(d):
    for v in d.values():
        if isinstance(v, dict):
            yield from hojas(v)
        else:
            yield v


def prueba_toques_sin_huecos():
    parte, estado, _, _ = jugada()
    prep = mc.preparar(parte)
    t0, e0, _ = mc.toques(prep, 3.0, 1.5)
    t1, e1, _ = ins.toques_por_tramos(prep, 3.0, 1.5, 10)
    assert np.array_equal(t0, t1) and np.array_equal(e0, e1), (t0, t1)
    assert set(e1.tolist()) == {0, 1}, e1
    print("ok  sin huecos, toques_por_tramos = medidas_cambios.toques:", t1.tolist(), e1.tolist())


def prueba_toques_con_hueco():
    parte, estado, _, _ = jugada()
    parte["x"], parte["y"] = parte["x"].copy(), parte["y"].copy()
    parte["x"][140:150] = np.nan
    parte["y"][140:150] = np.nan
    prep = mc.preparar(parte)
    t0, _, _ = mc.toques(prep, 3.0, 1.5)
    t1, e1, _ = ins.toques_por_tramos(prep, 3.0, 1.5, 10)
    sin_hueco, _, _ = ins.toques_por_tramos(mc.preparar(jugada()[0]), 3.0, 1.5, 10)
    assert len(t0) < len(sin_hueco), "medidas_cambios.toques debería perder toques tras un NaN"
    assert np.array_equal(t1, sin_hueco), (t1, sin_hueco)
    assert not np.any((t1 >= 137) & (t1 <= 153)), "no se inventan toques en los bordes del hueco"
    print("ok  con hueco: el original encuentra", len(t0), "toques; por tramos,", len(t1), "(los mismos que sin hueco)")


def prueba_fecha():
    t = np.array([100, 130, 160])
    eq = np.array([0, 1, 0])
    assert ins.fecha_cambio(130, 1, 0, t, eq) == ("en el toque", 130)
    assert ins.fecha_cambio(150, 1, 0, t, eq) == ("poco después", 130)
    assert ins.fecha_cambio(170, 1, 0, t[:2], eq[:2]) == ("más tarde", 130)
    # con un toque del equipo anterior en medio, el toque del equipo nuevo ya no cuenta
    assert ins.fecha_cambio(170, 1, 0, t, eq)[0] == "sin toque visible"
    assert ins.fecha_cambio(120, 1, 0, t, eq) == ("antes del toque", 130)
    assert ins.fecha_cambio(125, 1, 0, np.array([100]), np.array([0]))[0] == "sin toque visible"
    # el toque del equipo nuevo tiene que ser posterior al último del equipo anterior
    assert ins.fecha_cambio(165, 0, 1, t, eq) == ("en el toque", 160)
    ini = {0: np.array([160]), 1: np.array([140])}
    assert ins.control_cambio(130, 1, 130, ini) == "antes del control"
    assert ins.control_cambio(142, 1, 130, ini) == "en el inicio del control"
    assert ins.control_cambio(150, 1, 130, ini) == "6-15 frames después del inicio"
    assert ins.control_cambio(170, 1, 130, ini) == "más de 15 después del inicio"
    assert ins.control_cambio(130, 1, 130, {0: np.array([], int), 1: np.array([], int)}) == "sin control"
    print("ok  clases de fecha y de control")


def prueba_instrumento():
    parte, estado, l1, l3 = jugada()
    for hueco in (False, True):
        p = dict(parte)
        if hueco:
            p["x"], p["y"] = parte["x"].copy(), parte["y"].copy()
            p["x"][140:150] = np.nan
            p["y"][140:150] = np.nan
        prep = ins.preparar_en_juego(p, estado)
        r1 = ins.medir(prep, estado, l1)
        r3 = ins.medir(prep, estado, l3)
        assert r1["toques_rival_sin_control"]["huecos"] == 1 and r1["toques_rival_sin_control"]["huecos_que_cambian"] == 1, r1
        assert r3["toques_rival_sin_control"]["huecos"] == 1 and r3["toques_rival_sin_control"]["huecos_que_cambian"] == 0, r3
        assert r1["cambios_directos"] == 2 and r1["fecha_respecto_al_toque"]["en el toque"] == 2, r1
        assert r3["cambios_directos"] == 0, r3
        assert r1["cortas_intercaladas"]["solo toque"] == 1, r1
        assert r1["toques_sueltos_rival"] == {"episodios": 1, "cambian": 1}, r1
        assert r3["toques_sueltos_rival"] == {"episodios": 1, "cambian": 0}, r3
        assert r1["placebo_toques_sueltos_propios"] == {"episodios": 1, "cambian": 0}, r1
        for r in (r1, r3):
            assert all(v is None or isinstance(v, (int, float)) for v in hojas(r)), "solo agregados"
        t = ins.tasas(ins.sumar([r1, r1]))
        assert t["huecos_rival_que_cambian"] == 1.0 and t["en_el_toque_de_los_que_tienen_toque"] == 1.0, t
    print("ok  instrumento: lectura 1 cambia en el toque del rival; lectura 3 no; igual con un hueco de balón")


def prueba_degradacion():
    parte, estado, _, _ = jugada()
    activo = estado == 1
    rng = np.random.default_rng(1)
    m = ins.mascara_bloques(len(estado), activo, 0.41, 25, rng)
    assert 0.41 <= m[activo].mean() < 0.9, m.mean()
    m2 = ins.mascara_bloques(len(estado), activo, 0.41, 25, np.random.default_rng(1))
    assert np.array_equal(m, m2), "determinista con la misma semilla"
    prep = ins.preparar_en_juego(parte, estado)
    z = np.zeros(len(estado))
    z[50:53] = 3.0  # balón alto
    prep["d_equipo"] = prep["d_equipo"].copy()
    prep["d_equipo"][:, 200:203] = 2.0  # disputa: los dos equipos a 2 m
    md, pct = ins.mascara_dirigida(prep, z, activo, 0.41, np.random.default_rng(2))
    assert md[45:58].all() and md[195:208].all() and md[activo].mean() >= 0.41, "balón alto y disputa tapados ±5"
    solo, pct_solo = ins.mascara_dirigida(prep, z, activo, 0.0, np.random.default_rng(2))
    assert solo.sum() == 26 and abs(pct_solo - 100.0 * 26 / len(estado)) < 0.1, (solo.sum(), pct_solo)
    nada, pct_nada = ins.mascara_dirigida(prep, z, activo, 0.0, np.random.default_rng(2), fraccion=0.0)
    assert nada.sum() == 0 and pct_nada == 0.0, "con fracción 0 no se tapa ninguna disputa"
    medias = [ins.mascara_dirigida(prep, z, activo, 0.0, np.random.default_rng(s), fraccion=0.5)[0].sum()
              for s in range(40)]
    assert set(medias) <= {0, 13, 26} and 0 < np.mean(medias) < 26, "con fracción 0,5 se tapan episodios enteros"
    d = ins.degradar(parte, md, 0.1, np.random.default_rng(3))
    assert np.all(np.isnan(d["x"][md])) and np.all(np.isfinite(d["x"][~md]))
    assert d["equipos"]["local"]["x"].shape == parte["equipos"]["local"]["x"].shape
    print("ok  degradación: bloques al {:.0%}, dirigida al {:.0%} ({}% por disputas)".format(
        m[activo].mean(), md[activo].mean(), pct))


def prueba_lector_atd():
    with tempfile.TemporaryDirectory() as carpeta:
        meta = os.path.join(carpeta, "sintetico_atd.xml")
        raw = os.path.join(carpeta, "sintetico_atd.txt")
        with open(meta, "w", encoding="utf-8") as fh:
            fh.write('<Root><Teams><Team id="L"><Name>Local</Name></Team><Team id="V"><Name>Visitante</Name></Team>'
                     '</Teams><Players><Player teamId="L"/><Player teamId="V"/><Player teamId="L"/></Players></Root>')
        with open(raw, "w") as fh:
            for fid in range(1, 31):
                f = fid - 1
                bola = "NaN,NaN,NaN" if f == 7 else "{:.3f},{:.3f},1.0".format(0.01 * f, 0.5)
                tercero = "NaN,NaN,NaN" if f == 6 else ("" if f == 9 else "0.5,0.6,0.0")
                extra = ";0.9,0.9,0.0" if f == 10 else ""
                fh.write("{}:{};{};{}{}:{}\n".format(fid, "0.1,0.2,0.0", "0.3,0.4,0.0", tercero, extra, bola))
            fh.write("linea rara sin el formato\n")
        parte, calidad = rv.leer_atd(raw, meta, 5, 20, (100.0, 50.0))
        assert len(parte["x"]) == 16
        assert calidad == {"frames_que_faltan": 0, "lineas_con_otro_numero_de_slots": 1, "slots": 3}, calidad
        assert abs(parte["x"][0] - 5.0) < 1e-9 and abs(parte["y"][0] - 25.0) < 1e-9, "frame de vídeo = frame_id − 1"
        assert np.isnan(parte["x"][2]), "balón NaN en el frame 7"
        loc, vis = parte["equipos"]["local"], parte["equipos"]["visitante"]
        assert loc["x"].shape == (16, 2) and vis["x"].shape == (16, 1)
        assert abs(loc["x"][0, 0] - 10.0) < 1e-9 and abs(loc["x"][0, 1] - 50.0) < 1e-9
        assert abs(vis["y"][0, 0] - 20.0) < 1e-9
        assert np.isnan(loc["x"][1, 1]), "slot NaN en el frame 6"
        assert np.isnan(loc["x"][4, 1]), "grupo vacío en el frame 9: NaN, como el baseline"
        _, calidad = rv.leer_atd(raw, meta, 25, 35, (100.0, 50.0))
        assert calidad["frames_que_faltan"] == 6, calidad
    print("ok  lector del ATD (fichero sintético con rutas explícitas; tolera lo mismo que el baseline)")


def prueba_main_sintetica():
    """`main()` entero con un paquete de datos inventado en una carpeta temporal y `--data-dir` explícito."""
    import contextlib
    import io
    import games
    primero, ultimo = rv.ventana_publica()
    with tempfile.TemporaryDirectory() as carpeta:
        rutas = games.asset_paths(data_dir=carpeta)
        for k in ("atd_meta", "atd_raw"):
            assert os.path.commonpath([os.path.abspath(rutas[k]), os.path.abspath(carpeta)]) == \
                os.path.abspath(carpeta), "las rutas tienen que estar en la carpeta temporal"
        os.makedirs(os.path.dirname(rutas["atd_raw"]))
        with open(rutas["atd_meta"], "w", encoding="utf-8") as fh:
            fh.write('<Root><Teams><Team id="L"><Name>L</Name></Team><Team id="V"><Name>V</Name></Team></Teams>'
                     '<Players><Player teamId="L"/><Player teamId="V"/><Player teamId="L"/><Player teamId="V"/>'
                     '</Players></Root>')
        rng = np.random.default_rng(5)
        with open(rutas["atd_raw"], "w") as fh:
            for fid in range(1, ultimo + rv.MARGEN + 100):
                a = fid / 200.0
                bx, by = 0.5 + 0.3 * np.cos(a), 0.5 + 0.3 * np.sin(a)
                bola = "NaN,NaN,NaN" if rng.random() < 0.3 else "{:.4f},{:.4f},5.0".format(bx, by)
                slots = ";".join("{:.4f},{:.4f},1.0".format(bx + 0.01 * j, by) for j in range(4))
                fh.write("{}:{}:{}\n".format(fid, slots, bola))
        texto = io.StringIO()
        with contextlib.redirect_stdout(texto):
            rv.main(["--data-dir", carpeta])
    salida = json.loads(texto.getvalue())
    assert salida["frames_de_la_ventana"] == ultimo - primero + 1
    assert salida["calidad_del_atd"]["frames_que_faltan"] == 0
    assert set(salida["variantes"]) == {"base", "ampliada"}
    assert all(v is None or isinstance(v, (int, float)) for v in hojas(salida["variantes"]["base"]["recuentos"]))
    print("ok  main() de recuento_ventana.py con un paquete sintético (--data-dir en una carpeta temporal)")


def prueba_gt_publica():
    primero, ultimo = rv.ventana_publica()
    estado, poss = rv.leer_gt(primero - rv.MARGEN, ultimo + rv.MARGEN)
    ruta = os.path.join(RAIZ, "evaluation", "gt", "BAR-ATH_possession_gt_public_meta.json")
    with open(ruta, encoding="utf-8") as fh:
        cuentas = json.load(fh)["label_counts_in_window"]
    assert int(np.sum(poss == 1)) == cuentas["H"] and int(np.sum(poss == 2)) == cuentas["A"]
    assert int(np.sum(estado[rv.MARGEN:-rv.MARGEN] == 0)) == cuentas["D"]
    assert not np.any(estado[:rv.MARGEN]) and not np.any(estado[-rv.MARGEN:]), "el margen no tiene etiquetas"
    f, _, _ = mc.cambios(estado, poss)
    print("ok  GT pública: recuentos iguales a sus metadatos;", len(f), "cambios directos H↔A")


def prueba_ventana_sintetica():
    parte, estado, l1, _ = jugada()
    salida = rv.medir_ventana(parte, estado, l1)
    assert set(salida) == {"base", "ampliada"}
    assert salida["base"]["tasas"]["huecos_rival_que_cambian"] == 1.0
    print("ok  medir_ventana con una jugada sintética")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    prueba_toques_sin_huecos()
    prueba_toques_con_hueco()
    prueba_fecha()
    prueba_instrumento()
    prueba_degradacion()
    prueba_lector_atd()
    prueba_gt_publica()
    prueba_ventana_sintetica()
    prueba_main_sintetica()
    print("todas las pruebas pasan")
