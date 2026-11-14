"""Mide los candidatos del estado de `D` (possession/dead_state.py) en los partidos abiertos de la DFL.

    python validation/scripts/d_estado/medir.py                    # los 7 partidos: unos minutos
    python validation/scripts/d_estado/medir.py --sin-sensibilidad # solo la medida principal
    python validation/scripts/d_estado/medir.py --partidos J03WMX J03WN1 --bootstrap 0   # para probar

Datos abiertos de otros partidos (Bassek et al., 2025, CC BY 4.0), sobre la caché del harness. Lo puede
ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Los candidatos, lo que queda fijo y la regla de lectura se escribieron antes de medir: docs/decisiones.md,
entrada del 14/11 «estado con jugadores: candidatos y regla de lectura».

Cómo se mide:

- **Dejando un partido fuera:** el modelo que puntúa un partido se entrena con los demás
  (`entrenar.ajustar`). La puntuación sale de `dead_state.log_odds`, el mismo código del pipeline.
- **Por frame:** AUC de `D` frente a juego.
- **Por parada:** la puntuación de la pieza sola pasa por el decodificador de `main` con sus costes por
  defecto (dos estados: juego o `D`) y las rachas de `D` que salen se comparan con las paradas reales.
  Detectada: una racha predicha cubre al menos la mitad de la parada. Espurio: una racha predicha que no
  toca ninguna parada real.
- **`spellF1` oficial con el equipo oráculo:** el `D` de la pieza y el equipo de las etiquetas. Donde la
  pieza dice juego y la etiqueta es `D`, se arrastra el equipo previo o se adelanta el que reanuda. Con las
  dos convenciones de etiquetas del harness y frente al control (la pieza no opina: ningún `D`).
- **Sensibilidad (no elige nada):** la escala de la puntuación a la mitad y al doble, y un temblor en las
  posiciones de los jugadores.
- **Placebo:** la misma puntuación desplazada 60 s dentro de cada parte.
"""

import argparse
import collections
import os
import sys
import time

import numpy as np
from sklearn.metrics import roc_auc_score

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(ROOT, "validation", "harness"))
sys.path.insert(0, ROOT)
import entrenar  # noqa: E402
import puntuar  # noqa: E402
from possession import dead_state, temporal, tracking  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
SEMILLA = 20261114
CONTROL = "control (v0): no opina"
ORDEN = ("E1", "E2", "E3")  # de más simple a menos
CONVENCIONES = ("flag", "control")
RELLENOS = ("previo", "siguiente")  # arrastrar el equipo previo o adelantar el que reanuda

# El criterio del 13/11, con la lectura fijada el 14/11 (docs/decisiones.md).
LATENCIA_MAX = 25  # frames
FRACCION_MIN = 0.70  # de las paradas reales, con el borde a LATENCIA_MAX o menos
SESGO_MAX = 12  # frames, mediana de la latencia de cada borde
ESPURIOS_MAX = 0.3  # por minuto de juego
RACHA_MIN = 25  # frames: lectura provisional de la duración mínima (es del decodificador)
COBERTURA = 0.5  # fracción de una parada que tiene que cubrir una racha predicha para detectarla

ESCALAS = (0.5, 2.0)  # sensibilidad: la puntuación a la mitad y al doble
TEMBLORES = (0.1, 0.2)  # sensibilidad: desviación típica en metros, por frame y por eje
PLACEBO_FRAMES = 60 * 25


# -- de la puntuación a las rachas de `D` -----------------------------------------------------------------

def rachas(mascara):
    """[(inicio, fin)] de los tramos True, con el fin sin incluir."""
    cambio = np.diff(np.concatenate(([0], np.asarray(mascara, dtype=np.int8), [0])))
    return list(zip(np.flatnonzero(cambio == 1).tolist(), np.flatnonzero(cambio == -1).tolist()))


def mascara_d(trk, puntuacion):
    """Dónde pone `D` el decodificador de `main` si solo opina esta pieza: array (n,) de bool."""
    score, allowed = tracking.no_evidence(len(puntuacion))
    score[:, D] = puntuacion
    return temporal.decode(score, allowed, trk.blocks) == D


def desplazada(puntuacion, blocks, frames):
    """El placebo: la misma puntuación desplazada `frames` dentro de cada parte, dando la vuelta."""
    out = puntuacion.copy()
    for a, b in blocks:
        out[a:b] = np.roll(puntuacion[a:b], frames)
    return out


