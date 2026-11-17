# Refinamientos de K2 sin reentrenar · SkillCorner, mitad de entrenamiento · 10 partidos

Código: d96fce8 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · pesos de K2: los de `conjunto_pesos.npz` (sha256 6d16316f85063f13…): cada partido con el pliegue que no lo vio. B5: los coeficientes de la entrega (nunca vio este proveedor).

## Partido a partido, frente a `main` (descriptivo, sin voto)

Cada casilla: peor partido / mediana / mejor partido, y en cuántos partidos queda por debajo de `main`.

| `D` | condición | etiquetas | K2 | K3 | K4 | K5 | K3 con 1/4 de K2 | K3 con 3/4 de K2 |
|---|---|---|---|---|---|---|---|---|
| etiquetas | detectado | sc | -0.013 / +0.019 / +0.051 (2) | +0.006 / +0.022 / +0.039 (0) | -0.012 / +0.025 / +0.052 (2) | +0.005 / +0.021 / +0.034 (0) | -0.001 / +0.013 / +0.025 (1) | -0.002 / +0.030 / +0.050 (1) |
| etiquetas | detectado, suavizado | sc | -0.016 / +0.025 / +0.058 (3) | -0.005 / +0.026 / +0.041 (1) | -0.005 / +0.030 / +0.059 (2) | -0.003 / +0.024 / +0.037 (1) | -0.007 / +0.013 / +0.032 (1) | -0.010 / +0.035 / +0.051 (1) |
| propio | detectado | sc | +0.003 / +0.020 / +0.042 (0) | +0.006 / +0.018 / +0.022 (0) | -0.001 / +0.021 / +0.040 (1) | +0.007 / +0.016 / +0.032 (0) | +0.002 / +0.013 / +0.020 (0) | +0.006 / +0.021 / +0.038 (0) |
| propio | detectado, suavizado | sc | +0.010 / +0.022 / +0.045 (0) | +0.004 / +0.018 / +0.036 (0) | +0.008 / +0.025 / +0.038 (0) | +0.006 / +0.019 / +0.035 (0) | -0.001 / +0.014 / +0.024 (1) | +0.010 / +0.025 / +0.035 (0) |

Veces que queda por debajo de `main`, de 40 (partido y celda): K2, 5; K3, 1; K4, 5; K5, 1; K3 con 1/4 de K2, 3; K3 con 3/4 de K2, 2.
