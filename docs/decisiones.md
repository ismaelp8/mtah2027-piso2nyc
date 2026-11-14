# Registro de decisiones

Aquí va cada decisión de método: qué se probó, con qué se midió, qué se eligió y por qué.
Es la materia prima del documento técnico, así que conviene escribirlo el mismo día y no al final.

Reglas para rellenarlo:

- Los números salen de la **validación externa** con partidos abiertos de otros equipos, o son
  **agregados** del partido (spellF1 y macroF1 de la ventana pública, recuentos). Nunca valores por
  frame.
  - Dataset principal propuesto: el de la Bundesliga (Bassek et al., 2025), pendiente del
    «experimento 0» de `docs/investigacion_metodos.md` §5.
  - Dataset secundario: Metrica sample-data.

  Cada entrada dice con cuál de los dos se midió.
- La ventana pública de 5 minutos sirve para comprobar que el pipeline es correcto, **no para elegir
  entre versiones**. Si una decisión se apoya en ella, está mal tomada.
- Si una diferencia de spellF1 es menor de ~0,04, es ruido: se apunta como empate.

## Plantilla

```
### AAAA-MM-DD · <módulo> · <título corto>
Quién:
Qué se probó:
Cómo se midió (dataset, nº de partidos/posesiones, métrica):
Resultado:
Decisión y por qué:
Descartado:
```

---

### 2026-11-10 · infraestructura · repo y datos

Quién: Ismael
Qué se hizo:
- Repo privado `ismaelp8/mtah2027-piso2nyc`, copia del oficial (no fork, para poder tenerlo privado).
  `upstream` apunta a `metrica-sports/more-than-a-hack-2027` para recibir correcciones.
- Los datos viven fuera del repo y fuera de OneDrive, en `MTAH_DATA_DIR`. El `.gitignore` oficial no se
  toca.
- `.claude/settings.json` intenta bloquear que Claude lea las rutas de datos. Es una red de seguridad,
  no la protección principal. Se probó el 11/11 (ver la entrada siguiente).

Decisión y por qué: el repo será público el 17 y el historial de git es permanente. Si un dato del
partido entra en un commit, aunque se borre después, se queda en el historial.

### 2026-11-11 · infraestructura · normas del repo y configuración de Claude

Quién: Ismael

Qué se hizo:
- **`CLAUDE.md` compartido.** Era un brief local de Ismael y ahora es el brief común que carga el Claude
  de todo el equipo: regla de datos, reto, puntuación, mapa, convenciones, flujo de git, estrategia y
  calendario. Lo personal de cada uno va en un `CLAUDE.local.md` excluido de git.
- **`CONTRIBUTING.md`** con las normas:
  - nunca commit a `main`;
  - una rama `tipo/descripcion` por tarea;
  - commits en una frase en español, con la autoría siempre de quien sube y sin `Co-Authored-By`;
  - PR con plantilla, revisada por `ismaelp8` o `ortegafer`, con una aprobación y merge con squash
    (`sync/*` con merge commit);
  - qué no entra en git;
  - notebooks sin outputs.
- **`.claude/`:**
  - `settings.json` con deny de los datos, allow de comandos seguros y la atribución a Claude
    desactivada (`attribution`);
  - siete skills: `/empezar`, `/subir`, `/actualizar`, `/revisar-pr`, `/sincronizar-upstream`,
    `/evaluar` y `/decision`;
  - el agente `revisor`;
  - un script que cuenta y borra los outputs de los notebooks sin enseñar su contenido.

Cómo se comprobó:
- **Las reglas deny** se probaron con ficheros de prueba inofensivos, con un fichero de control al lado.
  Nunca se tocaron los datos reales. Los ficheros de prueba fueron:
  - `BAR-ATH_tactical_dummy.txt`, `BAR-ATH_broadcast_dummy.txt` y `dummy.mp4`, fuera del repo;
  - una carpeta falsa `mtah2027-data/cache/`;
  - rutas inexistentes en `data/tactical/` y `data/broadcast/`;
  - los baselines públicos de `evaluation/results/` y sus informes.

  Resultados:
  - **Quedan bloqueados:** Read, Grep, Glob, `cat`/`head` y `Get-Content` sobre todos ellos.
  - **Se siguen leyendo:** la GT pública y los ficheros de control.
  - **Siguen funcionando:** `validate_submission.py` y `run_evaluation.py`. Reproducen
    `smooth50` = macroF1 0,6207 / spellF1 0,3256 en la ventana pública.
  - **No quedan bloqueados:** `python -c "open(...)"` ni `grep -r` sobre una carpeta.
  - **Corrección:** `Read(**/*.mp4)` no cubría nada fuera del repo. Se cambió por `Read(//**/*.mp4)`.
  - **Límite conocido:** todo lo anterior se vio en una sesión de Claude abierta directamente en la
    carpeta del repo, y se repitió allí con ficheros nuevos con el mismo resultado. En otra sesión,
    abierta en otra carpeta y movida después al repo, Read, Grep y `cat` leyeron los ficheros de
    prueba. La causa probable es que esa sesión no carga el `.claude/settings.json` del repo; no está
    confirmada.
