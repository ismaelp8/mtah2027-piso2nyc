"""Sondeo P4: quitar los slots sobrantes («el más nuevo», `ball.clean_slots`) en la DFL con slots como los del partido.

    python validation/investigacion_1116/slots_dfl.py [--bootstrap 1000]

Datos abiertos de otros partidos: los 7 de la DFL (Bassek et al., 2025, CC BY 4.0) y, para comprobar que no cambia
nada, la mitad de entrenamiento de SkillCorner (licencia MIT). Lo puede ejecutar cualquiera, Claude incluido. Solo
imprime agregados. La regla, la degradación y su calibración están en BITACORA.md (P4), escritas antes de medir; la
calibración sale solo de agregados del partido entero (P3 y el perfil del ATD), nunca de la ventana pública.
"""

import argparse
import collections
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
for carpeta in (AQUI, os.path.join(ROOT, "validation", "harness"), os.path.join(ROOT, "validation", "skillcorner"),
                os.path.join(ROOT, "validation", "apuesta_b"), os.path.join(ROOT, "validation", "partido"), ROOT,
                os.path.join(ROOT, "evaluation")):
    sys.path.insert(0, carpeta)
import cambio_antes_de_parada as cap  # noqa: E402  (VERSIONES y MODOS: tapado / a la vista)
import dfl  # noqa: E402
import lector as lc  # noqa: E402
import puntuar  # noqa: E402
import slots_sobrantes as ss  # noqa: E402  (validation/partido/slots_sobrantes.py: describir es pura)
from possession import ball  # noqa: E402

H, A = dfl.H, dfl.A
SEMILLA = 20261116
# Calibración (BITACORA.md P4), de agregados del partido entero:
MEDIANA_TRAMO_S = 35.5  # «tramo p50» de los slots del ATD (validation/resultados/2026-11-14_apuesta_b.md)
FRACCION = 0.129  # frames evaluados con sobrantes (P3)
CLASES = ((31, 1, 22), (52, 25, 92), (42, 125, 435), (5, 750, 1354))  # (rachas en P3, frames mín, frames máx)
P_LOCAL = 12896 / (12896 + 7504.0)  # P3: frames con sobrantes solo del local frente a solo del visitante
DESFASE_S = (180, 600)  # el fantasma copia a un jugador de su equipo de entre 3 y 10 minutos antes o después
COLUMNAS_FANTASMA = 2  # por equipo
PARTIDO = {  # P3, para la comprobación (no se ajusta nada con esto)
    "con sobrantes": 12.9, "más adentro de 2 m": 84.5, "más de 1 m fuera": 5.5, "velocidad 0,5–2 m/s": 45.1,
    "compañero a menos de 0,5 m": 1.1, "compañero a más de 3 m": 78.6, "jugador más cercano a 3–15 m": 58.8,
    "balón a 10–30 m": 32.0, "lleva visto menos de 5 s": 51.9}


