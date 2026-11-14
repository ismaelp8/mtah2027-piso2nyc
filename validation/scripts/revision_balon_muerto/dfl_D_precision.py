"""En el partido abierto de la DFL, con equipo oráculo: qué precisión de frontera y qué tasa de detección
hacen que el D sume en spellF1. Solo agregados."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfl_D_jugadores as dj
import possession_metrics as pm
import dfl_lector

PARTIDO = sys.argv[1] if len(sys.argv) > 1 else "J03WMX"
rng = np.random.RandomState(0)
datos = dfl_lector.cargar_cache(PARTIDO)
gts = {k: dj.etiquetas(datos["partes"][k]) for k in (1, 2)}

def mask_from_segs(n, segs):
    m = np.zeros(n, bool)
    for a, b in segs:
        a, b = max(0, a), min(n, b)
        if b > a: m[a:b] = True
    return m

def media(fn):
    return float(np.mean([fn(gts[k]) for k in (1, 2)]))

def jitter(gt, s_ini, s_fin, modo="previo"):
    segs = []
    for a, b in dj.runs(gt == pm.D):
        a2 = a + (int(round(rng.normal(0, s_ini))) if a > 0 else 0)
        b2 = b + (int(round(rng.normal(0, s_fin))) if b < len(gt) else 0)
        if b2 > a2: segs.append((a2, b2))
    return dj.spell(gt, dj.con_mascara(gt, mask_from_segs(len(gt), segs), modo))

def tasa(gt, frac, modo="previo"):
    segs = [(a, b) for a, b in dj.runs(gt == pm.D) if a == 0 or b == len(gt) or rng.rand() < frac]
    return dj.spell(gt, dj.con_mascara(gt, mask_from_segs(len(gt), segs), modo))

def sesgo(gt, d_ini, d_fin, modo="previo"):
    segs = [(a + (d_ini if a > 0 else 0), b + (d_fin if b < len(gt) else 0)) for a, b in dj.runs(gt == pm.D)]
    return dj.spell(gt, dj.con_mascara(gt, mask_from_segs(len(gt), segs), modo))

print(PARTIDO + ", media de las dos partes, equipo oráculo. Referencias: D perfecto 1.000; sin D {:.3f} (arrastre) / {:.3f} (adelanta el que reanuda)".format(
    media(lambda g: dj.spell(g, dj.con_mascara(g, np.zeros(len(g), bool)))), media(lambda g: dj.spell(g, dj.con_mascara(g, np.zeros(len(g), bool), "siguiente")))))
print("\nA. Todas las paradas detectadas, fronteras con ruido N(0, sigma) [frames]  (fila: sigma del inicio; columna: sigma del fin)")
sig = (0, 6, 12, 25, 50, 100)
print("   ini\\fin " + "".join("{:>7}".format(s) for s in sig))
for si in sig:
    print("   {:>7} ".format(si) + "".join("{:7.3f}".format(media(lambda g, si=si, sf=sf: jitter(g, si, sf))) for sf in sig))
print("\nB. Fronteras exactas, solo una fracción de las paradas detectada (las demás heredan el equipo previo / adelantan el que reanuda)")
for f in (0.3, 0.5, 0.7, 0.85, 1.0):
    print("   {:>4.0f} % de las paradas: {:.3f} / {:.3f}".format(100 * f, media(lambda g, f=f: tasa(g, f)), media(lambda g, f=f: tasa(g, f, "siguiente"))))
print("\nC. Sesgo sistemático en frames (inicio, fin), todas detectadas")
for di, df in ((25, 0), (50, 0), (125, 0), (0, 25), (0, 50), (25, 25), (50, 50), (-25, 0), (0, -25), (-25, 25)):
    print("   inicio {:+4d}  fin {:+4d}: {:.3f}".format(di, df, media(lambda g, di=di, df=df: sesgo(g, di, df))))
print("\nD. Paradas por tipo de reinicio en este partido y duración mediana (s)")
ev = dj.leer_eventos(dfl_lector.rutas_partido(PARTIDO)["eventos"])
for k in (1, 2):
    gt = gts[k]; t_ms = np.asarray(datos["partes"][k]["t_ms"], np.int64)
    por = {}
    for a, b in dj.runs(gt == pm.D):
        if b == len(gt): continue
        cerca = [(abs(dj.a_frame(t_ms, m) - b), tipo) for tipo, m in ev if tipo in dj.REINICIOS and abs(dj.a_frame(t_ms, m) - b) <= 125]
        tipo = min(cerca)[1] if cerca else "sin evento"
        por.setdefault(tipo, []).append((b - a) / 25)
    print("   parte {}: ".format(k) + ", ".join("{} n={} mediana {:.1f} s".format(t, len(v), np.median(v)) for t, v in sorted(por.items(), key=lambda kv: -len(kv[1]))))
