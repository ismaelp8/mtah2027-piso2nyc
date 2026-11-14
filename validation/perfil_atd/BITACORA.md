# Perfil del ATD · bitácora: cómo es el balón del ATD en todo el partido y si la degradación del harness lo imita

Es el paso 5 de `validation/PASOS.md` (duda D18) y el paso 1 de «Ismael» en `docs/PLAN_ENTREGA.md` §3.
Continúa la sección 9 de `validation/experimento2/BITACORA.md`.

## 1. Por qué (14/11/2026)

- **El harness de la DFL decide qué versión de cada pieza entra,** y su degradación del balón es
  provisional (`validation/harness/README.md`, «Límites»). Mientras no se compruebe contra el ATD, el
  orden entre evidencias de equipo no se da por bueno.
- **Qué se mide:** el balón y los jugadores del ATD en todos los frames evaluados, solo con el tracking.
  No usa etiquetas ni la ventana pública.
- **Para qué sirve y para qué no:** de aquí salen solo los parámetros de la degradación de la DFL
  (`validation/harness/dfl.py`). No sale ningún parámetro, constante ni etiqueta del pipeline.
- **Quién lo ejecuta:** una persona, una vez, en local (regla nº 1). Claude solo ve la salida.

## 2. El problema que hay que resolver antes: el partido entero no tiene etiquetas

- **El 41 % de `DATA.md` es de los frames evaluados,** con el juego y el balón muerto mezclados.
  `dfl.py` aplica ese 41 % (`OBJETIVO`) solo a los frames **vivos** de la DFL y, además, tapa el balón en
  todos los `D`. [medido, leyendo el código]
- **No cuadra con lo poco que sabemos:**
  - en la DFL el 44,8 % de los frames es `D`: tapándolos todos y quitando el 41 % del resto, el balón se
    ve en el 32 % de los frames (0,552 × 0,583, con las dos cifras de
    `validation/resultados/2026-11-14_harness_dfl.md`), frente al 59,3 % del ATD; [inferencia: es una
    cuenta, falta medirlo con el perfil]
  - en la ventana pública, el balón se ve en el 93,5 % de los frames de juego (experimento 2). [medido]
- **[inferencia]** El ATD pierde el balón sobre todo cuando está muerto o fuera, y en juego falta bastante
  menos del 41 %. Si es así, la condición «huecos» del harness es demasiado severa. Cuánto falta en juego
  es lo primero que tiene que decir esta medida.
- **Cómo se separa sin etiquetas:** por la duración del hueco. Un hueco corto es una oclusión o un balón
  aéreo; uno largo, casi siempre, balón muerto o fuera de plano. [inferencia, sin verificar] Por eso se dan
  tres cortes (2, 5 y 15 s) y las tres severidades del harness salen de ellos (regla R1).
- **Las medidas del experimento 2 eran «por minuto vivo»,** con la GT. Aquí no hay GT, así que todo se da
  con dos denominadores que se calculan igual en el ATD y en la DFL:
  - **todo el balón visible;**
  - **sin el balón parado:** se quitan los tramos en que el balón no sale de un radio de 2 m durante 3 s o
    más (la definición del diagnóstico del 12/11). El ATD ve el balón colocado antes de un saque; el
    harness lo tapa.

  Las referencias de la DFL (3,5 toques, 10,4 controles, 0,9 cm) se vuelven a calcular con estos
  denominadores: las antiguas no se comparan.

## 3. Cómo se organiza el código

- **La medida es una función pura,** `perfil(trk) -> dict`, sin ficheros, en `validation/perfil_atd/perfil.py`.
  Recibe un `Tracking` y devuelve solo recuentos y cuantiles.
- **El mismo código mide las dos cosas:**
  - `validation/partido/perfil_atd.py` la llama con el ATD leído por `possession.tracking.from_files`, el
    lector de `from_atd` y del pipeline (lo ejecuta Ismael);
  - `validation/perfil_atd/perfil_dfl.py` la llama con la DFL degradada como en `validation/harness/dfl.py`,
    con sus constantes como parámetros (lo ejecuta Claude). Con los valores del harness da exactamente
    el tracking de `dfl.tracking_de`, y el script lo comprueba antes de medir.
- **Toques, controles y temblor** son los de `validation/experimento2/instrumento.py`, con sus umbrales
  (`toques_por_tramos`, `retenciones` Ret-12, `temblor`). `instrumento.medir` no se usa: necesita etiquetas.
- **Prueba:** `validation/scripts/prueba_perfil_atd.py`, con un `Tracking` inventado de resultado conocido y
  la misma guarda que `prueba_pipeline.py` (abrir un fichero es un error).

## 4. Qué imprime (fijado antes de medir, 14/11)

**Garantías de la salida,** para que se pueda pegar a Claude:

- las dos partes siempre juntas: nada por parte, por minuto, por jugada ni por frame;
- solo recuentos, porcentajes y cuantiles 10, 50 y 90. Ni mínimos ni máximos;
- una celda con menos de 5 casos se imprime como «< 5»;
- los `SET PIECES`, todos juntos;
- si falla, imprime solo el tipo de error y la línea del código.

«Hueco» es una racha de frames evaluados seguidos sin balón; «racha», con balón. «Primaria» quiere decir
que entra en la regla de la sección 5; «descriptiva», que se apunta y no decide.

| nº | agregado | intervalos | para qué | |
|---|---|---|---|---|
| 0 | frames evaluados y frames con balón | – | comprobar que se lee lo mismo que el 12/11 (158.857 y 94.214) | control |
| 1 | huecos y rachas con balón: cuántos, y cuántos frames suman | 5 duraciones: < 0,5 s, 0,5–2 s, 2–5 s, 5–15 s, > 15 s | cuánto falta en juego (`OBJETIVO`) y cuánto duran las pérdidas (`MEDIA_BLOQUE`) | primaria |
| 2 | salto del balón entre el último punto visto y el primero tras el hueco | las 5 duraciones × 3 distancias: < 3 m, 3–15 m, ≥ 15 m | distinguir la oclusión del pase aéreo | descriptiva |
| 3a | disputas (un jugador de cada equipo a 3 m o menos): % de los frames con balón que lo son | los dos denominadores | dónde se pierde (`DISPUTAS`): si el ATD pierde el balón en las disputas, entre los frames con balón quedan menos | primaria |
| 3b | pérdidas por 1.000 frames con balón, según lo que había en el último frame visto: dentro o fuera de una disputa, y por densidad y zona | huecos de hasta 5 s y de más de 5 s; 3 densidades (0–1, 2–3, 4 o más jugadores a 5 m) × 3 zonas (a 5 m o menos de una línea, tercio central, tercios de fondo) | lo mismo, con más detalle | descriptiva |
| 4a | temblor del balón (mediana de la segunda diferencia), toques con equipo por minuto (umbral de 3 m/s) y controles Ret-12 por minuto | los dos denominadores | cuánto está suavizado (`SUAVIZADO`) | primaria |
| 4b | toques por minuto con umbral de 1 y de 2 m/s; autocorrelación de la velocidad del balón a 5, 12 y 25 frames; % de ternas de frames con la segunda diferencia por debajo de 1 mm y de 5 mm | los dos denominadores | si un detector de toques recalibrado vería algo; suavizado frente a interpolado | descriptiva |
| 5 | distancia del balón al jugador más cercano: % de los frames con balón a 1 m, 1,5 m y 3 m o menos, y a más de 5 m; % con el rival al menos 1 m más lejos; cambios del equipo más cercano por minuto | los dos denominadores | si la proximidad se comporta igual: es lo que usan los candidatos de evidencia de equipo | primaria |
| 6 | pares de frames seguidos a más de 40 m/s; rachas con balón de 1 o 2 frames; pares con la posición idéntica y duración de esas rachas | las rachas idénticas, en 4 duraciones: < 1 s, 1–5 s, 5–30 s, > 30 s | detecciones falsas y balón congelado (propuesta del experimento 0) | descriptiva |
| 7 | slots por equipo; jugadores localizados por frame y equipo; duración de los tramos continuos de un slot y tramos por minuto; temblor de los jugadores; saltos de un slot a más de 12 m/s por minuto | cuantiles 10, 50 y 90 | cómo degradar a los jugadores, si hace falta | solo si R5 no cuadra |
| 8 | % de frames con balón dentro de las ventanas `SET PIECES`, en los 10 s anteriores y en el resto | 3 tramos, todos los reinicios juntos | si el balón se ve durante el tiempo muerto | descriptiva |

