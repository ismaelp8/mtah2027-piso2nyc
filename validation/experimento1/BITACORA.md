# Bitácora del experimento 1: cuándo cambia la posesión y con qué control corregir la DFL

Registro de cada paso, comando y comprobación. Solo agregados. Etiquetas de evidencia: **[medido]**,
**[inferencia]**, **[sin verificar]**.

## Encargo

- **Quién lo pide:** Ismael, directamente en la sesión, el 12/11/2026.
- **Qué:**
  1. entender bien cuándo cambia la posesión según la normativa del repo oficial;
  2. buscar métodos o estudios implementados, que funcionen y que usen el mismo criterio que el reto;
  3. valorar si con lo que tenemos (DFL, detectores del experimento 0, candidatos del informe) se puede
     seguir o hace falta algo nuevo.
- **Punto de partida:** decisión de Ismael del 12/11 (`docs/decisiones.md`): se siguen las normas del
  reto, la posesión cambia cuando el rival controla.

## 1. Qué dice la normativa oficial (leída entera el 12/11)

Fuentes: `CHALLENGE.md`, `FAQ.md`, `OVERVIEW.md`, `SUBMISSION.md`, `RULES.md`, `EVALUATION.md` y
`DATA.md`. `upstream` no tiene cambios desde la copia (último commit del 23/10).

- **El cambio:** un jugador del rival consigue la posesión **controlada** (`CHALLENGE.md` 55–58).
- **Balón disputado o suelto:** la posesión sigue con el último equipo que la tuvo (62–64).
- **Tras un reinicio:** hay un poseedor claro (66–67).
- **No es cambio** (76–80):
  - un toque sin control;
  - un desvío de un pase que no lo intercepta;
  - un duelo aéreo ganado sin control posterior de ese equipo ("de ese equipo": vale que controle un
    compañero).
- **Proxies de control, solo orientativos** (69–74): un jugador retiene el balón unos segundos; un
  equipo encadena más de dos pases.
- **Lo que manda:** la GT, que sale mecánicamente del flag de un tracking corregido, sin suavizar
  (97–100). La GT pública es la referencia de cómo se etiquetan estos casos (82–87, 102–103).
- **`SUBMISSION.md`** pide explicar en el documento técnico dónde se pone la línea en balones sueltos,
  disputas y reinicios (70).

**La GT pública, leída como etiquetas** (permitido por `CLAUDE.md`: significado de las etiquetas, no
para elegir versiones) **[medido]**:

- 21 rachas, 17 posesiones;
- dos posesiones del local muy cortas intercaladas entre dos del visitante (A → H → A): 19 frames
  (0,76 s) y 33 frames (1,32 s); y una del visitante de 71 frames (2,84 s) entre dos del local;
- 12 cambios directos H↔A en unos 4 minutos de balón vivo.

**Lectura [inferencia]:** la GT no exige "unos segundos" de control. Tiene posesiones de menos de 1 s
entre dos del mismo rival. Pueden ser controles reales muy breves (recibir y perderla enseguida) o
toques sin control. Solo el vídeo lo dice: es la comprobación cualitativa que puede hacer una persona.

## 2. Antes de mirar los duelos de los eventos DFL

**Qué hay en los eventos** (vistos solo los nombres y valores de los atributos, sin cruzar con el flag)
**[medido]**:

- los duelos (`TacklingGame`) llevan `PossessionChange` (true/false), `WinnerRole` y `LoserRole`
  (`withBallControl` / `withoutBallControl`), `WinnerResult` (`ballcontactSucceeded`, `layoff`,
  `ballClaimed`, `ballControlRetained`, `fouled`, `dribbledAround`) y `Type` (`ground` / `air`);
- hay recuperaciones (`BallClaiming`, `Type` `InterceptedBall` o `BallClaimed`) y despejes
  (`OtherBallAction`, `DefensiveClearance`);
- `BallPossessionPhase` es casi único por evento (1.190 valores en 1.231 eventos de J03WMX): no agrupa
  posesiones de equipo.

Son anotaciones humanas: una referencia independiente del flag y del tracking. Si `PossessionChange`
sigue un criterio de control, sirve para medir el flag y para elegir la definición de control sin
circularidad.

**Medida fijada antes de cruzar con el flag:**

- cada duelo se pasa al frame cuya `T` es la más cercana a su `EventTime`; se quedan los que tienen el
  balón activo en ese frame;
- X es el equipo del jugador `withBallControl` antes del duelo e Y el otro;
- **M1:** el flag de la DFL marca a Y en algún frame activo entre 2 s antes y 3 s después del duelo
  (ventana ancha por el error de hora de los eventos, −0,37 ± 1,82 s);
- **grupos:**
  - G1, `PossessionChange` = true;
  - G2, `PossessionChange` = false y ganador Y (`WinnerRole` `withoutBallControl`): toque del rival
    sin cambio de posesión según el anotador. Se da por `WinnerResult` y por `Type`;
  - G3, `PossessionChange` = false y ganador X: el que tenía el balón gana el duelo (placebo).

**Lo esperado:** G1 alto en cualquier caso y G3 bajo. Para G2:

- si el flag sigue al último toque, alto, como G1;
- si sigue al control, bajo, como G3.

Es descriptivo: no decide nada por sí solo. `fouled` se da aparte, porque lleva a un `D` cuyo flag es el
del equipo que reanuda.

## 3. Resultado de M1 y medida afinada

**M1** (`duelos_dfl.py`, 1.412 duelos, 147 descartados por balón inactivo en el frame del evento)
**[medido]**: el flag marca a Y en el 88,3 % de G1, el 87,2 % de G2 y el 57,7 % de G3.

- G2 se parece a G1, como si el flag tratara igual los duelos que el anotador da sin cambio.
- Pero **el placebo (G3) sale muy alto**: en 5 s el flag cambia a menudo por el juego normal. M1 no
  discrimina bien. Se apunta tal cual y no se usa para concluir.

**Sorpresa en los atributos** (tabla cruzada, sin el flag) **[medido]**:

- 90 duelos con `PossessionChange` = false en los que el que no tenía el balón gana con `ballClaimed`;
- 77 con `PossessionChange` = true en los que gana el que tenía el balón.

O `PossessionChange` no significa "cambio de posesión del equipo" tal como lo entendemos, o los roles
significan otra cosa. **[sin verificar]** hasta encontrar el catálogo de definiciones de la DFL.

**Medida afinada (fijada después de ver M1, antes de calcularla):**

- **Sincronía con el tracking:** el frame del duelo es, entre 3 s antes y 3 s después de la hora del
  evento, el frame activo en que el más lejano de los dos jugadores del duelo (`Winner`, `Loser`, por su
  `PersonId`) está más cerca del balón. Si esa distancia pasa de 3 m, el duelo no se sincroniza y se
  cuenta aparte.
- **M2:** entre los duelos con el flag en X 10 frames antes, qué fracción tiene el flag en Y en algún
  frame activo entre 5 frames antes y 25 frames después (−0,2 s / +1 s).
- **M3:** qué fracción tiene el flag en Y 2 s después.
- **Grupos por quién gana y cómo** (`WinnerResult`): Y con `ballClaimed` (control positivo: tiene que
  cambiar con cualquier criterio), Y con `ballcontactSucceeded` (el caso en disputa), Y con `layoff`, X
  con `ballControlRetained` (control negativo), y los demás. Se da también por `PossessionChange`.
- **Lo esperado:** si el flag sigue al toque, Y-`ballcontactSucceeded` se parece a Y-`ballClaimed` en
  M2. Si sigue al control, se parece a X-`ballControlRetained`.

## 4. Resultado de la medida afinada (`duelos_sincronizados.py`)

**Sincronía [medido]:** 1.137 duelos medidos; 70 sin sincronizar (> 3 m) y 205 con el flag fuera de X
10 frames antes. En el frame sincronizado, el más lejano de los dos jugadores está a 0,83 m del balón
(mediana; p90 1,34 m).

| quién gana y cómo | n | M2: flag en Y hasta 1 s | M3: flag en Y a 2 s |
|---|---|---|---|
| Y, `ballClaimed` (se hace con el balón) | 168 | 75,0 % | 70,5 % |
| Y, `ballcontactSucceeded` (toca el balón) | 288 | 76,4 % | 72,0 % |
| Y, `layoff` (lo juega de primeras) | 80 | 80,0 % | 70,6 % |
| X, `ballControlRetained` (lo conserva) | 112 | 10,7 % | 22,7 % |
| X, `dribbledAround` (regatea) | 43 | 9,3 % | 16,7 % |
| X, `layoff` | 238 | 29,4 % | 32,3 % |

- **El flag cambia igual con un toque que con una recuperación** (76 % frente a 75 %), y casi nunca si
  el que tenía el balón lo conserva (11 %). **Confirma 2g con anotaciones humanas,** sin el detector de
  toques del experimento 0.
- **`PossessionChange` sí distingue lo que el flag no.** En Y-`ballcontactSucceeded`, el flag cambia en
  el primer segundo igual (74,8 % con `PossessionChange` = true y 77,6 % con false). A los 2 s sigue en
  Y el 89,2 % con true y solo el 56,9 % con false. Lo mismo en `ballClaimed` (85,7 % frente a 43,8 %) y
  en `layoff` (96,0 % frente a 46,2 %).
- **Lectura [inferencia]:** el anotador marca cambio de posesión cuando el equipo que gana el duelo se
  queda con el balón, que es un criterio de control como el del reto. El flag cambia en el toque y luego
  vuelve. Falta confirmar la definición en el catálogo de la DFL **[sin verificar]**.
- **Consecuencia:** los duelos anotados son una referencia humana, independiente del tracking, para
  elegir la definición de control sin circularidad. Son unos 1.400 en los 7 partidos.

## 5. Antes de medir cuánto pesa corregir (fijado antes de calcular)

**Corrección R(c)** para una definición de control c, por parte:

1. se toman las rachas del flag (H, A y `D`);
2. una racha de equipo que sigue a un `D`, o que abre la parte, se queda como está: tras un reinicio
   hay un poseedor claro;
