D: oraculo · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/b13_trayectorias_2026-11-17.json (huella d10f5d6f7e85) · código: ad6dd9f
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- B12: GRU bidireccional: {"nota": "ronda 1 (docs/decisiones.md, 17/11): referencia para B13", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b12"}}}
- B13: trayectorias: {"nota": "docs/decisiones.md, 17/11, «B13»: codificador de conjuntos de jugadores y balón por equipo desde su dirección de ataque, GRU bidireccional a 5 Hz, entrenada también sin balón a trozos; puntuada como B5", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b13"}}}

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
| como el ATD | B12: GRU bidireccional | 0,554 | 0,498–0,621 | +0,148 [+0,135 a +0,161] | 7 de 7 | 1774 / 3061 | 0,882 |
| como el ATD | B13: trayectorias | 0,593 | 0,514–0,656 | +0,187 [+0,173 a +0,200] | 7 de 7 | 1865 / 3061 | 0,892 |
| como el ATD | elegida dejando un partido fuera | 0,593 | – | +0,187 | – | 1865 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,435 | 0,405–0,479 | – | – | 2811 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,512 | 0,452–0,598 | +0,078 [+0,065 a +0,090] | 7 de 7 | 1675 / 3061 | 0,869 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,573 | 0,515–0,635 | +0,138 [+0,126 a +0,151] | 7 de 7 | 1829 / 3061 | 0,889 |
| como el ATD, sin bloques | B13: trayectorias | 0,605 | 0,541–0,660 | +0,171 [+0,157 a +0,184] | 7 de 7 | 1898 / 3061 | 0,896 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,605 | – | +0,171 | – | 1898 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,454 | 0,419–0,494 | – | – | 2726 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,524 | 0,470–0,600 | +0,070 [+0,057 a +0,081] | 7 de 7 | 1675 / 3061 | 0,874 |
| limpio (sin voto) | B12: GRU bidireccional | 0,571 | 0,514–0,639 | +0,116 [+0,102 a +0,129] | 7 de 7 | 1774 / 3061 | 0,890 |
| limpio (sin voto) | B13: trayectorias | 0,613 | 0,556–0,667 | +0,159 [+0,145 a +0,172] | 7 de 7 | 1912 / 3061 | 0,898 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,613 | – | +0,159 | – | 1912 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,393 | 0,356–0,420 | – | – | 2944 / 3061 | 0,808 |
| huecos y suavizado (sin voto) | main | 0,482 | 0,423–0,535 | +0,089 [+0,076 a +0,101] | 7 de 7 | 1674 / 3061 | 0,857 |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | 0,527 | 0,462–0,574 | +0,134 [+0,121 a +0,148] | 7 de 7 | 1676 / 3061 | 0,874 |
| huecos y suavizado (sin voto) | B13: trayectorias | 0,560 | 0,489–0,630 | +0,167 [+0,154 a +0,181] | 7 de 7 | 1805 / 3061 | 0,883 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,560 | – | +0,167 | – | 1805 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,464 | 0,440–0,494 | – | – | 2844 / 1736 | 0,823 |
| como el ATD | main | 0,728 | 0,661–0,787 | +0,265 [+0,249 a +0,279] | 7 de 7 | 1661 / 1736 | 0,904 |
| como el ATD | B12: GRU bidireccional | 0,762 | 0,709–0,794 | +0,299 [+0,284 a +0,312] | 7 de 7 | 1774 / 1736 | 0,919 |
| como el ATD | B13: trayectorias | 0,749 | 0,678–0,796 | +0,285 [+0,270 a +0,299] | 7 de 7 | 1865 / 1736 | 0,915 |
| como el ATD | elegida dejando un partido fuera | 0,762 | – | +0,299 | – | 1774 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,494 | 0,465–0,528 | – | – | 2811 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,748 | 0,691–0,802 | +0,254 [+0,240 a +0,268] | 7 de 7 | 1675 / 1736 | 0,912 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,775 | 0,738–0,812 | +0,282 [+0,267 a +0,295] | 7 de 7 | 1829 / 1736 | 0,925 |
| como el ATD, sin bloques | B13: trayectorias | 0,750 | 0,688–0,802 | +0,257 [+0,242 a +0,270] | 7 de 7 | 1898 / 1736 | 0,916 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,775 | – | +0,282 | – | 1829 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,524 | 0,483–0,573 | – | – | 2726 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,764 | 0,713–0,815 | +0,241 [+0,227 a +0,254] | 7 de 7 | 1675 / 1736 | 0,917 |
| limpio (sin voto) | B12: GRU bidireccional | 0,793 | 0,743–0,819 | +0,270 [+0,255 a +0,283] | 7 de 7 | 1774 / 1736 | 0,929 |
| limpio (sin voto) | B13: trayectorias | 0,753 | 0,702–0,819 | +0,229 [+0,213 a +0,242] | 7 de 7 | 1912 / 1736 | 0,917 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,793 | – | +0,270 | – | 1774 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,448 | 0,422–0,515 | – | – | 2944 / 1736 | 0,830 |
| huecos y suavizado (sin voto) | main | 0,705 | 0,640–0,745 | +0,257 [+0,242 a +0,272] | 7 de 7 | 1674 / 1736 | 0,900 |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | 0,741 | 0,696–0,777 | +0,293 [+0,277 a +0,307] | 7 de 7 | 1676 / 1736 | 0,911 |
| huecos y suavizado (sin voto) | B13: trayectorias | 0,735 | 0,625–0,792 | +0,287 [+0,271 a +0,301] | 7 de 7 | 1805 / 1736 | 0,909 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,728 | – | +0,280 | – | 1722 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B12: GRU bidireccional: **gana**
- B13: trayectorias: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B12: GRU bidireccional | +0,056 [+0,046 a +0,066] | 7 de 7 |
| flag | como el ATD | B13: trayectorias | +0,094 [+0,083 a +0,106] | 7 de 7 |
| flag | como el ATD, sin bloques | B12: GRU bidireccional | +0,061 [+0,051 a +0,071] | 7 de 7 |
| flag | como el ATD, sin bloques | B13: trayectorias | +0,093 [+0,081 a +0,105] | 7 de 7 |
| flag | limpio (sin voto) | B12: GRU bidireccional | +0,047 [+0,038 a +0,056] | 7 de 7 |
| flag | limpio (sin voto) | B13: trayectorias | +0,089 [+0,076 a +0,102] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B12: GRU bidireccional | +0,046 [+0,036 a +0,057] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B13: trayectorias | +0,078 [+0,067 a +0,092] | 7 de 7 |
| control | como el ATD | B12: GRU bidireccional | +0,034 [+0,022 a +0,046] | 7 de 7 |
| control | como el ATD | B13: trayectorias | +0,021 [+0,007 a +0,034] | 6 de 7 |
| control | como el ATD, sin bloques | B12: GRU bidireccional | +0,028 [+0,016 a +0,039] | 5 de 7 |
| control | como el ATD, sin bloques | B13: trayectorias | +0,003 [-0,011 a +0,015] | 4 de 7 |
| control | limpio (sin voto) | B12: GRU bidireccional | +0,029 [+0,018 a +0,040] | 7 de 7 |
| control | limpio (sin voto) | B13: trayectorias | -0,012 [-0,025 a +0,001] | 2 de 7 |
| control | huecos y suavizado (sin voto) | B12: GRU bidireccional | +0,036 [+0,025 a +0,047] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B13: trayectorias | +0,030 [+0,017 a +0,043] | 6 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B12: GRU bidireccional: **empate o no concluye**
- B13: trayectorias: **empate o no concluye**

### Eventos humanos (descriptivo; regla de lectura en validation/harness/README.md)

Puntos, con los partidos medidos juntos: 3142 pase completado, 195 recuperación, 229 duelo con cambio, 211 duelo sin cambio.

| balón | versión | pase completado | recuperación | duelo con cambio | duelo sin cambio |
|---|---|---|---|---|---|
| (todas) | etiquetas «flag» como predicción | 97,9 | 89,2 | 88,6 | 47,4 |
| (todas) | etiquetas «control» como predicción | 98,8 | 87,7 | 84,3 | 74,9 |
| como el ATD | control: voto ±50 | 89,5 | 84,1 | 82,5 | 55,0 |
| como el ATD | main | 96,3 | 70,3 | 77,3 | 74,9 |
| como el ATD | B12: GRU bidireccional | 97,4 | 79,5 | 86,0 | 68,7 |
| como el ATD | B13: trayectorias | 98,6 | 76,9 | 84,7 | 60,7 |
| como el ATD, sin bloques | control: voto ±50 | 91,1 | 87,7 | 86,9 | 55,9 |
| como el ATD, sin bloques | main | 96,9 | 72,8 | 80,3 | 73,9 |
| como el ATD, sin bloques | B12: GRU bidireccional | 98,2 | 81,0 | 88,2 | 65,4 |
| como el ATD, sin bloques | B13: trayectorias | 98,7 | 78,5 | 86,5 | 60,7 |
| limpio (sin voto) | control: voto ±50 | 93,1 | 91,3 | 88,2 | 55,5 |
| limpio (sin voto) | main | 97,9 | 74,9 | 83,0 | 75,4 |
| limpio (sin voto) | B12: GRU bidireccional | 98,7 | 79,0 | 88,6 | 68,7 |
| limpio (sin voto) | B13: trayectorias | 98,6 | 79,5 | 86,9 | 61,6 |
| huecos y suavizado (sin voto) | control: voto ±50 | 88,9 | 84,6 | 77,7 | 59,7 |
| huecos y suavizado (sin voto) | main | 95,7 | 56,9 | 60,3 | 81,0 |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | 97,2 | 70,3 | 75,5 | 70,1 |
| huecos y suavizado (sin voto) | B13: trayectorias | 97,8 | 73,3 | 82,5 | 64,0 |

Diferencias en puntos, [5–95 %]:

| balón | versión | frente a | recuperación | duelo con cambio | duelo sin cambio | lectura |
|---|---|---|---|---|---|---|
| como el ATD | main | control: voto ±50 | -13,8 [-19,0 a -8,2] | -5,2 [-9,2 a -1,3] | +19,9 [+14,2 a +25,6] | compromiso |
| como el ATD | B12: GRU bidireccional | control: voto ±50 | -4,6 [-9,7 a +0,5] | +3,5 [-0,4 a +7,4] | +13,7 [+8,1 a +19,9] | mejora |
| como el ATD | B12: GRU bidireccional | main | +9,2 [+5,1 a +13,3] | +8,7 [+5,2 a +12,7] | -6,2 [-10,4 a -1,4] | compromiso |
| como el ATD | B13: trayectorias | control: voto ±50 | -7,2 [-13,3 a -1,0] | +2,2 [-3,1 a +7,0] | +5,7 [-1,0 a +12,8] | empeora |
| como el ATD | B13: trayectorias | main | +6,7 [+0,0 a +12,8] | +7,4 [+2,2 a +12,2] | -14,2 [-19,9 a -8,1] | compromiso |
| como el ATD, sin bloques | main | control: voto ±50 | -14,9 [-19,5 a -9,7] | -6,6 [-10,5 a -2,6] | +18,0 [+12,3 a +23,7] | compromiso |
| como el ATD, sin bloques | B12: GRU bidireccional | control: voto ±50 | -6,7 [-11,3 a -1,5] | +1,3 [-2,2 a +4,8] | +9,5 [+4,3 a +15,2] | compromiso |
| como el ATD, sin bloques | B12: GRU bidireccional | main | +8,2 [+4,1 a +12,3] | +7,9 [+4,4 a +11,4] | -8,5 [-12,3 a -4,3] | compromiso |
| como el ATD, sin bloques | B13: trayectorias | control: voto ±50 | -9,2 [-14,9 a -3,6] | -0,4 [-5,2 a +3,9] | +4,7 [-1,4 a +11,4] | empeora |
| como el ATD, sin bloques | B13: trayectorias | main | +5,6 [-0,5 a +11,8] | +6,1 [+1,3 a +10,9] | -13,3 [-19,0 a -7,1] | compromiso |
| limpio (sin voto) | main | control: voto ±50 | -16,4 [-21,5 a -11,3] | -5,2 [-8,7 a -1,7] | +19,9 [+14,7 a +25,1] | compromiso |
| limpio (sin voto) | B12: GRU bidireccional | control: voto ±50 | -12,3 [-17,4 a -7,2] | +0,4 [-3,1 a +3,5] | +13,3 [+8,1 a +19,0] | compromiso |
| limpio (sin voto) | B12: GRU bidireccional | main | +4,1 [+0,0 a +8,2] | +5,7 [+2,6 a +9,2] | -6,6 [-10,9 a -1,9] | compromiso |
| limpio (sin voto) | B13: trayectorias | control: voto ±50 | -11,8 [-17,4 a -6,2] | -1,3 [-5,7 a +3,1] | +6,2 [+0,0 a +12,8] | empeora |
| limpio (sin voto) | B13: trayectorias | main | +4,6 [-1,5 a +10,3] | +3,9 [-0,9 a +8,3] | -13,7 [-19,0 a -7,6] | empeora |
| huecos y suavizado (sin voto) | main | control: voto ±50 | -27,7 [-33,4 a -21,5] | -17,5 [-22,7 a -11,8] | +21,3 [+15,6 a +27,0] | compromiso |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | control: voto ±50 | -14,4 [-20,0 a -9,2] | -2,2 [-7,4 a +2,6] | +10,4 [+3,8 a +17,1] | compromiso |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | main | +13,3 [+8,7 a +17,9] | +15,3 [+10,0 a +20,1] | -10,9 [-15,6 a -5,7] | compromiso |
| huecos y suavizado (sin voto) | B13: trayectorias | control: voto ±50 | -11,3 [-16,9 a -5,6] | +4,8 [-0,4 a +9,6] | +4,3 [-1,9 a +10,9] | empeora |
| huecos y suavizado (sin voto) | B13: trayectorias | main | +16,4 [+10,8 a +22,1] | +22,3 [+16,2 a +27,5] | -17,1 [-22,7 a -10,9] | compromiso |

Veredicto en las condiciones que votan: «como el ATD», «como el ATD, sin bloques» (descriptivo, no entra en §5.8):

- main: frente a control: voto ±50, **compromiso**
- B12: GRU bidireccional: frente a control: voto ±50, **depende del balón**; frente a main, **compromiso**
- B13: trayectorias: frente a control: voto ±50, **empeora**; frente a main, **compromiso**
