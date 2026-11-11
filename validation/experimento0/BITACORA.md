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

### 1. Lector propio, probado con datos sintéticos

- **Script:** `dfl_lector.py` (lxml en streaming). Guarda una caché `.npz` por partido en
  `~/mtah2027-datos-abiertos/dfl_cache/`, fuera del repo.
- **Prueba sintética** (`pruebas_sinteticas.py`): un XML inventado con el formato de la DFL, con un
  frame del balón perdido, un flag ausente, un salto de 80 ms en `T`, un jugador con un frame fuera de
  la rejilla del balón, un árbitro y dos partes. El lector detecta exactamente cada cosa **[medido]**.
  La misma prueba cubre después las etiquetas y su perfil: con flags inventados de 5 posesiones y 2
  paradas conocidas, salen 5 y 2 **[medido]**.

### 2. J03WMX (Köln–Bayern) con el lector propio

`python validation/experimento0/dfl_lector.py J03WMX`: 17 s, memoria pico 765 MB, caché de 16 MB.

| criterio | resultado | veredicto |
|---|---|---|
| C1 frames de balón por parte | 70.708 y 75.259, un frame más por parte que `TotalTime` / 40 (70.707 y 75.258) | cumple |
| C2 total frente al artículo | 145.967 = 145.967 | cumple |
| C3 pasos de `N` y de `T` | todos de 1 frame y de 40 ms; `N` ordenado; sin repetidos | cumple |
| C4 frames de jugador fuera de la rejilla del balón | 0 | cumple |
| C5 valores de los flags | `BallStatus` ∈ {0, 1} y `BallPossession` ∈ {1, 2} en todos los frames; ninguno ausente | cumple |

Además **[medido]**: siempre hay exactamente 22 jugadores por frame (11 + 11; con los cambios, 16
jugadores distintos por equipo en la 2ª parte). Hay 3 árbitros por parte, que el lector aparta. Las dos
partes empiezan con el balón activo (el tracking arranca en el saque inicial) y acaban inactivas.

`python validation/experimento0/comprobaciones_lector.py J03WMX`:

| criterio | resultado | veredicto |
|---|---|---|
| C6 fracción activa frente al tiempo neto oficial | 66,789 % frente a 66,788 % y 50,684 % frente a 50,683 %; los frames activos son `PlayingTime` / 40 + 1 en las dos partes | cumple, pero **no es independiente**: el tiempo neto oficial sale del mismo flag **[inferencia]**. Valida el lector, no lo que cuenta como inactivo |
| C7 tramos inactivos frente a reinicios de los eventos | 103 tramos (41 + 62) frente a 104 reinicios en el XML de eventos: 52 saques de banda, 20 faltas, 14 saques de puerta, 10 córners, 5 saques iniciales, 1 penalti y 2 balones a tierra. Cociente 0,99. Ningún tramo inactivo de menos de 1 s | cumple el criterio fijado. Matiz: las dos partes empiezan activas y acaban inactivas. Quitando los 2 tramos finales (no acaban en un reinicio) y los 2 saques iniciales que abren cada parte, son 101 tramos para 102 reinicios (0,99), o 101 para 100 sin los balones a tierra (1,01). `RefereeBall` se añadió a la lista después de ver los tipos de evento. Que los totales cuadren **no prueba** que cada reinicio tenga su tramo: eso es 2d |
| C8 unidades de `S` | `S` / velocidad de las posiciones: p10 2,5–2,8, mediana 3,72–3,74, p90 4,4–4,6 | cumple: km/h. La dispersión puede deberse a que `S` esté suavizada o a que sea la velocidad en 3D (con `Z`) **[inferencia]**; no bloquea, porque 2c calcula la velocidad con las posiciones |
| C9 origen | primer frame activo a 0,25 m y 0,47 m de (0, 0) | cumple: origen en el centro |
| C10 escala | p99,9 de \|x\| = 52,2–52,9 y de \|y\| = 34,6–34,8; máximos 55,1 y 36,8 (balón fuera del campo) | cumple: metros |
| C11 sentido de `BallPossession` | 7.814 frames estables; el jugador cercano es del equipo del flag en el 98,9 % (flag 1: 97,4 % y 99,3 %; flag 2: 99,6 % y 98,6 %) | cumple: 1 = local en este partido. Falta comprobarlo en los otros 6 |

Informativo **[medido]**: con el balón inactivo, el flag sigue al equipo del jugador cercano en el 85 %
de los frames estables. El flag de posesión no se apaga en las paradas.

Los 108 eventos `Delete` del XML de eventos no llevan el id de ningún evento, y su propio `EventId` no
coincide con el de ningún otro evento del fichero: no anulan ningún reinicio **[medido]** (lo comprueba
`comprobaciones_lector.py`).

### 3. kloppy frente al lector propio (C12 y D9)

- **Balón** (`comprobar_kloppy.py J03WMX balon`): la función interna `_unstack_framesets` de kloppy,
  leyendo solo el balón, da los mismos frames y los mismos dos flags que el lector propio, frame a frame,
  con 0 diferencias en las dos partes **[medido]**. **C12 cumple.**
- **Mapeo** (`comprobar_kloppy.py J03WMX mapeo --limite 3000`) **[medido]**:
  - `teams[0]` es el local (`HomeTeamId`) aunque en el XML vaya primero el visitante;
  - `ball_state` solo toma `alive` y `dead`, y en 3.000 frames no discrepa del XML ni en `ball_state` ni
    en el poseedor;
  - con `coordinates="sportec"`, las 66.000 posiciones de jugador (3.000 frames × 22) y las del balón
    coinciden con la caché con diferencia 0,0 m; el equipo de cada jugador y el número de jugadores por
    frame coinciden en todos. **El lector propio queda validado también para los jugadores**;
  - 25 fps;
  - cuando falta `BallPossession`, kloppy pone el visitante (lo dice su código). En la DFL no falta
    nunca (C5), así que aquí no afecta.