def con_temblor(trk, sigma, indice):
    """El tracking con ruido gaussiano de `sigma` metros en las posiciones de los jugadores."""
    rng = np.random.default_rng([SEMILLA, indice, int(round(1000 * sigma))])
    ruido_x = rng.normal(0.0, sigma, trk.px.shape).astype(np.float32)
    ruido_y = rng.normal(0.0, sigma, trk.py.shape).astype(np.float32)
    return trk._replace(px=trk.px + ruido_x, py=trk.py + ruido_y)


# -- medidas por parada -----------------------------------------------------------------------------------

def medir_paradas(gt, mascara, blocks):
    """Recuentos y latencias de un partido, para juntarlos después con los de los demás."""
    out = collections.defaultdict(list)
    out.update(paradas=0, detectadas=0, espurios=0, d_cortas=0, juego_cortas=0, frames_juego=0)
    for a, b in blocks:
        g, m = gt[a:b], mascara[a:b]
        reales, predichas = rachas(g == D), rachas(m)
        out["frames_juego"] += int(np.sum((g == H) | (g == A)))
        tocada = [False] * len(predichas)
        for inicio, fin in reales:
            mejor, solape = None, 0
            for k, (c, d) in enumerate(predichas):
                comun = min(fin, d) - max(inicio, c)
                if comun > 0:
                    tocada[k] = True
                    if comun > solape:
                        mejor, solape = (c, d), comun
            detectada = mejor is not None and solape >= COBERTURA * (fin - inicio)
            out["paradas"] += 1
            out["detectadas"] += int(detectada)
            # Un borde que coincide con el principio o el final de la parte no es un cambio: no cuenta.
            if inicio > 0:
                out["lat_inicio"].append(mejor[0] - inicio if detectada else None)
            if fin < b - a:
                out["lat_fin"].append(mejor[1] - fin if detectada else None)
        out["espurios"] += int(sum(not t for t in tocada))
        out["d_cortas"] += int(sum(d - c < RACHA_MIN for c, d in predichas))
        out["juego_cortas"] += int(sum(d - c < RACHA_MIN for c, d in rachas(~m) if c > 0 and d < b - a))
    return out


def juntar_paradas(por_partido):
    """Las medidas del criterio con varios partidos juntos."""
    suma = lambda clave: sum(p[clave] for p in por_partido)  # noqa: E731
    fila = {"paradas": suma("paradas"), "detectadas": suma("detectadas"),
            "espurios_min": suma("espurios") / max(suma("frames_juego") / 25.0 / 60.0, 1e-9),
            "d_cortas": suma("d_cortas"), "juego_cortas": suma("juego_cortas")}
    for borde in ("inicio", "fin"):
        todas = [v for p in por_partido for v in p["lat_" + borde]]
        vistas = np.array([v for v in todas if v is not None], dtype=float)
        fila["n_" + borde] = len(todas)
        fila[borde + "_ok"] = float(np.sum(np.abs(vistas) <= LATENCIA_MAX)) / max(len(todas), 1)
        cuantiles = np.percentile(vistas, [10, 50, 90]) if len(vistas) else [np.nan] * 3
        fila[borde + "_p10"], fila[borde + "_p50"], fila[borde + "_p90"] = (float(q) for q in cuantiles)
    borde_ok = "{} a ≤ %d frames en ≥ %.0f %%" % (LATENCIA_MAX, 100 * FRACCION_MIN)
    fila["cumple"] = {
        borde_ok.format("inicio"): fila["inicio_ok"] >= FRACCION_MIN,
        borde_ok.format("fin"): fila["fin_ok"] >= FRACCION_MIN,
        "sesgo mediano dentro de ±{}".format(SESGO_MAX):
            abs(fila["inicio_p50"]) <= SESGO_MAX and abs(fila["fin_p50"]) <= SESGO_MAX,
        "espurios ≤ {:g} por minuto".format(ESPURIOS_MAX): fila["espurios_min"] <= ESPURIOS_MAX,
        "ninguna racha de menos de {} frames".format(RACHA_MIN): fila["d_cortas"] + fila["juego_cortas"] == 0,
    }
    return fila


# -- `spellF1` con el equipo oráculo ---------------------------------------------------------------------

