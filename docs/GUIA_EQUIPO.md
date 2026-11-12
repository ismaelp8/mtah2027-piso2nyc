# Guía del equipo: More than a Hack 2027

Lo que cada miembro tiene que saber antes de escribir una línea de código.

- **De dónde sale cada cosa:**
  - los datos del reto (métrica, formatos, reglas): la documentación pública del repo (README,
    CHALLENGE, DATA, EVALUATION, SUBMISSION, RULES, FAQ, OVERVIEW) y el código de `evaluation/` y
    `starter/`;
  - el calendario, el reparto de roles y la estrategia: `CLAUDE.md`, el brief que comparte el Claude
    de todo el equipo;
  - las normas del repo (ramas, commits, PR, qué no entra en git): `CONTRIBUTING.md`.
- **Si algo choca con los ficheros oficiales, mandan ellos.** Si choca con
  `evaluation/possession_metrics.py`, manda el código.

---

## 0. Resumen en 30 segundos

- **Tarea:** para cada uno de los **199.319 frames** del vídeo táctico, decir `H` (posesión del Barça),
  `A` (posesión del Athletic), `D` (balón muerto) o `X` (sin respuesta).
- **Entrega:** martes **17/11/2026**, mediante un formulario de Google que llegará por email. Se suben un
  CSV, la URL de un repo público y un documento técnico.
- **Ranking:** `spellF1`, que mide si recuperas cada posesión entera. El desempate es `macroF1`. Baseline a
  batir: **0,2433**.
- **El problema central:** el balón falta en el **41 %** de los frames evaluados, justo en los momentos
  difíciles. Además, fragmentar posesiones se castiga muchísimo.
- **Las dos reglas que descalifican:** nada etiquetado a mano sobre este partido, y ningún dato del
  partido puede pasar por un LLM en la nube (Claude incluido).

---

## 1. El reto

| label | significado |
|---|---|
| `H` | Barcelona (local) en posesión, balón vivo |
| `A` | Athletic (visitante) en posesión, balón vivo |
| `D` | balón muerto. **No se pregunta de quién es** |
| `X` | no contesto |

**Formato:** CSV con cabecera `frame,label`, exactamente 199.319 filas, `frame` de 0 a 199318 en orden y
sin celdas vacías (para abstenerse se escribe `X`).

**Frames evaluados** (`games.half_video_blocks("BAR-ATH")`):

| tramo | frames | ¿se evalúa? |
|---|---|---|
| antes del partido | 0–11.184 | no |
| **1ª parte** | **11.185–90.651** | **sí** |
| descanso | 90.652–110.807 | no |
| **2ª parte** | **110.808–190.197** | **sí** |
| después del final | 190.198–199.318 | no |

En total se evalúan 158.857 frames. Fuera de esos tramos se puede poner `X` sin coste.

**Trampa conocida (está en el FAQ):** la 2ª parte se evalúa desde el frame 110.808, pero el saque inicial
es en el **113.742**. Esos 2.934 frames se evalúan y todos son `D`. Mejor detectarlo con un algoritmo
(Smart Tagging `Kick Off (Start)`, jugadores colocados en su campo) que meter el número a mano. Si se
acaba usando la constante del FAQ, hay que documentarlo.

---

## 2. Cómo se puntúa (lo más importante de todo)

### spellF1: el que decide

- Una **posesión** es una racha máxima de `H` o de `A`. Los tramos `D` son paradas, no posesiones.
  `H H D D H H` son **dos** posesiones.
- Cada posesión predicha se empareja **uno a uno** con una real por IoU temporal (intersección entre
  unión de intervalos). Se calcula el F1 con umbrales de IoU 0,3 / 0,4 / 0,5 / 0,6 / 0,7 y se promedia.
- Lo que cuesta llegar tarde a cada transición:

