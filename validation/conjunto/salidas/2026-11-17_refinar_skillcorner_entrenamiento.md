# Refinamientos de K2 sin reentrenar · SkillCorner, mitad de entrenamiento · 10 partidos

Código: 74f3191 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `conjunto_pesos.npz` (sha256 6d16316f85063f13…): cada partido con el pliegue que no lo vio. B5: los coeficientes de la entrega (nunca vio este proveedor).
α de K2: 4, la de «todos» · este script: sha256 d37f2cd30c97b99d…

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.543 | 0.543 | +0.023 [+0.015 a +0.031] | 8 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.539 | 0.539 | +0.024 [+0.016 a +0.032] | 7 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| propio | detectado | sc | 0.391 | 0.413 | 0.413 | +0.021 [+0.014 a +0.029] | 10 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.412 | 0.412 | +0.024 [+0.017 a +0.032] | 10 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |

Posesiones predichas en la primera celda: K2, 2306 · K2, 2306 · `main`, 2270 (reales: 3228).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.543 | 0.541 | +0.021 [+0.016 a +0.026] | 10 de 10 | -0.002 [-0.009 a +0.004] | 4 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.539 | 0.537 | +0.023 [+0.017 a +0.028] | 9 de 10 | -0.002 [-0.008 a +0.005] | 5 de 10 |
| propio | detectado | sc | 0.391 | 0.413 | 0.408 | +0.017 [+0.011 a +0.022] | 10 de 10 | -0.005 [-0.010 a +0.000] | 4 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.412 | 0.408 | +0.021 [+0.015 a +0.026] | 10 de 10 | -0.004 [-0.009 a +0.001] | 5 de 10 |

Posesiones predichas en la primera celda: K3, 2195 · K2, 2306 · `main`, 2270 (reales: 3228).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.543 | 0.542 | +0.022 [+0.014 a +0.030] | 8 de 10 | -0.001 [-0.004 a +0.002] | 5 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.539 | 0.541 | +0.027 [+0.019 a +0.035] | 8 de 10 | +0.003 [-0.001 a +0.006] | 7 de 10 |
| propio | detectado | sc | 0.391 | 0.413 | 0.412 | +0.020 [+0.013 a +0.028] | 9 de 10 | -0.001 [-0.003 a +0.001] | 3 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.412 | 0.412 | +0.024 [+0.016 a +0.032] | 10 de 10 | -0.001 [-0.003 a +0.002] | 5 de 10 |

Posesiones predichas en la primera celda: K4, 2287 · K2, 2306 · `main`, 2270 (reales: 3228).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.543 | 0.540 | +0.021 [+0.016 a +0.026] | 10 de 10 | -0.002 [-0.009 a +0.004] | 4 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.539 | 0.535 | +0.021 [+0.016 a +0.026] | 9 de 10 | -0.003 [-0.009 a +0.003] | 5 de 10 |
| propio | detectado | sc | 0.391 | 0.413 | 0.410 | +0.018 [+0.013 a +0.024] | 10 de 10 | -0.003 [-0.009 a +0.002] | 5 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.412 | 0.409 | +0.021 [+0.016 a +0.026] | 10 de 10 | -0.004 [-0.009 a +0.002] | 6 de 10 |

Posesiones predichas en la primera celda: K5, 2209 · K2, 2306 · `main`, 2270 (reales: 3228).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.543 | 0.531 | +0.012 [+0.008 a +0.016] | 9 de 10 | -0.011 [-0.019 a -0.004] | 3 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.539 | 0.528 | +0.013 [+0.010 a +0.017] | 9 de 10 | -0.011 [-0.018 a -0.004] | 4 de 10 |
| propio | detectado | sc | 0.391 | 0.413 | 0.404 | +0.013 [+0.010 a +0.017] | 10 de 10 | -0.008 [-0.015 a -0.002] | 4 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.412 | 0.403 | +0.015 [+0.011 a +0.019] | 9 de 10 | -0.010 [-0.016 a -0.003] | 3 de 10 |

Posesiones predichas en la primera celda: K3 con 1/4 de K2, 2220 · K2, 2306 · `main`, 2270 (reales: 3228).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.543 | 0.545 | +0.026 [+0.019 a +0.033] | 9 de 10 | +0.002 [-0.002 a +0.007] | 5 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.539 | 0.541 | +0.026 [+0.019 a +0.033] | 9 de 10 | +0.002 [-0.002 a +0.007] | 6 de 10 |
| propio | detectado | sc | 0.391 | 0.413 | 0.412 | +0.021 [+0.015 a +0.028] | 10 de 10 | -0.000 [-0.004 a +0.004] | 4 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.412 | 0.411 | +0.023 [+0.017 a +0.030] | 10 de 10 | -0.001 [-0.005 a +0.003] | 4 de 10 |

Posesiones predichas en la primera celda: K3 con 3/4 de K2, 2227 · K2, 2306 · `main`, 2270 (reales: 3228).

## La regla en SkillCorner (+0.005 y 7 de 10 en las cuatro celdas, frente a `main`)

- K2: **pasa** · peor celda +0.0214 · media +0.0233
- K3: **pasa** · peor celda +0.0166 · media +0.0202
- K4: **pasa** · peor celda +0.0204 · media +0.0233
- K5: **pasa** · peor celda +0.0182 · media +0.0202
- K4 frente a K2: media en las celdas que cuentan -0.0000 (se pide +0.003) y peor celda -0.0012 (se pide −0.002 o más): **no pasa**
