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
  que se ve y una tira de colores por tramo. Se abre con doble clic; no necesita internet ni instalar nada.

El vídeo sale de `games.video_path()` (la ruta de `MTAH_DATA_DIR`) o de `--video`. Si el navegador no lo
abre, la página deja elegirlo a mano.

- Por pantalla solo imprime cuántos tramos hay y dónde ha escrito. Ni etiquetas ni tiempos.
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
        if [c for _, _, c in sg] != [c for _, _, c in sp]:
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

def rle(codes):
    """[[primer frame, código], …] de cada racha, para buscar la etiqueta de un frame en la página."""
    inicios = np.concatenate(([0], np.flatnonzero(codes[1:] != codes[:-1]) + 1))
    return [[int(i), int(codes[i])] for i in inicios]


def pagina(gt, pred, lista, nombre, video_uri):
    datos = {
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


def main():
    parser = argparse.ArgumentParser(description="Página con los tramos en que la entrega y la GT pública "
                                                 "difieren, para verlos junto al vídeo en el navegador.")
    parser.add_argument("entrega", help="nombre de la entrega en evaluation/results (sin .csv) o ruta a un CSV")
    parser.add_argument("--gt", default=GT_PUBLICA, help="CSV de la GT (por defecto, la pública)")
    parser.add_argument("--video", default=None, help="vídeo táctico (por defecto, el de MTAH_DATA_DIR)")
    parser.add_argument("--margen", type=float, default=MARGEN_S, help="segundos a cada lado de cada tramo")
    parser.add_argument("--salida", default=None, help="ruta de la página (por defecto, en ~/mtah2027-salidas)")
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
        html = pagina(gt, pred, lista, nombre, pathlib.Path(os.path.abspath(video)).as_uri() if hay_video else "")
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
    <video id="v" preload="auto" controls playsinline></video>
    <div class="vivo">
      <span class="reloj" id="reloj">–</span>
      <span>GT <span class="eti" id="etiGT">–</span></span>
      <span>nuestra <span class="eti" id="etiPred">–</span></span>
      <span id="tramoActual" class="reloj"></span>
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
    <div class="nota" id="nota"></div>
    <div class="tira"><div class="rot">GT<br>nuestra<br>difieren</div><canvas id="cTramo" height="54"></canvas></div>
    <div class="tira"><div class="rot">ventana</div><canvas id="cVentana" height="40"></canvas></div>
    <div class="teclas">
      <kbd>espacio</kbd> reproducir/parar · <kbd>←</kbd><kbd>→</kbd> un frame · <kbd>Mayús</kbd>+<kbd>←</kbd><kbd>→</kbd> un segundo ·
      <kbd>N</kbd>/<kbd>P</kbd> tramo siguiente/anterior · <kbd>R</kbd> repetir · <kbd>L</kbd> bucle · <kbd>1</kbd><kbd>2</kbd><kbd>3</kbd> velocidad ¼, ½, 1.
      Clic en una tira para saltar a ese momento. Colores: azul H, naranja A, gris D, blanco X; rojo, donde difieren.
    </div>
  </section>
  <aside>
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
