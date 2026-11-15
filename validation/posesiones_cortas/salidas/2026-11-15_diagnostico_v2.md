# Posesiones cortas: convención o modelo, y margen de B5 (descriptivo)

Pipeline de `main` (B5, coste 25) con el `D` de las etiquetas. Duraciones a 25 fps.

## 1. ¿Convención o modelo? (DFL, «como el ATD», `D` de las etiquetas)

Posesiones por minuto vivo: flag 8,30, control 4,71, `main` 4,50,

| predicción | GT | spellF1 | posesiones predichas / reales |
|---|---|---|---|
| etiquetas «control» | flag | 0,648 | 1736 / 3061 |
| etiquetas «flag» | control | 0,648 | 3061 / 1736 |
| `main` | control | 0,728 | 1661 / 1736 |
| `main` | flag | 0,498 | 1661 / 3061 |

Las posesiones del flag, en tres: las que también son una posesión del control (IoU ≥ 0,5); las que no, y en la mayor parte de sus frames el control da el otro equipo (el toque del rival sin control); y las que no, y el control da el mismo equipo (un trozo del equipo que retiene, partido por un toque). «encontradas»: `main` las encuentra con IoU ≥ 0,5.

| duración (flag) | también en control | encontradas | toque del rival | encontradas | trozo del que retiene | encontradas |
|---|---|---|---|---|---|---|
| < 1 s | 49 | 14 % | 248 | 0 % | 87 | 0 % |
| 1–2 s | 123 | 29 % | 245 | 3 % | 167 | 7 % |
| 2–5 s | 410 | 50 % | 269 | 9 % | 255 | 10 % |
| 5–10 s | 409 | 76 % | 29 | 28 % | 131 | 11 % |
| ≥ 10 s | 578 | 93 % | 2 | 50 % | 59 | 20 % |
| **todas** | 1569 | 70 % | 793 | 5 % | 699 | 9 % |

## 2. Margen de B5 dentro de cada posesión real

DFL: posesiones si se sigue el signo de `m` frame a frame: 2531; con el Viterbi de `main`: 1661.

### DFL, «como el ATD», etiquetas «flag»

Una fila por duración real y si `main` la encuentra (IoU ≥ 0,5). `S/coste`: la suma de `m` en la posesión dividida por lo que cuesta meterla (25 por lado pegado al otro equipo); solo las que tienen algún lado así. «paga»: `S` > coste. «el mejor trozo paga»: hay un trozo seguido con suma > coste.

| duración | ¿la encuentra? | posesiones | con 2 lados rivales | S/coste, mediana | paga | el mejor trozo paga | m por frame, media | N1 bien / mal por frame | z a favor por frame | balón visible |
|---|---|---|---|---|---|---|---|---|---|---|
| < 1 s | sí | 8 | 0 % | +4,55 | 100 % | 100 % | +11,19 | 32 % / 24 % | 100 % | 56 % |
| < 1 s | no | 376 | 56 % | -1,54 | 15 % | 15 % | -4,83 | 41 % / 32 % | 23 % | 74 % |
| 1–2 s | sí | 54 | 15 % | +5,78 | 93 % | 100 % | +6,04 | 39 % / 47 % | 91 % | 86 % |
| 1–2 s | no | 481 | 63 % | -2,66 | 33 % | 36 % | -2,26 | 42 % / 42 % | 38 % | 84 % |
| 2–5 s | sí | 256 | 34 % | +16,46 | 94 % | 100 % | +8,00 | 59 % / 29 % | 90 % | 88 % |
| 2–5 s | no | 678 | 72 % | -2,07 | 42 % | 51 % | +0,02 | 44 % / 39 % | 46 % | 83 % |
| 5–10 s | sí | 331 | 39 % | +53,07 | 97 % | 100 % | +11,41 | 63 % / 26 % | 91 % | 89 % |
| 5–10 s | no | 238 | 76 % | +29,22 | 71 % | 82 % | +9,16 | 56 % / 32 % | 73 % | 87 % |
| ≥ 10 s | sí | 549 | 50 % | +226,21 | 100 % | 100 % | +20,01 | 74 % / 14 % | 97 % | 88 % |
| ≥ 10 s | no | 90 | 67 % | +130,82 | 94 % | 100 % | +16,15 | 69 % / 17 % | 93 % | 85 % |

