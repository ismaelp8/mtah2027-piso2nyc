"""K8: el piloto en el pliegue de `J03WMX`, frente a dos K2 del mismo pliegue (la de la GPU y una de la CPU).

    python validation/conjunto/piloto_k8.py --k2-cpu pesos_k2cpu_s26.npz --k8 pesos_k8_s26.npz

Datos abiertos de otros partidos (DFL, CC BY 4.0; SkillCorner, mitad de entrenamiento, MIT; Metrica sample-data). Lo
puede ejecutar cualquiera, Claude incluido. Solo imprime agregados. **No lee el examen de SkillCorner.**

La regla está en docs/decisiones.md (17/11, K8), escrita antes de entrenar. Los partidos son los que el pliegue de
`J03WMX` no vio: `J03WMX` en la DFL y `1874553` y `2010085` en SkillCorner. Metrica, que ese pliegue tampoco vio, va sin
voto. Cada versión es el logit del pliegue de `J03WMX` con α = 4, puntuado como K2:

- **K2, GPU:** el pliegue de `possession/conjunto_pesos.npz`, el de la harness de K2;
- **K2, CPU:** el mismo entrenamiento en la CPU, con la semilla de K8 (`entrenar.py --semilla`);
- **K8:** `entrenar_k8.py` con esa misma semilla: mismos pesos iniciales, mismos trozos y mismos aumentos; solo
  cambia la pérdida.

`main` (B5, con el pliegue de B5 que no vio `J03WMX` en la DFL y los coeficientes de la entrega en SkillCorner), el
`D` y el decodificador se montan como en `detalle_abiertos.py`, con su balón: la primera condición que vota. Las
cuentas son las de `detalle_abiertos.detalle`:

- **V:** los cambios directos entre equipos vistos (a ±1 s), entre los reales;
- **S:** los cambios entre equipos nuestros que sobran;
- **P:** las posesiones reales de 2 a 5 s encontradas (con un solape de 0,5 o más).

El ruido de cada medida es la diferencia entre las dos K2 (`N_x = |x(K2, CPU) − x(K2, GPU)|`).
"""

import argparse
import collections
import concurrent.futures
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import refinar  # noqa: E402
import medir  # noqa: E402
import detalle_abiertos as da  # noqa: E402
import cj_comun as cj  # noqa: E402
import comun as cc  # noqa: E402
import lector  # noqa: E402
from comun import dfl, puntuar  # noqa: E402
from possession import aprendida, conjunto  # noqa: E402
from possession.tracking import A, H  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PLIEGUE = cj.PILOTO  # J03WMX
SC = tuple(p for p in cj.SKILLCORNER if cj.pliegue_de("sc", p) == PLIEGUE)  # 1874553 y 2010085
MODOS = ("oraculo", "propio")
VOTAN = (("DFL, control", "oraculo"), ("SkillCorner", "oraculo"))  # V, S y P: `D` de las etiquetas
CELDAS_SPELL = (("DFL, control", "oraculo"), ("DFL, control", "propio"), ("SkillCorner", "oraculo"),
                ("SkillCorner", "propio"))
V_MIN, S_TOL, P_MIN, SPELL_TOL = 3.0, 0.05, 2.0, 0.005  # docs/decisiones.md, 17/11, K8
CERCA = 25  # frames: ±5 grupos alrededor de un cambio real, para la media de |z| (sin voto)
DOS_A_CINCO = 2  # el tramo de 2 a 5 s de `detalle_abiertos.TRAMOS`


def ruta(fichero):
    if fichero == "repo":
        return os.path.join(os.path.dirname(os.path.dirname(AQUI)), "possession", "conjunto_pesos.npz")
    return fichero if os.path.isabs(fichero) else str(cj.carpeta() / fichero)


