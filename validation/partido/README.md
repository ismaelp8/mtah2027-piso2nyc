# Scripts que leen datos del partido

**Los ejecuta solo una persona, en local.** Claude los escribe, pero no los ejecuta: leen datos del
partido (regla nº 1 de `CLAUDE.md`).

- Imprimen solo agregados (recuentos, porcentajes y métricas), así que su salida se puede pegar a Claude
  tal cual.
- Si fallan, no deberían imprimir valores de datos: solo el tipo de error y las líneas del código.
- No escriben ficheros en el repo.
- Qué hace cada uno está en la tabla de scripts de [`validation/README.md`](../README.md).

Se ejecutan desde la raíz del repo, con el entorno de siempre y `MTAH_DATA_DIR` apuntando a los datos. Por
ejemplo:

```bash
python validation/partido/recuento_ventana.py
```