- **Contradicción con el plan: las coordenadas por defecto de kloppy no son metros.** `PASOS.md` 2a dice
  que las de por defecto son "metros, origen en el centro". En kloppy 3.18 el sistema por defecto es el
  de kloppy: x = X/105 + 0,5 e y = −Y/68 + 0,5 (de 0 a 1, origen arriba a la izquierda y eje `y`
  invertido; residuo de 1e-15). Con `coordinates="sportec"` devuelve exactamente los metros del XML
  **[medido]** (el ajuste está en `comprobar_kloppy.py J03WMX mapeo`). El lector propio no se ve
  afectado (trabaja en metros: C9 y C10), pero el fragmento de `PASOS.md` lo tiene mal.
  **Corrección propuesta** para 2a de `PASOS.md`: `coordinates="sportec"` para tener metros con origen
  en el centro. No se ha aplicado: lo decide la sesión orquestadora. Lo hecho después de verlo no usa
  coordenadas de kloppy.
- **Carga completa** (`comprobar_kloppy.py J03WMX completo`: `only_alive=False` y `to_df()`, como en
  `PASOS.md` 2a) **[medido]**: funciona. 145.967 frames y 137 columnas; `alive` 85.369 y `dead`
  60.598, igual que el lector propio. Tarda 104 s (98 s de `load_tracking`), con un pico de memoria de
  4,5 GB; al sistema le llegaron a quedar 1,53 GB libres. La RAM libre al lanzarla no se apuntó (4,4 GB
  al empezar la sesión), y a la vez corrieron las etiquetas, el perfil y las pruebas sintéticas.
  Lectura: con unos 6 GB libres cabe, pero justo; un partido cada vez (D9).
- **Fallo del vigilante de memoria, corregido:** en Windows, el python del entorno virtual es un
  lanzador que arranca el intérprete real como proceso hijo. El vigilante medía el lanzador (4 MB) y no
  el intérprete; el corte por memoria libre del sistema sí funcionaba, pero habría matado solo al
  lanzador. Ahora vigila y corta el árbol de procesos entero. En esta ejecución no hizo falta cortar.

### 4. 2a de J03WMX

`python validation/experimento0/etiquetas_dfl.py J03WMX` (CSV fuera del repo) y
`python validation/scripts/perfil_etiquetas.py ~/mtah2027-datos-abiertos/dfl_etiquetas/J03WMX.csv`
**[medido]**:

| medida | valor |
|---|---|
| reparto de frames | H 26,8 %, A 31,7 %, D 41,5 % |
| paradas | 103; duración p10 5,0 s, mediana 15,5 s, p90 48,9 s |
| posesiones | 511 (8,98 por minuto de balón vivo); duración p10 0,7 s, p25 1,4 s, mediana 3,0 s, p75 7,9 s, p90 15,3 s |
| posesiones cortas | 6 % de menos de 0,5 s, 17 % de menos de 1 s, 37 % de menos de 2 s, 50 % de menos de 3 s |
| cambios directos de equipo con el balón vivo | 408 (H→A 209, A→H 199) |
| rachas de 2 frames o menos | 3 en todo el partido: no hay parpadeo de frame a frame |
| huella de retrasos (**solo informativa, D21**) | 0,9898 / 0,9503 / 0,8184 / 0,4943 con 1 / 3 / 8 / 25 frames; la tabla oficial dice 1,0000 / 0,9818 / 0,8933 / 0,6539 |

**Lectura (sin decidir nada todavía):**
- El 41,5 % de `D` y las 103 paradas encajan con un balón inactivo que incluye todos los reinicios
  (D5, a confirmar caso a caso en 2d).
- El flag de posesión cambia mucho: 408 cambios directos y un 17 % de posesiones de menos de 1 s, sin
  parpadeo de frame a frame. Puede ser que cambie con cada toque del rival y no solo con un control, que
  es justo lo que el reto dice que no debe pasar. **No está medido:** es la pregunta de 2c (D3, D4).
  Otras explicaciones posibles, que 2c tiene que distinguir: pases cortos de verdad del rival
  (posesiones reales y cortas), duelos con balón dividido, o un flag por jugador más cercano.
- La huella de retrasos no entra en este argumento ni dice nada sobre la GT del reto: es solo
  informativa (D1, D21).

### Criterios de 2c, 2d y 2e

**Cuándo se escribieron:** el 11/11, después de ver el 2a de J03WMX (511 posesiones, 86 de menos de
1 s, 408 cambios directos) y **antes de medir nada en los instantes de cambio**. Están pendientes de
revisión de la sesión orquestadora. Si cambian después de ver datos, se dirá aquí y por qué.

**Definiciones comunes** (todo con las posiciones del lector propio, en metros):

- **cambio H↔A:** frame en el que el flag pasa de un equipo al otro con el balón activo en ese frame y
  en el anterior;
- **velocidad del balón:** diferencia centrada de ±2 frames, para no amplificar el ruido de posición;
- **jugador en contacto:** a 1,0 m del balón o menos;
- **retención por un equipo:** al menos 5 frames seguidos (0,2 s) en los que el jugador más cercano al
  balón es de ese equipo y está en contacto;
- **placebo:** la misma medida en frames activos elegidos al azar, con semilla fija, dentro de
  posesiones del equipo correspondiente y a más de 2 s de cualquier cambio;
- **eventos:** su hora (`EventTime`) se pasa a frame con la `T` del tracking. Como su error es de
  −0,37 ± 1,82 s según los autores, solo se usan con ventanas de varios segundos.

**Punto 1. `D` cubre todo balón fuera de juego (2a, 2d).**

- **1a. Cobertura de reinicios.** Para cada reinicio del XML de eventos (saque de banda, de puerta,
  córner, falta, penalti y saque inicial que no abre una parte), ¿termina un tramo `D` a 3 s o menos del
  evento?
  - Cumple: 90 % o más en saques de banda, de puerta y córners, con los 7 partidos juntos.
  - No cumple: menos del 70 % en alguno de esos tres.
- **1b. Balón fuera ⇒ `D`.** En los tramos en que el balón está más de 0,5 m fuera de las líneas
  durante 1 s seguido o más:
  - cumple si el flag dice activo en el 5 % de esos frames o menos;
  - no cumple si es más del 15 %.

**Punto 2. La posesión cambia con un control del rival, no con un toque (2c).**