def diagnostico_z(z, gt, blocks):
    """Sin voto: lo que hace z por frame frente a la etiqueta (pérdida y acierto en los vivos con equipo) y la media
    de |z| a ±`CERCA` frames de un cambio directo entre equipos, y lejos de ellos. Sumas, para juntar partidos."""
    gt = np.asarray(gt)
    dentro = np.zeros(len(gt), dtype=bool)
    for a, b in blocks:
        dentro[a:b] = True
    vivo = dentro & ((gt == H) | (gt == A))
    y = (gt == H).astype(np.float64)
    perdida = np.logaddexp(0.0, z) - y * z
    bien = np.where(gt == H, z > 0, z < 0)
    cambios = np.flatnonzero(vivo[1:] & vivo[:-1] & (gt[1:] != gt[:-1])) + 1
    cerca = np.zeros(len(gt), dtype=bool)
    for t in cambios:
        cerca[max(0, t - CERCA):t + CERCA + 1] = True
    cerca &= vivo
    lejos = vivo & ~cerca
    return collections.Counter({"perdida": float(perdida[vivo].sum()), "bien": int(bien[vivo].sum()),
                                "vivos": int(vivo.sum()), "abs cerca": float(np.abs(z[cerca]).sum()),
                                "cerca": int(cerca.sum()), "abs lejos": float(np.abs(z[lejos]).sum()),
                                "lejos": int(lejos.sum())})


def de_un_tracking(trk, gts, versiones, pliegue_b5):
    piezas = medir._piezas(puntuar.solo_lectura(trk), next(iter(gts.values())), pliegue_b5)
    logits, zs = {}, {}
    for nombre, fichero in versiones:
        refinar._usar_pesos(ruta(fichero))
        zs[nombre] = conjunto.salidas(piezas["limpio"], PLIEGUE)[0]
        logits[nombre] = float(conjunto.pesos(PLIEGUE)["alfa"]) * zs[nombre]
    primera = next(iter(gts))
    salida = {("z", primera, nombre): (diagnostico_z(z, gts[primera], piezas["blocks"]), None)
              for nombre, z in zs.items()}
    for modo in MODOS:
        preds = {"main": medir._decodificar(piezas, piezas["b5"], modo)}
        for nombre, s in logits.items():
            mio = aprendida.puntuacion_de("b5", s, piezas["visible"], 1.0, piezas["cercano"])
            preds[nombre] = medir._decodificar(piezas, mio, modo)
        for nombre, pred in preds.items():
            for convencion, gt in gts.items():
                salida[(convencion, modo, nombre)] = (da.detalle(gt, pred)[0], puntuar.contar(gt, pred))
    return salida


def trabajo(t):
    dominio, partido, versiones = t
    inicio = time.time()
    if dominio == "dfl":
        cargado = dfl.cargar(partido)
        gts = collections.OrderedDict((("DFL, control", cargado["gt"]["control"]), ("DFL, flag", cargado["gt"]["flag"])))
        salida = de_un_tracking(dfl.tracking_de(cargado, dfl.VOTAN[0]), gts, versiones, partido)
    elif dominio == "sc":
        lector.exigir_solo_entrenamiento([partido])
        trk, gt = lector.tracking_de(lector.leer_crudo(partido), lector.VOTAN[0], partido)
        salida = de_un_tracking(trk, {"SkillCorner": gt}, versiones, None)
    else:
        lc = refinar.lector_metrica()
        trk, gt = lc.tracking_de(lc.leer(partido), lc.VOTAN[0], partido)
        salida = de_un_tracking(trk, {"Metrica": gt}, versiones, None)
    return (dominio, partido), salida, time.time() - inicio


