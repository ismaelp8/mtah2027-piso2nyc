Zonas: Z1 posesiones reales de 2 a 10 s en que `main` dice el otro equipo; Z2 ±1 s de los cambios reales; Z4 juego sin balón. «Rescata»: de los frames de Z2 que `main` falla, en cuántos la señal opina y acierta. «Estropea»: de los que `main` acierta, en cuántos opina y falla. «+ B5»: regresión con la diferencia de B5 y la señal, fuera de muestra, frente al signo de B5 solo, en puntos de acierto por frame.

## SkillCorner, mitad de entrenamiento (10 partidos), «detectado», `main` con el `D` de las etiquetas

### SkillCorner (la regresión se entrena en una mitad y se mide en la otra)

| señal | opina en juego | acierta en juego | Z1: opina / acierta | Z2: rescata / estropea | sin balón: opina / acierta | + B5: Δ acierto en juego | + B5: Δ en Z1∪Z2 | + B5: Δ sin balón |
|---|---|---|---|---|---|---|---|---|
| R1 más cercano (N1) | 93 % | 75.1 % | 93 % / 37.1 % | 33.7 % / 20.7 % | 0 % / nan % | +0.01 | -0.02 | +0.00 |
| R2 dirección del balón (B9) | 59 % | 61.3 % | 64 % / 50.1 % | 33.2 % / 19.6 % | 0 % / nan % | -0.01 | -0.01 | +0.00 |
| R3 signo de B5 | 99 % | 84.8 % | 100 % / 12.3 % | 1.3 % / 0.5 % | 89 % / 73.9 % | – | – | – |
| S1 diferencia de distancias > 1 m | 72 % | 80.3 % | 58 % / 34.7 % | 22.6 % / 12.6 % | 0 % / nan % | -0.09 | +0.29 | +0.00 |
| S2 los dos más cercanos, mismo equipo | 6 % | 62.1 % | 8 % / 51.4 % | 5.3 % / 3.2 % | 0 % / nan % | +0.03 | -0.04 | +0.00 |
| S3 mayoría a 3 m | 53 % | 82.6 % | 39 % / 42.4 % | 17.3 % / 10.0 % | 0 % / nan % | -0.15 | +0.55 | +0.00 |
| S4 mayoría a 5 m | 56 % | 73.1 % | 47 % / 53.0 % | 23.4 % / 19.9 % | 0 % / nan % | -0.20 | +0.27 | +0.00 |
| S5 mayoría a 10 m | 59 % | 54.5 % | 61 % / 62.2 % | 34.7 % / 37.9 % | 0 % / nan % | -0.16 | -0.09 | +0.00 |
| S6 llega antes (control del campo) | 38 % | 81.7 % | 20 % / 46.2 % | 12.2 % / 6.7 % | 0 % / nan % | -0.13 | +0.39 | +0.00 |
| S7 el que más se acerca | 66 % | 46.8 % | 70 % / 44.4 % | 28.4 % / 49.1 % | 0 % / nan % | +0.03 | +0.40 | +0.00 |
| S8 pegado 12 frames a 2 m (circular con control) | 39 % | 89.4 % | 29 % / 27.4 % | 4.4 % / 1.2 % | 0 % / nan % | -0.01 | +0.04 | +0.00 |
| S9 balón lento junto a un jugador | 21 % | 87.7 % | 16 % / 29.6 % | 3.0 % / 1.5 % | 0 % / nan % | -0.02 | +0.06 | +0.00 |
| S10 se mueve con el balón | 21 % | 79.6 % | 20 % / 38.0 % | 5.5 % / 5.2 % | 0 % / nan % | -0.00 | +0.07 | +0.00 |
| S11 el balón frena junto a un jugador | 33 % | 80.2 % | 31 % / 39.8 % | 15.1 % / 5.6 % | 2 % / 56.9 % | -0.06 | +0.39 | -0.01 |
| S12 más cercano presionado | 12 % | 65.6 % | 22 % / 30.6 % | 4.4 % / 3.1 % | 0 % / nan % | -0.00 | +0.05 | +0.00 |
| S13 más cercano libre | 46 % | 84.6 % | 25 % / 34.7 % | 10.7 % / 6.4 % | 0 % / nan % | -0.20 | +0.34 | +0.00 |
| S14 dos contactos seguidos (circular con control) | 38 % | 83.5 % | 34 % / 38.3 % | 11.2 % / 5.6 % | 8 % / 69.2 % | -0.01 | +0.68 | +0.08 |
| S15 el más ancho | 72 % | 88.1 % | 58 % / 11.7 % | 9.8 % / 9.5 % | 48 % / 81.7 % | +0.14 | -0.28 | -0.45 |
| S16 el más largo | 53 % | 83.7 % | 52 % / 16.9 % | 8.3 % / 8.8 % | 36 % / 71.9 % | +0.03 | -0.16 | -0.02 |
| S17 el de más área | 75 % | 87.1 % | 66 % / 12.9 % | 9.9 % / 10.4 % | 49 % / 77.8 % | +0.21 | -0.19 | -0.43 |
| S18 línea defensiva más alta | 88 % | 53.8 % | 91 % / 31.7 % | 38.0 % / 40.2 % | 69 % / 45.8 % | -0.00 | +0.46 | +0.05 |
| S19 por detrás del balón (el otro defiende) | 71 % | 72.0 % | 65 % / 49.6 % | 28.7 % / 27.1 % | 0 % / nan % | -0.30 | +0.41 | +0.00 |
| S20 sin balón: se queda el último | 7 % | 69.6 % | 7 % / 42.4 % | 1.9 % / 0.2 % | 100 % / 69.6 % | +0.52 | +0.19 | +7.23 |
| S21 el balón desaparece junto al portero | 2 % | 81.3 % | 1 % / 27.3 % | 0.1 % / 0.0 % | 24 % / 81.3 % | +0.41 | +0.01 | +5.68 |
| B5 + todas las señales de equipo | – | – | – | – | – | +0.76 | +2.08 | +7.54 |

Referencia: el signo de B5 acierta el 84.1 % de los frames de juego, el 47.2 % en Z1∪Z2 y el 66.0 % sin balón.
