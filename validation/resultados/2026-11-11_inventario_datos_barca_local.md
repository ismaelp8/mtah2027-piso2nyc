# Inventario: datos abiertos de partidos del Barça como local

- **Fecha:** 2026-11-11 · **Quién:** Claude, en la sesión de Ismael.
- **Qué se buscó:** datos abiertos de partidos del Barça como local, en el Camp Nou, que se parezcan a
  los del reto más que los de la Bundesliga.
- **Cómo se comprobó:** cada cifra sale de leer el índice de cada fuente (ficheros `competitions.json`,
  `matches.json`, árboles de git, API de figshare) o de cabeceras HTTP, no de memoria. Lo que no se pudo
  comprobar va marcado.
- **Ninguno de estos datos es del partido del reto,** así que las reglas permiten usarlos.

## Resumen

1. **El partido del reto no se jugó en el Camp Nou.** El Barça no jugó ningún partido oficial allí entre
   el 28/05/2023 y el 22/11/2025: las temporadas 2023-24 y 2024-25 las jugó en Montjuïc (Estadi Olímpic
   Lluís Companys). El partido del reto es de la jornada 2 de 2024-25 (`DATA.md`), así que se jugó allí.
   No se ha consultado ninguna fuente sobre ese partido concreto.
2. **No hay tracking abierto de ningún partido del Barça con flags de posesión y de balón muerto por
   frame,** que es lo que tiene la GT del reto. Tampoco de Montjuïc: los datos abiertos de LaLiga
   acaban en la temporada 2020-21.
3. **Sí hay tres cosas útiles del Barça como local en el Camp Nou:**

| fuente | qué hay | partidos del Barça como local | licencia | sirve para |
|---|---|---|---|---|
| **StatsBomb** | eventos con marca temporal al milisegundo; 360 (posiciones sin identidad en cada evento) solo en 2020-21 | **264** (2004-05 a 2020-21), todos en el Camp Nou; **18** con 360 | acuerdo de StatsBomb: investigación, sin redistribuir, logo al publicar, sin uso comercial | priors de LaLiga: paradas por tipo y su duración, granularidad de las posesiones |
| **SkillCorner** (versión 2020) | tracking de broadcast a 10 fps, sin corregir, con posesión por frame calculada por SkillCorner | **1:** Barça–Real Madrid, 18/12/2019, Camp Nou, 0-0 | MIT (el texto habla de "Software") y piden que se les cite | banco de pruebas con tracking automático real de un partido del Barça en casa |
| **Wyscout** (Pappalardo et al., 2019) | eventos de la temporada 2017-18 completa | 19 (temporada completa) | CC BY 4.0 | priors de paradas con una licencia más limpia que la de StatsBomb |

**Lo que no sirve:** SoccerNet tiene 26 partidos del Barça como local, pero son anotaciones de acciones
sobre el vídeo de TV, con precisión de un segundo; para estos fines no añade nada a los eventos de
StatsBomb. La edición 2026 de More than a Hack no publicó sus datos (no he encontrado nada abierto).

**Qué cambia en el plan:** nada de lo esencial. La Bundesliga sigue siendo el dataset principal, porque
es el único con el mismo tipo de etiqueta que la GT (flags por frame del tracking). Los datos del Barça
entran como apoyo: pasos 3 y 4 de `validation/PASOS.md`.

## Por qué "del Barça en el Camp Nou" no es lo que más se parece

- **El estadio no influye** en un método que trabaja con tracking. Influiría en uno que trabajase con
  vídeo (posición de la cámara), y aun así el partido del reto se grabó en Montjuïc.
- **Lo que hace que unos datos se parezcan a los del reto,** por orden de importancia:
  1. que la etiqueta sea la misma: flags por frame de un tracking corregido. Solo la Bundesliga;
  2. que el ruido sea el mismo: tracking automático con el balón perdido en duelos y áreas. Nadie tiene
     el del ATD; SkillCorner tiene otro ruido (cámara de TV, repeticiones, ~14 jugadores visibles de
     22);
  3. que la competición y el equipo se parezcan: duración de las paradas, ritmo, estilo. Aquí los
     eventos de LaLiga con el Barça de local sí aportan.
