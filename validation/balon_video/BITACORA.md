# Bitácora: el balón sacado del vídeo táctico (16/11)

- **Quién lo decide:** Ismael (16/11): «vamos a centrarnos en la red o los métodos que te he mencionado para el tema de
  detectar el balón», con el modelo https://huggingface.co/martinjolif/yolo-football-ball-detection como primera
  opción. Lo orquesta Claude (sesión principal de Ismael); las medidas en datos abiertos las hace una sesión aparte.
- **Regla nº 1:** el vídeo, el ATD y la homografía del partido solo los lee una persona. Claude escribe los scripts y
  lee solo agregados. El detector corre **en local**: nada de servicios en línea (ni la inferencia de Hugging Face ni
  Roboflow). Ningún recorte ni imagen del partido se guarda fuera de `MTAH_DATA_DIR`.
- **Escrita el 16/11 a las 14:15, antes de ver el resultado de la puerta 0** (la sesión aparte ya estaba midiendo; la
  sesión principal no ha leído nada suyo).

## Por qué

- El balón del ATD viene suavizado cerca de 1 s y llega unos 4 frames tarde (`2026-11-14_perfil_atd.md`,
  `2026-11-15_retraso_balon.md`). El suavizado borra los toques: en la ventana pública el detector de toques del
  experimento 2 ve 2,2 por minuto, frente a 20–38 en la DFL (`2026-11-14_experimento2_convencion_tracking.md`).
- Lo que más nota quita son las posesiones cortas y los cambios de equipo (`2026-11-15_diagnostico_errores.md`), y
  ninguna de 26 señales del tracking añade nada a B5 (`docs/investigacion_2026-11-16.md` §3). Un balón sin suavizar es
  la única fuente de información nueva.
- **La cota** [medido, revisión externa, anexo A.1]: con el balón limpio de la DFL y B5 tal cual, con el `D` propio,
  de 0,416 a 0,443 con el flag (+0,027) y de 0,616 a 0,659 con control (+0,043). Un detector real dará menos.

## Lo que no se hace

- **Afinar el detector con frames del partido etiquetados a mano:** sería etiquetar el partido (`RULES.md`, regla 1).
  Con pseudoetiquetas sacadas del ATD sí se podría (`RULES.md`: «pseudo-labels produced by an algorithm»), pero solo
  como plan B si el modelo tal cual no ve el balón, y con su propia regla.
- **Elegir nada con la ventana pública,** como siempre.
- **Darle el balón del vídeo a las piezas de `D` que ya hay.** La capa del hueco y la del balón fuera se midieron con el
  balón del ATD, donde «no hay balón» significa algo. El balón del vídeo, si entra, solo lo ve la evidencia de equipo
  (B5). Una capa **nueva** de `D` con el balón del vídeo (visto fuera del campo, o quieto antes de un reinicio) es
  posible, pero sería otra decisión con su propia regla, medida con agregados del partido como D7: la DFL no tiene
  vídeo y tapa el balón en los `D`.

## Puerta 0: ¿hasta qué tamaño ve el balón el detector? (datos abiertos, la sesión aparte)

- **Medida:** el modelo tal cual sobre el split de test de su dataset (125 imágenes, CC BY 4.0), reduciendo cada imagen
  hasta que el balón mida b ∈ {3, 4, 5, 6, 8, 10, 12, 16} px, en dos variantes (tal cual y ampliada ×2 antes de
  detectar), con confianza 0,10 y 0,25. Además, tiempos en CPU y si la salida es determinista.
- **Límite:** son imágenes del mismo tipo que las de entrenamiento (clips de la Bundesliga), así que el acierto aquí es
  optimista para nuestro vídeo [inferencia].
- **Se lee con la puerta 1a.** `b_partido` es la mediana del diámetro del balón en el partido, redondeada hacia abajo
  al tamaño más cercano del barrido.
- **Sigue si** en `b_partido` alguna de las dos variantes, con alguno de los dos umbrales, encuentra el balón en el 50 %
  o más de las imágenes con 0,5 falsos positivos por imagen o menos, **y** el tiempo estimado de esa variante para los
  199.319 frames cabe en 8 horas en la máquina que lo vaya a ejecutar.
- **Si no:** se para la línea y se apunta aquí. El plan B (afinar con pseudoetiquetas del ATD) necesita una decisión
  nueva de Ismael.

## Puerta 1a: ¿cuántos píxeles mide el balón en el partido? (lo ejecuta Ismael)

- `python validation/partido/tamano_balon_video.py` (prueba sin datos: `validation/scripts/prueba_tamano_balon_video.py`).
- Imprime percentiles de los píxeles por metro de la homografía donde el ATD ve el balón, el diámetro del balón en
  píxeles (también por zonas) y cuánto campo entra en la imagen. Es descriptiva: da `b_partido` para la puerta 0.

## Puerta 1b: ¿trae el detector toques que el ATD no trae? (lo ejecuta Ismael; script por escribir)

- **El script** (se escribe después de las puertas 0 y 1a, con la variante que haya pasado, y antes de ejecutarlo se
  sube aquí): el detector en tramos de frames seguidos repartidos por las dos partes, unos 10 minutos de vídeo en
  total. Lleva cada detección al campo con la inversa de la homografía. Imprime solo agregados.
- **Sigue si se cumplen las tres:**
  1. donde el ATD ve el balón, el detector encuentra uno a 3 m o menos del balón del ATD (adelantado 4 frames) en el
     70 % o más de los frames;
  2. de las detecciones hechas donde el ATD ve el balón, el 10 % o menos está a más de 5 m de él;
  3. con el detector de toques del experimento 0 (3 m/s, 1,5 m, por tramos de balón visible), el balón del detector da
     10 toques o más por minuto de frames con balón del ATD. Al lado se imprime lo que da el balón del ATD en esos
     mismos frames (en la ventana pública, 2,2).
  4. **(añadida el 16/11 a las 14:40, antes de medir nada de la 1b)** el temblor del detector no fabrica esos toques:
     los mismos cambios de velocidad sin ningún jugador a 3 m o menos («suelo de ruido»), por minuto, no pasan del
     doble de los que da la DFL con su balón limpio con el mismo código. Por qué: con un temblor de 0,1 m por frame,
     el detector de toques ya ve decenas de toques falsos por minuto [cuenta, sin medir]. La cifra de la DFL se calcula
     y se apunta aquí antes de ejecutar la 1b.

