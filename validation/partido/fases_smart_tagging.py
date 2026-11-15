"""Las fases del Smart Tagging como pista de equipo: el recuento de `validation/fases_smart_tagging/BITACORA.md`.

**Lee datos del partido (ATD y Smart Tagging) y una entrega nuestra: lo ejecuta una persona, en local, nunca
Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/fases_smart_tagging.py --entrega evaluation/results/equipo_v3.csv

Si no tienes la entrega, se genera con `python -m possession.pipeline --name equipo_v3`.

Mide, en los frames evaluados y con las dos partes juntas (bitácora §3):

1. la regla del plan: el acuerdo entre el equipo de la fase y el del control claro (el mismo equipo a 1 m durante
   1 s), frente a las fases desplazadas;
2. los frames con fases solapadas que dan equipos distintos;
3. las transiciones: de los inicios de `ATTACKING TRANSITION`, cuántos tienen un cambio nuestro a ese equipo a
   2 s o menos, frente a los inicios desplazados;
4. el alcance del empujón del plan: los frames sin balón que no son `D`.

- Imprime solo agregados del partido entero: recuentos y porcentajes, por código (frames) y por clase
  (inicios). Una celda de 1 a 4 casos sale como "< 5". Nada por frame, por minuto ni por jugada: la salida se
  puede pegar a Claude.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.

Cómo se lee está fijado antes de ejecutarlo, en la bitácora §3. Después de ver los números no se retoca nada.
`recuento(trk, eventos, etiquetas)` es una función pura: la prueba
(`validation/scripts/prueba_fases_smart_tagging.py`) la ejecuta con un partido inventado.
"""

import argparse
import csv
import hashlib
import os
import sys
import time
import traceback
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
import games  # noqa: E402
from possession import candidates, tracking  # noqa: E402
from possession.tracking import A, D, H, X  # noqa: E402
from starter import load_smart_tagging  # noqa: E402

FICHEROS = ["atd_raw", "atd_meta", "smart_tagging"]
MINIMO_CELDA = 5

# La tabla de la bitácora §2, de OVERVIEW.md: `Team` es el equipo que hace la fase.
ATAQUE = ("build up", "progression", "creating chances", "attacking transition", "long ball", "ball in final third",
          "ball in the box", "players in the box")
DEFENSA = ("defending in attacking third", "defending in middle third", "defending in defensive third",
           "defensive transition")
FUERA = ("set pieces", "goals")
EQUIPOS = {"barcelona": H, "atletic club": A, "athletic club": A}
TRANSICION = "attacking transition"
SIN_FASE, SOLAPADO = -1, 2

# Fijados antes de ejecutar (bitácora §3); ninguno sale del partido ni de la ventana pública.
CONTROL_RADIO = 1.0  # m (P7 de la revisión externa)
CONTROL_FRAMES = 25  # frames: 1 s
PLACEBO_S = (-480, -360, -240, 240, 360, 480)  # los de validation/partido/agregados_dead_ball.py
VENTANA_S = 2  # s, a cada lado del inicio de una transición
UMBRAL_ACUERDO = 0.80
FACTOR_PLACEBO = 0.5  # desacuerdo real ≤ la mitad del desacuerdo medio del placebo (lectura de «dobla»)
UMBRAL_SOLAPE = 0.10  # descriptivo: por encima, la tabla es sospechosa
DESFASES_S = (-2, -1, 0, 1, 2)  # cortes de los intervalos del desfase de 3.3
# El sha256 de equipo_v3 (CLAUDE.md), para decir si la entrega es esa.
SHA_V3 = ("9539ce42", "cc17a")

CLASES = ("cambio a ese equipo a ±2 s", "sin cambio, ya era ese equipo", "era el otro equipo", "era D o X")


def norm(texto):
    return (texto or "").strip().lower()


def equipo_con_balon(evento):
    """(equipo con el balón o None, motivo): «ataque», «defensa», «fuera», «sin tabla» o «team n/a»."""
    codigo = norm(evento["code"])
    if codigo in FUERA:
        return None, "fuera"
    if codigo not in ATAQUE + DEFENSA:
        return None, "sin tabla"
    equipo = EQUIPOS.get(norm(evento["tags"].get("Team")))
    if equipo is None:
        return None, "team n/a"
    return (equipo, "ataque") if codigo in ATAQUE else (1 - equipo, "defensa")


