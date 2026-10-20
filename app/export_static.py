"""Génère une version autonome du prototype (une seule page HTML, données intégrées).

Usage : python -m app.export_static --db data/sam.sqlite --out data/medicaments.html
La page fonctionne sans serveur : recherche, alternatives et coût patient sont calculés dans le navigateur.
"""
import argparse
import json
import pathlib
import re
import sqlite3

from app import queries as q

TEMPLATE = pathlib.Path(__file__).with_name("static_template.html")


MASS_TO_MG = {"mg": 1, "g": 1000, "ug": 0.001, "µg": 0.001}
NUMBER = r"(\d+(?:[.,]\d+)?)"


def to_float(value):
    return float(value.replace(",", "."))


def parse_pack(pack):
    """Contenu d'une boîte : '90' -> (90, ''), '200 (2 x 100)' -> (200, ''), '30 x 1 ml' -> (30, 'ml'), '1 l' -> (1000, 'ml')."""
    if not pack:
        return None, None
    m = re.match(NUMBER + r"\s*x\s*" + NUMBER + r"\s*(ml|g|l)?\b", pack, re.I)
    if m:
        qty, unit = to_float(m.group(1)) * to_float(m.group(2)), (m.group(3) or "").lower()
    else:
        m = re.match(NUMBER + r"\s*(ml|g|l)?\b", pack, re.I)
        if not m:
            return None, None
        qty, unit = to_float(m.group(1)), (m.group(2) or "").lower()
    if unit == "l":
        qty, unit = qty * 1000, "ml"
    return qty, unit


def mono_strengths(db):
    """Dosage des VMP à une seule substance active : {vmp_code: (quantité, unité, dénominateur, unité du dénominateur)}."""
    rows = db.execute("""SELECT vmp_code, amount, unit, denominator, denominator_unit FROM vmp_ingredient
                         WHERE vmp_code IN (SELECT vmp_code FROM vmp_ingredient GROUP BY vmp_code HAVING count(*) = 1)""")
    return {r["vmp_code"]: (r["amount"], r["unit"], r["denominator"], r["denominator_unit"])
            for r in rows if r["amount"] is not None and r["denominator"]}


def pack_and_substance(pack, strength):
    """[quantité de la boîte, unité, quantité totale de substance active, unité] pour comparer les prix.

    La substance est exprimée en mg quand c'est une masse ; sinon dans son unité d'origine (UI…).
    """
    qty, unit = parse_pack(pack)
    total, total_unit = None, None
    if qty is not None and strength:
        amount, amount_unit, denominator, denominator_unit = strength
        matches = {"1": "", "mL": "ml", "g": "g"}.get(denominator_unit)
        if matches is not None and matches == unit:
            factor = MASS_TO_MG.get(amount_unit)
            total = qty * amount / denominator * (factor or 1)
            total_unit = "mg" if factor else amount_unit
    return [qty, unit, round(total, 4) if total is not None else None, total_unit]


class Table:
    """Table de chaînes dédupliquées : chaque texte répété n'est stocké qu'une fois."""

    def __init__(self):
        self.items, self.index = [], {}

    def __call__(self, value):
        if value is None:
            return -1
        if value not in self.index:
            self.index[value] = len(self.items)
            self.items.append(value)
        return self.index[value]


def split_link(url, prefixes):
    """Découpe un lien en (préfixe dédupliqué, suffixe) pour réduire la taille."""
    if not url:
        return None
    cut = url.rfind("/") + 1
    if "=" in url[cut:]:
        cut = url.rfind("=") + 1
    return [prefixes(url[:cut]), url[cut:]]


def build(db_path):
    db = q.connect(db_path)
    text, prefixes = Table(), Table()
    strengths = mono_strengths(db)
    products = []
    for r in db.execute(f"""
            SELECT d.cnk, d.price, d.cheap, d.cheapest, d.reimbursable, p.*, a.black_triangle, a.company,
                   a.vmp_code, v.vmp_group_code, g.name AS group_name, v.vtm_code, vt.name AS substance
            FROM dmpp d JOIN ampp p ON p.cti_extended = d.cti_extended JOIN amp a ON a.amp_code = p.amp_code
            LEFT JOIN vmp v ON v.vmp_code = a.vmp_code LEFT JOIN vmp_group g ON g.vmp_group_code = v.vmp_group_code
            LEFT JOIN vtm vt ON vt.vtm_code = v.vtm_code
            WHERE d.delivery_environment = '{q.PUBLIC}' ORDER BY p.prescription_name"""):
        products.append([
            r["cnk"], r["prescription_name"], r["cti_extended"], r["price"],
            (r["cheap"] or 0) | (r["cheapest"] or 0) << 1 | (r["reimbursable"] or 0) << 2
            | (r["commercialized"] or 0) << 3 | (r["black_triangle"] or 0) << 4
            | (r["generic_prescription_required"] or 0) << 5 | (r["status"] == "AUTHORIZED") << 6,
            r["atc"], text(r["atc_description"]), text((r["delivery_modus_description"] or "").split(" - ")[0] or None),
            text(r["company"]), r["vmp_group_code"], text(r["group_name"]), r["vtm_code"], text(r["substance"]),
            text(r["end_of_commercialization"]),
            [split_link(r[k], prefixes) for k in ("cbip_link", "spc_link", "leaflet_link",
                                                    "rma_professional_link", "rma_patient_link", "dhpc_link")],
        ] + pack_and_substance(r["pack"], strengths.get(r["vmp_code"])))
    supply = {r["cti_extended"]: [r["start_date"], r["expected_end"], text(r["reason"]), text(r["impact"]),
                                  r["limited_availability"], r["reported_by"], text(r["additional_information"])]
              for r in db.execute("SELECT * FROM supply_problem")}
    contexts = {}
    cnks = [p[0] for p in products]
    for cnk in cnks:
        rows = q.reimbursement_contexts(db, cnk)
        if rows:
            contexts[cnk] = [[c["chapter"], c["paragraph"], text(c["paragraph_key"]), c["category"],
                              text(c["criterion"]), c["fee_bim"], c["fee_ordinary"], c["copayment_supplement"]]
                             for c in rows]
    data = {"meta": q.meta(db), "text": text.items, "prefixes": prefixes.items,
            "products": products, "supply": supply, "contexts": contexts}
    db.close()
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=pathlib.Path, default=pathlib.Path("data/sam.sqlite"))
    p.add_argument("--out", type=pathlib.Path, default=pathlib.Path("data/medicaments.html"))
    p.add_argument("--fragment", action="store_true", help="sans squelette HTML (publication sur claude.ai)")
    a = p.parse_args()
    a.out.write_text(render(a.db, standalone=not a.fragment), encoding="utf-8")
    print(f"{a.out} ({a.out.stat().st_size / 1e6:.1f} Mo)")


# Squelette minimal pour ouvrir la page hors de claude.ai (navigateur ou serveur local).
SKELETON = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>
</head><body>
{content}
</body></html>
"""


def render(db_path, standalone=True):
    """Page complète avec les données intégrées ; `standalone=False` donne le fragment publié sur claude.ai."""
    payload = json.dumps(build(db_path), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    content = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)
    return SKELETON.replace("{content}", content) if standalone else content


if __name__ == "__main__":
    main()
