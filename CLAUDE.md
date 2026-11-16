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
| Ismael Pintor | `ismaelp8` | infraestructura y entrega (esqueleto, harness, integración), dueño del documento técnico |
| David Ortega | `ortegafer` | decodificador (`possession/temporal.py`) |
| Antonio Azuer | `antonioazuero11-wq` | evidencia de equipo y limpieza del balón (`possession/candidates.py`, `possession/ball.py`) |
| Manuel Herrero | `manuelherrero` | `D`: fronteras y anclas (`possession/dead_ball.py`) |
| Ana Aparicio | — | `D`: estado (`possession/dead_state.py`) y documento técnico |

Qué tiene que hacer cada uno hasta la entrega: [`docs/PLAN_ENTREGA.md`](docs/PLAN_ENTREGA.md).

- **Si alguien delega el git en Claude** (lo dice en su `CLAUDE.local.md` o lo pide en la
  conversación), hazlo tú con las skills. Explica cada paso en una frase sencilla, sin jerga, y pide
  confirmación antes de subir nada.
- **Cualquiera del equipo puede contestar una duda, tomar una decisión y revisar, aprobar o mergear la PR
  de otra persona** (decisión de Ismael, 15/11). Ismael no es una puerta: Claude no frena a nadie por no ser
  él.
  - Donde este brief, el plan, una bitácora o un comentario del código digan «lo decide Ismael», «se le
    pasa a Ismael» o «pendiente de permiso de Ismael», léelo como «lo decide el equipo».
  - Quien decide lo apunta en `docs/decisiones.md` (`/decision`), con su nombre y el porqué.
  - Lo que viene después de una decisión no cambia: si toca `pipeline.PIECES`, un valor por defecto o código
    que usa la entrega, alguien regenera la entrega y la valida.
- **Cada uno puede mergear su propia PR,** sin esperar una aprobación. Si quiere otra opinión, se la pide a
  quien esté disponible.
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

## Dónde estamos (actualizado el 16/11/2026)

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
  - **Reproducible:** Ismael (Windows) y un compañero (Linux) sacaron el mismo sha256 de `equipo_v0`.
- **Pieza de `D` de estado de Ana en `main`** (PR 5, 14/11; `validation/resultados/2026-11-14_d_estado.md`
  y `2026-11-14_agregados_jugadores_atd.md`).
  - El modelo E2, con los jugadores, opina en la columna `D`. Los agregados del ATD dicen que se traslada.
  - **Entrega `equipo_v1`** (Ismael, con `main` en `4738082`): válida, con el 43,4 % de `D` en los frames
    evaluados, 111 paradas y sha256 `c7d3dd31…647d`.
  - En la ventana pública ya marca el `D` (F1 de `D` 0,77). La ventana solo dice que no está rota; no
    elige.
- **Evidencia de equipo y limpieza de Antonio en `main`** (PR 6, 14/11): N2 y la retención pierden
  frente a `main` con el flag, así que se quedan como opciones (`candidates.evidence(trk, method=...)`). La
  limpieza va como variante (`ball.clean_v1`): empata en el harness, que no puede ver los saltos falsos del
  ATD. La entrega no cambia.
  - **El arreglo de la limpieza está en `main`** (PR 7, 15/11): `ball.clean_v1` ya está corregida y tiene
    sus pruebas (`validation/scripts/prueba_limpieza.py`). Sigue empatando con `main` en el harness, y en el
    partido cambiaría el 0,23 % de los frames con balón [medido por Antonio].
  - **No está encendida:** `ball.clean` devuelve el balón tal cual y la entrega no cambia. Encenderla
    obligaría a medir o reentrenar B5 y a repetir la medida de Manuel, que se hicieron con `ball.clean` v0.
