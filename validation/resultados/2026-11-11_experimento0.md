# Experimento 0 · 2026-11-11 · Claude (sesión de Ismael)

> ¿El flag por frame de la Bundesliga (DFL) se comporta como pide `CHALLENGE.md`? Pasos 1 y 2 de
> `validation/PASOS.md`. Solo agregados. Cada afirmación lleva **[medido]**, **[inferencia]** o
> **[sin verificar]**. El registro paso a paso está en `validation/experimento0/BITACORA.md`.

**Lectura en tres líneas:**

1. **`D` sí:** el balón muerto de la DFL cubre todo balón fuera de juego y cumple en los 7 partidos
   **[medido]**.
   - Empieza 3–4 frames después de que el balón cruce la línea.
   - Acaba en el golpeo del reinicio o pocos frames después: en el primer frame activo, el jugador del
     equipo del flag está a 0,75 m del balón (mediana) y el 87 % a 2 m o menos.
2. **Cambio de posesión no:** el flag pasa al rival en su primer toque, haya control o no **[medido]**:
   - toques sin control del rival entre dos controles del mismo equipo: el flag marca al rival en el
     85 %, frente al 10 % del placebo;
   - en el 81 % de los casos en que el flag era del otro equipo justo antes, cambia en ese toque.

   Se parece a una regla de "último toque" **[inferencia]**.
3. **Sorpresa:** mientras el flag dice inactivo, la posición del balón está congelada (100 % de los
   frames `D`) y salta al reanudar (mediana de 6,2 m). En la DFL, la posición del balón delata el `D`.
   Los jugadores no se congelan **[medido]**.

- **Código:** rama `exp/experimento-0`, carpeta `validation/experimento0/`. Las cifras de este
  fichero salen del commit `65d552f` (solo commits locales; sin push).
- **Datos:** Bundesliga (Bassek, Rein, Weber y Memmert, 2025), figshare
  10.6084/m9.figshare.28196177.v1, CC BY 4.0, 7 partidos.
- **Comandos** (todos imprimen solo agregados; los detalles van en JSON junto a la caché, fuera del
  repo):
  - `python validation/scripts/descargar_datos_abiertos.py dfl` (paso 1)
  - `python validation/experimento0/dfl_lector.py <partido>`, uno cada vez (caché `.npz`)
  - `python validation/experimento0/pruebas_sinteticas.py` (todas las pruebas: OK)
  - `python validation/experimento0/parada2_resumen.py` (2a, 2b, C1–C11)
  - `python validation/experimento0/parada3.py` (2c, 2d, 2e, 2g, 1a, 1b, sensibilidad: 46,1 s y
    457 MB de pico con los 7 partidos)
  - `python validation/experimento0/diagnostico_congelado.py` (cuánto toca el balón congelado a
    toques, controles y 2g)
  - `python validation/experimento0/parada3_tablas.py` (las tablas de este fichero)
- **kloppy:** 3.18.0. Solo se usó para comprobar el lector propio, con `coordinates="sportec"` para
  tener metros.

## Resumen para Ismael

**Qué se ha hecho, en cuatro pasos:**

1. **Descargar los 7 partidos de la Bundesliga** (2,6 GB en 4 minutos, todos los ficheros
   verificados).
2. **Leerlos con un lector propio.** kloppy necesitaba 4,5 GB de memoria y casi 2 minutos por partido;
   el lector propio tarda unos 15 s y usa menos de 1 GB. Se comprobó que da exactamente los mismos
   frames que dice el artículo (1.002.644), lo mismo que kloppy y que no le falta ningún frame.
3. **Sacar la etiqueta H/A/D de cada frame y describirla** (parada 2):
   - el balón está muerto el 45 % del tiempo;
   - hay unas 100 paradas por partido;
   - hay 3.061 posesiones, con una mediana de 3,7 s; el 12,5 % dura menos de 1 s.
4. **Medir cuándo cambian los flags** (parada 3). Los criterios se escribieron antes de mirar, cada
   medida tiene su placebo (la misma medida en momentos al azar) y cada parámetro se movió en 21
   variaciones.

**Qué hemos aprendido:**

- **El balón muerto de la DFL es como el `D` del reto.** Pasa a muerto unos 3–4 frames después de que
  el balón salga y vuelve a vivo en el golpeo del saque o muy poco después. Cubre todos los saques de
  banda, de puerta y córners. Sirve tal cual.
- **El cambio de posesión no es como el del reto.** La DFL da la posesión al rival en cuanto la toca,
  aunque sea un toque sin control: un despeje, un desvío o un rechace. El reto dice que eso no cambia la
  posesión. Pasa en los 7 partidos y con cualquier ajuste de los parámetros: en esos toques, el flag
  marca al rival en el 85 % de los casos, frente al 10 % del placebo.
- **Sorpresa: mientras el balón está muerto, la DFL lo deja quieto donde estaba y lo hace saltar al
  reanudar.** Si se entrena o se prueba un detector de balón muerto con estos datos sin tapar el balón
  en esos frames, el balón le chiva la respuesta. Los jugadores sí se mueven con normalidad.

**Qué hay que decidir (tú):** si usamos la posesión de la DFL tal cual o corregida. Hay dos lecturas:

- la DFL marca "quién tocó el último" y el reto pide "quién controla", y hay que corregirla;
- la GT del reto se generó de forma parecida a la DFL (sale del flag de un tracking corregido), y
  entonces corregirla nos alejaría de la GT.

Con estos datos no se puede saber cuál es. La propuesta es generar las dos versiones de etiquetas,
medir con las dos y, si te parece, preguntar a la organización si su GT cambia de equipo con un toque
sin control. Quitar solo las posesiones de menos de 1 s no bastaría: la mayoría de las rachas que crea
un toque duran más (mediana de 2 s).

**Qué falta:**

- 2f (etiquetas a partir de los eventos de la DFL), que necesita reglas fijadas antes de medir;
- el paso 3 (Barça como local), que depende de D15 y D16;
- en la rama hay dos commits antiguos (`844a358` y `ac7a3d7`) con la ruta local del entorno virtual en
  la bitácora. Se quitó después, pero sigue en el historial. No se ha subido nada; decides tú si se
  reescribe antes del push.

## Comprobaciones de lectura (D8, D9)

| partido | local en `teams[0]` | valores de `ball_state` | saltos de `frame_id` dentro de las partes |
|---|---|---|---|
| J03WMX | sí, comprobado con kloppy aunque en el XML vaya primero el visitante | `alive` / `dead` (0/1 en el XML) | 0 |
| J03WN1 | el lector propio lo toma de `Role`; no comprobado con kloppy | 0/1 en el XML | 0 |
| J03WOH | ídem | 0/1 | 0 |
| J03WOY | ídem | 0/1 | 0 |
| J03WPY | ídem | 0/1 | 0 |
| J03WQQ | ídem | 0/1 | 0 |
| J03WR9 | ídem | 0/1 | 0 |

**[medido]** en los 7:

- frames por parte igual a `TotalTime` / 40 + 1, y 1.002.644 en total, como el artículo;
- ningún salto de `N` ni de `T`, ningún frame repetido;
- flags siempre presentes;
- `BallPossession` 1 = local en los 7 (C11: del 97,0 % al 99,4 % de los frames estables).

En J03WMX, kloppy y el lector propio coinciden frame a frame en el balón, en los dos flags y en las
66.000 posiciones de jugador comprobadas. Las coordenadas por defecto de kloppy 3.18 no son metros: van
de 0 a 1. Con `coordinates="sportec"` sí lo son (corregido en `PASOS.md`).

## 2a. Descripción por partido (D5)

De `parada2_resumen.py` (parada 2) **[medido]**:

