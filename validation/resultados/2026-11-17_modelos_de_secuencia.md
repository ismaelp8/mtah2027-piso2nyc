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
| B15 | (pendiente) | | | | |

## Lectura

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
cuando estén, `possession/trayectorias2_pesos.npz` (B14) y `possession/trayectorias2_b15_pesos.npz` (B15).

- **Medir sin entrenar:** `python validation/harness/puntuar.py --versiones validation/harness/versiones/b14_trayectorias2_2026-11-17.json --d oraculo`
  (y `--d propio`); `python validation/secuencia/skillcorner.py --candidatos b14`.
- **Volver a entrenar B14/B15** (torch en CPU; en esta máquina, unas 2 h por pliegue con 3 en paralelo):
  1. `python validation/trayectorias/exportar2.py` y `python validation/trayectorias/paquetes.py` (y
     `etiquetas_control.py` para B15);
  2. `python validation/trayectorias/entrenar2.py <pliegue>` (B14) o `... <pliegue> --control` (B15), con
     `<pliegue>` en `todos`, `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ` y `J03WR9`;
  3. `python validation/secuencia/juntar.py b14` (α) y `python validation/secuencia/juntar.py escribir --modelos b14`.
- **Prueba sin datos:** `python validation/scripts/prueba_secuencia.py` (B11 y B12).
- **Entrega de prueba** (solo si algo pasa la regla y su examen; la ejecuta una persona):
  `python validation/partido/probar_entrega.py prueba_bNN --pieza candidates=aprendida.evidence_bNN`.
