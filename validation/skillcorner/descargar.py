"""Descarga los 20 partidos abiertos de SkillCorner (A-League 2024/25) fuera del repo.

Datos abiertos de otros partidos: tracking automático de la retransmisión a 10 fps, con posesión de equipo
por frame, fases de juego y eventos. Licencia MIT; SkillCorner pide que se le cite. Lo puede ejecutar
cualquiera, Claude incluido. Solo imprime nombres, tamaños y recuentos.

    python validation/skillcorner/descargar.py [--destino DIR] [--limite N]

La versión va fijada a un commit. El tracking va por Git LFS: se baja de media.githubusercontent.com y se
comprueba su sha256 contra el puntero LFS del mismo commit. Si un fichero ya está con el tamaño correcto, no
se vuelve a bajar.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "scripts"))
import descargar_datos_abiertos as dda  # noqa: E402

SHA = "4340d274572876239c154c90bc507a9b3250a656"  # master del 14/09/2026
RAW = "https://raw.githubusercontent.com/SkillCorner/opendata/" + SHA + "/{ruta}"
LFS = "https://media.githubusercontent.com/media/SkillCorner/opendata/" + SHA + "/{ruta}"
LIGEROS = ("match.json", "phases_of_play.csv", "dynamic_events.csv")


def leer(url):
    peticion = urllib.request.Request(url, headers={"User-Agent": dda.AGENTE})
    with urllib.request.urlopen(peticion, timeout=120) as respuesta:
        return respuesta.read()


def sha256_de(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def puntero_lfs(ruta):
    """(sha256, bytes) del puntero LFS de un fichero del repo."""
    campos = dict(linea.split(" ", 1) for linea in leer(RAW.format(ruta=ruta)).decode("utf-8").splitlines() if " " in linea)
    if not campos.get("oid", "").startswith("sha256:"):
        sys.exit("ERROR: {} no es un puntero LFS".format(ruta))
    return campos["oid"].split(":", 1)[1], int(campos["size"])


def partidos():
    return sorted(int(m["id"]) for m in json.loads(leer(RAW.format(ruta="data/matches.json")).decode("utf-8")))


def bajar(destino, limite=None):
    carpeta = destino / "skillcorner"
    ids = partidos()
    print("SkillCorner, A-League 2024/25: {} partidos -> {}".format(len(ids), carpeta))
    for k, id_ in enumerate(ids):
        if limite is not None and k >= limite:
            break
        base = "data/matches/{0}/{0}_".format(id_)
        for nombre in LIGEROS:
            dda.descargar(RAW.format(ruta=base + nombre), carpeta / str(id_) / "{}_{}".format(id_, nombre))
        ruta = base + "tracking_extrapolated.jsonl"
        sha, tam = puntero_lfs(ruta)
        fichero = carpeta / str(id_) / "{}_tracking_extrapolated.jsonl".format(id_)
        dda.descargar(LFS.format(ruta=ruta), fichero, tam)
        if sha256_de(fichero) != sha:
            fichero.unlink()
            sys.exit("ERROR: el sha256 de {} no coincide con el puntero LFS".format(fichero.name))
    print("Cita: SkillCorner Open Data (https://github.com/SkillCorner/opendata, commit {}), licencia MIT."
          .format(SHA[:12]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--destino", type=Path, default=dda.destino_por_defecto())
    parser.add_argument("--limite", type=int, default=None, help="para probar: como mucho N partidos")
    args = parser.parse_args()
    bajar(dda.comprobar_destino(args.destino), args.limite)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
