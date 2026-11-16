# Bitácora: el balón sacado del vídeo táctico (16/11)

> **Cerrada (16/11, 22:10): la línea se paró en la puerta 1b, que dio «NO SIGUE».** Falla la condición 2: el 40,7 %
> de las detecciones cae a más de 5 m del balón del ATD, y el límite era el 10 %. Esta copia de `main` es la versión de
> la mañana. El detalle (las reglas posteriores, el resultado de la 1b y su lectura) está en la rama
> `exp/balon-video`, en este mismo fichero. La decisión está en `docs/decisiones.md`, entrada del 16/11 «la línea del
> balón del vídeo se para».

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

## Puerta 2: ¿entra en la entrega? (regla de entrada fijada ahora; los detalles, antes de medir)

Es la tercera excepción a «lo que no ha ganado en el harness no entra»: la DFL no tiene vídeo. Esta línea tiene su
propia regla y no usa la del «límite de daño» de los cambios pequeños (`docs/decisiones.md`, 16/11).

1. **En la DFL, con una degradación «como el vídeo»** calibrada solo con la puerta 1b (el balón sin suavizar, con la
   cobertura y el error de posición medidos; nunca con la ventana pública), B5 con ese balón frente a `main`:
   - con control, +0,01 o más en las dos condiciones que votan y ganando en 6 de 7 partidos, con el `D` de las
     etiquetas y con el propio;
   - con el flag, no pierde más de 0,005 en ninguna celda.
2. **Entrega de prueba frente a `equipo_v8`,** con criterios de daño escritos aquí antes de generarla.
3. **Reproducible:** el comando único regenera la entrega byte a byte dos veces en una máquina y una en otra (con la
   detección dentro: las detecciones del partido no se pueden publicar). Si no, no entra.
4. **Tiempo:** el comando entero cabe en 8 horas en la máquina de referencia que se documente.
5. **Licencias:** el modelo y `ultralytics` son AGPL-3.0; se declara en el documento técnico, con el dataset
   (CC BY 4.0) y sus autores.

**Dónde va lo que sale del partido:** la caché de detecciones es dato del partido derivado. Va en
`MTAH_DATA_DIR/tactical/` con un nombre que empiece por `BAR-ATH_tactical_` (lo cubre el bloqueo de
`.claude/settings.json`), nunca en el repo ni en `~/mtah2027-salidas/`.

## Resultados

(vacío)
