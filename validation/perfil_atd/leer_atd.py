"""La regla de lectura de la bitácora (secciones 5 y 7) aplicada a la salida del perfil del ATD.

    python validation/perfil_atd/leer_atd.py salida_atd.json [--partidos J03WMX ...]
    python validation/perfil_atd/leer_atd.py --ensayo J03WR9 0.3 0.25 25

`salida_atd.json` es la salida de `validation/partido/perfil_atd.py` tal cual: solo agregados del partido,
pegados por quien lo ejecutó. Lo demás se mide en la DFL con `perfil_dfl.py`, así que lo puede ejecutar
Claude. Tarda unos 10 minutos con los 7 partidos. Imprime, en markdown, cada regla con su veredicto y los
parámetros de la degradación que salen de ella.

Con `--ensayo PARTIDO OBJETIVO DISPUTAS SUAVIZADO`, ese partido de la DFL, degradado con esos parámetros,
hace de ATD y los otros 6 hacen de DFL: la regla tiene que devolver los parámetros plantados (bitácora
§7.5). En el ensayo no se mira R0, que es un control del ATD.

Está escrito antes de ver ningún número del ATD, como la regla: el código es la regla, y lo que no
decide la regla (R6, una ley de huecos nueva para R2, otra forma de tapar las disputas) lo dice y no lo
hace.
"""

import argparse
import collections
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import perfil as pf  # noqa: E402
import perfil_dfl as pdfl  # noqa: E402

CONTROL = (("frames evaluados", 158857), ("frames con balón", 94214), ("tramos de balón parado", 59),
           ("frames en tramos de balón parado", 7336))  # R0: los del 12/11
DISPUTAS = (0.0, 0.25, 0.5, 0.75, 1.0)
REJILLA_OBJETIVO = (0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.41, 0.5)
SUAVIZADOS = (1, 5, 11, 25, 51)
SEVERIDADES = tuple(nombre for nombre, _ in pf.PRM["severidades"])
DECIDEN = ("baja", "media")  # §7.6: la severidad alta mezcla en la DFL paradas cortas tapadas; se apunta y no decide
BASE = {"objetivo": 0.2, "disputas": 0.5, "media_bloque": 25, "suavizado": 1}
CASOS_MAX_SUPRIMIDOS = 4  # una celda "< 5" tiene como mucho 4 casos


def num(v, d=2):
    return "–" if v is None else "{:.{}f}".format(v, d).replace(".", ",")


def sino(v):
    return "–" if v is None else ("sí" if v else "no")


class DFL:
    """Los partidos de la DFL cargados una vez, y las primarias de cada condición medida, en caché."""

    def __init__(self, partidos):
        self.cargados = [pdfl.cargar(p) for p in partidos]
        pdfl.comprobar_igual_que_el_harness(self.cargados[0])
        self.cache = {}

    def medir(self, prm):
        clave = tuple(round(float(prm[p]), 6) for p in pdfl.PARAMETROS)
        if clave not in self.cache:
            parciales, por_partido = [], {}
            for c in self.cargados:
                trk, _, _ = pdfl.tracking_con(c, prm)
                m = pf.medidas(trk, jugadores=False)
                parciales.append(m)
                por_partido[c["partido"]] = pf.primarias(pf.resumir([m]))
            self.cache[clave] = {"juntos": pf.primarias(pf.resumir(parciales)), "por_partido": por_partido}
        return self.cache[clave]


def rango(res, clave):
    valores = [p[clave] for p in res["por_partido"].values() if p.get(clave) is not None]
    return (min(valores), max(valores)) if valores else (None, None)


def interpolar(xs, ys, y):
    """(x, cómo) tal que la curva no decreciente ys(xs) vale y, interpolando entre puntos de la rejilla."""
    if y <= ys[0]:
        return xs[0], "por debajo del suelo"
    if y >= ys[-1]:
        return xs[-1], "por encima de la rejilla"
    for x0, y0, x1, y1 in zip(xs, ys, xs[1:], ys[1:]):
        if y0 <= y <= y1 and y1 > y0:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0), "interpolado"
    return xs[-1], "curva no ordenada"


