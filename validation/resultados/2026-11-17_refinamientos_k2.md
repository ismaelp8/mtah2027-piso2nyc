# Refinamientos de K2 sin reentrenar: la mezcla con B5 (K3) y el espejo (K4)

- **Quién y cuándo:** Claude, en la sesión de Ismael, el 17/11/2026. Rama `exp/k2-refinar`, que sale de
  `exp/modelo-conjunto` en `2b187b9`.
- **Encargo:** «seguir profundizando en ese método y refinarlo lo máximo posible», mientras David comprueba K2.
- **Regla nº 1 respetada.** No se ha abierto nada del partido. Todo se midió en datos abiertos de otros partidos: los 7
  de la Bundesliga (DFL; Bassek et al., 2025, CC BY 4.0), los 10 de entrenamiento de SkillCorner (A-League 2024/25,
  MIT) y los 3 de Metrica sample-data. **El examen de SkillCorner no se ha leído.**
- **Reglas escritas antes de medir:** `docs/decisiones.md`, 17/11 (`d96fce8`, candidatos y regla; `017c4fe`, la lectura
  de la semilla nueva). Los resultados, en las entradas «K4 se cierra; K3 pasa dos de sus tres puntos» y «la semilla
  nueva del modelo de un solo proveedor».
- **Mientras tanto, David encendió K2** en su rama `feat/encender-k2` (`equipo_v10`, reproducida en su máquina). Todo
  lo que sigue compara K3 y K2 con B5, que es a lo que estas tablas llaman `main`.
- **Después (17/11 por la tarde): K3 pasó su entrega de prueba frente a `equipo_v10` e Ismael decidió encenderla,**
  en la rama `feat/encender-k3` (`docs/decisiones.md`, «se enciende K3»). Es una decisión del equipo: con la regla
  de abajo, K3 no quedaba recomendada por encima de K2. Los pasos que faltan, en `validation/conjunto/COMPROBAR_K3.md`.
- **Etiquetas:** [medido] en esta sesión, con la salida en `validation/conjunto/salidas/2026-11-17_refinar_*`;
  [inferencia] es una lectura mía.

Para leerlo sin el resto del repo:
- **`main`** es la entrega de hoy, con B5 como evidencia de equipo: una regresión logística sobre unos 30 resúmenes por
  frame.
- **K2** es la red que mira a cada jugador (`validation/resultados/2026-11-17_modelo_conjunto.md`). Está apagada.
- **Control y flag** son las dos formas de etiquetar la posesión en la Bundesliga: con control, la posesión cambia
  cuando el rival controla el balón (es lo que dice el reto); con el flag, en su primer toque.
- **Un pliegue** es un modelo entrenado sin el partido que se puntúa, para que no lo haya visto.
- **Una réplica** es el mismo entrenamiento repetido aquí, con otros números al azar.
- Las cifras son diferencias de `spellF1` con `main`. Por debajo de unos ±0,01 es ruido.

## En pocas líneas

1. **K4, el espejo, se cierra** [medido]. Promediar el logit de K2 con el del campo en espejo gana en la DFL (+0,005
   con control) y empata en SkillCorner y en Metrica. La regla pedía ganar en los dos.
2. **K3, la mezcla a partes iguales de K2 y B5, gana a `main` en todo lo medido** [medido]: en la DFL (+0,029 a +0,054
   con control), en SkillCorner (+0,017 a +0,023), en Metrica (+0,014 a +0,029) y, con una réplica de K2 entrenada solo
   con la DFL, en SkillCorner (+0,008 a +0,011), donde K2 solo empata.
3. **Pero no queda recomendada por encima de K2.** El punto que tenía que decidirlo (¿deja de perder donde K2 pierde?)
   no se puede leer: la réplica no repite la pérdida publicada de K2. Con la regla escrita antes, K3 se queda como
   opción apagada.
4. **K3 es un seguro, y es más prudente justo en los cambios de posesión.** Partido a partido falla menos que K2 (3
   casos por debajo de `main` de 136, frente a 12). A cambio predice un 2 % menos de posesiones que `main`, se queda
   con la mitad de lo que K2 mejora en las recuperaciones, y en Metrica y con el flag queda por debajo de K2.
