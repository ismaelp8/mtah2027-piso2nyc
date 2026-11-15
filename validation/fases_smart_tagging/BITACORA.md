# Fases del Smart Tagging como pista de equipo · bitácora

Es la tarea 2 de Antonio en `docs/PLAN_ENTREGA.md` §3 (P7 de `docs/revision_externa_2026-11-15.md`). Ismael
dio el sí el 15/11 (`docs/decisiones.md`, «Antonio empieza su tarea 2»). Todo lo de las secciones 1 a 5 está
escrito **antes de ejecutar nada** en el partido.

## 1. Por qué (Antonio Azuero, con Claude · 15/11/2026)

- **Las fases son la única información de equipo que la entrega no usa.** Cubren el 68,1 % de los frames
  evaluados [medido, `validation/resultados/2026-11-14_agregados_balon_muerto.md`].
- **No se puede medir en la DFL,** que no tiene Smart Tagging. Por eso hay un recuento del partido con una regla
  previa, como pide el plan.
- **Lo que puede entrar es poco** (plan y decisión del 15/11): un empujón pequeño, por debajo de 1 por frame, al
  equipo de la fase vigente, **solo en los frames sin balón**. Un uso más amplio lo decide Ismael.
- **Una medida en la Bundesliga dice que la pista «este equipo tiene el balón» apenas ayuda con ese alcance.**
  Por eso el número que más interesa es el de las transiciones (sección 3.3): cuántos inicios de «Attacking
  Transition» tienen ya un cambio nuestro a ese equipo a menos de 2 s.

## 2. La tabla: qué equipo tiene el balón en cada fase

Sale de `OVERVIEW.md`: `Team` es el equipo que hace la fase.

| código | equipo con el balón |
|---|---|
| `BUILD UP`, `PROGRESSION`, `CREATING CHANCES`, `ATTACKING TRANSITION`, `LONG BALL`, `BALL IN FINAL THIRD`, `BALL IN THE BOX`, `PLAYERS IN THE BOX` (ataque) | el de la fase |
| `DEFENDING IN ATTACKING THIRD`, `DEFENDING IN MIDDLE THIRD`, `DEFENDING IN DEFENSIVE THIRD`, `DEFENSIVE TRANSITION` (defensa) | el otro |
| `SET PIECES`, `GOALS` | fuera |

- **`Team`:** `Barcelona` es `H` y `Atletic Club` (así, con la errata de `DATA.md`) es `A`. También vale
  `Athletic Club`. `N/A` o cualquier otro valor queda fuera.
- Los códigos y los equipos se comparan sin distinguir mayúsculas. Un código que no esté en la tabla queda
  fuera y se cuenta.
- Una fase cubre los frames de `start_frame` a `end_frame`, sin incluir el último (`starter/load_smart_tagging.py`).
- **Equipo de la fase en un frame:** el que dan las fases que lo cubren. Si dan equipos distintos, el frame es
  **«solapado con equipos distintos»**: se cuenta y se excluye de todo lo demás.

Solo cuentan los frames evaluados.

## 3. Qué se mide (fijado antes de ejecutar)

`python validation/partido/fases_smart_tagging.py --entrega <csv>`: el ATD, el Smart Tagging y una entrega
(sección 4).

### 3.1 La regla del plan: acuerdo en los frames de control claro (decide)

- **Control claro** (P7): el mismo equipo es el más cercano al balón, a **1 m** o menos, durante **25 frames
  (1 s)** o más. Es `candidates.retention_team(trk, radius=1.0, min_frames=25)`, con el balón tal cual (el de
  la entrega, `ball.clean` v0).
- **Acuerdo:** de los frames de control claro con equipo de fase, en cuántos coincide el equipo de la fase con
  el del control.
- **Placebo:** el mismo cálculo con todas las fases desplazadas −480, −360, −240, +240, +360 y +480 s, los
  desplazamientos de `validation/partido/agregados_dead_ball.py`. Se da cada uno y su media.
