"""Comprobaciones C6 a C11 de la bitácora sobre la caché de un partido de la Bundesliga.

- C6: fracción de balón activo por parte frente a `PlayingTime` / `TotalTime` de los metadatos.
- C7: tramos de balón inactivo frente a reinicios contados en el XML de eventos (sin kloppy).
- C8: unidades de la velocidad `S` del balón frente a la que sale de las posiciones.
- C9: origen de coordenadas (balón en el primer frame activo de cada parte).
- C10: escala de coordenadas (extremos del balón activo).
- C11: sentido de `BallPossession` en frames estables (balón lento con un solo jugador cerca).

Solo imprime agregados. Datos abiertos de otros partidos: lo puede ejecutar Claude.

Uso:
    python validation/experimento0/comprobaciones_lector.py J03WMX
"""

import argparse
import collections
import json
import os
import sys

import numpy as np
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfl_lector  # noqa: E402

FPS = 25
REINICIOS = ("ThrowIn", "FreeKick", "GoalKick", "CornerKick", "KickOff", "Penalty", "RefereeBall")

# Criterios fijados en la bitácora antes de medir.
C11_V_MAX = 2.0       # m/s
C11_R_UNO = 1.0       # m: un solo jugador a esta distancia o menos
C11_R_NADIE = 2.0     # m: ningún otro jugador a menos de esta distancia
C8_V_MIN = 3.0        # m/s: balón en movimiento para comparar unidades


def rachas(mascara):
    """Longitudes de las rachas de True (array booleano)."""
    m = np.concatenate(([False], mascara, [False])).astype(np.int8)
    d = np.diff(m)
    return np.flatnonzero(d == -1) - np.flatnonzero(d == 1)


def reinicios_en_eventos(ruta):
    """Reinicios por tipo en el XML de eventos, y si algún evento `Delete` anula alguno.

    Los `Delete` no llevan el id del evento que borran; se comprueba si su propio `EventId` coincide
    con el de algún otro evento del fichero.
    """
    raiz = etree.parse(ruta).getroot()
    eventos = raiz.findall("Event")
    cuenta = collections.Counter()
    for e in eventos:
        if len(e) and e[0].tag in REINICIOS:
            cuenta[e[0].tag] += 1
    deletes = [e for e in eventos if len(e) and e[0].tag == "Delete"]
    ids_otros = {e.get("EventId") for e in eventos if not (len(e) and e[0].tag == "Delete")}
    return dict(cuenta), {"eventos_delete": len(deletes),
                          "delete_con_EventId_de_otro_evento": sum(1 for e in deletes if e.get("EventId") in ids_otros),
                          "delete_con_atributo_EventId_propio": sum(1 for e in deletes if e[0].get("EventId"))}


def velocidad_central(x, y, k=2):
    """Velocidad (m/s) con diferencia centrada de ±k frames; NaN en los bordes."""
    v = np.full(len(x), np.nan)
    v[k:-k] = np.hypot(x[2 * k:] - x[:-2 * k], y[2 * k:] - y[:-2 * k]) / (2 * k / FPS)
    return v


