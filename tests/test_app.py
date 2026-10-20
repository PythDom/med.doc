"""Tests du chargeur SAM v2, de l'export de la page et du serveur local, sur un mini-export synthétique."""
import http.client
import shutil
import subprocess
import http.server
import json
import pathlib
import re
import sqlite3
import tempfile
import threading
import unittest

from app import export_static, server
from app import queries as q
from sam_v2 import load

NS = 'xmlns="urn:x"'
AMP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<ExportActualMedicines {NS}>
  <Amp code="SAM1-00" vmpCode="10"><Data from="2020-01-01"><OfficialName>Gabapentine A</OfficialName>
    <Status>AUTHORIZED</Status><Name><Fr>Gabapentine A</Fr></Name><BlackTriangle>false</BlackTriangle>
    <MedicineType>ALLOPATHIC</MedicineType></Data>
    <Ampp ctiExtended="1-01"><Data from="2020-01-01"><Atc code="N02BF01"><Description>Gabapentin</Description></Atc>
      <DeliveryModus code="M1"><Description><Fr>Prescription médicale - Art 6</Fr></Description></DeliveryModus>
      <PrescriptionNameFamhp><Fr>Gabapentine A 400 mg gél. 90</Fr></PrescriptionNameFamhp><PackDisplayValue><Fr>90</Fr></PackDisplayValue>
      <Status>AUTHORIZED</Status><CrmLink><Fr>http://cbip/a</Fr></CrmLink></Data>
      <Commercialization><Data from="2020-01-01"/></Commercialization>
      <SupplyProblem><Data from="2026-10-01"><ExpectedEndOn>2026-12-30</ExpectedEndOn>
        <Reason><Fr>Retard dans la production</Fr></Reason><LimitedAvailability>false</LimitedAvailability>
        <ReportedBy>Company</ReportedBy></Data></SupplyProblem>
      <Dmpp code="1000001" deliveryEnvironment="P"><Data from="2020-01-01"><Price>25.00</Price>
        <Cheap>true</Cheap><Cheapest>false</Cheapest><Reimbursable>true</Reimbursable></Data></Dmpp>
    </Ampp>
  </Amp>
  <Amp code="SAM2-00" vmpCode="10"><Data from="2020-01-01"><OfficialName>Gabapentine B</OfficialName>
    <Status>AUTHORIZED</Status><Name><Fr>Gabapentine B</Fr></Name></Data>
    <Ampp ctiExtended="2-01"><Data from="2020-01-01"><Atc code="N02BF01"/>
      <PrescriptionNameFamhp><Fr>Gabapentine B 400 mg gél. 100</Fr></PrescriptionNameFamhp><PackDisplayValue><Fr>200 (2 x 100)</Fr></PackDisplayValue>
      <Status>AUTHORIZED</Status></Data>
      <Commercialization><Data from="2020-01-01"/></Commercialization>
      <Dmpp code="1000002" deliveryEnvironment="P"><Data from="2020-01-01" to="2025-12-31"><Price>99.00</Price>
        <Reimbursable>true</Reimbursable></Data><Data from="2026-01-01"><Price>23.50</Price>
        <Cheap>true</Cheap><Cheapest>true</Cheapest><Reimbursable>true</Reimbursable></Data></Dmpp>
    </Ampp>
    <Ampp ctiExtended="2-02"><Data from="2020-01-01"><Atc code="N02BF01"/>
      <PrescriptionNameFamhp><Fr>Gabapentine B 400 mg gél. 30 (retiré)</Fr></PrescriptionNameFamhp>
      <Status>AUTHORIZED</Status></Data>
      <Commercialization><Data from="2020-01-01" to="2024-01-01"/></Commercialization>
      <Dmpp code="1000003" deliveryEnvironment="P"><Data from="2020-01-01"><Price>0.0000</Price></Data></Dmpp>
    </Ampp>
  </Amp>
</ExportActualMedicines>"""

VMP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<ExportVirtualMedicines {NS}>
  <Vtm code="5"><Data from="2016-01-01"><Name><Fr>gabapentine</Fr></Name></Data></Vtm>
  <VmpGroup code="77"><Data from="2016-01-01"><Name><Fr>gabapentine oral 400 mg</Fr></Name></Data></VmpGroup>
  <Vmp code="10"><Data from="2016-01-01"><Name><Fr>gabapentine 400 mg capsule</Fr></Name>
    <VmpGroup code="77"/><Vtm code="5"/></Data>
    <VmpComponent><Data from="2016-01-01"/><VirtualIngredient><Data from="2016-01-01"><Type>ACTIVE_SUBSTANCE</Type>
      <Substance code="1"><Name><Fr>Gabapentine</Fr></Name></Substance>
      <Strength><NumeratorRange unit="mg"><Min>400.0000</Min><Max>400.0000</Max></NumeratorRange>
      <Denominator unit="1">1.0000</Denominator></Strength></Data></VirtualIngredient></VmpComponent></Vmp>
</ExportVirtualMedicines>"""

