# El instante del reinicio en el partido: ningún tipo de reinicio tiene ancla

- **Fecha y quién:** 15/11/2026. Lo ejecutó Manuel en local; el script es de la sesión de Claude de Manuel.
  La lectura la apunta la sesión de Claude de Ana, que sigue la pieza desde el 15/11 por la tarde.
- **Datos:** el ATD y el Smart Tagging del partido, en `MTAH_DATA_DIR`. Solo agregados del partido entero.
- **Código:** la rama `feat/d-instante-reinicio` en `17f7648`: el script y la regla de `569d3b4`, con el
  `possession/` de `main` en `98c38ca`, que trajo ese merge. Entre otras cosas trae la PR 12 de Ana: las
  ventanas de `dead_state` ya no cruzan los bordes de los tramos. La regla de lectura se subió a GitHub antes de
  ejecutar el script; su última versión es la de `569d3b4`. Está en `docs/decisiones.md`, entrada «`D` · el
  instante del reinicio: regla escrita antes de medir» (15/11).
- **Huellas impresas:** modelo de Ana `def73c1ebf2b` y código de `possession/` `b8a00a1a1aea`. Coinciden con
  las que se calculan en local con `17f7648`. En `569d3b4` la del código era `6169ad54157a`: el modelo de Ana
  cambió con la PR 12 entre escribir la regla y ejecutarla, y la ejecución ya lo lleva.
- **Comando:** `python validation/partido/agregados_instante_reinicio.py`
- **Para qué:** decidir, con la regla fijada antes, si el fin del `D` de cada ventana `SET PIECES` cae en un
  sitio fijo con poca dispersión y, si cae, cuál de los dos candidatos de la capa entra (A, B o ninguno).
  Añade los agregados de la tarea 3 del plan para la capa del hueco.
- **Lectura en tres líneas:**
  1. **No entra ninguna de las dos capas del instante:** ningún tipo de reinicio tiene ancla. En los dos tipos
     con 10 transiciones o más, la del modelo de Ana se dispersa más de 3 s (3,2 s en los saques de banda y
     3,1 s en los córners), y el máximo era 2 s. Tampoco gana la mediana fija a la transición de cada ventana
     [medido].
  2. **El modelo de Ana no separa por el lado del juego:** ve `D` en el 49,6 % del control de juego, más que
     en lo evaluado (47,4 %) [medido]. Así que el candidato A no habría podido entrar en ningún tipo
     [inferencia, comprobada en el código]. Parte de la explicación puede ser que ese control incluye frames
     del tramo antes del saque de la 2ª parte [inferencia, comprobada en el código; `docs/decisiones.md`].
  3. **Tarea 3, descriptivo:** en 19 de los 28 huecos el `D` de la entrega ya empieza antes del hueco o en su
     primer segundo. La capa del hueco cambia 1.083 frames, 561 de ellos (51,8 %) en los primeros 5 s de cada
     hueco [medido]. Dar más peso al principio del hueco tendría poco que ganar [inferencia].

**Ojo con el orden:** la confirmación de las 9 interpretaciones y los dos añadidos que Ana pidió para antes de
ejecutar llegaron cuando ya se había ejecutado. Las 9 se confirmaron sin cambios, así que la ejecución aplica la
regla confirmada; los añadidos no los lleva, y no cambian el veredicto (`docs/decisiones.md`, misma entrada).

La salida, tal cual la pegó Manuel. Solo falta la línea del prompt de PowerShell. Las celdas de menos de 5
casos ya salen tapadas («< 5») y las proporciones de grupos de menos de 5, como «—».

