# Posesión del balón frame a frame: documento técnico

**Equipo:** [PENDIENTE: `<NOMBRE_EQUIPO>`, el mismo que puso cada uno al inscribirse]
**Entrega:** `<NOMBRE_EQUIPO>.csv`, hoy igual byte a byte a nuestra versión interna `equipo_v9` (sha256
`d9706dfb4b5389d391146d5d7efd022f01aa2a427d3e61f7ab2c06b3ecccbe63`). [PENDIENTE: sha256 final si la
entrega cambia antes del cierre, por ejemplo si se enciende K2 (§8)]
[PENDIENTE: idioma del documento, que decide el equipo; si se queda en español, un resumen en inglés de unas
150 palabras al principio]

> Etiquetas: **[medido]** es una medida; **[inferencia]** es una conclusión razonada que no se ha medido;
> **[sin verificar]** es algo que no hemos podido comprobar. Lo que no lleva etiqueta describe el código o
> una regla nuestra. Del partido solo damos agregados (recuentos y porcentajes); los únicos números de frame
> que aparecen son los oficiales (`games.py`, `DATA.md`, `FAQ.md`).

> **Términos.** **La DFL:** el dataset abierto de 7 partidos de la Bundesliga de Bassek et al. (2025) (§5).
> **El flag:** su etiqueta de posesión por frame (`BallPossession`), que cambia en el primer toque del rival
> aunque no controle. **Control:** esas etiquetas corregidas para exigir control (§3). **Harness:** nuestro
> banco de pruebas en esos 7 partidos; corre las piezas de la entrega que no dependen del Smart Tagging ni
> del balón fuera y las puntúa con el scorer oficial (§6.1). **«Como el ATD»:** el balón de la DFL degradado
> para parecerse al del partido, con huecos y suavizado. **`D` oráculo:** el `D` copiado de las etiquetas,
> para medir solo `H` frente a `A`. **Pliegue:** cada uno de los 7 entrenamientos que dejan fuera un partido.

## 0. Resumen

**Qué entregamos.** Un CSV `frame,label` de 199.319 filas que da `H`, `A` o `D` en cada frame de los dos
tramos evaluados y `X` fuera de ellos. Lo genera un solo comando, solo con numpy, a partir del tracking
automático (ATD) y del Smart Tagging del partido.

**El método en un párrafo.** Cada pieza da, en cada frame, una puntuación para `H`, `A` y `D`. Las
puntuaciones se suman y un decodificador de Viterbi elige la secuencia con más puntuación, pagando un coste
fijo por cada cambio de estado. La evidencia de equipo es una regresión logística (B5) entrenada en la DFL
con proximidad al balón y forma de los equipos. El estado de `D` es otra regresión logística (E2) que solo
mira a los jugadores. Se añaden cuatro capas pequeñas: el tramo antes del saque de la 2ª parte, el hueco sin
balón (de 5 a 60 s) antes de cada reinicio del Smart Tagging que no es un saque inicial, los contraataques
del Smart Tagging y el balón visto fuera del campo. Al final, una regla pasa a `D` las posesiones de menos de
5 s que llegan con un cambio directo desde el otro equipo y acaban en una parada («cortas a `D`»).

**Por qué así.** No hay etiquetas del partido que se puedan usar, y la ventana pública no sirve para elegir
(§6.5). Por eso todo se eligió en partidos abiertos de otras ligas, con piezas pequeñas que se miden por
separado. Cada pieza entró por una regla escrita antes (§6.1). B5 y E2 ganaron en el harness. «Cortas a `D`»
entró por una regla de límite de daño: gana con control en la DFL y en SkillCorner y no pierde más de 0,005 con
el flag. Esa regla se escribió cuando ya se conocían sus cifras en la DFL; a ciegas solo estaban el examen de
SkillCorner y la entrega de prueba. Tres capas que el harness no puede medir entraron por reglas de daño, con
agregados del partido (§8).

**La validación, en datos de otros partidos** (spellF1). Estas tres cifras miden solo `H` frente a `A`,
porque usan el `D` oráculo:
- DFL, balón «como el ATD»: **0,498** frente a 0,406 del baseline con el flag, y **0,728** frente a 0,464
  con control; gana en 7 de 7 [medido].
- SkillCorner (20 partidos, tracking automático de retransmisión): **+0,131** sobre el baseline, en 20 de 20
  [medido].
- Metrica (3 partidos): **+0,118** sobre el baseline, en 3 de 3 [medido].

Con nuestro propio `D` bajan a 0,414 (flag) y 0,623 (control) en la DFL, frente a 0,310 y 0,353 del baseline
(§6.2) [medido]. En SkillCorner bajan a 0,381, frente a 0,249; esa cifra es de antes de «cortas a `D`», que allí
suma de +0,008 a +0,010 (§6.3) [medido].

**Qué nivel cabe esperar.** Entre **0,33 y 0,51** de spellF1 en el partido, con unos **0,39** como punto
central [inferencia]. El número del harness es optimista (§6.6).

## 1. El problema y lo que manda el diseño

La nota es el spellF1: cada posesión es un objeto, se empareja una a una con las reales por IoU temporal y se
promedia el F1 con umbrales de 0,3 a 0,7 (`EVALUATION.md`). De ahí salen dos consecuencias:

- **Fragmentar es lo peor:** cada posesión inventada es un falso positivo. El baseline sin suavizar inventa
  muchísimas y saca 0,049 en el partido.
- **Un cambio desplazado baja el IoU de las dos posesiones que separa.** La tabla oficial de retrasos lo
  ilustra (8 frames: 0,89; 1 s: 0,65); solo la usamos para describir (§10).

Por eso la salida no es un voto frame a frame, sino un **decodificador temporal** que ve la evidencia de los
dos lados de cada cambio y lo coloca donde la evidencia lo pide, con un coste por cambio que hace de
histéresis.

La dificultad central es el balón del ATD: falta en el 40,7 % de los frames evaluados (`DATA.md`: se ve en
94.214 de 158.857), y viene suavizado unos 25 frames y retrasado unos 4 respecto a los jugadores [medido,
agregados del partido]. Por eso casi nada se apoya en cambios bruscos de la velocidad del balón.

## 2. El enfoque, pieza a pieza

Todas las piezas cumplen el mismo contrato (`possession/tracking.py`): reciben un `Tracking` (arrays
indexados por frame de vídeo, en metros, con 46 slots sin identidad y su equipo) y devuelven
`(score, allowed)`, dos arrays (n, 3) con columnas `H`, `A`, `D`. `score` se suma; `allowed = False` prohíbe
un estado y se reserva para lo que se sabe seguro. Así el código que se mide en datos abiertos es el mismo que
se entrega.

Cadena de la entrega (`possession/pipeline.py`), en este orden:

| # | pieza | qué aporta | constantes clave |
|---|---|---|---|
| 0 | lector del ATD y `ball.clean` | balón y jugadores en metros; la limpieza es la v0 (deja el balón tal cual) | campo 105,3 × 68,0 m |
| 1 | equipo, B5 (`aprendida.evidence_b5`) | −round(α·\|z\|, 6) al equipo que el modelo no da como poseedor (z = logit de `H` frente a `A`); +1 al equipo del jugador más cercano si se ve el balón | α = 4; 30 rasgos |
| 2 | estado de `D`, E2 (`dead_state.evidence`) | log-odds de «juego parado» en la columna `D` | recorte ±8; escala 1 |
| 3 | anclas de `D` (`dead_ball.evidence`) | solo `D` en los 2.934 frames antes del saque de la 2ª parte; `D` prohibido en el frame del saque de cada parte; +1 en `D` en el hueco sin balón de 5 a 60 s antes de cada reinicio que no es saque inicial | 5 s y 60 s; `GAP_SCORE` = 1 |
| 4 | contraataques (`transiciones.evidence_equipo`) | +8 por frame al equipo de cada «Attacking Transition», 5 s | `WEIGHT` = 8; `CAP_S` = 5 |
| 5 | balón fuera (`dead_ball.ball_out`) | +5 en `D` con el balón visto a más de 1 m fuera | 1 m; cola de 16 frames |
| 6 | decodificador (`temporal.decode_cortas_a_d`) | Viterbi sobre {`H`, `A`, `D`}, por tramo; después, «cortas a `D`»: pasa a `D` las posesiones cortas que llegan con un cambio directo desde el otro equipo y acaban en `D` | 25 por cada cambio; corte de 125 frames (5 s) |

**B5, evidencia de equipo.** Regresión logística de `H` frente a `A` con 30 rasgos «local menos visitante»,
sin término independiente ni identidad de slot: 20 del balón (qué equipo tiene al más cercano, núcleos
gaussianos de 1, 2,5 y 6 m y distancia del más cercano con tope de 15 m, en ventanas de 1, 13, 51 y 151
frames) y 10 de los jugadores (posición del juego y del balón en la dirección de ataque, velocidad hacia
delante y dispersión; cuatro de ellos repetidos solo sin balón cerca). Por qué así:
- solo decide entre `H` y `A`: en la DFL el balón se tapa en los `D`, y un `D` aprendido allí sería «sin
  balón = `D`»;
- simétrica, para no aprender la ventaja de campo de siete partidos de otra liga;
- castiga al equipo que el modelo no da y suma el +1 del más cercano: la versión que premiaba (B2) empujaba
  hacia un equipo en las paradas y solo veía el 31,6 % de ellas, y sin el +1 (B4) decía `D` de más [medido];
- coeficientes escritos en el módulo, para que el pipeline solo dependa de numpy.

**E2, estado de `D`.** Regresión logística con 11 agregados de los jugadores (velocidades, jugadores casi
parados, fuera de las líneas o en un área, distancia entre equipos, dispersión y cuántos están en su mitad).
No usa el balón: en la DFL va tapado en los `D`, y en el ATD que falte no significa `D`. Da el estado, no el
instante: las fronteras las pone el decodificador.

**Anclas de `D`.** Los 2.934 frames entre el primer frame evaluado de la 2ª parte (110.808) y su saque
(113.742) son `D` según el FAQ y se fuerzan a `D`; en la 1ª parte el primer frame evaluado ya es el saque.
Los saques salen de las constantes oficiales (§10), no de un detector: buscar el golpeo con el balón del ATD
no lo encontró en ninguno de los 6 saques de centro que marca el Smart Tagging [medido]. El hueco antes del
reinicio solo puntúa: «sin balón = `D`» se descartó porque mete retraso y parpadeo [medido].

**Contraataques.** El equipo de las «Attacking Transition» coincide con el que controla el balón en el
93,1 % de los frames de control claro según el balón del ATD, y en 17 de los 24 contraataques nuestra
etiqueta pasaba a ese equipo de 2 a 10 s después del inicio de la fase del Smart Tagging [medido, agregados
del partido, sin GT]. El 8 y los 5 s se fijaron antes con una simulación en la DFL (una pista perfecta que
marca los contraataques, con peso 8 y un máximo de 5 s) y no se retocaron.

**Balón fuera.** En SkillCorner un balón visto fuera es `D` el 93–94 % de las veces; con una versión
anterior de la entrega decíamos `H` o `A` en el 36 % de esos frames del partido [medido]. La prueba se abrió
tras el visionado de la ventana pública (§10); la tarea ya estaba en el plan. El peso 5 se razonó con el
juego vivo típico de la DFL (mediana de E2) y la cola de 16 frames con el suavizado (12) y el retraso (4) del
balón del ATD.

**Decodificador.** Viterbi en cada tramo evaluado, con costes `H`↔`A`, a `D` y desde `D` de 25. El coste 25
no está ajustado: con B5, 12 y 50 empatan con él según la regla de §6.1 (con el flag 50 pierde un poco y 12
empata; con control 50 gana un poco y 12 pierde), y con un empate se queda lo que hay [medido].

**Cortas a `D`.** Después del Viterbi, en cada tramo, una posesión de menos de 125 frames que llega con un
cambio directo desde el otro equipo y acaba en `D` pasa a `D`. No se toca si `D` está prohibido en alguno de sus
frames (el del saque de cada parte). Solo puede pasar frames de un equipo a `D`. El fallo que ataca: si nuestro
`D` llega tarde, el equipo que va a sacar se acerca al balón y le damos una posesión que no existe; con un F1
sobre posesiones, resta dos veces, porque sobra ella y estropea el final de la anterior. En la DFL hay de 108 a
160 posesiones así en los 7 partidos; solo del 8 al 26 % se emparejan con una real, y del 39 al 58 % de sus
frames son `D` de verdad [medido]. Entró por la regla de límite de daño (§6.1), con el `D` propio [medido]:
- DFL con control: de +0,007 a +0,019, ganando en 6 o 7 de 7 partidos en cada celda;
- SkillCorner: +0,010 y +0,009 en la mitad de entrenamiento, y +0,009 y +0,008 en la de examen, en 10 de 10;
- DFL con el flag: de −0,002 a +0,004; la peor celda pierde 0,0024, dentro del límite de 0,005.

El corte de 5 s viene de la regla del sondeo que la propuso, escrita antes de medir; no se compararon cortes
para elegirlo (§8).

**Tracking que falta o con ruido.** Sin balón, B5 opina con la forma de los equipos y con ventanas largas, y
el decodificador mantiene el estado salvo que la evidencia pague el cambio. Los slots se tratan sin identidad.
El ATD se comprueba al leerlo y cualquier línea rara para la entrega.

## 3. Las reglas de posesión implementadas

