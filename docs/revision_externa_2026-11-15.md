# Revisión externa del repositorio · 2026-11-15 · Claude (revisor externo, sesión de Ismael)

> **Encargo de Ismael (15/11):** encontrar los puntos débiles de método, de validación y de código; buscar
> fuera métodos, código y datasets que puedan mejorar la nota; y proponer mejoras ordenadas por lo que dan
> frente a lo que cuestan.
>
> **Regla nº 1 respetada.** No se ha abierto ningún dato del partido: ni `MTAH_DATA_DIR`, ni `data/`, ni
> ficheros `BAR-ATH_*`, ni vídeo, ni nuestras entregas, ni `evaluation/reports/`. Todo lo que se cita del
> partido son agregados que ya estaban en `validation/resultados/` y en `docs/decisiones.md`.
>
> **Qué se ha leído:** `CLAUDE.md`, la documentación oficial (`CHALLENGE`, `EVALUATION`, `DATA`, `FAQ`,
> `RULES`, `OVERVIEW`), `evaluation/possession_metrics.py`, `docs/PLAN_ENTREGA.md`, `docs/decisiones.md`,
> `docs/investigacion_metodos.md`, todo `possession/`, el harness y los resultados de
> `validation/resultados/`.
>
> **Qué se ha ejecutado:** solo el harness y cuatro scripts propios sobre los 7 partidos abiertos de la
> Bundesliga (Bassek et al., 2025, CC BY 4.0), con `MTAH_DATA_DIR` apuntando a una ruta que no existe. El
> código es el de `main` en `05b6d98`, sin cambios. Los scripts y sus salidas están **fuera del repo**: el
> encargo solo permitía escribir este fichero. Las medidas están en el anexo A.
>
> **Etiquetas:** **[doc]** lo dice la documentación o el código oficial; **[medido]** está medido, y se dice
> dónde; **[medido aquí]** lo he medido en esta revisión (anexo A); **[inferencia]** es una deducción sin
> confirmar; **[fuente]** lo dice una fuente externa de la sección 7; **[sin verificar]** no lo he podido
> comprobar.
>
> **Sobre el calendario.** El encargo pedía separar lo que cabe antes del corte del lunes 16 a las 14:00.
> Ismael dijo después (15/11) que el tiempo no es el límite y que hay margen hasta el martes. Se mantiene
> la columna «¿cabe antes del corte?» como información; mover el corte es decisión suya.

**En pocas líneas:**

1. **El pipeline es sólido y prudente.** El protocolo (candidatos antes de medir, placebos, dos
   convenciones, nada elegido con la ventana pública) es mejor que el de la mayoría de trabajos publicados
   que he leído. No he encontrado ningún error que rompa la entrega.
2. **El 0,498 del harness es optimista en nivel** [medido aquí]. El baseline oficial saca 0,2433 en el
   partido; el mismo baseline en el harness, con su propio `D`, saca entre 0,310 y 0,397. La diferencia es
   de +0,07 a +0,15. Con ese descuento, lo nuestro quedaría entre 0,30 y 0,50 en el partido
   [inferencia]: por encima del baseline, lejos del 0,498.
3. **La GT del reto no se parece al flag de la DFL tal cual** [medido aquí, descriptivo, bajo D21]. La
   ventana pública es típica de las etiquetas de control y atípica de las del flag. La huella oficial de
   retrasos cae entre las dos, fuera del rango de los 7 partidos con cualquiera de ellas. La decisión del
   12/11 («exigir control») queda mejor apoyada de lo que estaba.
4. **La evidencia de equipo es donde más se pierde, y no tiene arreglo barato** [medido aquí]. Dos
   prototipos distintos encima de B5 (un ancla de retención y un detector de toques a la escala del
   suavizado) empatan con `main`: +0,005 con el flag y −0,008 con control. El suavizado del balón borra la
   proximidad en un tercio de los cambios reales.
5. **Lo que queda con más recorrido no se mide en la DFL:** que el balón opine sobre el `D`, y comprobar
   que el balón del ATD no llega con retraso. Las dos necesitan a una persona con el partido.
6. **Tres cosas que dije en el chat han cambiado al medirlas** (sección 2): retiro el prior de reinicio,
   bajo la expectativa de la evidencia de equipo y cambio la lectura de la convención.

> **Añadido después (15/11, tarde): B5 aguanta con un tracking automático.** A petición de Ismael se midió
> el pipeline en los 20 partidos abiertos de SkillCorner (A-League 2024/25, tracking automático de la
> retransmisión), con una regla escrita antes (`validation/skillcorner/BITACORA.md`). Resultado en
> `validation/resultados/2026-11-15_skillcorner.md`:
> - con el `D` oráculo, `main` gana al baseline por +0,13 en 20 de 20 partidos y a N1 por +0,06 en 19 de 20
>   [medido]. La ventaja de B5 ya no sale solo de la DFL;
> - con solo los jugadores que la retransmisión detecta, la ventaja sobre N1 baja a +0,03 [medido, sin voto];
> - con el `D` propio, el baseline saca 0,249, cerca de su 0,2433 del partido, y `main` 0,381 [medido;
>   descriptivo, bajo D21]. Apunta al centro del rango de 0,30 a 0,50 del punto 2 [inferencia];
> - la huella de las etiquetas de SkillCorner (0,678 a 25 frames) es la más cercana a la oficial (0,654) de
>   todas las medidas, entre el flag y el control de la DFL [medido; descriptivo, bajo D21].
>
> Cambia la sección 3.2, punto 10 («los jugadores del harness son perfectos»): con jugadores automáticos, la
> ventaja de B5 aguanta. Y la tabla de propuestas: la P9 (segundo dataset) ya está hecha como validación.
>
> **Añadido después (15/11, tarde): la convención de los eventos de Metrica tampoco tumba a B5.** Los 3
> partidos de sample-data, con las etiquetas derivadas de sus eventos (toque con impacto) y la regla escrita
> antes en `validation/metrica/BITACORA.md`. Resultado en `validation/resultados/2026-11-15_metrica.md`:
> - con el `D` oráculo, `main` gana al baseline por +0,118 en 3 de 3 y a N1 por +0,058 en 2 de 3 [medido].
>   Son 3 partidos: confirma, no sustituye a la DFL ni a SkillCorner;
> - esas etiquetas tienen 4,70 posesiones por minuto vivo y una huella de 0,724 a 25 frames: entre el flag
>   de la DFL (0,552) y el control (0,808), y menos cerca de la oficial (0,654) que SkillCorner (0,678)
>   [medido; descriptivo, bajo D21]. No se usa para elegir la convención de la entrega. La regla de eventos
>   a etiquetas quedó escrita en `validation/metrica/BITACORA.md` §3 antes de esa huella, y no se ha tocado
>   después;
> - **nota de la revisión (Ismael, 15/11):** la comparación de esa huella con la tabla oficial no es firme.
>   Con la parada en el frame final del evento salen 4,99 posesiones por minuto y una huella de 0,690, y la
>   regla deja paradas sin marcar (`validation/metrica/BITACORA.md` §8). La ventaja de B5 sí aguanta: +0,112
>   frente al baseline y +0,067 frente a N1.
>
> **Nota para Claude sobre el Mundial, sin descarga** (`validation/pff/BITACORA.md`). Ismael dice que las
> normas del reto no prohíben los 64 partidos de PFF FC del Mundial 2022. Claude pide no bajarlos hasta
> que la organización conteste la licencia. Son el único conjunto abierto con tracking de retransmisión y,
> en cada frame, balón vivo o muerto y equipo.

---

## 0. Lo que he entendido del reto y de dónde se partía

### 0.1 El reto

- **Tarea:** una etiqueta por cada uno de los 199.319 frames del vídeo táctico del Barça–Athletic: `H`,
  `A`, `D` (balón muerto) o `X` (sin respuesta). Se evalúan 158.857 frames, las dos partes. [doc]
- **Nota:** `spellF1`. Cada posesión (racha máxima de `H` o de `A`) es un objeto. Las predichas se
  emparejan una a una con las reales del mismo equipo por IoU temporal, y se promedia el F1 con umbrales
  de 0,3 a 0,7. No hay crédito parcial y todas las posesiones pesan igual. El desempate es `macroF1`.
  [doc, `evaluation/possession_metrics.py`]
- **Lo que castiga:** inventar cambios, perder posesiones cortas y llegar tarde. Un retraso uniforme de 8
  frames deja 0,89 y uno de 1 s, 0,65. Las diferencias de menos de 0,04 son ruido. [doc]
- **La GT** sale de forma mecánica de un tracking **corregido** que no tenemos: `D` donde ese tracking
  marca el balón muerto y, si no, el equipo que nombra como poseedor. La definición habla de control
  «controlado», pero remite a la GT pública como referencia. [doc, `CHALLENGE.md` L82–103]
