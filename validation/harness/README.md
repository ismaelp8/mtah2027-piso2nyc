# Harness de la DFL

**Qué es:** el banco de pruebas del pipeline. Ejecuta las mismas piezas de `possession/` que se ejecutan
con el partido, pero sobre los 7 partidos abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0), que
sí tienen etiquetas por frame, y las puntúa con el scorer oficial. Con él se decide qué versión de cada
pieza entra en la entrega, sin tocar el partido ni la ventana pública.

Son datos abiertos de otros partidos: lo puede ejecutar cualquiera, Claude incluido. Solo imprime
agregados.

## Cómo se ejecuta

Hace falta la caché de la DFL (pasos 1 y 2 de [`../PASOS.md`](../PASOS.md)):

```bash
python validation/scripts/descargar_datos_abiertos.py dfl
```

```bash
python validation/experimento0/dfl_lector.py J03WMX
```

El lector se ejecuta una vez por partido (`J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ` y
`J03WR9`) y necesita `lxml`. Después:

```bash
python validation/harness/puntuar.py
```

Tarda medio minuto con los 7 partidos. Con `--partidos J03WMX` mide uno solo, para probar; con `--json`
da la salida completa; con `--versiones fichero.json`, puntúa las versiones de ese fichero (ver «Cómo
se prueba una versión nueva»).

## Qué mide

| | |
|---|---|
| **etiquetas** | dos convenciones: `flag` (el de la DFL tal cual, que cambia en el primer toque del rival) y `control` (corregido con "C0-12 o dos toques", experimento 1). La de la GT del reto sigue sin medir |
| **balón** | desde el 14/11, calibrado con el perfil del ATD (`validation/resultados/2026-11-14_harness_como_el_atd.md`). **Votan** «como el ATD» (microcortes de hasta 0,5 s, el 11,3 % del juego en bloques de 5 a 15 s y el balón suavizado con una media móvil de 25 frames) y «como el ATD, sin bloques». **Sin voto:** `limpio` y «huecos y suavizado» (la de antes, con el 41 % del juego tapado en bloques de 1 s). En todas se tapa el balón en los `D` y en sus bordes |
| **control** | el baseline oficial: jugador más cercano y voto por mayoría de ±50 frames |
| **`D`** | copiado de las etiquetas para todas las versiones, el control incluido (`D` oráculo) |
| **métrica** | `spellF1` oficial con los 7 partidos juntos y por partido, y la diferencia con el control con un intervalo por bootstrap pareado sobre las posesiones |

## Cómo se lee

Un candidato gana (`docs/investigacion_metodos.md` §5.8) si:

- gana al control en 6 de los 7 partidos o más;
- la diferencia es de 0,03 o más y su intervalo no incluye el cero;
- todo eso se mantiene en las condiciones del balón que votan **y** con las dos convenciones.

Si no, es un empate y entra la versión más simple. La sección «Regla de §5.8» de la salida aplica esta
regla frente al control.

**Frente a lo que ya hay en `main`:** la sección «Frente a la versión de main» aplica la misma regla
frente a la versión de `main` (`{}` en el fichero de versiones). Para sustituir a lo de `main`, un
candidato tiene que ganar al control **y** ganar a `main`. Si empata con `main`, se queda lo de `main`,
que es lo más simple. Es la regla del empate de arriba aplicada a `main`. Decidido por Ismael el 14/11
(`docs/decisiones.md`).

La fila «coste elegido dejando un partido fuera» elige, para cada partido, la versión que más saca en los
otros seis y la puntúa en ese. Es el número honesto de un parámetro ajustado.

## Cómo se prueba una versión nueva

Sin tocar `puntuar.py`: las versiones van en un fichero JSON y se pasan con `--versiones`.

1. **Escribe tu variante en tu pieza** (`possession/`), como otra función del mismo módulo y con la misma
   firma, o como una opción con valor por defecto de la que ya hay. Lo que va en la entrega no cambia
   hasta que cambies la función de siempre.
2. **Escribe las versiones en un JSON**, en `validation/harness/versiones/` y con un nombre tuyo (por
   ejemplo, `candidatos_2026-11-15.json`). Hazlo antes de medir: es la lista de candidatos de
   `docs/decisiones.md`. Dos o tres, no veinte: con muchas variantes gana el azar.
