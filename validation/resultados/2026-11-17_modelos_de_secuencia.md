# Redes de secuencia para la evidencia de equipo (B11 a B15) · 2026-11-17 · Claude (sesión de Ismael)

- **Qué es:** cinco redes que sustituirían a B5 como evidencia de equipo (`H` frente a `A`), todas apagadas, fuera de
  `pipeline.PIECES`. La entrega no cambia.
- **Datos:** solo abiertos. Se entrena en la DFL (7 partidos; cada partido se puntúa con el pliegue que no lo vio) y se
  comprueba en la mitad de entrenamiento de SkillCorner. El examen de SkillCorner solo se ha abierto para B12, por excepción de Ismael, y no pasó.
- **Regla:** la del límite de daño del 16/11, frente a `main` (`docs/decisiones.md`).
- **Rama:** `claude/serene-lumiere-16245d`. El detalle de cada una está en `docs/decisiones.md` (17/11) y las salidas, en
  `validation/secuencia/salidas/2026-11-17_*`.

## Las redes

| | qué ve | cómo |
|---|---|---|
| B11 | 12 canales por frame (proximidad al balón y forma, sin promediar) | convolucional dilatada de ±5 s |
| B12 | los mismos 12 canales a 5 Hz | GRU bidireccional de 16 sobre la parte entera |
| B13 | **las trayectorias**: cada jugador (posición, velocidad, posición respecto al balón, vecinos) y el balón, desde la dirección de ataque de cada equipo | codificador de conjuntos por equipo y GRU bidireccional de 32 a 5 Hz; entrenada también sin balón a trozos |
| B14 | lo de B13 más rasgos de control (co-movimiento y acercamiento al balón) | B13 con atención conjunta, entrenada con dominio aleatorizado como el ATD: jugadores degradados, tracklets cortados, fantasmas, balón con retraso, espejo |
| B15 | lo de B14 | B14 entrenada con la etiqueta de control en todos los frames vivos |
| B16 | lo de B14 | B15 entrenada también con SkillCorner `ENTRENAMIENTO` (comprobada en SkillCorner con validación cruzada) |
| B17 | lo de B14 | la media de los logits de B15 y B16, sin reentrenar |

Todas son antisimétricas por construcción (cambiar los equipos cambia el signo), predicen en numpy sin torch (comprobado:
la diferencia con torch es de 10⁻⁵ o menos) y se puntúan como B5.

## Resultados frente a `main` (DFL, las dos condiciones del balón que votan)

Diferencia de `spellF1` y en cuántos de 7 partidos gana. La regla pide, con control, +0,005 o más en las dos condiciones
y 6 de 7, con los dos modos del `D`; con el flag, no perder más de 0,005.

| | control, `D` de las etiquetas | control, `D` propio | flag | SkillCorner `ENTRENAMIENTO` (4 celdas) | posesiones (`main` 1.661; reales 1.736 control) |
|---|---|---|---|---|---|
| B11 | +0,012 (4) / +0,007 (4) | +0,023 (5) / +0,014 (5) | +0,10 (7) | pierde o empata | 1.989 |
| B12 | +0,034 (7) / +0,028 (**5**) | +0,034 (7) / +0,028 (**5**) | +0,05 (7) | gana las 4 (+0,011 a +0,014, 7–9 de 10); el EXAMEN no pasa (+0,004 a +0,009) | 1.774 |
| B13 | +0,021 (6) / +0,003 (4) | +0,025 (5) / +0,007 (3) | +0,09 (7) | pierde las 4 (−0,010 a −0,024) | 1.865 |
| B14 | **+0,048 (7) / +0,027 (7)** | **+0,053 (7) / +0,030 (7)** | +0,11 a +0,12 (7) | pierde o empata (−0,017 a +0,002) | 1.904 |
| **B15** | **+0,054 (7) / +0,042 (7)** | **+0,050 (7) / +0,035 (7)** | **+0,034 a +0,048 (6–7)** | +0,006 en las 4 (7, 6, 8 y 6 de 10) | 1.655 |
| **B16** | **+0,052 (7) / +0,043 (7)** | **+0,044 (7) / +0,034 (7)** | **+0,037 a +0,046 (6–7)** | +0,002 a +0,010 (6–7 de 10) | 1.686 |
| **B17** | **+0,061 (7) / +0,048 (7)** | **+0,055 (7) / +0,039 (6)** | **+0,038 a +0,049 (7)** | **+0,002 a +0,016 (6–8 de 10); 3 de 4 celdas** | 1.654 |

## Lectura

