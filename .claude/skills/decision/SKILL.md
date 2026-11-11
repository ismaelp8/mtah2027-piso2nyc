---
name: decision
description: Apunta una decisión de método en docs/decisiones.md con la plantilla del equipo (qué se probó, cómo se midió, resultado, decisión y descartes). Úsala con "/decision", "apunta esto", "deja constancia de que elegimos X" o cuando se elija entre dos enfoques.
argument-hint: "[título corto]"
---

# Apuntar una decisión

Título: $ARGUMENTS

`docs/decisiones.md` es la materia prima del documento técnico. Una entrada buena se escribe el mismo
día, es corta y tiene números agregados.

1. **Rama.** Si está en `main`, propón `/empezar` antes: la entrada viaja en la PR de la tarea, o en una
   rama `docs/` si va sola.
2. **Campos** de la plantilla del fichero. Sácalos de la conversación y pregunta solo lo que falte:
   ```
   ### AAAA-MM-DD · <módulo> · <título corto>
   Quién:
   Qué se probó:
   Cómo se midió (dataset, nº de partidos/posesiones, métrica):
   Resultado:
   Decisión y por qué:
   Descartado:
   ```
   - **Fecha:** la de hoy.
   - **Módulo:** infraestructura, balón, `D`, candidatos, temporal, `X`, validación, documento…
   - **Quién:** la persona que decide, no Claude.
3. **Comprobaciones antes de escribir:**
   - **Los números son agregados** de la validación externa o del partido (spellF1, macroF1,
     recuentos). Nunca valores por frame.
   - **Si la decisión se apoya en la ventana pública de 5 minutos,** dilo: no vale para elegir entre
     versiones. Propón medirlo con la validación externa.
   - **Si la diferencia de spellF1 es menor de ~0,04,** apúntala como empate.
4. **Escribir.** Añade la entrada al final del fichero, en orden cronológico, separada por una línea en
   blanco. No toques las entradas de otros.
5. **Cierre.** Enséñale la entrada. Va en el próximo commit de la rama (`/subir`).
