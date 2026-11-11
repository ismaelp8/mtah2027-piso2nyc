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


def main():
    with tempfile.TemporaryDirectory() as carpeta:
        prueba_lector(carpeta)
    prueba_etiquetas()
    print("todas las pruebas: OK")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
