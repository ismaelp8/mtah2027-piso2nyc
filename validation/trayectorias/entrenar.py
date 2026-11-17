"""Entrena B13 (red sobre trayectorias, possession/trayectorias.py) en un pliegue de la DFL, con torch en CPU.

    python validation/trayectorias/entrenar.py J03WMX      # el pliegue sin J03WMX (para el harness)
    python validation/trayectorias/entrenar.py todos       # el de los 7 (la entrega y SkillCorner)
    python validation/trayectorias/entrenar.py todos --fontaneria   # 3 pasos, a un fichero aparte

Hace falta torch (el entorno `mtah2027-balon`) y los rasgos de `exportar.py`. Datos abiertos de otros partidos (DFL,
CC BY 4.0): lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

- Los 6 partidos del pliegue (o los 7), con el balón de las dos condiciones que votan, como ejemplos aparte.
- Trozos de `TROZO` muestras (5 Hz), `LOTE` por paso, sorteados con semilla fija. Las `MARGEN` muestras de cada
  borde del trozo no cuentan en la pérdida.
- **Sin balón a trozos:** en la mitad de los trozos se apaga el balón (sus rasgos y los del jugador que dependen de
  él) en bloques de 5 a 20 s hasta tapar al menos el 25 % del trozo, para que la red aprenda a decidir sin él.
- Entropía cruzada sobre z a 25 Hz (interpolado como en la predicción) en los frames vivos donde el flag y control
  coinciden (1 si el flag es `H`).
- AdamW con tasa en coseno, recorte del gradiente a 1, `HILOS` hilos y semilla fija por pliegue.

Escribe los pesos en `comun.fichero_pesos("b13", pliegue)` (fuera del repo). Al final enseña, como descripción, el
acierto por frame dentro del pliegue y en el partido que quedó fuera, y la diferencia entre torch y numpy.
"""

import argparse
import math
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "validation", "secuencia"))
sys.path.insert(0, AQUI)
import comun  # noqa: E402  (pliegues, semilla y rutas de los pesos)
import rutas  # noqa: E402
from possession import trayectorias  # noqa: E402

CONDICIONES = comun.CONDICIONES
TROZO = 2000  # muestras (400 s)
LOTE = 6
MARGEN = 25  # muestras (5 s)
PASOS = 2000
TASA = 1e-3
TASA_FINAL = 5e-5
DECAIMIENTO = 1e-4
HILOS = 3
OCULTO_JUGADOR = 32
BALON = 16
MARCO = 48
GRU = 32
SIN_BALON_P = 0.5
SIN_BALON_TAPA = 0.25
SIN_BALON_BLOQUE = (25, 100)  # muestras (5 a 20 s)
NB = list(trayectorias.CANALES_DEL_BALON)


class B13(nn.Module):
    def __init__(self):
        super().__init__()
        nj, nb = trayectorias.N_JUGADOR, trayectorias.N_BALON
        self.propios1, self.propios2 = nn.Linear(nj, OCULTO_JUGADOR), nn.Linear(OCULTO_JUGADOR, OCULTO_JUGADOR)
        self.rivales1, self.rivales2 = nn.Linear(nj, OCULTO_JUGADOR), nn.Linear(OCULTO_JUGADOR, OCULTO_JUGADOR)
        self.balon = nn.Linear(nb, BALON)
        self.marco = nn.Linear(4 * OCULTO_JUGADOR + BALON + 2, MARCO)
        self.delante = nn.GRU(2 * MARCO, GRU, batch_first=True)
        self.detras = nn.GRU(2 * MARCO, GRU, batch_first=True)
        self.salida = nn.Linear(2 * GRU, 1)

    @staticmethod
    def conjunto(x, hay, l1, l2):
        h = torch.relu(l2(torch.relu(l1(x))))  # (B, T, S, O)
        m = hay.unsqueeze(-1)
        hm = h * m
        return torch.cat([hm.sum(2) / m.sum(2).clamp(min=1.0), hm.amax(2)], dim=-1)

    def incrustar(self, propios, rivales, balon, hay_p, hay_r):
        a = self.conjunto(propios, hay_p, self.propios1, self.propios2)
        b = self.conjunto(rivales, hay_r, self.rivales1, self.rivales2)
        c = torch.relu(self.balon(balon))
        n = torch.stack([hay_p.sum(2) / 11.0, hay_r.sum(2) / 11.0], dim=-1)
        return torch.relu(self.marco(torch.cat([a, b, c, n], dim=-1)))

    def g(self, x):  # x (B, T, 96), trozos sin relleno
        delante, _ = self.delante(x)
        detras, _ = self.detras(torch.flip(x, [1]))
        return self.salida(torch.cat([delante, torch.flip(detras, [1])], dim=-1))[..., 0]

    def forward(self, d):
        e_h = self.incrustar(d["H_propios"], d["H_rivales"], d["H_balon"], d["hay_h"], d["hay_a"])
        e_a = self.incrustar(d["A_propios"], d["A_rivales"], d["A_balon"], d["hay_a"], d["hay_h"])
        return 0.5 * (self.g(torch.cat([e_h, e_a], -1)) - self.g(torch.cat([e_a, e_h], -1)))

    def a_numpy(self):
        p = {}
        for nombre in ("propios1", "propios2", "rivales1", "rivales2", "balon", "marco"):
            capa = getattr(self, nombre)
            p[nombre + "_w"], p[nombre + "_b"] = capa.weight, capa.bias
        a, b = self.delante, self.detras
        p.update({"w_ih": a.weight_ih_l0, "b_ih": a.bias_ih_l0, "w_hh": a.weight_hh_l0, "b_hh": a.bias_hh_l0,
                  "w_ih_r": b.weight_ih_l0, "b_ih_r": b.bias_ih_l0, "w_hh_r": b.weight_hh_l0,
                  "b_hh_r": b.bias_hh_l0, "salida_w": self.salida.weight, "salida_b": self.salida.bias})
        return {k: v.detach().numpy().astype(np.float32) for k, v in p.items()}


