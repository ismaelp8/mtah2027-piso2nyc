D: propio · partidos: 7 · bootstrap: 1000
versiones: validation/harness/versiones/b17_media_2026-11-17.json (huella a5b8402c52be) · código: a88d550
- main: {"nota": "la entrega: B5 (aprendida.evidence_b5), dead_state y decode_cortas_a_d; el harness deja fuera el partido que puntúa"}
- B15: B14 con la etiqueta de control: {"nota": "docs/decisiones.md, 17/11, «B15»: referencia", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b15"}}}
- B16: B15 con SkillCorner: {"nota": "docs/decisiones.md, 17/11, «B16»: B15 entrenada también con SkillCorner ENTRENAMIENTO", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b16"}}}
- B17: media de B15 y B16: {"nota": "docs/decisiones.md, 17/11, «B17»: la media de los logits de B15 y B16, sin reentrenar; α, la media geométrica de las dos", "piezas": {"candidates": {"dejar_fuera": true, "funcion": "aprendida.evidence_b17"}}}
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
| como el ATD | B15: B14 con la etiqueta de control | 0,457 | 0,356–0,525 | +0,147 [+0,135 a +0,160] | 7 de 7 | 1556 / 3061 | 0,837 |
| como el ATD | B16: B15 con SkillCorner | 0,456 | 0,360–0,517 | +0,146 [+0,132 a +0,159] | 7 de 7 | 1568 / 3061 | 0,834 |
| como el ATD | B17: media de B15 y B16 | 0,461 | 0,362–0,537 | +0,151 [+0,138 a +0,164] | 7 de 7 | 1556 / 3061 | 0,837 |
| como el ATD | elegida dejando un partido fuera | 0,461 | – | +0,151 | – | 1556 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,346 | 0,306–0,399 | – | – | 3421 / 3061 | 0,819 |
| como el ATD, sin bloques | main | 0,431 | 0,365–0,508 | +0,084 [+0,073 a +0,096] | 7 de 7 | 1537 / 3061 | 0,828 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 0,465 | 0,374–0,532 | +0,118 [+0,106 a +0,131] | 7 de 7 | 1558 / 3061 | 0,845 |
| como el ATD, sin bloques | B16: B15 con SkillCorner | 0,468 | 0,392–0,525 | +0,121 [+0,109 a +0,134] | 7 de 7 | 1578 / 3061 | 0,843 |
| como el ATD, sin bloques | B17: media de B15 y B16 | 0,468 | 0,398–0,536 | +0,122 [+0,110 a +0,135] | 7 de 7 | 1561 / 3061 | 0,845 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,462 | – | +0,115 | – | 1545 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,351 | 0,314–0,402 | – | – | 3508 / 3061 | 0,831 |
| limpio (sin voto) | main | 0,440 | 0,386–0,511 | +0,088 [+0,076 a +0,100] | 7 de 7 | 1532 / 3061 | 0,834 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 0,466 | 0,394–0,534 | +0,115 [+0,102 a +0,128] | 7 de 7 | 1559 / 3061 | 0,848 |
| limpio (sin voto) | B16: B15 con SkillCorner | 0,468 | 0,401–0,522 | +0,117 [+0,104 a +0,129] | 7 de 7 | 1559 / 3061 | 0,846 |
| limpio (sin voto) | B17: media de B15 y B16 | 0,467 | 0,410–0,527 | +0,115 [+0,103 a +0,128] | 7 de 7 | 1544 / 3061 | 0,848 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,464 | – | +0,113 | – | 1539 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,327 | 0,295–0,357 | – | – | 3274 / 3061 | 0,757 |
| huecos y suavizado (sin voto) | main | 0,391 | 0,341–0,440 | +0,064 [+0,052 a +0,077] | 7 de 7 | 1542 / 3061 | 0,801 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 0,435 | 0,353–0,512 | +0,108 [+0,095 a +0,121] | 7 de 7 | 1510 / 3061 | 0,822 |
| huecos y suavizado (sin voto) | B16: B15 con SkillCorner | 0,427 | 0,345–0,528 | +0,100 [+0,087 a +0,113] | 7 de 7 | 1473 / 3061 | 0,820 |
| huecos y suavizado (sin voto) | B17: media de B15 y B16 | 0,433 | 0,347–0,523 | +0,106 [+0,092 a +0,119] | 7 de 7 | 1498 / 3061 | 0,822 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,435 | – | +0,108 | – | 1510 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,353 | 0,325–0,380 | – | – | 3458 / 1736 | 0,773 |
| como el ATD | main | 0,623 | 0,522–0,680 | +0,270 [+0,254 a +0,287] | 7 de 7 | 1538 / 1736 | 0,856 |
| como el ATD | B15: B14 con la etiqueta de control | 0,673 | 0,558–0,731 | +0,320 [+0,302 a +0,335] | 7 de 7 | 1556 / 1736 | 0,875 |
| como el ATD | B16: B15 con SkillCorner | 0,667 | 0,559–0,719 | +0,315 [+0,298 a +0,330] | 7 de 7 | 1568 / 1736 | 0,875 |
| como el ATD | B17: media de B15 y B16 | 0,678 | 0,570–0,736 | +0,325 [+0,308 a +0,340] | 7 de 7 | 1556 / 1736 | 0,876 |
| como el ATD | elegida dejando un partido fuera | 0,678 | – | +0,325 | – | 1556 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,397 | 0,355–0,426 | – | – | 3421 / 1736 | 0,839 |
| como el ATD, sin bloques | main | 0,651 | 0,571–0,704 | +0,253 [+0,239 a +0,268] | 7 de 7 | 1537 / 1736 | 0,869 |
| como el ATD, sin bloques | B15: B14 con la etiqueta de control | 0,685 | 0,595–0,751 | +0,288 [+0,272 a +0,303] | 7 de 7 | 1558 / 1736 | 0,885 |
| como el ATD, sin bloques | B16: B15 con SkillCorner | 0,684 | 0,619–0,738 | +0,287 [+0,272 a +0,301] | 7 de 7 | 1578 / 1736 | 0,885 |
| como el ATD, sin bloques | B17: media de B15 y B16 | 0,689 | 0,621–0,745 | +0,292 [+0,276 a +0,307] | 7 de 7 | 1561 / 1736 | 0,886 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,689 | – | +0,292 | – | 1561 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,407 | 0,369–0,442 | – | – | 3508 / 1736 | 0,851 |
| limpio (sin voto) | main | 0,666 | 0,594–0,713 | +0,260 [+0,245 a +0,273] | 7 de 7 | 1532 / 1736 | 0,875 |
| limpio (sin voto) | B15: B14 con la etiqueta de control | 0,701 | 0,628–0,745 | +0,294 [+0,279 a +0,310] | 7 de 7 | 1559 / 1736 | 0,889 |
| limpio (sin voto) | B16: B15 con SkillCorner | 0,694 | 0,628–0,752 | +0,287 [+0,273 a +0,302] | 7 de 7 | 1559 / 1736 | 0,889 |
| limpio (sin voto) | B17: media de B15 y B16 | 0,701 | 0,634–0,751 | +0,294 [+0,279 a +0,309] | 7 de 7 | 1544 / 1736 | 0,890 |
| limpio (sin voto) | elegida dejando un partido fuera | 0,696 | – | +0,289 | – | 1553 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,351 | 0,327–0,385 | – | – | 3274 / 1736 | 0,775 |
| huecos y suavizado (sin voto) | main | 0,590 | 0,514–0,632 | +0,239 [+0,223 a +0,255] | 7 de 7 | 1542 / 1736 | 0,841 |
| huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | 0,653 | 0,549–0,721 | +0,302 [+0,284 a +0,318] | 7 de 7 | 1510 / 1736 | 0,861 |
| huecos y suavizado (sin voto) | B16: B15 con SkillCorner | 0,644 | 0,530–0,708 | +0,293 [+0,275 a +0,309] | 7 de 7 | 1473 / 1736 | 0,861 |
| huecos y suavizado (sin voto) | B17: media de B15 y B16 | 0,651 | 0,545–0,718 | +0,300 [+0,283 a +0,316] | 7 de 7 | 1498 / 1736 | 0,861 |
| huecos y suavizado (sin voto) | elegida dejando un partido fuera | 0,653 | – | +0,302 | – | 1510 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B15: B14 con la etiqueta de control: **gana**
- B16: B15 con SkillCorner: **gana**
- B17: media de B15 y B16: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B15: B14 con la etiqueta de control | +0,043 [+0,034 a +0,053] | 7 de 7 |
| flag | como el ATD | B16: B15 con SkillCorner | +0,042 [+0,034 a +0,051] | 7 de 7 |
| flag | como el ATD | B17: media de B15 y B16 | +0,047 [+0,038 a +0,056] | 7 de 7 |
| flag | como el ATD, sin bloques | B15: B14 con la etiqueta de control | +0,034 [+0,025 a +0,044] | 7 de 7 |
| flag | como el ATD, sin bloques | B16: B15 con SkillCorner | +0,037 [+0,029 a +0,046] | 7 de 7 |
| flag | como el ATD, sin bloques | B17: media de B15 y B16 | +0,038 [+0,029 a +0,047] | 7 de 7 |
| flag | limpio (sin voto) | B15: B14 con la etiqueta de control | +0,027 [+0,018 a +0,036] | 7 de 7 |
| flag | limpio (sin voto) | B16: B15 con SkillCorner | +0,028 [+0,019 a +0,037] | 7 de 7 |
| flag | limpio (sin voto) | B17: media de B15 y B16 | +0,027 [+0,018 a +0,036] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | +0,044 [+0,034 a +0,053] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B16: B15 con SkillCorner | +0,036 [+0,027 a +0,045] | 7 de 7 |
| flag | huecos y suavizado (sin voto) | B17: media de B15 y B16 | +0,042 [+0,033 a +0,051] | 7 de 7 |
| control | como el ATD | B15: B14 con la etiqueta de control | +0,050 [+0,037 a +0,062] | 7 de 7 |
| control | como el ATD | B16: B15 con SkillCorner | +0,044 [+0,034 a +0,054] | 7 de 7 |
| control | como el ATD | B17: media de B15 y B16 | +0,055 [+0,043 a +0,066] | 7 de 7 |
| control | como el ATD, sin bloques | B15: B14 con la etiqueta de control | +0,035 [+0,022 a +0,046] | 7 de 7 |
| control | como el ATD, sin bloques | B16: B15 con SkillCorner | +0,034 [+0,023 a +0,044] | 7 de 7 |
| control | como el ATD, sin bloques | B17: media de B15 y B16 | +0,039 [+0,027 a +0,050] | 6 de 7 |
| control | limpio (sin voto) | B15: B14 con la etiqueta de control | +0,035 [+0,023 a +0,046] | 6 de 7 |
| control | limpio (sin voto) | B16: B15 con SkillCorner | +0,028 [+0,018 a +0,038] | 7 de 7 |
| control | limpio (sin voto) | B17: media de B15 y B16 | +0,035 [+0,024 a +0,046] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B15: B14 con la etiqueta de control | +0,063 [+0,051 a +0,074] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B16: B15 con SkillCorner | +0,054 [+0,043 a +0,065] | 7 de 7 |
| control | huecos y suavizado (sin voto) | B17: media de B15 y B16 | +0,061 [+0,050 a +0,071] | 7 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B15: B14 con la etiqueta de control: **gana**
- B16: B15 con SkillCorner: **gana**
- B17: media de B15 y B16: **gana**
