# Investigación de métodos: posesión frame a frame

> **Estado:** informe de investigación del 11/11/2026, ampliado el mismo día con la búsqueda de datos del
> Barça como local (sección 8.4). No hay código de pipeline todavía. Los pasos que faltan están en
> [`validation/PASOS.md`](../validation/PASOS.md) y los resultados se apuntan en
> [`validation/resultados/`](../validation/resultados/README.md).
>
> **Qué es:** análisis de la métrica, verificación de las referencias propuestas, alternativas por etapa,
> tres pipelines completos y un protocolo para decidir con datos de otros partidos.
>
> **Regla nº 1 respetada:** para escribirlo no se ha abierto ningún dato del partido. Las cifras salen de
> la documentación oficial, del scorer oficial sobre los baselines públicos, de la GT pública de 5
> minutos (solo para entender la métrica, nunca para elegir parámetros) y de una GT sintética.
>
> **Scripts de las cifras [medido]:** `validation/scripts/sensibilidad_metrica.py` (GT sintética) y
> `validation/scripts/perfil_etiquetas.py` (GT pública), más el scorer oficial para los baselines. Sus
> salidas están en `validation/resultados/2026-11-11_*.md`.
>
> **Cómo leer las etiquetas de evidencia:** **[doc]** está en la documentación o el código oficial;
> **[medido]** lo he calculado yo y se puede repetir; **[fuente]** lo dice una fuente externa enlazada en
> la sección 9; **[inferencia]** es una deducción mía sin confirmar; **[sin verificar]** no he podido
> comprobarlo.

---

## 0. Recomendación

**Construir un único pipeline con piezas intercambiables y un solo decodificador para todos los frames.
Empezar con reglas (pipeline A) y sustituir la emisión por un modelo entrenado con los 7 partidos
abiertos de la Bundesliga (pipeline B) solo si gana en la validación externa.** El detalle está en la
sección 4.

### Por qué

- **La nota la deciden el decodificador y el balón muerto, no el reparto entre nivel 1 y nivel 2.** En el
  partido completo, cambiar solo la ventana de suavizado del baseline lleva el `spellF1` de 0,05 a 0,24
  mientras el `macroF1` apenas se mueve (0,65 a 0,67). **[doc]** Inventar cambios de posesión es el error
  más caro de la métrica (sección 1.3). Como ilustración, en la ventana pública solo 2 de las 29
  transiciones del baseline caen cerca de una real y casi nunca acierta el balón muerto (sección 1.6).
- **Hay un dataset abierto con el mismo tipo de etiqueta que la GT.** El de la Bundesliga trae en cada
  frame el equipo poseedor y si el balón está activo, con licencia CC-BY 4.0. Es mejor punto de partida
  para validar y entrenar que derivar etiquetas de los eventos de Metrica (sección 5). Del Barça no hay
  nada equivalente: sí hay eventos de 264 partidos suyos en el Camp Nou, que sirven de apoyo para lo que
  depende de la liga y del equipo (sección 8.4).
- **El nivel 2 de la propuesta original no cabe en seis días.** Ball Radar no tiene pesos ni licencia,
  el balón mide unos 4 píxeles en el vídeo táctico y MS-TCN++ necesita partidos etiquetados y tiempo
  (secciones 2 y 8).
- **El plan decide con medidas.** Cada elección entre métodos pasa por el protocolo de la sección 5, con
  datos de otros partidos y una regla escrita de cuándo una diferencia es real.

### Qué cambia respecto al esquema original

| pieza propuesta | veredicto | qué hacer |
|---|---|---|
| Savitzky-Golay + Kalman RTS sobre el balón | cambiar | filtro de validez e interpolación de huecos cortos; suavizado solo para distancias; sin Kalman |
| detección de cortes del broadcast con OpenCV | quitar | la columna `valid` de su homografía ya lo marca, y el broadcast queda fuera del plazo |
| router 60 % / 40 % por balón visible | cambiar | clases de observabilidad que fijan cuánto pesa cada evidencia; un solo decodificador (sección 6) |
| nivel 1: zonas de posesión y de duelo de FIFA | mantener | candidato N3 y variables del modelo aprendido |
| nivel 1: pitch control de Spearman | quitar | sin evidencia de que ayude aquí |
| nivel 1: LightGBM o CatBoost multiescala | mantener | candidato N5, entrenado con la Bundesliga degradada; uno de los dos, no ambos |
| nivel 2: Ball Radar | fuera del plazo | sustituir por arrastre en el decodificador y reglas de puente |
| nivel 2: ROI + YOLOv8-p2 sobre el vídeo | fuera del plazo | candidato para la fase siguiente |
| nivel 2: MS-TCN++ | fuera del plazo | sus lecciones entran por el post-proceso |
| decodificador: CRF con máscara y Viterbi | mantener | Viterbi con coste de cambio y transiciones prohibidas |
| poda de micro-posesiones de menos de 18 frames | mantener, con cambio | el umbral sale de los datos abiertos; la GT tiene posesiones así de cortas |
| ajuste de los límites a los saques | mantener | también a los toques detectados |

Además, **la `X` solo fuera de los tramos evaluados** (sección 1.4).

### Qué no es alcanzable

Un resultado casi perfecto frame a frame no es realista con este tracking (sección 7). En torno a un
tercio de las posesiones reales dura menos de 3 segundos (lectura de la tabla oficial, sección 1.2) y
el balón falta sobre todo cuando cambia la posesión. No doy una cifra de techo sin medirla: la sección 7.3 propone las dos medidas que la fijan.
Batir el baseline con margen sí es probable.

### Lo que no sé todavía

Las cuatro dudas que más pesan:

- **Cómo se producen los flags de posesión del proveedor** y, por tanto, si las fronteras de la GT
  llevan un retraso humano.
- **Si el flag de la Bundesliga se comporta como el del reto.** Lo comprueba el experimento 0.
- **Si la degradación imitará bien al ATD.** Depende del perfil de agregados que ejecute una persona.
- **Cuántos cambios de posesión ocurren con el balón oculto.** Lo dice el recuento de la sección 6.4.

Además hay una **consulta abierta con la organización** (D21): si podemos usar la tabla de retrasos de
`EVALUATION.md` para algo más que leer la métrica. Ismael decidió el 11/11 preguntarlo por email y no
decidir nada con ella mientras no contesten (sección 1.2).

La lista completa (D1…D21), con cómo se resuelve cada una y en qué paso, está al final de
[`validation/PASOS.md`](../validation/PASOS.md).

### Siguientes pasos

- **El experimento 0 lo hace el equipo** siguiendo [`validation/PASOS.md`](../validation/PASOS.md): paso 2
  con la Bundesliga, paso 3 con los eventos del Barça como local y paso 5 (perfil del ATD), que ejecuta
  una persona en local.
- **Los resultados se apuntan en `validation/resultados/`,** con una plantilla para el experimento 0.
- **Por decisión de Ismael (11/11), este plan manda** sobre lo que digan `CLAUDE.md` y
  `docs/GUIA_EQUIPO.md` sobre la validación externa (Metrica como dataset principal) y la política de `X`
  (en las oclusiones largas). Se escribieron antes de este paso.

---

## 1. Lectura del problema desde la métrica

### 1.1 Qué puntúa `spellF1`

- **La unidad es la posesión, no el frame.** Una posesión es una racha máxima de `H` o de `A` dentro de
  una parte. Los tramos `D` no son posesiones, pero las cortan: `H H D D H H` son dos. **[doc]**
- **Emparejamiento uno a uno.** Cada posesión predicha se empareja con una real del mismo equipo por IoU
  temporal, de mayor a menor IoU. Se calcula el F1 con umbrales 0,3 / 0,4 / 0,5 / 0,6 / 0,7 y se
  promedia. **[doc]**
- **No hay crédito parcial.** Una pareja que no llega al umbral cuenta dos veces: la posesión real queda
  sin detectar y la predicha es un falso positivo.
- **Todas las posesiones pesan lo mismo.** Una de 1 segundo cuenta igual que una de 40.
- **Las dos partes son independientes.** Ninguna posesión cruza el descanso. **[doc]**
- **La `X` se rellena antes de emparejar** con la última etiqueta de esa parte. **[doc]**

### 1.2 Lo que la tabla oficial de retrasos dice sobre la GT privada

`EVALUATION.md` publica cuánto baja el `spellF1` si todas las etiquetas llegan tarde:

| retraso uniforme | spellF1 **[doc]** |
|---|---|
| 1 frame | 1,0000 |
| 3 frames | 0,9818 |
| 8 frames | 0,8933 |
| 25 frames (1 s) | 0,6539 |

La documentación no dice sobre qué GT está calculada. No es la ventana pública, que da 1,00 / 0,95 /
0,78 para los mismos retrasos **[medido]**, así que doy por hecho que es el partido completo
**[inferencia]**. Si es así, la tabla es una función de la GT privada y de ella se puede deducir cómo son
las posesiones reales. Con un retraso de `d` frames, una posesión de longitud `L` sigue emparejada con umbral
`t` solo si `(L − d) / (L + d) ≥ t`, es decir, si `L ≥ d·(1 + t) / (1 − t)`:

| retraso | longitud mínima para sobrevivir con umbral 0,3 / 0,4 / 0,5 / 0,6 / 0,7 (frames) |
|---|---|
| 3 | 6 / 7 / 9 / 12 / 17 |
| 8 | 15 / 19 / 24 / 32 / 46 |
| 25 | 47 / 59 / 75 / 100 / 142 |

Que con 25 frames de retraso queden 0,65 significa que, de media sobre los cinco umbrales, **un 35 % de
las posesiones reales dura menos que esas longitudes** (entre 1,9 y 5,7 segundos).

Ajustando una distribución lognormal de duraciones a los tres valores publicados **[medido, inferencia]**:

| | valor ajustado |
|---|---|
| mediana de una posesión | ≈ 5,3 s |
| posesiones de menos de 0,7 s (18 frames) | ≈ 6 % |
| posesiones de menos de 1 s | ≈ 9 % |
| posesiones de menos de 2 s | ≈ 22 % |
| posesiones de menos de 3 s | ≈ 33 % |
| posesiones de menos de 5 s | ≈ 48 % |

El ajuste reproduce la tabla oficial: 0,977 / 0,896 / 0,654 con la fórmula y 0,979 / 0,898 / 0,651
simulando, frente a 0,982 / 0,893 / 0,654. La forma
lognormal es una suposición; lo que es robusto es el orden de magnitud.

> **Cómo se usa esta sección: solo como lectura de la métrica, y todo lo que deduce es inferencia.**
> `OVERVIEW.md` explica que la
> organización no publica estadísticas de la GT completa (número de posesiones, duración media,
> reparto), porque son justo lo que permitiría ajustar contra ella. `EVALUATION.md` lo dice igual: los
> recuentos y duraciones "would hand you the ground truth's own counts to tune against". Y `RULES.md` §2
> prohíbe usar la GT completa "or anything derived from it". La tabla de retrasos sí está publicada, pero
> lo que se deduce de ella son estadísticas de ese tipo. Por eso, **ningún parámetro
> (duración mínima, poda, coste de cambio) ni la elección de dataset se decide con estas cifras ni con
> la huella de retrasos**. Ismael decidió el 11/11 preguntarlo a la organización por email y no decidir
> nada con ello hasta que contesten (duda D21 de [`validation/PASOS.md`](../validation/PASOS.md)).

