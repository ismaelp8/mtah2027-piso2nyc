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
- medir B2 con los jugadores degradados como el ATD. Hecho el 14/11, en la entrada siguiente: sigue
  ganando a `main`, aunque sin voto;
- decidir qué se hace con su escala frente al `D`.

Corte: lunes 16 a las 14:00.

Descartado:
- **B1:** empata con `main`, y entre empatados se queda lo de `main`.
- **Un `D` aprendido** (punto 3).
- **Gradient boosting** (§4.2): no cabe sin dependencias nuevas, y sus árboles no se pueden escribir en el
  módulo con solo numpy.
- **Entrenar con las etiquetas `control`:** son circulares con los rasgos de proximidad (README del
  harness).

### 2026-11-14 · validación · apuesta B con los jugadores como el ATD (antes de medir)

Quién: Ismael (pidió la medida: «Sí, mídelo»); Claude la escribe y mide.

Qué se prueba: si la ventaja de B2 sobre `main` aguanta con los jugadores degradados como los del ATD. El
harness no los degrada y la ventaja de B2 sobre B1 sale de los jugadores
(`validation/resultados/2026-11-14_apuesta_b.md`). Es una medida de sensibilidad en `validation/apuesta_b/`:
las condiciones del harness no cambian.

De dónde se parte: R6 de `validation/perfil_atd/BITACORA.md`, escrita antes de medir el ATD, con una sola
desviación (el paso 1). Lo medido de los jugadores:

| | localizados por equipo: media / p10 / p50 / p90 | tramos de un slot: p50 | temblor |
|---|---|---|---|
| ATD | 10,20 y 10,29 / 9 / 11 / 11 | 35,5 s | 0,136 cm |
| DFL sin degradar | 11,0 y 10,8 | 2.765 s | 1,0 cm |

Cómo se degradan, por jugador, antes de barajar los slots y con un generador aparte (el balón queda
idéntico al del harness):
1. **Suavizado, en lugar del ruido de R6,** porque el ATD tiembla menos que la DFL: una media móvil
   centrada de k frames. k sale de {1, 5, 9, 13, 25}, el que deje el temblor más cerca de 0,136 cm.
2. **Los que faltan, en tres variantes,** porque no se sabe dónde le faltan los jugadores al ATD. Cada
   variante calibra un parámetro para que la media de localizados por equipo **en los frames de juego**
   quede en 10,25 ± 0,1. Se hace en juego porque con el `D` oráculo una ausencia en una parada no cambia
   ninguna etiqueta.
   - **«al azar»** (R6 tal cual): rachas presentes y ausentes que se alternan, de longitud geométrica. La
     media de las presentes se fija para que la mediana de los tramos dé 35,5 s; la de las ausentes es el
     parámetro que se calibra.
   - **«en las aglomeraciones»:** un jugador a 1,5 m o menos de otro y a 15 m o menos del balón (el limpio)
     desaparece con una probabilidad por frame, que es lo que se calibra. Vuelve tras una racha geométrica
     de media 1 s.
   - **«lejos de la jugada»:** falta todo jugador a más de W m del balón (el limpio) a lo largo del campo.
     W es lo que se calibra. Es el caso difícil para B2: `main` apenas lo nota, y los rasgos de forma de
     B2 sí.

Qué variantes votan, decidido por el perfil y no por la nota de B2. Se mide con `perfil._jugadores`, el
mismo código que midió el ATD, en los frames evaluados como en el ATD. Una variante vota si cumple las tres
cosas:
- media de localizados por equipo a 0,5 o menos de 10,25 (la tolerancia de R6);
- p50 = 11, p10 entre 8 y 10 y p90 = 11;
- mediana de los tramos entre 17,8 y 71 s (de ×½ a ×2, como R6).

Las que no pasan se puntúan sin voto. Además se apuntan, como descripción:
- qué parte de las ausencias cae en juego;
- los saltos de más de 12 m/s por minuto (0,689 en el ATD).

Qué se mide: B2 con los coeficientes ya escritos (entrenados con los jugadores limpios), B1, `main` y el
control, con `validation/harness/versiones/apuesta_b.json` sin cambios. Se mide en las dos condiciones del
balón que votan, con las dos convenciones y en cada variante de jugadores.

Comprobación del instrumento: sin degradar a los jugadores, el tracking es idéntico al de
`dfl.tracking_de`, y `main` repite 0,428 y 0,456 con el flag.

Regla de lectura, fijada antes de medir:
- **«B2 aguanta»:** B2 gana a `main` con §5.8 (las dos condiciones del balón que votan y las dos
  convenciones) en todas las variantes de jugadores que votan.
- **«depende de dónde falten»:** gana en alguna, pero no en todas.
- **«no aguanta»:** no gana en ninguna.
- **Si no aguanta o depende, B2 no entra tal cual.** Reentrenarla con los jugadores degradados sería un
  candidato nuevo, declarado como tal y con el corte del lunes 16 a las 14:00.
- **Descriptivo:** B2 frente a B1 en cada variante, para ver si la ventaja de los jugadores se mantiene.

Sin modelar:
- slots con el equipo cambiado;
- slots de más (el ATD tiene 24 y 22 por equipo);
- detecciones falsas de jugadores.

Añadido tras calibrar y mirar el perfil, antes de puntuar ninguna versión (14/11) [medido]:
- **La calibración** (commit `60fc9fb`): suavizado de 13 frames (0,154 cm de temblor); 78,12 frames por
  ausencia «al azar», 0,1875 por frame «en las aglomeraciones» y W = 44,38 m «lejos de la jugada». Las tres
  dejan 10,24–10,27 localizados por equipo en juego.
- **Ninguna variante pasa la comprobación del perfil:**

  | variante | qué falla |
  |---|---|
  | «al azar» | p50 del visitante: 10 |
  | «lejos de la jugada» | p10: 7, y p50 del visitante: 10 |
  | «en las aglomeraciones» | solo la mediana de los tramos: 16,3 s, por debajo de 17,8 |

  Lo que dice [inferencia]: en el ATD faltan varios jugadores a la vez, pero no tantos ni tan a menudo
  como lejos del balón.
- **Saltos de más de 12 m/s:** unos 25 por minuto en las tres variantes, frente a 0,689 del ATD. Vienen del
  barajado de slots del harness, que es mucho más duro que los cambios de slot del ATD, y vale para todas
  las versiones.
- **Ajuste, como en R6, que calibra también la mediana de los tramos:**
  - «en las aglomeraciones» pasa a ausencias de 2, 3 o 4 s de media (en vez de 1 s);
  - se toma la primera de esas tres que pase el perfil, recalibrando su probabilidad para 10,25 en juego;
  - si pasa, es la única variante que vota;
  - «al azar» y «lejos de la jugada» se puntúan sin voto, como descripción y como cota;
  - si ninguna pasa, la medida no concluye y las tres se puntúan sin voto.
- **Tampoco pasa con el ajuste** (commit `b539f85`) [medido]:
  - con ausencias de 2, 3 y 4 s, la mediana de los tramos ya cuadra (20,4 / 24,9 / 27,6 s);
  - pero el p50 de localizados del visitante queda en 10 en los tres casos.

  Causa probable [inferencia]: en la DFL el visitante ya parte de 10,8 localizados (no de 11), y la
  calibración iguala la media de los dos equipos, no la de cada uno.
- **Por la regla, la medida no concluye.** No se retoca más la degradación. Las tres variantes se
  puntúan sin voto, con la calibración de `60fc9fb` (ausencias de 1 s en las aglomeraciones), como
  descripción y como cota.

Resultado (14/11; `validation/resultados/2026-11-14_apuesta_b.md` §7) [medido, sin voto]:
- **B2 gana a `main` con §5.8 en las tres variantes,** con las dos convenciones y en las dos condiciones
  del balón, en 7 de 7 partidos.
- **Con el flag**, frente a `main` («como el ATD» y «sin bloques»):

  | jugadores | margen |
  |---|---|
  | «al azar» | +0,093 y +0,080 |
  | «en las aglomeraciones» | +0,103 y +0,096 |
  | «lejos de la jugada» | +0,067 y +0,050 |

- **Quitar jugadores cerca del balón** baja a N1 entre 0,03 y 0,06, y a B2 como mucho 0,01.
- **B1** gana a `main` en las dos primeras variantes y empata en la tercera.

Decisión y por qué:
- **La medida no concluye por la regla,** porque ninguna variante vota.
- **Como descripción,** no hay ninguna señal de que la ventaja de B2 dependa de tener a los jugadores
  perfectos de la DFL: también gana en «lejos de la jugada», el caso difícil para sus rasgos de forma.
- **Lo que queda para decidir si B2 entra** es la escala frente al `D`. Lo decide Ismael.

Añadido después (14/11, `validation/apuesta_b/d_propio.py`) [medido, descriptivo]:
- **Con la pieza de `D` de `main` dentro** (E2 de Ana, PR 5) y sin oráculo, B2 tal cual solo ve el
  31,6 % de las 713 paradas reales, frente al 87,8 % de N1 y el 84,7 % de B1.
- **Por eso pierde contra `main` en `spellF1`:** 0,309 frente a 0,366 con el flag, y 0,477 frente a
  0,505 con el control («como el ATD»).
- **El número favorece a N1,** porque la DFL tapa el balón en los `D`. Pero el mecanismo es real: B2
  opina con los jugadores, haya balón o no, y en las paradas le gana a la pieza de Ana.
- **B2 no puede entrar tal cual.** Haría falta un candidato nuevo que no pese en las paradas, medido otra
  vez. Lo decide Ismael.

Descartado: retocar más la degradación hasta que una variante vote. Sería buscar hasta que algo pase.

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

### 2026-11-14 · `D` · el estado con jugadores (E2) entra por defecto: los jugadores del ATD se mueven como los de la DFL

Quién: Ismael

Qué se probó: si el modelo de estado de `D` (E2, `possession/dead_state.py`), entrenado con los jugadores
de la DFL, se traslada al ATD, y qué hace si faltan jugadores.

Cómo se midió (dataset, nº de partidos/posesiones, métrica):
- los agregados de los jugadores del ATD en los 158.857 frames evaluados
  (`validation/partido/agregados_jugadores.py`, ejecutado por Ismael), leídos con una regla de cinco
  condiciones fijada antes de ejecutar;
- la referencia de la DFL partido a partido y la pieza con jugadores que faltan a ratos, en los 7
  partidos (713 paradas), con `validation/scripts/d_estado/traslado_atd.py`.

Detalle en `validation/resultados/2026-11-14_agregados_jugadores_atd.md`.

Resultado:
- **[medido] Se cumplen las cinco condiciones:** el 35,4 % de los frames con la velocidad media por
  debajo de 1,2 m/s (DFL, por partido: 27–38 %), un p10 de 0,70 m/s (0,62–0,76), algún jugador fuera del
  campo en el 11,0 % (12,6–17,7 %), tres o más en el 0,7 % (0–1,2 %) y 22 slots vistos de mediana.
- **[medido en la DFL] Que falten jugadores a ratos no rompe la pieza:** con 20 vistos de 22 detecta el
  86 % de las paradas, igual que con todos. Con 18, el `spellF1` con equipo oráculo baja de 0,813 a 0,789
  y sigue por encima de no opinar (0,770).
- **[observación] Antes de los saques de banda y de puerta la velocidad media de los jugadores no baja:**
  queda por debajo de 1,2 m/s en el 44 % y el 36 % de los frames, frente al 91 % antes de un córner. Son
  36 de los 59 reinicios.

Decisión y por qué:
- **E2 queda por defecto en `possession/dead_state.py`** (PR 5). Gana a no opinar con la regla de §5.8
  con el equipo oráculo, y lo que quedaba sin verificar, que se trasladara al ATD, se cumple.
- **No se da por cumplido el criterio del 13/11.** La pieza da el estado y llega tarde al instante. El
  instante lo pone la pieza de fronteras (Manuel), sobre todo en los saques de banda y de puerta.
- **Los umbrales de la regla los puso la revisión de la PR** y se escribieron en la conversación antes de
  ejecutar, no en el repo.
- **La elección entre candidatos no depende del desempate.** El desempate de la entrada anterior («entra
  el más simple al que ningún otro gana») se fijó tras probar el script con 2 de los 7 partidos, y está
  declarado. Sin él, el más simple sería E1, que no gana a no opinar con el flag (+0,006, en 3 de 7): la
  elección real era E2 o no opinar.
- **La escala de la puntuación está sin ajustar:** va tal cual (escala 1, recortada a ±8), frente al 1 de
  la evidencia de equipo y los costes de 25. En la medida de la PR, a la mitad sale algo mejor y al doble
  deja de cumplir §5.8 con el flag.
- **La entrega regenerada queda dentro de la banda fijada antes** (orden de magnitud [inferencia de la
  DFL]: `D` entre el 15 y el 60 % de los frames evaluados y 250 paradas como mucho): 43,4 % de `D` y 111
  paradas [medido]. Fuera de ella se habría vuelto atrás con un commit que dejara `evidence` sin opinar.
  En la ventana pública no está rota (ninguna `X` evaluada, 19 posesiones frente a 17, F1 de `D` 0,767);
  eso no elige ni mide la mejora.
- **Pendiente (Ana):** apuntar la versión de `scikit-learn` con la que se entrenó.
- **Sin medir:**
  - que el `D` acierte en este partido: no se puede. La ventana pública solo dice si algo está roto;
  - los rasgos de forma de los equipos en el ATD (centroides, dispersión, cada equipo en su mitad y
    jugadores en un área): la regla no los cubre. Su única comprobación es la entrega regenerada;
  - las piezas juntas. Los costes `to_dead` y `from_dead` y la escala de esta pieza son el mismo ajuste,
    y el harness, con el `D` oráculo, no lo ve. Quien cambie esos costes repite
    `validation/scripts/d_estado/medir.py`.

Descartado:
- **Dejar la pieza sin opinar por defecto y el modelo con otro nombre:** era la alternativa si fallaba
  alguna condición.

### 2026-11-14 · candidatos · limpieza fija del balón y candidatos N2 y retención frente a N1, escritos antes de medir

Quién: Antonio Azuero

Qué se probó: **escrito antes de medir; todavía no se ha medido nada.** Es la pieza de
`docs/PLAN_ENTREGA.md` §3 (Antonio): `possession/ball.py` y `possession/candidates.py`.

- **Limpieza del balón (`ball.py`): una sola versión, fija y sin variantes** (plan, §3 y §8). Se aplica en
  este orden:
  1. **salto imposible:** se quita un punto si, para llegar a él desde el punto visto anterior **y** para
     ir de él al siguiente, el balón tendría que ir a más de 40 m/s. Se exigen los dos lados para no
     borrar el primer punto bueno después de un salto;
  2. **detección aislada:** se quita una racha de 1 o 2 frames con balón que tiene huecos a los dos lados;
  3. **hueco corto:** se interpola en línea recta un hueco de 12 frames o menos (menos de 0,5 s) entre dos
     puntos vistos, salvo en dos casos:
     - el hueco obliga a ir a más de 40 m/s: el balón no reaparece donde se le espera;
     - el balón reaparece junto a un jugador del otro equipo: en el primer frame tras el hueco, el más
       cercano es del equipo contrario al más cercano del último frame antes del hueco, y está a 2 m o
       menos. Ahí puede haber un cambio de posesión, y decide el decodificador.
