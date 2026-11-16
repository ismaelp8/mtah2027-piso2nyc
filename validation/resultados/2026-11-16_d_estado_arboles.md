# Estado de `D` con árboles (idea 2.4): G2 y G3 frente a E2 · 2026-11-16 · Antonio, con Claude

> Los candidatos, lo que queda fijo y la regla de entrada se escribieron y se guardaron en git antes de medir:
> `docs/decisiones.md`, entrada del 16/11 «estado con árboles (idea 2.4): candidatos y regla de entrada» (commit
> `d0b67aa`). El script solo se probó antes con 2 partidos y la salida descartada, para ver que corría.

- **Para qué:** la idea 2.4 de `docs/investigacion_2026-11-16.md`: cambiar la regresión logística de la pieza de
  estado (E2, `possession/dead_state.py`, de Ana) por árboles con *boosting*, para colocar mejor los bordes de las
  paradas.
- **Datos:** los 7 partidos abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0). Nada del partido.
- **Candidatos:** G2, árboles con los 11 rasgos de E2; G3, con los 19 de E3. `HistGradientBoostingClassifier` de
  `scikit-learn` 1.7.2 con los parámetros fijados antes de medir, que imprime la salida. Cada candidato puntúa un
  partido con los árboles entrenados en los otros seis.
- **Entorno:** uno aparte, que no entra en `requirements-entrega.txt`: Python 3.11.18, numpy 2.4.6, scipy 1.17.1,
  pandas 3.1.1 y `scikit-learn` 1.7.2. Con él, `entrenar.py --comprobar` reproduce el `MODEL` de E2 bit a bit.
- **Comando:** `python validation/scripts/d_estado/medir_arboles.py` (bootstrap de 1.000 remuestreos; unos 3 minutos).
- **Código medido:** el de esta rama sobre `d0b67aa`, con `arboles.py` y `medir_arboles.py` tal como se suben.

**Lectura en cinco líneas** [medido, salvo donde se dice]:

1. **Con la regla, ningún candidato gana y la idea 2.4 se cierra.** G2 no llega en 4 de las 8 celdas del harness, todas
   con el balón tapado en los `D`. G3 no llega en 1: con el balón tapado, «como el ATD, sin bloques» y el flag saca
   +0,008 y gana en 5 de 7 (se piden +0,010 y 6 de 7).
2. **En el criterio del 13/11, los dos mejoran a E2 y no empeoran nada.** G3: el inicio a 25 frames o menos en el 47 %
   de las paradas (E2, 35 %), el fin en el 54 % (40 %), sesgo mediano de +5 y 0 frames (+14 y +17) y 0,16 `D` espurios
   por minuto (0,26). Sigue sin cumplir el criterio él solo: pide el 70 %.
3. **Con el equipo oráculo, G3 gana a E2 por +0,034 a +0,046 en las cuatro columnas** (7 de 7 en todas). En el pipeline
   entero la mejora se diluye: de +0,008 a +0,030 frente a `main`, más con el balón a la vista en los `D`.
4. **Los árboles son más frágiles que E2 si los jugadores tiemblan:** con 0,1 m detectan el 46 % de las paradas, frente
   al 61 % de E2. Con 0,2 m los tres se hunden (3–4 %).
5. **Que `main` esté en muestra no cambia nada:** E2 dejando un partido fuera queda a −0,001 o menos de `main` en todas
   las celdas. La comparación es justa.

## Salida del script

partidos: 7 · bootstrap: 1000 · árboles: {'learning_rate': 0.1, 'max_iter': 200, 'max_leaf_nodes': 15, 'min_samples_leaf': 200, 'l2_regularization': 1.0, 'early_stopping': False, 'random_state': 0} · scikit-learn en un entorno aparte

### Criterio del 13/11: por parada, 7 partidos juntos