### Corrección de la puerta 1b (16/11, 15:50, antes de ejecutar nada del partido)

**Lo que la motiva:** la calibración en la DFL (`salidas/2026-11-16_calibracion_toques_dfl.md`, datos abiertos)
[medido]:
- con el balón limpio salen 38,4 toques y 2,1 de suelo de ruido por minuto, así que el umbral de la condición 4 es
  4,2;
- un temblor de solo 0,05 m ya da 8,7 de suelo de ruido, y no pasa. Con el balón de 4 px, eso es menos de un píxel
  [inferencia];
- el balón «como el ATD», sin ningún temblor, ya da 4,1.

**Por qué no sirve como puerta** [inferencia]:
- En el partido, el suelo de ruido sube por cosas que no dependen del detector: jugadores que faltan en el ATD, balones
  en el aire llevados al césped con la homografía y frames de balón muerto.
- B5 no usa toques: usa la distancia del balón a los jugadores, en ventanas, y un temblor de unos centímetros apenas
  la mueve.

La condición 4, tal como estaba, podía tumbar un detector que a B5 le sirve, y la 3 no distingue toques de verdad de
toques de temblor sin la 4.

**Cómo queda la puerta 1b:**
- **Las condiciones 3 y 4 pasan a descriptivas.** Se imprimen, y al lado va el suelo de ruido del balón del ATD en los
  mismos frames, como referencia dentro del partido.
- **Además, el sondeo imprime:**
  - el temblor del balón del detector (`instrumento.temblor` del experimento 2: la mediana de |x[t+1] − 2·x[t] +
    x[t−1]|, con los tres frames con detección);
  - la longitud media de las rachas de fallos: frames seguidos con balón del ATD y sin detección a 3 m o menos.
- **La 1b decide con las condiciones 1 y 2 y con una quinta.**

**5. La emulación en la DFL (la medida de la puerta 2.1, adelantada), leída en el punto que mide la 1b.**
- **La rejilla, calculada en datos abiertos antes de que se ejecute la 1b:**
  - cobertura p ∈ {0,5, 0,6, 0,7, 0,8, 0,9, 1,0};
  - temblor σ ∈ {0,03, 0,06, 0,12, 0,25} m;
  - fallos en rachas de longitud media ∈ {1, 12, 50} frames.
- **El balón emulado:** donde el balón «como el ATD» del harness se ve, con probabilidad p es el balón limpio más un
  ruido gaussiano σ; si no, es el balón «como el ATD». Donde el balón «como el ATD» no se ve, tampoco se ve: el
  detector solo busca alrededor del balón del ATD.
- **Lo que se mide:** B5 de `main` (dejando el partido fuera) con ese balón, frente a B5 con el balón «como el ATD».
- **La celda que se lee:**
  - p: la condición 1, redondeada hacia abajo a la rejilla;
  - σ: el menor de la rejilla cuyo temblor en la DFL (calibrado con la misma función) es igual o mayor que el que
    mide la 1b;
  - la longitud de las rachas: la medida en la 1b, redondeada hacia arriba a la rejilla.
- **Pasa si, en esa celda y con el `D` de las etiquetas:**
  - con control: +0,01 o más en las dos condiciones que votan, ganando en 6 de 7 partidos;
  - con el flag: no pierde más de 0,005 en ninguna.

**La variante,** fijada el 16/11 a las 16:00, antes de medir nada del partido, con la puerta 0 [medido]:
- se detecta en un recorte de 320 px alrededor de la proyección del balón del ATD en t+4, ampliado ×2: la red recibe
  640×640;
- es la única variante que pasa la puerta 0 desde 3 px (con la imagen tal cual hacen falta 6 px) y que cabe en 8 horas
  en CPU (unos 60 ms por frame en la CPU de la puerta 0);
- con 320 px de lado quedan unos ±8 m de margen alrededor del balón del ATD con el balón de 4 px [cuenta];
- se usa la misma variante en la 1b y en la detección del partido entero, sea cual sea `b_partido`, siempre que sea de
  3 px o más. Con menos, la línea se para.

**El balón del vídeo que recibe B5,** también fijado ahora:
- en cada frame con balón del ATD, la detección de más confianza a 5 m o menos del balón del ATD en t+4;
- si no hay ninguna, el balón del ATD adelantado 4 frames (`ball.advance_ball`), para que todo el balón vaya en el
  mismo tiempo que los jugadores;
- donde el ATD no ve el balón, nada, como en la emulación de la condición 5.

**Si la 1b pasa,** se lanza de noche la detección del partido entero. La puerta 2 no cambia: la 2.1 se repite con la
cobertura, el temblor y las rachas del partido entero, y después vienen la 2.2, la 2.3, la 2.4 y la 2.5.

### Precisiones de la puerta 1b (16/11, 17:00, antes de ejecutar nada del partido)

Salen de la revisión del sondeo (`validation/partido/balon_video_sondeo.py`): cinco revisores encontraron 29 problemas
y se arreglaron todos. El sondeo las aplica así:
- **La variante fijada incluye la confianza mínima de 0,10.** Con otra variante o con otra confianza, el sondeo no da
  veredicto.
- **Muestra mínima: 10 tramos y 3.000 frames.** Por defecto son 40 tramos de 375 frames, que empiezan en el saque de
  cada parte (antes del de la 2ª parte todo es `D`).
