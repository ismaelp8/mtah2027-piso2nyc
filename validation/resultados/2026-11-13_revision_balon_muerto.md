# Revisión del detector de balón muerto v1: qué hay, qué le falta y qué vale el `D` en la métrica

- **Fecha:** 2026-11-13 · **Quién:** Claude, en la sesión de Ana Aparicio, a petición suya: revisión crítica del
  trabajo de Manuel en la rama `feat/detector-balon-muerto` (commit `792cb80`, aún no en `main`).
- **Datos:** ninguno del partido. GT pública (`evaluation/gt/`), la GT sintética del repo
  (`validation/scripts/sensibilidad_metrica.py`) y el partido abierto `J03WMX` de la Bundesliga (Köln–Bayern,
  Bassek et al. 2025, CC BY 4.0), bajado con `descargar_datos_abiertos.py dfl --limite 1` a
  `~/mtah2027-datos-abiertos`, fuera del repo.
- **Scripts:** `validation/scripts/revision_balon_muerto/` (su `README.md` dice cómo repetir cada cifra). Los
  agregados de la sección 7 están escritos en `validation/partido/agregados_*.py`, para que los ejecute Manuel.
- **Etiquetas:** **[medido]** calculado y repetible; **[inferencia]** deducción sin confirmar; **[sin verificar]**
  no comprobado; **[doc]** está en la documentación oficial.

## Lectura en cinco líneas

1. **La v1 es correcta pero no es un detector:** marca los 2.934 frames anteriores al saque de la 2ª parte que
   publica el FAQ. Son el 1,8 % de los frames evaluados y, si el `D` ronda el 40 % como en la Bundesliga
   (33–49 % en `J03WMX`), en torno al **5 % del `D` que hay que encontrar**. Todo lo demás del `D` sigue sin
   hacer y sin plan concreto.
2. **El valor del `D` está en las fronteras, no en la cobertura** [medido, DFL con equipo oráculo]: detectar
   **todas** las paradas con los dos bordes 2 s tarde vale lo mismo que no poner ningún `D` (0,83 frente a
   0,82); detectar **la mitad** con los bordes exactos vale 0,92; todas con ruido de ±1 s, 0,90.
3. **Tres reglas de diseño que nadie ha escrito y que deciden más que el método:** el `D` no puede parpadear
   dentro de una parada (un hueco de 10 frames cada 4 s baja el spellF1 a 0,62); el equipo que reanuda tiene que
   ser el correcto desde el primer frame (medio segundo de equipo equivocado tras cada reinicio: 0,80); y las
   fronteras tienen que estar a menos de 0,5–1 s.
4. **Los dos descartes de Manuel son prematuros:** "balón fuera → cubre poco" confunde cubrir frames con
   disparar el inicio del `D`; y "lo que encuentra el detector de golpeo no son reinicios" se apoya en una
   suposición (que el ATD ve el balón quieto más de 1 s antes de sacar) que sus propios datos contradicen.
5. **Los jugadores solos dicen el estado, no el momento** [medido, DFL]: AUC 0,93–0,97 por frame, pero el
   inicio del `D` llega entre 1 y 7 s tarde y el spellF1 no mejora frente a no poner `D`. El camino es
   **tiempo con el balón y el Smart Tagging, estado con los jugadores**, y el modelo de jugadores se puede
   entrenar en la DFL ya, sin esperar a la degradación.

---

## 1. Qué pide el reto del `D` y qué vale en la métrica

**Lo que pide** [doc]: `D` donde el tracking corregido marca el balón muerto; no se pregunta de quién es. Un
`D` corta la posesión: `H H D D H H` son dos posesiones. Para el ranking (`spellF1`) el `D` sirve para
**cortar las posesiones donde se cortan de verdad**; para el desempate (`macroF1`) es una de las tres clases.
Y hay un tercer uso que no está escrito en ningún sitio del repo: **proteger las etiquetas de equipo** durante
una parada, cuando el jugador más cercano al balón quieto es ruido.

**Cuánto `D` hay que esperar:** la ventana pública tiene un 19,6 % (4 paradas de 5,5 a 20 s) [medido]; la
Bundesliga, 44,8 % con los 7 partidos y 33 % / 49 % en las dos partes de `J03WMX` [medido]; unas 100 paradas
por partido. Nada de esto se usa para ajustar nada: es para saber el tamaño del problema.