3. **Ejecuta el harness con ese fichero:**

   ```bash
   python validation/harness/puntuar.py --versiones validation/harness/versiones/candidatos_2026-11-15.json
   ```

4. **Sube el JSON en tu PR con la tabla.** La salida empieza por el fichero, su huella, el commit del
   código (y si había cambios sin commit) y cada versión, así que quien revisa puede repetirla en tu rama.
   La huella es el sha256 del contenido sin espacios: no cambia con los saltos de línea de Windows, el BOM
   ni el sangrado. Identifica el fichero, no el código: por eso va también el commit.

**El fichero.** Cada clave es el nombre de una versión, como saldrá en la tabla. El control (el baseline
oficial) va siempre delante y no hace falta escribirlo. **Incluye la versión de `main` (`{}`):** el
harness compara cada candidato con ella (sección «Frente a la versión de main» de la salida), con la
misma regla de §5.8 que frente al control. Eso es lo que decide entre tu candidato y lo que ya hay.

```json
{
  "N1 (main)": {},
  "N2, radio 2 m": {
    "nota": "el más cercano solo opina a menos de 2 m y con el rival a más de 1 m",
    "piezas": {"candidates": {"funcion": "evidence_n2", "opciones": {"radio": 2.0}}}
  },
  "Viterbi, coste 40": {"params": {"switch": 40, "to_dead": 40, "from_dead": 40}}
}
```

`evidence_n2` es inventada: para usarla tendría que existir en `possession/candidates.py`. Si tu variante
es una opción de la función de siempre, basta con las opciones: `{"candidates": {"opciones": {"radio":
2.0}}}`.

| clave | qué es |
|---|---|
| `params` | los parámetros del decodificador que use la versión (con el de siempre, las claves de `temporal.DEFAULTS`). Sin ella, los de por defecto |
| `piezas` | qué función usa cada pieza en lugar de la de siempre. Las piezas: `ball` (en lugar de `clean`), `candidates` y `dead_state` (en lugar de `evidence`) y `temporal` (en lugar de `decode`). La función tiene que estar en ese módulo de `possession/`. Vale su nombre (`"evidence_n2"`) o `{"funcion": ..., "opciones": {...}}`; sin `funcion`, la de siempre. Las opciones se le pasan como argumentos con nombre |
| `nota` | texto libre: qué es y por qué. Sale en la cabecera |
| `tipo` | `pipeline` (por defecto) o `control`. Un `control` es el baseline con otra ventana (`"ventana": 125`) |

**Una pieza aprendida, dejando un partido fuera** (decisión de Ismael del 14/11, para la apuesta B). Dos
añadidos a `piezas`:

- **`"modulo.funcion"`:** la función sale de otro módulo de `possession/` en lugar del de la pieza. Solo los
  que admite `OTROS_MODULOS` en `puntuar.py`: hoy, `aprendida` para la pieza `candidates`. Así la apuesta B
  vive en `possession/aprendida.py` sin tocar `candidates.py`.
- **`"dejar_fuera": true`:** al puntuar cada partido de la DFL, el harness le pasa a la función
  `fuera=<partido>`, y la función usa los coeficientes que se entrenaron sin ese partido. Sin él, un modelo
  entrenado con los 7 se puntuaría sobre partidos que ya vio, contra §5.8. Fuera del harness (la entrega),
  `fuera` vale `None`: los coeficientes de los 7. Al leer el fichero, la versión se prueba con `None` y con
  cada partido, así que un pliegue que falta da error antes de medir.

```json
{
  "main: N1 y coste 25": {},
  "B1: proximidad aprendida": {
    "piezas": {"candidates": {"funcion": "aprendida.evidence_b1", "dejar_fuera": true}}
  }
}
```

`validation/harness/versiones/apuesta_b.json` es el fichero de la apuesta B, y
`validation/apuesta_b/entrenar.py` escribe los coeficientes de cada pliegue en el módulo.

**Lo que da error a propósito:**
- una función que acepta `fuera` sin `"dejar_fuera": true`, porque se puntuaría con los coeficientes de los
  7 partidos, sobre partidos que ya vio;
- puntuar una versión que deja fuera el partido sin decir cuál.