- **El script de notebooks** se probó con notebooks falsos: detecta los outputs, los limpia y deja el
  notebook válido para nbformat.
- **GitHub:**
  - la protección de ramas y los rulesets devuelven 403 en GitHub Free con repo privado, así que
    CODEOWNERS tampoco haría nada;
  - los reviewers se piden con `gh pr create --reviewer`.

Decisión y por qué:
- **Las normas son una convención** que aplican el equipo y las skills, porque GitHub no las puede
  imponer en este plan.
- **Squash** para que cada PR sea un commit en `main`. Las `sync/*` van con merge commit para no perder
  la historia de `upstream`.
- **Los dos commits iniciales van directos a `main`** por decisión de Ismael: el del informe de métodos
  con `validation/` y este de normas y configuración. A partir de ahí, todo entra por rama y PR.

Descartado:
- **Un hook de Claude** que bloqueara los comandos de shell que nombren los datos. Cerraría el hueco de
  `python -c` y `grep -r`, pero se decide no montarlo de momento: la protección es la regla nº 1.
- **Un aviso del estado del repo al abrir la sesión.**
- **CODEOWNERS:** no funciona en este plan.

### 2026-11-11 · validación · la `X` y el dataset de la validación externa

Quién: Ismael, a partir de `docs/investigacion_metodos.md`

Qué se decidió:
- **La `X` solo se usa fuera de los tramos evaluados.** Dentro, también en las oclusiones largas, se
  escribe siempre una etiqueta.
- **El dataset principal propuesto para la validación externa es el de la Bundesliga** (Bassek et al.,
  2025: 7 partidos, CC-BY 4.0). Queda pendiente del experimento 0. Metrica sample-data pasa a ser el
  dataset secundario.

Cómo se midió:
- **La `X`:** no es una medición, es una propiedad de la métrica (`EVALUATION.md` y
  `evaluation/possession_metrics.py`). El scorer sustituye cada `X` por la última etiqueta de esa parte
  antes de calcular spellF1, y en macroF1 la cuenta como fallo.
- **El dataset:** todavía no se ha medido nada. El experimento 0 de `validation/PASOS.md` comprueba con
  agregados si las etiquetas de la Bundesliga se comportan como pide la definición de posesión de
  `CHALLENGE.md`.

Decisión y por qué:
- **La `X`:** escribir la etiqueta anterior da el mismo spellF1 que una `X` y un macroF1 igual o mejor.
  La `X` nunca gana en un frame evaluado.
- **El dataset:** el de la Bundesliga trae en cada frame qué equipo posee el balón y si está vivo, el
  mismo tipo de etiqueta que la GT del reto. Metrica sample-data no trae posesión por frame: hay que
  derivarla de los eventos, que es otra convención.
- **`CLAUDE.md` y `docs/GUIA_EQUIPO.md` decían otra cosa** (`X` en las oclusiones largas y validar con
  Metrica) porque se escribieron antes del informe. Ismael decidió seguir el criterio del informe, y los
  dos documentos están alineados con él desde hoy.

Abierto:
- **El experimento 0.** Hasta que se haga, la Bundesliga es una propuesta y no una decisión cerrada.
- **La consulta D21** (`validation/PASOS.md`): si la tabla de retrasos de `EVALUATION.md` se puede usar
  para algo más que para leer la métrica. Ismael decidió preguntárselo a la organización por email.
  Hasta que conteste no se decide nada con esa tabla: ni parámetros, ni podas, ni la elección de
  dataset.

Descartado:
- **`X` en las oclusiones largas dentro de una posesión,** que era la política anterior.
- **Metrica sample-data como dataset principal.**

### 2026-11-11 · infraestructura · Ismael sube directo a `main`

Quién: Ismael

Qué cambia:
- **Ismael (`ismaelp8`) puede hacer commit y push directo a `main`,** sin rama ni PR.
- **Para el resto no cambia nada:** rama por tarea y PR revisada por Ismael o David.
- Sustituye a la norma «nunca commit a `main`» de la entrada de normas de este mismo día.

Decisión y por qué:
- Ismael es quien más cambios hace y quien mejor conoce git. Pasar cada cambio suyo por una PR solo
  añade espera.
- Sus commits pasan las mismas comprobaciones que una PR: datos, notebooks, ficheros oficiales y
  autoría. Nunca con `--force`.
- Si quiere que David le revise algo, usa rama y PR.
- Está en `CONTRIBUTING.md` §5, en `CLAUDE.md` y en las skills `/subir`, `/empezar`, `/actualizar` y
  `/decision`.

### 2026-11-12 · validación · experimento 0: `D` de la DFL vale; el equipo se deriva con el control del reto

Quién: Ismael

Qué se probó: si el flag por frame de la Bundesliga (DFL) se comporta como pide `CHALLENGE.md`.
Experimento 0, pasos 1 y 2 de `validation/PASOS.md`, con los criterios fijados antes de medir.

