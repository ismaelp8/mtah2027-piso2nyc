# Modelo conjunto frente a `main` · tanda «v1» · SkillCorner, mitad de entrenamiento · 10 partidos

Código: 5cd0357, con cambios sin commit en possession/ o validation/harness/ · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · salidas del modelo: la pieza en numpy (possession/conjunto.py).

## Candidato K2 · α = 4, elegida en la DFL con los 7

| α | `D` | condición | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / main / reales |
|---|---|---|---|---|---|---|---|
| 4 | etiquetas | detectado | 0.519 | 0.543 | +0.023 [+0.015 a +0.031] | 8 de 10 | 2306 / 2270 / 3228 |
| 4 | etiquetas | detectado, suavizado | 0.514 | 0.539 | +0.024 [+0.016 a +0.032] | 7 de 10 | 2317 / 2284 / 3228 |
| 4 | propio | detectado | 0.391 | 0.413 | +0.021 [+0.014 a +0.029] | 10 de 10 | 2148 / 2097 / 3228 |
| 4 | propio | detectado, suavizado | 0.388 | 0.412 | +0.024 [+0.017 a +0.032] | 10 de 10 | 2143 / 2104 / 3228 |

Regla (+0.005 y 7 de 10 en las cuatro celdas): **pasa**.