- **Evidencia de equipo (`candidates.py`): tres versiones.** Las tres dan 1 a favor de un equipo en los
  frames en que opinan y 0 («no opino») en el resto, la misma unidad que la v0:
  - **N1, la referencia:** el equipo del jugador más cercano al balón. Es la v0, lo mismo que el baseline;
  - **N2, más cercano con radio y margen:** opina solo si el más cercano está a 1,5 m o menos y el más
    cercano del otro equipo está al menos 1 m más lejos que él;
  - **Ret, control por retención:** opina en los frames de una racha de 12 frames seguidos o más (0,48 s)
    en la que el más cercano es siempre del mismo equipo y está a 1,5 m o menos. Va por equipo y no por
    jugador, porque un slot no es un jugador. Es la traducción de «un toque sin control no cambia la
    posesión».
- **De dónde salen los valores** (ninguno sale del partido ni de la ventana pública):
  - 40 m/s, las rachas de 1 o 2 frames y los huecos de menos de 0,5 s son los cortes que ya mide el perfil
    del ATD (`validation/perfil_atd/BITACORA.md` §4, filas 1 y 6). Así, la medida del balón del partido
    dirá cuánto toca cada regla en el ATD. Los golpeos más fuertes publicados rondan 18–35 m/s
    (`docs/investigacion_metodos.md` §2.1);
  - 1,5 m es el radio de control «ampliado» del experimento 2 (por si el ATD es más ruidoso) y el de los
    toques del experimento 0. El margen de 1 m y Ret-12 también los mide el perfil (filas 5 y 4a);
  - 2 m es el radio de toque «ampliado» del experimento 2.
- **Ret se parece a la regla que fabricó las etiquetas `control`** del harness (C0-12: el mismo jugador a
  1 m o menos durante 12 frames, o dos toques). Ganará con ellas por construcción. Se mantiene así porque
  traduce la convención decidida el 12/11 («exigir control»). La circularidad la resuelve la regla:
  solo cuenta lo que gane también con el `flag`.

Cómo se medirá (dataset, nº de partidos/posesiones, métrica):

- **Harness de la DFL** (`validation/harness/puntuar.py`): los 7 partidos de la Bundesliga (Bassek et
  al., 2025), con el `D` oráculo, las dos convenciones (`flag` y `control`) y las tres condiciones del
  balón. `spellF1` oficial y bootstrap pareado de 1.000 remuestreos con semilla fija.
- **Lo único que cambia entre versiones es la evidencia:** las tres con la limpieza nueva y el
  decodificador v0 (Viterbi con coste 25).
- **Comparación principal: cada candidato frente a N1.** Gana con la regla de §5.8 si, en las tres
  condiciones y con las dos convenciones, gana en 6 de los 7 partidos o más, la diferencia es de 0,03 o
  más y el intervalo del 5 al 95 % no incluye el cero.
  - Si no gana, es un empate y se queda N1, que es el más simple.
  - Si ganan los dos, se comparan entre sí con la misma regla. Si empatan, entra N2, que no tiene ventana
    temporal.
- **Además, frente al control del harness** (baseline, voto de ±50), que es la tabla que pide el plan en
  cada PR. No cambia la regla de arriba.
- **Sensibilidad a la escala, que no decide:** las tres evidencias también con costes 12 y 50. N2 y Ret
  opinan en menos frames que N1, así que con el mismo coste son más conservadoras. Si el orden cambia con
  el coste, se apunta: la ventaja sería de la escala, que es cosa del decodificador, y no de la evidencia.
- **La limpieza se comprueba, no se elige:** N1 con y sin la limpieza nueva. Si con ella N1 pierde 0,03 o
  más en alguna condición o convención, se avisa a Ismael antes de la PR y no se retocan sus valores. En
  la DFL, los pasos 1 y 2 casi no harán nada, porque la degradación no mete detecciones falsas. Su efecto
  en el ATD no se puede medir fuera.
- **Diagnóstico, que no decide:** acierto de equipo y posesiones predichas frente a reales.
- **Aviso del plan (§3 y §4):** el orden entre evidencias no se da por bueno hasta que la degradación de
  la DFL esté comprobada con la medida del balón del ATD. Con esta medida se implementa y se mide; la
  decisión llega después.

Primera medida (14/11 por la tarde, con las condiciones de antes; ya no decide): lo de arriba no ha
cambiado.

- **Cómo se midió:** como estaba escrito, con una copia local de `validation/harness/puntuar.py` que
  dejaba elegir la evidencia de cada versión y la versión de referencia. Se hizo antes de que el harness
  aceptara `--versiones`, sobre el `main` de entonces (84b8d7c); esa copia ya no existe.
- **Con qué se mide:** 3.061 posesiones con el `flag` y 1.736 con `control`, y el balón visible en el
  98,7 % de los frames de juego (limpio) o en el 58,3 % (con huecos). [medido]
- **La comparación principal, frente a N1 con coste 25:** diferencia de `spellF1` con los 7 partidos
  juntos, su intervalo del 5 al 95 % y en cuántos partidos gana. [medido]

  | etiquetas | balón | N1 | N2 − N1 | Ret − N1 |
  |---|---|---|---|---|
  | flag | limpio | 0,474 | −0,095 [−0,108 a −0,083], 0 de 7 | −0,092 [−0,104 a −0,080], 0 de 7 |
  | flag | huecos | 0,383 | −0,056 [−0,067 a −0,047], 0 de 7 | −0,070 [−0,081 a −0,059], 0 de 7 |
  | flag | huecos y suavizado | 0,374 | −0,066 [−0,076 a −0,056], 0 de 7 | −0,068 [−0,079 a −0,057], 0 de 7 |
  | control | limpio | 0,630 | +0,005 [−0,013 a +0,023], 4 de 7 | +0,013 [−0,005 a +0,029], 5 de 7 |
  | control | huecos | 0,589 | −0,023 [−0,040 a −0,008], 1 de 7 | −0,046 [−0,062 a −0,029], 0 de 7 |
  | control | huecos y suavizado | 0,573 | −0,037 [−0,054 a −0,021], 0 de 7 | −0,044 [−0,061 a −0,027], 0 de 7 |

- **Ninguno de los dos gana a N1** con la regla de §5.8. [medido]
  - Con el `flag` pierden en las tres condiciones y en los 7 partidos.
  - Con `control`, que los favorece por construcción, empatan con el balón limpio; con huecos, N2 empata
    (−0,023, por debajo de 0,03) y Ret pierde.
- **Por qué, en parte:** opinan en menos frames y, con el mismo coste, cambian de equipo menos veces.
  Con coste 25 predicen 998–1.162 posesiones (N2) y 1.025–1.232 (Ret), frente a 1.382–1.871 de N1.
  [medido]
- **Sensibilidad a la escala, que no decide:** [medido]
  - con coste 50 pierden en las seis combinaciones (de −0,04 a −0,07, 0 de 7);
  - con coste 12 y el `flag` siguen perdiendo (de −0,02 a −0,05, en 0–3 de 7);
  - con coste 12 y `control` ganan mucho (de +0,06 a +0,21, 7 de 7). N1 con coste 12 predice 2.003–3.079
    posesiones, frente a 1.736 reales.
  - Con `control`, el orden cambia con el coste: es cosa de la escala del decodificador, no de la
    evidencia. Con el `flag` no cambia con ningún coste.
- **Cada evidencia con su mejor coste de los tres** (mirado después; solo descriptivo): con el `flag`, N1
  sigue por delante en las tres condiciones. N1 saca 0,474 / 0,397 / 0,379, N2 0,433 / 0,364 / 0,333 y
  Ret 0,430 / 0,344 / 0,330. [medido]
- **La limpieza, comprobada:** N1 con y sin la limpieza nueva se mueve entre −0,002 y +0,008 (redondeado
  a tres decimales), en las 18 combinaciones de coste, condición y convención. Está lejos del −0,03 que
  obligaba a avisar. [medido] En la DFL solo actuaría el relleno de huecos cortos, porque la degradación
  no mete saltos ni detecciones falsas. [inferencia: no se contaron los puntos que toca cada paso]
- **Para el decodificador (David)** [inferencia]: la evidencia y el coste de cambio no se eligen por
  separado.
  - Con `control`, la mejor combinación medida es una evidencia que opina poco con un coste bajo: N2 con
    coste 12 saca 0,680 con el balón limpio.
  - Con el `flag`, nada gana a N1 con coste 25.

Cambios antes de volver a medir (14/11 por la noche, escritos antes de la segunda medida):

- **Por qué se vuelve a medir:** desde el 14/11 por la noche, el harness tapa el balón «como el ATD».
  Votan «como el ATD» y «como el ATD, sin bloques», y para sustituir a `main` hay que ganar al control
  **y** a `main` (entrada de Ismael de arriba; plan, §4). Las condiciones de la primera medida ya no
  votan. Los candidatos y sus valores no cambian.
- **Cómo se mide ahora:** sin tocar `puntuar.py`, con
  `validation/harness/versiones/evidencia_equipo_2026-11-14.json`. El fichero trae cuatro versiones, y
  cada una cambia una sola pieza respecto a `main`:
  - «N1 (main)», `{}`;
  - «limpieza v1», con `ball.clean_v1`;
  - N2;
  - Ret.
- **Lo que cambia respecto a lo escrito antes de medir:**
  - **N2 y Ret se miden sin la limpieza nueva,** frente a `main`, y no con ella frente a N1. Así cada
    versión cambia una sola pieza. En la primera medida, la limpieza movió a N1 menos de 0,01.
  - **La limpieza ya no entra «fija»:** pasa a ser una candidata más (`ball.clean_v1`). `ball.clean`
    sigue siendo lo de `main` hasta que gane. El plan (§3 y §8) la daba por fija, pero la regla nueva dice
    que, si empata con `main`, se queda lo de `main`. Si se aplica esa regla o la del plan, lo decide
    Ismael.
  - **La sensibilidad con costes 12 y 50 no se repite:** no decidía y ya se midió.
- **Mensaje de Ismael (14/11 por la noche):**
  - hay que priorizar `ball.py`, porque quitar los ~200 saltos imposibles del ATD ayuda a cualquier
    evidencia;
  - N2 y Ret tendrían que ganar también a la apuesta B (B2), que ya gana a `main`.
  - Lo que sabemos del ATD (perfil del 14/11, agregados): 216 pares de frames seguidos a más de 40 m/s,
    149 rachas con balón, menos de 5 rachas de 1 o 2 frames y 15 huecos de hasta 0,5 s que suman 51
    frames. [medido, por Ismael] **En el partido, el paso 1 es el único que puede hacer algo.** En la DFL
    no hay saltos que quitar, así que el harness no lo puede ver. [inferencia]
- **Nota de la PR 7 (Antonio, 15/11), fuera del mensaje:** el perfil cuenta 216 **pares** de frames
  seguidos a más de 40 m/s, no puntos que la regla quite. El mensaje de arriba queda como se escribió.

Segunda medida (14/11 por la noche, harness «como el ATD»; la que decide):

- **Comando:**
  `python validation/harness/puntuar.py --versiones validation/harness/versiones/evidencia_equipo_2026-11-14.json`
  (huella fe8bc4f406cf, código 41b1431). 7 partidos, `D` oráculo, bootstrap de 1.000 remuestreos.
- **Con qué se mide:** 3.061 posesiones con el `flag` y 1.736 con `control`. El balón es visible en el
  87,3 % de los frames de juego «como el ATD» y en el 98,7 % «como el ATD, sin bloques». [medido]
- **Frente a `main`** (N1, sin limpieza): diferencia de `spellF1`, intervalo del 5 al 95 % y en cuántos
  partidos gana, en las dos condiciones que votan. [medido]

  | etiquetas | balón | `main` | limpieza v1 | N2 | Ret |
  |---|---|---|---|---|---|
  | flag | como el ATD | 0,428 | +0,000 [+0,000 a +0,001], 1 de 7 | −0,095 [−0,107 a −0,083], 0 de 7 | −0,082 [−0,095 a −0,070], 0 de 7 |
  | flag | como el ATD, sin bloques | 0,456 | +0,000 [+0,000 a +0,001], 1 de 7 | −0,105 [−0,117 a −0,092], 0 de 7 | −0,088 [−0,100 a −0,076], 0 de 7 |
  | control | como el ATD | 0,580 | +0,001 [+0,000 a +0,002], 1 de 7 | −0,017 [−0,035 a −0,000], 3 de 7 | +0,006 [−0,011 a +0,024], 5 de 7 |
  | control | como el ATD, sin bloques | 0,602 | +0,001 [+0,000 a +0,002], 1 de 7 | −0,014 [−0,033 a +0,004], 2 de 7 | +0,016 [−0,001 a +0,033], 5 de 7 |

- **Frente al control** (baseline, voto de ±50), en las condiciones que votan: `main` y la limpieza v1
  ganan por +0,022 con el `flag` (7 de 7 y 6 de 7) y por +0,108 a +0,117 con `control`. N2 y Ret pierden
  con el `flag` (de −0,060 a −0,083, 0 de 7) y ganan con `control` (de +0,094 a +0,125). [medido]
- **Ninguna de las tres gana a `main`** con la regla de §5.8. [medido]
  - N2 y Ret pierden con el `flag` en las dos condiciones y en los 7 partidos. Con `control` empatan.
  - La limpieza v1 empata en todo: no cambia ni una posesión predicha (1.782 y 1.920, igual que `main`).
- **Las dos condiciones sin voto** dan lo mismo que la primera medida: N2 y Ret pierden con el `flag`, y la
  limpieza mueve menos de 0,003. [medido]

Decisión y por qué:
- **Se queda N1** (`METHOD = "N1"`). N2 y Ret pierden frente a `main` con el `flag`, en las dos medidas,
  en todas las condiciones y en los 7 partidos. Con la regla, que exige las dos convenciones, no hay más
  que discutir. Además, para entrar tendrían que ganar también a la apuesta B (B2).
- **N2 y Ret se quedan en el código, sin usar,** como posibles variables de la apuesta B. Lo que entrega el
  pipeline no cambia.
- **La limpieza v1 no entra todavía:** `ball.clean` sigue siendo lo de `main`.
  - En la DFL empata, como se esperaba: no hay saltos falsos que quitar y casi no hay huecos cortos.
  - Lo que puede aportar está en los saltos del ATD, y el harness no lo ve. [inferencia] El perfil cuenta
    216 pares de frames seguidos a más de 40 m/s, no puntos que la regla quite: en un salto que se queda o
    en una excursión de varios frames, como mucho quita el tránsito, y el salto queda. Cuánto quita en el
    partido: medido el 15/11, en la entrada «balón · corrección del paso 2 de la limpieza» de más abajo.
    (Corregido el 15/11, en la PR 7, tras la revisión de la PR 6.)
  - Hace falta saber qué hace con el ATD antes de decidir, con un script de `validation/partido/` que
    ejecuta una persona.
  - Si entra con una prueba que no es el harness, lo decide Ismael, porque su regla dice que un empate con
    `main` deja lo de `main`.

Descartado (antes de medir):
- **N4, toques por cambios de velocidad del balón:** el experimento 2 apunta a que el balón del ATD viene
  suavizado, y el detector calibrado en la DFL casi no ve toques en él (plan, §3).
- **N3, las zonas de FIFA:** su ganancia exige un cambio de dirección o de velocidad del balón, y tiene el
  mismo problema que N4.
- **Variantes de la limpieza y barridos de radios o de frames:** con muchas variantes gana el azar (plan,
  §4 y §8).