- **La evidencia de equipo de la entrega es B5 desde el 14/11 por la noche** (apuesta B de Ismael;
  `validation/resultados/2026-11-14_apuesta_b.md` y `docs/decisiones.md`).
  - **Qué es:** un modelo aprendido en la DFL, con la proximidad al balón y la forma de los equipos, decide
    entre `H` y `A`. Frente al `D` empuja como N1, para no tapar la pieza de Ana.
  - **Cumplió los tres criterios fijados antes de medir:**
    - gana al control y a N1 con §5.8;
    - con la pieza de Ana ve tantas paradas como N1;
    - aguanta con el balón a la vista en las paradas.
  - **En el harness** la fila por defecto («Viterbi, coste 25 (v0)») es ya B5: 0,498 / 0,512 con el flag.
  - **Entrega `equipo_v2`** (Ismael, 15/11, con `main` en `962bddd`): válida, con el 44,4 % de `D` en los
    frames evaluados, 114 paradas, 219 posesiones de 16,1 s de media (la v1 tenía 321 de 11,2 s) y sha256
    `864ef3d9…5007`.
    - **Reproducible:** sale el mismo sha256 dos veces en Windows y una en Linux. En esas dos máquinas, el
      `np.exp` de B5 no cambia el resultado.
    - En la ventana pública no se rompe nada: el `D` acierta los mismos frames que la v1.
  - **Pierde recuperaciones** en los eventos humanos. Lo ajusta David con los costes, que ahora se miden
    en la escala de B5.
- **Fronteras de `D` de Manuel en `main`** (PR 8, 15/11; `validation/resultados/2026-11-15_agregados_dead_ball.md`
  y `docs/decisiones.md`).
  - **Qué hace:** si el balón desaparece entre 5 y 60 s antes de un `SET PIECES` del Smart Tagging que no
    es un saque inicial, empuja ese hueco hacia `D`. Solo puntúa: no prohíbe nada.
  - **Cómo se decidió:** con una regla fijada antes de medir, que Manuel ejecutó en el partido. El harness
    no puede decidirlo, porque la DFL no tiene Smart Tagging.
  - Su peso (`GAP_SCORE` = 1) está sin ajustar y va con los costes `to_dead` y `from_dead` de David.
  - Se midió con `ball.clean` v0. Si se enciende la limpieza de Antonio, hay que repetir esa medida y medir
    B5, que se entrenó con el balón de `ball.clean` v0.
  - Desde esta PR la entrega usa el Smart Tagging, y `pipeline.build` lo pide al arrancar.
- **Decodificador de David en `main`** (PR 9, 15/11; `docs/decisiones.md`): la duración mínima y la poda
  quedan como opciones de `possession/temporal.py` (`decode_min` y `decode_prune`). Empatan con `main`, así
  que la entrega no cambia.
  - **Su diagnóstico** (`validation/scripts/diagnostico_spell.py`, descriptivo): con una evidencia perfecta
    el decodificador casi no pierde nada. La mayor pérdida está en la evidencia de equipo con el balón a la
    vista, sobre todo en recuperaciones y posesiones de 2 a 5 s; la segunda, en el `D` propio.
- **Entrega vigente: `equipo_v9`** (16/11 por la noche): `equipo_v8` más «cortas a `D`»
  (`temporal.decode_cortas_a_d`, en `pipeline.PIECES` desde el 16/11; Ismael: «si enciendela»; `docs/decisiones.md`).
  - Es la entrega de prueba `prueba_cortas_a_d`: sha256 `d9706dfb…be63`, válida, con 201 posesiones de 17,0 s de
    media, 116 paradas y el 46,2 % de `D` en lo evaluado. Ismael la generó en el entorno limpio y Manuel en su
    máquina, y sale igual.
  - Frente a `equipo_v8` cambian 1.167 frames, todos de un equipo a `D` (609 de `H` y 558 de `A`).
  - **Falta que Ismael la regenere con `main` ya encendido:** `python -m possession.pipeline --name equipo_v9`, con
    el python del entorno limpio, tiene que dar esa huella.
  - **En el harness:** con el `D` de las etiquetas, la fila por defecto no cambia (la salida es idéntica antes y
    después). Con el `D` propio, sí: 0,416 → 0,414 con el flag y 0,616 → 0,623 con control («como el ATD»). Quien
    compare con «main» usando el `D` propio fija `main` en `3220707` o vuelve a medir su referencia.
