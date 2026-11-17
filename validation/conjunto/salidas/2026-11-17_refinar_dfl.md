# Refinamientos de K2 sin reentrenar · DFL · 7 partidos

Código: d96fce8 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `conjunto_pesos.npz` (sha256 6d16316f85063f13…): cada partido con el pliegue que no lo vio. B5: el pliegue que no vio el partido (sí vio otros de la DFL).

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.780 | 0.780 | +0.051 [+0.040 a +0.064] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.542 | 0.542 | +0.044 [+0.034 a +0.054] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.794 | 0.794 | +0.046 [+0.035 a +0.057] | 6 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.549 | 0.549 | +0.037 [+0.027 a +0.046] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD | control | 0.623 | 0.668 | 0.668 | +0.045 [+0.035 a +0.057] | 6 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD | flag | 0.414 | 0.457 | 0.457 | +0.043 [+0.034 a +0.052] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.686 | 0.686 | +0.036 [+0.024 a +0.047] | 6 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.464 | 0.464 | +0.033 [+0.024 a +0.042] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.631 | 0.631 | +0.044 [+0.032 a +0.055] | 6 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.430 | 0.430 | +0.035 [+0.027 a +0.044] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.648 | 0.648 | +0.035 [+0.024 a +0.046] | 6 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.438 | 0.438 | +0.029 [+0.020 a +0.037] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |

Posesiones predichas en la primera celda: 1651 · K2, 1651 · `main`, 1661 (reales: 1736).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.780 | 0.782 | +0.054 [+0.045 a +0.063] | 7 de 7 | +0.003 [-0.005 a +0.010] | 3 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.542 | 0.529 | +0.031 [+0.023 a +0.039] | 7 de 7 | -0.013 [-0.020 a -0.007] | 1 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.794 | 0.794 | +0.047 [+0.038 a +0.054] | 7 de 7 | +0.000 [-0.008 a +0.009] | 2 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.549 | 0.536 | +0.024 [+0.017 a +0.031] | 7 de 7 | -0.013 [-0.020 a -0.007] | 2 de 7 |
| propio | como el ATD | control | 0.623 | 0.668 | 0.665 | +0.042 [+0.034 a +0.050] | 7 de 7 | -0.003 [-0.011 a +0.005] | 3 de 7 |
| propio | como el ATD | flag | 0.414 | 0.457 | 0.439 | +0.025 [+0.018 a +0.032] | 7 de 7 | -0.018 [-0.024 a -0.011] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.686 | 0.683 | +0.032 [+0.025 a +0.040] | 7 de 7 | -0.003 [-0.012 a +0.005] | 2 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.464 | 0.448 | +0.017 [+0.011 a +0.024] | 7 de 7 | -0.016 [-0.023 a -0.010] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.631 | 0.627 | +0.040 [+0.032 a +0.048] | 7 de 7 | -0.004 [-0.012 a +0.004] | 3 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.430 | 0.417 | +0.022 [+0.015 a +0.028] | 7 de 7 | -0.013 [-0.020 a -0.007] | 2 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.648 | 0.642 | +0.029 [+0.022 a +0.037] | 6 de 7 | -0.006 [-0.014 a +0.002] | 2 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.438 | 0.422 | +0.013 [+0.007 a +0.020] | 6 de 7 | -0.015 [-0.022 a -0.009] | 1 de 7 |

