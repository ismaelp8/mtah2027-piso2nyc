# More than a Hack 2027: brief compartido para Claude

> Claude carga este fichero al empezar cada sesión en este repo, la abra quien la abra. **Léelo entero
> antes de hacer nada.**
>
> - Normas del repo (ramas, commits, PR, qué no entra en git): [`CONTRIBUTING.md`](CONTRIBUTING.md).
> - Guía larga para personas: [`docs/GUIA_EQUIPO.md`](docs/GUIA_EQUIPO.md). Registro de decisiones:
>   [`docs/decisiones.md`](docs/decisiones.md).
> - Lo personal (quién eres, tu rol, tu sistema operativo, tus rutas) va en `CLAUDE.local.md`, que no
>   se sube a git (ver `CONTRIBUTING.md` §1).
> - Si algo de aquí choca con los `.md` oficiales, mandan ellos. Si choca con
>   `evaluation/possession_metrics.py`, manda el código.

**Entrega:** martes **17 de noviembre de 2026, 23:59 CET**. Las instrucciones llegan por email antes
del 14.

---

## ⚠️ Regla nº 1: los datos del concurso no pasan por Claude

Los términos del concurso prohíben subir o enseñar a cualquier LLM alojado en la nube los vídeos, los
datasets o **cualquier extracto** de ellos. Claude es un LLM en la nube. Saltarse esto puede
descalificar al equipo, así que:

- **No abras, leas, busques, listes ni cargues nada de `$MTAH_DATA_DIR`**, ni de `data/` dentro del
  repo si alguien descomprimió ahí. Esto vale para Read, Grep, Glob, `cat`, `head`, `ls`, `python -c` y
  cualquier script que imprima contenido.
- **Nadie adjunta ficheros `BAR-ATH_*` con `@` ni los arrastra al chat.** Al adjuntar un fichero, la app
  manda su contenido al modelo, y eso ya cuenta como subirlo. Si alguien lo hace por error, no uses el
  contenido y avísalo en ese momento.
- **No ejecutes código que lea los datos del partido** (nuestro pipeline, `starter/baseline.py`, los
  notebooks). Claude escribe el código, la persona lo ejecuta en local y te pega solo agregados:
  - spellF1 y macroF1;
  - recuentos y tiempos;
  - errores sin valores de datos: tipo de error, fichero y línea.
- **Lo que Claude sí puede ejecutar:**
  - `evaluation/validate_submission.py` y `evaluation/run_evaluation.py`, que solo leen las entregas y
    la GT pública y solo imprimen agregados;
  - los scripts de `validation/scripts/`, que solo leen datos abiertos de otros partidos, la GT pública
    o nada.

  Los scripts que lean datos del partido van en `validation/partido/` y los ejecuta solo una persona.
- **No leas nuestras entregas** (`evaluation/results/*.csv`) **ni `evaluation/reports/`**: son etiquetas
  del partido frame a frame. Para saber qué dice una entrega, usa `validate_submission.py`.
- **Notebooks:** sus outputs guardan datos (tablas, coordenadas, gráficos del tracking).
  - Antes de leer un `.ipynb` o de mirar su diff, compruébalo con
    `python .claude/skills/subir/outputs_notebooks.py <notebook>`, que solo imprime recuentos.
  - Si tiene outputs, no lo abras. Pide a su dueño que lo limpie, o límpialo tú con `--limpiar` si te da
    permiso.
- **Para saber cómo son los datos, usa `DATA.md`** (resumen más abajo). No lo compruebes contra los
  ficheros.
- **Sí se puede leer:**
  - el código y la documentación del repo;
  - los 5 minutos de GT pública de `evaluation/gt/`;
  - los datos abiertos de **otros** partidos: el dataset de la Bundesliga de Bassek et al. y Metrica
    sample-data (ver «Cómo validar sin hacer trampa»).
- **Si hay dudas sobre si algo cuenta como "extracto"**, se pregunta a
  hackathon.talentarena@mobileworldcapital.com **antes** de hacerlo.

