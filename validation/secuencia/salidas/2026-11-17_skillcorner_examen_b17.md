### ATENCIÓN: se abre la mitad de EXAMEN de SkillCorner para b17. Apúntalo.

SkillCorner, mitad de examen (10 partidos). main = B5, dead_state y decode_cortas_a_d; los candidatos, con el modelo de los 7 partidos de la DFL. Bootstrap pareado de 1000 (5–95 %).

| `D` | condición | versión | spellF1 | frente a main [5–95 %] | gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| oraculo | detectado | main | 0.509 | – | – | 2283 / 3152 |
| oraculo | detectado | b17 | 0.528 | +0.020 [+0.012 a +0.027] | 9 de 10 | 2289 / 3152 |
| oraculo | detectado, suavizado | main | 0.504 | – | – | 2331 / 3152 |
| oraculo | detectado, suavizado | b17 | 0.523 | +0.019 [+0.012 a +0.027] | 9 de 10 | 2308 / 3152 |
| propio | detectado | main | 0.389 | – | – | 2052 / 3152 |
| propio | detectado | b17 | 0.397 | +0.009 [+0.002 a +0.015] | 7 de 10 | 2065 / 3152 |
| propio | detectado, suavizado | main | 0.384 | – | – | 2089 / 3152 |
| propio | detectado, suavizado | b17 | 0.392 | +0.008 [+0.001 a +0.015] | 6 de 10 | 2082 / 3152 |

Regla escrita antes de medir: +0.005 o más y ganar en 7 de 10, en las cuatro celdas.
- b17: NO PASA (3 de 4 celdas)