```
pipeline: piezas {"ball": "clean", "candidates": "aprendida.evidence_b5", "dead_state": "evidence", "temporal": "decode"}   costes {"from_dead": 25.0, "switch": 25.0, "to_dead": 25.0}
huellas: modelo de Ana def73c1ebf2b   código de possession/ b8a00a1a1aea
regla: sostén 2 s   búsqueda hasta 10 s tras el fin de la ventana   capa ±1 en D: 3 s antes del instante (sin hueco) y 3 s después (A)

1. Dónde cae el reinicio dentro de cada ventana SET PIECES (no los saques iniciales)
   ventanas en lo evaluado: 53   duración mediana 35.0 s   a más de 1 s de esa mediana: < 5
   desfases en s desde el INICIO de la ventana (desde el fin: réstale la duración): p10 / p25 / p50 / p75 / p90 (recorrido intercuartílico)
   corner kick            n=12
      modelo de Ana, de parado a juego   n=11  +2.2 / +3.8 / +4.8 / +6.9 / +7.3  (3.1)
      el balón vuelve a verse            n=11  +4.5 / +5.7 / +6.6 / +7.4 / +10.1  (1.7)
      balón: vuelve a verse 11   visto al empezar < 5   no vuelve < 5
      con las dos señales (n=11): distancia mediana entre ellas 1.8 s; del balón al ancla fija 2.0 s
   free kick              n=5
      modelo de Ana, de parado a juego   n=< 5
      el balón vuelve a verse            n=< 5
      balón: vuelve a verse < 5   visto al empezar < 5   no vuelve < 5
   goal kick              n=10
      modelo de Ana, de parado a juego   n=8
      el balón vuelve a verse            n=< 5
      balón: vuelve a verse < 5   visto al empezar 8   no vuelve < 5
   throw-in               n=26
      modelo de Ana, de parado a juego   n=25  +3.7 / +5.8 / +6.9 / +9.0 / +19.3  (3.2)
      el balón vuelve a verse            n=17  +1.3 / +4.0 / +6.1 / +7.0 / +13.0  (3.0)
      balón: vuelve a verse 17   visto al empezar 9   no vuelve < 5
      con las dos señales (n=16): distancia mediana entre ellas 1.6 s; del balón al ancla fija 2.0 s

2. La regla, por tipo (≥ 10 con transición, recorrido ≤ 2 s, ≥ 5 con balón y medianas a ≤ 1 s, y el ancla fija más cerca del balón que la transición de cada ventana)
   placebo: las ventanas desplazadas -8/-6/-4/+4/+6/+8 min, lejos de reinicios reales: 103; un tipo no tiene ancla si su placebo también tiene poca dispersión
   corner kick            suficientes sí   poca dispersión no   el balón coincide no   el ancla gana no   el placebo no se concentra sí (n=15)   -> ancla: no
   free kick              suficientes no   poca dispersión no   el balón coincide no   el ancla gana no   el placebo no se concentra sí (n=5)   -> ancla: no
   goal kick              suficientes no   poca dispersión no   el balón coincide no   el ancla gana no   el placebo no se concentra sí (n=12)   -> ancla: no
   throw-in               suficientes sí   poca dispersión no   el balón coincide sí   el ancla gana no   el placebo no se concentra sí (n=31)   -> ancla: no

3. Los dos candidatos de la capa
   modelo de Ana, D en: partido 47.4 %   control de D (antes del saque de la 2ª parte) 94.6 %   control de juego (a más de 60 s de cualquier reinicio) 49.6 %
   puntos medios: parado antes si ≥ 71.0 %   juego después si ≤ 48.5 %
   ningún tipo tiene ancla: no se prueba ningún candidato

-> entra: ninguno

4. La capa del hueco (PR #8): frames evaluados que cambian de etiqueta con ella: 1083   de ellos, en los primeros 5 s de cada hueco: 561
   frames con piezas en conflicto sin la capa del hueco: 0
   inicio del D de la entrega desde el inicio de cada hueco (huecos: 28; negativo si el D ya venía de antes):
      < 0 s          11
      0 a 1 s        8
      1 a 3 s        < 5
      3 a 5 s        < 5
      ≥ 5 s          < 5
      sin D          < 5

   tiempo 17 s
```

## Cómo se lee cada número

- **Sección 1:** las ventanas son las `SET PIECES` que no son saques iniciales y empiezan en un tramo evaluado.
  Los cuantiles solo salen con 10 casos o más. «Distancia mediana entre ellas» es la del balón a la transición
  de su propia ventana; «del balón al ancla fija», la del balón a la mediana del tipo.
- **Sección 2:** un tipo tiene ancla si cumple las cinco cosas. Con menos de 10 transiciones («suficientes
  no»), las tres siguientes salen como «no» sin calcularse. El `n` del placebo es el de las ventanas
  desplazadas de ese tipo que tienen transición; en total hay 103 ventanas desplazadas.
- **«El balón coincide»** compara las dos medianas: saques de banda +6,1 s frente a +6,9 s (0,8 s, sí) y
  córners +6,6 s frente a +4,8 s (1,8 s, no).
- **«El ancla gana»** compara la distancia del balón a la mediana fija (2,0 s en los dos) con la del balón a la
  transición de su ventana (1,6 y 1,8 s). Gana si la primera es menor, y no lo es en ninguno.
- **Sección 3:** los puntos medios son (47,4 + 94,6) / 2 = 71,0 % y (47,4 + 49,6) / 2 = 48,5 %. El instrumento
  separa si el control de `D` queda por encima del partido y el control de juego por debajo; aquí el de juego
  queda por encima.
- **Sección 4:** «0 a 1 s» es de 0 s incluido a 1 s sin incluir. «< 0 s» quiere decir que el `D` de la
  entrega ya venía de antes del hueco.
