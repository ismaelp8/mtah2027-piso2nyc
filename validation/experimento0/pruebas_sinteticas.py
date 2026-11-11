"""Pruebas con datos sintéticos de respuesta conocida para los scripts del experimento 0.

Cada prueba fabrica unos datos pequeños en una carpeta temporal (fuera del repo), los pasa por el script
y comprueba que sale exactamente lo esperado. No lee ningún dato real.

Uso:
    python validation/experimento0/pruebas_sinteticas.py
"""

import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfl_lector  # noqa: E402

LOCAL, VISITANTE = "DFL-CLU-LOCAL", "DFL-CLU-VISIT"

METADATOS = """<?xml version="1.0" encoding="UTF-8"?>
<PutDataRequest><MatchInformation>
<General MatchId="DFL-MAT-PRUEBA" CompetitionName="Prueba" HomeTeamId="{l}" HomeTeamName="Local FC"
 GuestTeamId="{v}" GuestTeamName="Visitante CF"/>
<Environment PitchX="105.00" PitchY="68.00"/>
<Teams><Team TeamId="{v}" TeamName="Visitante CF" Role="guest"/><Team TeamId="{l}" TeamName="Local FC" Role="home"/></Teams>
<OtherGameInformation TotalTimeFirstHalf="400" TotalTimeSecondHalf="200" PlayingTimeFirstHalf="300" PlayingTimeSecondHalf="200"/>
</MatchInformation></PutDataRequest>
""".format(l=LOCAL, v=VISITANTE)


def _t(ms):
    s, m = divmod(ms, 1000)
    return "2023-01-01T13:00:{:02d}.{:03d}+00:00".format(s, m)


def _frame(n, ms, x, y, extra=""):
    return '<Frame N="{}" T="{}" X="{:.2f}" Y="{:.2f}" D="0.00" S="0.00" A="0.00" M="1"{}/>'.format(
        n, _t(ms), x, y, extra)


def xml_posiciones():
    """Parte 1: balón en N 10000-10009 sin el 10007, con BallStatus ausente en 10005.
    Parte 2: balón en N 100000-100004. Un local con un frame (10007) fuera de la rejilla del balón."""
    lineas = ['<?xml version="1.0" encoding="UTF-8"?>', "<PutDataRequest><Positions>"]
    lineas.append('<FrameSet GameSection="firstHalf" TeamId="referee" PersonId="REF1">')
    lineas += [_frame(10000 + i, 40 * i, 0.0, 0.0) for i in range(10)]
    lineas.append("</FrameSet>")
    lineas.append('<FrameSet GameSection="firstHalf" TeamId="BALL" PersonId="BALLID">')
    for i in range(10):
        if i == 7:
            continue
        estado = "" if i == 5 else ' BallStatus="{}"'.format(0 if i == 9 else 1)
        posesion = ' BallPossession="{}"'.format(1 if i < 4 else 2)
        lineas.append(_frame(10000 + i, 40 * i, float(i), 0.0, ' Z="0.11"' + posesion + estado))
    lineas.append("</FrameSet>")
    lineas.append('<FrameSet GameSection="firstHalf" TeamId="{}" PersonId="P_LOCAL">'.format(LOCAL))
    lineas += [_frame(10000 + i, 40 * i, float(i) + 0.5, 1.0) for i in range(10)]
    lineas.append("</FrameSet>")
    lineas.append('<FrameSet GameSection="firstHalf" TeamId="{}" PersonId="P_VISIT">'.format(VISITANTE))
    lineas += [_frame(10000 + i, 40 * i, -5.0, -5.0) for i in range(5)]
    lineas.append("</FrameSet>")
    lineas.append('<FrameSet GameSection="secondHalf" TeamId="BALL" PersonId="BALLID">')
    lineas += [_frame(100000 + i, 40 * i, 0.0, 0.0, ' Z="0.11" BallPossession="2" BallStatus="1"') for i in range(5)]
    lineas.append("</FrameSet>")
    lineas.append("</Positions></PutDataRequest>")
    return "\n".join(lineas)


