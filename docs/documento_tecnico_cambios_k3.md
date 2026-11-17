# Documento técnico: qué hay que cambiar para `equipo_v11` (K3)

Nota de relevo (17/11/2026, por la tarde). La escribe Claude en la sesión de Ismael, que tuvo que cerrar el PC antes de
que se editara el documento. **`docs/documento_tecnico.md` no se ha tocado:** sigue escrito para `equipo_v9` (B5). Quien
lo actualice puede borrar este fichero al acabar.

- **Dónde está el documento:** rama `docs/documento-tecnico` (PR 21), en `12b8f9e`. Esta rama
  (`docs/documento-tecnico-k3`) sale de ahí y solo añade esta nota. Ojo: hay otro borrador, `docs/technical_document.md`,
  en la rama `feat/d-golpeo-video` (16/11); no es este.
- **De dónde salen las cifras:** todo está en `main` (`88259ce`): `docs/decisiones.md` (entradas del 17/11 sobre el
  modelo conjunto, K3, los pesos y `equipo_v11`), `validation/resultados/2026-11-17_modelo_conjunto.md`,
  `validation/resultados/2026-11-17_refinamientos_k2.md` y `validation/conjunto/salidas/`. Son agregados de datos
  abiertos o agregados del partido que pegó una persona.

## 1. Lo que ha cambiado

- **La entrega es `equipo_v11`:** sha256 `811658cd52267cbd75607270c2c359e2244b05b8a6d091d6ce8330d2d971c04b`, válida,
  198 posesiones de 17,4 s de media (96 y 102), 116 paradas (54 y 62) y el 45,8 % de `D` en lo evaluado [medido].
  Generada desde `main` en `23dcbc1`, en Windows, con Python 3.13.1 y numpy 2.5.4. Es byte a byte `prueba_k3`, que se
  generó con Python 3.12.10 y numpy 1.26.4.
- **La evidencia de equipo es K3** (`aprendida.evidence_k3`, en `possession/refinamientos.py`): la media a partes
  iguales de dos logits de `H` frente a `A`, el de K2 y el de B5, cada uno con su α (4 los dos en la entrega). Se puntúa
  como B5: −round(|s|, 6) al equipo que la mezcla no da y +1 al equipo del jugador más cercano si se ve el balón. El
  `D`, el decodificador y las capas del partido no cambian. `PESO_K2` = 0,5 se fijó antes de medir.
- **K2** (`possession/conjunto.py`) es una red que mira a cada jugador: 14 números por jugador, una red compartida
  14 → 32 → 32, la suma y el máximo por equipo, y una convolucional temporal de 40 canales (6 bloques, dilaciones 1 a
  32, ±12,6 s a 5 Hz). 36.260 pesos, antisimétrica al cambiar los equipos, solo ReLU. En la entrega corre en numpy, sin
  exponenciales ni BLAS.
- **Los pesos van en el repo:** `possession/conjunto_pesos.npz` (1,2 MB, 8 juegos: 7 pliegues y el de todos), sha256
  `6d16316f85063f13765fe4a8707558d6f26b800b9d43ce877d8dad95ae8c0da2`. Es una excepción escrita a `CONTRIBUTING.md` §7.
- **K2 se entrenó con dos datasets:** los 7 partidos de la DFL (etiquetas de control, en todos los frames vivos) y los 10
  de la mitad de entrenamiento de SkillCorner (sus propias etiquetas). Con torch 2.14.1 en una GPU (RTX 3060): AdamW,
  3.000 pasos, semilla fija. El entrenamiento en GPU no se repite bit a bit; por eso el repo lleva los pesos.
- **Quién decidió:** K2 lo encendió David (pasó su regla entera). K3 lo encendió Ismael, con el equipo, el 17/11.

## 2. Frases del documento que ahora son falsas

Esto es lo primero que hay que arreglar. Por sección:

