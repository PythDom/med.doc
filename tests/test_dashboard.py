"""Tests du tableau de bord : lecture des exports (KMEHR, CSV, Excel), indicateurs et page produite."""
import datetime as dt
import io
import pathlib
import tempfile
import unittest
import zipfile

from dashboard import indicators, readers, report
from sam_v2 import load
from tests.test_app import AMP_XML, CHAPTERIV_XML, IMPP_XML, RMB_XML, VMP_XML

KMEHR = """<?xml version="1.0" encoding="UTF-8"?>
<kmehrmessage xmlns="http://www.ehealth.fgov.be/standards/kmehr/schema/v1"><folder>
  <patient><id S="ID-PATIENT" SV="1.0">85073003328</id><firstname>Jeanne</firstname><familyname>Exemple</familyname>
    <birthdate><date>1950-06-15</date></birthdate><sex><cd S="CD-SEX" SV="1.0">female</cd></sex></patient>
  <transaction><cd S="CD-TRANSACTION" SV="1.11">pharmaceuticalprescription</cd><date>2026-03-14</date>
    <item><cd S="CD-ITEM" SV="1.11">medication</cd><content><medicinalproduct>
      <intendedcd S="CD-DRUG-CNK" SV="01-2016">1000001</intendedcd><intendedname>Gabapentine A 400 mg</intendedname>
      </medicinalproduct></content><quantity><decimal>2</decimal></quantity></item>
    <item><cd S="CD-ITEM" SV="1.11">medication</cd><content><substanceproduct>
      <intendedcd S="CD-VMPGROUP" SV="1.0">77</intendedcd><intendedname>gabapentine oral 400 mg</intendedname>
      </substanceproduct></content></item>
    <item><cd S="CD-ITEM" SV="1.11">healthcareelement</cd><content><cd S="CD-DRUG-CNK">1000002</cd></content></item>
  </transaction>
  <transaction><cd S="CD-TRANSACTION" SV="1.11">medicationscheme</cd><date>2026-01-01</date>
    <item><cd S="CD-ITEM" SV="1.11">medication</cd><content><medicinalproduct>
      <intendedcd S="CD-DRUG-CNK" SV="01-2016">1000002</intendedcd></medicinalproduct></content></item>
  </transaction>
</folder></kmehrmessage>"""

CSV = ("N° dossier;Date de naissance;Sexe;Date;Code CNK;Médicament;Quantité\n"
       "A12;15/06/1950;F;14/03/2026;1000001;Gabapentine A;2\n"
       "A12;15/06/1950;F;14/04/2026;1000002;Gabapentine B;1\n"
       "B07;01/01/1990;M;02/05/2026;;Produit sans CNK;1\n")


