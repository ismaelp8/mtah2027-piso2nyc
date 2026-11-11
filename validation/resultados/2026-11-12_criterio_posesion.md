# Cuándo cambia la posesión y con qué control corregir la DFL · 2026-11-12 · Claude (sesión de Ismael)

> Experimento 1. Responde a Ismael (12/11): entender bien cuándo cambia la posesión según el repo
> oficial, buscar métodos implementados con el mismo criterio y valorar si con lo que tenemos se puede
> seguir. Solo agregados. Cada afirmación lleva **[medido]**, **[inferencia]**, **[fuente]** o **[sin
> verificar]**. El registro paso a paso está en `validation/experimento1/BITACORA.md`.

**En pocas líneas:**

1. **El texto del reto pide control, pero hay tres lecturas posibles de qué cambia la posesión.**
   - **Último toque:** el flag de la DFL, aunque su artículo diga "el jugador que controla".
   - **Toque con impacto significativo:** las definiciones de eventos de Metrica, la organizadora.
   - **Control establecido:** el texto de `CHALLENGE.md` y StatsBomb.

   El texto apunta a la tercera (un duelo aéreo ganado sin control no es cambio). La GT sale de un flag
   de proveedor y tiene dos posesiones cortas entre dos del rival, algo que encaja mejor con la segunda.
   Las dos se separan en el 70 % de los toques sin control **[medido]**.
2. **Con lo que tenemos podemos seguir.** El tracking de la DFL tiene el balón siempre, y sus eventos
   humanos (pases completados, recuperaciones y duelos con `PossessionChange`) sirven de referencia sin
   circularidad.
   - Elegir la definición de control mueve entre un tercio y dos tercios de las posesiones.
   - Para la lectura del texto, la más equilibrada es "control de 12 frames o dos toques seguidos": no
     queda por detrás de C0-8 ni de C0-12 en ninguna referencia **[medido]**.
3. **Fuera no hay nada que lo resuelva hecho.** Ningún método abierto da posesión de equipo por frame
   con criterio de control. Lo realista es lo que ya tenemos (detectores propios, eventos humanos y una
   regla documentada). Como extras opcionales, que necesitan permiso: los tiempos humanos de ELASTIC en
   3 partidos y `databallpy`.
4. **La pieza que falta solo la puede poner una persona:** mirar el vídeo de la ventana pública y
   contar.
   - ¿Las 3 rachas cortas son toques o controles?
   - ¿Los 12 cambios se fechan en el primer toque o cuando ya hay control?

   Decide qué lectura sigue la GT y cuándo fecha los cambios; esto último mueve más de 8 frames entre
   un cuarto y la mitad de los cambios.

- **Código:** `validation/experimento1/` (`duelos_dfl.py`, `duelos_sincronizados.py`, `correccion.py`,
  `peso_correccion.py`, `comparar_definiciones.py`, `fecha_del_cambio.py`, `lecturas_toque.py`), sobre
  la caché del experimento 0. Rama `exp/experimento-0`, commits locales.
- **Datos:** los 7 partidos de la Bundesliga (Bassek et al., 2025): posiciones y eventos.

## 1. Cuándo cambia la posesión, según el repo oficial

Leídos enteros `CHALLENGE.md`, `FAQ.md`, `OVERVIEW.md`, `SUBMISSION.md`, `RULES.md`, `EVALUATION.md` y
`DATA.md`. `upstream` no ha cambiado desde la copia.

| regla | dónde |
|---|---|
| El cambio es cuando un jugador del rival consigue la posesión **controlada**. Es "el momento" en que pasa al otro equipo | `CHALLENGE.md` 55–58 |
| Con el balón disputado o suelto, la posesión sigue con el último equipo que la tuvo | 62–64 |
| Tras un reinicio hay un poseedor claro | 66–67 |
| No es cambio: un toque sin control; un desvío de un pase que no lo intercepta; un duelo aéreo ganado sin control posterior **de ese equipo** | 76–80 |
| Proxies de control, orientativos: un jugador retiene el balón unos segundos; un equipo encadena más de dos pases | 69–74 |
| Lo que manda es la GT: sale mecánicamente del flag del tracking corregido, sin suavizar. La GT pública es la referencia de cómo se etiquetan estos casos | 82–87, 97–103 |
| El documento técnico tiene que decir dónde se pone la línea en balones sueltos, disputas y reinicios | `SUBMISSION.md` 70 |