- **El estilo cambia con los años:** el Barça de 2024-25 (Flick, línea alta y presión) no juega como el
  de 2015-2021. Por eso conviene mirar primero las temporadas más recientes.

## Detalle por fuente

### StatsBomb (eventos)

- **Repo:** https://github.com/statsbomb/open-data, commit fijado
  `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb` (11/11/2026). LaLiga es la competición 11.
- **Partidos del Barça como local por temporada:** 2004-05: 5 · 2005-06: 10 · 2006-07: 13 ·
  2007-08: 13 · 2008-09: 15 · 2009-10: 16 · 2010-11: 16 · 2011-12: 18 · 2012-13: 15 · 2013-14: 15 ·
  2014-15: 19 · 2015-16: 19 · 2016-17: 18 · 2017-18: 19 · 2018-19: 18 · 2019-20: 17 · 2020-21: 18.
  **Total 264**, todos con estadio "Spotify Camp Nou". La 2015-16 está completa (380 partidos).
- **360:** de LaLiga solo la 2020-21 (los 18 partidos del Barça como local). En el
  partido comprobado, cada evento con 360 trae `actor`, `keeper`, `location` y `teammate`, **sin
  identidad de jugador** (como nuestro ATD): mediana de 18 jugadores visibles (mínimo 6, máximo 21), y el
  90 % de los eventos tiene su 360.
- **Campos útiles de los eventos** (comprobado en el Clásico del 18/12/2019, id 303596, 4.158 eventos):
  - `timestamp` al milisegundo desde el inicio de cada parte, y `duration`;
  - `possession` (contador) y `possession_team`: 105 posesiones de StatsBomb en la 1ª parte y 96 en la
    2ª, con su propia definición, que no es la del reto;
  - reinicios como tipo de pase: 39 saques de banda, 24 faltas, 13 saques de puerta, 8 córners y 2
    saques iniciales en ese partido;
  - `out` (el balón sale), `Injury Stoppage`, `Half Start` / `Half End`, `Foul Committed`.
- **Acuerdo de uso** (`LICENSE.pdf` del repo, versión del 8/9/2023):
  - es para investigación;
  - no se pueden redistribuir los datos: nunca en nuestro repo, solo el script que los descarga;
  - no se pueden explotar comercialmente ni los datos ni el análisis derivado;
  - quien publique un análisis tiene que poner el logo de StatsBomb;
  - piden que cada usuario se registre en su web (nombre y email) antes de usar los datos.
- **Descarga:** `python validation/scripts/descargar_datos_abiertos.py statsbomb-barca-local`
  (por defecto las 6 últimas temporadas: 109 partidos, unos 0,4 GB).

### SkillCorner, Barça–Real Madrid del 18/12/2019

- **Qué es:** uno de los 9 partidos de 2019-20 que SkillCorner abrió en 2020 (campeón y subcampeón de
  las cinco grandes ligas). Id 2841: FC Barcelona–Real Madrid CF, 18/12/2019, estadio "Camp Nou",
  campo de 105 × 68 m, 0-0. También está el partido de vuelta en el Bernabéu (id 3442).
- **Formato:** tracking de broadcast a 10 fps, coordenadas en metros con origen en el centro, solo lo
  que se ve en la TV (de media 14 jugadores de 22), sin datos en repeticiones y primeros planos. Cada
  frame trae `possession` (jugador y equipo), calculada por SkillCorner de forma automática y sin
  corregir.
