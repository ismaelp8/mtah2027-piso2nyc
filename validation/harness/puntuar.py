"""Harness de la DFL: puntúa el pipeline (possession/) en los 7 partidos abiertos de la Bundesliga.

    python validation/harness/puntuar.py                      # los 7 partidos: medio minuto
    python validation/harness/puntuar.py --partidos J03WMX    # un partido, para probar
    python validation/harness/puntuar.py --json               # la salida completa, en JSON

Ejecuta las mismas piezas que el partido (`possession.pipeline.run`) sobre el tracking de la DFL en el
formato común (`dfl.py`) y las puntúa con el scorer oficial (`evaluation/possession_metrics.py`). Son
datos abiertos de otros partidos: lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Cómo se mide:

- con las dos convenciones de etiquetas ("flag" y "control") y en tres condiciones del balón;
- frente al control, que es el baseline oficial: jugador más cercano y voto por mayoría de ±50 frames;
- con el `D` copiado de las etiquetas (`D` oráculo) para todos, el control incluido. La DFL congela el
  balón mientras está muerto y hay que taparlo; así «no hay balón» casi equivale a «`D`», cosa que en el
  ATD no pasa. Con `--d propio` cada versión pone su `D`, pero ese número no sirve para decidir;
- `spellF1` con los 7 partidos juntos (sumando los recuentos de posesiones de cada uno), por partido, y
  la diferencia con el control con un intervalo por bootstrap pareado sobre las posesiones reales.

Cuándo gana un candidato (docs/investigacion_metodos.md §5.8): gana en 6 de 7 partidos o más, la
diferencia es de 0,03 o más y su intervalo no incluye el cero, y todo eso se mantiene en las tres
condiciones y con las dos convenciones.

Para probar una versión nueva, añádela a `VERSIONES`.
"""

import argparse
import collections
import json
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import dfl  # noqa: E402
import possession_metrics as pm  # noqa: E402
from possession import candidates, pipeline, tracking  # noqa: E402
from starter import baseline  # noqa: E402

H, A, D, X = tracking.H, tracking.A, tracking.D, tracking.X
SEMILLA_BOOTSTRAP = 0
PERCENTILES = (5, 95)
EMPATE = 0.03  # por debajo de esta diferencia de spellF1, empate (§5.8)
MIN_PARTIDOS = 6  # de 7: en cuántos tiene que ganar un candidato
CONTROL = "control: voto ±50"

# Versiones que se puntúan. "control" es el baseline oficial; "pipeline" es possession.pipeline.run con
# esos parámetros del decodificador (None son los que trae por defecto).
VERSIONES = collections.OrderedDict([
    (CONTROL, {"tipo": "control", "ventana": 50}),
    ("Viterbi, coste 12", {"tipo": "pipeline", "params": {"switch": 12.0, "to_dead": 12.0, "from_dead": 12.0}}),
    ("Viterbi, coste 25 (v0)", {"tipo": "pipeline", "params": None}),
    ("Viterbi, coste 50", {"tipo": "pipeline", "params": {"switch": 50.0, "to_dead": 50.0, "from_dead": 50.0}}),
    ("Viterbi, coste 100", {"tipo": "pipeline", "params": {"switch": 100.0, "to_dead": 100.0, "from_dead": 100.0}}),
])


# -- el `D` oráculo y el control -----------------------------------------------------------------------

def d_oraculo(gt):
    """Evidencia con el `D` de las etiquetas: solo `D` donde hay `D`, y nunca `D` donde hay juego."""
    score, allowed = tracking.no_evidence(len(gt))
    allowed[gt == D, :2] = False
    allowed[(gt == H) | (gt == A), D] = False
    return score, allowed


def imponer_d(codes, gt, blocks):
    """El `D` de las etiquetas sobre una salida ya hecha, para tratar al control como a los candidatos.

    Donde la etiqueta es `D`, `D`. Donde hay juego y la salida decía `D`, el último equipo que había
    dicho (o el siguiente, al principio del tramo): es lo que hace el scorer con una `X`.
    """
    out = codes.copy()
    for a, b in blocks:
        w, g = out[a:b], gt[a:b]
        vivo = (g == H) | (g == A)
        w[g == D] = D
        falta = vivo & (w == D)
        conocido = vivo & (w != D)
        primeros = np.flatnonzero(conocido)
        if len(primeros) == 0:
            w[falta] = H
            continue
        ultimo = np.maximum.accumulate(np.where(conocido, np.arange(b - a), -1))
        ultimo[ultimo < 0] = primeros[0]
        w[falta] = w[ultimo[falta]]
    return out


