# Retraso del balón del ATD · bitácora: ¿llega el balón tarde respecto a los jugadores?

Es la tarea 1 de Antonio en `docs/PLAN_ENTREGA.md` §3 (tareas desde el 15/11) y la propuesta P1 de
`docs/revision_externa_2026-11-15.md`. Todo lo de las secciones 1 a 6 está escrito **antes de medir nada**,
ni en la DFL ni en el partido.

## 1. Por qué (Antonio Azuero, con Claude · 15/11/2026)

- **El balón del ATD viene suavizado unos 25 frames** [medido: `validation/resultados/2026-11-14_perfil_atd.md`].
  Ese perfil mide cuánto tiembla el balón, y el temblor es el mismo con un suavizado centrado que con uno
  hacia atrás. **La fase no la ha medido nadie.**
- **El harness da por hecho que es centrado** (`validation/harness/dfl.py`, `media_movil`). Si el ATD
  suavizara hacia atrás (cada frame, media de los 25 anteriores), el balón llegaría unos 12 frames tarde.
- **Cuánto costaría:** la tabla oficial de `EVALUATION.md` da 0,89 con 8 frames de retraso y 0,65 con
  1 s. Unos 12 frames costarían más que cualquier mejora medida hasta ahora [inferencia: interpolando la
  tabla].
- **Qué sale de aquí:** solo si hace falta desplazar el balón del `Tracking`, y cuánto. Ninguna etiqueta,
  ninguna constante de frames del partido y nada elegido con la ventana pública.
- **La latencia de la ventana pública no sirve de puerta** (plan §3): en nuestras entregas ha salido −6,0
  (`equipo_v1`) y +2,4 (`equipo_v3`) frames, con 5 parejas cada vez. No se usa aquí.

## 2. La medida (fijada antes de medir)

Mide el desfase entre el balón y el jugador que lo lleva. Es una medida **relativa**: si el balón y los
jugadores vinieran retrasados lo mismo, saldría 0 (límite en la sección 6).

1. **Tramos de conducción:** rachas de frames seguidos, dentro de un mismo tramo evaluado, con el balón a la
   vista, en las que **el mismo slot** es el más cercano al balón y está a **1,5 m o menos**, durante
   **25 frames (1 s) o más**.
   - El plan dice «el mismo equipo». Aquí se pide el mismo slot, que implica el mismo equipo, porque hace
     falta la velocidad de un jugador concreto. Si dos compañeros se turnan como más cercano, su velocidad
     saltaría de uno a otro.
   - Un slot no es un jugador a lo largo del partido. Dentro de una racha sí lo es casi siempre, y un
     intercambio de slot se descarta por la velocidad (punto 2).
2. **Velocidades, como vector (x, y), con una diferencia centrada de ±2 frames:**
   `v(t) = (pos(t+2) − pos(t−2)) / (4/25 s)`.
   - Es simétrica, así que no mete desfase.
   - Para el jugador se usa la del slot de la racha. Pasa a NaN si falta un extremo, si sale del tramo
     evaluado o si supera **12 m/s**: eso es un intercambio de slot, no un jugador (`validation/partido/comun.py`).
   - Para el balón, lo mismo con **40 m/s** (`possession/ball.py`, `MAX_SPEED`).
3. **Correlación por desfase `L`, de −25 a +25 frames:**
   - se compara la velocidad del jugador en `t` con la del balón en `t + L`, con `t` y `t + L` **dentro de
     la misma racha** (así no entra el pase con el que llega o se va el balón);
   - cada componente (x e y) se centra en su media dentro de cada racha y para cada `L`; se cuenta una
     racha en un `L` solo si tiene **10 parejas válidas o más**;
   - las sumas de todas las rachas se juntan en una correlación de Pearson por `L`.
4. **El desfase medido, `L̂`,** es el `L` de la correlación más alta. En un empate gana el de menor `|L|` y,
   después, el menor.
   - **Signo:** `L̂ > 0` es que el balón llega tarde. Una media hacia atrás de 25 frames da unos +12.
5. **Intervalo:** bootstrap por rachas, 200 remuestreos con semilla fija; se dan los percentiles 5 y 95 de
   `L̂`.
6. **Descriptivo, no decide:** el mismo desfase con el módulo de la velocidad en vez del vector, el `L̂` de
   cada parte, la correlación en el pico y la curva en algunos `L`.

El código es una función pura sobre un `Tracking` (`validation/retraso_balon/retraso.py`): el mismo en la
DFL y en el partido.

