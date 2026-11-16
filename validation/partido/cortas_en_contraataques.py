"""¿Borra «cortas a `D`» posesiones que acaba de crear la capa de los contraataques? Recuentos del partido.

**Lee dos entregas nuestras (etiquetas del partido frame a frame) y el Smart Tagging: lo ejecuta una persona,
en local, nunca Claude** (regla nº 1 de `CLAUDE.md`).

    python validation/partido/cortas_en_contraataques.py prueba_cortas_a_d --contra equipo_v8

Para qué: es el criterio 5 de los de daño de la idea 1.3 (`docs/decisiones.md`, 16/11, «la idea 1.3 se
desaparca»). `transiciones.evidence_equipo` está encendida en la entrega y empuja al equipo de cada «Attacking
Transition» durante sus 5 primeros segundos; «cortas a `D`» podría convertir en parada justo la posesión que ese
empujón acaba de crear. **Si son más de 2, se para y se avisa.**

La ventana no se recalcula a mano: se pide a `transiciones.push`, la misma función que usa la capa de la
entrega, así que son exactamente los frames donde empuja.

**Imprime solo agregados del partido entero:** cuántas posesiones tiene cada entrega, cuántas se quitan,
cuántas de las quitadas caen en la ventana de un contraataque y cuántas empiezan dentro de ella. Ni frames, ni
momentos, ni etiquetas. Si falla, imprime solo el tipo de error y las líneas del código. No escribe ficheros.
"""

import argparse
import os
import sys
import traceback

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import games  # noqa: E402
import possession_metrics as pm  # noqa: E402
from possession import temporal, tracking, transiciones  # noqa: E402

RESULTADOS = os.path.join(ROOT, "evaluation", "results")
TOPE_AVISO = 2  # más de 2 posesiones quitadas en la ventana: se para y se avisa


def ruta_de(entrega):
    return entrega if os.path.isfile(entrega) else os.path.join(RESULTADOS, entrega + ".csv")


def informe_de_error(error):
    """Tipo de error y líneas del código, sin el mensaje: podría llevar valores de datos.

    El mismo de `comparar_entregas.py`, para que los dos scripts del partido se puedan pegar igual.
    """
    pila = traceback.extract_tb(error.__traceback__)
    donde = " <- ".join("{}:{}".format(os.path.basename(f.filename), f.lineno) for f in reversed(pila[-4:]))
    return "ERROR {} en {}. Sin valores de datos: se puede pegar tal cual.".format(type(error).__name__, donde)


def ventana_contraataques(n, blocks, paths, game=games.GAME):
    """Los frames donde empuja la capa de los contraataques de la entrega, pedidos a `transiciones.push`."""
    fps = games.GAMES[game]["fps"]
    fases = transiciones.transitions(paths["smart_tagging"], fps)
    if not fases:
        raise ValueError("el Smart Tagging no trae ninguna ATTACKING TRANSITION con Team de los de TEAMS")
    score, _ = transiciones.push(n, blocks, fases, fps, neutral=False)
    return (score[:, tracking.H] > 0) | (score[:, tracking.A] > 0), len(fases)


def quitadas(antes, despues, blocks):
    """[(inicio, fin)] de las posesiones de `antes` que en `despues` son `D` enteras, por tramo evaluado."""
    out = []
    for a, b in blocks:
        for etiqueta, i, j in temporal.runs(np.asarray(antes[a:b])):
            if etiqueta in (tracking.H, tracking.A) and np.all(despues[a + i:a + j] == tracking.D):
                out.append((a + i, a + j))
    return out


def posesiones(codes, blocks):
    """Cuántas rachas de `H` o `A` hay en los tramos evaluados."""
    return sum(1 for a, b in blocks
               for etiqueta, _, _ in temporal.runs(np.asarray(codes[a:b])) if etiqueta in (tracking.H, tracking.A))


