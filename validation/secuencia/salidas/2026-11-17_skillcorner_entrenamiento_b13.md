SkillCorner, mitad de entrenamiento (10 partidos). main = B5, dead_state y decode_cortas_a_d; los candidatos, con el modelo de los 7 partidos de la DFL. Bootstrap pareado de 1000 (5–95 %).

| `D` | condición | versión | spellF1 | frente a main [5–95 %] | gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| oraculo | detectado | main | 0.519 | – | – | 2270 / 3228 |
| oraculo | detectado | b13 | 0.495 | -0.024 [-0.033 a -0.016] | 1 de 10 | 2683 / 3228 |
| oraculo | detectado, suavizado | main | 0.514 | – | – | 2284 / 3228 |
| oraculo | detectado, suavizado | b13 | 0.496 | -0.018 [-0.027 a -0.010] | 2 de 10 | 2621 / 3228 |
| propio | detectado | main | 0.391 | – | – | 2097 / 3228 |
| propio | detectado | b13 | 0.376 | -0.015 [-0.023 a -0.008] | 2 de 10 | 2427 / 3228 |
| propio | detectado, suavizado | main | 0.388 | – | – | 2104 / 3228 |
| propio | detectado, suavizado | b13 | 0.378 | -0.010 [-0.017 a -0.001] | 4 de 10 | 2378 / 3228 |

Regla escrita antes de medir: +0.005 o más y ganar en 7 de 10, en las cuatro celdas.
- b13: NO PASA (0 de 4 celdas)
