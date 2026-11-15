# Posesiones cortas: por qué predecimos menos posesiones de las que hay · bitácora

> Sale de la reapertura de la evidencia de equipo (Ismael, 15/11; `docs/decisiones.md`). Solo datos
> abiertos de otros partidos: la DFL (Bassek et al., 2025, CC BY 4.0) y SkillCorner (A-League 2024/25,
> licencia MIT), solo la mitad `lector.ENTRENAMIENTO` hasta que haya un candidato cerrado. Lo puede ejecutar
> Claude. Solo agregados. Rama `claude/posesiones-cortas-5e84f8`.

## 1. Las preguntas, por orden

1. ¿Cuánto de «predecimos de menos» es convención y cuánto es modelo?
2. ¿Qué le falta a la evidencia en un cambio real? Cuánto margen da B5 dentro de las posesiones reales
   cortas frente a lo que cuesta meterlas (dos cambios de 25), y qué distingue a las que se funden con la de
   al lado.
3. ¿Qué información queda sin usar?
4. Dos o tres candidatos, escritos y subidos con su regla antes de medirlos.

## 2. Diagnóstico descriptivo (preguntas 1 y 2)

`python validation/posesiones_cortas/diagnostico.py`. **No decide nada:** no hay regla previa, sirve para
elegir qué candidatos escribir. Usa el pipeline de `main` con el `D` de las etiquetas, como el harness.

Primera salida, tal cual: `salidas/2026-11-15_diagnostico_v1.md` (código `3b227c4` más estos scripts).
**Dos etiquetas de esa salida exageran** (revisión del 15/11) y se corrigen en la siguiente:
- «solo en el flag» no son solo toques del rival: el emparejamiento uno a uno deja sin pareja también los
  trozos del equipo que retiene a cada lado del toque. Hay que partirlas por equipo;
- el grupo «jugadores» mezcla la posición en el campo (sus dos pesos mayores: «balón en la dirección de
  ataque, ventana 51» y «juego en la dirección de ataque, sin balón cerca») con la velocidad y la dispersión.

## 3. Sondeo de información por frame

`python validation/posesiones_cortas/informacion.py`; salida en `salidas/2026-11-15_informacion_v1.md`.
Descriptivo. Lo que dice [medido]: dentro de las posesiones del flag de menos de 2 s, el más cercano es del
equipo bueno en el 49–57 % de los frames con balón, **también con el balón limpio**. Suavizar a los
jugadores igual que el balón no cambia nada (±1 punto). Lo que no dice: nada del instante del cambio, que
es donde el suavizado sí borra la proximidad (anexo A.4 de la revisión externa: del 94 al 56–63 %).

Segunda salida del diagnóstico, con las dos etiquetas corregidas: `salidas/2026-11-15_diagnostico_v2.md`.
- De las 1.492 posesiones del flag que no son del control, 793 son toques del rival sin control (`main`
  encuentra el 5 %) y 699 son trozos del equipo que retiene, partidos por el toque (el 9 %).
- En las posesiones cortas que no encontramos, empujan en contra el balón en 151 frames, la velocidad de los
  equipos y la dispersión. La posición en el campo va casi neutra.
- `main` saca 4,25 posesiones por minuto vivo en SkillCorner (reales: 6,05) y 4,50 en la DFL (control
  4,71, flag 8,30). Si se siguiera el signo de la evidencia frame a frame saldrían 2.531 en la DFL, frente a
  las 1.661 del Viterbi.

## 4. Puerta: entrenar con tracking automático (SkillCorner)

`python validation/posesiones_cortas/puerta_skillcorner.py`; salida en `salidas/2026-11-15_puerta_skillcorner.md`.
Regla de la puerta, fijada antes de ejecutarla (revisión del 15/11): se entrena y se mira en los mismos 10
partidos de `lector.ENTRENAMIENTO`; si ni así se mueven las posesiones de 2 a 5 s, no se gasta un candidato.

Resultado [medido]: no se mueven. Con los rasgos de B5 entrenados con todos los frames vivos de SkillCorner
(solos o junto a las filas de B5), las de 2 a 5 s quedan en el 28–30 % (`main`, 29 %) y el spellF1 pasa de
0,519 a 0,520–0,528 («detectado») y de 0,514 a 0,516–0,521 («detectado, suavizado»). **Descartada como
candidato:** limitan los rasgos, no las filas.

## 5. Techo de «proponer y clasificar» trozos del rival

`python validation/posesiones_cortas/techo_propuestas.py`; salida en `salidas/2026-11-15_techo_propuestas.md`.
Descriptivo. Propuestas sin etiquetas: dentro de cada posesión de `main`, los trozos en que el más cercano es
del rival a 2 o 3 m durante 12 o 25 frames. Un oráculo acepta solo las que coinciden con una posesión real
del rival, y se vuelve a decodificar.

Resultado [medido]: el techo es bajo. Con el clasificador perfecto se gana de +0,008 a +0,013 con el control,
de +0,017 a +0,039 con el flag y de +0,009 a +0,030 en SkillCorner. Además, solo el 2–11 % de las propuestas
son buenas: un clasificador de verdad lo tendría muy difícil. **Descartada:** ni con un oráculo llega al
+0,03 con el control.

## 6. Sondeo: la dirección en que se mueve el balón

