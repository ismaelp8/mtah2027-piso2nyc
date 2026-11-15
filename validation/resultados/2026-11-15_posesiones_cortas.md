# Posesiones cortas: por qué predecimos menos posesiones de las que hay · 2026-11-15 · Claude (sesión de Ismael)

- **Fecha y quién:** 15/11/2026. Lo pidió Ismael al reabrir la evidencia de equipo («predecimos muchas menos
  posesiones de las que hay, sobretodo cuando son posesiones cortas»; `docs/decisiones.md`). Lo escribió y
  lo ejecutó Claude, en la rama `claude/posesiones-cortas-5e84f8`, que entró en `main` en un solo commit.
  La rama se conserva en GitHub: sus commits prueban que cada regla se subió antes de medir.
- **Datos:** los 7 partidos de la Bundesliga (Bassek et al., 2025, CC BY 4.0) con el balón «como el ATD», y
  la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`, 10 partidos de la A-League 2024/25,
  licencia MIT) con el balón «detectado». El examen de SkillCorner (`lector.EXAMEN`) no se ha tocado. Nada
  del partido.
- **Código:** `main` en `3b227c4` más `validation/posesiones_cortas/` (bitácora en su `BITACORA.md`); B9 y sus
  medidas, en `4e662ad`. B5 con los coeficientes que no vieron cada partido en la DFL, y con los de la entrega
  en SkillCorner. El `D` de las etiquetas (oráculo), como el harness, salvo en los criterios con el `D`
  propio.
- **Qué es:** un diagnóstico descriptivo (puntos 1 a 8, sin regla previa) y la medida de un candidato, B9,
  leída con la regla que se subió antes de entrenarlo (punto 9 y `docs/decisiones.md`).

## Lectura corta

1. **Con el flag, la mayor parte de lo que perdemos es convención** [medido].
   - De las 3.061 posesiones del flag, 1.492 no existen con el control: 793 son toques del rival sin control
     y 699 son trozos del equipo que retiene, partidos por esos toques. `main` encuentra el 5 y el 9 %.
   - Son unas 1.390 de las 1.863 que no encontramos: tres cuartos.
   - Las etiquetas del control, puntuadas como predicción contra el flag, sacan 0,648. Es el techo de un
     método perfecto que exija control, si la GT fuera el flag.
2. **Pero `main` saca un ritmo casi fijo, sea cual sea la GT** [medido]. Posesiones por minuto vivo:

   | | reales | `main` |
   |---|---|---|
   | DFL, control | 4,71 | 4,50 |
   | SkillCorner (también exige control) | 6,05 | 4,25 |
   | DFL, flag | 8,30 | 4,50 |
   | partido (la GT pública son 17 posesiones) | 4,2 | 3,7 |

   Las tres primeras filas van con el `D` de las etiquetas; la del partido, con el nuestro.
   - Si la GT del reto se parece a SkillCorner, nos falta de verdad un 30 % [inferencia].
   - Si se parece al control de la DFL, el número cuadra y el fallo es dónde cambiamos.
3. **En las posesiones que no encontramos, la evidencia de B5 apunta al otro equipo durante casi toda la
   posesión** [medido]. En las que se pierden por «otro equipo», la suma de la evidencia a favor del equipo
   bueno es de −6 a −11 veces lo que cuesta meterlas, y solo el 1–3 % la paga.
   - **Bajar el coste de cambio, por sí solo, no las arregla** [inferencia, con eso y con que los costes 12 y
     50 ya empataron]: hay que cambiar el signo de la evidencia.
   - El decodificador no se limita a seguir el signo frame a frame: con el signo saldrían 2.531 posesiones
     en la DFL, y el Viterbi da 1.661 [medido].
4. **Lo que empuja en contra son las señales lentas** [medido]: el balón en ventanas de 151 frames, la
   velocidad de los equipos y la dispersión. Las señales rápidas (el más cercano y el balón en 1 y 13
   frames) van a favor, pero pesan diez veces menos.
5. **Las que «se funden con la de al lado» son una consecuencia** [medido]: su evidencia está bien (la paga
   el 90–99 %). Se funden porque falta la posesión corta del rival que va en medio.
6. **Con el flag, en las de menos de 2 s, el más cercano no dice nada frame a frame** [medido]: es del equipo
   bueno en el 49–57 % de los frames con balón, **también con el balón limpio**. No es un efecto del
   suavizado.
   - Con el control es otra cosa: el 82 % en las de menos de 1 s y el 58–60 % en las de 1 a 2 s.
   - La dirección del balón (punto 9) da el 66–68 % en las de 1 a 2 s.

   Lo que más se puede ganar está en las de 2 a 10 s [inferencia].
7. **Entrenar con tracking automático no lo arregla** [medido]: con los rasgos de B5 entrenados con todos los
   frames vivos de SkillCorner, y mirando en los mismos partidos (lo más optimista posible), las de 2 a 5 s
   siguen en el 29–30 % y el spellF1 pasa de 0,519 a 0,520–0,528. Limitan los rasgos, no las filas.
8. **«Proponer y clasificar» trozos del rival tiene un techo bajo** [medido]: con un clasificador perfecto
   gana de +0,008 a +0,013 con el control. Solo el 2–11 % de las propuestas son buenas.
9. **La dirección en que se mueve el balón es la única señal nueva que encuentra posesiones cortas** [medido]:
   B9 (B5 con esa señal) gana a `main` con §5.8 usando el flag (+0,039 y +0,048, dejando un partido fuera),
   y el placebo lo confirma. Pero:
   - empata con el control;
   - empeora los duelos sin cambio más de lo permitido;
   - **no mejora en SkillCorner** (−0,005 y +0,004).

   Con la regla escrita antes de medir, es un empate: **B5 se queda.**
   - SkillCorner también exige control, y B9 también empata con el control de la DFL. **No se puede separar**
     si en SkillCorner falla por el tracking automático o por la convención.

10. **Fase 2: las posesiones largas se pierden por lo mismo** [medido, con el `D` de las etiquetas]. De las
    de 10 s o más que existen con las dos convenciones se pierden pocas: 41 de 646 con el control y 42 de
    578 con el flag.
    - El 73–81 % se pierde solo porque no vemos una posesión del rival pegada a ella; esa vecina dura 2 s o
      más en la mitad de los casos.
    - En las de 5 a 10 s, la mitad es eso y la otra mitad, que decimos el otro equipo.
    - Ninguna se pierde por cómo el decodificador coloca los cambios.
    - Con nuestro `D` (descriptivo) se suman los bordes con un `D` y las paradas falsas dentro de las largas.
    - Detalle: `validation/posesiones_cortas/BITACORA.md` §8.
11. **Lo que vale cada tipo de fallo** [medido, con un oráculo que arregla solo ese tipo, `D` de las
    etiquetas, «como el ATD»]:

    | arreglo | flag | control | SkillCorner |
    |---|---|---|---|
    | faltan, decimos el otro equipo, 2–10 s | +0,240 | +0,123 | +0,191 |
    | faltan, decimos el otro equipo, < 2 s | +0,254 | +0,045 | +0,200 |
    | sobran, cambio real desplazado | +0,088 | +0,051 | +0,084 |
    | sobran, inventadas | +0,016 | +0,074 | +0,065 |
    | sobran, solo las inventadas con las dos convenciones | +0,015 | +0,027 | – |
    | faltan, decimos el otro equipo, ≥ 10 s | +0,011 | +0,007 | +0,035 |

    - De las 402 que sobran con el control, 143 son inventadas, 76 son un cambio real desplazado, 150 son
      trozos de una posesión real partida y 33 están fundidas.
    - Las inventadas con las dos convenciones son 60, y 38 acaban justo antes de una parada. Ni con un
      oráculo llegan a +0,03 [medido].
    - Detalle: `validation/posesiones_cortas/BITACORA.md` §9.
12. **`main` con el balón tarde** [medido, descriptivo, `D` de las etiquetas, «como el ATD»]: con 6, 12 y 25
    frames de retraso cae −0,001, −0,027 y −0,057 con el flag, y −0,019, −0,088 y −0,184 con el control. La
    medida de Antonio (PR 11) da unos 4 frames de retraso del balón del ATD respecto a los jugadores.
13. **Fase 3: con estos rasgos no hay más, ni con un modelo flexible** [medido, puerta con la regla subida
    antes en `3193b43`; fuera de muestra, `D` de las etiquetas]. Se probó una red de una capa de 32 con los
    rasgos de B9, y con ellos más 6 señales de los jugadores alrededor de un cambio.

    | | control, DFL | flag, DFL | SkillCorner |
    |---|---|---|---|
    | red frente a `main` | −0,005 a −0,003 | +0,061 a +0,092 | −0,025 a −0,019 |
    | red frente a la lineal con los mismos rasgos | +0,001 a +0,008 (intervalos que cruzan el cero) | +0,022 a +0,033 | −0,023 a −0,010 |

    - Con el control, la red encuentra más posesiones de 2 a 10 s (del 65 al 74–76 %), pero predice tantas
      de más (1.912–2.005 frente a 1.661) que el spellF1 no se mueve.
    - Lo que la red saca de más son cambios del tipo del flag, y solo en la DFL. Es la misma apuesta de
      convención que B9, más grande, y en SkillCorner pierde [inferencia].
    - Detalle: `validation/posesiones_cortas/BITACORA.md` §10.

14. **Fase 4: el déficit del partido no es propio del partido** [medido, regla subida antes en `ba55354`].
    Con nuestro `D`, `main` saca en los datos abiertos el mismo ritmo que en el partido:

    | | posesiones por minuto de juego predicho | por partido | duración media |
    |---|---|---|---|
    | partido (`equipo_v3`) | 3,70 | – | 16,2 s |
    | DFL «como el ATD», balón tapado en los `D` | 4,29 | 3,75–5,76 | 14,0 s |
    | DFL «como el ATD», balón a la vista en los `D` | 4,26 | 3,83–5,50 | 14,1 s |
    | SkillCorner «detectado» | 4,11 | 3,45–4,96 | 14,6 s |

    - Las 3,7 del partido son el 86–90 % de esos ritmos y caen dentro de su rango por partido. Con la regla,
      «cerca»: el déficit del partido es el mismo de siempre (el signo de la evidencia en las posesiones de
      2 a 10 s), y no hace falta un script del partido.
    - El hueco frente a las posesiones reales es el que ya se medía: 4,7 por minuto con el control de la DFL,
      6,05 en SkillCorner y 8,3 con el flag.
15. **Fase 4: una pista de equipo de fuera valdría poco tal como está planteada** [medido con una pista
    sintética, descriptivo, cota superior]. Trozos de 7,5 s de media que dicen un equipo y aciertan o fallan
    enteros, colocados sin mirar los bordes de las posesiones, sumados a `main`:
    - **solo en los frames sin balón (el alcance del plan):** no cambia nada (±0,008), porque en «como el ATD»
      solo el 12,7 % de los frames vivos no tiene balón;
    - **en todos los frames:** con el control ayuda (+0,011 a +0,022) solo si acierta el 90 % o más y pesa 2
      o 4 por frame. Con el flag no ayuda nunca. Con un acierto del 70 % y peso 4, tiende a empeorar el control;
    - **es una cota superior:** los fallos sintéticos son independientes de los de B5, y los de las fases
      reales no lo serán;
    - **lo que no mide:** unas fases que empezaran cerca de los cambios reales, que valdrían más;
    - **no decide nada** hasta que Antonio tenga la cobertura y el acuerdo reales;
    - detalle: `validation/posesiones_cortas/BITACORA.md` §11.
16. **Fase 4: una pista que marque dónde cambia la posesión valdría algo más, pero solo en el mejor caso**
    [medido con una pista sintética de transiciones, descriptivo, cota superior; regla en `92b4771`]. Marcas que
    empiezan en un cambio real y dicen el equipo nuevo durante hasta 5 s:
    - con las 24 transiciones del partido (≈ 16 % de los cambios), perfectas y con peso 8, darían +0,013 a
      +0,016 si caen al azar, y +0,021 a +0,027 si caen todas en cambios que `main` no ve;
    - con 1 s de error y un 90 % de precisión se quedan en +0,009 a +0,019;
    - para llegar a +0,03 hace falta el 30 % de los cambios, todos de los que `main` no ve, a 1 s o menos y con
      peso 8 en todos los frames, que va más allá del alcance del plan;
    - ninguna combinación hace daño;
    - detalle: `validation/posesiones_cortas/BITACORA.md` §13.
17. **H3 y H5 del visionado (¿caen los huecos del balón del ATD en los cambios?): no concluye** [medido en el
    partido por Ismael, con la regla subida antes]. R sale igual que en la DFL (1,19 frente a 1,20) y F por
    debajo, pero solo 6 de nuestros cambios caen junto a un hueco. En pleno juego el ATD casi no pierde el
    balón (37 huecos): la mayor parte va pegada a nuestras paradas. No se abre nada antes de la entrega.
    Detalle: `validation/resultados/2026-11-15_huecos_y_cambios.md`.
18. **¿Cuenta la GT pública los toques sin control? No concluye** [medido, regla subida antes en `89610fd`].
    Hay 2 posesiones de menos de 2 s metidas entre dos del otro equipo (0,50 por minuto de juego). Quedan
    entre el control (p90 0,37) y el flag (p25 0,53), cerca de SkillCorner (mediana 0,57). Con 0 habría sido
    «exige control» y con 3 o más, «cuenta toques». Detalle: `validation/posesiones_cortas/BITACORA.md` §15.
19. **B9, listo para que decida Ismael** [medido; tabla completa en la §16 de la bitácora]:
    - gana con el flag (+0,039 y +0,048) y empata con el control (−0,006 y −0,005);
    - con el balón 4 frames tarde, como midió Antonio en el partido, sale igual: +0,035 y +0,043 con el
      flag, y −0,005 y −0,008 con el control;
    - no gana en SkillCorner (−0,005 y +0,004);
    - no cumple el límite de los duelos sin cambio (−5,7 frente a −5);
    - cumple los criterios del `D` propio;
    - es una apuesta de convención que ni la regla ni la ventana pública eligen.

## Estado de cada idea

| idea | estado |
|---|---|
| bajar o subir el coste de cambio | probado antes (12 y 50): empata |
| un coste de cambio que dependa del contexto | sin medir; en contra, el punto 3 [inferencia] |
| entrenar con más filas o con tracking automático (SkillCorner) | puerta: plano [medido] |
| proponer trozos del rival y clasificarlos | techo bajo, ni con un oráculo llega a +0,03 con el control [medido] |
| la dirección en que se mueve el balón (B9) | medido con regla: empate |
| deshacer el suavizado del balón | no se puede validar en el harness (allí es una media exacta sin ruido) |
| señales de los jugadores alrededor de un cambio (medias hacia delante y hacia atrás) | puerta de la fase 3: no ganan con el control ni en SkillCorner [medido] |
| un modelo no lineal con los mismos rasgos (red de una capa) | puerta de la fase 3: no gana con el control ni en SkillCorner [medido] |
| quitar las posesiones inventadas (fase 2) | ni con un oráculo llega a +0,03 en las que lo son con las dos convenciones [medido] |
| un arreglo del decodificador para las posesiones largas (fase 2) | no hay de dónde: ninguna se pierde por cómo se colocan los cambios [medido] |

## Qué se recomienda

- **No cambiar la entrega por esto** [medido, con la regla]. B9 no pasa, y no mejora en SkillCorner, el
  tracking automático más parecido al partido que hay abierto.
- **El retraso del balón del ATD pesaba más que cualquier candidato, y ya está medido.** Con el balón 12
  frames tarde, `main` caería en la DFL de 0,728 a 0,640 con el control y de 0,498 a 0,472 con el flag
  [medido, descriptivo]. La medida de Antonio (PR 11, `validation/resultados/2026-11-15_retraso_balon.md`)
  dice que el balón del ATD llega unos 4 frames tarde respecto a los jugadores. Con 6 frames, `main` cae
  −0,019 con el control y nada con el flag [medido, punto 12]: el riesgo grande queda descartado
  [inferencia].
- **Para el documento técnico:**
  - con el flag, tres cuartos de lo que no encontramos son toques sin control [medido];
  - con el flag, en las de menos de 2 s, el más cercano no dice nada frame a frame, ni con el balón limpio
    [medido];
  - con el control, el número de posesiones cuadra en la DFL [medido].

## Qué información haría falta

- **El instante de los toques** [inferencia]. Por frame, el más cercano no ayuda en las posesiones cortas del
  flag ni con el balón limpio (punto 6), así que la información tendría que estar en los toques.
  - El anexo A.4 de la revisión externa (una medida de fuera, sin repetir por el equipo) dice que el
    suavizado los borra: con el balón limpio, el equipo nuevo está a 1,5 m del balón en el 94 % de los
    cambios reales; suavizado, en el 56–63 % [sin verificar].
- **Para recuperarlos haría falta un balón sin suavizar** [inferencia]: el del vídeo táctico, o deshacer el
  suavizado del ATD.
  - Deshacerlo no se puede validar en el harness: allí el suavizado es una media centrada exacta y sin ruido,
    y una inversa ganaría por construcción.
  - En el ATD el núcleo no está medido.
- **Por qué la dirección del balón dice menos en SkillCorner que en la DFL** [sin explicar]: el 66 % frente al
  81 % en las de 2 a 5 s. Puede ser la otra liga, la retransmisión, el balón a 10 fps o la convención. Si se
  entendiera, se sabría si al ATD le pasa lo mismo.

## Lo que dice y lo que no

- Todo es de datos abiertos de otros partidos: nada del partido del reto.
- El `D` es el de las etiquetas, salvo en los criterios con el `D` propio.
- El examen de SkillCorner (`lector.EXAMEN`) no se ha tocado: la regla de B9 no dejaba ejecutarlo.
- El diseño de B9 (la señal, el umbral y la ventana) salió de un sondeo y de una puerta en los mismos 7
  partidos de la DFL. Dejar un partido fuera protege sus coeficientes, no su diseño.

## Detalle

- Diagnóstico y sondeos: `validation/posesiones_cortas/BITACORA.md` (§2 a §6), con las salidas tal cual en
  `validation/posesiones_cortas/salidas/`.
- B9, su regla y su resultado: `docs/decisiones.md` (15/11, «posesiones cortas: B9»).
- Comandos (todos con datos abiertos; los puede ejecutar Claude):
  - `python validation/posesiones_cortas/diagnostico.py`
  - `python validation/posesiones_cortas/informacion.py`
  - `python validation/posesiones_cortas/informacion_direccion.py`
  - `python validation/posesiones_cortas/puerta_skillcorner.py`
  - `python validation/posesiones_cortas/techo_propuestas.py`
  - `python validation/posesiones_cortas/puerta_direccion.py`
  - `python validation/posesiones_cortas/entrenar_b9.py`
  - `python validation/harness/puntuar.py --versiones validation/harness/versiones/posesiones_cortas_b9.json --eventos`
  - `python validation/apuesta_b/d_propio.py --versiones validation/harness/versiones/posesiones_cortas_b9.json`
  - `python validation/posesiones_cortas/medir_b9.py entrenamiento` (y `placebo` y `retraso`)