def fases_validas(eventos):
    """[(equipo con el balón, inicio, fin, código)] de las fases que entran en la tabla."""
    salida = []
    for evento in eventos:
        equipo, _ = equipo_con_balon(evento)
        if equipo is not None:
            salida.append((equipo, int(evento["start_frame"]), int(evento["end_frame"]), norm(evento["code"])))
    return salida


def equipo_de_fase(n, fases, desplazamiento=0):
    """Por frame: el equipo con el balón según las fases (desplazadas `desplazamiento` frames), SIN_FASE si no
    hay ninguna y SOLAPADO si las que lo cubren dan equipos distintos."""
    hay = np.zeros((2, n), dtype=bool)
    for equipo, inicio, fin, _ in fases:
        a, b = max(0, inicio + desplazamiento), min(n, fin + desplazamiento)
        if a < b:
            hay[equipo, a:b] = True
    salida = np.full(n, SIN_FASE, dtype=np.int8)
    salida[hay[H] & ~hay[A]] = H
    salida[hay[A] & ~hay[H]] = A
    salida[hay[H] & hay[A]] = SOLAPADO
    return salida


def evaluados(trk):
    mascara = np.zeros(len(trk.bx), dtype=bool)
    for a, b in trk.blocks:
        mascara[a:b] = True
    return mascara


def acuerdo(fase, control, mascara):
    """(frames de control claro con equipo de fase, de ellos los que coinciden)."""
    con = mascara & (control >= 0) & ((fase == H) | (fase == A))
    return int(con.sum()), int((con & (fase == control)).sum())


def clase_transicion(etiquetas, inicio, equipo, ventana):
    """(clase 0–3 de la bitácora §3.3, desfase en frames del cambio más cercano o None, origen o None)."""
    n = len(etiquetas)
    a, b = max(1, inicio - ventana), min(n - 1, inicio + ventana)
    f = np.arange(a, b + 1)
    cambio = (etiquetas[f] == equipo) & (etiquetas[f - 1] != equipo) & (etiquetas[f - 1] != X)
    if cambio.any():
        cerca = f[cambio][np.argmin(np.abs(f[cambio] - inicio))]
        origen = "otro equipo" if etiquetas[cerca - 1] == 1 - equipo else "D"
        return 0, int(cerca - inicio), origen
    ahora = etiquetas[inicio]
    if ahora == equipo:
        return 1, None, None
    if ahora == 1 - equipo:
        return 2, None, None
    return 3, None, None


def transiciones(eventos, etiquetas, mascara, fps, desplazamiento=0):
    """Clases, desfases y orígenes de los inicios de ATTACKING TRANSITION (desplazados) en tramos evaluados."""
    ventana = int(VENTANA_S * fps)
    clases, desfases, origenes = [0] * len(CLASES), [], {"otro equipo": 0, "D": 0}
    for evento in eventos:
        if norm(evento["code"]) != TRANSICION:
            continue
        equipo, _ = equipo_con_balon(evento)
        inicio = int(evento["start_frame"]) + desplazamiento
        if equipo is None or not (0 <= inicio < len(etiquetas)) or not mascara[inicio]:
            continue
        clase, desfase, origen = clase_transicion(etiquetas, inicio, equipo, ventana)
        clases[clase] += 1
        if desfase is not None:
            desfases.append(desfase / float(fps))
            origenes[origen] += 1
    return {"inicios": sum(clases), "clases": clases, "desfases": desfases, "origenes": origenes}


