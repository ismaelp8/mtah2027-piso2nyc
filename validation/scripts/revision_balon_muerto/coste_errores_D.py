"""Coste en spellF1 de los errores propios del detector de D, sobre la GT sintética del repo
(validation/scripts/sensibilidad_metrica.py). No lee ningún dato del partido. Solo imprime agregados."""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
sys.path.insert(0, os.path.join(ROOT, "validation", "scripts"))
import possession_metrics as pm  # noqa: E402
import sensibilidad_metrica as sm  # noqa: E402

SEMILLAS = range(6)


def segs(c):
    return sm.segmentos(c)


def d_segments(c):
    return [(a, b) for a, b, k in segs(c) if k == pm.D]


def quitar_D(c, frac, rng, cuando=None):
    """Una fracción de las paradas no se detecta: heredan la etiqueta anterior.
    cuando='igual' solo las que tienen el mismo equipo a los dos lados; 'distinto' solo las otras."""
    out = c.copy()
    sg = segs(c)
    for i, (a, b, k) in enumerate(sg):
        if k != pm.D or i == 0 or i == len(sg) - 1:
            continue
        mismo = sg[i - 1][2] == sg[i + 1][2]
        if cuando == "igual" and not mismo:
            continue
        if cuando == "distinto" and mismo:
            continue
        if rng.rand() < frac:
            out[a:b] = out[a - 1]
    return out


def mover_inicio_D(c, k):
    """Cada D empieza k frames tarde (k>0) o pronto (k<0)."""
    out = c.copy()
    for a, b in d_segments(c):
        if a == 0:
            continue
        if k > 0:
            out[a:min(a + k, b)] = c[a - 1]
        else:
            out[max(a + k, 0):a] = pm.D
    return out


def mover_fin_D(c, k):
    """Cada D acaba k frames tarde (k>0: el reinicio se detecta tarde) o pronto (k<0)."""
    out = c.copy()
    n = len(c)
    for a, b in d_segments(c):
        if b >= n:
            continue
        if k > 0:
            out[b:min(b + k, n)] = pm.D
        else:
            out[max(b + k, a):b] = c[b]
    return out


def acortar_D(c, n_frames):
    """D solo dura n frames (disparo al salir el balón y nada más); el resto hereda la etiqueta previa."""
    out = c.copy()
    for a, b in d_segments(c):
        if a == 0 or b - a <= n_frames:
            continue
        out[a + n_frames:b] = c[a - 1]
    return out


def equipo_mal_tras_D(c, k):
    """Tras cada D, los primeros k frames vivos se dan al equipo equivocado."""
    out = c.copy()
    n = len(c)
    for a, b in d_segments(c):
        if b >= n:
            continue
        fin = min(b + k, n)
        j = b
        while j < fin and c[j] == c[b]:
            j += 1
        out[b:j] = 1 - c[b]
    return out


def equipo_previo_tras_D(c, k):
    """Tras cada D, se arrastra el equipo de ANTES de la parada durante k frames (no sabemos quién saca)."""
    out = c.copy()
    n = len(c)
    for a, b in d_segments(c):
        if b >= n or a == 0:
            continue
        fin = min(b + k, n)
        j = b
        while j < fin and c[j] == c[b]:
            j += 1
        out[b:j] = c[a - 1]
    return out


def d_fragmentado(c, hueco, cada):
    """Dentro de cada D largo, un hueco de `hueco` frames vuelve a la etiqueta previa cada `cada` frames."""
    out = c.copy()
    for a, b in d_segments(c):
        if a == 0:
            continue
        for t in range(a + cada, b - hueco, cada):
            out[t:t + hueco] = c[a - 1]
    return out


def inventar_D(c, por_min, rng):
    """D inventados de 1–4 s dentro del juego vivo, `por_min` por minuto de balón vivo."""
    out = c.copy()
    n = len(c)
    n_ins = int(por_min * (np.sum(c != pm.D) / 25 / 60))
    for _ in range(n_ins):
        t = rng.randint(0, n - 100)
        largo = rng.randint(25, 100)
        if np.all(c[t:t + largo] != pm.D):
            out[t:t + largo] = pm.D
    return out


