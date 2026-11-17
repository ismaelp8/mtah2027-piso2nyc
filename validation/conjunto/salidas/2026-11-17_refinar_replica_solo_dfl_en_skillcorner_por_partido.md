# Refinamientos de K2 sin reentrenar · SkillCorner, mitad de entrenamiento · 10 partidos

Código: 74f3191 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `pesos_r_solo_dfl.npz` (sha256 68880ef3193064f2…), de un modelo que solo vio la DFL. B5: los coeficientes de la entrega (nunca vio este proveedor).
α de K2: 4, la de «todos» · este script: sha256 d37f2cd30c97b99d… · recuentos guardados, calculados con el código 74f3191 y el script d37f2cd30c97b99d…

## Partido a partido, frente a `main` (descriptivo, sin voto)

Cada casilla: peor partido / mediana / mejor partido, y en cuántos partidos queda por debajo de `main`.

| `D` | condición | etiquetas | K2 | K3 | K4 | K5 | K3 con 1/4 de K2 | K3 con 3/4 de K2 |
|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | -0.054 / -0.013 / +0.049 (6) | -0.024 / +0.013 / +0.037 (4) | -0.046 / -0.011 / +0.043 (6) | -0.020 / +0.014 / +0.039 (4) | -0.012 / +0.012 / +0.028 (2) | -0.032 / +0.006 / +0.050 (4) |
| etiquetas | detectado, suavizado | sc | -0.045 / +0.004 / +0.045 (5) | -0.025 / +0.017 / +0.046 (4) | -0.044 / +0.007 / +0.051 (4) | -0.024 / +0.016 / +0.047 (3) | -0.017 / +0.016 / +0.035 (2) | -0.034 / +0.011 / +0.049 (4) |
| propio | detectado | sc | -0.038 / -0.003 / +0.034 (5) | -0.010 / +0.011 / +0.026 (3) | -0.038 / +0.000 / +0.035 (5) | -0.016 / +0.012 / +0.027 (3) | -0.007 / +0.011 / +0.027 (2) | -0.019 / +0.004 / +0.031 (4) |
| propio | detectado, suavizado | sc | -0.034 / +0.004 / +0.035 (4) | -0.010 / +0.012 / +0.027 (3) | -0.037 / +0.011 / +0.036 (4) | -0.008 / +0.012 / +0.034 (3) | -0.003 / +0.015 / +0.028 (2) | -0.021 / +0.009 / +0.031 (4) |

Veces que queda por debajo de `main`, de 40 (partido y celda): K2, 20; K3, 14; K4, 19; K5, 13; K3 con 1/4 de K2, 8; K3 con 3/4 de K2, 16.

## Posesiones reales encontradas (descriptivo, sin voto; solape de 0,5 o más)

| `D` | condición | etiquetas | versión | reales | predichas | encontradas | de las reales | de las predichas |
|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | main | 3228 | 2270 | 1450 | 44.9 % | 63.9 % |
| etiquetas | detectado | sc | K2 | 3228 | 2491 | 1505 | 46.6 % | 60.4 % |
| etiquetas | detectado | sc | K3 | 3228 | 2307 | 1491 | 46.2 % | 64.6 % |
| etiquetas | detectado | sc | K4 | 3228 | 2512 | 1497 | 46.4 % | 59.6 % |
| etiquetas | detectado | sc | K5 | 3228 | 2309 | 1489 | 46.1 % | 64.5 % |
| etiquetas | detectado, suavizado | sc | main | 3228 | 2284 | 1443 | 44.7 % | 63.2 % |
| etiquetas | detectado, suavizado | sc | K2 | 3228 | 2448 | 1496 | 46.3 % | 61.1 % |
| etiquetas | detectado, suavizado | sc | K3 | 3228 | 2293 | 1476 | 45.7 % | 64.4 % |
| etiquetas | detectado, suavizado | sc | K4 | 3228 | 2455 | 1497 | 46.4 % | 61.0 % |
| etiquetas | detectado, suavizado | sc | K5 | 3228 | 2309 | 1484 | 46.0 % | 64.3 % |
| propio | detectado | sc | main | 3228 | 2097 | 1045 | 32.4 % | 49.8 % |
| propio | detectado | sc | K2 | 3228 | 2273 | 1072 | 33.2 % | 47.2 % |
| propio | detectado | sc | K3 | 3228 | 2128 | 1075 | 33.3 % | 50.5 % |
| propio | detectado | sc | K4 | 3228 | 2272 | 1067 | 33.1 % | 47.0 % |
| propio | detectado | sc | K5 | 3228 | 2135 | 1068 | 33.1 % | 50.0 % |
| propio | detectado, suavizado | sc | main | 3228 | 2104 | 1036 | 32.1 % | 49.2 % |
| propio | detectado, suavizado | sc | K2 | 3228 | 2235 | 1056 | 32.7 % | 47.2 % |
| propio | detectado, suavizado | sc | K3 | 3228 | 2126 | 1065 | 33.0 % | 50.1 % |
| propio | detectado, suavizado | sc | K4 | 3228 | 2233 | 1059 | 32.8 % | 47.4 % |
| propio | detectado, suavizado | sc | K5 | 3228 | 2136 | 1074 | 33.3 % | 50.3 % |
