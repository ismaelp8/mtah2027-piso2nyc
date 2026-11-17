# Modelo conjunto frente a `main` · tanda «solo_dfl» · SkillCorner, mitad de entrenamiento · 10 partidos

Código: 4845078 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · salidas del modelo: las de torch.

## Candidato K2 · α = 4, fijada desde la DFL

| α | `D` | condición | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / main / reales |
|---|---|---|---|---|---|---|---|
| 4 | etiquetas | detectado | 0.519 | 0.504 | -0.015 [-0.023 a -0.007] | 3 de 10 | 2426 / 2270 / 3228 |
| 4 | etiquetas | detectado, suavizado | 0.514 | 0.505 | -0.010 [-0.018 a -0.002] | 5 de 10 | 2417 / 2284 / 3228 |
| 4 | propio | detectado | 0.391 | 0.384 | -0.007 [-0.015 a -0.000] | 5 de 10 | 2217 / 2097 / 3228 |
| 4 | propio | detectado, suavizado | 0.388 | 0.384 | -0.004 [-0.011 a +0.003] | 4 de 10 | 2208 / 2104 / 3228 |

Regla (+0.005 y 7 de 10 en las cuatro celdas): **no pasa**.
