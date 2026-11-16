## Las posesiones candidatas (corte de 5 s), 7 partidos juntos

| balón en los `D` | condición | etiquetas | candidatas | emparejadas con una real (IoU ≥ 0,5) | sus frames son, de verdad: `D` / su equipo / el de antes |
|---|---|---|---|---|---|
| tapado | como el ATD | flag | 108 | 26 (24 %) | 42 % / 37 % / 22 % |
| tapado | como el ATD | control | 108 | 20 (19 %) | 42 % / 33 % / 26 % |
| tapado | como el ATD, sin bloques | flag | 120 | 31 (26 %) | 39 % / 36 % / 25 % |
| tapado | como el ATD, sin bloques | control | 120 | 24 (20 %) | 39 % / 32 % / 29 % |
| a la vista | como el ATD | flag | 156 | 17 (11 %) | 58 % / 21 % / 21 % |
| a la vista | como el ATD | control | 156 | 12 (8 %) | 58 % / 16 % / 27 % |
| a la vista | como el ATD, sin bloques | flag | 160 | 19 (12 %) | 54 % / 22 % / 24 % |
| a la vista | como el ATD, sin bloques | control | 160 | 15 (9 %) | 54 % / 16 % / 30 % |

## spellF1 con el `D` propio: `main` y las dos variantes (diferencia frente a `main`)

| balón en los `D` | condición | etiquetas | `main` | 3 s, a D | 3 s, al de antes | 5 s, a D | 5 s, al de antes | 10 s, a D | 10 s, al de antes |
|---|---|---|---|---|---|---|---|---|---|
| tapado | como el ATD | flag | 0.416 | +0.000 (3 de 7) | -0.002 (3 de 7) | -0.002 (2 de 7) | -0.007 (2 de 7) | -0.015 (0 de 7) | -0.034 (0 de 7) |
| tapado | como el ATD | control | 0.616 | +0.008 (7 de 7) | +0.008 (7 de 7) | +0.007 (6 de 7) | +0.005 (5 de 7) | -0.004 (3 de 7) | -0.020 (1 de 7) |
| tapado | como el ATD, sin bloques | flag | 0.433 | +0.001 (3 de 7) | -0.001 (2 de 7) | -0.002 (2 de 7) | -0.008 (2 de 7) | -0.015 (0 de 7) | -0.035 (0 de 7) |
| tapado | como el ATD, sin bloques | control | 0.642 | +0.009 (7 de 7) | +0.010 (7 de 7) | +0.009 (6 de 7) | +0.007 (5 de 7) | -0.002 (3 de 7) | -0.019 (1 de 7) |
| a la vista | como el ATD | flag | 0.391 | +0.004 (5 de 7) | +0.002 (3 de 7) | +0.004 (5 de 7) | -0.003 (2 de 7) | -0.000 (5 de 7) | -0.021 (1 de 7) |
| a la vista | como el ATD | control | 0.569 | +0.014 (7 de 7) | +0.014 (7 de 7) | +0.018 (7 de 7) | +0.016 (7 de 7) | +0.021 (6 de 7) | +0.006 (4 de 7) |
| a la vista | como el ATD, sin bloques | flag | 0.405 | +0.004 (5 de 7) | +0.002 (4 de 7) | +0.004 (5 de 7) | -0.003 (3 de 7) | -0.000 (4 de 7) | -0.021 (0 de 7) |
| a la vista | como el ATD, sin bloques | control | 0.593 | +0.015 (7 de 7) | +0.015 (7 de 7) | +0.019 (7 de 7) | +0.017 (7 de 7) | +0.022 (7 de 7) | +0.009 (4 de 7) |
