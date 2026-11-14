# Plan hasta la entrega: quién hace qué (14–17 de noviembre)

> **Decidido por Ismael el 14/11/2026.** Sustituye al reparto y al calendario anteriores de `CLAUDE.md` y
> de `docs/GUIA_EQUIPO.md` §9, y al orden de «Lo siguiente» del 14/11 por la mañana. El porqué está en
> [`docs/decisiones.md`](decisiones.md) (entrada del 14/11).
>
> **Para quién:** cada persona del equipo y su Claude. Lee las secciones 0, 1 y 2, y después la de tu
> pieza en la sección 3.
>
> **Entrega:** martes 17 de noviembre, 23:59 CET.

## 0. En 30 segundos

- **Un solo pipeline con cinco piezas y una persona por pieza.** Todas avanzan a la vez.
- **El pipeline ya corre de punta a punta,** con la versión más simple de cada pieza (`possession/`). Tu
  trabajo es sustituir la tuya por una mejor, sin tocar las de los demás.
- **Las piezas se enchufan con una interfaz común** (sección 2). No se cambia sin avisar a Ismael.
- **Qué versión entra lo decide el harness de la DFL** (sección 4): los 7 partidos abiertos de la
  Bundesliga. Nunca la ventana pública de 5 minutos.
- **Corte: lunes 16 a las 14:00.** Lo que no haya ganado en el harness para entonces no entra. Se congela
  el lunes por la noche.

## 1. Quién hace qué

| pieza | quién | su fichero | qué entrega | dónde se prueba |
|---|---|---|---|---|
| esqueleto, harness e integración | Ismael | `possession/pipeline.py`, `possession/tracking.py`, `validation/harness/` | el pipeline de un comando, el harness de la DFL, la integración diaria, el congelado y la entrega | partido inventado y DFL |
| decodificador | David | `possession/temporal.py` | la secuencia final de etiquetas: costes de cambio ajustados, duraciones mínimas y poda | DFL, sin datos del partido |
| `D`: fronteras y anclas | Manuel | `possession/dead_ball.py` | cuándo empieza y cuándo acaba cada parada, y qué equipo reanuda, con el balón, el Smart Tagging y el silbato | agregados del partido; lo del balón, también en la DFL |
| `D`: estado, y documento técnico | Ana | `possession/dead_state.py` | la probabilidad de que el juego esté parado en cada frame, con los jugadores; desde el lunes, el documento técnico | DFL |
| evidencia de equipo y limpieza del balón | Antonio | `possession/candidates.py`, `possession/ball.py` | quién tiene el balón cuando se ve: proximidad con control, frente al jugador más cercano | DFL degradada |
| apuesta B: evidencia aprendida | Ismael, en una sesión aparte | `possession/aprendida.py` | un modelo de `H` frente a `A` (decisión del 14/11); solo si gana al de reglas | DFL |

Cada uno trabaja en su fichero. Si necesitas algo de otra pieza, pídeselo a su dueño.

## 2. Cómo se enchufan las piezas

```
ATD ─► Tracking ─► limpieza ─► evidencias por frame ─► suma ─► decodificador ─► CSV
       tracking.py  ball.py    candidates.py                    temporal.py     pipeline.py
                               dead_state.py
                               dead_ball.py
```

**El `Tracking`** (`possession/tracking.py`) es lo único que reciben las piezas:

| campo | qué es |
|---|---|
| `bx`, `by` | balón en metros, forma (n,). `NaN` donde no se ve |
| `px`, `py` | slots de jugadores en metros, forma (n, n_slots). `NaN` donde falta |
| `team` | equipo de cada slot: 0 local (`H`), 1 visitante (`A`) |
| `pitch` | (largo, ancho) en metros; el origen está en una esquina |
| `blocks` | tramos evaluados, como (inicio, fin) con el fin sin incluir |
| `fps` | 25 |

`n` son los frames del vídeo: 199.319 en el partido.

**Las piezas de evidencia** (`candidates`, `dead_state`, `dead_ball`) tienen una función
`evidence(trk)` que devuelve dos arrays de forma (n, 3), con las columnas en el orden `H`, `A`, `D`:

- **`score`:** puntuación de cada estado en cada frame. Es aditiva: el pipeline suma las de todas las
  piezas. Solo cuentan las diferencias entre las columnas de un mismo frame. Una fila a cero es «no opino».
