"""Recuento de revisión de las fases del Smart Tagging: `validation/fases_smart_tagging/BITACORA.md` §7.

**Lee datos del partido (ATD y Smart Tagging) y una entrega nuestra: lo ejecuta una persona, en local, nunca
Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/fases_smart_tagging_revision.py --entrega evaluation/results/equipo_v3.csv

Usa la tabla, el control claro, la lectura de la entrega y los desplazamientos del placebo de
`validation/partido/fases_smart_tagging.py` (lo importa). Mide, en los frames evaluados y con las dos partes
juntas:

1. los frames solapados con equipos distintos, por código y por pareja de códigos, y cuántos tienen una fase
   «de zona» (bitácora §7.1, decide si la tabla vale);
2. cuánto tarda nuestra etiqueta en ser la del equipo de cada `ATTACKING TRANSITION`, y con qué etiqueta
   vamos dentro de esas fases, frente al placebo (§7.2, descriptivo, para Ismael).

- Imprime solo agregados del partido entero, con las celdas de 1 a 4 como "< 5". Nada por frame, por minuto
  ni por jugada: la salida se puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.

Cómo se lee está fijado antes de ejecutarlo (bitácora §7). `revision(trk, eventos, etiquetas)` es una función
pura: la prueba (`validation/scripts/prueba_fases_smart_tagging.py`) la ejecuta con un partido inventado.
"""

import argparse
import os
import sys
import time
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import fases_smart_tagging as fst  # noqa: E402  (añade la raíz al path)
import games  # noqa: E402
from possession import candidates, tracking  # noqa: E402
from possession.tracking import A, H  # noqa: E402
from starter import load_smart_tagging  # noqa: E402

# Fijados antes de ejecutar (bitácora §7).
ZONA = ("players in the box", "ball in final third", "ball in the box")
UMBRAL_ZONA = 0.70
TOP_PAREJAS = 10
MAX_ESPERA_S = 15
CORTES_S = (2, 5, 10, 15)
INTERVALOS = ("ya lo era en el inicio", "hasta 2 s", "de 2 a 5 s", "de 5 a 10 s", "de 10 a 15 s",
              "no lo es en 15 s")
UMBRAL_TARDE = 0.5  # la mitad o más de los inicios esperan más de 2 s (o no llegan)
UMBRAL_FRAMES_OTRO = 0.20  # el 20 % o más de los frames de las transiciones, con el otro equipo


def coberturas(n, fases):
    """{(código, equipo con el balón): máscara de frames}."""
    salida = {}
    for equipo, inicio, fin, codigo in fases:
        mascara = salida.setdefault((codigo, equipo), np.zeros(n, dtype=bool))
        mascara[max(0, inicio):min(n, fin)] = True
    return salida


def solapes(n, fases, evaluados):
    """Los frames evaluados solapados con equipos distintos, por código, por pareja y con fase de zona."""
    cub = coberturas(n, fases)
    vacio = np.zeros(n, dtype=bool)
    codigos = sorted({c for c, _ in cub})
    lado = {k: np.any([cub.get((c, k), vacio) for c in codigos], axis=0) if codigos else vacio for k in (H, A)}
    conflicto = evaluados & lado[H] & lado[A]
    por_codigo = {c: int(np.sum(conflicto & (cub.get((c, H), vacio) | cub.get((c, A), vacio)))) for c in codigos}
    parejas = []
    for i, c1 in enumerate(codigos):
        for c2 in codigos[i:]:
            m = conflicto & ((cub.get((c1, H), vacio) & cub.get((c2, A), vacio)) |
                             (cub.get((c1, A), vacio) & cub.get((c2, H), vacio)))
            k = int(m.sum())
            if k:
                parejas.append((k, c1, c2))
    parejas.sort(key=lambda p: (-p[0], p[1], p[2]))
    zona = np.any([cub.get((z, k), vacio) for z in ZONA for k in (H, A)], axis=0)
    return {"solapados": int(conflicto.sum()), "por_codigo": por_codigo, "parejas": parejas[:TOP_PAREJAS],
            "con_zona": int(np.sum(conflicto & zona))}


def espera(etiquetas, inicio, equipo, fps):
    """Índice de INTERVALOS: cuánto tarda la etiqueta en ser `equipo` desde `inicio`."""
    if etiquetas[inicio] == equipo:
        return 0
    fin = min(len(etiquetas), inicio + MAX_ESPERA_S * fps + 1)
    llega = np.flatnonzero(etiquetas[inicio + 1:fin] == equipo)
    if len(llega) == 0:
        return len(INTERVALOS) - 1
    segundos = (llega[0] + 1) / float(fps)
    for k, corte in enumerate(CORTES_S):
        if segundos <= corte:
            return k + 1
    return len(INTERVALOS) - 1


