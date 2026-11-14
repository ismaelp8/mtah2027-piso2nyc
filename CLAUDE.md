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
| Ismael Pintor | `ismaelp8` | infraestructura y entrega (esqueleto, harness, integración), reviewer, dueño del documento técnico |
| David Ortega | `ortegafer` | decodificador (`possession/temporal.py`), reviewer |
| Antonio Azuer | `antonioazuero11-wq` | evidencia de equipo y limpieza del balón (`possession/candidates.py`, `possession/ball.py`) |
| Manuel Herrero | `manuelherrero` | `D`: fronteras y anclas (`possession/dead_ball.py`) |
| Ana Aparicio | — | `D`: estado (`possession/dead_state.py`) y documento técnico |

Qué tiene que hacer cada uno hasta la entrega: [`docs/PLAN_ENTREGA.md`](docs/PLAN_ENTREGA.md).

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
   en `main`, propón `/empezar`, salvo que sea Ismael: él puede trabajar directo en `main`.
4. **Ponte al día con «Dónde estamos»** (justo debajo) antes de proponer trabajo. Si la persona no lo
   conoce, resúmeselo en unas líneas: qué está hecho, qué falta y qué hace falta de ella.

---

## Dónde estamos (actualizado el 14/11/2026)

Lee esto para saber en qué punto está el equipo. El detalle está en los ficheros enlazados.

**Hecho:**

- **Experimento 0** (`validation/resultados/2026-11-11_experimento0.md`; bitácora en
  `validation/experimento0/`): el flag de la Bundesliga (DFL) frente a `CHALLENGE.md`.
  - **`D` de la DFL: vale tal cual.** Hay que tapar el balón en los frames `D` y en las ventanas que
    tocan sus bordes: la DFL congela su posición mientras está muerto y la hace saltar al reanudar.
  - **Equipo (H/A): no vale tal cual.** El flag cambia en el primer toque del rival, aunque no controle.
  - **Decisión de Ismael** (12/11, `docs/decisiones.md`): se siguen las normas del reto. Las etiquetas
    de equipo de la DFL se derivan con un criterio de control.
- **Experimento 1** (`validation/resultados/2026-11-12_criterio_posesion.md`; bitácora en
  `validation/experimento1/`): cuándo cambia la posesión y con qué control corregir la DFL.
  - **Hay tres lecturas:**
    - último toque (el flag de la DFL);
    - toque con impacto significativo (las definiciones de eventos de Metrica);
    - control establecido (el texto del reto y StatsBomb).

    El texto del reto apunta a la tercera.
  - **Referencia sin circularidad:** los eventos humanos de la DFL (pases completados, recuperaciones y
    duelos con `PossessionChange`).
  - **Cuánto pesa:** la definición de control mueve entre un tercio y dos tercios de las posesiones.
    Hay una candidata, "control de 12 frames o dos toques seguidos", con un compromiso medido; no es una
    ganadora.
  - **Fuera no hay nada hecho:** ningún método abierto da posesión de equipo por frame con criterio de
    control. Se construye con piezas propias.
- **Recuento a ojo del vídeo de la ventana** (Manu y Antonio, 12–13/11; PR #1, todavía abierta, rama
  `exp/recuento-video-ventana-publica`, secciones 16 y 17 de la bitácora del experimento 1):
  - una señal de que la GT da la posesión con un toque sin control (1 caso claro y 1 discutible);
  - el protocolo de Antonio para contar frame a frame (sección 17);
  - no se completó.
