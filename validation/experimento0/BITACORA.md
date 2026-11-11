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
