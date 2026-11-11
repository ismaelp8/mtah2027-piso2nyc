"""Parada 3 del experimento 0: 2c, 2d, 2e y 2g en los 7 partidos de la Bundesliga, con sensibilidad.

Aplica `medidas_cambios.py` a las dos partes de cada partido con los parámetros principales fijados en la
bitácora y, después, variando cada parámetro de uno en uno. Da los veredictos fijados antes de medir,
partido a partido y con los 7 juntos, los placebos, el anclaje de la hora de los eventos y el contraste
del detector de toques con los pases de los eventos. Todo se da con dos variantes: la fijada antes de
medir ("original") y la que solo usa frames con el balón en juego ("solo_en_juego"), añadida al ver que
el balón se congela mientras el flag dice inactivo. Solo imprime agregados; el detalle se guarda en
JSON junto a la caché, fuera del repo.

Uso:
    python validation/experimento0/parada3.py               # principal y sensibilidad
    python validation/experimento0/parada3.py --solo-principal
"""

import argparse
import collections
import datetime
import json
import os
import sys
import time

import numpy as np
from lxml import etree

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import dfl_lector  # noqa: E402
import etiquetas_dfl  # noqa: E402
import medidas_cambios as mc  # noqa: E402

PARTIDOS = etiquetas_dfl.PARTIDOS
PRIMERA = ("J03WMX", "J03WN1")
FPS = 25
REINICIOS = ("ThrowIn", "GoalKick", "CornerKick", "FreeKick", "Penalty", "KickOff", "RefereeBall")
SEMILLA = 20261111
CRITERIOS = ("1a", "1b", "2b", "2c", "3a", "2g", "2b retención", "2c retención")

VARIACIONES = [
    ("radio 1,5 m", {"radio": 1.5}),
    ("retención 3", {"frames_retencion": 3}), ("retención 8", {"frames_retencion": 8}),
    ("retención 12", {"frames_retencion": 12}),
    ("control 8", {"frames_control": 8}), ("control 20", {"frames_control": 20}),
    ("ventana 2b ±1 s", {"ventana_antes": 25, "ventana_despues": 25}),
    ("ventana 2b ±2 s", {"ventana_antes": 50, "ventana_despues": 50}),
    ("momento ±1 s", {"ventana_momento": 25}),
    ("aire 1,5 m", {"radio_aire": 1.5}), ("aire 3 m", {"radio_aire": 3.0}),
    ("aire 3 m/s", {"velocidad_aire": 3.0}), ("aire 8 m/s", {"velocidad_aire": 8.0}),
    ("fuera 1,0 m", {"margen_fuera": 1.0}),
    ("cobertura ±2 s", {"ventana_cobertura": 50}), ("cobertura ±3 s", {"ventana_cobertura": 75}),
    ("toque 2 m/s", {"umbral_toque": 2.0}), ("toque 5 m/s", {"umbral_toque": 5.0}),
    ("placebo ±1 s", {"margen_placebo": 25}), ("placebo ±3 s", {"margen_placebo": 75}),
    ("reanudar ±1 s", {"ventana_reanudar": 25}),
]


# -- eventos -------------------------------------------------------------------------------------------

def _ms(texto):
    return int(round(datetime.datetime.fromisoformat(texto).timestamp() * 1000))


def leer_eventos(ruta, meta):
    """[(tipo, ms, equipo 0/1 o -1)] de todos los eventos con hora, sin los `Delete`."""
    raiz = etree.parse(ruta).getroot()
    salida = []
    for e in raiz.findall("Event"):
        if not len(e) or e.get("EventTime") is None or e[0].tag == "Delete":
            continue
        hijo = e[0]
        team = hijo.get("Team") or hijo.get("WinnerTeam")
        eq = 0 if team == meta["local_id"] else (1 if team == meta["visitante_id"] else -1)
        salida.append((hijo.tag, _ms(e.get("EventTime")), eq))
    return salida


def a_frame(t_ms, ms):
    """Frame de la parte cuya T es la más cercana a `ms`."""
    i = int(np.clip(np.searchsorted(t_ms, ms), 1, len(t_ms) - 1))
    return i if abs(t_ms[i] - ms) < abs(t_ms[i - 1] - ms) else i - 1


