# Investigación del 16/11: qué más se puede hacer para subir la nota

- **Quién y cuándo:** Claude, en una sesión de investigación abierta por la sesión principal de Ismael, la madrugada
  del lunes 16/11/2026.
- **Encargo de Ismael:** «que busque puntos débiles, maneras de mejorar, que investigue […] por internet aportando
  nuevas ideas. Que mas podemos hacer para sacar mayores resultados aun». Ampliado después (también palabras de
  Ismael): cribar a fondo las señales del propio tracking.
- **Regla nº 1 respetada.** No se ha abierto nada del partido: ni el tracking, ni el Smart Tagging, ni el vídeo, ni
  las entregas. Los números del partido que se citan son agregados que ya estaban en el repo.
- **Qué se ha medido:** doce sondeos en datos abiertos de otros partidos, cada uno con su regla de lectura subida
  **antes** de ejecutarlo: los 7 de la Bundesliga (Bassek et al., 2025, CC BY 4.0), la mitad de entrenamiento de
  SkillCorner (`lector.ENTRENAMIENTO`; el examen no se ha tocado) y los 3 de Metrica sample-data. Reglas, scripts,
  salidas y resultados: `validation/investigacion_1116/` (la bitácora es `BITACORA.md`).
- **Qué no se ha cambiado:** nada de `possession/` ni de la entrega.
- **Etiquetas:** [medido] lo he medido en esta sesión o está medido en el repo, y se dice dónde; [fuente] lo dice una
  fuente externa de la sección 7; [inferencia] es una deducción mía; [sin verificar] no lo he podido comprobar.

---

## En pocas líneas

1. **La mayoría de lo que se podía probar barato ya está probado, y ahora también lo nuevo.** He medido doce ideas
   distintas. Ninguna gana a `main` con la regla de §5.8 (+0,03, con las dos convenciones) [medido].
2. **La única mejora medida a favor es pequeña y no pasa sus reglas:** pasar a `D` las posesiones de menos de 5 s
   que acaban en una parada nuestra. Con el balón tapado en los `D`, que es lo más parecido al ATD, da +0,007 / +0,009
   con el control, +0,009 / +0,010 en SkillCorner (gana en los 10 partidos) y −0,002 con el flag [medido, S5 y S9].
   Las dos reglas que escribí antes de medirla dicen «no hay candidato».
3. **Las señales «nuevas» del tracking no añaden nada a B5** [medido, S7 y S7b]. Probé 26 señales (distancias, velocidades,
   formación, el momento del toque, los huecos del balón, el balón muerto). Las que más aciertan en general, como la
   anchura de los equipos (87–91 %), son justo las que fallan donde fallamos (12–27 %): parecen decir el equipo que
   llevaba un rato con el balón [inferencia].
4. **Lo grande no cabe antes del martes:** sacar el balón del vídeo o de la retransmisión. Es lo único que traería
   información nueva sobre los toques, y cuesta días [fuente e inferencia].
5. **Un punto débil nuevo de la validación:** en Metrica el balón va pegado al jugador (a menos de 0,3 m en el 46 % de
   los frames, frente al 6 % en la DFL) [medido, S10]. La ventaja de B5 allí no prueba nada sobre la proximidad.
6. **Nivel honrado:** nada de esta ronda mueve la nota más de lo que el partido mide como ruido (unos 0,04 según
   `EVALUATION.md`). Lo que propongo suma, en el mejor caso, de +0,01 a +0,03, y casi todo depende de la convención.

---

## 1. Las tres que haría primero

> **Actualización (16/11, mañana):** la sesión principal decidió hacer la 1.1 y la 1.2, y dejar la 1.3 en espera. Los
> dos agregados del partido están escritos, con sus reglas antes (P1 y P2 de
> `validation/investigacion_1116/BITACORA.md`): `validation/partido/cambios_entre_fases.py` y
> `validation/partido/rasgos_b5.py`. Los ejecuta Ismael.
>
> **Resultados (16/11):**
> - **1.1, cerrada:** solo 16 cambios entre fases cuentan (se pedían 30), y en 10 la entrega ya iba con ese equipo.
> - **1.2, abrió un candidato y se cerró:** un equipo tiene más de 11 slots en el 12,8 % de los frames con balón (0 % en
>   los datos abiertos), y ahí la velocidad del equipo, la dispersión y el núcleo de 1 m se salen de rango. El sobrante
>   está dentro del campo y se mueve como un jugador (P3). Imitado en la DFL, le cuesta a `main` como mucho 0,008, por
>   debajo del 0,010 de la regla, y quitar el slot más nuevo apenas lo recupera (P4). `ball.clean_slots` se queda apagada.

### 1.1 Los cambios de equipo entre fases del Smart Tagging (ficha 2.2)

- **Qué hacer hoy, lunes:**
  1. **Claude escribe un agregado del partido** (`validation/partido/`), copiando la estructura de
     `fases_smart_tagging.py` §4, con su regla subida antes. Media hora.
  2. **Ismael lo ejecuta.** Cinco minutos; solo imprime recuentos.
  3. **Si pasa su regla, Antonio** (o quien esté) **programa la capa** copiando `transiciones.evidence_equipo`, con el
     mismo peso y tope, y la prueba con los cuatro criterios de los contraataques. Dos horas.