- **Entrega anterior: `equipo_v8`** (Ismael, 16/11, con `main` en `44678d1`): `equipo_v5` más la capa del balón
  fuera (D7, más abajo). Es válida, con 219 posesiones de 15,8 s de media, 116 paradas, el 45,4 % de `D` en lo
  evaluado y sha256 `d78c514d…e2b2`.
  - **El ensayo del 16/11 por la noche pasa** (Ismael, entorno limpio, Python 3.13.9 y numpy 2.5.4, con `main` en
    `c6a3dee` y sin cambios locales): el mismo sha256, 0 conflictos, ninguna racha corta y el validador en verde.
    `main` ya llevaba la PR 20 («cortas a `D`», apagada), así que esa PR no cambia la entrega.
  - Sale byte a byte igual que `prueba_d7_v5`, la entrega de prueba.
  - Frente a `equipo_v5` cambian 574 frames, todos de un equipo a `D` (331 de `H` y 243 de `A`), con 3 paradas
    más. Los 817 cambios de la capa de los contraataques siguen enteros.
  - En la ventana pública, el spellF1 no cambia (0,658) y el macroF1 sube de 0,851 a 0,865. No elige nada: con 17
    posesiones, una diferencia de hasta 0,39 es ruido.
  - **Reproducida en otra máquina** (Antonio, 16/11): el mismo sha256 en un Mac M1 (macOS, ARM), con Python 3.13.7
    y numpy 2.5.4, tres veces y sin cambios locales.
- **Antes: `equipo_v5`** (Ismael, 15/11, en el entorno limpio con `main` en `2f34a7f`): `equipo_v3`
  más la capa de los contraataques (más abajo). Es válida, con 219 posesiones de 15,9 s de media, 113
  paradas, el mismo `D` que `equipo_v3` y sha256 `27dc8aa8…efb7`.
  - Sale byte a byte igual que `prueba_transiciones2`, que se generó con numpy 2.3.4.
  - Frente a `equipo_v3` cambian 817 frames, todos de un equipo al otro.
  - Con `main` en `b027409` (después de las PR 15, 10 y 16), `equipo_v7` sale igual.
  - **Reproducida en otra máquina:** sale lo mismo (Ismael, 16/11).
- **Antes: `equipo_v3`.** La generó Ismael el 15/11, con `main` en `6e8fb27`: válida, con el 45,1 % de `D`
  en los frames evaluados, 113 paradas, 215 posesiones de 16,2 s de media y sha256 `9539ce42…cc17a`.
  - Es la misma, byte a byte, que sacó Manuel en su máquina: reproducida en dos máquinas.
  - La PR 9 no la cambia: regenerada con `main` en `86ddcbb`, sale el mismo sha256.
- **Lector y comando de la entrega** (Ismael, 15/11, `d6bd128`; tareas 2 y 3 de su bloque del plan). No
  cambian ninguna etiqueta.
  - **El lector del ATD** (`possession/io.py`) cuenta las líneas leídas y las saltadas, y los frames sin
    línea. Si una línea no se puede leer, el error no enseña el valor.
  - **`python -m possession.pipeline`** imprime:
    - las versiones de Python y numpy;
    - ese recuento;
    - las rachas de menos de 12 y de 25 frames por tramo.

    Con piezas en conflicto, no escribe el CSV.
  - **En el partido** (Ismael lo ejecutó): 199.319 líneas, todas válidas; 0 saltadas o repetidas y 0
    frames sin línea. Desde entonces, cualquier línea rara es un error y no se genera la entrega.
  - **No hay rachas cortas:** ninguna de menos de 12 ni de 25 frames en los dos tramos.
