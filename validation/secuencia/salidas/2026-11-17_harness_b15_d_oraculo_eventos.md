D: oraculo · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/b15_control_2026-11-17.json (huella a9120537a4a5) · código: f3f7e9b
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- B14: trayectorias con dominio aleatorizado: {"nota": "docs/decisiones.md, 17/11, «B14»: referencia para B15", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b14"}}}
- B15: B14 con la etiqueta de control: {"nota": "docs/decisiones.md, 17/11, «B15»: la red de B14 entrenada con la etiqueta de control en todos los frames vivos; puntuada como B5", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b15"}}}

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
| como el ATD | B14: trayectorias con dominio aleatorizado | 0,618 | 0,540–0,678 | +0,212 [+0,198 a +0,227] | 7 de 7 | 1904 / 3061 | 0,901 |
| como el ATD | B15: B14 con la etiqueta de control | 0,546 | 0,454–0,626 | +0,140 [+0,127 a +0,154] | 7 de 7 | 1655 / 3061 | 0,885 |
| como el ATD | elegida dejando un partido fuera | 0,618 | – | +0,212 | – | 1904 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,435 | 0,405–0,479 | – | – | 2811 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,512 | 0,452–0,598 | +0,078 [+0,065 a +0,090] | 7 de 7 | 1675 / 3061 | 0,869 |
| como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | 0,630 | 0,569–0,689 | +0,195 [+0,181 a +0,209] | 7 de 7 | 1934 / 3061 | 0,905 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 0,549 | 0,460–0,614 | +0,115 [+0,101 a +0,128] | 7 de 7 | 1662 / 3061 | 0,887 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,630 | – | +0,195 | – | 1934 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,454 | 0,419–0,494 | – | – | 2726 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,524 | 0,470–0,600 | +0,070 [+0,057 a +0,081] | 7 de 7 | 1675 / 3061 | 0,874 |
| limpio (sin voto) | B14: trayectorias con dominio aleatorizado | 0,625 | 0,563–0,681 | +0,171 [+0,156 a +0,184] | 7 de 7 | 1903 / 3061 | 0,905 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 0,551 | 0,488–0,621 | +0,097 [+0,083 a +0,111] | 7 de 7 | 1669 / 3061 | 0,889 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,625 | – | +0,171 | – | 1903 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,393 | 0,356–0,420 | – | – | 2944 / 3061 | 0,808 |
| huecos y suavizado (sin voto) | main | 0,482 | 0,423–0,535 | +0,089 [+0,076 a +0,101] | 7 de 7 | 1674 / 3061 | 0,857 |
| huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | 0,580 | 0,511–0,657 | +0,187 [+0,174 a +0,200] | 7 de 7 | 1784 / 3061 | 0,889 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 0,522 | 0,442–0,611 | +0,129 [+0,115 a +0,143] | 7 de 7 | 1623 / 3061 | 0,878 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,580 | – | +0,187 | – | 1784 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,464 | 0,440–0,494 | – | – | 2844 / 1736 | 0,823 |
| como el ATD | main | 0,728 | 0,661–0,787 | +0,265 [+0,249 a +0,279] | 7 de 7 | 1661 / 1736 | 0,904 |
| como el ATD | B14: trayectorias con dominio aleatorizado | 0,776 | 0,741–0,828 | +0,313 [+0,298 a +0,325] | 7 de 7 | 1904 / 1736 | 0,927 |
| como el ATD | B15: B14 con la etiqueta de control | 0,782 | 0,698–0,830 | +0,318 [+0,302 a +0,333] | 7 de 7 | 1655 / 1736 | 0,926 |
| como el ATD | elegida dejando un partido fuera | 0,776 | – | +0,312 | – | 1705 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,494 | 0,465–0,528 | – | – | 2811 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,748 | 0,691–0,802 | +0,254 [+0,240 a +0,268] | 7 de 7 | 1675 / 1736 | 0,912 |
| como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | 0,775 | 0,742–0,811 | +0,282 [+0,268 a +0,294] | 7 de 7 | 1934 / 1736 | 0,929 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 0,789 | 0,710–0,843 | +0,296 [+0,279 a +0,310] | 7 de 7 | 1662 / 1736 | 0,929 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,789 | – | +0,296 | – | 1662 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,524 | 0,483–0,573 | – | – | 2726 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,764 | 0,713–0,815 | +0,241 [+0,227 a +0,254] | 7 de 7 | 1675 / 1736 | 0,917 |
| limpio (sin voto) | B14: trayectorias con dominio aleatorizado | 0,784 | 0,743–0,817 | +0,261 [+0,247 a +0,274] | 7 de 7 | 1903 / 1736 | 0,933 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 0,804 | 0,742–0,842 | +0,281 [+0,265 a +0,294] | 7 de 7 | 1669 / 1736 | 0,933 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,804 | – | +0,281 | – | 1669 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,448 | 0,422–0,515 | – | – | 2944 / 1736 | 0,830 |
| huecos y suavizado (sin voto) | main | 0,705 | 0,640–0,745 | +0,257 [+0,242 a +0,272] | 7 de 7 | 1674 / 1736 | 0,900 |
| huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | 0,763 | 0,702–0,803 | +0,315 [+0,301 a +0,330] | 7 de 7 | 1784 / 1736 | 0,920 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 0,767 | 0,672–0,828 | +0,319 [+0,302 a +0,335] | 7 de 7 | 1623 / 1736 | 0,920 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,762 | – | +0,314 | – | 1655 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B14: trayectorias con dominio aleatorizado: **gana**
- B15: B14 con la etiqueta de control: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B14: trayectorias con dominio aleatorizado | +0,120 [+0,108 a +0,132] | 7 de 7 |
| flag | como el ATD | B15: B14 con la etiqueta de control | +0,048 [+0,038 a +0,058] | 6 de 7 |
| flag | como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | +0,118 [+0,105 a +0,130] | 7 de 7 |
| flag | como el ATD, sin bloques | B15: B14 con la etiqueta de control | +0,037 [+0,027 a +0,047] | 6 de 7 |
| flag | limpio (sin voto) | B14: trayectorias con dominio aleatorizado | +0,101 [+0,090 a +0,113] | 7 de 7 |
| flag | limpio (sin voto) | B15: B14 con la etiqueta de control | +0,027 [+0,018 a +0,038] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | +0,098 [+0,087 a +0,110] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | +0,041 [+0,031 a +0,051] | 7 de 7 |
| control | como el ATD | B14: trayectorias con dominio aleatorizado | +0,048 [+0,034 a +0,061] | 7 de 7 |
| control | como el ATD | B15: B14 con la etiqueta de control | +0,054 [+0,041 a +0,066] | 7 de 7 |
| control | como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | +0,027 [+0,014 a +0,040] | 7 de 7 |
| control | como el ATD, sin bloques | B15: B14 con la etiqueta de control | +0,042 [+0,030 a +0,053] | 7 de 7 |
| control | limpio (sin voto) | B14: trayectorias con dominio aleatorizado | +0,020 [+0,007 a +0,032] | 5 de 7 |
| control | limpio (sin voto) | B15: B14 con la etiqueta de control | +0,040 [+0,028 a +0,051] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | +0,058 [+0,045 a +0,071] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | +0,062 [+0,050 a +0,073] | 7 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B14: trayectorias con dominio aleatorizado: **empate o no concluye**
- B15: B14 con la etiqueta de control: **gana**

### Eventos humanos (descriptivo; regla de lectura en validation/harness/README.md)

Puntos, con los partidos medidos juntos: 3142 pase completado, 195 recuperación, 229 duelo con cambio, 211 duelo sin cambio.

| balón | versión | pase completado | recuperación | duelo con cambio | duelo sin cambio |
|---|---|---|---|---|---|
| (todas) | etiquetas «flag» como predicción | 97,9 | 89,2 | 88,6 | 47,4 |
| (todas) | etiquetas «control» como predicción | 98,8 | 87,7 | 84,3 | 74,9 |
| como el ATD | control: voto ±50 | 89,5 | 84,1 | 82,5 | 55,0 |
| como el ATD | main | 96,3 | 70,3 | 77,3 | 74,9 |
| como el ATD | B14: trayectorias con dominio aleatorizado | 98,9 | 86,2 | 90,0 | 68,2 |
| como el ATD | B15: B14 con la etiqueta de control | 98,3 | 77,4 | 79,5 | 72,5 |
| como el ATD, sin bloques | control: voto ±50 | 91,1 | 87,7 | 86,9 | 55,9 |
| como el ATD, sin bloques | main | 96,9 | 72,8 | 80,3 | 73,9 |
| como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | 98,9 | 87,7 | 90,4 | 66,4 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 98,4 | 79,0 | 81,2 | 72,5 |
| limpio (sin voto) | control: voto ±50 | 93,1 | 91,3 | 88,2 | 55,5 |
| limpio (sin voto) | main | 97,9 | 74,9 | 83,0 | 75,4 |
| limpio (sin voto) | B14: trayectorias con dominio aleatorizado | 99,2 | 85,1 | 90,4 | 67,8 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 98,6 | 80,5 | 80,8 | 73,5 |
| huecos y suavizado (sin voto) | control: voto ±50 | 88,9 | 84,6 | 77,7 | 59,7 |
| huecos y suavizado (sin voto) | main | 95,7 | 56,9 | 60,3 | 81,0 |
| huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | 98,4 | 75,4 | 84,7 | 68,2 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 97,5 | 70,8 | 77,7 | 76,8 |

Diferencias en puntos, [5–95 %]:

| balón | versión | frente a | recuperación | duelo con cambio | duelo sin cambio | lectura |
|---|---|---|---|---|---|---|
| como el ATD | main | control: voto ±50 | -13,8 [-19,0 a -8,2] | -5,2 [-9,2 a -1,3] | +19,9 [+14,2 a +25,6] | compromiso |
| como el ATD | B14: trayectorias con dominio aleatorizado | control: voto ±50 | +2,1 [-3,1 a +6,7] | +7,4 [+3,1 a +11,8] | +13,3 [+7,1 a +19,9] | mejora |
| como el ATD | B14: trayectorias con dominio aleatorizado | main | +15,9 [+9,7 a +21,0] | +12,7 [+8,7 a +17,0] | -6,6 [-11,8 a -0,9] | compromiso |
| como el ATD | B15: B14 con la etiqueta de control | control: voto ±50 | -6,7 [-11,8 a -1,0] | -3,1 [-7,4 a +0,9] | +17,5 [+11,8 a +24,2] | compromiso |
| como el ATD | B15: B14 con la etiqueta de control | main | +7,2 [+1,5 a +12,8] | +2,2 [-1,7 a +6,1] | -2,4 [-7,6 a +2,8] | mejora |
| como el ATD, sin bloques | main | control: voto ±50 | -14,9 [-19,5 a -9,7] | -6,6 [-10,5 a -2,6] | +18,0 [+12,3 a +23,7] | compromiso |
| como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | control: voto ±50 | +0,0 [-4,6 a +4,6] | +3,5 [-0,4 a +7,4] | +10,4 [+4,3 a +16,6] | mejora |
| como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | main | +14,9 [+9,2 a +20,0] | +10,0 [+6,1 a +14,4] | -7,6 [-12,3 a -2,4] | compromiso |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | control: voto ±50 | -8,7 [-13,8 a -3,1] | -5,7 [-9,6 a -2,2] | +16,6 [+10,9 a +22,7] | compromiso |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | main | +6,2 [+0,5 a +11,8] | +0,9 [-2,6 a +4,4] | -1,4 [-5,7 a +3,8] | mejora |
| limpio (sin voto) | main | control: voto ±50 | -16,4 [-21,5 a -11,3] | -5,2 [-8,7 a -1,7] | +19,9 [+14,7 a +25,1] | compromiso |
| limpio (sin voto) | B14: trayectorias con dominio aleatorizado | control: voto ±50 | -6,2 [-10,3 a -2,1] | +2,2 [-1,7 a +6,1] | +12,3 [+6,6 a +18,0] | compromiso |
| limpio (sin voto) | B14: trayectorias con dominio aleatorizado | main | +10,3 [+5,1 a +15,4] | +7,4 [+3,5 a +11,8] | -7,6 [-12,3 a -2,4] | compromiso |
| limpio (sin voto) | B15: B14 con la etiqueta de control | control: voto ±50 | -10,8 [-15,4 a -5,6] | -7,4 [-11,8 a -3,5] | +18,0 [+12,3 a +24,2] | compromiso |
| limpio (sin voto) | B15: B14 con la etiqueta de control | main | +5,6 [+0,0 a +10,8] | -2,2 [-6,6 a +1,7] | -1,9 [-6,6 a +3,3] | no concluye |
| huecos y suavizado (sin voto) | main | control: voto ±50 | -27,7 [-33,4 a -21,5] | -17,5 [-22,7 a -11,8] | +21,3 [+15,6 a +27,0] | compromiso |
| huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | control: voto ±50 | -9,2 [-14,9 a -4,1] | +7,0 [+1,7 a +11,8] | +8,5 [+2,8 a +14,7] | compromiso |
| huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | main | +18,5 [+12,8 a +24,1] | +24,5 [+18,8 a +30,1] | -12,8 [-18,0 a -7,1] | compromiso |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | control: voto ±50 | -13,8 [-19,5 a -8,7] | +0,0 [-4,8 a +4,4] | +17,1 [+11,4 a +23,2] | compromiso |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | main | +13,8 [+8,2 a +19,0] | +17,5 [+12,7 a +22,7] | -4,3 [-8,5 a +0,5] | mejora |

Veredicto en las condiciones que votan: «como el ATD», «como el ATD, sin bloques» (descriptivo, no entra en §5.8):

- main: frente a control: voto ±50, **compromiso**
- B14: trayectorias con dominio aleatorizado: frente a control: voto ±50, **mejora**; frente a main, **compromiso**
- B15: B14 con la etiqueta de control: frente a control: voto ±50, **compromiso**; frente a main, **mejora**