## 3. Calibración en la DFL (fijada antes de medir)

Los 7 partidos abiertos, con el tracking del harness (`validation/harness/dfl.py`, jugadores sin degradar y
slots barajados). Lo ejecuta Claude: `python validation/retraso_balon/calibrar_dfl.py`.

| condición | balón | se espera | ¿decide? |
|---|---|---|---|
| `limpio` | el de la DFL, sin suavizar | el desfase físico entre balón y jugador | no, descriptiva |
| `centrado` | «como el ATD» del harness: media centrada de 25 y los huecos del ATD | **0 ± 2** | sí |
| `hacia atrás` | media de los 25 frames anteriores, con los mismos huecos | **+12 ± 2** | sí |
| `centrado +6` | el de `centrado`, retrasado 6 frames | **+6 ± 2** | sí |
| `centrado −6` | el de `centrado`, adelantado 6 frames | **−6 ± 2** | sí |

- **Por qué `+6` y `−6`,** que el plan no pide: la regla del partido corta entre 3 y 4 frames. Con solo 0 y
  +12, el instrumento podría separar los dos extremos y equivocarse en medio.
- **Cómo se construyen:** `hacia atrás`, `+6` y `−6` se hacen sobre el balón `limpio` del harness, con la
  misma máscara de huecos que `centrado`. El script comprueba antes que, con la media centrada, reproduce el
  balón de «como el ATD» del harness. Si no, da error y no mide.
- **Pasa si,** en cada una de las cuatro condiciones que deciden:
  - el `L̂` de **6 de los 7 partidos o más** cae en su banda;
  - y el `L̂` de los 7 juntos también.

  Se exige partido a partido porque en el ATD solo hay un partido: la medida tiene que valer con uno.
- **Si no pasa,** no se ejecuta en el partido (plan §3). Se apunta aquí y en `docs/decisiones.md`, y la
  tarea se cierra sin tocar nada. Un instrumento nuevo sería otra regla, escrita y subida antes de volver a
  medir.

## 4. El recuento en el partido (fijado antes de medir)

`python validation/partido/retraso_balon.py`. **Lee datos del partido: lo ejecuta Antonio, en local,
nunca Claude** (regla nº 1). Solo si la calibración pasa.

- Lee el ATD con `possession/tracking.py`, el mismo lector que el pipeline, y mide los frames evaluados con
  el mismo código que la DFL.
- **El balón tal cual viene,** sin `ball.clean_v1`, porque es el que usa la entrega (`ball.clean` v0).
- **Imprime solo agregados del partido entero:** recuentos de rachas y de frames, `L̂`, su intervalo, el
  `L̂` de cada parte, correlaciones y la lectura de la sección 5. Una celda de 1 a 4 casos sale como «< 5».
  Nada por minuto, por jugada ni por frame.
- Si falla, imprime solo el tipo de error y las líneas del código, sin valores de datos.
- No escribe ningún fichero.

## 5. Cómo se leerá (fijado antes de medir)

Con el `L̂` de las dos partes juntas. El script imprime la lectura que toca:

1. **No concluyente** si las dos partes se separan más de 4 frames (`|L̂₁ − L̂₂| > 4`) o el intervalo del
   5 al 95 % mide más de 8 frames. Es el «no se puede separar» del candidato 3 del plan: **no se toca nada y
   se apunta.**
   - Por qué 4 y 8: 4 es el corte de la regla. Si las dos partes discrepan más que eso, o el intervalo
     cubre dos cortes, la medida no puede decir de qué lado está.
2. Si no, **`|L̂| ≤ 3`:** **candidato 1, no se toca nada.**
3. Si no, **`|L̂| ≥ 4`:** **candidato 2.** Se escribe una variante en `possession/ball.py` que adelanta el
   balón `L̂` frames, o lo retrasa si `L̂` es negativo. `ball.clean` no cambia: encenderla lo decide
   Ismael, y obligaría a reentrenar o medir B5 y a repetir la medida de Manuel, como la limpieza.

**Después de ver el número no se retoca nada:** ni el radio, ni la duración de las rachas, ni los cortes.

## 6. Límites conocidos

- **Es relativa.** Si los jugadores del ATD también vinieran retrasados, esta medida no lo ve: compara el
  balón con el jugador. Separarlo pediría otra referencia, como el vídeo, que no cabe antes del 17. Es el
  candidato 3 del plan: se apunta y no se toca.