`python validation/posesiones_cortas/informacion_direccion.py`; salida en
`salidas/2026-11-15_informacion_direccion.md`. Descriptivo. B5 sabe dónde está el balón en el campo, pero no
hacia dónde se mueve. La señal: la velocidad del balón en la dirección de ataque del local, medida en 13, 25
o 51 frames, da `H` por encima de 2 m/s y `A` por debajo de −2 m/s. Una velocidad medida en 13 frames o más
aguanta un suavizado de 25.

Resultado [medido], en los frames en que la señal opina (la mitad, más o menos), acierto frente al del más
cercano en los mismos tramos de duración:

| | 1–2 s | 2–5 s | 5–10 s | ≥ 10 s |
|---|---|---|---|---|
| DFL flag: dirección en 13 frames / más cercano | 66 / 49 % | 81 / 57 % | 83 / 68 % | 68 / 84 % |
| DFL control: dirección en 13 frames / más cercano | 68 / 58 % | 81 / 60 % | 79 / 65 % | 66 / 81 % |
| SkillCorner: dirección en 13 frames / más cercano | 57 / 52 % | 66 / 58 % | 66 / 66 % | 60 / 79 % |

Es la primera señal que acierta más en las posesiones de 1 a 10 s que en las largas: es justo donde falla
B5. En SkillCorner es más débil [sin explicar].

Puerta antes de escribir un candidato, fijada antes de ejecutarla:
`python validation/posesiones_cortas/puerta_direccion.py`. Se entrena con los 7 partidos de la DFL y se mira
en los mismos 7, frente a B2 reentrenada igual (la referencia justa). Si la dirección no mueve las posesiones
de 2 a 10 s, no se gasta un candidato.

Resultado de la puerta [medido, en los mismos partidos: optimista]; salida en
`salidas/2026-11-15_puerta_direccion.md`. spellF1 con α = 2 / 4 / 8:

| balón | etiquetas | B2 reentrenada | B2 + dirección |
|---|---|---|---|
| como el ATD | flag | 0,498 / 0,499 / 0,499 | 0,537 / 0,547 / 0,550 |
| como el ATD | control | 0,736 / 0,730 / 0,723 | 0,741 / 0,722 / 0,708 |
| sin bloques | flag | 0,512 / 0,513 / 0,513 | 0,558 / 0,572 / 0,575 |
| sin bloques | control | 0,756 / 0,749 / 0,743 | 0,760 / 0,742 / 0,727 |

- **Mueve las posesiones de 2 a 10 s:** con el control, las de 2 a 5 s encontradas pasan del 53–55 % al
  62–63 %; con el flag, del 27–28 % al 34–38 %.
- **Con el control casi no gana:** predice más posesiones (1.609 → 1.749 con α = 2) y la mitad de lo que
  sobra es «más corta que la real»: parte posesiones buenas con trozos falsos del rival [inferencia: pases
  hacia atrás rápidos del equipo que tiene el balón].
- **La puerta se pasa** (mueve las de 2 a 10 s). Es la primera idea que da más de +0,03 con el flag en estas
  condiciones, aunque sea en los mismos partidos.

## 7. B9: candidato, regla y resultado

La regla y el candidato están en `docs/decisiones.md` (15/11, «posesiones cortas: B9»), con commit `cd75d3d`
antes de entrenar. Coeficientes en `4e662ad`. Salidas en `salidas/2026-11-15_{entrenar,harness,dpropio,
sk_entr,placebo,retraso}_b9.md`.

Resultado [medido]: **empate.**
- Gana con el flag: +0,039 y +0,048.
- Empata con el control: −0,006 y −0,005.
- Los duelos sin cambio bajan −5,7 en «sin bloques», y el límite era −5.
- En la mitad de entrenamiento de SkillCorner da −0,005 y +0,004.

El examen no se ejecutó. B5 se queda.

## 8. Fase 2: las posesiones de 2 s o más que no encontramos

Lo pidió Ismael por la sesión principal: mirar también las otras posesiones, no solo las cortas.
`python validation/posesiones_cortas/largas.py`; salida en `salidas/2026-11-15_largas.md`. Descriptivo, sin
regla. Por cada posesión real no encontrada se prueban arreglos locales (las vecinas del otro equipo bien
puestas; el borde con un `D` real; los `D` nuestros dentro) y se apunta el primero que basta para llegar a
IoU ≥ 0,5.

Resultado con el `D` de las etiquetas [medido], en las posesiones que existen con las dos convenciones:

| | no encontradas | por una vecina del otro equipo | decimos el otro equipo | otra cosa |
|---|---|---|---|---|
| control, 2–5 s | 183 de 384 | 40 % | 60 % | 0 % |
| control, 5–10 s | 79 de 382 | 46 % | 54 % | 0 % |
| control, ≥ 10 s | 41 de 646 | 73 % | 15 % | 12 % |
| flag, 2–5 s | 203 de 410 | 45 % | 55 % | 0 % |
| flag, 5–10 s | 100 de 409 | 60 % | 40 % | 0 % |
| flag, ≥ 10 s | 42 de 578 | 81 % | 7 % | 12 % |

- **Ninguna se pierde por el emparejamiento** (0 %): ninguna llega a IoU ≥ 0,5 sin arreglar nada.
- **La vecina que falta no siempre es corta:** dura menos de 2 s en el 24–50 % de los casos.
- **En SkillCorner sale lo mismo:** la vecina explica el 45 %, el 55 % y el 67 % en las de 2 a 5, de 5 a 10 y
  de 10 s o más.
