# K3: qué es y qué falta por comprobar (17/11/2026)

Para quien vaya a hacer las comprobaciones. Rama `exp/k2-refinar`. El detalle está en
`validation/resultados/2026-11-17_refinamientos_k2.md` y en `docs/decisiones.md` (entradas del 17/11).

## Qué es K3

- **B5** es la evidencia de equipo de `equipo_v9`: una regresión logística sobre unos 30 resúmenes por frame.
- **K2** es la red que mira a cada jugador. Es la evidencia de equipo de `equipo_v10`, la entrega que encendió David.
- **K3 es la media de las dos.** Cada una da un número por frame (positivo, el local tiene el balón; negativo, el
  visitante). K3 los promedia a partes iguales y lo demás no cambia: el mismo balón muerto, el mismo decodificador y
  las mismas capas del partido.
- **No se ha entrenado nada nuevo.** Usa los pesos de K2 que ya están en el repo y los coeficientes de B5.
- **Está apagada.** El código es `possession/refinamientos.py` y un envoltorio, `aprendida.evidence_k3`. La entrega no
  cambia.

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
- **Con la regla que se escribió antes de medir, K3 no queda recomendada por encima de K2.** Pasa dos de sus tres
  puntos; el tercero no se pudo leer (ver el paso 3).

## Lo que falta por comprobar

### 1. La entrega de prueba en el partido

La hace una persona con los datos del partido y el entorno limpio (`requirements-entrega.txt`). Unos 10 minutos.

    git fetch origin
    git switch --detach origin/exp/k2-refinar
    python -m possession.pipeline --name equipo_v9_rama
    python -m possession.pipeline --name prueba_k2_rama --pieza candidates=aprendida.evidence_k2
    python validation/partido/probar_entrega.py prueba_k3 --pieza candidates=aprendida.evidence_k3 --contra prueba_k2_rama
    python evaluation/validate_submission.py evaluation/results/prueba_k3.csv
    python evaluation/run_evaluation.py

Qué tiene que salir (los criterios están en `docs/decisiones.md`, «K3: la entrega de prueba frente a `equipo_v10`»,
escritos antes de generarla):

| criterio | qué se pide |
|---|---|
| C0 | `equipo_v9_rama` con sha256 `d9706dfb…be63` y `prueba_k2_rama` con `784e65e5…acbc` (el de `equipo_v10`) |
| C1 | `prueba_k3` válida y con 0 frames en conflicto |
| C3 | frente a `prueba_k2_rama` cambia como mucho el 7 % de los frames evaluados; de un equipo al otro, el 3,5 %; entre un equipo y `D`, el 3,5 % |
| C4 | entre 183 y 213 posesiones, entre 108 y 122 paradas y entre el 44,4 y el 47,4 % de `D` |
| C5 | ninguna posesión de menos de 12 frames y como mucho 4 de menos de 25 |
| C6 | en la ventana pública, frente a `equipo_v10`: el macroF1 no baja más de 0,03 ni el spellF1 más de 0,10 |

**Qué se le pega a Claude:** la salida de los comandos tal cual. Solo lleva agregados (huellas, recuentos, porcentajes).
Nunca el CSV ni tablas frame a frame.

### 2. Reproducirla en una segunda máquina

Otra persona repite el comando de `prueba_k3` y compara el sha256. Hace falta solo si el equipo decide entregar con K3:
K3 hereda una exponencial de B5 y, como con B5 y con K2, hay que ver que sale igual en dos máquinas.

### 3. El punto que quedó sin leer de la regla de K3

La regla preguntaba si K3 deja de perder donde K2 pierde. Para eso hace falta el modelo de K2 que perdía: el que se
entrenó el 17/11 solo con la Bundesliga. Sus pesos no están en el repo. Están en el ordenador donde se entrenó K2 (el
de la tarjeta gráfica RTX 3060), en la carpeta de datos abiertos:

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

No bloquea la entrega de prueba.

### 4. Los 5 minutos públicos

Sirven para ver que nada se ha roto (el criterio C6) y para entender qué tipo de errores hacemos
(`notebooks/ventana_publica_detalle.ipynb`, de David). **No sirven para elegir entre K2 y K3:** son 17 posesiones, y
por debajo de 0,42 de diferencia todo es ruido. Para elegir están las medidas de arriba.

## Si el equipo decide entregar con K3

1. `pipeline.PIECES["candidates"]` pasa a `"aprendida.evidence_k3"`.
2. Se regenera la entrega: tiene que salir byte a byte igual que `prueba_k3`.
3. Se reproduce en una segunda máquina.
4. Se cuenta en el documento técnico.

Si no, la entrega sigue siendo la que haya: `equipo_v10` con K2 cuando `feat/encender-k2` entre en `main`.

## Lo que no hay que hacer

- Elegir entre K2 y K3 mirando la ventana pública.
- Subir a git los `.pt`, los CSV de las entregas o cualquier dato.
- Pegarle a Claude nada del partido que no sean agregados.
