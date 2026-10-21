"""Chargement de l'état *actuel* d'un export SAM v2 dans une base SQLite.

Chaque entité SAM est historisée par des blocs <Data from=… to=…> ; on ne garde que
le bloc valide à la date de référence (par défaut : aujourd'hui).

Usage : python -m sam_v2.load --xml-dir data/sam/sam-12590 --db data/sam.sqlite [--date 2026-10-20]
"""
import argparse
import datetime as dt
import pathlib
import sqlite3
import xml.etree.ElementTree as ET

SCHEMA = """
CREATE TABLE amp (amp_code TEXT PRIMARY KEY, vmp_code TEXT, name TEXT, official_name TEXT,
    status TEXT, black_triangle INTEGER, medicine_type TEXT, company TEXT);
CREATE TABLE ampp (cti_extended TEXT PRIMARY KEY, amp_code TEXT, prescription_name TEXT, pack TEXT,
    atc TEXT, atc_description TEXT, delivery_modus TEXT, delivery_modus_description TEXT, status TEXT, generic_prescription_required INTEGER,
    ex_factory_price REAL, commercialized INTEGER, end_of_commercialization TEXT,
    spc_link TEXT, leaflet_link TEXT, rma_professional_link TEXT, rma_patient_link TEXT,
    dhpc_link TEXT, cbip_link TEXT);
CREATE TABLE dmpp (cnk TEXT, delivery_environment TEXT, cti_extended TEXT, price REAL,
    cheap INTEGER, cheapest INTEGER, reimbursable INTEGER, PRIMARY KEY (cnk, delivery_environment));
CREATE TABLE supply_problem (cti_extended TEXT PRIMARY KEY, start_date TEXT, expected_end TEXT,
    reason TEXT, impact TEXT, limited_availability INTEGER, reported_by TEXT, additional_information TEXT);
CREATE TABLE reimbursement (cnk TEXT, delivery_environment TEXT, legal_reference_path TEXT,
    category TEXT, criterion_code TEXT, criterion TEXT, reference_base_price REAL,
    reimbursement_base_price REAL, copayment_supplement REAL, temporary INTEGER,
    PRIMARY KEY (cnk, delivery_environment, legal_reference_path));
CREATE TABLE copayment (cnk TEXT, delivery_environment TEXT, legal_reference_path TEXT,
    regime_type TEXT, fee REAL);
CREATE TABLE vmp (vmp_code TEXT PRIMARY KEY, name TEXT, vmp_group_code TEXT, vtm_code TEXT);
CREATE TABLE vmp_ingredient (vmp_code TEXT, substance_code TEXT, substance TEXT, amount REAL, unit TEXT,
    denominator REAL, denominator_unit TEXT);
CREATE TABLE imported (imported_id TEXT PRIMARY KEY, name TEXT, country TEXT, strength TEXT, pack_size TEXT,
    cnk TEXT, form TEXT, route TEXT, notes TEXT, start_date TEXT);
CREATE TABLE imported_substance (imported_id TEXT, substance_code TEXT, substance TEXT);
CREATE TABLE vmp_group (vmp_group_code TEXT PRIMARY KEY, name TEXT, no_switch_reason TEXT,
    no_generic_prescription_reason TEXT);
CREATE TABLE vtm (vtm_code TEXT PRIMARY KEY, name TEXT);
CREATE TABLE chapter_iv_paragraph (chapter TEXT, paragraph TEXT, key_string TEXT,
    agreement_type TEXT, publication_date TEXT, PRIMARY KEY (chapter, paragraph));
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE INDEX idx_dmpp_cti ON dmpp(cti_extended);
CREATE INDEX idx_ampp_amp ON ampp(amp_code);
CREATE INDEX idx_amp_vmp ON amp(vmp_code);
CREATE INDEX idx_vmp_group ON vmp(vmp_group_code);
CREATE INDEX idx_copayment_cnk ON copayment(cnk);
"""


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child(el, name):
    if el is None:
        return None
    for c in el:
        if local(c.tag) == name:
            return c
    return None


def children(el, name):
    return [c for c in el if local(c.tag) == name] if el is not None else []


def text(el, *path, lang="Fr"):
    """Texte d'un descendant ; si l'élément est multilingue, renvoie la langue demandée."""
    for name in path:
        el = child(el, name)
        if el is None:
            return None
    translated = child(el, lang)
    if translated is not None:
        el = translated
    return el.text.strip() if el.text and el.text.strip() else None


