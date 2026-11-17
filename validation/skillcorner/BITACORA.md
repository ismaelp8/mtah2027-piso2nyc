# SkillCorner (A-League 2024/25): ¿aguanta B5 con un tracking automático? · bitácora

> Sale de la revisión externa del 15/11 (`docs/revision_externa_2026-11-15.md`, conversación posterior con
> Ismael). Ismael eligió «empieza por SkillCorner como validación». Solo datos abiertos de otros partidos:
> lo puede ejecutar Claude. Solo agregados.

## 1. Por qué

- El harness de la DFL dice que B5 gana al baseline y a N1, pero la DFL es tracking limpio y revisado por
  operadores. El partido es tracking automático. Nadie ha medido si la ventaja de B5 aguanta con un tracking
  automático.
- SkillCorner publica partidos con tracking **automático** de la retransmisión y posesión de equipo por
  frame. Es lo más parecido al ATD que hay abierto.
- **Es una validación, no un entrenamiento.** B5 y E2 se usan con los coeficientes de la entrega (los 7
  partidos de la DFL): nunca han visto estos partidos.

## 2. Los datos

- **Fuente:** https://github.com/SkillCorner/opendata (licencia MIT; piden citar a SkillCorner). 20
  partidos de la A-League 2024/25 en `data/matches.json` (el README dice 10; el repositorio trae 20).
- **Por partido:** `{id}_match.json` (plantillas, campo, partes), `{id}_tracking_extrapolated.jsonl` (10 fps;
  balón con `is_detected`; jugadores con `player_id` e `is_detected`; `possession` con `player_id` y
  `group`), `{id}_phases_of_play.csv` y `{id}_dynamic_events.csv`.
- **El tracking va por Git LFS:** se baja de `media.githubusercontent.com` y se comprueba su sha256 contra el
  puntero LFS.
- **Se guardan fuera del repo,** en `$MTAH_OPEN_DATA_DIR/skillcorner` (por defecto
  `~/mtah2027-datos-abiertos/skillcorner`), con una caché `.npz` al lado.

**Lo que se miró antes de escribir esta regla** (un solo partido, `1886347`, solo recuentos; no se puntuó
ningún método):

- 59.061 frames a 10 fps. En el 26 % no hay tracking (ni jugadores ni balón): la retransmisión enseña otra
  cosa. 14.871 de esos 15.603 frames caen fuera de las fases.
- Balón detectado en 35.750 frames y estimado (`is_detected` falso) en 7.708.
- 22 jugadores por frame de mediana, 15 detectados.
- Las fases de juego («only defined when the ball is in play», README de SkillCorner) cubren 32.127 frames
  en 104 tramos seguidos. Los 103 huecos entre tramos duran 20 s de mediana (p10 6 s, p90 51 s).
- `possession.group` se conoce en 30.645 + 416 frames dentro de las fases. Dentro de las fases falta en 94
  ráfagas de 6 frames de mediana. Coincide con el equipo de la fase en el 85,7 % de los frames.
- 231 cambios directos de `group` entre los dos equipos.

## 3. Las etiquetas (fijadas antes de medir)

- **`D`:** todo frame fuera de las fases de juego.
- **`H` o `A`:** dentro de las fases, el `possession.group` del frame («home team» es `H`). Donde falta,
  se rellena con el último conocido dentro del mismo tramo de juego y, al principio del tramo, con el
  siguiente. Es la regla del reto: con el balón suelto la posesión sigue con el último equipo. Un tramo de
  juego sin ningún `group` se queda sin etiqueta (`X`), para no inventar.
- **Qué convención es:** la de SkillCorner. Su «player possession» exige control («able to do a pass, shot
  or carry»; especificación de sus Dynamic Events). Es una tercera convención, distinta del flag y del
  control de la DFL. Se describe (posesiones por minuto vivo y huella), no se corrige.
- **Las dos partes,** con un hueco de `X` en medio, como en el harness.

## 4. El tracking, en el formato del pipeline

- **De 10 a 25 fps.** Las ventanas del pipeline van en frames a 25 fps (B5: 1, 13, 51 y 151 frames), así
  que hay que pasar a 25 fps. Cada frame a 25 fps toma el instante `j / 25`:
  - posiciones: interpolación lineal entre las dos muestras a 10 fps que lo rodean, solo si las dos
    existen; si no, `NaN`;
  - etiquetas: las de la muestra a 10 fps anterior (escalón).
- **Metros con el origen en una esquina:** se suma la mitad del campo de `match.json` (`pitch_length`,
  `pitch_width`).
- **Jugadores:** un slot por `player_id`, con su equipo de `match.json`. Los slots se barajan a trozos con
  `dfl.barajar_slots`, como en el harness.
- **El balón no se tapa en los `D`.** En la DFL se tapaba porque está congelado y delata la etiqueta; aquí
  no se sabe que lo esté. Se apunta qué parte de los frames `D` tiene balón (descriptivo).

**Condiciones:**

| | balón | jugadores | ¿vota? |
|---|---|---|---|
| «detectado» | solo donde `is_detected` | todos (también los estimados) | sí |
| «detectado, suavizado» | lo mismo con la media móvil de 25 frames del harness (`dfl.media_movil`) | todos | sí |
| «con el estimado» | también el estimado | todos | no |
| «solo jugadores detectados» | detectado | solo `is_detected` | no |

Votan dos porque no se sabe cuánto se parece el balón de SkillCorner, ya pasado a 25 fps, al del ATD.

## 5. Versiones (escritas antes de medir)

