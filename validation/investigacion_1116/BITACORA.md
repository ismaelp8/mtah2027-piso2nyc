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