- **2a. Solo con las etiquetas.** De las posesiones de menos de 1 s con el balón activo antes y
  después, cuántas están intercaladas (el mismo rival antes y después: X–y–X) y cuántas tocan un `D`.
  Se resume en R = posesiones intercaladas de menos de 1 s / total de posesiones.
  - Lectura fijada antes de calcularla: R del 10 % o más indica que el flag cambia a menudo con toques
    breves (no cumple); R del 3 % o menos es compatible con un cambio por control (cumple); entre medias
    lo deciden 2b y 2c.
  - Los cortes son a juicio, sin referencia externa.
  - Se mide en los 7 partidos en la parada 2, porque solo usa etiquetas.
- **2b. Retención.** Qué porcentaje de cambios H↔A tiene una retención del equipo nuevo en ±1 s.
  - Cumple si es el 70 % o más; no cumple si es el 40 % o menos.
  - Se da junto al placebo.
- **2c. Momento.** Frames desde el cambio hasta el inicio de la primera retención del equipo nuevo,
  buscada en ±2 s.
  - Mediana entre −12 y +12 frames (±0,5 s): el flag cambia cuando el rival controla.
  - Mediana de más de +12: cambia antes de que controle (con el primer toque o anticipándose).
  - Mediana de menos de −12: cambia después, con retraso (D7).

**Punto 3. La posesión se queda con el último equipo mientras el balón está suelto o en un pase
fallado (2c, 2f).**

- **3a. Cambios en el aire.** Porcentaje de cambios H↔A sin ningún jugador a 2 m del balón o menos y
  con el balón a más de 5 m/s.
  - Cumple si es el 10 % o menos; no cumple si es el 30 % o más.
- **3b (2f, si se hace).** En los pases fallados del XML de eventos (`Evaluation = unsuccessful`), el
  flag no pasa al rival antes de su primer contacto.

**Descriptivos, sin veredicto (D6):**

- **2d:** dónde está el balón al pasar a inactivo (dentro o fuera, distancia a la línea); desfase desde
  que cruza una línea, si la cruzó en los 3 s anteriores; duración de la parada por tipo aproximado.
- **2e:** desfase entre el paso a activo y el primer frame con el balón a más de 2 m/s (en ±3 s); si el
  equipo del flag durante la parada es el que reanuda (el del flag en el primer frame activo).
- **2c, lo que pide `PASOS.md`:**
  - distancias del balón a los jugadores en el frame del cambio;
  - desfase hasta el toque más cercano del equipo nuevo, con su placebo. Un toque es un cambio de
    velocidad del balón de 3 m/s o más entre los 4 frames anteriores y los 4 siguientes, con un jugador
    de ese equipo a 1,5 m o menos;
  - fracción de cambios con un jugador del equipo nuevo a 1,5 m o menos en ±1 s, con su placebo.

  El detector de toques se prueba antes con una trayectoria sintética de toques conocidos y ruido de
  1–2 cm. Después se contrasta con los eventos (pases por minuto), nunca con el flag.

**Sensibilidad** (todos los criterios). Una conclusión aguanta si el veredicto no cambia en ninguna de
estas variaciones:

| parámetro | valores |
|---|---|
| radio de contacto | 1,0 / 1,5 m |
| retención | 3 / 5 / 8 frames |
| ventanas de 2b y 2c | ±1 / ±2 s |
| cambio en el aire | 1,5 / 2 / 3 m y 3 / 5 / 8 m/s |
| margen de fuera del campo | 0,5 / 1,0 m |
| ventana de cobertura de reinicios | ±2 / ±3 / ±5 s |
| umbral de toque | 2 / 3 / 5 m/s |
| ventana del placebo y del paso a activo | ±1 / ±3 s |

**Distribuciones:** p10, p50 y p90 por partido y con los 7 juntos, con un histograma para ver si hay dos
modas. Los dos partidos de 1ª Bundesliga se comparan con los cinco del Düsseldorf.

**Propuesta de decisión del paso 2** (la decide Ismael): la Bundesliga vale como proxy principal si
cumplen los puntos 1, 2 y 3. Si alguno no cumple, se apunta en qué difiere y si se puede corregir al
derivar las etiquetas, por ejemplo quitando las posesiones intercaladas de menos de 1 s.

### Cambios en los criterios de 2c, 2d y 2e (antes de medir)

**Cuándo y por qué:** el 11/11, a petición de la sesión orquestadora tras revisar la parada 1, y antes
de medir ningún instante de cambio, ningún tramo `D` frente a un reinicio concreto y ningún toque. Lo
que sigue sustituye a la sección anterior en lo que choque con ella.

**1a. Cobertura de reinicios.**

- **Por qué cambia:** con el error de hora de los eventos (−0,37 ± 1,82 s), solo por ese error
  quedaría fuera de ±3 s alrededor del 11 % de los reinicios y fuera de ±2 s alrededor del 28 %. El
  90 % podría fallar con una cobertura perfecta.
- **Ventana principal: ±5 s.** Las de ±2 y ±3 s son solo descriptivas.
- **Emparejamiento uno a uno y en orden:** cada fin de `D` sirve para un solo reinicio. Los reinicios
  se recorren en orden de tiempo y cada uno se queda con el fin de `D` libre más cercano dentro de la
  ventana.
- **Se da también:** la distribución del desfase (hora del reinicio menos fin del tramo `D`
  emparejado) por tipo de reinicio, y la tasa de emparejamiento por azar con un placebo (los mismos
  instantes desplazados al azar dentro de la parte, con semilla fija).
- **Sentido contrario:** qué fracción de tramos `D` acaba emparejada con un reinicio, y qué son los que
  no (por ejemplo, el final de cada parte).
- Los cortes no cambian: cumple con el 90 % o más en saques de banda, de puerta y córners; no cumple
  con menos del 70 % en alguno.

**2b. Retención y control.**

- **Por qué cambia:** un balón a 10 m/s tarda 0,2 s en cruzar un círculo de 1 m de radio, así que un
  desvío o un balón que pasa de largo cuenta como una retención de 5 frames.