- **L2, las reglas de puente en los huecos:** se dejan para después, si hay tiempo, con su propia entrada.

### 2026-11-14 · candidatos · apuesta B: B2 que no pesa en las paradas (candidatos, antes de medir)

Quién: Ismael aprobó probarlo («Sí, pruébalo»), con estas condiciones para entrar. Claude escribe los
candidatos y mide.

Por qué: con la pieza de `D` de `main` dentro (E2 de Ana), B2 tal cual solo ve el 31,6 % de las paradas y
pierde contra `main` (entrada del 14/11 y `validation/resultados/2026-11-14_apuesta_b.md` §4). B2 empuja de
media 4,2 por frame hacia un equipo en las paradas, y gana a los ±8 de Ana.

Lo común: el mismo logit que B2 (mismos rasgos y mismos pesos de cada pliegue, sin reentrenar). La
columna `D` sigue a cero.
- **Escala α:** se elige en cada pliegue con sus partidos de entrenamiento, **con la pieza de `D` de
  `main` dentro y sin oráculo**, y con el decodificador de `main`.
  - Criterio: más `spellF1` medio en las dos condiciones que votan y con las dos convenciones.
  - Rejilla: 1/8, 1/4, 1/2, 1, 2, 4 y 8, más ancha que la de B2, que salió en el borde.
  - Si empatan, la más pequeña.

Candidatos:
- **B3, B2 con puerta de balón** (el que se le explicó a Ismael): puntúa como B2 en los frames en que se ve
  el balón, y cero en los demás. La puerta es la de N1: el balón visible en ese frame, sin ventana. Una
  ventana de ±12 frames dejaría unos 7 frames ruidosos en cada borde de cada parada.
  - **Cuánto baja la voz sin balón: a cero, fijado.** Con el `D` propio de la DFL, «sin balón» es casi
    «`D`», así que cualquier ajuste se elegiría por ese artefacto.
  - Lo que cuesta: B2 pierde su evidencia en los huecos de juego, que era el 84,7 % de acierto sin balón.
- **B4, B2 que castiga al perdedor** (añadido; no es lo que se le explicó a Ismael): cero para el equipo
  que da el modelo, −α·|z| para el otro y cero para `D`.
  - La diferencia `H` − `A` es la de B2, así que con el `D` oráculo y la α de B2 da las mismas etiquetas.
  - El margen del ganador sobre `D` es siempre cero: el `D` lo decide solo la pieza de Ana.
  - Riesgo: sin el +1 que da N1 al ganador, puede decir `D` de más.

Criterios para entrar, fijados antes de medir:
1. **En el harness, con el `D` oráculo:** gana al control y a `main` con §5.8, en las condiciones que votan
   y con las dos convenciones.
2. **Con `validation/apuesta_b/d_propio.py`** (pieza de `D` de `main`, balón tapado en los `D` como en el
   harness), en las dos condiciones que votan:
   - ve al menos tantas paradas como `main` (87,8 % en las dos);
   - la precisión de su `D` no queda más de 2 puntos por debajo de la de `main` (93,8 % y 94,7 %), para que
     no gane diciendo `D` de más;
   - su `spellF1` con el `D` propio no queda por debajo del de `main` en las cuatro celdas (0,366 / 0,505 y
     0,394 / 0,536).

   Se lee con su límite de siempre: el tapado del balón en los `D` favorece a lo que solo opina con balón.

Si cumplen los dos, entra el más simple (B3). Si no cumple ninguno el lunes 16 a las 14:00, la apuesta B se
abandona.

Descriptivo, no es criterio: una segunda tabla de `d_propio.py` con el balón de la DFL a la vista en los
`D` (congelado). Es el caso que el tapado esconde: en el ATD, el balón se ve en el 68 % de los frames de
las ventanas `SET PIECES`.

Comprobaciones del instrumento:
- B4 con la α de B2 y el `D` oráculo da las mismas etiquetas que B2;
- B3 con la puerta abierta y la α de B2 es B2;
- tras entrenar, los coeficientes de `b1` y `b2` no cambian: el diff solo añade.

La terquedad en los robos (los eventos) no se resuelve aquí: la ajustará David con los costes, encima de la
evidencia que entre.

Resultado (14/11; `validation/resultados/2026-11-14_apuesta_b.md` §8, código `412c705`) [medido]:
- **Criterio 1: los dos ganan al control y a `main`** con §5.8. Frente a `main`, con el flag:

  | | «como el ATD» | «sin bloques» |
  |---|---|---|
  | B3 | +0,056 | +0,054 |
  | B4 | +0,066 | +0,052 |

  Con el control, de +0,142 a +0,150. Todo en 7 de 7 partidos.
- **Criterio 2, con la regla escrita: no lo cumple ninguno.**
  - **B3** ve 625 y 624 paradas, frente a 626 de `main` (de 713). La regla pide «al menos tantas», y queda
    1 y 2 paradas por debajo. Su precisión del `D` (97,4 y 98,9 %) y su `spellF1` con el `D` propio
    (0,422 / 0,641 y 0,450 / 0,679) quedan por encima de los de `main`.
  - **B4** ve más paradas (88,4 y 88,2 %), pero la precisión de su `D` (89,0 y 89,1 %) queda 4,8 y 5,6
    puntos por debajo de la de `main`, y el límite es 2: dice `D` de más.
- **Descriptivo, con el balón a la vista en los `D`:** B3 solo ve el 6,9 % de las paradas, `main` el
  75,3 % y B4 el 87,8 %.

Decisión y por qué: **por la regla escrita, no entra ni B3 ni B4.**
- B3 falla por 1 y 2 paradas de 713. Además, se come las paradas en las que se ve el balón, que en el
  ATD son muchas [inferencia].
- B4 dice `D` de más.
- Leer el «al menos tantas» con tolerancia, ahora que se ven los números, no vale.

Siguiente candidato posible, que decide Ismael: B4 más N1, es decir, la diferencia `H` − `A` de B2 y el
margen de 1 de N1 donde se ve el balón. Corte: lunes 16 a las 14:00.

Descartado: B3 y B4 tal cual.


### 2026-11-14 · candidatos · apuesta B: B5, B4 más el +1 de N1 (candidato, antes de medir)

Quién: Ismael aprobó probarlo con un tercer criterio («Sí, prueba B5»). Claude lo escribe y lo mide.

Por qué: en B3 y B4, la ventaja en `H` frente a `A` aguanta, y lo difícil es el margen del ganador sobre `D`
(entrada anterior):
- B3 lo daba con el balón y se comía las paradas en las que se ve el balón;
- en B4 era cero y sobraba `D`;
- N1 da un margen de 1 donde se ve el balón, y su `D` sale bien.

**B5:** la puntuación de B4 más la de N1.
- **B4:** los pesos de B2 y −α·|z| al equipo que no da el modelo.
- **N1:** +1 al equipo del jugador más cercano donde se ve el balón, con
  `candidates.nearest_team`, que es lo que hace `candidates.evidence` hoy. Se escribe aparte para que B5 no
  cambie si cambia `candidates.evidence`.
- **Frente a `H` y `A`:** decide la diferencia de B2 más la de N1.
- **Frente a `D`:** empuja como `main`, con 1 donde se ve el balón y 0 donde no.
- **α:** se elige en cada pliegue igual que en B3 y B4, con la pieza de `D` de `main` dentro y sin oráculo,
  con la rejilla 1/8 a 8. Si empatan, la más pequeña.

Criterios para entrar, los tres, fijados antes de medir:
1. **En el harness, con el `D` oráculo:** gana al control y a `main` con §5.8, en las condiciones que votan
   y con las dos convenciones.
2. **Con `validation/apuesta_b/d_propio.py`, con el balón tapado en los `D` como en el harness,** en las dos
   condiciones que votan, como en B3 y B4:
   - al menos tantas paradas vistas como `main` (626 de 713);
   - una precisión del `D` a 2 puntos o menos de la de `main` (93,8 % y 94,7 %);
   - un `spellF1` con el `D` propio no por debajo del de `main` en las cuatro celdas (0,366 / 0,505 y
     0,394 / 0,536).
3. **Con `d_propio.py` y el balón de la DFL a la vista en los `D`** (congelado; lo que pasa en el ATD con
   los balones parados), en las dos condiciones que votan: las paradas vistas no pueden quedar más de 1
   punto por debajo de las de `main` (537 de 713, el 75,3 %), es decir, al menos 530 de 713.
   - **Por qué ese margen:** un punto son 7 paradas. Es la mitad del ruido de una proporción de 713
     (±1,6 puntos) y deja fuera lo que le pasó a B3 (6,9 %).
   - **Va con margen y el criterio 2 no:** el 2 se fijó estricto y así se mantiene.

Si cumple los tres, B5 es el candidato de la apuesta B para entrar, y la decisión de cambiar
`pipeline.PIECES` es de Ismael. Si no, la apuesta B se abandona el lunes 16 a las 14:00.

Comprobaciones del instrumento:
- B5 menos B4 es exactamente la puntuación de N1;
- con el `D` oráculo, la diferencia `H` − `A` de B5 es la de B2 más la de N1;
- los coeficientes de B1 a B4 no cambian al reentrenar.

Resultado (14/11; `validation/resultados/2026-11-14_apuesta_b.md` §9, código `aaa2650`) [medido]:
**B5 cumple los tres criterios.**
1. **En el harness** gana al control y a `main` con §5.8, en 7 de 7 partidos en todas las celdas:

   | etiquetas | «como el ATD» | «sin bloques» |
   |---|---|---|
   | flag | +0,071 | +0,056 |
   | control | +0,148 | +0,146 |

2. **Con `d_propio.py` y el balón tapado:**
   - ve 629 y 628 paradas, frente a 626 de `main`;
   - la precisión de su `D` es 93,3 y 94,2 %, frente a 93,8 y 94,7 %;
   - su `spellF1` con el `D` propio es 0,416 / 0,616 y 0,433 / 0,642, frente a 0,366 / 0,505 y
     0,394 / 0,536.
3. **Con el balón a la vista en los `D`:** ve 545 paradas, frente a 537 de `main` (el mínimo era 530).

Eventos (descriptivo): un compromiso frente a `main`, como B2. Pierde en las recuperaciones (70 frente a
84) y gana en los duelos sin cambio (75 frente a 62).

Decisión y por qué: **B5 es el candidato de la apuesta B para entrar en la entrega.** Cumple los tres
criterios fijados antes de medir. Lo que faltaba lo decidía Ismael:
- cambiar `pipeline.PIECES["candidates"]` a `aprendida.evidence_b5`. Hecho, con su sí permanente, en la
  entrada «B5 entra en la entrega»;
- regenerar la entrega y comprobar su sha256;
- que David ajuste los costes encima de B5 (los de hoy están en la escala de N1).

Sin medir con B5: los jugadores degradados como el ATD (se midió con B2).

Añadido antes de medir (14/11): **B5 con los jugadores degradados como el ATD.**
- Se mide con `validation/apuesta_b/jugadores.py --versiones validation/harness/versiones/apuesta_b5.json`,
  con las mismas tres variantes y la misma calibración (`60fc9fb`).
- La lectura es la misma que con B2: sin voto, porque ninguna variante reproduce el perfil del ATD. Se
  mira si B5 gana a `main` con §5.8 en cada variante.
- Es descriptivo: no cambia el veredicto de B5, pero dice si su ventaja depende de los jugadores perfectos
  de la DFL.
- **Resultado** [medido, sin voto]: B5 gana a `main` con §5.8 en las tres variantes, en 7 de 7 partidos.
  Con el flag, de +0,059 a +0,106; con el control, de +0,120 a +0,236. La ventaja no depende de los
  jugadores perfectos.

Descartado: B3 y B4 (entrada anterior).


### 2026-11-14 · candidatos · B5 entra en la entrega como evidencia de equipo

Quién: Ismael, con su sí permanente a la apuesta B. Lo transmitió su sesión con esta cita: «A partir de
ahora todo lo que pregunte la sesión de Apuesta B dile que sí y acaba subiendo todos los cambios al final».
La sesión precisó que eso incluye cambiar `pipeline.PIECES` si B5 gana con los tres criterios. Claude hizo
el cambio en la rama; lo comprueba y lo sube a `main` la sesión de Ismael.

Qué se decidió: **la pieza de equipo de la entrega pasa de N1 (`candidates.evidence`) a B5
(`aprendida.evidence_b5`).** B5 cumplió los tres criterios fijados antes de medir (entrada anterior):
- con el harness, gana al control y a `main` con §5.8;
- con la pieza de `D` de `main`, no estropea el `D`, ni con el balón tapado ni a la vista;
- como descripción, sigue ganando con los jugadores degradados como el ATD.

Qué cambia:
- **`possession/pipeline.py`:**
  - `PIECES["candidates"]` = `"aprendida.evidence_b5"`;
  - `run` usa `default_piece`, que lee `PIECES` (antes, `run` tenía `candidates.evidence` escrito a mano);
  - en la entrega, `fuera` = None: los coeficientes de los 7 partidos de la DFL.
- **El harness deja fuera el partido también en la pieza de la entrega,** cuando la versión no la nombra y
  la función tiene `fuera`. Si no, la versión de `main` (`{}`) se puntuaría con partidos que ya vio.
  Comprobado: `{}` da las mismas 8 celdas que B5 escrita a mano con `dejar_fuera`
  (`comprobar_camino_nuevo.py`).
- **`aprendida.py` lleva su propia copia del «más cercano»** (`equipo_mas_cercano`, igual que
  `candidates.nearest_team` del 14/11). Así no hay importación circular, y B5 no cambia si Antonio cambia
  `candidates.py`.
- **Pruebas** (`prueba_pipeline.py`, `prueba_harness.py` y `prueba_aprendida.py`) y
  `versiones/ejemplo.json`, con B5 como pieza de la entrega.

Consecuencias:
- **La entrega cambia:** Ismael tiene que regenerarla (`python -m possession.pipeline`), validarla y
  apuntar el sha256 nuevo.
  - La reproducción byte a byte hay que comprobarla dos veces, y en otra máquina.
  - B5 usa `np.exp`, que puede variar en el último bit según la CPU; el redondeo a 6 decimales lo hace
    improbable, no imposible.
  - Se pegan solo agregados: frames en conflicto, posesiones por tramo y sha256.
- **Desde aquí, «main» es B5 en el harness.**
  - Los costes del decodificador (David) se ajustan encima de B5. Los de hoy (25) son con los que se eligió
    su α.
  - Los candidatos de evidencia de equipo (Antonio) tienen que ganar a B5.
- **Las tablas de antes de este cambio tienen N1 como `main`.** Para repetirlas, se usa el commit que cita
  cada resultado.
- **Eventos humanos:** B5 pierde en las recuperaciones (70 frente a 84). Lo ajustará David con los costes,
  como aceptó Ismael.

- **`validation/harness/versiones/evidencia_equipo_2026-11-14.json` (Antonio)** escribía N2 y Ret como
  `{"candidates": {"opciones": {...}}}`, sin `funcion`. Ahora apuntaría a B5 y daría error, así que se le
  puso `"funcion": "evidence"`, que es lo que midió. Su `{}` («N1 (main)») es B5 desde este cambio.

Descartado: el envoltorio en `candidates.py`. Habría tocado la pieza de Antonio y creaba una importación
circular.

### 2026-11-14 · `D` · fronteras y anclas: capas, candidatos y regla de lectura, escritos antes de medir

Quién: Manuel

