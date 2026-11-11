"""Parada 2 del experimento 0: 2a y 2b de los 7 partidos de la Bundesliga, con C1-C7 y C11.

Reúne, por partido, con los 7 juntos y por grupos (los dos de 1ª Bundesliga frente a los cinco del
Düsseldorf):
- C1-C5 (del resumen que guarda `dfl_lector.py`) y el total de frames frente a la tabla del artículo;
- C6, C7 y C11 (`comprobaciones_lector.py`);
- 2a: perfil de las etiquetas (`perfil_etiquetas.py`) y la medida R (`etiquetas_dfl.medida_r`);
- 2b: huella de retrasos, SOLO INFORMATIVA (D21).

Necesita las cachés de los 7 partidos (`dfl_lector.py <partido>`). Imprime tablas en markdown, solo con
agregados, y guarda el detalle en JSON junto a la caché, fuera del repo.

Uso:
    python validation/experimento0/parada2_resumen.py
"""

import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "scripts"))
import anclas_metadatos  # noqa: E402
import comprobaciones_lector  # noqa: E402
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
import perfil_etiquetas  # noqa: E402
import possession_metrics as pm  # noqa: E402

PARTIDOS = etiquetas_dfl.PARTIDOS
GRUPOS = {"1ª Bundesliga (J03WMX, J03WN1)": ("J03WMX", "J03WN1"),
          "Düsseldorf en casa (5 de 2. Bundesliga)": ("J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")}
TOTAL_ARTICULO = 1002644
FPS = 25


def perfil_de(lab):
    codigos = pm.label_codes(lab)
    p = perfil_etiquetas.perfil(codigos, FPS)
    pos, par = p["posesiones"], p["paradas"]
    q = lambda v, k: round(float(np.percentile(v, k)) / FPS, 2)
    return {
        "frames_evaluados": p["frames_evaluados"],
        "pct_H_A_D": [round(100 * p["reparto"][k], 2) for k in ("H", "A", "D")],
        "posesiones": int(len(pos)),
        "posesiones_por_minuto_vivo": round(len(pos) / p["minutos_vivos"], 2),
        "posesion_s_p10_p50_p90": [q(pos, 10), q(pos, 50), q(pos, 90)],
        "pct_posesiones_menos_de_1s_2s_3s": [round(100 * float(np.mean(pos < c * FPS)), 1) for c in (1, 2, 3)],
        "paradas": int(len(par)),
        "parada_s_p10_p50_p90": [q(par, 10), q(par, 50), q(par, 90)],
        "huella_1_3_8_25": [round(v, 4) for v in perfil_etiquetas.huella(codigos).values()],
        "hist_posesiones_s": np.histogram(pos / FPS, bins=[0, 0.5, 1, 2, 3, 5, 10, 20, 40, 1e9])[0].tolist(),
    }


def r_de(lab):
    """Medida R por parte (las partes van separadas por 'X')."""
    total = {}
    cortes = np.flatnonzero(lab == "X")
    trozos = np.split(lab, cortes)
    for trozo in trozos:
        trozo = trozo[trozo != "X"]
        if not len(trozo):
            continue
        for k, v in etiquetas_dfl.medida_r(trozo).items():
            total[k] = total.get(k, 0) + v
    total["R_pct"] = round(100.0 * total.get("cortas_intercaladas", 0) / total["posesiones"], 2)
    return total


