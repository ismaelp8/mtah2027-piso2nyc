"""K7: las tres comprobaciones del instrumento, antes de entrenar en serio (docs/decisiones.md, 17/11, K7).

    python validation/conjunto/comprobar_k7.py metrica
    python validation/conjunto/comprobar_k7.py pasos --ref comprobar_ref --k7 comprobar_k7
    python validation/conjunto/comprobar_k7.py paridad --etiqueta k7s

Datos abiertos de otros partidos (la caché de `exportar.py` y de `exportar_metrica.py`). Lo puede ejecutar cualquiera,
Claude incluido. Solo imprime agregados. Hace falta torch para `pasos` y `paridad`.

- **metrica:** lo exportado de Metrica es lo de `validation/metrica/lector.py`, con sus dos condiciones (el balón y
  las etiquetas, frame a frame), y el balón no se ve en los frames `D`.
- **pasos:** `entrenar_k7.py c --parte-metrica 0` da los mismos pesos, bit a bit, que `entrenar.py todos --solo dfl`
  con la misma semilla y los mismos pasos. Si no, hay una diferencia que no es K7.
- **paridad:** los pesos que escribe `juntar_k7.py` (la versión que vota) dan en `possession/conjunto.py` la misma z
  que el modelo de torch, en un partido de SkillCorner de la mitad de entrenamiento. Como `paridad.py`: torch va en
  float32, así que se pide una diferencia máxima de z por debajo de 0,01.
"""

import argparse
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import cj_comun as cj  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def metrica():
    import refinar  # noqa: E402  (el lector de Metrica)
    from possession.tracking import D
    lc = refinar.lector_metrica()
    print("| partido | condición | frames | balón igual | etiquetas iguales | frames `D` | `D` con balón a la vista |")
    print("|---|---|---|---|---|---|---|")
    bien = True
    for id_ in [int(p) for p in lc.partidos()]:
        crudo = lc.leer(id_)
        with np.load(cj.fichero_partido("metrica", id_)) as d:
            guardado = {k: d[k] for k in d.files}
        for j, condicion in enumerate(lc.CONDICIONES):
            trk, gt = lc.tracking_de(crudo, condicion, id_)
            bx, by = guardado["bx_{}".format(j)], guardado["by_{}".format(j)]
            igual = all(np.array_equal(np.asarray(a, dtype=np.float32), b, equal_nan=True)
                        for a, b in ((trk.bx, bx), (trk.by, by), (trk.px, guardado["px"]), (trk.py, guardado["py"])))
            etiquetas = np.array_equal(gt, guardado["gt_control"])
            muerto = np.asarray(gt) == D
            a_la_vista = int(np.sum(muerto & np.isfinite(bx)))
            bien = bien and igual and etiquetas
            print("| {} | {} | {} | {} | {} | {} | {} ({:.2f} %) |".format(
                id_, condicion, len(gt), "sí" if igual else "**no**", "sí" if etiquetas else "**no**",
                int(muerto.sum()), a_la_vista, 100.0 * a_la_vista / max(int(muerto.sum()), 1)))
    return bien


def pasos(ref, k7):
    import torch
    a = torch.load(cj.fichero_pesos(ref, "todos"), map_location="cpu", weights_only=False)
    b = torch.load(cj.fichero_pesos(k7, "todos"), map_location="cpu", weights_only=False)
    print("Semillas: {} y {} · pasos: {} y {}".format(a["semilla"], b["semilla"], a["config"]["pasos"],
                                                      b["config"]["pasos"]))
    claves = sorted(set(a["pesos"]) | set(b["pesos"]))
    distintos = [k for k in claves if k not in a["pesos"] or k not in b["pesos"]
                 or not torch.equal(a["pesos"][k], b["pesos"][k])]
    print("Tensores comparados: {} · distintos: {}".format(len(claves), ", ".join(distintos) or "ninguno"))
    return not distintos and a["semilla"] == b["semilla"]


def paridad(etiqueta, partido):
    import torch
    import entrenar as en
    import entrenar_k7 as ek
    import red
    from paridad import tracking_de
    from possession import conjunto
    guardado = torch.load(cj.fichero_pesos(etiqueta, "todos"), map_location="cpu", weights_only=False)
    cfg = guardado["config"]
    clase = red.Conjunto if cfg["variante"] == "c" else ek.ConjuntoK7
    modelo = clase(cfg["oculto"], cfg["canales"], tuple(cfg["dilaciones"]), cfg["abandono"])
    modelo.load_state_dict(guardado["pesos"])
    modelo.eval()
    m = en.cargar("sc", partido, torch.device("cpu"), 33)
    z_torch, _ = en.predecir(modelo, m, *m["balones"][0])
    fichero = "pesos_{}.npz".format(etiqueta) if cfg["variante"] == "c" else "pesos_{}_media.npz".format(etiqueta)
    conjunto.PESOS = str(cj.carpeta() / fichero)
    conjunto._CACHE.clear()
    trk = tracking_de("sc", partido)
    z = conjunto.salidas(trk, None)[0]
    dentro = np.zeros(len(z), dtype=bool)
    for a, b in trk.blocks:
        dentro[a:b] = True
    dif = float(np.max(np.abs(z - z_torch)[dentro]))
    signo = int(np.sum((np.sign(z) != np.sign(z_torch)) & dentro))
    print("| sc {} | {} | {} | {:.2e} | {} |".format(partido, fichero, int(dentro.sum()), dif, signo))
    return dif < 1e-2


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("que", choices=("metrica", "pasos", "paridad"))
    parser.add_argument("--ref", default="comprobar_ref")
    parser.add_argument("--k7", default="comprobar_k7")
    parser.add_argument("--etiqueta", default=None)
    parser.add_argument("--partido", type=int, default=cj.SKILLCORNER[0])
    args = parser.parse_args()
    if args.que == "metrica":
        bien = metrica()
    elif args.que == "pasos":
        bien = pasos(args.ref, args.k7)
    else:
        print("| partido | pesos | frames | dif. máx. de z | signo de z distinto |")
        print("|---|---|---|---|---|")
        bien = paridad(args.etiqueta, args.partido)
    print("\nComprobación «{}»: **{}**".format(args.que, "pasa" if bien else "NO PASA"))
    sys.exit(0 if bien else 1)


if __name__ == "__main__":
    main()
