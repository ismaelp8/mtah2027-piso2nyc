# Silbato del árbitro en el audio · bitácora

Alternativa **B6** de `docs/investigacion_metodos.md` §2.2: detectar el silbato del árbitro en el audio
del vídeo táctico como señal de balón muerto (`D`). Estaba sin evaluar.

## 1. Criterios fijados antes de medir · Antonio Azuero · 13/11/2026

**Pregunta:** ¿se oye el silbato en el audio del vídeo táctico, y lo bastante limpio como para que valga
la pena construir algo con él? Aquí no se construye el detector de `D`: solo se mira si la señal existe.

**Lo que ya se sabe:** el vídeo táctico trae audio (Antonio, 13/11). `DATA.md` no lo menciona.

**Lo que se espera, por el reglamento** **[inferencia]**:
- el árbitro pita para **parar** el juego en faltas, fueras de juego y goles, y al final de cada parte;
- pita el saque inicial de cada parte y tras gol;
- **no** suele pitar cuando el balón sale por banda o por fondo, ni en la mayoría de los reinicios
  (saques de banda, de puerta, córners).

Así que el silbato, como mucho, marcaría el **inicio** de una parte de los `D`. No sustituye a nada; se
sumaría al resto de señales.

### Cómo se detecta

Código en `validation/scripts/silbato.py`. Todo fijado antes de mirar el audio del partido:

| qué | valor |
|---|---|
| audio | mono, 16 kHz, decodificado con ffmpeg |
| una ventana por frame de vídeo | 1.024 muestras (64 ms, Hann), centrada en el centro del frame |
| alineación | con los `start_time` del vídeo y del audio que da ffprobe |
| banda del silbato | 2.000–4.500 Hz |
| frame "tonal" | algún bin de la banda está ≥ `U` dB por encima de la mediana de su entorno (±300 Hz) |
| `U` | 15 dB; se imprimen también 10 y 20 dB como sensibilidad |
| un silbato | ≥ 4 frames tonales (0,16 s), con huecos de ≤ 2 frames y saltos de frecuencia del pico de ≤ 250 Hz entre frames tonales seguidos |

**Cambio antes de medir el partido (13/11):** la primera versión comparaba el pico con la mediana de
**toda** la banda. Con ruido rosa sintético (más energía en los graves), el borde de 2.000 Hz parecía un
tono: en un partido falso de 2,2 h, sin más silbatos que 4 colocados a propósito, salían 1.153 "silbatos"
con 10 dB, el 94 % a 2.000–2.500 Hz **[medido, sintético]**. Con la mediana del entorno (±300 Hz) salen
44 con 10 dB y solo los colocados con 15 dB **[medido, sintético]**. El cambio se hizo con audio
sintético, sin haber mirado el audio del partido.

**Pruebas sin datos del partido** (las ejecutó Claude, 13/11):
- `validation/scripts/prueba_silbato.py`: 3 silbatos y 3 señuelos (tono grave, chasquido de 40 ms y
  barrido rápido) en ruido rosa. Detecta los 3 en su frame (±1) y ningún señuelo, también leído en
  bloques irregulares y dentro de un mp4 AAC con el audio desplazado 0,4 s. `TODO BIEN`.
- `validation/partido/silbato_audio.py` con un partido falso de 199.319 frames (ruido rosa, 4 silbatos y
  un Smart Tagging inventado): termina en 18 s, encuentra los silbatos colocados y no imprime nada más
  que agregados.

### Qué se mide (solo agregados del partido entero)

