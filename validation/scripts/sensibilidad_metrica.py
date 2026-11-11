"""Cuánto cuesta cada tipo de error en spellF1, medido sobre una GT sintética.

No lee ningún dato del partido. Sus únicas entradas son la tabla de retrasos publicada en
EVALUATION.md (3 / 8 / 25 frames -> 0,9818 / 0,8933 / 0,6539) y el scorer oficial.

Qué hace
--------
1. Ajusta una lognormal de duraciones de posesión que reproduce esa tabla. La forma lognormal es una
   suposición; lo robusto es el orden de magnitud (cuántas posesiones son cortas).
2. Genera partes sintéticas con esa distribución. Supuestos propios: el 40 % de las posesiones
   acaba en balón muerto y una parada dura unos 12 s de mediana.
3. Aplica un tipo de error cada vez a un etiquetado perfecto y lo puntúa con el scorer oficial.

Sirve para ordenar los errores por coste, no para predecir nuestra nota. Como se calibra con la tabla
oficial, sus cifras son lectura de la métrica y no base para fijar parámetros (duda D21 de
validation/PASOS.md). De aquí salen las tablas
de las secciones 1.2, 1.3 y 7.2 de docs/investigacion_metodos.md. Es determinista (semillas fijas)
y tarda unos segundos.

Uso:
    python validation/scripts/sensibilidad_metrica.py
"""

import os
import sys
from math import erf, log, sqrt

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import possession_metrics as pm  # noqa: E402

OBJETIVO = {3: 0.9818, 8: 0.8933, 25: 0.6539}  # EVALUATION.md
IOUS = pm.SPELL_IOUS


def cdf(x, mu, s):
    return 0.5 * (1 + erf((log(x) - mu) / (s * sqrt(2))))


def tabla(mu, s):
    """spellF1 esperado con un retraso uniforme d si las duraciones son lognormales (mu, s)."""
    out = {}
    for d in OBJETIVO:
        out[d] = float(np.mean([1 - cdf(d * (1 + t) / (1 - t), mu, s) for t in IOUS]))
    return out


def ajustar():
    mejor = None
    for mu in np.arange(3.0, 6.5, 0.02):
        for s in np.arange(0.6, 2.2, 0.02):
            tb = tabla(mu, s)
            err = sum((tb[d] - OBJETIVO[d]) ** 2 for d in OBJETIVO)
            if mejor is None or err < mejor[0]:
                mejor = (err, mu, s, tb)
    return mejor


def generar_gt(semilla, mu, s, n_vivos=90000, p_muerto=0.4):
    """Una 'parte' sintética: posesiones H/A con paradas D detrás de una fracción de ellas."""
    rng = np.random.RandomState(semilla)
    etiquetas = []
    equipo = rng.randint(0, 2)
    vivos = 0
    etiquetas.append(np.full(250, pm.D, dtype=np.int8))
    while vivos < n_vivos:
        largo = int(np.clip(round(np.exp(rng.normal(mu, s))), 3, 3000))
        etiquetas.append(np.full(largo, equipo, dtype=np.int8))
        vivos += largo
        if rng.rand() < p_muerto:
            dlargo = int(np.clip(round(np.exp(rng.normal(np.log(300), 0.6))), 50, 3000))
            etiquetas.append(np.full(dlargo, pm.D, dtype=np.int8))
            equipo = rng.randint(0, 2)        # tras una parada puede reanudar cualquiera
        else:
            equipo = 1 - equipo               # pérdida en juego
    etiquetas.append(np.full(250, pm.D, dtype=np.int8))
    return np.concatenate(etiquetas)


def segmentos(codigos):
    b = np.flatnonzero(codigos[1:] != codigos[:-1]) + 1
    bordes = np.concatenate(([0], b, [len(codigos)]))
    return [(int(bordes[i]), int(bordes[i + 1]), int(codigos[bordes[i]]))
            for i in range(len(bordes) - 1)]