RMB_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<ExportReimbursements {NS}>
  <ReimbursementContext code="1000002" codeType="CNK" deliveryEnvironment="P" legalReferencePath="RD20180201-I-0">
    <Data from="2026-01-01"><ReimbursementCriterion category="B" code="262"><Description><Fr>IV.18 douleurs</Fr></Description>
      </ReimbursementCriterion><ReferenceBasePrice>0</ReferenceBasePrice><ReimbursementBasePrice>23.5</ReimbursementBasePrice>
      <CopaymentSupplement>0.50</CopaymentSupplement><Temporary>false</Temporary></Data>
    <Copayment regimeType="1"><Data from="2026-01-01"><FeeAmount>3.63</FeeAmount></Data></Copayment>
    <Copayment regimeType="2"><Data from="2026-01-01"><FeeAmount>6.04</FeeAmount></Data></Copayment>
  </ReimbursementContext>
  <ReimbursementContext code="1000002" codeType="CNK" deliveryEnvironment="P" legalReferencePath="RD20180201-IV-1640000">
    <Data from="2026-01-01"><ReimbursementCriterion category="A" code="5"><Description><Fr>IV.7 épilepsie</Fr></Description>
      </ReimbursementCriterion><ReferenceBasePrice>0</ReferenceBasePrice><ReimbursementBasePrice>23.5</ReimbursementBasePrice>
      <Temporary>false</Temporary></Data>
    <Copayment regimeType="1"><Data from="2026-01-01"><FeeAmount>1.00</FeeAmount></Data></Copayment>
    <Copayment regimeType="2"><Data from="2026-01-01"><FeeAmount>2.00</FeeAmount></Data></Copayment>
  </ReimbursementContext>
