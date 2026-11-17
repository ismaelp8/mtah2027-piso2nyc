# Comprobación del instrumento en los 8 pliegues, dentro del proveedor, frente a K2 y a `main`

Código: 456884d · bootstrap pareado de 1000 · este script: sha256 243759087a9c9f05… · K2: `conjunto_pesos.npz` (sha256 6d16316f85063f13…).
«candidato» es candidato. Cada partido, con el pliegue que no lo vio.

## DFL, 7 partidos

| `D` | condición | etiquetas | main | K2 | K2 con α = 4 | K2 con α = 4 − main [5–95 %] · gana | K2 con α = 4 − K2 [5–95 %] · gana |
|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.780 | 0.785 | +0.057 [+0.045 a +0.069] · 7 | +0.005 [+0.003 a +0.007] · 3 |
| etiquetas | como el ATD | flag | 0.498 | 0.542 | 0.541 | +0.043 [+0.033 a +0.053] · 7 | -0.001 [-0.003 a +0.001] · 1 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.794 | 0.801 | +0.053 [+0.042 a +0.064] · 7 | +0.007 [+0.005 a +0.009] · 3 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.549 | 0.548 | +0.036 [+0.027 a +0.046] · 7 | -0.001 [-0.003 a +0.002] · 1 |
| propio | como el ATD | control | 0.623 | 0.668 | 0.673 | +0.050 [+0.039 a +0.062] · 7 | +0.005 [+0.003 a +0.006] · 3 |
| propio | como el ATD | flag | 0.414 | 0.457 | 0.455 | +0.041 [+0.033 a +0.051] · 7 | -0.001 [-0.003 a +0.001] · 2 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.686 | 0.692 | +0.041 [+0.030 a +0.052] · 6 | +0.005 [+0.003 a +0.007] · 3 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.464 | 0.463 | +0.032 [+0.024 a +0.042] · 7 | -0.001 [-0.003 a +0.001] · 1 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.631 | 0.636 | +0.049 [+0.037 a +0.060] · 6 | +0.005 [+0.002 a +0.007] · 3 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.430 | 0.427 | +0.033 [+0.024 a +0.041] · 7 | -0.003 [-0.005 a -0.000] · 0 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.648 | 0.652 | +0.040 [+0.028 a +0.050] · 6 | +0.005 [+0.002 a +0.007] · 3 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.438 | 0.435 | +0.026 [+0.017 a +0.034] · 7 | -0.003 [-0.006 a -0.001] · 0 |

## SkillCorner, mitad de entrenamiento, 10 partidos

| `D` | condición | etiquetas | main | K2 | K2 con α = 4 | K2 con α = 4 − main [5–95 %] · gana | K2 con α = 4 − K2 [5–95 %] · gana |
|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | 0.519 | 0.543 | 0.543 | +0.023 [+0.015 a +0.031] · 8 | +0.000 [+0.000 a +0.000] · 0 |
| etiquetas | detectado, suavizado | sc | 0.514 | 0.539 | 0.539 | +0.024 [+0.016 a +0.032] · 7 | +0.000 [+0.000 a +0.000] · 0 |
| propio | detectado | sc | 0.391 | 0.413 | 0.413 | +0.021 [+0.014 a +0.029] · 10 | +0.000 [+0.000 a +0.000] · 0 |
| propio | detectado, suavizado | sc | 0.388 | 0.412 | 0.412 | +0.024 [+0.017 a +0.032] · 10 | +0.000 [+0.000 a +0.000] · 0 |

Instrumento: `main` y K2 en la DFL con control, «como el ATD», `D` de las etiquetas: 0.728 → 0.780 (publicado: 0.728 → 0.780): **coincide**

## Lo que ataca (cuentas de `detalle_abiertos.py`; `D` de las etiquetas, primera condición)

| datos | versión | V: cambios entre equipos vistos | nuestros | S: nos sobran | P: posesiones de 2 a 5 s encontradas | de menos de 2 s |
|---|---|---|---|---|---|---|
| DFL, control | main | 36.9 % de 1026 | 951 | 570 | 53.1 % de 399 | 22.0 % |
| DFL, control | K2 | 50.6 % de 1026 | 941 | 423 | 64.9 % de 399 | 22.6 % |
| DFL, control | K2 con α = 4 | 50.4 % de 1026 | 923 | 407 | 64.7 % de 399 | 22.0 % |
| DFL, flag | main | 20.2 % de 2351 | 951 | 475 | 27.4 % de 934 | 6.7 % |
| DFL, flag | K2 | 26.1 % de 2351 | 941 | 331 | 33.3 % de 934 | 6.3 % |
| DFL, flag | K2 con α = 4 | 25.7 % de 2351 | 923 | 322 | 33.0 % de 934 | 6.2 % |
| SkillCorner | main | 19.3 % de 2210 | 1252 | 887 | 28.7 % de 714 | 14.0 % |
| SkillCorner | K2 | 23.5 % de 2210 | 1288 | 832 | 32.2 % de 714 | 14.9 % |
| SkillCorner | K2 con α = 4 | 23.5 % de 2210 | 1288 | 832 | 32.2 % de 714 | 14.9 % |