**Tres cosas que el texto deja abiertas [inferencia]:**

1. **Qué es "controlada".** Los proxies hablan de segundos o de varios pases, pero no son la regla.
2. **Cuándo se fecha el cambio:** en el primer toque de la secuencia que acaba en control, o cuando el
   control ya está establecido. "Sin control posterior de ese equipo" sugiere que la secuencia cuenta
   desde su primer toque, pero no lo dice.
3. **Si la GT sigue el texto.** La GT sale del flag de un tracking corregido, y ese tracking "nombra un
   equipo" también con el balón muerto (el que reanudará o el que la tocó por última vez,
   líneas 42–45), como el flag de la DFL.

**Lo que se ve en la GT pública, solo como etiquetas [medido]:**

- 17 posesiones y 12 cambios directos H↔A;
- dos posesiones del local de 19 y 33 frames (0,76 s y 1,32 s) entre dos del visitante.

La GT no exige "unos segundos": tiene posesiones de menos de 1 s. Pueden ser controles muy breves o
toques. Solo el vídeo lo dice (sección 6).

## 2. Qué tenemos en la DFL para medirlo sin hacer trampa

**El tracking de la DFL tiene el balón en el 100 % de los frames**, y sus eventos los anota una
persona. Así se puede medir sin circularidad: el control se detecta con el tracking y se contrasta con
lo que dice el anotador, que no ha visto nuestro detector.

**Los eventos traen lo que hace falta para el criterio del reto [medido]:**

- **duelos** (`TacklingGame`, 1.412 en los 7 partidos), con:
  - quién tenía el balón (`WinnerRole`/`LoserRole`: `withBallControl` / `withoutBallControl`);
  - cómo se gana (`WinnerResult`: `ballcontactSucceeded`, `layoff`, `ballClaimed`,
    `ballControlRetained`, `fouled`, `dribbledAround`);
  - si hubo cambio de posesión (`PossessionChange`);
- **recuperaciones** (`BallClaiming`: `InterceptedBall`, `BallClaimed`);
- **pases con resultado** (`Evaluation`) y **receptor** (`Recipient`);
- **despejes** (`DefensiveClearance`).

**Los duelos, situados en su frame exacto con el tracking** (el frame en que los dos jugadores están
más cerca del balón; mediana 0,83 m), frente al flag (1.137 duelos) **[medido]**:

| quién gana el duelo y cómo | n | el flag pasa al que gana en el primer segundo | sigue en él a los 2 s |
|---|---|---|---|
| el que no tenía el balón, se hace con él (`ballClaimed`) | 168 | 75,0 % | 70,5 % |
| el que no tenía el balón, solo lo toca (`ballcontactSucceeded`) | 288 | 76,4 % | 72,0 % |
| el que no tenía el balón, lo juega de primeras (`layoff`) | 80 | 80,0 % | 70,6 % |
| el que tenía el balón lo conserva (`ballControlRetained`) | 112 | 10,7 % | 22,7 % |

- **El flag trata igual un toque que una recuperación.** Lo confirma ahora un anotador humano, sin el
  detector de toques del experimento 0.
- **El anotador sí distingue.** Cuando el rival solo toca el balón, el flag sigue en él a los 2 s:
  - en el 89,2 % de los duelos con `PossessionChange` = true;
  - en el 56,9 % de los que tienen false.

  El anotador marca cambio de posesión cuando el equipo que gana el duelo se queda con el balón, como
  pide el reto **[inferencia]**. Su definición oficial está **[sin verificar]** (sección 4).

## 3. Cuánto pesa la definición de control

**Cómo se corrige (R(c), fijada antes de medir):**

- una racha del rival que no sigue a un `D` se queda solo si el rival tiene control según la
  definición c en algún frame de la racha;
- si no, pasa al equipo anterior;
- tras un reinicio, el que reanuda se queda.

**Definiciones probadas, sin ajustar:**

- C0-k: el mismo jugador, el más cercano, a ≤ 1 m durante k frames. C0-50 (2 s) es el proxy "unos
  segundos";
