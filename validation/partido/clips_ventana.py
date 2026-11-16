"""Página para ver en el navegador, junto al vídeo táctico, los tramos en que una entrega y la GT pública no
coinciden.

**Lee una entrega nuestra (etiquetas del partido frame a frame) y apunta al vídeo del partido: lo ejecuta una
persona, en local, nunca Claude** (regla nº 1 de `CLAUDE.md`). La página que escribe tampoco se le enseña a
Claude: lleva las etiquetas de la entrega frame a frame.

    python validation/partido/clips_ventana.py equipo_v3

Para qué: `RULES.md` permite mirar el vídeo y los datos para entender y depurar, y `CHALLENGE.md` dice que
la GT pública está para ver cómo se etiquetan los casos. Esta página lleva directamente a los momentos de los
5 minutos públicos en que la entrega y la GT no coinciden, y enseña debajo del vídeo, en directo, qué dice
cada una. Guía del visionado: `validation/partido/GUIA_VISIONADO.md`.

**Lo que no se puede hacer con lo que se vea:** convertirlo en etiquetas, correcciones o constantes ligadas
a momentos del partido, ni ajustar nada con estos 5 minutos. Lo que se aprenda se convierte en una idea
general y se mide en los partidos abiertos (`validation/harness/`, `validation/skillcorner/`).

Qué hace:
- busca los frames evaluados en que la entrega y la GT difieren y los agrupa en tramos, con `--margen`
  segundos a cada lado (3 por defecto); dos tramos que se pisan se funden en uno;
- a cada tramo le pone una etiqueta: «borde» si la GT y la entrega tienen las mismas posesiones y paradas
  y solo se mueve algún borde, y «equipo» o «D» según dónde difieren;
- escribe una página HTML, fuera del repo, con el vídeo, la lista de tramos, las dos etiquetas del frame
  que se ve y una tira de colores por tramo. Se abre con doble clic; no necesita internet ni instalar nada;
- si encuentra el ATD, sus metadatos y la homografía (en `MTAH_DATA_DIR`), dibuja el ATD encima del vídeo,
  proyectado con la homografía de cada frame: los jugadores con el color de su equipo, el balón con su
  estela y las líneas del campo, que tienen que caer sobre las pintadas. También lo enseña visto desde
  arriba, en un minimapa. Lleva solo los frames de la ventana y 10 s de margen. `--sin-atd` lo quita.

El vídeo sale de `games.video_path()` (la ruta de `MTAH_DATA_DIR`) o de `--video`. Si el navegador no lo
abre, la página deja elegirlo a mano.

- Por pantalla solo imprime cuántos tramos hay, si lleva el ATD (cuántos frames) y dónde ha escrito. Ni
  etiquetas ni tiempos.
- No escribe en el repo: la página va a `~/mtah2027-salidas/` (o donde diga `--salida`).
- Si falla, imprime solo el tipo de error y la línea del código.
"""

import argparse
import json
import os
import pathlib
import sys
import traceback

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import games  # noqa: E402
import possession_metrics as pm  # noqa: E402

FPS = 25
GT_PUBLICA = os.path.join(ROOT, "evaluation", "gt", "BAR-ATH_possession_gt_public.csv")
RESULTADOS = os.path.join(ROOT, "evaluation", "results")
SALIDAS = os.path.join(os.path.expanduser("~"), "mtah2027-salidas")
MARGEN_S = 3.0
H, A, D, X = (pm.LABELS.index(c) for c in "HADX")
NOMBRES = pm.LABELS


def codigos(ruta):
    return pm.label_codes(pm.read_label_csv(ruta))


# -- tramos --------------------------------------------------------------------------------------

def diferencias(gt, pred, runs):
    """[(a, b)] semiabiertos, en orden: frames evaluados seguidos en que la GT y la entrega difieren."""
    out = []
    for inicio, fin in runs:
        dif = (gt[inicio:fin] != pred[inicio:fin]).astype(np.int8)
        bordes = np.diff(np.concatenate(([0], dif, [0])))
        out += [(inicio + int(a), inicio + int(b))
                for a, b in zip(np.flatnonzero(bordes == 1), np.flatnonzero(bordes == -1))]
    return out


def agrupar(difs, margen, n):
    """Tramos [a, b) con `margen` frames a cada lado de cada diferencia, dentro de [0, n), fundidos si se
    pisan o se tocan. Cada tramo guarda sus diferencias."""
    tramos = []
    for a, b in difs:
        ini, fin = max(0, a - margen), min(n, b + margen)
        if tramos and ini <= tramos[-1]["b"]:
            tramos[-1]["b"] = max(tramos[-1]["b"], fin)
            tramos[-1]["dif"].append([a, b])
        else:
            tramos.append({"a": ini, "b": fin, "dif": [[a, b]]})
    return tramos


def segundos(frames):
    return "{:.2f} s".format(frames / FPS).replace(".", ",")


def nombre_cambio(de, a):
    par = "{}→{}".format(NOMBRES[de], NOMBRES[a])
    if {de, a} == {H, A}:
        return "cambio de equipo " + par
    if a == D and de in (H, A):
        return "empieza la parada " + par
    if de == D and a in (H, A):
        return "se reanuda " + par
    return par


def secuencia(segs, a, b):
    """«…H → A 1,20 s → H…»: las rachas del tramo; las de dentro, con su duración."""
    partes = []
    for ini, fin, codigo in segs:
        texto = NOMBRES[codigo]
        if ini > a and fin < b:
            texto += " " + segundos(fin - ini)
        if ini <= a:
            texto = "…" + texto
        if fin >= b:
            texto += "…"
        partes.append(texto)
    return " → ".join(partes)


