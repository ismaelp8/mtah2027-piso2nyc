# Posesión del balón frame a frame: documento técnico

**Equipo:** Piso2 NYC Team

**Entrega:** `Piso2 NYC Team.csv`, generada con un solo comando a partir del tracking automático (ATD) y del
Smart Tagging del partido (sha256 `811658cd52267cbd75607270c2c359e2244b05b8a6d091d6ce8330d2d971c04b`).

**Summary (English).** We label every frame as `H`, `A` or `D` with a numpy-only pipeline. Each component scores
`H`, `A` and `D` per frame; the scores are added and a Viterbi decoder picks the best sequence, paying a fixed cost
for each change of state. Team evidence averages a logistic regression and a small per-player neural network;
dead-ball evidence is a logistic regression on player aggregates plus four small layers. We require controlled
possession, as `CHALLENGE.md` says. Everything was trained and chosen on open data from other games (Bundesliga,
SkillCorner), never on the provided game or its public window. The rest of this document is in Spanish.

## 1. Enfoque

**Lo que manda el diseño.** El spellF1 trata cada posesión como un objeto: una posesión inventada es un falso
positivo, y un cambio desplazado baja el IoU de las dos posesiones que separa. Por eso la salida no es un voto
frame a frame, sino un decodificador temporal con un coste por cada cambio de estado. La dificultad central es el
balón del ATD: falta en el 40,7 % de los frames evaluados y, según agregados del partido, llega suavizado (unos
25 frames) y unos 4 frames por detrás de los jugadores. Por eso casi nada se apoya en la velocidad del balón.

**Cómo funciona.** Cada pieza recibe el tracking en metros (46 slots sin identidad, cada uno con su equipo) y
devuelve, en cada frame, una puntuación para `H`, `A` y `D` y una máscara de estados prohibidos, que solo se usa
para lo que se sabe seguro. Las puntuaciones se suman y un Viterbi elige la secuencia en cada tramo evaluado. El
código que se mide en los datos abiertos es el mismo que genera la entrega.

| pieza | qué aporta |
|---|---|
| equipo (K3) | media a partes iguales de los logits de `H` frente a `A` de dos modelos. B5: regresión logística con 30 rasgos simétricos (proximidad al balón en ventanas de 1 a 151 frames y forma de los equipos). K2: red pequeña que procesa a cada jugador con 14 rasgos, agrega por equipo y ve ±12,6 s (36.260 pesos). Solo decide entre `H` y `A` |
| estado de `D` (E2) | regresión logística con 11 agregados de los jugadores (velocidades, jugadores parados o fuera de las líneas, distancia entre equipos, dispersión). No usa el balón: que falte no significa que esté muerto |
| anclas de `D` | `D` forzado entre el inicio del tramo evaluado de la 2ª parte y su saque, y prohibido en el frame de cada saque. +1 en `D` si el balón desaparece de 5 a 60 s antes de un reinicio del Smart Tagging que no es un saque inicial |
| contraataques | +8 por frame al equipo de cada «Attacking Transition» del Smart Tagging, durante 5 s |
| balón fuera | +5 en `D` con el balón visto a más de 1 m fuera del campo |
| decodificador | Viterbi sobre {`H`, `A`, `D`} con un coste de 25 por cambio. Después, una posesión de menos de 5 s que llega con un cambio directo desde el otro equipo y acaba en `D` pasa a `D` («cortas a `D`») |

**Por qué así.** No hay etiquetas del partido que se puedan usar, y la ventana pública no sirve para elegir (en el
repo oficial, el baseline que gana en ella pierde en el partido). Todo se eligió en partidos abiertos de otras
ligas, con piezas pequeñas medidas por separado y reglas de entrada escritas antes de medir:

- **Harness:** el pipeline en los 7 partidos abiertos de la Bundesliga (la DFL), con el balón degradado como el
  del ATD (huecos, bloques y suavizado), puntuado con el scorer oficial y con dos convenciones de etiqueta: el
  flag de posesión de la DFL, que cambia en el primer toque del rival, y ese flag corregido para exigir control.
