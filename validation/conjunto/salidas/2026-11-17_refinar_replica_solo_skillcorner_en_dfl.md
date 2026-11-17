# Refinamientos de K2 sin reentrenar · DFL · 7 partidos

Código: c377501 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `pesos_r_solo_sc.npz` (sha256 bdb014153e0dcf39…), de un modelo que solo vio SkillCorner. B5: el pliegue que no vio el partido (sí vio otros de la DFL).
α de K2: 4, la de «todos» · este script: sha256 d37f2cd30c97b99d…

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.645 | 0.645 | -0.083 [-0.097 a -0.070] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.443 | 0.443 | -0.056 [-0.067 a -0.044] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.678 | 0.678 | -0.070 [-0.083 a -0.057] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.475 | 0.475 | -0.038 [-0.049 a -0.027] | 1 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD | control | 0.623 | 0.566 | 0.566 | -0.057 [-0.070 a -0.043] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD | flag | 0.414 | 0.374 | 0.374 | -0.040 [-0.049 a -0.029] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.603 | 0.603 | -0.048 [-0.061 a -0.034] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.406 | 0.406 | -0.025 [-0.035 a -0.015] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.556 | 0.556 | -0.031 [-0.043 a -0.019] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.365 | 0.365 | -0.030 [-0.039 a -0.020] | 0 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.592 | 0.592 | -0.021 [-0.033 a -0.009] | 1 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.396 | 0.396 | -0.013 [-0.023 a -0.005] | 1 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |

Posesiones predichas en la primera celda: K2, 1753 · K2, 1753 · `main`, 1661 (reales: 1736).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.645 | 0.728 | -0.000 [-0.009 a +0.009] | 4 de 7 | +0.083 [+0.073 a +0.094] | 7 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.443 | 0.479 | -0.020 [-0.028 a -0.012] | 1 de 7 | +0.036 [+0.027 a +0.044] | 7 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.678 | 0.756 | +0.008 [+0.000 a +0.016] | 5 de 7 | +0.078 [+0.068 a +0.088] | 7 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.475 | 0.505 | -0.007 [-0.013 a +0.000] | 3 de 7 | +0.031 [+0.022 a +0.040] | 5 de 7 |
| propio | como el ATD | control | 0.623 | 0.566 | 0.623 | -0.000 [-0.010 a +0.009] | 4 de 7 | +0.057 [+0.047 a +0.067] | 7 de 7 |
| propio | como el ATD | flag | 0.414 | 0.374 | 0.397 | -0.017 [-0.024 a -0.010] | 1 de 7 | +0.022 [+0.015 a +0.030] | 7 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.603 | 0.655 | +0.005 [-0.003 a +0.013] | 5 de 7 | +0.053 [+0.042 a +0.063] | 7 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.406 | 0.422 | -0.009 [-0.015 a -0.003] | 2 de 7 | +0.016 [+0.008 a +0.024] | 6 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.556 | 0.587 | -0.001 [-0.009 a +0.008] | 4 de 7 | +0.030 [+0.021 a +0.039] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.365 | 0.379 | -0.015 [-0.022 a -0.009] | 0 de 7 | +0.014 [+0.007 a +0.020] | 6 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.592 | 0.620 | +0.008 [+0.001 a +0.014] | 4 de 7 | +0.029 [+0.019 a +0.037] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.396 | 0.403 | -0.006 [-0.012 a -0.000] | 1 de 7 | +0.007 [+0.000 a +0.014] | 6 de 7 |

