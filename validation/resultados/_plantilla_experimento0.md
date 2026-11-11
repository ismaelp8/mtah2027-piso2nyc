# Experimento 0 · AAAA-MM-DD · <quién>

> Copia este fichero a `AAAA-MM-DD_experimento0.md` y rellénalo. Los pasos están en
> `validation/PASOS.md` (paso 2). Solo agregados.

- **Código:** rama y commit de `validation/experimento0/`.
- **Datos:** Bundesliga (Bassek et al., 2025), figshare 10.6084/m9.figshare.28196177.v1, 7 partidos.
- **Comandos:**
- **kloppy:** versión.

## Comprobaciones de lectura (D8, D9)

| partido | local en `teams[0]` | valores de `ball_state` | saltos de `frame_id` dentro de las partes |
|---|---|---|---|
| J03WMX | | | |
| J03WN1 | | | |
| J03WPY | | | |
| J03WOH | | | |
| J03WQQ | | | |
| J03WOY | | | |
| J03WR9 | | | |

## 2a. Descripción por partido (D5)

| partido | frames | % D | paradas | posesiones | posesiones por minuto vivo | mediana (s) | p10 (s) | p90 (s) | < 1 s | < 2 s | < 3 s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J03WMX | | | | | | | | | | | |
| … | | | | | | | | | | | |
| los 7 juntos | | | | | | | | | | | |

## 2b. Huella de retrasos (solo informativa, D21: no decide nada)

| | 1 | 3 | 8 | 25 |
|---|---|---|---|---|
| oficial (`EVALUATION.md`) | 1,0000 | 0,9818 | 0,8933 | 0,6539 |
| DFL, los 7 juntos | | | | |
| DFL, partido con la huella más baja | | | | |
| DFL, partido con la huella más alta | | | | |

Comparación entre fuentes abiertas (flags DFL, eventos DFL, eventos Barça):

## 2c. Cambios H↔A (D3, D4, D7)

| medida | p10 | mediana | p90 |
|---|---|---|---|
| distancia del balón al jugador más cercano del equipo nuevo (m) | | | |
| distancia del balón al jugador más cercano del equipo antiguo (m) | | | |
| desfase del cambio respecto al toque del equipo nuevo (frames, negativo = antes) | | | |

Fracción de cambios con un jugador del equipo nuevo a menos de 1,5 m en ±1 s:
Umbrales usados para "toque":

## 2d. Paso a inactivo (D5, D6)

| medida | valor |
|---|---|
| % de pasos a inactivo con el balón fuera del campo | |
| desfase desde que el balón cruza la línea (frames, mediana y p90) | |
| duración de la parada por tipo aproximado (mediana, s): banda / fondo / dentro del campo | |

## 2e. Paso a activo (D6)

| medida | valor |
|---|---|
| desfase entre el flag y el balón en movimiento (frames, mediana y p90) | |
| % de paradas en las que el equipo del flag durante la parada es el que reanuda | |

## 2f. Opcional: eventos frente a flags (D11)

| | 1 | 3 | 8 | 25 |
|---|---|---|---|---|
| huella de las etiquetas de eventos de la DFL | | | | |

`spellF1` de eventos contra flags:

## Dudas resueltas

| id | respuesta |
|---|---|
| | |

## Conclusión y decisión

- ¿La Bundesliga vale como proxy principal? (según 2a, 2c, 2d y 2e frente a `CHALLENGE.md`, no según la huella)
- ¿Cuándo debe cambiar nuestra etiqueta de equipo y cuándo empieza y acaba un `D`?
- ¿Qué cambia en el plan?