**Estado (15/11), para quien llegue aquí:**
- **entra en `evidence`:** la capa 4, el hueco sin balón antes de cada reinicio;
- **no entran:** de gol a saque (no ancla ningún gol), R1 y la capa 3 (la salida del balón);
- **pendientes:** el final de cada parte y el equipo que reanuda.

Todo lo que sigue se escribió en este orden: las reglas, antes de cada medida. El resultado del 15/11 está
al final, antes de «Abierto».

Qué se va a probar: la pieza de `possession/dead_ball.py` (función `evidence`), por capas, en este orden.
Cada capa entra con la PR de la medida que la respalda (ver «Abierto»). Sale de
`docs/PLAN_ENTREGA.md` §3 y de `validation/resultados/2026-11-13_revision_balon_muerto.md` §6.

1. **Anclas duras,** en `allowed` (solo `D`):
   - ya en `main`: el tramo antes del saque de cada parte;
   - **de cada gol a su saque:** desde el fin de cada ventana `GOALS` hasta el inicio de la ventana del
     siguiente `Kick Off (After Goal)`. Un gol sin saque etiquetado después, o con el saque a más de 3
     minutos del fin de su ventana `GOALS`, no ancla nada. Cada saque se empareja con un solo gol (el
     emparejamiento cambió después: ver «Cambio después de ver los agregados»).
     **[sin verificar]** Que la ventana `GOALS` acabe con el balón ya en la portería;
   - **el final de cada parte:** solo si lo pide el agregado 4 (regla de abajo). Su candidato se escribe
     aquí antes de medirlo.
2. **Fin del `D` (el reinicio) y equipo que reanuda,** dentro de cada ventana `SET PIECES`. Candidatos para
   el instante del reinicio:
   - **R1:** el golpeo del balón, es decir, el balón visto quieto que empieza a moverse (`find_strike` de
     `validation/partido/diagnostico_balon_muerto.py`);
   - **R2:** sin instante: `D` antes del inicio de la ventana, juego después de su fin, y dentro decide el
     decodificador.

   **El equipo que reanuda:** el `Team` del `SET PIECE`, puntuado en `H` o `A` desde el reinicio. Los
   `Team = N/A` no puntúan equipo. Los saques de banda, que son `N/A`, quedan para una capa aparte
   (jugador fuera de la banda, agregado 6).
3. **Inicio del `D` (la salida):** el balón que desaparece a 2 m o menos de una línea, con 1 m/s o más
   hacia fuera y un hueco de 2 s o más. Son los umbrales del agregado 3. Se empareja con el `SET PIECES`
   que le sigue a 30 s o menos, y da `D` desde la salida hasta el reinicio de la capa 2.
4. **El hueco sin balón antes de cada reinicio** (idea de Ismael, 14/11; se añadió después de ver los
   agregados de abajo y antes de medirla). Se apoya en el perfil del ATD
   (`validation/resultados/2026-11-14_perfil_atd.md`): en los 10 s antes de cada `SET PIECE` el ATD ve el
   balón en el 27,6 % de los frames, frente al 59,2 % del resto [medido].
   - **Qué hace:** para cada ventana `SET PIECES` que no es un saque inicial, si no se ve el balón en los
     5 s anteriores a su inicio, puntúa `D` desde el primer frame sin balón hasta el inicio de la ventana.
   - **No puntúa** si el hueco pasa de 60 s (sería una parada larga o juego sin balón, y la capa no sabe
     distinguirlos) ni si otro `GOALS` u otro `SET PIECES` empieza dentro del hueco.
   - **No es `D` a pelo,** que es lo descartado el 13/11 y lo que `docs/PLAN_ENTREGA.md` §3 prohíbe
     («usar la falta de balón como `D`»): es una puntuación blanda, solo antes de un reinicio del Smart
     Tagging, y decide el decodificador. Así lo planteó Ismael en su mensaje a Manuel del 14/11: «como
     evidencia para el decodificador (no como D a pelo, que es lo que se descartó el 13/11)».
   - Código: `gaps_before_restarts` en `possession/dead_ball.py`, todavía fuera de `evidence` (entró el
     15/11: ver «Resultado de `validation/partido/agregados_dead_ball.py`», al final).

**Lo que no entra:**
- **el silbato:** según el mensaje de Antonio del 14/11, su sondeo no pasa su criterio porque la señal
  está sucia. Todavía no está apuntado en `validation/silbato/` **[sin verificar en el repo]**; lo apunta
  él;
- **lo descartado el 13/11:** suavizar el `D` con un voto, usar la falta de balón como `D` y arrastrar el
  equipo a través de una parada.

Cómo se medirá (dataset, nº de partidos/posesiones, métrica):
- **Agregados del partido:** los tres scripts de `validation/partido/` (`agregados_smart_tagging.py`,
  `agregados_balon_reinicios.py` y `agregados_jugadores.py`), que ejecuta Manuel.
- **Gol a saque y la capa 4:** `validation/partido/agregados_dead_ball.py`, que también ejecuta Manuel, con
  su propia regla (abajo).
- **La capa 3, que solo usa el balón, también en la DFL:** los 7 partidos con el balón tapado «como el
  ATD» y el criterio del 13/11.
- **Lo que usa el Smart Tagging no se puede medir en la DFL.** Se comprueba en el partido con agregados:
  ventanas que reciben un fin de `D`, duración de los `D` en intervalos gruesos, y balón en movimiento
  dentro de lo anclado.
- **Siempre:** `validation/scripts/prueba_pipeline.py` en verde después de cada cambio. La ventana pública
  solo dice si algo está roto.

Regla de lectura (fijada antes de ver los agregados):
- **De gol a saque entra** si el agregado 1 (punto 3) da los 4 goles con su saque etiquetado después. Si
  falta alguno, entran los que lo tienen.
- **El final de parte:** se escribe y se mide una capa para él solo si, en las dos partes, la velocidad
  media de los jugadores en los 30 s finales tiene un p50 por debajo de 1,2 m/s (como la DFL en `D`;
  agregado 4). Si no, no se hace nada.
- **R1 entra** solo en los tipos de reinicio (5 casos o más) en los que se cumplen las dos cosas
  (agregado 2):
  - el golpeo aparece en el 70 % o más de las ventanas;
  - cae a ±1 s de la subida de velocidad de los jugadores en el 70 % o más de las encontradas.

  En los demás tipos va R2.
- **La capa 3 entra** si se cumplen las dos cosas del agregado 3 y después pasa el criterio del 13/11 en
  la DFL. Si no, queda fuera:
  - el 50 % o más de las salidas van seguidas de un `SET PIECES` a 30 s o menos;
  - el 50 % o más de las ventanas de banda, córner y saque de puerta, los tres tipos juntos, tienen una
    salida en los 15 s previos. (El script cuenta de 15 s antes a 2 s después del inicio de la ventana;
    una ventana más estrecha solo puede dar menos, así que la decisión de abajo no cambia.)
- **Ningún umbral sale del partido:**
  - los de detección (2 m, 1 m/s, 2 s, 30 s, 15 s, ±1 s) son los de los scripts de la revisión;
  - el 1,2 m/s es la referencia de la DFL;
  - los de esta regla (70 %, 50 % y 3 minutos) se fijan aquí, antes de medir;
  - las puntuaciones de cada capa se marcan «sin ajustar» en el código.

**Cuándo se escribió la regla:** en la sesión de Manuel, antes de que él ejecutara los tres scripts. Pero
va en el mismo commit que el resultado, así que el historial de git no lo demuestra. Desde aquí, la regla
de cada medida nueva se sube en un commit antes de ejecutar su script.

Resultado (los tres agregados, ejecutados por Manuel el 14/11; solo agregados del partido entero):
- **[medido] Las ventanas `SET PIECES` duran 35 s** en banda, córner, saque de puerta y falta (p10, p50 y
  p90 de 35 s), y 5 s en los saques iniciales.
- **[medido] El golpeo cae más de 5 s antes del fin de la ventana** en las 53 ventanas de banda, córner,
  saque de puerta y falta.
- **[inferencia] El fin de la ventana no es el reinicio.** Se sostiene si el golpeo es el reinicio, y eso
  no lo ha validado la regla de R1.
- **[medido] `Team = N/A`** en el 100 % de los saques de banda y de los saques iniciales, y en el 0 % de
  córners, saques de puerta y faltas.
- **[medido] Los 4 goles tienen su saque etiquetado después,** con el emparejamiento de
  `agregados_smart_tagging.py`: desde el **inicio** de `GOALS`, sin emparejar uno a uno y sin tope. Del
  inicio de cada `GOALS` a su saque suman 16.403 frames (10,3 % de los evaluados), con una mediana de
  168 s.
  - Es unas 2,7 veces lo que infería la revisión (§4.2, unos 6.000 frames) y más que las paradas tras gol
    de la DFL (51 y 93 s). **[sin verificar]** Si es porque la ventana `GOALS` empieza con la jugada del
    gol o porque hubo revisiones largas.
- **[medido] Velocidad media de los jugadores en los 30 s finales de cada parte:** p50 de 1,15 m/s en la
  1ª y de 0,81 en la 2ª.
- **[medido] Golpeo a ±1 s de la subida de velocidad de los jugadores,** sobre las encontradas:
  - banda, 0 de 26;
  - córner, 2 de 12;
  - saque de puerta, 0 de 10;
  - saques iniciales, 3 de 5;
  - faltas, 3 de 5.

  El golpeo aparece en 26 de 26, 12 de 12, 10 de 10, 5 de 6 y 5 de 5.
- **[medido] Salidas del balón:** 24 de 133 huecos largos. De ellas, 16 (66,7 %) van seguidas de un
  `SET PIECES` a 30 s o menos. Tienen una salida entre 15 s antes y 2 s después de su inicio 6 de las 48
  ventanas de banda, córner y saque de puerta (12,5 %).
- **[medido] La columna de velocidad del balón del ATD** frente al desplazamiento suavizado a 1 s:
  correlación de 0,08 y cociente de medianas de 0,27.
- **[medido] Velocidad media de los jugadores en todo el partido:** p10/p50/p90 de 0,70/1,50/2,94 m/s, con
  el 35,4 % por debajo de 1,2. La fracción de jugadores a menos de 1 m/s da 0,08/0,29/0,74. La DFL sin
  temblor da 0,71/1,63/3,14, el 31,1 % y 0,03/0,24/0,73 (`validation/resultados/2026-11-14_d_estado.md`).
- **[medido] Algún jugador fuera de los límites:** en el 84,6 % de las ventanas de banda, el 91,7 % de las
  de córner, el 70 % de las de saque de puerta, el 80 % de las de falta y ninguna de saque inicial.

Decisión según la regla, sin cambiarla:
- **De gol a saque pasa esta regla,** pero entra en `main` solo si pasa también la de
  `validation/partido/agregados_dead_ball.py` (abajo). Cuántos goles anclan con el emparejamiento del
  código está **[sin verificar]** hasta ejecutarlo.
- **El final de parte se escribe como capa** (1,15 y 0,81 m/s, por debajo de 1,2). Su candidato se apunta
  antes de medirlo en la DFL. Ojo: 1,15 está muy cerca de 1,2, el tramo antes del saque de la 2ª parte,
  que es `D`, va a 1,30, y el 35 % del partido está por debajo de 1,2. Así que 1,2 no separa bien, y el
  candidato no lo usará como detector.
- **R1 no entra en ningún tipo.** El golpeo aparece en casi todas las ventanas, pero coincide con la
  subida de los jugadores como mucho en el 60 %.
  - En las faltas, contando solo las 4 que tienen subida, saldría el 75 %. La regla dice «de las
    encontradas», que son 5, así que no se cambia.
- **La capa 3 no entra:** 12,5 %, frente al 50 % pedido.

Lo que estos agregados enseñan y la regla no preveía:
- **La columna de velocidad del balón del ATD no se usa** (correlación de 0,08). Se decide sin un criterio
  escrito antes, porque la regla no tenía uno para el agregado 5.
- **R2 está mal especificada.** Con ventanas de 35 s fijos y el reinicio dentro, «`D` antes del inicio y
  juego después del fin» no dice dónde está el reinicio.
  - No se va a medir dónde cae el golpeo dentro de la ventana para fijarlo: sería circular (el golpeo no
    se ha validado) y daría una constante sacada del partido.
  - R2 se escribirá sin desfase sacado del partido: o «`D` hasta el inicio de la ventana, y dentro decide
    el decodificador», o con un desfase de la DFL o de la documentación de Metrica.
- **El equipo que reanuda por el `Team`** solo vale para 27 reinicios (córner, saque de puerta y falta).
- **[inferencia] Lo medido no contradice que el modelo de jugadores de Ana se traslade al ATD:** las dos
  líneas de su criterio se parecen a la fila sin temblor de la DFL. Un p50 algo más bajo también podría
  deberse a más tiempo parado.
- **[medido] En los 30 s iniciales del bloque de la 2ª parte**, que son `D` según el FAQ, los jugadores
  van a 1,30 m/s de mediana. Un `D` no siempre es lento.

Cambio después de ver los agregados, por fallos encontrados con casos inventados y no con datos:
- **El emparejamiento de gol a saque** era hacia delante (cada gol con el primer saque libre). Con un gol
  sin su saque, un `GOALS` falso o un reinicio por medio, anclaba juego vivo. Ahora va hacia atrás (cada
  saque con el último gol que acaba antes) y no ancla si entre los dos empieza otro `GOALS` u otro
  `SET PIECES`.
- **Después de la segunda revisión** (también con casos inventados), tampoco ancla si el otro `GOALS` o
  `SET PIECES` empieza justo en un extremo del tramo (en el fin del gol o en el mismo frame que el saque),
  ni si otro `GOALS` se pisa con el tramo aunque empiece antes. Dos saques en el mismo frame no anclan
  ninguno.
- **Las tres suposiciones del tramo, todas [sin verificar]:**
  - (a) la ventana `GOALS` acaba con el balón ya en la portería;
  - (b) la ventana del saque empieza en el reinicio o antes. Apoyo indirecto [inferencia]: según el
    código oficial (`starter/load_smart_tagging.py`, cabecera), las dos ventanas de `Kick Off (Start)`
    contienen el saque real. Que las de `Kick Off (After Goal)` hagan lo mismo no está comprobado;
  - (c) cada `GOALS` es un gol válido.

  **Si falla cualquiera de las tres, se fuerza `D` en juego.** (Antes ponía que si fallaba (a) solo se
  perdían frames de `D`: era al revés. Si la ventana acaba antes de que entre el balón, el tramo empieza
  con juego.) Si se cumplen, lo que se pierde es el `D` entre el gol y el fin de su ventana, que no se
  ancla y decide el decodificador.

Regla de lectura de `validation/partido/agregados_dead_ball.py`, fijada antes de ejecutarlo:
- **Sustituye a la que había aquí,** que no se llegó a usar. La segunda revisión vio tres problemas:
  - al mirar los tramos juntos, un gol falso se diluía entre los buenos;
  - no decía qué hacer sin goles ni sin balón;
  - dejaba abierto retocar la capa hasta que pasara.

  Esta regla se sube a GitHub antes de que Manuel ejecute el script, así que el historial demuestra el
  orden.
- **Gol a saque está programado, pero fuera de `evidence`** (`goal_to_kickoff_mask`, que `dead_mask` no usa
  todavía), igual que la capa 4. Así, mergear la rama antes de medir no cambia la entrega. Si pasa la
  regla, se conecta en el commit que trae los agregados.