- **`allowed`:** `False` prohíbe ese estado en ese frame. Es para lo que se sabe seguro, como el tramo
  antes del saque. El pipeline cruza las de todas las piezas.

Con esto una pieza de `D` también puede decir qué equipo reanuda: puntúa `H` o `A` en los frames
posteriores al reinicio.

**El decodificador** (`temporal.decode(score, allowed, blocks, params)`) recibe la suma y devuelve una
etiqueta por frame: 0 `H`, 1 `A`, 2 `D` y 3 `X` fuera de los tramos evaluados. La histéresis, las
duraciones mínimas y la poda van aquí, no en las piezas de evidencia.

**Para comparar variantes de una pieza** (14/11): escríbela como otra función de tu módulo, con la misma
firma (la apuesta B usa además `possession/aprendida.py`, que el harness admite para `candidates`). El harness la usa en lugar de la de siempre con `pipeline.run(..., pieces=...)`, que se rellena
desde el fichero de `--versiones` (README del harness). La entrega usa siempre las de siempre:
`ball.clean`, `aprendida.evidence_b5` (la apuesta B, desde el 15/11; antes `candidates.evidence`),
`dead_state.evidence` y `temporal.decode`, que son las que nombra
`pipeline.PIECES`. Todas las versiones reciben el mismo tracking, de solo lectura: una pieza devuelve una
copia (`trk._replace(...)`), nunca lo cambia.

**Lo que da error a propósito,** para que no pase en silencio: una puntuación con `NaN` o infinito en un
frame evaluado, una pieza que no devuelve arrays de forma (n, 3), un parámetro del decodificador mal
escrito, y dos piezas que se contradicen en lo que prohíben. Todas las piezas, también `dead_ball`,
reciben el tracking con el balón ya limpio.

**Reglas de la interfaz:**

- **Funciones puras sobre arrays.** Ninguna pieza abre ficheros, salvo `dead_ball.py`, que usa los del
  partido. Así el mismo código corre en el partido y en la DFL: lo que valida el harness es lo que se
  entrega.
- **Un slot no es un jugador.** Su índice no identifica a nadie a lo largo del partido. El harness
  baraja los slots para que un código que dependa de eso falle allí y no en el partido.
- **Determinista:** sin azar o con semilla fija, y con los empates resueltos siempre igual.
- **Distancias en metros.** El `Tracking` ya viene escalado.
- **Ninguna constante sale del partido ni de la ventana pública.** Los umbrales se fijan en la DFL. Un
  valor por defecto que aún no se ha ajustado se marca como «sin ajustar» en el código.
- **Solo numpy y pandas en el pipeline.** Si entrenas un modelo, sus coeficientes van escritos en tu
  módulo y el script que los calcula, en `validation/`, con semilla fija. Una dependencia nueva la decide
  Ismael.

**Comprobación de que no has roto nada** (sin datos del partido; Claude puede ejecutarla):

```bash
python validation/scripts/prueba_pipeline.py
```

## 3. Tu pieza

### Ismael: esqueleto, harness e integración

**Hecho hoy:** el esqueleto (`tracking`, `ball`, `candidates`, `dead_state`, `temporal`, `pipeline`) con
su prueba con un partido inventado, y el harness de la DFL (`validation/harness/`) con su primera medida.

**Hoy:**

1. **La medida del balón del ATD en todo el partido:** el script lo escribe Claude en
   `validation/partido/` y lo ejecutas tú. Mide la visibilidad, la longitud de los huecos y cuánto está
   suavizado el balón. Sin ella, la degradación de la DFL no es creíble y no se puede elegir entre
   evidencias de equipo.
2. **La primera entrega de prueba:** ejecutar `python -m possession.pipeline`, validarla y puntuarla en
   la ventana pública (`/evaluar`) solo para ver que no está rota.
3. **Lo de la organización:** las instrucciones de entrega del email, el formulario, la cuenta de Google
   y el nombre de equipo.

**Domingo y lunes:** revisar y mergear las PR a diario, mantener una entrega válida en todo momento,
congelar, y reproducir el CSV byte a byte en una máquina limpia.

