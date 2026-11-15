# Agregados del partido para las capas de `dead_ball.py`: de gol a saque y el hueco antes de cada reinicio

- **Fecha y quién:** 15/11/2026. Lo ejecutó Manuel en local; el script y la lectura son de la sesión de
  Claude de Manuel.
- **Datos:** el ATD y el Smart Tagging del partido, en `MTAH_DATA_DIR`. Solo agregados del partido entero.
- **Código:** la rama `feat/d-fronteras` en `e677893`. La regla de lectura se subió a GitHub en ese commit,
  antes de ejecutar el script: `docs/decisiones.md`, entrada «`D` · fronteras y anclas» (14/11).
- **Comando:** `python validation/partido/agregados_dead_ball.py`
- **Para qué:** decidir con la regla fijada antes si entran las dos capas medidas de
  `possession/dead_ball.py`.
- **Lectura en tres líneas:**
  1. **De gol a saque no entra:** no ancla ninguno de los 4 goles, y las ventanas `GOALS` duran 169 s de
     mediana [medido]. Parecen llegar hasta el saque [inferencia: comparando esa mediana con la de 168 s del
     inicio de `GOALS` al saque, del 14/11]. Además, el control falla, porque en el tramo antes del
     saque de la 2ª parte (`D` seguro) el balón del ATD va deprisa el 46,7 % del tiempo visto, frente al
     50,5 % del partido [medido].
  2. **El hueco antes de cada reinicio entra:** cobertura 52,8 % (≥ 50 %), placebo 23,3 % (el doble,
     46,6 %, queda por debajo) y el modelo de Ana ve `D` en el 84,5 % de los huecos, por encima del punto
     medio (71,0 %) entre el partido (47,4 %) y el control (94,6 %) [medido]. Con márgenes justos.
  3. **Descriptivo:** en los primeros 5 s de los huecos el modelo de Ana solo ve `D` en el 60,9 %; el
     `Team` de los 27 `SET PIECES` que lo traen coincide siempre con un nombre del ATD (16 local, 11
     visitante).

La salida, tal cual. Solo se han quitado las líneas del prompt de PowerShell y los espacios al final de
línea. Los saltos de línea de en medio de algunas filas de la sección 2 son del terminal, que las partió al
copiarlas.

```
limpieza del balón: ball.clean (pipeline.PIECES)

1. De cada gol a su saque
   goles 4   saques tras gol 4   goles que anclan 0 de 4
   frames anclados (evaluados), sumados: 0 (  0.0 % de los evaluados)
   duración de las ventanas GOALS, mediana: 169 s
   anclas duras si entrara la capa (también el tramo antes del saque): 2934 frames (  1.8 % de los evaluados)   fuera de los evaluados 0

2. ¿Cada tramo anclado se comporta como balón muerto?
   balón deprisa (≥ 5 m/s a 1 s) en el partido: 50.5 % de los frames con balón visto; un tramo falla por encima del 25.3 %
   pruebas: tramo entero, y 5 s desde 1 s dentro de cada borde; deciden con ≥ 25 frames de balón visto
   tramos anclados 0   pasan 0   fallan 0   no deciden 0
   fallos por prueba: tramo entero 0   borde inicial 0   borde final 0
   bordes que no deciden (ahí la frontera queda sin comprobar): inicial 0 ((a))   final 0 ((b))
   control (tramo antes del saque de la 2ª parte): falla
   placebo (desplazados -480/-360/-240/+240/+360/+480 s): 0 tramos, deciden 0, fallan 0 (  —   de los que deciden)
   partido entero (evaluados)                      158857 frames   balón visto  59.3 %   deprisa  50.5 % de los vistos

              jugadores (m/s) p10=0.70  p50=1.50  p90=2.94   modelo de Ana: D en el 47.4 %
   tramo antes del saque de la 2ª parte (D, FAQ)     2934 frames   balón visto  80.8 %   deprisa  46.7 % de los vistos

              jugadores (m/s) p10=0.87  p50=1.20  p90=1.70   modelo de Ana: D en el 94.6 %
   de gol a saque (anclado)
                    0 frames   balón visto   —     deprisa   —   de los vistos

              jugadores (m/s) sin datos   modelo de Ana: D en el —
   regla: el control pasa no   el placebo tiene potencia no   ningún tramo falla y la mitad o más pasan no   -> la capa entra: no

3. Equipo de los SET PIECES frente a los nombres de los metadatos del ATD
   SET PIECES 59   con equipo 27   igual al local 16   igual al visitante 11   sin coincidir 0

4. El hueco sin balón antes de cada reinicio (no se cuentan los saques iniciales)
   ventanas que empiezan en frames evaluados: 53
   hueco 28 ( 52.8 %)   balón visto 23 ( 43.4 %)   hueco largo 0 (  0.0 %)   reinicio dentro 2 (  3.8 %)
      throw-in               n= 26   con hueco 13 ( 50.0 %)
      corner kick            n= 12   con hueco 11 ( 91.7 %)
      goal kick              n= 10   con hueco 2 ( 20.0 %)
      free kick              n=  5   con hueco 2 ( 40.0 %)
   placebo (inicios desplazados -480/-360/-240/+240/+360/+480 s): 279 inicios, con hueco 65 ( 23.3 %)
   duración de los huecos (n=28)
      < 10 s           8  ( 28.6 %)
      10 a 20 s       10  ( 35.7 %)
      20 a 40 s        9  ( 32.1 %)
      ≥ 40 s           1  (  3.6 %)
   frames de hueco (evaluados), sumados: 12588 (  7.9 % de los evaluados)
   control del modelo de Ana: el tramo antes del saque
   modelo de Ana, D en: partido 47.4 %   control 94.6 %   punto medio 71.0 %   huecos 84.5 %   primeros 5 s de los huecos 60.9 %
   modelo de Ana en los huecos, por grupo (descriptivo): córner y falta (n=13) 90.2 %   banda y saque de puerta (n=15) 75.1 %
   jugadores (m/s) en los huecos: p10=0.57  p50=1.00  p90=1.73
   regla: cobertura ≥ 50 % sí   ≥ 2 veces el placebo sí   el modelo de Ana separa el control del partido sí   huecos ≥ punto medio sí   -> la capa entra: sí

   tiempo 6 s
```
