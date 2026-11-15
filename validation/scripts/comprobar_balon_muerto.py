"""Comprueba possession/dead_ball.py sin datos del partido: solo el código, la GT pública y un Smart Tagging
inventado, que se escribe en una carpeta temporal y se borra al terminar.

La sección 9 prueba la regla de validation/partido/agregados_dead_ball.py con un partido inventado en
memoria: importa su `measure`, que no abre ficheros, y nunca ejecuta su `main`, que es lo que lee el
partido.

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


def smart_tagging_xml(folder, name, instances, shuffle_seed=None, teams=None):
    """Un Smart Tagging inventado con `instances` = [(código, inicio_s, fin_s, Type o None)] y, si se da,
    el `Team` de cada una (si no, `N/A`). Devuelve la ruta."""
    rows = list(zip(instances, teams or ["N/A"] * len(instances)))
    if shuffle_seed is not None:
        random.Random(shuffle_seed).shuffle(rows)
    body = []
    for i, ((code, start_s, end_s, kind), team) in enumerate(rows):
        labels = "<label><group>Team</group><text>{}</text></label>".format(team)
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


def check_team_restart(game, folder):
    """La capa del equipo que reanuda (todavía fuera de evidence) y las cuentas de su script, con datos
    inventados. Importa las funciones de validation/partido/agregados_equipo_reanuda.py, nunca su `main`, y
    llama a `measure_teams` con la apertura de ficheros prohibida."""
    sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
    import agregados_equipo_reanuda as aer  # solo sus cuentas

    fps = games.GAMES[game]["fps"]
    n = games.GAMES[game]["n_video_frames"]
    length, width = games.GAMES[game]["pitch"]
    H, A, D = tracking.H, tracking.A, tracking.D

    # La capa: equipos y evidencia.
    path = smart_tagging_xml(folder, "equipos.xml", [
        ("SET PIECES", 1000, 1035, "Corner Kick"), ("SET PIECES", 2000, 2035, "Goal Kick"),
        ("SET PIECES", 3000, 3035, "Throw-in"), ("SET PIECES", 4549.6, 4554.6, "Kick Off (Start)"),
        ("SET PIECES", 5000, 5035, "Free Kick"), ("SET PIECES", 100, 135, "Corner Kick")],
        teams=["fc local", "VISITANTE CF", "N/A", "N/A", "Otro Nombre", "FC Local"])
    events = dead_ball.smart_tagging_events(path, fps)
    check("el Smart Tagging trae el equipo, en minúsculas",
          [e["team"] for e in events] == ["fc local", "fc local", "visitante cf", "n/a", "n/a", "otro nombre"],
          str([e["team"] for e in events]))
    teams = [(w["start"], t) for w, t in dead_ball.restart_teams(events, "FC Local", "Visitante CF")]
    check("restart_teams: local en H y visitante en A; N/A, saques iniciales y otros nombres no entran",
          teams == [(100 * fps, H), (1000 * fps, H), (2000 * fps, A)], str(teams))
    check("restart_teams: sin nombres o con los dos iguales da error",
          all(pp.raises(ValueError, lambda h=h, a=a: dead_ball.restart_teams(events, h, a))
              for h, a in (("", "x"), ("x", None), ("FC Local", "fc local"))))
    bx = np.zeros(n)
    trk = tracking.Tracking(bx, bx.copy(), np.empty((n, 0)), np.empty((n, 0)), np.empty(0, dtype=np.int8),
                            (length, width), tracking.evaluated_blocks(game), fps)
    score, allowed = dead_ball.team_restart_evidence(trk, events, "FC Local", "Visitante CF")
    expected = np.zeros((n, 3))
    expected[1000 * fps:1035 * fps, A] = -dead_ball.TEAM_SCORE  # córner del local: se resta al visitante
    expected[2000 * fps:2035 * fps, H] = -dead_ball.TEAM_SCORE  # saque de puerta del visitante
    check("team_restart_evidence: resta en el otro equipo justo en la ventana; nada en D; fuera de lo "
          "evaluado, nada", bool(np.array_equal(score, expected)) and bool(allowed.all()))
    check("la puntuación del equipo es la de la regla: 1 por frame, sin ajustar", dead_ball.TEAM_SCORE == 1.0)
    check("el equipo que reanuda no entra todavía en evidence",
          not dead_ball.evidence(trk, {"smart_tagging": path}, game)[0][:, :2].any())

    # El lado que defiende cada equipo.
    blocks = tracking.evaluated_blocks(game)
    px = np.full((n, 4), np.nan)
    first_half, second_half = slice(*blocks[0]), slice(*blocks[1])
    px[first_half, :2], px[first_half, 2:] = 20.0, 80.0  # el local (slots 0 y 1) a la izquierda
    px[second_half, :2], px[second_half, 2:] = 80.0, 20.0
    team_of_slot = np.array([0, 0, 1, 1], dtype=np.int8)
    players = tracking.Tracking(bx, bx.copy(), px, px.copy(), team_of_slot, (length, width), blocks, fps)
    check("lado izquierdo: lo defiende el local en la 1ª parte y el visitante en la 2ª",
          aer.left_defender(players) == {1: H, 2: A})

    # La física de cada ventana: el balón quieto en el punto del reinicio y, después, el golpeo.
    def ball_at(x, y=1.0, start=1000 * fps):
        bx, by = np.full(n, np.nan), np.full(n, np.nan)
        bx[start - 50:start + 50], by[start - 50:start + 50] = x, y
        bx[start + 50:start + 100] = x + np.arange(1, 51)  # golpeo: se mueve 1 m por frame
        by[start + 50:start + 100] = y
        return bx, by

    corner, goal_kick = {"type": "corner kick", "start": 1000 * fps, "end": 1035 * fps}, \
        {"type": "goal kick", "start": 1000 * fps, "end": 1035 * fps}
    left = {1: H}
    check("córner en el lado izquierdo, que defiende el local: lo saca el visitante",
          aer.physics_check(*ball_at(1.0), corner, A, 1, left, length) == aer.AGREE
          and aer.physics_check(*ball_at(1.0), corner, H, 1, left, length) == aer.DISAGREE)
    check("saque de puerta en el lado izquierdo: lo saca el local, que lo defiende; en el derecho, el otro",
          aer.physics_check(*ball_at(5.0), goal_kick, H, 1, left, length) == aer.AGREE
          and aer.physics_check(*ball_at(length - 5.0), goal_kick, A, 1, left, length) == aer.AGREE)
    check("el punto cerca del medio campo no decide; justo dentro del cuarto final, sí",
          aer.physics_check(*ball_at(length / 2), corner, A, 1, left, length) == aer.NOT_IN_QUARTER
          and aer.physics_check(*ball_at(length / 4 + 0.1), corner, A, 1, left, length) == aer.NOT_IN_QUARTER
          and aer.physics_check(*ball_at(length / 4 - 0.1), corner, A, 1, left, length) == aer.AGREE)
    early_x = ball_at(1.0)[0]
    early_x[100:200] = length - 1.0  # mucho antes, el balón visto en el otro lado
    check("el punto del reinicio es el último visto antes del golpeo, no el primero",
          aer.physics_check(early_x, np.where(np.isnan(early_x), np.nan, 1.0), corner, A, 1, left, length)
          == aer.AGREE)
    check("sin balón no hay golpeo y no decide",
          aer.physics_check(np.full(n, np.nan), np.full(n, np.nan), corner, A, 1, left, length) == aer.NO_STRIKE)

    # Con qué equipo sale el pipeline de la parada.
    codes = np.array([H, D, D, H, A, A, D, D, D, D], dtype=np.int8)
    check("exit_team: el primer H o A después del último D de la ventana, buscado hasta el fin del tramo",
          aer.exit_team(codes, 0, 4, 10) == (H, 3) and aer.exit_team(codes, 4, 8, 10) == (None, None)
          and aer.exit_team(codes, 0, 1, 10) == (None, None) and aer.exit_team(codes, 1, 2, 10) == (H, 3)
          and aer.exit_team(np.array([D, H, D, A], dtype=np.int8), 0, 4, 4) == (A, 3))
    window = {"start": 0, "end": 6}
    check("exit_state: el del Team, el otro, sin parada, sin salida, y si el otro aparece después",
          aer.exit_state(codes, window, H, 10) == (aer.SAME, True)
          and aer.exit_state(codes, window, A, 10) == (aer.OTHER, False)
          and aer.exit_state(codes, {"start": 3, "end": 6}, H, 10) == (aer.NO_STOP, False)
          and aer.exit_state(codes, {"start": 6, "end": 9}, H, 10) == (aer.NO_EXIT, False))
    check("runs: posesiones y paradas dentro de los tramos",
          aer.runs(codes, ((0, 6), (6, 10))) == (3, 2), str(aer.runs(codes, ((0, 6), (6, 10)))))

    # Las dos condiciones de la regla, en sus límites.
    check("condición 1: 9 de 10 entra; 8 de 10, 8 de 9 y 9 de 9 (menos de 10 que deciden), no",
          aer.physics_rule(9, 10) and not aer.physics_rule(8, 10) and not aer.physics_rule(8, 9)
          and not aer.physics_rule(9, 9)
          and not aer.physics_rule(0, 0))
    check("condición 2: 1 sin la capa y 0 con ella entra; 0 y 0, o 2 y 2, no",
          aer.contributes_rule(1, 0) and not aer.contributes_rule(0, 0) and not aer.contributes_rule(2, 2))

    # measure_teams de punta a punta con el partido inventado de la sección 9, sin abrir ficheros.
    trk, events = synthetic_match(game)
    for event in events:
        event["team"] = {"corner kick": "local", "goal kick": "visitante"}.get(event["type"], "n/a")
    anchors = lambda clean: dead_ball.evidence(clean, None, game)  # noqa: E731
    try:
        with pp.no_files():
            m = aer.measure_teams(trk, events, "Local", "Visitante", anchors, game)
    except AssertionError:
        check("measure_teams no abre ningún fichero", False)
        raise
    check("measure_teams: corre sin abrir ficheros, sin conflictos y con la regla coherente",
          m["windows"] == 4 and m["conflicts"] == (0, 0) and m["entra"] == (m["physics_ok"] and m["contributes"])
          and sum(m["exits"][0].values()) == sum(m["exits"][1].values()) == 4,
          "ventanas {} conflictos {}".format(m["windows"], m["conflicts"]))


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

    print("\n10. El equipo que reanuda (medido, todavía fuera de evidence), con datos inventados")
    folder = tempfile.mkdtemp(prefix="comprobar_balon_muerto_")
    try:
        check_team_restart(game, folder)
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
