"""Comprobación C12 de la bitácora: el lector propio frente a kloppy 3.18, en un partido.

Tres comprobaciones acotadas, para no depender de una carga completa que puede no caber en memoria:

1. `balon`: la función interna de kloppy `_unstack_framesets` leyendo solo el balón (se saltan todos los
   demás objetos). Los recuentos de `BallStatus` y `BallPossession` por parte tienen que coincidir
   exactamente con los del lector propio.
2. `mapeo`: `sportec.load_tracking(limit=..., only_alive=False)`. Orden de los equipos, valores de
   `ball_state`, `ball_owning_team` frente al flag crudo, coordenadas frente al XML crudo, campo y fps.
3. `completo`: la carga completa que propone PASOS.md (`only_alive=False` y `to_df()`), en un proceso
   hijo vigilado: se mide la memoria pico y se corta si el hijo pasa de 9 GB o si al sistema le quedan
   menos de 1,5 GB libres.

Solo imprime agregados. Datos abiertos de otros partidos: lo puede ejecutar Claude.

Uso:
    python validation/experimento0/comprobar_kloppy.py J03WMX balon
    python validation/experimento0/comprobar_kloppy.py J03WMX mapeo
    python validation/experimento0/comprobar_kloppy.py J03WMX completo
"""

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfl_lector  # noqa: E402

LIMITE_HIJO_GB = 9.0
MINIMO_LIBRE_GB = 1.5