- **La condición 2 cuenta todas las detecciones del recorte.** También las que caen fuera del campo o no se pueden
  proyectar, que cuentan como lejos.
- **La base son los frames con balón del ATD dentro del campo.** Los que lo tienen fuera se cuentan aparte.
- **Si el vídeo no decodifica 199.319 frames, no hay veredicto.**
- **Fuera de la rejilla no pasa:** cobertura por debajo de 0,5, temblor mayor que el de σ = 0,25, o una racha de fallos
  más larga que la mayor de la emulación.
- **Corrección a la regla de las 15:50 sobre la longitud de las rachas:**
  - Se compara con la racha media **real** de fallos de cada celda de la emulación, en esa p y esa σ, y se toma la
    menor L cuya racha real es igual o mayor que la medida.
  - Con L = 1 los fallos son independientes y su racha media es 1/p (1,43 con p = 0,7). Con la regla literal
    («redondeada hacia arriba a la rejilla») nunca salía L = 1.
  - La lectura literal se imprime al lado, sin voto.
- **El «4,1 de ruido sin temblor» del balón «como el ATD» es en buena parte un artefacto** [medido,
  `salidas/2026-11-16_calibracion_toques_dfl.md`]:
  - 564 de sus 1.324 eventos caen justo a 18 frames de un `D`, donde la media móvil se queda con un solo lado;
  - lejos de los `D` da 2,44 por minuto, frente a 1,72 del balón limpio.

### Réplicas de la condición 5 (16/11, 18:30, antes de ejecutar nada del partido; la regla no cambia)

**Por qué:** con una sola tirada por celda, el ruido de Monte Carlo del Δ de control (de 0,0006 a 0,0028) era del
orden de la distancia al +0,01, así que el veredicto de una celda dependía de la semilla. Lo encontró la revisión de
`emular_dfl.py`.

**Qué se hace:**
- En las celdas con p ≥ 0,7 se hacen R = 8 réplicas, con la semilla `[SEMILLA, partido, condición, 100p, 1000σ, L, r]`
  (la réplica 0, sin el último elemento).
- En cada partido, las R réplicas se juntan con `puntuar.juntar` para «gana en»; el Δ sale de los 7×R recuentos
  juntos, y el veredicto, de esos dos.
- El intervalo es el de la réplica 0 y es solo descriptivo.

**«Sin decidir»:** una celda cuyo Δ juntado cae a menos de dos errores estándar del umbral, o cuyo «gana en» de control
cruza el 6 según la réplica. Se imprime y no vota: vota el veredicto juntado.

**Reconocido:** R y las semillas se fijaron después de ver una rejilla de una sola tirada. No se ha ejecutado nada del
partido, y el umbral y la regla no cambian.

Salida: `salidas/2026-11-16_emulacion_dfl.md` y `.json` (script `358043bf…`). La calibración del temblor está en
`salidas/2026-11-16_calibracion_temblor_dfl.*`: con un temblor medido de 0,0947 m o menos, σ = 0,03.

**Lo que dice la rejilla, para saber qué esperar** [medido, DFL, `D` de las etiquetas; Δ frente a `main`, con «como el
ATD» / «sin bloques»]:
- **El detector perfecto** (p = 1, σ = 0): +0,010 / +0,012 con el flag y +0,014 / +0,017 con control.
- **Uno realista** (p = 0,8, σ = 0,06): de +0,007 a +0,009 con el flag y de +0,011 a +0,015 con control.
- **En casi todas las celdas** gana en 6 o 7 partidos de 7 con las dos convenciones.
- **Lectura** [inferencia]: con B5 tal cual, el balón del vídeo da como mucho del orden de +0,01, positivo con las dos
  convenciones pero por debajo del ruido del partido (0,04). Para sacar más hace falta un modelo que aproveche el balón
  nítido (B10, la tarea de David) o usarlo en los bordes del `D`.

## Puerta 2: ¿entra en la entrega? (regla de entrada fijada ahora; los detalles, antes de medir)

Es la tercera excepción a «lo que no ha ganado en el harness no entra»: la DFL no tiene vídeo. Esta línea tiene su
propia regla y no usa la del «límite de daño» de los cambios pequeños (`docs/decisiones.md`, 16/11).

1. **En la DFL, con una degradación «como el vídeo»** calibrada solo con la puerta 1b (el balón sin suavizar, con la
   cobertura y el error de posición medidos; nunca con la ventana pública), B5 con ese balón frente a `main`:
   - con control, +0,01 o más en las dos condiciones que votan y ganando en 6 de 7 partidos, con el `D` de las
     etiquetas y con el propio;
   - con el flag, no pierde más de 0,005 en ninguna celda.
2. **Entrega de prueba frente a `equipo_v8`,** con criterios de daño escritos aquí antes de generarla. **Escritos el
   16/11 a las 17:20:**
   - **Cómo se genera:**
     - `python -m possession.pipeline --name prueba_balon_video --capa balon_video.ajuste_b5_video`, con la caché de
       la detección del partido entero;
     - la capa le cambia a B5 el balón del ATD por el balón del vídeo (la regla de arriba) y no toca nada más;
     - se compara con `validation/partido/probar_entrega.py ... --contra equipo_v8`.
   - **Pasa si se cumple todo:**
     - 0 frames con piezas en conflicto, y ninguna racha de menos de 25 frames (posesiones, juego y paradas) en los dos
       tramos;
     - el `D` casi no se mueve, porque la capa solo cambia B5: como mucho 1.000 frames evaluados entre los que pasan de
       `D` a juego y los que pasan de juego a `D`, y las paradas a ±6 de las 116 de `equipo_v8`;
     - las posesiones, entre 219 y 328 (×1,5). Con menos, la capa no hace nada; con más, sospecha de parpadeo;
     - los frames que cambian de un equipo al otro, el 10 % o menos de los evaluados (15.886);
     - la ventana pública se imprime y no decide.
   - **Lo que decide si mejora es la 2.1.** Esto solo dice que no rompe nada.
