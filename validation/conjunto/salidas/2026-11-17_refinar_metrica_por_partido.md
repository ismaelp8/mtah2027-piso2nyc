# Refinamientos de K2 sin reentrenar · Metrica · 3 partidos

Código: 8409165 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `conjunto_pesos.npz` (sha256 6d16316f85063f13…): los de la entrega (todos los partidos). B5: los coeficientes de la entrega (nunca vio este proveedor).

## Partido a partido, frente a `main` (descriptivo, sin voto)

Cada casilla: peor partido / mediana / mejor partido, y en cuántos partidos queda por debajo de `main`.

| `D` | condición | etiquetas | K2 | K3 | K4 | K5 | K3 con 1/4 de K2 | K3 con 3/4 de K2 |
|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | -0.000 / +0.036 / +0.069 (1) | +0.010 / +0.028 / +0.031 (0) | +0.008 / +0.026 / +0.071 (0) | +0.010 / +0.028 / +0.032 (0) | +0.003 / +0.011 / +0.020 (0) | +0.007 / +0.028 / +0.052 (0) |
| etiquetas | suavizado 25 | eventos | +0.007 / +0.041 / +0.058 (0) | +0.009 / +0.035 / +0.044 (0) | +0.011 / +0.044 / +0.060 (0) | +0.011 / +0.039 / +0.052 (0) | +0.005 / +0.014 / +0.019 (0) | +0.015 / +0.038 / +0.053 (0) |
| propio | tal cual | eventos | -0.015 / +0.031 / +0.045 (1) | +0.002 / +0.020 / +0.021 (0) | -0.006 / +0.026 / +0.051 (1) | +0.003 / +0.019 / +0.020 (0) | -0.003 / +0.009 / +0.014 (1) | -0.003 / +0.030 / +0.041 (1) |
| propio | suavizado 25 | eventos | +0.000 / +0.033 / +0.036 (0) | +0.000 / +0.020 / +0.030 (0) | +0.002 / +0.027 / +0.036 (0) | -0.001 / +0.021 / +0.032 (1) | +0.000 / +0.013 / +0.020 (0) | +0.006 / +0.030 / +0.034 (0) |

Veces que queda por debajo de `main`, de 12 (partido y celda): K2, 2; K3, 0; K4, 1; K5, 1; K3 con 1/4 de K2, 1; K3 con 3/4 de K2, 1.

## Posesiones reales encontradas (descriptivo, sin voto; solape de 0,5 o más)

| `D` | condición | etiquetas | versión | reales | predichas | encontradas | de las reales | de las predichas |
|---|---|---|---|---|---|---|---|---|
| etiquetas | tal cual | eventos | main | 879 | 612 | 505 | 57.5 % | 82.5 % |
| etiquetas | tal cual | eventos | K2 | 879 | 624 | 533 | 60.6 % | 85.4 % |
| etiquetas | tal cual | eventos | K3 | 879 | 607 | 517 | 58.8 % | 85.2 % |
| etiquetas | tal cual | eventos | K4 | 879 | 629 | 535 | 60.9 % | 85.1 % |
| etiquetas | tal cual | eventos | K5 | 879 | 607 | 519 | 59.0 % | 85.5 % |
| etiquetas | suavizado 25 | eventos | main | 879 | 611 | 494 | 56.2 % | 80.9 % |
| etiquetas | suavizado 25 | eventos | K2 | 879 | 623 | 524 | 59.6 % | 84.1 % |
| etiquetas | suavizado 25 | eventos | K3 | 879 | 608 | 514 | 58.5 % | 84.5 % |
| etiquetas | suavizado 25 | eventos | K4 | 879 | 628 | 527 | 60.0 % | 83.9 % |
| etiquetas | suavizado 25 | eventos | K5 | 879 | 609 | 520 | 59.2 % | 85.4 % |
| propio | tal cual | eventos | main | 879 | 639 | 425 | 48.4 % | 66.5 % |
| propio | tal cual | eventos | K2 | 879 | 641 | 437 | 49.7 % | 68.2 % |
| propio | tal cual | eventos | K3 | 879 | 642 | 432 | 49.1 % | 67.3 % |
| propio | tal cual | eventos | K4 | 879 | 650 | 441 | 50.2 % | 67.8 % |
| propio | tal cual | eventos | K5 | 879 | 642 | 433 | 49.3 % | 67.4 % |
| propio | suavizado 25 | eventos | main | 879 | 641 | 417 | 47.4 % | 65.1 % |
| propio | suavizado 25 | eventos | K2 | 879 | 644 | 432 | 49.1 % | 67.1 % |
| propio | suavizado 25 | eventos | K3 | 879 | 637 | 425 | 48.4 % | 66.7 % |
| propio | suavizado 25 | eventos | K4 | 879 | 645 | 431 | 49.0 % | 66.8 % |
| propio | suavizado 25 | eventos | K5 | 879 | 634 | 426 | 48.5 % | 67.2 % |
