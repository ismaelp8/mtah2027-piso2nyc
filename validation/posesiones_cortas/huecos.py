"""Dónde caen nuestros cambios de equipo respecto a los huecos del balón en el juego. Biblioteca, sin ficheros.

La usan `validation/partido/huecos_y_cambios.py` (el partido, lo ejecuta una persona) y
`validation/posesiones_cortas/huecos_dfl.py` (la referencia de la DFL, la puede ejecutar Claude). Regla de
lectura en `validation/posesiones_cortas/BITACORA.md` §14.

Definiciones, sobre una salida nuestra (códigos `H`, `A`, `D`, `X`) y el balón visible frame a frame:
- **juego:** los frames en que decimos `H` o `A`, dentro de los tramos evaluados;
- **hueco:** una racha de frames sin balón dentro de un tramo;
  - **en juego:** todos sus frames son de juego, y el frame de antes y el de después también, con balón;
  - **pegado a un `D` o al borde:** los demás;
- **cambio:** un frame de juego cuya etiqueta es distinta de la del frame anterior, también de juego (`H` a
  `A` o al revés);
- **al reaparecer:** de 0 a `TRAS` frames después del primer frame con balón tras un hueco en juego de 13
  frames o más.

Recuentos (`medir`):
- por duración del hueco en juego: cuántos hay; en cuántos decimos un equipo antes del hueco (el frame de antes)
  y otro después (`TRAS` frames tras reaparecer); y, de esos, si nuestro cambio cae dentro del hueco o al
  reaparecer;
- de todos nuestros cambios: cuántos caen dentro de un hueco en juego de 13 frames o más, cuántos al reaparecer
  y cuántos en otro sitio;
- **al azar,** en la misma salida: qué parte de los frames de juego está dentro de esos huecos y qué parte al
  reaparecer. Es lo que darían unos cambios repartidos al azar en el juego.
"""

import numpy as np

H, A, D = 0, 1, 2
TRAS = 12  # frames: «al reaparecer» es de 0 a 12 frames (0,5 s) tras volver el balón
MINIMO_HUECO = 13  # frames: los huecos que cuentan para la regla duran 0,5 s o más
TRAMOS = ((1, 13, "≤ 0,5 s"), (13, 51, "0,5–2 s"), (51, 126, "2–5 s"), (126, 376, "5–15 s"), (376, 10 ** 9, "> 15 s"))
CLAVES = ("huecos", "con cambio", "cambio dentro", "cambio al reaparecer")


