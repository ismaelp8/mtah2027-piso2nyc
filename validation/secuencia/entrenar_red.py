"""Entrena B11 (convolucional) o B12 (GRU) en un pliegue de la DFL, con torch en CPU.

    python validation/secuencia/entrenar_red.py b11 J03WMX     # el pliegue sin J03WMX (para el harness)
    python validation/secuencia/entrenar_red.py b12 todos      # el de los 7 (la entrega y SkillCorner)

Hace falta torch (el entorno `mtah2027-balon`) y los canales de `exportar.py`. Datos abiertos de otros partidos
(DFL, CC BY 4.0): lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Lo que hace es lo fijado antes de medir (docs/decisiones.md, 17/11, «B11 y B12, modelos de secuencia»):
- los 6 partidos del pliegue (o los 7), con el balón de las dos condiciones que votan, como ejemplos aparte;
- canales divididos por su raíz cuadrática media en esos frames;
- entropía cruzada sobre z solo en los frames vivos donde el flag y control coinciden (1 si el flag es `H`);
- z = ½·(g(x) − g(espejo de x)): antisimétrico por construcción;
- AdamW, un hilo, semilla fija y pasos fijos (`comun.B11`, `comun.B12`), sin parada temprana.

Escribe los pesos del pliegue en `comun.fichero_pesos` (fuera del repo); `juntar.py` elige α y los junta en
`possession/secuencia_pesos.npz`. Al final enseña, como descripción, el acierto por frame dentro del pliegue y en
el partido que quedó fuera, y la diferencia entre el z de torch y el de numpy (`possession.secuencia`).
"""

import argparse
import time

import numpy as np
import torch
import torch.nn as nn

import comun
from possession import secuencia

NI = secuencia.N_IMPARES
TROZOS_B12 = 2


def espejo(x, eje):
    """Los impares cambian de signo; los pares no. `eje` es el de los canales."""
    impares, pares = torch.split(x, [NI, x.shape[eje] - NI], dim=eje)
    return torch.cat([-impares, pares], dim=eje)


class B11(nn.Module):
    def __init__(self, entradas, canales):
        super().__init__()
        self.entrada = nn.Conv1d(entradas, canales, 1)
        self.bloques = nn.ModuleList([nn.Conv1d(canales, canales, secuencia.NUCLEO, padding=d, dilation=d)
                                      for d in secuencia.DILACIONES])
        self.salida = nn.Conv1d(canales, 1, 1)

    def g(self, x):
        h = self.entrada(x)
        for bloque in self.bloques:
            h = h + bloque(torch.relu(h))
        return self.salida(torch.relu(h))[:, 0]

    def forward(self, x):  # x (lote, canales, L)
        return 0.5 * (self.g(x) - self.g(espejo(x, 1)))

    def a_numpy(self):
        p = {"entrada_w": self.entrada.weight, "entrada_b": self.entrada.bias,
             "salida_w": self.salida.weight, "salida_b": self.salida.bias}
        for j, bloque in enumerate(self.bloques):
            p["bloque{}_w".format(j)] = bloque.weight
            p["bloque{}_b".format(j)] = bloque.bias
        return {k: v.detach().numpy().astype(np.float32) for k, v in p.items()}


class B12(nn.Module):
    """GRU bidireccional escrita como dos GRU de un sentido: la de atrás recorre cada parte invertida.

    Es lo mismo que `nn.GRU(bidirectional=True)` con cada secuencia en su largo, sin `pack_padded_sequence` (su
    paso hacia atrás es lentísimo en CPU). El relleno va al final y no toca a los frames de antes.
    """

    def __init__(self, entradas, oculto):
        super().__init__()
        self.delante = nn.GRU(entradas, oculto, batch_first=True)
        self.detras = nn.GRU(entradas, oculto, batch_first=True)
        self.salida = nn.Linear(2 * oculto, 1)

    def g(self, x5, invertir):
        delante, _ = self.delante(x5)
        idx = invertir[..., None].expand(-1, -1, x5.shape[2])
        detras, _ = self.detras(torch.gather(x5, 1, idx))
        detras = torch.gather(detras, 1, invertir[..., None].expand(-1, -1, detras.shape[2]))
        return self.salida(torch.cat([delante, detras], dim=2))[..., 0]

    def forward(self, x5, invertir):  # x5 (lote, T, canales)
        return 0.5 * (self.g(x5, invertir) - self.g(espejo(x5, 2), invertir))

    def a_numpy(self):
        a, b = self.delante, self.detras
        p = {"w_ih": a.weight_ih_l0, "b_ih": a.bias_ih_l0, "w_hh": a.weight_hh_l0, "b_hh": a.bias_hh_l0,
             "w_ih_r": b.weight_ih_l0, "b_ih_r": b.bias_ih_l0, "w_hh_r": b.weight_hh_l0, "b_hh_r": b.bias_hh_l0,
             "salida_w": self.salida.weight, "salida_b": self.salida.bias}
        return {k: v.detach().numpy().astype(np.float32) for k, v in p.items()}