- **Reglas que condicionan todo:** nada se ajusta con los 5 minutos públicos; nada de etiquetas a mano ni
  de datos humanos de este partido; datos de otros partidos, los que se quiera; la entrega se regenera
  byte a byte; los datos no pasan por un LLM en la nube. [doc]

### 0.2 Lo que se daba al empezar

| qué | cómo viene | lo que importa |
|---|---|---|
| tracking automático (ATD) | 46 slots sin identidad y el balón, por frame | el balón falta en el 41 % de los frames evaluados; nada está corregido |
| Smart Tagging | 638 intervalos automáticos | 59 `SET PIECES` (los 26 saques de banda, sin equipo), 4 `GOALS` y 575 fases; 36 intervalos no traen equipo |
| homografía | una matriz por frame | válida en el 100 % del táctico |
| vídeo táctico | 25 fps, 1920×1080 | el índice de la entrega; trae audio (lo vio Antonio) |
| retransmisión | vídeo, ATD y homografía | sin sincronizar con el táctico |
| GT pública | 5 minutos, 17 posesiones | solo para comprobar el pipeline |
| código oficial | scorer, validador, `games.py`, lectores | el scorer es el mismo que usará la organización |
| baseline | jugador más cercano y voto por mayoría | 0,0486 sin suavizar; 0,1996 / **0,2433** / 0,2242 con ±25 / ±50 / ±125 |

### 0.3 Dónde está el equipo

- **Pipeline** (`possession/pipeline.py`): evidencia de equipo B5, estado de `D` con jugadores (E2),
  anclas de `D` (tramo antes del saque y hueco antes de cada reinicio) y Viterbi con coste 25.
- **Entrega vigente, `equipo_v3`:** 45,1 % de `D`, 113 paradas y 215 posesiones de 16,2 s de media
  [medido, `docs/decisiones.md` L1653–1661].
- **Harness de la DFL:** 0,498 / 0,512 con el flag y 0,728 / 0,748 con control, con el `D` copiado de las
  etiquetas. Con el `D` propio, 0,416 y 0,616. [medido; repetido aquí con los mismos números, anexo A.1]

### 0.4 Dónde se quiere llegar

- **El objetivo es relativo:** pasan los 20 mejores. No hay tabla pública y no se sabe dónde estará el
  corte [sin verificar].
- **Lo que sí se puede decir** [inferencia, sección 3.2]: lo nuestro debería quedar entre 0,30 y 0,50 en
  el partido. Es batir el baseline con margen. No es el 0,5–0,7 que sugiere el harness.
- **Una observación** [cálculo sobre agregados ya publicados]: la entrega tiene 3,7 posesiones por minuto
  de juego (215 en unos 58 minutos vivos). El mismo pipeline da 4,5 en la DFL, la GT pública tiene 4,2 y
  las etiquetas de control de la DFL, 4,7. Puede ser el partido o puede ser que en el ATD se nos escapen
  más cambios. No se puede saber sin la GT.

---

## 1. Resumen: las cinco cosas que haría, en orden

| # | qué | quién | horas | ¿cabe antes del corte? | qué puede dar |
|---|---|---|---|---|---|
| 1 | **Comprobar que el balón del ATD no llega con retraso** (propuesta P1): la línea de latencia de `/evaluar` y un agregado nuevo del partido | Ismael, con un script que escribe Claude | 2–3 | sí | nada si no hay retraso; hasta +0,04 a +0,07 si hay 8–12 frames y se corrigen |
| 2 | **Que el balón opine sobre el `D`** (P2): balón fuera de las líneas, todos los huecos largos, más peso al principio del hueco y el fin del `D` en la reaparición del balón. Y preguntar a la organización cómo se construyen las ventanas de 35 s | Manuel | 4–6, más dos ejecuciones suyas | depende de que Manuel ejecute hoy | de 0 a +0,04 |
| 3 | **Congelado sin sorpresas** (P3): versiones fijadas, ancla de juego vivo en el saque, comprobación de líneas leídas, reproducción en una máquina limpia y con otro Python | Ismael | 2–3 | sí | evita un cero |
| 4 | **Una sola ronda de reentrenamiento de B5** (P4), con tres candidatos escritos antes. Expectativa baja | Ismael (sesión de la apuesta B) | 3–5 | sí | de −0,01 a +0,02 |
| 5 | **Dejar escrita la convención y el nivel esperado** (P5): apuntar en `docs/decisiones.md` las medidas del anexo A, insistir con D21 y contar el rango esperado en el documento técnico | Ismael y Ana | 1–2 | sí | no cambia la nota; evita decidir a ciegas |

**Por qué este orden.**

- **La 1 es la única palanca grande que nadie ha mirado.** Un retraso sistemático cuesta más que cualquier
  mejora que hayáis medido, y comprobarlo es barato.
- **La 2 ataca la segunda pérdida medida** (el `D` propio cuesta entre 0,08 y 0,11 en el harness, y ese
  número es optimista) y es lo único grande que queda sin intentar.
- **La 3 no sube la nota, pero un CSV que no se regenera vale cero.**
- **La 4 va cuarta porque la he medido en parte y no promete** (sección 3.1, punto 1).
- **Fuera de la lista:** el prior de reinicio que propuse en el chat. Lo medí y no tiene señal.

---

## 2. Lo que cambia respecto a lo que dije en el chat (15/11, 12:58)

Aquel mensaje se escribió sin poder ejecutar nada. Al medir, cambian estas cosas:

| lo que dije | lo que sale al medir | qué hago |
|---|---|---|
| Prior de reinicio: tras una parada suele sacar el otro equipo (era la 4ª de las cinco) | `main` solo se equivoca de equipo en el primer segundo del 5,5–5,7 % de los reinicios. El equipo real tras la parada es distinto del que decía `main` antes de ella en el 42,5 %: el prior «el contrario» no informa | la retiro |
| Ancla de retención encima de B5: +0,02 a +0,06 | +0,006 con el flag y −0,008 con control: empate, y el signo depende de la convención | bajo la expectativa de toda la propuesta a «de −0,01 a +0,02» |
| Un detector de toques a la escala del suavizado «sigue viendo los pases» | Los ve: 24–28 eventos por minuto, frente a 3,7 con el detector de 4 frames. Pero solo cubre el 37–43 % de los cambios (mi regla pedía el 50 %) y, como evidencia añadida, también empata | pasa de «+0,02 a +0,05» a «no entra tal cual» |
| Convención: «daría peso 50/50» | La ventana pública es típica de control y atípica del flag. La huella oficial queda entre las dos | me inclino por control o algo intermedio; el flag tal cual es lo menos apoyado |
| Huella de las etiquetas de control: «estimo 0,79» a mano | 0,808, con los 7 partidos entre 0,76 y 0,84 | sustituyo la estimación |
| El contraste del harness con los baselines era una propuesta | Lo he ejecutado: el harness sobrestima el nivel entre +0,07 y +0,15, y conserva el orden de las ventanas con control, pero no con el flag | pasa de propuesta a resultado |
| Recuento a ojo de la PR 1: «no lo mergearía como evidencia» | Releídas `CHALLENGE.md` L82–87 y `RULES.md` L55–71: es zona gris, no una infracción clara | lo matizo en la sección 3.4 |

---

## 3. Puntos débiles, de más a menos grave

### 3.1 Método

**1. Faltan cambios de posesión, y lo barato ya está probado.**

- **Qué pasa.** `main` predice 951 cambios de equipo; hay 1.026 con control y 2.351 con el flag. Encuentra
  el 27 % (flag) y el 53 % (control) de las posesiones de 2 a 5 s, y el 58 % y el 76 % de las de 5 a 10 s
  [medido, `docs/decisiones.md` L1816–1824]. Los costes 12 y 50 empatan [medido, L1750–1770].
- **Por qué** [inferencia]. B5 pesa sobre todo las ventanas de 151 frames (`possession/aprendida.py` L41 y
  `2026-11-14_apuesta_b.md` §2), se entrenó solo donde el flag y control coinciden, y con pérdida por
  frame. Está hecha para acertar el equipo, no el instante del cambio.
- **Lo nuevo: hay un límite de información** [medido aquí, anexo A.4]. En los cambios reales del flag, el
  equipo nuevo es el más cercano a 1,5 m o menos en ±0,5 s en el 94 % de los casos con el balón limpio.
  Con el balón «como el ATD, sin bloques» (la misma visibilidad, pero suavizado 25 frames), en el 63 %.
  Con «como el ATD», en el 56 %. **El suavizado borra la proximidad en un tercio de los cambios.**
