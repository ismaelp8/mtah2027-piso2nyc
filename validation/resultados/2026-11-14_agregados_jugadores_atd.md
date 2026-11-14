# ¿Se traslada al ATD el estado de `D` con jugadores? · 2026-11-14 · Ismael (ejecución local), con Claude

- **Datos:** el ATD del partido, solo agregados de los frames evaluados; y los 7 partidos abiertos de la
  Bundesliga (Bassek et al., 2025, CC BY 4.0) como referencia.
- **Comandos:**
  - `python validation/partido/agregados_jugadores.py`, que lee el partido: lo ejecutó Ismael;
  - `python validation/scripts/d_estado/traslado_atd.py`, la referencia de la DFL: lo puede ejecutar Claude.
- **Para qué:** el modelo de `possession/dead_state.py` (E2) se entrena con los jugadores de la DFL, que
  están revisados. Los del ATD son automáticos. Antes de dejarlo por defecto había que saber si se mueven
  igual: en [`2026-11-14_d_estado.md`](2026-11-14_d_estado.md) quedó como «sin verificar».

**Lectura en tres líneas:**

1. **Se traslada** [medido, con una regla fijada antes de ejecutar]: se cumplen las cinco condiciones. Los
   jugadores del ATD se mueven como los de la DFL sin temblor añadido.
2. **Que falten jugadores no rompe la pieza** [medido en la DFL]: con 20 vistos de 22 detecta las mismas
   paradas (86 %), y con 18 sigue por encima de no opinar.
3. **No dice que el `D` acierte en este partido:** eso no se puede medir. Donde peor verá el estado es
   antes de los saques de banda y de puerta, en los que la velocidad media de los jugadores no baja
   [observación].

## La regla, fijada antes de ejecutar

Los umbrales los puso la revisión de la PR 5, a partir de la referencia por partido de abajo y de la tabla
de temblor de `2026-11-14_d_estado.md`. Se escribieron en la conversación de revisión antes de que Ismael
ejecutara el script; no estaban en el repo. Los márgenes son un criterio de la revisión, no una medida.

| medida (frames evaluados) | se traslada si | partido | DFL, por partido |
|---|---|---|---|
| frames con la velocidad media en 2 s por debajo de 1,2 m/s | entre el 20 y el 45 % | 35,4 % | 27,0–38,1 % |
| velocidad media en 2 s, p10 | 0,95 m/s o menos | 0,70 | 0,62–0,76 |
| frames con algún jugador fuera del campo (más de 0,3 m) | 20 % o menos | 11,0 % | 12,6–17,7 % |
| frames con tres o más fuera | 2 % o menos | 0,7 % | 0,0–1,2 % |
| slots vistos por frame, mediana | 18 o más | 22 | 21–22 |

- **Por qué esos umbrales:**
  - con un temblor de 0,05 m en los jugadores, la DFL da el 23,9 % por debajo de 1,2 m/s y un p10 de 0,94,
    y la pieza sigue viendo casi todo el `D`; con 0,1 m da el 1,4 % y un p10 de 1,35, y ve bastante menos;
  - por arriba, el 45 % queda fuera de lo que da ningún partido de la DFL: ahí no se sabría si hay más
    paradas o si los jugadores van más lentos;
  - cada jugador fuera del campo suma 3,3 a la puntuación de `D`. En la DFL eso pasa en el 2 % de los
    frames con el balón en juego y en el 30 % de los `D`;
  - que falten jugadores se probó hasta una mediana de 18 vistos.
- **Si se cumplen las cinco,** el modelo puede ir por defecto. Si no, la pieza se queda sin opinar y se
  decide si se entrena una variante, escrita antes de medirla.
- **Lo que la regla no cubre:** los rasgos de forma de los equipos (la distancia entre centroides, la
  dispersión, cada equipo en su mitad y los jugadores en un área). Con una forma rara pesan mucho: en el
  partido inventado de `prueba_pipeline.py`, con 5 jugadores por equipo colocados al azar, el modelo da
  todo el tramo por `D`. La única comprobación de eso en el partido es la entrega regenerada: sus
  recuentos de `D` y de paradas, y la ventana pública, que solo dice si algo está roto.

**Resultado: se cumplen las cinco.**

## Referencia de la DFL, partido a partido

[medido] `python validation/scripts/d_estado/traslado_atd.py`, parte A. Frames con etiqueta.

