"""Requêtes sur la base SQLite produite par sam_v2.load (circuit officine publique uniquement).

La recherche, les alternatives et le coût patient sont calculés dans la page (app/static_template.html) ;
ce module fournit les données qu'elle intègre.
"""
import sqlite3

PUBLIC = "P"  # deliveryEnvironment : officine publique
REGIMES = {"1": "BIM", "2": "ordinaire"}  # PIM 5.1.1 : 1 = préférentiel, 2 = actif


def connect(path):
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def meta(db):
    return {r["key"]: r["value"] for r in db.execute("SELECT key, value FROM meta")}


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
        contexts.append({**dict(r), "chapter": chapter, "paragraph": paragraph, "paragraph_key": key})
    return contexts


def split_legal_path(legal_reference_path):
    """'RD20180201-IV-1640000' -> ('IV', '1640000') ; 'RD20180201-I-0' -> ('I', '0')."""
    parts = (legal_reference_path or "").split("-")
    return (parts[1], parts[-1]) if len(parts) >= 3 else ("", "")