- **Lo nuevo: dos añadidos distintos encima de B5 empatan** [medido aquí, anexos A.3 y A.5]:

  | prototipo | flag, como el ATD | flag, sin bloques | control, como el ATD | control, sin bloques |
  |---|---|---|---|---|
  | B5 + ancla de retención | +0,006, 5 de 7 | +0,007, 5 de 7 | −0,008, 2 de 7 | −0,008, 3 de 7 |
  | B5 + evento de toque a escala | +0,005, 7 de 7 | +0,006, 5 de 7 | −0,008, 1 de 7 | −0,008, 2 de 7 |

  Los dos encuentran dos o tres puntos más de posesiones reales en casi todos los tramos de duración, y
  los pagan con entre 85 y 127 posesiones predichas de más.
- **Lectura** [inferencia]. Sumados a lo anterior del equipo (N2, Ret y B1 tampoco ganaron a `main`), son
  cinco intentos por proximidad o por reglas que no mueven la nota. Lo que falta no es otra regla: es
  información que el balón suavizado no trae, o un modelo que aprenda el instante del cambio.
- **Las de menos de 1 s (el 2 % encontradas) no son recuperables** con un balón suavizado 1 s
  [inferencia].

**2. Las fronteras del `D` son la segunda pérdida.**

- E2 detecta el 86 % de las paradas, pero acierta el inicio a 1 s en el 35 % y el fin en el 40 %. El
  inicio va de −127 a +116 frames entre el p10 y el p90 [medido, `2026-11-14_d_estado.md`].
- Con el equipo perfecto: sin `D`, 0,770; con E2, 0,809; con el `D` perfecto, 1,000. E2 recupera 0,04 de
  0,23 [medido, ídem].
- Antes de los saques de banda y de puerta los jugadores no frenan (44 % y 36 % de frames lentos, frente
  al 91 % antes de un córner) [medido, `2026-11-14_agregados_jugadores_atd.md`]. Son 36 de los 59
  reinicios etiquetados, y en un partido normal son la mayoría de las paradas [fuente, Siegle y Lames,
  vía `docs/investigacion_metodos.md` §2.2].

**3. El balón casi no opina sobre el `D`.**

- Solo lo hace la capa del hueco: 28 de 53 reinicios, con peso 1 frente a los ±8 de E2. Movió el `D` del
  44,4 al 45,1 % [medido, `docs/decisiones.md` L1616–1661].
- No se usan dos señales que ya están medidas: el balón visto fuera de las líneas (el 4,2 % de los frames
  con balón [medido, 12/11]) y el resto de los 131 huecos largos [medido, `2026-11-14_perfil_atd.md`].
- El perfil dice que la mayor parte del balón que falta sería balón muerto [inferencia del equipo]. Si es
  así, el inicio de un hueco largo es la mejor pista del inicio de una parada que tenéis, y hoy solo se
  usa delante de un `SET PIECES`.

**4. Hay cuatro escalas acopladas sin una medida conjunta.**

- α = 4 de B5, el recorte a ±8 de E2, `GAP_SCORE` = 1 y `to_dead` / `from_dead` = 25.
- El propio código dice que nadie puede medirlas (`possession/temporal.py` L24–31 y
  `possession/dead_ball.py` L161–165). Con el `D` oráculo no cambian nada.
- La sensibilidad de Ana dice que la escala de E2 a la mitad sale algo mejor (+0,007) y al doble deja de
  cumplir §5.8 con el flag [medido]. Es decir: la entrega está cerca de un borde por arriba.

**5. Las fases del Smart Tagging no se usan como pista de equipo.**

- Cubren el 68,1 % de los frames evaluados [medido, `2026-11-14_agregados_balon_muerto.md`].
- `OVERVIEW.md` L128 define `Team` como «the team performing the event», y «Attacking Transition» como lo
  que sigue a recuperar el balón [doc]. Las transiciones son 48 intervalos que apuntan justo a las
  recuperaciones, que es lo que B5 pierde.
- No se puede medir en la DFL. Por eso va con poco peso y detrás de lo demás.

**6. Tras un reinicio, `main` acierta el equipo casi siempre** [medido aquí, anexo A.2].

- Se equivoca en el primer segundo en 38–40 de 696 reinicios (5,5–5,7 %), con el `D` oráculo.
- No es un punto débil en la DFL. En el partido, con el `D` propio y el balón que falta alrededor de los
  reinicios, puede ser peor [sin verificar].

### 3.2 Validación

**7. El harness sobrestima el nivel** [medido aquí, anexo A.1].

- **Qué se midió:** los cuatro baselines oficiales dentro del harness, cada uno con su propio `D`, como en
  el partido.

  | | sin suavizar | ±25 | ±50 | ±125 |
  |---|---|---|---|---|
  | **partido completo (oficial)** | 0,049 | 0,200 | **0,243** | 0,224 |
  | flag, como el ATD | 0,117 | 0,306 | 0,310 | 0,218 |
  | flag, sin bloques | 0,124 | 0,339 | 0,346 | 0,228 |
  | control, como el ATD | 0,069 | 0,287 | 0,353 | 0,308 |
  | control, sin bloques | 0,074 | 0,322 | 0,397 | 0,329 |

- **Con la regla fijada antes:**
  - **nivel:** no es creíble. El ±50 queda a +0,067, +0,103, +0,110 y +0,154 del oficial; la regla pedía
    ±0,05;
  - **orden:** se conserva (±50 > ±125 > ±25 > sin suavizar) con las etiquetas de control en las dos
    condiciones que votan. Con el flag, no: ±25 y ±125 salen al revés.
- **Qué implica para lo nuestro** [inferencia]. `main` con el `D` propio saca 0,416 / 0,433 (flag) y
  0,616 / 0,642 (control). Si el harness nos sobrestima como al baseline:

  | supuesto | flag | control |
  |---|---|---|
  | la misma diferencia absoluta | 0,33–0,35 | 0,49–0,51 |
  | la misma proporción | 0,30–0,33 | 0,39–0,42 |

  **De 0,30 a 0,50.** No es un pronóstico. Supone que el optimismo es el mismo para nosotros que para el
  baseline, y no tiene por qué:
  - a favor de menos descuento: el baseline hace el `D` con «no hay balón», que el harness regala y el
    partido no; lo nuestro lo hace con los jugadores, que sí se trasladan [medido por el equipo];
  - a favor de más: los rasgos de forma de B5 no están comprobados en el ATD, y las fronteras del `D`
    tampoco.
- **Mirado después, sin regla previa:** las proporciones entre ventanas del partido (0,20 / 0,82 / 1 /
  0,92) se parecen mucho a las del harness con control y «como el ATD» (0,20 / 0,81 / 1 / 0,87), y poco a
  las del flag (0,38 / 0,99 / 1 / 0,70). Apunta en la misma dirección que el punto 8.
- **Aviso de reglas:** compara con las notas oficiales del baseline, que salen de la GT privada. Es
  descriptivo y no elige nada (sección 3.4, punto 17).

**8. La convención: el flag tal cual es lo menos apoyado** [medido aquí, anexo A.6; descriptivo, bajo D21].

- **La huella de retrasos a 25 frames:**

  | | los 7 juntos | por partido, mín–máx |
  |---|---|---|
  | DFL con el flag | 0,552 | 0,494–0,613 |
  | **oficial (`EVALUATION.md`)** | **0,654** | – |
  | DFL con control | 0,808 | 0,763–0,844 |

  La oficial no cae dentro del rango de ninguna de las dos. Con 3 y 8 frames pasa lo mismo: siempre queda
  entre las dos.
- **La ventana pública frente a 129 ventanas de 7.500 frames de la DFL:**

  | | ventana pública | DFL con el flag: p10–p90 | DFL con control: p10–p90 |
  |---|---|---|---|
  | posesiones por minuto vivo | 4,23 | 5,23–13,44 (solo el 5 % de las ventanas queda por debajo de la pública) | 3,18–7,44 (el 29 % queda por debajo) |
  | huella a 25 frames | 0,777 | 0,43–0,73 (el 95 % queda por debajo de la pública) | 0,69–0,93 (el 30 % queda por debajo) |

  Con la regla fijada antes: la ventana pública es típica de control y atípica del flag.
- **Lectura** [inferencia]. La GT del reto tiene más posesiones cortas que las etiquetas de control de la
  DFL y menos que su flag. Caben tres explicaciones, y no se pueden separar:
  - una convención intermedia (el «toque con impacto significativo» de los eventos de Metrica);
  - control, con un partido más cortado que los siete de la DFL;
  - otra liga y otro operador.