- **La física también tiene fase.** El balón no se mueve exactamente con el pie, así que el desfase de la
  condición `limpio` no tiene por qué ser 0. La banda de ±2 de la calibración ya lo absorbe, y `limpio` se
  da para verlo.
- **Las rachas se buscan con el balón que hay.** Con un balón retrasado, el jugador rápido se aleja más de
  1,5 m de él y quedan sobre todo las conducciones lentas. La condición `hacia atrás` mide justo eso.
- **La DFL tiene más disputas que el ATD** (20 % frente a 14,5 %, plan §4). Aquí pesa poco, porque solo
  cuentan los tramos en que un jugador lleva el balón.

## 7. Resultado de la calibración (15/11, después de medir)

La regla de las secciones 1 a 6 se guardó en el commit `d94addb` antes de ejecutar nada. Calibración con
`python validation/retraso_balon/calibrar_dfl.py`, 7 partidos, 8 s.

**No pasa. La medida no se ejecuta en el partido** (§3).

| condición | se espera | `L̂` de los 7 juntos | partidos en la banda | ¿pasa? |
|---|---|---|---|---|
| `limpio` | descriptiva | −6 | — | — |
| `centrado` | 0 ± 2 | −7 | 0 de 7 | **no** |
| `hacia atrás` | +12 ± 2 | +12 | 7 de 7 | sí |
| `centrado +6` | +6 ± 2 | +6 | 6 de 7 | sí, por poco |
| `centrado −6` | −6 ± 2 | −11 | 0 de 7 | **no** |

[medido] Por partido, `L̂` de `limpio` va de −7 a −5 y el de `centrado`, de −8 a −6. En `centrado +6`, el
intervalo de 5 de los 7 partidos va de −7 a +6.

**Por qué falla** (diagnóstico en la DFL, con la curva de los 7 juntos; no cambia la regla):

| L | −20 | −16 | −12 | −8 | −6 | −4 | −2 | 0 | +2 | +4 | +6 | +8 | +12 | +16 | +20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `limpio` | 0,41 | 0,47 | 0,53 | 0,57 | 0,57 | 0,57 | 0,54 | 0,47 | 0,49 | 0,49 | 0,48 | 0,46 | 0,40 | 0,33 | 0,27 |
| `centrado` | 0,60 | 0,67 | 0,73 | 0,76 | 0,76 | 0,75 | 0,72 | 0,69 | 0,69 | 0,69 | 0,67 | 0,64 | 0,56 | 0,48 | 0,40 |
| `hacia atrás` | 0,23 | 0,29 | 0,36 | 0,41 | 0,42 | 0,41 | 0,40 | 0,39 | 0,44 | 0,49 | 0,53 | 0,56 | 0,59 | 0,57 | 0,51 |
| `centrado +6` | 0,49 | 0,56 | 0,63 | 0,67 | 0,68 | 0,67 | 0,65 | 0,63 | 0,66 | 0,68 | 0,69 | 0,68 | 0,64 | 0,58 | 0,51 |
| `centrado −6` | 0,57 | 0,64 | 0,67 | 0,66 | 0,64 | 0,62 | 0,58 | 0,54 | 0,51 | 0,48 | 0,43 | 0,39 | 0,30 | 0,22 | 0,17 |

- **La curva tiene dos jorobas** [medido]: una hacia −6 (el balón va por delante del jugador) y otra
  hacia +3 (va por detrás), con un valle en 0. El máximo salta de una a otra según la condición. Por eso
  `L̂` no se mueve lo mismo que el desplazamiento: centrado da −7, retrasado 6 da +6 y adelantado 6 da −11.
- **Lectura física** [inferencia]: en una conducción, el jugador empuja el balón y lo sigue, y el balón se
  adelanta; al protegerlo o al recibir, el balón va detrás. En la DFL pesan parecido, y el máximo de una
  mezcla así no es estable.
- **Lo que sí se mueve con el retraso es la forma entera de la curva** [medido, en la tabla]: cuanto más
  tarde llega el balón, más peso tiene a la derecha. Con un resumen de la curva entera, en vez de su
  máximo, quizá saldría una medida que se mueve con el desplazamiento. **No se ha medido**: sería un
  instrumento nuevo, con su regla escrita y subida antes, y diseñado después de ver estas curvas de la DFL
  (nunca el partido).

**Qué se hace:** nada en `possession/`. El partido no se ha tocado.

## 8. Versión 2 (Antonio, con Claude · 15/11, antes de medirla)

Antonio decidió el 15/11 probar una segunda versión. Todo lo de esta sección está escrito antes de
ejecutarla. **Es la última:** si no pasa, la tarea se cierra sin una tercera.

