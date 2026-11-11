"""Descarga los datos abiertos de OTROS partidos que usa la validación externa.

Nada de esto es del partido del reto: son datos públicos de otros partidos, que las reglas permiten
y que Claude sí puede leer. Se guardan FUERA del repo y nunca se suben (licencias y tamaño).

Fuentes, con la versión fijada para que la descarga sea siempre la misma:

  dfl                   Los 7 partidos de la Bundesliga de Bassek et al. (2025): tracking TRACAB a
                        25 Hz con equipo poseedor y balón activo/inactivo en cada frame, más eventos.
                        CC BY 4.0. figshare 10.6084/m9.figshare.28196177.v1, con comprobación md5.
                        2,63 GB (con --solo-ligeros, 5 MB: sin los 7 XML de posiciones).
  statsbomb-barca-local Eventos de StatsBomb de los partidos de LaLiga del Barça como local (todos en
                        el Camp Nou). Por defecto, las 6 últimas temporadas publicadas (109 partidos,
                        unos 0,4 GB). Acuerdo de StatsBomb: uso para investigación, sin redistribuir,
                        con su logo en lo que se publique; piden registrarse en su web. La temporada
                        2024-25, la del partido del reto, está excluida aunque llegara a publicarse.
  clasico-2019          Barça–Real Madrid del 18/12/2019 en el Camp Nou: tracking de broadcast de
                        SkillCorner (10 fps, sin corregir; versión de 2020, ya retirada de su repo
                        pero accesible en el historial) y los eventos de StatsBomb del mismo partido.

Uso:
    python validation/scripts/descargar_datos_abiertos.py dfl
    python validation/scripts/descargar_datos_abiertos.py dfl --solo-ligeros
    python validation/scripts/descargar_datos_abiertos.py statsbomb-barca-local [--temporadas 2019/2020 2020/2021] [--con-360]
    python validation/scripts/descargar_datos_abiertos.py statsbomb-barca-local --temporadas todas
    python validation/scripts/descargar_datos_abiertos.py clasico-2019

    --destino DIR   carpeta de datos abiertos; por defecto $MTAH_OPEN_DATA_DIR o ~/mtah2027-datos-abiertos
    --limite N      para probar: como mucho N ficheros de posiciones (dfl) o N partidos (statsbomb)

Si un fichero ya está con el tamaño correcto, no se vuelve a bajar. Solo imprime nombres, tamaños y
recuentos, nunca contenido.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# -- versiones fijadas ---------------------------------------------------------------------------
# DFL: ids, nombres, tamaños y md5 leídos de la API de figshare (artículo 28196177, versión 1).
# El host springernature.figshare.com que usa kloppy 3.18 responde a los scripts con un desafío
# antirrobots; ndownloader.figshare.com sirve el mismo fichero. Espejo: huggingface.co/datasets/
# pysport/idsse-data (revisión a715a38dfbaf5f58e431727c2b78d174101a703c), mismos nombres.
DFL_URL = "https://ndownloader.figshare.com/files/{id}"
DFL_FICHEROS = [
    # (id figshare, nombre, bytes, md5)
    (51643475, "DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WMX.xml", 11930, "bc5d5b21dbcf36aa30f4cd0428309f6b"),
    (51643472, "DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WN1.xml", 11722, "37b0f85588c0acfb995fe633c7ac2e0d"),
    (51643478, "DFL_02_01_matchinformation_DFL-COM-000002_DFL-MAT-J03WOH.xml", 11745, "b9710781d400dd812f62b0a6e3d7bce8"),
    (51643481, "DFL_02_01_matchinformation_DFL-COM-000002_DFL-MAT-J03WOY.xml", 11952, "7b021e577fca917a63111d55cc29ae5b"),
    (51643487, "DFL_02_01_matchinformation_DFL-COM-000002_DFL-MAT-J03WPY.xml", 11922, "65a4568e4f374af94d3c1015cbc7c4f5"),
    (51643484, "DFL_02_01_matchinformation_DFL-COM-000002_DFL-MAT-J03WQQ.xml", 11932, "5979209af316a914ce57347d0633df6c"),
    (51643490, "DFL_02_01_matchinformation_DFL-COM-000002_DFL-MAT-J03WR9.xml", 11823, "5e2d580d3d8ed97e32959de90d04992b"),
    (51643493, "DFL_03_02_events_raw_DFL-COM-000001_DFL-MAT-J03WMX.xml", 776578, "2d88e180a1f63c7e4157feb980fc7255"),
    (51643496, "DFL_03_02_events_raw_DFL-COM-000001_DFL-MAT-J03WN1.xml", 612114, "83e8ed7ea8e8ebbbdc61f61ac3534008"),
    (51643499, "DFL_03_02_events_raw_DFL-COM-000002_DFL-MAT-J03WOH.xml", 635747, "ab66e51512f39d06f49f27dd3b4c2f40"),
    (51643502, "DFL_03_02_events_raw_DFL-COM-000002_DFL-MAT-J03WOY.xml", 683018, "64b1be01d6ff6848168efebd56f344b9"),
    (51643505, "DFL_03_02_events_raw_DFL-COM-000002_DFL-MAT-J03WPY.xml", 698898, "f68482441d38723d69f244f896482803"),
    (51643508, "DFL_03_02_events_raw_DFL-COM-000002_DFL-MAT-J03WQQ.xml", 732186, "b7e9d82af4034539d802319be6c57776"),
    (51643511, "DFL_03_02_events_raw_DFL-COM-000002_DFL-MAT-J03WR9.xml", 681050, "c13bc5efa5eca4a022cc678210b87d5f"),
    (51643514, "DFL_04_03_positions_raw_observed_DFL-COM-000001_DFL-MAT-J03WMX.xml", 418524833, "e4273a2adf5dbd9d4ec42def2f01905c"),
    (51643517, "DFL_04_03_positions_raw_observed_DFL-COM-000001_DFL-MAT-J03WN1.xml", 391722803, "bacb2f609c1d1b0bfc906f6b9d4109f2"),
    (51643520, "DFL_04_03_positions_raw_observed_DFL-COM-000002_DFL-MAT-J03WOH.xml", 348945715, "3efff25a86a61768e7d253b4bba137a3"),
    (51643523, "DFL_04_03_positions_raw_observed_DFL-COM-000002_DFL-MAT-J03WOY.xml", 362567859, "4e1063e0a0ae499920cf68ac1aa3ab4e"),
    (51643526, "DFL_04_03_positions_raw_observed_DFL-COM-000002_DFL-MAT-J03WPY.xml", 371688499, "e56ff1336a334f8da51110fbe7cab764"),
    (51643529, "DFL_04_03_positions_raw_observed_DFL-COM-000002_DFL-MAT-J03WQQ.xml", 356219423, "9105bad987191d3c3c362c1fce9a4fcd"),
    (51643532, "DFL_04_03_positions_raw_observed_DFL-COM-000002_DFL-MAT-J03WR9.xml", 372934140, "e060bb7d7a5a3bfbd15bbf9bc631024d"),
]

# StatsBomb: commit del repo statsbomb/open-data del 11/11/2026. LaLiga es la competición 11.
SB_SHA = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
SB_URL = "https://raw.githubusercontent.com/statsbomb/open-data/" + SB_SHA + "/{ruta}"
SB_LALIGA = 11
SB_TEMPORADAS_DEFECTO = ("2015/2016", "2016/2017", "2017/2018", "2018/2019", "2019/2020", "2020/2021")
# El partido del reto es de LaLiga 2024-25 (jornada 2). RULES.md §2 prohíbe usar datos humanos sobre él,
# de cualquier fuente. StatsBomb no publica esa temporada, pero si algún día la publica, no se baja.
SB_TEMPORADAS_EXCLUIDAS = ("2024/2025",)

# SkillCorner: commit del 09/10/2020 con los 9 partidos de 2019/20. El 06/10/2025 se borraron del
# HEAD del repo, pero el historial los sigue sirviendo. Partido 2841 = Barça–Real Madrid, Camp Nou.
SC_SHA = "1b99d401ddc82e366c5c20d6860878668fd5858f"
SC_URL = "https://raw.githubusercontent.com/SkillCorner/opendata/" + SC_SHA + "/{ruta}"
SC_FICHEROS = [
    ("data/matches/2841/match_data.json", 14377),
    ("data/matches/2841/structured_data.json", 77099672),
    ("README.md", 5071),
    ("LICENSE", 1097),
]
SB_CLASICO = 303596  # el mismo partido en StatsBomb

AGENTE = "mtah2027-validacion/1.0"


def destino_por_defecto():
    return Path(os.environ.get("MTAH_OPEN_DATA_DIR") or (Path.home() / "mtah2027-datos-abiertos"))


def comprobar_destino(destino):
    """Se niega a escribir dentro del repo o de los datos del partido, o en una carpeta que los contenga.

    Lo segundo importa porque Claude puede leer la carpeta de datos abiertos: si contuviera los datos
    del partido (por ejemplo, --destino ~ con los datos en ~/mtah2027-data), una búsqueda recursiva
    pasaría por ellos.
    """
    destino = destino.resolve()
    if destino == ROOT or ROOT in destino.parents:
        sys.exit("ERROR: {} está dentro del repo. Los datos abiertos van fuera.".format(destino))
    if destino in ROOT.parents:
        sys.exit("ERROR: {} contiene el repo. Usa una carpeta propia para los datos abiertos."
                 .format(destino))
    if any(parte.lower() == "mtah2027-data" for parte in destino.parts):
        sys.exit("ERROR: {} está dentro de una carpeta mtah2027-data, la de los datos del partido."
                 .format(destino))
    if (destino / "mtah2027-data").exists():
        sys.exit("ERROR: {} contiene la carpeta mtah2027-data. Usa una carpeta propia para los datos "
                 "abiertos.".format(destino))
    datos_partido = os.environ.get("MTAH_DATA_DIR")
    if datos_partido:
        datos_partido = Path(datos_partido).resolve()
        if destino == datos_partido or datos_partido in destino.parents:
            sys.exit("ERROR: {} está dentro de MTAH_DATA_DIR.".format(destino))
        if destino in datos_partido.parents:
            sys.exit("ERROR: {} contiene MTAH_DATA_DIR. Usa una carpeta propia para los datos abiertos."
                     .format(destino))
    return destino


def md5_de(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def descargar(url, ruta, tam=None, md5=None):
    """Baja url a ruta. Si ya existe con el tamaño esperado, no hace nada. Devuelve los bytes."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists() and (tam is None or ruta.stat().st_size == tam):
        print("  ya está   {:>10.1f} MB  {}".format(ruta.stat().st_size / 1e6, ruta.name))
        return ruta.stat().st_size
    parcial = ruta.with_name(ruta.name + ".part")
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(peticion, timeout=120) as respuesta, open(parcial, "wb") as f:
        shutil.copyfileobj(respuesta, f, 1 << 20)
    bytes_ = parcial.stat().st_size
    if tam is not None and bytes_ != tam:
        parcial.unlink()
        sys.exit("ERROR: {} tiene {} bytes y se esperaban {}".format(ruta.name, bytes_, tam))
    if md5 is not None and md5_de(parcial) != md5:
        parcial.unlink()
        sys.exit("ERROR: el md5 de {} no coincide".format(ruta.name))
    parcial.replace(ruta)
    print("  bajado    {:>10.1f} MB  {}{}".format(bytes_ / 1e6, ruta.name, "  (md5 ok)" if md5 else ""))
    return bytes_