- Ret-5: el equipo, a ≤ 1 m, 5 frames;
- dos toques: dos toques seguidos del mismo equipo en ≤ 2 s;
- la unión "C0-12 o dos toques".

| definición | posesiones (7 partidos) | por minuto vivo | frames vivos que cambian | pases completados bien | recuperaciones bien | duelos con cambio (true) bien | duelos sin cambio (false) bien |
|---|---|---|---|---|---|---|---|
| flag tal cual | 3.061 | 8,30 | 0 % | 97,9 % | 89,2 % | 88,6 % | 47,4 % |
| C0-8 | 1.747 | 4,74 | 7,2 % | 97,5 % | 84,6 % | 81,7 % | 71,6 % |
| C0-12 | 1.549 | 4,20 | 8,9 % | 96,6 % | 81,0 % | 76,4 % | 78,2 % |
| C0-20 | 1.359 | 3,69 | 10,6 % | 95,3 % | 75,4 % | 71,6 % | 82,0 % |
| C0-50 | 1.008 | 2,73 | 19,3 % | 84,0 % | 59,0 % | 52,4 % | 82,0 % |
| Ret-5 | 2.047 | 5,55 | 4,9 % | 98,2 % | 86,2 % | 87,3 % | 61,6 % |
| dos toques | 1.552 | 4,21 | 8,7 % | 98,1 % | 80,5 % | 78,6 % | 77,7 % |
| C0-12 o dos toques | 1.736 | 4,71 | 6,8 % | 98,8 % | 87,7 % | 84,3 % | 74,9 % |

Las cuatro referencias, explicadas:

- **pases completados** (3.142): la etiqueta, 5 frames después de que el receptor reciba, es del equipo
  del pasador. Con cualquier lectura del reto ese equipo controla;
- **recuperaciones** (195): la etiqueta, 0,5 s después de la recuperación, es del equipo que recupera;
- **duelos** (229 con cambio, 211 sin): la etiqueta a 2 s está en el equipo que dice el anotador.

**Lectura [medido]:**

- **La elección pesa muchísimo.** Cualquier corrección quita entre un tercio y dos tercios de las
  posesiones del flag (de 3.061 a 1.008–2.047), y cambia el equipo del 5–19 % de los frames vivos.
- **Hay un compromiso:** cuanto más exigente el control, menos cambios falsos y más posesiones reales
  quitadas.
  - C0-50, el proxy "unos segundos", quita el 16 % de las posesiones de pases completados y el 41 % de
    las recuperaciones: demasiado;
  - el flag tal cual y Ret-5 dejan demasiados cambios falsos.
- **"C0-12 o dos toques" no queda por detrás de C0-8 ni de C0-12 en ninguna de las cuatro
  referencias,** y en tres va por delante. Las diferencias con C0-12 son significativas en tres
  referencias (bootstrap emparejado, intervalo del 95 %): +1,7 a +2,8 puntos en pases, +3,6 a +10,3 en
  recuperaciones y +4,4 a +11,8 en duelos con cambio. En duelos sin cambio es un empate (−6,6 a +0,5).
  Corresponde a los dos proxies del reto: un jugador retiene el balón, o el equipo encadena toques.
- **Las recuperaciones son el punto débil de todas** (59–88 %).
- **No se elige aquí:**
  - el significado de `PossessionChange` está sin verificar;
  - la fecha del cambio está abierta;
  - la decisión es de Ismael.

**La fecha del cambio pesa tanto como la definición [medido].** La corrección deja cada cambio donde
lo puso el flag, en el primer toque. Si la GT lo fecha al empezar el control, se moverían más de 8
frames:

- el 24,5 % de los cambios con "C0-12 o dos toques";
- el 52,7 % con C0-12.

Con 8 frames de retraso el `spellF1` ya baja a 0,89.

## 4. Métodos y definiciones de fuera

### 4.1 Definiciones, verificadas en la fuente cuando se dice