- **Definición de control, fijada ahora:** al menos 12 frames seguidos (0,5 s) en los que el mismo
  jugador del equipo (el mismo `PersonId`) es el más cercano al balón y está a 1,0 m o menos. La
  retención de 5 frames se sigue dando, como medida más blanda.
- **Cada cambio H↔A se clasifica en tres grupos**, mirando del frame f − 25 al f + 50 (1 s antes y 2 s
  después):
  1. seguido de control del equipo nuevo;
  2. solo un toque: algún jugador del equipo nuevo a 1,0 m o menos en algún frame, pero sin control;
  3. nada: ningún jugador del equipo nuevo a 1,0 m o menos en la ventana.
- **Veredicto de 2b, con el control:** cumple si el 70 % o más de los cambios tiene control del equipo
  nuevo en la ventana; no cumple si es el 40 % o menos.
- **Placebo, concreto:** frames activos al azar, con semilla fija, a más de 2 s de cualquier cambio, con
  la misma ventana. Dos referencias:
  - el control del equipo que **no** tiene el flag: tasa de falsos positivos;
  - el control del equipo que **sí** lo tiene: techo.

  El 70 % se lee entre esas dos.
- **Sensibilidad:** retención de 3, 5, 8 y 12 frames; control de 8, 12 y 20 frames.

**2c. Momento.** Además del veredicto por la mediana: la distribución en frames (p10, p50 y p90) del
desfase entre el cambio y el inicio del control del equipo nuevo, y qué fracción de cambios cae a ±3,
±8 y ±25 frames del inicio del control. Es lo que tendrá que imitar nuestro método.

**Nuevo: 2g. El sentido que pide el reto.** `CHALLENGE.md` dice que un toque sin control, un desvío o
un duelo aéreo ganado sin control posterior no cambian la posesión. Se mide al revés, sin mirar el
flag para elegir los casos:

- **Toque**, solo con el tracking: un cambio de velocidad del balón de 3 m/s o más entre la media de los
  4 frames siguientes y la de los 4 anteriores, en un máximo local (±4 frames), atribuido al equipo del
  jugador más cercano si está a 1,5 m o menos. El detector se prueba antes con una trayectoria sintética
  con toques en instantes conocidos y ruido de 1–2 cm.
- **Toque del rival sin control:** un toque del equipo Y cuyo control anterior (en los 5 s previos) es
  del equipo X, cuyo control siguiente (en los 5 s posteriores) también es de X, y sin ningún control de
  Y entre medias.
- **Medida:** en qué fracción de esos toques el flag marca a Y en algún frame entre el toque y el
  siguiente control de X.
  - Cumple si es el 10 % o menos; no cumple si es el 30 % o más; entre medias, inconcluso.
  - Se da aparte para los toques con el balón alto (`Z` de más de 1,5 m), que son los duelos aéreos.

**Lectura final (para la parada 3).** `CHALLENGE.md` dice que la GT sale mecánicamente del flag de un
tracking corregido, que su texto no es una especificación técnica y que, si la definición y la GT no
coinciden, manda la GT. Así que, si el punto 2 no cumple, hay dos lecturas:

- la DFL marca distinto de lo que pide el reto, y habría que corregir al derivar las etiquetas;
- los flags de proveedor se comportan así, y la GT del reto podría parecerse más a la DFL que al texto.

No se presentará ninguna corrección (por ejemplo, quitar las posesiones intercaladas de menos de 1 s)
como la opción por defecto. Se expondrán las dos lecturas, qué las distinguiría y qué no podemos saber.
La ventana pública sigue sin usarse para decidir.

### 5. Parada 2: 2a y 2b de los 7 partidos

**Qué se ejecutó:**

- `dfl_lector.py` en los 7 partidos, uno cada vez: entre 13 y 14 s por partido. El resumen de cada uno
  se guarda junto a su caché, fuera del repo.
- `etiquetas_dfl.py` en los 7 (CSV fuera del repo).
- `parada2_resumen.py`, que reúne C1–C7 y C11 (con `comprobaciones_lector.py`), el perfil de 2a, la
  medida R y la huella de 2b. Tarda 9 s.

La medida R tiene su prueba sintética en `pruebas_sinteticas.py`: con una secuencia inventada de 6
posesiones, 1 intercalada, 1 junto a `D` y 2 en el borde, el recuento sale exacto **[medido]**.

**Salida de `parada2_resumen.py`** **[medido]** (decimales con punto, tal como la imprime el script):

