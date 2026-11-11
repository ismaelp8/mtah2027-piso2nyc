---
name: empezar
description: Empieza una tarea nueva en este repo. Actualiza main desde GitHub y crea una rama con nombre convencional (tipo/descripcion). Úsala cuando alguien diga que va a empezar algo ("voy a hacer el detector de D", "quiero probar un HMM", "nueva tarea") o cuando vaya a escribir código estando en main.
argument-hint: "[qué vas a hacer]"
---

# Empezar una tarea

Quien te habla puede no saber git: explica cada paso en una frase sencilla y sin jerga. Los comandos
valen igual en bash y en PowerShell.

Tarea: $ARGUMENTS (si viene vacío, pregunta qué va a hacer).

1. **Identidad.** Ejecuta `git config user.name` y `git config user.email`.
   - Si están vacíos o no son de la persona que te habla, para.
   - Ayúdale a configurarlos con su nombre y el email de su cuenta de GitHub (`CONTRIBUTING.md` §1).
   - Nunca inventes esos valores ni pongas los de otra persona.
2. **Estado actual:** `git branch --show-current` y `git status --short`.
   - **Hay cambios sin commitear y está en `main`:** se vendrán a la rama nueva al crearla. Díselo y
     sigue.
   - **Hay cambios sin commitear y está en otra rama:** pregunta si es trabajo de esa otra tarea. Si lo
     es, propón `/subir` primero. No uses `stash` ni descartes nada sin su permiso.
   - **Hay ficheros de notebooks entre los cambios:** no los abras (ver la regla nº 1 en `CLAUDE.md`).
3. **Actualizar `main`:**
   ```
   git fetch origin
   git switch main          # si hay cambios sin commitear, git los conserva al cambiar de rama
   git pull --ff-only origin main
   ```
   Si el `pull --ff-only` falla, el `main` local tiene commits que no están en GitHub. Para, explícalo y
   no hagas `reset` sin su permiso.
4. **Nombre de la rama:** `tipo/descripcion-corta`, con los tipos de `CONTRIBUTING.md` §2 (`feat`, `exp`,
   `fix`, `docs`, `infra`, `sync`).
   - Minúsculas, guiones, sin tildes y de unos 40 caracteres como mucho.
   - Propón el nombre en una línea. Si no está claro el tipo, pregunta.
   - Comprueba que no existe: `git branch -a --list "*<descripcion>*"`.
5. **Crear la rama:** `git switch -c <rama>`. No la subas todavía: se sube con `/subir`.
6. **Cierre:** dile en dos líneas en qué rama está y que, cuando quiera subir lo que haga, diga
   `/subir`. Si la tarea es una decisión de método, recuérdale `/decision`.