def bajar_dfl(destino, solo_ligeros, limite):
    carpeta = destino / "dfl"
    print("DFL / Bundesliga -> {}".format(carpeta))
    grandes = 0
    for id_, nombre, tam, md5 in DFL_FICHEROS:
        es_grande = "positions" in nombre
        if es_grande and solo_ligeros:
            continue
        if es_grande and limite is not None and grandes >= limite:
            continue
        grandes += int(es_grande)
        descargar(DFL_URL.format(id=id_), carpeta / nombre, tam, md5)
    print("Cita: Bassek, Rein, Weber y Memmert (2025), Scientific Data 12, 195. CC BY 4.0, con "
          "autorización de la DFL.")


def partidos_barca_local(carpeta, temporadas):
    """[(temporada, partido)] de LaLiga con el Barça de local en las temporadas pedidas."""
    competiciones = carpeta / "competitions.json"
    descargar(SB_URL.format(ruta="data/competitions.json"), competiciones)
    with open(competiciones, encoding="utf-8") as f:
        laliga = {c["season_name"]: c["season_id"] for c in json.load(f)
                  if c["competition_id"] == SB_LALIGA}
    if temporadas == ["todas"]:
        temporadas = sorted(t for t in laliga if t not in SB_TEMPORADAS_EXCLUIDAS)
    excluidas = [t for t in temporadas if t in SB_TEMPORADAS_EXCLUIDAS]
    if excluidas:
        sys.exit("ERROR: la temporada {} contiene el partido del reto y está excluida (RULES.md §2)."
                 .format(", ".join(excluidas)))
    desconocidas = [t for t in temporadas if t not in laliga]
    if desconocidas:
        sys.exit("ERROR: temporadas sin datos de LaLiga en StatsBomb: {}. Hay: {}".format(
            desconocidas, ", ".join(sorted(laliga))))
    salida = []
    for temporada in temporadas:
        ruta = carpeta / "matches" / "{}_{}.json".format(SB_LALIGA, laliga[temporada])
        descargar(SB_URL.format(ruta="data/matches/{}/{}.json".format(SB_LALIGA, laliga[temporada])), ruta)
        with open(ruta, encoding="utf-8") as f:
            partidos = [p for p in json.load(f) if p["home_team"]["home_team_name"] == "Barcelona"]
        salida += [(temporada, p) for p in sorted(partidos, key=lambda p: p["match_date"])]
    return salida