def control(trk, ventana):
    """El baseline oficial: equipo del jugador más cercano y voto por mayoría de ±`ventana` frames."""
    letras = baseline.smooth(candidates.nearest_team(trk), ventana)
    codes = np.full(len(letras), X, dtype=np.int8)
    for a, b in trk.blocks:
        for code, letra in ((H, "H"), (A, "A"), (D, "D")):
            codes[a:b][letras[a:b] == letra] = code
    return codes


def ejecutar(version, trk, gt, modo_d):
    """Etiquetas de una versión sobre un `Tracking` de la DFL."""
    if version["tipo"] == "control":
        codes = control(trk, version["ventana"])
        return imponer_d(codes, gt, trk.blocks) if modo_d == "oraculo" else codes
    extra = [d_oraculo(gt)] if modo_d == "oraculo" else []
    return pipeline.run(trk, extra=extra, params=version["params"])


# -- puntuación ----------------------------------------------------------------------------------------

def contar(gt, pred):
    """Recuentos de un partido con el scorer oficial.

    `flags` tiene una fila por umbral de IoU y una columna por posesión real: True si se emparejó.
    """
    runs = pm.valid_runs(gt)
    filled = pm.fill_abstentions(pred, runs)
    reales = pm.possession_spells(gt, runs)
    predichas = pm.possession_spells(filled, runs)
    solapes = pm.spell_overlaps(reales, predichas)
    flags = np.vstack([pm.matched_gt_flags(solapes, len(reales), umbral) for umbral in pm.SPELL_IOUS])
    cm3 = pm.scored_confusion(pm.confusion(gt, pred))
    return {"flags": flags, "n_pred": len(predichas), "n_gt": len(reales),
            "macro_f1": float(pm.macro_f1(cm3)), "team_acc": float(pm.team_accuracy(cm3)[0])}