- **Entra si se cumplen las dos:**
  1. el acuerdo es del **80 % o más**;
  2. **«dobla al placebo»**, que aquí se lee así: el desacuerdo con las fases reales es **como mucho la
     mitad** del desacuerdo medio con las desplazadas.

     Leído al pie de la letra, «el doble de acuerdo» no se puede cumplir: el placebo debería rondar el
     50 %. **Esta lectura la tiene que confirmar Ismael antes de subir la regla.**
- **Si no entra,** la pista no se usa, ni siquiera como empujón pequeño, y se apunta.

### 3.2 Frames solapados con equipos distintos (descriptivo)

- Cuántos frames evaluados con fase son «solapados con equipos distintos», y su porcentaje.
- **Cómo se lee:** por encima del 10 % de los frames con fase, la tabla de la sección 2 es sospechosa y se
  revisa antes de usar nada. No decide por sí solo: un acuerdo bajo ya hace fallar la regla de 3.1.

### 3.3 Transiciones (descriptivo; el número que más interesa)

De los inicios de `ATTACKING TRANSITION` con `Team` `H` o `A` que caen en un tramo evaluado, cuántos tienen
en nuestra entrega **un cambio a ese equipo a 2 s o menos** (50 frames, antes o después del inicio).

- **Un cambio a ese equipo** es un frame en que la etiqueta pasa a ser ese equipo desde otra (el otro equipo o
  `D`). Se separan los que vienen del otro equipo y los que vienen de `D`.
- **Cada inicio cae en una de cuatro clases, en este orden:**
  1. hay un cambio a ese equipo a ±2 s;
  2. no lo hay, pero en el inicio nuestra etiqueta ya es ese equipo;
  3. en el inicio nuestra etiqueta es el otro equipo;
  4. en el inicio es `D` (o `X`).
- **Placebo:** los mismos inicios desplazados los 6 desplazamientos de 3.1. Da cuántos cambios caen a ±2 s
  por casualidad.
- **También el desfase** entre el inicio y nuestro cambio, en intervalos gruesos: de −2 a −1 s, de −1 a 0, de
  0 a +1 y de +1 a +2 s.

### 3.4 Alcance del empujón (descriptivo)

Lo que podría tocar el empujón del plan: los frames evaluados **sin balón** cuya etiqueta en la entrega no es
`D`.
- cuántos son;
- cuántos tienen equipo de fase;
- en cuántos de ellos nuestra etiqueta es el otro equipo: son lo más que podría cambiar.

## 4. El script (fijado antes de ejecutar)

`validation/partido/fases_smart_tagging.py`. **Lee datos del partido (ATD y Smart Tagging) y una entrega
nuestra: lo ejecuta Antonio, en local, nunca Claude** (regla nº 1).

- **La entrega:** `equipo_v3`, la vigente. Si no la tiene, la genera con
  `python -m possession.pipeline --name equipo_v3`. El script imprime su sha256 abreviado y si es el de
  `equipo_v3` (`9539ce42…cc17a`).
- **Imprime solo agregados:** recuentos y porcentajes del partido entero, por código (frames) y por clase
  (inicios). Una celda de 1 a 4 casos sale como «< 5». Nada por frame, por minuto ni por jugada.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.
- `recuento(trk, eventos, etiquetas)` es una función pura. La prueba
  (`validation/scripts/prueba_fases_smart_tagging.py`) la ejecuta con un partido inventado de resultado
  conocido.

## 5. Límites conocidos

- **El control claro solo ve frames con balón,** y el empujón actuaría en frames sin balón. Que las fases
  acierten donde se ve el balón no garantiza que acierten donde no se ve.
- **El control claro es nuestro criterio, no la GT.** Un acuerdo alto dice que las fases y la proximidad
  coinciden, no que acierten la posesión.
- **Con 24 `ATTACKING TRANSITION`** (`DATA.md`), las clases de 3.3 tienen pocos casos: muchas celdas saldrán
  como «< 5».

## 6. Resultado (15/11, después de ejecutar)

- **La regla:** el commit `7d8a2ca`, en la rama `exp/fases-smart-tagging-equipo`, subido antes de ejecutar.
  A la pregunta «¿confirma Ismael la lectura de "dobla al placebo"?» de §3.1, Antonio contestó que sí antes
  de subirla.
