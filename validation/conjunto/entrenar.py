"""Entrena el modelo conjunto en un pliegue, con torch (GPU o CPU), y guarda sus salidas fuera de muestra.

    python validation/conjunto/entrenar.py J03WMX     # el pliegue sin J03WMX y sin sus dos partidos de SkillCorner
    python validation/conjunto/entrenar.py todos      # el de los 17 partidos (la entrega y el examen)
    python validation/conjunto/entrenar.py todos --solo sc --etiqueta solo_sc   # solo SkillCorner: se puntúa en la DFL
    python validation/conjunto/entrenar.py todos --solo dfl --etiqueta r_solo_dfl --dispositivo cpu   # sin GPU

Hace falta el entorno `mtah2027-conjunto` (torch con CUDA) y la caché de `exportar.py`. Con `--dispositivo cpu`
(17/11, «dos refinamientos de K2 sin reentrenar») vale cualquier torch: es el mismo entrenamiento, más lento y con
otros números al azar, porque el generador de la CPU no es el de la GPU. Datos abiertos de otros
partidos (DFL, CC BY 4.0; SkillCorner, MIT): lo puede ejecutar cualquiera, Claude incluido. Solo imprime agregados.
**No lee el examen de SkillCorner:** la lista de partidos es `cj_comun.SKILLCORNER`, la mitad de entrenamiento.

Lo que hace es lo fijado en docs/decisiones.md (17/11, «modelo conjunto»): trozos de 512 grupos (5 Hz), mitad de la
DFL y mitad de SkillCorner, con los aumentos hacia el ATD; entropía cruzada de z y de los cambios con las etiquetas
de control (en SkillCorner, las suyas) y del auxiliar con el flag; AdamW, pasos fijos y semilla fija, sin parada
temprana. Al final escribe los pesos y, para los partidos que el pliegue no vio, z y las probabilidades de cambio a
25 Hz (`cj_comun.fichero_salida`), con cada balón que mide el harness.

Con `--solo dfl` o `--solo sc` (comprobación del 17/11, «el otro proveedor») entrena con los partidos de un solo
proveedor y guarda las salidas de todos los del otro, que no ha visto.
"""

import argparse
import json
import math
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

import cj_comun as cj
import red

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SLOTS = 48  # columnas por partido en el dispositivo; la última queda libre para el slot duplicado
CONFIG = {
    "pasos": 3000, "lote": 32, "grupos": 512, "margen": 64, "tasa": 2e-3, "decaimiento": 1e-4, "calentamiento": 100,
    "peso_cambios": 1.0, "peso_flag": 0.3,
    "oculto": 32, "canales": 40, "dilaciones": (1, 2, 4, 8, 16, 32), "abandono": 0.1,
    # aumentos hacia el ATD, por trozo
    "retraso_max": 5, "p_hueco": 0.3, "hueco": (25, 100), "p_falta": 0.06, "p_rato": 0.10, "rato": (25, 125),
    "p_duplicado": 0.25, "sigma_duplicado": 0.4, "p_a_la_vista": 0.5,
    # aumentos hacia un tracking automático, solo en los trozos de la DFL (ronda K2r). Apagados por defecto: con estos
    # valores el entrenamiento es el de K2.
    "visibilidad_min": 1.0, "p_10hz": 0.0, "p_ruido": 0.0, "sigma_ruido": 0.2,
}
# La única configuración de la ronda K2r (docs/decisiones.md, 17/11, «una ronda contra el cambio de proveedor»).
ROBUSTO = {"visibilidad_min": 0.65, "p_10hz": 0.5, "p_ruido": 0.5}
HZ_ORIGEN = 10.0  # la frecuencia de SkillCorner, que su lector pasa a 25 fps por interpolación