| fuente | qué cambia la posesión | balón suelto o disputado | balón muerto | verificado |
|---|---|---|---|---|
| **el reto** (`CHALLENGE.md`) | el rival consigue la posesión **controlada** | sigue el último equipo | `D` (el tracking nombra un equipo, la GT lo tira) | **[fuente]** |
| **Metrica, eventos** (`events-definitions.pdf` de su `sample-data`) | posesión desde el **primer toque**; no se pierde si el toque del rival no tiene impacto significativo (el pase llega o el poseedor sigue controlando) | un toque con impacto da la posesión al que toca | la posesión acaba al salir el balón | **[fuente]** |
| **StatsBomb** (open data v1.1, pág. 9) | posesión nueva cuando un equipo **ha establecido el control** | los toques del rival quedan dentro de la posesión | un reinicio puede abrir posesión nueva | **[fuente]** |
| **DFL, flag del tracking** | el artículo dice "el jugador que controla el balón" (Bassek et al. 2025); en los datos cambia en el **primer toque** | no documentado | `BallStatus` 0; el flag ya es del que reanuda | **[fuente]** y **[medido]** |
| **DFL, eventos** (`PossessionChange`) | el catálogo no es público; se comporta como "el equipo se queda con el balón" | — | — | **[medido]**, definición **[sin verificar]** |
| Opta, Wyscout | control | sigue el último equipo | de nadie | **[sin verificar]** (subagente) |
| FIFA EFI | control | tercer estado "en disputa" | estado propio | **[sin verificar]** (subagente) |
| Link y Hoernig 2017 | posesión al entrar el balón en el espacio de acción; "control" es una capa aparte | — | de nadie | **[sin verificar]** (subagente) |

**Tres lecturas, y dónde se separan:**

1. **Último toque.** Es el flag de la DFL.
2. **Toque con impacto significativo.** Son los eventos de Metrica.
   - No cambian la posesión un desvío que no corta el pase, ni un toque tras el que el poseedor sigue
     controlando: son los dos primeros ejemplos de `CHALLENGE.md`.
   - Pero un toque que deja el balón suelto da la posesión al que toca, aunque luego lo recupere el otro
     equipo. Eso crea rachas cortas X → y → X.
3. **Control establecido.** Es el texto del reto y StatsBomb. Su tercer ejemplo (un duelo aéreo ganado
   sin control posterior de ese equipo no es cambio) es justo donde 2 y 3 se separan.

**Cuánto se separan en la DFL** (`lecturas_toque.py`, sobre los 203 toques sin control del rival entre
dos controles del mismo equipo) **[medido]**:

| qué pasa después del toque | casos | lectura 2 | lectura 3 | el flag de la DFL cambia |
|---|---|---|---|---|
| balón suelto, lo recupera otro compañero | 70,0 % | cambio (racha corta) | sin cambio | 90,1 % |
| el mismo jugador vuelve a controlar | 22,2 % | depende | sin cambio | 75,6 % |
| el pase llega a su destino | 7,9 % (mínimo) | sin cambio | sin cambio | 68,8 % |

### 4.2 Métodos implementados

Resumen de un subagente. Lo verificado aquí en la fuente está marcado.

- **Ningún método abierto da posesión de equipo por frame con criterio de control.**
- **`databallpy`** (MIT, activo; **[fuente: código]**):
  - posesión por jugador al estilo de Vidal-Codina et al. 2022: zona alrededor del jugador y ganancia si
    el balón cambia de velocidad o de dirección. Un desvío cuenta como ganancia: es por toque;
  - su posesión de equipo solo cambia con un pase, regate o tiro con éxito del rival: parecido al
    control, pero fecha el cambio tarde;
  - lee los datos abiertos de la DFL (según el subagente).
- **ELASTIC** (código MPL-2.0, datos CC BY 4.0; **[fuente: README]**): eventos corregidos de J03WMX,
  J03WN1 y J03WPY, con el frame en que ocurre cada uno y en que se recibe el balón (mediana de tres
  anotadores). Es una referencia de tiempo humana en 3 de nuestros 7 partidos.
- **Sin verificar aquí:**
  - Link y Hoernig 2017 tienen la única definición publicada de control validada con personas, pero sin
    código ni umbrales;
  - Vidal-Codina et al. 2022 no tienen código público;
  - PathCRF trae los eventos de los 7 partidos sincronizados con ELASTIC.
