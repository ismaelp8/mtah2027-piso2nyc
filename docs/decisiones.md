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

Añadido (15/11, `main` en `4305576`) [medido por Ismael]: **con numpy 2.3.4 también sale `9539ce42…cc17a`.**
- Se regeneró, sin querer, en otro entorno de Ismael: Python 3.13.9 con numpy 2.3.4, en vez del entorno limpio.
- Salen los mismos recuentos y el validador da `Valid`.
- Es la primera prueba de que la huella aguanta un cambio de versión de numpy. No cambia lo fijado: la entrega
  se regenera con `requirements-entrega.txt`.

Añadido (15/11, `main` en `8f90dea`, después de la PR 12 de Ana) [medido por Ismael]: **la PR 12 no cambia la
entrega.**
- `equipo_v4` se regeneró en el entorno limpio (Python 3.13.9, numpy 2.5.4). Sale con el sha256 de `equipo_v3`,
  y `validation/partido/comparar_entregas.py` da 0 frames evaluados distintos.
- Se comprobó que la copia de Ismael estaba en `8f90dea` y sin cambios locales en el código de la entrega.
- Desde entonces el comando imprime el commit con el que se genera y avisa si el código tiene cambios sin
  commitear (`pipeline.code_version`), para que no haga falta comprobarlo a mano.

Falta:
- **Repetir la huella en el ensayo del lunes por la noche,** en el entorno limpio
  (`C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe`), con lo que haya entrado en `main` hasta
  entonces.
- **La versión de numpy de la máquina Linux** que reprodujo `equipo_v2` [sin verificar].
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

### 2026-11-15 · candidatos · se reabre la evidencia de equipo tras la ronda de B5

Quién: Ismael, el mismo 15/11, después de que la ronda única de reentrenamiento de B5 empatara y la regla de
parada cerrara la evidencia de equipo (entrada anterior). Sus palabras: «si, claramente vamos a reabrirla
dejate de decisiones tomadas de tiempo. Es claro que tenemos un problema en que predecimos muchas menos
posesiones de las que hay, sobretodo cuando son posesiones cortas.»

Por qué [medido, `validation/resultados/2026-11-15_diagnostico_errores.md`]:
- **Cambiamos de equipo de menos.** Con el flag, `main` hace 1.661 cambios de equipo en la DFL y hay 3.061;
  en la mitad de SkillCorner para diagnosticar, 2.270 frente a 3.228.
- **Llegamos tarde o no llegamos.** Solo entre el 16 y el 37 % de los cambios reales tiene uno nuestro a
  menos de 1 s (en el placebo, el 2 %).
- **Casi nunca partimos una posesión en dos.** El problema está en las que faltan, no en las que sobran.

Qué cambia:
- **La regla de parada del 15/11 deja de valer.** La evidencia de equipo vuelve a admitir candidatos.
- **Lo demás sigue igual:** cada candidato se escribe antes de medir, y para entrar tiene que ganar a `main`
  con §5.8 en el harness de la DFL. SkillCorner tiene 10 partidos de examen que no se tocan hasta el final.
- **B5 sigue en la entrega** (`equipo_v3`) hasta que algo gane.
- **El estudio lo hace la sesión «Posesiones cortas»,** en su rama. Sus resultados se apuntan aquí cuando
  entren en `main`.

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

Nota de la revisión (Ismael, 15/11), al mergear la PR 11 (`acec765`):
- «El riesgo de unos 12 frames queda descartado» se lee con el primer límite: descartado **respecto a los
  jugadores**. Un retraso que el balón y los jugadores compartan respecto al vídeo no se puede ver con esta
  medida.
- El cambio del lado negativo de la lectura (con −4 o menos se apunta y no se toca) lo pidió la revisión y
  entró después de ejecutar en el partido. No cambia el resultado, que es positivo.
- `ball.advance_ball` entra apagada, como propone la PR. La entrega no cambia. Encenderla sigue siendo
  decisión de Ismael.

### 2026-11-15 · candidatos · Antonio empieza su tarea 2: las fases del Smart Tagging como pista de equipo

Quién: Ismael. La tarea 2 de Antonio (`docs/PLAN_ENTREGA.md` §3) estaba reservada a su decisión. Sus palabras
(15/11): «si, quiero que haga su tarea 2 le doy mi si».

Qué se probó: nada todavía. Es el permiso para empezar.

Por qué ahora:
- Antonio ha cerrado su tarea 1: el balón llega 4 frames tarde respecto a los jugadores y la corrección queda
  apagada (entrada anterior).
- El estudio de las posesiones cortas (rama `claude/posesiones-cortas-5e84f8`, todavía fuera de `main`) mide,
  en datos abiertos, que lo que más vale es acertar el equipo en las posesiones de 2 a 10 s, y que ninguna
  señal del tracking lo arregla: B9 y una red de una capa empatan con las etiquetas de control.
- Las fases son la única información de equipo que la entrega no usa. Cubren el 68,1 % de los frames
  evaluados [medido, `validation/resultados/2026-11-14_agregados_balon_muerto.md`].

Cómo se medirá: no se puede medir en la DFL, que no tiene Smart Tagging. Vale la regla del plan, sin
cambios: un recuento del partido, que ejecuta Antonio, con el acuerdo entre el equipo de la fase y el del
más cercano en los frames de control claro, frente a las fases desplazadas. Si no llega al 80 % o no dobla
al placebo, no entra.

Lo que se añade al recuento, escrito antes de ejecutarlo y solo descriptivo:
- la tabla de cada código a «tiene el balón el equipo de la fase» o «lo tiene el otro», sacada de
  `OVERVIEW.md` (`Team` es el equipo que hace la fase). Quedan fuera `N/A`, `SET PIECES` y `GOALS`;
- cuántos frames tienen fases solapadas que dan equipos distintos. Esos frames se excluyen, y una tasa alta
  dice que la tabla está mal;
- cuántos inicios de «Attacking Transition» tienen un cambio nuestro a ese equipo a menos de 2 s, frente al
  placebo.

Decisión y por qué: Antonio empieza. El alcance de lo que puede entrar es el del plan: un empujón pequeño,
en los frames sin balón. Un uso más amplio pide otra decisión de Ismael, porque no se puede medir.

Descartado: copiar las fases como etiquetas, o darles un peso comparable al coste de cambio
(`docs/revision_externa_2026-11-15.md`).

### 2026-11-15 · candidatos · posesiones cortas: B9, B5 con la dirección del balón (candidato, antes de medir)

Quién: sale de la reapertura de Ismael («se reabre la evidencia de equipo tras la ronda de B5», más arriba).
Claude lo escribe, lo entrena y lo mide en la rama
`claude/posesiones-cortas-5e84f8`. La regla tiene commit antes de entrenar.

Por qué (`validation/resultados/2026-11-15_posesiones_cortas.md` y `validation/posesiones_cortas/BITACORA.md`):
- en las posesiones que no encontramos, la evidencia de B5 apunta al otro equipo durante casi toda la
  posesión. Hay que cambiar su signo, no el coste de cambio;
- el más cercano no trae información por frame en las de menos de 2 s, ni con el balón limpio;
- la dirección en que se mueve el balón sí la trae: en las de 2 a 5 s acierta el 81 % de los frames en que
  opina en la DFL (el más cercano, el 57–60 %) y el 66 % en SkillCorner;
- dos ideas se descartaron antes con su puerta: entrenar con SkillCorner y «proponer y clasificar».

**Cómo se eligió el diseño, para que conste:** la señal, el umbral de 2 m/s y la ventana de 13 frames salen
de un sondeo y de una puerta hechos en los mismos 7 partidos de la DFL (BITACORA §6). Dejar un partido fuera
protege los coeficientes, no el diseño. Lo único que no ha visto nada de esto es el examen de SkillCorner
(`lector.EXAMEN`).

Candidato, uno solo. **B9 es B5 con tres rasgos más,** la dirección del balón
(`aprendida.direccion_del_balon`):
- en cada frame, la velocidad del balón en x de t−6 a t+6, con el signo de la dirección de ataque del local
  (la de B2: el local ataca hacia donde está, en media, el visitante);
- vale +1 si pasa de 2 m/s y −1 si baja de −2 m/s. Vale 0 si no, si falta el balón en alguno de los dos
  extremos o si alguno cae fuera del tramo;
- los rasgos son su media centrada en 1, 13 y 51 frames.

Lo demás, como B6, B7 y B8 (`validation/posesiones_cortas/entrenar_b9.py`):
- las mismas filas: frames vivos en los que el flag y el control coinciden, uno de cada 5, con el balón
  «como el ATD» y `ball.clean`;
- la misma regresión y los mismos pliegues;
- la misma puntuación que B5;
- la misma elección de α, con la pieza de `D` de `main` dentro y sin oráculo.

No hay segundo candidato. Reentrenar con peso cerca de los cambios (B7) y con más filas (la puerta de
SkillCorner) ya salió plano con el control.

Comprobaciones del instrumento, antes de leer nada:
- los coeficientes de B1 a B8 quedan iguales byte a byte;
- los rasgos de B9 son los de B5 más las tres columnas de la puerta;
- la elección de α del script, con los pesos de B2, repite la α de B5 en cada pliegue;
- la fila de `main` repite 0,498 / 0,512 / 0,728 / 0,748 en el harness y 629 / 628 / 545 en
  `d_propio.py`;
- `prueba_aprendida.py` y `prueba_harness.py` en verde.

Cómo se mide, en este orden:
1. **Harness con el `D` oráculo y `--eventos`,** con `validation/harness/versiones/posesiones_cortas_b9.json`
   y `dejar_fuera`. Regla de §5.8 frente a `main` y frente al control, en las dos condiciones que votan y con
   las dos convenciones.
2. **Eventos humanos,** en la misma ejecución, como en la ronda de B5: la estimación de la diferencia frente
   a `main`, en las dos condiciones que votan. La de las recuperaciones tiene que ser mayor que cero, y la de
   los duelos sin cambio no puede bajar de −5 puntos.
3. **Criterios 2 y 3 de B5,** con `validation/apuesta_b/d_propio.py --versiones` y el mismo fichero, como en
   la ronda de B5. Quedarse corto por poco cuenta como no cumplir.
4. **SkillCorner, mitad de entrenamiento (descriptivo, antes del examen):** B9 con los coeficientes de los 7
   frente a `main`, con el `D` oráculo, en las dos condiciones que votan. Si la diferencia no es mayor que
   cero en las dos, el examen no se ejecuta.
5. **SkillCorner, examen (una sola vez):** lo mismo en `lector.EXAMEN`.
   - **Aguanta:** la diferencia frente a `main` es de 0 o más en las dos condiciones que votan.
   - **Gana:** la diferencia es de +0,03 o más, con el intervalo por encima de cero y ganando en 8 de los 10
     partidos o más, en las dos condiciones.

Descriptivo, escrito antes de medir. No decide nada:
- **placebo:** B9 con sus pesos, pero con las tres columnas de la dirección desplazadas 60 s dentro de cada
  tramo. Con el flag, la ganancia sobre `main` tiene que desaparecer (+0,01 o menos);
- **sensibilidad:** el balón retrasado 12 frames, como si el suavizado del ATD fuera hacia atrás, para B9 y
  para `main`. ¿Se mantiene la ganancia?

Regla de lectura, fijada antes de medir:
- **Lectura 1, la de siempre: entra** si cumple 1, 2 y 3 y aguanta en el examen (5). Se propone a Ismael
  cambiar `pipeline.PIECES`, en un commit aparte, y la decisión es suya.
- **Lectura 2, para que decida Ismael.** Se le presenta, sin entrar sola, si cumple todo esto:
  - con el flag, gana a `main` con §5.8: +0,03 o más, en 6 de 7 o más y con el intervalo por encima de cero,
    en las dos condiciones que votan;
  - con el control, no pierde: la diferencia frente a `main` es de −0,01 o más en las dos condiciones que
    votan;
  - cumple 2 y 3;
  - en el examen de SkillCorner, la diferencia frente a `main` es mayor que cero con el intervalo por encima
    de cero, en las dos condiciones que votan.

  Es el caso «mejor con el flag y con SkillCorner, igual con el control». Si la GT del reto está entre las
  dos convenciones, como sugiere SkillCorner, saldría a cuenta. §5.8 tal cual lo llamaría empate.
- **Si no cumple ni la 1 ni la 2, es un empate.** Se apunta y se cierra con el informe.
- **Nada de lo medido cambia el candidato:** ni el umbral, ni las ventanas, ni las filas, ni la rejilla de α.

Resultado (15/11; `validation/resultados/2026-11-15_posesiones_cortas.md`, código `4e662ad`; salidas en
`validation/posesiones_cortas/salidas/`) [medido]:
- **Instrumento:**
  - B1 a B8 sin cambios (el diff solo añade B9);
  - los rasgos de B9 son los de B5 más los de la puerta;
  - la elección de α repite la de B5 en los 8 pliegues;
  - `main` repite 0,498 / 0,512 / 0,728 / 0,748 y 629 / 628 / 545;
  - las dos pruebas, en verde.
- **1. Harness, frente a `main`:** con el flag gana con §5.8 (+0,039 en 7 de 7 y +0,048 en 6 de 7, los dos
  intervalos por encima de cero). Con el control empata (−0,006 y −0,005, los dos intervalos cruzan el cero).
  Frente al control del harness gana en todo.
- **2. Eventos: no cumple.** Las recuperaciones suben +8,2 y +7,7 puntos, y los duelos con cambio, +4,8 y
  +5,2. Pero los duelos sin cambio bajan −4,7 («como el ATD») y −5,7 («sin bloques»), y el límite era −5.
- **3. `D` propio: cumple.**
  - Con el balón tapado: 630 y 629 paradas vistas, frente a 629 y 628. La precisión del `D` queda a 0,1
    puntos. El spellF1 con el `D` propio no baja en ninguna celda: 0,456 / 0,618 y 0,480 / 0,643, frente a
    0,416 / 0,616 y 0,433 / 0,642.
  - Con el balón a la vista: 543 paradas vistas frente a 545, a 0,3 puntos.
- **4. SkillCorner, mitad de entrenamiento: no es positivo en las dos condiciones.** «Detectado» da −0,005
  [−0,009 a +0,000], ganando en 1 de 10. «Detectado, suavizado» da +0,004 [−0,002 a +0,009], en 7 de 10.
  **El examen no se ejecuta:** `lector.EXAMEN` sigue intacto.
- **Placebo** (descriptivo): con la dirección desplazada 60 s, la ganancia con el flag desaparece (−0,019 y
  −0,012). La señal es real en la DFL.
- **Sensibilidad** (descriptivo): con el balón 12 frames tarde, B9 mantiene la ganancia con el flag (+0,040 y
  +0,044), pero con el control pierde (−0,022 y −0,026). **De paso:** el propio `main` cae de 0,728 a 0,640
  con el control y de 0,498 a 0,472 con el flag.

Decisión y por qué: **no cumple ni la lectura 1 ni la 2. Es un empate: B5 sigue en la entrega y
`pipeline.PIECES` no cambia.**
- Falla el paso 4 de las dos lecturas, y la lectura 2 también falla el criterio 2.
- B9 es la primera idea que encuentra posesiones cortas de verdad en la DFL. Las de 2 a 5 s encontradas con
  el control pasan del 53 al 62 % en la puerta. Las recuperaciones suben 8 puntos.
- Pero no mejora en SkillCorner, el tracking automático más parecido al ATD que hay abierto. Ahí la dirección
  del balón ya acertaba menos (el 66 % en las de 2 a 5 s, frente al 81 % en la DFL) [sin explicar].
- SkillCorner también exige control, y B9 también empata con el control de la DFL. No se puede separar si en
  SkillCorner falla por el tracking automático o por la convención.

Descartado: B9 tal cual. Queda en `possession/aprendida.py`, con sus coeficientes y fuera de
`pipeline.PIECES`, como referencia del documento técnico.

### 2026-11-15 · candidatos · posesiones cortas, fase 3: con estos rasgos no hay más, ni con un modelo flexible

Quién: lo pidió la sesión principal (orquestadora, por encargo de Ismael). Claude escribió la puerta con su
regla (`validation/posesiones_cortas/BITACORA.md` §10, commit `3193b43`) antes de ejecutarla.

Qué se probó: si lo que limita es la forma lineal de B5 y B9 o los rasgos. Una red de una capa de 32, en
numpy y sin sesgos, con los rasgos de B9, y con ellos más 6 señales de los jugadores alrededor de un cambio.
Mismas filas, pliegues y elección de α que B9.

Cómo se midió: fuera de muestra, con el `D` de las etiquetas. En la DFL, cada partido con el pliegue que no lo
vio; en `lector.ENTRENAMIENTO` de SkillCorner, con el modelo de los 7 partidos. El examen no se abrió.

Resultado [medido]:
- con el control, la red empata con `main` (−0,005 a −0,003) y con su versión lineal;
- en SkillCorner pierde (−0,019 a −0,025);
- con el flag gana mucho (+0,061 a +0,092 frente a `main`).

Encuentra más posesiones de 2 a 10 s, pero predice tantas de más que con el control no gana.

Decisión y por qué: **se cierra la pregunta. Con estos rasgos no hay más, ni con un modelo flexible.** No se
abre ningún candidato, B5 sigue en la entrega y `pipeline.PIECES` no cambia. Lo que la red gana con el flag
es una apuesta de convención que no se traslada a SkillCorner.

Descartado: la red, en sus dos brazos, y las señales de los jugadores alrededor de un cambio.

### 2026-11-15 · `D` · el estado con jugadores no mira fuera de los tramos evaluados

Quién: Ana. Es la tarea 1 de su bloque (`docs/PLAN_ENTREGA.md` §3), que Ismael repartió a partir del punto
14 y de P3 de la revisión externa (`docs/revision_externa_2026-11-15.md`).

Qué pasaba:
- **Las ventanas de `possession/dead_state.py` cruzaban el borde de cada tramo evaluado.** Los rasgos
  promedian hasta ±2 s alrededor de cada frame, y la velocidad de un jugador usa los frames t − 2 y t + 2.
- **En la DFL del harness, fuera de cada parte no hay datos,** y la media los ignora. En el partido sí los
  hay: los jugadores están parados antes del saque. Los primeros segundos de cada parte recibían una
  evidencia de `D` que el harness nunca ve [inferencia de la revisión; no se ha medido en el partido].

Qué se cambió:
- **`dead_state.segments`** corta el tracking por los bordes de `trk.blocks`. Ni la ventana de un rasgo ni
  la velocidad de un jugador usan frames de fuera del segmento de su frame.
- **No se reentrena:** el modelo E2 y sus coeficientes son los mismos.
- **Las sumas acumuladas siguen siendo las de todo el partido.** Solo se recortan los límites de cada
  ventana. Donde fuera de los tramos no hay datos (la DFL del harness), el resultado es idéntico, bit a
  bit, al de antes.

Cómo se midió (7 partidos de la DFL, sin datos del partido) [medido]:
- **Los 19 rasgos y la puntuación, bit a bit iguales a los de antes** en los frames evaluados de los 7
  partidos (entre 137.214 y 146.810 por partido). Comparado con el código de `main` en `fb9e921`.
- **`validation/scripts/d_estado/medir.py`:** la misma salida que antes, salvo los tiempos.
- **`entrenar.py --comprobar`:** `MODEL` coincide con el recalculado (diferencia máxima 0).
- **`validation/scripts/d_estado/prueba_d_estado.py`** (nuevo, con un partido inventado): lo que haya fuera
  de los tramos no cambia la puntuación de dentro. Sin recortar, sí la cambia: 96 de los 100 primeros
  frames de los dos tramos.
- **`prueba_pipeline.py` y `prueba_harness.py`:** en verde.

Decisión y por qué: **entra, porque quita una diferencia entre lo que valida el harness y lo que se
entrega,** y en la DFL no cambia nada.
- **En el partido solo pueden cambiar los rasgos de los 52 primeros y los 52 últimos frames de cada tramo
  evaluado:** los 50 frames (2 s) de la ventana más larga del modelo E2, más los 2 del desfase de la
  velocidad (`SPEED_LAG`). Lo que cambien las etiquetas ahí está [sin verificar]: lo dirá la entrega que
  regenere Ismael.
- **Más lejos de los bordes, los rasgos de velocidad pueden cambiar en el último bit.** La velocidad pierde
  2 valores en cada borde, y eso mueve el redondeo de la suma acumulada de ahí en adelante. El redondeo de
  la puntuación a 1/1024 lo absorbe. Con un partido inventado de 60.000 frames con datos fuera de los
  tramos [medido]: los rasgos de velocidad cambian menos de 1e-12 en términos relativos hasta a unos
  11.000 frames de un borde, y la puntuación cambia en 52 de 48.000 frames evaluados, todos a 51 frames o
  menos de un borde.
- **Para la regeneración:** conviene contar cuántas etiquetas cambian respecto a `equipo_v3` y cuántas caen
  lejos de los cuatro bordes, porque el decodificador puede mover un cambio más allá de esos 52 frames. Los
  frames afectados incluyen el principio de la 1ª parte, que previsiblemente cae en la ventana pública
  [sin verificar]: lo que salga ahí no decide si el cambio se queda.
- **Fuera de los tramos,** un frame pegado a un tramo ya no ve los datos de dentro. Ahí se escribe `X` y
  no se evalúa.

Descartado: calcular los rasgos tramo a tramo, con una suma acumulada por tramo. Haría que lo de fuera no
moviera ni el último bit, pero cambiaría el último bit de las sumas en la 2ª parte de la DFL, y lo medido
en el harness dejaría de ser idéntico bit a bit a lo de antes. En el partido no hay diferencia práctica
entre las dos opciones: con las dos el último bit puede moverse lejos de los bordes.

### 2026-11-15 · `D` · el estado con jugadores: opción de escala y versión de `scikit-learn`

Quién: Ana. Son las tareas 2 y 3 de su bloque (`docs/PLAN_ENTREGA.md` §3; P6 de la revisión externa y lo
que quedó pendiente de la PR 5).

Qué se cambió:
- **`dead_state.evidence(trk, scale=1.0)`:** la escala multiplica la puntuación de la columna `D`. Se
  aplica a la puntuación ya recortada a ±8, como en la sensibilidad de
  `validation/scripts/d_estado/medir.py`, y además se vuelve a redondear a múltiplos de 1/1024. Con 0,5 la
  pieza puntúa entre −4 y +4.
- **No es idéntica a esa sensibilidad:** `medir.py` no redondea, así que con 0,5 las dos difieren en 1/2048
  como mucho. `medir.py` se queda como está, para que siga dando las cifras del 14/11: con el redondeo,
  cuatro de ellas cambian en el último decimal (E1 y E3 con la escala 0,5; E2, ninguna) [medido, DFL].
- **El valor por defecto es 1 y la entrega no cambia:** con la escala 1 la puntuación es la misma bit a
  bit [medido, con un partido inventado].
- **Para el harness:** `"piezas": {"dead_state": {"funcion": "evidence", "opciones": {"scale": 0.5}}}` en
  un fichero de `validation/harness/versiones/`. Es lo que necesita David para su tarea 2.
- **La versión de `scikit-learn` del entrenamiento del 14/11 es la 1.7.2,** con numpy 2.2.4, scipy 1.15.3
  y Python 3.10.12. Queda apuntada en `possession/dead_state.py`, en `entrenar.py` (que ahora imprime las
  versiones que usa) y en el README de `validation/scripts/d_estado/`.
  - Es la que hay instalada en la máquina de Ana desde antes del entrenamiento [medido: fecha de
    instalación]. Con ella, `entrenar.py --comprobar` da hoy los mismos coeficientes (diferencia máxima 0)
    [medido].

Cómo se midió: `validation/scripts/d_estado/prueba_d_estado.py`, con un partido inventado. Comprueba la
escala 1, 0,5, 2 y 0, las escalas que dan error, que el harness acepta la opción y que el pipeline da las
mismas etiquetas con la escala 1.

Decisión y por qué: **la opción entra, apagada.** No se ha medido ninguna escala distinta de 1 con ella:
eso es la tarea 2 de David, que es descriptiva, y lo que gane en sus dos modos y con las dos convenciones
lo decide Ismael.

Descartado:
- **Aplicar la escala antes de recortar:** con 0,5 la pieza seguiría llegando a ±8 en los frames más
  claros. No sería la escala que midió `medir.py` el 14/11 (a la mitad, algo mejor; al doble, peor).
- **No volver a redondear:** con una escala que no sea potencia de 2, las sumas del decodificador dejarían
  de ser exactas y la pieza podría deshacer empates entre `H` y `A`. El coste es que la escala 0,5 mueve la
  puntuación 1/2048 como mucho.

### 2026-11-15 · validación · posesiones cortas, fase 4: el déficit no es propio del partido; cota de una pista de equipo de fuera

Quién: lo pidió Ismael por la sesión principal («haga una investigacion tambien para ver como arreglar lo
demas»). Claude escribió las dos reglas (`validation/posesiones_cortas/BITACORA.md` §11, commit `ba55354`) antes
de ejecutar. Es descriptivo.

Qué se probó y resultado [medido]:
- **¿Es real el déficit del partido?** Con nuestro `D`, `main` saca 4,29 / 4,26 posesiones por minuto de juego
  predicho en la DFL y 4,11 en SkillCorner, con partidos de 3,45 a 5,76. Las 3,7 del partido caen dentro: con
  la regla, «cerca». El déficit es el de siempre, no propio del partido.
- **¿Cuánto valdría una pista de equipo de fuera (como las fases del Smart Tagging)?** Con una pista sintética
  en la DFL (trozos de 7,5 s que aciertan o fallan enteros, sin mirar los bordes):
  - solo en los frames sin balón, que es el alcance del plan, no cambia nada (±0,008);
  - en todos los frames, ayuda con el control (+0,011 a +0,022) solo si acierta el 90 % o más y pesa 2 o 4;
  - con el flag no ayuda nunca.

  Es una cota superior: los fallos son independientes de los de B5.

Decisión y por qué: ninguna. Lo de la pista se pasa a Antonio y a Ismael para la tarea 2:
- con el alcance del plan, la pista casi no tiene dónde actuar;
- para que pese, tendría que acertar mucho y usarse en todos los frames, y eso es otra decisión de Ismael;
- valdría más si marca dónde cambia la posesión, y eso no se ha medido.

**Añadido el mismo día, con su regla antes de ejecutar** (`validation/posesiones_cortas/BITACORA.md` §13, commit
`92b4771`): una pista sintética que marca dónde cambia la posesión, como las «Attacking Transition».
- Con las 24 transiciones del partido (≈ 16 % de los cambios), perfectas y con peso 8 en todos los frames,
  daría +0,013 a +0,016 si caen al azar y +0,021 a +0,027 si caen en cambios que `main` no ve [medido, cota
  superior].
- Para llegar a +0,03 hace falta el 30 % de los cambios, todos de los que `main` no ve y a 1 s o menos.
- Ninguna combinación hace daño.
- Para Antonio: lo que importa es cuántas transiciones caen a 1 s o menos de un cambio real, cuántas no las ve
  `main` y con qué retraso.
- Para Ismael: solo pesaría con un alcance mayor que el del plan (todos los frames, peso fuerte).

**H3 y H5 del visionado, el mismo día** (regla en `validation/posesiones_cortas/BITACORA.md` §14, commit `41c3c23`,
antes de que Ismael ejecutara `validation/partido/huecos_y_cambios.py`):
- en el partido, nuestros cambios no se juntan con los huecos del balón más que en la DFL (R 1,19 frente a
  1,20), y tras un hueco cambiamos menos;
- con solo 6 cambios junto a un hueco, la regla dice que no concluye;
- en pleno juego el ATD casi no pierde el balón (37 huecos).

Decisión: ninguna. No se abre ni una degradación nueva ni un candidato antes de la entrega.


### 2026-11-15 · infraestructura · cualquiera del equipo puede contestar, decidir y revisar

Quién: Ismael. Sus palabras (15/11): «No puede ser todo tan restrictivo lo que te dije yo de que me utilizaran
de revisor era orientativo pero todo el mundo puede responder, decidir y revisar. Por eso si eliminar eso
mejor».

Qué pasaba: las normas decían que las PR las revisaban Ismael y David, y el plan y las bitácoras reservaban
muchas decisiones a Ismael («lo decide Ismael», «se le pasa a Ismael», «pendiente de permiso de Ismael»). El
Claude de una compañera se negó a que contestara una duda que otro compañero tenía para Ismael.

Decisión y por qué: Ismael no es una puerta.
- Cualquiera del equipo puede contestar una duda, tomar una decisión y revisar, aprobar o mergear la PR de
  otra persona.
- Cada uno puede mergear su propia PR, sin esperar una aprobación. Ismael lo aclaró después (15/11): «si,
  claro que puede mergear alguien su propia PR».
- Donde un texto del repo reserve algo a Ismael, se lee como «lo decide el equipo». Quien decide lo apunta
  aquí, con su nombre y el porqué.
- Cambiado en `CLAUDE.md`, `CONTRIBUTING.md`, `docs/PLAN_ENTREGA.md`, `docs/GUIA_EQUIPO.md`, las skills
  `/subir` y `/revisar-pr` y la plantilla de PR. Las menciones de decisiones ya tomadas («decisión de
  Ismael, 14/11») se quedan: dicen quién decidió.

Lo que no cambia:
- lo que viene después de una decisión: si toca `pipeline.PIECES`, un valor por defecto o código que usa la
  entrega, alguien regenera la entrega y la valida;
- la regla nº 1 de los datos, la ventana pública, las reglas escritas antes de medir, que solo Ismael sube
  directo a `main` y el resto de las normas de git.

Descartado: buscar y cambiar cada frase de las bitácoras, los resultados y los comentarios del código. Basta
con la regla general de `CLAUDE.md`, que todas las sesiones leen al empezar.

### 2026-11-15 · validación · visionado de la ventana pública junto al vídeo (reglas, escritas antes de mirar)

Quién: Ismael (mira el vídeo); Claude prepara la herramienta y ordena lo que cuente, sin ver nada del partido.

Qué se hace:
- Ismael mira, junto al vídeo táctico, los tramos de los 5 minutos públicos en que `equipo_v3` y la GT
  pública no coinciden, con `validation/partido/clips_ventana.py`. Esa página la abre solo él, y su guía es
  `validation/partido/GUIA_VISIONADO.md`.
- Lo que vea se convierte en hipótesis generales, cada una con su forma de medirla en la DFL y en
  SkillCorner y su criterio escrito antes de medir.

Con qué reglas (`RULES.md` §1 y §2; `CHALLENGE.md`, «The reference is the ground truth»):
- mirar el vídeo y la GT pública para entender cómo se etiquetan los casos está permitido;
- no se convierte nada en etiquetas, correcciones ni reglas o constantes ligadas a momentos del partido;
- no se ajusta ni se elige nada con la ventana: son 17 posesiones;
- Ismael cuenta patrones generales, sin minutos, frames ni recuentos tramo a tramo. No es una medida, a
  diferencia del recuento a ojo de la PR 1 (zona gris, `docs/revision_externa_2026-11-15.md` §3.4);
- Claude no ve el vídeo, ni la página, ni la entrega, ni notas con tiempos.

Resultado (15/11, los 10 tramos de `equipo_v3`: 4 solo de borde y 6 con posesiones o paradas distintas).
Son jugadas concretas, contadas en general; no es una medida. La página y la sincronía con el vídeo se
comprobaron antes (saque inicial, avance de un frame, parada al final de cada tramo).

- **Cambios de equipo** (pasadas a la sesión de posesiones cortas, que las contrastó con lo medido):
  - la GT da el cambio en el primer toque de la secuencia que gana la posesión (despeje que cae a un
    compañero, pase de primeras, portero que coge el balón). Las etiquetas de control del harness ya fechan
    así el cambio: no hay nada que medir (H1, H4);
  - en el partido llegamos tarde, de 0,7 a 3 s, y en los datos abiertos no (mediana de +0 a +3 frames).
    Hipótesis: el ATD pierde el balón en el vuelo de los balones aéreos y la degradación del harness no lo
    copia (H5). Se midió con `validation/partido/huecos_y_cambios.py`, junto con la del portero (H3), y
    **no concluye** (`validation/resultados/2026-11-15_huecos_y_cambios.md`). R vale 1,19 en el partido,
    frente a 1,20 en la DFL, y solo 6 de nuestros 103 cambios caen junto a un hueco. H3 y H5 se cierran sin
    candidato;
  - mover cada cambio al primer acercamiento del equipo nuevo (H2): con un oráculo, techo de +0,05 con el
    control. Sin candidato;
  - tres posesiones cortísimas por un toque sin control (despejes) que la GT cuenta. **Es contexto:** no
    reabre «exigir control».
- **Balón muerto** (para Manuel y Ana):
  - D4: la GT pone el `D` en el instante del pitido, también tras una ley de la ventaja. El sondeo del
    silbato está sucio; solo se puede medir en el partido;
  - D2: si nuestro `D` llega tarde, damos la posesión al equipo que va a sacar;
  - D5: el `D` acaba en el golpeo del saque; vamos tarde o pronto según la parada;
  - D6: `D` antes de tiempo con el balón en juego junto a la línea;
  - D3: `D` falso de menos de 2 s en pleno juego;
  - **D7, la más cara: el balón fuera del campo no dispara el `D`.** Ninguna pieza lo usa (comprobado en el
    código). En un saque de puerta damos la posesión al portero que va a por el balón durante unos 10 s. La
    revisión del 13/11 ya propuso ese disparo y no se midió. Coincide con la tarea 2 de Manuel en
    `docs/PLAN_ENTREGA.md` §3 («el balón visto fuera de las líneas»), que está sin hacer.
  - Cada una lleva su forma de medirla en la DFL o con agregados del partido.

Decisión y por qué: **ninguna.** Nada se ajustó ni se eligió con la ventana. Las hipótesis se pasaron a la
sesión de posesiones cortas y a la de la pieza de Ismael. Cuáles se miden lo decide Ismael, con su criterio
escrito antes de medir.

### 2026-11-15 · validación · dos hipótesis del visionado se prueban: el balón fuera del campo y los toques sin control

Quién: Ismael. Sus palabras (15/11): «vale las tenemos como hipotesis pero no quieres aplicar alguna? Puede que
probando algunas de las cosas que he comentado puede que tengamos mejores soluciones».

Qué se abre, y en qué orden:
- **D7, el balón fuera del campo como señal de `D`.** Es la tarea 2 de Manuel en `docs/PLAN_ENTREGA.md` §3,
  sin hacer, con la definición del plan (el balón visto a más de 1 m fuera). No se puede medir en la DFL: allí
  el balón se queda quieto mientras está muerto, así que «fuera es `D`» se cumple por construcción.
  - Primero, un recuento del partido que ejecuta Ismael: de los frames con el balón visto a más de 1 m fuera,
    cuántos etiqueta ya `equipo_v3` como `D`, como `H` y como `A`. Si casi todos son `D`, se cierra.
  - Después, una capa nueva en `possession/dead_ball.py`, apagada, con un solo peso escrito y razonado antes
    del recuento. Sin variantes, y sin mover el margen para encajar ningún caso del visionado.
- **La convención de los toques sin control.** En el visionado salieron tres posesiones cortísimas por un
  toque sin control que la GT cuenta. Se cuenta, en la GT pública, cuántas posesiones cortas quedan entre dos
  del otro equipo sin un `D` en medio, con el mismo código medido antes en el flag y el control de la DFL y en
  SkillCorner, y con la lectura escrita antes de mirar.
  - Dice qué significan las etiquetas, que es para lo que está la GT pública. Cambiar a B9 por ese número
    sería una decisión aparte de Ismael, porque la ventana no elige entre versiones.

Qué no se abre, y por qué:
- D2 (un cambio de equipo falso antes de la parada): es consecuencia de un `D` que llega tarde y su techo es
  de +0,015 a +0,027. Se vuelve a mirar después de D7.
- D5 (el final de la parada): es la rama abierta de Manuel.
- D4 (el pitido): el sondeo del silbato salió sucio y añade una dependencia del audio.
- D3 y D6: no tienen una palanca clara.

Cómo termina cada una: como una opción apagada con su evidencia. Encenderla es una decisión aparte, y obliga a
regenerar la entrega y validarla.

### 2026-11-15 · `D` · D7, el balón fuera del campo: peso y regla del recuento, antes de ejecutarlo

Quién: lo prueba la sesión de integración, por encargo de Ismael pasado por la sesión principal (entrada
anterior). Es la tarea 2 de Manuel en el plan, sin hacer. Si sale una capa, será una función nueva en
`possession/dead_ball.py`, sin tocar sus líneas, y apagada.

**El peso, con una fórmula fijada antes de calcularlo** (`validation/scripts/peso_balon_fuera.py`, commit
`ec3c1ce`):
- La capa sumaría `W` en la columna `D` en cada frame con el balón visto a más de 1 m fuera. En ese frame, el
  equipo más cercano lleva el +1 de N1 dentro de B5 y el `D` lleva la puntuación de `dead_state` (`ds`). El
  frame empuja hacia `D` si `W + ds > 1`.
- Fórmula: `W = 1 − P95`, con `P95` el percentil 95 de `ds` en el juego vivo a 5 s o más de cualquier parada,
  en la DFL, redondeado hacia abajo. Así, un balón visto fuera por error en pleno juego (un balón de repuesto,
  el temblor junto a la línea) empujaría hacia `D` como mucho en el 5 % de esos frames.
- **Resultado [medido en la DFL]: `W = 0`.** En el juego vivo, `ds` tiene una mediana de −3,42 y un P95 de
  0,25. En el primer segundo de las paradas reales, la mediana es −0,31.
- **Lectura:** con esa seguridad, la capa no aporta nada. Cualquier peso de 1 o más empujaría hacia `D` en más
  del 5 % del juego vivo si el ATD viera fuera un balón que no lo está. La fórmula no se cambia después de ver
  el resultado.

**El recuento del partido, igualmente** (`validation/partido/balon_fuera.py`; lo ejecuta Ismael, solo
agregados; prueba con datos inventados en `validation/scripts/prueba_balon_fuera.py`). Sirve para saber cuánto
premio hay y decidir si merece la pena una decisión nueva sobre el peso.
- **Balón fuera:** visto a más de 1 m fuera de las líneas, con el balón como lo ve el pipeline, en los tramos
  evaluados y sin el tramo antes del saque de la 2ª parte.
- **Racha:** frames seguidos con el balón fuera, de 5 o más.
- **Llegamos tarde** a una racha si empieza con `H` o `A` en `equipo_v3` y nuestro `D` empieza más de 12
  frames (0,5 s) después, o no llega en 10 s.
- **Regla:**
  - **se cierra** si las rachas en que llegamos tarde son menos de 10 o menos del 15 % de las rachas;
  - **queda abierta** si son 10 o más y el 25 % o más. Abierta no enciende nada: hará falta una decisión
    nueva sobre el peso, con su riesgo escrito antes;
  - en medio, no concluye y no se abre nada.

Si queda abierta, la decisión nueva tendría que contar con dos cosas, medidas antes de elegir el peso:
- **Lo que no se sabe:** cuántas veces el ATD ve el balón fuera mientras el juego sigue. Lo mejor que hay son
  SkillCorner y Metrica, si su balón sale alguna vez del campo con el juego vivo.
- **Un riesgo al final de las paradas:** el balón del ATD va suavizado unos 25 frames, así que tras un saque de
  banda se sigue viendo fuera unos frames con el juego ya en marcha. Una capa con peso retrasaría el final del
  `D`, que ya llega tarde a veces (D5 del visionado).

Añadido el mismo día, antes del recuento del partido [medido en datos abiertos, descriptivo;
`validation/scripts/balon_fuera_abiertos.py`]: **«fuera es `D`» en SkillCorner y en Metrica.** Es el único
número que no es circular: allí el `D` sale de las fases de juego o de los eventos, no de dónde está el balón.
- **SkillCorner,** mitad de entrenamiento (el examen no se toca):
  - de los frames con el balón visto a más de 1 m fuera, el 93,0 % son `D` con el balón detectado, y el 94,3 %
    con el balón suavizado como el ATD;
  - de las rachas de 5 frames o más (596 y 465), caen enteras en juego 45 y 26. De ellas duran 2 s o más 3
    y 3, y 5 s o más, ninguna;
  - 44 y 38 rachas empiezan en juego y acaban en `D`: allí la parada de la etiqueta empieza después de que se
    vea el balón fuera.
- **Metrica** (3 partidos):
  - el 69,8 % de esos frames son `D` con el balón tal cual, y el 74,6 % suavizado;
  - de las rachas (47 y 22), caen enteras en juego 17 y 7. De ellas duran 2 s o más 2 y 2.
  - Sus etiquetas salen de eventos con su propia hora, así que el borde de la parada es más impreciso.
- **Lectura:** un balón visto fuera durante 2 s o más con el juego vivo es raro en los dos. Una capa que solo
  pudiera crear una parada nueva con 2 s seguidos de balón fuera inventaría pocas. Esto no cambia el peso
  fijado (W = 0): sirve para la decisión nueva sobre el peso, si el recuento del partido la abre.

**Resultado del recuento del partido** (15/11, ejecutado por Ismael con `equipo_v3`) [medido]: **queda abierta.**
- Hay 2.319 frames evaluados con el balón a más de 1 m fuera. En 1.476 decimos `D`; en 843 (36 %), `H` o `A`.
  En SkillCorner, esa proporción es del 6–7 %.
- Hay 47 rachas de 5 frames o más (13 por el fondo y 34 por la banda). En 22 ya decimos `D` al empezar.
- **Llegamos tarde en 23 (48,9 %).** En 10 de ellas, nuestro `D` no llega en 10 s.

**La decisión nueva sobre el peso,** escrita antes de generar ninguna entrega con la capa (la propone Claude;
encenderla la decide el equipo con los criterios de abajo):
- **Capa `dead_ball.ball_out`, apagada.** Es una función nueva, al final de `possession/dead_ball.py`, sin tocar
  sus líneas, y no la llama `evidence`.
- **Qué puntúa:** el balón visto a más de 1 m fuera, en las rachas de 5 frames o más, dentro de los tramos
  evaluados. No puntúa los 16 últimos frames de cada racha: tras un saque de banda, el balón del ATD se sigue
  viendo fuera con el juego ya en marcha, por el suavizado (la mitad de 25, 12 frames) y por el retraso medido
  por Antonio (4 frames).
- **Peso `BALL_OUT_SCORE` = 5,** el entero más grande con el que, en el juego vivo típico, un balón visto
  fuera tiene que durar 3 s o más para crear una parada él solo.
  - Cada frame suma `W + ds − 1` hacia `D`, donde el −1 es el +1 de N1, y una parada nueva cuesta 50
    (`to_dead` + `from_dead`). Con la mediana del juego vivo en la DFL (−3,42), `L ≥ 50 / (W − 4,42) ≥ 75`
    frames, así que `W ≤ 5,09`.
  - Por qué 3 s: en SkillCorner, las rachas de balón fuera con el juego vivo de 2 s o más son 3 en 10
    partidos, y de 5 s o más, ninguna.
  - Al principio de una parada real (mediana −0,31), cada frame con el balón fuera empuja +3,7 hacia `D`.
- **En la DFL no cambia casi nada** [medido]: con el `D` propio, 23 frames de 2.012.288 en las dos condiciones
  que votan. Allí el balón está tapado en los `D`, como se esperaba. No es una ganancia.

**Cómo se mide y cuándo se propone encenderla** (entrega de prueba que genera Ismael:
`python -m possession.pipeline --name prueba_d7 --capa dead_ball.ball_out`). Se propone encenderla si se
cumplen los tres:
1. `python validation/partido/balon_fuera.py --entrega prueba_d7`: llegamos tarde en menos del 15 % de las
   rachas, que con la regla de arriba se cerraría;
2. el resumen de `prueba_d7`: el `D` en los frames evaluados no pasa del 60 % y las paradas no pasan de 250
   (la banda de la capa de Manuel), y como mucho hay 15 paradas más que en `equipo_v3` (113). El recuento
   tiene 10 rachas sin `D`; muchas más serían paradas inventadas;
3. `python validation/partido/comparar_entregas.py equipo_v3 prueba_d7`: el 80 % o más de los frames que
   cambian pasan de `H` o `A` a `D`.

Si no se cumple alguno, la capa se queda apagada y se apunta aquí. Si se cumplen, encenderla es una decisión
del equipo: se añade la capa a `pipeline.build`, se regenera la entrega en el entorno limpio, se valida y se
apunta la huella.

**Resultado de la entrega de prueba `prueba_d7`** (15/11; la generó Ismael con el código de `cb95d90`, sin
cambios locales) [medido, solo agregados]: **falla el criterio 1, así que la capa se queda apagada.**
1. **Llegamos tarde en 12 de 47 rachas (25,5 %), frente a 23 (48,9 %) sin la capa.** Al empezar la racha ya
   decimos `D` en 34 (antes, 22), y en 7 nuestro `D` no llega en 10 s (antes, 10). Se pedía menos del 15 %:
   **no se cumple.**
2. **Se cumple.** El `D` ocupa el 45,4 % de los frames evaluados (`equipo_v3`: 45,1 %), y hay 116 paradas, 3 más.
3. **Se cumple.** Cambian 574 frames evaluados (0,361 %): 331 de `H` a `D` y 243 de `A` a `D`, ningún otro par,
   todos a más de 250 frames de un borde. Las posesiones siguen siendo 215.

Lectura: no hace daño y arregla la mitad de las rachas en que llegábamos tarde, pero no llega al criterio
fijado antes. **No se enciende.** El sha256 de `prueba_d7` es `eb244885…4f7f`. La sesión principal le propone a
Ismael una segunda versión que mantenga la parada desde que el balón se ve fuera hasta que vuelve a verse
dentro. Sería una decisión nueva, escrita antes de generar nada.

### 2026-11-15 · validación · la GT pública no dice si cuenta los toques sin control; B9, listo para decidir

Quién: Claude, por el encargo de «dos hipótesis del visionado se prueban» (más arriba). Regla en `validation/posesiones_cortas/BITACORA.md` §15,
con commit (`89610fd`) antes de mirar la GT pública.

Qué se midió y resultado [medido]:
- **Sándwiches:** posesiones de menos de 2 s metidas entre dos del otro equipo, sin `D` en medio.
  - Por minuto de juego, en ventanas de 7.500 frames, la mediana es 1,37 con el flag de la DFL, 0 con el
    control y 0,57 en SkillCorner.
  - La GT pública tiene 2 en 4,02 minutos (0,50 por minuto).
  - La regla decía «exige control» con 0 y «cuenta toques» con 3 o más: con 2, **no concluye**.
- **B9 con el balón 4 frames tarde** (lo que midió Antonio en el partido) sale igual que sin retraso: +0,035
  y +0,043 con el flag, −0,005 y −0,008 con el control. La tabla completa de lo que B9 cumple y no cumple
  está en la §16 de la bitácora.

Decisión: ninguna. B5 sigue en la entrega. Cambiar a B9 sería una decisión de Ismael, apuntada como suya: ni
§5.8 ni la ventana pública lo eligen.

**Decisión de Ismael (15/11): «Me quedo con B5».** B9 queda apagado en `possession/aprendida.py`, fuera de
`pipeline.PIECES`, y no se genera ninguna entrega de prueba con él. Se le recomendó así porque B9 no gana ni en
SkillCorner ni con el control, y la GT pública no apunta al flag.

Añadido (15/11) [medido por Ismael]: la entrega de prueba con B9 (`--pieza candidates=aprendida.evidence_b9`,
commit `2a4232c`) cambia poco en el partido: 216 posesiones frente a 215, y 49 frames más de `D`. No cambia la
decisión.

### 2026-11-15 · candidatos · se prueba un empujón al equipo de la fase en los contraataques, como opción apagada

Quién: Ismael. A la pregunta de si Antonio preparaba la opción de las transiciones, apagada, contestó (15/11):
«si a todo».

Por qué, con los números de la PR 13 de Antonio (`validation/resultados/2026-11-15_fases_smart_tagging.md`,
agregados del partido con `equipo_v3`):
- en los frames de control claro, la etiqueta de «Attacking Transition» coincide con el equipo que tiene el
  balón en el 93,1 %;
- en 19 de los 24 inicios seguimos con el otro equipo, y en 17 tardamos de 2 a 10 s en cambiar;
- dentro de esas fases vamos con el equipo equivocado en 3.365 frames (36,2 %).

Antonio proponía cerrar: con la cota de la DFL (`validation/posesiones_cortas/BITACORA.md`, pista de
transiciones), una pista así daría como mucho de +0,02 a +0,03, por debajo del +0,03 de §5.8. Se prueba de
todos modos porque ese umbral es para medidas del harness, el mecanismo está comprobado en el partido y en
esa cota ninguna combinación hacía daño. La ganancia esperada es pequeña (en torno a +0,01 o +0,02) y no se
puede medir en otros partidos, que no tienen Smart Tagging.

Qué se hace:
- Antonio escribe una función nueva en `possession/` que suma un peso a la columna del equipo de la fase
  durante los primeros segundos de cada «Attacking Transition». Un solo peso y un solo tope, escritos y
  razonados antes de generar nada.
- La sesión de integración la enchufa como capa de prueba (`--capa`), sin tocar `pipeline.PIECES`.
- Ismael genera la entrega de prueba, la compara con `equipo_v3` (`validation/partido/comparar_entregas.py`)
  y la valida.

Cómo termina: como una opción apagada con su comparación. Encenderla es una decisión aparte.

### 2026-11-15 · candidatos · fases del Smart Tagging: pasan la regla del plan por poco y la tabla hay que revisarla

Quién: Antonio Azuero. Un uso más amplio que el del plan lo decide Ismael.

Qué se probó: la tarea 2 de Antonio (`docs/PLAN_ENTREGA.md` §3, P7 de la revisión externa), con el sí de
Ismael (entrada «Antonio empieza su tarea 2»). Se probó si el equipo de las fases del Smart Tagging sirve de
pista en los frames sin balón.
- **La tabla de cada código al equipo con el balón,** de `OVERVIEW.md`: en las fases de ataque lo tiene el
  equipo de la fase y en las de defensa, el otro. Quedan fuera `SET PIECES`, `GOALS` y `Team = N/A`.
- **La regla** se escribió y se subió antes de ejecutar (`7d8a2ca`, `validation/fases_smart_tagging/BITACORA.md`).
  «Dobla al placebo» se lee como «el desacuerdo es, como mucho, la mitad del del placebo»; lo aceptó Ismael
  a través de Antonio.

Cómo se midió: `validation/partido/fases_smart_tagging.py`, ejecutado por Antonio en local con `equipo_v3`
(sha256 comprobado). Solo agregados del partido entero.
- **Control claro:** el mismo equipo a 1 m durante 1 s.
- **Placebo:** las fases desplazadas ±240, ±360 y ±480 s.

Resultado [medido; la salida entera está en `validation/resultados/2026-11-15_fases_smart_tagging.md`]:
- **Acuerdo en control claro: 81,8 %** (10.256 frames). El desacuerdo es del 18,2 %, frente al 44,2 % del
  placebo. **La regla del plan se cumple, por poco.**
- **Solapados con equipos distintos: 13,5 %** de los frames con fase. Pasa del 10 % de §3.2, así que hay que
  revisar la tabla antes de usar nada.
  - El sentido de ataque y defensa está bien: las fases salen a pares idénticos (cada ataque de un equipo con
    la defensa del otro).
  - Los solapes vendrían de las fases largas «de zona», como `PLAYERS IN THE BOX` o `BALL IN FINAL THIRD`
    [inferencia, sin verificar]. Esas, junto con `BALL IN THE BOX` y `CREATING CHANCES`, son las que menos
    aciertan (del 72 al 75 %). Las transiciones aciertan el 93 %, y la progresión, el 92 %.
- **Transiciones:** en 19 de los 24 inicios de `ATTACKING TRANSITION` (79 %), nuestra entrega sigue en el
  otro equipo y no cambia en ±2 s. En el placebo pasa en el 28 %. Los pocos cambios que hay llegan de +1 a
  +2 s.
- **Alcance del empujón del plan:** como mucho 1.455 frames sin balón (menos del 1 % de los evaluados) tienen
  nuestra etiqueta del otro equipo y una fase.

Decisión y por qué:
- **Según la regla, entra, pero no se enciende nada todavía.** §3.2 pide revisar la tabla antes. La revisión
  que falta es un agregado: los solapes por pareja de códigos.
- **Con el alcance del plan, la pista vale poco:** no más de 1.455 frames. Cuadra con la medida en la
  Bundesliga, según la cual «este equipo tiene el balón» apenas ayuda con ese alcance.
- **Lo que más promete son los contraataques,** porque llegamos tarde o no llegamos a casi 4 de cada 5. Un
  empujón al inicio de las `ATTACKING TRANSITION` se sale del plan: **lo decide Ismael**. Antes convendría
  medir cuánto tarda nuestro cambio después de esos inicios.
- La entrega no cambia.

Descartado, de momento:
- elegir solo los códigos que más aciertan: sería decidirlo después de ver los números;
- copiar las fases como etiquetas (decisión del 15/11).

### 2026-11-15 · candidatos · fases del Smart Tagging, revisión: la tabla vale y en los contraataques llegamos 2–10 s tarde

Quién: Antonio Azuero. Lo que se le propone, lo decide Ismael.

Qué se probó: el recuento de revisión de `validation/fases_smart_tagging/BITACORA.md` §7. La regla se subió
antes de ejecutar (`95e766a`). Tiene dos partes:
- cerrar la revisión de la tabla que pedía la entrada anterior;
- medir cuánto tardamos en los contraataques.

Cómo se midió: `validation/partido/fases_smart_tagging_revision.py`, ejecutado por Antonio en local con
`equipo_v3`. Solo agregados, frente a los mismos inicios desplazados.

Resultado [medido; salida en `validation/resultados/2026-11-15_fases_smart_tagging.md`]:
- **La tabla vale:** en el 95,3 % de los 14.610 frames solapados interviene una fase de zona (`PLAYERS IN THE
  BOX`, `BALL IN FINAL THIRD` o `BALL IN THE BOX`), y la regla pedía el 70 %. La fase de zona del equipo que
  atacaba sigue abierta cuando el otro arranca [inferencia].
- **Contraataques:** de los 24 inicios de `ATTACKING TRANSITION`, nuestra etiqueta pasa a ese equipo entre 2 y
  5 s después en 11, y entre 5 y 10 s en 6. Menos de 5 ya lo eran o llegan antes de 2 s. En el placebo, lo
  normal es no llegar en 15 s (51,9 %).
- **Dentro de esas fases** vamos con el otro equipo en el 36,2 % de los frames (3.365); en el placebo, en el
  23,6 %. Donde el balón está claramente en los pies del equipo que contraataca, coincidimos en el 95,7 %.

Decisión y por qué:
- **La revisión de la tabla se cierra:** vale tal cual, excluyendo los solapados. Con la regla del plan ya
  cumplida, el empujón pequeño (solo sin balón, como mucho 1.455 frames) se puede escribir como módulo aparte
  para que lo enchufe Ismael. Vale poco.
- **Se le propone a Ismael medir un empujón al inicio de las `ATTACKING TRANSITION`,** como pide la lectura
  de §7.2: el 83 % de los inicios espera más de 2 s (el placebo, el 70 %, casi todo sin llegar) y el 36 % de los
  frames va con el otro equipo.
  - Es más que el empujón del plan: 3.365 frames, justo al empezar posesiones.
  - Se sale del alcance del plan.
  - No se puede medir en la DFL. Una cota sería simular el empujón en el harness con las recuperaciones de los
    eventos humanos de la DFL.
- La entrega no cambia.

Límite: el inicio que marca el Smart Tagging no es la GT. Si fuera antes de la recuperación real, parte de la
espera no sería un retraso.

**Junto con la cota de la DFL** (entrada «posesiones cortas, fase 4»; bitácora §9):
- Una pista perfecta que marque las 24 transiciones, con peso 8 en todos los frames, daría de +0,021 a +0,027
  si cae en cambios que `main` no ve [medido allí, cota superior]. Según nuestros recuentos, es justo el caso
  del partido: 19 de 24 sin cambio a ±2 s, y de 2 a 10 s tarde [medido aquí].
- **Ni así llega al +0,03 de §5.8,** y el empujón del plan, solo sin balón, se queda en ±0,008 [inferencia, al
  juntar las dos medidas].
- **Propuesta: cerrar la tarea 2 sin encender nada.** Con las normas del 15/11, la decisión es del equipo y la
  puede tomar Antonio.

### 2026-11-15 · candidatos · el empujón en los contraataques: peso 8 y tope de 5 s, fijados antes de generar nada

Quién: Antonio Azuero, con el «si a todo» de Ismael (entrada «se prueba un empujón al equipo de la fase en los
contraataques»). La entrega de prueba la genera y la compara la sesión de integración de Ismael.

Qué se hace: una capa nueva, `possession/transiciones.py`, con la firma de la de Manuel:
`evidence(trk, paths=None, game=games.GAME)`, que devuelve `(score, allowed)`. **No se enchufa en
`pipeline.py`:** se prueba con `--capa transiciones.evidence`, como opción apagada.
- **Sin `paths` no opina** (todo a cero y todo permitido). Así, en la DFL y en `prueba_pipeline.py`, no cambia
  nada.
- **Solo `ATTACKING TRANSITION`,** con `Team` `Barcelona` (`H`) o `Atletic Club` (`A`). Las demás fases no
  entran, y menos las de zona, que son las que se solapan con equipos distintos. `N/A` no entra.
- **Qué suma:** el peso a la columna del equipo de la fase, desde el frame de inicio y durante el tope, sin
  pasar del final de la fase ni del tramo evaluado. Solo cuentan las fases que empiezan en un tramo evaluado.
- **Y el mismo peso a la columna `D` en esos frames.** Lo señaló el agente revisor, antes de generar nada.
  - Solo cuentan las diferencias entre columnas: sumar solo al equipo también empujaría 8 por frame contra `D`.
  - La cota de la DFL se midió con el `D` impuesto (`d_oraculo` en `validation/harness/puntuar.py`: `D`
    prohibido en el juego y obligado en las paradas). Así que no vio ese efecto, y con el `D` impuesto la
    columna `D` no cambia nada. **Con esto la capa hace exactamente lo que midió la cota:** empuja contra el
    otro equipo y no opina entre jugar y parar.
  - En el partido el `D` es blando (`dead_state` y la capa del hueco), y sin esto podría borrar o acortar una
    parada que cayera en esos 5 s si la fase no acaba justo en el fuera.
  - Se aparta un poco de «sumar un peso a la columna del equipo». Lo que llega a la diferencia entre `H` y
    `A` es igual.
- Un frame cubierto por dos transiciones del mismo equipo recibe el peso **una vez**, no dos. Si lo cubren
  dos de equipos distintos, lo reciben las tres columnas y la capa no opina.
- **No prohíbe nada:** `allowed` va todo a `True`.
- **Con `paths` y sin ninguna transición con equipo, da error:** si los nombres de `Team` no coincidieran, la
  capa no haría nada sin avisar.

**El peso y el tope, uno de cada, razonados antes de generar nada:**
- **Peso: 8 por frame.**
  - Es el mayor de la rejilla de la cota de la DFL (`validation/posesiones_cortas/BITACORA.md` §13: w = 1, 2, 4
    y 8) y el único con el que la cota se acercaba a algo (de +0,021 a +0,027 con marcas perfectas en cambios
    que `main` no ve). Con 4 daba poco más de la mitad.
  - **En esa cota ninguna combinación hizo daño, ni con un 30 % de marcas falsas** (q = 0,7). Aquí la
    etiqueta acierta el 93,1 % en control claro (q ≈ 0,9).
  - En la escala del decodificador, 8 por frame durante 5 s suman 1.000 frente a un coste de cambio de 25: la
    capa fuerza el cambio al equipo de la fase frente al otro, salvo que B5 diga lo contrario con mucha fuerza.
- **Tope: 5 s (125 frames) desde el inicio de la fase,** o hasta su final si dura menos.
  - Es el tope de la marca en la cota de la DFL, que duraba lo que la posesión real con un máximo de 125
    frames. Aquí el final de la fase hace de final de la posesión.
  - No se alarga: la cota de la DFL no midió marcas más largas, y una transición mal marcada haría más daño
    cuanto más dure.
- **De contexto, no de motivo:** el recuento de las fases dice que llegamos de 2 a 10 s tarde en 17 de 24
  contraataques (de 2 a 5 s en 11). Explica por qué se prueba, no por qué se eligieron 8 y 5 s, que salen de la
  cota de la DFL.
- **Ninguno de los dos sale del partido ni de la ventana pública,** y no se retocan después de generar la
  entrega de prueba.

Cómo se probará: no se puede medir en la DFL, que no tiene Smart Tagging. La sesión de integración genera la
entrega de prueba con `--capa transiciones.evidence`, la compara con `equipo_v3`
(`python validation/partido/comparar_entregas.py equipo_v3 <la de prueba>`) y la valida.

**Cómo se leerá la comparación** (fijado antes de generar, como en D7). Con lo que imprime `comparar_entregas.py`:
1. **Casi todo es un cambio de equipo:** de los frames evaluados que cambian, el 90 % o más pasan de `H` a `A` o
   de `A` a `H`. Con la capa neutra frente a `D`, los cambios entre `D` y juego solo pueden venir de arrastre
   del decodificador.
2. **Las paradas no se mueven:** el número de paradas cambia en 2 como mucho.
3. **No fragmenta:** las posesiones suben 24 como mucho, una por transición. Si la fase marca un contraataque que
   ya veíamos, solo se adelanta el cambio y el número no se mueve. Si marca uno que no veíamos, o uno falso, se
   añaden una o dos.
4. **Tamaño:** como mucho cambian 5.000 frames evaluados (el 3,1 %). Los frames con el otro equipo dentro de las
   fases de transición son 3.365, y el resto es margen para el arrastre del decodificador.

**Si falla alguna, se queda apagada** y se apunta por qué. Si pasan las cuatro, **sigue apagada** hasta que el
equipo decida encenderla. Sería una excepción a «lo que no ha ganado en el harness no entra» (plan §4), porque
esta capa no se puede medir en la DFL, y esa excepción la decide el equipo (normas del 15/11). La ventana pública
tampoco elige: solo dice si algo se ha roto.

**Una excepción al contrato de las piezas:** `possession/tracking.py` y `docs/PLAN_ENTREGA.md` §2 dicen que
ninguna pieza abre ficheros salvo `dead_ball.py`. Esta es la segunda que abre los del partido: solo con `paths`,
que solo le da `pipeline.build` cuando una persona genera una entrega. Sin `paths` no abre nada, y el harness no
le pasa rutas. Habría que añadir la excepción a esos dos textos, que son de Ismael.

Descartado:
- **un peso o un tope por código, por equipo o por duración de la fase:** «un solo peso y un solo tope»;
- **usar las `DEFENSIVE TRANSITION`:** son el espejo exacto de las de ataque (§6 de la bitácora de las fases) y
  no añaden nada;
- **prohibir el otro equipo en `allowed`:** una fase mal marcada no se podría corregir.


### 2026-11-15 · `D` · D7, segunda versión: mantener la parada hasta que el balón vuelva a verse dentro (antes de generar)

Quién: Ismael la pidió por la sesión principal («Sí, pídela»). Claude la escribe. **Es la segunda versión, y se
diseñó después de ver el resultado de la primera** (entrada «D7» de más arriba: con `prueba_d7` llegamos tarde
en 12 de 47 rachas, frente a 23 sin la capa, y en 7 nuestro `D` no llega en 10 s). Es el segundo intento, y no
habrá un tercero con estos criterios.

Por qué: la primera versión solo puntúa mientras el balón se ve fuera. Si se ve fuera un momento y después el
ATD lo pierde, como en el saque de puerta que vio Ismael, el `D` no llega. Por el reglamento, un balón que ha
salido no vuelve al juego sin un saque.

**La capa, `dead_ball.ball_out_hold`,** una función nueva al final de `possession/dead_ball.py`, apagada. No
toca las líneas que ya había, ni `pipeline.build`, ni `PIECES`.
- **Lo mismo que la primera versión**, con el mismo peso (5) y la misma cola (16 frames).
- **Además, en cada racha visible de 25 frames (1 s) o más con el balón fuera,** mantiene el peso en `D`
  mientras el balón no se ve o se ve fuera, hasta 16 frames antes de que vuelva a verse dentro (a 1 m o menos
  de las líneas).
- **Tope:** si el balón no vuelve a verse dentro en 60 s, o se acaba el tramo, no se mantiene. Es el tope de
  la capa del hueco de Manuel.
- **Por qué 1 s de racha visible:** es el riesgo de una parada falsa, un balón visto fuera por error y perdido
  justo después.
  - En SkillCorner (mitad de entrenamiento), las rachas enteras en juego de 1 s o más son 7 en 10 partidos
    (0,7 por partido): menos de una por partido aunque todas acabaran con el balón perdido. Con 5 frames
    serían 26–45, de 2,6 a 4,5 por partido.
  - En el partido, el ATD casi no pierde el balón en pleno juego: 37 huecos
    (`validation/resultados/2026-11-15_huecos_y_cambios.md`).
  - No se ha fijado con el resultado de la primera versión.
- **En el hueco el empujón es más fuerte que con el balón a la vista:** sin balón, B5 no da el +1 de N1, así
  que cada frame suma `5 + ds` hacia `D`. Por eso la racha mínima: sin ella, un balón perdido tras un error de
  un instante crearía una parada.

**Cómo se mide: los mismos tres criterios que la primera, sin tocar los umbrales,** con la entrega de prueba
`prueba_d7b`. Ahora se genera y se mide con un solo comando, que ejecuta Ismael:
`python validation/partido/probar_entrega.py prueba_d7b --capa dead_ball.ball_out_hold`.
1. llegamos tarde en menos del 15 % de las rachas;
2. el `D` no pasa del 60 % de los frames evaluados, hay como mucho 250 paradas y como mucho 15 más que en
   `equipo_v3` (113);
3. el 80 % o más de los frames que cambian frente a `equipo_v3` pasan de `H` o `A` a `D`.

Si se cumplen los tres, se propone encenderla: se añade a `pipeline.build`, se regenera la entrega en el
entorno limpio, se valida y se apunta la huella. Si no, se queda apagada y D7 se cierra aquí.

En la DFL [medido, con el `D` propio en las dos condiciones que votan]: cambian 23 frames de 2.012.288, los mismos que con la primera versión. Con el balón tapado en
los `D`, como se esperaba. No es una ganancia.

**Resultado de `prueba_d7b`** (15/11; la generó Ismael con `validation/partido/probar_entrega.py` y el código de
`0043a3c`, sin cambios locales) [medido, solo agregados]: **sale byte a byte igual que `prueba_d7`** (sha256
`eb244885…4f7f`). Mantener la parada en el hueco no cambia ninguna etiqueta del partido.
1. Llegamos tarde en 12 de 47 rachas (25,5 %), y en 7 nuestro `D` sigue sin llegar en 10 s: **no se cumple.**
2. Se cumple: 116 paradas, 3 más, y el `D` en el 45,4 %.
3. Se cumple: los 574 frames que cambian frente a `equipo_v3` pasan de `H` o `A` a `D`.

**Decisión, con la regla fijada antes: la segunda versión se queda apagada y D7 se cierra aquí.** Las dos capas
siguen en `possession/dead_ball.py`, apagadas, con su evidencia.

[inferencia, sin medir] En las 7 rachas que quedan, o el balón se ve fuera menos de 1 s antes de perderse, o
no vuelve a verse dentro en 60 s. No se mide, porque D7 está cerrada.

### 2026-11-15 · candidatos · el empujón en los contraataques: la primera versión crea paradas; segunda versión, solo al equipo

Quién: lo prueba la sesión principal de Ismael (Claude), con su encargo del 15/11: «haz todo lo que necesites no
dependas de que yo te diga que si a las cosas». La capa es de Antonio (PR 14).

**Resultado de la primera versión** (`transiciones.evidence`; entrega de prueba `prueba_transiciones`, generada
por Ismael con `main` en `9f89d10`; solo agregados) [medido]:
- cambian 2.202 frames evaluados (el 1,386 %): de `H` a `A` 171, de `A` a `H` 226, de `H` a `D` 660 y de `A` a
  `D` 1.145;
- las posesiones pasan de 215 a 219 y las paradas de 113 a 131. Aparecen 2 paradas y 1 posesión de menos de 25
  frames;
- **con los cuatro criterios escritos antes, fallan dos:** el 1 (el 18 % de los cambios son de equipo; se pedía
  el 90 %) y el 2 (18 paradas más; se pedían 2 como mucho). Pasan el 3 (4 posesiones más) y el 4 (2.202 frames).
  **Se queda apagada.**

**Por qué crea paradas** [inferencia, con el código]:
- B5 no premia al equipo que prefiere: resta al otro. En `possession/aprendida.py`, la columna del equipo que B5
  no prefiere lleva −α·|z|, y la del que prefiere, 0.
- Donde B5 prefiere al otro equipo, la columna del equipo de la fase queda por debajo de la de `D`, que en el
  juego vivo ronda −3,4 (la mediana de `dead_state` en la DFL, entrada de D7).
- Al sumar 8 a las dos, `D` queda por encima del equipo de la fase y también del otro, y el decodificador elige
  `D`. La capa «neutra frente a `D`» le daba la ventaja a `D`.

**Segunda versión, `transiciones.evidence_equipo`,** escrita antes de generar ninguna entrega con ella:
- lo mismo que la primera, pero el peso va **solo a la columna del equipo de la fase.** Es lo que se pidió al
  principio y lo que hacía la pista de la cota de la DFL (`validation/posesiones_cortas/BITACORA.md` §13);
- el mismo peso (8) y el mismo tope (5 s). No se tocan;
- **el riesgo,** el que señaló el revisor de la PR 14: también empuja contra `D`, así que puede acortar una
  parada que caiga en esos 5 s, por ejemplo una falta que corta el contraataque. Lo vigila el criterio 2;
- **los mismos cuatro criterios, con los mismos umbrales.** Si falla alguno, se queda apagada;
- es la segunda versión y se diseñó después de ver el resultado de la primera. Si no pasa, la idea se cierra:
  no se prueba otro peso ni otro tope.

Cómo se prueba (lo ejecuta Ismael):
`python -m possession.pipeline --name prueba_transiciones2 --capa transiciones.evidence_equipo` y
`python validation/partido/comparar_entregas.py equipo_v3 prueba_transiciones2`.

Si pasa los cuatro, sigue apagada: encenderla es una decisión aparte, y obliga a regenerar y validar la entrega.

**Resultado de la segunda versión** (`prueba_transiciones2`; la generó Ismael con
`validation/partido/probar_entrega.py` y el código de `5920c7f`, sin cambios locales; sha256 `27dc8aa8…efb7`)
[medido, solo agregados]: **pasa los cuatro criterios.**
1. Cambian 817 frames evaluados, todos de un equipo al otro: 274 de `H` a `A` y 543 de `A` a `H`. Es el 100 %, y
   se pedía el 90 %.
2. Las paradas no se mueven: 113 y 113. Se permitían 2 de diferencia.
3. Las posesiones pasan de 215 a 219: 4 más, y se permitían 24.
4. Cambian 817 frames, el 0,514 %, y se permitían 5.000.

No hay rachas de menos de 25 frames ni piezas en conflicto, y todos los cambios caen a más de 250 frames de un
borde.

Con la regla, **sigue apagada hasta que el equipo decida encenderla.** Sería una excepción a «lo que no ha
ganado en el harness no entra», porque esta capa no se puede medir en la DFL.


### 2026-11-15 · candidatos · se enciende la capa de los contraataques (`transiciones.evidence_equipo`)

Quién: Ismael («Sí, enciéndela»), con la recomendación de Claude, después de que la segunda versión pasara sus
cuatro criterios (entrada «el empujón en los contraataques: la primera versión crea paradas»).

Qué se decidió: **la entrega suma `transiciones.evidence_equipo`.** Es una excepción a «lo que no ha ganado en el
harness no entra» (plan §4), que la regla de la capa dejaba en manos del equipo. La DFL no tiene Smart Tagging,
así que el harness no puede medirla.

Por qué se recomendó:
- **Hace lo que se buscaba.** En 17 de 24 contraataques llegábamos de 2 a 10 s tarde, y la capa adelanta el
  cambio al equipo de la fase.
- **Pasó los cuatro criterios escritos antes:**
  - los 817 frames que cambian son todos de un equipo al otro;
  - las paradas no se mueven y hay 4 posesiones más;
  - no hay rachas cortas.
- **En la cota de la DFL nunca hizo daño,** ni con un 30 % de marcas falsas, y aquí la etiqueta de equipo de
  las fases acierta el 93,1 % en control claro.
- **La ganancia esperada es pequeña:** de +0,013 a +0,027 como cota superior con marcas perfectas. No se ha
  medido con el `spellF1` del partido, ni se puede.

Qué cambia:
- **`possession/pipeline.py`:** `DELIVERY_LAYERS = (transiciones.evidence_equipo,)`. `build` la suma a las anclas
  de `dead_ball.evidence`, con las rutas del partido. `PIECES` y `run` no cambian, así que el harness y la DFL
  siguen igual.
- **La excepción de que la capa abre el Smart Tagging,** escrita en `possession/tracking.py`, en el plan (§2) y
  en `CLAUDE.md`.
- **La entrega cambia:** hay que regenerarla en el entorno limpio. Tiene que salir igual que `prueba_transiciones2`
  (sha256 `27dc8aa8…efb7`, generada con numpy 2.3.4), con 817 frames distintos frente a `equipo_v3`. Pasará a ser
  la entrega vigente, y la comprobación del lunes por la noche se hace con ella.

Resultado (15/11) [medido por Ismael]: **`equipo_v5`, la entrega vigente.**
- Se regeneró en el entorno limpio (Python 3.13.9, numpy 2.5.4) con `main` en `2f34a7f`, sin cambios locales.
- Sale con el sha256 `27dc8aa8…efb7`, byte a byte igual que `prueba_transiciones2`.
- Frente a `equipo_v3` cambian 817 frames, todos de un equipo al otro. Las paradas siguen en 113, y las
  posesiones pasan de 215 a 219.
- El validador oficial la da por válida.
- Con `main` en `b027409` (PR 15 y PR 10 de David y PR 16 de Manuel y Ana), `equipo_v7` sale con el mismo
  sha256, en el entorno limpio y validada [medido por Ismael].
- Reproducida en otra máquina con el mismo resultado (Ismael, 16/11: «ha dado lo mismo»).

### 2026-11-15 · `D` · el instante del reinicio: regla escrita antes de medir

Quién: Manuel, en el orden de prioridades que fijó Ismael el 15/11 (primero el instante del reinicio,
después el equipo que reanuda; ni las paradas tras gol ni el final de cada parte).

Por qué: cada final de parada es el principio de una posesión, y llegar 1 s tarde cuesta mucho `spellF1`.
En la DFL, el modelo de Ana (E2) acaba la parada a 25 frames o menos en el 40 % de los casos, con un sesgo
mediano de +17 frames [medido en la DFL; entrada «`D` · estado con jugadores: resultado de la medida», 14/11].

**Cambia dos cosas escritas, por decisión de Ismael.**
- **La decisión del 14/11.** Ese día se escribió: «No se va a medir dónde cae el golpeo dentro de la ventana
  para fijarlo: sería circular (el golpeo no se ha validado) y daría una constante sacada del partido».
- **`docs/PLAN_ENTREGA.md` §2:** «Ninguna constante sale del partido ni de la ventana pública. Los umbrales
  se fijan en la DFL».

Lo que hay a favor: la parte de Manuel en el mismo plan (§3) pide el fin del `D` «dentro de cada ventana
`SET PIECES`, con lo que digan los agregados». Y dice que lo que usa el Smart Tagging se comprueba en el
partido con agregados, porque la DFL no lo tiene. El mensaje de Ismael del 15/11 lo pide así: «Si cae en un
sitio fijo con poca dispersión, ancla ahí el final del D». La excepción a §2 es suya, y la confirma o no al
revisar la PR.

Frente a lo del 14/11 hay dos diferencias:
- **no se usa el golpeo,** sino dos señales que no son etiquetas ni dependen de él: cuándo vuelve a verse el
  balón y cuándo el modelo de Ana (entrenado en la DFL) pasa de parado a juego;
- **lo que sale no es un frame del partido,** sino un desfase desde el inicio de la ventana, uno por tipo de
  reinicio.

Sigue siendo un parámetro estimado con este partido, sin etiquetas. Se declara así, y no se ajusta nada con
la ventana pública.

Qué se va a medir: `validation/partido/agregados_instante_reinicio.py`, que ejecuta Manuel. Una sola
ejecución mide las señales, aplica la regla, comprueba las condiciones del candidato A y prueba los
candidatos en el pipeline.
- **Las ventanas:** las `SET PIECES` que no son saques iniciales y empiezan en un tramo evaluado (53 en este
  partido). Los saques iniciales quedan fuera: el de cada parte ya tiene su ancla, y los de después de un
  gol son 4.
- **Las señales** se buscan desde el inicio de la ventana hasta 10 s después de su fin, sin pasar del inicio
  del siguiente `GOALS` o `SET PIECES`:
  - **el modelo de Ana pasa a juego:** el primer frame con log-odds > 0 en el anterior y < 0 durante los 2 s
    siguientes. El frame tiene que caer antes del corte; los 2 s de sostén pueden pasar de él;
  - **el balón vuelve a verse:** si no se veía en el frame anterior al inicio de la ventana, el primero en
    que se ve. Si se veía, no cuenta.
- **Desde el inicio o desde el fin:** las ventanas duran 35 s fijos [medido, 14/11], así que la dispersión
  es la misma. Se mide desde el inicio. Para comprobarlo, el script imprime la duración mediana y cuántas
  ventanas se apartan de ella más de 1 s.
- **Todo se cuenta en frames** y se imprime en segundos. Así una frontera exacta (25 o 50 frames) no falla
  por la coma flotante, como pasaría al restar segundos (55/25 − 30/25 da algo más de 1).

Regla de lectura, fijada antes de ejecutarlo:
- **Un tipo de reinicio tiene ancla si se cumplen las cinco cosas:**
  - hay 10 ventanas o más con la transición del modelo de Ana;
  - su recorrido intercuartílico es de 2 s (50 frames) o menos, así que la mitad de las ventanas cae en 2 s;
  - hay 5 ventanas o más en las que vuelve a verse el balón, y la mediana de esa reaparición queda a 1 s
    (25 frames) o menos de la mediana de la transición. Son dos señales independientes que señalan el
    mismo sitio;
  - **el ancla fija gana a la señal de cada ventana:** en las ventanas con las dos señales (5 o más), la
    distancia mediana del balón al ancla es menor que la distancia mediana del balón a la transición de su
    propia ventana. Si la dispersión de la transición fuera real (saques rápidos y lentos), una constante
    movería la mitad de las salidas un segundo o más; esta condición exige que, por lo menos, no se aleje de
    la otra señal. Un empate no basta;
  - **el placebo no se concentra** (lo pide el plan del 15/11 para cada capa):
    - son las mismas ventanas desplazadas ±4, 6 y 8 minutos, como el placebo de la capa del hueco;
    - solo cuentan las que empiezan en un tramo evaluado y lejos de cualquier `GOALS` o `SET PIECES` real
      (a más de su duración más 10 s, antes o después);
    - si la transición del modelo de Ana en el placebo también tiene 10 casos o más con recorrido de 2 s o
      menos, la concentración de las ventanas reales no dice nada, y el tipo se queda sin ancla.

  Los tipos con menos de 5 ventanas van juntos en «otros», sin ancla.
- **El juez.** El plan pide el modelo de Ana como juez, pero aquí da una de las dos señales; la que confirma es
  la otra, el balón. No hay un juez aparte.
- **El ancla** es la mediana de la transición, en frames desde el inicio de la ventana.
- **Los dos candidatos de la capa** (mensaje de Ismael del 15/11: «ni A ni B a ciegas»):
  - **comunes a los dos:**
    - empuje blando y corto, con la escala que tenía `GAP_SCORE` el 15/11 (1 por frame), sin prohibir nada.
      Queda fijada por esta regla: si `GAP_SCORE` cambia, esta no cambia sola;
    - se cortan en el siguiente `GOALS` o `SET PIECES`;
    - una ventana no recibe nada si el instante cae en ese corte o después, o si otro reinicio empieza en
      el mismo frame;
  - **candidato 1, B:** solo en las ventanas con hueco (las que puntúa la capa del hueco), +1 en `D` desde el
    inicio de la ventana hasta el instante. Alarga el `D` del hueco hasta el instante, y nada más;
  - **candidato 2, A:** en todas las ventanas del tipo:
    - +1 en `D` antes del instante. En las ventanas con hueco empieza en el inicio de la ventana, como en B;
      en las demás solo cubre los 3 s anteriores al instante;
    - −1 en `D` durante los 3 s siguientes.
  - **Los 3 s de cada lado** están sin ajustar y quedan fijos por esta regla. Son a priori: cubren el segundo
    de margen que se le exige al instante en A.
  - **En las ventanas con hueco,** el empuje antes del instante dura lo que el ancla, porque alargar el `D`
    del hueco hasta el instante es justo eso. El mensaje solo pide recortarlo en las ventanas sin hueco.
- **Un tipo con ancla cumple A si además se cumplen tres cosas, con estos números:**
  1. **El instante es nítido:** el 80 % de las ventanas del tipo tiene la transición a menos de 1 s
     (25 frames) de la mediana. Las ventanas sin transición cuentan como lejos. Con menos de 10 ventanas no
     hay ancla, así que un tipo con pocos casos no entra por separado (las faltas son 5).
  2. **El modelo de Ana está de acuerdo a los dos lados del instante,** con el criterio del punto medio de
     la capa del hueco:
     - se compara con tres proporciones de `D` del modelo de Ana:
       - la del partido, en lo evaluado;
       - la del control de `D`: el tramo antes del saque de la 2ª parte, `D` según el FAQ;
       - la del control de juego: los frames evaluados a más de 60 s de cualquier `GOALS` o `SET PIECES`
         (antes de su inicio o después de su fin). Es el mismo horizonte que el hueco más largo de la capa
         del hueco, y no usa etiquetas. Incluye paradas que el Smart Tagging no marca (solo trae 5 faltas),
         así que es un control de juego imperfecto: si no queda por debajo del partido, el instrumento no
         separa y A no entra. El balón deprisa no sirve: no separa `D` de juego en este partido (46,7 % frente
         a 50,5 %, entrada «fronteras y anclas» del 15/11);
     - el instrumento tiene que separar: el control de `D` por encima del partido y el control de juego por
       debajo;
     - en los 3 s anteriores al instante, la proporción de `D` queda en el punto medio entre el partido y el
       control de `D`, o por encima;
     - en los 3 s siguientes queda en el punto medio entre el partido y el control de juego, o por debajo;
     - se mide por separado en las ventanas con hueco y en las demás, casi todas con el balón a la vista
       hasta el inicio. Cada grupo necesita 5 ventanas o más, y los dos tienen que cumplirlo: las segundas
       son las que A añade y las de más riesgo.
  3. **El placebo no pasa:** se toman los mismos instantes en las ventanas desplazadas del placebo de
     arriba, todas juntas (sin separar por grupos) y 5 o más. Si ahí la proporción de `D` también cumple el
     punto medio a los dos lados, el acuerdo de las ventanas reales no dice nada.
- **La condición de daño** de cada candidato que se prueba, con el pipeline de la entrega sin la capa y con
  ella:
  - ningún frame con piezas en conflicto;
  - **ninguna ventana que recibe la capa queda partida por ella:** con la capa tiene dos tramos de `D` o más,
    y más de los que tenía sin ella.
    - Los tramos se cuentan desde el inicio de la ventana hasta 10 s después de su fin o del fin de la capa,
      lo que llegue más tarde, sin pasar del siguiente reinicio.
    - Así se ve si el `D` sale en el instante y vuelve donde acaba la capa (`D`, 3 s de juego y otra vez `D`):
      esa parada partida añade una posesión.
    - Pasar de ningún tramo a uno no cuenta: es lo que hace la capa cuando alarga hasta el instante un `D`
      que acababa en el inicio de la ventana (por ejemplo, el de la capa del hueco);
  - las posesiones no suben más que las paradas (cada posesión nueva tiene que venir de una parada nueva
    que la parte);
  - **la entrega con la capa queda dentro de la banda del plan** (§3, 15/11): del 15 al 60 % de `D` en lo
    evaluado y 250 paradas como mucho.
- **Qué entra, en este orden:**
  1. **Si algún tipo cumple A,** se prueba el candidato A: A en esos tipos y B en los demás tipos con ancla.
     Entra si alguna ventana recibe la capa y se cumple la condición de daño.
  2. **Si no,** se prueba B en todos los tipos con ancla, con la misma condición.
  3. **Si tampoco,** no entra nada.

  Con esta salida no se reajusta nada: ni los 2 s, ni las 10 y 5 ventanas, ni el 1 s, ni los 2 s de sostén,
  ni los 10 s de búsqueda, ni el placebo, ni la banda, ni el 80 %, ni los 3 s de cada lado, ni las
  puntuaciones.
- **Si entra uno,** y solo entonces, el script imprime los desfases en frames y el modo de cada tipo, listos
  para copiar. Cómo se conectan en `evidence` lo decide Ismael:
  - copiando la constante en `possession/dead_ball.py`, que es la excepción a §2;
  - o calculando el ancla al ejecutar, con estas mismas funciones.

  La medida es la misma en los dos casos. Después se regenera la entrega y se comprueba que no hay
  conflictos y que sigue dentro de la banda.
- **Con qué se midió:** el script imprime:
  - las piezas del pipeline (`pipeline.PIECES`, con la limpieza del balón) y los costes del decodificador
    (`temporal.DEFAULTS`);
  - una huella del modelo de Ana (`dead_state.MODEL`);
  - una huella del código de `possession/`.

  Si antes de que la capa entre cambian la limpieza o el modelo de Ana, se repite todo con esta misma regla.
  Si cambian la evidencia de equipo o los costes, se repite por lo menos la sección 3 (el daño). **→ Ya no: el
  veredicto quedó cerrado y este script no se repite por ninguna de esas causas** (Manuel, 15/11; entrada
  «cierres de la pieza de Manuel»).
- **Descriptivo, no decide:**
  - los cuantiles de las dos señales por tipo, solo con 10 ventanas o más: con menos serían ventanas sueltas;
  - cuántas ventanas tienen el balón visto al empezar;
  - la distancia entre las dos señales, y la del balón al ancla fija;
  - cuántas salidas del `D` del pipeline caen a 1 s o menos del instante, sin la capa y con ella;
  - cuántos frames evaluados cambian antes del instante, después y fuera de la capa, por tipo de cambio
    (lo que pidió Ismael);
  - las proporciones de `D` del modelo de Ana a cada lado del instante, por grupo y en el placebo.
- **Lo que espero [inferencia]:**
  - **Con los recuentos ya medidos** (15/11, entrada «fronteras y anclas»: con hueco, banda 13 de 26, córner
    11 de 12, saque de puerta 2 de 10), A solo puede entrar en los saques de banda. Los córners tienen
    1 ventana sin hueco y los saques de puerta 2 con hueco, menos de 5 en un grupo: en ellos A no entra, y
    como mucho reciben B. En los saques de banda es justo donde el modelo de Ana ve peor la parada.
  - Con 10 ventanas como mínimo, solo pueden tener ancla los saques de banda (26), los córners (12) y los
    saques de puerta (10, y tendrían que tener transición las 10). Las faltas (5) nunca.
  - Los saques de banda y de puerta pueden quedarse sin ancla. Antes de ellos la velocidad media de los
    jugadores casi no baja: está por debajo de 1,2 m/s en el 44 % y el 36 % de los frames, frente al 91 %
    antes de un córner (entrada «el estado con jugadores (E2) entra por defecto», 14/11). El modelo de Ana puede no llegar a decir «parado» ahí, y
    la transición faltaría o saldría dispersa.
- **Lo que no comprueba [sin verificar]:**
  - **Que las señales caigan en el reinicio de verdad.** Las dos son aproximaciones, y el balón puede volver a
    verse antes del saque (colocado) o después. Que coincidan las dos es lo único que lo apoya.
  - **El retraso que hereda el ancla.** Es la mediana de una señal que llega tarde: en la DFL, E2 acaba las
    paradas con un sesgo mediano de +17 frames (la misma entrada del 14/11 de «Por qué»). La coincidencia con el balón (25 frames) no puede ver un sesgo
    así. Si se traslada al ATD, el ancla llega unos 0,7 s tarde, y la capa solo quita la dispersión, no el
    sesgo.
  - **Corregirlo sería otra regla,** que decidirían Ismael y Ana: restar un sesgo medido en la DFL, o anclar
    en el balón. No se hace con esta salida.
  - **Que «el ancla gana» distinga siempre.** Si las dos señales son precisas y el reinicio cae siempre en el
    mismo sitio, las dos medianas se parecen y, con 5 a 13 pares, la condición sale casi a cara o cruz. En
    ese caso la capa apenas movería nada, así que perderla cuesta poco.
  - **Que el acuerdo del modelo de Ana en A sea independiente.** El instante sale de la transición del
    propio modelo, así que el punto 2 está en parte a favor por construcción. Lo que añade es mirarlo por
    grupos (con hueco y sin él). El placebo aporta poco aquí: en instantes al azar las proporciones de antes
    y de después se parecen a la del partido, así que casi nunca pasa.
  - **Que la transición sea la de esa parada.** Es la primera que aparece. Si el modelo no llega a decir
    «parado» en la ventana, puede coger un repunte suelto. Eso se ve en la dispersión: un tipo con
    transiciones así no pasa el recorrido de 2 s.
- **Los recuentos de ventanas por debajo de 5 se imprimen como «< 5»,** como en el perfil del ATD. Valen
  también para las ventanas con ancla, las que tienen más tramos de `D` y las salidas cerca del instante.
  Las duraciones solo salen como mediana y como recuento de las que se apartan.
- **El script imprime la regla aplicada.** Si lo impreso y este texto no cuadran, manda este texto.
- **Que el código aplica este texto se comprueba en el repo:** sección 11 de
  `validation/scripts/comprobar_balon_muerto.py`, con datos inventados y la apertura de ficheros
  prohibida. Comprueba:
  - que las constantes de la regla son estas, también el 5 de «otros»;
  - qué cuenta como parada partida (de 0 a 1 tramos no; de 0 o 1 a 2, sí);
  - que la huella del código sale igual con finales de línea de Windows y de Linux;
  - las señales y la regla en sus límites exactos, en frames;
  - la capa y sus cortes;
  - la condición de daño;
  - los empujes de cada candidato en las ventanas con hueco y sin él, y sus cortes;
  - el 80 % justo, el segundo justo y el punto medio a cada lado;
  - el control de juego (60 s antes y después de cada reinicio);
  - las condiciones de A una a una: no se cumple con 4 ventanas en el placebo, con el placebo pasando, con 10
    transiciones nítidas de 13 ventanas (77 %) ni con un grupo de 4; el placebo solo usa su tipo;
  - que las proporciones de grupos de menos de 5 ventanas se impriman como «—»;
  - partidos de punta a punta (12 saques de banda, 6 con hueco y 6 con el balón a la vista):
    - con el instante nítido y el modelo de Ana de acuerdo: entra A, y lo que cambia cae después del
      instante;
    - con el instante borroso: entra B, que alarga el `D` del hueco y no toca las ventanas sin hueco;
    - con el modelo de Ana sin ver parado antes del instante en las ventanas sin hueco: entra B;
    - con el placebo de A pasando (aunque el de la transición no se concentre): entra B;
    - con solo 2 ventanas sin hueco: ese grupo no puede avalar A, y entra B;
    - sin ninguna ventana con hueco y con el instante borroso: B no recibe ninguna ventana y no entra nada;
    - con la parada partida en dos ventanas, y con una posesión nueva sin parada: A no entra y entra B;
    - con dos ventanas que ya tenían dos tramos de `D` sin la capa, que A no empeora: entra A;
    - con la entrega fuera de la banda: ninguno; justo en su borde (A la saca, B no): entra B;
    - con conflictos: ninguno;
    - con el reinicio disperso, con tres tipos de 4 ventanas y con el siguiente reinicio cortando la
      búsqueda: sin ancla;
    - con 10 ventanas separadas 10 minutos: sin transiciones en el placebo hay ancla; con el placebo tan
      concentrado como las reales, no.

  Romper la capa y el script a propósito (80 cambios, uno a uno, entre ellos los que las revisiones vieron
  pasar sin que fallara nada) hace fallar alguna prueba. Uno más se dejó fuera porque no cambia nada:
  medir la salida del `D` desde el primer empuje en vez de desde el inicio de la ventana. Esa salida quedaría
  a más de 3 s del instante, y el umbral descriptivo es de 1 s.

**Revisión antes de subirla (15/11).** El revisor encontró en la primera versión seis agujeros, y se
arreglaron antes de ejecutar nada:
- la parada partida no se contaba, porque los tramos de `D` se miraban solo hasta el fin de la capa;
- las fronteras se comparaban en segundos;
- el ancla podía ganar sin superar a la señal de cada ventana;
- la máscara «< 5» estaba incompleta;
- el ancla se imprimía en segundos, pero la capa espera frames;
- la sección 11 dejaba pasar 8 de sus 9 roturas: las constantes sin fijar, el frame anterior al inicio,
  los bordes de los cortes y las posesiones con y sin la capa al revés.

También pidió nombrar el choque con §2 del plan y el retraso que hereda el ancla, que van arriba.

**El plan nuevo de Ismael (15/11, tras la revisión externa)** pide para cada capa de esta pieza un placebo
desplazado y la entrega dentro de la banda. Las dos cosas se añadieron a la regla antes de ejecutar nada, igual
que el histograma de la tarea 3.

**Mensaje de Ismael (15/11), antes de ejecutar: «ni A ni B a ciegas».** La primera versión tenía una sola
forma de la capa (la que ahora es A, con 5 s después del instante). El plan del 15/11 describía otra (la que
ahora es B). Ismael pidió escribir las dos como candidatos en la misma regla, con las condiciones de A y
sus números antes de medir, y que decida la medida.

**Para que Ismael las confirme antes de ejecutar,** estas son todas las interpretaciones de su mensaje:
1. **El 80 %** («por ejemplo, el 80 %») queda fijado en el 80 %. Se cuenta sobre todas las ventanas del
   tipo: las que no tienen transición cuentan como lejos. «A menos de 1 s» es estricto (24 frames sí, 25 no).
2. **El máximo de cada lado** es de 3 s.
3. **En las ventanas con hueco,** el empuje antes del instante no tiene ese máximo: empieza en el inicio de
   la ventana y dura lo que el ancla, porque eso es «alargar el `D` del hueco hasta el instante». El máximo
   de 3 s se aplica en las ventanas sin hueco y después del instante.
4. **«Sin hueco»** es toda ventana que la capa del hueco no puntúa. Casi todas tienen el balón a la vista
   hasta su inicio (23 de 25 el 15/11); las otras 2 tenían otro reinicio dentro del hueco.
5. **Los dos grupos** (con hueco y sin él) necesitan 5 ventanas o más cada uno, y los dos tienen que
   cumplir el punto medio. La alternativa sería dar A solo al grupo que lo cumple; no se hace. Con los
   recuentos medidos, eso deja A solo para los saques de banda.
6. **El control de juego** del punto medio, que la capa del hueco no tenía, son los frames a más de 60 s de
   cualquier reinicio. La primera versión usaba el balón deprisa, que no separa `D` de juego en este
   partido (lo vio la tercera revisión).
7. **A y B se mezclan por tipo:** el candidato A lleva A en los tipos que lo cumplen y B en los demás. Si
   ese candidato no pasa el daño, se prueba B en todos; no se prueba quitando A tipo a tipo.
8. **El placebo de A** junta las ventanas desplazadas del tipo, sin separar por grupos, con 5 o más.
9. **El recuento de antes y después del instante** usa en los dos candidatos el mismo tramo de después
   (3 s), aunque B no empuje ahí.

**Tercera revisión (15/11), antes de ejecutar:**
- **El control de juego del punto medio era el balón deprisa,** que ya se había medido que no separa `D` de
  juego en este partido. Además se atribuía mal: el umbral es de la prueba de gol a saque, no de la capa
  del hueco. Ahora son los frames a más de 60 s de cualquier reinicio (punto 6 de arriba).
- **Tres condiciones sin prueba que fallara si se rompían:** el mínimo de 5 ventanas del placebo de A, que el
  80 % se cuente sobre todas las ventanas y que el placebo de A use solo su tipo. Ahora las tres tienen
  prueba (las condiciones de A van en una función, `a_conditions`).
- **Lo impreso enseñaba las proporciones de grupos de menos de 5 ventanas.** Ahora salen como «—».
- **Con B, la fila de «después del instante» salía siempre vacía.** Ahora el tramo de después es el mismo en
  los dos candidatos.
- Detalles: `restart_anchor_spans` ya no recibe `fps`, que no usaba, y `ANCHOR_SCORE` es 1 fijo, no un alias
  de `GAP_SCORE`.

**Segunda revisión (15/11), también antes de subirla y de ejecutar nada:**
- **La condición de daño contaba como parada partida el paso de 0 a 1 tramos de `D`.** Es justo lo que hace la
  capa cuando alarga el `D` del hueco hasta el instante: la habría rechazado cuando hace su trabajo. Ahora
  hacen falta 2 tramos o más, y más que sin la capa.
- **La línea para copiar las anclas salía aunque la capa no entrara.** Ahora solo sale si entra.
- **El grupo «otros» no tenía ninguna prueba.** Ahora la tiene, y la capa además exige que alguna ventana la
  reciba.
- **Lo impreso no decía con qué evidencia de equipo ni con qué costes se midió el daño.** Ahora lo dice.

Lo que pidió el revisor de la PR #8:
- **Los comentarios de `GAP_SCORE`, `LONG_GAP_S` y `MAX_GAP_BEFORE_RESTART_S`** los dejó Ismael en `main`
  (`05b6d98`), y esta rama se queda con su texto.
- **Los recuentos de casos de menos de 5** (goles, tramos, ventanas, reinicios) se tapan con «< 5» en todas
  las secciones de `validation/partido/agregados_dead_ball.py`; los frames, no.
- **Los agregados que faltaban** (tarea 3 del plan del 15/11) van como sección 4 de este script, y los dos
  son descriptivos:
  - de los frames que cambian de etiqueta con la capa del hueco, cuántos caen en los primeros 5 s de cada
    hueco;
  - un histograma grueso de la distancia entre el inicio de cada hueco y el inicio del `D` de la entrega: por
    debajo de 0 (el `D` ya venía de antes), de 0 a 1 s, de 1 a 3, de 3 a 5, 5 s o más, y sin `D`.

  Dar más peso al principio del hueco necesitaría su propia regla, escrita antes de medir.
- **Si se enciende la limpieza de Antonio** (`clean_v1`), se repiten `agregados_dead_ball.py` y este script con
  la misma regla. Los dos imprimen con qué limpieza se midió. **→ Este script ya no se repite** (cierres de la pieza
  de Manuel, 15/11); **`agregados_dead_ball.py` sí**, porque mide la capa del hueco, que está en la entrega.

Abierto:
- **El equipo que reanuda:** retirado de momento (plan del 15/11, tarea 6: la revisión externa midió en la
  DFL que `main` falla el equipo en el primer segundo tras el reinicio en el 5,5–5,7 % de los casos). Si se
  retoma: una puntuación a favor del equipo que saca durante los primeros segundos tras el reinicio, con los
  segundos medidos en la DFL. La versión medida el 15/11 (restar al otro equipo durante toda la ventana) no
  entró: está en la rama `feat/d-equipo-reanuda`, con su resultado. Allí se midió que el `Team` del Smart
  Tagging es fiable (20 de 20 con la física).

**Resultado (añadido después de ejecutarlo; lo de arriba no ha cambiado).** Lo ejecutó Manuel en local el
15/11. Apunta la lectura la sesión de Claude de Ana, que sigue la pieza desde ese día. La salida entera está en
`validation/resultados/2026-11-15_instante_reinicio.md`.
- **Con qué se midió** [medido]:
  - el script y esta regla, tal como quedaron en `569d3b4`, con el `possession/` de `main` en `98c38ca`, que
    trajo el merge `17f7648`. Ese `possession/` lleva, entre otras cosas, la PR 12 de Ana: las ventanas de
    `dead_state` ya no cruzan los bordes de los tramos, así que cambian sus rasgos en los 52 primeros y los 52
    últimos frames de cada tramo;
  - la huella del código de `possession/` que imprimió el script, `b8a00a1a1aea`, es la de ese `possession/`. En
    `569d3b4` era `6169ad54157a`. La del modelo de Ana, `def73c1ebf2b`, es la misma en los dos, porque solo mira
    `dead_state.MODEL`;
  - el modelo de Ana cambió, pues, entre escribir la regla y ejecutarla. La ejecución ya lo lleva, así que no
    obliga a repetir nada;
  - piezas `ball.clean`, `aprendida.evidence_b5`, `dead_state.evidence` y `temporal.decode`, con los costes 25 /
    25 / 25;
  - 53 ventanas, de 35,0 s de mediana; menos de 5 se apartan más de 1 s de ella.
- **La regla, por tipo** [medido]. Los desfases van desde el inicio de la ventana.

  | tipo | ventanas | con transición del modelo de Ana | su recorrido intercuartílico | el balón vuelve a verse | medianas a ≤ 1 s | ¿gana el ancla fija? | ancla |
  |---|---|---|---|---|---|---|---|
  | saque de banda | 26 | 25 (mediana +6,9 s) | **3,2 s** | 17 (mediana +6,1 s; recorrido 3,0 s) | sí (0,8 s) | no (2,0 s frente a 1,6 s) | **no** |
  | córner | 12 | 11 (mediana +4,8 s) | **3,1 s** | 11 (mediana +6,6 s; recorrido 1,7 s) | no (1,8 s) | no (2,0 s frente a 1,8 s) | **no** |
  | saque de puerta | 10 | 8, menos de 10 | no se calcula | < 5 (en 8 se veía al empezar) | no se calcula | no se calcula | **no** |
  | falta | 5 | < 5 | no se calcula | < 5 | no se calcula | no se calcula | **no** |

  - «¿Gana el ancla fija?» compara la distancia mediana del balón a la mediana del tipo con la del balón a la
    transición de su propia ventana (16 pares en los saques de banda y 11 en los córners).
  - El placebo (103 ventanas desplazadas) no se concentra en ningún tipo.
- **→ Ningún tipo tiene ancla, no se prueba ningún candidato y no entra ninguna de las dos capas del instante**
  [medido]. En los saques de banda y los córners, los dos tipos con 10 transiciones o más, falla primero la
  dispersión: el recorrido pasa de 3 s, y el máximo era 2 s. En los saques de puerta y las faltas falla antes el
  número de transiciones.
- **El modelo de Ana como instrumento** [medido]: ve `D` en el 47,4 % de lo evaluado, en el 94,6 % del control de
  `D` y en el 49,6 % del control de juego. Las tres proporciones se cuentan en los frames en que el modelo opina
  (log-odds distinto de 0). El control de juego queda por encima del partido: el instrumento no separa por el lado
  del juego.
  - [inferencia, comprobada en el código: `ana_agrees` exige que el control de juego quede por debajo del
    partido, y las tres proporciones no dependen de las anclas] **A no habría podido entrar en ningún tipo aunque
    hubiera habido ancla** (condición 2 de A). El script no llegó a mirar A.
- **Qué dice:**
  - [medido] En los dos tipos que se pueden medir, la transición del modelo de Ana no cae en un sitio fijo de la
    ventana.
  - **Saques de banda.** [medido] Las dos señales se dispersan (3,2 s la transición y 3,0 s el balón), y la
    transición de cada ventana queda más cerca del balón (1,6 s de mediana) que la mediana fija (2,0 s).
    [inferencia] La diferencia entre ventanas parece real (saques rápidos y lentos), no solo ruido del
    instrumento. La ventaja de la transición de cada ventana sobre la mediana es pequeña (0,4 s, con cifras
    redondeadas a 0,1 s y 16 pares), así que no da para más.
  - **Córners.** [medido] El balón se concentra (recorrido de 1,7 s) y la transición no (3,1 s); la mediana del
    balón cae 1,8 s después que la de la transición. [inferencia] Aquí la dispersión parece más del instrumento
    que del reinicio, y el 2,0 frente a 1,8 s sale sobre todo de ese desfase. Anclar los córners en el balón no
    se puede con esta salida: sería una regla nueva, estimada con este mismo partido y escrita antes de medir
    otra vez.
  - [inferencia] Para fechar el fin del `D` de cada saque de banda haría falta una señal por ventana, por ejemplo
    la reaparición del balón en las ventanas con hueco, no un desfase fijo. También sería una regla nueva.
  - [inferencia] El control de juego puede tener tanto `D` por tres cosas: el tramo antes del saque de la 2ª parte
    (punto siguiente), paradas que el Smart Tagging no marca (solo trae 5 faltas) o `D` del modelo en pleno
    juego. [sin verificar] El final de cada parte tampoco lo marca ningún `SET PIECES`.
- **Algo que se vio después de ejecutar, en el control de juego** [inferencia, comprobada en el código]:
  - `far_from_restarts` aplica la regla al pie de la letra: parte de todos los frames evaluados y quita los que
    están a menos de 60 s de un `GOALS` o un `SET PIECES`. La ventana `Kick Off (Start)` de la 2ª parte es un
    `SET PIECES`, así que quita unos 1.500 frames del tramo antes del saque, pero no el resto. Ese tramo es `D`
    según el FAQ y es el control de `D`.
  - La cuenta: 2.934 − 1.500 − (lo que va del inicio de la ventana al saque, de 0 a unos 125 frames) deja en el
    control de juego entre unos 1.310 y 1.434 frames. Supone que la ventana dura unos 5 s y contiene el saque
    (entrada del 12/11), y que ningún otro `GOALS` o `SET PIECES` cae a menos de 60 s del tramo (el Smart Tagging
    tiene falsos positivos).
  - En el tramo entero el modelo de Ana ve `D` el 94,6 %. La parte que se queda en el control es la más lejana al
    saque [sin verificar que ahí sea igual].
  - Si fuera el 94,6 %, quitarla dejaría el control de juego por debajo del 47,4 % si tiene menos de unos
    27.000–32.000 frames en los que el modelo opina [inferencia, cuenta con las cifras redondeadas]. El script no
    imprimía ese recuento.
  - No cambia el veredicto, que falla antes por la dispersión. Ana decidió después quitar el tramo para cualquier
    repetición (abajo, «Cambios a la regla después de la ejecución»).
- **La tarea 3 del plan** (sección 4 de la misma salida; son agregados descriptivos, sin un criterio escrito
  antes de medir) [medido]:
  - la capa del hueco cambia 1.083 frames evaluados, 561 de ellos (el 51,8 %) en los primeros 5 s de cada hueco;
    sin ella no hay frames con piezas en conflicto;
  - el `D` de la entrega empieza, respecto al inicio de cada uno de los 28 huecos: antes del hueco en 11; en su
    primer segundo (de 0 a 1 s) en 8; de 1 a 3 s, de 3 a 5 s, a 5 s o más, o sin `D`, menos de 5 cada uno (9
    entre los cuatro).
  - [inferencia] En 19 de 28 huecos el `D` ya empieza antes del hueco o en su primer segundo, así que dar más
    peso al principio del hueco tendría poco que ganar ahí. En los otros 9 (un tercio) empieza 1 s tarde o más, o
    no hay `D`. En contra de subir el peso está lo que ya decía el plan: en esos 5 s el modelo de Ana solo ve `D`
    el 60,9 %, y un peso alto puede forzar `D` en juego.
  - La tarea pide hacerlo «solo si eso lo apoya». Cerrarla como «no se apoya» sería una lectura de estos
    agregados, no el resultado de una regla. Queda por decidir. **→ Cerrada como «no se apoya»** (Manuel, 15/11;
    entrada «cierres de la pieza de Manuel»).
- **El orden real de los mensajes** [fuente: los mensajes del 15/11 entre Manuel, Ana e Ismael]:
  - Manuel mandó las 9 interpretaciones de arriba para que se confirmaran antes de ejecutar.
  - Contestó Ana, que lo había hablado con Ismael: confirmó las 9 sin cambios y pidió dos añadidos, para antes de
    ejecutar.
  - Su respuesta llegó cuando Manuel ya había ejecutado. **Se ejecutó antes de recibir la confirmación de las 9 y
    sin los dos añadidos.** Las 9 se confirmaron sin cambios, así que la ejecución aplica la regla confirmada.
- **Los dos añadidos de Ana**, tal como los pidió:
  1. que el script imprima cuántos frames tiene el control de juego; si son menos del 5 % de los frames evaluados
     (7.943 de 158.857), el instrumento no separa y A no entra;
  2. que el ancla sea la mediana de la transición menos el retraso mediano medido en la DFL para ese tipo: 20
     frames en los saques de banda y 16 en los córners. Los tipos sin una medida propia de 50 paradas o más en la
     DFL no se corrigen. Es un número de la DFL, no del partido.
     - En la DFL la transición llega esa mediana tarde, y de las paradas con transición solo el 45 % (saques de
       banda) y el 57 % (córners) caen a menos de 1 s del fin real [fuente: medida de Ana en la DFL, 15/11; su
       script y su salida, abajo].
     - Salvedad de Ana: en la DFL se busca desde el inicio de la parada, y aquí desde el inicio de la ventana
       `SET PIECES`. [inferencia] Al buscar desde antes, en la DFL se pueden coger transiciones falsas tempranas
       (en los saques de banda, p10 −26 y p25 −2 frames), así que, si acaso, los 20 y 16 frames corrigen de menos.
- **Por qué los añadidos no cambian el veredicto** [inferencia, comprobada en el código: `anchor_rule` exige
  `tight`, que solo usa el recorrido de las transiciones tal cual; `a_conditions` solo se llama en los tipos con
  ancla]:
  - en los saques de banda y los córners falla primero la dispersión; restar un retraso fijo por tipo mueve todos
    sus instantes por igual y no cambia el recorrido;
  - en los saques de puerta y las faltas falla antes el número de transiciones, que los añadidos tampoco tocan;
  - el mínimo del control de juego solo actúa sobre A, que solo se mira en los tipos con ancla, y no hay ninguno.

Abierto, después del resultado:
- **La excepción a §2 del plan no hace falta mientras el veredicto siga siendo «no entra»:** no se copia en
  `possession/dead_ball.py` ninguna constante sacada del partido.
- **¿Se repite si cambia el modelo de Ana?** La regla dice que se repite todo si cambian la limpieza o el modelo de
  Ana antes de que la capa entre. Eso incluye `dead_state.MODEL` y también el cálculo de los rasgos y de los
  log-odds: la PR 12 los cambió sin tocar `MODEL` ni su huella. Como la capa no ha entrado, un cambio así obliga
  a repetir la medida. Repetir con cada cambio sería buscar hasta que salga. Queda por decidir si el veredicto se
  cierra como «no entra». **→ Cerrado como «no entra»** (Manuel, 15/11; entrada «cierres de la pieza de Manuel»).
  - Ojo con la huella del código: con el merge de `main` del 15/11 por la noche (`69f4647`) pasó a ser
    `fafbd30245b5` [medido], porque `possession/pipeline.py` ahora imprime el commit. Una repetición enseñaría otra
    huella sin que cambie nada que afecte a esta medida; cualquier cambio de `possession/` la cambia.
- **La tarea 3:** cerrarla como «no se apoya» sería una lectura (arriba). Queda por decidir. **→ Cerrada como «no se
  apoya»** (Manuel, 15/11; entrada «cierres de la pieza de Manuel»).
- **Una señal por ventana** en vez de un desfase fijo: es solo una idea, sin regla.
- **La rama `feat/d-equipo-reanuda`** sigue en GitHub, sin PR. Queda por decidir si se guarda como registro. Como
  ya está subida, no se reescribe: se haría una rama nueva desde `main` con esos commits. **→ Se queda en GitHub
  sin PR, como registro** (Manuel, 15/11; entrada «cierres de la pieza de Manuel»).
- **La máscara «< 5» del script se puede deshacer restando** en algunas filas: en los saques de banda, «no vuelve»
  sale de restar al total «vuelve a verse» y «visto al empezar»; también salen, restando, las ventanas sin
  transición. No son datos de ninguna jugada, pero si se quiere que tape de verdad, hay que tapar también una celda
  complementaria.
- **Para la pieza de estado (`dead_state`)** [inferencia]: el control de juego tiene más `D` que el partido. El
  tramo antes del saque puede explicar una parte (arriba); lo demás serían paradas sin marcar o `D` del modelo en
  pleno juego.

**Cambios a la regla después de la ejecución del 15/11 (decisión de Ana, 15/11).** Valen para cualquier
repetición. La ejecución del 15/11 no los lleva, y su veredicto no cambia (arriba). Los dos primeros son los
añadidos que Ana pidió para antes de ejecutar; el tercero lo decidió después de ver la salida.
- Las precisiones del punto 2 (dónde se usa el ancla corregida, qué sigue sin corregir y la mediana positiva) no
  estaban en el mensaje de Ana: se fijaron después de la ejecución, la última al repetir su medida de la DFL, y
  ninguna mira el partido.
- Estos cambios no son, por sí solos, motivo para repetir la medida.
- Si se repite por otra causa: la condición 2 de A, con el control de juego nuevo, se cambió viendo que fallaba
  (49,6 % frente a 47,4 %). Un «sí» de esa condición no será una prueba a ciegas, y así se dirá al leer su resultado.

1. **El control de juego tiene que tener frames suficientes** (añadido de Ana). El script imprime cuántos frames
   tiene (todos, opine o no el modelo en ellos), qué parte son de lo evaluado y el mínimo. Si son menos del 5 % de
   los 158.857 frames evaluados, contando el tramo antes del saque (7.943; en el código, en enteros,
   `PLAY_MIN_NUM, PLAY_MIN_DEN = 1, 20`), A no se cumple en ningún tipo.
2. **El ancla es la mediana de la transición menos su retraso en la DFL** (añadido de Ana):
   `DFL_DELAY = {"throw-in": 20, "corner kick": 16}`, en frames.
   - **Dónde se usa el ancla corregida:** en el instante de la capa (los dos candidatos), en las condiciones de A
     a los dos lados del instante y en el placebo de A. Es también lo que se imprime para copiar si la capa entra.
   - **Qué sigue con la mediana sin corregir:** si un tipo tiene ancla no cambia. El recorrido, «nítido» y la
     coincidencia con el balón no se tocan. «El ancla fija gana» se calcula con la mediana sin corregir,
     comparada con las transiciones sin corregir; en lo impreso se llama ahora «la mediana gana».
   - **Dos efectos de aplicarlo así** [inferencia]. Es como lo describía el traspaso de Manuel (el ancla corregida
     para la capa, los lados de A y el placebo de A). Si se cambia lo decide Ana, como dueña de la pieza y del modelo
     de estado, antes de cualquier repetición, y lo apunta aquí:
     - la coincidencia con el balón se mira con la mediana sin corregir, así que ya no avala del todo el instante
       que se usa. Con el balón 0,9 s después de la mediana la condición se cumple, y el ancla de los saques de
       banda quedaría a 1,7 s del balón. El 15/11, en los córners, el balón caía 1,8 s después de la transición:
       restar 16 frames lo alejaría hasta unos 2,4 s;
     - los lados de A se miran en el ancla corregida con el mismo instrumento que llega tarde. Si el retraso de la
       DFL se traslada al partido, de los 75 frames de «después» unos 20 (16 en los córners) son `D` del
       instrumento por construcción: el 27 % y el 21 %, con un umbral que el 15/11 fue del 48,5 %. Juega en contra
       de A;
     - la alternativa sería comparar el balón con la mediana corregida y mirar los lados de A en la mediana, donde
       ve el instrumento. Entonces contaría que la reaparición del balón también puede llegar tarde (el balón del
       ATD viene suavizado unos 25 frames y unos 4 frames tarde respecto a los jugadores), y eso no está medido.

     (Nota del 15/11 por la noche: Ana seguía la pieza por traspaso cuando escribió «lo decide Ana, como dueña de la
     pieza». Manuel la retoma; desde entonces, un cambio así lo deciden Manuel y Ana. El veredicto quedó cerrado en
     la entrada «cierres de la pieza de Manuel», así que no hay repetición prevista.)
   - **Si el ancla corregida cae antes del inicio de la ventana** (una mediana menor que el retraso), ese tipo no
     recibe la capa ni puede cumplir A. Con las medianas del 15/11 (de 120 a 172 frames) no puede pasar.
   - **Qué tipos se corrigen.** Ana escribió «los tipos sin una medida propia de 50 paradas o más en la DFL no
     se corrigen». Al repetir su medida salió que las faltas y los saques de puerta también pasan de 50 paradas,
     con la mediana negativa. Ana decidió que solo se corrigen los saques de banda y los córners: una mediana
     negativa no es un retraso, porque la transición llega antes del fin real. Así, la regla es «50 paradas o
     más con transición y la mediana positiva».
   - **La medida** [medido en la DFL; el 15/11, en la máquina de Ana, con
     `validation/scripts/d_estado/retraso_transicion.py`, que es el script de Ana y entra hoy en el repo]:

     | tipo | paradas | con transición | mediana de la transición − el fin real | a menos de 1 s, de las que tienen transición |
     |---|---|---|---|---|
     | saque de banda | 301 | 266 | +20 frames | 45 % |
     | córner | 57 | 54 | +16,5 frames | 57 % |
     | falta | 160 | 148 | −5,5 frames | 46 % |
     | saque de puerta | 109 | 106 | −114,5 frames | 26 % |

     La mediana exacta de los córners es 16,5. Se usa 16, como en el mensaje de Ana (el script redondea al par).
     La salida entera está en `validation/resultados/2026-11-15_instante_reinicio.md`.
3. **El control de juego no incluye el tramo antes del saque de la 2ª parte** (decidido después de ver la
   salida; no es uno de los dos añadidos):
   - qué pasaba: el código seguía la regla escrita, «los frames evaluados a más de 60 s de cualquier `GOALS` o
     `SET PIECES`». Eso deja dentro unos 1.310–1.434 frames de ese tramo, que es `D` según el FAQ y es el propio
     control de `D` (arriba, «Algo que se vio después de ejecutar»);
   - qué cambia: el control de juego son esos mismos frames sin el tramo antes del saque de cada parte
     (`dead_ball.pre_kickoff`);
   - por qué: un control de juego no puede llevar frames que son `D` seguro. Es un cambio de la regla visto con la
     salida delante (49,6 % frente a 47,4 %), así que se apunta como posterior. No cambia el veredicto del 15/11.

Lo que no cambia: el resto de la regla y todos sus números.

**El pipeline de la entrega, con sus capas** (15/11, por la noche). `main` encendió ese día la capa de los
contraataques (`pipeline.DELIVERY_LAYERS`), que `pipeline.build` suma a `dead_ball.evidence`. El script corre ahora el
pipeline con esas capas en sus tres ejecuciones (sin la capa, con cada candidato y sin la capa del hueco); si no, sus
secciones 3 y 4 no medirían la entrega. También lee el ATD como `pipeline.build` (una línea rara es un error) e imprime
las versiones y el commit. No es un cambio de la regla, que ya decía «el pipeline de la entrega», y la ejecución del
15/11 no se ve afectada: entonces la entrega no tenía esa capa.

Cómo se comprobó:
- **Pruebas** (sección 11 de `validation/scripts/comprobar_balon_muerto.py`, con partidos inventados y la apertura de
  ficheros prohibida):
  - las constantes nuevas, congeladas, y el 5 % justo en enteros (7.943 de 158.857 vale; 7.942, no);
  - el ancla de la capa: la mediana menos 20 frames en los saques de banda, menos 16 en los córners y sin corregir
    en los saques de puerta y las faltas;
  - de punta a punta, con un modelo de Ana inventado que deja de ver parado en el frame 180, 20 frames antes de la
    mediana de su transición (10 o 30 antes de cada una; un destello retrasa la transición formal). Es un caso
    inventado que prueba que el retraso se aplica donde toca:
    - con el retraso, A entra en el 180 y el `D` sale ahí; sin él, en el 200;
    - las condiciones de A se miran en el ancla corregida: si el modelo vuelve a ver parado de los 10,4 a los 11 s,
      A se cumple en el 180 y no en el 200;
    - el placebo de A usa el ancla corregida, no la mediana;
    - en los córners se restan 16 frames y en los saques de puerta, ninguno;
    - con un retraso mayor que la mediana, ninguna ventana recibe la capa y no entra nada;
  - el control de juego: no incluye los 2.934 frames del tramo antes del saque; cuenta todos sus frames, también
    donde el modelo no opina; el 5 % se cuenta sobre los 158.857 evaluados (316 s de control no llegan, aunque
    llegarían sobre lo evaluado sin el tramo antes del saque); y con menos del 5 %, A no se cumple aunque se cumpla
    todo lo demás (entra B);
  - lo impreso: el `main` del script, con las funciones que leen el partido sustituidas y la apertura de ficheros
    prohibida, imprime los cambios a la regla, la mediana y el ancla corregida, «la mediana gana», el control de
    juego con su mínimo en frames y, en la línea para copiar, el ancla corregida;
  - las capas de la entrega: van en las tres ejecuciones del pipeline (una capa que bloquea 10 frames da 10 conflictos
    en las tres); `main` lee el ATD como `pipeline.build`, pasa las rutas del partido a `dead_ball.evidence` y a las
    capas (a la entrega sin la capa del hueco, sin rutas) e imprime las versiones y el commit;
  - las pruebas de antes de los cambios siguen, con el ancla igual a la mediana (`no_delay`), salvo la de los 10
    saques de banda separados 10 minutos, que va con los retrasos por defecto. Dos cambian por el tercer cambio:
    - en el partido base, el control de juego pasa a tener un 0 % de `D`. Antes tenía algo porque llevaba el tramo
      antes del saque;
    - en la del placebo que pasa, los 3 s de después del instante se ponen en juego también en las ventanas
      desplazadas que caen en una parada real. Antes la prueba pasaba porque ese tramo subía el punto medio.
- **Sabotajes** (una vez, en memoria, fuera del repo): 33 roturas de lo nuevo, una a una. Las pruebas detectan 32,
  entre ellas las dos que encontró la segunda revisión (el 5 % contado sobre lo evaluado sin el tramo antes del
  saque, y contar solo los frames en que el modelo opina) y las de lo impreso (la línea para copiar con la mediana,
  la mediana y el ancla cruzadas, «el ancla gana» y el mínimo redondeado hacia abajo). La que no, no cambia nada:
  medir el control de `D` en todo el tramo antes del saque en vez de en su parte evaluada, que es el tramo entero.
- **Lo impreso, a mano** (una vez, fuera del repo): el `main` con un partido inventado en un caso en que entra A y
  en otro en que no hay ancla. Tapa con «< 5» y «—» lo que debe. Cambian tres textos: en la cabecera de la sección
  2, «el ancla fija más cerca» pasa a ser «la mediana fija más cerca»; en cada tipo, «el ancla gana» pasa a ser «la
  mediana gana»; y «del balón al ancla fija», «del balón a la mediana fija». Hay líneas nuevas: la de los cambios a
  la regla, el recuento del control de juego con su mínimo, «sin el tramo antes del saque» y «control de juego
  suficiente».

### 2026-11-15 · `D` · juego vivo en el saque de cada parte: regla escrita antes de regenerar la entrega

Quién: Ana, que sigue la pieza de Manuel desde el 15/11. Es la tarea 4 de Manuel en `docs/PLAN_ENTREGA.md` §3:
«prohibir `D` en el frame del saque de cada parte (un frame en `allowed`). En la misma PR, para que el fichero tenga
un solo cambio abierto».

Qué cambia en `possession/dead_ball.py`:
- `kickoff_mask(game)` da el frame del saque de cada parte. Son los de FAQ.md, tal como los guarda el código oficial
  (`KICKOFF_VIDEO_FRAMES`: 11.185 y 113.742), los mismos que ya usa el tramo antes del saque. Solo cuenta un saque si
  cae en su tramo evaluado, y solo para BAR-ATH: con otro partido da error, como `pre_kickoff`.
- En `evidence`: `allowed[kickoff_mask(game), D] = False`. No toca ninguna puntuación. Va también sin rutas
  (`paths=None`), como el tramo antes del saque, porque no lee ningún fichero.
- No choca con el tramo antes del saque, que acaba en el frame anterior (113.741). En la 1ª parte el primer frame
  evaluado ya es el saque, así que allí no hay tramo.

Por qué: los 2.934 frames de 110.808 a 113.741 son `D`, y en el 113.742 se saca [fuente: FAQ.md]; desde ese frame el
balón está en juego [inferencia a partir de FAQ.md, que no lo dice con esas palabras; corregido el 15/11, antes
decía solo «fuente»]. La GT pública tampoco tiene `D` en el primer frame evaluado de la 1ª parte (sección 3 de
`validation/scripts/comprobar_balon_muerto.py`). No sale ninguna constante del partido: son las de `games.py` y del
código oficial.

Qué puede salir mal [inferencia]: obligado a salir de `D` en el saque, el decodificador puede volver a `D` justo
después, si la evidencia de `D` de los segundos siguientes suma más de lo que cuesta volver a `D` y salir otra vez
(`to_dead` + `from_dead`, 50 con los costes de hoy). Saldría una posesión de 1 frame y una parada partida, peor que no
hacer nada. Por eso la regla mira las posesiones, las paradas y las rachas cortas.

No lleva juez ni placebo: el saque no es una señal estimada, sino un frame que da la organización. Lo que se mide es
que no haga daño. Tampoco se puede medir en la DFL: la pieza usa constantes de este partido.

Cómo se mide: `validation/partido/agregados_saque_juego_vivo.py`, que ejecuta una persona.
- Corre el pipeline de la entrega dos veces, sin escribir ningún fichero: con `dead_ball.evidence` tal cual y con el
  ancla quitada (`D` permitido otra vez en esos dos frames). Las dos veces suma las demás capas de la entrega
  (`pipeline.DELIVERY_LAYERS`, desde el 15/11 la de los contraataques), como `pipeline.build`, y lee el ATD como él.
- Imprime las versiones de Python y numpy, el commit y los dos sha256. El de «sin el ancla» tiene que ser el de la
  entrega vigente, `equipo_v5` (`27dc8aa8…efb7`).

Regla de lectura, fijada antes de ejecutarlo. **Entra si se cumplen las seis:**
0. sin el ancla sale la entrega vigente: el sha256 empieza por `27dc8aa8` y acaba en `efb7` (`equipo_v5`). Si no,
   ha cambiado algo más (el código de `main` o el entorno, por ejemplo la versión de numpy). Entonces la regla no se
   aplica: el script avisa, no enseña nada más y sale con código 1. No entra hasta explicarlo y volver a ejecutar:
   - en un entorno que reproduzca `equipo_v5`;
   - o con la entrega vigente puesta al día (`VIGENTE` del script). Solo se pone al día a una entrega generada con
     `python -m possession.pipeline` desde `main`, validada y apuntada en este fichero con su sha256, en un commit
     anterior a la nueva ejecución. Nunca al sha256 «sin el ancla» que imprime este script;
1. con el ancla, ningún frame evaluado con piezas en conflicto (lo mismo que exige `pipeline` para escribir el CSV);
2. cada parte tiene su saque en su tramo evaluado, y en ese frame la entrega con el ancla no tiene `D`;
3. la entrega con el ancla queda dentro de la banda del plan: del 15 al 60 % de `D` en lo evaluado y 250 paradas
   como mucho;
4. en cada tramo, con el ancla no suben las posesiones, ni las paradas, ni las rachas cortas (de posesión, de juego y
   de parada, de menos de 12 y de menos de 25 frames, como las cuenta `pipeline.short_runs`);
5. todo lo que cambia cae en los 60 s después del saque de su parte: nada antes del saque ni más tarde. Los 60 s son a
   priori, el mismo horizonte que `dead_ball.MAX_GAP_BEFORE_RESTART_S`. Lo esperado es que solo cambien frames justo
   después de los saques; si cambia algo más lejos, no entra hasta entender por qué.
- Si no cambia ningún frame, entra igual: en este partido no hace nada, pero deja fijada la frontera.
- **La condición 4 también rechaza un caso bueno** [inferencia]: un saque seguido de una parada real en los primeros
  segundos. Sin el ancla, el `D` puede seguir de largo por esa jugada; con ella, la salida ya está pagada y la entrega
  se queda en juego hasta la parada: sale una posesión más y una parada más, aunque las etiquetas fueran mejores. Se
  acepta perderlo: sin juez no se distingue de un rebote.
- Con esta salida no se reajusta nada: ni los 60 s, ni la banda, ni el frame del saque.
- Descriptivo: cuántos frames cambian, de qué clase (de `D` a juego, de juego a `D` o de un equipo al otro) y a qué
  distancia después del saque (de 0 a 1 s, de 1 a 5, de 5 a 30, de 30 a 60 y 60 s o más), y qué sube en cada tramo.
- **Lo que imprime y la regla nº 1:** como solo hay dos saques, lo que cambia describe como mucho dos tramos de nuestra
  propia entrega, junto a ellos. Por eso junta las dos partes y no dice de qué equipo a cuál; tampoco da ningún número
  de frame.

Lo que espero [inferencia]: que cambien pocos frames, de `D` a juego, en los primeros segundos tras el saque de la 2ª
parte, porque el modelo de Ana acaba las paradas tarde (sesgo mediano de +17 frames en la DFL, entrada del 14/11), y
que en la 1ª parte cambie poco o nada. El riesgo es el rebote de arriba.

**Cuándo se mergea:** la rama se sube con el ancla ya en `evidence` y con esta regla, pero no se mergea en `main`
hasta ejecutar el script en ella. Si entrara en `main` antes, `python -m possession.pipeline` dejaría de dar `equipo_v5`
sin que nadie hubiera aplicado la regla.

Si entra:
- una persona regenera la entrega (`python -m possession.pipeline --name equipo_v6`) y la valida
  (`python evaluation/validate_submission.py evaluation/results/equipo_v6.csv`, o `/evaluar`);
- el sha256 que imprime el comando tiene que ser el «con el ancla» del script. Si no lo es, esa entrega no se usa y se
  investiga;
- la entrega deja de ser `equipo_v5`: hay que avisar al equipo para que el ensayo del lunes la reproduzca con esta
  rama ya en `main`.

Si no entra: se quita de `evidence` la línea del ancla antes del merge (la función se queda, probada) y se apunta
aquí por qué.

Lo que no comprueba [sin verificar]:
- que el saque caiga justo en ese frame: lo dice la organización [fuente: FAQ.md]. El 12/11 se vio que las ventanas
  `Kick Off (Start)` del Smart Tagging lo contienen;
- qué equipo saca: lo decide el decodificador con la evidencia de equipo, como antes.

Relación con las otras medidas de la pieza: `validation/partido/agregados_instante_reinicio.py` corre el pipeline con
`dead_ball.evidence` como entrega (secciones 3 y 4), así que, si se repite, ya lleva el ancla del saque y las demás
capas de la entrega. Como el instante no entró, no hay que repetir su sección 3 (el daño).
`validation/partido/agregados_dead_ball.py` no corre el pipeline.

Cómo se comprobó, antes de ejecutar nada:
- **Pruebas** (sección 12 de `validation/scripts/comprobar_balon_muerto.py`, con datos inventados y la apertura de
  ficheros prohibida):
  - `kickoff_mask`: los dos frames de FAQ.md y ninguno más; con otro partido, error; un saque fuera de su tramo no se
    ancla;
  - `evidence`, con rutas y sin ellas: `D` prohibido justo en esos dos frames, con `H` y `A` permitidos ahí; ningún
    frame se queda sin estado permitido (la prueba de la sección 7 que decía que `evidence` nunca prohibía `D` ahora
    dice esto);
  - quitar el ancla devuelve la evidencia de antes de la tarea 4, sin tocar la que recibe; el sha256 del script es el
    mismo que el del CSV que escribe `pipeline.write_submission`;
  - la regla con etiquetas puestas a mano: entra si el `D` que seguía tras el saque acaba en él, o si no cambia nada;
    no entra si sin el ancla no sale la entrega vigente, si vuelve a `D` justo después, si solo sube una racha corta,
    solo el número de posesiones o solo el de paradas, si cambia algo a 60 s o más o antes del saque, con `D` en el
    saque, si una parte no tiene su saque o tiene dos, con conflictos o fuera de la banda (mirada con el ancla puesta,
    también por las 250 paradas). En el primer frame de la 1ª parte: entra si desaparece el `D` del principio y no si
    sale un frame y vuelve a `D`;
  - de punta a punta, con el pipeline y piezas controladas: con poca evidencia de `D` tras el saque de la 2ª parte,
    cambian 75 frames de `D` a `H` y entra; con mucha, rebota (1 frame de `H`), suben las posesiones y las paradas y
    no entra; si la entrega sin el ancla no es la vigente, no entra; con otra pieza que solo permite `D` en el saque,
    hay conflicto y no entra; las demás capas de la entrega van en las dos ejecuciones; los dos sha256 salen en su
    orden;
  - el pipeline es el de la entrega: con las lecturas del partido sustituidas, la entrega «con el ancla» del script
    es, byte a byte, la que sale de `pipeline.build`, con una capa de la entrega que solo opina si recibe las rutas;
  - lo impreso: el `main` del script, con las funciones que leen el partido sustituidas. Lee el ATD como
    `pipeline.build`, pasa las rutas del partido a `dead_ball.evidence` y a las capas de la entrega, imprime las
    versiones y el commit, y cada número sale en su sitio (sin el ancla y con ella), sin equipos. Si solo falla la
    condición 0, avisa, no enseña nada más y sale con código 1; si solo falla la banda, la línea de la banda dice
    «no» y no sale el aviso.
- **Sabotajes** (en memoria, fuera del repo): 77 roturas, una a una. En el ancla: quitarla, prohibir `H` en vez de
  `D`, ponerla un frame tarde o un frame antes, alargarla 25 frames, quitar la guarda del tramo, aplicarla a cualquier
  partido o solo con rutas. En el script: la entrega vigente, las capas y las rutas de la entrega, la lectura del ATD,
  quitar el ancla mal, el sha256, las rachas, lo que sube, las distancias, las clases de cambio, cada condición de la
  regla, cada número de lo impreso y la parada en la condición 0; y que `run_main` no devuelva las funciones a su
  sitio. Las pruebas detectan 75. Las dos que no, hoy no cambian nada:
  - contar como «de `D` a juego» también de `D` a `D`, que no puede pasar en un frame que cambia;
  - sumar las capas de la entrega antes que `dead_ball.evidence`: solo cambiaría el orden de la suma, y hoy cada una
    puntúa columnas distintas. Si una capa futura puntuara la misma columna, la condición 0 lo pararía.
  Del instante: 38 roturas, 37 detectadas, y la equivalente de siempre.
- **Lo impreso, a mano:** el `main` con un partido inventado, en un caso en que entra y en otro en que rebota, con
  el código de antes de la cuarta revisión. Con el partido inventado el sha256 «sin el ancla» no es el de `equipo_v5`,
  así que se vio también el aviso de la condición 0.
- **Cuatro revisiones** del agente `revisor` antes de subirla. La tercera vio que `main` había cambiado la entrega
  (`equipo_v5`, con la capa de los contraataques) y que la regla no decía qué hacer si el sha256 no cuadraba: de ahí la
  condición 0, las capas de la entrega en el script y lo de no decir equipos. La cuarta, sin ningún 🔴, pidió que la
  condición 0 se pudiera aplicar de verdad (el script se para y no enseña nada más, y cómo se pone al día la entrega
  vigente), pruebas de que `main` pasa las rutas y las capas, y escribir que la rama no se mergea hasta aplicar la
  regla.

**Resultado (añadido después de ejecutarlo; lo de arriba no ha cambiado).** Lo ejecutó Ana en local el 15/11, con la
rama en `03fe7e8` y sin cambios locales en el código de la entrega. La salida entera está en
`validation/resultados/2026-11-15_saque_juego_vivo.md`.
- **Con qué se midió** [medido]: Python 3.10.12 y numpy 2.2.4; huellas del modelo de Ana `def73c1ebf2b` y del código
  de `possession/` `bb963526df2a`; las piezas de `pipeline.PIECES`, costes 25 / 25 / 25 y la capa de los contraataques.
- **Condición 0:** sin el ancla sale `equipo_v5` byte a byte (`27dc8aa8…efb7`), así que la regla se aplica [medido].
- **→ Entra:** se cumplen las seis condiciones [medido].
  - Con el ancla la entrega sale con el mismo sha256: no cambia ningún frame. La entrega ya salía del `D` en el frame
    de los dos saques.
  - Sin conflictos, con un 45,09 % de `D` y 113 paradas; las posesiones (103 y 116), las paradas (53 y 60) y las
    rachas cortas de cada tramo no se mueven.
- **Qué dice** [inferencia]: el rebote que preocupaba no pasa, porque no hay nada que corregir en este partido. El
  ancla no mejora la entrega de hoy; deja fijada la frontera para cualquier cambio futuro de las piezas de `D`, que ya
  no podrá alargar una parada más allá del saque.
- **Lo que sigue, según la regla:** regenerar la entrega con `python -m possession.pipeline --name equipo_v6` y
  validarla. Su sha256 tiene que ser `27dc8aa8…efb7`, el mismo que `equipo_v5`: la entrega vigente no cambia de
  contenido. Después la rama ya se puede mergear.

**Entrega regenerada (15/11)** [medido por Ana, en su máquina, con la rama en `f6a8880`]: `python -m possession.pipeline
--name equipo_v6` da 0 conflictos, ninguna racha corta y el sha256 `27dc8aa8…efb7`, el mismo que el «con el ancla» del
script y que `equipo_v5`. El validador oficial la da por válida (199.319 filas). La entrega vigente no cambia de
contenido: `equipo_v6` es `equipo_v5` byte a byte. La rama ya se puede mergear.

### 2026-11-15 · `D` · cierres de la pieza de Manuel: el instante, la tarea 3 y la rama del equipo que reanuda

Quién: Manuel, que retoma su pieza (`docs/PLAN_ENTREGA.md` §3). Ana la siguió por traspaso desde el 15/11 por la
tarde y apuntó estas preguntas abiertas en la entrada «el instante del reinicio». Las normas del 15/11 dejan decidir
a cualquiera del equipo y piden apuntarlo aquí. Las tres decisiones no se le consultaron a Ana antes: se le avisa.

Qué se probó: nada nuevo. Son decisiones sobre resultados ya medidos.

Cómo se midió: no aplica. Las cifras del instante y de la tarea 3 salen de
`validation/resultados/2026-11-15_instante_reinicio.md`. El 60,9 %, de
`validation/resultados/2026-11-15_agregados_dead_ball.md` (citado en el plan, §3), medido con el modelo de Ana de
antes de la PR 12. Las del equipo que reanuda, del fichero de resultados de su rama.

Decisión y por qué:
- **El instante del reinicio se cierra como «no entra»,** y este script no se repite por ninguna causa:
  - tampoco si cambian el modelo de Ana o la limpieza del balón, ni si cambian la evidencia de equipo o los costes;
  - así quedan sin efecto las frases de su regla que obligaban a repetirlo (marcadas arriba, en su entrada);
  - la capa del hueco no entra en el cierre: `agregados_dead_ball.py` se sigue repitiendo si se enciende la
    limpieza de Antonio.

  Por qué, por tipo de reinicio [inferencia sobre lo medido]:
  - **saques de banda:** la transición del modelo de Ana se dispersa 3,2 s y la reaparición del balón 3,0 s. El
    balón no depende del modelo, así que la variación parece del propio reinicio: un desfase fijo no vale, sea cual
    sea el modelo;
  - **córners:** el balón se concentra (1,7 s) y la transición no (3,1 s). Aquí la dispersión parece más del
    instrumento, y un modelo distinto sí podría concentrarla. El cierre no se apoya en que no tenga arreglo, sino
    en dos cosas: repetir con cada cambio sería buscar hasta que salga, y anclar los córners en el balón sería una
    regla nueva, estimada con este mismo partido.

  Consecuencias: la capa sigue fuera de `evidence`, programada y probada. El cambio 3 del control de juego (el que
  se decidió viendo la salida) no llega a usarse. La excepción a §2 del plan no hace falta. Si alguien quiere
  fechar el fin del `D` (por ejemplo, con una señal por ventana o con el balón en los córners), sería una regla
  nueva, escrita antes de medir.
- **La tarea 3 («más peso al principio del hueco») se cierra como «no se apoya».**
  - En 19 de los 28 huecos el `D` de la entrega ya empieza antes del hueco o en su primer segundo, así que hay poco
    que ganar [inferencia sobre agregados medidos].
  - Un peso alto ahí puede forzar `D` en juego: en esos 5 s el modelo de Ana solo veía `D` el 60,9 %.
  - No es el resultado de una regla escrita antes: es una lectura de los agregados, y así se dice.
- **La rama `feat/d-equipo-reanuda` se queda en GitHub sin PR, como registro** (`63c6bc6`; la regla se subió en
  `28565ce`, antes de ejecutar). Su resultado, para que no dependa de que la rama siga existiendo [medido por Manuel
  el 15/11, solo agregados]:
  - el `Team` del Smart Tagging es fiable en córners y saques de puerta: coincide con la física en 20 de 20;
  - la capa no entra: no arregla ninguna salida y hace daño (retrasa 3 cambios, añade 2 posesiones y 1 parada, y
    pasa 220 frames de juego a `D`);
  - descriptivo: sin la capa, el pipeline sale de 12 de las 25 paradas con el equipo contrario al del `Team`. No se
    sabe si es el pipeline o la forma de medir la salida [inferencia].

  La tarea 6 del plan (el equipo que reanuda) está retirada.

Lo que no cambia: la entrega. Esta entrada y los retoques de la misma PR no tocan nada de lo que usa la entrega.
- El docstring de `possession/dead_ball.py` ya dice que el saque entró.
- La cita del FAQ pasa a ser [inferencia].
- Los cambios del ancla corregida los deciden Manuel y Ana.

Descartado:
- **Repetir el instante con cada cambio del modelo de Ana:** sería buscar hasta que salga.
- **Una PR de registro para `feat/d-equipo-reanuda`:** no cambia la entrega y la rama ya guarda el registro.

### 2026-11-16 · `D` · se enciende la capa del balón fuera (`dead_ball.ball_out`), con una entrega de prueba antes

Quién: Ismael. Sus palabras (16/11): «vamos a encender la primera capa del balón. Crea otra sesión para
implementarla». La implementa Claude, en una sesión aparte.

**Qué se decide:** la entrega suma `dead_ball.ball_out`, la primera versión de D7, si pasa la lectura de abajo.
- El peso (5) y la cola (16 frames) no se tocan.
- La segunda versión, `ball_out_hold`, sigue apagada: salió byte a byte igual que la primera.

**Por qué, contra la regla escrita:**
- La capa tenía tres criterios, escritos antes de generar `prueba_d7` (entrada «D7, el balón fuera del campo», 15/11).
  **Falló el 1 y pasó el 2 y el 3** [medido por Ismael]:
  1. llegamos tarde en 12 de 47 rachas de balón fuera (25,5 %); sin la capa, en 23 (48,9 %). Se pedía menos del
     15 %;
  2. hay 116 paradas, 3 más que en `equipo_v3`, y el `D` ocupa el 45,4 % de los frames evaluados;
  3. cambian 574 frames evaluados, todos de un equipo a `D` (331 de `H` y 243 de `A`). Las posesiones siguen en 215.
- Por la regla escrita, la capa se quedaba apagada. La entrada «D7, segunda versión» cerró D7.
- **Ismael decide encenderla igualmente.** El criterio 1 mide si el problema queda resuelto del todo, no si la capa
  hace daño. Los dos criterios de daño se cumplieron.
- Es la segunda excepción a «lo que no ha ganado en el harness no entra» (plan §4), después de la capa de los
  contraataques.

**Lo que no se puede medir:**
- **En la DFL, nada:** allí el balón se queda quieto mientras está muerto y va tapado en los `D`, así que «fuera es
  `D`» se cumple por construcción. Con la capa cambian 23 frames de 2.012.288.
- Lo único que la apoya fuera del partido es descriptivo: en SkillCorner, un balón visto fuera es `D` el 93–94 % de
  las veces.
- Cuánto mueve el `spellF1` del partido no se sabe.

**La lectura de la entrega de prueba, fijada antes de generarla.**

Por qué hace falta otra prueba: las de ayer se hicieron sobre `equipo_v3`. Desde entonces está encendida la capa de
los contraataques (`transiciones.evidence_equipo`), y nadie ha generado la entrega con las dos capas.
- Donde se solapan (los 5 primeros segundos de un contraataque con el balón visto fuera), la de los contraataques
  suma 8 a un equipo y esta suma 5 a `D`. Ahí el resultado no tiene por qué ser la suma de las dos pruebas.
- Por eso los umbrales dejan margen sobre lo de ayer.

Lo que espero: casi lo mismo que `prueba_d7` [inferencia]. `equipo_v5` tiene el mismo `D` que `equipo_v3` en los
frames evaluados [medido: los 817 frames que cambian son de un equipo al otro y las dos tienen 113 paradas, entrada
«se enciende la capa de los contraataques»], y la capa de los contraataques no suma a la columna `D`. Unos 574 frames
de un equipo a `D`, 116 paradas, 219 posesiones y 12 de 47 rachas en que llegamos tarde.

Cómo se genera (lo ejecuta Ismael, desde `C:\dev\mtah2027-piso2nyc`, con `main` al día y el python del entorno
limpio):
1. `validation/partido/probar_entrega.py prueba_d7_v5 --capa dead_ball.ball_out --contra equipo_v5`: genera la
   entrega de prueba, cuenta el balón fuera y la compara con `equipo_v5`;
2. `validation/partido/comparar_entregas.py equipo_v3 prueba_d7_v5`: la compara con la de antes de las dos capas.

**Pasa si se cumple todo esto:**
0. **Procedencia:** la salida del paso 1 dice un commit de `main` desde `f733af5` (el que sube esta entrada) que
   **todavía no lleva `dead_ball.ball_out` en `pipeline.DELIVERY_LAYERS`**, «sin cambios locales en el código de la
   entrega», «capa añadida dead_ball.ball_out», y las versiones de Python y numpy. Con la capa ya encendida,
   `--capa` la sumaría dos veces (peso 10) y la salida no lo diría; por eso el commit que la enciende hace que
   `build` dé error en ese caso. Además, la columna «antes» de cada comparación tiene que ser la de la entrega
   apuntada: 219 posesiones y 113 paradas (`equipo_v5`, paso 1) y 215 y 113 (`equipo_v3`, paso 2). Si algo de esto
   no se cumple, esa salida no vale y se repite.
1. **Sin conflictos ni rachas cortas:** 0 frames con piezas en conflicto. En los dos tramos, 0 posesiones, 0 rachas
   de juego y 0 paradas de menos de 25 frames.
2. **La banda del plan:** el `D` no pasa del 60 % de los frames evaluados y las paradas no pasan de 250. El `D` se
   lee en «frames por etiqueta» del resumen y se divide entre 158.857: fuera de los tramos evaluados la entrega
   escribe `X`.
3. **Frente a `equipo_v5`** (paso 1, la comparación):
   - a. **cambia algo, y no mucho:** de 1 a 1.000 frames evaluados. Ayer cambiaron 574. Con el balón fuera y `H` o
     `A` en `equipo_v3` había 843 frames; lo demás es margen para el arrastre del decodificador. Si no cambia
     ninguno, la capa no se ha aplicado;
   - b. el 90 % o más de los frames que cambian pasan de `H` o `A` a `D`. Ayer, el 100 %;
   - c. de `D` a `H` o `A`, 25 frames o menos (1 s). La capa solo suma a `D`: esto solo puede venir del arrastre del
     decodificador;
   - d. de un equipo al otro (`H → A` más `A → H`), 82 frames o menos, el 10 % de 817. Acota el arrastre del
     decodificador entre equipos: frames de los 817 que vuelven al equipo de `equipo_v3`, más cambios de equipo
     nuevos. Lo que esta capa puede quitarle a la de los contraataques por la vía principal (de un equipo a `D`) no
     lo ve este criterio, sino el 4;
   - e. las paradas suben 6 como mucho (de 113 a 119 o menos). Ayer subieron 3, y el doble deja margen al solape.
     Cada parada nueva tendría que salir de una racha en que nuestro `D` no llegaba en 10 s, y eran 10;
   - f. las posesiones no suben más que las paradas: cada posesión nueva tiene que venir de una parada nueva que
     parte una posesión.
4. **La capa de los contraataques no pierde lo que arregló:** (`H → A` más `A → H` del paso 2, frente a `equipo_v3`)
   menos (`H → A` más `A → H` del paso 1, frente a `equipo_v5`) da 736 o más, el 90 % de los 817 de `equipo_v5` (274
   de `H` a `A` y 543 de `A` a `H`).
   - Por qué la resta: fuera de los 817, `equipo_v3` y `equipo_v5` son iguales. Si de los 817 se conservan C, vuelven
     al equipo de antes V y pasan a `D` los demás, y hay N cambios de equipo nuevos fuera de ellos, el paso 2 cuenta
     C + N y el paso 1, V + N. La resta da C − V, una cota inferior de los que se conservan.
   - Contar solo el paso 2 dejaría pasar cambios nuevos como si fueran arreglos conservados.

Descriptivo, no decide: el recuento del balón fuera (paso 1). Espero unas 12 rachas tarde de 47, como ayer. No es un
criterio: es el que falló ayer y Ismael ha decidido no exigirlo.

Las celdas «< 5» de las comparaciones (de 1 a 4 frames) cuentan como 4 si van en contra de un criterio y como 1 si
van a favor.

Corregido el 16/11, antes de generar nada, tras una revisión de esta lectura: el criterio 0 exige un commit sin la
capa encendida y las bases de cada comparación; el 4 pasa a contarse con la resta (antes contaba solo el paso 2, en
neto); y el porqué de 3d dice lo que mide. Los umbrales no han cambiado.

**Si falla alguna:** no se enciende nada. No se retocan ni la capa ni los umbrales. Se para, se le cuenta a Ismael con
la salida y se apunta aquí.

**Si pasan todas:**
- se añade `dead_ball.ball_out` **al final** de `pipeline.DELIVERY_LAYERS`, detrás de la de los contraataques. Es el
  mismo orden de suma que en la prueba, para que salga la misma huella;
- el harness no cambia: `pipeline.run` no usa `DELIVERY_LAYERS`;
- se pasan las pruebas y se sube a `main`;
- Ismael regenera la entrega sin opciones, en el entorno limpio. Tiene que dar, byte a byte, el sha256 de
  `prueba_d7_v5`. Después se valida.

**Resultado de `prueba_d7_v5`** (16/11; la generó Ismael en el entorno limpio con `main` en `4b666f4`) [medido, solo
agregados]: **pasa todos los criterios.** La salida entera se pegó en la sesión que la implementa.
0. Se cumple. Python 3.13.9 y numpy 2.5.4; commit `4b666f4`, sin cambios locales en el código de la entrega y sin la capa
   en `DELIVERY_LAYERS` (sigue siendo solo la de los contraataques); «capa añadida dead_ball.ball_out». Las bases
   cuadran: 219 posesiones y 113 paradas en `equipo_v5`, y 215 y 113 en `equipo_v3`.
1. Se cumple: 0 frames en conflicto y ninguna racha de menos de 12 ni de 25 frames en los dos tramos.
2. Se cumple: el `D` ocupa el 45,4 % de los frames evaluados (72.199 de 158.857), y hay 116 paradas (54 y 62).
3. Frente a `equipo_v5`, se cumplen las seis:
   - a. cambian 574 frames evaluados (0,361 %), todos a más de 250 frames de un borde;
   - b. todos pasan de un equipo a `D`: 331 de `H` y 243 de `A`;
   - c. ninguno pasa de `D` a juego;
   - d. ninguno pasa de un equipo al otro;
   - e. las paradas pasan de 113 a 116, 3 más;
   - f. las posesiones no se mueven (219 y 219).
4. Se cumple: 817 − 0 = 817. Frente a `equipo_v3` cambian 1.391 frames: 274 de `H` a `A` y 543 de `A` a `H`, los mismos
   de `equipo_v5`, y 331 y 243 a `D`, los mismos de `prueba_d7`.

Descriptivo: llegamos tarde en 12 de 47 rachas de balón fuera (25,5 %), y en 7 nuestro `D` no llega en 10 s. Es lo mismo
que con `prueba_d7`.

Lectura: las dos capas no se tocan [inferencia, por los recuentos]. Lo que cambia esta capa sobre `equipo_v5` tiene los
mismos recuentos que lo que cambiaba sobre `equipo_v3` (331 y 243 a `D`, 3 paradas más), y los 817 cambios de equipo
siguen enteros [medido]. El validador oficial la da por válida (199.319 filas, 219 posesiones de 15,8 s de
media). Su sha256 es `d78c514dcf5e8ad9bcff5f76da0aadf409c01ce89ad65ad0435421daf31ce2b2`.

**Se enciende:** `pipeline.DELIVERY_LAYERS = (transiciones.evidence_equipo, dead_ball.ball_out)`. `build` da error si
`--capa` repite una capa de la entrega. La entrega nueva será `equipo_v8`, y tiene que dar el sha256 de `prueba_d7_v5`.

**Resultado (16/11) [medido]: `equipo_v8`, la entrega vigente.**
- Ismael la regeneró con el comando del entorno limpio (`python -m possession.pipeline --name equipo_v8`) y `main` en
  `44678d1`, sin cambios locales en el código de la entrega y sin capas añadidas. La línea de las versiones no se pegó,
  así que el entorno queda [sin verificar]. `prueba_d7_v5`, con la misma huella, sí salió con Python 3.13.9 y numpy
  2.5.4; y esta huella ya ha aguantado otras veces un cambio de numpy, así que coincidir no lo prueba.
- Falta reproducirla en otra máquina. En el ensayo de esta noche tiene que salir `d78c514d…e2b2`, no la de `equipo_v5`.
- **Sale byte a byte igual que `prueba_d7_v5`:** sha256 `d78c514dcf5e8ad9bcff5f76da0aadf409c01ce89ad65ad0435421daf31ce2b2`.
- 0 frames en conflicto y ninguna racha corta; 219 posesiones (103 y 116) y 116 paradas (54 y 62).
- El validador oficial la da por válida: 199.319 filas, 219 posesiones de 15,8 s de media.
- Frente a `equipo_v5`: 574 frames de un equipo a `D`, ningún otro cambio.

**En la ventana pública** (lo pidió Ismael; comprobación, no elige) [medido con `evaluation/run_evaluation.py
--bootstrap 1000`, sobre `prueba_d7_v5`, que es el mismo fichero]:
- spellF1 igual: 0,658 en `equipo_v5` y en la nueva. El scorer dice que, con 17 posesiones, una diferencia de hasta
  0,39 es ruido.
- macroF1 de 0,851 a 0,865, y transF1 (±25 frames) de 0,263 a 0,308. Los frames que pasan a `D` dentro de la ventana
  coinciden con `D` en la GT más de lo que no coinciden [inferencia, por el macroF1].
- Lectura: no rompe nada en la ventana. Si mejora el `spellF1` del partido no se puede saber: ni la ventana ni la DFL lo
  miden.

### 2026-11-16 · validación · en los cambios pequeños hacia control, el flag pasa de veto a límite de daño

Quién: Ismael (16/11), sobre la recomendación de la sesión principal: «Me parece bien tu recomendación con límite de
daño». Escrita antes de medir ningún candidato con ella.

Qué se decide: una regla de entrada nueva para los cambios que se pueden medir en datos abiertos y que ganan con las
etiquetas de control y en SkillCorner pero empatan o pierden poco con el flag (el punto débil 3 de
`docs/investigacion_2026-11-16.md`: el coste 40 y «cortas a `D`» se quedaban fuera por el veto del flag).

Un candidato de ese tipo entra si se cumple todo, frente a `main`:
1. **DFL con control:** +0,005 o más en las dos condiciones del balón que votan, ganando en 6 de 7 partidos en cada una.
   Si toca el `D`, con el `D` propio y en los dos modos del balón en los `D` (tapado y a la vista).
2. **SkillCorner:** gana en la mitad de entrenamiento y lo confirma **una sola vez** en la de examen
   (`lector.EXAMEN`), con +0,005 o más y ganando en 7 de 10. El umbral se escribe antes de abrirla y cada uso del
   examen se apunta aquí. Ismael dio el permiso para abrirlo el 16/11. **Usado el 16/11 por el candidato
   «cortas a `D`» con el corte de 125 frames** (ver la entrada «la idea 1.3 se desaparca»). `CLAUDE.md` lo lee
   como una vez **por candidato**, así que esto no agota el examen para otros candidatos.
3. **DFL con el flag:** no pierde más de 0,005 en ninguna celda (condición × modo del `D`).
4. **Entrega de prueba** frente a la vigente, con criterios de daño escritos antes de generarla.

Lo que no cambia:
- Lo que dice ganar con las dos convenciones sigue con §5.8 (+0,03).
- Las capas que solo corren en el partido siguen con sus criterios propios.
- El balón del vídeo tiene su propia regla (`validation/balon_video/BITACORA.md`).
- No usa la tabla de retrasos ni las notas oficiales del partido completo (D21).

Por qué:
- El equipo decidió el 12/11 «exigir control».
- La ventana pública tiene 4,23 posesiones por minuto de juego, típico de control (4,71) y no del flag (8,30)
  [descriptivo, revisión externa A.6].
- SkillCorner, que también exige control, dice lo mismo que control en los sondeos del 16/11.

Riesgo: si la GT se parece al flag, cada cambio de este tipo puede costar hasta 0,005.

Descartado:
- Mantener el veto: deja fuera cambios pequeños y consistentes en la dirección que eligió el equipo.
- Decidir solo con control: si la GT se parece al flag, la pérdida no tendría límite.

Estado: la idea 1.3 («cortas a `D`»), la candidata que lo motivó, queda aparcada (Ismael, 16/11). Nada entra solo por
esta decisión.

### 2026-11-16 · balón · se abre la línea del balón sacado del vídeo táctico, con sus puertas escritas antes de medir

Quién: Ismael (16/11), que pide centrarse en detectar el balón en el vídeo, con el modelo
`martinjolif/yolo-football-ball-detection` (YOLO11n afinado, AGPL-3.0) como primera opción.

Qué: un detector de balón público, ejecutado en local sobre el vídeo táctico, para tener un balón sin el suavizado de
1 s del ATD. Solo lo vería la evidencia de equipo (B5); el `D` sigue con el balón del ATD.

Cómo se decide: cuatro puertas escritas antes de medir en `validation/balon_video/BITACORA.md`:
- puerta 0: el acierto del detector según el tamaño del balón, en datos abiertos;
- puerta 1a: el tamaño del balón en el partido (`validation/partido/tamano_balon_video.py`, lo ejecuta Ismael);
- puerta 1b: si el balón del detector trae toques que el ATD no trae;
- puerta 2: la entrada, con la DFL degradada «como el vídeo», la entrega de prueba, la reproducción byte a byte con la
  detección dentro del comando y 8 horas como mucho.

Es la tercera excepción a «lo que no ha ganado en el harness no entra»: la DFL no tiene vídeo.

Riesgos apuntados antes de empezar:
- el balón puede medir unos 4 px (era una cuenta, no una medida);
- la entrega tiene que regenerarse byte a byte con una red dentro, y eso no está garantizado entre máquinas;
- el tiempo de cálculo.

`equipo_v8` no cambia mientras no pase la puerta 2.

### 2026-11-16 · `D` · estado con árboles (idea 2.4): candidatos y regla de entrada, escritos antes de medir

Quién: Antonio, con la tarea asignada el 16/11 (idea 2.4 de `docs/investigacion_2026-11-16.md`). La pieza
(`possession/dead_state.py`) es de Ana: no se toca salvo que un candidato gane, y entonces solo con una función nueva
apagada.

Qué se probó: todavía nada. Esta entrada fija los candidatos, lo que queda fijo y la regla, antes de entrenar ni medir.

- **Candidatos (dos):**
  - **G2:** árboles con *boosting* con los 11 rasgos de E2;
  - **G3:** lo mismo con los 19 rasgos de E3 (E2 más las ventanas solo hacia atrás y solo hacia delante, de 2 y 4 s).
- **Referencia:** E2, el modelo de `main` (la regresión logística de la entrada del 14/11).
- **Lo que queda fijo y no se ajusta:**
  - `HistGradientBoostingClassifier` de `scikit-learn` 1.7.2 con `learning_rate` 0,1, 200 árboles, 15 hojas por árbol,
    200 frames por hoja como mínimo, `l2_regularization` 1, sin parada temprana y `random_state` 0, entrenado con un
    solo hilo para que dos ejecuciones den lo mismo. Son valores comunes fijados ahora; no se prueba ningún otro;
  - las muestras de E2: uno de cada 5 frames con etiqueta y con todos los rasgos, `D` frente a juego;
  - la salida, como E2: el logaritmo de la razón de probabilidades en la columna `D`, cero donde falta algún rasgo,
    recortado a ±8 y redondeado a la rejilla de `SCORE_GRID`; escala 1;
  - el decodificador y sus costes, los de `main`.
- **Entorno:** uno aparte (`scikit-learn` 1.7.2, numpy 2.4.6, Python 3.11) que no entra en `requirements-entrega.txt`.
  Reproduce el `MODEL` de E2 bit a bit (`entrenar.py --comprobar`).

Cómo se medirá (dataset, nº de partidos/posesiones, métrica): los 7 partidos de la DFL (Bassek et al., 2025, CC BY 4.0).
Cada candidato puntúa un partido con los árboles entrenados en los otros seis.

1. **Harness con el `D` propio:** el pipeline de `main` con su `dead_state` cambiado por el candidato. Ocho celdas: las
   dos convenciones (flag y control) × las dos condiciones que votan («como el ATD» y «como el ATD, sin bloques») × el
   balón en los `D` tapado (como `puntuar.py --d propio`) y a la vista (como `con_balon_en_d` de
   `validation/apuesta_b/d_propio.py`).
2. **El criterio del 13/11** de `validation/scripts/d_estado/medir.py`, con E2 medido en la misma ejecución, también
   dejando un partido fuera.

Decisión y por qué (la regla de entrada, fijada antes de medir):
- **Un candidato gana si cumple las dos cosas:**
  1. **Harness:** frente a `main`, +0,010 o más de `spellF1` con los 7 partidos juntos y gana en 6 de 7 partidos, **en
     cada una de las ocho celdas**. El intervalo del bootstrap se enseña pero no decide.
  2. **No empeora el criterio del 13/11** frente a E2:
     - sigue cumpliendo las dos condiciones que E2 cumple: 0,3 `D` espurios o menos por minuto de juego y ninguna racha
       de menos de 25 frames;
     - el inicio y el fin a 25 frames o menos no bajan más de 1 punto (lo que redondea la tabla);
     - el sesgo mediano de cada borde, en valor absoluto, no sube más de 1 frame.
- **Si ganan los dos, entra G2,** salvo que G3 le gane con la regla 1 en las ocho celdas.
- **Si gana,** la predicción de los árboles pasa a numpy en `dead_state.py` como función nueva **apagada** (los árboles
  como arrays en el módulo), determinista y redondeada a la rejilla de `SCORE_GRID`, con su prueba en
  `validation/scripts/`, y PR. Encenderla es otra decisión, con su entrega de prueba.
- **Si no gana ninguno,** se apunta lo medido y la idea 2.4 se cierra. Nada de lo de arriba se vuelve a probar con otros
  valores.

Descriptivo, sin voto: AUC por frame, paradas detectadas y `spellF1` con equipo oráculo de `medir.py`; el placebo
(desplazada 60 s); la escala a la mitad y al doble; un temblor de 0,1 y 0,2 m en los jugadores; las condiciones del
balón sin voto; y una fila de E2 dejando un partido fuera en el harness.

Avisos, escritos antes de medir:
- **`main` está en muestra en el harness:** su `MODEL` se entrenó con los 7 partidos, y el candidato deja fuera el que
  se puntúa. Eso juega en contra del candidato. La fila de E2 dejando un partido fuera dice cuánto.
- **E2 ya es frágil con un temblor en los jugadores** (detecta el 61 % de las paradas con 0,1 m; entrada del 14/11).
  Si los árboles lo son más, se apunta como riesgo y lo decide el equipo; no cambia la regla.
- **La regla pide ganar también con el flag.** Es más estricta que la del límite de daño del 16/11.

Descartado (antes de medir):
- **Probar otros valores de los árboles** (más árboles, más hojas, otra tasa): sería ajustar mirando la medida.
- **Usar el balón:** lo mismo que el 14/11; delataría el `D` en la DFL.
- **Una red o un bosque aleatorio:** con dos candidatos como mucho, se prueba el *boosting*, que es lo que mejor salió
  en Lang et al. (2022) (allí AdaBoost; aquí el *gradient boosting* por histogramas de `scikit-learn`, que entrena rápido).

### 2026-11-16 · `D` · estado con árboles (idea 2.4): ningún candidato gana; se cierra

Quién: Antonio

Qué se probó: G2 y G3, los dos candidatos de la entrada anterior, frente a E2, con su regla.

Cómo se midió (dataset, nº de partidos/posesiones, métrica): los 7 partidos de la DFL dejando uno fuera (713 paradas),
con `validation/scripts/d_estado/medir_arboles.py`: el criterio del 13/11 con las funciones de `medir.py` y el harness
con el `D` propio, con el balón tapado y a la vista en los `D`. Detalle en
`validation/resultados/2026-11-16_d_estado_arboles.md`.

Resultado:
- **[medido] Harness, regla 1 (+0,010 y 6 de 7 en las ocho celdas):**
  - **G3 no cumple en 1 de 8:** con el balón tapado, «como el ATD, sin bloques» y el flag, +0,008 y gana en 5 de 7. En
    las otras siete, de +0,011 a +0,030 y 6 o 7 de 7;
  - **G2 no cumple en 4 de 8,** las cuatro con el balón tapado (de −0,001 a +0,006). Con el balón a la vista, de +0,011
    a +0,019.
- **[medido] Criterio del 13/11, regla 2:** los dos lo mejoran y ninguno empeora nada. G3: inicio y fin a 25 frames o
  menos en el 47 % y el 54 % de las paradas (E2: 35 % y 40 %), sesgo mediano de +5 y 0 frames (E2: +14 y +17) y 0,16
  `D` espurios por minuto (E2: 0,26). Ninguno llega al 70 % que pide el criterio.
- **[medido] Descriptivo:**
  - con el equipo oráculo, G3 gana a E2 por +0,034 a +0,046 y G2 por +0,023 a +0,028;
  - placebo: con la puntuación desplazada 60 s, AUC 0,52 y `spellF1` 0,22 a 0,28 por debajo de no opinar;
  - con un temblor de 0,1 m en los jugadores, los árboles detectan el 46 % de las paradas (E2, el 61 %);
  - E2 dejando un partido fuera queda a −0,001 o menos de `main`: estar en muestra no le da ventaja.

Decisión y por qué:
- **Ningún candidato gana con la regla fijada antes de medir. La idea 2.4 se cierra** y `possession/dead_state.py` no
  cambia. No se escribe la predicción en numpy ni se abre la PR del paso 4.
- **G3 se queda cerca:** gana en siete de las ocho celdas y mejora los bordes en el criterio del 13/11. La regla no
  cambia después de medir. Si el equipo quisiera volver sobre G3, sería otra decisión, con su regla escrita antes.
- **Riesgo apuntado:** los árboles son más frágiles que E2 si los jugadores del ATD tiemblan.

Descartado:
- **G2 y G3,** por la regla 1. Los parámetros de los árboles no se prueban con otros valores (entrada anterior).
### 2026-11-16 · decodificador · la idea 1.3 («cortas a `D`») se desaparca y se implementa apagada

Quién: Manuel, por encargo de Ismael (16/11). **Reglas escritas antes de medir nada con ellas.**

**Ojo con el estado anterior:** la entrada «el flag pasa de veto a límite de daño» de hoy dice que la idea 1.3
«queda aparcada (Ismael, 16/11)». Este encargo la desaparca y la lleva hasta la entrega de prueba con esa misma
regla de límite de daño. El permiso para abrir el examen de SkillCorner es del mismo día.

> **Estado al cerrar esta entrada:** las cuatro condiciones del límite de daño pasan y la variante se queda
> **apagada**; la entrega sigue siendo `equipo_v8`. **El examen de SkillCorner se abrió el 16/11 para este
> candidato, con el corte de 125 frames** (ver «El examen de SkillCorner» más abajo). `CLAUDE.md` lo permite
> una vez **por candidato**, así que no queda agotado para otros. Antes de encender nada, leer también el
> apartado «El corte de 125 frames no es el único que pasaría».

**`possession/temporal.py` es la pieza de David,** así que la PR le pide la revisión a `ortegafer`. El cambio es
solo aditivo: `decode`, `decode_min`, `decode_prune`, `prune`, `runs`, `viterbi`, `viterbi_min`, `_prepare` y
las constantes de antes quedan idénticas, y `pipeline.PIECES` no se toca. Conviene que lo sepa porque ahí vive
lo que él está midiendo. **No se ha comparado «cortas a `D`» con su `decode_prune`,** que también quita
posesiones cortas: son reglas distintas (la poda pasa la racha corta al otro equipo si lo tiene al lado; esta la
pasa a `D` solo si acaba en parada), pero medirlas juntas no se ha hecho y sería lo siguiente si al equipo le
interesa.

Qué se ha hecho: `temporal.cortas_a_d` y `temporal.decode_cortas_a_d(score, allowed, blocks, params=None,
corte=125)` en `possession/temporal.py`, **apagadas**: no están en `pipeline.PIECES` y la entrega no cambia.
Es el Viterbi de `decode` y después, en cada tramo, las posesiones de menos de `corte` frames que vienen de un
cambio directo desde el otro equipo y acaban en `D` pasan a `D`. `corte` es una duración (125 frames son 5 s a
25 fps, la frecuencia del partido, de la DFL y de SkillCorner), no un frame de este partido.

**Es la misma lógica que S9** [medido, sin datos]: `validation/scripts/prueba_cortas_a_d.py` comprueba en 400
casos inventados que, con `D` permitido en todas partes, da exactamente lo mismo que la variante «a D» de
`validation/investigacion_1116/paquete_control.py` (las candidatas de `cambio_antes_de_parada.candidatas`
puestas a `D`). La prueba compara además el AST de `candidatas` con la copia que usa, así que si alguien cambia
la referencia, falla y hay que repetir la medida. Es lícito meterla dentro del decodificador porque
`pipeline.run` acaba en `return decode(score, allowed, trk.blocks, params)`: el decodificador es el último paso
y recibe los mismos tramos, así que hacerlo dentro o fuera es lo mismo.

**Una diferencia a propósito con S9:** `cortas_a_d` no convierte una candidata si `D` está prohibido en alguno
de sus frames, como hace `prune`. S9 no mira `allowed`. En el partido eso importa en el frame del saque de cada
parte, donde `dead_ball.evidence` prohíbe `D` (PR 16).

**En datos abiertos la puerta es inerte, así que la reproducción de S9 es exacta** [medido por inspección, lo
apuntó el `revisor` y se comprobó con `grep allowed\\[ possession/`]: el único sitio de `possession/` que
restringe `allowed` es `dead_ball.py`, que solo opina con las rutas del partido; `aprendida.evidence_b5` y
`dead_state.evidence` salen las dos de `no_evidence`, que deja `allowed` entero a `True`, y con el `D` propio no
se añade la evidencia del oráculo. En la DFL y en SkillCorner `cortas_a_d` es por tanto bit a bit
`cambio_antes_de_parada.candidatas`, y el riesgo queda acotado al partido: un frame por parte.

**Comprobado sin datos del partido** [medido]: 759 casos en verde de `prueba_cortas_a_d.py` y 20 de
`prueba_cortas_en_contraataques.py`; `leer_versiones` del harness valida la versión y la ejecuta sobre su
partido inventado; las pruebas de David (`prueba_decodificador.py`) y `prueba_pipeline.py` siguen en verde.
**Sabotajes** (en memoria, fuera del repo):
17 roturas, una a una (el corte estricto, el límite de largo, que acabe en `D`, el cambio directo, el equipo de
antes, la primera y la última racha del tramo, `allowed`, pasar al equipo de antes, no copiar, encadenar las
candidatas, los tramos sin volverse tupla, la validación del corte, los `params`, el corte por defecto y el
corte por tramos): **las 17 se cazan.** Dos escapaban al principio porque el sabotaje caía en las líneas
idénticas de `decode_prune`, y una tercera porque con evidencia al azar las rachas no llegan a 125 frames y el
valor del corte no se ejercitaba; de ahí la prueba con evidencia forzada.

**Puerta de entrada: la regla del límite de daño de hoy.** Las cifras que tiene que reproducir son las de S9
(columna «cortas a `D`», `D` propio, diferencia de `spellF1` frente a `main`):

| etiquetas | balón en los `D` | «como el ATD» | «sin bloques» |
|---|---|---|---|
| DFL flag | a la vista | +0,004 (5 de 7) (*) | +0,004 (5 de 7) (*) |
| DFL flag | tapado | −0,002 | −0,002 |
| DFL control | a la vista | +0,018 (7 de 7) | +0,019 (7 de 7) |
| DFL control | tapado | +0,007 | +0,009 |
| SkillCorner entrenamiento | – | +0,010 (10 de 10) | +0,009 (10 de 10) |

En la DFL las dos columnas son las dos condiciones que votan, «como el ATD» y «como el ATD, sin bloques». **En
la fila de SkillCorner son sus dos condiciones, «detectado» y «detectado, suavizado»** (`lector.VOTAN`), no las
de la DFL: se reproducen con el script de SkillCorner, no con el de la DFL.

(*) **La tabla de la bitácora** de S9 da ese «5 de 7» una sola vez, para una celda que colapsa las dos
condiciones. Pero **su salida sí los publica por separado** (`validation/investigacion_1116/salidas/
2026-11-16_s9_paquete_control.md`), y son 5 de 7 en las dos, igual que sale al reproducirlo: no era ninguna
inferencia, solo una lectura incompleta de la bitácora.

Sobre el papel **no contradice** ninguna de las tres condiciones medibles en abierto: con el control da +0,005
o más en las cuatro celdas y con el flag no pierde más de 0,005 en ninguna. La condición 1 pide además ganar en
6 de 7 partidos *en cada celda*, y **la tabla de la bitácora** de S9 solo trae el recuento por partido en dos de
las cuatro celdas de control (las de «a la vista», 7 de 7), con un «26 de 28» agregado que no excluye que una
celda se quede en 5 de 7. **Si al reproducirlas no salen las mismas cifras, se para y se averigua por qué antes
de seguir.**

(Corregido después, porque se escribió mal dos veces: lo que faltaba estaba solo en **la tabla** de la bitácora.
Las **salidas** de S5 y de S9 que ya estaban en `main` publican los cuatro recuentos, así que la condición 1 no
estaba «por comprobar»: ya se podía leer en el repo. Reproducido sale lo mismo, 6 de 7 en las dos celdas.)

**Las medidas se hacen siempre con el `D` propio, nunca con el oráculo.** Con el `D` oráculo,
`puntuar.d_oraculo` prohíbe `D` donde las etiquetas tienen juego y `pipeline.combine` cruza los `allowed`, así
que la puerta `allowed[start:stop, D].all()` de `cortas_a_d` solo dejaría pasar las candidatas que ya son `D`
de verdad: la regla saldría correcta por construcción y el número vendría del oráculo, no de la señal. El
harness usa el oráculo **por defecto**, así que se mide con `validation/scripts/cortas_a_d_dfl.py` (que no
admite oráculo y da los dos modos del balón) y con `cortas_a_d_skillcorner.py`. Lo encontró el agente `revisor`
antes de medir nada.

**Medir con el `D` propio es una excepción consciente al párrafo final de `docs/PLAN_ENTREGA.md` §4**, que dice
que «ningún número con `D` propio que dependa del balón se da por bueno». La condición 1 del límite de daño
(16/11) es posterior y pide expresamente el `D` propio en los dos modos del balón, porque esta regla toca el
`D`: con el `D` oráculo no se puede medir, igual que no se pueden medir en el harness las capas que solo corren
en el partido. Queda apuntado aquí para que el plan y esta entrada no se lean como una contradicción.

**Con qué se mide** (los dos los puede ejecutar Claude, examen incluido: SkillCorner son datos abiertos y la
regla nº 1 no está en juego. Lo que el examen exige no es una persona, sino una **autorización explícita** del
equipo en el momento y la bandera `--confirmo-el-unico-uso`, para que no se gaste por inercia):
- **DFL, las ocho celdas:** `validation/scripts/cortas_a_d_dfl.py`. Hacía falta un script propio porque
  `validation/harness/puntuar.py --d propio` solo da el modo «tapado» y las condiciones 1 y 3 piden también «a
  la vista», que vive en `validation/apuesta_b/d_propio.py`; y porque `paquete_control.py` mide su propia copia
  de la lógica, no `temporal.decode_cortas_a_d`.
- **SkillCorner:** `validation/scripts/cortas_a_d_skillcorner.py`, que por defecto usa solo la mitad de
  entrenamiento. `validation/skillcorner/medir.py` no servía: no acepta `--versiones` y por defecto usa los 20
  partidos, **examen incluido**.

**Umbral del examen de SkillCorner, escrito antes de abrirlo:** entra si en `lector.EXAMEN` (los 10 partidos
que nadie ha tocado) gana a `main` por **+0,005 o más** y gana en **7 de 10** partidos, en las dos condiciones
que votan allí. Se ejecuta **una sola vez para este candidato** (`CLAUDE.md`: una vez por candidato), con el
permiso que dio Ismael el 16/11, y el uso se apunta aquí y en `validation/skillcorner/BITACORA.md`.

**Criterios de daño de la entrega de prueba, escritos antes de generarla** (`prueba_cortas_a_d` frente a
`equipo_v8`):
1. **0 frames evaluados con piezas en conflicto** y ninguna racha de menos de 25 frames en ningún tramo.
2. **El 100 % de los frames que cambian pasa de `H` o `A` a `D`.** Por construcción no puede cambiar nada más
   (la prueba lo comprueba); si sale otra cosa, hay un error y se para.
3. **Dentro de la banda del plan** (§3, 15/11): del 15 al 60 % de `D` en lo evaluado y 250 paradas como mucho.
4. **Cuántas posesiones quita:** se apunta el número. No hay umbral, pero se lee con cuidado, porque el punto
   débil conocido del pipeline es que predice **menos** posesiones de las que hay (219 en `equipo_v8`, frente a
   los 4,11 por minuto vivo de SkillCorner y los 4,26–4,29 de la DFL con nuestro `D`), y esta regla solo puede
   quitar más. **Corregido después de medir:** aquí se escribió «3,7 por minuto vivo» para `equipo_v8`, y ese
   3,70 es de `equipo_v3` (215 posesiones; `validation/resultados/2026-11-15_posesiones_cortas.md`).
   `equipo_v8` va a 3,79. La errata no cambia el criterio, que era apuntar el número y leerlo con cuidado.
5. **Cuántas de las posesiones que quita caen en los 5 primeros segundos de una «Attacking Transition» del
   Smart Tagging** (la capa de los contraataques, encendida en la entrega):
   `validation/partido/cortas_en_contraataques.py`. **Si son más de 2, se para y se avisa,** porque la regla
   estaría borrando lo que esa capa acaba de crear.

Lo que no cambia: la entrega sigue siendo `equipo_v8` y `pipeline.PIECES` no se toca. Que entre o no lo decide
el equipo con estos números.

**Resultado en datos abiertos (16/11, Manuel, con la rama en `84b2ccc`) [medido]: reproduce S9 celda por
celda, y las condiciones 1 y 3 pasan.**

Lo ejecutó Claude (son datos abiertos): `validation/scripts/cortas_a_d_dfl.py` y
`cortas_a_d_skillcorner.py`, con el fichero de versiones `cortas_a_d_2026-11-16.json` (huella
`7d0ba8cf…425e`). DFL: 7 partidos, `D` propio, los dos modos del balón. SkillCorner: los 10 de
`lector.ENTRENAMIENTO`.

| etiquetas | balón en los `D` | «como el ATD» | «sin bloques» | S9 decía |
|---|---|---|---|---|
| DFL flag | a la vista | +0,004 (5 de 7) | +0,004 (5 de 7) | +0,004 / +0,004 (5 de 7) |
| DFL flag | tapado | −0,002 (2 de 7) | −0,002 (2 de 7) | −0,002 / −0,002 |
| DFL control | a la vista | +0,018 (7 de 7) | +0,019 (7 de 7) | +0,018 / +0,019 (7 de 7) |
| DFL control | tapado | +0,007 (6 de 7) | +0,009 (6 de 7) | +0,007 / +0,009 |
| SkillCorner entrenamiento | – | +0,010 (10 de 10) | +0,009 (10 de 10) | +0,010 / +0,009 (10 de 10) |

(en SkillCorner las dos columnas son «detectado» y «detectado, suavizado»)

- **Las diez cifras coinciden con S9**, así que la regla de parada del paso 3 no se activa.
- **Que la puerta `allowed` sea inerte en datos abiertos está [medido por inspección]**, no por estas cifras:
  el único sitio de `possession/` que recorta `allowed` es `dead_ball.py`, que solo opina con las rutas del
  partido, y `pipeline.combine` solo relaja conflictos. Que las cifras cuadren es coherente con eso, pero por sí
  solo sería [inferencia]: podrían cuadrar por compensación.
- **Se cierra lo que quedaba «por comprobar»:** el recuento por partido de las dos celdas de control con el
  balón tapado es **6 de 7 en las dos**. Suman 7+7+6+6 = 26 de 28, que es el agregado que daba S9. **La
  condición 1 pasa.**
  - **Matiz, para no vender esto como más de lo que es** (corregido dos veces, en la tercera y la cuarta
    revisión): lo único que no traía esos recuentos era la *tabla de la bitácora* de S9. **Las dos salidas que
    ya están en `main` sí los publicaban**, y las dos dicen lo mismo:
    `validation/investigacion_1116/salidas/2026-11-16_s5_cambio_antes_de_parada.md` y
    `…/2026-11-16_s9_paquete_control.md`, con 6 de 7 en las dos celdas de control con el balón tapado y 5 de 7
    en cada una de las dos del flag con el balón a la vista. Así que aquí no se descubre ningún número.
  - **Lo que sí aporta la reproducción:** que esas cifras salen **ejecutando `temporal.decode_cortas_a_d`**, la
    pieza que iría en la entrega, y no la copia de la lógica que vive en el sondeo. Y sale idéntica a la salida
    de S9 en los ocho valores absolutos (0,395 / 0,409 / 0,414 / 0,431 / 0,587 / 0,613 / 0,623 / 0,651) y en los
    ocho recuentos por partido.
- **El «5 de 7»** que la tabla de la bitácora daba una sola vez sale en las dos condiciones del flag con
  el balón a la vista: 5 de 7 en cada una, como ya publicaba la salida de S9.
- **Condición 1 (control): PASA.** Las cuatro celdas dan +0,0072, +0,0087, +0,0185 y +0,0192, todas por encima
  de +0,005, con 6 o 7 de 7.
- **Condición 3 (flag): PASA.** La peor celda pierde 0,0024, menos de los 0,005 del límite.
- **Condición 2: pasa la mitad de entrenamiento.** Falta la confirmación en `lector.EXAMEN`, sin abrir **en
  ese momento**; se abrió después, en el apartado siguiente.
- **El control queda muy por debajo en las ocho celdas** (de 0,257 a 0,397 frente a 0,391–0,642 de `main`), así
  que la variante no gana por un `main` flojo.

**Lo que faltaba al escribir esto:** la condición 2 en el examen y la condición 4 (entrega de prueba). Las dos
se cerraron el mismo día, más abajo. La entrega sigue siendo `equipo_v8`.

**El examen de SkillCorner: abierto el 16/11 para este candidato (Manuel, con la rama en `846a305`).** [medido]

`CLAUDE.md` dice que el examen «se puede abrir una vez **por candidato**», así que esto gasta el uso de «cortas
a `D`» con el corte de 125 frames, no el examen entero.

Lo autorizó Ismael el 16/11 y el umbral estaba escrito y commiteado antes de bajar los datos (+0,005 o más y
ganar en 7 de 10, en las dos condiciones). **Lo ejecutó Claude, con la autorización de Manuel en el momento**
(«Sí, ábrelo»), con `cortas_a_d_skillcorner.py --examen --confirmo-el-unico-uso`, sobre los 10 partidos de
`lector.EXAMEN` y el mismo fichero de versiones (huella `7d0ba8cf…425e`). SkillCorner son datos abiertos, así
que la regla nº 1 no lo impide; el guardarraíl es la autorización y la bandera, no que lo teclee una persona.

| condición | `main` | «cortas a `D`» | veredicto |
|---|---|---|---|
| detectado | 0,380 | 0,389 (+0,009, 10 de 10) | PASA |
| detectado, suavizado | 0,376 | 0,384 (+0,008, 10 de 10) | PASA |

- **Pasa las dos**, con margen sobre el umbral y ganando en los 10 partidos.
- Da una pizca menos que la mitad de entrenamiento (+0,010 / +0,009), que es lo que se espera de un conjunto
  que nadie había tocado. La diferencia es de 0,001: no hay señal de que el entrenamiento estuviera inflado.

**Estado de las cuatro condiciones del límite de daño:** 1 PASA, 2 PASA (entrenamiento y examen), 3 PASA.
**Faltaba solo la 4, la entrega de prueba,** que lee el partido y la ejecuta una persona; se cerró el mismo día,
en el apartado siguiente. La entrega sigue siendo `equipo_v8` y `pipeline.PIECES` no se toca.

**Condición 4, la entrega de prueba (16/11, la generó Manuel en su máquina) [medido, solo agregados]: pasa los
cinco criterios.**

`prueba_cortas_a_d`, con `python validation/partido/probar_entrega.py prueba_cortas_a_d --pieza
temporal=temporal.decode_cortas_a_d --contra equipo_v8`, con el código de `1fcf40f` y, según el propio comando,
«sin cambios locales en el código de la entrega». sha256 `d9706dfb…be63`.

1. **0 frames evaluados con piezas en conflicto** y ninguna racha de menos de 25 frames (ni de 12) en los dos
   tramos. **Cumple.**
2. **El 100 % de lo que cambia pasa de un equipo a `D`:** 1.167 frames de 158.857 (0,735 %), 609 de `H` y 558
   de `A`, y ninguno a otra cosa. Cuadra con los recuentos por etiqueta (`H` 54.445 → 53.836, `A` 32.213 →
   31.655, `D` 72.199 → 73.366). **Cumple.**
3. **Dentro de la banda del plan:** `D` en el 46,18 % de lo evaluado (45,45 % en `equipo_v8`) y 116 paradas.
   **Cumple.**
4. **Quita 18 posesiones:** 219 → 201 (103 → 95 en el tramo 1 y 116 → 106 en el 2). Las paradas no se mueven
   (116 → 116), que es lo que se espera: una candidata convertida se funde con el `D` que ya venía detrás, así
   que no crea ni destruye paradas.
5. **0 de las 18 caen en la ventana de un contraataque** (`cortas_en_contraataques.py`, con las 24 «Attacking
   Transition» con equipo), y 0 empiezan dentro. El criterio pedía 2 como mucho. **Cumple con holgura:** la
   regla no está borrando lo que crea la capa de los contraataques.

**Las dos comprobaciones de rutina que `probar_entrega.py` no hace** (las ejecutó Claude; los dos scripts leen
solo la entrega y la GT pública) [medido]:
- **El validador oficial la da por válida:** 199.319 filas, frames 0..199318, y 201 posesiones de 17,0 s de
  media.
- **En la ventana pública no se rompe nada:** spellF1 0,658 → **0,680** y macroF1 0,865 → **0,874** frente a
  `equipo_v8`. **No elige nada,** por la regla del repo: la ventana sirve para comprobar que el pipeline es
  correcto, nunca para elegir entre versiones. En el `spellF1` hay además una razón numérica —17 posesiones, y
  una diferencia de hasta 0,39 es ruido (`CLAUDE.md`)—; el `macroF1` es por frame y mucho menos ruidoso, pero
  tampoco decide. Lo único que dice esto es que la variante no rompe la alineación ni el formato.

Además [medido]:
- **Los 1.167 frames que cambian están todos a más de 250 frames del borde de un tramo evaluado,** y 0 cambian
  fuera de los tramos: no es un efecto de borde.
- **El balón fuera (D7) no se mueve:** con la variante llegamos tarde en 12 de 47 rachas (25,5 %), que es el
  valor apuntado para la capa `ball_out` que lleva `equipo_v8`. La comparación es contra ese registro, no
  contra una ejecución nueva de `equipo_v8`. La regla no arregla ese problema ni lo empeora.

**El punto en contra, que estaba apuntado antes de medir (criterio 4) y se confirma:** el pipeline ya predice
**menos** posesiones de las que hay, y esta regla quita más. Pasa de 3,79 a **3,53 por minuto de juego vivo**
[calculado aquí dividiendo las posesiones por los frames de `H` y `A`: 219/57,8 min y 201/57,0 min], cuando las
referencias en datos abiertos con nuestro `D` son 4,11 en SkillCorner y 4,26–4,29 en la DFL. El 3,70 que
aparece en `validation/resultados/2026-11-15_posesiones_cortas.md` **no es de `equipo_v8`**: es de `equipo_v3`,
que tenía 215 posesiones. `equipo_v8` va a 3,79, así que el ritmo baja de 3,79 a 3,53 y no de 3,7 a 3,53. Es
decir: **el harness y SkillCorner dicen que sube el `spellF1`, y a la vez el recuento de posesiones se aleja de
las referencias.** No es una contradicción —se gana emparejando mejor las posesiones que quedan, no teniendo
más— pero es el riesgo que hay que pesar si la GT se parece al flag, donde la regla da −0,002.

**Las cuatro condiciones del límite de daño pasan.** Encenderla (`pipeline.PIECES["temporal"]`) es una decisión
del equipo, no de esta rama: aquí la variante se queda **apagada** y la entrega sigue siendo `equipo_v8`.

### Lo más importante para mergear: esta rama no cambia la entrega [medido]

**Regenerada desde el commit de esta rama (`1fcf40f`), la entrega vigente sale byte a byte igual:** sha256
`d78c514dcf5e8ad9bcff5f76da0aadf409c01ce89ad65ad0435421daf31ce2b2`, el de `equipo_v8`, con 0 conflictos y los
recuentos apuntados (219 posesiones, 103 y 116; 116 paradas, 54 y 62; 45,45 % de `D`). El comando dijo «sin
cambios locales en el código de la entrega».

Es la comprobación que pide el repo cuando una PR toca código que usa la entrega: aunque `decode_cortas_a_d`
viva ya en el módulo del decodificador, `pipeline.PIECES` sigue con `decode` y no cambia ninguna etiqueta.

La medida se hizo con la rama en `1fcf40f`. Lo único que ha cambiado en `possession/` desde entonces es el
docstring de `cortas_a_d` (`git diff 1fcf40f..HEAD -- possession/`), que no puede cambiar ninguna etiqueta, así
que la huella sigue valiendo para el tip de la rama.

### Añadido: `equipo_v8` en una tercera máquina, con versiones nuevas [medido]

**Corregido al traer `main`:** esto se escribió como «la segunda máquina que pedía `CLAUDE.md`», y ya no lo es.
Antonio la reprodujo el mismo 16/11 en un Mac M1 (macOS, ARM) con Python 3.13.7, y está apuntado en `CLAUDE.md`.
Lo de aquí es **una tercera máquina**, y lo que añade no es cerrar ese pendiente, sino el entorno:

- **Windows con Python 3.14.4 y numpy 2.4.4**, en vez de los 3.13.9 y 2.5.4 fijados. Ojo con no mezclar
  huellas: el rango numpy 2.3.4 ↔ 2.5.4 es de `equipo_v3`/`equipo_v5`. **La huella de `equipo_v8` solo se había
  visto con numpy 2.5.4** (Python 3.13.9 en Windows y 3.13.7 en el Mac de Antonio), así que esta ejecución
  aporta dos cosas nuevas para `equipo_v8`: **el primer numpy distinto (2.4.4) y el primer Python 3.14**. No
  cambia lo fijado: `requirements-entrega.txt` sigue mandando para el congelado.
- Con un matiz que conviene que juzgue quien lleve el congelado: se generó desde `1fcf40f`, el commit de esta
  rama, no desde `main`. Como el sha256 es el mismo, eso no debilita la reproducción y además prueba lo del
  apartado anterior; pero si el ensayo del congelado quiere la reproducción «desde `main`» en sentido estricto,
  esto no la sustituye.

### El corte de 125 frames no es el único que pasaría

Lo encontró el agente `revisor` en la tercera pasada, **después** de abrir el examen. Es el punto que el equipo
tiene que discutir antes de encender nada.

**Por qué 125 y no otro:** porque es el corte que la regla de S5 fijó antes de medir (5 s) y el que midió S9.
No se eligió comparando cortes: se heredó. Esta rama no lo ha tocado.

**Pero la tabla de sensibilidad de S5 ya estaba en `main`** (`validation/investigacion_1116/salidas/
2026-11-16_s5_cambio_antes_de_parada.md`) y dice que **el corte de 3 s (75 frames) de la misma variante «a D»
también pasaría las condiciones 1 y 3**, y en algunos sitios mejor [medido, S5, no reproducido en esta rama]:

| celda | 75 frames (3 s) | 125 frames (5 s), lo medido aquí |
|---|---|---|
| control / tapado / como el ATD | +0,008 (7 de 7) | +0,007 (6 de 7) |
| control / tapado / sin bloques | +0,009 (7 de 7) | +0,009 (6 de 7) |
| control / a la vista / como el ATD | +0,014 (7 de 7) | +0,018 (7 de 7) |
| control / a la vista / sin bloques | +0,015 (7 de 7) | +0,019 (7 de 7) |
| flag / tapado / como el ATD | +0,000 (3 de 7) | **−0,002** (2 de 7) |
| flag / tapado / sin bloques | +0,001 (3 de 7) | **−0,002** (2 de 7) |
| flag / a la vista / como el ATD | +0,004 (5 de 7) | +0,004 (5 de 7) |
| flag / a la vista / sin bloques | +0,004 (5 de 7) | +0,004 (5 de 7) |

Lectura honesta, sin exagerar en ninguna dirección:
- **75 no pierde nada con el flag** (+0,000 a +0,004), y 125 pierde 0,002 en las dos celdas de «tapado». Como el
  riesgo de toda esta idea es justo «¿y si la GT se parece al flag?», ahí 75 es más seguro.
- **75 gana en 7 de 7 en las cuatro celdas de control**, frente a los 6 de 7 de 125 en las de «tapado».
- **125 gana más con el control y el balón a la vista** (+0,018 / +0,019 frente a +0,014 / +0,015). En las celdas
  de «tapado», 75 va igual o mejor.
- **No es una dominación limpia:** depende de qué celda se considere la que manda.

**Y cuál manda no está cerrado en el repo,** así que conviene decirlo antes de apoyarse en ello: la lectura de
que «tapado» es el modo que más se parece al ATD sale de que en **los 10 s antes de un `SET PIECES`** el ATD ve
el balón en el 27,6 % de los frames (`2026-11-14_perfil_atd.md`), y es la que usa
`docs/investigacion_2026-11-16.md` §2.1. Pero el mismo fichero da un 68 % mirando **las ventanas `SET PIECES`
enteras**, y con esa cifra S5 concluye lo contrario («con el balón a la vista… que es lo que pasa en el ATD»).
Con «a la vista» como modo que manda, 125 es mejor que 75. **Esta rama no resuelve cuál es la ventana correcta;**
solo avisa de que el argumento de «75 es más seguro» y la lectura de los intervalos dependen de esa elección.

**Lo que es mío como fallo de proceso:** se abrió el examen con 125 sin haber mirado antes esta tabla de
sensibilidad, que ya estaba en el repo. Si la hubiera leído, lo honesto habría sido plantear al equipo qué corte
llevar al examen **antes** de gastar nada.

**Lo que no es tan grave como escribí al principio** (lo corrigió el `revisor` en la quinta pasada):
`CLAUDE.md` dice que el examen «se puede abrir una vez **por candidato**», y el precedente de B9
(`docs/decisiones.md`, la regla de B9, paso 5) le reservaba su propia ejecución única. Así que **un candidato a
75 frames no se queda necesariamente sin confirmación ciega.**

**La pregunta que decide el equipo, no esta rama:** ¿un cambio de corte de la misma idea es un **candidato
nuevo**, con derecho a su propio uso del examen, o un **ajuste del mismo candidato**, que es justo la fuga de la
que el examen protege? No la resuelvo aquí: es la diferencia entre poder confirmar 75 a ciegas o no, y afecta a
un recurso de todos.
- Si cuenta como candidato nuevo: se mide 75 en la DFL y en entrenamiento (basta `"corte": 75` en el fichero de
  versiones) y, si pasa, se lleva al examen con su umbral escrito antes.
- Si cuenta como el mismo: 75 solo puede apoyarse en la DFL y en la mitad de entrenamiento, y eso hay que
  decirlo en el documento técnico.

**Y mientras eso no se decida,** lo que ha pasado la puerta completa es 125, que es lo único que esta rama
propone como medido.

### Los intervalos de la diferencia (añadidos tras la tercera revisión) [medido]

La regla del 16/11 no pide intervalo —usa el recuento por partido como sustituto—, pero `docs/PLAN_ENTREGA.md`
§4 sí lo pide para §5.8 y los márgenes aquí son estrechos, así que se midió con `cortas_a_d_dfl.py
--bootstrap 1000` (pareado sobre las posesiones reales, `puntuar.diferencia_bootstrap`).

**Qué son exactamente estos intervalos, porque toda la lectura de abajo se apoya en su extremo malo:** son los
**percentiles 5 y 95** (`puntuar.PERCENTILES`), es decir del 90 %; con un 95 % saldrían más anchos. Y el
remuestreo es de las posesiones reales **juntando los 7 partidos**, no partido a partido, así que no recoge la
varianza entre partidos: para eso está el recuento «x de 7», que es el sustituto que eligió la regla.

| celda | diferencia | intervalo |
|---|---|---|
| control / a la vista / como el ATD | +0,0185 | [+0,0154, +0,0216] |
| control / a la vista / sin bloques | +0,0192 | [+0,0158, +0,0227] |
| control / tapado / como el ATD | +0,0072 | [+0,0029, +0,0115] |
| control / tapado / sin bloques | +0,0087 | [+0,0044, +0,0133] |
| flag / a la vista / como el ATD | +0,0041 | [+0,0014, +0,0068] |
| flag / a la vista / sin bloques | +0,0042 | [+0,0013, +0,0069] |
| flag / tapado / como el ATD | −0,0023 | [−0,0057, +0,0008] (incluye el 0) |
| flag / tapado / sin bloques | −0,0024 | [−0,0060, +0,0012] (incluye el 0) |

**Lo que añaden, y no es menor:**
- **Las cuatro celdas del control ganan de verdad:** ningún intervalo incluye el 0.
- **Pero en las dos celdas de «tapado» el intervalo baja por debajo del umbral:** +0,0029 y +0,0044, frente a
  los +0,005 que pide la condición 1. El valor central pasa; la incertidumbre se solapa con el umbral. Y
  «tapado» es el modo que la lectura de `docs/investigacion_2026-11-16.md` §2.1 considera más parecido al ATD
  —**no está cerrado en el repo:** ver el apartado del corte de 75 frames—.
- **La pérdida con el flag no se distingue de cero** en las dos celdas de «tapado», lo cual es bueno para la
  condición 3; pero el extremo malo del intervalo (−0,0057 y −0,0060) se pasa de los 0,005 que esa condición
  permite.

**Por la letra de la regla, que se escribió con valores centrales y el recuento por partido como sustituto del
intervalo, las condiciones 1 y 3 pasan.** Esto no lo cambia: lo matiza, y refuerza el apartado del corte de 75
frames, que en esas dos celdas de «tapado» da +0,008 / +0,009 con el control y +0,000 / +0,001 con el flag.
Si el equipo quiere que la regla del 16/11 exija además que el intervalo no cruce el umbral, eso es una decisión
suya y esta candidata tendría que volver a leerse con ella.

### 2026-11-16 · decodificador · «cortas a `D`»: la entrega de prueba, reproducida en el entorno limpio de Ismael

Quién: la ejecutó Ismael; lo apunta la sesión planificadora (Claude), que revisó y mergeó la PR 20. Solo agregados.

Cómo se generó: `python validation/partido/probar_entrega.py prueba_cortas_a_d --pieza
temporal=temporal.decode_cortas_a_d --contra equipo_v8`, en el entorno limpio (Python 3.13.9, numpy 2.5.4), con `main`
en `c52a746` y sin cambios locales en el código de la entrega.

Resultado [medido]:
- **sha256 `d9706dfb4b5389d391146d5d7efd022f01aa2a427d3e61f7ab2c06b3ecccbe63`.** Es la huella entera, que faltaba.
  Coincide con lo que apuntó Manuel (`d9706dfb…be63`, generada con `1fcf40f`, Python 3.14.4 y numpy 2.4.4) y con todos
  sus recuentos: la entrega de prueba sale igual en dos máquinas, con dos Python y dos numpy.
- 0 frames con piezas en conflicto y ninguna racha de menos de 25 frames en los dos tramos.
- Frente a `equipo_v8` cambian 1.167 frames evaluados (el 0,735 %), todos de un equipo a `D` (609 de `H` y 558 de
  `A`), y ninguno a 250 frames o menos de un borde de tramo.
- Las posesiones pasan de 219 a 201 y las paradas siguen en 116. El `D` es el 46,18 % de lo evaluado.
- El balón fuera (D7) no se mueve: llegamos tarde en 12 de 47 rachas, como con `equipo_v8`. «Cortas a `D`» no arregla
  ese problema: son casos distintos.
- Validador oficial: `Valid`, 199.319 filas, 201 posesiones de 17,0 s de media.
- Ventana pública: spellF1 de 0,658 a 0,680 y macroF1 de 0,865 a 0,874. No elige nada: solo dice que no se rompe.

Estado: **sigue apagada.** `pipeline.PIECES` no cambia y la entrega es `equipo_v8`.

Para encenderla, si el equipo lo decide:
1. Antes, el ensayo de `equipo_v8` con `main` como está: tiene que dar `d78c514d…e2b2`.
2. `pipeline.PIECES["temporal"] = "decode_cortas_a_d"`. La entrega regenerada en el entorno limpio tiene que dar la
   huella de arriba.
3. Lo que quede escrito contra `equipo_v8` (la puerta 2.2 del balón del vídeo) reescribe sus límites contra la base
   nueva antes de generar nada.

### 2026-11-16 · infraestructura · ensayo de la entrega: `equipo_v8` sale igual con `main` en `c6a3dee`

Quién: lo ejecutó Ismael; lo apunta la sesión planificadora (Claude). Solo agregados.

Qué se probó: el ensayo del congelado del plan (el paso 1 de `validation/balon_video/ESTA_NOCHE.md`):
`python -m possession.pipeline --name ensayo_16nov` con el python del entorno limpio, y el validador oficial.

Resultado [medido]:
- `python 3.13.9, numpy 2.5.4`; `código: commit c6a3dee, sin cambios locales en el código de la entrega`; las piezas
  de la entrega, sin capas añadidas.
- ATD: 199.319 líneas leídas y válidas; 0 saltadas, 0 repetidas y 0 frames sin línea.
- `H` 54.445, `A` 32.213, `D` 72.199 y `X` 40.462. Tramo 1: 103 posesiones y 54 paradas; tramo 2: 116 y 62. Ninguna
  racha de menos de 12 ni de 25 frames, y 0 frames con piezas en conflicto.
- **sha256 `d78c514dcf5e8ad9bcff5f76da0aadf409c01ce89ad65ad0435421daf31ce2b2`, el de `equipo_v8`.**
- Validador: `OK` y `Valid`, 199.319 filas, 219 posesiones de 15,8 s de media.

Qué cierra:
- El entorno de `equipo_v8`, que estaba [sin verificar]: sale con el limpio.
- La PR 20 («cortas a `D`», apagada, `10aadef`) no cambia la entrega tampoco en el entorno limpio. Manuel lo había
  visto con Python 3.14.4 y numpy 2.4.4.
- `equipo_v8` sale igual en tres máquinas: el Windows de Ismael, el Mac M1 de Antonio y el Windows de Manuel.

Para cuando se decida encender «cortas a `D`» [leído en el código]: la fila por defecto del harness (`{}`) sale de
`pipeline.PIECES` (`validation/harness/puntuar.py`). Al cambiar `PIECES["temporal"]` cambia el «main» de referencia de
cualquier medida en marcha (B10, la puerta 2.1 del balón del vídeo, la capa de `D` de Ana). Cada una fija el commit de
antes del cambio o vuelve a medir su referencia.

### 2026-11-16 · decodificador · se enciende «cortas a `D`»: `pipeline.PIECES["temporal"]` pasa a `decode_cortas_a_d`

Quién: Ismael (16/11, por la noche): «si enciendela». Lo aplica la sesión planificadora (Claude), que lo había
recomendado.

Qué cambia:
- `pipeline.PIECES["temporal"]` pasa de `decode` a `decode_cortas_a_d`, con el corte de 125 frames. Nada más del
  código de la entrega.
- La entrega nueva es `equipo_v9`. Tiene que salir byte a byte igual que `prueba_cortas_a_d` (sha256
  `d9706dfb4b5389d391146d5d7efd022f01aa2a427d3e61f7ab2c06b3ecccbe63`), que Ismael generó en el entorno limpio con
  `main` en `c52a746` y Manuel en su máquina. **Regenerada por Ismael con `main` en `1e71d72`: sale esa huella,** con
  el validador en verde (201 posesiones de 17,0 s de media).

Por qué:
- Es la primera candidata que pasa entera la regla del límite de daño (16/11), escrita antes de medir: con control en
  la DFL, de +0,007 a +0,019 con 6 o 7 de 7; en SkillCorner, +0,010 y +0,009 en entrenamiento y +0,009 y +0,008 en el
  examen, 10 de 10; con el flag, la peor celda pierde 0,0024.
- La entrega de prueba pasa los cinco criterios de daño, y sale igual en dos máquinas (entrada anterior).
- El ensayo de `equipo_v8` ya estaba hecho con `main` en `c6a3dee`.

Riesgo que se acepta:
- Si la GT se parece al flag, cuesta hasta 0,002 [medido en la DFL].
- Quita 18 posesiones (219 → 201), y el punto débil conocido es que predecimos de menos.

Comprobado al encender [medido, datos abiertos y pruebas sin datos]:
- **Harness de la DFL** (`validation/harness/puntuar.py --bootstrap 0 --json`, los 7 partidos), antes (`main` en
  `3220707`) y después:
  - con el `D` de las etiquetas, la salida es idéntica byte a byte. La regla no convierte nada donde `D` está
    prohibido, así que la referencia «main» de las medidas con el `D` de las etiquetas no se mueve;
  - con el `D` propio cambia, como midió Manuel. Fila «Viterbi, coste 25 (v0)»: con el flag, 0,416 → 0,414 («como el
    ATD») y 0,433 → 0,431 («sin bloques»); con control, 0,616 → 0,623 y 0,642 → 0,651.
- **Pruebas sin datos de `validation/scripts/`:** en verde. `prueba_pipeline.py` y `prueba_harness.py` fijaban el
  decodificador por defecto y se ponen al día. `prueba_silbato.py` no pasa en esta máquina porque no encuentra un
  programa externo; no depende de este cambio [sin verificar que fallara antes].

Lo que arrastra:
- **Harness:** una versión que no nombra «funcion» en `temporal` usa ahora `decode_cortas_a_d`. Para repetir una medida
  anterior con el `D` propio hace falta `main` en `3220707`.
- **Medidas en marcha** (B10 y el detector de cambios de David, la puerta 2.1 del balón del vídeo, la capa de Ana): con
  el `D` propio, fijan `3220707` o vuelven a medir su referencia. Con el `D` de las etiquetas no cambia nada.
- **La puerta 2.2 del balón del vídeo** está escrita contra `equipo_v8`. Vale mientras su entrega de prueba se genere
  desde `exp/balon-video` sin traer `main`. Si se trae, se reescriben antes los límites contra `equipo_v9`.
- **`validation/balon_video/ESTA_NOCHE.md`** (en `exp/balon-video`) dice que `main` da `d78c514d…e2b2`. Desde este
  commit, `main` da la huella de `equipo_v9`. Para reproducir `equipo_v8` hace falta `main` en `3220707`.
- `validation/partido/probar_entrega.py` compara por defecto con `equipo_v9`.

Descartado:
- El corte de 75 frames: se elegiría después de ver los resultados, y no puede confirmarse en el examen sin abrirlo
  otra vez. El examen de SkillCorner queda cerrado para esta idea [recomendación de la revisión de la PR 20; el equipo
  no la ha discutido].
- Esperar a mañana: no quedaba ninguna comprobación pendiente.

### 2026-11-16 · balón · la línea del balón del vídeo se para: la puerta 1b da «NO SIGUE»

Quién: lo ejecutó Ismael en su Windows (CPU) y pegó solo agregados; lo apunta la sesión del balón del vídeo (Claude).
Se los pasó también a David, que los había pedido.

Qué se probó: la puerta 1b de `validation/balon_video/BITACORA.md` (rama `exp/balon-video`), con la variante fijada
antes de medir: un detector YOLO11n público en un recorte de 320 px alrededor del balón del ATD en t+4, ampliado ×2 y
con confianza 0,10, en 40 tramos de 15 s (7.010 frames con balón del ATD dentro del campo). El vídeo decodifica sus
199.319 frames.

Resultado [medido, agregados del partido]:
- **Condición 1, cumple:** el 78,94 % de esos frames tiene una detección a 3 m o menos del balón del ATD (umbral:
  70 %).
- **Condición 2, no cumple:** el 40,68 % de las detecciones está a más de 5 m del balón del ATD (umbral: 10 %). El
  detector da 2,64 detecciones por frame de media.
- **Condición 5, cumple:** la emulación en la DFL, leída en la celda p = 0,7, σ = 0,03 y L = 12, pasa «sin decidir».
- **Global: «NO SIGUE».**
- Descriptivo: 45,9 toques por minuto con el balón del detector y 2,1 con el del ATD; el desfase con el ATD que mejor
  cuadra es 0 frames, no los 4 esperados; unas 2,5 h de CPU para el partido entero.

Decisión: **la línea se para, con la regla tal como estaba escrita.** No se lanza la detección del partido entero ni
ninguna puerta 2.x, y la capa `balon_video.ajuste_b5_video` no entra. La entrega sigue siendo `equipo_v9`.

Después, por decisión de Ismael, la variante B (la misma 1b con confianza 0,25, el otro valor que midió la puerta 0;
regla escrita antes de medirla): también «NO SIGUE», con el 36,3 % de las detecciones a más de 5 m [medido]. No se
prueba ninguna otra confianza: sería elegir el umbral con el partido. Detalle en la bitácora de `exp/balon-video`.

Lo que queda: el código, las pruebas y la bitácora siguen en `exp/balon-video` para el documento técnico. No entran en
`main`: la capa no se va a encender, y un `regenerar.py` en la raíz del repo público, que genera otra entrega,
confundiría.

Lo que arrastra: B10 (David) y la capa de `D` con el golpeo del vídeo (Ana) necesitaban la detección del partido
entero. Sin ella no tienen balón del vídeo.

Descartado:
- **Cambiar la condición 2 después de ver el resultado.** Contaba todas las detecciones del recorte, y la regla de B5
  solo usa la más fiable a 5 m o menos del balón del ATD [inferencia: muchas de las lejanas no se usarían]. Pero se
  escribió antes de medir justo para parar un detector que ve muchas cosas que no son el balón, y no se toca.
- **Los «balones largos»** (la fase que se quedó sin subir en el ordenador del trabajo de Ismael): su techo es del
  orden de +0,01 [inferencia, con la cota de la DFL y el 4,6 % de huecos con juego del partido] y pediría una detección
  nueva y puertas nuevas.

### 2026-11-16 · temporal · detector de cambios de posesión: candidatos, rejilla y regla de entrada (antes de medir)

Quién: David (16/11), con Claude. Escrita antes de medir nada; el techo (punto 1) y el detector (punto 2) se miden
después de este commit.

Qué se prueba: una pieza nueva que no contesta «¿quién tiene el balón?», como B5, sino «¿acaba de cambiar la posesión
en este frame, y hacia qué equipo?». B5 no se toca. Por qué: B5 pesa señales lentas y, tras un cambio, sigue votando
al equipo anterior; en las posesiones que perdemos empuja al contrario con 6–11 veces el coste de cambio, así que
bajar `switch` no las arregla (`validation/resultados/2026-11-15_posesiones_cortas.md`, puntos 3 y 4).

Cómo entra en el pipeline (todo apagado por defecto: sin el detector, `main` da exactamente lo mismo):
- **`temporal.decode_cambios`:** el Viterbi de siempre, con el coste de pasar de un equipo al otro rebajado en cada
  frame: `max(0, switch − w·p_haciaX(t))` para entrar en X. Los pasos por `D` no cambian.
- **La capa de estados `cambios.capa`:** `score_X(t) = γ · max de p_haciaX(τ)` con τ en `[t − 12 − W, t − 12]`. Los 12
  frames son el semiancho de la clase (abajo): así, con un detector perfecto, el empujón empieza en el cambio y no 12
  frames antes. Sin ella, B5 sigue votando al equipo anterior y el Viterbi no corta.
- **`pipeline.run(..., cambios=None)`:** el argumento nuevo, opcional. Con `None`, el camino de siempre.

1. **El techo, antes de entrenar (descriptivo, no decide):** se pasa como detector perfecto `p = 1` a 12 frames o menos
   de cada cambio directo real de la DFL (los que cruzan un `D` no cuentan), hacia el equipo nuevo. Se da el spellF1
   con el flag (con los cambios del flag), con control (con los de control) y con el flag usando los cambios de control
   (lo que sacaría un detector perfecto entrenado con control si la GT fuera el flag), y la tabla por duración.

2. **El detector aprendido:**
   - **Etiquetas:** DFL, convención de control. «Hacia H» / «hacia A»: frames vivos a 12 o menos de un cambio directo
     (si dos cambios pisan el mismo frame, el más cercano). «Sin cambio»: el resto de los vivos. Los `D` no entran. No
     se quitan los frames dudosos.
   - **Rasgos** en t, con k ∈ {6, 13, 25}, todos en metros (también en el partido, con `x_m, y_m` del balón del vídeo):
     la distancia del jugador más cercano de cada equipo al balón en t−k, t y t+k y su diferencia; el cambio de esa
     diferencia entre t−k y t+k; la velocidad del balón antes y después, el ángulo de giro y la aceleración; los
     jugadores de cada equipo a 2 m o menos en t−k y t+k; la fracción de la ventana sin balón y la fracción con balón
     del vídeo. Nada de ventanas de más de 25 frames ni rasgos de forma.
   - **Simetría:** cada fila va dos veces, la segunda con los equipos intercambiados.
   - **Modelo:** `HistGradientBoostingClassifier` de scikit-learn (no LightGBM, que no está instalado; mismo tipo de
     modelo), 3 clases, con `learning_rate` 0,1, 200 iteraciones, 31 hojas, 100 muestras por hoja, L2 de 1, sin parada
     temprana, semilla 0 y un solo hilo. «Sin cambio» pesa menos: entra 1 de cada 5 de sus frames. No se prueban otros.
   - **Pliegues:** 7, uno por partido de la DFL (cada partido se puntúa con el modelo que no lo vio). No son 16: los 16
     de la apuesta B eran 8 pliegues × 2 convenciones.
   - **Dos variantes del balón que ve el detector** (B5 y el `D` siguen con el balón «como el ATD» en las dos):
     - **respaldo:** el balón «como el ATD» del harness;
     - **principal («como el vídeo»):** donde el balón «como el ATD» se ve, con probabilidad p es el balón limpio más
       un ruido gaussiano σ; si no, el balón «como el ATD»; los fallos van en rachas de longitud media L. Es la
       emulación de `validation/balon_video/BITACORA.md` (condición 5). **Celda provisional:** p = 0,8, σ = 0,06 m,
       L = 12, hasta que la puerta 1b mida el detector del partido; entonces se repite en la celda medida, con la
       regla de lectura de esa bitácora.
   - **Paso 0, la versión con reglas** (línea base, sin voto propio): toque = el balón gira más de 30° o cambia su
     velocidad más de un 40 % entre los 6 frames anteriores y los 6 posteriores, con un jugador a menos de 2 m; cambio
     hacia X si el toque anterior era del otro equipo y el siguiente toque es de X o X sigue siendo el más cercano 20
     frames. Sin ajustar umbrales.

3. **La rejilla del decodificador,** fija: w ∈ {0, 12,5, 25}, γ ∈ {0, 2, 4} y W ∈ {25, 50} (14 combinaciones con
   algún efecto). **El candidato de cada variante es uno solo:** para cada partido, la combinación que más saca en los
   otros seis (media del spellF1 de control en las dos condiciones que votan, con las probabilidades fuera de muestra),
   puntuada en ese. Las 14 se imprimen como descripción. No está anidado del todo, como la fila «elegida dejando un
   partido fuera» del harness.

Regla de entrada: la del «límite de daño» del 16/11, tal cual, para cada variante frente a `main`:
1. DFL con control: +0,005 o más en las dos condiciones que votan, ganando en 6 de 7 partidos en cada una, con el `D`
   de las etiquetas **y** con el `D` propio (la capa empuja a un equipo también frente a `D`, así que toca el `D`).
2. SkillCorner: gana en la mitad de entrenamiento y lo confirma una sola vez en el examen (+0,005 o más, 7 de 10).
   Solo se abre si pasa el punto 1.
3. DFL con el flag: no pierde más de 0,005 en ninguna celda.
4. Entrega de prueba frente a la vigente, con criterios de daño escritos antes de generarla. Para la variante principal
   hace falta la detección del partido entero.

La predicción de los árboles en numpy (para que la entrega siga usando solo numpy) se escribe solo si pasa 1 y 3.

Avisado antes de medir:
- **Circularidad:** las etiquetas de control salen de una regla de proximidad con el tracking limpio, y los rasgos son
  de proximidad. El número con control saldrá inflado; por eso deciden también el flag (límite de daño) y SkillCorner.
- **El «hueco del vídeo junto a un jugador»** no se puede aprender en la DFL: en la emulación los fallos son al azar,
  no balones tapados. Entra solo como «fracción de la ventana con balón del vídeo».
- **El detector del vídeo solo busca alrededor del balón del ATD:** donde el ATD no ve el balón, el detector de
  cambios tampoco tiene balón.
- El respaldo ve el balón suavizado 1 s: el experimento 2 y B8 dicen que ahí casi no hay toques que ver.

**Añadido el 16/11, después de ver el techo en un partido y antes de entrenar o medir ningún detector:** la rejilla
gana γ = 8 (20 combinaciones con algún efecto). Por qué: con el detector perfecto, en un partido (J03WMX), el spellF1
seguía subiendo en γ = 4, el borde de la rejilla. El techo es descriptivo y elige mirando el resultado; el candidato
sigue siendo uno, elegido dejando un partido fuera.

Estado: medido el 16/11 (entrada siguiente). `pipeline.PIECES` y la entrega no cambian.

### 2026-11-16 · temporal · detector de cambios de posesión: el techo es alto, pero ningún candidato pasa la regla

Quién: David (16/11), con Claude. Salidas: `validation/cambios/salidas/2026-11-16_techo.md` y `2026-11-16_medir.md`.

Cómo se midió: los 7 partidos de la DFL, balón «como el ATD» y «sin bloques», `D` de las etiquetas y propio, con
`validation/cambios/techo.py` y `medir.py` (código en `1c69918`). `main` repite el harness (0,498 / 0,728 y 0,416 /
0,616). La emulación del vídeo va en la celda provisional (p = 0,8, σ = 0,06 m, L = 12).

Resultado [medido]:
- **El techo (detector perfecto, descriptivo, mejor combinación mirando el resultado):** con el `D` de las etiquetas y
  «como el ATD», de 0,728 a 0,824 con control (+0,096), de 0,498 a 0,716 con el flag (+0,218) y, con los cambios de
  control puntuados con el flag, a 0,584 (+0,085); 7 de 7 en todo. Con el `D` propio, +0,091 con control. La rebaja del
  coste sola da +0,007; la capa sola, +0,084. La mejor combinación es el borde de la rejilla (γ = 8, W = 50).
- **El detector por sí solo** (umbral 0,5): el aprendido ve el 55–63 % de los cambios de control con el balón de
  respaldo y el 62–71 % con el del vídeo, pero da de 10 a 16 avisos por minuto vivo y solo el 23–25 % es bueno. Las
  reglas con el balón del vídeo ven lo mismo (61–71 %) con 4,6–5,2 avisos por minuto y el 36–37 % bueno; con el de
  respaldo, el 31–35 %.
- **Los cuatro candidatos, con la regla** (diferencia con `main`; control / flag, «como el ATD»):

  | candidato | `D` de las etiquetas | `D` propio | punto 1 | punto 3 |
  |---|---|---|---|---|
  | aprendido, respaldo | −0,007 / +0,004 | −0,014 / −0,002 | no pasa | pasa |
  | aprendido, vídeo | +0,003 / +0,017 | −0,011 / +0,004 | no pasa | pasa |
  | reglas, respaldo | −0,000 / +0,006 | −0,001 / +0,005 | no pasa | pasa |
  | reglas, vídeo | +0,003 / +0,024 | +0,006 / +0,023 | no pasa | pasa |

  El que más se acerca es el de reglas con el balón del vídeo: gana con el flag en 6 o 7 partidos de 7 (+0,023 a
  +0,027) y con control queda en +0,003 a +0,007 en 5 de 7 (se pedían 6).

Decisión y por qué: **ninguno entra.** No se abre SkillCorner ni se escribe la predicción en numpy. El código queda
apagado (`decode_cambios`, `cambios.capa`, `pipeline.run(cambios=None)`).

Lectura [inferencia]: el mecanismo vale (el techo) y lo que falla es la precisión del detector: tres de cada cuatro
avisos del aprendido son falsos, y cada uno empuja una posesión que no existe. Con el `D` propio el aprendido pierde
más, porque la capa empuja a un equipo también frente a `D`. El balón del vídeo sí trae información: dobla los cambios
que ven las reglas.

Descartado: elegir una combinación de la tabla descriptiva (varias ganan en alguna celda): sería elegir mirando.

### 2026-11-16 · temporal · detector de cambios, segunda ronda: cuatro familias contra la falta de precisión (antes de medir)

Quién: David (16/11, «haz la segunda ronda»), con Claude. Escrita antes de medir nada de esta ronda.

Qué se prueba: la primera ronda dijo que el mecanismo vale (techo de +0,096 con control) y que falla la precisión del
detector (10–16 avisos por minuto, el 23–25 % buenos) y el efecto de la capa sobre el `D` propio. Cuatro familias, todas
sobre las probabilidades y los modelos de la primera ronda (no se reentrena la primera etapa):

- **C, la capa contra el otro equipo:** `cambios.capa(..., contra_d=True)` suma lo mismo a la columna `D`, así que solo
  empuja contra el otro equipo. Se aplica a los cuatro detectores de la primera ronda, sin tocarlos.
- **A, avisos:** la probabilidad del aprendido se corrige por el submuestreo de «sin cambio» (1 de cada 5) y se queda en
  avisos: el máximo de cada racha con p ≥ u, separados 25 frames o más (gana el más alto). La capa y la rebaja reciben
  1 a 12 frames o menos de cada aviso. u ∈ {0,5, 0,7, 0,85}.
- **B, confirmación:** un segundo modelo mira cada aviso de la primera etapa (los de A con u = 0,3) y dice si es un
  cambio real. Rasgos, solo aquí con más de 25 frames: en los 50 y 75 frames siguientes, la fracción de frames con
  balón en que el equipo nuevo es el más cercano, la mediana de la distancia de cada equipo y la fracción sin balón; en
  los 50 anteriores, la fracción en que el más cercano era el otro equipo; los toques de cada equipo (`cambios.toques`)
  en los 75 siguientes y en los 50 anteriores; y la p del aviso. Mismo `HistGradientBoostingClassifier` (con 20 muestras
  por hoja, porque hay pocos avisos), un modelo por partido dejado fuera. Quedan los avisos con p₂ ≥ v, v ∈ {0,3, 0,5,
  0,7}. No está anidado del todo: los avisos de los partidos de entrenamiento salen de modelos de la primera etapa que
  sí vieron el partido que se puntúa.
- **D, las reglas afinadas:** `GIRO_TOQUE` ∈ {20, 30, 45}, `CAMBIO_VELOCIDAD` ∈ {0,3, 0,4, 0,6} y `CONFIRMA` ∈ {12, 20,
  30} (27 juegos; el de hoy es 30 / 0,4 / 20).

La rejilla del decodificador de esta ronda: w ∈ {0, 25}, γ ∈ {4, 8, 16}, W ∈ {50, 100} y la capa de las dos formas
(`contra_d` sí o no): 24 combinaciones. Para D, solo cuatro (w = 0, W = 50, γ ∈ {4, 8}, las dos formas), por tiempo.

Un candidato por familia y balón (10 en total: C × 4 detectores, A × 2 balones, B × 2 y D × 2). Cada uno elige todo lo
suyo (u, v o el juego de umbrales, y la combinación del decodificador) dejando un partido fuera: lo que más saca en los
otros seis, con la media del spellF1 de control en las dos condiciones que votan **y los dos modos del `D`** (con el `D`
de las etiquetas, `contra_d` no cambia nada, así que no se podría elegir).

Regla de entrada: la misma de la primera ronda (el límite de daño; puntos 1 y 3 aquí). Son 10 candidatos y ya hubo 4:
si pasa uno solo y por poco, se dice. La emulación del vídeo sigue en la celda provisional.

Estado: medida el 16/11 (entrada siguiente).

### 2026-11-16 · temporal · detector de cambios, segunda ronda: las reglas afinadas con el balón del vídeo pasan los puntos 1 y 3

Quién: David (16/11), con Claude. Salida: `validation/cambios/salidas/2026-11-16_ronda2.md` (`ronda2.py`, código en
`d6cc926`; los 7 partidos de la DFL; emulación del vídeo en la celda provisional p = 0,8, σ = 0,06 m, L = 12).

Resultado [medido], diferencia con `main` del candidato de cada familia (control / flag; el rango de las cuatro celdas:
dos condiciones que votan × `D` de las etiquetas y propio):

| familia | balón de respaldo | balón «como el vídeo» |
|---|---|---|
| C, primera ronda con la capa contra el otro equipo: aprendido | +0,003 a +0,006 / +0,012 a +0,016 | +0,009 a +0,013 / +0,019 a +0,020 |
| C: reglas sin afinar | +0,004 a +0,014 / +0,007 a +0,015 | +0,010 a +0,015 / +0,038 a +0,043 |
| A, avisos | −0,005 / +0,004 a +0,005 | −0,010 a −0,003 / +0,008 a +0,014 |
| B, confirmación | +0,003 a +0,006 / +0,006 a +0,008 | +0,008 a +0,011 / +0,017 a +0,025 |
| **D, reglas afinadas** | +0,006 a +0,009 / +0,010 a +0,013 | **+0,014 a +0,020 / +0,049 a +0,054** |

- **D con el balón del vídeo pasa el punto 1** (control: +0,014, +0,020, +0,019 y +0,020, ganando en 6, 6, 6 y 7 de 7;
  los cuatro intervalos por encima de cero) **y el punto 3** (con el flag gana en 7 de 7 en las cuatro celdas). Lo
  elegido es estable: en 6 de los 7 pliegues, giro de 45°, cambio de velocidad del 60 %, 30 frames de confirmación,
  w = 0, γ = 8, W = 50 y la capa contra el otro equipo; en el séptimo, lo mismo sin «contra el otro».
- **Los otros nueve no pasan el punto 1.** Ninguno falla el punto 3: nada pierde con el flag.
- **La capa contra el otro equipo arregla el daño al `D` propio:** el aprendido con el balón del vídeo pasa de −0,011 /
  −0,014 (primera ronda) a +0,011 / +0,013. Se elige en casi todos los pliegues.
- **Los avisos (A) empeoran y la confirmación (B) mejora poco:** con la probabilidad corregida quedan muy pocos avisos.
- Con el balón de respaldo nada pasa: sin el balón del vídeo no hay candidato.

Decisión y por qué: **el candidato «reglas afinadas con el balón del vídeo» sigue al punto 2 (SkillCorner).** No entra
todavía en nada: `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian.

Lo que hay que decir con el número:
- **Es 1 de 14 candidatos** en dos rondas. Pasa con margen sobre el umbral (+0,014 frente a +0,005) y con la misma
  elección en 6 de 7 pliegues, pero no es una prueba limpia: SkillCorner y la entrega de prueba siguen siendo obligatorios.
- **Depende del balón del vídeo, que aquí es una emulación en una celda provisional.** Hay que repetirlo con la
  cobertura, el temblor y las rachas que mida la puerta 1b. SkillCorner no tiene balón limpio que emular: allí solo se
  puede medir con su propio balón.
- **Ni la capa ni las reglas usan un modelo:** si entra, no hace falta scikit-learn ni exportar árboles.
- Sigue muy lejos del techo (+0,096): el detector ve una parte de los cambios.

Descartado: A (avisos) y B (confirmación) con estos umbrales; el detector aprendido como candidato.

**Añadido el 16/11, tras traer `main` (`032d4d8`):** la segunda ronda se midió con `temporal.decode`, y desde `1e71d72`
la entrega decodifica con `decode_cortas_a_d` (`equipo_v9`). El candidato se repitió con el decodificador de la entrega
(`validation/cambios/confirmar.py`, salida en `salidas/2026-11-16_confirmar.md`), sin elegir nada: reglas 45° / 60 % /
30 frames, γ = 8, W = 50, contra el otro equipo. **Sigue pasando los puntos 1 y 3** [medido]: con control, +0,014 y
+0,020 con el `D` de las etiquetas (6 de 7) y +0,021 y +0,019 con el propio (7 y 6 de 7); con el flag, de +0,044 a
+0,054 (7 de 7). Predice más posesiones: de 1.661 a 1.859 con el `D` de las etiquetas (1.736 reales con control) y de
1.538 a 1.647 con el propio. Como w = 0, el candidato es solo una capa de estados: no necesita `decode_cambios` ni
tocar `pipeline.run`, y se suma con `--capa` como las demás. Un partido se puntúa con una combinación que su pliegue no
eligió (eligió la misma sin «contra el otro»).

### 2026-11-16 · temporal · detector de cambios: el candidato en las celdas que midió la puerta 1b (antes de medir)

Quién: David (16/11), con Claude. Escrita antes de ejecutar nada con estas celdas.

Por qué: la puerta 1b ya midió el detector del vídeo en el partido (entrada «la línea del balón del vídeo se para»), y
el candidato de la segunda ronda se midió con una celda provisional (p = 0,8, σ = 0,06 m, L = 12) que **no tiene
detecciones equivocadas**. La 1b dice que las hay: la detección elegida está a más de 3 m del balón del ATD en el
18,76 % de los frames en que hay alguna (el 91,0 %). Para unas reglas que buscan giros y cambios de velocidad, un salto
a un falso positivo es un toque falso.

Qué se mide: el mismo candidato, sin elegir nada (reglas 45° / 60 % / 30 frames, γ = 8, W = 50, contra el otro equipo,
con `decode_cortas_a_d`), en dos celdas:
- **M1, la celda de la bitácora del vídeo:** p = 0,7, σ = 0,03 m, L = 12, sin detecciones equivocadas.
- **M2, con las equivocadas (la que decide):** de los frames con balón «como el ATD», el 74 % lleva el balón limpio con
  σ = 0,03 m (0,91 × 0,8124), el 17 % una detección equivocada (0,91 × 0,1876) y el 9 % el balón «como el ATD». Los
  frames que no son buenos van en rachas de longitud media 6 (la racha de fallos medida, 6,18); cada racha es
  «equivocada» con probabilidad 17/26 y, si no, «sin detección». En una racha equivocada el balón es el del ATD más un
  desplazamiento fijo de 3 a 5 m (uniforme) en una dirección al azar, más el mismo ruido σ. Es el caso malo: supone que
  todas las detecciones a más de 3 m son falsos positivos, cuando parte será error del balón del ATD, que va suavizado.

Regla: los puntos 1 y 3 del límite de daño, como siempre. **Si M2 no pasa, el candidato se cierra** con el detector tal
como está (confianza 0,10). Si pasa M2, sigue dependiendo de que haya balón del vídeo del partido entero, y eso lo
decide el equipo: la línea del vídeo está parada.

No se cambia nada del candidato mirando esto. Limitación: M2 no modela el desfase (la 1b ve 0 frames, no 4).

### 2026-11-16 · temporal · detector de cambios: con las cifras de la puerta 1b el candidato no pasa; se cierra

Quién: David (16/11), con Claude. Salidas: `validation/cambios/salidas/2026-11-16_confirmar_M1.md` y `_M2.md`
(`confirmar.py --celda`, código en `3b7b76a` más el script; los 7 partidos de la DFL, con `decode_cortas_a_d`).

Resultado [medido], diferencia con `main` (el rango de las cuatro celdas):

| celda de la emulación | control | flag | punto 1 | punto 3 |
|---|---|---|---|---|
| provisional (p = 0,8, σ = 0,06, sin equivocadas) | +0,014 a +0,021 (6–7 de 7) | +0,044 a +0,054 | pasa | pasa |
| M1 (p = 0,7, σ = 0,03, sin equivocadas) | +0,010 a +0,017 (5, 6, 6 y 6 de 7) | +0,039 a +0,051 | no pasa, por un partido | pasa |
| **M2 (74 % buena, 17 % equivocada, 9 % sin detección)** | **−0,022 a −0,042 (0–1 de 7)** | +0,034 a +0,054 | **no pasa** | pasa |

- Con las detecciones equivocadas, el candidato predice de más: de 1.661 a 1.971–2.083 posesiones con el `D` de las
  etiquetas, cuando con control hay 1.736. Cada salto a un falso positivo es un toque falso.
- Con el flag sigue ganando en 7 de 7 en las tres celdas: el flag tiene 3.061 posesiones y aguanta las inventadas. Lo
  que gana depende, pues, de la convención.

Decisión y por qué: **el candidato se cierra,** con la regla escrita antes de medir (M2 decidía). Además, la línea del
balón del vídeo está parada en la puerta 1b y no hay detección del partido entero. No se abre SkillCorner. El código
queda apagado: `cambios.capa`, `cambios.p_reglas`, `temporal.decode_cambios` y `pipeline.run(cambios=None)`.
`pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega (`equipo_v9`) no cambian.

Lo que queda para el documento técnico y para la fase siguiente:
- **El mecanismo vale:** un detector de cambios perfecto da +0,096 con control y +0,218 con el flag sobre B5.
- **El balón del vídeo trae la información que falta** (las reglas ven el doble de cambios que con el balón del ATD),
  **pero solo si sus detecciones equivocadas se filtran.** M2 es el caso malo: supone que toda detección a más de 3 m
  del balón del ATD es falsa. Lo que habría que probar, si se retoma: un filtro de trayectoria (continuidad entre
  frames) o una confianza mínima más alta antes de buscar toques.
- Sin balón del vídeo no hay candidato: con el del ATD nada pasó en ninguna de las dos rondas.

Descartado: reajustar los umbrales de las reglas para M2 (sería elegir después de ver el resultado, y la regla decía
que no se cambiaba nada).

### 2026-11-16 · temporal · detector de cambios en SkillCorner: el instrumento y la regla de lectura (antes de medir)

**Nota al juntar las ramas (16/11):** esta regla y su medida se hicieron en `exp/cambios-skillcorner`, que salió de
`feat/detector-cambios` en `032d4d8`, sin saber que en `869ad78` (entrada anterior) el candidato ya se había cerrado
con las cifras de la puerta 1b. Se midió la celda provisional, sin detecciones equivocadas. El texto de la regla se
deja como se escribió antes de medir; el caso «Si pasa» ya no aplica.

Quién: lo pidió Ana (16/11); la escribe Claude antes de puntuar ningún detector en SkillCorner. Rama
`exp/cambios-skillcorner`, que sale de `feat/detector-cambios` en `032d4d8`.

Qué se prueba: el punto 2 de la regla del detector (entrada «candidatos, rejilla y regla de entrada» de hoy), en la
mitad de entrenamiento de SkillCorner. Solo para el candidato que pasó los puntos 1 y 3 en la DFL (entrada «segunda
ronda» de hoy): **las reglas afinadas con el balón del vídeo**, con lo elegido en 6 de los 7 pliegues: giro de 45°,
cambio de velocidad de 0,6, 30 frames de confirmación, w = 0, γ = 8, W = 50 y la capa contra el otro equipo. Nada de
esto se elige en SkillCorner.

Cómo se medirá: con `validation/cambios/medir_skillcorner.py` (`50b7135`), una sola ejecución:

    python validation/cambios/medir_skillcorner.py --detector reglas --giro 45 --velocidad 0.6 --confirma 30 \
        --w 0 --gamma 8 --ventana 50 --contra-d --balon sin-suavizar

- **Partidos:** los 10 de `lector.ENTRENAMIENTO`. `lector.EXAMEN` solo se lee con `--examen` y
  `--examen-con-permiso`; con `--examen` solo, da error.
- **Condiciones:** las dos que votan en SkillCorner, «detectado» y «detectado, suavizado», pasadas de 10 a 25 fps con
  `lector.tracking_de`, como `validation/skillcorner/medir.py`.
- **`main`:** B5 con los coeficientes de la entrega, `dead_state` y `temporal.decode` con coste 25. Es la de
  `validation/resultados/2026-11-15_skillcorner.md` y la de las rondas de la DFL. No lleva «cortas a `D`», que está en
  la entrega desde hoy:
  - con el `D` de las etiquetas no cambia nada, porque solo convierte rachas en las que `D` está permitido [por
    inspección del código];
  - con el `D` propio, el detector junto con «cortas a `D`» no se mide aquí.
- **El candidato:** la misma evidencia más `cambios.capa`, decodificada con `temporal.decode_cambios` y
  `cambios.rebaja` (`ronda2.decodificar`).
- **El balón que ve el detector** (`--balon sin-suavizar`): el detectado de SkillCorner sin la media móvil de 25
  frames, en las dos condiciones. B5 y el `D` siguen con el de la condición.
  - Es la disposición de la DFL: allí el detector ve el balón «del vídeo», sin el suavizado de 1 s, y B5 y el `D`,
    el balón «como el ATD».
  - En «detectado, suavizado» la disposición es la misma. En «detectado», los dos ven el mismo balón.
  - No emula el detector del vídeo: SkillCorner no tiene un balón limpio que emular (entrada «segunda ronda»).
- **Los dos modos del `D`:** el de las etiquetas (`puntuar.d_oraculo`) y el propio.
- **Métrica:** `spellF1` con los 10 partidos juntos, en cuántos de los 10 gana y el bootstrap pareado (5–95 %, 1.000
  remuestreos).

Resultado de la comprobación del instrumento, hecha antes de escribir esta regla [medido]. Sin detector
(`--detector ninguno`: `p` a cero, con w = 25, γ = 8, W = 50 y la capa contra el otro equipo, para que pase por todo
el camino del candidato; salida en `validation/cambios/salidas/2026-11-16_skillcorner_instrumento.md`):
- el candidato sale igual que `main` en todos los frames en las 40 salidas (10 partidos × 2 condiciones × 2 modos del
  `D`);
- `main` saca 0,519 y 0,514 con el `D` de las etiquetas y 0,382 y 0,378 con el propio («detectado» y «detectado,
  suavizado»), con 2.270, 2.284, 2.342 y 2.345 posesiones predichas frente a 3.228 reales;
- **repite la medida del 15/11 en estos 10 partidos:**
  - `2026-11-15_skillcorner.md` solo da los 20 juntos (0,514 y 0,509 con el `D` de las etiquetas), así que se
    ejecutó el código de esa medida (`3b227c4`, `validation/skillcorner/medir.py --partidos` con estos 10; salida en
    `validation/cambios/salidas/2026-11-16_skillcorner_referencia_1511.md`);
  - da lo mismo en las cuatro celdas: el mismo `spellF1`, el mismo mínimo y máximo por partido y las mismas
    posesiones predichas;
  - `validation/resultados/2026-11-15_diagnostico_errores.md` ya daba 0,519, con 2.270 posesiones de 3.228, en
    «detectado» con el `D` de las etiquetas.

Decisión y por qué (la regla de lectura, escrita antes de puntuar ningún detector en SkillCorner):
- **Pasa la mitad de entrenamiento** si, frente a `main`, saca **+0,005 o más con los 10 partidos juntos y gana en 7
  de 10**, en las **cuatro celdas**: «detectado» y «detectado, suavizado», con el `D` de las etiquetas y con el propio.
  - El umbral es el del punto 2 (el límite de daño del 16/11, no el +0,03 de §5.8).
  - Se piden los dos modos del `D`, como en el punto 1, porque la capa toca el `D`.
- El intervalo del bootstrap se enseña, pero no decide.
- **Descriptivo, sin voto:**
  - lo que ve el detector frente a las etiquetas de SkillCorner: cambios vistos, avisos por minuto vivo y avisos
    buenos;
  - las posesiones predichas.
- **Una sola ejecución,** con lo de arriba. Después de ver los números no se cambia nada: ni el candidato, ni el balón,
  ni las condiciones, ni `main`, ni la regla. En SkillCorner no se prueban otros umbrales ni otras combinaciones.
- **Si no pasa:** el candidato no sigue y el detector se queda apagado. El examen no se abre.
- **Si pasa:** no entra nada, porque **la línea del balón del vídeo se paró hoy** (la puerta 1b da «NO SIGUE»; entrada
  de `main` del 16/11). En el partido no habrá balón del vídeo, así que este candidato no se puede entregar tal cual.
  - El examen se abre una vez por candidato, con `--examen --examen-con-permiso` y la autorización del equipo en el
    momento.
  - Solo tiene sentido abrirlo si el equipo recupera un balón del vídeo. Hasta entonces, no se abre.

Descartado (antes de medir):
- **Medir aquí las reglas afinadas con el balón de respaldo:** no pasaron el punto 1 en la DFL, y la regla del 16/11
  solo abre SkillCorner si pasa. Tampoco se mide ninguno de los otros 13 candidatos de las dos rondas.
- **Medir el candidato junto con «cortas a `D`»:** sería otra comparación, con su propia regla.
- **Elegir en SkillCorner** el balón, los umbrales o la combinación.

El script mide otros detectores elegidos en la DFL (el aprendido o las reglas, con sus umbrales y su combinación) por
argumentos. Cada uso nuevo lleva antes su propia regla en este fichero.

Estado: escrita antes de medir. El resultado va en la entrada siguiente.

### 2026-11-16 · temporal · detector de cambios en SkillCorner: las reglas afinadas no pasan la mitad de entrenamiento

**Nota al juntar las ramas (16/11):** este resultado no decide nada nuevo. El candidato ya estaba cerrado por la
puerta 1b (`869ad78`); SkillCorner lo confirma por otro lado: tampoco pasa en un tracking automático de otro proveedor.

Quién: lo pidió Ana (16/11); lo ejecutó Claude (son datos abiertos), una sola vez, con la regla de la entrada anterior
ya commiteada (`c111042`).

Qué se probó: las reglas afinadas con el balón del vídeo (giro de 45°, cambio de velocidad de 0,6, 30 frames de
confirmación; w = 0, γ = 8, W = 50, contra el otro equipo), con el balón detectado de SkillCorner sin suavizar.

Cómo se midió: `validation/cambios/medir_skillcorner.py` en `c111042`, los 10 partidos de `lector.ENTRENAMIENTO`
(3.228 posesiones), `spellF1` con bootstrap de 1.000. Salida en
`validation/cambios/salidas/2026-11-16_skillcorner_reglas_afinadas.md`. El examen no se abrió.

Resultado [medido], candidato frente a `main`:

| `D` | condición | `main` | candidato | diferencia [5–95 %] | gana en |
|---|---|---|---|---|---|
| de las etiquetas | detectado | 0,519 | 0,514 | −0,005 [−0,011 a −0,000] | 4 de 10 |
| de las etiquetas | detectado, suavizado | 0,514 | 0,511 | −0,003 [−0,008 a +0,003] | 5 de 10 |
| propio | detectado | 0,382 | 0,381 | −0,000 [−0,005 a +0,004] | 6 de 10 |
| propio | detectado, suavizado | 0,378 | 0,381 | +0,003 [−0,002 a +0,008] | 6 de 10 |

- **Ninguna de las cuatro celdas cumple** (+0,005 y 7 de 10). Es un empate, o una pérdida pequeña con el `D` de las
  etiquetas.
- Descriptivo: el candidato predice unas 150–240 posesiones más que `main` (2.507 frente a 2.270 en «detectado» con el
  `D` de las etiquetas), pero el detector solo ve el 21 % de los 2.210 cambios directos de las etiquetas, con 3,8 avisos
  por minuto vivo y el 22 % de avisos buenos. En la DFL, con el balón «del vídeo», las reglas veían el 61–71 % con un
  36–37 % de avisos buenos (primera ronda, sin afinar).

Decisión y por qué: **con la regla escrita antes, el candidato no sigue.** El detector de cambios se queda apagado y el
examen de SkillCorner no se abre para él. `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian.

Lectura [inferencia]: lo que la DFL ganaba con el balón «del vídeo» no se traslada a un tracking automático de otro
proveedor. Con el balón de SkillCorner (10 fps, interpolado) las reglas ven pocos cambios, y la mayoría de sus avisos son
falsos, así que añaden posesiones que no existen. Va en la línea de la primera ronda: falla la precisión del detector,
no el mecanismo.

Descartado: probar otros umbrales o combinaciones en SkillCorner (sería elegir mirando).

### 2026-11-17 · candidatos · modelo conjunto: los jugadores uno a uno, control y SkillCorner en el entrenamiento (candidatos y regla, antes de medir)

Quién: lo pidió Ismael el 17/11 con un análisis de fuera sobre dónde cojeamos («Empieza a desarrollar un plan para
resolverlo y ejecútalo»). Lo escribe Claude en la rama `exp/modelo-conjunto`, que sale de `main` en `ed49929`, antes
de exportar, entrenar o medir nada.

**Qué dice el análisis y qué se hace con cada punto:**

| punto del análisis | qué se hace aquí |
|---|---|
| 1. Preguntar «¿dónde cambia?» y aprender el ritmo de los datos | una salida del modelo que dice «aquí cambia, y hacia quién» (candidato K1) |
| 2. Un solo modelo que mire a los 22 jugadores en el tiempo | el modelo de abajo (candidato K2). **Sin el `D`** (ver «Lo que se deja fuera») |
| 3. Decodificar para la métrica (riesgo mínimo) | solo si un candidato pasa los puntos 1 y 3 de la regla: S2 (16/11) midió que con la evidencia de B5 no sirve |
| 4. El balón del vídeo con movimiento | no se hace aquí: necesita el vídeo del partido, su línea se paró con su propia regla (16/11) y hay una rama a medias (`claude/balon-video-v2`) |
| 5. Preguntar a la organización qué regla usa | el repo oficial tiene los issues cerrados [medido: `gh issue list` responde «has disabled issues»], aunque el FAQ dice «Open an issue». Queda un borrador de correo en `validation/conjunto/pregunta_organizacion.md`; lo manda una persona |
| 6. Probar en paquete y con más partidos | los candidatos se miden enteros (modelo y decodificador de `main`) y SkillCorner entra también en el entrenamiento, con cada partido puntuado por un modelo que no lo vio |

**Por qué no repite lo cerrado ni lo que está en marcha:**
- El detector de cambios de David (16/11) miraba el balón y el jugador más cercano de cada equipo en ±25 frames, con
  árboles, solo en la DFL. Su techo es alto (+0,096 con control) y falló por precisión: de 10 a 16 avisos por minuto,
  el 23–25 % buenos.
- B11 y B12 (otra sesión, rama `claude/serene-lumiere-16245d`, en marcha) son redes de secuencia sobre 12 canales ya
  agregados por frame, entrenadas solo en la DFL y solo donde el flag y control coinciden. La primera medida de B11
  [medido por esa sesión, todavía sin subir]: +0,104 y +0,108 con el flag, +0,012 y +0,007 con control (4 de 7) y
  −0,012 y −0,009 en SkillCorner con el `D` de las etiquetas. Es el patrón de siempre: más posesiones, gana con el
  flag, empata con control y no se traslada a otro proveedor.
- Lo que nadie ha probado, y es lo que se prueba aquí: (a) que el modelo reciba a cada jugador, no agregados; (b)
  entrenar con las etiquetas de control en todos los frames vivos, para que aprenda a no cambiar con un toque sin
  control; (c) entrenar también con SkillCorner, para que aguante otro proveedor; (d) una salida de cambios entrenada
  junto a la de equipo.

**El modelo** (fijado antes de entrenar; lo que puede tocar el piloto está más abajo):
- **Entrada por jugador y frame** (14 números, todos con sumas, productos, divisiones, raíces y máximos: nada de
  exponenciales, para que la predicción en numpy salga bit a bit igual en cualquier máquina). Cada jugador se mira en
  el sistema de su equipo (el eje x apunta a la portería que ataca), así que cambiar los equipos de nombre no cambia
  sus números:
  - posición respecto al balón (2), tres núcleos racionales de la distancia al balón (1, 2,5 y 6 m, los radios de
    B1) y la distancia con tope de 15 m;
  - su velocidad (2) y su velocidad respecto a la del balón (2), por diferencia de ±2 frames; por encima de 12 m/s es
    un cambio de slot y va a cero;
  - cuánto se acerca al balón; su posición en el campo (2); y qué parte del grupo de 5 frames está presente.
- **Entrada por frame:** balón visible, su velocidad, su distancia a la banda (pares) y su posición y velocidad en la
  dirección de ataque del local (4, impares).
- **A 5 Hz:** las entradas se promedian en grupos de 5 frames por tramo evaluado. El balón del ATD va suavizado 1 s y
  SkillCorner viene de 10 fps: a 25 Hz no hay más información. Las salidas vuelven a 25 Hz por interpolación lineal
  entre los centros de los grupos, como B12.
- **Red, solo con ReLU:** una red pequeña por jugador (14 → 32 → 32), compartida; por equipo, la suma (dividida por
  11) y el máximo de sus jugadores, más cuántos hay; después, una convolucional temporal de 40 canales con 6 bloques
  residuales (núcleo 3, dilaciones 1 a 32: ve ±12,6 s). Unos 36.000 pesos.
- **Antisimetría exacta,** como B11: cada salida impar es ½·(g(x) − g(x con los equipos cambiados)), y cada salida
  par, ½·(g(x) + g(x cambiado)).
- **Salidas:** z, el logit de `H` frente a `A`; dos logits de cambio, «hacia `H`» y «hacia `A`» (la clase de
  `validation/cambios/comun.clases`: frames vivos a 12 o menos de un cambio directo); y un logit auxiliar del flag,
  solo para entrenar.
- **Etiquetas y pérdida:** entropía cruzada por grupo, en los frames vivos. z y los cambios, con control en la DFL y
  con las etiquetas de SkillCorner; el auxiliar, con el flag de la DFL y peso 0,3. Los `D` entran como contexto y no
  en la pérdida.
- **Datos:** los 7 partidos de la DFL y los 10 de `lector.ENTRENAMIENTO` de SkillCorner, cada uno con el balón de
  sus dos condiciones que votan. **`lector.EXAMEN` no se lee en ningún paso** (`exigir_solo_entrenamiento` en cada
  lector).
- **Aumentos hacia el ATD,** sorteados por trozo con semilla fija: el campo en espejo; el balón entre 0 y 5 frames
  tarde (el ATD llega unos 4, 15/11); slots que faltan y un slot duplicado (en el partido un equipo tiene más de 11
  slots en el 12,9 % de los frames, 16/11); un hueco más de balón de 1 a 4 s; y, en la DFL, el balón a la vista en
  los `D` la mitad de las veces (`d_propio.con_balon_en_d`: en el ATD se ve en el 68 % de los frames de las ventanas
  `SET PIECES`).
- **Entrenamiento:** torch en la GPU, en un entorno aparte (`mtah2027-conjunto`); AdamW (tasa 2e-3, decaimiento
  1e-4), 3.000 pasos de 32 trozos de 512 grupos (102 s), mitad de la DFL y mitad de SkillCorner; los 64 grupos de
  cada borde no cuentan en la pérdida; semilla 20261117 más el índice del pliegue; sin parada temprana.
- **Pliegues:** 7, y el de todos. El pliegue k deja fuera el partido k de la DFL y los partidos k y k + 7 de
  `lector.ENTRENAMIENTO` (los que haya). Cada partido se puntúa con el pliegue que no lo vio. El de todos es el de la
  entrega y el del examen.

**Los dos candidatos,** frente a `main` (B5, `dead_state` y `decode_cortas_a_d` con coste 25):
- **K1, la capa de cambios aprendida:** `main` más `cambios.capa(p, γ, 50, contra_d=True)`, con `p` las dos
  probabilidades de cambio del modelo. Es el mecanismo de la segunda ronda de David (W = 50, contra el otro equipo,
  sin rebaja), con otro detector. γ sale de (2, 4, 8).
- **K2, el equipo del modelo en lugar de B5:** z puntuada como B5 (`aprendida.puntuacion_de("b5", z, visible, α,
  cercano)`), sin capa. α sale de la rejilla de B5 (1/16 a 8).
- **Cómo se eligen γ y α:** para cada partido de la DFL, el valor que más saca en los otros seis con sus salidas
  fuera de muestra (media del `spellF1` de las dos convenciones, las dos condiciones que votan y los dos modos del
  `D`); si empatan, el más pequeño. En SkillCorner y en la entrega, el elegido con los 7. No está anidado del todo,
  como la rejilla del detector de cambios.

**Regla de entrada: el límite de daño del 16/11, tal cual,** para cada candidato:
1. **DFL con control:** +0,005 o más en las dos condiciones que votan, ganando en 6 de 7, con el `D` de las
   etiquetas y con el propio.
2. **SkillCorner** (solo si pasan 1 y 3): +0,005 o más con los 10 partidos de entrenamiento juntos y 7 de 10, en las
   cuatro celdas, **cada partido con el pliegue que no lo vio**. Solo entonces se abre el examen, una vez y para un
   solo candidato (si pasan los dos, el que más gana con control en la DFL; si empatan, K1, que no quita B5), con el
   modelo de todos y el mismo umbral. Ismael dio el permiso el 16/11, una vez por candidato; el uso se apunta en
   `validation/skillcorner/BITACORA.md`.
3. **DFL con el flag:** no pierde más de 0,005 en ninguna celda. Además, con el `D` propio y el balón a la vista en
   los `D`, tampoco pierde más de 0,005 con ninguna convención.
4. **Entrega de prueba** frente a `equipo_v9`, con criterios de daño escritos antes de generarla. La ejecuta una
   persona.

**Sin voto (descriptivo):** lo que ve la salida de cambios fuera de muestra, con la medida de David (cambios vistos,
avisos por minuto vivo y avisos buenos, umbral 0,5), para compararla con su detector; el acierto por frame; las
posesiones predichas frente a las reales; y el resultado sin el partido del piloto.

**El piloto.** Antes de entrenar los 8 pliegues se entrena uno solo (el que deja fuera `J03WMX` y dos partidos de
SkillCorner) para ver que aprende. Mirando ese pliegue se pueden tocar: los pasos, la tasa, el tamaño de la red, los
pesos de la pérdida, la fuerza de los aumentos y los errores del código. **No se tocan:** los candidatos, las
etiquetas, los pliegues, las rejillas ni la regla. Lo que quede se fija en un commit antes de entrenar el resto, y esos
tres partidos se dicen: sus resultados han servido para elegir.

**Lo que se deja fuera, y por qué:**
- **El `D` dentro del modelo.** El harness tapa el balón en todos los `D` de la DFL y SkillCorner casi no tiene
  tracking en las paradas (S4): un modelo que ve el balón aprendería «sin balón, `D`», que en el ATD no vale. El `D`
  sigue siendo de `dead_state` y `dead_ball`. Es la parte del punto 2 del análisis que no se prueba.
- **Un decodificador nuevo.** Los dos candidatos entran por enchufes que ya existen y están probados, sin tocar
  `pipeline.py`, `PIECES` ni `DELIVERY_LAYERS`.
- **La predicción en numpy,** las pruebas de paridad y el fichero de pesos: solo para un candidato que pase 1 y 3.
  Hasta entonces, las salidas del modelo se calculan con torch y se guardan fuera del repo.

Avisado antes de medir:
- **Circularidad:** las etiquetas de control salen de una regla de proximidad con el tracking limpio. Aquí pesa más
  que en B5, porque se entrena con ellas en todos los frames. Por eso deciden también el flag (como límite) y
  SkillCorner, cuyas etiquetas no son nuestras.
- **Los precedentes** (la red de una capa, B9, el detector de cambios y B11) ganaron con el flag, empataron con control
  y no pasaron SkillCorner. Si sale lo mismo, la regla lo cierra.
- **Nada de esto se mide en el ATD.** Los jugadores del ATD (46 slots, sin identidad) no se parecen del todo a ninguno
  de los dos proveedores; los aumentos lo acercan, pero no lo prueban.

Estado: escrita antes de exportar, entrenar o medir. El piloto y el resultado van en las entradas siguientes.
`pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega (`equipo_v9`) no cambian.

### 2026-11-17 · candidatos · modelo conjunto: el piloto no cambia nada; la configuración queda fijada

Quién: Claude, en la sesión de Ismael (17/11). Escrita después del piloto y antes de entrenar los otros pliegues.

Qué se probó: el pliegue que deja fuera `J03WMX` (DFL) y `1874553` y `2010085` (SkillCorner), con la configuración
de la entrada anterior y cinco variantes, todas dentro de lo que el piloto podía tocar. Código en `validation/conjunto/`
(`exportar.py`, `red.py`, `entrenar.py`, `medir.py`); torch 2.14.1 con CUDA en la RTX 3060, unos 2,7 minutos por
pliegue.

Resultado [medido; los tres partidos que el pliegue no vio, con el balón de sus dos condiciones que votan]:

| variante | pesos | pasos | acierto de z: DFL / SkillCorner | pérdida de z: DFL / SkillCorner | dentro de muestra (DFL) |
|---|---|---|---|---|---|
| **la escrita antes** | 36.260 | 3.000 | 93,7 % / 85,9 % | 0,160 / 0,317 | 93,2 % |
| red 9 veces mayor (64 por jugador, 96 canales, 10 bloques) | 308.484 | 8.000 | 92,1 % / 84,8 % | 0,42 / 1,05 | 99,4 % |
| la misma, 6.000 pasos | 36.260 | 6.000 | 93,5 % / 85,8 % | 0,155 / 0,343 | 95,2 % |
| 64 canales, abandono 0,2 | 84.740 | 4.000 | 92,0 % / 85,7 % | 0,184 / 0,355 | 96,2 % |
| más abandono, más slots que faltan y más decaimiento | 36.260 | 3.000 | 93,5 % / 86,4 % | 0,167 / 0,315 | 92,3 % |
| la misma, 2.000 pasos | 36.260 | 2.000 | 93,6 % / 86,0 % | 0,160 / 0,314 | 91,7 % |

- **La red grande se aprende los partidos de memoria:** acierta el 99 % de lo que vio y pierde fuera. Con ±12 s de
  contexto, la posición de 22 jugadores identifica el momento del partido.
- **La escrita antes no se sobreajusta** (acierta lo mismo dentro y fuera) y las tres variantes pequeñas dan lo mismo
  fuera de muestra, dentro del ruido de tres partidos.
- **La salida de cambios es prudente:** con el umbral 0,5 ve el 22–25 % de los cambios de control de la DFL, con 0,8–1,0
  avisos por minuto vivo y el 68–72 % buenos (el detector aprendido de David: 55–63 % vistos, 10–16 avisos por minuto,
  23–25 % buenos). En SkillCorner ve el 4–9 %, con el 30–40 % buenos.
- **Comprobación del instrumento** (`medir.py --comprobar`, `J03WMX`): K1 con `p` a cero y K2 con el logit y la α de B5
  dan `main` frame a frame en las 18 salidas.
- **La predicción en numpy** (`possession/conjunto.py`, sin exponenciales y sin BLAS) frente a torch en dos partidos:
  diferencia máxima de z de 0,003, y el signo cambia en 7 y 25 frames de 150.000 (`paridad.py`). Tarda 4–5 s por
  partido.
- **Descriptivo, con los candidatos en esos tres partidos** (han servido para mirar; no deciden):
  - K2 en `J03WMX`, con α entre 1 y 8: de +0,068 a +0,089 con control y de +0,03 a +0,05 con el flag, con el `D` de las
    etiquetas; en los dos de SkillCorner, con α entre 0,5 y 4: de +0,050 a +0,056 con el `D` de las etiquetas y de
    +0,027 a +0,033 con el propio.
  - K1 en `J03WMX`, con γ = 8: +0,024 y +0,018 con control y +0,035 con el flag; en SkillCorner, entre −0,006 y +0,018.

Decisión y por qué: **no se toca nada.** Los 8 pliegues se entrenan con la configuración escrita antes de entrenar
(`entrenar.CONFIG`). Es la más simple de las que empatan y no hay que explicar ningún cambio. La red grande se descarta
por sobreajuste.

Lo que se dice con el resultado final: `J03WMX`, `1874553` y `2010085` son los partidos del piloto. No cambiaron la
configuración, pero se miraron antes de fijarla; el resultado se da también sin `J03WMX`.

Descartado: la red grande y las variantes con más pasos o más canales (sobreajuste); elegir entre las tres pequeñas
por una diferencia que tres partidos no distinguen.

Estado: configuración fijada en este commit. El resultado de los 7 partidos de la DFL y de SkillCorner va en la entrada
siguiente.

### 2026-11-17 · candidatos · modelo conjunto: K2 pasa los puntos 1, 2 y 3 de su regla (examen incluido); K1 no pasa

Quién: Claude, en la sesión de Ismael (17/11). Las reglas son las de las dos entradas anteriores (`b4ec45f` y
`5cd0357`), escritas antes de medir.

Qué se probó: los dos candidatos, con los 8 pliegues entrenados con la configuración fijada.
- **K2:** el logit del modelo conjunto en lugar del de B5 (`aprendida.evidence_k2`), puntuado como B5.
- **K1:** `main` más la capa de cambios aprendida (`conjunto.capa_cambios`).

Cómo se midió:
- **DFL:** los 7 partidos, cada uno con el pliegue que no lo vio, con `validation/conjunto/medir.py` y con el harness
  oficial (`puntuar.py --versiones validation/harness/versiones/conjunto_2026-11-17.json`, con `--d oraculo --eventos` y
  con `--d propio`; código en `56ee7c6`). Bootstrap pareado de 1.000.
- **SkillCorner:** los 10 partidos de `lector.ENTRENAMIENTO`, cada uno con el pliegue que no lo vio, y los 10 de
  `lector.EXAMEN`, **una sola vez y solo para K2**, con el modelo de los 17 partidos (código en `a37010a`; apuntado en
  `validation/skillcorner/BITACORA.md`).
- **`main`** es la entrega de hoy (B5, `dead_state` y `decode_cortas_a_d`) y repite sus cifras conocidas: 0,498 y 0,728
  en la DFL con el `D` de las etiquetas, 0,414 y 0,623 con el propio, y 0,519 y 0,391 en SkillCorner.
- **γ y α,** elegidas dejando un partido fuera: γ = 8 en los 7 pliegues; α = 4 en cuatro y 8 en tres, y 4 con los 7.
- Salidas en `validation/conjunto/salidas/`; resumen en `validation/resultados/2026-11-17_modelo_conjunto.md`.

Resultado [medido], K2 frente a `main`:

| datos | `D` | condición | `main` | K2 | diferencia [5–95 %] | gana en |
|---|---|---|---|---|---|---|
| DFL, control | de las etiquetas | como el ATD | 0,728 | 0,780 | +0,051 [+0,040 a +0,064] | 7 de 7 |
| DFL, control | de las etiquetas | como el ATD, sin bloques | 0,748 | 0,794 | +0,046 [+0,035 a +0,057] | 6 de 7 |
| DFL, control | propio | como el ATD | 0,623 | 0,668 | +0,045 [+0,035 a +0,057] | 6 de 7 |
| DFL, control | propio | como el ATD, sin bloques | 0,651 | 0,686 | +0,036 [+0,024 a +0,047] | 6 de 7 |
| DFL, flag | de las etiquetas | como el ATD | 0,498 | 0,542 | +0,044 [+0,034 a +0,054] | 7 de 7 |
| DFL, flag | de las etiquetas | como el ATD, sin bloques | 0,512 | 0,549 | +0,037 [+0,027 a +0,046] | 7 de 7 |
| DFL, flag | propio | como el ATD | 0,414 | 0,457 | +0,043 [+0,034 a +0,052] | 7 de 7 |
| DFL, flag | propio | como el ATD, sin bloques | 0,431 | 0,464 | +0,033 [+0,024 a +0,042] | 7 de 7 |
| SkillCorner, entrenamiento | de las etiquetas | detectado | 0,519 | 0,543 | +0,023 [+0,015 a +0,031] | 8 de 10 |
| SkillCorner, entrenamiento | de las etiquetas | detectado, suavizado | 0,514 | 0,539 | +0,024 [+0,016 a +0,032] | 7 de 10 |
| SkillCorner, entrenamiento | propio | detectado | 0,391 | 0,413 | +0,021 [+0,014 a +0,029] | 10 de 10 |
| SkillCorner, entrenamiento | propio | detectado, suavizado | 0,388 | 0,412 | +0,024 [+0,017 a +0,032] | 10 de 10 |
| **SkillCorner, examen** | de las etiquetas | detectado | 0,509 | 0,532 | +0,023 [+0,015 a +0,032] | 9 de 10 |
| **SkillCorner, examen** | de las etiquetas | detectado, suavizado | 0,504 | 0,532 | +0,028 [+0,019 a +0,037] | 10 de 10 |
| **SkillCorner, examen** | propio | detectado | 0,389 | 0,409 | +0,021 [+0,013 a +0,028] | 8 de 10 |
| **SkillCorner, examen** | propio | detectado, suavizado | 0,384 | 0,410 | +0,026 [+0,019 a +0,034] | 10 de 10 |

- **Punto 1 (DFL con control): pasa.** Pedía +0,005 y 6 de 7 en las cuatro celdas.
- **Punto 3 (DFL con el flag): pasa, y además gana** en 7 de 7 en las cuatro celdas. Con el balón a la vista en los
  `D` y el `D` propio tampoco pierde: +0,044 y +0,035 con control y +0,035 y +0,029 con el flag.
- **Punto 2 (SkillCorner): pasa** la mitad de entrenamiento con los pliegues cruzados y **el examen**, con el umbral
  escrito antes (+0,005 y 7 de 10 en las cuatro celdas).
- **Gana también con la regla de §5.8 frente a `main`** (más de +0,03 con las dos convenciones en las dos condiciones
  que votan, 6 de 7 o más y los intervalos por encima de cero), con el `D` de las etiquetas y con el propio. Es lo que
  dice la salida del harness oficial; la regla que se había escrito era la del límite de daño.
- **Eventos humanos de la DFL** (descriptivo; no dependen de nuestras etiquetas), «como el ATD», K2 frente a `main`:
  recuperaciones del 70,3 al 80,0 % (+9,7 [+4,1 a +14,9]), duelos con cambio del 77,3 al 82,5 % (+5,2 [+2,2 a +9,2]) y
  duelos sin cambio del 74,9 al 77,7 % (+2,8 [−1,9 a +7,6]). Veredicto del harness: «mejora» en las dos condiciones.
  Cambia más cuando debe y no cambia más cuando no debe.
- **No predice más posesiones, las coloca mejor:** en la DFL con el `D` de las etiquetas, 1.651 frente a las 1.661 de
  `main` (1.736 reales con control). En SkillCorner, 2.306 frente a 2.270 (3.228 reales).
- **No depende de α:** con cualquier α entre 0,5 y 8 gana en las ocho celdas de la DFL (con control, de +0,032 a
  +0,062).
- **Sin el partido del piloto** (6 partidos): con control, +0,047 (6 de 6), +0,042, +0,043 y +0,034 (5 de 6); con el
  flag, de +0,034 a +0,045 (6 de 6).
- **Las condiciones sin voto** (`D` de las etiquetas; flag y control): con el balón limpio, +0,032 y +0,034; con «huecos
  y suavizado», la prueba de estrés con el 41 % del juego sin balón, +0,040 y +0,064.

**K1 no pasa el punto 1:** con control gana +0,009 (5 de 7), +0,008 (4 de 7), +0,016 (6 de 7) y +0,011 (4 de 7), y se
pedían 6 de 7 en las cuatro celdas. Con el flag gana +0,024 a +0,028 (7 de 7). No sigue a SkillCorner y
`conjunto.capa_cambios` se queda apagada.

**La pieza en numpy** (`possession/conjunto.py`, la que usaría la entrega; pesos en `possession/conjunto_pesos.npz`,
1,2 MB):
- da las mismas cifras que las salidas de torch en todas las celdas de la DFL y de SkillCorner;
- frente a torch, la diferencia máxima de z es de 0,003 y el signo cambia en 4 a 65 frames de unos 145.000 por partido;
- la interpolación de grupos a frames se reescribió sin `np.interp` después del examen, para que el último bit no
  dependa de la máquina (`56ee7c6`). Da lo mismo hasta 2·10⁻¹⁵, y las tablas del harness oficial salen idénticas fila a
  fila antes y después. El examen no se repitió;
- pasa `validation/scripts/prueba_conjunto.py` (24 comprobaciones sin datos) y no cambia la entrega: `prueba_pipeline`,
  `prueba_aprendida`, `prueba_harness`, `prueba_cambios` y `prueba_decodificador` siguen en verde.

Decisión y por qué: **K2 ha pasado los puntos 1, 2 y 3 y sigue al punto 4** (la entrega de prueba, más abajo). No entra
todavía en nada: `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega (`equipo_v9`) no cambian. K1 se cierra.

Lo que hay que decir con el número:
- **Circularidad.** Las etiquetas de control salen de una regla de proximidad y el modelo se entrena con ellas. Lo que
  no es circular dice lo mismo: gana con el flag, en SkillCorner (sus etiquetas no son nuestras) y en los eventos
  humanos.
- **Cuántas cosas se han probado.** Dos candidatos y seis variantes de entrenamiento en el piloto, que no cambió nada.
  El examen se usó una vez.
- **La α no está anidada del todo,** como la rejilla del detector de cambios. Pesa poco: todas las α entre 0,5 y 8
  ganan.
- **El harness sobrestima el nivel y nada de esto se ha medido en el ATD.** El modelo ve a cada jugador, y los 46 slots
  del ATD no se parecen del todo ni a la DFL ni a SkillCorner. Para eso está el punto 4.
- **Qué parte del análisis era cierta** [inferencia, sobre lo medido]: no hizo falta cambiar la pregunta ni el
  decodificador. Lo que movió el número fue cambiar la evidencia: mirar a cada jugador, entrenar con control en todos
  los frames vivos y entrenar también con otro proveedor. La salida de cambios por sí sola (K1) no bastó.

**Punto 4: la entrega de prueba, con los criterios de daño escritos antes de generarla.**

Lo que cabe esperar [medido en los datos abiertos con `validation/conjunto/cuanto_cambia.py`: el pipeline entero con el
`D` propio, sin las capas del partido, con K2 en lugar de B5]:

| datos | frames evaluados que cambian | de un equipo al otro | entre un equipo y `D` | posesiones | paradas | frames `D` | posesiones de menos de 12 / de 25 frames |
|---|---|---|---|---|---|---|---|
| DFL (7 partidos, 4 celdas) | 4,4–5,3 % | 3,2–3,5 % | 1,2–1,8 % | de +0,1 a +2,8 % | de −0,3 a +0,4 % | de −0,2 a +0,2 puntos | 0 / de 6 a 12 en los 7 partidos |
| SkillCorner (10 partidos, 2 celdas) | 7,5–7,9 % | 3,1–3,3 % | 4,5–4,6 % | de +3,1 a +4,2 % | +1,5 % | de +2,1 a +2,4 puntos | 0 / 6 o 7 en los 10 partidos |

La fuerza de la evidencia es parecida a la de B5 [medido en dos partidos de SkillCorner, con los pesos de la entrega: la
mediana de la diferencia `H` − `A` por frame es de 8,3–8,6 con K2 y de 9,0–10,4 con B5; las dos con α = 4], así que las
capas del partido (contraataques, balón fuera, anclas) pesan más o menos lo mismo frente a ella.

Lo ejecuta una persona, con el python del entorno limpio y desde la carpeta de esta rama:

    python -m possession.pipeline --name equipo_v9_rama
    python validation/partido/conjunto_en_el_partido.py
    python validation/partido/probar_entrega.py prueba_k2 --pieza candidates=aprendida.evidence_k2 --contra equipo_v9_rama
    python evaluation/validate_submission.py evaluation/results/prueba_k2.csv

y después `/evaluar` para ver la ventana pública de las dos.

K2 pasa el punto 4 si se cumple todo:
- **C0, la rama no cambia la entrega:** `equipo_v9_rama` sale con el sha256 de `equipo_v9` (`d9706dfb…be63`).
- **C1, es una entrega:** `prueba_k2` es válida y sale con 0 frames en conflicto.
- **C2, el modelo ve en el ATD algo parecido a lo que vio:** las seis salidas de `conjunto_en_el_partido.py` caen
  dentro del rango de las 34 vistas de los datos abiertos, ensanchado un cuarto por cada lado (lo dice el script). Las
  entradas que caigan fuera se apuntan y no deciden. Se espera una: en el partido un equipo tiene más de 11 slots en el
  12,9 % de los frames, y en los abiertos, en menos del 1 %.
- **C3, cambia lo que cabe esperar:** frente a `equipo_v9_rama` cambia como mucho el 12 % de los frames evaluados; de un
  equipo al otro, como mucho el 6 %; y entre un equipo y `D`, en los dos sentidos, como mucho el 6 %.
- **C4, no cambia el ritmo ni el `D`:** entre 185 y 235 posesiones (`equipo_v9` tiene 201), entre 109 y 123 paradas
  (tiene 116) y entre el 45,2 y el 49,2 % de `D` en lo evaluado (tiene el 46,2 %).
- **C5, no fragmenta:** ninguna posesión de menos de 12 frames y como mucho 4 de menos de 25.
- **C6, no se rompe en la ventana pública:** el macroF1 no baja más de 0,03 ni el spellF1 más de 0,10 respecto a
  `equipo_v9`. Una subida no cuenta: la ventana no elige (con 17 posesiones, hasta 0,39 es ruido).

Si pasa todo, K2 ha cumplido su regla entera y lo que queda es una decisión del equipo: encenderlo es poner
`"aprendida.evidence_k2"` en `pipeline.PIECES["candidates"]`, regenerar y validar (`equipo_v10`), y reproducirlo en otra
máquina antes de entregar. Si falla C2, o C3, C4 o C5, no se enciende sin mirar antes por qué.

**Punto 3 del análisis, decodificar para la métrica: regla del sondeo, escrita antes de ejecutarlo.** Con un candidato
que ha pasado, se repite S2 (16/11) con la evidencia de K2 en lugar de la de B5:
`validation/conjunto/riesgo_minimo_k2.py`, que usa el instrumento de S2 sin tocarlo (DFL, «como el ATD», `D` de las
etiquetas; lo que el instrumento llama `main` es el Viterbi de coste 25 sobre K2). La regla es la de S2, tal cual:
- «la duda del modelo sirve» si la correlación de rangos entre la anchura de la duda y el error es de 0,3 o más, o la
  anchura separa los cambios sin pareja con un AUC de 0,65 o más, con las dos convenciones;
- «el riesgo mínimo merece construirse» si la elección por parte gana al Viterbi de coste 25 por +0,010 o más con las dos
  convenciones.
Si no merece construirse, el punto 3 se cierra también para este modelo. Avisado antes: z se entrenó frame a frame, así
que la cadena con temperatura puede volver a fragmentarse, como con B5; una distribución sobre secuencias pediría
entrenar el modelo como un CRF, que sería otro candidato.

Descartado: encender K2 sin el punto 4; repetir el examen después del cambio de la interpolación; elegir entre α
mirando la tabla; seguir con K1.

Estado: K2 espera el punto 4, que ejecuta una persona. El sondeo del riesgo mínimo se ejecuta después de este commit.

### 2026-11-17 · temporal · riesgo mínimo con la evidencia de K2: no merece construirse; se cierra

Quién: Claude, en la sesión de Ismael (17/11). Regla en la entrada anterior, escrita antes de ejecutarlo (`10c899f`).

Qué se probó: el sondeo S2 del 16/11 con la evidencia de K2 en lugar de la de B5
(`validation/conjunto/riesgo_minimo_k2.py`; salida en `validation/conjunto/salidas/2026-11-17_riesgo_minimo_k2.md`).

Cómo se midió: los 7 partidos de la DFL, «como el ATD», `D` de las etiquetas, K2 con el pliegue que no vio cada partido;
24 muestras por parte; seis costes de cambio.

Resultado [medido]:
- **La duda del modelo ahora sí dice algo:** la anchura de la duda separa los cambios sin pareja con un AUC de 0,68
  (flag) y 0,70 (control); con B5 eran 0,60 y 0,69. La correlación con el error es de 0,24 y 0,25 (con B5, 0,09 y 0,14).
  Cumple la primera parte de la regla por el AUC.
- **Las muestras se siguen fragmentando:** una muestra tiene una mediana de 2.196 posesiones por parte, cuando hay unas
  220. z se entrenó frame a frame, y los frames vecinos no son independientes.
- **La elección por parte no gana:** elige el coste 8 en 13 de las 14 partes y saca 0,549 con el flag (+0,007 sobre el
  coste 25) y 0,761 con control (−0,019). Se pedía +0,010 con las dos convenciones. Ni un oráculo que eligiera el mejor
  coste en cada parte pasa de +0,009 y +0,010.
- Descriptivo: con K2, subir el coste a 35 o 50 da +0,004 y +0,006 con control y −0,002 y −0,006 con el flag. Es el
  mismo compromiso entre convenciones que con B5, y no se toca.

Decisión y por qué: **no merece construirse; el punto 3 del análisis se cierra también para este modelo.** No se prueban
variantes.

Lo que queda apuntado para una fase siguiente: una distribución sobre secuencias de verdad pediría entrenar el modelo
como un CRF, con la verosimilitud de la secuencia entera. Sería otro candidato, con su regla.

### 2026-11-17 · candidatos · modelo conjunto: tres comprobaciones más antes de recomendar nada (lectura, antes de medir)

Quién: Claude, en la sesión de Ismael (17/11), tras la revisión del resultado. Escrita antes de entrenar o medir nada
de esto, y antes de que nadie ejecute nada sobre el partido.

Por qué: todo lo que K2 ha pasado está medido **dentro del proveedor**. Los partidos de la DFL se puntuaron con modelos
que vieron otros partidos de la DFL, y los de SkillCorner (el examen incluido), con modelos que vieron SkillCorner. El
partido es un tercer proveedor, y ahí es donde falló B11. Además, dos rasgos medidos del ATD se usaron como aumentos al
entrenar, pero no se han puntuado.

Son tres comprobaciones **descriptivas**: no cambian la regla de K2 ni abren un candidato. Dicen cuánto fiarse del punto
4 y qué decirle a quien decida.

1. **El otro proveedor** (`entrenar.py --solo` y `medir.py --alfa 4`). Dos modelos con la configuración fijada, cada uno
   con un solo proveedor, puntuados en el otro: uno entrenado con los 10 partidos de `lector.ENTRENAMIENTO`, en los 7 de
   la DFL; otro con los 7 de la DFL, en los 10 de `lector.ENTRENAMIENTO`. α = 4, la elegida; no se elige nada. No toca
   el examen.
   - **«Aguanta otro proveedor»** si, en los dos sentidos, gana a `main` en todas las celdas (la DFL con control y con el
     flag, y SkillCorner; `D` de las etiquetas y propio) y por +0,005 o más con control y en SkillCorner. Entonces la
     recomendación de probarlo en el partido se mantiene tal cual.
   - **«Depende del proveedor»** si en algún sentido se queda entre −0,005 y +0,005. Entonces la ganancia medida viene
     de haber visto ese proveedor, y en el ATD cabe esperar un empate: K2 solo se enciende si el punto 4 sale limpio, y
     se dice que el harness no lo respalda fuera de sus proveedores.
   - **«No aguanta»** si en algún sentido pierde más de 0,005 en alguna celda. Entonces no se recomienda encenderlo
     para la entrega, aunque pase el punto 4: sería una apuesta, y se dice así.
   - Además dice si entrenar con SkillCorner hacía falta: es lo que mide el modelo entrenado solo con la DFL.
2. **Los slots y el balón como los del partido** (`validation/conjunto/como_el_atd.py`). En los 7 partidos de la DFL,
   con el pliegue que no vio cada uno y las dos condiciones que votan, K2 y `main` con tres degradaciones que ya existen
   y están calibradas con agregados del partido: los slots de P4 (tracklets cortados y un slot de más en el 12,9 % de los
   frames, `investigacion_1116/slots_dfl.degradar`), el balón 4 frames tarde (`ball.advance_ball`, 15/11) y las dos
   juntas.
   - **«Aguanta»** si, con las dos juntas, K2 sigue ganando a `main` por +0,005 o más con control en las cuatro celdas
     (dos condiciones, `D` de las etiquetas y propio) y no pierde con el flag.
   - Si no, se dice cuál de las dos lo estropea y cuánto. K2 mira a cada jugador, así que un slot de más puede pesarle
     más que a B5.
3. **La referencia del criterio C2, con el balón a la vista en las paradas.** `referencia_abiertos.json` se calculó
   con las vistas en que el balón va tapado en los `D`. En el ATD el balón se ve en la mayoría de los frames de las
   paradas, así que sus agregados «con balón» incluyen frames que la referencia no vio, y el criterio podría saltar sin
   motivo. Se añaden las 14 vistas de la DFL con el balón a la vista en los `D` (48 vistas en total) y se regenera el
   JSON. **Es una enmienda al criterio C2, hecha antes de que nadie ejecute nada sobre el partido.** El resto de C2 no
   cambia.
4. **Metrica** (añadido antes de ejecutarlo; `validation/conjunto/metrica.py`). Los 3 partidos de Metrica sample-data,
   que el modelo de los 17 partidos nunca vio y que son de un tercer proveedor, con las condiciones de
   `validation/metrica/medir.py`. Solo se dice lo que sale, con dos avisos ya medidos: sus etiquetas vienen de eventos
   (un toque con impacto, no control) y su balón va pegado al jugador (S10), así que favorece a la proximidad. Si K2
   pierde más de 0,005 frente a `main` en la condición que vota con el `D` de las etiquetas, se apunta como otro aviso
   de proveedor; si gana, no prueba nada por sí solo.

**Añadido después de ver los puntos 1 y 4, y antes de ejecutar lo que sigue.** El punto 1 dice que con un solo
proveedor el modelo no se traslada al otro, y el 4, que el modelo de los dos proveedores gana en Metrica. Para saber
cuánto vale lo segundo y cuánto protege el criterio C2, dos medidas más, también descriptivas:

5. **Los modelos de un solo proveedor, en Metrica** (`metrica.py --pesos`). Si también ganan a `main` allí, Metrica no
   distingue nada (su balón va pegado al jugador) y la ganancia del modelo de los dos proveedores no dice que
   generalice. Si pierden o empatan y el de los dos gana, es una señal a favor de que entrenar con dos proveedores sí
   ayuda en un tercero. Una señal, con 3 partidos: no una prueba.
6. **¿Habría saltado C2 donde sabemos que el modelo falla?** (`validation/conjunto/potencia_c2.py`). Con cada modelo de
   un solo proveedor: la referencia son sus seis salidas en las vistas de su proveedor (dentro de muestra, porque no
   hay otra; se dice) y se mira en cuántas vistas del otro proveedor alguna salida cae fuera del rango ensanchado un
   cuarto, que es lo que hace C2 con el partido. Si salta en la mayoría de las vistas del otro proveedor, C2 sirve de
   alarma; si no, pasar C2 no dice que el modelo funcione en el ATD, y se le dice así a quien decida.

Estado: escrita antes de medir. Los resultados van en la entrada siguiente.

### 2026-11-17 · candidatos · modelo conjunto: K2 no se traslada de un proveedor a otro; no se recomienda para la entrega sin más

Quién: Claude, en la sesión de Ismael (17/11). La lectura es la de la entrada anterior, escrita antes de medir
(`bf15c4b`, `4845078` y `8c46846`). Salidas en `validation/conjunto/salidas/`.

Resultado [medido]:

1. **El otro proveedor: «no aguanta».** K2 con α = 4 frente a `main`, con el modelo entrenado con un solo proveedor y
   puntuado en el otro:

   | entrenado solo con | puntuado en | `D` de las etiquetas | `D` propio |
   |---|---|---|---|
   | la DFL (7 partidos) | SkillCorner, entrenamiento (10) | −0,015 [−0,023 a −0,007] (3 de 10) y −0,010 [−0,018 a −0,002] (5 de 10) | −0,007 y −0,004 |
   | SkillCorner (10) | la DFL, con control (7) | −0,096 [−0,110 a −0,082] y −0,075 [−0,088 a −0,061] (0 de 7) | −0,062 y −0,045 |
   | SkillCorner (10) | la DFL, con el flag (7) | −0,060 y −0,041 (0 de 7) | −0,036 y −0,024 |

   - El modelo entrenado solo con la DFL pierde en SkillCorner lo mismo que B11 (−0,012 y −0,009). **Entrenar con
     SkillCorner hacía falta para ganar en SkillCorner**: eso ya no es una lectura, está medido.
   - El modelo entrenado solo con SkillCorner pierde mucho en la DFL. Acierta el 83–90 % de los frames vivos, cuando el
     de los dos proveedores acierta el 90–95 %.
   - **Todo lo que K2 pasó (la DFL, SkillCorner y su examen) lo pasó con partidos de ese mismo proveedor en el
     entrenamiento.** El partido es de otro.
   - Un matiz [inferencia]: aquí se mezclan dos cambios, el de los datos y el de las etiquetas. SkillCorner etiqueta
     la posesión a su manera (6,05 posesiones por minuto, frente a 4,71 con control), así que parte de la pérdida es de
     convención.
2. **Los slots y el balón como los del partido: «aguanta».** Con los tracklets cortados, un slot de más en el 12,9 % de
   los frames y el balón 4 frames tarde, todo junto, K2 gana a `main` por +0,068 (7 de 7), +0,055, +0,054 y +0,040 con
   control y por +0,042 a +0,052 con el flag. A `main` las dos degradaciones le cuestan hasta 0,013 con control; a K2,
   entre −0,002 y +0,004. Los aumentos del entrenamiento hacen lo que tenían que hacer.
3. **La referencia de C2** se regeneró con 48 vistas (`8c46846`), las 14 nuevas con el balón a la vista en los `D`. El
   script del partido dice ahora, además y sin voto, si las seis salidas caen dentro del rango de un mismo proveedor.
4. **Metrica, con el modelo de los 17 partidos:** +0,035 [+0,019 a +0,051] (2 de 3) en la condición que vota y +0,036
   (3 de 3) en la otra, con el `D` de las etiquetas; +0,021 y +0,024 con el propio.
5. **Metrica, con los modelos de un solo proveedor:** el de la DFL gana (+0,023 [+0,007 a +0,040] y +0,026) y el de
   SkillCorner pierde (−0,022 [−0,045 a +0,001] y −0,021). **Metrica sí distingue,** y el modelo de los dos proveedores
   es el que más gana de los tres. Es una señal a favor de que entrenar con dos ayuda en un tercero; con 3 partidos y un
   balón pegado al jugador, no es una prueba.
6. **C2 habría saltado donde el modelo falla:** con el modelo de solo SkillCorner, en 22 de las 28 vistas de la DFL
   (sobre todo por |z| sin balón y por los cambios de signo por minuto); con el de solo la DFL, en las 20 vistas de
   SkillCorner (los cambios de signo por minuto, en las 20). **C2 sirve de alarma.** Dos avisos: aquí la referencia era
   dentro de muestra, más estrecha; y en el partido el rango junta dos proveedores, más ancho (los cambios de signo van
   de 3,0 a 8,1 por minuto), así que es menos sensible. Por eso se añadió la línea por proveedor del punto 3.

   **Corrección (17/11, después del punto 4): «C2 sirve de alarma» dice más de lo que se midió.** Las dos salidas que
   hacen saltar el criterio, los cambios de signo por minuto y |z| sin balón, separan la DFL de SkillCorner también con
   el modelo de los dos proveedores, que funciona en los dos: de 3,0 a 4,6 frente a 5,4 a 8,1, y de 1,9 a 6,8 frente a
   0,5 a 1,4 (`referencia_abiertos.json`). Un modelo que funciona en SkillCorner también haría saltar una referencia
   hecha solo con la DFL. Lo que mide esta prueba es que los proveedores se ven distintos, no que C2 detecte un modelo
   que falla. **C2 dice si el partido se parece, para el modelo, a un proveedor conocido, y nada más.** Se retira de lo
   que hay «a favor» en la lista de más abajo.

Decisión y por qué, con la lectura escrita antes:
- **Por la comprobación 1, K2 no se recomienda para la entrega sin más.** Lo que el harness mide es lo que gana K2 en
  proveedores que ha visto, y el partido es de uno que no ha visto. Encenderlo es una apuesta, y se dice así.
- **No es una apuesta a ciegas** [inferencia, sobre lo medido]:
  - a favor: gana en el único tercer proveedor abierto (4 y 5); aguanta los dos rasgos medidos del ATD mejor que B5
    (2); y hay una alarma que funciona donde se sabe que falla (6);
  - en contra: con un solo proveedor no se traslada (1), y del ATD no hay ni un partido con etiquetas para comprobarlo.
    La ventana pública no vale para eso: con 17 posesiones no distingue nada, y no se puede elegir con ella.
- **Lo decide el equipo.** K2 sigue apagado: `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega (`equipo_v9`) no cambian.
  Si el equipo quiere mirarlo, el punto 4 está listo (C0 a C6, entrada «K2 pasa los puntos 1, 2 y 3»), con C2 leído
  así: si las salidas se salen, no se enciende; si caen dentro, la apuesta sigue siendo una apuesta, pero sin señales
  en contra.

Lo que queda para el documento técnico y para la fase siguiente:
- **El techo dentro del proveedor es alto:** mirar a cada jugador da de +0,04 a +0,05 sobre B5 cuando el modelo ha
  visto partidos de ese proveedor.
- **Lo que cojea ahora es el cambio de proveedor,** no la arquitectura ni el decodificador. Con etiquetas de unos pocos
  partidos del mismo tracking que el del reto, este modelo se podría entrenar para él. Sin ellas, lo que queda es
  acercar los datos de entrenamiento al ATD (jugadores que faltan como en SkillCorner, ruido de tracking automático) y
  medirlo dejando un proveedor fuera, que es el instrumento que ha salido de aquí.
- **B5 sí se traslada** (gana al baseline en SkillCorner y en Metrica sin haberlos visto): un modelo de 30 agregados
  generaliza mejor que uno de 36.000 pesos que ve a cada jugador. Es la razón de que siga en la entrega.

Descartado: recomendar K2 por sus cifras dentro del proveedor; abrir ahora una ronda de entrenamiento «más robusto»
(sería otro candidato, con su regla y sin examen disponible); usar la ventana pública para decidir.

Estado: K2 apagado, medido y documentado. El punto 4 espera a que el equipo decida si lo quiere mirar.

### 2026-11-17 · candidatos · modelo conjunto: una ronda contra el cambio de proveedor (K2r), con una sola configuración (antes de entrenar)

Quién: Claude, en la sesión de Ismael (17/11). Escrita antes de entrenar o medir nada de esta ronda.

Por qué se abre, cuando la entrada anterior la descartaba: Ismael pidió el 16/11 que, si una ronda falla, se abra otra
con su regla en vez de cerrar. Y esta es barata: no cambia la red ni la pieza en numpy, solo los aumentos del
entrenamiento, es decir, los pesos. Se corrige aquí lo que decía «Descartado» en la entrada anterior.

Qué se prueba: si el modelo entrenado **solo con la DFL** deja de perder en SkillCorner cuando sus partidos de
entrenamiento se parecen más a un tracking automático. Es el sentido que importa para el partido: de un tracking limpio
a uno automático. Una sola configuración, `entrenar.ROBUSTO`, que añade tres aumentos **a los trozos de la DFL** (los de
SkillCorner ya son así) y no toca nada más:
- **jugadores que faltan, como en SkillCorner:** en cada trozo se sortea cuántos se ven, entre el 65 y el 100 %, y cada
  slot falta todo el trozo con la probabilidad que toque (en SkillCorner se ven de 7,4 a 8,7 jugadores por equipo; en
  la DFL, de 10,5 a 11,0; en el partido, unos 10);
- **datos a 10 Hz,** en la mitad de los trozos: los jugadores y el balón se remuestrean a 10 Hz y se interpolan de
  vuelta, como hace el lector de SkillCorner;
- **ruido lento de posición,** en la mitad de los trozos: un desplazamiento por jugador de 0,2 m de desviación, que
  cambia cada segundo y se interpola en medio.

Regla, en dos pasos:
- **Paso A.** El modelo entrenado solo con la DFL con esos aumentos, puntuado en los 10 partidos de
  `lector.ENTRENAMIENTO` con α = 4 (lo mismo que la comprobación 1, que dio −0,015, −0,010, −0,007 y −0,004):
  - **«se traslada»** si gana a `main` por +0,005 o más en las cuatro celdas;
  - **«deja de perder»** si queda en −0,005 o más en las cuatro, sin llegar a lo anterior;
  - si pierde más de 0,005 en alguna celda, **la ronda se cierra aquí,** sin probar otros aumentos.
- **Paso B,** solo si A «se traslada» o «deja de perder». Se entrenan los 8 pliegues del modelo de los dos proveedores
  con esos aumentos (K2r, tanda `v2`) y se mide como K2: puntos 1 y 3 en la DFL, la mitad de entrenamiento de
  SkillCorner con los pliegues cruzados, Metrica y `como_el_atd.py`. K2r sustituye a K2 como candidato para el punto 4
  si pasa los puntos 1 y 3 y SkillCorner cruzado, y no queda más de 0,005 por debajo de K2 en ninguna celda de control
  de la DFL ni en Metrica. Si no, K2 se queda como está.
- **El examen de SkillCorner no se abre para K2r:** es una variante de un candidato ya examinado, y el equipo no ha
  decidido si eso cuenta como candidato nuevo (`validation/skillcorner/BITACORA.md`). Se dice con el resultado.

Avisado antes de medir:
- Que el paso A salga bien no prueba que K2r gane en el ATD: prueba que estos aumentos acercan un tracking limpio a uno
  automático de otro proveedor. Es la mejor imitación que hay de lo que le pasará con el partido.
- Los tres aumentos se eligieron por lo medido en `referencia.py` y por cómo lee SkillCorner su lector, no mirando
  ningún resultado. No se prueban uno a uno ni se ajustan sus valores.

Estado: escrita antes de entrenar. El resultado va en la entrada siguiente.

### 2026-11-17 · candidatos · modelo conjunto, ronda K2r: los aumentos acercan, pero no bastan; se cierra en el paso A

Quién: Claude, en la sesión de Ismael (17/11). Regla en la entrada anterior, escrita antes de entrenar (`068357a`).

Qué se probó: el paso A. El modelo entrenado solo con los 7 partidos de la DFL con `entrenar.ROBUSTO` (jugadores que
faltan, datos a 10 Hz y ruido lento de posición en los trozos de la DFL), puntuado con α = 4 en los 10 partidos de
`lector.ENTRENAMIENTO`. Salida en `validation/conjunto/salidas/2026-11-17_k2r_paso_a.md`.

Resultado [medido], frente a `main`:

| `D` | condición | sin los aumentos (comprobación 1) | con los aumentos |
|---|---|---|---|
| de las etiquetas | detectado | −0,015 [−0,023 a −0,007] (3 de 10) | −0,004 [−0,012 a +0,004] (5 de 10) |
| de las etiquetas | detectado, suavizado | −0,010 [−0,018 a −0,002] (5 de 10) | −0,002 [−0,010 a +0,006] (5 de 10) |
| propio | detectado | −0,007 | −0,008 [−0,015 a −0,001] (3 de 10) |
| propio | detectado, suavizado | −0,004 | −0,005 [−0,012 a +0,002] (4 de 10) |

- Con el `D` de las etiquetas, los aumentos se comen la pérdida: de perder a empatar.
- Con el `D` propio no cambian nada, y una celda queda por debajo de −0,005.

Decisión y por qué: **la ronda se cierra en el paso A,** con la regla escrita antes (pedía no perder más de 0,005 en
ninguna celda). No se entrena K2r ni se prueban otros aumentos. K2 se queda como está, apagado y con su aviso.

Lectura [inferencia]: parecerse a un tracking automático por fuera (menos jugadores, 10 Hz, ruido) quita la mitad del
problema. La otra mitad no está en cómo se ven los datos: SkillCorner etiqueta la posesión a su manera, y eso no lo
arregla ningún aumento. Para el partido vale lo mismo: lo que falta no es solo que el ATD se parezca a los datos de
entrenamiento, sino saber qué regla usa su tracking corregido. Es la pregunta a la organización
(`validation/conjunto/pregunta_organizacion.md`).

Descartado: probar los aumentos uno a uno o con otros valores (la regla lo excluía); abrir el examen.

Estado: cerrada. `entrenar.ROBUSTO` queda en el código, apagado por defecto (`--robusto`).

### 2026-11-17 · candidatos · modelo conjunto: K2 pasa el punto 4 en el partido (C0 a C6); encenderlo sigue siendo una decisión del equipo

Quién: Ismael ejecutó los cuatro comandos en el entorno limpio (Python 3.13.9 y numpy 2.5.4, con la rama en `73c3787` y
sin cambios locales) y pegó la salida, que solo lleva agregados. Claude la lee con los criterios escritos antes
(entrada «K2 pasa los puntos 1, 2 y 3», `10c899f`; C2 con la enmienda de las 48 vistas, `8c46846`) y mide C6 con el
scorer oficial, que solo lee las entregas y la GT pública.

Resultado [medido en el partido; solo agregados]:

| criterio | qué pedía | qué ha salido | ¿pasa? |
|---|---|---|---|
| C0, la rama no cambia la entrega | `equipo_v9_rama` con el sha256 de `equipo_v9` | `d9706dfb…be63`, con 201 posesiones, 116 paradas y 0 conflictos | sí |
| C1, es una entrega | válida y con 0 frames en conflicto | `prueba_k2` es válida, con 0 conflictos; sha256 `784e65e5…acbc` | sí |
| C2, el modelo dice en el ATD lo que dice en los abiertos | las seis salidas dentro del rango ensanchado | 0 de 6 fuera. De las 45 entradas, 1 fuera, la que se esperaba: un equipo tiene más de 11 slots en el 13,2 % de los grupos (en los abiertos, del 0,3 al 0,7 %) | sí |
| C3, cambia lo que cabe esperar | como mucho el 12 % de los frames; de un equipo al otro, el 6 %; entre un equipo y `D`, el 6 % | 7.666 de 158.857 frames (4,83 %); 5.181 de un equipo al otro (3,26 %); 2.485 entre un equipo y `D` (1,56 %) | sí |
| C4, no cambia el ritmo ni el `D` | de 185 a 235 posesiones, de 109 a 123 paradas y del 45,2 al 49,2 % de `D` | 203 posesiones (de 16,9 s de media), 115 paradas y el 45,9 % de `D` | sí |
| C5, no fragmenta | ninguna posesión de menos de 12 frames y como mucho 4 de menos de 25 | 0 y 1 | sí |
| C6, no se rompe en la ventana pública | el macroF1 no baja más de 0,03 ni el spellF1 más de 0,10 | macroF1 de 0,8743 a 0,8730; spellF1 de 0,6800 a 0,6800; 13 posesiones las dos; 0 frames de `X` | sí |

Lo que dice además la salida, sin voto:
- **Las seis salidas del modelo caen dentro del rango de la DFL sola,** y dos caen fuera del de SkillCorner (los cambios
  de signo de z por minuto y |z| sin balón). En el partido, z cambia de signo 4,1 veces por minuto (en la DFL, de 3,0 a
  4,6; en SkillCorner, de 5,4 a 8,1), y se ven 10,3 jugadores por equipo (en la DFL, de 10,5 a 11,0; en SkillCorner, de
  7,4 a 8,7).
- **Lo que cambia frente a `equipo_v9` se parece a lo que cambiaba en la DFL,** no en SkillCorner: el 4,8 % de los
  frames (DFL, 4,4–5,3 %; SkillCorner, 7,5–7,9 %), el 1,6 % entre un equipo y `D` (1,2–1,8 % y 4,5–4,6 %) y un 1 % más
  de posesiones (de +0,1 a +2,8 % y de +3,1 a +4,2 %).
- **De qué a qué:** 3.258 frames de `H` a `A` y 1.923 de `A` a `H`; 711 y 302 de un equipo a `D`; 531 y 941 de `D` a un
  equipo. Ninguno a 250 frames o menos del borde de un tramo ni fuera de los tramos.
- **El balón fuera (D7)** no cambia: llegamos tarde en 12 de 47 rachas, como con `equipo_v9`.
- **La ventana pública no elige** (17 posesiones; el propio scorer dice que por debajo de 0,42 todo es ruido): que salga
  igual solo dice que no se ha roto nada.

Decisión y por qué:
- **K2 ha cumplido su regla entera,** los cuatro puntos, con todo escrito antes de medir.
- **No se enciende aquí.** La lectura de la comprobación del proveedor, también escrita antes, no cambia: fuera de los
  proveedores que ha visto, el harness no respalda a K2, así que encenderlo es una apuesta y la decide el equipo.
  `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega (`equipo_v9`) siguen igual.
- **Lo que el punto 4 añade a la apuesta** [inferencia, sobre lo medido]: no hay ninguna señal en contra. Para el
  modelo, el partido se parece a la DFL: sus seis salidas caen dentro del rango de la DFL sola, y lo que cambia frente a
  `equipo_v9` es lo que cambiaba allí. La DFL es el proveedor que más se parece al ATD por fuera (se ve a casi todos
  los jugadores) y donde K2 más gana. Eso dice que el ATD no le resulta raro al modelo, no que acierte en él: sigue sin
  haber un solo partido del ATD con etiquetas.
- **Corregido el mismo día:** la primera versión de esta entrada contaba además a favor que la «alarma» de C2 se había
  quedado callada. No vale como prueba: C2 mide si el partido se parece a un proveedor conocido, no si el modelo falla
  (corrección en la entrada de las comprobaciones, punto 6).

Si el equipo decide encenderlo:
- `pipeline.PIECES["candidates"]` pasa a `"aprendida.evidence_k2"`; la rama se junta en `main`; y la entrega se regenera
  con `python -m possession.pipeline`. Tiene que salir byte a byte igual que `prueba_k2` (`784e65e5…acbc`), porque son
  las mismas piezas.
- **Hay que reproducirla en otra máquina antes de entregar.** `possession/conjunto.py` es código numérico nuevo. Está
  escrito para dar lo mismo bit a bit (sin exponenciales, sin BLAS y sin `np.interp`), pero solo se ha ejecutado en la
  máquina de Ismael.
- El documento técnico tiene que contar K2: los datos de entrenamiento (los 7 partidos de la DFL de Bassek et al., 2025,
  CC BY 4.0, y los 10 de entrenamiento de SkillCorner, MIT), las etiquetas (control en la DFL y las de SkillCorner), que
  se entrenó con torch en una GPU y que la entrega solo usa los pesos, en numpy.

Descartado: decidir con la ventana pública; añadir más comprobaciones sin etiquetas (la que había ya ha contestado).

Estado: K2 apagado, con su regla cumplida. Pendiente de que el equipo decida si lo enciende.

### 2026-11-17 · balón · la detección del balón del vídeo en el partido entero confirma el sondeo; la línea sigue parada

Quién: la ejecutó Ismael en su Windows (CPU, 1,87 h; commit `b9876e6` de `exp/balon-video`, sin cambios locales). Lo
apunta la sesión planificadora (Claude). Solo agregados.

Resultado [medido, agregados del partido]:
- 91.838 frames con balón del ATD en los tramos con juego; 233.298 detecciones, 2,54 por frame. El 97,5 % de los
  frames tiene alguna.
- Condición 1: el 78,0 % de los frames tiene una detección a 3 m o menos (en el sondeo, 78,9 %). Condición 2: el
  42,0 % de las detecciones está a más de 5 m (en el sondeo, 40,7 %). Sale lo mismo que en la muestra.
- La detección más cercana al balón del ATD está a 1,33 m de mediana (p75 2,54 m; p95 6,84 m). Las que elige la capa
  tienen una confianza de 0,80 de mediana; todas juntas, de 0,58.
- Con la selección de la capa: 43,7 toques por minuto, frente a 2,4 con el balón del ATD, y 17,4 de ruido, frente a
  2,9. Temblor de 0,049 m y racha media de fallos de 7,4 frames.
- El desfase con el balón del ATD que mejor cuadra es 0 frames en las dos partes, no los 4 esperados.
- Puerta 2.1 leída con estas cifras: celda p = 0,7, σ = 0,03 y L = 12. Pasa con el `D` de las etiquetas («sin
  decidir») y no pasa con el `D` propio.
- Huella de la caché: `8cda6bf2d85dbe6ff88fbc2e6279fbc1c769dc5e471d10a6267c72a61612fd71`.

Decisión: no cambia nada. La línea sigue parada (16/11) y la capa no entra: con el `D` propio no pasa su regla. La
caché queda en la carpeta de datos de Ismael; si alguien retoma el balón como trayectoria, no hace falta volver a
detectar.

Lectura [inferencia]: el detector ve el balón en la mayoría de los frames. Si las 2,5 detecciones por frame fueran
todas falsas y repartidas por el recorte, la más cercana estaría a unos 3,5 m de mediana, no a 1,33 m. Lo que sobra
son detecciones falsas, de poca confianza.

### 2026-11-17 · candidatos · B11 y B12, modelos de secuencia para la evidencia de equipo (candidatos y regla, antes de medir)

Quién: lo pidió Ismael el 16/11 por la noche («deberiamos probar modelos mas potentes [...] Vamos a intentar lo que
sea»), a través de la sesión planificadora. Lo escribe Claude en la rama `claude/serene-lumiere-16245d` antes de
entrenar ni medir nada. Lo único que se ha ejecutado antes es una prueba de velocidad con datos inventados, para fijar
los pasos de entrenamiento.

Qué se prueba: si un modelo que mira la secuencia, con una ventana hacia atrás y otra hacia delante (etiquetamos en
diferido), encuentra los cambios de posesión que B5 no ve. B5 es una regresión logística por frame.

No repite lo cerrado. La red de una capa (fase 3, 15/11) y B6–B9 miraban los rasgos de un frame, ya promediados en
ventanas fijas. Aquí el modelo recibe los canales de cada frame sin promediar y aprende sus propios filtros en el
tiempo. B5 no se toca.

**Lo común a los dos candidatos:**
- **Canales por frame** (`possession/secuencia.py`, `canales`), calculados por tramo evaluado y a cero fuera:
  - **9 impares** (local menos visitante; cambian de signo si se cambian los equipos):
    - los 5 de proximidad al balón de B1 en ventana 1: el signo del más cercano, los núcleos de 1, 2,5 y 6 m y la
      distancia del más cercano con tope;
    - el juego en la dirección de ataque;
    - el balón en la dirección de ataque, en ventana 1;
    - la velocidad de los jugadores en la dirección de ataque y la diferencia de dispersión, las dos sin promediar (las
      series de `aprendida._rasgos_forma` antes de sus medias).
  - **3 pares** (no cambian si se cambian los equipos):
    - balón visible (0 o 1);
    - la distancia al jugador más cercano de cualquiera de los dos equipos, con tope de 15 m (15 sin balón);
    - la velocidad del balón en m/s, por diferencia centrada de ±1 frame, con tope de 40 (0 sin balón).
  - Cada canal se divide por su raíz cuadrática media en los frames de entrenamiento del pliegue, que se guarda con
    los pesos.
- **Antisimetría exacta:** z = ½·(g(impares, pares) − g(−impares, pares)). Si se cambian los equipos, z cambia de
  signo. Los canales pares solo los puede usar así; una lineal impar como B5, no.
- **Puntuación, como B5:** el modelo solo da el logit z, y se puntúa con `aprendida.puntuacion_de("b5", z, visible, α,
  cercano)`: −α·|z| al equipo que pierde y el +1 de N1 donde se ve el balón. Frente al `D`, empuja como B5.
- **Etiquetas y pérdida, como B5:**
  - solo cuentan los frames vivos en los que el flag y control coinciden (`H` = 1, `A` = 0);
  - entropía cruzada sobre el logit;
  - el resto de frames entra como contexto, pero no en la pérdida;
  - así ningún candidato es una apuesta de convención.
- **Datos: solo la DFL.** Cada partido entra con el balón de las dos condiciones que votan (`dfl.tracking_de`: «como el
  ATD» y «como el ATD, sin bloques»), como dos ejemplos.
  - SkillCorner no se usa para entrenar. Así su mitad de entrenamiento queda fuera de muestra para el modelo de los 7.
- **Pliegues:** 8 por candidato, uno sin cada partido de la DFL (el harness, con `dejar_fuera`) y el de los 7 (la
  entrega y SkillCorner).
- **Entrenamiento:**
  - torch 2.15 en CPU (`mtah2027-balon`), float32 y un hilo;
  - semilla 20261117 más el índice del pliegue;
  - AdamW con decaimiento 1e-4 y un número de pasos fijo;
  - sin parada temprana ni validación: nada se elige mirando el partido que queda fuera.
- **α** se elige de (1/16, 1/8, 1/4, 1/2, 1, 2, 4, 8) como la de B5 (`entrenar.elegir_alfa_d_propio`):
  - la que da más `spellF1` medio con las dos convenciones y las dos condiciones que votan, en los 6 partidos de
    entrenamiento del pliegue;
  - con la pieza de `D` de `main` dentro, sin oráculo, y con el decodificador de `main` (`decode_cortas_a_d`, coste
    25);
  - si empatan, la más pequeña.
  - Es dentro de muestra, como en B5. Una red puede dar logits más afilados en los partidos que vio, así que se enseña,
    como descripción, el acierto por frame dentro y fuera del pliegue.
- **La predicción de la entrega:**
  - va en numpy puro, en float64 y sin BLAS: sumas canal a canal en orden fijo, como `aprendida.logit`;
  - los pesos van en `possession/secuencia_pesos.npz`;
  - los envoltorios son `aprendida.evidence_b11` y `aprendida.evidence_b12`, como B6–B9, y quedan apagados;
  - se comprueba que da lo mismo que torch (con tolerancia, porque torch va en float32) y que la fila `{}` del harness
    no cambia. La prueba sin datos va en `validation/scripts/prueba_secuencia.py`.

**B11, convolucional temporal:**
- entrada 1×1 de 12 a 24 canales;
- 7 bloques residuales `h + conv(ReLU(h))`, con núcleo 3 y dilaciones 1, 2, 4, …, 64;
- ReLU y salida 1×1;
- unos 12.600 pesos;
- ve ±127 frames (±5,1 s), con ceros fuera del tramo;
- se entrena con trozos de 1.536 frames, 16 por paso, sorteados con semilla fija. Los 128 frames de cada borde del
  trozo no cuentan en la pérdida;
- 1.500 pasos, con tasa 1e-3.

**B12, GRU bidireccional:**
- los canales, en medias de 5 frames (5 Hz, por tramo);
- una GRU de 16 en cada sentido y una salida lineal de 32 a 1;
- z vuelve a 25 Hz por interpolación lineal entre los centros de los grupos;
- unos 2.900 pesos;
- se entrena con las partes enteras, que es lo que verá en la predicción: 24 secuencias por pliegue, todas en cada paso;
- 250 pasos, con tasa 3e-3;
- **si a las 04:00 del 17/11 no ha terminado de entrenar, se cierra sin medir.**

**Regla de entrada.** Es la del «límite de daño» del 16/11, tal cual, frente a `main` (`{}`), para cada candidato:
1. **DFL con control:** +0,005 o más en las dos condiciones del balón que votan, ganando en 6 de 7 partidos en cada
   una, con el `D` de las etiquetas y con el `D` propio.
2. **SkillCorner** (solo si pasan 1 y 3):
   - **mitad de entrenamiento** (`lector.ENTRENAMIENTO`, con el modelo de los 7): +0,005 o más con los 10 partidos
     juntos y ganando en 7 de 10, en las cuatro celdas («detectado» y «detectado, suavizado», con el `D` de las
     etiquetas y con el propio), como el detector de cambios del 16/11. El intervalo se enseña, pero no decide;
   - **solo entonces** se avisa a la planificadora antes de abrir el examen (`lector.EXAMEN`). Se abre una vez, para
     un solo candidato, con el mismo umbral: +0,005 o más y 7 de 10, en las cuatro celdas.
3. **DFL con el flag:** no pierde más de 0,005 en ninguna celda (condición que vota × modo del `D`). Si además gana con
   el flag, se dice: es lo que más convence.
4. **Entrega de prueba** frente a `equipo_v9`, con los criterios de daño escritos antes de generarla.

- **Un único candidato llega al examen.** Si pasan los dos, el que más gana con control en la DFL (media de las cuatro
  celdas); si empatan, B11.
- **Si ninguno pasa en abierto, se cierra y se apunta,** sin probar más variantes.

Cómo se mide:
- **DFL:** `validation/harness/puntuar.py --versiones validation/harness/versiones/b11_secuencia_2026-11-17.json`, con
  `--d oraculo` y con `--d propio`, y bootstrap de 1.000.
- **SkillCorner:** `validation/secuencia/skillcorner.py`. `main` es la entrega de hoy: B5, `dead_state` y
  `decode_cortas_a_d`.
- Siempre se enseñan las posesiones predichas frente a las reales.

Avisado antes de medir:
- **Los precedentes:** la red de una capa y el detector de cambios encontraron más posesiones, ganaron con el flag,
  empataron con control y perdieron o empataron en SkillCorner. Si sale el mismo patrón, la regla lo cierra.
- **Circularidad:** las etiquetas de control salen de una regla de proximidad, y los canales son de proximidad. El
  número con control puede salir inflado; por eso deciden también el flag (como límite) y SkillCorner.
- **α dentro de muestra:** si la red se sobreajusta, α sale demasiado grande para el partido que no vio. Eso juega en
  contra del candidato, no a favor.

Estado: escrita antes de entrenar ni medir. El resultado va en la entrada siguiente.

### 2026-11-17 · candidatos · B11 y B12: resultado de la medida

Quién: Claude, en la rama `claude/serene-lumiere-16245d`, con la regla y los candidatos ya commiteados (`6c4176c`). Son
datos abiertos: lo ejecutó Claude, sin tocar el partido.

Cómo se midió:
- **Entrenamiento:** `validation/secuencia/exportar.py`, `entrenar_red.py` y `juntar.py`, como se fijó en la entrada
  anterior.
  - Un cambio de implementación antes de medir nada, que no cambia el modelo: la GRU bidireccional de B12 se escribe
    como dos GRU de un sentido, la de atrás sobre cada parte invertida, sin `pack_padded_sequence`, cuyo paso hacia
    atrás era lentísimo en CPU. Su gradiente se suma en dos mitades del lote, para que quepan 4 pliegues en 16 GB.
- **DFL:** `validation/harness/puntuar.py`, con `main` y B11 (las versiones del fichero commiteado sin B12, que aún
  entrenaba), con `--d oraculo` y `--d propio`, bootstrap de 1.000 y `--eventos` (descriptivo).
  - Código en `90952d0`, con los pesos de B11 que se commitearon después en `de770f4` (el mismo fichero, sha256
    `c148da19…0e18`).
  - Salidas en `validation/secuencia/salidas/2026-11-17_*`.
- **`main` repite el harness:** 0,498 / 0,512 con el flag y 0,728 / 0,748 con control, con el `D` de las etiquetas;
  0,414 / 0,431 y 0,623 / 0,651 con el propio.
- **SkillCorner:** `validation/secuencia/skillcorner.py --candidatos b11`, en la mitad de entrenamiento.
  - **Diferencia con la regla:** la regla decía «solo si pasan 1 y 3», y el encargo de la planificadora pedía medir
    `ENTRENAMIENTO` en todo caso. Se midió después de saber que B11 no pasaba el punto 1. No decide nada: B11 ya estaba
    cerrado. Se leyó con el umbral escrito antes. El examen no se abrió.

**B11, resultado [medido], frente a `main`** (diferencia [5–95 %], en cuántos de 7 gana):

| convención | `D` | «como el ATD» | «como el ATD, sin bloques» |
|---|---|---|---|
| control | de las etiquetas | +0,012 [−0,001 a +0,026], 4 de 7 | +0,007 [−0,006 a +0,020], 4 de 7 |
| control | propio | +0,023 [+0,011 a +0,037], 5 de 7 | +0,014 [+0,001 a +0,027], 5 de 7 |
| flag | de las etiquetas | +0,104 [+0,093 a +0,116], 7 de 7 | +0,108 [+0,097 a +0,120], 7 de 7 |
| flag | propio | +0,097 [+0,087 a +0,109], 7 de 7 | +0,101 [+0,090 a +0,112], 7 de 7 |

- **Posesiones predichas** (`D` de las etiquetas, «como el ATD»): 1.989, frente a 1.661 de `main`. Las reales son 1.736
  con control y 3.061 con el flag.
- **SkillCorner, `ENTRENAMIENTO`** (10 partidos, modelo de los 7, frente a `main`):

  | `D` | «detectado» | «detectado, suavizado» |
  |---|---|---|
  | de las etiquetas | −0,012 [−0,020 a −0,004], 4 de 10 | −0,009 [−0,017 a −0,001], 4 de 10 |
  | propio | +0,000 [−0,007 a +0,008], 4 de 10 | +0,001 [−0,007 a +0,008], 5 de 10 |

  Predice 2.655 posesiones frente a 2.270 de `main` (las reales son 3.228), pero no son las buenas. Ninguna de las
  cuatro celdas cumple: «no pasa».
- **Eventos humanos** («como el ATD», frente a `main`, descriptivo): recuperaciones +11,8 puntos [+6,7 a +16,9], duelos
  con cambio +9,6 [+5,2 a +14,0] y duelos sin cambio −10,0 [−14,7 a −4,7]: un **compromiso**. Frente al control,
  «mejora».
- **Descriptivo:**
  - acierto por frame en el partido que no vio, del 92,2 al 95,5 % (del 94,6 al 95,5 % dentro del pliegue);
  - α de 2 a 8 (el pliegue sin J03WN1 cae en el borde de la rejilla, 8);
  - numpy frente a torch: diferencia máxima de z de 4·10⁻⁶, sin ningún signo distinto, en los 8 pliegues.

**Veredicto de B11, con la regla escrita antes: no pasa.**
- **Punto 1, DFL con control: no pasa.** Supera el +0,005 en las cuatro celdas, pero gana en 4 o 5 partidos de 7, y se
  pedían 6.
- **Punto 3, DFL con el flag: pasa, y gana mucho:** +0,10 en las cuatro celdas, 7 de 7. Es la mayor ganancia con el
  flag medida hasta ahora.
- **SkillCorner,** medido fuera de la regla: pierde con el `D` de las etiquetas y empata con el propio.
- Ninguna regla vigente lo admite. El límite de daño falla por el «6 de 7», y §5.8 por no llegar a +0,03 con control.

Lectura [inferencia]: es el patrón de la red de una capa y del detector de cambios, más marcado. B11 encuentra muchos
más cambios de equipo (recuperaciones y duelos con cambio), y eso le hace ganar mucho con el flag. Pero también cambia
cuando no debe (duelos sin cambio), y con un tracking de otro proveedor esas posesiones de más no aciertan. Las
etiquetas de control y SkillCorner, que exigen control, no ven la mejora.

**B12: cómo se midió.**
- Terminó de entrenar a tiempo: el último pliegue, a las 03:58 (el plazo era a las 04:00).
- La medida es la oficial: el harness con el fichero de versiones commiteado, desde un árbol limpio (código `bfc9566`,
  sin cambios) y con los pesos de los dos modelos (sha256 `ba31988a…db76`).
- Las cifras de B11 salen iguales que arriba.
- SkillCorner, otra vez con `--candidatos b11 b12`, también fuera del orden de la regla, como en B11.
- Salidas en `validation/secuencia/salidas/2026-11-17_*oficial*`, con la tabla por partido en
  `..._harness_oficial_por_partido.md`.

**B12, resultado [medido], frente a `main`** (diferencia [5–95 %], en cuántos de 7 gana):

| convención | `D` | «como el ATD» | «como el ATD, sin bloques» |
|---|---|---|---|
| control | de las etiquetas | +0,034 [+0,022 a +0,046], 7 de 7 | +0,028 [+0,016 a +0,039], **5 de 7** |
| control | propio | +0,034 [+0,023 a +0,046], 7 de 7 | +0,028 [+0,017 a +0,039], **5 de 7** |
| flag | de las etiquetas | +0,056 [+0,046 a +0,066], 7 de 7 | +0,061 [+0,051 a +0,071], 7 de 7 |
| flag | propio | +0,046 [+0,038 a +0,055], 7 de 7 | +0,053 [+0,044 a +0,062], 7 de 7 |

- **Por partido, con control y «sin bloques»,** pierde en J03WPY (−0,006 con el `D` de las etiquetas, −0,000 con el
  propio) y en J03WQQ (−0,025 y −0,004).
- **Posesiones predichas** (`D` de las etiquetas, «como el ATD»): 1.774, frente a 1.661 de `main`. Las reales son 1.736
  con control y 3.061 con el flag.
- **SkillCorner, `ENTRENAMIENTO`** (frente a `main`, umbral escrito antes: +0,005 y 7 de 10):

  | `D` | «detectado» | «detectado, suavizado» |
  |---|---|---|
  | de las etiquetas | +0,011 [+0,004 a +0,018], 7 de 10 | +0,014 [+0,006 a +0,021], 7 de 10 |
  | propio | +0,012 [+0,005 a +0,019], 9 de 10 | +0,014 [+0,007 a +0,022], 9 de 10 |

  Cumple las cuatro celdas. Predice 2.465 posesiones frente a 2.270 de `main` (las reales son 3.228).
- **Eventos humanos** («como el ATD», frente a `main`, descriptivo): recuperaciones +9,2 puntos [+5,1 a +13,3], duelos
  con cambio +8,7 [+5,2 a +12,7] y duelos sin cambio −6,2 [−10,4 a −1,4]: un **compromiso**, más suave que el de B11.
- **Cuánto cambia la salida frente a `main`** (descriptivo, con el `D` propio;
  `validation/secuencia/cambios_frente_a_main.py`):
  - con otra etiqueta, el 3,8–4,1 % de los frames en la DFL y el 6,4–6,7 % en SkillCorner;
  - entran o salen de `D` el 1,1 % en la DFL y el 3,8 % en SkillCorner, pero el `D` total se mueve 0,4 puntos como
    mucho y las paradas casi no cambian;
  - las posesiones suben un 4–6 % en la DFL y un 9–10 % en SkillCorner;
  - hay menos posesiones de menos de 25 frames que con `main`.
- **Con los jugadores degradados como los del ATD** (descriptivo):
  - medido con `validation/apuesta_b/jugadores.py --versiones` y el fichero de hoy, con el `D` de las etiquetas, en
    las tres variantes del 14/11, que salen sin voto; salida en `..._jugadores_como_el_atd.md`;
  - frente a `main`, B12 sigue ganando: con control de +0,017 a +0,041 (5 a 7 de 7) y con el flag de +0,049 a
    +0,061 (7 de 7);
  - B11, con control, pierde en dos de las tres variantes (de −0,010 a −0,039).
- **Descriptivo:**
  - acierto por frame en el partido que no vio, del 91,2 al 94,4 %;
  - α = 8 en los 8 pliegues, el borde de la rejilla fijada;
  - numpy frente a torch: diferencia máxima de z de 2,4·10⁻⁵ en la DFL, sin ningún signo distinto.

**Veredicto de B12, con la regla escrita antes: no pasa.**
- **Punto 1, DFL con control: no pasa.** Gana entre +0,028 y +0,034 en las cuatro celdas, con el intervalo por encima
  de cero, pero en «sin bloques» gana en 5 de 7 partidos con los dos modos del `D`, y se pedían 6.
- **Punto 3, DFL con el flag: pasa, y gana:** +0,046 a +0,061, 7 de 7.
- **SkillCorner, `ENTRENAMIENTO`:** cumpliría las cuatro celdas, pero se midió fuera del orden de la regla y no la
  rescata.
- **§5.8 frente a `main`:** tampoco pasa (+0,028 con control en «sin bloques», por debajo de +0,03).
- **El examen de SkillCorner no se abre:** la regla solo lo abre si pasan los puntos 1 y 3.

Lectura [inferencia]:
- B12 es el primer candidato de la evidencia de equipo que gana con las dos convenciones en la DFL y, además, en
  SkillCorner. Se queda fuera por dos partidos con pérdidas pequeñas en una condición.
- B11 encuentra más cambios, pero muchos falsos (1.989 posesiones). B12 añade menos (1.774) y acierta más.
- B12 saca más que B11. Con lo medido no se puede decir por qué: entre los dos cambian a la vez la memoria, los 5 Hz y
  α.

**Decisión: con la regla escrita antes, B11 y B12 se cierran y quedan apagados** (`aprendida.evidence_b11` y
`evidence_b12`). `pipeline.PIECES` y la entrega no cambian. No se prueban más variantes.

**Lo que queda abierto, para Ismael (no lo decide esta sesión):** una excepción para B12, como la de `ball_out` del
16/11.
- **A favor:** gana con control en las cuatro celdas de la DFL (+0,028 a +0,034, con el intervalo por encima de cero),
  con el flag en todas (7 de 7) y en SkillCorner, que es otro proveedor y exige control.
- **En contra:**
  - falla el «6 de 7» que se escribió antes de medir;
  - α cae en el borde de la rejilla;
  - el harness no degrada a los jugadores, y B12 usa sus canales sin promediar. Con los jugadores como los del ATD
    aguanta (arriba), pero esas variantes no votan: el ATD tiene además slots duplicados que no se imitan;
  - su recurrencia usa `np.exp` y `np.tanh` en 14.000 pasos por parte. La puntuación va redondeada a 6 decimales, pero
    si entra hay que reproducir la entrega una vez en otra máquina antes de entregar;
  - **puntúa el doble de fuerte que B5:** la media de |H − A| en la DFL es 25,6 frente a 13,1 (cociente 1,95–1,96;
    `cambios_frente_a_main.py b12 --escala`). La capa de los contraataques, que suma 8 y se pesó con la escala de B5,
    pesaría la mitad. El `D` no se ve afectado: frente a `D`, B12 empuja como B5.
- **Si la decide, el orden es este:**
  1. Se avisa a la planificadora y se abre el examen de SkillCorner una vez, para B12, con el umbral escrito arriba
     (+0,005 o más y 7 de 10, en las cuatro celdas). Son datos abiertos: lo puede ejecutar Claude.

         python validation/secuencia/skillcorner.py --examen b12 --confirmo-el-unico-uso

     El uso se apunta en `validation/skillcorner/BITACORA.md` («Usos del examen») y aquí.
  2. Si el examen pasa, Ismael genera la entrega de prueba con el python del entorno limpio.
     - Se ejecuta desde la carpeta de esta rama (el worktree `.claude/worktrees/musing-roentgen-2874e5`).
     - Con `--contra`, la ruta de `equipo_v9.csv` en su carpeta, porque las entregas no van en git:

           C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe validation/partido/probar_entrega.py prueba_b12 --pieza candidates=aprendida.evidence_b12 --contra C:\dev\mtah2027-piso2nyc\evaluation\results\equipo_v9.csv

     - Comprobado sin datos con ese python (3.13.9, numpy 2.5.4): la pieza se resuelve, carga los pesos y da lo mismo
       dos veces.

  3. Encenderla (`pipeline.PIECES["candidates"]`) es otra decisión, con la entrega regenerada y validada.

**Criterios de daño de esa entrega de prueba frente a `equipo_v9`.** Se escriben antes de generarla y solo valen si hay
excepción y el examen pasa. Las bandas salen de lo que B12 cambia en abierto (arriba). Si falla uno, B12 no entra, diga
lo que diga el examen:
1. 0 frames con piezas en conflicto (si no, el pipeline no escribe el CSV).
2. Ninguna posesión de menos de 25 frames en los dos tramos, como `equipo_v9`. En abierto, B12 da menos que `main`.
3. **El `D` casi no se mueve:**
   - el `D` de los frames evaluados, a 0,5 puntos o menos del 46,2 % de `equipo_v9`;
   - entre 111 y 121 paradas (116 en `equipo_v9`);
   - los frames que entran o salen de `D` (en `comparar_entregas.py`), como mucho el 6 % de los evaluados, unos 9.500.
     En abierto, del 1,1 al 3,8 %; el tope es el máximo más la mitad.
4. **Posesiones:** entre 197 y 227 (201 en `equipo_v9`, de −2 a +13 %). En abierto suben de un 4 a un 10 %.
5. **Frames con otra etiqueta:** como mucho el 10 % de los evaluados, unos 15.900. En abierto, del 3,8 al 6,7 %.
6. **Balón fuera** (`balon_fuera.py`): no más de 2 rachas «tarde» más que `equipo_v9` con el mismo script (el de
   `equipo_v9` sale de `python validation/partido/balon_fuera.py --entrega equipo_v9`).
7. El validador, en verde.

**Desviaciones del plan escrito antes:**
- SkillCorner se midió para los dos fuera del orden de la regla, como pedía el encargo. No rescata a ninguno.
- B12 tuvo dos cambios de implementación antes de medir nada: dos GRU de un sentido en lugar de `pack_padded_sequence`,
  y el gradiente sumado en dos mitades. Es el mismo modelo y el mismo gradiente, salvo el redondeo.
- B12 terminó de entrenar 90 s antes del plazo que se fijó.

**La entrega no cambia:**
- B11 y B12 están fuera de `pipeline.PIECES`;
- la fila de `main` del harness repite sus números de siempre;
- `prueba_aprendida.py`, `prueba_pipeline.py`, `prueba_harness.py` y `prueba_secuencia.py` dan todo bien.

No se ha regenerado.

Estado: B11 y B12 cerrados por la regla y apagados. La excepción de B12 queda pendiente de Ismael.

### 2026-11-17 · candidatos · segunda ronda: B13, una red sobre las trayectorias (se prueba)

Ismael, a través de la planificadora: sin plazos, y si una ronda no pasa, se prueba otra. Regla: la del límite de daño
del 16/11, frente a `main`. B13 (`possession/trayectorias.py`, apagada):
- cada equipo se codifica desde su dirección de ataque, con un codificador de conjuntos de todos sus jugadores y los
  rivales, y el balón;
- encima, una GRU bidireccional a 5 Hz, antisimétrica;
- se entrena en la DFL con el balón de las dos condiciones que votan y también sin balón a trozos.

Se mide en el harness con `validation/harness/versiones/b13_trayectorias_2026-11-17.json`.

B14 (`possession/trayectorias2.py`, apagada) es B13 con tres cambios:
- rasgos de control por jugador: núcleos de 1 y 3 m, co-movimiento y acercamiento al balón;
- atención conjunta sobre los dos equipos;
- entrenada con dominio aleatorizado como el ATD (`exportar2.py`): dos copias más de cada partido, con jugadores
  degradados, tracklets cortados, slots fantasma y el balón con otra semilla y de 0 a 6 frames tarde, y espejo en y.

Se mide igual, frente a `main`.

**B13, medido [harness, `ad6dd9f`; salidas en `validation/secuencia/salidas/2026-11-17_harness_b13_*`]:** frente a `main`,
con el flag +0,094 / +0,093 (7 de 7) y con control +0,021 (6 de 7) / +0,003 (4 de 7) con el `D` de las etiquetas, y
+0,025 (5 de 7) / +0,007 (3 de 7) con el propio. No pasa el punto 1 y queda por debajo de B12 con control. Predice
1.865 posesiones (`main` 1.661, B12 1.774; las reales son 1.736 con control). Es el patrón de B11: encuentra más cambios,
pero muchos sobran.

B15 (se prueba; `aprendida.evidence_b15`, apagada) es la red de B14 entrenada con la etiqueta de control en todos los
frames vivos, no solo donde el flag y control coinciden.
- Por qué: B11 y B13 cambian de equipo de más. Nunca vieron en la pérdida los toques breves del rival (del 5 al 9 % de
  los vivos), y ahí cambian.
- Es una apuesta de convención declarada («exigir control», 12/11). Como las etiquetas de control salen de una regla de
  proximidad, el número con control sale favorecido. Pesan el flag (como límite) y SkillCorner.

**B13 en SkillCorner `ENTRENAMIENTO`** (descriptivo, `..._skillcorner_entrenamiento_b13.md`): pierde en las cuatro celdas
frente a `main`, de −0,010 a −0,024 (de 1 a 4 de 10). **B13 se cierra.**

### 2026-11-17 · candidatos · excepción para B12: se abre el examen de SkillCorner (decisión de Ismael)

Quién: Ismael (17/11, 10:20): «si puedes lánzalo y si ves que está todo ok mergea la branch con B12». Lo ejecuta Claude,
en la sesión de Ismael del ordenador del trabajo. Escrita antes de abrir el examen.

Qué se decide: la excepción que dejaba abierta la entrada «B11 y B12: resultado de la medida».
- **El examen:** se abre `lector.EXAMEN` de SkillCorner una sola vez, para B12, con el umbral escrito en esa entrada:
  +0,005 o más y ganar en 7 de 10, en las cuatro celdas (`D` de las etiquetas y propio, «detectado» y «detectado,
  suavizado»). Comando: `python validation/secuencia/skillcorner.py --examen b12 --confirmo-el-unico-uso`. El uso se
  apunta en `validation/skillcorner/BITACORA.md` («Usos del examen»).
- **Si pasa:** B12 entra en `main`, **apagado**. Encenderlo (`pipeline.PIECES["candidates"]`) sigue los pasos de esa
  entrada: una persona con los datos genera la entrega de prueba frente a `equipo_v9`, se lee con sus siete criterios de
  daño, y después se regenera, se valida y se reproduce en otra máquina.
- **Si no pasa:** B12 se queda cerrado y apagado, y a `main` va solo el registro.

Por qué: es la tercera excepción a «lo que no ha ganado en el harness no entra», tras los contraataques y el balón
fuera. A diferencia de esas dos, B12 sí se mide en datos abiertos y gana en todo salvo en el «6 de 7» de una celda.

### 2026-11-17 · candidatos · B12, examen de SkillCorner: no pasa; B12 se queda cerrado y apagado

Quién: Claude, en la sesión de Ismael del ordenador del trabajo, con la excepción que decidió Ismael (entrada anterior).
Son datos abiertos.

Cómo se midió:
- **El comando:** `python validation/secuencia/skillcorner.py --examen b12 --confirmo-el-unico-uso`, sobre `lector.EXAMEN`
  (10 partidos).
- **Qué se compara:**
  - `main` es B5, `dead_state` y `decode_cortas_a_d`;
  - B12, con el modelo de los 7 partidos de la DFL;
  - bootstrap pareado de 1.000.
- **Con qué pesos:** desde una copia con los pesos de B12 escritos como números (`possession/secuencia_pesos.py`), que se
  comprobó que son idénticos bit a bit a los medidos (sha256 de la fuente `ba31988a…db76`).

**Resultado [medido]:**

| `D` | condición | `main` | B12 | frente a `main` [5–95 %] | gana en |
|---|---|---|---|---|---|
| de las etiquetas | «detectado» | 0,509 | 0,513 | +0,004 [−0,003 a +0,012] | 6 de 10 |
| de las etiquetas | «detectado, suavizado» | 0,504 | 0,510 | +0,007 [−0,001 a +0,015] | 7 de 10 |
| propio | «detectado» | 0,389 | 0,394 | +0,006 [−0,001 a +0,013] | 7 de 10 |
| propio | «detectado, suavizado» | 0,384 | 0,394 | +0,009 [+0,002 a +0,017] | 7 de 10 |

B12 predice más posesiones que `main` (2.512 frente a 2.283, con el `D` de las etiquetas y «detectado»). Las reales son
3.152.

**Con la regla escrita antes** (+0,005 o más y ganar en 7 de 10, en las cuatro celdas): **no pasa.** Cumple tres de las
cuatro celdas. Falla «detectado» con el `D` de las etiquetas: +0,004 y gana en 6 de 10.

**Decisión** (la que se escribió antes de abrir el examen):
- B12 se queda cerrado y apagado;
- a `main` va solo el registro, no el código ni los pesos;
- el examen de SkillCorner queda usado para B12;
- no se prueba ninguna variante de B12.

Lectura [inferencia]:
- En el examen, B12 gana menos que en la mitad de entrenamiento: de +0,004 a +0,009, frente a +0,011 a +0,014. Parte de
  la ventaja era de esa mitad.
- Las cuatro celdas siguen siendo positivas, pero ninguna se aleja del ruido.

Lo que no se hace: buscar otra excepción para B12. Sería buscar hasta que salga.

### 2026-11-17 · temporal · detector de cambios con el balón del ATD, encima de K2 y de `main` (candidatos y regla, antes de medir)

Quién: David (17/11, «haz los 3»), con Claude, en la rama `exp/cambios-sobre-k2`, que sale de `exp/modelo-conjunto`
en `2b187b9`. Escrita antes de medir nada de esta entrada.

Por qué: el balón del vídeo no se puede usar (la línea está parada y su detector se equivoca en el 18 % de los
frames), así que queda la variante «respaldo» del detector de cambios, con el balón del ATD. En la segunda ronda se
quedó cerca (+0,006 a +0,009 con control, 5–6 de 7) frente a un `main` que ya no es el de hoy: entonces decodificaba
con `decode` y hoy con `decode_cortas_a_d`, y puede que la evidencia de equipo pase a ser K2.

Candidatos, con la configuración fija que eligió la segunda ronda (no se elige nada aquí):
- **R1:** reglas con giro de 20°, cambio de velocidad del 60 % y 20 frames de confirmación; capa con γ = 4,
  W = 50, contra el otro equipo; sin rebaja (lo elegido para «D reglas · respaldo» en 6 de 7 pliegues).
- **R2:** las reglas sin afinar (30°, 40 %, 20 frames); γ = 4, W = 100, contra el otro equipo (lo elegido para «C
  reglas · respaldo» en los 7 pliegues).

Cada uno se mide sobre dos bases, con el decodificador de la entrega (`decode_cortas_a_d`):
- **sobre `main`:** B5, la entrega de hoy;
- **sobre K2:** `aprendida.evidence_k2` en lugar de B5, con el pliegue que no vio el partido.

Son cuatro comparaciones: cada candidato frente a su base (no frente a la otra base).

Regla de entrada, la del límite de daño del 16/11 en la DFL (los 7 partidos, «como el ATD» y «sin bloques», con el
`D` de las etiquetas y con el propio):
1. con control, +0,005 o más en las cuatro celdas, ganando en 6 de 7 en cada una;
2. con el flag, no pierde más de 0,005 en ninguna.
Si un candidato pasa sobre una base, sigue a SkillCorner (`validation/cambios/medir_skillcorner.py`, mitad de
entrenamiento; +0,005 y 7 de 10 en las cuatro celdas) y, si pasa, al examen, una sola vez y para un solo candidato, y a
la entrega de prueba. Sobre K2 solo tiene sentido si el equipo enciende K2.

Avisado: son 2 configuraciones elegidas antes, más 14 candidatos de las rondas anteriores; con la regla de 6 de 7 en
cuatro celdas, un candidato que no aporta nada pasaría pocas veces, pero no ninguna.

Estado: medida el 17/11 (entrada siguiente).

### 2026-11-17 · temporal · detector de cambios con el balón del ATD, encima de K2 y de `main`: ninguno pasa; se cierra

Quién: David (17/11), con Claude. Salida: `validation/cambios/salidas/2026-11-17_sobre_k2.md` (`sobre_k2.py`; los 7
partidos de la DFL, con `decode_cortas_a_d`; cada pieza aprendida con el pliegue que no vio el partido).

Comprobación del instrumento [medido]: B5 da 0,728 / 0,498 y K2 0,780 / 0,542 («como el ATD», `D` de las etiquetas),
las mismas cifras que la entrada de K2.

Resultado [medido], diferencia con su base (rango de las cuatro celdas):

| candidato | base | control (gana en) | flag |
|---|---|---|---|
| R1 (20°, 60 %, 20 frames; γ 4, W 50) | `main` (B5) | +0,006 a +0,011 (5, 5, 7 y 6 de 7) | +0,010 a +0,013 |
| R2 (30°, 40 %, 20 frames; γ 4, W 100) | `main` (B5) | +0,004 a +0,013 (5, 4, 6 y 5 de 7) | +0,007 a +0,010 |
| R1 | K2 | +0,002 a +0,008 (4, 5, 4 y 6 de 7) | +0,010 a +0,012 |
| R2 | K2 | +0,005 a +0,008 (4, 4, 6 y 4 de 7) | +0,006 a +0,007 |

Decisión y por qué: **ninguno pasa el punto 1** (todos fallan por el número de partidos; ninguno pierde con el flag).
Con la regla escrita antes, no siguen a SkillCorner y el detector de cambios queda cerrado para esta entrega, con el
balón del ATD y con el del vídeo. `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian.

Lectura [inferencia]: el detector con el balón del ATD aporta algo pequeño y siempre del mismo signo (+0,002 a +0,013,
nunca negativo), pero no gana en suficientes partidos. Encima de K2 aporta menos que encima de B5: K2 ya corrige parte
de los cambios que tarda en ver B5. Es material para el documento técnico y para el Innovation Challenge, junto con el
techo (+0,096 con control).

### 2026-11-17 · candidatos · se enciende K2: `pipeline.PIECES["candidates"]` pasa a `aprendida.evidence_k2`

Quién: David (17/11): «quiero encender yo K2 […] Es la última opción que nos queda para mejorarlo, aunque sea un poco».
Cualquiera del equipo puede decidir (decisión del 15/11). El cambio de código, en la rama `feat/encender-k2` (sale de
`exp/modelo-conjunto` con `main` y `exp/cambios-sobre-k2` juntados).

Qué se enciende: K2, el modelo conjunto (`possession/conjunto.py`, pesos en `possession/conjunto_pesos.npz`), como
evidencia de equipo de la entrega en lugar de B5. El `D` (`dead_state`, `dead_ball`), el decodificador
(`decode_cortas_a_d`) y las capas del partido (`DELIVERY_LAYERS`) no cambian.

Por qué [medido; entradas del 17/11 sobre K2]:
- **Cumplió su regla entera,** los cuatro puntos, con todo escrito antes de medir: DFL con control, de +0,036 a +0,051
  (6–7 de 7); con el flag, de +0,033 a +0,044 (7 de 7); SkillCorner, de +0,021 a +0,024 en entrenamiento y de +0,021 a
  +0,028 en el examen (8–10 de 10); y la entrega de prueba `prueba_k2` pasa los siete criterios de daño (C0 a C6).
- **Es el único candidato de equipo que gana con las dos convenciones y en un examen que no había visto.** B9, B11, B12,
  B13 y el detector de cambios no lo consiguieron.
- **En el partido, el modelo se comporta como en la DFL:** sus salidas caen dentro del rango de la DFL y lo que cambia
  frente a `equipo_v9` (el 4,8 % de los frames) es lo que cambiaba allí.
- **Reproducción:** según David, Ismael la repitió en su máquina y sale la misma huella [sin verificar en el repo]. La
  de David, en otra máquina, sí está medida: entrada siguiente.

El riesgo, que se asume: entrenado con un solo proveedor, K2 pierde en el otro, y el ATD es un tercero. Nada de lo
medido es en el ATD con etiquetas. Es una apuesta con todas las señales medibles a favor y ninguna en contra.

Lo que hay que hacer después del merge:
- regenerar la entrega con el entorno limpio (`python -m possession.pipeline`): tiene que salir byte a byte igual que
  `prueba_k2`, sha256 `784e65e5…acbc`, válida, con 0 conflictos y 203 posesiones; será `equipo_v10`;
- reproducirla en una segunda máquina distinta de la que generó `prueba_k2`, si no se ha hecho ya;
- contar K2 en el documento técnico: los datos de entrenamiento (los 7 partidos de la DFL de Bassek et al., 2025,
  CC BY 4.0, y los 10 de entrenamiento de SkillCorner, MIT), las etiquetas (control en la DFL y las de SkillCorner), que
  se entrenó con torch en una GPU y que la entrega usa solo los pesos, en numpy.

Cambios en las pruebas sin datos: las que comprobaban que la pieza de equipo era B5 (`prueba_pipeline`, `prueba_harness`,
`prueba_balon_fuera`) o que K2 estaba apagado (`prueba_conjunto`) dicen ahora K2. `prueba_pipeline` deja a las piezas
leer, y solo leer, el fichero de pesos de K2, que es parte del código; cualquier otro fichero sigue siendo un error.

El harness: su versión de `main` (`{}`) pasa a ser K2. Quien compare con «main» usando tablas de antes fija `main` en un
commit anterior o vuelve a medir su referencia.

Descartado: dejar B5 (la entrega de hoy, `equipo_v9`), que es lo seguro; se cambia porque K2 gana en todo lo que se ha
podido medir.

### 2026-11-17 · infraestructura · `equipo_v10`, con K2: misma huella que `prueba_k2`, reproducida en la máquina de David

Quién: lo ejecutó David en su Windows, en un entorno limpio creado con `requirements-entrega.txt` (Python 3.13.1 y numpy
2.5.4), con la rama `feat/encender-k2` en `7e0c2cc` y sin cambios locales en el código de la entrega. Pegó solo
agregados.

Resultado [medido, agregados del partido]:
- `python -m possession.pipeline --name equipo_v10`: 0 frames con piezas en conflicto y sha256
  `784e65e5825a7fe52f7fe5f3a51c9f5e1bccf2c9f89a1372b7b344a3f882acbc`, **byte a byte igual que `prueba_k2`**, que
  generó Ismael en su máquina con Python 3.13.9.
- El validador da `Valid`: 199.319 filas, 203 posesiones de 16,9 s de media.

Qué significa: K2 da lo mismo en dos máquinas distintas y con dos versiones de Python 3.13, que era lo que faltaba
antes de entregar con él (`possession/conjunto.py` es código numérico nuevo). **`equipo_v10` es la entrega vigente**
cuando `feat/encender-k2` entre en `main`; hasta entonces, `main` sigue dando `equipo_v9`.

### 2026-11-17 · candidatos · modelo conjunto: dos refinamientos de K2 sin reentrenar, K3 (la mezcla con B5) y K4 (el espejo) (candidatos y regla, antes de medir)

Quién: lo pidió Ismael el 17/11 («seguir profundizando en ese método y refinarlo lo máximo posible»), mientras David
comprueba K2. Lo escribe Claude en la rama `exp/k2-refinar`, que sale de `exp/modelo-conjunto` en `2b187b9`, antes de
medir ningún candidato.

**Lo que no cambia.** `aprendida.evidence_k2`, `possession/conjunto.py`, `conjunto_pesos.npz` y todo lo que hay detrás
de `prueba_k2` (`784e65e5…acbc`) se quedan byte a byte como están: es lo que David comprueba. Los refinamientos van en
un módulo nuevo (`possession/refinamientos.py`), con nombres nuevos, apagados.

**Comprobación previa del instrumento** [medido, 17/11, en el portátil de Ismael, Linux, con numpy 2.5.4]: la tabla
publicada de K2 sale igual, con sus intervalos. En la DFL, 0,728 → 0,780 (+0,051 [+0,040 a +0,064], 7 de 7) y las
otras once celdas; en la mitad de entrenamiento de SkillCorner, 0,519 → 0,543 y las otras tres
(`medir.py --con-la-pieza`).

**Por qué estos dos y no otros:**
- Lo medido dice que lo que cojea en K2 es el cambio de proveedor, no la red. Ya están cerrados la red mayor y más
  pasos (el piloto), K1, el riesgo mínimo, el coste del decodificador con K2, la ronda K2r y el detector de cambios de
  David encima de K2.
- Pulir dentro del proveedor da ruido: los intervalos del harness son de ±0,01 y estos 17 partidos ya han juzgado
  muchos candidatos. Por eso el eje que decide aquí es el del otro proveedor.
- En este portátil no hay GPU. Lo que no reentrena se puede medir hoy, con los pesos de los 8 pliegues que ya están en
  el repo.

**Los candidatos** (fijados; no se elige ningún valor mirando resultados):
- **K3, la mezcla con B5.** El logit de la mezcla es la media a partes iguales del de K2 y del de B5, cada uno en su
  escala (α·z), y se puntúa como B5: −|s| al equipo que pierde y el +1 de N1 donde se ve el balón. B5 es la pieza que
  se traslada de un proveedor a otro y K2 la que gana dentro: si K2 falla en un proveedor nuevo, B5 sigue opinando.
  La parte de K2 es ½ y no se elige: dejando un partido fuera saldría una parte mayor, porque dentro del proveedor K2
  gana a B5, y eso no es lo que la mezcla tiene que asegurar. Con ¼ y con ¾ se enseña sin voto.
- **K4, el espejo.** El logit de K2 promediado con el del mismo tracking con el campo en espejo (y → ancho − y). El
  modelo se entrenó con ese espejo como aumento, pero no es simétrico por construcción (sí lo es al cambiar los
  equipos); el promedio le quita ese ruido. Tarda el doble (unos 10 s por partido).
- **K5,** solo si K3 y K4 pasan los dos: K3 con el logit de K4. Se mide una vez, con la regla de K3.

**Cómo se mide** (`validation/conjunto/refinar.py`; `main`, K2 y el `D` se montan como en `medir.py`):
- **A. Dentro del proveedor,** con los pesos de los 8 pliegues del repo: los 7 partidos de la DFL (K2 y B5, cada uno con
  el pliegue que no vio el partido) y los 10 de `lector.ENTRENAMIENTO` de SkillCorner (K2 con el pliegue cruzado; B5 con
  los coeficientes de la entrega, que nunca vio SkillCorner). **El examen de SkillCorner no se abre:** está gastado
  para K2 y una variante no lo recibe. El script no tiene bandera para leerlo.
- **B. El otro proveedor.** Los pesos de los dos modelos de un solo proveedor del 17/11 están en la máquina de la GPU,
  no en el repo. Aquí se entrenan dos **réplicas** con la misma configuración (`entrenar.py todos --solo dfl` y
  `--solo sc`, con `--dispositivo cpu`): mismo entrenamiento, otros números al azar. Cada una se puntúa en el otro
  proveedor con α = 4, como entonces.
  - **La réplica vale** si K2 con ella repite el problema publicado. La de solo la DFL, en SkillCorner: pierde más de
    0,005 frente a `main` en las dos celdas con el `D` de las etiquetas (publicado: −0,015 y −0,010). La de solo
    SkillCorner, en la DFL con control: pierde más de 0,03 en las cuatro celdas (publicado: de −0,045 a −0,096). Si
    una réplica no vale, ese sentido no se puede leer y se dice.
  - **El sentido que decide es el de la DFL a SkillCorner:** de un tracking limpio a uno automático, como del
    entrenamiento al partido, y con las dos mitades de la mezcla fuera de su proveedor (ni esa K2 ni B5 vieron
    SkillCorner). En el otro sentido, B5 sí ha visto la DFL (va con el pliegue que no vio el partido), así que
    favorece a la mezcla: se enseña sin voto.
- **C. Metrica** (los 3 partidos de sample-data, bajados del commit que cita `validation/metrica/BITACORA.md`), con los
  pesos de la entrega de K2 y de B5. Ninguno vio ese proveedor: es lo más parecido que hay a lo que le pasará a la
  entrega. Son 3 partidos, con sus avisos de siempre (etiquetas de eventos y balón pegado al jugador).

**Regla de K3:**
1. **Dentro (A), frente a `main`,** el límite de daño del 16/11, como K2: en la DFL, +0,005 o más con control en las
   cuatro celdas ganando en 6 de 7, y sin perder más de 0,005 con el flag ni con el balón a la vista en los `D`; en
   SkillCorner, +0,005 o más y 7 de 10 en las cuatro celdas.
2. **El otro proveedor (B), de la DFL a SkillCorner, frente a `main`:** «quita la pérdida» si queda en −0,005 o más en
   las cuatro celdas.
3. **Metrica (C), frente a `main`:** no pierde más de 0,005 en la condición que vota («tal cual»), con el `D` de las
   etiquetas ni con el propio.

Lectura, escrita antes:
- **Si pasa 1, 2 y 3,** K3 es la forma más prudente de la apuesta: se le propone al equipo en lugar de K2, con su
  propio punto 4 (una entrega de prueba que ejecuta una persona, con criterios de daño escritos antes de generarla).
  Con el resultado se dice el precio: lo que K3 deja de ganar frente a K2 dentro del proveedor.
- **Si falla 1,** K3 se cierra: la mezcla no gana ni donde K2 gana.
- **Si falla 2 o 3,** K3 se cierra: la mezcla no protege, y K2 se queda como está, con su aviso.
- **Si la réplica de solo la DFL no vale,** el punto 2 no se puede leer: K3 no se recomienda por encima de K2 y se
  queda como opción apagada, con lo que digan 1 y 3.

**Regla de K4,** frente a K2 (es el mismo modelo, promediado): gana si la media de la diferencia con K2 en las celdas
de control llega a +0,003, en la DFL (las cuatro del punto 1) y en SkillCorner (las cuatro), y ninguna celda de ninguno
de los dos baja de −0,002. Si gana, K4 sustituye a K2 dentro de lo que se proponga (K2 pasa a K4 y K3 a K5). Si no, es
un empate y se cierra: no merece la complejidad.

Avisado antes de medir:
- **Cuántas cosas se prueban:** dos candidatos y uno condicionado, sin ningún valor elegido. Con la regla de 6 de 7 y
  7 de 10, un candidato que no aporta nada pasaría pocas veces, pero no ninguna.
- **La mezcla es un seguro, y un seguro cuesta:** dentro del proveedor K3 quedará por debajo de K2. Solo compensa si en
  el otro proveedor deja de perder. Que lo haga en SkillCorner y en Metrica no prueba que lo haga en el ATD.
- **Las réplicas no son los modelos del 17/11.** Por eso se comprueba primero que repiten su problema.
- **Nada de esto se mide en el partido.** Si un candidato pasa, su punto 4 lo ejecuta una persona.

Lo que se deja fuera: reentrenar el modelo de los dos proveedores (semillas, aumentos, más datos), que necesita la GPU
y sería otro candidato con su regla; el examen de SkillCorner; cualquier cambio en `pipeline.PIECES`.

Estado: escrita antes de medir. `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian.

### 2026-11-17 · candidatos · modelo conjunto: una semilla más del modelo de un solo proveedor (lectura, antes de entrenarla)

Quién: Claude, en la sesión de Ismael (17/11). Escrita antes de entrenar o medir la semilla nueva. La primera réplica ya
está medida y vista (salida en `validation/conjunto/salidas/2026-11-17_refinar_replica_solo_dfl_en_skillcorner.md`); su
lectura con la regla de K3 va en la entrada de resultados.

Por qué: la réplica del modelo de solo la DFL (misma configuración, otros números al azar, en la CPU) no repite en
SkillCorner la pérdida publicada. K2 con ella queda en −0,005, +0,001, −0,000 y +0,003 frente a `main`; con el modelo
original eran −0,015, −0,010, −0,007 y −0,004. Frame a frame los dos modelos aciertan lo mismo en esos 10 partidos
[medido: 84,0 % frente a 83,8 % con el balón detectado, y la misma pérdida, 0,762 frente a 0,766]. Que la nota difiera
en 0,010 con el mismo acierto apunta a ruido del entrenamiento [inferencia: es una sola réplica, que además cambia de
GPU a CPU, de 48 a 33 columnas y de versión de torch].

Qué se hace: **una** réplica más del modelo de solo la DFL, con la semilla 20261125 (`entrenar.py --semilla`), la misma
configuración y en la CPU. Se puntúa en los 10 partidos de `lector.ENTRENAMIENTO` con α = 4, como la primera. Con lo
que salga se decide si se entrena una tercera.

Lectura, escrita antes:
- **«La pérdida publicada depende del entrenamiento»** si K2 con la semilla nueva queda otra vez a 0,005 o menos de
  `main` en las dos celdas con el `D` de las etiquetas. Serían dos entrenamientos de tres en empate, y el aviso sobre
  K2 pasa a decirse así: fuera de su proveedor, un entrenamiento de K2 queda entre un empate y una pérdida de 0,015.
- **«La pérdida es del modelo»** si pierde más de 0,005 en las dos. Serían dos de tres con pérdida, y el aviso se queda
  como estaba.
- En otro caso se dice el rango, sin más.
- **La mezcla con otra semilla:** se dice si K3 con la semilla nueva queda en −0,005 o más frente a `main` en las
  cuatro celdas, y cuánto saca a K2.
- **El promedio de las dos semillas** (la media de sus z, `refinar.py --pesos` con los dos ficheros) se enseña frente
  a `main` y frente a cada semilla por separado. Es una lectura, no un candidato para la entrega: la entrega usaría el
  modelo de los dos proveedores, y promediar semillas de ese modelo pide entrenarlas en la GPU.

Lo que no cambia: **el veredicto de K3 con su regla.** Esta ronda es descriptiva: sirve para decir cuánto pesa el aviso
de proveedor de K2 y qué entrenar después.

Lo que se deja: la réplica de solo SkillCorner (el sentido sin voto) se para para dejarle la CPU a esta. Si no da
tiempo a terminarla, se dice.

Estado: escrita antes de entrenar.

### 2026-11-17 · candidatos · modelo conjunto, refinamientos sin reentrenar: K4 (el espejo) se cierra; K3 (la mezcla con B5) pasa dos de sus tres puntos y el tercero no se puede leer

Quién: Claude, en la sesión de Ismael (17/11). Regla en la entrada «dos refinamientos de K2 sin reentrenar», escrita
antes de medir (`d96fce8`). Todo en datos abiertos de otros partidos; nada del partido.

Qué se probó: K3, la media a partes iguales del logit de K2 y del de B5, y K4, el logit de K2 promediado con el del
campo en espejo (`possession/refinamientos.py`, apagados).

Cómo se midió (`validation/conjunto/refinar.py`; salidas en `validation/conjunto/salidas/2026-11-17_refinar_*`):
- el instrumento da lo que tiene que dar: la mezcla con todo el peso en K2 da K2 y con todo en B5 da `main`, frame a
  frame (24 salidas); y `main` y K2 repiten sus cifras publicadas en la DFL, en SkillCorner y en Metrica;
- **A, dentro del proveedor:** los 7 partidos de la DFL y los 10 de `lector.ENTRENAMIENTO`, cada uno con el pliegue que
  no lo vio;
- **B, el otro proveedor:** una réplica del modelo de solo la DFL, entrenada aquí en la CPU (3.000 pasos, 55 minutos),
  puntuada en los 10 partidos de `lector.ENTRENAMIENTO` con α = 4;
- **C, Metrica:** los 3 partidos, con los pesos de la entrega;
- además, el harness oficial con los eventos humanos (`validation/harness/versiones/refinamientos_k2_2026-11-17.json`).

Resultado [medido], diferencia de `spellF1` con `main` (entre paréntesis, en cuántos partidos gana):

| datos | celdas | K2 | K3 | K4 |
|---|---|---|---|---|
| DFL, control | 2 condiciones × `D` de las etiquetas y propio | +0,051 (7), +0,046 (6), +0,045 (6), +0,036 (6) | +0,054 (7), +0,047 (7), +0,042 (7), +0,032 (7) | +0,060 (7), +0,052 (7), +0,048 (7), +0,038 (6) |
| DFL, flag | las mismas | +0,044, +0,037, +0,043, +0,033 (7 en todas) | +0,031, +0,024, +0,025, +0,017 (7 en todas) | +0,047, +0,039, +0,041, +0,033 (7 en todas) |
| SkillCorner, entrenamiento | 2 condiciones × 2 modos del `D` | +0,023 (8), +0,024 (7), +0,021 (10), +0,024 (10) | +0,021 (10), +0,023 (9), +0,017 (10), +0,021 (10) | +0,022 (8), +0,027 (8), +0,020 (9), +0,024 (10) |
| Metrica, pesos de la entrega | 2 condiciones × 2 modos del `D` | +0,035 (2 de 3), +0,036 (3), +0,021 (2), +0,024 (3) | +0,023 (3), +0,029 (3), +0,014 (3), +0,017 (3) | +0,035 (3), +0,039 (3), +0,024 (2), +0,022 (3) |
| SkillCorner, con la réplica de solo la DFL | las de SkillCorner | −0,005 (4), +0,001 (5), −0,000 (5), +0,003 (6) | +0,008 (6), +0,011 (6), +0,010 (7), +0,010 (7) | −0,009 (4), +0,001 (6), −0,001 (5), +0,004 (6) |

Con la regla escrita antes:
- **K4 no pasa y se cierra.** Frente a K2 gana en la DFL (+0,005 de media con control, peor celda −0,001) y empata en
  SkillCorner (−0,000 de media), y se pedía +0,003 en los dos. En Metrica tampoco se mueve (de −0,001 a +0,003). El
  espejo le quita ruido al modelo donde más gana, pero no donde importa. K5 no llegó a ser candidato (pedía que
  pasaran K3 y K4); el script lo imprime y no añade nada a K3.
- **K3, punto 1 (dentro del proveedor): pasa.** En la DFL gana con control en las cuatro celdas y en 7 de 7; con el flag
  y con el balón a la vista en los `D` no pierde (gana de +0,013 a +0,040). En SkillCorner gana en las cuatro celdas y en
  9 o 10 de 10.
- **K3, punto 3 (Metrica): pasa.** No pierde frente a `main`: gana +0,023 y +0,014 en la condición que vota, en 3 de 3.
- **K3, punto 2 (el otro proveedor): no se puede leer.** La réplica no vale con el criterio escrito antes: K2 con ella
  no pierde más de 0,005 en las dos celdas con el `D` de las etiquetas (queda en −0,005 y +0,001; con el modelo original
  eran −0,015 y −0,010). Sin una pérdida que quitar, el punto no dice lo que tenía que decir.
- **Así que K3 no se recomienda por encima de K2 y se queda como opción apagada,** con lo que dicen los puntos 1 y 3.
  Es lo que la regla decía para este caso, y no se reescribe.

Lo que sale sin voto, y hay que decirlo junto al número de K3:
- **El precio de la mezcla:** con control deja la ganancia de K2 casi como estaba (de −0,006 a +0,003 frente a K2 en
  la DFL, contando las celdas con el balón a la vista en los `D`), pero con el flag pierde de 0,013 a 0,018 frente a
  K2, y en Metrica, lo más parecido a la entrega, de 0,006 a 0,012. Con la regla de §5.8 frente a `main`, el harness oficial dice «gana» para K2 y «empate o no concluye» para K3.
- **Lo que la mezcla da a cambio:** con la réplica, en un proveedor que ninguna de sus dos mitades vio, K3 gana a
  `main` en las cuatro celdas (+0,008 a +0,011) y a K2 solo (+0,008 a +0,013, con los intervalos por encima de cero).
  Y partido a partido falla menos: en los bloques A y C, K2 queda por debajo de `main` en 12 de 136 casos (partido y
  celda), el peor con −0,026; K3, en 3, el peor con −0,007.
- **K3 es más prudente justo en los cambios de posesión.** Con el `D` propio predice un 2 % menos de posesiones que
  `main` (K2, hasta un 2 % más); con el `D` de las etiquetas, un 4 % menos en la DFL (K2, las mismas). En los eventos
  humanos de la DFL, «como el ATD», acierta el 74,9 % de las recuperaciones (`main`, el 70,3 %; K2, el 80,0 %) y el
  79,9 % de los duelos con cambio (77,3 % y 82,5 %): se queda con la mitad de lo que K2 mejora ahí. «Sin bloques»
  conserva la mitad en las recuperaciones (+4,1 puntos de +7,7) y casi nada en los duelos con cambio (+0,4 de +3,1).
  A cambio acierta más duelos sin cambio (79,6 %, frente a 74,9 % y 77,7 %).
- **Ni K2 ni K3 ven más posesiones: las colocan mejor.** En la DFL con control hay 1.736 posesiones reales; `main`
  encuentra el 72,5 %, K2 el 76,9 % y K3 el 75,9 % (emparejadas con un solape de 0,5 o más). Con el flag, el 39,1, el
  42,5 y el 41,0 %; en SkillCorner, el 44,9, el 47,9 y el 46,3 %. El hueco de los cambios que no vemos sigue ahí.

Lo que hay que decir con el número:
- **Añadido después de ver el bloque A:** las tablas partido a partido y las de posesiones encontradas
  (`*_por_partido.md`). Son descriptivas y no entran en ninguna regla.
- **`possession/aprendida.py` ha cambiado después de escribir que lo de detrás de `prueba_k2` no se tocaba:** tiene un
  envoltorio nuevo, `evidence_k3`, para el harness oficial y para una entrega de prueba. No cambia B5 ni K2
  (`prueba_pipeline`, `prueba_aprendida`, `prueba_harness`, `prueba_conjunto` y `prueba_refinamientos` siguen en verde),
  pero el fichero ya no es byte a byte el de `exp/modelo-conjunto`. Si algo de esta rama sigue adelante, primero el
  criterio C0 desde esta rama: `equipo_v9_rama` tiene que salir con `d9706dfb…be63`.
- **La réplica no es el modelo del 17/11** (CPU, 33 columnas y torch 2.15, según el comando de esta sesión: la salida
  del entrenamiento no lo imprimía, y desde ahora sí; lleva el mismo número de semilla, 20261124, pero el generador de
  la CPU no es el de la GPU). Frame a frame acierta lo mismo que él en
  SkillCorner (84,0 % frente a 83,8 %), así que la diferencia de 0,010 en la nota apunta a ruido del entrenamiento
  [inferencia]. Hay una semilla más en marcha, con su lectura escrita antes (entrada anterior).
- **El sentido de SkillCorner a la DFL no se ha medido todavía.** Su réplica está a medias y parada, para dejarle la
  CPU a la semilla nueva. Era el sentido sin voto.
- **Cuántas cosas se han mirado:** dos candidatos, sin elegir ningún valor. Además, el script mide e imprime en todas
  las ejecuciones K5, que no llegó a ser candidato, y la mezcla con ¼ y con ¾ de K2, sin voto. Con ¾ queda a 0,006 o
  menos de K2 con control, en SkillCorner y en Metrica, pierde de 0,005 a 0,011 con el flag en la DFL, y con la
  réplica saca +0,006 a +0,007. Elegir ¾ ahora sería elegir mirando el resultado.
- **La mezcla que se mide en la DFL no es siempre la de la entrega.** Cada logit va con la α de su pliegue: la de K2
  es 4, 4, 4, 4, 8, 8 y 8, y la de B5, 2, 4, 4, 4, 4, 4 y 8. En tres partidos (`J03WMX`, `J03WPY` y `J03WQQ`) K2
  entra con el doble de escala relativa que en la entrega, donde las dos son 4. En SkillCorner y en Metrica la mezcla
  sí es la de la entrega. Es lo que decía la regla («cada uno en su escala»); cuánto mueve las cifras de la DFL se
  mide aparte, sin voto.
- **Con qué código salió cada salida.** El sello «Código» de las salidas es el commit que había al ejecutarlas, y los
  scripts de `validation/conjunto/` entraron en el commit siguiente: `cuanto_cambia_k3.py` en `8409165`,
  `detalle_abiertos.py` en `118e854` y las tablas de `*_por_partido.md` en `3794aaf`. Desde ahora `refinar.py` imprime
  su propia huella y la α, y guarda con cada caché de recuentos el dominio, los pesos y el código con que se calculó.
  **Regeneradas después** (13:51, con el código de `74f3191`): las once salidas de `refinar.py`,
  `detalle_abiertos.py` y `cuanto_cambia_k3.py` se volvieron a calcular desde cero y salen idénticas fuera de las
  líneas de cabecera. Las guardadas en la rama son las regeneradas, con su sello y la huella de cada script.

Lo que haría legible el punto 2: los pesos de los dos modelos de un solo proveedor del 17/11
(`conjunto_cache/pesos/solo_dfl_todos.pt` y `solo_sc_todos.pt`, en la máquina de la GPU). Con ellos K2 sí pierde, y la
medida es un comando (`juntar.py --etiqueta solo_dfl --pliegues todos --destino … --alfa 4` y
`refinar.py --dominio sc --pesos … --entrenado-con dfl`).

Si el equipo quiere ver K3 en el partido: una entrega de prueba, que ejecuta una persona, con criterios de daño
escritos antes de generarla. Lo que cabe esperar está medido (`validation/conjunto/cuanto_cambia_k3.py`): frente a
`main` cambia del 2,6 al 3,0 % de los frames evaluados en la DFL y del 4,6 al 5,0 % en SkillCorner (K2, del 4,4 al
5,3 % y del 7,4 al 7,8 %), con un 2 % menos de posesiones, las mismas paradas y ninguna posesión de menos de 12 frames.

Descartado: recomendar K3 por lo que sale con la réplica (la regla decía que así no se podía leer); elegir el peso de
la mezcla mirando la tabla; abrir el examen de SkillCorner; seguir con K4 o con K5.

Estado: K3 y K4 apagados. `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian. K2 sigue como estaba: con su
regla cumplida y pendiente de lo que decida el equipo.

### 2026-11-17 · validación · las tres conclusiones de David en la ventana pública se repiten en los datos abiertos (descriptivo)

Quién: Claude, en la sesión de Ismael (17/11), a petición suya («por si combinamos algo suyo en el estudio»). David
subió `notebooks/ventana_publica_detalle.ipynb` (rama `feat/encender-k2`, sin outputs [comprobado con
`outputs_notebooks.py` antes de abrirlo]) y sacó tres conclusiones de los 5 minutos públicos del partido, que Ismael
pegó como agregados. Claude no ha ejecutado el notebook: lee una entrega del partido.

Qué se hizo: las mismas cuentas del notebook (cambios emparejados a ±25 frames con el scorer oficial; posesiones
encontradas con un solape de 0,5 o más y la causa de las perdidas) en los 20 partidos abiertos, para `main`, K2 y K3,
cada uno con el pliegue que no vio el partido (`validation/conjunto/detalle_abiertos.py`; salida en
`validation/conjunto/salidas/2026-11-17_detalle_abiertos.md`). No hay regla: es descriptivo y no elige nada.

Resultado [medido], con el `D` propio:
1. **«Cuando vemos un cambio lo ponemos en su sitio; el problema son los que no vemos»: se repite.** De los cambios
   directos entre equipos, `main` ve el 35,0 % en la DFL con control, el 18,7 % con el flag, el 17,6 % en SkillCorner y
   el 34,3 % en Metrica. K2 ve el 48,1, el 24,9, el 21,2 y el 40,0 %; K3, el 44,4, el 22,6, el 19,6 y el 37,7 %. El
   retraso mediano de todos los cambios que vemos (también los que pasan por `D`) es de 0 a +5 frames. K2 además
   inventa menos: le sobran 396 cambios entre equipos en
   la DFL, frente a 505 de `main`.
2. **«Nos faltan posesiones» (13 de 17 en la ventana): se repite.** Con `main` predecimos el 89 % de las que hay en la
   DFL con control, el 73 % en Metrica, el 65 % en SkillCorner y el 50 % con el flag.
3. **«Nuestras posesiones duran más: nos comemos las cortas del rival»: se repite.** Las posesiones reales de menos de
   2 s no las encuentra ninguna versión (del 0 al 9 %); las de 2 a 5 s, `main` el 27 %, K2 el 39 % y K3 el 33 % en la
   DFL con control. Casi nunca partimos una posesión (las partidas o más cortas son del 1 al 3 % de las reales):
   las perdemos por no decir su equipo ni en la mitad de sus frames, por fundirlas con la de al lado o por taparlas
   con `D`.

Lectura [inferencia]: lo que se ve en 17 posesiones del partido es lo mismo que se ve en miles de otros tres
proveedores, así que no es un accidente de la ventana. K2 mueve los tres números en la buena dirección y K3 se queda a
medio camino; ninguno cierra el hueco de los cambios que no vemos ni el de las posesiones de menos de 2 s.

Decisión: ninguna. Queda como material para el documento técnico y para decidir qué entrenar después: lo que falta no
es colocar mejor los cambios, es ver más, sobre todo los que abren posesiones cortas.

Estado: descriptivo. `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian.

### 2026-11-17 · candidatos · modelo conjunto: la semilla nueva del modelo de un solo proveedor; fuera de su proveedor K2 queda entre un empate y una pérdida pequeña, y promediar ayuda

Quién: Claude, en la sesión de Ismael (17/11). La lectura es la de la entrada «una semilla más», escrita antes de
entrenarla (`017c4fe`). Salidas en `validation/conjunto/salidas/2026-11-17_refinar_semilla2_*`,
`…_refinar_media_de_dos_semillas_*` y `…_entrenamiento_semilla2_solo_dfl.md`.

Qué se probó: una réplica más del modelo de solo la DFL (semilla 20261125, en la CPU, 3.000 pasos), puntuada en los 10
partidos de `lector.ENTRENAMIENTO` con α = 4; y la media de las z de las dos réplicas.

Resultado [medido], K2 entrenado solo con la DFL, frente a `main` en SkillCorner (`D` de las etiquetas, las dos
condiciones; y `D` propio, las dos):

| qué | `D` de las etiquetas | `D` propio |
|---|---|---|
| K2, modelo original del 17/11 (GPU) | −0,015 y −0,010 | −0,007 y −0,004 |
| K2, réplica 1 (CPU, semilla 20261124) | −0,005 y +0,001 | −0,000 y +0,003 |
| K2, réplica 2 (CPU, semilla 20261125) | −0,007 y −0,003 | −0,003 y −0,001 |
| K2, la media de las z de las dos réplicas | +0,004 y +0,004 | +0,002 y +0,002 |
| K3 con la réplica 1 | +0,008 y +0,011 | +0,010 y +0,010 |
| K3 con la réplica 2 | +0,008 y +0,011 | +0,005 y +0,008 |
| K3 con la media de las dos réplicas | +0,013 y +0,017 | +0,007 y +0,011 |

Con la lectura escrita antes:
- **Ni «depende del entrenamiento» ni «es del modelo»: el caso mixto.** Con la semilla nueva K2 pierde más de 0,005 en
  una de las dos celdas con el `D` de las etiquetas (−0,007) y en la otra no (−0,003). Se dice el rango: **en tres
  entrenamientos con la misma configuración, K2 fuera de su proveedor queda entre +0,003 y −0,015 frente a `main`, y
  en la primera celda pierde las tres veces (de −0,005 a −0,015).** No gana en ninguno. El aviso sobre K2 se queda,
  con su tamaño corregido: un empate o una pérdida pequeña, no siempre −0,015.
- Las dos réplicas aciertan frame a frame lo mismo que el modelo original (83,9 y 84,0 %, frente a 83,8 %): lo que
  cambia de un entrenamiento a otro no es el acierto, es dónde caen los cambios.
- **La mezcla aguanta con otra semilla:** K3 queda en +0,005 o más frente a `main` en las cuatro celdas, y saca a K2
  solo de +0,009 a +0,015, en 9 o 10 de 10 partidos. Es lo mismo que con la réplica 1 (+0,008 a +0,013).
- **Promediar las dos semillas parece ayudar** [lectura, no candidato]: la media de las z queda de +0,002 a +0,004
  frente a `main` (un empate), por encima de cada semilla por separado en siete de las ocho comparaciones (de −0,000
  a +0,011). El intervalo pareado queda por encima de cero en cuatro de las ocho y toca el cero en las otras cuatro:
  es poca evidencia, de dos semillas de un modelo de un solo proveedor. Mezclada con B5 da lo mejor que se ha medido
  fuera del proveedor: de +0,007 a +0,017.

Lo que no cambia: **el veredicto de K3 con su regla.** El punto 2 sigue sin poderse leer: ninguna de las dos réplicas
repite la pérdida en las dos celdas con el `D` de las etiquetas, que es lo que la regla pedía. Lo que sale aquí es
descriptivo y coherente en las dos: fuera del proveedor, la mezcla gana a B5 solo y a K2 solo.

La comprobación que quedó de la revisión, sin voto (`refinar.py --alfas-de-la-entrega`; salida en
`…_refinar_dfl_alfas_de_la_entrega.md`): con las α de la entrega (4 y 4) en los siete pliegues de la DFL, K3 gana a
`main` de +0,034 a +0,056 con control (7 de 7 en las cuatro celdas) y de +0,014 a +0,025 con el flag. Frente a K2 con
esa misma α queda de −0,001 a −0,008 con control y de −0,015 a −0,023 con el flag: **el precio de la mezcla con
control no es cero, es de hasta 0,008.** Con esas α, K4 tampoco pasa en la DFL (peor celda −0,002).

Lo que sale para lo siguiente [inferencia, sobre lo medido]:
- Lo que más ha ayudado fuera del proveedor no es afinar la red, es promediar: la red con B5 (medido en dos réplicas)
  y, con menos evidencia, dos semillas entre sí. Un paso que probar después es un K2 de los dos proveedores con
  varias semillas promediadas (en la GPU son minutos), medido como K2, con su regla y sin examen disponible.
- No se entrena una tercera semilla hoy: el rango ya dice lo que tenía que decir, y cada una son 55 minutos de CPU.

Descartado: leer esto como que K3 ha pasado su punto 2 (la regla no lo permite); proponer el promedio de semillas para
la entrega de hoy (pide entrenar en la GPU, pesos nuevos, su punto 4 y su reproducción).

Estado: descriptivo. `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian. La réplica de solo SkillCorner (el
sentido sin voto) se ha reanudado; su medida se apunta cuando acabe.

### 2026-11-17 · candidatos · modelo conjunto: la réplica de solo SkillCorner (el sentido sin voto): donde K2 falla de verdad, la mezcla vuelve al nivel de `main`

Quién: Claude, en la sesión de Ismael (17/11). Es la segunda réplica de la entrada «dos refinamientos de K2 sin
reentrenar»: el modelo de solo SkillCorner (misma configuración, en la CPU), puntuado con α = 4 en los 7 partidos de la
DFL y en los 3 de Metrica. Salidas en `validation/conjunto/salidas/2026-11-17_refinar_replica_solo_skillcorner_*` y
`…_entrenamiento_replica_solo_skillcorner.md`. La regla decía que este sentido se enseña sin voto en la DFL, porque
allí B5 sí ha visto el proveedor.

Resultado [medido], frente a `main`:

| dónde | K2 con la réplica | K3 con la réplica |
|---|---|---|
| DFL, control (4 celdas) | −0,083, −0,070, −0,057 y −0,048 (0 de 7) | −0,000, +0,008, −0,000 y +0,005 |
| DFL, flag (4 celdas) | −0,056, −0,038, −0,040 y −0,025 | −0,020, −0,007, −0,017 y −0,009 |
| Metrica (4 celdas) | −0,024, −0,019, −0,025 y −0,026 | +0,014, +0,007, +0,001 y −0,006 |

- **La réplica vale:** repite la pérdida publicada (con control, de −0,045 a −0,096; aquí, de −0,048 a −0,083) y pierde
  más de 0,03 en las cuatro celdas, que es lo que se pedía.
- **En la DFL la mezcla quita la pérdida con control** (vuelve al nivel de `main`) **y no con el flag** (se queda de
  0,007 a 0,020 por debajo). Sin voto: aquí la mitad de B5 juega en casa.
- **En Metrica ninguna de las dos mitades ha visto el proveedor,** y K2 pierde de verdad (de −0,019 a −0,026). La
  mezcla lo deja entre −0,006 y +0,014: quita la pérdida en tres de las cuatro celdas y roza el límite en la cuarta
  (−0,006 [−0,016 a +0,004]). Son 3 partidos.

Lectura [inferencia]: es el caso que la regla de K3 quería ver y que la réplica de solo la DFL no dio, pero en otro
sentido y en otros datos de los que la regla nombraba. No cambia el veredicto de K3, que sigue con su punto 2 sin
leer. Dice de qué tamaño es el seguro: cuando K2 se equivoca mucho, la mezcla cae más o menos donde estaba B5, no
por encima.

Estado: descriptivo. Con esto están medidos los dos sentidos del otro proveedor. `pipeline.PIECES`, `DELIVERY_LAYERS`
y la entrega no cambian.

### 2026-11-17 · candidatos · K3: la entrega de prueba frente a `equipo_v10`, con los criterios de daño escritos antes de generarla

Quién: Ismael (17/11): «quiero una entrega de prueba de K3 frente a `equipo_v10`». Lo escribe Claude en la rama
`exp/k2-refinar`, antes de que nadie genere `prueba_k3`. La ejecuta una persona, con los datos del partido y el entorno
limpio; Claude solo lee los agregados que se peguen.

Dónde está cada cosa:
- **`equipo_v10`** es la entrega con K2 que encendió David en `feat/encender-k2` (sha256
  `784e65e5825a7fe52f7fe5f3a51c9f5e1bccf2c9f89a1372b7b344a3f882acbc`, la misma que `prueba_k2`): 203 posesiones de
  16,9 s de media, 115 paradas y el 45,9 % de `D` en lo evaluado [medido por Ismael y por David].
- **Esta rama sale de antes de encender K2:** su `pipeline.PIECES` lleva B5, así que sin opciones genera `equipo_v9`.
  Entre las dos ramas, `possession/` solo difiere en esa línea de `pipeline.py` [medido: `git diff`], así que desde
  esta rama `--pieza candidates=aprendida.evidence_k2` tiene que dar los bytes de `equipo_v10`.

Los comandos, con el python del entorno limpio y desde la carpeta del repo en esta rama
(`git fetch origin` y `git switch --detach origin/exp/k2-refinar`):

    python -m possession.pipeline --name equipo_v9_rama
    python -m possession.pipeline --name prueba_k2_rama --pieza candidates=aprendida.evidence_k2
    python validation/partido/probar_entrega.py prueba_k3 --pieza candidates=aprendida.evidence_k3 --contra prueba_k2_rama
    python evaluation/validate_submission.py evaluation/results/prueba_k3.csv
    python evaluation/run_evaluation.py

Lo que cabe esperar de K2 a K3 [medido en datos abiertos con `validation/conjunto/cuanto_cambia_k3.py`, `D` propio, sin
las capas del partido]:

| datos | frames evaluados que cambian | de un equipo al otro | entre un equipo y `D` | posesiones | paradas | frames `D` | posesiones de menos de 12 / de 25 frames |
|---|---|---|---|---|---|---|---|
| DFL (7 partidos, 4 celdas) | 2,0–2,5 % | 1,4–1,6 % | 0,5–0,9 % | de −2,3 a −4,6 % | de −0,1 a +0,1 % | de −0,3 a 0,0 puntos | 0 / 1 en los 7 partidos |
| SkillCorner (10 partidos, 2 celdas) | 3,3 % | 1,6–1,7 % | 1,6–1,7 % | de −4,0 a −4,2 % | −0,6 % | de −0,6 a −0,7 puntos | 0 / 2 en los 10 partidos |

Con K2, el partido salió como la DFL (cambió el 4,8 % de los frames frente a `equipo_v9`; en la DFL, del 4,4 al 5,3 %).

K3 pasa su entrega de prueba si se cumple todo:
- **C0, la rama no cambia las entregas conocidas:** `equipo_v9_rama` sale con el sha256 de `equipo_v9`
  (`d9706dfb4b5389d391146d5d7efd022f01aa2a427d3e61f7ab2c06b3ecccbe63`) y `prueba_k2_rama`, con el de `equipo_v10`
  (`784e65e5…acbc`). La segunda es la referencia con la que se compara K3.
- **C1, es una entrega:** `prueba_k3` es válida y sale con 0 frames en conflicto.
- **C3, cambia lo que cabe esperar** frente a `prueba_k2_rama`: como mucho el 7 % de los frames evaluados; de un equipo
  al otro, como mucho el 3,5 %; y entre un equipo y `D`, en los dos sentidos, como mucho el 3,5 %.
- **C4, no cambia el ritmo ni el `D`:** entre 183 y 213 posesiones (`equipo_v10` tiene 203), entre 108 y 122 paradas
  (tiene 115) y entre el 44,4 y el 47,4 % de `D` en lo evaluado (tiene el 45,9 %).
- **C5, no fragmenta:** ninguna posesión de menos de 12 frames y como mucho 4 de menos de 25.
- **C6, no se rompe en la ventana pública:** frente a `equipo_v10`, el macroF1 no baja más de 0,03 ni el spellF1 más
  de 0,10. Una subida no cuenta: la ventana no elige (17 posesiones; por debajo de 0,42 todo es ruido).

Lo que no se repite: el criterio C2 de K2 (lo que el modelo ve en el ATD frente a los datos abiertos). K3 no trae
ningún modelo nuevo: usa los pesos de K2 que ya pasaron C2 y el B5 de la entrega.

Sin voto, para apuntar: de qué a qué cambian los frames, y el recuento del balón fuera (D7), que con `equipo_v9` y con
`equipo_v10` da 12 rachas tarde de 47.

Qué significa cada resultado:
- **Si pasa todo,** K3 ha hecho en el partido lo que se le puede pedir sin etiquetas: no rompe nada y cambia lo
  esperado. No dice que K3 gane a K2 en el partido; eso no se puede medir. La elección entre `equipo_v10` y K3 sigue
  siendo del equipo, con lo medido en datos abiertos: K3 falla menos partido a partido y es más prudente en los
  cambios de posesión; K2 gana más donde funciona.
- **Si falla C0,** no se sigue: algo de esta rama cambia una entrega y hay que mirarlo antes.
- **Si falla C3, C4 o C5,** K3 no se enciende sin mirar antes por qué.

Si el equipo decide entregar con K3: `pipeline.PIECES["candidates"]` pasa a `"aprendida.evidence_k3"`, la entrega se
regenera y tiene que salir byte a byte igual que `prueba_k3`; **hay que reproducirla en una segunda máquina** (K3
hereda el `np.exp` de los rasgos de B5); y el documento técnico tiene que contarla.

Pendiente aparte, y no bloquea la entrega de prueba: el punto 2 de la regla de K3 sigue sin leer. Lo haría legible
medir K3 con los pesos del modelo de solo la DFL del 17/11, que están en la máquina donde se entrenó K2
(`<datos abiertos>/conjunto_cache/pesos/solo_dfl_todos.pt`).

Estado: criterios escritos antes de generar `prueba_k3`. `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian.

### 2026-11-17 · candidatos · K3 pasa su entrega de prueba frente a `equipo_v10` (C0 a C6), en un entorno que no es el limpio

Quién: la ejecutó David en su máquina, con la rama `exp/k2-refinar` en `4a67424` y sin cambios locales, y pasó los
agregados por el chat del equipo; Ismael los pegó. Claude los lee con los criterios escritos antes (entrada «K3: la
entrega de prueba frente a `equipo_v10`», `4a67424`). Solo agregados.

Resultado [medido por David en el partido; solo agregados]:

| criterio | qué pedía | qué ha salido | ¿pasa? |
|---|---|---|---|
| C0, la rama no cambia las entregas conocidas | `equipo_v9_rama` con `d9706dfb…be63` y `prueba_k2_rama` con `784e65e5…acbc` | las dos huellas | sí |
| C1, es una entrega | válida y con 0 frames en conflicto | `prueba_k3` es válida, con 0 conflictos; sha256 `811658cd…c04b` | sí |
| C3, cambia lo que cabe esperar frente a K2 | como mucho el 7 % de los frames; de un equipo al otro, el 3,5 %; entre un equipo y `D`, el 3,5 % | 4.219 de 158.857 frames (2,66 %); 2.719 de un equipo al otro (1,71 %); 1.500 entre un equipo y `D` (0,94 %) | sí |
| C4, no cambia el ritmo ni el `D` | de 183 a 213 posesiones, de 108 a 122 paradas y del 44,4 al 47,4 % de `D` | 198 posesiones, 116 paradas y el 45,8 % de `D` | sí |
| C5, no fragmenta | ninguna posesión de menos de 12 frames y como mucho 4 de menos de 25 | 0 y 0 | sí |
| C6, no se rompe en la ventana pública | frente a `equipo_v10`, el macroF1 no baja más de 0,03 ni el spellF1 más de 0,10 | macroF1 de 0,873 a 0,876; spellF1 de 0,680 a 0,693 | sí |

Sin voto:
- De un equipo al otro, 1.798 frames pasan de `A` a `H` y 921 de `H` a `A`.
- El balón fuera (D7) no cambia: tarde en 12 de 47 rachas.
- Lo que cambia es lo que se esperaba de los datos abiertos, y se parece más a la DFL (del 2,0 al 2,5 % de los frames
  y de −2,3 a −4,6 % de posesiones) que a SkillCorner: aquí, el 2,7 % y un 2,5 % menos de posesiones (198 frente a 203).
- La subida en la ventana pública no cuenta: son 17 posesiones (una emparejada más) y por debajo de 0,42 todo es ruido.

El aviso del entorno: **no se generó con el entorno limpio,** sino con Python 3.12.10 y numpy 1.26.4.
- En ese entorno, `equipo_v9_rama` y `prueba_k2_rama` salen con sus huellas de siempre: B5 y K2 dan los mismos bytes
  con numpy 1.26.4 que con 2.5.4. Es un dato a favor de la reproducibilidad de `equipo_v10`.
- La huella de `prueba_k3` (`811658cd…c04b`) queda sin confirmar en el entorno limpio. Si el equipo elige K3, hay que
  regenerarla con `requirements-entrega.txt` y reproducirla en una segunda máquina antes de entregar.

Decisión y por qué:
- **K3 ha pasado su entrega de prueba:** en el partido no rompe nada y cambia lo esperado. No dice que gane a K2 en el
  partido: eso no se puede medir.
- **No se enciende aquí.** Con su regla, K3 sigue sin quedar recomendada por encima de K2 (su punto 2 no se pudo leer),
  y elegir entre `equipo_v10` y K3 es del equipo. `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian.

Estado: K3 apagada, con su entrega de prueba pasada. Pendiente de lo que decida el equipo.

### 2026-11-17 · candidatos · se enciende K3: `pipeline.PIECES["candidates"]` pasa a `aprendida.evidence_k3`

Quién: Ismael (17/11, por la tarde): «lo he comentado con el equipo pero ya te digo yo me decanto por K3 de momento»,
y pidió juntar la rama de los refinamientos con la de David. El cambio de código lo hace Claude en la rama
`feat/encender-k3`, que junta `feat/encender-k2` (hasta `02313a9`, sin el notebook) y `exp/k2-refinar`.

Qué se enciende: K3, la media a partes iguales del logit de K2 y del de B5, puntuada como B5
(`possession/refinamientos.py`, por el envoltorio `aprendida.evidence_k3`), como evidencia de equipo de la entrega en
lugar de K2 sola. El `D` (`dead_state`, `dead_ball`), el decodificador (`decode_cortas_a_d`) y las capas del partido
(`DELIVERY_LAYERS`) no cambian. No se entrena nada: usa los pesos de K2 y los coeficientes de B5 que ya estaban.

Por qué [medido; entradas del 17/11 sobre los refinamientos]:
- **Gana a B5 en todo lo medido:** de +0,034 a +0,056 con control en la DFL (con las α de la entrega), de +0,017 a
  +0,023 en SkillCorner y de +0,014 a +0,029 en Metrica.
- **Falla menos partido a partido:** queda por debajo de B5 en 3 de 136 casos (el peor, −0,007); K2, en 12 (el peor,
  −0,026).
- **Fuera del proveedor aguanta mejor que K2:** con K2 entrenada con un solo proveedor, K3 queda de −0,020 a +0,014
  frente a B5, y K2 sola, de −0,083 a +0,003.
- **Pasó su entrega de prueba frente a `equipo_v10`** (C0 a C6): cambia el 2,7 % de los frames, con 198 posesiones y
  116 paradas.

Lo que se sabe en contra, y se asume:
- **Con la regla escrita antes de medir, K3 no quedaba recomendada por encima de K2:** su punto 2 no se pudo leer. Lo
  que se midió después va a su favor, pero no en la prueba que la regla nombraba. Encenderla es una decisión del
  equipo, no un veredicto de la regla.
- **Gana menos donde K2 funciona:** con el flag, de 0,015 a 0,023 menos que K2; en Metrica, de 0,006 a 0,012 menos; con
  control, hasta 0,008 menos.
- **Es más prudente en los cambios de posesión:** de los cambios directos entre equipos en la DFL ve el 44 % (K2, el
  48 %; B5, el 35 %), y se queda con la mitad de la mejora de K2 en recuperaciones.
- Nada de esto se ha medido en el partido con etiquetas. Sigue siendo una apuesta, más prudente que la de K2.

Qué cambia en el código:
- `pipeline.PIECES["candidates"]` pasa a `"aprendida.evidence_k3"`.
- Las pruebas sin datos que fijaban K2 como pieza de equipo dicen ahora K3 (`prueba_pipeline`, `prueba_harness`,
  `prueba_balon_fuera`, `prueba_conjunto`, `prueba_refinamientos`). Pasan 24 de 25; `prueba_silbato` necesita `ffmpeg`
  y falla igual sin este cambio.
- **`main`, en los scripts del estudio, vuelve a ser B5 fijada a mano** (`validation/conjunto/medir.py`, `metrica.py` y
  las dos definiciones de versiones del harness): con K2 o K3 en la entrega, tomarla de `pipeline.PIECES` comparaba
  la red consigo misma. El candado de `refinar.py` que se negaba a medir deja de hacer falta y se quita.
- `validation/partido/probar_entrega.py` compara por defecto con `equipo_v11`.
- Los comentarios de `possession/` que decían «apagado» o B5 están al día. Son código de la entrega: van en este
  mismo cambio, antes de regenerar.

Lo que hay que hacer, en este orden:
1. **Regenerar en el entorno limpio** (`requirements-entrega.txt`), desde esta rama y sin cambios locales:
   `python -m possession.pipeline --name equipo_v11`. Tiene que salir con 0 conflictos, 198 posesiones y, si numpy
   2.5.4 da los mismos bytes que 1.26.4 como pasó con B5 y con K2, sha256 `811658cd…c04b`. Si sale otra huella, la
   buena es la del entorno limpio, y se apunta.
2. **Validar** ese mismo fichero con `evaluation/validate_submission.py`.
3. **Reproducirla en una segunda máquina.** K3 hereda el `np.exp` de los rasgos de B5.
4. **El documento técnico** tiene que contar K2 y K3: los datos de entrenamiento y su origen, que es una apuesta y qué
   se sabe en contra.
5. Lo pendiente de la PR 26 que no es de esta rama: la excepción escrita de los pesos (`CONTRIBUTING.md` §7) y los
   cuatro scripts de SkillCorner que dan por hecho que la entrega no vio esos partidos.

Vuelta atrás: en `main`, `pipeline.PIECES["candidates"]` vuelve a `"aprendida.evidence_k2"` (la entrega tiene que
salir con `784e65e5…acbc`, la de `equipo_v10`, reproducida en dos máquinas) o a `"aprendida.evidence_b5"` (con
`d9706dfb…be63`, la de `equipo_v9`), cambiando a la vez las comprobaciones de las pruebas que fijan la pieza. Desde
esta rama, las dos huellas salieron bien al pasar la pieza a mano (criterio C0 de la entrega de prueba).

Descartado: mezclar con ¾ de K2 (se vio sin voto y elegirlo ahora sería elegir mirando el resultado); esperar a los
pesos de la máquina de la GPU para leer el punto 2 (no llegan hoy).

Estado: encendida, y mergeada en `main` el 17/11 con merge commit por decisión de Ismael («súbelo a la branch y
directamente mergea con el main»), sin esperar a regenerar. **`equipo_v11` no existe todavía:** hay que regenerarla
desde `main` en el entorno limpio, validarla y reproducirla antes de entregar. Lleva dentro la rama de David
(`feat/encender-k2`, hasta `02313a9`): su notebook queda fuera, y la excepción escrita de los pesos en
`CONTRIBUTING.md` §7, pendiente.

### 2026-11-17 · infraestructura · los pesos de K2 están en git: excepción escrita a `CONTRIBUTING.md` §7 y al contrato de las piezas

Quién: Ismael (17/11, por la tarde), al leer la revisión de la PR 26: «sí, escríbela la excepción». La escribe Claude.

Qué pasaba: la revisión de la PR 26 marcó dos incumplimientos formales, que entraron en `main` con el merge de
`feat/encender-k3`:
- `possession/conjunto_pesos.npz` es un `*.npz`, y `CONTRIBUTING.md` §7 dice que los `*.npz` no entran en git;
- `possession/conjunto.py` abre ese fichero, y el contrato decía que ninguna pieza abre ficheros salvo `dead_ball.py`
  y `transiciones.py`.

Decisión: **se aceptan los dos, como una sola excepción escrita, y solo para ese fichero.**

Por qué:
- **No le aplica el motivo de la norma.** §7 excluye las cachés y los rasgos por frame porque son datos derivados del
  partido que permiten reconstruir los originales. Esto son los pesos de la red de K2 (8 juegos de 36.260 números),
  entrenada con datos abiertos de otros partidos: la Bundesliga de Bassek et al., 2025 (CC BY 4.0) y SkillCorner (MIT).
  No lleva nada del partido [medido: las claves del fichero son solo los pesos, las dilaciones, α y γ de cada juego].
- **Hace falta dentro del repo.** La entrega lo usa, y el entrenamiento en GPU no se repite bit a bit, así que sin el
  fichero el repo no regenera el CSV con un comando.
- **No cabe como texto en el módulo,** que es lo que el plan pedía para los coeficientes de un modelo (así van los de B5).
- **La pieza no lee el partido:** la ruta sale de la carpeta del módulo, carga sin `pickle` y el harness corre con el
  mismo fichero. `prueba_pipeline.py` deja leer esa ruta exacta, y solo leer; cualquier otro fichero sigue siendo un
  error.

Qué queda escrito: `CONTRIBUTING.md` §7 (la excepción, con su sha256
`6d16316f85063f13765fe4a8707558d6f26b800b9d43ce877d8dad95ae8c0da2`), `docs/PLAN_ENTREGA.md` §2 (el contrato y la
regla de los coeficientes), `CLAUDE.md` («Interfaz común») y `possession/tracking.py` (que ya lo decía desde el
merge).

Lo que no cubre: ningún otro `.npz`, `.npy`, `.pkl` ni `.pt`. Los pesos de los experimentos se quedan fuera del repo.
Si el fichero cambia, cambia la entrega: se regenera y se apunta el sha256 nuevo.

Lo que obliga a hacer: el documento técnico tiene que citar los dos conjuntos de datos con sus licencias, porque los
pesos derivan de ellos y el repo será público.

Descartado: quitar el fichero (la entrega con K2 o K3 no se podría regenerar); pasarlo a texto hoy (obligaría a tocar
`possession/` y a regenerar y reproducir otra vez).

Estado: escrita. De la revisión de la PR 26 queda pendiente lo que no es de `possession/`: los cuatro scripts de
SkillCorner que dan por hecho que la entrega no vio esos partidos, y el notebook de David, que se quedó fuera de `main`.

### 2026-11-17 · infraestructura · `equipo_v11`, con K3: generada desde `main` en el entorno limpio, válida y con la huella de `prueba_k3`

Quién: la generó una persona del equipo en Windows (la ruta del repo es `C:\PROYECTOS\mtah2027-piso2nyc`; el entorno,
Python 3.13.1 y numpy 2.5.4, es el que David usó para `equipo_v10` [quién fue, sin confirmar]) e Ismael pegó la
salida, que solo lleva agregados. Claude la lee.

Resultado [medido en el partido; solo agregados]:
- **`python -m possession.pipeline --name equipo_v11`,** con `main` en `23dcbc1` y sin cambios locales en el código de
  la entrega, con las piezas de la entrega y sin capas añadidas:
  - el ATD, entero: 199.319 líneas leídas y válidas, ninguna saltada ni repetida, y ningún frame sin línea;
  - 0 frames con piezas en conflicto;
  - 198 posesiones (96 en la primera parte y 102 en la segunda) y 116 paradas (54 y 62);
  - ninguna racha de menos de 12 frames ni de menos de 25, en ninguna de las dos partes;
  - el 45,8 % de `D` en lo evaluado, y toda la `X` fuera de los tramos evaluados;
  - sha256 `811658cd52267cbd75607270c2c359e2244b05b8a6d091d6ce8330d2d971c04b`.
- **El validador da `Valid`:** 199.319 filas y 198 posesiones de 17,4 s de media.

Qué significa:
- **Es byte a byte la entrega de prueba `prueba_k3`,** que pasó los criterios C0 a C6 frente a `equipo_v10`. Aquella
  se generó con Python 3.12.10 y numpy 1.26.4; esta, con el entorno limpio. K3 da los mismos bytes con las dos
  versiones de numpy, como B5 y K2.
- **Los recuentos son los esperados** en la entrada «se enciende K3»: 198 posesiones, 116 paradas y 0 conflictos.
- **`equipo_v11` es la entrega vigente:** generada desde `main`, en el entorno limpio y validada.

Lo que falta antes de entregar:
- **Reproducirla en una segunda máquina.** Las dos generaciones pueden ser de la misma máquina con dos entornos [sin
  confirmar]. K3 hereda el `np.exp` de los rasgos de B5, y ni K2 ni K3 se han ejecutado sobre el partido en Linux.
- **El documento técnico** tiene que contar K2 y K3 y citar los datos de entrenamiento con sus licencias.
- Copiar ese mismo fichero como `<NOMBRE_EQUIPO>.csv` y pasar `validate_submission.py` sobre la copia.

Estado: `equipo_v11` generada y validada. `main` no cambia de código: después de `23dcbc1` solo entra documentación.