1. Metadatos del audio: códec, muestreo, canales y diferencia de inicio y de duración con el vídeo.
2. Silbatos en los frames evaluados: cuántos, por minuto, duración y frecuencia (histogramas).
3. **Comprobaciones con lo que se sabe que se pita:**
   - **final de cada parte** (último frame evaluado de cada parte, de `games.half_video_blocks`):
     ¿hay silbato entre 1 s antes y 3 s después? Resultado como "k de 2";
   - **saques iniciales** (las 6 etiquetas `Kick Off` del Smart Tagging, todas juntas): ¿hay silbato
     entre 2 s antes del inicio de la etiqueta y 1 s después de su fin? "k de 6";
   - **demás reinicios del Smart Tagging** (todos juntos, sin separar por tipo, hasta que Ismael diga si
     se puede): ¿hay silbato en los 30 s antes del inicio de la etiqueta (la parada)? ¿Y dentro de la
     etiqueta (la reanudación)?
4. **Placebo:** las mismas ventanas de los reinicios desplazadas ±60, ±90 y ±120 s. Da la tasa de
   "silbatos" que caen en una ventana por azar.

### Cómo se lee (fijado antes de medir)

- **Señal útil:** final de parte 2 de 2, saques iniciales 5 de 6 o más, y la tasa en los 30 s antes de un
  reinicio claramente por encima del placebo (al menos el doble).
- **Hay señal pero sucia:** pasan las comprobaciones, pero el placebo también da alto (muchos silbatos
  por azar: grada, ruido). Haría falta un detector mejor antes de usarlo.
- **No hay señal:** final de parte o saques iniciales por debajo de la mitad. Se descarta B6 con esta
  configuración y se apunta en `docs/decisiones.md`.
- **Si sale la sincronía mal** (inicio del audio y del vídeo muy distintos y las comprobaciones fallan
  todas), se revisa la alineación antes de concluir nada.
- **No sale** ningún ajuste: si se cambian umbrales después de ver el resultado, se dice y se vuelve a
  validar fuera del partido.

### Límites conocidos

- No hay datos abiertos de otros partidos con audio a mano para validar fuera. Esto es un sondeo de si
  la señal existe, no la validación de un detector.
- Los pitos de la grada también son tonos agudos. Este detector no los separa del árbitro.
- La alineación asume que el vídeo va a 25 fps constantes, como dice `DATA.md`.

### Regla de datos

`validation/partido/silbato_audio.py` lee el vídeo y el Smart Tagging del partido: lo ejecuta solo
Antonio, en local, y pega solo su salida, que son agregados. La prueba con audio sintético
(`validation/scripts/prueba_silbato.py`) no lee nada del partido y la puede ejecutar Claude.

## 2. Cambios antes de medir el partido · Ana Aparicio (con Claude) · 14/11/2026

Según esta bitácora, `silbato_audio.py` todavía no se había ejecutado sobre el partido. Los cambios se
hacen sin haber visto su salida y salen de la revisión del 14/11 (sesión de Ana con Claude). Si alguien
ya la vio, se apunta aquí y estos cambios cuentan como hechos después de medir.

El detector (`validation/scripts/silbato.py`) no cambia: mismas bandas, umbrales y reglas de §1. Cambia
lo que se comprueba con él.

### Qué cambia y por qué

1. **Final de parte: ventana de −5 s a +3 s** (antes, de −1 s a +3 s). `DATA.md` llama "after the
   final whistle" al tramo que sigue al último frame evaluado, pero no dice si el corte cae justo en el
   pitido. En la DFL el tracking sigue 3–5 s después del pitido **[medido, revisión del 13/11]**.
2. **Goles: comprobación nueva.** El árbitro pita al dar un gol. Ventana: del inicio de la etiqueta
   `GOALS` a 10 s después de su fin. Resultado como "k de 4", con su placebo. **[sin verificar]** Que el
   intervalo `GOALS` contenga el momento del gol.
