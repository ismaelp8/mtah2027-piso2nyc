# Guía del visionado de la ventana pública

Para mirar, junto al vídeo táctico, dónde no coinciden nuestra entrega y la GT pública, y sacar ideas
generales. Unos 45 minutos.

## Las reglas, en cuatro líneas

- **Se puede:** mirar el vídeo y la GT pública para entender cómo se etiquetan los casos y depurar
  (`RULES.md` §1, «What remains fine»; `CHALLENGE.md`, «The reference is the ground truth»).
- **No se puede:** convertir lo que veas en etiquetas, correcciones o reglas y constantes ligadas a
  momentos de este partido, ni ajustar nada con estos 5 minutos (`RULES.md` §1 y §2).
- **Claude no ve nada:** ni el vídeo, ni la página, ni tus notas con tiempos (regla nº 1 de `CLAUDE.md`).
- **Lo que salga se mide en otros partidos** (la DFL y SkillCorner), nunca en la ventana.

## 1. Generar la página

Desde la raíz del repo, con el entorno de siempre y `MTAH_DATA_DIR` apuntando a los datos:

```bash
python validation/partido/clips_ventana.py equipo_v3
```

- Imprime cuántos tramos hay y la ruta de la página, en `~/mtah2027-salidas/`. Ábrela con doble clic.
- Si la página no abre el vídeo sola, te deja elegir `BAR-ATH_tactical.mp4` a mano.
- `--margen 5` da más contexto alrededor de cada tramo (por defecto, 3 s).

## 2. Antes de nada: comprobar la alineación (1 minuto)

- Pulsa **«saque inicial»**: la página va al frame del saque de `games.py`. El balón tiene que salir en
  ese frame o en el de al lado. Usa `←` y `→` para ir de frame en frame.
- Compara el reloj de la página (`m:ss:ff`, minuto, segundo y frame) con el reloj del vídeo, si se ve.
- **Si no cuadra, para** y dile a Claude cuántos frames de diferencia hay. Lo demás no vale hasta
  arreglarlo.

## 3. Cómo se usa

- La lista de la derecha tiene un tramo por cada sitio en que difieren, en orden. Cada uno lleva:
  - **borde:** las mismas posesiones y paradas, pero un cambio llega antes o después. La nota dice cuál
    y cuánto;
  - **equipo:** decimos el otro equipo en algún frame;
  - **D:** una de las dos dice balón muerto y la otra no.
- Debajo del vídeo ves, en directo, qué dice la GT y qué decimos nosotros en el frame que se ve; en rojo
  cuando no coinciden. La tira del tramo enseña las dos etiquetas a la vez, con una marca por segundo.
- **Teclas:** espacio para reproducir o parar; `←` y `→`, un frame; con `Mayús`, un segundo; `N` y `P`, el
  tramo siguiente o el anterior; `R`, repetir; `L`, bucle; `1`, `2` y `3`, velocidad ¼, ½ y 1.
- El tramo se para solo al final. Lo cómodo: a ½ la primera vez y, en el momento del cambio, frame a
  frame.
- Con prisa, marca «esconder los de solo borde» y mira primero los demás.

## 4. Qué mirar en cada tipo

**Cambios de equipo que no hacemos** (la GT cambia y nosotros no):

- ¿Qué pasa cuando cambia la GT: un pase interceptado, una entrada, un balón dividido o un rebote?
- ¿Cambia en el primer toque del rival o cuando ya lo controla (para el balón, da dos toques o pasa)?
- ¿Cuánto dura la posesión que nos perdemos? ¿Es muy corta?
- ¿Cómo está la jugada: balón por el aire, área llena, el balón tapado o lejos de todos?

**Cambios que hacemos donde no toca** (nosotros cambiamos y la GT no):

- ¿Qué lo provoca: un toque del rival sin control, un balón que pasa cerca de un rival, un despeje, un
  balón largo o un balón dividido?
- ¿Tras un despeje o un balón largo, la GT sigue con el equipo anterior hasta que alguien controla?

**Bordes de equipo** (llegamos antes o después):

- ¿En qué momento cambia la GT: al golpear el pase, cuando el balón llega al rival, en su primer toque o
  cuando ya controla?
- ¿Vamos siempre tarde, siempre pronto o depende?

**Paradas (`D`):**

- **Inicio:** ¿la GT empieza el `D` cuando el balón cruza la línea, cuando pita el árbitro o cuando el
  balón sale del plano? ¿Y nosotros?
- **Final:** ¿la GT acaba el `D` en el golpeo del saque, cuando alguien coge el balón o antes?
- ¿Depende del tipo: banda, córner, puerta, falta o gol?
- ¿Hay paradas que no vemos o que inventamos? ¿Cómo son: cortas, con el juego casi parado o con el
  balón fuera de plano?
- Con sonido, ¿ayuda el silbato?

## 5. Cómo contárselo a Claude

- **En general, sin minutos, frames, números de tramo ni recuentos tramo a tramo.** Por ejemplo: «en los
  saques de banda la GT acaba el `D` en el golpeo y nosotros más tarde», o «tras un despeje la GT sigue con
  el equipo que despejó hasta que alguien controla».
- Puedes decir «pasa a menudo» o «lo vi una vez». No hace falta contar.
- Si tomas notas con tiempos, guárdalas fuera del repo, no se las pegues a Claude y bórralas al acabar.
- Si te sale «en el minuto tal pasa esto», Claude no lo apuntará.

## 6. Qué se hace después

- Claude convierte lo que cuentes en dos a cuatro **hipótesis generales**, cada una con su forma de
  medirla en la DFL y en SkillCorner y su criterio escrito antes de medir.
- Las de cambios de equipo van a la sesión de las posesiones cortas. Las de balón muerto, a las piezas de
  Manuel y de Ana.
- Nada se elige ni se ajusta con la ventana: son 17 posesiones y no distinguen versiones (`EVALUATION.md`).
- En `docs/decisiones.md` queda qué se miró, con qué reglas y que no se ajustó nada.