def reinicios_de_la_parte(eventos, t_ms):
    """[(tipo, frame, equipo)] de los reinicios de la parte (±10 s), sin el saque inicial que la abre."""
    salida = []
    for tipo, ms, eq in eventos:
        if tipo in REINICIOS and t_ms[0] - 10000 <= ms <= t_ms[-1] + 10000:
            fr = a_frame(t_ms, ms)
            if tipo == "KickOff" and fr <= 5 * FPS:
                continue  # el saque inicial que abre la parte no viene de un D
            salida.append((tipo, fr, eq))
    return salida


# -- carga (una vez) y medida -----------------------------------------------------------------------------

def cargar(partido):
    datos = dfl_lector.cargar_cache(partido)
    meta = datos["meta"]
    eventos = leer_eventos(dfl_lector.rutas_partido(partido)["eventos"], meta)
    partes = {}
    anclaje = []
    for k in (1, 2):
        p = datos["partes"][k]
        t_ms = np.asarray(p["t_ms"], np.int64)
        estado = np.asarray(p["estado"])
        # anclaje de la hora: saque inicial que abre la parte frente al primer frame activo
        primer_activo = int(np.flatnonzero(estado == 1)[0])
        saques = [ms for tipo, ms, _ in eventos if tipo == "KickOff" and abs(ms - t_ms[primer_activo]) <= 30000]
        anclaje.append(None if not saques else round((min(saques, key=lambda m: abs(m - t_ms[primer_activo]))
                                                      - t_ms[primer_activo]) / 1000.0, 2))
        quietos, vel = mc.movimiento_jugadores(p)
        en_d = estado[1:] != 1
        partes[k] = {"parte": {"estado": estado, "poss": np.asarray(p["poss"])}, "t_ms": t_ms,
                     "prep": mc.preparar(p), "reinicios": reinicios_de_la_parte(eventos, t_ms),
                     "jugadores": {"frames_d": int(en_d.sum()), "frames_d_quietos": int((quietos & en_d).sum()),
                                   "frames_activos_quietos": int((quietos & ~en_d).sum()),
                                   "vel_d": vel[en_d], "vel_activo": vel[~en_d]}}
    return {"meta": meta, "eventos": eventos, "partes": partes, "anclaje_saque_s": anclaje}


def resumen_jugadores(lista):
    """Jugadores en los frames D y activos de varias partes: si se congelan y a qué velocidad van."""
    fd = sum(j["frames_d"] for j in lista)
    vd = np.concatenate([j["vel_d"] for j in lista])
    va = np.concatenate([j["vel_activo"] for j in lista])
    return {"frames_d": fd, "d_todos_quietos_pct": round(100.0 * sum(j["frames_d_quietos"] for j in lista) / fd, 2),
            "activos_todos_quietos": sum(j["frames_activos_quietos"] for j in lista),
            "vel_media_d_p10_p50_p90": [round(float(x), 2) for x in np.nanpercentile(vd, [10, 50, 90])],
            "vel_media_activo_p10_p50_p90": [round(float(x), 2) for x in np.nanpercentile(va, [10, 50, 90])]}


def medir_partido(i, datos, prm):
    rng = np.random.default_rng(SEMILLA + i)
    rng_cal = np.random.default_rng(SEMILLA + 100 + i)
    campo = tuple(datos["meta"]["campo"])
    resultados, calib = [], collections.Counter()
    for k in (1, 2):
        d = datos["partes"][k]
        r = mc.medir_parte(d["parte"], prm, rng, d["reinicios"], prep=d["prep"], campo=campo)
        # contraste del detector de toques con los pases (Play) de los eventos, en ±2 s
        t_ms, estado = d["t_ms"], d["parte"]["estado"]
        tt, eq, _ = mc.toques(d["prep"], prm["umbral_toque"], prm["radio_toque"])
        if prm.get("solo_activos"):
            tt, eq = mc.toques_en_juego(tt, eq, estado)
        activos = np.flatnonzero(estado == 1)
        for tipo, ms, e_eq in datos["eventos"]:
            if tipo != "Play" or e_eq < 0 or not (t_ms[0] <= ms <= t_ms[-1]):
                continue
            fr = a_frame(t_ms, ms)
            calib["pases"] += 1
            calib["pases_con_toque_2s"] += int(np.any((np.abs(tt - fr) <= 50) & (eq == e_eq)))
            al_azar = int(activos[rng_cal.integers(0, len(activos))])
            calib["azar_con_toque_2s"] += int(np.any((np.abs(tt - al_azar) <= 50) & (eq == e_eq)))
        calib["toques_atribuidos"] += r["toques_atribuidos"]
        calib["toques"] += r["toques"]
        # evento más cercano (cualquier tipo) a cada fin de D que no se emparejó con un reinicio
        cerca = []
        for fr in r.get("fines_d_sin_reinicio", []):
            ms0 = t_ms[fr]
            cand = [(abs(m - ms0), tipo) for tipo, m, _ in datos["eventos"] if abs(m - ms0) <= 10000]
            cerca.append(min(cand)[1] if cand else "ninguno a 10 s")
        r["fines_d_sin_reinicio_evento_cercano"] = cerca
        resultados.append(r)
    return juntar(resultados), dict(calib)