| dónde | qué dice | qué pasa |
|---|---|---|
| cabecera y §9 | `equipo_v9`, `d9706dfb…be63`, 201 posesiones, 116 paradas, 46,2 % | es `equipo_v11` (punto 1) |
| «Términos» | pliegue = dejar fuera un partido de la DFL | los pliegues de K2 dejan fuera además dos partidos de SkillCorner; faltan K2 y K3 |
| §0, «El método en un párrafo» | la evidencia de equipo es B5 | es K3: la media de K2 y B5 |
| §0, «Solo con numpy» | – | sigue siendo cierto, pero ahora lee además el fichero de pesos |
| §0 y §6.1 | «Cada pieza entró por una regla escrita antes»; «B5 y E2 ganaron en el harness» | K2 pasó su regla entera, examen incluido. **K3 entró por decisión del equipo:** el punto 2 de su propia regla no se pudo leer. Con §5.8, K3 frente a B5 es «empate o no concluye» con el flag |
| §2, fila 1 de la tabla y el párrafo de B5 | B5, `aprendida.evidence_b5`, α = 4, 30 rasgos | K3; B5 pasa a ser una de sus dos mitades. Faltan los párrafos de K2 y de K3 |
| §2, «Tracking que falta» y §4, fila del Smart Tagging | «B5 opina…», «salvo que B5 diga…» | ahora es K3 |
| §3 | «B5 se entrenó solo donde el flag coincide con control» | sigue valiendo para B5; K2 se entrenó con control en todos los frames vivos y con las etiquetas de SkillCorner |
| §4, tabla de abiertos | SkillCorner: «solo validación»; K2 «pasa y está apagado» | 10 partidos son entrenamiento de K2; K2 está en la entrega dentro de K3 |
| §4, valores que salen de agregados del partido | la lista | crece: los aumentos de K2 se calibraron con tres agregados del partido (el balón llega unos 4 frames tarde; un equipo tiene más de 11 slots en el 12,9 % de los frames; el balón se ve en el 68 % de los frames de las ventanas `SET PIECES`) |
| §5 | «Solo dos piezas están entrenadas, y las dos con el mismo dataset» | son tres modelos, y K2 usa también SkillCorner |
| §5 | «SkillCorner y Metrica usan los coeficientes de la entrega, que nunca vieron esos partidos»; «Regenerar la entrega no reentrena nada» | lo primero es falso para 10 de los 20 partidos de SkillCorner. Lo segundo sigue valiendo |
| §5, «Etiquetas usadas solo para validar» | SkillCorner, 20 partidos | las de 10 partidos entrenan K2 |
| §6.5 | `equipo_v9`: 0,680 y 0,874 | `equipo_v11`: 0,693 y 0,876 (`equipo_v10`: 0,680 y 0,873). No elige nada |
| §8 | el bloque «Lo que puede cambiar la entrega antes del cierre: K2» | ya pasó: se reescribe como parte del método y de las limitaciones |
| §8 | «Pasamos de 219 a 201 posesiones, de 3,79 a 3,53 por minuto» | ahora 198, unas 3,45 por minuto de juego vivo (198 entre 57,4 minutos) |
| §9 | lo que lee la entrega; las máquinas | lee además `possession/conjunto_pesos.npz`. La reproducción de `equipo_v11` en una segunda máquina **no está confirmada** y nunca se ha ejecutado en Linux ni en macOS |
| §10 | usos del examen de SkillCorner; declaración del LLM | K2 lo abrió una vez y pasa; **K3 no lo ha abierto.** Claude escribió y ejecutó el entrenamiento de K2 con datos abiertos. Junto a los pesos hay que citar la DFL (CC BY 4.0) y SkillCorner (MIT), porque derivan de ellos |

## 3. Cifras para las tablas [medido, datos abiertos]

