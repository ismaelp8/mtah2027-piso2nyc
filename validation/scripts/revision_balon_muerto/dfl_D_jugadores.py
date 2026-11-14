"""¿Sirven los jugadores solos para detectar D? Medido en un partido abierto de la DFL (datos de otro
partido, CC BY 4.0). Sin usar el balón (en la DFL está congelado durante el D y delataría la etiqueta).
Solo imprime agregados. Umbrales elegidos en una parte y evaluados en la otra."""
import os, sys, json, datetime, itertools
import numpy as np
from lxml import etree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
sys.path.insert(0, os.path.join(ROOT, "validation", "experimento0"))
import possession_metrics as pm
import dfl_lector
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression

FPS = 25
PARTIDO = sys.argv[1] if len(sys.argv) > 1 else "J03WMX"
REINICIOS = ("ThrowIn", "FreeKick", "GoalKick", "CornerKick", "KickOff", "Penalty", "RefereeBall")

def ms(texto):
    return int(round(datetime.datetime.fromisoformat(texto).timestamp() * 1000))

def leer_eventos(ruta):
    raiz = etree.parse(ruta).getroot()
    out = []
    for e in raiz.findall("Event"):
        if not len(e) or e.get("EventTime") is None or e[0].tag == "Delete":
            continue
        out.append((e[0].tag, ms(e.get("EventTime"))))
    return out

def a_frame(t_ms, m):
    i = int(np.clip(np.searchsorted(t_ms, m), 1, len(t_ms) - 1))
    return i if abs(t_ms[i] - m) < abs(t_ms[i - 1] - m) else i - 1

def mov_avg(v, w):
    """Media móvil centrada de ancho 2w+1, ignorando NaN."""
    v = np.asarray(v, float)
    ok = ~np.isnan(v)
    c1 = np.concatenate(([0.0], np.cumsum(np.where(ok, v, 0.0))))
    c0 = np.concatenate(([0.0], np.cumsum(ok.astype(float))))
    i = np.arange(len(v)); lo = np.maximum(0, i - w); hi = np.minimum(len(v), i + w + 1)
    num = c1[hi] - c1[lo]; den = c0[hi] - c0[lo]
    return np.where(den > 0, num / np.maximum(den, 1), np.nan)

def runs(mask):
    m = np.asarray(mask, bool)
    d = np.diff(np.concatenate(([0], m.astype(int), [0])))
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))

def rasgos(parte, campo):
    L, W = campo
    X = np.concatenate([parte["equipos"]["local"]["x"], parte["equipos"]["visitante"]["x"]], axis=1).astype(float)
    Y = np.concatenate([parte["equipos"]["local"]["y"], parte["equipos"]["visitante"]["y"]], axis=1).astype(float)
    nl = parte["equipos"]["local"]["x"].shape[1]
    n = X.shape[0]
    V = np.full_like(X, np.nan)
    V[2:-2] = np.hypot(X[4:] - X[:-4], Y[4:] - Y[:-4]) / (4.0 / FPS)
    with np.errstate(all="ignore"):
        tracked = np.sum(~np.isnan(V), axis=1)
        vmean = np.nanmean(V, axis=1)
        vp75 = np.nanpercentile(V, 75, axis=1)
        vmax = np.nanmax(V, axis=1)
        slow = np.sum(V < 1.0, axis=1) / np.maximum(tracked, 1)
        fuera = np.sum((np.abs(X) > L / 2 + 0.3) | (np.abs(Y) > W / 2 + 0.3), axis=1)
        caja1 = np.sum((X > L / 2 - 16.5) & (np.abs(Y) < 20.16), axis=1)
        caja2 = np.sum((X < -L / 2 + 16.5) & (np.abs(Y) < 20.16), axis=1)
        cxl, cyl = np.nanmean(X[:, :nl], axis=1), np.nanmean(Y[:, :nl], axis=1)
        cxv, cyv = np.nanmean(X[:, nl:], axis=1), np.nanmean(Y[:, nl:], axis=1)
        dcent = np.hypot(cxl - cxv, cyl - cyv)
        spread = (np.nanstd(X[:, :nl], axis=1) + np.nanstd(X[:, nl:], axis=1) + np.nanstd(Y[:, :nl], axis=1) + np.nanstd(Y[:, nl:], axis=1)) / 4
        # ¿cada equipo entero en su mitad? (saque inicial)
        propio = np.minimum(np.nanmean(X[:, :nl] < 0, axis=1), 1) ; propio = np.maximum(propio, 1 - propio)
        propio_v = np.nanmean(X[:, nl:] < 0, axis=1); propio_v = np.maximum(propio_v, 1 - propio_v)
    F = {
        "v_media": vmean, "v_media_1s": mov_avg(vmean, 12), "v_media_2s": mov_avg(vmean, 25), "v_media_4s": mov_avg(vmean, 50),
        "frac_lentos_2s": mov_avg(slow, 25), "v_p75_2s": mov_avg(vp75, 25), "v_max_2s": mov_avg(vmax, 25),
        "fuera_2s": mov_avg(fuera, 25), "caja_max_2s": mov_avg(np.maximum(caja1, caja2), 25),
        "dist_centroides_2s": mov_avg(dcent, 25), "dispersion_2s": mov_avg(spread, 25),
        "en_su_mitad_2s": mov_avg(np.minimum(propio, propio_v), 25),
    }
    return F