**Lo que implica:**

- **Las posesiones cortas son muchas y valen lo mismo que las largas.** Cualquier duración mínima de 2
  segundos o más descarta de entrada una de cada cinco posesiones reales. El voto por mayoría de ±2 s del
  baseline hace exactamente eso.
- **La ventana pública no es representativa.** En sus 17 posesiones la mediana es 7,6 s y el mismo
  retraso de 25 frames da 0,78 en vez de 0,65 **[medido]**. El partido completo tiene más posesiones
  cortas que los 5 minutos públicos.
- **La GT contiene micro-posesiones reales.** En la ventana pública hay una de 19 frames y otra de 33
  **[medido]**. Es coherente con que "nada se suaviza". Esto solo describe qué significan las etiquetas;
  ningún umbral debe salir de aquí.
- **La poda de "<18 frames" de la propuesta original** quitaría en torno al 6 % de las posesiones reales
  si el ajuste es correcto. Puede compensar si casi todo lo que se poda es ruido, pero el umbral tiene
  que salir de los datos abiertos (sección 5), no de esta estimación ni de la ventana pública.

### 1.3 Cuánto cuesta cada tipo de error

He generado una GT sintética con la distribución de duraciones anterior y le he aplicado un error cada
vez, puntuando con `evaluation/possession_metrics.py` **[medido]**. Supuestos propios: el 40 % de las
posesiones termina en balón muerto y una parada dura unos 12 s de mediana. Sirve para **ordenar** los
errores por coste, no para predecir nuestra nota ni para fijar parámetros. Como la GT sintética se
calibra con la tabla oficial, estas conclusiones quedan en el mismo estado que D21: son lectura de la
métrica, no base para elegir parámetros.

| error aplicado a un etiquetado por lo demás perfecto | spellF1 |
|---|---|
| desfase aleatorio de cada frontera, σ = 6 / 12 / 25 frames | 0,95 / 0,88 / 0,75 |
| el mismo desfase solo en los cambios `H`↔`A`, σ = 12 / 25 | 0,93 / 0,85 |
| el mismo desfase solo en las fronteras con `D`, σ = 12 / 25 / 50 | 0,96 / 0,90 / 0,83 |
| no detectar ninguna posesión de menos de 1 / 2 / 3 / 5 s | 0,93 / 0,83 / 0,74 / 0,61 |
| cambios de posesión inventados: 0,5 / 1 / 2 / 4 / 8 por minuto de juego | 0,91 / 0,84 / 0,71 / 0,54 / 0,35 |
| paradas no detectadas: 10 / 25 / 50 / 100 % | 0,97 / 0,91 / 0,82 / 0,63 |
| tramos `D` inventados de 1–4 s: 0,5 / 1 / 2 por minuto de juego | 0,94 / 0,89 / 0,79 |

**Lectura:**

1. **El baseline (0,24) puntúa como un etiquetado perfecto con más de 8 cambios inventados por minuto.**
   **[inferencia]**: es una analogía con la escala sintética, no una medida del baseline.
   Su problema son las transiciones falsas, no los frames mal etiquetados.
2. **Inventar cambios es el error más caro por unidad:** uno por minuto de juego cuesta 0,16.
3. **No ver las posesiones cortas es el segundo:** perder todas las de menos de 3 s cuesta 0,26. Por eso
   "suavizar más" no es la solución: cambia un error por el otro.
4. **El coste de los dos errores es parecido por caso.** Un cambio inventado en mitad de una posesión
   real cuesta hasta una posesión perdida y tres falsos positivos. Una posesión corta real no detectada
   entre dos del mismo equipo cuesta dos o tres posesiones perdidas. La decisión correcta es la de un
   modelo calibrado (cambiar cuando la probabilidad supera aproximadamente 0,5), no un sesgo fijo hacia
   suavizar. Es un razonamiento sobre cómo cuenta la métrica, no una medida.
5. **La precisión temporal importa menos que acertar el número de posesiones**, pero no es gratis: medio
   segundo de desfase típico (σ = 12) cuesta 0,12.
6. **El balón muerto pesa menos por caso, pero hay muchos casos.** No detectar ninguna parada cuesta 0,37.

### 1.4 La `X` no aporta nada en los frames evaluados

- Para `spellF1`, una `X` es "repite mi etiqueta anterior". Para `macroF1` es un fallo. **[doc]**
- Escribir directamente la etiqueta anterior da **el mismo `spellF1`** y un `macroF1` igual o mejor. La
  `X` está dominada en cualquier frame evaluado.
- Además, un decodificador que trabaja con el partido entero ve los dos lados del hueco y puede colocar
  el cambio en el punto más probable, cosa que "repetir la anterior" no hace.

**Recomendación:** `X` solo fuera de los tramos evaluados. Esto corrige el punto 5 de la estrategia de
`CLAUDE.md` ("poner `X` en las oclusiones largas"): es inocuo para el ranking, pero resta en el
desempate.

### 1.5 Cómo se generó la GT y qué implica

**Lo documentado [doc]:** la GT es mecánica. Hay `D` donde el tracking corregido marca el balón muerto y,
en el resto, el equipo que ese tracking nombra como poseedor. No se suaviza. El tracking nombra un equipo
incluso con el balón fuera de juego.

**Lo que deduzco [inferencia]:** esa pareja "equipo poseedor + vivo/muerto por frame" es el formato del
tracking óptico de estadio tipo TRACAB, no una derivación a partir de eventos.

- El lector de TRACAB de kloppy 3.18 exige en cada frame exactamente `H` o `A` como equipo poseedor y
  `Alive` o `Dead` como estado. Son las mismas letras de este reto. **[medido en el código de kloppy]**
- El tracking oficial de LaLiga (Mediacoach) usa TRACAB. **[fuente]**

**Qué implica, sea o no TRACAB:**

- **La etiqueta es un flag de proveedor, con sus propias convenciones.** Cuándo exactamente cambia de
  equipo y cuándo pasa a muerto no se deduce de la definición de `CHALLENGE.md`: se aprende de datos que
  tengan el mismo tipo de flag.
- **Existe un dataset abierto con ese flag por frame:** el de la Bundesliga de Bassek et al. (7 partidos,
  `BallPossession` y `BallStatus` en cada frame). Es un proxy más directo de la GT que derivar etiquetas a
  partir de los eventos de Metrica. Los detalles están en las secciones 5 y 8.
- **No he podido verificar cómo se producen esos flags** (operador humano en directo, algoritmo o
  mezcla). **[sin verificar]** Si interviene una persona, las fronteras de la GT llevan un retraso humano
  que ningún método puede adivinar exactamente. El "experimento 0" de la sección 5 lo mide en los datos
  abiertos.

### 1.6 Dónde pierde el baseline

Salida del scorer oficial para `baseline_smooth50` en la ventana pública **[medido]**. Son 17 posesiones:
sirve para ver el tipo de fallo, no para decidir nada.

| qué | valor |
|---|---|
| transiciones predichas / reales | 29 / 20 |
| transiciones acertadas a ±1 s | **2 de 20** |
| posesiones predichas / reales | 26 / 17 |
| posesiones emparejadas con IoU 0,5 | 7 |
| recall de `D` | **0,21** |
| acierto de equipo con balón vivo (sin suavizar / suavizado) | 0,78 / 0,86 |
| frames `D` reales en los que el baseline **sin suavizar** dice `H` o `A`, es decir, con balón localizado | 975 de 1.469 (66 %) |

**Lectura:**

- **Casi ninguna transición del baseline cae donde hay una real.** Acierta el equipo en la mayoría de
  frames, pero cambia en momentos equivocados.
- **El balón se ve durante la mayor parte del tiempo muerto.** El baseline sin suavizar solo escribe `H` o
  `A` donde hay balón localizado, y lo hace en dos de cada tres frames `D` reales. "No hay balón → `D`"
  falla en los dos sentidos: marca `D` en juego vivo cuando el balón se pierde y marca posesión cuando el
  balón está parado esperando un saque.
- **"Balón visible" no es "frame fácil".** Con el balón localizado, el jugador más cercano es del equipo
  equivocado en el 22 % de los frames vivos.

**El margen frente a 0,2433 está, por este orden, en:**

1. dejar de inventar cambios de posesión;
2. modelar el balón muerto con señales propias (posición, saques, jugadores parados) en vez de con la
   ausencia de balón;
3. colocar cada cambio real en su sitio, incluidos los que ocurren mientras el balón no se ve;
4. no borrar las posesiones cortas reales.

---

## 2. Alternativas por etapa

En todas las tablas, "byte a byte" indica si la salida se puede regenerar idéntica en otra máquina. El
coste es en días de una persona. Las licencias y la existencia de código y pesos están verificadas en la
sección 8.

### 2.1 Limpieza del balón

| id | alternativa | cómo funciona | qué necesita | coste | riesgo | licencia | byte a byte |
|---|---|---|---|---|---|---|---|
| A1 | filtro de validez | descarta saltos físicamente imposibles y detecciones aisladas; marca el balón fuera de [0, 1] | nada | 0,5 | bajo | propio | sí |
| A2 | interpolar huecos cortos | recta entre la última y la siguiente posición, solo si el hueco es corto y el balón reaparece donde se le espera | longitud máxima medida en datos abiertos | 0,5 | medio | propio | sí |
| A3 | Savitzky-Golay | polinomio local para suavizar y derivar | nada | horas | medio | scipy, BSD | sí |
| A4 | Kalman + suavizador RTS | modelo de velocidad constante que rellena huecos y da incertidumbre | ajustar los ruidos | 1 | medio-alto | propio | sí |
| A5 | imputación aprendida (Ball Radar, TranSPORTmer) | una red predice el balón a partir de los jugadores | 22 trayectorias completas, entrenar, GPU | más de una semana | alto | sin licencia o sin código | dudoso |
| A6 | balón del ATD del broadcast | usar el balón del otro tracking cuando el táctico no lo ve | sincronizar los dos timelines | 2–4 | alto | propio | sí, si la sincronización es determinista |

**Lectura:**

- **Suavizar el balón borra justo la señal que buscamos.** Un toque se ve como un pico de aceleración o
  un cambio de dirección. Link y Hoernig definen el golpeo como un máximo local de aceleración del balón
  de al menos 4 m/s². **[fuente]**
- **Dos series de balón:** una ligeramente suavizada para distancias y otra sin suavizar para detectar
  toques.
- **Vidal-Codina et al. usan Savitzky-Golay** (orden 2, 7 frames) sobre un balón limpio. **[fuente]**
  Para distancias vale; para detectar toques, no.
- **Kalman + RTS no compensa de entrada.** El modelo de velocidad constante falla en cada golpeo, y hay
  un trabajo de 2025 que documenta su deriva con balones que botan (en otro deporte). **[fuente]** La
  incertidumbre en los huecos ya la gestiona el decodificador.
- **Nunca interpolar a través de un hueco si el balón reaparece junto a un jugador del otro equipo.** Ahí
  hay un posible cambio de posesión y decide el decodificador.
