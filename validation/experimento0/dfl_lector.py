"""Lector propio de las posiciones de la Bundesliga (DFL), por streaming y sin kloppy.

Por qué no kloppy: kloppy 3.18 guarda todos los frames de todos los objetos en diccionarios de Python
(unos 3,4 millones por partido), lo que no cabe en la memoria libre de un portátil. Este lector recorre el
XML una vez con lxml y guarda arrays de numpy, por parte:

- balón: `N`, `T` (ms), `X`, `Y`, `Z`, `S`, `BallPossession` y `BallStatus` (-1 si falta el atributo);
- jugadores: `X` e `Y` alineados a los frames del balón, una columna por jugador (`PersonId`) y una
  matriz por equipo (local y visitante por su `TeamId`, que se compara con `HomeTeamId`).

El resultado se guarda en una caché `.npz` FUERA del repo, junto a los datos abiertos. Solo imprime
agregados: recuentos, pasos de `N` y `T`, valores de los flags, tiempo y memoria.

Son datos abiertos de otros partidos: lo puede ejecutar cualquiera, Claude incluido.

Uso:
    python validation/experimento0/dfl_lector.py J03WMX [--carpeta DIR] [--xml-posiciones F --xml-metadatos F]
"""

import argparse
import collections
import glob
import json
import os
import sys
import time

import numpy as np
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anclas_metadatos  # noqa: E402

SECCIONES = {"firstHalf": 1, "secondHalf": 2}
SIN_DATO = -1


def carpeta_dfl():
    return anclas_metadatos.carpeta_por_defecto()


def carpeta_cache():
    return os.path.join(os.path.dirname(carpeta_dfl()), "dfl_cache")


def rutas_partido(partido, carpeta=None):
    carpeta = carpeta or carpeta_dfl()
    pos = glob.glob(os.path.join(carpeta, "DFL_04_03_positions_raw_observed_*_DFL-MAT-{}.xml".format(partido)))
    meta = glob.glob(os.path.join(carpeta, "DFL_02_01_matchinformation_*_DFL-MAT-{}.xml".format(partido)))
    ev = glob.glob(os.path.join(carpeta, "DFL_03_02_events_raw_*_DFL-MAT-{}.xml".format(partido)))
    if len(pos) != 1 or len(meta) != 1:
        sys.exit("ERROR: no encuentro un único XML de posiciones y de metadatos de {} en {}".format(partido, carpeta))
    return {"posiciones": pos[0], "metadatos": meta[0], "eventos": ev[0] if len(ev) == 1 else None}


def _a_ms(textos):
    """ISO 8601 con zona ('...T13:30:12.600+00:00') a milisegundos. Devuelve (ms, zonas vistas)."""
    zonas = collections.Counter(t[-6:] for t in textos)
    sin_zona = [t[:-6] if t[-6] in "+-" else t for t in textos]
    ms = np.array(sin_zona, dtype="datetime64[ms]").astype(np.int64)
    return ms, dict(zonas)


def leer_posiciones(ruta_xml):
    """Recorre el XML una vez. Devuelve {(seccion, team_id, person_id): dict de listas} y recuentos."""
    conjuntos = {}
    secciones_vistas = collections.Counter()
    actual = None
    contexto = etree.iterparse(ruta_xml, events=("start", "end"), tag=("FrameSet", "Frame"), huge_tree=True)
    for evento, el in contexto:
        if el.tag == "FrameSet":
            if evento == "start":
                seccion = el.get("GameSection")
                secciones_vistas[seccion] += 1
                clave = (seccion, el.get("TeamId"), el.get("PersonId"))
                es_balon = el.get("TeamId") == "BALL"
                actual = {"balon": es_balon, "N": [], "T": [], "X": [], "Y": [], "Z": [], "S": [],
                          "P": [], "B": []}
                conjuntos[clave] = actual
            else:
                el.clear()
                while el.getprevious() is not None:
                    del el.getparent()[0]
                actual = None
            continue
        # Frame
        if evento == "start" and actual is not None:
            g = el.get
            actual["N"].append(g("N"))
            actual["X"].append(g("X"))
            actual["Y"].append(g("Y"))
            if actual["balon"]:
                actual["T"].append(g("T"))
                actual["Z"].append(g("Z"))
                actual["S"].append(g("S"))
                actual["P"].append(g("BallPossession"))
                actual["B"].append(g("BallStatus"))
        elif evento == "end":
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]
    return conjuntos, dict(secciones_vistas)