def etiquetas(parte):
    e = np.asarray(parte["estado"]); p = np.asarray(parte["poss"])
    gt = np.full(len(e), pm.X, dtype=np.int8)
    gt[e == 0] = pm.D
    gt[(e == 1) & (p == 1)] = pm.H
    gt[(e == 1) & (p == 2)] = pm.A
    return gt

def ffill(team):
    """team: array con -1 donde no hay equipo; rellena hacia delante (y hacia atrás al principio)."""
    t = team.copy(); idx = np.where(t >= 0, np.arange(len(t)), -1)
    idx = np.maximum.accumulate(idx)
    first = np.flatnonzero(t >= 0)[0]
    idx[idx < 0] = first
    return t[idx]

def bfill(team):
    return ffill(team[::-1])[::-1]

def con_mascara(gt, mask_d, modo="previo"):
    """Etiquetas con equipo oráculo y el D de la máscara. Donde la máscara dice vivo y la GT es D,
    se arrastra el equipo previo ('previo') o se adelanta el que reanuda ('siguiente')."""
    team = np.where(gt == pm.D, -1, gt).astype(np.int8)
    filled = ffill(team) if modo == "previo" else bfill(team)
    pred = np.where(mask_d, pm.D, filled).astype(np.int8)
    return pred

def histeresis(score, on, off, min_d, min_vivo, mayor_es_d=False):
    """D cuando score < on hasta que score > off (o al revés si mayor_es_d). Luego quita D cortos y
    huecos vivos cortos."""
    s = np.nan_to_num(score, nan=np.inf if not mayor_es_d else -np.inf)
    if mayor_es_d: s = -s; on, off = -on, -off
    d = np.zeros(len(s), bool); en = False
    for i in range(len(s)):
        if not en and s[i] < on: en = True
        elif en and s[i] > off: en = False
        d[i] = en
    # rellenar huecos vivos cortos dentro de D
    for a, b in runs(~d):
        if b - a < min_vivo and a > 0 and b < len(d): d[a:b] = True
    for a, b in runs(d):
        if b - a < min_d: d[a:b] = False
    return d

def spell(gt, pred):
    return pm.evaluate(gt, pred)["spell_f1_mean"]

def nivel_parada(gt, mask_d):
    """Recall de paradas, latencias de inicio y fin, D espurios."""
    true = runs(gt == pm.D); pred = runs(mask_d)
    det, lat_ini, lat_fin = 0, [], []
    for a, b in true:
        best, ov = None, 0
        for c, d in pred:
            o = max(0, min(b, d) - max(a, c))
            if o > ov: ov, best = o, (c, d)
        if ov >= 0.5 * (b - a):
            det += 1; lat_ini.append(best[0] - a); lat_fin.append(best[1] - b)
    espurios = sum(1 for c, d in pred if all(min(b, d) - max(a, c) <= 0 for a, b in true))
    q = lambda v: "p10/p50/p90 = {:+.0f}/{:+.0f}/{:+.0f} frames".format(*np.percentile(v, [10, 50, 90])) if v else "—"
    return {"paradas": len(true), "detectadas": det, "espurios": espurios, "lat_ini": q(lat_ini), "lat_fin": q(lat_fin),
            "abs_ini_le_25": float(np.mean(np.abs(lat_ini) <= 25)) if lat_ini else 0,
            "abs_fin_le_25": float(np.mean(np.abs(lat_fin) <= 25)) if lat_fin else 0}

