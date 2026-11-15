"""Prueba `validation/partido/clips_ventana.py` con una GT y una entrega inventadas, de resultado conocido.

No lee nada del partido: los CSV y el «vídeo» son inventados y van a una carpeta temporal que se borra al
terminar, y `MTAH_DATA_DIR` apunta a una carpeta que no existe. También usa la GT pública (que se puede leer)
contra sí misma. Claude puede ejecutarla.

    python validation/scripts/prueba_clips_ventana.py

Comprueba:
- los tramos: dónde empiezan y acaban, el margen, que se funden los que se pisan, que se recortan en los
  extremos del vídeo y que fuera de los frames evaluados no cuenta ninguna diferencia;
- la etiqueta de cada tramo («borde», «equipo», «D») y la nota de los bordes movidos;
- la página: los datos que lleva reconstruyen las dos etiquetas, el vídeo se enlaza solo si existe y sale
  igual byte a byte dos veces;
- lo que imprime: solo recuentos y rutas;
- que se niega a escribir dentro del repo y que, si falla, no enseña valores.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "validation", "partido", "clips_ventana.py")
GT_PUBLICA = os.path.join(ROOT, "evaluation", "gt", "BAR-ATH_possession_gt_public.csv")
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
sys.path.insert(0, os.path.join(ROOT, "evaluation"))

N = 3000
VENTANA = (30, 2950)
FALLOS = []


def comprobar(condicion, que):
    print("{} {}".format("ok  " if condicion else "FALLA", que))
    if not condicion:
        FALLOS.append(que)


def etiquetas(rachas):
    """Lista de N etiquetas: X fuera de la ventana salvo que se diga otra cosa."""
    out = ["X"] * N
    for a, b, c in rachas:
        out[a:b] = [c] * (b - a)
    return out


GT = etiquetas([(30, 50, "D"), (50, 800, "H"), (800, 1500, "A"), (1200, 1230, "H"), (1260, 1270, "H"),
                (1500, 2000, "H"), (2000, 2100, "D"), (2100, 2950, "A"), (2940, 2950, "H")])
# Fuera de la ventana la entrega dice H: no debe contar como diferencia.
PRED = etiquetas([(0, 30, "H"), (30, 50, "H"), (50, 810, "H"), (810, 1500, "A"), (1500, 1700, "H"),
                  (1700, 1740, "A"), (1740, 2030, "H"), (2030, 2100, "D"), (2100, 2950, "A"), (2950, N, "H")])


def escribir(ruta, labels):
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("frame,label\n")
        f.writelines("{},{}\n".format(i, c) for i, c in enumerate(labels))


def ejecutar(*args):
    env = dict(os.environ, MTAH_DATA_DIR=os.path.join(TMP, "no_existe"))
    r = subprocess.run([sys.executable, SCRIPT] + list(args), capture_output=True, text=True,
                       encoding="utf-8", env=env, cwd=ROOT)
    return r.returncode, r.stdout, r.stderr


def datos_de(ruta_html):
    with open(ruta_html, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"const DATOS = (.*?);\nconst FPS", html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</")), html


def desde_rle(rle):
    out = np.empty(N, dtype=int)
    for k, (inicio, codigo) in enumerate(rle):
        fin = rle[k + 1][0] if k + 1 < len(rle) else N
        out[inicio:fin] = codigo
    return out


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
TMP = tempfile.mkdtemp(prefix="prueba_clips_")
try:
    import clips_ventana as cv
    import possession_metrics as pm

    gt_csv, pred_csv = os.path.join(TMP, "gt.csv"), os.path.join(TMP, "inventada.csv")
    escribir(gt_csv, GT)
    escribir(pred_csv, PRED)

    # -- tramos, sin pasar por la línea de comandos --
    gt, pred = cv.codigos(gt_csv), cv.codigos(pred_csv)
    comprobar(pm.valid_runs(gt) == [VENTANA], "la ventana inventada es la esperada")
    lista = cv.tramos(gt, pred, 3.0)
    comprobar([(t["a"], t["b"]) for t in lista]
              == [(0, 125), (725, 885), (1125, 1345), (1625, 1815), (1925, 2105), (2865, 3000)],
              "seis tramos, en orden, con 3 s de margen y recortados en los extremos del vídeo")
    comprobar(lista[2]["dif"] == [[1200, 1230], [1260, 1270]], "las dos posesiones cortas se funden en un tramo")
    comprobar([t["borde"] for t in lista] == [False, True, False, False, True, False],
              "«borde» solo donde las posesiones y paradas son las mismas")
    comprobar([t["tipos"] for t in lista] == [["D"], ["equipo"], ["equipo"], ["equipo"], ["D"], ["equipo"]],
              "tipos «equipo» y «D»")
    comprobar(lista[1]["nota"] == "cambio de equipo H→A: nosotros 0,40 s tarde (10 frames)",
              "nota del borde de equipo")
    comprobar(lista[4]["nota"] == "empieza la parada H→D: nosotros 1,20 s tarde (30 frames)",
              "nota del borde de la parada")
    comprobar(lista[2]["gt_txt"] == "…A → H 1,20 s → A 1,20 s → H 0,40 s → A…" and lista[2]["pred_txt"] == "…A…",
              "secuencias del tramo con posesiones que faltan")
    comprobar(lista[0]["gt_txt"] == "D 0,80 s → H…" or lista[0]["gt_txt"] == "…D → H…",
              "el tramo del extremo solo mira los frames evaluados")
    comprobar(len(cv.tramos(gt, pred, 0.5)) == 7, "con 0,5 s de margen las dos posesiones cortas van por separado")
    comprobar(cv.tramos(gt, gt.copy()) == [], "sin diferencias no hay tramos")

    # -- línea de comandos --
    html1 = os.path.join(TMP, "salida", "pagina.html")
    rc, out, err = ejecutar(pred_csv, "--gt", gt_csv, "--salida", html1)
    comprobar(rc == 0 and not err, "se ejecuta sin errores")
    lineas = out.strip().splitlines()
    comprobar(lineas == ["tramos: 6 (2 solo de borde, 4 con posesiones o paradas distintas)",
                         "aviso: no encuentro el vídeo táctico (MTAH_DATA_DIR o --video); la página te dejará elegirlo",
                         "página escrita en {}".format(html1),
                         "ábrela con doble clic, o arrastrándola a la ventana del navegador"],
              "imprime solo recuentos y rutas")
    datos, html = datos_de(html1)
    comprobar(np.array_equal(desde_rle(datos["gt"]), gt) and np.array_equal(desde_rle(datos["pred"]), pred),
              "la página reconstruye las dos etiquetas")
    comprobar(datos["video"] == "" and datos["runs"] == [list(VENTANA)] and len(datos["tramos"]) == 6,
              "sin vídeo, la página lo pedirá a mano")
    comprobar(datos["saque"] == 11186, "el saque inicial sale de games.py")
    comprobar("__DATOS__" not in html and "__NOMBRE__" not in html, "la plantilla queda rellena")

    html2 = os.path.join(TMP, "salida", "pagina2.html")
    ejecutar(pred_csv, "--gt", gt_csv, "--salida", html2)
    with open(html1, "rb") as f1, open(html2, "rb") as f2:
        comprobar(f1.read() == f2.read(), "la página sale igual byte a byte")

    video = os.path.join(TMP, "vídeo de prueba.mp4")
    open(video, "wb").close()
    html3 = os.path.join(TMP, "salida", "con_video.html")
    rc, out, _ = ejecutar(pred_csv, "--gt", gt_csv, "--salida", html3, "--video", video)
    datos3, _ = datos_de(html3)
    comprobar(rc == 0 and "aviso" not in out and datos3["video"].startswith("file:///")
              and datos3["video"].endswith("v%C3%ADdeo%20de%20prueba.mp4"),
              "con vídeo, la página lo enlaza (ruta con espacios y acentos)")

    rc, out, _ = ejecutar(pred_csv, "--gt", gt_csv, "--salida", html1, "--margen", "0.5")
    comprobar(rc == 0 and out.startswith("tramos: 7 "), "--margen cambia cómo se funden")

    dentro = os.path.join(ROOT, "pagina_prueba.html")
    rc, out, err = ejecutar(pred_csv, "--gt", gt_csv, "--salida", dentro)
    comprobar(rc != 0 and not os.path.exists(dentro) and "dentro del repo" in err, "se niega a escribir en el repo")

    corta = os.path.join(TMP, "corta.csv")
    escribir(corta, PRED[:-1])
    rc, out, err = ejecutar(corta, "--gt", gt_csv, "--salida", html1)
    comprobar(rc != 0 and re.fullmatch(r"ERROR: ValueError en clips_ventana\.py:\d+", err.strip()) is not None,
              "si falla, solo el tipo de error y la línea")

    rc, out, _ = ejecutar(GT_PUBLICA, "--salida", os.path.join(TMP, "salida", "publica.html"))
    comprobar(rc == 0 and out.startswith("tramos: 0 "), "la GT pública contra sí misma no da tramos")
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print()
print("todo bien" if not FALLOS else "{} fallos".format(len(FALLOS)))
sys.exit(1 if FALLOS else 0)