- **Con el `D` propio** (descriptivo: el balón tapado en los `D` de la DFL delata la etiqueta) salen dos
  causas más:
  - el borde con un `D`: el 23–37 % de las no encontradas de 2 a 10 s que existen con las dos convenciones;
  - un `D` nuestro dentro, una parada falsa que parte una posesión larga: el 21–22 % de las de 10 s o más.

Lectura [inferencia]:
- **Las largas no son un problema aparte.** Con el `D` de las etiquetas, o se pierden por una posesión del
  rival que no vemos a su lado, o porque decimos el otro equipo. Las dos cosas son lo de la fase 1: el
  signo de la evidencia.
- **No hay un arreglo del decodificador:** con el emparejamiento a 0 %, nada se pierde por cómo se colocan
  los cambios una vez que la evidencia es la que es.
- **Lo que añade nuestro `D`** (bordes y paradas falsas) es de las piezas de `D` (Manuel y Ana), y el harness
  no puede medirlo bien.
- **No sale ningún candidato de esta fase.**

## 9. Fase 2: las que sobran, cuánto vale cada fallo y el balón con retraso

Lo pidió la sesión principal (orquestadora, por encargo de Ismael). `python validation/posesiones_cortas/fase2.py`
y `python validation/posesiones_cortas/inventadas.py`; salidas en `salidas/2026-11-15_fase2.md` y
`salidas/2026-11-15_inventadas.md`. Descriptivo, sin regla. DFL «como el ATD» y SkillCorner (mitad de
entrenamiento).

**Las que sobran** (con el `D` de las etiquetas) [medido]:

| clase | flag | control | SkillCorner |
|---|---|---|---|
| inventada (otro equipo, sin ninguna real de su equipo a ≤ 2 s) | 63 | 143 | 251 |
| cambio real desplazado | 140 | 76 | 188 |
| trozo de una real partida | 86 | 150 | 246 |
| fundida | 174 | 33 | 135 |
| **total** | 463 | 402 | 820 |

- Las inventadas son cortas (el 82 % de las del control dura menos de 5 s). El 60 % está pegada a un `D`
  real. Lo que más empuja a su favor es la posición en el campo: +3,3 por frame con el control y +4,5 con
  el flag.
- **De las inventadas con el control, solo 60 lo son también con el flag.** 38 de esas 60 acaban justo antes
  de una parada; tras un reinicio solo hay 6. Las demás inventadas del control son, con el flag, posesiones
  reales (40) o cambios desplazados (32). Quitarlas sería una apuesta de convención.

**Cuánto vale cada tipo de fallo:** sus frames como en las etiquetas, uno cada vez; «como el ATD» y «sin
bloques» [medido]:

| arreglo, `D` oráculo | flag | control | SkillCorner |
|---|---|---|---|
| faltan, decimos el otro equipo, < 2 s | +0,254 / +0,252 | +0,045 / +0,041 | +0,200 |
| faltan, decimos el otro equipo, 2–10 s | +0,240 / +0,230 | +0,123 / +0,114 | +0,191 |
| faltan, decimos el otro equipo, ≥ 10 s | +0,011 / +0,019 | +0,007 / +0,007 | +0,035 |
| sobran, inventadas | +0,016 / +0,014 | +0,074 / +0,070 | +0,065 |
| sobran, cambio real desplazado | +0,088 / +0,082 | +0,051 / +0,046 | +0,084 |
| sobran, solo las inventadas con las dos convenciones | +0,015 | +0,027 | – |

Con el `D` propio, además: los bordes de las paradas que vemos valen +0,048 / +0,073 (flag / control,
«como el ATD»); las paradas falsas, +0,012 / +0,016; y las que no vemos, +0,014 / +0,019.

**`main` con el balón tarde** (`D` oráculo; descriptivo; no es la medida de Antonio):

| balón | etiquetas | 0 frames | 6 | 12 | 25 |
|---|---|---|---|---|---|
| como el ATD | flag | 0,498 | −0,001 | −0,027 | −0,057 |
| como el ATD | control | 0,728 | −0,019 | −0,088 | −0,184 |
| sin bloques | flag | 0,512 | −0,000 | −0,030 | −0,067 |
| sin bloques | control | 0,748 | −0,017 | −0,097 | −0,207 |

Lectura [inferencia]:
- **Lo que más vale, con cualquier convención, son las posesiones de 2 a 10 s que no encontramos porque
  decimos el otro equipo** (+0,12 con el control). Es el signo de la evidencia, lo de la fase 1, y B9 ya lo
  intentó.
- **Las inventadas son lo segundo con el control** (+0,07), pero:
  - solo 60 lo son con las dos convenciones;
  - quitar esas 60 con un oráculo perfecto da +0,015 y +0,027. No llega a +0,03 con ninguna convención.

  No hay una palanca clara que pase §5.8. Su patrón (antes de una parada, empujadas por la posición en el
  campo) queda apuntado. El harness tapa el balón 5 frames alrededor de cada `D`, así que puede ser en parte
  cosa del harness.
- **Los bordes de las paradas valen tanto como las inventadas** (+0,05 a +0,07 con el `D` propio). Son de
  las piezas de `D`.
- **El retraso del balón:** con 6 frames casi no cuesta; con 12 cuesta más que cualquier mejora medida; con 25
  se hunde el control.
- **No se escribe ningún candidato en la fase 2.**

## 10. Fase 3: ¿limitan los rasgos o limita la forma lineal? (puerta, regla fijada antes de ejecutar)

