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
- **Las piezas se enchufan con una interfaz común** (sección 2). No se cambia sin avisar al equipo.
- **Cualquiera del equipo puede contestar, decidir y revisar** (decisión de Ismael, 15/11). Donde este plan
  diga «lo decide Ismael» o «se le pasa a Ismael», léelo como «lo decide el equipo». Quien decide lo apunta
  en `docs/decisiones.md`, con su nombre.
- **Qué versión entra lo decide el harness de la DFL** (sección 4): los 7 partidos abiertos de la
  Bundesliga. Nunca la ventana pública de 5 minutos.
- **Corte: martes 17** (decisión de Ismael del 15/11; antes era el lunes 16 a las 14:00). La hora es
  provisional, las 12:00, hasta que Ismael la confirme. Lo que no haya ganado en el harness para entonces
  no entra. El lunes por la noche se ensaya el congelado; el definitivo es el martes, tras el corte.

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
       tracking.py  ball.py    aprendida.py (B5, 14/11)         temporal.py     pipeline.py
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
`ball.clean`, `aprendida.evidence_k3` (la media de K2 y B5, desde el 17/11; del 14/11 al 17/11, `aprendida.evidence_b5`),
`dead_state.evidence` y `temporal.decode`, que son las que nombra
`pipeline.PIECES`. Todas las versiones reciben el mismo tracking, de solo lectura: una pieza devuelve una
copia (`trk._replace(...)`), nunca lo cambia.

**Lo que da error a propósito,** para que no pase en silencio: una puntuación con `NaN` o infinito en un
frame evaluado, una pieza que no devuelve arrays de forma (n, 3), un parámetro del decodificador mal
escrito, y dos piezas que se contradicen en lo que prohíben. Todas las piezas, también `dead_ball`,
reciben el tracking con el balón ya limpio.

**Reglas de la interfaz:**

- **Funciones puras sobre arrays.** Ninguna pieza abre ficheros, salvo `dead_ball.py` y, desde el 15/11,
  `transiciones.py`, que usan los del partido (el Smart Tagging) solo con las rutas que les pasa
  `pipeline.build`. Así el mismo código corre en el partido y en la DFL: lo que valida el harness es lo que
  se entrega, salvo esas dos capas del partido, que el harness no puede ver. Desde el 16/11 la entrega suma
  además `dead_ball.ball_out` (`pipeline.DELIVERY_LAYERS`): no abre ficheros, pero tampoco corre en el
  harness, porque en la DFL el balón está tapado en los `D` (docs/decisiones.md, 16/11). Desde el 17/11,
  `conjunto.py` lee además sus pesos (`possession/conjunto_pesos.npz`): son parte del código y salen de datos
  abiertos, no del partido, así que corre igual en el harness (docs/decisiones.md, 17/11).
- **Un slot no es un jugador.** Su índice no identifica a nadie a lo largo del partido. El harness
  baraja los slots para que un código que dependa de eso falle allí y no en el partido.
- **Determinista:** sin azar o con semilla fija, y con los empates resueltos siempre igual.
- **Distancias en metros.** El `Tracking` ya viene escalado.
- **Ninguna constante sale del partido ni de la ventana pública.** Los umbrales se fijan en la DFL. Un
  valor por defecto que aún no se ha ajustado se marca como «sin ajustar» en el código.
- **Solo numpy y pandas en el pipeline.** Si entrenas un modelo, sus coeficientes van escritos en tu
  módulo y el script que los calcula, en `validation/`, con semilla fija. Una dependencia nueva la decide
  Ismael. La excepción son los pesos de la red de K2 (36.260 por juego), que no caben como texto: van en
  `possession/conjunto_pesos.npz` (`CONTRIBUTING.md` §7), y la red se entrenó con torch fuera del pipeline.

**Comprobación de que no has roto nada** (sin datos del partido; Claude puede ejecutarla):

```bash
python validation/scripts/prueba_pipeline.py
```

## 3. Tu pieza

**Desde el 15/11, cada bloque empieza por «Tareas desde el 15/11».** Salen de la revisión externa
([`revision_externa_2026-11-15.md`](revision_externa_2026-11-15.md)), repartidas por pieza. Antes de usarla:

- **Sus medidas (anexo A) son de fuera:** sus scripts no están en el repo y nadie del equipo las ha
  repetido. Sirven para ordenar el trabajo, no para decidir qué entra.
