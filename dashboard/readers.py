"""Lecture des prescriptions exportées du logiciel médical (Medispring ou autre), sur la machine du médecin.

Formats acceptés :
- KMEHR (XML) : dossiers patients PMF/SMF, prescriptions, schémas de médication ; fichiers .xml ou archives .zip ;
- tableaux CSV ou Excel (.xlsx), par exemple un export du module de reporting, avec détection des colonnes.

Les identifiants des patients (NISS, numéro de dossier) sont remplacés dès la lecture par un numéro aléatoire
propre à cette lecture : aucune identité n'est conservée ni écrite.
"""
import csv
import datetime as dt
import hashlib
import io
import pathlib
import re
import secrets
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from typing import NamedTuple, Optional


class Prescription(NamedTuple):
    patient: int                  # numéro pseudonyme, propre à une lecture
    age: Optional[int]            # âge à la date de prescription
    sex: Optional[str]            # 'F', 'M' ou None
    date: dt.date
    cnk: Optional[str]            # conditionnement prescrit (7 chiffres)
    vmp_group: Optional[str]      # prescription en DCI (groupe VMP), quand le code est présent
    name: str
    packs: float


class Pseudonymizer:
    """Remplace chaque identifiant par un numéro ; le sel aléatoire n'est jamais enregistré."""

    def __init__(self):
        self.salt, self.numbers = secrets.token_bytes(16), {}

    def __call__(self, identifier):
        key = hashlib.sha256(self.salt + str(identifier).encode("utf-8")).hexdigest()
        return self.numbers.setdefault(key, len(self.numbers) + 1)


def age_at(birth, when):
    if birth is None:
        return None
    return when.year - birth.year - ((when.month, when.day) < (birth.month, birth.day))


def parse_date(value):
    """Dates courantes des exports : 2026-03-14, 14/03/2026, 14-03-2026, 14.03.2026, nombre de jours Excel."""
    if value is None:
        return None
    if isinstance(value, (dt.date, dt.datetime)):
        return value.date() if isinstance(value, dt.datetime) else value
    text = str(value).strip()
    if not text:
        return None
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if m:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", text)
    if m:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    if re.match(r"^\d+(\.\d+)?$", text) and 20000 < float(text) < 80000:  # numéro de série Excel
        return dt.date(1899, 12, 30) + dt.timedelta(days=int(float(text)))
    return None


def parse_sex(value):
    v = normalize(value)
    if v in ("f", "female", "femme", "vrouw", "v", "2"):
        return "F"
    if v in ("m", "male", "homme", "man", "h", "1"):
        return "M"
    return None


def parse_number(value, default=1.0):
    try:
        return float(str(value).replace(",", ".")) if str(value).strip() else default
    except ValueError:
        return default


def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(c for c in value if not unicodedata.combining(c)).strip().lower()


# ---------------------------------------------------------------- KMEHR

def local(tag):
    return tag.rsplit("}", 1)[-1]


def find(el, *names):
    for name in names:
        if el is None:
            return None
        el = next((c for c in el if local(c.tag) == name), None)
    return el


def find_all(el, name):
    return [c for c in el.iter() if local(c.tag) == name]


def codes(el):
    """Codes {S: valeur} des éléments <cd> et <intendedcd> d'un sous-arbre."""
    found = {}
    for c in el.iter():
        if local(c.tag) in ("cd", "intendedcd") and c.text:
            found.setdefault(c.get("S"), c.text.strip())
    return found


def transaction_type(transaction):
    """Valeur du <cd S="CD-TRANSACTION"> propre à la transaction (pas celui de ses éléments)."""
    for c in transaction:
        if local(c.tag) == "cd" and c.get("S") == "CD-TRANSACTION":
            return (c.text or "").strip()
    return None


def kmehr_date(el):
    d = find(el, "date")
    return parse_date(d.text) if d is not None and d.text else None