| partido | frames | % D | paradas | posesiones | posesiones por minuto vivo | mediana (s) | p10 (s) | p90 (s) | < 1 s | < 2 s | < 3 s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J03WMX | 145.967 | 41,5 | 103 | 511 | 8,98 | 3,00 | 0,68 | 15,28 | 16,8 % | 37,4 % | 49,7 % |
| J03WN1 | 141.561 | 51,7 | 107 | 500 | 10,97 | 3,12 | 0,80 | 12,08 | 15,2 % | 34,2 % | 47,6 % |
| J03WOH | 137.214 | 47,6 | 102 | 402 | 8,38 | 3,94 | 0,88 | 18,54 | 11,4 % | 27,4 % | 39,1 % |
| J03WOY | 142.536 | 46,5 | 113 | 456 | 8,97 | 3,60 | 1,04 | 17,58 | 9,0 % | 28,1 % | 43,2 % |
| J03WPY | 146.211 | 44,3 | 97 | 421 | 7,75 | 3,84 | 0,72 | 20,60 | 13,5 % | 29,5 % | 41,6 % |
| J03WQQ | 142.345 | 40,7 | 99 | 401 | 7,13 | 4,68 | 1,08 | 21,28 | 9,2 % | 25,2 % | 38,7 % |
| J03WR9 | 146.810 | 41,9 | 92 | 370 | 6,51 | 4,24 | 0,96 | 23,60 | 11,1 % | 25,4 % | 38,4 % |
| los 7 juntos | 1.002.644 | 44,8 | 713 | 3.061 | 8,30 | 3,68 | 0,84 | 18,60 | 12,5 % | 30,0 % | 43,1 % |

- **Medida R** (posesiones de menos de 1 s intercaladas entre dos del mismo rival / todas): 6,89 % con
  los 7. Está entre los dos cortes (3 % y 10 %), así que no decide. Por partido, del 3,95 % al 10,76 %.
- J03WN1 tiene un 51,7 % de `D`: el visitante juega con 10 casi todo el partido.

**Histograma de duraciones en escala logarítmica** (pedido en la parada 2) **[medido]**:

Bordes (s): 0,04 · 0,06 · 0,10 · 0,16 · 0,25 · 0,40 · 0,63 · 1,00 · 1,59 · 2,52 · 4,00 · 6,34 · 10,05 · 15,92 · 25,24 · 40,00 · 63,40 · 100,47 · 159,24 · 252,38 · 400,00

| partido | recuentos | máximos locales (s: n) | dos modas (regla fijada) |
|---|---|---|---|
| J03WMX | 1 2 2 13 4 18 54 62 74 63 68 56 45 22 16 8 3 0 0 0 | 0,06: 2; 0,16: 13; 1,59: 74; 4,00: 68 | sí |
| J03WN1 | 2 0 6 12 7 9 41 59 77 80 73 63 40 16 12 3 0 0 0 0 | 0,04: 2; 0,16: 12; 2,52: 80 | sí |
| J03WOH | 1 1 2 3 2 11 29 34 60 59 56 57 37 28 17 5 0 0 0 0 | 0,04: 1; 0,16: 3; 1,59: 60; 6,34: 57 | sí |
| J03WOY | 0 1 1 7 1 11 23 54 74 80 74 45 35 31 12 5 2 0 0 0 | 0,06: 1; 0,16: 7; 2,52: 80 | sí |
| J03WPY | 1 2 4 8 3 14 27 38 53 71 58 47 37 25 24 8 1 0 0 0 | 0,16: 8; 2,52: 71 | sí |
| J03WQQ | 1 2 2 2 5 7 19 32 71 41 56 57 50 29 18 7 2 0 0 0 | 0,06: 2; 1,59: 71; 6,34: 57 | no |
| J03WR9 | 0 1 5 7 4 7 20 32 45 57 54 49 26 28 19 11 5 0 0 0 | 0,16: 7; 2,52: 57; 15,92: 28 | sí |
| los 7 | 6 9 22 52 26 77 213 311 454 451 439 374 270 179 118 47 13 0 0 0 | 0,16: 52; 1,59: 454 | sí |

- Con los 7 juntos hay **dos modas**: una pequeña en 0,16–0,25 s (4 a 6 frames, 52 posesiones) y la
  principal en 1,6–2,5 s. Entre las dos, 26 posesiones en 0,25–0,40 s.
- No es un efecto de que los frames sean enteros: el intervalo del valle y el del pico pequeño contienen
  el mismo número de duraciones posibles (3 frames cada uno).
- Por partido, la regla fijada da dos modas en 6 de 7, pero el pico pequeño tiene entre 3 y 13
  posesiones: por separado, es débil.
- Las rachas de 4–6 frames encajan con los cambios de flag por un toque (2g) **[inferencia]**.

## 2b. Huella de retrasos (solo informativa, D21: no decide nada)

| | 1 | 3 | 8 | 25 |
|---|---|---|---|---|
| oficial (`EVALUATION.md`) | 1,0000 | 0,9818 | 0,8933 | 0,6539 |
| DFL, los 7 juntos | 0,9905 | 0,9590 | 0,8594 | 0,5522 |
| DFL, partido con la huella más baja (J03WMX) | 0,9898 | 0,9503 | 0,8184 | 0,4943 |
| DFL, partido con la huella más alta (J03WQQ) | 0,9920 | 0,9731 | 0,8933 | 0,6125 |

Comparación entre fuentes abiertas: falta la de eventos DFL (2f, no hecho) y la de eventos del Barça
(paso 3).

## 2c. Cambios H↔A (D3, D4, D7)

Lo que pide `PASOS.md` (variante original, los 7) **[medido]**:

| medida | p10 | mediana | p90 |
|---|---|---|---|
| distancia del balón al jugador más cercano del equipo nuevo (m) | 0,19 | 0,62 | 1,13 |
| distancia del balón al jugador más cercano del equipo antiguo (m) | 0,63 | 2,07 | 6,65 |
| desfase del cambio respecto al toque del equipo nuevo (frames, cambio − toque; negativo = el flag cambia antes del toque) | −6 | 0 | +2 |

- **Cambios con un jugador del equipo nuevo a ≤ 1,5 m en ±1 s:** 99,6 %. En el placebo (frames estables
  al azar): 21,8 % para el equipo sin el flag y 96,1 % para el que lo tiene.
- **Cambios con un toque del equipo nuevo en ±2 s:** 87,5 %; en el placebo, 2,3 %.
- **Umbrales para "toque":** cambio de velocidad de ≥ 3 m/s entre la media de los 4 frames siguientes y
  la de los 4 anteriores, máximo local en ±4 frames, jugador a ≤ 1,5 m. Se probó con trayectorias
  sintéticas (golpeo, desvío de 60°, balón que pasa de largo a 0,3 m sin tocarlo y ruido). En datos
  reales, el 96,2 % de los pases de los eventos tiene un toque del mismo equipo a ±2 s, frente al 58,4 %
  de instantes al azar.

| partido | distancia equipo nuevo p10 / p50 / p90 (m) | distancia equipo antiguo (m) | con toque del nuevo en ±2 s % | desfase toque − cambio p10 / p50 / p90 (frames) | placebo: toque del otro en ±2 s % | nuevo a ≤ 1,5 m en ±1 s % | placebo: otro / flag a ≤ 1,5 m % | 3a: cambio en el aire % |
|---|---|---|---|---|---|---|---|---|
| J03WMX | 0,13 / 0,61 / 1,16 | 0,59 / 1,99 / 6,32 | 86,0 | -2 / 0 / 8 | 1,5 | 99,3 | 24,1 / 96,6 | 0,0 |
| J03WN1 | 0,15 / 0,64 / 1,08 | 0,69 / 2,09 / 6,50 | 88,1 | -1 / 0 / 7 | 3,7 | 99,2 | 27,5 / 94,7 | 0,3 |
| J03WOH | 0,23 / 0,59 / 1,02 | 0,52 / 1,79 / 6,11 | 86,4 | -2 / 0 / 2 | 1,8 | 100,0 | 22,0 / 95,1 | 0,0 |
| J03WOY | 0,21 / 0,57 / 1,02 | 0,59 / 2,04 / 6,28 | 85,5 | -2 / 0 / 2 | 1,6 | 100,0 | 22,4 / 96,3 | 0,0 |
| J03WPY | 0,24 / 0,62 / 1,15 | 0,67 / 2,04 / 5,93 | 88,0 | -2 / 0 / 19 | 2,4 | 99,7 | 20,4 / 96,8 | 0,0 |
| J03WQQ | 0,33 / 0,72 / 1,31 | 0,65 / 2,32 / 7,86 | 88,4 | -3 / 0 / 5 | 3,8 | 99,3 | 21,6 / 96,2 | 1,3 |
| J03WR9 | 0,22 / 0,61 / 1,09 | 0,83 / 2,25 / 6,81 | 90,6 | -2 / 0 / 1 | 1,2 | 100,0 | 14,8 / 96,8 | 0,0 |
| 1ª (J03WMX, J03WN1) | 0,14 / 0,63 / 1,15 | 0,60 / 2,03 / 6,48 | 87,0 | -2 / 0 / 8 | 2,6 | 99,3 | 25,8 / 95,7 | 0,1 |
| Düsseldorf (5) | 0,23 / 0,62 / 1,12 | 0,63 / 2,08 / 6,81 | 87,7 | -2 / 0 / 3 | 2,1 | 99,8 | 20,2 / 96,3 | 0,3 |
| los 7 | 0,19 / 0,62 / 1,13 | 0,63 / 2,07 / 6,65 | 87,5 | -2 / 0 / 6 | 2,3 | 99,6 | 21,8 / 96,1 | 0,2 |