Cómo se midió:
- **Dataset:** la Bundesliga (Bassek et al., 2025): 7 partidos, 1.002.644 frames, 2.351 cambios H↔A
  con el balón vivo y 710 paradas.
- **Medidas:** solo tracking y eventos, con placebos y 21 variaciones de cada parámetro.
- **Réplica:** la sesión orquestadora repitió 2g con detectores propios.
- **Detalle:** en `validation/resultados/2026-11-11_experimento0.md`. No se usó la ventana pública ni
  la tabla de retrasos (D21).

Resultado:
- **`D` cumple en los 7 partidos.**
  - El 99,4–100 % de los saques de banda, de puerta y córners tiene un final de `D` a ±5 s. En el
    placebo, el 14,6 %.
  - Con el balón fuera 1 s o más y el flag activo solo hay 2 episodios en 7 partidos.
  - El `D` empieza 3–4 frames después de que el balón cruce la línea y acaba en el golpeo del reinicio
    o pocos frames después.
- **El balón está congelado durante los `D`:** el 100 % de esos frames repite la posición anterior, y
  al reanudar salta una mediana de 6,2 m. La posición del balón delata la etiqueta.
- **El equipo no cumple: el flag sigue al primer toque del rival.**
  - Con un toque sin control del rival entre dos controles del mismo equipo, el flag pasa al rival en
    el 72–85 % de los casos según el detector. En el placebo, el 10–14 %.
  - No cumple en ninguno de los 7 partidos y aguanta todas las variaciones.
  - El cambio cae en el mismo frame del toque (mediana 0).

Decisión y por qué:
- **`D` de la DFL: vale tal cual,** tapando el balón en los frames `D` y en las ventanas que tocan sus
  bordes (entrada y salida). Si no, el balón congelado y el salto al reanudar dan la respuesta.
- **H/A de la DFL: no vale tal cual.** Las etiquetas de equipo se derivan con el criterio de control
  del reto: la posesión cambia cuando el rival controla el balón, no cuando lo toca.
- **Por qué:** es lo que dice `CHALLENGE.md`: un toque sin control, un desvío que no intercepta el pase
  o un duelo aéreo ganado sin control posterior no cambian la posesión. Ismael lo decidió el 12/11.

Abierto:
- **Qué definición de control se usa para corregir las etiquetas de la DFL.** Hay varias metodologías
  en el informe. La propuesta del siguiente paso está al final del fichero de resultados.
- **Riesgo apuntado:** que la GT del reto siga, como la DFL, al primer toque. `CHALLENGE.md` dice que
  su tracking nombra equipo con el balón muerto ("whoever will restart, or touched it last"; líneas
  42–45), y eso va en esa dirección. Las líneas 76–80 van en la contraria. Si Ismael lo pide, se puede
  comprobar de forma cualitativa con la ventana pública (una persona, sí o no) o preguntando a la
  organización.

Descartado:
- **Usar el flag de posesión de la DFL tal cual como etiqueta de equipo.**

### 2026-11-12 · `D` · versión 1 del detector: el tramo antes del saque; con la regla probada, el balón del ATD no fecha reinicios

Quién: Manuel

Qué se probó:
- Fechar el saque inicial de cada parte y cada reanudación de los `SET PIECES` del Smart Tagging con el
  balón del ATD: el balón visto quieto (5 frames dentro de 0,5 m) que empieza a moverse, buscándolo
  desde 10 s antes de la etiqueta. En los saques iniciales, además, quieto a menos de 2 m del centro.
- Antes de eso, medir si el ATD ve el balón fuera del campo, en los reinicios y quieto, y si x = 0,5 es
  la mitad del campo.

Cómo se midió: agregados del partido entero (ATD y Smart Tagging), con
`validation/partido/diagnostico_balon_muerto.py` y `validation/partido/diagnostico_coordenadas.py`,
ejecutados por Manuel en local. Salida completa y lectura en
`validation/resultados/2026-11-12_balon_muerto_atd.md`. La GT pública solo se usa para comprobar que la
máscara no la contradice (`validation/scripts/comprobar_balon_muerto.py`), no para elegir nada.

Resultado (cada punto con su etiqueta, como en el fichero de resultados):
- **[medido]** De los frames con balón, solo el 4,2 % lo tiene fuera del campo. Antes de un córner el
  balón no se ve fuera en ninguno de 12, pero solo se ve en 2.
- **[inferencia]** Cuando el balón sale, el ATD casi siempre lo pierde.
- **[medido]** En los saques iniciales no se encuentra el golpeo con el balón quieto en el centro: 0 de
  6. En 4 de los 6 se ve balón, pero menos de 5 frames a menos de 2 m del centro.
- **[sin verificar]** Por qué en esos 4 saques: el ATD solo ve el balón después del golpeo, queda tapado,
  o sigue otro objeto.
