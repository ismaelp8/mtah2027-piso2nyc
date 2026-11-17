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
