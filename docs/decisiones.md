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

### 2026-11-14 · `D` · estado con jugadores: candidatos y regla de lectura, escritos antes de medir

Quién: Ana

Qué se probó: todavía nada. Esta entrada fija lo que se va a comparar y cómo se va a leer, antes de
entrenar ni medir. La pieza es `possession/dead_state.py`: cuánto parece que el juego está parado en
cada frame, solo con los jugadores (`docs/PLAN_ENTREGA.md` §3).

- **Candidatos:**
  - **control (v0):** la pieza no opina, como hasta ahora;
  - **E1:** la velocidad media de los jugadores en 2 s, en una regresión logística de una variable;
  - **E2:** una regresión logística con los 11 rasgos de la revisión del 13/11 (§5.3), en ventanas
    centradas: velocidad media en 1, 2 y 4 s, percentil 75 y máximo de la velocidad, fracción de
    jugadores a menos de 1 m/s, jugadores fuera del campo, jugadores en un área, distancia entre los
    centroides de los equipos, dispersión, y cada equipo en su mitad;
  - **E3:** E2 más la velocidad media y la fracción de jugadores lentos en ventanas solo hacia atrás y
    solo hacia delante, de 2 y 4 s (19 rasgos). Pregunta que contesta: si mirar por separado lo que
    viene y lo que pasó coloca mejor el principio y el final de la parada.
- **Lo que queda fijo y no se compara:**
  - solo jugadores, sin balón: en la DFL va tapado durante el `D` y delataría la etiqueta, y en el ATD
    que falte no significa `D`;
  - los rasgos son agregados por frame de los slots que se ven; nada depende de qué slot es cada uno.
    La velocidad es la de `validation/partido/comun.py` (diferencia centrada de ±2 frames, sin los
    saltos de más de 12 m/s), para que el agregado 4 del partido se pueda comparar;
  - regresión logística de `scikit-learn` con los rasgos estandarizados, `C = 1` y uno de cada 5
    frames, sin azar. Los coeficientes del módulo son los del ajuste con los 7 partidos;
  - salida: el logaritmo de la razón de probabilidades en la columna `D`, con escala 1 y recortado a
    ±8; cero donde no se ve a nadie. Sin umbral ni histéresis, y sin prohibir nada;
  - el decodificador es el de `main` con sus costes por defecto (25). No se toca: es de David.

Cómo se midió (dataset, nº de partidos/posesiones, métrica): se medirá en los 7 partidos de la DFL
(Bassek et al., 2025), dejando uno fuera: el modelo que puntúa un partido se entrena con los otros
seis. Los jugadores van sin degradar y con los slots barajados, como en `validation/harness/dfl.py`.
Scripts en `validation/scripts/d_estado/`.

- **Por frame:** AUC de `D` frente a juego.
- **Por parada:** la puntuación de la pieza sola pasa por el decodificador (juego o `D`) y se compara
  con las paradas reales. Una parada está detectada si una racha de `D` predicha cubre al menos la
  mitad. Se miden la latencia del inicio y del fin, y los `D` espurios (rachas predichas que no tocan
  ninguna parada real).
- **`spellF1` oficial con el equipo oráculo:** el `D` de la pieza y el equipo de las etiquetas, con las
  dos convenciones (flag y control) y rellenando de las dos formas de la revisión (arrastrar el equipo
  previo o adelantar el que reanuda). Frente al control, con el bootstrap pareado del harness.
- **Sensibilidad, que no elige nada:** la escala de la puntuación a la mitad y al doble, y un temblor
  de 0,1 y 0,2 m en las posiciones de los jugadores.
- **Placebo:** la misma puntuación desplazada 60 s. No debería detectar paradas ni sumar.

Resultado: pendiente. Irá en una entrada aparte, con las medidas.

Decisión y por qué (la regla de lectura, fijada antes de medir):
- **El criterio del 13/11, con los 7 partidos juntos y leído así:**
  - el inicio a 25 frames o menos en al menos el 70 % de las paradas reales, y lo mismo el fin. Una
    parada no detectada cuenta como fallo. Los bordes que coinciden con el principio o el final de una
    parte no cuentan;
  - el sesgo mediano de cada borde dentro de ±12 frames, sobre las detectadas;
  - 0,3 `D` espurios o menos por minuto de juego;
  - ninguna racha de `D` ni de juego de menos de 25 frames. La duración mínima es del decodificador y
    no está elegida: 1 s es una lectura provisional.