- **Regla de entrada:** ganar por 0,03 o más, con el intervalo 5–95 % del bootstrap por encima de cero y en 6 de 7
  partidos, con las dos convenciones. Así entraron B5 y E2.
- **Límite de daño,** para cambios pequeños hacia control: ganar con control en la DFL y en SkillCorner (con un
  examen de 10 partidos que cada candidato abre una vez) sin perder más de 0,005 con el flag. Así entraron
  «cortas a `D`» y K2.
- **K3** entró por decisión del equipo: K2 gana mucho con los proveedores que vio al entrenar, pero se traslada
  mal a otros (el ATD es un tercero), y la media con B5 conserva parte de esa ganancia y falla menos partido a
  partido.
- **Las capas del Smart Tagging y del balón fuera** no se pueden medir en la DFL. Entraron por reglas de daño
  escritas antes, con recuentos del partido sin etiquetas.

## 2. Validación y lo que se descartó

Cada partido se puntúa con evidencias de equipo que no lo vieron. En la DFL, el `D` se copia de las etiquetas para
medir solo `H` frente a `A`, con el balón «como el ATD»; la columna de K3 cubre también las medidas con nuestro `D`:

| datos | baseline | cadena con B5 | K3 sobre B5 |
|---|---|---|---|
| DFL, flag (7 partidos) | 0,406 | 0,498 | de +0,014 a +0,025 |
| DFL, control (7 partidos) | 0,464 | 0,728 | de +0,034 a +0,056 |
| SkillCorner (20 partidos) | — | +0,131 sobre el baseline | de +0,017 a +0,023 (10 partidos) |
| Metrica (3 partidos) | — | +0,118 sobre el baseline | de +0,014 a +0,029 |

La cadena con B5 gana al baseline en 7 de 7, 20 de 20 y 3 de 3 partidos. Con nuestro propio `D` saca 0,414 (flag)
y 0,623 (control) en la DFL, frente a 0,310 y 0,353 del baseline, y 0,381 frente a 0,249 en SkillCorner (antes de
«cortas a `D`»). Descontando lo que cada celda regala al baseline (0,2433 en el partido), estimamos para el partido
un spellF1 de entre 0,35 y 0,56, con unos 0,41 como punto central; el harness es optimista (§6). En la ventana
pública la entrega saca 0,693, pero con 17 posesiones es ruido y no se usó para elegir.

**Probado y descartado,** cada candidato con su regla escrita antes:
- **Otras evidencias de equipo:** el jugador más cercano (B5 le gana por +0,071 y +0,056 con el flag), reglas de
  radio y retención, variantes de la logística y una red de una capa.
- **Modelos de secuencia** (convolución temporal, GRU y redes sobre trayectorias; B11 a B17): ganan con el flag en
  la DFL, pero no lo sostienen con control o en SkillCorner, o empatan con K2. Los exámenes de B12 y B17 no pasan.
- **Variantes de K2:** una salida que avisa de los cambios, entrenarla solo con la DFL y promediarla con el campo
  en espejo. Tampoco pasa un detector de cambios de posesión: da demasiados avisos falsos.
- **Otros modelos de `D`** (logísticas y árboles) y anclas fijas (del gol al saque, el instante del reinicio): no
  ganan a E2, o pasan juego vivo a `D`.
- **Decodificador y balón:** la duración mínima, la poda y los costes 12 y 50 empatan con el de 25; limpiar el
  balón, adelantarlo 4 frames o quitar los slots sobrantes también empatan.
- **El Smart Tagging como pista de equipo sin balón:** alcanza menos del 1 % de los frames evaluados.
- **El balón detectado en el vídeo táctico** (YOLO11n público, en local): el 42 % de sus detecciones cae a más de
  5 m del balón del ATD, y en la DFL, incluso perfecto, solo le daría a B5 unos +0,01.