- **Un repositorio que no se ha abierto:** el subagente encontró el repositorio público de otro equipo de
  este reto, con ficheros derivados del partido. No se ha mirado (regla nº 1 y juego limpio).

## 5. ¿Podemos seguir con lo que tenemos?

**Sí.** Para la lectura del texto (control), lo necesario ya está.

- **El tracking de la DFL tiene el balón en todos los frames,** y los detectores de toque y de control
  están probados con trayectorias sintéticas y contra los eventos.
- **Los eventos humanos de la DFL dan referencias sin circularidad:** pases completados, recuperaciones y
  duelos con `PossessionChange`. Miden los dos fallos posibles: dejar cambios falsos y quitar posesiones
  reales.
- **La corrección R(c) está escrita y probada,** y una definición ("C0-12 o dos toques") no queda por
  detrás de C0-8 ni de C0-12 en ninguna referencia.

**Lo que falta, por orden de importancia:**

1. **Qué lectura sigue la GT (2 o 3).** Cambia mucho la corrección: con la lectura 2 se quitaría solo una
   parte pequeña de las rachas creadas por un toque; con la 3, casi todas. Solo lo dice el vídeo de la
   ventana pública (sección 6).
2. **Cuándo se fecha el cambio** (primer toque o control establecido): mueve más de 8 frames entre un
   cuarto y la mitad de los cambios. También solo lo dice el vídeo.
3. **Qué significa exactamente `PossessionChange`:** el catálogo de la DFL no es público. Su
   comportamiento encaja con "el equipo se queda con el balón", pero es una inferencia.
4. **Las recuperaciones son el punto débil de todas las correcciones** (59–88 % de acierto). Hay margen
   para mejorar la detección de control ahí.

**Cosas nuevas que ayudarían, pero no hacen falta para decidir** (las dos piden permiso):

- **los tiempos humanos de ELASTIC en 3 partidos:** para comprobar la fecha de nuestros toques y de los
  cambios corregidos. Es una descarga de su repositorio;
- **`databallpy`:** como contraste de la posesión por jugador. Es instalar una dependencia, que habría
  que fijar en `requirements.txt`.

**Propuesta de siguientes pasos:**

1. Ismael mira el vídeo y da los recuentos de la sección 6.
2. Con eso se fija la convención (lectura 2 o 3, y la fecha) y se escribe antes de medir el protocolo
   de elección de c: referencias, regla de empate y sensibilidad.
3. Se construye el generador de etiquetas de la DFL con la convención como opción. Con él se validan
   N1–N5 y se puede medir cuánto cambia el ranking si la convención estuviera mal.

## 6. Lo que solo puede hacer una persona: mirar la ventana pública

`CHALLENGE.md` dice que la GT pública es donde se ve qué significa "poseer" (líneas 82–87 y
102–103), y `CLAUDE.md` permite usarla para el significado de las etiquetas, nunca para elegir
versiones. Mirar el vídeo para entenderlo está permitido; convertir lo que se ve en etiquetas, no.

**Propuesta: Ismael mira el vídeo táctico en los momentos de la ventana pública y responde solo con
recuentos.** Los momentos los da `evaluation/gt/BAR-ATH_possession_gt_public.csv`.

1. **Las tres posesiones cortas entre dos del rival** (19, 33 y 71 frames): ¿en cuántas el equipo de
   esa racha controla el balón, y en cuántas solo lo toca, lo desvía o lo despeja?
2. **Los 12 cambios directos H↔A:** ¿en cuántos cambia la etiqueta en el primer toque del equipo nuevo,
   y en cuántos más tarde, cuando ya controla?

Con eso se sabe:

- si la GT sigue al control (lo decidido) o al toque, como la DFL;
- cuándo fecha el cambio. Es lo que más pesa en el `spellF1` y no se puede medir de otra forma.

Las respuestas se apuntan como recuentos en la bitácora. Ninguna etiqueta, constante ni parámetro sale
de ahí.

**Cómo leer las respuestas:**

- **Si las rachas cortas son toques que dejan el balón suelto:** la GT sigue la lectura 2 (Metrica) o la
  1, y hay que revisar la decisión del 12/11 con Ismael.
- **Si son controles breves:** encaja con la lectura 3, la decidida.
