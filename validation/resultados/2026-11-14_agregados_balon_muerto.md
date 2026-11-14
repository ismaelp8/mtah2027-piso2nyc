# Agregados del partido para el detector de `D`: fronteras y anclas

- **Fecha y quién:** 14/11/2026. Los ejecutó Manuel en local; los scripts son de Ana (commit `0b8be4d`, sin
  cambios después) y la lectura, de la sesión de Claude de Manuel.
- **Datos:** el ATD y el Smart Tagging del partido, en `MTAH_DATA_DIR`. Solo agregados del partido entero.
- **Comandos:** los tres de abajo, desde la raíz del repo.
- **Para qué:** decidir cómo usa cada señal la pieza de fronteras y anclas (`possession/dead_ball.py`), con
  la regla escrita antes de ejecutarlos: `docs/decisiones.md`, entrada «`D` · fronteras y anclas» (14/11).
  Ahí están la regla, la decisión y lo que la regla no preveía.
- **Lectura en tres líneas:**
  1. Las ventanas `SET PIECES` duran 35 s fijos (5 s los saques iniciales) y el golpeo cae más de 5 s antes
     de su fin en las 53 de banda, córner, saque de puerta y falta [medido]: el fin de la ventana no es el
     reinicio [inferencia].
  2. El golpeo coincide a ±1 s con la subida de velocidad de los jugadores como mucho en el 60 % de un tipo
     (R1 no entra), y solo 6 de las 48 ventanas de banda, córner y saque de puerta (12,5 %) tienen una
     salida del balón justo antes (la capa 3 no entra).
  3. Los 4 goles tienen su saque etiquetado después; en los 30 s finales de cada parte los jugadores van a
     1,15 y 0,81 m/s de mediana; el `Team` viene en córner, saque de puerta y falta, y nunca en banda ni
     en los saques iniciales.

La salida, tal cual. Solo se han quitado las líneas del prompt de PowerShell y los espacios al final de
línea. En un punto, el copiado pegó el final de un script con el comando del siguiente; aquí van
separados.

## `python validation/partido/agregados_smart_tagging.py`