def desplazar_fronteras(codigos, sd, rng, solo=None):
    """Mueve cada frontera N(0, sd) frames. solo='D': solo las de D; solo='T': solo H<->A."""
    segs = segmentos(codigos)
    cortes = [s[0] for s in segs[1:]]
    nuevos = []
    for i, c in enumerate(cortes):
        con_d = segs[i][2] == pm.D or segs[i + 1][2] == pm.D
        if solo == "D" and not con_d:
            nuevos.append(c)
        elif solo == "T" and con_d:
            nuevos.append(c)
        else:
            nuevos.append(int(round(c + rng.normal(0, sd))))
    nuevos = np.clip(nuevos, 1, len(codigos) - 1)
    nuevos = np.maximum.accumulate(nuevos)
    bordes = [0] + list(nuevos) + [len(codigos)]
    out = np.empty(len(codigos), dtype=np.int8)
    for i, (_, _, k) in enumerate(segs):
        out[bordes[i]:bordes[i + 1]] = k
    return out


def perder_cortas(codigos, m, p=1.0, rng=None, desde=0):
    """Las posesiones con desde <= largo < m se pierden con probabilidad p: heredan la etiqueta anterior."""
    out = codigos.copy()
    for a, b, k in segmentos(codigos):
        if k != pm.D and desde <= (b - a) < m and a > 0:
            if p >= 1.0 or rng.rand() < p:
                out[a:b] = out[a - 1]
    return out


def cambios_falsos(codigos, por_minuto, rng, lo=10, hi=40):
    """Inventa cambios de posesión de 10-40 frames dentro de posesiones reales."""
    out = codigos.copy()
    vivos = np.flatnonzero(codigos != pm.D)
    n = int(round(por_minuto * len(vivos) / 1500.0))
    for inicio in rng.choice(vivos, size=n, replace=False):
        largo = rng.randint(lo, hi + 1)
        tramo = codigos[inicio:inicio + largo]
        if len(tramo) == largo and np.all(tramo == tramo[0]) and tramo[0] != pm.D:
            out[inicio:inicio + largo] = 1 - tramo[0]
    return out


def paradas_perdidas(codigos, q, rng):
    """Cada parada se pierde con probabilidad q: hereda el equipo anterior."""
    out = codigos.copy()
    segs = segmentos(codigos)
    for i, (a, b, k) in enumerate(segs):
        if k == pm.D and 0 < i < len(segs) - 1 and rng.rand() < q:
            out[a:b] = out[a - 1]
    return out


def d_falsos(codigos, por_minuto, rng, lo=25, hi=100):
    """Inventa tramos D de 1-4 s dentro del juego vivo."""
    out = codigos.copy()
    vivos = np.flatnonzero(codigos != pm.D)
    n = int(round(por_minuto * len(vivos) / 1500.0))
    for inicio in rng.choice(vivos, size=n, replace=False):
        largo = rng.randint(lo, hi + 1)
        out[inicio:inicio + largo] = pm.D
    return out