- **Ronda única de reentrenamiento de B5: empate** (15/11; `docs/decisiones.md` y
  `validation/resultados/2026-11-14_apuesta_b.md` §11). Por la regla de parada se cerró la evidencia de
  equipo; **Ismael la reabrió el mismo día** (punto siguiente). B5 sigue en la entrega y `pipeline.PIECES` no
  cambia.
  - **Los candidatos:** B6 (sin las ventanas de 151 frames), B7 (más peso cerca de los cambios) y B8 (con
    el evento de toque).
  - **Ninguno cumple los tres criterios** fijados antes de medir. El que más se acerca es B7: mejora las
    recuperaciones y los duelos con cambio, y gana +0,012 y +0,015 con el flag, pero no llega al +0,03 de
    §5.8 y con el control no se mueve.
  - **Sus coeficientes quedan en `possession/aprendida.py`.** Los de B1 a B5 no cambian.
  - **`validation/partido/slots_duplicados.py`** dice si el ATD duplica a algún jugador. Se ejecutó el 16/11
    (punto «16/11», más abajo).
- **La evidencia de equipo está reabierta** (Ismael, 15/11): «Es claro que tenemos un problema en que
  predecimos muchas menos posesiones de las que hay, sobretodo cuando son posesiones cortas.»
  - **B5 sigue en la entrega** como evidencia de equipo; la entrega vigente es la de arriba.
  - **El estudio de las posesiones cortas está en `main`** (`4305576`;
    `validation/resultados/2026-11-15_posesiones_cortas.md` y `validation/posesiones_cortas/BITACORA.md`).
    La rama `claude/posesiones-cortas-5e84f8` se conserva en GitHub, porque sus commits prueban que las reglas
    iban antes de medir. Lo que dice [medido en datos abiertos]:
    - **Con el flag, tres cuartos de lo que no encontramos son toques del rival sin control.**
    - **`main` saca un ritmo casi fijo de posesiones,** sea cual sea la GT. Con el control de la DFL, el
      número cuadra (4,50 por minuto vivo frente a 4,71). En SkillCorner, que también exige control, falta
      un 30 % (4,25 frente a 6,05).
    - **B9, que es B5 más la dirección en que se mueve el balón, empata.** Gana con el flag (+0,039 y
      +0,048), pero empata con el control, empeora los duelos sin cambio más de lo permitido y no mejora en
      SkillCorner (−0,005 y +0,004). Queda en `aprendida.py`, fuera de `PIECES`. **Ismael se queda con B5**
      (`5fc02b8`). La entrega de prueba con B9 cambia poco: 216 posesiones frente a 215.
    - **Las fases 2 y 3 se cerraron sin candidato.** Quitar las posesiones inventadas no llega a +0,03 ni
      con un oráculo, y una red de una capa con los mismos rasgos no gana con el control ni en SkillCorner.
    - **La fase 4 tampoco abre nada** (`a950880`; `docs/decisiones.md`):
      - el déficit de posesiones no es propio del partido: con nuestro `D`, 4,29 y 4,26 por minuto en la DFL
        y 4,11 en SkillCorner, y las 3,7 del partido caen dentro;
      - una pista de equipo de fuera, como las fases del Smart Tagging, daría poco, y solo con un alcance
        mayor que el del plan;
      - H3 y H5 del visionado no concluyen: en el partido, nuestros cambios no se juntan con los huecos del
        balón más que en la DFL. No se abre ninguna degradación nueva antes de la entrega.
  - **La entrega no cambia con B9** [medido sin datos del partido]: los rasgos de B2, los coeficientes de B1 a
    B8 y `evidence_b5` son idénticos, y la huella del partido inventado es la misma. Ismael la confirma al
    regenerar.
