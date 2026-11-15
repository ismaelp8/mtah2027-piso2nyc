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
                (1500, 2000, "H"), (2000, 2100, "D"), (2100, 2950, "A"), (2400, 2430, "H"),
                (2940, 2950, "H")])
# Fuera de la ventana la entrega dice H: no debe contar como diferencia. La posesión corta de 2400 la ponemos
# 2 s después, sin pisarse con la real: mismas rachas, pero no es un borde.
PRED = etiquetas([(0, 30, "H"), (30, 50, "H"), (50, 810, "H"), (810, 1500, "A"), (1500, 1700, "H"),
                  (1700, 1740, "A"), (1740, 2030, "H"), (2030, 2100, "D"), (2100, 2950, "A"), (2480, 2510, "H"),
                  (2950, N, "H")])


def escribir(ruta, labels):
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("frame,label\n")
        f.writelines("{},{}\n".format(i, c) for i, c in enumerate(labels))


def ejecutar(*args, datos=None):
    env = dict(os.environ, MTAH_DATA_DIR=datos or os.path.join(TMP, "no_existe"))
    r = subprocess.run([sys.executable, SCRIPT] + list(args), capture_output=True, text=True,
                       encoding="utf-8", env=env, cwd=ROOT)
    return r.returncode, r.stdout, r.stderr