- **La entrega:** `equipo_v3`, generada por Antonio con `python -m possession.pipeline --name equipo_v3`. El
  sha256 coincide (`9539ce42…cc17a`), también con Python 3.11 y numpy 2.4.6.
- **La ejecución:** Antonio ejecutó `python validation/partido/fases_smart_tagging.py --entrega …` en local
  (4 s). La salida entera, tal cual, está en `validation/resultados/2026-11-15_fases_smart_tagging.md`.

**Controles:** 158.857 frames evaluados, 94.214 con balón. De las 638 fases, 571 entran en la tabla.

| | resultado | regla | lectura |
|---|---|---|---|
| acuerdo en control claro (§3.1) | **81,8 %** (10.256 frames de 16.560 con fase) | 80 % o más | se cumple, por poco |
| desacuerdo frente al placebo (§3.1) | 18,2 % frente a 44,2 % de media (de 39,1 a 50,9 %) | como mucho la mitad: 22,1 % | se cumple |
| **regla del plan** | | | **entra** |
| solapados con equipos distintos (§3.2) | **13,5 %** de los 108.185 frames con fase | por encima del 10 %, sospechoso | **hay que revisar la tabla antes de usar nada** |

**Qué dice cada parte:**

- **La tabla, por parejas** [medido]: las fases salen a pares idénticos, con las mismas instancias, frames y
  acuerdo:
  - `ATTACKING TRANSITION` y `DEFENSIVE TRANSITION` (24, 3.850 frames, 93,1 %);
  - `BUILD UP` y `DEFENDING IN ATTACKING THIRD` (22, 5.491, 87,8 %);
  - `PROGRESSION` y `DEFENDING IN MIDDLE THIRD` (66, 28.472, 92,0 %);
  - `CREATING CHANCES` y `DEFENDING IN DEFENSIVE THIRD` (30, 19.164, 72,5 %).

  El Smart Tagging marca a la vez la fase de ataque de un equipo y la de defensa del otro. Con la tabla de §2,
  cada pareja da el mismo equipo con el balón. **El sentido de ataque y defensa está bien:** si estuviera al
  revés, cada pareja sería un solape con equipos distintos.
- **De dónde pueden venir los solapes** [inferencia, sin verificar]: de las fases largas «de zona», que siguen
  abiertas aunque cambie la posesión. `PLAYERS IN THE BOX` suma 61.044 frames con 97 instancias, y `BALL IN
  FINAL THIRD`, 49.561 con 93. Esas, junto con `BALL IN THE BOX` y `CREATING CHANCES`, son las que menos
  aciertan (del 72 al 75 %). Las de ataque y transición aciertan del 88 al 93 %.
- **Las transiciones (§3.3)** [medido]: hay 24 inicios.

  | clase | reales | placebo |
  |---|---|---|
  | cambio nuestro a ese equipo a ±2 s | < 5 | 6,8 % |
  | ya era ese equipo | < 5 | 22,6 % |
  | **era el otro equipo** | **19 (79,2 %)** | 27,8 % |
  | era `D` o `X` | < 5 | 42,9 % |

  Los pocos cambios que hay llegan **tarde**, de +1 a +2 s, y vienen del otro equipo.

  [inferencia] En casi 4 de cada 5 contraataques marcados, nuestra entrega sigue en el otro equipo al
  empezar y no cambia en 2 s. Y es la fase más fiable: acierta el 93,1 % donde se ve el balón. Cuadra con lo
  que ya se sabía: B5 pierde recuperaciones y llegamos tarde a los cambios. **No dice** si cambiamos después de
  los 2 s ni cuánto después.
- **El alcance del empujón (§3.4)** [medido]: hay 9.941 frames evaluados sin balón que no son `D`. De ellos,
  6.525 (65,6 %) tienen equipo de fase, y en 1.455 (22,3 %) nuestra etiqueta es del otro equipo. **Lo más que
  podría cambiar el empujón del plan son 1.455 frames, menos del 1 % de los evaluados.**

**Qué se hace:**