def recuento(trk, eventos, etiquetas):
    """El recuento de la bitácora §3 con un `Tracking`, los eventos del Smart Tagging (como los da
    starter/load_smart_tagging.load) y las etiquetas de una entrega (0 H, 1 A, 2 D, 3 X). Sin suprimir celdas."""
    n = len(trk.bx)
    etiquetas = np.asarray(etiquetas)
    if len(etiquetas) != n:
        raise ValueError("la entrega no tiene tantas filas como frames tiene el tracking")
    fps = int(trk.fps)
    mascara = evaluados(trk)
    fases = fases_validas(eventos)
    fase = equipo_de_fase(n, fases)
    control = np.where(mascara, candidates.retention_team(trk, radius=CONTROL_RADIO, min_frames=CONTROL_FRAMES),
                       -1)

    tabla = {}
    for evento in eventos:
        codigo = norm(evento["code"])
        _, motivo = equipo_con_balon(evento)
        fila = tabla.setdefault(codigo, {"instancias": 0, "motivo": set(), "team_na": 0})
        fila["instancias"] += 1
        fila["motivo"].add(motivo)
        fila["team_na"] += int(motivo == "team n/a")
    for codigo, fila in tabla.items():
        propias = [f for f in fases if f[3] == codigo]
        cubre = equipo_de_fase(n, propias) if propias else np.full(n, SIN_FASE, dtype=np.int8)
        cubre = np.where(fase == SOLAPADO, SIN_FASE, cubre)  # los solapados se excluyen de todo
        fila["frames"] = int(np.sum(mascara & ((cubre == H) | (cubre == A))))
        fila["control"], fila["coinciden"] = acuerdo(cubre, control, mascara)
        motivos = fila.pop("motivo") - {"team n/a"}
        fila["clase"] = motivos.pop() if len(motivos) == 1 else ("team n/a" if not motivos else "mixta")

    control_total = int(np.sum(mascara & (control >= 0)))
    con_fase, coinciden = acuerdo(fase, control, mascara)
    placebo = []
    for s in PLACEBO_S:
        f_s = equipo_de_fase(n, fases, s * fps)
        placebo.append(acuerdo(f_s, control, mascara))

    visto = np.isfinite(trk.bx) & np.isfinite(trk.by)
    sin_balon = mascara & ~visto & (etiquetas != D) & (etiquetas != X)
    con_equipo = sin_balon & ((fase == H) | (fase == A))
    return {
        "frames_evaluados": int(mascara.sum()),
        "frames_con_balon": int(np.sum(mascara & visto)),
        "fases": len(eventos),
        "fases_validas": len(fases),
        "tabla": tabla,
        "frames_con_fase": int(np.sum(mascara & (fase != SIN_FASE))),
        "frames_solapados": int(np.sum(mascara & (fase == SOLAPADO))),
        "frames_control": control_total,
        "control_con_fase": con_fase,
        "control_coinciden": coinciden,
        "placebo": placebo,
        "transiciones": transiciones(eventos, etiquetas, mascara, fps),
        "transiciones_placebo": [transiciones(eventos, etiquetas, mascara, fps, s * fps) for s in PLACEBO_S],
        "sin_balon_vivo": int(sin_balon.sum()),
        "sin_balon_con_fase": int(con_equipo.sum()),
        "sin_balon_otro_equipo": int(np.sum(con_equipo & (etiquetas == 1 - fase))),
    }


def veredicto(r):
    """(entra, acuerdo, desacuerdo medio del placebo, por qué) según la bitácora §3.1."""
    if not r["control_con_fase"]:
        return False, None, None, "no hay frames de control claro con fase"
    acuerdo_real = r["control_coinciden"] / float(r["control_con_fase"])
    tasas = [c / float(t) for t, c in r["placebo"] if t]
    if not tasas:
        return False, acuerdo_real, None, "el placebo no tiene frames"
    desacuerdo_placebo = 1.0 - float(np.mean(tasas))
    uno = acuerdo_real >= UMBRAL_ACUERDO
    dos = (1.0 - acuerdo_real) <= FACTOR_PLACEBO * desacuerdo_placebo
    porque = "acuerdo {} el 80 %; desacuerdo {} la mitad del del placebo".format(
        "llega a" if uno else "NO llega a", "no pasa de" if dos else "PASA de")
    return uno and dos, acuerdo_real, desacuerdo_placebo, porque


# -- impresión ----------------------------------------------------------------------------------------------

def celda(n, minimo=MINIMO_CELDA):
    """Un recuento para imprimir: de 1 a minimo − 1 casos sale como "< 5"."""
    return "< {}".format(minimo) if 0 < n < minimo else str(n)


def pct(parte, total, minimo=MINIMO_CELDA):
    if not total or 0 < parte < minimo:
        return "–"
    return "{:.1f} %".format(100.0 * parte / total).replace(".", ",")


def intervalos_desfase(desfases):
    cortes = DESFASES_S
    return [("{:+d} a {:+d} s".format(a, b), sum(a <= d < b or (b == cortes[-1] and d == b) for d in desfases))
            for a, b in zip(cortes[:-1], cortes[1:])]


