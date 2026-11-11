# Bitácora del experimento 0

Registro de cada paso, comando y comprobación del experimento 0 (pasos 1 y 2 de `validation/PASOS.md`).
Solo agregados. Etiquetas de evidencia: **[medido]**, **[inferencia]**, **[sin verificar]**.

## Encargo

- **Qué:** ejecutar los pasos 1 y 2 de `validation/PASOS.md` en la rama `exp/experimento-0`, con tres
  paradas para que la sesión orquestadora revise cada una.
- **Quién lo pide:** Ismael, a través de la sesión orquestadora ("More than a Hack hackathon setup"),
  el 11/11/2026. La descarga de 2,63 GB se lanzó con ese encargo.
- **Alcance:** paso 1 (descarga) y paso 2 (2a–2e obligatorios; 2f si lo anterior está sólido). Los pasos
  3 y 4 no (dependen del registro en StatsBomb y de D15 y D16). El paso 5 nunca lo ejecuta Claude.
- **Paradas:**
  1. descarga completa y lector validado con un partido (J03WMX), con su 2a;
  2. 2a y 2b de los 7 partidos;
  3. 2c, 2d y 2e (y 2f), con el fichero de resultados relleno.

## Entorno

| qué | valor |
|---|---|
| Python | 3.13.9, en el entorno virtual del proyecto |
| kloppy | 3.18.0 |
| numpy / pandas / lxml / psutil | 2.5.4 / 3.1.1 / 6.1.3 / 7.2.2 |
| sistema | Windows 11 |
| RAM | 16,9 GB, 4,4 GB libres al empezar |
| disco | 45 GB libres en C: al empezar |
| datos abiertos | `~/mtah2027-datos-abiertos/dfl` (fuera del repo y de `MTAH_DATA_DIR`) |

## Paso 1. Descarga

- **Comando:** `python validation/scripts/descargar_datos_abiertos.py dfl`, en segundo plano.
- **Inicio:** 2026-11-11 22:49:38.
- **Fuente:** figshare 10.6084/m9.figshare.28196177.v1 (host `ndownloader.figshare.com`), 21 ficheros,
  2.627.505.889 bytes, cada uno con su md5. CC BY 4.0 (Bassek, Rein, Weber y Memmert, 2025).
- **Resultado [medido]:** terminó a las 22:53:42 (4 min 4 s). Los 21 ficheros, con el md5 correcto;
  ninguno a medias (`.part`); 2,5 GB en disco.
- **Antes de fijar los criterios** solo se miraron los metadatos y la cabecera del primer XML de
  posiciones (nombres de los atributos: `N`, `T`, `X`, `Y`, `D`, `S`, `A`, `M`; el balón añade `Z`,
  `BallPossession` y `BallStatus`). Ningún recuento ni ningún valor de flag.

## Antes de leer las posiciones

### Metadatos (`DFL_02_01_matchinformation_*`) [medido]

- **Estructura:** `General` (equipos local y visitante, `HomeTeamId`, `GuestTeamId`), `Environment`
  (`PitchX` = 105,00 y `PitchY` = 68,00 en los 7) y `OtherGameInformation` con `TotalTimeFirstHalf`,
  `TotalTimeSecondHalf`, `PlayingTimeFirstHalf` y `PlayingTimeSecondHalf`, en milisegundos.
- **El orden de `<Teams>` cambia de un partido a otro:** el visitante va primero en J03WMX, J03WN1,
  J03WPY y J03WR9, y el local primero en J03WOH, J03WOY y J03WQQ. Un lector que use el orden del
  documento confundiría local y visitante en algunos partidos. Cada `Team` lleva `Role` (`home` o
  `guest`): el local se toma de ahí y de `HomeTeamId`, nunca del orden.
- **Anclas por partido**, calculadas solo con los metadatos con `anclas_metadatos.py` (el tiempo neto
  es `PlayingTime`). Una primera versión de esta tabla, hecha a mano, tenía dos porcentajes mal
  redondeados (J03WPY y J03WR9); se sustituyó por la salida del script antes del primer commit.