Lo pide la sesión principal (orquestadora, por encargo de Ismael). Las puertas de §4 y §6 usaron una regresión
lineal. Con ella no se separa «los rasgos no dan más» de «una regresión lineal no sabe usarlos». En las
posesiones de 2 a 10 s las señales rápidas van a favor y las lentas en contra; decir «si las rápidas coinciden
un rato, ignora las lentas» no es lineal. Script: `python validation/posesiones_cortas/puerta_no_lineal.py`.

**Modelo no lineal** (todo fijado aquí, sin ajustar después): una red de una capa oculta, en numpy.
- 32 unidades `tanh`, **sin sesgos en ninguna capa:** cambiar los equipos de lado cambia el signo de la
  salida, como en B5. La salida es el logit `z`.
- Entradas divididas por su raíz cuadrática media, como `entrenar.ajustar`.
- Pérdida logística media más una L2 de 1e-4 sobre los pesos.
- Adam con paso 0,01, 1.500 iteraciones con todas las filas a la vez, y pesos iniciales normales con la
  semilla 20261115.

**Dos brazos:**
1. **la red con los 33 rasgos de B9:** los de B5 más los tres de la dirección del balón;
2. **la red con esos 33 más 6 de los jugadores alrededor de un cambio.** Se calculan sobre las dos series
   de B2: la velocidad del juego en la dirección de ataque del local y la diferencia de dispersión (local
   menos visitante). De cada una salen su media **hacia delante** (de t a t+w−1) y **hacia atrás** (de t−w+1
   a t), con w = 25 y 75 frames para la velocidad y w = 50 para la dispersión. Una media hacia delante
   distinta de la de hacia atrás es un cambio de comportamiento de los equipos: lo que hace un equipo al
   ganar o perder el balón.

**Referencias:**
- `main` (B5);
- la misma forma lineal con los mismos rasgos: B9, ya entrenada, para el brazo 1, y la regresión de
  `entrenar.ajustar` con los 39 rasgos para el brazo 2.

**Lo demás, como B9:**
- las mismas filas (flag = control, uno de cada 5, «como el ATD»);
- los mismos pliegues;
- la misma puntuación que B5;
- α elegida igual, con la rejilla de B5 y la pieza de `D` de `main` dentro, en los partidos de entrenamiento
  de cada pliegue.

**Medida, solo fuera de muestra y con el `D` de las etiquetas:**
- **DFL:** cada partido con el modelo que no lo vio, en las dos condiciones que votan.
- **SkillCorner, `lector.ENTRENAMIENTO`:** con el modelo de los 7 partidos de la DFL, que nunca ha visto
  SkillCorner, en «detectado» y «detectado, suavizado». El examen no se abre.
- **Qué se mide:** el spellF1 frente a `main` (diferencia, intervalo del 5 al 95 % por bootstrap pareado y en
  cuántos partidos gana) y el % de posesiones reales de 2 a 10 s encontradas (IoU ≥ 0,5).

**Regla de lectura:**
- **Abre un candidato** un brazo de la red que cumpla las tres cosas:
  - a) DFL con las etiquetas de control, en las dos condiciones que votan: +0,010 o más frente a `main`, con
    el intervalo por encima de cero;
  - b) DFL con las etiquetas de control, en las dos condiciones: las posesiones de 2 a 10 s encontradas suben
    3 puntos o más frente a `main`;
  - c) SkillCorner, en las dos condiciones que votan: diferencia frente a `main` mayor que cero, con el
    intervalo por encima de cero.

  Si cumplen los dos brazos, el más simple (el 1). Antes de entrenar el candidato se le dice a la sesión
  principal cuánto cuesta congelarlo.
- **Cierra la pregunta** si ningún brazo cumple a), b) y c). La respuesta final a «qué información falta»
  queda así: «con estos rasgos no hay más, ni con un modelo flexible (una red de una capa de 32)».
- **Descriptivo, no cambia lo anterior:**
  - «la forma lineal limita» si la red gana a su referencia lineal con los mismos rasgos por +0,010 o más,
    con el intervalo por encima de cero, en la DFL con el control y en las dos condiciones;
  - las etiquetas del flag se enseñan, pero no deciden en esta puerta.
- **Comprobaciones del instrumento, antes de leer nada:**
  - `main` repite 0,498 / 0,512 / 0,728 / 0,748 por este camino, y B9, 0,537 / 0,560 / 0,722 / 0,743;
  - la red es impar: con los rasgos cambiados de signo da el logit cambiado de signo.
- **Nada de lo medido cambia la red,** ni los rasgos de los jugadores, ni los umbrales.

**Resultado** [medido; salida en `salidas/2026-11-15_puerta_no_lineal.md`; regla en `3193b43`]:
- **Instrumento:** `main` y B9 repiten 0,728 / 0,748 / 0,498 / 0,512 y 0,722 / 0,743 / 0,537 / 0,560 por este
  camino. La red es impar. Su α sale 2 en los 8 pliegues.
- **a) DFL con el control, frente a `main`: no.** La red 33 da −0,005 y −0,004, y la red 39, −0,003 y −0,003.
  Todos los intervalos cruzan el cero.
- **b) Posesiones de 2 a 10 s con el control: sí.** Pasan del 65 y el 68 % al 74–79 %. Pero se predicen
  1.912–2.005 posesiones frente a 1.661, y lo que se gana se pierde en las que sobran.