3. una racha del equipo Y que sigue a una del equipo X se queda solo si Y tiene control según c en
   algún frame de la racha. Si no, pasa a ser de X: la posesión sigue con el último equipo que la tuvo;
4. se recorre en orden, así que una racha reetiquetada se une a la anterior;
5. el `D` no cambia; los frames `D` se tapan para los detectores (variante "solo en juego").

**Definiciones de control c** (las del experimento 0 y las de `CHALLENGE.md`, sin ajustar):

- C0-8, C0-12, C0-20 y C0-50: el mismo jugador, el más cercano, a ≤ 1 m durante ≥ 8, 12, 20 o 50
  frames. C0-50 (2 s) es el proxy "unos segundos";
- Ret-5: el equipo, el más cercano, a ≤ 1 m durante ≥ 5 frames;
- Dos toques: dos toques seguidos de Y separados ≤ 2 s sin toque de X entre medias (un pase entre
  compañeros o una conducción);
- C0-12 o dos toques.

**Qué se mide (descriptivo, no elige nada):**

- por partido y con los 7: posesiones, posesiones por minuto vivo, cambios H↔A, rachas quitadas y su
  duración, frames que cambian de equipo;
- acuerdo con los duelos anotados: entre los duelos sincronizados con el flag en X antes y ganados por
  Y con toque, recuperación o `layoff`, qué fracción tiene la etiqueta corregida en Y a 2 s:
  - con `PossessionChange` = true (debería ser alto);
  - con false (debería ser bajo);
  - y la media de los dos aciertos (acierto equilibrado).

  Lo mismo para el flag sin corregir, como referencia.

## 6. Cuánto pesa corregir (`peso_correccion.py`) [medido]

Prueba sintética de la corrección (`correccion.py`): OK.

| definición de control | posesiones (los 7) | por minuto vivo | cambios H↔A | < 1 s | frames vivos que cambian de equipo | acuerdo con los duelos anotados (equilibrado) |
|---|---|---|---|---|---|---|
| flag tal cual | 3.061 | 8,30 | 2.351 | 384 | 0 % | 68,0 % |
| C0-8 | 1.747 | 4,74 | 1.037 | 76 | 7,2 % | 76,6 % |
| C0-12 | 1.549 | 4,20 | 839 | 43 | 8,9 % | 77,3 % |
| C0-20 | 1.359 | 3,69 | 649 | 18 | 10,6 % | 76,8 % |
| C0-50 (2 s, "unos segundos") | 1.008 | 2,73 | 298 | 8 | 19,3 % | 67,2 % |
| Ret-5 | 2.047 | 5,55 | 1.337 | 119 | 4,9 % | 74,5 % |
| dos toques | 1.552 | 4,21 | 842 | 15 | 8,7 % | 78,2 % |
| C0-12 o dos toques | 1.736 | 4,71 | 1.026 | 48 | 6,8 % | 79,6 % |

- **Acuerdo con los duelos:** 229 duelos con `PossessionChange` = true y 211 con false. Todos tienen el
  flag en X antes, los gana Y con toque, recuperación o `layoff`, y tienen el balón activo a 2 s.
  - El flag tal cual acierta el 88,6 % de los true, pero solo el 47,4 % de los false.
  - C0-12 acierta el 76,4 % y el 78,2 %.
- **Cuánto pesa:** cualquier corrección quita entre un tercio y dos tercios de las posesiones. Las
  rachas quitadas duran una mediana de 1,5–2,3 s, según la definición.
- **Lo que separa la referencia de duelos:**
  - el flag tal cual y C0-50 quedan claramente peor (67–68 %);
  - Ret-5 queda algo peor (74,5 %);
  - C0-8, C0-12, C0-20, dos toques y la unión quedan en 76,6–79,6 %. Con unos 440 duelos, esas
    diferencias son del tamaño del ruido (unos ±3 puntos) **[inferencia]**. Es un empate a falta de más
    referencias.
- **Contexto, no se usa para elegir:**
  - el flag tal cual tiene unas 8,3 posesiones por minuto de balón vivo, más o menos el doble que la
    ventana pública (17 posesiones de los primeros 5 minutos, no representativas);
  - es coherente con que la GT no cambie en cada toque **[inferencia]**;
  - no se compara ninguna definición de control con la ventana pública.
- **Lo que R(c) no resuelve: la fecha del cambio.** R(c) solo quita rachas: todo cambio que se queda
  sigue fechado donde lo puso el flag, en el primer toque. Si la GT fecha el cambio cuando empieza el
  control, habría desfases de varios frames; a la escala del `spellF1`, 8 frames pesan. Queda abierto.

## 7. Antes de medir el otro fallo: quitar posesiones reales (fijado antes de calcular)

La referencia de duelos solo ve una parte: es pequeña (unos 440 casos) y con `PossessionChange` = true
las correcciones ya bajan del 88,6 % del flag al 72–82 %, lo que apunta a que quitan posesiones
reales. Para medir ese fallo se usan eventos en los que un equipo **seguro** tiene el balón con
cualquier lectura del reto:

- **Pases completados** (`Play` en juego, `Evaluation` = `successfullyCompleted`, con `Recipient`):
  - se sitúan en el frame activo, en ±3 s de su hora, en que el pasador (`Player`, por `PersonId`) está
    más cerca del balón (≤ 1,5 m; si no, no se cuentan);
  - la recepción es, en los 3 s siguientes, el frame en que el receptor está más cerca del balón
    (≤ 1,5 m);
  - **G-pase:** la etiqueta 5 frames después de la recepción es del equipo del pasador. No depende de
    cuándo se feche el cambio: en un pase completado el equipo ya controla al recibir;
  - aparte, y solo descriptivo porque sí depende de la fecha: la etiqueta en el frame del pase.
- **Recuperaciones** (`BallClaiming`, `InterceptedBall` o `BallClaimed`):
  - se sitúan igual con el jugador que recupera;
  - **G-recuperación:** la etiqueta 12 frames (0,5 s) después es de su equipo.
- Se descartan los casos con el balón inactivo en los frames medidos.
- **Para cada definición:** el fallo de quitar (porcentaje de G-pase y G-recuperación con la etiqueta
  del otro equipo) frente al de no quitar (los duelos con `PossessionChange` = false que siguen en Y a
  2 s).
- **Empate:** diferencias de acierto entre definiciones con bootstrap emparejado (1.000 remuestreos,
  semilla 20261112), sobre los mismos eventos. Si el intervalo del 95 % de la diferencia incluye el 0,
  es un empate.
- **Nada de esto elige todavía:** la elección necesita, además, que se verifique qué significa
  `PossessionChange`, y la decide Ismael.

## 8. Los dos fallos, medidos (`comparar_definiciones.py`) [medido]

Eventos usados:

- 3.142 pases completados situados (113 sin situar al pasador y 975 sin situar la recepción a ≤ 1,5 m
  en 3 s);
- 195 recuperaciones;
- 440 duelos.

Acierto de cada corrección (en G-pase y G-recuperación, lo que no es acierto es una posesión real
quitada):

| definición | G-pase | G-recuperación | duelo `PossessionChange` = true (Y a 2 s) | duelo `PossessionChange` = false (X a 2 s) |
|---|---|---|---|---|
| flag tal cual | 97,9 % | 89,2 % | 88,6 % | 47,4 % |
| C0-8 | 97,5 % | 84,6 % | 81,7 % | 71,6 % |
| C0-12 | 96,6 % | 81,0 % | 76,4 % | 78,2 % |
| C0-20 | 95,3 % | 75,4 % | 71,6 % | 82,0 % |
| C0-50 | 84,0 % | 59,0 % | 52,4 % | 82,0 % |
| Ret-5 | 98,2 % | 86,2 % | 87,3 % | 61,6 % |
| dos toques | 98,1 % | 80,5 % | 78,6 % | 77,7 % |
| C0-12 o dos toques | 98,8 % | 87,7 % | 84,3 % | 74,9 % |

Diferencias con C0-12 (bootstrap emparejado, intervalo del 95 %, en puntos):

| definición | G-pase | G-recuperación | `PossessionChange` = true | `PossessionChange` = false |
|---|---|---|---|---|
| C0-12 o dos toques | +1,7 a +2,8 | +3,6 a +10,3 | +4,4 a +11,8 | −6,6 a +0,5 (empate) |
| dos toques | +1,0 a +2,2 | empate | empate | empate |
| C0-8 | +0,5 a +1,3 | +1,0 a +6,7 | +2,6 a +8,3 | −10,4 a −3,3 |
| C0-20 | −1,7 a −0,8 | −9,2 a −2,6 | −8,3 a −1,3 | +0,5 a +7,1 |

Lectura:

- **Quitar posesiones reales es poco frecuente en los pases completados** (95–99 %), salvo con C0-50
  (16 % quitadas): el proxy "unos segundos" quita demasiado. Las recuperaciones son el punto débil de
  todas (59–88 %).
- **Hay un compromiso:** cuanto más exigente el control, menos falsos cambios (duelos false) y más
  posesiones reales quitadas (recuperaciones y duelos true).
- **"C0-12 o dos toques" no queda por detrás de C0-8 ni de C0-12 en ninguna de las cuatro
  referencias,** y en tres de ellas va por delante. Corresponde a los dos proxies del reto: un jugador
  retiene el balón, o el equipo encadena toques (pases).
- **No se elige nada aquí:**
  - el significado de `PossessionChange` sigue **[sin verificar]**;
  - la fecha del cambio queda abierta (R(c) no la toca);
  - la decisión es de Ismael.
- **En el frame del pase** (depende de la fecha): 93,0 % el flag y 82,9–94,7 % las correcciones.
- **Por partido** (G-pase / G-recuperación / duelos true / duelos false), el patrón se repite en los 7
  **[medido]**:
  - el flag tal cual acierta solo el 25–61 % de los duelos sin cambio en todos los partidos;
  - "C0-12 o dos toques" acierta el 98–100 % de G-pase, el 78–100 % de G-recuperación (unas 28 por
    partido), el 79–90 % de los duelos true y el 68–82 % de los false.

## 9. Cuánto importa la fecha del cambio (`fecha_del_cambio.py`, descriptivo) [medido]