**Red de seguridad.** `.claude/settings.json` se probó el 11/11/2026 con ficheros de prueba inofensivos,
nunca con datos reales.
- **Bloquea** Read, Grep, Glob, `cat` y `Get-Content` sobre:
  - `BAR-ATH_tactical*`, `BAR-ATH_broadcast*` y `*.mp4`, estén donde estén;
  - cualquier carpeta llamada `mtah2027-data`;
  - `data/tactical/` y `data/broadcast/`;
  - `evaluation/results/*.csv` y `evaluation/reports/`.
- **No bloquea:**
  - `python -c "open(...)"`;
  - un `grep -r` sobre una carpeta;
  - datos guardados en otra ruta con otros nombres.
- **Solo está comprobada en una sesión abierta directamente en la carpeta del repo.** En una sesión
  abierta en otra carpeta y movida después al repo, las mismas pruebas no bloquearon nada: Read, Grep y
  `cat` leyeron los ficheros de prueba.

La protección de verdad es esta regla, no la configuración.

---

## El equipo

| persona | GitHub | papel |
|---|---|---|
| Ismael Pintor | `ismaelp8` | infraestructura y entrega, reviewer, dueño del documento técnico |
| David Ortega | `ortegafer` | reviewer |
| Antonio Azuer | `antonioazuero11-wq` | por asignar |
| Manuel Herrero | `manuelherrero` | por asignar |
| Ana Aparicio | — | documento técnico |

- **Si alguien delega el git en Claude** (lo dice en su `CLAUDE.local.md` o lo pide en la
  conversación), hazlo tú con las skills. Explica cada paso en una frase sencilla, sin jerga, y pide
  confirmación antes de subir nada.
- **Ismael y David revisan las PR.** Nadie aprueba su propia PR.
- **Nombre de equipo para la entrega: por confirmar.** Tiene que coincidir exactamente con el que puso
  cada uno al inscribirse. Hasta entonces, `<NOMBRE_EQUIPO>`.

## Al empezar cada sesión

1. **Quién habla.** Si `CLAUDE.local.md` no lo dice, pregunta su nombre y su rol, y ofrécele crear su
   `CLAUDE.local.md` (plantilla en `CONTRIBUTING.md` §1).
2. **Primera sesión de esa persona:**
   - resume el reto en 5 líneas para confirmar que lo has entendido;
   - si está montando su máquina, guíale por `docs/GUIA_EQUIPO.md` §7 paso a paso y espera su
     confirmación en cada uno.
3. **Antes de tocar nada,** mira `git status` y `git branch --show-current`. Si va a escribir algo y está
   en `main`, propón `/empezar`.

---

## El reto en una pantalla

- **Partido:** FC Barcelona (local, `H`) contra Athletic Club (visitante, `A`). LaLiga 2024-25, jornada 2.
- **Tarea:** para **cada frame** del vídeo táctico, decir quién tiene la posesión del balón.
- **Salida:** un CSV `frame,label` con exactamente **199.319 filas** (frames 0…199318, en orden).

| label | significado |
|---|---|
| `H` | posesión del Barça, balón en juego |
| `A` | posesión del Athletic, balón en juego |
| `D` | balón muerto (fuera de juego). No se pregunta de quién es |
| `X` | sin respuesta |

- **Ranking:** `spellF1`, sin jurado. El desempate es `macroF1`.
- **Baseline a batir:** spellF1 **0,2433** sobre el partido completo (`baseline_smooth50`).
- **Ground truth disponible:** solo los primeros **5 minutos** de juego.
  - Sirve para comprobar que el pipeline funciona.
  - **No** sirve para entrenar ni para ajustar parámetros: está prohibido.
  - La nota final se calcula con el partido entero, cuya ground truth es privada.
- **Pasan al Innovation Challenge** (26 nov – 14 ene) los 20 mejores equipos. Los resultados se publican
  antes del 26 de noviembre.

### Qué cuenta como posesión (CHALLENGE.md)

- Mientras el balón está en juego, siempre hay un equipo en posesión. Si el balón está suelto o
  disputado, la posesión **sigue siendo del último equipo** que la tuvo.
- La posesión cambia solo cuando el rival consigue un control **controlado** del balón. No la cambian:
  - un toque sin control;
  - un desvío que no intercepta el pase;
  - un duelo aéreo ganado sin control posterior.
