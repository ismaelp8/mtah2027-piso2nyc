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