def clases(gt, semiancho=cj.SEMIANCHO):
    """Como `validation/cambios/comun.clases`: 1 «hacia H» y 2 «hacia A» a `semiancho` frames o menos de un cambio
    directo (el más cercano; en el empate, el primero), 0 en el resto de los vivos y −1 fuera del juego."""
    n = len(gt)
    vivo = gt < 2
    frames = np.flatnonzero(vivo[1:] & vivo[:-1] & (gt[1:] != gt[:-1])) + 1
    clase = np.zeros(n, dtype=np.int8)
    lejos = np.full(n, np.iinfo(np.int32).max, dtype=np.int64)
    for t in frames:
        a, b = max(0, t - semiancho), min(n, t + semiancho + 1)
        dist = np.abs(np.arange(a, b) - t)
        gana = dist < lejos[a:b]
        clase[a:b][gana] = 1 + int(gt[t])
        lejos[a:b][gana] = dist[gana]
    clase[~vivo] = -1
    return clase, frames, gt[frames]


def calidad(p, clase, frames, hacia, umbral=0.5):
    """La medida de `validation/cambios/medir.calidad`: (cambios reales, vistos, avisos, buenos, frames vivos)."""
    s = cj.SEMIANCHO
    vistos = sum(bool((p[max(0, t - s):t + s + 1, x] >= umbral).any()) for t, x in zip(frames, hacia))
    avisos = buenos = 0
    for x in (0, 1):
        alto = p[:, x] >= umbral
        bordes = np.flatnonzero(np.diff(np.concatenate(([0], alto.astype(np.int8), [0]))))
        for a, b in zip(bordes[0::2], bordes[1::2]):
            avisos += 1
            buenos += bool((clase[a:b] == 1 + x).any())
    return np.array([len(frames), vistos, avisos, buenos, int(np.sum(clase >= 0))])


def cargar(dominio, partido, device, columnas=SLOTS):
    """Un partido de la caché, en el dispositivo, con las columnas de slots rellenadas hasta `columnas`."""
    with np.load(cj.fichero_partido(dominio, partido)) as d:
        datos = {k: d[k] for k in d.files}
    n, slots = datos["px"].shape
    if slots >= columnas:
        raise ValueError("{} slots no caben en {} columnas con una libre".format(slots, columnas))
    relleno = np.full((n, columnas - slots), np.nan, dtype=np.float32)
    team = np.concatenate((datos["team"].astype(np.int64), np.full(columnas - slots, -1, dtype=np.int64)))
    blocks = [(int(a), int(b)) for a, b in datos["blocks"]]
    direccion = []
    for a, b in blocks:  # el local ataca hacia donde está, en media, el visitante (aprendida._rasgos_forma)
        x = datos["px"][a:b].astype(np.float64)
        media = [np.nanmean(x[:, datos["team"] == e]) for e in (0, 1)]
        direccion.append(float(np.sign(media[1] - media[0])))
    gt = datos["gt_control"].astype(np.int64)
    clase, frames, hacia = clases(gt)
    balones = [(datos["bx_{}".format(j)], datos["by_{}".format(j)]) for j in (0, 1)]
    if dominio == "dfl":
        balones += [(datos["bxd_{}".format(j)], datos["byd_{}".format(j)]) for j in (0, 1)]
    a_gpu = lambda v, tipo=torch.float32: torch.as_tensor(v, dtype=tipo, device=device)  # noqa: E731
    return {
        "dominio": dominio, "partido": partido, "n": n, "blocks": blocks, "direccion": direccion,
        "largo": float(datos["pitch"][0]), "ancho": float(datos["pitch"][1]),
        "px": a_gpu(np.concatenate((datos["px"], relleno), axis=1)),
        "py": a_gpu(np.concatenate((datos["py"], relleno), axis=1)),
        "team": a_gpu(team, torch.int64),
        "balones": [(a_gpu(x), a_gpu(y)) for x, y in balones],
        "gt": a_gpu(gt, torch.int64), "clase": a_gpu(clase, torch.int64),
        "flag": a_gpu(datos["gt_flag"], torch.int64) if "gt_flag" in datos else None,
        "np": {"gt": gt, "clase": clase, "frames": frames, "hacia": hacia},
    }