3. **Reproducible:** el comando único regenera la entrega byte a byte dos veces en una máquina y una en otra (con la
   detección dentro: las detecciones del partido no se pueden publicar). Si no, no entra.
4. **Tiempo:** el comando entero cabe en 8 horas en la máquina de referencia que se documente.
5. **Licencias:** el modelo y `ultralytics` son AGPL-3.0; se declara en el documento técnico, con el dataset
   (CC BY 4.0) y sus autores.
6. **Si se enciende** (`possession/balon_video.py`, `ajuste_b5_video`, en `pipeline.DELIVERY_LAYERS`), es una excepción
   NUEVA a la interfaz: la capa lee `BAR-ATH_tactical_balon_video.npz`, en la carpeta de `paths["atd_raw"]`. Hay que
   apuntarlo en `possession/tracking.py`, en `docs/PLAN_ENTREGA.md` §2 y en `CLAUDE.md`, y la detección tiene que ir en
   el comando de la entrega (punto 3).

### Precisión de la puerta 2.1: el `D` propio, con réplicas (16/11, 20:40, antes de leer ninguna cifra del partido)

La escribe la sesión que lee las puertas en la máquina de Ismael. A esta hora no ha visto ni el JSON de la 1b ni el de
la detección del partido entero.

**Por qué:** la 2.1 pide pasar «con el `D` de las etiquetas y con el propio». En la rejilla de `emular_dfl.py`, el `D`
propio va con una sola tirada por celda (la réplica 0), porque para la 1b era solo descriptivo. Es el problema que las
réplicas de las 18:30 arreglaron para el `D` de las etiquetas: el ruido de una tirada es del orden de la distancia al
+0,01. En la 2.1 el `D` propio sí decide.

**Qué se hace:**
- El `D` propio se calcula con R = 8 réplicas en las celdas con p ≥ 0,7: las mismas semillas, el mismo balón emulado y
  la misma forma de juntar que a las 18:30. Con p < 0,7 sigue habiendo una sola tirada con los dos `D`, como entonces.
- Lo calcula `emular_dfl_propio.py`, con las funciones de `emular_dfl.py` y sin tocarlo. Escribe en
  `salidas/2026-11-16_emulacion_dfl_propio.*`. El JSON de la emulación no se regenera: lo leen por su nombre el sondeo y
  la detección.
- Se calculan todas las celdas con p ≥ 0,7 ahora, antes de saber cuál se leerá.
- **Comprobación:** la réplica 0 tiene que dar, celda a celda, las cifras del `D` propio del JSON de la emulación
  (script `358043bf…`). Si no las da, no se lee nada con este fichero y se avisa.

**Cómo se lee la 2.1:** en la celda (p, σ, L) que dé la detección del partido entero (`condicion_5_descriptiva.celda`,
leída con la regla de la 1b). Pasa si pasan los dos:
- con el `D` de las etiquetas, el veredicto juntado del JSON de la emulación (`cumple`);
- con el `D` propio, el veredicto juntado de `…_emulacion_dfl_propio.json`. El `propio_pasa` que imprime la detección
  sale de una sola tirada y se queda como descriptivo.

En cada `D`, el veredicto es el de siempre: con control, +0,01 o más y 6 de 7 en las dos condiciones que votan; con el
flag, no pierde más de 0,005 en ninguna de las dos. «Sin decidir» se imprime y no vota.

**Reconocido:** la rejilla del `D` propio con una tirada ya estaba a la vista (`salidas/2026-11-16_emulacion_dfl.md`), y
la 1b de Antonio puede estar ya ejecutada. El umbral y la regla no cambian.

### La entrega pasa a `equipo_v9`: contra qué se leen la 2.1 y la 2.2 (16/11, 21:25, antes de generar ninguna entrega de prueba)

**Qué cambia:** Ismael ha decidido encender «cortas a `D`» en `main` (`temporal.decode_cortas_a_d`, PR 20). La entrega
vigente pasa a ser `equipo_v9`: 201 posesiones, 116 paradas y 1.167 frames más de `D` que `equipo_v8` [medido por Ismael
con la entrega de prueba; lo pasa la sesión planificadora]. `exp/balon-video` sale de antes y no lleva ese cambio.

**La 2.1** está medida contra el pipeline de `equipo_v8`: el `possession/` de esta rama, que es el de `main` en `3220707`,
antes del cambio.
- Con el `D` de las etiquetas, «cortas a `D`» no debería cambiar nada [inferencia]: la regla no convierte donde `D` no
  está permitido.
- Con el `D` propio y el decodificador de `equipo_v9` no está medida. Si la capa se fuera a encender sobre
  `equipo_v9`, antes se repite la rejilla del `D` propio con ese decodificador y con la misma regla.

**La 2.2** tiene ahora dos partes, y para encender la capa tienen que pasar las dos:
- **Parte A, la de siempre, frente a `equipo_v8`.** Dice si la capa rompe algo por sí sola. La entrega de prueba se
  genera con el decodificador de `equipo_v8`: desde `exp/balon-video` sin traer `main` o, con `main` dentro, añadiendo
  `--pieza temporal=temporal.decode`. Los criterios de las 17:20 no cambian.
- **Parte B, frente a `equipo_v9`,** solo si la capa se fuera a encender. Con `main` dentro y el decodificador de la
  entrega: `probar_entrega.py prueba_balon_video_v9 --capa balon_video.ajuste_b5_video --contra equipo_v9`. Pasa si se
  cumple todo:
  - 0 frames con piezas en conflicto, y ninguna racha de menos de 25 frames en los dos tramos;
  - las paradas, entre 110 y 122. «Cortas a `D`» no crea ni quita paradas: alarga hacia atrás la que ya hay [por el
    código de `temporal.cortas_a_d`];
  - las posesiones, entre 201 y 301 (las de `equipo_v9`, ×1,5);
  - los frames que cambian de un equipo al otro, como mucho 15.886, el 10 % de los evaluados;
  - entre los frames evaluados que pasan de `D` a juego y los que pasan de juego a `D`, como mucho 2.167: los 1.000 de
    siempre más los 1.167 que mueve «cortas a `D`» entera. Con este decodificador la capa sí puede mover el `D`, porque
    cambia qué posesiones cortas acaban en una parada;
  - la ventana pública se imprime y no decide.