5. **Fuera de su proveedor, K2 queda entre un empate y una pérdida pequeña** [medido]: en tres entrenamientos del
   modelo de solo la DFL (el original y dos réplicas), de +0,003 a −0,015 frente a `main` en SkillCorner, sin ganar en
   ninguno. **Promediar parece ayudar** (con solo dos semillas): la media de las dos réplicas queda en +0,002 a +0,004, y
   mezclada con B5, en +0,007 a +0,017, lo mejor que se ha medido fuera del proveedor.
6. **Ni K2 ni K3 ven más cambios de posesión: los colocan mejor.** El hueco de las posesiones que no vemos sigue ahí.

## Qué son K3 y K4

- **K3.** Dos opiniones sobre quién tiene el balón, la de K2 y la de B5, cada una un número por frame (positivo, el
  local; negativo, el visitante). K3 es su media, y se puntúa como B5. Si las dos coinciden, opina con la misma fuerza;
  si discrepan, opina flojo y el decodificador mantiene lo que había. No se entrena nada.
- **K4.** K2 dos veces: con el campo como viene y con el campo en espejo (las bandas cambiadas), y la media de las dos.
  K2 se entrenó viendo las dos versiones, pero no da exactamente lo mismo en una y en otra.
- **K5** (K3 con el logit de K4) no llegó a ser candidato, porque K4 no pasó.
- Los tres están en `possession/refinamientos.py`, apagados. No tocan B5, K2 ni sus pesos.

## Resultado [medido]

Diferencia con `main`; entre corchetes, el intervalo del 5 al 95 %; después, en cuántos partidos gana.

**DFL, 7 partidos, cada uno con el pliegue que no lo vio:**

| etiquetas | `D` | condición | K2 | K3 | K4 |
|---|---|---|---|---|---|
| control | de las etiquetas | como el ATD | +0,051 [+0,040 a +0,064] · 7 | +0,054 [+0,045 a +0,063] · 7 | +0,060 [+0,049 a +0,071] · 7 |
| control | de las etiquetas | como el ATD, sin bloques | +0,046 [+0,035 a +0,057] · 6 | +0,047 [+0,038 a +0,054] · 7 | +0,052 [+0,041 a +0,063] · 7 |
| control | propio | como el ATD | +0,045 [+0,035 a +0,057] · 6 | +0,042 [+0,034 a +0,050] · 7 | +0,048 [+0,037 a +0,059] · 7 |
| control | propio | como el ATD, sin bloques | +0,036 [+0,024 a +0,047] · 6 | +0,032 [+0,025 a +0,040] · 7 | +0,038 [+0,027 a +0,049] · 6 |
| flag | de las etiquetas | como el ATD | +0,044 [+0,034 a +0,054] · 7 | +0,031 [+0,023 a +0,039] · 7 | +0,047 [+0,037 a +0,057] · 7 |
| flag | de las etiquetas | como el ATD, sin bloques | +0,037 [+0,027 a +0,046] · 7 | +0,024 [+0,017 a +0,031] · 7 | +0,039 [+0,029 a +0,048] · 7 |
| flag | propio | como el ATD | +0,043 [+0,034 a +0,052] · 7 | +0,025 [+0,018 a +0,032] · 7 | +0,041 [+0,032 a +0,051] · 7 |
| flag | propio | como el ATD, sin bloques | +0,033 [+0,024 a +0,042] · 7 | +0,017 [+0,011 a +0,024] · 7 | +0,033 [+0,024 a +0,042] · 7 |

Con el balón a la vista en los `D` y el `D` propio, K3 saca +0,040 y +0,029 con control y +0,022 y +0,013 con el flag.

**SkillCorner, los 10 partidos de entrenamiento, con los pliegues cruzados:**