**Qué cuesta cada error del `D`** [medido]. Tres fuentes: la GT sintética del repo (6 partes, ~37 % de `D`,
142 paradas por 332 posesiones), la GT pública con el equipo perfecto, y el partido `J03WMX` con el equipo
perfecto (media de sus dos partes). Perfecto = 1,000.

| error del detector de `D` (todo lo demás perfecto) | sintética | GT pública | DFL `J03WMX` |
|---|---|---|---|
| ningún `D` (se arrastra el equipo previo) | 0,638 | 0,812 | 0,817 |
| se pierde el 50 % / 20 % / 10 % de las paradas | 0,816 / 0,926 / 0,963 | — | 0,923 (50 %) / 0,965 (85 %) |
| el `D` empieza 0,5 / 1 / 2 / 5 s tarde | 0,985 / 0,953 / 0,903 / 0,803 | 1,000 / 1,000 / 0,976 / 0,894 | — / 0,944 / 0,907 / 0,861 |
| el `D` empieza 1 s **pronto** (se come el final de la posesión) | 0,917 | — | 0,924 |
| el `D` acaba (el reinicio) 0,5 / 1 / 2 / 2,5 / 5 s tarde | 0,965 / 0,919 / 0,859 / 0,836 / 0,747 | 1,000 / 1,000 / 1,000 / — / 0,929 | — / 0,953 / 0,923 / — / — |
| los dos bordes 1 s / 2 s tarde | 0,865 / 0,763 | — | 0,896 / **0,827** |
| los dos bordes con ruido N(0, 0,25 s) / N(0, 0,5 s) / N(0, 1 s) | — | — | 0,947 / 0,925 / 0,903 |
| el `D` dura 1–5 s y vuelve al equipo previo (disparo sin fin) | 0,786–0,818 | 0,908 | — |
| el `D` parpadea: hueco de 10 frames cada 100 / 25 cada 250 | **0,623** / 0,853 | — | — |
| equipo equivocado durante 0,5 / 1 / 3 s tras cada reinicio (`D` perfecto) | **0,805** / 0,772 / 0,702 | — | — |
| se arrastra el equipo previo 1 s / toda la posesión tras cada reinicio | 0,876 / 0,792 | — | — |
| 1 `D` inventado de 1–4 s por minuto de juego | 0,920 | 0,644 (uno en cada posesión larga) | — |

**Lo que se deduce** [inferencia a partir de lo medido]:

- **Precisión antes que cobertura.** En `J03WMX`, la mitad de las paradas con bordes exactos (0,92) vale más
  que todas con ruido de ±1 s (0,90), y todas con 2 s de retraso en los dos bordes (0,83) no valen nada frente
  a no poner `D` (0,82).
- **El reinicio pesa más que el inicio.** Acabar el `D` 1 s tarde cuesta 0,08 en la sintética; empezarlo 1 s
  tarde, 0,05. Recortar el principio de la posesión siguiente duele más que alargar la anterior.
- **Nunca parpadear.** Cada hueco dentro de una parada es una posesión inventada. Esto fija una duración mínima
  del `D` y una histéresis, que salen de los datos abiertos, no de la ventana pública.
- **El equipo al reanudar es parte del `D`.** Un `D` perfecto con el equipo equivocado medio segundo tras cada
  reinicio (0,80) cuesta más que perder la mitad de las paradas (0,82). En `J03WMX` el equipo cambia a través
  del 90 % de las paradas [medido], así que "arrastrar el anterior" falla casi siempre.
- **En la ventana pública casi nada de esto se ve.** Con 4 paradas largas, el `D` puede acabar 2 s tarde y
  seguir en 1,000. La ventana pública no sirve para evaluar el detector de `D`; la DFL sí.

---

## 2. Qué ha hecho Manuel exactamente

Un commit de 1.155 líneas, todas nuevas:

| fichero | qué es |
|---|---|
| `possession/dead_ball.py` | `dead_mask()`: máscara booleana de 199.319 posiciones con `True` entre el primer frame evaluado de cada parte y su saque, sin incluirlo. Los saques son `KICKOFF_VIDEO_FRAMES` de `starter/load_smart_tagging.py` (los del FAQ). 1ª parte: 0 frames; 2ª: 2.934. Con otro partido, `ValueError`. No lee ningún fichero. |
| `possession/io.py` | `load_ball()` y `load_players()`: leen el ATD crudo a arrays por frame de vídeo en metros, `NaN` donde falta. |
| `validation/partido/diagnostico_balon_muerto.py` | solo lo ejecuta una persona. Mide en el ATD: balón fuera del campo; balón visto, quieto y fuera antes de cada `SET PIECE` por tipo; balón quieto en el centro en los saques iniciales; y un experimento de fechar cada reanudación como "balón quieto que empieza a moverse" (5 frames dentro de 0,5 m, buscando desde 10 s antes de la etiqueta). |
| `validation/partido/diagnostico_coordenadas.py` | ¿x = 0,5 separa a los equipos antes de los saques? Temblor del balón entre frames, la columna de velocidad del ATD y tramos con el balón quieto. |
| `validation/scripts/comprobar_balon_muerto.py` | comprueba la v1 sin datos del partido: interfaz, no abre ficheros, 2.934 frames, no contradice la GT pública, determinismo, FAQ frente a `games.py` (±1 frame), otro partido falla. Lo ejecuté: todo en verde. |
| `validation/resultados/2026-11-12_balon_muerto_atd.md` | salidas completas y lectura, con etiquetas [medido]/[inferencia]/[sin verificar]. |
| `docs/decisiones.md` | decisión: v1 = tramo previo al saque; descartadas las dos reglas con el balón; "la vía más prometedora" son los jugadores con la DFL degradada; dos preguntas abiertas a Ismael. |

**Lo que midió en el ATD** (sus agregados, [medido por Manuel]): el balón se ve en el 59,3 % de los frames
evaluados (coincide con `DATA.md`: la alineación del lector es correcta); de los vistos, el 4,2 % está fuera del
campo (3.949 frames, el 85 % por banda); el balón se ve quieto 3 s o más solo 17 veces (radio 0,5 m); en los
saques iniciales no se encuentra el golpeo (0 de 6; solo en 1 se ve el balón 5 frames cerca del centro); su
detector de golpeo "encuentra algo" en los 53 reinicios de los otros tipos, en 51 con menos de 1 s de balón
quieto antes y en 37 a 5 s o más del inicio de la etiqueta; x = 0,5 separa a los equipos en los 6 saques; la
columna de velocidad del ATD no se comporta como m/s (mediana 1,1 frente a 5,1 calculada).

## 3. Lo que está bien

- **Higiene impecable con la regla nº 1:** scripts del partido en `validation/partido/`, solo agregados, saques
  iniciales siempre juntos, mensajes de error sin valores de datos, salida UTF-8 en Windows.
- **Umbrales fijados antes de medir** y cada afirmación con su etiqueta de evidencia.
- **El lector funciona y es rápido:** con un ATD sintético del mismo tamaño, 3,6 s los 46 slots y 0,2 s el balón
  [medido]; alineación `frame_id − 1` y escala a metros correctas.
- **La v1 es exactamente lo que dice el FAQ** y los 2.934 frames están comprobados contra las dos fuentes.
- **La decisión está registrada** con lo probado, lo descartado y lo abierto. Es materia prima directa para el
  documento técnico.
- **Ha descubierto dos cosas que importan para la degradación:** el ATD no congela el balón en el tiempo muerto
  (al revés que la DFL) y casi nunca lo ve fuera del campo ni quieto.

## 4. Crítica

### 4.1 Dos descartes que no se sostienen con lo medido

**"Balón fuera del campo → `D` cubriría muy poco."** Cierto para *cubrir* frames y falso para lo que importa:
3.949 frames fuera repartidos entre unos 70 reinicios por salida del balón (48 en el Smart Tagging; 69 por partido
en la DFL) son **2–3 s de balón visible fuera por cada salida** [inferencia a partir de sus agregados]. El `D`
no hay que *verlo* frame a frame: hay que fechar su **inicio** y su **fin**. En la DFL el `D` empieza 3–4 frames
después de cruzar la línea (experimento 0); en el ATD, el balón que se ve fuera, o el que **desaparece saliendo**
(última posición a menos de 2 m de una línea y velocidad hacia fuera), es el disparo del inicio. No se midió lo
segundo, que es lo que cubre los casos en que el ATD pierde el balón al salir.