La tabla de abajo da el desfase con el signo contrario (toque − cambio).

**Criterios del punto 2 fijados antes de medir** (bitácora):

- **2b:** cambio seguido de control del equipo nuevo (el mismo jugador, el más cercano, a ≤ 1 m durante
  ≥ 12 frames) entre 1 s antes y 2 s después.
- **2c:** momento del inicio de ese control.
- **"Retención":** las columnas así llamadas usan la retención de 5 frames del mismo equipo con la
  ventana nueva (−1 s / +2 s).
  - El criterio original exacto de 2b era la retención en ±1 s. Es la fila "ventana 2b ±1 s" de la
    sensibilidad: 59,8 % con los 7, entre medias, y entre medias en los 7 partidos (59,6 % solo en
    juego).
  - El 2c original buscaba la primera retención en ±2 s. Aquí se toma la más cercana al cambio.

| partido | cambios | por min vivo | control % | solo toque % | nada % | placebo control: otro / flag % | control normalizado % | retención 5 frames % | placebo retención: otro / flag % | momento del control p10 / p50 / p90 (frames) | sin control en ±2 s % | a ±3 / ±8 / ±25 frames % | momento de la retención p10 / p50 / p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| J03WMX | 408 | 7,17 | 41,7 (40,0) | 53,9 | 4,4 | 1,1 / 85,5 | 48 | 70,1 (69,1) | 2,9 / 93,8 | -15 / -1 / 34 | 58,1 | 35,7 / 49,1 / 71,9 | -13 / -3 / 29 |
| J03WN1 | 394 | 8,64 | 43,4 (42,1) | 54,1 | 2,5 | 3,5 / 74,3 | 56 | 68,3 (67,8) | 7,4 / 90,5 | -18 / -3 / 36 | 55,8 | 22,4 / 40,8 / 77,0 | -16 / -3 / 34 |
| J03WOH | 301 | 6,28 | 46,8 (46,5) | 50,8 | 2,3 | 1,7 / 75,8 | 61 | 70,8 (70,4) | 4,2 / 92,4 | -15 / -2 / 38 | 53,5 | 25,7 / 41,4 / 67,9 | -14 / -2 / 30 |
| J03WOY | 344 | 6,76 | 36,9 (36,3) | 61,0 | 2,0 | 2,2 / 75,8 | 47 | 68,6 (68,6) | 4,5 / 90,5 | -14 / -2 / 35 | 63,4 | 29,4 / 44,4 / 79,4 | -13 / -2 / 31 |
| J03WPY | 324 | 5,97 | 37,7 (37,7) | 59,3 | 3,1 | 1,4 / 78,5 | 47 | 65,4 (64,8) | 4,3 / 93,7 | -10 / -1 / 38 | 62,3 | 32,0 / 45,9 / 67,2 | -10 / -3 / 33 |
| J03WQQ | 302 | 5,37 | 52,3 (51,7) | 46,0 | 1,7 | 2,1 / 82,6 | 62 | 72,5 (71,2) | 5,0 / 94,0 | -17 / -1 / 38 | 48,3 | 25,0 / 44,2 / 71,2 | -15 / -2 / 31 |
| J03WR9 | 278 | 4,89 | 43,2 (42,1) | 52,9 | 4,0 | 1,7 / 80,1 | 53 | 70,5 (70,1) | 4,0 / 92,9 | -12 / -2 / 38 | 57,2 | 32,8 / 50,4 / 74,8 | -10 / -3 / 27 |
| 1ª (J03WMX, J03WN1) | 802 | 7,82 | 42,5 (41,0) | 54,0 | 3,5 | 2,4 / 79,9 | 52 | 69,2 (68,5) | 5,1 / 92,2 | -17 / -2 / 36 | 57,0 | 29,0 / 44,9 / 74,5 | -15 / -3 / 31 |
| Düsseldorf (5) | 1.549 | 5,82 | 43,1 (42,6) | 54,3 | 2,6 | 1,8 / 78,6 | 54 | 69,5 (68,9) | 4,4 / 92,7 | -14 / -2 / 38 | 57,2 | 28,7 / 45,1 / 71,9 | -12 / -2 / 32 |
| los 7 | 2.351 | 6,38 | 42,9 (42,1) | 54,2 | 2,9 | 2,0 / 79,0 | 53 | 69,4 (68,8) | 4,6 / 92,5 | -15 / -2 / 37 | 57,1 | 28,8 / 45,0 / 72,8 | -13 / -3 / 31 |

Histograma del momento del control, los 7 (frames, control − cambio): [-50, -25): 46; [-25, -12): 80; [-12, -8): 53; [-8, -3): 150; [-3, 4): 290; [4, 9): 14; [9, 13): 17; [13, 26): 130; [26, 51): 228

**2g. El sentido que pide el reto: ¿un toque sin control del rival cambia el flag?** Se eligen los
casos sin mirar el flag: un toque del equipo Y, sin control de Y, entre dos controles del equipo X
separados como mucho 5 s, y sin `D` entre medias.

| partido | toques del rival sin control | el flag pasa al rival % | huecos | huecos con cambio % | flag del equipo de los controles 3 frames antes % | … y luego pasa al rival % | de esos, cambia en ≤ 2 frames % | cambia a 0 / ≤ 2 / ≤ 5 frames % | racha del rival p10 / p50 / p90 (s) | racha < 1 s % | aéreos · cambia % | placebo (toques propios): huecos · cambia % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| J03WMX | 35 (34) | 85,7 (88,2) | 31 | 83,9 | 71,4 | 57,1 | 68,0 | 54,3 / 77,1 / 80,0 | 0,79 / 1,84 / 3,82 | 20,0 | 6 · 83,3 | 212 · 12,3 |
| J03WN1 | 43 (40) | 81,4 (80,0) | 35 | 77,1 | 69,8 | 51,2 | 70,0 | 53,5 / 79,1 / 79,1 | 0,54 / 1,96 / 3,93 | 28,6 | 7 · 85,7 | 113 · 15,9 |
| J03WOH | 34 (33) | 91,2 (90,9) | 26 | 88,5 | 70,6 | 64,7 | 87,5 | 58,8 / 88,2 / 88,2 | 1,16 / 2,32 / 5,36 | 9,7 | 9 · 88,9 | 137 · 11,7 |
| J03WOY | 18 (17) | 88,9 (88,2) | 17 | 88,2 | 66,7 | 55,6 | 83,3 | 61,1 / 88,9 / 88,9 | 1,30 / 2,40 / 4,34 | 6,2 | 3 · 100,0 | 136 · 8,1 |
| J03WPY | 28 (28) | 85,7 (85,7) | 25 | 84,0 | 71,4 | 57,1 | 70,0 | 57,1 / 78,6 / 85,7 | 0,60 / 1,64 / 2,52 | 25,0 | 10 · 100,0 | 177 · 10,7 |
| J03WQQ | 23 (22) | 73,9 (72,7) | 23 | 73,9 | 82,6 | 56,5 | 57,9 | 47,8 / 65,2 / 65,2 | 0,82 / 2,04 / 3,29 | 11,8 | 5 · 100,0 | 183 · 5,5 |
| J03WR9 | 22 (22) | 90,9 (90,9) | 19 | 94,7 | 72,7 | 68,2 | 93,8 | 50,0 / 90,9 / 90,9 | 0,20 / 1,96 / 3,64 | 15,0 | 3 · 100,0 | 182 · 7,7 |
| 1ª (J03WMX, J03WN1) | 78 (74) | 83,3 (83,8) | 66 | 80,3 | 70,5 | 53,8 | 69,1 | 53,8 / 78,2 / 79,5 | 0,54 / 1,96 / 3,92 | 24,6 | 13 · 84,6 | 325 · 13,5 |
| Düsseldorf (5) | 125 (122) | 86,4 (86,1) | 110 | 85,5 | 72,8 | 60,8 | 78,0 | 55,2 / 82,4 / 84,0 | 0,71 / 2,06 / 4,21 | 13,9 | 30 · 96,7 | 815 · 8,6 |
| los 7 | 203 (196) | 85,2 (85,2) | 176 | 83,5 | 71,9 | 58,1 | 74,7 | 54,7 / 80,8 / 82,3 | 0,64 / 2,00 / 4,12 | 17,9 | 43 · 93,0 | 1.140 · 10,0 |