def cociente_ok(atd, dfl, suelo):
    if atd is None or dfl is None:
        return None
    a, b = max(atd, suelo), max(dfl, suelo)
    return 0.5 <= a / b <= 2.0 if b > 0 else a == b


# -- lo que llega del ATD, con las celdas suprimidas como cotas ------------------------------------------

def suprimida(v):
    return isinstance(v, str)


def s_del_atd(salida, nombre, segundos):
    """(s, cota) de una severidad del ATD (sin_parado). Si está suprimida (menos de 5 huecos hasta el
    corte), s es None y la cota es el máximo que puede valer: 4 huecos de T segundos."""
    v = salida["1_huecos_y_rachas"]["s_pct"]["sin_parado"][pf.etiqueta_severidad(nombre, segundos)]
    if not suprimida(v):
        return v, v
    con_balon = salida["0_control"]["balon_parado"]["frames_con_balon_fuera_de_ellos"]
    faltan = CASOS_MAX_SUPRIMIDOS * segundos * 25.0
    return None, 100.0 * faltan / (con_balon + faltan)


def reparto_del_atd(salida, nombre, segundos):
    """{intervalo: (valor, cota)} del reparto de una severidad del ATD. Una celda suprimida vale como mucho
    4 huecos entre los que sí salen más esos 4."""
    reparto = salida["1_huecos_y_rachas"]["reparto_de_los_huecos_pct"]["sin_parado"][pf.etiqueta_severidad(nombre, segundos)]
    huecos = salida["1_huecos_y_rachas"]["sin_parado"]["huecos_n"][:len(reparto)]
    impresos = sum(n for n in huecos if not suprimida(n))
    cota = 100.0 * CASOS_MAX_SUPRIMIDOS / (impresos + CASOS_MAX_SUPRIMIDOS)
    return collections.OrderedDict((k, (None, cota) if suprimida(v) else (v, v)) for k, v in reparto.items())


def tasas_suprimidas(salida_atd, atd):
    """Las tasas por minuto que salen suprimidas ("< 5" casos) cuentan como el suelo de R4 (0,5 por minuto).

    Vale si hay 10 minutos con balón o más: menos de 5 casos en 10 minutos ya es menos de 0,5 por minuto.
    """
    s = salida_atd["4_suavizado"]["sin_parado"]
    crudos = {"toques_por_min": s["toques_por_min"]["umbral {:g} m/s".format(pf.PRM["umbrales_toque"][0])],
              "controles_por_min": s["controles_ret12_por_min"]}
    for clave, crudo in crudos.items():
        if atd[clave] is None and suprimida(crudo) and (s["minutos_con_balon"] or 0) >= 10:
            atd[clave] = pdfl.SUELO_TASA
    return atd


# -- la regla ------------------------------------------------------------------------------------------