def _rachas(mascara):
    bordes = np.diff(np.concatenate(([0], mascara.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(bordes == 1).tolist(), np.flatnonzero(bordes == -1).tolist()))


def tramo(largo):
    for a, b, nombre in TRAMOS:
        if a <= largo < b:
            return nombre
    raise ValueError(largo)


def nuevo():
    salida = {("hueco", t, k): 0 for _, _, t in TRAMOS for k in CLAVES}
    salida.update({k: 0 for k in ("huecos pegados a un D o al borde", "cambios", "cambios dentro de un hueco",
                                  "cambios al reaparecer", "cambios en otro sitio", "frames de juego",
                                  "frames de juego dentro de un hueco", "frames de juego al reaparecer")})
    return salida


def medir(codes, visible, blocks, acc=None):
    """Suma a `acc` (o a uno nuevo) los recuentos de una salida. Solo enteros: no guarda frames."""
    acc = nuevo() if acc is None else acc
    codes = np.asarray(codes)
    visible = np.asarray(visible, dtype=bool)
    for a, b in blocks:
        c, v = codes[a:b], visible[a:b]
        n = b - a
        juego = (c == H) | (c == A)
        dentro = np.zeros(n, bool)  # dentro de un hueco en juego de MINIMO_HUECO o más
        reaparece = np.zeros(n, bool)  # al reaparecer tras uno de esos huecos
        for s, e in _rachas(~v):
            en_juego = (s > 0 and e < n and juego[s - 1:e + 1].all())
            if not en_juego:
                acc["huecos pegados a un D o al borde"] += 1
                continue
            t = tramo(e - s)
            acc[("hueco", t, "huecos")] += 1
            fin = min(n - 1, e + TRAS)
            despues = c[fin] if juego[fin] else c[e]
            if c[s - 1] != despues:
                acc[("hueco", t, "con cambio")] += 1
                trozo = c[s - 1:fin + 1]
                k = int(np.flatnonzero(trozo[1:] != trozo[:-1])[0]) + s  # primer cambio desde s
                if k < e:
                    acc[("hueco", t, "cambio dentro")] += 1
                else:
                    acc[("hueco", t, "cambio al reaparecer")] += 1
            if e - s >= MINIMO_HUECO:
                dentro[s:e] = True
                reaparece[e:fin + 1] = True
        reaparece &= ~dentro
        cambio = np.zeros(n, bool)
        cambio[1:] = juego[1:] & juego[:-1] & (c[1:] != c[:-1])
        acc["cambios"] += int(cambio.sum())
        acc["cambios dentro de un hueco"] += int((cambio & dentro).sum())
        acc["cambios al reaparecer"] += int((cambio & reaparece).sum())
        acc["cambios en otro sitio"] += int((cambio & ~dentro & ~reaparece).sum())
        acc["frames de juego"] += int(juego.sum())
        acc["frames de juego dentro de un hueco"] += int((juego & dentro).sum())
        acc["frames de juego al reaparecer"] += int((juego & reaparece).sum())
    return acc


def razon(acc):
    """(M, M al azar, R): % de nuestros cambios dentro de un hueco o al reaparecer, lo mismo para frames de juego
    al azar, y su cociente. None si no hay cambios."""
    if not acc["cambios"] or not acc["frames de juego"]:
        return None
    m = 100.0 * (acc["cambios dentro de un hueco"] + acc["cambios al reaparecer"]) / acc["cambios"]
    azar = 100.0 * (acc["frames de juego dentro de un hueco"] + acc["frames de juego al reaparecer"]) / acc["frames de juego"]
    return m, azar, (m / azar if azar else None)


TRAMOS_F = ("0,5–2 s", "2–5 s", "5–15 s")  # los huecos de la fracción F


def fraccion_con_cambio(acc):
    """(F, huecos): % de los huecos en juego de 0,5 a 15 s tras los que decimos otro equipo, y cuántos son."""
    n = sum(acc[("hueco", t, "huecos")] for t in TRAMOS_F)
    cc = sum(acc[("hueco", t, "con cambio")] for t in TRAMOS_F)
    return (100.0 * cc / n if n else None), n


def celda(n, suprimir, minimo=5):
    return "< {}".format(minimo) if suprimir and 0 < n < minimo else str(n)


def pct(n, total, suprimir, minimo=5):
    if not total or (suprimir and 0 < n < minimo):
        return "–"
    return "{:.1f} %".format(100.0 * n / total).replace(".", ",")


def lineas(nombre, acc, suprimir):
    """Las tablas de una fuente. Con `suprimir`, una celda de 1 a 4 casos sale como «< 5» (el partido)."""
    salida = ["### {}".format(nombre), "",
              "| duración del hueco en juego | huecos | decimos otro equipo después | de esos: cambio dentro del hueco "
              "| de esos: cambio al reaparecer (≤ 0,5 s) |", "|---|---|---|---|---|"]
    for _, _, t in TRAMOS:
        n = acc[("hueco", t, "huecos")]
        cc = acc[("hueco", t, "con cambio")]
        salida.append("| {} | {} | {} ({}) | {} | {} |".format(
            t, celda(n, suprimir), celda(cc, suprimir), pct(cc, n, suprimir),
            pct(acc[("hueco", t, "cambio dentro")], cc, suprimir), pct(acc[("hueco", t, "cambio al reaparecer")], cc,
                                                                      suprimir)))
    salida += ["", "Huecos pegados a un `D` nuestro o al borde de un tramo (no cuentan): {}.".format(
        celda(acc["huecos pegados a un D o al borde"], suprimir)), ""]
    total = acc["cambios"]
    salida += ["| nuestros cambios `H`↔`A` | cuántos | % | al azar (% de los frames de juego) |", "|---|---|---|---|",
               "| todos | {} | – | – |".format(celda(total, suprimir)),
               "| dentro de un hueco en juego de ≥ 0,5 s | {} | {} | {} |".format(
                   celda(acc["cambios dentro de un hueco"], suprimir), pct(acc["cambios dentro de un hueco"], total, suprimir),
                   pct(acc["frames de juego dentro de un hueco"], acc["frames de juego"], False)),
               "| al reaparecer tras uno de esos (≤ 0,5 s) | {} | {} | {} |".format(
                   celda(acc["cambios al reaparecer"], suprimir), pct(acc["cambios al reaparecer"], total, suprimir),
                   pct(acc["frames de juego al reaparecer"], acc["frames de juego"], False)),
               "| en otro sitio | {} | {} | – |".format(celda(acc["cambios en otro sitio"], suprimir),
                                                      pct(acc["cambios en otro sitio"], total, suprimir))]
    def coma(x, cifras):
        return "{:.{}f}".format(x, cifras).replace(".", ",")
    r = razon(acc)
    if r is not None and r[2] is not None:
        salida += ["", "M (dentro o al reaparecer) = {} % de los cambios; al azar, {} %; R = M / azar = {}.".format(
            coma(r[0], 1), coma(r[1], 1), coma(r[2], 2))]
    f, n = fraccion_con_cambio(acc)
    con = sum(acc[("hueco", t, "con cambio")] for t in TRAMOS_F)
    if f is not None and suprimir and (0 < n < 5 or 0 < con < 5):
        # Con 1 a 4 huecos con cambio, el porcentaje deja ver una celda pequeña (15/11: la primera ejecución lo hizo).
        salida.append("F: menos de 5 casos, no se imprime.")
    elif f is not None:
        salida.append("F = {} % de los {} huecos en juego de 0,5 a 15 s tienen otro equipo después.".format(coma(f, 1), n))
    return salida


def oculta_f(acc):
    """¿Hay que ocultar F en la salida del partido? Sí si sale de 1 a 4 huecos, o de 1 a 4 huecos con cambio."""
    n = sum(acc[("hueco", t, "huecos")] for t in TRAMOS_F)
    con = sum(acc[("hueco", t, "con cambio")] for t in TRAMOS_F)
    return 0 < n < 5 or 0 < con < 5