- **c) SkillCorner: no.** Las dos redes pierden frente a `main`: de −0,019 a −0,025, ganando en 0 a 2 de 10.
- **Descriptivo:**
  - frente a su lineal, con el control, +0,001 y +0,001 (red 33) y +0,005 y +0,008 (red 39), con intervalos
    que cruzan el cero;
  - con el flag, la red 39 gana a `main` por +0,087 y +0,092 y a su lineal por +0,031 y +0,033;
  - en SkillCorner, la red pierde también frente a su lineal.

**Se cierra la pregunta:** con estos rasgos no hay más, ni con un modelo flexible (una red de una capa de 32).
- La forma lineal no limita con el control [medido].
- Con el flag, la red saca más cambios de toque en la DFL, pero eso no se traslada a SkillCorner. Es una
  apuesta de convención, más grande que la de B9 [inferencia].
- Las señales de los jugadores alrededor de un cambio ayudan solo con el flag.

## 11. Fase 4: ¿es real el déficit del partido? y ¿cuánto valdría una pista de equipo de fuera? (reglas fijadas antes de ejecutar)

Lo pide Ismael por la sesión principal: «haga una investigacion tambien para ver como arreglar lo demas». Las
fases 2 y 3 no se repiten. Rama `claude/posesiones-fase4`, cortada de `main` en `4305576`.

### 11.1 ¿Es real el déficit del partido? Igual con igual

`python validation/posesiones_cortas/ritmo_d_propio.py`. Las 3,7 posesiones por minuto vivo del partido
(`equipo_v3`: 215 posesiones, de 16,2 s de media) van con nuestro `D`. Las 4,50 de la DFL y las 4,25 de
SkillCorner, con el `D` de las etiquetas. Aquí todo va con nuestro `D`: `main` sin oráculo.

- **Qué se mide:** posesiones predichas por minuto de juego predicho, en los tramos evaluados, y su reparto
  por duración (< 2 s, 2–5 s, 5–10 s, 10–20 s, ≥ 20 s) y su duración media. Con todos los partidos juntos y
  por partido.
- **Referencias que deciden:**
  - R1: la DFL «como el ATD», con el balón tapado en los `D`;
  - R2: la DFL «como el ATD», con el balón a la vista en los `D` (`d_propio.con_balon_en_d`);
  - R3: SkillCorner, `lector.ENTRENAMIENTO`, «detectado».

  «Como el ATD, sin bloques» y «detectado, suavizado» se enseñan sin voto.
- **Regla:**
  - **«El partido va más corto»** si, en al menos dos de las tres referencias, 3,7 queda por debajo de 0,85
    veces su ritmo con todos los partidos juntos **y** por debajo de su mínimo por partido. Entonces se
    escribe el script de `validation/partido/` que pide la sesión principal, con su lectura escrita antes.
  - **Si no, «cerca»:** no hay un déficit propio del partido, la respuesta sigue siendo el signo de la
    evidencia y se cierra.
  - La duración media (16,2 s) se compara igual, pero solo como descripción.

### 11.2 ¿Cuánto valdría una pista de equipo de fuera? Una pista sintética en la DFL

`python validation/posesiones_cortas/pista_sintetica.py`. Antonio tiene el sí de Ismael para usar las fases del
Smart Tagging como pista de equipo (`docs/decisiones.md`, 15/11), y la DFL no tiene Smart Tagging. Aquí se acota
cuánto podría valer una pista así con una inventada. **No decide nada.**

- **La pista:**
  - en cada tramo evaluado se alternan trozos con pista y huecos sin ella. Los trozos duran, de media, 188
    frames (7,5 s: las 575 fases del partido cubren el 68,1 % de 158.857 frames); los huecos tienen la media
    que da la cobertura c. Las dos longitudes son geométricas, con semilla fija;
  - cada trozo dice el equipo que tiene la mayor parte de sus frames vivos según el control, con
    probabilidad p, y el otro si no. Acierta o falla entero;
  - se colocan al azar, sin mirar dónde empiezan las posesiones: no da información sobre los bordes;
  - suma w por frame a la columna de su equipo. Con dos alcances: solo en los frames sin balón (el del plan)
    y en todos;
  - para cada c, la colocación y el sorteo de aciertos son los mismos en toda la rejilla (números aleatorios
    comunes): al subir p solo cambian trozos de fallo a acierto.
- **Rejilla fija:** p en 0,7, 0,8, 0,9 y 0,95; c en 0,3, 0,5 y 0,68; w en 0,25, 0,5, 1, 2 y 4.
- **Medida:** `main` con la pista sumada a su evidencia, el `D` de las etiquetas, las dos condiciones que votan
  y las dos convenciones. spellF1 frente a `main` sin pista, con el intervalo del 5 al 95 % por bootstrap
  pareado.
- **Lectura** (descriptiva):
  - **ayuda:** +0,01 o más con el intervalo por encima de cero, con las dos convenciones y en las dos
    condiciones;
  - **hace daño:** −0,01 o menos con el intervalo por debajo de cero, con alguna convención, en las dos
    condiciones;
  - se dice, por alcance y cobertura, el menor acierto con el que algún peso ayuda, y con p = 0,7, desde qué
    peso hace daño.
- **Es una cota superior:** los fallos sintéticos son independientes de los de B5, y los de las fases reales
  no lo serán. Además, colocar los trozos al azar no dice nada de los bordes, y las fases reales pueden
  empezar cerca de un cambio (eso valdría más). Nada de esto decide hasta que Antonio tenga la cobertura y el
  acuerdo reales.

### 11.3 Resultados