**Dónde va lo que sale del partido:** la caché de detecciones es dato del partido derivado. Va en
`MTAH_DATA_DIR/tactical/` con un nombre que empiece por `BAR-ATH_tactical_` (lo cubre el bloqueo de
`.claude/settings.json`), nunca en el repo ni en `~/mtah2027-salidas/`.

## Cómo se reproduce: el comando único (puertas 2.3 y 2.4)

Si la línea entra, la entrega se regenera con un solo comando con la detección dentro: `regenerar.py`, en la raíz del
repo.
- `regenerar.py` lee el partido, así que solo lo ejecuta una persona.
- Hoy genera una entrega de prueba con la capa por `--capa`; no toca `pipeline.py` ni `DELIVERY_LAYERS`.
- Su prueba sin datos, que puede ejecutar cualquiera, es `validation/scripts/prueba_regenerar.py`.

**Python y los dos entornos.** Los dos con Python 3.13, y aparte, para que torch y ultralytics no toquen lo de la
entrega:

| entorno | versiones | qué ejecuta |
|---|---|---|
| de la entrega | `requirements-entrega.txt`: numpy 2.5.4, pandas 3.1.1 y sus dos dependencias | `regenerar.py`, el pipeline y el validador |
| del detector | `requirements-detector.txt`: torch 2.15.0, torchvision 0.29.2, ultralytics 8.4.215, opencv-python 5.0.0.93, numpy 2.5.4 y pandas 3.1.1 | la detección (`validation/partido/balon_video_detectar.py`) |

Se crean una sola vez. En Windows el python de un entorno es `<carpeta>\Scripts\python.exe`, y el entorno se crea con
`py -3.13 -m venv <carpeta>`:

```bash
python3.13 -m venv <entrega>
<entrega>/bin/python -m pip install -r requirements-entrega.txt
python3.13 -m venv <detector>
<detector>/bin/python -m pip install -r requirements-detector.txt
<detector>/bin/python -m pip show opencv-python-headless        # tiene que decir que no está
<detector>/bin/python validation/balon_video/detector.py --descargar
<detector>/bin/python validation/balon_video/detector.py --comprobar
```

- **En Linux,** antes del `pip install -r` del detector, torch y torchvision desde el índice de CPU (si no, pip baja
  varios GB de CUDA): `<detector>/bin/python -m pip install torch==2.15.0 torchvision==0.29.2 --index-url
  https://download.pytorch.org/whl/cpu`.
- **El modelo** (`--descargar`) va a `~/mtah2027-modelos/`, fuera del repo, con su sha256 fijado. Es AGPL-3.0, como
  ultralytics (puerta 2.5).
- **No se fijan** las dependencias de ultralytics (pillow, scipy, matplotlib…): solo las seis de arriba.

**El comando:**

```bash
<entrega>/bin/python regenerar.py --python-detector <detector>/bin/python
```

- `--name <nombre>` cambia el nombre del CSV. Por defecto es `regenerada_balon_video` con la capa apagada y
  `pipeline.DEFAULT_NAME` con ella encendida.
- `--forzar` rehace la detección aunque la caché valga: es la segunda ejecución de la 2.3 en una misma máquina.
- `--python-detector` también puede ir en la variable `MTAH_PYTHON_DETECTOR`. Solo hace falta si hay que detectar.

**Qué hace y qué imprime.** Comprueba el entorno de la entrega contra su requirements y que están los cinco ficheros
del partido. Después decide si hay que detectar:
- **No detecta** si la caché vale:
  - está completa, es de la variante fijada y su huella cuadra con sus arrays;
  - su llave es la que escribiría la detección ahora: el mismo código que detecta, los mismos hilos, el mismo vídeo y
    la misma lista de frames. La lista se recalcula con el ATD y la homografía (un par de minutos);
  - y las versiones que guarda son las fijadas.
- **Detecta** si no vale o con `--forzar`. Antes comprueba el entorno del detector de dos formas: las versiones de los
  paquetes y las que guardaría en la caché (`detector.versiones()`). La detección va siempre con `--forzar`, así que:
  - pisa la caché que no valía y tira un parcial de otra configuración;
  - si se corta, el mismo comando sigue desde el último parcial, que es de la misma configuración.

Luego genera la entrega con la capa y la pasa por el validador. Imprime, solo agregados:
- las versiones de los dos entornos;
- el commit, y si hay cambios sin commitear en el código que detecta;
- la huella de la caché;
- el sha256 de la entrega;
- el veredicto del validador y los tiempos.

**Dónde va la caché:** en `MTAH_DATA_DIR/tactical/BAR-ATH_tactical_balon_video.npz`; mientras se detecta, también un
`….parcial.npz`. Es dato del partido derivado:
- nunca en el repo, ni en `~/mtah2027-salidas/`;
- ni se pega a Claude ni se publica.

Quien reproduzca la entrega la rehace con el mismo comando.

**Qué se compara (2.3):** la huella de la caché y el sha256 de la entrega. Tienen que salir iguales dos veces en una
máquina (la segunda con `--forzar`) y una en otra, con el mismo commit y «sin cambios locales». Si las huellas no
coinciden, el JSON de la detección dice qué cambia (`para_comparar_maquinas`).

