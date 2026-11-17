# Riesgo mínimo con la evidencia de K2 (el sondeo S2 del 16/11, con K2 en lugar de B5)

Código: 10c899f. Lo que el instrumento llama `main` es aquí el Viterbi de coste 25 sobre K2.

## 1. Temperatura

Verosimilitud negativa media por frame vivo (menos es mejor), los 7 partidos juntos:

| T | flag | control |
|---|---|---|
| 1 | 4.856 | 2.700 |
| 2 | 2.915 | 1.552 |
| 4 | 1.430 | 0.764 |
| 8 | 0.651 | 0.346 |
| 16 | 0.300 | 0.183 |
| 32 | 0.328 | 0.290 |

T elegida para cada partido con los otros seis: 16, 16, 16, 16, 16, 16, 16

## 2. La anchura de la duda frente al error de cada cambio de `main`

| etiquetas | cambios de `main` | con pareja a ±50 | Spearman anchura–error (con pareja) | AUC: anchura separa los sin pareja | anchura mediana con / sin pareja |
|---|---|---|---|---|---|
| flag | 941 | 796 | 0.24 | 0.68 | 31 / 57 |
| control | 941 | 667 | 0.25 | 0.70 | 29 / 54 |

## 3. Elegir por parte el Viterbi con más spellF1 esperado

Coste elegido en cada una de las 14 partes: 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 18, 8, 8
Posesiones en una muestra, por parte: mediana 2196 (mín 1044 – máx 2963)

| etiquetas | coste 8 | coste 12 | coste 18 | coste 25 | coste 35 | coste 50 | elegido por parte (riesgo mínimo) | mejor por parte (oráculo) |
|---|---|---|---|---|---|---|---|---|
| flag | 0.549 | 0.546 | 0.545 | 0.542 | 0.540 | 0.536 | 0.549 | 0.551 |
| control | 0.761 | 0.766 | 0.774 | 0.780 | 0.784 | 0.786 | 0.761 | 0.790 |

spellF1 esperado frente a las muestras, media de las 14 partes: coste 8: 0.061, coste 12: 0.060, coste 18: 0.059, coste 25: 0.058, coste 35: 0.057, coste 50: 0.056