| `D` | condición | K2 | K3 | K4 |
|---|---|---|---|---|
| de las etiquetas | detectado | +0,023 [+0,015 a +0,031] · 8 | +0,021 [+0,016 a +0,026] · 10 | +0,022 [+0,014 a +0,030] · 8 |
| de las etiquetas | detectado, suavizado | +0,024 [+0,016 a +0,032] · 7 | +0,023 [+0,017 a +0,028] · 9 | +0,027 [+0,019 a +0,035] · 8 |
| propio | detectado | +0,021 [+0,014 a +0,029] · 10 | +0,017 [+0,011 a +0,022] · 10 | +0,020 [+0,013 a +0,028] · 9 |
| propio | detectado, suavizado | +0,024 [+0,017 a +0,032] · 10 | +0,021 [+0,015 a +0,026] · 10 | +0,024 [+0,016 a +0,032] · 10 |

**Metrica, 3 partidos, con los pesos de la entrega** (un proveedor que ni K2 ni B5 vieron):

| `D` | condición | K2 | K3 | K4 |
|---|---|---|---|---|
| de las etiquetas | tal cual (vota) | +0,035 [+0,019 a +0,051] · 2 | +0,023 [+0,013 a +0,033] · 3 | +0,035 [+0,019 a +0,050] · 3 |
| de las etiquetas | suavizado 25 | +0,036 [+0,020 a +0,052] · 3 | +0,029 [+0,018 a +0,041] · 3 | +0,039 [+0,022 a +0,054] · 3 |
| propio | tal cual (vota) | +0,021 [+0,007 a +0,035] · 2 | +0,014 [+0,005 a +0,025] · 3 | +0,024 [+0,010 a +0,038] · 2 |
| propio | suavizado 25 | +0,024 [+0,010 a +0,037] · 3 | +0,017 [+0,008 a +0,028] · 3 | +0,022 [+0,009 a +0,036] · 3 |

**Con la regla:**
- **K4 frente a K2:** en la DFL, +0,005 de media con control y peor celda −0,001; en SkillCorner, −0,000 de media.
  Se pedía +0,003 en los dos: **no pasa.**
- **K3, punto 1 (dentro del proveedor): pasa.** **Punto 3 (Metrica): pasa.**
- **Con la regla de §5.8 frente a `main`** (más de +0,03 con las dos convenciones), el harness oficial dice «gana» para
  K2 y «empate o no concluye» para K3, que con el flag se queda en +0,017 a +0,031.

## El otro proveedor [medido]

El 17/11 se midió que K2 entrenado solo con la DFL perdía en SkillCorner. Los pesos de ese modelo están en la máquina de
la GPU, así que aquí se entrenó una réplica en la CPU (3.000 pasos, 55 minutos) y se puntuó igual, con α = 4:

| `D` | condición | K2, modelo original (17/11) | K2, réplica | K3, con la réplica | K3 − K2, con la réplica |
|---|---|---|---|---|---|
| de las etiquetas | detectado | −0,015 [−0,023 a −0,007] | −0,005 [−0,013 a +0,003] · 4 de 10 | +0,008 [+0,002 a +0,014] · 6 | +0,013 [+0,008 a +0,018] · 7 |
| de las etiquetas | detectado, suavizado | −0,010 [−0,018 a −0,002] | +0,001 [−0,007 a +0,009] · 5 | +0,011 [+0,004 a +0,018] · 6 | +0,010 [+0,005 a +0,014] · 9 |
| propio | detectado | −0,007 | −0,000 [−0,008 a +0,006] · 5 | +0,010 [+0,004 a +0,016] · 7 | +0,011 [+0,006 a +0,015] · 6 |
| propio | detectado, suavizado | −0,004 | +0,003 [−0,005 a +0,011] · 6 | +0,010 [+0,004 a +0,017] · 7 | +0,008 [+0,003 a +0,012] · 7 |

- **La réplica no repite la pérdida.** La regla pedía, para poder leer el punto 2 de K3, que K2 con la réplica perdiera
  más de 0,005 en las dos celdas con el `D` de las etiquetas. Queda en −0,005 y +0,001. **El punto 2 no se puede leer,**
  y con la regla escrita antes K3 no se recomienda por encima de K2.