**Cuánto tarda** (la detección entera, sin medir todavía en el partido):
- **Con la caché hecha:** lo que tarda el pipeline, unos minutos, más un par de minutos para recalcular la lista.
- **Con la detección:** la puerta 0 midió de 43 a 72 ms por recorte de 640×640 en CPU (Intel Core Ultra 5 225U). Son
  de 2,4 a 4,0 horas si se detectaran los 199.319 frames. Es un techo:
  - solo se detecta donde el ATD ve el balón, en los tramos con juego;
  - pero además se decodifica el vídeo entero.
- **El techo de cada máquina** lo da el ensayo del sondeo (`horas_estimadas_partido_entero_techo`). La cifra real son
  los `tiempos_acumulados` del JSON de la detección, y es la medida de la 2.4: el comando entero tiene que caber en
  8 horas en la máquina de referencia.
- **Medido con el ensayo** (Antonio, 16/11): en un Mac M1 (macOS, 8 núcleos, 4 hilos de torch), 1,118 ms por frame
  decodificado y 51,78 ms por detección. Da un techo de **2,93 horas** para el partido entero [medido].

La detección real se apunta aquí cuando se mida:

| máquina | CPU | techo del ensayo | horas de la detección | minutos de la entrega |
|---|---|---|---|---|
| Antonio | Apple M1 | 2,93 h | — | — |

**Límites:**
- El determinismo de la detección entre máquinas está sin medir. Lo dice la 2.3. Entre un Mac ARM y un Windows x86,
  torch en CPU puede no dar lo mismo bit a bit [inferencia].
- `torchvision` no queda guardada en la caché: `detector.versiones()` no la lleva. `regenerar.py` la comprueba antes
  de detectar, pero una caché hecha a mano con el paso 9 de `ESTA_NOCHE.md` se acepta sin que nadie la haya mirado.

## Resultados

### Puerta 1b: «NO SIGUE». La línea se para (16/11, 22:10; lo ejecutó Ismael en su Windows, CPU) [medido, agregados del partido]

**Veredicto, con la regla tal como estaba escrita:** `"global": "NO SIGUE"`. Falla la condición 2. **La línea del
balón del vídeo se para:** no se lanza la detección del partido entero, no se lee ninguna puerta 2.x y la capa
`balon_video.ajuste_b5_video` se queda apagada. La entrega sigue siendo la vigente, `equipo_v9`.

- **Cómo:** `balon_video_sondeo.py` con la variante fijada (recorte de 320 px ampliado ×2, confianza 0,10), con
  `exp/balon-video` y el entorno del detector (Python 3.13.9, numpy 2.5.4, torch 2.15.0+cpu, opencv 5.0.0, ultralytics
  8.4.215, 4 hilos, FFMPEG). Modelo `fb37942448e7`, revisión `63666b30e2a4`. El vídeo decodifica sus 199.319 frames.
- **Muestra:** 40 tramos de 375 frames (15.000), con 7.010 frames con balón del ATD en t+4 dentro del campo y 179
  fuera.
- **Condición 1, cumple:** el 78,94 % de esos frames tiene una detección a 3 m o menos del balón del ATD (umbral: 70 %).
- **Condición 2, NO cumple:** el 40,68 % de las detecciones está a más de 5 m del balón del ATD (7.650 de 18.805;
  umbral: 10 %). Solo con las que caen dentro del campo, 39,66 % (sin voto).
  - El detector da 2,64 detecciones por frame de media: el 74,4 % de los frames tiene 2 o más y el 1,75 %, ninguna.
- **Condición 5, cumple:** la celda es p = 0,7, σ = 0,03 y L = 12 (temblor del detector 0,050 m; racha media de fallos
  6,18 frames), y está «sin decidir».
- **Descriptivo:**
  - toques por minuto: 45,9 con el balón del detector y 2,1 con el del ATD; ruido, 17,2 y 2,6;
  - la detección elegida (la más cercana a 5 m o menos) está a más de 3 m del balón del ATD en el 18,8 % de los
    frames;
  - alineación: el desfase con menor mediana de distancia es 0 frames (por parte, −1 y 0), no los 4 que se esperaban.
    Solo descriptivo: con tantos falsos positivos no dice gran cosa del retraso del balón del ATD, y
    `ball.advance_ball` está apagada en la entrega;
  - tiempo: 1,09 ms por frame decodificado y 43,4 ms por detección; 2,46 h estimadas para el partido entero (techo
    del ensayo: 3,12 h).

**Lectura: la mayoría de las detecciones son falsos positivos** [inferencia, con cuentas; la propuso la sesión
planificadora y aquí se comprueban sus números]:
- **El recorte:** con el balón de 5,92 px (22 cm, unos 26,9 px por metro), los 320 px son unos 11,9 m de lado. La parte
  a más de 5 m del centro es el 44,5 % del área, y la parte a 3 m o menos, el 20,0 %.
- **La condición 2:** el 40,7 % de las detecciones lejos es casi ese 44,5 %. Las detecciones caen casi como si se
  repartieran al azar por el recorte. Son 2,64 por frame, frente a los 0,25 falsos positivos por imagen de la puerta 0.
- **La condición 1:** con 2,64 detecciones repartidas al azar por frame, que alguna caiga a 3 m o menos pasa en cerca
  del 41 % de los frames (Poisson). Parte del 78,9 % no es el balón.
- **La condición 5 «cumple» porque la emulación no tiene falsos positivos:** solo fallos y temblor gaussiano, no un
  objeto equivocado a 5 m o menos. La detección elegida está a más de 3 m del balón del ATD en el 18,8 % de los frames.
- **Límites de la cuenta:**
  - los píxeles por metro cambian con la perspectiva: con el balón de p5 (4,4 px) el recorte cubre unos 16 m, y con el
    de p95 (8,9 px), unos 8 m;
  - los falsos positivos no tienen por qué repartirse al azar: pueden juntarse cerca de los jugadores, que están cerca
    del balón;
  - las detecciones elegidas tienen más confianza que el resto (mediana 0,79 frente a 0,56), así que algunas sí serán
    el balón.