- **Balón suelto o disputado.** La posesión sigue con el último equipo que la tuvo. No hay ninguna regla
  explícita de «último toque»: el coste de cambio exige evidencia sostenida del rival para cambiar, y un
  toque aislado no la da.
- **Toques sin control y desvíos.** Hemos elegido **exigir control**, como dice `CHALLENGE.md`. El flag
  cambia en el primer toque del rival aunque no controle (en el 72–85 % de esos casos [medido]). Por eso B5
  se entrenó solo donde el flag coincide con una corrección por control (una racha del rival que no sigue a
  un `D` se queda solo si el mismo jugador está a 1 m o menos durante 12 frames, o si su equipo encadena dos
  toques en 2 s).
- **Duelos aéreos ganados sin control.** No hay regla propia: sin retención o encadenamiento del rival no
  hay evidencia sostenida para pagar el cambio [inferencia].
- **Balón muerto y reinicios.** `D` sale de la suma de E2 (jugadores parados o fuera de sitio), el balón
  visto fuera, el hueco sin balón de 5 a 60 s antes de cada reinicio del Smart Tagging que no es un saque
  inicial, y el tramo antes del saque de la 2ª parte. Una parada solo se crea si la evidencia paga dos
  cambios de 25. El equipo que reanuda no se arrastra a través de la parada: en el partido J03WMX de la DFL
  cambia en el 90 % de ellas [medido, un solo partido]. Tras un reinicio, la posesión es del equipo que la
  evidencia da después.
- **Posesión corta justo antes de una parada.** Si una posesión de menos de 5 s llega con un cambio directo
  desde el otro equipo y acaba en `D`, se escribe `D` («cortas a `D`», §2): ese cambio se trata como un `D` que
  pusimos tarde, no como un control del rival. No crea paradas nuevas: alarga hacia atrás una que ya existe.
- **La `X`.** Solo fuera de los tramos evaluados (40.462 frames). Dentro, siempre `H`, `A` o `D`, también en
  oclusiones largas: el scorer rellena la `X` con la etiqueta anterior para el spellF1 y la cuenta como fallo
  en el macroF1, así que nunca gana.

## 4. Datos usados y descartados

**Del partido.**

| fuente | uso |
|---|---|
| ATD táctico (tracking y metadatos) | entrada principal. 199.319 líneas, todas válidas [medido] |
| Smart Tagging | `SET PIECES` para el hueco antes del reinicio; «Attacking Transition» con su `Team` para los contraataques. Nunca prohíbe nada ni se copia como etiqueta, pero en los 5 primeros segundos de cada contraataque el empujón (8 por frame, 1.000 frente a un coste de cambio de 25) fuerza el cambio al equipo de la fase, salvo que B5 diga con mucha fuerza lo contrario [inferencia, por construcción] |
| constantes de saque (`starter/load_smart_tagging.py`) | anclas de `D` (§2) |
| GT pública (5 min) | comprobar formato y alineación y, como pide `CHALLENGE.md` («Use it to understand what is expected»), entender qué significan las etiquetas (§6.5 y §10). No entrenó, no fijó ningún parámetro y no eligió ninguna versión |
| vídeo táctico | lo miraron personas para entender el juego y la GT pública (§10). Además, un detector de balón automático lo procesó en local, primero en una muestra de 10 minutos y después en el partido entero, para la línea del balón del vídeo, que se descartó (§7) |
| homografía | no la usa la entrega. La usó la línea del balón del vídeo, descartada (§7), para llevar las detecciones al campo y medir el balón en píxeles |
| broadcast | descartado: no está sincronizado, no hay herramienta pública para alinearlo y su homografía solo vale en el 65,8 % |
| audio (silbato) | sondeado y descartado: no pasó su criterio porque la señal sale sucia [sin verificar: el resultado no quedó escrito en `validation/silbato/`] |

Algunos valores salen de agregados del partido, sin ninguna etiqueta: el umbral de 5 s de los huecos largos,
la cola de 16 frames del balón fuera y la degradación «como el ATD», que salen del perfil del balón del ATD
(suavizado de unos 25 frames y retraso de unos 4). Además, las capas del hueco antes del reinicio, de los contraataques y del balón fuera entraron con recuentos
del partido, frente a reglas de daño escritas antes de medir (§8), y «cortas a `D`» cerró así el último punto de
su regla, con una entrega de prueba (§6.1). Nada de esto está ligado a frames
concretos ni sale de la ventana pública. `RULES.md` permite «inspecting the data to understand them, debug
your pipeline and design features» y prohíbe convertir lo visto en «labels, corrections, or rules and
constants tied to specific frames of the game». Lo declaramos para que la organización lo pueda juzgar.

**Abiertos, de otros partidos.**

| dataset | uso |
|---|---|
| Bundesliga, Bassek et al. (2025), 7 partidos | entrenamiento de B5 y E2 y harness (§5, §6) |
| SkillCorner Open Data, 20 partidos de la A-League 2024/25 | solo validación. La medida de §6.3 usa los 20. Después se apartaron 10 como examen, que cada candidato abre una sola vez, con el umbral escrito antes. Lo abrieron «cortas a `D`» (pasa y está en la entrega), K2 (pasa y está apagado, §8) y B12 (no pasa, §7) |
| Metrica sample-data, 3 partidos | solo validación |
| dataset del detector de balón (Roboflow, clips de la Bundesliga, CC BY 4.0) | solo para medir el detector de la línea del vídeo (125 imágenes de su parte de test; §7). No entrena nada nuestro |
| StatsBomb, Wyscout, SoccerNet, PFF FC y otros | inventariados o descartados: licencia dudosa, sin balón medido o sin aportar nada a lo anterior |

No se usa ningún dato humano de este partido (Opta, StatsBomb, Wyscout, LaLiga…), ni agregados de la
temporada 2024-25.

## 5. Datos de entrenamiento

Solo dos piezas están entrenadas, y las dos con el **mismo dataset**. El detector de balón que se probó para la
línea del vídeo no entra en la entrega (§7).

- **Fuente:** Bassek, Rein, Weber y Memmert (2025), *An integrated dataset of spatiotemporal and event data
  in elite soccer*, Scientific Data 12, 195. Licencia CC BY 4.0, con autorización de la DFL.
- **Contenido:** 7 partidos de 1ª y 2ª Bundesliga 2022-23, tracking TRACAB a 25 Hz revisado por operadores,
  1.002.644 frames [medido], con `BallStatus` (vivo o muerto) y `BallPossession` en cada frame.
- **Quién etiquetó:** el proveedor; las etiquetas por frame vienen con el tracking revisado, pero cómo genera
  la DFL esos flags no está documentado [sin verificar]. Las de control las deriva nuestro código.