def read_kmehr(source, pseudonymize, prescriptions_only=True):
    """Prescriptions d'un message KMEHR (un ou plusieurs dossiers patients).

    Par défaut, seules les transactions « pharmaceuticalprescription » sont comptées. Si le fichier n'en
    contient aucune (certains exports ne gardent que l'historique de médication), les éléments « medication »
    de toutes les transactions sont repris.
    """
    root = ET.parse(source).getroot()
    rows = []
    for folder in find_all(root, "folder"):
        patient = find(folder, "patient")
        identifier = None
        if patient is not None:
            ids = [i.text for i in patient if local(i.tag) == "id" and i.text]
            names = [(c.text or "") for c in patient.iter() if local(c.tag) in ("firstname", "familyname")]
            identifier = ids[0] if ids else " ".join(names) or None
        birth_el, sex_el = find(patient, "birthdate"), find(patient, "sex")
        birth = kmehr_date(birth_el) if birth_el is not None else None
        sex = parse_sex(codes(sex_el).get("CD-SEX")) if sex_el is not None else None
        number = pseudonymize(identifier or f"{source}:{id(folder)}")
        transactions = [t for t in folder if local(t.tag) == "transaction"]
        wanted = [t for t in transactions if transaction_type(t) == "pharmaceuticalprescription"]
        if not prescriptions_only or not wanted:
            wanted = transactions
        for transaction in wanted:
            when = kmehr_date(transaction)
            for item in find_all(transaction, "item"):
                if not any(local(c.tag) == "cd" and c.get("S") == "CD-ITEM" and (c.text or "").strip() == "medication"
                           for c in item):
                    continue
                content = codes(item)
                cnk = content.get("CD-DRUG-CNK")
                group = content.get("CD-VMPGROUP")
                names = [(c.text or "").strip() for c in item.iter() if local(c.tag) == "intendedname"]
                begin_el = find(item, "beginmoment")
                begin = kmehr_date(begin_el) if begin_el is not None else None
                date = begin or when
                quantity = find(item, "quantity", "decimal")
                if date is None or not (cnk or group or names):
                    continue
                rows.append(Prescription(number, age_at(birth, date), sex, date, cnk.zfill(7) if cnk else None,
                                         group, names[0] if names else "", parse_number(
                                             quantity.text if quantity is not None else "", 1.0)))
    return rows


# ---------------------------------------------------------------- tableaux (CSV, Excel)

COLUMNS = {
    "cnk": ("cnk", "code cnk", "cnk code"),
    "date": ("date", "datum", "date de prescription", "voorschriftdatum", "date prescription"),
    "patient": ("patient", "id patient", "patient id", "dossier", "numero de dossier", "niss", "inss", "rijksregister"),
    "birth": ("date de naissance", "naissance", "geboortedatum", "birth", "birthdate"),
    "age": ("age", "leeftijd"),
    "sex": ("sexe", "geslacht", "sex", "genre"),
    "packs": ("quantite", "nombre", "aantal", "qty", "quantity", "boites", "conditionnements"),
    "name": ("medicament", "produit", "nom", "geneesmiddel", "product", "denomination", "libelle"),
    "vmp_group": ("groupe vmp", "vmp group", "vmpgroup", "code dci"),
}


def detect_columns(headers, overrides=None):
    """Associe chaque champ à une colonne d'après son en-tête (correspondance exacte, puis partielle)."""
    normalized = [normalize(h) for h in headers]
    mapping = {}
    for field, keys in COLUMNS.items():
        if overrides and overrides.get(field):
            wanted = normalize(overrides[field])
            mapping[field] = normalized.index(wanted) if wanted in normalized else None
            continue
        exact = [i for i, h in enumerate(normalized) if h in keys]
        partial = [i for i, h in enumerate(normalized) if any(k in h for k in keys)]
        mapping[field] = (exact or partial or [None])[0]
    if mapping["date"] == mapping["birth"] and mapping["birth"] is not None:
        mapping["date"] = next((i for i, h in enumerate(normalized) if "date" in h and i != mapping["birth"]), None)
    return mapping