- **Cuánto puede dar:** de 0 a +0,03. Es la única pista nueva sobre el instante de los cambios, que es lo que más
  falla, y se apoya en la única capa que entró de la revisión anterior.

### 1.2 Comprobar en el partido dos supuestos que nadie ha mirado (ficha 2.3)

- **Qué hacer hoy:**
  1. **Ismael ejecuta `validation/partido/slots_duplicados.py`.** Ya existe, y no consta en el repo que se haya
     ejecutado [sin verificar]. Un minuto.
  2. **Claude escribe un agregado** que compare la distribución de los rasgos de B5 en el partido con la de la DFL y
     SkillCorner (solo cuantiles), con su regla. Ismael lo ejecuta.
  3. **Si algún rasgo de peso está fuera de rango,** se mide en datos abiertos una estandarización por partido, sin
     etiquetas, que las reglas permiten (sección 2.3).
- **Cuánto puede dar:** no sube la nota si todo está bien, pero es lo único que puede descubrir una pérdida grande que
  el harness no ve.

### 1.3 Pasar a `D` las posesiones cortas que acaban en una parada nuestra (ficha 2.1)

- **Qué hacer hoy:**
  1. **Ismael decide si quiere apostar por esto.** Falló las dos reglas que escribí antes de medirla; el número que hay
     es pequeño y a favor del control (ficha 2.1).
  2. **Si quiere, una sola prueba de verdad:** la regla fija (5 s, a `D`) en el examen de SkillCorner
     (`lector.EXAMEN`), que nadie ha tocado, con el umbral escrito antes (propongo: +0,005 o más y ganar en 7 de 10).
     **El examen solo se abre con el permiso de Ismael.** Media hora.
  3. **Si pasa, David lo programa** como opción del decodificador (unas 20 líneas después del Viterbi) y Ismael genera
     la entrega de prueba y la compara con `equipo_v5`, con criterios escritos antes (el de más abajo incluido).
- **Cuánto puede dar:** de +0,005 a +0,01 si la GT se parece al control o a SkillCorner; −0,002 si se parece al flag.

**Por qué este orden.** La 1.1 tiene el techo más alto de lo que cabe en un día, y no cuesta nada mirar si hay
algo. La 1.2 es barata y protege la base. La 1.3 es la única con un número medido a favor, pero es pequeño, depende de
la convención y no pasó sus reglas.

---

## 2. Cada idea, con su ficha

### 2.1 Pasar a `D` las posesiones cortas que acaban en una parada nuestra

- **Qué es.** Después del Viterbi: cada posesión de menos de 5 s que viene de un cambio directo desde el otro equipo y
  acaba en un `D` nuestro pasa a `D`. No toca la evidencia ni los costes.
- **Qué fallo arregla.** Uno que vio Ismael en el visionado (hipótesis D2, sin abrir): si nuestro `D` llega tarde, el
  equipo que va a sacar se acerca al balón y le damos una posesión que no existe. Con un F1 sobre posesiones, cada una
  resta dos veces: sobra ella y estropea el final de la anterior.
- **En qué me apoyo** [medido, S5]:
  - En la DFL hay de 108 a 160 de estas posesiones en los 7 partidos. Solo entre el 8 y el 26 % se emparejan con una
    real.
  - De sus frames, entre el 39 y el 58 % son `D` de verdad. Son, sobre todo, un `D` que llega tarde.
- **Cuánto da y de dónde sale** [medido, S9; `D` propio; diferencia frente a `main`]:

  | etiquetas | balón en los `D` | «como el ATD» | «sin bloques» |
  |---|---|---|---|
  | control | a la vista | +0,018 (7 de 7) | +0,019 (7 de 7) |
  | control | tapado | +0,007 (6 de 7) | +0,009 (6 de 7) |
  | flag | a la vista | +0,004 (5 de 7) | +0,004 (5 de 7) |
  | flag | tapado | −0,002 | −0,002 |
  | SkillCorner | – | +0,010 (10 de 10, «detectado») | +0,009 (10 de 10, «suavizado») |

  - **El modo que más se parece al ATD es «tapado».** El ATD pierde el balón en bloques largos, como la DFL con los `D`
    tapados, y en los 10 s antes de cada `SET PIECES` lo ve solo en el 27,6 % de los frames [medido,
    `2026-11-14_perfil_atd.md`]. Las cifras que cuentan son, por tanto, las de «tapado» y SkillCorner: de +0,007 a
    +0,010 con el control y en SkillCorner, y −0,002 con el flag.
  - En el partido espero menos que en el harness, porque el harness sobrestima el nivel [inferencia].
- **Horas:** 1–2 de David, más la entrega de prueba de Ismael.
- **Qué puede salir mal:**
  - Que en el partido estas posesiones sean de verdad: una recuperación justo antes de que el balón salga. Entonces
    quitarlas resta. En la DFL lo son entre el 8 y el 26 % [medido, S5].
  - Que la GT se parezca al flag. Entonces da ±0,003.
  - Que borre lo que crea la capa de los contraataques: una posesión que esa capa adelanta y que acaba en una parada
    nuestra puede caer en la regla.