**Aviso de honestidad:** la versión 2 se diseña **después de ver las curvas de la DFL de la sección 7**
(nunca el partido). Para que su calibración siga siendo una prueba, se mide con partidos y retrasos que
no se han mirado (punto 3).

### 8.1 Qué cambia y qué no

- **No cambia la curva:** las mismas rachas, velocidades, parejas y correlación por desfase de §2, con el
  mismo código (`retraso.sumas`).
- **Cambia cómo se lee la curva.** En vez de su máximo, se compara la curva **entera** con una familia de
  curvas de referencia hechas en la DFL con retrasos conocidos. El desfase medido, `d̂`, es el retraso de la
  curva de referencia que más se le parece.
  - Así da igual que la curva tenga dos jorobas o no se desplace lo mismo que el balón: la familia se hace
    con el mismo instrumento, así que trae esas rarezas dentro.

### 8.2 La medida

1. **La familia:** en cada partido de la DFL, el balón `centrado` de §3 (media centrada de 25 y huecos
   «como el ATD») retrasado `d` frames, para `d` de **−18 a +18**, de uno en uno. Se construye como
   `centrado ±6` en §3. Cada curva de la familia junta las rachas de los partidos que se usen.
2. **Comparación:** las dos curvas se normalizan (se les resta su media y se dividen por su desviación,
   sobre los `L` de −25 a +25) y se calcula la media de las diferencias al cuadrado. `d̂` es el `d` de la
   menor; en un empate gana el de menor `|d|` y, después, el menor. Esa diferencia mínima es el **residuo**:
   dice cuánto se parece la curva a la familia.
3. **Intervalo y partes,** como en §2: bootstrap de 200 por rachas con semilla fija (la familia no se
   remuestrea) y el `d̂` de cada parte con la misma familia.
4. **Descriptivo:** el `L̂` de la versión 1 (el máximo de la curva).

### 8.3 Calibración en la DFL (fijada antes de medir)

`python validation/retraso_balon/calibrar_dfl_v2.py`, que lo ejecuta Claude.

- **Dejando un partido fuera:** cada partido se mide con la familia hecha con los otros 6. Así la medida
  nunca se compara consigo misma.
- **Los retrasos de prueba** son el balón `centrado` retrasado **−9, −6, −3, 0, +3, +6 y +9** frames, más
  `hacia atrás` (la media de los 25 frames anteriores de §3), que debe dar **+12**.
  - −9, −3, +3 y +9 **no se han mirado nunca**: la sección 7 solo tiene 0, ±6 y +12.
- **Pasa si** en cada una de las 8 pruebas el `d̂` cae a **±2** del retraso de verdad en **6 de los 7
  partidos o más**.
- **Descriptivo, no decide:** un balón con un suavizado de otra forma, una media exponencial hacia atrás de
  retraso medio 8 frames (α = 1/9). Dice si la medida aguanta un filtro que no está en la familia.
- **El residuo de referencia** es el mayor residuo de las 8 pruebas en los 7 partidos. Se usa en la lectura
  del partido (8.5).

### 8.4 El recuento en el partido

El mismo script de §4 (`validation/partido/retraso_balon.py`), cambiado a la versión 2. Lo ejecuta Antonio,
solo si la calibración de 8.3 pasa.

- **Familia:** la de los 7 partidos de la DFL juntos. El script la calcula al empezar desde la caché de la
  DFL, con el residuo de referencia, así que tarda un par de minutos y necesita la DFL bajada.
- **Imprime solo agregados,** como en §4: `d̂`, su intervalo, `d̂` de cada parte, el residuo del ATD y el de
  referencia, el `L̂` de la versión 1 y la lectura.

### 8.5 Cómo se leerá (fijado antes de medir)

Como en §5, con `d̂` en lugar de `L̂` y una condición más:

1. **No concluyente** si:
   - el residuo del ATD es **más del doble** del residuo de referencia: la curva del ATD no se parece a la
     familia y la comparación no vale;
   - o las partes se separan más de 4 frames;
   - o el intervalo del 5 al 95 % mide más de 8 frames.

   No se toca nada y se apunta.
2. Si no, `|d̂| ≤ 3`: **candidato 1, no se toca nada.**
3. Si no, `|d̂| ≥ 4`: **candidato 2,** una variante en `possession/ball.py` que desplaza el balón `d̂`
   frames. `ball.clean` no cambia: lo decide Ismael.

**Después de ver el número no se retoca nada.**

