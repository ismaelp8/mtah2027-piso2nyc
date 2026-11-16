# La medida del 15/11 en los 10 partidos de `lector.ENTRENAMIENTO` (referencia del instrumento)

Salida de `validation/skillcorner/medir.py` con el código de `3b227c4` (el de `validation/resultados/2026-11-15_skillcorner.md`),
ejecutado el 16/11 en una copia de ese commit (`git archive 3b227c4`), con:

    python validation/skillcorner/medir.py --partidos 1874553 1899585 1927964 1959846 1996435 2006229 2007448 2010085 2013725 2016236 --bootstrap 0

Las filas de `main (B5, coste 25)` en «detectado» y «detectado, suavizado» son las que tiene que repetir
`medir_skillcorner.py --detector ninguno` (`2026-11-16_skillcorner_instrumento.md`). Las líneas de progreso, que van a
stderr, no se copian.

**Las tres líneas de la regla del final no son un veredicto.** Con `--bootstrap 0` no hay intervalo, y esa regla
(BITACORA.md §6) pide que el intervalo quede por encima de cero, así que salen «no» por construcción. La regla se leyó
el 15/11 con los 20 partidos y el bootstrap.

```text
partidos: 10 · bootstrap: 0 · código: pipeline de main, B5 y dead_state con los coeficientes de la entrega

### Las etiquetas (convención de SkillCorner)

- posesiones: 3228 · 6.05 por minuto vivo · frames `D`: 45.6 % · frames de las partes sin etiqueta: 0.04 %
- huella de retrasos 1 / 3 / 8 / 25 frames: 0.9968 / 0.9769 / 0.8878 / 0.6729
  (DFL flag 0,5522 · oficial 0,6539 · DFL control 0,8082 a 25 frames; descriptivo)

| condición | ¿vota? | balón visible en los frames vivos | balón visible en los `D` |
|---|---|---|---|
| detectado | sí | 92.8 % | 21.1 % |
| detectado, suavizado | sí | 92.8 % | 21.1 % |
| con el estimado | no | 98.3 % | 45.8 % |
| solo jugadores detectados | no | 92.8 % | 21.1 % |

### `D` oraculo (decide)

| balón y jugadores | versión | spellF1, 10 partidos | por partido, mín–máx | frente al control [5–95 %] · gana en | frente a N1 [5–95 %] · gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| detectado | control: voto ±50 | 0.395 | 0.358–0.470 | – | -0.071 · 0 de 10 | 3942 / 3228 |
| detectado | N1, coste 25 | 0.466 | 0.422–0.506 | +0.071 · 10 de 10 | – | 2556 / 3228 |
| detectado | main (B5, coste 25) | 0.519 | 0.451–0.574 | +0.124 · 10 de 10 | +0.053 · 9 de 10 | 2270 / 3228 |
| detectado, suavizado | control: voto ±50 | 0.388 | 0.350–0.450 | – | -0.064 · 0 de 10 | 4111 / 3228 |
| detectado, suavizado | N1, coste 25 | 0.453 | 0.410–0.504 | +0.064 · 10 de 10 | – | 2653 / 3228 |
| detectado, suavizado | main (B5, coste 25) | 0.514 | 0.444–0.566 | +0.126 · 10 de 10 | +0.062 · 9 de 10 | 2284 / 3228 |
| con el estimado (sin voto) | control: voto ±50 | 0.403 | 0.362–0.465 | – | -0.048 · 0 de 10 | 3822 / 3228 |
| con el estimado (sin voto) | N1, coste 25 | 0.451 | 0.399–0.501 | +0.048 · 10 de 10 | – | 2696 / 3228 |
| con el estimado (sin voto) | main (B5, coste 25) | 0.522 | 0.461–0.583 | +0.119 · 10 de 10 | +0.071 · 10 de 10 | 2286 / 3228 |
| solo jugadores detectados (sin voto) | control: voto ±50 | 0.396 | 0.355–0.464 | – | -0.067 · 0 de 10 | 4016 / 3228 |
| solo jugadores detectados (sin voto) | N1, coste 25 | 0.463 | 0.419–0.508 | +0.067 · 10 de 10 | – | 2589 / 3228 |
| solo jugadores detectados (sin voto) | main (B5, coste 25) | 0.494 | 0.438–0.539 | +0.097 · 10 de 10 | +0.030 · 8 de 10 | 2569 / 3228 |

### `D` propio (descriptivo)

| balón y jugadores | versión | spellF1, 10 partidos | por partido, mín–máx | frente al control [5–95 %] · gana en | frente a N1 [5–95 %] · gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| detectado | control: voto ±50 | 0.258 | 0.234–0.327 | – | -0.083 · 0 de 10 | 4862 / 3228 |
| detectado | N1, coste 25 | 0.342 | 0.314–0.380 | +0.083 · 10 de 10 | – | 2712 / 3228 |
| detectado | main (B5, coste 25) | 0.382 | 0.346–0.432 | +0.123 · 10 de 10 | +0.040 · 10 de 10 | 2342 / 3228 |
| detectado, suavizado | control: voto ±50 | 0.258 | 0.236–0.317 | – | -0.076 · 0 de 10 | 4920 / 3228 |
| detectado, suavizado | N1, coste 25 | 0.334 | 0.301–0.380 | +0.076 · 10 de 10 | – | 2795 / 3228 |
| detectado, suavizado | main (B5, coste 25) | 0.378 | 0.345–0.427 | +0.120 · 10 de 10 | +0.044 · 9 de 10 | 2345 / 3228 |
| con el estimado (sin voto) | control: voto ±50 | 0.255 | 0.225–0.322 | – | -0.075 · 0 de 10 | 4262 / 3228 |
| con el estimado (sin voto) | N1, coste 25 | 0.330 | 0.302–0.370 | +0.075 · 10 de 10 | – | 2868 / 3228 |
| con el estimado (sin voto) | main (B5, coste 25) | 0.380 | 0.348–0.424 | +0.125 · 10 de 10 | +0.051 · 10 de 10 | 2355 / 3228 |
| solo jugadores detectados (sin voto) | control: voto ±50 | 0.259 | 0.230–0.327 | – | -0.056 · 0 de 10 | 5007 / 3228 |
| solo jugadores detectados (sin voto) | N1, coste 25 | 0.315 | 0.275–0.358 | +0.056 · 10 de 10 | – | 2626 / 3228 |
| solo jugadores detectados (sin voto) | main (B5, coste 25) | 0.352 | 0.301–0.391 | +0.093 · 10 de 10 | +0.037 · 9 de 10 | 2624 / 3228 |

### Regla de BITACORA.md §6 (`D` oráculo, condiciones que votan: detectado, detectado, suavizado)

- «B5 aguanta con tracking automático» (main frente al control): **no**
- «La ventaja de B5 sobre N1 aguanta» (main frente a N1): **no**
- (descriptivo) N1 frente al control: **no**
  Gana: +0.03 o más con los partidos juntos, en 8 de 10 o más y con el intervalo por encima de cero, en las dos condiciones que votan.
```