def juntar(partes):
    """Une las listas y suma los recuentos de varias partes (o partidos)."""
    total = {}
    for r in partes:
        for k, v in r.items():
            if isinstance(v, list):
                total.setdefault(k, []).extend(v)
            elif isinstance(v, dict):
                dd = total.setdefault(k, {})
                for kk, vv in v.items():
                    dd.setdefault(kk, []).extend(vv)
            else:
                total[k] = total.get(k, 0) + v
    return total


# -- resúmenes y veredictos ---------------------------------------------------------------------------------

def pct(lista):
    lista = [x for x in lista if x is not None]
    return round(100.0 * sum(bool(x) for x in lista) / len(lista), 1) if lista else None


def q(lista, ks=(10, 50, 90)):
    lista = [x for x in lista if x is not None]
    return [round(float(np.percentile(lista, k)), 2) for k in ks] if lista else None


def veredicto(valor, cumple, no_cumple, mayor_es_mejor=True):
    if valor is None:
        return "sin datos"
    if mayor_es_mejor:
        return "cumple" if valor >= cumple else ("no cumple" if valor <= no_cumple else "entre medias")
    return "cumple" if valor <= cumple else ("no cumple" if valor >= no_cumple else "entre medias")


def veredicto_momento(m):
    if m is None:
        return "sin datos"
    return "al controlar" if -12 <= m <= 12 else ("antes de controlar" if m > 12 else "después de controlar")


def resumen_momento(mom, cambios):
    con = [m for m in mom if m is not None]
    bordes = [-50, -25, -12, -8, -3, 4, 9, 13, 26, 51]
    return {"sin_control_pct": round(100.0 * (len(mom) - len(con)) / cambios, 1) if cambios else None,
            "p10_p50_p90": q(con),
            "dentro_3_8_25_pct": [round(100.0 * float(np.mean(np.abs(con) <= w)), 1) for w in (3, 8, 25)] if con else None,
            "histograma": {"bordes": bordes, "cuentas": np.histogram(con, bins=bordes)[0].tolist()} if con else None}


