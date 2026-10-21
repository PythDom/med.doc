"""Construit le tableau de bord à partir d'exports du logiciel médical (Medispring ou autre).

Usage :
  python -m dashboard.build EXPORT [EXPORT ...] [--db data/sam.sqlite] [--out data/tableau-de-bord.html]
                            [--regime 2] [--depuis 2026-01-01] [--jusqu-au 2026-06-30] [--colonne cnk="Code CNK"]

EXPORT : fichiers KMEHR (.xml), archives .zip, dossiers, tableaux .csv ou .xlsx.
Tout est traité sur cet ordinateur ; la page produite ne contient que des chiffres agrégés et des numéros de
produits, jamais d'identité de patient. Elle s'ouvre directement ou via le prototype (http://localhost:8765/tableau-de-bord).
"""
import argparse
import datetime as dt
import pathlib

from dashboard import indicators, readers, report


def build(paths, db_path, out, regime="2", start=None, end=None, overrides=None, base_url="/"):
    prescriptions, summary = readers.read_files(paths, overrides)
    tables = [(n, k, c, cols) for n, k, c, cols in summary if cols]
    for name, kind, count, columns in tables:  # pour un tableau, montrer les colonnes reconnues
        detected = ", ".join(f"{field}={header!r}" for field, header in columns.items() if header)
        print(f"  {name} : {kind}, {count} prescription(s) · colonnes : {detected}")
    by_kind = {}
    for _, kind, count, columns in summary:
        if not columns:
            files, rows = by_kind.get(kind, (0, 0))
            by_kind[kind] = (files + 1, rows + count)
    for kind, (files, rows) in by_kind.items():
        print(f"  {kind} : {files} fichier(s), {rows} prescription(s)")
    if not prescriptions:
        raise SystemExit("Aucune prescription lue. Vérifiez le format des fichiers (voir python -m dashboard.build --help).")
    result = indicators.compute(prescriptions, db_path, start, end, regime)
    page = report.render(result, base_url, files_read=len(summary), generated=dt.date.today().strftime("%d/%m/%Y"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    t = result["totals"]
    print(f"Tableau de bord : {out} ({t['prescriptions']} prescriptions, {t['patients']} patients, "
          f"{result['period']['first']} → {result['period']['last']})")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("exports", nargs="+", type=pathlib.Path)
    p.add_argument("--db", type=pathlib.Path, default=pathlib.Path("data/sam.sqlite"))
    p.add_argument("--out", type=pathlib.Path, default=pathlib.Path("data/tableau-de-bord.html"))
    p.add_argument("--regime", choices=("1", "2"), default="2", help="coût patient : 1 = BIM, 2 = ordinaire")
    p.add_argument("--depuis", type=dt.date.fromisoformat, help="première date incluse (AAAA-MM-JJ)")
    p.add_argument("--jusqu-au", dest="until", type=dt.date.fromisoformat, help="dernière date incluse (AAAA-MM-JJ)")
    p.add_argument("--colonne", action="append", default=[], metavar="CHAMP=EN-TÊTE",
                   help="forcer une colonne d'un tableau : cnk, date, patient, birth, age, sex, packs, name, vmp_group")
    p.add_argument("--fichier-autonome", action="store_true",
                   help="liens vers medicaments.html (page autonome) au lieu du prototype local")
    a = p.parse_args()
    overrides = dict(item.split("=", 1) for item in a.colonne)
    build(a.exports, a.db, a.out, a.regime, a.depuis, a.until, overrides,
          "medicaments.html" if a.fichier_autonome else "/")


if __name__ == "__main__":
    main()