**Lo que no se repite,** porque ya está medido en `validation/resultados/2026-11-12_balon_muerto_atd.md`: el
balón fuera de [0, 1] (4,2 % de los frames con balón) y los cuantiles del salto entre frames. Los tramos de
balón quieto solo se vuelven a calcular para el denominador `sin_parado` y como control. Tampoco se
repiten la columna de velocidad del ATD (`agregados_balon_reinicios.py`) ni el total de slots vistos por
frame (`agregados_jugadores.py`).

**El agregado 8 solo existe en el ATD:** la DFL no tiene Smart Tagging. Es un indicio, no una medida del
`D`: el Smart Tagging solo marca 59 reinicios.

**Placebo del 3b,** también descriptivo: las pérdidas por 1.000 frames en dos mitades de los frames con
balón repartidas al azar, con semilla fija. Si su cociente se aleja de 1 tanto como el de las disputas,
el 3b es ruido.

## 5. Cómo se leerá (fijado antes de medir, 14/11)

**Qué se compara.** El ATD con la DFL degradada, medidos con la misma función.

- «La DFL» son los 7 partidos juntos. Se apunta también el mínimo y el máximo por partido.
- Una medida que en la DFL varía entre partidos más que su propia tolerancia pasa a descriptiva: no
  distingue al ATD de un partido cualquiera.
- `V` son los frames con balón y `M(T)`, los frames sin balón que caen en huecos de `T` segundos o menos.

**Antes de que Ismael ejecute nada en el partido,** se mide en la DFL cómo se mueve cada medida primaria
al mover su parámetro (`s(T)` con `OBJETIVO`, las disputas con `DISPUTAS`, el temblor, los toques y los
controles con `SUAVIZADO`). La que no suba o baje de forma ordenada con su parámetro pasa a descriptiva, y
se apunta aquí antes de ver ningún número del ATD.

- **R0. Control.** Si los frames evaluados o los frames con balón no son 158.857 y 94.214, el lector no
  lee lo mismo que el del 12/11: se para y se busca por qué.
- **R1. Cuánto falta en juego: las tres severidades.**
  - `s(T) = M(T) / (V + M(T))`, con `T` = 2, 5 y 15 s. Son las severidades baja, media y alta.
  - En cada severidad, el `OBJETIVO` de la DFL es la `s(T)` del ATD con su propio corte. La media,
    `s(5 s)`, sustituye al 0,41 de hoy.
  - Cuadra si, en cada severidad, la `s(T)` de la DFL degradada con ese mismo corte queda a ±5 puntos de
    la del ATD.
- **R2. Cuánto duran las pérdidas.** En cada severidad, el reparto de los huecos de hasta su corte entre
  los intervalos que caben en él (hasta 2 s, dos; hasta 5 s, tres; hasta 15 s, cuatro).
  - Cuadra si cada intervalo queda a ±10 puntos.
  - Si no, en esa severidad los bloques dejan de ser geométricos de 1 s de media y su duración se sortea
    con el reparto medido en el ATD.
- **R3. Dónde se pierde.** Con el % de los frames con balón que son disputas (3a), sin el balón parado y
  en la severidad media.
  - `DISPUTAS` toma, de 0, 25, 50, 75 y 100 %, el valor que deje ese porcentaje más cerca del del ATD.
  - Cuadra si queda a ±3 puntos.
  - Límite: si al ATD le faltan jugadores, ve menos disputas de las que hay. Por eso R5 se mira después.
- **R4. Cuánto está suavizado.** Sin el balón parado y en la severidad media.
  - Se mide la DFL con medias móviles de 1, 5, 11, 25 y 51 frames.
  - `SUAVIZADO` toma la que dé la menor suma de |ln(ATD / DFL)| del temblor, los toques y los controles
    por minuto. Una tasa por debajo de 0,5 por minuto cuenta como 0,5.
  - Cuadra si las tres quedan entre la mitad y el doble.
  - Si no cuadra con ninguna, el balón del ATD no es un balón suavizado con una media móvil. Entonces
    nada que dependa de la velocidad del balón se decide en el harness.
  - El 4b solo sirve para apuntar, como inferencia, si parece suavizado o interpolado.
- **R5. La proximidad.** Con la degradación que salga de R1–R4, sin el balón parado y en la severidad
  media.
  - Cuadra si los tres porcentajes de distancia (1 m, 1,5 m y 3 m) quedan a ±10 puntos y los cambios del
    equipo más cercano por minuto, entre la mitad y el doble.
  - Se apunta también en las severidades baja y alta. Si allí no cuadra, se dice, pero no cambia nada.
- **R6. Los jugadores: solo si R5 no cuadra.** Hoy el harness no los degrada. Se prueban dos cambios,
  en este orden, y se vuelve a mirar R5 después de cada uno:
  1. **Ruido:** gaussiano de 2, 5, 10 o 25 cm, el que deje el temblor de los jugadores más cerca del del
     ATD.
  2. **Los que faltan:** quitar slots a rachas hasta igualar la media de localizados por equipo (±0,5) y
     la mediana de la duración de los tramos (entre la mitad y el doble).

  Si R5 cuadra sin tocar a los jugadores, el agregado 7 se apunta y no cambia nada.
- **R7. Qué puede decidir el harness después.**

  | resultado | qué decide |
  |---|---|
  | R1, R2, R3 y R5 cuadran, con o sin los cambios de R6 | el orden entre evidencias de equipo por proximidad |
  | además cuadra R4 | también lo que use la velocidad del balón |
  | alguno no cuadra, con los cambios ya aplicados | sigue en «todavía no», diciendo cuál |

- **R8. Un cambio de la degradación cambia los números de todos.** Se anuncia con fecha en
  `docs/PLAN_ENTREGA.md` §4 y en `validation/harness/README.md`, y se vuelve a ejecutar la tabla de
  referencia.
- **R9. Los parámetros de la degradación salen de esta regla,** nunca de qué versión del pipeline puntúa
  mejor.

**Límite de las tres severidades:** las tres dan por hecho que un hueco largo es balón muerto. Ninguna
cubre el caso contrario, que el ATD pierda el balón mucho rato con el juego vivo.

**Propuesta para el paso 3, que decide Ismael:**

- las tres condiciones que votan en la regla de §5.8 pasan a ser las tres severidades, todas con el
  suavizado que salga de R4;
- «limpio» y la condición de hoy (41 % de los frames vivos) se siguen puntuando como referencias, sin
  voto. La de hoy cubre el caso contrario del límite de arriba.

## 6. Dudas para Ismael antes de escribir el script

Por defecto, las tres quedan **fuera**:

1. **El tramo antes del saque de la 2ª parte** (2.934 frames, `D` según el FAQ): el % de frames con balón.
   Es un solo número, pero de un tramo concreto del partido.
2. **La ventana pública:** el % de frames con balón en los `D` de la GT pública frente a los de juego. Es
   la única medida con etiquetas de si el ATD ve el balón muerto, pero serviría para fijar un parámetro
   del harness.
3. **Las dos partes por separado.**

**Ismael dio el sí a las secciones 4 y 5 el 14/11, sin tocar estas dudas: las tres quedan fuera.**

## 7. Cambios antes de medir, tras el sí de Ismael (14/11)

Salieron al escribir el código y al hacer la medida en seco. Ninguno se ha hecho viendo un número del ATD:
nadie ha ejecutado todavía `validation/partido/perfil_atd.py`. Necesitan otro sí de Ismael antes de que lo
ejecute.

