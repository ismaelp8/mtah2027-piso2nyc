"""Entrena B14 (red de trayectorias, segunda versión: possession/trayectorias2.py) en un pliegue de la DFL.

    python validation/trayectorias/entrenar2.py J03WMX     # el pliegue sin J03WMX (para el harness)
    python validation/trayectorias/entrenar2.py todos      # el de los 7 (la entrega y SkillCorner)
    python validation/trayectorias/entrenar2.py todos --fontaneria
    python validation/trayectorias/entrenar2.py J03WMX --control  # B15: la etiqueta de control en todos los vivos
    python validation/trayectorias/entrenar2.py J03WMX --skillcorner   # B16: B15 más SkillCorner ENTRENAMIENTO
    python validation/trayectorias/entrenar2.py scA --skillcorner      # B16 sin la mitad A de SkillCorner (comprobación)

Hace falta torch (el entorno `mtah2027-balon`) y los rasgos de `exportar2.py`. Datos abiertos de otros partidos (DFL,
CC BY 4.0): lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.

Como `entrenar.py` (B13), con:
- las tres copias de cada partido y condición (el harness y dos con dominio aleatorizado como el ATD);
- los presentes de cada frame empaquetados al principio y en float16 (`paquetes.py`), abiertos con memmap para que
  quepan varios pliegues a la vez (la red no depende del orden de los slots);
- además del balón apagado a trozos, un espejo en y en la mitad de los trozos;
- la atención conjunta de `trayectorias2.incrustar`.
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
import comun  # noqa: E402
sys.path.insert(0, AQUI)  # comun pone validation/apuesta_b delante, que también tiene un entrenar.py
import entrenar as b13  # noqa: E402  (frames_del_trozo, apilar, la tasa y las constantes del trozo)
import paquetes  # noqa: E402
import rutas  # noqa: E402
from possession import trayectorias, trayectorias2  # noqa: E402

COPIAS = (0, 1, 2)
PASOS = 2500
ESPEJO_P = 0.5
NB = list(trayectorias2.CANALES_DEL_BALON)
CLAVES = ("H_propios", "H_rivales", "A_propios", "A_rivales", "H_balon", "A_balon")


def fichero(partido, condicion, copia):
    return rutas.carpeta() / "rasgos2_{}_{}_c{}.npz".format(partido, rutas.CONDICIONES.index(condicion), copia)


class B14(nn.Module):
    def __init__(self):
        super().__init__()
        nj, nb, o = trayectorias2.N_JUGADOR, trayectorias2.N_BALON, b13.OCULTO_JUGADOR
        self.propios1, self.propios2 = nn.Linear(nj, o), nn.Linear(o, o)
        self.rivales1, self.rivales2 = nn.Linear(nj, o), nn.Linear(o, o)
        self.atp, self.atr = nn.Linear(o, 1), nn.Linear(o, 1)
        self.balon = nn.Linear(nb, b13.BALON)
        self.marco = nn.Linear(6 * o + b13.BALON + 3, b13.MARCO)
        self.delante = nn.GRU(2 * b13.MARCO, b13.GRU, batch_first=True)
        self.detras = nn.GRU(2 * b13.MARCO, b13.GRU, batch_first=True)
        self.salida = nn.Linear(2 * b13.GRU, 1)

    def incrustar(self, propios, rivales, balon, hay_p, hay_r):
        hp = torch.relu(self.propios2(torch.relu(self.propios1(propios))))
        hr = torch.relu(self.rivales2(torch.relu(self.rivales1(rivales))))
        s = torch.cat([self.atp(hp)[..., 0], self.atr(hr)[..., 0]], dim=-1)
        m = torch.cat([hay_p, hay_r], dim=-1)
        alguno = m.sum(-1, keepdim=True) > 0
        s = torch.where(alguno, s.masked_fill(m == 0, float("-inf")), torch.zeros_like(s))
        w = torch.softmax(s, dim=-1) * m
        w = w / w.sum(-1, keepdim=True).clamp(min=1e-30)
        sp = hay_p.shape[-1]
        wp, wr = w[..., :sp], w[..., sp:]
        partes = []
        for h, mm, ww in ((hp, hay_p, wp), (hr, hay_r, wr)):
            hm = h * mm.unsqueeze(-1)
            partes += [hm.sum(-2) / mm.sum(-1, keepdim=True).clamp(min=1.0), hm.amax(-2),
                       (h * ww.unsqueeze(-1)).sum(-2)]
        c = torch.relu(self.balon(balon))
        n = torch.stack([wp.sum(-1), hay_p.sum(-1) / 11.0, hay_r.sum(-1) / 11.0], dim=-1)
        return torch.relu(self.marco(torch.cat(partes + [c, n], dim=-1)))

    def g(self, x):
        delante, _ = self.delante(x)
        detras, _ = self.detras(torch.flip(x, [1]))
        return self.salida(torch.cat([delante, torch.flip(detras, [1])], dim=-1))[..., 0]

    def forward(self, d):
        e_h = self.incrustar(d["H_propios"], d["H_rivales"], d["H_balon"], d["hay_h"], d["hay_a"])
        e_a = self.incrustar(d["A_propios"], d["A_rivales"], d["A_balon"], d["hay_a"], d["hay_h"])
        return 0.5 * (self.g(torch.cat([e_h, e_a], -1)) - self.g(torch.cat([e_a, e_h], -1)))

    def a_numpy(self):
        p = {}
        for nombre in ("propios1", "propios2", "rivales1", "rivales2", "atp", "atr", "balon", "marco"):
            capa = getattr(self, nombre)
            p[nombre + "_w"], p[nombre + "_b"] = capa.weight, capa.bias
        a, b = self.delante, self.detras
        p.update({"w_ih": a.weight_ih_l0, "b_ih": a.bias_ih_l0, "w_hh": a.weight_hh_l0, "b_hh": a.bias_hh_l0,
                  "w_ih_r": b.weight_ih_l0, "b_ih_r": b.bias_ih_l0, "w_hh_r": b.weight_hh_l0,
                  "b_hh_r": b.bias_hh_l0, "salida_w": self.salida.weight, "salida_b": self.salida.bias})
        return {k: v.detach().numpy().astype(np.float32) for k, v in p.items()}


def leer(partidos, copias=COPIAS):
    """Las secuencias empaquetadas por `paquetes.py`, abiertas con memmap (los procesos comparten la caché)."""
    crudas = []
    for partido in partidos:
        for condicion in rutas.CONDICIONES:
            for copia in copias:
                k = 0
                while paquetes.nombre(partido, condicion, copia, k, "y").exists():
                    c = {clave: np.load(paquetes.nombre(partido, condicion, copia, k, clave), mmap_mode="r")
                         for clave in paquetes.CLAVES}
                    c["partido"], c["copia"], c["parte"] = partido, copia, k
                    crudas.append(c)
                    k += 1
    if not crudas:
        raise FileNotFoundError("no hay paquetes: python validation/trayectorias/paquetes.py")
    return crudas


# B16: las dos mitades de SkillCorner ENTRENAMIENTO para la validación cruzada (`exportar_sc.py`). «scA» se entrena con
# la DFL entera y la mitad B, y se comprueba en la A; «scB», al revés. Los pliegues de la DFL usan las 10.
SC_ENTRENAMIENTO = (1874553, 1899585, 1927964, 1959846, 1996435, 2006229, 2007448, 2010085, 2013725, 2016236)
SC_MITADES = {"scA": SC_ENTRENAMIENTO[:5], "scB": SC_ENTRENAMIENTO[5:]}
SC_CONDICIONES = ("detectado", "detectado, suavizado")


def nombre_sc(id_, condicion, parte, clave):
    return paquetes.carpeta() / "sc_{}_{}_{}_{}.npy".format(id_, SC_CONDICIONES.index(condicion), parte, clave)


def leer_sc(ids):
    """Las secuencias de SkillCorner de `exportar_sc.py` (etiquetas de SkillCorner en todos los vivos), con memmap."""
    crudas = []
    for id_ in ids:
        for condicion in SC_CONDICIONES:
            k = 0
            while nombre_sc(id_, condicion, k, "y").exists():
                c = {clave: np.load(nombre_sc(id_, condicion, k, clave), mmap_mode="r") for clave in paquetes.CLAVES}
                c["partido"], c["copia"], c["parte"] = "sc{}".format(id_), 0, k
                crudas.append(c)
                k += 1
    if not crudas:
        raise FileNotFoundError("no hay rasgos de SkillCorner: python validation/trayectorias/exportar_sc.py")
    return crudas


def con_control(secuencias):
    """B15: la etiqueta (1 si control dice `H`) y la máscara (frames vivos con control) de `etiquetas_control.py`."""
    for c in secuencias:
        c["y"] = np.load(paquetes.nombre_control(c["partido"], c["parte"], "y"))
        c["m"] = np.load(paquetes.nombre_control(c["partido"], c["parte"], "m"))


def rellenar_a(x, s):
    """Rellena con ceros la dimensión de los slots (la 1) hasta `s`."""
    if x.shape[1] >= s:
        return x
    return np.concatenate([x, np.zeros((x.shape[0], s - x.shape[1]) + x.shape[2:], x.dtype)], axis=1)


SLOTS = {"s": 0}  # el máximo de slots de las secuencias del pliegue (lo fija `main`)


def tensores(c, a, largo, sin_balon=None, espejo=False):
    d = {}
    for clave in CLAVES:
        x = c[clave][a:a + largo].astype(np.float32)
        if not clave.endswith("balon"):
            x = rellenar_a(x, SLOTS["s"])
        if clave.endswith("balon"):
            if sin_balon is not None:
                x[sin_balon] = 0.0
            if espejo:
                x[:, list(trayectorias2.ESPEJO_BALON)] *= -1.0
        else:
            if sin_balon is not None and sin_balon.any():
                x[np.ix_(np.flatnonzero(sin_balon), np.arange(x.shape[1]), NB)] = 0.0
            if espejo:
                x[:, :, list(trayectorias2.ESPEJO_JUGADOR)] *= -1.0
        d[clave] = torch.from_numpy(x + 0.0)
    for clave in ("hay_h", "hay_a"):
        d[clave] = torch.from_numpy(rellenar_a(c[clave][a:a + largo].astype(np.float32), SLOTS["s"]))
    return d


def entrenar(secuencias, semilla):
    modelo = B14()
    opt = torch.optim.AdamW(modelo.parameters(), lr=b13.TASA, weight_decay=b13.DECAIMIENTO)
    rng = np.random.default_rng(semilla)
    largos = np.array([len(c["H_balon"]) for c in secuencias])
    pesos = (largos - b13.TROZO + 1).clip(min=0).astype(np.float64)
    pesos /= pesos.sum()
    f, i0, i1, w = b13.frames_del_trozo(b13.TROZO)
    for paso in range(PASOS):
        tasa = b13.TASA_FINAL + 0.5 * (b13.TASA - b13.TASA_FINAL) * (1 + math.cos(math.pi * paso / PASOS))
        for grupo in opt.param_groups:
            grupo["lr"] = tasa
        trozos, ys, ms = [], [], []
        for k in rng.choice(len(secuencias), size=b13.LOTE, p=pesos):
            c = secuencias[k]
            a = int(rng.integers(0, largos[k] - b13.TROZO + 1))
            trozos.append(tensores(c, a, b13.TROZO, b13.sin_balon_al_azar(b13.TROZO, rng), rng.random() < ESPEJO_P))
            ys.append(c["y"][5 * a + f])
            ms.append(c["m"][5 * a + f])
        z5 = modelo(b13.apilar(trozos))
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
            print("  paso {} · pérdida {:.4f} · tasa {:.1e}".format(paso, float(perdida.detach()), tasa), flush=True)
    return modelo


def z_torch(modelo, c):
    with torch.no_grad():
        z5 = modelo(b13.apilar([tensores(c, 0, len(c["H_balon"]))]))[0].numpy().astype(np.float64)
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
    parser.add_argument("pliegue", choices=comun.PLIEGUES + tuple(SC_MITADES))
    parser.add_argument("--fontaneria", action="store_true", help="3 pasos y los pesos a un fichero aparte")
    parser.add_argument("--hilos", type=int, default=b13.HILOS, help="hilos de torch (solo cambia la velocidad)")
    parser.add_argument("--control", action="store_true",
                        help="B15: entrena con la etiqueta de control en todos los frames vivos (etiquetas_control.py)")
    parser.add_argument("--skillcorner", action="store_true",
                        help="B16: B15 (control) más SkillCorner ENTRENAMIENTO (exportar_sc.py), con scA y scB")
    args = parser.parse_args()
    if args.skillcorner:
        args.control = True
    if args.pliegue in SC_MITADES and not args.skillcorner:
        raise SystemExit("scA y scB son pliegues de B16: hace falta --skillcorner")
    modelo_nombre = "b16" if args.skillcorner else "b15" if args.control else "b14"
    if args.fontaneria:
        PASOS = 3
    torch.set_num_threads(args.hilos)
    indice = comun.indice_pliegue(args.pliegue) if args.pliegue in comun.PLIEGUES else 8 + list(SC_MITADES).index(args.pliegue)
    semilla = comun.SEMILLA + (400 if args.skillcorner else 300 if args.control else 200) + indice
    torch.manual_seed(semilla)
    inicio = time.time()
    secuencias = leer([p for p in comun.PARTIDOS if p != args.pliegue])
    if args.control:
        con_control(secuencias)
    if args.skillcorner:
        fuera_sc = SC_MITADES.get(args.pliegue, ())
        secuencias += leer_sc([i for i in SC_ENTRENAMIENTO if i not in fuera_sc])
    SLOTS["s"] = max(max(c["hay_h"].shape[1], c["hay_a"].shape[1]) for c in secuencias)
    print(modelo_nombre + " · pliegue {} · {} secuencias · {} slots tras empaquetar · semilla {}".format(
        args.pliegue, len(secuencias), secuencias[0]["hay_h"].shape[1], semilla), flush=True)
    modelo = entrenar(secuencias, semilla)
    pesos = modelo.a_numpy()
    destino = comun.fichero_pesos(modelo_nombre, args.pliegue)
    if args.fontaneria:
        destino = destino.with_name("fontaneria_" + destino.name)
    destino.parent.mkdir(parents=True, exist_ok=True)
    np.savez(destino, **pesos)
    print("entrenado en {:.0f} s".format(time.time() - inicio), flush=True)

    dentro = [c for c in secuencias if c["copia"] == 0]
    total, bien, perdida = acierto(modelo, dentro)
    linea = "acierto por frame (descriptivo, copia 0): dentro {:.1f} % (pérdida {:.4f})".format(
        100.0 * bien / total, perdida)
    fuera = []
    if args.pliegue in SC_MITADES:
        fuera = leer_sc(SC_MITADES[args.pliegue])
    elif args.pliegue != "todos":
        fuera = leer([args.pliegue], copias=(0,))
        if args.control:
            con_control(fuera)
    if fuera:
        total, bien, perdida = acierto(modelo, fuera)
        linea += " · fuera ({}) {:.1f} % (pérdida {:.4f})".format(args.pliegue, 100.0 * bien / total, perdida)
    print(linea)
    c = (fuera or dentro)[0]
    p = {k: np.asarray(v, dtype=np.float64) for k, v in pesos.items()}
    rasgos = {0: tuple(c[k].astype(np.float64) for k in ("H_propios", "H_rivales", "H_balon")),
              1: tuple(c[k].astype(np.float64) for k in ("A_propios", "A_rivales", "A_balon"))}
    z_np = trayectorias.a_frames(trayectorias2.logit_muestras(rasgos, c["hay_h"], c["hay_a"], p), len(c["y"]))
    z_t = z_torch(modelo, c)
    print("torch frente a numpy en una parte de {}: diferencia máxima de z {:.2e}, signo distinto en {} frames · "
          "{:.0f} s".format(c["partido"], float(np.max(np.abs(z_np - z_t))),
                            int(np.sum(np.sign(z_np) != np.sign(z_t))), time.time() - inicio))


if __name__ == "__main__":
    main()