```text
Total de frames: 1002644 (artículo: 1002644, diferencia +0)

| partido | C1 frames − TotalTime/40 | C2 − artículo | C3 saltos N / T / repetidos | C4 | C5 BallStatus / BallPossession | jugadores por frame | C6 diferencia (puntos) | C7 tramos / reinicios | C7 ajustado (sin balones a tierra) | C11 frames, coincide |
|---|---|---|---|---|---|---|---|---|---|---|
| J03WMX | +1 / +1 | +0 | 0 / 0 / 0 | 0 | 0,1 / 1,2 | 22–22 | 0.001 / 0.001 | 103 / 104 = 0.99 | 101 / 102 = 0.99 (1.01) | 7814 · 98.9% |
| J03WN1 | +1 / +1 | +0 | 0 / 0 / 0 | 0 | 0,1 / 1,2 | 21–22 | 0.001 / -0.001 | 107 / 104 = 1.029 | 105 / 103 = 1.019 (1.05) | 6638 · 98.5% |
| J03WOH | +1 / +1 | +0 | 0 / 0 / 0 | 0 | 0,1 / 1,2 | 22–22 | 0.0 / -0.001 | 102 / 100 = 1.02 | 100 / 99 = 1.01 (1.031) | 7014 · 98.8% |
| J03WOY | +1 / +1 | +0 | 0 / 0 / 0 | 0 | 0,1 / 1,2 | 22–22 | -0.001 / 0.0 | 113 / 110 = 1.027 | 111 / 109 = 1.018 (1.037) | 6638 · 98.9% |
| J03WPY | +1 / +1 | +0 | 0 / 0 / 0 | 0 | 0,1 / 1,2 | 22–22 | 0.001 / 0.001 | 97 / 97 = 1.0 | 95 / 95 = 1.0 (1.044) | 7837 · 99.1% |
| J03WQQ | +1 / +1 | +0 | 0 / 0 / 0 | 0 | 0,1 / 1,2 | 21–22 | 0.0 / 0.0 | 99 / 99 = 1.0 | 97 / 97 = 1.0 (1.01) | 9967 · 97.0% |
| J03WR9 | +1 / +1 | +0 | 0 / 0 / 0 | 0 | 0,1 / 1,2 | 22–22 | 0.0 / 0.001 | 92 / 92 = 1.0 | 90 / 90 = 1.0 (1.011) | 11813 · 99.4% |

| partido | H / A / D (%) | posesiones | por min vivo | posesión p10 / p50 / p90 (s) | < 1 s / < 2 s / < 3 s (%) | paradas | parada p10 / p50 / p90 (s) | cortas: intercaladas / junto a D / borde | R (%) | huella 1 / 3 / 8 / 25 (informativa) |
|---|---|---|---|---|---|---|---|---|---|---|
| J03WMX | 26.79 / 31.69 / 41.51 | 511 | 8.98 | 0.68 / 3.0 / 15.28 | 16.8 / 37.4 / 49.7 | 103 | 5.01 / 15.48 / 48.89 | 55 / 31 / 0 | 10.76 | 0.9898 / 0.9503 / 0.8184 / 0.4943 |
| J03WN1 | 25.73 / 22.57 / 51.7 | 500 | 10.97 | 0.8 / 3.12 / 12.08 | 15.2 / 34.2 / 47.6 | 107 | 5.38 / 23.84 / 49.25 | 44 / 32 / 0 | 8.8 | 0.9884 / 0.9476 / 0.8352 / 0.5048 |
| J03WOH | 28.51 / 23.92 / 47.57 | 402 | 8.38 | 0.88 / 3.94 / 18.54 | 11.4 / 27.4 / 39.1 | 102 | 6.22 / 19.12 / 52.58 | 23 / 23 / 0 | 5.72 | 0.9925 / 0.9706 / 0.8746 / 0.5816 |
| J03WOY | 26.53 / 26.99 / 46.48 | 456 | 8.97 | 1.04 / 3.6 / 17.58 | 9.0 / 28.1 / 43.2 | 113 | 4.54 / 19.24 / 48.57 | 18 / 23 / 0 | 3.95 | 0.9956 / 0.9732 / 0.8829 / 0.5395 |
| J03WPY | 35.01 / 20.7 / 44.29 | 421 | 7.75 | 0.72 / 3.84 / 20.6 | 13.5 / 29.5 / 41.6 | 97 | 5.55 / 22.8 / 55.38 | 35 / 22 / 0 | 8.31 | 0.9862 / 0.9492 / 0.8518 / 0.5639 |
| J03WQQ | 26.01 / 33.24 / 40.74 | 401 | 7.13 | 1.08 / 4.68 / 21.28 | 9.2 / 25.2 / 38.7 | 99 | 7.86 / 19.6 / 43.38 | 18 / 18 / 1 | 4.49 | 0.992 / 0.9731 / 0.8933 / 0.6125 |
| J03WR9 | 36.26 / 21.85 / 41.89 | 370 | 6.51 | 0.96 / 4.24 / 23.6 | 11.1 / 25.4 / 38.4 | 92 | 7.88 / 20.02 / 48.08 | 18 / 23 / 0 | 4.86 | 0.9886 / 0.9524 / 0.8751 / 0.6011 |
| los 7 | 29.32 / 25.85 / 44.84 | 3061 | 8.3 | 0.84 / 3.68 / 18.6 | 12.5 / 30.0 / 43.1 | 713 | 5.76 / 19.64 / 49.35 | 211 / 172 / 1 | 6.89 | 0.9905 / 0.959 / 0.8594 / 0.5522 |
| 1ª Bundesliga (J03WMX, J03WN1) | 26.27 / 27.2 / 46.53 | 1011 | 9.86 | 0.72 / 3.08 / 13.96 | 16.0 / 35.8 / 48.7 | 210 | 5.1 / 19.82 / 49.2 | 99 / 63 / 0 | 9.79 | 0.9891 / 0.949 / 0.8267 / 0.4995 |
| Düsseldorf en casa (5 de 2. Bundesliga) | 30.54 / 25.3 / 44.15 | 2050 | 7.7 | 0.92 / 3.92 / 20.05 | 10.8 / 27.2 / 40.3 | 503 | 5.98 / 19.52 / 49.16 | 112 / 109 / 1 | 5.46 | 0.9911 / 0.964 / 0.8755 / 0.5781 |

Histograma de duraciones de posesión (s): [0-0,5) [0,5-1) [1-2) [2-3) [3-5) [5-10) [10-20) [20-40) [40+)
  J03WMX: [29, 57, 105, 63, 74, 89, 56, 27, 11]
  J03WN1: [32, 44, 95, 67, 93, 97, 46, 23, 3]
  J03WOH: [14, 32, 64, 47, 77, 81, 54, 28, 5]
  J03WOY: [17, 24, 87, 69, 94, 76, 51, 31, 7]
  J03WPY: [27, 30, 67, 51, 78, 71, 54, 34, 9]
  J03WQQ: [14, 23, 64, 54, 57, 79, 64, 37, 9]
  J03WR9: [23, 18, 53, 48, 62, 76, 44, 30, 16]
  los 7: [156, 228, 535, 399, 535, 569, 369, 210, 60]
  1ª Bundesliga (J03WMX, J03WN1): [61, 101, 200, 130, 167, 186, 102, 50, 14]
  Düsseldorf en casa (5 de 2. Bundesliga): [95, 127, 335, 269, 368, 383, 267, 160, 46]
```

**Lectura de C1–C11 en los 7** **[medido]**:

- **C1 y C2:** los 7 cumplen. Cada parte tiene `TotalTime` / 40 + 1 frames, y el total es 1.002.644,
  exactamente el del artículo.
- **C3, C4 y C5:** los 7 cumplen. No hay ningún salto de `N` ni de `T`, ningún frame repetido, ningún
  frame de jugador fuera de la rejilla del balón, y los flags solo toman 0/1 y 1/2, sin ausentes. **D8
  resuelta: no faltan frames.**
