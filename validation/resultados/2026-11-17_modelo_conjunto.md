# Modelo conjunto: una evidencia de equipo que mira a cada jugador (K2)

- **Quién y cuándo:** Claude, en la sesión de Ismael, el 17/11/2026. Rama `exp/modelo-conjunto`.
- **Encargo:** un análisis de fuera decía que cojeamos en la evidencia de equipo, que no ve los cambios de posesión.
  Ismael pidió un plan para resolverlo y ejecutarlo.
- **Regla nº 1 respetada.** No se ha abierto nada del partido. Todo se midió en datos abiertos de otros partidos: los 7
  de la Bundesliga (Bassek et al., 2025, CC BY 4.0) y los 20 de SkillCorner (A-League 2024/25, MIT).
- **Reglas escritas antes de medir:** `docs/decisiones.md`, 17/11 (`b4ec45f`, candidatos y regla; `5cd0357`,
  configuración fijada tras el piloto).
- **Etiquetas:** [medido] en esta sesión, con la salida en `validation/conjunto/salidas/`; [inferencia] es una lectura
  mía.

## En pocas líneas

1. **K2 gana a `main` en todo lo que se puede medir sin el partido** [medido]: en la DFL con control (+0,036 a +0,051),
   en la DFL con el flag (+0,033 a +0,044) y en SkillCorner (+0,021 a +0,028), examen incluido.
2. **Es el primer candidato que pasa las tres cosas a la vez.** La red de una capa, B9, el detector de cambios y B11
   ganaban con el flag, empataban con control y no pasaban SkillCorner.
3. **No inventa posesiones: las coloca mejor.** Predice casi las mismas que `main` (1.651 frente a 1.661 en la DFL) y
   acierta más recuperaciones y más duelos con cambio en los eventos humanos.
4. **No está en la entrega.** Falta el punto 4 de su regla, que es del partido y lo ejecuta una persona: cuatro
   comandos, con los criterios de daño ya escritos.
5. **K1, la capa de cambios aprendida, no pasa:** gana con el flag, pero con control solo gana en 4–6 de 7 partidos.

## Qué es K2

- **Qué mira.** A cada jugador por separado: dónde está respecto al balón, cómo se mueve, si se acerca al balón y dónde
  está en el campo (14 números). B5 mira unos pocos agregados por frame.
- **Cómo los junta.** Una red pequeña por jugador, la misma para todos; por equipo, la suma y el máximo de sus jugadores;
  y una convolucional temporal que ve ±12,6 s, a 5 Hz. 36.260 pesos. No necesita identidades ni un número fijo de
  jugadores.
- **Qué dice.** Solo `H` frente a `A`: un logit z, que se puntúa igual que el de B5
  (`aprendida.puntuacion_de("b5", …)`, con α = 4). El `D`, el decodificador y las capas del partido no cambian.
- **Con qué se entrenó.** Las etiquetas de control en los 7 partidos de la DFL y las de SkillCorner en sus 10 partidos
  de entrenamiento, con el balón «como el ATD», y aumentos hacia el ATD: el balón hasta 5 frames tarde, slots que faltan
  y duplicados, huecos de balón y el balón a la vista en las paradas.
- **Cómo corre en la entrega.** `possession/conjunto.py`, en numpy puro, sin exponenciales ni BLAS: sumas, productos,
  divisiones, raíces y máximos, término a término. Tarda unos 5 s por partido. Los pesos van en
  `possession/conjunto_pesos.npz` (1,2 MB). Torch solo hizo falta para entrenar.

## Resultado [medido]

K2 frente a `main` (B5, `dead_state` y `decode_cortas_a_d`). En la DFL y en la mitad de entrenamiento de SkillCorner,
cada partido se puntúa con un modelo que no lo vio.