| versión | AUC por frame, media (mín–máx) | paradas detectadas | inicio a ≤ 25 frames (por partido, mín–máx) | fin a ≤ 25 frames (por partido, mín–máx) | latencia del inicio p10 / p50 / p90 | latencia del fin p10 / p50 / p90 | `D` espurios por minuto de juego | rachas de menos de 25 frames (`D` / juego) |
|---|---|---|---|---|---|---|---|---|
| E2 | 0,957 (0,952–0,966) | 611 de 713 (86 %) | 35 % (26 %–42 %) | 40 % (33 %–45 %) | -127 / +14 / +116 | -31 / +17 / +160 | 0,26 | 0 / 0 |
| E2, temblor de 0.1 m | 0,956 (0,952–0,964) | 434 de 713 (61 %) | 17 % (12 %–25 %) | 35 % (32 %–40 %) | -6 / +55 / +226 | -83 / +0 / +36 | 0,02 | 0 / 0 |
| E2, temblor de 0.2 m | 0,952 (0,945–0,961) | 18 de 713 (3 %) | 0 % (0 %–2 %) | 1 % (0 %–4 %) | +10 / +150 / +436 | -490 / -21 / -4 | 0,00 | 0 / 0 |
| G2 | 0,971 (0,963–0,978) | 620 de 713 (87 %) | 43 % (31 %–51 %) | 51 % (43 %–60 %) | -39 / +14 / +97 | -38 / +6 / +72 | 0,23 | 0 / 0 |
| G2, placebo: desplazada 60 s | 0,524 (0,491–0,569) | 285 de 713 (40 %) | 3 % (1 %–6 %) | 2 % (0 %–4 %) | -1065 / -168 / +229 | -205 / +184 / +861 | 0,72 | 0 / 0 |
| G2, escala × 0.5 | 0,971 (0,963–0,978) | 615 de 713 (86 %) | 42 % (30 %–49 %) | 49 % (42 %–58 %) | -55 / +13 / +93 | -37 / +6 / +94 | 0,13 | 0 / 0 |
| G2, escala × 2 | 0,971 (0,962–0,978) | 616 de 713 (86 %) | 42 % (31 %–51 %) | 51 % (42 %–59 %) | -32 / +15 / +103 | -41 / +5 / +65 | 0,33 | 0 / 0 |
| G2, temblor de 0.1 m | 0,956 (0,947–0,965) | 325 de 713 (46 %) | 11 % (8 %–15 %) | 25 % (15 %–37 %) | -2 / +66 / +288 | -122 / -15 / +20 | 0,02 | 0 / 0 |
| G2, temblor de 0.2 m | 0,892 (0,864–0,918) | 31 de 713 (4 %) | 1 % (0 %–2 %) | 2 % (0 %–4 %) | +17 / +123 / +260 | -445 / -47 / +15 | 0,01 | 0 / 0 |
| G3 | 0,976 (0,968–0,983) | 621 de 713 (87 %) | 47 % (34 %–57 %) | 54 % (48 %–62 %) | -49 / +5 / +77 | -48 / +0 / +54 | 0,16 | 0 / 0 |
| G3, placebo: desplazada 60 s | 0,524 (0,490–0,572) | 293 de 713 (41 %) | 2 % (0 %–5 %) | 2 % (0 %–3 %) | -1077 / -142 / +209 | -237 / +187 / +782 | 0,64 | 0 / 0 |
| G3, escala × 0.5 | 0,976 (0,968–0,983) | 620 de 713 (87 %) | 46 % (36 %–56 %) | 53 % (44 %–60 %) | -72 / +5 / +77 | -47 / +0 / +80 | 0,11 | 0 / 0 |
| G3, escala × 2 | 0,976 (0,967–0,982) | 621 de 713 (87 %) | 47 % (34 %–57 %) | 55 % (48 %–64 %) | -46 / +5 / +78 | -49 / -1 / +45 | 0,24 | 0 / 0 |
| G3, temblor de 0.1 m | 0,963 (0,954–0,973) | 327 de 713 (46 %) | 12 % (8 %–16 %) | 21 % (12 %–34 %) | -4 / +60 / +272 | -106 / -20 / +19 | 0,00 | 0 / 0 |
| G3, temblor de 0.2 m | 0,891 (0,849–0,921) | 23 de 713 (3 %) | 0 % (0 %–1 %) | 2 % (0 %–3 %) | +22 / +195 / +323 | -77 / +1 / +70 | 0,00 | 0 / 0 |