```
instancias 638   SET PIECES 59   GOALS 4   otras fases 575

1. Ventanas SET PIECES por tipo: duración y Team N/A
   throw-in               n= 26   duración (s) p10=35.00  p50=35.00  p90=35.00   Team N/A 26 (100.0 %)
      duración en intervalos (n=26)
         < 2 s            0  (  0.0 %)
         2 a 5 s          0  (  0.0 %)
         5 a 10 s         0  (  0.0 %)
         10 a 20 s        0  (  0.0 %)
         ≥ 20 s          26  (100.0 %)
   corner kick            n= 12   duración (s) p10=35.00  p50=35.00  p90=35.00   Team N/A 0 (  0.0 %)
      duración en intervalos (n=12)
         < 2 s            0  (  0.0 %)
         2 a 5 s          0  (  0.0 %)
         5 a 10 s         0  (  0.0 %)
         10 a 20 s        0  (  0.0 %)
         ≥ 20 s          12  (100.0 %)
   goal kick              n= 10   duración (s) p10=35.00  p50=35.00  p90=35.00   Team N/A 0 (  0.0 %)
      duración en intervalos (n=10)
         < 2 s            0  (  0.0 %)
         2 a 5 s          0  (  0.0 %)
         5 a 10 s         0  (  0.0 %)
         10 a 20 s        0  (  0.0 %)
         ≥ 20 s          10  (100.0 %)
   kick off (todos)       n=  6   duración (s) p10=5.00  p50=5.00  p90=5.00   Team N/A 6 (100.0 %)
      duración en intervalos (n=6)
         < 2 s            0  (  0.0 %)
         2 a 5 s          0  (  0.0 %)
         5 a 10 s         6  (100.0 %)
         10 a 20 s        0  (  0.0 %)
         ≥ 20 s           0  (  0.0 %)
   free kick              n=  5   duración (s) p10=35.00  p50=35.00  p90=35.00   Team N/A 0 (  0.0 %)
      duración en intervalos (n=5)
         < 2 s            0  (  0.0 %)
         2 a 5 s          0  (  0.0 %)
         5 a 10 s         0  (  0.0 %)
         10 a 20 s        0  (  0.0 %)
         ≥ 20 s           5  (100.0 %)

2. Cobertura de los frames evaluados por las fases
   alguna fase (no SET PIECES)     108185 frames ( 68.1 %)
   alguna ventana SET PIECES        43899 frames ( 27.6 %)
   fase o ventana                  118915 frames ( 74.9 %)
   ninguna etiqueta                 39942 frames ( 25.1 %)
   huecos sin ninguna etiqueta, duración (n=74)
      < 2 s            9  ( 12.2 %)
      2 a 5 s         12  ( 16.2 %)
      5 a 10 s        14  ( 18.9 %)
      10 a 30 s       25  ( 33.8 %)
      ≥ 30 s          14  ( 18.9 %)
   frames en huecos de ≥ 5 s: 38674 ( 24.3 % de los evaluados)

3. GOALS → siguiente Kick Off (After Goal), todos los goles juntos
   goles 4   con saque posterior etiquetado 4   saques tras gol etiquetados 4
   frames entre gol y saque, sumados: 16403 ( 10.3 % de los evaluados)   mediana 168 s

4. Primera fase posterior a cada ventana SET PIECES: inicio de la fase − fin de la ventana
   throw-in               n= 26   con fase en los 30 s siguientes 26
      desfase (negativo: la fase empieza dentro de la ventana) (n=26)
         < -5 s          21  ( 80.8 %)
         -5 a -2.5 s      1  (  3.8 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         2  (  7.7 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            2  (  7.7 %)
   corner kick            n= 12   con fase en los 30 s siguientes 12
      desfase (negativo: la fase empieza dentro de la ventana) (n=12)
         < -5 s          10  ( 83.3 %)
         -5 a -2.5 s      1  (  8.3 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            1  (  8.3 %)
   goal kick              n= 10   con fase en los 30 s siguientes 10
      desfase (negativo: la fase empieza dentro de la ventana) (n=10)
         < -5 s           9  ( 90.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        1  ( 10.0 %)
         ≥ 5 s            0  (  0.0 %)
   kick off (todos)       n=  6   con fase en los 30 s siguientes 6
      desfase (negativo: la fase empieza dentro de la ventana) (n=6)
         < -5 s           0  (  0.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         1  ( 16.7 %)
         0 a 1 s          1  ( 16.7 %)
         1 a 2.5 s        1  ( 16.7 %)
         2.5 a 5 s        1  ( 16.7 %)
         ≥ 5 s            2  ( 33.3 %)
   free kick              n=  5   con fase en los 30 s siguientes 5
      desfase (negativo: la fase empieza dentro de la ventana) (n=5)
         < -5 s           5  (100.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
```

## `python validation/partido/agregados_balon_reinicios.py`

