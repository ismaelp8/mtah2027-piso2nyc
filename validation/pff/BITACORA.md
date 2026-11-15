# Mundial 2022 (PFF FC): nota para Claude · 15/11 · sin descarga

> Ismael pide que esto se lo comente a Claude. **No se descarga nada** hasta que la organización conteste
> sobre la licencia de PFF, como ha pedido Claude el 15/11. Esta nota no abre ningún fichero de ese dataset.

## Qué ha dicho Ismael

Las normas del reto no lo prohíben: son otros partidos, y se pueden usar si se citan. Lo dice él el 15/11.
Eso no contesta la licencia del propio dataset. Hasta el mensaje de la organización, no se baja.

## Qué es

- PFF FC, Mundial masculino 2022: **64 partidos**. Tracking de la retransmisión, eventos y notas de
  jugador. Anuncio: https://www.blog.fc.pff.com/blog/pff-fc-release-2022-world-cup-data. Se pide el acceso
  desde ahí; no está en un git público.
- kloppy lo lee (`pff.load_tracking`). Documentación:
  https://kloppy.pysport.org/user-guide/loading-data/pff/. En cada frame trae `ball_state` (`alive` u
  otra cosa) y `ball_owning_team_id`. Con `only_alive=False` no se tiran los frames de balón parado: si
  no, desaparece el `D`, igual que en la Bundesliga.
- El ejemplo de esa documentación va a unos 30 fps (un frame cada ~33 ms). No lo hemos medido nosotros.
- En `docs/investigacion_metodos.md` §5.2 se dejó fuera: no había texto de licencia, y las etiquetas de
  equipo parecían dispersas y arrastradas hacia adelante. Eso hay que volver a medirlo, no darlo por
  cierto. **[fuente, sin volver a abrirlo]**

## Qué conclusión daría, que ahora no tenemos

La Bundesliga tiene la etiqueta del reto (muerto, o un equipo) pero el tracking está revisado. SkillCorner
tiene tracking automático, pero su `D` es «fuera de la fase de juego», no un estado del balón del
proveedor. Metrica son 3 partidos y la etiqueta sale de los eventos.

Este es el único conjunto abierto que junta las dos cosas: tracking de retransmisión y, en cada frame, si
el balón está vivo y de qué equipo es. Con 64 partidos se puede entrenar y dejar un examen, que con los 7
de la Bundesliga no cabe: B5 ya los ha visto todos.

## Cómo se usaría, si la licencia llega

1. Partir los 64 **antes de abrir un fichero**. La mitad de examen no se usa para entrenar ni para mirar
   errores, igual que `validation/skillcorner/BITACORA.md` §8.
2. Escribir la regla de `ball_state` / `ball_owning_team_id` a `H`/`A`/`D` antes de medir nada. Lo primero,
   solo con la mitad de entrenamiento y solo con recuentos: si el equipo viene en todos los frames vivos o
   está vacío y hay que arrastrarlo.
3. No comparar esa huella de retrasos con la tabla oficial para decidir si la etiqueta vale. La misma
   cautela que en Metrica. D21 sigue sin respuesta.
4. B5, si se reentrena, sale como candidato con los coeficientes nuevos y se puntúa en el harness de la
   Bundesliga y en el examen de SkillCorner. El examen de PFF no se mira hasta que el candidato esté
   cerrado.
