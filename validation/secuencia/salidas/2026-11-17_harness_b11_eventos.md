D: oraculo · partidos: 7 · bootstrap: 1000
versiones: C:/Users/34656/AppData/Local/Temp/claude/2995c0edd3bfb807/31a19aa9-a02c-4ec8-ba92-350f1afc6fe6/scratchpad/b11/solo_b11.json (huella bf9b12fccef1) · código: 90952d0, con cambios sin commit en possession/ o validation/harness/
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- B11: convolucional temporal: {"nota": "docs/decisiones.md, 17/11, «B11 y B12, modelos de secuencia»: canales por frame sin promediar, 7 bloques residuales dilatados (±5,1 s), puntuada como B5", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b11"}}}

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
| como el ATD | B11: convolucional temporal | 0,602 | 0,541–0,668 | +0,196 [+0,183 a +0,209] | 7 de 7 | 1989 / 3061 | 0,892 |
| como el ATD | elegida dejando un partido fuera | 0,602 | – | +0,196 | – | 1989 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,435 | 0,405–0,479 | – | – | 2811 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,512 | 0,452–0,598 | +0,078 [+0,065 a +0,090] | 7 de 7 | 1675 / 3061 | 0,869 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,620 | 0,566–0,696 | +0,186 [+0,174 a +0,198] | 7 de 7 | 2038 / 3061 | 0,898 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,620 | – | +0,186 | – | 2038 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,454 | 0,419–0,494 | – | – | 2726 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,524 | 0,470–0,600 | +0,070 [+0,057 a +0,081] | 7 de 7 | 1675 / 3061 | 0,874 |
| limpio (sin voto) | B11: convolucional temporal | 0,604 | 0,534–0,678 | +0,150 [+0,136 a +0,162] | 7 de 7 | 1972 / 3061 | 0,897 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,604 | – | +0,150 | – | 1972 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,393 | 0,356–0,420 | – | – | 2944 / 3061 | 0,808 |
| huecos y suavizado (sin voto) | main | 0,482 | 0,423–0,535 | +0,089 [+0,076 a +0,101] | 7 de 7 | 1674 / 3061 | 0,857 |
| huecos y suavizado (sin voto) | B11: convolucional temporal | 0,561 | 0,468–0,637 | +0,168 [+0,155 a +0,181] | 7 de 7 | 1868 / 3061 | 0,881 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,561 | – | +0,168 | – | 1868 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,464 | 0,440–0,494 | – | – | 2844 / 1736 | 0,823 |
| como el ATD | main | 0,728 | 0,661–0,787 | +0,265 [+0,249 a +0,279] | 7 de 7 | 1661 / 1736 | 0,904 |
| como el ATD | B11: convolucional temporal | 0,741 | 0,705–0,778 | +0,277 [+0,263 a +0,290] | 7 de 7 | 1989 / 1736 | 0,918 |
| como el ATD | elegida dejando un partido fuera | 0,741 | – | +0,277 | – | 1989 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,494 | 0,465–0,528 | – | – | 2811 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,748 | 0,691–0,802 | +0,254 [+0,240 a +0,268] | 7 de 7 | 1675 / 1736 | 0,912 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,755 | 0,705–0,797 | +0,262 [+0,248 a +0,274] | 7 de 7 | 2038 / 1736 | 0,924 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,739 | – | +0,245 | – | 1934 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,524 | 0,483–0,573 | – | – | 2726 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,764 | 0,713–0,815 | +0,241 [+0,227 a +0,254] | 7 de 7 | 1675 / 1736 | 0,917 |
| limpio (sin voto) | B11: convolucional temporal | 0,768 | 0,721–0,815 | +0,245 [+0,231 a +0,257] | 7 de 7 | 1972 / 1736 | 0,928 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,755 | – | +0,231 | – | 1861 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,448 | 0,422–0,515 | – | – | 2944 / 1736 | 0,830 |
| huecos y suavizado (sin voto) | main | 0,705 | 0,640–0,745 | +0,257 [+0,242 a +0,272] | 7 de 7 | 1674 / 1736 | 0,900 |
| huecos y suavizado (sin voto) | B11: convolucional temporal | 0,718 | 0,668–0,773 | +0,270 [+0,256 a +0,284] | 7 de 7 | 1868 / 1736 | 0,909 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,718 | – | +0,270 | – | 1868 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B11: convolucional temporal: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B11: convolucional temporal | +0,104 [+0,093 a +0,116] | 7 de 7 |
| flag | como el ATD, sin bloques | B11: convolucional temporal | +0,108 [+0,097 a +0,120] | 7 de 7 |
| flag | limpio (sin voto) | B11: convolucional temporal | +0,080 [+0,069 a +0,091] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B11: convolucional temporal | +0,080 [+0,069 a +0,091] | 7 de 7 |
| control | como el ATD | B11: convolucional temporal | +0,012 [-0,001 a +0,026] | 4 de 7 |
| control | como el ATD, sin bloques | B11: convolucional temporal | +0,007 [-0,006 a +0,020] | 4 de 7 |
| control | limpio (sin voto) | B11: convolucional temporal | +0,004 [-0,008 a +0,016] | 5 de 7 |
| control | huecos y suavizado (sin voto) | B11: convolucional temporal | +0,013 [+0,002 a +0,024] | 5 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B11: convolucional temporal: **empate o no concluye**

### Eventos humanos (descriptivo; regla de lectura en validation/harness/README.md)

Puntos, con los partidos medidos juntos: 3142 pase completado, 195 recuperación, 229 duelo con cambio, 211 duelo sin cambio.

| balón | versión | pase completado | recuperación | duelo con cambio | duelo sin cambio |
|---|---|---|---|---|---|
| (todas) | etiquetas «flag» como predicción | 97,9 | 89,2 | 88,6 | 47,4 |
| (todas) | etiquetas «control» como predicción | 98,8 | 87,7 | 84,3 | 74,9 |
| como el ATD | control: voto ±50 | 89,5 | 84,1 | 82,5 | 55,0 |
| como el ATD | main | 96,3 | 70,3 | 77,3 | 74,9 |
| como el ATD | B11: convolucional temporal | 98,2 | 82,1 | 86,9 | 64,9 |
| como el ATD, sin bloques | control: voto ±50 | 91,1 | 87,7 | 86,9 | 55,9 |
| como el ATD, sin bloques | main | 96,9 | 72,8 | 80,3 | 73,9 |
| como el ATD, sin bloques | B11: convolucional temporal | 98,6 | 84,1 | 90,0 | 64,0 |
| limpio (sin voto) | control: voto ±50 | 93,1 | 91,3 | 88,2 | 55,5 |
| limpio (sin voto) | main | 97,9 | 74,9 | 83,0 | 75,4 |
| limpio (sin voto) | B11: convolucional temporal | 98,9 | 83,1 | 90,4 | 64,0 |
| huecos y suavizado (sin voto) | control: voto ±50 | 88,9 | 84,6 | 77,7 | 59,7 |
| huecos y suavizado (sin voto) | main | 95,7 | 56,9 | 60,3 | 81,0 |
| huecos y suavizado (sin voto) | B11: convolucional temporal | 97,4 | 74,4 | 78,2 | 67,3 |

Diferencias en puntos, [5–95 %]:

| balón | versión | frente a | recuperación | duelo con cambio | duelo sin cambio | lectura |
|---|---|---|---|---|---|---|
| como el ATD | main | control: voto ±50 | -13,8 [-19,0 a -8,2] | -5,2 [-9,2 a -1,3] | +19,9 [+14,2 a +25,6] | compromiso |
| como el ATD | B11: convolucional temporal | control: voto ±50 | -2,1 [-7,2 a +3,1] | +4,4 [+0,0 a +8,7] | +10,0 [+4,3 a +16,1] | mejora |
| como el ATD | B11: convolucional temporal | main | +11,8 [+6,7 a +16,9] | +9,6 [+5,2 a +14,0] | -10,0 [-14,7 a -4,7] | compromiso |
| como el ATD, sin bloques | main | control: voto ±50 | -14,9 [-19,5 a -9,7] | -6,6 [-10,5 a -2,6] | +18,0 [+12,3 a +23,7] | compromiso |
| como el ATD, sin bloques | B11: convolucional temporal | control: voto ±50 | -3,6 [-8,2 a +1,0] | +3,1 [-0,9 a +6,6] | +8,1 [+2,4 a +13,7] | mejora |
| como el ATD, sin bloques | B11: convolucional temporal | main | +11,3 [+6,2 a +16,4] | +9,6 [+5,2 a +13,5] | -10,0 [-14,2 a -5,2] | compromiso |
| limpio (sin voto) | main | control: voto ±50 | -16,4 [-21,5 a -11,3] | -5,2 [-8,7 a -1,7] | +19,9 [+14,7 a +25,1] | compromiso |
| limpio (sin voto) | B11: convolucional temporal | control: voto ±50 | -8,2 [-12,8 a -3,6] | +2,2 [-1,3 a +5,7] | +8,5 [+3,3 a +14,2] | compromiso |
| limpio (sin voto) | B11: convolucional temporal | main | +8,2 [+3,1 a +12,8] | +7,4 [+3,5 a +11,4] | -11,4 [-15,6 a -6,2] | compromiso |
| huecos y suavizado (sin voto) | main | control: voto ±50 | -27,7 [-33,4 a -21,5] | -17,5 [-22,7 a -11,8] | +21,3 [+15,6 a +27,0] | compromiso |
| huecos y suavizado (sin voto) | B11: convolucional temporal | control: voto ±50 | -10,3 [-15,9 a -5,1] | +0,4 [-5,2 a +5,7] | +7,6 [+1,4 a +14,2] | compromiso |
| huecos y suavizado (sin voto) | B11: convolucional temporal | main | +17,4 [+12,3 a +22,6] | +17,9 [+12,6 a +23,1] | -13,7 [-19,0 a -8,1] | compromiso |

Veredicto en las condiciones que votan: «como el ATD», «como el ATD, sin bloques» (descriptivo, no entra en §5.8):

- main: frente a control: voto ±50, **compromiso**
- B11: convolucional temporal: frente a control: voto ±50, **mejora**; frente a main, **compromiso**