Posesiones predichas en la primera celda: 1597 · K2, 1651 · `main`, 1661 (reales: 1736).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.780 | 0.788 | +0.060 [+0.049 a +0.071] | 7 de 7 | +0.009 [+0.005 a +0.013] | 6 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.542 | 0.545 | +0.047 [+0.037 a +0.057] | 7 de 7 | +0.003 [-0.001 a +0.007] | 6 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.794 | 0.800 | +0.052 [+0.041 a +0.063] | 7 de 7 | +0.006 [+0.002 a +0.010] | 5 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.549 | 0.551 | +0.039 [+0.029 a +0.048] | 7 de 7 | +0.002 [-0.002 a +0.005] | 4 de 7 |
| propio | como el ATD | control | 0.623 | 0.668 | 0.671 | +0.048 [+0.037 a +0.059] | 7 de 7 | +0.003 [-0.001 a +0.007] | 4 de 7 |
| propio | como el ATD | flag | 0.414 | 0.457 | 0.455 | +0.041 [+0.032 a +0.051] | 7 de 7 | -0.001 [-0.005 a +0.003] | 2 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.686 | 0.689 | +0.038 [+0.027 a +0.049] | 6 de 7 | +0.002 [-0.002 a +0.006] | 5 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.464 | 0.463 | +0.033 [+0.024 a +0.042] | 7 de 7 | -0.001 [-0.004 a +0.003] | 3 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.631 | 0.633 | +0.046 [+0.034 a +0.057] | 6 de 7 | +0.002 [-0.003 a +0.006] | 5 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.430 | 0.430 | +0.036 [+0.026 a +0.044] | 7 de 7 | +0.000 [-0.003 a +0.004] | 3 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.648 | 0.650 | +0.037 [+0.026 a +0.048] | 6 de 7 | +0.002 [-0.002 a +0.006] | 4 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.438 | 0.439 | +0.030 [+0.021 a +0.039] | 7 de 7 | +0.001 [-0.002 a +0.005] | 4 de 7 |

Posesiones predichas en la primera celda: 1643 · K2, 1651 · `main`, 1661 (reales: 1736).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.780 | 0.780 | +0.051 [+0.043 a +0.060] | 7 de 7 | +0.000 [-0.008 a +0.007] | 2 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.542 | 0.530 | +0.031 [+0.024 a +0.039] | 7 de 7 | -0.012 [-0.020 a -0.006] | 1 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.794 | 0.794 | +0.046 [+0.037 a +0.054] | 7 de 7 | -0.000 [-0.008 a +0.008] | 3 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.549 | 0.538 | +0.026 [+0.019 a +0.033] | 7 de 7 | -0.010 [-0.018 a -0.004] | 2 de 7 |
| propio | como el ATD | control | 0.623 | 0.668 | 0.663 | +0.040 [+0.032 a +0.047] | 7 de 7 | -0.006 [-0.014 a +0.003] | 2 de 7 |
| propio | como el ATD | flag | 0.414 | 0.457 | 0.438 | +0.024 [+0.018 a +0.030] | 7 de 7 | -0.018 [-0.025 a -0.012] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.686 | 0.682 | +0.032 [+0.024 a +0.040] | 7 de 7 | -0.004 [-0.012 a +0.004] | 3 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.464 | 0.449 | +0.018 [+0.012 a +0.024] | 7 de 7 | -0.015 [-0.022 a -0.009] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.631 | 0.629 | +0.042 [+0.034 a +0.050] | 7 de 7 | -0.002 [-0.010 a +0.006] | 3 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.430 | 0.416 | +0.021 [+0.015 a +0.028] | 7 de 7 | -0.014 [-0.021 a -0.007] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.648 | 0.644 | +0.031 [+0.024 a +0.039] | 6 de 7 | -0.004 [-0.012 a +0.004] | 2 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.438 | 0.424 | +0.015 [+0.009 a +0.021] | 6 de 7 | -0.013 [-0.020 a -0.006] | 2 de 7 |

