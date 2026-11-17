# Refinamientos de K2 sin reentrenar · DFL · 7 partidos

Código: 925311d · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `conjunto_pesos.npz` (sha256 6d16316f85063f13…): cada partido con el pliegue que no lo vio. B5: el pliegue que no vio el partido (sí vio otros de la DFL).
α de K2: la de la entrega, 4, igual que la de B5 en la mezcla (4); los pesos, los del pliegue · este script: sha256 32a0c2d4217872dc…

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.785 | 0.785 | +0.057 [+0.045 a +0.069] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.541 | 0.541 | +0.043 [+0.033 a +0.053] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.801 | 0.801 | +0.053 [+0.042 a +0.064] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.548 | 0.548 | +0.036 [+0.027 a +0.046] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD | control | 0.623 | 0.673 | 0.673 | +0.050 [+0.039 a +0.062] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD | flag | 0.414 | 0.455 | 0.455 | +0.041 [+0.033 a +0.051] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.692 | 0.692 | +0.041 [+0.030 a +0.052] | 6 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.463 | 0.463 | +0.032 [+0.024 a +0.042] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.636 | 0.636 | +0.049 [+0.037 a +0.060] | 6 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.427 | 0.427 | +0.033 [+0.024 a +0.041] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.652 | 0.652 | +0.040 [+0.028 a +0.050] | 6 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.435 | 0.435 | +0.026 [+0.017 a +0.034] | 7 de 7 | +0.000 [+0.000 a +0.000] | 0 de 7 |

Posesiones predichas en la primera celda: K2, 1633 · K2, 1633 · `main`, 1661 (reales: 1736).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.785 | 0.784 | +0.056 [+0.047 a +0.064] | 7 de 7 | -0.001 [-0.009 a +0.007] | 3 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.541 | 0.524 | +0.025 [+0.019 a +0.033] | 7 de 7 | -0.017 [-0.025 a -0.010] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.801 | 0.796 | +0.048 [+0.040 a +0.056] | 7 de 7 | -0.005 [-0.014 a +0.004] | 1 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.548 | 0.533 | +0.021 [+0.015 a +0.028] | 7 de 7 | -0.015 [-0.023 a -0.008] | 1 de 7 |
| propio | como el ATD | control | 0.623 | 0.673 | 0.665 | +0.042 [+0.034 a +0.049] | 7 de 7 | -0.008 [-0.017 a +0.000] | 1 de 7 |
| propio | como el ATD | flag | 0.414 | 0.455 | 0.433 | +0.019 [+0.013 a +0.024] | 7 de 7 | -0.023 [-0.030 a -0.015] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.692 | 0.684 | +0.034 [+0.026 a +0.041] | 7 de 7 | -0.007 [-0.016 a +0.001] | 2 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.463 | 0.445 | +0.014 [+0.009 a +0.020] | 7 de 7 | -0.018 [-0.025 a -0.011] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.636 | 0.627 | +0.040 [+0.032 a +0.047] | 7 de 7 | -0.009 [-0.017 a -0.001] | 2 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.427 | 0.411 | +0.016 [+0.011 a +0.022] | 7 de 7 | -0.016 [-0.023 a -0.009] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.652 | 0.643 | +0.031 [+0.023 a +0.038] | 7 de 7 | -0.009 [-0.017 a -0.001] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.435 | 0.422 | +0.013 [+0.007 a +0.019] | 6 de 7 | -0.013 [-0.019 a -0.006] | 2 de 7 |

