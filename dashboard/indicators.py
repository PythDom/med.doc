"""Indicateurs de prescription calculés à partir des prescriptions lues et de la base SAM locale.

Ce sont des estimations destinées à l'auto-évaluation, pas les chiffres officiels de l'INAMI :
- l'INAMI calcule sur les médicaments remboursés et délivrés (Farmanet), ici on compte ce qui est prescrit ;
- les indicateurs « bon marché » sont ceux de la base SAM actuelle, pas ceux en vigueur à la date de prescription ;
- les volumes sont comptés en conditionnements (boîtes), pas en DDD.
"""
import collections
import datetime as dt
import sqlite3

from app.export_static import parse_pack
from app.queries import split_legal_path

# Seuils et classes repris des retours de l'INAMI aux prescripteurs (voir README).
CHEAP_THRESHOLD_GP = 0.60      # pourcentage minimum de prescriptions bon marché, médecine générale
PPI_THRESHOLD = 0.25           # part maximale de patients sous IPP (indicateur CNPQ)
CLASSES = [
    ("Antibiotiques", ("J01",)),
    ("Inhibiteurs de la pompe à protons (IPP)", ("A02BC",)),
    ("Anti-inflammatoires non stéroïdiens (AINS)", ("M01A",)),
    ("Antidépresseurs", ("N06A",)),
    ("Benzodiazépines et apparentés", ("N05BA", "N05CD", "N05CF")),
]
ANTIBIOTICS = [
    ("Amoxicilline", ("J01CA04",)),
    ("Amoxicilline + acide clavulanique", ("J01CR02",)),
    ("Macrolides", ("J01FA",)),
    ("Quinolones", ("J01M",)),
    ("Autres antibiotiques", ("J01",)),
]


def products(db):
    """Informations utiles par CNK (officine publique) : classe, statut, prix et coût patient."""
    info = {}
    for r in db.execute("""
            SELECT d.cnk, d.price, d.cheap, d.cheapest, d.reimbursable, p.prescription_name, p.atc, p.pack,
                   p.commercialized, p.cti_extended, s.expected_end, v.vmp_group_code, g.name AS group_name,
                   vt.name AS substance
            FROM dmpp d JOIN ampp p ON p.cti_extended = d.cti_extended JOIN amp a ON a.amp_code = p.amp_code
            LEFT JOIN supply_problem s ON s.cti_extended = p.cti_extended
            LEFT JOIN vmp v ON v.vmp_code = a.vmp_code LEFT JOIN vmp_group g ON g.vmp_group_code = v.vmp_group_code
            LEFT JOIN vtm vt ON vt.vtm_code = v.vtm_code
            WHERE d.delivery_environment = 'P'"""):
        info[r["cnk"]] = dict(r)
        info[r["cnk"]]["qty"] = parse_pack(r["pack"])[0]
    shortages = {r[0] for r in db.execute("SELECT cti_extended FROM supply_problem")}
    for p in info.values():
        p["shortage"] = p["cti_extended"] in shortages
        p["cost"] = {"1": None, "2": None}
    # Coût patient : contexte du chapitre I (sans accord du médecin-conseil), sinon le premier ; prix public si non remboursé.
    contexts = collections.defaultdict(list)
    for r in db.execute("""SELECT r.cnk, r.legal_reference_path, r.copayment_supplement, c.regime_type, c.fee
                           FROM reimbursement r JOIN copayment c ON c.cnk = r.cnk AND c.delivery_environment = r.delivery_environment
                            AND c.legal_reference_path = r.legal_reference_path
                           WHERE r.delivery_environment = 'P' ORDER BY r.legal_reference_path"""):
        contexts[r["cnk"]].append(r)
    for cnk, p in info.items():
        rows = contexts.get(cnk)
        if not rows:
            price = p["price"] or None
            p["cost"] = {"1": None if p["reimbursable"] else price, "2": None if p["reimbursable"] else price}
            continue
        paths = [r["legal_reference_path"] for r in rows]
        chosen = next((x for x in paths if split_legal_path(x)[0] == "I"), paths[0])
        for r in rows:
            if r["legal_reference_path"] == chosen:
                p["cost"][r["regime_type"]] = r["fee"] + (r["copayment_supplement"] or 0)
    return info


def starts_with(atc, prefixes):
    return bool(atc) and any(atc.startswith(x) for x in prefixes)


def month(d):
    return d.strftime("%Y-%m")


