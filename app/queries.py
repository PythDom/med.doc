"""Requêtes sur la base SQLite produite par sam_v2.load (circuit officine publique uniquement)."""
import sqlite3
import unicodedata

PUBLIC = "P"  # deliveryEnvironment : officine publique
REGIMES = {"1": "BIM", "2": "ordinaire"}  # PIM 5.1.1 : 1 = préférentiel, 2 = actif


def normalize(value):
    """Minuscules sans accents, pour une recherche tolérante."""
    if value is None:
        return ""
    value = unicodedata.normalize("NFKD", value)
    return "".join(c for c in value if not unicodedata.combining(c)).lower()


def connect(path):
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    db.create_function("norm", 1, normalize, deterministic=True)
    return db


def meta(db):
    return {r["key"]: r["value"] for r in db.execute("SELECT key, value FROM meta")}


def search(db, query, limit=60):
    """Recherche par CNK (7 chiffres) ou par nom de produit / substance."""
    query = query.strip()
    if query.isdigit():
        where, args = "d.cnk = ?", [query.zfill(7)]
    else:
        terms = [f"%{t}%" for t in normalize(query).split()]
        if not terms:
            return []
        where = " AND ".join(["norm(p.prescription_name || ' ' || coalesce(vt.name, '')) LIKE ?"] * len(terms))
        args = terms
    return db.execute(f"""
        SELECT d.cnk, p.prescription_name, p.commercialized, d.price, d.reimbursable,
               s.cti_extended IS NOT NULL AS supply_problem, vt.name AS substance
        FROM dmpp d
        JOIN ampp p ON p.cti_extended = d.cti_extended
        JOIN amp a ON a.amp_code = p.amp_code
        LEFT JOIN vmp v ON v.vmp_code = a.vmp_code
        LEFT JOIN vtm vt ON vt.vtm_code = v.vtm_code
        LEFT JOIN supply_problem s ON s.cti_extended = p.cti_extended
        WHERE d.delivery_environment = '{PUBLIC}' AND {where}
        ORDER BY p.commercialized DESC, p.prescription_name
        LIMIT ?""", args + [limit]).fetchall()


def product(db, cnk):
    return db.execute(f"""
        SELECT d.cnk, d.price, d.cheap, d.cheapest, d.reimbursable, p.*, a.name AS amp_name,
               a.black_triangle, a.company, a.vmp_code, v.name AS vmp_name, v.vmp_group_code,
               g.name AS vmp_group_name, g.no_switch_reason, v.vtm_code, vt.name AS substance
        FROM dmpp d
        JOIN ampp p ON p.cti_extended = d.cti_extended
        JOIN amp a ON a.amp_code = p.amp_code
        LEFT JOIN vmp v ON v.vmp_code = a.vmp_code
        LEFT JOIN vmp_group g ON g.vmp_group_code = v.vmp_group_code
        LEFT JOIN vtm vt ON vt.vtm_code = v.vtm_code
        WHERE d.cnk = ? AND d.delivery_environment = '{PUBLIC}'""", (cnk,)).fetchone()


def supply_problem(db, cti_extended):
    return db.execute("SELECT * FROM supply_problem WHERE cti_extended = ?", (cti_extended,)).fetchone()


def reimbursement_contexts(db, cnk):
    """Contextes de remboursement d'un CNK, avec le ticket modérateur par régime."""
    rows = db.execute(f"""
        SELECT r.*,
               (SELECT fee FROM copayment k WHERE k.cnk = r.cnk AND k.delivery_environment = r.delivery_environment
                  AND k.legal_reference_path = r.legal_reference_path AND k.regime_type = '1') AS fee_bim,
               (SELECT fee FROM copayment k WHERE k.cnk = r.cnk AND k.delivery_environment = r.delivery_environment
                  AND k.legal_reference_path = r.legal_reference_path AND k.regime_type = '2') AS fee_ordinary
        FROM reimbursement r
        WHERE r.cnk = ? AND r.delivery_environment = '{PUBLIC}'
        ORDER BY r.legal_reference_path""", (cnk,)).fetchall()
    contexts = []
    for r in rows:
        chapter, paragraph = split_legal_path(r["legal_reference_path"])
        key = None
        if chapter in ("II", "III", "IV") and paragraph != "0":
            found = db.execute("SELECT key_string FROM chapter_iv_paragraph WHERE chapter = ? AND paragraph = ?",
                               (chapter, paragraph)).fetchone()
            key = found["key_string"] if found else None
        contexts.append(dict(r) | {"chapter": chapter, "paragraph": paragraph, "paragraph_key": key})
    return contexts


def split_legal_path(legal_reference_path):
    """'RD20180201-IV-1640000' -> ('IV', '1640000') ; 'RD20180201-I-0' -> ('I', '0')."""
    parts = (legal_reference_path or "").split("-")
    return (parts[1], parts[-1]) if len(parts) >= 3 else ("", "")


def patient_cost(context, regime):
    """Ticket modérateur + supplément éventuel (système de remboursement de référence)."""
    fee = context["fee_bim"] if regime == "1" else context["fee_ordinary"]
    if fee is None:
        return None
    return fee + (context["copayment_supplement"] or 0)


def _alternatives(db, join_condition, args, exclude_cti, limit):
    rows = db.execute(f"""
        SELECT DISTINCT d.cnk, p.prescription_name, p.cti_extended, d.price, d.cheap, d.cheapest, d.reimbursable
        FROM amp a
        JOIN vmp v ON v.vmp_code = a.vmp_code
        JOIN ampp p ON p.amp_code = a.amp_code
        JOIN dmpp d ON d.cti_extended = p.cti_extended AND d.delivery_environment = '{PUBLIC}'
        WHERE {join_condition} AND p.cti_extended != ?
          AND p.commercialized = 1 AND p.status = 'AUTHORIZED'
          AND NOT EXISTS (SELECT 1 FROM supply_problem s WHERE s.cti_extended = p.cti_extended)
        ORDER BY d.reimbursable DESC, d.price IS NULL, d.price
        LIMIT ?""", args + [exclude_cti, limit]).fetchall()
    return [dict(r) | {"contexts": reimbursement_contexts(db, r["cnk"])} for r in rows]


def alternatives(db, prod, limit=25):
    """Alternatives disponibles, par niveaux de proximité décroissante."""
    levels = []
    if prod["vmp_group_code"]:
        levels.append(("Même groupe (substituable : même substance, dosage et forme)",
                       _alternatives(db, "v.vmp_group_code = ?", [prod["vmp_group_code"]], prod["cti_extended"], limit)))
    if prod["vtm_code"]:
        same_vtm = _alternatives(db, "v.vtm_code = ? AND coalesce(v.vmp_group_code, '') != ?",
                                 [prod["vtm_code"], prod["vmp_group_code"] or ""], prod["cti_extended"], limit)
        levels.append(("Même substance, autre dosage ou autre forme (adaptation de la posologie)", same_vtm))
    if prod["atc"] and len(prod["atc"]) >= 5:
        same_class = _alternatives(db, "p.atc LIKE ? AND coalesce(v.vtm_code, '') != ?",
                                   [prod["atc"][:5] + "%", prod["vtm_code"] or ""], prod["cti_extended"], limit)
        levels.append((f"Autre substance de la même classe ATC ({prod['atc'][:5]}) : décision thérapeutique", same_class))
    return levels
