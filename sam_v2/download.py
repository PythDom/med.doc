"""Téléchargement de l'export complet SAM v2 (portail public websamcivics, sans authentification).

Usage : python -m sam_v2.download --out data/sam [--xsd 6]
"""
import argparse
import pathlib
import urllib.request
import zipfile

BASE = "https://www.vas.ehealth.fgov.be/websamcivics/samcivics/download"


def latest_version(xsd: int) -> str:
    with urllib.request.urlopen(f"{BASE}/samv2-full-getLastVersion?xsd={xsd}", timeout=60) as r:
        return r.read().decode().strip()


def download(out: pathlib.Path, xsd: int = 6) -> pathlib.Path:
    """Télécharge et décompresse la dernière version ; renvoie le dossier des XML."""
    version = latest_version(xsd)
    target = out / f"sam-{version}"
    if target.exists():
        print(f"Version {version} déjà présente : {target}")
        return target
    out.mkdir(parents=True, exist_ok=True)
    zip_path = out / f"sam-{version}.zip"
    url = f"{BASE}/samv2-download?type=FULL&xsd={xsd}&version={version}"
    print(f"Téléchargement de la version {version}…")
    with urllib.request.urlopen(url, timeout=1800) as r, open(zip_path, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(target)
    zip_path.unlink()
    print(f"Export décompressé dans {target}")
    return target


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=pathlib.Path, default=pathlib.Path("data/sam"))
    p.add_argument("--xsd", type=int, default=6)
    a = p.parse_args()
    download(a.out, a.xsd)