- **Experimento 2** (14/11, `validation/resultados/2026-11-14_experimento2_convencion_tracking.md`;
  bitácora y regla de lectura en `validation/experimento2/`): el recuento hecho con el tracking en vez de a
  ojo.
  - **El instrumento** usa las medidas de toque y control de los experimentos 0 y 1. En la DFL distingue
    "la etiqueta cambia en el toque" de "exige control", salvo si el balón se pierde en todas las disputas
    o tiene mucho ruido.
  - **En la ventana queda sin decidir**, por la regla fijada antes. Ismael lo ejecutó con
    `validation/partido/recuento_ventana.py`. El detector de toques casi no ve toques en el ATD: 2,2 por
    minuto, frente a 20–38 en la DFL. No es por falta de balón: en la ventana se ve el 93,5 % del juego.
  - **Por qué** [inferencia, apoyada en la DFL]: el balón del ATD se comporta como uno **suavizado en
    torno a 1 s**. En la DFL, una media móvil de 25 frames reproduce su temblor y sus toques y controles
    por minuto.
  - **Qué implica:**
    - nada que dependa de cambios bruscos de la velocidad del balón, calibrado en la DFL, sirve tal cual
      en el ATD; la proximidad al balón sí aguanta;
    - la degradación DFL→ATD tiene que suavizar el balón.
  - **La regla del temporizador de Antonio** apenas cambia las etiquetas de la DFL: con 10 frames de
    margen siguen 6,0 cambios por minuto vivo, frente a 2,78 exigiendo control.
  - **La convención sigue sin medir.** Se mantiene la decisión del 12/11: exigir control.
- **Balón muerto** (Manuel, con la revisión de la sesión de Ana, 12–13/11; mergeado el 14/11):
  - qué hay: `possession/dead_ball.py` v1, que marca el tramo antes del saque de la 2ª parte, y
    `possession/io.py`, el lector del ATD del pipeline;
  - diagnóstico del balón del ATD (`validation/resultados/2026-11-12_balon_muerto_atd.md`) y revisión
    (`2026-11-13_revision_balon_muerto.md`): el `D` suma por la precisión de sus fronteras (≤ 1 s), no
    por cubrir frames; hay una propuesta de v2 por capas;
  - el sondeo del silbato en el audio, en `validation/silbato/`;
  - el detalle y las decisiones están en `docs/decisiones.md` (12/11 y 13/11).
- **Esqueleto del pipeline** (14/11): `possession/` corre de punta a punta con la versión más simple de
  cada pieza (`tracking`, `ball`, `candidates`, `dead_state`, `dead_ball`, `temporal` y `pipeline`).
  - Se comprueba sin datos del partido con `python validation/scripts/prueba_pipeline.py`.
  - La entrega la genera una persona con `python -m possession.pipeline`.
  - Los valores por defecto están sin ajustar.
- **Harness de la DFL** (14/11, `validation/harness/`; primera medida en
  `validation/resultados/2026-11-14_harness_dfl.md`): puntúa el pipeline en los 7 partidos abiertos con
  el scorer oficial, en medio minuto. Lo puede ejecutar Claude.
  - Mide con las dos convenciones de etiquetas, en tres condiciones del balón y frente al baseline, con
    el `D` copiado de las etiquetas.
  - **Quién gana depende de la convención.** Con las etiquetas corregidas por control, el Viterbi con
    coste 25 gana al voto del baseline por más de 0,10 en los 7 partidos; con el flag tal cual, empata o
    pierde por poco. Con la regla de §5.8 no gana ninguna versión.
  - **Ese +0,10 está inflado por construcción:** las etiquetas de control salen de una regla de
    proximidad, parecida a lo que se mide. El flag es el mismo tipo de etiqueta que la GT del reto: lo
    que no aguante con el flag no cuenta.
  - El `D` no se puede validar ahí con el balón.
  - **Desde el 14/11 por la noche, la degradación imita al balón del ATD** (ver el punto siguiente).
    Los números de esta primera medida, con la condición de antes, ya no deciden.