## 3. Reglas de posesión implementadas

- **Exigimos control,** como dice `CHALLENGE.md`. Los modelos se entrenaron con etiquetas corregidas por
  control: una racha del rival se queda solo si un mismo jugador está a 1 m o menos durante 12 frames, o si su
  equipo encadena dos toques en 2 s.
- **Balón suelto o disputado:** la posesión sigue con el último equipo que la tuvo. No hay una regla de «último
  toque»: el coste de cambio exige una evidencia sostenida del rival, y un toque aislado no la da.
- **Toques sin control, desvíos y duelos aéreos ganados sin control:** no cambian la posesión, por la misma razón.
- **Balón muerto y reinicios:** `D` sale de la suma de E2, del balón visto fuera, del hueco sin balón antes de
  cada reinicio del Smart Tagging y del tramo anterior al saque de la 2ª parte. Una parada solo se crea si la
  evidencia paga dos cambios. Tras un reinicio, la posesión es del equipo que dé la evidencia: no se arrastra el
  de antes de la parada.
- **Posesión corta justo antes de una parada:** si dura menos de 5 s, llega con un cambio directo y acaba en `D`,
  se escribe `D`. Ese cambio se trata como un `D` que pusimos tarde, no como un control del rival.
- **La `X`** solo se escribe fuera de los tramos evaluados. Dentro siempre hay `H`, `A` o `D`, también en
  oclusiones largas.

## 4. Datos usados y descartados

**Del partido.**

| fuente | uso |
|---|---|
| ATD táctico | entrada principal: 199.319 líneas, todas válidas |
| Smart Tagging | los `SET PIECES` (hueco antes del reinicio) y las «Attacking Transition» con su equipo (contraataques). Nunca se copia como etiqueta |
| constantes de saque | 11.185 y 113.742 (`starter/load_smart_tagging.py`, `FAQ.md`), para las anclas de `D`. Con los tramos evaluados de `games.py`, son las únicas constantes ligadas a frames, y las publica la organización |
| GT pública (5 min) | comprobar el formato y la alineación y entender las etiquetas. No entrena, no fija parámetros ni elige versiones |
| vídeo táctico | lo vieron personas para entender el juego; un detector de balón lo procesó en local para la línea descartada (§2) |
| homografía | solo en la línea descartada del vídeo |
| broadcast y audio | descartados: el broadcast no está sincronizado y su homografía solo vale en el 65,8 %; el silbato da una señal sucia |

Algunos valores salen de agregados del partido, sin etiquetas: el perfil del balón del ATD (suavizado y retraso),
con el que se degradan los datos abiertos, el umbral de 5 s de los huecos y la cola de 16 frames del balón fuera.
Una persona revisó junto al vídeo los tramos de la ventana pública en que una versión anterior fallaba, con reglas
escritas antes y sin ajustar nada; de ahí salieron dos hipótesis (el balón fuera y «cortas a `D`») que se midieron
en datos abiertos o con agregados sin etiquetas. Al principio, un miembro anotó a ojo si 15 cambios de la GT
pública le parecían un toque o un control; se dejó a medias y no entró en ningún código, parámetro ni elección. Lo
declaramos para que la organización lo juzgue frente a `RULES.md`.

**Abiertos, de otros partidos.**

| dataset | uso |
|---|---|
| Bundesliga (DFL), Bassek et al. (2025), 7 partidos | entrenamiento de B5, E2 y K2, y harness |
| SkillCorner Open Data, 20 partidos de la A-League 2024/25 | validación; 10 de ellos entrenan K2 y los otros 10 son el examen |
| Metrica sample-data, 3 partidos | solo validación |
| dataset de balones de Roboflow (CC BY 4.0) | solo para medir el detector descartado |

No se usa ningún dato humano de este partido (Opta, StatsBomb, Wyscout, LaLiga…). StatsBomb, Wyscout, SoccerNet y
PFF FC se descartaron por la licencia, por no traer el balón medido o por no aportar nada.