def leer(salida_atd, dfl, ensayo=False):
    atd = tasas_suprimidas(salida_atd, pf.primarias(salida_atd))
    informe = collections.OrderedDict()

    # R0: si el lector no lee lo mismo que el 12/11, se para.
    c = salida_atd["0_control"]
    vistos = (c["frames_evaluados"], c["frames_con_balon"], c["balon_parado"]["tramos_n"], c["balon_parado"]["frames"])
    informe["R0"] = [(nombre, visto, esperado, visto == esperado) for (nombre, esperado), visto in zip(CONTROL, vistos)]
    informe["ensayo"] = ensayo
    informe["parar"] = not ensayo and not all(ok for *_, ok in informe["R0"])
    if informe["parar"]:
        return informe

    # R1', R2 y R3': para cada DISPUTAS, el OBJETIVO de cada severidad y si el % de disputas cabe.
    por_disputas = collections.OrderedDict()
    for d in DISPUTAS:
        curva = [dfl.medir(dict(BASE, objetivo=o, disputas=d)) for o in REJILLA_OBJETIVO]
        fila = {"severidades": collections.OrderedDict()}
        for sev, segundos in pf.PRM["severidades"]:
            s_atd, cota = s_del_atd(salida_atd, sev, segundos)
            ys = [r["juntos"]["s_" + sev] for r in curva]
            objetivo, como = interpolar(REJILLA_OBJETIVO, ys, s_atd if s_atd is not None else 0.0)
            res = dfl.medir(dict(BASE, objetivo=objetivo, disputas=d))
            s = res["juntos"]["s_" + sev]
            # Cuadra si queda a ±5 puntos del ATD; con el ATD suprimido, del intervalo [0, cota].
            r1 = s is not None and (abs(s - s_atd) <= 5.0 if s_atd is not None else s <= cota + 5.0)
            repartos = []
            for intervalo, (valor, cota_r) in reparto_del_atd(salida_atd, sev, segundos).items():
                dfl_r = res["juntos"]["reparto_{} {}".format(sev, intervalo)]
                ok = dfl_r is not None and (abs(dfl_r - valor) <= 10.0 if valor is not None else dfl_r <= cota_r + 10.0)
                repartos.append((intervalo, valor, cota_r, dfl_r, ok))
            fila["severidades"][sev] = {
                "objetivo": objetivo, "como": como, "suelo": ys[0], "s_atd": s_atd, "cota": cota, "s_dfl": s,
                "r1": r1, "repartos": repartos, "r2": all(ok for *_, ok in repartos), "decide": sev in DECIDEN}
        media = dfl.medir(dict(BASE, objetivo=fila["severidades"]["media"]["objetivo"], disputas=d))
        lo, hi = rango(media, "disputa_pct")
        margen = (hi - lo) / 2.0 if lo is not None else None  # el ATD es otro partido: el rango se ensancha
        fila["disputas_dfl"] = (media["juntos"]["disputa_pct"], lo, hi, margen)
        fila["r3"] = (atd["disputa_pct"] is not None and lo is not None
                      and lo - margen <= atd["disputa_pct"] <= hi + margen)
        fila["r1"] = all(fila["severidades"][s]["r1"] for s in DECIDEN)
        fila["r2"] = all(fila["severidades"][s]["r2"] for s in DECIDEN)
        fila["queda"] = fila["r1"] and fila["r2"] and fila["r3"]
        por_disputas[d] = fila
    informe["R1_R2_R3"] = por_disputas
    quedan = [d for d, f in por_disputas.items() if f["queda"]]
    informe["quedan"] = quedan

    def cerca_del_atd(d):
        return abs(por_disputas[d]["disputas_dfl"][0] - (atd["disputa_pct"] or 0.0))

    # R4': el suavizado, con el DISPUTAS que quede más cerca del ATD (si no queda ninguno, el más cercano,
    # solo para apuntarlo).
    d_r4 = min(quedan or list(DISPUTAS), key=cerca_del_atd)
    o_r4 = por_disputas[d_r4]["severidades"]["media"]["objetivo"]
    filas, mejor = [], None
    for s in SUAVIZADOS:
        res = dfl.medir(dict(BASE, objetivo=o_r4, disputas=d_r4, suavizado=s))["juntos"]
        distancia = sum(abs(math.log(max(atd[k], pdfl.SUELO_TASA) / max(res[k], pdfl.SUELO_TASA)))
                        for k in ("toques_por_min", "controles_por_min"))
        filas.append((s, res["toques_por_min"], res["controles_por_min"], res["temblor_cm"], distancia))
        if mejor is None or distancia < mejor[-1]:
            mejor = filas[-1]
    informe["R4"] = {"disputas": d_r4, "objetivo": o_r4, "filas": filas, "suavizado": mejor[0],
                     "atd": (atd["toques_por_min"], atd["controles_por_min"], atd["temblor_cm"]),
                     "cuadra": all(cociente_ok(atd[k], v, pdfl.SUELO_TASA)
                                   for k, v in (("toques_por_min", mejor[1]), ("controles_por_min", mejor[2])))}

    # R5: la proximidad, con cada DISPUTAS que quede y el suavizado elegido. Decide la severidad media; la
    # baja y la alta se apuntan.
    r5 = collections.OrderedDict()
    for d in quedan or [d_r4]:
        por_sev = collections.OrderedDict()
        for sev in SEVERIDADES:
            o = por_disputas[d]["severidades"][sev]["objetivo"]
            res = dfl.medir(dict(BASE, objetivo=o, disputas=d, suavizado=informe["R4"]["suavizado"]))["juntos"]
            comprobaciones = [(k, atd[k], res[k], atd[k] is not None and res[k] is not None and abs(atd[k] - res[k]) <= 10.0)
                              for k in ("cercano_a_1_m_pct", "cercano_a_1.5_m_pct", "cercano_a_3_m_pct")]
            comprobaciones.append(("cambios_cercano_por_min", atd["cambios_cercano_por_min"], res["cambios_cercano_por_min"],
                                   cociente_ok(atd["cambios_cercano_por_min"], res["cambios_cercano_por_min"],
                                               pdfl.SUELO_TASA)))
            por_sev[sev] = {"objetivo": o, "comprobaciones": comprobaciones,
                            "cuadra": all(ok for *_, ok in comprobaciones)}
        r5[d] = {"por_severidad": por_sev, "cuadra": por_sev["media"]["cuadra"]}
    informe["R5"] = r5

    # R7': queda un DISPUTAS con R1', R2 y R3', y con él cuadra R5.
    finales = [d for d in quedan if r5[d]["cuadra"]]
    informe["R7"] = {"quedan": quedan, "finales": finales, "R4": informe["R4"]["cuadra"],
                     "proximidad": bool(finales), "velocidad": bool(finales) and informe["R4"]["cuadra"],
                     "falta_R6": bool(quedan) and not finales}
    return informe


