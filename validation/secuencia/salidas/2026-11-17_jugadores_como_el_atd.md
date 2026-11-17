## Jugadores «al azar» (sin voto; parámetro 78.12, suavizado 13)

### Etiquetas: flag

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,368 | 0,323–0,401 | – | – | 3065 / 3061 | 0,776 |
| como el ATD | main | 0,498 | 0,429–0,578 | +0,130 [+0,117 a +0,142] | 7 de 7 | 1712 / 3061 | 0,861 |
| como el ATD | B11: convolucional temporal | 0,583 | 0,520–0,648 | +0,215 [+0,202 a +0,227] | 7 de 7 | 2068 / 3061 | 0,884 |
| como el ATD | B12: GRU bidireccional | 0,546 | 0,479–0,604 | +0,179 [+0,165 a +0,191] | 7 de 7 | 1832 / 3061 | 0,877 |
| como el ATD | elegida dejando un partido fuera | 0,583 | – | +0,215 | – | 2068 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,391 | 0,360–0,415 | – | – | 3037 / 3061 | 0,788 |
| como el ATD, sin bloques | main | 0,508 | 0,439–0,593 | +0,117 [+0,104 a +0,129] | 7 de 7 | 1715 / 3061 | 0,867 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,598 | 0,543–0,676 | +0,207 [+0,194 a +0,219] | 7 de 7 | 2116 / 3061 | 0,890 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,566 | 0,504–0,620 | +0,175 [+0,162 a +0,187] | 7 de 7 | 1876 / 3061 | 0,884 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,598 | – | +0,207 | – | 2116 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,409 | 0,382–0,441 | – | – | 3065 / 1736 | 0,793 |
| como el ATD | main | 0,715 | 0,665–0,764 | +0,306 [+0,291 a +0,320] | 7 de 7 | 1712 / 1736 | 0,901 |
| como el ATD | B11: convolucional temporal | 0,705 | 0,675–0,748 | +0,296 [+0,282 a +0,308] | 7 de 7 | 2068 / 1736 | 0,907 |
| como el ATD | B12: GRU bidireccional | 0,743 | 0,699–0,785 | +0,334 [+0,319 a +0,348] | 7 de 7 | 1832 / 1736 | 0,912 |
| como el ATD | elegida dejando un partido fuera | 0,743 | – | +0,334 | – | 1832 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,432 | 0,421–0,452 | – | – | 3037 / 1736 | 0,807 |
| como el ATD, sin bloques | main | 0,734 | 0,690–0,786 | +0,302 [+0,287 a +0,315] | 7 de 7 | 1715 / 1736 | 0,909 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,717 | 0,688–0,746 | +0,284 [+0,271 a +0,296] | 7 de 7 | 2116 / 1736 | 0,913 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,759 | 0,707–0,801 | +0,327 [+0,312 a +0,340] | 7 de 7 | 1876 / 1736 | 0,918 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,759 | – | +0,327 | – | 1876 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B11: convolucional temporal: **gana**
- B12: GRU bidireccional: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B11: convolucional temporal | +0,085 [+0,074 a +0,096] | 7 de 7 |
| flag | como el ATD | B12: GRU bidireccional | +0,049 [+0,039 a +0,059] | 7 de 7 |
| flag | como el ATD, sin bloques | B11: convolucional temporal | +0,090 [+0,079 a +0,102] | 7 de 7 |
| flag | como el ATD, sin bloques | B12: GRU bidireccional | +0,058 [+0,049 a +0,068] | 7 de 7 |
| control | como el ATD | B11: convolucional temporal | -0,010 [-0,022 a +0,003] | 3 de 7 |
| control | como el ATD | B12: GRU bidireccional | +0,028 [+0,016 a +0,040] | 7 de 7 |
| control | como el ATD, sin bloques | B11: convolucional temporal | -0,017 [-0,029 a -0,005] | 2 de 7 |
| control | como el ATD, sin bloques | B12: GRU bidireccional | +0,025 [+0,013 a +0,037] | 6 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B11: convolucional temporal: **empate o no concluye**
- B12: GRU bidireccional: **empate o no concluye**

