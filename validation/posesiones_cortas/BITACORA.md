# Posesiones cortas: por qué predecimos menos posesiones de las que hay · bitácora

> Sale de la reapertura de la evidencia de equipo (Ismael, 15/11; `docs/decisiones.md`). Solo datos
> abiertos de otros partidos: la DFL (Bassek et al., 2025, CC BY 4.0) y SkillCorner (A-League 2024/25,
> licencia MIT), solo la mitad `lector.ENTRENAMIENTO` hasta que haya un candidato cerrado. Lo puede ejecutar
> Claude. Solo agregados. Rama `claude/posesiones-cortas-5e84f8`.

## 1. Las preguntas, por orden

1. ¿Cuánto de «predecimos de menos» es convención y cuánto es modelo?
2. ¿Qué le falta a la evidencia en un cambio real? Cuánto margen da B5 dentro de las posesiones reales
   cortas frente a lo que cuesta meterlas (dos cambios de 25), y qué distingue a las que se funden con la de
   al lado.
3. ¿Qué información queda sin usar?
4. Dos o tres candidatos, escritos y subidos con su regla antes de medirlos.

## 2. Diagnóstico descriptivo (preguntas 1 y 2)

`python validation/posesiones_cortas/diagnostico.py`. **No decide nada:** no hay regla previa, sirve para
elegir qué candidatos escribir. Usa el pipeline de `main` con el `D` de las etiquetas, como el harness.

Primera salida, tal cual: `salidas/2026-11-15_diagnostico_v1.md` (código `3b227c4` más estos scripts).
**Dos etiquetas de esa salida exageran** (revisión del 15/11) y se corrigen en la siguiente:
- «solo en el flag» no son solo toques del rival: el emparejamiento uno a uno deja sin pareja también los
  trozos del equipo que retiene a cada lado del toque. Hay que partirlas por equipo;
- el grupo «jugadores» mezcla la posición en el campo (sus dos pesos mayores: «balón en la dirección de
  ataque, ventana 51» y «juego en la dirección de ataque, sin balón cerca») con la velocidad y la dispersión.

## 3. Sondeo de información por frame

`python validation/posesiones_cortas/informacion.py`; salida en `salidas/2026-11-15_informacion_v1.md`.
Descriptivo. Lo que dice [medido]: dentro de las posesiones del flag de menos de 2 s, el más cercano es del
equipo bueno en el 49–57 % de los frames con balón, **también con el balón limpio**. Suavizar a los
jugadores igual que el balón no cambia nada (±1 punto). Lo que no dice: nada del instante del cambio, que
es donde el suavizado sí borra la proximidad (anexo A.4 de la revisión externa: del 94 al 56–63 %).