- **Cómo se valida sin el partido:**
  - ya está medido en datos abiertos (S5 y S9), pero se diseñó y se midió en los mismos partidos;
  - la prueba limpia es una sola ejecución en el examen de SkillCorner, con la regla fija y el umbral escrito antes, si
    Ismael lo permite;
  - en el partido, solo para ver que no se rompe nada, con criterios escritos antes de generar: cuántas posesiones
    quita, que casi todo lo que cambia pase de `H` o `A` a `D`, y **cuántas de las que quita caen en los 5 s de un
    empujón de los contraataques** (si son más de un par, se mira antes de seguir).
- **No pasó sus reglas.** Con la de S5 no hay candidato (con el flag y el balón tapado no gana), y con la de S9 tampoco
  es «una apuesta razonable». Tampoco pasa §5.8: no llega a +0,03 y no gana con el flag. Lo único a su favor es que el
  equipo decidió el 12/11 «exigir control», y SkillCorner, que también exige control, dice lo mismo que el control.
- **Veredicto: quizá; lo decide Ismael.** Si quiere apostar por la convención de control con algo pequeño, que pase
  antes por el examen de SkillCorner.
- **Lo que no haría:** juntarla con subir el coste de cambio a 40. El coste 40 gana algo con el control y en
  SkillCorner (de +0,006 a +0,010), pero pierde con el flag (de −0,002 a −0,005), y el paquete de los dos pierde hasta
  −0,008 con el flag [medido, S1 y S9].

### 2.2 Los cambios de equipo entre fases del Smart Tagging

- **Qué es.** Las fases de ataque del Smart Tagging (`BUILD UP`, `PROGRESSION`, `CREATING CHANCES`, `LONG BALL` y
  `ATTACKING TRANSITION`) llevan el equipo que ataca. Cuando una fase de ataque de un equipo sigue a una del otro,
  su inicio es un candidato a cambio de posesión. Hoy solo se usan las 24 `ATTACKING TRANSITION`.
- **Qué fallo arregla.** El más caro: las posesiones de 2 a 10 s en que decimos el otro equipo. Arreglarlas valdría
  +0,12 con el control y +0,19 en SkillCorner [medido, `2026-11-15_posesiones_cortas.md`, punto 11]. El tracking no
  trae esa información (S7 de esta ronda, fase 3 de las posesiones cortas). El Smart Tagging es la única fuente de fuera
  que la puede traer.
- **En qué me apoyo:**
  - [medido, `2026-11-15_fases_smart_tagging.md`] en control claro, las fases de ataque aciertan el equipo entre el 72
    y el 93 % (`PROGRESSION` 92,0 %, `BUILD UP` 87,8 %, `LONG BALL` 79,9 %). En los contraataques llegábamos de 2 a 10 s
    tarde en 17 de 24, y la capa que lo corrige pasó sus cuatro criterios y está en la entrega.
  - [medido, `validation/posesiones_cortas/BITACORA.md` §13] la cota de la DFL con marcas en los cambios reales: con
    el 16 % de los cambios, perfectas, de +0,013 a +0,027; con 1 s de error y un 90 % de precisión, de +0,009 a +0,019;
    para llegar a +0,03 hace falta el 30 % de los cambios, a 1 s o menos. Ninguna combinación hizo daño.
- **Cuánto puede dar:** de 0 a +0,03 [inferencia sobre esa cota]. Depende de cuántos cambios marquen las fases (hoy
  24, cerca del 16 % de los cambios, según la misma bitácora) y de lo pegados al cambio real que estén.
- **Horas:** media hora el agregado, cinco minutos ejecutarlo, dos horas la capa y su prueba.
- **Qué puede salir mal:**
  - **Las fases no son posesiones** (`DATA.md`). Un `BUILD UP` puede empezar a mitad de una posesión, cuando el portero
    ya llevaba un rato con el balón. Por eso solo cuentan los inicios que **cambian** de equipo respecto a la fase de
    ataque anterior.
  - **Que mida reinicios en vez de cambios.** Tras una parada, la fase nueva puede ser del otro equipo sin que haya
    ningún cambio en juego. Solo cuentan los cambios sin un `SET PIECES` entre las dos fases y sin un hueco del balón de
    5 s o más (el de la capa del hueco).
  - Las fases «de zona» (`BALL IN FINAL THIRD`, `PLAYERS IN THE BOX`, `BALL IN THE BOX`) se solapan con equipos distintos
    [medido]: no entran.
  - Si el inicio de la fase cae varios segundos después del cambio real, la marca empuja tarde. El agregado lo dice.
- **Cómo se valida sin la GT** (la DFL no tiene Smart Tagging; regla a escribir antes de ejecutar):
  - **El agregado:** por cada inicio que cambia de equipo, si nuestra entrega va con el otro equipo y cuánto tarda en
    cambiar, frente a un placebo con las fases desplazadas (como §4 de `fases_smart_tagging.py`).
  - **Regla que propongo:** sigue si, en el 50 % o más de esos inicios, `equipo_v5` va con el otro equipo y no cambia en
    2 s (en el placebo, la mitad o menos de eso), y hay 30 o más.
  - **La capa:** la misma que la de los contraataques (peso 8, 5 s, solo al equipo de la fase), con sus cuatro
    criterios.
- **Veredicto: hacerla ya** el agregado. La capa, solo si el agregado pasa.

### 2.3 Comprobar en el partido dos supuestos frágiles