def con_equipo_oraculo(gt, mascara, blocks, relleno):
    """Etiquetas con el `D` de `mascara` y el equipo de `gt`; `X` fuera de las partes.

    Donde la máscara dice juego y la etiqueta no trae equipo (es `D`), se usa el equipo anterior
    ("previo") o el siguiente ("siguiente") de esa parte.
    """
    pred = np.full(len(gt), X, dtype=np.int8)
    for a, b in blocks:
        g = gt[a:b]
        hay = (g == H) | (g == A)
        indice = np.arange(b - a)
        if not hay.any():
            equipo = np.full(b - a, H, dtype=np.int8)
        elif relleno == "previo":
            ultimo = np.maximum.accumulate(np.where(hay, indice, -1))
            ultimo[ultimo < 0] = np.flatnonzero(hay)[0]
            equipo = g[ultimo]
        else:
            siguiente = np.minimum.accumulate(np.where(hay, indice, b - a)[::-1])[::-1]
            siguiente[siguiente >= b - a] = np.flatnonzero(hay)[-1]
            equipo = g[siguiente]
        pred[a:b] = np.where(mascara[a:b], D, equipo)
    return pred


def recuentos_spell(datos, mascara):
    """{(convención, relleno): recuento del scorer oficial} de un partido con ese `D`."""
    blocks = datos["trk"].blocks
    return {(c, r): puntuar.contar(datos["gt"][c], con_equipo_oraculo(datos["gt"][c], mascara, blocks, r))
            for c in CONVENCIONES for r in RELLENOS}


def comparar(candidato, referencia, n_draws):
    """Diferencia de `spellF1` entre dos versiones, con los partidos juntos y por partido."""
    f1_c = [puntuar.spell_f1(r["flags"], r["n_pred"]) for r in candidato]
    f1_r = [puntuar.spell_f1(r["flags"], r["n_pred"]) for r in referencia]
    junto_c, junto_r = puntuar.juntar(candidato), puntuar.juntar(referencia)
    return {"spell_f1": puntuar.spell_f1(*junto_c), "min": min(f1_c), "max": max(f1_c),
            "diferencia": puntuar.spell_f1(*junto_c) - puntuar.spell_f1(*junto_r),
            "intervalo": puntuar.diferencia_bootstrap(junto_c, junto_r, n_draws),
            "gana_en": int(sum(c > r for c, r in zip(f1_c, f1_r))),
            "pierde_en": int(sum(c < r for c, r in zip(f1_c, f1_r)))}


def al_reves(comparacion):
    """La misma comparación vista desde la otra versión."""
    intervalo = comparacion["intervalo"]
    return {"diferencia": -comparacion["diferencia"], "gana_en": comparacion["pierde_en"],
            "intervalo": None if intervalo is None else [-intervalo[1], -intervalo[0]]}


def gana(comparacion, n_partidos):
    """La regla de §5.8 para una comparación."""
    intervalo = comparacion["intervalo"]
    return (comparacion["diferencia"] >= puntuar.EMPATE
            and comparacion["gana_en"] >= min(puntuar.MIN_PARTIDOS, n_partidos)
            and (intervalo is None or intervalo[0] > 0))


# -- la medida --------------------------------------------------------------------------------------------

def puntuaciones(cargados, nombres):
    """La puntuación de cada partido con el modelo entrenado en los demás: {partido: array (n,)}."""
    out = {}
    for datos in cargados:
        resto = [otro for otro in cargados if otro is not datos]
        modelo = entrenar.ajustar(resto, nombres)
        out[datos["partido"]] = (dead_state.log_odds(datos["trk"], modelo), modelo)
    return out


def medir_version(cargados, puntuacion_de):
    """Las medidas de una versión: `puntuacion_de(datos)` da la puntuación de `D` de un partido."""
    paradas, spell, auc = [], collections.defaultdict(list), []
    for datos in cargados:
        puntuacion = puntuacion_de(datos)
        gt = datos["gt"]["flag"]
        con_etiqueta = gt != X
        auc.append(float(roc_auc_score(gt[con_etiqueta] == D, puntuacion[con_etiqueta])))
        mascara = mascara_d(datos["trk"], puntuacion)
        paradas.append(medir_paradas(gt, mascara, datos["trk"].blocks))
        for clave, recuento in recuentos_spell(datos, mascara).items():
            spell[clave].append(recuento)
    return {"paradas": juntar_paradas(paradas), "paradas_por_partido": [juntar_paradas([p]) for p in paradas],
            "spell": dict(spell), "auc": auc}