- **Perfil del balón del ATD y harness «como el ATD»** (14/11; `validation/resultados/2026-11-14_perfil_atd.md`
  y `2026-11-14_harness_como_el_atd.md`). Ismael ejecutó el perfil y se leyó con una regla fijada antes.
  - **El ATD casi no tiene huecos cortos:** pierde el balón en bloques de 5 s o más, como la DFL con
    solo los `D` tapados [medido]. La mayor parte de su 41 % sin balón sería balón muerto [inferencia].
    El balón viene suavizado unos 25 frames [medido].
  - **Votan dos condiciones:** «como el ATD» (microcortes, el 11,3 % del juego en bloques de 5 a 15 s y
    suavizado 25) y «como el ATD, sin bloques». `limpio` y la condición de antes se puntúan sin voto.
  - **Con el flag, el Viterbi de `main` gana al baseline por +0,022 en 7 de 7** (antes perdía), pero no
    llega al +0,03 de §5.8.
  - **El harness ya puede decidir** el orden entre evidencias de equipo y lo que use la velocidad del
    balón.
  - **Para sustituir lo que hay en `main`,** un candidato tiene que ganar al control y a `main`
    (decisión de Ismael, 14/11).
  - **Cada uno prueba sus versiones sin tocar `puntuar.py`:** con un JSON en
    `validation/harness/versiones/` y `--versiones` (README del harness). `--eventos` añade los eventos
    humanos de la DFL, como referencia descriptiva.

**Lo siguiente: el plan hasta la entrega** ([`docs/PLAN_ENTREGA.md`](docs/PLAN_ENTREGA.md), decidido por
Ismael el 14/11). Sustituye al orden anterior, que dejaba el modelo temporal para el final.

- **Un solo pipeline con cinco piezas y una persona por pieza,** todas a la vez:

  | pieza | quién | fichero |
  |---|---|---|
  | esqueleto, harness de la DFL, integración y entrega | Ismael | `possession/pipeline.py`, `validation/harness/` |
  | decodificador | David | `possession/temporal.py` |
  | `D`: fronteras y anclas | Manuel | `possession/dead_ball.py` |
  | `D`: estado; documento técnico | Ana | `possession/dead_state.py` |
  | evidencia de equipo y limpieza del balón | Antonio | `possession/candidates.py`, `possession/ball.py` |

- **Cada persona sustituye su pieza sin tocar las demás.** La interfaz está en `possession/tracking.py` y
  en la sección 2 del plan.
- **Qué versión entra lo decide el harness de la DFL,** nunca la ventana pública (sección 4 del plan).
- **La medida del balón del ATD está hecha (14/11),** y la degradación del harness se calibró con ella
  (punto anterior).
- **La convención sigue siendo "exigir control".** El harness puntúa con las dos: el flag y la corregida.
- **Corte: lunes 16 a las 14:00.** Lo que no haya ganado en el harness no entra.

**Si quien abre la sesión no sabe cuál es su pieza,** enséñale su parte de la sección 3 del plan antes de
proponer nada.

**Pendiente de permiso de Ismael:**

- descargar los tiempos humanos de ELASTIC, en 3 partidos de la DFL;
- instalar `databallpy`.

**Cómo se trabaja en `validation/`:**

- los criterios se escriben antes de medir;
- placebos y sensibilidad;
- resultados por partido y con los 7 juntos;
- cada afirmación con [medido], [inferencia] o [sin verificar];
- los scripts de `validation/partido/` leen el partido: los escribe Claude, los ejecuta una persona y
  solo se pegan agregados. Una ejecución sobre la ventana pública se lee con una regla fijada antes, y
  nunca sirve para elegir parámetros.

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
  PLAN_ENTREGA.md            quién hace qué hasta la entrega, la interfaz de las piezas y el calendario
  decisiones.md              registro de decisiones (materia prima del documento técnico)
  investigacion_metodos.md   análisis de métodos, alternativas y recomendación
possession/                  el pipeline: una pieza por fichero, y pipeline.py, que genera la entrega
validation/                  validación externa con datos abiertos: pasos, scripts y resultados agregados
  harness/                   el harness de la DFL: puntúa el pipeline en los 7 partidos abiertos