Posesiones predichas en la primera celda: K3, 1575 · K2, 1633 · `main`, 1661 (reales: 1736).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.785 | 0.793 | +0.065 [+0.054 a +0.077] | 7 de 7 | +0.009 [+0.005 a +0.013] | 7 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.541 | 0.542 | +0.044 [+0.034 a +0.054] | 7 de 7 | +0.001 [-0.003 a +0.005] | 4 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.801 | 0.805 | +0.058 [+0.046 a +0.069] | 7 de 7 | +0.005 [+0.001 a +0.009] | 5 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.548 | 0.549 | +0.037 [+0.027 a +0.046] | 7 de 7 | +0.001 [-0.003 a +0.004] | 4 de 7 |
| propio | como el ATD | control | 0.623 | 0.673 | 0.676 | +0.053 [+0.042 a +0.064] | 7 de 7 | +0.004 [-0.001 a +0.008] | 5 de 7 |
| propio | como el ATD | flag | 0.414 | 0.455 | 0.453 | +0.039 [+0.030 a +0.048] | 7 de 7 | -0.002 [-0.006 a +0.002] | 3 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.692 | 0.693 | +0.043 [+0.031 a +0.054] | 6 de 7 | +0.002 [-0.002 a +0.005] | 5 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.463 | 0.462 | +0.032 [+0.023 a +0.041] | 7 de 7 | -0.001 [-0.004 a +0.003] | 3 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.636 | 0.636 | +0.049 [+0.037 a +0.060] | 7 de 7 | +0.000 [-0.004 a +0.004] | 4 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.427 | 0.428 | +0.033 [+0.024 a +0.042] | 7 de 7 | +0.000 [-0.004 a +0.004] | 4 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.652 | 0.652 | +0.039 [+0.028 a +0.050] | 6 de 7 | -0.000 [-0.005 a +0.004] | 3 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.435 | 0.437 | +0.028 [+0.020 a +0.037] | 7 de 7 | +0.003 [-0.001 a +0.006] | 5 de 7 |

Posesiones predichas en la primera celda: K4, 1623 · K2, 1633 · `main`, 1661 (reales: 1736).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.785 | 0.781 | +0.053 [+0.045 a +0.061] | 7 de 7 | -0.004 [-0.012 a +0.005] | 1 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.541 | 0.526 | +0.027 [+0.021 a +0.034] | 7 de 7 | -0.016 [-0.024 a -0.008] | 1 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.801 | 0.794 | +0.047 [+0.039 a +0.054] | 7 de 7 | -0.006 [-0.015 a +0.002] | 1 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.548 | 0.536 | +0.024 [+0.017 a +0.031] | 7 de 7 | -0.012 [-0.020 a -0.006] | 2 de 7 |
| propio | como el ATD | control | 0.623 | 0.673 | 0.663 | +0.039 [+0.033 a +0.046] | 7 de 7 | -0.010 [-0.020 a -0.001] | 1 de 7 |
| propio | como el ATD | flag | 0.414 | 0.455 | 0.433 | +0.019 [+0.014 a +0.025] | 7 de 7 | -0.022 [-0.029 a -0.015] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.692 | 0.682 | +0.031 [+0.023 a +0.038] | 7 de 7 | -0.010 [-0.019 a -0.002] | 1 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.463 | 0.446 | +0.015 [+0.010 a +0.021] | 7 de 7 | -0.017 [-0.024 a -0.011] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.636 | 0.627 | +0.040 [+0.032 a +0.047] | 7 de 7 | -0.009 [-0.018 a -0.000] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.427 | 0.413 | +0.018 [+0.013 a +0.024] | 7 de 7 | -0.014 [-0.021 a -0.007] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.652 | 0.644 | +0.032 [+0.025 a +0.039] | 7 de 7 | -0.008 [-0.016 a +0.000] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.435 | 0.423 | +0.014 [+0.009 a +0.020] | 7 de 7 | -0.011 [-0.018 a -0.005] | 2 de 7 |

Posesiones predichas en la primera celda: K5, 1584 · K2, 1633 · `main`, 1661 (reales: 1736).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.785 | 0.762 | +0.034 [+0.028 a +0.041] | 7 de 7 | -0.022 [-0.032 a -0.012] | 1 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.541 | 0.511 | +0.013 [+0.008 a +0.018] | 7 de 7 | -0.030 [-0.039 a -0.022] | 0 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.801 | 0.775 | +0.028 [+0.022 a +0.034] | 7 de 7 | -0.025 [-0.035 a -0.015] | 1 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.548 | 0.524 | +0.011 [+0.006 a +0.016] | 6 de 7 | -0.025 [-0.034 a -0.017] | 0 de 7 |
| propio | como el ATD | control | 0.623 | 0.673 | 0.647 | +0.024 [+0.019 a +0.029] | 7 de 7 | -0.026 [-0.036 a -0.016] | 1 de 7 |
| propio | como el ATD | flag | 0.414 | 0.455 | 0.424 | +0.010 [+0.006 a +0.014] | 7 de 7 | -0.031 [-0.040 a -0.023] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.692 | 0.669 | +0.019 [+0.013 a +0.024] | 7 de 7 | -0.022 [-0.032 a -0.012] | 1 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.463 | 0.438 | +0.008 [+0.004 a +0.012] | 5 de 7 | -0.025 [-0.033 a -0.017] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.636 | 0.609 | +0.022 [+0.017 a +0.026] | 7 de 7 | -0.027 [-0.037 a -0.017] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.427 | 0.403 | +0.008 [+0.004 a +0.012] | 5 de 7 | -0.025 [-0.032 a -0.016] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.652 | 0.628 | +0.015 [+0.011 a +0.020] | 7 de 7 | -0.025 [-0.034 a -0.015] | 1 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.435 | 0.415 | +0.006 [+0.002 a +0.011] | 6 de 7 | -0.019 [-0.027 a -0.012] | 0 de 7 |