| caso | spellF1 |
|---|---|
| perfecto | 1,0000 |
| 1 frame tarde | 1,0000 |
| 3 frames tarde | 0,9818 |
| 8 frames tarde | 0,8933 |
| 1 segundo tarde | 0,6539 |
| cualquier constante o etiquetas al azar | 0,0000 |

- **Fragmentar es lo peor.** Una posesión real partida en tres son dos falsos positivos y un emparejamiento
  pobre. El baseline sin suavizar saca 0,0486 en spellF1 con un macroF1 de 0,65.
- **Ruido:** en el partido completo, una diferencia de menos de ~0,04 en spellF1 no significa nada.
  `python evaluation/run_evaluation.py --bootstrap 1000` da intervalos.

### macroF1: desempate

- Es el F1 por frame de `H`, `A` y `D`, promediado sin ponderar. Su rango útil va de ~0,16 a 1, y las
  diferencias de menos de ~0,01 son ruido.
- Apenas nota los retrasos, porque casi todos los frames están en mitad de una posesión.

### Cómo cuenta la `X`

- **En macroF1** cuenta como fallo.
- **En spellF1** el scorer la sustituye por **la última etiqueta de esa misma parte** antes de emparejar.
  Es decir, una `X` equivale a repetir la etiqueta anterior.
- **Conclusión: la `X` solo se usa fuera de los tramos evaluados.** En un frame evaluado, escribir
  directamente la etiqueta anterior da el mismo spellF1 y un macroF1 igual o mejor. Lo explica
  `docs/investigacion_metodos.md` §1.4.

### La ventana pública NO es un leaderboard

En `evaluation/gt/` hay ground truth de los primeros **5 minutos** (17 posesiones). El propio repo
demuestra que engaña:

| baseline | spellF1 público | spellF1 partido completo |
|---|---|---|
| `smooth50` | 0,3256 | **0,2433** (el mejor de verdad) |
| `smooth125` | **0,4242** (parece el mejor) | 0,2242 |

Sirve para comprobar que el pipeline es correcto (alineación, formato, significado de las etiquetas) y
para nada más. Entrenar o ajustar con ella está **prohibido** por las reglas, no es solo un consejo.
Tampoco hay leaderboard en vivo ni feedback antes del cierre.

---

## 3. Qué es "posesión" para la ground truth

- Mientras el balón está vivo **siempre** hay un equipo en posesión. Si está suelto o disputado, la
  posesión **sigue siendo del último que la tuvo**.
- Solo cambia cuando el rival consigue un **control**. No la cambian un toque sin control, un desvío que
  no intercepta el pase ni un duelo aéreo ganado sin control posterior. Como aproximaciones sugieren que
  un jugador conserve el balón unos segundos o que haya más de dos pases seguidos del mismo equipo.
- **Cómo se generó la GT:** de forma mecánica a partir del tracking **corregido** de Metrica. Hay `D`
  donde ese tracking marca el balón muerto y, en el resto de frames, el equipo que marca como poseedor.
  Sin suavizado y sin ajustes a mano. La pregunta útil, por tanto, es qué entiende el tracking corregido
  por "muerto" y por "poseedor", y la ventana pública lo muestra.
- Si nuestra lectura de la definición choca con la ventana pública, **tiene razón la ventana pública**.

---

## 4. Los datos

| | **tactical** | **broadcast** |
|---|---|---|
| papel | **la referencia: la fila *i* de la entrega es el frame *i*** | opcional, **no sincronizado** |
| vídeo | 199.319 frames, 25 fps, 1920×1080, 4,9 GB | su propio timeline, con cortes y repeticiones, 13 GB |
| tracking (ATD) | 199.319 registros | 164.488 registros |
| homografía | 100 % válida | 65,8 % válida |
| Smart Tagging | 638 instancias | no tiene |
| balón visible | 56,9 % de los frames | 50,5 % de los frames |

### ATD (tracking automático)

- **Línea:** `<frame_id>:<jugador>;<jugador>;...:<balón>`. Cada grupo es `x,y,velocidad` y lo ausente es
  `NaN`.