### 7.1 Precisiones

- **R1 y R2 van con el denominador `sin_parado`,** como R3, R4 y R5: sin los frames con balón de los tramos
  de balón parado ni los huecos que caen dentro de ellos. Es el motivo de la sección 2: el ATD ve el balón
  colocado antes de un reinicio y el harness lo tapa, así que con `todo` ese balón engordaría el
  denominador del ATD y no el de la DFL. La versión `todo` se imprime igual, pero no decide.
- **R0 tiene un control más:** los tramos de balón parado (2 m, 3 s o más) tienen que ser 59 y sumar
  7.336 frames, como en el diagnóstico del 12/11 (`validation/resultados/2026-11-12_balon_muerto_atd.md`,
  radio 2,0 m). Es el mismo algoritmo, `still_runs`, y la prueba lo compara con él en 20 balones al azar.
- **«Varía entre partidos más que su tolerancia»** quiere decir que algún partido de la DFL queda fuera de
  la tolerancia alrededor de los 7 juntos, en la referencia de la medida en seco. Estaba así en
  `perfil_dfl.py` antes de ejecutarlo.

### 7.2 Medida en seco en la DFL

[medido] `python validation/perfil_atd/perfil_dfl.py --seco`, los 7 partidos, unos 110 s, con el código
definitivo (tras la revisión de la sección 7.6: sin los huecos de los bordes de cada tramo). Cada barrido
mueve un parámetro desde la referencia (`objetivo` 0,2, `disputas` 0,5, bloques de 25 frames, sin
suavizar). Cada celda da los 7 partidos juntos y, entre corchetes, el mínimo y el máximo por partido. «Parte
dirigida» es el % de los frames vivos que tapa la parte de las disputas y los balones altos antes de
completar con bloques. Antes de medir, el script comprueba que la degradación parametrizada reproduce
las tres condiciones del harness.

**`objetivo`, con `disputas` 0,5**

| objetivo | s_baja | s_media | s_alta | parte dirigida (% de los vivos) |
|---|---|---|---|---|
| 0 | 6,44 [5,40–7,80] | 13,99 [11,05–16,04] | 24,56 [21,48–28,13] | 22,4 |
| 0.1 | 6,44 [5,40–7,80] | 13,99 [11,05–16,04] | 24,56 [21,48–28,13] | 22,4 |
| 0.2 | 7,00 [5,95–8,22] | 14,86 [13,25–16,04] | 25,46 [23,72–28,13] | 22,4 |
| 0.3 | 11,33 [7,55–14,63] | 20,89 [17,07–23,38] | 31,71 [27,83–34,03] | 22,4 |
| 0.41 | 17,52 [14,70–20,55] | 30,47 [27,40–32,49] | 41,48 [37,36–43,49] | 22,4 |
| ¿ordenada? | no | no | no | |

**`objetivo`, con `disputas` 0 (sin parte dirigida)**

| objetivo | s_baja | s_media | s_alta | parte dirigida (% de los vivos) |
|---|---|---|---|---|
| 0 | 0,00 [0,00–0,00] | 0,67 [0,22–1,01] | 9,05 [7,17–11,11] | 0,0 |
| 0.1 | 5,99 [4,78–6,66] | 9,79 [9,37–10,44] | 17,85 [16,42–19,84] | 0,0 |
| 0.2 | 11,40 [10,61–12,46] | 18,58 [17,96–19,16] | 26,41 [25,58–27,84] | 0,0 |
| 0.3 | 16,69 [15,48–18,14] | 27,23 [26,63–27,87] | 34,95 [34,38–35,37] | 0,0 |
| 0.41 | 22,18 [20,56–23,73] | 36,11 [35,57–36,60] | 44,37 [43,87–45,01] | 0,0 |
| ¿ordenada? | sí | sí | sí | |

**`disputas`, con `objetivo` 0,2** (con `objetivo` 0,1 sale lo mismo: 21,39; 18,31; 13,86; 8,48 y 0,00)

| disputas | disputa_pct | parte dirigida (% de los vivos) |
|---|---|---|
| 0 | 21,28 [17,91–26,49] | 0,0 |
| 0.25 | 18,32 [14,90–23,00] | 10,6 |
| 0.5 | 13,87 [11,60–16,91] | 22,4 |
| 0.75 | 8,48 [5,34–11,75] | 33,1 |
| 1 | 0,00 [0,00–0,00] | 44,2 |
| ¿ordenada? | sí | |

**`suavizado`** (frames de la media móvil del balón)

| suavizado | temblor_cm | toques_por_min | controles_por_min |
|---|---|---|---|
| 1 | 2,24 [2,24–3,16] | 36,49 [33,36–43,88] | 14,69 [13,49–16,31] |
| 5 | 0,82 [0,72–1,08] | 32,06 [28,40–40,73] | 14,56 [13,42–16,33] |
| 11 | 0,86 [0,78–1,04] | 18,59 [16,99–22,88] | 14,01 [12,93–15,87] |
| 25 | 0,95 [0,88–1,09] | 3,84 [3,22–4,50] | 11,46 [10,75–13,17] |
| 51 | 0,65 [0,62–0,68] | 0,34 [0,14–0,58] | 6,78 [6,30–7,14] |
| ¿ordenada? | no | sí | sí |

El temblor sin suavizar sale en valores discretos (2,24 y 3,16 cm son √5 y √10 cm): las posiciones de la
DFL vienen redondeadas al centímetro. [inferencia]

**Tolerancia por partido, en la referencia:** todas las medidas primarias quedan dentro en los 7 partidos,
salvo el % de disputas, con un partido fuera: 13,87 [11,60–16,91] y ±3 puntos de tolerancia. Las demás:

| medida | 7 juntos [mín–máx] | tolerancia |
|---|---|---|
| s_baja / s_media / s_alta | 7,00 [5,95–8,22] / 14,86 [13,25–16,04] / 25,46 [23,72–28,13] | ±5 puntos |
| reparto de los huecos (los 9 intervalos de las tres severidades) | el que más se separa: 10,92 [3,96–15,09] | ±10 puntos |
| temblor_cm / toques_por_min / controles_por_min | 2,24 [2,24–3,16] / 36,49 [33,36–43,88] / 14,69 [13,49–16,31] | de ×½ a ×2 |
| a 1 / 1,5 / 3 m o menos (%) | 39,58 [37,07–42,13] / 53,09 [51,16–55,90] / 71,53 [70,00–73,15] | ±10 puntos |
| cambios del equipo más cercano por minuto | 29,83 [24,89–33,20] | de ×½ a ×2 |

**Jugadores sin degradar ni barajar los slots** (7 juntos): 11,0 y 10,8 localizados por frame (local y
visitante), tramos de slot de 2.765 s de mediana (cada slot es una persona) y 1,0 cm de temblor.

### 7.3 Qué cambia

1. **`s(T)` sigue siendo primaria, pero `OBJETIVO` tiene un suelo.**
   - Sin parte dirigida (`DISPUTAS` = 0), `s(T)` sube de forma ordenada con `OBJETIVO` en las tres
     severidades. [medido]
   - Con `DISPUTAS` = 0,5 no se mueve por debajo de lo que ya tapa la parte dirigida. Es un defecto del
     parámetro, no de la medida. La parte dirigida sola tapa el 0; 10,6; 22,4; 33,1 y 44,2 % de los frames
     vivos con `DISPUTAS` 0; 0,25; 0,5; 0,75 y 1. [medido]
   - **Consecuencia:** con `DISPUTAS` = 0,5, la `s` media de la DFL no baja del 14 %. [medido] En la
     ventana pública, al ATD le faltaba el 6,5 % del balón en juego (experimento 2; es otra medida, con
     etiquetas). [medido] R1 y R3 no se pueden fijar por separado. [inferencia]