def resumir(r, calib=None):
    s = {"cambios": r["cambios"], "minutos_vivos": round(r["minutos_vivos"], 1),
         "cambios_por_minuto": round(r["cambios"] / r["minutos_vivos"], 2)}
    g = collections.Counter(r["grupos"])
    s["grupos_pct"] = {k: round(100.0 * g[k] / r["cambios"], 1) for k in ("control", "toque", "nada")}
    s["retencion_pct"] = pct(r["con_retencion"])
    s["placebo_n"] = r["placebo_n"]
    for k in ("control_otro", "control_flag", "retencion_otro", "retencion_flag", "cerca_otro", "cerca_flag"):
        s["placebo_" + k + "_pct"] = pct(r["placebo_" + k])
    s["momento"] = resumen_momento(r["momento"], r["cambios"])
    s["momento_retencion"] = resumen_momento(r["momento_retencion"], r["cambios"])
    s["aire_pct"] = pct(r["en_el_aire"])
    tsc = r["toques_sin_control"]
    s["toques_sin_control"] = len(tsc)
    s["toques_sin_control_cambia_pct"] = pct([c["cambia"] for c in tsc])
    s["toques_sin_control_desfase_p10_p50_p90"] = q([c["desfase"] for c in tsc])
    s["toques_sin_control_desfase_0_2_5_pct"] = [pct([c["desfase"] is not None and c["desfase"] <= w for c in tsc])
                                                 for w in (0, 2, 5)]
    s["toques_sin_control_x_antes_pct"] = pct([c["x_antes"] for c in tsc])
    s["toques_sin_control_x_antes_y_cambia_pct"] = pct([c["x_antes"] and c["cambia"] for c in tsc])
    s["toques_sin_control_x_antes_cambia_en_2_pct"] = pct(
        [c["cambia"] and c["desfase"] <= 2 for c in tsc if c["x_antes"]])
    dur = [c["duracion"] for c in tsc if c["cambia"]]
    s["toques_sin_control_duracion_p10_p50_p90"] = q(dur)
    s["toques_sin_control_duracion_menos_1s_pct"] = pct([d < FPS for d in dur])
    s["huecos_2g"] = len(r["huecos_2g"])
    s["huecos_2g_cambia_pct"] = pct(r["huecos_2g"])
    s["aereos_sin_control"] = sum(1 for c in tsc if c["aereo"])
    s["aereos_sin_control_cambia_pct"] = pct([c["cambia"] for c in tsc if c["aereo"]])
    s["rasos_sin_control_cambia_pct"] = pct([c["cambia"] for c in tsc if not c["aereo"]])
    tsp = r["toques_propios_sin_control"]
    s["placebo_2g_toques_propios"] = len(tsp)
    s["placebo_2g_cambia_pct"] = pct([c["cambia"] for c in tsp])
    s["placebo_2g_huecos"] = len(r["huecos_2g_placebo"])
    s["placebo_2g_huecos_cambia_pct"] = pct(r["huecos_2g_placebo"])
    s["d_nuevo_p10_p50_p90"] = q(r["d_nuevo_en_cambio"])
    s["d_viejo_p10_p50_p90"] = q(r["d_viejo_en_cambio"])
    s["nuevo_cerca_1s_pct"] = pct(r["nuevo_cerca_1s"])
    s["desfase_toque_encontrado_pct"] = pct([d is not None for d in r["desfase_toque"]])
    s["desfase_toque_p10_p50_p90"] = q(r["desfase_toque"])
    s["placebo_toque_encontrado_pct"] = pct([d is not None for d in r["placebo_desfase_toque_otro"]])
    s["placebo_desfase_toque_p10_p50_p90"] = q(r["placebo_desfase_toque_otro"])
    s["fuera_frames"] = r["fuera_frames"]
    s["fuera_activo_pct"] = round(100.0 * r["fuera_activos"] / r["fuera_frames"], 2) if r["fuera_frames"] else None
    s["fuera_activo_frames_todos"] = r["fuera_activo_frames_todos"]
    s["fuera_activo_frames_por_minuto"] = round(r["fuera_activo_frames_todos"] / r["minutos_vivos"], 2)
    s["fuera_activo_episodios_1s"] = len(r["fuera_activo_episodios"])
    s["fuera_activo_episodio_max_s"] = round(max(r["fuera_activo_episodios"]) / FPS, 2) if r["fuera_activo_episodios"] else 0
    pa = r["pasos_a_inactivo"]
    tipos = collections.Counter(p["tipo"] for p in pa)
    s["inactivo"] = {
        "n": len(pa), "tipos": dict(tipos),
        "fuera_en_inicio_pct": pct([p["fuera_en_inicio"] for p in pa]),
        "flag_constante_pct": pct([p["flag_constante"] for p in pa]),
        "flag_igual_al_anterior_pct": pct([p["flag_igual_al_anterior"] for p in pa]),
        "dist_linea_p10_p50_p90": q([p["dist_linea"] for p in pa]),
        "con_cruce_3s_pct": pct([p["desfase_cruce"] is not None for p in pa]),
        "desfase_cruce_por_tipo": {t: q([p["desfase_cruce"] for p in pa if p["tipo"] == t]) for t in tipos},
        "duracion_s_por_tipo": {t: q([p["duracion"] / FPS for p in pa if p["tipo"] == t and p["duracion"]]) for t in tipos},
    }
    re_ = r["pasos_a_activo"]
    lag2 = [p["desfase_movimiento_activo"] for p in re_]
    s["activo"] = {"n": len(re_), "desfase_movimiento_p10_p50_p90": q([p["desfase_movimiento"] for p in re_]),
                   "sin_movimiento_3s_pct": pct([p["desfase_movimiento"] is None for p in re_]),
                   "desfase_movimiento_activo_p10_p50_p90": q(lag2),
                   "movimiento_activo_en_0_5_25_frames_pct": [pct([x is not None and x <= w for x in lag2]) for w in (0, 5, 25)],
                   "sin_movimiento_activo_3s_pct": pct([x is None for x in lag2]),
                   "mismo_equipo_pct": pct([p["mismo_equipo"] for p in re_]),
                   "salto_al_reanudar_m_p10_p50_p90": q([p["salto"] for p in re_]),
                   "d_flag_m_p10_p50_p90": q([p["d_flag"] for p in re_]),
                   "d_flag_1_2_m_pct": [pct([p["d_flag"] <= w for p in re_]) for w in (1.0, 2.0)],
                   "balon_quieto_en_D_pct": round(100.0 * r["frames_d_quietos"] / r["frames_d"], 2) if r["frames_d"] else None}
    ad, dd = r["cortas_antes_de_D"], r["cortas_despues_de_D"]
    s["cortas"] = {
        "antes_de_D": len(ad), "despues_de_D": len(dd), "entre_dos_D": r["cortas_entre_dos_D"],
        "antes_toque_pct": pct([c["toque"] for c in ad]), "antes_control_pct": pct([c["control"] for c in ad]),
        "antes_fuera_pct": pct([c["fuera"] for c in ad]),
        "antes_toque_sin_control_y_fuera_pct": pct([c["toque"] and not c["control"] and c["fuera"] for c in ad]),
        "antes_reanuda_el_otro_pct": pct([c["reanuda_el_otro"] for c in ad]),
        "antes_toque_sin_control_y_fuera_reanuda_el_otro_pct": pct(
            [c["reanuda_el_otro"] for c in ad if c["toque"] and not c["control"] and c["fuera"]]),
        "despues_toque_pct": pct([c["toque"] for c in dd]), "despues_control_pct": pct([c["control"] for c in dd]),
    }
    if "cobertura" in r:
        s["cobertura"] = {
            "pct": {t: pct([d is not None for d in v]) for t, v in r["cobertura"].items()},
            "n": {t: len(v) for t, v in r["cobertura"].items()},
            "desfase_s_p10_p50_p90": {t: q([d / FPS for d in v if d is not None]) for t, v in r["cobertura"].items()},
            "placebo_pct": pct(r["cobertura_placebo"]),
            "fines_d": r["fines_d"],
            "fines_d_emparejados_pct": round(100.0 * r["fines_d_emparejados"] / r["fines_d"], 1) if r["fines_d"] else None,
            "fines_d_sin_reinicio": len(r["fines_d_sin_reinicio"]),
            "sin_reinicio_evento_cercano": dict(collections.Counter(r["fines_d_sin_reinicio_evento_cercano"])),
        }
        em = r["reinicios_emparejados"]
        tipos_em = sorted(set(e["tipo"] for e in em))
        s["reinicio_y_flag"] = {
            t: {"n": sum(1 for e in em if e["tipo"] == t), "d_flag_p10_p50_p90": q([e["d_flag"] for e in em if e["tipo"] == t]),
                "d_flag_1_m_pct": pct([e["d_flag"] <= 1.0 for e in em if e["tipo"] == t]),
                "equipo_evento_igual_flag_pct": pct([e["equipo_coincide"] for e in em if e["tipo"] == t])}
            for t in tipos_em}
        s["reinicio_equipo_evento_igual_flag_pct"] = pct([e["equipo_coincide"] for e in em])
    if calib:
        c = dict(calib)
        c["pases_por_minuto"] = round(calib["pases"] / r["minutos_vivos"], 2)
        c["toques_atribuidos_por_minuto"] = round(calib["toques_atribuidos"] / r["minutos_vivos"], 2)
        c["pases_con_toque_pct"] = round(100.0 * calib["pases_con_toque_2s"] / calib["pases"], 1)
        c["azar_con_toque_pct"] = round(100.0 * calib["azar_con_toque_2s"] / calib["pases"], 1)
        s["calibracion"] = c
    # veredictos fijados antes de medir
    cob = s.get("cobertura", {}).get("pct", {})
    tres = [cob.get(t) for t in ("ThrowIn", "GoalKick", "CornerKick")]
    if any(v is None for v in tres):
        v1a = "sin datos"
    elif all(v >= 90 for v in tres):
        v1a = "cumple"
    elif any(v < 70 for v in tres):
        v1a = "no cumple"
    else:
        v1a = "entre medias"
    m = (s["momento"]["p10_p50_p90"] or [None, None])[1]
    mr = (s["momento_retencion"]["p10_p50_p90"] or [None, None])[1]
    s["veredictos"] = {
        "1a": v1a,
        "1b": veredicto(s["fuera_activo_pct"], 5, 15, mayor_es_mejor=False),
        "2b": veredicto(s["grupos_pct"]["control"], 70, 40),
        "2c": veredicto_momento(m),
        "3a": veredicto(s["aire_pct"], 10, 30, mayor_es_mejor=False),
        "2g": veredicto(s["toques_sin_control_cambia_pct"], 10, 30, mayor_es_mejor=False),
        "2b retención": veredicto(s["retencion_pct"], 70, 40),
        "2c retención": veredicto_momento(mr),
    }
    return s


