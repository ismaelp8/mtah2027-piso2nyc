# ¿Caen los huecos del balón del ATD en los cambios más que al azar? (H3 y H5) · 2026-11-15 · Ismael (ejecución local), con Claude

- **Fecha y quién:** 15/11/2026. Lo decidió la sesión principal a partir de las hipótesis H3 y H5 del visionado
  de la ventana pública. Claude escribió el script y la regla; Ismael lo ejecutó en local y pegó la salida.
- **Datos:** el ATD del partido y la entrega vigente (`equipo_v3`), solo agregados del partido entero. Como
  referencia, los 7 partidos de la DFL (Bassek et al., 2025, CC BY 4.0) con el balón «como el ATD». Nada de la
  ventana pública.
- **Código:** `python validation/partido/huecos_y_cambios.py <entrega>` (rama `claude/posesiones-fase4`, regla en
  `validation/posesiones_cortas/BITACORA.md` §14, commit `41c3c23` antes de ejecutar). Definiciones en
  `validation/posesiones_cortas/huecos.py`.

## Lectura con la regla

**No concluye: no se abre nada antes de la entrega.** [medido]

- **R** (cuánto se juntan nuestros cambios con los huecos del balón, frente al azar): 1,19 en el partido y 1,20
  en la DFL. El cociente es 0,99.
- **F** (qué parte de los huecos de 0,5 a 15 s acaba con otro equipo después): en el partido, por debajo de la
  DFL (28,1 %). El cociente no pasa de 1,25.
- **Los dos cocientes apuntan a «se cierra»,** pero solo 6 de nuestros cambios caen junto a un hueco, y la regla
  pedía 20.
- **Lo que sí se ve** [medido]:
  - en pleno juego, el ATD casi no pierde el balón: 37 huecos, 14 de ellos de 0,5 s o menos;
  - la mayor parte (113) va pegada a nuestras paradas;
  - de nuestros 103 cambios directos de equipo, 97 caen lejos de un hueco.
- **Lo que no dice:** los cambios son los nuestros, no los reales. Si en un cambio real el balón desaparece y
  nosotros no cambiamos en absoluto, aquí no se ve.

## Una celda pequeña que el script dejó ver

La primera ejecución imprimió F del partido como un porcentaje de 23 huecos que deja deducir un recuento de 1 a
4 casos. La tabla ya lo ocultaba como «< 5». Las normas de `validation/partido/README.md` piden ocultar esas
celdas.
- Es un recuento del partido entero, no un dato por frame.
- **Se corrigió el script:** F no se imprime si sale de 1 a 4 casos. La prueba
  (`validation/scripts/prueba_huecos.py`) cubre el caso.
- **Abajo, esas dos cifras van ocultas.**

## Salida, tal cual (salvo las dos cifras de F del partido, ocultas)

```text
# Nuestros cambios de equipo y los huecos del balón (H3; regla en validation/posesiones_cortas/BITACORA.md §14)

Entrega: equipo_v3.csv

### Partido (ATD y la entrega)

| duración del hueco en juego | huecos | decimos otro equipo después | de esos: cambio dentro del hueco | de esos: cambio al reaparecer (≤ 0,5 s) |
|---|---|---|---|---|
| ≤ 0,5 s | 14 | 0 (0,0 %) | – | – |
| 0,5–2 s | 0 | 0 (–) | – | – |
| 2–5 s | 0 | 0 (–) | – | – |
| 5–15 s | 23 | < 5 (–) | – | 0,0 % |
| > 15 s | 0 | 0 (–) | – | – |

Huecos pegados a un `D` nuestro o al borde de un tramo (no cuentan): 113.

| nuestros cambios `H`↔`A` | cuántos | % | al azar (% de los frames de juego) |
|---|---|---|---|
| todos | 103 | – | – |
| dentro de un hueco en juego de ≥ 0,5 s | 6 | 5,8 % | 4,6 % |
| al reaparecer tras uno de esos (≤ 0,5 s) | 0 | 0,0 % | 0,3 % |
| en otro sitio | 97 | 94,2 % | – |

M (dentro o al reaparecer) = 5,8 % de los cambios; al azar, 4,9 %; R = M / azar = 1,19.
F: menos de 5 casos, no se imprime.   [oculta a posteriori]

### Referencia: DFL, 7 partidos, «como el ATD», `main` con nuestro `D` (huecos al azar)

| duración del hueco en juego | huecos | decimos otro equipo después | de esos: cambio dentro del hueco | de esos: cambio al reaparecer (≤ 0,5 s) |
|---|---|---|---|---|
| ≤ 0,5 s | 65 | 1 (1,5 %) | 0,0 % | 100,0 % |
| 0,5–2 s | 0 | 0 (–) | – | – |
| 2–5 s | 16 | 6 (37,5 %) | 100,0 % | 0,0 % |
| 5–15 s | 151 | 41 (27,2 %) | 95,1 % | 4,9 % |
| > 15 s | 13 | 8 (61,5 %) | 87,5 % | 12,5 % |

Huecos pegados a un `D` nuestro o al borde de un tramo (no cuentan): 699.

| nuestros cambios `H`↔`A` | cuántos | % | al azar (% de los frames de juego) |
|---|---|---|---|
| todos | 948 | – | – |
| dentro de un hueco en juego de ≥ 0,5 s | 88 | 9,3 % | 7,8 % |
| al reaparecer tras uno de esos (≤ 0,5 s) | 5 | 0,5 % | 0,4 % |
| en otro sitio | 855 | 90,2 % | – |

M (dentro o al reaparecer) = 9,8 % de los cambios; al azar, 8,2 %; R = M / azar = 1,20.
F = 28,1 % de los 167 huecos en juego de 0,5 a 15 s tienen otro equipo después.

## Regla de BITACORA.md §14

R del partido = 1,19; R de la DFL = 1,20; cociente = 0,99,
F del partido: menos de 5 casos, no se imprime; F de la DFL = 28,1 %; el cociente no pasa de 1,25.   [oculta a posteriori]
**No concluye:** menos de 20 casos (cambios junto a un hueco, o huecos de 0,5 a 15 s).
```
