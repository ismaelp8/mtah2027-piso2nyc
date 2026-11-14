# Harness de la DFL con la degradación «como el ATD»: la tabla de referencia de nuevo · 2026-11-14 · Claude (sesión de Ismael)

> Paso 3 de «Ismael» (`docs/PLAN_ENTREGA.md` §4, cambio del 14/11). La degradación se calibra con el perfil
> del balón del ATD (`2026-11-14_perfil_atd.md`) y la regla de lectura fijada antes de medir. El cambio de
> forma lo decidió Ismael con el perfil delante («Como el ATD»), y está escrito en
> `validation/perfil_atd/BITACORA.md` §9.1 y §9.2 antes de volver a leer. Solo agregados de datos
> abiertos. Cada afirmación lleva **[medido]**, **[inferencia]** o **[sin verificar]**.

**En pocas líneas:**

1. **Con la forma nueva, la regla deja `DISPUTAS` 0, y decide él** [medido]. Cuadran R1', R2 (ahora
   también la severidad alta), R3' y R5, y el suavizado sale de 25 frames.
   - La severidad alta pide tapar el 11,3 % de los frames vivos en bloques de 5 a 15 s.
   - Las severidades baja y media no identifican `OBJETIVO` (§9.2).
   - Lo que puede decidir el harness pasa a «se puede decidir»: el orden entre evidencias de equipo por
     proximidad y lo que use la velocidad del balón.
2. **Votan dos condiciones:** «como el ATD», con los bloques de 5 a 15 s, y «como el ATD, sin bloques».
   Acotan lo que el perfil no puede medir: si los huecos largos que el ATD tiene de más son juego o
   paradas. «limpio» y la condición de antes del perfil («huecos y suavizado») se puntúan sin voto.
3. **«como el ATD» reproduce el perfil del ATD** [medido]:
   - huecos de 5 s o más: 111,1 por 90 minutos, frente a 111,3;
   - `s` alta: 15,66 % frente a 15,67 %;
   - el reparto de los huecos de hasta 15 s es parecido;
   - toques: 3,7 por minuto frente a 3,3.

   **No reproduce** el % de disputas (20,3 frente a 14,5) ni la visibilidad total (48,2 % frente a
   59,3 %), porque la DFL tiene más `D` (44,8 %) que lo que le falta al ATD [medido].

   **Ojo: casi todo esto es calibración, no comprobación.**
   - Calibrado: R1' ajusta la `s` alta; la ley de huecos y el ritmo de los microcortes se copiaron del
     ATD; el suavizado lo eligió R4'.
   - Comprobaciones independientes: R5 (proximidad), que cuadra, y R3' (disputas), que solo pasa por el
     margen ensanchado.
   - Las disputas son justo donde se separan las evidencias de equipo por proximidad. Que la DFL tenga
     más que el ATD puede favorecer a esas evidencias en el harness [inferencia].
4. **Con el flag, el Viterbi de coste 25 (el de `main`) gana al baseline en las dos condiciones que
   votan** [medido]: +0,022 [+0,013 a +0,030] en 7 de 7 partidos y +0,022 [+0,015 a +0,029] en 6 de 7.
   - Con la condición de antes perdía (−0,022). Parte de la conclusión del 14/11 («con el flag empata o
     pierde») venía de una degradación mucho más dura que el ATD [inferencia].
   - No llega al +0,03 de §5.8. Con las etiquetas de control gana por +0,11.
   - Con la regla de §5.8 sigue sin ganar ninguna versión: «empate o no concluye».
5. **Frente a la versión de `main` (coste 25)** [medido]:
   - el coste 100 pierde;
   - 12 y 50 empatan;
   - el 50 queda casi igual con las etiquetas de control (+0,007 y +0,015) y pierde con el flag (−0,063
     y −0,065);
   - el 12 pierde con las dos convenciones.
6. **En los eventos humanos** (descriptivo), subir el coste sigue siendo un compromiso [medido]: gana en
   los duelos sin cambio y pierde en las recuperaciones y en los duelos con cambio. Frente al baseline,
   el coste 25 «mejora» con «como el ATD» y es «compromiso» sin bloques.

