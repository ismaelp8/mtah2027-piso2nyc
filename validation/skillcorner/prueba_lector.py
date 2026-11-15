"""Prueba del lector de SkillCorner con un partido inventado. No lee datos de ningún partido real.

    python validation/skillcorner/prueba_lector.py
"""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "harness"))
import lector as lc  # noqa: E402
import puntuar  # noqa: E402
from possession import pipeline  # noqa: E402

H, A, D, X = lc.H, lc.A, lc.D, lc.X
FALLOS = []


def comprobar(condicion, texto):
    print("{}  {}".format("ok   " if condicion else "FALLA", texto))
    if not condicion:
        FALLOS.append(texto)


def partido_inventado(carpeta):
    """Dos partes de 20 frames a 10 fps, 2 jugadores por equipo, campo de 100 × 60."""
    id_ = 7
    meta = {
        "home_team": {"id": 1}, "away_team": {"id": 2}, "pitch_length": 100, "pitch_width": 60,
        "players": [{"id": 11, "team_id": 1}, {"id": 12, "team_id": 1}, {"id": 21, "team_id": 2}, {"id": 22, "team_id": 2}],
        "match_periods": [{"start_frame": 0, "end_frame": 19}, {"start_frame": 20, "end_frame": 39}],
    }
    grupos = {**{t: "home team" for t in (4, 5, 6)}, **{t: "away team" for t in (8, 9)},
              **{t: "home team" for t in range(22, 36)}}
    filas = []
    for t in range(40):
        jugadores = [{"player_id": pid, "x": float(t + k), "y": float(k), "is_detected": not (pid == 22 and t < 10)}
                     for k, pid in enumerate((11, 12, 21, 22))]
        filas.append({"frame": t, "period": 1 if t < 20 else 2,
                      "ball_data": {"x": float(t), "y": 1.0, "z": 0.0, "is_detected": t != 5},
                      "player_data": jugadores,
                      "possession": {"player_id": None, "group": grupos.get(t)}})
    d = Path(carpeta) / str(id_)
    d.mkdir(parents=True)
    with open(d / "7_match.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)
    with open(d / "7_tracking_extrapolated.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in reversed(filas))  # desordenadas a propósito
    with open(d / "7_phases_of_play.csv", "w", encoding="utf-8") as f:
        f.write("frame_start,frame_end\n2,9\n12,17\n22,35\n")
    return d, id_


def main():
    with tempfile.TemporaryDirectory() as tmp:
        d, id_ = partido_inventado(tmp)
        crudo = lc.parsear(d, id_)
    comprobar(crudo["bx"][3] == 3.0 and crudo["bdet"][3] and not crudo["bdet"][5], "balón y su is_detected por frame")
    comprobar(list(crudo["team"]) == [H, H, A, A], "equipo de cada slot desde match.json")

    lab = lc.etiquetas(crudo["fases"], crudo["grupo"])
    esperado = [D, D, H, H, H, H, H, H, A, A, D, D, X, X, X, X, X, X, D, D]
    comprobar(list(lab[:20]) == esperado, "etiquetas: D fuera de las fases, relleno hacia delante y al inicio hacia atrás, X sin group")
    comprobar(set(lab[22:36]) == {H} and set(lab[20:22]) == {D} and set(lab[36:40]) == {D}, "segunda parte")

    i0, w = lc.instantes(20)
    comprobar(len(i0) == 48 and i0[-1] == 18 and abs(w[-1] - 0.8) < 1e-9, "20 muestras a 10 fps dan 48 frames a 25 fps")
    comprobar(i0[5] == 2 and abs(w[5]) < 1e-9 and i0[1] == 0 and abs(w[1] - 0.4) < 1e-9, "instantes de los frames a 25 fps")

    trk, gt = lc.tracking_de(crudo, "detectado", id_)
    comprobar(trk.blocks == ((0, 48), (548, 596)) and len(gt) == 596 and len(trk.bx) == 596, "dos partes con un hueco de 500")
    comprobar(set(gt[48:548]) == {X}, "hueco de X entre partes")
    comprobar(abs(trk.bx[1] - 50.4) < 1e-9 and abs(trk.by[1] - 31.0) < 1e-9, "metros con el origen en una esquina e interpolación")
    cerca_del_5 = [j for j in range(48) if 4.0 < j * 0.4 < 6.0]
    comprobar(np.isnan(trk.bx[cerca_del_5]).all(), "«detectado»: sin balón donde hace falta la muestra estimada")
    comprobar(gt[5] == H and gt[0] == D and gt[548 + 2] == D and gt[548 + 5] == H, "etiquetas en escalón")
    trk_e, _ = lc.tracking_de(crudo, "con el estimado", id_)
    comprobar(not np.isnan(trk_e.bx[cerca_del_5]).any(), "«con el estimado»: balón también donde no se detecta")
    trk_s, _ = lc.tracking_de(crudo, "detectado, suavizado", id_)
    comprobar(np.array_equal(np.isnan(trk_s.bx), np.isnan(trk.bx)), "el suavizado no rellena huecos")
    trk_j, _ = lc.tracking_de(crudo, "solo jugadores detectados", id_)
    comprobar(np.isnan(trk_j.px[:20]).sum() > np.isnan(trk.px[:20]).sum(), "«solo jugadores detectados» quita a los estimados")
    trk_b, _ = lc.tracking_de(crudo, "detectado", id_)
    comprobar(np.array_equal(trk_b.px, trk.px, equal_nan=True), "barajado determinista")
    comprobar(sorted(np.nanmean(trk.px[:48], axis=0).round(3)) == sorted(np.nanmean(trk_e.px[:48], axis=0).round(3)),
              "el barajado no cambia las posiciones, solo los slots")

    for nombre, extra in (("D oráculo", [puntuar.d_oraculo(gt)]), ("D propio", [])):
        codes = pipeline.run(puntuar.solo_lectura(trk), extra=extra)
        dentro = np.zeros(len(gt), bool)
        for a, b in trk.blocks:
            dentro[a:b] = True
        comprobar(len(codes) == len(gt) and set(codes[~dentro]) == {X} and X not in set(codes[dentro]),
                  "el pipeline corre con {}".format(nombre))
    print("\n{}".format("TODO BIEN" if not FALLOS else "{} FALLOS".format(len(FALLOS))))
    sys.exit(1 if FALLOS else 0)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