Lectura **[medido]**:

- **El flag marca al rival en el 85,2 % de esos toques** (83,5 % contando una vez cada hueco entre dos
  controles). Por partido, entre el 73,9 % y el 91,2 %, con 18–43 toques por partido. El corte de "no
  cumple" era del 30 %.
- **Placebo:** con un toque del mismo equipo X entre sus dos controles, el flag pasa a Y en el 10,0 % de
  los huecos (1.140 huecos). La diferencia es del toque del rival, no de la ventana.
- **Es en el toque, no antes:** en el 71,9 % de los casos el flag es de X 3 frames antes del toque. De
  esos, el 81 % pasa a Y, y el 74,7 % lo hace a 2 frames o menos del toque.
- **Contando solo los cambios de X a Y:** el 58,1 % de todos los toques.
- **El resto del 85 %:** casos en que el flag ya era de Y antes del toque. Puede haber, por ejemplo,
  un toque anterior de Y en el mismo hueco.
- **Sensibilidad:** entre el 81 % y el 87 % por toque (del 80 % al 86 % por hueco) en todas las
  variaciones de las dos variantes.
- **Duración de la racha del rival que crea el toque:** mediana de 2,0 s (p10 0,64 s, p90 4,1 s). Solo
  el 17,9 % dura menos de 1 s.

## 2d. Paso a inactivo (D5, D6)

| medida | valor |
|---|---|
| % de pasos a inactivo con el balón fuera del campo | 66,1 % en el inicio del `D` (68,3 % cruzó una línea en los 3 s anteriores) |
| desfase desde que el balón cruza la línea (frames, mediana y p90) | banda 4 y 10; fondo 3 y 8 |
| duración de la parada por tipo aproximado (mediana, s): banda / fondo / dentro del campo | 13,8 / 28,1 / 29,6 |

- pasos a inactivo: 710; tipo aproximado: banda 305, fondo 180, dentro 225;
- balón fuera del campo en el inicio del `D`: 66,1 %; cruzó una línea en los 3 s anteriores: 68,3 %;
- flag constante durante todo el `D`: 99,6 %; igual al del último frame activo: 30,8 %;
- distancia a la línea más cercana en el inicio del `D` (m, > 0 fuera): p10 / p50 / p90 = -16,25 / 0,30 / 1,24;
- frames desde que cruza la línea hasta el `D`, p10 / p50 / p90: banda 2 / 4 / 10; fondo 1 / 3 / 8
- duración de la parada (s), p10 / p50 / p90: banda 4,8 / 13,8 / 27,1; fondo 12,0 / 28,1 / 61,0; dentro 8,3 / 29,6 / 58,3

| partido | fuera en el inicio % | banda / fondo / dentro |
|---|---|---|
| J03WMX | 78,6 | 54 / 28 / 21 |
| J03WN1 | 69,8 | 49 / 27 / 30 |
| J03WOH | 63,4 | 40 / 28 / 33 |
| J03WOY | 68,8 | 56 / 24 / 32 |
| J03WPY | 72,2 | 41 / 31 / 25 |
| J03WQQ | 40,4 | 26 / 15 / 58 |
| J03WR9 | 68,5 | 39 / 27 / 26 |
| 1ª (J03WMX, J03WN1) | 74,2 | 103 / 55 / 51 |
| Düsseldorf (5) | 62,7 | 202 / 125 / 174 |
| los 7 | 66,1 | 305 / 180 / 225 |

**Punto 1 del reto: `D` cubre todo balón fuera de juego.**

| tipo | reinicios | con fin de D a ±5 s % | ±3 s % | ±2 s % | desfase evento − fin de D p10 / p50 / p90 (s) |
|---|---|---|---|---|---|
| ThrowIn | 308 | 99,4 | 96,8 | 72,7 | -2,32 / -0,76 / 1,90 |
| FreeKick | 172 | 95,9 | 91,9 | 74,4 | -2,08 / -0,52 / 2,24 |
| GoalKick | 119 | 100,0 | 89,9 | 68,1 | -2,36 / -0,56 / 2,75 |
| CornerKick | 57 | 100,0 | 80,7 | 56,1 | -3,67 / -1,56 / 0,08 |
| KickOff | 18 | 94,4 | 61,1 | 33,3 | -3,59 / -2,44 / -0,22 |
| RefereeBall | 15 | 73,3 | 40,0 | 20,0 | -4,52 / -2,28 / -0,20 |
| Penalty | 3 | 100,0 | 100,0 | 100,0 | -0,71 / -0,04 / 0,47 |

Placebo (instantes al azar, ±5 s): 14,6 %. Fines de `D` emparejados con un reinicio: 97,0 % de 699; sin reinicio: 21 (evento más cercano: Play 9, FreeKick 4, Foul 3, ninguno a 10 s 2, VideoAssistantAction 1, KickOff 1, BallClaiming 1).

| partido | saque de banda % | de puerta % | córner % | falta % | fines de D emparejados % | saque inicial − primer frame activo, 1ª / 2ª parte (s) |
|---|---|---|---|---|---|---|
| J03WMX | 100,0 | 100,0 | 100,0 | 90,0 | 97,0 | -0,37 / 0,03 |
| J03WN1 | 95,7 | 100,0 | 100,0 | 96,3 | 94,3 | 2,25 / 1,89 |
| J03WOH | 100,0 | 100,0 | 100,0 | 93,8 | 95,0 | -1,61 / -1,37 |
| J03WOY | 100,0 | 100,0 | 100,0 | 96,3 | 95,5 | -0,79 / -1,07 |
| J03WPY | 100,0 | 100,0 | 100,0 | 100,0 | 98,9 | -1,01 / -0,95 |
| J03WQQ | 100,0 | 100,0 | 100,0 | 100,0 | 100,0 | -0,31 / -0,51 |
| J03WR9 | 100,0 | 100,0 | 100,0 | 96,2 | 98,9 | -0,38 / -0,66 |
| 1ª (J03WMX, J03WN1) | 98,0 | 100,0 | 100,0 | 93,6 | 95,6 | — |
| Düsseldorf (5) | 100,0 | 100,0 | 100,0 | 96,8 | 97,6 | — |
| los 7 | 99,4 | 100,0 | 100,0 | 95,9 | 97,0 | — |

- **1a cumple en los 7**, con la ventana principal de ±5 s **[medido]**.
- Las ventanas de ±2 y ±3 s se fijaron como descriptivas, por el error de hora de los eventos. El
  script las marca como "no aguanta", pero no deciden.
