# Refinamientos de K2 sin reentrenar · DFL · 7 partidos

Código: 8409165 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `conjunto_pesos.npz` (sha256 6d16316f85063f13…): cada partido con el pliegue que no lo vio. B5: el pliegue que no vio el partido (sí vio otros de la DFL).

## Partido a partido, frente a `main` (descriptivo, sin voto)

Cada casilla: peor partido / mediana / mejor partido, y en cuántos partidos queda por debajo de `main`.

| `D` | condición | etiquetas | K2 | K3 | K4 | K5 | K3 con 1/4 de K2 | K3 con 3/4 de K2 |
|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | +0.000 / +0.051 / +0.078 (0) | +0.025 / +0.056 / +0.078 (0) | +0.017 / +0.061 / +0.091 (0) | +0.022 / +0.048 / +0.077 (0) | +0.027 / +0.040 / +0.059 (0) | +0.012 / +0.062 / +0.078 (0) |
| etiquetas | como el ATD | flag | +0.017 / +0.045 / +0.068 (0) | +0.017 / +0.029 / +0.047 (0) | +0.025 / +0.047 / +0.069 (0) | +0.021 / +0.030 / +0.045 (0) | +0.006 / +0.017 / +0.032 (0) | +0.023 / +0.040 / +0.057 (0) |
| etiquetas | como el ATD, sin bloques | control | -0.010 / +0.058 / +0.070 (1) | +0.018 / +0.052 / +0.069 (0) | +0.007 / +0.059 / +0.087 (0) | +0.012 / +0.045 / +0.075 (0) | +0.018 / +0.033 / +0.043 (0) | +0.002 / +0.057 / +0.075 (0) |
| etiquetas | como el ATD, sin bloques | flag | +0.013 / +0.035 / +0.072 (0) | +0.010 / +0.025 / +0.036 (0) | +0.018 / +0.035 / +0.077 (0) | +0.015 / +0.026 / +0.040 (0) | +0.002 / +0.017 / +0.029 (0) | +0.013 / +0.030 / +0.057 (0) |
| propio | como el ATD | control | -0.001 / +0.052 / +0.060 (1) | +0.021 / +0.042 / +0.060 (0) | +0.006 / +0.055 / +0.063 (0) | +0.010 / +0.044 / +0.058 (0) | +0.022 / +0.027 / +0.049 (0) | +0.007 / +0.048 / +0.060 (0) |
| propio | como el ATD | flag | +0.032 / +0.041 / +0.064 (0) | +0.015 / +0.022 / +0.042 (0) | +0.029 / +0.044 / +0.063 (0) | +0.011 / +0.019 / +0.039 (0) | +0.002 / +0.013 / +0.028 (0) | +0.020 / +0.030 / +0.052 (0) |
| propio | como el ATD, sin bloques | control | -0.010 / +0.046 / +0.058 (1) | +0.011 / +0.036 / +0.047 (0) | -0.003 / +0.034 / +0.067 (1) | +0.002 / +0.034 / +0.055 (0) | +0.006 / +0.025 / +0.029 (0) | -0.009 / +0.041 / +0.048 (1) |
| propio | como el ATD, sin bloques | flag | +0.019 / +0.033 / +0.055 (0) | +0.006 / +0.014 / +0.030 (0) | +0.013 / +0.030 / +0.058 (0) | +0.005 / +0.016 / +0.035 (0) | +0.000 / +0.009 / +0.025 (0) | +0.009 / +0.024 / +0.042 (0) |
| propio, balón a la vista en los D | como el ATD | control | -0.016 / +0.048 / +0.072 (1) | +0.006 / +0.041 / +0.063 (0) | -0.006 / +0.051 / +0.072 (1) | +0.011 / +0.046 / +0.059 (0) | +0.013 / +0.023 / +0.042 (0) | -0.004 / +0.047 / +0.067 (1) |
| propio, balón a la vista en los D | como el ATD | flag | +0.019 / +0.034 / +0.066 (0) | +0.001 / +0.023 / +0.032 (0) | +0.028 / +0.030 / +0.059 (0) | +0.003 / +0.026 / +0.028 (0) | -0.007 / +0.013 / +0.023 (1) | +0.014 / +0.028 / +0.049 (0) |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | -0.026 / +0.041 / +0.057 (1) | -0.007 / +0.037 / +0.043 (1) | -0.011 / +0.041 / +0.056 (1) | -0.000 / +0.037 / +0.042 (1) | +0.008 / +0.019 / +0.027 (0) | -0.012 / +0.042 / +0.056 (1) |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | +0.012 / +0.021 / +0.067 (0) | -0.003 / +0.014 / +0.025 (1) | +0.012 / +0.028 / +0.061 (0) | -0.001 / +0.021 / +0.024 (1) | -0.005 / +0.009 / +0.018 (2) | +0.007 / +0.025 / +0.044 (0) |