**Ojo con la fila «elegida dejando un partido fuera»** cuando hay versiones con `dejar_fuera`: no está
anidada del todo. Para elegir la versión de un partido mira lo que sacan las versiones en los otros seis, y
cada uno se puntuó con un pliegue que sí vio el primero. La regla de §5.8 no usa esa fila.

**Las erratas dan error al leer el fichero, antes de cargar ningún partido:** una clave desconocida, una
pieza o una función que no existe, una opción que la función no acepta, `NaN` o `Infinity`, o un nombre
de fila del propio harness. Además, cada versión se ejecuta entera sobre un partido inventado de un
minuto: así fallan también unos `params` que el decodificador no admite, una función que no es una pieza
(no devuelve lo que pide la interfaz) y una pieza que escribe en el tracking. **El tracking es de solo
lectura:** todas las versiones reciben el mismo, así que una pieza tiene que devolver una copia
(`trk._replace(bx=...)`) en vez de cambiarlo. `validation/harness/versiones/ejemplo.json` es un fichero
completo:

```bash
python validation/harness/puntuar.py --versiones validation/harness/versiones/ejemplo.json
```

Su última versión escribe las funciones de siempre una a una, así que tiene que dar lo mismo que la
primera. Comprobado (14/11): con el ejemplo, las versiones que también están en `VERSIONES` dan los mismos
números en las 24 celdas. Sin `--versiones` salen los mismos números que antes del cambio. La salida
solo añade la sección frente a la versión de `main`.

**Con `--versiones`, la fila «dejando un partido fuera»** se llama «elegida dejando un partido fuera» y
elige entre las versiones del pipeline de tu fichero.

**La pieza de `D` de estado (`dead_state`) no se mide así hoy.** Con `--d oraculo`, que es lo que se usa
por defecto, el `D` sale de las etiquetas: una variante de `dead_state` no cambia nada, y si su `allowed`
contradice las etiquetas, el pipeline da error («las piezas se contradicen»). Con `--d propio` cada versión
pone su `D`, pero ese número no decide nada: el balón tapado en los `D` de la DFL delata la etiqueta. El
modo con el equipo copiado de las etiquetas que promete el plan (§4) todavía no existe. Mientras tanto,
el `D` se mide con sus propios scripts y su criterio del 13/11.

**Sin `--versiones`** se puntúan las de `VERSIONES` en `puntuar.py`: el decodificador con cuatro costes.
Es la tabla de referencia (`validation/resultados/2026-11-14_harness_dfl.md`).

`python validation/scripts/prueba_harness.py` prueba la lectura del fichero sin cargar ningún partido.

## Eventos humanos (`--eventos`): la referencia sin circularidad

**Por qué.** Las etiquetas `control` salen de una regla de proximidad, y una versión que se le parezca gana
con ellas por construcción. Los eventos los anota una persona en la DFL, no nuestras reglas. Para
situarlos en el tiempo sí se usa el tracking limpio: el jugador del evento a 1,5 m o menos del balón. Con
`--eventos`, el harness mira además la etiqueta de cada versión en esos eventos, con las guardas y los
retardos del experimento 1 (`eventos.py`):

| punto | etiqueta que se espera | cuántos (7 partidos) |
|---|---|---|
| pase completado | equipo del pasador, 5 frames después de la recepción | 3.142 |
| recuperación | equipo que recupera, 12 frames (0,5 s) después | 195 |
| duelo con cambio (`PossessionChange` = true) | el que gana el duelo, 2 s después | 229 |
| duelo sin cambio (`PossessionChange` = false) | el que tenía el balón, 2 s después | 211 |

**Comprobación del instrumento [medido, 14/11].** Con las etiquetas del harness como si fueran una
predicción salen los recuentos y los porcentajes del experimento 1: 97,9 / 89,2 / 88,6 / 47,4 con el flag y
98,8 / 87,7 / 84,3 / 74,9 con la corrección. Esas dos filas salen siempre en la tabla: si cambian, algo
se ha roto.

**Regla de lectura,** escrita el 14/11 antes de puntuar ninguna versión con ella:

- **Qué se mide:** el % de aciertos por tipo de punto, con los 7 partidos juntos, una tabla por condición
  del balón. No hay una por convención: los eventos no dependen de ella. Con el `D` oráculo nunca hay
  `D` en estos puntos, porque todos caen con el balón en juego.
