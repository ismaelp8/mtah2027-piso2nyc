"""¿Cuánto dependen los números de Metrica de dónde se pone la parada? Comprobaciones de la revisión.

    python validation/metrica/sensibilidad_paradas.py [--bootstrap 1000]

Datos abiertos de otros partidos (ver `lector.py`): lo puede ejecutar cualquiera, Claude incluido. Solo
imprime agregados. **Se escribió después de ver la medida** (`BITACORA.md` §8): no cambia la regla de §3 ni
decide nada. No toca la caché: cambia las etiquetas en memoria.

1. Cuánto dura cada evento que para el juego. La regla de §3 pone la parada en su frame de inicio.
2. Cuántos saques (`SET PIECE`) llegan con la etiqueta todavía en juego: paradas que la regla no ve.
3. La misma medida de `medir.py`, con la parada en el frame final del evento.
"""

import argparse
import collections
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import lector as lc  # noqa: E402
import medir  # noqa: E402

H, A, D, X = lc.H, lc.A, lc.D, lc.X


def _subtipo_json(sub):
    if isinstance(sub, dict):
        return sub.get("name") or ""
    if isinstance(sub, list):
        return " ".join((x.get("name") or "") if isinstance(x, dict) else str(x) for x in sub)
    return "" if sub is None else str(sub)


def eventos_crudos(id_):
    """[(n de la parte, [(inicio, fin o None, tipo, subtipo, equipo)])], con los frames en el índice de la parte."""
    base = lc.carpeta() / "data" / "Sample_Game_{}".format(id_)
    out = []
    if id_ < 3:
        frames, periodo, _, _ = lc._pares(lc._csv(base / "Sample_Game_{}_RawTrackingData_Home_Team.csv".format(id_)))
        tabla = pd.read_csv(base / "Sample_Game_{}_RawEventsData.csv".format(id_))
        equipos = {"Home": H, "Away": A}
        for parte in (1, 2):
            filas = np.flatnonzero(periodo == parte)
            indice = {int(frames[i]): k for k, i in enumerate(filas)}
            ev = []
            for f in tabla.itertuples(index=False):
                if int(f[3]) != parte or indice.get(int(f[4])) is None:
                    continue
                ev.append((indice[int(f[4])], indice.get(int(f[6])), str(f[1]),
                           "" if pd.isna(f[2]) else str(f[2]), equipos[str(f[0])]))
            out.append((len(filas), ev))
        return out
    raw, meta = base / "Sample_Game_3_tracking.txt", base / "Sample_Game_3_metadata.xml"
    limites, _ = lc._limites_juego3(meta, raw)
    ids = [t.get("id") for t in ET.parse(meta).getroot().iter("Team")]
    equipos = {ids[0]: H, ids[1]: A}
    with open(base / "Sample_Game_3_events.json", encoding="utf-8") as handle:
        datos = json.load(handle)["data"]
    for k, (a, b) in enumerate(limites, start=1):
        n = b - a + 1
        ev = []
        for f in datos:
            if int(f["period"]) != k:
                continue
            tipo = f["type"]["name"] if isinstance(f["type"], dict) else str(f["type"])
            fin = int(f["end"]["frame"]) - a
            ev.append((int(f["start"]["frame"]) - a, fin if 0 <= fin < n else None, tipo,
                       _subtipo_json(f.get("subtypes")), equipos[f["team"]["id"]]))
        out.append((n, ev))
    return out


def al_final(evento):
    """El evento tal cual o, si para el juego y dura, su control al inicio y su parada al final."""
    ini, fin, tipo, sub, eq = evento
    if not lc._es_parada(tipo, sub) or fin is None or fin <= ini:
        return [(ini, tipo, sub, eq)]
    out = [(ini, tipo, "", eq)] if tipo in lc.CONTROLES else []
    return out + [(fin, "BALL OUT", "", eq)]


def etiquetas(partes, mover):
    trozos = []
    for n, ev in partes:
        lista = []
        for e in ev:
            lista += al_final(e) if mover else [(e[0], e[2], e[3], e[4])]
        trozos.append(lc.etiquetar(n, lista))
    return np.concatenate(trozos).astype(np.int8)