**Apuesta B** (evidencia aprendida, `docs/investigacion_metodos.md` §4.2; de `H` frente a `A` y no de tres
clases, por decisión del 14/11 en `docs/decisiones.md`): en una sesión aparte, cuando el harness y la
degradación estén comprobados. Se abandona el lunes a las 14:00 si no ha ganado. Medida el 14/11:
`validation/resultados/2026-11-14_apuesta_b.md`.

### David: decodificador (`possession/temporal.py`)

**Qué hay:** un Viterbi sobre {`H`, `A`, `D`} con tres costes de cambio (`switch`, `to_dead`,
`from_dead`), todos a 25 y **sin ajustar**. Es la pieza que más mueve el `spellF1` y la única que no
tenía dueño.

**Qué tienes que hacer:**

1. **Ajustar los costes en la DFL,** dejando un partido fuera cada vez, con el `D` copiado de las
   etiquetas (el `D` oráculo del harness). Así se aísla tu pieza de las de `D`.
2. **Garantizar las duraciones mínimas:** ninguna racha de `D` ni de juego vivo por debajo de un mínimo.
   Lo pide el criterio de aceptación del `D` (decisión del 13/11): un `D` que parpadea cuesta más que un
   `D` perdido.
3. **Probar la poda y el ajuste de fronteras** (T7 de `docs/investigacion_metodos.md` §2.5): reetiquetar
   las rachas más cortas que un mínimo. El mínimo sale de la DFL: la GT tiene posesiones reales de menos
   de 1 s.

**Candidatos,** escritos aquí antes de medir: (a) Viterbi con los costes ajustados; (b) el mismo con
duraciones mínimas; (c) el mismo con poda. El control es el voto por mayoría de ±50 frames del baseline.

**El orden importa (14/11 por la noche).** Los costes se miden en las unidades de la evidencia de equipo.
- **Qué evidencia hay:** la de `main` es el jugador más cercano, con un empujón fijo por frame. La apuesta
  B de Ismael (B2, evidencia aprendida con la proximidad y la forma de los equipos) va ganando a `main` y
  da empujones de tamaño variable, con una escala ajustada para el coste 25 de hoy. Falta comprobarla con
  jugadores como los del ATD.
- **Ya, sobre `main`:** escribe el código de (b) y (c) y el fichero de versiones con los candidatos.
- **Cuando se decida B2 (entra o se descarta):** ajusta los costes encima de la evidencia que quede en
  `main`. Ismael avisa. Si entra B2 y cambias los costes, hay que volver a mirar su escala: coordínalo con
  Ismael.
- **La pieza de `D` de estado de Ana ya está en `main`.** Con el `D` oráculo no cambia nada en tu medida.

**De dónde partes** (`validation/resultados/2026-11-14_harness_como_el_atd.md`, con el `D` oráculo y la
degradación «como el ATD» del 14/11):
- **Contra el baseline:** el Viterbi con coste 25 le gana en los 7 partidos. Con las etiquetas corregidas
  por control gana por más de 0,10. Con el flag gana por +0,022, por debajo del 0,03 de §5.8.
- **Contra el coste 25:** 12 y 50 empatan, y 100 pierde. Con el flag, 50 pierde; con las etiquetas de
  control, queda casi igual.
- **Las dos convenciones:** el coste que conviene cambia con la convención, y la de la GT sigue sin medir.
  Lo que elijas tiene que aguantar con las dos.
- **Para sustituir lo de `main`:** hay que ganar al control y a `main`. Con `--eventos` ves los aciertos en
  los eventos humanos de la DFL. Son descriptivos, pero enseñan el precio de subir el coste: aciertas más
  duelos sin cambio y pierdes recuperaciones.

**Ojo con ese +0,10:** las etiquetas de control salen de una regla de proximidad, y el Viterbi sobre el
jugador más cercano se parece a ella, así que parte de la ventaja es por construcción. El flag es el
mismo tipo de etiqueta que la GT del reto: lo que no aguante con el flag no cuenta.

**No necesitas datos del partido.** Todo se mide en la DFL y lo puede ejecutar tu Claude.

**Primer paso:** baja la DFL (sección 6) y ejecuta `python validation/scripts/prueba_pipeline.py` y
`python validation/harness/puntuar.py`.

### Manuel: `D`, fronteras y anclas (`possession/dead_ball.py`)