def prueba_lector(carpeta):
    pos = os.path.join(carpeta, "pos.xml")
    met = os.path.join(carpeta, "meta.xml")
    with open(pos, "w", encoding="utf-8") as f:
        f.write(xml_posiciones())
    with open(met, "w", encoding="utf-8") as f:
        f.write(METADATOS)
    meta = dfl_lector.anclas_metadatos.leer(met)
    assert meta["local_id"] == LOCAL and meta["visitante_id"] == VISITANTE, meta
    assert meta["orden_teams"] == ["guest", "home"]
    conjuntos, secciones = dfl_lector.leer_posiciones(pos)
    assert secciones == {"firstHalf": 4, "secondHalf": 1}, secciones
    datos, res = dfl_lector.construir(conjuntos, meta)
    p1, r1, r2 = datos["partes"][1], res["partes"][1], res["partes"][2]
    assert r1["frames_balon"] == 9 and r2["frames_balon"] == 5
    assert r1["pasos_N_distintos_de_1"] == 1 and r1["huecos_N_frames_perdidos"] == 1
    assert r1["pasos_T_distintos_de_40ms"] == 1 and r1["pasos_T_valores_raros"] == {80: 1}
    assert r1["BallStatus"] == {"1": 7, "ausente": 1, "0": 1}, r1["BallStatus"]
    assert r1["BallPossession"] == {"1": 4, "2": 5}
    assert list(p1["estado"]) == [1, 1, 1, 1, 1, -1, 1, 1, 0]
    assert r1["frames_jugador_fuera_de_la_rejilla_del_balon"] == 1
    assert r1["jugadores_por_equipo"] == {"local": 1, "visitante": 1}
    assert r1["otros_framesets"] == {"referee": 1}
    # El local está en todos los frames del balón; el visitante solo en los cinco primeros.
    assert int(np.sum(~np.isnan(p1["equipos"]["local"]["x"]))) == 9
    assert int(np.sum(~np.isnan(p1["equipos"]["visitante"]["x"]))) == 5
    # El frame 10008 del balón está en la fila 7 y el local en x = 8,5.
    assert abs(float(p1["equipos"]["local"]["x"][7, 0]) - 8.5) < 1e-6
    assert list(np.diff(p1["t_ms"])) == [40, 40, 40, 40, 40, 40, 80, 40]
    # Ida y vuelta por la caché.
    ruta = os.path.join(carpeta, "cache", "PRUEBA.npz")
    dfl_lector.guardar_cache(datos, ruta)
    vuelta = dfl_lector.cargar_cache("PRUEBA", os.path.dirname(ruta))
    assert np.array_equal(vuelta["partes"][1]["estado"], p1["estado"])
    assert np.allclose(vuelta["partes"][1]["equipos"]["local"]["x"], p1["equipos"]["local"]["x"], equal_nan=True)
    print("lector: OK (9 + 5 frames, 1 hueco de N, 1 salto de 80 ms, 1 flag ausente, 1 frame fuera de rejilla)")