| medida | mínimo entre partidos | mediana | máximo |
|---|---|---|---|
| velocidad media en 2 s, p10 (m/s) | 0,62 | 0,74 | 0,76 |
| velocidad media en 2 s, p50 (m/s) | 1,44 | 1,64 | 1,74 |
| velocidad media en 2 s, p90 (m/s) | 2,96 | 3,21 | 3,27 |
| % de frames por debajo de 1,2 m/s | 26,99 | 30,36 | 38,12 |
| fracción de jugadores a menos de 1 m/s, p50 | 0,22 | 0,23 | 0,30 |
| % de frames con 1 jugador o más fuera (más de 0,3 m) | 12,55 | 13,98 | 17,70 |
| % de frames con 3 o más fuera | 0,00 | 0,36 | 1,15 |
| % con 1 o más fuera, solo con el balón en juego | 1,54 | 2,10 | 2,99 |
| % con 1 o más fuera, solo en `D` | 25,16 | 29,97 | 37,40 |
| slots vistos por frame, mediana | 21,00 | 22,00 | 22,00 |
| % de frames en `D` | 40,74 | 44,29 | 51,70 |

## La pieza si faltan jugadores a ratos

[medido] El mismo script, parte B, con los 7 partidos juntos. En la DFL están todos los jugadores; en el
ATD se ven 22 de mediana y 18 en el p10. Usa el `MODEL` del módulo, que ha visto estos partidos al
entrenar: las filas valen para compararlas entre sí, no como nota. Por eso la primera no coincide con la
medida de la pieza, que deja un partido fuera (0,809).

| jugadores | vistos por frame, mediana | frames que el modelo ve más `D` que juego | `D` real | paradas detectadas | inicio a ≤ 25 frames | fin a ≤ 25 frames | `D` espurios por minuto de juego | `spellF1` con equipo oráculo (flag, previo) | sin `D` |
|---|---|---|---|---|---|---|---|---|---|
| están todos (como en la medida de la pieza) | 22 | 44,8 % | 44,8 % | 611 de 713 (86 %) | 35 % | 40 % | 0,24 | 0,813 | 0,770 |
| falta el 7 % del tiempo, en bloques de 2 s | 20 | 45,2 % | 44,8 % | 613 de 713 (86 %) | 33 % | 39 % | 0,29 | 0,807 | 0,770 |
| falta el 7 % del tiempo, en bloques de 0,4 s | 20 | 45,3 % | 44,8 % | 617 de 713 (87 %) | 34 % | 39 % | 0,28 | 0,806 | 0,770 |
| falta el 20 % del tiempo, en bloques de 2 s | 18 | 46,3 % | 44,8 % | 612 de 713 (86 %) | 31 % | 37 % | 0,35 | 0,789 | 0,770 |

Las dos partes se ejecutaron con un sustituto en numpy de las dos funciones de `scikit-learn` que usan
estos scripts, porque no estaba instalado. Con ese sustituto, los coeficientes del módulo y la tabla
principal de `2026-11-14_d_estado.md` salen idénticos a los de la PR.

## Lo que la salida enseña de las paradas

[observación, sobre la salida de abajo; no elige nada]

- **Antes de un córner, de una falta o de un saque inicial el juego ya parece parado:** en el 91 %, el
  73 % y el 94 % de los frames de los 10 s anteriores, la velocidad media de los jugadores queda por
  debajo de 1,2 m/s.
- **Antes de un saque de banda o de puerta, no:** el 44 % y el 36 %. Son 36 de los 59 reinicios del Smart
  Tagging. Ahí el estado solo no basta: hace falta el instante, que es la pieza de fronteras
  (`possession/dead_ball.py`).
- **El final de las dos partes parece balón muerto:** en los 30 s finales, el 53 % y el 87 % de los frames
  por debajo de 1,2 m/s.

## Comprobación con la entrega regenerada

[medido] Ismael regeneró la entrega con `main` en `4738082`, ya con el modelo por defecto
(`python -m possession.pipeline --name equipo_v1`; sha256 `c7d3dd31…5647d`). La banda se fijó antes de
regenerarla, como orden de magnitud sacado de la DFL [inferencia].

| | entrega | banda fijada antes |
|---|---|---|
| frames `D`, de los 158.857 evaluados | 68.897 (43,4 %) | entre el 15 y el 60 % |
| paradas | 111 (51 y 60) | 250 como mucho |
| posesiones | 321 (166 y 155) | – |
| frames con piezas en conflicto | 0 | – |

- **Queda dentro de la banda:** no se vuelve atrás.
- **`validate_submission.py`:** válida, 199.319 filas.
- **Ventana pública, solo para ver que no está rota:**
  - ninguna `X` en frames evaluados;
  - 19 posesiones, frente a 17 reales;
  - el `D` deja de ser casi cero: F1 de `D` 0,767 (precisión 0,85 y cobertura 0,70);
  - `spellF1` 0,489 y `macroF1` 0,788; `baseline_smooth50`, 0,326 y 0,621.

  Son 5 minutos y 17 posesiones: no elige entre versiones ni dice cuánto mejora.

## Salida del script del partido

`python validation/partido/agregados_jugadores.py`, tal cual. Solo agregados de los frames evaluados.