Las latencias van en frames; positivo es tarde. Una parada no detectada cuenta como fallo en las dos columnas de «a ≤ 25 frames».

### `spellF1` oficial con el equipo oráculo, 7 partidos juntos

El `D` perfecto da 1,000 en todas las columnas. «Frente al control» lleva el intervalo del 5 al 95 % del bootstrap pareado del harness y en cuántos partidos gana.

| versión | flag, previo | flag, siguiente | control, previo | control, siguiente |
|---|---|---|---|---|
| control (v0): no opina | 0,770 | 0,786 | 0,620 | 0,615 |
| E2 | 0,809 · +0,039 [+0,026 a +0,052] · 6 de 7 | 0,819 · +0,032 [+0,019 a +0,045] · 6 de 7 | 0,795 · +0,175 [+0,154 a +0,196] · 7 de 7 | 0,787 · +0,172 [+0,152 a +0,192] · 7 de 7 |
| E2, temblor de 0.1 m | 0,809 · +0,039 [+0,030 a +0,048] · 7 de 7 | 0,835 · +0,048 [+0,038 a +0,059] · 7 de 7 | 0,781 · +0,161 [+0,145 a +0,178] · 7 de 7 | 0,778 · +0,163 [+0,147 a +0,181] · 7 de 7 |
| E2, temblor de 0.2 m | 0,763 · -0,007 [-0,011 a -0,003] · 1 de 7 | 0,785 · -0,001 [-0,006 a +0,003] · 1 de 7 | 0,635 · +0,015 [+0,008 a +0,023] · 7 de 7 | 0,634 · +0,020 [+0,012 a +0,028] · 7 de 7 |
| G2 | 0,836 · +0,066 [+0,054 a +0,078] · 7 de 7 | 0,847 · +0,060 [+0,048 a +0,072] · 7 de 7 | 0,818 · +0,197 [+0,177 a +0,219] · 7 de 7 | 0,812 · +0,198 [+0,177 a +0,217] · 7 de 7 |
| G2, placebo: desplazada 60 s | 0,495 · -0,275 [-0,290 a -0,258] · 0 de 7 | 0,503 · -0,284 [-0,300 a -0,268] · 0 de 7 | 0,392 · -0,228 [-0,249 a -0,207] · 0 de 7 | 0,392 · -0,223 [-0,244 a -0,202] · 0 de 7 |
| G2, escala × 0.5 | 0,841 · +0,070 [+0,058 a +0,082] · 7 de 7 | 0,851 · +0,065 [+0,052 a +0,077] · 7 de 7 | 0,828 · +0,208 [+0,188 a +0,228] · 7 de 7 | 0,823 · +0,208 [+0,188 a +0,227] · 7 de 7 |
| G2, escala × 2 | 0,829 · +0,059 [+0,047 a +0,071] · 7 de 7 | 0,840 · +0,053 [+0,041 a +0,065] · 7 de 7 | 0,805 · +0,185 [+0,164 a +0,205] · 7 de 7 | 0,801 · +0,186 [+0,165 a +0,205] · 7 de 7 |
| G2, temblor de 0.1 m | 0,787 · +0,017 [+0,009 a +0,025] · 6 de 7 | 0,819 · +0,033 [+0,024 a +0,042] · 7 de 7 | 0,740 · +0,119 [+0,104 a +0,135] · 7 de 7 | 0,743 · +0,128 [+0,111 a +0,144] · 7 de 7 |
| G2, temblor de 0.2 m | 0,768 · -0,002 [-0,005 a +0,002] · 2 de 7 | 0,786 · -0,000 [-0,004 a +0,003] · 2 de 7 | 0,638 · +0,018 [+0,010 a +0,025] · 7 de 7 | 0,629 · +0,015 [+0,007 a +0,022] · 7 de 7 |
| G3 | 0,843 · +0,073 [+0,061 a +0,084] · 7 de 7 | 0,857 · +0,071 [+0,057 a +0,083] · 7 de 7 | 0,829 · +0,209 [+0,189 a +0,230] · 7 de 7 | 0,832 · +0,218 [+0,197 a +0,237] · 7 de 7 |
| G3, placebo: desplazada 60 s | 0,498 · -0,273 [-0,287 a -0,256] · 0 de 7 | 0,506 · -0,280 [-0,297 a -0,265] · 0 de 7 | 0,398 · -0,222 [-0,245 a -0,201] · 0 de 7 | 0,398 · -0,217 [-0,239 a -0,196] · 0 de 7 |
| G3, escala × 0.5 | 0,846 · +0,076 [+0,064 a +0,088] · 7 de 7 | 0,861 · +0,075 [+0,061 a +0,087] · 7 de 7 | 0,835 · +0,214 [+0,195 a +0,235] · 7 de 7 | 0,838 · +0,224 [+0,203 a +0,243] · 7 de 7 |
| G3, escala × 2 | 0,839 · +0,069 [+0,057 a +0,080] · 7 de 7 | 0,852 · +0,066 [+0,053 a +0,078] · 7 de 7 | 0,822 · +0,202 [+0,181 a +0,221] · 7 de 7 | 0,823 · +0,209 [+0,187 a +0,228] · 7 de 7 |
| G3, temblor de 0.1 m | 0,788 · +0,018 [+0,010 a +0,027] · 6 de 7 | 0,820 · +0,034 [+0,025 a +0,043] · 7 de 7 | 0,736 · +0,116 [+0,100 a +0,132] · 7 de 7 | 0,743 · +0,129 [+0,112 a +0,144] · 7 de 7 |
| G3, temblor de 0.2 m | 0,768 · -0,003 [-0,006 a +0,000] · 1 de 7 | 0,789 · +0,003 [-0,001 a +0,006] · 5 de 7 | 0,634 · +0,014 [+0,007 a +0,021] · 7 de 7 | 0,630 · +0,016 [+0,008 a +0,022] · 7 de 7 |