def main():
    cache = dfl_lector.carpeta_cache()
    por_partido, etiquetas = {}, {}
    for partido in PARTIDOS:
        with open(os.path.join(cache, "{}_lector.json".format(partido)), encoding="utf-8") as f:
            lector = json.load(f)
        comp = comprobaciones_lector.comprobar(partido)
        datos = dfl_lector.cargar_cache(partido)
        meta = datos["meta"]
        lab = etiquetas_dfl.etiquetas_partido(datos)
        etiquetas[partido] = lab
        partes = lector["partes"]
        esperado = [t // 40 for t in meta["total_ms"]]
        por_partido[partido] = {
            "local_visitante": "{}–{}".format(meta["local"], meta["visitante"]),
            "C1_frames_por_parte": [partes["1"]["frames_balon"], partes["2"]["frames_balon"]],
            "C1_menos_TotalTime_40": [partes["1"]["frames_balon"] - esperado[0], partes["2"]["frames_balon"] - esperado[1]],
            "C2_total": lector["frames_balon_total"],
            "C2_menos_articulo": lector["frames_balon_total"] - anclas_metadatos.FRAMES_ARTICULO[partido],
            "C3_saltos_N_T_repetidos": [sum(partes[k]["pasos_N_distintos_de_1"] for k in partes),
                                        sum(partes[k]["pasos_T_distintos_de_40ms"] for k in partes),
                                        sum(partes[k]["N_repetidos"] for k in partes)],
            "C4_frames_jugador_fuera_de_rejilla": sum(partes[k]["frames_jugador_fuera_de_la_rejilla_del_balon"] for k in partes),
            "C5_valores": {"BallStatus": sorted(set(v for k in partes for v in partes[k]["BallStatus"])),
                           "BallPossession": sorted(set(v for k in partes for v in partes[k]["BallPossession"]))},
            "jugadores_por_frame_min_max": [min(partes[k]["jugadores_por_frame_min_mediana_max"][0] for k in partes),
                                            max(partes[k]["jugadores_por_frame_min_mediana_max"][2] for k in partes)],
            "C6_dif_puntos_por_parte": [comp["partes"][k]["C6_diferencia_puntos"] for k in (1, 2)],
            "C6_activos_menos_PlayingTime_40": [comp["partes"][k]["C6_frames_activos_menos_PlayingTime_entre_40"] for k in (1, 2)],
            "C7_tramos_reinicios_cociente": [comp["C7_tramos_inactivos_total"], comp["C7_reinicios_total"],
                                             comp["C7_cociente_tramos_entre_reinicios"]],
            "C7_ajustado": comp["C7_ajustado"],
            "C7_reinicios_por_tipo": comp["C7_reinicios_en_eventos"],
            "C7_delete": comp["C7_eventos_delete"],
            "empieza_inactivo_acaba_inactivo": [[comp["partes"][k]["empieza_inactivo"], comp["partes"][k]["acaba_inactivo"]] for k in (1, 2)],
            "tramos_inactivos_menos_de_1s": sum(comp["partes"][k]["C7_tramos_inactivos_menos_de_1s"] for k in (1, 2)),
            "C8_mediana_S_entre_v": [comp["partes"][k]["C8_S_entre_v_posiciones_p10_p50_p90"][1] for k in (1, 2)],
            "C9_distancia_centro_m": [comp["partes"][k]["C9_distancia_al_centro_m"] for k in (1, 2)],
            "C10_p999_abs_x_y": [comp["partes"][k]["C10_p999_abs_x_y"] for k in (1, 2)],
            "C11_frames_y_coincide": [comp["C11_total_frames"], comp["C11_total_coincide"]],
            "C11_por_flag": {k: [comp["partes"][k]["C11_coincide_con_flag_1"], comp["partes"][k]["C11_coincide_con_flag_2"]] for k in (1, 2)},
            "inactivo_coincide_jugador_y_flag": [comp["partes"][k]["inactivo_coincide_jugador_y_flag"] for k in (1, 2)],
            "lector_segundos_memoria_mb": [lector["segundos_total"], lector["memoria_pico_mb"]],
            "perfil": perfil_de(lab),
            "R": r_de(lab),
        }
    juntas = np.concatenate([np.concatenate([etiquetas[p], np.array(["X"])]) for p in PARTIDOS])
    resumen = {"partidos": por_partido,
               "total_frames": sum(v["C2_total"] for v in por_partido.values()),
               "total_frames_articulo": TOTAL_ARTICULO,
               "los_7": {"perfil": perfil_de(juntas), "R": r_de(juntas)},
               "grupos": {}}
    for nombre, lista in GRUPOS.items():
        g = np.concatenate([np.concatenate([etiquetas[p], np.array(["X"])]) for p in lista])
        resumen["grupos"][nombre] = {"perfil": perfil_de(g), "R": r_de(g)}
    with open(os.path.join(cache, "parada2.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=1)
    imprimir(resumen)


def imprimir(r):
    P = r["partidos"]
    print("Total de frames: {} (artículo: {}, diferencia {:+d})\n".format(
        r["total_frames"], r["total_frames_articulo"], r["total_frames"] - r["total_frames_articulo"]))
    print("| partido | C1 frames − TotalTime/40 | C2 − artículo | C3 saltos N / T / repetidos | C4 | C5 BallStatus / BallPossession | jugadores por frame | C6 diferencia (puntos) | C7 tramos / reinicios | C7 ajustado (sin balones a tierra) | C11 frames, coincide |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for p, v in P.items():
        a = v["C7_ajustado"]
        print("| {} | {:+d} / {:+d} | {:+d} | {} / {} / {} | {} | {} / {} | {}–{} | {} / {} | {} / {} = {} | {} / {} = {} ({}) | {} · {:.1%} |".format(
            p, v["C1_menos_TotalTime_40"][0], v["C1_menos_TotalTime_40"][1], v["C2_menos_articulo"],
            *v["C3_saltos_N_T_repetidos"], v["C4_frames_jugador_fuera_de_rejilla"],
            ",".join(v["C5_valores"]["BallStatus"]), ",".join(v["C5_valores"]["BallPossession"]),
            *v["jugadores_por_frame_min_max"], *v["C6_dif_puntos_por_parte"], *v["C7_tramos_reinicios_cociente"],
            a["tramos_inactivos_que_no_son_el_final_de_una_parte"], a["reinicios_que_no_abren_una_parte"],
            a["cociente"], a["cociente_sin_RefereeBall"], v["C11_frames_y_coincide"][0], v["C11_frames_y_coincide"][1]))
    print("\n| partido | H / A / D (%) | posesiones | por min vivo | posesión p10 / p50 / p90 (s) | < 1 s / < 2 s / < 3 s (%) | paradas | parada p10 / p50 / p90 (s) | cortas: intercaladas / junto a D / borde | R (%) | huella 1 / 3 / 8 / 25 (informativa) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    filas = [(p, v["perfil"], v["R"]) for p, v in P.items()] + [("los 7", r["los_7"]["perfil"], r["los_7"]["R"])] + \
            [(n, g["perfil"], g["R"]) for n, g in r["grupos"].items()]
    for nombre, f, R in filas:
        print("| {} | {} / {} / {} | {} | {} | {} / {} / {} | {} / {} / {} | {} | {} / {} / {} | {} / {} / {} | {} | {} / {} / {} / {} |".format(
            nombre, *f["pct_H_A_D"], f["posesiones"], f["posesiones_por_minuto_vivo"], *f["posesion_s_p10_p50_p90"],
            *f["pct_posesiones_menos_de_1s_2s_3s"], f["paradas"], *f["parada_s_p10_p50_p90"],
            R.get("cortas_intercaladas", 0), R.get("cortas_junto_a_D", 0), R.get("cortas_en_el_borde", 0), R["R_pct"],
            *f["huella_1_3_8_25"]))
    print("\nHistograma de duraciones de posesión (s): [0-0,5) [0,5-1) [1-2) [2-3) [3-5) [5-10) [10-20) [20-40) [40+)")
    for nombre, f, _ in filas:
        print("  {}: {}".format(nombre, f["hist_posesiones_s"]))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
