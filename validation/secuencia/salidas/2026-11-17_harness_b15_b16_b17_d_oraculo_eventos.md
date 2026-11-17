D: oraculo · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/b17_media_2026-11-17.json (huella a5b8402c52be) · código: a88d550
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- B15: B14 con la etiqueta de control: {"nota": "docs/decisiones.md, 17/11, «B15»: referencia", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b15"}}}
- B16: B15 con SkillCorner: {"nota": "docs/decisiones.md, 17/11, «B16»: B15 entrenada también con SkillCorner ENTRENAMIENTO", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b16"}}}
- B17: media de B15 y B16: {"nota": "docs/decisiones.md, 17/11, «B17»: la media de los logits de B15 y B16, sin reentrenar; α, la media geométrica de las dos", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b17"}}}

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
| como el ATD | B15: B14 con la etiqueta de control | 0,546 | 0,454–0,626 | +0,140 [+0,127 a +0,154] | 7 de 7 | 1655 / 3061 | 0,885 |
| como el ATD | B16: B15 con SkillCorner | 0,545 | 0,454–0,619 | +0,139 [+0,125 a +0,152] | 7 de 7 | 1686 / 3061 | 0,882 |
| como el ATD | B17: media de B15 y B16 | 0,547 | 0,460–0,631 | +0,141 [+0,127 a +0,155] | 7 de 7 | 1654 / 3061 | 0,884 |
| como el ATD | elegida dejando un partido fuera | 0,545 | – | +0,139 | – | 1648 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,435 | 0,405–0,479 | – | – | 2811 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,512 | 0,452–0,598 | +0,078 [+0,065 a +0,090] | 7 de 7 | 1675 / 3061 | 0,869 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 0,549 | 0,460–0,614 | +0,115 [+0,101 a +0,128] | 7 de 7 | 1662 / 3061 | 0,887 |
| como el ATD, sin bloques | B16: B15 con SkillCorner | 0,553 | 0,477–0,615 | +0,118 [+0,105 a +0,132] | 7 de 7 | 1705 / 3061 | 0,886 |
| como el ATD, sin bloques | B17: media de B15 y B16 | 0,551 | 0,488–0,621 | +0,117 [+0,103 a +0,131] | 7 de 7 | 1669 / 3061 | 0,887 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,549 | – | +0,114 | – | 1670 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,454 | 0,419–0,494 | – | – | 2726 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,524 | 0,470–0,600 | +0,070 [+0,057 a +0,081] | 7 de 7 | 1675 / 3061 | 0,874 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 0,551 | 0,488–0,621 | +0,097 [+0,083 a +0,111] | 7 de 7 | 1669 / 3061 | 0,889 |
| limpio (sin voto) | B16: B15 con SkillCorner | 0,555 | 0,499–0,612 | +0,101 [+0,087 a +0,114] | 7 de 7 | 1680 / 3061 | 0,888 |
| limpio (sin voto) | B17: media de B15 y B16 | 0,556 | 0,500–0,618 | +0,102 [+0,088 a +0,115] | 7 de 7 | 1657 / 3061 | 0,890 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,554 | – | +0,100 | – | 1653 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,393 | 0,356–0,420 | – | – | 2944 / 3061 | 0,808 |
| huecos y suavizado (sin voto) | main | 0,482 | 0,423–0,535 | +0,089 [+0,076 a +0,101] | 7 de 7 | 1674 / 3061 | 0,857 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 0,522 | 0,442–0,611 | +0,129 [+0,115 a +0,143] | 7 de 7 | 1623 / 3061 | 0,878 |
| huecos y suavizado (sin voto) | B16: B15 con SkillCorner | 0,517 | 0,441–0,625 | +0,124 [+0,109 a +0,137] | 7 de 7 | 1580 / 3061 | 0,876 |
| huecos y suavizado (sin voto) | B17: media de B15 y B16 | 0,524 | 0,453–0,621 | +0,131 [+0,116 a +0,144] | 7 de 7 | 1608 / 3061 | 0,878 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,522 | – | +0,129 | – | 1613 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,464 | 0,440–0,494 | – | – | 2844 / 1736 | 0,823 |
| como el ATD | main | 0,728 | 0,661–0,787 | +0,265 [+0,249 a +0,279] | 7 de 7 | 1661 / 1736 | 0,904 |
| como el ATD | B15: B14 con la etiqueta de control | 0,782 | 0,698–0,830 | +0,318 [+0,302 a +0,333] | 7 de 7 | 1655 / 1736 | 0,926 |
| como el ATD | B16: B15 con SkillCorner | 0,781 | 0,719–0,831 | +0,317 [+0,302 a +0,332] | 7 de 7 | 1686 / 1736 | 0,926 |
| como el ATD | B17: media de B15 y B16 | 0,789 | 0,723–0,836 | +0,326 [+0,310 a +0,341] | 7 de 7 | 1654 / 1736 | 0,927 |
| como el ATD | elegida dejando un partido fuera | 0,789 | – | +0,326 | – | 1654 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,494 | 0,465–0,528 | – | – | 2811 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,748 | 0,691–0,802 | +0,254 [+0,240 a +0,268] | 7 de 7 | 1675 / 1736 | 0,912 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 0,789 | 0,710–0,843 | +0,296 [+0,279 a +0,310] | 7 de 7 | 1662 / 1736 | 0,929 |
| como el ATD, sin bloques | B16: B15 con SkillCorner | 0,791 | 0,748–0,839 | +0,298 [+0,283 a +0,311] | 7 de 7 | 1705 / 1736 | 0,930 |
| como el ATD, sin bloques | B17: media de B15 y B16 | 0,795 | 0,746–0,834 | +0,302 [+0,286 a +0,315] | 7 de 7 | 1669 / 1736 | 0,930 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,795 | – | +0,302 | – | 1669 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,524 | 0,483–0,573 | – | – | 2726 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,764 | 0,713–0,815 | +0,241 [+0,227 a +0,254] | 7 de 7 | 1675 / 1736 | 0,917 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 0,804 | 0,742–0,842 | +0,281 [+0,265 a +0,294] | 7 de 7 | 1669 / 1736 | 0,933 |
| limpio (sin voto) | B16: B15 con SkillCorner | 0,803 | 0,769–0,850 | +0,280 [+0,264 a +0,293] | 7 de 7 | 1680 / 1736 | 0,934 |
| limpio (sin voto) | B17: media de B15 y B16 | 0,810 | 0,754–0,847 | +0,286 [+0,271 a +0,300] | 7 de 7 | 1657 / 1736 | 0,934 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,810 | – | +0,286 | – | 1657 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,448 | 0,422–0,515 | – | – | 2944 / 1736 | 0,830 |
| huecos y suavizado (sin voto) | main | 0,705 | 0,640–0,745 | +0,257 [+0,242 a +0,272] | 7 de 7 | 1674 / 1736 | 0,900 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 0,767 | 0,672–0,828 | +0,319 [+0,302 a +0,335] | 7 de 7 | 1623 / 1736 | 0,920 |
| huecos y suavizado (sin voto) | B16: B15 con SkillCorner | 0,763 | 0,686–0,812 | +0,315 [+0,299 a +0,330] | 7 de 7 | 1580 / 1736 | 0,920 |
| huecos y suavizado (sin voto) | B17: media de B15 y B16 | 0,769 | 0,697–0,828 | +0,321 [+0,305 a +0,336] | 7 de 7 | 1608 / 1736 | 0,921 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,765 | – | +0,317 | – | 1613 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B15: B14 con la etiqueta de control: **gana**
- B16: B15 con SkillCorner: **gana**
- B17: media de B15 y B16: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B15: B14 con la etiqueta de control | +0,048 [+0,038 a +0,058] | 6 de 7 |
| flag | como el ATD | B16: B15 con SkillCorner | +0,046 [+0,037 a +0,056] | 6 de 7 |
| flag | como el ATD | B17: media de B15 y B16 | +0,049 [+0,039 a +0,059] | 7 de 7 |
| flag | como el ATD, sin bloques | B15: B14 con la etiqueta de control | +0,037 [+0,027 a +0,047] | 6 de 7 |
| flag | como el ATD, sin bloques | B16: B15 con SkillCorner | +0,041 [+0,032 a +0,051] | 7 de 7 |
| flag | como el ATD, sin bloques | B17: media de B15 y B16 | +0,039 [+0,030 a +0,049] | 7 de 7 |
| flag | limpio (sin voto) | B15: B14 con la etiqueta de control | +0,027 [+0,018 a +0,038] | 7 de 7 |
| flag | limpio (sin voto) | B16: B15 con SkillCorner | +0,031 [+0,022 a +0,041] | 6 de 7 |
| flag | limpio (sin voto) | B17: media de B15 y B16 | +0,033 [+0,023 a +0,043] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | +0,041 [+0,031 a +0,051] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B16: B15 con SkillCorner | +0,035 [+0,026 a +0,045] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B17: media de B15 y B16 | +0,042 [+0,033 a +0,052] | 7 de 7 |
| control | como el ATD | B15: B14 con la etiqueta de control | +0,054 [+0,041 a +0,066] | 7 de 7 |
| control | como el ATD | B16: B15 con SkillCorner | +0,052 [+0,041 a +0,063] | 7 de 7 |
| control | como el ATD | B17: media de B15 y B16 | +0,061 [+0,049 a +0,072] | 7 de 7 |
| control | como el ATD, sin bloques | B15: B14 con la etiqueta de control | +0,042 [+0,030 a +0,053] | 7 de 7 |
| control | como el ATD, sin bloques | B16: B15 con SkillCorner | +0,043 [+0,033 a +0,054] | 7 de 7 |
| control | como el ATD, sin bloques | B17: media de B15 y B16 | +0,048 [+0,037 a +0,059] | 7 de 7 |
| control | limpio (sin voto) | B15: B14 con la etiqueta de control | +0,040 [+0,028 a +0,051] | 7 de 7 |
| control | limpio (sin voto) | B16: B15 con SkillCorner | +0,039 [+0,029 a +0,049] | 7 de 7 |
| control | limpio (sin voto) | B17: media de B15 y B16 | +0,045 [+0,034 a +0,057] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | +0,062 [+0,050 a +0,073] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B16: B15 con SkillCorner | +0,058 [+0,048 a +0,069] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B17: media de B15 y B16 | +0,064 [+0,053 a +0,075] | 7 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B15: B14 con la etiqueta de control: **gana**
- B16: B15 con SkillCorner: **gana**
- B17: media de B15 y B16: **gana**

### Eventos humanos (descriptivo; regla de lectura en validation/harness/README.md)

Puntos, con los partidos medidos juntos: 3142 pase completado, 195 recuperación, 229 duelo con cambio, 211 duelo sin cambio.

| balón | versión | pase completado | recuperación | duelo con cambio | duelo sin cambio |
|---|---|---|---|---|---|
| (todas) | etiquetas «flag» como predicción | 97,9 | 89,2 | 88,6 | 47,4 |
| (todas) | etiquetas «control» como predicción | 98,8 | 87,7 | 84,3 | 74,9 |
| como el ATD | control: voto ±50 | 89,5 | 84,1 | 82,5 | 55,0 |
| como el ATD | main | 96,3 | 70,3 | 77,3 | 74,9 |
| como el ATD | B15: B14 con la etiqueta de control | 98,3 | 77,4 | 79,5 | 72,5 |
| como el ATD | B16: B15 con SkillCorner | 98,3 | 70,3 | 82,1 | 77,3 |
| como el ATD | B17: media de B15 y B16 | 98,5 | 75,9 | 79,0 | 74,4 |
| como el ATD, sin bloques | control: voto ±50 | 91,1 | 87,7 | 86,9 | 55,9 |
| como el ATD, sin bloques | main | 96,9 | 72,8 | 80,3 | 73,9 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 98,4 | 79,0 | 81,2 | 72,5 |
| como el ATD, sin bloques | B16: B15 con SkillCorner | 98,7 | 71,8 | 83,4 | 77,3 |
| como el ATD, sin bloques | B17: media de B15 y B16 | 98,7 | 76,9 | 80,3 | 73,5 |
| limpio (sin voto) | control: voto ±50 | 93,1 | 91,3 | 88,2 | 55,5 |
| limpio (sin voto) | main | 97,9 | 74,9 | 83,0 | 75,4 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 98,6 | 80,5 | 80,8 | 73,5 |
| limpio (sin voto) | B16: B15 con SkillCorner | 98,9 | 74,4 | 83,4 | 80,6 |
| limpio (sin voto) | B17: media de B15 y B16 | 98,9 | 75,4 | 81,2 | 76,8 |
| huecos y suavizado (sin voto) | control: voto ±50 | 88,9 | 84,6 | 77,7 | 59,7 |
| huecos y suavizado (sin voto) | main | 95,7 | 56,9 | 60,3 | 81,0 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 97,5 | 70,8 | 77,7 | 76,8 |
| huecos y suavizado (sin voto) | B16: B15 con SkillCorner | 97,9 | 64,1 | 76,0 | 78,2 |
| huecos y suavizado (sin voto) | B17: media de B15 y B16 | 98,0 | 68,2 | 77,3 | 79,1 |

Diferencias en puntos, [5–95 %]:

| balón | versión | frente a | recuperación | duelo con cambio | duelo sin cambio | lectura |
|---|---|---|---|---|---|---|
| como el ATD | main | control: voto ±50 | -13,8 [-19,0 a -8,2] | -5,2 [-9,2 a -1,3] | +19,9 [+14,2 a +25,6] | compromiso |
| como el ATD | B15: B14 con la etiqueta de control | control: voto ±50 | -6,7 [-11,8 a -1,0] | -3,1 [-7,4 a +0,9] | +17,5 [+11,8 a +24,2] | compromiso |
| como el ATD | B15: B14 con la etiqueta de control | main | +7,2 [+1,5 a +12,8] | +2,2 [-1,7 a +6,1] | -2,4 [-7,6 a +2,8] | mejora |
| como el ATD | B16: B15 con SkillCorner | control: voto ±50 | -13,8 [-19,5 a -8,2] | -0,4 [-4,8 a +3,9] | +22,3 [+16,1 a +28,9] | compromiso |
| como el ATD | B16: B15 con SkillCorner | main | +0,0 [-5,2 a +5,1] | +4,8 [+1,3 a +8,3] | +2,4 [-1,9 a +6,6] | mejora |
| como el ATD | B17: media de B15 y B16 | control: voto ±50 | -8,2 [-13,3 a -2,6] | -3,5 [-7,9 a +0,9] | +19,4 [+13,7 a +25,6] | compromiso |
| como el ATD | B17: media de B15 y B16 | main | +5,6 [+0,0 a +10,8] | +1,7 [-2,2 a +5,2] | -0,5 [-5,2 a +4,3] | no concluye |
| como el ATD, sin bloques | main | control: voto ±50 | -14,9 [-19,5 a -9,7] | -6,6 [-10,5 a -2,6] | +18,0 [+12,3 a +23,7] | compromiso |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | control: voto ±50 | -8,7 [-13,8 a -3,1] | -5,7 [-9,6 a -2,2] | +16,6 [+10,9 a +22,7] | compromiso |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | main | +6,2 [+0,5 a +11,8] | +0,9 [-2,6 a +4,4] | -1,4 [-5,7 a +3,8] | mejora |
| como el ATD, sin bloques | B16: B15 con SkillCorner | control: voto ±50 | -15,9 [-21,0 a -10,8] | -3,5 [-7,9 a +0,4] | +21,3 [+15,2 a +27,0] | compromiso |
| como el ATD, sin bloques | B16: B15 con SkillCorner | main | -1,0 [-6,2 a +3,6] | +3,1 [-0,4 a +6,6] | +3,3 [-0,5 a +7,6] | no concluye |
| como el ATD, sin bloques | B17: media de B15 y B16 | control: voto ±50 | -10,8 [-16,4 a -5,1] | -6,6 [-10,9 a -2,6] | +17,5 [+11,8 a +23,7] | compromiso |
| como el ATD, sin bloques | B17: media de B15 y B16 | main | +4,1 [-1,0 a +9,2] | +0,0 [-3,5 a +3,5] | -0,5 [-4,7 a +4,7] | no concluye |
| limpio (sin voto) | main | control: voto ±50 | -16,4 [-21,5 a -11,3] | -5,2 [-8,7 a -1,7] | +19,9 [+14,7 a +25,1] | compromiso |
| limpio (sin voto) | B15: B14 con la etiqueta de control | control: voto ±50 | -10,8 [-15,4 a -5,6] | -7,4 [-11,8 a -3,5] | +18,0 [+12,3 a +24,2] | compromiso |
| limpio (sin voto) | B15: B14 con la etiqueta de control | main | +5,6 [+0,0 a +10,8] | -2,2 [-6,6 a +1,7] | -1,9 [-6,6 a +3,3] | no concluye |
| limpio (sin voto) | B16: B15 con SkillCorner | control: voto ±50 | -16,9 [-22,1 a -11,8] | -4,8 [-9,2 a -0,9] | +25,1 [+19,4 a +30,8] | compromiso |
| limpio (sin voto) | B16: B15 con SkillCorner | main | -0,5 [-5,2 a +4,1] | +0,4 [-3,5 a +3,9] | +5,2 [+0,9 a +9,5] | mejora |
| limpio (sin voto) | B17: media de B15 y B16 | control: voto ±50 | -15,9 [-21,5 a -10,3] | -7,0 [-10,9 a -3,1] | +21,3 [+15,6 a +27,0] | compromiso |
| limpio (sin voto) | B17: media de B15 y B16 | main | +0,5 [-4,6 a +5,1] | -1,7 [-5,7 a +1,7] | +1,4 [-2,8 a +6,2] | no concluye |
| huecos y suavizado (sin voto) | main | control: voto ±50 | -27,7 [-33,4 a -21,5] | -17,5 [-22,7 a -11,8] | +21,3 [+15,6 a +27,0] | compromiso |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | control: voto ±50 | -13,8 [-19,5 a -8,7] | +0,0 [-4,8 a +4,4] | +17,1 [+11,4 a +23,2] | compromiso |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | main | +13,8 [+8,2 a +19,0] | +17,5 [+12,7 a +22,7] | -4,3 [-8,5 a +0,5] | mejora |
| huecos y suavizado (sin voto) | B16: B15 con SkillCorner | control: voto ±50 | -20,5 [-26,7 a -14,4] | -1,7 [-6,6 a +3,1] | +18,5 [+12,3 a +24,6] | compromiso |
| huecos y suavizado (sin voto) | B16: B15 con SkillCorner | main | +7,2 [+1,5 a +12,3] | +15,7 [+10,9 a +20,5] | -2,8 [-7,1 a +1,9] | mejora |
| huecos y suavizado (sin voto) | B17: media de B15 y B16 | control: voto ±50 | -16,4 [-22,1 a -11,3] | -0,4 [-4,8 a +4,4] | +19,4 [+13,7 a +25,6] | compromiso |
| huecos y suavizado (sin voto) | B17: media de B15 y B16 | main | +11,3 [+5,6 a +16,4] | +17,0 [+12,2 a +22,3] | -1,9 [-6,2 a +2,8] | mejora |

Veredicto en las condiciones que votan: «como el ATD», «como el ATD, sin bloques» (descriptivo, no entra en §5.8):

- main: frente a control: voto ±50, **compromiso**
- B15: B14 con la etiqueta de control: frente a control: voto ±50, **compromiso**; frente a main, **mejora**
- B16: B15 con SkillCorner: frente a control: voto ±50, **compromiso**; frente a main, **depende del balón**
- B17: media de B15 y B16: frente a control: voto ±50, **compromiso**; frente a main, **no concluye**
