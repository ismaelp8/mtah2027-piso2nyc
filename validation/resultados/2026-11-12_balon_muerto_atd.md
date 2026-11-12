# ¿Sirve el balón del ATD para el detector de balón muerto?

- **Fecha:** 2026-11-12 · **Quién:** Manuel Herrero ejecutó los scripts en local; Claude los escribió, en
  la sesión de Manuel, sin acceso a los datos.
- **Datos:** el ATD táctico del partido (`BAR-ATH_tactical_atd.txt` y `_atd.xml`) y su Smart Tagging
  (`BAR-ATH_tactical_smart_tagging.xml`), del paquete de la organización descargado de su Drive el
  12/11/2026. El paquete no trae número de versión.
- **Código:** el commit de `main` que añade este fichero
  (`git log --diff-filter=A -- validation/resultados/2026-11-12_balon_muerto_atd.md`).
- **Comandos:**
  ```bash
  python validation/partido/diagnostico_balon_muerto.py
  python validation/partido/diagnostico_coordenadas.py
  python validation/scripts/comprobar_balon_muerto.py
  ```
- **Para qué:** decidir con qué señales se construye el detector de `D` (`possession/dead_ball.py`).
  Antes de escribir reglas con el balón había que saber si el ATD ve el balón fuera del campo, en los
  reinicios y quieto, y si x = 0,5 es la mitad del campo.
- **Lectura en tres líneas:**
  1. **Con la regla probada, el balón del ATD no fecha ni saques ni reinicios.**
     - **[medido]** No encuentra el golpeo en ninguno de los 6 saques iniciales.
     - **[medido]** De los frames con balón, solo el 4,2 % lo tiene fuera del campo, y quieto 3 s o más
       se ve 17 veces en los frames evaluados (radio 0,5 m).
     - **[inferencia]** En los demás reinicios lo que encuentra no son los reinicios reales.
  2. **[medido]** **x = 0,5 separa a los dos equipos en los 6 saques iniciales.** Que sea exactamente la
     línea de medio campo está **[sin verificar]**. El 10 % de los saltos del balón entre frames mide
     4 cm o menos.
  3. **El detector de `D` se queda en la versión 1** (los 2.934 frames antes del saque de la 2ª parte).
     Otras reglas con el balón no se han probado. **[inferencia]** La vía más prometedora para el resto
     parece la de los jugadores con la Bundesliga degradada.
- **Dudas de `PASOS.md`:** responde en parte a la **D18** (cómo es el ATD). Toca la propuesta del
  experimento 0 sobre el balón congelado, pero con otra métrica (ver «El balón quieto»). No resuelve la
  D13. El paso 5 (perfil completo del ATD) sigue pendiente.
- **Regla de datos:** solo agregados del partido entero.
  - Los saques iniciales van siempre juntos (los 6): por separado serían jugadas identificables
    (`PASOS.md`, paso 5).
  - Los demás reinicios van por tipo (26 saques de banda, 12 córners, 10 saques de puerta y 5 faltas),
    con intervalos gruesos. Es un criterio propio: el tipo hace falta para diseñar el detector, y cada
    tipo junta 5 casos o más.
  - `PASOS.md` pide los `SET PIECES` "todos juntos" para el perfil del ATD. Queda preguntado a Ismael en
    la PR; si prefiere juntarlos, se cambia el script y se vuelve a ejecutar.

## Salidas

Los dos diagnósticos se ejecutaron con la versión de esta PR. Las secciones cuyo cálculo no cambió entre
versiones dieron las mismas cifras que en las ejecuciones anteriores: 1, 2 y 4 del primero, y 1, 2 y 3
del segundo. Con la versión anterior, cada script se ejecutó dos veces y las dos salidas fueron
idénticas salvo la línea del tiempo.

### `validation/partido/diagnostico_balon_muerto.py`