Para cada cambio que se queda tras la corrección: frames entre el cambio del flag (el primer toque del
equipo nuevo) y el primer frame de control del equipo nuevo según la definición.

| definición | cambios | mediana / p75 / p90 (frames) | en el mismo frame | a más de 8 frames | a más de 1 s |
|---|---|---|---|---|---|
| C0-12 | 839 | 15 / 47 / 83 | 45,5 % | 52,7 % | 40,5 % |
| dos toques | 842 | 0 / 25 / 74 | 62,1 % | 28,5 % | 24,0 % |
| C0-12 o dos toques | 1.026 | 0 / 3 / 53 | 71,1 % | 24,5 % | 20,6 % |

**Lectura:** si la GT fecha el cambio al empezar el control, y no en el primer toque, entre una cuarta
parte y la mitad de los cambios se moverían más de 8 frames. Es la escala en que el `spellF1` ya pierde
(0,89 con 8 frames de retraso). La fecha es una pregunta tan importante como la definición de control,
y solo la GT pública con el vídeo puede responderla.

## 10. Búsqueda de métodos implementados (subagente, verificado en parte a mano)

Un subagente revisó métodos publicados con código. Lo verificado aquí en la fuente primaria está
marcado **[fuente]**.

- **Bassek et al. 2025** (artículo del dataset, texto completo en Europe PMC, PMC11787359) **[fuente]**:
  - dice que la posesión "is defined by the player in control of the ball", y remite al catálogo de
    definiciones de la DFL (versión 5.1, 2020);
  - el flag, en cambio, cambia en el primer toque (2g y sección 4).

  **Un proveedor llama "control" a algo que en la práctica es "último toque".** Lo mismo podría pasar
  con el tracking corregido del reto: su texto habla de control, pero su GT sale de un flag de
  proveedor **[inferencia]**.
- **`databallpy`** (MIT, activo) **[fuente: código]**:
  - posesión por jugador al estilo de Vidal-Codina: zona de `pz_radius` y una ganancia válida si cambia
    la velocidad (`bv_threshold`) o la dirección (`ba_threshold`), con `min_frames_pz` = 0 por
    defecto. Un desvío cuenta como ganancia: es por toque;
  - `add_team_possession` cambia de equipo solo en un pase, regate o tiro con éxito
    (`is_successful`) del rival: se parece al control, pero fecha el cambio tarde;
  - lee los datos abiertos de la DFL (según el subagente).
- **ELASTIC** (Kim et al.; código MPL-2.0, datos CC BY 4.0) **[fuente: README]**:
  - en `benchmark/gt/` hay eventos corregidos (quitados falsos positivos, añadidos los que faltaban) de
    J03WMX, J03WN1 y J03WPY, con `frame_id` (cuándo ocurre) y `receive_frame_id` (cuándo se recibe);
  - cada momento es la mediana de tres anotadores.

  Es una referencia de tiempo humana, frame a frame, en 3 de nuestros 7 partidos.
- **Sin verificar aquí** (solo lo dice el subagente):
  - Link y Hoernig 2017: definen el control con una red bayesiana, sin código y sin umbrales
    publicados;
  - Vidal-Codina et al. 2022: sin código público;
  - PathCRF trae los eventos sincronizados con ELASTIC en los 7 partidos;
  - el resto de cifras de validación.
- **Conclusión del subagente:** ningún método abierto da una etiqueta de equipo por frame con criterio
  de control. Lo realista es combinar piezas (eventos DFL, tiempos de ELASTIC, detectores propios) con
  una regla de equipo propia y documentada.
- **Un hallazgo que no se ha mirado:** el subagente encontró el repositorio público de otro equipo de
  este mismo reto, con ficheros derivados del partido. No se ha abierto (regla nº 1 y juego limpio); lo
  decide Ismael.

## 11. Definiciones de los proveedores (subagente, verificadas aquí en la fuente)

- **Metrica, eventos** (`documentation/events-definitions.pdf` de `metrica-sports/sample-data`, leído
  aquí con `pdftotext`) **[fuente]**:
  - un jugador está en posesión desde que toca el balón (o decide dejarlo correr para controlarlo más
    allá);
  - la pierde cuando otro jugador se hace con ella, o cuando el balón sale;
  - no la pierde si el toque del rival no tiene un impacto significativo: el pase llega a su destino, o
    el que tenía el balón lo sigue controlando.

  Es **toque con filtro de impacto**.
- **StatsBomb** (especificación de open data v1.1, pág. 9, leída aquí) **[fuente]**:
  - una posesión nueva empieza cuando un equipo demuestra que ha establecido el control;
  - el equipo de la posesión aparece también en las acciones del rival dentro de ella (por ejemplo, un
    intento de entrada).

  Es **control establecido**.
- **DFL:** el catálogo de definiciones no es público; `PossessionChange` sigue **[sin verificar]**.
- Según el subagente, sin verificar aquí:
  - Opta y Wyscout van por control;
  - la FIFA (EFI) usa un tercer estado "en disputa";
  - Link y Hoernig separan "posesión" (al entrar el balón en el espacio de acción del jugador) de
    "control" (una capa más estricta).