```
4. Velocidad media de los jugadores (m/s, media móvil de 2 s)
   slots vistos por frame en los evaluados: p10=18.00  p50=22.00  p90=22.00
   referencia DFL (7 partidos)  en D p10/p50/p90 = 0.53 / 1.02 / 1.69   en juego = 1.38 / 2.27 / 3.62
   todos los frames evaluados                                  158857 frames   p10=0.70  p50=1.50  p90=2.94   < 1.2 m/s  35.4 %
   parte 1: 30 s iniciales del bloque evaluado                    750 frames   p10=1.78  p50=2.59  p90=4.06   < 1.2 m/s   1.6 %
   parte 1: 30 s finales del bloque evaluado                      751 frames   p10=0.11  p50=1.15  p90=1.85   < 1.2 m/s  52.7 %
   parte 2: 30 s iniciales del bloque evaluado                    750 frames   p10=0.89  p50=1.30  p90=1.65   < 1.2 m/s  33.9 %
   parte 2: 30 s finales del bloque evaluado                      751 frames   p10=0.61  p50=0.81  p90=1.50   < 1.2 m/s  87.2 %
   throw-in (n=26): 10 s antes de la ventana                     6500 frames   p10=0.80  p50=1.33  p90=2.56   < 1.2 m/s  44.2 %
   throw-in (n=26): 5 s después de la ventana                    3250 frames   p10=0.96  p50=1.69  p90=2.83   < 1.2 m/s  24.5 %
   corner kick (n=12): 10 s antes de la ventana                  3000 frames   p10=0.52  p50=0.84  p90=1.15   < 1.2 m/s  91.2 %
   corner kick (n=12): 5 s después de la ventana                 1500 frames   p10=1.04  p50=1.49  p90=3.38   < 1.2 m/s  25.8 %
   goal kick (n=10): 10 s antes de la ventana                    2500 frames   p10=0.67  p50=1.72  p90=3.37   < 1.2 m/s  35.6 %
   goal kick (n=10): 5 s después de la ventana                   1250 frames   p10=0.90  p50=1.97  p90=3.08   < 1.2 m/s  18.6 %
   kick off (todos) (n=6): 10 s antes de la ventana              1500 frames   p10=0.28  p50=0.80  p90=1.14   < 1.2 m/s  93.7 %
   kick off (todos) (n=6): 5 s después de la ventana              750 frames   p10=0.84  p50=2.01  p90=3.39   < 1.2 m/s  16.7 %
   free kick (n=5): 10 s antes de la ventana                     1250 frames   p10=0.46  p50=0.83  p90=1.48   < 1.2 m/s  73.0 %
   free kick (n=5): 5 s después de la ventana                     625 frames   p10=0.75  p50=1.12  p90=2.17   < 1.2 m/s  55.4 %
   todos los reinicios: 10 s antes de la ventana                14750 frames   p10=0.59  p50=1.05  p90=2.44   < 1.2 m/s  59.8 %
   todos los reinicios: 5 s después de la ventana                7375 frames   p10=0.95  p50=1.71  p90=2.96   < 1.2 m/s  25.6 %
   fracción de jugadores a menos de 1 m/s (media de 2 s), en los evaluados: p10=0.08  p50=0.29  p90=0.74

6. Jugadores fuera de los límites del campo (más de 0.3 m)
   frames evaluados con ninguno jugador(es) fuera:  141374 ( 89.0 %)
   frames evaluados con uno jugador(es) fuera:   14250 (  9.0 %)
   frames evaluados con dos jugador(es) fuera:    2181 (  1.4 %)
   frames evaluados con tres o más fuera:          1052 (  0.7 %)
   de los frames con alguno fuera: por banda  80.2 %   por fondo  22.3 %
   throw-in               n= 26   ventanas (desde 5 s antes) con algún jugador fuera 22 ( 84.6 %)   segundos con alguien fuera por ventana p10=0.00  p50=6.74  p90=15.28
   corner kick            n= 12   ventanas (desde 5 s antes) con algún jugador fuera 11 ( 91.7 %)   segundos con alguien fuera por ventana p10=0.86  p50=4.26  p90=11.57
   goal kick              n= 10   ventanas (desde 5 s antes) con algún jugador fuera 7 ( 70.0 %)   segundos con alguien fuera por ventana p10=0.00  p50=1.00  p90=9.76
   kick off (todos)       n=  6   ventanas (desde 5 s antes) con algún jugador fuera 0 (  0.0 %)   segundos con alguien fuera por ventana p10=0.00  p50=0.00  p90=0.00
   free kick              n=  5   ventanas (desde 5 s antes) con algún jugador fuera 4 ( 80.0 %)   segundos con alguien fuera por ventana p10=2.75  p50=7.72  p90=12.18
```