def rachas(m):
    borde = np.diff(np.concatenate(([0], m.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(borde == 1), np.flatnonzero(borde == -1)))


def cortar_tracklets(trk, rng):
    """Cada racha de presencia de cada slot se corta en trozos de duración exponencial (mediana MEDIANA_TRAMO_S) y
    cada trozo pasa a un slot del mismo equipo libre desde al menos un frame antes: el jugador sigue, su slot es nuevo."""
    escala = MEDIANA_TRAMO_S / np.log(2.0) * trk.fps
    px, py = np.asarray(trk.px), np.asarray(trk.py)
    presente = np.isfinite(px) & np.isfinite(py)
    n = len(px)
    trozos, equipos = [], []
    for k in (H, A):
        libre = []  # por columna nueva: el primer frame en que está libre (fin del último trozo + 1)
        for j in np.flatnonzero(np.asarray(trk.team) == k):
            for a, b in rachas(presente[:, j]):
                t = a
                while t < b:
                    fin = min(b, t + max(1, int(rng.exponential(escala))))
                    destino = next((c for c, f in enumerate(libre) if f < t), None)
                    if destino is None:
                        libre.append(0)
                        destino = len(libre) - 1
                    libre[destino] = fin + 1
                    trozos.append((k, destino, j, t, fin))
                    t = fin
        equipos.append(len(libre))
    columnas = {k: np.arange(equipos[k]) + (0 if k == H else equipos[H]) for k in (H, A)}
    nx = np.full((n, sum(equipos)), np.nan, dtype=np.float32)
    ny = np.full((n, sum(equipos)), np.nan, dtype=np.float32)
    for k, destino, j, a, b in trozos:
        c = columnas[k][destino]
        nx[a:b, c], ny[a:b, c] = px[a:b, j], py[a:b, j]
    team = np.repeat(np.array([H, A], dtype=np.int8), equipos)
    return trk._replace(px=nx, py=ny, team=team)


def anadir_fantasmas(trk, rng):
    """(tracking con fantasmas, máscara de las columnas fantasma). Rachas de un slot de más hasta cubrir FRACCION de
    los frames de los tramos; el fantasma copia a un jugador real de su equipo de otro momento del mismo tramo."""
    px, py = np.asarray(trk.px), np.asarray(trk.py)
    team = np.asarray(trk.team)
    presente = np.isfinite(px) & np.isfinite(py)
    n = len(px)
    gx = np.full((n, 2 * COLUMNAS_FANTASMA), np.nan, dtype=np.float32)
    gy = np.full((n, 2 * COLUMNAS_FANTASMA), np.nan, dtype=np.float32)
    gteam = np.repeat(np.array([H, A], dtype=np.int8), COLUMNAS_FANTASMA)
    ocupado = np.zeros((2 * COLUMNAS_FANTASMA, n), dtype=bool)
    cubierto = np.zeros(n, dtype=bool)
    tramos = list(trk.blocks)
    largos = np.array([b - a for a, b in tramos], dtype=float)
    objetivo = FRACCION * largos.sum()
    pesos = np.array([c[0] for c in CLASES], dtype=float)
    intentos = 0
    while cubierto.sum() < objetivo and intentos < 100000:
        intentos += 1
        _, lo, hi = CLASES[rng.choice(len(CLASES), p=pesos / pesos.sum())]
        largo = int(rng.integers(lo, hi + 1))
        a, b = tramos[rng.choice(len(tramos), p=largos / largos.sum())]
        if b - a <= largo:
            continue
        inicio = int(rng.integers(a, b - largo))
        k = H if rng.random() < P_LOCAL else A
        col = next((c for c in np.flatnonzero(gteam == k)
                    if not ocupado[c, max(0, inicio - 1):inicio + largo + 1].any()), None)
        if col is None:
            continue
        desfase = int(rng.uniform(*DESFASE_S) * trk.fps) * (1 if rng.random() < 0.5 else -1)
        origen = inicio + desfase
        if origen < a or origen + largo > b:
            origen = inicio - desfase
            if origen < a or origen + largo > b:
                continue
        candidatos = [j for j in np.flatnonzero(team == k) if presente[origen:origen + largo, j].all()]
        if not candidatos:
            continue
        j = candidatos[int(rng.integers(len(candidatos)))]
        gx[inicio:inicio + largo, col] = px[origen:origen + largo, j]
        gy[inicio:inicio + largo, col] = py[origen:origen + largo, j]
        ocupado[col, inicio:inicio + largo] = True
        cubierto[inicio:inicio + largo] = True
    # Columnas barajadas, para que el índice no delate al fantasma (el empate de clean_slots mira el índice).
    orden = rng.permutation(px.shape[1] + gx.shape[1])
    nx = np.hstack([px, gx])[:, orden]
    ny = np.hstack([py, gy])[:, orden]
    nteam = np.concatenate([team, gteam])[orden]
    fantasma = np.concatenate([np.zeros(px.shape[1], bool), np.ones(gx.shape[1], bool)])[orden]
    return trk._replace(px=nx, py=ny, team=nteam), fantasma


def degradar(trk, indice):
    rng = np.random.default_rng([SEMILLA, indice])
    cortado = cortar_tracklets(trk, rng)
    con, fantasma = anadir_fantasmas(cortado, rng)
    return puntuar.solo_lectura(cortado), puntuar.solo_lectura(con), fantasma


def sumar_descripcion(total, r):
    for clave, valor in r.items():
        if isinstance(valor, list) and valor and isinstance(valor[0], (int, np.integer)):
            total[clave] = [a + b for a, b in zip(total.get(clave, [0] * len(valor)), valor)]
        elif isinstance(valor, (int, np.integer)):
            total[clave] = total.get(clave, 0) + int(valor)
    return total


def calibracion(d):
    m = float(d["muestras"])
    return {"con sobrantes": 100.0 * d["con_sobrantes"] / d["evaluados"],
            "más adentro de 2 m": 100.0 * d["sitio"][4] / m, "más de 1 m fuera": 100.0 * d["fuera_1m"] / m,
            "velocidad 0,5–2 m/s": 100.0 * d["velocidad"][1] / m, "compañero a menos de 0,5 m": 100.0 * d["companero"][0] / m,
            "compañero a más de 3 m": 100.0 * d["companero"][3] / m,
            "jugador más cercano a 3–15 m": 100.0 * d["cualquiera"][1] / m,
            "balón a 10–30 m": 100.0 * d["balon"][2] / m,
            "lleva visto menos de 5 s": 100.0 * (d["edad"][0] + d["edad"][1]) / m}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bootstrap", type=int, default=1000)
    args = ap.parse_args()
    version = puntuar.leer_versiones(cap.VERSIONES)[0]["main: B5 y coste 25"]
    arreglo = dict(version)
    arreglo["piezas"] = {"ball": ball.clean_slots}
    rec = collections.defaultdict(list)  # (D, convención, condición o modo, versión) -> recuentos por partido
    descripcion, acierto = {}, np.zeros(2, dtype=np.int64)
    identidad = {"DFL sin degradar": 0, "DFL con los tracklets cortados": 0, "SkillCorner": 0}
    for partido in dfl.PARTIDOS:
        t0 = time.time()
        cargado = dfl.cargar(partido)
        gt = cargado["gt"]
        indice = cargado["indice"]
        for cond in dfl.VOTAN:
            base = puntuar.solo_lectura(dfl.tracking_de(cargado, cond))
            identidad["DFL sin degradar"] += int(ball.surplus_slots(base).sum())
            cortado, con, fantasma = degradar(base, indice)
            identidad["DFL con los tracklets cortados"] += int(ball.surplus_slots(cortado).sum())
            if cond == dfl.VOTAN[0]:
                sumar_descripcion(descripcion, ss.describir(con, gt["flag"]))
                sobra = ball.surplus_slots(con)
                acierto += [int(sobra[:, fantasma].sum()), int(sobra.sum())]
            preds = {"A": puntuar.ejecutar(version, cortado, gt["flag"], "oraculo", partido),
                     "B": puntuar.ejecutar(version, con, gt["flag"], "oraculo", partido),
                     "C": puntuar.ejecutar(arreglo, con, gt["flag"], "oraculo", partido)}
            for conv in dfl.CONVENCIONES:
                for v, p in preds.items():
                    rec[("etiquetas", conv, cond, v)].append(puntuar.contar(gt[conv], p))
        for modo, hacer in cap.MODOS.items():
            base = puntuar.solo_lectura(hacer(cargado, dfl.VOTAN[0]))
            cortado, con, _ = degradar(base, indice)
            preds = {"A": puntuar.ejecutar(version, cortado, gt["flag"], "propio", partido),
                     "B": puntuar.ejecutar(version, con, gt["flag"], "propio", partido),
                     "C": puntuar.ejecutar(arreglo, con, gt["flag"], "propio", partido)}
            for conv in dfl.CONVENCIONES:
                for v, p in preds.items():
                    rec[("propio", conv, modo, v)].append(puntuar.contar(gt[conv], p))
        print("DFL {} en {:.0f} s".format(partido, time.time() - t0), file=sys.stderr, flush=True)
    ids = list(lc.ENTRENAMIENTO)
    lc.exigir_solo_entrenamiento(ids)
    for id_ in ids:
        trk, _ = lc.tracking_de(lc.leer_crudo(id_), "detectado", id_)
        identidad["SkillCorner"] += int(ball.surplus_slots(trk).sum())

    print("## Comprobación de la degradación (P3 en el partido frente a la DFL degradada, «como el ATD»; sin regla)\n")
    print("| medida (%) | partido | DFL degradada |")
    print("|---|---|---|")
    cal = calibracion(descripcion)
    for clave, valor in PARTIDO.items():
        print("| {} | {:.1f} | {:.1f} |".format(clave, valor, cal[clave]))
    print("\nDe lo que quita `clean_slots` en la DFL degradada, es el fantasma: {:.1f} % ({} de {} slots × frame)".format(
        100.0 * acierto[0] / max(acierto[1], 1), acierto[0], acierto[1]))
    print("\nSlots que quitaría sin fantasmas (tiene que ser 0): " + ", ".join(
        "{} {}".format(k, v) for k, v in identidad.items()))

    print("\n## spellF1. A: tracklets cortados; B: más fantasmas; C: B con `clean_slots`\n")
    print("| `D` | etiquetas | condición o balón en los `D` | A | B | C | B − A | C − B [5–95 %] · gana en | recupera |")
    print("|---|---|---|---|---|---|---|---|---|")
    celdas = []
    for clave in sorted({k[:3] for k in rec}, key=lambda k: (k[0] != "etiquetas", k[1], k[2])):
        f = {v: puntuar.spell_f1(*puntuar.juntar(rec[clave + (v,)])) for v in "ABC"}
        intervalo = puntuar.diferencia_bootstrap(puntuar.juntar(rec[clave + ("C",)]), puntuar.juntar(rec[clave + ("B",)]),
                                                 args.bootstrap)
        gana = sum(puntuar.spell_f1(c["flags"], c["n_pred"]) > puntuar.spell_f1(b["flags"], b["n_pred"])
                   for c, b in zip(rec[clave + ("C",)], rec[clave + ("B",)]))
        perdida, ganancia = f["A"] - f["B"], f["C"] - f["B"]
        recupera = ganancia / perdida if perdida > 0 else float("nan")
        celdas.append((clave, perdida, ganancia, recupera, intervalo, gana))
        print("| {} | {} | {} | {:.3f} | {:.3f} | {:.3f} | {:+.3f} | {:+.3f} {} · {} de 7 | {} |".format(
            clave[0], clave[1], clave[2], f["A"], f["B"], f["C"], -perdida, ganancia,
            "[{:+.3f} a {:+.3f}]".format(*intervalo) if intervalo else "", gana,
            "–" if perdida <= 0 else "{:.0f} %".format(100 * recupera)))

    print("\n## Regla de P4\n")
    dano = [c for c in celdas if c[1] >= 0.010]
    if not dano:
        print("→ Los fantasmas no hacen daño (B pierde menos de 0,010 frente a A en todas las celdas): se cierra.")
        return
    recupera = all(c[2] >= 0.5 * c[1] for c in dano)
    no_pierde = all(c[2] >= -0.005 for c in celdas)
    identico = all(v == 0 for v in identidad.values())
    print("- hacen daño en {} de {} celdas".format(len(dano), len(celdas)))
    print("- recupera la mitad o más en todas esas: {}".format("sí" if recupera else "NO"))
    print("- no pierde más de 0,005 frente a B en ninguna celda: {}".format("sí" if no_pierde else "NO"))
    print("- sin fantasmas no cambia nada: {}".format("sí" if identico else "NO"))
    print("→ {}".format("EL ARREGLO PASA" if recupera and no_pierde and identico else "EL ARREGLO NO PASA"))
    s58 = [c for c in celdas if c[0][0] == "etiquetas"]
    pasa58 = all(c[2] >= 0.03 and c[4] and c[4][0] > 0 and c[5] >= 6 for c in s58)
    print("§5.8 de C frente a B (el `D` de las etiquetas, las dos condiciones y las dos convenciones): {}".format(
        "gana" if pasa58 else "no gana"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