**11.1, el ritmo** [medido; `salidas/2026-11-15_ritmo_d_propio.md`]. Con nuestro `D`, posesiones por minuto de
juego predicho:
- R1 (DFL «como el ATD», balón tapado): 4,29, con partidos entre 3,75 y 5,76;
- R2 (balón a la vista en los `D`): 4,26, entre 3,83 y 5,50;
- R3 (SkillCorner «detectado»): 4,11, entre 3,45 y 4,96.

El reparto por duración es parecido en las tres: 5–6 % de menos de 2 s, unos 20 % de 2 a 5 s y el resto de 5 s
o más. La duración media va de 14,0 a 14,6 s; la del partido, 16,2 s.
- **Regla: «cerca».** En ninguna referencia 3,7 queda por debajo de las dos cotas. Lo más cerca, R1:
  3,70 frente a 3,65 y 3,75.
- **No hay un déficit propio del partido.** No se escribe el script de `validation/partido/`.
- El partido predice algo menos y algo más largo que la media de los datos abiertos, dentro del rango por
  partido [medido]. Puede ser el partido o nuestro `D`; con esto no se separa [sin verificar].

**11.2, la pista sintética** [medido; `salidas/2026-11-15_pista_sintetica.md`].
- **Instrumento:** `main` sin pista repite 0,498 / 0,728 / 0,512 / 0,748.
- **Cobertura conseguida** sobre los frames evaluados: 23, 38 y 50 % para c = 0,3, 0,5 y 0,68. Queda por debajo
  de lo nominal porque se descartan los trozos sin ningún frame vivo, que caen enteros en una parada. Sobre los
  frames vivos debería quedar cerca de c [inferencia, sin medir].
- **Solo en los frames sin balón:** ninguna celda ayuda ni hace daño (±0,008). En «como el ATD» solo el 12,7 %
  de los frames vivos no tiene balón, y en «sin bloques», el 1,3 %.
- **En todos los frames:**
  - **con el control** ayuda (▲) con p ≥ 0,9 y w ≥ 2. Con c = 0,68 son +0,014 a +0,022; con c = 0,3, p ≥ 0,9 y
    w = 4, +0,011;
  - **con el flag** no ayuda nunca (de −0,008 a +0,002);
  - con p = 0,7 y w = 4 tiende a empeorar: −0,011 / −0,007 con el control y −0,006 / −0,003 con el flag. No
    llega al ▼ de la regla.
- **Lectura con la regla:**
  - ningún peso ayuda con las dos convenciones a la vez, con ningún acierto ni ninguna cobertura;
  - con p = 0,7, ningún peso llega a «hace daño» en las dos condiciones;
  - una pista de equipo colocada sin mirar los bordes solo refuerza el equipo de las posesiones largas, que
    B5 ya acierta: no crea cambios donde faltan [inferencia].
- **Para Antonio** [inferencia]: con el alcance del plan (sin balón), su pista casi no tiene dónde actuar.
  Pesaría algo solo si acierta el 90 % o más y se usa en todos los frames, y eso exige otra decisión de
  Ismael. Valdría más si las fases marcan dónde cambia la posesión (las transiciones), y eso no se ha medido.

## 12. Hipótesis del visionado de la ventana pública, contrastadas con lo medido

La sesión «ventana-video» pasó cuatro hipótesis generales del visionado de Ismael (nota compartida
`2026-11-15_ventana-video_hipotesis.md`; sin momentos ni frames). Nada se mide en la ventana.

- **H1 y H4 (la GT fecha el cambio en el primer toque de la secuencia que gana; un toque libre vale ya):**
  - las etiquetas de control del harness ya lo hacen así [comprobado en el código]. `correccion.corregir`
    (`validation/experimento1/correccion.py`) solo sobrescribe las rachas del flag sin control; las que acepta
    conservan su inicio, que es el primer toque de la racha del equipo nuevo;
  - el pase de primeras a un compañero entra por «dos toques» (dos toques seguidos del mismo equipo a 50 frames
    o menos), y el despeje que cae a un compañero, por el control de ese compañero;
  - el harness no premia ir tarde.
- **«Llegamos unos 2 s tarde»:** en los datos abiertos, no [medido, descriptivo;
  `python validation/posesiones_cortas/retraso_cambios.py`, salida en `salidas/2026-11-15_retraso_cambios.md`].
  De los cambios reales con un cambio nuestro al mismo equipo a ±4 s:
  - con el control de la DFL llegamos tarde de 1 a 4 s en el 14–17 % y pronto en el 15–16 %, con mediana de +0
    a +3 frames;
  - con el flag, tarde en el 10–12 % y pronto en el 6–7 %, con mediana de +6 a +9 frames;
  - en SkillCorner, tarde en el 6–7 % y pronto en el 13 %, con mediana de −12 frames;
  - lo que domina es que no hay ningún cambio nuestro a ±4 s: el 28–32 % con el control, el 63–64 % con el
    flag y el 64 % en SkillCorner.

  Si en el partido llegamos 2 s tarde, los datos abiertos no lo reproducen [inferencia]. Puede ser cosa del
  partido o de un puñado de casos en 5 minutos.
- **H2 (llevar cada cambio al primer acercamiento del equipo nuevo):**
  - su techo es el de los «cambios reales desplazados» de la fase 2: +0,051 con el control, +0,088 con el flag
    y +0,084 en SkillCorner, con un oráculo [medido];
  - un desplazamiento fijo no ayuda, porque no hay un sesgo de retraso;
  - haría falta mover cada cambio por su cuenta, con la proximidad en el instante del cambio. Con el balón
    suavizado, esa proximidad acierta en el 56–63 % (anexo A.4 de la revisión externa, sin repetir por el
    equipo).