def recorte(valores, lo, hi, a, b):
    """valores[lo:hi], con NaN en la parte que cae fuera del tramo [a, b)."""
    dentro = valores[max(lo, a):min(hi, b)]
    antes, despues = max(a - lo, 0), max(hi - b, 0)
    if not antes and not despues:
        return dentro
    relleno = (0, 0) * (dentro.dim() - 1) + (antes, despues)
    return F.pad(dentro, relleno, value=float("nan"))


def lote_de(partidos, rng, cfg, device):
    """Un lote de trozos de `partidos` (lista de (partido cargado, cuántos trozos))."""
    grupos = cfg["grupos"]
    frames = grupos * cj.GRUPO
    p = red.PASO_VEL
    campos = {k: [] for k in ("px", "py", "bx", "by", "team", "direccion", "largo", "ancho", "gt", "clase", "flag",
                              "con_flag", "es_dfl")}
    for m, cuantos in partidos:
        largos = np.array([b - a for a, b in m["blocks"]], dtype=np.float64)
        for _ in range(cuantos):
            k = int(rng.choice(len(largos), p=largos / largos.sum()))
            a, b = m["blocks"][k]
            t0 = a + cj.GRUPO * int(rng.integers(0, (b - a) // cj.GRUPO - grupos + 1))
            j = int(rng.integers(0, 2))
            if m["dominio"] == "dfl" and rng.random() < cfg["p_a_la_vista"]:
                j += 2
            retraso = int(rng.integers(0, cfg["retraso_max"] + 1))
            bx, by = m["balones"][j]
            campos["px"].append(recorte(m["px"], t0 - p, t0 + frames + p, a, b))
            campos["py"].append(recorte(m["py"], t0 - p, t0 + frames + p, a, b))
            campos["bx"].append(recorte(bx, t0 - p - retraso, t0 + frames + p - retraso, a, b))
            campos["by"].append(recorte(by, t0 - p - retraso, t0 + frames + p - retraso, a, b))
            campos["team"].append(m["team"])
            campos["direccion"].append(m["direccion"][k])
            campos["largo"].append(m["largo"])
            campos["ancho"].append(m["ancho"])
            centros = slice(t0 + cj.GRUPO // 2, t0 + frames, cj.GRUPO)
            campos["gt"].append(m["gt"][centros])
            campos["clase"].append(m["clase"][centros])
            campos["flag"].append(m["flag"][centros] if m["flag"] is not None
                                  else torch.full((grupos,), 3, dtype=torch.int64, device=device))
            campos["con_flag"].append(m["flag"] is not None)
            campos["es_dfl"].append(m["dominio"] == "dfl")
    salida = {k: torch.stack(v) for k, v in campos.items() if k in ("px", "py", "bx", "by", "team", "gt", "clase",
                                                                    "flag")}
    for k in ("direccion", "largo", "ancho"):
        salida[k] = torch.tensor(campos[k], dtype=torch.float32, device=device)
    salida["es_dfl"] = torch.tensor(campos["es_dfl"], dtype=torch.bool, device=device)
    return salida


def aumentar(lote, cfg, gen):
    """Los aumentos hacia el ATD, sobre el lote crudo (en el sitio). Los sortea `gen`, con semilla fija."""
    px, py, bx, by, team = lote["px"], lote["py"], lote["bx"], lote["by"], lote["team"].clone()
    n, frames, slots = px.shape
    device = px.device
    nan = float("nan")

    def azar(*forma):
        return torch.rand(*forma, generator=gen, device=device)

    def entero(bajo, alto, *forma):
        return torch.randint(bajo, alto + 1, forma, generator=gen, device=device)

    # el campo en espejo (y → ancho − y)
    espejo = azar(n) < 0.5
    ancho = lote["ancho"]
    py = torch.where(espejo[:, None, None], ancho[:, None, None] - py, py)
    by = torch.where(espejo[:, None], ancho[:, None] - by, by)
    # un slot duplicado en la última columna, que está libre
    duplicado = azar(n) < cfg["p_duplicado"]
    origen = torch.multinomial((team >= 0).float(), 1, generator=gen)[:, 0]
    filas = torch.arange(n, device=device)
    ruido = torch.randn(n, 2, generator=gen, device=device) * cfg["sigma_duplicado"]
    px[:, :, slots - 1] = torch.where(duplicado[:, None], px[filas, :, origen] + ruido[:, :1], nan)
    py[:, :, slots - 1] = torch.where(duplicado[:, None], py[filas, :, origen] + ruido[:, 1:], nan)
    team[:, slots - 1] = torch.where(duplicado, team[filas, origen], -1)
    t = torch.arange(frames, device=device)
    es_dfl = lote["es_dfl"]
    # datos a 10 Hz (solo en trozos de la DFL): se remuestrea a 10 Hz y se interpola de vuelta, como hace el lector de
    # SkillCorner; con una de las dos muestras ausente, el valor falta
    if cfg["p_10hz"] > 0:
        elegido = es_dfl & (azar(n) < cfg["p_10hz"])
        paso = 25.0 / HZ_ORIGEN
        muestras = int((frames - 1) / paso) + 1
        instante = torch.arange(muestras, device=device) * paso
        bajo = instante.floor().long()
        alto = (bajo + 1).clamp(max=frames - 1)
        peso = instante - bajo
        vuelta = t / paso
        antes = vuelta.floor().long().clamp(max=muestras - 1)
        despues = (antes + 1).clamp(max=muestras - 1)
        peso_vuelta = vuelta - antes

        def a_10hz(valores):  # valores (n, frames, ...) -> lo mismo, pasado por 10 Hz
            forma = (1, -1) + (1,) * (valores.dim() - 2)
            w = peso.view(forma)
            lento = torch.where(w < 1e-6, valores[:, bajo], (1.0 - w) * valores[:, bajo] + w * valores[:, alto])
            w = peso_vuelta.view(forma)
            exacto = (w < 1e-6) | (despues == antes).view(forma)
            return torch.where(exacto, lento[:, antes], (1.0 - w) * lento[:, antes] + w * lento[:, despues])

        px = torch.where(elegido[:, None, None], a_10hz(px), px)
        py = torch.where(elegido[:, None, None], a_10hz(py), py)
        bx = torch.where(elegido[:, None], a_10hz(bx), bx)
        by = torch.where(elegido[:, None], a_10hz(by), by)
    # ruido lento de posición (solo en trozos de la DFL): un desplazamiento por jugador que cambia cada segundo
    if cfg["p_ruido"] > 0:
        elegido = es_dfl & (azar(n) < cfg["p_ruido"])
        nudos = frames // 25 + 2
        valor = torch.randn(n, nudos, slots, 2, generator=gen, device=device) * cfg["sigma_ruido"]
        u = t / 25.0
        i0 = u.floor().long()
        w = (u - i0).view(1, -1, 1, 1)
        desplazamiento = (1.0 - w) * valor[:, i0] + w * valor[:, i0 + 1]
        desplazamiento = desplazamiento * elegido[:, None, None, None]
        px, py = px + desplazamiento[..., 0], py + desplazamiento[..., 1]
    # slots que faltan todo el trozo o un rato
    falta = azar(n, slots) < cfg["p_falta"]
    if cfg["visibilidad_min"] < 1.0:  # jugadores que faltan como en SkillCorner (solo en trozos de la DFL)
        se_ven = cfg["visibilidad_min"] + (1.0 - cfg["visibilidad_min"]) * azar(n)
        falta = falta | (es_dfl[:, None] & (azar(n, slots) < (1.0 - se_ven)[:, None]))
    rato = azar(n, slots) < cfg["p_rato"]
    inicio = entero(0, frames - 1, n, slots)
    largo = entero(cfg["rato"][0], cfg["rato"][1], n, slots)
    fuera = falta[:, None, :] | (rato[:, None, :] & (t[None, :, None] >= inicio[:, None, :])
                                 & (t[None, :, None] < (inicio + largo)[:, None, :]))
    px, py = torch.where(fuera, nan, px), torch.where(fuera, nan, py)
    # un hueco más de balón
    hueco = azar(n) < cfg["p_hueco"]
    inicio = entero(0, frames - 1, n)
    largo = entero(cfg["hueco"][0], cfg["hueco"][1], n)
    tapado = hueco[:, None] & (t[None, :] >= inicio[:, None]) & (t[None, :] < (inicio + largo)[:, None])
    bx, by = torch.where(tapado, nan, bx), torch.where(tapado, nan, by)
    lote.update(px=px, py=py, bx=bx, by=by, team=team)
    return lote


def signo_de(team, direccion):
    """+1 si el slot ataca hacia x creciente, −1 si hacia x decreciente, 0 en las columnas vacías."""
    lado = torch.where(team == 0, 1.0, torch.where(team == 1, -1.0, 0.0))
    return lado * direccion[:, None]


def adelante(modelo, lote):
    por_slot, hay, impares, pares = red.entradas(lote["px"], lote["py"], lote["bx"], lote["by"],
                                                 signo_de(lote["team"], lote["direccion"]), lote["direccion"],
                                                 lote["largo"], lote["ancho"])
    return modelo(por_slot, hay, lote["team"], impares, pares)


def perdida_de(salidas, lote, cfg):
    """(pérdida total, {término: valor}). Solo cuentan los grupos del centro del trozo, en frames vivos."""
    z, hacia_h, hacia_a, flag = salidas
    centro = torch.zeros_like(z, dtype=torch.bool)
    centro[:, cfg["margen"]:z.shape[1] - cfg["margen"]] = True

    def media(logit, objetivo, mascara):
        mascara = mascara & centro
        valores = F.binary_cross_entropy_with_logits(logit, objetivo.to(logit.dtype), reduction="none")
        return (valores * mascara).sum() / mascara.sum().clamp(min=1)

    gt, clase, gt_flag = lote["gt"], lote["clase"], lote["flag"]
    terminos = {
        "z": media(z, gt == 0, gt < 2),
        "cambios": media(hacia_h, clase == 1, clase >= 0) + media(hacia_a, clase == 2, clase >= 0),
        "flag": media(flag, gt_flag == 0, gt_flag < 2),
    }
    total = terminos["z"] + cfg["peso_cambios"] * terminos["cambios"] + cfg["peso_flag"] * terminos["flag"]
    return total, {k: float(v.detach()) for k, v in terminos.items()}


@torch.no_grad()
def predecir(modelo, m, bx, by):
    """(z, p) a 25 Hz de un partido entero con el balón dado: z (n,) y p (n, 2), a cero fuera de los tramos."""
    modelo.eval()
    p = red.PASO_VEL
    z25, p25 = np.zeros(m["n"]), np.zeros((m["n"], 2))
    for (a, b), direccion in zip(m["blocks"], m["direccion"]):
        largo = b - a
        grupos = -(-largo // cj.GRUPO)
        fin = a + grupos * cj.GRUPO
        lote = {"px": recorte(m["px"], a - p, fin + p, a, b)[None], "py": recorte(m["py"], a - p, fin + p, a, b)[None],
                "bx": recorte(bx, a - p, fin + p, a, b)[None], "by": recorte(by, a - p, fin + p, a, b)[None],
                "team": m["team"][None],
                "direccion": torch.tensor([direccion], dtype=torch.float32, device=bx.device),
                "largo": torch.tensor([m["largo"]], dtype=torch.float32, device=bx.device),
                "ancho": torch.tensor([m["ancho"]], dtype=torch.float32, device=bx.device)}
        z, hacia_h, hacia_a, _ = (v[0].double().cpu().numpy() for v in adelante(modelo, lote))
        inicio = np.arange(grupos) * cj.GRUPO
        centros = (inicio + np.minimum(inicio + cj.GRUPO - 1, largo - 1)) / 2.0
        t = np.arange(largo, dtype=np.float64)
        z25[a:b] = np.interp(t, centros, z)
        for columna, logit in enumerate((hacia_h, hacia_a)):
            p25[a:b, columna] = 1.0 / (1.0 + np.exp(-np.interp(t, centros, logit)))
    return z25, p25


def describir(modelo, partidos, titulo):
    """Tabla descriptiva de la salida en `partidos`: acierto de z y calidad del detector (medida de David)."""
    print("\n{}\n".format(titulo))
    print("| partido | balón | acierto de z en los vivos | pérdida de z | cambios | vistos | avisos por minuto vivo "
          "| avisos buenos |")
    print("|---|---|---|---|---|---|---|---|")
    for m in partidos:
        ref = m["np"]
        vivo = ref["gt"] < 2
        y = (ref["gt"][vivo] == 0).astype(np.float64)
        nombres = (cj.CONDICIONES_DFL if m["dominio"] == "dfl" else cj.CONDICIONES_SC)
        for j, (bx, by) in enumerate(m["balones"][:2]):
            z, p = predecir(modelo, m, bx, by)
            acierto = float(np.mean((z[vivo] > 0) == (y > 0.5)))
            perdida = float(np.mean(np.logaddexp(0.0, z[vivo]) - y * z[vivo]))
            reales, vistos, avisos, buenos, vivos = calidad(p, ref["clase"], ref["frames"], ref["hacia"])
            print("| {} {} | {} | {:.1f} % | {:.4f} | {} | {:.0f} % | {:.1f} | {:.0f} % |".format(
                m["dominio"], m["partido"], nombres[j], 100.0 * acierto, perdida, reales,
                100.0 * vistos / max(reales, 1), avisos / (vivos / 25.0 / 60.0), 100.0 * buenos / max(avisos, 1)),
                flush=True)


def guardar_salidas(modelo, m, etiqueta, pliegue, solo=None):
    datos = {"pliegue": np.array(pliegue)}
    if solo is not None:
        datos["solo"] = np.array(solo)  # el único proveedor con el que se entrenó
    for j, (bx, by) in enumerate(m["balones"]):
        clave = "{}{}".format("d" if j >= 2 else "", j % 2)  # 0, 1: las condiciones; d0, d1: balón a la vista en D
        z, p = predecir(modelo, m, bx, by)
        datos["z_" + clave], datos["p_" + clave] = z, p
    destino = cj.fichero_salida(etiqueta, m["dominio"], m["partido"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(destino, **datos)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pliegue", choices=cj.PLIEGUES)
    parser.add_argument("--etiqueta", default="piloto", help="nombre de la tanda: pesos y salidas van con él")
    parser.add_argument("--config", default=None, help="JSON con los valores de CONFIG que se cambian")
    parser.add_argument("--solo", choices=("dfl", "sc"), default=None,
                        help="entrena con un solo proveedor (pliegue «todos») y guarda las salidas del otro")
    parser.add_argument("--robusto", action="store_true",
                        help="la configuración de la ronda K2r: los aumentos de `ROBUSTO` en los trozos de la DFL")
    parser.add_argument("--dispositivo", choices=("cuda", "cpu"), default="cuda",
                        help="dónde entrena; en la CPU salen otros números al azar que en la GPU")
    parser.add_argument("--hilos", type=int, default=None, help="hilos de torch en la CPU (por defecto, los suyos)")
    parser.add_argument("--semilla", type=int, default=None,
                        help="otra semilla (por defecto, la del pliegue): para medir cuánto cambia el resultado de un "
                             "entrenamiento a otro con la misma configuración")
    parser.add_argument("--columnas", type=int, default=SLOTS,
                        help="columnas de slots por partido (por defecto {}); con menos, la CPU hace menos cuentas "
                             "sobre columnas vacías. Cambia los números al azar, no el modelo".format(SLOTS))
    parser.add_argument("--describir-dentro", action="store_true",
                        help="enseña también la tabla en dos partidos que el pliegue sí vio")
    args = parser.parse_args()
    if args.solo and args.pliegue != "todos":
        parser.error("--solo va con el pliegue «todos»")
    cfg = dict(CONFIG)
    if args.robusto:
        cfg.update(ROBUSTO)
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
    if args.solo:  # el otro proveedor entero queda fuera
        fuera_dfl, fuera_sc = (cj.DFL, ()) if args.solo == "sc" else ((), cj.SKILLCORNER)
    dentro = {"dfl": [cargar("dfl", p, device, args.columnas) for p in cj.DFL if p not in fuera_dfl],
              "sc": [cargar("sc", p, device, args.columnas) for p in cj.SKILLCORNER if p not in fuera_sc]}
    print("# Modelo conjunto · tanda «{}» · pliegue {} · semilla {}\n".format(args.etiqueta, args.pliegue, semilla))
    print("Entrena con {} partidos de la DFL y {} de SkillCorner; deja fuera: {}.".format(
        len(dentro["dfl"]), len(dentro["sc"]), ", ".join(str(p) for p in fuera_dfl + fuera_sc) or "ninguno"))
    print("Configuración: {}\n".format(json.dumps({k: cfg[k] for k in sorted(cfg)}, ensure_ascii=False)))
    print("Dispositivo: {} · torch {} · hilos {} · columnas de slots {}\n".format(
        device.type, torch.__version__, torch.get_num_threads(), args.columnas))

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
    if args.solo:
        reparto_del_lote = [(args.solo, cfg["lote"])]
    acumulado, cuenta = {}, 0
    for paso in range(cfg["pasos"]):
        modelo.train()
        elegidos = []
        for dominio, cuantos in reparto_del_lote:
            reparto = np.bincount(rng.integers(0, len(dentro[dominio]), size=cuantos), minlength=len(dentro[dominio]))
            elegidos += [(m, int(c)) for m, c in zip(dentro[dominio], reparto) if c]
        lote = aumentar(lote_de(elegidos, rng, cfg, device), cfg, gen)
        total, terminos = perdida_de(adelante(modelo, lote), lote, cfg)
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

    destino = cj.fichero_pesos(args.etiqueta, args.pliegue)
    destino.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"pesos": modelo.state_dict(), "config": cfg, "pliegue": args.pliegue, "semilla": semilla}, destino)

    fuera = ([cargar("dfl", p, device, args.columnas) for p in fuera_dfl]
             + [cargar("sc", p, device, args.columnas) for p in fuera_sc])
    if fuera:
        describir(modelo, fuera, "## Fuera de muestra: los partidos que el pliegue no vio (descriptivo, umbral 0,5)")
        for m in fuera:
            guardar_salidas(modelo, m, args.etiqueta, args.pliegue, args.solo)
    if args.describir_dentro or not fuera:
        describir(modelo, [lista[0] for lista in dentro.values() if lista],
                  "## Dentro de muestra: partidos que el pliegue sí vio (descriptivo)")
    if args.pliegue == "todos":
        # El de todos no tiene partidos fuera: sus salidas en los 17 son dentro de muestra y no se guardan.
        pass
    print("\nHecho en {:.0f} s.".format(time.time() - inicio))


if __name__ == "__main__":
    main()