def leer(partidos):
    """Secuencias (una por partido, condición y parte): canales (canales, L), etiqueta y máscara."""
    secuencias = []
    for partido in partidos:
        for condicion in comun.CONDICIONES:
            with np.load(comun.fichero_canales(partido, condicion)) as d:
                x, y, m, tramos = d["canales"], d["etiqueta"], d["mascara"], d["tramos"]
            for a, b in tramos:
                secuencias.append({"x": x[a:b].T.astype(np.float64), "y": y[a:b].astype(np.float32),
                                   "m": m[a:b], "partido": partido})
    return secuencias


def interpolacion(largo):
    """Índices y pesos de `secuencia.desagrupar`: z[t] = (1 − w)·z5[i0] + w·z5[i1]."""
    c = secuencia.centros(largo)
    t = np.arange(largo, dtype=np.float64)
    i0 = np.clip(np.searchsorted(c, t, side="right") - 1, 0, len(c) - 1)
    i1 = np.minimum(i0 + 1, len(c) - 1)
    hueco = np.where(i1 > i0, c[i1] - c[i0], 1.0)
    w = np.clip((t - c[i0]) / hueco, 0.0, 1.0)
    w[i1 == i0] = 0.0
    return i0, i1, w


def lote_b12(secuencias):
    """Tensores de B12: x5 rellenado al final, el índice que invierte cada secuencia en su largo, los índices y
    pesos de vuelta a 25 Hz, la etiqueta y la máscara."""
    x5 = [secuencia.agrupar(s["x"]).T for s in secuencias]
    largos = [len(v) for v in x5]
    largo_max, frames_max = max(largos), max(s["x"].shape[1] for s in secuencias)
    n = len(secuencias)
    X = np.zeros((n, largo_max, secuencia.N_CANALES), dtype=np.float32)
    I0 = np.zeros((n, frames_max), dtype=np.int64)
    I1 = np.zeros((n, frames_max), dtype=np.int64)
    W = np.zeros((n, frames_max), dtype=np.float32)
    Y = np.zeros((n, frames_max), dtype=np.float32)
    M = np.zeros((n, frames_max), dtype=np.float32)
    R = np.tile(np.arange(largo_max, dtype=np.int64), (n, 1))
    for k, s in enumerate(secuencias):
        X[k, :largos[k]] = x5[k]
        R[k, :largos[k]] = np.arange(largos[k] - 1, -1, -1)
        largo = s["x"].shape[1]
        i0, i1, w = interpolacion(largo)
        I0[k, :largo], I1[k, :largo], W[k, :largo] = i0, i1, w
        Y[k, :largo], M[k, :largo] = s["y"], s["m"]
    return (torch.from_numpy(X), torch.from_numpy(R), torch.from_numpy(I0), torch.from_numpy(I1),
            torch.from_numpy(W), torch.from_numpy(Y), torch.from_numpy(M))


def z_b12(modelo, X, R, I0, I1, W):
    z5 = modelo(X, R)
    return (1.0 - W) * torch.gather(z5, 1, I0) + W * torch.gather(z5, 1, I1)


def entrenar_b11(secuencias, semilla):
    cfg = comun.B11
    modelo = B11(secuencia.N_CANALES, cfg["canales"])
    opt = torch.optim.AdamW(modelo.parameters(), lr=cfg["tasa"], weight_decay=comun.DECAIMIENTO)
    rng = np.random.default_rng(semilla)
    validas = [s for s in secuencias if s["x"].shape[1] >= cfg["trozo"]]
    pesos = np.array([s["x"].shape[1] - cfg["trozo"] + 1 for s in validas], dtype=np.float64)
    pesos /= pesos.sum()
    margen = np.zeros(cfg["trozo"], dtype=np.float32)
    margen[cfg["margen"]:cfg["trozo"] - cfg["margen"]] = 1.0
    for paso in range(cfg["pasos"]):
        elegidas = rng.choice(len(validas), size=cfg["lote"], p=pesos)
        xs, ys, ms = [], [], []
        for k in elegidas:
            s = validas[k]
            a = int(rng.integers(0, s["x"].shape[1] - cfg["trozo"] + 1))
            xs.append(s["x"][:, a:a + cfg["trozo"]])
            ys.append(s["y"][a:a + cfg["trozo"]])
            ms.append(s["m"][a:a + cfg["trozo"]] * margen)
        x = torch.from_numpy(np.stack(xs).astype(np.float32))
        y, m = torch.from_numpy(np.stack(ys)), torch.from_numpy(np.stack(ms).astype(np.float32))
        perdida = (nn.functional.binary_cross_entropy_with_logits(modelo(x), y, reduction="none") * m).sum() \
            / m.sum().clamp(min=1.0)
        opt.zero_grad()
        perdida.backward()
        opt.step()
        if paso % 250 == 0 or paso == cfg["pasos"] - 1:
            print("  paso {} · pérdida {:.4f}".format(paso, float(perdida)), flush=True)
    return modelo