| datos | `D` | condición | `main` | K2 | diferencia [5–95 %] | gana en |
|---|---|---|---|---|---|---|
| DFL, control | de las etiquetas | como el ATD | 0,728 | 0,780 | +0,051 [+0,040 a +0,064] | 7 de 7 |
| DFL, control | de las etiquetas | como el ATD, sin bloques | 0,748 | 0,794 | +0,046 [+0,035 a +0,057] | 6 de 7 |
| DFL, control | propio | como el ATD | 0,623 | 0,668 | +0,045 [+0,035 a +0,057] | 6 de 7 |
| DFL, control | propio | como el ATD, sin bloques | 0,651 | 0,686 | +0,036 [+0,024 a +0,047] | 6 de 7 |
| DFL, flag | de las etiquetas | como el ATD | 0,498 | 0,542 | +0,044 [+0,034 a +0,054] | 7 de 7 |
| DFL, flag | de las etiquetas | como el ATD, sin bloques | 0,512 | 0,549 | +0,037 [+0,027 a +0,046] | 7 de 7 |
| DFL, flag | propio | como el ATD | 0,414 | 0,457 | +0,043 [+0,034 a +0,052] | 7 de 7 |
| DFL, flag | propio | como el ATD, sin bloques | 0,431 | 0,464 | +0,033 [+0,024 a +0,042] | 7 de 7 |
| SkillCorner, entrenamiento | de las etiquetas | detectado | 0,519 | 0,543 | +0,023 [+0,015 a +0,031] | 8 de 10 |
| SkillCorner, entrenamiento | de las etiquetas | detectado, suavizado | 0,514 | 0,539 | +0,024 [+0,016 a +0,032] | 7 de 10 |
| SkillCorner, entrenamiento | propio | detectado | 0,391 | 0,413 | +0,021 [+0,014 a +0,029] | 10 de 10 |
| SkillCorner, entrenamiento | propio | detectado, suavizado | 0,388 | 0,412 | +0,024 [+0,017 a +0,032] | 10 de 10 |
| SkillCorner, examen | de las etiquetas | detectado | 0,509 | 0,532 | +0,023 [+0,015 a +0,032] | 9 de 10 |
| SkillCorner, examen | de las etiquetas | detectado, suavizado | 0,504 | 0,532 | +0,028 [+0,019 a +0,037] | 10 de 10 |
| SkillCorner, examen | propio | detectado | 0,389 | 0,409 | +0,021 [+0,013 a +0,028] | 8 de 10 |
| SkillCorner, examen | propio | detectado, suavizado | 0,384 | 0,410 | +0,026 [+0,019 a +0,034] | 10 de 10 |

**Con la regla del límite de daño (16/11):** pasa el punto 1 (control), el 3 (flag) y el 2 (SkillCorner, con el examen
usado una vez). **Con la regla de §5.8 frente a `main`:** «gana», según la salida del harness oficial.

**Los eventos humanos de la DFL** (descriptivo; los anota una persona, no nuestras reglas), «como el ATD»:

| versión | pase completado | recuperación | duelo con cambio | duelo sin cambio |
|---|---|---|---|---|
| `main` | 96,3 % | 70,3 % | 77,3 % | 74,9 % |
| K2 | 98,0 % | 80,0 % | 82,5 % | 77,7 % |
| K2 − `main` [5–95 %] | – | +9,7 [+4,1 a +14,9] | +5,2 [+2,2 a +9,2] | +2,8 [−1,9 a +7,6] |

**Lo demás:**
- Con el balón a la vista en los `D` y el `D` propio: +0,044 y +0,035 con control, +0,035 y +0,029 con el flag.
- Sin el partido del piloto: con control, de +0,034 a +0,047 (5 o 6 de 6); con el flag, de +0,034 a +0,045 (6 de 6).
- Con cualquier α entre 0,5 y 8 gana en las ocho celdas de la DFL.
- Sin voto: con el balón limpio, +0,032 (flag) y +0,034 (control); con «huecos y suavizado», +0,040 y +0,064.

## El piloto y el sobreajuste [medido]

Antes de entrenar los 8 pliegues se entrenó uno, con seis variantes. Fuera de muestra, las tres pequeñas empatan y las
grandes pierden:

| variante | pesos | acierto de z fuera: DFL / SkillCorner | dentro (DFL) |
|---|---|---|---|
| la escrita antes (la que se usa) | 36.260 | 93,7 % / 85,9 % | 93,2 % |
| red 9 veces mayor, 8.000 pasos | 308.484 | 92,1 % / 84,8 % | 99,4 % |
| 64 canales, abandono 0,2 | 84.740 | 92,0 % / 85,7 % | 96,2 % |