2. **El % de disputas pasa a descriptivo.**
   - En la referencia, un partido queda a 3,04 puntos de los 7 juntos, y la tolerancia es ±3. [medido]
   - La dispersión es de la DFL, no del parámetro: con `DISPUTAS` = 0 los partidos ya van del 17,9 al
     26,5 %, y los rangos de dos valores seguidos de `DISPUTAS` se solapan, salvo los de 0,75 y 1.
     [medido]
   - **Lo que le queda:** descartar los valores de `DISPUTAS` cuyo rango por partido no contiene el % del
     ATD, con margen (R3' de la sección 7.4).
3. **El temblor pasa a descriptivo.** No baja de forma ordenada con el suavizado (2,24; 0,82; 0,86; 0,95 y
   0,65 cm con 1, 5, 11, 25 y 51 frames). [medido] R4 se decide con los toques y los controles por minuto,
   que sí bajan en orden.
4. **Las pérdidas en disputa (3b) siguen siendo descriptivas, y para la degradación de hoy no informan.**
   - La degradación tapa episodios de disputa enteros, con 5 frames a cada lado. Así, el último frame
     visto antes de un hueco casi nunca es una disputa: en la referencia, 0,52 pérdidas por 1.000 frames
     en disputa frente a 4,86 fuera. [medido]
   - El placebo sí queda equilibrado: 4,26 y 4,28 por 1.000 frames en las dos mitades al azar. [medido]

### 7.4 La regla con estos cambios

Sustituye a R1, R3, R4 y R7 de la sección 5; lo demás sigue igual. Está también como código, escrito
antes de ver el ATD: `validation/perfil_atd/leer_atd.py`, que lee la salida del ATD y mide la DFL.

- **R1'. `OBJETIVO` se ajusta para cada valor de `DISPUTAS` (0; 0,25; 0,5; 0,75 y 1), en cada severidad.**
  - Es el `OBJETIVO` que deja la `s(T)` de la DFL igual a la del ATD, interpolando en una rejilla de 0 a
    0,5. Si la del ATD queda por debajo del suelo de ese `DISPUTAS`, `OBJETIVO` = 0.
  - Cuadra si la `s(T)` de la DFL con ese `OBJETIVO` queda a ±5 puntos de la del ATD.
  - **Una celda «< 5» del ATD es una cota, no un fallo.** Una `s(T)` suprimida vale como mucho lo que dan 4
    huecos de `T` segundos: `OBJETIVO` es el más bajo, y cuadra si la DFL no pasa de esa cota más 5
    puntos. En R2, un intervalo suprimido vale como mucho 4 huecos entre los que sí salen más esos 4.
- **R2,** como en la sección 5, con el `OBJETIVO` de R1' de cada severidad. El reparto es por número de
  huecos. Con pocos huecos en el ATD, la tolerancia crece con su ruido (R2', sección 7.7). R1' y R2 se
  juzgan juntos, con todos los `OBJETIVO` que cumplen R1' (R1''), y una celda también cuadra dentro del
  rango por partido ensanchado (R2''), las dos en la sección 7.8.
- **R3'. El % de disputas acota `DISPUTAS`; no lo ajusta.**
  - Cabe si queda dentro del rango por partido de la DFL, con el `OBJETIVO` de la severidad media,
    ensanchado a cada lado con toda su anchura (sección 7.9; antes, la mitad).
  - El margen es porque el ATD es otro partido, y el rango de 6 o 7 partidos no cubre con seguridad a uno
    nuevo (sección 7.5).
- **Queda un `DISPUTAS` si cuadran R1' y R2 en las severidades baja y media, y R3'.** La alta se apunta y
  no decide (sección 7.6).
- **R4'. `SUAVIZADO`,** como en R4 pero solo con los toques y los controles por minuto, sin el temblor. Se
  mide con el `DISPUTAS` que queda y más se parece al ATD (la distancia de la sección 7.8). Una tasa del ATD suprimida (menos de
  5 casos), con 10 minutos con balón o más, cuenta como el suelo de 0,5 por minuto.
- **R5,** con cada `DISPUTAS` que queda y el suavizado de R4', en la severidad media. El que no cuadra,
  sale. En la baja y en la alta se apunta y no decide, como decía la sección 5.
- **R7'.** El harness mide con todos los `DISPUTAS` que quedan tras R5. **Cambiado por decisión de Ismael
  el 14/11** (sección 8, punto 3): decide el que más se parece al ATD, y los demás solo vetan.

  | resultado | qué decide |
  |---|---|
  | queda al menos un `DISPUTAS` | el orden entre evidencias de equipo por proximidad |
  | además cuadra R4' | también lo que use la velocidad del balón |
  | quedan tras R1', R2 y R3', pero R5 no cuadra con ninguno | toca R6 (los jugadores) |
  | no queda ninguno | «todavía no»; en el paso 3 cambia la forma de tapar y se vuelve a leer con esta misma regla |

  Para el último caso, los candidatos son la ley de huecos del ATD (R2) y dos argumentos de
  `instrumento.mascara_dirigida` que hoy van fijos: `dilatar` (5 frames alrededor de cada disputa) y
  `aire` (balones a más de 1,5 m). No se construye nada antes de ver el ATD.
- **R6', si hace falta:** como R6, pero los tramos de slot del ATD se comparan con los de la DFL sin barajar,
  en los que cada slot es una persona (sección 7.6).
- **R0 para la lectura:** si no cuadra, `leer_atd.py` imprime R0 y no sigue.

### 7.5 Ensayo de la regla con la DFL (antes de medir)

**Cómo:** un partido de la DFL, degradado con parámetros conocidos, hace de ATD (con las celdas de menos
de 5 casos suprimidas, como el ATD) y los otros 6 hacen de DFL. La regla tiene que devolver los
parámetros plantados. Comando: `python validation/perfil_atd/leer_atd.py --ensayo PARTIDO objetivo
disputas suavizado`.

**Primer ensayo, con la primera versión de R3'** (rango sin margen y `DISPUTAS` filtrado solo por R3'):
J03WR9 con `objetivo` 0,3, `disputas` 0,25 y suavizado 25. [medido]

- Recupera el suavizado (25 frames) y, con `DISPUTAS` 0,25, un `OBJETIVO` de 0,30 a 0,33 según la
  severidad, con R1' y R2 cuadrando en las tres.
- **Pero R3' descarta el `DISPUTAS` verdadero:** el falso ATD tiene un 14,70 % de disputas, y el rango de
  los otros 6 con 0,25 va de 16,61 a 23,26. Se queda con 0,5 (12,66–17,65), con el que R2 no cuadra en la
  severidad alta.
- **Por qué** [inferencia]: el % de disputas depende del partido, no solo de la degradación. J03WR9 tiene
  menos disputas que los demás.
- **Qué cambia:** el margen de R3' y que R1' y R2 también filtran (sección 7.4). Con eso, de este ensayo
  solo quedaría el 0,25.

**Con la regla definitiva** (la de la sección 7.4, con los cambios de la 7.6), cuatro ensayos con otros
partidos y otros parámetros. [medido]

| partido que hace de ATD | plantado: `objetivo` · `disputas` · suavizado | `DISPUTAS` que quedan | `OBJETIVO` con el plantado (baja / media / alta) | suavizado elegido | R5 |
|---|---|---|---|---|---|
| J03WR9 | 0,3 · 0,25 · 25 | 0,25 y 0,5 | 0,326 / 0,313 / 0,303 | 25 | cuadra con los dos |
| J03WPY | 0,2 · 0 · 5 | 0 y 0,25 | 0,185 / 0,192 / 0,189 | 5 | cuadra con los dos |
| J03WMX | 0,15 · 0,5 · 11 | 0,5 | 0,203 / 0,201 / 0,238 | 5 | cuadra |
| J03WQQ | 0,41 · 0,75 · 51 | 0,75 | 0,499 / 0,445 / 0,419 | 51 | cuadra |

- **El `DISPUTAS` plantado queda siempre:** solo en 2 de los 4 ensayos y con un vecino en los otros 2.
  [medido] Con la severidad alta decidiendo (la versión anterior), J03WR9 se quedaba solo con el 0,25;
  ahora el 0,5 también queda, porque solo fallaba allí.
- **El harness mide con todos los que quedan,** así que en esos dos casos el vecino entra como eje de
  robustez, igual que las dos convenciones de etiquetas.
- **`OBJETIVO` sale a ±0,03 del plantado cuando está por encima del suelo y el suavizado no pasa de 25
  frames.** [medido]
  - En J03WMX el plantado (0,15) queda por debajo del suelo de `DISPUTAS` 0,5: la parte dirigida ya tapa
    más, así que la degradación es la misma que con el suelo. La regla devuelve ~0,20, donde los bloques
    empiezan a sumar. [inferencia]
  - Con suavizado 51 (J03WQQ) sale hasta 0,09 por encima, en la severidad baja. R1' se ajusta sin
    suavizar, y un suavizado tan fuerte deja el balón casi quieto y crea tramos de balón parado.
    [inferencia] R1' sigue cuadrando: la `s(T)` es la misma, lo que cambia es con qué `OBJETIVO` se llega.
- **El suavizado acierta en 3 de 4:** en J03WMX elige 5 en vez de 11, casi empatados (distancias 0,387 y
  0,412). [medido] Los toques por minuto también dependen del partido. [inferencia] Sí separa el suavizado
  de ~1 s (25 frames) del ligero (5 u 11), que es lo que importa para el detector de toques.
- **R5 cuadra en los 4,** también en las severidades baja y alta, que se apuntan. [medido]
- **Lo que el ensayo no puede ver:** el falso ATD es la DFL, que tapa todo el `D`. Si el ATD pierde el balón
  de otra manera (por ejemplo, en huecos largos con el juego vivo), el ensayo no lo cubre. [inferencia]
- **Un fallo que habría pasado con el ATD,** arreglado antes de medir: con suavizado 51, el falso ATD tiene
  menos de 5 toques en todo el partido. La tasa sale suprimida («< 5») y la regla se rompía. Ahora un
  recuento suprimido con 10 minutos con balón o más cuenta como el suelo de R4 (0,5 por minuto), porque
  es menos que eso.

### 7.6 Cambios tras la revisión del código (14/11, antes de medir)

Una revisión adversarial, con cinco enfoques y un verificador por enfoque, revisó el código y la regla:
regla nº 1, código frente a bitácora, reimplementación independiente, paridad ATD/DFL y escala real. Cambia
esto:

1. **Bordes de los tramos evaluados (regla nº 1).**
   - Con los recuentos de huecos y de rachas y los totales de 3b se deducía si el ATD ve el balón en el
     primer y en el último frame evaluado de cada parte. Son frames públicos, así que eso es un valor por
     frame.
   - Ahora el balón se analiza del primer al último frame con balón de cada tramo. Los huecos de los
     bordes no cuentan (además estaban cortados), y los frames de los huecos de más de 15 s salen sumados
     con los de esos bordes.
   - La prueba lo comprueba: con y sin balón en los bordes, rachas − huecos es el número de tramos, y cada
     hueco tiene su salto y su pérdida.
2. **«< 5» no es una garantía absoluta.**
   - Una celda con menos de 5 casos sigue saliendo «< 5», pero los totales del partido (frames con balón,
     pares de frames, el reparto de R2, `s(T)`) a veces permiten deducirla.
   - Se acepta: es un recuento del partido entero, sin nada ligado a un frame ni a un instante, y la regla
     nº 1 permite recuentos.
   - Se quita de la salida lo que no hacía falta y la deducía directamente: el total de ternas y los
     frames de las rachas de 1 o 2 frames.
   - Las tres tasas que quedaban sin suprimir (cambios del más cercano, tramos de slot y saltos de slot por
     minuto) se suprimen como las demás.
   - Los frames no son casos: no se suprimen.
3. **La severidad alta se apunta y no decide (R1' y R2).**
   - En la DFL todo `D` es un hueco por construcción: se tapa, con 5 frames a cada lado, y 250 de sus 711
     paradas duran 15 s o menos. [medido, revisión] Sin ningún hueco de juego, la `s` alta ya vale 9,05 %
     [7,17–11,11], más que la tolerancia de ±5. [medido, sección 7.2]
   - El ATD no tapa el `D`: ve el balón en muchas paradas cortas. [inferencia]
   - La baja y la media casi no lo notan: 0,00 y 0,67 % sin huecos de juego. [medido]
4. **R2 es por número de huecos,** no por frames. Las dos lecturas se separan unos 30 puntos en la DFL.
   [medido, revisión]
5. **Una celda «< 5» del ATD es una cota, no un fallo** (R1' y R2, sección 7.4). Sin esto, un intervalo
   suprimido hacía fallar R2 con todos los `DISPUTAS`, y una `s(T)` suprimida rompía el código.
6. **R0 para la lectura** de `leer_atd.py`. Antes la apuntaba y seguía.
7. **R5 se apunta también en las severidades baja y alta,** como decía la sección 5.
8. **El agregado 7 de la DFL se mide sin barajar los slots.**
   - Con el barajado del harness, los tramos de slot y los saltos de más de 12 m/s medían el barajado, no
     el tracking: 68,8 s de mediana y 29,5 saltos por minuto. [medido, revisión]
   - Sin barajar, cada slot es una persona: 2.765 s de mediana [medido, sección 7.2], y 0,55 tramos y 0,87
     saltos por minuto [medido, revisión].
   - R6' compara el ATD con la DFL sin barajar.
9. **En 3b, la zona «a 5 m o menos de una línea» incluía el balón fuera del campo,** y la etiqueta lo
   decía. Ya no aplica: la sección 7.7 quita la densidad y la zona del 3b.
10. **Las rachas de balón en la misma posición** van en intervalos [inicio, fin): una de 30 s justos cae en
    «30 s o más».
11. **Límite que se apunta y no se corrige:** el `V` del ATD incluye balón muerto que se ve y que la DFL
    siempre tapa.
    - Es el balón fuera del campo: el 4,2 % de los frames con balón del ATD, frente al 0,15 % en la DFL.
    - También el tramo antes del saque de la 2ª parte: 2.934 frames, el 1,85 % de los evaluados.
    - Está acotado y cae dentro de las tolerancias. [inferencia]

**Lo demás** [medido, revisión]:

- **Reimplementación independiente:** en Python puro, coincide número a número en 36 casos principales,
  6 extremos y 200 al azar, salvo las dos etiquetas de los puntos 9 y 10.
- **Paridad:** la degradación parametrizada reproduce las tres condiciones del harness en los 7 partidos.
- **Escala real:** con un tracking inventado de la forma del ATD (199.319 × 46), el perfil tarda 3,4 s y el
  script entero, 7 s, con unos 540 MB de pico y sin avisos.
- **Regla nº 1:** fuera de los bordes del punto 1, ningún número es un valor por frame. El script no escribe
  nada, solo lee los tres ficheros y, al fallar, no imprime valores.

**El arreglo de los bordes, comprobado contra el código arreglado:** se repite el ataque del revisor con 200
trackings al azar y los 16 estados posibles de los bordes. Lo que se deduce de la salida (bordes sin balón,
tramos que empiezan sin balón, huecos sin salto) es siempre lo mismo. [medido] El verificador de la regla
nº 1 lo confirma con su propio atacante: con el código arreglado, la cuenta de bordes sin balón sale
siempre 0 en 60 sorteos. [medido, revisión]

**Lo que la revisión deja aceptado, a falta del sí de Ismael** (punto 2):

- las celdas «< 5» que se deducen de los totales: un intervalo de huecos (por el reparto y `s(T)`), una
  fila de rachas y una del salto;
- el verificador las rebaja de «bloqueantes» a importantes o menores: son recuentos exactos pequeños del
  partido entero, sin frame ni instante. [medido, revisión]

### 7.7 Pocos huecos: menos celdas pequeñas y la regla ensayada así (14/11, antes de medir)

**Cuántos huecos tendrá el ATD.** Con las cifras del 12/11, el balón del ATD tiene unas 149 rachas en los
frames evaluados: 94.214 frames con balón menos 94.065 pares de frames seguidos. Son, por tanto, unos 150
huecos en todo el partido. [medido, es una cuenta] Los ensayos de la sección 7.5 tenían cientos o miles de
huecos cortos.

**Menos celdas pequeñas.** Con unos 150 huecos, el agregado 2 (5 duraciones × 3 distancias) y el 3b (18
estratos) tendrían muchas celdas de menos de 5 casos, y algunas se podrían deducir de los totales. Los dos
son descriptivos, y el 3b no informa con la degradación de hoy (sección 7.3). Se dejan más gruesos:

- **2:** huecos de hasta 5 s y de más, por las 3 distancias;
- **3b:** solo dentro o fuera de disputa, sin densidad ni zona.

**La regla con pocos huecos.** Ensayo con J03WR9 haciendo de ATD, sin parte dirigida y con `objetivo` 0 y
0,02: unos 0 y 60 huecos de hasta 2 s. Con la regla de la sección 7.4 no queda ningún `DISPUTAS`, ni
siquiera el verdadero (0). [medido] Hay dos causas:

- **Vacío contra vacío:** con `objetivo` 0, la DFL no tiene huecos de hasta 2 s y su reparto sale vacío.
  R2 lo contaba como «no cuadra».
- **Ruido:** con 0,02, el reparto del falso ATD se separa del de la DFL hasta 15 puntos solo por azar. Con
  unos 60 huecos, un error típico de la proporción es de unos 6 puntos. [inferencia]

**Cambio (R2'):**

- La tolerancia de cada celda es la mayor de ±10 puntos y 2,5 errores típicos del reparto del ATD,
  √(p·(1 − p)/n). Aquí p es la proporción de la DFL y n, los huecos impresos del ATD en esa severidad.
- **El 2,5 se fijó después de ver el ensayo de J03WR9 con 0,02,** antes de ver nada del ATD: allí la peor
  celda se separaba 15,08 puntos y la tolerancia nueva es de 15,1. Por eso se comprueba con otros dos
  partidos que no se miraron al fijarlo (J03WPY y J03WOH, abajo).
- Con 157 huecos o más es ±10, como antes. Los cuatro ensayos de la sección 7.5 tienen 204 o más en las
  severidades que deciden. [medido] Por eso no cambian. [inferencia: no se han vuelto a ejecutar]
- Si la DFL no tiene ningún hueco en una severidad, cuadra solo si el ATD tampoco tiene 5 o más.

**Resultado con R2'** [medido]:

| partido que hace de ATD | plantado: `objetivo` · `disputas` · suavizado | `DISPUTAS` que quedan | suavizado elegido |
|---|---|---|---|
| J03WR9 | 0 · 0 · 25 | 0 | 25 |
| J03WR9 | 0,02 · 0 · 25 | 0 | 25 |
| J03WPY | 0,02 · 0 · 25 | 0 | 25 |
| J03WOH | 0,02 · 0 · 25 | 0 | 25 |

- **Queda solo el `DISPUTAS` verdadero** en los cuatro.
- **Con J03WOH, que no se miró al fijar el 2,5, no va justo:** `OBJETIVO` sale 0,021 y 0,019 (plantado,
  0,02) y la mayor diferencia del reparto es de 6 puntos, con 13 de tolerancia. [medido]
- **El ensayo de J03WR9 con 0,02, repetido con el código del commit `74e2c6d`, da una salida idéntica** a la
  de antes: la regla del commit es la que se ensayó. [medido]
- **Con pocos huecos, R1' apenas separa:** una `s` de pocos puntos queda a ±5 del suelo de casi todo. Lo que
  separa es R2: la parte dirigida deja otro reparto de duraciones que los bloques al azar. [inferencia]
- **Límite:** sigue sin ensayarse un ATD que pierda el balón en huecos largos con el juego vivo, que la
  degradación de la DFL no sabe producir (sección 7.5).

### 7.8 R1' y R2 juntos, el reparto con el rango por partido y cuál se parece más (14/11, antes de medir)

**Lo que encontró la sesión planificadora** con un ensayo propio. Con J03WOY haciendo de ATD (`objetivo` 0,1,
`disputas` 0,25 y suavizado 25) no queda ningún `DISPUTAS`, tampoco el verdadero. [medido, revisión] Con el
código de `3d0bf73` sale lo mismo: `OBJETIVO` 0,111 en la severidad media, y R2 falla en ≤ 0,5 s (5,17 frente
a 16,88) y en 2–5 s (42,24 frente a 23,12). [medido]

- El `objetivo` plantado queda por debajo del suelo de `DISPUTAS` 0,25, así que el falso ATD solo tiene la
  parte dirigida.
- Su `s` media (8,04) pasa del suelo de los otros seis (6,58). Es variación entre partidos y queda dentro
  de los ±5 puntos de R1'. Pero R1' interpolaba hasta igualarla y devolvía un `OBJETIVO` de 0,111, justo
  por encima del suelo.
- Ese poco de más mete bloques al azar, muchos y cortos. Como R2 cuenta huecos, el reparto cambia mucho y
  deja de cuadrar. Con el `OBJETIVO` del suelo, cuadraría. [inferencia, de la sesión planificadora]
- Los ensayos con pocos huecos de la sección 7.7 no lo vieron: todos usaban `DISPUTAS` 0, sin parte
  dirigida.

**Primer cambio (R1''): R1' y R2 se juzgan juntos,** como propuso la sesión planificadora.

- En cada severidad, los candidatos son los `OBJETIVO` de la rejilla (0; 0,05; 0,1; 0,15; 0,2; 0,25; 0,3;
  0,35; 0,41 y 0,5) y el interpolado de R1', si no cae en ella.
- La severidad cuadra si alguno cumple R1' (la `s` a ±5 puntos del ATD) y R2 (el reparto, con R2').
- De los que cumplen las dos, se queda el de `s` más cercana al ATD; si empatan, el de menor `OBJETIVO`.
- Motivo: R1' acepta cualquier `OBJETIVO` que deje la `s` a ±5 puntos, así que no tiene sentido juzgar R2
  solo con el que la iguala exactamente.

**Solo con R1'' no basta.** [medido] Con los nueve ensayos de `--ensayos`, ocho recuperan el `DISPUTAS`
plantado, pero J03WOY sigue sin dejar ninguno.

- En la severidad media no cuadra con el 0,25 ningún `OBJETIVO` de la rejilla, tampoco el del suelo.
- La causa es el reparto. Con solo la parte dirigida (el suelo de 0,25), J03WOY tiene un 42,2 % de huecos
  de 2–5 s, y los otros seis juntos, un 28,7 %. La diferencia, 13,6 puntos, pasa de la tolerancia de R2'
  (10,5). [medido]
- Es variación entre partidos, la misma que llevó a R3' a ensanchar el rango del % de disputas.
  [inferencia]

**Segundo cambio (R2''):** una celda del reparto también cuadra si el ATD cae dentro del rango por partido
de la DFL, ensanchado a cada lado con la mitad de su anchura. Si la celda del ATD está suprimida, cuadra si
ese rango ensanchado baja de su cota.

**Tercer cambio: cuál se parece más al ATD** (R4' y R7').

- Con R1'', en J03WR9 (plantado 0,25) quedan el 0,25 y el 0,5, y el % de disputas elige el 0,5. [medido]
- J03WR9 tiene menos disputas que los demás: ese % mezcla la degradación con el estilo del partido.
  [inferencia]
- Ahora «el que más se parece» es el de menor distancia. Es la suma, en las severidades baja y media, de
  |ATD − DFL| de la `s` dividido por 5 puntos y de cada celda del reparto dividido por su tolerancia de R2',
  más |ATD − DFL| del % de disputas dividido por 3 puntos (la tolerancia de R3 en la sección 5). Lo que el
  ATD tiene suprimido («< 5») no cuenta. Si empatan, el menor `DISPUTAS`.
- Sustituye a la definición que se apuntó en la sección 8, punto 3, a falta del sí de Ismael.

**Los ensayos, con los tres cambios** (`python validation/perfil_atd/leer_atd.py --ensayos`). [medido]

| partido que hace de ATD | plantado: `objetivo` · `disputas` · suavizado | `DISPUTAS` que quedan | decide | `OBJETIVO` con el plantado (baja / media / alta) | suavizado elegido |
|---|---|---|---|---|---|
| J03WR9 | 0,3 · 0,25 · 25 | 0,25 y 0,5 | 0,25 | 0,326 / 0,313 / 0,303 | 25 |
| J03WR9 | 0 · 0 · 25 | 0 | 0 | 0 / 0 / 0 | 25 |
| J03WR9 | 0,02 · 0 · 25 | 0 | 0 | 0,024 / 0,017 / 0,050 | 25 |
| J03WPY | 0,2 · 0 · 5 | 0 y 0,25 | 0 | 0,185 / 0,192 / 0,189 | 5 |
| J03WPY | 0,02 · 0 · 25 | 0 | 0 | 0,018 / 0,020 / 0 | 25 |
| J03WMX | 0,15 · 0,5 · 11 | 0,25 y 0,5 | 0,5 | 0,203 / 0,201 / 0,238 | 5 |
| J03WQQ | 0,41 · 0,75 · 51 | 0,75 | 0,75 | 0,500 / 0,445 / 0,419 | 51 |
| J03WOH | 0,02 · 0 · 25 | 0 | 0 | 0,021 / 0,019 / 0,018 | 25 |
| J03WOY | 0,1 · 0,25 · 25 | 0,25 | 0,25 | 0 / 0 / 0 | 25 |

- **En los nueve queda el `DISPUTAS` plantado y es el que decide.** Con R7' tal como estaba (el más cercano
  en % de disputas), en J03WR9 decidía el 0,5.
- **J03WOY se recupera:** con el 0,25, el `OBJETIVO` sale en el suelo, que es donde está el plantado (0,1
  queda por debajo del suelo).
- **La regla es algo más permisiva:** en J03WMX queda también el 0,25, que solo veta.
- **El suavizado acierta en 8 de 9;** en J03WMX elige 5 en vez de 11, como antes.
- **Dos fallos de código** encontrados al ensayar, y arreglados antes de medir:
  - un nombre de variable que tapaba la función de la distancia;
  - una tasa suprimida que rompía R4' con menos de 10 minutos con balón.

  La prueba recorre ahora la regla entera con una DFL inventada, para que un fallo así no pase en silencio.

### 7.9 R3' con el margen entero y la severidad alta solo con R1' (14/11, antes de medir)

Una revisión independiente de los cambios de la 7.8 (el código frente a la bitácora, y un ensayo con
J03WN1, que no había hecho nunca de ATD) encontró esto. [medido, revisión]

- **Un falso negativo de R3'.** Con J03WN1 haciendo de ATD (`objetivo` 0,05, `disputas` 0,25 y suavizado
  25) no queda ningún `DISPUTAS`.
  - El 0,25 plantado cumple R1'' y R2'' y es el de menor distancia, pero R3' lo descarta. El falso ATD
    tiene un 22,01 % de disputas, y el rango de los otros seis, [14,75–19,38] ± 2,32, llega hasta 21,70.
  - J03WN1 es el partido de la DFL con más disputas (26,43 % sin parte dirigida; los otros seis van de 17,68
    a 22,41).
  - **Dejando un partido fuera, en los 7:** con el margen de la mitad, R3' solo descarta el valor
    verdadero en J03WN1 (de +0,81 a +1,66 puntos con `DISPUTAS` 0, y de +0,31 a +0,99 con 0,25). Con un
    margen igual a toda la anchura del rango caben los 7.
- **La severidad alta elegía su `OBJETIVO` con su propio R2,** que no es fiable (sección 7.6) y no decide.
- **Detalles:**
  - el informe no enseñaba el rango por partido de R2'' ni el % de disputas del ATD, así que no se podía
    comprobar el veredicto desde la salida;
  - el recuento de candidatos contaba dos veces el `OBJETIVO` interpolado cuando caía en la rejilla;
  - un JSON guardado con `>` en PowerShell lleva BOM y no se leía;
  - la prueba nueva no comprobaba R2'' ni la distancia.

**Cambios:**

- **R3' se ensancha a cada lado con toda la anchura del rango por partido** (antes, la mitad). R2'' se
  queda con la mitad: en ningún ensayo ha dejado fuera el valor verdadero.
- **En la severidad alta, `OBJETIVO` sale solo de R1'** (el de `s` más cercana al ATD entre los que la dejan
  a ±5 puntos).