**B5.** Etiqueta: el flag, solo en frames vivos donde coincide con la corrección por control; uno de cada 5
frames; balón degradado «como el ATD»; jugadores sin degradar y slots barajados. Unas 87.000–90.000 filas por
pliegue de 6 partidos [medido]. Newton con 25 iteraciones y L2 = 1, sin azar. α se eligió en una rejilla de
1/8 a 8 por el spellF1 medio en los partidos de entrenamiento de cada pliegue, con la pieza de `D` dentro y
sin oráculo: salió 4 en cinco de los siete pliegues, 2 en uno y 8 en otro; el ajuste con los 7 partidos, el
de la entrega, también da 4 [medido]. [PENDIENTE: filas del ajuste con los 7 partidos, la suma de las que
imprime por partido `python validation/apuesta_b/entrenar.py --seco`]

**E2.** Etiqueta: `D` o juego según `BallStatus`. Uno de cada 5 frames de los 7 partidos: 200.532 frames,
44,8 % `D`. scikit-learn 1.7.2 (C = 1, sin azar) solo para entrenar; los coeficientes van escritos en el
módulo.

**Cómo se evitó entrenar con el partido.** Ninguna etiqueta de entrenamiento sale del partido: ni la GT
pública, ni etiquetas a mano, ni datos humanos. Lo único del partido que llega al entrenamiento de B5 es el
perfil agregado del balón con el que se degrada la DFL (§4), sin etiquetas. Los coeficientes se validaron
dejando un partido fuera (7 pliegues). En el harness con nuestro `D`, E2 va con el modelo de los 7 partidos,
en muestra; dejando uno fuera cambia 0,001 o menos [medido]. SkillCorner y Metrica usan los coeficientes de
la entrega, que nunca vieron esos partidos. Regenerar la entrega no reentrena nada.

**Etiquetas usadas solo para validar** (no entrenan nada de la entrega):
- **Eventos de la DFL**, anotados por personas en el mismo dataset [sin verificar quién]: 195 recuperaciones,
  229 duelos con cambio de posesión y 211 sin cambio, como referencia descriptiva (§8) [medido].
- **SkillCorner**, 20 partidos: `D` fuera de sus fases de juego, y `H` o `A` según el campo
  `possession.group` que publica SkillCorner, cuya posesión exige control. Son 6.380 posesiones y un 46,5 %
  de frames `D` [medido]. Cómo produce SkillCorner ese campo: [sin verificar].
- **Metrica**, 3 partidos: etiquetas derivadas por nuestro código de sus eventos. Son 879 posesiones y un
  34,8 % de frames `D` [medido].

## 6. Validación y resultados

### 6.1 El harness y las reglas de decisión

El harness ejecuta `pipeline.run` sobre los 7 partidos de la DFL y puntúa con el scorer oficial. El balón se
degrada como el del ATD: tapado en los `D` y 5 frames a cada lado (la DFL lo congela mientras está muerto),
microcortes, el 11,3 % del juego en bloques de 5 a 15 s y una media móvil de 25 frames. Los slots se
barajan. Se puntúa con **dos convenciones**, el flag (el mismo tipo de etiqueta que la GT del reto) y
control. La segunda favorece a la proximidad por construcción, así que un candidato tiene que ganar con las
dos.

**Regla (`docs/investigacion_metodos.md` §5.8):** un candidato gana si mejora en **0,03 o más**, con el
intervalo 5–95 % del bootstrap por encima de cero y en 6 de 7 partidos o más, en las dos condiciones del
balón que cuentan para decidir («como el ATD» y «como el ATD, sin bloques») y con las dos convenciones. Si
empata con lo que hay, se queda lo que hay. Los criterios de cada candidato se escribieron antes de medir.
Así ganó B5 frente al jugador más cercano. E2 se midió con la misma regla frente a no opinar en `D`, con el
equipo oráculo, y también ganó (+0,039 y +0,032 con el flag) [medido].

**Regla de límite de daño** (16/11, escrita antes de medir ningún candidato con ella; `docs/decisiones.md`).
Es para cambios pequeños hacia control, que §5.8 deja fuera porque con el flag empatan o pierden poco. Un
candidato entra si cumple todo esto frente a lo que hay:
1. con control en la DFL, gana +0,005 o más en las dos condiciones del balón que votan, en 6 de 7 partidos en
   cada una;
2. en SkillCorner, gana en la mitad de entrenamiento y lo confirma una sola vez en la de examen, con +0,005 o
   más y en 7 de 10 partidos (cada candidato tiene un solo uso del examen, y cada uso se apunta);
3. con el flag no pierde más de 0,005 en ninguna celda;
4. una entrega de prueba pasa unos criterios de daño escritos antes de generarla.

Por qué: el equipo eligió el 12/11 «exigir control», y SkillCorner, que también lo exige, coincide con control.
El riesgo que se acepta: si la GT se parece al flag, cada cambio así puede costar hasta 0,005. Por esta regla
entró «cortas a `D`» (§2). Ojo: era la candidata que motivó la regla, así que sus cifras en la DFL y en la mitad
de entrenamiento de SkillCorner ya se conocían al escribir los umbrales. Lo que se midió a ciegas, con el umbral
escrito antes, fue el examen de SkillCorner (10 de 10) y la entrega de prueba. Un candidato que toca el `D` se mide con el `D` propio, con el balón tapado y a la
vista en los `D`, porque con el `D` oráculo la regla no puede actuar. La línea del balón del vídeo tuvo su
propia regla (§7).

### 6.2 Tabla principal

`D` oráculo (mide solo `H` frente a `A`); los 7 partidos juntos; cada partido se puntúa con B5 entrenado sin
él [medido]:

| etiquetas | balón | baseline | nosotros | diferencia [5–95 %] | gana en |
|---|---|---|---|---|---|
| flag | como el ATD | 0,406 | 0,498 | +0,093 [+0,080, +0,104] | 7 de 7 |
| flag | sin bloques | 0,435 | 0,512 | +0,078 [+0,066, +0,088] | 7 de 7 |
| control | como el ATD | 0,464 | 0,728 | +0,265 [+0,250, +0,278] | 7 de 7 |
| control | sin bloques | 0,494 | 0,748 | +0,254 [+0,240, +0,267] | 7 de 7 |

Fuente: `validation/investigacion_1116/salidas/2026-11-16_s1_dfl_oraculo.md` (código `f19fcc7`, bootstrap de
200 remuestreos).

«Cortas a `D`» no cambia esta tabla. Con el `D` oráculo, `D` está prohibido donde las etiquetas tienen juego,
así que la regla no convierte nada: la salida del harness es idéntica byte a byte antes y después [medido].