- Una posesión es una racha máxima de un mismo equipo con el balón vivo. `H H D D H H` son **dos**
  posesiones.
- La ground truth se generó de forma mecánica a partir del tracking **corregido**:
  - `D` donde el tracking corregido marca el balón como muerto;
  - en el resto de frames, el equipo que ese tracking marca como poseedor;
  - sin suavizado ni ajustes a mano.

## Qué decide la nota (`EVALUATION.md` y `evaluation/possession_metrics.py`)

- **spellF1:** cada posesión se trata como un objeto. Las posesiones predichas se emparejan una a una con
  las reales por IoU temporal y se calcula el F1 con umbrales de 0,3 a 0,7, promediado.
  - **Lo que cuesta retrasarse:**

    | retraso | spellF1 |
    |---|---|
    | 1 frame | sin penalización |
    | 3 frames | 0,98 |
    | 8 frames | 0,89 |
    | 1 segundo | 0,65 |

  - **Fragmentar es lo peor que se puede hacer.** El baseline sin suavizar inventa muchísimas posesiones
    y saca spellF1 0,05, aunque su macroF1 parece aceptable.
  - Diferencias de menos de ~0,04 en spellF1 son ruido.
- **macroF1:** F1 medio por frame de `H`, `A` y `D`. Aquí la `X` cuenta como fallo.
- **La `X` en spellF1** se rellena con la última etiqueta de esa misma parte. Es decir, para spellF1
  una `X` equivale a repetir la etiqueta anterior. Por eso:
  - en un frame evaluado, escribir directamente la etiqueta anterior da **el mismo spellF1** y un
    macroF1 igual o mejor;
  - **la `X` solo se usa fuera de los tramos evaluados.** Dentro, siempre se escribe una etiqueta.
- **Frames evaluados:**

  | tramo | frames |
  |---|---|
  | 1ª parte | 11.185–90.651 |
  | 2ª parte | 110.808–190.197 |
  | total | 158.857 frames |

  Lo que se escriba fuera de esos rangos se ignora.

  **Ojo:** la 2ª parte se evalúa desde el frame 110.808, pero el saque inicial es en el **113.742**. Esos
  2.934 frames se evalúan y todos son `D`. Lo dice el FAQ. Mejor detectarlo con un algoritmo; si se usa
  la constante, se documenta.
- **Los 5 minutos públicos no sirven para elegir entre versiones.** El propio repo lo demuestra:

  | baseline | spellF1 en la ventana pública | spellF1 en el partido completo |
  |---|---|---|
  | `smooth125` | **0,4242** (el mejor en la ventana) | 0,2242 |
  | `smooth50` | 0,3256 | **0,2433** (el mejor de verdad) |

## Los datos (resumen de `DATA.md`; no abrir los ficheros)

Vienen en la carpeta de Drive que mandó la organización. Se descomprimen **fuera del repo y fuera de
OneDrive, iCloud o Dropbox**, en la ruta a la que apunta `MTAH_DATA_DIR`:

```
$MTAH_DATA_DIR/
├─ tactical/                               ← la referencia: la fila i de la entrega es el frame i
│  ├─ BAR-ATH_tactical.mp4                 199.319 frames, 25 fps, 1920×1080
│  ├─ BAR-ATH_tactical_atd.xml             metadatos del tracking (equipos, slots)
│  ├─ BAR-ATH_tactical_atd.txt             tracking de jugadores y balón
│  ├─ BAR-ATH_tactical_homography.csv      una matriz 3×3 por frame, válida en el 100 %
│  └─ BAR-ATH_tactical_smart_tagging.xml   638 fases tácticas y balones parados
└─ broadcast/                              opcional, NO sincronizado con el táctico
   ├─ BAR-ATH_broadcast.mp4                164.488 frames, con cortes y repeticiones
   ├─ BAR-ATH_broadcast_atd.xml / _atd.txt
   └─ BAR-ATH_broadcast_homography.csv     válida solo en el 65,8 %
```

