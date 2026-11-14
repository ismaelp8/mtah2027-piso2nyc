# Experimento 2 · bitácora: qué convención sigue la GT pública, medida con el tracking

Continúa la sección 6 del resultado del experimento 1
(`validation/resultados/2026-11-12_criterio_posesion.md`) y el protocolo de Antonio (sección 17 de la
bitácora del experimento 1, en la PR #1). Va en una carpeta nueva para no chocar con esa PR.

## 1. Por qué (14/11/2026)

- **Lo pide Ismael** (14/11). Antonio está con otra cosa, y a ojo se escapan cosas. Hay que usar todos
  los datos que nos dan (el tracking de jugadores y balón, aunque no sea perfecto) y comparar siempre con
  la ventana pública.
- **El vídeo no lo puede ver Claude** (regla nº 1). El tracking sí puede responder a máquina dos de las
  tres preguntas del protocolo de la sección 17:
  - **la 2:** cuándo cambia la etiqueta respecto al primer toque del equipo nuevo;
  - **la 3:** si los toques del rival sin control cambian la etiqueta.

  La **intención** de un toque no se ve en el tracking: aquí no se mide.
- **Qué permiten las reglas:**
  - `CHALLENGE.md` (líneas 82–87 y 102–103): la GT pública es donde se ve qué significa "poseer", y si
    nuestra lectura choca con ella, manda la GT.
  - `RULES.md` §2 y `EVALUATION.md` (líneas 139–141): la ventana pública sirve para comprobar que las
    etiquetas significan lo que creemos, nunca para elegir entre versiones ni para entrenar.
  - Aquí se usa solo para leer la convención. No sale ningún parámetro, etiqueta ni constante.

## 2. El instrumento (fijado antes de medir, 14/11)

Código en `instrumento.py`. Son las medidas del experimento 0 con sus mismos umbrales; no se ajusta nada.

- **Toque:** cambio de velocidad del balón de 3 m/s o más, atribuido al equipo del jugador más cercano si
  está a 1,5 m o menos.
  - Se busca por tramos de balón visible de 10 frames o más. `medidas_cambios.toques` acumula
    velocidades con `cumsum` y un solo frame sin balón le borra los toques del resto de la parte; en la
    DFL nunca pasó porque el balón no falta. Lo comprueba `pruebas_sinteticas.py`.
  - En los bordes de un hueco no se busca toque: ni se interpola ni se inventa.
  - Se quitan los toques cuya ventana toca un frame sin balón vivo.
- **Control de equipo: Ret-12.** El más cercano es del mismo equipo, a 1 m o menos, durante 12 frames.
  Es de equipo, y no de jugador, porque en el ATD un slot no es un jugador.
- **Pregunta 2 (cambios directos H↔A):** `T` es el primer toque del equipo nuevo después del último toque
  del equipo anterior que no pasa del cambio `F`, buscando en `F ± 50` frames.
  - Clases de `Δ = F − T` (las de la sección 17): antes del toque (`Δ < −5`), en el toque (`±5`), poco
    después (6–25), más tarde (más de 25) y sin toque visible.
  - Además, `F` frente al inicio del primer Ret-12 del equipo nuevo entre `T − 5` y `F + 50`.
- **Pregunta 1 (posesiones cortas X → y → X de menos de 3 s):** control, solo toque, sin balón o nada.
- **Pregunta 3:** la medida 2g del experimento 0 (`toques_sin_control`), contada por hueco entre dos
  controles del mismo equipo. Dice si la etiqueta pasa al rival tras un toque suyo sin control. Lleva su
  placebo: toques propios sin control.
- **Dos variantes, siempre las dos:**
  - **base:** la de arriba;
  - **ampliada:** radio de control de 1,5 m y radio de toque de 2 m, por si el ATD es más ruidoso.
- **Salida:** solo recuentos por clase y proporciones.

## 3. Calibración en la DFL (fijada antes de medir, 14/11)

Código en `calibrar_dfl.py`. Los 7 partidos y dos juegos de etiquetas:

- **flag tal cual:** lectura 1, cambia en el primer toque del rival;
- **corregida "C0-12 o dos toques":** lectura 3, con el cambio fechado en el toque, como en
  `validation/experimento1/correccion.py`.

Las etiquetas salen siempre del tracking limpio. El instrumento mide sobre tracking degradado para
parecerse al ATD, con la semilla 20261114:

| condición | balón quitado | ruido |
|---|---|---|
| limpia | nada | no |
| bloques 41 % | el 41 % de los frames vivos, en bloques al azar de 1 s de media | no |
| dirigida 41 % | disputas (los dos equipos a 3 m o menos) y balones altos (más de 1,5 m), ±5 frames; se completa hasta el 41 % con bloques | no |
| dirigida + 10 cm | igual | gaussiano de 10 cm en el balón y 5 cm en los jugadores |
| dirigida + 25 cm | igual | 25 cm y 12,5 cm |
| intermedias | el 41 %, tapando el 0, 25, 50, 75 o 100 % de los episodios de disputa y completando con bloques | 0, 10 o 25 cm (añadidas en la sección 5, antes de la ventana) |

**El instrumento distingue las dos lecturas en una condición si se cumplen las dos cosas:**

- en la pregunta 3, la proporción de huecos que cambian es al menos 0,40 mayor con el flag que con la
  corregida (los 7 partidos juntos);
- los rangos por partido no se solapan.

## 4. Cómo se leerá la ventana pública (fijado antes de ejecutarla, 14/11)

**Sustituida por la sección 7**, también antes de ejecutar nada en la ventana. Se deja como se escribió.

La ejecuta una persona con `validation/partido/recuento_ventana.py`, una sola vez. Claude solo ve los
agregados.

1. **Qué condición de la DFL se parece al ATD:**
   - se elige entre las "dirigida" (DATA.md: el ATD pierde el balón justo en las jugadas importantes);
   - gana la que tenga el **temblor del balón** más parecido al del ATD (mediana de la segunda diferencia
     de la posición, en cm), comparando por cociente;
   - si el temblor del ATD pasa del de la condición con 25 cm, se usa esa y la calibración se apunta como
     optimista;
   - esto solo usa el tracking, no las etiquetas.
2. **Si el instrumento no distingue las lecturas en esa condición** (sección 3): no se decide nada con el
   tracking.
3. **Pregunta 3, la principal.** Hacen falta 5 huecos o más en la variante base. Con `r` la proporción de
   la GT y `r1`, `r3` las del flag y la corregida en la condición elegida, y `m = (r1 + r3) / 2`:
   - **`r ≥ m + 0,10`:** la GT cambia con toques del rival sin control (lectura 1 o 2). Toca revisar la
     decisión del 12/11 con Ismael.
   - **`r ≤ m − 0,10`:** la GT exige control (lectura 3), como se decidió el 12/11.
   - **en medio, o con menos de 5 huecos:** sin decidir.
4. **Robustez:** la variante ampliada tiene que dar el mismo veredicto. Si no, sin decidir.
5. **Pregunta 2 (la fecha).** Solo con 6 cambios o más con toque visible:
   - si la proporción "en el toque" es al menos la del flag en la condición elegida menos 0,25: la GT
     fecha el cambio en el toque;
   - si "poco después" más "más tarde" llegan a la mitad: lo fecha después del toque;
   - si no: sin decidir.

   El margen exacto, si lo hay, no sale de aquí: se fija con la DFL.
6. **Pregunta 1:** descriptiva. Son 3 posesiones.
7. **Sin decidir:** se lleva a Ismael con dos salidas. Una es preguntar a la organización. La otra es
   mirar a ojo solo los casos que el tracking no ve, con el protocolo de la sección 17 y apuntando solo
   recuentos.

## 5. Cambio antes de medir: la pregunta 3 necesita más casos (14/11)

**Qué se vio** [medido], ejecutando la calibración en un solo partido (J03WMX), antes de que nadie
ejecute nada en la ventana:

- la medida 2g tiene pocos casos: 31 huecos en el partido con el balón limpio, 9 con bloques y 1 con la
  degradación dirigida;
- la ventana tiene unos 4 minutos de juego, así que esperaríamos unos 2 huecos aun con el balón perfecto.
  La regla de la sección 4 pide 5: la pregunta 3 quedaría sin decidir siempre.

**Se añade, sin quitar nada: toques sueltos del rival** (`instrumento.toques_sueltos`). Un toque del
equipo `y` cuenta si se cumplen las cuatro cosas:

- la etiqueta marca al otro equipo tres frames antes, y el balón está vivo de `t − 5` a `t + 50`;
- abre episodio: el toque anterior no es de `y` a 25 frames o menos;
- `y` no tiene control después, ni un Ret-12 que empiece de `t − 5` a `t + 50` ni un segundo toque suyo
  a 50 frames o menos sin uno del rival en medio;
- se mira si la etiqueta pasa a `y` de `t` a `t + 25`.

Lleva el mismo placebo con toques sueltos del equipo que tiene la etiqueta.

**La regla de la sección 4 cambia así** (antes de ver nada de la ventana):

- en el punto 3, si hay menos de 5 huecos, se usan los toques sueltos con la misma regla (`m ± 0,10`, con
  sus `r1` y `r3`), y hacen falta 5 episodios o más;
- el criterio de que el instrumento distingue (sección 3) se aplica igual a los toques sueltos.

**Segundo cambio, con los 7 partidos** (también antes de la ventana). Lo que decide si el instrumento sirve
es **cómo pierde el balón el tracking**: al azar o justo en las disputas (sección 6). Eso se puede medir en
el ATD sin etiquetas:

- **Nueva medida de tracking:** qué parte de los frames vivos con balón visible son disputas (un jugador de
  cada equipo a 3 m o menos).
- **Condiciones intermedias:** se tapa el 0, 25, 50, 75 o 100 % de los episodios de disputa, cada uno con
  ruido de 0, 10 o 25 cm, para que un ATD que esté entre los dos extremos no se lea contra el que no es.
- **La regla de la sección 4 queda sustituida por la de la sección 7.** Se añade un control de cordura,
  se precisa cuándo cuenta la variante ampliada y se resuelve el caso en que la pregunta 2 diera las dos
  respuestas a la vez.

## 6. Resultados de la calibración (14/11, 7 partidos)

[medido] `calibrar_dfl.py --tabla`, semilla 20261114, variante base.

- Las proporciones son de los 7 partidos juntos y, entre corchetes, el mínimo y el máximo por partido.
- `r1` es el flag (cambia en el toque) y `r3` la corregida (exige control), en los toques sueltos del rival.
- "Por minuto" es por minuto de balón vivo. La ventana tiene unos 4.

| disputas tapadas | ruido | disputas entre los visibles | temblor (cm) | toques/min | controles/min | sueltos/min | `r1` | `r3` | ¿distingue? | en el toque (flag) | cambios con toque visible |
|---|---|---|---|---|---|---|---|---|---|---|---|
| limpia | – | 21,0 % | 2,2 | 37,9 | 13,4 | 1,89 | 0,88 [0,72–0,94] | 0,19 [0,14–0,29] | sí | 0,79 | 0,86 |
| 0 % | 0 cm | 21,3 % | 2,2 | 20,7 | 9,5 | 1,37 | 0,89 [0,77–0,94] | 0,31 [0,21–0,43] | sí | 0,68 | 0,56 |
| 0 % | 10 cm | 20,6 % | 29,6 | 37,0 | 9,1 | 1,65 | 0,67 [0,58–0,74] | 0,22 [0,17–0,29] | sí | 0,57 | 0,64 |
| 0 % | 25 cm | 21,0 % | 72,5 | 42,7 | 6,2 | 2,03 | 0,53 [0,46–0,62] | 0,18 [0,15–0,22] | no | 0,51 | 0,67 |
| 25 % | 0 cm | 17,1 % | 2,2 | 20,5 | 9,4 | 1,18 | 0,87 [0,75–0,90] | 0,35 [0,29–0,40] | sí | 0,68 | 0,51 |
| 25 % | 10 cm | 17,2 % | 29,5 | 37,6 | 9,1 | 1,43 | 0,67 [0,58–0,71] | 0,21 [0,14–0,31] | sí | 0,54 | 0,59 |
| 25 % | 25 cm | 17,4 % | 72,6 | 42,2 | 6,1 | 1,67 | 0,53 [0,47–0,62] | 0,17 [0,13–0,20] | no | 0,51 | 0,57 |
| 50 % | 0 cm | 13,9 % | 2,2 | 20,1 | 9,4 | 0,93 | 0,90 [0,80–0,97] | 0,32 [0,23–0,42] | sí | 0,64 | 0,46 |
| 50 % | 10 cm | 13,9 % | 29,6 | 37,7 | 9,1 | 1,16 | 0,67 [0,59–0,71] | 0,25 [0,19–0,29] | sí | 0,54 | 0,51 |
| 50 % | 25 cm | 13,8 % | 72,7 | 42,8 | 6,2 | 1,32 | 0,52 [0,45–0,63] | 0,19 [0,16–0,24] | no | 0,48 | 0,54 |
| 75 % | 0 cm | 7,7 % | 2,2 | 19,8 | 9,2 | 0,61 | 0,90 [0,79–1,00] | 0,38 [0,29–0,48] | sí | 0,61 | 0,37 |
| 75 % | 10 cm | 7,3 % | 29,3 | 37,6 | 9,1 | 0,70 | 0,71 [0,63–0,80] | 0,28 [0,18–0,36] | sí | 0,48 | 0,41 |
| 75 % | 25 cm | 8,3 % | 72,3 | 42,7 | 6,2 | 0,90 | 0,56 [0,45–0,71] | 0,21 [0,13–0,32] | no | 0,45 | 0,44 |
| 100 % | 0 cm | 0,0 % | 2,2 | 17,1 | 8,6 | 0,22 | 0,95 [0,83–1,00] | 0,70 [0,46–0,83] | no | 0,50 | 0,23 |
| 100 % | 10 cm | 0,1 % | 29,4 | 34,5 | 8,5 | 0,18 | 0,91 [0,70–1,00] | 0,53 [0,36–1,00] | no | 0,38 | 0,28 |
| 100 % | 25 cm | 0,3 % | 72,6 | 39,1 | 5,8 | 0,21 | 0,82 [0,73–1,00] | 0,49 [0,19–0,88] | no | 0,34 | 0,29 |

- **La medida 2g (huecos entre controles)** distingue con el balón limpio (`r1` 0,84 frente a `r3` 0,23,
  171 huecos). Con el balón degradado se queda en unos 4–90 huecos en los 7 partidos: uno o ninguno en la
  ventana.
- **Los toques sueltos distinguen** mientras el tracking no pierda casi todas las disputas (hasta el 75 %)
  y el ruido no pase de unos 10 cm.
  - **Pero en la ventana hay pocos casos.** Con 1,2–2 por minuto vivo saldrían 5–8, justo el mínimo de la
    regla. Si se pierde la mitad de las disputas o más, quedan 5 o menos.
  - [inferencia] Aun con 5–8 casos, la respuesta es orientativa.
- **Si el tracking pierde todas las disputas, no distinguen.** Desaparecen casi todos los toques del
  rival, y los pocos que quedan "cambian" también con la corregida, porque el control que vino después no
  se ve.
- **Pregunta 2, la fecha.** Este instrumento ve si la GT fecha el cambio en el toque o después, no si
  exige control: la corregida también lo fecha en el toque y da casi lo mismo.
  - De los 12 cambios de la ventana tendrían toque visible unos 10 con el balón limpio, 7–8 con pérdidas
    al azar y 3 si se pierden todas las disputas.
- **La variante ampliada** da lo mismo sin ruido. Con ruido distingue peor, y con 10 cm ya no distingue en
  ninguna condición.

**Qué se espera de la ventana** [inferencia]: depende de qué parte de los frames con balón del ATD son
disputas.

- **Cerca del 21 %:** la pregunta 3 tiene una respuesta orientativa.
- **Del 14 % para abajo:** sin decidir. `DATA.md` hace pensar que es lo más probable ("goes missing
  disproportionately on the frames that matter").

En cualquier caso, la ejecución mide cómo es el balón del ATD: visibilidad, disputas, temblor, y toques y
controles por minuto. Es lo que necesita la degradación DFL→ATD, el paso 3 de «Dónde estamos».

## 7. Regla final para leer la ventana (fijada antes de ejecutarla, 14/11)

Sustituye a la de la sección 4. Se aplica a la salida de `validation/partido/recuento_ventana.py`, que
ejecuta una persona una sola vez. Los pasos 1 y 2 solo usan tracking, no etiquetas.

1. **Condición de la DFL que se parece al ATD** (variante base, tabla de la sección 6):
   - **disputas tapadas:** la fila cuya proporción de disputas entre los visibles (sin ruido: 21,3; 17,1;
     13,9; 7,7; 0,0 %) esté más cerca de la del ATD;
   - **ruido:** la de temblor más parecido por cociente (2,2; 29,5; 72,5 cm).
2. **Control de cordura:** los toques y los controles por minuto vivo del ATD tienen que estar a menos del
   doble y a más de la mitad de los de esa condición. Si no, el ATD no se parece a nada de lo calibrado: sin
   decidir.
3. **Si en esa condición el instrumento no distingue** (columna "¿distingue?"): sin decidir con el
   tracking.
4. **Pregunta 3.**
   - Se usan los huecos si hay 5 o más; si no, los toques sueltos, que también necesitan 5 o más.
   - Con `r` la proporción de la GT, `r1` y `r3` los de la condición elegida y `m = (r1 + r3) / 2`:

     | resultado | lectura |
     |---|---|
     | `r ≥ m + 0,10` | la GT cambia con toques del rival sin control (lectura 1 o 2): toca revisar con Ismael la decisión del 12/11 |
     | `r ≤ m − 0,10` | la GT exige control (lectura 3), como se decidió el 12/11 |
     | en medio | sin decidir |
5. **Variante ampliada.** Solo cuenta si distingue en la condición elegida (la suya, en la tabla de
   `calibrar_dfl.py --tabla`). Si allí distingue y da el veredicto contrario: sin decidir. Si no distingue,
   no se mira.
6. **Pregunta 2, la fecha.** Solo con 6 cambios o más con toque visible.
   - **En el toque:** la proporción "en el toque" es al menos la del flag en esa condición menos 0,25.
   - **Después del toque:** "poco después" y "más tarde" suman la mitad o más.
   - Si se cumplen las dos, o ninguna: sin decidir.
7. **Pregunta 1:** descriptiva. Son 3 posesiones.
8. **Si queda sin decidir,** se lleva a Ismael con dos salidas:
   - preguntar a la organización;
   - mirar a ojo solo los casos que el tracking no ve, con el protocolo de la sección 17 del experimento 1,
     apuntando solo recuentos.
9. **De aquí no sale ningún parámetro,** solo la convención. El margen y la definición de control se fijan
   con la DFL.

## 8. Antecedente: la regla del temporizador de Antonio, medida en la DFL (14/11)

Se apunta aquí y no en la bitácora del experimento 1 para no chocar con sus secciones 16 y 17, que están
en la rama `exp/recuento-video-ventana-publica` (PR #1).

**Hipótesis de Antonio** (13/11) [sin verificar]: la posesión pasa al equipo que toca el balón con
intención, salvo que el equipo que la tenía lo vuelva a tocar antes de N frames.

- Sobre el flag de la DFL, que cambia en cada toque, eso equivale a quitar las rachas X → y → X de menos de
  N frames.
- La intención no se ve en el tracking y no se modela.

**Cómo se midió:** `validation/experimento1/temporizador.py`, sobre los 7 partidos, con criterios fijados
en su docstring antes de ejecutarlo. Es descriptivo: no elige N.

**Resultados** [medido]:

| etiquetas | posesiones | cambios H↔A por minuto vivo | posesiones de menos de 3 s | frames vivos que cambian |
|---|---|---|---|---|
| flag tal cual | 3.061 | 6,38 | 43,1 % | 0 % |
| N = 5 | 2.965 | 6,12 | 41,2 % | 0,03 % |
| N = 10 | 2.923 | 6,00 | 40,4 % | 0,05 % |
| N = 15 | 2.879 | 5,88 | 39,6 % | 0,10 % |
| N = 25 | 2.705 | 5,41 | 35,7 % | 0,42 % |
| corregida "C0-12 o dos toques" | 1.736 | 2,78 | 16,0 % | 6,76 % |

- **Rachas X → y → X del flag, por duración:**
  - 68 duran de 1 a 6 frames, sobre todo 3–4;
  - 11 duran de 7 a 10;
  - de 11 a 25 frames vuelven a subir.

  Si la regla del temporizador existe, la DFL sugiere un margen de ese orden. [inferencia]
- **Referencias humanas:** con el temporizador, igual que con el flag tal cual.
  - Pases completados: 97,8–98,0 %.
  - Recuperaciones: 89,2 %.
  - Duelos con `PossessionChange` true: 87,3–88,6 %.
  - Duelos con `PossessionChange` false: 45,5–47,4 %.

  Con la corregida, los duelos false suben al 74,9 % y los true bajan al 84,3 %.
- **El temporizador apenas cambia las etiquetas:** con N = 10 quita unas 140 de 3.061 posesiones. Las dos
  convenciones se separan un factor 2 en cambios por minuto, así que elegir bien la convención es lo que
  más pesa.
- **La ventana pública,** con cautela [inferencia]:
  - tiene 12 cambios directos en unos 4 minutos de juego (≈3 por minuto) y 3 de 17 posesiones de menos
    de 3 s (18 %);
  - se parece más a la corregida (2,78 y 16 %) que al temporizador (6,0 y 40 %);
  - son 5 minutos de otro partido y de otra liga: no prueba nada y no se usa para elegir;
  - la pregunta 3 de la sección 7 es la que puede separarlo.

## 9. Resultado en la ventana pública (14/11)

Ismael ejecutó `validation/partido/recuento_ventana.py` una vez, en local, y pegó la salida: solo
agregados. Está tal cual en `validation/resultados/2026-11-14_experimento2_convencion_tracking.md`.

**Calidad del ATD en la ventana** [medido]: no falta ningún frame y las 7.500 líneas tienen 46 slots.

| medida de tracking (variante base) | ATD, ventana | DFL limpia | DFL, condición elegida (50 % de disputas tapadas, sin ruido) |
|---|---|---|---|
| balón visible en juego | 93,5 % | 100 % | 59,0 % |
| disputas entre los frames con balón | 14,6 % | 21,0 % | 13,9 % |
| temblor del balón | 1,2 cm | 2,2 cm | 2,2 cm |
| toques con equipo por minuto vivo | **2,2** | 37,9 | 20,1 |
| controles Ret-12 por minuto vivo | 13,4 | 13,4 | 9,4 |

**La regla de la sección 7, paso a paso:**

1. **Condición:** las disputas (14,6 %) quedan más cerca de la fila del 50 % (13,9 %), y el temblor
   (1,2 cm) de la fila sin ruido (2,2 cm).
2. **Cordura:** no pasa. Los toques por minuto del ATD son 0,11 veces los de esa condición (2,2 frente a
   20,1), muy por debajo de la mitad. Los controles sí están en rango (1,43 veces). **Resultado: sin
   decidir**, porque el ATD no se parece a nada de lo calibrado.
3. **Para que conste**, aunque la regla ya no llega aquí [medido]:
   - **pregunta 3:** 0 huecos y 0 toques sueltos del rival en la variante base; 3 toques sueltos en la
     ampliada (cambia 1), por debajo de 5;
   - **pregunta 2:** ninguno de los 12 cambios tiene un toque visible en la base, y 1 en la ampliada. Eso
     pasa aunque los 12 tienen balón visible en al menos la mitad de ±1 s;
   - **pregunta 1:** las 3 posesiones cortas tienen balón visible, pero ni control Ret-12 ni toque
     detectado del equipo de la racha ("nada").

**Por qué no sale ningún toque.** Exploración hecha después de ver los agregados de la ventana, solo con
tracking y datos abiertos; no estaba fijada antes.

- [medido] En la DFL, suavizar el balón con una media móvil reproduce las tres medidas de tracking del
  ATD:

  | media móvil (frames) | temblor | toques con equipo por minuto | controles Ret-12 por minuto |
  |---|---|---|---|
  | 1 (sin suavizar) | 2,2 cm | 37,9 | 13,4 |
  | 5 | 0,8 cm | 33,4 | 13,2 |
  | 11 | 0,8 cm | 19,3 | 12,7 |
  | **25** | **0,9 cm** | **3,5** | **10,4** |
  | 51 | 0,7 cm | 0,1 | 6,5 |
  | ATD, ventana | 1,2 cm | 2,2 | 13,4 |

- [inferencia] El balón del ATD se comporta como uno **suavizado en torno a 1 s**. El detector de toques
  del experimento 0 compara la velocidad media de 4 frames antes y 4 después: con un balón así, un golpeo
  no llega a 3 m/s de cambio en 4 frames. La proximidad (Ret-12) sí aguanta.
- [inferencia] No sabemos si es suavizado de verdad o interpolación entre detecciones. Tampoco si en el
  resto del partido es igual: en la ventana falta el 6,5 % del balón, y `DATA.md` da un 41 % para todos
  los frames evaluados.

**Qué implica:**

- **La convención sigue sin medir.** Se mantiene la decisión del 12/11 (exigir control).
- **Para el pipeline, aunque no responda a la convención,** esto es lo más útil del experimento:
  - nada que dependa de cambios bruscos de la velocidad del balón, calibrado en la DFL, funciona tal
    cual en el ATD;
  - la degradación DFL→ATD tiene que suavizar el balón (del orden de 1 s), no solo quitarlo y meter ruido
    independiente frame a frame;
  - con un balón suavizado 1 s, fechar un cambio al frame con el balón es difícil. Un desfase de 25 frames
    deja el `spellF1` de una posesión en 0,65.
- **Siguiente paso propuesto:** medir el balón del ATD en todo el partido con un script de
  `validation/partido/` que solo use tracking (sin etiquetas):
  - visibilidad y longitud de los huecos;
  - si está suavizado (autocorrelación de la velocidad, cambios de dirección en ventanas largas);
  - la columna de velocidad del ATD frente a la calculada.

  Con eso se calibra la degradación y un detector de toques que funcione en el ATD. Después se podría
  repetir la ventana con un instrumento nuevo y su regla fijada antes.

**Relación con el diagnóstico del balón del ATD de Manuel** (`validation/resultados/2026-11-12_balon_muerto_atd.md`
y su revisión del 13/11, ya en `main`):

- **Encaja:** su detector de golpeo no encuentra el golpeo en ninguno de los 6 saques iniciales. Es lo
  esperable con un balón suavizado en torno a 1 s. [inferencia]
- **Lo matiza:**
  - él midió en todo el partido un salto mediano de 0,20 m entre frames seguidos (5 m/s) y lo leyó como
    temblor;
  - en la ventana, la segunda diferencia (lo que aquí se llama temblor) es de 1,2 cm, así que esos saltos
    serían sobre todo movimiento de un balón con trayectoria suave, no ruido;
  - [inferencia] solo con la ventana: en el resto del partido puede ser distinto.
- **El siguiente paso se coordina con lo suyo:**
  - `validation/partido/agregados_balon_reinicios.py` ya compara la columna de velocidad del ATD con el
    desplazamiento suavizado a 0,5 y 1 s;
  - la medida del suavizado del balón en todo el partido debería ir en ese mismo bloque, o en uno hermano
    que lea el ATD con `possession/io.py`, en vez de con el lector propio de `recuento_ventana.py`.