- **Qué implica.**
  - La decisión del 12/11 queda mejor apoyada que cuando se tomó.
  - La frase «el flag es el mismo tipo de etiqueta que la GT del reto: lo que no aguante con el flag no
    cuenta» (`docs/PLAN_ENTREGA.md` §3) le da al flag un veto que estas medidas no respaldan del todo.
  - **Ninguna decisión pasada cambia:** lo que perdía con el flag tampoco ganaba 0,03 con control (el
    coste 50 da +0,010; N2 y Ret empatan).
- **Lo que decía a favor del flag sigue ahí y pesa menos.** La GT parece TRACAB [inferencia: los IdFrame
  de `games.py` L51–55 son frames desde medianoche a 25 Hz, y 1.713.242 / 25 da las 19:02:10], como la
  DFL. Pero dos flags del mismo proveedor pueden no comportarse igual, y aquí las medidas dicen que no.

**9. No se ha medido si el balón del ATD llega con retraso.**

- El harness suaviza con una media **centrada** (`validation/harness/dfl.py` L106–116 y L179–181). El
  perfil midió cuánto suaviza el ATD (unos 25 frames), no si el filtro es centrado o causal.
- Si fuera causal, el balón llegaría unos 12 frames tarde, y todos los cambios con él [inferencia]. Ocho
  frames de retraso cuestan un 11 % de la nota [doc].
- En el repo solo hay latencias con signo de los baselines en la ventana pública, con 2 a 11 parejas: no
  dicen nada [medido, `2026-11-11_baselines_ventana_publica.md`]. De nuestras entregas no hay ninguna
  apuntada.

**10. Los jugadores del harness son perfectos.**

- No hay duplicados, ni slots con el equipo cambiado, ni detecciones falsas. La medida con jugadores
  degradados «no concluye» por su propia regla (`docs/decisiones.md` L640–666).
- Los rasgos de forma de E2 y de B5 (centroides, dispersión, dirección de ataque) no están comprobados en
  el ATD: la regla de traslado no los cubre (L868–869) y B5 con jugadores como el ATD se midió sin voto
  (L1236–1247).

**11. Decisiones apoyadas en medidas flojas o circulares.**

- **El golpeo del reinicio (R1)** se descartó porque no coincide con la subida de velocidad de los
  jugadores (`docs/decisiones.md` L1422–1452). Vuestros propios agregados dicen que antes de los saques
  de banda y de puerta los jugadores no frenan, así que no hay subida que buscar. El criterio no tenía
  potencia en 36 de las 53 ventanas [inferencia]. R1 no quedó refutado: quedó sin medir.
- **La capa del hueco** pasó con 52,8 % frente al 50 % pedido (dos huecos menos y no entra), y su juez es
  el modelo de Ana, al que la capa corrige [medido, L1616–1643]. La entrada lo dice. Lo apunto porque mi
  propuesta P2 se apoya en la misma capa.
- **B5 es el quinto candidato** de la apuesta B sobre los mismos 7 partidos (B1 a B5). El sesgo de
  selección es pequeño frente a su margen de +0,07 [inferencia], y los criterios se escribieron antes.
- **Las etiquetas de control** son circulares con cualquier evidencia de proximidad. Está dicho y tratado
  en el README del harness.

**12. Lo que no se puede medir:** el `D` con balón (la DFL lo congela), nada que use el Smart Tagging, y la
nota real.

### 3.3 Código

No he encontrado ningún error que cambie etiquetas de forma grave. Lo que sigue va de más a menos
importante.

**13. La reproducción byte a byte tiene cuatro flecos.**

- **`requirements.txt` no fija versiones** (L9–10) y se trabaja con Python 3.13. El scorer oficial presume
  de 3.8 y 3.11. Si la organización regenera con otro numpy, el resultado está [sin verificar].
- **`np.exp`** (`possession/aprendida.py` L109) **y `np.hypot`** (`possession/dead_state.py` L162) no
  garantizan el último bit entre CPU. El redondeo a 6 decimales y a 1/1024 lo hace improbable. Está
  probado en dos máquinas x86 [medido]; no en ARM ni con otro numpy.
- **El nombre por defecto es `equipo_v0`** (`possession/pipeline.py` L26). El comando que se documente
  tiene que escribir el fichero con el nombre del equipo.
- **`possession/io.py` no comprueba cuántas líneas ha leído.** Las líneas mal formadas se saltan en
  silencio (L26–27 y L55–56) y sus frames quedan a `NaN`. Con un ATD truncado saldría una entrega válida
  y distinta, sin aviso.

**14. `dead_state.window_mean` no respeta los tramos evaluados** (`possession/dead_state.py` L200–213).

- Las ventanas de hasta ±2 s cruzan el inicio de cada parte. En el harness, antes de la parte hay un
  hueco vacío y la media lo ignora. En el partido hay jugadores parados antes del saque.
- Los primeros 1–2 s de la 1ª parte reciben evidencia de `D` que el harness nunca ve [inferencia]. El FAQ
  dice que el primer frame evaluado de la 1ª parte ya es juego [doc], y no hay ningún ancla que lo diga:
  `dead_ball.evidence` solo prohíbe `H` y `A` antes del saque (L248–249).
- Afecta, como mucho, a la primera posesión de cada parte: muy poco en la nota. Lo apunto porque es una
  diferencia entre lo que valida el harness y lo que se entrega.

**15. Menores.**

- **Un slot duplicado cuenta doble** en los núcleos gaussianos de B5 (`possession/aprendida.py` L105–109).
  `DATA.md` dice que el tracker a veces duplica a alguien [doc].
- **`pipeline.main` escribe el CSV aunque haya piezas en conflicto** y sale con error después (L162–171).
  El fichero malo se queda en `evaluation/results/` con el nombre bueno.
- **El resumen de la entrega no imprime cuántas rachas cortas hay** (por ejemplo, de menos de 12 y de 25
  frames). El criterio del 13/11 lo pide y hoy no se ve.
- **Compatibilidad con Python 3.8** de `possession/` [sin verificar, solo leído]: no usa f-strings ni
  sintaxis nueva, así que debería correr.

### 3.4 Reglas

