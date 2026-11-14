# Scripts de la revisión del detector de balón muerto (13/11/2026)

Ninguno lee datos del partido: solo la GT pública, una GT sintética o el partido abierto `J03WMX` de la
Bundesliga (Bassek et al., 2025, CC BY 4.0). Los puede ejecutar cualquiera, Claude incluido. Resultado y
lectura en `validation/resultados/2026-11-13_revision_balon_muerto.md`.

| script | qué mide | datos |
|---|---|---|
| `coste_errores_D.py` | spellF1 de cada error propio del detector de `D` (paradas perdidas, bordes tarde o pronto, `D` que parpadea, equipo equivocado al reanudar) sobre la GT sintética de `sensibilidad_metrica.py` | ninguno |
| `gt_publica_sin_D.py` | lo mismo, con el equipo oráculo de la GT pública (solo lectura de la métrica) | GT pública |
| `prueba_io.py` | `possession/io.py` con un ATD sintético: alineación, `NaN`, escala a metros, slots variables y tiempo con 199.319 líneas × 46 slots | ninguno |
| `dfl_D_jugadores.py` | ¿sirven los jugadores solos para `D`? AUC por rasgo, dos detectores (umbral con histéresis y regresión logística) con umbral elegido en una parte y evaluado en la otra, latencias de inicio y fin, recall por tipo de reinicio | DFL `J03WMX` |
| `dfl_D_precision.py` | con equipo oráculo: qué precisión de frontera y qué fracción de paradas detectadas hacen que el `D` sume; sesgos sistemáticos; duración de las paradas por tipo | DFL `J03WMX` |

Los dos últimos necesitan `lxml` y `scikit-learn`, que no están en `requirements.txt` (es el del scorer y
lo decide Ismael): `pip install lxml scikit-learn`. Y hace falta la caché del partido:

```bash
python validation/scripts/descargar_datos_abiertos.py dfl --limite 1   # baja J03WMX (418 MB) y los metadatos
python validation/experimento0/dfl_lector.py J03WMX                     # caché .npz junto a los datos (13 s, <200 MB)
python validation/scripts/revision_balon_muerto/dfl_D_jugadores.py J03WMX
python validation/scripts/revision_balon_muerto/dfl_D_precision.py
```