**Tres lecturas, no dos [inferencia]:**

1. **Último toque:** el flag de la DFL.
2. **Toque con impacto significativo:** los eventos de Metrica, la organizadora.
   - Un desvío que no corta el pase, o un toque tras el que el poseedor sigue controlando, no cambia
     nada, y eso coincide con dos de los tres ejemplos de `CHALLENGE.md`.
   - Pero un toque que deja el balón suelto sí da la posesión al que toca. Eso crea rachas cortas
     X → y → X como las de 19 y 33 frames de la GT pública.
3. **Control establecido:** el texto de `CHALLENGE.md` y StatsBomb.
   - El tercer ejemplo del reto, un duelo aéreo ganado sin control posterior de ese equipo, es justo
     donde 2 y 3 se separan. Que el reto lo ponga como "no es cambio" apunta a 3.

## 12. Antes de medir cuánto se separan las lecturas 2 y 3 (fijado antes de calcular)

Sobre los casos de 2g (un toque del rival Y sin control, entre dos controles de X separados ≤ 5 s y
sin `D`; variante original), se cruza el jugador de los dos controles con los pases de los eventos:

- **mismo jugador:** el que controlaba antes vuelve a controlar;
- **pase que llega:** otro jugador de X controla después, y hay un pase de los eventos del primero al
  segundo, completado (`successfullyCompleted`, `Recipient` = el segundo), a ±3 s del toque. Es un
  desvío que no corta el pase;
- **balón suelto recuperado:** otro jugador de X controla después y no hay ese pase completado.

**Qué se da:**

- el reparto de los casos entre las tres clases;
- en cada clase, cuántos hacen que el flag pase a Y.

**Cómo se lee:**

- la lectura 3 no cambia en ninguna clase;
- la lectura 2 no cambia en "pase que llega" y sí en "balón suelto recuperado";
- en "mismo jugador" depende de si el poseedor lo siguió controlando.

Es descriptivo.

## 13. Cuánto se separan las lecturas 2 y 3 (`lecturas_toque.py`) [medido]

De los 203 casos de 2g:

| clase | casos | reparto | el flag pasa al rival |
|---|---|---|---|
| balón suelto recuperado por otro jugador de X | 142 | 70,0 % | 90,1 % |
| el mismo jugador de X vuelve a controlar | 45 | 22,2 % | 75,6 % |
| pase que llega a su destino pese al toque | 16 | 7,9 % | 68,8 % |

**Lectura:**

- **Las lecturas 2 y 3 se separan en la mayoría de los casos.** En el 70 % el toque deja el balón
  suelto y lo recupera un compañero:
  - con la lectura 2 (Metrica) es una posesión corta del rival;
  - con la 3 (reto, StatsBomb) no cambia nada.
- **El flag de la DFL se parece a la lectura 2** en esa clase (cambia en el 90 %). Se aparta de ella en
  los pases que llegan (cambia en el 69 %, y con la lectura 2 no debería).
- La clase se decide con los pases de los eventos, a ±3 s. Un pase completado no encontrado convierte
  un "pase que llega" en "balón suelto", así que el 7,9 % es un mínimo **[inferencia]**.
- **La GT pública tiene dos rachas cortas X → y → X** (19 y 33 frames). Encajan de forma natural con
  la lectura 2, y con la 3 solo si son controles muy breves. Con 17 posesiones no prueba nada
  **[inferencia]**. El vídeo lo decide.

## 14. Antes de repetir la comparación (fijado antes de calcular)

Tras la revisión, se repite `comparar_definiciones.py` con tres añadidos, sin cambiar nada más:

- **el bootstrap emparejado también contra C0-8,** no solo contra C0-12;
- **la referencia de duelos sin cambio, quitando los 80 `ballClaimed` con `PossessionChange` = false,**
  que contradicen la lectura simple del atributo. Se mira si se mantiene el orden;
- **la referencia de duelos con horizonte de 1 s y 3 s,** además de 2 s.

Además, se deja constancia de que la sección 9 (fecha del cambio) se escribió después de medir: es
descriptiva y no se fijó antes.

## 15. Resultado de la comparación repetida [medido]

- **Sin los 80 `ballClaimed` contradictorios,** la referencia de duelos sin cambio mantiene el orden:
  - el flag tal cual acierta el 44,8 %;
  - C0-8 el 69,9 %, C0-12 el 77,9 % y C0-20 el 82,2 %;
  - dos toques el 79,1 % y la unión el 76,1 %.

  Lo que justifica corregir no depende de esos casos.
- **Con horizonte de 1 s y de 3 s,** el flag tal cual sigue claramente peor en los duelos sin cambio
  (28,9 % y 54,8 %).
- **"C0-12 o dos toques" frente a C0-8** (intervalo del 95 %):
  - mejor en pases (+0,9 a +1,8) y en recuperaciones (+0,5 a +6,2);
  - empate en los duelos (con cambio, −0,9 a +6,1; sin cambio, −0,9 a +7,6);
  - mejor en los duelos sin cambio quitando los `ballClaimed` (+1,2 a +11,7).