- **Coordenadas normalizadas 0–1.** Para calcular distancias hay que escalar con `games.GAMES["BAR-ATH"]["pitch"]`,
  que vale (105,3; 68,0) m. El campo no es cuadrado y no escalar falsea las distancias cerca de las bandas.
- **46 slots para 22 jugadores, sin identidad.** Solo se sabe el equipo. Los slots aparecen, desaparecen
  y se intercambian, así que cualquier análisis tiene que ser colectivo y no por jugador.
- **Alineación:** `video_frame = frame_id - 1`. Los offsets por mitad de `games.py` son del contador
  interno de la GT, no hacen falta para leer el ATD (lo explica `starter/load_atd.py`).
- Con kloppy: `metrica.load_tracking_epts(meta_data=..., raw_data=...)`. `starter/baseline.py` lo lee
  usando solo numpy.

### Smart Tagging

- Es **automático**, así que tiene falsos positivos y falsos negativos. Es evidencia, no una respuesta.
- Viene en formato SportsCode XML. `<start>` y `<end>` van en segundos desde el inicio del vídeo táctico,
  y el frame es `round(seg * 25)`.
- Los códigos van en MAYÚSCULAS (`SET PIECES`) y las etiquetas en formato título (`Team`,
  `Kick Off (Start)`): hay que comparar sin distinguir mayúsculas.
- `Team = N/A` aparece 36 veces, entre ellas **en todos los saques de banda**.
- Los `SET PIECES` son reinicios: 26 saques de banda, 12 córners, 10 saques de puerta, 5 faltas y 6 saques
  iniciales. Marcan dónde **termina** un tramo `D`.
- Los intervalos son **fases, no posesiones**: un `BUILD UP` puede quedarse corto o cubrir dos. Copiarlos
  tal cual importa sus errores.

### Homografía

- Es una matriz 3×3 por frame, de coordenadas de campo (0–1) a píxeles. Sirve para proyectar el tracking
  sobre el vídeo y depurar.
- Antes de usarla hay que mirar `valid`. `reprojection_error` mide cuánto fiarse: más bajo es mejor.

### Broadcast

- Su timeline es distinto, sin tabla de correspondencia. Si se usa, sincronizarlo con el táctico es
  problema nuestro. **Se deja para el final**, si sobra tiempo.
- Si nuestra entrega sale con ~164k filas, hemos indexado el broadcast por error.

---

## 5. Reglas: qué se puede y qué no

**Se puede:** cualquier método, siempre que la organización pueda inspeccionarlo y el documento técnico
lo explique. Eso incluye modelos preentrenados, APIs comerciales, LLMs (como herramienta, sin pasarles
datos del partido), tracking propio, datos de **otros** partidos (también etiquetados a mano) y métodos
no supervisados o pseudoetiquetas generadas por algoritmo sobre este partido.

**No se puede:**

1. **Etiquetar a mano cualquier cosa de este partido**, para ningún fin: ni para la entrega, ni para
   entrenar, ni para validar. Corregir a mano el tracking también es etiquetar. Mirar el vídeo para
   entenderlo sí está permitido; convertir lo visto en etiquetas o en **constantes ligadas a frames
   concretos** no.
2. **Usar la GT privada** o cualquier dato humano sobre este partido (Opta, StatsBomb, Wyscout,
   LaLiga…).
3. **Entregar un fichero que el repo no regenere exactamente.** Tiene que salir el mismo fichero, no uno
   parecido. La organización puede volver a ejecutar el repo ganador.
4. **Redistribuir los datos:** ni en el repo público ni como datos derivados que permitan reconstruirlos
   (exportaciones de tracking por frame, clips de vídeo…).
5. **Pasar datos o extractos a un LLM en la nube.** Lo dicen los términos y está citado en el FAQ y en
   el OVERVIEW.