def imprimir(informe):
    out = ["### R0. Control", "", "| control | ATD | esperado | ¿igual? |", "|---|---|---|---|"]
    out += ["| {} | {} | {} | {} |".format(n, v, e, sino(ok)) for n, v, e, ok in informe["R0"]]
    if informe["ensayo"]:
        out += ["", "En el ensayo no se mira R0: el falso ATD es un partido de la DFL."]
    if informe["parar"]:
        out += ["", "**R0 no cuadra: se para y se busca por qué. No se lee nada más.**"]
        return "\n".join(out)

    out += ["", "### R1', R2 y R3'", "",
            "Deciden las severidades baja y media; la alta se apunta (bitácora §7.6). Entre corchetes, la cota de "
            "un valor del ATD suprimido.", "",
            "| `DISPUTAS` | severidad | `OBJETIVO` | cómo | suelo de s (%) | s ATD | s DFL | R1' | R2 | % disputas DFL [mín–máx] ± margen | R3' | ¿queda? |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for d, f in informe["R1_R2_R3"].items():
        disp, lo, hi, margen = f["disputas_dfl"]
        for sev, s in f["severidades"].items():
            s_atd = num(s["s_atd"]) if s["s_atd"] is not None else "[≤ {}]".format(num(s["cota"]))
            marca = "" if s["decide"] else " (se apunta)"
            out.append("| {:g} | {}{} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                d, sev, marca, num(s["objetivo"], 3), s["como"], num(s["suelo"]), s_atd, num(s["s_dfl"]),
                sino(s["r1"]), sino(s["r2"]),
                "{} [{}–{}] ± {}".format(num(disp), num(lo), num(hi), num(margen)) if sev == "media" else "",
                sino(f["r3"]) if sev == "media" else "", sino(f["queda"]) if sev == "media" else ""))
    quedan = informe["quedan"]
    out += ["", "Quedan: {}.".format(", ".join("{:g}".format(d) for d in quedan) if quedan else "ninguno")]
    out += ["", "**Reparto de los huecos (R2)**, ATD frente a DFL, con el `OBJETIVO` de cada severidad:", "",
            "| `DISPUTAS` | severidad | intervalo | ATD | DFL | ¿cuadra? |", "|---|---|---|---|---|---|"]
    for d, f in informe["R1_R2_R3"].items():
        for sev, s in f["severidades"].items():
            for intervalo, valor, cota, dfl_r, ok in s["repartos"]:
                atd_txt = num(valor) if valor is not None else "[≤ {}]".format(num(cota))
                out.append("| {:g} | {} | {} | {} | {} | {} |".format(d, sev, intervalo, atd_txt, num(dfl_r), sino(ok)))
    r4 = informe["R4"]
    out += ["", "### R4'. Suavizado (con `DISPUTAS` {:g} y `OBJETIVO` {})".format(r4["disputas"], num(r4["objetivo"], 3)), "",
            "ATD: {} toques/min, {} controles/min, {} cm de temblor (descriptivo).".format(
                num(r4["atd"][0], 1), num(r4["atd"][1], 1), num(r4["atd"][2])), "",
            "| suavizado | toques/min | controles/min | temblor (cm, descriptivo) | distancia |", "|---|---|---|---|---|"]
    out += ["| {} | {} | {} | {} | {} |".format(s, num(t, 1), num(c, 1), num(te), num(dd, 3)) for s, t, c, te, dd in r4["filas"]]
    out += ["", "Elegido: {} frames. Cuadra: {}.".format(r4["suavizado"], sino(r4["cuadra"]))]
    out += ["", "### R5. Proximidad (decide la severidad media)", "",
            "| `DISPUTAS` | severidad | medida | ATD | DFL | ¿cuadra? |", "|---|---|---|---|---|---|"]
    for d, v in informe["R5"].items():
        for sev, x in v["por_severidad"].items():
            marca = "" if sev == "media" else " (se apunta)"
            out += ["| {:g} | {}{} | {} | {} | {} | {} |".format(d, sev, marca, k, num(a), num(b), sino(ok))
                    for k, a, b, ok in x["comprobaciones"]]
    r7 = informe["R7"]
    finales = ", ".join("{:g}".format(d) for d in r7["finales"]) or "ninguno"
    out += ["", "### R7", "",
            "- `DISPUTAS` con los que mide el harness (R1', R2, R3' y R5): **{}**".format(finales),
            "- el orden entre evidencias de equipo por proximidad: **{}**".format(
                "se puede decidir" if r7["proximidad"] else "todavía no"),
            "- lo que use la velocidad del balón: **{}**".format("se puede decidir" if r7["velocidad"] else "todavía no")]
    if r7["falta_R6"]:
        out.append("- R5 no cuadra con ningún `DISPUTAS` que queda: toca R6 (degradar a los jugadores), que este "
                   "script no hace.")
    if not r7["quedan"]:
        out.append("- No queda ningún `DISPUTAS`: en el paso 3 cambia la forma de tapar (R2 con la ley de huecos del "
                   "ATD, o la parte dirigida con `dilatar` y `aire`), y se vuelve a leer con esta misma regla.")
    return "\n".join(out)


