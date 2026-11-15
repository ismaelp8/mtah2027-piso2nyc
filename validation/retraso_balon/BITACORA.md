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