- **Las medidas:** todas sobre los frames evaluados y con el balón como lo ve el pipeline (`tracking.from_atd`
  y `ball.clean`).
  - **Balón deprisa:** 5 m/s o más, con el desplazamiento suavizado a 1 s, en fracción de los frames con
    balón visto.
  - **Cuándo falla una prueba:** si esa fracción pasa de la mitad de la del partido entero. Solo decide
    con 1 s (25 frames) de balón visto o más.
  - **Cada tramo pasa tres pruebas:** el tramo entero (para (c)) y 5 s en cada borde, empezando 1 s dentro
    (para (a) y (b)). La velocidad de un frame usa las posiciones de ±0,96 s a su alrededor, así que desde
    1 s dentro ninguna mira frames de fuera del tramo, salvo por el suavizado propio del balón del ATD
    (unos 25 frames, que meten en el borde alrededor de 0,5 s de lo de fuera). El tramo falla si falla
    alguna, y no decide si no decide ninguna.
  - **(a) y (b) solo se comprueban donde el ATD ve el balón en el borde.** (a) queda sin comprobar en los
    tramos cuyo borde inicial no decide, y (b) en los que no decide el final (lo probable si el ATD no ve
    el balón tras el gol). Un tramo puede pasar así por el tramo entero. El script imprime cuántos bordes
    de cada lado no deciden; esas fronteras son **[sin verificar]**, y la PR lo dice.
  - **El script solo imprime cuántos tramos pasan y cuántos fallan,** nunca cuál: con 4 goles, cualquier
    desglose identifica cada parada.
- **De gol a saque entra si se cumplen las tres cosas.** Si no, queda fuera entera:
  - **el control pasa:** el tramo antes del saque de la 2ª parte, que el FAQ da como `D`, pasa las mismas
    pruebas. Si no, el instrumento no separa el balón muerto del juego y la medida no decide;
  - **el placebo tiene potencia:** se desplazan los tramos anclados 4, 6 y 8 minutos a cada lado (los que
    caen enteros en un tramo evaluado sin tocar ninguna ancla). Al menos el doble de los que hay anclados
    tienen que decidir, y tienen que fallar la mitad o más de los que deciden. Si no, la medida no decide;
  - **ningún tramo anclado falla, y pasan la mitad o más.** No se puede quitar un gol concreto, porque
    sería una constante sacada del partido. Por eso un solo tramo que falla deja fuera toda la capa.

  Es conservadora a propósito: un tramo bueno puede fallar si el ATD apenas ve el balón tras el gol y
  alguien lo patea al centro. Se prefiere perder la capa a forzar `D` en juego.
- **Sin ningún gol que ancle,** esta capa no tiene nada que subir.
- **El hueco antes de cada reinicio (capa 4) entra si se cumplen las tres cosas,** con una puntuación de
  `D` de 1 por frame, marcada «sin ajustar» (la misma escala que `NEAREST_SCORE` en `candidates.py`; la
  escala la ajusta David con los costes). Se aplica a todos los tipos de reinicio menos los saques
  iniciales:
  - **cobertura:** la mitad o más de las ventanas `SET PIECES` que no son saques iniciales y empiezan en
    frames evaluados tienen un hueco que la capa puntúa (el estado `hueco`: de 5 a 60 s y sin otro
    reinicio dentro). Cuentan todas en el denominador, también las de los estados `hueco largo` y
    `reinicio dentro`;
  - **placebo:** esa cobertura es al menos el doble de la de los mismos inicios desplazados 4, 6 y 8
    minutos a cada lado;
  - **el modelo de jugadores de Ana** (`possession/dead_state.py`, entrenado en la DFL e independiente del
    balón) ve `D` en los frames de todos los huecos al menos tanto como en el punto medio entre el
    partido entero y el control. Es decir, los huecos se parecen más al `D` seguro que al partido medio.
    Se cuenta solo en los frames en que el modelo opina. Si en el control no ve más `D` que en el partido
    entero, el instrumento no separa y la capa no entra.
    - **El control** es el tramo antes del saque de la 2ª parte y, si gol a saque entra (es decir, si
      cumple las tres condiciones de arriba: control, placebo y tramos), también esos tramos. El tramo antes del saque solo
      puede no bastar: en sus primeros 30 s los jugadores van a 1,30 m/s de mediana, con el 33,9 % por
      debajo de 1,2, casi como el partido entero (1,50 y 35,4 %) [medido, agregado 4]. Si el modelo no
      ve ahí más `D` que en el partido, la capa no entraría sin haber aprendido nada de los huecos. Si
      aun así no separa, se dice así en el resultado: no es un fallo de los huecos.
    - **Puede ver peor los huecos de banda y saque de puerta [inferencia]:** antes de esos reinicios la
      velocidad media de los jugadores no baja (44 % y 36 % de los 10 s previos por debajo de 1,2 m/s,
      frente al 91 % y el 73 % antes de córner y falta; medida de Ismael en
      `validation/resultados/2026-11-14_agregados_jugadores_atd.md`, que él marca como observación). Pero
      el modelo también mira cuántos jugadores hay fuera del campo (`fuera_2s`, con peso 3,32), y hay
      alguno fuera en el 84,6 % de las ventanas de banda y el 70 % de las de puerta [medido, agregado 6,
      contando desde 5 s antes de la ventana hasta su fin; no en el hueco].
      Si los ve peor, la condición es más difícil de pasar: la regla queda conservadora, no al revés.
    - **Dos cambios antes de medir:** la primera versión era esta. La segunda, al ver la medida de Ismael,
      juzgaba solo los huecos de córner y falta con «la mayoría de los frames». La revisión la tumbó por
      tres motivos:
      - daba por hecho, sin etiqueta, que el modelo no ve las paradas de banda y de puerta;
      - casi no podía fallar, porque se eligieron justo los tipos con los jugadores ya lentos antes de la
        ventana, y «la mayoría» está cerca de la proporción de `D` (el 44,8 % de los frames de la DFL con
        los que se entrenó el modelo);
      - la capa se aplicaría también a banda y puerta sin que nada mirara esos huecos.
    - **Lo que no comprueba:** que el hueco empiece justo en la parada. El modelo llega tarde al instante
      (entrada anterior de Ismael), así que solo dice si el hueco es sobre todo `D`. **[sin verificar]**
      Con lo que hay, la precisión del inicio no se puede medir: la DFL tapa el balón a partir de sus
      propias etiquetas de `D`, y medirla ahí sería circular (`docs/PLAN_ENTREGA.md` §4, «El `D` en la
      DFL tiene un límite»).
- **Si algo no pasa,** la capa se queda fuera. Con esta salida no se reajusta ningún número: ni los topes
  (180 s, 5 s, 60 s), ni los umbrales (5 m/s, la mitad, el 50 %, el doble, el punto medio), ni los
  desplazamientos.
- **El script imprime la regla aplicada** (las líneas «regla: … -> la capa entra»). Si lo impreso y este
  texto no cuadran, manda este texto. Que el código aplica este texto se comprueba en el repo, en la
  sección 9 de `validation/scripts/comprobar_balon_muerto.py`, con la apertura de ficheros prohibida:
  - **la regla en sus umbrales exactos:** `goal_rule` y `gap_rule` justo en cada límite y un poco por
    debajo, dónde miran los bordes (desde 1 s dentro y durante 5 s), el placebo que no pisa anclas y el
    modelo de Ana contado solo donde opina;
  - **`measure` con un partido inventado y doce variantes,** cada una con su resultado esperado: el
    partido normal (entran las dos capas, con sus recuentos exactos), un gol falso (falla el tramo
    entero), una ventana `GOALS` que acaba antes del gol y un saque que empieza tarde (falla el borde, no
    el tramo entero), sin balón en los tramos o en el control (no deciden), el balón siempre lento (el
    placebo no tiene potencia), sin goles, juego en el control (el control falla y no entra ninguna),
    jugadores corriendo en el control (los tramos de gol a saque lo completan), jugadores corriendo en
    los huecos (no pasa el modelo de Ana), hueco antes de solo 2 de 8 ventanas (no llega a la
    cobertura) y sin balón 45 s de cada minuto (no gana al placebo).

  Se comprobó rompiendo la regla a propósito, condición a condición (32 roturas, entre ellas las 24 que
  probó la segunda revisión): todas hacen fallar alguna prueba. El script de esas roturas no está en el
  repo **[sin verificar en el repo]**; las pruebas que las detectan, sí.
- **Descriptivo, no decide:** el desglose por tipo, la duración de los huecos, la velocidad de los
  jugadores, el modelo de Ana en lo anclado, en los primeros 5 s de los huecos y en cada grupo (córner y
  falta; banda y saque de puerta), y el recuento de equipos del Smart Tagging que coinciden con los
  nombres del ATD (para la capa del equipo que reanuda).
- **De dónde sale cada número.** Ninguno sale de la GT ni de la salida de este script. Los 5 s se
  eligieron con un agregado del partido medido antes:
  - 5 m/s: se fija aquí; el suavizado de 1 s es el de `agregados_balon_reinicios.py`;
  - 5 s de hueco: el umbral de los huecos largos del perfil del ATD (`2026-11-14_perfil_atd.md`);
  - 60 s: una parada antes de un saque de banda, un córner o un saque de puerta suele durar menos de un
    minuto **[sin verificar]**. Las faltas con barrera o tarjeta pueden pasar de 60 s: esas quedan como
    `hueco largo`, sin puntuar, y la capa es más conservadora;
  - la mitad, el doble, el punto medio y el 50 %: se fijan aquí;
  - los desplazamientos de 4, 6 y 8 minutos: los tramos de gol a saque duran 3 minutos como mucho, así
    que desplazados no se pisan consigo mismos.

Resultado de `validation/partido/agregados_dead_ball.py` (ejecutado por Manuel el 15/11, con la regla ya en
GitHub en `e677893`; la salida, tal cual, en `validation/resultados/2026-11-15_agregados_dead_ball.md`):
- **[medido] De gol a saque:** 4 goles y 4 saques tras gol, pero no ancla ninguno. Las ventanas `GOALS`
  duran 169 s de mediana.
- **[medido] El control de la prueba del balón falla:** en el tramo antes del saque de la 2ª parte, que es
  `D`, el balón visto va deprisa el 46,7 % del tiempo, frente al 50,5 % del partido entero.
- **[medido] El hueco antes de cada reinicio:**
  - 53 ventanas: hueco 28 (52,8 %), balón visto 23, hueco largo 0 y reinicio dentro 2;
  - por tipo, con hueco: banda 13 de 26, córner 11 de 12, saque de puerta 2 de 10 y falta 2 de 5;
  - placebo: 65 de 279 inicios (23,3 %);
  - modelo de Ana: `D` en el 47,4 % del partido, el 94,6 % del control (solo el tramo antes del saque,
    porque gol a saque no entra) y el 84,5 % de los huecos; punto medio, 71,0 %.
- **[medido] El `Team` de los `SET PIECES`:** 27 lo traen, y los 27 coinciden con un nombre de los
  metadatos del ATD (16 el local y 11 el visitante).

Decisión según la regla, sin cambiarla:
- **De gol a saque no entra:** no ancla ningún gol, y además el control no pasa. Queda programada y probada
  (`goal_to_kickoff` y `goal_to_kickoff_mask`), fuera de `dead_mask`.
- **El hueco antes de cada reinicio entra en `evidence`:** `GAP_SCORE` de 1 por frame en la columna `D`,
  sin ajustar, en las mismas ventanas que se midieron (las que empiezan en un tramo evaluado). La escala la
  ajusta David con los costes del decodificador.
- **Desde aquí la entrega usa el Smart Tagging** (a través de `dead_ball.evidence`). El aviso de abajo para
  Ismael (`pipeline.py` no lo pide en `games.require`) pasa a importar, y el documento técnico lo tiene que
  decir.

Lo que la regla no preveía (no cambia la decisión):
- **[inferencia] Las ventanas `GOALS` parecen cubrir la parada entera hasta el saque,** no acabar con el
  balón en la portería. La suposición (a) falla, pero de la forma que deja la capa sin tramos, no de la
  que fuerza `D` en juego. Usar la propia ventana `GOALS` como `D` sería un candidato nuevo: se escribiría
  y se mediría antes de entrar. Con esta salida no se hace.
- **[medido] La prueba del balón deprisa no separa `D` de juego en este partido** (46,7 % frente a
  50,5 %). [inferencia] El balón del ATD no está quieto durante el `D`, o tiene ruido: cualquier capa que
  feche el `D` con la velocidad del balón tiene que contar con ello.
- **Los márgenes de la capa 4 son justos:** con 2 huecos menos, la cobertura bajaría al 49,1 %.
- **[medido, descriptivo] En los primeros 5 s de los huecos el modelo de Ana solo ve `D` en el 60,9 %,**
  por debajo del punto medio, frente al 84,5 % del hueco entero. [inferencia] O algunos huecos empiezan
  antes de la parada, o el modelo llega tarde al instante (entrada de Ismael). El inicio de la capa sigue
  **[sin verificar]**. La escala de `GAP_SCORE` la decide David con los costes del decodificador, o un
  criterio escrito antes de medir; nunca la ventana pública.
- **[medido] Por tipo, el hueco aparece sobre todo antes de los córners** (11 de 12) y casi nunca antes de los
  saques de puerta (2 de 10).
- **El `Team` coincide siempre con los nombres del ATD:** la capa del equipo que reanuda (27 reinicios:
  córner, saque de puerta y falta) se puede escribir. Queda pendiente.
- **[medido] La entrega regenerada** (Manuel, 15/11, con la rama en `8f6ca9f`:
  `python -m possession.pipeline --name equipo_dfronteras`; sha256 `9539ce42…cc17a`):
  - 0 frames con piezas en conflicto;
  - `D` en 71.625 de los 158.857 frames evaluados (45,1 %), 113 paradas y 215 posesiones, frente al 44,4 %,
    114 y 219 de `equipo_v2`: dentro de la banda fijada para la entrega (`D` entre el 15 y el 60 %, 250
    paradas como mucho);
  - `validate_submission.py`: válida, y ninguna `X` en frames evaluados;
  - ventana pública, solo para ver que no está rota (no elige ni mide la mejora): `spellF1` 0,658 y
    `macroF1` 0,851, con 14 posesiones frente a las 17 de la GT.

Abierto:
- **Dos ficheros más, además de `dead_ball.py`, los dos de esta pieza:** las pruebas de las capas con un
  Smart Tagging inventado y de la regla con un partido inventado (secciones 7, 8 y 9 de
  `validation/scripts/comprobar_balon_muerto.py`) y `validation/partido/agregados_dead_ball.py`. Las dos
  filas de `validation/README.md` que los describen se tocan solo para eso.
- **La salida de los tres agregados de arriba,** tal cual, está en
  `validation/resultados/2026-11-14_agregados_balon_muerto.md`.
- **Una PR por medida:** las capas que se miden en la misma ejecución del script (gol a saque y la capa 4)
  van en la misma PR, cada una con sus agregados. Una capa que no pasa no entra en `evidence`.
- **Aviso para Ismael:** `possession/pipeline.py` no pide el Smart Tagging en `games.require`. Si falta,
  el error sale de `ET.parse` y se entiende peor.
- **La capa 4 se midió con la limpieza del balón v0 (`ball.clean`, que lo deja igual).** Si la entrega
  pasa a `clean_v1` de Antonio, que quita detecciones aisladas, los huecos pueden alargarse: habría que
  volver a ejecutar `agregados_dead_ball.py` con la misma regla. La salida dice con qué limpieza se midió.