- **H3 (el portero coge el balón y deja de verse):** el harness no lo puede medir tal cual. En la DFL el balón
  se ve mientras el portero lo tiene, y los huecos «como el ATD» caen al azar. Haría falta otra degradación,
  que tape el balón tras cada parada del portero en los eventos de la DFL [sin medir].

## 13. Fase 4: una pista que marque dónde cambia la posesión (regla fijada antes de ejecutar)

Lo pide la sesión principal, a raíz de §11. Las fases del Smart Tagging que más prometen marcan un cambio: una
«Attacking Transition» empieza justo después de recuperar el balón (`OVERVIEW.md`). En el partido hay 24, con
sus 24 «Defensive Transition» espejo. La DFL tiene unos 147 cambios directos por partido con el control: 24 son
en torno al 16 %. Script: `python validation/posesiones_cortas/pista_transiciones.py`. **No decide nada:** es
una cota superior que le dice a Antonio qué tiene que cumplir su recuento de transiciones, y a Ismael si
compensa darle a esa pista un alcance mayor que el del plan.

**La pista** (DFL «como el ATD» y «sin bloques», `D` de las etiquetas, `main` con el pliegue que no vio cada
partido):
- **una marca buena** empieza en un cambio directo real de equipo según el control, desplazado al azar un
  número entero de frames entre −j y +j, y dice el equipo nuevo. Dura lo que la posesión real que empieza en
  ese cambio, con un tope de 125 frames (5 s), y sin salir del tramo;
- **una marca falsa** empieza en un frame de juego al azar, sin ningún cambio directo real a 125 frames o
  menos, y dice el equipo que no tiene el balón según el control (es la falsa que hace daño: pide un cambio).
  Dura 125 frames;
- **cada marca** suma w por frame a la columna de su equipo, en todos los frames que cubre.

**Rejilla fija:**
- r, la fracción de cambios directos reales que se marcan: 0,10, 0,16 y 0,30;
- j, el error en el instante: 0, 12, 25 y 50 frames;
- q, la precisión: 0,7, 0,9 y 1. Con n marcas buenas hay n·(1 − q)/q falsas, redondeado;
- w: 1, 2, 4 y 8;
- **dos formas de elegir qué cambios se marcan:**
  - **al azar** entre todos los cambios directos;
  - **solo entre los que `main` no encuentra:** sin un cambio de `main` al mismo equipo a 25 frames o menos.
    Es la cota optimista: las transiciones son recuperaciones, justo lo que B5 pierde;
- **números aleatorios comunes,** semilla fija por partido y condición. El orden de los cambios, el
  desplazamiento de cada uno (u·j, con u fijo) y las posiciones falsas son los mismos en toda la rejilla. Al
  subir r se añaden marcas, y al subir j el mismo cambio se desplaza más.

**Qué se mide:**
- el spellF1 frente a `main` sin pista, con las dos convenciones y en las dos condiciones, con el intervalo del 5
  al 95 % por bootstrap pareado;
- la fracción de cambios directos reales con un cambio nuestro al mismo equipo a 25 frames o menos.

**Lectura** (descriptiva):
- **«llega»:** +0,03 o más con el intervalo por encima de cero en las dos condiciones. Se dice por separado con
  cada convención;
- **«hace daño»:** −0,01 o menos con el intervalo por debajo de cero en las dos condiciones, con alguna
  convención;
- se dice, por forma de elegir y por convención, la menor r que llega con algún j, q y w, y qué combinaciones
  hacen daño.

**Es una cota superior:**
- las marcas buenas salen de los cambios reales y las falsas, del azar, no de los fallos de un detector real;
- no se sabe si las transiciones del Smart Tagging corresponden a cambios del control, ni con qué retraso.

### 13.1 Resultado

[medido, descriptivo, cota superior; `salidas/2026-11-15_pista_transiciones.md`; regla en `92b4771`]
- **Instrumento:** `main` sin pista repite 0,498 / 0,728 / 0,512 / 0,748.
- **Contexto:** hay 2.052 cambios directos reales con el control, con las dos condiciones juntas. El 61 % no
  tiene un cambio de `main` al mismo equipo a 1 s o menos.
- **Lectura con la regla:**
  - **eligiendo los cambios al azar, ninguna combinación llega a +0,03,** con ninguna convención;
  - **eligiendo solo los que `main` no encuentra,** llega con r = 0,30 y w = 8: con el control, si j ≤ 25 y
    q ≥ 0,7–0,9 (de +0,031 a +0,049); con el flag, solo con j = 0 y q = 1 (+0,038 / +0,031);
  - **ninguna combinación hace daño.**
- **Con r = 0,16** (las 24 transiciones del partido son en torno al 16 % de los cambios), «como el ATD» /
  «sin bloques»:

  | cómo se eligen | marcas | w = 4, control | w = 8, control | w = 8, flag |
  |---|---|---|---|---|
  | al azar | perfectas (j = 0, q = 1) | +0,010 / +0,009 | +0,016 / +0,013 | +0,013 / +0,010 |
  | al azar | j = 25, q = 0,9 | +0,007 / +0,006 | +0,009 / +0,008 | +0,009 / +0,006 |
  | solo las que `main` no encuentra | perfectas | +0,016 / +0,012 | +0,027 / +0,021 | +0,021 / +0,015 |
  | solo las que `main` no encuentra | j = 25, q = 0,9 | +0,012 / +0,009 | +0,019 / +0,015 | +0,016 / +0,012 |

  Los cambios reales con uno nuestro a 1 s o menos pasan del 37 al 42–46 % con el control.
