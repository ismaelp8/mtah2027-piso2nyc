# Refinamientos de K2 sin reentrenar · SkillCorner, mitad de entrenamiento · 10 partidos

Código: 74f3191 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `pesos_r_solo_dfl.npz` (sha256 68880ef3193064f2…), de un modelo que solo vio la DFL. B5: los coeficientes de la entrega (nunca vio este proveedor).
α de K2: 4, la de «todos» · este script: sha256 d37f2cd30c97b99d…

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.515 | 0.515 | -0.005 [-0.013 a +0.003] | 4 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.515 | 0.515 | +0.001 [-0.007 a +0.009] | 5 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| propio | detectado | sc | 0.391 | 0.391 | 0.391 | -0.000 [-0.008 a +0.006] | 5 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.391 | 0.391 | +0.003 [-0.005 a +0.011] | 6 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |

Posesiones predichas en la primera celda: K2, 2491 · K2, 2491 · `main`, 2270 (reales: 3228).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.515 | 0.528 | +0.008 [+0.002 a +0.014] | 6 de 10 | +0.013 [+0.008 a +0.018] | 7 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.515 | 0.525 | +0.011 [+0.004 a +0.018] | 6 de 10 | +0.010 [+0.005 a +0.014] | 9 de 10 |
| propio | detectado | sc | 0.391 | 0.391 | 0.401 | +0.010 [+0.004 a +0.016] | 7 de 10 | +0.011 [+0.006 a +0.015] | 6 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.391 | 0.398 | +0.010 [+0.004 a +0.017] | 7 de 10 | +0.008 [+0.003 a +0.012] | 7 de 10 |

Posesiones predichas en la primera celda: K3, 2307 · K2, 2491 · `main`, 2270 (reales: 3228).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.515 | 0.510 | -0.009 [-0.017 a -0.001] | 4 de 10 | -0.004 [-0.007 a -0.002] | 4 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.515 | 0.515 | +0.001 [-0.008 a +0.009] | 6 de 10 | -0.000 [-0.003 a +0.002] | 5 de 10 |
| propio | detectado | sc | 0.391 | 0.391 | 0.390 | -0.001 [-0.009 a +0.006] | 5 de 10 | -0.001 [-0.003 a +0.002] | 6 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.391 | 0.392 | +0.004 [-0.004 a +0.011] | 6 de 10 | +0.001 [-0.002 a +0.003] | 6 de 10 |

Posesiones predichas en la primera celda: K4, 2512 · K2, 2491 · `main`, 2270 (reales: 3228).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.515 | 0.527 | +0.008 [+0.002 a +0.014] | 6 de 10 | +0.012 [+0.007 a +0.017] | 7 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.515 | 0.526 | +0.012 [+0.005 a +0.018] | 7 de 10 | +0.011 [+0.006 a +0.015] | 8 de 10 |
| propio | detectado | sc | 0.391 | 0.391 | 0.400 | +0.009 [+0.003 a +0.014] | 7 de 10 | +0.009 [+0.005 a +0.014] | 7 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.391 | 0.400 | +0.012 [+0.006 a +0.019] | 7 de 10 | +0.010 [+0.005 a +0.014] | 8 de 10 |

Posesiones predichas en la primera celda: K5, 2309 · K2, 2491 · `main`, 2270 (reales: 3228).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.515 | 0.530 | +0.011 [+0.006 a +0.015] | 8 de 10 | +0.015 [+0.009 a +0.021] | 6 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.515 | 0.529 | +0.014 [+0.009 a +0.020] | 8 de 10 | +0.013 [+0.007 a +0.020] | 7 de 10 |
| propio | detectado | sc | 0.391 | 0.391 | 0.403 | +0.011 [+0.007 a +0.016] | 8 de 10 | +0.012 [+0.006 a +0.018] | 7 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.391 | 0.401 | +0.013 [+0.008 a +0.018] | 8 de 10 | +0.010 [+0.004 a +0.016] | 7 de 10 |

Posesiones predichas en la primera celda: K3 con 1/4 de K2, 2257 · K2, 2491 · `main`, 2270 (reales: 3228).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.515 | 0.526 | +0.006 [-0.001 a +0.014] | 6 de 10 | +0.011 [+0.008 a +0.014] | 8 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.515 | 0.521 | +0.007 [-0.001 a +0.014] | 6 de 10 | +0.006 [+0.003 a +0.009] | 8 de 10 |
| propio | detectado | sc | 0.391 | 0.391 | 0.398 | +0.007 [+0.000 a +0.013] | 6 de 10 | +0.007 [+0.004 a +0.011] | 8 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.391 | 0.395 | +0.007 [-0.000 a +0.014] | 6 de 10 | +0.004 [+0.001 a +0.007] | 7 de 10 |

Posesiones predichas en la primera celda: K3 con 3/4 de K2, 2353 · K2, 2491 · `main`, 2270 (reales: 3228).

## El otro proveedor (frente a `main`; «quita la pérdida» es −0.005 o más en todas las celdas)

- K2: peor celda -0.0046 · media -0.0003 · **quita la pérdida**
- K3: peor celda +0.0082 · media +0.0098 · gana en todas (+0.005 o más)
- K4: peor celda -0.0090 · media -0.0015 · **pierde más de 0.005 en alguna celda**
- K5: peor celda +0.0078 · media +0.0101 · gana en todas (+0.005 o más)
- K3 con 1/4 de K2: peor celda +0.0106 · media +0.0123 · gana en todas (+0.005 o más)
- K3 con 3/4 de K2: peor celda +0.0063 · media +0.0067 · gana en todas (+0.005 o más)
