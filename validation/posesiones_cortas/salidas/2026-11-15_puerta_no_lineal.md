# Fase 3: ¿limitan los rasgos o la forma lineal? (puerta, BITACORA.md §10)

α por pliegue (los 7 y sin cada partido), lineal 39 / red 33 / red 39: todos: 4 / 2 / 2; J03WMX: 2 / 2 / 2; J03WN1: 4 / 2 / 2; J03WOH: 4 / 2 / 2; J03WOY: 4 / 2 / 2; J03WPY: 8 / 2 / 2; J03WQQ: 4 / 2 / 2; J03WR9: 2 / 2 / 2

### DFL, cada partido con el pliegue que no lo vio, `D` oráculo

| balón y etiquetas | versión | spellF1 | frente a main [5–95 %] · gana en | frente a su lineal [5–95 %] | 2–10 s encontradas | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| como el ATD, control | main (B5) | 0,728 | – | – | 65 % (544 de 836) | 1661 / 1736 |
| como el ATD, control | lineal, 33 (B9) | 0,722 | -0,006 [-0,015 a +0,002] · 3 de 7 | – | 70 % (583 de 836) | 1810 / 1736 |
| como el ATD, control | red, 33 | 0,723 | -0,005 [-0,016 a +0,005] · 1 de 7 | +0,001 [-0,007 a +0,009] | 74 % (617 de 836) | 1912 / 1736 |
| como el ATD, control | lineal, 39 | 0,720 | -0,008 [-0,018 a +0,001] · 3 de 7 | – | 73 % (607 de 836) | 1889 / 1736 |
| como el ATD, control | red, 39 | 0,725 | -0,003 [-0,015 a +0,009] · 3 de 7 | +0,005 [-0,004 a +0,014] | 76 % (635 de 836) | 1987 / 1736 |
| como el ATD, sin bloques, control | main (B5) | 0,748 | – | – | 68 % (568 de 836) | 1675 / 1736 |
| como el ATD, sin bloques, control | lineal, 33 (B9) | 0,743 | -0,005 [-0,014 a +0,004] · 4 de 7 | – | 74 % (619 de 836) | 1851 / 1736 |
| como el ATD, sin bloques, control | red, 33 | 0,744 | -0,004 [-0,014 a +0,006] · 3 de 7 | +0,001 [-0,007 a +0,009] | 78 % (654 de 836) | 1965 / 1736 |
| como el ATD, sin bloques, control | lineal, 39 | 0,736 | -0,011 [-0,022 a -0,002] · 3 de 7 | – | 76 % (637 de 836) | 1924 / 1736 |
| como el ATD, sin bloques, control | red, 39 | 0,744 | -0,003 [-0,015 a +0,007] · 4 de 7 | +0,008 [-0,001 a +0,017] | 79 % (661 de 836) | 2005 / 1736 |
| como el ATD, flag | main (B5) | 0,498 | – | – | 39 % (587 de 1503) | 1661 / 3061 |
| como el ATD, flag | lineal, 33 (B9) | 0,537 | +0,039 [+0,030 a +0,047] · 7 de 7 | – | 45 % (677 de 1503) | 1810 / 3061 |
| como el ATD, flag | red, 33 | 0,559 | +0,061 [+0,051 a +0,071] · 7 de 7 | +0,022 [+0,013 a +0,030] | 49 % (740 de 1503) | 1912 / 3061 |
| como el ATD, flag | lineal, 39 | 0,553 | +0,054 [+0,046 a +0,063] · 7 de 7 | – | 49 % (736 de 1503) | 1889 / 3061 |
| como el ATD, flag | red, 39 | 0,586 | +0,087 [+0,077 a +0,097] · 7 de 7 | +0,033 [+0,024 a +0,042] | 53 % (795 de 1503) | 1987 / 3061 |
| como el ATD, sin bloques, flag | main (B5) | 0,512 | – | – | 41 % (617 de 1503) | 1675 / 3061 |
| como el ATD, sin bloques, flag | lineal, 33 (B9) | 0,560 | +0,048 [+0,040 a +0,057] · 6 de 7 | – | 49 % (731 de 1503) | 1851 / 3061 |
| como el ATD, sin bloques, flag | red, 33 | 0,584 | +0,072 [+0,062 a +0,082] · 7 de 7 | +0,024 [+0,016 a +0,033] | 53 % (798 de 1503) | 1965 / 3061 |
| como el ATD, sin bloques, flag | lineal, 39 | 0,573 | +0,060 [+0,052 a +0,069] · 7 de 7 | – | 52 % (781 de 1503) | 1924 / 3061 |
| como el ATD, sin bloques, flag | red, 39 | 0,604 | +0,092 [+0,081 a +0,102] · 7 de 7 | +0,031 [+0,022 a +0,040] | 55 % (828 de 1503) | 2005 / 3061 |