- **El error de hora explica por qué caen [inferencia]:**
  - el saque inicial de cada parte queda entre −1,6 y +2,25 s del primer frame activo, y con un desfase
    parecido en las dos partes de cada partido (por ejemplo, +2,25 y +1,89 s en J03WN1);
  - el desfase evento − fin de `D` tiene la mediana negativa en todos los tipos.
- **Los fines de `D` sin reinicio** (21 de 699) tienen cerca sobre todo un pase o una falta. Puede ser
  un reinicio que los eventos registran como pase normal, o una falta con ventaja **[sin verificar]**.

| partido | frames en tramos fuera de ≥ 1 s (con D) | de ellos activos % (criterio fijado) | frames activos fuera, cualquier duración | por minuto vivo | episodios activos fuera de ≥ 1 s | el más largo (s) |
|---|---|---|---|---|---|---|
| J03WMX | 30.473 | 0,53 | 179 | 3,15 | 0 | 0 |
| J03WN1 | 29.412 | 0,62 | 229 | 5,02 | 0 | 0 |
| J03WOH | 26.100 | 0,47 | 122 | 2,54 | 0 | 0 |
| J03WOY | 17.749 | 0,75 | 135 | 2,65 | 0 | 0 |
| J03WPY | 24.082 | 0,57 | 138 | 2,54 | 0 | 0 |
| J03WQQ | 7.233 | 1,99 | 150 | 2,67 | 1 | 2,68 |
| J03WR9 | 25.019 | 0,54 | 138 | 2,43 | 1 | 1,40 |
| 1ª (J03WMX, J03WN1) | 59.885 | 0,58 | 408 | 3,98 | 0 | 0 |
| Düsseldorf (5) | 100.183 | 0,67 | 683 | 2,57 | 2 | 2,68 |
| los 7 | 160.068 | 0,64 | 1.091 | 2,96 | 2 | 2,68 |

- **1b cumple en los 7 [medido].**
- El criterio fijado (0,64 % de frames activos en tramos de ≥ 1 s fuera) usa como denominador sobre
  todo frames de parada: el balón congelado fuera de la línea.
- La medida que no depende de eso da lo mismo: en los 7 partidos solo hay **2 episodios** de 1 s o
  más con el balón a más de 0,5 m fuera y el flag activo (2,68 s y 1,40 s).
- Los frames activos fuera de cualquier duración (2,96 por minuto vivo) son los 3–4 frames que tarda el
  flag en pasar a inactivo al salir el balón.

## 2e. Paso a activo (D6)

| medida | valor |
|---|---|
| desfase entre el flag y el balón en movimiento (frames, mediana y p90) | 0 y 0 (medida nueva, solo con frames activos). Con el balón congelado solo puede dar 0 o más: dice que el flag no pasa a activo antes del golpeo, no que no lo haga después. Para eso, la fila siguiente |
| jugador del equipo del flag más cercano al balón en el primer frame activo | p10 / p50 / p90 = 0,20 / 0,75 / 2,51 m; el 69,8 % a ≤ 1 m y el 87,3 % a ≤ 2 m |
| % de paradas en las que el equipo del flag durante la parada es el del flag en el primer frame activo | 99,7 % |
| equipo del evento de reinicio emparejado = flag en el primer frame activo | 97,8 % (saque de banda 96,1 %, falta 100 %, de puerta 100 %, córner 96,5 %) |

| partido | balón quieto en los frames D % | salto del balón al reanudar p10 / p50 / p90 (m) | medida fijada: desfase p10 / p50 / p90 (artefacto) | medida nueva: desfase p10 / p50 / p90 | se mueve a 0 / ≤ 5 / ≤ 25 frames % | flag de la parada = equipo que reanuda % |
|---|---|---|---|---|---|---|
| J03WMX | 100,00 | 2,06 / 6,22 / 26,51 | -2 / -2 / -2 | 0 / 0 / 1 | 82,2 / 100,0 / 100,0 | 100,0 |
| J03WN1 | 100,00 | 1,66 / 6,13 / 21,64 | -2 / -2 / -2 | 0 / 0 / 0 | 88,6 / 95,2 / 98,1 | 100,0 |
| J03WOH | 100,00 | 1,67 / 5,88 / 25,44 | -2 / -2 / -2 | 0 / 0 / 0 | 96,0 / 100,0 / 100,0 | 100,0 |
| J03WOY | 100,00 | 1,82 / 6,85 / 24,55 | -2 / -2 / -2 | 0 / 0 / 0 | 94,6 / 98,2 / 100,0 | 100,0 |
| J03WPY | 100,00 | 1,53 / 5,84 / 22,17 | -2 / -2 / -2 | 0 / 0 / 0 | 92,6 / 98,9 / 100,0 | 100,0 |
| J03WQQ | 100,00 | 1,45 / 6,03 / 21,79 | -2 / -2 / -2 | 0 / 0 / 0 | 91,8 / 97,9 / 99,0 | 97,9 |
| J03WR9 | 100,00 | 1,70 / 5,66 / 24,62 | -2 / -2 / -2 | 0 / 0 / 0 | 94,4 / 100,0 / 100,0 | 100,0 |
| 1ª (J03WMX, J03WN1) | 100,00 | 1,74 / 6,20 / 24,36 | -2 / -2 / -2 | 0 / 0 / 1 | 85,4 / 97,6 / 99,0 | 100,0 |
| Düsseldorf (5) | 100,00 | 1,57 / 6,24 / 23,89 | -2 / -2 / -2 | 0 / 0 / 0 | 93,9 / 99,0 / 99,8 | 99,6 |
| los 7 | 100,00 | 1,63 / 6,22 / 23,98 | -2 / -2 / -2 | 0 / 0 / 0 | 91,4 / 98,6 / 99,6 | 99,7 |

- **La medida fijada en `PASOS.md` no sirve aquí.** Da −2 frames en todas las paradas porque el balón
  está congelado durante el `D` y salta al reanudar. La velocidad centrada de ±2 frames ve ese salto
  2 frames antes. Se apunta como artefacto y se da la medida nueva.
Todos los pasos a activo (699): jugador del equipo del flag más cercano al balón en el primer frame activo, p10 / p50 / p90 = 0,20 / 0,75 / 2,51 m; a ≤ 1 m / ≤ 2 m: 69,8 / 87,3 %.

| tipo de reinicio (emparejado a ±5 s) | n | jugador del flag más cercano p10 / p50 / p90 (m) | a ≤ 1 m % | equipo del evento = flag en el primer frame activo % |
|---|---|---|---|---|
| ThrowIn | 306 | 0,19 / 0,75 / 2,91 | 57,5 | 96,1 |
| FreeKick | 165 | 0,23 / 0,70 / 1,01 | 88,5 | 100,0 |
| GoalKick | 119 | 0,23 / 0,80 / 2,16 | 78,2 | 100,0 |
| CornerKick | 57 | 0,28 / 0,92 / 3,56 | 50,9 | 96,5 |
| KickOff | 17 | 0,27 / 0,59 / 1,06 | 88,2 | — |
| RefereeBall | 11 | 0,11 / 0,44 / 0,62 | 100,0 | — |
| Penalty | 3 | 0,88 / 0,99 / 1,61 | 66,7 | 100,0 |

Equipo del evento = flag, todos los tipos: 97,8 %.

- **Cuándo pasa a activo [medido]:**
  - en el primer frame activo, el balón está pegado a un jugador del equipo del flag (mediana
    0,75 m), así que el `D` acaba en el golpeo o muy cerca;
  - en la cola (p90 de 2,5 m; en saques de banda y córners, entre el 51 % y el 58 % a ≤ 1 m) el balón ya
    ha salido unos metros: el flag pasaría a activo unos frames después del golpeo **[inferencia]**.
    Con el balón congelado no se puede medir mejor.
- **El flag durante la parada [medido]:**
  - es constante en el 99,6 % de los `D`, y en las 696 que acaban en un reinicio, en todas
    (`diagnostico_congelado.py`);
  - solo coincide con el del último frame activo en el 30,8 %;
  - coincide con el equipo del evento de reinicio en el 97,8 %.

  Es decir, el flag pasa al equipo que reanuda en el primer frame del `D`.