- **No he encontrado una longitud máxima estándar de hueco ni un tope estándar de velocidad del balón.**
  **[sin verificar]** Los golpeos máximos medidos rondan 18–35 m/s. **[fuente]** La longitud de hueco se
  mide en datos abiertos: se oculta balón conocido y se mira el error.

**Elección:** A1 + A2. A3 solo para distancias. A4, A5 y A6 fuera del plazo o sin ventaja clara.

### 2.2 Balón muerto (`D`)

| id | alternativa | cómo funciona | qué necesita | coste | riesgo | byte a byte |
|---|---|---|---|---|---|---|
| B1 | reglas geométricas | empieza `D` cuando el balón sale de los límites o queda parado en posición de saque; termina cuando el balón arranca | balón visible en esos momentos | 1 | medio | sí |
| B2 | `SET PIECES` del Smart Tagging | cada reinicio etiquetado marca el final de un `D` | nada | 0,5 | medio: la lista es incompleta | sí |
| B3 | clasificador con solo jugadores | posición, velocidad y aceleración de los jugadores en ventanas pasadas y futuras | entrenar en la Bundesliga degradada | 1–1,5 | medio: fronteras imprecisas | sí, con versiones fijadas |
| B4 | emisión conjunta de tres clases | el mismo modelo de nivel 1 da la probabilidad de `H`, `A` y `D` | entrenar | incluido en N5 | medio | sí, con versiones fijadas |
| B5 | inicio de la 2ª parte | `Kick Off (Start)` del Smart Tagging, o todos los jugadores en su campo y el balón en el centro | nada | horas | bajo | sí |
| B6 | silbato en el audio | detectar el silbato del árbitro | audio en el vídeo | desconocido | alto: no hay nada reciente publicado | no evaluado |

**Licencias:** todo es código propio. B3 y B4 usan además LightGBM (MIT).

**Lectura:**

- **Los reinicios etiquetados probablemente son menos de la mitad.** Un estudio de la Bundesliga cuenta
  unas 108 interrupciones por partido: 40 saques de banda, 33 faltas, 17 saques de puerta y 10 córners.
  **[fuente]** El Smart Tagging de este partido trae 59, de ellas 5 faltas. **[doc]** Es otra liga y otra
  temporada, así que es un aviso y no una medida.
- **El tiempo muerto es mucho.** El tiempo efectivo de juego ronda el 59–61 % (59,3 % en LaLiga según
  CIES, con datos de 2019 a 2021, antes de la temporada del reto).
  **[fuente]** Cabe esperar que en torno al 40 % de los frames evaluados sean `D`. La ventana pública
  tiene un 20 %: tampoco en esto es representativa.
- **Solo con los jugadores se acierta el estado, pero no el momento.** Lang et al. logran un 92 % de
  acierto por frame sin usar el balón, con un error medio de 1,7 s en cada frontera. **[fuente]** Un
  segundo de retraso cuesta mucho (sección 1.3).
- **Las paradas duran mucho más que una oclusión:** de media 13 s un saque de banda, 23 s un saque de
  puerta y 27 s una falta o un córner. **[fuente]** Esas medias solo cuentan paradas de al menos 2 s que
  su modelo detectó bien, así que sobrestiman algo. Una duración mínima para `D` es razonable; su valor
  sale de los datos abiertos.

**Elección:** B1 para el momento, B2 como evidencia adicional, B5 para la 2ª parte, y B3 o B4 para
confirmar y cubrir los casos en que el balón no se ve.

### 2.3 Candidato de posesión con balón visible (nivel 1)

| id | alternativa | cómo funciona | qué necesita | coste | riesgo | licencia | byte a byte |
|---|---|---|---|---|---|---|---|
| N1 | jugador más cercano | el equipo del jugador más próximo al balón | nada | hecho | alto: 22 % de error con balón visible | oficial | sí |
| N2 | más cercano con radio y margen | solo opina si un jugador está a menos de `R` y el rival claramente más lejos | radios de datos abiertos | 0,5 | medio | propio | sí |
| N3 | zonas de FIFA (Vidal-Codina et al.) | zona de posesión de 0,5–1 m alrededor de cada jugador; zona de duelo de 1 m alrededor del balón; solo hay ganancia si el balón cambia de dirección o de velocidad | balón limpio; umbrales del anexo del artículo | 1 | medio | artículo CC BY; sin código oficial | sí |
| N4 | toques con confirmación | detecta toques por aceleración o giro del balón; el cambio de posesión exige un segundo toque o balón retenido, y se fecha en el primer toque | umbrales de datos abiertos | 1 | medio | propio | sí |
| N5 | gradient boosting multiescala | variables sin identidad en ventanas de varias longitudes; devuelve probabilidades | entrenar en la Bundesliga degradada | 1,5–2 | medio: cambio de dominio | LightGBM, MIT | sí, con modelo commiteado y versiones fijadas |
| N6 | pitch control (Spearman) | probabilidad de que cada equipo llegue antes a un punto | velocidades e identidades estables | 1–2 | alto | implementación MIT | sí |

**Lectura:**

- **N3 no resuelve por sí solo este reto.** Es posesión por jugador; la posesión de equipo queda como
  trabajo futuro en el artículo. No detecta el balón muerto: lo toma del proveedor o lo deduce de que
  falta el balón, que es justo la suposición que aquí falla. **[fuente]**
- **La idea que sí vale de N3 es la validación de la ganancia:** el balón en la zona de un jugador solo
  cuenta si cambia de dirección o de velocidad. Es la traducción directa de "un toque sin control no
  cambia la posesión". `databallpy` la implementa con licencia MIT y otros valores por defecto (radio
  1,5 m, 5 m/s y 10°). **[fuente]**
- **N4 implementa la regla del reto de forma explícita.** Link y Hoernig definen la posesión de equipo
  igual: solo termina cuando empieza la posesión de un rival. **[fuente]**
- **El cuello de botella publicado es fechar los eventos, no clasificarlos,** y los detectores por reglas
  bajan de 0,87 a 0,70 de F1 al cambiar de datos. **[fuente]** Es un argumento para validar con la
  degradación y no fiarse de umbrales de artículos.
- **N6 no merece una implementación propia.** No he encontrado evidencia de que el pitch control en la
  posición del balón indique quién lo tiene. **[sin verificar]** Lo aprovechable es su idea de que
  controlar lleva tiempo, que ya está en N4.
- **LightGBM o CatBoost: uno, no los dos.** La diferencia esperable entre ellos está por debajo del
  ruido. LightGBM trata los valores ausentes de forma nativa, que aquí es lo habitual.

**Elección:** comparar N2, N3 y N4 contra N1 con el protocolo de la sección 5 y, en paralelo, construir
N5 con las señales de N3 y N4 como variables.

### 2.4 Frames sin balón (nivel 2)

| id | alternativa | cómo funciona | qué necesita | coste | riesgo | byte a byte |
|---|---|---|---|---|---|---|
| L1 | arrastre en el decodificador | sin evidencia, el estado se mantiene; el cambio se coloca donde lo pide la evidencia de los dos lados | nada | incluido | bajo | sí |
| L2 | reglas de puente | si el balón reaparece con el mismo equipo no hay cambio; si reaparece controlado por el rival, se sitúa el cambio dentro del hueco con un desfase medido | desfase de datos abiertos | 0,5–1 | medio | sí |
| L3 | clasificador con solo jugadores | forma colectiva: centroides y su velocidad, anchura, profundidad, altura de las líneas | entrenar en la Bundesliga degradada | 1 | medio: señal débil | sí, con versiones fijadas |
| L4 | autoentrenamiento en el propio partido | las anclas de control claro hacen de pseudoetiquetas para entrenar L3 con el tracking de este partido | nada externo | 1–1,5 | medio: las anclas no se parecen a los huecos | sí, con semillas fijas |
| L5 | equipo de la fase del Smart Tagging | la fase táctica vigente como indicio del equipo con balón | calibrar su fiabilidad contra las anclas | 0,5 | medio: fases, no posesiones | sí |
| L6 | Ball Radar, TranSPORTmer, PathCRF | redes que infieren balón o posesión solo con jugadores | trayectorias completas y continuas; entrenar | más de una semana | alto | dudoso |
| L7 | volver a detectar el balón en el vídeo | detector de objetos pequeños sobre el vídeo táctico | GPU; el balón mide unos 4 px | 2–4 | alto | dudoso |
| L8 | balón del ATD del broadcast | igual que A6 | sincronización | 2–4 | alto | sí, si es determinista |

**Licencias:** L1, L2, L5 y L8 son código propio. L3 y L4 usan LightGBM (MIT). En L6, PathCRF es
MPL-2.0, Ball Radar no tiene licencia y TranSPORTmer no tiene código público. En L7, Ultralytics es
AGPL-3.0 y FootAndBall y WASB son MIT.

**Lectura:**

- **Los resultados publicados de "posesión sin balón" son del 78–90 % de acierto, en condiciones más
  fáciles que las nuestras:** solo juego vivo, tracking limpio e identidades. **[fuente]** Ball Radar da
  85,9 % de acierto de equipo y un error de balón de 3,7 m, demasiado grueso para elegir poseedor por
  cercanía.
- **Las señales colectivas valen como indicio débil para rellenar, no para detectar cambios.** No he
  encontrado ningún trabajo que mida el acierto de equipo solo con forma colectiva. **[sin verificar]**
- **L4 está permitido por las reglas:** son pseudoetiquetas producidas por un algoritmo, sin que nadie
  decida ninguna. **[doc]** Su ventaja es que aprende del ruido real de este tracking. Su límite es que
  no se puede validar contra la GT; se valida el procedimiento entero en los datos abiertos degradados.
- **L5 no se puede validar fuera,** porque los datos abiertos no traen Smart Tagging. Por eso su
  fiabilidad se mide contra las anclas del propio partido y entra con poco peso.
- **L6, L7 y L8 no caben** (secciones 2.6 y 8).

**Elección:** L1 siempre. L2 después. L3, L4 y L5 solo si el recuento de la sección 6.4 muestra que hay
suficientes cambios de posesión dentro de huecos largos como para justificarlos.

### 2.5 Modelo temporal

| id | alternativa | cómo funciona | qué necesita | coste | riesgo | licencia | byte a byte |
|---|---|---|---|---|---|---|---|
| T1 | voto por mayoría | la etiqueta más frecuente en una ventana | nada | hecho | alto | oficial | sí |
| T2 | histéresis y limpieza | umbrales distintos para entrar y salir; rellenar huecos cortos; borrar islas cortas | umbrales de datos abiertos | 0,5 | bajo | propio | sí |
| T3 | Viterbi con coste de cambio | camino más probable sobre {`H`, `A`, `D`} con una penalización por cada cambio | emisiones y dos o tres penalizaciones | 0,5–1 | bajo | propio, unas 50 líneas | sí |
| T4 | Viterbi con duraciones explícitas (HSMM) | además modela cuánto dura cada estado | distribuciones de duración de datos abiertos | 1–1,5 | medio | propio | sí |
| T5 | CRF con transiciones enmascaradas | como T3, prohibiendo los cambios físicamente imposibles | la máscara | +0,5 sobre T3 | bajo | propio | sí |
| T6 | red de segmentación (MS-TCN++, ASFormer, ASRF) | una red refina las probabilidades y aprende las fronteras | entrenar con partidos etiquetados | 3 o más | alto | MIT | con CPU y versiones fijadas |
| T7 | poda y ajuste de fronteras | reetiquetar tramos muy cortos; mover cada frontera al toque o al saque más cercano | umbrales de datos abiertos | 0,5 | bajo | propio | sí |