def ids_no_balon(ruta_xml):
    """PersonId de todos los FrameSet que no son el balón, con una pasada de texto por el XML."""
    patron = re.compile(r'<FrameSet [^>]*TeamId="([^"]+)"[^>]*PersonId="([^"]+)"')
    ids = set()
    with open(ruta_xml, encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("<FrameSet"):
                m = patron.search(linea)
                if m and m.group(1) != "BALL":
                    ids.add(m.group(2))
    return ids


def comprobar_balon(partido):
    from kloppy.infra.serializers.tracking.sportec.deserializer import _unstack_framesets
    rutas = dfl_lector.rutas_partido(partido)
    saltar = ids_no_balon(rutas["posiciones"])
    t0 = time.time()
    with open(rutas["posiciones"], "rb") as f:
        frames = _unstack_framesets(f, only_alive=False, objects_to_skip=saltar)
    t_kloppy = time.time() - t0
    propio = dfl_lector.cargar_cache(partido)
    salida = {"partido": partido, "objetos_saltados": len(saltar), "segundos_kloppy": round(t_kloppy, 1), "partes": {}}
    iguales = True
    for parte in (1, 2):
        fr = frames.get(parte, {})
        k_estado = collections.Counter(v["ball"].get("BallStatus", "ausente") for v in fr.values() if "ball" in v)
        k_poss = collections.Counter(v["ball"].get("BallPossession", "ausente") for v in fr.values() if "ball" in v)
        k_otros = sum(1 for v in fr.values() if set(v) - {"ball"})
        d = propio["partes"][parte]
        p_estado = collections.Counter(str(int(v)) for v in d["estado"])
        p_poss = collections.Counter(str(int(v)) for v in d["poss"])
        # Frame a frame: mismos N y mismos flags.
        n_k = np.array(sorted(fr), dtype=np.int64)
        mismos_n = bool(np.array_equal(n_k, d["n"]))
        if mismos_n:
            est_k = np.array([int(fr[n]["ball"]["BallStatus"]) for n in n_k], dtype=np.int8)
            pos_k = np.array([int(fr[n]["ball"]["BallPossession"]) for n in n_k], dtype=np.int8)
            difs = int(np.sum(est_k != d["estado"])) + int(np.sum(pos_k != d["poss"]))
        else:
            difs = None
        salida["partes"][parte] = {
            "frames_kloppy": len(fr), "frames_propio": int(len(d["n"])),
            "BallStatus_kloppy": dict(k_estado), "BallStatus_propio": dict(p_estado),
            "BallPossession_kloppy": dict(k_poss), "BallPossession_propio": dict(p_poss),
            "frames_kloppy_con_otros_objetos": k_otros,
            "mismos_N": mismos_n, "diferencias_frame_a_frame": difs,
        }
        iguales &= (dict(k_estado) == dict(p_estado) and dict(k_poss) == dict(p_poss) and mismos_n and difs == 0)
    salida["C12_coinciden_exactamente"] = iguales
    return salida


def comprobar_mapeo(partido, limite):
    from kloppy import sportec
    from kloppy.domain import BallState, Ground
    rutas = dfl_lector.rutas_partido(partido)
    t0 = time.time()
    ds = sportec.load_tracking(meta_data=rutas["metadatos"], raw_data=rutas["posiciones"],
                               limit=limite, only_alive=False)
    t_carga = time.time() - t0
    propio = dfl_lector.cargar_cache(partido)
    meta = propio["meta"]
    equipos = ds.metadata.teams
    d1 = propio["partes"][1]
    pos_idx = {int(n): i for i, n in enumerate(d1["n"])}
    estados = collections.Counter()
    discrepancias = collections.Counter()
    max_dif_xy = 0.0
    n_comparados = 0
    for fr in ds.frames:
        if fr.period.id != 1:
            continue
        i = pos_idx.get(int(fr.frame_id))
        if i is None:
            discrepancias["frame_sin_pareja"] += 1
            continue
        n_comparados += 1
        estados[fr.ball_state.value if fr.ball_state else "None"] += 1
        estado_crudo = int(d1["estado"][i])
        if (fr.ball_state == BallState.ALIVE) != (estado_crudo == 1):
            discrepancias["ball_state"] += 1
        local_k = fr.ball_owning_team is not None and fr.ball_owning_team.team_id == meta["local_id"]
        if local_k != (int(d1["poss"][i]) == 1):
            discrepancias["ball_owning_team"] += 1
        if fr.ball_coordinates is not None:
            dx = abs(fr.ball_coordinates.x - d1["x"][i])
            dy = abs(fr.ball_coordinates.y - d1["y"][i])
            max_dif_xy = max(max_dif_xy, float(dx), float(dy))
    return {
        "partido": partido, "limite": limite, "segundos_carga": round(t_carga, 1),
        "memoria_pico_mb": dfl_lector.memoria_pico_mb(),
        "teams_0": {"team_id": equipos[0].team_id, "ground": equipos[0].ground.value,
                    "es_HomeTeamId": equipos[0].team_id == meta["local_id"]},
        "teams_1": {"team_id": equipos[1].team_id, "ground": equipos[1].ground.value,
                    "es_GuestTeamId": equipos[1].team_id == meta["visitante_id"]},
        "orden_teams_en_xml": meta["orden_teams"],
        "sistema_de_coordenadas": str(ds.metadata.coordinate_system),
        "pitch_dimensions": [ds.metadata.pitch_dimensions.x_dim.min, ds.metadata.pitch_dimensions.x_dim.max,
                             ds.metadata.pitch_dimensions.y_dim.min, ds.metadata.pitch_dimensions.y_dim.max],
        "frame_rate": ds.metadata.frame_rate,
        "frames_comparados_parte_1": n_comparados,
        "valores_ball_state": dict(estados),
        "discrepancias": dict(discrepancias),
        "max_diferencia_xy_balon_m": round(max_dif_xy, 4),
    }


def _hijo_completo(partido):
    from kloppy import sportec
    rutas = dfl_lector.rutas_partido(partido)
    t0 = time.time()
    ds = sportec.load_tracking(meta_data=rutas["metadatos"], raw_data=rutas["posiciones"], only_alive=False)
    t_carga = time.time() - t0
    df = ds.to_df()
    t_df = time.time() - t0
    vivos = int((df["ball_state"] == "alive").sum())
    print(json.dumps({"frames": int(len(df)), "columnas": int(df.shape[1]), "frames_alive": vivos,
                      "valores_ball_state": {str(k): int(v) for k, v in df["ball_state"].value_counts(dropna=False).items()},
                      "segundos_load_tracking": round(t_carga, 1), "segundos_hasta_to_df": round(t_df, 1),
                      "memoria_pico_mb_hijo": dfl_lector.memoria_pico_mb()}))


def comprobar_completo(partido):
    import psutil
    t0 = time.time()
    hijo = subprocess.Popen([sys.executable, os.path.abspath(__file__), partido, "hijo-completo"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    proc = psutil.Process(hijo.pid)
    pico_rss, min_libre, cortado = 0, float("inf"), None
    while hijo.poll() is None:
        try:
            rss = proc.memory_info().rss
        except psutil.NoSuchProcess:
            break
        libre = psutil.virtual_memory().available
        pico_rss, min_libre = max(pico_rss, rss), min(min_libre, libre)
        if rss > LIMITE_HIJO_GB * 1e9 or libre < MINIMO_LIBRE_GB * 1e9:
            cortado = "el hijo pasó de {} GB".format(LIMITE_HIJO_GB) if rss > LIMITE_HIJO_GB * 1e9 \
                else "quedaban menos de {} GB libres".format(MINIMO_LIBRE_GB)
            hijo.kill()
            break
        time.sleep(0.5)
    salida_hijo, error_hijo = hijo.communicate()
    resultado = {"partido": partido, "segundos": round(time.time() - t0, 1),
                 "pico_rss_mb_observado": round(pico_rss / 1e6), "minimo_libre_sistema_mb": round(min_libre / 1e6),
                 "cortado": cortado, "codigo_salida": hijo.returncode}
    if salida_hijo.strip():
        resultado["hijo"] = json.loads(salida_hijo.strip().splitlines()[-1])
    if hijo.returncode not in (0, None) and not cortado:
        resultado["error_hijo_ultimas_lineas"] = error_hijo.strip().splitlines()[-3:]
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("partido")
    parser.add_argument("modo", choices=("balon", "mapeo", "completo", "hijo-completo"))
    parser.add_argument("--limite", type=int, default=3000)
    args = parser.parse_args()
    if args.modo == "hijo-completo":
        _hijo_completo(args.partido)
        return
    funcion = {"balon": lambda: comprobar_balon(args.partido),
               "mapeo": lambda: comprobar_mapeo(args.partido, args.limite),
               "completo": lambda: comprobar_completo(args.partido)}[args.modo]
    print(json.dumps(funcion(), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