- **Código:**
  - `validation/harness/dfl.py`: `CONDICIONES`, `VOTAN`, `PARAMETROS_DE` y la forma «atd» en
    `degradar_con` y `mascara_como_el_atd`;
  - `validation/harness/puntuar.py`;
  - `validation/perfil_atd/leer_atd.py --forma atd`.
- **Datos:** los 7 partidos de la Bundesliga (Bassek et al., 2025, CC BY 4.0) y sus XML de eventos.
  Nada del partido, salvo los agregados ya publicados del perfil del ATD.
- **Comandos:**
  - `python validation/perfil_atd/leer_atd.py <salida del ATD> --forma atd`: la regla;
  - `python validation/harness/puntuar.py --eventos`: la tabla, con bootstrap de 1.000 remuestreos y
    semilla fija. Dos ejecuciones dan la misma salida.

## 1. La regla con la forma «atd»

| `DISPUTAS` | baja: R1' / R2 | media: R1' / R2 | R3' | ¿queda? | distancia al ATD |
|---|---|---|---|---|---|
| 0 | sí / sí | sí / sí | sí | **sí** | 3,66 |
| 0,25 | sí / no | no / no | sí | no | 9,46 |
| 0,5 | no / no | no / no | sí | no | 11,61 |
| 0,75 | no / no | no / no | sí | no | 16,45 |
| 1 | no / no | no / no | no | no | 22,83 |

- **`OBJETIVO` de la severidad alta (R1'): 0,113** [medido], con R2 de la alta cuadrando en sus cuatro
  celdas. Los huecos de 5 a 15 s son el 76,8 % en la DFL y el 82,6 % en el ATD.
- **R4' y R5 con `OBJETIVO` 0,113** (repetidos aparte, porque la regla los calculó con el 0,41 de la media
  §9.2): suavizado de 25 frames, con 3,7 toques y 10,7 controles por minuto, frente a 3,3 y 12,2 del
  ATD. Proximidad: 29,8 / 45,6 / 70,1 % a 1 / 1,5 / 3 m o menos, frente a 28,2 / 41,8 / 65,7 %. Cuadra.
- **Ensayo de la forma nueva** (J03WR9 con `objetivo` 0,05, `disputas` 0 y suavizado 25 hace de ATD):
  - queda 0 y decide 0;
  - el suavizado sale 25;
  - la alta da 0,026 para el 0,05 plantado: se queda corta.

## 2. El perfil de las condiciones del harness, frente al ATD

[medido] Los 7 partidos de la DFL juntos, frente al ATD.

| condición | balón visible (%) | huecos de 5 s o más por 90 min | `s` alta (%) | reparto alta ≤ 0,5 / 0,5–2 / 2–5 / 5–15 s (%) | disputas (%) | toques/min |
|---|---|---|---|---|---|---|
| ATD | 59,3 | 111,3 | 15,67 | 16,3 / < 5 / < 5 / 82,6 | 14,5 | 3,3 |
| como el ATD | 48,2 | 111,1 | 15,66 | 15,8 / 0 / 7,5 / 76,7 | 20,3 | 3,7 |
| como el ATD, sin bloques | 54,4 | 88,2 | 9,09 | 24,3 / 0 / 12,5 / 63,3 | 20,5 | 3,8 |
| limpio | 54,5 | 88,2 | 9,05 | 0 / 0 / 16,5 / 83,5 | 21,3 | 38,6 |
| huecos y suavizado (la de antes) | 32,2 | 118,8 | 41,51 | 27,4 / 45,1 / 19,0 / 8,5 | 13,6 | 3,6 |

## 3. Lo que esta medida no dice

- **Si los huecos largos del ATD caen en juego o en paradas** [sin verificar]. Por eso votan dos
  condiciones.
- **El `D`.** Va copiado de las etiquetas, y el harness no tiene el modo con el equipo copiado de las
  etiquetas que prometía el plan.