def hist_log(duraciones_frames):
    """Histograma en log10(segundos), intervalos de 0,2 décadas de 0,04 s a 400 s, y si hay dos modas."""
    bordes = np.arange(np.log10(0.04), np.log10(400) + 1e-9, 0.2)
    h = np.histogram(np.log10(np.asarray(duraciones_frames) / FPS), bins=bordes)[0]
    picos = [i for i in range(len(h)) if h[i] > 0 and (i == 0 or h[i] > h[i - 1]) and (i == len(h) - 1 or h[i] >= h[i + 1])]
    pares = []
    for a in range(len(picos)):
        for b in range(a + 1, len(picos)):
            entre = h[picos[a] + 1:picos[b]]
            if len(entre) and entre.min() <= 0.7 * min(h[picos[a]], h[picos[b]]):
                pares.append([round(10 ** bordes[picos[a]], 2), round(10 ** bordes[picos[b]], 2),
                              int(h[picos[a]]), int(h[picos[b]]), int(entre.min())])
    return {"bordes_s": [round(10 ** x, 3) for x in bordes], "cuentas": h.tolist(),
            "picos": [[round(10 ** bordes[p], 2), int(h[p])] for p in picos],
            "dos_modas": bool(pares), "pares_de_modas": pares}


def ejecutar(prm, datos):
    por_partido, crudo, calib = {}, {}, {}
    for i, p in enumerate(PARTIDOS):
        crudo[p], calib[p] = medir_partido(i, datos[p], prm)
        por_partido[p] = resumir(crudo[p], calib[p])

    def sumar(ps):
        return dict(sum((collections.Counter(calib[p]) for p in ps), collections.Counter()))

    resto = [p for p in PARTIDOS if p not in PRIMERA]
    juntos = resumir(juntar(list(crudo.values())), sumar(PARTIDOS))
    grupos = {"1ª (J03WMX, J03WN1)": resumir(juntar([crudo[p] for p in PRIMERA]), sumar(PRIMERA)),
              "Düsseldorf (5)": resumir(juntar([crudo[p] for p in resto]), sumar(resto))}
    cuenta = {c: dict(collections.Counter(s["veredictos"][c] for s in por_partido.values())) for c in CRITERIOS}
    return {"por_partido": por_partido, "los_7": juntos, "grupos": grupos, "veredictos_por_partido": cuenta}