- **Las paradas tras un gol se quedan sin capa de esta pieza:** de gol a saque no ancla, y la capa 4 no
  mira los saques iniciales (la regla se fijó así). Ahí solo opina el modelo de Ana. Meter los saques tras
  gol en la capa 4 sería un candidato nuevo, que se escribe y se mide antes de entrar.

### 2026-11-15 · decodificador · costes, duraciones mínimas y poda (candidatos, antes de medir)

Quién: David (`possession/temporal.py`), con Claude. Escrito antes de ejecutar el harness con B5 en `main`
(`d671f44`): ningún número de abajo se ha mirado al escribirlo.

Qué hay en `main`: Viterbi sobre {`H`, `A`, `D`} con `switch`, `to_dead` y `from_dead` a 25, sin ajustar,
encima de B5 (`aprendida.evidence_b5`). El α de B5 se eligió con el coste 25.

**Lo que el harness puede medir y lo que no** [inferencia, por construcción del harness]:
- Con el `D` oráculo, `D` solo está permitido donde las etiquetas dicen `D`, y `H` y `A` solo donde no. Todos
  los caminos posibles tienen los mismos cambios hacia y desde `D`, así que **`to_dead` y `from_dead` no
  cambian nada en el harness**. Solo se mide `switch` (`H` ↔ `A`).
- Por lo mismo, **la duración mínima del `D` no se mide en el harness.** Se escribe como garantía para el
  partido (el criterio del `D` del 13/11 pide que ninguna racha de `D` ni de juego vivo quede por debajo de
  un mínimo) y se comprueba con evidencia inventada (comprobaciones de abajo). Si se quieren en
  `validation/scripts/prueba_pipeline.py`, lo decide Ismael, que es su dueño.
- `to_dead` y `from_dead` se quedan en 25. Ajustarlos pide el `D` propio, y con el balón tapado en los `D`
  de la DFL ese número no decide (plan §4).

**Candidatos** (las tres del plan, §3 «David»), todos encima de B5 y con el `D` oráculo:

| | qué | parámetros, fijados antes de medir |
|---|---|---|
| `main` | Viterbi, coste 25 | `{}` |
| (a) | Viterbi con otro coste de cambio | `switch` 12 y 50 (la mitad y el doble; `to_dead` y `from_dead`, 25) |
| (b) | Viterbi con duración mínima, como restricción dura dentro del Viterbi | ninguna racha de `H` o `A` de menos de 12 frames, ni de `D` de menos de 25; coste 25 |
| (c) | Viterbi de `main` y después poda | cada racha de `H` o `A` de menos de 12 frames pasa al otro equipo si tiene al lado una racha de ese equipo; coste 25 |

- **Por qué 12 frames (0,5 s) y no más:** la GT tiene posesiones reales de menos de 1 s (plan §3) y la
  convención «control» del harness exige 12 frames de control para cambiar. Un mínimo de 1 s o más quitaría
  posesiones reales. No sale de la ventana pública ni de la tabla de retrasos (D21).
- **Por qué 25 frames (1 s) para el `D`:** una parada real dura varios segundos, y un `D` que parpadea cuesta
  más que un `D` perdido (13/11). Sin ajustar: no se puede medir aquí.
- **Lo prohibido manda sobre el mínimo:** una racha que `allowed` obliga a cortar (por ejemplo, el juego vivo
  entre dos `D` del oráculo, o el tramo antes del saque) puede ser más corta. Si no, con el `D` oráculo
  habría tramos sin ningún camino posible.
- **La poda (c)** empieza siempre por la racha más corta (si empatan, la primera en el tiempo), la fusiona
  con sus vecinas y repite hasta que no queda ninguna por debajo del mínimo. Respeta `allowed`, y una racha
  de juego vivo entre dos `D` no se toca. Es T7 sin el ajuste de fronteras al toque, que pide anclas que el
  decodificador no tiene.
  - *Cambiado antes de medir (15/11):* la primera versión recorría las rachas una sola vez, en orden de
    tiempo. La comprobación 3 de abajo, con evidencia inventada, enseñó que rebotaba: al cambiar una racha
    corta, la siguiente podía volver a cambiar, y quedaban rachas cortas. No se había puntuado nada en el
    harness.

**Regla de lectura** (la del plan §4 y §5.8, sin cambios):
- se mide con `python validation/harness/puntuar.py --versiones <fichero> --eventos`, con los 7 partidos;
- un candidato entra si gana al control **y** a `main` con §5.8: 6 de 7 partidos o más, +0,03 o más con
  el intervalo por encima de cero, en «como el ATD» y «como el ATD, sin bloques», con las dos convenciones;
- si empata con `main`, se queda `main`. Si ganan varios y empatan entre sí, entra el más simple:
  (a), luego (c), luego (b);
- en (a), la fila «elegida dejando un partido fuera» se mira como descripción: si los pliegues no eligen
  siempre el mismo coste, el coste no está bien determinado;
- los eventos humanos (`--eventos`) son descriptivos. Se mira sobre todo si sube el acierto en las
  recuperaciones (B5 saca 70 frente a 84 de N1) sin hundir los duelos sin cambio.

Comprobaciones del instrumento, antes de medir:
1. (b) con mínimos de 1 frame y (c) con poda de 0 frames dan exactamente la salida de `main`;
2. (b) da el mejor camino que cumple las reglas: comparado con todos los caminos posibles, por fuerza bruta,
   en tramos cortos;
3. con evidencia inventada, (b) no deja ninguna racha por debajo del mínimo salvo las que obliga `allowed`,
   y (c) no deja ninguna posesión corta que se pueda podar.

Todas salen bien [medido, evidencia inventada, sin datos de ningún partido].

Resultado (15/11, `python validation/harness/puntuar.py --versiones
validation/harness/versiones/decodificador_2026-11-15.json --eventos`, huella `969922247863`, código
`d671f44` más `possession/temporal.py` de la rama `feat/decodificador`; 7 partidos, `D` oráculo) [medido]:

| etiquetas | balón | `main` | (a) 12 | (a) 50 | (b) | (c) |
|---|---|---|---|---|---|---|
| flag | como el ATD | 0,498 | −0,000 (4 de 7) | −0,004 (2 de 7) | +0,000 | +0,000 |
| flag | sin bloques | 0,512 | +0,000 (3 de 7) | −0,005 (2 de 7) | +0,000 | +0,000 |
| control | como el ATD | 0,728 | −0,017 (0 de 7) | +0,010 (7 de 7) | +0,000 | +0,000 |
| control | sin bloques | 0,748 | −0,015 (0 de 7) | +0,010 (7 de 7) | +0,000 | +0,000 |

(diferencias de `spellF1` frente a `main`; entre paréntesis, en cuántos partidos gana)

- **Los cuatro candidatos ganan al control y empatan con `main`** con §5.8. Ninguno llega a +0,03.
- **(a): el coste que conviene depende de la convención,** como el 14/11 con N1. Con el flag, 50 pierde un
  poco (intervalo entero por debajo de cero) y 12 empata; con las etiquetas de control, 50 gana un poco y 12
  pierde. La fila «elegida dejando un partido fuera» no da una elección estable entre convenciones. El 25 de
  `main` queda en medio.
- **(b) y (c) dan la salida de `main`** en las dos condiciones que votan (posesiones predichas iguales,
  diferencia +0,000). Solo cambian algo en «huecos y suavizado», sin voto: +0,001 y +0,002.
  [inferencia] Con B5 y coste 25 el Viterbi ya casi no deja posesiones de menos de 12 frames: para pagar dos
  cambios de 25 en menos de 12 frames, la evidencia tiene que dar más de 4 por frame a favor del otro equipo.
- **Eventos (descriptivo):** ningún candidato recupera las recuperaciones de B5 (70,3 frente a 84,1 del
  control, «como el ATD»). El coste 12 no las sube (69,2) y empeora los duelos sin cambio. [inferencia] Las
  recuperaciones que pierde B5 no son un problema del coste de cambio, sino de la evidencia.

Decisión y por qué: **se queda `main` (Viterbi, coste 25).** Es la regla escrita antes de medir: si un
candidato empata con `main`, se queda `main`. La entrega no cambia.
- `decode_min` y `decode_prune` se quedan en `possession/temporal.py` como opciones, fuera de la entrega
  (`pipeline.PIECES` sigue con `decode`). `decode_min` es la garantía de duración mínima del `D` que pide el
  criterio del 13/11, por si se usa con un `D` propio que parpadee. Eso no se puede medir en el harness.
  **Nota de la revisión (Ismael, 15/11):** no es una garantía completa. `decode_min` deja pasar la primera
  y la última racha de cada tramo y las que corta lo prohibido, y una racha corta la alarga hasta el mínimo
  en vez de quitarla. No está medida ni va en la entrega: el «ninguna racha por debajo del mínimo» del
  criterio del 13/11 sigue sin cumplirse en lo que se entrega.
- **Lo que queda abierto, para Ismael:** el decodificador solo podría mover más la nota en `to_dead` y
  `from_dead`, es decir, con el `D` propio, que el harness hoy no puede usar para decidir (plan §4).

Descartado: subir o bajar el coste de cambio (empata y el signo depende de la convención), y la poda y la
duración mínima como cambio de la entrega (empatan: dan lo mismo que `main`).

### 2026-11-15 · validación · dónde se pierde el `spellF1` (diagnóstico descriptivo)

Quién: David, con Claude, después de la entrada anterior.

Qué se probó: cuánto `spellF1` pierde cada fase. Se cambia una pieza cada vez por la respuesta de las
etiquetas. Es **descriptivo:** no se escribió antes de medir y no decide nada. Sirve para repartir el
trabajo que queda.

Cómo se midió: los 7 partidos de la DFL, con el balón «como el ATD» y las dos convenciones, el scorer
oficial (`puntuar.contar`) y el código `d671f44` más `possession/temporal.py` de `feat/decodificador`.
Script: `python validation/scripts/diagnostico_spell.py` (unos 3 minutos; solo la DFL). Las versiones:
- `main`: B5, coste 25 y `D` oráculo, lo que mide el harness;
- `main` con el `D` propio: el `D` lo pone `dead_state`, sin oráculo, con el balón tapado en los `D` (no
  decide; plan §4);
- equipo perfecto donde se ve el balón: +5 al equipo de la etiqueta en los frames con balón visible y 0 en
  el resto; coste 25 y `D` oráculo;
- equipo perfecto siempre: lo mismo en todos los frames de juego.

Resultado [medido]:

| versión | flag | control |
|---|---|---|
| equipo perfecto siempre (techo del decodificador) | 0,970 | 0,999 |
| equipo perfecto donde se ve el balón | 0,901 | 0,947 |
| `main` | 0,498 | 0,728 |
| `main` con el `D` propio | 0,416 | 0,616 |

Posesiones reales que `main` encuentra (IoU ≥ 0,5), por duración:

| duración | flag: reales | flag: encontradas | control: reales | control: encontradas |
|---|---|---|---|---|
| < 1 s | 384 | 2 % | 48 | 15 % |
| 1–2 s | 535 | 10 % | 111 | 25 % |
| 2–5 s | 934 | 27 % | 399 | 53 % |
| 5–10 s | 569 | 58 % | 437 | 76 % |
| ≥ 10 s | 639 | 86 % | 741 | 92 % |

Cambios de equipo en juego: 2.351 reales con el flag y 1.026 con el control. `main` predice 951.

Lectura [inferencia]:
- **El decodificador casi no pierde:** con una evidencia perfecta saca 0,97–1,00.
- **Los huecos del balón pierden poco:** entre 0,05 y 0,07, la diferencia entre «perfecto siempre» y
  «perfecto donde se ve».
- **La evidencia de equipo con el balón a la vista es la mayor pérdida:** 0,40 con el flag y 0,22 con el
  control. Sobre todo, cambios reales que no se ven (recuperaciones, posesiones de 2 a 5 s).
- **El `D` propio es la segunda:** entre 0,08 y 0,11, y en el harness va regalado.
  **Nota de la revisión (Ismael, 15/11):** ese número sale de `--d propio`, que no decide: el balón tapado
  en los `D` delata la etiqueta, así que la pérdida real puede ser mayor [inferencia].
- **Con el flag, casi todo lo que se pierde son posesiones de menos de 2 s** (919 reales, el 30 %). Si la
  GT del reto se parece al flag, ahí hay mucha nota. Ir a por ellas es cambiar la convención «exigir
  control» (decisión de Ismael del 12/11), no el código del decodificador.
  **Corrección de la revisión (Ismael, 15/11):** «casi todo» no sale de la tabla. Con sus porcentajes, las
  de menos de 2 s son alrededor del 46 % de las que no se encuentran (unas 858 de 1.868) y las de 2 a 5 s,
  el 36 % (unas 682). Lo que sí dice la tabla es que casi todas las de menos de 2 s se pierden (el 93 %).

Decisión: ninguna. Se pasa a Ismael para el reparto hasta el corte del lunes a las 14:00.

### 2026-11-14 · balón · corrección del paso 2 de la limpieza y recuento en el partido, escritos antes de ejecutarlo

Quién: Antonio Azuero

Qué se probó: **escrito antes de ejecutar el recuento en el partido y antes de la comprobación del
harness.** Sale de la revisión de Ismael de la PR 6: la limpieza entra fija, sin competir, si no empeora
(plan, §3 y §8). El harness no puede juzgarla, porque la DFL no tiene saltos falsos; la juzga el recuento
del partido.

> **Nota de la revisión (Ismael, 15/11):** lo de «entra fija, sin competir, si no empeora» sale del mensaje
> que se le pasó a Antonio tras revisar la PR 6. No estaba apuntado como decisión. Con el recuento ya
> hecho, encender la limpieza sigue sin decidir: `ball.clean` devuelve el balón tal cual.

- **Corrección de un fallo de `clean_v1`, no una variante nueva.** La limpieza sigue siendo una sola
  versión, con los mismos pasos y valores.
  - **El fallo (lo vio Ismael):** el paso 2 (rachas aisladas) se calculaba después de quitar los saltos
    del paso 1. Contaba como hueco el agujero que acababa de abrir el paso 1 y borraba balón bueno pegado
    a un pico. Ejemplo: con un hueco largo, 2 frames buenos, un pico de 1 frame y más balón bueno, se
    perdían 3 frames en vez de 1. En espejo, igual.
  - **El arreglo:** los pasos 1 y 2 se calculan los dos sobre el balón de entrada y se quitan juntos.
  - **Prueba:** `validation/scripts/prueba_limpieza.py`, con 62 comprobaciones sin datos del partido:
    los 36 casos de la PR 6, el caso del fallo en los dos sentidos y el recuento con un tracking
    inventado. Los 5 casos del fallo dan error con el `ball.py` de `main` y pasan con el arreglo.
    [medido, sintético]