- **Qué es.** Dos agregados del partido, sin etiquetas:
  1. **Slots duplicados.** Un slot duplicado cuenta doble en los núcleos de B5 (`possession/aprendida.py`,
     `_rasgos_balon`) y en las mayorías. `DATA.md` dice que el ATD duplica a veces a alguien.
     `validation/partido/slots_duplicados.py` lo cuenta; no consta en el repo ningún resultado [sin verificar si se ha
     ejecutado].
  2. **Los rasgos de B5 en el partido frente a la DFL y SkillCorner.** Los de forma (centroides, dispersión, velocidad
     hacia la portería) no están comprobados en el ATD: la regla de traslado del 14/11 era de la pieza de estado
     (revisión externa, punto 10).
- **Actualización (16/11): ya hay un dato** [medido; BITACORA P2b]. Ismael ejecutó `slots_duplicados.py`. Las parejas
  del mismo equipo muy juntas salen como en la DFL, que no tiene duplicados (12,26 % a 1 m en los dos), así que los
  núcleos de B5 casi no se tocan. Pero **un equipo tiene más de 11 slots en el 12,86 % de los frames**, y en los 17
  partidos abiertos, en el 0,0 %. Eso mueve los rasgos de forma. `rasgos_b5.py` separa ahora esos frames del resto.
- **Qué fallo arregla.** Ninguno medido: es lo que el harness no puede ver. Si un rasgo de peso estuviera desplazado
  en el partido, B5 empujaría hacia un equipo sin motivo, y ningún sondeo de datos abiertos lo diría.