```
1. Balón en los frames evaluados
   frames evaluados  158857   con balón   94214 ( 59.3 %)
   fuera del campo por más de 0 m:   3949 (  4.2 % de los vistos)   por fondo    602   por banda   3347
   fuera del campo por más de 1 m:   2525 (  2.7 % de los vistos)   por fondo    374   por banda   2151
   fuera del campo por más de 3 m:   1555 (  1.7 % de los vistos)   por fondo    169   por banda   1386

2. Reinicios del Smart Tagging (SET PIECES), por tipo
   throw-in               n= 26
      visto en la ventana                     26  (100.0 %)
      visto >50 % de la ventana               22  ( 84.6 %)
      quieto en la ventana                    26  (100.0 %)
      visto en los 10 s previos               18  ( 69.2 %)
      fuera del campo en los 10 s previos     10  ( 38.5 %)
   corner kick            n= 12
      visto en la ventana                     12  (100.0 %)
      visto >50 % de la ventana                9  ( 75.0 %)
      quieto en la ventana                    12  (100.0 %)
      visto en los 10 s previos                2  ( 16.7 %)
      fuera del campo en los 10 s previos      0  (  0.0 %)
   goal kick              n= 10
      visto en la ventana                     10  (100.0 %)
      visto >50 % de la ventana                8  ( 80.0 %)
      quieto en la ventana                    10  (100.0 %)
      visto en los 10 s previos                9  ( 90.0 %)
      fuera del campo en los 10 s previos      3  ( 30.0 %)
   kick off (todos)       n=  6
      visto en la ventana                      5  ( 83.3 %)
      visto >50 % de la ventana                1  ( 16.7 %)
      quieto en la ventana                     5  ( 83.3 %)
      visto en los 10 s previos                2  ( 33.3 %)
      fuera del campo en los 10 s previos      1  ( 16.7 %)
   free kick              n=  5
      visto en la ventana                      5  (100.0 %)
      visto >50 % de la ventana                4  ( 80.0 %)
      quieto en la ventana                     5  (100.0 %)
      visto en los 10 s previos                2  ( 40.0 %)
      fuera del campo en los 10 s previos      1  ( 20.0 %)

3. Saques iniciales, todos juntos: ¿se ve el balón quieto en el centro?
   saques iniciales (de inicio de parte y tras gol): 6
      con balón visto en los 10 s previos o en la ventana                  5 de 6
      con el balón 5 frames o más a menos de 2 m del centro                1 de 6
      con balón visto, pero menos de 5 frames a menos de 2 m del centro    4 de 6
      reanudación encontrada con el balón quieto en el centro              0 de 6
   ¿las etiquetas Kick Off (Start) contienen los saques publicados en FAQ.md? sí

4. Máscara D de possession/dead_ball.py
   frames D   2934 de 158857 evaluados (  1.8 %)   fuera de los evaluados 0

5. Experimento descartado: reanudación como balón quieto que empieza a moverse
   throw-in               n= 26   encontrada  26 (100.0 %)
      segundos desde el inicio de la etiqueta hasta la reanudación
         0–1 s          1  (  3.8 %)
         1–2.5 s        4  ( 15.4 %)
         2.5–5 s        4  ( 15.4 %)
         ≥5 s          17  ( 65.4 %)
      cuánto llevaba quieto el balón antes de la reanudación
         0–1 s         24  ( 92.3 %)
         1–3 s          2  (  7.7 %)
         3–10 s         0  (  0.0 %)
         ≥10 s          0  (  0.0 %)
   corner kick            n= 12   encontrada  12 (100.0 %)
      segundos desde el inicio de la etiqueta hasta la reanudación
         0–1 s          0  (  0.0 %)
         1–2.5 s        0  (  0.0 %)
         2.5–5 s        0  (  0.0 %)
         ≥5 s          12  (100.0 %)
      cuánto llevaba quieto el balón antes de la reanudación
         0–1 s         12  (100.0 %)
         1–3 s          0  (  0.0 %)
         3–10 s         0  (  0.0 %)
         ≥10 s          0  (  0.0 %)
   goal kick              n= 10   encontrada  10 (100.0 %)
      segundos desde el inicio de la etiqueta hasta la reanudación
         0–1 s          3  ( 30.0 %)
         1–2.5 s        1  ( 10.0 %)
         2.5–5 s        3  ( 30.0 %)
         ≥5 s           3  ( 30.0 %)
      cuánto llevaba quieto el balón antes de la reanudación
         0–1 s         10  (100.0 %)
         1–3 s          0  (  0.0 %)
         3–10 s         0  (  0.0 %)
         ≥10 s          0  (  0.0 %)
   kick off (todos)       n=  6   encontrada   0 (  0.0 %)
      segundos desde el inicio de la etiqueta hasta la reanudación
         0–1 s          0  (  —  )
         1–2.5 s        0  (  —  )
         2.5–5 s        0  (  —  )
         ≥5 s           0  (  —  )
      cuánto llevaba quieto el balón antes de la reanudación
         0–1 s          0  (  —  )
         1–3 s          0  (  —  )
         3–10 s         0  (  —  )
         ≥10 s          0  (  —  )
   free kick              n=  5   encontrada   5 (100.0 %)
      segundos desde el inicio de la etiqueta hasta la reanudación
         0–1 s          0  (  0.0 %)
         1–2.5 s        0  (  0.0 %)
         2.5–5 s        0  (  0.0 %)
         ≥5 s           5  (100.0 %)
      cuánto llevaba quieto el balón antes de la reanudación
         0–1 s          5  (100.0 %)
         1–3 s          0  (  0.0 %)
         3–10 s         0  (  0.0 %)
         ≥10 s          0  (  0.0 %)
   frames con el balón quieto antes de una reanudación: 466 (  0.3 % de los evaluados)

   tiempo 1 s
```

