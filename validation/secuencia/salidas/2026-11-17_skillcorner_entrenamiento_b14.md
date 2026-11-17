SkillCorner, mitad de entrenamiento (10 partidos). main = B5, dead_state y decode_cortas_a_d; los candidatos, con el modelo de los 7 partidos de la DFL. Bootstrap pareado de 1000 (5–95 %).

| `D` | condición | versión | spellF1 | frente a main [5–95 %] | gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| oraculo | detectado | main | 0.519 | – | – | 2270 / 3228 |
| oraculo | detectado | b14 | 0.503 | -0.017 [-0.025 a -0.009] | 2 de 10 | 2730 / 3228 |
| oraculo | detectado, suavizado | main | 0.514 | – | – | 2284 / 3228 |
| oraculo | detectado, suavizado | b14 | 0.502 | -0.013 [-0.021 a -0.005] | 4 de 10 | 2710 / 3228 |
| propio | detectado | main | 0.391 | – | – | 2097 / 3228 |
| propio | detectado | b14 | 0.390 | -0.002 [-0.009 a +0.005] | 5 de 10 | 2461 / 3228 |
| propio | detectado, suavizado | main | 0.388 | – | – | 2104 / 3228 |
| propio | detectado, suavizado | b14 | 0.390 | +0.002 [-0.006 a +0.009] | 5 de 10 | 2451 / 3228 |

Regla escrita antes de medir: +0.005 o más y ganar en 7 de 10, en las cuatro celdas.
- b14: NO PASA (0 de 4 celdas)