**16. El recuento a ojo de la [PR 1](https://github.com/ismaelp8/mtah2027-piso2nyc/pull/1) es zona gris.**

- A favor: `CHALLENGE.md` L82–87 dice que la GT pública está para entender cómo se etiquetan los casos, y
  `RULES.md` L69–71 permite mirar el vídeo para entender.
- En contra: `RULES.md` L55–58 prohíbe etiquetas a mano de este partido «for any purpose», también para
  validar. Clasificar doce cambios como «toque» o «control» es un juicio humano sobre momentos concretos.
- No decidió nada y no se completó. Con las medidas del punto 8 ya no hace falta. Yo no lo usaría como
  evidencia, y lo contaría en el documento técnico con su alcance.

**17. D21 sigue sin respuesta, y esta revisión la roza.**

- Los puntos 7 y 8 comparan con cifras oficiales que salen de la GT privada: las notas del baseline y la
  tabla de retrasos. `RULES.md` §2 prohíbe usar la GT completa «or anything derived from it».
- Son descriptivas: no he elegido ningún parámetro con ellas ni propongo hacerlo. Pero si se usan para
  algo (por ejemplo, para quitarle el veto al flag), hay que tener antes la respuesta de la organización.

**18. Agregados del partido pegados a un LLM en la nube y publicados en el repo.**

- Los términos hablan de «extracts». Un recuento no es un extracto en el sentido corriente, y el equipo
  suprime las celdas de menos de 5. El riesgo me parece bajo [inferencia].
- Aun así, el repo será público con decenas de agregados del partido. Pediría una confirmación por
  escrito y lo explicaría en el documento técnico.

**19. El documento técnico tiene que declarar** el entrenamiento con la DFL (citando a Bassek et al. y a
la DFL, CC BY 4.0), el uso de un LLM para escribir código y documentación, el uso del Smart Tagging y las
constantes de saque de `starter/load_smart_tagging.py`.

---

## 4. Propuestas

Las ganancias son [inferencia] salvo donde se dice. Ninguna se da por buena sin su medida.

### 4.1 Tabla

| id | qué | ataca | ganancia esperada y supuestos | horas | riesgo | dependencias | cómo se mide | ¿antes del corte? |
|---|---|---|---|---|---|---|---|---|
| P1 | Comprobar el retraso del balón del ATD | 9 | 0 si no hay retraso. Si hay 8–12 frames y se corrigen, +0,04 a +0,07 (supone que la tabla oficial de retrasos se aplica en proporción a nuestra nota) | 2–3 | bajo | ninguna | latencia con signo de `/evaluar` y un agregado del partido calibrado en la DFL | sí |
| P2 | El balón opina sobre el `D` | 2, 3 | 0 a +0,04 (supone cerrar entre nada y un tercio de lo que cuesta el `D` propio) | 4–6 | medio: puede forzar `D` en juego | ninguna | regla escrita antes y agregados del partido, como la capa 4 | depende |
| P3 | Congelado sin sorpresas | 13, 14 | evita un cero | 2–3 | bajo | fijar numpy y pandas | sha256 en una máquina limpia y con otro Python | sí |
| P4 | Una ronda de reentrenamiento de B5 | 1 | −0,01 a +0,02 (los dos añadidos medidos empatan) | 3–5 | bajo: si empata, no entra | ninguna | harness con §5.8, eventos y los criterios 2 y 3 de B5 | sí |
| P5 | Convención y nivel esperado, por escrito | 7, 8, 17 | no cambia la nota | 1–2 | ninguno | respuesta de la organización | – | sí |
| P6 | Barrer las escalas del `D` con dos modos de balón | 4 | 0 a +0,02; lo probable es un empate | 2–3 | bajo | ninguna | `validation/apuesta_b/d_propio.py`, balón tapado y a la vista | sí |
| P7 | Fases del Smart Tagging como pista de equipo | 5 | 0 a +0,02 | 3–4 | medio: su escala no se mide | ninguna | acuerdo con B5 en frames de control claro, con placebo | justo |
| P8 | Detector de cambios aprendido (secuencia) | 1 | desconocida | días | alto | quizá un modelo no lineal | harness | no |
| P9 | Segundo dataset con tracking automático (SkillCorner) | 10 | no sube la nota; mide lo que la DFL no puede | 1–2 días | medio | lector nuevo | repetir el harness a 10 fps | no |

### 4.2 Detalle de cada una

**P1. Comprobar el retraso del balón del ATD.**

- **Qué es.** Dos comprobaciones, una barata y una limpia.
  - **La barata:** `evaluation/run_evaluation.py` ya imprime, por entrega, la línea
    `latency mean … median …` a ±25 frames (L350–353). Basta con que Ismael pegue esa línea de
    `equipo_v3`. Es comprobar la alineación, que es para lo que sirve la ventana pública.
  - **La limpia, sin GT:** un agregado del partido. En los tramos en que un jugador lleva el balón (el
    mismo equipo es el más cercano a 1,5 m o menos durante 1 s o más), se busca el desfase que maximiza la
    correlación entre la velocidad del balón y la del jugador más cercano. Un filtro centrado da 0; uno
    causal de 25 frames, unos +12.
- **En qué me apoyo.** El harness supone una media centrada (`validation/harness/dfl.py` L179–181) y nadie
  ha medido la fase. La tabla oficial pone precio al retraso.
- **Cómo se mide.** Antes de tocar el partido, el script se calibra en la DFL: con el balón suavizado
  centrado tiene que dar 0 ± 2 frames y, con una media causal, +12 ± 2. Si no separa, no se ejecuta en el
  partido.
- **Candidatos, antes de medir.**
  1. No tocar nada, si el desfase medido es de 3 frames o menos en valor absoluto.
  2. Desplazar el balón del `Tracking` el desfase medido, si es de 4 frames o más y la latencia de la
     ventana pública tiene el mismo signo.
  3. Si los dos números se contradicen, no tocar nada y apuntarlo.
- **Riesgo.** Que los jugadores también vengan retrasados: el desfase relativo saldría 0 y el absoluto no.
  Por eso van las dos comprobaciones.
- **Lo que no vale:** elegir el desplazamiento que más sube la nota en la ventana pública.

**P2. Que el balón opine sobre el `D`.**

- **Qué es.** Cuatro capas, cada una con su regla, en `possession/dead_ball.py`:
  1. **Balón fuera:** puntuación de `D` en los frames en que el balón se ve más de 1 m fuera de las
     líneas.
  2. **Todos los huecos largos:** la capa 4 de hoy, también en los huecos de 5 a 60 s que no van delante
     de un `SET PIECES`. El Smart Tagging solo trae 59 reinicios y un partido tiene unas 100 paradas (713
     en los 7 de la DFL [medido por el equipo]).
  3. **Más peso al principio del hueco:** 8 por frame en los 2 primeros segundos (el recorte de E2), para
     compensar que E2 llega tarde al inicio (mediana de +14 frames [medido]).
  4. **El fin del `D` en la reaparición:** dejar de puntuar `D` en el primer frame en que vuelve a verse
     el balón tras el hueco, en vez de en el inicio de la ventana.
- **Y una pregunta a la organización** (un issue, que es el canal que dan): cómo se construyen las
  ventanas `SET PIECES` de 35 s exactos y dónde cae el reinicio dentro de ellas. Si el inicio es «el
  reinicio menos una constante», fecha el fin de 53 paradas sin medir nada. Cuesta cinco minutos.
- **En qué me apoyo.** El perfil del ATD (el balón se pierde en bloques, como en la DFL con solo los `D`
  tapados), el coste del `D` propio (0,08 a 0,11 en el harness) y que la capa 4 ya pasó su regla.
- **Cómo se mide.** No se puede en la DFL. Como la capa 4:
  - regla escrita y subida antes de que Manuel ejecute;
  - el modelo de Ana como juez de que el tramo es sobre todo `D`, con el punto medio entre el partido y
    el control;
  - el placebo desplazado 4, 6 y 8 minutos;
  - la entrega regenerada dentro de la banda (del 15 al 60 % de `D`, 250 paradas como mucho).
- **Añadiría un agregado:** un histograma grueso de la distancia entre el inicio de cada hueco y el
  inicio del `D` que sale del decodificador. Dice si la capa adelanta el `D` o si no cambia nada.
- **Riesgo.** Los huecos largos que caen en juego: el perfil no sabe cuántos son. La capa 2 es la más
  arriesgada. El orden de entrada sería 1, 3, 4 y 2.
- **Lo que no vale:** fijar ningún peso mirando la ventana pública.

**P3. Congelado sin sorpresas.**

- Fijar `numpy` y `pandas` con `==` (la excepción prevista de `CLAUDE.md`) y apuntar la versión de Python.
- Reproducir el CSV en un entorno limpio con esas versiones y, si se puede, con Python 3.11.
- Que `io.load_players` y `io.load_ball` den error si no han leído exactamente `n_frames` líneas válidas.
- Prohibir `D` en el frame del saque de cada parte (un frame en `allowed`), y recortar las ventanas de
  `dead_state` al tramo evaluado, con la misma medida de siempre (`validation/scripts/d_estado/medir.py`)
  para ver que no cambia nada en la DFL.
- Que `summary` imprima las rachas de menos de 12 y de 25 frames.
- Que el comando documentado escriba `<NOMBRE_EQUIPO>.csv`.

**P4. Una sola ronda de reentrenamiento de B5.**

- **Qué es.** Lo que no se puede probar con un añadido: cambiar lo que aprende el modelo.
- **Candidatos, antes de medir** (los tres con `validation/apuesta_b/entrenar.py`, sin tocar el resto):
  1. B5 sin las ventanas de 151 frames.
  2. B5 con peso 5 en los frames a ±2 s de un cambio de equipo.
  3. B5 con dos rasgos nuevos: el evento de toque a escala del anexo A.4, con signo (local menos
     visitante), en ventanas de 13 y de 51 frames.
- **En qué me apoyo, y por qué espero poco.** Los dos añadidos del anexo empatan. Un peso aprendido puede
  hacerlo algo mejor que mi escala fija, pero no hay motivo para esperar un salto.
- **Cómo se mide.** Harness con §5.8 frente a `main`, `--eventos` (que suban las recuperaciones de 70 sin
  bajar más de 5 puntos los duelos sin cambio) y los criterios 2 y 3 de B5 con `d_propio.py`.
- **Regla de parada:** una ronda. Si los tres empatan, se cierra la evidencia de equipo y se escribe en
  `docs/decisiones.md`.

**P5. Convención y nivel esperado, por escrito.**

- Apuntar en `docs/decisiones.md` las medidas del anexo A como descriptivas.
- Volver a preguntar D21, con la pregunta concreta: «¿podemos usar las notas publicadas del baseline y la
  tabla de retrasos para elegir entre dos convenciones de etiquetas de datos externos?».
- Si contestan que sí: añadir al harness una tercera convención intermedia (por ejemplo, `Ret-5` o
  `C0-8`, que ya están en `validation/experimento1/`), elegida por su huella, y dejar que vote.
- Si contestan que no, o no contestan: no se toca nada.
- En el documento técnico, dar el rango esperado (0,30–0,50) y de dónde sale.

**P6. Barrer las escalas del `D`.**

- `to_dead` y `from_dead` en 12, 25 y 50, y la escala de E2 en 0,5 y 1, con `d_propio.py` en sus dos
  modos (balón tapado en los `D` y balón a la vista). Entra lo que gane en los dos modos y con las dos
  convenciones.
- Los dos modos acotan lo que no se puede medir, igual que las dos condiciones que votan.

**P7. Fases del Smart Tagging como pista de equipo.**

- Un empujón pequeño (por debajo de 1 por frame) al equipo de la fase vigente, solo en los frames sin
  balón.
- Antes, un agregado del partido: en los frames de control claro (el mismo equipo a 1 m durante 1 s), con
  qué frecuencia coincide el equipo de la fase con el del más cercano, frente al mismo cálculo con las
  fases desplazadas. Si no llega al 80 % o no dobla al placebo, no entra.

---

## 5. Respuesta a las seis preguntas

**1. ¿Cómo recuperar posesiones cortas y recuperaciones con un balón suavizado 1 s?**

- **Las de menos de 1 s, no se puede** [inferencia]: dos toques a menos de 1 s se funden en uno.
- **Las demás, no he encontrado una forma barata, y lo he medido** [medido aquí].
  - El suavizado no impide ver los toques si se miden a su escala: 24–28 eventos por minuto, frente a 3,7
    con el detector de 4 frames [medido por el equipo].
  - Esos eventos son muy específicos: aparecen en el 37–43 % de los cambios reales del flag y en el
    1,2–1,5 % de los instantes estables. De los eventos del rival, el 67 % va seguido de un cambio real
    del flag, y el 40 % con control.
  - Pero no pasan mi regla de cobertura (50 %) y, sumados a B5, empatan.
  - La proximidad sola cubre más (56–63 %) con mucho más ruido (8–9 % en el placebo).
- **Por qué** [inferencia]: en un tercio de los cambios, el balón suavizado no llega a acercarse al
  jugador que lo tocó. Esa información no está en el ATD.
- **Lo que queda,** de más barato a más caro:
  - que el modelo aprenda el peso del evento (P4, candidato 3);
  - un modelo de secuencia que prediga el instante del cambio (P8);
  - un segundo sensor: el balón del vídeo o de la retransmisión.
- **Mi consejo:** una ronda de P4 y, si empata, dejarlo. Con una GT que parece más cerca de control, las
  posesiones muy cortas pesan menos de lo que sugiere la columna del flag.

**2. ¿Cómo fijar el inicio y el final de cada parada a menos de 1 s?**

- **Con los jugadores solos no se llega.** Lo publicado da unos 1,7 s de error [fuente, Lang et al., vía
  vuestro informe; no he podido releer el artículo], y E2 da el 35–40 %.
- **Hacen falta señales de instante,** y casi todas son del balón:
  - **inicio:** el balón visto fuera de las líneas y el primer frame de un hueco largo;
  - **fin:** la reaparición del balón y el inicio de la ventana `SET PIECES`, si la organización confirma
    cómo se construye.
- **El silbato** serviría sobre todo para las faltas (5 etiquetadas), los goles y el final de cada parte.
  No pasó su sondeo [sin verificar en el repo] y mete `ffmpeg` en la reproducción.
- **Nada de esto se valida en la DFL.** Se entra con regla y agregados (P2).
- **Objetivo realista:** del 35–40 % al 50–60 % de bordes a 1 s, no al 90 % [inferencia].

**3. ¿Cómo saber algo de la convención de la GT sin ajustar nada con la ventana pública? ¿Y qué entregar
si no se puede saber?**

- **Se puede saber algo, sin ajustar nada** [medido aquí, anexo A.6]:
  - la ventana pública es típica de las etiquetas de control (percentiles 29 y 30) y atípica de las del
    flag (por debajo del 5 % y por encima del 95 %);
  - la huella oficial de retrasos (0,654) queda entre el flag (0,552) y control (0,808), fuera del rango
    por partido de los dos;
  - el barrido de ventanas del baseline oficial tiene la forma del de control.
- **Conclusión** [inferencia]: la GT es más parecida a control que al flag, con más posesiones cortas que
  nuestro control. El flag tal cual es lo menos apoyado.
- **Con qué cautela:** todo es descriptivo y roza D21. Son 17 posesiones de una ventana y un solo partido
  de otra liga.
- **Qué entregar:** lo que hay. B5 con coste 25 gana con las dos convenciones, y esa es la propiedad que
  importa cuando no se sabe. No bajaría el coste para perseguir el flag ni lo subiría a 50: con control
  da +0,010 y con el flag −0,004.

**4. ¿Qué cambiarías del decodificador, sabiendo que con evidencia perfecta ya saca 0,97?**

- **Casi nada.**
  - Los costes empatan [medido por David].
  - El prior de reinicio no tiene señal [medido aquí].
  - Las duraciones mínimas y la poda dan la salida de `main` [medido por David].
- **Sí:** prohibir `D` en el frame del saque de cada parte (P3).
- **Solo si entra un detector de eventos:** que el coste de cambio dependa del contexto. En PathCRF,
  pasar de transiciones fijas a dependientes del contexto sube el F1 de eventos de 73,8 a 75,7 [fuente,
  leído]. Es poco, y mi prototipo dice que aquí daría menos.
- **No** a las duraciones explícitas (semi-Markov): con tres estados y una evidencia que ya integra 151
  frames, no hay parpadeo que quitar.

**5. ¿Merece la pena algo del vídeo o del audio antes del martes?**

- **No.**
  - El balón mide unos 4 píxeles en el táctico, y los detectores públicos se entrenaron con balones
    mayores [fuente, vía vuestro informe].
  - Sincronizar la retransmisión es trabajo de días y un error de 1 s cuesta más de lo que aporta.
  - El silbato: ver la pregunta 2.
  - Cualquiera de los tres complica la reproducción byte a byte.
- **Para la fase siguiente,** el orden sería: el balón de la retransmisión (ya detectado, solo falta
  sincronizar), el audio y, lo último, volver a detectar el balón.

**6. ¿Hay algo en la validación que te haga desconfiar del 0,498?**

- **Sí, y ahora está medido** (puntos 7 a 10):
  - lleva el `D` regalado; con el `D` propio es 0,416, y ese número aún es optimista;
  - el harness sobrestima el baseline entre +0,07 y +0,15;
  - los jugadores son perfectos;
  - la fase del suavizado está sin medir.
- **En qué sí confío:** en el orden entre versiones cuando la diferencia es grande y aguanta con las dos
  convenciones (B5 frente a N1, +0,07). El harness conserva el orden de los baselines con control.
- **En qué no:** en el nivel, ni en diferencias de 0,01.

---

## 6. Lo que no haría

- **El prior de reinicio** (lo propuse y lo retiro): 5,5–5,7 % de reinicios mal y un prior que no informa.
- **Más añadidos por reglas encima de B5** (anclas, radios, eventos con peso fijo): van cinco intentos
  sin ganar.
- **Seguir ajustando el coste de cambio, α o las duraciones mínimas:** ya empatan, y el signo depende de
  la convención.
- **Encender `ball.clean_v1`:** toca el 0,23 % de los frames, no arregla los 15 saltos y obliga a
  reentrenar B5 y a repetir dos medidas.
- **Copiar las fases del Smart Tagging como etiquetas,** o darles un peso comparable al coste de cambio.
- **PathCRF o Ball Radar:** piden 11 trayectorias continuas por equipo y, al cambiar de proveedor,
  PathCRF baja del 67 al 53 % y del 68 al 42 % de acierto de arista [fuente, leído].
- **Retocar más la degradación del harness** hasta que el nivel cuadre con el baseline oficial: sería
  ajustar contra la GT privada.
- **Elegir nada con la ventana pública, con el recuento a ojo o con la tabla de retrasos** mientras D21
  siga abierta.
- **Vídeo, retransmisión o audio** antes del martes.

---

## 7. Fuentes

**Leído entero**

- PathCRF (Kim et al., KDD 2026): https://arxiv.org/html/2602.12080 · código:
  https://github.com/hyunsungkim-ds/pathcrf. Posesión sin balón con un CRF y Viterbi. Cifras usadas: el
  F1 de eventos por variante (tabla 2) y la caída entre proveedores (tabla 6). Para construir sus
  etiquetas detecta toques con Ramer–Douglas–Peucker sobre la trayectoria del balón.
- Documentación oficial del reto y `evaluation/possession_metrics.py`.

**Leído en parte (resumen y método)**

- ELASTIC (Kim et al., 2025): https://arxiv.org/html/2508.09238 · código:
  https://github.com/hyunsungkim-ds/elastic. Frames candidatos a toque: mínimos de la distancia jugador–
  balón, máximos de la aceleración del balón (como norma de la derivada del vector velocidad, suavizada
  con Savitzky–Golay) y jugador a menos de 3 m. De ahí sale el radio de 3 m del anexo A.4.
- databallpy, posesión de equipo y de jugador:
  https://databallpy.readthedocs.io/en/latest/features/team_and_player_possession.html. Observa que
  TRACAB da la posesión a un equipo tras un pase fallado, y que su definición no coincide con la de
  eventos.

**Leído solo en el extracto de la búsqueda**

- SkillCorner opendata: https://github.com/SkillCorner/opendata. 10 partidos de la A-League 2024/25,
  tracking automático de retransmisión a 10 fps, licencia MIT, posesión por frame y jugadores
  extrapolados marcados. Su «player possession» exige control. Especificación:
  https://26560301.fs1.hubspotusercontent-eu1.net/hubfs/26560301/Guides/Dynamic%20Events/20250216%20-%20Dynamic%20Events%20CSV%20Specifications.pdf
- Vidal-Codina et al. (2022): https://link.springer.com/article/10.1007/s12283-022-00381-6. Zonas de
  posesión de 0,5 a 1 m según el proveedor, zona de duelo de 1 m y disparadores de balón parado.
- Bassek et al. (2025): https://www.nature.com/articles/s41597-025-04505-y.
- Lector de TRACAB de floodlight: https://floodlight.readthedocs.io/en/latest/modules/io/tracab.html.
- Validez de TRACAB Gen4 y Gen5: https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0230179.
- ASRF (Ishikawa et al.): https://arxiv.org/html/2007.06866v1.
- PFF/Gradient, Mundial 2022, en kloppy: https://kloppy.pysport.org/user-guide/loading-data/pff/. Trae el
  estado del balón y el equipo por frame; la licencia sigue sin aclarar.
- SoccerTrack v2: https://huggingface.co/datasets/atomscott/soccertrack-v2. Vídeo de campo completo, pero
  su balón está reconstruido a partir de los eventos, no medido.
- Detector de silbato (UPC, 2014):
  https://gtav.upc.edu/en/publications/papers/2014/the-importance-of-audio-descriptors-in-automatic-soccer-highlights-generation.
  Banda de 3,5 a 4,5 kHz y un filtro de entropía contra el ruido de la grada.
- CORAL (adaptación de dominio para modelos lineales): https://github.com/VisionLearningGroup/CORAL.
- Lang et al. (2022), solo el resumen de congreso:
  https://monarch.qucosa.de/landing-page/https%3A%2F%2Fmonarch.qucosa.de%2Fapi%2Fqucosa%253A80752%2Fmets%2F/.
  102 partidos, 92 % por instante y 81 % de precisión en interrupciones enteras. El artículo en PMC dio
  error 403.

**De oídas, sin releer**

- Semi-Markov frente a HMM (Fried et al.), Link y Hoernig, y Siegle y Lames: ya están en
  `docs/investigacion_metodos.md`.
- Que TRACAB cuenta los frames desde medianoche.
- Que las implementaciones vectoriales de `np.exp` pueden diferir en el último bit entre CPU.

---

## 8. Lo que no he podido comprobar

- **Nada del partido.** Todos los números del ATD, del Smart Tagging y de las entregas son los vuestros.
- **Los scripts del anexo no están en el repo.** Las reglas de lectura se fijaron en la conversación con
  Ismael antes de ejecutar cada uno, no en un commit. El historial de git no lo demuestra.
- **Los prototipos se midieron con una sola escala cada uno,** fijada antes. No probé otras, para no
  elegir con el resultado. Un peso distinto podría dar otra cosa.
- **No he medido los prototipos con `--eventos` ni con el `D` propio.**
- **El rango de 0,30 a 0,50** es una cuenta sobre dos supuestos, no una medida.
- **Las ganancias de la tabla de propuestas** son estimaciones.
- **Sin verificar:** la hora oficial del saque del partido, que la GT sea TRACAB, cómo suaviza Metrica el
  balón, cómo construye las ventanas de 35 s y si `possession/` corre con Python 3.8.
- **No he ejecutado** `prueba_pipeline.py` ni las demás pruebas del repo.
- **No he mirado** las PR abiertas, ni `evaluation/reports/`, ni las entregas.
- **El recuento a ojo de la PR 1** lo conozco solo por lo que dice `CLAUDE.md`.

---

## Anexo A. Medidas de esta revisión

**Común a todas.**

- **Datos:** los 7 partidos abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0), sobre la caché del
  experimento 0. La GT pública, solo en A.6. Nada del partido.