Sin oráculo, cada uno con su propio `D`, sacamos 0,414 (flag) y 0,623 (control) en «como el ATD» (0,416 y
0,616 antes de «cortas a `D`»), y el baseline 0,310 y 0,353 [medido]. Ese número no sirve para elegir entre
evidencias de equipo, porque con el balón tapado en los `D` «no hay balón» casi equivale a «`D`». Se usó, como
excepción declarada, para «cortas a `D`», que toca el `D` y con el oráculo no se puede medir. Por eso se midió
en los dos modos del balón en los `D` (§6.1).

### 6.3 SkillCorner y Metrica

- **SkillCorner** (tracking automático, posesión que exige control): +0,131 y +0,135 sobre el baseline (con
  el balón que detecta SkillCorner, tal cual y suavizado como el del ATD), en 20 de 20, y +0,059 y +0,065
  sobre el jugador más cercano en 19 de 20 [medido]. Sin oráculo, cada uno con su propio `D` (el baseline,
  el suyo: `D` donde nadie tiene el balón en ±50; nosotros, E2), el baseline saca 0,249, muy cerca de su
  0,2433 oficial, y nosotros 0,381 [medido]. Ese 0,381 es de antes de «cortas a `D`», que con el `D` propio
  suma +0,010 y +0,009 en la mitad de entrenamiento y +0,009 y +0,008 en la de examen (§2) [medido].
- **Metrica** (etiquetas derivadas de eventos): +0,118 sobre el baseline en 3 de 3 [medido]. Ojo: en esos
  datos el balón va pegado al jugador (a menos de 0,3 m del más cercano en el 45,6 % de los frames de juego
  con balón, frente al 6,4 % en la DFL sin degradar [medido]), así que no prueba nada sobre los rasgos de
  proximidad; solo que el pipeline corre con otro proveedor.

Los criterios de SkillCorner y Metrica se escribieron antes de puntuar, pero no se subieron a git antes, así
que el historial no lo prueba. Estos dos resultados confirman y no decidieron nada.

### 6.4 Diagnóstico de errores (descriptivo)

En la DFL y en 10 de los 20 partidos de SkillCorner (la mitad de entrenamiento) [medido]:
- **casi nunca partimos una posesión** (1–4 % de las que no encontramos);
- **cambiamos de equipo de menos:** con el flag predecimos 1.661 posesiones frente a 3.061, y en SkillCorner
  2.270 frente a 3.228;
- **las posesiones cortas se pierden:** encontramos el 2 % de las de menos de 1 s y el 27 % de las de 2–5 s
  con el flag, frente al 86 % de las de 10 s o más;
- con evidencia de equipo perfecta, el decodificador saca 0,970 (flag): la pérdida está en la evidencia de
  equipo con el balón a la vista (0,40 con el flag) y, después, en el `D` propio (0,08–0,11; los bordes de
  las paradas que ya vemos valen como mucho 0,05–0,07).

### 6.5 La ventana pública, solo como comprobación

`equipo_v9` saca 0,680 de spellF1 y 0,874 de macroF1 en los 5 minutos públicos (`equipo_v8`, sin «cortas a
`D`», 0,658 y 0,865) [medido]; con 17 posesiones,
una diferencia de hasta 0,39 es ruido, y en el repo oficial el que gana en la ventana (`smooth125`, 0,4242)
pierde en el partido frente a `smooth50` (0,2242 frente a 0,2433; `EVALUATION.md`). No elegimos ninguna
versión ni ningún parámetro con ella; su uso descriptivo está en §4 y §10.

### 6.6 Qué nivel cabe esperar y por qué el harness es optimista

El baseline oficial (`baseline_smooth50`) saca 0,2433 en el partido. En el harness, con su propio `D`, saca
0,310, 0,346, 0,353 y 0,397 en las cuatro celdas que deciden [medido]. Si a nuestra nota con nuestro `D` en
cada celda (0,414, 0,431, 0,623 y 0,651) le quitamos lo que esa celda regala al baseline, quedamos entre
0,33 y 0,51 [inferencia]. En SkillCorner, donde el baseline saca casi su nota oficial (0,249), sacábamos 0,381
antes de «cortas a `D`», que allí suma de +0,008 a +0,010 [medido]; de ahí el punto central de unos 0,39
[inferencia]. Las cifras oficiales solo describen (§10).

Por qué el harness es optimista:
- **la cadena completa nunca se ha puntuado con etiquetas:** el harness no ejecuta las anclas del Smart
  Tagging, los contraataques ni el balón fuera;
- en las filas con nuestro `D`, E2 se puntúa en los mismos partidos con los que se entrenó (§5);
- en el harness están los 22 jugadores, sin ruido; en el partido un equipo tiene más de 11 slots en el
  12,9 % de los frames evaluados (imitado en la DFL, cuesta como mucho 0,008) [medido];
- la DFL tiene más disputas visibles que el ATD (20,3 % frente a 14,5 %), justo donde la proximidad decide
  [medido; que nos favorezca, inferencia];
- no sabemos qué convención sigue la GT: con el flag estamos en 0,498 y con control en 0,728.

## 7. Qué se probó y se descartó

En el harness o con agregados del partido, cada uno con su regla escrita antes [medido]:
- **Otras evidencias de equipo:** el jugador más cercano (B5 le gana por +0,071 y +0,056 con el flag), dos
  reglas de radio y retención (frente al jugador más cercano pierden de 0,08 a 0,11 con el flag y empatan con
  control), otras ocho variantes de la logística y una red de una capa. Empatan o pierden.
- **Otros modelos del estado de `D`:** otras logísticas y árboles de decisión. Ninguno gana a E2.
- **Decodificador:** la duración mínima, la poda y los costes 12 y 50 empatan con el coste 25.
- **Limpiar el balón, adelantarlo 4 frames y quitar los slots sobrantes:** empatan; quedan apagados.
- **El Smart Tagging como pista de equipo sin balón:** acierta el 81,8 % en control claro, pero alcanza menos
  del 1 % de los frames evaluados. Los cambios de equipo entre fases dan 16 casos y la regla pedía 30. Una
  primera versión de los contraataques, que también puntuaba `D`, creaba 18 paradas nuevas.
- **Anclas fijas para el `D`** (del gol al saque, el instante del reinicio, el equipo que reanuda): o no hay
  un instante fijo, o pasan juego vivo a `D`.
- **Doce sondeos más, el 16/11** (un coste por parte, el encuadre de la cámara, señales nuevas): ninguno gana.
  Uno de ellos, «cortas a `D`», pasó después la regla de límite de daño y está en la entrega (§2).
- **Un detector de cambios de posesión** (16–17/11): una pieza que avisa de que la posesión acaba de cambiar y
  abarata ese cambio en el decodificador. Con un detector perfecto subiríamos de 0,728 a 0,824 con control
  [medido, techo descriptivo], pero los detectores reales dan demasiados avisos falsos (solo es bueno del 23 al
  37 %) [medido]. Ninguno pasa su regla: ni en la DFL, ni en la mitad de entrenamiento de SkillCorner (de −0,005
  a +0,003), ni encima de K2 (§8; registrado en la rama `exp/cambios-sobre-k2`).