Posesiones predichas en la primera celda: 1602 · K2, 1651 · `main`, 1661 (reales: 1736).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.780 | 0.769 | +0.041 [+0.034 a +0.048] | 7 de 7 | -0.011 [-0.020 a -0.001] | 2 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.542 | 0.517 | +0.018 [+0.013 a +0.024] | 7 de 7 | -0.026 [-0.035 a -0.018] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.794 | 0.780 | +0.033 [+0.027 a +0.039] | 7 de 7 | -0.013 [-0.024 a -0.004] | 2 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.549 | 0.527 | +0.015 [+0.010 a +0.020] | 7 de 7 | -0.022 [-0.030 a -0.014] | 0 de 7 |
| propio | como el ATD | control | 0.623 | 0.668 | 0.652 | +0.029 [+0.024 a +0.035] | 7 de 7 | -0.016 [-0.026 a -0.006] | 2 de 7 |
| propio | como el ATD | flag | 0.414 | 0.457 | 0.429 | +0.015 [+0.010 a +0.020] | 7 de 7 | -0.027 [-0.036 a -0.020] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.686 | 0.673 | +0.022 [+0.016 a +0.028] | 7 de 7 | -0.014 [-0.023 a -0.003] | 2 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.464 | 0.441 | +0.011 [+0.006 a +0.016] | 7 de 7 | -0.022 [-0.031 a -0.015] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.631 | 0.613 | +0.026 [+0.021 a +0.032] | 7 de 7 | -0.018 [-0.028 a -0.008] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.430 | 0.406 | +0.011 [+0.007 a +0.016] | 6 de 7 | -0.024 [-0.032 a -0.016] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.648 | 0.630 | +0.017 [+0.013 a +0.023] | 7 de 7 | -0.018 [-0.028 a -0.008] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.438 | 0.416 | +0.007 [+0.003 a +0.012] | 5 de 7 | -0.021 [-0.029 a -0.013] | 0 de 7 |

Posesiones predichas en la primera celda: 1589 · K2, 1651 · `main`, 1661 (reales: 1736).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.780 | 0.784 | +0.056 [+0.046 a +0.065] | 7 de 7 | +0.005 [-0.001 a +0.010] | 5 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.542 | 0.537 | +0.038 [+0.030 a +0.047] | 7 de 7 | -0.005 [-0.011 a -0.001] | 2 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.794 | 0.799 | +0.051 [+0.041 a +0.060] | 7 de 7 | +0.005 [-0.001 a +0.011] | 5 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.549 | 0.543 | +0.031 [+0.023 a +0.039] | 7 de 7 | -0.005 [-0.010 a -0.000] | 1 de 7 |
| propio | como el ATD | control | 0.623 | 0.668 | 0.667 | +0.044 [+0.034 a +0.053] | 7 de 7 | -0.001 [-0.007 a +0.004] | 2 de 7 |
| propio | como el ATD | flag | 0.414 | 0.457 | 0.446 | +0.032 [+0.024 a +0.040] | 7 de 7 | -0.011 [-0.016 a -0.006] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.686 | 0.684 | +0.034 [+0.024 a +0.043] | 6 de 7 | -0.002 [-0.008 a +0.004] | 3 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.464 | 0.454 | +0.024 [+0.016 a +0.031] | 7 de 7 | -0.009 [-0.015 a -0.004] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.631 | 0.633 | +0.046 [+0.036 a +0.054] | 6 de 7 | +0.002 [-0.005 a +0.008] | 4 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.430 | 0.424 | +0.029 [+0.022 a +0.037] | 7 de 7 | -0.006 [-0.011 a -0.001] | 2 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.648 | 0.649 | +0.036 [+0.027 a +0.045] | 6 de 7 | +0.001 [-0.005 a +0.008] | 4 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.438 | 0.432 | +0.023 [+0.015 a +0.030] | 7 de 7 | -0.006 [-0.011 a -0.000] | 3 de 7 |

Posesiones predichas en la primera celda: 1615 · K2, 1651 · `main`, 1661 (reales: 1736).

## La regla en la DFL (límite de daño del 16/11, frente a `main`)

- K2: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas) **pasa** · punto 3 (flag, no pierde más de 0.005) **pasa** · balón a la vista en los `D` (no pierde más de 0.005) **pasa** · media con control +0.0447
- K3: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas) **pasa** · punto 3 (flag, no pierde más de 0.005) **pasa** · balón a la vista en los `D` (no pierde más de 0.005) **pasa** · media con control +0.0439
- K4: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas) **pasa** · punto 3 (flag, no pierde más de 0.005) **pasa** · balón a la vista en los `D` (no pierde más de 0.005) **pasa** · media con control +0.0497
- K5: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas) **pasa** · punto 3 (flag, no pierde más de 0.005) **pasa** · balón a la vista en los `D` (no pierde más de 0.005) **pasa** · media con control +0.0422
- K4 frente a K2: media en las celdas que cuentan +0.0051 (se pide +0.003) y peor celda -0.0012 (se pide −0.002 o más): **pasa**