def medir(partidos, n_draws, sensibilidad, avisar):
    cargados = []
    for partido in partidos:
        cargados.append(entrenar.cargar(partido))
        avisar("cargado {}".format(partido))
    indice = {datos["partido"]: k for k, datos in enumerate(cargados)}

    sin_d = {datos["partido"]: np.zeros(len(datos["trk"].bx), dtype=bool) for datos in cargados}
    referencia = collections.defaultdict(list)  # el control: ningún `D`
    for datos in cargados:
        for clave, recuento in recuentos_spell(datos, sin_d[datos["partido"]]).items():
            referencia[clave].append(recuento)

    versiones = collections.OrderedDict()
    modelos = {}
    for nombre in ORDEN:
        por_partido = puntuaciones(cargados, entrenar.CANDIDATOS[nombre])
        modelos[nombre] = {p: m for p, (_, m) in por_partido.items()}
        base = {p: s for p, (s, _) in por_partido.items()}
        versiones[nombre] = medir_version(cargados, lambda d: base[d["partido"]])
        avisar("medido {}".format(nombre))
        if not sensibilidad:
            continue
        versiones[nombre + ", placebo: desplazada 60 s"] = medir_version(
            cargados, lambda d: desplazada(base[d["partido"]], d["trk"].blocks, PLACEBO_FRAMES))
        for escala in ESCALAS:
            versiones["{}, escala × {:g}".format(nombre, escala)] = medir_version(
                cargados, lambda d: np.clip(escala * base[d["partido"]],
                                            -dead_state.SCORE_CLIP, dead_state.SCORE_CLIP))
        for sigma in TEMBLORES:
            versiones["{}, temblor de {:g} m".format(nombre, sigma)] = medir_version(
                cargados, lambda d: dead_state.log_odds(
                    con_temblor(d["trk"], sigma, indice[d["partido"]]), modelos[nombre][d["partido"]]))
        avisar("medida la sensibilidad de {}".format(nombre))

    frente_al_control = {nombre: {clave: comparar(v["spell"][clave], referencia[clave], n_draws)
                                  for clave in referencia} for nombre, v in versiones.items()}
    control = {clave: comparar(referencia[clave], referencia[clave], 0) for clave in referencia}
    entre_candidatos = {
        (a, b): {clave: comparar(versiones[a]["spell"][clave], versiones[b]["spell"][clave], n_draws)
                 for clave in referencia}
        for a, b in (("E2", "E1"), ("E3", "E2"), ("E3", "E1"))}
    return {"partidos": partidos, "versiones": versiones, "control": control,
            "frente_al_control": frente_al_control, "entre_candidatos": entre_candidatos}


# -- salida -----------------------------------------------------------------------------------------------

def num(valor, signo=False, decimales=3):
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "–"
    formato = "{:+." + str(decimales) + "f}" if signo else "{:." + str(decimales) + "f}"
    return formato.format(valor).replace(".", ",")


def pct(valor):
    return "{:.0f} %".format(100.0 * valor)


def con_intervalo(c):
    texto = num(c["diferencia"], True)
    if c["intervalo"]:
        texto += " [{} a {}]".format(num(c["intervalo"][0], True), num(c["intervalo"][1], True))
    return texto


def tabla_criterio(resultado):
    n = len(resultado["partidos"])
    lineas = ["### Criterio del 13/11: por parada, {} partidos juntos".format(n), "",
              "| versión | AUC por frame, media (mín–máx) | paradas detectadas | inicio a ≤ 25 frames (por "
              "partido, mín–máx) | fin a ≤ 25 frames (por partido, mín–máx) | latencia del inicio p10 / p50 / p90 "
              "| latencia del fin p10 / p50 / p90 | `D` espurios por minuto de juego | rachas de menos de 25 "
              "frames (`D` / juego) |", "|---|---|---|---|---|---|---|---|---|"]
    for nombre, v in resultado["versiones"].items():
        p, pp = v["paradas"], v["paradas_por_partido"]
        celdas = [
            nombre,
            "{} ({}–{})".format(num(float(np.mean(v["auc"]))), num(min(v["auc"])), num(max(v["auc"]))),
            "{} de {} ({})".format(p["detectadas"], p["paradas"], pct(p["detectadas"] / max(p["paradas"], 1))),
        ]
        for borde in ("inicio_ok", "fin_ok"):
            celdas.append("{} ({}–{})".format(pct(p[borde]), pct(min(q[borde] for q in pp)),
                                              pct(max(q[borde] for q in pp))))
        for borde in ("inicio", "fin"):
            celdas.append(" / ".join(num(p[borde + "_" + q], True, 0) for q in ("p10", "p50", "p90")))
        celdas += [num(p["espurios_min"], decimales=2), "{} / {}".format(p["d_cortas"], p["juego_cortas"])]
        lineas.append("| " + " | ".join(celdas) + " |")
    lineas += ["", "Las latencias van en frames; positivo es tarde. Una parada no detectada cuenta como fallo "
               "en las dos columnas de «a ≤ 25 frames».", ""]
    return "\n".join(lineas)