**Tracking automático (ATD):**
- Es automático y sin corregir.
- Formato de cada línea: `<frame>:<jugador>;<jugador>;...:<balón>`. Cada grupo es `x,y,velocidad` y los
  valores ausentes son `NaN`.
- Hay **46 slots de track para 22 jugadores**, sin identidad de jugador: solo se sabe el equipo. Los slots
  aparecen, desaparecen y se intercambian.
- Las coordenadas están **normalizadas entre 0 y 1**. Para calcular distancias hay que escalar a metros
  con 105,3 × 68,0 (`games.GAMES["BAR-ATH"]["pitch"]`), porque el campo no es cuadrado.
- **El balón falta en el 41 % de los frames evaluados**, y sobre todo en los momentos importantes: áreas
  llenas, balones aéreos y entradas. Es la dificultad central del reto.
- Durante el juego se ven de media 20,5 objetos.

**Smart Tagging:**
- Es automático: puede tener falsos positivos y falsos negativos.
- Viene en formato SportsCode XML. Los códigos van en mayúsculas (`SET PIECES`) y las etiquetas en formato
  título (`Team`, `Kick Off (Start)`). Compara sin distinguir mayúsculas.
- Cada fase lleva el equipo. `Team = N/A` aparece 36 veces, entre ellas **en todos los saques de banda**.
- Los intervalos son **fases, no posesiones**.
- Los `SET PIECES` marcan reinicios de juego: 26 saques de banda, 12 córners, 10 saques de puerta, 5 faltas
  y 6 saques iniciales.

**Homografía:** convierte coordenadas de campo (0–1) en píxeles del vídeo. Columnas:
`frame,h00…h22,reprojection_error,valid`.

**Alineación de frames** (ante la duda, el lector de `starter/baseline.py` es la referencia):

| fuente | índice | frame de la entrega |
|---|---|---|
| ATD | `frame_id` 1…199319 | `frame_id - 1` |
| Smart Tagging | segundos desde el inicio del vídeo | `round(segundos * 25)` |
| homografía | `frame` 0…199318 | el mismo |

---

## Mapa del repositorio

**Lo oficial (de Metrica): no se toca.** Solo cambia cuando llega un arreglo de `upstream`
(`/sincronizar-upstream`).

```
games.py                     constantes del partido, rutas de los ficheros (asset_paths) y alineación
evaluation/
  possession_metrics.py      definición de todas las métricas (manda sobre la documentación)
  run_evaluation.py          el scorer oficial, el mismo que usará la organización
  validate_submission.py     los mismos checks que el scorer; ejecutar antes de cada entrega
  gt/                        los 5 minutos públicos de ground truth
  results/                   aquí van las entregas (*.csv, ignorados por git salvo los baselines)
starter/                     baseline.py (jugador más cercano + voto por mayoría), loaders, 3 notebooks
data/                        vacío salvo su README; los datos van fuera, en MTAH_DATA_DIR
README · CHALLENGE · DATA · EVALUATION · SUBMISSION · RULES · FAQ · OVERVIEW (.md), .gitignore,
LICENSE, CITATION.cff, requirements.txt, requirements-starter.txt
```

Documentación oficial, en este orden: README → CHALLENGE → DATA → EVALUATION → SUBMISSION → RULES → FAQ.
La única excepción prevista es fijar las versiones de `requirements.txt` antes de congelar, y la
decide el responsable de infraestructura.

**Lo nuestro:**

```
CLAUDE.md                    este brief
CONTRIBUTING.md              normas del repo
.github/pull_request_template.md
.claude/
  settings.json              deny de los datos, allow de comandos seguros, commits sin atribución a Claude
  skills/                    /empezar /subir /actualizar /revisar-pr /sincronizar-upstream /evaluar /decision
  agents/revisor.md          revisa un diff contra nuestras reglas
docs/
  GUIA_EQUIPO.md             guía larga para personas
  decisiones.md              registro de decisiones (materia prima del documento técnico)
  investigacion_metodos.md   análisis de métodos, alternativas y recomendación
validation/                  validación externa con datos abiertos: pasos, scripts y resultados agregados
```