- **Lo que sí se ve, sin voto:** en un proveedor que ninguna de sus dos mitades vio, la mezcla gana a `main` en las
  cuatro celdas y a K2 solo en las cuatro, con los intervalos por encima de cero. Juntas ven más que por separado.
- **La réplica y el original aciertan lo mismo frame a frame** en esos 10 partidos: 84,0 % y 83,8 % con el balón
  detectado, y la misma pérdida (0,762 y 0,766). Que la nota difiera en 0,010 con el mismo acierto apunta a que un
  entrenamiento de K2 y otro, iguales en todo menos en el azar, se separan esa cantidad fuera de su proveedor
  [inferencia: es una réplica, que además cambia de GPU a CPU, de 48 a 33 columnas y de versión de torch].
- **Fuera de su proveedor, K2 cambia de equipo de más:** con la réplica predice 2.491 posesiones en SkillCorner
  (`main`, 2.270) y casan el 60,4 % (`main`, el 63,9 %). La mezcla lo frena: 2.307, y casan el 64,6 %.
- **Una segunda réplica, con otra semilla** (lectura escrita antes de entrenarla): K2 queda en −0,007, −0,003, −0,003
  y −0,001. Es el caso mixto de su lectura: pierde más de 0,005 en una de las dos celdas con el `D` de las etiquetas.
  **En los tres entrenamientos, K2 fuera de su proveedor va de +0,003 a −0,015, y no gana en ninguno.** K3 con ella
  repite lo de la primera: de +0,005 a +0,011 frente a `main` y de +0,009 a +0,015 frente a K2 solo (9 o 10 de 10).
  Las dos réplicas siguen sin repetir la pérdida en las dos celdas que pedía la regla, así que el punto 2 de K3 sigue
  sin poderse leer.
- **La media de las z de las dos réplicas** (una lectura, no un candidato): K2 pasa a +0,004, +0,004, +0,002 y
  +0,002, por encima de cada semilla en siete de las ocho comparaciones, con el intervalo por encima de cero en
  cuatro. Es poca evidencia: dos semillas de un modelo de un solo proveedor. Mezclada con B5: +0,013, +0,017, +0,007
  y +0,011.
- **La réplica de solo la DFL en Metrica:** K2, +0,030 en las cuatro celdas; K3, de +0,025 a +0,036. Allí el modelo de solo la DFL
  funciona casi como el de los dos proveedores.
- **El otro sentido, sin voto: K2 entrenado solo con SkillCorner.** Esta réplica sí repite la pérdida publicada. En la
  DFL, K2 queda de −0,048 a −0,083 con control y de −0,025 a −0,056 con el flag; la mezcla vuelve al nivel de `main`
  con control (de −0,000 a +0,008) y se queda de 0,007 a 0,020 por debajo con el flag. Allí la mitad de B5 juega en
  casa. En Metrica, que ninguna de las dos mitades vio, K2 pierde de −0,019 a −0,026 y la mezcla queda entre −0,006 y
  +0,014. **Cuando K2 se equivoca mucho, la mezcla cae más o menos donde estaba B5, no por encima.**
- **Partido a partido, con la réplica de solo la DFL:** K2 queda por debajo de `main` en 20 de 40 casos (el peor, −0,054); K3, en 14
  (el peor, −0,025).

## Los cambios de posesión [medido]

Es donde más fallamos (`validation/resultados/2026-11-15_diagnostico_errores.md`): cambiamos de equipo de menos.

**Posesiones reales encontradas** (emparejadas con una predicha con un solape de 0,5 o más), `D` de las etiquetas:

| datos | reales | `main`: predichas, encontradas | K2 | K3 |
|---|---|---|---|---|
| DFL, control | 1.736 | 1.661, el 72,5 % | 1.651, el 76,9 % | 1.597, el 75,9 % |
| DFL, flag | 3.061 | 1.661, el 39,1 % | 1.651, el 42,5 % | 1.597, el 41,0 % |
| SkillCorner, entrenamiento | 3.228 | 2.270, el 44,9 % | 2.306, el 47,9 % | 2.195, el 46,3 % |
| Metrica | 879 | 612, el 57,5 % | 624, el 60,6 % | 607, el 58,8 % |