- **Frente a C0-12, con horizonte de 3 s, queda peor en los duelos sin cambio** (−8,1 a −1,5). A 1 s y
  2 s es un empate.

  Es una candidata con un compromiso, no una ganadora.

## 16. Recuento del vídeo — ventana pública · Manuel Herrero · 12/11/2026 (corregido el 13/11/2026)

Revisión visual, por una sola persona, de los momentos de la sección 6 del resultado del experimento 1
en el vídeo táctico. Los momentos salen de la GT pública y se miraron con tiempos al segundo.

**Aquí van solo recuentos**, como pide la sección 6 ("las respuestas se apuntan como recuentos").

**Nota sobre la versión del 12/11:** traía dos tablas con el tiempo y la observación de cada momento, y
una conclusión que nombraba dos de esos tiempos.
- Se han quitado porque la regla pide solo recuentos y prohíbe etiquetar a mano momentos del partido.
- Los tiempos se pueden sacar de la GT pública oficial. Las observaciones de cada momento del vídeo, no.
- Están en el commit `c90449a`, que está en GitHub, en la PR #1. No desaparecen al hacer squash ni al
  borrar la rama, y las normas prohíben reescribir historia ya subida.
- Qué hacer antes de publicar el repo lo decide Ismael.

### Pregunta 1 — las 3 posesiones cortas entre dos del rival (19, 33 y 71 frames)

- **[medido]** En 1 de las 3 hay control.
- **[medido]** En 1 de las 3 no hay control: un toque de cabeza, el balón sale a un lado y lo recupera
  el rival. Aun así, la GT le da la posesión. Es el caso que `CHALLENGE.md` (línea 78) pone de ejemplo de
  lo que no cambia la posesión: un toque sin control.
- **[medido]** 1 de las 3 es discutible: tres toques seguidos de tres jugadores del mismo equipo sin
  dominarlo, y lo recupera el rival.
  - Con la candidata "C0-12 o dos toques" (sección 3 del resultado: dos toques seguidos del mismo equipo
    en 2 s o menos) podría contar como control.
  - **[inferencia]** La racha dura 19 frames (menos de 1 s), así que si los tres toques caen dentro de
    ella, caen en menos de 2 s. Que caigan dentro está **[sin verificar]**.

### Pregunta 2 — los 12 cambios directos H↔A

- **[medido]** Lo que se vio en cada cambio:

  | qué se vio | cambios |
  |---|---|
  | al menos un toque previo del equipo nuevo y control después | 6 |
  | uno sin control y uno discutible (las dos rachas sin control claro de la pregunta 1) | 2 |
  | dudoso: rebote y balón fuera, sin que conste control | 1 |
  | sin información sobre el primer toque | 3 |
- **Sin responder: en qué frame cambia la etiqueta,** en el primer toque o cuando ya hay control.
  - Los tiempos iban al segundo. Con un segundo de desfase el `spellF1` de una posesión baja a 0,65
    (`CLAUDE.md`, tabla de retrasos), así que esa resolución no basta.
  - Lo apuntado describe cómo fue cada jugada, no el frame del cambio.

### Conclusión (corregida el 13/11/2026)

**Qué se retira:** la conclusión del 12/11 decía que la GT usa control establecido (lectura 3) y que el
cambio se fecha unos fotogramas después del primer contacto. Se retira porque la pregunta 2 no se pudo
responder con la precisión necesaria y porque la pregunta 1 tiene un caso claro en contra.

**Qué queda:**

- **[inferencia]** En al menos una disputa, la GT da la posesión con un toque sin control.
  - Eso encaja con la lectura 1 (último toque) o con la 2 (toque con impacto), no con la 3 (control
    establecido).
  - Es 1 caso claro y 1 discutible, de un solo observador y con tiempos al segundo: una señal, no una
    medida firme.
- **[inferencia] La regla escrita antes de mirar** no prevé un resultado mixto como este (1 control,
  1 toque claro y 1 discutible).
  - La sección 6 del resultado dice: "**Si las rachas cortas son toques que dejan el balón suelto:** la
    GT sigue la lectura 2 (Metrica) o la 1, y hay que revisar la decisión del 12/11 con Ismael".
  - Se aplica la rama prudente: con al menos un caso claro de toque, toca revisar esa decisión con
    Ismael.
- **[inferencia]** Gana peso el riesgo apuntado en `docs/decisiones.md`: que la GT siga al toque.
- **Pendiente:** estas observaciones no separan la lectura 1 de la 2. Para separarlas habría que contar
  toques del rival que **no** cambian la etiqueta.

**Cómo responder la pregunta 2:** repetirla frame a frame, con el frame exacto de cada cambio sacado de la
GT pública. Antes de mirar, se fija aquí por escrito:
- qué cuenta como "primer toque" y qué como "control";
- la tolerancia en frames;
- que en el repo solo se apuntan recuentos, sin números de frame ni momentos.

## 17. Protocolo del recuento frame a frame — ventana pública · Antonio Azuero · 13/11/2026

**Borrador.** Se escribe antes de mirar, como pide la sección 16. Lo mira una persona en local; Claude no
ve el vídeo. Objetivo: saber qué lectura sigue la GT (1, 2 o 3 de la sección 3 del resultado) y en qué
momento fecha el cambio.