## 5. Datos de entrenamiento

| dataset | quién etiquetó | cuánto | modelos |
|---|---|---|---|
| Bundesliga (DFL), Bassek et al. (2025), CC BY 4.0 | el proveedor: `BallStatus` y `BallPossession` por frame, con el tracking revisado por operadores. Las etiquetas con control las deriva nuestro código | 7 partidos, 1.002.644 frames | B5, E2 y K2 |
| SkillCorner Open Data, MIT | SkillCorner: `possession.group`, que exige control. El `D` sale de sus fases de juego | 10 partidos | K2 |

- **B5:** el flag, solo donde coincide con la corrección por control; uno de cada 5 frames vivos (103.135 filas);
  Newton con L2 = 1. La escala de sus logits (4) se eligió en los partidos de entrenamiento de cada pliegue.
- **E2:** `D` o juego según `BallStatus`, en uno de cada 5 frames: 200.532 frames, el 44,8 % `D`. scikit-learn
  1.7.2 (C = 1) solo para entrenar; los coeficientes van escritos en el código.
- **K2:** la corrección por control en todos los frames vivos de la DFL y `possession.group` en SkillCorner, con
  aumentos hacia el ATD (balón retrasado, slots que faltan o duplicados, huecos de balón). Torch, 3.000 pasos,
  semilla 20261124. Los pesos van en el repo (`possession/conjunto_pesos.npz`), porque el entrenamiento en GPU no se
  repite bit a bit; la entrega solo los lee y corre en numpy.
- **K3** no se entrena: mezcla B5 y K2 con peso ½, fijado antes de medir.

Ninguna etiqueta de entrenamiento sale del partido. Lo único del partido que llega al entrenamiento es el perfil
agregado del balón con el que se degrada la DFL. B5 y K2 se validaron dejando fuera el partido que se puntúa. E2,
con nuestro `D` en el harness, va con el modelo de los 7 partidos; dejando uno fuera cambia 0,001 o menos.
Regenerar la entrega no reentrena nada.

## 6. Limitaciones

- **Cambiamos de equipo de menos y tarde.** De los cambios directos entre equipos en la DFL con control, K3 ve el
  44 %, y no encuentra las posesiones de menos de 2 s. La mayor pérdida está en la evidencia de equipo con el balón a la vista.
- **Los bordes de `D` son imprecisos:** E2 pone el inicio a 25 frames o menos solo en el 35 % de las paradas. Bien
  puestos valdrían de +0,05 a +0,07 en la DFL.
- **Tres capas no se han medido con etiquetas:** el hueco antes del reinicio, los contraataques y el balón fuera.
  El balón fuera, además, falló su criterio de eficacia (seguimos llegando tarde en el 25,5 % de las rachas de
  balón fuera, y se pedía menos del 15 %), aunque pasó los de daño.
- **«Cortas a `D`» quita posesiones, y ya predecimos de menos:** 198 en el partido (unas 3,5 por minuto de juego,
  frente a 4,1–4,3 en los datos abiertos). Si la GT se parece al flag, cuesta hasta 0,002. Su regla se escribió con
  sus cifras de la DFL ya conocidas; a ciegas solo se midieron su examen de SkillCorner y su entrega de prueba.
- **K2 se traslada mal de un proveedor a otro:** entrenada solo con la DFL, queda entre +0,003 y −0,015 frente a
  B5 en SkillCorner. K3 reduce ese riesgo, pero no lo quita.
- **No sabemos qué convención sigue la GT:** con el flag estamos en 0,498 y con control en 0,728.
- **El harness es optimista:** no ejecuta las capas del Smart Tagging ni del balón fuera, tiene a los 22 jugadores
  sin ruido (en el partido, un equipo tiene más de 11 slots en el 12,9 % de los frames evaluados) y más disputas
  visibles que el ATD.

**Con más tiempo:** un detector de balón en el vídeo que no confunda otras cosas con el balón, los tiempos de
eventos corregidos que publica ELASTIC para 3 partidos de la DFL, varias semillas de K2 y más proveedores de
tracking en su entrenamiento.