## Jugadores «en las aglomeraciones» (sin voto; parámetro 0.1875, suavizado 13)

### Etiquetas: flag

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,361 | 0,331–0,389 | – | – | 3021 / 3061 | 0,763 |
| como el ATD | main | 0,487 | 0,405–0,551 | +0,125 [+0,111 a +0,139] | 7 de 7 | 1666 / 3061 | 0,858 |
| como el ATD | B11: convolucional temporal | 0,578 | 0,507–0,643 | +0,217 [+0,203 a +0,230] | 7 de 7 | 2164 / 3061 | 0,881 |
| como el ATD | B12: GRU bidireccional | 0,543 | 0,481–0,597 | +0,182 [+0,168 a +0,195] | 7 de 7 | 1838 / 3061 | 0,875 |
| como el ATD | elegida dejando un partido fuera | 0,578 | – | +0,217 | – | 2164 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,377 | 0,350–0,403 | – | – | 2993 / 3061 | 0,771 |
| como el ATD, sin bloques | main | 0,501 | 0,414–0,574 | +0,123 [+0,110 a +0,137] | 7 de 7 | 1679 / 3061 | 0,863 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,597 | 0,525–0,668 | +0,219 [+0,206 a +0,232] | 7 de 7 | 2215 / 3061 | 0,888 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,561 | 0,492–0,610 | +0,184 [+0,170 a +0,197] | 7 de 7 | 1880 / 3061 | 0,881 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,597 | – | +0,219 | – | 2215 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,381 | 0,366–0,400 | – | – | 3021 / 1736 | 0,769 |
| como el ATD | main | 0,703 | 0,640–0,761 | +0,322 [+0,305 a +0,337] | 7 de 7 | 1666 / 1736 | 0,896 |
| como el ATD | B11: convolucional temporal | 0,673 | 0,639–0,718 | +0,292 [+0,278 a +0,304] | 7 de 7 | 2164 / 1736 | 0,898 |
| como el ATD | B12: GRU bidireccional | 0,727 | 0,674–0,751 | +0,346 [+0,330 a +0,360] | 7 de 7 | 1838 / 1736 | 0,907 |
| como el ATD | elegida dejando un partido fuera | 0,727 | – | +0,346 | – | 1838 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,395 | 0,371–0,430 | – | – | 2993 / 1736 | 0,776 |
| como el ATD, sin bloques | main | 0,719 | 0,673–0,771 | +0,325 [+0,310 a +0,340] | 7 de 7 | 1679 / 1736 | 0,902 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,680 | 0,651–0,720 | +0,286 [+0,273 a +0,297] | 7 de 7 | 2215 / 1736 | 0,902 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,736 | 0,710–0,757 | +0,342 [+0,327 a +0,355] | 7 de 7 | 1880 / 1736 | 0,912 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,736 | – | +0,342 | – | 1880 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B11: convolucional temporal: **gana**
- B12: GRU bidireccional: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B11: convolucional temporal | +0,092 [+0,080 a +0,104] | 7 de 7 |
| flag | como el ATD | B12: GRU bidireccional | +0,057 [+0,046 a +0,067] | 7 de 7 |
| flag | como el ATD, sin bloques | B11: convolucional temporal | +0,096 [+0,083 a +0,109] | 7 de 7 |
| flag | como el ATD, sin bloques | B12: GRU bidireccional | +0,061 [+0,050 a +0,070] | 7 de 7 |
| control | como el ATD | B11: convolucional temporal | -0,030 [-0,044 a -0,017] | 0 de 7 |
| control | como el ATD | B12: GRU bidireccional | +0,024 [+0,012 a +0,037] | 6 de 7 |
| control | como el ATD, sin bloques | B11: convolucional temporal | -0,039 [-0,054 a -0,026] | 0 de 7 |
| control | como el ATD, sin bloques | B12: GRU bidireccional | +0,017 [+0,004 a +0,028] | 5 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B11: convolucional temporal: **empate o no concluye**
- B12: GRU bidireccional: **empate o no concluye**

## Jugadores «lejos de la jugada» (sin voto; parámetro 44.38, suavizado 13)