De dónde sale `m` (media por frame, a favor del equipo bueno), por grupo de B5:

| duración | ¿la encuentra? | N1 | balón v1 | balón v13 | balón v51 | balón v151 | posición en el campo | velocidad de los equipos | dispersión | total |
|---|---|---|---|---|---|---|---|---|---|---|
| < 1 s | sí | +0,08 | +0,14 | +1,32 | +0,43 | -0,18 | +1,74 | +1,61 | +6,05 | +11,19 |
| < 1 s | no | +0,09 | +0,06 | +0,21 | -0,38 | -1,60 | +0,52 | -2,00 | -1,73 | -4,83 |
| 1–2 s | sí | -0,08 | -0,21 | -0,22 | +1,20 | -1,89 | -1,96 | +3,21 | +5,98 | +6,04 |
| 1–2 s | no | -0,00 | +0,02 | +0,16 | -0,24 | -1,13 | +0,39 | -1,06 | -0,40 | -2,26 |
| 2–5 s | sí | +0,30 | -0,07 | +0,20 | +0,82 | +1,62 | +0,00 | +2,71 | +2,43 | +8,00 |
| 2–5 s | no | +0,04 | -0,02 | +0,15 | +0,29 | -0,20 | +0,58 | +0,68 | -1,53 | +0,02 |
| 5–10 s | sí | +0,37 | -0,09 | +0,22 | +1,17 | +3,87 | +0,38 | +4,08 | +1,41 | +11,41 |
| 5–10 s | no | +0,24 | -0,08 | +0,19 | +1,23 | +3,16 | -0,67 | +3,10 | +1,99 | +9,16 |
| ≥ 10 s | sí | +0,61 | -0,18 | +0,37 | +0,92 | +8,74 | +2,74 | +2,42 | +4,39 | +20,01 |
| ≥ 10 s | no | +0,52 | -0,15 | +0,27 | +0,94 | +6,89 | +0,68 | +1,57 | +5,44 | +16,15 |

De las 1863 no encontradas: otro equipo 55 %; la nuestra es más larga 44 %; la nuestra es más corta o va partida 1 %.
- «otro equipo»: 1024 con algún lado rival; paga el 1 %, el mejor trozo paga el 8 %; S/coste mediana -6,61,
- «la nuestra es más larga»: 811 con algún lado rival; paga el 90 %, el mejor trozo paga el 93 %; S/coste mediana +15,80,

### DFL, «como el ATD», etiquetas «control»

Una fila por duración real y si `main` la encuentra (IoU ≥ 0,5). `S/coste`: la suma de `m` en la posesión dividida por lo que cuesta meterla (25 por lado pegado al otro equipo); solo las que tienen algún lado así. «paga»: `S` > coste. «el mejor trozo paga»: hay un trozo seguido con suma > coste.

| duración | ¿la encuentra? | posesiones | con 2 lados rivales | S/coste, mediana | paga | el mejor trozo paga | m por frame, media | N1 bien / mal por frame | z a favor por frame | balón visible |
|---|---|---|---|---|---|---|---|---|---|---|
| < 1 s | sí | 7 | 0 % | +7,43 | 100 % | 100 % | +13,27 | 22 % / 30 % | 100 % | 52 % |
| < 1 s | no | 41 | 24 % | -1,70 | 24 % | 24 % | -2,38 | 54 % / 9 % | 30 % | 63 % |
| 1–2 s | sí | 28 | 11 % | +5,79 | 84 % | 100 % | +6,89 | 44 % / 40 % | 88 % | 83 % |
| 1–2 s | no | 83 | 40 % | -2,49 | 34 % | 41 % | -0,82 | 48 % / 33 % | 39 % | 81 % |
| 2–5 s | sí | 212 | 21 % | +17,57 | 94 % | 100 % | +8,07 | 55 % / 31 % | 90 % | 86 % |
| 2–5 s | no | 187 | 57 % | -2,53 | 41 % | 55 % | +0,23 | 45 % / 37 % | 43 % | 82 % |
| 5–10 s | sí | 332 | 29 % | +48,51 | 96 % | 100 % | +10,25 | 60 % / 27 % | 90 % | 87 % |
| 5–10 s | no | 105 | 50 % | -6,47 | 42 % | 76 % | +2,73 | 44 % / 40 % | 51 % | 84 % |
| ≥ 10 s | sí | 680 | 31 % | +240,58 | 100 % | 100 % | +18,25 | 72 % / 17 % | 96 % | 88 % |
| ≥ 10 s | no | 61 | 41 % | +83,17 | 79 % | 97 % | +10,76 | 56 % / 24 % | 76 % | 80 % |