**"Lo que encuentra el detector de golpeo no son los reinicios."** La inferencia se apoya en que "antes de un
córner o una falta el balón suele estar colocado y parado más de un segundo, y aquí casi nunca llega a un
segundo". Pero su propia medida dice que el ATD **casi nunca ve el balón quieto** (17 tramos de ≥ 3 s en todo el
partido) y que antes de un córner **no lo ve** (2 de 12 en los 10 s previos). Si el ATD solo recupera el balón
cuando empieza a moverse, lo esperable es justo lo que midió: pocos frames quietos y luego movimiento. Esas 53
detecciones **pueden ser los reinicios reales**, y la medida correcta para saberlo no es cuánto llevaba quieto el
balón, sino si caen donde cae otra señal independiente: el final de la ventana `SET PIECES`, el inicio de la
primera fase posterior (`BALL IN THE BOX` tras un córner) o la subida de velocidad de los jugadores. Son
agregados baratos (sección 7). Antes de verlos, el experimento no está descartado: está sin evaluar.

### 4.2 Casos que no se han tenido en cuenta

1. **Los goles.** El Smart Tagging trae 4 `GOALS` y 4 `Kick Off (After Goal)`. Entre cada gol y su saque hay una
   parada larga (51 y 93 s las dos de `J03WMX` [medido]; unos 4 × 60 s ≈ 6.000 frames aquí, en torno al 4 % de
   los evaluados [inferencia]) con el borde derecho dentro de una ventana de ±2,5 s. Es el `D` más barato del
   partido después del previo al saque y nadie lo usa.
2. **El equipo que reanuda.** No aparece en la v1 ni en su plan, y es lo que más cuesta de todo lo medido. La
   fuente está a mano: el `Team` del `SET PIECE` (córners, saques de puerta, faltas; `N/A` en los saques de banda),
   reglas por tipo (saque de puerta → equipo que defiende esa portería; córner → el que ataca), el jugador que
   está fuera de la banda junto al balón en un saque de banda, y el primer control tras el reinicio (el
   decodificador puede mirar hacia delante). En la DFL el flag de la parada es el equipo que reanuda en el 99,7 %.
3. **Que el `D` no parpadee ni se parta.** No hay duración mínima ni histéresis en ningún sitio. Con la métrica
   es la primera condición de diseño (0,62).
4. **El final de cada parte.** En la DFL el tracking sigue 3–5 s después del pitido final y esos frames son `D`
   [medido]. En el partido no se sabe cuánto dura ese tramo dentro del bloque evaluado, pero es una parada sin
   reinicio: el detector tiene que poder acabar una parte en `D`. Un agregado lo dice (sección 7).
5. **Las paradas dentro del campo** (faltas, lesiones, VAR, cambios): el 32 % de las paradas de la DFL, mediana
   30 s. El Smart Tagging solo tiene 5 faltas. Aquí el balón no sale y a menudo se ve: la única señal es la de
   los jugadores, y la v1 ni la menciona para este caso.
6. **El balón como veto, no solo como disparo.** Balón visible y moviéndose a más de unos m/s varios frames es
   evidencia fuerte de juego vivo. Solo se ha probado el balón como señal positiva de `D`.
7. **Los `SET PIECES` como fin del `D` (B2).** Sigue "abierto" sin que se haya medido lo más básico: cuánto duran
   sus ventanas por tipo (él mismo lo marca [sin verificar]) y si contienen la subida de velocidad de los
   jugadores. Sin eso no se puede usar ni descartar.
8. **La interfaz.** Una máscara booleana no se puede combinar con un decodificador. El plan del repo
   (`investigacion_metodos.md` §4) pide emisiones por frame (log-probabilidad de `H`, `A`, `D`). El módulo
   debería devolver un **score de `D` por frame** más una **lista de anclas** (frame, tipo, equipo, fiabilidad):
   tramos duros (previo al saque, gol→saque), fines de `D` (reinicios), inicios de `D` (salidas). La máscara de
   la v1 cabe ahí como un ancla dura.

### 4.3 Código y comprobaciones

