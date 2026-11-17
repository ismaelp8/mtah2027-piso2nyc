"""B11 y B12 en SkillCorner: la mitad de entrenamiento y, solo con permiso, el examen (una vez, un candidato).

    python validation/secuencia/skillcorner.py
    python validation/secuencia/skillcorner.py --examen b11 --confirmo-el-unico-uso

Datos abiertos de otros partidos (A-League 2024/25, licencia MIT; `validation/skillcorner/descargar.py`). Lo
puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. La regla está en docs/decisiones.md (17/11, «B11
y B12, modelos de secuencia»), escrita antes de medir:

- **Mitad de entrenamiento** (`lector.ENTRENAMIENTO`), con el modelo de los 7 partidos de la DFL (`fuera=None`):
  el candidato pasa si, frente a `main`, saca +0,005 o más con los 10 partidos juntos y gana en 7 de 10, en las
  cuatro celdas: «detectado» y «detectado, suavizado», con el `D` de las etiquetas y con el propio. El intervalo
  del bootstrap se enseña, pero no decide. SkillCorner no se usó para entrenar.
- **Examen** (`lector.EXAMEN`): solo si un candidato pasa los puntos 1 y 3 en la DFL y la mitad de entrenamiento,
  después de avisar a la planificadora, una vez y para ese candidato. Mismo umbral. Cada uso se apunta en
  `validation/skillcorner/BITACORA.md` («Usos del examen») y en docs/decisiones.md.

`main` es la entrega de hoy: B5, `dead_state` y `decode_cortas_a_d` (`pipeline.PIECES`). El candidato solo cambia
la pieza de equipo.
"""

import argparse
import collections
import os
import sys
import time

import comun

sys.path.insert(0, os.path.join(comun.ROOT, "validation", "skillcorner"))
import lector as lc  # noqa: E402
import puntuar  # noqa: E402
from possession import aprendida, pipeline  # noqa: E402

UMBRAL = 0.005
GANA_DE = 7
MODOS = ("oraculo", "propio")
CANDIDATOS = {"b11": aprendida.evidence_b11, "b12": aprendida.evidence_b12, "b13": aprendida.evidence_b13,
              "b14": aprendida.evidence_b14, "b15": aprendida.evidence_b15}


def ejecutar(nombre, trk, gt, modo):
    extra = [puntuar.d_oraculo(gt)] if modo == "oraculo" else []
    piezas = None if nombre == "main" else {"candidates": CANDIDATOS[nombre]}
    return pipeline.run(trk, extra=extra, pieces=piezas)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--examen", choices=sorted(CANDIDATOS),
                        help="abre lector.EXAMEN para ESE candidato (una vez; con permiso del equipo)")
    parser.add_argument("--confirmo-el-unico-uso", action="store_true", dest="confirmado")
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--candidatos", nargs="+", choices=sorted(CANDIDATOS), default=sorted(CANDIDATOS),
                        help="en la mitad de entrenamiento: qué candidatos se miden (por defecto, los dos)")
    args = parser.parse_args()
    if args.examen:
        if not args.confirmado:
            print("El examen (lector.EXAMEN) se abre una vez por candidato y con el permiso del equipo en el momento.")
            print("Mira antes «Usos del examen» en validation/skillcorner/BITACORA.md. Si toca, añade --confirmo-el-unico-uso.")
            return 1
        ids, nombres, mitad = list(lc.EXAMEN), ["main", args.examen], "EXAMEN"
        print("### ATENCIÓN: se abre la mitad de EXAMEN de SkillCorner para {}. Apúntalo.\n".format(args.examen))
    else:
        ids, nombres, mitad = list(lc.ENTRENAMIENTO), ["main"] + sorted(args.candidatos), "ENTRENAMIENTO"
        lc.exigir_solo_entrenamiento(ids)

    rec = collections.defaultdict(list)  # (modo, condición, versión) -> recuento por partido
    for id_ in ids:
        t0 = time.time()
        crudo = lc.leer_crudo(id_)
        for cond in lc.VOTAN:
            trk, gt = lc.tracking_de(crudo, cond, id_)
            trk = puntuar.solo_lectura(trk)
            for modo in MODOS:
                for nombre in nombres:
                    rec[(modo, cond, nombre)].append(puntuar.contar(gt, ejecutar(nombre, trk, gt, modo)))
        print("partido {} en {:.0f} s".format(id_, time.time() - t0), file=sys.stderr, flush=True)

    print("SkillCorner, mitad de {} ({} partidos). main = B5, dead_state y decode_cortas_a_d; los candidatos, con el "
          "modelo de los 7 partidos de la DFL. Bootstrap pareado de {} (5–95 %).\n".format(
              mitad.lower(), len(ids), args.bootstrap))
    print("| `D` | condición | versión | spellF1 | frente a main [5–95 %] | gana en | posesiones predichas / reales |")
    print("|---|---|---|---|---|---|---|")
    veredictos = collections.defaultdict(list)
    for modo in MODOS:
        for cond in lc.VOTAN:
            base = rec[(modo, cond, "main")]
            jb = puntuar.juntar(base)
            f0 = puntuar.spell_f1(*jb)
            for nombre in nombres:
                r = rec[(modo, cond, nombre)]
                jr = puntuar.juntar(r)
                f = puntuar.spell_f1(*jr)
                if nombre == "main":
                    print("| {} | {} | main | {:.3f} | – | – | {} / {} |".format(modo, cond, f, jr[1], jr[0].shape[1]))
                    continue
                gana = sum(puntuar.spell_f1(a["flags"], a["n_pred"]) > puntuar.spell_f1(b["flags"], b["n_pred"])
                           for a, b in zip(r, base))
                i = puntuar.diferencia_bootstrap(jr, jb, args.bootstrap)
                print("| {} | {} | {} | {:.3f} | {:+.3f}{} | {} de {} | {} / {} |".format(
                    modo, cond, nombre, f, f - f0, " [{:+.3f} a {:+.3f}]".format(*i) if i else "", gana, len(r),
                    jr[1], jr[0].shape[1]))
                veredictos[nombre].append((f - f0 >= UMBRAL) and gana >= GANA_DE)
    print("\nRegla escrita antes de medir: +{:.3f} o más y ganar en {} de {}, en las cuatro celdas.".format(
        UMBRAL, GANA_DE, len(ids)))
    for nombre, celdas in veredictos.items():
        print("- {}: {} ({} de 4 celdas)".format(nombre, "PASA" if all(celdas) else "NO PASA", sum(celdas)))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