def spell_f1(flags, n_pred):
    """spellF1 medio sobre los umbrales, a partir de los emparejamientos. Igual que pm.spell_scores."""
    f1s = []
    for fila in flags:
        tp = int(fila.sum())
        fp, fn = n_pred - tp, len(fila) - tp
        f1s.append(2.0 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return float(np.mean(f1s))


def juntar(recuentos):
    """Los recuentos de varios partidos como si fueran uno. Vale porque ninguna posesión cruza partidos."""
    return np.hstack([r["flags"] for r in recuentos]), int(sum(r["n_pred"] for r in recuentos))


def diferencia_bootstrap(candidato, referencia, n_draws):
    """Intervalo de la diferencia de spellF1 (candidato − control), remuestreando las posesiones reales.

    Pareado: los dos se puntúan sobre el mismo remuestreo. Sigue el esquema de pm.bootstrap_spell_f1: el
    número de posesiones predichas se deja fijo y los falsos positivos no bajan de cero.
    """
    if not n_draws:
        return None
    (flags_c, pred_c), (flags_r, pred_r) = candidato, referencia
    n_gt = flags_c.shape[1]
    rng = np.random.RandomState(SEMILLA_BOOTSTRAP)

    def f1(flags, n_pred, picks):
        tp = flags[:, picks].sum(axis=1).astype(float)
        fp = np.maximum(0.0, n_pred - tp)
        fn = n_gt - tp
        return float(np.mean(np.where(tp > 0, 2.0 * tp / np.maximum(2 * tp + fp + fn, 1.0), 0.0)))

    difs = np.empty(n_draws)
    for draw in range(n_draws):
        picks = rng.randint(0, n_gt, n_gt)
        difs[draw] = f1(flags_c, pred_c, picks) - f1(flags_r, pred_r, picks)
    bajo, alto = np.percentile(difs, PERCENTILES)
    return [float(bajo), float(alto)]


def comprobar_formula(gt, pred, recuento):
    """El spellF1 de este fichero tiene que ser el del scorer oficial."""
    runs = pm.valid_runs(gt)
    oficial = pm.spell_scores(gt, pm.fill_abstentions(pred, runs), runs)["mean_f1"]
    propio = spell_f1(recuento["flags"], recuento["n_pred"])
    if abs(oficial - propio) > 1e-12:
        raise AssertionError("el spellF1 del harness ({}) no coincide con el oficial ({})".format(propio, oficial))


def resumir(por_partido, partidos, n_draws):
    """Agregados de cada versión en una condición y una convención, a partir de los recuentos por partido."""
    filas = collections.OrderedDict()
    referencia = [por_partido[(CONTROL, p)] for p in partidos]
    f1_ref = [spell_f1(r["flags"], r["n_pred"]) for r in referencia]
    for nombre in VERSIONES:
        recuentos = [por_partido[(nombre, p)] for p in partidos]
        f1s = [spell_f1(r["flags"], r["n_pred"]) for r in recuentos]
        flags, n_pred = juntar(recuentos)
        fila = {
            "spell_f1": spell_f1(flags, n_pred),
            "spell_f1_por_partido": dict(zip(partidos, f1s)),
            "macro_f1_medio": float(np.mean([r["macro_f1"] for r in recuentos])),
            "acierto_de_equipo_medio": float(np.mean([r["team_acc"] for r in recuentos])),
            "posesiones_predichas": n_pred,
            "posesiones_reales": int(flags.shape[1]),
        }
        if nombre != CONTROL:
            fila["diferencia"] = fila["spell_f1"] - filas[CONTROL]["spell_f1"]
            fila["diferencia_intervalo"] = diferencia_bootstrap((flags, n_pred), juntar(referencia), n_draws)
            fila["gana_en"] = int(sum(a > b for a, b in zip(f1s, f1_ref)))
        filas[nombre] = fila
    filas["Viterbi, coste elegido dejando un partido fuera"] = dejar_uno_fuera(por_partido, partidos, filas)
    return filas


def dejar_uno_fuera(por_partido, partidos, filas):
    """Para cada partido, la versión del pipeline que más saca en los otros; se puntúa en el que queda fuera."""
    candidatas = [n for n, v in VERSIONES.items() if v["tipo"] == "pipeline"]
    if len(partidos) < 2 or not candidatas:
        return None
    elegidas, recuentos = [], []
    for fuera in partidos:
        resto = [p for p in partidos if p != fuera]
        mejor = max(candidatas, key=lambda n: (spell_f1(*juntar([por_partido[(n, p)] for p in resto])),
                                               -candidatas.index(n)))
        elegidas.append(mejor)
        recuentos.append(por_partido[(mejor, fuera)])
    flags, n_pred = juntar(recuentos)
    f1 = spell_f1(flags, n_pred)
    return {"spell_f1": f1, "diferencia": f1 - filas[CONTROL]["spell_f1"],
            "elegidas": dict(collections.Counter(elegidas)),
            "posesiones_predichas": n_pred, "posesiones_reales": int(flags.shape[1])}


def medir(partidos, modo_d, n_draws, avisar=None):
    """{convención: {condición: {versión: agregados}}} y los recuentos de etiquetas de cada partido."""
    recuentos = collections.defaultdict(dict)  # (convención, condición) -> {(versión, partido): recuento}
    perfil = collections.OrderedDict()
    comprobado = False
    for partido in partidos:
        inicio = time.time()
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        perfil[partido] = {c: {"frames_H": int(np.sum(gt[c] == H)), "frames_A": int(np.sum(gt[c] == A)),
                               "frames_D": int(np.sum(gt[c] == D)),
                               "posesiones": len(pm.possession_spells(gt[c], pm.valid_runs(gt[c])))}
                           for c in dfl.CONVENCIONES}
        for condicion in dfl.CONDICIONES:
            trk = dfl.tracking_de(cargado, condicion)
            visible = ~np.isnan(trk.bx)
            vivo = (gt["flag"] == H) | (gt["flag"] == A)
            perfil[partido].setdefault("balon_visible_en_juego_pct", {})[condicion] = round(
                100.0 * float(np.mean(visible[vivo])), 1)
            for nombre, version in VERSIONES.items():
                # El `D` es el mismo en las dos convenciones: una sola ejecución sirve para las dos.
                pred = ejecutar(version, trk, gt["flag"], modo_d)
                for convencion in dfl.CONVENCIONES:
                    recuento = contar(gt[convencion], pred)
                    if not comprobado:
                        comprobar_formula(gt[convencion], pred, recuento)
                        comprobado = True
                    recuentos[(convencion, condicion)][(nombre, partido)] = recuento
        if avisar:
            avisar("hecho {} en {:.0f} s".format(partido, time.time() - inicio))
    salida = collections.OrderedDict()
    for convencion in dfl.CONVENCIONES:
        salida[convencion] = collections.OrderedDict(
            (condicion, resumir(recuentos[(convencion, condicion)], partidos, n_draws))
            for condicion in dfl.CONDICIONES)
    return salida, perfil


# -- salida --------------------------------------------------------------------------------------------

def num(valor, signo=False):
    if valor is None:
        return "–"
    return ("{:+.3f}" if signo else "{:.3f}").format(valor).replace(".", ",")


def veredicto(salida, nombre, n_partidos):
    """¿Gana `nombre` al control con la regla de §5.8? Mira todas las condiciones y convenciones."""
    filas = [salida[c][k][nombre] for c in salida for k in salida[c]]
    gana = all(f["diferencia"] >= EMPATE and f["gana_en"] >= min(MIN_PARTIDOS, n_partidos)
               and (f["diferencia_intervalo"] is None or f["diferencia_intervalo"][0] > 0) for f in filas)
    pierde = all(f["diferencia"] <= -EMPATE for f in filas)
    return "gana" if gana else "pierde" if pierde else "empate o no concluye"


def tabla_perfil(perfil):
    """Cómo son las etiquetas y el balón de los partidos medidos, todos juntos."""
    lineas = ["### Con qué se mide", "", "| etiquetas | posesiones | frames `D` |", "|---|---|---|"]
    for convencion in dfl.CONVENCIONES:
        filas = [p[convencion] for p in perfil.values()]
        frames = sum(f["frames_H"] + f["frames_A"] + f["frames_D"] for f in filas)
        lineas.append("| {} | {} | {:.1f} % |".format(
            convencion, sum(f["posesiones"] for f in filas),
            100.0 * sum(f["frames_D"] for f in filas) / max(frames, 1)).replace(".", ","))
    lineas += ["", "| balón | visible en los frames de juego (media de los partidos) |", "|---|---|"]
    for condicion in dfl.CONDICIONES:
        media = float(np.mean([p["balon_visible_en_juego_pct"][condicion] for p in perfil.values()]))
        lineas.append("| {} | {:.1f} % |".format(condicion, media).replace(".", ","))
    lineas.append("")
    return "\n".join(lineas)


def tablas(salida, partidos):
    lineas = []
    for convencion, por_condicion in salida.items():
        lineas.append("### Etiquetas: {}".format(convencion))
        lineas.append("")
        lineas.append("| balón | versión | spellF1, {} partidos | por partido, mín–máx | frente al control "
                      "[5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |".format(len(partidos)))
        lineas.append("|---|---|---|---|---|---|---|---|")
        for condicion, filas in por_condicion.items():
            for nombre, f in filas.items():
                if f is None:
                    continue
                if "elegidas" in f:
                    lineas.append("| {} | {} | {} | – | {} | – | {} / {} | – |".format(
                        condicion, nombre, num(f["spell_f1"]), num(f["diferencia"], True),
                        f["posesiones_predichas"], f["posesiones_reales"]))
                    continue
                valores = list(f["spell_f1_por_partido"].values())
                if nombre == CONTROL:
                    frente, gana = "–", "–"
                else:
                    intervalo = f["diferencia_intervalo"]
                    frente = num(f["diferencia"], True) + (
                        " [{} a {}]".format(num(intervalo[0], True), num(intervalo[1], True)) if intervalo else "")
                    gana = "{} de {}".format(f["gana_en"], len(partidos))
                lineas.append("| {} | {} | {} | {}–{} | {} | {} | {} / {} | {} |".format(
                    condicion, nombre, num(f["spell_f1"]), num(min(valores)), num(max(valores)), frente, gana,
                    f["posesiones_predichas"], f["posesiones_reales"], num(f["acierto_de_equipo_medio"])))
        lineas.append("")
    lineas.append("### Regla de §5.8 (todas las condiciones y las dos convenciones)")
    lineas.append("")
    for nombre, version in VERSIONES.items():
        if version["tipo"] == "pipeline":
            lineas.append("- {}: **{}**".format(nombre, veredicto(salida, nombre, len(partidos))))
    return "\n".join(lineas)


def main():
    parser = argparse.ArgumentParser(description="Puntúa el pipeline en los partidos abiertos de la DFL.")
    parser.add_argument("--partidos", nargs="+", default=list(dfl.PARTIDOS), choices=list(dfl.PARTIDOS))
    parser.add_argument("--d", choices=("oraculo", "propio"), default="oraculo",
                        help="de dónde sale el D: de las etiquetas (por defecto) o de cada versión")
    parser.add_argument("--bootstrap", type=int, default=1000, help="remuestreos del intervalo; 0 lo quita")
    parser.add_argument("--json", action="store_true", help="imprime la salida completa en JSON")
    args = parser.parse_args()

    salida, perfil = medir(args.partidos, args.d, args.bootstrap,
                           avisar=lambda texto: print(texto, file=sys.stderr))
    if args.json:
        print(json.dumps({"d": args.d, "partidos": args.partidos, "perfil": perfil, "resultados": salida},
                         ensure_ascii=False, indent=1))
        return
    print("D: {} · partidos: {} · bootstrap: {}".format(args.d, len(args.partidos), args.bootstrap))
    if args.d == "propio":
        print("AVISO: con el D propio, el balón tapado en los D de la DFL delata la etiqueta. No decide nada.")
    print()
    print(tabla_perfil(perfil))
    print(tablas(salida, args.partidos))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
