"""Prueba las dos capas del golpeo de `possession/balon_video.py` (`golpeo_desde_hueco` y `golpeo_desde_ventana`) sin
datos de ningún partido.

    python validation/scripts/prueba_golpeo_capa.py

Lo puede ejecutar cualquiera, Claude incluido. El partido, el Smart Tagging y la caché de golpeos son inventados (la
caché la escribe el propio escritor de `validation/partido/balon_video_golpeo.py` en una carpeta temporal). Comprueba:

- sin `paths`, ceros y todo permitido, sin abrir ningún fichero;
- las constantes, columnas, nombre, formato, estado y huellas copiadas son las del script;
- los tramos exactos de cada candidato: +PESO_D en `D` desde el inicio de la ventana (o del hueco, con
  `golpeo_desde_hueco` y solo en la ventana con hueco) hasta el golpeo, y −PESO_JUEGO durante TRAS_GOLPEO frames,
  cortado en el siguiente reinicio; nada en las ventanas que no tienen el estado «golpeo»; nada en `H` ni en `A`;
- con el decodificador de la entrega, una parada que acababa 110 frames antes del golpeo y otra que acababa 20 después
  acaban justo en el golpeo con la capa (y no sin ella);
- se enchufa con `--capa` y no va en la entrega;
- una caché que falta, ilegible o que no cuadra (modelo, constantes, ventanas, huella, golpeo fuera de su ventana) da
  error sin valores y sin la excepción original encadenada;
- determinismo.
"""

import contextlib
import json
import os
import shutil
import sys
import tempfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, ROOT)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import games  # noqa: E402
from possession import balon_video as bv, pipeline, temporal, tracking  # noqa: E402
from possession.tracking import D, Tracking  # noqa: E402
import balon_video_golpeo as bvg  # noqa: E402
import detector as det  # noqa: E402
import prueba_pipeline as pp  # noqa: E402  (no_files)

FALLOS = []
N = 12000
BLOQUES = ((100, 6000), (6100, 11900))
PITCH = (105.3, 68.0)
GAME = games.GAME


def check(nombre, ok, detalle=""):
    print("  [{}] {}{}".format("OK" if ok else "FALLA", nombre, "   " + str(detalle) if detalle else ""))
    if not ok:
        FALLOS.append(nombre)


def carpeta_segura():
    carpeta = os.path.realpath(tempfile.mkdtemp(prefix="mtah_prueba_golpeo_capa_"))
    datos = os.path.realpath(games.DATA_DIR)
    if carpeta == datos or carpeta.startswith(datos + os.sep) or "mtah2027-data" in carpeta.lower():
        raise SystemExit("la carpeta temporal cae dentro de los datos del partido: no se ejecuta")
    return carpeta


def partido():
    """El ATD ve el balón todo el rato salvo de 1700 a 2099 (el hueco de la ventana A)."""
    bx = np.full(N, 50.0)
    by = np.full(N, 30.0)
    bx[1700:2100] = by[1700:2100] = np.nan
    px = np.column_stack([np.full(N, 20.0), np.full(N, 80.0)])
    py = np.column_stack([np.full(N, 20.0), np.full(N, 50.0)])
    return Tracking(bx, by, px, py, np.array([0, 1], dtype=np.int8), PITCH, BLOQUES, 25)


# (tipo, inicio, fin) de las ventanas, y lo que dice la caché de cada una.
VENTANAS = [
    ("corner kick", 2000, 2875, bvg.GOLPEO, 2150),  # A: con hueco (desde el 1700)
    ("free kick", 4000, 4875, bvg.GOLPEO, 4180),  # B: sin hueco
    ("throw-in", 7000, 7875, bvg.SIN_GOLPEO, -1),  # C: sin golpeo
    ("goal kick", 9000, 9875, bvg.GOLPEO, 9050),  # D: el siguiente reinicio (E) empieza en el 9100
    ("free kick", 9100, 9975, bvg.AMBIGUO, 9200),  # E: ambiguo
]


def events():
    salida = [{"code": "set pieces", "type": "kick off (start)", "start": 150, "end": 275}]
    salida += [{"code": "set pieces", "type": t, "start": a, "end": b} for t, a, b, _, _ in VENTANAS]
    return sorted(salida, key=lambda e: (e["start"], e["end"], e["code"], e["type"]))


def xml(ruta, evs):
    cuerpo = ["<instance><ID>{}</ID><start>{}</start><end>{}</end><code>{}</code><label><group>Type</group><text>{}"
              "</text></label></instance>".format(i, e["start"] / 25.0, e["end"] / 25.0, e["code"].upper(),
                                                  e["type"].title()) for i, e in enumerate(evs)]
    with open(ruta, "w") as f:
        f.write("<file><ALL_INSTANCES>{}</ALL_INSTANCES></file>".format("".join(cuerpo)))


