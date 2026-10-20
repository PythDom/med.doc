"""Génère des dossiers KMEHR **fictifs** pour essayer le tableau de bord sans données réelles.

Usage : python -m dashboard.sample --db data/sam.sqlite --out data/exemple-fictif.zip [--patients 250]
Les patients, dates et quantités sont inventés ; seuls les CNK sont de vrais produits de la base SAM.
"""
import argparse
import datetime as dt
import pathlib
import random
import sqlite3
import zipfile
from xml.sax.saxutils import escape

# Traitements typiques de médecine générale : (classe ATC, probabilité par patient, chronique ?)
PROFILE = [
    ("C10AA", 0.25, True), ("C09AA", 0.18, True), ("C09CA", 0.08, True), ("C07AB", 0.12, True),
    ("A02BC", 0.28, True), ("A10BA02", 0.08, True), ("B01AC06", 0.10, True), ("N06AB", 0.12, True),
    ("N05BA", 0.07, True), ("R03AK", 0.05, True), ("N03AX12", 0.03, True),
    ("J01CA04", 0.30, False), ("J01CR02", 0.16, False), ("J01FA", 0.08, False), ("J01MA", 0.04, False),
    ("M01AE", 0.22, False), ("N02BE01", 0.30, False),
]
KMEHR_NS = "http://www.ehealth.fgov.be/standards/kmehr/schema/v1"


def candidates(db, atc):
    rows = db.execute("""SELECT d.cnk, p.prescription_name FROM dmpp d JOIN ampp p ON p.cti_extended = d.cti_extended
                         WHERE d.delivery_environment = 'P' AND d.reimbursable = 1 AND p.commercialized = 1 AND p.atc LIKE ?
                         ORDER BY d.cnk""", (atc + "%",)).fetchall()
    return rows


def item(cnk, name, date, packs):
    return f"""<item><id S="ID-KMEHR" SV="1.0">1</id><cd S="CD-ITEM" SV="1.11">medication</cd>
<content><medicinalproduct><intendedcd S="CD-DRUG-CNK" SV="01-2016">{cnk}</intendedcd>
<intendedname>{escape(name)}</intendedname></medicinalproduct></content>
<beginmoment><date>{date.isoformat()}</date></beginmoment><quantity><decimal>{packs}</decimal></quantity></item>"""


def patient_file(number, birth, sex, prescriptions):
    transactions = "".join(f"""<transaction><id S="ID-KMEHR" SV="1.0">{i + 1}</id>
<cd S="CD-TRANSACTION" SV="1.11">pharmaceuticalprescription</cd><date>{date.isoformat()}</date><time>10:00:00</time>
<author><hcparty><cd S="CD-HCPARTY" SV="1.11">persphysician</cd><firstname>Médecin</firstname><familyname>Fictif</familyname></hcparty></author>
<iscomplete>true</iscomplete><isvalidated>true</isvalidated>{"".join(item(c, n, date, q) for c, n, q in lines)}</transaction>"""
                           for i, (date, lines) in enumerate(prescriptions))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kmehrmessage xmlns="{KMEHR_NS}"><header><standard><cd S="CD-STANDARD" SV="1.11">20161201</cd></standard>
<id S="ID-KMEHR" SV="1.0">exemple-fictif.{number}</id><date>2026-10-20</date><time>12:00:00</time></header>
<folder><id S="ID-KMEHR" SV="1.0">1</id><patient><id S="ID-PATIENT" SV="1.0">FICTIF-{number:05d}</id>
<firstname>Patient</firstname><familyname>Fictif {number}</familyname><birthdate><date>{birth.isoformat()}</date></birthdate>
<sex><cd S="CD-SEX" SV="1.0">{sex}</cd></sex></patient>{transactions}</folder></kmehrmessage>"""


def generate(db_path, out, patients=250, months=12, seed=7, end=dt.date(2026, 10, 15)):
    rng = random.Random(seed)
    db = sqlite3.connect(db_path)
    pools = {atc: candidates(db, atc) for atc, _, _ in PROFILE}
    db.close()
    start = end - dt.timedelta(days=30 * months)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for number in range(1, patients + 1):
            age = rng.choice([rng.randint(18, 44), rng.randint(45, 64), rng.randint(65, 92)])
            birth = dt.date(end.year - age, rng.randint(1, 12), rng.randint(1, 28))
            visits = {}
            for atc, probability, chronic in PROFILE:
                if not pools[atc] or rng.random() > probability * (1.5 if age >= 65 and chronic else 1):
                    continue
                cnk, name = rng.choice(pools[atc])
                if chronic:
                    day = start + dt.timedelta(days=rng.randint(0, 60))
                    while day <= end:
                        visits.setdefault(day, []).append((cnk, name, 1))
                        day += dt.timedelta(days=rng.choice([84, 90, 98]))
                else:
                    for _ in range(rng.randint(1, 2)):
                        day = start + dt.timedelta(days=rng.randint(0, 30 * months))
                        visits.setdefault(day, []).append((cnk, name, 1))
            if visits:
                z.writestr(f"patient-{number:05d}.xml",
                           patient_file(number, birth, rng.choice(["male", "female"]), sorted(visits.items())))
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=pathlib.Path, default=pathlib.Path("data/sam.sqlite"))
    p.add_argument("--out", type=pathlib.Path, default=pathlib.Path("data/exemple-fictif.zip"))
    p.add_argument("--patients", type=int, default=250)
    a = p.parse_args()
    print(f"Dossiers fictifs : {generate(a.db, a.out, a.patients)}")
