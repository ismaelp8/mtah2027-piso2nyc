"""K8: entrena el modelo conjunto en un pliegue con la pérdida de K2 más una pérdida por secuencia (CRF).

    python validation/conjunto/entrenar_k8.py J03WMX --etiqueta k8_s26 --semilla 20261126 --dispositivo cpu --columnas 33 --hilos 12
    python validation/conjunto/entrenar_k8.py J03WMX --etiqueta comprobar_k8 --lambda-crf 0 --config '{"pasos": 20}'

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, MIT). Lo puede ejecutar cualquiera, Claude incluido.
Solo imprime agregados. **No lee el examen de SkillCorner:** la lista es `cj_comun.SKILLCORNER`.

Lo fijado en docs/decisiones.md (17/11, K8, antes de entrenar). Es `entrenar.py` (la misma `CONFIG`, los mismos
proveedores, aumentos, lotes y pérdida) con un término más: λ · (−log p del camino de la etiqueta) por grupo vivo del
centro del trozo, con el CRF de `crf.py` (w = 5·α con α = 4, coste de cambio 25, λ = 1). Con `--lambda-crf 0` es
`entrenar.py` paso a paso: es la comprobación del instrumento (`comprobar_k8.py pasos`).

Escribe los pesos y las salidas fuera de muestra como `entrenar.py` (`cj_comun.fichero_pesos` y
`cj_comun.fichero_salida`), así que `juntar.py --alfa 4` y `paridad.py` los leen igual. `entrenar.py`, `red.py`,
`possession/conjunto.py` y los pesos de K2 no cambian.
"""

import argparse
import json
import math
import sys
import time

import numpy as np
import torch