- `possession/io.py` rompía con `IndexError` si el balón venía como un solo token `NaN` [medido con un ATD
  sintético]. El baseline oficial lo tolera (`ball[0] == "N"`). El fichero real no lo trae (el script corrió),
  pero el lector debe ser al menos tan defensivo como el oficial. **Corregido en esta rama.**
- La columna de velocidad del ATD "no se comporta como m/s" porque se compara con el salto entre frames, que
  está dominado por el temblor (mediana de 0,2 m por frame = 5 m/s). Una velocidad **suavizada** daría justo esa
  mediana más baja. Antes de prohibirla, compararla con el desplazamiento suavizado a 0,5–1 s (un coeficiente de
  correlación y un cociente de medianas, nada más).
- `comprobar_balon_muerto.py` compara con la GT pública y pasa por construcción (la v1 solo marca la 2ª parte).
  Él lo dice. Pero el bloque "ningún `D` nuestro donde la GT dice `H` o `A`" seguirá pasando con cualquier
  detector que no toque la ventana pública, y dejará de pasar con cualquiera que la toque bien o mal: no es una
  prueba del detector, es ruido en verde.
- La discusión de ±1 frame entre el FAQ y `games.py` ocupa medio fichero y no importa: un frame de desfase no
  cuesta nada en `spellF1` [doc].
- `dead_mask(paths=None, ...)` ignora las rutas. Correcto para la v1; la firma vale para la interfaz común.

### 4.4 Qué se midió y qué no

Lo que se midió (balón quieto, x = 0,5, temblor) no decidía nada del detector. Lo que sí lo decidía, si los
jugadores dan el estado y el momento del `D`, no se midió, aunque la DFL con etiquetas y los scripts del
experimento 0 estaban disponibles. La sección 5.3 lo mide.

---

## 5. Pruebas nuevas de esta revisión

### 5.1 Coste de cada error (sección 1)

`coste_errores_D.py` y `gt_publica_sin_D.py`. Están en la tabla de la sección 1.

### 5.2 `possession/io.py` con un ATD sintético

`prueba_io.py` [medido]: `frame_id` 1 → índice 0, (0,5; 0,5) → (52,65; 34,00) m; `NaN,NaN,NaN` → `NaN`; un
solo `NaN` → `IndexError` en la v1 de Manuel, corregido en esta rama; slots variables → `ValueError` con mensaje
sin datos; 199.319 líneas × 46 slots en 3,6 s y 73 MB; el balón en 0,2 s.

### 5.3 ¿Sirven los jugadores solos para el `D`? (DFL `J03WMX`, sin usar el balón)

`dfl_D_jugadores.py`. Rasgos solo de posiciones de jugadores, sin identidad (valen igual con slots del ATD):
velocidad media y p75 de los jugadores en ventanas de 1, 2 y 4 s, fracción de jugadores a menos de 1 m/s,
jugadores fuera del campo, jugadores en el área, distancia entre centroides, dispersión, equipos en su mitad.
Umbrales elegidos en una parte y evaluados en la otra. Equipo oráculo para aislar el `D`.

| | parte 2 (62 paradas) | parte 1 (41 paradas) |
|---|---|---|
| AUC por frame de la velocidad media (2 s) | 0,932 | 0,939 |
| AUC de la regresión logística con los 11 rasgos | 0,947 | 0,968 |
| **referencia: sin ningún `D`** (arrastre / adelantando al que reanuda) | 0,781 / 0,801 | 0,852 / 0,869 |
| velocidad media con histéresis: paradas detectadas (≥ 50 %) | 23 / 62 | 18 / 41 |
| · latencia del inicio p10 / p50 / p90 (frames) | +22 / **+171** / +417 | −7 / **+198** / +341 |
| · latencia del fin p10 / p50 / p90 | −17 / +4 / +46 | −10 / +14 / +35 |
| · spellF1 (arrastre / adelantando) | 0,760 / 0,827 | 0,851 / 0,888 |
| regresión logística + histéresis: paradas detectadas | 43 / 62 | 35 / 41 |
| · latencia del inicio p10 / p50 / p90 | −41 / +29 / +167 | −219 / +20 / +95 |
| · latencia del fin p10 / p50 / p90 | −83 / +10 / +48 | −22 / +30 / +186 |
| · inicio a ≤ 1 s / fin a ≤ 1 s | 35 % / 63 % | 29 % / 34 % |
| · spellF1 (arrastre / adelantando) | 0,775 / 0,814 | 0,864 / 0,858 |
| · macroF1 | 0,873 | 0,931 |
| · detectadas por tipo | banda 24/32, falta 6/10, puerta 5/8, córner 7/7, saque 1/1 | banda 17/20, falta 6/8, puerta 6/6, córner 3/3, saque 1/1 |