```

**Lo previsto:** `notebooks/` para la exploración, siempre sin outputs.

## Convenciones de código

- **Módulos pequeños** con funciones puras de numpy y pandas.
- **Deterministas:**
  - semillas fijas;
  - nada que dependa del orden en que aparecen los ficheros ni de la hora.

  La entrega tiene que regenerarse **byte a byte**.
- **Sin rutas fijas.** Todo pasa por `games.py` (`games.asset_paths()`, `games.GAMES`,
  `games.half_video_blocks()`), y los datos se localizan con `MTAH_DATA_DIR`.
- **Interfaz común** (`possession/tracking.py` y `docs/PLAN_ENTREGA.md` §2):
  - cada pieza recibe un `Tracking`: arrays indexados por **frame de vídeo**, **199.319** en el partido.
    No recibe rutas ni abre ficheros; solo `possession/dead_ball.py` usa además los del partido, con las
    rutas de `games.asset_paths()`;
  - las piezas de evidencia devuelven `(score, allowed)`: dos arrays de forma (n, 3), con las columnas
    `H`, `A` y `D`;
  - el decodificador devuelve una etiqueta por frame de vídeo.

  Así las piezas se combinan sin pelearse por la alineación, y el mismo código corre en el partido y en
  la DFL del harness.
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
    - **Experimento 0 hecho** (12/11):
      - su `D` vale tal cual, tapando el balón en los `D` y en sus bordes;
      - su flag de equipo cambia en el primer toque del rival, así que las etiquetas de equipo se
        derivan con un criterio de control.

      Ver «Dónde estamos».
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

- **Solo Ismael (`ismaelp8`) hace commit y push directo a `main`** (`CONTRIBUTING.md` §5). Compruébalo
  con `gh api user --jq .login`.
  - Con cualquier otra persona, nunca: cada tarea va en su rama `tipo/descripcion` (`/empezar`) y entra
    por PR.
  - Con Ismael, antes del push: `git fetch origin` y, si GitHub va por delante,
    `git pull --rebase --autostash origin main`. Si quiere que le revise David, rama y PR.
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
| `/subir` | limpia notebooks, revisa, hace el commit con tu autoría, push y PR con plantilla y reviewers; Ismael puede subir directo a `main` |
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

Desde el 14/11 manda [`docs/PLAN_ENTREGA.md`](docs/PLAN_ENTREGA.md): lo que hace cada persona, la interfaz
de las piezas y cómo se decide qué entra.

| pieza | responsable | qué hace |
|---|---|---|
| Esqueleto, harness e integración | Ismael | pipeline de un comando, harness de la DFL, integración diaria, congelado, reproducibilidad, formulario |
| Decodificador | David | costes de cambio, duraciones mínimas y poda |
| `D`: fronteras y anclas | Manuel | inicio y fin de cada parada y equipo que reanuda, con el balón, el Smart Tagging y el silbato |
| `D`: estado | Ana | probabilidad de juego parado por frame, con los jugadores |
| Evidencia de equipo y limpieza del balón | Antonio | proximidad con control, frente al jugador más cercano |
| Documento técnico | Ana desde el lunes, con Ismael como dueño | a partir de `docs/decisiones.md` y `validation/resultados/` |

| día | objetivo |
|---|---|
| **sáb 14** | esqueleto y harness en `main`; todos con la DFL en local; agregados del partido ejecutados; primera entrega de prueba. Revisar las instrucciones de entrega, el formulario y las cuentas de Google |
| **dom 15** | cada pieza itera contra el harness; las PR entran según ganan |
| **lun 16, 14:00** | **corte:** lo que no haya ganado en el harness no entra |
| **lun 16, tarde y noche** | **congelar** y comprobar la reproducción exacta en una máquina limpia. Documento técnico |
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
