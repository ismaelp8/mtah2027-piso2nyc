# Puerta: ¿entrenar con SkillCorner mueve las posesiones de 2 a 5 s? (en los mismos partidos)

Filas: SK 160192 (10 partidos, «detectado, suavizado»), DFL 103135. Último paso de Newton: SK 5.4e-15, DFL + SK 4.3e-15.

## Condición «detectado»

### main (B5, coeficientes de la entrega), α = 4

spellF1 0.519 · posesiones reales 3228 · nuestras 2270 · encontradas con IoU ≥ 0,5: 1450 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 83 % | 13 % | 0 % |
| 1–2 s | 427 | 21 % | 62 % | 16 % | 0 % |
| 2–5 s | 714 | 29 % | 39 % | 32 % | 0 % |
| 5–10 s | 688 | 48 % | 23 % | 28 % | 1 % |
| ≥ 10 s | 1102 | 74 % | 6 % | 17 % | 3 % |
| **de las 1778 no encontradas** | | | 57 % | 40 % | 2 % |

Posesiones nuestras que sobran: 820 de 2270 (36 %). Por causa: otro equipo 54 %; más larga que la real 16 %; más corta que la real 30 %.

Cambios directos de equipo: 2210 reales y 1252 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 16 % | 26 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -5, p25 -15, p75 +6; 360 parejas.

### SK, en los mismos partidos, α = 2