**Lectura** [inferencia]:

- **El estado sí; el momento no.** Los jugadores separan `D` de vivo con AUC > 0,93 y la logística encuentra el
  70–85 % de las paradas. Pero el inicio llega tarde (los jugadores frenan poco a poco) y disperso, y con eso
  **el spellF1 no mejora frente a no poner `D`** (0,775 frente a 0,781; 0,864 frente a 0,852). El macroF1 sí
  sube mucho (0,87–0,93): es el desempate, no el ranking. Coincide con Lang et al. (92 % por frame, 1,7 s de
  error de frontera) citados en `investigacion_metodos.md`.
- **Ojo con la referencia.** "Sin `D`" con equipo oráculo es optimista: en el pipeline real, durante una parada
  no detectada el candidato por balón emite ruido. El `D` de jugadores protege de eso aunque no sume en esta
  prueba. Pero la conclusión se mantiene: **sin anclas de tiempo del balón o del Smart Tagging, el detector de
  jugadores no gana ranking.**
- **Los rasgos no necesitan la degradación.** Son agregados por equipo sin identidad; con 20,5 objetos de media
  en el ATD cambian poco. El modelo de estado se puede entrenar hoy con los 7 partidos de la DFL; lo que sí hay
  que comprobar en el ATD es el reparto de la velocidad media (un agregado).
- **Paradas largas y cortas.** Córners (mediana 31–36 s), goles (51–93 s) y "sin evento" (lesiones, 68–149 s)
  se detectan todas; las que fallan son saques de banda (12–14 s) y saques de puerta (13–14 s), donde 1–2 s de
  retraso al entrar y al salir se comen media parada.
- **El 90 % de las paradas de `J03WMX` cambia de equipo.** Arrastrar el equipo previo a través de una parada no
  detectada es casi siempre un error; adelantar el que reanuda (lo que haría un decodificador con anclas) es
  mejor en todas las filas.

### 5.4 Qué precisión y qué cobertura hacen falta (DFL `J03WMX`, equipo oráculo)

`dfl_D_precision.py` [medido], media de las dos partes:

| ruido N(0, σ) en los bordes, σ en frames (fila inicio, columna fin) | 0 | 6 | 12 | 25 | 50 |
|---|---|---|---|---|---|
| **0** | 1,000 | 0,954 | 0,946 | 0,946 | 0,933 |
| **6** | 0,988 | 0,947 | 0,941 | 0,937 | 0,921 |
| **12** | 0,977 | 0,941 | 0,925 | 0,910 | 0,904 |
| **25** | 0,953 | 0,913 | 0,899 | 0,903 | 0,883 |
| **50** | 0,919 | 0,876 | 0,878 | 0,880 | 0,858 |

| fracción de paradas con bordes exactos | 30 % | 50 % | 70 % | 85 % | 100 % |
|---|---|---|---|---|---|
| spellF1 (arrastre / adelantando) | 0,876 / 0,888 | 0,923 / 0,905 | 0,932 / 0,949 | 0,965 / 0,978 | 1,000 |

Sesgos sistemáticos: inicio +1 s → 0,944; fin +1 s → 0,953; los dos +1 s → 0,896; los dos +2 s → **0,827**
(= sin `D`); inicio −1 s → 0,924; fin −1 s → 0,919.

**Criterio de aceptación que propongo para cualquier detector de `D`, medido en la DFL antes de tocar el
partido:** |latencia| ≤ 25 frames en el inicio y en el fin en al menos el 70 % de las paradas, sesgo mediano de
cada borde dentro de ±12 frames, `D` espurios ≤ 0,3 por minuto de juego, y ninguna racha de `D` ni de vivo por
debajo de la duración mínima elegida. Con menos que eso, el detector no mejora el ranking.

---

