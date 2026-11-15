# Puerta: ¿la dirección del balón mueve las posesiones de 2 a 10 s? (DFL, en los mismos 7 partidos)

Filas: 103135. Pesos de dirección (rasgos divididos por su raíz cuadrática media): +0.04, +0.40, +0.63.

## Condición «como el ATD»

### B2 reentrenada en los 7 (referencia justa), α = 2, etiquetas «flag»

spellF1 0.498 · posesiones reales 3061 · nuestras 1609 · encontradas con IoU ≥ 0,5: 1188 (39 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 2 % | 73 % | 25 % | 0 % |
| 1–2 s | 535 | 9 % | 57 % | 34 % | 0 % |
| 2–5 s | 934 | 27 % | 41 % | 32 % | 1 % |
| 5–10 s | 569 | 59 % | 12 % | 29 % | 0 % |
| ≥ 10 s | 639 | 85 % | 1 % | 13 % | 1 % |
| **de las 1873 no encontradas** | | | 56 % | 44 % | 1 % |

Posesiones nuestras que sobran: 421 de 1609 (26 %). Por causa: otro equipo 43 %; más larga que la real 40 %; más corta que la real 16 %.

Cambios directos de equipo: 2351 reales y 899 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 11 % | 19 % | 30 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +2, p25 -9, p75 +14; 454 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 4, etiquetas «flag»

spellF1 0.499 · posesiones reales 3061 · nuestras 1664 · encontradas con IoU ≥ 0,5: 1206 (39 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 3 % | 73 % | 24 % | 0 % |
| 1–2 s | 535 | 10 % | 56 % | 33 % | 0 % |
| 2–5 s | 934 | 28 % | 40 % | 31 % | 1 % |
| 5–10 s | 569 | 59 % | 12 % | 29 % | 0 % |
| ≥ 10 s | 639 | 85 % | 1 % | 13 % | 1 % |
| **de las 1855 no encontradas** | | | 56 % | 44 % | 1 % |

Posesiones nuestras que sobran: 458 de 1664 (28 %). Por causa: otro equipo 46 %; más larga que la real 36 %; más corta que la real 18 %.

Cambios directos de equipo: 2351 reales y 954 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 11 % | 20 % | 31 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +2, p25 -9, p75 +14; 466 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 8, etiquetas «flag»

spellF1 0.499 · posesiones reales 3061 · nuestras 1707 · encontradas con IoU ≥ 0,5: 1219 (40 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 3 % | 73 % | 24 % | 0 % |
| 1–2 s | 535 | 11 % | 56 % | 33 % | 0 % |
| 2–5 s | 934 | 28 % | 40 % | 31 % | 1 % |
| 5–10 s | 569 | 59 % | 12 % | 29 % | 0 % |
| ≥ 10 s | 639 | 86 % | 1 % | 12 % | 1 % |
| **de las 1842 no encontradas** | | | 56 % | 43 % | 1 % |

Posesiones nuestras que sobran: 488 de 1707 (29 %). Por causa: otro equipo 45 %; más larga que la real 34 %; más corta que la real 20 %.

Cambios directos de equipo: 2351 reales y 997 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 11 % | 20 % | 32 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +3, p25 -9, p75 +14; 480 parejas.

### B2 + dirección del balón, en los 7, α = 2, etiquetas «flag»

spellF1 0.537 · posesiones reales 3061 · nuestras 1749 · encontradas con IoU ≥ 0,5: 1303 (43 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 3 % | 74 % | 24 % | 0 % |
| 1–2 s | 535 | 13 % | 55 % | 32 % | 0 % |
| 2–5 s | 934 | 34 % | 35 % | 30 % | 1 % |
| 5–10 s | 569 | 63 % | 9 % | 27 % | 0 % |
| ≥ 10 s | 639 | 86 % | 1 % | 12 % | 1 % |
| **de las 1758 no encontradas** | | | 55 % | 44 % | 1 % |

Posesiones nuestras que sobran: 446 de 1749 (26 %). Por causa: otro equipo 41 %; más larga que la real 39 %; más corta que la real 20 %.

Cambios directos de equipo: 2351 reales y 1039 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 17 % | 25 % | 35 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +0, p25 -8, p75 +10; 595 parejas.

### B2 + dirección del balón, en los 7, α = 4, etiquetas «flag»

spellF1 0.547 · posesiones reales 3061 · nuestras 1864 · encontradas con IoU ≥ 0,5: 1357 (44 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 3 % | 73 % | 24 % | 0 % |
| 1–2 s | 535 | 16 % | 52 % | 32 % | 0 % |
| 2–5 s | 934 | 36 % | 34 % | 29 % | 1 % |
| 5–10 s | 569 | 64 % | 10 % | 25 % | 1 % |
| ≥ 10 s | 639 | 87 % | 1 % | 11 % | 1 % |
| **de las 1704 no encontradas** | | | 55 % | 43 % | 1 % |

Posesiones nuestras que sobran: 507 de 1864 (27 %). Por causa: otro equipo 43 %; más larga que la real 32 %; más corta que la real 25 %.

Cambios directos de equipo: 2351 reales y 1154 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 18 % | 28 % | 38 % |
| placebo: los mismos, desplazados 60 s | 1 % | 3 % | 6 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +2, p25 -7, p75 +10; 664 parejas.

### B2 + dirección del balón, en los 7, α = 8, etiquetas «flag»

spellF1 0.550 · posesiones reales 3061 · nuestras 1945 · encontradas con IoU ≥ 0,5: 1394 (46 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 4 % | 72 % | 24 % | 0 % |
| 1–2 s | 535 | 19 % | 50 % | 31 % | 0 % |
| 2–5 s | 934 | 38 % | 34 % | 27 % | 1 % |
| 5–10 s | 569 | 65 % | 10 % | 24 % | 1 % |
| ≥ 10 s | 639 | 87 % | 1 % | 10 % | 1 % |
| **de las 1667 no encontradas** | | | 55 % | 43 % | 2 % |

Posesiones nuestras que sobran: 551 de 1945 (28 %). Por causa: otro equipo 45 %; más larga que la real 28 %; más corta que la real 27 %.

Cambios directos de equipo: 2351 reales y 1235 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 19 % | 29 % | 39 % |
| placebo: los mismos, desplazados 60 s | 1 % | 3 % | 6 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +2, p25 -7, p75 +10; 691 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 2, etiquetas «control»

spellF1 0.736 · posesiones reales 1736 · nuestras 1609 · encontradas con IoU ≥ 0,5: 1253 (72 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 15 % | 62 % | 23 % | 0 % |
| 1–2 s | 111 | 21 % | 49 % | 31 % | 0 % |
| 2–5 s | 399 | 53 % | 29 % | 18 % | 1 % |
| 5–10 s | 437 | 77 % | 14 % | 8 % | 0 % |
| ≥ 10 s | 741 | 91 % | 2 % | 4 % | 2 % |
| **de las 483 no encontradas** | | | 58 % | 38 % | 4 % |

Posesiones nuestras que sobran: 356 de 1609 (22 %). Por causa: otro equipo 56 %; más larga que la real 9 %; más corta que la real 35 %.

Cambios directos de equipo: 1026 reales y 899 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 20 % | 37 % | 56 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +0, p25 -10, p75 +13; 377 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 4, etiquetas «control»

spellF1 0.730 · posesiones reales 1736 · nuestras 1664 · encontradas con IoU ≥ 0,5: 1262 (73 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 15 % | 62 % | 23 % | 0 % |
| 1–2 s | 111 | 24 % | 48 % | 28 % | 0 % |
| 2–5 s | 399 | 54 % | 28 % | 18 % | 1 % |
| 5–10 s | 437 | 77 % | 15 % | 8 % | 0 % |
| ≥ 10 s | 741 | 91 % | 2 % | 4 % | 2 % |
| **de las 474 no encontradas** | | | 58 % | 38 % | 4 % |

Posesiones nuestras que sobran: 402 de 1664 (24 %). Por causa: otro equipo 55 %; más larga que la real 8 %; más corta que la real 36 %.

Cambios directos de equipo: 1026 reales y 954 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 21 % | 37 % | 57 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -10, p75 +13; 378 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 8, etiquetas «control»

spellF1 0.723 · posesiones reales 1736 · nuestras 1707 · encontradas con IoU ≥ 0,5: 1265 (73 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 17 % | 62 % | 21 % | 0 % |
| 1–2 s | 111 | 27 % | 48 % | 24 % | 1 % |
| 2–5 s | 399 | 55 % | 28 % | 17 % | 1 % |
| 5–10 s | 437 | 76 % | 15 % | 8 % | 0 % |
| ≥ 10 s | 741 | 91 % | 2 % | 4 % | 2 % |
| **de las 471 no encontradas** | | | 59 % | 36 % | 5 % |

Posesiones nuestras que sobran: 442 de 1707 (26 %). Por causa: otro equipo 54 %; más larga que la real 7 %; más corta que la real 39 %.

Cambios directos de equipo: 1026 reales y 997 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 20 % | 37 % | 58 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -10, p75 +13; 384 parejas.

### B2 + dirección del balón, en los 7, α = 2, etiquetas «control»

spellF1 0.741 · posesiones reales 1736 · nuestras 1749 · encontradas con IoU ≥ 0,5: 1311 (76 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 17 % | 62 % | 21 % | 0 % |
| 1–2 s | 111 | 25 % | 50 % | 24 % | 0 % |
| 2–5 s | 399 | 62 % | 23 % | 14 % | 1 % |
| 5–10 s | 437 | 81 % | 11 % | 7 % | 2 % |
| ≥ 10 s | 741 | 91 % | 2 % | 3 % | 3 % |
| **de las 425 no encontradas** | | | 57 % | 35 % | 8 % |

Posesiones nuestras que sobran: 438 de 1749 (25 %). Por causa: otro equipo 53 %; más larga que la real 5 %; más corta que la real 42 %.

Cambios directos de equipo: 1026 reales y 1039 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 29 % | 44 % | 61 % |
| placebo: los mismos, desplazados 60 s | 2 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +0, p25 -9, p75 +9; 453 parejas.

### B2 + dirección del balón, en los 7, α = 4, etiquetas «control»

spellF1 0.722 · posesiones reales 1736 · nuestras 1864 · encontradas con IoU ≥ 0,5: 1311 (76 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 17 % | 62 % | 21 % | 0 % |
| 1–2 s | 111 | 31 % | 46 % | 23 % | 1 % |
| 2–5 s | 399 | 63 % | 22 % | 13 % | 2 % |
| 5–10 s | 437 | 79 % | 12 % | 6 % | 2 % |
| ≥ 10 s | 741 | 91 % | 2 % | 3 % | 4 % |
| **de las 425 no encontradas** | | | 56 % | 32 % | 12 % |

Posesiones nuestras que sobran: 553 de 1864 (30 %). Por causa: otro equipo 51 %; más larga que la real 4 %; más corta que la real 45 %.

Cambios directos de equipo: 1026 reales y 1154 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 29 % | 47 % | 63 % |
| placebo: los mismos, desplazados 60 s | 1 % | 3 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -8, p75 +10; 479 parejas.

### B2 + dirección del balón, en los 7, α = 8, etiquetas «control»

spellF1 0.708 · posesiones reales 1736 · nuestras 1945 · encontradas con IoU ≥ 0,5: 1320 (76 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 17 % | 62 % | 21 % | 0 % |
| 1–2 s | 111 | 33 % | 44 % | 22 % | 1 % |
| 2–5 s | 399 | 63 % | 21 % | 13 % | 3 % |
| 5–10 s | 437 | 80 % | 12 % | 5 % | 3 % |
| ≥ 10 s | 741 | 91 % | 2 % | 3 % | 4 % |
| **de las 416 no encontradas** | | | 56 % | 31 % | 13 % |

Posesiones nuestras que sobran: 625 de 1945 (32 %). Por causa: otro equipo 52 %; más larga que la real 4 %; más corta que la real 45 %.

Cambios directos de equipo: 1026 reales y 1235 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 29 % | 47 % | 65 % |
| placebo: los mismos, desplazados 60 s | 1 % | 3 % | 6 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -9, p75 +10; 483 parejas.

## Condición «como el ATD, sin bloques»

### B2 reentrenada en los 7 (referencia justa), α = 2, etiquetas «flag»

spellF1 0.512 · posesiones reales 3061 · nuestras 1626 · encontradas con IoU ≥ 0,5: 1232 (40 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 3 % | 72 % | 25 % | 0 % |
| 1–2 s | 535 | 9 % | 57 % | 33 % | 0 % |
| 2–5 s | 934 | 28 % | 40 % | 31 % | 1 % |
| 5–10 s | 569 | 62 % | 10 % | 28 % | 0 % |
| ≥ 10 s | 639 | 87 % | 1 % | 12 % | 0 % |
| **de las 1829 no encontradas** | | | 56 % | 44 % | 0 % |

Posesiones nuestras que sobran: 394 de 1626 (24 %). Por causa: otro equipo 43 %; más larga que la real 42 %; más corta que la real 15 %.

Cambios directos de equipo: 2351 reales y 916 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 12 % | 21 % | 31 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -10, p75 +13; 495 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 4, etiquetas «flag»

spellF1 0.513 · posesiones reales 3061 · nuestras 1681 · encontradas con IoU ≥ 0,5: 1252 (41 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 3 % | 73 % | 24 % | 0 % |
| 1–2 s | 535 | 11 % | 57 % | 32 % | 0 % |
| 2–5 s | 934 | 29 % | 39 % | 31 % | 1 % |
| 5–10 s | 569 | 62 % | 10 % | 27 % | 0 % |
| ≥ 10 s | 639 | 87 % | 0 % | 12 % | 0 % |
| **de las 1809 no encontradas** | | | 56 % | 43 % | 1 % |

Posesiones nuestras que sobran: 429 de 1681 (26 %). Por causa: otro equipo 46 %; más larga que la real 36 %; más corta que la real 17 %.

Cambios directos de equipo: 2351 reales y 971 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 12 % | 22 % | 33 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +2, p25 -9, p75 +14; 506 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 8, etiquetas «flag»

spellF1 0.513 · posesiones reales 3061 · nuestras 1717 · encontradas con IoU ≥ 0,5: 1263 (41 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 3 % | 73 % | 24 % | 0 % |
| 1–2 s | 535 | 12 % | 57 % | 31 % | 0 % |
| 2–5 s | 934 | 30 % | 39 % | 30 % | 1 % |
| 5–10 s | 569 | 62 % | 10 % | 28 % | 0 % |
| ≥ 10 s | 639 | 88 % | 0 % | 12 % | 0 % |
| **de las 1798 no encontradas** | | | 56 % | 43 % | 1 % |

Posesiones nuestras que sobran: 454 de 1717 (26 %). Por causa: otro equipo 45 %; más larga que la real 35 %; más corta que la real 20 %.

Cambios directos de equipo: 2351 reales y 1007 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 12 % | 22 % | 33 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +3, p25 -9, p75 +14; 523 parejas.

### B2 + dirección del balón, en los 7, α = 2, etiquetas «flag»

spellF1 0.558 · posesiones reales 3061 · nuestras 1792 · encontradas con IoU ≥ 0,5: 1375 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 3 % | 72 % | 24 % | 0 % |
| 1–2 s | 535 | 14 % | 55 % | 31 % | 0 % |
| 2–5 s | 934 | 37 % | 33 % | 29 % | 1 % |
| 5–10 s | 569 | 66 % | 8 % | 26 % | 0 % |
| ≥ 10 s | 639 | 89 % | 1 % | 10 % | 0 % |
| **de las 1686 no encontradas** | | | 55 % | 44 % | 1 % |

Posesiones nuestras que sobran: 417 de 1792 (23 %). Por causa: otro equipo 42 %; más larga que la real 39 %; más corta que la real 19 %.

Cambios directos de equipo: 2351 reales y 1082 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 19 % | 28 % | 38 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +0, p25 -8, p75 +9; 659 parejas.

### B2 + dirección del balón, en los 7, α = 4, etiquetas «flag»

spellF1 0.572 · posesiones reales 3061 · nuestras 1912 · encontradas con IoU ≥ 0,5: 1442 (47 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 4 % | 72 % | 24 % | 0 % |
| 1–2 s | 535 | 19 % | 51 % | 30 % | 0 % |
| 2–5 s | 934 | 40 % | 32 % | 28 % | 1 % |
| 5–10 s | 569 | 67 % | 9 % | 23 % | 1 % |
| ≥ 10 s | 639 | 90 % | 1 % | 9 % | 1 % |
| **de las 1619 no encontradas** | | | 56 % | 43 % | 1 % |

Posesiones nuestras que sobran: 470 de 1912 (25 %). Por causa: otro equipo 43 %; más larga que la real 32 %; más corta que la real 25 %.

Cambios directos de equipo: 2351 reales y 1202 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 20 % | 31 % | 41 % |
| placebo: los mismos, desplazados 60 s | 2 % | 3 % | 6 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -7, p75 +10; 737 parejas.

### B2 + dirección del balón, en los 7, α = 8, etiquetas «flag»

spellF1 0.575 · posesiones reales 3061 · nuestras 1999 · encontradas con IoU ≥ 0,5: 1482 (48 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 4 % | 71 % | 25 % | 0 % |
| 1–2 s | 535 | 21 % | 49 % | 29 % | 0 % |
| 2–5 s | 934 | 42 % | 31 % | 26 % | 1 % |
| 5–10 s | 569 | 68 % | 8 % | 22 % | 1 % |
| ≥ 10 s | 639 | 90 % | 1 % | 9 % | 1 % |
| **de las 1579 no encontradas** | | | 56 % | 43 % | 2 % |

Posesiones nuestras que sobran: 517 de 1999 (26 %). Por causa: otro equipo 45 %; más larga que la real 27 %; más corta que la real 27 %.

Cambios directos de equipo: 2351 reales y 1289 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 21 % | 33 % | 43 % |
| placebo: los mismos, desplazados 60 s | 2 % | 3 % | 7 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +2, p25 -7, p75 +10; 776 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 2, etiquetas «control»

spellF1 0.756 · posesiones reales 1736 · nuestras 1626 · encontradas con IoU ≥ 0,5: 1292 (74 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 17 % | 60 % | 23 % | 0 % |
| 1–2 s | 111 | 23 % | 47 % | 31 % | 0 % |
| 2–5 s | 399 | 55 % | 27 % | 17 % | 1 % |
| 5–10 s | 437 | 79 % | 12 % | 8 % | 1 % |
| ≥ 10 s | 741 | 94 % | 2 % | 4 % | 1 % |
| **de las 444 no encontradas** | | | 58 % | 38 % | 4 % |

Posesiones nuestras que sobran: 334 de 1626 (21 %). Por causa: otro equipo 57 %; más larga que la real 9 %; más corta que la real 34 %.

Cambios directos de equipo: 1026 reales y 916 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 23 % | 41 % | 60 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +0, p25 -10, p75 +12; 418 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 4, etiquetas «control»

spellF1 0.749 · posesiones reales 1736 · nuestras 1681 · encontradas con IoU ≥ 0,5: 1300 (75 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 17 % | 60 % | 23 % | 0 % |
| 1–2 s | 111 | 26 % | 46 % | 28 % | 0 % |
| 2–5 s | 399 | 56 % | 27 % | 17 % | 1 % |
| 5–10 s | 437 | 80 % | 13 % | 7 % | 0 % |
| ≥ 10 s | 741 | 93 % | 1 % | 4 % | 2 % |
| **de las 436 no encontradas** | | | 58 % | 38 % | 4 % |

Posesiones nuestras que sobran: 381 de 1681 (23 %). Por causa: otro equipo 56 %; más larga que la real 8 %; más corta que la real 36 %.

Cambios directos de equipo: 1026 reales y 971 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 23 % | 41 % | 62 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -10, p75 +13; 419 parejas.

### B2 reentrenada en los 7 (referencia justa), α = 8, etiquetas «control»

spellF1 0.743 · posesiones reales 1736 · nuestras 1717 · encontradas con IoU ≥ 0,5: 1303 (75 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 21 % | 60 % | 19 % | 0 % |
| 1–2 s | 111 | 27 % | 48 % | 23 % | 2 % |
| 2–5 s | 399 | 57 % | 27 % | 15 % | 1 % |
| 5–10 s | 437 | 79 % | 13 % | 8 % | 0 % |
| ≥ 10 s | 741 | 93 % | 1 % | 4 % | 2 % |
| **de las 433 no encontradas** | | | 59 % | 36 % | 5 % |

Posesiones nuestras que sobran: 414 de 1717 (24 %). Por causa: otro equipo 54 %; más larga que la real 7 %; más corta que la real 39 %.

Cambios directos de equipo: 1026 reales y 1007 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 22 % | 42 % | 63 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -10, p75 +13; 427 parejas.

### B2 + dirección del balón, en los 7, α = 2, etiquetas «control»

spellF1 0.760 · posesiones reales 1736 · nuestras 1792 · encontradas con IoU ≥ 0,5: 1361 (78 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 21 % | 58 % | 21 % | 0 % |
| 1–2 s | 111 | 26 % | 49 % | 25 % | 0 % |
| 2–5 s | 399 | 67 % | 20 % | 12 % | 1 % |
| 5–10 s | 437 | 83 % | 9 % | 6 % | 2 % |
| ≥ 10 s | 741 | 93 % | 1 % | 2 % | 3 % |
| **de las 375 no encontradas** | | | 57 % | 34 % | 9 % |

Posesiones nuestras que sobran: 431 de 1792 (24 %). Por causa: otro equipo 54 %; más larga que la real 4 %; más corta que la real 42 %.

Cambios directos de equipo: 1026 reales y 1082 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 33 % | 49 % | 66 % |
| placebo: los mismos, desplazados 60 s | 2 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +0, p25 -8, p75 +9; 503 parejas.

### B2 + dirección del balón, en los 7, α = 4, etiquetas «control»

spellF1 0.742 · posesiones reales 1736 · nuestras 1912 · encontradas con IoU ≥ 0,5: 1365 (79 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 23 % | 58 % | 19 % | 0 % |
| 1–2 s | 111 | 32 % | 43 % | 23 % | 2 % |
| 2–5 s | 399 | 68 % | 19 % | 11 % | 2 % |
| 5–10 s | 437 | 83 % | 11 % | 5 % | 2 % |
| ≥ 10 s | 741 | 93 % | 1 % | 2 % | 4 % |
| **de las 371 no encontradas** | | | 56 % | 31 % | 13 % |

Posesiones nuestras que sobran: 547 de 1912 (29 %). Por causa: otro equipo 52 %; más larga que la real 3 %; más corta que la real 45 %.

Cambios directos de equipo: 1026 reales y 1202 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 33 % | 52 % | 69 % |
| placebo: los mismos, desplazados 60 s | 2 % | 3 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -7, p75 +10; 536 parejas.

### B2 + dirección del balón, en los 7, α = 8, etiquetas «control»

spellF1 0.727 · posesiones reales 1736 · nuestras 1999 · encontradas con IoU ≥ 0,5: 1370 (79 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 23 % | 58 % | 19 % | 0 % |
| 1–2 s | 111 | 34 % | 41 % | 23 % | 2 % |
| 2–5 s | 399 | 68 % | 18 % | 11 % | 3 % |
| 5–10 s | 437 | 83 % | 10 % | 4 % | 3 % |
| ≥ 10 s | 741 | 92 % | 1 % | 2 % | 4 % |
| **de las 366 no encontradas** | | | 55 % | 30 % | 16 % |

Posesiones nuestras que sobran: 629 de 1999 (31 %). Por causa: otro equipo 52 %; más larga que la real 3 %; más corta que la real 45 %.

Cambios directos de equipo: 1026 reales y 1289 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 33 % | 53 % | 71 % |
| placebo: los mismos, desplazados 60 s | 2 % | 3 % | 6 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +2, p25 -7, p75 +10; 546 parejas.