## 7. Reproducción

**Código:** https://github.com/ismaelp8/mtah2027-piso2nyc, en el último commit de `main` en el momento de la
entrega (17/11/2026). El código que genera el CSV no ha cambiado desde el commit `23dcbc1`.

**Entorno:** Python 3.13 y `requirements-entrega.txt` (numpy 2.5.4 y pandas 3.1.1). La entrega solo importa numpy
y la biblioteca estándar; pandas lo usan el validador y el scorer oficiales. Python 3.11 no sirve, porque numpy
2.5.4 pide 3.12 o más.

**Datos:** el paquete del concurso, tal cual, en `data/` dentro del repo, o en otra carpeta con `MTAH_DATA_DIR`
apuntando a la que contiene `tactical/`. La entrega solo lee el ATD táctico y el Smart Tagging.

**Comandos,** desde la raíz del repo. Linux y macOS:

```
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-entrega.txt
export MTAH_DATA_DIR=/ruta/al/paquete
.venv/bin/python -m possession.pipeline --name "Piso2 NYC Team"
.venv/bin/python evaluation/validate_submission.py "evaluation/results/Piso2 NYC Team.csv"
```

Windows (PowerShell):

```
py -3.13 -m venv <carpeta>
<carpeta>\Scripts\python -m pip install -r requirements-entrega.txt
$env:MTAH_DATA_DIR = 'D:\ruta\al\paquete'
<carpeta>\Scripts\python -m possession.pipeline --name "Piso2 NYC Team"
<carpeta>\Scripts\python evaluation/validate_submission.py "evaluation/results/Piso2 NYC Team.csv"
```

Generar el CSV tarda unos 10 s. El comando imprime solo agregados y se niega a escribir el CSV si el ATD tiene
alguna línea rara o si dos piezas se contradicen en un frame evaluado.

**Resultado esperado:** sha256 `811658cd52267cbd75607270c2c359e2244b05b8a6d091d6ce8330d2d971c04b`, con 198
posesiones de 17,4 s de media, 116 paradas y `D` en el 45,8 % de los frames evaluados. Ha salido con esa huella en
Windows (entorno limpio, Python 3.13.1 y numpy 2.5.4), en un portátil Linux distinto (entorno limpio, Python 3.13.9
y numpy 2.5.4) y en otra instalación con numpy 1.26.4. No hay azar, y nada depende del orden de los ficheros ni de
la hora.

## 8. Licencias y referencias

Bundesliga: CC BY 4.0. SkillCorner Open Data: MIT. Metrica sample-data: sin fichero de licencia; su README pide
citar la fuente. Código y GT pública del reto: MIT (Metrica Sports). Los pesos de K2 derivan de la Bundesliga y de
SkillCorner. El detector de balón probado (AGPL-3.0) no está en la entrega. El código propio del equipo se publica
sin licencia, para que se pueda revisar y reproducir la entrega.

- Bassek, Rein, Weber y Memmert (2025). An integrated dataset of spatiotemporal and event data in elite soccer.
  *Scientific Data*, 12, 195. doi:10.1038/s41597-025-04505-y. Datos: doi:10.6084/m9.figshare.28196177. Con
  autorización de la DFL.
- SkillCorner. Open Data (commit 4340d2745728), https://github.com/SkillCorner/opendata.
- Metrica Sports. Sample data, https://github.com/metrica-sports/sample-data.
- Kim, Choi, Seo, Boomstra, Yoon y Park (2025). ELASTIC: Event-Tracking Data Synchronization in Soccer Without
  Annotated Event Locations. Workshop MLSA de ECML PKDD 2025. arXiv:2508.09238.
- Metrica Sports y Barça Innovation Hub (2026). More than a Hack 2027: Frame-level Ball Possession, v1.0.0.
  https://github.com/metrica-sports/more-than-a-hack-2027.
