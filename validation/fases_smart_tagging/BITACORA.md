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
