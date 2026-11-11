# Pasos para completar el experimento 0 y lo que viene después

> **Para quién:** quien haga el experimento, y su Claude. Léelo entero antes de empezar.
>
> **De dónde sale:** el plan y su porqué están en [`docs/investigacion_metodos.md`](../docs/investigacion_metodos.md).
> Aquí está la parte práctica: qué hacer, en qué orden, qué apuntar y qué dudas resuelve cada paso.
>
> **Qué manda:** por decisión de Ismael (11/11), donde `CLAUDE.md` o `docs/GUIA_EQUIPO.md` digan otra
> cosa sobre la validación externa o sobre la política de `X`, manda este plan. Esos documentos se
> escribieron antes de planear este paso.

## Resumen

| paso | qué | datos | quién lo ejecuta | tiempo | prioridad |
|---|---|---|---|---|---|
| 0 | preparar copia, rama, entorno y carpeta de datos abiertos | — | cualquiera | 30 min | obligatorio |
| 1 | descargar la Bundesliga | abiertos, 2,6 GB | cualquiera, Claude incluido | 30 min | obligatorio |
| 2 | **experimento 0:** ¿el flag de la Bundesliga se comporta como el del reto? | Bundesliga | cualquiera, Claude incluido | medio día | obligatorio |
| 3 | el Barça como local: paradas y posesiones en LaLiga | abiertos (eventos) | cualquiera, Claude incluido | medio día | recomendado |
| 4 | banco de pruebas: Barça–Real Madrid de 2019 con tracking automático | abiertos | cualquiera, Claude incluido | 1 día | opcional |
| 5 | perfil del ATD | **del partido** | **solo una persona en local**; Claude escribe el script, nunca lo ejecuta | 2 h | necesario antes de degradar |
| 6 | lo que viene después | — | — | — | — |

Los pasos 2, 3 y 5 se pueden hacer a la vez, por personas distintas. El 4 es para quien acabe antes.