| partido | local–visitante | competición | campo | orden de <Teams> | local por Role = HomeTeamId | TotalTime/40 (1ª + 2ª) | artículo | diferencia | neto 1ª | neto 2ª | neto total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J03WMX | 1. FC Köln–FC Bayern München | Bundesliga | 105.00 × 68.00 | guest, home | sí | 70707 + 75258 = 145965 | 145967 | +2 | 66.8% | 50.7% | 58.5% |
| J03WN1 | VfL Bochum 1848–Bayer 04 Leverkusen | Bundesliga | 105.00 × 68.00 | guest, home | sí | 69287 + 72272 = 141559 | 141561 | +2 | 55.9% | 41.0% | 48.3% |
| J03WOH | Fortuna Düsseldorf–SSV Jahn Regensburg | 2. Bundesliga | 105.00 × 68.00 | home, guest | sí | 69423 + 67789 = 137212 | 137214 | +2 | 54.5% | 50.3% | 52.4% |
| J03WOY | Fortuna Düsseldorf–F.C. Hansa Rostock | 2. Bundesliga | 105.00 × 68.00 | home, guest | sí | 69110 + 73424 = 142534 | 142536 | +2 | 54.6% | 52.5% | 53.5% |
| J03WPY | Fortuna Düsseldorf–1. FC Nürnberg | 2. Bundesliga | 105.00 × 68.00 | guest, home | sí | 69130 + 77079 = 146209 | 146211 | +2 | 66.8% | 45.8% | 55.7% |
| J03WQQ | Fortuna Düsseldorf–FC St. Pauli | 2. Bundesliga | 105.00 × 68.00 | home, guest | sí | 69203 + 73140 = 142343 | 142345 | +2 | 68.0% | 51.0% | 59.3% |
| J03WR9 | Fortuna Düsseldorf–1. FC Kaiserslautern | 2. Bundesliga | 105.00 × 68.00 | guest, home | sí | 68353 + 78455 = 146808 | 146810 | +2 | 64.8% | 52.3% | 58.1% |

  En los 7, `TotalTime` / 40 queda exactamente 2 frames por debajo de la tabla del artículo (uno por
  parte) **[medido]**. En los 7, el local por `Role` coincide con `HomeTeamId` **[medido]**. Lo más probable es que cada parte tenga un frame más que su duración en
  milisegundos / 40 (frames del 0 al final, ambos incluidos) **[inferencia]**.

### Por qué un lector propio

kloppy 3.18 lee el XML por streaming, pero guarda todos los frames de todos los objetos en diccionarios
de Python (unos 3,4 millones de diccionarios por partido). Con 4,4 GB de RAM libre no hay margen. El
lector principal es propio (lxml en streaming, arrays de numpy guardados fuera del repo). kloppy se usa
en comprobaciones acotadas:

1. su propia función interna `_unstack_framesets` solo con el balón, para comparar los flags con el
   lector propio;
2. `load_tracking(limit=...)` para ver el orden de los equipos, los valores de `ball_state`, las
   coordenadas y qué pone cuando falta el poseedor;
3. una carga completa, una sola vez y sola, midiendo la memoria pico. Si no cabe, es un hallazgo de D9,
   porque `PASOS.md` 2a usa `to_df()`.

### Criterios fijados antes de medir (lector y 2a)

Se escriben y se commitean antes de leer ningún fichero de posiciones. No se cambian después; si
hubiera que cambiar alguno, se dirá aquí y por qué.

| id | qué se comprueba | cumple | no cumple |
|---|---|---|---|
| C1 | frames de balón por parte frente a `TotalTime` / 40 | diferencia de 2 frames o menos | más de 25 frames (es la respuesta a D8) |
| C2 | frames de balón del partido frente a la tabla del artículo | diferencia de 2 frames o menos | otra cosa (D8) |
| C3 | pasos de `N` dentro de cada parte en el balón, y de `T` (40 ms) | todos de 1 frame y 40 ms | cualquier salto: se cuentan y se describen (D8) |
| C4 | frames de jugadores cuyo `N` no está en el balón | 0 | se cuentan (D8) |
| C5 | valores de los flags | `BallStatus` ∈ {0, 1} y `BallPossession` ∈ {1, 2} en todos los frames del balón | se cuentan los ausentes y los raros |
| C6 | fracción de balón activo por parte frente a `PlayingTime` / `TotalTime` | 1 punto o menos de diferencia: coinciden. Hasta 3 puntos: parecidos (el dato oficial puede venir de otra fuente, por ejemplo los operadores de eventos) | más de 3 puntos: no cuadra, se investiga (D5) |
| C7 | tramos de balón inactivo frente a reinicios contados en el XML de eventos | cociente entre 0,85 y 1,30: el `D` cubre los reinicios | menos de 0,70: al `D` le faltan reinicios (D5). Entre 0,70 y 0,85 o más de 1,30: se investiga |
| C8 | unidades de `S`: mediana de `S` / (desplazamiento por frame × 25) en el balón en movimiento | ≈ 3,6 (± 0,3): km/h. ≈ 1 (± 0,1): m/s | otra cosa: se investiga |
| C9 | origen de coordenadas: balón en el primer frame activo de cada parte | a 2 m o menos de (0, 0): origen en el centro | más lejos: se investiga |
| C10 | escala de coordenadas | máximos de \|x\| y \|y\| del balón activo cerca de 52,5 y 34 (± 3 m) | otra cosa: se investiga |
| C11 | sentido de `BallPossession` (1 = local), en cada uno de los 7 partidos | en frames estables (balón activo a menos de 2 m/s, un solo jugador a 1 m o menos y ningún otro a menos de 2 m), el equipo del jugador coincide con el del flag en el 80 % o más | 20 % o menos: el sentido está invertido. Entre medias: ambiguo, y no se sigue a 2c |
| C12 | lector propio frente a kloppy | recuentos de los dos flags por parte idénticos | cualquier diferencia se explica antes de seguir |

## Registro

(Se añade cada ejecución: comando, tiempo, memoria y resultado.)