La condición 2 se escribió antes de medir para parar justo un detector así, y no se cambia después de ver el resultado.
Reabrir la línea sería una decisión nueva, con su propia regla escrita antes de medir, y no llegaría al corte.

**Lo que queda de la línea:** el código, las pruebas y esta bitácora siguen en `exp/balon-video`, para el documento
técnico (lo que se probó y por qué se descartó). No entran en `main`.

### Variante B: la 1b con confianza 0,25 (decisión de Ismael, 16/11, 22:10; escrita antes de medirla)

**Quién y por qué:** Ismael pide seguir con la confianza («¿no continuarías con lo de la confianza?»). La 1b con 0,10
falló por los falsos positivos, y subir la confianza mínima es la forma directa de quitarlos.

**Qué valor y por qué ese:** 0,25, el otro umbral que la puerta 0 midió en datos abiertos. Con el balón de 5 px y ×2
dio un recall de 0,872 y 0,10 falsos positivos por imagen (con 0,10: 0,912 y 0,25). No se elige ningún otro valor.

**Reconocido:** se escribe después de ver la 1b con 0,10, que trae los percentiles de confianza del partido
(detecciones: p25 0,27 y p50 0,56). Un umbral más alto se elegiría mirando esos números, y por eso no se admite.

**La regla:** la misma 1b, sin cambiar nada más:
- la misma muestra (40 tramos de 375 frames desde el saque de cada parte), la misma variante (recorte de 320 px, ×2) y
  el mismo código;
- las mismas condiciones 1, 2 y 5, con los mismos umbrales: 70 %, 10 % y la celda de la emulación;
- sigue si da «SIGUE». Si da «NO SIGUE» o no hay veredicto, la línea se queda parada y no se prueba ninguna otra
  confianza.

**Lo que espero** [inferencia, apuntado antes de medir]: que no pase. Con 0,25 se quita más o menos la cuarta parte de
las detecciones (la que está por debajo del p25), y para bajar del 40,7 % al 10 % de detecciones lejanas haría falta
quitar casi todos los falsos positivos.

**Si pasa:**
- la detección del partido entero se hace con 0,25. Hay que cambiar `CONF` en `validation/balon_video/detector.py` y
  en `possession/balon_video.py`. Cambia la llave de la caché, pero todavía no hay ninguna caché hecha;
- después vienen las puertas 2.1 a 2.5 como están escritas, contra la entrega vigente, `equipo_v9`.

### Puerta 1a y reproducción de `equipo_v8` (16/11, tarde; lo ejecutó Antonio en su Mac M1, macOS, CPU) [medido, agregados del partido]

- **`equipo_v8` reproducida en otra máquina:**
  - con Python 3.13.7 y numpy 2.5.4 sale el sha256 `d78c514dcf5e8ad9bcff5f76da0aadf409c01ce89ad65ad0435421daf31ce2b2`;
  - tres veces, sin cambios locales: dos en `exp/balon-video` (`3aa1916`) y una en `main`;
  - el validador la da por válida: 219 posesiones de 15,8 s y 116 paradas;
  - es la primera reproducción en macOS y en ARM: la huella de la entrega aguanta un cambio de sistema y de procesador.
- **El balón en el vídeo** (`tamano_balon_video.py`):
  - diámetro p50 = 5,92 px, con p5 = 4,4 y p95 = 8,86 px; solo el 1,4 % de los frames, por debajo de 4 px;
  - el «unos 4 px» que había en el repo (una cuenta) se quedaba corto.
- **Lectura con la regla** de las puertas 0 y 1a: `b_partido` = 5 px. La variante fijada (×2) pasa la puerta 0, con un
  recall de 0,912 / 0,872 y 0,25 / 0,10 falsos positivos por imagen.
- **El tiempo,** en su máquina, con FFMPEG y 4 hilos:
  - 1,118 ms por frame decodificado y 51,78 ms por detección;
  - un techo de 2,93 horas para el partido entero: también cabe en 8 horas.
- **El entorno del detector, comprobado:**
  - versiones: torch 2.15.0, torchvision 0.29.2, ultralytics 8.4.215, opencv-python 5.0.0.93, numpy 2.5.4, pandas
    3.1.1;
  - el modelo es `fb37942448e7…`, con su escaneo del pickle bien;
  - las pruebas sin datos, todas en verde;
  - el ensayo corto de la 1b, correcto.
- **Pendiente:** la 1b de verdad (en marcha a las 18:50).

### Ensayo de la entrega en `main` (16/11, noche; lo ejecutó Ismael en Windows, con el entorno limpio) [medido, agregados del partido]

- **Qué:** el paso 1 de `ESTA_NOCHE.md`: `python -m possession.pipeline --name ensayo_16nov`, con Python 3.13.9 y numpy
  2.5.4, en `main` (`c6a3dee`) y sin cambios locales en el código de la entrega.
- **Sale el sha256 de `equipo_v8`:** `d78c514dcf5e8ad9bcff5f76da0aadf409c01ce89ad65ad0435421daf31ce2b2`.
- El validador la da por válida: 219 posesiones de 15,8 s de media. Hay 0 frames con piezas en conflicto y ninguna
  racha de menos de 25 frames.
- `main` lleva ya la PR 20 («cortas a `D`», apagada): no cambia la entrega.
- Los agregados se los pegó Ismael a la sesión planificadora, que los pasó a esta.

### La rejilla de la 2.1 con el `D` propio y réplicas (16/11, 21:20; datos abiertos, antes de leer ninguna cifra del partido) [medido]

Salida: `salidas/2026-11-16_emulacion_dfl_propio.md` y `.json` (script `emular_dfl_propio.py`, `1d7f4765…`; 37 minutos
con 10 procesos en la máquina de Ismael, Python 3.13.9 y numpy 2.5.4).

- **La comprobación pasa:** la réplica 0 da las cifras del `D` propio del JSON de la emulación en 48 de 48 celdas
  (tolerancia 1e-12). Esta máquina reproduce las cuentas del ordenador donde se hizo la rejilla.