def rachas_d(gt):
    return int(np.sum(np.diff(np.concatenate([[0], (gt == D).astype(np.int8)])) == 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    ids = lc.partidos()
    if not ids:
        sys.exit("No hay partidos de Metrica bajados, en {}".format(lc.carpeta()))

    duraciones = collections.defaultdict(list)
    saques = saques_en_juego = sin_marcar = vivos = 0
    antes = collections.Counter()
    alternativo, filas = {}, []
    for id_ in ids:
        crudo = lc.leer(id_)
        partes = eventos_crudos(id_)
        igual = np.array_equal(etiquetas(partes, False), crudo["gt"])
        nuevo = etiquetas(partes, True)
        if len(nuevo) != len(crudo["gt"]):
            sys.exit("las etiquetas del juego {} no miden lo mismo que la caché".format(id_))
        filas.append("| {} | {} | {:.2f} % | {:.1f} % → {:.1f} % | {} → {} |".format(
            id_, "sí" if igual else "NO", 100.0 * np.mean(nuevo != crudo["gt"]),
            100.0 * np.mean(crudo["gt"][crudo["gt"] != X] == D), 100.0 * np.mean(nuevo[nuevo != X] == D),
            rachas_d(crudo["gt"]), rachas_d(nuevo)))
        alternativo[id_] = dict(crudo, gt=nuevo)
        for n, ev in partes:
            gt = lc.etiquetar(n, [(e[0], e[2], e[3], e[4]) for e in ev])
            vivos += int(np.sum((gt == H) | (gt == A)))
            for ini, fin, tipo, sub, _ in ev:
                if lc._es_parada(tipo, sub) and fin is not None:
                    clave = tipo if tipo != "BALL LOST" else "BALL LOST ({})".format(sub.strip().upper())
                    duraciones[clave].append(fin - ini)
            for s in sorted({e[0] for e in ev if e[2] == "SET PIECE" and 0 <= e[0] < n}):
                saques += 1
                if s == 0 or gt[s - 1] not in (H, A):
                    continue
                saques_en_juego += 1
                previos = [e for e in ev if e[0] < s]
                if not previos:
                    continue
                ultimo = max(previos, key=lambda e: e[0])
                antes["{} ({})".format(ultimo[2], ultimo[3].strip().upper() or "sin subtipo")] += 1
                acaba = max(min(e[1] if e[1] is not None else e[0], s) for e in previos)
                sin_marcar += s - acaba

    print("## 1. Cuánto dura cada evento que para el juego (la regla de §3 para en su frame de inicio)\n")
    print("| evento | n | fin − inicio, frames: p25 / mediana / p75 | con duración 0 |")
    print("|---|---|---|---|")
    for clave in sorted(duraciones):
        d = np.array(duraciones[clave], dtype=float)
        print("| {} | {} | {:.0f} / {:.0f} / {:.0f} | {} |".format(
            clave, len(d), np.percentile(d, 25), np.median(d), np.percentile(d, 75), int(np.sum(d == 0))))

    print("\n## 2. Saques que llegan con la etiqueta todavía en juego\n")
    print("- saques: {} · con la etiqueta en juego justo antes: {} ({:.0f} %)".format(
        saques, saques_en_juego, 100.0 * saques_en_juego / max(saques, 1)))
    print("- frames entre el final del último evento y ese saque (cota del balón muerto sin marcar): {} · "
          "{:.1f} % de los frames en juego".format(sin_marcar, 100.0 * sin_marcar / max(vivos, 1)))
    print("- último evento antes de esos saques: " + " · ".join(
        "{}: {}".format(k, v) for k, v in antes.most_common(8)))

    print("\n## 3. La medida, con la parada en el frame final del evento\n")
    print("| juego | sin mover, ¿salen las etiquetas de la caché? | frames que cambian | `D` antes → después | paradas antes → después |")
    print("|---|---|---|---|---|")
    print("\n".join(filas) + "\n")
    lc.leer = lambda id_, raiz=None: alternativo[id_]
    sys.argv = ["medir.py", "--bootstrap", str(args.bootstrap)]
    medir.main()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