def main():
    _, mu, s, _ = sm.ajustar()
    gts = [sm.generar_gt(k, mu, s) for k in SEMILLAS]  # una sola vez

    def score(fn):
        vals = []
        for k, gt in enumerate(gts):
            rng = np.random.RandomState(100 + k)
            vals.append(pm.evaluate(gt, fn(gt, rng))["spell_f1_mean"])
        return float(np.mean(vals))

    def fila(nombre, fn):
        print("  {:<62} {:.3f}".format(nombre, score(fn)))

    gt0 = gts[0]
    nd = len(d_segments(gt0))
    npos = len([1 for _, _, k in segs(gt0) if k != pm.D])
    print("GT sintética (semilla 0): {} posesiones, {} paradas, {:.0f} % de frames D; lognormal mu={:.2f} s={:.2f}".format(
        npos, nd, 100 * np.mean(gt0 == pm.D), mu, s))
    print("spellF1 medio sobre {} partes sintéticas (perfecto = 1.000)\n".format(len(SEMILLAS)))

    print("A. Paradas no detectadas (heredan la etiqueta anterior)")
    for frac in (1.0, 0.8, 0.5, 0.2, 0.1):
        fila("se pierde el {:.0f} % de las paradas".format(100 * frac), lambda c, r, f=frac: quitar_D(c, f, r))
    fila("se pierden solo las paradas con el MISMO equipo a los dos lados", lambda c, r: quitar_D(c, 1.0, r, "igual"))
    fila("se pierden solo las paradas con equipo DISTINTO a los dos lados", lambda c, r: quitar_D(c, 1.0, r, "distinto"))

    print("\nB. Inicio del D (el balón sale / se pita) detectado tarde o pronto")
    for k in (3, 8, 12, 25, 50, 125, 250):
        fila("empieza {} frames tarde ({:.1f} s)".format(k, k / 25), lambda c, r, k=k: mover_inicio_D(c, k))
    for k in (12, 25, 50):
        fila("empieza {} frames PRONTO ({:.1f} s)".format(k, k / 25), lambda c, r, k=k: mover_inicio_D(c, -k))

    print("\nC. Fin del D (el reinicio) detectado tarde o pronto")
    for k in (3, 8, 12, 25, 50, 62, 125):
        fila("acaba {} frames tarde ({:.1f} s)".format(k, k / 25), lambda c, r, k=k: mover_fin_D(c, k))
    for k in (12, 25, 50):
        fila("acaba {} frames PRONTO ({:.1f} s)".format(k, k / 25), lambda c, r, k=k: mover_fin_D(c, -k))

    print("\nD. Los dos bordes tarde a la vez")
    for k in (12, 25, 50):
        fila("inicio y fin {} frames tarde".format(k), lambda c, r, k=k: mover_fin_D(mover_inicio_D(c, k), k))

    print("\nE. D que solo dura un instante (disparo al salir el balón, sin saber cuándo se reanuda)")
    for n in (25, 50, 125):
        fila("cada D dura {} frames y luego vuelve al equipo previo".format(n), lambda c, r, n=n: acortar_D(c, n))

    print("\nF. D detectado pero parpadea dentro de la parada")
    fila("hueco de 10 frames cada 100 dentro de cada D", lambda c, r: d_fragmentado(c, 10, 100))
    fila("hueco de 25 frames cada 250 dentro de cada D", lambda c, r: d_fragmentado(c, 25, 250))

    print("\nG. Equipo al reanudar (D perfecto)")
    for k in (12, 25, 75, 250):
        fila("equipo equivocado durante {} frames tras cada D".format(k), lambda c, r, k=k: equipo_mal_tras_D(c, k))
    for k in (25, 75, 250):
        fila("se arrastra el equipo previo durante {} frames tras cada D".format(k), lambda c, r, k=k: equipo_previo_tras_D(c, k))
    fila("se arrastra el equipo previo durante TODA la posesión siguiente", lambda c, r: equipo_previo_tras_D(c, 10 ** 9))

    print("\nH. Referencia: D inventados en juego vivo (ya medido en el repo)")
    for por_min in (0.5, 1, 2):
        fila("{} D inventados de 1–4 s por minuto".format(por_min), lambda c, r, p=por_min: inventar_D(c, p, r))


if __name__ == "__main__":
    main()