## 6. Propuesta: detector de `D` v2, por capas

Todo devuelve arrays de 199.319 posiciones indexados por frame de vídeo, como pide `CLAUDE.md`. Ningún umbral
sale de la ventana pública; todos se fijan en la DFL (sección 5.4) y se comprueban en el ATD con agregados.

| capa | qué | de dónde sale el tiempo | fiabilidad |
|---|---|---|---|
| **anclas duras** | tramo previo al saque de cada parte (la v1); de cada `GOALS` a su `Kick Off (After Goal)`; final de parte si la última parada no reanuda | FAQ, Smart Tagging | alta |
| **fin del `D` (reinicio)** | dentro de cada ventana `SET PIECES`: primera reaparición del balón con velocidad alta tras un hueco, o la subida de velocidad media de los jugadores; si no hay nada, el centro de la ventana | ATD + Smart Tagging | media–alta |
| **inicio del `D` (salida)** | balón visto fuera de los límites; **última posición vista a menos de ~2 m de una línea con velocidad hacia fuera y hueco largo después**; caída de la velocidad media de los jugadores con la logística de 5.3 | ATD | media |
| **estado** (entre inicio y fin, y en las paradas sin `SET PIECE`: faltas, lesiones) | probabilidad de `D` por frame del modelo de jugadores, entrenado en los 7 partidos de la DFL | ATD | media; es lo que cubre el 40 % de reinicios que al Smart Tagging le faltan |
| **veto de vivo** | balón visible y a más de unos m/s durante varios frames → no `D` | ATD | alta |
| **equipo al reanudar** | `Team` del `SET PIECE`; reglas por tipo; jugador fuera de la banda junto al balón; primer control tras el reinicio (mirando hacia delante) | Smart Tagging + ATD | — |

**Salida del módulo:** `dead_score` (log-probabilidad de `D` por frame), `anchors` (lista de (frame, tipo,
equipo, peso)) y la máscara dura. **La histéresis y la duración mínima viven en el decodificador**, que es quien
puede prohibir rachas cortas de `D` y de vivo y colocar el cambio de equipo donde lo pide la evidencia de los
dos lados. Sin decodificador, una máscara con umbral parpadea.

**Qué no hacer:** suavizar el `D` con un voto por mayoría (introduce justo el retraso de 1–2 s que lo anula);
usar la ausencia del balón como `D` (lo que hace el baseline y por lo que tiene recall 0,21 en `D`); arrastrar el
equipo anterior a través de una parada.

## 7. Agregados baratos que solo Manuel puede ejecutar (sin frames, sin jugadas)

Cada uno decide algo de la sección 6. Están escritos en tres scripts de `validation/partido/`:
`agregados_smart_tagging.py` (1), `agregados_balon_reinicios.py` (2, 3 y 5) y `agregados_jugadores.py` (4 y 6).
Solo imprimen agregados; se han probado con un partido sintético, no con el real.

1. **Duración de las ventanas `SET PIECES` por tipo** (cuantiles 10/50/90) y, para los otros códigos, qué
   fracción de los frames evaluados cubre al menos una fase que no sea `SET PIECES`. Decide cómo usar B2.
2. **Cruce de las 53 "reanudaciones" del detector de golpeo con el fin de su ventana `SET PIECES` y con la
   subida de velocidad media de los jugadores** (desfase en intervalos gruesos: < 0,5 s, 0,5–1, 1–2,5, > 2,5 s).
   Decide si el descarte de 4.1 era correcto.
3. **Huecos largos del balón (> 2 s) cuya última posición está a menos de 2 m de una línea y con velocidad hacia
   fuera:** cuántos hay, y qué fracción de las ventanas `SET PIECES` de banda, córner y puerta tiene uno en los
   15 s previos. Decide el disparo del inicio del `D`.
4. **Velocidad media de los jugadores:** cuantiles en todo el partido, en los 5 s posteriores al inicio de cada
   `SET PIECE`, y en los 30 s finales de cada bloque evaluado. Dice si el modelo de la DFL se traslada y si el
   final de cada parte es `D`.
5. **La columna de velocidad del ATD frente al desplazamiento suavizado a 0,5 y 1 s:** correlación y cociente
   de medianas. Decide si se puede usar.