def medir(antes, despues, blocks, ventana):
    """Los recuentos del criterio 5, sin abrir nada. `ventana` es un array de bool por frame."""
    fuera_de_d = 0
    for a, b in blocks:
        cambia = np.asarray(antes[a:b]) != np.asarray(despues[a:b])
        fuera_de_d += int(np.sum(cambia & (np.asarray(despues[a:b]) != tracking.D)))
    lista = quitadas(antes, despues, blocks)
    solapan = sum(1 for i, j in lista if ventana[i:j].any())
    empiezan = sum(1 for i, j in lista if ventana[i])
    return {"posesiones_antes": posesiones(antes, blocks), "posesiones_despues": posesiones(despues, blocks),
            "quitadas": len(lista), "en_ventana": solapan, "empiezan_en_ventana": empiezan,
            "cambios_que_no_son_a_d": fuera_de_d}


def lineas(res, nombres, fases):
    out = ["## «Cortas a `D`»: posesiones quitadas y la capa de los contraataques", ""]
    out.append("Entregas: {} (antes) y {} (después). «Attacking Transition» con equipo: {}.".format(
        nombres[0], nombres[1], fases))
    out.append("")
    out.append("| qué | cuántas |")
    out.append("|---|---|")
    out.append("| posesiones en {} | {} |".format(nombres[0], res["posesiones_antes"]))
    out.append("| posesiones en {} | {} |".format(nombres[1], res["posesiones_despues"]))
    out.append("| posesiones quitadas (pasan a `D` enteras) | {} |".format(res["quitadas"]))
    out.append("| de ellas, en la ventana de un contraataque | {} |".format(res["en_ventana"]))
    out.append("| de ellas, que empiezan dentro de la ventana | {} |".format(res["empiezan_en_ventana"]))
    out.append("| frames que cambian a algo que no es `D` | {} |".format(res["cambios_que_no_son_a_d"]))
    out.append("")
    if res["cambios_que_no_son_a_d"]:
        out.append("**ERROR:** la variante solo puede pasar frames de `H` o `A` a `D`. Si cambia algo más, no es "
                   "«cortas a `D`» sola: revisa qué se ha generado antes de seguir.")
    if res["en_ventana"] > TOPE_AVISO:
        out.append("**PARA Y AVISA:** {} posesiones quitadas caen en la ventana de un contraataque, y el "
                   "criterio 5 pedía {} como mucho. La regla estaría borrando lo que esa capa acaba de "
                   "crear.".format(res["en_ventana"], TOPE_AVISO))
    else:
        out.append("Criterio 5 **cumplido**: {} en la ventana, {} como mucho.".format(
            res["en_ventana"], TOPE_AVISO))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("nueva", help="la entrega de prueba: nombre en evaluation/results (sin .csv) o ruta a un CSV")
    ap.add_argument("--contra", default="equipo_v8", help="la entrega vigente con la que se compara")
    args = ap.parse_args(argv)
    rutas = [ruta_de(args.contra), ruta_de(args.nueva)]
    for ruta in rutas:
        if not os.path.isfile(ruta):
            print("No encuentro una de las entregas: pasa su nombre en evaluation/results (sin .csv) o la ruta.")
            return 1
    antes, despues = [pm.label_codes(pm.read_label_csv(ruta)) for ruta in rutas]
    if len(antes) != len(despues):
        print("Las dos entregas no tienen el mismo número de filas.")
        return 1
    blocks = tracking.evaluated_blocks(games.GAME)
    ventana, fases = ventana_contraataques(len(antes), blocks, games.asset_paths())
    res = medir(antes, despues, blocks, ventana)
    print("\n".join(lineas(res, [os.path.basename(r) for r in rutas], fases)))
    return 2 if res["en_ventana"] > TOPE_AVISO or res["cambios_que_no_son_a_d"] else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as e:  # sin el mensaje: podría llevar valores de datos
        print(informe_de_error(e))
        sys.exit(1)
