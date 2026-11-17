# Refinamientos de K2 sin reentrenar · SkillCorner, mitad de entrenamiento · 10 partidos

Código: 74f3191 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `conjunto_pesos.npz` (sha256 6d16316f85063f13…): cada partido con el pliegue que no lo vio. B5: los coeficientes de la entrega (nunca vio este proveedor).
α de K2: 4, la de «todos» · este script: sha256 d37f2cd30c97b99d… · recuentos guardados, calculados con el código 74f3191 y el script d37f2cd30c97b99d…

## Partido a partido, frente a `main` (descriptivo, sin voto)

Cada casilla: peor partido / mediana / mejor partido, y en cuántos partidos queda por debajo de `main`.

| `D` | condición | etiquetas | K2 | K3 | K4 | K5 | K3 con 1/4 de K2 | K3 con 3/4 de K2 |
|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | -0.013 / +0.019 / +0.051 (2) | +0.006 / +0.022 / +0.039 (0) | -0.012 / +0.025 / +0.052 (2) | +0.005 / +0.021 / +0.034 (0) | -0.001 / +0.013 / +0.025 (1) | -0.002 / +0.030 / +0.050 (1) |
| etiquetas | detectado, suavizado | sc | -0.016 / +0.025 / +0.058 (3) | -0.005 / +0.026 / +0.041 (1) | -0.005 / +0.030 / +0.059 (2) | -0.003 / +0.024 / +0.037 (1) | -0.007 / +0.013 / +0.032 (1) | -0.010 / +0.035 / +0.051 (1) |
| propio | detectado | sc | +0.003 / +0.020 / +0.042 (0) | +0.006 / +0.018 / +0.022 (0) | -0.001 / +0.021 / +0.040 (1) | +0.007 / +0.016 / +0.032 (0) | +0.002 / +0.013 / +0.020 (0) | +0.006 / +0.021 / +0.038 (0) |
| propio | detectado, suavizado | sc | +0.010 / +0.022 / +0.045 (0) | +0.004 / +0.018 / +0.036 (0) | +0.008 / +0.025 / +0.038 (0) | +0.006 / +0.019 / +0.035 (0) | -0.001 / +0.014 / +0.024 (1) | +0.010 / +0.025 / +0.035 (0) |

Veces que queda por debajo de `main`, de 40 (partido y celda): K2, 5; K3, 1; K4, 5; K5, 1; K3 con 1/4 de K2, 3; K3 con 3/4 de K2, 2.

## Posesiones reales encontradas (descriptivo, sin voto; solape de 0,5 o más)

| `D` | condición | etiquetas | versión | reales | predichas | encontradas | de las reales | de las predichas |
|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | main | 3228 | 2270 | 1450 | 44.9 % | 63.9 % |
| etiquetas | detectado | sc | K2 | 3228 | 2306 | 1546 | 47.9 % | 67.0 % |
| etiquetas | detectado | sc | K3 | 3228 | 2195 | 1493 | 46.3 % | 68.0 % |
| etiquetas | detectado | sc | K4 | 3228 | 2287 | 1529 | 47.4 % | 66.9 % |
| etiquetas | detectado | sc | K5 | 3228 | 2209 | 1496 | 46.3 % | 67.7 % |
| etiquetas | detectado, suavizado | sc | main | 3228 | 2284 | 1443 | 44.7 % | 63.2 % |
| etiquetas | detectado, suavizado | sc | K2 | 3228 | 2317 | 1541 | 47.7 % | 66.5 % |
| etiquetas | detectado, suavizado | sc | K3 | 3228 | 2212 | 1489 | 46.1 % | 67.3 % |
| etiquetas | detectado, suavizado | sc | K4 | 3228 | 2305 | 1538 | 47.6 % | 66.7 % |
| etiquetas | detectado, suavizado | sc | K5 | 3228 | 2226 | 1488 | 46.1 % | 66.8 % |
| propio | detectado | sc | main | 3228 | 2097 | 1045 | 32.4 % | 49.8 % |
| propio | detectado | sc | K2 | 3228 | 2148 | 1115 | 34.5 % | 51.9 % |
| propio | detectado | sc | K3 | 3228 | 2057 | 1088 | 33.7 % | 52.9 % |
| propio | detectado | sc | K4 | 3228 | 2133 | 1103 | 34.2 % | 51.7 % |
| propio | detectado | sc | K5 | 3228 | 2064 | 1096 | 34.0 % | 53.1 % |
| propio | detectado, suavizado | sc | main | 3228 | 2104 | 1036 | 32.1 % | 49.2 % |
| propio | detectado, suavizado | sc | K2 | 3228 | 2143 | 1120 | 34.7 % | 52.3 % |
| propio | detectado, suavizado | sc | K3 | 3228 | 2058 | 1091 | 33.8 % | 53.0 % |
| propio | detectado, suavizado | sc | K4 | 3228 | 2135 | 1108 | 34.3 % | 51.9 % |
| propio | detectado, suavizado | sc | K5 | 3228 | 2068 | 1099 | 34.0 % | 53.1 % |
