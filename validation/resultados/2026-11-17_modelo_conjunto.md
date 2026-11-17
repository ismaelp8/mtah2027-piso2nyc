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

1. **K2 gana a `main` donde ha visto partidos de ese proveedor** [medido]: en la DFL con control (+0,036 a +0,051),
   en la DFL con el flag (+0,033 a +0,044) y en SkillCorner (+0,021 a +0,028), examen incluido. Pasa su regla y gana
   también con §5.8.
2. **Pero no se traslada de un proveedor a otro** [medido]: entrenado solo con la DFL pierde en SkillCorner (−0,010 a
   −0,015), y entrenado solo con SkillCorner pierde en la DFL (−0,075 a −0,096 con control). El partido es de un
   tercer proveedor. **Por eso no se recomienda para la entrega sin más: es una apuesta.**
3. **No es una apuesta a ciegas** [medido]: en Metrica, el único tercer proveedor abierto, el modelo de los dos
   proveedores gana (+0,035) y más que cualquiera de un solo proveedor; aguanta los slots de más y el balón tarde del
   ATD mejor que B5; y hay una alarma (el criterio C2) que salta donde se sabe que el modelo falla.
4. **No inventa posesiones: las coloca mejor.** Predice casi las mismas que `main` (1.651 frente a 1.661 en la DFL) y
   acierta más recuperaciones y más duelos con cambio en los eventos humanos.
5. **No está en la entrega, y lo decide el equipo.** El punto 4 de su regla, en el partido, está listo: cuatro
   comandos, con los criterios de daño ya escritos.
6. **K1, la capa de cambios aprendida, no pasa,** y decodificar a riesgo mínimo con K2 tampoco merece construirse.

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

## El cambio de proveedor [medido]

Todo lo de arriba se midió con partidos del mismo proveedor en el entrenamiento. Para ver qué pasa sin ellos se
entrenaron dos modelos con un solo proveedor cada uno, y se puntuó todo también en Metrica, que ninguno vio. K2 con
α = 4 frente a `main`, con el `D` de las etiquetas:

| entrenado con | en la DFL, control | en SkillCorner, entrenamiento | en Metrica |
|---|---|---|---|
| solo la DFL | – | −0,015 y −0,010 | +0,023 y +0,026 |
| solo SkillCorner | −0,096 y −0,075 | – | −0,022 y −0,021 |
| los dos (K2) | +0,051 y +0,046 (cruzado) | +0,023 y +0,024 (cruzado); examen, +0,023 y +0,028 | +0,035 y +0,036 |

- **Con un solo proveedor, K2 no se traslada al otro.** El de solo la DFL pierde en SkillCorner lo mismo que B11.
- **Con los dos, gana en el tercero,** y más que cualquiera de un solo proveedor. Metrica son 3 partidos, con un balón
  pegado al jugador y etiquetas sacadas de eventos: es una señal, no una prueba.
- **B5 sí se traslada:** gana al baseline en SkillCorner y en Metrica sin haberlos visto. Un modelo de 30 agregados
  generaliza mejor que uno de 36.000 pesos que ve a cada jugador.

**Una ronda para acercar los proveedores (K2r), cerrada en su primer paso.** Con una sola configuración de aumentos
en los partidos de la DFL (jugadores que faltan como en SkillCorner, datos a 10 Hz y ruido lento de posición), el modelo
de solo la DFL pasa de −0,015 y −0,010 en SkillCorner a −0,004 y −0,002 con el `D` de las etiquetas: un empate. Con el
`D` propio no cambia (−0,008 y −0,005), y la regla pedía no perder más de 0,005 en ninguna celda. Parecerse por fuera a
un tracking automático quita la mitad del problema; la otra mitad es que cada proveedor etiqueta la posesión a su
manera [inferencia].

**Los dos rasgos medidos del ATD** (`como_el_atd.py`, DFL): con los tracklets cortados, un slot de más en el 12,9 % de
los frames y el balón 4 frames tarde, K2 gana a `main` por +0,040 a +0,068 con control. A `main` esas degradaciones le
cuestan hasta 0,013; a K2, nada.

**La alarma** (`potencia_c2.py`): el criterio C2 del punto 4 compara las salidas del modelo en el partido con su rango
en los datos abiertos. Con los modelos de un solo proveedor, salta en 22 de las 28 vistas de la DFL y en las 20 de
SkillCorner. En el partido es menos sensible, porque el rango junta dos proveedores.

## Decodificar para la métrica [medido]

El sondeo de riesgo mínimo del 16/11, repetido con K2: la duda del modelo ahora sí dice algo (AUC de 0,68 y 0,70),
pero las muestras se siguen fragmentando (2.196 posesiones por parte, cuando hay unas 220) y la elección por parte
pierde con control (−0,019). No merece construirse. Haría falta entrenar el modelo como un CRF.

## Qué parte del análisis de fuera era cierta [inferencia, sobre lo medido]

- **Cierto:** el cuello de botella era la evidencia de equipo, y un modelo que mira a los jugadores uno a uno y en el
  tiempo lo mejora.
- **No hizo falta:** cambiar la pregunta («¿dónde cambia?») ni el decodificador. La salida de cambios por sí sola (K1) no
  pasó, y K2 gana con el Viterbi de coste fijo de siempre.
- **Lo que decidió** fue lo que el análisis ponía como detalle del entrenamiento: las etiquetas de control en todos los
  frames vivos (B11, sin ellas, ganaba solo con el flag [inferencia: no se ha medido K2 sin ellas]) y entrenar también
  con SkillCorner (medido: sin él, K2 pierde allí).
- **Lo que el análisis no veía:** el problema que queda no es de arquitectura, sino de proveedor. Un modelo que mira a
  cada jugador aprende también las manías del tracking con el que se entrena.
- **No se probó:** meter el `D` en el modelo (el harness no puede validarlo con el balón) ni el balón del vídeo.

## Si el equipo quiere mirarlo: el punto 4, en el partido

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

- **Nada del partido.** Si el ATD se parece lo bastante a los datos de entrenamiento no lo dice el harness. El punto 4
  puede dar la alarma, pero no puede probar que K2 gane allí: no hay ni un partido del ATD con etiquetas, y la ventana
  pública no sirve para elegir.
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
| `validation/conjunto/como_el_atd.py`, `metrica.py`, `potencia_c2.py`, `riesgo_minimo_k2.py` | las comprobaciones: los rasgos del ATD, el tercer proveedor, la alarma y el riesgo mínimo |
| `validation/partido/conjunto_en_el_partido.py` | **lee el partido:** las entradas y las salidas del modelo en el ATD frente a la referencia |
| `validation/scripts/prueba_conjunto.py`, `prueba_conjunto_en_el_partido.py` | pruebas sin datos |
| `validation/harness/versiones/conjunto_2026-11-17.json` | las versiones del harness oficial |
| `validation/conjunto/pregunta_organizacion.md` | borrador de la pregunta a la organización sobre la regla de posesión (sin enviar) |
