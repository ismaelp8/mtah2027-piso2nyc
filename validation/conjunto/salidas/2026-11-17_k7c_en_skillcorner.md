# K7: entrenado sin SkillCorner, puntuado en SkillCorner · mitad de entrenamiento · 10 partidos

Código: 3481436 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · α = 4 en todos · este script: sha256 21b30a03e21c98f4…
Pesos: réplica 1, `pesos_r_solo_dfl.npz` (sha256 68880ef3193064f2…); réplica 2, `pesos_r2_solo_dfl.npz` (sha256 f6cfbc24de4844eb…); K7c, `pesos_k7c.npz` (sha256 777be0c21fde6bc7…).

## Comprobación del instrumento (antes de leer nada)

| `D` | condición | `main` publicado / ahora | réplica 1 − main publicado / ahora | réplica 2 − main publicado / ahora | ¿coincide? |
|---|---|---|---|---|---|
| etiquetas | detectado | 0.519 / 0.519 | -0.005 / -0.005 | -0.007 / -0.007 | sí |
| etiquetas | detectado, suavizado | 0.514 / 0.514 | +0.001 / +0.001 | -0.003 / -0.003 | sí |
| propio | detectado | 0.391 / 0.391 | -0.000 / -0.000 | -0.003 / -0.003 | sí |
| propio | detectado, suavizado | 0.388 / 0.388 | +0.003 / +0.003 | -0.001 / -0.001 | sí |

## K7c

| `D` | condición | main | K7c | K7c − main [5–95 %] | gana a main en | − original (publicado) | − réplica 1 [5–95 %] | gana a la réplica 1 en | − réplica 2 [5–95 %] | gana a la réplica 2 en |
|---|---|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | 0.519 | 0.512 | -0.007 [-0.015 a +0.000] | 5 de 10 | +0.008 | -0.003 [-0.008 a +0.003] | 3 de 10 | -0.000 [-0.006 a +0.005] | 4 de 10 |
| etiquetas | detectado, suavizado | 0.514 | 0.518 | +0.003 [-0.005 a +0.011] | 6 de 10 | +0.013 | +0.002 [-0.003 a +0.008] | 6 de 10 | +0.006 [+0.001 a +0.013] | 8 de 10 |
| propio | detectado | 0.391 | 0.392 | +0.000 [-0.007 a +0.007] | 5 de 10 | +0.007 | +0.001 [-0.004 a +0.006] | 5 de 10 | +0.004 [-0.002 a +0.009] | 6 de 10 |
| propio | detectado, suavizado | 0.388 | 0.396 | +0.008 [+0.000 a +0.015] | 6 de 10 | +0.012 | +0.005 [+0.000 a +0.010] | 6 de 10 | +0.009 [+0.003 a +0.015] | 8 de 10 |

Posesiones predichas en la primera celda: K7c, 2494 · réplica 1, 2491 · réplica 2, 2447 · `main`, 2270 (reales: 3228).

## La regla

Lo mejor de los tres modelos de solo la DFL en cada celda, frente a `main`: -0.0046, +0.0010, -0.0005, +0.0027.

- K7c: frente a `main` -0.0071, +0.0032, +0.0002, +0.0079 · media +0.0010 · en lo mejor de los tres o por encima en las 4 celdas: no · media de +0.004 o más: no → **no se traslada mejor**