def ensayo(partido, objetivo, disputas, suavizado):
    """(salida, partidos de referencia): un partido de la DFL degradado con parámetros conocidos hace de
    ATD, con las celdas de menos de 5 casos suprimidas como en el partido; los otros hacen de DFL."""
    prm = {"objetivo": objetivo, "disputas": disputas, "media_bloque": BASE["media_bloque"], "suavizado": suavizado}
    trk, _, _ = pdfl.tracking_con(pdfl.cargar(partido), prm)
    salida = pf.para_imprimir(pf.perfil(trk, minimo_celda=5))
    return salida, [p for p in pdfl.dfl.PARTIDOS if p != partido]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("salida_atd", nargs="?", help="la salida de validation/partido/perfil_atd.py, guardada en un JSON")
    ap.add_argument("--partidos", nargs="+", default=list(pdfl.dfl.PARTIDOS), choices=list(pdfl.dfl.PARTIDOS))
    ap.add_argument("--ensayo", nargs=4, metavar=("PARTIDO", "OBJETIVO", "DISPUTAS", "SUAVIZADO"),
                    help="ensayo de la regla (bitácora §7.5): ese partido de la DFL, degradado así, hace de ATD")
    args = ap.parse_args()
    if args.ensayo:
        partido, objetivo, disputas, suavizado = args.ensayo
        salida, partidos = ensayo(partido, float(objetivo), float(disputas), int(suavizado))
        print("Ensayo: {} hace de ATD con objetivo {}, disputas {} y suavizado {}; los otros {} hacen de DFL.\n".format(
            partido, objetivo, disputas, suavizado, len(partidos)))
    elif args.salida_atd:
        with open(args.salida_atd, encoding="utf-8") as f:
            salida = json.load(f)
        partidos = args.partidos
    else:
        ap.error("hace falta la salida del ATD o --ensayo")
    print(imprimir(leer(salida, DFL(partidos), ensayo=bool(args.ensayo))))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