**Lo previsto** (propuesta de `docs/GUIA_EQUIPO.md` §8):
- un paquete `possession/` con `io`, `ball`, `dead_ball`, `candidates`, `temporal` y `pipeline`, que
  genere la entrega con un solo comando;
- `notebooks/` para la exploración, siempre sin outputs.

## Convenciones de código

- **Módulos pequeños** con funciones puras de numpy y pandas.
- **Deterministas:**
  - semillas fijas;
  - nada que dependa del orden en que aparecen los ficheros ni de la hora.

  La entrega tiene que regenerarse **byte a byte**.
- **Sin rutas fijas.** Todo pasa por `games.py` (`games.asset_paths()`, `games.GAMES`,
  `games.half_video_blocks()`), y los datos se localizan con `MTAH_DATA_DIR`.
- **Interfaz común:**
  - cada módulo recibe las rutas de `games.asset_paths()`;
  - cada módulo devuelve un `np.ndarray` de **199.319** posiciones indexado por **frame de vídeo**.

  Así las piezas se combinan sin pelearse por la alineación.
- **Distancias en metros:** se escalan con `games.GAMES["BAR-ATH"]["pitch"]`.
- **Ninguna constante ligada a frames concretos de este partido** salvo las de `games.py`. Mirar el vídeo
  para entenderlo está permitido. Convertir lo que se ve en etiquetas, correcciones o constantes, no.
- **Nada se ajusta contra la ventana pública.**
- **Los scripts imprimen solo agregados:** recuentos, porcentajes, métricas y tiempos. Nada de
  `print(df.head())`, `display()` ni logs con valores por frame. Así su salida se puede pegar a Claude.
- **Dependencias:** cada una se declara en `requirements.txt` y se fija su versión antes de congelar.
- **Cada decisión de método** se apunta en `docs/decisiones.md` (`/decision`): qué se probó, qué se
  descartó y por qué. Es la materia prima del documento técnico.

## Cómo comprobar resultados sin ver datos

- Para comprobar algo del partido, escribe un script que imprima **solo agregados** y pide a la persona
  que lo ejecute y te pegue el resultado.
- **`/evaluar`** valida una entrega y la puntúa en la ventana pública, enseñando solo agregados.
  `python evaluation/run_evaluation.py --bootstrap 1000` da intervalos para ver si una mejora es real o
  ruido.
- **Si alguien propone ajustar contra los 5 minutos públicos,** recuérdale la regla y propón la
  validación externa.

## Cómo validar sin hacer trampa

- **Los 5 minutos públicos** se usan solo para comprobar que el pipeline es correcto: alineación, formato
  y significado de las etiquetas. Nunca para elegir entre dos versiones.