def leer(partidos):
    """Una secuencia por partido, condición y parte: rasgos a 5 Hz (con los slots rellenados a `s`) y etiquetas."""
    crudas = []
    for partido in partidos:
        for condicion in CONDICIONES:
            with np.load(rutas.fichero(partido, condicion)) as d:
                k = 0
                while "{}_y".format(k) in d.files:
                    crudas.append({clave.split("_", 1)[1]: d[clave] for clave in d.files
                                   if clave.startswith("{}_".format(k))})
                    crudas[-1]["partido"] = partido
                    k += 1
    s = max(max(c["hay_h"].shape[1], c["hay_a"].shape[1]) for c in crudas)

    def rellenar(x):
        return np.concatenate([x, np.zeros(x.shape[:1] + (s - x.shape[1],) + x.shape[2:], x.dtype)], axis=1)

    for c in crudas:
        for clave in ("H_propios", "H_rivales", "A_propios", "A_rivales", "hay_h", "hay_a"):
            c[clave] = rellenar(c[clave])
    return crudas


def tensores(c, a, largo, sin_balon=None):
    """Los tensores de un trozo [a, a + largo) de una secuencia, con el balón apagado donde `sin_balon` es True."""
    d = {}
    for clave in ("H_propios", "H_rivales", "A_propios", "A_rivales", "H_balon", "A_balon"):
        x = c[clave][a:a + largo].astype(np.float32)
        if sin_balon is not None:
            x = x.copy()
            if clave.endswith("balon"):
                x[sin_balon] = 0.0
            else:
                x[np.ix_(np.flatnonzero(sin_balon), np.arange(x.shape[1]), NB)] = 0.0
        d[clave] = torch.from_numpy(x)
    for clave in ("hay_h", "hay_a"):
        d[clave] = torch.from_numpy(c[clave][a:a + largo].astype(np.float32))
    return d


def apilar(trozos):
    return {k: torch.stack([t[k] for t in trozos]) for k in trozos[0]}


def frames_del_trozo(largo):
    """Frames (relativos al trozo) que cuentan en la pérdida e interpolación: (f, i0, i1, w). Grupos de 5 enteros."""
    rep = trayectorias.representantes(5 * largo)
    f = np.arange(rep[MARGEN], rep[largo - 1 - MARGEN] + 1)
    i0 = np.searchsorted(rep, f, side="right") - 1
    i1 = np.minimum(i0 + 1, largo - 1)
    w = (f - rep[i0]) / np.maximum(rep[i1] - rep[i0], 1)
    return f, torch.from_numpy(i0), torch.from_numpy(i1), torch.from_numpy(w.astype(np.float32))


def sin_balon_al_azar(largo, rng):
    tapa = np.zeros(largo, bool)
    if rng.random() >= SIN_BALON_P:
        return tapa
    while tapa.mean() < SIN_BALON_TAPA:
        n = int(rng.integers(SIN_BALON_BLOQUE[0], SIN_BALON_BLOQUE[1] + 1))
        a = int(rng.integers(0, max(largo - n, 1)))
        tapa[a:a + n] = True
    return tapa