### 8.6 Límites nuevos

- **La familia es de la DFL.** Si el balón del ATD se relaciona con el jugador de otra manera (otro
  proveedor y otro suavizado), la comparación puede sesgarse. El residuo lo vigila en parte: no ve un sesgo
  que conserve la forma de la curva.
- **La familia solo tiene el suavizado de caja de 25 frames.** Si el del ATD tiene otra forma, la prueba
  exponencial de 8.3 dice cuánto pesa eso, pero no decide.

## 9. Resultado de la calibración v2 (15/11, después de medir)

La regla de la sección 8 se subió a GitHub en el commit `3e92064` (rama `exp/retraso-balon-atd`) antes de
ejecutar nada. Calibración con `python validation/retraso_balon/calibrar_dfl_v2.py`, 7 partidos, 41 s.

**Pasa. La medida se puede ejecutar en el partido** (§8.3).

| prueba | retraso de verdad | `d̂` por partido | en la banda |
|---|---|---|---|
| `centrado −9` | −9 | de −10 a −7 | 7 de 7 |
| `centrado −6` | −6 | de −7 a −5 | 7 de 7 |
| `centrado −3` | −3 | de −4 a −1 | 7 de 7 |
| `centrado 0` | 0 | de −2 a +2 | 7 de 7 |
| `centrado +3` | +3 | de +2 a +5 | 7 de 7 |
| `centrado +6` | +6 | de +5 a +7 | 7 de 7 |
| `centrado +9` | +9 | de +8 a +10 | 7 de 7 |
| `hacia atrás` | +12 | de +11 a +14 | 7 de 7 |

[medido] Con cada partido medido con la familia de los otros 6:

- **El intervalo del 5 al 95 % mide de 1 a 4 frames,** y las dos partes se separan como mucho 3 frames.
  Ninguna prueba habría salido «no concluyente» por esas dos condiciones.
- **El residuo de referencia** (el mayor de las 8 pruebas) es **0,027**, el de `hacia atrás` en J03WOH. El
  resto va de 0,000 a 0,018.
- **El máximo de la versión 1** sigue saltando: con `centrado +3` da −6 o −7 en los 7 partidos.

**La prueba descriptiva** (exponencial hacia atrás, retraso medio +8, fuera de la familia):

- `d̂` va de **+3 a +7**: se queda corto, de 1 a 5 frames;
- su residuo va de **0,082 a 0,205**, de 3 a 8 veces el de referencia.

Con la regla de §8.5, las 7 habrían salido «no concluyente» por el residuo. [inferencia] Si el ATD
suavizara con una forma así, la medida no se daría por buena: la protección hace su papel. Y si saliera
concluyente con un filtro de otra forma, podría quedarse corta.

**Lo siguiente:** Antonio ejecuta `python validation/partido/retraso_balon.py` y pega la salida. Se lee con
§8.5, sin retocar nada.

## 10. Resultado en el partido (15/11, después de medir)

Antonio ejecutó `python validation/partido/retraso_balon.py --data-dir …` en local (45 s) y pegó la salida,
que solo trae agregados. Con `main` en `3b227c4` y la rama en `b143176`.

**Controles:** 158.857 frames evaluados y 94.214 con balón, los del perfil del ATD; la familia, con los 7
partidos de la DFL.

| | valor | regla de §8.5 |
|---|---|---|
| rachas de conducción | 572 (290 y 282 por parte), 29.183 frames | — |
| residuo | 0,018 | ≤ 2 × 0,027 = 0,054: la curva se parece a la familia |
| `d̂` por parte | +3 y +4 | se separan 1 frame, ≤ 4 |
| intervalo del 5 al 95 % | de +2 a +5 | 3 frames, ≤ 8 |
| **`d̂`** | **+4** | **`|d̂|` ≥ 4: candidato 2** |

[medido] **El balón del ATD llega unos 4 frames tarde respecto a los jugadores.** Lo descriptivo: el máximo
de la versión 1 da +5 (por parte, +5 y −6: sigue saltando de joroba) y +6 con el módulo.

**Cautelas:**
- **Está en el corte:** el intervalo incluye +2 y +3, que serían el candidato 1. La regla decide con `d̂`, y
  no se ha retocado.
- **Es relativa:** si los jugadores del ATD también llegaran tarde, no se ve (§6).

### 10.1 El candidato 2 y lo que valdría encenderlo

- **La variante,** como pide la regla: `possession/ball.py`, `advance_ball`, que adelanta el balón
  `BALL_LEAD` = 4 frames. `ball.clean` no cambia, así que la entrega tampoco.
