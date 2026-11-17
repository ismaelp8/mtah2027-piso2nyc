# El detector de cambios de posesión en SkillCorner frente a `main`

- código: c111042 · SkillCorner, mitad de entrenamiento (10 partidos) · bootstrap: 1000
- detector: reglas: giro de 45°, cambio de velocidad de 0.6, confirmación de 30 frames
- balón del detector: «sin-suavizar» (B5 y el `D` van con el de la condición)
- combinación: w 0 · γ 8 · W 50 · contra el otro equipo
- `main`: B5, `dead_state` y `temporal.decode` (coste 25), sin «cortas a `D`»

## El detector por sí solo (descriptivo; cambios directos de las etiquetas de SkillCorner, umbral 0,5)

| condición | cambios reales | vistos | avisos por minuto vivo | avisos buenos |
|---|---|---|---|---|
| detectado | 2210 | 21 % | 3.8 | 22 % |
| detectado, suavizado | 2210 | 21 % | 3.8 | 22 % |

## `spellF1` frente a `main`

| `D` | condición | `main` | candidato | diferencia [5–95 %] | gana en | posesiones predichas (`main` / candidato) / reales |
|---|---|---|---|---|---|---|
| de las etiquetas | detectado | 0.519 | 0.514 | -0.005 [-0.011 a -0.000] | 4 de 10 | 2270 / 2507 / 3228 |
| de las etiquetas | detectado, suavizado | 0.514 | 0.511 | -0.003 [-0.008 a +0.003] | 5 de 10 | 2284 / 2522 / 3228 |
| propio | detectado | 0.382 | 0.381 | -0.000 [-0.005 a +0.004] | 6 de 10 | 2342 / 2497 / 3228 |
| propio | detectado, suavizado | 0.378 | 0.381 | +0.003 [-0.002 a +0.008] | 6 de 10 | 2345 / 2493 / 3228 |

## Regla (docs/decisiones.md, 16/11, escrita antes de medir)

- `D` de las etiquetas, detectado: -0.005 y 4 de 10 → no cumple
- `D` de las etiquetas, detectado, suavizado: -0.003 y 5 de 10 → no cumple
- `D` propio, detectado: -0.000 y 6 de 10 → no cumple
- `D` propio, detectado, suavizado: +0.003 y 6 de 10 → no cumple

+0.005 o más con los 10 juntos y ganando en 7 de 10, en las cuatro celdas: **no pasa**