- **Para Antonio y para Ismael** [inferencia]:
  - con unas 24 transiciones, la pista daría como mucho de +0,01 a +0,03, y solo si cumple tres cosas:
    - marca recuperaciones que `main` no ve;
    - las fecha a 1 s o menos;
    - se usa en todos los frames con un peso fuerte (w = 8 por frame, hasta 5 s). Eso va más allá del alcance
      del plan (solo sin balón) y lo decide Ismael;
  - para el recuento de Antonio, eso son tres preguntas: cuántas transiciones caen a 1 s o menos de un cambio
    de nuestras etiquetas de control, cuántas de esas `main` no encuentra y con qué retraso;
  - es una cota superior: las marcas buenas salen de los cambios reales.

## 14. H3 y H5: ¿caen los huecos del balón del ATD en los cambios más que al azar? (regla fijada antes de ejecutar)

Lo decide la sesión principal: H2 no se abre (con el control llegamos pronto tan a menudo como tarde, y en
SkillCorner, pronto). H3 se mira con una sola medida del partido, sin candidato. La H5 de la sesión del vídeo
(el balón se pierde en el vuelo de un despeje y cambiamos al recibir) entra en la misma medida. **Nada más hasta
que Ismael pegue los números:** ni una degradación nueva ni un candidato.

**Por qué:** en el harness, los huecos del balón caen al azar. En el partido pueden caer justo en los cambios:
el portero lo coge y deja de verse, o un balón por el aire.

**Qué se mide, sin etiquetas** (definiciones en `validation/posesiones_cortas/huecos.py`):
- **script del partido:** `validation/partido/huecos_y_cambios.py <entrega>`, que lee el ATD y una entrega
  nuestra y lo ejecuta Ismael;
- **referencia:** `validation/posesiones_cortas/huecos_dfl.py`, con `main` y nuestro `D` en la DFL «como el
  ATD», donde los huecos caen al azar. El script del partido la calcula también y la pone al lado;
- **por duración del hueco en juego:** cuántos hay, en cuántos decimos otro equipo después, y si nuestro
  cambio cae dentro o al reaparecer (≤ 0,5 s);
- **R:** el % de nuestros cambios que caen dentro de un hueco en juego de 0,5 s o más, o en los 0,5 s tras
  reaparecer, dividido por el % de frames de juego que caen ahí. R > 1 es que nuestros cambios se juntan con
  los huecos más que unos cambios al azar. En la DFL, R > 1 solo puede venir del decodificador, que cambia
  cuando la evidencia vuelve;
- **F:** el % de los huecos en juego de 0,5 a 15 s tras los que decimos otro equipo. Ve lo que R no ve: si el
  balón desaparece justo en los cambios reales y nosotros no cambiamos durante el hueco, sino al volver el
  balón.

**Regla de lectura,** con los cocientes partido / DFL de R y de F:
- **se cierra** («en el partido los huecos no caen en los cambios más que al azar») si los dos cocientes son
  de 1,25 o menos;
- **queda abierta** si alguno es de 1,5 o más, con al menos 20 cambios junto a un hueco y 20 huecos de 0,5 a
  15 s en el partido. Entonces habría que pensar una degradación, calibrada con este agregado del partido
  entero y nunca para reproducir el retraso visto en la ventana;
- **no concluye** en los demás casos, o con menos casos: no se abre nada antes de la entrega;
- **descriptivo:** la tabla por duración. La franja de 0,5 a 5 s es la de la H5.

**Límites:**
- son nuestros cambios, no los reales, porque en el partido no hay etiquetas;
- la DFL tapa además el balón en sus `D` y bordes. Los huecos pegados a un `D` nuestro no cuentan, ni en el
  partido ni en la DFL;
- un R o una F más altos en el partido pueden venir también de que su balón sea distinto, no solo de que los
  huecos caigan en los cambios [inferencia].

`python validation/scripts/prueba_huecos.py` prueba la medida y la regla con datos inventados.

**Referencia de la DFL** [medido; `salidas/2026-11-15_huecos_dfl.md`, código `41c3c23`; solo se cambió después el
formato de dos frases]: R = 1,20 y F = 28,1 % de 167 huecos en juego de 0,5 a 15 s. En la DFL «como el ATD» no
hay huecos de 0,5 a 2 s, igual que en el ATD, que casi no los tiene: la franja de la H5 se apoya en los de 2 a
15 s. Falta el partido: lo ejecuta Ismael.

**Resultado del partido** (Ismael lo ejecutó en local el 15/11 con `equipo_v3`; salida en
`validation/resultados/2026-11-15_huecos_y_cambios.md`) [medido]:
- R: 1,19 en el partido frente a 1,20 en la DFL (cociente 0,99). F: en el partido, por debajo de la DFL; el
  cociente no pasa de 1,25.
- **Con la regla, no concluye:** los dos cocientes apuntan a «se cierra», pero solo 6 de nuestros cambios caen
  junto a un hueco, y se pedían 20. No se abre nada antes de la entrega.
- En pleno juego, el ATD casi no pierde el balón: 37 huecos. La mayor parte (113) va pegada a nuestras paradas.
- **Un fallo del script, corregido:** la frase de F dejaba deducir una celda de 1 a 4 casos que la tabla
  ocultaba. Ahora F no se imprime en ese caso, y la prueba lo cubre.