- **Jugadores por frame:** 22 en todo momento, salvo en J03WN1 y J03WQQ, que bajan a 21. Se comprobó
  que no es un hueco del tracking: es una expulsión. En los dos hay una tarjeta roja en los eventos, y el
  equipo afectado juega con 10 en un tramo seguido hasta el final del partido:
  - J03WN1: el visitante (Leverkusen), desde el 15 % de la 1ª parte; casi todo el partido es 11 contra 10;
  - J03WQQ: el visitante (St. Pauli), desde el 28 % de la 2ª parte.
- **C6:** en los 7, la fracción activa coincide con el tiempo neto oficial (diferencias de 0,001 puntos
  o menos). Confirma que el dato oficial sale del mismo flag; sigue sin ser una prueba independiente.
- **C7:** el cociente entre tramos inactivos y reinicios va de 0,99 a 1,03, y ajustado por los bordes
  de cada parte, de 0,99 a 1,02. Sin los balones a tierra va de 1,01 a 1,05. Los 7 están dentro del
  rango fijado (0,85–1,30). La cobertura uno a uno sigue siendo 2d.
- **C11:** en los 7, el jugador cercano es del equipo del flag entre el 97,0 % (J03WQQ) y el 99,4 %
  (J03WR9) de los frames estables, con entre 6.638 y 11.813 frames por partido. **`BallPossession` 1 =
  local queda confirmado en los 7**, que era la condición para pasar a 2c.

**2a en los 7** **[medido]**:

- **Balón muerto:** entre el 40,7 % y el 51,7 % de los frames, con 92–113 paradas por partido (713 en
  total) y una duración mediana de 15,5 a 23,8 s. J03WN1, con el 51,7 %, es el partido del 11 contra 10
  casi entero.
- **Posesiones:** 370–511 por partido (3.061 en total), de 6,5 a 11,0 por minuto de balón vivo.
  Duración mediana de 3,0 a 4,7 s. Las de menos de 1 s son entre el 9,0 % y el 16,8 %.
- **Histograma de duraciones:** con los 7 juntos, los intervalos más poblados son de 1 a 10 s. Con
  intervalos de anchura desigual no se ven dos modas claras; no se ha comprobado con un método formal
  **[sin verificar]**.

**Medida R (criterio 2a de la bitácora)** **[medido]**:

- De las posesiones de menos de 1 s, 211 están intercaladas entre dos del mismo rival, 172 tocan un `D`
  y 1 está en el borde de una parte.
- **R = 6,89 % con los 7 juntos.** Está entre los dos cortes fijados (3 % y 10 %), así que, como se fijó
  antes de medir, R no decide: **lo deciden 2b y 2c.**
- Por partido, R va del 3,95 % (J03WOY) al 10,76 % (J03WMX). J03WMX es el único que pasa del 10 %.
- **Los dos de 1ª (9,79 %) frente a los cinco del Düsseldorf (5,46 %).** Los de 1ª tienen también más
  posesiones de menos de 1 s (16,0 % frente a 10,8 %) y más posesiones por minuto (9,9 frente a 7,7).
  Explicaciones posibles, que con dos partidos no se pueden separar **[inferencia]**:
  - otro estilo de juego en 1ª, con más presión y más duelos;
  - las particularidades de esos dos partidos: un Bayern y un Leverkusen con 10 casi todo el partido;
  - operadores distintos en cada estadio, si el flag lo marca una persona (D7);
  - el mismo equipo local en los cinco de 2ª, que hace que sus partidos se parezcan entre sí.
- Casi la mitad de las posesiones cortas (172 de 384) tocan un `D`: duran menos de 1 s justo antes de
  una parada o justo después de un reinicio. Qué son se verá en 2d y 2e **[sin verificar]**.

**2b, solo informativa (D21):** la huella con los 7 juntos es 0,9905 / 0,959 / 0,8594 / 0,5522 con 1 /
3 / 8 / 25 frames. No se usa para decidir nada.

**Sin verificar todavía:**
- la cobertura uno a uno de los reinicios (2d);
- qué son las posesiones cortas junto a un `D` (2d, 2e);
- si la diferencia entre 1ª y 2. Bundesliga se debe a la liga, a esos partidos o a los operadores.

### 6. Parada 3: medidas añadidas y detalles fijados antes de mirar los datos

**Cuándo:** el 11/11, tras la revisión de la parada 2 y antes de calcular ninguna medida de 2c, 2d, 2e
ni 2g con datos reales. Lo nuevo lo pide la sesión orquestadora; los detalles concretan lo ya fijado
sin cambiar ningún corte.

**Veredicto por partido.** Cada criterio se da con los 7 juntos y partido a partido, contando cuántos
de los 7 cumplen, cuántos no y cuántos quedan entre medias. La diferencia entre los dos de 1ª y los del
Düsseldorf se trata como variación entre partidos, no como efecto de la liga.

**Nuevo: posesiones cortas junto a un `D`** (las de menos de 1 s que tocan una parada).

- **Antes de un `D`** (X → y → `D`, con y del equipo Y y de menos de 25 frames). Para cada una:
  1. **toque de Y:** hay un toque detectado de Y entre 5 frames antes del inicio de y y su final;
  2. **control de Y:** algún control de Y (12 frames, mismo jugador) se solapa con y;
  3. **balón fuera:** en el inicio del `D`, el balón está fuera de las líneas o las cruzó en los 3 s
     anteriores;
  4. **quién reanuda:** el equipo del flag en el primer frame activo después del `D`.
- Si se dan 1 y 3 y no 2, es un **toque de Y sin control que cambia el flag justo antes de que el balón
  salga** (un despeje o un desvío a córner o a banda). Cuenta para 2g aunque no esté intercalado. Se da
  qué fracción de las posesiones cortas antes de un `D` son así, y en cuántas reanuda X (lo esperable si
  el último toque fue de Y).
- **Después de un `D`** (`D` → y → X): si hay un toque de Y entre 5 frames antes del inicio de y y 25
  frames después, si Y tiene control y quién es X. Es descriptivo: un reinicio de Y que se pierde
  enseguida.