- **Modelos de secuencia para la evidencia de equipo** (17/11): redes entrenadas en la DFL que leen la
  evidencia en el tiempo, con la inferencia en numpy. Son una convolución temporal (B11), una GRU bidireccional
  (B12), una red sobre las trayectorias de los jugadores (B13) y esa red con rasgos de control, entrenada con la
  DFL degradada como el ATD (B14). Con el flag todas ganan mucho en la DFL, de +0,046 a +0,120, pero no lo
  sostienen con control o en SkillCorner [medido]:
  - B11 y B13 ganan con control solo en 3 a 6 de 7 partidos, según la celda; en SkillCorner, B11 empata o
    pierde y B13 pierde (de −0,010 a −0,024);
  - B14 pasa en la DFL con margen (con control, de +0,027 a +0,053, en 7 de 7), pero en la mitad de
    entrenamiento de SkillCorner pierde con el `D` de las etiquetas (−0,017 y −0,013) y empata con el propio
    (registrado en la rama `claude/serene-lumiere-16245d`, donde están el código y los pesos de B11 a B16);
  - B12 es la única que también gana en la mitad de entrenamiento de SkillCorner (de +0,011 a +0,014, en las
    cuatro celdas). En la DFL, con control, gana de +0,028 a +0,034, pero en una condición solo en 5 de 7
    partidos, y se pedían 6. Por una excepción, decidida después de ese resultado y escrita antes de abrir el
    examen, se abrió su examen de SkillCorner: cumple 3 de las 4 celdas, y en la que falla gana +0,004, en 6 de
    10. Se queda fuera, sin probar variantes;
  - [PENDIENTE: B15 y B16, que se estaban entrenando al escribir esto; poner su resultado o «sin medir antes
    del corte»].

  Lectura [inferencia]: estas redes encuentran más cambios de equipo. Eso gana con el flag, que cambia en cada
  toque, pero muchos de esos cambios sobran cuando la posesión exige control, y con el tracking de otro
  proveedor aciertan menos.
- **El balón sacado del vídeo táctico** (16/11). La idea era darle a B5 un balón sin el suavizado de casi 1 s del
  ATD. Se usó un detector público (YOLO11n afinado para balones, AGPL-3.0), en local y en CPU, sobre un recorte de
  320 px alrededor del balón del ATD, ampliado ×2. Sus reglas se escribieron antes de medir
  (`validation/balon_video/BITACORA.md`, rama `exp/balon-video`):
  - en datos abiertos ve balones de 4–5 px en el 82–91 % de las imágenes, y en nuestro vídeo el balón mide 5,9 px de
    mediana [medido];
  - en el partido, en una muestra de 10 minutos, el 41 % de sus detecciones cae a más de 5 m del balón del ATD, y la
    regla pedía el 10 % como mucho. Da 2,6 detecciones por frame [medido], y la mayoría no son el balón
    [inferencia]. La línea se paró ahí;
  - el 17/11 se pasó el detector por el partido entero (1,9 h en CPU) y salió lo mismo: el 42,0 % de las
    detecciones a más de 5 m y 2,5 por frame [medido]. La más cercana al balón del ATD queda a 1,33 m de mediana,
    así que el detector sí ve el balón casi siempre, y lo que sobra son detecciones falsas [inferencia]. La línea
    siguió parada;
  - con la confianza mínima a 0,25 en vez de 0,10 (el otro valor medido en datos abiertos), sigue el 36 % lejos
    [medido]: los falsos positivos tienen tanta confianza como el balón [inferencia]. No se probaron más valores,
    porque sería elegir el umbral con el partido;
  - aunque hubiera pasado, en la DFL con un balón como el del vídeo, hasta un detector perfecto le daría a B5 del orden
    de +0,01, por debajo del ruido del partido [medido, DFL emulada];
  - con la línea se quedó sin balón del vídeo, y sin medir, una capa de `D` que cerraba cada parada en el golpeo
    del balón. La variante del detector de cambios con el balón del vídeo se midió en la DFL emulada y, con las
    cifras de esta puerta, pierde con control.

## 8. Limitaciones y qué haríamos con más tiempo

- **Cambiamos de equipo de menos y tarde** (§6.4). B5 pierde recuperaciones frente al jugador más cercano en
  los eventos humanos de la DFL (70 % frente a 84 %) [medido].
- **Los bordes del `D` son imprecisos:** E2 pone el inicio a 25 frames o menos solo en el 35 % de las
  paradas [medido]. Bien puestos valdrían +0,05 a +0,07 [medido, DFL].
- **Tres capas entraron sin medida en datos con etiquetas:** el hueco antes del reinicio, los contraataques y
  el balón fuera entraron por reglas de daño escritas antes y agregados del partido; las dos últimas son
  excepciones declaradas a «lo que no gana en el harness no entra». El balón fuera, además, falló su criterio
  de eficacia (seguíamos llegando tarde en el 25,5 % de las rachas de balón fuera, y se pedía menos del 15 %)
  y pasó los de daño. Su efecto en el spellF1 no se conoce.
- **«Cortas a `D`» quita posesiones, y ya predecimos de menos.** Pasamos de 219 a 201 posesiones, de 3,79 a
  3,53 por minuto de juego vivo, cuando en datos abiertos, con nuestro `D`, salen de 4,1 a 4,3 [medido]. Gana
  porque empareja mejor las que quedan [inferencia]. Además:
  - si la GT se parece al flag, cuesta hasta 0,002 [medido, DFL];
  - la regla de límite de daño se escribió con sus cifras de la DFL ya conocidas; a ciegas solo estaban el
    examen de SkillCorner y la entrega de prueba (§6.1);
  - con el balón tapado en los `D`, el extremo bajo del intervalo del 5–95 % con control (+0,003 y +0,004) queda
    por debajo de los +0,005 de la regla, que se escribió con valores centrales [medido];
  - el corte de 5 s se heredó del sondeo. Uno de 3 s también pasaría en la DFL, sin pérdida con el flag [medido
    en el sondeo, sin reproducir], pero elegirlo después de ver los resultados sería ajustar, y no se puede
    confirmar en el examen sin abrirlo otra vez.
- **Escalas sin ajustar entre sí:** la escala de E2, `GAP_SCORE` y los costes de `D` valen 1, 1 y 25 por
  defecto.
- **La convención de la GT no está medida.**

Con más tiempo: un detector de balón que no confunda otras cosas con el balón en nuestro vídeo (afinado con
pseudoetiquetas o con seguimiento en el tiempo; §7), y los tiempos de eventos corregidos a mano
(mediana de tres anotadores, según su README) que publica ELASTIC para 3 de los 7 partidos de la DFL, para
medir mejor dónde cambia la posesión.