| partido | frames D | con todos los jugadores quietos % | frames activos con todos quietos | velocidad media de los jugadores en D p10 / p50 / p90 (m/s) | en juego p10 / p50 / p90 (m/s) |
|---|---|---|---|---|---|
| J03WMX | 60.598 | 0,00 | 0 | 0,53 / 1,01 / 1,62 | 1,38 / 2,26 / 3,51 |
| J03WN1 | 73.183 | 0,00 | 0 | 0,54 / 0,98 / 1,62 | 1,32 / 2,16 / 3,55 |
| J03WOH | 65.268 | 0,00 | 0 | 0,53 / 1,05 / 1,69 | 1,47 / 2,43 / 3,74 |
| J03WOY | 66.249 | 0,00 | 0 | 0,62 / 1,06 / 1,81 | 1,47 / 2,37 / 3,64 |
| J03WPY | 64.751 | 0,00 | 0 | 0,46 / 0,97 / 1,65 | 1,41 / 2,29 / 3,72 |
| J03WQQ | 57.993 | 0,00 | 0 | 0,50 / 1,06 / 1,76 | 1,39 / 2,33 / 3,69 |
| J03WR9 | 61.494 | 0,00 | 0 | 0,53 / 1,03 / 1,73 | 1,32 / 2,10 / 3,38 |
| los 7 | 449.536 | 0,00 | 0 | 0,53 / 1,02 / 1,69 | 1,38 / 2,27 / 3,62 |

**Los jugadores no se congelan [medido]:** ningún frame `D` tiene a todos los jugadores quietos. Van
más despacio que en juego (mediana de 1,0 m/s frente a 2,3 m/s), pero se mueven. La fuga es solo de la
posición del balón.

## Posesiones cortas junto a un `D` (lo pidió la revisión de la parada 2)

De las 172 posesiones de menos de 1 s que tocan un `D`: 156 van justo antes, 11 justo después y 5 entre
dos `D`. Cuadra con las 172 de la parada 2 **[medido]**.

| variante | antes de D | después de D | entre dos D | antes: toque de Y % | antes: control de Y % | antes: balón fuera % | antes: toque sin control y fuera % | antes: reanuda X % (todas) | antes: reanuda X % (toque sin control y fuera) | después: toque de Y % | después: control de Y % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| original | 156 | 11 | 5 | 68,6 | 23,1 | 71,2 | 40,4 | 80,1 | 88,9 | 36,4 | 9,1 |
| solo_en_juego | 156 | 11 | 5 | 60,3 | 17,9 | 71,2 | 39,1 | 80,1 | 88,5 | 0,0 | 0,0 |

**Antes de un `D`** (X → y → `D`, con y del equipo Y):

- **Cota del toque de Y:** se mide si hay un toque de Y en la racha, no si Y dio el último toque. Las
  dos variantes acotan esa cifra (68,6 % y 60,3 %), sin dar el valor exacto.
- **Toque de Y sin control y balón fuera:** 40,4 % (original) y 39,1 % (solo en juego). Es el despeje o
  el desvío que manda el balón fuera.
- **Quién reanuda:** en esos casos, el otro equipo en el 88,9 %. En todas las cortas antes de un `D`,
  el 80,1 %. Encaja con que el flag siga al último que toca antes de salir **[inferencia]**.
- **Cuentan para 2g:** un toque sin control que cambia el flag. Van en el mismo sentido que el 85 %.

**Después de un `D`:** son solo 11. En la variante original salen toques que son el salto del balón al
reanudar; sin ellos, ninguno. No se puede leer nada.

## 2f. Opcional: eventos frente a flags (D11)

**No se ha hecho.** Pide derivar etiquetas de los eventos de la DFL con las reglas del paso 3. Esas
reglas están escritas para campos de StatsBomb (`out`, `Pass Offside`, `possession_team`), y
trasladarlas a los eventos de la DFL es un diseño que hay que fijar antes de medir. Por eso:

- no hay huella de eventos DFL ni `spellF1` de eventos contra flags;
- tampoco 3b (pases fallados de los eventos), que dependía de 2f.

Se propone como parada siguiente.

## Sensibilidad

Cada parámetro se varió de uno en uno, con el resto en su valor principal **[medido]**.

| variación | 2b control % | placebo otro / flag % | retención % | 2c p50 | 2c ret. p50 | 3a aire % | 2g toques | 2g cambia % | 2g huecos % | placebo 2g % | 1b activo % | 1b episodios | 1a banda / puerta / córner % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| radio 1,5 m | 58,6 | 3,3 / 91,1 | 87,2 | -4 | -4 | 0,2 | 279 | 85,3 | 84,2 | 14,2 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| retención 3 | 42,9 | 2,0 / 79,0 | 86,0 | -2 | -2 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| retención 8 | 42,9 | 2,0 / 79,0 | 54,6 | -2 | -2 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| retención 12 | 42,9 | 2,0 / 79,0 | 43,2 | -2 | -2 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| control 8 | 54,2 | 2,6 / 87,0 | 69,4 | -2 | -3 | 0,2 | 230 | 84,3 | 83,9 | 10,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| control 20 | 32,5 | 1,4 / 69,0 | 69,4 | -1 | -3 | 0,2 | 160 | 83,8 | 83,2 | 9,2 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| ventana 2b ±1 s | 33,5 | 1,0 / 72,2 | 59,8 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| ventana 2b ±2 s | 45,2 | 2,2 / 85,0 | 72,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| momento ±1 s | 42,9 | 2,0 / 79,0 | 69,4 | -3 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| aire 1,5 m | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 2,0 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| aire 3 m | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| aire 3 m/s | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| aire 8 m/s | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| fuera 1,0 m | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,59 | 1 | 99,4 / 100,0 / 100,0 |
| cobertura ±2 s | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 72,7 / 68,1 / 56,1 |
| cobertura ±3 s | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 96,8 / 89,9 / 80,7 |
| toque 2 m/s | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 216 | 81,5 | 80,5 | 9,4 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| toque 5 m/s | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 183 | 86,9 | 85,7 | 8,8 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| placebo ±1 s | 42,9 | 4,5 / 75,7 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| placebo ±3 s | 42,9 | 1,3 / 81,6 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| reanudar ±1 s | 42,9 | 2,0 / 79,0 | 69,4 | -2 | -3 | 0,2 | 203 | 85,2 | 83,5 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |

| variación | 2b control % | placebo otro / flag % | retención % | 2c p50 | 2c ret. p50 | 3a aire % | 2g toques | 2g cambia % | 2g huecos % | placebo 2g % | 1b activo % | 1b episodios | 1a banda / puerta / córner % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| radio 1,5 m | 57,3 | 3,3 / 91,1 | 86,5 | -4 | -4 | 0,2 | 267 | 85,0 | 83,9 | 14,3 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| retención 3 | 42,1 | 2,0 / 79,0 | 85,5 | -2 | -2 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| retención 8 | 42,1 | 2,0 / 79,0 | 53,9 | -2 | -2 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| retención 12 | 42,1 | 2,0 / 79,0 | 42,4 | -2 | -2 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| control 8 | 53,5 | 2,6 / 87,0 | 68,8 | -2 | -3 | 0,2 | 224 | 84,4 | 83,9 | 10,4 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| control 20 | 31,3 | 1,3 / 69,0 | 68,8 | -1 | -3 | 0,2 | 151 | 83,4 | 83,1 | 9,4 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| ventana 2b ±1 s | 33,0 | 1,0 / 72,2 | 59,6 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| ventana 2b ±2 s | 44,3 | 2,2 / 85,0 | 71,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| momento ±1 s | 42,1 | 2,0 / 79,0 | 68,8 | -3 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| aire 1,5 m | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 2,0 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| aire 3 m | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| aire 3 m/s | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| aire 8 m/s | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| fuera 1,0 m | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,59 | 1 | 99,4 / 100,0 / 100,0 |
| cobertura ±2 s | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 72,7 / 68,1 / 56,1 |
| cobertura ±3 s | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 96,8 / 89,9 / 80,7 |
| toque 2 m/s | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 209 | 81,3 | 80,3 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| toque 5 m/s | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 177 | 87,0 | 85,8 | 8,9 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| placebo ±1 s | 42,1 | 4,4 / 75,7 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| placebo ±3 s | 42,1 | 1,3 / 81,6 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |
| reanudar ±1 s | 42,1 | 2,0 / 79,0 | 68,8 | -2 | -3 | 0,2 | 196 | 85,2 | 83,4 | 9,5 | 0,64 | 2 | 99,4 / 100,0 / 100,0 |