- **Los detalles, arreglados:** el informe enseña el rango y el % de disputas, el interpolado ya no se cuenta
  dos veces, el JSON se lee con o sin BOM y la prueba comprueba R2'' y la distancia (68 comprobaciones).

**Los ensayos, con la regla definitiva** (`python validation/perfil_atd/leer_atd.py --ensayos`: los 9 de la
sección 7.8 y los dos de J03WN1). [medido]

| partido que hace de ATD | plantado: `objetivo` · `disputas` · suavizado | % de disputas del ATD | `DISPUTAS` que quedan | decide | `OBJETIVO` con el plantado (baja / media / alta) | suavizado elegido |
|---|---|---|---|---|---|---|
| J03WR9 | 0,3 · 0,25 · 25 | 14,70 | 0, 0,25 y 0,5 | 0,25 | 0,326 / 0,313 / 0,303 | 25 |
| J03WR9 | 0 · 0 · 25 | 16,64 | 0 | 0 | 0 / 0 / 0 | 25 |
| J03WR9 | 0,02 · 0 · 25 | 16,65 | 0 | 0 | 0,024 / 0,017 / 0 | 25 |
| J03WPY | 0,2 · 0 · 5 | 20,91 | 0 y 0,25 | 0 | 0,185 / 0,192 / 0,189 | 5 |
| J03WPY | 0,02 · 0 · 25 | 20,14 | 0 | 0 | 0,018 / 0,020 / 0 | 25 |
| J03WN1 | 0,05 · 0,25 · 25 | 22,01 | 0,25 | 0,25 | 0,104 / 0,100 / 0,117 | 25 |
| J03WN1 | 0,3 · 0,5 · 11 | 17,04 | 0,5 | 0,5 | 0,254 / 0,275 / 0,305 | 11 |
| J03WMX | 0,15 · 0,5 · 11 | 14,90 | 0,25 y 0,5 | 0,5 | 0,203 / 0,201 / 0,238 | 5 |
| J03WQQ | 0,41 · 0,75 · 51 | 6,89 | 0,75 | 0,75 | 0,500 / 0,445 / 0,419 | 51 |
| J03WOH | 0,02 · 0 · 25 | 21,54 | 0 | 0 | 0,021 / 0,019 / 0,018 | 25 |
| J03WOY | 0,1 · 0,25 · 25 | 18,89 | 0,25 | 0,25 | 0 / 0 / 0 | 25 |