**Eventos humanos de la DFL** (los anota una persona; «como el ATD», `D` de las etiquetas):

| versión | pase completado | recuperación | duelo con cambio | duelo sin cambio |
|---|---|---|---|---|
| `main` | 96,3 % | 70,3 % | 77,3 % | 74,9 % |
| K2 | 98,0 % | 80,0 % | 82,5 % | 77,7 % |
| K3 | 97,5 % | 74,9 % | 79,9 % | 79,6 % |
| K3 − `main` [5–95 %] | – | +4,6 [+1,0 a +8,2] | +2,6 [+0,4 a +5,2] | +4,7 [+1,4 a +8,5] |

- **K2 no predice más posesiones que `main`: predice casi las mismas y acierta más.** De cada 100 reales encuentra
  entre 2 y 4 más, y acierta 10 recuperaciones más de cada 100.
- **K3 predice menos** (con el `D` de las etiquetas, un 4 % menos que `main` en la DFL y un 3 % en SkillCorner; con el
  propio, un 2 %) **y se queda a medio camino:** la mitad de la mejora de K2 en recuperaciones y, en duelos con
  cambio, entre casi nada («sin bloques», +0,4 puntos de +3,1) y la mitad («como el ATD»). A cambio es la que menos
  cambia cuando no debe.
- **El hueco sigue ahí.** Con el flag y en SkillCorner no encontramos ni la mitad de las posesiones reales, con
  ninguna de las tres. Las redes que predicen más posesiones (B11, B13 y B14) ganan con el flag y pierden o
  empatan en SkillCorner: las que añaden no caen donde deben [medido por la otra línea, en la rama
  `claude/serene-lumiere-16245d`; no es de esta sesión].

## Las tres conclusiones de David, donde hay miles de posesiones [medido]

David miró la entrega frente a los 5 minutos públicos del partido (`notebooks/ventana_publica_detalle.ipynb`, rama
`feat/encender-k2`; 17 posesiones) y sacó tres conclusiones. El mismo análisis, con sus mismas cuentas, se repite aquí en
los 20 partidos abiertos (`validation/conjunto/detalle_abiertos.py`), con el `D` propio, como en la entrega:

**1. «Cuando vemos un cambio lo ponemos en su sitio; el problema son los que no vemos.» Se repite.**

| datos | cambios directos entre equipos | `main` ve | K2 ve | K3 ve | nos sobran: `main` / K2 / K3 |
|---|---|---|---|---|---|
| DFL, control (7 partidos) | 1.026 | 35,0 % | 48,1 % | 44,4 % | 505 / 396 / 373 |
| DFL, flag (7) | 2.351 | 18,7 % | 24,9 % | 22,6 % | 438 / 315 / 308 |
| SkillCorner, entrenamiento (10) | 2.210 | 17,6 % | 21,2 % | 19,6 % | 719 / 685 / 633 |
| Metrica (3) | 668 | 34,3 % | 40,0 % | 37,7 % | 148 / 108 / 125 |

Un cambio está «visto» si hay uno nuestro hacia el mismo estado a 1 s o menos. De todos los que vemos (también los que
pasan por `D`), el retraso mediano es de +2 a +5 frames en la DFL, de 0 en SkillCorner y de +1 a +3 en Metrica. Con el
`D` de las etiquetas es de 0 en todas partes y unos 9 de cada 10 caen a 12 frames o menos: el poco retraso que hay viene de
nuestro `D`, no de la evidencia de equipo.

**2. «Reales 17, nuestras 13: nos faltan 4» (el 76 %). Se repite.** Con `main` predecimos el 89 % de las posesiones que
hay en la DFL con control, el 73 % en Metrica, el 65 % en SkillCorner y el 50 % en la DFL con el flag. K2 predice hasta
un 2 % más que `main`, y K3, un 2 % menos en la DFL y en SkillCorner.