def attr(el, *path, name="code"):
    for p in path:
        el = child(el, p)
        if el is None:
            return None
    return el.get(name)


def flag(value):
    return None if value is None else int(value == "true")


def num(value):
    return float(value) if value not in (None, "") else None


def current(el, today: str):
    """Bloc <Data> valide à la date de référence, ou None."""
    for d in children(el, "Data"):
        if d.get("from", "0000") <= today and (d.get("to") is None or d.get("to") >= today):
            return d
    return None


def iter_entities(path: pathlib.Path, names: set):
    """Parcourt les entités de premier niveau d'un fichier sans tout garder en mémoire."""
    context = ET.iterparse(path, events=("start", "end"))
    _, root = next(context)
    depth = 1
    for event, el in context:
        if event == "start":
            depth += 1
            continue
        depth -= 1
        if depth == 1:
            if local(el.tag) in names:
                yield local(el.tag), el
            root.clear()


def find(xml_dir: pathlib.Path, prefix: str) -> pathlib.Path:
    return next(xml_dir.glob(f"{prefix}-*.xml"))


def load_amp(db, xml_dir, today):
    for _, amp in iter_entities(find(xml_dir, "AMP"), {"Amp"}):
        d = current(amp, today)
        if d is None:
            continue
        code = amp.get("code")
        company = child(d, "Company")
        db.execute("INSERT INTO amp VALUES (?,?,?,?,?,?,?,?)", (
            code, amp.get("vmpCode"), text(d, "Name"), text(d, "OfficialName"), text(d, "Status"),
            flag(text(d, "BlackTriangle")), text(d, "MedicineType"),
            text(current(company, today), "Denomination") if company is not None else None))
        for ampp in children(amp, "Ampp"):
            ad = current(ampp, today)
            if ad is None:
                continue
            cti = ampp.get("ctiExtended")
            commercialization = current(child(ampp, "Commercialization"), today)
            db.execute("INSERT INTO ampp VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                cti, code, text(ad, "PrescriptionNameFamhp"), text(ad, "PackDisplayValue"),
                attr(ad, "Atc"), text(ad, "Atc", "Description"), attr(ad, "DeliveryModus"),
                text(ad, "DeliveryModus", "Description"),
                text(ad, "Status"), flag(text(ad, "GenericPrescriptionRequired")),
                num(text(ad, "ExFactoryPrice")), int(commercialization is not None),
                text(ad, "EndOfCommercialization"),
                text(ad, "SpcLink"), text(ad, "LeafletLink"), text(ad, "RmaProfessionalLink"),
                text(ad, "RmaPatientLink"), text(ad, "DHPCLink"), text(ad, "CrmLink")))
            sp = current(child(ampp, "SupplyProblem"), today)
            if sp is not None:
                db.execute("INSERT INTO supply_problem VALUES (?,?,?,?,?,?,?,?)", (
                    cti, sp.get("from"), text(sp, "ExpectedEndOn"), text(sp, "Reason"),
                    text(sp, "Impact"), flag(text(sp, "LimitedAvailability")),
                    text(sp, "ReportedBy"), text(sp, "AdditionalInformation")))
            for dmpp in children(ampp, "Dmpp"):
                dd = current(dmpp, today)
                if dd is None:
                    continue
                db.execute("INSERT OR REPLACE INTO dmpp VALUES (?,?,?,?,?,?,?)", (
                    dmpp.get("code"), dmpp.get("deliveryEnvironment"), cti, num(text(dd, "Price")),
                    flag(text(dd, "Cheap")), flag(text(dd, "Cheapest")), flag(text(dd, "Reimbursable"))))


def load_rmb(db, xml_dir, today):
    for _, ctx in iter_entities(find(xml_dir, "RMB"), {"ReimbursementContext"}):
        d = current(ctx, today)
        if d is None:
            continue
        key = (ctx.get("code"), ctx.get("deliveryEnvironment"), ctx.get("legalReferencePath"))
        db.execute("INSERT OR REPLACE INTO reimbursement VALUES (?,?,?,?,?,?,?,?,?,?)", key + (
            attr(d, "ReimbursementCriterion", name="category"), attr(d, "ReimbursementCriterion"),
            text(d, "ReimbursementCriterion", "Description"), num(text(d, "ReferenceBasePrice")),
            num(text(d, "ReimbursementBasePrice")), num(text(d, "CopaymentSupplement")),
            flag(text(d, "Temporary"))))
        for cp in children(ctx, "Copayment"):
            cd = current(cp, today)
            if cd is not None:
                db.execute("INSERT INTO copayment VALUES (?,?,?,?,?)",
                           key + (cp.get("regimeType"), num(text(cd, "FeeAmount"))))