- **Código:** `main` en `05b6d98`, con el árbol de trabajo limpio antes y después.
- **Entorno:** el Python del equipo, con `MTAH_DATA_DIR` apuntando a una ruta que no existe.
- **Reglas de lectura:** escritas en la conversación antes de ejecutar cada script.
- **Comprobaciones del instrumento** [medido aquí]: `main` repite 0,498 / 0,512 / 0,728 / 0,748 con el `D`
  oráculo y 0,416 / 0,433 / 0,616 / 0,642 con el propio; el control ±50 repite 0,406 / 0,435 / 0,464 /
  0,494; la huella del flag repite 0,9905 / 0,9590 / 0,8594 / 0,5522 del experimento 0.

### A.1 Los cuatro baselines oficiales en el harness

- **Comando:** `python validation/harness/puntuar.py --versiones <fichero> --d propio`, y lo mismo con
  `--d oraculo`. Huella del fichero: `9498f55b3b04`.
- **El fichero:**

  ```json
  {
    "main (B5, coste 25)": {},
    "control: sin suavizar": {"tipo": "control", "ventana": 0},
    "control: voto de 25": {"tipo": "control", "ventana": 25},
    "control: voto de 125": {"tipo": "control", "ventana": 125}
  }
  ```

- **Regla, fijada antes:** el harness es creíble como predictor del orden si conserva
  ±50 > ±125 > ±25 > sin suavizar, y como predictor del nivel si el ±50 con `D` propio queda a ±0,05 de
  0,2433.