- **La convención de la GT.** Sigue sin medir. Por eso se mide con las dos.
- **Las disputas.** La DFL ve más disputas que el ATD (20 % frente a 14,5 %). Puede ser que el ATD pierda el
  balón en ellas, o que vea menos jugadores [inferencia].

## Salida, tal cual

`python validation/harness/puntuar.py --eventos`:

```text
D: oraculo · partidos: 7 · bootstrap: 1000

### Con qué se mide

| etiquetas | posesiones | frames `D` |
|---|---|---|
| flag | 3061 | 44,8 % |
| control | 1736 | 44,8 % |

| balón | visible en los frames de juego (media de los partidos) |
|---|---|
| como el ATD | 87,3 % |
| como el ATD, sin bloques | 98,7 % |
| limpio (sin voto) | 98,7 % |
| huecos y suavizado (sin voto) | 58,3 % |

### Etiquetas: flag

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,406 | 0,369–0,443 | – | – | 2844 / 3061 | 0,805 |
| como el ATD | Viterbi, coste 12 | 0,401 | 0,379–0,434 | -0,005 [-0,013 a +0,004] | 4 de 7 | 3061 / 3061 | 0,791 |
| como el ATD | Viterbi, coste 25 (v0) | 0,428 | 0,378–0,476 | +0,022 [+0,013 a +0,030] | 7 de 7 | 1782 / 3061 | 0,807 |
| como el ATD | Viterbi, coste 50 | 0,365 | 0,314–0,421 | -0,041 [-0,053 a -0,029] | 0 de 7 | 1224 / 3061 | 0,806 |
| como el ATD | Viterbi, coste 100 | 0,286 | 0,221–0,344 | -0,120 [-0,134 a -0,107] | 0 de 7 | 921 / 3061 | 0,786 |
| como el ATD | Viterbi, coste elegido dejando un partido fuera | 0,428 | – | +0,022 | – | 1782 / 3061 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,435 | 0,405–0,479 | – | – | 2811 / 3061 | 0,819 |
| como el ATD, sin bloques | Viterbi, coste 12 | 0,419 | 0,396–0,454 | -0,015 [-0,023 a -0,007] | 2 de 7 | 3366 / 3061 | 0,801 |
| como el ATD, sin bloques | Viterbi, coste 25 (v0) | 0,456 | 0,415–0,507 | +0,022 [+0,015 a +0,029] | 6 de 7 | 1920 / 3061 | 0,820 |
| como el ATD, sin bloques | Viterbi, coste 50 | 0,392 | 0,334–0,446 | -0,043 [-0,055 a -0,031] | 0 de 7 | 1303 / 3061 | 0,821 |
| como el ATD, sin bloques | Viterbi, coste 100 | 0,305 | 0,238–0,357 | -0,130 [-0,144 a -0,117] | 0 de 7 | 954 / 3061 | 0,799 |
| como el ATD, sin bloques | Viterbi, coste elegido dejando un partido fuera | 0,456 | – | +0,022 | – | 1920 / 3061 | – |
| limpio (sin voto) | control: voto ±50 | 0,454 | 0,419–0,494 | – | – | 2726 / 3061 | 0,831 |
| limpio (sin voto) | Viterbi, coste 12 | 0,452 | 0,427–0,483 | -0,002 [-0,010 a +0,006] | 3 de 7 | 3079 / 3061 | 0,818 |
| limpio (sin voto) | Viterbi, coste 25 (v0) | 0,474 | 0,435–0,526 | +0,020 [+0,012 a +0,027] | 6 de 7 | 1871 / 3061 | 0,831 |
| limpio (sin voto) | Viterbi, coste 50 | 0,399 | 0,335–0,447 | -0,056 [-0,068 a -0,044] | 0 de 7 | 1297 / 3061 | 0,828 |
| limpio (sin voto) | Viterbi, coste 100 | 0,314 | 0,250–0,365 | -0,140 [-0,155 a -0,127] | 0 de 7 | 969 / 3061 | 0,806 |
| limpio (sin voto) | Viterbi, coste elegido dejando un partido fuera | 0,474 | – | +0,020 | – | 1871 / 3061 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,393 | 0,356–0,420 | – | – | 2944 / 3061 | 0,808 |
| huecos y suavizado (sin voto) | Viterbi, coste 12 | 0,381 | 0,350–0,424 | -0,012 [-0,021 a -0,003] | 2 de 7 | 2088 / 3061 | 0,785 |
| huecos y suavizado (sin voto) | Viterbi, coste 25 (v0) | 0,372 | 0,325–0,433 | -0,022 [-0,032 a -0,011] | 1 de 7 | 1382 / 3061 | 0,796 |
| huecos y suavizado (sin voto) | Viterbi, coste 50 | 0,320 | 0,270–0,362 | -0,073 [-0,085 a -0,060] | 0 de 7 | 1049 / 3061 | 0,794 |
| huecos y suavizado (sin voto) | Viterbi, coste 100 | 0,259 | 0,202–0,293 | -0,135 [-0,149 a -0,121] | 0 de 7 | 835 / 3061 | 0,772 |
| huecos y suavizado (sin voto) | Viterbi, coste elegido dejando un partido fuera | 0,381 | – | -0,012 | – | 2088 / 3061 | – |

### Etiquetas: control

| balón | versión | spellF1, 7 partidos | por partido, mín–máx | frente al control [5–95 %] | gana en | posesiones predichas / reales | acierto de equipo |
|---|---|---|---|---|---|---|---|
| como el ATD | control: voto ±50 | 0,464 | 0,440–0,494 | – | – | 2844 / 1736 | 0,823 |
| como el ATD | Viterbi, coste 12 | 0,418 | 0,368–0,440 | -0,045 [-0,054 a -0,037] | 0 de 7 | 3061 / 1736 | 0,806 |
| como el ATD | Viterbi, coste 25 (v0) | 0,580 | 0,564–0,609 | +0,116 [+0,106 a +0,127] | 7 de 7 | 1782 / 1736 | 0,828 |
| como el ATD | Viterbi, coste 50 | 0,587 | 0,537–0,637 | +0,123 [+0,106 a +0,140] | 7 de 7 | 1224 / 1736 | 0,838 |
| como el ATD | Viterbi, coste 100 | 0,505 | 0,435–0,561 | +0,042 [+0,020 a +0,062] | 6 de 7 | 921 / 1736 | 0,822 |
| como el ATD | Viterbi, coste elegido dejando un partido fuera | 0,580 | – | +0,116 | – | 1324 / 1736 | – |
| como el ATD, sin bloques | control: voto ±50 | 0,494 | 0,465–0,528 | – | – | 2811 / 1736 | 0,839 |
| como el ATD, sin bloques | Viterbi, coste 12 | 0,419 | 0,381–0,446 | -0,075 [-0,082 a -0,068] | 0 de 7 | 3366 / 1736 | 0,816 |
| como el ATD, sin bloques | Viterbi, coste 25 (v0) | 0,602 | 0,585–0,611 | +0,108 [+0,100 a +0,117] | 7 de 7 | 1920 / 1736 | 0,843 |
| como el ATD, sin bloques | Viterbi, coste 50 | 0,617 | 0,561–0,664 | +0,124 [+0,107 a +0,139] | 7 de 7 | 1303 / 1736 | 0,856 |
| como el ATD, sin bloques | Viterbi, coste 100 | 0,532 | 0,462–0,576 | +0,039 [+0,016 a +0,059] | 5 de 7 | 954 / 1736 | 0,838 |
| como el ATD, sin bloques | Viterbi, coste elegido dejando un partido fuera | 0,617 | – | +0,124 | – | 1303 / 1736 | – |
| limpio (sin voto) | control: voto ±50 | 0,524 | 0,483–0,573 | – | – | 2726 / 1736 | 0,851 |
| limpio (sin voto) | Viterbi, coste 12 | 0,470 | 0,428–0,509 | -0,054 [-0,061 a -0,047] | 1 de 7 | 3079 / 1736 | 0,833 |
| limpio (sin voto) | Viterbi, coste 25 (v0) | 0,629 | 0,604–0,649 | +0,106 [+0,097 a +0,114] | 7 de 7 | 1871 / 1736 | 0,855 |
| limpio (sin voto) | Viterbi, coste 50 | 0,635 | 0,576–0,675 | +0,112 [+0,096 a +0,127] | 7 de 7 | 1297 / 1736 | 0,864 |
| limpio (sin voto) | Viterbi, coste 100 | 0,545 | 0,480–0,590 | +0,022 [+0,000 a +0,042] | 5 de 7 | 969 / 1736 | 0,846 |
| limpio (sin voto) | Viterbi, coste elegido dejando un partido fuera | 0,628 | – | +0,105 | – | 1382 / 1736 | – |
| huecos y suavizado (sin voto) | control: voto ±50 | 0,448 | 0,422–0,515 | – | – | 2944 / 1736 | 0,830 |
| huecos y suavizado (sin voto) | Viterbi, coste 12 | 0,484 | 0,460–0,529 | +0,036 [+0,025 a +0,047] | 6 de 7 | 2088 / 1736 | 0,806 |
| huecos y suavizado (sin voto) | Viterbi, coste 25 (v0) | 0,574 | 0,545–0,607 | +0,126 [+0,111 a +0,141] | 7 de 7 | 1382 / 1736 | 0,828 |
| huecos y suavizado (sin voto) | Viterbi, coste 50 | 0,543 | 0,491–0,584 | +0,095 [+0,075 a +0,113] | 7 de 7 | 1049 / 1736 | 0,830 |
| huecos y suavizado (sin voto) | Viterbi, coste 100 | 0,470 | 0,399–0,520 | +0,022 [-0,000 a +0,043] | 5 de 7 | 835 / 1736 | 0,809 |
| huecos y suavizado (sin voto) | Viterbi, coste elegido dejando un partido fuera | 0,574 | – | +0,126 | – | 1382 / 1736 | – |

### Regla de §5.8 (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones)

- Viterbi, coste 12: **empate o no concluye**
- Viterbi, coste 25 (v0): **empate o no concluye**
- Viterbi, coste 50: **empate o no concluye**
- Viterbi, coste 100: **empate o no concluye**

### Frente a la versión de main («Viterbi, coste 25 (v0)»)

| etiquetas | balón | versión | frente a main [5–95 %] | gana en |
|---|---|---|---|---|
| flag | como el ATD | Viterbi, coste 12 | -0,027 [-0,036 a -0,017] | 2 de 7 |
| flag | como el ATD | Viterbi, coste 50 | -0,063 [-0,074 a -0,053] | 0 de 7 |
| flag | como el ATD | Viterbi, coste 100 | -0,142 [-0,155 a -0,128] | 0 de 7 |
| flag | como el ATD, sin bloques | Viterbi, coste 12 | -0,037 [-0,047 a -0,027] | 1 de 7 |
| flag | como el ATD, sin bloques | Viterbi, coste 50 | -0,065 [-0,075 a -0,054] | 0 de 7 |
| flag | como el ATD, sin bloques | Viterbi, coste 100 | -0,152 [-0,166 a -0,138] | 0 de 7 |
| flag | limpio (sin voto) | Viterbi, coste 12 | -0,022 [-0,031 a -0,011] | 1 de 7 |
| flag | limpio (sin voto) | Viterbi, coste 50 | -0,075 [-0,086 a -0,065] | 0 de 7 |
| flag | limpio (sin voto) | Viterbi, coste 100 | -0,160 [-0,174 a -0,147] | 0 de 7 |
| flag | huecos y suavizado (sin voto) | Viterbi, coste 12 | +0,009 [+0,001 a +0,018] | 4 de 7 |
| flag | huecos y suavizado (sin voto) | Viterbi, coste 50 | -0,051 [-0,060 a -0,042] | 0 de 7 |
| flag | huecos y suavizado (sin voto) | Viterbi, coste 100 | -0,113 [-0,125 a -0,101] | 0 de 7 |
| control | como el ATD | Viterbi, coste 12 | -0,162 [-0,172 a -0,150] | 0 de 7 |
| control | como el ATD | Viterbi, coste 50 | +0,007 [-0,007 a +0,019] | 3 de 7 |
| control | como el ATD | Viterbi, coste 100 | -0,075 [-0,094 a -0,056] | 0 de 7 |
| control | como el ATD, sin bloques | Viterbi, coste 12 | -0,183 [-0,195 a -0,172] | 0 de 7 |
| control | como el ATD, sin bloques | Viterbi, coste 50 | +0,015 [+0,001 a +0,030] | 5 de 7 |
| control | como el ATD, sin bloques | Viterbi, coste 100 | -0,070 [-0,091 a -0,050] | 0 de 7 |
| control | limpio (sin voto) | Viterbi, coste 12 | -0,160 [-0,171 a -0,149] | 0 de 7 |
| control | limpio (sin voto) | Viterbi, coste 50 | +0,006 [-0,008 a +0,020] | 4 de 7 |
| control | limpio (sin voto) | Viterbi, coste 100 | -0,084 [-0,104 a -0,065] | 0 de 7 |
| control | huecos y suavizado (sin voto) | Viterbi, coste 12 | -0,090 [-0,101 a -0,078] | 0 de 7 |
| control | huecos y suavizado (sin voto) | Viterbi, coste 50 | -0,031 [-0,045 a -0,019] | 0 de 7 |
| control | huecos y suavizado (sin voto) | Viterbi, coste 100 | -0,104 [-0,122 a -0,086] | 0 de 7 |

Regla de §5.8 frente a main (las condiciones que votan: «como el ATD», «como el ATD, sin bloques» y las dos convenciones):

- Viterbi, coste 12: **empate o no concluye**
- Viterbi, coste 50: **empate o no concluye**
- Viterbi, coste 100: **pierde**

### Eventos humanos (descriptivo; regla de lectura en validation/harness/README.md)

Puntos, con los partidos medidos juntos: 3142 pase completado, 195 recuperación, 229 duelo con cambio, 211 duelo sin cambio.

| balón | versión | pase completado | recuperación | duelo con cambio | duelo sin cambio |
|---|---|---|---|---|---|
| (todas) | etiquetas «flag» como predicción | 97,9 | 89,2 | 88,6 | 47,4 |
| (todas) | etiquetas «control» como predicción | 98,8 | 87,7 | 84,3 | 74,9 |
| como el ATD | control: voto ±50 | 89,5 | 84,1 | 82,5 | 55,0 |
| como el ATD | Viterbi, coste 12 | 89,3 | 84,1 | 84,3 | 59,7 |
| como el ATD | Viterbi, coste 25 (v0) | 90,9 | 84,1 | 80,8 | 62,1 |
| como el ATD | Viterbi, coste 50 | 91,1 | 76,4 | 69,4 | 71,1 |
| como el ATD | Viterbi, coste 100 | 88,4 | 67,7 | 59,0 | 75,8 |
| como el ATD, sin bloques | control: voto ±50 | 91,1 | 87,7 | 86,9 | 55,9 |
| como el ATD, sin bloques | Viterbi, coste 12 | 90,7 | 87,7 | 86,0 | 56,9 |
| como el ATD, sin bloques | Viterbi, coste 25 (v0) | 92,1 | 86,2 | 83,0 | 60,2 |
| como el ATD, sin bloques | Viterbi, coste 50 | 92,7 | 77,4 | 72,1 | 70,6 |
| como el ATD, sin bloques | Viterbi, coste 100 | 89,6 | 67,7 | 60,7 | 74,4 |
| limpio (sin voto) | control: voto ±50 | 93,1 | 91,3 | 88,2 | 55,5 |
| limpio (sin voto) | Viterbi, coste 12 | 93,2 | 89,2 | 87,8 | 60,7 |
| limpio (sin voto) | Viterbi, coste 25 (v0) | 94,0 | 86,7 | 84,3 | 63,5 |
| limpio (sin voto) | Viterbi, coste 50 | 93,9 | 77,9 | 74,2 | 72,5 |
| limpio (sin voto) | Viterbi, coste 100 | 90,7 | 68,2 | 62,0 | 74,4 |
| huecos y suavizado (sin voto) | control: voto ±50 | 88,9 | 84,6 | 77,7 | 59,7 |
| huecos y suavizado (sin voto) | Viterbi, coste 12 | 88,0 | 80,5 | 79,5 | 58,8 |
| huecos y suavizado (sin voto) | Viterbi, coste 25 (v0) | 89,4 | 76,9 | 72,5 | 64,5 |
| huecos y suavizado (sin voto) | Viterbi, coste 50 | 88,7 | 69,7 | 62,0 | 67,3 |
| huecos y suavizado (sin voto) | Viterbi, coste 100 | 85,7 | 64,1 | 55,0 | 68,7 |

Diferencias en puntos, [5–95 %]:

| balón | versión | frente a | recuperación | duelo con cambio | duelo sin cambio | lectura |
|---|---|---|---|---|---|---|
| como el ATD | Viterbi, coste 12 | control: voto ±50 | +0,0 [-4,1 a +4,1] | +1,7 [-1,3 a +5,2] | +4,7 [+0,0 a +9,0] | no concluye |
| como el ATD | Viterbi, coste 12 | Viterbi, coste 25 (v0) | +0,0 [-2,6 a +2,6] | +3,5 [+0,9 a +6,1] | -2,4 [-5,7 a +0,9] | mejora |
| como el ATD | Viterbi, coste 25 (v0) | control: voto ±50 | +0,0 [-3,1 a +3,1] | -1,7 [-4,4 a +0,9] | +7,1 [+3,3 a +10,9] | mejora |
| como el ATD | Viterbi, coste 50 | control: voto ±50 | -7,7 [-11,8 a -3,6] | -13,1 [-17,1 a -9,1] | +16,1 [+10,9 a +20,9] | compromiso |
| como el ATD | Viterbi, coste 50 | Viterbi, coste 25 (v0) | -7,7 [-11,3 a -4,1] | -11,4 [-15,3 a -7,4] | +9,0 [+4,7 a +12,8] | compromiso |
| como el ATD | Viterbi, coste 100 | control: voto ±50 | -16,4 [-21,5 a -11,3] | -23,6 [-28,8 a -18,3] | +20,9 [+14,7 a +26,5] | compromiso |
| como el ATD | Viterbi, coste 100 | Viterbi, coste 25 (v0) | -16,4 [-21,5 a -11,3] | -21,8 [-27,1 a -16,6] | +13,7 [+9,0 a +19,0] | compromiso |
| como el ATD, sin bloques | Viterbi, coste 12 | control: voto ±50 | +0,0 [-3,6 a +3,1] | -0,9 [-3,5 a +1,7] | +0,9 [-2,8 a +4,7] | no concluye |
| como el ATD, sin bloques | Viterbi, coste 12 | Viterbi, coste 25 (v0) | +1,5 [-1,0 a +4,1] | +3,1 [+0,4 a +5,3] | -3,3 [-6,6 a +0,0] | mejora |
| como el ATD, sin bloques | Viterbi, coste 25 (v0) | control: voto ±50 | -1,5 [-4,1 a +1,0] | -3,9 [-6,1 a -1,7] | +4,3 [+1,4 a +7,6] | compromiso |
| como el ATD, sin bloques | Viterbi, coste 50 | control: voto ±50 | -10,3 [-14,9 a -6,2] | -14,8 [-18,8 a -10,9] | +14,7 [+10,0 a +19,4] | compromiso |
| como el ATD, sin bloques | Viterbi, coste 50 | Viterbi, coste 25 (v0) | -8,7 [-12,3 a -5,1] | -10,9 [-14,8 a -7,4] | +10,4 [+6,2 a +14,2] | compromiso |
| como el ATD, sin bloques | Viterbi, coste 100 | control: voto ±50 | -20,0 [-25,1 a -14,9] | -26,2 [-31,4 a -21,4] | +18,5 [+12,8 a +24,2] | compromiso |
| como el ATD, sin bloques | Viterbi, coste 100 | Viterbi, coste 25 (v0) | -18,5 [-23,6 a -13,3] | -22,3 [-27,5 a -17,0] | +14,2 [+9,0 a +19,4] | compromiso |
| limpio (sin voto) | Viterbi, coste 12 | control: voto ±50 | -2,1 [-5,1 a +1,0] | -0,4 [-3,1 a +2,2] | +5,2 [+0,9 a +9,5] | mejora |
| limpio (sin voto) | Viterbi, coste 12 | Viterbi, coste 25 (v0) | +2,6 [+0,0 a +5,1] | +3,5 [+0,9 a +6,1] | -2,8 [-6,2 a +0,5] | mejora |
| limpio (sin voto) | Viterbi, coste 25 (v0) | control: voto ±50 | -4,6 [-7,2 a -2,1] | -3,9 [-6,6 a -1,3] | +8,1 [+4,3 a +11,4] | compromiso |
| limpio (sin voto) | Viterbi, coste 50 | control: voto ±50 | -13,3 [-17,4 a -9,2] | -14,0 [-18,3 a -10,0] | +17,1 [+12,3 a +21,3] | compromiso |
| limpio (sin voto) | Viterbi, coste 50 | Viterbi, coste 25 (v0) | -8,7 [-12,3 a -5,1] | -10,0 [-14,0 a -6,5] | +9,0 [+5,2 a +12,8] | compromiso |
| limpio (sin voto) | Viterbi, coste 100 | control: voto ±50 | -23,1 [-28,2 a -18,5] | -26,2 [-31,0 a -21,4] | +19,0 [+12,8 a +24,6] | compromiso |
| limpio (sin voto) | Viterbi, coste 100 | Viterbi, coste 25 (v0) | -18,5 [-23,6 a -13,3] | -22,3 [-27,1 a -17,5] | +10,9 [+5,7 a +16,1] | compromiso |
| huecos y suavizado (sin voto) | Viterbi, coste 12 | control: voto ±50 | -4,1 [-8,7 a +0,5] | +1,7 [-1,7 a +5,2] | -0,9 [-5,7 a +4,3] | no concluye |
| huecos y suavizado (sin voto) | Viterbi, coste 12 | Viterbi, coste 25 (v0) | +3,6 [+1,0 a +6,7] | +7,0 [+3,9 a +10,5] | -5,7 [-9,0 a -1,9] | compromiso |
| huecos y suavizado (sin voto) | Viterbi, coste 25 (v0) | control: voto ±50 | -7,7 [-12,8 a -3,1] | -5,2 [-9,2 a -0,9] | +4,7 [-0,9 a +10,4] | empeora |
| huecos y suavizado (sin voto) | Viterbi, coste 50 | control: voto ±50 | -14,9 [-20,5 a -9,2] | -15,7 [-21,0 a -10,5] | +7,6 [+1,4 a +13,7] | compromiso |
| huecos y suavizado (sin voto) | Viterbi, coste 50 | Viterbi, coste 25 (v0) | -7,2 [-10,8 a -3,1] | -10,5 [-14,0 a -7,4] | +2,8 [-0,5 a +6,2] | empeora |
| huecos y suavizado (sin voto) | Viterbi, coste 100 | control: voto ±50 | -20,5 [-26,7 a -14,4] | -22,7 [-28,8 a -16,6] | +9,0 [+2,4 a +15,6] | compromiso |
| huecos y suavizado (sin voto) | Viterbi, coste 100 | Viterbi, coste 25 (v0) | -12,8 [-17,9 a -7,7] | -17,5 [-22,7 a -12,7] | +4,3 [+0,0 a +8,5] | empeora |

Veredicto en las condiciones que votan: «como el ATD», «como el ATD, sin bloques» (descriptivo, no entra en §5.8):

- Viterbi, coste 12: frente a control: voto ±50, **no concluye**; frente a Viterbi, coste 25 (v0), **mejora**
- Viterbi, coste 25 (v0): frente a control: voto ±50, **depende del balón**
- Viterbi, coste 50: frente a control: voto ±50, **compromiso**; frente a Viterbi, coste 25 (v0), **compromiso**
- Viterbi, coste 100: frente a control: voto ±50, **compromiso**; frente a Viterbi, coste 25 (v0), **compromiso**
```