**Qué hay:** tu v1 (el tramo antes del saque de la 2ª parte) y una función nueva, `evidence()`, que la
pasa al pipeline con la interfaz común. Es la pieza del partido: usa el Smart Tagging y las constantes
de saque, así que no corre en la DFL.

**Qué tienes que hacer,** siguiendo las capas de la revisión
(`validation/resultados/2026-11-13_revision_balon_muerto.md` §6):

1. **Hoy, antes que nada: ejecutar los agregados** de `validation/partido/agregados_smart_tagging.py`,
   `agregados_balon_reinicios.py` y `agregados_jugadores.py`, y pegar la salida a tu Claude. Deciden cómo
   se usa cada señal y si los dos descartes reabiertos se cierran.
2. **Anclas duras:** de cada gol a su saque, y el final de cada parte. Salen del Smart Tagging o de un
   algoritmo, nunca de lo que se ve en el vídeo. Van en `allowed`.
3. **Fin del `D` (el reinicio):** dentro de cada ventana `SET PIECES`, con lo que digan los agregados.
4. **Inicio del `D` (la salida):** el balón que desaparece cerca de una línea yendo hacia fuera.
5. **Equipo que reanuda:** el `Team` del `SET PIECE`, puntuando `H` o `A` tras el reinicio. Medio segundo
   de equipo equivocado tras cada reinicio baja el `spellF1` de 1,00 a 0,80.
6. **El silbato** (`validation/silbato/`): entra como una señal más del inicio del `D` solo si pasa el
   criterio que ya está fijado en su bitácora. Falta que una persona ejecute
   `validation/partido/silbato_audio.py`.

**Criterio para entrar** (decisión del 13/11, tal cual): latencia de 25 frames o menos en el inicio y en
el fin en al menos el 70 % de las paradas, sesgo mediano dentro de ±12 frames, 0,3 `D` espurios o menos
por minuto de juego, y ninguna racha por debajo de la duración mínima.

- Lo que usa solo el balón y los jugadores se mide en la DFL con los scripts de
  `validation/scripts/revision_balon_muerto/`.
- Lo que usa el Smart Tagging no se puede medir en la DFL. Se comprueba en el partido con agregados
  (cuántas ventanas `SET PIECES` reciben un fin de `D`, duración de los `D` en intervalos gruesos), y la
  ventana pública solo dice si algo está roto.

**No hagas:** suavizar el `D` con un voto por mayoría, usar la falta de balón como `D`, ni arrastrar el
equipo anterior a través de una parada. Los tres están descartados con medidas (decisión del 13/11).

### Ana: `D`, estado (`possession/dead_state.py`) y documento técnico

**Qué hay:** una versión que no opina. Solo usa el `Tracking`, así que corre igual en el partido y en la
DFL.

**Qué tienes que hacer:**

1. **El modelo de estado con jugadores** de tu revisión (§5.3): rasgos de equipo sin identidad, entrenado
   con los 7 partidos de la DFL dejando uno fuera. No hace falta esperar a la degradación.
2. **Devolverlo como puntuación de la columna `D`** (por ejemplo, el logaritmo de la razón de
   probabilidades), sin umbral ni histéresis: eso lo pone el decodificador.
3. **Los coeficientes van escritos en el módulo** y el entrenamiento, en `validation/`. `scikit-learn`
   solo se usa para entrenar, no en el pipeline.
4. **Comprobar que se traslada al ATD:** el agregado 4 de la revisión (velocidad media de los jugadores),
   que ejecuta Manuel, dice si los jugadores del ATD se mueven como los de la DFL.

**Criterio para entrar:** el mismo del 13/11 que el de Manuel. Tu propia medida dice que el estado solo
llega tarde (el inicio, 1 s de mediana) y no mejora el `spellF1`: tu pieza suma junto a las fronteras de
Manuel, que ponen el instante. Coordinaos.

**Documento técnico:** desde el lunes, con Ismael como dueño. La materia prima es `docs/decisiones.md` y
`validation/resultados/`. Tiene que explicar el enfoque, los datos usados y los descartados, los datos de
entrenamiento y su origen, las reglas de posesión, las limitaciones y cómo reproducirlo.

### Antonio: evidencia de equipo (`possession/candidates.py`) y limpieza (`possession/ball.py`)

**Qué hay:** el jugador más cercano al balón (N1), que es lo que hace el baseline, y una limpieza que
todavía no hace nada.

