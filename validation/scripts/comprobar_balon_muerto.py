"""Comprueba possession/dead_ball.py sin datos del partido: solo el código, la GT pública y un Smart Tagging
inventado, que se escribe en una carpeta temporal y se borra al terminar.

Las secciones 9 y 11 (la 10, el equipo que reanuda, está en la rama `feat/d-equipo-reanuda`, que no
entró) prueban las reglas de validation/partido/agregados_dead_ball.py y
agregados_instante_reinicio.py con partidos inventados en memoria: importan sus cuentas, que no abren
ficheros (se comprueba con la apertura de ficheros prohibida), y nunca ejecutan su `main`, que es lo que
lee el partido.

    python validation/scripts/comprobar_balon_muerto.py

Sale con código 1 si falla alguna comprobación. Claude puede ejecutarlo (validation/README.md).
"""

import builtins
import csv
import hashlib
import io
import os
import random
import shutil
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import games  # noqa: E402
import prueba_pipeline as pp  # noqa: E402  (no_files: la guarda de la regla nº 1)
from possession import dead_ball, tracking  # noqa: E402
from starter.load_smart_tagging import KICKOFF_VIDEO_FRAMES  # noqa: E402

GT_PATH = os.path.join(ROOT, "evaluation", "gt", "BAR-ATH_possession_gt_public.csv")
FAQ_SECOND_HALF_DEAD_FRAMES = 2934  # FAQ.md: "Those 2,934 frames are graded and all of them are D"
ANCHOR_KEYS = {1: "kickoff", 2: "kickoff_2nd"}

failures = []