Posesiones predichas en la primera celda: K3, 1582 · K2, 1753 · `main`, 1661 (reales: 1736).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.645 | 0.644 | -0.084 [-0.098 a -0.071] | 0 de 7 | -0.001 [-0.005 a +0.003] | 3 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.443 | 0.437 | -0.061 [-0.073 a -0.050] | 0 de 7 | -0.005 [-0.009 a -0.002] | 2 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.678 | 0.675 | -0.073 [-0.086 a -0.060] | 0 de 7 | -0.003 [-0.007 a +0.002] | 2 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.475 | 0.470 | -0.042 [-0.055 a -0.032] | 0 de 7 | -0.005 [-0.009 a -0.001] | 2 de 7 |
| propio | como el ATD | control | 0.623 | 0.566 | 0.569 | -0.054 [-0.068 a -0.040] | 0 de 7 | +0.003 [-0.001 a +0.008] | 6 de 7 |
| propio | como el ATD | flag | 0.414 | 0.374 | 0.373 | -0.041 [-0.050 a -0.031] | 0 de 7 | -0.001 [-0.005 a +0.003] | 4 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.603 | 0.604 | -0.047 [-0.060 a -0.033] | 0 de 7 | +0.001 [-0.004 a +0.006] | 3 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.406 | 0.404 | -0.027 [-0.036 a -0.017] | 0 de 7 | -0.001 [-0.005 a +0.002] | 3 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.556 | 0.559 | -0.028 [-0.040 a -0.016] | 1 de 7 | +0.003 [-0.001 a +0.007] | 4 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.365 | 0.367 | -0.027 [-0.037 a -0.018] | 0 de 7 | +0.002 [-0.001 a +0.006] | 5 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.592 | 0.595 | -0.017 [-0.029 a -0.005] | 1 de 7 | +0.004 [-0.000 a +0.008] | 4 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.396 | 0.398 | -0.011 [-0.020 a -0.002] | 1 de 7 | +0.002 [-0.001 a +0.005] | 5 de 7 |

Posesiones predichas en la primera celda: K4, 1749 · K2, 1753 · `main`, 1661 (reales: 1736).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.645 | 0.729 | +0.001 [-0.009 a +0.010] | 5 de 7 | +0.085 [+0.075 a +0.095] | 7 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.443 | 0.477 | -0.021 [-0.029 a -0.014] | 1 de 7 | +0.035 [+0.026 a +0.043] | 7 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.678 | 0.757 | +0.009 [+0.001 a +0.017] | 6 de 7 | +0.079 [+0.069 a +0.089] | 7 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.475 | 0.503 | -0.009 [-0.016 a -0.002] | 2 de 7 | +0.028 [+0.020 a +0.037] | 6 de 7 |
| propio | como el ATD | control | 0.623 | 0.566 | 0.624 | +0.001 [-0.008 a +0.011] | 4 de 7 | +0.058 [+0.048 a +0.069] | 7 de 7 |
| propio | como el ATD | flag | 0.414 | 0.374 | 0.397 | -0.017 [-0.025 a -0.010] | 1 de 7 | +0.022 [+0.015 a +0.030] | 7 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.603 | 0.656 | +0.005 [-0.002 a +0.014] | 5 de 7 | +0.053 [+0.042 a +0.064] | 7 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.406 | 0.421 | -0.009 [-0.015 a -0.003] | 2 de 7 | +0.016 [+0.008 a +0.024] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.556 | 0.588 | +0.001 [-0.008 a +0.010] | 3 de 7 | +0.032 [+0.023 a +0.041] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.365 | 0.379 | -0.016 [-0.022 a -0.009] | 1 de 7 | +0.014 [+0.007 a +0.020] | 6 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.592 | 0.620 | +0.007 [-0.001 a +0.014] | 4 de 7 | +0.028 [+0.019 a +0.037] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.396 | 0.401 | -0.008 [-0.013 a -0.002] | 2 de 7 | +0.005 [-0.001 a +0.012] | 5 de 7 |