def para_imprimir(r, sha=None, minimo=MINIMO_CELDA):
    """Las líneas de la salida, con las celdas pequeñas suprimidas. Los controles salen siempre."""
    entra, acuerdo_real, desacuerdo_placebo, porque = veredicto(r)
    lineas = [
        "Fases del Smart Tagging como pista de equipo (validation/fases_smart_tagging/BITACORA.md): frames "
        "evaluados, las dos partes juntas",
        "",
        "0. Controles",
        "   frames evaluados: {}   con balón: {}".format(r["frames_evaluados"], r["frames_con_balon"]),
        "   fases en el fichero: {}   en la tabla, con Team H o A: {}".format(r["fases"], r["fases_validas"]),
        "   entrega: sha256 {}   ¿es equipo_v3? {}".format(
            "—" if sha is None else "{}…{}".format(sha[:8], sha[-5:]),
            "—" if sha is None else ("sí" if (sha[:8], sha[-5:]) == SHA_V3 else "NO")),
        "",
        "1. La tabla (bitácora §2): por código, instancias, Team N/A, frames con fase y acuerdo en control claro",
    ]
    for codigo in sorted(r["tabla"], key=lambda c: (r["tabla"][c]["clase"], c)):
        f = r["tabla"][codigo]
        lineas.append("   {:<30} {:<9} inst {:>4}  N/A {:>4}  frames {:>7}  control {:>6}  acuerdo {:>7}".format(
            codigo, f["clase"], celda(f["instancias"], minimo), celda(f["team_na"], minimo),
            celda(f["frames"], minimo), celda(f["control"], minimo), pct(f["coinciden"], f["control"], minimo)))
    lineas += [
        "",
        "2. Frames solapados con equipos distintos (descriptivo; sospechoso por encima del {:.0f} %)".format(
            100 * UMBRAL_SOLAPE),
        "   frames evaluados con fase: {}   solapados con equipos distintos: {} ({})".format(
            celda(r["frames_con_fase"], minimo), celda(r["frames_solapados"], minimo),
            pct(r["frames_solapados"], r["frames_con_fase"], minimo)),
        "   ¿sospechoso? {}".format("sí" if r["frames_con_fase"] and
                                    r["frames_solapados"] > UMBRAL_SOLAPE * r["frames_con_fase"] else "no"),
        "",
        "3. La regla del plan: acuerdo en control claro (mismo equipo a {:g} m durante {} frames)".format(
            CONTROL_RADIO, CONTROL_FRAMES),
        "   frames de control claro: {}   con fase: {} ({})".format(
            celda(r["frames_control"], minimo), celda(r["control_con_fase"], minimo),
            pct(r["control_con_fase"], r["frames_control"], minimo)),
        "   acuerdo con las fases reales: {}".format(pct(r["control_coinciden"], r["control_con_fase"], minimo)),
        "   placebo (fases desplazadas):",
    ]
    for s, (total, coinciden) in zip(PLACEBO_S, r["placebo"]):
        lineas.append("      {:+5d} s   con fase {:>7}   acuerdo {}".format(s, celda(total, minimo),
                                                                       pct(coinciden, total, minimo)))
    lineas += [
        "   desacuerdo: reales {}   placebo, media {}".format(
            "—" if acuerdo_real is None else "{:.1f} %".format(100 * (1 - acuerdo_real)).replace(".", ","),
            "—" if desacuerdo_placebo is None else "{:.1f} %".format(100 * desacuerdo_placebo).replace(".", ",")),
        "   → {}: {}".format("ENTRA (empujón pequeño, solo sin balón)" if entra else "NO ENTRA", porque),
        "",
    ]
    t = r["transiciones"]
    lineas += [
        "4. Transiciones (descriptivo): inicios de ATTACKING TRANSITION y nuestra entrega a ±{} s".format(VENTANA_S),
        "   inicios en tramos evaluados, con Team H o A: {}".format(celda(t["inicios"], minimo)),
    ]
    placebo_inicios = sum(p["inicios"] for p in r["transiciones_placebo"])
    for k, nombre in enumerate(CLASES):
        placebo_k = sum(p["clases"][k] for p in r["transiciones_placebo"])
        lineas.append("   {:<32} reales {:>4} ({:>7})   placebo {:>4} de {} ({})".format(
            nombre, celda(t["clases"][k], minimo), pct(t["clases"][k], t["inicios"], minimo),
            celda(placebo_k, minimo), placebo_inicios, pct(placebo_k, placebo_inicios, minimo)))
    lineas.append("   de los cambios a ±{} s, desde el otro equipo: {}   desde D: {}".format(
        VENTANA_S, celda(t["origenes"]["otro equipo"], minimo), celda(t["origenes"]["D"], minimo)))
    lineas.append("   desfase de nuestro cambio respecto al inicio: " + "   ".join(
        "{} {}".format(nombre, celda(k, minimo)) for nombre, k in intervalos_desfase(t["desfases"])))
    lineas += [
        "",
        "5. Alcance del empujón (descriptivo): frames evaluados sin balón que no son D en la entrega",
        "   frames: {}   con equipo de fase: {} ({})   con nuestra etiqueta del otro equipo: {} ({})".format(
            celda(r["sin_balon_vivo"], minimo), celda(r["sin_balon_con_fase"], minimo),
            pct(r["sin_balon_con_fase"], r["sin_balon_vivo"], minimo), celda(r["sin_balon_otro_equipo"], minimo),
            pct(r["sin_balon_otro_equipo"], r["sin_balon_con_fase"], minimo)),
    ]
    return lineas