**Nuevo: dos modas.** Histograma de las duraciones de posesión en escala logarítmica, con intervalos de
la misma anchura (0,2 décadas, de 0,04 s a 400 s), por partido y con los 7 juntos. Se dice que hay dos
modas si hay dos máximos locales separados por un intervalo con como mucho el 70 % del menor de los dos.
Es descriptivo.

**Detalles de implementación** (concretan lo fijado; no cambian ningún corte):

- **velocidad por frame:** v_t = (p_t − p_{t−1}) × 25;
- **toque:** módulo de la diferencia entre la velocidad media de los frames t+1…t+4 y la de los frames
  t−3…t, de 3 m/s o más y máximo local en ±4 frames. Se atribuye al equipo del jugador más cercano si
  está a 1,5 m o menos; si no, el toque no es de nadie;
- **jugador más cercano:** entre los dos equipos, en cada frame;
- **control:** rachas de 12 frames o más en las que el mismo `PersonId` es el más cercano y está a 1,0 m
  o menos;
- **retención:** rachas de 5 frames o más en las que el más cercano es del mismo equipo y está a 1,0 m o
  menos;
- **2c, momento:** se toma el control del equipo nuevo cuyo inicio cae en ±2 s del cambio y está más
  cerca de él. Los cambios sin ningún control así se cuentan aparte;
- **placebo de 2b, 2c y de las medidas de `PASOS.md`:** hasta 2.000 frames activos por partido elegidos
  al azar, con semilla 20261111 + número del partido (0–6). Ninguno tiene un cambio a menos de 50
  frames, todos tienen el balón activo y el mismo flag en su ventana, y se usa la misma ventana que en
  la medida real;
- **2g:** el toque tiene el balón activo y no hay ningún `D` entre el toque y el siguiente control de X.
  Si lo hay, el caso va a "posesiones cortas antes de un `D`";
- **1a:** la hora del evento (`EventTime`) se pasa al frame cuya `T` es la más cercana. Se excluyen los
  saques iniciales a 5 s o menos del primer frame de la parte (abren la parte y no vienen de un `D`).
  El fin de un `D` es el primer frame activo tras un tramo inactivo. Los balones a tierra se dan aparte.
  El placebo usa el mismo número de instantes por parte, al azar y uniformes dentro de la parte;
- **1b:** campo de 105 × 68 m (metadatos): fuera si \|x\| > 52,5 + margen o \|y\| > 34 + margen;
- **2d, tipo de parada:** fuera por banda si \|y\| > 34; fuera por fondo si \|x\| > 52,5; dentro del
  campo en otro caso. Se mira en el inicio del `D` o, si cruzó una línea en los 3 s anteriores, en el
  primer frame fuera;
- **sensibilidad:** cada parámetro se varía de uno en uno, con el resto en su valor principal.

### 7. Parada 3: 2c, 2d, 2e y 2g de los 7 partidos

**Ficheros.** Las tablas completas están en `validation/resultados/2026-11-11_experimento0.md`. Las
genera `parada3_tablas.py` a partir del JSON que escribe `parada3.py`, fuera del repo, sin copiar
cifras a mano.

**Pruebas sintéticas, antes de tocar datos reales** **[medido]**:

- **Detectores:**
  - golpeo junto al local A: un toque en el frame 60 ± 2 y un control;
  - balón que pasa de largo a 6 m/s a 0,3 m del visitante B: ningún toque y ningún control, pero sí una
    retención de 5 frames. Por eso se cambió a control;
  - desvío de 60° junto al visitante C: un toque y ningún control;
  - ruido: ningún toque.
- **Lógica,** con segmentos puestos a mano: grupos de 2b, momento, 2g y emparejamiento uno a uno.
- **`medir_parte` de principio a fin.** Guion: pase con control, desvío a banda, saque de banda y
  control. Pasó a la primera. Para no quedarse en "pasa", se imprimieron los valores intermedios, y
  coinciden con lo previsto al escribir el guion:
  - toques en 200, 250, 350, 412, 426, 549 y 579;
  - controles 0–203, 248–354 y 578–700;
  - momento −4;
  - 7 frames desde el cruce de la línea hasta el `D`;
  - 9 frames activos fuera.
- **Prueba de balón congelado:** un jugador junto al balón durante un `D` da un control con todos los
  frames y ninguno con `solo_activos`.

**Registro, en el orden en que se hizo y se vio:**

1. **Primera ejecución** (`parada3.py --solo-principal`, variante fijada): 4 s. Veredictos con los 7:
   1a cumple, 1b cumple, 2b entre medias, 2c "al controlar", 3a cumple, 2g no cumple.
2. **2e daba −2 frames en todas las paradas.** Ningún dato real es tan regular, así que antes de
   seguir se miró el balón en los frames inactivos (comprobación aparte, solo agregados) **[medido]**:
   - en los 7 partidos, el 100 % de los frames `D` tiene la misma posición que el anterior;
   - el salto al empezar el `D` es 0 en todos (el balón se congela en la posición del último frame
     activo);
   - al reanudar salta: mediana de unos 6 m, p10 de 1,5–2 m y p90 de 22–27 m;
   - la velocidad centrada de ±2 frames ve ese salto 2 frames antes, y de ahí el −2. **La medida
     fijada de 2e no sirve con estos datos.**
3. **Qué más toca el congelado** (`diagnostico_congelado.py`, solo recuentos) **[medido]**:
   - 603 de 5.439 controles (11 %) incluyen frames `D`: un jugador junto al balón congelado;
   - 1.289 de 16.397 toques (8 %) tienen su ventana en un borde de `D`: la parada brusca y el salto;
   - 317 de 2.351 cambios tienen un `D` en su ventana de 2b;
   - de los 203 casos de 2g, ninguno tiene un `D` entre el control anterior y el toque, así que 2g no
     se ve afectado.

   Por eso se añadió la variante **"solo en juego"**. Cambia poco: 2b pasa del 42,9 % al 42,1 % y 2g
   se queda en el 85,2 %. Lo que sí cambia son los toques "después de un `D`", que eran el salto.