- **Resultado final: el examen de SkillCorner de B17 no pasa** (una sola vez, para la familia B15–B17): +0,020 y +0,019 con el `D` de las etiquetas (9 de 10), +0,009 (7 de 10) y +0,008 (**6 de 10**) con el propio. Falla una celda por el «7 de 10». **B15–B17 se quedan cerrados y apagados.** En Metrica, B15–B17 sacan +0,021 a +0,030; K2, +0,035 (dos proveedores). En la DFL, B17 y K2 empatan; en SkillCorner, K2 va por delante.
- **En dos frases:** con el límite de daño (la regla de esta ronda), ninguna pasa SkillCorner `ENTRENAMIENTO` (B15, B16 y B17 cumplen 2, 1 y 3 de las 4 celdas), así que el examen no se abre. Con §5.8 (la regla de lo que gana con las dos convenciones), B15, B16 y B17 ganan a `main` en la DFL; decidir cuál manda es de Ismael y de la planificadora. B17 se hizo después de ver B15 y B16 en `ENTRENAMIENTO`, y esa mitad la han leído siete candidatos: su 3 de 4 es optimista.
- **B15, B16 y B17 ganan a `main` con §5.8 en la DFL** (+0,03 o más con las dos convenciones, 6–7 de 7, los dos modos del `D`). **B17 (la media de B15 y B16) es la más fuerte:** +0,039 a +0,061 con control y +0,038 a +0,049 con el flag, y en SkillCorner `ENTRENAMIENTO` cumple 3 de las 4 celdas del límite de daño (falla una con +0,002 y 6 de 10). Siguiente paso, si Ismael lo decide: el examen de SkillCorner para B17 (una vez) y la entrega de prueba (`python validation/partido/probar_entrega.py prueba_b17 --pieza candidates=aprendida.evidence_b17`, con el python del entorno limpio y `--contra` con la ruta de `equipo_v9.csv`). Ojo: puntúan unas 6 veces más fuerte que B5, así que la capa de los contraataques pesaría poco a su lado.
- **B15 gana a `main` con la regla de §5.8 en la DFL** (+0,03 o más con control y con el flag, 6–7 de 7, con los dos modos del `D`), el primer candidato que lo consigue desde B5. En SkillCorner `ENTRENAMIENTO` es positiva en las cuatro celdas (+0,006) pero no llega al «7 de 10» en dos. Entrenar con la etiqueta de control quitó los cambios de equipo de sobra de B14. El examen de SkillCorner de B15 y la entrega de prueba quedan para la decisión de Ismael. B16 (B15 entrenada también con SkillCorner) se está entrenando.
- **Ninguna pasa la regla, de momento.** **B14 es la primera que pasa los puntos 1 y 3 en la DFL, con margen** (7 de 7 en
  todo), pero en SkillCorner pierde con el `D` de las etiquetas y empata con el propio. B12 es la otra que más se acerca (gana con control en las cuatro celdas y en SkillCorner `ENTRENAMIENTO`, pero en «sin bloques» gana en 5 de 7). Ismael le hizo la excepción y **su examen de SkillCorner no pasa**: +0,004 a +0,009, falla una celda (+0,004 y 6 de 10). B12 queda cerrado y el examen, usado para B12.
- **Las redes que miran más fino (B11 y B13) cambian de equipo de más.** Ganan mucho con el flag (+0,09 a +0,10), que
  cambia en el primer toque, pero poco con control y pierden en SkillCorner. Predicen demasiadas posesiones. B15 ataca
  justo eso: aprende de los toques breves del rival que no son un cambio.
- **B14 generaliza mejor por frame que B13** en el partido que no ve (95,3 % frente a 93,8 % en J03WMX). Las copias como
  el ATD ayudan.

## Cómo seguir desde otro ordenador

Todo es con datos abiertos (`MTAH_OPEN_DATA_DIR` o `~/mtah2027-datos-abiertos`, con la caché de la DFL y SkillCorner).
Los pesos están en el repo: `possession/secuencia_pesos.npz` (B11, B12), `possession/trayectorias_pesos.npz` (B13) y,
`possession/trayectorias2_pesos.npz` (B14), `possession/trayectorias2_b15_pesos.npz` (B15) y `possession/trayectorias2_b16_pesos.npz` (B16; B17 usa los de B15 y B16).

- **Medir sin entrenar:** `python validation/harness/puntuar.py --versiones validation/harness/versiones/b14_trayectorias2_2026-11-17.json --d oraculo`
  (y `--d propio`); `python validation/secuencia/skillcorner.py --candidatos b14`.
- **Volver a entrenar B14/B15** (torch en CPU; en esta máquina, unas 2 h por pliegue con 3 en paralelo):
  1. `python validation/trayectorias/exportar2.py` y `python validation/trayectorias/paquetes.py` (y
     `etiquetas_control.py` para B15);
  2. `python validation/trayectorias/entrenar2.py <pliegue>` (B14) o `... <pliegue> --control` (B15), con
     `<pliegue>` en `todos`, `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ` y `J03WR9`;
  3. `python validation/secuencia/juntar.py b14` (α) y `python validation/secuencia/juntar.py escribir --modelos b14`.
- **Pruebas sin datos:** `python validation/scripts/prueba_secuencia.py` (B11 y B12) y `python validation/scripts/prueba_trayectorias.py` (B13 a B17: interfaz, antisimetría exacta, determinismo, orden de los slots y tope de la velocidad del balón). Las dos dan «Todo bien».
- **Entrega de prueba** (solo si algo pasa la regla y su examen; la ejecuta una persona):
  `python validation/partido/probar_entrega.py prueba_bNN --pieza candidates=aprendida.evidence_bNN`.