- **Recuento en el partido:** `validation/partido/limpieza_balon.py`. Lo ejecuta Antonio en local y pega
  solo agregados. Cuenta en los frames evaluados, con las dos partes juntas:
  - **paso 1:** puntos que quita, y los pares de frames seguidos a más de 40 m/s del perfil, por clase. Un
    **tramo** son pares imposibles seguidos, del frame p (antes del primero) al q (después del último).
    Las clases son:
    - **pico:** dos pares o más, con el balón de p a q a 40 m/s o menos. El paso 1 quita todo su
      interior;
    - **excursión:** un tramo que no es pico y otro que empieza como mucho 25 frames (1 s) después, en el
      mismo tramo evaluado, con el balón de vuelta donde se le espera (40 m/s o menos de p del primero a
      q del segundo). El paso 1 no la toca;
    - **salto que se queda:** el resto;
  - **paso 2:** puntos y rachas que quita;
  - **paso 3:** huecos cortos tras los pasos 1 y 2, cuántos rellena y cuántos frames;
  - **en total:** los frames que cambian, en número y en % de los frames evaluados con balón;
  - **saltos imposibles entre dos puntos con balón seguidos**, haya un hueco en medio o no, antes y
    después de limpiar. Esta cuenta, y no la de pares, dice si se quitan saltos: al abrir un hueco
    desaparece un par, aunque el salto siga ahí;
  - **descriptivo:** los frames en que cambia el equipo del más cercano.
  - Las celdas de 1 a 4 casos salen como «< 5». Antes de contar, el script comprueba que reproduce
    `clean_v1` exactamente.
- **Comprobación en el harness:** `validation/harness/versiones/limpieza_balon_2026-11-14.json`, con
  `{}` (lo de `main`: B5 sin limpieza) y la limpieza corregida.
  - **No empeora** si, en ninguna de las cuatro combinaciones que votan (dos condiciones del balón por dos
    convenciones), pierde frente a `main` por 0,03 o más.
  - Si empeora, no se propone y se avisa a Ismael.

Cómo se lee el recuento (fijado antes de ejecutarlo):

- **0, controles:** 158.857 frames evaluados, 94.214 con balón y 216 pares a más de 40 m/s, como en el
  perfil del ATD. Si alguno no cuadra, no se lee nada más y se revisa el script.
- **Sale como se esperaba si se cumplen las dos condiciones:**
  - (a) los saltos imposibles entre puntos con balón seguidos bajan a la mitad o menos;
  - (b) los frames que cambian son el 1 % o menos de los frames evaluados con balón, unos 940 como mucho.

  Entonces se propone en la PR que `clean` pase a ser `clean_v1`. Eso cambia la entrega: la regenera y la
  valida Ismael.
- **Si falla (a):** la regla no quita la mayoría de los saltos, que serían sobre todo saltos que se quedan
  o excursiones. `clean_v1` no pasa a la entrega en esta PR. Una regla para esos saltos sería una variante
  nueva, con su propia entrada antes de medir.
- **Si falla (b):** la limpieza toca mucho más de lo que promete. No pasa a la entrega y se revisa por qué.
- **No deciden:** las clases de los pares, los pasos 2 y 3 y el equipo más cercano, que son descriptivos.
- **Lo que espero, sin mucha seguridad** [inferencia]: que se cumplan las dos. Con el balón del ATD
  suavizado unos 25 frames, un pico de un solo frame debería verse amortiguado, así que una parte de los
  216 pares podrían ser saltos que se quedan, que la regla no quita. Por eso (a) no está garantizada.
- **Después de ver los números no se retoca ningún umbral.**

Resultado (añadido después de ejecutarlo; lo de arriba no ha cambiado):

- **Harness, antes de ejecutar el recuento:**
  `python validation/harness/puntuar.py --versiones validation/harness/versiones/limpieza_balon_2026-11-14.json`
  (huella 0163fe4b792a; código b0625fa de la rama `feat/limpieza-balon`, la PR que sigue a la 6). 7
  partidos, `D` oráculo, bootstrap de 1.000 remuestreos. En las condiciones que votan: [medido]

  | etiquetas | balón | control | `main` (B5 sin limpieza) | limpieza v1 corregida | limpieza − `main` |
  |---|---|---|---|---|---|
  | flag | como el ATD | 0,406 | 0,498 (+0,093, 7 de 7) | 0,498 (+0,093, 7 de 7) | +0,000 [+0,000 a +0,000], 0 de 7 |
  | flag | como el ATD, sin bloques | 0,435 | 0,512 (+0,078, 7 de 7) | 0,512 (+0,077, 7 de 7) | −0,000 [−0,000 a +0,000], 0 de 7 |
  | control | como el ATD | 0,464 | 0,728 (+0,265, 7 de 7) | 0,728 (+0,265, 7 de 7) | +0,000 [+0,000 a +0,000], 0 de 7 |
  | control | como el ATD, sin bloques | 0,494 | 0,748 (+0,254, 7 de 7) | 0,748 (+0,254, 7 de 7) | +0,000 [+0,000 a +0,000], 0 de 7 |

  Entre paréntesis, la diferencia con el control y en cuántos partidos gana. **No empeora.**
- **Recuento en el partido** (`python validation/partido/limpieza_balon.py`; lo ejecutó Antonio en local,
  4 s; solo agregados): [medido]

  | qué | cuánto |
  |---|---|
  | controles: frames evaluados, con balón, pares a más de 40 m/s | 158.857, 94.214 y 216: cuadran |
  | paso 1: puntos quitados | 201 |
  | pares por clase (pares / tramos): pico | 0 / 0 |
  | excursión | 95 / 6 |
  | salto que se queda | 121 / 9 |
  | paso 2: puntos quitados | 0 |
  | paso 3: huecos cortos tras los pasos 1 y 2, rellenos y frames | 22, < 5 y 14 |
  | frames que cambian | 215 (0,23 % de los frames evaluados con balón) |
  | saltos imposibles entre puntos con balón seguidos | 227 antes y 26 después |
  | pares a más de 40 m/s después | 0 |

- **A la letra, la regla se cumple:** los controles cuadran, (a) los saltos bajan de 227 a 26 y (b) cambia
  el 0,23 % de los frames. [medido]
- **En sustancia, (a) no midió lo que pretendía y es el caso de «Si falla (a)»:** la regla decía que esa
  cuenta «dice si se quitan saltos», y los saltos no se quitan. Son saltos que se quedan y excursiones, como
  avisaba «Lo que espero». [inferencia, cuadra exacto con los recuentos] El detalle:
  - **Los 216 pares no son picos.** Son 15 tramos largos de pares seguidos, de unos 14 pares de media: 6
    tramos que forman 3 excursiones de menos de 1 s y 9 saltos que se quedan. Parece un salto grande del
    balón (más de 40 m) suavizado en unos 25 frames. [Nota de la revisión, 15/11: «más de 40 m» está sin
    verificar; del recuento solo salen más de unos 23 m, y los 25 frames son del perfil.]
  - **El paso 1 quita el interior de los 15 tramos:** 201 = 216 − 15 puntos, los del tránsito a más de
    40 m/s.
  - **Los 15 saltos siguen ahí,** entre los dos extremos de cada tramo: 26 = 15 + los 11 saltos a través de
    un hueco que ya había antes. El balón sigue apareciendo en el sitio equivocado al final de cada salto
    que se queda y durante cada excursión.
  - **(a) baja tanto porque antes cada tramo contaba unas 14 veces y después cuenta una.** Al escribir la
    regla supuse que los saltos serían cortos. Contados por tramo, siguen los 15 de 15. La regla no se
    retoca; se apunta que su (a) no sirvió para lo que se escribió.
  - Las definiciones de arriba dicen que el paso 1 «no toca» las excursiones. Es inexacto cuando el tramo
    tiene dos pares o más: también les quita el tránsito, aunque el salto queda.
  - Los 215 frames con otro equipo como el más cercano son casi todos frames que se quedan sin balón: esa
    línea no informa.
- **Nota de la revisión (Ismael, 15/11):** (a) no falló (227 → 26). Estaba mal definida: antes cada tramo
  cuenta unas 14 veces y después una. La regla se cumple a la letra, y su consecuencia no se aplica por eso.
  Si la limpieza se enciende, será por decisión de Ismael, no porque haya pasado la regla.
- **Las pruebas** (después de la revisión de esta PR): `prueba_limpieza.py` tiene 65 comprobaciones. Además
  de las 62 de arriba, prueba un salto y una excursión en la frontera entre dos tramos evaluados. Arriba
  dice «los 36 casos de la PR 6»: eran 38, con los que se añadieron al pasarlos al repo. [medido, sintético]
- **El paso 2 no hace nada en el partido** (0 puntos), como decía el perfil (menos de 5 rachas cortas). El
  paso 3 rellena 14 frames y deja sin rellenar los huecos de los 15 tramos, porque el salto que los cruza
  es imposible. Es lo que pide la regla. [medido]

Decisión y por qué:
- **No se propone el cambio de `clean` como «salió como se esperaba».** A la letra cumple; en sustancia,
  no quita los saltos.
- **Lo decide Ismael, con lo que sí aguanta:**
  - no empeora en el harness (±0,000);
  - en el partido toca el 0,23 % de los frames con balón;
  - quita los 201 frames de tránsito a más de 40 m/s, posiciones en las que el balón no puede estar;
  - no arregla los 15 saltos grandes (3 excursiones y 9 saltos que se quedan).
- **Si se cambia, no va en esta PR.** B5 se entrenó con `ball.clean` tal cual, y
  `validation/scripts/prueba_aprendida.py` lo comprueba. Cambiar `clean` obliga a reentrenarla con
  `validation/apuesta_b/entrenar.py`, que escribe en `possession/aprendida.py`, la pieza de Ismael.
  **Nota de la revisión (Ismael, 15/11):** encenderla obliga además a volver a ejecutar
  `validation/partido/agregados_dead_ball.py` (la capa del hueco de `dead_ball`, PR 8, se midió con
  `ball.clean` tal cual), a repetir la medida de B5 en el harness una vez reentrenada (sus criterios y los
  costes van en su escala) y a regenerar y reproducir la entrega.
- **Una regla para los 15 saltos** sería una variante nueva, con su propia entrada antes de medir. Afecta a
  muy pocos frames del partido, así que solo merece la pena si sobra tiempo antes del corte. [inferencia]

Descartado:
- **Retocar los umbrales o la definición de (a) después de ver el recuento:** la regla estaba fijada antes.
- **Cambiar `clean` en esta PR:** rompería `prueba_aprendida.py` y dejaría a B5 con coeficientes
  entrenados sobre otro balón.

### 2026-11-15 · infraestructura · el corte pasa del lunes 16 a las 14:00 al martes 17

Quién: Ismael

Qué se probó: nada. Es una decisión de calendario, tomada tras repartir las tareas de la revisión externa
del 15/11 (`docs/PLAN_ENTREGA.md` §3 y `docs/revision_externa_2026-11-15.md`).

Cómo se midió (dataset, nº de partidos/posesiones, métrica): no aplica.

Resultado: no aplica.

Decisión y por qué:
- **El corte pasa al martes 17.** Ismael decide que hay margen hasta el martes para esas tareas.
- **La hora es provisional, las 12:00,** hasta que Ismael la confirme. La entrega se cierra a las 23:59 CET
  y después del corte hay que congelar, reproducir, hacer público el repo, validar el fichero y enviarlo.
- **Lo que cuesta:** el congelado y la reproducción en una máquina limpia ya no caben el lunes por la noche.
  Para no hacerlo por primera vez el martes, el lunes por la noche se ensaya con lo que haya en `main`.
- **Lo que no cambia:** lo que no haya ganado en el harness antes del corte no entra, y el documento técnico
  se escribe desde el lunes.

Descartado:
- **Mantener el lunes a las 14:00.**


### 2026-11-15 · infraestructura · versiones de la entrega fijadas: numpy 2.5.4 y Python 3.13, en un fichero aparte

Quién: Ismael, con la propuesta de Claude. Le planteó las dos opciones y respondió «adelante con todo». Es
la tarea 1 de su bloque (`docs/PLAN_ENTREGA.md` §3).

Qué se decidió:
- **`requirements-entrega.txt`** fija numpy 2.5.4, pandas 3.1.1 y las dos dependencias de pandas, con
  **Python 3.13** (probado con 3.13.9). Lleva dentro el comando para crear el entorno y regenerar.
- **`requirements.txt` no se toca:** es el oficial de Metrica.

Por qué:
- **Con estas versiones salió `equipo_v3`** en la máquina de Ismael, así que no hay que regenerar para
  cambiar de versión.
- **numpy 2.5.4 pide Python 3.12 o más** (PyPI). Para Python 3.11 habría que bajar a numpy 2.4.6 y volver a
  comprobar la huella. Las normas piden dependencias fijadas y el mismo fichero (`SUBMISSION.md` §2,
  `RULES.md`), no una versión de Python concreta.
- **`requirements.txt` promete Python 3.8 y 3.11** para el scorer oficial. Fijar ahí numpy 2.5.4 lo
  rompería para quien lo instale con esas versiones.
- **El pipeline solo importa numpy.** pandas es del validador y del scorer oficiales.

Comprobado [medido, sin datos del partido]:
- **Entorno limpio** en `C:\Users\34656\.venvs\mtah2027-entrega`, con `py -3.13 -m venv` y
  `pip install -r requirements-entrega.txt`:
  - `pip freeze` coincide con el fichero;
  - `validation/scripts/prueba_pipeline.py` sale en verde;
  - el validador oficial da por válido `baseline_smooth50.csv`.
- **El CSV del pipeline sobre el partido inventado** de `prueba_pipeline.py` sale con el mismo sha256 en el
  entorno de trabajo y en el limpio (`2621a1e2…d9fd`).

Resultado (15/11, ejecutado por Ismael con `main` en `988ce88`) [medido]: **el entorno limpio reproduce la
entrega.**
- Con Python 3.13.9 y numpy 2.5.4, `equipo_v3_limpio` sale con el sha256 `9539ce42…cc17a`, el de
  `equipo_v3`, y el validador oficial lo da por válido.
- El lector del ATD (`d6bd128`) no se salta nada: 199.319 líneas leídas y válidas; 0 vacías, mal formadas,
  fuera de rango o repetidas; 0 frames sin línea.
  - Como estaba previsto (tarea 2 del plan), desde ahora cualquiera de esos recuentos distinto de 0 es un
    error y no se genera la entrega (`pipeline.check_atd`).
- **No hay rachas cortas:** ninguna posesión, racha de juego ni parada de menos de 12 o de 25 frames en
  ninguno de los dos tramos. En la entrega se cumple la condición del criterio del 13/11 de que no haya
  rachas de `D` ni de juego de menos de 25 frames.

Falta:
- **Repetir la huella en el ensayo del lunes por la noche,** con lo que haya entrado en `main` hasta
  entonces.
- **La versión de numpy de la máquina Linux** que reprodujo `equipo_v2` [sin verificar]. Si era otra, la
  huella ya aguanta un cambio de versión.
- **El nombre del CSV:** `<NOMBRE_EQUIPO>` sigue sin confirmar. Hasta entonces, el comando lo recibe con
  `--name` y el nombre por defecto sigue siendo `equipo_v0`.

Descartado:
- **numpy 2.4.6 para poder usar Python 3.11:** habría que regenerar y comprobar otra vez, y las normas no lo
  piden.
- **Fijar las versiones en `requirements.txt`:** es oficial y su comentario promete 3.8 y 3.11.


### 2026-11-15 · candidatos · apuesta B: una sola ronda de reentrenamiento de B5 (candidatos, antes de medir)

Quién: tarea 4 de Ismael en el plan (`docs/PLAN_ENTREGA.md` §3), que sale de la propuesta P4 de la revisión
externa (`docs/revision_externa_2026-11-15.md`). Ismael la arrancó por la sesión de revisión («pásaselo tú a
las dos sesiones»). El borrador es de la sesión de integración; Claude lo completa, entrena y mide. La regla
tiene commit antes de entrenar.