def prueba_etiquetas():
    """Flags conocidos: parte 1 = H20 A30 D30 A10 H30; parte 2 = D10 H25.
    Posesiones: H20, A30, A10, H30 y H25 (5); paradas: 2."""
    import etiquetas_dfl
    sys.path.insert(0, os.path.join(dfl_lector.os.path.dirname(dfl_lector.os.path.dirname(
        dfl_lector.os.path.abspath(dfl_lector.__file__))), "scripts"))
    import perfil_etiquetas
    import possession_metrics as pm
    e1 = np.array([1] * 50 + [0] * 30 + [1] * 40, dtype=np.int8)
    p1 = np.array([1] * 20 + [2] * 30 + [2] * 30 + [2] * 10 + [1] * 30, dtype=np.int8)
    e2 = np.array([0] * 10 + [1] * 25, dtype=np.int8)
    p2 = np.array([1] * 35, dtype=np.int8)
    datos = {"partes": {1: {"estado": e1, "poss": p1}, 2: {"estado": e2, "poss": p2}}}
    lab = etiquetas_dfl.etiquetas_partido(datos)
    assert len(lab) == 120 + 1 + 35 and lab[120] == "X"
    assert "".join(lab[:120]) == "H" * 20 + "A" * 30 + "D" * 30 + "A" * 10 + "H" * 30
    res = etiquetas_dfl.resumen(datos)
    assert res[1]["cambios_de_etiqueta"] == {"A>D": 1, "A>H": 1, "D>A": 1, "H>A": 1}, res[1]
    assert res[1]["rachas_de_menos_de_1s_por_etiqueta"] == {"A": 1, "H": 1}
    assert res[2]["reparto"] == {"D": 10, "H": 25}
    codigos = pm.label_codes(lab)
    perfil = perfil_etiquetas.perfil(codigos, fps=25)
    assert perfil["tramos"] == 2, perfil["tramos"]
    assert sorted(perfil["posesiones"].tolist()) == [10, 20, 25, 30, 30], perfil["posesiones"]
    assert sorted(perfil["paradas"].tolist()) == [10, 30]
    print("etiquetas y perfil: OK (5 posesiones, 2 paradas, 2 tramos)")
    # Medida R: A4 (borde) H10 (intercalada) A30 D5 H10 (junto a D) A40 H5 (borde).
    lab_r = np.array(list("A" * 4 + "H" * 10 + "A" * 30 + "D" * 5 + "H" * 10 + "A" * 40 + "H" * 5))
    r = etiquetas_dfl.medida_r(lab_r)
    assert r == {"posesiones": 6, "cortas": 4, "cortas_en_el_borde": 2, "cortas_intercaladas": 1,
                 "cortas_junto_a_D": 1}, r
    print("medida R: OK (6 posesiones, 1 intercalada, 1 junto a D, 2 en el borde)")


def _parte(bx, by, local, visitante, estado=None, poss=None):
    """Parte sintética en el formato de la caché. local/visitante: listas de (x, y) por frame (arrays n)."""
    n = len(bx)
    lx = np.stack([p[0] for p in local], axis=1).astype(np.float32)
    ly = np.stack([p[1] for p in local], axis=1).astype(np.float32)
    vx_ = np.stack([p[0] for p in visitante], axis=1).astype(np.float32)
    vy_ = np.stack([p[1] for p in visitante], axis=1).astype(np.float32)
    return {"x": np.asarray(bx, float), "y": np.asarray(by, float), "z": np.zeros(n),
            "estado": np.ones(n, np.int8) if estado is None else np.asarray(estado, np.int8),
            "poss": np.ones(n, np.int8) if poss is None else np.asarray(poss, np.int8),
            "equipos": {"local": {"x": lx, "y": ly}, "visitante": {"x": vx_, "y": vy_}}}


