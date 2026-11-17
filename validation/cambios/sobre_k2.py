"""El detector de cambios con el balón del ATD, encima de K2 y de `main` (docs/decisiones.md, 17/11).

    python validation/cambios/sobre_k2.py

Datos abiertos (los 7 partidos de la DFL). Lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Dos candidatos con la configuración fija de la segunda ronda (variante «respaldo»: el balón de la condición, el
mismo que ven B5 y K2), cada uno sobre dos bases, con el decodificador de la entrega:
- «main»: B5 (`aprendida.evidence_b5`);
- «K2»: `aprendida.evidence_k2`.
Cada pieza aprendida, con el pliegue que no vio el partido. Cada candidato se compara con su base.
"""

import concurrent.futures
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import comun  # noqa: E402
from comun import Base, aprendida, cambios, dfl, pipeline, puntuar  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# (giro, cambio de velocidad, frames de confirmación), γ, W, contra el otro equipo
CANDIDATOS = {
    "R1": ((20.0, 0.6, 20), 4.0, 50, True),
    "R2": ((cambios.GIRO_TOQUE, cambios.CAMBIO_VELOCIDAD, cambios.CONFIRMA), 4.0, 100, True),
}
BASES = {"main": aprendida.evidence_b5, "K2": aprendida.evidence_k2}
UMBRAL, DANO, MIN_PARTIDOS = 0.005, 0.005, 6


def partido(nombre_partido):
    cargado = dfl.cargar(nombre_partido)
    gt = cargado["gt"]
    decode = pipeline.default_piece("temporal")
    recuentos = {}
    for condicion in dfl.VOTAN:
        trk = pipeline.default_piece("ball")(puntuar.solo_lectura(dfl.tracking_de(cargado, condicion)))
        estado = pipeline.default_piece("dead_state")(trk)
        capas = {nombre: cambios.capa(cambios.p_reglas(trk, *regla), gamma, ventana, contra_d=contra)[0]
                 for nombre, (regla, gamma, ventana, contra) in CANDIDATOS.items()}
        for base_nombre, pieza in BASES.items():
            equipo = pieza(trk, fuera=nombre_partido)
            for modo in comun.MODOS_D:
                piezas = [equipo, estado] + ([puntuar.d_oraculo(gt["flag"])] if modo == "oraculo" else [])
                score, allowed, conflicto = pipeline.combine(piezas, len(trk.bx))
                if any(conflicto[a:b].any() for a, b in trk.blocks):
                    raise ValueError("las piezas se contradicen")
                base = Base(score, allowed, trk.blocks)
                preds = {"base": decode(base.score, base.allowed, base.blocks)}
                for nombre, capa in capas.items():
                    preds[nombre] = decode(base.score + capa, base.allowed, base.blocks)
                for quien, pred in preds.items():
                    for convencion in dfl.CONVENCIONES:
                        recuentos[(base_nombre, quien, condicion, modo, convencion)] = puntuar.contar(
                            gt[convencion], pred)
    return nombre_partido, recuentos


def main():
    partidos = list(dfl.PARTIDOS)
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        recuentos = dict(pool.map(partido, partidos))
    print("# El detector de cambios con el balón del ATD, encima de K2 y de `main`\n")
    print("Código: {} · decodificador {} · {}\n".format(
        puntuar.version_del_codigo(), pipeline.PIECES["temporal"],
        "; ".join("{}: reglas {}, γ {:g}, W {}{}".format(n, r, g, w, ", contra el otro" if c else "")
                  for n, (r, g, w, c) in CANDIDATOS.items())))
    print("Referencia: B5 (`main`) frente a K2, sin capa (descriptivo):\n")
    print("| `D` | condición | etiquetas | main | K2 | diferencia | gana en |")
    print("|---|---|---|---|---|---|---|")
    for modo in comun.MODOS_D:
        for condicion in dfl.VOTAN:
            for convencion in dfl.CONVENCIONES[::-1]:
                k2 = [recuentos[p][("K2", "base", condicion, modo, convencion)] for p in partidos]
                b5 = [recuentos[p][("main", "base", condicion, modo, convencion)] for p in partidos]
                dif, _, gana = comun.frente_a(k2, b5, 0)
                print("| {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} | {} de 7 |".format(
                    "etiquetas" if modo == "oraculo" else "propio", condicion, convencion, comun.spell(b5),
                    comun.spell(k2), dif, gana))
    veredictos = []
    for base_nombre in BASES:
        for nombre in CANDIDATOS:
            print("\n## {} sobre {}\n".format(nombre, base_nombre))
            print("| `D` | condición | etiquetas | base | candidato | diferencia [intervalo] | gana en | posesiones: base → "
                  "candidato (reales) |")
            print("|---|---|---|---|---|---|---|---|")
            pasa_1, pasa_3 = True, True
            for modo in comun.MODOS_D:
                for condicion in dfl.VOTAN:
                    for convencion in dfl.CONVENCIONES[::-1]:
                        cand = [recuentos[p][(base_nombre, nombre, condicion, modo, convencion)] for p in partidos]
                        ref = [recuentos[p][(base_nombre, "base", condicion, modo, convencion)] for p in partidos]
                        dif, intervalo, gana = comun.frente_a(cand, ref)
                        if convencion == "control":
                            pasa_1 &= dif >= UMBRAL and gana >= MIN_PARTIDOS
                        else:
                            pasa_3 &= dif >= -DANO
                        print("| {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} [{:+.3f} a {:+.3f}] | {} de 7 | {} → {} ({}) |"
                              .format("etiquetas" if modo == "oraculo" else "propio", condicion, convencion,
                                      comun.spell(ref), comun.spell(cand), dif, intervalo[0], intervalo[1], gana,
                                      sum(r["n_pred"] for r in ref), sum(r["n_pred"] for r in cand),
                                      sum(r["n_gt"] for r in ref)))
            veredictos.append((nombre, base_nombre, pasa_1, pasa_3))
            print("\nRegla: punto 1 **{}** · punto 3 **{}**.".format("pasa" if pasa_1 else "no pasa",
                                                                      "pasa" if pasa_3 else "no pasa"))
    print("\n## Veredicto\n")
    for nombre, base_nombre, pasa_1, pasa_3 in veredictos:
        print("- {} sobre {}: **{}**".format(nombre, base_nombre,
                                             "sigue a SkillCorner" if pasa_1 and pasa_3 else "no entra"))


if __name__ == "__main__":
    main()
