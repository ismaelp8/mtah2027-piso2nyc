# Refinamientos de K2 sin reentrenar · Metrica · 3 partidos

Código: 8409165 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `pesos_r_solo_dfl.npz` (sha256 68880ef3193064f2…), de un modelo que solo vio la DFL. B5: los coeficientes de la entrega (nunca vio este proveedor).

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.698 | 0.698 | +0.030 [+0.013 a +0.047] | 2 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.683 | 0.683 | +0.031 [+0.012 a +0.049] | 2 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| propio | tal cual | eventos | 0.542 | 0.571 | 0.571 | +0.030 [+0.015 a +0.046] | 2 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.557 | 0.557 | +0.030 [+0.015 a +0.046] | 2 de 3 | +0.000 [+0.000 a +0.000] | 0 de 3 |

Posesiones predichas en la primera celda: 649 · K2, 649 · `main`, 612 (reales: 879).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.698 | 0.703 | +0.035 [+0.021 a +0.048] | 3 de 3 | +0.005 [-0.006 a +0.016] | 2 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.683 | 0.688 | +0.036 [+0.022 a +0.050] | 3 de 3 | +0.005 [-0.007 a +0.016] | 2 de 3 |
| propio | tal cual | eventos | 0.542 | 0.571 | 0.569 | +0.028 [+0.015 a +0.040] | 3 de 3 | -0.002 [-0.012 a +0.008] | 1 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.557 | 0.553 | +0.025 [+0.013 a +0.038] | 3 de 3 | -0.005 [-0.015 a +0.006] | 1 de 3 |

Posesiones predichas en la primera celda: 620 · K2, 649 · `main`, 612 (reales: 879).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.698 | 0.700 | +0.032 [+0.016 a +0.048] | 2 de 3 | +0.002 [-0.003 a +0.007] | 2 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.683 | 0.689 | +0.037 [+0.019 a +0.054] | 2 de 3 | +0.006 [-0.000 a +0.012] | 3 de 3 |
| propio | tal cual | eventos | 0.542 | 0.571 | 0.570 | +0.028 [+0.013 a +0.044] | 2 de 3 | -0.002 [-0.008 a +0.004] | 1 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.557 | 0.561 | +0.033 [+0.018 a +0.049] | 2 de 3 | +0.003 [-0.002 a +0.009] | 2 de 3 |

Posesiones predichas en la primera celda: 644 · K2, 649 · `main`, 612 (reales: 879).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.698 | 0.698 | +0.030 [+0.017 a +0.043] | 3 de 3 | +0.000 [-0.011 a +0.012] | 1 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.683 | 0.687 | +0.035 [+0.020 a +0.049] | 3 de 3 | +0.004 [-0.008 a +0.015] | 2 de 3 |
| propio | tal cual | eventos | 0.542 | 0.571 | 0.564 | +0.022 [+0.011 a +0.034] | 3 de 3 | -0.007 [-0.018 a +0.003] | 1 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.557 | 0.547 | +0.020 [+0.007 a +0.032] | 3 de 3 | -0.010 [-0.021 a -0.000] | 1 de 3 |

Posesiones predichas en la primera celda: 617 · K2, 649 · `main`, 612 (reales: 879).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.698 | 0.690 | +0.022 [+0.012 a +0.032] | 3 de 3 | -0.008 [-0.022 a +0.006] | 1 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.683 | 0.681 | +0.029 [+0.017 a +0.041] | 3 de 3 | -0.002 [-0.017 a +0.011] | 1 de 3 |
| propio | tal cual | eventos | 0.542 | 0.571 | 0.554 | +0.013 [+0.003 a +0.022] | 3 de 3 | -0.017 [-0.031 a -0.004] | 1 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.557 | 0.546 | +0.018 [+0.009 a +0.029] | 3 de 3 | -0.012 [-0.025 a +0.001] | 1 de 3 |

Posesiones predichas en la primera celda: 613 · K2, 649 · `main`, 612 (reales: 879).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | 0.668 | 0.698 | 0.702 | +0.034 [+0.018 a +0.049] | 2 de 3 | +0.004 [-0.002 a +0.010] | 2 de 3 |
| etiquetas | suavizado 25 | eventos | 0.652 | 0.683 | 0.689 | +0.036 [+0.020 a +0.053] | 2 de 3 | +0.005 [-0.003 a +0.012] | 2 de 3 |
| propio | tal cual | eventos | 0.542 | 0.571 | 0.573 | +0.032 [+0.017 a +0.046] | 2 de 3 | +0.002 [-0.004 a +0.007] | 2 de 3 |
| propio | suavizado 25 | eventos | 0.527 | 0.557 | 0.560 | +0.033 [+0.019 a +0.048] | 3 de 3 | +0.003 [-0.004 a +0.011] | 2 de 3 |

Posesiones predichas en la primera celda: 636 · K2, 649 · `main`, 612 (reales: 879).

## El otro proveedor (frente a `main`; «quita la pérdida» es −0.005 o más en todas las celdas)

- K2: peor celda +0.0297 · media +0.0301 · gana en todas (+0.005 o más)
- K3: peor celda +0.0253 · media +0.0309 · gana en todas (+0.005 o más)
- K4: peor celda +0.0279 · media +0.0325 · gana en todas (+0.005 o más)
- K5: peor celda +0.0199 · media +0.0267 · gana en todas (+0.005 o más)
- K3 con 1/4 de K2: peor celda +0.0125 · media +0.0204 · gana en todas (+0.005 o más)
- K3 con 3/4 de K2: peor celda +0.0315 · media +0.0337 · gana en todas (+0.005 o más)