### `validation/partido/diagnostico_coordenadas.py`

```
1. Coordenadas normalizadas (0–1) en los frames evaluados
   balón x       p0.5=-0.000   p5=0.071   p50=0.503   p95=0.891   p99.5=0.970
   balón y       p0.5=-0.013   p5=0.075   p50=0.543   p95=0.975   p99.5=1.126
   jugadores x   p0.5=0.015   p5=0.088   p50=0.502   p95=0.903   p99.5=0.982
   jugadores y   p0.5=0.025   p5=0.155   p50=0.519   p95=0.908   p99.5=1.005
   frames con el balón a menos de 2 m de (0,5; 0,5): 413 (  0.4 % de los vistos)

2. En el segundo anterior al inicio de cada etiqueta de saque inicial, todas juntas
   saques iniciales: 6   con los dos equipos a lados opuestos de x = 0,5: 6 de 6
   local (H)      jugadores vistos por frame 10.6   en su lado:  91.1 %
   visitante (A)  jugadores vistos por frame 10.7   en su lado:  87.9 %

3. Temblor del balón entre frames seguidos, los dos con balón, en los evaluados
   pares de frames 94065
   salto (m)               p10=0.040   p25=0.095   p50=0.203   p75=0.382   p90=0.572   p99=0.984
   salto × 25 (m/s)        p10=1.005   p25=2.370   p50=5.082   p75=9.538   p90=14.310   p99=24.604
   velocidad del ATD       p10=0.226   p25=0.618   p50=1.130   p75=1.609   p90=3.242   p99=5.262

4. Tramos con el balón quieto en los evaluados (cada parte por separado; un hueco sin
   balón de hasta 1 s no corta el tramo)
   radio 0.5 m   ≥1 s:  122   ≥3 s:   17   ≥10 s:    2   frames en tramos ≥3 s: 2402 (  1.5 % de los evaluados)
   radio 1.0 m   ≥1 s:  249   ≥3 s:   30   ≥10 s:    2   frames en tramos ≥3 s: 4033 (  2.5 % de los evaluados)
   radio 2.0 m   ≥1 s:  556   ≥3 s:   59   ≥10 s:    3   frames en tramos ≥3 s: 7336 (  4.6 % de los evaluados)

   tiempo 6 s
```

### `validation/scripts/comprobar_balon_muerto.py`

Solo lee el código y la GT pública, así que la puede ejecutar Claude.

```
1. Interfaz común
  [OK] es un np.ndarray
  [OK] 199.319 posiciones   (199319,)
  [OK] booleana   bool
  [OK] no abre ningún fichero   0 abiertos

2. Dónde marca D
  [OK] nada fuera de los frames evaluados   0 frames
  [OK] parte 1: 0 frames D   tiene 0
  [OK] parte 2: 2934 frames D   tiene 2934
  [OK] parte 2: un solo tramo, del primer frame evaluado al anterior al saque
  [OK] 2ª parte: los 2934 frames que da FAQ.md   tiene 2934

3. Frente a la GT pública (solo para comprobar que no se contradicen; no valida el detector)
  [OK] la GT pública tiene 199.319 filas   199319
  [OK] ningún D nuestro donde la GT pública dice H o A   0 frames
  [OK] la GT pública no tiene D en el primer frame evaluado (no hay tramo antes del saque)
  (informativo) D de la GT pública que cubre esta versión: 0 de 1469

4. Determinismo
  [OK] dos llamadas dan la misma máscara byte a byte
  sha256 4069162c187c7cc9

5. Las dos fuentes de los frames de saque
  [OK] parte 1: FAQ.md y el ancla de games.py difieren en 1 frame como mucho   diferencia +1
  [OK] parte 2: FAQ.md y el ancla de games.py difieren en 1 frame como mucho   diferencia -1

6. Otro partido
  [OK] con otro partido da un error en vez de una máscara

TODO BIEN
```

Además, se rompió el detector a propósito de tres maneras (tramo desplazado un frame, abrir un fichero,
marcar `D` en la 1ª parte) y el script falló en las tres.