def compute(prescriptions, db_path, start=None, end=None, regime="2", recent_days=180):
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    info = products(db)
    meta = {r["key"]: r["value"] for r in db.execute("SELECT key, value FROM meta")}
    db.close()

    rows = [p for p in prescriptions if (start is None or p.date >= start) and (end is None or p.date <= end)]
    if not rows:
        raise ValueError("Aucune prescription dans la période choisie.")
    first, last = min(p.date for p in rows), max(p.date for p in rows)
    patients = {p.patient for p in rows}

    # Rattachement à la base SAM.
    known = [p for p in rows if p.cnk in info]
    dci = [p for p in rows if p.cnk not in info and p.vmp_group]
    unknown = [p for p in rows if p.cnk not in info and not p.vmp_group]

    # Prescriptions bon marché : boîtes remboursables (selon SAM) + prescriptions en DCI.
    cheap_by_month = collections.defaultdict(lambda: [0.0, 0.0])
    for p in known:
        product = info[p.cnk]
        if product["reimbursable"] and product["cheap"] is not None:
            cheap_by_month[month(p.date)][1] += p.packs
            cheap_by_month[month(p.date)][0] += p.packs if product["cheap"] else 0
    for p in dci:
        cheap_by_month[month(p.date)][0] += p.packs
        cheap_by_month[month(p.date)][1] += p.packs
    cheap_total = [sum(v[0] for v in cheap_by_month.values()), sum(v[1] for v in cheap_by_month.values())]

    volume_by_month = collections.Counter()
    for p in rows:
        volume_by_month[month(p.date)] += p.packs

    # Classes surveillées : part des patients ayant reçu au moins une prescription.
    classes = []
    for label, prefixes in CLASSES:
        selected = [p for p in known if starts_with(info[p.cnk]["atc"], prefixes)]
        classes.append({"label": label, "patients": len({p.patient for p in selected}),
                        "share": len({p.patient for p in selected}) / len(patients),
                        "packs": sum(p.packs for p in selected)})

    antibiotics = [p for p in known if starts_with(info[p.cnk]["atc"], ("J01",))]
    antibiotic_mix, counted = [], set()
    total_ab = sum(p.packs for p in antibiotics)
    for label, prefixes in ANTIBIOTICS:
        selected = [p for p in antibiotics if starts_with(info[p.cnk]["atc"], prefixes) and id(p) not in counted]
        counted.update(id(p) for p in selected)
        packs = sum(p.packs for p in selected)
        antibiotic_mix.append({"label": label, "packs": packs, "share": packs / total_ab if total_ab else None})

    # IPP au long cours : prescriptions étalées sur au moins 90 jours chez un même patient.
    ppi_dates = collections.defaultdict(list)
    for p in known:
        if starts_with(info[p.cnk]["atc"], ("A02BC",)):
            ppi_dates[p.patient].append(p.date)
    long_ppi = sum(1 for dates in ppi_dates.values() if (max(dates) - min(dates)).days >= 90)

    # Substances les plus prescrites.
    by_substance = collections.Counter()
    for p in known:
        by_substance[info[p.cnk]["substance"] or info[p.cnk]["prescription_name"]] += p.packs
    for p in dci:
        by_substance[p.name or f"Groupe VMP {p.vmp_group}"] += p.packs

    # À revoir : produits prescrits récemment, aujourd'hui en rupture ou retirés du marché.
    recent_from = last - dt.timedelta(days=recent_days)
    recent = collections.defaultdict(set)
    for p in known:
        if p.date >= recent_from:
            recent[p.cnk].add(p.patient)
    shortages = sorted(({"cnk": c, "name": info[c]["prescription_name"], "patients": len(ps),
                         "expected_end": info[c]["expected_end"]}
                        for c, ps in recent.items() if info[c]["shortage"]), key=lambda x: -x["patients"])
    withdrawn = sorted(({"cnk": c, "name": info[c]["prescription_name"], "patients": len(ps)}
                        for c, ps in recent.items() if not info[c]["commercialized"] and not info[c]["shortage"]),
                       key=lambda x: -x["patients"])

    # Économies possibles pour les patients : même groupe substituable et même contenu de boîte,
    # conditionnement disponible au coût patient le plus bas.
    best = {}
    for c, x in info.items():
        cost = x["cost"][regime]
        if x["vmp_group_code"] and x["qty"] and x["commercialized"] and not x["shortage"] and cost is not None:
            key = (x["vmp_group_code"], x["qty"])
            if cost < best.get(key, (float("inf"), None))[0]:
                best[key] = (cost, c)
    savings = collections.defaultdict(lambda: {"packs": 0.0, "amount": 0.0})
    for p in known:
        x = info[p.cnk]
        cost, cheaper = x["cost"][regime], best.get((x["vmp_group_code"], x["qty"]))
        if cost is None or not cheaper or cheaper[1] == p.cnk or cost - cheaper[0] < 0.005:
            continue
        savings[(p.cnk, cheaper[1])]["packs"] += p.packs
        savings[(p.cnk, cheaper[1])]["amount"] += (cost - cheaper[0]) * p.packs
    savings = sorted(({"cnk": a, "name": info[a]["prescription_name"], "alternative_cnk": b,
                       "alternative": info[b]["prescription_name"], "unit_gap": info[a]["cost"][regime] - info[b]["cost"][regime],
                       **v} for (a, b), v in savings.items()), key=lambda x: -x["amount"])

    months = sorted(set(volume_by_month) | set(cheap_by_month))
    return {
        "period": {"first": first.isoformat(), "last": last.isoformat()},
        "sources": {"sam": meta.get("export"), "sam_date": meta.get("reference_date"), "cbip": meta.get("cbip_version")},
        "regime": regime,
        "totals": {"prescriptions": len(rows), "packs": sum(p.packs for p in rows), "patients": len(patients),
                   "known": len(known), "dci": len(dci), "unknown": len(unknown)},
        "cheap": {"share": cheap_total[0] / cheap_total[1] if cheap_total[1] else None,
                  "threshold": CHEAP_THRESHOLD_GP, "packs": cheap_total[1]},
        "months": [{"month": m, "packs": volume_by_month.get(m, 0),
                    "cheap_share": (cheap_by_month[m][0] / cheap_by_month[m][1]) if cheap_by_month[m][1] else None}
                   for m in months],
        "classes": classes,
        "antibiotics": {"packs": total_ab, "mix": antibiotic_mix},
        "ppi": {"patients": len(ppi_dates), "share": len(ppi_dates) / len(patients), "threshold": PPI_THRESHOLD,
                "long_term": long_ppi},
        "top_substances": [{"name": n, "packs": v} for n, v in by_substance.most_common(15)],
        "shortages": shortages, "withdrawn": withdrawn,
        "savings": savings[:15], "savings_total": sum(s["amount"] for s in savings),
        "unknown_names": collections.Counter(p.name or "(sans nom)" for p in unknown).most_common(10),
    }