def describir(gt, pred, tramo, runs):
    """Añade al tramo `tipos`, `borde`, `gt_txt`, `pred_txt` y `nota` (solo para la página)."""
    a, b = tramo["a"], tramo["b"]
    tipos = set()
    for x, y in tramo["dif"]:
        g, p = gt[x:y], pred[x:y]
        if ((g == D) | (p == D)).any():
            tipos.add("D")
        if (np.isin(g, (H, A)) & np.isin(p, (H, A))).any():
            tipos.add("equipo")
        if (p == X).any():
            tipos.add("X")
    trozos = [(max(a, s), min(b, e)) for s, e in runs if max(a, s) < min(b, e)]
    borde, gt_txt, pred_txt, notas = True, [], [], []
    for s, e in trozos:
        sg, sp = pm.segments(gt, [(s, e)]), pm.segments(pred, [(s, e)])
        gt_txt.append(secuencia(sg, s, e))
        pred_txt.append(secuencia(sp, s, e))
        # «Borde» solo si las rachas son las mismas y cada una pisa a la suya: una posesión corta que
        # ponemos 2 s más allá, sin pisarse con la real, no es un borde movido.
        if [c for _, _, c in sg] != [c for _, _, c in sp] or any(
                max(g[0], p[0]) >= min(g[1], p[1]) for g, p in zip(sg, sp)):
            borde = False
            continue
        for i in range(1, len(sg)):
            delta = sp[i][0] - sg[i][0]
            if delta:
                notas.append("{}: nosotros {} {} ({} frames)".format(
                    nombre_cambio(sg[i - 1][2], sg[i][2]), segundos(abs(delta)),
                    "tarde" if delta > 0 else "pronto", abs(delta)))
    tramo["tipos"] = sorted(tipos)
    tramo["borde"] = borde
    tramo["gt_txt"] = " | ".join(gt_txt)
    tramo["pred_txt"] = " | ".join(pred_txt)
    tramo["nota"] = "; ".join(notas) if borde else "las posesiones o las paradas no son las mismas"
    return tramo


def tramos(gt, pred, margen_s=MARGEN_S):
    runs = pm.valid_runs(gt)
    margen = int(round(margen_s * FPS))
    return [describir(gt, pred, t, runs) for t in agrupar(diferencias(gt, pred, runs), margen, len(gt))]


# -- página --------------------------------------------------------------------------------------

# -- el ATD, para dibujarlo encima del vídeo -------------------------------------------------------

ATD_MARGEN_S = 10          # segundos de ATD antes y después de lo que enseña la página
ATD_MAX_FRAMES = 30000     # con más, la página pesaría demasiado: se dibuja sin ATD
ESCALA = 10000             # coordenadas 0–1 del campo guardadas como enteros (1/10.000 ≈ 1 cm)
COLUMNAS_H = ["h{}{}".format(fila, col) for fila in range(3) for col in range(3)]  # como starter/load_homography


def rango_atd(gt, lista, margen=ATD_MARGEN_S * FPS):
    """[f0, f1): los frames de los que la página lleva el ATD (los tramos evaluados y los de la lista, con margen)."""
    runs = pm.valid_runs(gt)
    inicio = min([runs[0][0]] + [t["a"] for t in lista]) - margen
    fin = max([runs[-1][1]] + [t["b"] for t in lista]) + margen
    return max(0, inicio), min(len(gt), fin)


def entero(valor):
    return int(round(float(valor) * ESCALA)) if np.isfinite(valor) else None


def datos_atd(paths, f0, f1, game=games.GAME):
    """El balón, los jugadores y la homografía de [f0, f1), en coordenadas 0–1 del campo (las del ATD).

    Lee el ATD con el lector del pipeline (`tracking.from_atd`, que da metros y el equipo de cada slot) y la
    homografía con las columnas de `starter/load_homography.py`, buscando cada fila por su `frame`.
    """
    import pandas as pd
    from possession import tracking

    trk = tracking.from_atd(paths, game)
    largo, ancho = trk.pitch
    balon, jugadores = [], []
    for f in range(f0, f1):
        balon.append(None if not (np.isfinite(trk.bx[f]) and np.isfinite(trk.by[f]))
                     else [entero(trk.bx[f] / largo), entero(trk.by[f] / ancho)])
        fila = []
        for slot in np.flatnonzero(np.isfinite(trk.px[f]) & np.isfinite(trk.py[f])).tolist():
            fila += [slot, entero(trk.px[f, slot] / largo), entero(trk.py[f, slot] / ancho)]
        jugadores.append(fila)
    tabla = pd.read_csv(paths["homography"])
    tabla = tabla[(tabla["frame"] >= f0) & (tabla["frame"] < f1)]
    matrices = [None] * (f1 - f0)
    for frame, valido, valores in zip(tabla["frame"].tolist(), tabla["valid"].tolist(),
                                      tabla[COLUMNAS_H].values.tolist()):
        if valido and all(np.isfinite(valores)):
            matrices[int(frame) - f0] = [float("{:.7g}".format(v)) for v in valores]
    return {"f0": f0, "n": f1 - f0, "escala": ESCALA, "campo": [largo, ancho],
            "equipo": [int(t) for t in trk.team], "balon": balon, "jug": jugadores, "hom": matrices}


def rle(codes):
    """[[primer frame, código], …] de cada racha, para buscar la etiqueta de un frame en la página."""
    inicios = np.concatenate(([0], np.flatnonzero(codes[1:] != codes[:-1]) + 1))
    return [[int(i), int(codes[i])] for i in inicios]


def pagina(gt, pred, lista, nombre, video_uri, atd=None):
    datos = {
        "atd": atd,
        "fps": FPS,
        "n": int(len(gt)),
        "nombre": nombre,
        "video": video_uri,
        "saque": games.anchor_video_frame(games.GAMES[games.GAME]["kickoff"]),
        "runs": [[int(s), int(e)] for s, e in pm.valid_runs(gt)],
        "gt": rle(gt),
        "pred": rle(pred),
        "tramos": lista,
    }
    texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return PLANTILLA.replace("__NOMBRE__", nombre).replace("__DATOS__", texto)


