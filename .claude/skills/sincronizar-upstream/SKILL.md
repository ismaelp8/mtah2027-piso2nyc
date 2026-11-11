---
name: sincronizar-upstream
description: Trae a nuestro repo las correcciones que publique Metrica en el repo oficial (upstream), en una rama sync/upstream-AAAAMMDD con su PR, que se mergea con merge commit. Úsala con "/sincronizar-upstream", "¿ha cambiado algo en el repo oficial?" o "trae los cambios de Metrica".
---

# Sincronizar con `upstream` (repo oficial de Metrica)

Normalmente la hace Ismael. Los cambios de `upstream` son públicos, así que se pueden leer.

1. **Remoto.** Ejecuta `git remote -v`. Si no está `upstream`, añádelo:
   ```
   git remote add upstream https://github.com/metrica-sports/more-than-a-hack-2027.git
   ```
2. **¿Hay algo nuevo?**
   ```
   git fetch upstream
   git log --oneline main..upstream/main
   ```
   Si no sale nada, díselo y termina.
3. **Qué trae.** Ejecuta `git diff --stat main...upstream/main` y lee los commits. Resume en unas líneas
   qué cambia y si afecta a lo que hacemos:
   - el scorer o las métricas;
   - el validador;
   - `games.py` (constantes, alineación);
   - la documentación (reglas, FAQ).

   Un cambio en la evaluación puede cambiar qué conviene optimizar: si lo hay, propón `/decision` para
   dejarlo apuntado.
4. **Con su sí:**
   ```
   git switch main
   git pull --ff-only origin main
   git switch -c sync/upstream-AAAAMMDD
   git merge upstream/main
   ```
   - El mensaje del merge: una frase en español con fecha y resumen, por ejemplo
     `Cambios de upstream del 13/11: el validador acepta CRLF`. El commit lo firma quien sincroniza.
   - Si hay conflicto en un fichero oficial, gana `upstream`: `git checkout --theirs <fichero>` y luego
     `git add <fichero>`. En un fichero nuestro, se resuelve a mano con la persona.
5. **Push y PR** como en `/subir` §6–§8, con:
   - el tipo `sync` marcado;
   - en «Cómo se ha comprobado», que `python evaluation/run_evaluation.py` sigue funcionando y lo que
     imprime de los baselines.

   Dile que esta PR **se mergea con merge commit, no con squash** (`CONTRIBUTING.md` §5).
