D: propio · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/b11_secuencia_2026-11-17.json (huella ebc06129fb62) · código: bfc9566
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- B11: convolucional temporal: {"nota": "docs/decisiones.md, 17/11, «B11 y B12, modelos de secuencia»: canales por frame sin promediar, 7 bloques residuales dilatados (±5,1 s), puntuada como B5", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b11"}}}
- B12: GRU bidireccional: {"nota": "docs/decisiones.md, 17/11, «B11 y B12, modelos de secuencia»: los mismos canales a 5 Hz, GRU de 16 en cada sentido, puntuada como B5", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b12"}}}
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
| como el ATD | B11: convolucional temporal | 0,511 | 0,437–0,599 | +0,201 [+0,188 a +0,214] | 7 de 7 | 1798 / 3061 | 0,839 |
| como el ATD | B12: GRU bidireccional | 0,460 | 0,384–0,529 | +0,150 [+0,137 a +0,163] | 7 de 7 | 1600 / 3061 | 0,834 |
| como el ATD | elegida dejando un partido fuera | 0,511 | – | +0,201 | – | 1798 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,346 | 0,306–0,399 | – | – | 3421 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,431 | 0,365–0,508 | +0,084 [+0,073 a +0,096] | 7 de 7 | 1537 / 3061 | 0,828 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,532 | 0,464–0,623 | +0,185 [+0,173 a +0,197] | 7 de 7 | 1828 / 3061 | 0,851 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,484 | 0,411–0,552 | +0,137 [+0,125 a +0,149] | 7 de 7 | 1631 / 3061 | 0,845 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,532 | – | +0,185 | – | 1828 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,351 | 0,314–0,402 | – | – | 3508 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,440 | 0,386–0,511 | +0,088 [+0,076 a +0,100] | 7 de 7 | 1532 / 3061 | 0,834 |
| limpio (sin voto) | B11: convolucional temporal | 0,514 | 0,437–0,598 | +0,163 [+0,150 a +0,175] | 7 de 7 | 1782 / 3061 | 0,854 |
| limpio (sin voto) | B12: GRU bidireccional | 0,480 | 0,415–0,547 | +0,129 [+0,116 a +0,141] | 7 de 7 | 1603 / 3061 | 0,847 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,514 | – | +0,163 | – | 1782 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,327 | 0,295–0,357 | – | – | 3274 / 3061 | 0,757 |
| huecos y suavizado (sin voto) | main | 0,391 | 0,341–0,440 | +0,064 [+0,052 a +0,077] | 7 de 7 | 1542 / 3061 | 0,801 |
| huecos y suavizado (sin voto) | B11: convolucional temporal | 0,468 | 0,388–0,539 | +0,142 [+0,128 a +0,155] | 7 de 7 | 1707 / 3061 | 0,822 |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | 0,432 | 0,342–0,481 | +0,105 [+0,092 a +0,118] | 7 de 7 | 1526 / 3061 | 0,816 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,468 | – | +0,142 | – | 1707 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,353 | 0,325–0,380 | – | – | 3458 / 1736 | 0,773 |
| como el ATD | main | 0,623 | 0,522–0,680 | +0,270 [+0,254 a +0,287] | 7 de 7 | 1538 / 1736 | 0,856 |
| como el ATD | B11: convolucional temporal | 0,647 | 0,595–0,677 | +0,294 [+0,280 a +0,307] | 7 de 7 | 1798 / 1736 | 0,864 |
| como el ATD | B12: GRU bidireccional | 0,657 | 0,565–0,697 | +0,305 [+0,289 a +0,319] | 7 de 7 | 1600 / 1736 | 0,868 |
| como el ATD | elegida dejando un partido fuera | 0,657 | – | +0,305 | – | 1600 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,397 | 0,355–0,426 | – | – | 3421 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,651 | 0,571–0,704 | +0,253 [+0,239 a +0,268] | 7 de 7 | 1537 / 1736 | 0,869 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,665 | 0,632–0,695 | +0,268 [+0,255 a +0,280] | 7 de 7 | 1828 / 1736 | 0,875 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,679 | 0,614–0,704 | +0,281 [+0,267 a +0,296] | 7 de 7 | 1631 / 1736 | 0,879 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,679 | – | +0,281 | – | 1631 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,407 | 0,369–0,442 | – | – | 3508 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,666 | 0,594–0,713 | +0,260 [+0,245 a +0,273] | 7 de 7 | 1532 / 1736 | 0,875 |
| limpio (sin voto) | B11: convolucional temporal | 0,678 | 0,638–0,711 | +0,271 [+0,258 a +0,284] | 7 de 7 | 1782 / 1736 | 0,883 |
| limpio (sin voto) | B12: GRU bidireccional | 0,691 | 0,636–0,721 | +0,284 [+0,269 a +0,297] | 7 de 7 | 1603 / 1736 | 0,884 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,691 | – | +0,284 | – | 1603 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,351 | 0,327–0,385 | – | – | 3274 / 1736 | 0,775 |
| huecos y suavizado (sin voto) | main | 0,590 | 0,514–0,632 | +0,239 [+0,223 a +0,255] | 7 de 7 | 1542 / 1736 | 0,841 |
| huecos y suavizado (sin voto) | B11: convolucional temporal | 0,614 | 0,543–0,644 | +0,263 [+0,248 a +0,277] | 7 de 7 | 1707 / 1736 | 0,848 |
| huecos y suavizado (sin voto) | B12: GRU bidireccional | 0,626 | 0,540–0,667 | +0,275 [+0,257 a +0,291] | 7 de 7 | 1526 / 1736 | 0,851 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,626 | – | +0,275 | – | 1526 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B11: convolucional temporal: **gana**
- B12: GRU bidireccional: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B11: convolucional temporal | +0,097 [+0,087 a +0,109] | 7 de 7 |
| flag | como el ATD | B12: GRU bidireccional | +0,046 [+0,038 a +0,055] | 7 de 7 |
| flag | como el ATD, sin bloques | B11: convolucional temporal | +0,101 [+0,090 a +0,112] | 7 de 7 |
| flag | como el ATD, sin bloques | B12: GRU bidireccional | +0,053 [+0,044 a +0,062] | 7 de 7 |
| flag | limpio (sin voto) | B11: convolucional temporal | +0,075 [+0,064 a +0,085] | 7 de 7 |
| flag | limpio (sin voto) | B12: GRU bidireccional | +0,040 [+0,032 a +0,050] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B11: convolucional temporal | +0,077 [+0,067 a +0,087] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B12: GRU bidireccional | +0,041 [+0,032 a +0,051] | 7 de 7 |
| control | como el ATD | B11: convolucional temporal | +0,023 [+0,011 a +0,037] | 5 de 7 |
| control | como el ATD | B12: GRU bidireccional | +0,034 [+0,023 a +0,046] | 7 de 7 |
| control | como el ATD, sin bloques | B11: convolucional temporal | +0,014 [+0,001 a +0,027] | 5 de 7 |
| control | como el ATD, sin bloques | B12: GRU bidireccional | +0,028 [+0,017 a +0,039] | 5 de 7 |
| control | limpio (sin voto) | B11: convolucional temporal | +0,011 [-0,000 a +0,023] | 4 de 7 |
| control | limpio (sin voto) | B12: GRU bidireccional | +0,024 [+0,014 a +0,035] | 6 de 7 |
| control | huecos y suavizado (sin voto) | B11: convolucional temporal | +0,024 [+0,013 a +0,035] | 6 de 7 |
| control | huecos y suavizado (sin voto) | B12: GRU bidireccional | +0,036 [+0,024 a +0,047] | 7 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B11: convolucional temporal: **empate o no concluye**
- B12: GRU bidireccional: **empate o no concluye**