```
2. Las reanudaciones del detector de golpeo frente a tres señales independientes
   (desfase = reanudación − señal, en segundos; negativo: la reanudación cae antes)
   throw-in               n= 26   reanudación encontrada 26 (100.0 %)
      frente al FIN de la ventana SET PIECES (n=26)
         < -5 s          26  (100.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
      frente al inicio de la primera fase posterior (n=26)
         < -5 s           9  ( 34.6 %)
         -5 a -2.5 s      3  ( 11.5 %)
         -2.5 a -1 s      4  ( 15.4 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          2  (  7.7 %)
         1 a 2.5 s        2  (  7.7 %)
         2.5 a 5 s        2  (  7.7 %)
         ≥ 5 s            4  ( 15.4 %)
      frente a la subida de velocidad de los jugadores (n=24)
         < -5 s          11  ( 45.8 %)
         -5 a -2.5 s      6  ( 25.0 %)
         -2.5 a -1 s      2  (  8.3 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        3  ( 12.5 %)
         2.5 a 5 s        1  (  4.2 %)
         ≥ 5 s            1  (  4.2 %)
   corner kick            n= 12   reanudación encontrada 12 (100.0 %)
      frente al FIN de la ventana SET PIECES (n=12)
         < -5 s          12  (100.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
      frente al inicio de la primera fase posterior (n=12)
         < -5 s           5  ( 41.7 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         1  (  8.3 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        1  (  8.3 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            5  ( 41.7 %)
      frente a la subida de velocidad de los jugadores (n=12)
         < -5 s           2  ( 16.7 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         2  ( 16.7 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        2  ( 16.7 %)
         2.5 a 5 s        5  ( 41.7 %)
         ≥ 5 s            1  (  8.3 %)
   goal kick              n= 10   reanudación encontrada 10 (100.0 %)
      frente al FIN de la ventana SET PIECES (n=10)
         < -5 s          10  (100.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
      frente al inicio de la primera fase posterior (n=10)
         < -5 s           3  ( 30.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         1  ( 10.0 %)
         0 a 1 s          2  ( 20.0 %)
         1 a 2.5 s        3  ( 30.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            1  ( 10.0 %)
      frente a la subida de velocidad de los jugadores (n=9)
         < -5 s           8  ( 88.9 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        1  ( 11.1 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
   kick off (todos)       n=  6   reanudación encontrada 5 ( 83.3 %)
      frente al FIN de la ventana SET PIECES (n=5)
         < -5 s           0  (  0.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      2  ( 40.0 %)
         -1 a 0 s         3  ( 60.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
      frente al inicio de la primera fase posterior (n=5)
         < -5 s           1  ( 20.0 %)
         -5 a -2.5 s      2  ( 40.0 %)
         -2.5 a -1 s      1  ( 20.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          1  ( 20.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
      frente a la subida de velocidad de los jugadores (n=5)
         < -5 s           0  (  0.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      1  ( 20.0 %)
         -1 a 0 s         2  ( 40.0 %)
         0 a 1 s          1  ( 20.0 %)
         1 a 2.5 s        1  ( 20.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
   free kick              n=  5   reanudación encontrada 5 (100.0 %)
      frente al FIN de la ventana SET PIECES (n=5)
         < -5 s           5  (100.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)
      frente al inicio de la primera fase posterior (n=5)
         < -5 s           0  (  0.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         0  (  0.0 %)
         0 a 1 s          0  (  0.0 %)
         1 a 2.5 s        0  (  0.0 %)
         2.5 a 5 s        2  ( 40.0 %)
         ≥ 5 s            3  ( 60.0 %)
      frente a la subida de velocidad de los jugadores (n=4)
         < -5 s           0  (  0.0 %)
         -5 a -2.5 s      0  (  0.0 %)
         -2.5 a -1 s      0  (  0.0 %)
         -1 a 0 s         1  ( 25.0 %)
         0 a 1 s          2  ( 50.0 %)
         1 a 2.5 s        1  ( 25.0 %)
         2.5 a 5 s        0  (  0.0 %)
         ≥ 5 s            0  (  0.0 %)

3. El balón que desaparece saliendo del campo
   huecos sin balón de ≥ 2 s que empiezan en frames evaluados: 133
   de ellos, con el último punto a ≤ 2 m de una línea y ≥ 1 m/s hacia fuera (salidas): 24 ( 18.0 %)   por banda 13   por fondo 11
   salidas seguidas de una ventana SET PIECES en ≤ 30 s: 16 ( 66.7 %)
   segundos de la salida al inicio de esa ventana (n=16)
      < 2 s            0  (  0.0 %)
      2 a 5 s          2  ( 12.5 %)
      5 a 10 s         4  ( 25.0 %)
      10 a 20 s        5  ( 31.2 %)
      ≥ 20 s           5  ( 31.2 %)
   throw-in               n= 26   con una salida en los 15 s previos: 5 ( 19.2 %)
   corner kick            n= 12   con una salida en los 15 s previos: 1 (  8.3 %)
   goal kick              n= 10   con una salida en los 15 s previos: 0 (  0.0 %)
   kick off (todos)       n=  6   con una salida en los 15 s previos: 1 ( 16.7 %)
   free kick              n=  5   con una salida en los 15 s previos: 1 ( 20.0 %)

5. Columna de velocidad del balón del ATD frente al desplazamiento suavizado
   frames comparables 7361
   columna del ATD        p10=0.44  p50=1.32  p90=3.69
   desplazamiento a 1 s   p10=0.58  p50=4.88  p90=11.73   correlación 0.08   cociente de medianas columna/suavizado 0.27

   tiempo 6 s
```

## `python validation/partido/agregados_jugadores.py`