- **Entre candidatos, la regla de §5.8 sobre el `spellF1` con equipo oráculo:** 0,03 o más, en 6 de 7
  partidos y con el intervalo sin el cero, con las dos convenciones y las dos formas de rellenar. Si
  no, empate, y entra el más simple: E1 antes que E2, y E2 antes que E3.
- **Las tres condiciones del balón del harness no aplican:** la pieza no usa el balón y el equipo es
  oráculo, así que serían tres veces el mismo número.
- **Si ningún candidato cumple el criterio él solo, no se da por cumplido.** Es lo esperable: la
  revisión midió en un partido que el estado llega 1 s tarde de mediana al inicio. Se apunta lo medido
  y se decide con Ismael si la pieza entra como estado, junto a las fronteras de Manuel.
- **Sin verificar:** que se traslade al ATD. Depende del agregado 4 del partido (velocidad media de
  los jugadores), que ejecuta Manuel.
- **Aclaración, añadida antes de medir con los 7 partidos:** el script de medida se probó con los dos
  partidos que ya estaban bajados, solo para ver que funcionaba. Ahí se vio que la regla de arriba no
  dice qué hacer si el orden no es transitivo (E3 gana a E1, pero E3 empata con E2 y E2 con E1). Se
  lee así: **entra el candidato más simple al que ningún otro gana.** Los números de esa prueba no se
  usan para nada más.

Descartado (antes de medir):
- **Usar el balón en esta pieza,** por lo dicho arriba.
- **Poner un umbral, una histéresis o una duración mínima en la pieza:** van en el decodificador.
- **Modelos no lineales (árboles, redes):** no caben como coeficientes escritos en el módulo y piden
  una dependencia nueva.
- **Ajustar la escala de la puntuación o los costes del decodificador para que el `D` salga mejor:**
  los costes son la pieza de David. Aquí la escala solo se mira como sensibilidad.

### 2026-11-14 · `D` · estado con jugadores: resultado de la medida

Quién: Ana

Qué se probó: los tres candidatos y el control de la entrada anterior, con su regla de lectura.

Cómo se midió (dataset, nº de partidos/posesiones, métrica): los 7 partidos de la DFL dejando uno
fuera (713 paradas; 3.061 posesiones con el flag y 1.736 con control), con
`validation/scripts/d_estado/medir.py`. Detalle en `validation/resultados/2026-11-14_d_estado.md`.

Resultado:
- **[medido] Ningún candidato cumple él solo el criterio del 13/11.** E2: 86 % de las paradas
  detectadas, inicio a 25 frames o menos en el 35 % y fin en el 40 % (se pide el 70 %), sesgo mediano
  de +14 y +17 frames, 0,26 `D` espurios por minuto y ninguna racha corta. E3 solo falla la latencia
  (37 % y 41 %). E1 falla cuatro de las cinco condiciones.
- **[medido] Frente a no opinar, con el equipo oráculo:** E2 gana con la regla de §5.8 (+0,039 y
  +0,032 con el flag, en 6 de 7 partidos; +0,175 y +0,172 con control, en 7 de 7). E3 también; E1 no.
- **[medido] Entre candidatos:** E3 empata con E2 (+0,002 a +0,010) y gana a E1; E2 empata con E1.
  Entra el más simple al que ningún otro gana: E2.
- **[medido] Placebo:** con la puntuación desplazada 60 s, AUC 0,52 y `spellF1` 0,28 por debajo del
  control.
- **[medido] Sensibilidad:** con la escala a la mitad sale algo mejor (+0,007) y con el doble deja de
  cumplir §5.8 con el flag (+0,020). Con un temblor de 0,1 m en los jugadores detecta el 61 % de las
  paradas; con 0,2 m, el 3 %, aunque el AUC sigue en 0,95.

Decisión y por qué:
- **El candidato escrito en `possession/dead_state.py` es E2.**
- **No se da por cumplido el criterio.** La pieza da el estado, no el instante: si entra, y cómo,
  lo decide Ismael, junto a las fronteras de Manuel.
- **Antes de usarla en el partido hace falta el agregado 4** (Manuel), comparado con la tabla de
  `referencia_agregado4.py`. Si los jugadores del ATD tiemblan, la pieza votaría contra el `D` [inferencia].
- **Para David:** los costes `to_dead` y `from_dead` y la escala de esta pieza son el mismo ajuste.

Descartado:
- **E1,** porque E3 le gana, y **E3,** porque no gana a E2 y es más complejo.