## Qué dice cada medida

### El balón fuera del campo

- **[medido]** El ATD ve el balón en el 59,3 % de los frames evaluados. `DATA.md` dice lo mismo
  (le falta en el 41 %). De esos frames con balón, el 4,2 % lo tiene fuera del campo, y el 85 % de ellos
  (3.347 de 3.949) por la banda.
- **[medido]** En los 10 s previos a un reinicio, el balón se ve fuera en:
  - 10 de 26 saques de banda (se ve en 18);
  - 3 de 10 saques de puerta (se ve en 9);
  - 0 de 12 córners, pero antes de un córner el balón solo se ve en 2 de 12.
- **[inferencia]** Cuando el balón sale, el ATD casi siempre lo pierde, así que "balón fuera del campo →
  `D`" cubriría muy poco del tiempo muerto.

### Los saques iniciales

- **[medido]** En los 6 saques iniciales, en el segundo anterior al inicio de la etiqueta, los dos
  equipos quedan a lados opuestos de x = 0,5. Está en su lado el 91,1 % de los jugadores vistos del local
  y el 87,9 % de los del visitante. "Su lado" es el de la mayoría de su equipo, así que esos porcentajes
  son del 50 % o más por construcción. Lo que cuenta como prueba es el 6 de 6.
- **[fuente]** El Smart Tagging etiqueta 2 de esos saques como de inicio de parte y 4 como tras gol
  (`DATA.md`). El reglamento obliga a cada equipo a estar en su mitad antes del saque.
- **[sin verificar]** Que x = 0,5 sea exactamente la línea de medio campo, y no esté a un par de metros.
  Tampoco se ha comprobado nada de y.
- **[sin verificar]** Por qué un 9–12 % de jugadores queda al otro lado. Posibles causas que estas medidas
  no separan:
  - jugadores pegados a la línea con ruido de posición;
  - la ventana incluye el golpeo si la etiqueta empieza tarde;
  - x = 0,5 algo desplazada.
- **[medido]** En 5 de 6 saques se ve balón en los 10 s previos o en la ventana, pero en los 10 s
  previos solo en 2 de 6. Solo en 1 se ve el balón 5 frames o más a menos de 2 m del centro; en los
  otros 4 se ve, pero menos de 5 frames cerca del centro.
- **[fuente]** La ventana del Smart Tagging dura unos 5 s alrededor del saque
  (`starter/load_smart_tagging.py`), así que incluye frames posteriores al golpeo.
- **[sin verificar]** Para esos 4 hay tres explicaciones que estas medidas no separan:
  1. el ATD solo ve el balón después del golpeo, cuando ya ha salido del centro;
  2. el balón del centro queda tapado por los jugadores;
  3. el ATD sigue algo que no es el balón de juego (otro balón, un objeto, un falso positivo).
- **Cómo se separarían:** con un agregado de los 6 saques juntos. Frames con balón antes y después del
  inicio de la etiqueta, y distancia mínima al centro solo en el tramo previo.
- **Consecuencia para el detector:** ninguna. Sea cual sea la explicación, con esta regla el golpeo no se
  fecha con el balón. Para `ball.py` queda como pregunta abierta si el ATD sigue a veces objetos que no
  son el balón.

### El temblor y la velocidad del balón

- **[medido]** El 10 % de los saltos entre frames seguidos con balón mide 4 cm o menos.
- **[inferencia]** Cuando el ATD ve bien un balón quieto, lo sitúa con precisión de centímetros. Pero
  esos saltos pequeños también pueden ser de un balón que rueda despacio, así que no lo prueban.
- **[medido]** La columna de velocidad del balón del ATD no se comporta como la velocidad del balón en
  m/s:
  - mediana de 1,1 frente a 5,1 m/s calculados con las posiciones;
  - percentil 99 de 5,3 frente a 24,6.

  Qué mide de verdad **[sin verificar]**. Hasta saberlo, no hay que usarla.
- **[medido]** El balón cae fuera de [0, 1] en y bastante más por un lado (p99,5 = 1,126) que por el
  otro (p0,5 = −0,013).
- **[sin verificar]** Se ve mejor fuera del campo en la banda más cercana a la cámara, o allí hay otros
  balones u objetos.

### El balón quieto

- **[medido]** Tramos con el balón a menos de 0,5 m del primer punto del tramo, en los frames evaluados
  y con huecos sin balón de hasta 1 s dentro del tramo:
  - de 3 s o más, 17;
  - con radio de 2 m, 59, que suman el 4,6 % de los frames evaluados.