def filas(trk, evs, cambios=None):
    ventanas = bvg.preparar_ventanas(trk, evs)
    salida = []
    for v, (tipo, a, b, estado, k) in zip(ventanas, VENTANAS):
        fila = {c: -1 for c in bvg.ENTEROS}
        fila.update({c: v[c] for c in ("inicio", "fin", "corte", "limite", "desde", "hasta", "reaparicion")})
        fila.update({"x_m": np.nan, "y_m": np.nan, "tipo": v["tipo"], "estado": estado,
                     "estado_hueco": v["estado_hueco"], "golpeo": k})
        salida.append(fila)
    for i, clave, valor in (cambios or []):
        salida[i][clave] = valor
    return ventanas, salida


def escribir(carpeta, trk, evs, cambios=None, meta_cambios=None, huella_falsa=False, ventanas_de=None):
    ventanas, fs = filas(trk, evs, cambios)
    arrays = bvg.arrays_de(fs)
    meta = bvg.metadatos_de(GAME, N, PITCH, det.MODELO_SHA256, {"python": "falso"}, 4, "c" * 64,
                            ventanas if ventanas_de is None else ventanas_de)
    for clave, valor in (meta_cambios or {}).items():
        if clave == "QUIETO":
            meta["constantes"]["QUIETO"] = valor
        else:
            meta[clave] = valor
    ruta = os.path.join(carpeta, bv.NOMBRE_GOLPEOS)
    bvg.guardar(ruta, arrays, meta, {}, "0" * 64 if huella_falsa else bvg.huella(arrays))
    return arrays


def esperado(desde_hueco):
    d = np.zeros(N)
    for tipo, a, b, estado, k in VENTANAS:
        if estado != bvg.GOLPEO:
            continue
        desde = 1700 if (desde_hueco and a == 2000) else a
        hasta = min(k + bv.TRAS_GOLPEO, 9100 if a == 9000 else N)
        d[desde:k] += bv.PESO_D
        d[k:hasta] -= bv.PESO_JUEGO
    return d


def prueba_sin_paths(trk):
    print("\n1. Sin paths")
    with pp.no_files():
        for capa in (bv.golpeo_desde_hueco, bv.golpeo_desde_ventana):
            score, allowed = capa(trk)
            check("{}: ceros y todo permitido, sin abrir nada".format(capa.__name__),
                  not score.any() and allowed.all() and score.shape == (N, 3))


def prueba_copias(trk, evs, arrays):
    print("\n2. Las copias del script")
    check("las constantes", bv.CONSTANTES_GOLPEO == bvg.CONSTANTES)
    check("las columnas", bv.ENTEROS_GOLPEO == bvg.ENTEROS and bv.REALES_GOLPEO == bvg.REALES
          and bv.TEXTOS_GOLPEO == bvg.TEXTOS)
    check("el nombre, el formato y el estado", bv.NOMBRE_GOLPEOS == bvg.NOMBRE_CACHE and bv.FORMATO_GOLPEOS ==
          bvg.FORMATO and bv.ESTADO_GOLPEO == bvg.GOLPEO)
    check("la huella de la caché", bv.huella_golpeos(arrays) == bvg.huella(arrays))
    check("la huella de las ventanas", bv.huella_ventanas_golpeo(bv.ventanas_golpeo(evs, trk.blocks))
          == bvg.huella_ventanas(bvg.preparar_ventanas(trk, evs)))
    check("la variante del detector", (bv.LADO, bv.FACTOR, bv.CONF, bv.MODELO_SHA256) == (det.LADO, det.FACTOR,
                                                                                         det.CONF, det.MODELO_SHA256))


def prueba_tramos(trk, paths):
    print("\n3. Los tramos de cada candidato")
    for capa, desde_hueco in ((bv.golpeo_desde_hueco, True), (bv.golpeo_desde_ventana, False)):
        score, allowed = capa(trk, paths=paths)
        check("{}: exactamente los tramos esperados en D".format(capa.__name__),
              np.array_equal(score[:, D], esperado(desde_hueco)))
        check("{}: nada en H ni en A y todo permitido".format(capa.__name__),
              not score[:, :2].any() and allowed.all())
    h, _ = bv.golpeo_desde_hueco(trk, paths=paths)
    v, _ = bv.golpeo_desde_ventana(trk, paths=paths)
    check("los dos candidatos solo se distinguen en el hueco de la ventana A (1700 a 1999)",
          np.array_equal(np.flatnonzero(h[:, D] != v[:, D]), np.arange(1700, 2000)))
    check("el empuje a juego se corta en el siguiente reinicio (9100)", v[9099, D] == -bv.PESO_JUEGO and
          v[9100, D] == 0)
    check("nada en las ventanas sin golpeo o ambiguas", not v[7000:7875, D].any() and not v[9100:9975, D].any())