def contraataques(eventos, etiquetas, control, evaluados, fps, desplazamiento=0):
    """Esperas y etiquetas dentro de las ATTACKING TRANSITION (desplazadas `desplazamiento` frames)."""
    n = len(etiquetas)
    esperas = [0] * len(INTERVALOS)
    frames = {"ese equipo": 0, "el otro": 0, "D o X": 0}
    en_control = dict(frames)
    for evento in eventos:
        if fst.norm(evento["code"]) != fst.TRANSICION:
            continue
        equipo, _ = fst.equipo_con_balon(evento)
        inicio = int(evento["start_frame"]) + desplazamiento
        if equipo is None or not (0 <= inicio < n) or not evaluados[inicio]:
            continue
        esperas[espera(etiquetas, inicio, equipo, fps)] += 1
        a, b = inicio, min(n, int(evento["end_frame"]) + desplazamiento)
        dentro = evaluados[a:b]
        etiqueta = etiquetas[a:b][dentro]
        suyo = control[a:b][dentro] == equipo
        for destino, sel in ((frames, np.ones(len(etiqueta), dtype=bool)), (en_control, suyo)):
            destino["ese equipo"] += int(np.sum(sel & (etiqueta == equipo)))
            destino["el otro"] += int(np.sum(sel & (etiqueta == 1 - equipo)))
            destino["D o X"] += int(np.sum(sel & (etiqueta != equipo) & (etiqueta != 1 - equipo)))
    return {"inicios": sum(esperas), "esperas": esperas, "frames": frames, "en_control": en_control}


def revision(trk, eventos, etiquetas):
    """El recuento de la bitácora §7. Sin suprimir celdas."""
    n = len(trk.bx)
    etiquetas = np.asarray(etiquetas)
    if len(etiquetas) != n:
        raise ValueError("la entrega no tiene tantas filas como frames tiene el tracking")
    fps = int(trk.fps)
    evaluados = fst.evaluados(trk)
    fases = fst.fases_validas(eventos)
    control = np.where(evaluados, candidates.retention_team(trk, radius=fst.CONTROL_RADIO,
                                                            min_frames=fst.CONTROL_FRAMES), -1)
    return {
        "frames_evaluados": int(evaluados.sum()),
        "fases_validas": len(fases),
        "solapes": solapes(n, fases, evaluados),
        "contraataques": contraataques(eventos, etiquetas, control, evaluados, fps),
        "placebo": [contraataques(eventos, etiquetas, control, evaluados, fps, s * fps) for s in fst.PLACEBO_S],
    }


def lectura_solapes(r):
    """(la tabla vale, por qué) según la bitácora §7.1."""
    s = r["solapes"]
    if not s["solapados"]:
        return True, "no hay frames solapados con equipos distintos"
    parte = s["con_zona"] / float(s["solapados"])
    if parte >= UMBRAL_ZONA:
        return True, "en el {:.1f} % de los solapados interviene una fase de zona (≥ 70 %)".format(
            100 * parte).replace(".", ",")
    return False, "solo en el {:.1f} % de los solapados interviene una fase de zona (< 70 %)".format(
        100 * parte).replace(".", ",")


def tarde(c):
    """Fracción de inicios que esperan más de 2 s o no llegan en 15 s."""
    return sum(c["esperas"][2:]) / float(c["inicios"]) if c["inicios"] else None


def lectura_contraataques(r):
    """(se le propone a Ismael medir un empujón al inicio, por qué) según la bitácora §7.2. No decide nada."""
    c = r["contraataques"]
    real = tarde(c)
    placebo = [tarde(p) for p in r["placebo"] if p["inicios"]]
    total = sum(c["frames"].values())
    otro = c["frames"]["el otro"] / float(total) if total else None
    if real is None or otro is None or not placebo:
        return False, "no hay transiciones que medir"
    uno = real >= UMBRAL_TARDE and real > np.mean(placebo)
    dos = otro >= UMBRAL_FRAMES_OTRO
    return uno and dos, "esperan más de 2 s el {:.0f} % de los inicios (placebo {:.0f} %); el {:.0f} % de los " \
        "frames de las transiciones va con el otro equipo".format(100 * real, 100 * np.mean(placebo), 100 * otro)