- **[medido]** En los 6 saques iniciales los equipos quedan a lados opuestos de x = 0,5.
- **[sin verificar]** Que x = 0,5 sea exactamente la línea de medio campo.
- **[medido]** La "reanudación" sale en los 53 saques de banda, córners, saques de puerta y faltas. En 51
  el balón llevaba quieto menos de 1 s, en 2 entre 1 y 3 s, y en ninguno 3 s o más. La regla cubriría
  466 frames (0,3 %).
- **[inferencia]** No son los reinicios reales.
- **[medido]** El ATD ve el balón quieto 3 s o más en 17 tramos de los frames evaluados (radio 0,5 m),
  aunque se toleren huecos sin balón de hasta 1 s.
- **[inferencia]** No congela el balón en el tiempo muerto, al revés que la DFL.
- **[medido]** La columna de velocidad del balón no se comporta como m/s: mediana de 1,1 frente a 5,1 m/s
  calculados con las posiciones.

Decisión y por qué:
- **Versión 1: solo el tramo previo al saque de cada parte.** Son 2.934 frames en la 2ª parte y 0 en la
  1ª, con los frames de saque que publica `FAQ.md` (`KICKOFF_VIDEO_FRAMES` de
  `starter/load_smart_tagging.py`). Con la regla probada no se encontró el golpeo en ninguno de los 6
  saques iniciales.
- **Las anclas de `games.py` difieren de esos frames en ±1, en sentidos opuestos en cada parte.**
  `games.py` las describe como el frame en que se golpea el balón, así que puede ser una diferencia de
  convención. Se usan los frames del FAQ porque coinciden con los 2.934 frames `D` que publica la
  organización. Con las anclas saldrían 2.933 en la 2ª parte y 1 en la 1ª, justo en el primer frame
  evaluado, que el FAQ y la GT pública dan como balón en juego.
- **Con las dos reglas probadas, el balón del ATD no da el resto del `D`** [medido]. Son "balón fuera del
  campo → `D`" y "balón quieto que empieza a moverse".
- **Otras reglas con el balón no se han probado**: por ejemplo, combinarlo con la posición en el campo,
  con el tiempo que lleva sin verse o con los jugadores.
- **La vía que parece más prometedora** [inferencia] es el enfoque con jugadores (B3 o B4 de
  `docs/investigacion_metodos.md` §2.2), entrenado y validado con la Bundesliga degradada.

Abierto:
- Que Ismael confirme que usar los frames publicados que guarda `starter/` cumple la regla de
  "ninguna constante de frames salvo las de `games.py`".
- **Pregunta para `ball.py`:** si el ATD sigue a veces objetos que no son el balón de juego. El fichero de
  resultados dice qué agregado lo separaría.
- Que Ismael diga si los reinicios por tipo (5 casos o más por tipo) cumplen la regla de agregados, o
  si se juntan todos.