- **Cuánto cuesta ese retraso en la DFL** (descriptivo, no decide): el harness con el balón retrasado
  4 frames frente a `main`, con `validation/harness/versiones/retraso_balon_2026-11-15.json`.

  | etiquetas | «como el ATD» | «como el ATD, sin bloques» |
  |---|---|---|
  | flag | +0,001 [−0,003 a +0,006] | +0,002 [−0,002 a +0,007] |
  | control | −0,007 [−0,012 a −0,002] | −0,006 [−0,011 a −0,001] |

  [medido] Con §5.8, empate. **Encender la corrección ganaría como mucho unas 0,007** [inferencia: lo que
  pierde la DFL con el retraso], muy por debajo del 0,03 de §5.8.
- [inferencia] El retraso del balón no pasa entero a las etiquetas: B5 mira ventanas largas y el
  decodificador cobra cada cambio. Por eso cuesta mucho menos que un retraso de 4 frames de la tabla oficial.

**Propuesta para Ismael: no encenderla.** Encenderla obliga a reentrenar o medir B5 y a repetir la medida de
Manuel, por menos de una centésima. El riesgo de la revisión externa (unos 12 frames, que costarían más que
cualquier mejora) **queda descartado respecto a los jugadores**. La tarea se cierra.

- **Si algún día se enciende,** también hay que cambiar el harness: su degradación «como el ATD» tendría que
  retrasar el balón 4 frames. Hoy llega a su hora (media centrada), así que con la pieza encendida el harness
  mediría un balón adelantado, no una corrección.

## 11. Revisión de Ismael y sensibilidad al ancho del suavizado (15/11, después de medir el partido)

**El orden, tal cual pasó:**

| hora | qué |
|---|---|
| 16:41 | regla de la v2 (`3e92064`) |
| 16:44 | calibración de la v2 en la DFL (`b143176`) |
| hacia las 16:50 | Antonio ejecuta la v2 en el partido (§10) |
| después | llega el mensaje de Ismael, que había revisado `3e92064` |

Ismael no sabía que el partido ya se había medido. Escribió esto:

1. **Cambiar la lectura del lado negativo y subirlo antes de ejecutar:** con `d̂` de −4 o menos, se apunta y
   no se toca nada. Medido por él: un balón con un suavizado centrado de 49 frames, sin retraso, da entre −6
   y −1 (falsa alarma en 3 de 7), y unos jugadores que llegan tarde también dan negativo.
2. **Apuntar en la bitácora la calibración de la v2:** está en §9.
3. **Ejecutarlo en el partido y pegar la salida entera, salga lo que salga:** está en §10. La salida tal cual
   está en `validation/resultados/2026-11-15_retraso_balon.md`.

**El cambio del punto 1 entra, pero después de medir.** Ya no se puede subir antes de ejecutar. No cambia la
lectura del partido: `d̂` = +4 es positivo, y el lado positivo no cambia. En el código, `retraso.lectura` da
ahora «negativo, se apunta» con `d̂` ≤ −4.

**Sensibilidad al ancho del suavizado** (DFL, descriptivo; hecha después de medir el partido, sin cambiar
ninguna regla). Es el balón centrado sin retraso, con otros anchos, medido dejando un partido fuera con la
familia de caja de 25. Lo correcto sería 0:

| ancho | `d̂` en los 7 partidos | residuo | ¿alguno da +4 o más? |
|---|---|---|---|
| 13 | de −1 a +2 | de 0,002 a 0,006 | no |
| 25 (la familia, §9) | de −2 a +2 | de 0,001 a 0,002 | no |
| 37 | de −3 a +1 | de 0,002 a 0,006 | no |
| 49 | de −6 a −1 (3 de 7 en −4 o menos) | de 0,011 a 0,037 | no |

- [medido] Reproduce lo que vio Ismael con 49 frames.
- [medido] **Un suavizado centrado de 13 a 49 frames no fabrica un +4:** los anchos más estrechos dan como
  mucho +2. El residuo no avisa de ninguno de estos casos: el mayor, 0,037, queda por debajo de 0,054.
- [inferencia] El +4 del ATD no se explica por un suavizado centrado de otro ancho. Si el ATD suavizara menos
  de 25 frames (el perfil mide unos 25), parte del +4 podría ser ese sesgo, y el retraso de verdad estaría más
  cerca de +2. Con cualquiera de las dos lecturas, la decisión de §10.1 no cambia.