**Lectura:**

- **El decodificador mueve la métrica de segmentos mucho más que el acierto por instante.** En PathCRF,
  añadir el CRF deja el acierto por instante casi igual (69,2 % → 69,6 %) y sube el F1 de eventos de 65,3
  a 75,7. **[fuente]**
- **Un post-proceso simple recupera casi toda la ganancia.** En segmentación de acciones, reetiquetar los
  tramos cortos sube el F1 segmental de 76,1 a 82,4; un detector de fronteras aprendido llega a 84,9.
  **[fuente]** Ese F1 segmental es de la misma familia que `spellF1`.
- **No hay evidencia de que las duraciones explícitas mejoren a un Viterbi bien ajustado.** El trabajo
  que los compara los encuentra muy parecidos. **[fuente]** T4 solo si gana en la validación externa.
- **"CRF con máscara dinámica" es T3 más T5.** Con tres estados y emisiones ya calculadas, un CRF es un
  Viterbi cuyas dos o tres penalizaciones se ajustan buscando directamente el mejor `spellF1`. La máscara
  útil aquí: no se permite pasar a un equipo que no tiene ningún jugador cerca del balón cuando el balón
  se ve.
- **Las librerías de HMM no compensan.** `hmmlearn` está en mantenimiento limitado, `hsmmlearn` está
  archivada y es GPL, y `sklearn-crfsuite` no declara soporte de Python 3.13. **[fuente]** Un Viterbi
  propio en numpy no añade dependencias.
- **El orden de la limpieza importa:** primero histéresis, luego rellenar huecos cortos y al final borrar
  islas cortas. **[fuente]**

**Elección:** T3 + T5 + T7. T4 como experimento. T6 fuera del plazo.

### 2.6 Vídeo y broadcast

| id | alternativa | cómo funciona | qué necesita | coste | riesgo | licencia | byte a byte |
|---|---|---|---|---|---|---|---|
| V1 | detectar el balón en el vídeo táctico | YOLOv8 con cabeza P2, FootAndBall o WASB, por teselas | GPU; entre 1 y 16 horas por pasada | 2–4 | alto | AGPL-3.0 (Ultralytics) o MIT | dudoso |
| V2 | action spotting | modelos de SoccerNet que marcan pases y conducciones | vídeo de broadcast; Linux y GPU de 24 GB | más de una semana | alto | MIT o GPL-3.0; datos con NDA | dudoso |
| V3 | sincronizar el broadcast | alinear los dos timelines para usar su balón y su cámara | emparejar jugadores en coordenadas de campo, o reloj del marcador | 2–4 | alto | propio | sí, si es determinista |
| V4 | detección de cortes con OpenCV | localizar cambios de plano en el broadcast | nada | horas | — | — | — |

**Lectura:**

- **El balón mide unos 4 píxeles en el vídeo táctico.** Es una cuenta, no una medida: 0,22 m en un campo
  de 105 m que ocupa 1.920 px. Los detectores públicos se entrenaron con balones de 8–20 px y no hay
  ninguna cifra publicada para plano de campo completo. **[fuente]**
- **Donde el tracking de Metrica perdió el balón (oclusión, balón aéreo, área poblada), un detector
  genérico lo perderá igual o más.**
- **Los modelos de action spotting no dan posesión.** Dan eventos sueltos con un segundo de tolerancia,
  entrenados con broadcast. El baseline con equipo se queda en 47–52 de Team-mAP@1 en su propio dominio.
  **[fuente]**
- **Sincronizar broadcast y táctico no está resuelto con herramientas públicas.** Lo publicado más
  cercano usa el reloj del marcador, con precisión de un segundo. **[fuente]**
- **V4 sobra.** La columna `valid` de la homografía del broadcast ya marca los 122 tramos que no son
  plano de campo. **[doc]**
- **Hay un problema de reglas además del coste.** Las detecciones por frame no se pueden commitear:
  serían una exportación del partido. Quien reproduzca el repo tendría que regenerarlas, y PyTorch no
  garantiza resultados idénticos entre plataformas ni entre CPU y GPU. **[fuente]** Eso choca con
  regenerar el CSV exacto.

**Elección:** nada de esto antes del 17. V3 es la idea con mejor relación entre valor y coste para la
fase siguiente, porque no necesita procesar vídeo.

---

## 3. Tabla comparativa y ranking

Ordenado por prioridad. La columna "qué error ataca" remite a la tabla de costes de la sección 1.3. No
doy una ganancia numérica por pieza: es lo que mide el protocolo de la sección 5.

### 3.1 Lo que cabe antes del 17

| prioridad | pieza | qué error ataca | coste (días) | riesgo | evidencia a favor |
|---|---|---|---|---|---|
| 1 | **Decodificador** Viterbi con coste de cambio, máscara y poda (T3 + T5 + T7) | cambios inventados, el error más caro | 1 | bajo | en PathCRF el CRF sube 10 puntos el F1 de eventos con el mismo acierto por instante |
| 2 | **Balón muerto** con señales propias (B1 + B2 + B5) | paradas no detectadas y `D` inventados | 1,5 | medio | el baseline tiene un recall de `D` de 0,21 en la ventana pública |
| 3 | **Harness externo**, experimento 0 y degradación (sección 5) | ninguno directamente: permite decidir todo lo demás | 2 | bajo | sin él, cada elección es una conjetura |
| 4 | **Emisión por reglas** con confirmación de control (N4, N3) | cambios mal situados | 1 | medio | más del 90 % de detección de pases con balón limpio |
| 5 | **Emisión aprendida** de tres clases con gradient boosting (N5 + B4) | convención del flag, fronteras y `D` a la vez | 2 | medio: cambio de dominio | aprende la convención del proveedor en vez de suponerla |
| 6 | **Reglas de puente** en huecos (L2) | cambios ocurridos sin balón | 0,5–1 | medio | — |
| 7 | **Señales sin balón** (L3, L4, L5) | lo mismo | 1–2 | medio | solo si el recuento de la sección 6.4 lo justifica |
| 8 | **Duraciones explícitas** (T4) | equilibrio entre posesiones cortas y cambios falsos | 1 | medio | evidencia publicada débil: solo si gana en la validación |

**Por qué este orden:**

- **1 y 2 atacan los dos fallos estructurales del baseline** y no dependen de ningún entrenamiento.
- **3 va antes que las emisiones** porque sin validación externa no hay forma de elegir entre N2, N3, N4
  y N5 sin caer en ajustar contra la ventana pública.
- **5 es la pieza con más recorrido y más riesgo.** Su ventaja es que no hay que adivinar cuándo cambia
  el flag del proveedor; su riesgo es que la degradación no imite bien al ATD.
- **6, 7 y 8 se deciden con medidas**, no por adelantado.

### 3.2 Lo que cabría pero no compensa

| pieza | por qué no |
|---|---|
| Kalman + RTS sobre el balón (A4) | suaviza los toques; el decodificador ya gestiona los huecos |
| pitch control (N6) | sin evidencia de que indique quién tiene el balón; necesita velocidades estables |
| comparar LightGBM con CatBoost | la diferencia esperable está por debajo del ruido |
| detección de cortes con OpenCV (V4) | la columna `valid` del broadcast ya lo da |
| librerías de HMM o CRF | un Viterbi propio son unas 50 líneas y no añade dependencias |

### 3.3 Lo que no cabe antes del 17

| pieza | coste | motivo principal |
|---|---|---|
| sincronizar el broadcast y usar su balón (V3, A6, L8) | 2–4 días | sin herramienta pública; un error de 1 s en la sincronización cuesta más de lo que aporta |
| detectar el balón en el vídeo (V1, L7) | 2–4 días más horas de GPU | balón de unos 4 px; reproducción exacta dudosa; AGPL si se usa Ultralytics |
| Ball Radar, TranSPORTmer, PathCRF (A5, L6) | más de una semana | piden trayectorias completas y continuas; sin pesos, sin licencia o sin código |
| red de segmentación temporal (T6) | 3 días o más | su ganancia sobre un post-proceso simple es pequeña en lo publicado |
| action spotting en vídeo (V2) | más de una semana | no da posesión; otro dominio; datos con NDA |

---

## 4. Pipelines completos

Los tres comparten esqueleto e interfaz. Cada pieza devuelve arrays de 199.319 posiciones indexados por
frame de vídeo, como pide `CLAUDE.md`:

```
ATD ─► limpieza del balón ─► emisiones por frame ─► decodificador por parte ─► poda y ajuste ─► CSV
        (A1 + A2)             log-prob. de H, A, D     (T3 + T5)                 (T7)
```

Lo único que cambia entre pipelines es **de dónde salen las emisiones**.

### 4.1 Pipeline A: reglas y decodificador

| | |
|---|---|
| emisión `D` | reglas geométricas, `SET PIECES` e inicio de la 2ª parte (B1 + B2 + B5) |
| emisión `H`/`A` | la regla que gane en la sección 5 (N2, N3 o N4) |
| sin balón | arrastre y reglas de puente (L1 + L2) |
| de dónde salen los parámetros | de los datos abiertos degradados |
| entrenamiento | ninguno |
| coste | unos 3 días entre dos personas |
| byte a byte | sí: numpy puro |
| riesgo principal | los umbrales a mano no recogen la convención del flag; `D` cuando el balón no se ve |
| ventaja | se explica en una página del documento técnico y da una entrega pronto |

### 4.2 Pipeline B: emisión aprendida con datos abiertos

| | |
|---|---|
| emisión `H`/`A`/`D` | un único modelo de gradient boosting que da la probabilidad de las tres clases (N5 + B4), con las señales de las reglas del pipeline A como variables |
| variables | sin identidad de jugador: distancias de los jugadores más cercanos de cada equipo al balón, cinemática del balón, toques detectados, forma colectiva, tiempo desde y hasta la última vez que se vio el balón, todo en ventanas de varias longitudes |
| sin balón | el mismo modelo, que ve qué variables faltan; más L2 |
| entrenamiento | 7 partidos de la Bundesliga degradados, con copias con los equipos intercambiados y el campo reflejado |
| coste | unos 2 días más sobre el pipeline A |
| riesgo principal | que la degradación no imite al ATD o que la convención del flag alemán no coincida con la del reto (experimento 0) |
| ventaja | no hay que adivinar cuándo cambia el flag: se aprende |

**Cómo se hace reproducible byte a byte:**

- el fichero del modelo entrenado se commitea (sale solo de datos abiertos, así que se puede publicar);
- versiones fijadas e inferencia en un solo hilo;
- las probabilidades se redondean antes de decodificar, para que una diferencia en el último decimal no
  cambie ninguna etiqueta;
- el script de entrenamiento va en el repo con semillas fijas, para que la organización pueda
  inspeccionar de dónde sale el modelo.

**Dependencia nueva:** el pipeline B añade `lightgbm` a `requirements.txt`. Esa decisión es del
responsable de infraestructura.