Las notas (baseline, B5, K2 y K3) son de una misma ejecución del harness del 17/11 (código `8409165`;
`validation/conjunto/salidas/2026-11-17_refinar_harness_oraculo_eventos.md` y `…_refinar_harness_propio.md`). La columna
«K3 − B5» y su intervalo son de `…_refinar_dfl.md` (código `74f3191`, bootstrap pareado de 1.000), con los mismos
modelos. **No las mezcles con los intervalos de la tabla actual de §6.2, que son de un bootstrap de 200.**

**DFL, 7 partidos, cada uno con los modelos que no lo vieron (spellF1):**

| etiquetas | `D` | balón | baseline | B5 | K2 | K3 | K3 − B5 [5–95 %] | gana en |
|---|---|---|---|---|---|---|---|---|
| flag | oráculo | como el ATD | 0,406 | 0,498 | 0,542 | 0,529 | +0,031 [+0,023 a +0,039] | 7 de 7 |
| flag | oráculo | sin bloques | 0,435 | 0,512 | 0,549 | 0,536 | +0,024 [+0,017 a +0,031] | 7 de 7 |
| control | oráculo | como el ATD | 0,464 | 0,728 | 0,780 | 0,782 | +0,054 [+0,045 a +0,063] | 7 de 7 |
| control | oráculo | sin bloques | 0,494 | 0,748 | 0,794 | 0,794 | +0,047 [+0,038 a +0,054] | 7 de 7 |
| flag | propio | como el ATD | 0,310 | 0,414 | 0,457 | 0,439 | +0,025 [+0,018 a +0,032] | 7 de 7 |
| flag | propio | sin bloques | 0,346 | 0,431 | 0,464 | 0,448 | +0,017 [+0,011 a +0,024] | 7 de 7 |
| control | propio | como el ATD | 0,353 | 0,623 | 0,668 | 0,665 | +0,042 [+0,034 a +0,050] | 7 de 7 |
| control | propio | sin bloques | 0,397 | 0,651 | 0,686 | 0,683 | +0,032 [+0,025 a +0,040] | 7 de 7 |

- En esta tabla cada logit va con la α de su pliegue. Con las α de la entrega (4 y 4) en los siete pliegues, K3 gana a
  B5 de +0,034 a +0,056 con control (7 de 7) y de +0,014 a +0,025 con el flag, y queda hasta 0,008 por debajo de K2 con
  control.
- **SkillCorner: solo la mitad de entrenamiento (10 partidos), con pliegues cruzados.** K3 − B5: +0,021 [+0,016 a
  +0,026] y +0,023 [+0,017 a +0,028] con el `D` de las etiquetas; +0,017 [+0,011 a +0,022] y +0,021 [+0,015 a +0,026]
  con el propio; gana en 9 o 10 de 10. **No hay cifra de K3 con los 20 partidos ni con el examen: no la escribas.**
  El +0,131 sobre el baseline en 20 de 20 es de B5, y hay que decirlo así.
- **Metrica** (3 partidos, un proveedor que ni K2 ni B5 vieron; pesos de la entrega): K3 − B5, +0,023 y +0,029 con el
  `D` de las etiquetas y +0,014 y +0,017 con el propio (3 de 3).
- **Fuera del proveedor** (la limitación principal):
  - K2 entrenada solo con la DFL, en SkillCorner: de +0,003 a −0,015 en tres entrenamientos, sin ganar en ninguno; K3,
    medida con dos de ellos (las réplicas), de +0,005 a +0,011;
  - K2 entrenada solo con SkillCorner, en la DFL: de −0,048 a −0,083 con control; K3 vuelve al nivel de B5 con control
    (de −0,000 a +0,008) y queda de 0,007 a 0,020 por debajo con el flag;
  - cuando K2 se equivoca mucho, la mezcla cae más o menos donde estaba B5, no por encima.