def datos_de(ruta_html):
    with open(ruta_html, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"const DATOS = (.*?);\nconst FPS", html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</")), html


def escribir_partido(carpeta):
    """ATD, metadatos y homografía inventados de N frames, con los nombres de `games.asset_paths`. Sin vídeo.

    - 4 slots: los dos primeros del equipo local, quietos en y = 0,5; el último falta en los frames 1000–1099.
    - El balón avanza por x y está en y = 0,3; falta en 2000–2099 (NaN,NaN,NaN) y en 2100–2109 (un solo NaN).
    - Homografía: la misma escala en todos los frames; el 1500 no es válido (NaN y valid = 0).
    """
    import games
    paths = games.asset_paths(data_dir=carpeta)
    os.makedirs(os.path.dirname(paths["atd_raw"]))
    with open(paths["atd_meta"], "w", encoding="utf-8") as f:
        f.write('<Metadata><Team id="t1"><Name>Casa</Name></Team><Team id="t2"><Name>Fuera</Name></Team>'
                '<Player teamId="t1"/><Player teamId="t1"/><Player teamId="t2"/><Player teamId="t2"/></Metadata>\n')
    with open(paths["atd_raw"], "w", encoding="utf-8", newline="\n") as f:
        for frame in range(N):
            jug = ["{},0.5,0".format(0.1 + 0.2 * k) for k in range(4)]
            if 1000 <= frame < 1100:
                jug[3] = "NaN,NaN,NaN"
            balon = "{},0.3,1".format(frame / 3000)
            if 2000 <= frame < 2100:
                balon = "NaN,NaN,NaN"
            elif 2100 <= frame < 2110:
                balon = "NaN"
            f.write("{}:{}:{}\n".format(frame + 1, ";".join(jug), balon))
    with open(paths["homography"], "w", encoding="utf-8", newline="\n") as f:
        f.write("frame,h00,h01,h02,h10,h11,h12,h20,h21,h22,reprojection_error,valid\n")
        for frame in range(N):
            matriz = "1600,0,160,0,900,90,0,0,1" if frame != 1500 else ",".join(["NaN"] * 9)
            f.write("{},{},0.2,{}\n".format(frame, matriz, int(frame != 1500)))
    return paths


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
              == [(0, 125), (725, 885), (1125, 1345), (1625, 1815), (1925, 2105), (2325, 2585), (2865, 3000)],
              "siete tramos, en orden, con 3 s de margen y recortados en los extremos del vídeo")
    comprobar(lista[2]["dif"] == [[1200, 1230], [1260, 1270]], "las dos posesiones cortas se funden en un tramo")
    comprobar([t["borde"] for t in lista] == [False, True, False, False, True, False, False],
              "«borde» solo donde las posesiones y paradas son las mismas y cada una pisa a la suya")
    comprobar(lista[5]["gt_txt"] == lista[5]["pred_txt"] and not lista[5]["borde"],
              "una posesión corta desplazada sin pisarse no es un borde")
    comprobar([t["tipos"] for t in lista]
              == [["D"], ["equipo"], ["equipo"], ["equipo"], ["D"], ["equipo"], ["equipo"]],
              "tipos «equipo» y «D»")
    comprobar(lista[1]["nota"] == "cambio de equipo H→A: nosotros 0,40 s tarde (10 frames)",
              "nota del borde de equipo")
    comprobar(lista[4]["nota"] == "empieza la parada H→D: nosotros 1,20 s tarde (30 frames)",
              "nota del borde de la parada")
    comprobar(lista[2]["gt_txt"] == "…A → H 1,20 s → A 1,20 s → H 0,40 s → A…" and lista[2]["pred_txt"] == "…A…",
              "secuencias del tramo con posesiones que faltan")
    comprobar(lista[0]["gt_txt"] == "D 0,80 s → H…" or lista[0]["gt_txt"] == "…D → H…",
              "el tramo del extremo solo mira los frames evaluados")
    comprobar(len(cv.tramos(gt, pred, 0.5)) == 9, "con 0,5 s de margen las posesiones cortas van por separado")
    comprobar(cv.tramos(gt, gt.copy()) == [], "sin diferencias no hay tramos")

    # -- línea de comandos --
    html1 = os.path.join(TMP, "salida", "pagina.html")
    rc, out, err = ejecutar(pred_csv, "--gt", gt_csv, "--salida", html1)
    comprobar(rc == 0 and not err, "se ejecuta sin errores")
    lineas = out.strip().splitlines()
    comprobar(lineas == ["tramos: 7 (2 solo de borde, 5 con posesiones o paradas distintas)",
                         "ATD encima del vídeo: no (no encuentro atd_raw, atd_meta, homography en MTAH_DATA_DIR)",
                         "aviso: no encuentro el vídeo táctico (MTAH_DATA_DIR o --video); la página te dejará elegirlo",
                         "página escrita en {}".format(html1),
                         "ábrela con doble clic, o arrastrándola a la ventana del navegador"],
              "imprime solo recuentos y rutas")
    datos, html = datos_de(html1)
    comprobar(np.array_equal(desde_rle(datos["gt"]), gt) and np.array_equal(desde_rle(datos["pred"]), pred),
              "la página reconstruye las dos etiquetas")
    comprobar(datos["video"] == "" and datos["runs"] == [list(VENTANA)] and len(datos["tramos"]) == 7,
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
    comprobar(rc == 0 and out.startswith("tramos: 9 "), "--margen cambia cómo se funden")

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

    # -- el ATD encima del vídeo, con un partido inventado (ATD, metadatos y homografía) --
    datos_dir = os.path.join(TMP, "datos")
    paths = escribir_partido(datos_dir)
    html4 = os.path.join(TMP, "salida", "con_atd.html")
    rc, out, err = ejecutar(pred_csv, "--gt", gt_csv, "--salida", html4, datos=datos_dir)
    comprobar(rc == 0 and not err and "ATD encima del vídeo: sí, 3000 frames alrededor de la ventana" in out,
              "con los ficheros, la página lleva el ATD (y solo imprime cuántos frames)")
    atd = datos_de(html4)[0]["atd"]
    comprobar(atd["f0"] == 0 and atd["n"] == N and atd["equipo"] == [0, 0, 1, 1]
              and atd["campo"] == [105.3, 68.0] and atd["escala"] == 10000,
              "el ATD cubre la ventana y sus tramos con margen, con el equipo de cada slot")
    comprobar(atd["balon"][600] == [2000, 3000] and atd["balon"][2050] is None and atd["balon"][2105] is None,
              "el balón vuelve a 0–1 y falta donde el ATD no lo ve (NaN,NaN,NaN o un solo NaN)")
    comprobar(atd["jug"][600] == [0, 1000, 5000, 1, 3000, 5000, 2, 5000, 5000, 3, 7000, 5000]
              and atd["jug"][1050] == [0, 1000, 5000, 1, 3000, 5000, 2, 5000, 5000],
              "jugadores: slot, x e y de los que se ven")
    comprobar(atd["hom"][600] == [1600, 0, 160, 0, 900, 90, 0, 0, 1] and atd["hom"][1500] is None,
              "la homografía de cada frame, y ninguna donde no es válida")
    comprobar(atd["balon"][1] == [3, 3000], "el frame_id del ATD empieza en 1: la línea 2 es el frame 1")

    rc, out, _ = ejecutar(pred_csv, "--gt", gt_csv, "--salida", html4, "--sin-atd", datos=datos_dir)
    comprobar(rc == 0 and "ATD encima del vídeo: no (--sin-atd)" in out and datos_de(html4)[0]["atd"] is None,
              "--sin-atd deja la página sin ATD")

    tope, cv.ATD_MAX_FRAMES = cv.ATD_MAX_FRAMES, 100
    original = cv.games.asset_paths
    cv.games.asset_paths = lambda *a, **k: paths
    try:
        sin, aviso = cv.leer_atd(gt, lista)
        comprobar(sin is None and aviso == "no (3000 frames: más de 100, la página pesaría demasiado)",
                  "con demasiados frames, la página va sin ATD")
        cv.ATD_MAX_FRAMES = tope
        with open(paths["atd_raw"], "a", encoding="utf-8") as f:
            f.write("2999:0.1,0.5,0;0.3,0.5,0;0.5,0.5,0;0.7,0.5,0:mal,0.3,0\n")
        sin, aviso = cv.leer_atd(gt, lista)
        comprobar(sin is None and re.fullmatch(r"no \(ValueError en io\.py:\d+\)", aviso) is not None
                  and "mal" not in aviso, "si el ATD no se puede leer, la página va sin él y el aviso no enseña valores")
    finally:
        cv.ATD_MAX_FRAMES, cv.games.asset_paths = tope, original
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print()
print("todo bien" if not FALLOS else "{} fallos".format(len(FALLOS)))
sys.exit(1 if FALLOS else 0)
