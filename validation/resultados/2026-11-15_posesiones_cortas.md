# Posesiones cortas: por qué predecimos menos posesiones de las que hay · 2026-11-15 · Claude (sesión de Ismael)

- **Fecha y quién:** 15/11/2026. Lo pidió Ismael al reabrir la evidencia de equipo («predecimos muchas menos
  posesiones de las que hay, sobretodo cuando son posesiones cortas»; `docs/decisiones.md`). Lo escribió y
  lo ejecutó Claude, en la rama `claude/posesiones-cortas-5e84f8`.
- **Datos:** los 7 partidos de la Bundesliga (Bassek et al., 2025, CC BY 4.0) con el balón «como el ATD», y
  la mitad de entrenamiento de SkillCorner (`lector.ENTRENAMIENTO`, 10 partidos de la A-League 2024/25,
  licencia MIT) con el balón «detectado». El examen de SkillCorner (`lector.EXAMEN`) no se ha tocado. Nada
  del partido.
- **Código:** `main` en `3b227c4` más `validation/posesiones_cortas/` (bitácora en su `BITACORA.md`). B5 con
  los coeficientes que no vieron cada partido en la DFL, y con los de la entrega en SkillCorner. El `D` de
  las etiquetas (oráculo), como el harness.
- **Es descriptivo:** no decide nada. Sirve para saber qué candidatos merece la pena escribir.

## Lectura corta

1. **Con el flag, la mitad del hueco es convención** [medido].
   - De las 3.061 posesiones del flag, 793 son toques del rival sin control y 699 son trozos del equipo que
     retiene, partidos por esos toques. `main` encuentra el 5 y el 9 %.
   - Las etiquetas del control, puntuadas como predicción contra el flag, sacan 0,648: es el techo de un
     método perfecto que exige control si la GT fuera el flag.
2. **Pero `main` saca un ritmo casi fijo, sea cual sea la GT** [medido]. Posesiones por minuto vivo:

   | | reales | `main` |
   |---|---|---|
   | DFL, control | 4,71 | 4,50 |
   | SkillCorner (también exige control) | 6,05 | 4,25 |
   | DFL, flag | 8,30 | 4,50 |
   | partido (la GT pública son 17 posesiones) | 4,2 | 3,7 |

   Si la GT del reto se parece a SkillCorner, nos faltan de verdad un 30 % [inferencia]. Si se parece al
   control de la DFL, el número cuadra y el fallo es dónde cambiamos.
3. **En las posesiones que no encontramos, la evidencia de B5 apunta al otro equipo durante casi toda la
   posesión** [medido]. En las que se pierden por «otro equipo», la suma de la evidencia a favor del equipo
   bueno es de −6 a −11 veces lo que cuesta meterlas, y solo el 1–3 % la paga. **Bajar el coste de cambio
   no las arregla:** hay que cambiar el signo de la evidencia.
4. **Lo que empuja en contra son las señales lentas** [medido]: el balón en ventanas de 151 frames, la
   velocidad de los equipos y la dispersión. Las señales rápidas (el más cercano y el balón en 1 y 13
   frames) van a favor, pero pesan diez veces menos.
5. **Las que «se funden con la de al lado» son una consecuencia** [medido]: su evidencia está bien (la paga
   el 90–99 %). Se funden porque falta la posesión corta del rival que va en medio.
6. **En las de menos de 2 s hay un límite de información** [medido]: dentro de ellas, el más cercano es del
   equipo bueno en el 49–57 % de los frames con balón, **también con el balón limpio**. No se pueden
   recuperar frame a frame. Lo que queda por ganar está en las de 2 a 10 s.
7. **Entrenar con tracking automático no lo arregla** [medido]: con los rasgos de B5 entrenados con todos los
   frames vivos de SkillCorner, y mirando en los mismos partidos (lo más optimista posible), las de 2 a 5 s
   siguen en el 29–30 % y el spellF1 pasa de 0,519 a 0,520–0,528. Limitan los rasgos, no las filas.
