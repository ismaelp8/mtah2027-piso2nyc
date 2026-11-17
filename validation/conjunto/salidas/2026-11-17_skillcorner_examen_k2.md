# Modelo conjunto frente a `main` · tanda «v1» · SkillCorner, MITAD DE EXAMEN · 10 partidos

Código: a37010a · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · salidas del modelo: la pieza en numpy (possession/conjunto.py).

## Candidato K2 · α = 4, elegida en la DFL con los 7

| α | `D` | condición | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / main / reales |
|---|---|---|---|---|---|---|---|
| 4 | etiquetas | detectado | 0.509 | 0.532 | +0.023 [+0.015 a +0.032] | 9 de 10 | 2243 / 2283 / 3152 |
| 4 | etiquetas | detectado, suavizado | 0.504 | 0.532 | +0.028 [+0.019 a +0.037] | 10 de 10 | 2231 / 2331 / 3152 |
| 4 | propio | detectado | 0.389 | 0.409 | +0.021 [+0.013 a +0.028] | 8 de 10 | 2056 / 2052 / 3152 |
| 4 | propio | detectado, suavizado | 0.384 | 0.410 | +0.026 [+0.019 a +0.034] | 10 de 10 | 2046 / 2089 / 3152 |

Regla (+0.005 y 7 de 10 en las cuatro celdas): **pasa**.
