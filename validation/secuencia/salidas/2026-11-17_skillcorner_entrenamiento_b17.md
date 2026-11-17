SkillCorner, mitad de entrenamiento (10 partidos). main = B5, dead_state y decode_cortas_a_d; los candidatos, con el modelo de los 7 partidos de la DFL. Bootstrap pareado de 1000 (5–95 %).

| `D` | condición | versión | spellF1 | frente a main [5–95 %] | gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| oraculo | detectado | main | 0.519 | – | – | 2270 / 3228 |
| oraculo | detectado | b17 | 0.528 | +0.009 [+0.002 a +0.016] | 7 de 10 | 2287 / 3228 |
| oraculo | detectado, suavizado | main | 0.514 | – | – | 2284 / 3228 |
| oraculo | detectado, suavizado | b17 | 0.531 | +0.016 [+0.008 a +0.024] | 8 de 10 | 2272 / 3228 |
| propio | detectado | main | 0.391 | – | – | 2097 / 3228 |
| propio | detectado | b17 | 0.394 | +0.002 [-0.004 a +0.008] | 6 de 10 | 2113 / 3228 |
| propio | detectado, suavizado | main | 0.388 | – | – | 2104 / 3228 |
| propio | detectado, suavizado | b17 | 0.396 | +0.008 [+0.001 a +0.015] | 8 de 10 | 2114 / 3228 |

Regla escrita antes de medir: +0.005 o más y ganar en 7 de 10, en las cuatro celdas.
- b17: NO PASA (3 de 4 celdas)