- **Tres exámenes de B5 en datos abiertos** (15/11, `main` en `bb4f2ef`). El pipeline de la entrega, tal
  cual, con el `D` de las etiquetas:
  - **SkillCorner** (`validation/skillcorner/`; `validation/resultados/2026-11-15_skillcorner.md`): 20
    partidos de la A-League con tracking automático de retransmisión.
    - `main` gana al baseline por +0,131 (20 de 20) y a N1 por +0,059 (19 de 20).
    - Está partido en dos: 10 partidos para diagnosticar o entrenar y 10 de examen que no se tocan
      (`lector.ENTRENAMIENTO` y `lector.EXAMEN`).
  - **Metrica** (`validation/metrica/`; `validation/resultados/2026-11-15_metrica.md`): 3 partidos.
    - `main` gana al baseline por +0,118 (3 de 3) y a N1 por +0,058 (2 de 3).
    - Las etiquetas salen de sus eventos, así que no sirven de referencia para la convención.
  - **Diagnóstico de errores** (`validation/scripts/diagnostico_errores.py`;
    `validation/resultados/2026-11-15_diagnostico_errores.md`), en la DFL y en la mitad de SkillCorner:
    - casi nunca partimos una posesión, pero cambiamos de equipo de menos: con el flag, 1.661 cambios frente
      a 3.061 en la DFL, y 2.270 frente a 3.228 en SkillCorner;
    - solo entre el 16 y el 37 % de los cambios reales tiene uno nuestro a menos de 1 s (en el placebo, el
      2 %);
    - los dos bordes de las paradas detectadas valen como mucho 0,05–0,07 en la DFL.
  - **`validation/partido/ver_ventana.py`** dibuja la GT pública y una entrega para verlas junto al vídeo. Lo
    ejecuta Ismael.
- **Retraso del balón del ATD** (Antonio, PR 11, 15/11; `validation/resultados/2026-11-15_retraso_balon.md`
  y `docs/decisiones.md`). Es su tarea 1, cerrada.
  - **El balón llega unos 4 frames tarde respecto a los jugadores** [medido por Antonio en el partido, solo
    agregados]: de +2 a +5, con +3 y +4 en las dos partes. El riesgo de la revisión, unos 12 frames, queda
    descartado.
  - **No ve un retraso que compartan el balón y los jugadores** respecto al vídeo: la medida es relativa.
  - **En el harness, ese retraso cuesta entre −0,007 y +0,002:** es un empate. `ball.advance_ball` entra
    **apagada**: `ball.clean` y `pipeline.PIECES` no cambian.
  - **La entrega no cambia:** el código de antes es idéntico y solo se añade la función. Se confirma al
    regenerar en el ensayo del lunes.
- **Las fases del Smart Tagging como pista de equipo** (tarea 2 de Antonio, PR 13, `4ceff85`): la tabla de
  fases vale, y llegamos de 2 a 10 s tarde en 17 de los 24 contraataques. Con la cota de la DFL, ningún uso
  llega a +0,03.
  - **Capa apagada `transiciones.evidence`** (PR 14, `9f89d10`): suma 8 por frame al equipo de cada «Attacking
    Transition» durante sus 5 primeros segundos, y lo mismo a `D`, así que solo empuja contra el otro equipo.
  - Antonio escribió cuatro criterios antes de generar nada (`docs/decisiones.md`). **La primera versión los falla:**
    crea 18 paradas, así que se queda apagada.
  - **La segunda, `transiciones.evidence_equipo`** (`5920c7f`), pone el peso solo al equipo de la fase y **pasa los
    cuatro:**
    - cambian 817 frames, todos de un equipo al otro;
    - las paradas no se mueven y hay 4 posesiones más.
  - **Encendida desde el 15/11** (Ismael: «Sí, enciéndela»): `pipeline.DELIVERY_LAYERS`. Es una excepción a la
    regla del harness, porque la DFL no tiene Smart Tagging.
  - **La entrega cambia:** es `equipo_v5` (arriba), igual byte a byte que `prueba_transiciones2`. La excepción
    de que abre ficheros del partido está en `possession/tracking.py` y en el plan (§2).