- **Lo que compara con las notas oficiales del baseline o con la tabla de retrasos** sale de la GT privada.
  Es descriptivo y no elige nada mientras la organización no conteste (D21).
- **El corte pasa al martes 17** (decisión de Ismael del 15/11). Hora provisional, las 12:00: ver la
  sección 5.
- **Lo demás no cambia:** regla escrita y subida antes de medir, rama nueva desde `main`, PR, y nada elegido
  con la ventana pública.

### Ismael: esqueleto, harness e integración

**Tareas desde el 15/11** (revisión externa, P3, P4 y P5):

1. **Congelado sin sorpresas.**
   - Fijar `numpy` y `pandas` con `==` en `requirements.txt` y apuntar la versión de Python (la excepción
     prevista en `CLAUDE.md`).
   - Reproducir el CSV en un entorno limpio con esas versiones y, si se puede, con Python 3.11.
   - Que el comando documentado escriba `<NOMBRE_EQUIPO>.csv`: hoy el nombre por defecto es `equipo_v0`.
2. **`possession/io.py` se salta en silencio las líneas mal formadas.** Con un ATD truncado saldría una
   entrega válida y distinta. Primero, que el pipeline imprima cuántas líneas se saltó, y ejecutarlo: nadie
   sabe cuántas son hoy. Solo si sale 0, convertirlo en error.
3. **`possession/pipeline.py`:** no dejar el CSV con el nombre bueno si hay piezas en conflicto, y que el
   resumen imprima cuántas rachas hay de menos de 12 y de 25 frames (lo pide el criterio del 13/11).
4. **Apuesta B, una sola ronda de reentrenamiento,** con tres candidatos escritos antes de medir:
   - B5 sin las ventanas de 151 frames;
   - B5 con peso 5 en los frames a ±2 s de un cambio de equipo;
   - B5 con dos rasgos nuevos: el evento de toque medido a la escala del suavizado (anexo A.4 de la
     revisión), con signo, en ventanas de 13 y de 51 frames.

   Se mide en el harness frente a `main`, con `--eventos` y con los criterios 2 y 3 de B5. **Regla de
   parada:** si los tres empatan, se cierra la evidencia de equipo y se apunta en `docs/decisiones.md`.
   De paso: un slot duplicado cuenta doble en los núcleos de B5 (`possession/aprendida.py`).
5. **Dos preguntas a la organización,** que envía Ismael:
   - D21: si se pueden usar las notas publicadas del baseline y la tabla de retrasos para elegir entre dos
     convenciones de etiquetas de datos externos;
   - cómo se construyen las ventanas `SET PIECES` del Smart Tagging y dónde cae el reinicio dentro de ellas.
6. **Si se va a citar el anexo A de la revisión,** sus scripts tienen que entrar en `validation/scripts/` y
   repetirse aquí.
7. **Decisiones que son de Ismael y condicionan tareas de otros:**
   - la hora del corte del martes (provisional, las 12:00);
   - si se reabre la decisión del 13/11 («la falta de balón no es `D`») para puntuar todos los huecos largos
     (tarea 5 de Manuel);
   - si una medida con el `D` propio puede cambiar un valor por defecto (tarea 2 de David);
   - si la limpieza del balón se enciende (hoy, no).

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
degradación estén comprobados. Se abandona en el corte si no ha ganado. Medida el 14/11:
`validation/resultados/2026-11-14_apuesta_b.md`.

### David: decodificador (`possession/temporal.py`)

**Tareas desde el 15/11** (revisión de la PR 9 y revisión externa, P6):

1. **Pendiente de la PR 9, en una PR corta:**
   - `blocks = tuple(blocks)` al entrar en `_prepare`: con un generador, `decode` devuelve todo `X` sin dar
     error. Hoy nadie lo llama así, pero es la función de la entrega;
   - una prueba propia, `validation/scripts/prueba_decodificador.py`, y la fila de `diagnostico_spell.py` en
     `validation/README.md`.
2. **Medir los costes del `D` con el `D` propio. Solo medir.**
   - `to_dead` y `from_dead` en 12, 25 y 50, en un fichero de `validation/harness/versiones/` escrito antes.
   - Con `python validation/harness/puntuar.py --versiones <fichero> --d propio` y con
     `python validation/apuesta_b/d_propio.py --versiones <fichero>`, que mide además con el balón a la
     vista en los `D`. Los dos modos acotan lo que no se puede medir.
   - Cuando Ana añada la opción de escala a su pieza (su tarea 2), repetirlo con la escala a 0,5.
   - **Es descriptivo:** un número con el `D` propio no decide (§4), y la escala de B5 se eligió con coste
     25. Si algo gana en los dos modos y con las dos convenciones, se lleva al equipo, que decide.