### Entre candidatos (diferencia de `spellF1`, el primero menos el segundo)

| comparación | flag, previo | flag, siguiente | control, previo | control, siguiente |
|---|---|---|---|---|
| G2 − E2 | +0,027 [+0,020 a +0,034] · 7 de 7 | +0,028 [+0,021 a +0,035] · 7 de 7 | +0,023 [+0,014 a +0,031] · 6 de 7 | +0,026 [+0,017 a +0,034] · 6 de 7 |
| G3 − E2 | +0,034 [+0,026 a +0,041] · 7 de 7 | +0,038 [+0,031 a +0,045] · 7 de 7 | +0,034 [+0,025 a +0,043] · 7 de 7 | +0,046 [+0,037 a +0,054] · 7 de 7 |
| G3 − G2 | +0,007 [+0,002 a +0,012] · 5 de 7 | +0,010 [+0,005 a +0,015] · 5 de 7 | +0,012 [+0,005 a +0,018] · 5 de 7 | +0,020 [+0,014 a +0,026] · 6 de 7 |

### Harness con el `D` propio, 7 partidos juntos, frente a `main`

Cada celda: `spellF1` · diferencia con `main` [intervalo del 5 al 95 % del bootstrap pareado] · en cuántos partidos gana a `main`. Votan las filas con «sí».