- **En los 11 queda el `DISPUTAS` plantado y es el que decide.** J03WN1 con 0,25, que fallaba, se recupera.
- **Precio del margen entero:** en J03WR9 con 0,25 queda también el 0, que solo veta. En cuatro de los once
  quedan dos o tres `DISPUTAS`: el harness medirá con todos, y los vecinos solo vetan (R7').
- **`OBJETIVO`:** a ±0,05 del plantado cuando está por encima del suelo, salvo con suavizado 51 (sección
  7.5). Por debajo del suelo sale en el suelo o cerca (J03WOY, J03WN1 con 0,05).
- **El suavizado acierta en 10 de 11;** en J03WMX elige 5 en vez de 11, como antes.

## 8. Lo que decide Ismael antes de ejecutar nada en el partido

Cada punto pendiente tiene un valor por defecto, y un «sí» sin más quiere decir ese valor. La respuesta se
apunta aquí, con fecha, y se sube antes de ejecutar `validation/partido/perfil_atd.py`.

**Su respuesta (14/11), antes de ver ningún número del ATD:** «Sí, y súbelo», a la pregunta «¿Das el sí a
la sección 8 por defecto, con R1'' incluida?». Cubre los puntos 1, 2 y 4 con sus valores por defecto, y la
sección 7.8 tal como estaba entonces: solo R1''.

**Lo que vino después de su sí, confirmado (14/11), antes de ver ningún número del ATD:** R2'' y la
distancia (sección 7.8) y la sección 7.9 entera. Su respuesta: «Sí, súbelo», a la pregunta «¿Confirmas los
cambios de la regla posteriores a tu sí, para subirlo?». Con eso, la regla queda fijada en el commit que lo
apunta, antes de ejecutar `validation/partido/perfil_atd.py`.

1. **Los cambios de las secciones 7.1 a 7.9.** Sí.
2. **Las celdas «< 5» que se pueden deducir de los totales** (sección 7.6, punto 2). Son recuentos del
   partido entero, sin frame ni instante. Sí: se aceptan, con los agregados 2 y 3b más gruesos (sección
   7.7).
3. **R7', con qué `DISPUTAS` se decide: decidido por Ismael el 14/11, antes de ver ningún número del ATD.**
   - Se lo planteó la sesión planificadora, en otra conversación, como dos opciones:
     - A: ganar con todos los `DISPUTAS` que queden;
     - B: ganar con el que más se parece al ATD y no perder con los demás.
   - Su respuesta, que transmite esa sesión: «vale la B, pásaselo tú a la otra sesión».
   - El texto que aceptó: «Para R7': decide el valor de DISPUTAS que más se parezca al ATD. Los demás que
     queden se puntúan y se enseñan al lado, y solo le quitan la victoria a un candidato si con alguno
     queda 0,03 o más por debajo del control. Apúntalo en la bitácora antes de que yo ejecute el script.»
   - **Cuál se parece más al ATD**, fijado antes de medir. La primera versión era el `DISPUTAS` cuyo % de
     disputas en la DFL está más cerca del del ATD, y en J03WR9 elegía mal. La definición vale ahora la
     distancia de la sección 7.8, que usa también R4'. Confirmada por Ismael con lo demás que vino después
     de su sí (arriba).
   - Lo de exigir las dos convenciones de etiquetas es del plan (`docs/PLAN_ENTREGA.md` §4) y no cambia.
4. **Qué condiciones del balón votan en la regla de §5.8 cuando el harness use la degradación nueva.**
   Sí, el valor por defecto, que es la propuesta de la sección 5:
   - votan las tres severidades, con el `DISPUTAS` del punto 3, el `OBJETIVO` que sale para cada una (R1''
     en la baja y la media, R1' en la alta) y el suavizado de R4';
   - «limpio» y la condición de hoy (41 % de los frames vivos) se siguen puntuando, sin voto.

## 9. Después de medir (14/11)

Ismael ejecutó `validation/partido/perfil_atd.py` el 14/11, con todo lo anterior en `main` (`84b8d7c`).
`leer_atd.py` se ejecutó sin cambiar nada de esta carpeta. El resultado está en
`validation/resultados/2026-11-14_perfil_atd.md`.

- **R0 cuadra. No queda ningún `DISPUTAS`** (R7: «todavía no») [medido]. R4' (25 frames) y R5 se
  calcularon con `DISPUTAS` 0,25, que no pasa R1': son descriptivos.
- **Lo que no estaba previsto** [inferencia, sección 2 del resultado]: el balón del ATD se parece al de
  la DFL con solo los `D` tapados (`limpio`), y la mayor parte de su 41 % sin balón sería balón muerto. Los
  dos candidatos de la sección 7.4 (la ley de huecos del ATD, `dilatar` y `aire`) siguen tapando balón en
  juego. Lo que pide el perfil es tapar menos.
- **El cambio de forma del paso 3 lo decide Ismael.** Lo que se elija se apunta aquí como cambio posterior
  a medir, y se vuelve a leer con esta misma regla.

### 9.1 La forma nueva, escrita antes de volver a leer (14/11)

**Decisión de Ismael (14/11), con el resultado delante:** «Como el ATD». La condición principal pasa a
parecerse al ATD: el balón tapado en los `D`, casi nada más en juego, y suavizado. La de antes (41 % de los
vivos) queda como prueba de estrés, sin voto. Se vuelve a leer con esta misma regla.

**Cómo se tapa (forma «atd», `dfl.degradar_con` y `dfl.mascara_como_el_atd`).** Es el primer candidato de
la sección 7.4, la ley de huecos del ATD, con sus dos partes medidas:

- **la misma parte dirigida** (`DISPUTAS`), sin cambios;
- **microcortes al ritmo del ATD:** 15 por cada 94.214 frames vivos, con longitud geométrica de media 3,4
  frames (51 frames en 15 huecos) y como mucho 12 (0,5 s);
- **bloques de 5 a 15 s** (longitud uniforme) para completar `OBJETIVO`, en vez de los de 1 s de media.

**La regla no cambia.** `leer_atd.py --forma atd` recorre los mismos `DISPUTAS` y `OBJETIVO` con las mismas
R0 a R7'. Sin `--forma`, la lectura es la de antes, byte a byte.

**Qué entra en el harness, según lo que salga** (punto 4 de la sección 8):

- **votan** las condiciones de la forma «atd» con el `DISPUTAS` que decida, el `OBJETIVO` de cada
  severidad y el suavizado de R4'. Las severidades con el mismo `OBJETIVO` son la misma condición y se
  juntan;
- **se puntúan sin voto** «limpio» y «huecos y suavizado» (la de antes);
- **si con la forma «atd» tampoco queda ningún `DISPUTAS`,** se para y decide Ismael.

**Ensayo:** J03WR9, degradado con la forma «atd» (`objetivo` 0,05, `disputas` 0 y suavizado 25), hace de
ATD. La regla tiene que devolver `DISPUTAS` 0 y suavizado 25. Se lanza a la vez que la lectura.

### 9.2 Lo que dice el ensayo de la forma «atd», escrito antes de ver la relectura del ATD (14/11)

**Ensayo:** J03WR9, degradado con la forma «atd» (`objetivo` 0,05, `disputas` 0 y suavizado 25), hace de
ATD (`leer_atd.py --ensayo J03WR9 0.05 0 25 --forma atd`).

- **Lo que sale bien** [medido]: queda `DISPUTAS` 0 y decide él. El suavizado elegido es 25 y R5 cuadra.
- **En las severidades baja y media, `OBJETIVO` no se identifica** [medido]. Los 10 valores de la rejilla
  pasan R1' y R2, y la regla elige 0,41 porque es el de `s` más cercana. Con la forma «atd», los bloques
  duran de 5 a 15 s y no cuentan en los huecos de hasta 2 s ni de hasta 5 s.
- **La severidad alta sí lo ve, pero se queda corta** [medido]: da 0,026 para el 0,05 plantado. Su `s`
  mezcla los huecos de las paradas, que cambian de un partido a otro [inferencia].

**Cambio, escrito antes de ver la relectura del ATD:**

- **Con la forma «atd», `OBJETIVO` sale solo de la severidad alta (R1').** Las severidades baja y media
  siguen decidiendo `DISPUTAS` (R1', R2 y R3'), como hasta ahora.
- **Votan dos condiciones,** que acotan lo que el perfil no puede medir: si los huecos de 5 a 15 s que el
  ATD tiene de más son juego o paradas.
  - «como el ATD»: el `DISPUTAS` que decide, microcortes, el `OBJETIVO` de la alta y el suavizado de R4';
  - «como el ATD, sin bloques»: lo mismo con `OBJETIVO` 0, como si todos los huecos largos fueran
    paradas.
- **Se puntúan sin voto** «limpio» y «huecos y suavizado».
- **Esto cambia la sección 9.1,** que decía «el `OBJETIVO` de cada severidad». Se le enseña a Ismael antes
  de subir.