Posesiones predichas en la primera celda: K3 con 1/4 de K2, 1589 · K2, 1633 · `main`, 1661 (reales: 1736).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.785 | 0.786 | +0.058 [+0.048 a +0.067] | 7 de 7 | +0.002 [-0.004 a +0.007] | 5 de 7 |
| etiquetas | como el ATD | flag | 0.498 | 0.541 | 0.536 | +0.038 [+0.030 a +0.047] | 7 de 7 | -0.005 [-0.010 a +0.001] | 1 de 7 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.801 | 0.800 | +0.052 [+0.042 a +0.061] | 7 de 7 | -0.001 [-0.007 a +0.005] | 4 de 7 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.548 | 0.543 | +0.031 [+0.023 a +0.039] | 7 de 7 | -0.005 [-0.010 a +0.000] | 2 de 7 |
| propio | como el ATD | control | 0.623 | 0.673 | 0.671 | +0.048 [+0.039 a +0.057] | 7 de 7 | -0.002 [-0.009 a +0.005] | 2 de 7 |
| propio | como el ATD | flag | 0.414 | 0.455 | 0.446 | +0.032 [+0.024 a +0.039] | 7 de 7 | -0.010 [-0.015 a -0.004] | 0 de 7 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.692 | 0.687 | +0.036 [+0.026 a +0.045] | 7 de 7 | -0.005 [-0.012 a +0.001] | 2 de 7 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.463 | 0.453 | +0.023 [+0.016 a +0.030] | 7 de 7 | -0.010 [-0.015 a -0.004] | 0 de 7 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.636 | 0.632 | +0.045 [+0.036 a +0.054] | 7 de 7 | -0.003 [-0.010 a +0.003] | 3 de 7 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.427 | 0.421 | +0.026 [+0.019 a +0.034] | 7 de 7 | -0.007 [-0.012 a -0.001] | 2 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.652 | 0.649 | +0.036 [+0.027 a +0.045] | 6 de 7 | -0.004 [-0.010 a +0.002] | 2 de 7 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.435 | 0.430 | +0.021 [+0.013 a +0.028] | 6 de 7 | -0.005 [-0.010 a +0.000] | 3 de 7 |

Posesiones predichas en la primera celda: K3 con 3/4 de K2, 1607 · K2, 1633 · `main`, 1661 (reales: 1736).

## La regla en la DFL (límite de daño del 16/11, frente a `main`)

- K2: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas) **pasa** · punto 3 (flag, no pierde más de 0.005) **pasa** · balón a la vista en los `D` (no pierde más de 0.005) **pasa** · media con control +0.0501
- K3: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas) **pasa** · punto 3 (flag, no pierde más de 0.005) **pasa** · balón a la vista en los `D` (no pierde más de 0.005) **pasa** · media con control +0.0449
- K4: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas) **pasa** · punto 3 (flag, no pierde más de 0.005) **pasa** · balón a la vista en los `D` (no pierde más de 0.005) **pasa** · media con control +0.0548
- K5: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas) **pasa** · punto 3 (flag, no pierde más de 0.005) **pasa** · balón a la vista en los `D` (no pierde más de 0.005) **pasa** · media con control +0.0425
- K4 frente a K2: media en las celdas que cuentan +0.0047 (se pide +0.003) y peor celda -0.0023 (se pide −0.002 o más): **no pasa**