- **Resultado con el `D` propio** (`spellF1`, 7 partidos juntos):

  | etiquetas | balón | sin suavizar | ±25 | ±50 | ±125 | `main` |
  |---|---|---|---|---|---|---|
  | flag | como el ATD | 0,117 | 0,306 | 0,310 | 0,218 | 0,416 |
  | flag | sin bloques | 0,124 | 0,339 | 0,346 | 0,228 | 0,433 |
  | control | como el ATD | 0,069 | 0,287 | 0,353 | 0,308 | 0,616 |
  | control | sin bloques | 0,074 | 0,322 | 0,397 | 0,329 | 0,642 |
  | flag | limpio (sin voto) | 0,122 | 0,361 | 0,351 | 0,224 | 0,443 |
  | control | limpio (sin voto) | 0,068 | 0,348 | 0,407 | 0,326 | 0,659 |
  | flag | huecos y suavizado (sin voto) | 0,050 | 0,242 | 0,327 | 0,257 | 0,393 |
  | control | huecos y suavizado (sin voto) | 0,026 | 0,206 | 0,351 | 0,365 | 0,582 |
  | **partido completo (oficial)** | | **0,049** | **0,200** | **0,243** | **0,224** | – |

- **Con el `D` oráculo,** para comparar: flag 0,136 / 0,360 / 0,406 / 0,366 y 0,131 / 0,379 / 0,435 /
  0,384; control 0,085 / 0,342 / 0,464 / 0,518 y 0,076 / 0,353 / 0,494 / 0,552.
- **Lectura con la regla:** el nivel no es creíble (de +0,067 a +0,154); el orden se conserva con control
  y no con el flag. Con control y «sin bloques», ±125 y ±25 quedan a 0,007: el orden se cumple por poco.
- **Mirado después:** la condición sin voto «huecos y suavizado» con el flag es la más cercana en nivel
  (0,050 / 0,242 / 0,327 / 0,257). No la leo como que el balón del ATD se le parezca: el perfil dice que
  no. La leo como que el partido es más difícil que las condiciones que votan, por motivos que el harness
  no modela.

### A.2 Reinicios: equipo equivocado en el primer segundo

- **Qué mide.** Con el `D` oráculo, por cada reinicio (juego, `D`, juego): si la mayoría de los primeros
  25 frames tras el `D` lleva el equipo equivocado.
- **Regla, fijada antes:** el prior de reinicio merece construirse si pasa en el 5 % o más.
- **Resultado** (696 reinicios; es igual con las dos convenciones, porque tras un reinicio coinciden):

  | balón | equivocado en el primer segundo | el equipo real cambia tras la parada (flag / control) | el equipo real es distinto del que decía `main` antes de la parada |
  |---|---|---|---|
  | como el ATD | 40 (5,7 %) | 70,3 % / 50,7 % | 42,5 % |
  | sin bloques | 38 (5,5 %) | 70,3 % / 50,7 % | 42,5 % |