</ExportReimbursements>"""

CHAPTERIV_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<ExportChapterIV {NS}>
  <Paragraph ChapterName="IV" ParagraphName="1640000"><Data from="2020-01-01">
    <KeyStringFr>crises d'épilepsie partielles</KeyStringFr><AgreementType>B</AgreementType></Data></Paragraph>
</ExportChapterIV>"""


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(cls.tmp.name)
        xml_dir = root / "sam-test"
        xml_dir.mkdir()
        for name, content in [("AMP", AMP_XML), ("VMP", VMP_XML), ("RMB", RMB_XML), ("CHAPTERIV", CHAPTERIV_XML)]:
            (xml_dir / f"{name}-1.xml").write_text(content, encoding="utf-8")
        cls.db_path = root / "sam.sqlite"
        load.load(xml_dir, cls.db_path, "2026-10-20")
        cls.db = q.connect(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.tmp.cleanup()

    def test_loader_keeps_only_current_data(self):
        raw = sqlite3.connect(self.db_path)
        self.assertEqual(raw.execute("SELECT price FROM dmpp WHERE cnk='1000002'").fetchone()[0], 23.5)
        self.assertEqual(raw.execute("SELECT commercialized FROM ampp WHERE cti_extended='2-02'").fetchone()[0], 0)
        self.assertEqual(raw.execute("SELECT count(*) FROM supply_problem").fetchone()[0], 1)
        raw.close()

    def test_reimbursement_contexts(self):
        contexts = {c["chapter"]: c for c in q.reimbursement_contexts(self.db, "1000002")}
        self.assertEqual(contexts["IV"]["paragraph_key"], "crises d'épilepsie partielles")
        self.assertEqual((contexts["I"]["fee_bim"], contexts["I"]["fee_ordinary"]), (3.63, 6.04))
        self.assertEqual(contexts["I"]["copayment_supplement"], 0.5)

    def test_split_legal_path(self):
        self.assertEqual(q.split_legal_path("RD20180201-IV-1640000"), ("IV", "1640000"))
        self.assertEqual(q.split_legal_path(None), ("", ""))

    def test_export_data(self):
        data = export_static.build(self.db_path)
        products = {p[0]: p for p in data["products"]}
        self.assertEqual(set(products), {"1000001", "1000002", "1000003"})
        flags = products["1000001"][4]
        self.assertTrue(flags & 1 and flags & 8 and flags & 64)  # bon marché, commercialisé, autorisé
        self.assertFalse(products["1000003"][4] & 8)  # retiré du marché
        self.assertIsNone(products["1000003"][3])  # prix 0 € = prix inconnu, pas gratuit
        self.assertIn("1-01", data["supply"])
        self.assertEqual(len(data["contexts"]["1000002"]), 2)
        prefix, suffix = products["1000001"][14][0]  # lien CBIP
        self.assertEqual(data["prefixes"][prefix] + suffix, "http://cbip/a")

    def test_pack_and_substance(self):
        raw = sqlite3.connect(self.db_path)
        self.assertEqual(raw.execute("SELECT amount, unit, denominator, denominator_unit FROM vmp_ingredient").fetchall(),
                         [(400.0, "mg", 1.0, "1")])
        raw.close()
        products = {p[0]: p for p in export_static.build(self.db_path)["products"]}
        self.assertEqual(products["1000001"][15:], [90.0, "", 36000.0, "mg"])
        self.assertEqual(products["1000002"][15:], [200.0, "", 80000.0, "mg"])
        self.assertEqual(export_static.parse_pack("5 x 1 ml + 5 x Injection needle"), (5.0, "ml"))
        self.assertEqual(export_static.parse_pack("1 l"), (1000.0, "ml"))
        self.assertEqual(export_static.parse_pack("Kit"), (None, None))

    @unittest.skipUnless(shutil.which("node"), "Node.js non installé")
    def test_page_highlight_functions(self):
        template = export_static.TEMPLATE.read_text(encoding="utf-8")
        pure = template.split("// BEGIN-PURE")[1].split("\n", 1)[1].split("// END-PURE")[0]
        script = pure + """
// cost = ce que paie le patient ; price = prix public.
const cost = x => x.cost;
const src = { qty: 90, unit: "" };
const a = { name: "a", qty: 100, unit: "", price: 23.52, cost: 6.04, subst: 40000 };
const b = { name: "b", qty: 90, unit: "", price: 25.08, cost: 6.56, subst: 36000 };
const c = { name: "c", qty: 90, unit: "", price: 25.25, cost: 6.60, subst: 36000 };
const d = { name: "d", qty: 200, unit: "", price: 46.14, cost: 11.51, subst: 80000 };
const n = { name: "n", qty: 90, unit: "", price: 15.00, cost: 15.00, subst: 36000 };  // non remboursé
const u = { name: "u", qty: 90, unit: "", price: 9.00, cost: null };                // coût inconnu
const e = { name: "e", qty: 90, unit: "ml", price: 1, cost: 1 };
const rows = [a, b, c, d, n, u, e];
const h = withHighlights([a, b, c, d], [[closestQuantity(src, rows, cost), "proche"], [cheapestBy([a, b, c, d], x => perUnit(x, cost)), "unité"]], 2);
console.log(JSON.stringify({
  closest: closestQuantity(src, rows, cost).name,
  perUnit: cheapestBy([a, b, c, d, n, u], x => perUnit(x, cost)).name,
  perSubstance: cheapestBy(rows, x => perSubstance(x, cost)).name,
  none: closestQuantity({ qty: null }, rows, cost),
  order: h.rows.map(x => x.name), tags: [...h.tags.values()] }));
"""
        out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout
        # Le non remboursé n (15 €, prix public le plus bas parmi les boîtes de 90) n'est jamais retenu :
        # le patient paie 15 € contre 6,56 € pour b.
        self.assertEqual(json.loads(out), {"closest": "b", "perUnit": "d", "perSubstance": "d", "none": None,
                                           "order": ["b", "d"], "tags": [["proche"], ["unité"]]})

    def test_render_standalone_page(self):
        page = export_static.render(self.db_path)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertNotIn("/*__DATA__*/", page)
        payload = re.search(r"const DATA = (.*?);\nconst T =", page, re.S).group(1)
        self.assertEqual(json.loads(payload)["meta"]["export"], "sam-test")
        self.assertFalse(export_static.render(self.db_path, standalone=False).startswith("<!doctype"))

    def test_server_routes(self):
        server.Handler.cache = server.PageCache(self.db_path)
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            def get(path):
                conn = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=10)
                conn.request("GET", path)
                response = conn.getresponse()
                body = response.read().decode("utf-8")
                conn.close()
                return response, body
            response, body = get("/")
            self.assertEqual(response.status, 200)
            self.assertIn("Officine SAM", body)
            response, _ = get("/produit/1000001")
            self.assertEqual((response.status, response.getheader("Location")), (302, "/#p1000001"))
            self.assertEqual(get("/inconnu")[0].status, 404)
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
