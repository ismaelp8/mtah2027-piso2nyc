# K3: qué es y qué falta para entregar con ella (17/11/2026)

**Estado, 17/11 por la tarde:** K3 pasó su entrega de prueba frente a `equipo_v10` e Ismael decidió encenderla. Está
en `main` (merge de `feat/encender-k3`, que junta la rama de David, `feat/encender-k2`, con la de los refinamientos,
`exp/k2-refinar`). **`equipo_v11` ya está generada y validada** desde `main` en `23dcbc1`, en el entorno limpio, con
la huella esperada (`811658cd…c04b`). **Falta reproducirla en otra máquina** (paso 2) **y el documento técnico**
(paso 3). El detalle está en
`validation/resultados/2026-11-17_refinamientos_k2.md` y en `docs/decisiones.md` (entradas del 17/11).

## Qué es K3

- **B5** es la evidencia de equipo de `equipo_v9`: una regresión logística sobre unos 30 resúmenes por frame.
- **K2** es la red que mira a cada jugador. Es la evidencia de equipo de `equipo_v10`, la entrega que encendió David.
- **K3 es la media de las dos.** Cada una da un número por frame (positivo, el local tiene el balón; negativo, el
  visitante). K3 los promedia a partes iguales y lo demás no cambia: el mismo balón muerto, el mismo decodificador y
  las mismas capas del partido.
- **No se ha entrenado nada nuevo.** Usa los pesos de K2 que ya están en el repo y los coeficientes de B5.
- **Está encendida en `main`:** `pipeline.PIECES["candidates"]` es `aprendida.evidence_k3`. El código es
  `possession/refinamientos.py` y ese envoltorio.

## Para qué sirve

K2 gana a B5 donde ha visto partidos de ese proveedor de tracking, pero entrenada con un solo proveedor no gana en
otro, y el partido es de un proveedor que no ha visto. K3 es un seguro: si K2 falla, B5 sigue opinando.

## Lo que ya está medido, en datos abiertos de otros partidos

Ganancia de `spellF1` sobre B5 (`equipo_v9`). Por debajo de ±0,01 es ruido.

| dónde | K2 | K3 |
|---|---|---|
| Bundesliga, 7 partidos, etiquetas de control | +0,036 a +0,051 | +0,032 a +0,054 |
| Bundesliga, etiquetas del flag (cambia en el primer toque) | +0,033 a +0,044 | +0,017 a +0,031 |
| SkillCorner, 10 partidos | +0,021 a +0,024 | +0,017 a +0,023 |
| Metrica, 3 partidos de un proveedor que nadie vio | +0,021 a +0,036 | +0,014 a +0,029 |
| SkillCorner, con K2 entrenada solo con la Bundesliga (dos repeticiones) | −0,007 a +0,003 | +0,005 a +0,011 |
| Metrica, con K2 entrenada solo con SkillCorner | −0,019 a −0,026 | −0,006 a +0,014 |
| veces por debajo de B5, partido a partido | 12 de 136 | 3 de 136 |

- **A favor de K3:** falla menos veces y gana donde K2 no ha visto al proveedor.
- **En contra:** gana menos donde K2 funciona, y es más prudente justo en los cambios de posesión. De los cambios
  directos entre equipos en la Bundesliga, B5 ve el 35 %, K2 el 48 % y K3 el 44 %. En recuperaciones anotadas por
  personas: 70 %, 80 % y 75 %.
- **Con la regla que se escribió antes de medir, K3 no quedaba recomendada por encima de K2:** pasa dos de sus tres
  puntos y el tercero no se pudo leer (ver el paso 4). Encenderla es una decisión del equipo, no de la regla.

## Lo que ya salió en el partido

La entrega de prueba `prueba_k3` (la ejecutó David con la rama `exp/k2-refinar` en `4a67424`; solo agregados) pasa los
criterios escritos antes de generarla:

| criterio | qué ha salido |
|---|---|
| C0 | `equipo_v9_rama` con `d9706dfb…be63` y `prueba_k2_rama` con `784e65e5…acbc` |
| C1 | válida y con 0 frames en conflicto; sha256 `811658cd…c04b` |
| C3 | frente a K2 cambian 4.219 frames (2,7 %): 2.719 de un equipo al otro y 1.500 entre un equipo y `D` |
| C4 | 198 posesiones, 116 paradas y el 45,8 % de `D` |
| C5 | ninguna posesión de menos de 12 frames ni de 25 |
| C6 | en la ventana pública no baja (macroF1 de 0,873 a 0,876 y spellF1 de 0,680 a 0,693, que es ruido) |