- **La tirada única no bastaba:** con 8 réplicas, el veredicto del `D` propio cambia en 12 de las 48 celdas.
- **Cuántas celdas pasan la 2.1** (con los dos `D`), de las 12 de cada cobertura:

  | p | pasan con el `D` propio | pasan con los dos |
  |---|---|---|
  | 0,7 | 7 | 6 |
  | 0,8 | 8 | 8 |
  | 0,9 | 11 | 11 |
  | 1 | 12 | 12 |

  En total, 38 pasan con el `D` propio, 42 con el de las etiquetas y 37 con los dos.
- **Lo que gana, con el `D` propio:** con control, de +0,009 a +0,017; con el flag, de +0,004 a +0,010. Nunca pierde.
- **Casi todo queda «sin decidir»:** 38 de 48 celdas están a menos de dos errores estándar del umbral, o su «gana en»
  cruza el 6 según la réplica. No vota, pero dice lo que hay: lo que da B5 tal cual con el balón del vídeo está justo en
  el +0,01 que pide la regla.
- **Lectura** [inferencia]: que la 2.1 pase o no en la celda del partido depende de milésimas. Pase o no, la ganancia
  esperada con B5 tal cual es de +0,01, por debajo del ruido del partido (0,04).

### Puerta 0 (16/11, sesión aparte; datos abiertos) [medido]

- **Entorno:** CPU Intel Core Ultra 5 225U (12 núcleos, 14 hilos), Python 3.14.7, torch 2.15.0+cpu, ultralytics 8.4.215,
  opencv-python-headless 5.0.0.93, numpy 2.5.4.
- **El modelo:** YOLO11n de una sola clase (`ball`), entrenado a imgsz 1280.
  - Revisión fijada: `63666b30e2a4973e089c982769f146af54530750`. El sha256 del `.pt` coincide con su puntero LFS.
  - Pesos en fp16.
- **Escaneo del pickle:** solo referencia `torch`, `ultralytics`, `collections` y `__builtin__.set` (el nombre de
  Python 2 que escribe el protocolo 2; normalizado a `builtins`). Se carga con `ULTRALYTICS_SAFE_LOAD=1`, es decir,
  `weights_only` con una lista de permitidos.
- **Sin conexiones:** `YOLO_OFFLINE=1`, sin autoinstalación y sin `sync`.
- **El dataset:** imágenes de 1920×1080. El balón mide 12,6 px de mediana (p5–p95: 7,7–20,8 en test, 8,1–19,9 en
  train).
- **El montaje es correcto:** con las imágenes tal cual, recall de 0,872 con 0,10 de confianza y de 0,864 con 0,25; a
  imgsz 1280, 0,840 y 0,760, en línea con la ficha del modelo (0,80).

Recall y falsos positivos por imagen (FP/img), con confianza 0,10 / 0,25, según el diámetro del balón b en la imagen
reducida. «×2» es reducir a b y ampliar ×2 antes de detectar: la red ve 2b.

| b (px) | tal cual: recall | tal cual: FP/img | ×2: recall | ×2: FP/img |
|---|---|---|---|---|
| 3 | 0,160 / 0,120 | 0,37 / 0,16 | 0,720 / 0,536 | 0,22 / 0,07 |
| 4 | 0,352 / 0,224 | 0,26 / 0,06 | **0,904 / 0,824** | 0,15 / 0,06 |
| 5 | 0,488 / 0,360 | 0,12 / 0,04 | 0,912 / 0,872 | 0,25 / 0,10 |
| 6 | 0,608 / 0,496 | 0,12 / 0,02 | 0,912 / 0,864 | 0,48 / 0,24 |
| 8 | 0,863 / 0,778 | 0,09 / 0,04 | 0,932 / 0,897 | 1,20 / 0,64 |
| 10 | 0,898 / 0,867 | 0,11 / 0,03 | 0,949 / 0,918 | 2,22 / 1,18 |

- **Lo que falla:** son balones sin ninguna detección, no detecciones mal colocadas.
- **Los falsos positivos de ×2:** caen lejos del balón (mediana de 22 a 63 radios) y crecen con el área de la imagen.
- **Tiempo por imagen en CPU** (de 4 a 14 hilos):
  - entrada de 640×640: de 43 a 72 ms, de 2,4 a 4,0 horas para 199.319 frames;
  - 1920×1088: de 244 a 375 ms, de 13,5 a 20,8 horas;
  - 3840×2176: de 1,4 a 2,0 s, de 79 a 113 horas.
  - Decodificar un 1080p sintético (mp4v): unos 1.000 fps con `read()` y 3.000 con `grab()`. No se probó H.264.
- **Determinismo:**
  - con el mismo número de hilos, idéntico bit a bit, en el mismo proceso y entre procesos;
  - con distinto número de hilos, difiere en el último bit: hasta 0,005 px en las cajas y 3,6e-7 en la confianza;
  - entre máquinas: sin medir.
- **Detalles para el código:** ultralytics pone torch a 8 hilos al preparar el predictor, así que los hilos se fijan
  después del calentamiento. Instalar `ultralytics` arrastra `opencv-python`, que pisa al `-headless`: hay que dejar
  solo uno.
- **Límite:** son imágenes del mismo tipo que las de entrenamiento. En nuestro vídeo el acierto será menor
  [inferencia].
- **Lectura con la regla:** falta `b_partido` (puerta 1a). Si el balón mide 4 px o más, la variante ×2 pasa con cualquiera
  de los dos umbrales (recall de 0,82 a 0,90, FP/img de 0,06 a 0,15). Su tiempo cabe en 8 horas solo si se detecta en un
  recorte alrededor del balón del ATD: uno de 320 px ampliado ×2 es una entrada de 640×640, unas 3 horas en esta CPU; la
  imagen entera ×2 no cabe. Tal cual solo pasa desde 6 px.