- **Diferencias:** frente al control y frente a la versión de `main` (la primera del pipeline sin
  `params` ni `piezas`, como `{}`). Bootstrap pareado sobre los puntos de cada tipo, 1.000 remuestreos,
  semilla fija, intervalo del 5 al 95 %.
- **Qué se lee:** las recuperaciones y los duelos con cambio (¿cambia cuando debe?) junto con los duelos
  sin cambio (¿se queda cuando debe?). No cambiar nunca gana en los segundos y cambiar siempre, en los
  primeros: por eso se leen siempre juntos. Los pases se enseñan pero no se leen: caen casi siempre dentro
  de posesiones largas (experimento 1).
- **Veredicto en cada condición,** con los intervalos de esos tres tipos:
  - **mejora:** al menos uno queda entero por encima de cero y ninguno entero por debajo;
  - **empeora:** al revés;
  - **compromiso:** uno por encima y otro por debajo;
  - **no concluye:** ninguno se separa de cero.
- **Veredicto de la versión:** el mismo en las condiciones del balón que votan, o «depende del balón».
  Cuando se escribió eran tres; desde el 14/11 votan dos (`dfl.VOTAN`).
- **Es descriptivo.** No entra en la regla de §5.8 ni cambia su veredicto. Si puede vetar a un candidato
  lo decide Ismael. Razones:
  - el significado oficial de `PossessionChange` está [sin verificar];
  - la selección de los duelos usa el flag (quién tenía el balón 10 frames antes);
  - (añadida tras la revisión del 14/11, sin cambiar la regla) los puntos se sitúan en el frame en que el
    jugador del evento está más cerca del balón limpio, a 1,5 m o menos. Eso puede favorecer a la
    evidencia por proximidad [inferencia];
  - el bootstrap remuestrea puntos sueltos, aunque se agrupan por partido y por posesión. Con intervalos
    del 90 % y tres tipos, salir de «no concluye» por azar no es raro.
- **Complementa al `spellF1`, no lo sustituye.** Mide aciertos en puntos sueltos, así que no ve la
  fragmentación: una versión que parpadea puede acertar en todos los puntos.

Hace falta el XML de eventos de cada partido, que baja `descargar_datos_abiertos.py dfl`. Sin él,
`--eventos` da error y el resto del harness funciona igual.

## Límites

- **Las etiquetas `control` favorecen a los métodos de proximidad.** Salen del flag filtrado con una regla
  de proximidad sobre el tracking limpio (el más cercano a 1 m durante 12 frames, o dos toques). Un
  candidato que use retención por proximidad se parece a esa regla y ganará con ellas por construcción.
  Por eso la regla exige ganar también con `flag`, que es el mismo tipo de etiqueta que la GT del reto.
  La referencia sin circularidad son los eventos humanos de la DFL (experimento 1), que el harness mira
  con `--eventos`, de momento solo como descripción (sección «Eventos humanos»).
- **El `D` no se puede validar aquí con el balón.** La DFL congela el balón mientras está muerto, así que
  hay que taparlo, y entonces «no hay balón» casi equivale a «`D`». En el ATD quizá pase bastante
  (`validation/resultados/2026-11-14_perfil_atd.md`, inferencia), pero no se puede medir. Por eso el `D` va
  copiado de las etiquetas. Con `--d propio` cada versión pone el suyo, pero ese número no decide nada.
- **La degradación imita al ATD en lo que se pudo medir sin etiquetas:** los huecos, el suavizado y la
  proximidad (14/11). No se sabe si los huecos largos del ATD caen en juego o en paradas, y por eso votan
  dos condiciones. La DFL ve más disputas que el ATD (20 % frente a 14,5 %).
- **Los jugadores no se degradan:** están todos, sin ruido. Los slots sí se barajan, para que nada dependa
  de que un slot sea una persona.
- **No hay Smart Tagging en la DFL.** Lo que lo usa (`possession/dead_ball.py`) no se mide aquí.

## Ficheros

| fichero | qué hace |
|---|---|
| `dfl.py` | carga un partido de la caché, calcula sus etiquetas con las dos convenciones, degrada el balón y lo pasa al formato de `possession/tracking.py` |
| `puntuar.py` | ejecuta cada versión, la puntúa y aplica la regla |
| `versiones/` | los ficheros de versiones de `--versiones`; `ejemplo.json` es el de muestra y `apuesta_b.json`, el de la apuesta B |
