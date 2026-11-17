# El signo de z sin balón: DFL (vota) y SkillCorner (sin voto)

Código: ccbfa26 · pesos de K2: `conjunto_pesos.npz` (sha256 6d16316f85063f13…), el pliegue que no vio cada partido · B5: el pliegue que no vio el partido en la DFL; los de la entrega en SkillCorner · este script: sha256 d8e1d20009128144…

## DFL, 7 partidos

| condición | etiquetas | versión | balón | frames | acierto | peor partido | mejor partido |
|---|---|---|---|---|---|---|---|
| como el ATD | control | K2 | con balón | 482819 | 93.3 % | 90.8 % | 95.2 % |
| como el ATD | control | K2 | sin balón | 70286 | 89.0 % | 84.0 % | 92.9 % |
| como el ATD | control | B5 | con balón | 482819 | 91.4 % | 88.2 % | 93.1 % |
| como el ATD | control | B5 | sin balón | 70286 | 84.2 % | 76.2 % | 86.4 % |
| como el ATD | flag | K2 | con balón | 482819 | 89.2 % | 85.4 % | 91.3 % |
| como el ATD | flag | K2 | sin balón | 70286 | 84.6 % | 77.6 % | 87.6 % |
| como el ATD | flag | B5 | con balón | 482819 | 87.5 % | 83.3 % | 89.6 % |
| como el ATD | flag | B5 | sin balón | 70286 | 79.3 % | 69.0 % | 83.0 % |
| como el ATD, sin bloques | control | K2 | con balón | 545857 | 93.3 % | 90.8 % | 94.9 % |
| como el ATD, sin bloques | control | K2 | sin balón | 7248 | 90.8 % | 85.2 % | 93.0 % |
| como el ATD, sin bloques | control | B5 | con balón | 545857 | 91.4 % | 87.9 % | 93.0 % |
| como el ATD, sin bloques | control | B5 | sin balón | 7248 | 86.2 % | 83.4 % | 90.8 % |
| como el ATD, sin bloques | flag | K2 | con balón | 545857 | 89.1 % | 84.8 % | 91.6 % |
| como el ATD, sin bloques | flag | K2 | sin balón | 7248 | 76.3 % | 73.3 % | 80.4 % |
| como el ATD, sin bloques | flag | B5 | con balón | 545857 | 87.3 % | 82.4 % | 89.5 % |
| como el ATD, sin bloques | flag | B5 | sin balón | 7248 | 72.5 % | 68.3 % | 78.1 % |

## SkillCorner, mitad de entrenamiento, 10 partidos (sin voto)

| condición | etiquetas | versión | balón | frames | acierto | peor partido | mejor partido |
|---|---|---|---|---|---|---|---|
| detectado | sc | K2 | con balón | 743207 | 85.9 % | 80.8 % | 89.3 % |
| detectado | sc | K2 | sin balón | 57764 | 73.0 % | 64.5 % | 82.9 % |
| detectado | sc | B5 | con balón | 743207 | 85.6 % | 79.7 % | 89.8 % |
| detectado | sc | B5 | sin balón | 57764 | 66.0 % | 57.2 % | 72.0 % |
| detectado, suavizado | sc | K2 | con balón | 743207 | 85.8 % | 80.4 % | 89.2 % |
| detectado, suavizado | sc | K2 | sin balón | 57764 | 72.3 % | 63.4 % | 82.3 % |
| detectado, suavizado | sc | B5 | con balón | 743207 | 85.5 % | 79.5 % | 89.6 % |
| detectado, suavizado | sc | B5 | sin balón | 57764 | 66.1 % | 57.6 % | 72.9 % |

## La regla

- K2 sin balón, DFL «como el ATD», etiquetas de control: 89.0 % (umbral 60 %) → **en los trozos de Metrica, los frames vivos sin balón crudo no cuentan en la pérdida**
