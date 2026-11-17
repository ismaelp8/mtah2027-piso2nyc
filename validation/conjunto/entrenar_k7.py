"""K7: entrena el modelo conjunto con la DFL y Metrica, sin SkillCorner, para puntuarlo en SkillCorner.

    python validation/conjunto/entrenar_k7.py c --etiqueta k7c --dispositivo cpu --columnas 33 --hilos 12
    python validation/conjunto/entrenar_k7.py s --etiqueta k7s --dispositivo cpu --columnas 33 --hilos 12

Datos abiertos de otros partidos (DFL, CC BY 4.0; Metrica sample-data). Lo puede ejecutar cualquiera, Claude incluido.
Solo imprime agregados. Hace falta torch y la caché de `exportar.py` y de `exportar_metrica.py`. **No lee el examen de
SkillCorner:** la tabla descriptiva del final usa `cj_comun.SKILLCORNER`, la mitad de entrenamiento, que este modelo
no ha visto.

Lo fijado en docs/decisiones.md (17/11, K7, antes de entrenar). Es el entrenamiento de K2 (`entrenar.py`, con su
`CONFIG`, sus aumentos y su pérdida) con dos cambios:

- **los proveedores:** la DFL y Metrica (pliegue «todos» de los dos), en lugar de la DFL y SkillCorner. Metrica es
  un cuarto del lote (8 trozos de 32, `--parte-metrica`), para que cada partido pese parecido: 3 de 10 partidos. Los
  modelos de solo la DFL con los que se compara veían 32 trozos de la DFL por paso; estos ven 24, con los mismos 3.000
  pasos. En Metrica, `gt_control` son las etiquetas de sus eventos y no hay flag: el término del flag se enmascara,
  como en SkillCorner;
- **la variante:** `c` tiene una sola z, como K2; `s` tiene una z por proveedor (la de la DFL y la de Metrica), y nada
  más: las salidas de cambio y la del flag son compartidas. Cada trozo aprende con la z de su proveedor, y en un
  proveedor que no ha visto se usa la media de las dos. Como la última capa es lineal, esa media es una sola fila de
  pesos: `juntar_k7.py` la escribe así y `possession/conjunto.py` la puntúa sin cambiar nada.

**La limpieza de Metrica** (decidida antes de entrenar, con `signo_sin_balon.py`): en sus trozos, los frames vivos
sin balón crudo (sin balón en «tal cual») no cuentan en la pérdida de z ni en la de cambios. Sus etiquetas, sacadas de
eventos, no casan con el balón en los bordes de las paradas: K2 acierta el signo ahí el 44,7 %, frente al 89,0 % en la
DFL «como el ATD».

Con `c --parte-metrica 0` es `entrenar.py todos --solo dfl`, paso a paso: es la comprobación del instrumento
(`comprobar_k7.py pasos`).

`entrenar.py`, `red.py`, `possession/conjunto.py` y los pesos de K2 no cambian.
"""

import argparse
import json
import math
import sys
import time

import numpy as np
import torch
import torch.nn as nn

import cj_comun as cj
import entrenar as en
import red

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROVEEDORES = ("dfl", "metrica")
PARTE_METRICA = 0.25  # la parte del lote que viene de Metrica: 8 trozos de 32 (fijada antes de entrenar)
METRICA = (1, 2, 3)  # los 3 partidos de sample-data (validation/metrica/lector.py)


def limpiar_metrica(m):
    """La limpieza de Metrica, sobre un partido cargado con `entrenar.cargar`: los frames vivos sin balón crudo pasan a
    no contar (z a 3 y la clase de cambios a −1). Las clases se calcularon antes, con las etiquetas enteras, así que
    los cambios no se mueven de sitio. Devuelve (frames que dejan de contar, frames vivos)."""
    with np.load(cj.fichero_partido("metrica", m["partido"])) as d:
        sin_balon = np.isnan(d["bx_0"])
    gt = m["np"]["gt"]
    mascara = (gt < 2) & sin_balon
    t = torch.as_tensor(mascara, device=m["gt"].device)
    m["gt"] = torch.where(t, torch.full_like(m["gt"], 3), m["gt"])
    m["clase"] = torch.where(t, torch.full_like(m["clase"], -1), m["clase"])
    return int(mascara.sum()), int((gt < 2).sum())