# -- lectura de ficheros (solo la ejecuta una persona) ------------------------------------------------------

def leer_entrega(ruta, n):
    """(códigos por frame, sha256 del fichero). Comprueba que tiene n filas frame,label en orden; los errores no
    enseñan valores."""
    with open(ruta, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    codigo = {"H": H, "A": A, "D": D, "X": X}
    etiquetas = np.full(n, X, dtype=np.int8)
    filas = 0
    with open(ruta, newline="") as f:
        lector = csv.reader(f)
        cabecera = next(lector, None)
        if cabecera is None or [c.strip().lower() for c in cabecera] != ["frame", "label"]:
            raise ValueError("la entrega no empieza por la cabecera frame,label")
        for i, fila in enumerate(lector):
            if i >= n or len(fila) != 2 or fila[0].strip() != str(i) or fila[1].strip() not in codigo:
                raise ValueError("la entrega no tiene una fila frame,label válida y en orden por frame "
                                 "(no se enseña cuál: regla nº 1)")
            etiquetas[i] = codigo[fila[1].strip()]
            filas += 1
    if filas != n:
        raise ValueError("la entrega no tiene {} filas".format(n))
    return etiquetas, sha


def medir(entrega, data_dir=None):
    """El recuento sobre el partido. Lee datos del partido y una entrega: solo lo ejecuta una persona."""
    game = games.GAME
    games.require(FICHEROS, game, data_dir)
    trk = tracking.from_atd(games.asset_paths(game, data_dir), game)
    eventos = load_smart_tagging.load(game, data_dir)
    etiquetas, sha = leer_entrega(entrega, len(trk.bx))
    return recuento(trk, eventos, etiquetas), sha


def informe_de_error(error):
    """Una línea con el tipo de error y dónde, sin el mensaje: el mensaje podría llevar valores de datos."""
    pila = traceback.extract_tb(error.__traceback__)
    donde = ", ".join("{}:{}".format(os.path.basename(p.filename), p.lineno) for p in pila[-4:])
    return "ERROR {} en {}. Sin valores de datos: se puede pegar tal cual.".format(type(error).__name__, donde)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entrega", required=True, help="CSV frame,label de la entrega (la vigente: equipo_v3)")
    ap.add_argument("--data-dir", default=None, help="carpeta de los datos (por defecto, MTAH_DATA_DIR)")
    args = ap.parse_args(argv)
    inicio = time.time()
    try:
        games.require(FICHEROS, games.GAME, args.data_dir)
    except (IOError, OSError):
        print("No encuentro el ATD o el Smart Tagging del partido: revisa que MTAH_DATA_DIR (o --data-dir) apunte "
              "a la carpeta de los datos.")
        return 1
    if not os.path.isfile(args.entrega):
        print("No encuentro la entrega: genérala con  python -m possession.pipeline --name equipo_v3")
        return 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # los avisos de numpy no llevan datos, pero ensucian la salida
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
        print(informe_de_error(e))
        sys.exit(1)
