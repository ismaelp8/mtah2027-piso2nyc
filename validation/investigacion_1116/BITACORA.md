# Sondeos de la investigación del 16/11 · bitácora

- **Quién y cuándo:** Claude (sesión de investigación de Ismael), 16/11/2026.
- **Para qué:** saber si cuatro ideas tienen recorrido antes de proponerlas en
  `docs/investigacion_2026-11-16.md`. **Un sondeo no decide que nada entre:** dice si merece la pena que
  alguien lo mida con la regla de §5.8.
- **Datos:** solo datos abiertos de otros partidos. Los 7 de la Bundesliga (Bassek et al., 2025, CC BY 4.0)
  con el harness, y la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`, licencia MIT). El examen
  de SkillCorner (`lector.EXAMEN`) no se toca. Nada del partido, ni la ventana pública.
- **Código:** `main` en `ee404f6`, sin cambios en `possession/`.
- **Las reglas de lectura de este fichero se escriben y se suben antes de ejecutar nada.** Los resultados se
  añaden después, debajo de cada regla.

## S1. ¿Conviene cambiar más de equipo cuando la nota es más baja?

**La idea.** El `spellF1` es un F1 sobre posesiones: F = 2·TP / (predichas + reales). Añadir k posesiones de
las que acierta una fracción p sube la nota solo si p > F/2 (si no rompen las que ya acertábamos). Con el `D`
de las etiquetas, el harness da F entre 0,50 y 0,73: el umbral está entre 0,25 y 0,36. En el partido se
espera F entre 0,30 y 0,50 (revisión externa, punto 2): el umbral bajaría a 0,15–0,25. Si esto pesa, el coste
de cambio que más conviene tiene que bajar cuando la nota baja.

**Qué se mide.** El pipeline de `main` con el coste de cambio en 6, 12, 18, 25 (`main`) y 40, sin tocar
`to_dead` ni `from_dead`:

- en la DFL, con `validation/harness/puntuar.py`, con el `D` de las etiquetas y con el `D` propio
  (`validation/harness/versiones/investigacion_costes_2026-11-16.json`);
- en la mitad de entrenamiento de SkillCorner, con `costes_skillcorner.py`, en las dos condiciones que votan
  allí y con los dos `D`.

**Regla de lectura, antes de medir (descriptiva).**

- «El efecto del nivel se ve» si, al pasar del `D` de las etiquetas al `D` propio, el coste con más `spellF1`
  baja o se queda igual en las cuatro celdas de la DFL (dos convenciones por dos condiciones que votan) y en
  SkillCorner, y baja en al menos tres de ellas.
- «Hay candidato para David» si un mismo coste menor que 25 gana a `main` por +0,010 o más con el `D` propio
  en el flag, en el control y en SkillCorner a la vez. Si no, queda como observación.
- El `D` propio de la DFL tiene un límite conocido: el balón tapado en los `D` delata la etiqueta. Por eso es
  descriptivo.

## S2. ¿Sirve decodificar a riesgo mínimo con la evidencia de B5?

**La idea.** El Viterbi da la secuencia más probable, no la que más `spellF1` espera. Con una distribución
sobre secuencias se puede elegir la salida que más `spellF1` medio saca frente a muestras de esa distribución.
Solo sirve si la distribución dice algo verdadero sobre dónde dudamos.

**Qué se mide** (`riesgo_minimo.py`; DFL, «como el ATD», `D` de las etiquetas, B5 con los coeficientes que no
vieron cada partido):

1. La distribución: la cadena del decodificador (evidencia sumada y costes de `main`) con una temperatura T:
   p(secuencia) ∝ exp(puntuación / T). T se elige en {1, 2, 4, 8, 16, 32} por la verosimilitud por frame de
   las etiquetas en los otros seis partidos, promediando las dos convenciones.
2. **Los bordes.** Para cada cambio directo de equipo de `main`, la anchura de la duda: los frames seguidos
   alrededor del cambio con la probabilidad del equipo nuevo entre 0,2 y 0,8. Se compara con el error real
   (distancia al cambio real más cercano hacia el mismo equipo a ±50 frames; sin ninguno, «sin pareja»).
3. **La elección.** 24 muestras por parte. Candidatos: el Viterbi con coste de cambio 8, 12, 18, 25, 35 y
   50. En cada parte se elige el candidato con más `spellF1` medio frente a las muestras, y se puntúa esa
   elección con las etiquetas de verdad. Se compara con `main` y con la mejor elección posible por parte
   (oráculo).

**Regla de lectura, antes de medir.**

- «La duda del modelo sirve» si la correlación de rangos entre anchura y error es de 0,3 o más, **o** la
  anchura separa los cambios sin pareja de los demás con un AUC de 0,65 o más. Con las dos convenciones.
- «El riesgo mínimo merece construirse» si la elección por parte gana a `main` por +0,010 o más con las dos
  convenciones. Con menos, no: la evidencia de B5 se equivoca con seguridad (posesiones cortas, punto 3) y
  ninguna regla de decisión lo arregla.

## S3. ¿Dice algo la cámara que no digan ya los jugadores?

**La idea.** La homografía del partido no se ha usado nunca. Da, en el 100 % de los frames, hacia dónde mira
la cámara táctica. Si el encuadre sigue al balón, sería un sustituto del balón cuando falta. SkillCorner trae
el encuadre proyectado en el campo (`image_corners_projection`), así que se puede sondear fuera del partido.
Es una cámara de retransmisión, no la táctica: **el sondeo puede exagerar**, y lo que cuenta al final es un
agregado del partido.

**Qué se mide** (`camara_skillcorner.py`; 4 partidos de `lector.ENTRENAMIENTO`; frames de juego con el balón
detectado):

- el error (RMSE, en metros) al predecir la x y la y del balón con una recta a partir de (a) el centroide de
  los jugadores detectados, (b) el centro del encuadre y (c) los dos; ajustado en dos partidos y medido en
  los otros dos, y al revés;
- el desfase con más correlación entre la velocidad en x del centro del encuadre y la del balón.

**Regla de lectura, antes de medir.** «La cámara añade algo» si, fuera de muestra, (c) baja el error de (a)
un 20 % o más en x. Si no, el centro del encuadre es, a efectos prácticos, el centroide de los jugadores que
se ven, que B5 y E2 ya usan: la idea no va entre las primeras y como mucho queda un agregado del partido.

## S4. ¿Se pueden medir los bordes de las paradas en SkillCorner?

**La idea.** En la DFL el balón va congelado en los `D` y hay que taparlo, así que nada que use el balón en
una parada se puede validar allí. SkillCorner no lo congela, pero sus `D` son sobre todo repeticiones sin
tracking. Si quedan bastantes paradas con tracking, valdrían para validar bordes por tipo de reinicio
(`start_type` de `dynamic_events.csv`).

**Qué se cuenta** (`paradas_skillcorner.py`; los 10 de `lector.ENTRENAMIENTO`): las rachas fuera de las fases
de juego dentro de cada parte, por duración; en cuántas hay algún jugador detectado en el 80 % o más de sus
frames, y en cuántas se ve el balón en su último segundo y en el primero después. Y los valores de
`start_type` y de `game_interruption_*`.

**Regla de lectura, antes de contar.** «Sirve para validar bordes» si hay 150 paradas o más con tracking en el
80 % de sus frames en los 10 partidos, y al menos 30 de cada uno de tres tipos de reinicio. Con menos, no.

## S5. Cambios de equipo falsos justo antes de una parada

**La idea** (hipótesis D2 del visionado, que no se abrió): si nuestro `D` llega tarde, el equipo que va a sacar
se acerca al balón y le damos una posesión corta que no existe. Con un F1 sobre posesiones, cada una de esas
resta dos veces: sobra ella y estropea el borde de la anterior.

**Qué se mide** (`cambio_antes_de_parada.py`; DFL, `D` propio, las dos condiciones que votan y dos modos del
balón en los `D`: tapado, como el harness, y a la vista, como `validation/apuesta_b/d_propio.py`):

- las posesiones predichas de menos de 5 s (125 frames) que acaban en un `D` nuestro y vienen de un cambio
  directo desde el otro equipo: cuántas son, cuántas se emparejan con una real (IoU ≥ 0,5) y qué hay de verdad
  en sus frames;
- el `spellF1` de `main` y de dos variantes: (a) esos frames pasan a `D`; (b) pasan al equipo de antes. También
  con 3 s y con 10 s, como sensibilidad.

**Regla de lectura, antes de medir.** «Hay candidato» si una misma variante, con el corte de 5 s, gana a `main`
por +0,010 o más con las dos convenciones, en las dos condiciones que votan y en los dos modos del balón. Si
gana solo en un modo, queda como observación: la DFL no sabe cuál de los dos se parece al ATD.

## S6. ¿Fecha el arranque del balón el final de una parada? (Metrica sample-data)

**La idea** (hipótesis D5 del visionado y descarte R1 del 14/11, que quedó sin medir): la parada acaba en el
golpeo del saque. Si antes del saque el balón se ve quieto, el instante en que arranca fecha el final del `D`.
No se puede medir en la DFL (el balón va congelado y tapado) ni en SkillCorner (sondeo S4). Los 3 partidos de
Metrica sample-data traen el frame de cada `SET PIECE`, anotado por una persona, y el balón.

**Qué se mide** (`arranque_balon_metrica.py`; los 3 partidos; el balón tal cual y suavizado 25 frames):

- en qué fracción de los frames `D` se ve el balón;
- en cada saque (paso de `D` a juego): si el balón se ve en el segundo anterior (80 % de los frames) y si está
  quieto (mediana de la velocidad por debajo de 1 m/s);
- el arranque: en ±3 s alrededor del saque, el primer frame con el balón a 3 m/s o más después de un segundo
  quieto. Con el balón suavizado se corrige la rampa de la media móvil. El error es arranque menos saque.

**Regla de lectura, antes de medir.** «Sirve» si el balón se ve en el segundo anterior en el 50 % o más de los
saques y, en esos, el arranque cae a ±12 frames del saque en el 50 % o más, con el balón tal cual y con el
suavizado. (La pieza de estado da el final a ±25 frames en el 40 % en la DFL.) Si el balón no se ve en los `D`
de estos datos, el sondeo se cierra sin medir nada más.

## S7. Cribado de señales del propio tracking (lo pidió Ismael el 16/11, a través de la sesión principal)

**Qué es.** Un cribado, no un candidato. Muchas señales sencillas del tracking, medidas todas igual, para ver
cuáles dicen algo **donde fallamos** que B5 no diga ya. Lo que ya está dentro de B5, B9 o E2 va como
referencia o no se repite: la velocidad de cada equipo hacia su portería, la dispersión, el juego en la
dirección de ataque (B2), la dirección del balón (B9), el evento de toque (B8 y anexo A.4), la velocidad media,
los lentos, los jugadores fuera y los del área (E2).

**Señales** (`cribado_senales.py`; todas con el tracking degradado, sin etiquetas; cada una opina `H`, `A` o
nada, con umbrales fijados aquí antes de medir):

- **Referencias:** R1 el más cercano (N1, ya en B5); R2 la dirección del balón (B9); R3 el signo de B5 frame a
  frame.
- **Distancias al balón:** S1 diferencia entre el más cercano de cada equipo, de más de 1 m, con alguno a menos
  de 10 m; S2 los dos más cercanos son del mismo equipo y están a menos de 5 m; S3, S4 y S5 mayoría de jugadores
  a 3, 5 y 10 m; S6 quién llega antes (0,7 s de reacción y carrera a 5 m/s desde la posición prevista, como el
  control del campo de Spearman), con 0,5 s de margen; S7 el que más rápido se acerca (más de 2 m/s, a menos de
  10 m).
- **Velocidades y el momento del toque:** S8 el mismo equipo a menos de 2 m durante los 12 frames anteriores;
  S9 balón lento (menos de 3 m/s) con un jugador a menos de 3 m; S10 el jugador que se mueve con el balón (a menos
  de 5 m, diferencia de velocidad de menos de 1,5 m/s, balón a más de 2 m/s, velocidades en ±12 frames); S11 el
  balón frena más de 3 m/s junto a un jugador (a menos de 3 m): su equipo durante 1 s; S12 el más cercano con dos
  rivales o más a 5 m (presionado); S13 el más cercano sin rivales a 5 m (libre); S14 dos contactos seguidos del
  mismo equipo a menos de 2 m del balón, separados por 2 s o menos: ese equipo durante 2 s.
- **Formación** (sin el jugador más retrasado de cada equipo, que suele ser el portero): S15 el equipo más ancho
  (desviación típica en y, 2 m de margen); S16 el más largo (en x, 2 m); S17 el de más área (razón de 1,3); S18 el
  de la línea defensiva más alta (5 m); S19 el equipo con tres jugadores o más por detrás del balón que el otro
  defiende.
- **Huecos del balón:** S20 el último más cercano visto se queda durante el hueco; S21 el balón desaparece a
  menos de 3 m del más retrasado de un equipo, dentro de su área (el portero lo coge): ese equipo durante el hueco.
- **Balón muerto, solo con los jugadores** (en la DFL el balón va tapado en los `D`): D1 velocidad media en 1 s
  de menos de 1,5 m/s (`D`) o de más de 2,5 (juego); D2 frenazo colectivo (la media del segundo siguiente baja
  más de 1 m/s): `D` durante 2 s; D3 arranque colectivo (sube más de 1 m/s): juego durante 1 s; D4 un jugador
  entre 0,5 y 3 m fuera de las líneas: `D`; D5 ocho jugadores o más en un área y velocidad media de menos de
  1,5 m/s: `D`.

**Dónde:** la DFL con el balón «como el ATD», con el flag y con el control, con el balón a su hora y 4 frames
tarde (lo medido en el partido); y la mitad `lector.ENTRENAMIENTO` de SkillCorner, «detectado». El examen no se
toca. La referencia es `main` con el `D` de las etiquetas (B5 con los coeficientes que no vieron cada partido de
la DFL; los de la entrega en SkillCorner).

**En qué frames** (los de juego, con las etiquetas de cada convención):

- Z1: dentro de las posesiones reales de 2 a 10 s en que `main` dice el otro equipo en la mayoría de sus frames;
- Z2: a ±1 s de los cambios directos de equipo reales;
- Z3: el primer y el último segundo de cada parada real y el segundo de juego de antes y de después, frente a
  `main` con su `D` propio (solo la DFL; solo las señales D);
- Z4: los frames de juego sin balón.

**Qué números:** en qué parte de los frames opina y cuánto acierta cuando opina; en Z2, cuántos frames que `main`
falla arregla («rescata») y cuántos que acierta estropea («estropea»); y el valor añadido sobre B5: una regresión
logística sin término independiente con la diferencia `H` − `A` de B5 y la señal, entrenada en todos los frames de
juego de los demás partidos (uno de cada 5) y medida en el que queda fuera (en SkillCorner, en dos mitades de 5
partidos), frente al signo de B5 solo. Es acierto por frame, no `spellF1`: el que decide es el harness.

**Regla de lectura, antes de medir:**

- **Una señal de equipo «añade»** si, con la regresión, sube el acierto en Z1 ∪ Z2 en 1,0 punto o más sin bajar el
  acierto en todos los frames de juego más de 0,2 puntos, en las cuatro medidas: DFL flag, DFL control, DFL control
  con el balón 4 frames tarde y SkillCorner.
- **«Apuesta de convención»** si lo cumple con el flag pero no con el control o en SkillCorner.
- **S8 y S14 son circulares con las etiquetas de control** (salen de la misma regla de «12 frames o dos toques»):
  con ellas solo cuentan el flag y SkillCorner.
- **Una señal de `D` «añade»** si en Z3 rescata al menos el 20 % de lo que `main` falla, el doble o más de lo que
  estropea, y dice `D` en el 5 % o menos de los frames de juego.
- **Si alguna señal añade,** se propone un candidato (B5 reentrenado con ella) para que lo construya otra sesión, con
  su regla de §5.8, la mitad de entrenamiento de SkillCorner y los eventos. Si ninguna añade, se dice y se cierra.
- Además, una fila con B5 más todas las señales de equipo a la vez: la cota de lo que este cribado puede dar.

---

# Resultados (16/11), en el orden en que se ejecutaron

Salidas tal cual en `salidas/`. Código: `main` en `ee404f6` más estos scripts, sin cambios en `possession/`.

## S1. El coste de cambio, con el `D` de las etiquetas y con el propio [medido]

`spellF1` con los partidos juntos; entre paréntesis, la diferencia frente a `main` (coste 25).

| datos | `D` | balón | 6 | 12 | 18 | 25 | 40 |
|---|---|---|---|---|---|---|---|
| DFL flag | etiquetas | como el ATD | 0,495 | 0,498 | **0,499** | 0,498 | 0,496 |
| DFL flag | etiquetas | sin bloques | 0,510 | 0,512 | **0,513** | 0,512 | 0,510 |
| DFL flag | propio | como el ATD | 0,414 | **0,418** | 0,417 | 0,416 | 0,413 |
| DFL flag | propio | sin bloques | 0,431 | 0,434 | **0,435** | 0,433 | 0,429 |
| DFL control | etiquetas | como el ATD | 0,698 | 0,712 | 0,721 | 0,728 | **0,735** (+0,007, 6 de 7) |
| DFL control | etiquetas | sin bloques | 0,720 | 0,733 | 0,742 | 0,748 | **0,755** (+0,008, 7 de 7) |
| DFL control | propio | como el ATD | 0,588 | 0,602 | 0,610 | 0,616 | **0,624** (+0,008, 6 de 7) |
| DFL control | propio | sin bloques | 0,615 | 0,628 | 0,637 | 0,642 | **0,649** (+0,008, 7 de 7) |
| SkillCorner | etiquetas | detectado | 0,498 | 0,506 | 0,514 | 0,519 | **0,529** (+0,010) |
| SkillCorner | etiquetas | detectado, suavizado | 0,494 | 0,505 | 0,510 | 0,514 | **0,524** (+0,010) |
| SkillCorner | propio | detectado | 0,366 | 0,371 | 0,376 | 0,382 | **0,389** (+0,007) |
| SkillCorner | propio | detectado, suavizado | 0,363 | 0,370 | 0,375 | 0,378 | **0,386** (+0,008) |

**Con la regla:**
- «El efecto del nivel se ve»: **no.** Al pasar al `D` propio el mejor coste solo baja en una de las cinco celdas
  (flag «como el ATD», de 18 a 12). Con el control y en SkillCorner sigue en 40.
- «Hay candidato para David»: **no.** Ningún coste menor que 25 gana a `main`.

**Lectura [inferencia]:** el umbral F/2 no manda aquí porque los cambios de más que da un coste bajo aciertan
menos que F/2: no son las posesiones que faltan (su evidencia tiene el signo contrario, posesiones cortas, punto 3).
**Lo nuevo es que SkillCorner, que no se había medido con otros costes, se pone del lado del control:** subir el
coste a 40 da +0,007 a +0,010 allí y con el control, y −0,002 a −0,004 con el flag. No llega a +0,03 y vuelve a ser
una apuesta de convención; lo que sí dice es que, si hubiera que moverlo, sería hacia arriba.

## S2. Riesgo mínimo con la evidencia de B5 [medido]

- La temperatura que mejor explica las etiquetas frame a frame es T = 16 en los 7 pliegues. Con ella, una muestra
  tiene una mediana de 2.685 posesiones por parte (las reales son unas 220 con el flag): la distribución se
  fragmenta, porque la evidencia de frames vecinos no es independiente.
- **La duda del modelo:** Spearman anchura–error 0,09 (flag) y 0,14 (control); AUC de los cambios sin pareja 0,60 y
  0,69. **No cumple** (pedía 0,3 o un AUC de 0,65 con las dos convenciones).
- **La elección por parte:** el riesgo mínimo elige el coste 8 en 13 de 14 partes y pierde: 0,497 frente a 0,498
  (flag) y 0,704 frente a 0,728 (control). **No merece construirse.**
- **El techo de elegir el coste por parte** (un oráculo que elige el mejor en cada parte): 0,504 (+0,006) y 0,741
  (+0,013). Ni con un oráculo llega a +0,03.

## S3. La cámara frente al centroide de los jugadores (SkillCorner) [medido]

- El centro del encuadre explica la x del balón igual que el centroide de los jugadores detectados (de 9,3 a 9,4 m
  y de 7,7 a 8,4 m de error) y la y peor (13 m frente a 10 m).
- Los dos juntos frente al centroide solo: +1 %, −9 %, −2 % y −2 % de error. **No cumple** (pedía −20 % en x).
- La cámara va unos 0,4 s detrás del balón (correlación máxima de 0,74 con 4 muestras de desfase).
- **Lectura:** el encuadre es, a efectos prácticos, el centroide de lo que se ve, que B5 y E2 ya usan. Además va
  tarde. Se cierra sin agregado del partido.

## S4. Paradas con tracking en SkillCorner [medido]

- 1.019 paradas entre dos fases de juego en los 10 partidos; solo 133 tienen jugadores detectados en el 80 % de sus
  frames, y casi todas son cortas (63 de menos de 5 s). Por tipo, con tracking: 80 saques de banda, 12 faltas, 7
  córners, 5 saques de puerta.
- **No cumple** (pedía 150 y 30 de tres tipos). SkillCorner no sirve para validar los bordes de las paradas.

## S5. Posesiones cortas justo antes de una parada nuestra [medido]

- Con el corte de 5 s hay de 108 a 160 en los 7 partidos. Solo entre el 8 y el 26 % se emparejan con una real; de
  sus frames, entre el 39 y el 58 % son `D` de verdad. Son, sobre todo, un `D` que llega tarde.
- Quitarlas (pasarlas a `D`): con el control, +0,007 a +0,009 con el balón tapado en los `D` y +0,018 / +0,019 con el
  balón a la vista (7 de 7). Con el flag, −0,002 tapado y +0,004 a la vista.
- **Con la regla: no hay candidato** (con el flag y el balón tapado no gana). Queda como observación: con el balón a la
  vista en los `D`, que es lo que pasa en el ATD (se ve en el 68 % de los frames de las ventanas `SET PIECES`), da
  +0,02 con el control y no hace daño con el flag.

## S6. El arranque del balón en Metrica sample-data [medido]

- El balón se ve en el 20 % de los frames `D` y en el segundo anterior al saque solo en 2 de 210 saques (1 %).
- **Se cierra sin medir nada más,** como decía la regla: en estos datos el balón tampoco se ve antes del saque.

## S8. El final de la parada por la geometría del saque (regla escrita antes de medir)

**La idea.** El final de las paradas vale +0,030 (flag) y +0,042 (control) en la DFL si se pone en su sitio
(diagnóstico de errores, punto 5), y la pieza de estado lo acierta a ±1 s en el 40 %. En un saque de banda el que
saca está fuera del campo hasta que lanza; en un córner, junto al banderín. El instante en que deja de haber alguien
ahí fecha el saque sin el balón. En la DFL se puede medir, porque los jugadores se ven durante las paradas (el
balón va tapado y no se usa). En el ATD hay jugadores fuera del campo en el 84,6 % de las ventanas de saque de banda
y en el 91,7 % de las de córner (agregados del 14/11).

**Qué se mide** (`fin_por_geometria.py`; DFL, 7 partidos, «como el ATD», `main` con su `D` propio):

- Para cada parada real de 2 s o más que `main` detecta (una racha nuestra de `D` la toca), el fin predicho Ê es el
  final de esa racha nuestra.
- **Tipo, por geometría, sin etiquetas:** «banda» si en [Ê − 5 s, Ê + 2 s] hay algún jugador entre 0,5 y 5 m fuera
  de una banda; si no, «córner» si hay alguno a menos de 2,5 m de un banderín; si no, «otro».
- **Ancla:** el frame siguiente al último en [Ê − 5 s, Ê + 2 s] con ese jugador fuera (banda) o junto al banderín
  (córner).
- El error con signo frente al final real, de Ê y del ancla, y la parte a ±12 y a ±25 frames.

**Regla de lectura, antes de medir.** «Hay candidato para Manuel y Ana» si, en los tipos «banda» y «córner» juntos,
el ancla queda a ±12 frames del final real en el 50 % o más de las paradas y en 15 puntos más que Ê, con al menos 60
paradas. Si solo lo cumple un tipo, se dice cuál. Si no, se cierra.

## S7. Cribado de señales [medido]

Salidas: `salidas/2026-11-16_s7_cribado_dfl.md` y `salidas/2026-11-16_s7_cribado_skillcorner.md`.

**Con la regla: ninguna señal de equipo añade, y ninguna de `D`.** La columna que decide es «+ B5: Δ en Z1 ∪ Z2»
(puntos de acierto por frame, fuera de muestra):

| señal | DFL flag | DFL control | DFL control, 4 tarde | SkillCorner | ¿añade? |
|---|---|---|---|---|---|
| R2 dirección del balón (B9, ya medida) | +6,27 | +2,75 | +2,22 | −0,01 | no: solo en la DFL, como B9 |
| S14 dos contactos seguidos (circular) | +0,98 | +0,40 | +0,52 | +0,68 | no |
| S18 línea defensiva más alta | +0,87 | −0,08 | −0,09 | +0,46 | no |
| S11 el balón frena junto a un jugador | +0,65 | +0,50 | +0,57 | +0,39 | no |
| S3 mayoría a 3 m | +0,16 | −0,10 | −0,10 | +0,55 | no |
| S15 el más ancho | −0,50 | −0,23 | −0,38 | −0,28 | no |
| S17 el de más área | −0,26 | +0,10 | −0,02 | −0,19 | no |
| **B5 + todas las señales a la vez** | +8,20 | +3,74 | +3,68 | +2,08 | – (cota) |

- **Lo que más enseña:** la anchura (S15) y el área (S17) aciertan el 87–91 % de los frames de juego, más que el más
  cercano, pero dentro de las posesiones que perdemos aciertan solo el 12–27 %. Son señales lentas: dicen el equipo
  que llevaba un rato con el balón, justo el fallo de B5. Lo mismo, en menor grado, la mayoría a 10 m y la línea
  defensiva.
- **Las señales del toque** (balón lento, que se mueve con un jugador, que frena) aciertan mucho cuando opinan (83–93
  %), pero opinan poco y casi siempre donde B5 ya acierta.
- **La dirección del balón** es la única que rescata mucho (+6 puntos con el flag), pero no hace nada en SkillCorner:
  es lo que ya dijo B9.
- **La cota** (todas a la vez, en una regresión): +2 puntos en SkillCorner y +3,7 con el control, por frame. Es del
  orden de lo que ya dio la red de una capa de la fase 3, que no movió el `spellF1`.
- **Balón muerto:** D1 rescata el 15 % y estropea el 13 %, y dice `D` en el 14 % del juego; el frenazo y el arranque
  colectivos opinan en el 5–7 % de Z3 y aciertan el 56–62 %. Nada pasa la regla.
- Con el balón 4 frames tarde no cambia nada de esto.

## S8. El final de la parada por la geometría del saque [medido]

| tipo | paradas | pieza de estado a ±12 / ±25 | ancla a ±12 / ±25 | mediana del error del ancla |
|---|---|---|---|---|
| banda | 251 | 37 % / 58 % | 27 % / 46 % | −13 frames |
| córner | 32 | 28 % / 53 % | 3 % / 28 % | +33 |

**Con la regla: no.** El ancla fecha peor que la pieza de estado. El que saca de banda vuelve a entrar en el campo
antes de que la parada acabe en las etiquetas, y el de córner se queda junto al banderín después de sacar. Se cierra.

## S9. El paquete «hacia el control»: coste 40 y las posesiones cortas antes de una parada a `D` (regla, antes de medir)

**Por qué.** S1 y S5 dan, cada uno, algo con el control y en SkillCorner y casi nada con el flag. Medidos juntos se
sabe si se suman. No pasa ni pasará §5.8 (no gana con las dos convenciones): es una apuesta de convención, y la
decide Ismael. Esto solo le da el número.

**Qué se mide** (`paquete_control.py`; `D` propio siempre, porque el segundo arreglo toca el `D`):

- versiones: `main`; coste 40; `main` y después las posesiones de menos de 5 s que acaban en un `D` nuestro y vienen
  de un cambio directo pasan a `D` (la variante «a D» de S5); y las dos cosas juntas (el coste 40 y después lo mismo);
- DFL, 7 partidos, las dos condiciones que votan, el balón tapado y a la vista en los `D`, con el flag y con el
  control;
- SkillCorner, mitad de entrenamiento, las dos condiciones que votan allí.

**Regla de lectura, antes de medir (descriptiva).** «Es una apuesta razonable hacia el control» si el paquete gana a
`main` por +0,015 o más en todas las celdas del control y de SkillCorner, y con el flag no pierde más de 0,010 en
ninguna. Si no, se dice qué falla.

## S10. ¿Está el balón de Metrica sample-data pegado al jugador? (regla, antes de medir)

**Por qué.** Bischofberger, Baca y Schikuta (PLOS ONE, 2024) dicen que en los datos de muestra de Metrica el balón
suele ser exactamente la posición del jugador que lo tiene. Si es así, la medida de B5 en Metrica
(`validation/resultados/2026-11-15_metrica.md`) premia por construcción la proximidad, como las etiquetas de control
de la DFL.

**Qué se mide** (`balon_metrica.py`): en los frames de juego con balón, la distancia al jugador más cercano, en
Metrica («tal cual») y en la DFL con el balón limpio (la referencia de un balón medido).

**Regla, antes de medir.** «El balón de Metrica está pegado» si está a menos de 0,3 m del más cercano en el 40 % o más
de los frames de juego con balón y en la DFL limpia en menos de la mitad de esa proporción. Si lo está, la medida de
Metrica no vale como prueba de los rasgos de proximidad y se dice en el documento técnico.

## S10. Resultado [medido]

| datos | a < 0,3 m del más cercano | mediana |
|---|---|---|
| Metrica, los 3 partidos | 45,6 % (54,1 / 52,4 / 32,7 %) | 0,61 m |
| DFL limpia, los 7 | 6,4 % | 1,34 m |

**Con la regla: el balón de Metrica está pegado al jugador.** Confirma lo que dice la fuente. La ventaja de B5 en
Metrica (+0,118 frente al baseline) no prueba nada de los rasgos de proximidad: allí la proximidad acierta por
construcción. Sigue valiendo como prueba de que el pipeline corre con otro proveedor.

## S11. Encoger nuestras paradas (regla, antes de medir)

**La idea.** Con el IoU, una posesión real de L frames sigue emparejada a 0,5 si la alargamos hasta L frames de más,
pero solo si la acortamos hasta L/2. Alargar es el error barato. Si dudamos de un borde de parada, conviene que la
posesión de al lado se coma el borde: empezar el `D` más tarde y acabarlo antes. Además, la pieza de estado acaba las
paradas tarde en la DFL (mediana de +17 frames) y las empieza tarde (+14). Lo primero va en la dirección cara.

**Qué se mide** (`encoger_paradas.py`; DFL, 7 partidos, `main` con su `D` propio, las dos condiciones que votan y el
balón tapado y a la vista en los `D`): cada racha nuestra de `D` que no toca el borde del tramo se encoge: su final se
adelanta f frames (esos frames pasan al equipo de después) y su inicio se retrasa i frames (al equipo de antes), sin
dejarla en menos de 25 frames. Versiones fijadas aquí: (f, i) = (6, 0), (12, 0), (17, 0), (12, 6) y (17, 12).

**Regla de lectura, antes de medir.** «Hay candidato para David, Manuel y Ana» si una misma versión gana a `main` por
+0,010 o más con el flag y con el control, en las dos condiciones y en los dos modos del balón, y en 5 de 7 partidos o
más en cada celda. El número de f se ha sacado de la DFL (la mediana de la pieza de estado), no del partido.

## S9. Resultado [medido]

Diferencia de `spellF1` frente a `main`, con el `D` propio (en cuántos partidos gana):

| etiquetas | balón en los `D` | coste 40 | cortas a `D` | las dos |
|---|---|---|---|---|
| DFL flag | a la vista | −0,004 / −0,005 | +0,004 / +0,004 (5 de 7) | −0,001 / −0,003 |
| DFL flag | tapado | −0,003 / −0,004 | −0,002 / −0,002 | −0,007 / −0,008 |
| DFL control | a la vista | +0,006 / +0,006 | +0,018 / +0,019 (7 de 7) | +0,021 / +0,021 |
| DFL control | tapado | +0,008 / +0,008 | +0,007 / +0,009 | +0,011 / +0,012 |
| SkillCorner | – | +0,007 / +0,007 (10 de 10) | +0,010 / +0,009 (10 de 10) | +0,015 / +0,015 (10 de 10) |

(las dos cifras de cada celda: «como el ATD» y «sin bloques» en la DFL; «detectado» y «detectado, suavizado» en
SkillCorner)

**Con la regla: no es «una apuesta razonable»** tal como se escribió: con el control y el balón tapado el paquete da
+0,011 / +0,012, por debajo de +0,015. Con el flag no pierde más de 0,010 en ninguna celda.

**Lo que enseña [inferencia]:** de las dos partes, la limpia es «cortas a `D`». Gana en SkillCorner en los 10 partidos
de las dos condiciones, con el control en 26 de 28 (7 partidos por dos condiciones y dos modos del balón), y con el
flag se queda entre −0,002 y +0,004. El coste 40 es el que paga con
el flag. Si se quiere apostar por algo, es por «cortas a `D`» sola.

## S11. Resultado [medido]

Encoger nuestras paradas no gana nada: de +0,001 a −0,007 en todas las celdas, y cuanto más se encoge, peor. **Con la
regla: no hay candidato.** [inferencia] El error de los bordes de la pieza de estado no es un sesgo fijo que se pueda
restar: es ancho (del p10 al p90 va de −127 a +116 frames en el inicio), y adelantar un final que ya llegaba a tiempo
cuesta lo que gana con los que llegaban tarde. Se cierra.

## S7b. Las señales de la lista de Ismael que S7 no cribó (regla, antes de medir)

**Por qué.** S7 concluye que las señales de forma son lentas. Lo que podría contradecirlo es **cómo cambia** la forma,
que no se midió. Tampoco se midieron si el receptor frena ni dónde está el balón respecto a cada bloque.

**Señales** (`cribado_senales_2.py`; mismas zonas, mismos números y misma regla que S7; R1 y R3 de referencia):

- S22 el que se abre: la anchura (desviación típica en y, sin el más retrasado) sube en los últimos 2 s más que la del
  otro, con 1 m de margen;
- S23 el que se alarga: lo mismo con la profundidad (en x);
- S24 el que gana área: el área crece en 2 s un 20 % más que la del otro (razón de razones);
- S25 el receptor frena: un jugador a menos de 3 m del balón, que se acerca a él, y cuya velocidad ha bajado más de
  2 m/s en los últimos 12 frames: su equipo;
- S26 el balón dentro de un solo bloque: el balón dentro del rectángulo del p10 al p90 de x e y de los jugadores de
  campo de un equipo y fuera del del otro: el otro equipo tiene el balón.

**No se criban, y por qué:** el balón quieto o junto a un córner, el área pequeña o una línea, y el balón fuera, como
señales de `D`. En la DFL el balón va tapado en los `D` y en SkillCorner las paradas casi no tienen tracking (S4). El
balón fuera ya se probó en el partido (D7, dos versiones apagadas).

**Regla de lectura:** la de S7.

## S7b. Resultado [medido]

«+ B5: Δ en Z1 ∪ Z2», en puntos (salida: `salidas/2026-11-16_s7b_cribado.md`):

| señal | DFL flag | DFL control | DFL control, 4 tarde | SkillCorner | acierta en Z1 (flag) |
|---|---|---|---|---|---|
| S22 el que se abre | +0,70 | −0,03 | +0,13 | −0,05 | 60 % |
| S23 el que se alarga | +0,43 | +0,11 | +0,23 | +0,08 | 30 % |
| S24 el que gana área | −0,01 | +0,07 | −0,02 | −0,00 | 50 % |
| S25 el receptor frena | +0,01 | +0,00 | +0,04 | −0,00 | 49 % (opina en el 1–2 %) |
| S26 el balón dentro de un solo bloque | −0,15 | +0,25 | +0,29 | +0,02 | 69 % (con el signo al revés del previsto en el juego en general) |
| B5 + las cinco | +1,18 | +0,08 | +0,14 | +0,07 | – |

**Con la regla: ninguna añade.**
- **Matiza S7:** el **cambio** de anchura (S22) acierta el 58–60 % dentro de las posesiones que perdemos, frente al
  12–27 % de la anchura fija. La forma que cambia sí dice algo distinto de B5, pero no lo bastante para sumar con el
  control ni en SkillCorner.
- S26 acierta el 14–16 % en el juego en general: el balón dentro del bloque de un equipo suele ser de ese equipo, al
  revés de lo previsto. Dentro de Z1 va al revés de B5, pero tampoco suma.
- S25 casi nunca opina.

---

# Agregados del partido (los ejecuta Ismael; reglas escritas antes)

Encargo de la sesión principal (16/11): hacer las ideas 1.1 y 1.2 del informe. Los scripts leen el partido, así que
**los ejecuta una persona**, y solo imprimen agregados. Claude no ve más que lo que se pegue.

## P1. Los cambios de equipo entre fases del Smart Tagging (idea 1.1; regla, antes de ejecutar)

**Script:** `validation/partido/cambios_entre_fases.py --entrega <la entrega vigente>`. Prueba con un partido
inventado: `validation/scripts/prueba_cambios_entre_fases.py`.

**Qué cuenta:**

- **Las fases de ataque** con `Team` `H` o `A` que empiezan en un tramo evaluado: `BUILD UP`, `PROGRESSION`,
  `CREATING CHANCES`, `LONG BALL` y `ATTACKING TRANSITION`. Las de zona (`BALL IN FINAL THIRD`, `BALL IN THE BOX`,
  `PLAYERS IN THE BOX`) no entran: se solapan con equipos distintos. Las de defensa no hacen falta: salen a pares con
  las de ataque.
- **Un cambio entre fases:** ordenadas por su inicio, una fase de ataque cuyo equipo no es el de la fase de ataque
  anterior del mismo tramo.
- **Se apartan, y se cuentan aparte:**
  - las que son `ATTACKING TRANSITION`: ya las cubre la capa de los contraataques;
  - las de un reinicio: si la fase empieza dentro de una ventana `SET PIECES` o `GOALS`, o si alguna de esas ventanas
    empieza entre 5 s antes del final de la fase anterior (o del inicio de la nueva, si se solapan) y el inicio de la
    nueva;
  - las que tienen, en ese mismo intervalo, un hueco del balón de 5 s o más (125 frames): probable parada.
- **Para cada cambio que queda:** la clase de la entrega en su inicio, como en el §4 de `fases_smart_tagging.py`
  (cambio a ese equipo a ±2 s; ya era ese equipo; era el otro equipo; era `D` o `X`), y cuánto tarda la entrega en
  pasar a ese equipo.
- **Placebo:** los mismos inicios desplazados −480, −360, −240, +240, +360 y +480 s, con el mismo equipo.

**Regla de lectura:**

- **Sigue** (se programa la capa, apagada) si hay **30 cambios o más**, en el **50 % o más** la entrega va con el
  otro equipo y no cambia en 2 s («era el otro equipo»), y en el placebo esa proporción es **la mitad o menos** que en
  los reales.
- **Con menos de 30 no sigue,** pase lo que pase con lo demás. La cota de la DFL con marcas perfectas en el 16 % de los
  cambios dio de +0,013 a +0,016 si caen al azar (`validation/posesiones_cortas/BITACORA.md` §13); con menos marcas, y
  no perfectas, se queda por debajo de +0,01, que no se distingue del ruido. Se apunta el recuento y se cierra.
- **Si no se cumple lo demás, tampoco sigue,** y se apunta qué falló.
- La entrega es la vigente cuando Ismael lo ejecute (`equipo_v5` o `equipo_v8`). El script imprime su sha256.
- Las celdas de 1 a 4 casos salen como «< 5».

**Resultado (16/11; lo ejecutó Ismael con `equipo_v8`, sha256 `d78c514d…ce2b2`)** [medido, agregados del partido]:

- 168 fases de ataque con equipo; 75 cambios de equipo entre fases seguidas. Se apartan 20 por ser contraataques (ya en
  la capa), 23 por un reinicio y 16 por un hueco del balón. **Cuentan 16.**
- En 10 de los 16 (62,5 %) la entrega ya iba con el equipo de la fase; «era el otro equipo» en menos de 5 (18,8 %), frente
  al 25,3 % del placebo.
- **Con la regla: no sigue** (menos de 30 cambios). Tampoco habría seguido con más: la entrega casi nunca llega tarde ahí.
- **Lectura [inferencia]:** fuera de los contraataques, cuando el Smart Tagging cambia de equipo entre fases ya lo hemos
  visto. La idea 1.1 se cierra y no se programa ninguna capa.

**Si sigue, la capa** (antes de generar nada): una función nueva en `possession/transiciones.py`, al lado de
`evidence_equipo`, con el mismo peso (8) y el mismo tope (5 s), solo a la columna del equipo, apagada, con su prueba
con datos inventados. La entrega de prueba se lee con los cuatro criterios de los contraataques
(`docs/decisiones.md`, 15/11), frente a la entrega vigente, escritos antes de generarla. Encenderla lo deciden la
sesión principal e Ismael.

## P2. Los rasgos de B5 en el partido frente a los datos abiertos (idea 1.2; regla, antes de ejecutar)

**Por qué.** B5 se entrenó en la DFL y aguanta en SkillCorner, pero sus rasgos de forma nunca se han mirado en el ATD.
Si un rasgo de peso estuviera desplazado en el partido, B5 empujaría hacia un equipo sin motivo, y ningún sondeo de
datos abiertos lo vería.

**Dos scripts:**

- `validation/investigacion_1116/referencia_rasgos_b5.py` (datos abiertos; lo ejecuta Claude **antes** de que Ismael
  mida el partido y su salida, `referencia_rasgos_b5.json`, se sube con esta regla):
  - los 30 rasgos de B5 (`aprendida.rasgos(trk, "b2")`) en los 7 partidos de la DFL («como el ATD», la condición con
    que se entrenó B5) y en los 10 de `lector.ENTRENAMIENTO` de SkillCorner («detectado»);
  - en los frames de los tramos evaluados con el balón visible en ese frame (así casi todos son de juego en los tres
    conjuntos: en la DFL el balón va tapado en los `D`, en SkillCorner las paradas casi no tienen tracking y en el ATD la
    mayor parte del balón que falta es balón muerto);
  - de cada rasgo, en cada partido, la mediana y el p90 de su **valor absoluto** (los rasgos son «local menos
    visitante»: con el signo, la mediana diría qué equipo domina el partido, no si el tracking es raro);
  - **los diez rasgos de más peso:** los de mayor |peso de B5| × desviación típica del rasgo en la DFL.
- `validation/partido/rasgos_b5.py` (**lo ejecuta Ismael**): lo mismo en el partido, y la comparación con la referencia.
  Imprime, de cada rasgo, la mediana y el p90 del partido frente al mínimo y el máximo de los 17 abiertos. Además, como
  descripción, cuánto coincide el signo de B5 con el del más cercano, en el partido y en los abiertos.

**Regla de lectura:**

- **«Desplazado»:** la mediana del valor absoluto de alguno de los diez rasgos de más peso cae fuera del rango
  (mínimo–máximo) de las medianas de los 17 partidos abiertos.
- **Si hay alguno desplazado,** el siguiente paso es un candidato: estandarizar ese rasgo por partido, medido en datos
  abiertos con su regla antes. Se avisa a la sesión principal antes de escribirlo.
- **Si no hay ninguno,** se apunta que los rasgos de B5 en el partido caen dentro de lo que se ve en los datos abiertos,
  y se cierra.
- **Lo que no separa:** un rasgo puede salir fuera porque el tracking es raro o porque el partido es raro (un equipo que
  domina mucho). Por eso el siguiente paso se mide en datos abiertos y no se decide con esto solo.

**La referencia, calculada antes de que Ismael mida el partido** (`referencia_rasgos_b5.json` y
`salidas/2026-11-16_p2_referencia_rasgos_b5.md`). Los diez de más peso, por este orden: el balón en la dirección de
ataque (ventana 51), la velocidad en la dirección de ataque (25), la dispersión (51), el signo del más cercano (151), el
núcleo de 1 m (151), el de 2,5 m (51), el juego en la dirección de ataque, el núcleo de 6 m (51), la distancia del más
cercano (51) y el núcleo de 1 m (13). El signo de B5 coincide con el del más cercano entre el 76,1 y el 85,1 % de los
frames con balón en los 17.

**Un límite que se ve al calcularla** (no cambia la regla): los cuatro rasgos «sin balón cerca» valen cero en los frames
con balón, así que esta comparación no los mira. Mirarlos pediría los frames sin balón, que en el partido son sobre
todo paradas y en los abiertos no, y no serían comparables.

### P2b. Los slots de más (añadido el 16/11, antes de que Ismael ejecute `rasgos_b5.py`)

**`validation/partido/slots_duplicados.py`, ejecutado por Ismael** (16/11; la salida la pasó la sesión principal), tal
cual:

```
frames_evaluados: 158857
pct_frames_con_un_equipo_de_mas_de_11_slots: 12.86
pct_frames_con_pareja_del_mismo_equipo_a_0.3_m: 1.26
pct_frames_con_balon_con_esa_pareja_a_0.3_m_del_balon_a_6_m: 0.08
pct_frames_con_pareja_del_mismo_equipo_a_0.5_m: 3.47
pct_frames_con_balon_con_esa_pareja_a_0.5_m_del_balon_a_6_m: 0.17
pct_frames_con_pareja_del_mismo_equipo_a_1_m: 12.26
pct_frames_con_balon_con_esa_pareja_a_1_m_del_balon_a_6_m: 0.67
```

**La referencia en datos abiertos** (`slots_abiertos.py`, la misma función `medir`; salida en
`salidas/2026-11-16_p2_slots_abiertos.md`) [medido]:

| medida | partido | DFL (sin duplicados) | SkillCorner, todos | SkillCorner, solo detectados |
|---|---|---|---|---|
| un equipo con más de 11 slots | **12,86 %** | 0,0 % | 0,0 % | 0,0 % |
| pareja del mismo equipo a 0,3 / 0,5 / 1 m | 1,26 / 3,47 / 12,26 % | 0,86 / 3,33 / 12,26 % | 0,62 / 1,57 / 4,91 % | 0,21 / 0,57 / 2,26 % |
| esa pareja a 6 m del balón, a 0,3 / 0,5 / 1 m | 0,08 / 0,17 / 0,67 % | 0,02 / 0,10 / 0,67 % | 0,08 / 0,21 / 0,84 % | 0,06 / 0,16 / 0,70 % |

**Lectura** [medido; lo que dice de la causa es inferencia]:

- **Las parejas del partido son, sobre todo, jugadores de verdad juntos:** la DFL, que no tiene duplicados, da casi lo
  mismo (solo a 0,3 m hay algo más en el partido: 1,26 frente a 0,86 %). Cerca del balón, igual. Los núcleos de B5 casi
  no se tocan.
- **Lo que no tiene ningún abierto es un equipo con más de 11 slots** (12,86 % de los frames). Como no van pegados a
  otro jugador, serán objetos de más asignados a un equipo (alguien fuera del campo, un árbitro, un fantasma)
  [inferencia]. Mueven los rasgos de forma: centroides, dispersión y dirección de ataque.

**Lo que se añade a `rasgos_b5.py` (descriptivo; la regla de P2 no cambia y se decide con todos los frames):** la misma
comparación por separado en los frames con balón con un equipo de más de 11 slots y en el resto, frente al mismo rango.

- Si alguno de los diez sale fuera **solo** en los frames con más de 11 slots y dentro en el resto, el arreglo que se
  propone es quitar los slots sobrantes (un candidato nuevo), no estandarizar.
- Si sale fuera también en el resto, se propone estandarizar, como dice P2.
- En los dos casos se avisa a la sesión principal antes de escribir nada.

### P2. Resultado (16/11; `rasgos_b5.py` lo ejecutó Ismael, con el código de `18f6ff3`) [medido, agregados del partido]

Medianas del valor absoluto, en los frames con balón; entre paréntesis, el rango de los 17 abiertos:

| rasgo (de los diez de más peso) | partido, todos | con un equipo de más de 11 slots (12,8 %) | el resto (87,2 %) |
|---|---|---|---|
| velocidad en la dirección de ataque, ventana 25 (1,716–2,512) | 1,722 | **1,478 fuera** | 1,761 |
| dispersión, ventana 51 (3,703–5,658) | 5,532 | **5,705 fuera** | 5,504 |
| núcleo de 1 m, ventana 13 (0,176–0,298) | **0,167 fuera** | **0,120 fuera** | **0,176 fuera**, en el borde |
| los otros siete | dentro | dentro | dentro |

- Fuera de los diez, también salen bajos el núcleo de 1 m de ventana 1 (0,132 frente a 0,166–0,305) y la velocidad de
  ventana 101 (1,570 frente a 1,599–2,297). El p90 de la dispersión es 12,38, frente a 10,53 como mucho en los abiertos.
- El signo de B5 coincide con el del más cercano en el 75,6 % de los frames con balón; en los abiertos, del 76,1 al
  85,1 % (descriptivo).

**Con la regla de P2: «desplazado»,** por el núcleo de 1 m de ventana 13. **Con P2b:**

- **La velocidad del equipo y la dispersión se salen solo en los frames con más de 11 slots** → el arreglo que se
  propone es quitar los slots sobrantes.
- **El núcleo de 1 m se sale en los dos grupos,** pero en el resto queda justo en el borde (0,176) y donde de verdad cae
  es con más de 11 slots (0,120) → estandarizarlo daría poco; lo que pesa es lo mismo, los slots de más [inferencia].

**¿Lo explica el retraso del balón?** No [medido en la DFL; `salidas/2026-11-16_p2_nucleo_y_retraso.md`]. Con el balón
4 frames tarde, el núcleo de 1 m de ventana 13 **sube** en los 7 partidos (media de 0,207 a 0,248), y el del partido
está por debajo. Queda sin explicar en los frames sin slots de más; puede ser el ruido de posición del ATD a esa escala
[sin verificar].

**Siguiente paso: un candidato, que hay que proponer antes a la sesión principal** (no se escribe nada aún):
1. un agregado del partido que describa los slots de más (dentro o fuera del campo, cerca de una banda, velocidad,
   cuánto duran, de qué equipo), con su regla;
2. una degradación de la DFL que los imite, para medir cuánto pierde B5 con ellos;
3. el arreglo (quitar los sobrantes con una regla fija) medido con esa degradación en el harness, con §5.8.

La sesión principal dio el sí el 16/11, con cuatro condiciones: el paso 1 va en el mismo encargo que P1; el arreglo es
lo más simple que explique lo que se vea, con una regla fija; se mide también el balón muerto (la pieza de estado usa la
velocidad y la dispersión de los jugadores); y la degradación se calibra con el agregado del partido entero, nunca con la
ventana pública.

## P3. Cómo son los slots sobrantes (paso 1 del candidato; regla, antes de ejecutar)

**Script:** `validation/partido/slots_sobrantes.py --entrega <la entrega vigente>` (lo ejecuta Ismael). Prueba con un
partido inventado: `validation/scripts/prueba_slots_sobrantes.py`.

**Qué es un frame «con sobrantes»:** un frame evaluado en que un equipo tiene más de 11 slots a la vez. **El sobrante**
es el slot de ese equipo que lleva menos tiempo visto sin cortarse (el más nuevo): el tracker abre un tracklet nuevo
para lo que acaba de detectar. Si sobran dos o más, se describe solo el más nuevo.

**Qué imprime, solo agregados del partido entero:**

- **Cuántos y cuánto duran:** frames con sobrantes por equipo; cuántos slots tiene el equipo (12, 13, 14 o más); las rachas
  seguidas de frames con sobrantes por duración (menos de 1 s, de 1 a 5 s, de 5 a 30 s, 30 s o más).
- **El sobrante, en los frames con sobrantes:** dónde está respecto a las líneas (más de 3 m fuera, de 1 a 3 m fuera, a
  menos de 1 m de la línea por fuera, a menos de 2 m por dentro, más adentro); su velocidad en 2 s (menos de 0,5 m/s, de
  0,5 a 2, más de 2, sin dato); la distancia al compañero más cercano (menos de 0,5 m, de 0,5 a 1, de 1 a 3, más de 3); la
  distancia al jugador más cercano de cualquier equipo (más de 15 m es «lejos de todos»); la distancia al balón (menos
  de 3 m, de 3 a 10, de 10 a 30, más de 30, sin balón); y cuánto lleva visto (las mismas cuatro duraciones).
- **Sin elegir quién sobra,** como comprobación: en qué parte de los frames con sobrantes tiene el equipo algún slot a más
  de 1 m fuera de las líneas, o una pareja de slots a menos de 0,5 m, frente a los frames en que ese equipo tiene de 9 a 11.
- **El balón muerto:** en qué parte de los frames con sobrantes dice `D` la entrega, frente a todos los frames evaluados.

**Qué arreglo se escribe, decidido antes de ver nada** (el primero que se cumpla):

1. **«Fuera del campo»,** si el sobrante está a más de 1 m fuera de las líneas en el 50 % o más de los frames con
   sobrantes. El arreglo: cuando un equipo tiene más de 11 slots, se quitan sus slots a más de 2 m fuera de las líneas,
   empezando por el más alejado, hasta dejarlo en 11. Los 2 m dejan vivo al que saca de banda, que está justo detrás de la
   línea.
2. **«Duplicado»,** si el sobrante está a menos de 0,5 m de un compañero en el 50 % o más. El arreglo: cuando un equipo
   tiene más de 11 slots, de cada pareja a menos de 0,5 m se quita el más nuevo, hasta dejarlo en 11.
3. **«El más nuevo»,** si no se cumple ninguna. El arreglo: cuando un equipo tiene más de 11 slots, se quitan sus slots más
   nuevos hasta dejarlo en 11.

En los tres, solo se quitan slots de los frames con sobrantes y solo los que sobran: un frame con 11 o menos no cambia. La
elección se apunta aquí, en un commit, antes del paso 2.

**Cómo sigue** (pasos 2 y 3, con su regla escrita después de ver la descripción y antes de medir): una degradación de la
DFL que añade slots como los del partido (la misma proporción de frames, las mismas duraciones, el mismo sitio y la
misma velocidad), cuánto pierde `main` con ella, y el arreglo frente a `main` con §5.8, con las dos convenciones y con
`validation/apuesta_b/d_propio.py`. La degradación se calibra solo con este agregado, nunca con la ventana pública.

### P3. Resultado y elección del arreglo (16/11; lo ejecutó Ismael con `equipo_v8`) [medido, agregados del partido]

- **Cuántos:** 20.425 frames con sobrantes (12,9 % de los evaluados): 12.896 solo del local, 7.504 solo del visitante y 25 de
  los dos. El equipo tiene 12 slots en 18.782, 13 en 876 y 14 o más en 767.
- **Cuánto duran las rachas:** 31 de menos de 1 s (359 frames), 52 de 1 a 5 s (3.041), 42 de 5 a 30 s (11.764) y 5 de 30 s o
  más (5.261).
- **El sobrante (el slot más nuevo), en 20.450 muestras:**
  - dentro del campo: el 84,5 % a más de 2 m de las líneas; solo el 5,5 % a más de 1 m fuera;
  - andando: el 45,1 % entre 0,5 y 2 m/s, el 16,1 % casi quieto, el 17,6 % a más de 2 m/s (sin dato el 21,2 %);
  - no es un duplicado: a menos de 0,5 m de un compañero solo el 1,1 %; a más de 3 m, el 78,6 %;
  - entre los jugadores: el jugador más cercano a menos de 3 m en el 34,1 %, de 3 a 15 m en el 58,8 %, a más de 15 m en el 7,1 %;
  - lejos del balón: de 10 a 30 m en el 32,0 %, a más de 30 m en el 19,0 %, a menos de 10 m en el 8,2 % (sin balón, el 40,9 %);
  - nuevo: lleva visto menos de 1 s el 17,3 %, de 1 a 5 s el 34,6 %, de 5 a 30 s el 42,8 % y 30 s o más el 5,3 %.
- **La comprobación sin elegir quién sobra:** algún slot a más de 1 m fuera en el 6,2 % (2,0 % con 9 a 11 slots); pareja a
  menos de 0,5 m en el 2,0 % (1,6 %). Ni fuera ni duplicados.
- **El balón muerto:** `equipo_v8` dice `D` en el 49,7 % de esos frames, frente al 45,4 % de todos.
- **Con la regla: el arreglo es «el más nuevo».** Cuando un equipo tiene más de 11 slots, se quitan sus slots más nuevos
  hasta dejarlo en 11.
- **Lectura [inferencia]:** algo que se mueve como un jugador, dentro del campo y entre los jugadores pero sin pegarse a
  ninguno, lejos del balón. Encaja con un árbitro asignado a un equipo, o con un jugador del otro equipo con el equipo
  cambiado. No se puede saber sin mirar, y no hace falta para el arreglo.

## P4. El arreglo «el más nuevo», medido en la DFL con una degradación como la del partido (regla, antes de medir)

**El arreglo:** `possession/ball.py`, `clean_slots(trk)`, una función nueva y apagada (no la llama la entrega). En cada
frame en que un equipo tiene más de 11 slots, deja a `NaN` los más nuevos (los que llevan menos frames seguidos vistos;
en un empate, el de índice más alto) hasta dejarlo en 11. No toca el balón, y un frame con 11 o menos no cambia. En el
harness entra como la pieza `ball` (`"piezas": {"ball": "clean_slots"}`), sin tocar `pipeline.py`. Prueba con datos
inventados: `validation/scripts/prueba_slots.py`.

**La degradación** (`slots_dfl.py`), calibrada solo con P3 y con el perfil del ATD:

1. **Tracklets cortados:** el slot de cada jugador real se corta en trozos de duración exponencial con mediana 35,5 s (el «tramo
   p50» del ATD, `validation/resultados/2026-11-14_apuesta_b.md`), y cada trozo pasa a otro slot del mismo equipo. El jugador sigue
   ahí, pero su slot es nuevo. Sin esto, en la DFL el sobrante sería siempre el más nuevo, y el arreglo no se equivocaría
   nunca.
2. **Fantasmas:** rachas de un slot de más hasta cubrir el 12,9 % de los frames de los tramos. La duración de cada racha se
   sortea con las cuatro clases de P3, en la proporción de su número de rachas (31, 52, 42 y 5), y dentro de cada clase
   alrededor de su media (de 1 a 22 frames, de 25 a 92, de 125 a 435 y de 750 a 1.354). Son del local con probabilidad
   0,632 (12.896 frente a 7.504). El fantasma copia la trayectoria de un jugador real de su equipo de entre 3 y 10 minutos
   antes o después: se mueve como un jugador, dentro del campo y sin pegarse a nadie.

Semilla fija. Como comprobación, sin regla, se imprime la descripción de P3 sobre la DFL degradada junto a la del partido.

**Qué se mide** (7 partidos de la DFL; las dos condiciones que votan; las dos convenciones):

- **A:** `main` con los tracklets cortados, sin fantasmas;
- **B:** `main` con tracklets cortados y fantasmas;
- **C:** `main` con `clean_slots`, con tracklets cortados y fantasmas;
- con el `D` de las etiquetas (como el harness, con §5.8) y con el `D` propio, con el balón tapado y a la vista en los `D`;
- en qué parte de los frames con sobrantes quita `clean_slots` justo al fantasma;
- que `clean_slots` no cambia nada sin fantasmas: la DFL sin degradar, la DFL con solo los tracklets cortados y la mitad de
  entrenamiento de SkillCorner tienen que dar las mismas etiquetas que `main`.

**Regla de lectura, antes de medir:**

- **Los fantasmas hacen daño** si B pierde frente a A 0,010 o más en alguna celda (convención × condición × `D`).
- **Si no hacen daño en ninguna, se cierra:** el arreglo no tiene nada que recuperar.
- **El arreglo pasa** si recupera la mitad o más de lo que pierde B en cada celda en que B pierde 0,010 o más, no pierde más
  de 0,005 frente a B en ninguna celda, y no cambia nada sin fantasmas.
- **§5.8 de C frente a B** se imprime y se dice tal cual. Si el arreglo pasa pero no llega a §5.8, decide la sesión principal
  con Ismael si se genera una entrega de prueba.
- **Si pasa,** la entrega de prueba se compara con `equipo_v8` con criterios escritos antes de generarla: cuántos frames
  cambian, de qué etiqueta a cuál y cuántos caen en frames con sobrantes. Encenderlo no es de esta sesión.
