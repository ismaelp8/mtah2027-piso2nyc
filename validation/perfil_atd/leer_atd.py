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
TOLERANCIA_R2 = 10.0  # puntos
ERRORES_TIPICOS_R2 = 2.5  # §7.7: con pocos huecos, la tolerancia de R2 crece con el ruido del ATD


def num(v, d=2):
    return "–" if v is None else "{:.{}f}".format(v, d).replace(".", ",")


def sino(v):
    return "–" if v is None else ("sí" if v else "no")


class DFL:
    """Los partidos de la DFL cargados una vez, y las primarias de cada condición medida, en caché."""

    def __init__(self, partidos, forma="dirigida"):
        self.cargados = [pdfl.cargar(p) for p in partidos]
        pdfl.comprobar_igual_que_el_harness(self.cargados[0])
        self.cache = {}
        # Bitácora §9 (después de medir, decisión de Ismael del 14/11): con la forma «atd», todas las
        # condiciones que mide la regla llevan la ley de huecos del ATD; la regla no cambia.
        self.forma = {} if forma == "dirigida" else {"forma": "atd", "microcortes": pdfl.dfl.MICROCORTES}

    def medir(self, prm):
        prm = dict(prm, **self.forma)
        clave = pdfl.clave_de(prm)
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
    """({intervalo: (valor, cota)}, huecos impresos) del reparto de una severidad del ATD. Una celda
    suprimida vale como mucho 4 huecos entre los que sí salen más esos 4. Los huecos impresos (sin contar
    los de las celdas suprimidas) son el tamaño de muestra con que se mide el ruido del reparto."""
    reparto = salida["1_huecos_y_rachas"]["reparto_de_los_huecos_pct"]["sin_parado"][pf.etiqueta_severidad(nombre, segundos)]
    huecos = salida["1_huecos_y_rachas"]["sin_parado"]["huecos_n"][:len(reparto)]
    impresos = sum(n for n in huecos if not suprimida(n))
    cota = 100.0 * CASOS_MAX_SUPRIMIDOS / (impresos + CASOS_MAX_SUPRIMIDOS)
    celdas = collections.OrderedDict((k, (None, cota) if suprimida(v) else (v, v)) for k, v in reparto.items())
    return celdas, impresos


def r2_cuadra(valor, cota, dfl, huecos, rango_por_partido=(None, None)):
    """(¿cuadra?, tolerancia) de una celda del reparto (§7.7 y §7.8).

    - La tolerancia es la mayor de ±10 puntos y 2,5 errores típicos del reparto del ATD, √(p·(1 − p)/n),
      con p la proporción de la DFL y n los huecos impresos del ATD en esa severidad. Con muchos huecos es
      ±10, como en la sección 5; con pocos, crece, porque el reparto del ATD es ruido.
    - También cuadra si el ATD cae dentro del rango por partido de la DFL ensanchado a cada lado con la mitad
      de su anchura, como en R3': el ATD es otro partido, y el reparto varía de un partido a otro (§7.8).
    - Una celda del ATD suprimida cuadra si la DFL no pasa de su cota más la tolerancia, o si el rango
      ensanchado baja de la cota.
    - Si la DFL no tiene ningún hueco en la severidad (su reparto sale vacío), cuadra solo si el ATD tampoco
      tiene 5 o más.
    """
    if dfl is None:
        return huecos == 0, None
    p = dfl / 100.0
    tolerancia = max(TOLERANCIA_R2, ERRORES_TIPICOS_R2 * 100.0 * math.sqrt(p * (1.0 - p) / huecos)) if huecos else 100.0
    lo, hi = rango_por_partido
    margen = (hi - lo) / 2.0 if lo is not None and hi is not None else None
    if valor is None:
        en_rango = margen is not None and lo - margen <= cota
        return dfl <= cota + tolerancia or en_rango, tolerancia
    en_rango = margen is not None and lo - margen <= valor <= hi + margen
    return abs(dfl - valor) <= tolerancia or en_rango, tolerancia