- **D7, el balón fuera del campo como señal de `D`** (`docs/decisiones.md`; capas en `possession/dead_ball.py`):
  - **El recuento del partido la deja abierta:** con `equipo_v3` llegamos tarde en 23 de 47 rachas en que el
    ATD ve el balón fuera. En SkillCorner, un balón visto fuera es `D` el 93–94 % de las veces.
  - **Primera versión, `ball_out`: se queda apagada.** Con ella llegamos tarde en 12 de 47 (25,5 %), y el
    criterio pedía menos del 15 %. No hace daño: los 574 frames que cambia pasan todos de `H` o `A` a `D`.
  - **Segunda versión, `ball_out_hold`** (`0043a3c`): mantiene la parada hasta que el balón vuelve a verse
    dentro. Su entrega de prueba sale byte a byte igual que la de la primera, así que tampoco cumple el
    criterio 1. Sigue apagada.
  - **`ball_out` encendida desde el 16/11** (`pipeline.DELIVERY_LAYERS`, detrás de la de los contraataques;
    `docs/decisiones.md`, 16/11). Falló su criterio 1 y pasó los dos de daño.
    - **Ismael decidió encenderla igualmente:** ese criterio mide si el problema queda resuelto, no si la capa
      hace daño.
    - Es la segunda excepción a «lo que no ha ganado en el harness no entra»: en la DFL el balón está tapado
      en los `D` y no se puede medir.
    - `pipeline.build` da error si `--capa` repite una capa que ya va en la entrega. El harness no cambia,
      porque `pipeline.run` no usa `DELIVERY_LAYERS`.
- **Entregas de prueba sin tocar `PIECES`:**
  - `python -m possession.pipeline --name <prueba> --pieza nombre=modulo.funcion --capa modulo.funcion`. Con
    el nombre de la entrega da error, y la salida dice qué se ha cambiado.
  - `python validation/partido/probar_entrega.py <prueba> --capa ...` hace la prueba entera en un solo comando:
    genera la entrega, cuenta el balón fuera y la compara con la vigente (`--contra`, hoy `equipo_v9`).
  - Lo ejecuta una persona (regla nº 1).
- **`D` de estado: tareas 1 a 3 de Ana en `main`** (PR 12, `98c38ca`; `docs/decisiones.md`).
  - Las ventanas de `dead_state` ya no cruzan el principio ni el final de los tramos evaluados.
  - `evidence` admite una escala, con 1 por defecto, para la medida de David.
  - Queda apuntada la versión de scikit-learn del entrenamiento (1.7.2).
  - En la DFL, el resultado es idéntico bit a bit, según Ana.
  - La mergeó Ana (cada uno puede mergear su propia PR); la sesión planificadora la revisó después.
  - **La entrega no cambia** [medido por Ismael]. Cambian los rasgos de los 52 primeros y 52 últimos frames de
    cada tramo, pero ninguna etiqueta:
    - `equipo_v4` se regeneró en el entorno limpio con `main` en `8f90dea` y sale byte a byte igual que
      `equipo_v3` (`9539ce42…cc17a`);
    - `validation/partido/comparar_entregas.py` da 0 frames distintos, y el validador da `Valid`.
- **El decodificador de David, al día** (15/11; ya no tiene PR abiertas):
  - **PR 15** (`8cc59e3`): los tramos pasan a tupla al entrar en `temporal._prepare`. Con un generador salía
    todo `X` sin error. Tiene prueba propia, `validation/scripts/prueba_decodificador.py`. La entrega ya
    pasaba los tramos como tupla.
  - **PR 10** (`1ffa7db`): los costes de `D` medidos con el `D` propio. Todo empata, así que se quedan los 25 y
    25 de `main`.
  - Le queda, si quiere, repetir la medida con la escala de Ana a 0,5.
- **El `D` de Manuel y Ana, PR 16** (`5176355`):
  - **El instante del reinicio:** no entra ninguna capa, porque ningún tipo de reinicio tiene un instante fijo.
  - **El juego vivo en el saque de cada parte:** entra en `dead_ball.evidence`. En ese frame no se permite
    `D`. No cambia ningún frame: `equipo_v6` sale con el mismo sha256 que `equipo_v5`.
- **Ninguna de las tres PR cambia la entrega** [medido por Ismael]:
  - `equipo_v7` se regeneró en el entorno limpio con `main` en `b027409` y sale con el sha256 de `equipo_v5`,
    `27dc8aa8…efb7`;
  - el validador la da por válida.