Posesiones predichas en la primera celda: K5, 1580 · K2, 1753 · `main`, 1661 (reales: 1736).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.645 | 0.737 | +0.009 [+0.002 a +0.016] | 5 de 7 | +0.092 [+0.080 a +0.104] | 7 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.443 | 0.489 | -0.009 [-0.015 a -0.003] | 2 de 7 | +0.047 [+0.037 a +0.057] | 7 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.678 | 0.761 | +0.013 [+0.008 a +0.019] | 6 de 7 | +0.083 [+0.071 a +0.094] | 7 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.475 | 0.509 | -0.003 [-0.008 a +0.002] | 3 de 7 | +0.034 [+0.024 a +0.045] | 6 de 7 |
| propio | como el ATD | control | 0.623 | 0.566 | 0.632 | +0.008 [+0.002 a +0.015] | 6 de 7 | +0.066 [+0.054 a +0.077] | 7 de 7 |
| propio | como el ATD | flag | 0.414 | 0.374 | 0.407 | -0.007 [-0.012 a -0.002] | 2 de 7 | +0.033 [+0.024 a +0.042] | 7 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.603 | 0.664 | +0.013 [+0.008 a +0.019] | 7 de 7 | +0.061 [+0.048 a +0.073] | 7 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.406 | 0.428 | -0.002 [-0.007 a +0.002] | 3 de 7 | +0.023 [+0.014 a +0.031] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.556 | 0.594 | +0.007 [+0.001 a +0.013] | 5 de 7 | +0.038 [+0.028 a +0.048] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.365 | 0.388 | -0.006 [-0.012 a -0.002] | 2 de 7 | +0.023 [+0.015 a +0.031] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.592 | 0.625 | +0.013 [+0.008 a +0.018] | 5 de 7 | +0.034 [+0.023 a +0.044] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.396 | 0.408 | -0.001 [-0.006 a +0.003] | 4 de 7 | +0.012 [+0.004 a +0.020] | 6 de 7 |

Posesiones predichas en la primera celda: K3 con 1/4 de K2, 1604 · K2, 1753 · `main`, 1661 (reales: 1736).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.645 | 0.702 | -0.026 [-0.038 a -0.015] | 0 de 7 | +0.057 [+0.049 a +0.065] | 7 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.443 | 0.466 | -0.032 [-0.041 a -0.023] | 0 de 7 | +0.024 [+0.017 a +0.031] | 7 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.678 | 0.735 | -0.013 [-0.023 a -0.003] | 0 de 7 | +0.057 [+0.049 a +0.065] | 7 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.475 | 0.497 | -0.016 [-0.024 a -0.007] | 1 de 7 | +0.022 [+0.015 a +0.029] | 7 de 7 |
| propio | como el ATD | control | 0.623 | 0.566 | 0.605 | -0.018 [-0.030 a -0.007] | 1 de 7 | +0.039 [+0.031 a +0.047] | 7 de 7 |
| propio | como el ATD | flag | 0.414 | 0.374 | 0.388 | -0.026 [-0.034 a -0.017] | 0 de 7 | +0.014 [+0.008 a +0.020] | 7 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.603 | 0.644 | -0.007 [-0.017 a +0.003] | 2 de 7 | +0.041 [+0.033 a +0.048] | 7 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.406 | 0.418 | -0.012 [-0.020 a -0.004] | 1 de 7 | +0.013 [+0.007 a +0.019] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.556 | 0.575 | -0.013 [-0.023 a -0.003] | 2 de 7 | +0.018 [+0.012 a +0.024] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.365 | 0.373 | -0.022 [-0.030 a -0.013] | 0 de 7 | +0.008 [+0.003 a +0.013] | 6 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.592 | 0.612 | -0.000 [-0.010 a +0.009] | 4 de 7 | +0.021 [+0.014 a +0.027] | 7 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.396 | 0.402 | -0.007 [-0.015 a -0.000] | 2 de 7 | +0.006 [+0.001 a +0.011] | 6 de 7 |

Posesiones predichas en la primera celda: K3 con 3/4 de K2, 1615 · K2, 1753 · `main`, 1661 (reales: 1736).

## El otro proveedor (frente a `main`; «quita la pérdida» es −0.005 o más en todas las celdas)

- K2: peor celda -0.0834 · media -0.0426 · **pierde más de 0.005 en alguna celda**
- K3: peor celda -0.0199 · media -0.0046 · **pierde más de 0.005 en alguna celda**
- K4: peor celda -0.0844 · media -0.0427 · **pierde más de 0.005 en alguna celda**
- K5: peor celda -0.0213 · media -0.0047 · **pierde más de 0.005 en alguna celda**
- K3 con 1/4 de K2: peor celda -0.0090 · media +0.0028 · **pierde más de 0.005 en alguna celda**
- K3 con 3/4 de K2: peor celda -0.0323 · media -0.0160 · **pierde más de 0.005 en alguna celda**