def comprobar(partido, cache=None):
    datos = dfl_lector.cargar_cache(partido, cache)
    meta = datos["meta"]
    rutas = dfl_lector.rutas_partido(partido)
    salida = {"partido": partido, "local": meta["local"], "visitante": meta["visitante"], "partes": {}}
    c11_total = collections.Counter()
    for parte, d in datos["partes"].items():
        estado, poss = d["estado"], d["poss"]
        activo = estado == 1
        n_activos = int(activo.sum())
        neto_ms, total_ms = meta["neto_ms"][parte - 1], meta["total_ms"][parte - 1]
        r = {}
        # C6
        r["C6_fraccion_activa"] = round(n_activos / len(estado), 5)
        r["C6_fraccion_neta_oficial"] = round(neto_ms / total_ms, 5)
        r["C6_diferencia_puntos"] = round(100 * (r["C6_fraccion_activa"] - r["C6_fraccion_neta_oficial"]), 3)
        r["C6_frames_activos_menos_PlayingTime_entre_40"] = n_activos - neto_ms // 40
        # C7 (tramos D y parpadeos)
        d_rachas = rachas(estado == 0)
        a_rachas = rachas(activo)
        r["C7_tramos_inactivos"] = int(len(d_rachas))
        r["C7_tramos_inactivos_menos_de_1s"] = int(np.sum(d_rachas < FPS))
        r["C7_tramos_inactivos_de_2_frames_o_menos"] = int(np.sum(d_rachas <= 2))
        r["tramos_activos"] = int(len(a_rachas))
        r["tramos_activos_menos_de_1s"] = int(np.sum(a_rachas < FPS))
        r["empieza_inactivo"] = bool(estado[0] == 0)
        r["acaba_inactivo"] = bool(estado[-1] == 0)
        # C8 (unidades de S)
        dx, dy = np.diff(d["x"]), np.diff(d["y"])
        v_pos = np.hypot(dx, dy) * FPS
        s = d["s"][1:]
        mov = (v_pos > C8_V_MIN) & activo[1:] & ~np.isnan(s)
        cociente = s[mov] / v_pos[mov]
        r["C8_frames_en_movimiento"] = int(mov.sum())
        r["C8_S_entre_v_posiciones_p10_p50_p90"] = [round(float(q), 3) for q in np.percentile(cociente, [10, 50, 90])]
        # C9 (origen)
        primero = int(np.flatnonzero(activo)[0])
        r["C9_balon_en_primer_frame_activo_xy"] = [round(float(d["x"][primero]), 2), round(float(d["y"][primero]), 2)]
        r["C9_distancia_al_centro_m"] = round(float(np.hypot(d["x"][primero], d["y"][primero])), 2)
        r["C9_frames_inactivos_antes_del_primer_activo"] = primero
        # C10 (escala)
        xa, ya = np.abs(d["x"][activo]), np.abs(d["y"][activo])
        r["C10_max_abs_x_y"] = [round(float(xa.max()), 2), round(float(ya.max()), 2)]
        r["C10_p999_abs_x_y"] = [round(float(np.percentile(xa, 99.9)), 2), round(float(np.percentile(ya, 99.9)), 2)]
        # C11 (sentido del flag de posesión)
        v = velocidad_central(d["x"], d["y"])
        cerca = {}
        for equipo in ("local", "visitante"):
            px, py = d["equipos"][equipo]["x"], d["equipos"][equipo]["y"]
            dist = np.hypot(px - d["x"][:, None], py - d["y"][:, None])
            cerca[equipo] = dist
        todas = np.concatenate([cerca["local"], cerca["visitante"]], axis=1)
        es_local = np.concatenate([np.ones(cerca["local"].shape[1], bool), np.zeros(cerca["visitante"].shape[1], bool)])
        todas_nan = np.where(np.isnan(todas), np.inf, todas)
        orden = np.argsort(todas_nan, axis=1)
        d1 = np.take_along_axis(todas_nan, orden[:, :1], axis=1)[:, 0]
        d2 = np.take_along_axis(todas_nan, orden[:, 1:2], axis=1)[:, 0]
        quien_local = es_local[orden[:, 0]]
        estables = activo & (v < C11_V_MAX) & (d1 <= C11_R_UNO) & (d2 >= C11_R_NADIE)
        coincide = np.where(poss == 1, quien_local, ~quien_local)
        r["C11_frames_estables"] = int(estables.sum())
        r["C11_coincide_jugador_y_flag"] = round(float(coincide[estables].mean()), 4) if estables.any() else None
        for valor in (1, 2):
            sel = estables & (poss == valor)
            r["C11_coincide_con_flag_{}".format(valor)] = round(float(coincide[sel].mean()), 4) if sel.any() else None
            r["C11_frames_con_flag_{}".format(valor)] = int(sel.sum())
        c11_total["n"] += int(estables.sum())
        c11_total["coinciden"] += int(coincide[estables].sum())
        # Informativo: lo mismo con el balón muerto.
        muertos = (estado == 0) & (v < C11_V_MAX) & (d1 <= C11_R_UNO) & (d2 >= C11_R_NADIE)
        r["inactivo_estables"] = int(muertos.sum())
        r["inactivo_coincide_jugador_y_flag"] = round(float(coincide[muertos].mean()), 4) if muertos.any() else None
        salida["partes"][parte] = r
    salida["C11_total_frames"] = c11_total["n"]
    salida["C11_total_coincide"] = round(c11_total["coinciden"] / c11_total["n"], 4) if c11_total["n"] else None
    if rutas["eventos"]:
        rein, deletes = reinicios_en_eventos(rutas["eventos"])
        n_rein = sum(rein.values())
        n_tramos = sum(p["C7_tramos_inactivos"] for p in salida["partes"].values())
        salida["C7_reinicios_en_eventos"] = rein
        salida["C7_eventos_delete"] = deletes
        salida["C7_reinicios_total"] = n_rein
        salida["C7_tramos_inactivos_total"] = n_tramos
        salida["C7_cociente_tramos_entre_reinicios"] = round(n_tramos / n_rein, 3)
        # Ajuste por los bordes de cada parte: un tramo inactivo final no acaba en un reinicio, y un
        # saque inicial con el que empieza la parte no viene de un tramo inactivo. RefereeBall se
        # añadió a la lista de reinicios después de ver los tipos de evento, así que se da también sin él.
        finales = sum(1 for p in salida["partes"].values() if p["acaba_inactivo"])
        iniciales = sum(1 for p in salida["partes"].values() if not p["empieza_inactivo"])
        tramos_que_acaban_en_reinicio = n_tramos - finales
        reinicios_tras_tramo = n_rein - iniciales
        sin_balon_a_tierra = reinicios_tras_tramo - rein.get("RefereeBall", 0)
        salida["C7_ajustado"] = {
            "tramos_inactivos_que_no_son_el_final_de_una_parte": tramos_que_acaban_en_reinicio,
            "reinicios_que_no_abren_una_parte": reinicios_tras_tramo,
            "cociente": round(tramos_que_acaban_en_reinicio / reinicios_tras_tramo, 3),
            "reinicios_sin_RefereeBall": sin_balon_a_tierra,
            "cociente_sin_RefereeBall": round(tramos_que_acaban_en_reinicio / sin_balon_a_tierra, 3),
        }
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("partido")
    parser.add_argument("--cache", default=None)
    args = parser.parse_args()
    print(json.dumps(comprobar(args.partido, args.cache), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
