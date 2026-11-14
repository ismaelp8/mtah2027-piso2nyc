# Harness de la DFL: primera medida del esqueleto del pipeline · 2026-11-14 · Claude (sesión de Ismael)

> Primera ejecución del harness (`validation/harness/`) con el esqueleto del pipeline (`possession/`).
> Solo agregados. Cada afirmación lleva **[medido]**, **[inferencia]** o **[sin verificar]**. Los
> criterios (dos convenciones, tres condiciones, la regla de §5.8) estaban escritos en
> `docs/PLAN_ENTREGA.md` §4 antes de ejecutarlo.

**En pocas líneas:**

1. **El harness funciona.** Puntúa los 7 partidos en unos 30 s, dos ejecuciones dan la misma salida, y su
   `spellF1` coincide con el del scorer oficial. [medido]
2. **Quién gana depende de la convención de las etiquetas.** [medido] Con el `D` copiado de las etiquetas
   y la evidencia del jugador más cercano:
   - con las etiquetas corregidas por control, el Viterbi con coste 25 gana al voto por mayoría del
     baseline en las tres condiciones (+0,106, +0,115 y +0,126) y en los 7 partidos;
   - con el flag tal cual, empata o pierde por poco (+0,020, −0,028 y −0,022).
3. **Con la regla de §5.8 no gana ninguna versión:** la diferencia tiene que mantenerse con las dos
   convenciones, y no se mantiene. [medido]
4. **El coste 25 es el más robusto de los cuatro probados:** nunca pierde por más de 0,03 y gana más de
   0,10 con una de las dos convenciones. [medido] No está ajustado: elegir el coste es el trabajo del
   decodificador, con sus candidatos escritos antes.
5. **La convención de la GT del reto, que sigue sin medir, decide qué decodificador conviene.**
   [inferencia] Es el mayor riesgo abierto.
6. **La ventaja con las etiquetas de control está inflada por construcción.** [inferencia] Esas etiquetas
   son el flag filtrado con una regla de proximidad (el más cercano a 1 m durante 12 frames, o dos
   toques), y lo que se mide es proximidad con un coste por cambiar. Se parecen. El flag, donde el Viterbi
   no gana, es el mismo tipo de etiqueta que la GT del reto.

- **Código:** `validation/harness/dfl.py` y `puntuar.py`; las piezas son las de `possession/`.
- **Datos:** los 7 partidos de la Bundesliga (Bassek et al., 2025, CC BY 4.0), sobre la caché del
  experimento 0. Nada del partido.
- **Comando:** `python validation/harness/puntuar.py` (bootstrap de 1.000 remuestreos, semilla fija).

## 1. Con qué se mide

[medido] Los 7 partidos juntos.

| etiquetas | posesiones | frames `D` |
|---|---|---|
| flag (cambia en el primer toque) | 3.061 | 44,8 % |
| control ("C0-12 o dos toques") | 1.736 | 44,8 % |

| balón | visible en los frames de juego |
|---|---|
| limpio | 98,7 % |
| huecos | 58,3 % |
| huecos y suavizado | 58,3 % |

- **Versiones:** el control es el baseline oficial (jugador más cercano y voto por mayoría de ±50
  frames). Las demás son el pipeline con la evidencia del jugador más cercano y el Viterbi con cuatro
  costes de cambio.
- **`D`:** copiado de las etiquetas en todas, el control incluido.

## 2. Resultados