Descartado:
- **La variante de B1 y B2 de §2.2 que fecha los reinicios con el balón** ("balón quieto que empieza a
  moverse"). Lo que detecta apunta a no ser los reinicios [inferencia]. B2 en sí, los `SET PIECES` como
  fin del `D`, sigue abierto.
- **"Balón fuera del campo → `D`" como regla principal:** cubriría muy poco, porque el ATD casi nunca ve
  el balón fuera [inferencia, a partir de lo medido].
- **Las otras dos vías de B5 para fechar el saque:**
  - la etiqueta `Kick Off (Start)`: es una ventana de unos 5 s, no un instante;
  - "todos los jugadores en su campo": dice que aún no se ha sacado, pero no en qué frame se saca.

  Las etiquetas de saque contienen los frames del FAQ, así que son coherentes con ellos. Que esos frames
  sean exactos es lo que dice la organización [fuente].

### 2026-11-13 · `D` · revisión del detector v1: el `D` suma por sus fronteras; dos descartes vuelven a abrirse

Quién: Ana (revisión pedida a Claude; lo que se reabre lo confirman Manuel e Ismael)

Qué se probó:
- Cuánto cuesta en `spellF1` cada error propio de un detector de `D`: paradas no detectadas, bordes tarde
  o pronto, `D` que parpadea dentro de una parada, `D` sin fin, equipo equivocado al reanudar.
- Si los jugadores solos (sin balón) sirven para detectar `D` y con qué precisión en las fronteras: AUC
  por rasgo, umbral con histéresis y regresión logística, con el umbral elegido en una parte y evaluado
  en la otra.
- `possession/io.py` con un ATD sintético del mismo tamaño.

Cómo se midió (dataset, nº de partidos/posesiones, métrica): scorer oficial sobre la GT sintética del repo
(6 partes, 142 paradas por 332 posesiones), la GT pública con el equipo perfecto (17 posesiones, 4
paradas; solo lectura de la métrica) y el partido abierto `J03WMX` de la DFL (103 paradas, 511
posesiones) con el equipo perfecto. Detalle y scripts en
`validation/resultados/2026-11-13_revision_balon_muerto.md`.

Resultado:
- **[medido]** En la DFL, con equipo perfecto: sin `D` 0,82; todas las paradas con los dos bordes 2 s tarde
  0,83; la mitad de las paradas con bordes exactos 0,92; todas con ruido de ±1 s 0,90.
- **[medido]** En la sintética: `D` que parpadea cada 4 s 0,62; equipo equivocado 0,5 s tras cada reinicio
  0,80; fin del `D` 1 s tarde 0,92; inicio 1 s tarde 0,95.
- **[medido]** Jugadores solos en la DFL: AUC 0,93–0,97 por frame; la logística detecta 43 de 62 y 35 de
  41 paradas, pero el inicio llega 1 s tarde de mediana (p90 de 4–7 s) y el `spellF1` no mejora frente a
  no poner `D` (0,775 frente a 0,781; 0,864 frente a 0,852).
- **[medido]** `io.py` rompía con un balón o slot escrito como un solo `NaN`; corregido en esta rama.

Decisión y por qué:
- **El criterio de aceptación de cualquier detector de `D`, medido en la DFL antes de integrarlo:**
  |latencia| ≤ 25 frames en el inicio y en el fin en al menos el 70 % de las paradas, sesgo mediano dentro
  de ±12 frames, `D` espurios ≤ 0,3 por minuto de juego y ninguna racha de `D` ni de vivo por debajo de la
  duración mínima. Por debajo de eso, el detector no mejora el ranking [inferencia a partir de lo medido].
- **El tiempo del `D` sale del balón y del Smart Tagging; el estado, de los jugadores.** El modelo de estado
  se entrena con los 7 partidos de la DFL con rasgos de equipo sin identidad, sin esperar a la degradación.
- **Se reabren dos descartes de la entrada del 12/11**, que quedan como «sin evaluar» hasta que Manuel
  ejecute `validation/partido/agregados_balon_reinicios.py`:
  - fechar los reinicios con el balón («quieto que empieza a moverse»): sus 53 detecciones con menos de
    1 s de balón quieto son lo esperable si el ATD solo recupera el balón cuando se mueve; hay que
    cruzarlas con el fin de la ventana `SET PIECES` y con la subida de velocidad de los jugadores;
  - «balón fuera del campo» como disparo del inicio del `D`: cubre pocos frames, pero son 2–3 s de balón
    visible por cada salida, y falta medir el balón que desaparece saliendo.
- Los agregados por tipo de reinicio se imprimen con 5 casos o más por tipo (los saques iniciales siempre
  juntos), el criterio que Manuel dejó preguntado a Ismael; si Ismael prefiere juntarlos, es una constante
  en `validation/partido/comun.py`.

Descartado:
- **Suavizar el `D` con un voto por mayoría o usar la ausencia del balón como `D`:** introducen justo el
  retraso o el parpadeo que anulan el `D` en `spellF1` [medido en la sintética y la DFL].
- **Arrastrar el equipo anterior a través de una parada:** en `J03WMX` el equipo cambia en el 90 % de las
  paradas [medido].

### 2026-11-14 · infraestructura · un solo pipeline con una pieza por persona; el harness de la DFL decide qué entra

Quién: Ismael

Qué se probó: no se midió nada nuevo; es una decisión de organización. Se valoraron tres formas de
repartir el trabajo de los dos días y medio que quedan:
- dos equipos, cada uno con un pipeline completo (A, por reglas, y B, con evidencia aprendida), para
  comparar por apartados cuál saca mejores resultados;
- ir apartado por apartado, empezando por el preprocessing y probando varias variantes de cada uno;
- un solo pipeline con piezas intercambiables, una persona por pieza y todas a la vez.

Cómo se midió (dataset, nº de partidos/posesiones, métrica): sin medida nueva. Se apoya en lo ya
documentado:
- `spellF1` no puntúa un apartado suelto: necesita el pipeline completo con todo fijo menos la pieza que
  se compara (`docs/investigacion_metodos.md` §5.1);
- los pipelines A y B solo se diferencian en la evidencia (§4);
- la limpieza del balón no está en el ranking de piezas (§3.1) y la degradación de la DFL es el eslabón
  más débil de la validación externa (§5.5);
- el experimento 2 (14/11) apunta a que el balón del ATD viene suavizado [inferencia, con 4 minutos de
  ventana], y la degradación todavía no imita ese balón.

Resultado:
- **[medido]** Lo único ejecutado es `validation/scripts/prueba_pipeline.py`, con un partido inventado:
  29 comprobaciones en verde. Entre ellas, 158.857 frames evaluados con etiqueta y `X` en el resto, el
  tramo antes del saque de la 2ª parte como `D`, el decodificador igual que la búsqueda exhaustiva en 200
  casos, el CSV regenerado byte a byte, y que una evidencia con NaN o dos piezas que se contradicen dan
  error en vez de pasar en silencio.
- **[medido]** Primera medida del harness (`validation/resultados/2026-11-14_harness_dfl.md`): los 7
  partidos de la DFL, con el `D` copiado de las etiquetas y la evidencia del jugador más cercano. Con las
  etiquetas corregidas por control (1.736 posesiones), el Viterbi con coste 25 gana al voto del baseline
  en las tres condiciones del balón (+0,106, +0,115 y +0,126) y en los 7 partidos. Con el flag tal cual
  (3.061 posesiones), empata o pierde por poco (+0,020, −0,028 y −0,022). Con la regla de §5.8 no gana
  ninguna versión, porque la diferencia no se mantiene con las dos convenciones.
- **[inferencia]** La ventaja con las etiquetas de control está inflada por construcción: esas etiquetas
  salen de una regla de proximidad (el más cercano a 1 m durante 12 frames, o dos toques) y lo que se
  mide es proximidad con un coste por cambiar. El flag es el mismo tipo de etiqueta que la GT del reto.
- Todavía no hay ningún número del pipeline en el partido.

Decisión y por qué:
- **Un solo pipeline con cinco piezas y una persona por pieza,** todas a la vez. El reparto y lo que hace
  cada uno están en `docs/PLAN_ENTREGA.md`.
- **Una interfaz común** (`possession/tracking.py`): las piezas reciben un `Tracking` y las de evidencia
  devuelven `(score, allowed)` de forma (n, 3); el decodificador consume la suma. Son funciones puras
  sobre arrays, para que el código que valida el harness sea el mismo que se entrega.
- **El pipeline corre de punta a punta desde hoy** con la versión más simple de cada pieza: jugador más
  cercano, `D` solo antes del saque de la 2ª parte y un Viterbi con coste de cambio.
- **Qué versión entra lo decide el harness de la DFL,** con la regla de §5.8, las dos convenciones de
  etiquetas y tres condiciones del tracking. La ventana pública se mira siempre y nunca elige.
- **Se cambia el orden de «Lo siguiente» del 14/11 por la mañana,** que dejaba el modelo temporal para el
  final. La medida del balón del ATD sigue siendo lo primero, pero a la vez que el pipeline.
- **Corte el lunes 16 a las 14:00:** lo que no haya ganado en el harness no entra.
- **Por qué:** el cuello de botella no es escribir código, sino las ejecuciones sobre el partido, que solo
  puede hacer una persona, y la integración. Con piezas en paralelo detrás de una interfaz, cada mejora
  entra sola y siempre hay una entrega válida.

Abierto:
- **La convención de la GT del reto.** La primera medida del harness dice que decide qué decodificador
  conviene. Sigue sin medir.
- **La medida del balón del ATD en todo el partido.** Hasta tenerla, no se elige entre evidencias de
  equipo ni se da por buena la apuesta B.
- **Los valores por defecto del esqueleto están sin ajustar:** los tres costes del decodificador a 25 y
  la puntuación 1 del jugador más cercano. Se fijan en la DFL.

Descartado:
- **Dos pipelines completos:** construirían dos veces el lector, la limpieza, el `D` y el decodificador,
  que son comunes y son lo que decide la nota, y doblarían las ejecuciones sobre el partido. De la idea
  queda A contra B como dos candidatos de una sola pieza, la evidencia, con corte para B.
- **Apartado por apartado, en orden:** el primer número de punta a punta llegaría el lunes, que es cuando
  hay que congelar.
- **Comparar variantes de limpieza del balón:** su árbitro sería una degradación que aún no imita al
  balón del ATD. Se fija la de §2.1 (filtro de validez e interpolar huecos cortos).

### 2026-11-14 · validación · el harness tapa el balón «como el ATD» y decide frente a `main`

Quién: Ismael (las dos decisiones), con el perfil del ATD delante; Claude midió.

Qué se probó:
- **El perfil del balón del ATD en todo el partido,** con la regla de lectura fijada antes de medir
  (`validation/perfil_atd/BITACORA.md`). Ismael ejecutó el script del partido y pegó solo agregados.
- **Dos formas de tapar el balón de la DFL:**
  - la de antes: el 41 % del juego, con la mitad de las disputas y bloques de 1 s;
  - la ley de huecos del ATD: microcortes de hasta 0,5 s y bloques de 5 a 15 s.

Cómo se midió (dataset, nº de partidos/posesiones, métrica): el ATD del partido (agregados) frente a los 7
partidos de la Bundesliga (Bassek et al., 2025) degradados. Huecos por duración, visibilidad, disputas,
toques y controles por minuto, y proximidad. Después, la tabla del harness (`spellF1` oficial con las
dos convenciones, 3.061 y 1.736 posesiones) y los eventos humanos de la DFL.

Resultado:
- **Con la forma de antes no queda ningún `DISPUTAS`** [medido]. El ATD casi no tiene huecos cortos y se
  parece a la DFL con solo los `D` tapados: 111 huecos de 5 s o más por 90 minutos frente a 88, y 59,3 %
  de balón visible frente a 54,5 % [medido]. La mayor parte de su 41 % sin balón sería balón muerto
  [inferencia]. La condición de antes era mucho más dura que el ATD.
- **Con la ley de huecos del ATD queda `DISPUTAS` 0, con suavizado de 25 frames** y el 11,3 % del juego en
  bloques de 5 a 15 s [medido].
- **Con el flag, el Viterbi de `main` gana al baseline** por +0,022 en 7 de 7 partidos con la condición
  nueva, y perdía por −0,022 con la de antes [medido]. No llega al +0,03 de §5.8: es empate.

Decisión y por qué:
- **Votan «como el ATD» y «como el ATD, sin bloques».** Acotan lo que no se puede medir sin etiquetas: si
  los huecos largos del ATD caen en juego o en paradas. «limpio» y la de antes se puntúan sin voto. Así
  el harness juzga con un balón como el que tendrá el pipeline en el partido.
- **Para sustituir a lo que hay en `main`, un candidato tiene que ganar al control y a `main`** con la
  regla de §5.8. Si empata con `main`, se queda lo de `main`. Es la regla del empate aplicada a lo que ya
  hay.
- **Los eventos humanos de la DFL (`--eventos`) son descriptivos.** No entran en §5.8. Si vetan a un
  candidato, lo decide Ismael caso a caso.

Descartado:
- **Los dos candidatos fijados antes de medir tal cual** (la ley de huecos aplicada al 41 %, `dilatar` y
  `aire`): seguían tapando el juego que el ATD sí ve. Se usó la ley de huecos del ATD con `OBJETIVO`
  calibrado por la regla.
- **Tomar `OBJETIVO` de las severidades baja y media:** con bloques de 5 a 15 s no lo identifican
  (bitácora §9.2).

### 2026-11-14 · candidatos · apuesta B: evidencia de equipo aprendida (candidatos, antes de medir)

Quién: Ismael (las tres decisiones de abajo, «Sí a las tres»); Claude escribe los candidatos y mide.

Qué se prueba: la apuesta B del plan (`docs/PLAN_ENTREGA.md` §3, «Ismael»; `docs/investigacion_metodos.md`
§4.2). Es una evidencia de equipo aprendida en la DFL que sustituye a N1 en la pieza `candidates`. El resto
del pipeline no cambia: el decodificador va con los costes de `main` (25) y el `D` sale del oráculo.

Decisiones de Ismael (14/11, antes de escribir código):
1. **La función va en un módulo nuevo, `possession/aprendida.py`,** y el harness acepta para la pieza
   `candidates` una función de ese módulo. Así no se toca `candidates.py`, que es de Antonio.
2. **El harness deja un partido fuera.** Cuando la versión lo pide en el JSON, el harness pasa a la pieza
   el partido que puntúa. El módulo guarda 7 juegos de coeficientes, cada uno entrenado sin un partido, y
   además el de los 7, que es el de la entrega y el de por defecto. Sin `--versiones`, la salida del
   harness no cambia.
3. **Solo `H` frente a `A`,** con la columna `D` a cero, como N1. Con el `D` oráculo la columna `D` no
   cambia ninguna etiqueta, y el harness tapa el balón en todos los `D`: un `D` aprendido en la DFL
   aprendería «sin balón = `D`». El `D` sigue siendo de Ana y Manuel. Por eso el modelo es de dos clases y
   no de tres, como decía §4.2.

Lo común a los dos candidatos (fijado antes de medir):
- **Modelo:** regresión logística de `H` frente a `A`, entrenada en numpy (Newton, iteraciones fijas, L2
  pequeña). No hay scikit-learn ni LightGBM, y en el pipeline solo va numpy: los coeficientes quedan
  escritos en el módulo.
- **Simétrica por construcción:** todos los rasgos son «lo del local menos lo del visitante» y no hay
  término independiente. Así no aprende la ventaja de jugar en casa de siete partidos de otra liga.
- **Rasgos sin identidad,** invariantes al orden de los slots, calculados dentro de cada tramo evaluado
  (ninguna ventana cruza el descanso). Las ventanas son medias centradas con el balón ausente a cero.
- **Datos de entrenamiento:** los partidos de la DFL con el balón «como el ATD» (la misma degradación que
  vota en el harness), solo los frames vivos en los que las dos convenciones coinciden (`flag` = `control`),
  uno de cada 5. Así el modelo no aprende ninguna de las dos convenciones en los frames en que discrepan.
- **Escala:** la puntuación es α·z a favor del equipo que el modelo da como poseedor (z, el logit) y cero
  para el otro y para `D`, redondeada a 6 decimales. α se elige dentro de cada pliegue, con los partidos de
  entrenamiento de ese pliegue: de la rejilla 1/16, 1/8, 1/4, 1/2, 1 y 2, la que da más `spellF1` medio en
  las dos condiciones que votan y con las dos convenciones, con el decodificador de `main` y el `D` oráculo.
  Si empatan, la más pequeña.
- **Dejando un partido fuera:** 7 pliegues. En el harness, cada partido se puntúa con el pliegue que no lo
  vio.

Candidatos (solo cambia el conjunto de rasgos):
- **B1, proximidad aprendida.** Rasgos del balón: el signo del equipo más cercano (N1); la suma de núcleos
  gaussianos de las distancias de cada equipo al balón, con σ de 1, 2,5 y 6 m; y la distancia del más
  cercano de cada equipo, con un tope de 15 m. Cada uno, en ventanas de 1, 13, 51 y 151 frames: 20 rasgos.
- **B2, proximidad y forma aprendidas.** B1 más rasgos de los jugadores, que también opinan sin balón. La
  dirección de ataque de cada equipo sale de la x media de sus jugadores en cada tramo. Con ella:
  - la posición del juego (los dos centroides) a lo largo del ataque del local;
  - la del balón, en ventanas de 1 y 51 frames;
  - la velocidad media de los jugadores de los dos equipos en esa dirección, en ventanas de 25 y 101 frames,
    sin las velocidades de más de 12 m/s, que son cambios de slot;
  - la dispersión de cada equipo, en una ventana de 51 frames.

  Además, el juego, las dos velocidades y la dispersión, repetidos solo donde no hay balón a ±12 frames:
  30 rasgos.

Cómo se medirá: `validation/harness/puntuar.py --versiones validation/harness/versiones/apuesta_b.json
--eventos`, con el control y la versión de `main` (`{}`) en el mismo fichero. Gana con la regla de §5.8 en
las dos condiciones que votan y con las dos convenciones, frente al control **y** frente a `main`. Los
eventos humanos son descriptivos. Antes de medir se comprobará que, sin `--versiones`, la salida no cambia
y que N1 por el camino nuevo da lo mismo que `{}`.

Añadido tras entrenar y antes de medir en el harness (14/11):
- **α salió 2, el borde superior de la rejilla, en los 16 pliegues** (B1 y B2). El `spellF1` medio de
  entrenamiento todavía sube de 1 a 2, pero menos que en el paso anterior: entre +0,001 y +0,011, frente a
  unos +0,018. **No se amplía la rejilla:** se mide con lo que da el procedimiento fijado. Además, α
  también fija cuánto pesa `H`/`A` frente a las piezas de `D` en la entrega, y con el `D` oráculo eso no
  se ve. Si un candidato se queda a menos de ~0,01 de la regla, la rejilla ampliada sería un tercer
  candidato, declarado como tal.
- **Valores fijados al escribir el código** (la entrada solo decía «iteraciones fijas, L2 pequeña»): L2 de
  1 sobre los rasgos divididos por su raíz cuadrática media, 25 iteraciones de Newton y los pesos con 6
  cifras significativas. Ninguno se ajustó. Con unas 90.000 filas, esa L2 es despreciable, y el último
  paso de Newton queda por debajo de 1e-13 en los 16 pliegues.
- **Comprobaciones del instrumento** [medido]:
  - sin `--versiones`, la salida del harness (tabla y `--json`) es idéntica byte a byte a la de `main`;
  - N1 por el camino nuevo (`aprendida.…` con `dejar_fuera`) da las mismas 8 celdas que `{}`, y la pieza
    recibe los 7 partidos;
  - `prueba_harness.py` y `prueba_pipeline.py` pasan.

Resultado (14/11; `validation/resultados/2026-11-14_apuesta_b.md`, código `b63374d`) [medido]:
- **B2 gana con la regla de §5.8 al control y a `main`,** en las dos condiciones que votan y con las dos
  convenciones:
  - con el flag, +0,062 [+0,050 a +0,075] y +0,045 [+0,032 a +0,058] frente a `main`, en 7 de 7;
  - con las etiquetas de control, +0,161 y +0,158, en 7 de 7.
- **B1 gana al control y empata con `main`:** con el flag, +0,016 y +0,011.
- **Eventos humanos (descriptivo):** B2 es un compromiso frente a `main`. Pierde 15,4 puntos en las
  recuperaciones y gana 14,2 en los duelos sin cambio: cambia de equipo menos y más tarde.
- **Límites que el harness no ve:**
  - lo que separa a B2 de B1 son los rasgos de los jugadores, y el harness no los degrada;
  - B2 puntúa de media 4,2 por frame a favor de un equipo en los `D` (N1, 0) y 7,7 en juego con balón
    (N1, 1), así que en la entrega compite con las piezas de `D` que puntúan.

Decisión y por qué: **pendiente de Ismael.** Con la regla, B2 sustituiría a N1. Antes de cambiar
`pipeline.PIECES` hace falta:
- medir B2 con los jugadores degradados como el ATD;
- decidir qué se hace con su escala frente al `D`.

Corte: lunes 16 a las 14:00.

Descartado:
- **B1:** empata con `main`, y entre empatados se queda lo de `main`.
- **Un `D` aprendido** (punto 3).
- **Gradient boosting** (§4.2): no cabe sin dependencias nuevas, y sus árboles no se pueden escribir en el
  módulo con solo numpy.
- **Entrenar con las etiquetas `control`:** son circulares con los rasgos de proximidad (README del
  harness).