Ante la duda, se pregunta **antes** de construir sobre ello: dudas de datos o métricas, issue en el repo
de Metrica; dudas de inscripción o términos, hackathon.talentarena@mobileworldcapital.com.

---

## 6. Cómo trabajar con Claude sin romper los términos

- Claude **sí** puede leer el código, la documentación, `evaluation/gt/` (la GT pública) y los datos
  abiertos de **otros** partidos.
- Claude **no** lee ningún CSV de `evaluation/results/`, tampoco los de los baselines. Son públicos,
  pero la carpeta está bloqueada entera y no hace falta leerlos: para eso están el validador y el
  scorer.
- Claude **no** puede ver nada de `MTAH_DATA_DIR`. Eso incluye no **adjuntar con `@`** ni arrastrar al
  chat ningún `BAR-ATH_*`, porque adjuntar envía el contenido. Tampoco puede ver outputs que impriman
  filas, coordenadas, etiquetas por frame o imágenes del vídeo.
- **Flujo:** Claude escribe el código, tú lo ejecutas en local y le pegas solo agregados (spellF1,
  macroF1, recuentos, tiempos, errores sin valores). Claude solo ejecuta él mismo:
  - `validate_submission.py` y `run_evaluation.py`, que imprimen agregados;
  - los scripts de `validation/scripts/`, que solo leen datos abiertos de otros partidos, la GT pública
    o nada.

  Los scripts que lean datos del partido van en `validation/partido/` y los ejecuta solo una persona.
- **`.claude/settings.json` es una red de seguridad**, probada el 11/11 con ficheros de prueba
  inofensivos.
  - **Bloquea** que Claude lea, busque o haga `cat` de `BAR-ATH_tactical*`, `BAR-ATH_broadcast*`,
    `*.mp4`, cualquier carpeta `mtah2027-data`, `evaluation/results/*.csv` y `evaluation/reports/`.
  - **No bloquea** un `python -c "open(...)"` ni un `grep -r` sobre una carpeta, ni datos guardados con
    otros nombres o en otra ruta.
  - **Solo está comprobada en una sesión de Claude abierta directamente en la carpeta del repo.** En
    una sesión abierta en otra carpeta y movida después al repo, las mismas pruebas no bloquearon nada.
    Abre siempre Claude en la carpeta del repo.

  No es un permiso para adjuntar nada.
- **Notebooks:** las celdas de salida guardan datos (tablas, gráficos del tracking). No se commitean con
  outputs y no se le pasan a Claude con outputs.
  - Antes de hacer commit: *Kernel → Restart & Clear Output*, o
    `python .claude/skills/subir/outputs_notebooks.py --limpiar <notebook>`.
  - Claude comprueba los outputs con ese mismo script, que solo imprime recuentos, antes de abrir un
    notebook.
- **Qué lee Claude al empezar:**
  - `CLAUDE.md`, el brief compartido que lee al empezar cada sesión en este repo;
  - tu `CLAUDE.local.md`, si lo tienes. Es personal y no se sube (`CONTRIBUTING.md` §1).
- **Si no quieres pelearte con git,** usa las skills: `/empezar`, `/subir`, `/actualizar`, `/evaluar` y
  `/decision`. Los reviewers tienen además `/revisar-pr`. Están explicadas en `CONTRIBUTING.md` §10.
- **Tus commits salen a tu nombre, nunca al de Claude.** El repo ya tiene desactivada la atribución a
  Claude. Comprueba tu identidad de git antes del primer commit (`CONTRIBUTING.md` §1 y §4).

---

## 7. Puesta en marcha (cada miembro)

```bash
# 1. Clonar (antes, aceptar la invitación de GitHub)
git clone https://github.com/ismaelp8/mtah2027-piso2nyc.git
cd mtah2027-piso2nyc
git remote add upstream https://github.com/metrica-sports/more-than-a-hack-2027.git
```