| versión | qué |
|---|---|
| control | el baseline oficial: jugador más cercano y voto de ±50 (`puntuar.control`) |
| N1 | la `main` de antes del 14/11: `candidates.evidence`, `dead_state` y Viterbi con coste 25 |
| `main` | la entrega: B5 (`aprendida.evidence_b5` con los coeficientes de los 7 partidos), `dead_state` y Viterbi con coste 25 |

- **`D` oráculo** (decide): el de las etiquetas, con `puntuar.d_oraculo` y `puntuar.imponer_d`, como el
  harness.
- **`D` propio** (descriptivo): cada versión pone el suyo.
- **Métrica:** `spellF1` oficial con los 20 partidos juntos y por partido; bootstrap pareado sobre las
  posesiones (`puntuar.diferencia_bootstrap`, 1.000 remuestreos, semilla fija).

## 6. Regla de lectura (fijada antes de medir)

- **«B5 aguanta con tracking automático»:** `main` gana al control con `D` oráculo por 0,03 o más con los
  20 partidos juntos, en 17 de 20 partidos o más (la proporción de 6 de 7) y con el intervalo por encima de
  cero, en las dos condiciones que votan.
- **«La ventaja de B5 sobre N1 aguanta»:** lo mismo, `main` frente a N1.
- **Si `main` no gana al control:** es una alarma. Se avisa a Ismael antes de cualquier otra cosa: B5 podría
  no trasladarse al ATD, y la entrega tendría que pensarse otra vez.
- **Si `main` gana al control pero no a N1:** la ventaja de B5 sobre N1 sería cosa de la DFL. Se avisa a
  Ismael; no cambia la entrega por sí solo.
- **Descriptivo, no decide:** el `D` propio, las condiciones sin voto, las posesiones por minuto vivo y la
  huella de retrasos de las etiquetas, y qué parte de los `D` tiene balón.
- **Después de ver los números no se cambia nada de lo de arriba:** ni las etiquetas, ni las condiciones,
  ni la regla.

## 7. Resultado

15/11, con los 20 partidos; detalle y salida en `validation/resultados/2026-11-15_skillcorner.md`.

- **«B5 aguanta con tracking automático»: sí** [medido]. `main` frente al control: +0,131 y +0,135, en 20
  de 20.
- **«La ventaja de B5 sobre N1 aguanta»: sí** [medido]. `main` frente a N1: +0,059 y +0,065, en 19 de 20.
- **Sin voto:** con solo los jugadores detectados, la ventaja sobre N1 baja a +0,028 (17 de 20).
- **Discrepancia:** esta sección pide 17 de 20 y la ejecución aplicó 18 de 20, más estricto. El veredicto
  es el mismo con los dos; `medir.py` se corrigió después para aplicar el 17 escrito.

## 8. Corte de entrenamiento y examen (15/11, después de medir los 20)

Lo fija Claude para cuando esto suba a `main`. La medida de la sección 7 ya estaba hecha con los 20 juntos
y no se repite ni se parte: ese resultado se queda como está.

A partir de aquí, entrenar un modelo o mirar errores solo con estos 10:

`1874553`, `1899585`, `1927964`, `1959846`, `1996435`, `2006229`, `2007448`, `2010085`, `2013725`, `2016236`.

Estos otros 10 son examen y no se tocan. No entran en un entrenamiento, ni en un ajuste, ni en una lista
de errores:

`1886347`, `1925299`, `1953632`, `1986691`, `1996436`, `2006363`, `2007721`, `2011166`, `2015213`, `2017461`.

Están en `lector.py` como `ENTRENAMIENTO` y `EXAMEN`. Un script nuevo que entrene o inspeccione errores
tiene que llamar a `exigir_solo_entrenamiento` antes de leerlos. `medir.py` no lo llama: reproduce la
medida de la sección 7, que es anterior a este corte.

### Usos del examen

Cada vez que se abre `EXAMEN`, se apunta aquí. **`CLAUDE.md` lo permite una vez por candidato**, así que esta
tabla lleva la cuenta por candidato, no un único uso global.

| fecha | candidato | quién lo autorizó | resultado |
|---|---|---|---|
| 16/11/2026 | «cortas a `D`» (idea 1.3), corte de 125 frames, con `validation/scripts/cortas_a_d_skillcorner.py --examen --confirmo-el-unico-uso` | Ismael dio el permiso el 16/11; Manuel lo autorizó en el momento | **Pasa:** +0,009 (10 de 10) con «detectado» y +0,008 (10 de 10) con «detectado, suavizado», sobre un umbral escrito antes de +0,005 y 7 de 10 |
| 17/11/2026 | B12 (GRU bidireccional, `aprendida.evidence_b12`), con `validation/secuencia/skillcorner.py --examen b12 --confirmo-el-unico-uso` | Ismael, en el momento (17/11, 10:20) | **No pasa:** con el `D` de las etiquetas, +0,004 (6 de 10) con «detectado» y +0,007 (7 de 10) con «detectado, suavizado»; con el propio, +0,006 y +0,009 (7 de 10). Falla una celda del umbral escrito antes (+0,005 y 7 de 10 en las cuatro). B12 se queda cerrado |

El detalle está en `docs/decisiones.md`, entrada «la idea 1.3 («cortas a `D`») se desaparca».

**Pendiente de que lo decida el equipo:** si cambiar un parámetro de una idea ya examinada (por ejemplo el
mismo «cortas a `D`» con el corte de 75 frames) cuenta como **candidato nuevo**, con su propio uso, o como
**ajuste del mismo**, que es la fuga de la que el examen protege. Hasta que se decida, no se abre el examen
para una variante de un candidato ya examinado.