**Lo que puede cambiar la entrega antes del cierre: K2.** [PENDIENTE: lo decide el equipo antes del corte.
Según lo que decida, este bloque se queda como «probado y no encendido» o se reescribe como parte del método.
Hoy su registro está solo en la rama `exp/modelo-conjunto`]
- **Qué es:** una evidencia de equipo que mira a cada jugador: una red por jugador, la suma y el máximo por
  equipo y una convolución temporal de ±12,6 s, con 36.260 pesos. Sustituye solo al logit de B5; el `D`, el
  decodificador y las capas del partido no cambian. Se entrenó con las etiquetas de control de la DFL y con las de
  la mitad de entrenamiento de SkillCorner, y en la entrega correría en numpy.
- **Lo medido** frente a la cadena de `equipo_v9`, cada partido con un modelo que no lo vio [medido]:
  - en la DFL, de +0,036 a +0,051 con control (6 o 7 de 7) y de +0,033 a +0,044 con el flag (7 de 7). Pasa
    también la regla general de §6.1 (+0,03);
  - en SkillCorner, de +0,021 a +0,028 en la mitad de examen, abierta una vez para K2;
  - predice tantas posesiones como la entrega: no inventa más, las coloca mejor;
  - su entrega de prueba es válida y cambia el 4,8 % de los frames evaluados; en la ventana pública no se rompe
    nada.
- **El aviso:** no se traslada de un proveedor a otro [medido]. Entrenado solo con la DFL pierde en SkillCorner
  (de −0,010 a −0,015), y entrenado solo con SkillCorner pierde en la DFL (de −0,075 a −0,096 con control). El
  partido es de un tercer proveedor. En Metrica, el único tercer proveedor abierto, el modelo entrenado con los
  dos gana (+0,035, en 3 partidos) [medido]. Encenderlo es una apuesta.
- **Si se enciende, cambian:**
  - la huella de la cabecera y de §9, que pasa a ser la de su entrega de prueba (`784e65e5…acbc`) [PENDIENTE:
    huella entera];
  - la fila 1 de §2, y «solo validación» de SkillCorner en §4;
  - §5, que dice que solo hay dos piezas entrenadas, y con el mismo dataset: K2 se entrenó también con
    SkillCorner.
- **Antes de entregarlo, faltaría:**
  - reproducirlo en otra máquina: `possession/conjunto.py` es código numérico nuevo;
  - decidir cómo van sus pesos al repo: hoy son un `.npz`, y `CONTRIBUTING.md` §7 no deja entrar ninguno.

## 9. Reproducción

**Código:** [PENDIENTE: URL del repo público], en el commit [PENDIENTE: hash o etiqueta git de la entrega
final].

**Entorno.** Python 3.13 y `requirements-entrega.txt` (numpy 2.5.4, pandas 3.1.1 y sus dos dependencias).
El código de la entrega solo importa numpy y la biblioteca estándar; pandas lo usan el validador y el scorer
oficiales. Python 3.11 no sirve, porque numpy 2.5.4 pide 3.12 o más.

**Datos.** El paquete del concurso descomprimido tal cual en `data/` dentro del repo, que es donde
`games.py` busca por defecto, o en otra carpeta con `MTAH_DATA_DIR` apuntando a la que contiene `tactical/`.
La entrega lee `BAR-ATH_tactical_atd.xml`, `BAR-ATH_tactical_atd.txt` y
`BAR-ATH_tactical_smart_tagging.xml`; si falta alguno, da un error que dice cuál.

**Comando** (desde la raíz del repo). Windows (PowerShell), la forma probada:

```
py -3.13 -m venv <carpeta>
<carpeta>\Scripts\python -m pip install -r requirements-entrega.txt
$env:MTAH_DATA_DIR = 'D:\ruta\al\paquete'
<carpeta>\Scripts\python -m possession.pipeline --name <NOMBRE_EQUIPO>
<carpeta>\Scripts\python evaluation/validate_submission.py evaluation/results/<NOMBRE_EQUIPO>.csv
```

macOS y Linux [PENDIENTE: que lo confirme quien reprodujo en macOS]:

```
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-entrega.txt
export MTAH_DATA_DIR=/ruta/al/paquete
.venv/bin/python -m possession.pipeline --name <NOMBRE_EQUIPO>
.venv/bin/python evaluation/validate_submission.py evaluation/results/<NOMBRE_EQUIPO>.csv
```

[PENDIENTE: cuánto tarda] 

El comando imprime solo agregados: versiones, commit y si hay cambios sin commitear, recuento del ATD,
posesiones y paradas por tramo, rachas cortas, conflictos y el sha256. Se niega a escribir el CSV si el ATD
tiene alguna línea rara o si dos piezas se contradicen en un frame evaluado.

**Huella esperada:** `d9706dfb4b5389d391146d5d7efd022f01aa2a427d3e61f7ab2c06b3ecccbe63` [PENDIENTE: final].
`equipo_v9`: 201 posesiones de 17,0 s de media, 116 paradas y `D` en el 46,2 % de los frames evaluados
[medido].

**Máquinas.** `equipo_v9` sale con el mismo sha256 en dos máquinas Windows [medido]:
- la de Ismael, en el entorno limpio (Python 3.13.9 y numpy 2.5.4), con `main` en `1e71d72` y sin cambios
  locales;
- la de Manuel (Python 3.14.4 y numpy 2.4.4), que generó el mismo fichero como entrega de prueba desde la rama
  de «cortas a `D`».

La versión anterior, `equipo_v8`, salió igual en tres máquinas [medido]: esas dos y un Mac M1 (macOS, ARM,
Python 3.13.7 y numpy 2.5.4), donde se generó tres veces. Que `equipo_v9` también salga igual en ARM es
[inferencia]: el paso nuevo solo mueve etiquetas según duraciones en frames, sin cálculos con decimales.
[PENDIENTE: reproducir `equipo_v9` en el Mac, y Python y numpy de la primera línea que imprime el comando en el
congelado con el `main` final]

No hay azar, los empates se resuelven siempre igual y nada depende del orden de los ficheros ni de la hora. B5
usa `np.exp`, que en teoría puede variar en el último bit según la CPU. El redondeo a 6 decimales lo hace
improbable, pero no lo damos por supuesto: comprobamos el sha256 del fichero en cada máquina, y con
`equipo_v8` sale el mismo en Windows x86 y en macOS ARM.

## 10. Declaraciones y referencias

**Uso de un LLM.** El equipo usó Claude (Anthropic), a través de Claude Code, para escribir código y
documentación, diseñar medidas en datos abiertos e investigar métodos. Las decisiones de método las tomaron
personas y están en `docs/decisiones.md` con su autor; Claude propuso candidatos y reglas de lectura y fijó
el reparto entrenamiento/examen de SkillCorner. También ejecutó en datos abiertos las medidas y los tres usos de
ese examen, con el permiso que dio Ismael el 16/11 (una vez por candidato) y el umbral escrito antes; dos de
ellos los autorizó además una persona en el momento. El LLM no interviene
al generar las etiquetas. Los commits no
llevan su firma, pero los documentos del repo lo nombran.

