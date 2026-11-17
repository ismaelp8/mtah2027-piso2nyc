"""El detalle de los cambios y de las posesiones, en los datos abiertos, para `main`, K2 y K3. Descriptivo.

    python validation/conjunto/detalle_abiertos.py [--procesos 3]

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, mitad de entrenamiento, MIT; Metrica sample-data). Lo
puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. No lee el examen de SkillCorner.

Es el análisis de `notebooks/ventana_publica_detalle.ipynb` (David, 17/11; rama `feat/encender-k2`), que mira una
entrega frente a los 5 minutos
públicos del partido (17 posesiones), repetido donde hay miles de posesiones con etiquetas: los 7 partidos de la DFL
(con control y con el flag), los 10 de entrenamiento de SkillCorner y los 3 de Metrica. Las cuentas son las suyas, con
las funciones del scorer oficial (`evaluation/possession_metrics.py`):

- **los cambios:** un cambio real se empareja con uno nuestro hacia el mismo estado a ±25 frames (1 s), como el
  transF1 oficial. Los emparejados son los «vistos», con su retraso (positivo, llegamos tarde); los reales sin pareja,
  los «no vistos»; los nuestros sin pareja, los que «nos sobran»;
- **las posesiones:** una real está «encontrada» si se empareja con una nuestra con un solape de 0,5 o más. Si no, la
  causa, en este orden: la tapamos con `D` (la mitad o más de sus frames) · «otro equipo»: decimos el bueno en menos
  de la mitad de sus frames (con el `D` de las etiquetas, el resto es el rival; con el propio, el rival o `D`) ·
  decimos el bueno, pero la nuestra es más larga (se funde con la de al lado) · la nuestra es más corta o va partida.

Las tres versiones se montan como en `refinar.py`, con el pliegue que no vio cada partido: `main` (B5), K2 y K3 (la
mezcla a partes iguales). Balón: la primera condición que vota de cada dominio. `D`: el propio (como en la entrega) y
el de las etiquetas (para ver solo la evidencia de equipo). No decide nada: sirve para saber si lo que se ve en la
ventana pública se repite donde hay datos, y qué cambia con cada versión.
"""

import argparse
import collections
import concurrent.futures
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import refinar  # noqa: E402  (pone en el camino harness/, cambios/, apuesta_b/, skillcorner/ y la raíz)
import medir  # noqa: E402
import cj_comun as cj  # noqa: E402
import lector  # noqa: E402  (validation/skillcorner/lector.py)
from comun import dfl, puntuar  # noqa: E402
from possession import aprendida, conjunto  # noqa: E402
from possession import refinamientos as rf  # noqa: E402

pm = puntuar.pm
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FPS = 25
TOLERANCIA = 25  # frames: como el notebook y el transF1 oficial
UMBRAL = 0.5
VERSIONES = ("main", "K2", "K3")
MODOS = ("propio", "oraculo")
TRAMOS = (0.0, 1.0, 2.0, 5.0, 10.0, 1e9)
NOMBRES = ("< 1 s", "1–2 s", "2–5 s", "5–10 s", "≥ 10 s")
CAUSAS = ("encontrada", "la tapamos con D", "otro equipo", "la nuestra es más larga",
          "la nuestra es más corta o va partida")
H, A, D = pm.LABELS.index("H"), pm.LABELS.index("A"), pm.LABELS.index("D")


def _entre_equipos(cambio):
    return cambio[1] in (H, A) and cambio[2] in (H, A)