Cada paso dice qué **dudas** resuelve (D1…D21). Están todas en la [tabla del final](#dudas-abiertas).
Quien resuelva una, apunta la respuesta en su fichero de resultados con el número de la duda.

## Reglas para todos los pasos

- **Regla nº 1 (`CLAUDE.md`).** Los pasos 0 a 4 solo usan datos abiertos de **otros** partidos: Claude
  puede leerlos y ejecutarlos. El paso 5 lee datos del partido: Claude escribe el script, una persona lo
  ejecuta y pega solo agregados.
- **Los datos abiertos van fuera del repo y lejos de los del partido.** Por defecto, en
  `~/mtah2027-datos-abiertos` (o donde diga `MTAH_OPEN_DATA_DIR`). Nunca dentro de `MTAH_DATA_DIR`,
  nunca en una carpeta llamada `mtah2027-data` y nunca dentro del repo. El script de descarga se niega a
  hacerlo.
- **Ningún fichero de datos entra en git,** tampoco los abiertos: las licencias no dejan redistribuirlos
  y pesan gigas. Se suben los scripts y los resultados agregados.
- **Nada sobre el partido del reto de fuentes humanas.** Por ejemplo, nada de datos de LaLiga 2024-25
  que incluyan el Barça–Athletic de la jornada 2, ni siquiera agregados de temporada (`RULES.md` §2). El
  script de descarga rechaza esa temporada.
- **La ventana pública no se usa para comparar ni para ajustar.** Lo que se calcule con `evaluation/gt/`
  es una comprobación de la métrica, nunca un prior.
- **La tabla oficial de retrasos de `EVALUATION.md` (0,9818 / 0,8933 / 0,6539 con 3 / 8 / 25 frames) no
  decide nada.** `OVERVIEW.md` explica que la organización no publica estadísticas de la GT completa para
  que nadie ajuste contra ellas. La comparación con la tabla se apunta como información y ningún
  parámetro ni la elección de dataset dependen de ella. Ismael lo ha preguntado a la organización y,
  hasta que conteste, es una medida descriptiva más (D21).
- **Git como siempre:** rama y PR (`/empezar`, `/subir`). Nada directo a `main`.

---

## Paso 0. Preparar

1. **Trae lo último de `main`** (`/actualizar`, o `git pull` estando en `main`).
2. **Comprueba que tu copia tiene `CLAUDE.md` y `.claude/settings.json`.** Llevan la regla nº 1 y el
   bloqueo de los datos del partido. Si no están, **no empieces** y avisa a Ismael: el commit de la
   documentación todavía no ha llegado a `main`.
3. **Crea la rama:** `/empezar experimento 0` (sale `exp/experimento-0`).
4. **Entorno:** el de siempre (`requirements-starter.txt`, con kloppy 3.18.0). Para comprobarlo:
   ```bash
   python -c "import kloppy; print(kloppy.__version__)"
   ```
5. **Carpeta de datos abiertos** (si no quieres la de por defecto):
   ```powershell
   [Environment]::SetEnvironmentVariable("MTAH_OPEN_DATA_DIR", "$HOME\mtah2027-datos-abiertos", "User")
   ```
   ```bash
   export MTAH_OPEN_DATA_DIR=~/mtah2027-datos-abiertos     # en ~/.zshrc o ~/.bashrc
   ```
6. **Dónde va cada cosa:** los scripts nuevos del experimento, en `validation/experimento0/`; los
   resultados, en `validation/resultados/` (ver su `README.md`).

## Paso 1. Descargar la Bundesliga

**Qué es.** 7 partidos de 1ª y 2ª Bundesliga 2022-23 (Bassek et al., 2025, CC BY 4.0). Tracking TRACAB
a 25 Hz revisado por operadores y, en cada frame, `BallPossession` (1 local, 2 visitante) y
`BallStatus` (0 inactivo, 1 activo). También eventos. Es el único dataset abierto con el mismo tipo de
etiqueta que la GT del reto.

```bash
python validation/scripts/descargar_datos_abiertos.py dfl
```

- Baja 21 ficheros (2,63 GB) y comprueba el md5 de cada uno. Si se corta, se relanza y sigue.
- Para probar antes sin los ficheros grandes: `--solo-ligeros` (5 MB).
- **No uses `sportec.load_open_tracking_data` de kloppy 3.18.** Descarga de un host de figshare que el
  11/11 respondía a los scripts con un desafío antirrobots. El script usa otro host de figshare que sí
  funciona. Si también fallara, el espejo `huggingface.co/datasets/pysport/idsse-data` tiene los mismos
  ficheros con los mismos nombres. (D10)

**Por cada partido** hay tres ficheros: `DFL_02_01_matchinformation_…` (metadatos), `DFL_03_02_events_raw_…`
(eventos) y `DFL_04_03_positions_raw_observed_…` (tracking, 350–420 MB).

## Paso 2. Experimento 0

**Pregunta:** ¿el flag por frame de la Bundesliga se comporta como pide `CHALLENGE.md`? Si sí, la
Bundesliga sirve para entrenar y para elegir umbrales. Si no, sabremos en qué se diferencia y cómo
corregirlo al derivar las etiquetas.

**Qué decide y qué no:** deciden 2a, 2c, 2d y 2e, que comparan el flag con la definición del reto. La
huella de retrasos (2b) se apunta como información y no decide nada (D21).

Hazlo **un partido cada vez**. Leer un XML de posiciones puede tardar minutos y ocupar varios GB de
memoria. Para probar el código, `limit=` devuelve solo los primeros frames, aunque puede que kloppy lea
el XML entero igualmente.

### 2a. Etiquetas y descripción

Fragmento orientativo, **sin probar** con los ficheros grandes:

```python
import numpy as np
from kloppy import sportec

ds = sportec.load_tracking(
    meta_data=".../DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WMX.xml",
    raw_data=".../DFL_04_03_positions_raw_observed_DFL-COM-000001_DFL-MAT-J03WMX.xml",
    only_alive=False,          # imprescindible: por defecto descarta el balón inactivo
)
df = ds.to_df()                # period_id, frame_id, ball_state, ball_owning_team_id, ball_x...
local = ds.metadata.teams[0].team_id
etiqueta = np.where(df["ball_state"] == "dead", "D",
                    np.where(df["ball_owning_team_id"] == local, "H", "A"))
```

- **Coordenadas:** para este paso, las de por defecto (metros, origen en el centro), que son las que
  hacen falta para medir distancias.
- **Comprobaciones antes de seguir:**
  - `ds.metadata.teams[0]` es el equipo local (los eventos de la DFL lo confirman: kloppy los lee con el
    local primero);
  - `ball_state` solo toma `"alive"` y `"dead"`;
  - dentro de cada parte, `frame_id` avanza de 1 en 1. kloppy salta los frames sin balón, y un salto
    falsearía las duraciones (D8). Apunta cuántos saltos hay;
  - con el balón inactivo, kloppy pone el visitante en `ball_owning_team_id` aunque no haya dato. Por
    eso la etiqueta mira primero `ball_state`.
- **Guarda las etiquetas** en un CSV `frame,label` en tu carpeta de datos abiertos, **fuera del repo**,
  con un frame `X` entre las dos partes. Luego:
  ```bash
  python validation/scripts/perfil_etiquetas.py <carpeta>/etiquetas_J03WMX.csv
  ```
  Da el reparto H/A/D, las posesiones por minuto, sus cuantiles de duración, la fracción de posesiones
  cortas, las paradas y la huella de retrasos.
- **Apunta** una fila por partido en la plantilla (`resultados/_plantilla_experimento0.md`). Lo que
  resuelve: el número de paradas y la fracción de tiempo muerto dicen qué cuenta la DFL como inactivo
  (D5). Si sale en torno al 40 % y unas 100 paradas por partido, incluye saques de banda, de puerta y
  córners.

### 2b. Huella de retrasos (solo informativa)

`perfil_etiquetas.py` la da para cada partido, junto a la tabla oficial. Para la de los 7 juntos,
concatena los 7 CSV con un frame `X` entre cada parte y pásale el resultado.

**Se apunta y no se decide nada con ella.** Ni la elección de dataset ni la poda ni la duración mínima
dependen de esta comparación hasta que la organización conteste la consulta de Ismael (D21). Sí es útil, y no depende de la GT del
reto, comparar huellas entre fuentes abiertas: flags de la DFL, eventos de la DFL (2f) y eventos del
Barça (paso 3).

### 2c. Cuándo cambia el flag de posesión

Para cada cambio `H`↔`A` con el balón vivo a los dos lados:

- **distancias en el frame del cambio:** del balón al jugador más cercano del equipo nuevo y del antiguo,
  en metros;
- **desfase respecto al toque:** frames entre el cambio y el toque más cercano de un jugador del equipo
  nuevo (con signo: negativo si el flag cambia antes del toque);
  - un **toque** es un pico de aceleración del balón (Link y Hoernig usan ≥ 4 m/s²) o un cambio brusco
    de dirección o velocidad (`databallpy`: 10° o 5 m/s) con el jugador a menos de ~1,5 m;
  - calcula la velocidad a partir de las posiciones (metros por frame × 25). La columna de velocidad de
    la DFL podría venir en km/h;
- **qué fracción de cambios tiene un jugador del equipo nuevo a menos de 1,5 m del balón en ±1 s.**

Apunta la mediana y los percentiles 10 y 90. Resuelve D3 y D4. Un desfase positivo sistemático de 0,3 a
1 s apunta a que el flag lo marca una persona (D7).

### 2d. Cuándo pasa a inactivo

Para cada paso de vivo a muerto:

- **dónde está el balón:** dentro o fuera del campo y a cuántos metros de la línea más cercana (las
  dimensiones están en `ds.metadata.pitch_dimensions`);
- si el balón cruzó una línea en los 3 s anteriores, **cuántos frames pasan** desde que la cruza hasta
  que cambia el flag;
- **duración de la parada,** por tipo aproximado: fuera por banda (saque de banda), fuera por línea de
  fondo (córner o saque de puerta), dentro del campo (falta, fuera de juego, lesión).

Resuelve D5 y D6.

### 2e. Cuándo vuelve a activo

Para cada paso de muerto a vivo:

- frames entre el cambio de flag y el primer frame en que el balón supera ~2 m/s (dentro de ±3 s);
- **qué equipo tiene el flag** durante la parada y si coincide con el que reanuda.

Resuelve D6. Ayuda a decidir cómo nombrar el equipo al volver de un `D`.

### Decisión del paso 2

La Bundesliga vale como proxy principal si su flag se comporta como pide `CHALLENGE.md`:

- `D` cubre todo balón fuera de juego, también banda, fondo y córner (2a, 2d);
- la posesión cambia con un control del rival, no con un toque (2c);
- se queda con el último equipo mientras el balón está suelto o en un pase fallado (2c, 2f).

Si algo no encaja, se apunta en qué difiere y se corrige al derivar las etiquetas, o se baja su peso.
Resuelve D2 a D6.

### 2f. Opcional: eventos frente a flags

- Deriva etiquetas de los eventos de la DFL (`sportec.load_event(event_data=..., meta_data=...)`; kloppy
  3.18 los lee, comprobado). kloppy no pone `ball_owning_team` en estos eventos: usa el equipo de cada
  evento con balón.
- Aplica las mismas reglas que en el paso 3. Calcula su huella y el `spellF1` contra las etiquetas de
  los flags.
- Ojo: los autores miden un desfase de −0,37 ± 1,82 s entre eventos y tracking. El `spellF1` entre las
  dos fuentes medirá sobre todo ese desfase, pero **la huella no depende de él**.
- Sirve para dos cosas: separar el efecto de la convención (flags frente a eventos) en el paso 3 (D11) y
  acotar el techo (sección 7.3 del informe).

**Al acabar el paso 2:** copia `resultados/_plantilla_experimento0.md` a
`resultados/AAAA-MM-DD_experimento0.md`, rellénala y súbela por PR. Si sale una decisión, apúntala con
`/decision`.

## Paso 3. El Barça como local: paradas y posesiones en LaLiga

**Por qué.** No hay tracking abierto de ningún partido del Barça con flags por frame (inventario en
[`resultados/2026-11-11_inventario_datos_barca_local.md`](resultados/2026-11-11_inventario_datos_barca_local.md)).
Lo que sí hay son eventos de 264 partidos del Barça como local en el Camp Nou. No sirven para la
convención del flag, pero sí para lo que depende de la liga y del equipo: cuántas paradas hay, cuánto
duran y cómo de cortas son las posesiones.

**Antes de descargar:** el acuerdo de StatsBomb pide registrarse en su web (nombre y email), no
redistribuir los datos y poner su logo en lo que se publique, y prohíbe el uso comercial (D16). Que se
registre quien lo use; Claude no puede hacerlo por nadie.

```bash
python validation/scripts/descargar_datos_abiertos.py statsbomb-barca-local
```

Por defecto baja las 6 últimas temporadas (2015-16 a 2020-21, 109 partidos, unos 0,4 GB). Con
`--temporadas todas`, los 264. Con `--con-360`, también los 360 de 2020-21.

**Etiquetas por frame a partir de los eventos** (reglas recomendadas, a 25 fps y por parte):

| qué | regla |
|---|---|
| tiempo | `timestamp` es el tiempo desde el inicio de cada parte: frame = `round(segundos × 25)`. Cada parte por separado, con un frame `X` entre ellas |
| empieza un `D` | evento con `out: true` (el balón sale tras esa acción, al final de su `duration`), pase con resultado `Pass Offside`, `Foul Committed` seguido de un reinicio (si se juega la ventaja no hay parada), `Injury Stoppage`, gol, `Half End` |
| termina el `D` | el siguiente reinicio: pase de tipo `Throw-in`, `Corner`, `Goal Kick`, `Free Kick` o `Kick Off`; tiro de tipo `Free Kick` o `Penalty`; `Referee Ball-Drop` |
| antes del primer saque de cada parte | `D` |
| equipo con el balón vivo | `possession_team` del evento; cambia en el primer evento de una posesión nueva de StatsBomb con otro equipo |

No es la convención de la GT (es otra fuente y otra definición), y los tiempos de los eventos llevan
error. Úsalo para recuentos, duraciones y huella, no para fronteras exactas.

**Qué medir**, por partido, y luego la mediana y el rango intercuartílico:

1. `perfil_etiquetas.py` sobre las etiquetas de cada partido: reparto H/A/D, posesiones por minuto,
   cuantiles de duración y huella;
2. reinicios por tipo (saques de banda, faltas, saques de puerta, córners, saques iniciales, penaltis) y
   duración de la parada por tipo (desde que empieza el `D` hasta el reinicio);
3. lo mismo separando 2015-18 y 2018-21, para ver si cambia con los años.

**Con qué se compara:**

- la huella de los flags de la DFL (paso 2b) y la de los eventos de la DFL con estas mismas reglas (paso
  2f). La pareja "eventos DFL frente a eventos Barça" tiene la misma convención y aísla la diferencia de
  liga y equipo (D11);
- la tabla oficial, solo como información (D21);
- los reinicios del Smart Tagging de nuestro partido: 59 en total (26 saques de banda, 12 córners, 10
  saques de puerta, 5 faltas, 6 saques iniciales, según `DATA.md`). Si en LaLiga hay unos 100 por
  partido, al Smart Tagging le faltan más de 40, sobre todo faltas (D12, D13).

**Opcional:** los eventos de Wyscout de LaLiga 2017-18 (CC BY 4.0, 19 partidos del Barça como local)
permiten contrastar los recuentos con otro proveedor y con una licencia más limpia. Se bajan a mano
desde `https://ndownloader.figshare.com/files/14464685` (`events.zip`, 77 MB).

Resultado en `resultados/AAAA-MM-DD_barca_local_eventos.md`.

## Paso 4. Opcional: banco de pruebas con el Barça–Real Madrid de 2019

**Qué es.** Tracking de broadcast de SkillCorner del Barça–Real Madrid del 18/12/2019 en el Camp Nou:
10 fps, automático y sin corregir, con ~14 de 22 jugadores visibles de media y nada en las repeticiones.
Es el único tracking automático abierto de un partido del Barça en casa. Los eventos del mismo partido
están en StatsBomb.

```bash
python validation/scripts/descargar_datos_abiertos.py clasico-2019
```

- **Lectura** (sin probar con este fichero):
  ```python
  from kloppy import skillcorner
  sc = skillcorner.load(meta_data=".../data_matches_2841_match_data.json",
                        raw_data=".../data_matches_2841_structured_data.json",
                        include_empty_frames=True,   # conserva los frames de repeticiones, sin datos
                        only_alive=False)            # por defecto descarta los frames sin posesión
  ```
- **Primero, su ruido:** calcula los mismos agregados que el perfil del ATD (paso 5): % de frames con
  balón, longitud de los huecos, jugadores visibles, duración de los tracks (`track_id`). Si se parece al
  ATD, este partido sirve para probar el pipeline con ruido real (D14).
- **Etiquetas:** de los eventos de StatsBomb (id 303596) con las reglas del paso 3. Hay que sincronizar:
  SkillCorner da el tiempo de partido por parte (`timestamp`, 0,1 s) y StatsBomb el tiempo desde el
  inicio de cada parte. Se alinean con el saque inicial de cada parte y se comprueba con algunos
  reinicios.
- **Cuando exista el pipeline A:** pasarlo por este partido y puntuarlo contra esas etiquetas. Es una
  prueba de punta a punta con un partido del Barça en casa, no una medida de la nota.
- **Ojo con el permiso (D15):** SkillCorner retiró estos datos de su repo en octubre de 2025. Siguen en
  el historial, y su README pedía citarles. Si Ismael lo ve dudoso, se usa solo como prueba y no para
  decidir nada.

Resultado en `resultados/AAAA-MM-DD_clasico_2019.md`.

## Paso 5. Perfil del ATD (datos del partido: solo una persona)

**Para qué.** Para degradar la Bundesliga hay que saber cómo es el ATD. Sin esto, la degradación es a
ciegas (D18).

- **Claude escribe el script** (`validation/partido/perfil_atd.py`, en una carpeta aparte de
  `validation/scripts/` porque lee datos del partido), que lee el ATD con `games.asset_paths()` e
  **imprime solo agregados**. **Una persona lo ejecuta en local** y pega la salida en
  `resultados/AAAA-MM-DD_perfil_atd.md`. **Claude nunca lo ejecuta.**
- **Qué imprime:** la tabla de la sección 5.5 del informe, con **pocos intervalos y gruesos** y solo
  totales del partido entero:
  - huecos sin balón y rachas con balón en 5 intervalos de duración (< 0,5 s, 0,5–2 s, 2–5 s, 5–15 s,
    > 15 s);
  - fracción de frames sin balón en una tabla de 3 × 3 (densidad de jugadores por tercio del campo);
  - salto de posición del balón tras un hueco, en 3 intervalos de metros;
  - jugadores localizados por frame y duración de los tramos de los slots: cuantiles 10, 50 y 90;
  - porcentaje de saltos imposibles o de balón fuera de [0, 1];
  - temblor de las posiciones: una mediana;
  - porcentaje de frames con balón en los 10 s previos a los `SET PIECES`, todos juntos.
- **Nunca** números de frame, instantes, jugadas concretas ni valores por frame.
- **Si hay duda** de si un agregado es demasiado fino para pegarlo a Claude o para publicarlo, se
  pregunta antes a la organización.

## Paso 6. Lo que viene después

Con el experimento 0 y el perfil del ATD:

1. degradar la Bundesliga y comprobar que se parece al ATD (sección 5.5 del informe);
2. montar el harness con fondo común y comparar las emisiones de nivel 1 (secciones 5.1 a 5.8);
3. con el pipeline A en marcha, contar en el partido los intervalos entre anclas (sección 6.4, D19);
4. comparar decodificadores (sección 5.9);
5. si se usa la regla de Vidal-Codina, leer los umbrales de su anexo (D20).

---

## Dudas abiertas

Lo que todavía no sabemos. Quien resuelva una, apunta la respuesta en su resultado con el número.

| id | duda | por qué importa | cómo se resuelve | paso |
|---|---|---|---|---|
| D1 | ¿La tabla oficial de retrasos está calculada sobre el partido completo? | lo que el informe deduce de ella (cuántas posesiones son cortas) depende de esto | no se puede medir. Se puede preguntar a la organización con un issue en su repo; mientras, es una hipótesis | — |
| D2 | ¿El flag de la DFL se comporta como pide `CHALLENGE.md` (qué es `D`, cuándo cambia la posesión)? | decide si la Bundesliga sirve como proxy principal | medidas 2a, 2c, 2d y 2e; la huella no decide (D21) | 2 |
| D3 | ¿Cuándo cambia el flag de la DFL: en el primer toque del rival, cuando controla o más tarde? | marca cuándo debe cambiar nuestra etiqueta | desfase entre toques y cambios | 2c |
| D4 | ¿El flag de la DFL se queda con el último equipo mientras el balón está suelto o en un pase fallado, como pide el reto? | es la regla del reto | 2c, y contrastar con los eventos en 2f | 2c, 2f |
| D5 | ¿Qué cuenta la DFL como balón inactivo? El artículo habla de interrupciones del árbitro, "por ejemplo tras una falta o durante una sustitución" | en el reto es `D` todo balón fuera de juego, también banda, fondo y córner | número de paradas y fracción de tiempo muerto; posición del balón al pasar a inactivo | 2a, 2d |
| D6 | ¿En qué momento pasa la DFL a inactivo (al cruzar la línea, al pitar, más tarde) y a activo (al golpear el balón)? | fronteras de `D` | desfases medidos | 2d, 2e |
| D7 | ¿Los flags de la GT del reto los marca una persona en directo, un algoritmo o una mezcla? | si es una persona, las fronteras llevan un retraso que nadie puede adivinar exactamente | en el partido, no se puede medir. Pista indirecta: un retraso sistemático del flag de la DFL. Se puede preguntar a la organización | 2c, 2d |
| D8 | ¿Faltan frames en el tracking de la DFL? kloppy salta los frames sin balón | las duraciones saldrían mal | `frame_id` de 1 en 1 dentro de cada parte | 2a |
| D9 | ¿Lee bien kloppy 3.18 la DFL: local en `teams[0]`, `ball_state` con "alive"/"dead", `coordinates="metrica"` cuando haga falta normalizar? | todo lo demás se apoya en la lectura | comprobarlo con el primer partido | 1, 2a |
| D10 | ¿La descarga es estable? El host de figshare que usa kloppy bloquea scripts | reproducibilidad del documento técnico | el script usa otro host; si falla, el espejo de Hugging Face o el navegador | 1 |
| D11 | ¿Son las posesiones del Barça como local más cortas o más largas que las de la Bundesliga, con la misma convención? | si difieren, la duración mínima y la poda elegidas con la DFL no valen tal cual | huella de eventos Barça frente a eventos DFL | 3, 2f |
| D12 | ¿Cuántos reinicios hay por partido en LaLiga con el Barça de local, de cada tipo, y cuánto dura cada parada? | priors del detector de `D` | recuentos y duraciones de los eventos | 3 |
| D13 | ¿Cuántos reinicios de nuestro partido no aparecen en el Smart Tagging? (59 etiquetados frente a unos 100 esperados) | si faltan muchos, el detector de `D` no puede apoyarse solo en los `SET PIECES` | comparar lo esperado (paso 3) con el Smart Tagging; en el partido, solo agregados (paso 5) | 3, 5 |
| D14 | ¿El ruido del tracking de broadcast de SkillCorner se parece al del ATD? | si se parece, el Clásico de 2019 sirve para probar el pipeline con ruido real | comparar con el perfil del ATD | 4, 5 |
| D15 | ¿Se puede usar el partido de SkillCorner que retiraron de su repo? | el documento técnico tiene que citar datos accesibles y con permiso | sigue en el historial y pedían que se les citara; si hay duda, preguntarles o usarlo solo como prueba. Decide Ismael | 4 |
| D16 | ¿El acuerdo de StatsBomb permite usar sus datos en un hackathon con premios? Prohíbe la explotación comercial | si no, hay que tirar de Wyscout (CC BY 4.0) | lo decide Ismael; si hay duda, preguntar a la organización o usar Wyscout | 3 |
| D17 | ¿En Metrica sample-data el balón es `NaN` cuando está fuera de juego? | si es así, allí "sin balón" sí significa muerto, al revés que en el ATD | % de balón ausente dentro y fuera de los tramos `BALL OUT`→`SET PIECE` | opcional |
| D18 | ¿Cómo es el ATD: huecos sin balón, dónde se pierde, jugadores visibles, fragmentación? | sin esto la degradación es a ciegas | perfil del ATD | 5 |
| D19 | ¿Cuántos cambios de posesión ocurren en el partido con el balón oculto? | decide si merece la pena el nivel 2 | recuento de intervalos entre anclas, con el pipeline A | 6 |
| D20 | ¿Qué umbrales de giro y velocidad del balón usa Vidal-Codina? Están en un anexo que nadie ha leído | candidato N3 | leer el PDF del anexo | 6 |
| D21 | ¿Podemos usar la tabla oficial de retrasos para algo más que leer la métrica? `OVERVIEW.md` y `EVALUATION.md` dicen que no publican estadísticas de la GT completa para que nadie ajuste contra ellas, `RULES.md` §2 prohíbe usar la GT completa "or anything derived from it", y lo que se deduce de la tabla son estadísticas de ese tipo. Vale también para la GT sintética de `sensibilidad_metrica.py`, que se calibra con ella | mientras no se resuelva, ningún parámetro, ninguna poda ni la elección de dataset dependen de ella | **consulta abierta:** Ismael decidió el 11/11 preguntarlo a la organización por email y no decidir nada con ello hasta que contesten | — |

**Preguntas a la organización.** D21 ya está preguntada por email (Ismael, 11/11). D1 y D7, y D16 si hay
duda, se pueden preguntar igual o con un issue en https://github.com/metrica-sports/more-than-a-hack-2027,
que es público. Decide Ismael si se hacen.
