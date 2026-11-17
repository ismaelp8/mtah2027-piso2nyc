# Refinamientos de K2 sin reentrenar · SkillCorner, mitad de entrenamiento · 10 partidos

Código: 19bedeb · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: la media de las z de `pesos_r_solo_dfl.npz` (sha256 68880ef3193064f2…) y `pesos_r2_solo_dfl.npz` (sha256 f6cfbc24de4844eb…), de modelos que solo vio la DFL. B5: los coeficientes de la entrega (nunca vio este proveedor).
α de K2: 4, la de «todos» · este script: sha256 6d06f765b740bbee…

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.523 | 0.523 | +0.004 [-0.004 a +0.011] | 6 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.519 | 0.519 | +0.004 [-0.004 a +0.012] | 6 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| propio | detectado | sc | 0.391 | 0.393 | 0.393 | +0.002 [-0.005 a +0.009] | 6 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.390 | 0.390 | +0.002 [-0.005 a +0.009] | 5 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |

Posesiones predichas en la primera celda: K2, 2366 · K2, 2366 · `main`, 2270 (reales: 3228).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.523 | 0.532 | +0.013 [+0.007 a +0.019] | 7 de 10 | +0.009 [+0.004 a +0.014] | 10 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.519 | 0.531 | +0.017 [+0.010 a +0.023] | 7 de 10 | +0.013 [+0.008 a +0.017] | 9 de 10 |
| propio | detectado | sc | 0.391 | 0.393 | 0.398 | +0.007 [+0.001 a +0.012] | 5 de 10 | +0.005 [+0.001 a +0.009] | 7 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.390 | 0.398 | +0.011 [+0.004 a +0.017] | 8 de 10 | +0.008 [+0.004 a +0.012] | 8 de 10 |

Posesiones predichas en la primera celda: K3, 2266 · K2, 2366 · `main`, 2270 (reales: 3228).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.523 | 0.523 | +0.003 [-0.004 a +0.011] | 6 de 10 | -0.000 [-0.003 a +0.002] | 4 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.519 | 0.521 | +0.006 [-0.002 a +0.014] | 6 de 10 | +0.002 [-0.000 a +0.005] | 8 de 10 |
| propio | detectado | sc | 0.391 | 0.393 | 0.393 | +0.002 [-0.005 a +0.009] | 6 de 10 | +0.000 [-0.002 a +0.002] | 6 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.390 | 0.391 | +0.003 [-0.004 a +0.010] | 6 de 10 | +0.001 [-0.001 a +0.003] | 5 de 10 |

Posesiones predichas en la primera celda: K4, 2375 · K2, 2366 · `main`, 2270 (reales: 3228).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.523 | 0.533 | +0.014 [+0.008 a +0.020] | 7 de 10 | +0.010 [+0.005 a +0.015] | 10 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.519 | 0.529 | +0.015 [+0.008 a +0.022] | 8 de 10 | +0.011 [+0.006 a +0.016] | 8 de 10 |
| propio | detectado | sc | 0.391 | 0.393 | 0.400 | +0.009 [+0.003 a +0.015] | 7 de 10 | +0.007 [+0.003 a +0.012] | 7 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.390 | 0.399 | +0.011 [+0.005 a +0.017] | 8 de 10 | +0.009 [+0.005 a +0.013] | 8 de 10 |

Posesiones predichas en la primera celda: K5, 2269 · K2, 2366 · `main`, 2270 (reales: 3228).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.523 | 0.532 | +0.013 [+0.008 a +0.017] | 8 de 10 | +0.009 [+0.004 a +0.015] | 7 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.519 | 0.529 | +0.015 [+0.010 a +0.020] | 9 de 10 | +0.011 [+0.005 a +0.016] | 7 de 10 |
| propio | detectado | sc | 0.391 | 0.393 | 0.401 | +0.009 [+0.005 a +0.014] | 9 de 10 | +0.007 [+0.002 a +0.013] | 7 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.390 | 0.400 | +0.012 [+0.007 a +0.017] | 10 de 10 | +0.009 [+0.004 a +0.015] | 6 de 10 |

Posesiones predichas en la primera celda: K3 con 1/4 de K2, 2238 · K2, 2366 · `main`, 2270 (reales: 3228).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.523 | 0.529 | +0.009 [+0.002 a +0.016] | 6 de 10 | +0.006 [+0.003 a +0.009] | 9 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.519 | 0.526 | +0.012 [+0.004 a +0.019] | 7 de 10 | +0.008 [+0.004 a +0.011] | 8 de 10 |
| propio | detectado | sc | 0.391 | 0.393 | 0.396 | +0.004 [-0.002 a +0.011] | 5 de 10 | +0.003 [-0.000 a +0.005] | 6 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.390 | 0.396 | +0.008 [+0.002 a +0.015] | 7 de 10 | +0.006 [+0.003 a +0.009] | 7 de 10 |

Posesiones predichas en la primera celda: K3 con 3/4 de K2, 2298 · K2, 2366 · `main`, 2270 (reales: 3228).

## El otro proveedor (frente a `main`; «quita la pérdida» es −0.005 o más en todas las celdas)

- K2: peor celda +0.0017 · media +0.0030 · **quita la pérdida**
- K3: peor celda +0.0069 · media +0.0117 · gana en todas (+0.005 o más)
- K4: peor celda +0.0017 · media +0.0036 · **quita la pérdida**
- K5: peor celda +0.0091 · media +0.0122 · gana en todas (+0.005 o más)
- K3 con 1/4 de K2: peor celda +0.0092 · media +0.0122 · gana en todas (+0.005 o más)
- K3 con 3/4 de K2: peor celda +0.0044 · media +0.0084 · **quita la pérdida**
