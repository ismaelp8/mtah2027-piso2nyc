D: oraculo · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/refinamientos_k2_2026-11-17.json (huella 8114352b3e4a) · código: 8409165
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- K2: modelo conjunto en lugar de B5: {"nota": "docs/decisiones.md, 17/11, «modelo conjunto»: el logit de K2 puntuado como B5, con el pliegue que no vio el partido", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_k2"}}}
- K3: mezcla de K2 y B5: {"nota": "docs/decisiones.md, 17/11, «dos refinamientos de K2 sin reentrenar»: la media a partes iguales del logit de K2 y del de B5, cada uno en su escala y con el pliegue que no vio el partido, puntuada como B5 (possession/refinamientos.py)", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_k3"}}}

### Con qué se mide

| etiquetas | posesiones | frames `D` |
|---|---|---|
| flag | 3061 | 44,8 % |
| control | 1736 | 44,8 % |

| balón | visible en los frames de juego (media de los partidos) |
|---|---|
| como el ATD | 87,3 % |
| como el ATD, sin bloques | 98,7 % |
| limpio (sin voto) | 98,7 % |
| huecos y suavizado (sin voto) | 58,3 % |

### Etiquetas: flag

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,406 | 0,369–0,443 | – | – | 2844 / 3061 | 0,805 |
| como el ATD | main | 0,498 | 0,440–0,566 | +0,093 [+0,081 a +0,105] | 7 de 7 | 1661 / 3061 | 0,863 |
| como el ATD | K2: modelo conjunto en lugar de B5 | 0,542 | 0,473–0,617 | +0,137 [+0,123 a +0,151] | 7 de 7 | 1651 / 3061 | 0,883 |
| como el ATD | K3: mezcla de K2 y B5 | 0,529 | 0,473–0,605 | +0,123 [+0,110 a +0,137] | 7 de 7 | 1597 / 3061 | 0,878 |
| como el ATD | elegida dejando un partido fuera | 0,542 | – | +0,137 | – | 1651 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,435 | 0,405–0,479 | – | – | 2811 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,512 | 0,452–0,598 | +0,078 [+0,065 a +0,090] | 7 de 7 | 1675 / 3061 | 0,869 |
| como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | 0,549 | 0,479–0,617 | +0,114 [+0,101 a +0,128] | 7 de 7 | 1673 / 3061 | 0,886 |
| como el ATD, sin bloques | K3: mezcla de K2 y B5 | 0,536 | 0,484–0,608 | +0,101 [+0,088 a +0,115] | 7 de 7 | 1609 / 3061 | 0,881 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,549 | – | +0,114 | – | 1673 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,454 | 0,419–0,494 | – | – | 2726 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,524 | 0,470–0,600 | +0,070 [+0,057 a +0,081] | 7 de 7 | 1675 / 3061 | 0,874 |
| limpio (sin voto) | K2: modelo conjunto en lugar de B5 | 0,556 | 0,485–0,617 | +0,101 [+0,088 a +0,114] | 7 de 7 | 1694 / 3061 | 0,890 |
| limpio (sin voto) | K3: mezcla de K2 y B5 | 0,544 | 0,492–0,610 | +0,089 [+0,076 a +0,102] | 7 de 7 | 1619 / 3061 | 0,885 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,556 | – | +0,101 | – | 1694 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,393 | 0,356–0,420 | – | – | 2944 / 3061 | 0,808 |
| huecos y suavizado (sin voto) | main | 0,482 | 0,423–0,535 | +0,089 [+0,076 a +0,101] | 7 de 7 | 1674 / 3061 | 0,857 |
| huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | 0,522 | 0,456–0,598 | +0,129 [+0,115 a +0,142] | 7 de 7 | 1583 / 3061 | 0,875 |
| huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | 0,508 | 0,439–0,592 | +0,115 [+0,101 a +0,128] | 7 de 7 | 1521 / 3061 | 0,871 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,522 | – | +0,129 | – | 1583 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,464 | 0,440–0,494 | – | – | 2844 / 1736 | 0,823 |
| como el ATD | main | 0,728 | 0,661–0,787 | +0,265 [+0,249 a +0,279] | 7 de 7 | 1661 / 1736 | 0,904 |
| como el ATD | K2: modelo conjunto en lugar de B5 | 0,780 | 0,729–0,813 | +0,316 [+0,301 a +0,331] | 7 de 7 | 1651 / 1736 | 0,927 |
| como el ATD | K3: mezcla de K2 y B5 | 0,782 | 0,717–0,829 | +0,319 [+0,304 a +0,334] | 7 de 7 | 1597 / 1736 | 0,922 |
| como el ATD | elegida dejando un partido fuera | 0,779 | – | +0,315 | – | 1603 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,494 | 0,465–0,528 | – | – | 2811 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,748 | 0,691–0,802 | +0,254 [+0,240 a +0,268] | 7 de 7 | 1675 / 1736 | 0,912 |
| como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | 0,794 | 0,754–0,828 | +0,300 [+0,284 a +0,315] | 7 de 7 | 1673 / 1736 | 0,932 |
| como el ATD, sin bloques | K3: mezcla de K2 y B5 | 0,794 | 0,743–0,853 | +0,301 [+0,286 a +0,315] | 7 de 7 | 1609 / 1736 | 0,927 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,787 | – | +0,293 | – | 1627 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,524 | 0,483–0,573 | – | – | 2726 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,764 | 0,713–0,815 | +0,241 [+0,227 a +0,254] | 7 de 7 | 1675 / 1736 | 0,917 |
| limpio (sin voto) | K2: modelo conjunto en lugar de B5 | 0,798 | 0,747–0,835 | +0,275 [+0,259 a +0,288] | 7 de 7 | 1694 / 1736 | 0,935 |
| limpio (sin voto) | K3: mezcla de K2 y B5 | 0,806 | 0,746–0,855 | +0,283 [+0,268 a +0,297] | 7 de 7 | 1619 / 1736 | 0,932 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,806 | – | +0,283 | – | 1619 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,448 | 0,422–0,515 | – | – | 2944 / 1736 | 0,830 |
| huecos y suavizado (sin voto) | main | 0,705 | 0,640–0,745 | +0,257 [+0,242 a +0,272] | 7 de 7 | 1674 / 1736 | 0,900 |
| huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | 0,768 | 0,721–0,810 | +0,321 [+0,305 a +0,336] | 7 de 7 | 1583 / 1736 | 0,920 |
| huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | 0,770 | 0,718–0,808 | +0,322 [+0,306 a +0,337] | 7 de 7 | 1521 / 1736 | 0,918 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,764 | – | +0,316 | – | 1567 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- K2: modelo conjunto en lugar de B5: **gana**
- K3: mezcla de K2 y B5: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | K2: modelo conjunto en lugar de B5 | +0,044 [+0,034 a +0,054] | 7 de 7 |
| flag | como el ATD | K3: mezcla de K2 y B5 | +0,031 [+0,023 a +0,039] | 7 de 7 |
| flag | como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | +0,037 [+0,027 a +0,046] | 7 de 7 |
| flag | como el ATD, sin bloques | K3: mezcla de K2 y B5 | +0,024 [+0,017 a +0,031] | 7 de 7 |
| flag | limpio (sin voto) | K2: modelo conjunto en lugar de B5 | +0,032 [+0,022 a +0,042] | 7 de 7 |
| flag | limpio (sin voto) | K3: mezcla de K2 y B5 | +0,020 [+0,013 a +0,028] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | +0,040 [+0,031 a +0,050] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | +0,026 [+0,019 a +0,034] | 7 de 7 |
| control | como el ATD | K2: modelo conjunto en lugar de B5 | +0,051 [+0,040 a +0,064] | 7 de 7 |
| control | como el ATD | K3: mezcla de K2 y B5 | +0,054 [+0,045 a +0,063] | 7 de 7 |
| control | como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | +0,046 [+0,035 a +0,057] | 6 de 7 |
| control | como el ATD, sin bloques | K3: mezcla de K2 y B5 | +0,047 [+0,038 a +0,054] | 7 de 7 |
| control | limpio (sin voto) | K2: modelo conjunto en lugar de B5 | +0,034 [+0,022 a +0,045] | 6 de 7 |
| control | limpio (sin voto) | K3: mezcla de K2 y B5 | +0,042 [+0,033 a +0,051] | 7 de 7 |
| control | huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | +0,064 [+0,052 a +0,075] | 7 de 7 |
| control | huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | +0,065 [+0,056 a +0,074] | 7 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- K2: modelo conjunto en lugar de B5: **gana**
- K3: mezcla de K2 y B5: **empate o no concluye**

### Eventos humanos (descriptivo; regla de lectura en validation/harness/README.md)

Puntos, con los partidos medidos juntos: 3142 pase completado, 195 recuperación, 229 duelo con cambio, 211 duelo sin cambio.

| balón | versión | pase completado | recuperación | duelo con cambio | duelo sin cambio |
|---|---|---|---|---|---|
| (todas) | etiquetas «flag» como predicción | 97,9 | 89,2 | 88,6 | 47,4 |
| (todas) | etiquetas «control» como predicción | 98,8 | 87,7 | 84,3 | 74,9 |
| como el ATD | control: voto ±50 | 89,5 | 84,1 | 82,5 | 55,0 |
| como el ATD | main | 96,3 | 70,3 | 77,3 | 74,9 |
| como el ATD | K2: modelo conjunto en lugar de B5 | 98,0 | 80,0 | 82,5 | 77,7 |
| como el ATD | K3: mezcla de K2 y B5 | 97,5 | 74,9 | 79,9 | 79,6 |
| como el ATD, sin bloques | control: voto ±50 | 91,1 | 87,7 | 86,9 | 55,9 |
| como el ATD, sin bloques | main | 96,9 | 72,8 | 80,3 | 73,9 |
| como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | 98,3 | 80,5 | 83,4 | 77,3 |
| como el ATD, sin bloques | K3: mezcla de K2 y B5 | 97,9 | 76,9 | 80,8 | 81,0 |
| limpio (sin voto) | control: voto ±50 | 93,1 | 91,3 | 88,2 | 55,5 |
| limpio (sin voto) | main | 97,9 | 74,9 | 83,0 | 75,4 |
| limpio (sin voto) | K2: modelo conjunto en lugar de B5 | 98,6 | 79,5 | 83,0 | 79,1 |
| limpio (sin voto) | K3: mezcla de K2 y B5 | 98,7 | 78,5 | 82,5 | 80,1 |
| huecos y suavizado (sin voto) | control: voto ±50 | 88,9 | 84,6 | 77,7 | 59,7 |
| huecos y suavizado (sin voto) | main | 95,7 | 56,9 | 60,3 | 81,0 |
| huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | 97,5 | 69,2 | 78,6 | 82,9 |
| huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | 97,5 | 64,6 | 73,4 | 85,3 |

Diferencias en puntos, [5–95 %]:

| balón | versión | frente a | recuperación | duelo con cambio | duelo sin cambio | lectura |
|---|---|---|---|---|---|---|
| como el ATD | main | control: voto ±50 | -13,8 [-19,0 a -8,2] | -5,2 [-9,2 a -1,3] | +19,9 [+14,2 a +25,6] | compromiso |
| como el ATD | K2: modelo conjunto en lugar de B5 | control: voto ±50 | -4,1 [-9,2 a +1,0] | +0,0 [-4,4 a +4,8] | +22,7 [+16,6 a +29,4] | mejora |
| como el ATD | K2: modelo conjunto en lugar de B5 | main | +9,7 [+4,1 a +14,9] | +5,2 [+2,2 a +9,2] | +2,8 [-1,9 a +7,6] | mejora |
| como el ATD | K3: mezcla de K2 y B5 | control: voto ±50 | -9,2 [-14,9 a -4,1] | -2,6 [-6,6 a +1,7] | +24,6 [+19,0 a +30,4] | compromiso |
| como el ATD | K3: mezcla de K2 y B5 | main | +4,6 [+1,0 a +8,2] | +2,6 [+0,4 a +5,2] | +4,7 [+1,4 a +8,5] | mejora |
| como el ATD, sin bloques | main | control: voto ±50 | -14,9 [-19,5 a -9,7] | -6,6 [-10,5 a -2,6] | +18,0 [+12,3 a +23,7] | compromiso |
| como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | control: voto ±50 | -7,2 [-12,3 a -2,1] | -3,5 [-7,4 a +0,9] | +21,3 [+14,7 a +27,5] | compromiso |
| como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | main | +7,7 [+3,1 a +12,3] | +3,1 [+0,0 a +6,6] | +3,3 [-1,4 a +7,6] | mejora |
| como el ATD, sin bloques | K3: mezcla de K2 y B5 | control: voto ±50 | -10,8 [-15,9 a -5,6] | -6,1 [-10,0 a -2,2] | +25,1 [+19,0 a +30,8] | compromiso |
| como el ATD, sin bloques | K3: mezcla de K2 y B5 | main | +4,1 [+0,5 a +7,2] | +0,4 [-1,3 a +2,6] | +7,1 [+4,2 a +10,4] | mejora |
| limpio (sin voto) | main | control: voto ±50 | -16,4 [-21,5 a -11,3] | -5,2 [-8,7 a -1,7] | +19,9 [+14,7 a +25,1] | compromiso |
| limpio (sin voto) | K2: modelo conjunto en lugar de B5 | control: voto ±50 | -11,8 [-16,4 a -7,2] | -5,2 [-9,2 a -0,9] | +23,7 [+17,5 a +29,9] | compromiso |
| limpio (sin voto) | K2: modelo conjunto en lugar de B5 | main | +4,6 [+0,0 a +9,2] | +0,0 [-3,1 a +3,5] | +3,8 [-0,9 a +8,5] | no concluye |
| limpio (sin voto) | K3: mezcla de K2 y B5 | control: voto ±50 | -12,8 [-17,9 a -8,2] | -5,7 [-9,2 a -2,2] | +24,6 [+19,0 a +30,3] | compromiso |
| limpio (sin voto) | K3: mezcla de K2 y B5 | main | +3,6 [+0,0 a +7,2] | -0,4 [-2,6 a +1,7] | +4,7 [+1,4 a +9,0] | mejora |
| huecos y suavizado (sin voto) | main | control: voto ±50 | -27,7 [-33,4 a -21,5] | -17,5 [-22,7 a -11,8] | +21,3 [+15,6 a +27,0] | compromiso |
| huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | control: voto ±50 | -15,4 [-21,1 a -10,3] | +0,9 [-3,9 a +5,7] | +23,2 [+17,5 a +29,4] | compromiso |
| huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | main | +12,3 [+7,2 a +17,4] | +18,3 [+13,1 a +23,1] | +1,9 [-2,4 a +6,6] | mejora |
| huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | control: voto ±50 | -20,0 [-25,6 a -14,9] | -4,4 [-9,2 a +0,4] | +25,6 [+19,9 a +31,8] | compromiso |
| huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | main | +7,7 [+4,1 a +11,3] | +13,1 [+9,2 a +17,0] | +4,3 [+0,9 a +8,1] | mejora |

Veredicto en las condiciones que votan: «como el ATD», «como el ATD, sin bloques» (descriptivo, no entra en §5.8):

- main: frente a control: voto ±50, **compromiso**
- K2: modelo conjunto en lugar de B5: frente a control: voto ±50, **depende del balón**; frente a main, **mejora**
- K3: mezcla de K2 y B5: frente a control: voto ±50, **compromiso**; frente a main, **mejora**
