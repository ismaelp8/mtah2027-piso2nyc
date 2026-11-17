# K7: entrenado sin SkillCorner, puntuado en SkillCorner · mitad de entrenamiento · 10 partidos

Código: 199c281 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · α = 4 en todos · este script: sha256 21b30a03e21c98f4…
Pesos: réplica 1, `pesos_r_solo_dfl.npz` (sha256 68880ef3193064f2…); réplica 2, `pesos_r2_solo_dfl.npz` (sha256 f6cfbc24de4844eb…); K7s, `pesos_k7s_media.npz` (sha256 bdaececafe4c239c…); K7s, z de la DFL, `pesos_k7s_dfl.npz` (sha256 a7dd7d5c911eef1f…); K7s, z de Metrica, `pesos_k7s_metrica.npz` (sha256 4fb7248b3c20c653…).

## Comprobación del instrumento (antes de leer nada)

| `D` | condición | `main` publicado / ahora | réplica 1 − main publicado / ahora | réplica 2 − main publicado / ahora | ¿coincide? |
|---|---|---|---|---|---|
| etiquetas | detectado | 0.519 / 0.519 | -0.005 / -0.005 | -0.007 / -0.007 | sí |
| etiquetas | detectado, suavizado | 0.514 / 0.514 | +0.001 / +0.001 | -0.003 / -0.003 | sí |
| propio | detectado | 0.391 / 0.391 | -0.000 / -0.000 | -0.003 / -0.003 | sí |
| propio | detectado, suavizado | 0.388 / 0.388 | +0.003 / +0.003 | -0.001 / -0.001 | sí |

## K7s

| `D` | condición | main | K7s | K7s − main [5–95 %] | gana a main en | − original (publicado) | − réplica 1 [5–95 %] | gana a la réplica 1 en | − réplica 2 [5–95 %] | gana a la réplica 2 en |
|---|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | 0.519 | 0.493 | -0.026 [-0.035 a -0.018] | 0 de 10 | -0.011 | -0.022 [-0.028 a -0.016] | 3 de 10 | -0.019 [-0.026 a -0.013] | 1 de 10 |
| etiquetas | detectado, suavizado | 0.514 | 0.495 | -0.020 [-0.029 a -0.012] | 3 de 10 | -0.010 | -0.021 [-0.027 a -0.015] | 1 de 10 | -0.017 [-0.023 a -0.010] | 1 de 10 |
| propio | detectado | 0.391 | 0.388 | -0.004 [-0.012 a +0.004] | 4 de 10 | +0.003 | -0.003 [-0.009 a +0.003] | 5 de 10 | -0.000 [-0.006 a +0.006] | 5 de 10 |
| propio | detectado, suavizado | 0.388 | 0.388 | +0.000 [-0.008 a +0.008] | 5 de 10 | +0.004 | -0.002 [-0.008 a +0.003] | 6 de 10 | +0.001 [-0.005 a +0.007] | 6 de 10 |

Posesiones predichas en la primera celda: K7s, 2782 · réplica 1, 2491 · réplica 2, 2447 · `main`, 2270 (reales: 3228).

## K7s, z de la DFL (sin voto)

| `D` | condición | main | K7s, z de la DFL | K7s, z de la DFL − main [5–95 %] | gana a main en | − original (publicado) | − réplica 1 [5–95 %] | gana a la réplica 1 en | − réplica 2 [5–95 %] | gana a la réplica 2 en |
|---|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | 0.519 | 0.516 | -0.004 [-0.011 a +0.004] | 6 de 10 | +0.011 | +0.001 [-0.005 a +0.006] | 5 de 10 | +0.003 [-0.003 a +0.009] | 7 de 10 |
| etiquetas | detectado, suavizado | 0.514 | 0.513 | -0.001 [-0.009 a +0.006] | 5 de 10 | +0.009 | -0.002 [-0.009 a +0.003] | 3 de 10 | +0.002 [-0.005 a +0.008] | 6 de 10 |
| propio | detectado | 0.391 | 0.397 | +0.006 [-0.001 a +0.013] | 6 de 10 | +0.013 | +0.006 [+0.001 a +0.012] | 7 de 10 | +0.009 [+0.004 a +0.015] | 8 de 10 |
| propio | detectado, suavizado | 0.388 | 0.395 | +0.007 [-0.001 a +0.014] | 6 de 10 | +0.011 | +0.004 [-0.002 a +0.010] | 7 de 10 | +0.008 [+0.002 a +0.013] | 6 de 10 |

Posesiones predichas en la primera celda: K7s, z de la DFL, 2422 · réplica 1, 2491 · réplica 2, 2447 · `main`, 2270 (reales: 3228).

## K7s, z de Metrica (sin voto)

| `D` | condición | main | K7s, z de Metrica | K7s, z de Metrica − main [5–95 %] | gana a main en | − original (publicado) | − réplica 1 [5–95 %] | gana a la réplica 1 en | − réplica 2 [5–95 %] | gana a la réplica 2 en |
|---|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | 0.519 | 0.463 | -0.057 [-0.066 a -0.048] | 0 de 10 | -0.042 | -0.052 [-0.060 a -0.045] | 0 de 10 | -0.050 [-0.057 a -0.042] | 0 de 10 |
| etiquetas | detectado, suavizado | 0.514 | 0.467 | -0.047 [-0.057 a -0.039] | 0 de 10 | -0.037 | -0.048 [-0.056 a -0.041] | 0 de 10 | -0.044 [-0.052 a -0.038] | 0 de 10 |
| propio | detectado | 0.391 | 0.374 | -0.017 [-0.026 a -0.009] | 1 de 10 | -0.010 | -0.017 [-0.025 a -0.010] | 2 de 10 | -0.014 [-0.021 a -0.007] | 2 de 10 |
| propio | detectado, suavizado | 0.388 | 0.375 | -0.013 [-0.022 a -0.004] | 2 de 10 | -0.009 | -0.016 [-0.023 a -0.009] | 4 de 10 | -0.012 [-0.019 a -0.005] | 4 de 10 |

Posesiones predichas en la primera celda: K7s, z de Metrica, 3194 · réplica 1, 2491 · réplica 2, 2447 · `main`, 2270 (reales: 3228).

## La regla

Lo mejor de los tres modelos de solo la DFL en cada celda, frente a `main`: -0.0046, +0.0010, -0.0005, +0.0027.

- K7s: frente a `main` -0.0262, -0.0199, -0.0037, +0.0003 · media -0.0124 · en lo mejor de los tres o por encima en las 4 celdas: no · media de +0.004 o más: no → **no se traslada mejor**
- K7s, z de la DFL (sin voto): frente a `main` -0.0038, -0.0014, +0.0060, +0.0071 · media +0.0020 · en lo mejor de los tres o por encima en las 4 celdas: no · media de +0.004 o más: no → **no se traslada mejor**
- K7s, z de Metrica (sin voto): frente a `main` -0.0567, -0.0475, -0.0175, -0.0131 · media -0.0337 · en lo mejor de los tres o por encima en las 4 celdas: no · media de +0.004 o más: no → **no se traslada mejor**