def prueba_detectores():
    """Toques y control con trayectorias de respuesta conocida y ruido de 1,5 cm."""
    import medidas_cambios as mc
    rng = np.random.default_rng(0)
    ruido = lambda n: rng.normal(0, 0.015, n)
    lejos = (np.full(200, 30.0), np.full(200, 20.0))

    # 1. Balón parado junto al local A (a 0,5 m) hasta el frame 60; en el 60 sale a 15 m/s.
    n = 200
    t = np.arange(n)
    bx = np.where(t < 60, 0.0, 15.0 * (t - 59) / 25.0) + ruido(n)
    by = np.zeros(n) + ruido(n)
    parte = _parte(bx, by, [(np.zeros(n), np.full(n, 0.5))], [lejos])
    prep = mc.preparar(parte)
    tt, eq, dv = mc.toques(prep, 3.0, 1.5)
    assert len(tt) == 1 and abs(int(tt[0]) - 60) <= 2 and int(eq[0]) == 0, (tt, eq, dv)
    segs = mc.controles(prep, 1.0, 12)
    assert len(segs) == 1 and segs[0][0] == 0 and 58 <= segs[0][1] <= 63 and segs[0][2] == 0, segs

    # 2. Balón que pasa de largo a 6 m/s junto al visitante B (a 0,3 m) sin tocarlo.
    bx = -20.0 + 6.0 * t / 25.0 + ruido(n)
    by = np.zeros(n) + ruido(n)
    parte = _parte(bx, by, [lejos], [(np.zeros(n), np.full(n, 0.3))])
    prep = mc.preparar(parte)
    tt, eq, _ = mc.toques(prep, 3.0, 1.5)
    paso = int(np.argmin(np.abs(bx)))
    assert not np.any(np.abs(tt - paso) <= 10), (tt, paso)
    assert mc.controles(prep, 1.0, 12) == []
    rets = mc.retenciones(prep, 1.0, 5)
    assert len(rets) == 1 and rets[0][2] == 1, rets  # la retención de 5 frames sí se deja engañar

    # 3. Desvío: a 12 m/s en +x; en el frame 100, junto al visitante C (0,4 m), gira 60°.
    bx = np.where(t <= 100, 12.0 * (t - 100) / 25.0, 12.0 * 0.5 * (t - 100) / 25.0) + ruido(n)
    by = np.where(t <= 100, 0.0, 12.0 * 0.866 * (t - 100) / 25.0) + ruido(n)
    parte = _parte(bx, by, [lejos], [(np.zeros(n), np.full(n, 0.4))])
    prep = mc.preparar(parte)
    tt, eq, _ = mc.toques(prep, 3.0, 1.5)
    assert len(tt) == 1 and abs(int(tt[0]) - 100) <= 2 and int(eq[0]) == 1, (tt, eq)
    assert mc.controles(prep, 1.0, 12) == []

    # 4. Ruido solo: balón parado y lejos de todos, sin ningún toque.
    parte = _parte(ruido(n), ruido(n), [lejos], [lejos])
    assert len(mc.toques(mc.preparar(parte), 3.0, 1.5)[0]) == 0
    print("detectores: OK (golpeo, balón que pasa de largo, desvío y ruido)")


def prueba_logica_cambios():
    """Grupos, momento del control, 2g y emparejamiento, con segmentos puestos a mano."""
    import medidas_cambios as mc
    n = 300
    d_equipo = np.full((2, n), 5.0)
    d_equipo[1, 95:100] = 0.8           # el visitante toca cerca del cambio del frame 100
    # Controles: locales en [0,30), [60,90), [160,190), [230,260); visitante en [170,200).
    segs = [(0, 30, 0, 0), (60, 90, 0, 0), (160, 190, 0, 1), (170, 200, 1, 5), (230, 260, 0, 1)]
    # Cambio a visitante en 100: su control empieza en 170, fuera de la ventana [75, 150] -> solo toque.
    # Cambio a visitante en 150: su control empieza en 170, dentro -> control, momento +20.
    # Cambio a visitante en 280: ningún control ni contacto del visitante en [255, 300) -> nada.
    f = np.array([100, 150, 280])
    nuevo = np.array([1, 1, 1])
    g = mc.grupos_cambio(f, nuevo, segs, d_equipo, 1.0, 25, 50)
    assert g == ["toque", "control", "nada"], g
    m = mc.momento_control(f, nuevo, segs, 50)
    assert m == [None, 20, None], m
    # 2g: toque del visitante en 40 entre controles locales [0,30) y [60,90); el flag cambia en 41-50.
    estado = np.ones(n, np.int8)
    poss = np.ones(n, np.int8)
    poss[41:51] = 2
    estado[200:205] = 0                 # un D entre el toque de 195 y el control de 230
    t_toq = np.array([40, 155, 195])
    eq_toq = np.array([1, 1, 1])
    res = mc.toques_sin_control(t_toq, eq_toq, [s for s in segs if s[2] == 0], estado, poss, np.zeros(n))
    assert [(c["t"], c["equipo"], c["cambia"], c["aereo"], c["desfase"], c["x_antes"], c["duracion"], c["hueco"])
            for c in res] == [(40, 1, True, False, 1, True, 10, 0), (155, 1, False, False, None, True, None, 60)], res
    assert mc.por_hueco(res + [dict(res[0], t=45, cambia=False)]) == [True, False]
    # placebo: un toque local en 40 entre los dos controles locales; el flag pasa al visitante en 41
    res = mc.toques_sin_control(np.array([40]), np.array([0]), [s for s in segs if s[2] == 0], estado, poss,
                                np.zeros(n), propio=True)
    assert [(c["t"], c["equipo"], c["cambia"], c["desfase"]) for c in res] == [(40, 0, True, 1)], res
    # Emparejamiento uno a uno: dos eventos y un solo fin cerca.
    desf, usados = mc.emparejar([100, 104], [101], 5)
    assert desf == [-1, None] and usados == {0}, (desf, usados)
    print("lógica de cambios: OK (grupos, momento, 2g, emparejamiento)")