[medido] `spellF1` oficial. «Frente al control» lleva el intervalo del 5 al 95 % de un bootstrap pareado
sobre las posesiones reales.

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control | gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| limpio | control: voto ±50 | 0,524 | 0,483–0,573 | – | – | 2.726 / 1.736 |
| limpio | Viterbi, coste 12 | 0,470 | 0,428–0,509 | −0,054 [−0,061 a −0,047] | 1 de 7 | 3.079 / 1.736 |
| limpio | Viterbi, coste 25 (v0) | 0,629 | 0,604–0,649 | +0,106 [+0,097 a +0,114] | 7 de 7 | 1.871 / 1.736 |
| limpio | Viterbi, coste 50 | 0,635 | 0,576–0,675 | +0,112 [+0,096 a +0,127] | 7 de 7 | 1.297 / 1.736 |
| limpio | Viterbi, coste 100 | 0,545 | 0,480–0,590 | +0,022 [+0,000 a +0,042] | 5 de 7 | 969 / 1.736 |
| huecos | control: voto ±50 | 0,472 | 0,456–0,519 | – | – | 2.848 / 1.736 |
| huecos | Viterbi, coste 12 | 0,516 | 0,497–0,556 | +0,044 [+0,032 a +0,055] | 7 de 7 | 1.979 / 1.736 |
| huecos | Viterbi, coste 25 (v0) | 0,588 | 0,565–0,626 | +0,115 [+0,099 a +0,130] | 7 de 7 | 1.371 / 1.736 |
| huecos | Viterbi, coste 50 | 0,562 | 0,511–0,614 | +0,090 [+0,070 a +0,108] | 7 de 7 | 1.059 / 1.736 |
| huecos | Viterbi, coste 100 | 0,480 | 0,426–0,520 | +0,008 [−0,015 a +0,030] | 5 de 7 | 839 / 1.736 |
| huecos y suavizado | control: voto ±50 | 0,448 | 0,422–0,515 | – | – | 2.944 / 1.736 |
| huecos y suavizado | Viterbi, coste 12 | 0,484 | 0,460–0,529 | +0,036 [+0,025 a +0,047] | 6 de 7 | 2.088 / 1.736 |
| huecos y suavizado | Viterbi, coste 25 (v0) | 0,574 | 0,545–0,607 | +0,126 [+0,111 a +0,141] | 7 de 7 | 1.382 / 1.736 |
| huecos y suavizado | Viterbi, coste 50 | 0,543 | 0,491–0,584 | +0,095 [+0,075 a +0,113] | 7 de 7 | 1.049 / 1.736 |
| huecos y suavizado | Viterbi, coste 100 | 0,470 | 0,399–0,520 | +0,022 [−0,000 a +0,043] | 5 de 7 | 835 / 1.736 |

### Etiquetas: flag

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control | gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| limpio | control: voto ±50 | 0,454 | 0,419–0,494 | – | – | 2.726 / 3.061 |
| limpio | Viterbi, coste 12 | 0,452 | 0,427–0,483 | −0,002 [−0,010 a +0,006] | 3 de 7 | 3.079 / 3.061 |
| limpio | Viterbi, coste 25 (v0) | 0,474 | 0,435–0,526 | +0,020 [+0,012 a +0,027] | 6 de 7 | 1.871 / 3.061 |
| limpio | Viterbi, coste 50 | 0,399 | 0,335–0,447 | −0,056 [−0,068 a −0,044] | 0 de 7 | 1.297 / 3.061 |
| limpio | Viterbi, coste 100 | 0,314 | 0,250–0,365 | −0,140 [−0,155 a −0,127] | 0 de 7 | 969 / 3.061 |
| huecos | control: voto ±50 | 0,409 | 0,376–0,439 | – | – | 2.848 / 3.061 |
| huecos | Viterbi, coste 12 | 0,398 | 0,366–0,441 | −0,011 [−0,020 a −0,001] | 2 de 7 | 1.979 / 3.061 |
| huecos | Viterbi, coste 25 (v0) | 0,381 | 0,337–0,438 | −0,028 [−0,039 a −0,018] | 1 de 7 | 1.371 / 3.061 |
| huecos | Viterbi, coste 50 | 0,330 | 0,273–0,378 | −0,079 [−0,092 a −0,066] | 0 de 7 | 1.059 / 3.061 |
| huecos | Viterbi, coste 100 | 0,263 | 0,209–0,305 | −0,146 [−0,161 a −0,132] | 0 de 7 | 839 / 3.061 |
| huecos y suavizado | control: voto ±50 | 0,393 | 0,356–0,420 | – | – | 2.944 / 3.061 |
| huecos y suavizado | Viterbi, coste 12 | 0,381 | 0,350–0,424 | −0,012 [−0,021 a −0,003] | 2 de 7 | 2.088 / 3.061 |
| huecos y suavizado | Viterbi, coste 25 (v0) | 0,372 | 0,325–0,433 | −0,022 [−0,032 a −0,011] | 1 de 7 | 1.382 / 3.061 |
| huecos y suavizado | Viterbi, coste 50 | 0,320 | 0,270–0,362 | −0,073 [−0,085 a −0,060] | 0 de 7 | 1.049 / 3.061 |
| huecos y suavizado | Viterbi, coste 100 | 0,259 | 0,202–0,293 | −0,135 [−0,149 a −0,121] | 0 de 7 | 835 / 3.061 |