**Datos del partido y el LLM.** Los términos prohíben pasar a un LLM en la nube los materiales del concurso
«or any extracts thereof» (`OVERVIEW.md`). Nuestra regla: al LLM solo le llegaban estadísticas resumen
calculadas en local por una persona (métricas, recuentos, porcentajes, cuantiles, tiempos y errores sin
valores) y la GT pública de 5 minutos, que el repo oficial publica bajo MIT (`LICENSE`). Claude no leía el
vídeo, el tracking, el Smart Tagging ni nuestras entregas: escribía los scripts que leen el partido
(`validation/partido/`), una persona los ejecutaba y le pegaba los agregados. Sí ejecutaba el validador y el
scorer oficiales, que leen las entregas en local e imprimen agregados. Una configuración local
(`.claude/settings.json`) bloquea algunas vías de lectura de esos ficheros (se probó con ficheros de prueba,
en sesiones abiertas en la carpeta del repo; no bloquea, por ejemplo, un `open()` desde Python), así que la
protección real es la regla. Esos agregados están también en `validation/resultados/`, `docs/decisiones.md`
y este documento; nunca valores por frame ni números de frame salvo los oficiales. Desde el 15/11 los
scripts del partido tapan como «< 5» los recuentos de 1 a 4 casos; antes no siempre, y en
`docs/decisiones.md` quedan algunos recuentos pequeños de diferencias entre entregas. Una vez se escapó una
celda y se corrigió (`validation/resultados/2026-11-15_huecos_y_cambios.md`). [PENDIENTE: enviar a
hackathon.talentarena@mobileworldcapital.com la consulta de si estas estadísticas cuentan como «extracts»;
citar su respuesta, o poner «lo consultamos el <fecha> y no hubo respuesta antes de la entrega»]

**Cifras oficiales.** Creemos que las notas publicadas de los baselines y la tabla de retrasos de
`EVALUATION.md` salen de la GT completa: la documentación no lo dice, y en la ventana pública los valores
son otros [inferencia]. Las usamos solo para describir (§1 y §6.6), nunca para elegir. El 11/11 preguntamos
por email a la organización si se pueden usar para algo más que leer la métrica. [PENDIENTE: su respuesta, o
«sin respuesta antes de la entrega»]

**Smart Tagging y constantes de saque.** Usamos el Smart Tagging (automático, permitido por el `FAQ.md`) en
dos capas (§2) y las constantes `KICKOFF_VIDEO_FRAMES` de `starter/load_smart_tagging.py`: 11.185, el primer
frame evaluado y el saque de la 1ª parte (`DATA.md` y `FAQ.md`), y 113.742, el saque de la 2ª parte
(`FAQ.md`). Sirven para forzar `D` antes del saque de la 2ª parte y prohibirlo en el frame de cada saque. Con
los tramos evaluados de `games.py`, que `DATA.md` publica como «boundaries, not answers», son las únicas
constantes ligadas a frames del partido, y las publica la organización.

**La ventana pública, el vídeo y un recuento a ojo.**
- **Lectura descriptiva de la convención** (14–16/11), con reglas escritas antes: el experimento 2, con el
  tracking de la ventana, quedó sin decidir; un recuento en la GT pública de posesiones cortas entre dos del rival
  no concluyó; y una revisión externa (`docs/revision_externa_2026-11-15.md`, anexo A.6) dio 4,23 posesiones
  por minuto de juego, típico de «exigir control», que la regla de entrada del 16/11 cita como un argumento
  más [descriptivo]. Nada de esto fijó un parámetro.
- **Visionado** (15/11): una persona miró junto al vídeo los tramos de la ventana en que una versión anterior
  de la entrega y la GT pública no coincidían, con reglas escritas antes (`docs/decisiones.md`, 15/11):
  contar patrones generales, sin tiempos ni recuentos por tramo, y no ajustar ni elegir nada. Salieron
  hipótesis generales, que se midieron en datos abiertos o con agregados del partido sin etiquetas. Dos
  acabaron en la entrega:
  - el balón visto fuera, que coincidía con una tarea del plan (§2 y §8);
  - «si nuestro `D` llega tarde, damos una posesión al equipo que va a sacar», que es «cortas a `D`» (§2),
    medida en la DFL y en SkillCorner.

  Ningún peso, margen, cola ni corte sale de la ventana.
- **Recuento a ojo** (12–13/11): dos miembros miraron en el vídeo de la ventana algunos cambios de posesión
  de la GT pública y apuntaron si les parecía un toque o un control. Dio una señal de que la GT puede dar la
  posesión con un toque sin control (1 caso claro y 1 discutible). Se dejó a medias. La revisión externa lo
  calificó de zona gris frente a `RULES.md` («No hand labels on the provided game, in any amount and for any
  purpose»), y por eso lo declaramos. No entró en ningún código, modelo, parámetro ni elección, y la
  convención elegida el 12/11, exigir control, no cambió. Sus notas están en la PR 1 del repo, cerrada sin
  fusionar. [PENDIENTE: que lo confirmen quienes lo hicieron y digan cuántos cambios miraron; decidir si esa
  rama sigue en el repo público]

**Licencias.** Bundesliga: CC BY 4.0. SkillCorner Open Data: MIT. Metrica sample-data: sin fichero de
licencia; su README pide citar la fuente. Código y GT pública del reto: MIT (Metrica Sports). [PENDIENTE:
licencia del código propio] El detector de balón que se probó (§7) no entra en la entrega: el modelo
(`martinjolif/yolo-football-ball-detection`) y `ultralytics` son AGPL-3.0, y su dataset de entrenamiento (Roboflow),
CC BY 4.0. Los scripts que lo usan están en la rama `exp/balon-video` y no redistribuyen el modelo.

**Referencias.**
- Bassek, Rein, Weber y Memmert (2025). An integrated dataset of spatiotemporal and event data in elite
  soccer. *Scientific Data*, 12, 195. doi:10.1038/s41597-025-04505-y. Datos: doi:10.6084/m9.figshare.28196177.
  Con autorización de la DFL.
- SkillCorner. Open Data, https://github.com/SkillCorner/opendata (commit 4340d2745728).
- Metrica Sports. Sample data, https://github.com/metrica-sports/sample-data.
- ELASTIC [PENDIENTE: referencia completa].
- Metrica Sports y Barça Innovation Hub (2026). More than a Hack 2027: Frame-level Ball Possession, v1.0.0.
  https://github.com/metrica-sports/more-than-a-hack-2027 (`CITATION.cff`).