4. **2g, contra un placebo.** Se añadió el placebo (toques del propio equipo entre sus dos controles):
   el flag pasa al otro equipo en el 9,5 % de los toques, frente al 85,2 %. También el desfase: el
   cambio cae en el mismo frame del toque (mediana 0).
5. **Revisión antes de escribir.** Se añadieron cuatro comprobaciones:
   - el estado del flag 3 frames antes del toque. Es de X en el 71,9 %; de esos, el 81 % pasa a Y, y el
     74,7 % a ≤ 2 frames;
   - el recuento por hueco entre controles: 83,5 % de 176 huecos; placebo, 10,0 % de 1.140;
   - la duración de la racha del rival: mediana de 2,0 s; solo el 17,9 % dura menos de 1 s;
   - para 1b, episodios activos fuera que no dependen del congelado: 2 en los 7 partidos.
6. **Flag durante el `D`.** Constante en el 99,6 % de las paradas, e igual al del último frame activo
   solo en el 30,8 %. El flag pasa al equipo que reanuda en el primer frame del `D` **[medido]**.
   En las 696 paradas que acaban en un reinicio es constante en todas (`diagnostico_congelado.py`).
7. **Medidas del congelado en el script** (porcentaje de balón quieto, salto al reanudar), para que
   sean reproducibles.
8. **Segunda revisión, antes de enviar.** Se añadieron cuatro comprobaciones.
   - **Cuándo pasa a activo.** Con el balón congelado, la medida nueva de 2e solo puede dar 0 o más:
     dice que el flag no pasa a activo antes del golpeo, pero no que no lo haga después. Por eso se
     midió la distancia del jugador del equipo del flag al balón en el primer frame activo:
     - mediana 0,75 m, p90 2,51 m;
     - el 69,8 % a ≤ 1 m;
     - en saques de banda y córners, entre el 51 % y el 58 % a ≤ 1 m.

     Lectura: en el golpeo o pocos frames después **[medido / inferencia]**.
   - **El equipo del evento de reinicio emparejado** coincide con el flag del primer frame activo en el
     97,8 % **[medido]**.
   - **Los jugadores no se congelan:** ningún frame `D` tiene a todos quietos. Velocidad media de 1,0 m/s
     en `D` frente a 2,3 m/s en juego **[medido]**.
   - **El criterio original exacto de 2b** (retención en ±1 s) es la fila "ventana 2b ±1 s": 59,8 %,
     entre medias en los 7 partidos.
   - Además, el desfase toque–cambio se da con el signo de `PASOS.md` en el fichero de resultados.

   Ejecución final: 46,1 s y 457 MB de pico para las dos variantes, con las 21 variaciones cada una.
   Cifras del commit `65d552f`.

**Cambios de criterio en esta parada:**

- **Antes de la primera ejecución con datos reales:**
  - 2b y 2c también con la retención (los criterios originales);
  - placebo de la retención;
  - margen del placebo como parámetro, para la fila "placebo ±1 / ±3 s" de la sensibilidad fijada;
  - tope de 1.000 placebos por parte (2.000 por partido, como se fijó);
  - distancia a la línea medida en el inicio del `D`;
  - eventos `Delete` fuera;
  - campo de los metadatos (105 × 68 en los 7);
  - anclaje de la hora con el saque inicial de cada parte.
- **Después de ver datos:**
  - variante "solo en juego";
  - distancia del jugador del flag al balón al reanudar, equipo del evento frente al flag, y
    movimiento de los jugadores durante los `D`;
  - medida nueva de 2e. La fijada se mantiene en la tabla, marcada como artefacto;
  - en 2g: placebo, desfase, flag 3 frames antes, recuento por hueco y duración de la racha;
  - en 1b: episodios activos fuera de ≥ 1 s;
  - flag durante el `D`, balón quieto y salto al reanudar.
- Ningún corte de ningún veredicto ha cambiado. Todo se da con el criterio fijado y con el nuevo.

**Resultados** (tablas en el fichero de resultados) **[medido]**:

| punto | criterio | los 7 | partidos que cumplen / entre medias / no | ¿aguanta? |
|---|---|---|---|---|
| 1 | 1a | cumple | 7 / 0 / 0 | sí con ±5 s; las ventanas de ±2 y ±3 s son descriptivas y caen por el error de hora de los eventos **[inferencia]** |
| 1 | 1b | cumple | 7 / 0 / 0 | sí |
| 2 | 2b (control) | entre medias, 42,9 % | 0 / 5 / 2 | no: control de 20 frames o ventana de ±1 s → no cumple |
| 2 | 2c | "al controlar", mediana −2 frames | 7 | sí, pero mide el primer contacto (ver abajo) |
| 2 | 2g | no cumple, 85,2 % | 0 / 0 / 7 | sí |
| 3 | 3a | cumple, 0,2 % | 7 / 0 / 0 | sí |

- **2c no apoya el punto 2.** El control "empieza" cuando el balón llega a 1 m, que es casi el primer
  contacto. Además, un 35,5 % de los cambios con control lo tiene 0,5–2 s después del cambio.
  **[inferencia]**: el flag cambia en el primer contacto del rival.
- **1ª frente a Düsseldorf:** el flag se comporta igual en los dos grupos (2g 83,3 % frente a 86,4 %;
  2b 42,5 % frente a 43,1 %).
- **Dos modas en las duraciones,** con los 7 juntos: una pequeña en 4–6 frames y la principal en
  1,6–2,5 s.

**2f no se ha hecho.** Las reglas del paso 3 están escritas para campos de StatsBomb. Trasladarlas a los
eventos de la DFL es un diseño que hay que fijar antes de medir. Queda propuesta como parada siguiente,
con 3b.

**Sorpresas:**

- el balón congelado durante el `D`, que delata la etiqueta;
- la medida fijada de 2e, inservible por eso;
- el flag cambia al equipo que reanuda en el primer frame del `D`.

**Sin verificar:**

- si el ATD también congela el balón muerto;
- qué son los 21 fines de `D` sin reinicio;
- la causa de la diferencia de R entre 1ª y 2. Bundesliga;
- 2f y 3b.
