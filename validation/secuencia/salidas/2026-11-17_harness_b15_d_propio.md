D: propio · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/b15_control_2026-11-17.json (huella a9120537a4a5) · código: f3f7e9b
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- B14: trayectorias con dominio aleatorizado: {"nota": "docs/decisiones.md, 17/11, «B14»: referencia para B15", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b14"}}}
- B15: B14 con la etiqueta de control: {"nota": "docs/decisiones.md, 17/11, «B15»: la red de B14 entrenada con la etiqueta de control en todos los frames vivos; puntuada como B5", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b15"}}}
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
| como el ATD | B14: trayectorias con dominio aleatorizado | 0,525 | 0,437–0,600 | +0,214 [+0,201 a +0,228] | 7 de 7 | 1747 / 3061 | 0,850 |
| como el ATD | B15: B14 con la etiqueta de control | 0,457 | 0,356–0,525 | +0,147 [+0,135 a +0,160] | 7 de 7 | 1556 / 3061 | 0,837 |
| como el ATD | elegida dejando un partido fuera | 0,525 | – | +0,214 | – | 1747 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,346 | 0,306–0,399 | – | – | 3421 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,431 | 0,365–0,508 | +0,084 [+0,073 a +0,096] | 7 de 7 | 1537 / 3061 | 0,828 |
| como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | 0,536 | 0,469–0,612 | +0,190 [+0,177 a +0,203] | 7 de 7 | 1775 / 3061 | 0,860 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 0,465 | 0,374–0,532 | +0,118 [+0,106 a +0,131] | 7 de 7 | 1558 / 3061 | 0,845 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,536 | – | +0,190 | – | 1775 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,351 | 0,314–0,402 | – | – | 3508 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,440 | 0,386–0,511 | +0,088 [+0,076 a +0,100] | 7 de 7 | 1532 / 3061 | 0,834 |
| limpio (sin voto) | B14: trayectorias con dominio aleatorizado | 0,534 | 0,466–0,603 | +0,183 [+0,170 a +0,196] | 7 de 7 | 1752 / 3061 | 0,861 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 0,466 | 0,394–0,534 | +0,115 [+0,102 a +0,128] | 7 de 7 | 1559 / 3061 | 0,848 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,534 | – | +0,183 | – | 1752 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,327 | 0,295–0,357 | – | – | 3274 / 3061 | 0,757 |
| huecos y suavizado (sin voto) | main | 0,391 | 0,341–0,440 | +0,064 [+0,052 a +0,077] | 7 de 7 | 1542 / 3061 | 0,801 |
| huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | 0,482 | 0,398–0,555 | +0,155 [+0,142 a +0,169] | 7 de 7 | 1630 / 3061 | 0,830 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 0,435 | 0,353–0,512 | +0,108 [+0,095 a +0,121] | 7 de 7 | 1510 / 3061 | 0,822 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,482 | – | +0,155 | – | 1630 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,353 | 0,325–0,380 | – | – | 3458 / 1736 | 0,773 |
| como el ATD | main | 0,623 | 0,522–0,680 | +0,270 [+0,254 a +0,287] | 7 de 7 | 1538 / 1736 | 0,856 |
| como el ATD | B14: trayectorias con dominio aleatorizado | 0,676 | 0,613–0,714 | +0,323 [+0,308 a +0,337] | 7 de 7 | 1747 / 1736 | 0,876 |
| como el ATD | B15: B14 con la etiqueta de control | 0,673 | 0,558–0,731 | +0,320 [+0,302 a +0,335] | 7 de 7 | 1556 / 1736 | 0,875 |
| como el ATD | elegida dejando un partido fuera | 0,663 | – | +0,311 | – | 1688 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,397 | 0,355–0,426 | – | – | 3421 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,651 | 0,571–0,704 | +0,253 [+0,239 a +0,268] | 7 de 7 | 1537 / 1736 | 0,869 |
| como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | 0,680 | 0,644–0,708 | +0,283 [+0,270 a +0,297] | 7 de 7 | 1775 / 1736 | 0,883 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 0,685 | 0,595–0,751 | +0,288 [+0,272 a +0,303] | 7 de 7 | 1558 / 1736 | 0,885 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,674 | – | +0,277 | – | 1635 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,407 | 0,369–0,442 | – | – | 3508 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,666 | 0,594–0,713 | +0,260 [+0,245 a +0,273] | 7 de 7 | 1532 / 1736 | 0,875 |
| limpio (sin voto) | B14: trayectorias con dominio aleatorizado | 0,689 | 0,646–0,723 | +0,282 [+0,268 a +0,296] | 7 de 7 | 1752 / 1736 | 0,888 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 0,701 | 0,628–0,745 | +0,294 [+0,279 a +0,310] | 7 de 7 | 1559 / 1736 | 0,889 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,701 | – | +0,294 | – | 1559 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,351 | 0,327–0,385 | – | – | 3274 / 1736 | 0,775 |
| huecos y suavizado (sin voto) | main | 0,590 | 0,514–0,632 | +0,239 [+0,223 a +0,255] | 7 de 7 | 1542 / 1736 | 0,841 |
| huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | 0,655 | 0,573–0,705 | +0,304 [+0,288 a +0,320] | 7 de 7 | 1630 / 1736 | 0,859 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 0,653 | 0,549–0,721 | +0,302 [+0,284 a +0,318] | 7 de 7 | 1510 / 1736 | 0,861 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,648 | – | +0,297 | – | 1606 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B14: trayectorias con dominio aleatorizado: **gana**
- B15: B14 con la etiqueta de control: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B14: trayectorias con dominio aleatorizado | +0,111 [+0,100 a +0,123] | 7 de 7 |
| flag | como el ATD | B15: B14 con la etiqueta de control | +0,043 [+0,034 a +0,053] | 7 de 7 |
| flag | como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | +0,106 [+0,095 a +0,118] | 7 de 7 |
| flag | como el ATD, sin bloques | B15: B14 con la etiqueta de control | +0,034 [+0,025 a +0,044] | 7 de 7 |
| flag | limpio (sin voto) | B14: trayectorias con dominio aleatorizado | +0,094 [+0,083 a +0,107] | 7 de 7 |
| flag | limpio (sin voto) | B15: B14 con la etiqueta de control | +0,027 [+0,018 a +0,036] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | +0,091 [+0,081 a +0,102] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | +0,044 [+0,034 a +0,053] | 7 de 7 |
| control | como el ATD | B14: trayectorias con dominio aleatorizado | +0,053 [+0,040 a +0,066] | 7 de 7 |
| control | como el ATD | B15: B14 con la etiqueta de control | +0,050 [+0,037 a +0,062] | 7 de 7 |
| control | como el ATD, sin bloques | B14: trayectorias con dominio aleatorizado | +0,030 [+0,016 a +0,043] | 7 de 7 |
| control | como el ATD, sin bloques | B15: B14 con la etiqueta de control | +0,035 [+0,022 a +0,046] | 7 de 7 |
| control | limpio (sin voto) | B14: trayectorias con dominio aleatorizado | +0,022 [+0,010 a +0,034] | 7 de 7 |
| control | limpio (sin voto) | B15: B14 con la etiqueta de control | +0,035 [+0,023 a +0,046] | 6 de 7 |
| control | huecos y suavizado (sin voto) | B14: trayectorias con dominio aleatorizado | +0,065 [+0,053 a +0,077] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | +0,063 [+0,051 a +0,074] | 7 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B14: trayectorias con dominio aleatorizado: **empate o no concluye**
- B15: B14 con la etiqueta de control: **gana**