def bajar_statsbomb(destino, temporadas, con_360, limite):
    carpeta = destino / "statsbomb"
    print("StatsBomb, LaLiga, Barça como local -> {}".format(carpeta))
    partidos = partidos_barca_local(carpeta, temporadas)
    print("partidos del Barça como local: {}  (estadios: {})".format(
        len(partidos), sorted({(p.get("stadium") or {}).get("name", "?") for _, p in partidos})))
    if limite is not None:
        partidos = partidos[:limite]
    total, con_tres = 0, 0
    for _, p in partidos:
        total += descargar(SB_URL.format(ruta="data/events/{}.json".format(p["match_id"])),
                           carpeta / "events" / "{}.json".format(p["match_id"]))
        if con_360 and p.get("match_status_360") == "available":
            con_tres += 1
            total += descargar(SB_URL.format(ruta="data/three-sixty/{}.json".format(p["match_id"])),
                               carpeta / "three-sixty" / "{}.json".format(p["match_id"]))
    print("eventos de {} partidos{}: {:.0f} MB".format(
        len(partidos), ", 360 de {}".format(con_tres) if con_360 else "", total / 1e6))
    print("Uso: acuerdo de StatsBomb (LICENSE.pdf de su repo). Citar a StatsBomb con su logo.")


def bajar_clasico(destino, solo_ligeros):
    carpeta = destino / "skillcorner"
    print("SkillCorner, Barça–Real Madrid 18/12/2019 (Camp Nou) -> {}".format(carpeta))
    for ruta, tam in SC_FICHEROS:
        if solo_ligeros and tam > 1e6:
            continue
        descargar(SC_URL.format(ruta=ruta), carpeta / ruta.replace("/", "_"), tam)
    sb = destino / "statsbomb" / "events" / "{}.json".format(SB_CLASICO)
    print("StatsBomb, el mismo partido -> {}".format(sb.parent))
    if not solo_ligeros:
        descargar(SB_URL.format(ruta="data/events/{}.json".format(SB_CLASICO)), sb)
    print("Cita: SkillCorner (pide que se le cite) y StatsBomb (con su logo).")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("fuente", choices=("dfl", "statsbomb-barca-local", "clasico-2019"))
    parser.add_argument("--destino", type=Path, default=None)
    parser.add_argument("--solo-ligeros", action="store_true",
                        help="sin los ficheros grandes (para probar)")
    parser.add_argument("--temporadas", nargs="+", default=list(SB_TEMPORADAS_DEFECTO),
                        help="temporadas de StatsBomb, por ejemplo 2019/2020, o 'todas'")
    parser.add_argument("--con-360", action="store_true", help="StatsBomb: también los 360")
    parser.add_argument("--limite", type=int, default=None,
                        help="para probar: como mucho N ficheros de posiciones (dfl) o N partidos "
                             "(statsbomb-barca-local); clasico-2019 lo ignora")
    args = parser.parse_args()

    destino = comprobar_destino(args.destino or destino_por_defecto())
    destino.mkdir(parents=True, exist_ok=True)
    if args.fuente == "dfl":
        bajar_dfl(destino, args.solo_ligeros, args.limite)
    elif args.fuente == "statsbomb-barca-local":
        bajar_statsbomb(destino, args.temporadas, args.con_360, args.limite)
    else:
        bajar_clasico(destino, args.solo_ligeros)


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")  # tildes bien también al redirigir a un fichero
    main()
