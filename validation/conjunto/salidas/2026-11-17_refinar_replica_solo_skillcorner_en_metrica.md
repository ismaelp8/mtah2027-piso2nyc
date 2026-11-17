# Refinamientos de K2 sin reentrenar · Metrica · 3 partidos

Código: c377501 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `pesos_r_solo_sc.npz` (sha256 bdb014153e0dcf39…), de un modelo que solo vio SkillCorner. B5: los coeficientes de la entrega (nunca vio este proveedor).
α de K2: 4, la de «todos» · este script: sha256 d37f2cd30c97b99d…

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.644 | 0.644 | -0.024 [-0.046 a -0.002] | 1 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.634 | 0.634 | -0.019 [-0.041 a +0.002] | 1 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| propio | tal cual | eventos | 0.542 | 0.516 | 0.516 | -0.025 [-0.043 a -0.009] | 1 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.501 | 0.501 | -0.026 [-0.044 a -0.009] | 1 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |

Posesiones predichas en la primera celda: K2, 680 · K2, 680 · `main`, 612 (reales: 879).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.644 | 0.682 | +0.014 [+0.001 a +0.027] | 2 de 3 | +0.038 [+0.020 a +0.055] | 3 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.634 | 0.659 | +0.007 [-0.007 a +0.019] | 1 de 3 | +0.026 [+0.008 a +0.042] | 3 de 3 |
| propio | tal cual | eventos | 0.542 | 0.516 | 0.542 | +0.001 [-0.011 a +0.012] | 1 de 3 | +0.026 [+0.011 a +0.041] | 3 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.501 | 0.522 | -0.006 [-0.016 a +0.004] | 1 de 3 | +0.021 [+0.007 a +0.035] | 3 de 3 |

Posesiones predichas en la primera celda: K3, 615 · K2, 680 · `main`, 612 (reales: 879).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.644 | 0.659 | -0.009 [-0.033 a +0.014] | 1 de 3 | +0.015 [+0.007 a +0.023] | 3 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.634 | 0.637 | -0.015 [-0.038 a +0.008] | 1 de 3 | +0.004 [-0.003 a +0.012] | 3 de 3 |
| propio | tal cual | eventos | 0.542 | 0.516 | 0.529 | -0.013 [-0.031 a +0.006] | 1 de 3 | +0.013 [+0.006 a +0.020] | 3 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.501 | 0.505 | -0.022 [-0.040 a -0.005] | 0 de 3 | +0.004 [-0.003 a +0.011] | 2 de 3 |

Posesiones predichas en la primera celda: K4, 688 · K2, 680 · `main`, 612 (reales: 879).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.644 | 0.682 | +0.014 [+0.001 a +0.027] | 2 de 3 | +0.037 [+0.020 a +0.054] | 3 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.634 | 0.659 | +0.006 [-0.007 a +0.019] | 1 de 3 | +0.025 [+0.008 a +0.042] | 3 de 3 |
| propio | tal cual | eventos | 0.542 | 0.516 | 0.542 | +0.001 [-0.010 a +0.013] | 1 de 3 | +0.026 [+0.012 a +0.041] | 3 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.501 | 0.520 | -0.007 [-0.017 a +0.003] | 1 de 3 | +0.019 [+0.005 a +0.033] | 3 de 3 |

Posesiones predichas en la primera celda: K5, 613 · K2, 680 · `main`, 612 (reales: 879).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.644 | 0.677 | +0.009 [+0.001 a +0.017] | 2 de 3 | +0.033 [+0.013 a +0.052] | 2 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.634 | 0.659 | +0.006 [-0.002 a +0.015] | 2 de 3 | +0.025 [+0.006 a +0.045] | 2 de 3 |
| propio | tal cual | eventos | 0.542 | 0.516 | 0.544 | +0.003 [-0.004 a +0.009] | 2 de 3 | +0.028 [+0.012 a +0.045] | 3 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.501 | 0.523 | -0.004 [-0.012 a +0.003] | 1 de 3 | +0.022 [+0.007 a +0.037] | 3 de 3 |

Posesiones predichas en la primera celda: K3 con 1/4 de K2, 600 · K2, 680 · `main`, 612 (reales: 879).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.644 | 0.669 | +0.002 [-0.018 a +0.020] | 1 de 3 | +0.025 [+0.014 a +0.036] | 3 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.634 | 0.662 | +0.010 [-0.009 a +0.027] | 1 de 3 | +0.028 [+0.016 a +0.041] | 3 de 3 |
| propio | tal cual | eventos | 0.542 | 0.516 | 0.527 | -0.015 [-0.030 a -0.001] | 1 de 3 | +0.010 [+0.001 a +0.019] | 3 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.501 | 0.510 | -0.017 [-0.032 a -0.004] | 1 de 3 | +0.009 [-0.002 a +0.019] | 2 de 3 |

Posesiones predichas en la primera celda: K3 con 3/4 de K2, 633 · K2, 680 · `main`, 612 (reales: 879).

## El otro proveedor (frente a `main`; «quita la pérdida» es −0.005 o más en todas las celdas)

- K2: peor celda -0.0262 · media -0.0236 · **pierde más de 0.005 en alguna celda**
- K3: peor celda -0.0055 · media +0.0039 · **pierde más de 0.005 en alguna celda**
- K4: peor celda -0.0225 · media -0.0149 · **pierde más de 0.005 en alguna celda**
- K5: peor celda -0.0072 · media +0.0034 · **pierde más de 0.005 en alguna celda**
- K3 con 1/4 de K2: peor celda -0.0040 · media +0.0035 · **quita la pérdida**
- K3 con 3/4 de K2: peor celda -0.0174 · media -0.0054 · **pierde más de 0.005 en alguna celda**