**3. «Nuestras posesiones duran un 34 % más: nos comemos posesiones cortas del rival.» Se repite, y se ve dónde.**

| datos | duración media: real / `main` / K2 / K3 (s) | de menos de 2 s: reales, y encontradas con `main` / K2 / K3 | de 2 a 5 s: reales, y encontradas |
|---|---|---|---|
| DFL, control | 12,7 / 14,8 / 14,5 / 15,1 | 159: el 5,7 / 8,8 / 6,9 % | 399: el 27,1 / 38,8 / 32,6 % |
| DFL, flag | 7,2 / 14,8 / 14,5 / 15,1 | 919: el 1,8 / 2,3 / 2,1 % | 934: el 16,3 / 22,3 / 18,1 % |
| SkillCorner, entrenamiento | 9,9 / 15,9 / 15,0 / 15,8 | 724: el 0,4 / 0,7 / 0,1 % | 714: el 13,6 / 15,1 / 13,9 % |
| Metrica | 12,8 / 16,3 / 16,3 / 16,3 | 140: el 2,1 / 5,0 / 4,3 % | 219: el 24,7 / 27,4 / 28,3 % |

- **Las posesiones de menos de 2 s no las encuentra ninguna versión.** En entre 4 y 7 de cada 10 no decimos su
  equipo ni en la mitad de sus frames: se las come la posesión de al lado o, con el `D` propio, una parada.
- **Lo que K2 arregla está entre 2 y 10 s:** en la DFL con control pasa del 27 al 39 % en las de 2 a 5 s y del 65 al
  68 % en las de 5 a 10 s. K3 se queda a medio camino (33 % y 68 %).
- **Casi nunca partimos una posesión:** las perdidas por ir partidas o más cortas son del 1 al 3 % de las reales. Las
  perdemos por no decir su equipo ni en la mitad de sus frames (del 10 al 30 %), por fundirlas con la de al lado (del 12 al 27 %) y por taparlas con `D` (del
  10 al 13 %).

Lo que significa [inferencia]: lo que David vio en 17 posesiones no es un accidente de la ventana. K2 mueve los tres
números en la buena dirección, pero el hueco grande (los cambios que no vemos y las posesiones cortas) sigue abierto
con cualquiera de las tres versiones.

## Partido a partido [medido, sin voto]

El reto es un solo partido, así que importa cuántas veces pierde cada versión, no solo la media. Casos (partido y
celda) en que queda por debajo de `main`:

| datos | casos | K2 | K3 | peor caso de K2 | peor caso de K3 |
|---|---|---|---|---|---|
| DFL | 84 | 5 | 2 | −0,026 | −0,007 |
| SkillCorner, entrenamiento | 40 | 5 | 1 | −0,016 | −0,005 |
| Metrica | 12 | 2 | 0 | −0,015 | +0,000 |

Estas tablas se añadieron después de ver el bloque de dentro del proveedor: no entran en ninguna regla.

## Qué significa para la entrega [inferencia, sobre lo medido]

- **K2 y K3 son dos formas de la misma apuesta.** K2 gana más donde funciona (Metrica, el flag, las recuperaciones).
  K3 gana un poco menos y falla menos veces, y fuera del proveedor es la que gana.
- **Lo que David ha encendido es K2,** y nada de lo medido aquí dice que haya que cambiarlo: con la regla escrita antes,
  K3 no queda recomendada por encima de K2. K3 queda como la versión prudente, lista para una entrega de prueba si el
  equipo la quiere mirar.
- **Nada de esto se ha medido en el partido.** Si el equipo quiere ver K3 en él, hace falta una entrega de prueba, que
  ejecuta una persona, con criterios de daño escritos antes de generarla. Lo que cabe esperar está medido
  (`cuanto_cambia_k3.py`): frente a `main` cambia del 2,6 al 3,0 % de los frames en la DFL y del 4,6 al 5,0 % en
  SkillCorner (K2: del 4,4 al 5,3 % y del 7,4 al 7,8 %), con un 2 % menos de posesiones, las mismas paradas y ninguna
  posesión de menos de 12 frames.