## Veredictos por partido y con los 7 juntos

La variante "original" es la fijada antes de medir. "solo_en_juego" quita los frames con el balón
inactivo de los toques, controles y contactos. Se añadió al ver el balón congelado.

| partido | 1a | 1b | 2b | 2c | 3a | 2g | 2b retención | 2c retención |
|---|---|---|---|---|---|---|---|---|
| J03WMX | cumple | cumple | entre medias | al controlar | cumple | no cumple | cumple | al controlar |
| J03WN1 | cumple | cumple | entre medias | al controlar | cumple | no cumple | entre medias | al controlar |
| J03WOH | cumple | cumple | entre medias | al controlar | cumple | no cumple | cumple | al controlar |
| J03WOY | cumple | cumple | no cumple | al controlar | cumple | no cumple | entre medias | al controlar |
| J03WPY | cumple | cumple | no cumple | al controlar | cumple | no cumple | entre medias | al controlar |
| J03WQQ | cumple | cumple | entre medias | al controlar | cumple | no cumple | cumple | al controlar |
| J03WR9 | cumple | cumple | entre medias | al controlar | cumple | no cumple | cumple | al controlar |
| 1ª (J03WMX, J03WN1) | cumple | cumple | entre medias | al controlar | cumple | no cumple | entre medias | al controlar |
| Düsseldorf (5) | cumple | cumple | entre medias | al controlar | cumple | no cumple | entre medias | al controlar |
| los 7 | cumple | cumple | entre medias | al controlar | cumple | no cumple | entre medias | al controlar |

| criterio | cumple / al controlar | entre medias | no cumple / otro momento | con los 7 juntos | aguanta la sensibilidad | variaciones que lo cambian |
|---|---|---|---|---|---|---|
| 1a | 7 | 0 | 0 | cumple | no | cobertura ±2 s → no cumple; cobertura ±3 s → entre medias |
| 1b | 7 | 0 | 0 | cumple | sí | — |
| 2b | 0 | 5 | 2 | entre medias | no | control 20 → no cumple; ventana 2b ±1 s → no cumple |
| 2c | 7 | 0 | 0 | al controlar | sí | — |
| 3a | 7 | 0 | 0 | cumple | sí | — |
| 2g | 0 | 0 | 7 | no cumple | sí | — |
| 2b retención | 4 | 3 | 0 | entre medias | no | radio 1,5 m → cumple; retención 3 → cumple; ventana 2b ±2 s → cumple |
| 2c retención | 7 | 0 | 0 | al controlar | sí | — |

| partido | 1a | 1b | 2b | 2c | 3a | 2g | 2b retención | 2c retención |
|---|---|---|---|---|---|---|---|---|
| J03WMX | cumple | cumple | no cumple | al controlar | cumple | no cumple | entre medias | al controlar |
| J03WN1 | cumple | cumple | entre medias | al controlar | cumple | no cumple | entre medias | al controlar |
| J03WOH | cumple | cumple | entre medias | al controlar | cumple | no cumple | cumple | al controlar |
| J03WOY | cumple | cumple | no cumple | al controlar | cumple | no cumple | entre medias | al controlar |
| J03WPY | cumple | cumple | no cumple | al controlar | cumple | no cumple | entre medias | al controlar |
| J03WQQ | cumple | cumple | entre medias | al controlar | cumple | no cumple | cumple | al controlar |
| J03WR9 | cumple | cumple | entre medias | al controlar | cumple | no cumple | cumple | al controlar |
| 1ª (J03WMX, J03WN1) | cumple | cumple | entre medias | al controlar | cumple | no cumple | entre medias | al controlar |
| Düsseldorf (5) | cumple | cumple | entre medias | al controlar | cumple | no cumple | entre medias | al controlar |
| los 7 | cumple | cumple | entre medias | al controlar | cumple | no cumple | entre medias | al controlar |

| criterio | cumple / al controlar | entre medias | no cumple / otro momento | con los 7 juntos | aguanta la sensibilidad | variaciones que lo cambian |
|---|---|---|---|---|---|---|
| 1a | 7 | 0 | 0 | cumple | no | cobertura ±2 s → no cumple; cobertura ±3 s → entre medias |
| 1b | 7 | 0 | 0 | cumple | sí | — |
| 2b | 0 | 4 | 3 | entre medias | no | control 20 → no cumple; ventana 2b ±1 s → no cumple |
| 2c | 7 | 0 | 0 | al controlar | sí | — |
| 3a | 7 | 0 | 0 | cumple | sí | — |
| 2g | 0 | 0 | 7 | no cumple | sí | — |
| 2b retención | 3 | 4 | 0 | entre medias | no | radio 1,5 m → cumple; retención 3 → cumple; ventana 2b ±2 s → cumple |
| 2c retención | 7 | 0 | 0 | al controlar | sí | — |

| punto | criterio | veredicto (los 7) | partidos que cumplen / entre medias / no | ¿aguanta? |
|---|---|---|---|---|
| 1 | 1a cobertura de reinicios (±5 s) | cumple | 7 / 0 / 0 | sí con la ventana principal; las de ±2 y ±3 s son descriptivas |
| 1 | 1b balón fuera ⇒ `D` | cumple | 7 / 0 / 0 | sí |
| 2 | 2a medida R | entre medias (6,89 %) | 0 / 6 / 1 (J03WMX, 10,76 %) | — |
| 2 | 2b control del equipo nuevo | entre medias (42,9 %) | 0 / 5 / 2 (solo en juego: 0 / 4 / 3) | no: control de 20 frames o ventana de ±1 s → no cumple |
| 2 | 2c momento del control | "al controlar" (mediana −2 frames) | 7 al controlar | sí, pero ver la lectura |
| 2 | 2g toque del rival sin control | **no cumple** (85,2 %) | 0 / 0 / 7 | sí: 80–87 % en todas las variaciones |
| 3 | 3a cambio en el aire | cumple (0,2 %) | 7 / 0 / 0 | sí |
| 3 | 3b pases fallados (2f) | sin medir | — | — |

**Lectura:**

- **2c no apoya el punto 2.** La mediana solo cubre el 43 % de cambios que tienen control. Además, el
  control "empieza" cuando el balón llega a 1 m del jugador, que es casi su primer contacto. Un 35,5 %
  de esos cambios tiene el control entre 0,5 y 2 s **después** del cambio: el flag cambió antes, con un
  toque. Lo que dice 2c es que el flag cambia en el primer contacto. El punto 2 se decide con 2g y 2b.
- **2b, normalizado entre sus placebos,** queda en torno al 53 %, y entre el 46 % y el 63 % según la
  variación. El placebo es el control del equipo sin el flag (2,0 %) frente al del que lo tiene
  (79,0 %). Es decir, solo la mitad de los cambios llevan un control del equipo nuevo en los 2 s
  siguientes.
- **1ª frente a Düsseldorf:** se comportan igual en todo (2g 83,3 % frente a 86,4 %; 2b 42,5 % frente a
  43,1 %). La diferencia de R de la parada 2 no viene de que el flag se comporte distinto
  **[inferencia]**. Con 2 partidos frente a 5, no se separa la liga de los partidos.

## Cambios de criterio en esta parada

Los detalles están en la bitácora (sección 7).

**Antes de la primera ejecución con datos reales:**

- 2b y 2c también con la retención de 5 frames (los criterios originales), además del control;
- placebo de la retención;
- margen del placebo como parámetro, para poder hacer la fila "placebo ±1 / ±3 s" de la sensibilidad
  fijada;