spellF1 0.526 · posesiones reales 3228 · nuestras 2113 · encontradas con IoU ≥ 0,5: 1427 (44 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 83 % | 14 % | 0 % |
| 1–2 s | 427 | 22 % | 62 % | 17 % | 0 % |
| 2–5 s | 714 | 29 % | 40 % | 31 % | 0 % |
| 5–10 s | 688 | 46 % | 23 % | 30 % | 1 % |
| ≥ 10 s | 1102 | 73 % | 6 % | 19 % | 2 % |
| **de las 1801 no encontradas** | | | 57 % | 42 % | 2 % |

Posesiones nuestras que sobran: 686 de 2113 (32 %). Por causa: otro equipo 54 %; más larga que la real 21 %; más corta que la real 25 %.

Cambios directos de equipo: 2210 reales y 1095 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 8 % | 15 % | 24 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -8, p25 -16, p75 +0; 337 parejas.

### SK, en los mismos partidos, α = 4

spellF1 0.525 · posesiones reales 3228 · nuestras 2152 · encontradas con IoU ≥ 0,5: 1431 (44 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 82 % | 15 % | 0 % |
| 1–2 s | 427 | 22 % | 62 % | 16 % | 0 % |
| 2–5 s | 714 | 29 % | 40 % | 31 % | 0 % |
| 5–10 s | 688 | 46 % | 23 % | 30 % | 1 % |
| ≥ 10 s | 1102 | 73 % | 6 % | 19 % | 2 % |
| **de las 1797 no encontradas** | | | 57 % | 42 % | 2 % |

Posesiones nuestras que sobran: 721 de 2152 (34 %). Por causa: otro equipo 54 %; más larga que la real 20 %; más corta que la real 26 %.

Cambios directos de equipo: 2210 reales y 1134 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 8 % | 16 % | 25 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -7, p25 -16, p75 +1; 344 parejas.

### SK, en los mismos partidos, α = 8

spellF1 0.520 · posesiones reales 3228 · nuestras 2224 · encontradas con IoU ≥ 0,5: 1437 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 82 % | 15 % | 0 % |
| 1–2 s | 427 | 22 % | 62 % | 16 % | 0 % |
| 2–5 s | 714 | 30 % | 39 % | 31 % | 0 % |
| 5–10 s | 688 | 47 % | 23 % | 30 % | 1 % |
| ≥ 10 s | 1102 | 72 % | 6 % | 19 % | 2 % |
| **de las 1791 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 787 de 2224 (35 %). Por causa: otro equipo 54 %; más larga que la real 18 %; más corta que la real 28 %.

Cambios directos de equipo: 2210 reales y 1206 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 16 % | 26 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -8, p25 -16, p75 +2; 354 parejas.

### DFL + SK, en los mismos partidos de SK, α = 2

spellF1 0.528 · posesiones reales 3228 · nuestras 2147 · encontradas con IoU ≥ 0,5: 1441 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 83 % | 14 % | 0 % |
| 1–2 s | 427 | 22 % | 62 % | 17 % | 0 % |
| 2–5 s | 714 | 30 % | 39 % | 31 % | 1 % |
| 5–10 s | 688 | 47 % | 24 % | 29 % | 1 % |
| ≥ 10 s | 1102 | 73 % | 6 % | 18 % | 2 % |
| **de las 1787 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 706 de 2147 (33 %). Por causa: otro equipo 54 %; más larga que la real 20 %; más corta que la real 27 %.

Cambios directos de equipo: 2210 reales y 1129 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 16 % | 25 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -8, p25 -16, p75 +2; 353 parejas.

### DFL + SK, en los mismos partidos de SK, α = 4

spellF1 0.528 · posesiones reales 3228 · nuestras 2191 · encontradas con IoU ≥ 0,5: 1451 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 84 % | 14 % | 0 % |
| 1–2 s | 427 | 22 % | 62 % | 17 % | 0 % |
| 2–5 s | 714 | 30 % | 39 % | 31 % | 0 % |
| 5–10 s | 688 | 48 % | 22 % | 29 % | 1 % |
| ≥ 10 s | 1102 | 74 % | 6 % | 18 % | 2 % |
| **de las 1777 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 740 de 2191 (34 %). Por causa: otro equipo 54 %; más larga que la real 18 %; más corta que la real 28 %.

Cambios directos de equipo: 2210 reales y 1173 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 17 % | 26 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -7, p25 -16, p75 +3; 369 parejas.

### DFL + SK, en los mismos partidos de SK, α = 8

spellF1 0.521 · posesiones reales 3228 · nuestras 2273 · encontradas con IoU ≥ 0,5: 1458 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 83 % | 14 % | 0 % |
| 1–2 s | 427 | 22 % | 62 % | 16 % | 0 % |
| 2–5 s | 714 | 30 % | 38 % | 31 % | 0 % |
| 5–10 s | 688 | 48 % | 23 % | 28 % | 1 % |
| ≥ 10 s | 1102 | 73 % | 6 % | 18 % | 2 % |
| **de las 1770 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 815 de 2273 (36 %). Por causa: otro equipo 54 %; más larga que la real 17 %; más corta que la real 29 %.

Cambios directos de equipo: 2210 reales y 1255 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 17 % | 26 % |
| placebo: los mismos, desplazados 60 s | 1 % | 3 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -7, p25 -15, p75 +4; 368 parejas.

## Condición «detectado, suavizado»

### main (B5, coeficientes de la entrega), α = 4

spellF1 0.514 · posesiones reales 3228 · nuestras 2284 · encontradas con IoU ≥ 0,5: 1443 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 83 % | 14 % | 0 % |
| 1–2 s | 427 | 21 % | 63 % | 15 % | 0 % |
| 2–5 s | 714 | 29 % | 40 % | 31 % | 0 % |
| 5–10 s | 688 | 48 % | 23 % | 28 % | 1 % |
| ≥ 10 s | 1102 | 73 % | 6 % | 17 % | 3 % |
| **de las 1785 no encontradas** | | | 57 % | 40 % | 3 % |

Posesiones nuestras que sobran: 841 de 2284 (37 %). Por causa: otro equipo 54 %; más larga que la real 15 %; más corta que la real 30 %.

Cambios directos de equipo: 2210 reales y 1266 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 16 % | 26 % |
| placebo: los mismos, desplazados 60 s | 2 % | 3 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -4, p25 -15, p75 +7; 361 parejas.

### SK, en los mismos partidos, α = 2

spellF1 0.520 · posesiones reales 3228 · nuestras 2127 · encontradas con IoU ≥ 0,5: 1407 (44 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 82 % | 15 % | 0 % |
| 1–2 s | 427 | 22 % | 62 % | 16 % | 0 % |
| 2–5 s | 714 | 28 % | 42 % | 30 % | 1 % |
| 5–10 s | 688 | 46 % | 24 % | 30 % | 1 % |
| ≥ 10 s | 1102 | 72 % | 7 % | 20 % | 2 % |
| **de las 1821 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 720 de 2127 (34 %). Por causa: otro equipo 54 %; más larga que la real 20 %; más corta que la real 26 %.

Cambios directos de equipo: 2210 reales y 1109 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 8 % | 15 % | 24 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -8, p25 -16, p75 +0; 336 parejas.

### SK, en los mismos partidos, α = 4

spellF1 0.521 · posesiones reales 3228 · nuestras 2154 · encontradas con IoU ≥ 0,5: 1419 (44 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 82 % | 15 % | 0 % |
| 1–2 s | 427 | 22 % | 63 % | 15 % | 0 % |
| 2–5 s | 714 | 29 % | 40 % | 30 % | 1 % |
| 5–10 s | 688 | 46 % | 24 % | 29 % | 1 % |
| ≥ 10 s | 1102 | 72 % | 7 % | 20 % | 2 % |
| **de las 1809 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 735 de 2154 (34 %). Por causa: otro equipo 54 %; más larga que la real 19 %; más corta que la real 27 %.

Cambios directos de equipo: 2210 reales y 1136 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 8 % | 15 % | 24 % |
| placebo: los mismos, desplazados 60 s | 1 % | 3 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -7, p25 -15, p75 +2; 338 parejas.

### SK, en los mismos partidos, α = 8

spellF1 0.516 · posesiones reales 3228 · nuestras 2221 · encontradas con IoU ≥ 0,5: 1425 (44 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 82 % | 15 % | 0 % |
| 1–2 s | 427 | 23 % | 61 % | 16 % | 0 % |
| 2–5 s | 714 | 29 % | 40 % | 30 % | 0 % |
| 5–10 s | 688 | 46 % | 23 % | 30 % | 1 % |
| ≥ 10 s | 1102 | 72 % | 7 % | 19 % | 2 % |
| **de las 1803 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 796 de 2221 (36 %). Por causa: otro equipo 54 %; más larga que la real 17 %; más corta que la real 29 %.

Cambios directos de equipo: 2210 reales y 1203 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 8 % | 16 % | 25 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -6, p25 -15, p75 +4; 352 parejas.

### DFL + SK, en los mismos partidos de SK, α = 2

spellF1 0.521 · posesiones reales 3228 · nuestras 2162 · encontradas con IoU ≥ 0,5: 1421 (44 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 82 % | 14 % | 0 % |
| 1–2 s | 427 | 22 % | 63 % | 16 % | 0 % |
| 2–5 s | 714 | 28 % | 40 % | 31 % | 1 % |
| 5–10 s | 688 | 47 % | 24 % | 29 % | 0 % |
| ≥ 10 s | 1102 | 72 % | 6 % | 19 % | 2 % |
| **de las 1807 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 741 de 2162 (34 %). Por causa: otro equipo 54 %; más larga que la real 19 %; más corta que la real 27 %.

Cambios directos de equipo: 2210 reales y 1144 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 8 % | 15 % | 25 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -7, p25 -16, p75 +2; 338 parejas.

### DFL + SK, en los mismos partidos de SK, α = 4

spellF1 0.520 · posesiones reales 3228 · nuestras 2201 · encontradas con IoU ≥ 0,5: 1429 (44 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 82 % | 15 % | 0 % |
| 1–2 s | 427 | 22 % | 62 % | 16 % | 0 % |
| 2–5 s | 714 | 28 % | 40 % | 31 % | 0 % |
| 5–10 s | 688 | 47 % | 23 % | 29 % | 1 % |
| ≥ 10 s | 1102 | 73 % | 6 % | 18 % | 3 % |
| **de las 1799 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 772 de 2201 (35 %). Por causa: otro equipo 54 %; más larga que la real 18 %; más corta que la real 28 %.

Cambios directos de equipo: 2210 reales y 1183 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 16 % | 25 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -7, p25 -15, p75 +4; 353 parejas.

### DFL + SK, en los mismos partidos de SK, α = 8

spellF1 0.517 · posesiones reales 3228 · nuestras 2278 · encontradas con IoU ≥ 0,5: 1440 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 82 % | 14 % | 0 % |
| 1–2 s | 427 | 23 % | 62 % | 15 % | 0 % |
| 2–5 s | 714 | 29 % | 39 % | 31 % | 1 % |
| 5–10 s | 688 | 47 % | 23 % | 29 % | 1 % |
| ≥ 10 s | 1102 | 73 % | 6 % | 18 % | 3 % |
| **de las 1788 no encontradas** | | | 57 % | 41 % | 2 % |

Posesiones nuestras que sobran: 838 de 2278 (37 %). Por causa: otro equipo 55 %; más larga que la real 16 %; más corta que la real 29 %.

Cambios directos de equipo: 2210 reales y 1260 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 17 % | 26 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 4 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -6, p25 -15, p75 +5; 368 parejas.