### 4.3 Pipeline C: segundo sensor de balón

| | |
|---|---|
| qué añade | el balón del ATD del broadcast, tras sincronizar los dos timelines (V3), o un detector sobre el vídeo táctico (V1) |
| qué resuelve | los cambios de posesión que ocurren con el balón oculto en el táctico |
| coste | 2–4 días, con riesgo alto |
| cuándo | no antes del 17. Es el candidato natural para el Innovation Challenge si pasamos |

### 4.4 Recomendado: A primero, B si gana

- **A y B comparten casi todo el código.** Montar A no es trabajo perdido: su decodificador, su limpieza y
  sus reglas son piezas de B.
- **A da una entrega validada el jueves,** como pide el calendario de `CLAUDE.md`.
- **B sustituye a A solo si gana con la regla de la sección 5.8.** Si no gana, o si el experimento 0 dice
  que el flag alemán no se parece al del reto, se entrega A.
- **C queda fuera** por coste, por riesgo y por el problema de reproducción.

**Calendario propuesto**, compatible con el de `CLAUDE.md`:

| día | qué |
|---|---|
| mié 11 | experimento 0; harness; script del perfil del ATD |
| jue 12 | pipeline A, primera versión: decodificador, `D` y emisión N2. Primera entrega validada |
| vie 13 | degradación comprobada; comparación N1–N4; primera versión de N5 |
| sáb 14 | decisión de nivel 1; recuento de intervalos entre anclas; reglas de puente |
| dom 15 | comparación de decodificadores; A frente a B |
| lun 16 | congelar y reproducir en una máquina limpia |
| mar 17 | validar el fichero exacto y entregar |

---

## 5. Plan de evaluación del nivel 1

### 5.1 Principio: fondo común y una sola pieza que cambia

Un método de nivel 1 solo opina sobre los frames con balón, y `spellF1` necesita los 199.319. Por eso los
candidatos **no se puntúan sueltos**: se monta un pipeline completo con todo fijo menos la pieza que se
compara.

| pieza | en la comparación de nivel 1 |
|---|---|
| limpieza del balón | la misma para todos |
| balón muerto | dos variantes: `D` copiado de las etiquetas ("oráculo") y el detector común |
| **emisión con balón visible** | **lo que se compara** |
| frames sin balón | sin evidencia: el decodificador arrastra el estado |
| decodificador | la misma familia; sus dos o tres parámetros se ajustan por candidato |

- **`D` oráculo** aísla la pregunta "¿quién tiene el balón?" de la pregunta "¿está vivo?".
- **Ajustar el decodificador por candidato** evita comparar un candidato bien acoplado con otro mal
  acoplado. El ajuste se hace siempre dejando fuera el partido en el que se puntúa.

### 5.2 Datos

| dataset | qué tiene | papel |
|---|---|---|
| **Bundesliga / DFL** (Bassek et al., 2025) | 7 partidos, 1.002.644 frames a 25 Hz, tracking TRACAB Gen5 con balón, y en cada frame `BallPossession` (1 local, 2 visitante) y `BallStatus` (0 inactivo, 1 activo). Licencia CC-BY 4.0. **[fuente]** | **principal:** entrenar, ajustar y comparar |
| **Metrica sample-data** | 3 partidos a 25 Hz con tracking limpio y eventos sincronizados, en las mismas coordenadas 0–1 que el ATD. No tiene flags por frame: kloppy devuelve `ball_owning_team=None`. **[medido en kloppy, fuente]** | **secundario:** comprobar que las conclusiones aguantan con otro proveedor y otra forma de etiquetar |
| **SkillCorner opendata** (versión actual) | 10 partidos de la A-League según su README (el repositorio lista 20 carpetas), con tracking sacado del broadcast a 10 fps, jugadores extrapolados marcados con `is_detected` y posesión por frame calculada por su propio sistema. **[fuente]** | **opcional:** es el único con ruido real de tracking automático, pero va a 10 fps y sus etiquetas no están revisadas |
| **Barça como local** (StatsBomb, SkillCorner 2019, Wyscout) | eventos de 264 partidos de LaLiga en el Camp Nou; tracking de broadcast del Barça–Real Madrid de 2019; eventos de LaLiga 2017-18 completa. Ninguno trae flags por frame. **[medido]** | **apoyo:** paradas y posesiones en LaLiga con el Barça de local, y banco de pruebas con tracking automático (sección 8.4) |

Otros datasets revisados y descartados para esto: PFF del Mundial 2022 (64 partidos, sin texto de licencia
y con etiquetas dispersas arrastradas), Google Research Football (simulado) y SoccerTrack v2 (sin
posiciones de balón medidas). **[fuente]**

**Descarga y lectura.** `validation/scripts/descargar_datos_abiertos.py dfl` baja los 21 ficheros
(2,63 GB, entre 350 y 420 MB de posiciones por partido) y comprueba su md5. Después, con el kloppy 3.18
ya instalado (sin ejecutar todavía con los ficheros de posiciones):

```python
from kloppy import sportec
ds = sportec.load_tracking(meta_data=".../DFL_02_01_matchinformation_..._J03WMX.xml",
                           raw_data=".../DFL_04_03_positions_raw_observed_..._J03WMX.xml",
                           only_alive=False)
```

- **`only_alive=False` es imprescindible.** Por defecto kloppy descarta los frames con balón inactivo y
  desaparecería la clase `D`. **[medido en kloppy]**
- **No hay que usar `sportec.load_open_tracking_data`.** En kloppy 3.18 descarga desde
  `springernature.figshare.com`, que el 11/11 respondía a los scripts con un desafío antirrobots
  (`x-amzn-waf-action: challenge`). `ndownloader.figshare.com` y el espejo de Hugging Face
  (`pysport/idsse-data`) sirven los mismos ficheros. **[medido]**
- **Coordenadas:** para medir distancias, `coordinates="sportec"`, que da exactamente los metros del XML
  con origen en el centro **[medido]**. Las de por defecto no son metros: kloppy 3.18 da su propio
  sistema, de 0 a 1, con origen arriba a la izquierda y el eje `y` invertido **[medido]**.
  `coordinates="metrica"` debería dejarlas en 0–1, como el ATD; kloppy acepta ese valor, pero no lo he
  probado con estos datos. **[sin verificar]**
- **Memoria:** la carga completa de un partido con kloppy (`only_alive=False` y `to_df()`) tarda unos
  104 s y llega a 4,5 GB de memoria **[medido]**. Con poca memoria libre,
  `validation/experimento0/dfl_lector.py` lee lo mismo por streaming con menos de 1 GB.
- Partidos disponibles: `J03WMX`, `J03WN1`, `J03WPY`, `J03WOH`, `J03WQQ`, `J03WOY`, `J03WR9`. kloppy 3.18
  lee sus eventos con el equipo local primero (comprobado con `J03WMX`). **[medido]**
- **El equipo poseedor solo significa algo con el balón activo.** kloppy asigna el visitante a cualquier
  valor que no sea 1, también cuando falta. **[medido en kloppy]**
- Los datos se descargan con un script y **no se commitean**. Hay que citar a los autores y a la DFL.

### 5.3 Etiquetas

- **Bundesliga:** `D` si `BallStatus` es 0; si no, `H` o `A` según `BallPossession`. Es la misma
  derivación mecánica que `CHALLENGE.md` describe para la GT del reto.
- **Las dos partes se separan con un tramo de `X`** en el array de etiquetas, para que el scorer no una
  posesiones a través del descanso. El scorer deduce los tramos evaluados de dónde la GT no es `X`.
- **Metrica:** hay que derivarlas de los eventos, que traen frame de inicio y de fin. Vivo entre un
  `SET PIECE` y el siguiente `BALL OUT`, falta o gol; equipo del último evento con control (`PASS`,
  `RECOVERY`). Es otra convención, y por eso es solo el dataset secundario.
- **No está verificado que en Metrica el balón sea `NaN` cuando está fuera de juego.** `databallpy` lo
  asume. **[sin verificar]** Si es así, en esos datos "sin balón" sí significa "muerto", al revés que en
  el ATD, y la degradación tiene que tenerlo en cuenta.

### 5.4 Experimento 0: ¿se parecen las etiquetas de la Bundesliga a la GT del reto?

Es lo primero, porque todo lo demás se apoya en ello. Medio día. Solo agregados.

**Medidas que deciden.** No dependen de ninguna cifra de la GT del reto: comparan el flag de la
Bundesliga con la definición de `CHALLENGE.md`.

| medida sobre las etiquetas de la Bundesliga | qué responde |
|---|---|
| posesiones por partido, cuantiles de duración, fracción de tiempo muerto, número de paradas | qué cuenta el proveedor como balón inactivo (¿también banda, fondo y córner?) |
| en cada cambio `H`↔`A`: distancia del balón al jugador más cercano del nuevo equipo y desfase hasta el toque más próximo | si el flag cambia en el primer toque, en el control o después, y si se queda con el último equipo con el balón suelto |
| en cada paso a inactivo: posición del balón respecto a las líneas y desfase desde que las cruza | cuándo empieza el balón muerto |
| en cada paso a activo: desfase desde que el balón empieza a moverse | cuándo se reanuda |
| opcional, medio día más: etiquetas derivadas de los eventos del mismo partido, puntuadas con `spellF1` contra los flags | cuánto separa a dos convenciones de etiquetado (sección 7.3) |

**Regla de decisión:** la Bundesliga vale como proxy principal si su flag se comporta como pide
`CHALLENGE.md`. Es decir: `D` cubre todo balón fuera de juego, la posesión cambia con un control del rival
y no con un toque, y se queda con el último equipo mientras el balón está suelto. Si no se comporta así,
se apunta en qué difiere y se corrige al derivar las etiquetas, o se baja su peso.

**Comparación informativa, que no decide nada.** La huella de retrasos (el `spellF1` de las etiquetas
contra sí mismas retrasadas 3, 8 y 25 frames) se apunta junto a la tabla oficial (0,9818 / 0,8933 /
0,6539), pero **ni la elección de dataset ni ningún parámetro dependen de esa comparación**. Es la misma
cautela que en la sección 1.2: es una medida descriptiva más, sin regla de decisión, hasta que la
organización conteste la consulta de Ismael (duda D21).
`validation/scripts/perfil_etiquetas.py` la calcula para cualquier CSV de etiquetas.

**Lo hace el equipo** con el paso 2 de [`validation/PASOS.md`](../validation/PASOS.md), que detalla cada
medida, las comprobaciones de lectura y la plantilla del resultado.

### 5.5 Degradar el tracking para que se parezca al ATD

El tracking de la Bundesliga es limpio: 22 jugadores con identidad y balón en todos los frames. Hay que
estropearlo hasta que se parezca al ATD. **Quitar el 41 % del balón al azar favorecería a todos los
métodos**, porque en el ATD el balón desaparece justo en duelos y balones aéreos.

**Paso 1. Perfil del ATD.** Un script que ejecuta una persona en local y que **solo imprime agregados**
de los frames evaluados. Son datos del partido, así que van con **pocos intervalos y gruesos**, solo
totales del partido entero y **ningún valor ligado a un frame, a un instante o a una jugada**:

| agregado (intervalos gruesos) | para qué |
|---|---|
| huecos sin balón y rachas con balón, en 5 intervalos de duración: < 0,5 s, 0,5–2 s, 2–5 s, 5–15 s, > 15 s | imitar la duración de las pérdidas |
| fracción de frames sin balón en una tabla de 3 × 3: densidad de jugadores a 5 m (baja, media, alta) por zona (tercio defensivo, medio, ofensivo) | imitar **dónde** se pierde |
| salto de posición del balón entre antes y después de un hueco, en 3 intervalos de metros, por las mismas 5 duraciones | distinguir oclusión de pase aéreo |
| jugadores localizados por frame: media y cuantiles 10, 50 y 90 | imitar los jugadores que faltan |
| duración de los tramos continuos de los slots: cuantiles 10, 50 y 90 | imitar la fragmentación |
| porcentaje de frames con saltos imposibles del balón o fuera de [0, 1] | imitar las detecciones falsas |
| temblor de las posiciones de los jugadores: mediana de la aceleración frame a frame | imitar el ruido de posición |
| porcentaje de frames con balón en los 10 s previos a los `SET PIECES`, todos juntos | aproximar si el balón se ve en el tiempo muerto |

**Si hay duda** de si un agregado es demasiado fino para pegarlo a Claude o para publicarlo, se pregunta
antes a la organización.

**Paso 2. Degradación.** Sobre cada partido abierto, con semillas fijas:

- quitar el balón con un proceso de dos estados cuya probabilidad de pérdida depende de la densidad de
  jugadores, la zona, la velocidad y la altura del balón (la Bundesliga trae la coordenada `Z`);
- quitar jugadores a rachas e ignorar sus identidades;
- añadir ruido de posición y detecciones falsas de balón.

**Paso 3. Comprobación.** Calcular los mismos agregados sobre los datos degradados y compararlos con el
perfil del ATD. Si no cuadran, se ajusta la degradación, no el método.

**Límite conocido:** la degradación es el eslabón más débil de la validación externa. Para acotarlo, cada
comparación se repite con tres severidades (por ejemplo 30 %, 41 % y 50 % de balón perdido). Si el orden
de los candidatos cambia con la severidad, la diferencia entre ellos no es fiable.

**Siempre se puntúa también sin degradar.** La diferencia entre el resultado con datos limpios y con
datos degradados es lo que cuesta el ruido del tracking (sección 7.3).

### 5.6 Candidatos de nivel 1

| id | emisión con balón visible | entrenamiento |
|---|---|---|
| N1 | equipo del jugador más cercano (la del baseline) | no |
| N2 | jugador más cercano con radio máximo y margen sobre el rival | no |
| N3 | zonas de posesión y de duelo de FIFA (Vidal-Codina et al.) | no |
| N4 | toques detectados por cambio de dirección o velocidad del balón; el cambio de posesión exige confirmación (segundo toque o balón retenido) y se fecha en el primer toque | no |
| N5 | gradient boosting con ventanas de varias escalas, entrenado dejando fuera el partido de prueba | sí |

N1 es el control: cualquier candidato tiene que superarlo. El pitch control entra, si acaso, como
variable de N5 (sección 2.3).

### 5.7 Métricas

- **Principal:** `spellF1` del pipeline completo, por partido y con todas las posesiones juntas.
- **Desempate:** `macroF1`.
- **Diagnóstico, solo en frames con balón visible:**
  - acierto de equipo con balón vivo;
  - precisión y recall de los cambios `H`↔`A` a ±12 y ±25 frames, y su retraso medio con signo;
  - cociente entre posesiones predichas y reales.

Todo sale de `evaluation/possession_metrics.py`, que acepta arrays de cualquier longitud.

### 5.8 Cuándo una diferencia es real

- **Entrenar y puntuar siempre en partidos distintos** (dejar un partido fuera, siete veces).
- **Intervalo por bootstrap sobre posesiones**, juntando los siete partidos. La banda oficial de 0,04 es
  para un partido; con siete debería rondar 0,04 / √7 ≈ 0,015, y hay que medirla, no suponerla.
- **Diferencias pareadas por partido.** Si un candidato gana en los siete, un test de signos bilateral
  da p = 2/128 ≈ 0,016. Si gana en seis, p ≈ 0,125.
- **Regla:** un candidato gana si el intervalo de la diferencia no incluye el cero **y** gana en al menos
  seis de los siete partidos **y** el orden se mantiene en las tres severidades de degradación. Si no, es
  un empate y se elige el más simple.
- **El bootstrap no mide el error de trasladar el resultado a otro partido y otro tracking.** Por eso,
  aunque salga significativa, una diferencia de menos de 0,03 se trata como empate.

### 5.9 Lo mismo para el nivel 2 y el decodificador

El harness es el mismo; cambia la pieza que se intercambia.

- **Nivel 2:** se fija la mejor emisión de nivel 1 y se comparan formas de tratar los huecos. El
  diagnóstico se restringe a los intervalos entre anclas de la sección 6.4: error de localización del
  cambio cuando las anclas discrepan y cambios inventados cuando coinciden.
- **Decodificador:** se fijan las emisiones y se comparan voto por mayoría (control), Viterbi con coste
  de cambio, Viterbi con duraciones explícitas, y cada uno con y sin poda de posesiones cortas y ajuste de
  fronteras.

### 5.10 Esfuerzo

| tarea | tiempo | depende de |
|---|---|---|
| experimento 0 | medio día | nada |
| harness: carga, etiquetas, puntuación por partido | medio día | nada |
| perfil del ATD (lo ejecuta una persona) | 2 horas | script |
| degradación y su comprobación | 1 día | perfil del ATD |
| candidatos N1–N4 con fondo común | 1 día, en paralelo | harness |
| candidato N5 | 1 día | harness y degradación |

---

## 6. Criterio para el router

### 6.1 Qué debe decidir el router

**Recomendación:** mantener el router, pero cambiarle el trabajo. Que decida **cuánto se fía el
decodificador de cada fuente de evidencia en cada frame**, no qué algoritmo etiqueta el frame. Un único
decodificador etiqueta todos los frames.

Tres razones:

- **Un cambio brusco de algoritmo pone la costura justo donde más duele.** El balón desaparece en los
  duelos y los balones aéreos, que es donde cambia la posesión. Si el nivel 1 etiqueta hasta el último
  frame con balón y el nivel 2 desde el siguiente, la frontera entre los dos cae sobre la transición.
- **`spellF1` no puede puntuar un método que solo etiqueta parte de los frames.** Los niveles solo se
  pueden comparar dentro de un pipeline completo (sección 5).
- **El reparto 60/40 por "balón visible o no" no separa lo fácil de lo difícil.** Con balón visible, el
  jugador más cercano falla el equipo en el 22 % de los frames vivos de la ventana pública (sección 1.6).
  Y muchos frames sin balón están en mitad de una posesión, donde la continuidad acierta sola.

### 6.2 Clases de observabilidad

Se calculan solo con el ATD, sin etiquetas. Variables por frame:

- si el balón está localizado tras la limpieza, y cuántos frames lleva así;
- longitud del hueco actual sin balón, tiempo desde la última vez que se vio y hasta la siguiente;
- distancia del balón al jugador más cercano de cada equipo, en metros, y la diferencia entre ambas;
- número de jugadores de cada equipo a menos de un radio `R` del balón;
- velocidad del balón;
- número de jugadores localizados en el frame.

| clase | definición orientativa | qué evidencia aporta |
|---|---|---|
| **C1 control claro** | balón visible y lento, un jugador a menos de `R1` y ningún rival a menos de `R2` | fuerte: sirve de ancla |
| **C2 balón en vuelo** | balón visible y nadie a menos de `R1` | por la regla del reto la posesión no cambia en el aire: continuidad |
| **C3 duelo** | balón visible con jugadores de los dos equipos a menos de `R2` | débil: hay que esperar a ver quién controla después |
| **C4 hueco corto** | sin balón durante `g1` frames o menos, y reaparece donde la trayectoria lo espera | se interpola y se trata como visible |
| **C5 hueco largo** | sin balón durante más de `g1` frames | ninguna del balón: aquí entra el nivel 2 |
| **C6 tracking degradado** | pocos jugadores localizados | mínima |

### 6.3 Cómo fijar los cortes sin mirar etiquetas del partido

1. **Los cortes `R1`, `R2` y `g1` se fijan en los datos abiertos degradados** (sección 5), donde sí hay
   etiquetas. Criterio: que en la clase C1 la emisión del nivel 1 acierte el equipo en torno al 98 % o
   más. C1 se define para ser fiable, no para ser grande.
2. **En esos mismos datos se mide el acierto del nivel 1 por clase.** Ese acierto fija el peso de la
   evidencia de cada clase en el decodificador.
3. **En el partido solo se calcula el reparto de frames por clase**, que es un agregado. Se compara con
   el reparto en los datos abiertos degradados. Si difieren mucho, la degradación no imita bien al ATD y
   hay que corregirla antes de fiarse de cualquier conclusión.

**Alternativa sin cortes fijos:** usar la probabilidad posterior del propio decodificador
(forward–backward). Los frames cuya etiqueta más probable no llega a un umbral son los inciertos. Es el
sentido literal de "router de incertidumbre" y no necesita reglas a mano; el umbral también se fija en
los datos abiertos.

### 6.4 Qué pasa de verdad al nivel 2

El problema difícil no son frames sueltos, sino **los intervalos entre dos anclas consecutivas**:

- **Las anclas discrepan** (antes `H`, después `A`): hubo un cambio en medio. El nivel 2 tiene que
  **situarlo**.
- **Las anclas coinciden** (antes `H`, después `H`): lo más probable es que no pasara nada. El nivel 2
  tiene que decidir si en medio hubo una posesión corta del rival o un balón muerto.

Contar cuántos intervalos de cada tipo hay en el partido y cuánto duran dice cuánto puede aportar el
nivel 2 antes de construirlo. Lo ejecuta una persona y pega **solo totales del partido**: número de
intervalos de cada tipo y su duración en los mismos 5 intervalos gruesos del perfil del ATD (sección
5.5), sin ningún valor ligado a un frame o a un instante. Si hay duda, se pregunta antes a la
organización.

---

## 7. Honestidad sobre el techo

### 7.1 Por qué un resultado casi perfecto no es alcanzable

- **La métrica cuenta posesiones y muchas son muy cortas.** En torno a un tercio dura menos de 3
  segundos y una de cada diez menos de 1 segundo (sección 1.2, inferencia a partir de la tabla oficial).
  Acertar una posesión de 2 segundos con IoU 0,5 exige que el error sumado de sus dos fronteras no pase
  de 1 segundo.
- **El balón falta en el 41 % de los frames evaluados, sobre todo en duelos, áreas pobladas y balones
  aéreos.** **[doc]** Son los momentos en los que cambia la posesión.
- **La GT es un flag de proveedor cuya convención temporal no conocemos.** Aunque leyéramos la jugada
  perfectamente, el instante exacto en que el flag cambia puede no coincidir con el nuestro.
- **No hay realimentación.** No hay leaderboard, la ventana pública no sirve para elegir y las
  diferencias de menos de 0,04 son ruido. **[doc]**

### 7.2 Qué nota corresponde a qué nivel de errores