def leer_atd(gt, lista):
    """(datos del ATD para la página, o None; qué imprimir). Si no se puede, la página va sin ATD.

    El aviso lleva solo recuentos, o el tipo de error y la línea del código, nunca valores de datos.
    """
    paths = games.asset_paths()
    faltan = [nombre for nombre in ("atd_raw", "atd_meta", "homography") if not os.path.isfile(paths[nombre])]
    if faltan:
        return None, "no (no encuentro {} en MTAH_DATA_DIR)".format(", ".join(faltan))
    f0, f1 = rango_atd(gt, lista)
    if f1 - f0 > ATD_MAX_FRAMES:
        return None, "no ({} frames: más de {}, la página pesaría demasiado)".format(f1 - f0, ATD_MAX_FRAMES)
    try:
        return datos_atd(paths, f0, f1), "sí, {} frames alrededor de la ventana".format(f1 - f0)
    except Exception as error:  # sin el mensaje: podría llevar valores de datos
        ultimo = traceback.extract_tb(sys.exc_info()[2])[-1]
        return None, "no ({} en {}:{})".format(type(error).__name__, os.path.basename(ultimo.filename), ultimo.lineno)


def main():
    parser = argparse.ArgumentParser(description="Página con los tramos en que la entrega y la GT pública "
                                                 "difieren, para verlos junto al vídeo en el navegador.")
    parser.add_argument("entrega", help="nombre de la entrega en evaluation/results (sin .csv) o ruta a un CSV")
    parser.add_argument("--gt", default=GT_PUBLICA, help="CSV de la GT (por defecto, la pública)")
    parser.add_argument("--video", default=None, help="vídeo táctico (por defecto, el de MTAH_DATA_DIR)")
    parser.add_argument("--margen", type=float, default=MARGEN_S, help="segundos a cada lado de cada tramo")
    parser.add_argument("--salida", default=None, help="ruta de la página (por defecto, en ~/mtah2027-salidas)")
    parser.add_argument("--sin-atd", action="store_true", help="no dibujar el ATD encima del vídeo")
    args = parser.parse_args()

    ruta = args.entrega if os.path.isfile(args.entrega) else os.path.join(RESULTADOS, args.entrega + ".csv")
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    salida = args.salida or os.path.join(SALIDAS, "ventana_tramos_{}.html".format(nombre))
    if os.path.abspath(salida).lower().startswith(os.path.abspath(ROOT).lower() + os.sep):
        sys.exit("La página no se escribe dentro del repo: elige otra ruta con --salida.")
    video = args.video or games.video_path()
    hay_video = os.path.isfile(video)
    try:
        gt, pred = codigos(args.gt), codigos(ruta)
        if len(gt) != len(pred):
            raise ValueError("la GT y la entrega no tienen el mismo número de filas")
        lista = tramos(gt, pred, args.margen)
        atd, aviso_atd = None, "no (--sin-atd)"
        if not args.sin_atd:
            atd, aviso_atd = leer_atd(gt, lista)
        html = pagina(gt, pred, lista, nombre, pathlib.Path(os.path.abspath(video)).as_uri() if hay_video else "",
                      atd)
        carpeta = os.path.dirname(os.path.abspath(salida))
        if not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        with open(salida, "w", encoding="utf-8") as fichero:
            fichero.write(html)
    except Exception as error:  # sin el mensaje: podría llevar valores de datos
        ultimo = traceback.extract_tb(sys.exc_info()[2])[-1]
        sys.exit("ERROR: {} en {}:{}".format(type(error).__name__, os.path.basename(ultimo.filename), ultimo.lineno))
    de_borde = sum(t["borde"] for t in lista)
    print("tramos: {} ({} solo de borde, {} con posesiones o paradas distintas)".format(
        len(lista), de_borde, len(lista) - de_borde))
    print("ATD encima del vídeo: {}".format(aviso_atd))
    if not hay_video:
        print("aviso: no encuentro el vídeo táctico (MTAH_DATA_DIR o --video); la página te dejará elegirlo")
    print("página escrita en {}".format(salida))
    print("ábrela con doble clic, o arrastrándola a la ventana del navegador")


PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ventana pública · __NOMBRE__</title>
<style>
  :root { --fondo:#15171a; --panel:#1f2226; --borde:#33373d; --texto:#e8e8e8; --suave:#a0a4aa;
          --h:#2b7bba; --a:#f28e2b; --d:#9a9a9a; --x:#ffffff; --rojo:#d62728; --acento:#4fa3e0; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--fondo); color:var(--texto); font:14px/1.4 system-ui, sans-serif; }
  header { padding:8px 16px; border-bottom:1px solid var(--borde); display:flex; gap:16px; align-items:center; flex-wrap:wrap; }
  header h1 { font-size:16px; margin:0; }
  header .resumen { color:var(--suave); }
  main { display:grid; grid-template-columns:minmax(0, 1fr) 380px; gap:12px; padding:12px 16px; }
  @media (max-width: 1000px) { main { grid-template-columns:1fr; } }
  video { width:100%; background:#000; display:block; max-height:72vh; }
  .vivo { display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin:8px 0; font-size:16px; }
  .reloj { font-variant-numeric:tabular-nums; font-family:ui-monospace, monospace; }
  .eti { display:inline-block; min-width:34px; text-align:center; padding:2px 8px; border-radius:4px; font-weight:700; color:#111; }
  .difiere { outline:3px solid var(--rojo); outline-offset:2px; }
  .botones { display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin:6px 0; }
  button { background:var(--panel); color:var(--texto); border:1px solid var(--borde); border-radius:4px; padding:4px 10px; cursor:pointer; font:inherit; }
  button:hover { border-color:var(--acento); }
  button.activo { background:var(--acento); color:#111; border-color:var(--acento); }
  canvas { width:100%; display:block; cursor:pointer; }
  .tira { display:grid; grid-template-columns:70px minmax(0,1fr); gap:6px; align-items:center; margin-top:6px; }
  .tira .rot { color:var(--suave); font-size:12px; line-height:18px; text-align:right; }
  .nota { color:var(--suave); margin:6px 0; min-height:2.8em; }
  aside { background:var(--panel); border:1px solid var(--borde); border-radius:6px; padding:8px; max-height:calc(100vh - 80px); overflow:auto; }
  aside h2 { font-size:14px; margin:4px 4px 8px; }
  ol { list-style:none; margin:0; padding:0; }
  li { padding:6px 8px; border-radius:4px; cursor:pointer; border:1px solid transparent; }
  li:hover { border-color:var(--borde); }
  li.actual { border-color:var(--acento); background:#263241; }
  li .cab { display:flex; gap:6px; align-items:center; }
  li .num { font-weight:700; min-width:28px; }
  li .txt { color:var(--suave); font-size:12px; margin-top:2px; }
  .chip { font-size:11px; padding:0 6px; border-radius:8px; border:1px solid var(--borde); }
  .chip.borde { color:var(--suave); }
  .chip.equipo { border-color:var(--a); color:var(--a); }
  .chip.D { border-color:var(--d); color:#ddd; }
  .chip.X { border-color:var(--x); }
  .elegir { display:none; background:#3a2a10; border:1px solid var(--a); padding:8px; border-radius:4px; margin-bottom:8px; }
  .aviso { color:var(--a); }
  .teclas { color:var(--suave); font-size:12px; margin-top:10px; }
  .marco { position:relative; }
  #capa { position:absolute; left:0; top:0; width:100%; height:100%; pointer-events:none; }
  #mapa { width:100%; display:block; border-radius:4px; margin-bottom:6px; }
  .mapaPie { color:var(--suave); font-size:12px; margin:0 4px 10px; min-height:1.4em; }
  body:not(.con-atd) .atd { display:none; }
  kbd { border:1px solid var(--borde); border-radius:3px; padding:0 4px; font-family:inherit; }
</style>
</head>
<body>
<header>
  <h1>Ventana pública · __NOMBRE__</h1>
  <span class="resumen" id="resumen"></span>
  <span class="aviso" id="aviso"></span>
</header>
<main>
  <section>
    <div class="elegir" id="elegir">
      El navegador no ha podido abrir el vídeo solo. Elige el vídeo táctico (<code>BAR-ATH_tactical.mp4</code>):
      <input type="file" id="fichero" accept="video/*">
    </div>
    <div class="marco"><video id="v" preload="auto" controls playsinline></video><canvas id="capa"></canvas></div>
    <div class="vivo">
      <span class="reloj" id="reloj">–</span>
      <span>GT <span class="eti" id="etiGT">–</span></span>
      <span>nuestra <span class="eti" id="etiPred">–</span></span>
      <span id="tramoActual" class="reloj"></span>
      <span id="atdInfo" class="atd" style="color:var(--suave); font-size:14px"></span>
    </div>
    <div class="botones">
      <button id="bAnt" title="tramo anterior (P)">◀ tramo</button>
      <button id="bRep" title="repetir el tramo (R)">↺ repetir</button>
      <button id="bSig" title="tramo siguiente (N)">tramo ▶</button>
      <button id="bPlay" title="reproducir o parar (espacio)">▶ / ❚❚</button>
      <button id="bBucle" title="repetir el tramo sin parar (L)">bucle</button>
      <span style="margin-left:8px">velocidad</span>
      <button data-vel="0.25">¼</button><button data-vel="0.5">½</button><button data-vel="1">1</button>
      <label style="margin-left:8px"><input type="checkbox" id="ocultarBorde"> esconder los de solo borde</label>
      <button id="bTodo" title="la ventana entera, sin parar en los tramos">ventana entera</button>
      <button id="bSaque" title="comprobar la alineación: el saque inicial">saque inicial</button>
    </div>
    <div class="botones atd">
      <span>ATD:</span>
      <label><input type="checkbox" id="cATD" checked> encima del vídeo (T)</label>
      <label><input type="checkbox" id="cLineas" checked> líneas del campo (C)</label>
      <label><input type="checkbox" id="cSlots"> número de slot (S)</label>
    </div>
    <div class="nota" id="nota"></div>
    <div class="tira"><div class="rot">GT<br>nuestra<br>difieren</div><canvas id="cTramo" height="54"></canvas></div>
    <div class="tira"><div class="rot">ventana</div><canvas id="cVentana" height="40"></canvas></div>
    <div class="teclas">
      <kbd>espacio</kbd> reproducir/parar · <kbd>←</kbd><kbd>→</kbd> un frame · <kbd>Mayús</kbd>+<kbd>←</kbd><kbd>→</kbd> un segundo ·
      <kbd>N</kbd>/<kbd>P</kbd> tramo siguiente/anterior · <kbd>R</kbd> repetir · <kbd>L</kbd> bucle · <kbd>1</kbd><kbd>2</kbd><kbd>3</kbd> velocidad ¼, ½, 1.
      Clic en una tira para saltar a ese momento. Colores: azul H, naranja A, gris D, blanco X; rojo, donde difieren.
      ATD: jugadores con el color de su equipo, balón en amarillo con su estela; si el ATD no lo ve, círculo
      discontinuo donde se vio por última vez. Para pantalla completa, usa la del navegador (F11): la del
      reproductor no enseña la capa.
    </div>
  </section>
  <aside>
    <div class="atd"><h2>ATD visto desde arriba</h2><canvas id="mapa"></canvas><div class="mapaPie" id="mapaPie"></div></div>
    <h2>Tramos en que la entrega y la GT difieren</h2>
    <ol id="lista"></ol>
  </aside>
</main>
<script>
"use strict";
const DATOS = __DATOS__;
const FPS = DATOS.fps, N = DATOS.n;
const NOMBRES = ["H", "A", "D", "X"];
const COLOR = ["#2b7bba", "#f28e2b", "#9a9a9a", "#ffffff"];
const ROJO = "#d62728";
const v = document.getElementById("v");
const $ = (id) => document.getElementById(id);

let actual = 0;          // frame que se ve
let anterior = 0;        // frame visto antes (para parar al final de un tramo)
let idx = -1;            // tramo activo (-1: ninguno)
let bucle = false;
let velocidad = 0.5;
let ocultarBorde = false;

function etiqueta(rle, f) {            // código de la racha que contiene f
  let lo = 0, hi = rle.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (rle[m][0] <= f) lo = m; else hi = m - 1; }
  return rle[lo][1];
}
function dos(x) { return String(x).padStart(2, "0"); }
function reloj(f) { const s = Math.floor(f / FPS); return Math.floor(s / 60) + ":" + dos(s % 60) + ":" + dos(f % FPS); }
function limitar(f) { return Math.max(0, Math.min(N - 1, f)); }
function visibles() { return DATOS.tramos.map((t, i) => i).filter((i) => !(ocultarBorde && DATOS.tramos[i].borde)); }

function ir(f) {                       // muestra el frame f (en la mitad de su intervalo de tiempo)
  actual = anterior = limitar(f);
  if (v.readyState > 0) v.currentTime = (actual + 0.5) / FPS;
  pintar();
}
function verTramo(i, reproducir = true) {
  if (i < 0 || i >= DATOS.tramos.length) return;
  idx = i;
  ir(DATOS.tramos[i].a);
  marcarLista();
  if (reproducir) { v.playbackRate = velocidad; v.play().catch(() => {}); }
}
function saltar(paso) {              // tramo siguiente (paso 1) o anterior (-1) entre los visibles
  const vis = visibles();
  if (!vis.length) return;
  let k = vis.indexOf(idx);
  if (k >= 0) k = Math.max(0, Math.min(vis.length - 1, k + paso));
  else if (paso > 0) { k = vis.findIndex((i) => DATOS.tramos[i].b > actual); if (k < 0) k = vis.length - 1; }
  else { k = 0; vis.forEach((i, j) => { if (DATOS.tramos[i].a < actual) k = j; }); }
  verTramo(vis[k]);
}

// -- frame que se ve, desde el vídeo --
function desdeTiempo() { return limitar(Math.floor(v.currentTime * FPS + 1e-6)); }
function alAvanzar(f) {
  anterior = actual; actual = f;
  const t = DATOS.tramos[idx];
  if (t && !v.paused && anterior < t.b && actual >= t.b) {
    if (bucle) ir(t.a); else v.pause();
  }
  pintar();
}
if ("requestVideoFrameCallback" in HTMLVideoElement.prototype) {
  const cada = (ahora, md) => {
    const porMedia = Math.round(md.mediaTime * FPS);
    alAvanzar(Math.abs(md.mediaTime - v.currentTime) < 0.5 ? limitar(porMedia) : desdeTiempo());
    v.requestVideoFrameCallback(cada);
  };
  v.requestVideoFrameCallback(cada);
} else {
  const bucleRaf = () => { if (!v.paused) alAvanzar(desdeTiempo()); requestAnimationFrame(bucleRaf); };
  requestAnimationFrame(bucleRaf);
}
v.addEventListener("seeked", () => { actual = desdeTiempo(); pintar(); });

// -- vídeo: abrirlo, o pedirlo a mano --
function pedirVideo(motivo) { $("elegir").style.display = "block"; if (motivo) $("aviso").textContent = motivo; }
v.addEventListener("error", () => pedirVideo("no se ha podido abrir el vídeo"));
v.addEventListener("loadedmetadata", () => {
  $("elegir").style.display = "none";
  const esperado = N / FPS;
  $("aviso").textContent = Math.abs(v.duration - esperado) > 1
    ? "ojo: el vídeo dura " + v.duration.toFixed(1) + " s y el táctico debería durar " + esperado.toFixed(1) + " s" : "";
  ir(actual);
});
$("fichero").addEventListener("change", (e) => {
  const f = e.target.files[0];
  if (f) { v.src = URL.createObjectURL(f); }
});
if (DATOS.video) v.src = DATOS.video; else pedirVideo("");

// -- ATD encima del vídeo y visto desde arriba --
const ATD = DATOS.atd;
const ESC = ATD ? ATD.escala : 1;
let verATD = true, verLineas = true, verSlots = false, orientacion = { invX: false, invY: false };
function atdIndice(f) { if (!ATD) return null; const i = f - ATD.f0; return i >= 0 && i < ATD.n ? i : null; }
function proyectar(h, x, y) {           // coordenadas 0–1 del campo -> píxeles del vídeo (starter/load_homography.py)
  const w = h[6] * x + h[7] * y + h[8];
  if (!(w > 1e-9)) return null;
  return [(h[0] * x + h[1] * y + h[2]) / w, (h[3] * x + h[4] * y + h[5]) / w];
}
function balonDe(i) { const b = ATD.balon[i]; return b ? [b[0] / ESC, b[1] / ESC] : null; }
function jugadoresDe(i) {
  const fila = ATD.jug[i], out = [];
  for (let k = 0; k < fila.length; k += 3) out.push([fila[k], fila[k + 1] / ESC, fila[k + 2] / ESC]);
  return out;
}
function ultimoBalon(i, max) {          // [posición, hace cuántos frames] del último balón visto
  for (let k = 1; k <= max && i - k >= 0; k++) { const b = balonDe(i - k); if (b) return [b, k]; }
  return null;
}
function lineasCampo() {                // las líneas del campo, como polilíneas en coordenadas 0–1
  if (!ATD) return [];
  const L = ATD.campo[0], W = ATD.campo[1], out = [];
  const seg = (x0, y0, x1, y1) => { const p = []; for (let k = 0; k <= 30; k++) p.push([x0 + (x1 - x0) * k / 30, y0 + (y1 - y0) * k / 30]); return p; };
  const caja = (x0, x1, mitad) => { const y0 = 0.5 - mitad / W, y1 = 0.5 + mitad / W; return [seg(x0, y0, x1, y0), seg(x1, y0, x1, y1), seg(x1, y1, x0, y1)]; };
  out.push(seg(0, 0, 1, 0), seg(1, 0, 1, 1), seg(1, 1, 0, 1), seg(0, 1, 0, 0), seg(0.5, 0, 0.5, 1));
  const c = []; for (let k = 0; k <= 64; k++) { const t = 2 * Math.PI * k / 64; c.push([0.5 + 9.15 / L * Math.cos(t), 0.5 + 9.15 / W * Math.sin(t)]); }
  out.push(c);
  out.push(...caja(0, 16.5 / L, 20.16), ...caja(1, 1 - 16.5 / L, 20.16), ...caja(0, 5.5 / L, 9.16), ...caja(1, 1 - 5.5 / L, 9.16));
  return out;
}
const LINEAS = lineasCampo();
if (ATD) {                              // el minimapa, orientado como lo ve la cámara
  for (const h of ATD.hom) {
    if (!h) continue;
    const a = proyectar(h, 0.5, 0), b = proyectar(h, 0.5, 1), c = proyectar(h, 0, 0.5), d = proyectar(h, 1, 0.5);
    if (a && b && c && d) { orientacion = { invY: a[1] > b[1], invX: c[0] > d[0] }; break; }
  }
  document.body.classList.add("con-atd");
}
function rectVideo() {                  // dónde pinta el navegador la imagen dentro del <video>
  const ew = v.clientWidth, eh = v.clientHeight, vw = v.videoWidth, vh = v.videoHeight;
  if (!vw || !vh || !ew || !eh) return null;
  const s = Math.min(ew / vw, eh / vh);
  return { s: s, x: (ew - vw * s) / 2, y: (eh - vh * s) / 2 };
}
function pintarCapa() {
  const capa = $("capa"), dpr = window.devicePixelRatio || 1;
  const w = Math.round(v.clientWidth * dpr), h = Math.round(v.clientHeight * dpr);
  if (capa.width !== w || capa.height !== h) { capa.width = w; capa.height = h; }
  const g = capa.getContext("2d");
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.clearRect(0, 0, capa.width, capa.height);
  const i = atdIndice(actual), r = rectVideo();
  if (!ATD || !verATD || i === null || !r || !ATD.hom[i]) return;
  const H = ATD.hom[i], px = 1 / r.s;  // px: un píxel de pantalla, en píxeles del vídeo
  g.setTransform(dpr * r.s, 0, 0, dpr * r.s, dpr * r.x, dpr * r.y);
  const poli = (pts) => {
    g.beginPath(); let sigue = false;
    for (const [x, y] of pts) {
      const p = proyectar(H, x, y);
      if (!p) { sigue = false; continue; }
      if (sigue) g.lineTo(p[0], p[1]); else g.moveTo(p[0], p[1]);
      sigue = true;
    }
    g.stroke();
  };
  if (verLineas) { g.strokeStyle = "rgba(255,255,0,0.55)"; g.lineWidth = 1.5 * px; LINEAS.forEach(poli); }
  g.font = (12 * px) + "px sans-serif";
  for (const [slot, x, y] of jugadoresDe(i)) {
    const p = proyectar(H, x, y);
    if (!p) continue;
    g.beginPath(); g.arc(p[0], p[1], 7 * px, 0, 2 * Math.PI);
    g.fillStyle = COLOR[ATD.equipo[slot]]; g.fill();
    g.lineWidth = 1.5 * px; g.strokeStyle = "#fff"; g.stroke();
    if (verSlots) { g.fillStyle = "#fff"; g.fillText(String(slot + 1), p[0] + 9 * px, p[1] - 9 * px); }
  }
  g.lineWidth = 2 * px;                 // estela: los 12 frames anteriores del balón
  for (let k = 12; k >= 1; k--) {
    if (i - k < 0) continue;
    const a = balonDe(i - k), b = balonDe(i - k + 1);
    if (!a || !b) continue;
    const pa = proyectar(H, a[0], a[1]), pb = proyectar(H, b[0], b[1]);
    if (!pa || !pb) continue;
    g.strokeStyle = "rgba(255,235,59," + (1 - k / 13).toFixed(2) + ")";
    g.beginPath(); g.moveTo(pa[0], pa[1]); g.lineTo(pb[0], pb[1]); g.stroke();
  }
  const b = balonDe(i);
  if (b) {
    const p = proyectar(H, b[0], b[1]);
    if (p) { g.beginPath(); g.arc(p[0], p[1], 6 * px, 0, 2 * Math.PI); g.fillStyle = "#ffeb3b"; g.fill(); g.strokeStyle = "#000"; g.stroke(); }
  } else {
    const u = ultimoBalon(i, 250), p = u && proyectar(H, u[0][0], u[0][1]);
    if (p) {
      g.setLineDash([4 * px, 3 * px]); g.strokeStyle = "rgba(255,235,59,0.85)";
      g.beginPath(); g.arc(p[0], p[1], 9 * px, 0, 2 * Math.PI); g.stroke(); g.setLineDash([]);
    }
  }
}
function pintarMapa() {
  if (!ATD) return;
  const mapa = $("mapa"), dpr = window.devicePixelRatio || 1;
  const ancho = mapa.clientWidth || 340, m = 8;
  const alto = Math.round((ancho - 2 * m) * ATD.campo[1] / ATD.campo[0]) + 2 * m;
  if (mapa.width !== Math.round(ancho * dpr) || mapa.height !== Math.round(alto * dpr)) {
    mapa.width = Math.round(ancho * dpr); mapa.height = Math.round(alto * dpr); mapa.style.height = alto + "px";
  }
  const g = mapa.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  const X = (x) => m + (orientacion.invX ? 1 - x : x) * (ancho - 2 * m);
  const Y = (y) => m + (orientacion.invY ? 1 - y : y) * (alto - 2 * m);
  g.fillStyle = "#1d4d2b"; g.fillRect(0, 0, ancho, alto);
  g.strokeStyle = "rgba(255,255,255,0.55)"; g.lineWidth = 1;
  LINEAS.forEach((pts) => { g.beginPath(); pts.forEach(([x, y], k) => (k ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)))); g.stroke(); });
  const i = atdIndice(actual);
  if (i === null) { $("mapaPie").textContent = "fuera del tramo con ATD"; return; }
  for (const [slot, x, y] of jugadoresDe(i)) {
    g.beginPath(); g.arc(X(x), Y(y), 4.5, 0, 2 * Math.PI);
    g.fillStyle = COLOR[ATD.equipo[slot]]; g.fill(); g.strokeStyle = "#fff"; g.lineWidth = 1; g.stroke();
    if (verSlots) { g.fillStyle = "#fff"; g.font = "10px sans-serif"; g.fillText(String(slot + 1), X(x) + 5, Y(y) - 5); }
  }
  const b = balonDe(i);
  let pie = "";
  if (b) {
    g.beginPath(); g.arc(X(b[0]), Y(b[1]), 4, 0, 2 * Math.PI); g.fillStyle = "#ffeb3b"; g.fill(); g.strokeStyle = "#000"; g.stroke();
  } else {
    const u = ultimoBalon(i, 250);
    if (u) {
      g.setLineDash([3, 2]); g.strokeStyle = "#ffeb3b";
      g.beginPath(); g.arc(X(u[0][0]), Y(u[0][1]), 6, 0, 2 * Math.PI); g.stroke(); g.setLineDash([]);
      pie = "sin balón: visto por última vez hace " + (u[1] / FPS).toFixed(1).replace(".", ",") + " s";
    } else pie = "sin balón en los últimos 10 s";
  }
  $("mapaPie").textContent = pie;
}
function infoATD() {
  if (!ATD) return "";
  const i = atdIndice(actual);
  if (i === null) return "ATD: fuera del tramo cargado";
  const b = balonDe(i), cuenta = [0, 0];
  jugadoresDe(i).forEach(([slot]) => cuenta[ATD.equipo[slot]]++);
  let texto = "ATD: " + (b ? "balón visto" : "sin balón");
  if (b && (b[0] < 0 || b[0] > 1 || b[1] < 0 || b[1] > 1)) texto += " · fuera del campo";
  return texto + " · jugadores " + cuenta[0] + " H, " + cuenta[1] + " A";
}

// -- pintar --
function pintarTira(canvas, a, b, filas, marcas) {
  const ancho = canvas.clientWidth || 600;
  if (canvas.width !== ancho) canvas.width = ancho;
  const g = canvas.getContext("2d"), alto = canvas.height, h = alto / filas.length;
  g.fillStyle = "#000"; g.fillRect(0, 0, ancho, alto);
  const x = (f) => (f - a) / (b - a) * ancho;
  filas.forEach((fila, r) => {
    for (let px = 0; px < ancho; px++) {
      const f = Math.floor(a + (px + 0.5) / ancho * (b - a));
      g.fillStyle = fila(f); g.fillRect(px, r * h, 1, h - 1);
    }
  });
  if (marcas) marcas(g, x, alto);
  if (actual >= a && actual < b) { g.fillStyle = "#fff"; g.fillRect(Math.floor(x(actual)) - 1, 0, 2, alto); }
}
const filaGT = (f) => COLOR[etiqueta(DATOS.gt, f)];
const filaPred = (f) => COLOR[etiqueta(DATOS.pred, f)];
const filaDif = (f) => (enVentana(f) && etiqueta(DATOS.gt, f) !== etiqueta(DATOS.pred, f)) ? ROJO : "#000";
function enVentana(f) { return DATOS.runs.some(([s, e]) => f >= s && f < e); }

function pintar() {
  const g = etiqueta(DATOS.gt, actual), p = etiqueta(DATOS.pred, actual);
  $("reloj").textContent = "frame " + actual + " · " + reloj(actual);
  $("etiGT").textContent = enVentana(actual) ? NOMBRES[g] : "fuera";
  $("etiGT").style.background = enVentana(actual) ? COLOR[g] : "#555";
  $("etiPred").textContent = NOMBRES[p];
  $("etiPred").style.background = COLOR[p];
  $("etiPred").classList.toggle("difiere", enVentana(actual) && g !== p);
  const t = DATOS.tramos[idx];
  if (t) {
    $("tramoActual").textContent = "tramo " + (idx + 1) + " de " + DATOS.tramos.length;
    $("nota").innerHTML = "<b>GT:</b> " + t.gt_txt + "<br><b>nuestra:</b> " + t.pred_txt + "<br>" + t.nota;
    pintarTira($("cTramo"), t.a, t.b, [filaGT, filaPred, filaDif], (gx, x, alto) => {
      gx.fillStyle = "rgba(255,255,255,0.25)";
      for (let f = Math.ceil(t.a / FPS) * FPS; f < t.b; f += FPS) gx.fillRect(Math.floor(x(f)), 0, 1, alto);
    });
  } else {
    $("tramoActual").textContent = "";
    $("nota").textContent = "Elige un tramo de la lista, o pulsa «tramo ▶».";
    const c = $("cTramo"); c.getContext("2d").clearRect(0, 0, c.width, c.height);
  }
  const s = DATOS.runs[0][0], e = DATOS.runs[DATOS.runs.length - 1][1];
  pintarTira($("cVentana"), s, e, [filaGT, filaPred, filaDif], (gx, x, alto) => {
    DATOS.tramos.forEach((tr, i) => {
      gx.strokeStyle = i === idx ? "#4fa3e0" : "rgba(255,255,255,0.5)";
      gx.strokeRect(x(tr.a) + 0.5, 0.5, Math.max(2, x(tr.b) - x(tr.a)), alto - 1);
    });
  });
  if (ATD) { $("atdInfo").textContent = infoATD(); pintarCapa(); pintarMapa(); }
}

// -- lista --
function marcarLista() {
  document.querySelectorAll("#lista li").forEach((li) => li.classList.toggle("actual", Number(li.dataset.i) === idx));
  const li = document.querySelector("#lista li.actual");
  if (li) li.scrollIntoView({ block: "nearest" });
}
function hacerLista() {
  const ol = $("lista"); ol.innerHTML = "";
  DATOS.tramos.forEach((t, i) => {
    if (ocultarBorde && t.borde) return;
    const li = document.createElement("li");
    li.dataset.i = i;
    const chips = (t.borde ? ["borde"] : []).concat(t.tipos)
      .map((c) => '<span class="chip ' + c + '">' + c + "</span>").join(" ");
    li.innerHTML = '<div class="cab"><span class="num">' + (i + 1) + '</span><span class="reloj">' + reloj(t.a) +
      "</span> " + chips + '</div><div class="txt">GT: ' + t.gt_txt + "<br>nuestra: " + t.pred_txt + "</div>";
    li.addEventListener("click", () => verTramo(i));
    ol.appendChild(li);
  });
  const borde = DATOS.tramos.filter((t) => t.borde).length;
  $("resumen").textContent = DATOS.tramos.length + " tramos: " + borde + " solo de borde, " +
    (DATOS.tramos.length - borde) + " con posesiones o paradas distintas";
  marcarLista();
}

// -- controles --
$("bAnt").onclick = () => saltar(-1);
$("bSig").onclick = () => saltar(1);
$("bRep").onclick = () => { if (idx >= 0) verTramo(idx); };
$("bPlay").onclick = () => { if (v.paused) { v.playbackRate = velocidad; v.play().catch(() => {}); } else v.pause(); };
$("bBucle").onclick = () => { bucle = !bucle; $("bBucle").classList.toggle("activo", bucle); };
$("bTodo").onclick = () => { idx = -1; marcarLista(); ir(DATOS.runs[0][0]); v.playbackRate = velocidad; v.play().catch(() => {}); };
$("bSaque").onclick = () => { idx = -1; marcarLista(); v.pause(); ir(DATOS.saque); };
$("ocultarBorde").onchange = (e) => { ocultarBorde = e.target.checked; hacerLista(); };
$("cATD").onchange = (e) => { verATD = e.target.checked; pintar(); };
$("cLineas").onchange = (e) => { verLineas = e.target.checked; pintar(); };
$("cSlots").onchange = (e) => { verSlots = e.target.checked; pintar(); };
function alternar(id) { const c = $(id); c.checked = !c.checked; c.onchange({ target: c }); }
function ponerVelocidad(x) {
  velocidad = x; v.playbackRate = x;
  document.querySelectorAll("[data-vel]").forEach((b) => b.classList.toggle("activo", Number(b.dataset.vel) === x));
}
document.querySelectorAll("[data-vel]").forEach((b) => (b.onclick = () => ponerVelocidad(Number(b.dataset.vel))));
function clicTira(canvas, rango) {
  canvas.addEventListener("click", (e) => {
    const r = rango(); if (!r) return;
    const caja = canvas.getBoundingClientRect();
    v.pause();
    ir(Math.floor(r[0] + (e.clientX - caja.left) / caja.width * (r[1] - r[0])));
  });
}
clicTira($("cTramo"), () => (DATOS.tramos[idx] ? [DATOS.tramos[idx].a, DATOS.tramos[idx].b] : null));
clicTira($("cVentana"), () => [DATOS.runs[0][0], DATOS.runs[DATOS.runs.length - 1][1]]);
document.addEventListener("keydown", (e) => {   // en captura, para que mande sobre las teclas del reproductor
  if (e.target.tagName === "INPUT" && e.target.type !== "checkbox") return;
  const k = e.key;
  if (k === " ") { e.preventDefault(); $("bPlay").onclick(); }
  else if (k === "ArrowRight" || k === "ArrowLeft") {
    e.preventDefault(); v.pause();
    ir(actual + (k === "ArrowRight" ? 1 : -1) * (e.shiftKey ? FPS : 1));
  }
  else if (k === "n" || k === "N") saltar(1);
  else if (k === "p" || k === "P") saltar(-1);
  else if (k === "r" || k === "R") $("bRep").onclick();
  else if (k === "l" || k === "L") $("bBucle").onclick();
  else if (k === "1") ponerVelocidad(0.25);
  else if (k === "2") ponerVelocidad(0.5);
  else if (k === "3") ponerVelocidad(1);
  else if (ATD && (k === "t" || k === "T")) alternar("cATD");
  else if (ATD && (k === "c" || k === "C")) alternar("cLineas");
  else if (ATD && (k === "s" || k === "S")) alternar("cSlots");
  else return;
  e.stopPropagation();
}, true);
window.addEventListener("resize", pintar);

ponerVelocidad(velocidad);
hacerLista();
actual = DATOS.runs[0][0];
pintar();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    main()
