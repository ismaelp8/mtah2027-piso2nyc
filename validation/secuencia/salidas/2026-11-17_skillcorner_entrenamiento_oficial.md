SkillCorner, mitad de entrenamiento (10 partidos). main = B5, dead_state y decode_cortas_a_d; los candidatos, con el modelo de los 7 partidos de la DFL. Bootstrap pareado de 1000 (5–95 %).

| `D` | condición | versión | spellF1 | frente a main [5–95 %] | gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| oraculo | detectado | main | 0.519 | – | – | 2270 / 3228 |
| oraculo | detectado | b11 | 0.508 | -0.012 [-0.020 a -0.004] | 4 de 10 | 2655 / 3228 |
| oraculo | detectado | b12 | 0.531 | +0.011 [+0.004 a +0.018] | 7 de 10 | 2465 / 3228 |
| oraculo | detectado, suavizado | main | 0.514 | – | – | 2284 / 3228 |
| oraculo | detectado, suavizado | b11 | 0.505 | -0.009 [-0.017 a -0.001] | 4 de 10 | 2749 / 3228 |
| oraculo | detectado, suavizado | b12 | 0.528 | +0.014 [+0.006 a +0.021] | 7 de 10 | 2525 / 3228 |
| propio | detectado | main | 0.391 | – | – | 2097 / 3228 |
| propio | detectado | b11 | 0.392 | +0.000 [-0.007 a +0.008] | 4 de 10 | 2408 / 3228 |
| propio | detectado | b12 | 0.404 | +0.012 [+0.005 a +0.019] | 9 de 10 | 2281 / 3228 |
| propio | detectado, suavizado | main | 0.388 | – | – | 2104 / 3228 |
| propio | detectado, suavizado | b11 | 0.389 | +0.001 [-0.007 a +0.008] | 5 de 10 | 2489 / 3228 |
| propio | detectado, suavizado | b12 | 0.402 | +0.014 [+0.007 a +0.022] | 9 de 10 | 2305 / 3228 |

Regla escrita antes de medir: +0.005 o más y ganar en 7 de 10, en las cuatro celdas.
- b11: NO PASA (0 de 4 celdas)
- b12: PASA (4 de 4 celdas)
