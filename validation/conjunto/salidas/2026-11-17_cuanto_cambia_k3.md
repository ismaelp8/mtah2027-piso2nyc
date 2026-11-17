# Cuánto cambia la salida con K3 (descriptivo, `D` propio, sin las capas del partido)

Código: 74f3191 · este script: sha256 68a7f25e53a4f34d… · 7 partidos de la DFL y 10 de SkillCorner, cada uno con el pliegue que no lo vio.

## De main a K3

| datos | condición | balón en los D | frames evaluados que cambian | de un equipo al otro | de un equipo a D | de D a un equipo | posesiones: main → K3 | paradas: main → K3 | frames D: main → K3 | posesiones de menos de 12 frames: main → K3 | de menos de 25: main → K3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DFL | como el ATD | balón tapado en los D | 2.9 % | 2.0 % | 0.36 % | 0.58 % | 1538 → 1507 (-2.0 %) | 698 → 701 (+0.4 %) | 43.4 % → 43.2 % | 0 → 0 | 7 → 1 |
| DFL | como el ATD | balón a la vista en los D | 3.0 % | 1.9 % | 0.52 % | 0.61 % | 1613 → 1577 (-2.2 %) | 698 → 699 (+0.1 %) | 39.0 % → 38.9 % | 0 → 0 | 6 → 1 |
| DFL | como el ATD, sin bloques | balón tapado en los D | 2.6 % | 1.7 % | 0.35 % | 0.58 % | 1537 → 1507 (-2.0 %) | 686 → 688 (+0.3 %) | 43.1 % → 42.8 % | 0 → 0 | 5 → 1 |
| DFL | como el ATD, sin bloques | balón a la vista en los D | 2.8 % | 1.7 % | 0.53 % | 0.56 % | 1621 → 1575 (-2.8 %) | 687 → 685 (-0.3 %) | 38.6 % → 38.6 % | 0 → 0 | 3 → 1 |
| SkillCorner | detectado | – | 4.6 % | 1.4 % | 2.35 % | 0.82 % | 2092 → 2053 (-1.9 %) | 1061 → 1070 (+0.8 %) | 43.3 % → 44.8 % | 1 → 0 | 16 → 2 |
| SkillCorner | detectado, suavizado | – | 5.0 % | 1.6 % | 2.51 % | 0.89 % | 2099 → 2054 (-2.1 %) | 1065 → 1075 (+0.9 %) | 43.1 % → 44.8 % | 1 → 0 | 16 → 2 |

## De main a K2

| datos | condición | balón en los D | frames evaluados que cambian | de un equipo al otro | de un equipo a D | de D a un equipo | posesiones: main → K2 | paradas: main → K2 | frames D: main → K2 | posesiones de menos de 12 frames: main → K2 | de menos de 25: main → K2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DFL | como el ATD | balón tapado en los D | 4.7 % | 3.5 % | 0.48 % | 0.68 % | 1538 → 1574 (+2.3 %) | 698 → 701 (+0.4 %) | 43.4 % → 43.2 % | 0 → 0 | 7 → 6 |
| DFL | como el ATD | balón a la vista en los D | 5.3 % | 3.5 % | 1.02 % | 0.80 % | 1613 → 1614 (+0.1 %) | 698 → 698 (+0.0 %) | 39.0 % → 39.2 % | 0 → 0 | 6 → 8 |
| DFL | como el ATD, sin bloques | balón tapado en los D | 4.4 % | 3.2 % | 0.48 % | 0.70 % | 1537 → 1580 (+2.8 %) | 686 → 689 (+0.4 %) | 43.1 % → 42.9 % | 0 → 0 | 5 → 11 |
| DFL | como el ATD, sin bloques | balón a la vista en los D | 5.1 % | 3.3 % | 1.00 % | 0.77 % | 1621 → 1625 (+0.2 %) | 687 → 685 (-0.3 %) | 38.6 % → 38.8 % | 0 → 0 | 3 → 12 |
| SkillCorner | detectado | – | 7.4 % | 3.0 % | 3.27 % | 1.13 % | 2092 → 2144 (+2.5 %) | 1061 → 1076 (+1.4 %) | 43.3 % → 45.4 % | 1 → 0 | 16 → 2 |
| SkillCorner | detectado, suavizado | – | 7.8 % | 3.2 % | 3.46 % | 1.15 % | 2099 → 2139 (+1.9 %) | 1065 → 1081 (+1.5 %) | 43.1 % → 45.5 % | 1 → 0 | 16 → 1 |

## De K2 a K3

| datos | condición | balón en los D | frames evaluados que cambian | de un equipo al otro | de un equipo a D | de D a un equipo | posesiones: K2 → K3 | paradas: K2 → K3 | frames D: K2 → K3 | posesiones de menos de 12 frames: K2 → K3 | de menos de 25: K2 → K3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DFL | como el ATD | balón tapado en los D | 2.0 % | 1.5 % | 0.25 % | 0.27 % | 1574 → 1507 (-4.3 %) | 701 → 701 (+0.0 %) | 43.2 % → 43.2 % | 0 → 0 | 6 → 1 |
| DFL | como el ATD | balón a la vista en los D | 2.5 % | 1.6 % | 0.30 % | 0.61 % | 1614 → 1577 (-2.3 %) | 698 → 699 (+0.1 %) | 39.2 % → 38.9 % | 0 → 0 | 8 → 1 |
| DFL | como el ATD, sin bloques | balón tapado en los D | 2.0 % | 1.4 % | 0.26 % | 0.28 % | 1580 → 1507 (-4.6 %) | 689 → 688 (-0.1 %) | 42.9 % → 42.8 % | 0 → 0 | 11 → 1 |
| DFL | como el ATD, sin bloques | balón a la vista en los D | 2.5 % | 1.6 % | 0.32 % | 0.59 % | 1625 → 1575 (-3.1 %) | 685 → 685 (+0.0 %) | 38.8 % → 38.6 % | 0 → 0 | 12 → 1 |
| SkillCorner | detectado | – | 3.3 % | 1.6 % | 0.53 % | 1.14 % | 2144 → 2053 (-4.2 %) | 1076 → 1070 (-0.6 %) | 45.4 % → 44.8 % | 0 → 0 | 2 → 2 |
| SkillCorner | detectado, suavizado | – | 3.3 % | 1.7 % | 0.49 % | 1.18 % | 2139 → 2054 (-4.0 %) | 1081 → 1075 (-0.6 %) | 45.5 % → 44.8 % | 0 → 0 | 1 → 2 |
