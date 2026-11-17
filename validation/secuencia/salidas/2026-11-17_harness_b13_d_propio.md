D: propio · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/b13_trayectorias_2026-11-17.json (huella d10f5d6f7e85) · código: ad6dd9f
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- B12: GRU bidireccional: {"nota": "ronda 1 (docs/decisiones.md, 17/11): referencia para B13", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b12"}}}
- B13: trayectorias: {"nota": "docs/decisiones.md, 17/11, «B13»: codificador de conjuntos de jugadores y balón por equipo desde su dirección de ataque, GRU bidireccional a 5 Hz, entrenada también sin balón a trozos; puntuada como B5", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b13"}}}
AVISO: con el D propio, el balón tapado en los D de la DFL delata la etiqueta. No decide nada.

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
| como el ATD | control: voto ±50 | 0,310 | 0,282–0,363 | – | – | 3458 / 3061 | 0,755 |
| como el ATD | main | 0,414 | 0,343–0,472 | +0,104 [+0,092 a +0,116] | 7 de 7 | 1538 / 3061 | 0,817 |
| como el ATD | B12: GRU bidireccional | 0,460 | 0,384–0,529 | +0,150 [+0,137 a +0,163] | 7 de 7 | 1600 / 3061 | 0,834 |
| como el ATD | B13: trayectorias | 0,500 | 0,414–0,569 | +0,189 [+0,176 a +0,202] | 7 de 7 | 1703 / 3061 | 0,841 |
| como el ATD | elegida dejando un partido fuera | 0,500 | – | +0,189 | – | 1703 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,346 | 0,306–0,399 | – | – | 3421 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,431 | 0,365–0,508 | +0,084 [+0,073 a +0,096] | 7 de 7 | 1537 / 3061 | 0,828 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,484 | 0,411–0,552 | +0,137 [+0,125 a +0,149] | 7 de 7 | 1631 / 3061 | 0,845 |
| como el ATD, sin bloques | B13: trayectorias | 0,514 | 0,448–0,579 | +0,167 [+0,154 a +0,180] | 7 de 7 | 1725 / 3061 | 0,850 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,514 | – | +0,167 | – | 1725 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,351 | 0,314–0,402 | – | – | 3508 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,440 | 0,386–0,511 | +0,088 [+0,076 a +0,100] | 7 de 7 | 1532 / 3061 | 0,834 |
| limpio (sin voto) | B12: GRU bidireccional | 0,480 | 0,415–0,547 | +0,129 [+0,116 a +0,141] | 7 de 7 | 1603 / 3061 | 0,847 |
| limpio (sin voto) | B13: trayectorias | 0,521 | 0,461–0,587 | +0,170 [+0,157 a +0,182] | 7 de 7 | 1748 / 3061 | 0,852 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,521 | – | +0,170 | – | 1748 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,327 | 0,295–0,357 | – | – | 3274 / 3061 | 0,757 |
| huecos y suavizado (sin voto) | main | 0,391 | 0,341–0,440 | +0,064 [+0,052 a +0,077] | 7 de 7 | 1542 / 3061 | 0,801 |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | 0,432 | 0,342–0,481 | +0,105 [+0,092 a +0,118] | 7 de 7 | 1526 / 3061 | 0,816 |
| huecos y suavizado (sin voto) | B13: trayectorias | 0,464 | 0,376–0,540 | +0,137 [+0,124 a +0,151] | 7 de 7 | 1619 / 3061 | 0,824 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,464 | – | +0,137 | – | 1619 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,353 | 0,325–0,380 | – | – | 3458 / 1736 | 0,773 |
| como el ATD | main | 0,623 | 0,522–0,680 | +0,270 [+0,254 a +0,287] | 7 de 7 | 1538 / 1736 | 0,856 |
| como el ATD | B12: GRU bidireccional | 0,657 | 0,565–0,697 | +0,305 [+0,289 a +0,319] | 7 de 7 | 1600 / 1736 | 0,868 |
| como el ATD | B13: trayectorias | 0,648 | 0,559–0,690 | +0,296 [+0,279 a +0,310] | 7 de 7 | 1703 / 1736 | 0,864 |
| como el ATD | elegida dejando un partido fuera | 0,657 | – | +0,305 | – | 1600 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,397 | 0,355–0,426 | – | – | 3421 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,651 | 0,571–0,704 | +0,253 [+0,239 a +0,268] | 7 de 7 | 1537 / 1736 | 0,869 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,679 | 0,614–0,704 | +0,281 [+0,267 a +0,296] | 7 de 7 | 1631 / 1736 | 0,879 |
| como el ATD, sin bloques | B13: trayectorias | 0,657 | 0,601–0,688 | +0,260 [+0,245 a +0,274] | 7 de 7 | 1725 / 1736 | 0,871 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,679 | – | +0,281 | – | 1631 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,407 | 0,369–0,442 | – | – | 3508 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,666 | 0,594–0,713 | +0,260 [+0,245 a +0,273] | 7 de 7 | 1532 / 1736 | 0,875 |
| limpio (sin voto) | B12: GRU bidireccional | 0,691 | 0,636–0,721 | +0,284 [+0,269 a +0,297] | 7 de 7 | 1603 / 1736 | 0,884 |
| limpio (sin voto) | B13: trayectorias | 0,658 | 0,608–0,705 | +0,251 [+0,236 a +0,265] | 7 de 7 | 1748 / 1736 | 0,872 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,691 | – | +0,284 | – | 1603 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,351 | 0,327–0,385 | – | – | 3274 / 1736 | 0,775 |
| huecos y suavizado (sin voto) | main | 0,590 | 0,514–0,632 | +0,239 [+0,223 a +0,255] | 7 de 7 | 1542 / 1736 | 0,841 |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | 0,626 | 0,540–0,667 | +0,275 [+0,257 a +0,291] | 7 de 7 | 1526 / 1736 | 0,851 |
| huecos y suavizado (sin voto) | B13: trayectorias | 0,634 | 0,523–0,699 | +0,283 [+0,266 a +0,299] | 7 de 7 | 1619 / 1736 | 0,850 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,634 | – | +0,283 | – | 1619 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B12: GRU bidireccional: **gana**
- B13: trayectorias: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B12: GRU bidireccional | +0,046 [+0,038 a +0,055] | 7 de 7 |
| flag | como el ATD | B13: trayectorias | +0,086 [+0,075 a +0,098] | 7 de 7 |
| flag | como el ATD, sin bloques | B12: GRU bidireccional | +0,053 [+0,044 a +0,062] | 7 de 7 |
| flag | como el ATD, sin bloques | B13: trayectorias | +0,083 [+0,071 a +0,095] | 7 de 7 |
| flag | limpio (sin voto) | B12: GRU bidireccional | +0,040 [+0,032 a +0,050] | 7 de 7 |
| flag | limpio (sin voto) | B13: trayectorias | +0,081 [+0,070 a +0,093] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B12: GRU bidireccional | +0,041 [+0,032 a +0,051] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B13: trayectorias | +0,073 [+0,062 a +0,084] | 7 de 7 |
| control | como el ATD | B12: GRU bidireccional | +0,034 [+0,023 a +0,046] | 7 de 7 |
| control | como el ATD | B13: trayectorias | +0,025 [+0,012 a +0,038] | 5 de 7 |
| control | como el ATD, sin bloques | B12: GRU bidireccional | +0,028 [+0,017 a +0,039] | 5 de 7 |
| control | como el ATD, sin bloques | B13: trayectorias | +0,007 [-0,007 a +0,020] | 3 de 7 |
| control | limpio (sin voto) | B12: GRU bidireccional | +0,024 [+0,014 a +0,035] | 6 de 7 |
| control | limpio (sin voto) | B13: trayectorias | -0,008 [-0,021 a +0,005] | 2 de 7 |
| control | huecos y suavizado (sin voto) | B12: GRU bidireccional | +0,036 [+0,024 a +0,047] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B13: trayectorias | +0,044 [+0,031 a +0,056] | 7 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B12: GRU bidireccional: **empate o no concluye**
- B13: trayectorias: **empate o no concluye**
