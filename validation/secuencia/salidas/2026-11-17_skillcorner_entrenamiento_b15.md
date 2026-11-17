SkillCorner, mitad de entrenamiento (10 partidos). main = B5, dead_state y decode_cortas_a_d; los candidatos, con el modelo de los 7 partidos de la DFL. Bootstrap pareado de 1000 (5–95 %).

| `D` | condición | versión | spellF1 | frente a main [5–95 %] | gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| oraculo | detectado | main | 0.519 | – | – | 2270 / 3228 |
| oraculo | detectado | b15 | 0.525 | +0.006 [-0.001 a +0.012] | 7 de 10 | 2322 / 3228 |
| oraculo | detectado, suavizado | main | 0.514 | – | – | 2284 / 3228 |
| oraculo | detectado, suavizado | b15 | 0.520 | +0.006 [-0.002 a +0.013] | 6 de 10 | 2301 / 3228 |
| propio | detectado | main | 0.391 | – | – | 2097 / 3228 |
| propio | detectado | b15 | 0.397 | +0.006 [-0.001 a +0.012] | 8 de 10 | 2128 / 3228 |
| propio | detectado, suavizado | main | 0.388 | – | – | 2104 / 3228 |
| propio | detectado, suavizado | b15 | 0.394 | +0.006 [-0.001 a +0.013] | 6 de 10 | 2109 / 3228 |

Regla escrita antes de medir: +0.005 o más y ganar en 7 de 10, en las cuatro celdas.
- b15: NO PASA (2 de 4 celdas)