def entrenar(secuencias, semilla):
    modelo = B13()
    opt = torch.optim.AdamW(modelo.parameters(), lr=TASA, weight_decay=DECAIMIENTO)
    rng = np.random.default_rng(semilla)
    largos = np.array([len(c["H_balon"]) for c in secuencias])
    pesos = (largos - TROZO + 1).clip(min=0).astype(np.float64)
    pesos /= pesos.sum()
    f, i0, i1, w = frames_del_trozo(TROZO)
    for paso in range(PASOS):
        tasa = TASA_FINAL + 0.5 * (TASA - TASA_FINAL) * (1 + math.cos(math.pi * paso / PASOS))
        for grupo in opt.param_groups:
            grupo["lr"] = tasa
        trozos, ys, ms = [], [], []
        for k in rng.choice(len(secuencias), size=LOTE, p=pesos):
            c = secuencias[k]
            a = int(rng.integers(0, largos[k] - TROZO + 1))
            trozos.append(tensores(c, a, TROZO, sin_balon_al_azar(TROZO, rng)))
            ys.append(c["y"][5 * a + f])
            ms.append(c["m"][5 * a + f])
        z5 = modelo(apilar(trozos))
        z = (1.0 - w) * z5[:, i0] + w * z5[:, i1]
        y = torch.from_numpy(np.stack(ys).astype(np.float32))
        m = torch.from_numpy(np.stack(ms).astype(np.float32))
        perdida = (nn.functional.binary_cross_entropy_with_logits(z, y, reduction="none") * m).sum() \
            / m.sum().clamp(min=1.0)
        opt.zero_grad()
        perdida.backward()
        nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        opt.step()
        if paso % 100 == 0 or paso == PASOS - 1:
            print("  paso {} · pérdida {:.4f} · tasa {:.1e}".format(paso, float(perdida), tasa), flush=True)
    return modelo


def z_torch(modelo, c):
    """z a 25 Hz de una parte entera, con torch (la interpolación de `trayectorias.a_frames`)."""
    with torch.no_grad():
        z5 = modelo(apilar([tensores(c, 0, len(c["H_balon"]))]))[0].numpy().astype(np.float64)
    return trayectorias.a_frames(z5, len(c["y"]))


def acierto(modelo, secuencias):
    total, bien, suma = 0, 0, 0.0
    for c in secuencias:
        z = z_torch(modelo, c)
        m = c["m"].astype(bool)
        y = c["y"][m].astype(np.float64)
        total += int(m.sum())
        bien += int(np.sum((z[m] > 0) == (y > 0.5)))
        suma += float(np.sum(np.logaddexp(0.0, z[m]) - y * z[m]))
    return total, bien, suma / max(total, 1)


def main():
    global PASOS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pliegue", choices=comun.PLIEGUES)
    parser.add_argument("--fontaneria", action="store_true", help="3 pasos y los pesos a un fichero aparte")
    args = parser.parse_args()
    if args.fontaneria:
        PASOS = 3
    torch.set_num_threads(HILOS)
    semilla = comun.SEMILLA + 100 + comun.indice_pliegue(args.pliegue)
    torch.manual_seed(semilla)
    inicio = time.time()
    secuencias = leer([p for p in comun.PARTIDOS if p != args.pliegue])
    print("b13 · pliegue {} · {} secuencias · semilla {}".format(args.pliegue, len(secuencias), semilla), flush=True)
    modelo = entrenar(secuencias, semilla)
    pesos = modelo.a_numpy()
    destino = comun.fichero_pesos("b13", args.pliegue)
    if args.fontaneria:
        destino = destino.with_name("fontaneria_" + destino.name)
    destino.parent.mkdir(parents=True, exist_ok=True)
    np.savez(destino, **pesos)
    print("entrenado en {:.0f} s".format(time.time() - inicio), flush=True)

    total, bien, perdida = acierto(modelo, secuencias)
    linea = "acierto por frame (descriptivo): dentro {:.1f} % (pérdida {:.4f})".format(100.0 * bien / total, perdida)
    fuera = []
    if args.pliegue != "todos":
        fuera = leer([args.pliegue])
        total, bien, perdida = acierto(modelo, fuera)
        linea += " · fuera ({}) {:.1f} % (pérdida {:.4f})".format(args.pliegue, 100.0 * bien / total, perdida)
    print(linea)
    c = (fuera or secuencias)[0]
    p = {k: np.asarray(v, dtype=np.float64) for k, v in pesos.items()}
    rasgos = {0: tuple(c[k].astype(np.float64) for k in ("H_propios", "H_rivales", "H_balon")),
              1: tuple(c[k].astype(np.float64) for k in ("A_propios", "A_rivales", "A_balon"))}
    z_np = trayectorias.a_frames(trayectorias.logit_muestras(rasgos, c["hay_h"], c["hay_a"], p), len(c["y"]))
    z_t = z_torch(modelo, c)
    print("torch frente a numpy en una parte de {}: diferencia máxima de z {:.2e}, signo distinto en {} frames · "
          "{:.0f} s".format(c["partido"], float(np.max(np.abs(z_np - z_t))),
                            int(np.sum(np.sign(z_np) != np.sign(z_t))), time.time() - inicio))


if __name__ == "__main__":
    main()
