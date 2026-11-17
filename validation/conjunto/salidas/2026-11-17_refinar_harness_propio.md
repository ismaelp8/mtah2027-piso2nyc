D: propio · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/refinamientos_k2_2026-11-17.json (huella 8114352b3e4a) · código: 8409165
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- K2: modelo conjunto en lugar de B5: {"nota": "docs/decisiones.md, 17/11, «modelo conjunto»: el logit de K2 puntuado como B5, con el pliegue que no vio el partido", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_k2"}}}
- K3: mezcla de K2 y B5: {"nota": "docs/decisiones.md, 17/11, «dos refinamientos de K2 sin reentrenar»: la media a partes iguales del logit de K2 y del de B5, cada uno en su escala y con el pliegue que no vio el partido, puntuada como B5 (possession/refinamientos.py)", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_k3"}}}
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
| como el ATD | K2: modelo conjunto en lugar de B5 | 0,457 | 0,378–0,521 | +0,146 [+0,133 a +0,160] | 7 de 7 | 1574 / 3061 | 0,836 |
| como el ATD | K3: mezcla de K2 y B5 | 0,439 | 0,370–0,504 | +0,129 [+0,116 a +0,141] | 7 de 7 | 1507 / 3061 | 0,832 |
| como el ATD | elegida dejando un partido fuera | 0,457 | – | +0,146 | – | 1574 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,346 | 0,306–0,399 | – | – | 3421 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,431 | 0,365–0,508 | +0,084 [+0,073 a +0,096] | 7 de 7 | 1537 / 3061 | 0,828 |
| como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | 0,464 | 0,392–0,527 | +0,117 [+0,105 a +0,130] | 7 de 7 | 1580 / 3061 | 0,845 |
| como el ATD, sin bloques | K3: mezcla de K2 y B5 | 0,448 | 0,391–0,513 | +0,101 [+0,089 a +0,114] | 7 de 7 | 1507 / 3061 | 0,840 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,464 | – | +0,117 | – | 1580 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,351 | 0,314–0,402 | – | – | 3508 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,440 | 0,386–0,511 | +0,088 [+0,076 a +0,100] | 7 de 7 | 1532 / 3061 | 0,834 |
| limpio (sin voto) | K2: modelo conjunto en lugar de B5 | 0,469 | 0,407–0,530 | +0,118 [+0,106 a +0,130] | 7 de 7 | 1598 / 3061 | 0,848 |
| limpio (sin voto) | K3: mezcla de K2 y B5 | 0,457 | 0,398–0,518 | +0,106 [+0,094 a +0,117] | 7 de 7 | 1519 / 3061 | 0,845 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,469 | – | +0,118 | – | 1598 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,327 | 0,295–0,357 | – | – | 3274 / 3061 | 0,757 |
| huecos y suavizado (sin voto) | main | 0,391 | 0,341–0,440 | +0,064 [+0,052 a +0,077] | 7 de 7 | 1542 / 3061 | 0,801 |
| huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | 0,431 | 0,360–0,504 | +0,105 [+0,091 a +0,117] | 7 de 7 | 1496 / 3061 | 0,821 |
| huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | 0,415 | 0,361–0,496 | +0,089 [+0,076 a +0,101] | 7 de 7 | 1450 / 3061 | 0,815 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,431 | – | +0,105 | – | 1496 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,353 | 0,325–0,380 | – | – | 3458 / 1736 | 0,773 |
| como el ATD | main | 0,623 | 0,522–0,680 | +0,270 [+0,254 a +0,287] | 7 de 7 | 1538 / 1736 | 0,856 |
| como el ATD | K2: modelo conjunto en lugar de B5 | 0,668 | 0,580–0,704 | +0,315 [+0,300 a +0,331] | 7 de 7 | 1574 / 1736 | 0,878 |
| como el ATD | K3: mezcla de K2 y B5 | 0,665 | 0,560–0,718 | +0,313 [+0,297 a +0,328] | 7 de 7 | 1507 / 1736 | 0,873 |
| como el ATD | elegida dejando un partido fuera | 0,662 | – | +0,309 | – | 1565 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,397 | 0,355–0,426 | – | – | 3421 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,651 | 0,571–0,704 | +0,253 [+0,239 a +0,268] | 7 de 7 | 1537 / 1736 | 0,869 |
| como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | 0,686 | 0,629–0,727 | +0,289 [+0,274 a +0,303] | 7 de 7 | 1580 / 1736 | 0,888 |
| como el ATD, sin bloques | K3: mezcla de K2 y B5 | 0,683 | 0,608–0,746 | +0,286 [+0,270 a +0,300] | 7 de 7 | 1507 / 1736 | 0,883 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,683 | – | +0,286 | – | 1576 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,407 | 0,369–0,442 | – | – | 3508 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,666 | 0,594–0,713 | +0,260 [+0,245 a +0,273] | 7 de 7 | 1532 / 1736 | 0,875 |
| limpio (sin voto) | K2: modelo conjunto en lugar de B5 | 0,691 | 0,624–0,738 | +0,284 [+0,269 a +0,297] | 7 de 7 | 1598 / 1736 | 0,891 |
| limpio (sin voto) | K3: mezcla de K2 y B5 | 0,699 | 0,623–0,755 | +0,292 [+0,277 a +0,306] | 7 de 7 | 1519 / 1736 | 0,890 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,699 | – | +0,292 | – | 1519 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,351 | 0,327–0,385 | – | – | 3274 / 1736 | 0,775 |
| huecos y suavizado (sin voto) | main | 0,590 | 0,514–0,632 | +0,239 [+0,223 a +0,255] | 7 de 7 | 1542 / 1736 | 0,841 |
| huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | 0,649 | 0,564–0,709 | +0,298 [+0,281 a +0,314] | 7 de 7 | 1496 / 1736 | 0,862 |
| huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | 0,642 | 0,560–0,700 | +0,291 [+0,274 a +0,307] | 7 de 7 | 1450 / 1736 | 0,858 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,649 | – | +0,298 | – | 1496 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- K2: modelo conjunto en lugar de B5: **gana**
- K3: mezcla de K2 y B5: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | K2: modelo conjunto en lugar de B5 | +0,043 [+0,034 a +0,052] | 7 de 7 |
| flag | como el ATD | K3: mezcla de K2 y B5 | +0,025 [+0,018 a +0,032] | 7 de 7 |
| flag | como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | +0,033 [+0,024 a +0,042] | 7 de 7 |
| flag | como el ATD, sin bloques | K3: mezcla de K2 y B5 | +0,017 [+0,011 a +0,024] | 7 de 7 |
| flag | limpio (sin voto) | K2: modelo conjunto en lugar de B5 | +0,030 [+0,021 a +0,039] | 7 de 7 |
| flag | limpio (sin voto) | K3: mezcla de K2 y B5 | +0,017 [+0,011 a +0,024] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | +0,040 [+0,031 a +0,050] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | +0,024 [+0,018 a +0,031] | 7 de 7 |
| control | como el ATD | K2: modelo conjunto en lugar de B5 | +0,045 [+0,035 a +0,057] | 6 de 7 |
| control | como el ATD | K3: mezcla de K2 y B5 | +0,042 [+0,034 a +0,050] | 7 de 7 |
| control | como el ATD, sin bloques | K2: modelo conjunto en lugar de B5 | +0,036 [+0,024 a +0,047] | 6 de 7 |
| control | como el ATD, sin bloques | K3: mezcla de K2 y B5 | +0,032 [+0,025 a +0,040] | 7 de 7 |
| control | limpio (sin voto) | K2: modelo conjunto en lugar de B5 | +0,024 [+0,013 a +0,035] | 6 de 7 |
| control | limpio (sin voto) | K3: mezcla de K2 y B5 | +0,032 [+0,024 a +0,040] | 7 de 7 |
| control | huecos y suavizado (sin voto) | K2: modelo conjunto en lugar de B5 | +0,059 [+0,048 a +0,070] | 7 de 7 |
| control | huecos y suavizado (sin voto) | K3: mezcla de K2 y B5 | +0,052 [+0,044 a +0,060] | 7 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- K2: modelo conjunto en lugar de B5: **gana**
- K3: mezcla de K2 y B5: **empate o no concluye**
