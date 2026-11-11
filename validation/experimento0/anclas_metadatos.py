"""Anclas de cada partido de la Bundesliga sacadas solo de los metadatos (sin tracking).

Lee los 7 `DFL_02_01_matchinformation_*.xml` y escribe, por partido, el local y el visitante (por su
`Role`, nunca por el orden del documento), las dimensiones del campo, el orden de `<Teams>` en el XML,
los frames esperados por parte (`TotalTime` / 40 ms) y la fracción de tiempo neto (`PlayingTime` /
`TotalTime`). Son datos abiertos de otros partidos: lo puede ejecutar cualquiera, Claude incluido.

Uso:
    python validation/experimento0/anclas_metadatos.py [carpeta_dfl]
"""

import glob
import os
import sys

from lxml import etree

# Frames por partido según la tabla 1 de Bassek et al. (2025), Scientific Data 12, 195.
FRAMES_ARTICULO = {
    "J03WMX": 145967, "J03WN1": 141561, "J03WPY": 146211, "J03WOH": 137214,
    "J03WQQ": 142345, "J03WOY": 142536, "J03WR9": 146810,
}
MS_POR_FRAME = 40


def carpeta_por_defecto():
    base = os.environ.get("MTAH_OPEN_DATA_DIR") or os.path.join(os.path.expanduser("~"),
                                                               "mtah2027-datos-abiertos")
    return os.path.join(base, "dfl")


def leer(ruta):
    raiz = etree.parse(ruta).getroot()
    general = raiz.find(".//General")
    entorno = raiz.find(".//Environment")
    otros = raiz.find(".//OtherGameInformation")
    equipos = raiz.findall(".//Teams/Team")
    roles = {e.get("Role"): e for e in equipos}
    return {
        "partido": general.get("MatchId").split("-")[-1],
        "competicion": general.get("CompetitionName"),
        "local": roles["home"].get("TeamName"),
        "local_id": roles["home"].get("TeamId"),
        "visitante": roles["guest"].get("TeamName"),
        "visitante_id": roles["guest"].get("TeamId"),
        "local_id_general": general.get("HomeTeamId"),
        "orden_teams": [e.get("Role") for e in equipos],
        "campo": (float(entorno.get("PitchX")), float(entorno.get("PitchY"))),
        "total_ms": (int(otros.get("TotalTimeFirstHalf")), int(otros.get("TotalTimeSecondHalf"))),
        "neto_ms": (int(otros.get("PlayingTimeFirstHalf")), int(otros.get("PlayingTimeSecondHalf"))),
    }


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else carpeta_por_defecto()
    rutas = sorted(glob.glob(os.path.join(carpeta, "DFL_02_01_matchinformation_*.xml")))
    if len(rutas) != 7:
        sys.exit("ERROR: esperaba 7 ficheros de metadatos en {} y hay {}".format(carpeta, len(rutas)))
    print("| partido | local–visitante | competición | campo | orden de <Teams> | local por Role = HomeTeamId | "
          "TotalTime/40 (1ª + 2ª) | artículo | diferencia | neto 1ª | neto 2ª | neto total |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for ruta in rutas:
        m = leer(ruta)
        frames = [t // MS_POR_FRAME for t in m["total_ms"]]
        resto = [t % MS_POR_FRAME for t in m["total_ms"]]
        total = sum(frames)
        articulo = FRAMES_ARTICULO[m["partido"]]
        neto = [n / float(t) for n, t in zip(m["neto_ms"], m["total_ms"])]
        neto_total = sum(m["neto_ms"]) / float(sum(m["total_ms"]))
        print("| {} | {}–{} | {} | {:.2f} × {:.2f} | {} | {} | {} + {} = {}{} | {} | {:+d} | {:.1%} | {:.1%} | {:.1%} |".format(
            m["partido"], m["local"], m["visitante"], m["competicion"], m["campo"][0], m["campo"][1],
            ", ".join(m["orden_teams"]), "sí" if m["local_id"] == m["local_id_general"] else "NO",
            frames[0], frames[1], total, "" if not any(resto) else " (resto {} ms)".format(resto),
            articulo, articulo - total, neto[0], neto[1], neto_total))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