Misma GT sintética de la sección 1.3, con varios errores a la vez **[medido]**. Como está calibrada con
la tabla oficial, es una escala para leer la métrica (D21), no una predicción:

| escenario | spellF1 | macroF1 |
|---|---|---|
| **A.** fronteras con σ = 6 frames; se pierden las posesiones de menos de 0,7 s; 0,25 cambios falsos por minuto; 5 % de paradas sin detectar | 0,87 | 0,96 |
| **B.** σ = 12; se pierden las de menos de 1 s y la mitad de las de 1–3 s; 0,5 falsos por minuto; 10 % de paradas | 0,69 | 0,93 |
| **C.** σ = 12; se pierden las de menos de 2 s y la mitad de las de 2–5 s; 1 falso por minuto; 20 % de paradas | 0,52 | 0,87 |
| **D.** σ = 25; se pierden las de menos de 3 s; 2 falsos por minuto; 30 % de paradas; 0,5 `D` falsos por minuto | 0,39 | 0,81 |
| baseline oficial (partido completo) | 0,24 | 0,67 |

**Lectura:**

- **El escenario A exige ver casi todos los toques de balón.** Con el 41 % de los frames sin balón no veo
  cómo llegar ahí usando solo el ATD.
- **No sé en qué escenario caerá nuestro sistema, y no voy a dar una cifra sin medir.** Depende de cuántos
  cambios de posesión ocurren con el balón oculto y de lo bien que se detecte el balón muerto. Es
  exactamente lo que miden las dos pruebas de la sección 7.3.
- **La tabla es una escala, no un pronóstico.** Sale de un ajuste a tres números publicados y de mis
  supuestos sobre el balón muerto.
- **El `macroF1` engaña.** En el escenario C, casi nueve de cada diez frames están bien y el `spellF1` es
  0,52. Un acierto alto por frame no indica un buen resultado en el ranking.

### 7.3 Las dos medidas que convierten esto en un número

Las dos se hacen con datos abiertos y están descritas en la sección 5. Hasta tenerlas, cualquier cifra de
techo es una conjetura.

1. **Coste del ruido del tracking.** El mismo pipeline sobre los partidos de la Bundesliga limpios y
   sobre los mismos partidos degradados para parecerse al ATD. El resultado con datos limpios es el techo
   del método; la diferencia es lo que cuesta el balón perdido.
2. **Coste de la convención de etiquetado.** Puntuar con `spellF1` unas etiquetas derivadas de los
   eventos de esos partidos contra sus flags por frame. Si dos definiciones razonables de posesión, las
   dos con información humana, se quedan por ejemplo en 0,7 entre sí, esa cifra marca hasta dónde llega
   un método que aplica la definición sin conocer la convención exacta del flag. Es una cota pesimista:
   los eventos de la Bundesliga tienen un desfase respecto al tracking de −0,37 ± 1,82 s según sus
   autores. **[fuente]**

### 7.4 Qué sí es razonable esperar

- **Batir el baseline con margen es probable.** Sus dos fallos son estructurales (confundir "sin balón"
  con balón muerto y cambiar de equipo en momentos equivocados) y un decodificador con coste de cambio y
  un detector de `D` propio los atacan directamente. La propia tabla oficial muestra que solo suavizar
  lleva de 0,05 a 0,24.
- **Lo que decide el ranking es relativo.** Pasan los 20 mejores y las diferencias pequeñas son ruido.
  Un pipeline sin errores tontos (alineación, los 2.934 frames `D` antes del saque de la 2ª parte,
  fichero validado, reproducción exacta) vale tanto como un método más sofisticado.

---

## 8. Verificación de las referencias propuestas

**Cómo se verificó:** cada referencia se buscó en su fuente primaria (arXiv, editorial, repositorio).
Las páginas se leyeron a través de una herramienta que las resume, así que antes de citar una cifra en el
documento técnico conviene releerla en el original. La licencia y los flags del dataset de la Bundesliga
los comprobé además en el artículo y en el código de kloppy instalado.

### 8.1 Resumen

| referencia | ¿existe? | ¿la cita es correcta? | ¿sirve antes del 17? |
|---|---|---|---|
| PathCRF | sí | sí; falta el congreso (KDD 2026) | no como modelo; sí la idea del decodificador |
| zonas de posesión y de duelo de FIFA | sí | sí | sí, como reglas de nivel 1 |
| Ball Radar | sí | **no:** título, arquitectura y repositorio | no |
| TranSPORTmer | sí | sí; es de 2024 | no |
| `lRomul/ball-action-spotting` | sí | a medias: ganó la edición de 2023 | no |
| `SoccerNet/sn-teamspotting` (T-DEED) | sí | sí | no |
| Kaggle DFL Bundesliga | sí | sí | no |
| MS-TCN++ | sí | sí | no como red; sí sus lecciones |
| YOLOv8-p2 | la configuración existe | sí | no |
| Metrica sample-data | sí | sí | sí, como dataset secundario |
| dataset de la Bundesliga (Bassek et al.) | sí | sí | **sí, como dataset principal** |

### 8.2 Detalle

**PathCRF**

- **Cita:** Kim, Lee, Seo, Ko, Yoon y Park, "PathCRF: Ball-Free Soccer Event Detection via Possession
  Path Inference from Player Trajectories", arXiv:2602.12080, publicado en KDD 2026.
- **Qué hace:** sin usar el balón, infiere en cada instante quién lo controla o entre qué dos jugadores
  viaja. Usa un CRF con las transiciones imposibles enmascaradas y decodifica con Viterbi.
- **Entrada:** 11 jugadores por equipo con trayectorias continuas, a 5 fps, y los tramos de juego vivo
  dados desde fuera. No decide el balón muerto.
- **Datos y resultados:** entrenado con los 7 partidos abiertos de la Bundesliga. 92,4 % de acierto de
  equipo por frame en juego vivo. En otra medida, el acierto de la arista exacta (quién la tiene o entre
  quiénes viaja) cae de cerca del 67 % al 42 % al cambiar de proveedor de tracking.
- **Código, pesos y licencia:** código MPL-2.0 y cinco modelos entrenados dentro del repositorio.
- **Aplicable aquí:** no directamente. Con 46 slots fragmentados habría que reconstruir antes 11
  trayectorias continuas por equipo. Además, sus pesos se entrenaron con los mismos 7 partidos que
  usaríamos para validar.

**Zonas de posesión y de duelo (Vidal-Codina et al.)**

- **Cita:** Vidal-Codina, Evans, El Fakir y Billingham, "Automatic event detection in football using
  tracking data", Sports Engineering 25, 18 (2022). MIT Sports Lab, financiado por FIFA.
- **Qué hace:** reglas sobre tracking. Zona de posesión de 0,5–1 m alrededor de cada jugador; zona de
  duelo de 1 m **alrededor del balón**; hay ganancia de posesión solo si el balón cambia de dirección o
  de velocidad dentro de la zona.
- **Entrada:** balón limpio a 25 Hz y un indicador de juego vivo. El balón muerto no lo detecta.
- **Resultados:** más del 90 % de detección en la mayoría de eventos, sobre 31 partidos privados.
- **Código y licencia:** artículo CC BY 4.0; sin código oficial. `databallpy` (MIT) implementa una parte
  con sus propios valores por defecto.
- **Pendiente:** los umbrales numéricos de giro y velocidad están en un anexo que no se ha leído.
  **[sin verificar]**
- **Aplicable aquí:** sí, como candidato N3 y como variables de N5.

**Ball Radar**

- **Errores en la cita:**
  - el título real es "Ball Trajectory Inference from Multi-Agent Sports Contexts Using Set Transformer
    and Hierarchical Bi-LSTM" (KDD 2023); "Ball Radar" es el nombre del repositorio;
  - usa Bi-LSTM, no GRU;
  - el repositorio es `hyunsungkim-ds/ballradar`.
- **Qué hace:** predice primero qué jugador tiene el balón y después la posición del balón.
- **Entrada:** 22 trayectorias completas a 10 Hz, solo tramos de juego vivo.
- **Resultados:** error de balón de 3,66 m y 85,85 % de acierto de equipo.
- **Código, pesos y licencia:** código público sin licencia (no concede derecho de reutilización) y sin
  pesos.
- **Aplicable aquí:** no.

**TranSPORTmer**

- **Cita:** Capellera, Ferraz, Rubio, Agudo y Moreno-Noguer, ACCV 2024, arXiv:2410.17785.
- **Qué hace:** un transformer para predecir, imputar e inferir el balón, y para clasificar el estado en
  pase, posesión, sin control o fuera de juego. El estado no lleva equipo.
- **Datos y resultados:** 283 partidos privados de LaLiga; error de balón de 2,71 m.
- **Código y pesos:** no se ha encontrado código oficial ni pesos.
- **Aplicable aquí:** no.

**`lRomul/ball-action-spotting`**

- **Qué es:** el primer puesto del SoccerNet Ball Action Spotting **de 2023**, con dos clases (pase y
  conducción) y 86,47 de mAP@1. No ganó ediciones posteriores.
- **Entrada:** vídeo de broadcast a 720p. No da equipo.
- **Código, pesos y licencia:** MIT; pesos en Google Drive; pide Linux y GPU.
- **Aplicable aquí:** no. Marca eventos sueltos con un segundo de tolerancia, en otro tipo de vídeo.

**`SoccerNet/sn-teamspotting` y T-DEED**

- **Qué es:** el kit del reto Team Ball Action Spotting 2025. Su baseline es T-DEED (Xarles et al., taller
  de CVPR 2024) con una salida adicional de equipo. Doce acciones, con el equipo como izquierda o
  derecha.
- **Resultados:** 47–52 de Team-mAP@1.
- **Licencia y datos:** GPL-3.0; los datos exigen firmar un NDA.
- **Aplicable aquí:** no.

**Kaggle DFL Bundesliga Data Shootout (2022)**

- **Qué fue:** detectar en vídeo jugadas, duelos y saques de banda. Ganó el equipo Hydrogen.
- **Código:** solo el tercer puesto es público, sin licencia.
- **Sin verificar:** las páginas de Kaggle no se pudieron leer; reglas, licencia de los datos y
  arquitectura ganadora quedan sin comprobar. **[sin verificar]**
- **Aplicable aquí:** no.

**MS-TCN++**

- **Cita:** Li, Abu Farha, Liu, Cheng y Gall, IEEE TPAMI 2020. Código MIT.
- **Qué hace:** segmentación temporal en varias etapas sobre características por frame, pensada contra
  la sobresegmentación. La pérdida de suavizado viene del MS-TCN de 2019, y el F1 segmental, de Lea et
  al.
- **Aplicable aquí:** como red, no: necesita partidos etiquetados y tiempo. Sus lecciones sí, a través
  del post-proceso de la sección 2.5.

**YOLOv8-p2**

- **Qué hay:** la configuración `yolov8-p2.yaml` existe en Ultralytics. No se han encontrado pesos
  preentrenados con esa cabeza.
- **Licencia:** AGPL-3.0, que obligaría a publicar el repo bajo AGPL.
- **Aplicable aquí:** no en plazo (sección 2.6).

**Metrica sample-data**

- **Qué es:** 3 partidos anonimizados a 25 Hz con tracking y eventos sincronizados. Sin flags de posesión
  por frame.