3. **No hace falta más:** el coste de cambio, las duraciones mínimas y la poda ya empatan.

Los textos de la PR 9 que había que corregir ya están corregidos en `main` (`05b6d98`).

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
- **Qué evidencia hay (14/11, de noche):** la de `main` es B5, la apuesta B de Ismael
  (`aprendida.evidence_b5`): la evidencia aprendida de B2 más el +1 del jugador más cercano. Entró porque
  cumplió los tres criterios fijados antes de medir (`docs/decisiones.md`). Da empujones de tamaño
  variable, con una escala elegida para el coste 25 de hoy y con la pieza de `D` de Ana dentro. En los
  eventos humanos pierde en las recuperaciones (70 frente a 84): es lo que hay que mirar al ajustar los
  costes.
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

**Tareas desde el 15/11** (revisión de la PR 8 y revisión externa, P2). Todas en `possession/dead_ball.py`,
una capa cada vez y en este orden:

1. **El final de la parada, en la reaparición del balón.** Hoy la capa del hueco puntúa `D` hasta el
   inicio de la ventana `SET PIECES`. Medir antes, con agregados y regla previa, dónde cae el reinicio:
   cuándo vuelve a verse el balón y cuándo el modelo de Ana pasa de parado a juego, contado desde el inicio
   y desde el fin de la ventana. Si cae en un sitio fijo con poca dispersión, la capa deja de puntuar ahí.
2. **El balón visto fuera de las líneas:** puntuación de `D` en los frames en que el balón se ve más de
   1 m fuera. El 12/11 se midió que es el 4,2 % de los frames con balón.
3. **Antes de tocar el principio del hueco, el agregado que falta:**
   - de los frames que cambian de etiqueta con la capa, cuántos caen en los primeros 5 s de cada hueco;
   - un histograma grueso de la distancia entre el inicio de cada hueco y el inicio del `D` que sale del
     decodificador.

   Solo si eso lo apoya, más peso al principio del hueco. Hoy el modelo de Ana ve `D` en el 60,9 % de esos
   5 s: un peso alto ahí puede forzar `D` en juego.
4. **Un ancla de juego vivo en el saque:** prohibir `D` en el frame del saque de cada parte (un frame en
   `allowed`). En la misma PR, para que el fichero tenga un solo cambio abierto.
5. **No entra salvo que Ismael reabra la decisión del 13/11:** puntuar `D` en todos los huecos largos,
   también sin un reinicio delante. Es «la falta de balón como `D`», que está descartada con medidas.
6. **Retirado de momento: el equipo que reanuda.** La revisión externa midió en la DFL que `main` falla el
   equipo en el primer segundo tras el reinicio en el 5,5–5,7 % de los casos. No lo hemos repetido, pero
   baja a «si sobra tiempo».
7. **De la revisión de la PR 8:** tapar con «< 5» las celdas de menos de 5 casos en tu script del partido.

**Cómo se mide cada capa:** no se puede en la DFL. Como la capa del hueco: regla escrita y subida antes
de ejecutar, el modelo de Ana como juez, el placebo desplazado y la entrega regenerada dentro de la banda
(del 15 al 60 % de `D` y 250 paradas como mucho). Si se enciende la limpieza de Antonio, se repite.

Los comentarios de tu fichero que había que corregir ya están corregidos en `main` (`05b6d98`).

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

**Tareas desde el 15/11** (revisión externa, P3, P5 y P6):

1. **Las ventanas de tu pieza cruzan el principio de cada tramo evaluado**
   (`dead_state.window_mean`). Con ventanas de hasta ±2 s, los primeros segundos de la 1ª parte reciben
   evidencia de los jugadores parados antes del saque. En la DFL no pasa, porque antes de cada parte hay un
   hueco vacío: es una diferencia entre lo que valida el harness y lo que se entrega.
   - Recortar las ventanas al tramo evaluado.
   - Comprobar con `validation/scripts/d_estado/medir.py` que en la DFL no cambia nada, y con
     `entrenar.py --comprobar` que los coeficientes siguen saliendo.
   - Cambia un poco la entrega: Ismael la regenera.