```bash
# 2. Entorno: Python 3.9+, venv FUERA de carpetas sincronizadas (OneDrive/iCloud)
python -m venv ~/.venvs/mtah2027
source ~/.venvs/mtah2027/bin/activate
pip install -r requirements-starter.txt        # numpy, pandas, kloppy==3.18.0, matplotlib, notebook
```
```powershell
# 2. Lo mismo en Windows
python -m venv $HOME\.venvs\mtah2027
& $HOME\.venvs\mtah2027\Scripts\Activate.ps1   # si PowerShell lo bloquea: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements-starter.txt
```

**2 bis. Git, GitHub y Claude.** Sigue `CONTRIBUTING.md` §1:
- tu identidad de git, con tu nombre y tu email de GitHub;
- `gh auth login`;
- excluir tu `CLAUDE.local.md`.

Sin la identidad bien puesta, tus commits saldrían a nombre de otra persona.

3. **Datos:** descargar la carpeta de Drive de la organización en `~/mtah2027-data/`, fuera del repo y
   fuera de OneDrive, con esta estructura y los nombres tal cual:

   ```
   ~/mtah2027-data/
   ├─ tactical/   BAR-ATH_tactical.mp4, _atd.xml, _atd.txt, _homography.csv, _smart_tagging.xml
   └─ broadcast/  BAR-ATH_broadcast.mp4, _atd.xml, _atd.txt, _homography.csv
   ```

   Los vídeos son opcionales para empezar: el baseline no los necesita. El táctico (4,9 GB) merece la pena
   para mirar jugadas; el broadcast (13 GB) puede esperar.

```bash
# 4. Variable de entorno
export MTAH_DATA_DIR=~/mtah2027-data            # macOS/Linux (añadir a ~/.zshrc o ~/.bashrc)
```
```powershell
[Environment]::SetEnvironmentVariable("MTAH_DATA_DIR", "$HOME\mtah2027-data", "User")   # Windows
```

```bash
# 5. Comprobar que todo funciona
python evaluation/run_evaluation.py     # sin datos: puntúa los 4 baselines públicos
python starter/baseline.py              # con datos: regenera los baselines a partir del ATD
python evaluation/run_evaluation.py     # debe dar smooth50 = spellF1 0.3256 / macroF1 0.6207
```

Si el último paso no da esas cifras, algo está mal en los datos o en la alineación. Hay que arreglarlo
antes de seguir.

---

## 8. Organización del repo

### Lo que viene de la organización (no se toca salvo que llegue un fix de `upstream`)

```
games.py                  constantes, rutas (asset_paths) y alineación
evaluation/               scorer oficial, métrica, validador, GT pública, results/
starter/                  baseline, loaders y 3 notebooks guiados
data/                     vacío, con su README; todo lo que entre ahí está gitignorado
*.md                      documentación oficial
```

### Lo que añadimos nosotros

Ya existe:
```
CLAUDE.md                 brief compartido para Claude (reto, reglas, estrategia, flujo de git)
CONTRIBUTING.md           normas del repo: ramas, commits, autoría, PR, upstream, qué no entra en git
.github/
  pull_request_template.md
.claude/
  settings.json           permisos: bloquea los datos, permite comandos seguros, sin atribución a Claude
  skills/                 /empezar /subir /actualizar /revisar-pr /sincronizar-upstream /evaluar /decision
  agents/revisor.md       revisa un diff contra nuestras reglas
docs/
  GUIA_EQUIPO.md          este documento
  decisiones.md           registro de decisiones (materia prima del documento técnico)
  investigacion_metodos.md  análisis de métodos, alternativas y recomendación
validation/               validación externa con datos abiertos: pasos, scripts y resultados agregados
                          (los datos se descargan, no se commitean)
```