def _flag(valores):
    """Lista de textos ('0', '1', '2' o None) a int8, con -1 para ausente; y recuento de valores crudos."""
    crudos = collections.Counter("ausente" if v is None else v for v in valores)
    arr = np.array([SIN_DATO if v is None else int(v) for v in valores], dtype=np.int8)
    return arr, dict(crudos)


def construir(conjuntos, meta):
    """Arrays por parte, con los jugadores alineados a los frames del balón."""
    salida = {"meta": meta, "partes": {}}
    resumen = {"partes": {}}
    for seccion, parte in sorted(SECCIONES.items(), key=lambda kv: kv[1]):
        balones = [v for (s, team, _), v in conjuntos.items() if s == seccion and team == "BALL"]
        if len(balones) != 1:
            raise ValueError("parte {}: {} FrameSets de balón".format(seccion, len(balones)))
        b = balones[0]
        n = np.array(b["N"], dtype=np.int64)
        orden = np.argsort(n, kind="stable")
        ordenado = bool(np.all(orden == np.arange(len(n))))
        n = n[orden]
        t_ms, zonas = _a_ms([b["T"][i] for i in orden])
        x = np.array(b["X"], dtype=np.float64)[orden]
        y = np.array(b["Y"], dtype=np.float64)[orden]
        z = np.array([np.nan if v is None else float(v) for v in b["Z"]], dtype=np.float64)[orden]
        s = np.array([np.nan if v is None else float(v) for v in b["S"]], dtype=np.float64)[orden]
        poss, poss_crudos = _flag([b["P"][i] for i in orden])
        estado, estado_crudos = _flag([b["B"][i] for i in orden])
        dn = np.diff(n)
        dt = np.diff(t_ms)
        res = {
            "frames_balon": int(len(n)),
            "N_primero": int(n[0]), "N_ultimo": int(n[-1]),
            "N_ordenado_en_xml": ordenado,
            "N_repetidos": int(np.sum(dn == 0)),
            "pasos_N_distintos_de_1": int(np.sum(dn != 1)),
            "huecos_N_frames_perdidos": int(np.sum(np.maximum(dn - 1, 0))),
            "pasos_T_distintos_de_40ms": int(np.sum(dt != 40)),
            "pasos_T_valores_raros": dict(collections.Counter(int(v) for v in dt[dt != 40]).most_common(5)),
            "zonas_horarias_T": zonas,
            "BallStatus": estado_crudos,
            "BallPossession": poss_crudos,
        }
        # Jugadores y árbitros, alineados a la rejilla de N del balón.
        equipos = {"local": meta["local_id"], "visitante": meta["visitante_id"]}
        por_equipo = {}
        otros = collections.Counter()
        fuera_de_rejilla = 0
        frames_jugadores = 0
        for nombre, team_id in equipos.items():
            personas = sorted(p for (s_, team, p) in conjuntos if s_ == seccion and team == team_id)
            mx = np.full((len(n), len(personas)), np.nan, dtype=np.float32)
            my = np.full((len(n), len(personas)), np.nan, dtype=np.float32)
            for j, persona in enumerate(personas):
                v = conjuntos[(seccion, team_id, persona)]
                pn = np.array(v["N"], dtype=np.int64)
                idx = np.searchsorted(n, pn)
                dentro = (idx < len(n)) & (n[np.minimum(idx, len(n) - 1)] == pn)
                fuera_de_rejilla += int(np.sum(~dentro))
                frames_jugadores += int(len(pn))
                mx[idx[dentro], j] = np.array(v["X"], dtype=np.float32)[dentro]
                my[idx[dentro], j] = np.array(v["Y"], dtype=np.float32)[dentro]
            por_equipo[nombre] = {"x": mx, "y": my, "personas": personas}
        for (s_, team, _p) in conjuntos:
            if s_ == seccion and team not in ("BALL", meta["local_id"], meta["visitante_id"]):
                otros[team] += 1
        res["jugadores_por_equipo"] = {k: len(v["personas"]) for k, v in por_equipo.items()}
        res["frames_jugadores"] = frames_jugadores
        res["frames_jugador_fuera_de_la_rejilla_del_balon"] = fuera_de_rejilla
        res["otros_framesets"] = dict(otros)
        jug_por_frame = (np.sum(~np.isnan(por_equipo["local"]["x"]), axis=1)
                         + np.sum(~np.isnan(por_equipo["visitante"]["x"]), axis=1))
        res["jugadores_por_frame_min_mediana_max"] = [int(jug_por_frame.min()), float(np.median(jug_por_frame)),
                                                     int(jug_por_frame.max())]
        salida["partes"][parte] = {"n": n, "t_ms": t_ms, "x": x, "y": y, "z": z, "s": s,
                                   "poss": poss, "estado": estado, "equipos": por_equipo}
        resumen["partes"][parte] = res
    return salida, resumen