| balón en los `D` | condición | convención | vota | `main` | E2 dejando un partido fuera (sin voto) | G2 | G3 |
|---|---|---|---|---|---|---|---|
| tapado | como el ATD | flag | sí | 0,416 | 0,416 · -0,000 [-0,002 a +0,001] · 1 de 7 | 0,422 · +0,006 [+0,000 a +0,011] · 6 de 7 | 0,429 · +0,013 [+0,007 a +0,018] · 7 de 7 |
| tapado | como el ATD | control | sí | 0,616 | 0,615 · -0,001 [-0,002 a +0,001] · 1 de 7 | 0,620 · +0,004 [-0,003 a +0,012] · 4 de 7 | 0,631 · +0,015 [+0,008 a +0,022] · 7 de 7 |
| tapado | como el ATD, sin bloques | flag | sí | 0,433 | 0,433 · -0,000 [-0,002 a +0,001] · 1 de 7 | 0,436 · +0,003 [-0,002 a +0,008] · 6 de 7 | 0,441 · +0,008 [+0,002 a +0,014] · 5 de 7 |
| tapado | como el ATD, sin bloques | control | sí | 0,642 | 0,641 · -0,001 [-0,003 a +0,001] · 1 de 7 | 0,641 · -0,001 [-0,008 a +0,007] · 3 de 7 | 0,652 · +0,011 [+0,003 a +0,018] · 6 de 7 |
| a la vista | como el ATD | flag | sí | 0,391 | 0,390 · -0,001 [-0,003 a +0,000] · 3 de 7 | 0,403 · +0,013 [+0,007 a +0,018] · 6 de 7 | 0,410 · +0,019 [+0,013 a +0,025] · 7 de 7 |
| a la vista | como el ATD | control | sí | 0,569 | 0,568 · -0,001 [-0,002 a +0,001] · 2 de 7 | 0,587 · +0,019 [+0,011 a +0,026] · 7 de 7 | 0,599 · +0,030 [+0,022 a +0,037] · 7 de 7 |
| a la vista | como el ATD, sin bloques | flag | sí | 0,405 | 0,404 · -0,001 [-0,002 a +0,001] · 3 de 7 | 0,416 · +0,011 [+0,006 a +0,016] · 6 de 7 | 0,421 · +0,017 [+0,010 a +0,022] · 7 de 7 |
| a la vista | como el ATD, sin bloques | control | sí | 0,593 | 0,593 · -0,000 [-0,002 a +0,001] · 2 de 7 | 0,607 · +0,014 [+0,006 a +0,021] · 6 de 7 | 0,619 · +0,026 [+0,018 a +0,033] · 7 de 7 |
| tapado | limpio | flag | no | 0,443 | 0,442 · -0,000 [-0,001 a +0,000] · 2 de 7 | 0,446 · +0,003 [-0,003 a +0,008] · 5 de 7 | 0,451 · +0,008 [+0,002 a +0,014] · 6 de 7 |
| tapado | limpio | control | no | 0,659 | 0,658 · -0,001 [-0,002 a +0,000] · 1 de 7 | 0,659 · +0,000 [-0,006 a +0,008] · 4 de 7 | 0,668 · +0,010 [+0,003 a +0,018] · 6 de 7 |
| tapado | huecos y suavizado | flag | no | 0,393 | 0,392 · -0,001 [-0,002 a +0,000] · 1 de 7 | 0,398 · +0,006 [+0,001 a +0,011] · 5 de 7 | 0,406 · +0,013 [+0,007 a +0,019] · 6 de 7 |
| tapado | huecos y suavizado | control | no | 0,582 | 0,581 · -0,001 [-0,003 a +0,001] · 2 de 7 | 0,590 · +0,008 [+0,000 a +0,016] · 4 de 7 | 0,605 · +0,023 [+0,015 a +0,031] · 7 de 7 |

### Cuánto `D` ve cada versión en el harness (descriptivo)