def analizar(prm, datos, con_sensibilidad):
    principal = ejecutar(prm, datos)
    salida = {"parametros": prm, "principal": principal}
    if not con_sensibilidad:
        return salida
    sens = {}
    for nombre, cambio in VARIACIONES:
        p2 = dict(prm)
        p2.update(cambio)
        res = ejecutar(p2, datos)
        l7 = res["los_7"]
        sens[nombre] = {"veredictos_los_7": l7["veredictos"], "veredictos_por_partido": res["veredictos_por_partido"],
                        "control_pct": l7["grupos_pct"]["control"], "retencion_pct": l7["retencion_pct"],
                        "momento_p50": (l7["momento"]["p10_p50_p90"] or [None, None])[1],
                        "momento_retencion_p50": (l7["momento_retencion"]["p10_p50_p90"] or [None, None])[1],
                        "aire_pct": l7["aire_pct"], "toques_sin_control": l7["toques_sin_control"],
                        "toques_sin_control_cambia_pct": l7["toques_sin_control_cambia_pct"],
                        "placebo_2g_cambia_pct": l7["placebo_2g_cambia_pct"],
                        "huecos_2g_cambia_pct": l7["huecos_2g_cambia_pct"],
                        "fuera_activo_episodios_1s": l7["fuera_activo_episodios_1s"],
                        "fuera_activo_pct": l7["fuera_activo_pct"], "cobertura_pct": l7["cobertura"]["pct"],
                        "placebo_control_otro_pct": l7["placebo_control_otro_pct"],
                        "placebo_control_flag_pct": l7["placebo_control_flag_pct"],
                        "placebo_retencion_otro_pct": l7["placebo_retencion_otro_pct"],
                        "placebo_retencion_flag_pct": l7["placebo_retencion_flag_pct"],
                        "cortas": l7["cortas"], "activo": l7["activo"]}
    salida["sensibilidad"] = sens
    estable = {}
    for c in CRITERIOS:
        base = principal["los_7"]["veredictos"][c]
        cambian = [n for n, v in sens.items() if v["veredictos_los_7"][c] != base]
        estable[c] = {"principal": base, "aguanta": not cambian,
                      "variaciones_que_lo_cambian": {n: sens[n]["veredictos_los_7"][c] for n in cambian}}
    salida["estabilidad"] = estable
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solo-principal", action="store_true")
    args = parser.parse_args()
    t0 = time.time()
    datos = {p: cargar(p) for p in PARTIDOS}
    salida = {"segundos_carga": round(time.time() - t0, 1),
              "anclaje_saque_s": {p: datos[p]["anclaje_saque_s"] for p in PARTIDOS}}
    jug = {p: [datos[p]["partes"][k]["jugadores"] for k in (1, 2)] for p in PARTIDOS}
    salida["jugadores_en_D"] = {p: resumen_jugadores(jug[p]) for p in PARTIDOS}
    salida["jugadores_en_D"]["los 7"] = resumen_jugadores([j for p in PARTIDOS for j in jug[p]])
    duraciones = {}
    for p in PARTIDOS:
        lab = etiquetas_dfl.etiquetas_partido(dfl_lector.cargar_cache(p))
        duraciones[p] = [n for e, n in etiquetas_dfl.rachas(lab) if e in ("H", "A")]
    salida["histogramas_log"] = {p: hist_log(duraciones[p]) for p in PARTIDOS}
    salida["histogramas_log"]["los 7"] = hist_log([x for p in PARTIDOS for x in duraciones[p]])
    variantes = {"original": dict(mc.PARAMETROS, solo_activos=False),
                 "solo_en_juego": dict(mc.PARAMETROS, solo_activos=True)}
    salida["variantes"] = {k: analizar(v, datos, not args.solo_principal) for k, v in variantes.items()}
    salida["segundos_total"] = round(time.time() - t0, 1)
    salida["memoria_pico_mb"] = dfl_lector.memoria_pico_mb()
    ruta = os.path.join(dfl_lector.carpeta_cache(), "parada3.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    corto = {"guardado": "dfl_cache/parada3.json", "segundos": salida["segundos_total"],
             "memoria_pico_mb": salida["memoria_pico_mb"]}
    for k, v in salida["variantes"].items():
        corto[k] = {"veredictos_los_7": v["principal"]["los_7"]["veredictos"],
                    "veredictos_por_partido": v["principal"]["veredictos_por_partido"],
                    "aguanta": {c: e["aguanta"] for c, e in v.get("estabilidad", {}).items()}}
    print(json.dumps(corto, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