2. **Una opción de escala en `dead_state.evidence`,** con 1 por defecto, para que David pueda medir la
   escala a 0,5 con el `D` propio (su tarea 2). El valor por defecto no cambia.
3. **Apuntar la versión de `scikit-learn`** con la que entrenaste (pendiente de la PR 5).
4. **Documento técnico,** desde el lunes y con Ismael. Además de lo previsto, tiene que declarar:
   - el entrenamiento con la DFL, citando a Bassek et al. (2025) y la licencia CC BY 4.0;
   - el uso de un LLM para escribir código y documentación;
   - el uso del Smart Tagging y de las constantes de saque de `starter/load_smart_tagging.py`;
   - que en el repo hay agregados del partido (recuentos y porcentajes), nunca valores por frame;
   - qué nivel cabe esperar y por qué el número del harness es optimista, con la cautela del principio de
     esta sección.

**Qué hay (14/11 por la noche):** tu modelo E2, en `main` desde la PR 5. Opina en la columna `D` con
los jugadores, y los agregados del ATD dicen que se traslada (`validation/resultados/2026-11-14_d_estado.md`
y `2026-11-14_agregados_jugadores_atd.md`). La entrega `equipo_v1` ya lo lleva. Los puntos de abajo son
el plan con el que se hizo.

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

**Tareas desde el 15/11** (revisión externa, P1 y P7):

1. **¿El balón del ATD llega con retraso?** El harness suaviza el balón con una media centrada, y nadie ha
   medido si el suavizado del ATD es centrado o va con retraso. Unos 12 frames de retraso costarían más que
   cualquier mejora medida hasta ahora.
   - **La medida:** en los tramos en que un jugador lleva el balón (el mismo equipo es el más cercano a
     1,5 m o menos durante 1 s o más), el desfase que maximiza la correlación entre la velocidad del balón
     y la del jugador más cercano.
   - **Primero se calibra en la DFL** (`validation/scripts/`, lo puede ejecutar Claude): con el balón
     suavizado centrado tiene que dar 0 ± 2 frames y, con una media móvil hacia atrás de 25 frames,
     +12 ± 2. Si no los separa, no se ejecuta en el partido.
   - **Después, el recuento en el partido** (`validation/partido/`, lo ejecutas tú, solo agregados), con
     estos candidatos escritos antes:
     1. si el desfase es de 3 frames o menos en valor absoluto, no se toca nada;
     2. si es de 4 o más, una variante en `possession/ball.py` que desplaza el balón ese desfase. `clean` no
        cambia hasta que lo decida el equipo;
     3. si los jugadores también pudieran venir con retraso y no se puede separar, no se toca y se apunta.
   - **La latencia de la ventana pública no sirve de puerta:** en nuestras entregas ha salido −6,0
     (`equipo_v1`) y +2,4 (`equipo_v3`) frames, con 5 parejas cada vez. No dice nada.
2. **Lo último, en marcha desde el 15/11: las fases del Smart Tagging como pista de equipo** en los
   frames sin balón. Necesita el Smart Tagging, así que no va en `candidates.py`: sería un módulo aparte
   que enchufa Ismael. Antes, un agregado del partido con regla previa: en los frames de control claro,
   con qué frecuencia coincide el equipo de la fase con el del más cercano, frente a las fases desplazadas.
   Si no llega al 80 % o no dobla al placebo, no entra.
3. **Cerrado:** la limpieza del balón queda arreglada y apagada (PR 7), y tus textos de la PR 7 ya están
   corregidos en `main` (`05b6d98`). No hace falta ninguna PR de seguimiento.

**Qué hay:** desde el 14/11 por la noche, la pieza de equipo de la entrega es B5 (`aprendida.evidence_b5`,
la apuesta B), no N1. Para entrar, un candidato tuyo tiene que ganar a B5 en el harness. N1 sigue en
`candidates.evidence`; el control del harness sigue siendo el baseline (N1 con voto de ±50).

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
| **lunes 16** | cada pieza sigue iterando; las PR entran según ganan. Documento técnico en marcha. **Por la noche, ensayo de congelado:** regenerar la entrega con lo que haya en `main` y reproducirla byte a byte en una máquina limpia |
| **martes 17, 12:00** (hora provisional) | **corte:** lo que no haya ganado no entra |
| **martes 17, tarde** | congelar; reproducir byte a byte; repo público, validar el fichero exacto y enviar con margen. Límite: 23:59 CET |

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