def guardar_cache(datos, ruta):
    arrays = {}
    for parte, d in datos["partes"].items():
        for k in ("n", "t_ms", "x", "y", "z", "s", "poss", "estado"):
            arrays["p{}_{}".format(parte, k)] = d[k]
        for equipo, e in d["equipos"].items():
            arrays["p{}_{}_x".format(parte, equipo)] = e["x"]
            arrays["p{}_{}_y".format(parte, equipo)] = e["y"]
            arrays["p{}_{}_personas".format(parte, equipo)] = np.array(e["personas"])
    arrays["meta_json"] = np.array(json.dumps(datos["meta"], ensure_ascii=False))
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    np.savez_compressed(ruta, **arrays)


def cargar_cache(partido, carpeta=None):
    """Lo que guarda `guardar_cache`, en el mismo formato que devuelve `construir`."""
    ruta = os.path.join(carpeta or carpeta_cache(), "{}.npz".format(partido))
    z = np.load(ruta, allow_pickle=False)
    meta = json.loads(str(z["meta_json"]))
    partes = {}
    for parte in (1, 2):
        d = {k: z["p{}_{}".format(parte, k)] for k in ("n", "t_ms", "x", "y", "z", "s", "poss", "estado")}
        d["equipos"] = {e: {"x": z["p{}_{}_x".format(parte, e)], "y": z["p{}_{}_y".format(parte, e)],
                            "personas": list(z["p{}_{}_personas".format(parte, e)])}
                        for e in ("local", "visitante")}
        partes[parte] = d
    return {"meta": meta, "partes": partes}


def memoria_pico_mb():
    try:
        import psutil
        info = psutil.Process().memory_info()
        return round(getattr(info, "peak_wset", info.rss) / 1e6)
    except ImportError:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("partido", help="id del partido, por ejemplo J03WMX")
    parser.add_argument("--carpeta", default=None, help="carpeta con los XML (por defecto la de datos abiertos)")
    parser.add_argument("--xml-posiciones", default=None)
    parser.add_argument("--xml-metadatos", default=None)
    parser.add_argument("--cache", default=None, help="carpeta de la caché .npz (por defecto, junto a los datos)")
    args = parser.parse_args()

    if args.xml_posiciones and args.xml_metadatos:
        rutas = {"posiciones": args.xml_posiciones, "metadatos": args.xml_metadatos}
    else:
        rutas = rutas_partido(args.partido, args.carpeta)
    meta = anclas_metadatos.leer(rutas["metadatos"])
    inicio = time.time()
    conjuntos, secciones = leer_posiciones(rutas["posiciones"])
    t_lectura = time.time() - inicio
    datos, resumen = construir(conjuntos, meta)
    del conjuntos
    ruta_cache = os.path.join(args.cache or carpeta_cache(), "{}.npz".format(args.partido))
    guardar_cache(datos, ruta_cache)
    total = time.time() - inicio
    resumen.update({
        "partido": meta["partido"], "local": meta["local"], "visitante": meta["visitante"],
        "secciones_en_xml": secciones,
        "frames_balon_total": sum(p["frames_balon"] for p in resumen["partes"].values()),
        "segundos_lectura": round(t_lectura, 1), "segundos_total": round(total, 1),
        "memoria_pico_mb": memoria_pico_mb(),
        "cache_mb": round(os.path.getsize(ruta_cache) / 1e6, 1),
    })
    # El resumen (solo agregados) se guarda junto a la caché, fuera del repo, para reunir los 7 partidos.
    with open(ruta_cache[:-len(".npz")] + "_lector.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=1)
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