- **Disponibilidad:** SkillCorner borró estos datos del repo el 06/10/2025 (commit `741bdb7`, "deleting
  old data"), pero el historial los sigue sirviendo. Commit fijado:
  `1b99d401ddc82e366c5c20d6860878668fd5858f`; `structured_data.json` mide 77.099.672 bytes (comprobado
  con una cabecera HTTP el 11/11/2026).
- **Lectura con kloppy 3.18:** `skillcorner.load(...)` detecta el formato antiguo; hay que pasarle
  `only_alive=False` e `include_empty_frames=True`, porque por defecto descarta los frames sin posesión
  y los vacíos. Sin probar con este fichero.
- **Los eventos del mismo partido están en StatsBomb** (id 303596), así que se pueden derivar etiquetas.
- **Descarga:** `python validation/scripts/descargar_datos_abiertos.py clasico-2019`.

### Wyscout (Pappalardo et al., 2019)

- **Qué es:** eventos de 7 competiciones completas, entre ellas LaLiga 2017-18 (380 partidos). Incluye
  los 19 del Barça como local en el Camp Nou.
- **Dónde:** figshare, colección 10.6084/m9.figshare.c.4415000.v5. El fichero de eventos (`events.zip`,
  77,3 MB, CC BY 4.0) se descarga desde `https://ndownloader.figshare.com/files/14464685` (comprobado con
  una descarga parcial).
- **Interés:** licencia limpia y eventos de interrupción explícitos (balón fuera, silbato). Otro
  proveedor de eventos para contrastar los recuentos de StatsBomb.

### SoccerNet

- 125 partidos de LaLiga en sus listas, 26 del Barça como local (4 de 2014-15, 4 de 2015-16, 17 de
  2016-17 y 1 de 2019-20).
- Son anotaciones de acciones sobre el vídeo de TV (balón fuera, saque de banda...), con precisión de un
  segundo. Según su SDK, las etiquetas se descargan sin firmar el NDA; el vídeo, en parte, no.
- Para lo que buscamos no aporta nada que no den los eventos de StatsBomb.

## Contraste rápido: ¿cuántos reinicios hay en un partido?

Para comprobar que kloppy 3.18 lee los eventos de la Bundesliga, se contaron los reinicios de un partido
(Colonia–Bayern, `J03WMX`): **102**. Fueron 52 saques de banda, 20 faltas, 14 saques de puerta, 10
córners, 5 saques iniciales y 1 penalti. El Clásico de StatsBomb da 86 pases de reinicio. Siegle y
Lames cuentan unas 108 interrupciones por partido en la Bundesliga.

El Smart Tagging de nuestro partido trae 59 `SET PIECES`: 26 saques de banda, 12 córners, 10 saques de
puerta, 5 faltas y 6 saques iniciales (`DATA.md`). **Si nuestro partido tiene un número de reinicios
normal, al Smart Tagging le faltan muchos, sobre todo faltas.** Es un indicio, no una medida: son
partidos y ligas distintos. El paso 3 de `validation/PASOS.md` lo convierte en una medida con los datos
de LaLiga.

## Cuidado

- **El partido del reto queda excluido en todas las fuentes.** Ninguna lo contiene (StatsBomb llega a
  2020-21, SkillCorner es de 2019-20, Wyscout de 2017-18 y SoccerNet de 2014-15 a 2019-20), y el script
  de descarga rechaza la temporada 2024-25 aunque StatsBomb llegara a publicarla.
- **Nada de datos de LaLiga 2024-25 que incluyan el Barça–Athletic de la jornada 2,** ni siquiera
  agregados de temporada: sería usar datos humanos del partido, prohibido por `RULES.md` §2.
- **Las fuentes de solo eventos (StatsBomb, Wyscout) son un proxy más débil que la Bundesliga:** sin
  tracking, con otra convención de posesión y con tiempos que fallan en torno a un segundo. Sirven para
  recuentos y duraciones de paradas, no para entrenar ni para fijar fronteras.
- **Modelos:** con la Bundesliga y Wyscout (CC BY 4.0) se puede publicar un modelo entrenado, citando.
  Con StatsBomb no está claro (su acuerdo prohíbe distribuir los datos y explotar el análisis derivado),
  y el partido de SkillCorner lo retiró su autor: con esos dos no se publica ningún modelo sin aclararlo.
- **Ningún fichero de estas fuentes entra en el repo:** solo los scripts que los descargan y los
  agregados que salgan de ellos.
