# ¿Por qué fallamos? Diagnóstico de errores en 17 partidos abiertos · 2026-11-15 · Claude (sesión de Ismael)

- **Fecha y quién:** 15/11/2026. Lo pidió Ismael: saber en qué casos falla el pipeline, con todos los
  partidos abiertos. Lo escribió y lo ejecutó Claude.
- **Datos:** los 7 partidos de la Bundesliga (Bassek et al., 2025, CC BY 4.0), con el balón «como el ATD»,
  y 10 de los 20 de SkillCorner (A-League 2024/25, licencia MIT), con el balón «detectado». Nada del
  partido.
- **Código:** `main` en `fb9e921` más `validation/skillcorner/`. En la DFL, B5 puntúa cada partido con los
  coeficientes que no lo han visto, como el harness.
- **Comando:** `python validation/scripts/diagnostico_errores.py` (unos 5 minutos).
- **Para qué:** repartir el trabajo que queda. **Es descriptivo: no decide nada.** No hubo regla previa.
- **SkillCorner se partió en dos antes de mirar nada.** Con los ids ordenados, los 10 de posición par se
  usan aquí. Los 10 de posición impar quedan intactos, como examen: una idea que salga de este diagnóstico
  se comprueba en ellos (`validation/skillcorner/BITACORA.md` §8).
- **Comprobación del instrumento** [medido]: repite el harness (0,498 y 0,728 con el `D` de las etiquetas;
  0,416 y 0,616 con el propio; 1.661 posesiones predichas) y la tabla por duración del diagnóstico de David
  (2 / 10 / 27 / 58 / 86 % con el flag). El emparejamiento es el del scorer oficial.

**Lectura en cinco líneas** [medido, salvo donde se dice]:

1. **Casi nunca partimos una posesión en trozos:** es la causa de entre el 1 y el 4 % de las que no
   encontramos. El fallo es de cambios de equipo, y depende de las etiquetas:
   - con el flag y con SkillCorner **cambiamos de menos:** predecimos 1.661 posesiones frente a 3.061, y
     2.270 frente a 3.228;
   - con control **cambiamos las veces justas, pero en otro sitio:** 1.661 frente a 1.736, y aun así faltan
     477 y sobran 402.
2. **De las que no encontramos,** entre el 55 y el 58 % es porque decimos el otro equipo casi todo el rato, y
   entre el 38 y el 44 % porque la nuestra se funde con la de al lado. Sale igual con las tres etiquetas.
3. **Las cortas se pierden enteras.** De las de menos de 2 s encontramos entre el 2 y el 25 %. De las de
   10 s o más, el 86–92 % en la DFL y el 74 % en SkillCorner.
4. **Pocos cambios reales tienen un cambio nuestro a menos de 1 s:** el 20 % con el flag, el 37 % con
   control y el 16 % en SkillCorner. El placebo (nuestros cambios desplazados 60 s) da el 2 %, así que no
   es casualidad. En los que caen a menos de 1 s no hay un retraso sistemático: la mediana es de +3 y +1
   frames en la DFL y de −5 en SkillCorner.
5. **En el `D`, los bordes de las paradas que ya vemos valen como mucho 0,05–0,07** en la DFL. Con el `D`
   propio, ponerlos en su sitio sube de 0,416 a 0,465 con el flag y de 0,616 a 0,689 con control. El inicio
   y el final valen parecido: +0,032 y +0,030 con el flag, +0,051 y +0,042 con control.

## Lo que dice y lo que no

- **[inferencia] Para las piezas de `D` (Manuel y Ana):** apoya lo que ya tienen asignado. Es un techo en la
  DFL: supone bordes perfectos en las paradas detectadas. «Detectada» es aquí cualquier parada con algún
  frame nuestro de `D` dentro (el 93 %); la pieza de estado pide cubrir la mitad y da el 86 %. Lo que queda
  hasta el `D` perfecto (0,498 y 0,728) son paradas que no vemos, paradas que inventamos y huecos de juego
  dentro de las detectadas.
- **[inferencia] Para la evidencia de equipo:** el fallo es de cambios, no de parpadeo. Bajar el coste de
  cambio ya se midió y empata. La evidencia de equipo está cerrada por la regla de parada del 15/11:
  reabrirla es decisión de Ismael.
- **[inferencia] Para el vídeo de la ventana pública:** lo que hay que buscar son los cambios de equipo que
  no hacemos, los que hacemos donde no toca y los bordes de las paradas.
- **Lo que no dice:**
  - nada del partido del reto;
  - nada del retraso del balón del ATD: aquí el balón de la DFL va suavizado sin retraso. La medida de
    Antonio sigue haciendo falta;
  - nada del `D` con Smart Tagging ni con el balón de verdad (en la DFL va tapado en los `D`);
  - el `D` de SkillCorner no se analiza: son sobre todo repeticiones sin tracking;
  - las causas son una clasificación, no una medida de cuánta nota da arreglar cada una.

## Cómo se clasifica cada posesión real que no encontramos

Una sola causa por posesión, en este orden:

- **otro equipo:** en la mayor parte de sus frames decimos el otro equipo;
- **la nuestra es más larga:** decimos el equipo bueno, pero la posesión nuestra que más la pisa es más
  larga que ella (se funde con lo de al lado);
- **la nuestra es más corta o va partida:** decimos el equipo bueno, pero a trozos o solo en parte.

## Salida, tal cual

```text
# Diagnóstico de errores del pipeline de main (descriptivo)

Posesión encontrada: emparejada con IoU ≥ 0,5 por el scorer oficial. Duraciones a 25 fps.

## 1–3. DFL, 7 partidos, «como el ATD», con el `D` de las etiquetas

### Etiquetas: flag

spellF1 0.498 · posesiones reales 3061 · nuestras 1661 · encontradas con IoU ≥ 0,5: 1198 (39 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 384 | 2 % | 73 % | 25 % | 0 % |
| 1–2 s | 535 | 10 % | 57 % | 33 % | 0 % |
| 2–5 s | 934 | 27 % | 40 % | 31 % | 1 % |
| 5–10 s | 569 | 58 % | 12 % | 30 % | 0 % |
| ≥ 10 s | 639 | 86 % | 1 % | 12 % | 1 % |
| **de las 1863 no encontradas** | | | 55 % | 44 % | 1 % |

Posesiones nuestras que sobran: 463 de 1661 (28 %). Por causa: otro equipo 44 %; más larga que la real 38 %; más corta que la real 19 %.

Cambios directos de equipo: 2351 reales y 951 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 11 % | 20 % | 31 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +3, p25 -9, p75 +14; 462 parejas.

### Etiquetas: control

spellF1 0.728 · posesiones reales 1736 · nuestras 1661 · encontradas con IoU ≥ 0,5: 1259 (73 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 48 | 15 % | 62 % | 23 % | 0 % |
| 1–2 s | 111 | 25 % | 48 % | 27 % | 0 % |
| 2–5 s | 399 | 53 % | 28 % | 18 % | 1 % |
| 5–10 s | 437 | 76 % | 15 % | 9 % | 0 % |
| ≥ 10 s | 741 | 92 % | 2 % | 4 % | 2 % |
| **de las 477 no encontradas** | | | 58 % | 38 % | 4 % |

Posesiones nuestras que sobran: 402 de 1661 (24 %). Por causa: otro equipo 54 %; más larga que la real 8 %; más corta que la real 37 %.

Cambios directos de equipo: 1026 reales y 951 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 20 % | 37 % | 57 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana +1, p25 -10, p75 +13; 376 parejas.

## 1–3. SkillCorner, «detectado», con el `D` de las etiquetas

Partidos para diagnosticar (`lector.ENTRENAMIENTO`): 10. Los otros 10 (`lector.EXAMEN`) quedan intactos, como examen.

### Etiquetas de SkillCorner

spellF1 0.519 · posesiones reales 3228 · nuestras 2270 · encontradas con IoU ≥ 0,5: 1450 (45 %)

| duración real | reales | encontradas | otro equipo | la nuestra es más larga | la nuestra es más corta o va partida |
|---|---|---|---|---|---|
| < 1 s | 297 | 3 % | 83 % | 13 % | 0 % |
| 1–2 s | 427 | 21 % | 62 % | 16 % | 0 % |
| 2–5 s | 714 | 29 % | 39 % | 32 % | 0 % |
| 5–10 s | 688 | 48 % | 23 % | 28 % | 1 % |
| ≥ 10 s | 1102 | 74 % | 6 % | 17 % | 3 % |
| **de las 1778 no encontradas** | | | 57 % | 40 % | 2 % |

Posesiones nuestras que sobran: 820 de 2270 (36 %). Por causa: otro equipo 54 %; más larga que la real 16 %; más corta que la real 30 %.

Cambios directos de equipo: 2210 reales y 1252 nuestros.

| cambios reales con un cambio nuestro al mismo equipo | a ±12 frames | a ±25 | a ±50 |
|---|---|---|---|
| nuestros cambios | 9 % | 16 % | 26 % |
| placebo: los mismos, desplazados 60 s | 1 % | 2 % | 5 % |

Retraso con signo de los que caen a ±25 frames (positivo es tarde): mediana -5, p25 -15, p75 +6; 360 parejas.

## 4. Qué borde del `D` cuesta más (DFL, «como el ATD», con el `D` propio)

Paradas reales: 713 · con algún frame nuestro de `D` dentro: 666 (93 %). Es un criterio más laxo que el de la pieza de estado, que pide cubrir la mitad de la parada.

| versión | spellF1, flag | spellF1, control |
|---|---|---|
| `D` propio, tal cual | 0.416 | 0.616 |
| + inicio de las paradas detectadas, el real | 0.448 | 0.667 |
| + final de las paradas detectadas, el real | 0.446 | 0.658 |
| + los dos bordes, los reales | 0.465 | 0.689 |
| `D` de las etiquetas (oráculo) | 0.498 | 0.728 |

Lo que queda entre «los dos bordes» y el oráculo: las paradas que no vemos, las que inventamos y los huecos de juego que dejamos dentro de una parada detectada.
```