- **Licencia:** no hay fichero de licencia. El README pide citar la fuente en cualquier uso público.
- **Carga:** `kloppy.metrica.load_open_data()` existe y carga solo el tracking; los eventos se cargan
  aparte.

**Dataset de la Bundesliga (Bassek et al., 2025)**

- **Cita:** Bassek, Rein, Weber y Memmert, "An integrated dataset of spatiotemporal and event data in
  elite soccer", Scientific Data 12, 195 (2025).
- **Qué es:** 7 partidos de 1ª y 2ª Bundesliga 2022/23 con tracking TRACAB Gen5 a 25 Hz revisado por
  operadores, eventos y, en cada frame del balón, `BallPossession` y `BallStatus`.
- **Licencia:** CC-BY 4.0, con autorización de la DFL.
- **Lo que el artículo no dice:** cómo se generan esos dos flags ni si la posesión se mantiene mientras
  el balón está suelto. **[sin verificar]**

### 8.3 Otras fuentes útiles que he encontrado

| fuente | qué aporta |
|---|---|
| Link y Hoernig (2017), PLOS ONE | definición de posesión de equipo igual que la del reto; golpeo como pico de aceleración del balón |
| Lang et al. (2022), Scientific Reports | balón vivo o muerto solo con jugadores: 92 % por frame, 1,7 s de error en las fronteras; duración de cada tipo de parada |
| Siegle y Lames (2012) | unas 108 interrupciones por partido y su reparto por tipo |
| Bischofberger et al. (2024), PLOS ONE | los detectores por reglas pierden acierto al cambiar de datos; el problema es fechar |
| Ishikawa et al. (2021), ASRF | cuánto recupera un post-proceso simple frente a un detector de fronteras aprendido |
| Fried et al. (2020) | duraciones explícitas frente a un HMM normal: resultados muy parecidos |
| `databallpy` (MIT) | implementación de posesión individual por zona y cambio de velocidad o dirección |
| SkillCorner opendata | tracking automático de broadcast con jugadores extrapolados marcados |

### 8.4 Datos del Barça como local

Búsqueda pedida por Ismael el 11/11. El inventario completo, con cifras por temporada y cómo se comprobó
cada una, está en
[`validation/resultados/2026-11-11_inventario_datos_barca_local.md`](../validation/resultados/2026-11-11_inventario_datos_barca_local.md).

- **El partido del reto no se jugó en el Camp Nou, sino en Montjuïc.** El Barça no jugó ningún partido
  oficial en el Camp Nou entre el 28/05/2023 y el 22/11/2025. **[fuente]**
- **No hay tracking abierto de ningún partido del Barça con flags de posesión y de balón muerto por
  frame,** ni datos abiertos de LaLiga posteriores a 2020-21. **[medido]**
- **El partido del reto queda excluido de forma explícita.** Ninguna de estas fuentes lo contiene: los
  datos abiertos de LaLiga acaban en 2020-21. Aun así, el script de descarga rechaza cualquier temporada
  2024-25, y ningún paso usa datos de esa temporada, ni siquiera agregados (`RULES.md` §2).
- **Lo que hay** (comparado con la Bundesliga, que es la referencia):

| fuente | partidos del Barça como local | ¿tracking con balón? | ¿flags por frame? | licencia | ¿se puede publicar un modelo entrenado con ella? | papel |
|---|---|---|---|---|---|---|
| Bundesliga (referencia) | ninguno | sí, 25 Hz, revisado | **sí** | CC BY 4.0 | sí, citando | proxy principal |
| StatsBomb | 264 (2004-05 a 2020-21), todos en el Camp Nou; 18 con 360 (2020-21) | no: eventos, y en 2020-21 posiciones sin identidad solo en cada evento | no | acuerdo propio: investigación, sin redistribuir, logo, sin uso comercial | **no está claro**: el acuerdo prohíbe distribuir los datos y explotar el análisis derivado. No se publica ningún modelo entrenado con ellos sin aclararlo (D16) | priors de paradas y posesiones (paso 3 de `PASOS.md`) |
| SkillCorner (2020) | 1: Barça–Real Madrid, 18/12/2019 | sí, de broadcast a 10 fps, sin corregir | no: su posesión es una estimación automática, sin balón muerto | MIT y piden que se les cite; retirado de su repo en 2025 | mejor no: datos retirados por su autor (D15) | banco de pruebas con tracking automático (paso 4) |
| Wyscout (Pappalardo et al.) | 19 (LaLiga 2017-18 completa) | no: eventos | no | CC BY 4.0 | sí, citando | contraste de los recuentos de paradas |
| SoccerNet | 26 | no: acciones anotadas sobre el vídeo de TV | no | etiquetas sin NDA; vídeo con NDA | no aplica | no aporta nada para esto |

- **Un dataset solo de eventos es un proxy más débil que la Bundesliga:** no tiene tracking, su
  convención de posesión es otra y sus tiempos llevan errores de alrededor de un segundo. Sirve para
  recuentos y duraciones de paradas, no para entrenar ni para fijar fronteras.

- **Qué cambia:** nada de lo esencial. El estadio no influye en un método con tracking. Lo que hace que
  unos datos se parezcan a los del reto es, por orden: la misma etiqueta y el mismo tipo de tracking (solo
  la Bundesliga), el mismo ruido (nadie tiene el del ATD) y la misma liga y equipo (aquí aportan los
  eventos del Barça).
- **Primer indicio útil:** un partido de la Bundesliga tiene 102 reinicios y el Clásico de StatsBomb 86
  pases de reinicio. El Smart Tagging de nuestro partido etiqueta 59, con solo 5 faltas. Es probable que
  le falten muchos reinicios, y el detector de `D` no debería apoyarse solo en ellos. **[medido, a
  confirmar en el paso 3]**

---

## 9. Fuentes

**Documentación y código del reto**

- `CHALLENGE.md`, `EVALUATION.md`, `DATA.md`, `RULES.md`, `FAQ.md`, `games.py`, `starter/baseline.py`,
  `evaluation/possession_metrics.py` y `evaluation/run_evaluation.py` de este repo.
- Código de kloppy 3.18.0 instalado en el entorno (lectores de TRACAB, Sportec y Metrica).

**Referencias propuestas**

- PathCRF: https://arxiv.org/abs/2602.12080 · https://github.com/hyunsungkim-ds/pathcrf
- Vidal-Codina et al.: https://doi.org/10.1007/s12283-022-00381-6 · https://arxiv.org/abs/2202.00804
- Ball Radar: https://arxiv.org/abs/2306.08206 · https://github.com/hyunsungkim-ds/ballradar
- TranSPORTmer: https://arxiv.org/abs/2410.17785
- Ball Action Spotting 2023: https://github.com/lRomul/ball-action-spotting ·
  https://arxiv.org/abs/2309.06006
- Team Ball Action Spotting 2025: https://github.com/SoccerNet/sn-teamspotting ·
  https://arxiv.org/abs/2508.19182
- T-DEED: https://arxiv.org/abs/2404.05392
- Kaggle DFL Bundesliga Data Shootout: https://www.kaggle.com/competitions/dfl-bundesliga-data-shootout ·
  https://github.com/bamps53/kaggle-dfl-3rd-place-solution
- MS-TCN++: https://arxiv.org/abs/2006.09220 · https://github.com/sj-li/MS-TCN2
- MS-TCN: https://arxiv.org/abs/1903.01945
- YOLOv8-p2:
  https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/models/v8/yolov8-p2.yaml ·
  https://www.ultralytics.com/license

**Datasets**

- Bundesliga (Bassek et al.): https://doi.org/10.1038/s41597-025-04505-y ·
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11787359/ · https://doi.org/10.6084/m9.figshare.28196177
- Metrica sample-data: https://github.com/metrica-sports/sample-data
- SkillCorner opendata: https://github.com/SkillCorner/opendata
- PFF, Mundial 2022: https://www.blog.fc.pff.com/blog/pff-fc-release-2022-world-cup-data
- kloppy, carga de Sportec: https://kloppy.pysport.org/user-guide/loading-data/sportec/
- Espejo de la Bundesliga en Hugging Face: https://huggingface.co/datasets/pysport/idsse-data

**Datos del Barça como local**

- StatsBomb open data: https://github.com/statsbomb/open-data (commit
  `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`; acuerdo de uso en su `LICENSE.pdf`)
- SkillCorner, versión de 2020 con el Barça–Real Madrid del 18/12/2019:
  https://github.com/SkillCorner/opendata/tree/1b99d401ddc82e366c5c20d6860878668fd5858f
- Wyscout (Pappalardo et al., 2019): https://doi.org/10.6084/m9.figshare.c.4415000.v5 ·
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6817871/
- SoccerNet, listas de partidos: https://github.com/SoccerNet/SoccerNet/tree/main/SoccerNet/data
- Vuelta del Barça al Camp Nou el 22/11/2025:
  https://www.fcbarcelona.com/en/news/4407735/first-game-back-at-spotify-camp-nou-in-figures ·
  https://stadiumdb.com/news/2025/11/spain_date_confirmed_barca_return_home_after_909_days

**Posesión, balón muerto y eventos a partir de tracking**

- Link y Hoernig (2017): https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0179953
- Bischofberger et al. (2024): https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0298107
- Lang et al. (2022): https://pmc.ncbi.nlm.nih.gov/articles/PMC9522646/
- Siegle y Lames (2012): https://lida.sport-iat.de/dfb/Record/4024884?lng=en
- CIES, tiempo efectivo de juego: https://football-observatory.com/IMG/sites/mr/mr64/en/
- `databallpy`: https://github.com/Alek050/databallpy ·
  https://databallpy.readthedocs.io/en/latest/features/team_and_player_possession.html
- Peral et al. (2025): https://arxiv.org/abs/2512.19528
- LaurieOnTracking (pitch control y velocidades):
  https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking

**Segmentación temporal y decodificación**

- Lea et al., F1 segmental: https://arxiv.org/abs/1611.05267
- Ishikawa et al., ASRF: https://arxiv.org/abs/2007.06866 · https://github.com/yiskw713/asrf
- ASFormer: https://arxiv.org/abs/2110.08568
- Fried et al., HSMM frente a HMM: https://arxiv.org/abs/2005.03684
- pyannote (histéresis y duraciones mínimas): https://github.com/pyannote/pyannote-audio

**Balón, vídeo y sincronización**

- Singh et al., deriva de filtros de Kalman con balones que botan: https://arxiv.org/abs/2509.18451
- Kellis y Katis, velocidad de golpeo: https://jssm.org/jssm-06-154.xml-abst
- FootAndBall: https://github.com/jac99/FootAndBall
- WASB: https://github.com/nttcom/WASB-SBDT
- Theiner et al., sincronización por el reloj del marcador: https://arxiv.org/abs/2110.11107
- Reproducibilidad en PyTorch: https://docs.pytorch.org/docs/stable/notes/randomness.html

**Origen del tracking de LaLiga**

- LaLiga, Mediacoach y TRACAB: https://newsletter.laliga.es/global-futbol/laliga-mediacoach-data-in-the-cloud
- Lector de TRACAB de floodlight: https://floodlight.readthedocs.io/en/latest/modules/io/tracab.html