def detalle(gt, pred):
    """Los recuentos de un partido: {clave: número o array}, que se suman entre partidos."""
    runs = pm.valid_runs(gt)
    llenado = pm.fill_abstentions(pred, runs)
    r = collections.Counter()

    reales, nuestros = pm.transitions(gt, runs), pm.transitions(llenado, runs)
    parejas, perdidos, sobrantes = pm.match_transitions(reales, nuestros, TOLERANCIA)
    retrasos = {}
    for clase, filtro in (("todos", lambda c: True), ("equipos", _entre_equipos)):
        r["cambios reales", clase] = sum(1 for c in reales if filtro(c))
        r["cambios nuestros", clase] = sum(1 for c in nuestros if filtro(c))
        r["vistos", clase] = sum(1 for real, _ in parejas if filtro(real))
        r["no vistos", clase] = sum(1 for c in perdidos if filtro(c))
        r["nos sobran", clase] = sum(1 for c in sobrantes if filtro(c))
    retrasos["todos"] = [mio[0] - real[0] for real, mio in parejas]

    pos_reales, pos_nuestras = pm.possession_spells(gt, runs), pm.possession_spells(llenado, runs)
    solapes = pm.spell_overlaps(pos_reales, pos_nuestras)
    encontrada = pm.matched_gt_flags(solapes, len(pos_reales), UMBRAL)
    casada = np.zeros(len(pos_nuestras), dtype=bool)
    usada = np.zeros(len(pos_reales), dtype=bool)
    for iou, i, j in solapes:
        if iou >= UMBRAL and not usada[i] and not casada[j]:
            usada[i] = casada[j] = True
    r["posesiones reales"], r["posesiones nuestras"] = len(pos_reales), len(pos_nuestras)
    r["frames reales"] = sum(b - a for a, b, _ in pos_reales)
    r["frames nuestros"] = sum(b - a for a, b, _ in pos_nuestras)
    r["nuestras sin pareja"] = int(np.sum(~casada))
    for (a, b, k), ok in zip(pos_reales, encontrada):
        dentro = llenado[a:b]
        if ok:
            causa = CAUSAS[0]
        elif np.mean(dentro == D) >= 0.5:
            causa = CAUSAS[1]
        elif np.mean(dentro == k) < 0.5:
            causa = CAUSAS[2]
        else:
            mejor, comun = None, 0
            for c, d, e in pos_nuestras:
                n = min(b, d) - max(a, c)
                if e == k and n > comun:
                    mejor, comun = (c, d), n
            causa = CAUSAS[3] if mejor and (mejor[1] - mejor[0]) > (b - a) else CAUSAS[4]
        tramo = int(np.searchsorted(TRAMOS, (b - a) / float(FPS), side="right") - 1)
        r["causa", causa] += 1
        r["tramo", tramo, "reales"] += 1
        r["tramo", tramo, causa] += 1
    return dict(r), {k: np.asarray(v, dtype=np.int64) for k, v in retrasos.items()}


def _etiquetas(piezas, s_k2, s_b5, modo):
    def decodificar(s):
        mio = aprendida.puntuacion_de("b5", s, piezas["visible"], 1.0, piezas["cercano"])
        return medir._decodificar(piezas, mio, modo)

    return {"main": medir._decodificar(piezas, piezas["b5"], modo), "K2": decodificar(s_k2),
            "K3": decodificar(rf.mezclar(s_k2, s_b5))}


def _de_un_tracking(trk, gts, pliegue_k2, alfa_k2, pliegue_b5):
    piezas = medir._piezas(puntuar.solo_lectura(trk), next(iter(gts.values())), pliegue_b5)
    limpio = piezas["limpio"]
    s_k2 = alfa_k2 * conjunto.salidas(limpio, pliegue_k2)[0]
    s_b5 = rf.logit_b5(limpio, pliegue_b5)
    salida = {}
    for modo in MODOS:
        for version, pred in _etiquetas(piezas, s_k2, s_b5, modo).items():
            for convencion, gt in gts.items():
                salida[(convencion, modo, version)] = detalle(gt, pred)
    return salida


def _trabajo(trabajo):
    dominio, partido = trabajo
    inicio = time.time()
    if dominio == "dfl":
        cargado = dfl.cargar(partido)
        gts = collections.OrderedDict((("DFL, control", cargado["gt"]["control"]), ("DFL, flag", cargado["gt"]["flag"])))
        # el `D` de las etiquetas es el mismo en las dos convenciones: `medir._piezas` lo toma de la primera
        salida = _de_un_tracking(dfl.tracking_de(cargado, dfl.VOTAN[0]), gts, partido,
                                 conjunto.pesos(partido)["alfa"], partido)
    elif dominio == "sc":
        lector.exigir_solo_entrenamiento([partido])
        trk, gt = lector.tracking_de(lector.leer_crudo(partido), lector.VOTAN[0], partido)
        salida = _de_un_tracking(trk, {"SkillCorner, entrenamiento": gt}, cj.pliegue_de("sc", partido),
                                 conjunto.pesos(None)["alfa"], None)
    else:
        lc = refinar.lector_metrica()
        trk, gt = lc.tracking_de(lc.leer(partido), lc.VOTAN[0], partido)
        salida = _de_un_tracking(trk, {"Metrica": gt}, None, conjunto.pesos(None)["alfa"], None)
    return trabajo, salida, time.time() - inicio