3. **Reinicios por tipo y con 10 s antes** (antes, 30 s antes y todos juntos):
   - Por tipo, con 5 casos o más (`comun.grouped_by_type`, el criterio de `docs/decisiones.md` del
     13/11). Los saques iniciales siguen aparte, en su propia comprobación.
   - **Por tipo**, porque según §1 en los saques de banda, de puerta y córners no se suele pitar: juntarlos
     con las faltas diluye la señal. Ahora esos tipos hacen de **control negativo**: su tasa tendría que
     quedar cerca del placebo.
   - **10 s**, porque con un silbato por minuto de fondo una ventana de 30 s acierta por azar en torno al
     40 % de las veces **[inferencia: 1 − e^(−0,5) ≈ 0,39]**, y "el doble del placebo" se vuelve
     imposible aunque la señal exista.
   - Además de "k de n", la **densidad** de silbatos (por minuto) dentro de las ventanas de cada tipo
     frente a la densidad fuera de toda ventana de reinicio, gol o saque inicial. La densidad no se
     satura.
4. **Silbato → frenazo de los jugadores (nuevo).** No hay datos abiertos con audio para validar fuera
   (§1, límites). La señal independiente más cercana dentro del partido es si los jugadores frenan
   después del silbato. Es la heurística del 14/11: el silbato fecha el inicio de la parada y los
   jugadores confirman que lo es.
   - Velocidad media de los jugadores del ATD (`comun.mean_speed`), con media móvil de 1 s (±0,5 s).
   - Por cada silbato del umbral principal (15 dB) en los frames evaluados, velocidad previa = media de
     los 2 s anteriores. Si es menor de 1,2 m/s (los jugadores ya estaban parados; es el `SLOW_MS` de
     `agregados_jugadores.py`), se cuenta aparte y no entra.
   - **Frenazo:** primer frame de los 6 s siguientes con la velocidad por debajo del 60 % de la previa.
     El 50 % y el 70 % se imprimen como sensibilidad.
   - Se imprime la fracción de silbatos con frenazo, el retraso hasta el frenazo en intervalos gruesos
     (< 0,5 s, 0,5–1, 1–2, 2–4 y ≥ 4 s) con sus cuantiles, y el cociente entre la velocidad de 3 a 5 s
     después y la previa.
   - **Placebo:** lo mismo con los silbatos desplazados ±60, ±90 y ±120 s.
5. **ffmpeg:** el mensaje de error ya no da solo la orden de Mac, y la salida imprime la versión de
   ffmpeg. Si el silbato entra en el pipeline, ffmpeg será una dependencia de sistema con versión
   fijada: la entrega tiene que regenerarse byte a byte.

### Cómo se lee (sustituye a la de §1)

- **Señal útil:** final de parte 2 de 2, saques iniciales 5 de 6 o más y, además, al menos una de estas
  dos:
  - faltas o goles con una tasa en su ventana de al menos el doble del placebo;
  - frenazo (60 %) tras los silbatos con jugadores en movimiento al menos el doble que en el placebo.
- **Control:** los tipos que no se pitan (banda, puerta, córner) cerca del placebo. Si salen tan altos
  como las faltas, el detector cuenta algo que no es el silbato del árbitro (grada, ruido de los
  reinicios) y la señal es sucia.
- **No hay señal:** final de parte o saques iniciales por debajo de la mitad. Se descarta B6 con esta
  configuración y se apunta en `docs/decisiones.md`.
- **El retraso entre silbato y frenazo es descriptivo.** No fija ningún umbral del detector de `D`
  (`CLAUDE.md`: nada se ajusta con el partido). La ventana del pipeline se fija antes, razonada y con la
  DFL; esto solo la comprueba.

### Límites nuevos

- Faltas (5) y goles (4) son pocos casos: su "k de n" es indicativo, no una prueba.
- Las ventanas placebo pueden caer en otras paradas, porque hay una cada minuto y medio más o menos. El
  placebo sale alto y la comprobación es conservadora.

### Regla de datos

`silbato_audio.py` ahora lee también el ATD (la velocidad de los jugadores). Sigue igual: lo ejecuta solo
Antonio, en local, y pega solo su salida. Se probó con un partido sintético (vídeo, Smart Tagging y ATD
inventados), nunca con el real.
