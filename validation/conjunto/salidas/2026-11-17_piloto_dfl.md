# Modelo conjunto frente a `main` · tanda «piloto1» · DFL · 1 partidos

Código: b4ec45f · bootstrap pareado de 200 · `main` = B5, `dead_state` y `decode_cortas_a_d`.

## Candidato K1

γ elegida para cada partido con los otros: 8 en 1. Con los 1: 8.

| `D` | condición | etiquetas | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / main / reales |
|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.752 | +0.024 [+0.006 a +0.043] | 1 de 1 | 253 / 234 / 261 |
| etiquetas | como el ATD | flag | 0.440 | 0.475 | +0.035 [+0.022 a +0.054] | 1 de 1 | 253 / 234 / 511 |
| etiquetas | como el ATD, sin bloques | control | 0.745 | 0.763 | +0.018 [-0.004 a +0.042] | 1 de 1 | 261 / 237 / 261 |
| etiquetas | como el ATD, sin bloques | flag | 0.452 | 0.487 | +0.034 [+0.019 a +0.055] | 1 de 1 | 261 / 237 / 511 |
| propio | como el ATD | control | 0.637 | 0.673 | +0.036 [+0.015 a +0.057] | 1 de 1 | 218 / 204 / 261 |
| propio | como el ATD | flag | 0.370 | 0.405 | +0.036 [+0.023 a +0.052] | 1 de 1 | 218 / 204 / 511 |
| propio | como el ATD, sin bloques | control | 0.667 | 0.696 | +0.029 [+0.008 a +0.052] | 1 de 1 | 222 / 206 / 261 |
| propio | como el ATD, sin bloques | flag | 0.385 | 0.422 | +0.036 [+0.025 a +0.054] | 1 de 1 | 222 / 206 / 511 |
| propio, balón a la vista en los D | como el ATD | control | 0.603 | 0.625 | +0.023 [+0.004 a +0.043] | 1 de 1 | 234 / 217 / 261 |
| propio, balón a la vista en los D | como el ATD | flag | 0.356 | 0.387 | +0.031 [+0.019 a +0.047] | 1 de 1 | 234 / 217 / 511 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.631 | 0.649 | +0.018 [-0.004 a +0.039] | 1 de 1 | 241 / 221 / 261 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.374 | 0.403 | +0.029 [+0.017 a +0.046] | 1 de 1 | 241 / 221 / 511 |

Regla: punto 1 (control, +0.005 y 1 de 1 en las 4 celdas): **pasa** · punto 3 (flag, no pierde más de 0.005): **pasa** · balón a la vista en los `D` (no pierde más de 0.005 con ninguna convención): **pasa**.

Los valores de γ, uno a uno (descriptivo; diferencia con `main` y en cuántos gana):

| γ | control, como el ATD, `D` etiquetas | flag, como el ATD, `D` etiquetas | control, como el ATD, sin bloques, `D` etiquetas | flag, como el ATD, sin bloques, `D` etiquetas | control, como el ATD, `D` propio | flag, como el ATD, `D` propio | control, como el ATD, sin bloques, `D` propio | flag, como el ATD, sin bloques, `D` propio |
|---|---|---|---|---|---|---|---|---|
| 2 | +0.009 (1) | +0.008 (1) | +0.008 (1) | +0.008 (1) | +0.002 (1) | +0.005 (1) | +0.006 (1) | +0.006 (1) |
| 4 | +0.025 (1) | +0.021 (1) | +0.019 (1) | +0.020 (1) | +0.020 (1) | +0.017 (1) | +0.023 (1) | +0.019 (1) |
| 8 | +0.024 (1) | +0.035 (1) | +0.018 (1) | +0.034 (1) | +0.036 (1) | +0.036 (1) | +0.029 (1) | +0.036 (1) |

## Candidato K2

α elegida para cada partido con los otros: 8 en 1. Con los 1: 8.