- **Versiones fijadas para el congelado** (15/11, `docs/decisiones.md`): `requirements-entrega.txt`, con
  numpy 2.5.4, pandas 3.1.1 y Python 3.13. `requirements.txt` es oficial y no se toca.
  - numpy 2.5.4 pide Python 3.12 o más, así que la reproducción con Python 3.11 queda descartada.
  - **El entorno limpio** (`C:\Users\34656\.venvs\mtah2027-entrega`) **reproduce `equipo_v3` byte a byte:**
    mismo sha256 `9539ce42…cc17a`, con `main` en `988ce88` y validado.
  - **Con `main` en `4305576`** (después de la PR 11 y del estudio de posesiones cortas), Ismael sacó la misma
    huella. Lo hizo en otro entorno, con numpy 2.3.4, así que la huella también aguanta ese cambio de versión.
  - **Con `main` en `8f90dea`** (después de la PR 12), ya en el entorno limpio, sale otra vez el mismo
    sha256.
  - **El ensayo del lunes por la noche está hecho** (16/11, `main` en `c6a3dee`): sale `d78c514d…e2b2`. Cada
    regeneración va con el python del entorno limpio:
    `C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe -m possession.pipeline`.
    - El comando imprime el commit con el que se genera. Si el código de la entrega tiene cambios sin
      commitear, lo avisa.
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

- **16/11: la investigación, los cierres y la línea del balón del vídeo.**
  - **La investigación del 16/11** (`docs/investigacion_2026-11-16.md`; `validation/investigacion_1116/`):
    - doce sondeos en datos abiertos; ninguno gana a `main` con §5.8;
    - la idea 1.1 (cambios de equipo entre fases del Smart Tagging) se cierra: cuentan 16 cambios y se pedían 30;
    - la 1.2, también: en el 12,9 % de los frames un equipo tiene más de 11 slots (0 % en los abiertos), pero imitado
      en la DFL le cuesta a `main` como mucho 0,008. `ball.clean_slots` se queda apagada;
    - la 1.3, «cortas a `D`» (`temporal.decode_cortas_a_d`, PR 20, `10aadef`), **está encendida desde el 16/11 por
      la noche:**
      - pasa las cuatro condiciones de la regla nueva (punto siguiente), con el examen de SkillCorner usado una vez
        para este candidato, con el corte de 125 frames;
      - en la entrega de prueba de Manuel cambian 1.167 frames, todos de un equipo a `D`, y las posesiones pasan de
        219 a 201;
      - Ismael la reprodujo en el entorno limpio: sale la misma entrega de prueba que a Manuel (sha256
        `d9706dfb…be63`);
      - **Ismael decidió encenderla** («si enciendela»): `pipeline.PIECES["temporal"]` es `decode_cortas_a_d` y la
        entrega pasa a ser `equipo_v9` (arriba);
      - lo que quede pendiente contra `equipo_v8` (la puerta 2.2 del balón del vídeo) vale mientras su entrega de
        prueba se genere sin traer `main`; si se trae, reescribe antes sus límites contra `equipo_v9`;
      - el corte se queda en 125 y el examen de SkillCorner queda cerrado para esta idea.
  - **Decisión de Ismael:** en los cambios pequeños hacia control, el flag pasa de veto a límite de daño
    (`docs/decisiones.md`, 16/11). El examen de SkillCorner se puede abrir una vez por candidato.
  - **Cierres:**
    - PR 17 (Manuel): el instante del reinicio y la tarea 3 de la pieza de `D`;
    - PR 18 (Antonio): los árboles para el estado de `D` (idea 2.4) no ganan. G3 falla en 1 de las 8 celdas y mejora
      los bordes en el criterio del 13/11, pero es más frágil con temblor.
  - **La línea del balón del vídeo** (rama `exp/balon-video`; reglas y resultados en
    `validation/balon_video/BITACORA.md`).
    - **Qué es:** un detector de balón público (YOLO11n, AGPL-3.0), en local y en CPU, en un recorte de 320 px
      alrededor del balón del ATD ampliado ×2. Solo lo vería B5, con una capa apagada (`balon_video.ajuste_b5_video`).
    - **Puerta 0 (datos abiertos):** con el balón de 4–5 px, encuentra el balón en el 82–91 % de las imágenes.
    - **Puerta 1a (Antonio):** en nuestro vídeo el balón mide 5,9 px de mediana [medido].
    - **Lo que cabe esperar** [medido, DFL emulada, `D` de las etiquetas]: con B5 tal cual, hasta un detector perfecto
      da solo +0,010/+0,012 con el flag y +0,014/+0,017 con control, y uno realista, +0,007–0,009 y +0,011–0,015.
      Positivo con las dos convenciones, pero pequeño.
    - **Si pasa la puerta 1b:** la detección del partido entero (unas 3 h de CPU), la entrega de prueba, la
      reproducción en dos máquinas y el comando único (`regenerar.py`, de Antonio). Todos los pasos:
      `validation/balon_video/ESTA_NOCHE.md`.
  - **En marcha (16/11, tarde):**
    - David: B10, un modelo de equipo pensado para el balón nítido, en la DFL emulada;
    - Manuel: la idea 1.3, hecha y en `main`, apagada (PR 20, arriba);
    - Ana: el final de cada parada en el golpeo del balón del vídeo, como capa nueva de `D`;
    - Antonio: la puerta 1b, la detección y `regenerar.py`;
    - Claude (sesión de Ismael): la línea del vídeo y el borrador del documento técnico.

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
- **Corte: martes 17** (decisión de Ismael del 15/11; antes, el lunes 16 a las 14:00). Hora provisional,
  las 12:00, hasta que Ismael la confirme. Lo que no haya ganado en el harness no entra.