def load_vmp(db, xml_dir, today):
    for name, el in iter_entities(find(xml_dir, "VMP"), {"Vmp", "VmpGroup", "Vtm"}):
        d = current(el, today)
        if d is None:
            continue
        if name == "Vmp":
            db.execute("INSERT INTO vmp VALUES (?,?,?,?)", (
                el.get("code"), text(d, "Name"), attr(d, "VmpGroup"), attr(d, "Vtm")))
            for component in children(el, "VmpComponent"):
                for ingredient in children(component, "VirtualIngredient"):
                    idata = current(ingredient, today)
                    strength = child(idata, "Strength")
                    if idata is None or text(idata, "Type") != "ACTIVE_SUBSTANCE" or strength is None:
                        continue
                    numerator, denominator = child(strength, "NumeratorRange"), child(strength, "Denominator")
                    low, high = num(text(numerator, "Min")), num(text(numerator, "Max"))
                    db.execute("INSERT INTO vmp_ingredient VALUES (?,?,?,?,?,?,?)", (
                        el.get("code"), attr(idata, "Substance"), text(idata, "Substance", "Name"),
                        low if low == high else None,
                        numerator.get("unit"), num(denominator.text if denominator is not None else None),
                        denominator.get("unit") if denominator is not None else None))
        elif name == "VmpGroup":
            db.execute("INSERT INTO vmp_group VALUES (?,?,?,?)", (
                el.get("code"), text(d, "Name"), attr(d, "NoSwitchReason"),
                attr(d, "NoGenericPrescriptionReason")))
        else:
            db.execute("INSERT INTO vtm VALUES (?,?)", (el.get("code"), text(d, "Name")))


def load_imported(db, xml_dir, today):
    """Médicaments importés autorisés temporairement (rupture), reliés aux produits belges par leurs substances."""
    for _, el in iter_entities(find(xml_dir, "IMPP"), {"ImportedMedicinalProductPackage"}):
        d = current(el, today)
        if d is None:
            continue
        key = el.get("Id")
        db.execute("INSERT OR REPLACE INTO imported VALUES (?,?,?,?,?,?,?,?,?,?)", (
            key, text(d, "Name"), text(d, "Country"), text(d, "Strength"), text(d, "PackSize"), text(d, "CNK"),
            text(d, "PharmaceuticalFormCode", "Name"), text(d, "RouteOfAdministrationCode", "Name"),
            text(d, "Notes"), d.get("from")))
        for substance in children(d, "ActiveSubstance"):
            db.execute("INSERT INTO imported_substance VALUES (?,?,?)",
                       (key, substance.get("code"), text(substance, "Name")))


def load_chapter_iv(db, xml_dir, today):
    for _, p in iter_entities(find(xml_dir, "CHAPTERIV"), {"Paragraph"}):
        d = current(p, today)
        if d is not None:
            db.execute("INSERT OR REPLACE INTO chapter_iv_paragraph VALUES (?,?,?,?,?)", (
                p.get("ChapterName"), p.get("ParagraphName"), text(d, "KeyStringFr"),
                text(d, "AgreementType"), text(d, "PublicationDate")))


def load(xml_dir: pathlib.Path, db_path: pathlib.Path, today: str):
    db_path.unlink(missing_ok=True)
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    for step in (load_vmp, load_rmb, load_chapter_iv, load_imported, load_amp):
        print(f"{step.__name__}…", flush=True)
        step(db, xml_dir, today)
        db.commit()
    db.executemany("INSERT INTO meta VALUES (?,?)",
                   [("export", xml_dir.name), ("reference_date", today)])
    db.commit()
    db.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xml-dir", type=pathlib.Path, required=True)
    p.add_argument("--db", type=pathlib.Path, default=pathlib.Path("data/sam.sqlite"))
    p.add_argument("--date", default=dt.date.today().isoformat())
    a = p.parse_args()
    load(a.xml_dir, a.db, a.date)