| balón en los `D` | condición | versión | frames `D` reales vistos como `D` | de lo que dice `D`, es `D` | paradas vistas (≥ mitad de sus frames) |
|---|---|---|---|---|---|
| tapado | como el ATD | main (E2 del módulo, en muestra) | 89 % | 93 % | 629 de 713 (88 %) |
| tapado | como el ATD | E2 dejando un partido fuera (sin voto) | 89 % | 93 % | 628 de 713 (88 %) |
| tapado | como el ATD | G2 | 90 % | 95 % | 642 de 713 (90 %) |
| tapado | como el ATD | G3 | 90 % | 95 % | 640 de 713 (90 %) |
| tapado | como el ATD, sin bloques | main (E2 del módulo, en muestra) | 89 % | 94 % | 628 de 713 (88 %) |
| tapado | como el ATD, sin bloques | E2 dejando un partido fuera (sin voto) | 89 % | 94 % | 628 de 713 (88 %) |
| tapado | como el ATD, sin bloques | G2 | 90 % | 95 % | 643 de 713 (90 %) |
| tapado | como el ATD, sin bloques | G3 | 90 % | 95 % | 640 de 713 (90 %) |
| a la vista | como el ATD | main (E2 del módulo, en muestra) | 79 % | 93 % | 545 de 713 (76 %) |
| a la vista | como el ATD | E2 dejando un partido fuera (sin voto) | 79 % | 93 % | 544 de 713 (76 %) |
| a la vista | como el ATD | G2 | 84 % | 95 % | 587 de 713 (82 %) |
| a la vista | como el ATD | G3 | 85 % | 95 % | 589 de 713 (83 %) |
| a la vista | como el ATD, sin bloques | main (E2 del módulo, en muestra) | 79 % | 94 % | 545 de 713 (76 %) |
| a la vista | como el ATD, sin bloques | E2 dejando un partido fuera (sin voto) | 79 % | 94 % | 544 de 713 (76 %) |
| a la vista | como el ATD, sin bloques | G2 | 84 % | 95 % | 587 de 713 (82 %) |
| a la vista | como el ATD, sin bloques | G3 | 85 % | 95 % | 589 de 713 (83 %) |
| tapado | limpio | main (E2 del módulo, en muestra) | 89 % | 94 % | 628 de 713 (88 %) |
| tapado | limpio | E2 dejando un partido fuera (sin voto) | 89 % | 94 % | 628 de 713 (88 %) |
| tapado | limpio | G2 | 90 % | 95 % | 644 de 713 (90 %) |
| tapado | limpio | G3 | 90 % | 95 % | 639 de 713 (90 %) |
| tapado | huecos y suavizado | main (E2 del módulo, en muestra) | 89 % | 92 % | 628 de 713 (88 %) |
| tapado | huecos y suavizado | E2 dejando un partido fuera (sin voto) | 88 % | 92 % | 628 de 713 (88 %) |
| tapado | huecos y suavizado | G2 | 90 % | 94 % | 643 de 713 (90 %) |
| tapado | huecos y suavizado | G3 | 90 % | 94 % | 639 de 713 (90 %) |

### Lectura con la regla fijada antes de medir (docs/decisiones.md, 16/11)

- **G2, harness (+0.010 y 6 de 7 en las ocho celdas):** **no cumple** en 4 de 8 (tapado, como el ATD, flag; tapado, como el ATD, control; tapado, como el ATD, sin bloques, flag; tapado, como el ATD, sin bloques, control)
- **G2, criterio del 13/11 frente a E2:** **no empeora**
- **G3, harness (+0.010 y 6 de 7 en las ocho celdas):** **no cumple** en 1 de 8 (tapado, como el ATD, sin bloques, flag)
- **G3, criterio del 13/11 frente a E2:** **no empeora**
- **Ningún candidato gana: la idea 2.4 se cierra.**
