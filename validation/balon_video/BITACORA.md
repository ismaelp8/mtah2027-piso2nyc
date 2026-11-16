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

**Dónde va lo que sale del partido:** la caché de detecciones es dato del partido derivado. Va en
`MTAH_DATA_DIR/tactical/` con un nombre que empiece por `BAR-ATH_tactical_` (lo cubre el bloqueo de
`.claude/settings.json`), nunca en el repo ni en `~/mtah2027-salidas/`.

## Resultados

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
