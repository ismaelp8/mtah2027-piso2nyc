"""K8: las comprobaciones del instrumento, antes del piloto (docs/decisiones.md, 17/11, K8).

    python validation/conjunto/comprobar_k8.py crf
    python validation/conjunto/comprobar_k8.py pasos --ref comprobar_k8_ref --k8 comprobar_k8 --pliegue J03WMX

- **crf:** `crf.nll` da lo mismo que enumerar todos los caminos, en 200 secuencias cortas al azar (con grupos que no
  están vivos), y su gradiente pasa `torch.autograd.gradcheck`. No lee ningún dato.
- **pasos:** `entrenar_k8.py --lambda-crf 0` da los mismos pesos, bit a bit, que `entrenar.py` con la misma semilla y
  los mismos pasos (los dos `.pt` los escribe quien ejecuta la comprobación, con `--config '{"pasos": 20}'`).
"""

import argparse
import itertools
import math
import sys

import torch

import cj_comun as cj
import crf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def por_enumeracion(z, gt, vivo, w, c):
    """−log p del camino de la etiqueta, enumerando los 2^G caminos (los grupos que no están vivos no cuentan)."""
    total = 0.0
    for b in range(z.shape[0]):
        grupos = z.shape[1]
        energias = []
        for camino in itertools.product((0, 1), repeat=grupos):
            energias.append(energia(z[b], camino, vivo[b], w, c))
        sobran = int((~vivo[b]).sum())  # cada grupo que no está vivo duplica los caminos sin cambiar la energía
        log_z = torch.logsumexp(torch.stack(energias), 0) - sobran * math.log(2.0)
        total = total + (log_z - energia(z[b], [int(v) for v in gt[b]], vivo[b], w, c))
    return total


def energia(z, camino, vivo, w, c):
    valor = torch.zeros((), dtype=z.dtype)
    for t, y in enumerate(camino):
        if vivo[t]:
            valor = valor + (0.5 * w * z[t] if y == 0 else -0.5 * w * z[t])
            if t and vivo[t - 1] and camino[t - 1] != y:
                valor = valor - c
    return valor


def comprobar_crf():
    gen = torch.Generator().manual_seed(20261117)
    peor = 0.0
    for prueba in range(200):
        lote, grupos = 2, int(torch.randint(1, 9, (1,), generator=gen))
        z = torch.randn(lote, grupos, generator=gen, dtype=torch.float64) * 2.0
        gt = torch.randint(0, 2, (lote, grupos), generator=gen)
        vivo = torch.rand(lote, grupos, generator=gen) < 0.75
        w, c = float(torch.rand(1, generator=gen) * 30.0), float(torch.rand(1, generator=gen) * 40.0)
        rapido, _ = crf.nll(z, gt, vivo, w, c)
        lento = por_enumeracion(z, gt, vivo, w, c)
        peor = max(peor, abs(float(rapido) - float(lento)))
    z = torch.randn(2, 6, generator=gen, dtype=torch.float64, requires_grad=True)
    gt = torch.randint(0, 2, (2, 6), generator=gen)
    vivo = torch.tensor([[True, True, False, True, True, True], [False, True, True, True, False, True]])
    gradiente = torch.autograd.gradcheck(lambda x: crf.nll(x, gt, vivo, 20.0, 25.0)[0], (z,))
    print("200 secuencias al azar: diferencia máxima con la enumeración {:.2e} · gradcheck: {}".format(
        peor, "pasa" if gradiente else "no pasa"))
    return peor < 1e-9 and gradiente


def pasos(ref, k8, pliegue):
    a = torch.load(cj.fichero_pesos(ref, pliegue), map_location="cpu", weights_only=False)
    b = torch.load(cj.fichero_pesos(k8, pliegue), map_location="cpu", weights_only=False)
    print("Semillas: {} y {} · pasos: {} y {} · λ del CRF: {}".format(
        a["semilla"], b["semilla"], a["config"]["pasos"], b["config"]["pasos"], b["config"].get("lambda_crf")))
    claves = sorted(set(a["pesos"]) | set(b["pesos"]))
    if set(a["pesos"]) != set(b["pesos"]):
        print("Los tensores no son los mismos")
        return False
    distintos = [k for k in claves if not torch.equal(a["pesos"][k], b["pesos"][k])]
    maxima = max(float((a["pesos"][k] - b["pesos"][k]).abs().max()) for k in claves)
    print("Tensores comparados: {} · distintos bit a bit: {} · diferencia máxima {:.1e}".format(
        len(claves), len(distintos), maxima))
    # Cada script se reproduce bit a bit consigo mismo, pero entre dos scripts distintos el último bit puede cambiar
    # con cómo queda la memoria del proceso (17/11: con 1 paso difieren 4 tensores, con 2 ninguno y con 20 casi todos,
    # siempre por debajo de 3e-6). Así que se pide lo mismo salvo redondeo: menos de 1e-5 tras 20 pasos.
    return a["semilla"] == b["semilla"] and maxima < 1e-5


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("que", choices=("crf", "pasos"))
    parser.add_argument("--ref", default="comprobar_k8_ref")
    parser.add_argument("--k8", default="comprobar_k8")
    parser.add_argument("--pliegue", default=cj.PILOTO)
    args = parser.parse_args()
    bien = comprobar_crf() if args.que == "crf" else pasos(args.ref, args.k8, args.pliegue)
    print("\nComprobación «{}»: **{}**".format(args.que, "pasa" if bien else "NO PASA"))
    sys.exit(0 if bien else 1)


if __name__ == "__main__":
    main()