- **[medido]** Exigiendo frames con balón seguidos, sin ningún hueco, las cifras salen idénticas.
  - Se midió con una versión anterior del script, que no llegó a git.
  - Se puede repetir poniendo `MAX_GAP_FRAMES = 0` en `validation/partido/comun.py`.
- **[sin verificar]** Por qué salen idénticas. Hay dos explicaciones que esta medida no separa:
  1. dentro de los tramos con el balón quieto el ATD no tiene huecos cortos;
  2. cuando pierde el balón un momento, no lo vuelve a ver en el mismo sitio.
- **[inferencia]** Aunque todos esos tramos fueran `D`, serían el 4,6 % de los frames, y se espera que en
  torno al 40 % sean `D` (`docs/investigacion_metodos.md` §2.2, **[fuente]**). El balón quieto no puede
  sostener el detector.
- **[inferencia]** El ATD no congela el balón durante el tiempo muerto, al revés que la DFL (experimento
  0). Es otra métrica que la de la propuesta de `PASOS.md` (posición idéntica a la del frame anterior).
  Al degradar la Bundesliga hay que tapar su balón en los `D`, como ya se decidió.

### El experimento descartado: fechar la reanudación con el balón quieto que se mueve

- **Qué se probó:** en cada reinicio del Smart Tagging, el primer frame de la ventana en que el balón,
  visto quieto justo antes, empieza a moverse.
  - "Quieto" son 5 frames vistos dentro de 0,5 m. Se busca desde 10 s antes de la etiqueta, y un hueco
    sin balón de más de 1 s lo olvida.
  - En los saques iniciales, además, quieto a menos de 2 m del centro.
  - Los umbrales se fijaron antes de medir.
- **[medido]** En los saques de banda, córners, saques de puerta y faltas encuentra algo en los 53. En 51
  el balón llevaba quieto menos de 1 s, en 2 entre 1 y 3 s, y en ninguno 3 s o más. En los saques
  iniciales no encuentra nada (0 de 6).
- **[medido]** Los tramos de balón quieto antes de esas "reanudaciones" suman 466 frames (0,3 % de los
  evaluados).
- **[medido]** En 37 de los 53, la "reanudación" cae 5 s o más después del inicio de la etiqueta.
- **[sin verificar]** Cuánto duran las ventanas del Smart Tagging en los demás reinicios (la de los
  saques iniciales dura unos 5 s, ver arriba).
- **[inferencia]** Lo que encuentra no son los reinicios. Antes de un córner, un saque de puerta o una
  falta, el balón suele estar colocado y parado más de un segundo, y aquí casi nunca llega a un segundo.
  En los saques de banda (26 de los 53) el balón va en las manos, así que esta regla casi no puede
  aplicarse.

## Qué cambia

- **`possession/dead_ball.py`, versión 1:** solo el tramo antes del saque de cada parte, con los frames
  de saque que publica `FAQ.md` (`KICKOFF_VIDEO_FRAMES` de `starter/load_smart_tagging.py`).
  - Son 2.934 frames en la 2ª parte y 0 en la 1ª, que es lo que dice el FAQ.
  - Las anclas de `games.py` difieren en ±1 frame, en sentidos opuestos en cada parte. `games.py` las
    describe como el frame en que se golpea el balón, así que puede ser una diferencia de convención.
    Con ellas saldrían 2.933 frames `D` en la 2ª parte y 1 en la 1ª: justo el primer frame evaluado,
    que el FAQ ("the first half is graded from the kickoff itself") y la GT pública dan como balón en
    juego.
  - La decisión está en `docs/decisiones.md`.
- **Para el resto del `D`:**
  - las dos reglas probadas con el balón quedan descartadas;
  - otras reglas con el balón (combinado con la posición, el tiempo sin verlo o los jugadores) no se
    han probado;
  - **[inferencia]** la vía más prometedora parece el enfoque con jugadores (B3 o B4 de
    `docs/investigacion_metodos.md` §2.2), entrenado y validado con la Bundesliga degradada.
- **Para la degradación de la Bundesliga (D18):**
  - el balón del ATD falta en el 40,7 % de los frames evaluados;
  - se ve quieto 3 s o más muy pocas veces;
  - casi nunca se ve fuera del campo;
  - queda abierto si a veces sigue un objeto que no es el balón de juego.
- **Para el perfil completo del ATD (paso 5 de `PASOS.md`):** faltan los huecos por duración, la tabla 3 ×
  3, los slots y los saltos imposibles.