De dónde sale `m` (media por frame, a favor del equipo bueno), por grupo de B5:

| duración | ¿la encuentra? | N1 | balón v1 | balón v13 | balón v51 | balón v151 | posición en el campo | velocidad de los equipos | dispersión | total |
|---|---|---|---|---|---|---|---|---|---|---|
| < 1 s | sí | -0,08 | +0,16 | +0,78 | +0,27 | -0,39 | +1,90 | +3,74 | +6,89 | +13,27 |
| < 1 s | no | +0,45 | +0,05 | +0,96 | +0,42 | -0,82 | -0,08 | -2,18 | -1,17 | -2,38 |
| 1–2 s | sí | +0,04 | -0,19 | -0,14 | +1,31 | -2,39 | -1,50 | +4,08 | +5,67 | +6,89 |
| 1–2 s | no | +0,16 | +0,02 | +0,31 | +0,05 | -0,67 | +0,69 | -0,42 | -0,96 | -0,82 |
| 2–5 s | sí | +0,24 | -0,10 | +0,14 | +1,03 | +1,28 | -0,79 | +2,66 | +3,62 | +8,07 |
| 2–5 s | no | +0,08 | -0,03 | +0,17 | +0,31 | -0,16 | +0,73 | +1,04 | -1,90 | +0,23 |
| 5–10 s | sí | +0,33 | -0,08 | +0,19 | +1,11 | +3,23 | +0,17 | +3,64 | +1,67 | +10,25 |
| 5–10 s | no | +0,04 | -0,03 | +0,13 | +0,68 | +0,53 | -0,46 | +1,42 | +0,43 | +2,73 |
| ≥ 10 s | sí | +0,55 | -0,17 | +0,32 | +0,96 | +7,81 | +1,86 | +2,41 | +4,51 | +18,25 |
| ≥ 10 s | no | +0,32 | -0,11 | +0,22 | +0,69 | +4,52 | +0,01 | +1,24 | +3,86 | +10,76 |

De las 477 no encontradas: otro equipo 58 %; la nuestra es más larga 38 %; la nuestra es más corta o va partida 4 %.
- «otro equipo»: 260 con algún lado rival; paga el 3 %, el mejor trozo paga el 29 %; S/coste mediana -8,40,
- «la nuestra es más larga»: 181 con algún lado rival; paga el 96 %, el mejor trozo paga el 99 %; S/coste mediana +20,32,

SkillCorner (`lector,ENTRENAMIENTO`, «detectado»): posesiones por minuto vivo, reales 6,05 y `main` 4,25 (3228 y 2270); si se sigue el signo de `m`: 3646,

### SkillCorner, `lector.ENTRENAMIENTO` (10 partidos), «detectado»

Una fila por duración real y si `main` la encuentra (IoU ≥ 0,5). `S/coste`: la suma de `m` en la posesión dividida por lo que cuesta meterla (25 por lado pegado al otro equipo); solo las que tienen algún lado así. «paga»: `S` > coste. «el mejor trozo paga»: hay un trozo seguido con suma > coste.