def xlsx(rows):
    """Classeur Excel minimal (chaînes partagées + une feuille)."""
    strings = sorted({str(c) for row in rows for c in row})
    index = {s: i for i, s in enumerate(strings)}
    sheet_rows = "".join(
        f'<row r="{r + 1}">' + "".join(f'<c r="{chr(65 + c)}{r + 1}" t="s"><v>{index[str(v)]}</v></c>' for c, v in enumerate(row))
        + "</row>" for r, row in enumerate(rows))
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("xl/sharedStrings.xml", f'<sst {ns}>' + "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet {ns}><sheetData>{sheet_rows}</sheetData></worksheet>')
    return buffer.getvalue()


class DashboardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(cls.tmp.name)
        xml_dir = root / "sam-test"
        xml_dir.mkdir()
        for name, content in [("AMP", AMP_XML), ("VMP", VMP_XML), ("RMB", RMB_XML), ("CHAPTERIV", CHAPTERIV_XML),
                              ("IMPP", IMPP_XML)]:
            (xml_dir / f"{name}-1.xml").write_text(content, encoding="utf-8")
        cls.db_path = root / "sam.sqlite"
        load.load(xml_dir, cls.db_path, "2026-10-20")
        (root / "export.xml").write_text(KMEHR, encoding="utf-8")
        (root / "export.csv").write_text(CSV, encoding="utf-8")
        (root / "export.xlsx").write_bytes(xlsx([line.split(";") for line in CSV.strip().split("\n")]))
        cls.root = root

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_kmehr_counts_prescriptions_only_and_pseudonymizes(self):
        rows, summary = readers.read_files([self.root / "export.xml"])
        self.assertEqual(summary[0][1:3], ("KMEHR", 2))
        first, dci = rows
        self.assertEqual((first.cnk, first.packs, first.age, first.sex, first.date), ("1000001", 2.0, 75, "F", dt.date(2026, 3, 14)))
        self.assertEqual((dci.cnk, dci.vmp_group), (None, "77"))
        self.assertEqual(first.patient, dci.patient)
        self.assertNotIn("85073003328", repr(rows))

    def test_kmehr_falls_back_to_medication_history(self):
        content = KMEHR.replace("pharmaceuticalprescription", "contactreport")
        rows = readers.read_kmehr(io.BytesIO(content.encode()), readers.Pseudonymizer())
        self.assertEqual(sorted(r.cnk or "dci" for r in rows), ["1000001", "1000002", "dci"])

    def test_csv_and_xlsx_columns_are_detected(self):
        for name in ("export.csv", "export.xlsx"):
            rows, summary = readers.read_files([self.root / name])
            columns = summary[0][3]
            self.assertEqual((columns["patient"], columns["birth"], columns["date"], columns["cnk"]),
                             ("N° dossier", "Date de naissance", "Date", "Code CNK"), name)
            self.assertEqual([(r.cnk, r.packs, r.age) for r in rows],
                             [("1000001", 2.0, 75), ("1000002", 1.0, 75), (None, 1.0, 36)], name)
            self.assertEqual(rows[0].patient, rows[1].patient)

    def test_column_override_and_missing_columns(self):
        data = "Jour;Produit\n14/03/2026;Gabapentine A\n"
        rows, columns = readers.read_rows(readers.read_csv(data.encode()), readers.Pseudonymizer(), {"date": "Jour"})
        self.assertEqual((len(rows), columns["date"]), (1, "Jour"))
        with self.assertRaises(ValueError):
            readers.read_rows([["Produit"], ["x"]], readers.Pseudonymizer())

    def test_parse_date(self):
        self.assertEqual(readers.parse_date("2026-03-14T10:00:00"), dt.date(2026, 3, 14))
        self.assertEqual(readers.parse_date("14.03.2026"), dt.date(2026, 3, 14))
        self.assertEqual(readers.parse_date("46095"), dt.date(2026, 3, 14))  # numéro de série Excel
        self.assertIsNone(readers.parse_date("bientôt"))

    def test_indicators(self):
        rows, _ = readers.read_files([self.root / "export.csv", self.root / "export.xml"])
        r = indicators.compute(rows, self.db_path)
        self.assertEqual(r["totals"]["unknown"], 1)            # produit sans CNK
        self.assertEqual(r["totals"]["dci"], 1)                # prescription en DCI (groupe VMP)
        self.assertEqual(r["cheap"]["share"], 1.0)             # tout est bon marché ou en DCI
        self.assertEqual([s["cnk"] for s in r["shortages"]], ["1000001"])
        self.assertEqual(r["totals"]["patients"], 3)
        self.assertEqual(r["period"], {"first": "2026-03-14", "last": "2026-05-02"})
        with self.assertRaises(ValueError):
            indicators.compute(rows, self.db_path, start=dt.date(2030, 1, 1))

    def test_report_contains_no_identity(self):
        rows, _ = readers.read_files([self.root / "export.xml", self.root / "export.csv"])
        page = report.render(indicators.compute(rows, self.db_path), files_read=2)
        self.assertIn("Tableau de bord des prescriptions", page)
        for secret in ("85073003328", "Jeanne", "Exemple", "A12", "B07"):
            self.assertNotIn(secret, page)


if __name__ == "__main__":
    unittest.main()