- **En qué me apoyo:**
  - [fuente] PathCRF pierde de 8 a 25 puntos de F1 al cambiar de proveedor (apéndice B,
    https://arxiv.org/html/2602.12080).
  - [medido, S7] B5 acierta el 86–90 % de los frames de juego en la DFL y el 84 % en SkillCorner: aguanta un cambio de
    proveedor. La pregunta es si también aguanta el del ATD.
- **Qué hacer si sale desplazado.** Las reglas lo permiten: «Learning without human labels — unsupervised or
  self-supervised methods, or pseudo-labels produced by an algorithm, provided no person decided any of them»
  (`RULES.md`, líneas 67–68). Lo más simple es estandarizar ese rasgo por partido (restar la mediana y dividir por el
  rango intercuartílico, también en el entrenamiento), medido en el harness y en SkillCorner.
- **Lo que no haría:** autoentrenar B5 con las etiquetas que él mismo pone en el partido. Entrenar en SkillCorner con
  sus etiquetas de verdad solo movió 0,519 a 0,520–0,528 [medido, posesiones cortas, punto 7]: unas pseudoetiquetas no
  pueden dar más que eso.
- **Cuánto puede dar:** 0 si todo está bien. Si algo está desplazado, no se sabe.
- **Horas:** una para el agregado de los rasgos, más un minuto para el de los slots.
- **Qué puede salir mal:** que salga un desplazamiento pequeño y nadie sepa si importa. Por eso hay que escribir la
  regla antes: por ejemplo, que la mediana de un rasgo de los diez de más peso caiga fuera del rango de los 17
  partidos abiertos.
- **Veredicto: hacerla ya.** Es barata.

### 2.4 Un modelo no lineal para el estado de `D`

> **Resultado (16/11, Antonio):** se cierra. Con la regla escrita antes de medir (`docs/decisiones.md`, 16/11), ningún
> candidato gana a `main`: G3 (árboles con los rasgos de E3) no llega en 1 de las 8 celdas del harness y G2 en 4. Los dos
> colocan mejor los bordes que E2. Detalle en `validation/resultados/2026-11-16_d_estado_arboles.md`.

- **Qué es.** Cambiar la regresión logística de la pieza de estado (E2) por árboles con *boosting*, con los mismos
  rasgos sin identidad y más ventanas antes y después.
- **Qué fallo arregla.** Los bordes de las paradas, la segunda pérdida: valen de +0,05 a +0,07 en la DFL si se ponen en
  su sitio [medido, `2026-11-15_diagnostico_errores.md`, punto 5]. E2 los acierta a ±1 s en el 35–40 %.
- **En qué me apoyo:**
  - [fuente] Lang et al. (2022), solo con jugadores, en 102 partidos de la Bundesliga: F1 de las paradas de 61,2 con
    regresión logística, 67,9 con *random forest* y 79,8 con AdaBoost. Error mediano de 1,00 s al inicio y de 0,84 s al
    final (https://pmc.ncbi.nlm.nih.gov/articles/PMC9522646/).
  - En contra [medido, `2026-11-14_d_estado.md`]: E3, con ventanas antes y después, empató con E2. Y la logística de
    Lang recibía coordenadas ordenadas por puesto, que una recta aprovecha mal; la nuestra recibe agregados, que ya son
    no lineales [inferencia]. El salto de Lang no tiene por qué repetirse aquí.
- **Cuánto puede dar:** de 0 a +0,02 [inferencia: un tercio de lo que valen los bordes, en el mejor caso].
- **Horas:** 4–6. Además, `scikit-learn` no está en el entorno del equipo, y la entrega solo usa numpy. Habría que
  instalarlo para entrenar (Ismael tiene que decirlo) y escribir la predicción de los árboles en numpy.
- **Qué puede salir mal:** que empate, como E3; y el riesgo de la reproducción si se cuela una dependencia nueva.
- **Cómo se valida:** `validation/scripts/d_estado/medir.py`, dejando un partido fuera, con su criterio del 13/11 y el
  `spellF1` con el `D` propio.
- **Veredicto: quizá,** después de las tres primeras.

### 2.5 El balón del vídeo táctico o de la retransmisión

- **Qué es.** Detectar el balón en el vídeo táctico con un modelo público, o sincronizar el tracking de la
  retransmisión para tener un segundo balón.
- **Qué fallo arregla.** El de fondo: el balón del ATD viene suavizado 1 s y eso borra los toques. Con el balón limpio
  de la DFL, el equipo nuevo está a 1,5 m del balón en el 94 % de los cambios reales; con el suavizado, en el 56–63 %
  [medido, revisión externa, anexo A.4].
- **En qué me apoyo:**
  - [fuente] FootAndBall (licencia MIT, pesos públicos; https://github.com/jac99/FootAndBall) saca un AP de 0,909 en
    ISSIA-CNR, con balones de 8 a 20 píxeles. WASB (https://github.com/nttcom/WASB-SBDT) saca un F1 de 88,3 en fútbol a
    1080p. Ninguno publica el acierto con balones de 4 píxeles, que es lo que mide el balón en el táctico (revisión
    externa).
  - [fuente] No he encontrado ningún método publicado para sincronizar dos trackings del mismo partido sin tiempo
    común. Y la homografía de la retransmisión no vale justo en repeticiones y primeros planos, que es donde están las
    paradas (`DATA.md`).
  - [medido] Con el balón limpio y B5 tal cual, el harness con el `D` propio pasa de 0,416 a 0,443 con el flag y de
    0,616 a 0,659 con el control (revisión externa, anexo A.1). Es la cota de un balón perfecto sin reentrenar.
- **Cuánto puede dar:** como mucho +0,03 / +0,04 con B5 tal cual; más si se reentrena con los toques. Pero solo si el
  detector ve un balón de 4 píxeles, y eso no se puede medir sin mirar el partido frame a frame.
- **Horas:** días. Detectar 199.319 frames son de 1,5 a 38 horas de GPU según el modelo [fuente, cálculo del agente de
  búsqueda, sin verificar]. Hay que añadir `ffmpeg` y un modelo a la reproducción byte a byte, y una inferencia en GPU
  no garantiza el mismo resultado en otra máquina.
- **Veredicto: no antes del martes. Sí para la fase siguiente** (el Innovation Challenge, si se pasa): es lo único que
  trae información nueva.

---

## 3. Cribado de señales del propio tracking (lo pidió Ismael)

**Qué se hizo** (S7 y S7b; reglas en `validation/investigacion_1116/BITACORA.md`, subidas antes de medir). 26 señales nuevas y
3 de referencia, todas sin etiquetas y con umbrales fijados antes. Se miden en los frames donde fallamos: las posesiones
de 2 a 10 s que `main` no ve (Z1) y ±1 s de los cambios reales (Z2). La columna que decide es cuánto sube el acierto en
Z1 ∪ Z2 una regresión con B5 y la señal, fuera de muestra. La regla pedía +1 punto en las cuatro medidas.

| señal | acierta en juego | acierta en Z1 | Δ Z1∪Z2: DFL flag | DFL control | control, balón 4 frames tarde | SkillCorner |
|---|---|---|---|---|---|---|
| R1 el más cercano (N1, ya en B5) | 76 % | 37 % | −0,01 | −0,43 | −0,29 | −0,02 |
| R2 dirección del balón (B9, ya medida) | 73 % | 77 % | **+6,27** | +2,75 | +2,22 | −0,01 |
| S1 diferencia de distancias > 1 m | 81 % | 33 % | +0,04 | −0,17 | −0,11 | +0,29 |
| S3 mayoría a 3 m | 83 % | 36 % | +0,16 | −0,10 | −0,10 | +0,55 |
| S6 llega antes (control del campo) | 80 % | 34 % | −0,05 | +0,08 | +0,24 | +0,39 |
| S8 pegado 12 frames a 2 m (circular con control) | 94 % | 28 % | +0,54 | +0,46 | +0,15 | +0,04 |
| S9 balón lento junto a un jugador | 92 % | 36 % | +0,22 | +0,24 | +0,20 | +0,06 |
| S10 se mueve con el balón | 83 % | 34 % | +0,02 | +0,01 | −0,06 | +0,07 |
| S11 el balón frena junto a un jugador | 84 % | 47 % | +0,65 | +0,50 | +0,57 | +0,39 |
| S13 el más cercano está libre | 83 % | 27 % | −0,07 | −0,01 | −0,01 | +0,34 |
| S14 dos contactos seguidos (circular con control) | 85 % | 54 % | +0,98 | +0,40 | +0,52 | +0,68 |
| S15 el equipo más ancho | 87 % | 14 % | −0,50 | −0,23 | −0,38 | −0,28 |
| S17 el de más área | 84 % | 16 % | −0,26 | +0,10 | −0,02 | −0,19 |
| S18 la línea defensiva más alta | 48 % | 32 % | +0,87 | −0,08 | −0,09 | +0,46 |
| S19 jugadores por detrás del balón | 73 % | 41 % | −0,19 | +0,04 | +0,30 | +0,41 |
| S21 el balón desaparece junto al portero | 83 % | – | +0,05 | +0,00 | +0,00 | +0,01 |
| S22 el equipo que se abre (cambio de anchura en 2 s) | 67 % | 60 % | +0,70 | −0,03 | +0,13 | −0,05 |
| S23 el que se alarga | 51 % | 30 % | +0,43 | +0,11 | +0,23 | +0,08 |
| S24 el que gana área | 69 % | 50 % | −0,01 | +0,07 | −0,02 | −0,00 |
| S25 el receptor frena | 50 % | 49 % | +0,01 | +0,00 | +0,04 | −0,00 |
| S26 el balón dentro de un solo bloque | 16 % | 69 % | −0,15 | +0,25 | +0,29 | +0,02 |
| **B5 + todas a la vez (S1–S21)** | | | +8,20 | +3,74 | +3,68 | +2,08 |

(acierto en juego y en Z1 con el flag de la DFL; la tabla completa, con las 24 señales, cuánto opina cada una, lo que
rescata y lo que estropea, está en `validation/investigacion_1116/salidas/`)

**Lectura** [medido, con la regla]:

- **Ninguna señal añade.** La que más se acerca, «dos contactos seguidos», se queda en +0,98 con el flag y es circular
  con el control.
- **Lo que más acierta en general falla donde fallamos.** La anchura y el área de los equipos aciertan el 84–91 % de los
  frames, más que el más cercano, pero en las posesiones que perdemos aciertan el 12–27 % [medido]. Mi lectura es que
  son señales lentas: un equipo tarda en abrirse más de lo que duran esas posesiones [inferencia]. Lo apoya S22: el
  **cambio** de anchura en 2 s sí acierta el 58–60 % ahí, pero tampoco suma a B5 con el control ni en SkillCorner
  [medido, S7b].
- **Cuidado con la columna de Z1:** Z1 son las posesiones en que B5 falla, así que cualquier señal parecida a B5 sale
  baja ahí por construcción (el propio signo de B5 acierta el 11–19 %). Por eso decide la regresión con B5 dentro, no
  esa columna.
- **Las señales del toque** (balón lento, que se mueve con un jugador, que frena) aciertan mucho cuando opinan (83–93 %),
  pero opinan poco, y casi siempre donde B5 ya acierta.
- **La dirección del balón** es la única que rescata, y solo en la DFL. En SkillCorner no hace nada. Es lo que ya dijo
  B9.
- **La cota** (todas a la vez) es de +2 a +4 puntos de acierto por frame con el control y en SkillCorner [medido].
  Parece del orden de lo que dio la red de una capa de las posesiones cortas, que no movió el `spellF1` [inferencia:
  son medidas distintas].
- **El retraso de 4 frames** no cambia nada.
- **Balón muerto** (D1 a D5, solo jugadores): ninguna pasa. Los jugadores lentos rescatan el 15 % de lo que falla la
  pieza de estado y estropean el 13 %; el frenazo y el arranque colectivos opinan en el 5–7 % de los bordes y aciertan
  el 56–62 %.
- **Fuera tampoco hay más.** El mejor descriptor de forma publicado (Baouan et al., 2025: proyecciones ordenadas de las
  posiciones) acierta el 82 % de los frames solo con la forma, menos que B5 [fuente]. Por lo que enseñan la anchura y el
  área, fallaría en el mismo sitio [inferencia].

**Qué sale de aquí: ningún candidato nuevo de equipo.** Con estas 26 señales no hay más, y ahora está medido de otra
forma que en la fase 3. Mi lectura es que lo que falta está en los toques, que el suavizado borra [inferencia].

**No se han cribado, y por qué:** el balón quieto, junto a un córner, al área pequeña o a una línea, y el balón fuera,
como señales de `D`. En la DFL el balón va tapado en los `D`, y en SkillCorner las paradas casi no tienen tracking (S4).
El balón fuera ya se probó en el partido (D7, dos versiones apagadas). Tampoco el control del campo completo (con
aceleraciones y la superficie entera): se probó su versión simple, el tiempo de llegada al balón (S6).

---

## 4. Las demás preguntas del encargo

**4.1 Cómo se resuelve fuera.**

- Nadie publica posesión de equipo por frame con balón malo y sin identidades. Lo más cercano:
  - TranSPORTmer y su continuación (Peral et al., 2026) recuperan el balón a 2–3 m y aciertan el poseedor en el 82–90 %.
    Pero usan datos privados de LaLiga y reciben como entrada qué equipo ataca: la posesión va dentro [fuente].
  - Ball Radar, PathCRF, ELASTIC: ya estaban en el repo.
- En retos parecidos no he encontrado ninguno de posesión desde tracking. Los que hay son de vídeo (SoccerNet, DFL
  Shootout) [fuente].
- Lo único que se puede montar en un día es lo de la sección 3, y no añade.

**4.2 Decodificar pensando en la métrica** [medido, S1, S2 y S11; fuente].

- **La teoría:** con un F1, añadir una posesión dudosa conviene si la probabilidad de acertarla pasa de F/2 (Lipton et
  al., 2014). Con F = 0,4, el 20 %. Partir una posesión en dos cuenta doble, así que entonces hace falta el 40 %.
- **Medido:**
  - bajar el coste de cambio para meter más posesiones no gana nunca (S1). Los cambios de más que salen aciertan menos
    que F/2, porque la evidencia de las que faltan tiene el signo contrario;
  - el riesgo mínimo con la evidencia de B5 no sirve (S2). Las muestras salen fragmentadas, y la duda del modelo apenas
    tiene que ver con el error real (correlación de 0,09 y 0,14). Ni eligiendo el mejor coste en cada parte con un
    oráculo se llega a +0,03 (+0,006 y +0,013);
  - el IoU castiga menos alargar una posesión que acortarla. Pero encoger nuestras paradas para aprovecharlo no gana
    (S11): el error de sus bordes es ancho, no un sesgo.
- **Fuera:** las mejoras de decodificar mejor son pequeñas en sistemas maduros (del 2 al 3 % relativo en voz, +0,33
  puntos de F1 en entidades). Las grandes de segmentación de acciones vienen de evidencia nueva [fuente].
- **Veredicto: no.** El decodificador no es el cuello de botella; la evidencia sí.

**4.3 Usar lo que no se usa.**

- **Cámara y homografía:** el centro del encuadre explica el balón igual que el centroide de los jugadores y va 0,4 s
  tarde (S3, en SkillCorner). Se cierra.
- **Vídeo y retransmisión:** sección 2.5.
- **Audio:** el sondeo del silbato salió sucio (14/11). Fuera, la receta que funciona combina la banda de 3,5 a 4,5 kHz
  con la entropía del espectro (93 % de exhaustividad y 88 % de precisión en 5 partidos) [fuente]. Si Antonio quiere
  repetirlo, es esa receta. Solo arreglaría el inicio de las faltas y los fueras de juego, y mete `ffmpeg` en la
  reproducción. Quizá, después.

**4.4 Adaptarse al partido sin etiquetas.** Sección 2.3. Las reglas lo permiten (`RULES.md`, líneas 67–68). El techo
medido de entrenar «en casa» es de +0,001 a +0,009 en SkillCorner con las etiquetas de verdad, así que el
autoentrenamiento no vale la pena. Una estandarización por partido sí, si se ve un desplazamiento.

**4.5 El balón muerto** [medido, S4, S6, S7, S8 y S11].

- No hay datos abiertos con el balón visible antes de los saques: en SkillCorner solo 133 de 1.019 paradas tienen
  tracking (S4); en Metrica el balón se ve antes del saque en 2 de 210 (S6); en la DFL va tapado. Los bordes con el
  balón solo se pueden probar en el partido, con agregados y placebo.
- Con los jugadores no hay más: la geometría del saque fecha el final peor que la pieza de estado (S8), y las señales
  colectivas no pasan (S7).
- Los 4,5 s de adelanto en los saques de puerta siguen sin arreglo. La pieza de estado da el juego por reanudado porque
  los jugadores ya se mueven [inferencia del equipo]. Lo único que lo arreglaría es el instante del golpeo, que necesita
  el balón.
- La sección 2.4 es lo único con recorrido.

---

## 5. Puntos débiles que nadie había mirado

1. **El balón de Metrica sample-data va pegado al jugador** [medido, S10; fuente: Bischofberger et al., 2024]. Está a
   menos de 0,3 m del más cercano en el 45,6 % de los frames de juego con balón; en la DFL limpia, en el 6,4 %. La
   ventaja de B5 en Metrica (+0,118 frente al baseline) no prueba nada de los rasgos de proximidad. Hay que decirlo en el
   documento técnico.
2. **La DFL y SkillCorner no están de acuerdo con las señales del movimiento del balón** [medido, S7]. La dirección del
   balón rescata +6 puntos en la DFL y nada en SkillCorner, igual que B9. Cualquier rasgo que use la dinámica del balón
   tiene que pasar por SkillCorner antes de creérselo. Ya se hizo con B9; conviene que sea norma.
3. **El veto del flag frena mejoras que van en la dirección que el equipo decidió** [medido, S1, S5 y S9]. Tres cambios
   distintos (coste 40, «cortas a `D`», el paquete) ganan con el control y en SkillCorner y empatan o pierden poco con el
   flag. La regla de §5.8 no deja entrar ninguno. El equipo decidió el 12/11 «exigir control». Decidir si el flag tiene
   veto o solo un límite de daño es de Ismael, y conviene hacerlo **antes** de medir más cosas.
4. **Los slots duplicados y los rasgos de forma de B5 nunca se han mirado en el partido** (sección 2.3).
5. **No hay forma de validar los bordes del `D` con el balón fuera del partido** (sección 4.5). Lo que se haga ahí entra
   con reglas y agregados, como la capa del hueco y D7.
6. **En el código de `possession/` no he encontrado nada nuevo que rompa la entrega.** Lo que vi ya está apuntado: la
   cuenta doble de los slots duplicados y las escalas acopladas de las capas (revisión externa, punto 4).

---

## 6. Lo que se descarta, y por qué (una línea cada una)

**Medido en esta ronda:**

- Bajar el coste de cambio para meter más posesiones: no gana con ninguna convención (S1).
- Subir el coste a 40: gana poco con el control y en SkillCorner y pierde con el flag (S1 y S9).
- Decodificar a riesgo mínimo con la evidencia de B5: las muestras se fragmentan y la duda no dice dónde fallamos (S2).
- Elegir el coste por parte: ni con un oráculo pasa de +0,013 (S2).
- El encuadre de la cámara como sustituto del balón: es el centroide de los jugadores, con retraso (S3).
- SkillCorner para validar los bordes de las paradas: solo 133 paradas con tracking (S4).
- Metrica para validar el arranque del balón: el balón no se ve antes del saque (S6).
- 26 señales del tracking (distancias, velocidades, formación y su cambio, toque, huecos) y 5 de balón muerto: ninguna añade (S7 y S7b).
- El final de la parada por la geometría del saque de banda o de córner: peor que la pieza de estado (S8).
- Encoger nuestras paradas, porque alargar una posesión es el error barato: empata o resta (S11).

**Leído fuera:**

- TranSPORTmer y Peral et al.: datos privados, sin código, y reciben quién ataca como entrada.
- El descriptor de forma de Baouan et al.: acierta menos que B5, y la forma es lenta (S7).
- Sincronizar la retransmisión: no hay método publicado, y falta homografía justo en las paradas.
- Paradas desde los planos de la retransmisión (Xie et al.): solo el 62 % de los bordes a ±3 s.
- Autoentrenamiento y corrección de priors en el partido: el techo con etiquetas de verdad ya es de +0,001 a +0,009.
- Deshacer el suavizado del balón: no se puede validar (en el harness el núcleo es exacto), y la cota de un balón
  perfecto con B5 tal cual es de +0,03 / +0,04.
- Posprocesos de segmentación de acciones (ASRF, FIFA): arreglan lo contrario, el exceso de cortes.

**Ya probado antes, para que no vuelva como nuevo:** N2, retención, B1 a B9, la red de una capa, entrenar con
SkillCorner, proponer y clasificar trozos, costes 12 y 50, duración mínima y poda, prior de reinicio, ancla de
retención, evento de toque (B8), costes del `D` con el `D` propio, el instante fijo del reinicio, el balón fuera (D7, dos
versiones), el silbato (sucio), el retraso del balón (4 frames, empate), la limpieza del balón (empate) y las fases como
pista de equipo sin balón (vale poco). Todo en `docs/decisiones.md`.

---

## 7. Fuentes

Las leyeron los agentes de búsqueda de esta sesión salvo donde dice «resumen»; las cifras se han copiado de sus
informes y pueden tener erratas de lectura.

- Lang et al. (2022), estado del juego solo con jugadores: https://pmc.ncbi.nlm.nih.gov/articles/PMC9522646/
- Vidal-Codina et al. (2022), tipo de reinicio por geometría: https://arxiv.org/abs/2202.00804
- Lipton, Elkan y Narayanaswamy (2014), umbral óptimo para F1: https://arxiv.org/abs/1402.1892
- Mangu, Brill y Stolcke (2000), consenso y escala de las puntuaciones: https://arxiv.org/abs/cs/0010012
- Jagannatha y Yu (2020), calibrar segmentos: https://arxiv.org/abs/2004.04361
- ASRF (Ishikawa et al.): https://arxiv.org/abs/2007.06866 · FIFA (Souri et al.): https://arxiv.org/abs/2108.03894
- Baouan, Rosenbaum y Pulido (2025), posesión desde la forma: https://arxiv.org/abs/2501.10299
- TranSPORTmer: https://arxiv.org/abs/2410.17785 · Peral et al. (2026): https://arxiv.org/abs/2512.19528
- Bischofberger, Baca y Schikuta (2024), eventos desde tracking y el balón de Metrica:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11025972/
- PathCRF, apéndice B (cambio de proveedor): https://arxiv.org/html/2602.12080
- FootAndBall: https://arxiv.org/abs/1912.05445 y https://github.com/jac99/FootAndBall
- WASB: https://arxiv.org/abs/2311.05237 y https://github.com/nttcom/WASB-SBDT
- Silbato (banda y entropía del espectro): https://arxiv.org/abs/1411.6496
- Xie et al., juego y paradas desde los planos: https://www.ee.columbia.edu/ln/dvmm/publications/02/icassp02_xlx.pdf
- ELASTIC, sincronizar eventos y tracking: https://arxiv.org/abs/2508.09238
- Alexandari et al., corrección de priors por EM: https://arxiv.org/abs/1901.06852
- Duraciones de las paradas en la Premier League 2025-26: https://theanalyst.com/articles/premier-league-football-time-throw-ins-goal-kicks-substitutions-stats
- PFF FC, Mundial 2022 (licencia sin aclarar; no se ha descargado): https://kloppy.pysport.org/user-guide/loading-data/pff/
- Johnson y Willsky, duraciones explícitas (resumen): https://arxiv.org/abs/1203.1365
- Filtro de tendencia L1 (resumen): https://web.stanford.edu/~boyd/papers/l1_trend_filter.html

## 8. Lo que no he podido comprobar

- Nada del partido. Las ideas 2.1, 2.2 y 2.3 necesitan que Ismael ejecute algo.
- Las cifras de las fuentes vienen de los informes de los agentes de búsqueda; no he releído los artículos.
- Los sondeos miden en datos abiertos con el harness, que sobrestima el nivel (revisión externa, punto 7). Las
  diferencias pequeñas pueden no repetirse en el partido.
- El cribado de señales mide acierto por frame, no `spellF1`.