def prueba_medir_parte():
    """`medir_parte` de principio a fin: pase con control, desvío a banda, saque de banda y control.

    Guion (frames): el local A conduce hasta el 200 y pasa al visitante B, que controla desde el ~248
    (flag al visitante en el 252); B golpea en el 350 hacia la banda; el local C lo desvía en el 412
    (flag al local en el 414, sin control); el balón sale por la banda (y > 34) en el 423 y se para;
    `D` del 430 al 549; saque del visitante en el 550 (flag al visitante) y control del visitante E.
    """
    import medidas_cambios as mc
    rng = np.random.default_rng(1)
    n = 700
    t = np.arange(n, dtype=float)
    bx, by = np.zeros(n), np.zeros(n)
    # 0–199 con A en (0, 0,5); 200–250 pase a 10 m/s hasta (20, 0); 250–349 parado junto a B.
    bx = np.where(t >= 200, np.minimum(10.0 * (t - 200) / 25.0, 20.0), 0.0)
    # 350–412 hacia la banda a 12 m/s; 412–426 desviado 60°; parado hasta el 549.
    sube = (t >= 350) & (t <= 412)
    by = np.where(sube, 12.0 * (t - 350) / 25.0, by)
    y412 = 12.0 * 62 / 25.0
    k = np.clip(t - 412, 0, 14)
    desv = t > 412
    bx = np.where(desv, 20.0 + 12.0 * 0.5 * k / 25.0, bx)
    by = np.where(desv, y412 + 12.0 * 0.866 * k / 25.0, by)
    x_o, y_o = 20.0 + 12.0 * 0.5 * 14 / 25.0, y412 + 12.0 * 0.866 * 14 / 25.0
    # saque en el 550: hacia −y a 8 m/s durante 30 frames, y parado junto a E.
    saque = t >= 550
    by = np.where(saque, y_o - 8.0 * np.clip(t - 549, 0, 30) / 25.0, by)
    bx = np.where(saque, x_o, bx)
    bx, by = bx + rng.normal(0, 0.01, n), by + rng.normal(0, 0.01, n)
    fijo = lambda x, y: (np.full(n, x), np.full(n, y))
    y_e = y_o - 8.0 * 30 / 25.0
    local = [fijo(0.0, 0.5), fijo(20.0, 30.2)]          # A, C
    visitante = [fijo(20.0, 0.5), fijo(x_o, y_e - 0.5)]  # B, E
    estado = np.ones(n, np.int8)
    estado[430:550] = 0
    poss = np.ones(n, np.int8)
    poss[252:414] = 2
    poss[550:] = 2
    parte = _parte(bx, by, local, visitante, estado, poss)
    r = mc.medir_parte(parte, dict(mc.PARAMETROS), rng, eventos_parte=[("ThrowIn", 552)])
    assert r["cambios"] == 2, r["cambios"]
    assert r["grupos"] == ["control", "toque"], r["grupos"]
    assert r["momento"][1] is None and -8 <= r["momento"][0] <= 0, r["momento"]
    assert r["en_el_aire"] == [False, False], r["en_el_aire"]
    assert r["toques_sin_control"] == [], r["toques_sin_control"]
    assert len(r["cortas_antes_de_D"]) == 1 and r["cortas_despues_de_D"] == [] and r["cortas_entre_dos_D"] == 0
    c = r["cortas_antes_de_D"][0]
    assert c == {"toque": True, "control": False, "fuera": True, "reanuda_el_otro": True}, c
    assert len(r["pasos_a_inactivo"]) == 1, r["pasos_a_inactivo"]
    p = r["pasos_a_inactivo"][0]
    assert p["fuera_en_inicio"] and p["tipo"] == "banda" and 3 <= p["desfase_cruce"] <= 10 and p["duracion"] == 120 and p["flag_constante"] and p["flag_igual_al_anterior"], p
    assert len(r["pasos_a_activo"]) == 1, r["pasos_a_activo"]
    q = r["pasos_a_activo"][0]
    assert q["mismo_equipo"] is False and -2 <= q["desfase_movimiento"] <= 2 and q["desfase_movimiento_activo"] == 0, q
    assert r["frames_d"] == 120 and r["frames_d_quietos"] == 0 and q["salto"] > 0.2, (r["frames_d_quietos"], q)
    # en el primer frame activo el balón ya avanzó 0,32 m y E está a 10,1 − 0,32 = 9,78 m (no hay sacador)
    assert abs(q["d_flag"] - 9.78) < 0.1, q
    r3 = mc.medir_parte(parte, dict(mc.PARAMETROS), np.random.default_rng(1), [("ThrowIn", 552, 1)])
    assert len(r3["reinicios_emparejados"]) == 1 and r3["reinicios_emparejados"][0]["equipo_coincide"] is True
    quietos, vel = mc.movimiento_jugadores(parte)
    assert quietos.all() and np.allclose(vel, 0.0)
    parte_mov = dict(parte, equipos={"local": {"x": parte["equipos"]["local"]["x"] + (np.arange(n) >= 100)[:, None] * 0.5,
                                               "y": parte["equipos"]["local"]["y"]},
                                     "visitante": parte["equipos"]["visitante"]})
    quietos, vel = mc.movimiento_jugadores(parte_mov)
    assert not quietos[99] and quietos[98] and quietos[100] and abs(vel[99] - 0.5 * 25 / 2) < 1e-6, vel[99]
    assert r["fuera_frames"] >= 100 and 0 < r["fuera_activos"] <= 12, (r["fuera_frames"], r["fuera_activos"])
    assert r["fuera_activo_frames_todos"] == r["fuera_activos"] and r["fuera_activo_episodios"] == [], r["fuera_activo_episodios"]
    assert r["cobertura"] == {"ThrowIn": [2]} and r["fines_d_emparejados"] == 1 and r["fines_d_sin_reinicio"] == []
    assert r["placebo_n"] > 0
    # con solo_activos sale lo mismo: aquí no hay nada junto al balón durante el D
    r2 = mc.medir_parte(parte, dict(mc.PARAMETROS, solo_activos=True), np.random.default_rng(1), [("ThrowIn", 552)])
    assert r2["grupos"] == r["grupos"] and r2["cortas_antes_de_D"] == r["cortas_antes_de_D"], r2["grupos"]

    # Balón congelado durante un D (frames 50–149) con un jugador a 0,5 m del 60 al 140: un control
    # falso si se miran todos los frames; ninguno con solo_activos.
    n = 200
    bx, by = np.zeros(n), np.zeros(n)
    jx = np.where((np.arange(n) >= 60) & (np.arange(n) < 140), 0.0, 30.0)
    estado = np.ones(n, np.int8)
    estado[50:150] = 0
    parte = _parte(bx, by, [(jx, np.full(n, 0.5))], [(np.full(n, 30.0), np.full(n, 20.0))], estado)
    assert mc.medir_parte(parte, dict(mc.PARAMETROS), np.random.default_rng(2))["controles"] == 1
    assert mc.medir_parte(parte, dict(mc.PARAMETROS, solo_activos=True), np.random.default_rng(2))["controles"] == 0
    print("medir_parte: OK (pase con control, desvío a banda, saque de banda; {} placebos; balón congelado en D)".format(
        r["placebo_n"]))


def main():
    with tempfile.TemporaryDirectory() as carpeta:
        prueba_lector(carpeta)
    prueba_etiquetas()
    prueba_detectores()
    prueba_logica_cambios()
    prueba_medir_parte()
    print("todas las pruebas: OK")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
