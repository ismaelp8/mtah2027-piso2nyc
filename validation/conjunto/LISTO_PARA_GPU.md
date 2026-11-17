# Rondas del modelo conjunto para la máquina con GPU

Esto es para quien ejecute una ronda de 8 pliegues en la máquina de la RTX 3060, sin haber seguido el trabajo. Una ronda
son unos 21 minutos en la GPU; en un portátil sin GPU, unas 7 horas. **Solo se ejecuta la ronda de un candidato cuando
su piloto haya pasado** (`docs/decisiones.md`, 17/11, la entrada de cada candidato). Todo son datos abiertos de otros
partidos: no se toca nada del partido del reto.

## Antes de empezar

1. **La rama:** `git fetch origin` y `git switch exp/k2-siguiente` (o la rama donde esté el candidato), sin cambios
   sin commitear.
2. **El entorno:** `mtah2027-conjunto` (torch con CUDA, numpy 2.5.4, pandas 3.1.1, lxml y kloppy). Comprueba que torch
   ve la GPU:
   `python -c "import torch; print(torch.cuda.is_available())"` tiene que decir `True`.
3. **Los datos abiertos y la caché** (`<datos abiertos>/conjunto_cache/`, por defecto `~/mtah2027-datos-abiertos`, o
   la carpeta a la que apunte `MTAH_OPEN_DATA_DIR`):
   - los 7 de la DFL y los 10 de SkillCorner: `python validation/conjunto/exportar.py` (salta los que ya estén);
   - Metrica, solo para K7: `python validation/conjunto/exportar_metrica.py`.

Todos los comandos van desde la carpeta del repo.

## K8 (pérdida por secuencia), si su piloto pasa

    python validation/conjunto/ronda_pliegues.py entrenar_k8.py --etiqueta k8 -- --dispositivo cuda
    python validation/conjunto/medir_pliegues.py --pesos pesos_k8.npz --nombre K8 > k8_ronda.md

- La primera línea entrena los 8 pliegues (los 7 de la DFL y el de «todos») y junta los pesos en
  `conjunto_cache/pesos_k8.npz`, con α = 4. Si se corta, se vuelve a lanzar igual: salta los pliegues que ya estén.
- La segunda mide K8 frente a K2 y a `main` en los 17 partidos, cada uno con el pliegue que no lo vio. Tarda unos
  minutos.
- **Qué pegar después:** el fichero `k8_ronda.md` entero (solo tiene agregados) y, de la salida de la primera línea, la
  tabla «Fuera de muestra» de cada pliegue y la última línea («Ronda … hecha en … min»).
- **Comprobación previa, una sola vez por máquina** (unos minutos, sin GPU):
  `python validation/conjunto/medir_pliegues.py --comprobar` tiene que terminar con «coincide». Si dice «NO COINCIDE»,
  no se sigue: hay algo distinto en el entorno o en el código.

## Lo que todavía no tiene ronda

- **K7 con los tres proveedores** (DFL, SkillCorner y Metrica), si pasa la prueba dejando un proveedor fuera: falta el
  script, que se escribe con su regla.
- **K6, varias semillas por pliegue** para promediarlas: hace falta que `medir_pliegues.py` acepte varios ficheros de
  pesos. Se escribe si el piloto de semillas lo merece.
