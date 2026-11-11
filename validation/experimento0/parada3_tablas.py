"""Tablas en markdown de la parada 3, a partir de `parada3.json` (lo escribe `parada3.py`).

Solo agregados, con coma decimal, para pegarlas en la bitácora y en el fichero de resultados sin
copiar cifras a mano.

Uso:
    python validation/experimento0/parada3_tablas.py > tablas.md
"""

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import dfl_lector  # noqa: E402

CRITERIOS = ("1a", "1b", "2b", "2c", "3a", "2g", "2b retención", "2c retención")


def f(x, dec=1):
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "sí" if x else "no"
    if isinstance(x, (list, tuple)):
        return " / ".join(f(v, dec) for v in x)
    if isinstance(x, int):
        return "{:,}".format(x).replace(",", ".")
    texto = ("{:." + str(dec) + "f}").format(x)
    if texto.lstrip("-").strip("0.") == "":
        texto = texto.lstrip("-")  # sin "-0"
    return texto.replace(".", ",")


def s_(lista):
    """Frames a segundos."""
    return None if lista is None else [v / 25.0 for v in lista]


def tabla(cab, filas):
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    out += ["| " + " | ".join(str(c) for c in fila) + " |" for fila in filas]
    return "\n".join(out)


def filas_partidos(P):
    return list(P["por_partido"].items()) + list(P["grupos"].items()) + [("los 7", P["los_7"])]