Previsto (propuesta, a cerrar al acordar la interfaz):
```
docs/<EQUIPO>.md          documento técnico final
possession/               nuestro código, un paquete Python
  io.py                   carga ATD, Smart Tagging y homografía en arrays por frame de vídeo
  ball.py                 limpieza del balón: interpolación, saltos imposibles, fuera de campo
  dead_ball.py            detector de D
  candidates.py           candidato de posesión por frame y control frente a toque
  temporal.py             modelo temporal (HMM/Viterbi o histéresis)
  pipeline.py             UN comando: datos → evaluation/results/<EQUIPO>.csv
notebooks/                exploración, siempre sin outputs
requirements.txt          dependencias fijadas con versión (al final, pip freeze de lo que se use)
```

**Interfaz común:** cada módulo recibe las rutas de `games.asset_paths()` y devuelve un `np.ndarray` de
**199.319** posiciones indexado por **frame de vídeo**. Así nadie se pelea con la alineación y las piezas
se combinan solas.

### Cómo se trabaja en el repo

Las normas completas están en **`CONTRIBUTING.md`**. En resumen:
- solo Ismael sube directo a `main`; los demás, nunca;
- una rama `tipo/descripcion` por tarea;
- cada commit sale con tu identidad;
- cada rama entra por PR con plantilla, con revisión de Ismael (`ismaelp8`) o David (`ortegafer`);
- basta una aprobación y se mergea con squash.

Lo que **nunca entra en git** (datos, vídeos, cachés, CSV de entregas, outputs de notebooks, PDFs,
`CLAUDE.local.md`) está en la tabla de `CONTRIBUTING.md` §7.

**Regla práctica:** antes de cada `git commit`, mirar `git status` y que no aparezca ningún `BAR-ATH_*`
salvo `evaluation/gt/BAR-ATH_possession_gt_public*`.

---

## 9. Estrategia de partida y reparto

Esto es un punto de partida, no un dogma. El detalle y los responsables de cada área están en
`CLAUDE.md`.

1. **Limpieza del balón:** interpolar huecos cortos, descartar saltos físicamente imposibles y marcar
   cuándo el balón sale del campo.
2. **Detector de `D`:** combina balón fuera, `SET PIECES` como fin del tramo muerto, jugadores parados o
   con baja velocidad media, posiciones típicas de córner o saque de banda, y el inicio de la 2ª parte.
   **Que falte el balón no significa que esté muerto.** El baseline lo trata como `D`, y por eso su clase
   `D` es mala.
3. **Candidato por frame:** el equipo del jugador más cercano con umbral en metros. Se exige control (balón
   lento cerca del mismo equipo durante varios frames, o pases seguidos) y no basta un toque. Sin balón,
   se recurre a señales colectivas (quién presiona, quién se despliega) y al equipo de la fase de Smart
   Tagging como prior.
4. **Modelo temporal sobre {H, A, D}** con un coste por cambio de estado. **Es lo que más mueve el
   spellF1.**
5. **Política de `X`:** solo fuera de los tramos evaluados. Dentro, también en las oclusiones largas, se
   escribe siempre una etiqueta.

| rol | qué hace |
|---|---|
| Infraestructura y entrega | repo, pipeline de un comando, reproducibilidad, validación, formulario |
| Balón muerto `D` y reinicios | límites, Smart Tagging, patrones de jugadores parados |
| Modelo de posesión | candidato por frame, control frente a toque, modelo temporal |
| Validación externa | datos abiertos, degradación, harness de experimentos |
| Documento técnico | todos, con el responsable de infraestructura como dueño |

| día | objetivo |
|---|---|
| mar 10 | repo, entorno, datos en local, baseline reproducido, todos han leído la documentación |
| mié 11 | exploración por áreas, interfaz común acordada, harness de validación externa empezado |
| jue 12 | primera versión de `D` y de posesión. **Primera entrega validada que bata el baseline** |
| vie 13 | modelo temporal integrado y experimentos con validación externa |
| sáb 14 | llegan las instrucciones de entrega: revisar formulario y cuenta de Google. Empezar el documento técnico |
| dom 15 – lun 16 | iterar. **Congelar el lunes por la noche** y reproducir en una máquina limpia |
| mar 17 | hacer público el repo, validar el fichero exacto y enviar con margen (se puede editar hasta las 23:59 CET) |