def medidas(cuentas, recuentos, datos, modo, version):
    c = collections.Counter()
    spell = []
    for dato in datos:
        c.update(cuentas[(dato, modo, version)])
    return {"V": 100.0 * c["vistos", "equipos"] / max(c["cambios reales", "equipos"], 1),
            "S": c["nos sobran", "equipos"],
            "P": 100.0 * c["tramo", DOS_A_CINCO, "encontrada"] / max(c["tramo", DOS_A_CINCO, "reales"], 1),
            "<2 s": 100.0 * (c["tramo", 0, "encontrada"] + c["tramo", 1, "encontrada"])
            / max(c["tramo", 0, "reales"] + c["tramo", 1, "reales"], 1),
            "reales": c["cambios reales", "equipos"], "P reales": c["tramo", DOS_A_CINCO, "reales"],
            "nuestros": c["cambios nuestros", "equipos"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--k2-cpu", required=True, help="pesos de K2 en la CPU, con la clave del pliegue")
    parser.add_argument("--k8", required=True, help="pesos de K8, con la clave del pliegue")
    parser.add_argument("--procesos", type=int, default=2)
    args = parser.parse_args()
    refinar.exigir_b5_en_main()
    lector.exigir_solo_entrenamiento(list(SC))
    versiones = (("K2, GPU", "repo"), ("K2, CPU", args.k2_cpu), ("K8", args.k8))
    for nombre, fichero in versiones:
        refinar._usar_pesos(ruta(fichero))
        if float(conjunto.pesos(PLIEGUE)["alfa"]) != 4.0:
            sys.exit("{} no trae α = 4 en el pliegue {}".format(fichero, PLIEGUE))
    lc = refinar.lector_metrica()
    trabajos = [("dfl", PLIEGUE, versiones)] + [("sc", p, versiones) for p in SC] + \
        [("metrica", int(p), versiones) for p in lc.partidos()]
    cuentas = collections.defaultdict(collections.Counter)
    recuentos = collections.defaultdict(list)
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        for (dominio, partido), salida, segundos in pool.map(trabajo, trabajos):
            for clave, (detalle, recuento) in salida.items():
                cuentas[clave].update(detalle)
                if recuento is not None:
                    recuentos[clave].append(recuento)
            print("# hecho {} {} en {:.0f} s".format(dominio, partido, segundos), file=sys.stderr, flush=True)

    nombres = ["main"] + [n for n, _ in versiones]
    print("# K8: el piloto en el pliegue de {} · {} y {} (SkillCorner) · Metrica sin voto\n".format(
        PLIEGUE, PLIEGUE, " y ".join(str(p) for p in SC)))
    print("Código: {} · este script: sha256 {}… · pesos: {}.".format(
        puntuar.version_del_codigo(), refinar.huella(os.path.abspath(__file__)),
        "; ".join("{}, `{}` (sha256 {}…)".format(n, os.path.basename(ruta(f)), refinar.huella(ruta(f)))
                  for n, f in versiones)))

    print("\n## Lo que ataca K8 (vota: DFL con control y SkillCorner juntos, `D` de las etiquetas)\n")
    print("| versión | V: cambios entre equipos vistos | nuestros | S: nos sobran | P: posesiones de 2 a 5 s "
          "encontradas | de menos de 2 s encontradas |")
    print("|---|---|---|---|---|---|")
    valores = {}
    for nombre in nombres:
        datos = [d for d, _ in VOTAN]
        valores[nombre] = medidas(cuentas, recuentos, datos, "oraculo", nombre)
        v = valores[nombre]
        print("| {} | {:.1f} % de {} | {} | {} | {:.1f} % de {} | {:.1f} % |".format(
            nombre, v["V"], v["reales"], v["nuestros"], v["S"], v["P"], v["P reales"], v["<2 s"]))

    print("\n## Lo mismo por proveedor (sin voto: SkillCorner pone unos tres cuartos de los cambios)\n")
    print("| datos | versión | V | nuestros | S | P | de menos de 2 s |")
    print("|---|---|---|---|---|---|---|")
    for dato, modo in VOTAN:
        for nombre in nombres:
            v = medidas(cuentas, recuentos, [dato], modo, nombre)
            print("| {} | {} | {:.1f} % de {} | {} | {} | {:.1f} % de {} | {:.1f} % |".format(
                dato, nombre, v["V"], v["reales"], v["nuestros"], v["S"], v["P"], v["P reales"], v["<2 s"]))

    print("\n## z por frame (sin voto: el riesgo de que la escala del CRF aplane z cerca de los cambios)\n")
    print("Frames vivos con equipo en la etiqueta (DFL con control y SkillCorner), balón de la primera condición.\n")
    print("| datos | versión | pérdida de z | acierto del signo | media de |z| a ±{} frames de un cambio | lejos de "
          "ellos | cerca / lejos |".format(CERCA))
    print("|---|---|---|---|---|---|---|")
    for dato in ("DFL, control", "SkillCorner", "Metrica"):
        for nombre in nombres[1:]:
            c = cuentas[("z", dato, nombre)]
            cerca, lejos = c["abs cerca"] / max(c["cerca"], 1), c["abs lejos"] / max(c["lejos"], 1)
            print("| {} | {} | {:.4f} | {:.1f} % | {:.2f} | {:.2f} | {:.2f} |".format(
                dato, nombre, c["perdida"] / max(c["vivos"], 1), 100.0 * c["bien"] / max(c["vivos"], 1), cerca,
                lejos, cerca / max(lejos, 1e-9)))

    print("\n## spellF1 en las celdas del piloto\n")
    print("| datos | `D` | {} |".format(" | ".join(nombres)))
    print("|---|---|" + "---|" * len(nombres))
    spell = collections.defaultdict(list)
    for dato, modo in CELDAS_SPELL:
        notas = {n: cc.spell(recuentos[(dato, modo, n)]) for n in nombres}
        for n in nombres:
            spell[n].append(notas[n])
        print("| {} | {} | {} |".format(dato, medir.NOMBRE_MODO[modo], " | ".join("{:.3f}".format(notas[n])
                                                                                  for n in nombres)))
    media = {n: float(np.mean(spell[n])) for n in nombres}
    print("| media | | {} |".format(" | ".join("{:.4f}".format(media[n]) for n in nombres)))

    print("\n## Sin voto: el flag, el `D` propio y Metrica\n")
    print("| datos | `D` | versión | V | nuestros | S | P | de menos de 2 s | spellF1 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for dato in ("DFL, control", "DFL, flag", "SkillCorner", "Metrica"):
        for modo in MODOS:
            if (dato, modo) in VOTAN:
                continue
            for nombre in nombres:
                v = medidas(cuentas, recuentos, [dato], modo, nombre)
                print("| {} | {} | {} | {:.1f} % de {} | {} | {} | {:.1f} % de {} | {:.1f} % | {:.3f} |".format(
                    dato, medir.NOMBRE_MODO[modo], nombre, v["V"], v["reales"], v["nuestros"], v["S"], v["P"],
                    v["P reales"], v["<2 s"], cc.spell(recuentos[(dato, modo, nombre)])))

    k8, cpu, gpu = valores["K8"], valores["K2, CPU"], valores["K2, GPU"]
    ruido = {x: abs(cpu[x] - gpu[x]) for x in ("V", "S", "P")}
    ruido_spell = abs(media["K2, CPU"] - media["K2, GPU"])
    puntos = [
        ("1. V sube al menos max({:g} puntos, 2·N_V = {:.1f})".format(V_MIN, 2 * ruido["V"]),
         k8["V"] - cpu["V"], k8["V"] - cpu["V"] >= max(V_MIN, 2 * ruido["V"])),
        ("2. S no sube más que max({:.0f} %, N_S = {})".format(100 * S_TOL, ruido["S"]),
         k8["S"] - cpu["S"], k8["S"] - cpu["S"] <= max(S_TOL * cpu["S"], ruido["S"])),
        ("3. P no baja más que max({:g} puntos, N_P = {:.1f})".format(P_MIN, ruido["P"]),
         k8["P"] - cpu["P"], k8["P"] - cpu["P"] >= -max(P_MIN, ruido["P"])),
        ("4. el spellF1 medio no baja más que max({}, N_spell = {:.4f})".format(SPELL_TOL, ruido_spell),
         media["K8"] - media["K2, CPU"], media["K8"] - media["K2, CPU"] >= -max(SPELL_TOL, ruido_spell)),
    ]
    print("\n## La regla (K8 frente a K2, CPU; el ruido es K2, CPU frente a K2, GPU)\n")
    print("Ruido: N_V {:.1f} puntos · N_S {} · N_P {:.1f} puntos · N_spell {:.4f}.\n".format(
        ruido["V"], ruido["S"], ruido["P"], ruido_spell))
    for texto, valor, pasa in puntos:
        print("- {}: {:+.4g} → **{}**".format(texto, valor, "pasa" if pasa else "no pasa"))
    todos = all(p for _, _, p in puntos)
    print("\n**{}**".format("K8 merece la ronda de 8 pliegues" if todos else "K8 no merece la ronda"))


if __name__ == "__main__":
    main()