**Qué tienes que hacer:**

1. **La limpieza del balón, fija y sin comparar variantes** (`ball.py`): descartar saltos imposibles y
   detecciones aisladas, e interpolar solo los huecos cortos. No se interpola si el balón reaparece junto
   a un jugador del otro equipo.
2. **Dos candidatos de evidencia de equipo por proximidad,** frente a N1:
   - **N2:** el más cercano solo opina si está a menos de un radio y el rival, claramente más lejos;
   - **control por retención:** el más cercano es del mismo equipo, a menos de un radio, durante varios
     frames seguidos. Es la traducción de «un toque sin control no cambia la posesión».
3. **Después, si hay tiempo:** las reglas de puente en los huecos (L2 de
   `docs/investigacion_metodos.md` §2.4).

**Lo que no entra de momento:** los candidatos que detectan toques por cambios bruscos de la velocidad
del balón (N4). El experimento 2 apunta a que el balón del ATD viene suavizado y el detector calibrado en
la DFL casi no ve toques en él.

**Cómo se mide:** en el harness, con el `D` oráculo. Los radios y los frames se fijan en la DFL.

**Ojo con el control por retención:** es casi la misma regla con la que se fabricaron las etiquetas de
control del harness (el más cercano a 1 m durante 12 frames). Con esas etiquetas ganará por construcción.
Solo cuenta lo que gane también con el flag.

**Aviso (actualizado el 14/11 por la noche):** la degradación de la DFL ya está comprobada con la medida
del balón del ATD (sección 4). El orden entre candidatos se decide en el harness con las condiciones que
votan, frente al control y frente a la versión de `main`. Ojo con lo que dependa de la velocidad del
balón: en el ATD viene suavizado unos 25 frames.

## 4. Cómo se decide qué entra

**El harness de la DFL** (`validation/harness/`; su `README.md` dice cómo se usa) ejecuta el pipeline con
las mismas piezas sobre los 7 partidos abiertos de la Bundesliga, que sí tienen etiquetas, y lo puntúa
con el scorer oficial. Lo puede ejecutar Claude, porque no son datos del partido. Tarda medio minuto:

```bash
python validation/harness/puntuar.py
```

**Cambio del 14/11 por la noche: la degradación imita al balón del ATD.**
- El perfil del balón del ATD en todo el partido (`validation/resultados/2026-11-14_perfil_atd.md`)
  dice que casi no tiene huecos cortos: pierde el balón en bloques de 5 s o más, como la DFL con solo
  los `D` tapados. La condición de antes, con el 41 % del balón en juego tapado en bloques de 1 s, era
  mucho más dura.
- Por decisión de Ismael, el harness tapa ahora el balón «como el ATD», calibrado con la regla fijada
  antes de medir (`validation/resultados/2026-11-14_harness_como_el_atd.md`).
- **Votan dos condiciones:** «como el ATD» y «como el ATD, sin bloques».
- **Se puntúan sin voto** «limpio» y la de antes («huecos y suavizado»).
- Los números de la tabla de referencia cambian: hay que medir de nuevo lo que se midió antes.

**Qué puede decidir y qué no:**

| | qué |
|---|---|
| **hoy** | la familia del decodificador y sus costes, con el `D` oráculo; el orden entre evidencias de equipo y lo que use la velocidad del balón (degradación «como el ATD», 14/11); la apuesta B. Ojo: la DFL tiene más disputas que el ATD (20 % frente a 14,5 %), y es donde más se separan las evidencias por proximidad |
| **todavía no** | el `D` en el harness: no tiene el modo con el equipo copiado de las etiquetas, y con el `D` oráculo una pieza de `D` no cambia nada. El `D` se mide con sus propios scripts (los de Ana traen ese modo) y el criterio del 13/11 |
| **nunca** | lo que usa el Smart Tagging, que la DFL no tiene |

**Cómo se mide siempre:**

- **Con las dos convenciones de etiquetas:** el flag de la DFL tal cual y el corregido con control. La
  convención de la GT sigue sin medir.
- **En las condiciones del balón que votan:** «como el ATD» (microcortes, bloques de 5 a 15 s en el
  11,3 % del juego y el balón suavizado 25 frames) y «como el ATD, sin bloques». Acotan si los huecos
  largos del ATD caen en juego o en paradas.