- **La validación de verdad usa datos de otros partidos**, que las reglas permiten en cualquier cantidad.
  El plan completo está en `docs/investigacion_metodos.md` §5.
  - **Dataset principal propuesto: el de la Bundesliga** (Bassek et al., 2025).
    - Son 7 partidos a 25 Hz con licencia CC-BY 4.0.
    - Trae en cada frame quién posee el balón y si está vivo, el mismo tipo de etiqueta que la GT del
      reto: `D` si el balón está inactivo y, si no, `H` o `A`.
    - **Está pendiente del «experimento 0»** (`validation/PASOS.md`), que comprueba si esas etiquetas
      se comportan como pide la definición de posesión de `CHALLENGE.md`. Hasta entonces es una
      propuesta, no una decisión cerrada.
  - **Dataset secundario: Metrica sample-data** (https://github.com/metrica-sports/sample-data).
    - Son 3 partidos con tracking y eventos sincronizados, que también se cargan con kloppy.
    - No trae posesión por frame: las etiquetas `H`/`A`/`D` hay que derivarlas de los eventos.
    - Sirve para comprobar que las conclusiones aguantan con otro proveedor.
  - El tracking abierto se **degrada** para que se parezca al ATD:
    - quitar ~41 % de los frames de balón;
    - eliminar identidades;
    - fragmentar tracks.
  - Se puntúa con `evaluation/possession_metrics.py`.
  - En el documento técnico hay que explicar la fuente, cómo se derivaron las etiquetas y cuántas se
    usaron, y citar a los autores de cada dataset.
  - Claude **sí puede** leer estos datos, porque son públicos y de otros partidos. Se descargan con un
    script y no se commitean.
- **Prohibido:**
  - etiquetar a mano cualquier cosa de este partido, ni siquiera para validar;
  - usar datos humanos de este partido de cualquier fuente (Opta, StatsBomb, Wyscout, LaLiga…).

---

## Flujo de git: lo que Claude hace siempre

Las normas completas están en `CONTRIBUTING.md`. Esto es lo que Claude no se salta nunca:

- **Nunca commit ni push a `main`.** Cada tarea va en su rama `tipo/descripcion` (`/empezar`).
- **Ficheros siempre por nombre:** `git add <ficheros>`. Nunca `git add -A`, `git add .` ni
  `git commit -a`.
- **Antes de cada commit:**
  - `git status` sin datos, cachés, CSV de entregas, PDFs, `CLAUDE.local.md` ni
    `.claude/settings.local.json`;
  - notebooks sin outputs;
  - ficheros oficiales sin tocar.
- **Autoría: el commit es de quien sube los cambios, con su propia identidad de git.**
  - Antes del primer commit de la sesión, comprueba `git config user.name` y `git config user.email`. Si
    no corresponden a esa persona, para y ayúdale a configurarlos.
  - Nunca `Co-Authored-By` (ni de Claude ni de nadie).
  - Nunca "Generated with Claude Code" en una PR.
  - Nunca hagas un commit en nombre de otra persona.

  `.claude/settings.json` ya desactiva la atribución a Claude.
- **Mensaje de commit:** una frase en español que diga qué cambia y por qué (`CONTRIBUTING.md` §3).
- **Pide confirmación** antes de cada push, de abrir una PR, de aprobarla y de mergearla. Que alguien
  pida `/subir` es pedir que se suba, pero antes enséñale el resumen.
- **Reviewers de cada PR:**

  | abre la PR | revisa |
  |---|---|
  | Ismael | `ortegafer` |
  | David | `ismaelp8` |
  | cualquier otra persona | los dos |

  Basta con **una aprobación**, y nadie aprueba su propia PR.
- **Merge:** lo hace quien aprueba.
  - Por defecto con squash.
  - Las PR `sync/*` (cambios de `upstream`) con merge commit.
- **Prohibido:**
  - `--force` en `main` o en ramas de otros;
  - `--no-verify`;
  - reescribir historia que ya está en GitHub.
- **En GitHub Free con repo privado no hay protección de ramas** (la API devuelve 403). Estas normas
  solo se cumplen si las cumplen Claude y el equipo.

## Skills y agente

| skill | para qué |
|---|---|
| `/empezar <tarea>` | actualiza `main` y crea la rama con nombre convencional |
| `/subir` | limpia notebooks, revisa, hace el commit con tu autoría, push y PR con plantilla y reviewers |
| `/actualizar` | trae lo último de `main` a tu rama; si tu PR ya está mergeada, vuelve a `main` y borra la rama |
| `/revisar-pr <n>` | para Ismael y David: revisa una PR con el agente `revisor`, aprueba o pide cambios, y mergea |
| `/sincronizar-upstream` | trae las correcciones de Metrica en una rama `sync/` con su PR |
| `/evaluar [csv]` | valida y puntúa una entrega, solo agregados |
| `/decision <título>` | apunta una decisión de método en `docs/decisiones.md` |

**Agente `revisor`** (`.claude/agents/revisor.md`): revisa un diff contra nuestras reglas (datos,
constantes de frames, determinismo, rutas, interfaz, ficheros oficiales, autoría) y devuelve 🔴/🟡/💭
con fichero y línea. Solo lee, nunca edita. Úsalo antes de `/subir` si el cambio toca código del
pipeline; `/revisar-pr` lo usa siempre.

---

## Estrategia propuesta (punto de partida, no dogma)

El análisis completo, las alternativas y la recomendación están en `docs/investigacion_metodos.md`.

1. **Limpieza del balón:**
   - interpolar huecos cortos;
   - descartar saltos físicamente imposibles;
   - marcar cuándo el balón sale de los límites del campo (x o y fuera de [0, 1]).
2. **Detector de balón muerto (`D`)**, combinando:
   - balón fuera de los límites;
   - los `SET PIECES` del Smart Tagging como marca del reinicio (ahí termina el `D`);
   - jugadores parados o velocidad media de los jugadores baja;
   - posiciones típicas de córner o saque de banda;
   - el tramo inicial de la 2ª parte (110.808–113.741).

   **Que te falte el balón no significa que esté muerto.**
3. **Candidato de posesión por frame:**
   - equipo del jugador más cercano, con un umbral de distancia en metros;
   - control = balón lento cerca del mismo equipo durante varios frames, o pases consecutivos de ese
     equipo;
   - un toque o un rebote no es control;
   - sin balón, usar señales colectivas (forma del equipo, quién presiona y quién se despliega) y el
     equipo de la fase del Smart Tagging como prior.
4. **Modelo temporal sobre {H, A, D}:** HMM/Viterbi o máquina de estados con histéresis y un coste por
   cada cambio de estado. **Es lo que más mueve el spellF1.**
5. **Política de `X`:** solo fuera de los tramos evaluados. Dentro, también en las oclusiones largas,
   se escribe siempre una etiqueta: repetir la anterior da el mismo spellF1 que una `X` y un macroF1
   igual o mejor.
6. **Vídeo y broadcast:** dejarlos para el final, si sobra tiempo. Son caros de procesar y hay poco
   tiempo.

## Reparto y calendario

| área | responsable | qué hace |
|---|---|---|
| Infraestructura y entrega | Ismael | repo, pipeline de un comando, reproducibilidad, validación, formulario |
| Balón muerto `D` y reinicios | por asignar | límites, Smart Tagging, patrones de jugadores parados |
| Modelo de posesión | por asignar | candidato por frame, control frente a toque, modelo temporal |
| Validación externa | por asignar | datos abiertos, degradación, harness de experimentos |
| Documento técnico | todos (+ Ana), con Ismael como dueño | se va escribiendo durante la semana |

| día | objetivo |
|---|---|
| **mar 10** | repo privado, entorno, datos en local, baseline reproducido, todo el equipo ha leído la documentación |
| **mié 11** | exploración por áreas, interfaz común acordada, normas del repo y configuración de Claude, harness de validación externa empezado |
| **jue 12** | primera versión de `D` y de posesión. **Primera entrega validada que bata el baseline** |
| **vie 13** | modelo temporal integrado y experimentos con la validación externa |
| **sáb 14** | llegan las instrucciones de entrega: revisar el formulario y las cuentas de Google. Empezar el documento técnico |
| **dom 15 – lun 16** | iterar. **Congelar la versión el lunes por la noche** y comprobar la reproducción exacta en una máquina limpia |
| **mar 17** | hacer público el repo, validar el fichero exacto y **enviar con margen**. El formulario se puede editar hasta las 23:59 CET |

## Checklist de entrega

- [ ] `<NOMBRE_EQUIPO>.csv`: 199.319 filas y `validate_submission.py` en verde **sobre ese mismo
      fichero**.
- [ ] Repo **público** que regenera **exactamente** el mismo CSV con un solo comando, sin datos ni CSV
      dentro.
- [ ] `<NOMBRE_EQUIPO>.pdf` o `.md` que explique:
  - el enfoque y por qué;
  - los datos usados y los descartados;
  - los datos de entrenamiento y su origen;
  - las reglas de posesión implementadas;
  - las limitaciones;
  - cómo reproducirlo.
- [ ] El nombre de equipo del formulario es el mismo que pusieron todos al inscribirse.
- [ ] Hay una cuenta de Google para subir los ficheros. Se envía una sola respuesta por equipo y cuenta
      la última.
- [ ] Antes de hacer público el repo:
  - `git log --all --stat` sin ningún `BAR-ATH_*` del partido ni CSV de entregas;
  - notebooks sin outputs;
  - `CLAUDE.md` y `docs/` revisados.

Dudas sobre datos y métricas: abrir un issue en el repo de la organización. Dudas sobre inscripción y
términos: hackathon.talentarena@mobileworldcapital.com.