def main():
    err, mu, s, tb = ajustar()
    print("lognormal ajustada: mediana {:.0f} frames ({:.1f} s), sigma {:.2f}, media {:.0f} frames "
          "({:.1f} s)".format(np.exp(mu), np.exp(mu) / 25, s, np.exp(mu + s * s / 2),
                              np.exp(mu + s * s / 2) / 25))
    print("tabla reproducida por el ajuste: {}  objetivo: {}".format(
        {d: round(v, 4) for d, v in tb.items()}, OBJETIVO))
    for x in (12, 18, 25, 50, 75, 125, 250, 500):
        print("  posesiones de menos de {:4d} frames ({:4.1f} s): {:.1f} %".format(
            x, x / 25, 100 * cdf(x, mu, s)))

    def run(nombre, fn, semillas=(0, 1, 2, 3)):
        spell, macro, cociente = [], [], []
        for semilla in semillas:
            gt = generar_gt(semilla, mu, s)
            rng = np.random.RandomState(1000 + semilla)
            pred = fn(gt, rng)
            r = pm.evaluate(gt, pred)
            spell.append(r["spell_f1_mean"])
            macro.append(r["macro_f1"])
            cociente.append(r["n_pred_spells"] / float(r["n_gt_spells"]))
        print("{:<66} spellF1 {:.3f}  macroF1 {:.3f}  posesiones pred/real {:.2f}".format(
            nombre, np.mean(spell), np.mean(macro), np.mean(cociente)))

    gt0 = generar_gt(0, mu, s)
    r0 = pm.evaluate(gt0, gt0)
    print("\nparte sintética: {} frames, {} posesiones, media {:.1f} s, balón vivo {:.2f}".format(
        len(gt0), r0["n_gt_spells"], r0["gt_mean_spell_duration_s"], np.mean(gt0 != pm.D)))

    print("\n-- comprobación: retraso uniforme sobre la GT sintética (debe parecerse a la oficial) --")
    for d in (3, 8, 25):
        run("retraso uniforme de {} frames".format(d),
            lambda g, rng, d=d: np.concatenate((np.full(d, g[0]), g[:-d])))

    print("\n-- fronteras desplazadas N(0, sd) --")
    for sd in (3, 6, 12, 25):
        run("sd {} frames, todas las fronteras".format(sd),
            lambda g, rng, sd=sd: desplazar_fronteras(g, sd, rng))
    for sd in (12, 25, 50):
        run("sd {} frames, solo las fronteras con D".format(sd),
            lambda g, rng, sd=sd: desplazar_fronteras(g, sd, rng, "D"))
    for sd in (12, 25):
        run("sd {} frames, solo los cambios H<->A".format(sd),
            lambda g, rng, sd=sd: desplazar_fronteras(g, sd, rng, "T"))

    print("\n-- posesiones cortas no detectadas (heredan la etiqueta anterior) --")
    for m in (12, 18, 25, 50, 75, 125):
        run("se pierden todas las de menos de {} frames ({:.1f} s)".format(m, m / 25.0),
            lambda g, rng, m=m: perder_cortas(g, m))

    print("\n-- cambios de posesión inventados dentro de posesiones reales (10-40 frames) --")
    for r in (0.25, 0.5, 1, 2, 4, 8):
        run("{:.2f} cambios falsos por minuto de balón vivo".format(r),
            lambda g, rng, r=r: cambios_falsos(g, r, rng))

    print("\n-- errores de balón muerto --")
    for q in (0.1, 0.25, 0.5, 1.0):
        run("{:.0f} % de las paradas no detectadas (D -> equipo anterior)".format(q * 100),
            lambda g, rng, q=q: paradas_perdidas(g, q, rng))
    for r in (0.25, 0.5, 1, 2):
        run("{:.2f} tramos D falsos (1-4 s) por minuto de balón vivo".format(r),
            lambda g, rng, r=r: d_falsos(g, r, rng))

    print("\n-- escenarios combinados (sección 7.2 del informe) --")
    run("A: sd 6 + pierde <18 + 0,25 falsos/min + 5 % paradas",
        lambda g, rng: paradas_perdidas(cambios_falsos(perder_cortas(
            desplazar_fronteras(g, 6, rng), 18), 0.25, rng), 0.05, rng))
    run("B: sd 12 + pierde <25 y la mitad de 25-75 + 0,5 falsos/min + 10 %",
        lambda g, rng: paradas_perdidas(cambios_falsos(perder_cortas(perder_cortas(
            desplazar_fronteras(g, 12, rng), 25), 75, 0.5, rng, 25), 0.5, rng), 0.10, rng))
    run("C: sd 12 + pierde <50 y la mitad de 50-125 + 1 falso/min + 20 %",
        lambda g, rng: paradas_perdidas(cambios_falsos(perder_cortas(perder_cortas(
            desplazar_fronteras(g, 12, rng), 50), 125, 0.5, rng, 50), 1, rng), 0.20, rng))
    run("D: sd 25 + pierde <75 + 2 falsos/min + 30 % + 0,5 D falsos/min",
        lambda g, rng: d_falsos(paradas_perdidas(cambios_falsos(perder_cortas(
            desplazar_fronteras(g, 25, rng), 75), 2, rng), 0.30, rng), 0.5, rng))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # tildes bien también al redirigir a un fichero
    main()