def tabla_spell(resultado):
    n = len(resultado["partidos"])
    lineas = ["### `spellF1` oficial con el equipo oráculo, {} partidos juntos".format(n), "",
              "El `D` perfecto da 1,000 en todas las columnas. «Frente al control» lleva el intervalo del 5 al "
              "95 % del bootstrap pareado del harness y en cuántos partidos gana.", "",
              "| versión | " + " | ".join("{}, {}".format(c, r) for c in CONVENCIONES for r in RELLENOS) + " |",
              "|---|" + "---|" * (len(CONVENCIONES) * len(RELLENOS))]
    claves = [(c, r) for c in CONVENCIONES for r in RELLENOS]
    lineas.append("| {} | {} |".format(CONTROL, " | ".join(num(resultado["control"][k]["spell_f1"]) for k in claves)))
    for nombre in resultado["versiones"]:
        celdas = []
        for k in claves:
            c = resultado["frente_al_control"][nombre][k]
            celdas.append("{} · {} · {} de {}".format(num(c["spell_f1"]), con_intervalo(c), c["gana_en"], n))
        lineas.append("| {} | {} |".format(nombre, " | ".join(celdas)))
    lineas += ["", "### Entre candidatos (diferencia de `spellF1`, el primero menos el segundo)", "",
               "| comparación | " + " | ".join("{}, {}".format(c, r) for c, r in claves) + " |",
               "|---|" + "---|" * len(claves)]
    for (a, b), por_clave in resultado["entre_candidatos"].items():
        lineas.append("| {} − {} | {} |".format(a, b, " | ".join(
            "{} · {} de {}".format(con_intervalo(por_clave[k]), por_clave[k]["gana_en"], n) for k in claves)))
    lineas.append("")
    return "\n".join(lineas)


def veredictos(resultado):
    n = len(resultado["partidos"])
    lineas = ["### Lectura con la regla fijada antes de medir", ""]
    for nombre in ORDEN:
        cumple = resultado["versiones"][nombre]["paradas"]["cumple"]
        fallos = [texto for texto, ok in cumple.items() if not ok]
        lineas.append("- **{}, criterio del 13/11:** {}".format(
            nombre, "**cumple**" if not fallos else "**no cumple** ({})".format("; ".join(fallos))))
        gana_al_control = all(gana(c, n) for c in resultado["frente_al_control"][nombre].values())
        lineas.append("- **{}, frente al control con la regla de §5.8:** {}".format(
            nombre, "**gana**" if gana_al_control else "**empate o no concluye**"))
    vencido = collections.defaultdict(list)  # candidato -> los que le ganan
    for (a, b), por_clave in resultado["entre_candidatos"].items():
        if all(gana(c, n) for c in por_clave.values()):
            texto = "**gana {}**".format(a)
            vencido[b].append(a)
        elif all(gana(al_reves(c), n) for c in por_clave.values()):
            texto = "**gana {}**".format(b)
            vencido[a].append(b)
        else:
            texto = "**empate**"
        lineas.append("- **{} frente a {} con la regla de §5.8:** {}".format(a, b, texto))
    entra = next(nombre for nombre in ORDEN if not vencido[nombre])
    lineas.append("- **Entre candidatos entra el más simple al que ningún otro gana: {}.**".format(entra))
    return "\n".join(lineas)


def main():
    parser = argparse.ArgumentParser(description="Mide los candidatos del estado de D en la DFL.")
    parser.add_argument("--partidos", nargs="+", default=list(entrenar.PARTIDOS), choices=list(entrenar.PARTIDOS))
    parser.add_argument("--bootstrap", type=int, default=1000, help="remuestreos del intervalo; 0 lo quita")
    parser.add_argument("--sin-sensibilidad", action="store_true", help="sin el placebo, las escalas ni el temblor")
    args = parser.parse_args()
    if len(args.partidos) < 2:
        sys.exit("Hacen falta al menos dos partidos: el modelo se entrena dejando uno fuera.")

    inicio = time.time()

    def avisar(texto):
        print("{} ({:.0f} s)".format(texto, time.time() - inicio), file=sys.stderr)

    resultado = medir(args.partidos, args.bootstrap, not args.sin_sensibilidad, avisar)
    print("partidos: {} · bootstrap: {} · decodificador: costes por defecto de possession/temporal.py {}".format(
        len(args.partidos), args.bootstrap, temporal.DEFAULTS))
    print()
    print(tabla_criterio(resultado))
    print(tabla_spell(resultado))
    print(veredictos(resultado))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