def main():
    datos = dfl_lector.cargar_cache(PARTIDO)
    meta = datos["meta"]; campo = tuple(meta["campo"])
    eventos = leer_eventos(dfl_lector.rutas_partido(PARTIDO)["eventos"])
    print("Partido {} ({}–{}), campo {:.1f} × {:.1f} m".format(PARTIDO, meta["local"], meta["visitante"], *campo))
    partes = {}
    for k in (1, 2):
        p = datos["partes"][k]
        gt = etiquetas(p); F = rasgos(p, campo)
        partes[k] = {"gt": gt, "F": F, "t_ms": np.asarray(p["t_ms"], np.int64), "poss": np.asarray(p["poss"])}
        dsegs = runs(gt == pm.D)
        minutos_vivos = np.sum(gt != pm.D) / FPS / 60
        print("\nParte {}: {} frames, {:.1f} % D, {} paradas, {:.1f} min de balón vivo".format(
            k, len(gt), 100 * np.mean(gt == pm.D), len(dsegs), minutos_vivos))
        print("   D de apertura (antes del saque): {:.1f} s   D de cierre (tras el pitido final): {:.1f} s".format(
            (dsegs[0][1] - dsegs[0][0]) / FPS if dsegs and dsegs[0][0] == 0 else 0,
            (dsegs[-1][1] - dsegs[-1][0]) / FPS if dsegs and dsegs[-1][1] == len(gt) else 0))
        # equipo antes y después de cada parada interior
        mismo = 0; interiores = 0
        for a, b in dsegs:
            if a == 0 or b == len(gt): continue
            interiores += 1; mismo += int(gt[a - 1] == gt[b])
        print("   paradas interiores {}: el mismo equipo a los dos lados en {:.0f} %".format(interiores, 100 * mismo / max(interiores, 1)))
        # tipo de reinicio al final de cada parada (±5 s)
        tipos = {}
        for a, b in dsegs:
            if b == len(gt): continue
            cerca = [(abs(a_frame(partes[k]["t_ms"], m) - b), tipo) for tipo, m in eventos if tipo in REINICIOS and abs(a_frame(partes[k]["t_ms"], m) - b) <= 5 * FPS]
            tipos[(a, b)] = min(cerca)[1] if cerca else "sin evento"
        partes[k]["tipos"] = tipos
        y = (gt == pm.D).astype(int)
        print("   AUC por frame (D frente a vivo), solo jugadores:")
        for nombre, v in F.items():
            ok = ~np.isnan(v)
            auc = roc_auc_score(y[ok], v[ok])
            print("      {:<20} {:.3f}  (mediana en D {:.2f}, en vivo {:.2f})".format(nombre, max(auc, 1 - auc), np.nanmedian(v[y == 1]), np.nanmedian(v[y == 0])))

    print("\n== Referencias con equipo oráculo (spellF1) ==")
    for k in (1, 2):
        gt = partes[k]["gt"]
        sin = np.zeros(len(gt), bool)
        v1 = np.zeros(len(gt), bool); first_alive = np.flatnonzero(gt != pm.D)[0]; v1[:first_alive] = True
        print("   parte {}: D perfecto {:.3f} | sin D {:.3f} | solo el D previo al saque (como la v1 de Manuel) {:.3f} | sin D adelantando el equipo que reanuda {:.3f}".format(
            k, spell(gt, con_mascara(gt, gt == pm.D)), spell(gt, con_mascara(gt, sin)), spell(gt, con_mascara(gt, v1)), spell(gt, con_mascara(gt, sin, "siguiente"))))

    print("\n== Detector 1: velocidad media de los jugadores (2 s) con histéresis, umbral elegido en la otra parte ==")
    rejilla = list(itertools.product(np.arange(0.8, 2.01, 0.1), (0.2, 0.4), (50, 125), (25, 50)))
    for entrena, prueba in ((1, 2), (2, 1)):
        gtE, FE = partes[entrena]["gt"], partes[entrena]["F"]
        mejor = max(rejilla, key=lambda c: spell(gtE, con_mascara(gtE, histeresis(FE["v_media_2s"], c[0], c[0] + c[1], c[2], c[3]))))
        on, delta, min_d, min_vivo = mejor
        gtP, FP = partes[prueba]["gt"], partes[prueba]["F"]
        mask = histeresis(FP["v_media_2s"], on, on + delta, min_d, min_vivo)
        r = pm.evaluate(gtP, con_mascara(gtP, mask)); r2 = pm.evaluate(gtP, con_mascara(gtP, mask, "siguiente"))
        np_ = nivel_parada(gtP, mask)
        print("   entrena parte {} -> prueba parte {}: on={:.1f} m/s off={:.1f} min_D={} min_vivo={}".format(entrena, prueba, on, on + delta, min_d, min_vivo))
        print("      spellF1 (equipo oráculo, arrastre previo) {:.3f}   (adelantando el que reanuda) {:.3f}   macroF1 {:.3f}   D F1 por frame {:.3f}".format(
            r["spell_f1_mean"], r2["spell_f1_mean"], r["macro_f1"], r["per_class"]["D"]["f1"] if "per_class" in r else float("nan")))
        print("      paradas {} detectadas (≥50 %) {}   D espurios {}   latencia inicio {}   fin {}   |ini|≤1 s {:.0f} %  |fin|≤1 s {:.0f} %".format(
            np_["paradas"], np_["detectadas"], np_["espurios"], np_["lat_ini"], np_["lat_fin"], 100 * np_["abs_ini_le_25"], 100 * np_["abs_fin_le_25"]))
        # por tipo de reinicio
        tipos = partes[prueba]["tipos"]; por_tipo = {}
        for (a, b), tipo in tipos.items():
            ov = np.sum(mask[a:b]) >= 0.5 * (b - a)
            por_tipo.setdefault(tipo, [0, 0]); por_tipo[tipo][0] += 1; por_tipo[tipo][1] += int(ov)
        print("      por tipo de reinicio (n, detectadas): " + ", ".join("{} {}/{}".format(t, v[1], v[0]) for t, v in sorted(por_tipo.items(), key=lambda kv: -kv[1][0])))

    print("\n== Detector 2: regresión logística con rasgos de jugadores (2 s), entrenada en la otra parte ==")
    nombres = ["v_media_1s", "v_media_2s", "v_media_4s", "frac_lentos_2s", "v_p75_2s", "v_max_2s", "fuera_2s", "caja_max_2s", "dist_centroides_2s", "dispersion_2s", "en_su_mitad_2s"]
    def matriz(F):
        M = np.column_stack([F[n] for n in nombres]); return np.nan_to_num(M, nan=0.0)
    for entrena, prueba in ((1, 2), (2, 1)):
        gtE = partes[entrena]["gt"]; XE = matriz(partes[entrena]["F"]); yE = (gtE == pm.D).astype(int)
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(XE, yE)
        gtP = partes[prueba]["gt"]; XP = matriz(partes[prueba]["F"])
        prob = mov_avg(clf.predict_proba(XP)[:, 1], 12)
        auc = roc_auc_score((gtP == pm.D).astype(int), prob)
        # umbral/histéresis elegidos en la parte de entrenamiento
        probE = mov_avg(clf.predict_proba(XE)[:, 1], 12)
        rejilla2 = list(itertools.product((0.4, 0.5, 0.6), (0.1, 0.2), (50, 125), (25, 50)))
        mejor = max(rejilla2, key=lambda c: spell(gtE, con_mascara(gtE, histeresis(probE, c[0], c[0] - c[1], c[2], c[3], mayor_es_d=True))))
        on, delta, min_d, min_vivo = mejor
        mask = histeresis(prob, on, on - delta, min_d, min_vivo, mayor_es_d=True)
        r = pm.evaluate(gtP, con_mascara(gtP, mask)); r2 = pm.evaluate(gtP, con_mascara(gtP, mask, "siguiente"))
        np_ = nivel_parada(gtP, mask)
        print("   entrena parte {} -> prueba parte {}: AUC {:.3f}; on={:.1f} off={:.1f} min_D={} min_vivo={}".format(entrena, prueba, auc, on, on - delta, min_d, min_vivo))
        print("      spellF1 (equipo oráculo, arrastre previo) {:.3f}   (adelantando el que reanuda) {:.3f}   macroF1 {:.3f}".format(r["spell_f1_mean"], r2["spell_f1_mean"], r["macro_f1"]))
        print("      paradas {} detectadas (≥50 %) {}   D espurios {}   latencia inicio {}   fin {}   |ini|≤1 s {:.0f} %  |fin|≤1 s {:.0f} %".format(
            np_["paradas"], np_["detectadas"], np_["espurios"], np_["lat_ini"], np_["lat_fin"], 100 * np_["abs_ini_le_25"], 100 * np_["abs_fin_le_25"]))
        tipos = partes[prueba]["tipos"]; por_tipo = {}
        for (a, b), tipo in tipos.items():
            ov = np.sum(mask[a:b]) >= 0.5 * (b - a)
            por_tipo.setdefault(tipo, [0, 0]); por_tipo[tipo][0] += 1; por_tipo[tipo][1] += int(ov)
        print("      por tipo de reinicio (n, detectadas): " + ", ".join("{} {}/{}".format(t, v[1], v[0]) for t, v in sorted(por_tipo.items(), key=lambda kv: -kv[1][0])))
        coef = sorted(zip(nombres, clf.coef_[0]), key=lambda kv: -abs(kv[1]))
        print("      coeficientes (sin estandarizar) por |peso|: " + ", ".join("{} {:+.2f}".format(n, c) for n, c in coef[:5]))

if __name__ == "__main__":
    main()
