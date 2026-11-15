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