- **La decisión es del equipo.** `pipeline.PIECES`, `DELIVERY_LAYERS` y la entrega no cambian.

## Lo que no he podido comprobar

- **Que K3 quite la pérdida de K2 en otro proveedor.** Hace falta un modelo de K2 que pierda. Los del 17/11 están en la
  máquina de la GPU (`conjunto_cache/pesos/solo_dfl_todos.pt` y `solo_sc_todos.pt`); con ellos es un comando.
- **Cuánto baila K2 de un entrenamiento a otro, con precisión.** Hay tres entrenamientos del modelo de solo la DFL; del
  modelo de los dos proveedores, el de la entrega, solo hay uno. Promediar varias semillas de ese pide la GPU.
- **La reproducción en otra máquina.** K3 solo suma dos logits que ya existen, pero no se ha ejecutado fuera de esta.
- **La mezcla que se mide en la DFL no es siempre la de la entrega.** Cada logit va con la α de su pliegue, y en tres
  partidos de la DFL K2 entra con el doble de escala relativa que en la entrega (donde las dos α son 4). En
  SkillCorner y en Metrica sí es la de la entrega. Medido aparte, sin voto, con las α de la entrega en los siete
  pliegues: K3 gana a `main` de +0,034 a +0,056 con control (7 de 7) y de +0,014 a +0,025 con el flag, y frente a K2
  queda de −0,001 a −0,008 con control. **El precio de la mezcla con control no es cero: es de hasta 0,008.**
- **Reproducción bit a bit.** K3 hereda el `np.exp` de los rasgos de B5, que K2 evitaba: una entrega de prueba de K3
  hay que reproducirla en otra máquina, como se hizo con B5 y con K2.
- **Con K2 encendido, `main` cambia de significado.** `refinar.py` y `detalle_abiertos.py` llaman `main` a la entrega
  con B5 y, en SkillCorner y en Metrica, la toman de `pipeline.PIECES`. Se niegan a medir si ahí ya no está B5: si
  esta rama se junta con `feat/encender-k2`, hay que decidir antes qué se llama `main`. Los scripts del estudio de K2
  (`medir.py`, `metrica.py`) tienen el mismo problema, sin candado. Y una entrega de prueba de K3 se compararía con
  `equipo_v10` (`784e65e5…acbc`), no con `equipo_v9`.
- **`possession/aprendida.py` tiene un envoltorio nuevo** (`evidence_k3`). No cambia B5 ni K2 y las pruebas siguen en
  verde, pero antes de que nada de esta rama siga adelante hay que repetir el criterio C0 desde ella: `equipo_v9_rama`
  tiene que salir con `d9706dfb…be63`.

## Ficheros

| fichero | qué es |
|---|---|
| `possession/refinamientos.py` | K3, K4 y K5, apagados |
| `possession/aprendida.py` | el envoltorio `evidence_k3`, para el harness oficial y para `--pieza` |
| `validation/conjunto/refinar.py` | la medida: dentro del proveedor, con otros pesos (`--pesos`) y en Metrica; las tablas descriptivas, con `--solo-por-partido` |
| `validation/conjunto/cuanto_cambia_k3.py` | lo que cabe esperar en una entrega de prueba de K3 |
| `validation/conjunto/detalle_abiertos.py` | el análisis del notebook de David (cambios y posesiones) en los 20 partidos abiertos, para `main`, K2 y K3 |
| `validation/conjunto/entrenar.py` | ahora entrena también en la CPU (`--dispositivo cpu`), con otra semilla (`--semilla`) y con menos columnas |
| `validation/scripts/prueba_refinamientos.py` | pruebas sin datos |
| `validation/harness/versiones/refinamientos_k2_2026-11-17.json` | `main`, K2 y K3 para el harness oficial |
| `validation/conjunto/salidas/2026-11-17_refinar_*`, `…_cuanto_cambia_k3.md`, `…_detalle_abiertos.md`, `…_entrenamiento_replica_solo_dfl.md`, `…_entrenamiento_semilla2_solo_dfl.md` | las salidas agregadas |