```
4. Velocidad media de los jugadores (m/s, media móvil de 2 s)
   slots vistos por frame en los evaluados: p10=18.00  p50=22.00  p90=22.00
   referencia DFL (7 partidos)  en D p10/p50/p90 = 0.53 / 1.02 / 1.69   en juego = 1.38 / 2.27 / 3.62
   todos los frames evaluados                                  158857 frames   p10=0.70  p50=1.50  p90=2.94   < 1.2 m/s  35.4 %
   parte 1: 30 s iniciales del bloque evaluado                    750 frames   p10=1.78  p50=2.59  p90=4.06   < 1.2 m/s   1.6 %
   parte 1: 30 s finales del bloque evaluado                      751 frames   p10=0.11  p50=1.15  p90=1.85   < 1.2 m/s  52.7 %
   parte 2: 30 s iniciales del bloque evaluado                    750 frames   p10=0.89  p50=1.30  p90=1.65   < 1.2 m/s  33.9 %
   parte 2: 30 s finales del bloque evaluado                      751 frames   p10=0.61  p50=0.81  p90=1.50   < 1.2 m/s  87.2 %
   throw-in (n=26): 10 s antes de la ventana                     6500 frames   p10=0.80  p50=1.33  p90=2.56   < 1.2 m/s  44.2 %
   throw-in (n=26): 5 s después de la ventana                    3250 frames   p10=0.96  p50=1.69  p90=2.83   < 1.2 m/s  24.5 %
   corner kick (n=12): 10 s antes de la ventana                  3000 frames   p10=0.52  p50=0.84  p90=1.15   < 1.2 m/s  91.2 %
   corner kick (n=12): 5 s después de la ventana                 1500 frames   p10=1.04  p50=1.49  p90=3.38   < 1.2 m/s  25.8 %
   goal kick (n=10): 10 s antes de la ventana                    2500 frames   p10=0.67  p50=1.72  p90=3.37   < 1.2 m/s  35.6 %
   goal kick (n=10): 5 s después de la ventana                   1250 frames   p10=0.90  p50=1.97  p90=3.08   < 1.2 m/s  18.6 %
   kick off (todos) (n=6): 10 s antes de la ventana              1500 frames   p10=0.28  p50=0.80  p90=1.14   < 1.2 m/s  93.7 %
   kick off (todos) (n=6): 5 s después de la ventana              750 frames   p10=0.84  p50=2.01  p90=3.39   < 1.2 m/s  16.7 %
   free kick (n=5): 10 s antes de la ventana                     1250 frames   p10=0.46  p50=0.83  p90=1.48   < 1.2 m/s  73.0 %
   free kick (n=5): 5 s después de la ventana                     625 frames   p10=0.75  p50=1.12  p90=2.17   < 1.2 m/s  55.4 %
   todos los reinicios: 10 s antes de la ventana                14750 frames   p10=0.59  p50=1.05  p90=2.44   < 1.2 m/s  59.8 %
   todos los reinicios: 5 s después de la ventana                7375 frames   p10=0.95  p50=1.71  p90=2.96   < 1.2 m/s  25.6 %
   fracción de jugadores a menos de 1 m/s (media de 2 s), en los evaluados: p10=0.08  p50=0.29  p90=0.74

6. Jugadores fuera de los límites del campo (más de 0.3 m)
   frames evaluados con ninguno jugador(es) fuera:  141374 ( 89.0 %)
   frames evaluados con uno jugador(es) fuera:   14250 (  9.0 %)
   frames evaluados con dos jugador(es) fuera:    2181 (  1.4 %)
   frames evaluados con tres o más fuera:          1052 (  0.7 %)
   de los frames con alguno fuera: por banda  80.2 %   por fondo  22.3 %
   throw-in               n= 26   ventanas (desde 5 s antes) con algún jugador fuera 22 ( 84.6 %)   segundos con alguien fuera por ventana p10=0.00  p50=6.74  p90=15.28
   corner kick            n= 12   ventanas (desde 5 s antes) con algún jugador fuera 11 ( 91.7 %)   segundos con alguien fuera por ventana p10=0.86  p50=4.26  p90=11.57
   goal kick              n= 10   ventanas (desde 5 s antes) con algún jugador fuera 7 ( 70.0 %)   segundos con alguien fuera por ventana p10=0.00  p50=1.00  p90=9.76
   kick off (todos)       n=  6   ventanas (desde 5 s antes) con algún jugador fuera 0 (  0.0 %)   segundos con alguien fuera por ventana p10=0.00  p50=0.00  p90=0.00
   free kick              n=  5   ventanas (desde 5 s antes) con algún jugador fuera 4 ( 80.0 %)   segundos con alguien fuera por ventana p10=2.75  p50=7.72  p90=12.18

   tiempo 5 s
```
