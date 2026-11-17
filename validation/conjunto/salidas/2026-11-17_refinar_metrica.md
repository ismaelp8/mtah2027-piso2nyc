# Refinamientos de K2 sin reentrenar · Metrica · 3 partidos

Código: 74f3191 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `conjunto_pesos.npz` (sha256 6d16316f85063f13…): los de la entrega (todos los partidos). B5: los coeficientes de la entrega (nunca vio este proveedor).
α de K2: 4, la de «todos» · este script: sha256 d37f2cd30c97b99d…

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.703 | 0.703 | +0.035 [+0.019 a +0.051] | 2 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.688 | 0.688 | +0.036 [+0.020 a +0.052] | 3 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| propio | tal cual | eventos | 0.542 | 0.563 | 0.563 | +0.021 [+0.007 a +0.035] | 2 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.551 | 0.551 | +0.024 [+0.010 a +0.037] | 3 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |

Posesiones predichas en la primera celda: K2, 624 · K2, 624 · `main`, 612 (reales: 879).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.703 | 0.691 | +0.023 [+0.013 a +0.033] | 3 de 3 | -0.012 [-0.024 a +0.001] | 1 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.688 | 0.682 | +0.029 [+0.018 a +0.041] | 3 de 3 | -0.007 [-0.018 a +0.005] | 1 de 3 |
| propio | tal cual | eventos | 0.542 | 0.563 | 0.556 | +0.014 [+0.005 a +0.025] | 3 de 3 | -0.007 [-0.018 a +0.005] | 1 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.551 | 0.545 | +0.017 [+0.008 a +0.028] | 3 de 3 | -0.006 [-0.016 a +0.004] | 0 de 3 |

Posesiones predichas en la primera celda: K3, 607 · K2, 624 · `main`, 612 (reales: 879).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.703 | 0.703 | +0.035 [+0.019 a +0.050] | 3 de 3 | +0.000 [-0.007 a +0.007] | 2 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.688 | 0.691 | +0.039 [+0.022 a +0.054] | 3 de 3 | +0.003 [-0.002 a +0.008] | 3 de 3 |
| propio | tal cual | eventos | 0.542 | 0.563 | 0.566 | +0.024 [+0.010 a +0.038] | 2 de 3 | +0.003 [-0.005 a +0.010] | 2 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.551 | 0.550 | +0.022 [+0.009 a +0.036] | 3 de 3 | -0.001 [-0.008 a +0.004] | 2 de 3 |

Posesiones predichas en la primera celda: K4, 629 · K2, 624 · `main`, 612 (reales: 879).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.703 | 0.692 | +0.024 [+0.013 a +0.034] | 3 de 3 | -0.011 [-0.024 a +0.003] | 1 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.688 | 0.687 | +0.034 [+0.022 a +0.046] | 3 de 3 | -0.002 [-0.013 a +0.010] | 1 de 3 |
| propio | tal cual | eventos | 0.542 | 0.563 | 0.556 | +0.015 [+0.005 a +0.025] | 3 de 3 | -0.007 [-0.018 a +0.006] | 1 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.551 | 0.545 | +0.018 [+0.008 a +0.028] | 2 de 3 | -0.006 [-0.016 a +0.004] | 0 de 3 |

Posesiones predichas en la primera celda: K5, 607 · K2, 624 · `main`, 612 (reales: 879).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.703 | 0.679 | +0.012 [+0.005 a +0.019] | 3 de 3 | -0.024 [-0.038 a -0.008] | 1 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.688 | 0.665 | +0.013 [+0.005 a +0.021] | 3 de 3 | -0.023 [-0.037 a -0.008] | 0 de 3 |
| propio | tal cual | eventos | 0.542 | 0.563 | 0.549 | +0.007 [+0.001 a +0.014] | 2 de 3 | -0.014 [-0.027 a -0.001] | 1 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.551 | 0.538 | +0.011 [+0.003 a +0.019] | 2 de 3 | -0.013 [-0.025 a -0.001] | 0 de 3 |

Posesiones predichas en la primera celda: K3 con 1/4 de K2, 616 · K2, 624 · `main`, 612 (reales: 879).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.703 | 0.697 | +0.029 [+0.016 a +0.041] | 3 de 3 | -0.006 [-0.016 a +0.004] | 1 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.688 | 0.688 | +0.035 [+0.022 a +0.048] | 3 de 3 | -0.001 [-0.010 a +0.009] | 1 de 3 |
| propio | tal cual | eventos | 0.542 | 0.563 | 0.565 | +0.023 [+0.011 a +0.035] | 2 de 3 | +0.002 [-0.007 a +0.012] | 1 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.551 | 0.551 | +0.024 [+0.012 a +0.036] | 3 de 3 | +0.000 [-0.008 a +0.008] | 1 de 3 |

Posesiones predichas en la primera celda: K3 con 3/4 de K2, 609 · K2, 624 · `main`, 612 (reales: 879).

## El otro proveedor (frente a `main`; «quita la pérdida» es −0.005 o más en todas las celdas)

- K2: peor celda +0.0214 · media +0.0290 · gana en todas (+0.005 o más)
- K3: peor celda +0.0144 · media +0.0210 · gana en todas (+0.005 o más)
- K4: peor celda +0.0222 · media +0.0300 · gana en todas (+0.005 o más)
- K5: peor celda +0.0147 · media +0.0227 · gana en todas (+0.005 o más)
- K3 con 1/4 de K2: peor celda +0.0070 · media +0.0106 · gana en todas (+0.005 o más)
- K3 con 3/4 de K2: peor celda +0.0232 · media +0.0278 · gana en todas (+0.005 o más)
