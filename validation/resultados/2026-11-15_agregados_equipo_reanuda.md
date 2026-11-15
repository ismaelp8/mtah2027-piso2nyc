# Agregados del partido para la capa del equipo que reanuda

- **Fecha y quién:** 15/11/2026. Lo ejecutó Manuel en local; el script y la lectura son de la sesión de
  Claude de Manuel.
- **Datos:** el ATD, sus metadatos y el Smart Tagging del partido, en `MTAH_DATA_DIR`. Solo agregados del
  partido entero.
- **Código:** la rama `feat/d-equipo-reanuda` en `28565ce`. La regla de lectura se subió a GitHub en ese
  commit, antes de ejecutar el script: `docs/decisiones.md`, entrada «`D` · el equipo que reanuda» (15/11).
- **Comando:** `python validation/partido/agregados_equipo_reanuda.py`
- **Para qué:** decidir con la regla fijada antes si entra la capa del equipo que reanuda de
  `possession/dead_ball.py`.
- **Lectura en tres líneas:**
  1. **El `Team` del Smart Tagging es fiable** en córners y saques de puerta: coincide con la física en 20 de
     20 [medido].
  2. **La capa no entra:** no arregla ninguna salida y hace daño (retrasa 3 cambios, añade 2 posesiones y
     1 parada, y pasa 220 frames de juego a `D`) [medido].
  3. **Descriptivo:** sin la capa, el pipeline sale de 12 de las 25 paradas con el equipo contrario al del
     `Team`. No se sabe si es el pipeline o la forma de medir la salida [inferencia].

La salida, tal cual. Solo se han quitado las líneas del prompt de PowerShell y los espacios al final de
línea.

```
limpieza del balón: ball.clean (pipeline.PIECES)

1. ¿El Team es el equipo que saca? (física, sin etiquetas)
   ventanas con el Team de un equipo, en lo evaluado: 27   corner kick 12   free kick 5   goal kick 10
   lado izquierdo (x pequeña), lo defiende: parte 1: el local (medias de x separadas 12.4 m)   parte 2: el visitante (medias de x separadas 12.1 m)
   corner kick    coincide 11   no coincide 0   sin balón de esta parada 1   fuera del cuarto final 0
                  de las que deciden, punto con menos de 1 s: 0   con 1 s o más: 11
   goal kick      coincide 9   no coincide 0   sin balón de esta parada 0   fuera del cuarto final 1
                  de las que deciden, punto con menos de 1 s: 8   con 1 s o más: 1
   córner y saque de puerta juntos: coinciden 20 de 20 que deciden (100.0 %)
   regla: deciden ≥ 10 y coinciden ≥ 90 % -> se cumple: sí

2. ¿Aporta algo? Equipo con el que sale el pipeline de la parada de cada ventana, frente al Team
   frames con piezas en conflicto: sin la capa 0   con ella 0
   sin la capa  el del Team 13   el otro 12   sin parada 2   sin salida 0
   con la capa  el del Team 13   el otro 12   sin parada 2   sin salida 0
   ventana a ventana: arregladas (del otro al del Team) 0   rotas (al revés) 0
   regla: arregla ≥ 1 y más de las que rompe -> se cumple: no

3. ¿Hace daño?
   paradas borradas 0   cambios al otro equipo retrasados 3
   posesiones y paradas: sin la capa 215 y 113   con ella 217 y 114
   frames evaluados que cambian: de un equipo al otro 84   de juego a D 220   de D a juego 0
   regla: ni borra paradas, ni retrasa cambios, ni añade posesiones o paradas -> se cumple: no

-> la capa entra: no

   tiempo 8 s
```