- tope de 1.000 placebos por parte (2.000 por partido, como se fijó);
- distancia a la línea medida en el inicio del `D`;
- eventos `Delete` fuera de las listas;
- campo de los metadatos (105 × 68 en los 7);
- anclaje de la hora con el saque inicial de cada parte.

**Después de ver datos:**

- **Variante "solo en juego"** (toques, controles y contactos solo con frames activos): el balón está
  congelado durante los `D`.
- **Medida nueva de 2e:** la fijada da −2 en todas las paradas por ese congelado. Se mantiene en la
  tabla, como artefacto.
- **En 2g:**
  - placebo con toques del propio equipo;
  - desfase entre toque y cambio;
  - estado del flag 3 frames antes;
  - recuento por hueco;
  - duración de la racha.
- **En 1b:** episodios activos fuera de ≥ 1 s, que no dependen del congelado.
- **En 2d y 2e:**
  - flag durante el `D`;
  - porcentaje de balón quieto en los `D`;
  - salto al reanudar;
  - distancia del jugador del flag al balón al reanudar;
  - equipo del evento frente al flag;
  - movimiento de los jugadores en los `D`.

En los dos casos se dan los resultados con el criterio fijado y con el nuevo. Ningún corte de los
veredictos ha cambiado.

## Dudas resueltas

| id | estado | respuesta y evidencia |
|---|---|---|
| D2 | a medias | **`D` sí** (1a y 1b cumplen en 7/7; 2d, 2e). **El cambio de posesión no:** cambia en el primer toque del rival aunque no controle (2g no cumple en 7/7, 85 % frente a un placebo del 10 %). |
| D3 | resuelta | **En el primer toque del rival.** Desfase cambio − toque: mediana 0 frames (p10 −6, p90 +2); el 87,5 % de los cambios tiene un toque del equipo nuevo a ±2 s, frente al 2,3 % del placebo. No espera al control (2g) ni cambia en el aire (3a: 0,2 %). |
| D4 | a medias | Mientras el balón viaja, el flag se queda con el último equipo (3a cumple). En un toque sin control del rival, cambia (2g). Los pases fallados de los eventos (3b) no se han medido: falta 2f. |
| D5 | resuelta | Inactivo es todo balón fuera de juego: banda, fondo y paradas dentro del campo. El 66 % de los `D` empieza con el balón fuera de las líneas; el 99,4–100 % de los saques de banda, de puerta y córners tiene su fin de `D` a ±5 s; con el balón fuera ≥ 1 s solo hay 2 episodios activos en 7 partidos. |
| D6 | resuelta | **A inactivo:** 3–4 frames después de que el balón cruce la línea (p90 de 8–10). **A activo:** en el golpeo o pocos frames después: en el primer frame activo, el jugador del equipo del flag está a 0,75 m del balón (mediana) y el 87 % a ≤ 2 m. No se puede afinar más porque el balón está congelado durante el `D`. El flag durante la parada ya es el del equipo del evento de reinicio (97,8 %). |
| D7 | a medias | **En la DFL**, ningún retraso sistemático: el cambio cae en el frame del toque y el `D` acaba en el golpeo o a pocos frames. No encaja con un marcado en directo con retraso humano de 0,3–1 s **[inferencia]**. **En la GT del reto** no se puede medir. |
| D8 | resuelta | No faltan frames: `N` y `T` de 1 en 1 en las dos partes de los 7, y 1.002.644 frames como el artículo. |
| D9 | resuelta | kloppy 3.18 lee bien la DFL: local en `teams[0]`, `ball_state` `alive`/`dead`, y 0 diferencias con el lector propio en J03WMX. Las coordenadas por defecto no son metros: hace falta `coordinates="sportec"`. Carga completa: 4,5 GB de pico, así que un partido cada vez. |
| D10 | resuelta (una descarga) | 21 ficheros, 2,63 GB, en 4 min, con el md5 correcto en todos. No se ha probado otro día ni el espejo. |

## Conclusión y decisión (propuesta; decide Ismael, nada escrito en `docs/decisiones.md`)

**¿La Bundesliga vale como proxy principal?**

- **Para `D`, sí, tal cual.** El punto 1 cumple en los 7 y aguanta la sensibilidad. Las fronteras son
  nítidas: empieza 3–4 frames tras salir el balón y acaba en el golpeo.
  - **Cuidado:** en la DFL, la posición del balón está congelada durante el `D` y salta al reanudar
    (mediana 6,2 m). Si se entrena o se valida un detector de `D` con la DFL sin tapar el balón en esos
    frames, el balón le da la respuesta. Los jugadores no se congelan: la fuga es solo del balón.
  - Al degradar la DFL para que se parezca al ATD, hay que enmascarar o reemplazar el balón en los `D`.
    Si el ATD hace lo mismo con el balón muerto, **[sin verificar]**; lo diría el perfil del ATD
    (paso 5, solo una persona).
- **Para el cambio de posesión, no tal cual.** El punto 2 no cumple (2g en 7/7, robusto). El 2b queda
  entre medias y el 2c dice que el flag cambia en el primer contacto. Hay dos lecturas, y con estos datos
  no se puede elegir entre ellas:
  - **Lectura a: la DFL marca otra cosa que el reto.** La DFL seguiría al último toque y el reto pide
    control. Habría que corregir al derivar las etiquetas:
    - Con el tracking completo de la DFL se pueden quitar las rachas del rival entre dos controles del
      mismo equipo sin control del rival.
    - Esa corrección depende de cómo definamos "control" (12 frames a 1 m del mismo jugador), que es una
      elección nuestra y cambia las etiquetas.
    - **Quitar solo las posesiones intercaladas de menos de 1 s no basta:** solo el 17,9 % de las
      rachas creadas por un toque sin control dura menos de 1 s (mediana 2 s).
  - **Lectura b: los flags de proveedor se comportan así, y la GT del reto podría también.** La GT del
    reto sale mecánicamente del flag de un tracking corregido, y si texto y GT no coinciden manda la
    GT. Con esta lectura, la DFL tal cual se parecería más a la GT que el texto.
  - **Qué las distinguiría:**
    - saber si el flag de posesión del tracking corregido del reto cambia con un toque sin control (lo
      sabe la organización);
    - saber qué proveedor y qué regla generan ese flag.
  - **Qué no podemos saber:**
    - la GT completa;
    - la ventana pública no se usa para decidir;
    - la huella de retrasos no decide (D21).
- **Propuesta:** no elegir todavía y no presentar ninguna corrección como la opción por defecto.
  1. Generar las dos versiones de etiquetas DFL: el flag tal cual y el flag corregido con el control
     del tracking.
  2. Medir con las dos cuánto cambia el método.
  3. Decidir con la respuesta a la pregunta anterior, si Ismael decide hacerla.

**¿Cuándo debe cambiar nuestra etiqueta de equipo y cuándo empieza y acaba un `D`?**

- **`D`:** empieza a los pocos frames de que el balón cruce la línea o de que el árbitro pare el juego,
  y acaba en el golpeo del reinicio o pocos frames después. Al volver de un `D`, la etiqueta es la del
  equipo que reanuda.
- **Equipo, según la lectura b:** en el primer toque del rival.
- **Equipo, según la lectura a:** cuando el rival controla. El tracking de la DFL da el momento del
  inicio del control: mediana de 2 frames antes del cambio del flag cuando hay control.

**¿Qué cambia en el plan?**

1. **Detector de `D`:** las etiquetas `D` de la DFL son buenas para entrenarlo y validarlo, siempre que
   se tape el balón en los frames `D`.
2. **Modelo de posesión:** hay que tener las dos versiones de etiquetas antes de elegir umbrales con la
   DFL.
3. **Pendiente:** 2f (eventos DFL con reglas fijadas antes) y el paso 3, que dependen de D15 y D16.

## Sin verificar

- Si el ATD también congela el balón durante el balón muerto (paso 5).
- Qué son los 21 fines de `D` sin reinicio en los eventos.
- Si la diferencia de R entre 1ª y 2. Bundesliga es por la liga, por esos partidos o por los operadores:
  el flag se comporta igual en los dos grupos.
- 3b y 2f.
- La estabilidad de la descarga en otro momento.