Comprobación: `main` y B9 por este camino (spellF1 de arriba) tienen que ser 0,728 / 0,748 / 0,498 / 0,512 y 0,722 / 0,743 / 0,537 / 0,560.

### SkillCorner, `lector.ENTRENAMIENTO` (10 partidos), con el modelo de los 7 de la DFL, `D` oráculo

| balón y etiquetas | versión | spellF1 | frente a main [5–95 %] · gana en | frente a su lineal [5–95 %] | 2–10 s encontradas | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| detectado | main (B5) | 0,519 | – | – | 38 % (537 de 1402) | 2270 / 3228 |
| detectado | lineal, 33 (B9) | 0,514 | -0,005 [-0,009 a +0,000] · 1 de 10 | – | 39 % (548 de 1402) | 2391 / 3228 |
| detectado | red, 33 | 0,499 | -0,021 [-0,028 a -0,013] · 0 de 10 | -0,016 [-0,022 a -0,010] | 42 % (593 de 1402) | 2744 / 3228 |
| detectado | lineal, 39 | 0,506 | -0,013 [-0,019 a -0,007] · 1 de 10 | – | 41 % (569 de 1402) | 2545 / 3228 |
| detectado | red, 39 | 0,494 | -0,025 [-0,033 a -0,019] · 2 de 10 | -0,013 [-0,018 a -0,007] | 41 % (574 de 1402) | 2744 / 3228 |
| detectado, suavizado | main (B5) | 0,514 | – | – | 38 % (534 de 1402) | 2284 / 3228 |
| detectado, suavizado | lineal, 33 (B9) | 0,518 | +0,004 [-0,002 a +0,009] · 7 de 10 | – | 40 % (556 de 1402) | 2415 / 3228 |
| detectado, suavizado | red, 33 | 0,495 | -0,020 [-0,027 a -0,012] · 0 de 10 | -0,023 [-0,030 a -0,018] | 41 % (577 de 1402) | 2779 / 3228 |
| detectado, suavizado | lineal, 39 | 0,505 | -0,009 [-0,015 a -0,003] · 3 de 10 | – | 41 % (570 de 1402) | 2587 / 3228 |
| detectado, suavizado | red, 39 | 0,495 | -0,019 [-0,027 a -0,012] · 2 de 10 | -0,010 [-0,015 a -0,004] | 41 % (579 de 1402) | 2776 / 3228 |

## Regla de BITACORA.md §10

- red, 33: a) control +0,010 con intervalo > 0: **no** · b) 2–10 s +3 puntos: **sí** · c) SkillCorner > 0 con intervalo > 0: **no** · (descriptivo) gana a su lineal: **no**
- red, 39: a) control +0,010 con intervalo > 0: **no** · b) 2–10 s +3 puntos: **sí** · c) SkillCorner > 0 con intervalo > 0: **no** · (descriptivo) gana a su lineal: **no**

**Se cierra la pregunta:** con estos rasgos no hay más, ni con un modelo flexible (una red de una capa de 32).