def check(name, ok, detail=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", name, "   " + detail if detail else ""))
    if not ok:
        failures.append(name)


def mask_without_opening_files(game):
    """La máscara y los ficheros que se intentaron abrir al calcularla."""
    opened = []
    real_open, real_io_open = builtins.open, io.open

    def spy(path, *args, **kwargs):
        opened.append(str(path))
        return real_open(path, *args, **kwargs)

    builtins.open = io.open = spy
    try:
        mask = dead_ball.dead_mask(game=game)
    finally:
        builtins.open, io.open = real_open, real_io_open
    return mask, opened


def smart_tagging_xml(folder, name, instances, shuffle_seed=None):
    """Un Smart Tagging inventado con `instances` = [(código, inicio_s, fin_s, Type o None)]. Devuelve la ruta."""
    rows = list(instances)
    if shuffle_seed is not None:
        random.Random(shuffle_seed).shuffle(rows)
    body = []
    for i, (code, start_s, end_s, kind) in enumerate(rows):
        labels = "<label><group>Team</group><text>N/A</text></label>"
        if kind:
            labels += "<label><group>Type</group><text>{}</text></label>".format(kind)
        body.append("<instance><ID>{}</ID><start>{}</start><end>{}</end><code>{}</code>{}</instance>".format(
            i, start_s, end_s, code, labels))
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("<file><ALL_INSTANCES>{}</ALL_INSTANCES></file>".format("".join(body)))
    return path


def check_goal_to_kickoff(game, folder):
    """La capa «de cada gol a su saque» con casos inventados, también los que anclarían juego vivo."""
    fps = games.GAMES[game]["fps"]
    n_frames = games.GAMES[game]["n_video_frames"]
    ko = "Kick Off (After Goal)"

    def spans(instances, seed=None):
        path = smart_tagging_xml(folder, "caso.xml", instances, seed)
        return dead_ball.goal_to_kickoff(dead_ball.smart_tagging_events(path, fps), fps)

    def at(seconds):
        return int(round(seconds * fps))

    check("gol con su saque: de fin del gol a inicio del saque",
          spans([("GOALS", 1000, 1010, None), ("SET PIECES", 1100, 1105, ko)]) == [(at(1010), at(1100))])
    check("códigos y tipos sin distinguir mayúsculas",
          spans([("goals", 1000, 1010, None), ("set pieces", 1100, 1105, "kick off (after goal)")])
          == [(at(1010), at(1100))])
    check("a 180 s justos del fin del gol entra; un frame más, no",
          len(spans([("GOALS", 100, 110, None), ("SET PIECES", 290, 295, ko)])) == 1
          and spans([("GOALS", 100, 110, None), ("SET PIECES", 290.04, 295, ko)]) == [])
    check("gol sin saque y otro gol con saque: solo ancla el segundo",
          spans([("GOALS", 100, 110, None), ("GOALS", 150, 160, None), ("SET PIECES", 200, 205, ko)])
          == [(at(160), at(200))])
    check("un reinicio entre el gol y el saque: no ancla",
          spans([("GOALS", 100, 110, None), ("SET PIECES", 150, 185, "Throw-in"), ("SET PIECES", 200, 205, ko)])
          == [])
    check("un gol que empieza entre otro gol y su saque: no ancla",
          spans([("GOALS", 100, 110, None), ("GOALS", 150, 215, None), ("SET PIECES", 200, 205, ko)]) == [])
    check("saque dentro de su ventana GOALS: no ancla ni se lleva el gol siguiente",
          spans([("GOALS", 100, 110, None), ("SET PIECES", 105, 110, ko),
                 ("GOALS", 300, 310, None), ("SET PIECES", 350, 355, ko)]) == [(at(310), at(350))])
    check("dos saques tras un gol: solo el primero",
          spans([("GOALS", 100, 110, None), ("SET PIECES", 150, 155, ko), ("SET PIECES", 200, 205, ko)])
          == [(at(110), at(150))])
    check("un reinicio que empieza justo en el fin del gol: no ancla",
          spans([("GOALS", 100, 110, None), ("SET PIECES", 110, 145, "Throw-in"), ("SET PIECES", 200, 205, ko)])
          == [])
    check("un gol falso y otro GOALS que empieza en el mismo frame que el saque: no ancla",
          spans([("GOALS", 100, 110, None), ("GOALS", 200, 210, None), ("SET PIECES", 200, 205, ko)]) == [])
    check("dos saques en el mismo frame: no ancla ninguno",
          spans([("GOALS", 100, 110, None), ("SET PIECES", 150, 155, ko), ("SET PIECES", 150, 155, ko)]) == [])
    check("dos GOALS que se pisan y el segundo pasa del saque: no ancla",
          spans([("GOALS", 100, 110, None), ("GOALS", 105, 160, None), ("SET PIECES", 150, 155, ko)]) == [])
    check("dos ventanas del mismo gol que acaban a la vez: ancla una vez",
          spans([("GOALS", 100, 110, None), ("GOALS", 95, 110, None), ("SET PIECES", 150, 155, ko)])
          == [(at(110), at(150))])
    check("un GOALS dentro de otro: ancla desde el fin más tardío",
          spans([("GOALS", 100, 110, None), ("GOALS", 102, 108, None), ("SET PIECES", 150, 155, ko)])
          == [(at(110), at(150))])
    several = [("GOALS", 1000, 1010, None), ("SET PIECES", 1100, 1105, ko), ("GOALS", 2000, 2010, None),
               ("GOALS", 3000, 3010, None), ("SET PIECES", 3210, 3215, ko), ("SET PIECES", 4000, 4035, "Throw-in"),
               ("BUILD UP", 4100, 4140, None), ("GOALS", 6000, 6012.5, None), ("SET PIECES", 6080, 6085, ko)]
    expected = [(at(1010), at(1100)), (at(6012.5), at(6080))]
    check("varios goles: solo los que tienen su saque cerca y sin nada por medio", spans(several) == expected,
          str(spans(several)))
    check("no depende del orden del fichero", all(spans(several, seed) == expected for seed in range(10)))

    path = smart_tagging_xml(folder, "partido_inventado.xml", several)
    trk = tracking.Tracking(np.full(n_frames, np.nan), np.full(n_frames, np.nan), np.empty((n_frames, 0)),
                            np.empty((n_frames, 0)), np.empty(0, dtype=np.int8), games.GAMES[game]["pitch"],
                            tracking.evaluated_blocks(game), fps)
    pre = dead_ball.pre_kickoff(game)
    anchored = np.zeros(n_frames, dtype=bool)
    for start, stop in expected:
        anchored[start:stop] = True
    goal_mask = dead_ball.goal_to_kickoff_mask({"smart_tagging": path}, game)
    check("la máscara de gol a saque son justo sus tramos", bool(np.array_equal(goal_mask, anchored)),
          "{} frames".format(int(goal_mask.sum())))
    # Gol a saque está medido pero fuera de evidence hasta que pase su regla (docs/decisiones.md, 14/11).
    check("con rutas, dead_mask sigue siendo solo el tramo antes del saque",
          bool(np.array_equal(dead_ball.dead_mask({"smart_tagging": path}, game), pre)))
    score, allowed = dead_ball.evidence(trk, {"smart_tagging": path}, game)
    check("evidence con rutas: solo D en el tramo antes del saque, fuera todo permitido, y no puntúa",
          bool(np.array_equal(~allowed[:, tracking.H], pre)) and bool(np.array_equal(~allowed[:, tracking.A], pre))
          and bool(allowed[:, tracking.D].all()) and not score.any())
    _, allowed_none = dead_ball.evidence(trk, None, game)
    check("evidence sin rutas: lo mismo", bool(np.array_equal(allowed_none, allowed)))


def check_gap_before_restart(game, folder):
    """El hueco sin balón antes de cada reinicio (en `evidence` desde el 15/11), con casos inventados."""
    fps = games.GAMES[game]["fps"]
    n = 20000
    long_gap = dead_ball.LONG_GAP_S * fps
    max_gap = dead_ball.MAX_GAP_BEFORE_RESTART_S * fps

    def ball(*holes, only_y=False):
        """Balón visto en todos los frames salvo en los huecos [inicio, fin)."""
        bx, by = np.zeros(n), np.zeros(n)
        for lo, hi in holes:
            by[lo:hi] = np.nan
            if not only_y:
                bx[lo:hi] = np.nan
        return bx, by

    def window(start, code="set pieces", kind="throw-in"):
        return {"code": code, "type": kind, "start": start, "end": start + 35 * fps}

    def result(bx, by, events):
        return [(state, span) for _, state, span in dead_ball.gaps_before_restarts(bx, by, events, fps)]

    w = 10000
    check("hueco de 20 s justo antes de la ventana: se puntúa desde el primer frame sin balón",
          result(*ball((w - 500, w)), [window(w)]) == [(dead_ball.GAP, (w - 500, w))])
    check("hueco de 5 s justos entra; un frame menos, no",
          result(*ball((w - long_gap, w)), [window(w)]) == [(dead_ball.GAP, (w - long_gap, w))]
          and result(*ball((w - long_gap + 1, w)), [window(w)]) == [(dead_ball.BALL_SEEN, None)])
    check("hueco de 60 s justos entra; un frame más, no",
          result(*ball((w - max_gap, w)), [window(w)]) == [(dead_ball.GAP, (w - max_gap, w))]
          and result(*ball((w - max_gap - 1, w)), [window(w)]) == [(dead_ball.GAP_TOO_LONG, None)])
    check("un balón visto en el último frame antes de la ventana: no hay hueco",
          result(*ball((w - 500, w - 1)), [window(w)]) == [(dead_ball.BALL_SEEN, None)])
    check("falta solo la y del balón: cuenta como no visto",
          result(*ball((w - 500, w), only_y=True), [window(w)]) == [(dead_ball.GAP, (w - 500, w))])
    for label, other in (("un SET PIECES dentro del hueco", window(w - 200, kind="corner kick")),
                         ("un SET PIECES justo en el primer frame del hueco", window(w - 500)),
                         ("un GOALS dentro del hueco", window(w - 200, code="goals", kind="")),
                         ("otra ventana en el mismo frame", window(w))):
        check(label + ": no se puntúa",
              result(*ball((w - 500, w)), [other, window(w)])[-1] == (dead_ball.RESTART_INSIDE, None))
    check("un SET PIECES justo antes del hueco no lo anula",
          result(*ball((w - 500, w)), [window(w - 501), window(w)])[-1] == (dead_ball.GAP, (w - 500, w)))
    path = smart_tagging_xml(folder, "huecos.xml", [
        ("SET PIECES", 100, 105, "Kick Off (Start)"), ("SET PIECES", 200, 205, "kick off (after goal)"),
        ("SET PIECES", w / fps, w / fps + 35, "THROW-IN"), ("GOALS", 150, 160, None)])
    events = dead_ball.smart_tagging_events(path, fps)
    windows = [e["type"] for e, _, _ in dead_ball.gaps_before_restarts(*ball(), events, fps)]
    check("los saques iniciales no entran y los tipos van en minúsculas", windows == ["throw-in"], str(windows))
    check("una ventana que empieza en el frame 0 o fuera del tracking no entra",
          result(*ball(), [window(0), window(n + 1), window(w)]) == [(dead_ball.BALL_SEEN, None)])
    try:
        dead_ball.gap_before(dead_ball.last_seen_before(*ball()), 0, [], fps)
        check("gap_before con inicio 0 da error", False)
    except ValueError:
        check("gap_before con inicio 0 da error", True)
    check("sin balón visto antes de la ventana: el hueco empieza en el frame 0",
          result(*ball((0, 1000)), [window(1000)]) == [(dead_ball.GAP, (0, 1000))])

    # La capa en evidence: GAP_SCORE en la columna D del hueco, nada más (con el tamaño del partido).
    n_frames = games.GAMES[game]["n_video_frames"]
    w = 50000
    bx = np.zeros(n_frames)
    bx[w - 500:w] = np.nan
    path = smart_tagging_xml(folder, "evidence_hueco.xml", [
        ("SET PIECES", w / fps, w / fps + 35, "Corner Kick"), ("SET PIECES", 3000, 3035, "Throw-in")])
    trk = tracking.Tracking(bx, bx.copy(), np.empty((n_frames, 0)), np.empty((n_frames, 0)),
                            np.empty(0, dtype=np.int8), games.GAMES[game]["pitch"],
                            tracking.evaluated_blocks(game), fps)
    score, allowed = dead_ball.evidence(trk, {"smart_tagging": path}, game)
    expected = np.zeros(n_frames)
    expected[w - 500:w] = dead_ball.GAP_SCORE
    check("evidence con rutas: GAP_SCORE en D justo en el hueco, nada en H ni A, y no prohíbe más",
          bool(np.array_equal(score[:, tracking.D], expected)) and not score[:, :2].any()
          and bool(np.array_equal(allowed, dead_ball.evidence(trk, None, game)[1])))
    first_stop = tracking.evaluated_blocks(game)[0][1]  # primer frame después de la 1ª parte evaluada

    def scored(start):
        """Frames de D puntuados con un hueco de 20 s antes de una ventana que empieza en `start`."""
        bx = np.zeros(n_frames)
        bx[start - 500:start] = np.nan
        path = smart_tagging_xml(folder, "borde.xml", [("SET PIECES", start / fps, start / fps + 35, "Throw-in")])
        trk = tracking.Tracking(bx, bx.copy(), np.empty((n_frames, 0)), np.empty((n_frames, 0)),
                                np.empty(0, dtype=np.int8), games.GAMES[game]["pitch"],
                                tracking.evaluated_blocks(game), fps)
        return int(np.count_nonzero(dead_ball.evidence(trk, {"smart_tagging": path}, game)[0][:, tracking.D]))

    check("ventana en el último frame evaluado: puntúa; justo después del tramo: no (como se midió)",
          scored(first_stop - 1) == 500 and scored(first_stop) == 0,
          "{} y {}".format(scored(first_stop - 1), scored(first_stop)))
    check("la puntuación del hueco es la de la regla: 1 por frame, sin ajustar (docs/decisiones.md)",
          dead_ball.GAP_SCORE == 1.0)
    check("evidence sin rutas no puntúa el hueco (no abre el Smart Tagging)",
          not dead_ball.evidence(trk, None, game)[0].any())


def synthetic_match(game, variant=""):
    """(tracking, eventos) de un partido inventado en memoria, para la regla de agregados_dead_ball.py.

    - Juego: el balón va y viene por el eje largo, 10 s deprisa (10 m/s) y 10 s despacio (1 m/s), y 4 slots
      lo siguen con un desfase fijo.
    - Balón muerto: balón y jugadores quietos en el tramo antes del saque y de cada gol a su saque.
    - Huecos: sin balón los segundos fijados antes de algunas ventanas; ahí los jugadores se paran.
    - Fuera de los tramos evaluados, el balón quieto en el centro.

    Variantes, cada una para que falle una parte de la regla:
    - "gol_falso": entre el primer gol y su saque hay juego;
    - "gol_temprano" y "saque_tarde": 5 s de juego deprisa al principio o al final de cada tramo de gol a
      saque (fallan las suposiciones (a) o (b));
    - "sin_balon_en_goles" y "sin_balon_en_control": no se ve el balón en esos tramos;
    - "juego_lento": el balón nunca va deprisa, así que el placebo no puede fallar;
    - "sin_goles";
    - "control_en_juego": en el tramo antes del saque, que es el control, hay juego;
    - "jugadores_en_control": en el control el balón está quieto, pero los jugadores corren;
    - "huecos_en_juego": en los huecos los jugadores siguen corriendo;
    - "pocos_huecos": solo hay hueco antes de 2 de las 8 ventanas;
    - "huecos_por_todo": el balón falta 45 s de cada minuto en todo el partido, no solo antes de los
      reinicios.
    """
    info = games.GAMES[game]
    n, fps = info["n_video_frames"], info["fps"]
    length, width = info["pitch"]
    t = np.arange(n) / fps
    if variant == "juego_lento":
        x = length / 2 + 3 * np.sin(2 * np.pi * t / 60)  # 0,3 m/s como mucho
    else:
        step = np.where(t % 20 < 10, 10.0, 1.0) * np.where((t // 4) % 2 == 0, 1.0, -1.0) / fps
        x = length / 2 + np.cumsum(step) % 60 - 30
    graded = np.zeros(n, dtype=bool)
    for first, stop in tracking.evaluated_blocks(game):
        graded[first:stop] = True
    x[~graded] = length / 2  # fuera de lo evaluado, el balón quieto: no debe contar para nada
    y = np.full(n, width / 2)
    rows = [  # (código, tipo, inicio_s, fin_s, segundos sin balón antes del inicio)
        ("set pieces", "throw-in", 460, 495, 0), ("goals", "", 1000, 1010, 0),
        ("set pieces", "kick off (after goal)", 1100, 1105, 0),
        ("set pieces", "corner kick", 1500, 1535, 20), ("set pieces", "goal kick", 1600, 1635, 10),
        ("set pieces", "throw-in", 1700, 1735, 0), ("set pieces", "free kick", 1800, 1835, 70),
        ("set pieces", "throw-in", 2000, 2035, 8), ("set pieces", "corner kick", 2500, 2535, 15),
        ("goals", "", 6000, 6012.5, 0), ("set pieces", "kick off (after goal)", 6080, 6085, 0),
        ("set pieces", "corner kick", 6500, 6535, 12)]
    if variant == "sin_goles":
        rows = [r for r in rows if r[0] != "goals" and r[1] != "kick off (after goal)"]
    if variant == "pocos_huecos":
        rows = [r if r[2] in (1500, 1600) else r[:4] + (0,) for r in rows]
    events = [{"code": code, "type": kind, "start": int(round(s * fps)), "end": int(round(e * fps))}
              for code, kind, s, e, _ in rows]
    pre = dead_ball.pre_kickoff(game)
    dead = pre.copy() if variant != "control_en_juego" else np.zeros(n, dtype=bool)
    goals = [e for e in events if e["code"] == "goals"]
    kicks = [e for e in events if e["type"] == "kick off (after goal)"]
    for i, (goal, kick) in enumerate(zip(goals, kicks)):
        if not (variant == "gol_falso" and i == 0):
            dead[goal["end"]:kick["start"]] = True
    motion = x.copy()  # el movimiento de juego, antes de parar el balón
    x[dead], y[dead] = length / 2, width / 2
    edges = {"gol_temprano": lambda goal, kick: slice(goal["end"], goal["end"] + 5 * fps),
             "saque_tarde": lambda goal, kick: slice(kick["start"] - 5 * fps, kick["start"])}
    if variant in edges:
        for goal, kick in zip(goals, kicks):
            seg = edges[variant](goal, kick)
            x[seg] = length / 2 + 10 * np.sin(2 * np.pi * t[seg] / 4)  # unos 9 m/s de media a 1 s
    running = x.copy()
    for event, row in zip(events, rows):
        x[event["start"] - row[4] * fps:event["start"]] = np.nan
    if variant == "huecos_por_todo":
        x[(t % 60) < 45] = np.nan
    if variant == "sin_balon_en_goles":
        for goal, kick in zip(goals, kicks):
            x[goal["end"]:kick["start"]] = np.nan
    if variant == "sin_balon_en_control":
        x[pre] = np.nan
    y[np.isnan(x)] = np.nan
    anchor = running if variant == "huecos_en_juego" else np.where(np.isnan(x), length / 2, x)
    if variant == "jugadores_en_control":
        anchor = np.where(pre, motion, anchor)
    offsets = ((-5, -3), (4, 6), (-8, 2), (6, -7))
    px = np.stack([anchor + dx for dx, _ in offsets], axis=1)
    py = np.stack([np.full(n, width / 2 + dy) for _, dy in offsets], axis=1)
    trk = tracking.Tracking(x, y, px, py, np.array([0, 1, 0, 1], dtype=np.int8), (length, width),
                            tracking.evaluated_blocks(game), fps)
    return trk, sorted(events, key=lambda e: (e["start"], e["end"], e["code"], e["type"]))


def check_rules(game):
    """La regla de agregados_dead_ball.py con el partido inventado y en sus umbrales exactos.

    Importa sus cuentas (`measure`, `goal_rule`, `gap_rule` y `dead_share`), nunca su `main`, que es lo que
    lee el partido, y llama a `measure` con la apertura de ficheros prohibida (pp.no_files), como hace
    prueba_perfil_atd.py. Si alguien añade una lectura fuera de `main`, falla aquí en vez de leer el partido.
    """
    sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
    import agregados_dead_ball as agg  # solo sus cuentas

    fps = games.GAMES[game]["fps"]
    PASS, FAIL, UNDECIDED = agg.PASS, agg.FAIL, agg.UNDECIDED

    def measure(variant=""):
        trk, events = synthetic_match(game, variant)
        try:
            with pp.no_files():
                return agg.measure(trk, events, game)
        except AssertionError:
            check("measure no abre ningún fichero ({})".format(variant or "partido normal"), False)
            raise

    m = measure()
    check("partido inventado: entran las dos capas", m["gol_entra"] and m["hueco_entra"],
          "control {} placebo {} tramos {}".format(m["control_ok"], m["power"], m["spans_ok"]))
    check("partido inventado: 2 goles anclan, 3.938 frames, y todos sus bordes deciden",
          m["spans"] == 2 and m["anchored_frames"] == 3938 and m["undecided_edges"] == (0, 0),
          "{} y {}".format(m["spans"], m["anchored_frames"]))
    expected_states = {dead_ball.GAP: 5, dead_ball.BALL_SEEN: 2, dead_ball.GAP_TOO_LONG: 1,
                       dead_ball.RESTART_INSIDE: 0}
    check("partido inventado: 8 ventanas, 5 con hueco que puntúa (cobertura 5/8), 65 s de hueco",
          m["windows"] == 8 and m["states"] == expected_states and m["gap_frames"] == 65 * fps
          and m["coverage"] == 5 / 8, "{} {} {}".format(m["windows"], m["states"], m["gap_frames"]))
    check("partido inventado: placebo del hueco con 2 de 45 inicios (3 caen fuera de lo evaluado)",
          m["shifted"] == 45 and m["placebo_gaps"] == 2 and m["coverage_placebo"] == 2 / 45,
          "{} de {}".format(m["placebo_gaps"], m["shifted"]))
    trk, _ = synthetic_match(game)
    graded = np.zeros(len(trk.bx), dtype=bool)
    for first, stop in trk.blocks:
        graded[first:stop] = True
    seen = ~np.isnan(trk.bx) & graded
    fast = seen & (agg.ball_speed(trk.bx, trk.by) >= agg.FAST_BALL_MS)
    check("partido inventado: el balón deprisa se cuenta solo en lo evaluado, y el límite es la mitad",
          m["f_match"] == fast.sum() / seen.sum() and m["limit"] == 0.5 * m["f_match"],
          "{:.4f}".format(m["f_match"]))

    m = measure("gol_falso")
    check("un gol falso: falla su tramo entero y gol a saque no entra; el hueco sí",
          not m["gol_entra"] and m["n_fail"] == 1 and m["fails_by_test"][0] == 1 and m["hueco_entra"])
    for variant, test, name in (("gol_temprano", 1, "la ventana GOALS acaba antes del gol: falla el borde inicial"),
                                ("saque_tarde", 2, "la del saque empieza tarde: falla el borde final")):
        m = measure(variant)
        check(name + " (no el tramo entero) y gol a saque no entra",
              not m["gol_entra"] and m["fails_by_test"][test] == 2 and m["fails_by_test"][0] == 0,
              "fallos por prueba {}".format(m["fails_by_test"]))
    m = measure("sin_balon_en_goles")
    check("sin balón en los tramos: ninguno decide, sus 2 bordes de cada lado tampoco, y gol a saque no entra",
          m["n_pass"] == m["n_fail"] == 0 and m["undecided_edges"] == (2, 2) and not m["spans_ok"]
          and not m["gol_entra"])
    m = measure("sin_balon_en_control")
    check("sin balón en el control: el control no decide y gol a saque no entra",
          m["control"] == [UNDECIDED] and not m["control_ok"] and not m["gol_entra"], str(m["control"]))
    m = measure("juego_lento")
    check("el balón nunca va deprisa: el placebo no falla, no tiene potencia y gol a saque no entra",
          m["placebo_fail"] == 0 and not m["power"] and not m["gol_entra"])
    m = measure("sin_goles")
    check("sin goles: gol a saque no entra y el placebo no tiene potencia",
          not m["gol_entra"] and m["spans"] == 0 and not m["power"])
    m = measure("control_en_juego")
    check("con juego en el control: el control falla y no entra ninguna de las dos capas",
          m["control"] == [FAIL] and not m["gol_entra"] and not m["instrument"] and not m["hueco_entra"],
          "control {} modelo de Ana: partido {} control {}".format(
              m["control"], agg.share(m["g_match"]), agg.share(m["g_ctrl"])))
    m = measure("huecos_en_juego")
    check("jugadores corriendo en los huecos: el hueco no entra; gol a saque sí",
          m["gol_entra"] and not m["hueco_entra"] and m["instrument"] and not m["looks_dead"])
    m = measure("pocos_huecos")
    check("hueco solo antes de 2 de 8 ventanas: cobertura 2/8 y el hueco no entra",
          m["coverage"] == 2 / 8 and not m["covers"] and not m["hueco_entra"])
    m = measure("jugadores_en_control")
    check("jugadores corriendo en el control: los tramos de gol a saque lo completan y el hueco entra",
          m["gol_entra"] and m["instrument"] and m["hueco_entra"],
          "modelo de Ana: partido {} control {}".format(agg.share(m["g_match"]), agg.share(m["g_ctrl"])))
    m = measure("huecos_por_todo")
    check("sin balón a menudo en todo el partido: el hueco no gana al placebo y no entra",
          not m["beats_placebo"] and not m["hueco_entra"],
          "cobertura {} placebo {}".format(agg.share(m["coverage"]), agg.share(m["coverage_placebo"])))

    # Las dos reglas en sus umbrales exactos (números exactos en binario: 0,25, 0,5 y 0,75).
    two_pass, placebo_ok = [PASS, PASS], [FAIL, FAIL, PASS, PASS, UNDECIDED]
    rule = agg.goal_rule
    check("gol a saque, en el límite: entra", rule(two_pass, [PASS], placebo_ok) == (True, True, True, True))
    check("gol a saque: pasa la mitad justa y el resto no decide: entra",
          rule([PASS, UNDECIDED], [PASS], placebo_ok)[3])
    check("gol a saque: ninguno pasa: no entra", not rule([UNDECIDED, UNDECIDED], [PASS], placebo_ok)[3])
    check("gol a saque: uno falla: no entra", not rule([PASS, FAIL], [PASS], placebo_ok)[3])
    check("gol a saque: el control no decide, falla o no hay: no entra",
          not any(rule(two_pass, control, placebo_ok)[0] for control in ([UNDECIDED], [PASS, FAIL], [])))
    check("gol a saque: el placebo decide 3 veces (menos del doble de 2): sin potencia",
          not rule(two_pass, [PASS], [FAIL, FAIL, PASS, UNDECIDED])[1])
    check("gol a saque: el placebo falla 1 de 4 (menos de la mitad): sin potencia",
          not rule(two_pass, [PASS], [FAIL, PASS, PASS, PASS])[1])
    gap = agg.gap_rule
    nan = float("nan")
    check("hueco, en el límite: entra", gap(0.5, 0.25, 0.25, 0.75, 0.5) == (True, True, True, True, True))
    covers, *_, enters = gap(0.4999, 0.0, 0.25, 0.75, 0.5)
    check("hueco: cobertura por debajo del 50 %: no entra", not covers and not enters)
    check("hueco: cobertura por debajo del doble del placebo: no entra", not gap(0.5, 0.2501, 0.25, 0.75, 0.5)[4])
    check("hueco: por debajo del punto medio: no entra", not gap(0.5, 0.25, 0.25, 0.75, 0.4999)[4])
    check("hueco: el control no ve más D que el partido: el instrumento no separa",
          gap(0.5, 0.25, 0.5, 0.5, 1.0)[2:] == (False, False, False))
    check("hueco: un NaN (placebo, control o huecos) no deja entrar",
          not any(gap(*values)[4] for values in ((0.5, nan, 0.25, 0.75, 0.5), (0.5, 0.25, 0.25, nan, 0.5),
                                                 (0.5, 0.25, 0.25, 0.75, nan))))
    # Dónde miran los bordes: desde 1 s dentro y durante 5 s, con arrays hechos a mano (todo visto).
    seen = np.ones(4000, dtype=bool)

    def verdict_with_fast(lo, hi):
        fast = np.zeros(4000, dtype=bool)
        fast[lo:hi] = True
        return agg.span_verdict(1000, 3000, seen, fast, 0.1)[1]

    check("balón deprisa solo en el primer segundo del tramo: el borde inicial no lo ve",
          verdict_with_fast(1000, 1000 + fps) == (PASS, PASS, PASS))
    check("deprisa desde el segundo 1: falla el borde inicial",
          verdict_with_fast(1000 + fps, 1000 + 2 * fps) == (PASS, FAIL, PASS))
    check("deprisa justo después de los 5 s del borde: no cuenta",
          verdict_with_fast(1000 + 6 * fps, 1000 + 7 * fps) == (PASS, PASS, PASS))
    def frames(lo, hi):
        mask = np.zeros(4000, dtype=bool)
        mask[lo:hi] = True
        return mask

    check("en el límite: de 200 frames vistos, 50 deprisa con límite 0,25 pasa y 51 falla",
          agg.fast_test(1000, 1200, seen, frames(1000, 1050), 0.25) == PASS
          and agg.fast_test(1000, 1200, seen, frames(1000, 1051), 0.25) == FAIL)
    check("en el límite: con 24 frames vistos no decide y con 25 sí",
          agg.fast_test(1000, 1200, frames(1000, 1024), frames(0, 0), 0.25) == UNDECIDED
          and agg.fast_test(1000, 1200, frames(1000, 1025), frames(0, 0), 0.25) == PASS)
    check("lo mismo en el borde final: el último segundo no cuenta y el anterior sí",
          verdict_with_fast(3000 - fps, 3000) == (PASS, PASS, PASS)
          and verdict_with_fast(3000 - 2 * fps, 3000 - fps) == (PASS, PASS, FAIL))
    blocked = np.zeros(200000, dtype=bool)
    blocked[20000 + 240 * fps:20100 + 240 * fps] = True
    shifted = agg.shifted_spans([(20000, 20100)], ((0, 200000),), blocked, fps)
    check("el placebo no usa tramos desplazados que pisan un ancla",
          len(shifted) == 5 and (20000 + 240 * fps, 20100 + 240 * fps) not in shifted, str(len(shifted)))
    odds = np.array([0.0, 0.0, 1.0, -1.0])
    check("el modelo de Ana solo cuenta donde opina",
          agg.dead_share(odds, np.ones(4, dtype=bool)) == 0.5
          and np.isnan(agg.dead_share(odds, np.array([True, True, False, False]))))


def check_restart_instant(game, folder):
    """El instante del reinicio: la capa del ancla (fuera de evidence hasta que pase su regla) y las cuentas
    de validation/partido/agregados_instante_reinicio.py, con datos inventados. Importa sus funciones, nunca
    su `main`, y llama a `measure_instant` con la apertura de ficheros prohibida."""
    sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
    import agregados_instante_reinicio as air  # solo sus cuentas

    fps = games.GAMES[game]["fps"]
    n = games.GAMES[game]["n_video_frames"]
    length, width = games.GAMES[game]["pitch"]
    blocks = tracking.evaluated_blocks(game)
    H, A, D = tracking.H, tracking.A, tracking.D

    check("la regla está congelada: sostén 2 s, búsqueda 10 s, 10 ventanas, recorrido 2 s, 5 balones, 1 s, "
          "«otros» por debajo de 5, placebo a ±4, 6 y 8 min, banda del 15 al 60 % y 250 paradas, y los "
          "descriptivos",
          (air.SUSTAIN_S, air.SEARCH_AFTER_S, air.MIN_WINDOWS, air.MAX_IQR_S, air.MIN_BALL, air.MAX_AGREE_S,
           air.MIN_CASES_PER_TYPE, air.PLACEBO_SHIFTS_S, air.BAND_D, air.MAX_STOPS, air.NEAR_S,
           air.FIRST_SECONDS_S, air.OFF_DURATION_S, air.GAP_D_EDGES_S, air.SHARP_S, air.SHARP_NUM, air.SHARP_DEN,
           air.agg.FAST_BALL_MS)
          == (2, 10, 10, 2.0, 5, 1.0, 5, (-480, -360, -240, 240, 360, 480), (0.15, 0.60), 250, 1.0, 5, 1.0,
              (0, 1, 3, 5), 1.0, 4, 5, 5.0))
    check("band_ok: del 15 al 60 % de D, ambos incluidos, y 250 paradas como mucho",
          air.band_ok(0.15, 250) and air.band_ok(0.60, 10) and not air.band_ok(0.1499, 10)
          and not air.band_ok(0.6001, 10) and not air.band_ok(0.3, 251))
    check("tight: 10 transiciones o más con recorrido de 50 frames o menos (50 justos, también)",
          air.tight([170] * 4 + [195] * 3 + [220] * 4, 25) and air.tight([170] * 3 + [195] * 4 + [220] * 3, 25)
          and not air.tight([170] * 3 + [195] * 3 + [220] * 3, 25)
          and not air.tight([100] * 5 + [200] * 5, 25))
    gaps = np.array([H, H, D, D, H, H, H, D, H, H], dtype=np.int8)
    check("gap_d_offsets: desde el inicio del hueco hasta el del D que lo toca (negativo si venía de antes), o "
          "None", air.gap_d_offsets(gaps, [(3, 6), (4, 7), (5, 9), (2, 4)]) == [-1, None, 2, 0])
    possession_dir = os.path.join(ROOT, "possession")
    prints = []
    for name, content in (("unix", b"x = 1\n"), ("windows", b"x = 1\r\n"), ("otro", b"x = 2\n")):
        os.makedirs(os.path.join(folder, name))
        with open(os.path.join(folder, name, "a.py"), "wb") as handle:
            handle.write(content)
        prints.append(air.code_fingerprint(os.path.join(folder, name)))
    check("code_fingerprint: corta, estable, igual con finales de línea de Windows y distinta si cambia el código",
          len(air.code_fingerprint(possession_dir)) == 12
          and air.code_fingerprint(possession_dir) == air.code_fingerprint(possession_dir)
          and prints[0] == prints[1] != prints[2])

    # Las dos señales.
    odds = np.array([1, 1, 1, -1, -1, -1, 1, 0, -1, -1, -1], dtype=float)
    check("play_transition: de log-odds > 0 a < 0 sostenido; un 0 antes no cuenta, y sin sostén no hay",
          air.play_transition(odds, 0, 11, 3) == 3 and air.play_transition(odds, 4, 11, 3) is None
          and air.play_transition(odds, 0, 11, 4) is None and air.play_transition(odds, 0, 5, 2) == 3)
    seen = np.array([1, 1, 0, 0, 0, 1, 1, 0, 0], dtype=bool)
    check("ball_back: mira el frame anterior al inicio (visto, vuelve a verse y cuándo, o no vuelve)",
          air.ball_back(seen, 1, 9) == (air.SEEN_AT_START, None) and air.ball_back(seen, 2, 9)[0] == air.SEEN_AT_START
          and air.ball_back(seen, 3, 9) == (air.BACK, 5) and air.ball_back(seen, 5, 9) == (air.BACK, 5)
          and air.ball_back(seen, 8, 9) == (air.NOT_BACK, None) and air.ball_back(seen, 3, 3) == (air.NOT_BACK, None))

    # La regla de un tipo, en frames y en sus límites. 11 transiciones con mediana 195, recorrido intercuartílico
    # de 50 frames justos (2 s, de 170 a 220) y colas (p10 y p90) más anchas. En segundos, 220/25 − 170/25 y
    # 220/25 − 195/25 se pasan de 2 y de 1 por la coma flotante: en frames, no.
    base = [20, 95, 170, 170, 195, 195, 195, 220, 220, 295, 370]
    wide = [20, 95, 169, 169, 195, 195, 195, 220, 220, 295, 370]  # recorrido de 51 frames
    ten = [170, 170, 170, 195, 195, 195, 195, 220, 220, 220]  # exactamente 10, mediana 195
    ball = [220] * 5  # a 25 frames justos (1 s) de la mediana
    beats = [(t, 220) for t in base[:5]]  # al ancla fija (195) hay 25; a su transición, mediana 50
    check("anchor_rule: con recorrido de 2 s justos y el balón a 1 s justo (en frames, sin coma flotante), y el "
          "ancla fija más cerca del balón que cada transición: entra; también con 10 transiciones justas",
          air.anchor_rule(base, ball, beats, fps) == (True, True, True, True, True)
          and air.anchor_rule(ten, ball, [(t, 220) for t in ten[:5]], fps) == (True, True, True, True, True)
          and 220 / fps - 170 / fps > air.MAX_IQR_S and 220 / fps - 195 / fps > air.MAX_AGREE_S)
    check("anchor_rule: no entra con recorrido de más de 2 s, el balón a más de 1 s, menos de 5 balones o pares, "
          "9 transiciones, o el ancla fija igual o peor que la transición de cada ventana",
          air.anchor_rule(wide, ball, beats, fps)[1:] == (False, True, True, False)
          and air.anchor_rule(base, [221] * 5, beats, fps)[2:] == (False, True, False)
          and air.anchor_rule(base, ball[:4], beats, fps)[2:] == (False, True, False)
          and air.anchor_rule(base, ball, beats[:4], fps)[3:] == (False, False)
          and air.anchor_rule(ten[:9], ball, beats, fps) == (False, False, False, False, False)
          and air.anchor_rule(base, ball, [(195, 220)] * 5, fps)[3:] == (False, False)
          and air.anchor_rule(base, ball, [(220, 220)] * 5, fps)[3:] == (False, False))
    check("anchor_of: la mediana de la transición, en frames", air.anchor_of(base) == 195 and air.anchor_of(ten) == 195)

    # La capa del ancla y sus cortes.
    w = 1000 * fps

    def window(start, kind="throw-in", code="set pieces"):
        return {"code": code, "type": kind, "team": "n/a", "start": start, "end": start + 35 * fps}

    anchors = {"throw-in": 10 * fps}
    spans = dead_ball.restart_anchor_spans([window(w)], anchors, blocks, fps)
    check("restart_anchor_spans: instante en el inicio más el ancla, y el corte en el siguiente reinicio",
          [(s, i, c) for _, s, i, c in spans] == [(w, w + 10 * fps, np.inf)])
    cut = dead_ball.restart_anchor_spans([window(w), window(w + 12 * fps, "corner kick")], anchors, blocks, fps)
    late = dead_ball.restart_anchor_spans([window(w), window(w + 8 * fps, code="goals")], anchors, blocks, fps)
    equal = dead_ball.restart_anchor_spans([window(w), window(w + 10 * fps, "corner kick")], anchors, blocks, fps)
    same = dead_ball.restart_anchor_spans([window(w), window(w, "corner kick")], anchors, blocks, fps)
    check("restart_anchor_spans: si el instante cae en el corte o después, o otro reinicio empieza en el mismo "
          "frame, la ventana no entra",
          [(s, i, c) for _, s, i, c in cut] == [(w, w + 10 * fps, w + 12 * fps)] and late == [] and equal == []
          and same == [])
    check("restart_anchor_spans: ni saques iniciales (aunque tengan ancla), ni tipos sin ancla, ni fuera de lo "
          "evaluado",
          dead_ball.restart_anchor_spans([window(w, "kick off (after goal)")], {"kick off (after goal)": 0},
                                         blocks, fps) == []
          and dead_ball.restart_anchor_spans([window(w, "corner kick"), window(100 * fps)], anchors, blocks, fps)
          == [])
    alone, other = window(w), window(w + 50 * fps, code="goals")
    check("next_restart: el siguiente GOALS o SET PIECES (también en el mismo frame), o infinito",
          dead_ball.next_restart([alone], alone) == np.inf
          and dead_ball.next_restart([alone, other, window(w + 60 * fps)], alone) == w + 50 * fps
          and dead_ball.next_restart([alone, window(w, "corner kick")], alone) == w
          and dead_ball.next_restart([window(w - fps), alone], alone) == np.inf)
    check("search_stop y harm_stop: 10 s tras el fin de la ventana (o de la capa, si acaba después), sin pasar "
          "del siguiente reinicio",
          air.search_stop(alone, np.inf, fps) == w + 45 * fps and air.search_stop(alone, w + 20 * fps, fps) == w + 20 * fps
          and air.harm_stop(alone, np.inf, w + 15 * fps, fps) == w + 45 * fps
          and air.harm_stop(alone, np.inf, w + 40 * fps, fps) == w + 50 * fps
          and air.harm_stop(alone, w + 30 * fps, w + 15 * fps, fps) == w + 30 * fps)
    check("la capa es la de la regla: 1 por frame (la escala de GAP_SCORE), 3 s antes del instante sin hueco y 3 s "
          "después con A, sin ajustar",
          (dead_ball.ANCHOR_SCORE, dead_ball.GAP_SCORE, dead_ball.PUSH_BEFORE_S, dead_ball.PUSH_AFTER_S)
          == (1.0, 1.0, 3, 3) and (dead_ball.BRIDGE, dead_ball.BOTH_SIDES) == ("B", "A"))

    # Los empujes de cada candidato. Una ventana con hueco (sin balón los 10 s de antes) y otra con el balón a
    # la vista hasta su inicio; el instante a los 10 s.
    gap_w, seen_w = window(w), window(w + 100 * fps)
    bx = np.zeros(n)
    bx[w - 10 * fps:w + 2 * fps] = np.nan
    bx[w + 100 * fps:w + 102 * fps] = np.nan
    trk = tracking.Tracking(bx, bx.copy(), np.empty((n, 0)), np.empty((n, 0)), np.empty(0, dtype=np.int8),
                            (length, width), blocks, fps)
    both = [gap_w, seen_w]

    def pushes(modes, tagged=both, anchor=10 * fps):
        return [(win is gap_w, has_gap, a, i, b) for win, has_gap, a, i, b in
                dead_ball.restart_anchor_pushes(bx, bx, tagged, {"throw-in": anchor}, modes, blocks, fps)]

    i0, i1 = w + 10 * fps, w + 110 * fps
    check("restart_anchor_pushes, B: solo la ventana con hueco, a D desde su inicio hasta el instante, nada después",
          pushes({"throw-in": "B"}) == [(True, True, w, i0, i0)])
    check("restart_anchor_pushes, A: con hueco, desde el inicio; sin hueco, solo 3 s antes; y 3 s después en las "
          "dos",
          pushes({"throw-in": "A"}) == [(True, True, w, i0, i0 + 3 * fps), (False, False, i1 - 3 * fps, i1, i1 + 3 * fps)])
    check("restart_anchor_pushes: sin hueco y con el instante a menos de 3 s del inicio, desde el inicio; el empuje "
          "de después se corta en el siguiente reinicio; un tipo sin modo no entra",
          pushes({"throw-in": "A"}, [seen_w], anchor=fps) == [(False, False, i1 - 10 * fps, i1 - 9 * fps,
                                                               i1 - 6 * fps)]
          and pushes({"throw-in": "A"}, [seen_w, window(i1 + fps, code="goals")]) == [(False, False, i1 - 3 * fps, i1,
                                                                                       i1 + fps)]
          and pushes({}) == [])
    try:
        pushes({"throw-in": "C"})
        unknown_mode = False
    except ValueError:
        unknown_mode = True
    check("restart_anchor_pushes: un modo desconocido es un error", unknown_mode)
    score, allowed = dead_ball.restart_anchor_evidence(trk, both, {"throw-in": 10 * fps}, {"throw-in": "A"})
    expected = np.zeros((n, 3))
    expected[w:i0, D] = 1.0
    expected[i0:i0 + 3 * fps, D] = -1.0
    expected[i1 - 3 * fps:i1, D] = 1.0
    expected[i1:i1 + 3 * fps, D] = -1.0
    check("restart_anchor_evidence: los empujes de restart_anchor_pushes, en la columna D; no prohíbe nada",
          bool(np.array_equal(score, expected)) and bool(allowed.all()))
    anchored = smart_tagging_xml(folder, "ancla.xml", [("SET PIECES", w / fps, w / fps + 35, "Throw-in")])
    check("el ancla no entra todavía en evidence (con un saque de banda y sin huecos, no puntúa nada)",
          not dead_ball.evidence(tracking.Tracking(np.zeros(n), np.zeros(n), np.empty((n, 0)), np.empty((n, 0)),
                                                   np.empty(0, dtype=np.int8), (length, width), blocks, fps),
                                 {"smart_tagging": anchored}, game)[0].any())

    # Las cuentas del daño y las condiciones de A.
    codes = np.array([H, D, D, H, D, H, H, D, D], dtype=np.int8)
    check("dead_runs y last_exit: tramos de D y salida del último; sin salida si el D llega al final",
          air.dead_runs(codes, 0, 9) == 3 and air.dead_runs(codes, 0, 3) == 1 and air.last_exit(codes, 0, 6) == 5
          and air.last_exit(codes, 0, 9) is None and air.last_exit(codes, 5, 7) is None)
    check("runs: posesiones y paradas", air.runs(codes, ((0, 9),)) == (3, 3))

    def runs_of(*spans):
        codes = np.full(20, H, dtype=np.int8)
        for a, b in spans:
            codes[a:b] = D
        return codes

    none, one, two, three = runs_of(), runs_of((2, 5)), runs_of((2, 5), (8, 10)), runs_of((2, 5), (8, 10), (12, 14))
    check("worse: la capa parte la parada si deja 2 tramos de D o más y más que sin ella (de 0 a 1 no cuenta)",
          not air.worse(none, one, 0, 20) and air.worse(none, two, 0, 20) and air.worse(one, two, 0, 20)
          and not air.worse(two, two, 0, 20) and air.worse(two, three, 0, 20) and not air.worse(one, one, 0, 20)
          and not air.worse(none, two, 0, 6))
    check("harm_rule: ninguna ventana partida y las posesiones no suben más que las paradas",
          air.harm_rule((10, 5), (11, 6), 0) and air.harm_rule((10, 5), (9, 5), 0)
          and not air.harm_rule((10, 5), (11, 5), 0) and not air.harm_rule((10, 5), (10, 5), 1))
    check("cases: los recuentos por debajo de 5 se tapan", air.cases(4) == "< 5" and air.cases(0) == "< 5"
          and air.cases(5) == "5")
    check("model_fingerprint: corta, estable y distinta si cambia el modelo",
          air.model_fingerprint({"a": 1, "b": [2]}) == air.model_fingerprint({"b": [2], "a": 1})
          and air.model_fingerprint({"a": 1}) != air.model_fingerprint({"a": 2})
          and len(air.model_fingerprint({"a": 1})) == 12)
    check("A es nítido con el 80 % justo de las ventanas a menos de 1 s (24 frames sí, 25 no), con las que no "
          "tienen transición contando como lejos, y con 10 ventanas o más",
          air.sharp([100] * 8 + [124, 76], 10, 25) and not air.sharp([100] * 7 + [125, 75, 200], 10, 25)
          and air.sharp([100] * 8, 10, 25) and not air.sharp([100] * 7, 10, 25)
          and air.sharp([100] * 10 + [400, 400], 12, 25) and not air.sharp([100] * 9 + [400] * 3, 12, 25)
          and not air.sharp([100] * 9, 9, 25) and not air.sharp([], 10, 25) and air.sharp_count([100] * 3 + [125], 25) == 3)
    check("candidates_for: primero A (A donde se cumple y B en los demás tipos) si algún tipo lo cumple, después B "
          "en todos; nada sin anclas",
          air.candidates_for({"x": 1, "y": 2}, {"x": True, "y": False})
          == [("A", {"x": "A", "y": "B"}), ("B", {"x": "B", "y": "B"})]
          and air.candidates_for({"x": 1}, {"x": False}) == [("B", {"x": "B"})]
          and air.candidates_for({"x": 1}, {"x": False, "z": True}) == [("B", {"x": "B"})]
          and air.candidates_for({}, {}) == [])
    shares = air.side_shares(np.array([-1, 1, 1, -1, 0, 1, -1, 0], dtype=float), [3], 8, 1)
    check("side_shares: proporción de D del modelo de Ana en los 3 frames de antes y de después (sin contar los 0)",
          shares == (2 / 3, 1 / 2))
    check("ana_agrees: el punto medio a cada lado, con los controles separando; un NaN o un control al revés, no",
          air.ana_agrees(0.65, 0.15, 0.3, 1.0, 0.0) and not air.ana_agrees(0.64, 0.15, 0.3, 1.0, 0.0)
          and not air.ana_agrees(0.65, 0.16, 0.3, 1.0, 0.0) and not air.ana_agrees(float("nan"), 0.1, 0.3, 1.0, 0.0)
          and not air.ana_agrees(0.9, 0.0, 0.3, 0.2, 0.0) and not air.ana_agrees(0.9, 0.0, 0.3, 1.0, 0.4))

    # measure_instant de punta a punta, sin abrir ficheros y con piezas controladas: 12 saques de banda a los
    # 1.000 s y cada 100 s. Las pares tienen hueco (sin balón desde 10 s antes); las impares, el balón a la vista
    # hasta su inicio. El balón vuelve a verse a los 8,4 s (210 frames), y el pipeline sale del D a los 9,6 s.
    # El modelo de Ana pasa a juego a los 7,6 u 8,4 s (190 o 210): nítido, con el ancla a 8 s (200), más cerca
    # del balón (10) que cada transición en las ventanas con hueco (mediana 20). Ve D antes del saque de la 2ª
    # parte (el control de D) y en una parada larga de la 2ª parte (sube el D del partido); ve juego con el
    # balón deprisa (de los 2.400 a los 2.800 s, el control de juego).
    starts = [(1000 + 100 * i) * fps for i in range(12)]
    events = [window(s) for s in starts]
    gaps = starts[0::2]
    sharp_offsets = [190, 210, 190, 210, 210, 190, 190, 210, 210, 190, 190, 210]
    blurred_offsets = [175, 200, 225, 175, 200, 225, 175, 200, 200, 225, 175, 200]
    bx = np.zeros(n)
    by = np.zeros(n)
    bx[60000:70000] = (np.arange(10000) * 0.4) % 50.0  # 10 m/s
    for s in starts:
        bx[s - (10 * fps if s in gaps else 0):s + 210] = np.nan
    match = tracking.Tracking(bx, by, np.empty((n, 0)), np.empty((n, 0)), np.empty(0, dtype=np.int8),
                              (length, width), blocks, fps)

    def ana(offsets):
        odds = np.full(n, -1.0)
        odds[dead_ball.pre_kickoff(game)] = 1.0
        odds[120000:160000] = 1.0
        for s, offset in zip(starts, offsets):
            odds[s - 10 * fps:s + offset] = 1.0
        return odds

    instrument = ana(sharp_offsets)

    def dead_piece(trk, band=40000, who=starts):
        score, allowed = tracking.no_evidence(n)
        for s in who:
            score[s:s + 240, D] = 1.0  # hasta los 9,6 s
        score[120000:120000 + band, D] = 1.0  # la parada larga: deja la entrega dentro de la banda
        return score, allowed

    def team_piece(trk):
        score, allowed = tracking.no_evidence(n)
        score[:, H] = 0.3
        return score, allowed

    def with_gap(trk):  # como la capa del hueco: empuja a D dos trozos del hueco, y el D lo cubre entero
        score, allowed = tracking.no_evidence(n)
        for s in gaps:
            score[s - 10 * fps:s - 8 * fps, D] = 5.0
            score[s - 3 * fps:s - 1 * fps, D] = 5.0
        return score, allowed

    no_gap = lambda trk: tracking.no_evidence(n)  # noqa: E731

    def measured(pieces, odds=instrument, tagged=events, trk=match):
        try:
            with pp.no_files():
                return air.measure_instant(trk, tagged, with_gap, no_gap, game, pieces=pieces,
                                           odds_fn=lambda c: odds)
        except AssertionError:
            check("measure_instant no abre ningún fichero", False)
            raise

    pieces = {"candidates": team_piece, "dead_state": dead_piece}
    m = measured(pieces)
    t = m["by_type"]["throw-in"]
    a = t.get("a", {})
    check("measure_instant: 12 ventanas de 35 s; transiciones nítidas y el balón a los 8,4 s en las 6 con hueco",
          m["windows"] == 12 and m["duration_median_s"] == 35.0 and m["off_duration"] == 0
          and t["transitions"] == sharp_offsets and t["ball"] == [210] * 6 and t["states"][air.BACK] == 6
          and t["states"][air.SEEN_AT_START] == 6 and t["pairs"] == [(o, 210) for o in sharp_offsets[0::2]])
    check("measure_instant: el ancla a 8 s (200 frames), y el placebo de la transición no se concentra",
          t["rule"] == (True, True, True, True, True) and t["placebo_ok"] and m["anchors"] == {"throw-in": 8 * fps},
          str(m["anchors"]))
    check("measure_instant: A se cumple: nítido, Ana de acuerdo a los dos lados en los dos grupos y el placebo no pasa",
          a.get("sharp") and a.get("sharp_count") == 12 and a["sides"]["con hueco"]["n"] == 6
          and a["sides"]["sin hueco"]["n"] == 6 and all(s["ok"] for s in a["sides"].values())
          and a["placebo"]["n"] >= 5 and not a["placebo"]["passes"] and a["ok"] and 0.25 < m["g_match"] < 0.35
          and m["g_dead"] == 1.0 and m["g_play"] == 0.0,
          "{} {} {}".format(a.get("sides"), a.get("placebo"), (m["g_match"], m["g_dead"], m["g_play"])))
    r = m["tested"].get("A", {})
    check("measure_instant: entra A, el primero que se prueba; con él el pipeline sale del D en el instante (antes, "
          "1,6 s tarde), y lo que cambia cae todo después del instante",
          list(m["tested"]) == ["A"] and m["chosen"] == "A" and m["entra"] and m["modes"] == {"throw-in": "A"}
          and r["pushes"] == 12 and r["with_gap"] == 6 and r["near"] == (0, 12) and r["changed_before"] == (0, 0, 0)
          and r["changed_after"] == (0, 0, 12 * 40) and r["changed_outside"] == (0, 0, 0) and r["split"] == 0
          and r["conflicts"] == (0, 0) and r["runs"][0] == r["runs"][1] and r["band_ok"] and r["ok"],
          "{} {} {} {}".format(list(m["tested"]), r.get("near"), r.get("changed_after"), r.get("runs")))
    check("measure_instant: la capa del hueco cambia 10 s de cada hueco (la mitad en sus primeros 5 s), y el D de la "
          "entrega empieza con cada hueco",
          m["gap_changed"] == 6 * 10 * fps and m["gap_changed_first"] == 6 * 5 * fps and m["gap_d_offsets"] == [0] * 6,
          "{} {} {}".format(m["gap_changed"], m["gap_changed_first"], m["gap_d_offsets"]))

    # B: con el instante borroso (7, 8 o 9 s) A no es nítido. El pipeline sale del D en el inicio de las ventanas
    # con hueco: B alarga ese D hasta el instante, sin tocar las demás.
    blurred = ana(blurred_offsets)
    m = measured({"candidates": team_piece, "dead_state": lambda trk: dead_piece(trk, who=starts[1::2])}, blurred)
    r = m["tested"].get("B", {})
    check("measure_instant: con el instante borroso A no se cumple y entra B, que alarga el D del hueco hasta el "
          "instante y no toca las ventanas sin hueco",
          m["anchors"] == {"throw-in": 8 * fps} and not m["by_type"]["throw-in"]["a"]["sharp"]
          and not m["by_type"]["throw-in"]["a"]["ok"] and list(m["tested"]) == ["B"] and m["chosen"] == "B"
          and m["modes"] == {"throw-in": "B"} and r["pushes"] == 6 and r["with_gap"] == 6 and r["near"] == (0, 6)
          and r["changed_before"] == (0, 6 * 200, 0) and r["changed_after"] == (0, 0, 0)
          and r["changed_outside"] == (0, 6 * 25, 0) and r["split"] == 0 and r["ok"],
          "{} {} {} {}".format(list(m["tested"]), r.get("near"), r.get("changed_before"), r.get("changed_outside")))

    # A no se cumple si el modelo de Ana no ve parado justo antes del instante en las ventanas sin hueco (un hueco
    # de 1,6 s de juego, demasiado corto para ser una transición).
    unsure = instrument.copy()
    for s in starts[1::2]:
        unsure[s + 130:s + 170] = -1.0
    m = measured(pieces, unsure)
    a = m["by_type"]["throw-in"]["a"]
    check("measure_instant: si Ana no ve parado antes del instante en las ventanas sin hueco, A no se cumple y entra B",
          m["by_type"]["throw-in"]["transitions"] == sharp_offsets and a["sharp"] and a["sides"]["con hueco"]["ok"]
          and not a["sides"]["sin hueco"]["ok"] and not a["ok"] and m["chosen"] == "B",
          "{} {}".format(a["sides"], m["chosen"]))

    # A no se cumple si el placebo pasa: en las ventanas desplazadas Ana ve parado justo antes del instante y juego
    # justo después (con dos destellos de D), aunque su transición queda dispersa.
    fooled = instrument.copy()
    for k, p in enumerate(air.placebo_windows(events, blocks, fps)):
        i = p["start"] + 8 * fps
        fooled[i - 3 * fps:i] = 1.0
        for b in range(25, (50, 150, 250, 350)[k % 4] + 1, 25):
            fooled[i + b] = 1.0
    m = measured(pieces, fooled)
    a = m["by_type"]["throw-in"]["a"]
    check("measure_instant: si el placebo pasa, A no se cumple y entra B, aunque el placebo de la transición no se "
          "concentre",
          m["by_type"]["throw-in"]["placebo_ok"] and len(m["by_type"]["throw-in"]["placebo"]) >= 10 and a["sharp"]
          and all(s["ok"] for s in a["sides"].values()) and a["placebo"]["passes"] and not a["ok"]
          and m["chosen"] == "B", "{} {}".format(a["placebo"], m["chosen"]))

    # A cumple sus condiciones pero no el daño, y entra B. La parada partida: en 2 ventanas el pipeline sigue en D
    # hasta los 30 s y duda entre los 8 y los 11 s; con A el D sale a los 8 s y vuelve a los 11 s.
    late = starts[10:]

    def dead_late(trk):
        score, allowed = dead_piece(trk)
        for s in late:
            score[s:s + 30 * fps, D] = 1.0
            score[s + 200:s + 275, D] = 0.5
        return score, allowed

    m = measured({"candidates": team_piece, "dead_state": dead_late})
    r = m["tested"].get("A", {})
    (poss0, stops0), (poss1, stops1) = r.get("runs", ((0, 0), (0, 0)))
    check("measure_instant: la parada partida se cuenta en A (2 ventanas), A no entra aunque las posesiones no suban "
          "más que las paradas, y entra B",
          r.get("split") == 2 and (poss1 - poss0, stops1 - stops0) == (2, 2) and not r.get("ok")
          and m["tested"]["B"]["split"] == 0 and m["tested"]["B"]["ok"] and m["chosen"] == "B",
          "{} {} {}".format(r.get("split"), r.get("runs"), m["chosen"]))

    # Una posesión sin parada: tras el instante la evidencia de equipo dice H 1,6 s y después A. Sin la capa el D
    # llega hasta los 9,6 s y se sale a A; con A se sale a los 8 s a H y luego a A.
    def dead_strong(trk):
        score, allowed = dead_piece(trk)
        for s in starts:
            score[s:s + 240, D] = 3.2
        return score, allowed

    def team_flip(trk):
        score, allowed = team_piece(trk)
        for s in starts:
            score[s + 200:s + 240, H] = 3.0
            score[s + 240:s + 60 * fps, H] = 0.0
            score[s + 240:s + 60 * fps, A] = 1.0
        return score, allowed

    m = measured({"candidates": team_flip, "dead_state": dead_strong})
    r = m["tested"].get("A", {})
    (poss0, stops0), (poss1, stops1) = r.get("runs", ((0, 0), (0, 0)))
    check("measure_instant: con una posesión nueva sin parada en cada ventana A no entra, y entra B",
          r.get("split") == 0 and (poss1 - poss0, stops1 - stops0) == (12, 0) and not r.get("ok")
          and m["chosen"] == "B", "{} {}".format(r.get("runs"), m["chosen"]))

    # Una parada que ya tiene dos tramos de D sin la capa (vuelve a D a los 20 s) y que A no empeora: no cuenta
    # como partida, y A entra.
    def dead_twice(trk):
        score, allowed = dead_piece(trk)
        for s in late:
            score[s + 500:s + 700, D] = 1.0
        return score, allowed

    m = measured({"candidates": team_piece, "dead_state": dead_twice})
    r = m["tested"].get("A", {})
    check("measure_instant: una ventana que ya tenía dos tramos de D sin la capa no cuenta como partida",
          r.get("split") == 0 and r["runs"][0] == r["runs"][1] and r["runs"][0][1] == 15 and r["ok"]
          and m["chosen"] == "A", "{} {}".format(r.get("split"), r.get("runs")))

    # Fuera de la banda (sin la parada larga, la entrega tiene menos del 15 % de D): no entra ninguno. Y justo en el
    # borde (sin la capa algo más del 15 %; con A, 480 frames menos de D, algo menos): A no entra y B, que no
    # quita D, sí.
    m = measured({"candidates": team_piece, "dead_state": lambda trk: dead_piece(trk, band=0)})
    check("measure_instant: con la entrega fuera de la banda, no entra ninguno",
          list(m["tested"]) == ["A", "B"] and not any(r["band_ok"] for r in m["tested"].values())
          and m["tested"]["A"]["dead_share"][1] < 0.15 and m["chosen"] is None and not m["entra"],
          str({k: r["dead_share"] for k, r in m["tested"].items()}))
    m = measured({"candidates": team_piece, "dead_state": lambda trk: dead_piece(trk, band=19607)})
    r = m["tested"]["A"]
    check("measure_instant: la banda se mira con la capa puesta (A: sin ella dentro, con ella fuera)",
          r["dead_share"][0] > 0.1505 and r["dead_share"][1] < 0.1495 and not r["band_ok"] and not r["ok"]
          and m["tested"]["B"]["band_ok"] and m["chosen"] == "B", str(r["dead_share"]))

    # Con piezas que se contradicen en unos frames (conflictos), no entra ninguno.
    def team_conflict(trk):
        score, allowed = team_piece(trk)
        allowed[50000:50010, :2] = False
        return score, allowed

    def dead_conflict(trk):
        score, allowed = dead_piece(trk)
        allowed[50000:50010, D] = False
        return score, allowed

    m = measured({"candidates": team_conflict, "dead_state": dead_conflict})
    check("measure_instant: con conflictos entre piezas no entra ninguno",
          m["conflicts_without"] == 10 and all(r["conflicts"] == (10, 10) and not r["ok"] for r in m["tested"].values())
          and list(m["tested"]) == ["A", "B"] and m["chosen"] is None, str(m["conflicts_without"]))

    # Las señales no se buscan más allá del siguiente reinicio: con un GOALS a los 7 s de cada ventana, ni la
    # transición (7,6 u 8,4 s) ni el balón (8,4 s) caen antes del corte, y no hay ancla.
    m = measured(pieces, tagged=events + [window(s + 7 * fps, code="goals") for s in starts])
    t = m["by_type"]["throw-in"]
    check("measure_instant: las señales se buscan solo hasta el siguiente reinicio",
          t["transitions"] == [] and t["ball"] == [] and t["states"][air.NOT_BACK] == 6 and m["anchors"] == {}
          and m["tested"] == {} and not m["entra"], str(t["states"]))

    # Tres tipos de 4 ventanas cada uno van juntos en «otros», que nunca tiene ancla.
    mixed = [window(s, ("throw-in", "corner kick", "goal kick")[i % 3]) for i, s in enumerate(starts)]
    m = measured(pieces, tagged=mixed)
    check("measure_instant: los tipos de menos de 5 ventanas van a «otros», sin ancla, y no entra ninguno",
          list(m["by_type"]) == ["otros"] and m["by_type"]["otros"]["n"] == 12
          and m["by_type"]["otros"]["rule"] == (False,) * 5 and m["anchors"] == {} and m["tested"] == {}
          and not m["entra"], str(list(m["by_type"])))

    # Con el reinicio disperso (a los 0, 2, 4 y 6 s), no hay ancla y no se prueba ningún candidato.
    scattered = ana([(i % 4) * 2 * fps for i in range(12)])
    m = measured(pieces, scattered)
    check("measure_instant: con el reinicio disperso, mucha dispersión, ninguna ancla y no entra ninguno",
          m["by_type"]["throw-in"]["rule"][1] is False and m["anchors"] == {} and not m["entra"])

    # El placebo de la transición. Las ventanas se desplazan ±4, 6 y 8 minutos; las que caen cerca de un reinicio
    # real o fuera de lo evaluado no cuentan.
    alone_at = window(1000 * fps)
    shifted = air.placebo_windows([alone_at], blocks, fps)
    near_goal = air.placebo_windows([alone_at, window(1250 * fps, code="goals")], blocks, fps)
    edge = air.placebo_windows([window(500 * fps)], blocks, fps)
    check("placebo_windows: ±4, 6 y 8 min con su tipo y duración; no cerca de un reinicio real ni fuera de lo "
          "evaluado",
          [p["start"] for p in shifted] == [(1000 + s) * fps for s in (-480, -360, -240, 240, 360, 480)]
          and all(p["end"] - p["start"] == 35 * fps and p["type"] == "throw-in" for p in shifted)
          and [p["start"] for p in near_goal] == [(1000 + s) * fps for s in (-480, -360, -240, 360, 480)]
          and [p["start"] for p in edge] == [(500 + s) * fps for s in (240, 360, 480)])

    # De punta a punta, con 10 saques de banda separados 10 minutos (5 en cada parte): sin transiciones en el
    # placebo hay ancla; si el modelo de Ana pasa a juego a los 8 s también en las ventanas desplazadas, el
    # placebo se concentra y no hay ancla.
    spaced = [s * fps for s in (500, 1100, 1700, 2300, 2900, 4500, 5100, 5700, 6300, 6900)]
    spaced_events = [window(s) for s in spaced]
    bx_spaced = np.zeros(n)
    real = np.full(n, -1.0)
    for s, offset in zip(spaced, [175, 200, 225, 175, 200, 225, 175, 200, 200, 225]):
        bx_spaced[s - 10 * fps:s + 210] = np.nan
        real[s - 10 * fps:s + offset] = 1.0
    fake = real.copy()
    for p in air.placebo_windows(spaced_events, blocks, fps):
        fake[p["start"] - 10 * fps:p["start"] + 200] = 1.0
    spaced_match = tracking.Tracking(bx_spaced, bx_spaced.copy(), np.empty((n, 0)), np.empty((n, 0)),
                                     np.empty(0, dtype=np.int8), (length, width), blocks, fps)
    results = []
    for odds_now in (real, fake):
        with pp.no_files():
            results.append(air.measure_instant(spaced_match, spaced_events, no_gap, no_gap, game,
                                               pieces={"candidates": team_piece, "dead_state": no_gap},
                                               odds_fn=lambda trk, o=odds_now: o))
    clean_placebo, concentrated = (r["by_type"]["throw-in"] for r in results)
    check("measure_instant: sin transiciones en el placebo hay ancla; con el placebo tan concentrado como las "
          "ventanas reales, no",
          clean_placebo["rule"][4] and clean_placebo["placebo_ok"] and results[0]["anchors"] == {"throw-in": 200}
          and concentrated["rule"][4] and not concentrated["placebo_ok"] and len(concentrated["placebo"]) >= 10
          and results[1]["anchors"] == {} and not results[1]["entra"],
          "{} {} {}".format(results[0]["placebo_windows"], len(concentrated["placebo"]), results[1]["anchors"]))


def main():
    game = games.GAME
    n_frames = games.GAMES[game]["n_video_frames"]
    blocks = games.half_video_blocks(game)

    print("1. Interfaz común")
    mask, opened = mask_without_opening_files(game)
    check("es un np.ndarray", isinstance(mask, np.ndarray))
    check("199.319 posiciones", mask.shape == (n_frames,), str(mask.shape))
    check("booleana", mask.dtype == bool, str(mask.dtype))
    check("no abre ningún fichero", not opened, "{} abiertos".format(len(opened)))

    print("\n2. Dónde marca D")
    graded = np.zeros(n_frames, dtype=bool)
    for _, first, last in blocks:
        graded[first:last + 1] = True
    check("nada fuera de los frames evaluados", not (mask & ~graded).any(),
          "{} frames".format(int((mask & ~graded).sum())))
    for half, first, last in blocks:
        kickoff = KICKOFF_VIDEO_FRAMES[dead_ball.HALF_NAMES[half]]
        dead = np.flatnonzero(mask[first:last + 1]) + first
        expected = max(0, kickoff - first)
        check("parte {}: {} frames D".format(half, expected), dead.size == expected,
              "tiene {}".format(dead.size))
        if dead.size:
            contiguous = dead[0] == first and dead[-1] == kickoff - 1 and dead.size == dead[-1] - dead[0] + 1
            check("parte {}: un solo tramo, del primer frame evaluado al anterior al saque".format(half),
                  contiguous)
    second_first = blocks[1][1]
    second_dead = int(mask[second_first:blocks[1][2] + 1].sum())
    check("2ª parte: los {} frames que da FAQ.md".format(FAQ_SECOND_HALF_DEAD_FRAMES),
          second_dead == FAQ_SECOND_HALF_DEAD_FRAMES, "tiene {}".format(second_dead))

    # La GT pública solo cubre el principio de la 1ª parte y esta versión solo marca la 2ª, así que
    # "ninguna contradicción" sale casi por construcción: no es una validación del detector. La que
    # aporta es la del primer frame evaluado, que confirma que la 1ª parte no tiene tramo previo.
    print("\n3. Frente a la GT pública (solo para comprobar que no se contradicen; no valida el detector)")
    with open(GT_PATH, newline="") as handle:
        rows = list(csv.reader(handle))[1:]
    labels = np.array([label for _, label in rows])
    check("la GT pública tiene 199.319 filas", labels.size == n_frames, str(labels.size))
    scored = labels != "X"
    contradictions = int((mask & scored & (labels != "D")).sum())
    check("ningún D nuestro donde la GT pública dice H o A", contradictions == 0,
          "{} frames".format(contradictions))
    first_graded = blocks[0][1]
    check("la GT pública no tiene D en el primer frame evaluado (no hay tramo antes del saque)",
          labels[first_graded] != "D")
    print("  (informativo) D de la GT pública que cubre esta versión: {} de {}".format(
        int((mask & (labels == "D")).sum()), int((labels == "D").sum())))

    print("\n4. Determinismo")
    again, _ = mask_without_opening_files(game)
    check("dos llamadas dan la misma máscara byte a byte", mask.tobytes() == again.tobytes())
    print("  sha256 {}".format(hashlib.sha256(mask.tobytes()).hexdigest()[:16]))

    print("\n5. Las dos fuentes de los frames de saque")
    for half, _, _ in blocks:
        published = KICKOFF_VIDEO_FRAMES[dead_ball.HALF_NAMES[half]]
        anchor = games.anchor_video_frame(games.GAMES[game][ANCHOR_KEYS[half]])
        check("parte {}: FAQ.md y el ancla de games.py difieren en 1 frame como mucho".format(half),
              abs(published - anchor) <= 1, "diferencia {:+d}".format(anchor - published))

    print("\n6. Otro partido")
    try:
        dead_ball.dead_mask(game="OTRO-PARTIDO")
        check("con otro partido da un error en vez de una máscara", False)
    except ValueError:
        check("con otro partido da un error en vez de una máscara", True)

    print("\n7. De cada gol a su saque, con un Smart Tagging inventado")
    folder = tempfile.mkdtemp(prefix="comprobar_balon_muerto_")
    try:
        check_goal_to_kickoff(game, folder)
        print("\n8. El hueco sin balón antes de cada reinicio (en evidence desde el 15/11)")
        check_gap_before_restart(game, folder)
    finally:
        shutil.rmtree(folder, ignore_errors=True)

    print("\n9. La regla de validation/partido/agregados_dead_ball.py, con un partido inventado en memoria")
    check_rules(game)

    print("\n11. El instante del reinicio (sin medir, todavía fuera de evidence), con datos inventados")
    folder = tempfile.mkdtemp(prefix="comprobar_balon_muerto_")
    try:
        check_restart_instant(game, folder)
    finally:
        shutil.rmtree(folder, ignore_errors=True)

    print("\n{}".format("TODO BIEN" if not failures else "FALLAN {}: {}".format(
        len(failures), "; ".join(failures))))
    return 1 if failures else 0


if __name__ == "__main__":
    # En Windows, al redirigir la salida a un fichero se usaría cp1252 en vez de UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