6. **Jugadores fuera de los límites por frame** (cuantiles y fracción de frames con alguno), y lo mismo en las
   ventanas de saque de banda. Decide el equipo que reanuda en los saques de banda.

## 8. El plan

**Dónde dice el plan que estaríamos y dónde estamos.** El calendario de `CLAUDE.md` e `investigacion_metodos.md`
§4.4 ponía el jueves 12 "primera versión de `D` y de posesión, primera entrega validada que bata el baseline" y el
viernes 13 "modelo temporal integrado". Es viernes 13 por la noche: no hay `pipeline.py`, `candidates.py`,
`temporal.py` ni `ball.py`; no hay ninguna entrega nuestra; el `D` cubre el 1,8 % de los frames. Lo que hay son
dos experimentos buenos (0 y 1) y un diagnóstico. Se congela el lunes 16 por la noche.

**Lo que no cuadra en "Lo siguiente, en este orden":**

- El recuento manual del vídeo y la convención de control van primero y **bloquean** todo lo demás. No deberían:
  la convención es un parámetro del candidato de posesión; el pipeline se monta igual y se cambia el parámetro
  cuando llegue el recuento.
- El `D` solo aparece como "degradación DFL→ATD con el balón tapado" y como "B3/B4 entrenado con la DFL
  degradada". La degradación necesita el perfil del ATD (paso 5, pendiente) y es "el eslabón más débil" según el
  propio informe. **Para el estado del `D` con rasgos de equipo no hace falta degradar** (5.3), y para el tiempo
  del `D` lo que hace falta son los agregados de la sección 7, que no dependen de nada.
- No hay ningún paso que mida el detector de `D` con el criterio de 5.4 antes de integrarlo. Sin eso se
  integrará un detector que no suma, o que resta.
- "Ningún `D` perdido cuesta 0,37" (`investigacion_metodos.md` §1.3) ha llevado a pensar el `D` como cobertura.
  Las medidas de aquí dicen que el `D` tarde o tembloroso cuesta lo mismo que el `D` perdido. El riesgo real del
  equipo no es no detectar paradas: es detectarlas 2 s tarde y creer que suma.

**Lo que propondría para los cuatro días que quedan:**

| día | qué | quién |
|---|---|---|
| sáb 14 (mañana) | **pipeline de punta a punta, aunque sea tonto:** `io` → limpieza mínima → candidato N2 → decodificador con coste de cambio e histéresis → `D` duro (v1 + goles→saque + `SET PIECES` como fin) → CSV validado y puntuado en la ventana pública **solo para ver que no está roto** | Ismael + uno |
| sáb 14 (en paralelo) | los 6 agregados de la sección 7 | Manuel |
| sáb 14 (en paralelo) | modelo de estado de `D` con los 7 partidos de la DFL (rasgos de 5.3, dejando un partido fuera) y el criterio de 5.4 como aceptación; `dead_score` + anclas con la interfaz de la sección 6 | quien lleve `D`, con Claude |
| dom 15 | integrar `D` v2 en el decodificador; harness en la DFL para comparar con/sin cada capa; la convención de control como parámetro cuando llegue el recuento | todos |
| lun 16 | congelar, reproducir byte a byte en una máquina limpia, documento | Ismael, Ana |
| mar 17 | validar el fichero exacto y entregar con margen | Ismael |

**Las dos preguntas de Manuel a Ismael**, por si sirve: (1) los frames de saque de `starter/load_smart_tagging.py`
son código oficial y los publica el FAQ; coinciden con `games.py` a ±1 frame, que es gratis: vale. (2) Agregados
por tipo de reinicio con 5 casos o más no identifican jugadas: cumplen el espíritu de la regla; yo los dejaría.

## Sin verificar

- Que el bloque evaluado del partido termine, como en la DFL, unos segundos después del pitido (agregado 4).
- Que la velocidad media de los jugadores del ATD se reparta como en la DFL (agregado 4). Si el temblor de los
  slots la infla, hay que suavizar más o usar la fracción de jugadores lentos.
- Cuánto se traslada el modelo de estado de una liga a otra: aquí se ha probado dentro de un partido (parte
  contra parte), que es optimista. Con los 7 partidos se mide dejando uno fuera.
- Si las 53 detecciones del detector de golpeo son reinicios (agregado 2).