Veces que queda por debajo de `main`, de 84 (partido y celda): K2, 5; K3, 2; K4, 3; K5, 2; K3 con 1/4 de K2, 3; K3 con 3/4 de K2, 3.

## Posesiones reales encontradas (descriptivo, sin voto; solape de 0,5 o más)

| `D` | condición | etiquetas | versión | reales | predichas | encontradas | de las reales | de las predichas |
|---|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | main | 1736 | 1661 | 1259 | 72.5 % | 75.8 % |
| etiquetas | como el ATD | control | K2 | 1736 | 1651 | 1335 | 76.9 % | 80.9 % |
| etiquetas | como el ATD | control | K3 | 1736 | 1597 | 1317 | 75.9 % | 82.5 % |
| etiquetas | como el ATD | control | K4 | 1736 | 1643 | 1348 | 77.6 % | 82.0 % |
| etiquetas | como el ATD | control | K5 | 1736 | 1602 | 1316 | 75.8 % | 82.1 % |
| etiquetas | como el ATD | flag | main | 3061 | 1661 | 1198 | 39.1 % | 72.1 % |
| etiquetas | como el ATD | flag | K2 | 3061 | 1651 | 1300 | 42.5 % | 78.7 % |
| etiquetas | como el ATD | flag | K3 | 3061 | 1597 | 1255 | 41.0 % | 78.6 % |
| etiquetas | como el ATD | flag | K4 | 3061 | 1643 | 1302 | 42.5 % | 79.2 % |
| etiquetas | como el ATD | flag | K5 | 3061 | 1602 | 1258 | 41.1 % | 78.5 % |
| etiquetas | como el ATD, sin bloques | control | main | 1736 | 1675 | 1296 | 74.7 % | 77.4 % |
| etiquetas | como el ATD, sin bloques | control | K2 | 1736 | 1673 | 1368 | 78.8 % | 81.8 % |
| etiquetas | como el ATD, sin bloques | control | K3 | 1736 | 1609 | 1337 | 77.0 % | 83.1 % |
| etiquetas | como el ATD, sin bloques | control | K4 | 1736 | 1661 | 1374 | 79.1 % | 82.7 % |
| etiquetas | como el ATD, sin bloques | control | K5 | 1736 | 1621 | 1344 | 77.4 % | 82.9 % |
| etiquetas | como el ATD, sin bloques | flag | main | 3061 | 1675 | 1241 | 40.5 % | 74.1 % |
| etiquetas | como el ATD, sin bloques | flag | K2 | 3061 | 1673 | 1315 | 43.0 % | 78.6 % |
| etiquetas | como el ATD, sin bloques | flag | K3 | 3061 | 1609 | 1270 | 41.5 % | 78.9 % |
| etiquetas | como el ATD, sin bloques | flag | K4 | 3061 | 1661 | 1314 | 42.9 % | 79.1 % |
| etiquetas | como el ATD, sin bloques | flag | K5 | 3061 | 1621 | 1282 | 41.9 % | 79.1 % |
| propio | como el ATD | control | main | 1736 | 1538 | 1039 | 59.9 % | 67.6 % |
| propio | como el ATD | control | K2 | 1736 | 1574 | 1127 | 64.9 % | 71.6 % |
| propio | como el ATD | control | K3 | 1736 | 1507 | 1093 | 63.0 % | 72.5 % |
| propio | como el ATD | control | K4 | 1736 | 1570 | 1130 | 65.1 % | 72.0 % |
| propio | como el ATD | control | K5 | 1736 | 1510 | 1091 | 62.8 % | 72.3 % |
| propio | como el ATD | flag | main | 3061 | 1538 | 960 | 31.4 % | 62.4 % |
| propio | como el ATD | flag | K2 | 3061 | 1574 | 1076 | 35.2 % | 68.4 % |
| propio | como el ATD | flag | K3 | 3061 | 1507 | 1019 | 33.3 % | 67.6 % |
| propio | como el ATD | flag | K4 | 3061 | 1570 | 1072 | 35.0 % | 68.3 % |
| propio | como el ATD | flag | K5 | 3061 | 1510 | 1017 | 33.2 % | 67.4 % |
| propio | como el ATD, sin bloques | control | main | 1736 | 1537 | 1089 | 62.7 % | 70.9 % |
| propio | como el ATD, sin bloques | control | K2 | 1736 | 1580 | 1161 | 66.9 % | 73.5 % |
| propio | como el ATD, sin bloques | control | K3 | 1736 | 1507 | 1122 | 64.6 % | 74.5 % |
| propio | como el ATD, sin bloques | control | K4 | 1736 | 1574 | 1161 | 66.9 % | 73.8 % |
| propio | como el ATD, sin bloques | control | K5 | 1736 | 1517 | 1125 | 64.8 % | 74.2 % |
| propio | como el ATD, sin bloques | flag | main | 3061 | 1537 | 1008 | 32.9 % | 65.6 % |
| propio | como el ATD, sin bloques | flag | K2 | 3061 | 1580 | 1097 | 35.8 % | 69.4 % |
| propio | como el ATD, sin bloques | flag | K3 | 3061 | 1507 | 1045 | 34.1 % | 69.3 % |
| propio | como el ATD, sin bloques | flag | K4 | 3061 | 1574 | 1093 | 35.7 % | 69.4 % |
| propio | como el ATD, sin bloques | flag | K5 | 3061 | 1517 | 1050 | 34.3 % | 69.2 % |
| propio, balón a la vista en los D | como el ATD | control | main | 1736 | 1613 | 998 | 57.5 % | 61.9 % |
| propio, balón a la vista en los D | como el ATD | control | K2 | 1736 | 1614 | 1070 | 61.6 % | 66.3 % |
| propio, balón a la vista en los D | como el ATD | control | K3 | 1736 | 1577 | 1053 | 60.7 % | 66.8 % |
| propio, balón a la vista en los D | como el ATD | control | K4 | 1736 | 1606 | 1077 | 62.0 % | 67.1 % |
| propio, balón a la vista en los D | como el ATD | control | K5 | 1736 | 1574 | 1050 | 60.5 % | 66.7 % |
| propio, balón a la vista en los D | como el ATD | flag | main | 3061 | 1613 | 927 | 30.3 % | 57.5 % |
| propio, balón a la vista en los D | como el ATD | flag | K2 | 3061 | 1614 | 1009 | 33.0 % | 62.5 % |
| propio, balón a la vista en los D | como el ATD | flag | K3 | 3061 | 1577 | 985 | 32.2 % | 62.5 % |
| propio, balón a la vista en los D | como el ATD | flag | K4 | 3061 | 1606 | 1016 | 33.2 % | 63.3 % |
| propio, balón a la vista en los D | como el ATD | flag | K5 | 3061 | 1574 | 975 | 31.9 % | 61.9 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | main | 1736 | 1621 | 1047 | 60.3 % | 64.6 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | K2 | 1736 | 1625 | 1110 | 63.9 % | 68.3 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | K3 | 1736 | 1575 | 1077 | 62.0 % | 68.4 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | K4 | 1736 | 1616 | 1113 | 64.1 % | 68.9 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | K5 | 1736 | 1586 | 1077 | 62.0 % | 67.9 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | main | 3061 | 1621 | 965 | 31.5 % | 59.5 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | K2 | 3061 | 1625 | 1038 | 33.9 % | 63.9 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | K3 | 3061 | 1575 | 999 | 32.6 % | 63.4 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | K4 | 3061 | 1616 | 1045 | 34.1 % | 64.7 % |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | K5 | 3061 | 1586 | 1000 | 32.7 % | 63.1 % |