def pct(parte, total):
    return "{:.1f} %".format(100.0 * parte / total) if total else "–"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--procesos", type=int, default=2)
    args = parser.parse_args()
    lc = refinar.lector_metrica()
    trabajos = ([("dfl", p) for p in cj.DFL] + [("sc", p) for p in cj.SKILLCORNER]
                + [("metrica", p) for p in lc.partidos()])
    cuentas = collections.defaultdict(collections.Counter)
    retrasos = collections.defaultdict(lambda: collections.defaultdict(list))
    partidos = collections.Counter()
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for (dominio, partido), salida, segundos in pool.map(_trabajo, trabajos):
            for clave, (recuento, retraso) in salida.items():
                cuentas[clave].update(recuento)
                for clase, valores in retraso.items():
                    retrasos[clave][clase].append(valores)
                if clave[1] == MODOS[0] and clave[2] == VERSIONES[0]:
                    partidos[clave[0]] += 1
            print("# hecho {} {} en {:.0f} s".format(dominio, partido, segundos), file=sys.stderr, flush=True)

    print("# El detalle de los cambios y de las posesiones en los datos abiertos (descriptivo)\n")
    print("Código: {} · este script: sha256 {}… · cuentas de `notebooks/ventana_publica_detalle.ipynb` con el scorer oficial · cambios emparejados "
          "a ±{} frames · posesiones encontradas con un solape de {} o más · cada partido con el pliegue que no lo vio."
          .format(puntuar.version_del_codigo(), refinar.huella(os.path.abspath(__file__)), TOLERANCIA, UMBRAL))
    datos = [d for d in ("DFL, control", "DFL, flag", "SkillCorner, entrenamiento", "Metrica") if partidos[d]]
    for modo in MODOS:
        print("\n## Con el `D` {}\n".format("propio (como en la entrega)" if modo == "propio" else "de las etiquetas"))
        print("### Los cambios\n")
        print("| datos | versión | cambios reales | vistos | no vistos | nos sobran | retraso de los vistos: mediana / "
              "media (frames) | vistos a 12 frames o menos | entre equipos: reales | vistos | nos sobran |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for dato in datos:
            for version in VERSIONES:
                c = cuentas[(dato, modo, version)]
                r = np.concatenate(retrasos[(dato, modo, version)]["todos"])
                print("| {} ({}) | {} | {} | {} ({}) | {} | {} | {:+.0f} / {:+.1f} | {} | {} | {} ({}) | {} |".format(
                    dato, partidos[dato], version, c["cambios reales", "todos"], c["vistos", "todos"],
                    pct(c["vistos", "todos"], c["cambios reales", "todos"]), c["no vistos", "todos"],
                    c["nos sobran", "todos"], float(np.median(r)) if len(r) else 0.0,
                    float(np.mean(r)) if len(r) else 0.0, pct(int(np.sum(np.abs(r) <= 12)), len(r)),
                    c["cambios reales", "equipos"], c["vistos", "equipos"],
                    pct(c["vistos", "equipos"], c["cambios reales", "equipos"]), c["nos sobran", "equipos"]))
        print("\n### Las posesiones\n")
        print("| datos | versión | reales | nuestras | encontradas | {} | nuestras sin pareja | duración media: real / "
              "nuestra (s) |".format(" | ".join(CAUSAS[1:])))
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for dato in datos:
            for version in VERSIONES:
                c = cuentas[(dato, modo, version)]
                n = c["posesiones reales"]
                print("| {} | {} | {} | {} | {} ({}) | {} | {} | {:.1f} / {:.1f} |".format(
                    dato, version, n, c["posesiones nuestras"], c["causa", CAUSAS[0]], pct(c["causa", CAUSAS[0]], n),
                    " | ".join("{} ({})".format(c["causa", causa], pct(c["causa", causa], n)) for causa in CAUSAS[1:]),
                    c["nuestras sin pareja"], c["frames reales"] / float(FPS) / max(n, 1),
                    c["frames nuestros"] / float(FPS) / max(c["posesiones nuestras"], 1)))
        print("\n### Por duración de la posesión real: encontradas, y perdidas por decir el otro equipo\n")
        print("| datos | duración | reales | {} |".format(" | ".join(
            "{}: encontradas / otro equipo".format(v) for v in VERSIONES)))
        print("|---|---|---|" + "---|" * len(VERSIONES))
        for dato in datos:
            for k, nombre in enumerate(NOMBRES):
                n = cuentas[(dato, modo, VERSIONES[0])]["tramo", k, "reales"]
                print("| {} | {} | {} | {} |".format(dato, nombre, n, " | ".join(
                    "{} / {}".format(pct(cuentas[(dato, modo, v)]["tramo", k, CAUSAS[0]], n),
                                     pct(cuentas[(dato, modo, v)]["tramo", k, CAUSAS[2]], n)) for v in VERSIONES)))


if __name__ == "__main__":
    main()