**Ojo:** se generó con Python 3.12.10 y numpy 1.26.4, no con el entorno limpio. En ese entorno B5 y K2 dieron sus
huellas de siempre, así que se espera la misma para K3, pero hay que confirmarlo.

## Lo que falta para entregar con K3

### 1. Regenerar la entrega en el entorno limpio

La hace una persona con los datos del partido y el entorno de `requirements-entrega.txt` (Python 3.13 y numpy 2.5.4),
sin cambios locales:

    git fetch origin
    git switch --detach origin/main
    python -m possession.pipeline --name equipo_v11
    python evaluation/validate_submission.py evaluation/results/equipo_v11.csv

Tiene que salir: «sin cambios locales», 0 frames en conflicto, 198 posesiones, 116 paradas y el validador en verde. La
huella esperada es `811658cd…c04b`. Si sale otra, la buena es la del entorno limpio: se apunta y se le dice a Claude.

**Qué se le pega a Claude:** la salida de los comandos tal cual (huella, recuentos, versiones). Nunca el CSV.

### 2. Reproducirla en una segunda máquina

Otra persona repite los mismos comandos y compara el sha256 entero. K3 hereda una exponencial de B5 y, como con B5 y con
K2, hay que ver que sale igual en dos máquinas antes de entregar.

### 3. Contarla en el documento técnico

K2 y K3: los datos de entrenamiento y su origen (los 7 partidos de la Bundesliga de Bassek et al., 2025, CC BY 4.0, y
los 10 de entrenamiento de SkillCorner, MIT), que la entrega usa solo los pesos en numpy, que K3 es la media de la red
y de la regresión, y que es una apuesta con lo que se sabe en contra.

### 4. El punto que quedó sin leer de la regla de K3 (no bloquea)

La regla preguntaba si K3 deja de perder donde K2 pierde. Para eso hace falta el modelo de K2 que perdía: el que se
entrenó el 17/11 solo con la Bundesliga. Sus pesos no están en el repo. Están en el ordenador de casa de Ismael (el de
la tarjeta gráfica RTX 3060), en la carpeta de datos abiertos:

    <datos abiertos>/conjunto_cache/pesos/solo_dfl_todos.pt
    <datos abiertos>/conjunto_cache/pesos/solo_sc_todos.pt

`<datos abiertos>` es `MTAH_OPEN_DATA_DIR` o, si no está definida, `mtah2027-datos-abiertos` en la carpeta personal.
Son dos ficheros de unos 150 KB con pesos de un modelo entrenado con datos abiertos: no llevan nada del partido. No se
suben a git. Dos maneras:

- **Copiarlos** (USB, Drive o como sea) a la misma ruta del ordenador donde se vaya a medir.
- **O medir en ese mismo ordenador,** con esta rama y el entorno del harness, y pegar la salida:

      cd validation/conjunto
      python juntar.py --etiqueta solo_dfl --pliegues todos --destino <datos abiertos>/conjunto_cache/pesos_solo_dfl.npz --alfa 4
      cd ../..
      python validation/conjunto/refinar.py --dominio sc --pesos <datos abiertos>/conjunto_cache/pesos_solo_dfl.npz --entrenado-con dfl

  K3 «quita la pérdida» si queda en −0,005 o más frente a `main` en las cuatro celdas. Es datos abiertos: la salida se
  puede pegar entera.

### Los 5 minutos públicos

Sirven para ver que nada se ha roto y para entender qué tipo de errores hacemos. **No sirven para elegir entre K2 y
K3:** son 17 posesiones, y por debajo de 0,42 de diferencia todo es ruido.

## Si hay que volver atrás

- **A K2:** `python -m possession.pipeline --name equipo_v10 --pieza candidates=aprendida.evidence_k2` tiene que dar
  `784e65e5…acbc`, la huella de `equipo_v10`, reproducida en dos máquinas.
- **A B5:** lo mismo con `--pieza candidates=aprendida.evidence_b5` y la huella de `equipo_v9`, `d9706dfb…be63`.

Para dejarlo fijo, `pipeline.PIECES["candidates"]` vuelve a esa pieza en un commit, con las comprobaciones de las
pruebas que la nombran (`docs/decisiones.md`, «se enciende K3»).

## Lo que no hay que hacer

- Elegir entre K2 y K3 mirando la ventana pública.
- Subir a git los `.pt`, los CSV de las entregas o cualquier dato.
- Pegarle a Claude nada del partido que no sean agregados.
- Tocar `possession/` después de regenerar: cuenta como código de la entrega y obligaría a regenerar otra vez.
