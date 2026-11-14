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
da la salida completa.

## Qué mide

| | |
|---|---|
| **etiquetas** | dos convenciones: `flag` (el de la DFL tal cual, que cambia en el primer toque del rival) y `control` (corregido con "C0-12 o dos toques", experimento 1). La de la GT del reto sigue sin medir |
| **balón** | tres condiciones: `limpio`, `huecos` (falta en el 41 % de los frames de juego) y `huecos y suavizado` (además, media móvil de 25 frames). En las tres se tapa el balón en los `D` y en sus bordes |
| **control** | el baseline oficial: jugador más cercano y voto por mayoría de ±50 frames |
| **`D`** | copiado de las etiquetas para todas las versiones, el control incluido (`D` oráculo) |
| **métrica** | `spellF1` oficial con los 7 partidos juntos y por partido, y la diferencia con el control con un intervalo por bootstrap pareado sobre las posesiones |

## Cómo se lee

Un candidato gana (`docs/investigacion_metodos.md` §5.8) si:

- gana al control en 6 de los 7 partidos o más;
- la diferencia es de 0,03 o más y su intervalo no incluye el cero;
- todo eso se mantiene en las tres condiciones del balón **y** con las dos convenciones.

Si no, es un empate y entra la versión más simple. La última sección de la salida aplica esta regla.

La fila «coste elegido dejando un partido fuera» elige, para cada partido, la versión que más saca en los
otros seis y la puntúa en ese. Es el número honesto de un parámetro ajustado.

## Cómo se prueba una versión nueva

1. Cambia tu pieza en `possession/` (o añade un parámetro).
2. Añade una entrada a `VERSIONES` en `puntuar.py`. Las de tipo `pipeline` llaman a
   `possession.pipeline.run` con los `params` del decodificador.
3. Ejecuta el harness y pega la tabla, con el control al lado, en tu PR.

Escribe antes en `docs/decisiones.md` qué candidatos vas a comparar. Dos o tres, no veinte: con muchas
variantes gana el azar.

## Límites

- **Las etiquetas `control` favorecen a los métodos de proximidad.** Salen del flag filtrado con una regla
  de proximidad sobre el tracking limpio (el más cercano a 1 m durante 12 frames, o dos toques). Un
  candidato que use retención por proximidad se parece a esa regla y ganará con ellas por construcción.
  Por eso la regla exige ganar también con `flag`, que es el mismo tipo de etiqueta que la GT del reto.
  La referencia sin circularidad son los eventos humanos de la DFL (experimento 1), que el harness aún no
  usa.
- **El `D` no se puede validar aquí con el balón.** La DFL congela el balón mientras está muerto, así que
  hay que taparlo, y entonces «no hay balón» casi equivale a «`D`». En el ATD no pasa. Por eso el `D` va
  copiado de las etiquetas. Con `--d propio` cada versión pone el suyo, pero ese número no decide nada.
- **La degradación es provisional.** Falta comprobarla contra la medida del balón del ATD en todo el
  partido. Hasta entonces, el orden entre evidencias de equipo no se da por bueno.
- **Los jugadores no se degradan:** están todos, sin ruido. Los slots sí se barajan, para que nada dependa
  de que un slot sea una persona.
- **No hay Smart Tagging en la DFL.** Lo que lo usa (`possession/dead_ball.py`) no se mide aquí.

## Ficheros

| fichero | qué hace |
|---|---|
| `dfl.py` | carga un partido de la caché, calcula sus etiquetas con las dos convenciones, degrada el balón y lo pasa al formato de `possession/tracking.py` |
| `puntuar.py` | ejecuta cada versión, la puntúa y aplica la regla |