- **Partido a partido:** K3 queda por debajo de B5 en 3 de 136 casos (el peor, −0,007); K2, en 12 (el peor, −0,026).
- **Cambios de posesión** (para §6.4 y §8; `D` propio, `detalle_abiertos.py`): de los cambios directos entre equipos en
  la DFL con control, B5 ve el 35,0 %, K2 el 48,1 % y K3 el 44,4 %. Recuperaciones en los eventos humanos: 70,3 %,
  80,0 % y 74,9 %. K3 predice entre un 2 y un 4 % menos de posesiones que B5. Las de menos de 2 s no las encuentra
  ninguna.
- **En el partido** (agregados): frente a `equipo_v10`, K3 cambia 4.219 de 158.857 frames (2,66 %): 2.719 de un equipo
  al otro y 1.500 entre un equipo y `D`. Pasó sus criterios de daño C0 a C6, escritos antes.

## 4. Cómo contar K3 sin decir de más

- **La regla de K3,** escrita antes de medir, tenía tres puntos. Pasa el 1 (dentro del proveedor) y el 3 (Metrica). El 2
  (¿deja de perder donde K2 pierde?) no se pudo leer, porque las réplicas de K2 no repitieron la pérdida publicada.
  Con esa regla, K3 no quedaba recomendada por encima de K2. Lo que se midió después va a su favor, pero no en la prueba
  que la regla nombraba.
- **Es una apuesta prudente, no una ganadora demostrada.** Nada se ha medido en el ATD con etiquetas, y el partido es
  de un tercer proveedor.
- **Lo que se midió con B5 y no se repitió con K3:** el empate de los costes 12, 25 y 50; las ganancias de «cortas a
  `D`»; los criterios de las capas del partido. Hay que decirlo donde se citen.
- **§6.6, el nivel esperado:** el 0,33–0,51 y el punto central de 0,39 se calcularon con B5. No los mezcles: deja esa
  cuenta y añade aparte lo que K3 suma en un proveedor que no vio (de +0,005 a +0,03), como [inferencia]. Si se cambia
  el número de §0, que lo decida una persona.
- **§7, lo que falta por contar:** K1 (la capa de cambios aprendida; no pasa), K2 sola (`equipo_v10`,
  `784e65e5825a7fe52f7fe5f3a51c9f5e1bccf2c9f89a1372b7b344a3f882acbc`, reproducida en dos máquinas; sustituida por K3),
  K2r, el riesgo mínimo con K2, K4 (el espejo; no pasa) y K5 (no llegó a candidato).
  - B15 a B17 están en `origin/claude/serene-lumiere-16245d`: ganan con §5.8 en la DFL y no cumplen el límite de daño
    en SkillCorner; el examen de B17, pendiente. Ya no vale decir que K2 es «el único» que gana con las dos
    convenciones.
  - K6a (no pasa su filtro), K7 (no pasa) y K8 (**sin medir:** el piloto se cortó) están en `origin/exp/k2-siguiente`,
    `validation/resultados/2026-11-17_siguientes_k2.md`. Lee esas entradas antes de citar una cifra. Si se cuenta K7,
    la fila de Metrica de §4 («solo validación») necesita una nota: se probó como entrenamiento y se descartó.
- **Recuentos pequeños.** El documento dice que los recuentos de 1 a 4 casos del partido van como «< 5». Las entradas
  de K2 y K3 traen alguno (posesiones de menos de 25 frames, entradas fuera de rango, posesiones emparejadas de más en
  la ventana): no los copies.
- **El ruido de la ventana pública** sale con dos cifras: 0,39 (`CLAUDE.md` y el documento) y 0,42 (las entradas de K2
  y K3). Deja una, con su fuente.

## 5. Lo que solo puede rellenar una persona

- el nombre del equipo, el idioma y el resumen en inglés, la URL del repo público y el commit final;
- **reproducir `equipo_v11` en una segunda máquina** (tiene que salir `811658cd…c04b`) y decir cuál;
- cuánto tarda el comando;
- las respuestas de la organización (los «extracts» y las cifras oficiales), o «sin respuesta antes de la entrega»;
- quién hizo el recuento a ojo y cuántos cambios miró; la licencia del código propio; la referencia de ELASTIC.