def para_imprimir(r, sha=None, minimo=fst.MINIMO_CELDA):
    """Las líneas de la salida, con las celdas pequeñas suprimidas. Los controles salen siempre."""
    celda, pct = fst.celda, fst.pct
    s = r["solapes"]
    vale, porque_tabla = lectura_solapes(r)
    propone, porque_cont = lectura_contraataques(r)
    lineas = [
        "Fases del Smart Tagging, recuento de revisión (validation/fases_smart_tagging/BITACORA.md §7): frames "
        "evaluados, las dos partes juntas",
        "",
        "0. Controles",
        "   frames evaluados: {}   fases en la tabla: {}".format(r["frames_evaluados"], r["fases_validas"]),
        "   entrega: sha256 {}   ¿es equipo_v3? {}".format(
            "—" if sha is None else "{}…{}".format(sha[:8], sha[-5:]),
            "—" if sha is None else ("sí" if (sha[:8], sha[-5:]) == fst.SHA_V3 else "NO")),
        "",
        "1. Solapados con equipos distintos: {}   con una fase de zona: {} ({})".format(
            celda(s["solapados"], minimo), celda(s["con_zona"], minimo), pct(s["con_zona"], s["solapados"], minimo)),
        "   por código (frames solapados en que interviene):",
    ]
    for codigo in sorted(s["por_codigo"], key=lambda c: (-s["por_codigo"][c], c)):
        lineas.append("      {:<30} {:>7}  ({})".format(codigo, celda(s["por_codigo"][codigo], minimo),
                                                       pct(s["por_codigo"][codigo], s["solapados"], minimo)))
    lineas.append("   las {} parejas con más frames (un código de cada lado):".format(TOP_PAREJAS))
    for k, c1, c2 in s["parejas"]:
        lineas.append("      {:<30} / {:<30} {:>7}  ({})".format(c1, c2, celda(k, minimo), pct(k, s["solapados"], minimo)))
    lineas += ["   → la tabla {}: {}".format("VALE, excluyendo los solapados" if vale else "SIGUE SOSPECHOSA",
                                            porque_tabla), ""]
    c = r["contraataques"]
    placebo_inicios = sum(p["inicios"] for p in r["placebo"])
    lineas += [
        "2. Contraataques: inicios de ATTACKING TRANSITION en tramos evaluados: {}   (placebo: {})".format(
            celda(c["inicios"], minimo), placebo_inicios),
        "   cuánto tarda nuestra etiqueta en ser la de ese equipo:",
    ]
    for k, nombre in enumerate(INTERVALOS):
        p = sum(pl["esperas"][k] for pl in r["placebo"])
        lineas.append("      {:<24} reales {:>4} ({:>7})   placebo {:>4} ({})".format(
            nombre, celda(c["esperas"][k], minimo), pct(c["esperas"][k], c["inicios"], minimo), celda(p, minimo),
            pct(p, placebo_inicios, minimo)))
    for titulo, clave in (("frames de las transiciones", "frames"),
                          ("de ellos, con control claro del equipo de la transición", "en_control")):
        total = sum(c[clave].values())
        total_p = sum(sum(p[clave].values()) for p in r["placebo"])
        lineas.append("   {}: {}   nuestra etiqueta:".format(titulo, celda(total, minimo)))
        for nombre in ("ese equipo", "el otro", "D o X"):
            p = sum(pl[clave][nombre] for pl in r["placebo"])
            lineas.append("      {:<12} reales {:>7} ({:>7})   placebo {:>7} ({})".format(
                nombre, celda(c[clave][nombre], minimo), pct(c[clave][nombre], total, minimo), celda(p, minimo),
                pct(p, total_p, minimo)))
    lineas += ["   → {}: {}".format("se le propone a Ismael medir un empujón al inicio" if propone
                                    else "se le pasan los números a Ismael", porque_cont)]
    return lineas


def medir(entrega, data_dir=None):
    """El recuento sobre el partido. Lee datos del partido y una entrega: solo lo ejecuta una persona."""
    game = games.GAME
    games.require(fst.FICHEROS, game, data_dir)
    trk = tracking.from_atd(games.asset_paths(game, data_dir), game)
    eventos = load_smart_tagging.load(game, data_dir)
    etiquetas, sha = fst.leer_entrega(entrega, len(trk.bx))
    return revision(trk, eventos, etiquetas), sha


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entrega", required=True, help="CSV frame,label de la entrega (la vigente: equipo_v3)")
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    inicio = time.time()
    try:
        games.require(fst.FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD o el Smart Tagging del partido: revisa que MTAH_DATA_DIR (o --data-dir) apunte "
              "a la carpeta de los datos.")
        return 1
    if not os.path.isfile(args.entrega):
        print("No encuentro la entrega: genérala con  python -m possession.pipeline --name equipo_v3")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        resultado, sha = medir(args.entrega, args.data_dir)
        lineas = para_imprimir(resultado, sha)
    print("\n".join(lineas))
    print("\n   tiempo {:.0f} s".format(time.time() - inicio))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(fst.informe_de_error(e))
        sys.exit(1)