| `D` | condición | etiquetas | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / main / reales |
|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.807 | +0.079 [+0.045 a +0.112] | 1 de 1 | 250 / 234 / 261 |
| etiquetas | como el ATD | flag | 0.440 | 0.494 | +0.054 [+0.033 a +0.082] | 1 de 1 | 250 / 234 / 511 |
| etiquetas | como el ATD, sin bloques | control | 0.745 | 0.813 | +0.068 [+0.040 a +0.098] | 1 de 1 | 255 / 237 / 261 |
| etiquetas | como el ATD, sin bloques | flag | 0.452 | 0.502 | +0.050 [+0.027 a +0.073] | 1 de 1 | 255 / 237 / 511 |
| propio | como el ATD | control | 0.637 | 0.707 | +0.070 [+0.038 a +0.097] | 1 de 1 | 227 / 204 / 261 |
| propio | como el ATD | flag | 0.370 | 0.418 | +0.048 [+0.028 a +0.072] | 1 de 1 | 227 / 204 / 511 |
| propio | como el ATD, sin bloques | control | 0.667 | 0.719 | +0.052 [+0.024 a +0.082] | 1 de 1 | 229 / 206 / 261 |
| propio | como el ATD, sin bloques | flag | 0.385 | 0.430 | +0.045 [+0.025 a +0.067] | 1 de 1 | 229 / 206 / 511 |
| propio, balón a la vista en los D | como el ATD | control | 0.603 | 0.675 | +0.073 [+0.041 a +0.103] | 1 de 1 | 233 / 217 / 261 |
| propio, balón a la vista en los D | como el ATD | flag | 0.356 | 0.402 | +0.046 [+0.027 a +0.067] | 1 de 1 | 233 / 217 / 511 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.631 | 0.680 | +0.049 [+0.018 a +0.075] | 1 de 1 | 238 / 221 / 261 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.374 | 0.411 | +0.037 [+0.020 a +0.057] | 1 de 1 | 238 / 221 / 511 |

Regla: punto 1 (control, +0.005 y 1 de 1 en las 4 celdas): **pasa** · punto 3 (flag, no pierde más de 0.005): **pasa** · balón a la vista en los `D` (no pierde más de 0.005 con ninguna convención): **pasa**.

Los valores de α, uno a uno (descriptivo; diferencia con `main` y en cuántos gana):

| α | control, como el ATD, `D` etiquetas | flag, como el ATD, `D` etiquetas | control, como el ATD, sin bloques, `D` etiquetas | flag, como el ATD, sin bloques, `D` etiquetas | control, como el ATD, `D` propio | flag, como el ATD, `D` propio | control, como el ATD, sin bloques, `D` propio | flag, como el ATD, sin bloques, `D` propio |
|---|---|---|---|---|---|---|---|---|
| 0.0625 | -0.077 (0) | -0.032 (0) | -0.089 (0) | -0.022 (0) | -0.032 (0) | -0.014 (0) | -0.045 (0) | -0.004 (0) |
| 0.125 | -0.014 (0) | -0.010 (0) | -0.028 (0) | -0.004 (0) | -0.010 (0) | -0.009 (0) | -0.019 (0) | -0.004 (0) |
| 0.25 | +0.025 (1) | +0.000 (1) | +0.022 (1) | +0.007 (1) | +0.017 (1) | -0.003 (0) | +0.008 (1) | +0.001 (1) |
| 0.5 | +0.078 (1) | +0.021 (1) | +0.071 (1) | +0.020 (1) | +0.049 (1) | +0.011 (1) | +0.040 (1) | +0.009 (1) |
| 1 | +0.089 (1) | +0.032 (1) | +0.083 (1) | +0.028 (1) | +0.065 (1) | +0.023 (1) | +0.054 (1) | +0.018 (1) |
| 2 | +0.079 (1) | +0.033 (1) | +0.075 (1) | +0.032 (1) | +0.065 (1) | +0.023 (1) | +0.053 (1) | +0.022 (1) |
| 4 | +0.081 (1) | +0.052 (1) | +0.074 (1) | +0.045 (1) | +0.072 (1) | +0.046 (1) | +0.054 (1) | +0.036 (1) |
| 8 | +0.079 (1) | +0.054 (1) | +0.068 (1) | +0.050 (1) | +0.070 (1) | +0.048 (1) | +0.052 (1) | +0.045 (1) |

## Veredicto con la regla (puntos 1 y 3; el 2, SkillCorner, solo se abre si pasan)

- K1: punto 1 pasa, punto 3 pasa, balón a la vista pasa → **sigue a SkillCorner**
- K2: punto 1 pasa, punto 3 pasa, balón a la vista pasa → **sigue a SkillCorner**
