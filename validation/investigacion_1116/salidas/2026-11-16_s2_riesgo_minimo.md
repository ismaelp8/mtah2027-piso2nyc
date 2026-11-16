## 1. Temperatura

Verosimilitud negativa media por frame vivo (menos es mejor), los 7 partidos juntos:

| T | flag | control |
|---|---|---|
| 1 | 5.611 | 3.571 |
| 2 | 3.242 | 2.013 |
| 4 | 1.584 | 0.987 |
| 8 | 0.705 | 0.438 |
| 16 | 0.337 | 0.242 |
| 32 | 0.414 | 0.385 |

T elegida para cada partido con los otros seis: 16, 16, 16, 16, 16, 16, 16

## 2. La anchura de la duda frente al error de cada cambio de `main`

| etiquetas | cambios de `main` | con pareja a ±50 | Spearman anchura–error (con pareja) | AUC: anchura separa los sin pareja | anchura mediana con / sin pareja |
|---|---|---|---|---|---|
| flag | 951 | 723 | 0.09 | 0.60 | 45 / 64 |
| control | 951 | 588 | 0.14 | 0.69 | 39 / 70 |

## 3. Elegir por parte el Viterbi con más spellF1 esperado

Coste elegido en cada una de las 14 partes: 8, 8, 8, 8, 8, 12, 8, 8, 8, 8, 8, 8, 8, 8
Posesiones en una muestra, por parte: mediana 2685 (mín 1340 – máx 5046)

| etiquetas | coste 8 | coste 12 | coste 18 | coste 25 | coste 35 | coste 50 | elegido por parte (riesgo mínimo) | mejor por parte (oráculo) |
|---|---|---|---|---|---|---|---|---|
| flag | 0.497 | 0.498 | 0.499 | 0.498 | 0.496 | 0.494 | 0.497 | 0.504 |
| control | 0.704 | 0.712 | 0.721 | 0.728 | 0.733 | 0.738 | 0.704 | 0.741 |

spellF1 esperado frente a las muestras, media de las 14 partes: coste 8: 0.027, coste 12: 0.026, coste 18: 0.025, coste 25: 0.025, coste 35: 0.024, coste 50: 0.023