def entrenar_b12(secuencias, semilla):
    cfg = comun.B12
    modelo = B12(secuencia.N_CANALES, cfg["oculto"])
    opt = torch.optim.AdamW(modelo.parameters(), lr=cfg["tasa"], weight_decay=comun.DECAIMIENTO)
    # Todas las secuencias en cada paso, con el gradiente sumado en `TROZOS_B12` mitades: es el mismo gradiente
    # (salvo el redondeo) con la mitad de memoria; con todas a la vez no caben varios pliegues en 16 GB.
    mitades = [lote_b12(secuencias[k::TROZOS_B12]) for k in range(TROZOS_B12)]
    total = float(sum(float(m[6].sum()) for m in mitades))
    for paso in range(cfg["pasos"]):
        opt.zero_grad()
        perdida = 0.0
        for X, R, I0, I1, W, Y, M in mitades:
            z = z_b12(modelo, X, R, I0, I1, W)
            parte = (nn.functional.binary_cross_entropy_with_logits(z, Y, reduction="none") * M).sum() / total
            parte.backward()
            perdida += float(parte)
        opt.step()
        if paso % 25 == 0 or paso == cfg["pasos"] - 1:
            print("  paso {} · pérdida {:.4f}".format(paso, float(perdida)), flush=True)
    return modelo


def z_torch(nombre, modelo, s):
    """z por frame de una secuencia entera, con torch (float32)."""
    with torch.no_grad():
        if nombre == "b11":
            return modelo(torch.from_numpy(s["x"][None].astype(np.float32)))[0].numpy().astype(np.float64)
        X, R, I0, I1, W, _, _ = lote_b12([s])
        return z_b12(modelo, X, R, I0, I1, W)[0].numpy().astype(np.float64)


def acierto(nombre, modelo, secuencias):
    """(frames en la pérdida, aciertos, pérdida media) con z de torch."""
    total, bien, suma = 0, 0, 0.0
    for s in secuencias:
        z = z_torch(nombre, modelo, s)
        m = s["m"].astype(bool)
        y = s["y"][m]
        total += int(m.sum())
        bien += int(np.sum((z[m] > 0) == (y > 0.5)))
        suma += float(np.sum(np.logaddexp(0.0, z[m]) - y * z[m]))
    return total, bien, suma / max(total, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("modelo", choices=secuencia.MODELOS)
    parser.add_argument("pliegue", choices=comun.PLIEGUES)
    parser.add_argument("--fontaneria", action="store_true",
                        help="solo para probar el código: 3 pasos y los pesos en un fichero aparte, que nada lee")
    args = parser.parse_args()
    if args.fontaneria:
        comun.B11 = dict(comun.B11, pasos=3)
        comun.B12 = dict(comun.B12, pasos=3)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    semilla = comun.SEMILLA + comun.indice_pliegue(args.pliegue)
    torch.manual_seed(semilla)
    inicio = time.time()

    entrena = [p for p in comun.PARTIDOS if p != args.pliegue]
    secuencias = leer(entrena)
    dentro = np.concatenate([s["x"] for s in secuencias], axis=1)
    rms = np.sqrt(np.mean(dentro ** 2, axis=1))
    rms[rms == 0] = 1.0
    del dentro
    for s in secuencias:
        s["x"] = s["x"] / rms[:, None]
    print("{} · pliegue {} · {} secuencias · semilla {}".format(args.modelo, args.pliegue, len(secuencias), semilla),
          flush=True)
    modelo = (entrenar_b11 if args.modelo == "b11" else entrenar_b12)(secuencias, semilla)
    pesos = modelo.a_numpy()
    pesos["rms"] = rms.astype(np.float64)
    destino = comun.fichero_pesos(args.modelo, args.pliegue)
    if args.fontaneria:
        destino = destino.with_name("fontaneria_" + destino.name)
    destino.parent.mkdir(parents=True, exist_ok=True)
    np.savez(destino, **pesos)

    # Descriptivo: acierto por frame dentro del pliegue y fuera, y torch frente a numpy.
    total, bien, perdida = acierto(args.modelo, modelo, secuencias)
    linea = "acierto por frame (descriptivo): dentro {:.1f} % (pérdida {:.4f})".format(100.0 * bien / total, perdida)
    fuera = []
    if args.pliegue != "todos":
        fuera = leer([args.pliegue])
        for s in fuera:
            s["x"] = s["x"] / rms[:, None]
        total, bien, perdida = acierto(args.modelo, modelo, fuera)
        linea += " · fuera ({}) {:.1f} % (pérdida {:.4f})".format(args.pliegue, 100.0 * bien / total, perdida)
    print(linea)
    s = (fuera or secuencias)[0]
    p = {k: np.asarray(v, dtype=np.float64) for k, v in pesos.items()}
    z_np = (secuencia.logit_b11 if args.modelo == "b11" else secuencia.logit_b12)(s["x"], p)
    z_t = z_torch(args.modelo, modelo, s)
    print("torch frente a numpy en una parte de {} ({} frames): diferencia máxima de z {:.2e}, signo distinto en {} "
          "frames · {:.0f} s".format(s["partido"], len(z_np), float(np.max(np.abs(z_np - z_t))),
                                     int(np.sum(np.sign(z_np) != np.sign(z_t))), time.time() - inicio))


if __name__ == "__main__":
    main()