### Etiquetas: flag

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,405 | 0,364–0,442 | – | – | 2853 / 3061 | 0,804 |
| como el ATD | main | 0,503 | 0,447–0,557 | +0,098 [+0,086 a +0,109] | 7 de 7 | 1816 / 3061 | 0,859 |
| como el ATD | B11: convolucional temporal | 0,591 | 0,517–0,674 | +0,186 [+0,173 a +0,199] | 7 de 7 | 2019 / 3061 | 0,888 |
| como el ATD | B12: GRU bidireccional | 0,561 | 0,500–0,610 | +0,156 [+0,144 a +0,169] | 7 de 7 | 1883 / 3061 | 0,883 |
| como el ATD | elegida dejando un partido fuera | 0,591 | – | +0,186 | – | 2019 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,433 | 0,405–0,473 | – | – | 2822 / 3061 | 0,818 |
| como el ATD, sin bloques | main | 0,517 | 0,462–0,584 | +0,085 [+0,073 a +0,095] | 7 de 7 | 1766 / 3061 | 0,868 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,606 | 0,530–0,693 | +0,173 [+0,160 a +0,185] | 7 de 7 | 2028 / 3061 | 0,896 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,573 | 0,514–0,628 | +0,141 [+0,128 a +0,153] | 7 de 7 | 1913 / 3061 | 0,888 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,606 | – | +0,173 | – | 2028 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,462 | 0,438–0,494 | – | – | 2853 / 1736 | 0,822 |
| como el ATD | main | 0,703 | 0,616–0,736 | +0,241 [+0,227 a +0,255] | 7 de 7 | 1816 / 1736 | 0,891 |
| como el ATD | B11: convolucional temporal | 0,734 | 0,671–0,791 | +0,272 [+0,258 a +0,285] | 7 de 7 | 2019 / 1736 | 0,915 |
| como el ATD | B12: GRU bidireccional | 0,744 | 0,700–0,777 | +0,282 [+0,267 a +0,295] | 7 de 7 | 1883 / 1736 | 0,915 |
| como el ATD | elegida dejando un partido fuera | 0,744 | – | +0,282 | – | 1883 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,492 | 0,469–0,524 | – | – | 2822 / 1736 | 0,838 |
| como el ATD, sin bloques | main | 0,737 | 0,682–0,775 | +0,245 [+0,232 a +0,258] | 7 de 7 | 1766 / 1736 | 0,906 |
| como el ATD, sin bloques | B11: convolucional temporal | 0,747 | 0,703–0,790 | +0,256 [+0,242 a +0,268] | 7 de 7 | 2028 / 1736 | 0,922 |
| como el ATD, sin bloques | B12: GRU bidireccional | 0,759 | 0,731–0,786 | +0,267 [+0,253 a +0,281] | 7 de 7 | 1913 / 1736 | 0,921 |
| como el ATD, sin bloques | elegida dejando un partido fuera | 0,759 | – | +0,267 | – | 1913 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- main: **gana**
- B11: convolucional temporal: **gana**
- B12: GRU bidireccional: **gana**

### Frente a la versión de main («main»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | B11: convolucional temporal | +0,088 [+0,077 a +0,100] | 7 de 7 |
| flag | como el ATD | B12: GRU bidireccional | +0,058 [+0,048 a +0,069] | 7 de 7 |
| flag | como el ATD, sin bloques | B11: convolucional temporal | +0,089 [+0,077 a +0,100] | 7 de 7 |
| flag | como el ATD, sin bloques | B12: GRU bidireccional | +0,056 [+0,047 a +0,066] | 7 de 7 |
| control | como el ATD | B11: convolucional temporal | +0,031 [+0,018 a +0,043] | 6 de 7 |
| control | como el ATD | B12: GRU bidireccional | +0,041 [+0,029 a +0,052] | 7 de 7 |
| control | como el ATD, sin bloques | B11: convolucional temporal | +0,010 [-0,002 a +0,022] | 5 de 7 |
| control | como el ATD, sin bloques | B12: GRU bidireccional | +0,022 [+0,010 a +0,033] | 6 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- B11: convolucional temporal: **empate o no concluye**
- B12: GRU bidireccional: **empate o no concluye**