**Hipótesis de partida (Antonio, 13/11)** **[sin verificar]**: la posesión pasa al último equipo que
toca el balón **con intención** (pase, corte o despeje dirigido), con un margen de unos frames después del
toque. Los rebotes involuntarios no la cambian. Es la lectura 2. Salió de una primera mirada a velocidad
normal, sin ir frame a frame, así que no cuenta como medida: este recuento la pone a prueba. Lo que no
está claro son los rebotes: un despeje propio que rebota en un rival y vuelve a mi equipo.

### Qué se mira

- **Pregunta 2 (repetida):** los 12 cambios directos H↔A de la GT pública. Para cada uno, `F` es el
  primer frame con la etiqueta nueva, sacado de `evaluation/gt/BAR-ATH_possession_gt_public.csv`.
  - Se mira el vídeo táctico de `F − 50` a `F + 50` (2 s a cada lado), frame a frame, con un
    reproductor que enseñe el número de frame. El frame del vídeo es el de la entrega (`DATA.md`).
- **Pregunta 3 (nueva, separa la lectura 1 de la 2):** en los tramos `H` y `A` de la ventana, cada toque
  del rival que **no** termina con el rival controlando el balón (rebotes, desvíos, cortes que dejan el
  balón suelto). Para cada uno: ¿la etiqueta cambia, aunque sea unos frames, o no?

### Definiciones

- **Toque (`T`):** primer frame en que un jugador del equipo nuevo toca el balón (pie, cabeza o cuerpo)
  y cambia su dirección o su velocidad, después del último toque del equipo anterior.
- **Intención:** cada toque se clasifica antes de mirar la etiqueta de la GT.
  - **Intencionado:** el jugador va a por el balón y lo dirige: pase, corte, intercepción o despeje.
  - **No intencionado:** el balón le da sin que lo busque: rebote en el cuerpo, desvío de un tiro o de un
    despeje.
  - **Dudoso:** no se puede decidir a simple vista.
- **Control (`C`):** primer frame de la segunda acción del equipo nuevo con el balón: segundo toque del
  mismo jugador, conducción o pase a un compañero que le llega.
- **Tolerancia:** ±5 frames (0,2 s). Con 3 frames de desfase el `spellF1` de una posesión es 0,98 y con
  8, 0,89 (`CLAUDE.md`), así que ±5 separa bien "en el toque" de "en el control".

### Cómo se clasifica cada cambio (pregunta 2)

Cada cambio se clasifica dos veces.

**Cuándo cambia la etiqueta respecto al toque** (`Δ = F − T`):

| clase | condición |
|---|---|
| antes del toque | `Δ < −5` |
| en el toque | `−5 ≤ Δ ≤ 5` |
| poco después (margen) | `5 < Δ ≤ 25` (hasta 1 s) |
| en el control | `Δ > 25` y `\|F − C\| ≤ 5` |
| más tarde | `Δ > 25` y lejos del control |
| sin información | `T` no se ve (oclusión, cámara) |

Si `C − T ≤ 10`, no se puede separar toque de control: el caso se clasifica igual, pero se apunta aparte
cuántos hay.

**De qué tipo es el toque `T`:** intencionado, no intencionado o dudoso.

### Cómo se clasifica cada toque del rival de la pregunta 3

| tipo de toque del rival | la etiqueta cambia | no cambia |
|---|---|---|
| intencionado (corte o despeje que deja el balón suelto) | | |
| no intencionado (rebote, desvío) | | |
| dudoso | | |

El caso de los rebotes: un despeje propio que rebota en un rival y vuelve a mi equipo es un toque **no
intencionado** del rival.

### Cómo se leen los resultados (fijado antes de mirar)

- **Lectura 1 (último toque, como la DFL):** los rebotes no intencionados del rival también cambian la
  etiqueta, aunque sea unos frames. Los cambios caen "en el toque".
- **Lectura 2 (toque con intención, la hipótesis de partida):** los toques intencionados del rival cambian
  la etiqueta y los no intencionados casi nunca. Los cambios caen "en el toque" o "poco después".
- **Lectura 3 (control establecido):** los cambios caen sobre todo "en el control", y los toques del
  rival sin control no cambian la etiqueta, sean intencionados o no.
- **Mezcla, o mayoría "sin información" o "dudoso":** no se decide con el vídeo. Se lleva a Ismael con la
  propuesta de preguntar a la organización.
- **El margen:** aunque muchos cambios caigan "poco después", de aquí no sale un número de frames para el
  pipeline. Solo sale la convención de que el cambio se fecha después del toque. El valor del margen se
  fija con la DFL, nunca con la ventana pública.

### Qué se apunta

- En el repo, **solo los recuentos** de cada clase. Ni frames, ni tiempos, ni descripciones de jugadas.
- Las notas de trabajo (frame a frame) se toman fuera del repo, no se pegan a Claude y se borran al
  terminar el recuento.
- **No sale** ningún desfase en frames para usar en el pipeline: solo la convención (qué lectura y si el
  cambio se fecha en el toque o en el control).