---

## 10. Validación de verdad: otros partidos

Como la ventana pública no sirve para elegir, hay que medirse con partidos de los que sí se tengan
etiquetas. El plan completo (datos, etiquetas, degradación, protocolo) está en
`docs/investigacion_metodos.md` §5. Claude **sí** puede leer estos datos, porque son de otros partidos.

- **Dataset principal propuesto: el de la Bundesliga** (Bassek et al., 2025;
  https://doi.org/10.1038/s41597-025-04505-y).
  - Son 7 partidos a 25 Hz, con licencia CC-BY 4.0.
  - Trae en cada frame qué equipo posee el balón y si está vivo: el mismo tipo de etiqueta que la GT
    del reto. Las etiquetas salen de forma mecánica: `D` si el balón está inactivo y, si no, `H` o `A`.
  - **El experimento 0 ya está hecho** (12/11, `validation/resultados/2026-11-11_experimento0.md`):
    - su balón muerto (`D`) vale tal cual, tapando la posición del balón en los `D` y en sus bordes
      (la DFL la congela mientras el balón está muerto);
    - su flag de equipo cambia en el primer toque del rival aunque no controle. Por decisión de Ismael,
      las etiquetas de equipo se derivan con el criterio de control del reto
      (`docs/decisiones.md`, 12/11);
    - cómo elegir ese control está en `validation/resultados/2026-11-12_criterio_posesion.md`.
- **Dataset secundario: Metrica sample-data** (https://github.com/metrica-sports/sample-data).
  - Son 3 partidos anonimizados con tracking y eventos sincronizados. `Sample_Game_3` viene en formato
    FIFA/EPTS, el mismo que nuestro ATD, así que se carga con el mismo
    `kloppy.metrica.load_tracking_epts`.
  - No trae posesión por frame. Las etiquetas hay que derivarlas de los eventos: equipo del último
    evento con control, y `D` entre balón fuera o falta y el reinicio.
  - Sirve para comprobar que las conclusiones aguantan con otro proveedor y otra forma de etiquetar.
- **Degradar** el tracking abierto para que se parezca al ATD: quitar ~41 % del balón (más en zonas
  pobladas y balones aéreos), quitar identidades y fragmentar tracks.
- **Puntuar** con `evaluation/possession_metrics.py`.
- Los priors (duración típica de una posesión, velocidades, distancias de control) se sacan **de aquí** y
  no de la ventana pública.
- Los datos abiertos se descargan con un script y **no se commitean**.
- En el documento técnico hay que contar la fuente, cómo se derivaron las etiquetas y cuántas hay, y citar
  a los autores de cada dataset.

---

## 11. Checklist de entrega

- [ ] `<EQUIPO>.csv`: 199.319 filas y `python evaluation/validate_submission.py <EQUIPO>.csv` en verde
      sobre **ese mismo fichero**.
- [ ] El nombre de fichero y el del formulario coinciden **exactamente** con el nombre de equipo que
      puso cada uno al inscribirse.
- [ ] Repo **público** que regenera **exactamente** el CSV con un solo comando y sin datos dentro.
      Dependencias fijadas y semillas fijas: el mismo fichero, byte a byte.
- [ ] Documento técnico (`.md` o `.pdf`): enfoque y por qué, datos usados y descartados, datos de
      entrenamiento y su origen, reglas de posesión implementadas, limitaciones y cómo reproducirlo.
- [ ] Una cuenta de Google para subir. Una sola respuesta por equipo; cuenta la última.

### Antes de hacer público el repo (17/11)

- [ ] `git log --all --stat` sin ningún `BAR-ATH_*` del partido ni CSV de entregas en el historial.
- [ ] Notebooks sin outputs.
- [ ] Revisar `CLAUDE.md` y `docs/` por si hay algo que no queramos publicar (nombres, notas internas).
