# El juego vivo en el saque de cada parte: entra, y la entrega no cambia

- **Fecha y quién:** 15/11/2026. Lo ejecutó Ana en local; el script y la lectura son de la sesión de Claude de Ana.
- **Datos:** el ATD y el Smart Tagging del partido, en `MTAH_DATA_DIR`. Solo agregados del partido entero.
- **Código:** la rama `feat/d-instante-reinicio` en `03fe7e8`, sin cambios locales en el código de la entrega. La
  regla de lectura se subió a GitHub en ese commit, antes de ejecutar el script: `docs/decisiones.md`, entrada «`D` ·
  juego vivo en el saque de cada parte: regla escrita antes de regenerar la entrega» (15/11).
- **Entorno:** Python 3.10.12 y numpy 2.2.4 (no es el entorno limpio de la entrega). La entrega sin el ancla sale con el
  sha256 de `equipo_v5`, así que el entorno la reproduce.
- **Comando:** `python3 validation/partido/agregados_saque_juego_vivo.py`
- **Para qué:** decidir, con la regla fijada antes, si entra el ancla de la tarea 4 del plan: `D` prohibido en el frame
  del saque de cada parte.
- **Lectura en tres líneas:**
  1. **Entra:** se cumplen las seis condiciones de la regla [medido].
  2. **No cambia ningún frame:** con el ancla, la entrega es byte a byte `equipo_v5` (`27dc8aa8…efb7`). La entrega ya
     salía del `D` en el frame de los dos saques; el ancla solo deja fijada esa frontera [medido].
  3. **No hay rebote ni conflictos:** las posesiones (103 y 116), las paradas (53 y 60) y las rachas cortas de cada
     tramo no se mueven, y no hay ningún frame con piezas en conflicto [medido].

La salida, tal cual. Solo falta la línea del prompt de la terminal.

```
python 3.10.12, numpy 2.2.4
código: commit 03fe7e8, sin cambios locales en el código de la entrega
pipeline: piezas {"ball": "clean", "candidates": "aprendida.evidence_b5", "dead_state": "evidence", "temporal": "decode"}   costes {"from_dead": 25.0, "switch": 25.0, "to_dead": 25.0}
capas de la entrega, además de dead_ball.evidence: transiciones.evidence_equipo
huellas: modelo de Ana def73c1ebf2b   código de possession/ bb963526df2a
regla: D prohibido en el frame del saque de cada parte; entra si sin el ancla sale la entrega vigente (equipo_v5, sha256 27dc8aa8…efb7); con el ancla, ningún frame evaluado con piezas en conflicto; cada parte tiene su saque y en él no hay D; dentro de la banda; en cada tramo no suben las posesiones, las paradas ni las rachas cortas; lo que cambia cae en los 60 s después del saque de su parte

1. La entrega, sin el ancla y con ella (sin escribir ningún fichero)
   sha256 sin el ancla 27dc8aa8fec6f6089148f10b418c0a49ef22035dc06e7989860b7328f7a8efb7   ¿es la vigente (equipo_v5)? sí
   sha256 con el ancla 27dc8aa8fec6f6089148f10b418c0a49ef22035dc06e7989860b7328f7a8efb7
   frames evaluados con piezas en conflicto: sin el ancla 0   con ella 0
   saques en su tramo: 1 y 1   frames del saque con D, con el ancla: 0
   D en lo evaluado: sin el ancla 45.09 %   con ella 45.09 %   paradas: 113 y 113   dentro de la banda (15–60 % y ≤ 250 paradas): sí
   tramo 1: posesiones 103 y 103   paradas 53 y 53   sube con el ancla: nada
   tramo 2: posesiones 116 y 116   paradas 60 y 60   sube con el ancla: nada

2. Lo que cambia con el ancla (las dos partes juntas)
   frames evaluados que cambian de etiqueta: 0   antes del saque de su parte: 0   a 60 s o más después: 0
   de D a juego 0   de juego a D 0   de un equipo al otro 0
   frames que cambian, por distancia después del saque de su parte:
      0 a 1 s        0
      1 a 5 s        0
      5 a 30 s       0
      30 a 60 s      0
      ≥ 60 s         0

3. La regla
   sin el ancla sale la entrega vigente (equipo_v5, sha256 27dc8aa8…efb7)   sí
   con el ancla, ningún frame evaluado con piezas en conflicto              sí
   cada parte tiene su saque y en él no hay D                               sí
   dentro de la banda                                                       sí
   en cada tramo no suben las posesiones, las paradas ni las rachas cortas  sí
   lo que cambia cae en los 60 s después del saque de su parte              sí

-> entra el ancla del saque: sí
```