- **Lectura.** Pasa el 5 % por poco, pero la última columna tumba el prior que propuse: darle una
  bonificación «al equipo contrario al de antes» fallaría más de la mitad de las veces. El máximo que se
  puede ganar son unas 40 posesiones de 3.061.

### A.3 Prototipo: B5 más un ancla de retención

- **Candidato, fijado antes:** B5 más `candidates.retention_team` con sus valores de siempre (1,5 m, 12
  frames). En los frames del ancla se resta al equipo contrario la α de B5 de ese pliegue. Así no cambia
  el margen del ganador frente a `D`. Coste 25, `D` oráculo.
- **Resultado:**

  | balón | etiquetas | `main` | con ancla | diferencia [5–95 %] | gana en | posesiones predichas |
  |---|---|---|---|---|---|---|
  | como el ATD | flag | 0,498 | 0,504 | +0,006 [+0,002 a +0,010] | 5 de 7 | 1.661 → 1.773 |
  | como el ATD | control | 0,728 | 0,721 | −0,008 [−0,012 a −0,003] | 2 de 7 | 1.661 → 1.773 |
  | sin bloques | flag | 0,512 | 0,519 | +0,007 [+0,003 a +0,011] | 5 de 7 | 1.675 → 1.802 |
  | sin bloques | control | 0,748 | 0,740 | −0,008 [−0,013 a −0,003] | 3 de 7 | 1.675 → 1.802 |

- **Con §5.8:** empate.
- **El techo del ancla.** De las posesiones reales que `main` no encuentra, cuántas tienen dentro el
  ancla del equipo correcto:

  | duración | flag: como el ATD / sin bloques | control: como el ATD / sin bloques |
  |---|---|---|
  | 1–2 s | 26 % / 29 % | 51 % / 54 % |
  | 2–5 s | 37 % / 43 % | 50 % / 60 % |
  | 5–10 s | 72 % / 79 % | 58 % / 68 % |

  Y el ancla del equipo equivocado se enciende dentro de una posesión real entre 1,9 y 3,2 veces por
  minuto de juego. Es decir: el ancla falta en la mitad de lo que habría que recuperar y sobra a menudo.

### A.4 Detector de toques a la escala del suavizado

- **Detector, fijado antes.**
  - Cambio de velocidad en `t`: la norma de la diferencia entre la velocidad del balón del frame `t+12` al
    `t+25` y la del `t−25` al `t−12`. Son 13 frames cada una, separadas 25: lo que tarda un escalón en
    pasar por una media móvil de 25.
  - Evento: máximo local en ±12 frames, de 3 m/s o más (el umbral de toque del experimento 0).
  - Equipo del evento: el del jugador más cercano en `t`, si está a 3 m o menos (el radio de ELASTIC).
- **Regla, fijada antes:** hay señal aprovechable si, con el flag y en las dos condiciones que votan, hay
  un evento del equipo nuevo a ±12 frames en el 50 % o más de los cambios reales, y en el placebo (el
  mismo instante 5 s después, sin ningún cambio ni `D` a ±2 s) pasa como mucho un tercio de eso.
- **Eventos por minuto de juego:** 24,2 («como el ATD»), 27,6 («sin bloques») y 31,8 («limpio»). El
  detector de 4 frames del equipo ve 3,7 en el balón suavizado y 38,6 en el limpio [medido por el equipo].
- **Cambios reales con señal del equipo nuevo a ±12 frames, y placebo:**

  | balón | etiquetas | evento: cambios / placebo | proximidad a 1,5 m: cambios / placebo |
  |---|---|---|---|
  | como el ATD | flag | 37,4 % / 1,2 % | 55,8 % / 8,3 % |
  | como el ATD | control | 41,6 % / 2,6 % | 60,8 % / 13,1 % |
  | sin bloques | flag | 42,9 % / 1,5 % | 63,3 % / 9,3 % |
  | sin bloques | control | 48,0 % / 3,0 % | 69,9 % / 14,1 % |
  | limpio (sin voto) | flag | 34,3 % / 1,7 % | 94,3 % / 9,2 % |
  | limpio (sin voto) | control | 40,1 % / 2,2 % | 96,8 % / 14,2 % |

  Con ±25 frames, el evento sube a 43,9 % y 50,2 % con el flag.
- **De los eventos del rival, cuántos tienen un cambio real hacia ese equipo a ±25 frames:** el 67 % con
  el flag y el 40 % con control, en las dos condiciones que votan.
- **Lectura con la regla:** no cumple la cobertura (37–43 %, por debajo del 50 %). El placebo sí: es
  treinta veces menor.
- **Lo que enseña de paso:** la proximidad cae del 94 % al 56–63 % solo por suavizar el balón.

### A.5 Prototipo: B5 más el evento de toque

- **Candidato, fijado antes:** en los ±6 frames de cada evento de A.4 con un jugador a 3 m o menos, se
  resta la α del pliegue al equipo contrario al del evento. Trece frames por α = 4 suman unos dos costes
  de cambio: un evento solo no fuerza una ida y vuelta, pero decide un cambio de ida. Coste 25, `D`
  oráculo.
- **Resultado:**

  | balón | etiquetas | `main` | con evento | diferencia [5–95 %] | gana en | posesiones predichas |
  |---|---|---|---|---|---|---|
  | como el ATD | flag | 0,498 | 0,504 | +0,005 [+0,002 a +0,009] | 7 de 7 | 1.661 → 1.746 |
  | como el ATD | control | 0,728 | 0,720 | −0,008 [−0,012 a −0,004] | 1 de 7 | 1.661 → 1.746 |
  | sin bloques | flag | 0,512 | 0,518 | +0,006 [+0,002 a +0,010] | 5 de 7 | 1.675 → 1.773 |
  | sin bloques | control | 0,748 | 0,740 | −0,008 [−0,012 a −0,003] | 2 de 7 | 1.675 → 1.773 |

- **Con §5.8:** empate.
- **Posesiones reales encontradas** («como el ATD»; `main` → con evento): con el flag, 10 → 12 % (1–2 s),
  27 → 29 % (2–5 s) y 58 → 59 % (5–10 s); con control, 25 → 27 %, 53 → 56 % y 76 → 77 %.

### A.6 Huella de retrasos y ventanas de 5 minutos, por convención

- **Qué mide.** Con `validation/scripts/perfil_etiquetas.py` (la huella) sobre las etiquetas del harness:
  - la huella con los 7 partidos juntos y por partido, con las dos convenciones;
  - las mismas dos cifras de la ventana pública (posesiones por minuto vivo y huella a 25 frames) en
    todas las ventanas de 7.500 frames seguidos de la DFL, sin solaparse, desde el inicio de cada parte.
- **Regla, fijada antes** (descriptiva, bajo D21):
  - la huella oficial a 25 frames es «compatible» con una convención si cae dentro del mínimo–máximo por
    partido;
  - la ventana pública es «típica» de una convención si sus dos cifras caen entre el p10 y el p90 de las
    ventanas de la DFL.
- **La huella** (1 / 3 / 8 / 25 frames):

  | | 1 | 3 | 8 | 25 | a 25, por partido |
  |---|---|---|---|---|---|
  | DFL con el flag | 0,9905 | 0,9590 | 0,8594 | 0,5522 | 0,494–0,613 |
  | oficial | 1,0000 | 0,9818 | 0,8933 | 0,6539 | – |
  | DFL con control | 0,9983 | 0,9944 | 0,9661 | 0,8082 | 0,763–0,844 |

  No es compatible con ninguna de las dos.
- **Las ventanas** (129 por convención; la pública: 17 posesiones, 4,02 minutos vivos, 4,23 por minuto y
  huella de 0,7765):

  | | p10 | p25 | p50 | p75 | p90 | ventanas por debajo de la pública |
  |---|---|---|---|---|---|---|
  | flag, posesiones por minuto vivo | 5,23 | 6,83 | 8,91 | 10,81 | 13,44 | 5 % |
  | flag, huella a 25 frames | 0,43 | 0,52 | 0,57 | 0,64 | 0,73 | 95 % |
  | control, posesiones por minuto vivo | 3,18 | 3,90 | 4,91 | 6,20 | 7,44 | 29 % |
  | control, huella a 25 frames | 0,69 | 0,76 | 0,83 | 0,88 | 0,93 | 30 % |

  Típica de control; atípica del flag.
- **Solo la primera ventana de cada partido** (n = 7): con el flag, de 5,67 a 16,84 posesiones por minuto
  vivo (la pública queda por debajo de las siete); con control, de 3,18 a 12,47, con mediana de 4,52.
- **Límites.** Es otra liga. La ventana pública son 17 posesiones. Las ventanas de un mismo partido no son
  independientes. Y compara con cifras que salen de la GT privada: no decide nada.