Por qué:
- **Dónde se pierde:** con B5, sobre todo en la evidencia de equipo con el balón a la vista, en las
  recuperaciones y en las posesiones de 2 a 5 s (diagnóstico de David, entrada del 15/11).
- **Por qué B5 llega tarde a los cambios** [inferencia de la revisión]: pesa mucho las ventanas de 151
  frames y se entrenó con una pérdida por frame. Está hecha para acertar el equipo, no el instante del
  cambio.
- **Lo que ya empató:** dos añadidos encima de B5 con una escala fija (anexos A.3 y A.5 de la revisión, sin
  repetir aquí). Lo que falta probar es cambiar lo que aprende el modelo. La revisión espera poco: de −0,01
  a +0,02.

Candidatos. Los tres salen de `validation/apuesta_b/entrenar.py` y son iguales que B5 en todo lo demás:
- las mismas filas de entrenamiento: frames vivos en los que el flag y el control coinciden, uno de cada 5,
  con el balón «como el ATD» y `ball.clean`;
- la misma regresión (`LAMBDA`, `ITERACIONES` y `CIFRAS`) y los mismos pliegues;
- la misma puntuación que B5: −α·|z| al equipo que no da el modelo, más el +1 de N1 donde se ve el balón;
- la misma elección de α: rejilla de 1/8 a 8, con la pieza de `D` de `main` dentro y sin oráculo. Si
  empatan, la más pequeña.

Lo único que cambia en cada uno:
- **B6, B5 sin las ventanas de 151 frames:** los rasgos de B2 menos los cinco de «ventana 151». Quedan 25.
- **B7, B5 con peso 5 cerca de los cambios:** los rasgos de B2. Cada fila de entrenamiento pesa 5 si está a
  50 frames o menos (±2 s) de un cambio de equipo, y 1 si no.
  - Un cambio de equipo es un frame cuya etiqueta y la del frame anterior son `H` o `A` y distintas, **en
    el control**, dentro del mismo tramo. Un cambio a través de una parada no cuenta.
  - **Por qué el control y no el flag:** cerca de un cambio que solo está en el flag (un toque breve del
    rival), las filas que se entrenan son todas del equipo que retiene, porque el toque no se entrena.
    Pesarlas enseñaría a aguantar más. Contadas antes de entrenar: 9.847 filas así, frente a 18.846 cerca
    de un cambio del control (que también está en el flag). Elegido antes de ver ningún resultado.
  - La regresión pondera cada fila por su peso, en el gradiente y en la hessiana, con la misma L2.
- **B8, B5 con el evento de toque:** los rasgos de B2 más dos, el evento de toque con signo en ventanas
  centradas de 13 y de 51 frames. El evento sigue el anexo A.4 de la revisión, reescrito con lo que trae un
  `Tracking` (el balón tal como llega, ya limpio, sin suavizarlo otra vez). Se calcula por tramo, sin
  cruzar sus bordes:
  - **cambio de velocidad en t:** la norma de la diferencia entre la velocidad media del balón del frame
    t+12 al t+25 y la del t−25 al t−12. No hay valor si falta el balón en alguno de esos cuatro frames o si
    alguno cae fuera del tramo;
  - **evento:** un t con un cambio de 3 m/s o más que es el máximo en ±12 frames. Si hay empate, cuenta el
    primero;
  - **signo:** +1 si el jugador más cercano al balón en t es del local y está a 3 m o menos; −1 si es del
    visitante; 0 si no hay nadie a 3 m. Si los dos están a la misma distancia, cuenta el local;
  - **rasgo:** la media centrada del signo en 13 y en 51 frames (`aprendida.media_centrada`), como los
    rasgos del balón de B2.

Comprobaciones del instrumento, antes de leer nada:
- **Los coeficientes de B1 a B5 no cambian al reentrenar,** así que la entrega no cambia. Además, las α de
  B1 a B5 son las del 14/11.
- **Las columnas:** B7 con peso 1 en todas las filas da los pesos de B2. Las primeras 30 columnas de B8 son
  los rasgos de B2, y las de B6 son las de B2 sin las cinco de 151.
- **El detector, con un balón inventado:**
  - un cambio brusco de velocidad, suavizado con una media de 25 frames, da un solo evento a ±2 frames de
    su sitio;
  - un balón a velocidad constante no da ninguno;
  - un jugador a 2 m da el signo de su equipo, y uno a 4 m da 0.
- **El detector, en la DFL, frente al anexo A.4:** eventos por minuto de juego.
  - Tiene que quedar a ±20 % de lo que mide la revisión: 24,2 «como el ATD» (de 19,4 a 29,0) y 27,6 «sin
    bloques» (de 22,1 a 33,1).
  - A.4 es una medida de fuera que nadie ha repetido. Si no cuadra, se para y se dice. No se ajusta el
    detector.

Cómo se mide (los tres frente a `main`, que es B5):
1. **Harness con el `D` oráculo:** `validation/harness/puntuar.py --eventos`, con
   `validation/harness/versiones/apuesta_b_ronda.json`, cada candidato con `dejar_fuera`. Regla de §5.8
   frente a `main` y frente al control, en las dos condiciones que votan y con las dos convenciones.
2. **Eventos humanos, en la misma ejecución:** en las dos condiciones que votan, se lee la estimación de la
   diferencia frente a `main`, no el intervalo.
   - La de las recuperaciones tiene que ser mayor que cero (son 195 puntos: una recuperación vale 0,5
     puntos).
   - La de los duelos sin cambio no puede bajar de −5 puntos.
   - Con B5, el acierto es del 70 y el 73 % en las recuperaciones, y del 75 y el 74 % en los duelos sin
     cambio.
3. **Criterios 2 y 3 de B5,** con `validation/apuesta_b/d_propio.py --versiones` y el mismo fichero. La
   referencia es la fila de `main` (`{}`) de esa misma ejecución, que tiene que repetir 629 / 628 paradas
   vistas con el balón tapado y 545 con el balón a la vista. Si no las repite, algo del `D` cambió en
   `main`: se para y se dice.
   - **Con el balón tapado:**
     - al menos tantas paradas vistas como `main`;
     - la precisión del `D` a 2 puntos o menos de la de `main`;
     - un `spellF1` con el `D` propio no por debajo del de `main` en las cuatro celdas.
   - **Con el balón a la vista en los `D`:** las paradas vistas no más de 1 punto por debajo de las de
     `main`.

Regla de lectura, fijada antes de medir:
- **Entra** el candidato que cumple 1, 2 y 3. Si cumplen varios, el más simple: B6 antes que B7, y B7 antes
  que B8.
  - El cambio de `pipeline.PIECES` va en un último commit aparte.
  - Ismael tiene un sí permanente para la apuesta B, pero este arranque no da permiso nuevo para `main`.
    Lo sube la sesión de integración.
- **Si ninguno cumple los tres, es un empate y se cierra la evidencia de equipo.**
  - «Empate» incluye perder.
  - Un candidato que mejora en los eventos pero no gana a `main` con §5.8 no entra.
  - Es la regla de parada: una sola ronda, sin segunda vuelta ni combinaciones. Se apunta aquí.
- **Nada de lo medido cambia los candidatos:** ni el peso 5, ni los ±2 s, ni la convención de los cambios,
  ni las ventanas, ni los umbrales del evento.

De paso, solo para mirar: **un slot duplicado cuenta doble en los núcleos de B5** (`possession/aprendida.py`,
`_rasgos_balon`).
- La DFL no tiene slots duplicados, así que el harness no lo ve.
- Arreglarlo cambiaría los rasgos de B5 y la entrega: sería un cuarto candidato, y la regla de parada no lo
  deja. No entra en esta ronda.
- Cuánto pasa en el partido solo lo dice un agregado de `validation/partido/` que ejecute una persona.

Resultado (15/11; `validation/resultados/2026-11-14_apuesta_b.md` §11, código `1142773`) [medido]:
- **Instrumento:**
  - los coeficientes de B1 a B5 no cambian;
  - el detector repite el anexo A.4 (24,2 / 27,6 / 31,8 eventos por minuto);
  - la fila de `main` de `d_propio.py` repite 629 / 628 y 545.
- **1. Harness con §5.8 frente a `main`: empatan los tres.** El que más se acerca es B7: +0,012 y +0,015
  con el flag (6 de 7), y −0,005 y +0,001 con el control. B6 pierde con el control (−0,017 y −0,013), y B8
  da +0,000 con el flag.
- **2. Eventos:**
  - B7 sube las recuperaciones +2,6 y los duelos con cambio +5,2 / +4,4, con −2,8 en los duelos sin
    cambio. Cumple.
  - B8 cumple por poco: +1,0 / +1,5 en las recuperaciones.
  - B6 no cumple: bajan las recuperaciones.
- **3. `D` propio: no lo cumple ninguno.**
  - B6: `spellF1` con el control 0,605 y 0,634, frente a 0,616 y 0,642.
  - B7: 627 paradas frente a 628 «sin bloques».
  - B8: `spellF1` con el flag 0,415 y 0,431, frente a 0,416 y 0,433.

Decisión y por qué: **ninguno cumple los tres criterios: es un empate, y por la regla de parada se cierra
la evidencia de equipo.** B5 sigue en la entrega, y `pipeline.PIECES` no cambia. No hay segunda vuelta ni
combinaciones.
- B7 aprende algo del instante del cambio: mejora los eventos y gana un poco con el flag. Pero no llega al
  +0,03 y no se mueve con el control.
- Esto confirma lo que esperaba la revisión (de −0,01 a +0,02).

Descartado: B6, B7 y B8. Y arreglar el slot duplicado de los núcleos: sería un cuarto candidato.
`validation/partido/slots_duplicados.py` dice cuánto pasa en el partido, si Ismael lo ejecuta.

### 2026-11-15 · balón · el balón del ATD llega unos 4 frames tarde: la corrección queda escrita y apagada

Quién: Antonio Azuero. Encenderla o no lo decide Ismael.

Qué se probó: la tarea 1 de Antonio en `docs/PLAN_ENTREGA.md` §3 (P1 de la revisión externa): si el balón
del ATD, suavizado unos 25 frames, llega tarde respecto a los jugadores. Si fuera una media hacia atrás,
serían unos 12 frames, y eso costaría más que cualquier mejora medida.
- **La medida** (`validation/retraso_balon/`, con su bitácora): en las rachas en que el mismo slot está a
  1,5 m o menos del balón durante 1 s o más, la correlación entre la velocidad del balón y la del jugador,
  para cada desfase de −25 a +25 frames. Es relativa al jugador.
- **v1:** el desfase del máximo de esa curva.
- **v2:** la curva entera, comparada con una familia de curvas de la DFL con retrasos conocidos (de −18 a
  +18). Se diseñó después de ver las curvas de la v1 en la DFL, nunca el partido.
- Las reglas de las dos se escribieron antes de medir. La de la v2 se subió antes de calibrar (`3e92064`).

Cómo se midió:
- **Calibración:** en los 7 partidos de la DFL, con el tracking del harness y retrasos conocidos. La v2,
  dejando un partido fuera, con retrasos de −9 a +12; los de −9, −3, +3 y +9 no se habían mirado antes.
- **Partido:** `validation/partido/retraso_balon.py`, ejecutado por Antonio en local, solo agregados. 572
  rachas, 29.183 frames.
- **Coste, descriptivo:** el harness con el balón de la DFL retrasado 4 frames frente a `main`
  (`validation/harness/versiones/retraso_balon_2026-11-15.json`).

Resultado [medido]:
- **La v1 no pasa la calibración:** con el balón centrado da −7 (se esperaba 0), y adelantado 6 frames da
  −11. La curva tiene dos jorobas, hacia −6 y hacia +3, y el máximo salta de una a otra. No se ejecutó en el
  partido.
- **La v2 pasa:** 8 de 8 pruebas, con los 7 partidos a ±2 en todas. Intervalos de 1 a 4 frames y residuo de
  referencia 0,027. Con un suavizado exponencial, que no está en la familia, se queda corta, pero su residuo
  es de 3 a 8 veces el de referencia: la regla la habría dado por no concluyente.
- **Partido:** `d̂` = **+4** (del 5 al 95 %, de +2 a +5; por parte, +3 y +4; residuo 0,018). Es el candidato 2
  de la regla.
- **Coste de ese retraso en el harness,** frente a `main`:
  - con el flag, +0,001 («como el ATD») y +0,002 («sin bloques»);
  - con control, −0,007 y −0,006.

  Con §5.8, **empate**.

Decisión y por qué:
- **Se escribe la variante `ball.advance_ball`,** que adelanta el balón `BALL_LEAD` = 4 frames, como pide el
  candidato 2. Tiene sus pruebas en `validation/scripts/prueba_retraso_balon.py`.
  - `BALL_LEAD` **sí sale del partido:** es un agregado del tracking entero, sin ninguna etiqueta, que
    calcula un algoritmo con la regla fijada antes de medir. Entra en lo que RULES.md permite («learning
    without human labels… provided no person decided any of them»). No está ligado a frames concretos ni
    sale de la ventana pública.
- **Queda apagada:** `ball.clean` y la entrega no cambian. Encenderla ganaría como mucho unas 0,007
  [inferencia, del harness], muy por debajo del 0,03 de §5.8. Y obligaría a tres cosas:
  - reentrenar o medir B5;
  - repetir la medida de Manuel;
  - que la degradación «como el ATD» del harness retrase el balón 4 frames. Hoy llega a su hora (media
    centrada), así que el harness mediría un balón adelantado, no una corrección.
- **Propuesta para Ismael: no encenderla.** El riesgo de la revisión (unos 12 frames) queda descartado y la
  tarea se cierra.
- **Para Ismael, dueño del harness:** la degradación «como el ATD» no imita ese +4. Según esta medida, en la
  DFL cuesta entre −0,007 y +0,002.

**Después de medir el partido** (bitácora §11):
- **La revisión de Ismael** llegó cuando el partido ya se había medido; él había revisado `3e92064`. Pidió
  que, con `d̂` de −4 o menos, se apunte y no se toque nada: un suavizado centrado de 49 frames sin retraso da
  entre −6 y −1, y unos jugadores que llegan tarde también dan negativo.
  - Entra en `retraso.lectura` («negativo, se apunta»), pero ya no se pudo subir antes de ejecutar.
  - No cambia la lectura del partido: +4 es positivo.
- **Sensibilidad al ancho del suavizado** (DFL, descriptivo; `calibrar_dfl_v2.py --anchos 13 37 49`). Con el
  balón centrado sin retraso:

  | ancho | `d̂` en los 7 partidos |
  |---|---|
  | 13 | de −1 a +2 |
  | 37 | de −3 a +1 |
  | 49 | de −6 a −1 |

  Un suavizado centrado de otro ancho no fabrica un +4. Si el ATD suavizara menos de 25 frames, el retraso
  de verdad podría estar más cerca de +2. La decisión no cambia.
- La salida entera del partido está en `validation/resultados/2026-11-15_retraso_balon.md`.

Descartado:
- la v1, porque no pasó la calibración;
- una tercera versión, que la regla de la v2 ya excluía;
- la latencia de la ventana pública como puerta (plan §3).

Límites:
- La medida es relativa: si los jugadores del ATD también llegaran tarde, no se vería.
- `d̂` está en el corte: el intervalo incluye +2 y +3, que habrían sido el candidato 1.