- **Frente al control:** el baseline (jugador más cercano y voto por mayoría), con el mismo tratamiento
  del `D`.
- **Frente a la versión de `main`:** para sustituir a lo que hay, un candidato tiene que ganar al control
  **y** a `main` con la misma regla. Si empata con `main`, se queda lo de `main` (decisión de Ismael,
  14/11).

**Cuándo gana un candidato** (`docs/investigacion_metodos.md` §5.8):

- gana en al menos 6 de los 7 partidos;
- el intervalo de la diferencia no incluye el cero;
- el orden se mantiene en las condiciones del balón que votan y con las dos convenciones;
- la diferencia de `spellF1` es de 0,03 o más. Por debajo es un empate, y entra el más simple.

**Dos o tres candidatos por pieza, escritos antes de medir.** Con muchas variantes, gana el azar. Se
escriben en un fichero de `validation/harness/versiones/` y se miden con
`python validation/harness/puntuar.py --versiones <fichero>`, sin tocar `puntuar.py` (el README del
harness dice cómo).

**La ventana pública** se mira siempre (`/evaluar`) y nunca elige: sirve para ver si algo está roto.

**El `D` en la DFL tiene un límite:** la DFL congela el balón mientras está muerto, así que el harness lo
tapa. Entonces «no hay balón» casi equivale a «`D`», cosa que en el ATD no pasa. Por eso las
comparaciones de hoy van con el `D` oráculo, y ningún número con `D` propio que dependa del balón se da
por bueno.

## 5. Calendario

| cuándo | qué |
|---|---|
| **sábado 14** | esqueleto y harness en `main`; todos con la DFL en local; agregados del partido ejecutados; primera entrega de prueba |
| **domingo 15** | cada pieza itera contra el harness; las PR entran según ganan |
| **lunes 16, 14:00** | **corte:** lo que no haya ganado no entra |
| **lunes 16, tarde y noche** | congelar; reproducir byte a byte en una máquina limpia; documento técnico |
| **martes 17** | repo público, validar el fichero exacto y enviar con margen. Límite: 23:59 CET |

## 6. Lo que solo puede hacer una persona

Claude no ve los datos del partido (regla nº 1 de `CLAUDE.md`). Esto lo ejecuta una persona en local y
pega solo los agregados:

| qué | quién | cuándo |
|---|---|---|
| `validation/partido/agregados_smart_tagging.py`, `agregados_balon_reinicios.py` y `agregados_jugadores.py` | Manuel | hoy |
| la medida del balón del ATD en todo el partido | Ismael | hoy |
| `validation/partido/silbato_audio.py` | Antonio | hoy |
| `python -m possession.pipeline` y `/evaluar` | Ismael | cada vez que entra una pieza |

**Y cada uno, hoy:** bajar la DFL para poder iterar con su Claude (unos 30 minutos y 2,6 GB, fuera del
repo; paso 1 de [`validation/PASOS.md`](../validation/PASOS.md)):

```bash
python validation/scripts/descargar_datos_abiertos.py dfl
```

## 7. Cómo se trabaja

- **Rama y PR,** como siempre: `/empezar`, `/subir`. Solo Ismael sube directo a `main`.
- **Una PR por mejora de tu pieza,** pequeña. No esperes al lunes para abrir la primera.
- **Cada PR que cambia una pieza lleva:**
  - `python validation/scripts/prueba_pipeline.py` en verde;
  - la tabla del harness, con el control al lado, y el fichero de versiones con el que se midió;
  - la entrada en `docs/decisiones.md` (`/decision`) con los candidatos que escribiste antes de medir.
- **Antes de empezar cada día:** `/actualizar`, para traer lo que hayan mergeado los demás.
- **Si te bloqueas más de una hora,** dilo en el grupo. Quedan dos días y medio.

## 8. Lo que no se hace

- **Dos pipelines completos.** A y B solo se diferencian en la evidencia; el resto se construiría dos
  veces.
- **Probar variantes de limpieza del balón.** Es la pieza que menos mueve la nota, y su árbitro sería una
  degradación que aún no imita al balón del ATD.
- **Vídeo, broadcast y redes** (`docs/investigacion_metodos.md` §3.3): no caben antes del 17.
- **Ajustar nada contra la ventana pública.**
