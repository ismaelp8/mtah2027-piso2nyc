# Refinamientos de K2 sin reentrenar · SkillCorner, mitad de entrenamiento · 10 partidos

Código: 19bedeb · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `pesos_r2_solo_dfl.npz` (sha256 f6cfbc24de4844eb…), de un modelo que solo vio la DFL. B5: los coeficientes de la entrega (nunca vio este proveedor).

## K2

| `D` | condición | etiquetas | main | K2 | K2 | K2 − main [5–95 %] | gana a main en | K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.512 | 0.512 | -0.007 [-0.015 a +0.001] | 5 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.511 | 0.511 | -0.003 [-0.011 a +0.006] | 5 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| propio | detectado | sc | 0.391 | 0.388 | 0.388 | -0.003 [-0.011 a +0.003] | 5 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.387 | 0.387 | -0.001 [-0.008 a +0.006] | 5 de 10 | +0.000 [+0.000 a +0.000] | 0 de 10 |

Posesiones predichas en la primera celda: 2447 · K2, 2447 · `main`, 2270 (reales: 3228).

## K3

| `D` | condición | etiquetas | main | K2 | K3 | K3 − main [5–95 %] | gana a main en | K3 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.512 | 0.528 | +0.008 [+0.002 a +0.014] | 7 de 10 | +0.015 [+0.011 a +0.020] | 9 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.511 | 0.526 | +0.011 [+0.005 a +0.018] | 8 de 10 | +0.014 [+0.009 a +0.020] | 10 de 10 |
| propio | detectado | sc | 0.391 | 0.388 | 0.397 | +0.005 [-0.001 a +0.011] | 7 de 10 | +0.009 [+0.005 a +0.013] | 9 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.387 | 0.396 | +0.008 [+0.002 a +0.014] | 9 de 10 | +0.009 [+0.004 a +0.013] | 10 de 10 |

Posesiones predichas en la primera celda: 2271 · K2, 2447 · `main`, 2270 (reales: 3228).

## K4

| `D` | condición | etiquetas | main | K2 | K4 | K4 − main [5–95 %] | gana a main en | K4 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.512 | 0.515 | -0.005 [-0.012 a +0.003] | 5 de 10 | +0.002 [+0.000 a +0.005] | 6 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.511 | 0.513 | -0.002 [-0.010 a +0.006] | 6 de 10 | +0.001 [-0.002 a +0.004] | 6 de 10 |
| propio | detectado | sc | 0.391 | 0.388 | 0.389 | -0.002 [-0.009 a +0.005] | 5 de 10 | +0.001 [-0.001 a +0.004] | 7 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.387 | 0.387 | -0.001 [-0.008 a +0.006] | 4 de 10 | -0.000 [-0.003 a +0.003] | 5 de 10 |

Posesiones predichas en la primera celda: 2442 · K2, 2447 · `main`, 2270 (reales: 3228).

## K5

| `D` | condición | etiquetas | main | K2 | K5 | K5 − main [5–95 %] | gana a main en | K5 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.512 | 0.530 | +0.010 [+0.004 a +0.016] | 6 de 10 | +0.017 [+0.013 a +0.022] | 9 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.511 | 0.529 | +0.014 [+0.008 a +0.021] | 9 de 10 | +0.017 [+0.012 a +0.023] | 10 de 10 |
| propio | detectado | sc | 0.391 | 0.388 | 0.399 | +0.007 [+0.001 a +0.013] | 7 de 10 | +0.011 [+0.006 a +0.015] | 9 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.387 | 0.396 | +0.008 [+0.002 a +0.014] | 9 de 10 | +0.009 [+0.004 a +0.014] | 10 de 10 |

Posesiones predichas en la primera celda: 2274 · K2, 2447 · `main`, 2270 (reales: 3228).

## K3 con 1/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 1/4 de K2 | K3 con 1/4 de K2 − main [5–95 %] | gana a main en | K3 con 1/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.512 | 0.533 | +0.014 [+0.009 a +0.019] | 9 de 10 | +0.021 [+0.015 a +0.027] | 8 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.511 | 0.530 | +0.015 [+0.011 a +0.020] | 9 de 10 | +0.018 [+0.012 a +0.025] | 8 de 10 |
| propio | detectado | sc | 0.391 | 0.388 | 0.402 | +0.010 [+0.006 a +0.015] | 9 de 10 | +0.014 [+0.008 a +0.019] | 9 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.387 | 0.400 | +0.012 [+0.008 a +0.018] | 10 de 10 | +0.013 [+0.007 a +0.019] | 9 de 10 |

Posesiones predichas en la primera celda: 2230 · K2, 2447 · `main`, 2270 (reales: 3228).

## K3 con 3/4 de K2 (sin voto)

| `D` | condición | etiquetas | main | K2 | K3 con 3/4 de K2 | K3 con 3/4 de K2 − main [5–95 %] | gana a main en | K3 con 3/4 de K2 − K2 [5–95 %] | gana a K2 en |
|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.512 | 0.523 | +0.004 [-0.003 a +0.011] | 5 de 10 | +0.011 [+0.008 a +0.014] | 8 de 10 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.511 | 0.519 | +0.005 [-0.003 a +0.012] | 7 de 10 | +0.008 [+0.004 a +0.011] | 9 de 10 |
| propio | detectado | sc | 0.391 | 0.388 | 0.396 | +0.004 [-0.003 a +0.011] | 8 de 10 | +0.008 [+0.005 a +0.010] | 9 de 10 |
| propio | detectado, suavizado | sc | 0.388 | 0.387 | 0.391 | +0.003 [-0.004 a +0.009] | 4 de 10 | +0.004 [+0.000 a +0.007] | 7 de 10 |

Posesiones predichas en la primera celda: 2343 · K2, 2447 · `main`, 2270 (reales: 3228).

## El otro proveedor (frente a `main`; «quita la pérdida» es −0.005 o más en todas las celdas)

- K2: peor celda -0.0070 · media -0.0035 · **pierde más de 0.005 en alguna celda**
- K3: peor celda +0.0053 · media +0.0082 · gana en todas (+0.005 o más)
- K4: peor celda -0.0045 · media -0.0023 · **quita la pérdida**
- K5: peor celda +0.0071 · media +0.0100 · gana en todas (+0.005 o más)
- K3 con 1/4 de K2: peor celda +0.0103 · media +0.0130 · gana en todas (+0.005 o más)
- K3 con 3/4 de K2: peor celda +0.0030 · media +0.0039 · **quita la pérdida**