### El coste elegido dejando un partido fuera

[medido] Para cada partido se elige el coste que más saca en los otros seis y se puntúa en ese.

| etiquetas | limpio | huecos | huecos y suavizado |
|---|---|---|---|
| control | 0,628 (+0,105) | 0,588 (+0,115) | 0,574 (+0,126) |
| flag | 0,474 (+0,020) | 0,398 (−0,011) | 0,381 (−0,012) |

### La regla de §5.8

[medido] Ninguna de las cuatro versiones gana: **empate o no concluye** en las cuatro. Con las etiquetas
de control, los costes 25 y 50 cumplen la regla en las tres condiciones; con el flag, ninguno.

## 3. Lectura

- **El número de posesiones lo explica casi todo.** [medido] El voto de ±50 frames predice entre 2.700 y
  2.950 posesiones, cerca de las 3.061 del flag. El Viterbi con coste 25 predice entre 1.400 y 1.900,
  cerca de las 1.736 de control. Cada versión acierta más con la convención cuyo número de posesiones se
  parece al suyo.
- **El coste que conviene cambia con la convención.** [medido] Con control, 25 o 50; con el flag, 12 o
  25. El 25 es el único que no pierde por más de 0,03 en ninguna de las seis combinaciones.
- **Con huecos, todos bajan.** [medido] El control pierde 0,05 y el Viterbi con coste 25, entre 0,04 y
  0,09. El suavizado quita otros 0,01–0,02. La evidencia del jugador más cercano no opina sin balón, y el
  41 % de los frames de juego se queda sin evidencia.
- **Qué implica para el reto.** [inferencia] Si la GT del reto sigue la lectura de control, que es la
  decisión del 12/11, un decodificador con coste de cambio mejora al baseline antes de tocar nada más;
  cuánto, no se sabe, porque el +0,10 está inflado (punto siguiente). Si sigue la del primer toque, no
  mejora, y habría que ajustarlo hacia más posesiones. Medir la convención, o preguntársela a la
  organización, vale más que cualquier ajuste del coste.

## 4. Lo que esta medida no dice

- **Cuánto se gana de verdad con las etiquetas de control.** Esas etiquetas salen del flag filtrado con
  una regla de proximidad sobre el tracking limpio: el más cercano a 1 m o menos durante 12 frames, o dos
  toques seguidos (`validation/experimento1/correccion.py`). Lo que se mide aquí es proximidad con un
  coste por cambiar de equipo: se parece a la regla que fabricó las etiquetas, así que parte del +0,10
  viene de ahí. [inferencia]
  - La referencia sin esa circularidad son los eventos humanos de la DFL (experimento 1). El harness
    todavía no puntúa contra ellos.
  - Cualquier candidato que use retención por proximidad ganará con las etiquetas de control por
    construcción. Solo cuenta lo que aguante también con el flag.
- **Nada sobre el `D`:** va copiado de las etiquetas. Los números no se pueden comparar con el 0,2433
  del baseline en el partido, que pone su propio `D`.
- **Nada sobre el partido:** la degradación es provisional y los jugadores están sin degradar.
- **No elige el coste:** son cuatro valores de prueba, sin candidatos escritos antes.

## 5. Sin verificar

- Que la degradación (huecos dirigidos a las disputas y media móvil de 25 frames) imite al balón del ATD.
  Lo dirá la medida del balón del ATD en todo el partido.
- Que el orden se mantenga cuando el `D` lo pongan las piezas y no las etiquetas.