def distancia_al_atd(fila, atd):
    """Cuánto se separa un `DISPUTAS` del ATD (§7.8), para elegir el que más se parece (R4' y R7').

    Suma, en las severidades que deciden, |ATD − DFL| de la `s` dividido por 5 puntos y de cada celda del
    reparto dividido por su tolerancia de R2', y |ATD − DFL| del % de disputas dividido por 3 puntos (la
    tolerancia de R3 en la sección 5). Lo suprimido del ATD no cuenta.
    """
    total = 0.0
    for sev in DECIDEN:
        s = fila["severidades"][sev]
        if s["s_atd"] is not None and s["s_dfl"] is not None:
            total += abs(s["s_dfl"] - s["s_atd"]) / 5.0
        for _, valor, _, dfl_r, _, tolerancia, _ in s["repartos"]:
            if valor is not None and dfl_r is not None and tolerancia:
                total += abs(dfl_r - valor) / tolerancia
    if atd["disputa_pct"] is not None and fila["disputas_dfl"][0] is not None:
        total += abs(fila["disputas_dfl"][0] - atd["disputa_pct"]) / 3.0
    return total


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

    # R1'' y R3': para cada DISPUTAS, el OBJETIVO de cada severidad y si el % de disputas cabe. R1' y R2 se
    # juzgan juntos (§7.8): cualquier OBJETIVO que deje la s a ±5 puntos del ATD vale para R1', así que R2 se
    # mira con todos ellos (los de la rejilla y el interpolado), no solo con el interpolado.
    por_disputas = collections.OrderedDict()
    for d in DISPUTAS:
        curva = [dfl.medir(dict(BASE, objetivo=o, disputas=d)) for o in REJILLA_OBJETIVO]
        fila = {"severidades": collections.OrderedDict()}
        for sev, segundos in pf.PRM["severidades"]:
            s_atd, cota = s_del_atd(salida_atd, sev, segundos)
            meta = s_atd if s_atd is not None else 0.0
            ys = [r["juntos"]["s_" + sev] for r in curva]
            interpolado, como = interpolar(REJILLA_OBJETIVO, ys, meta)
            candidatos = list(zip(REJILLA_OBJETIVO, curva))
            if not any(abs(interpolado - o) < 1e-9 for o in REJILLA_OBJETIVO):  # si cae en la rejilla, ya está
                candidatos.append((interpolado, dfl.medir(dict(BASE, objetivo=interpolado, disputas=d))))
            celdas, huecos = reparto_del_atd(salida_atd, sev, segundos)
            evaluados = []
            for objetivo, res in candidatos:
                s = res["juntos"]["s_" + sev]
                # R1': a ±5 puntos del ATD; con el ATD suprimido, del intervalo [0, cota].
                r1 = s is not None and (abs(s - s_atd) <= 5.0 if s_atd is not None else s <= cota + 5.0)
                repartos = []
                for intervalo, (valor, cota_r) in celdas.items():
                    clave = "reparto_{} {}".format(sev, intervalo)
                    dfl_r = res["juntos"][clave]
                    por_partido = rango(res, clave)
                    ok, tolerancia = r2_cuadra(valor, cota_r, dfl_r, huecos, por_partido)
                    repartos.append((intervalo, valor, cota_r, dfl_r, ok, tolerancia, por_partido))
                evaluados.append({"objetivo": objetivo, "s_dfl": s, "r1": r1, "repartos": repartos,
                                  "r2": all(r[4] for r in repartos),
                                  "como": como if abs(objetivo - interpolado) < 1e-9 else "rejilla"})
            # De los que cumplen R1' y R2, el de s más cercana al ATD (si empatan, el menor OBJETIVO). En la
            # severidad que no decide (la alta), solo R1': su R2 no es fiable (§7.6). Si no cumple ninguno, se
            # apunta el interpolado, que es el de R1' (y la severidad no cuadra).
            validos = [e for e in evaluados if e["r1"] and (e["r2"] or sev not in DECIDEN)]
            el_de_r1 = min(evaluados, key=lambda e: abs(e["objetivo"] - interpolado))
            elegido = (min(validos, key=lambda e: (abs(e["s_dfl"] - meta), e["objetivo"])) if validos
                       else el_de_r1)
            fila["severidades"][sev] = dict(elegido, suelo=ys[0], s_atd=s_atd, cota=cota, decide=sev in DECIDEN,
                                            validos=len(validos))
        media = dfl.medir(dict(BASE, objetivo=fila["severidades"]["media"]["objetivo"], disputas=d))
        lo, hi = rango(media, "disputa_pct")
        # El ATD es otro partido: el rango se ensancha a cada lado con toda su anchura (§7.9; con la mitad, la
        # comprobación dejando un partido fuera dejaba fuera a J03WN1).
        margen = (hi - lo) if lo is not None else None
        fila["disputas_dfl"] = (media["juntos"]["disputa_pct"], lo, hi, margen)
        fila["r3"] = (atd["disputa_pct"] is not None and lo is not None
                      and lo - margen <= atd["disputa_pct"] <= hi + margen)
        fila["r1"] = all(fila["severidades"][s]["r1"] for s in DECIDEN)
        fila["r2"] = all(fila["severidades"][s]["r2"] for s in DECIDEN)
        fila["queda"] = fila["r1"] and fila["r2"] and fila["r3"]
        fila["distancia"] = distancia_al_atd(fila, atd)
        por_disputas[d] = fila
    informe["R1_R2_R3"] = por_disputas
    informe["disputa_atd"] = atd["disputa_pct"]
    quedan = [d for d, f in por_disputas.items() if f["queda"]]
    informe["quedan"] = quedan

    def cerca_del_atd(d):
        """El que más se parece al ATD (§7.8): menor distancia; si empatan, el menor `DISPUTAS` (va primero)."""
        return por_disputas[d]["distancia"]

    # R4': el suavizado, con el DISPUTAS que quede más cerca del ATD (si no queda ninguno, el más cercano,
    # solo para apuntarlo).
    d_r4 = min(quedan or list(DISPUTAS), key=cerca_del_atd)
    o_r4 = por_disputas[d_r4]["severidades"]["media"]["objetivo"]
    filas, mejor = [], None
    for s in SUAVIZADOS:
        res = dfl.medir(dict(BASE, objetivo=o_r4, disputas=d_r4, suavizado=s))["juntos"]
        # Solo las tasas que hay en los dos lados (una tasa del ATD suprimida con menos de 10 minutos con balón
        # no se puede leer como el suelo); sin ninguna, R4' no decide.
        claves = [k for k in ("toques_por_min", "controles_por_min") if atd[k] is not None and res[k] is not None]
        separacion = (sum(abs(math.log(max(atd[k], pdfl.SUELO_TASA) / max(res[k], pdfl.SUELO_TASA))) for k in claves)
                      if claves else float("inf"))
        filas.append((s, res["toques_por_min"], res["controles_por_min"], res["temblor_cm"], separacion))
        if mejor is None or separacion < mejor[-1]:
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

    # R7' (decisión de Ismael del 14/11, bitácora §8.3): queda un DISPUTAS con R1', R2 y R3', y con él cuadra
    # R5. Decide el que más se parece al ATD, con la distancia de §7.8 (si empatan, el menor: `min` se queda
    # con el primero y `finales` va de menor a mayor); los demás se puntúan al lado y solo vetan.
    finales = [d for d in quedan if r5[d]["cuadra"]]
    decide = min(finales, key=cerca_del_atd) if finales else None
    informe["R7"] = {"quedan": quedan, "finales": finales, "decide": decide,
                     "vetan": [d for d in finales if d != decide], "R4": informe["R4"]["cuadra"],
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
            "% de disputas del ATD (R3'): {}.".format(num(informe["disputa_atd"])), "",
            "| `DISPUTAS` | severidad | `OBJETIVO` | cómo | suelo de s (%) | s ATD | s DFL | R1' | R2 | % disputas DFL [mín–máx] ± margen | R3' | ¿queda? |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for d, f in informe["R1_R2_R3"].items():
        disp, lo, hi, margen = f["disputas_dfl"]
        for sev, s in f["severidades"].items():
            s_atd = num(s["s_atd"]) if s["s_atd"] is not None else "[≤ {}]".format(num(s["cota"]))
            marca = "" if s["decide"] else " (se apunta)"
            out.append("| {:g} | {}{} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                d, sev, marca, num(s["objetivo"], 3), "{} ({} con R1' y R2)".format(s["como"], s["validos"]),
                num(s["suelo"]), s_atd, num(s["s_dfl"]),
                sino(s["r1"]), sino(s["r2"]),
                "{} [{}–{}] ± {}".format(num(disp), num(lo), num(hi), num(margen)) if sev == "media" else "",
                sino(f["r3"]) if sev == "media" else "", sino(f["queda"]) if sev == "media" else ""))
    quedan = informe["quedan"]
    out += ["", "Quedan: {}.".format(", ".join("{:g}".format(d) for d in quedan) if quedan else "ninguno"),
            "", "Distancia al ATD de cada `DISPUTAS` (§7.8; menos es más parecido): " + " · ".join(
                "{:g}: {}".format(d, num(f["distancia"])) for d, f in informe["R1_R2_R3"].items())]
    out += ["", "**Reparto de los huecos (R2)**, ATD frente a DFL, con el `OBJETIVO` de cada severidad: la "
            "tolerancia de cada celda (R2', §7.7) y el rango por partido ensanchado (R2'', §7.8):", "",
            "| `DISPUTAS` | severidad | intervalo | ATD | DFL | tolerancia (puntos) | rango por partido ± margen | ¿cuadra? |",
            "|---|---|---|---|---|---|---|---|"]
    for d, f in informe["R1_R2_R3"].items():
        for sev, s in f["severidades"].items():
            for intervalo, valor, cota, dfl_r, ok, tolerancia, (lo_r, hi_r) in s["repartos"]:
                atd_txt = num(valor) if valor is not None else "[≤ {}]".format(num(cota))
                rango_txt = ("[{}–{}] ± {}".format(num(lo_r), num(hi_r), num((hi_r - lo_r) / 2.0))
                             if lo_r is not None and hi_r is not None else "–")
                out.append("| {:g} | {} | {} | {} | {} | {} | {} | {} |".format(
                    d, sev, intervalo, atd_txt, num(dfl_r), num(tolerancia, 1), rango_txt, sino(ok)))
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
    vetan = ", ".join("{:g}".format(d) for d in r7["vetan"]) or "ninguno"
    decide = "{:g}".format(r7["decide"]) if r7["decide"] is not None else "ninguno"
    out += ["", "### R7", "",
            "- `DISPUTAS` con los que mide el harness (R1', R2, R3' y R5): **{}**".format(finales),
            "- decide (el que más se parece al ATD, §7.8; si empatan, el menor): **{}**".format(decide),
            "- se puntúan al lado y solo vetan (si el candidato queda 0,03 o más por debajo del control): "
            "**{}**".format(vetan),
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


# Los ensayos de la bitácora (§7.5, §7.7 y §7.8): (partido que hace de ATD, objetivo, disputas, suavizado).
ENSAYOS = (
    ("J03WR9", 0.3, 0.25, 25), ("J03WPY", 0.2, 0.0, 5), ("J03WMX", 0.15, 0.5, 11), ("J03WQQ", 0.41, 0.75, 51),
    ("J03WR9", 0.0, 0.0, 25), ("J03WR9", 0.02, 0.0, 25), ("J03WPY", 0.02, 0.0, 25), ("J03WOH", 0.02, 0.0, 25),
    ("J03WOY", 0.1, 0.25, 25), ("J03WN1", 0.05, 0.25, 25), ("J03WN1", 0.3, 0.5, 11),
)


def ensayos(partidos, detalle=False):
    """La tabla de ensayos de la bitácora: cada partido de `partidos` hace de ATD con sus parámetros de
    `ENSAYOS`, y los otros 6, de DFL (una sola DFL por partido, para todos sus ensayos)."""
    filas = ["| partido que hace de ATD | plantado: objetivo · disputas · suavizado | `DISPUTAS` que quedan | decide "
             "| `OBJETIVO` con el plantado (baja / media / alta) | suavizado elegido | R5 con el que decide |",
             "|---|---|---|---|---|---|---|"]
    informes = []
    for partido in partidos:
        dfl = None
        for p, objetivo, disputas, suavizado in ENSAYOS:
            if p != partido:
                continue
            salida, resto = ensayo(p, objetivo, disputas, suavizado)
            dfl = dfl or DFL(resto)
            informe = leer(salida, dfl, ensayo=True)
            informes.append(("{} con objetivo {:g}, disputas {:g} y suavizado {}".format(p, objetivo, disputas, suavizado),
                             informe))
            r7 = informe["R7"]
            sevs = informe["R1_R2_R3"][disputas]["severidades"]
            decide = r7["decide"]
            r5 = informe["R5"].get(decide, {}).get("cuadra") if decide is not None else None
            filas.append("| {} | {} · {} · {} | {} | {} | {} | {} | {} |".format(
                p, num(objetivo), num(disputas), suavizado,
                ", ".join(num(d) for d in r7["quedan"]) or "ninguno",
                num(decide) if decide is not None else "–",
                " / ".join(num(sevs[s]["objetivo"], 3) for s in SEVERIDADES),
                informe["R4"]["suavizado"], sino(r5)))
    salida = "\n".join(filas)
    if detalle:
        for titulo, informe in informes:
            salida += "\n\n## Ensayo: {}\n\n{}".format(titulo, imprimir(informe))
    return salida


def ensayo(partido, objetivo, disputas, suavizado, forma="dirigida"):
    """(salida, partidos de referencia): un partido de la DFL degradado con parámetros conocidos hace de
    ATD, con las celdas de menos de 5 casos suprimidas como en el partido; los otros hacen de DFL."""
    prm = {"objetivo": objetivo, "disputas": disputas, "media_bloque": BASE["media_bloque"], "suavizado": suavizado}
    if forma == "atd":
        prm.update(forma="atd", microcortes=pdfl.dfl.MICROCORTES)
    trk, _, _ = pdfl.tracking_con(pdfl.cargar(partido), prm)
    salida = pf.para_imprimir(pf.perfil(trk, minimo_celda=5))
    return salida, [p for p in pdfl.dfl.PARTIDOS if p != partido]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("salida_atd", nargs="?", help="la salida de validation/partido/perfil_atd.py, guardada en un JSON")
    ap.add_argument("--partidos", nargs="+", default=list(pdfl.dfl.PARTIDOS), choices=list(pdfl.dfl.PARTIDOS))
    ap.add_argument("--ensayo", nargs=4, metavar=("PARTIDO", "OBJETIVO", "DISPUTAS", "SUAVIZADO"),
                    help="ensayo de la regla (bitácora §7.5): ese partido de la DFL, degradado así, hace de ATD")
    ap.add_argument("--ensayos", nargs="*", metavar="PARTIDO", choices=sorted({e[0] for e in ENSAYOS}),
                    help="la tabla de ensayos de la bitácora (todos, o los de esos partidos)")
    ap.add_argument("--detalle", action="store_true", help="con --ensayos, también el informe de cada uno")
    ap.add_argument("--forma", choices=("dirigida", "atd"), default="dirigida",
                    help="cómo se tapa el balón de la DFL: la de antes de medir (por defecto) o la ley de huecos "
                         "del ATD (bitácora §9, después de medir)")
    args = ap.parse_args()
    if args.ensayos is not None:
        partidos = args.ensayos or sorted({e[0] for e in ENSAYOS})
        print(ensayos(partidos, args.detalle))
        return
    if args.ensayo:
        partido, objetivo, disputas, suavizado = args.ensayo
        salida, partidos = ensayo(partido, float(objetivo), float(disputas), int(suavizado), args.forma)
        print("Ensayo: {} hace de ATD con objetivo {}, disputas {} y suavizado {}; los otros {} hacen de DFL.\n".format(
            partido, objetivo, disputas, suavizado, len(partidos)))
    elif args.salida_atd:
        with open(args.salida_atd, encoding="utf-8-sig") as f:  # con o sin BOM (`>` en PowerShell lo pone)
            salida = json.load(f)
        partidos = args.partidos
    else:
        ap.error("hace falta la salida del ATD o --ensayo")
    print("Forma de tapar el balón de la DFL: {}.\n".format(
        "la ley de huecos del ATD (bitácora §9)" if args.forma == "atd" else "la de antes de medir"))
    print(imprimir(leer(salida, DFL(partidos, args.forma), ensayo=bool(args.ensayo))))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
