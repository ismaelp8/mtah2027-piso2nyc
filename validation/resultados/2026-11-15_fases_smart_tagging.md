# ¿Sirven las fases del Smart Tagging como pista de equipo? (15/11/2026)

- **Quién:** Antonio Azuero (ejecución local), con Claude.
- **Para qué:** la tarea 2 de Antonio en `docs/PLAN_ENTREGA.md` §3 (P7 de la revisión externa), con el sí de
  Ismael del 15/11.
- **Datos:** el ATD y el Smart Tagging del partido, y la entrega `equipo_v3`. Solo agregados.
- **Regla y detalle:** `validation/fases_smart_tagging/BITACORA.md`. La regla se subió antes de ejecutar
  (`7d8a2ca`), y la lectura está en su §6.
- **Comandos:**

  ```bash
  python -m possession.pipeline --name equipo_v3          # con MTAH_DATA_DIR; sha256 9539ce42…cc17a
  python validation/partido/fases_smart_tagging.py --entrega evaluation/results/equipo_v3.csv --data-dir <datos>
  ```

**Lectura en tres líneas:**

1. **La regla del plan se cumple, por poco:** 81,8 % de acuerdo en control claro, con un desacuerdo del 18,2 %
   frente al 44,2 % del placebo. Pero hay un 13,5 % de frames solapados con equipos distintos, más del 10 %:
   hay que revisar la tabla antes de usar nada. El sentido de ataque y defensa está bien, porque las fases
   salen a pares idénticos.
2. **Con el alcance del plan, la pista vale poco:** como mucho cambiaría 1.455 frames sin balón, menos del 1 %
   de los evaluados.
3. **Lo que más promete son las transiciones:** en 19 de los 24 inicios de «Attacking Transition» (79 %),
   nuestra entrega sigue en el otro equipo y no cambia en 2 s (en el placebo, el 28 %). Es la fase más fiable:
   un 93,1 % de acuerdo. Un uso así se sale del plan: lo decide Ismael.

## Salida tal cual

```
Fases del Smart Tagging como pista de equipo (validation/fases_smart_tagging/BITACORA.md): frames evaluados, las dos partes juntas

0. Controles
   frames evaluados: 158857   con balón: 94214
   fases en el fichero: 638   en la tabla, con Team H o A: 571
   entrega: sha256 9539ce42…cc17a   ¿es equipo_v3? sí

1. La tabla (bitácora §2): por código, instancias, Team N/A, frames con fase y acuerdo en control claro
   attacking transition           ataque    inst   24  N/A    0  frames    3850  control    508  acuerdo  93,1 %
   ball in final third            ataque    inst   93  N/A    0  frames   49561  control   5119  acuerdo  86,7 %
   ball in the box                ataque    inst   72  N/A    0  frames   23400  control   1851  acuerdo  72,0 %
   build up                       ataque    inst   22  N/A    0  frames    5491  control   1084  acuerdo  87,8 %
   creating chances               ataque    inst   30  N/A  < 5  frames   19164  control   1747  acuerdo  72,5 %
   long ball                      ataque    inst   29  N/A    0  frames    6533  control    612  acuerdo  79,9 %
   players in the box             ataque    inst   97  N/A    0  frames   61044  control   4577  acuerdo  75,1 %
   progression                    ataque    inst   66  N/A    0  frames   28472  control   4583  acuerdo  92,0 %
   defending in attacking third   defensa   inst   22  N/A    0  frames    5491  control   1084  acuerdo  87,8 %
   defending in defensive third   defensa   inst   30  N/A  < 5  frames   19164  control   1747  acuerdo  72,5 %
   defending in middle third      defensa   inst   66  N/A    0  frames   28472  control   4583  acuerdo  92,0 %
   defensive transition           defensa   inst   24  N/A    0  frames    3850  control    508  acuerdo  93,1 %
   goals                          fuera     inst  < 5  N/A    0  frames       0  control      0  acuerdo       –
   set pieces                     fuera     inst   59  N/A    0  frames       0  control      0  acuerdo       –

2. Frames solapados con equipos distintos (descriptivo; sospechoso por encima del 10 %)
   frames evaluados con fase: 108185   solapados con equipos distintos: 14610 (13,5 %)
   ¿sospechoso? sí

3. La regla del plan: acuerdo en control claro (mismo equipo a 1 m durante 25 frames)
   frames de control claro: 16560   con fase: 10256 (61,9 %)
   acuerdo con las fases reales: 81,8 %
   placebo (fases desplazadas):
       -480 s   con fase    9778   acuerdo 53,2 %
       -360 s   con fase    9831   acuerdo 58,8 %
       -240 s   con fase   10419   acuerdo 60,9 %
       +240 s   con fase    9349   acuerdo 54,9 %
       +360 s   con fase    9107   acuerdo 49,1 %
       +480 s   con fase    8351   acuerdo 58,3 %
   desacuerdo: reales 18,2 %   placebo, media 44,2 %
   → ENTRA (empujón pequeño, solo sin balón): acuerdo llega a el 80 %; desacuerdo no pasa de la mitad del del placebo

4. Transiciones (descriptivo): inicios de ATTACKING TRANSITION y nuestra entrega a ±2 s
   inicios en tramos evaluados, con Team H o A: 24
   cambio a ese equipo a ±2 s       reales  < 5 (      –)   placebo    9 de 133 (6,8 %)
   sin cambio, ya era ese equipo    reales  < 5 (      –)   placebo   30 de 133 (22,6 %)
   era el otro equipo               reales   19 ( 79,2 %)   placebo   37 de 133 (27,8 %)
   era D o X                        reales  < 5 (      –)   placebo   57 de 133 (42,9 %)
   de los cambios a ±2 s, desde el otro equipo: < 5   desde D: 0
   desfase de nuestro cambio respecto al inicio: -2 a -1 s 0   -1 a +0 s 0   +0 a +1 s 0   +1 a +2 s < 5

5. Alcance del empujón (descriptivo): frames evaluados sin balón que no son D en la entrega
   frames: 9941   con equipo de fase: 6525 (65,6 %)   con nuestra etiqueta del otro equipo: 1455 (22,3 %)

   tiempo 4 s
```