- **Según la regla, entra, pero no se usa todavía:** §3.2 pide revisar la tabla antes. La revisión que falta
  es un agregado del partido: los frames solapados con equipos distintos, por pareja de códigos.
- **Lo que vale la pista con el alcance del plan es poco:** como mucho, 1.455 frames.
- **Lo que más promete se sale del plan:** las transiciones. Un uso más amplio, como un empujón al inicio de
  las `ATTACKING TRANSITION`, lo decide Ismael. Antes haría falta saber cuánto tarda nuestro cambio después de
  esos inicios.
- **Nada de esto se ha encendido,** y la entrega no cambia.

## 7. Recuento de revisión (Antonio, con Claude · 15/11, antes de ejecutarlo)

Todo lo de esta sección está escrito antes de ejecutar nada. Sirve para dos cosas: cerrar la revisión de la
tabla que pide §3.2 y medir lo que falta de las transiciones para que Ismael decida.

`python validation/partido/fases_smart_tagging_revision.py --entrega evaluation/results/equipo_v3.csv`.
- Usa las mismas funciones, tabla, control claro, entrega y desplazamientos del placebo que §3 (importa
  `validation/partido/fases_smart_tagging.py`).
- **Lo ejecuta Antonio** e imprime solo agregados, con las celdas de 1 a 4 como «< 5».

### 7.1 Los solapes, por código y por pareja (decide si la tabla vale)

- **Por código:** en cuántos frames solapados con equipos distintos interviene cada código, por cualquiera de
  los dos lados.
- **Por pareja:** las 10 parejas de códigos (uno de cada lado) con más frames solapados.
- **Fases «de zona»:** `PLAYERS IN THE BOX`, `BALL IN FINAL THIRD` y `BALL IN THE BOX` (las que marcan dónde
  está el balón, no una acción). Se cuenta en cuántos solapados interviene al menos una.
- **Cómo se lee:**
  - si en el **70 % o más** de los frames solapados interviene una fase de zona, los solapes vienen de esas
    fases, que siguen abiertas aunque cambie la posesión. Como el sentido de ataque y defensa ya está
    comprobado (§6, las parejas idénticas), **la tabla vale tal cual, excluyendo los solapados**, y se cierra
    la revisión de §3.2;
  - si no, **la tabla sigue sospechosa y no se usa.**
- **Lo que no se hace:** quitar de la tabla las fases de zona, o cualquier otro código, después de ver los
  números. Sería otra tabla elegida con el partido. Si hiciera falta, lo decide Ismael.

### 7.2 Cuánto tardamos en los contraataques (descriptivo, para Ismael)

Para cada inicio de `ATTACKING TRANSITION` con `Team` `H` o `A` en un tramo evaluado (y, en el placebo, los
mismos inicios desplazados), se calcula la **espera**: cuánto tarda nuestra etiqueta en ser la de ese equipo,
contando desde el inicio.

- **Intervalos:** ya lo era en el inicio · hasta 2 s · de 2 a 5 s · de 5 a 10 s · de 10 a 15 s · no lo es en
  15 s.
- **Dentro de las fases de transición,** frame a frame, con los frames evaluados de esas fases juntos:
  - con qué etiqueta nuestra: ese equipo, el otro o `D`/`X`;
  - lo mismo solo en los frames de control claro del equipo de la transición, donde se ve el balón en sus
    pies.
- **Cómo se lee** (descriptivo: no decide nada; lo decide Ismael). Se le propone medir un empujón al inicio de
  las transiciones si se cumplen las dos:
  - la mitad o más de los inicios esperan más de 2 s (o no llegan en 15 s), más que en el placebo;
  - el 20 % o más de los frames de las fases de transición tienen nuestra etiqueta del otro equipo.

  Si no, se le pasan los números y nada más.

### 7.3 Límites

- **Son 24 transiciones:** muchas celdas saldrán «< 5», y una diferencia de pocos casos no dice nada.
- **El control claro no es la GT:** que nuestra etiqueta no coincida con el equipo que tiene el balón en los
  pies dice dónde discrepamos de la proximidad, no dónde fallamos.