| duración | ¿la encuentra? | posesiones | con 2 lados rivales | S/coste, mediana | paga | el mejor trozo paga | m por frame, media | N1 bien / mal por frame | z a favor por frame | balón visible |
|---|---|---|---|---|---|---|---|---|---|---|
| < 1 s | sí | 10 | 0 % | +5,08 | 100 % | 100 % | +6,94 | 49 % / 18 % | 94 % | 67 % |
| < 1 s | no | 287 | 55 % | -4,25 | 13 % | 14 % | -9,81 | 53 % / 32 % | 15 % | 85 % |
| 1–2 s | sí | 91 | 2 % | +8,01 | 92 % | 100 % | +12,15 | 53 % / 27 % | 96 % | 80 % |
| 1–2 s | no | 336 | 56 % | -9,62 | 20 % | 22 % | -7,21 | 44 % / 44 % | 21 % | 88 % |
| 2–5 s | sí | 205 | 23 % | +22,07 | 96 % | 100 % | +8,95 | 62 % / 32 % | 91 % | 93 % |
| 2–5 s | no | 509 | 62 % | -3,10 | 45 % | 52 % | +0,11 | 51 % / 44 % | 47 % | 95 % |
| 5–10 s | sí | 332 | 37 % | +59,10 | 96 % | 100 % | +11,64 | 69 % / 25 % | 90 % | 94 % |
| 5–10 s | no | 356 | 59 % | +29,35 | 59 % | 75 % | +5,18 | 56 % / 38 % | 60 % | 94 % |
| ≥ 10 s | sí | 812 | 40 % | +225,14 | 99 % | 100 % | +15,99 | 75 % / 18 % | 94 % | 93 % |
| ≥ 10 s | no | 290 | 56 % | +125,43 | 80 % | 91 % | +11,04 | 66 % / 25 % | 77 % | 91 % |

De dónde sale `m` (media por frame, a favor del equipo bueno), por grupo de B5:

| duración | ¿la encuentra? | N1 | balón v1 | balón v13 | balón v51 | balón v151 | posición en el campo | velocidad de los equipos | dispersión | total |
|---|---|---|---|---|---|---|---|---|---|---|
| < 1 s | sí | +0,30 | -0,04 | +0,38 | +0,94 | +1,49 | -0,68 | -0,40 | +4,95 | +6,94 |
| < 1 s | no | +0,21 | +0,10 | +0,08 | -0,96 | -4,46 | +0,17 | -1,43 | -3,50 | -9,81 |
| 1–2 s | sí | +0,25 | -0,06 | -0,04 | +0,23 | +4,19 | -0,57 | +1,15 | +6,99 | +12,15 |
| 1–2 s | no | -0,01 | +0,05 | +0,06 | -0,29 | -3,06 | +0,19 | -1,26 | -2,89 | -7,21 |
| 2–5 s | sí | +0,30 | -0,13 | +0,09 | +1,22 | +2,60 | -0,77 | +2,79 | +2,85 | +8,95 |
| 2–5 s | no | +0,07 | -0,03 | +0,10 | +0,40 | -0,28 | -0,09 | +0,57 | -0,63 | +0,11 |
| 5–10 s | sí | +0,43 | -0,13 | +0,23 | +1,27 | +4,78 | +0,69 | +2,34 | +2,03 | +11,64 |
| 5–10 s | no | +0,18 | -0,06 | +0,09 | +0,66 | +2,11 | +0,55 | +0,69 | +0,96 | +5,18 |
| ≥ 10 s | sí | +0,58 | -0,18 | +0,25 | +1,11 | +7,22 | +1,31 | +1,33 | +4,37 | +15,99 |
| ≥ 10 s | no | +0,42 | -0,12 | +0,18 | +0,79 | +5,18 | +0,62 | +0,40 | +3,57 | +11,04 |

De las 1778 no encontradas: otro equipo 57 %; la nuestra es más larga 40 %; la nuestra es más corta o va partida 2 %.
- «otro equipo»: 974 con algún lado rival; paga el 2 %, el mejor trozo paga el 14 %; S/coste mediana -11,18,
- «la nuestra es más larga»: 715 con algún lado rival; paga el 99 %, el mejor trozo paga el 99 %; S/coste mediana +48,22,