class ConjuntoK7(red.Conjunto):
    """`red.Conjunto` con una z por proveedor: la salida 0 es la de la DFL y la 4, la de Metrica.

    Si `self.proveedor` es un tensor booleano por trozo (True: la DFL), cada trozo saca la z de su proveedor; si es
    None, la media de las dos. Las otras tres salidas (los dos cambios y el flag) son las de K2.
    """

    def __init__(self, oculto=32, canales=40, dilaciones=(1, 2, 4, 8, 16, 32), abandono=0.1):
        super().__init__(oculto, canales, dilaciones, abandono)
        self.salida = nn.Conv1d(canales, 5, 1)
        self.proveedor = None

    def forward(self, por_slot, hay, team, impares, pares):
        u_h, u_a = self.equipos(por_slot, hay, team)
        directa = self.g(u_h, u_a, impares, pares)
        cambiada = self.g(u_a, u_h, -impares, pares)
        z_dfl = 0.5 * (directa[:, 0] - cambiada[:, 0])
        z_otro = 0.5 * (directa[:, 4] - cambiada[:, 4])
        if self.proveedor is None:
            z = 0.5 * (z_dfl + z_otro)
        else:
            z = torch.where(self.proveedor[:, None], z_dfl, z_otro)
        par = 0.5 * (directa[:, 1] + cambiada[:, 1])
        impar = 0.5 * (directa[:, 2] - cambiada[:, 2])
        flag = 0.5 * (directa[:, 3] - cambiada[:, 3])
        return z, par + impar, par - impar, flag


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("variante", choices=("c", "s"), help="c: una sola z; s: una z por proveedor")
    parser.add_argument("--etiqueta", required=True, help="nombre de la tanda: los pesos van con él")
    parser.add_argument("--parte-metrica", type=float, default=PARTE_METRICA)
    parser.add_argument("--dispositivo", choices=("cuda", "cpu"), default="cpu")
    parser.add_argument("--hilos", type=int, default=None)
    parser.add_argument("--semilla", type=int, default=None, help="por defecto, la de «todos» en `entrenar.py`")
    parser.add_argument("--columnas", type=int, default=en.SLOTS)
    parser.add_argument("--sin-describir", action="store_true", help="no enseña la tabla de SkillCorner al final")
    parser.add_argument("--config", default=None, help="JSON con los valores de CONFIG que se cambian (para comprobar)")
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
    semilla = args.semilla if args.semilla is not None else cj.SEMILLA + cj.PLIEGUES.index("todos")
    torch.manual_seed(semilla)
    rng = np.random.default_rng(semilla)
    gen = torch.Generator(device=device)
    gen.manual_seed(semilla)

    inicio = time.time()
    dentro = {"dfl": [en.cargar("dfl", p, device, args.columnas) for p in cj.DFL],
              "metrica": [en.cargar("metrica", p, device, args.columnas) for p in METRICA]}
    limpieza = [limpiar_metrica(m) for m in dentro["metrica"]]
    print("# K7{} · tanda «{}» · semilla {}\n".format(args.variante, args.etiqueta, semilla))
    print("Entrena con {} partidos de la DFL y {} de Metrica, sin SkillCorner. Variante {}: {}.".format(
        len(dentro["dfl"]), len(dentro["metrica"]), args.variante,
        "una sola z" if args.variante == "c" else "una z por proveedor; fuera, la media de las dos"))
    print("Limpieza de Metrica: dejan de contar {} de {} frames vivos ({:.1f} %), los que no tienen balón crudo.".format(
        sum(a for a, _ in limpieza), sum(b for _, b in limpieza),
        100.0 * sum(a for a, _ in limpieza) / max(sum(b for _, b in limpieza), 1)))
    print("Configuración: {}".format(json.dumps({k: cfg[k] for k in sorted(cfg)}, ensure_ascii=False)))
    print("Parte de Metrica en el lote: {:g} · dispositivo {} · torch {} · hilos {} · columnas de slots {}\n".format(
        args.parte_metrica, device.type, torch.__version__, torch.get_num_threads(), args.columnas))

    clase = red.Conjunto if args.variante == "c" else ConjuntoK7
    modelo = clase(cfg["oculto"], cfg["canales"], tuple(cfg["dilaciones"]), cfg["abandono"]).to(device)
    print("Pesos: {}".format(sum(v.numel() for v in modelo.parameters())), flush=True)
    opt = torch.optim.AdamW(modelo.parameters(), lr=cfg["tasa"], weight_decay=cfg["decaimiento"])

    def tasa(paso):
        if paso < cfg["calentamiento"]:
            return (paso + 1) / cfg["calentamiento"]
        avance = (paso - cfg["calentamiento"]) / max(1, cfg["pasos"] - cfg["calentamiento"])
        return 0.05 + 0.95 * 0.5 * (1.0 + math.cos(math.pi * avance))

    plan = torch.optim.lr_scheduler.LambdaLR(opt, tasa)
    de_metrica = int(round(cfg["lote"] * args.parte_metrica))
    reparto_del_lote = [(d, c) for d, c in (("dfl", cfg["lote"] - de_metrica), ("metrica", de_metrica)) if c]
    acumulado, cuenta = {}, 0
    for paso in range(cfg["pasos"]):
        modelo.train()
        elegidos = []
        for dominio, cuantos in reparto_del_lote:
            reparto = np.bincount(rng.integers(0, len(dentro[dominio]), size=cuantos), minlength=len(dentro[dominio]))
            elegidos += [(m, int(c)) for m, c in zip(dentro[dominio], reparto) if c]
        lote = en.aumentar(en.lote_de(elegidos, rng, cfg, device), cfg, gen)
        if args.variante == "s":
            modelo.proveedor = lote["es_dfl"]
        total, terminos = en.perdida_de(en.adelante(modelo, lote), lote, cfg)
        opt.zero_grad(set_to_none=True)
        total.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 5.0)
        opt.step()
        plan.step()
        for k, v in terminos.items():
            acumulado[k] = acumulado.get(k, 0.0) + v
        cuenta += 1
        if (paso + 1) % 250 == 0 or paso == 0:
            print("paso {:5d} · z {:.4f} · cambios {:.4f} · flag {:.4f} · {:.0f} s".format(
                paso + 1, *(acumulado[k] / cuenta for k in ("z", "cambios", "flag")), time.time() - inicio),
                flush=True)
            acumulado, cuenta = {}, 0
    if args.variante == "s":
        modelo.proveedor = None  # fuera de sus dos proveedores, la media de las dos z

    destino = cj.fichero_pesos(args.etiqueta, "todos")
    destino.parent.mkdir(parents=True, exist_ok=True)
    cfg_guardada = dict(cfg, variante=args.variante, proveedores=list(PROVEEDORES), parte_metrica=args.parte_metrica)
    torch.save({"pesos": modelo.state_dict(), "config": cfg_guardada, "pliegue": "todos", "semilla": semilla,
                "solo": "dfl+metrica"}, destino)
    print("\nPesos en {}.".format(destino.name))

    if not args.sin_describir:
        fuera = [en.cargar("sc", p, device, args.columnas) for p in cj.SKILLCORNER]
        en.describir(modelo, fuera, "## Fuera de muestra: SkillCorner, mitad de entrenamiento, que este modelo no vio "
                                    "(descriptivo, umbral 0,5)")
    print("\nHecho en {:.0f} s.".format(time.time() - inicio))


if __name__ == "__main__":
    main()
