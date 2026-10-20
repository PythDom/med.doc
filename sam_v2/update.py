"""Mise à jour en une commande : télécharge le dernier export SAM v2 et recharge la base SQLite.

Usage : python -m sam_v2.update [--data data]
Les anciennes versions de l'export sont supprimées pour libérer l'espace disque (≈ 2,7 Go par version).
"""
import argparse
import datetime as dt
import pathlib
import shutil

from sam_v2 import download, load


def update(data: pathlib.Path):
    xml_dir = download.download(data / "sam")
    for old in (data / "sam").glob("sam-*"):
        if old.is_dir() and old != xml_dir:
            shutil.rmtree(old)
    tmp = data / "sam.sqlite.tmp"
    load.load(xml_dir, tmp, dt.date.today().isoformat())
    tmp.replace(data / "sam.sqlite")
    print(f"Base à jour : {data / 'sam.sqlite'}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=pathlib.Path, default=pathlib.Path("data"))
    update(p.parse_args().data)