def read_rows(rows, pseudonymize, overrides=None):
    rows = [r for r in rows if any(str(c).strip() for c in r)]
    if not rows:
        return [], {}
    headers, body = rows[0], rows[1:]
    columns = detect_columns(headers, overrides)
    if columns["date"] is None or (columns["cnk"] is None and columns["name"] is None):
        missing = [f for f in ("date", "cnk") if columns[f] is None]
        raise ValueError(f"Colonnes introuvables : {', '.join(missing)}. En-têtes lus : {headers}. "
                         "Indiquez-les avec --colonne champ=« en-tête ».")
    get = lambda row, field: row[columns[field]] if columns[field] is not None and columns[field] < len(row) else None
    result = []
    for row in body:
        date = parse_date(get(row, "date"))
        if date is None:
            continue
        cnk = re.sub(r"\D", "", str(get(row, "cnk") or ""))
        birth = parse_date(get(row, "birth"))
        age = age_at(birth, date) if birth else (int(parse_number(get(row, "age"), -1)) if get(row, "age") else None)
        patient = get(row, "patient")
        result.append(Prescription(
            pseudonymize(patient) if patient not in (None, "") else 0, age if age is None or age >= 0 else None,
            parse_sex(get(row, "sex")), date, cnk.zfill(7) if cnk else None,
            str(get(row, "vmp_group") or "").strip() or None, str(get(row, "name") or "").strip(),
            parse_number(get(row, "packs"), 1.0)))
    return result, {f: (headers[i] if i is not None else None) for f, i in columns.items()}


def read_csv(data):
    text = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    dialect = csv.Sniffer().sniff(text[:5000], delimiters=";,\t")
    return list(csv.reader(io.StringIO(text), dialect))


def read_xlsx(data):
    """Première feuille d'un classeur Excel, sans bibliothèque externe."""
    z = zipfile.ZipFile(io.BytesIO(data))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
            shared.append("".join(t.text or "" for t in si.iter() if local(t.tag) == "t"))
    sheet = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))[0]
    rows = []
    for row in ET.fromstring(z.read(sheet)).iter("{%s}row" % ns["m"]):
        values = {}
        for cell in row.findall("m:c", ns):
            ref = re.match(r"([A-Z]+)", cell.get("r", "A")).group(1)
            col = 0
            for ch in ref:
                col = col * 26 + ord(ch) - 64
            kind, v = cell.get("t"), cell.find("m:v", ns)
            if kind == "s" and v is not None:
                value = shared[int(v.text)]
            elif kind == "inlineStr":
                value = "".join(t.text or "" for t in cell.iter() if local(t.tag) == "t")
            else:
                value = v.text if v is not None else ""
            values[col - 1] = value
        if values:
            rows.append([values.get(i, "") for i in range(max(values) + 1)])
    return rows


# ---------------------------------------------------------------- point d'entrée

def iter_sources(paths):
    """(nom, octets) de chaque fichier, en ouvrant les dossiers et les archives .zip."""
    for path in paths:
        path = pathlib.Path(path)
        if path.is_dir():
            yield from iter_sources(sorted(p for p in path.rglob("*") if p.is_file()))
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as z:
                for name in z.namelist():
                    if not name.endswith("/"):
                        yield f"{path.name}/{name}", z.read(name)
        else:
            yield path.name, path.read_bytes()


def read_files(paths, overrides=None, prescriptions_only=True):
    """Toutes les prescriptions des fichiers donnés, avec un résumé de ce qui a été lu."""
    pseudonymize, prescriptions, summary = Pseudonymizer(), [], []
    for name, data in iter_sources(paths):
        suffix = pathlib.Path(name).suffix.lower()
        if suffix == ".xml" or data[:200].lstrip().startswith(b"<"):
            rows = read_kmehr(io.BytesIO(data), pseudonymize, prescriptions_only)
            summary.append((name, "KMEHR", len(rows), None))
        elif suffix in (".csv", ".txt"):
            rows, cols = read_rows(read_csv(data), pseudonymize, overrides)
            summary.append((name, "CSV", len(rows), cols))
        elif suffix == ".xlsx":
            rows, cols = read_rows(read_xlsx(data), pseudonymize, overrides)
            summary.append((name, "Excel", len(rows), cols))
        else:
            summary.append((name, "ignoré", 0, None))
            continue
        prescriptions.extend(rows)
    return prescriptions, summary
