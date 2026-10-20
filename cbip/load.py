"""Base de données du Répertoire commenté des médicaments du CBIP (téléchargement libre, mise à jour mensuelle).

Le CBIP publie vers le 18 de chaque mois une version CSV de sa base sur https://www.cbip.be/fr/download.
On en garde le lien entre chaque CNK et son chapitre du Répertoire, et le texte des chapitres
(positionnement, indications, effets indésirables, grossesse et allaitement, interactions, posologie…).

Usage : python -m cbip.load --db data/sam.sqlite [--lang fr]
La base SQLite doit déjà exister (python -m sam_v2.load) : les tables du CBIP y sont ajoutées ou remplacées.
"""
import argparse
import csv
import io
import pathlib
import re
import sqlite3
import urllib.parse
import urllib.request
import zipfile

DOWNLOAD_PAGE = "https://www.cbip.be/{lang}/download"
SCHEMA = """
DROP TABLE IF EXISTS cbip_product;
DROP TABLE IF EXISTS cbip_chapter;
CREATE TABLE cbip_product (cnk TEXT PRIMARY KEY, chapter_code TEXT, posology TEXT, note TEXT);
CREATE TABLE cbip_chapter (chapter_code TEXT PRIMARY KEY, title TEXT, intro TEXT, posology TEXT);
"""


def fetch(url, timeout=120):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (med.doc, usage personnel)"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def latest_archive_url(lang="fr"):
    """Lien de la dernière archive CSV publiée (la page les liste de la plus récente à la plus ancienne)."""
    page = fetch(DOWNLOAD_PAGE.format(lang=lang)).decode("utf-8", "replace")
    suffix = "Fr" if lang == "fr" else "Nl"
    match = re.search(r'href="([^"]*csv4Emd_' + suffix + r'_[^"]+\.zip)"', page)
    if not match:
        raise SystemExit("Archive CSV du CBIP introuvable sur la page de téléchargement.")
    return urllib.parse.urljoin(DOWNLOAD_PAGE.format(lang=lang), match.group(1).replace("&amp;", "&"))


def read_csv(archive, name):
    with archive.open(name) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter=";"))


def load_archive(archive_bytes, db_path, version):
    archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    for r in read_csv(archive, "Hyr.csv"):
        db.execute("INSERT OR REPLACE INTO cbip_chapter VALUES (?,?,?,?)",
                   (r["HYR"], r["TI"].strip(), r["INTRO"].strip() or None, r["POS"].strip() or None))
    for r in read_csv(archive, "MPP.csv"):
        db.execute("INSERT OR REPLACE INTO cbip_product VALUES (?,?,?,?)",
                   (r["mppcv"], r["hyr_"], r["pos"].strip() or None, r["note"].strip() or None))
    db.execute("INSERT OR REPLACE INTO meta VALUES ('cbip_version', ?)", (version,))
    db.commit()
    db.close()


def load(db_path, lang="fr"):
    url = latest_archive_url(lang)
    version = re.search(r"csv4Emd_\w+?_(\w+)\.zip", url).group(1)
    print(f"Base du CBIP {version}…")
    load_archive(fetch(url), db_path, version)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=pathlib.Path, default=pathlib.Path("data/sam.sqlite"))
    p.add_argument("--lang", choices=("fr", "nl"), default="fr")
    a = p.parse_args()
    load(a.db, a.lang)