Con ±12 s de contexto, la posición de 22 jugadores identifica el momento del partido, y una red grande se lo aprende de
memoria. Con 17 partidos, el modelo tiene que ser pequeño. El piloto no cambió nada de lo escrito antes.

## Qué parte del análisis de fuera era cierta [inferencia, sobre lo medido]

- **Cierto:** el cuello de botella era la evidencia de equipo, y un modelo que mira a los jugadores uno a uno y en el
  tiempo lo mejora.
- **No hizo falta:** cambiar la pregunta («¿dónde cambia?») ni el decodificador. La salida de cambios por sí sola (K1) no
  pasó, y K2 gana con el Viterbi de coste fijo de siempre.
- **Lo que decidió** fue lo que el análisis ponía como detalle del entrenamiento: las etiquetas de control en todos los
  frames vivos (B11, sin ellas, ganaba solo con el flag) y entrenar también con SkillCorner (B11, sin él, perdía allí).
- **No se probó:** meter el `D` en el modelo (el harness no puede validarlo con el balón) ni el balón del vídeo.

## Lo que falta: el punto 4, en el partido

Lo ejecuta una persona, con el python del entorno limpio, desde la carpeta de la rama:

    python -m possession.pipeline --name equipo_v9_rama
    python validation/partido/conjunto_en_el_partido.py
    python validation/partido/probar_entrega.py prueba_k2 --pieza candidates=aprendida.evidence_k2 --contra equipo_v9_rama
    python evaluation/validate_submission.py evaluation/results/prueba_k2.csv

Los criterios (C0 a C6) están en `docs/decisiones.md`, 17/11, escritos antes de generar nada. En corto: la rama no
cambia la entrega; el modelo dice en el ATD cosas parecidas a las que dice en los datos abiertos; frente a `equipo_v9`
cambia como mucho el 12 % de los frames; el número de posesiones y de paradas y el `D` se quedan cerca; no fragmenta; y
la ventana pública no se rompe.

Lo que cabe esperar [medido en datos abiertos, `cuanto_cambia.py`]: cambia entre el 4 y el 8 % de los frames evaluados,
unos 3 puntos de un equipo al otro; las posesiones suben entre el 0 y el 4 %; ninguna posesión de menos de 12 frames.

## Lo que no he podido comprobar

- **Nada del partido.** Si el ATD se parece lo bastante a los datos de entrenamiento lo dice el punto 4, no el harness.
- **La reproducción en otra máquina.** La pieza está escrita para dar lo mismo bit a bit (sin exponenciales, sin BLAS y
  sin `np.interp`), pero solo se ha ejecutado en esta.
- **El entrenamiento no es reproducible bit a bit** (GPU). Los pesos sí: están en el repo, y la entrega solo usa los
  pesos.
- **El harness sobrestima el nivel.** La ganancia en el partido será menor que en la DFL [inferencia]; la de SkillCorner
  (+0,02 a +0,03) es la más parecida a un tracking automático.

## Ficheros

| fichero | qué es |
|---|---|
| `possession/conjunto.py`, `possession/conjunto_pesos.npz` | la pieza en numpy y sus pesos (apagada) |
| `possession/aprendida.py` | el envoltorio `evidence_k2`, para `--pieza` y para el harness |
| `validation/conjunto/exportar.py`, `red.py`, `entrenar.py`, `juntar.py` | exportar los datos abiertos, la red en torch, entrenar un pliegue y juntar los pesos |
| `validation/conjunto/medir.py` | K1 y K2 frente a `main`, con la regla; con `--con-la-pieza`, en numpy; el examen, cerrado salvo con dos banderas |
| `validation/conjunto/paridad.py` | numpy frente a torch |
| `validation/conjunto/cuanto_cambia.py`, `referencia.py`, `agregados.py`, `referencia_abiertos.json` | lo que cabe esperar en la entrega de prueba y la referencia para el partido |
| `validation/partido/conjunto_en_el_partido.py` | **lee el partido:** las entradas y las salidas del modelo en el ATD frente a la referencia |
| `validation/scripts/prueba_conjunto.py`, `prueba_conjunto_en_el_partido.py` | pruebas sin datos |
| `validation/harness/versiones/conjunto_2026-11-17.json` | las versiones del harness oficial |
| `validation/conjunto/pregunta_organizacion.md` | borrador de la pregunta a la organización sobre la regla de posesión (sin enviar) |