def main():
    j = json.load(open(os.path.join(dfl_lector.carpeta_cache(), "parada3.json"), encoding="utf-8"))
    V = j["variantes"]
    print("Tiempo total: {} s; memoria pico: {} MB.\n".format(f(j["segundos_total"]), j["memoria_pico_mb"]))

    for var in ("original", "solo_en_juego"):
        P = V[var]["principal"]
        print("### Veredictos, variante `{}`\n".format(var))
        print(tabla(["partido"] + list(CRITERIOS),
                    [[p] + [s["veredictos"][c] for c in CRITERIOS] for p, s in filas_partidos(P)]))
        print()
        print(tabla(["criterio", "cumple / al controlar", "entre medias", "no cumple / otro momento",
                     "con los 7 juntos", "aguanta la sensibilidad", "variaciones que lo cambian"],
                    [[c, sum(v for k, v in P["veredictos_por_partido"][c].items() if k in ("cumple", "al controlar")),
                      P["veredictos_por_partido"][c].get("entre medias", 0),
                      sum(v for k, v in P["veredictos_por_partido"][c].items()
                          if k not in ("cumple", "al controlar", "entre medias")),
                      P["los_7"]["veredictos"][c], f(V[var]["estabilidad"][c]["aguanta"]),
                      "; ".join("{} → {}".format(n, v) for n, v in V[var]["estabilidad"][c]["variaciones_que_lo_cambian"].items()) or "—"]
                     for c in CRITERIOS]))
        print()

    P = V["original"]["principal"]
    Pj = V["solo_en_juego"]["principal"]
    print("### 2b y 2c por partido (variante original; entre paréntesis, solo en juego)\n")
    filas = []
    for (p, s), (_, sj) in zip(filas_partidos(P), filas_partidos(Pj)):
        g = s["grupos_pct"]
        norm = (g["control"] - s["placebo_control_otro_pct"]) / (s["placebo_control_flag_pct"] - s["placebo_control_otro_pct"]) * 100
        filas.append([p, f(s["cambios"]), f(s["cambios_por_minuto"], 2),
                      "{} ({})".format(f(g["control"]), f(sj["grupos_pct"]["control"])), f(g["toque"]), f(g["nada"]),
                      f([s["placebo_control_otro_pct"], s["placebo_control_flag_pct"]]), f(norm, 0),
                      "{} ({})".format(f(s["retencion_pct"]), f(sj["retencion_pct"])),
                      f([s["placebo_retencion_otro_pct"], s["placebo_retencion_flag_pct"]]),
                      f(s["momento"]["p10_p50_p90"], 0), f(s["momento"]["sin_control_pct"]),
                      f(s["momento"]["dentro_3_8_25_pct"]), f(s["momento_retencion"]["p10_p50_p90"], 0)])
    print(tabla(["partido", "cambios", "por min vivo", "control %", "solo toque %", "nada %",
                 "placebo control: otro / flag %", "control normalizado %", "retención 5 frames %",
                 "placebo retención: otro / flag %", "momento del control p10 / p50 / p90 (frames)",
                 "sin control en ±2 s %", "a ±3 / ±8 / ±25 frames %", "momento de la retención p10 / p50 / p90"], filas))
    print()
    h = P["los_7"]["momento"]["histograma"]
    print("Histograma del momento del control, los 7 (frames, control − cambio): " +
          "; ".join("[{}, {}): {}".format(a, b, c) for a, b, c in zip(h["bordes"][:-1], h["bordes"][1:], h["cuentas"])) + "\n")

    print("### 2c, lo que pide `PASOS.md` (variante original)\n")
    filas = []
    for p, s in filas_partidos(P):
        filas.append([p, f(s["d_nuevo_p10_p50_p90"], 2), f(s["d_viejo_p10_p50_p90"], 2),
                      f(s["desfase_toque_encontrado_pct"]), f(s["desfase_toque_p10_p50_p90"], 0),
                      f(s["placebo_toque_encontrado_pct"]), f(s["nuevo_cerca_1s_pct"]),
                      f([s["placebo_cerca_otro_pct"], s["placebo_cerca_flag_pct"]]), f(s["aire_pct"])])
    print(tabla(["partido", "distancia equipo nuevo p10 / p50 / p90 (m)", "distancia equipo antiguo (m)",
                 "con toque del nuevo en ±2 s %", "desfase toque − cambio p10 / p50 / p90 (frames)",
                 "placebo: toque del otro en ±2 s %", "nuevo a ≤ 1,5 m en ±1 s %",
                 "placebo: otro / flag a ≤ 1,5 m %", "3a: cambio en el aire %"], filas))
    print()

    print("### 2g por partido (variante original; entre paréntesis, solo en juego)\n")
    filas = []
    for (p, s), (_, sj) in zip(filas_partidos(P), filas_partidos(Pj)):
        filas.append([p, "{} ({})".format(f(s["toques_sin_control"]), f(sj["toques_sin_control"])),
                      "{} ({})".format(f(s["toques_sin_control_cambia_pct"]), f(sj["toques_sin_control_cambia_pct"])),
                      f(s["huecos_2g"]), f(s["huecos_2g_cambia_pct"]),
                      f(s["toques_sin_control_x_antes_pct"]), f(s["toques_sin_control_x_antes_y_cambia_pct"]),
                      f(s["toques_sin_control_x_antes_cambia_en_2_pct"]),
                      f(s["toques_sin_control_desfase_0_2_5_pct"]),
                      f(s_(s["toques_sin_control_duracion_p10_p50_p90"]), 2), f(s["toques_sin_control_duracion_menos_1s_pct"]),
                      "{} · {}".format(f(s["aereos_sin_control"]), f(s["aereos_sin_control_cambia_pct"])),
                      "{} · {}".format(f(s["placebo_2g_huecos"]), f(s["placebo_2g_huecos_cambia_pct"]))])
    print(tabla(["partido", "toques del rival sin control", "el flag pasa al rival %", "huecos", "huecos con cambio %",
                 "flag del equipo de los controles 3 frames antes %", "… y luego pasa al rival %",
                 "de esos, cambia en ≤ 2 frames %", "cambia a 0 / ≤ 2 / ≤ 5 frames %",
                 "racha del rival p10 / p50 / p90 (s)", "racha < 1 s %", "aéreos · cambia %",
                 "placebo (toques propios): huecos · cambia %"], filas))
    print()

    print("### 1a, cobertura de reinicios (los 7)\n")
    l7 = P["los_7"]
    sens = V["original"]["sensibilidad"]
    cob = l7["cobertura"]
    tipos = sorted(cob["n"], key=lambda t: -cob["n"][t])
    print(tabla(["tipo", "reinicios", "con fin de D a ±5 s %", "±3 s %", "±2 s %", "desfase evento − fin de D p10 / p50 / p90 (s)"],
                [[t, f(cob["n"][t]), f(cob["pct"][t]), f(sens["cobertura ±3 s"]["cobertura_pct"].get(t)),
                  f(sens["cobertura ±2 s"]["cobertura_pct"].get(t)), f(cob["desfase_s_p10_p50_p90"][t], 2)] for t in tipos]))
    print()
    print("Placebo (instantes al azar, ±5 s): {} %. Fines de `D` emparejados con un reinicio: {} % de {}; "
          "sin reinicio: {} (evento más cercano: {}).\n".format(
              f(cob["placebo_pct"]), f(cob["fines_d_emparejados_pct"]), f(cob["fines_d"]), f(cob["fines_d_sin_reinicio"]),
              ", ".join("{} {}".format(k, v) for k, v in sorted(cob["sin_reinicio_evento_cercano"].items(), key=lambda kv: -kv[1]))))
    print(tabla(["partido", "saque de banda %", "de puerta %", "córner %", "falta %", "fines de D emparejados %",
                 "saque inicial − primer frame activo, 1ª / 2ª parte (s)"],
                [[p, f(s["cobertura"]["pct"].get("ThrowIn")), f(s["cobertura"]["pct"].get("GoalKick")),
                  f(s["cobertura"]["pct"].get("CornerKick")), f(s["cobertura"]["pct"].get("FreeKick")),
                  f(s["cobertura"]["fines_d_emparejados_pct"]), f(j["anclaje_saque_s"].get(p), 2)]
                 for p, s in filas_partidos(P)]))
    print()

    print("### 1b, balón fuera con el flag activo\n")
    print(tabla(["partido", "frames en tramos fuera de ≥ 1 s (con D)", "de ellos activos % (criterio fijado)",
                 "frames activos fuera, cualquier duración", "por minuto vivo", "episodios activos fuera de ≥ 1 s",
                 "el más largo (s)"],
                [[p, f(s["fuera_frames"]), f(s["fuera_activo_pct"], 2), f(s["fuera_activo_frames_todos"]),
                  f(s["fuera_activo_frames_por_minuto"], 2), f(s["fuera_activo_episodios_1s"]), f(s["fuera_activo_episodio_max_s"], 2)]
                 for p, s in filas_partidos(P)]))
    print()

    print("### 2d, paso a inactivo (los 7)\n")
    ina = l7["inactivo"]
    print("- pasos a inactivo: {}; tipo aproximado: {};".format(
        f(ina["n"]), ", ".join("{} {}".format(k, f(v)) for k, v in ina["tipos"].items())))
    print("- balón fuera del campo en el inicio del `D`: {} %; cruzó una línea en los 3 s anteriores: {} %;".format(
        f(ina["fuera_en_inicio_pct"]), f(ina["con_cruce_3s_pct"])))
    print("- flag constante durante todo el `D`: {} %; igual al del último frame activo: {} %;".format(
        f(ina["flag_constante_pct"]), f(ina["flag_igual_al_anterior_pct"])))
    print("- distancia a la línea más cercana en el inicio del `D` (m, > 0 fuera): p10 / p50 / p90 = {};".format(
        f(ina["dist_linea_p10_p50_p90"], 2)))
    print("- frames desde que cruza la línea hasta el `D`, p10 / p50 / p90: " + "; ".join(
        "{} {}".format(t, f(v, 0)) for t, v in ina["desfase_cruce_por_tipo"].items() if v))
    print("- duración de la parada (s), p10 / p50 / p90: " + "; ".join(
        "{} {}".format(t, f(v)) for t, v in ina["duracion_s_por_tipo"].items()))
    print()
    print(tabla(["partido", "fuera en el inicio %", "banda / fondo / dentro"],
                [[p, f(s["inactivo"]["fuera_en_inicio_pct"]),
                  " / ".join(f(s["inactivo"]["tipos"].get(t, 0)) for t in ("banda", "fondo", "dentro"))]
                 for p, s in filas_partidos(P)]))
    print()

    print("### 2e, paso a activo\n")
    print(tabla(["partido", "medida fijada: desfase p10 / p50 / p90 (artefacto)", "medida nueva: desfase p10 / p50 / p90",
                 "se mueve a 0 / ≤ 5 / ≤ 25 frames %", "flag de la parada = equipo que reanuda %"],
                [[p, f(s["activo"]["desfase_movimiento_p10_p50_p90"], 0), f(s["activo"]["desfase_movimiento_activo_p10_p50_p90"], 0),
                  f(s["activo"]["movimiento_activo_en_0_5_25_frames_pct"]), f(s["activo"]["mismo_equipo_pct"])]
                 for p, s in filas_partidos(P)]))
    print()

    print("### Posesiones cortas junto a un `D` (los 7)\n")
    filas = []
    for var in ("original", "solo_en_juego"):
        c = V[var]["principal"]["los_7"]["cortas"]
        filas.append([var, f(c["antes_de_D"]), f(c["despues_de_D"]), f(c["entre_dos_D"]), f(c["antes_toque_pct"]),
                      f(c["antes_control_pct"]), f(c["antes_fuera_pct"]), f(c["antes_toque_sin_control_y_fuera_pct"]),
                      f(c["antes_reanuda_el_otro_pct"]), f(c["antes_toque_sin_control_y_fuera_reanuda_el_otro_pct"]),
                      f(c["despues_toque_pct"]), f(c["despues_control_pct"])])
    print(tabla(["variante", "antes de D", "después de D", "entre dos D", "antes: toque de Y %", "antes: control de Y %",
                 "antes: balón fuera %", "antes: toque sin control y fuera %", "antes: reanuda X % (todas)",
                 "antes: reanuda X % (toque sin control y fuera)", "después: toque de Y %", "después: control de Y %"], filas))
    print()

    print("### Contraste del detector de toques con los pases de los eventos\n")
    print(tabla(["partido", "pases (Play)", "por min vivo", "toques atribuidos por min", "pases con toque del mismo equipo a ±2 s %",
                 "instantes activos al azar con toque %"],
                [[p, f(s["calibracion"]["pases"]), f(s["calibracion"]["pases_por_minuto"], 2),
                  f(s["calibracion"]["toques_atribuidos_por_minuto"], 2), f(s["calibracion"]["pases_con_toque_pct"]),
                  f(s["calibracion"]["azar_con_toque_pct"])] for p, s in filas_partidos(P)]))
    print()

    print("### Histograma de duraciones en escala logarítmica (0,2 décadas)\n")
    H = j["histogramas_log"]
    b = H["los 7"]["bordes_s"]
    print("Bordes (s): " + " · ".join(f(x, 2) for x in b) + "\n")
    print(tabla(["partido", "recuentos", "máximos locales (s: n)", "dos modas (regla fijada)"],
                [[p, " ".join(str(c) for c in h["cuentas"]), "; ".join("{}: {}".format(f(x, 2), n) for x, n in h["picos"]),
                  f(h["dos_modas"])] for p, h in H.items()]))
    print()

    for var in ("original", "solo_en_juego"):
        print("### Sensibilidad, variante `{}` (los 7)\n".format(var))
        S = V[var]["sensibilidad"]
        filas = []
        for n, s in S.items():
            filas.append([n, f(s["control_pct"]), f([s["placebo_control_otro_pct"], s["placebo_control_flag_pct"]]),
                          f(s["retencion_pct"]), f(s["momento_p50"], 0), f(s["momento_retencion_p50"], 0), f(s["aire_pct"]),
                          f(s["toques_sin_control"]), f(s["toques_sin_control_cambia_pct"]), f(s["huecos_2g_cambia_pct"]),
                          f(s["placebo_2g_cambia_pct"]), f(s["fuera_activo_pct"], 2), f(s["fuera_activo_episodios_1s"]),
                          f([s["cobertura_pct"].get(t) for t in ("ThrowIn", "GoalKick", "CornerKick")])])
        print(tabla(["variación", "2b control %", "placebo otro / flag %", "retención %", "2c p50", "2c ret. p50",
                     "3a aire %", "2g toques", "2g cambia %", "2g huecos %", "placebo 2g %", "1b activo %",
                     "1b episodios", "1a banda / puerta / córner %"], filas))
        print()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