**Si quien abre la sesión no sabe cuál es su pieza,** enséñale su parte de la sección 3 del plan antes de
proponer nada.

**Pendiente de que el equipo lo decida:**

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
Las versiones de la entrega no se fijan aquí: van en nuestro `requirements-entrega.txt` (decisión de Ismael,
15/11), porque `requirements.txt` promete Python 3.8 y 3.11 y numpy 2.5.4 pide 3.12 o más.

**Lo nuestro:**

```
CLAUDE.md                    este brief
CONTRIBUTING.md              normas del repo
requirements-entrega.txt     versiones fijadas con las que se regenera la entrega (Python 3.13)
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
    No recibe rutas ni abre ficheros; solo `possession/dead_ball.py` y `possession/transiciones.py` (desde
    el 15/11) usan además los del partido, con las rutas de `games.asset_paths()`;
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
- **Dependencias:** las de la entrega van en `requirements-entrega.txt`, con la versión fijada (`==`). Una
  dependencia nueva del pipeline obliga a repetir el entorno limpio y la huella.
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
- **Revisión de cada PR:** puede revisarla, aprobarla y mergearla cualquier persona del equipo, también
  quien la abre: cada uno puede mergear su propia PR sin esperar una aprobación. `/subir` pide la revisión a
  Ismael (`ismaelp8`) y a David (`ortegafer`) para que alguien se entere, pero no hace falta esperarlos.
- **Merge:** lo hace quien la revisa o quien la abre. Si la PR toca código que usa la entrega, avísalo al
  mergearla: alguien tiene que regenerar la entrega y validarla.
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
| `/revisar-pr <n>` | para quien revise la PR de otra persona: revisa una PR con el agente `revisor`, aprueba o pide cambios, y mergea |
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
| **lun 16** | cada pieza sigue iterando; las PR entran según ganan. Documento técnico en marcha. Por la noche, **ensayo de congelado** con lo que haya en `main`: regenerar y reproducir en una máquina limpia |
| **mar 17, 12:00** (hora provisional) | **corte:** lo que no haya ganado en el harness no entra |
| **mar 17, tarde** | **congelar** y comprobar la reproducción exacta; hacer público el repo, validar el fichero exacto y **enviar con margen**. El formulario se puede editar hasta las 23:59 CET |

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