import cj_comun as cj
import crf
import entrenar as en
import red

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LAMBDA_CRF = 1.0  # el peso del término de secuencia (fijado antes de entrenar)
ALFA = 4.0  # la α de la entrega: w = 5·α por grupo de 5 frames
COSTE = 25.0  # el coste de un cambio entre equipos en el decodificador de `main`


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pliegue", choices=cj.PLIEGUES)
    parser.add_argument("--etiqueta", required=True)
    parser.add_argument("--lambda-crf", type=float, default=LAMBDA_CRF)
    parser.add_argument("--config", default=None, help="JSON con los valores de CONFIG que se cambian (para comprobar)")
    parser.add_argument("--dispositivo", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--hilos", type=int, default=None)
    parser.add_argument("--semilla", type=int, default=None, help="por defecto, la del pliegue en `entrenar.py`")
    parser.add_argument("--columnas", type=int, default=en.SLOTS)
    args = parser.parse_args()
    cfg = dict(en.CONFIG)
    if args.config:
        cambios = json.loads(args.config)
        desconocidas = sorted(set(cambios) - set(cfg))
        if desconocidas:
            raise KeyError("claves desconocidas en --config: {}".format(desconocidas))
        cfg.update(cambios)
    device = torch.device(args.dispositivo)
    if args.hilos:
        torch.set_num_threads(args.hilos)
    semilla = args.semilla if args.semilla is not None else cj.SEMILLA + cj.PLIEGUES.index(args.pliegue)
    torch.manual_seed(semilla)
    rng = np.random.default_rng(semilla)
    gen = torch.Generator(device=device)
    gen.manual_seed(semilla)

    fuera_dfl, fuera_sc = cj.fuera_de(args.pliegue)
    inicio = time.time()
    dentro = {"dfl": [en.cargar("dfl", p, device, args.columnas) for p in cj.DFL if p not in fuera_dfl],
              "sc": [en.cargar("sc", p, device, args.columnas) for p in cj.SKILLCORNER if p not in fuera_sc]}
    print("# K8 · tanda «{}» · pliegue {} · semilla {}\n".format(args.etiqueta, args.pliegue, semilla))
    print("Entrena con {} partidos de la DFL y {} de SkillCorner; deja fuera: {}.".format(
        len(dentro["dfl"]), len(dentro["sc"]), ", ".join(str(p) for p in fuera_dfl + fuera_sc) or "ninguno"))
    print("Configuración: {}".format(json.dumps({k: cfg[k] for k in sorted(cfg)}, ensure_ascii=False)))
    print("CRF: λ {:g} · w = 5·α = {:g} · coste de cambio {:g} · dispositivo {} · torch {} · hilos {} · columnas {}\n"
          .format(args.lambda_crf, 5.0 * ALFA, COSTE, device.type, torch.__version__, torch.get_num_threads(),
                  args.columnas))

    modelo = red.Conjunto(cfg["oculto"], cfg["canales"], tuple(cfg["dilaciones"]), cfg["abandono"]).to(device)
    print("Pesos: {}".format(sum(v.numel() for v in modelo.parameters())), flush=True)
    opt = torch.optim.AdamW(modelo.parameters(), lr=cfg["tasa"], weight_decay=cfg["decaimiento"])

    def tasa(paso):
        if paso < cfg["calentamiento"]:
            return (paso + 1) / cfg["calentamiento"]
        avance = (paso - cfg["calentamiento"]) / max(1, cfg["pasos"] - cfg["calentamiento"])
        return 0.05 + 0.95 * 0.5 * (1.0 + math.cos(math.pi * avance))

    plan = torch.optim.lr_scheduler.LambdaLR(opt, tasa)
    mitad = cfg["lote"] // 2
    reparto_del_lote = [("dfl", mitad), ("sc", cfg["lote"] - mitad)]
    acumulado, cuenta = {}, 0
    for paso in range(cfg["pasos"]):
        modelo.train()
        elegidos = []
        for dominio, cuantos in reparto_del_lote:
            reparto = np.bincount(rng.integers(0, len(dentro[dominio]), size=cuantos), minlength=len(dentro[dominio]))
            elegidos += [(m, int(c)) for m, c in zip(dentro[dominio], reparto) if c]
        lote = en.aumentar(en.lote_de(elegidos, rng, cfg, device), cfg, gen)
        salidas = en.adelante(modelo, lote)
        total, terminos = en.perdida_de(salidas, lote, cfg)
        if args.lambda_crf:
            z = salidas[0]
            vivo = lote["gt"] < 2
            vivo[:, :cfg["margen"]] = False
            vivo[:, z.shape[1] - cfg["margen"]:] = False
            suma, n = crf.nll(z, lote["gt"], vivo, 5.0 * ALFA, COSTE)
            secuencia = suma / max(n, 1)
            total = total + args.lambda_crf * secuencia
            terminos["crf"] = float(secuencia.detach())
        opt.zero_grad(set_to_none=True)
        total.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 5.0)
        opt.step()
        plan.step()
        for k, v in terminos.items():
            acumulado[k] = acumulado.get(k, 0.0) + v
        cuenta += 1
        if (paso + 1) % 250 == 0 or paso == 0:
            print("paso {:5d} · z {:.4f} · cambios {:.4f} · flag {:.4f} · crf {:.4f} · {:.0f} s".format(
                paso + 1, *(acumulado.get(k, 0.0) / cuenta for k in ("z", "cambios", "flag", "crf")),
                time.time() - inicio), flush=True)
            acumulado, cuenta = {}, 0

    destino = cj.fichero_pesos(args.etiqueta, args.pliegue)
    destino.parent.mkdir(parents=True, exist_ok=True)
    cfg_guardada = dict(cfg, lambda_crf=args.lambda_crf, alfa_crf=ALFA, coste_crf=COSTE)
    torch.save({"pesos": modelo.state_dict(), "config": cfg_guardada, "pliegue": args.pliegue, "semilla": semilla},
               destino)
    fuera = ([en.cargar("dfl", p, device, args.columnas) for p in fuera_dfl]
             + [en.cargar("sc", p, device, args.columnas) for p in fuera_sc])
    if fuera:
        en.describir(modelo, fuera, "## Fuera de muestra: los partidos que el pliegue no vio (descriptivo, umbral 0,5)")
        for m in fuera:
            en.guardar_salidas(modelo, m, args.etiqueta, args.pliegue)
    print("\nHecho en {:.0f} s.".format(time.time() - inicio))


if __name__ == "__main__":
    main()
