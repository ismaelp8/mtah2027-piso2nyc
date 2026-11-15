"""D7 en datos abiertos: cuando el balón se ve fuera del campo, ¿es `D` en las etiquetas? Descriptivo.

    python validation/scripts/balon_fuera_abiertos.py

Datos abiertos de otros partidos: la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`; el examen
no se toca) y los 3 de Metrica. Lo puede ejecutar Claude. Solo imprime agregados.

Para qué (`docs/decisiones.md`, 15/11, D7): es el único número de datos abiertos que no es circular. En la DFL
el balón se queda quieto mientras está muerto y el harness lo tapa en los `D`. En SkillCorner el `D` sale de
las fases de juego, y en Metrica de los eventos; ninguno de los dos mira dónde está el balón.

Con la misma definición que el recuento del partido (`validation/partido/balon_fuera.py`): el balón visto a
más de 1 m fuera de las líneas, en los tramos con etiqueta, y rachas de 5 frames o más. Enseña:
- de los frames con el balón fuera, cuántos son `D`, `H`, `A` o `X` en las etiquetas (la precisión de
  «fuera es `D`»);
- de las rachas, cuántas caen enteras en juego y cuánto duran: es el riesgo de que una capa invente una
  parada (para eso, la racha tendría que durar lo bastante para pagar los dos costes de cambio).

No decide nada: el peso de la capa ya está fijado (W = 0, `peso_balon_fuera.py`).
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
sys.path.insert(0, ROOT)
import balon_fuera as bf  # noqa: E402

H, A, D, X = bf.pm.H, bf.pm.A, bf.pm.D, bf.pm.X
LARGAS = (25, 50, 125)  # frames: 1, 2 y 5 s


def contar(trk, gt, res):
    fuera, _ = bf.fuera_del_campo(np.asarray(trk.bx, float), np.asarray(trk.by, float), trk.pitch)
    for a, b in trk.blocks:
        f, e = fuera[a:b], np.asarray(gt[a:b])
        con_etiqueta = e != X
        res["frames"] += int(np.sum(f & con_etiqueta))
        for codigo in (H, A, D):
            res[codigo] += int(np.sum(f & (e == codigo)))
        for inicio, fin in bf.rachas(f & con_etiqueta):
            if fin - inicio < bf.RACHA_MINIMA:
                continue
            res["rachas"] += 1
            trozo = e[inicio:fin]
            if np.all(trozo != D):
                res["en_juego"] += 1
                for largo in LARGAS:
                    res[("en_juego", largo)] += int(fin - inicio >= largo)
            elif trozo[0] != D:
                res["empiezan_en_juego"] += 1


def nuevo():
    res = {"frames": 0, H: 0, A: 0, D: 0, "rachas": 0, "en_juego": 0, "empiezan_en_juego": 0}
    res.update({("en_juego", largo): 0 for largo in LARGAS})
    return res


def imprimir(nombre, condicion, partidos, res):
    def pct(n, total):
        return "{:.1f} %".format(100.0 * n / max(total, 1)).replace(".", ",")
    print("{} ({} partidos), balón «{}»: {} frames con el balón a más de 1 m fuera; D {} ({}), H {} y A {} "
          "({})".format(nombre, partidos, condicion, res["frames"], res[D], pct(res[D], res["frames"]), res[H],
                        res[A], pct(res[H] + res[A], res["frames"])))
    print("   rachas de 5 frames o más: {}; enteras en juego {} ({}), de ellas de 1 s o más {}, de 2 s o más {} "
          "y de 5 s o más {}; empiezan en juego y acaban en D {}".format(
              res["rachas"], res["en_juego"], pct(res["en_juego"], res["rachas"]), res[("en_juego", 25)],
              res[("en_juego", 50)], res[("en_juego", 125)], res["empiezan_en_juego"]))


def lector(fuente):
    """El lector de `validation/<fuente>/lector.py` (los dos se llaman igual: se cargan por su ruta)."""
    import importlib.util
    ruta = os.path.join(ROOT, "validation", fuente, "lector.py")
    spec = importlib.util.spec_from_file_location("lector_" + fuente, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def main():
    sk = lector("skillcorner")
    ids = [i for i in sk.ENTRENAMIENTO if i in sk.partidos()]
    sk.exigir_solo_entrenamiento(ids)
    crudos = {i: sk.leer_crudo(i) for i in ids}
    for condicion in ("detectado", "detectado, suavizado"):
        res = nuevo()
        for i in ids:
            trk, gt = sk.tracking_de(crudos[i], condicion, i)
            contar(trk, gt, res)
        imprimir("SkillCorner, mitad de entrenamiento", condicion, len(ids), res)
    del crudos
    me = lector("metrica")
    ids = me.partidos()
    for condicion in me.CONDICIONES:
        res = nuevo()
        for i in ids:
            trk, gt = me.tracking_de(me.leer(i), condicion, i)
            contar(trk, gt, res)
        imprimir("Metrica", condicion, len(ids), res)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