def prueba_decodificador(trk, paths):
    print("\n4. Con el decodificador de la entrega")
    score = np.zeros((N, 3))
    score[:, 0] = 1.0  # la evidencia de equipo empuja a H, como el +1 de N1
    score[:, D] = -3.0  # el estado dice «juego»...
    score[1700:2040, D] = 3.0  # ...salvo en la parada A, que acaba 110 frames antes del golpeo (2150)
    score[3900:4200, D] = 3.0  # y en la B, que acaba 20 frames después del golpeo (4180)
    score[8950:9070, D] = 3.0  # y en la D, que acaba 20 frames después del golpeo (9050)
    allowed = np.ones((N, 3), dtype=bool)

    def fin_de_parada(etiquetas, desde):
        trozo = etiquetas[desde:]
        return desde + int(np.flatnonzero(trozo != D)[0])

    sin = temporal.decode(score, allowed, trk.blocks)
    capa, _ = bv.golpeo_desde_ventana(trk, paths=paths)
    con = temporal.decode(score + capa, allowed, trk.blocks)
    check("sin la capa, las paradas acaban en el 2040 y en el 4200", fin_de_parada(sin, 1800) == 2040
          and fin_de_parada(sin, 3950) == 4200, (fin_de_parada(sin, 1800), fin_de_parada(sin, 3950)))
    check("con la capa, las dos acaban justo en el golpeo", fin_de_parada(con, 1800) == 2150
          and fin_de_parada(con, 3950) == 4180, (fin_de_parada(con, 1800), fin_de_parada(con, 3950)))
    check("y la de la ventana D (9070 sin la capa) también", fin_de_parada(sin, 9000) == 9070
          and fin_de_parada(con, 9000) == 9050, (fin_de_parada(sin, 9000), fin_de_parada(con, 9000)))


def prueba_enchufe():
    print("\n5. Se enchufa con --capa y no va en la entrega")
    for nombre in ("balon_video.golpeo_desde_hueco", "balon_video.golpeo_desde_ventana"):
        _, capas = pipeline.overrides([], [nombre])
        check("{} se resuelve".format(nombre), capas[0] in (bv.golpeo_desde_hueco, bv.golpeo_desde_ventana))
        check("y no está en DELIVERY_LAYERS ni en PIECES", capas[0] not in pipeline.DELIVERY_LAYERS
              and nombre.split(".")[1] not in pipeline.PIECES.values())


def error_de(trk, paths):
    try:
        bv.golpeo_desde_ventana(trk, paths=paths)
    except bv.ErrorCache as e:
        return e
    return None


def prueba_errores(trk, evs, carpeta, paths):
    print("\n6. Cachés que faltan o no cuadran")
    ruta = os.path.join(carpeta, bv.NOMBRE_GOLPEOS)
    os.remove(ruta)
    e = error_de(trk, paths)
    check("sin caché, error que lo dice", e is not None and "falta la caché de golpeos" in str(e))
    with open(ruta, "wb") as f:
        f.write(b"no es un npz")
    e = error_de(trk, paths)
    check("ilegible: error sin la excepción original encadenada", e is not None and e.__cause__ is None
          and e.__suppress_context__)
    casos = [
        ("otro modelo", dict(meta_cambios={"modelo_sha256": "f" * 64}), "modelo"),
        ("otras constantes", dict(meta_cambios={"QUIETO": 26}), "constantes del golpeo"),
        ("otras ventanas", dict(ventanas_de=bvg.preparar_ventanas(trk, evs)[:-1]), "ventanas del Smart Tagging"),
        ("una huella que no cuadra", dict(huella_falsa=True), "huella"),
        ("un golpeo fuera de su ventana", dict(cambios=[(0, "golpeo", 2875 - bvg.MARGEN_FIN)]), "fuera de su ventana"),
        ("un golpeo antes del inicio", dict(cambios=[(1, "golpeo", 3999)]), "fuera de su ventana"),
    ]
    for nombre, kwargs, texto in casos:
        escribir(carpeta, trk, evs, **kwargs)
        e = error_de(trk, paths)
        check("{}: error sin valores".format(nombre), e is not None and texto in str(e)
              and not any(ch.isdigit() for ch in str(e).replace("sha256", "")), e)
    escribir(carpeta, trk, evs)


def main():
    print("Prueba de las dos capas del golpeo (sin datos de ningún partido)")
    trk = partido()
    evs = events()
    carpeta = carpeta_segura()
    try:
        paths = {"smart_tagging": os.path.join(carpeta, "smart_tagging_falso.xml"),
                 "atd_raw": os.path.join(carpeta, "atd_falso.txt")}
        xml(paths["smart_tagging"], evs)
        arrays = escribir(carpeta, trk, evs)
        check("la ventana A tiene hueco y la B no",
              [v["estado_hueco"] for v in bvg.preparar_ventanas(trk, evs)][:2] == ["hueco", "balón visto"])
        prueba_sin_paths(trk)
        prueba_copias(trk, evs, arrays)
        prueba_tramos(trk, paths)
        prueba_decodificador(trk, paths)
        prueba_enchufe()
        prueba_errores(trk, evs, carpeta, paths)
        uno, _ = bv.golpeo_desde_hueco(trk, paths=paths)
        dos, _ = bv.golpeo_desde_hueco(trk, paths=paths)
        print("\n7. Determinismo")
        check("dos llamadas dan lo mismo", np.array_equal(uno, dos))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    print("\n" + ("TODO BIEN" if not FALLOS else "FALLAN {}: {}".format(len(FALLOS), "; ".join(FALLOS))))
    return 1 if FALLOS else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
