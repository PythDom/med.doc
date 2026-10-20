"""Tests du chargeur SAM v2 et des requêtes du prototype, sur un mini-export synthétique."""
import pathlib
import sqlite3
import tempfile
import unittest

from app import queries as q
from app import server
from sam_v2 import load

NS = 'xmlns="urn:x"'
AMP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<ExportActualMedicines {NS}>
  <Amp code="SAM1-00" vmpCode="10"><Data from="2020-01-01"><OfficialName>Gabapentine A</OfficialName>
    <Status>AUTHORIZED</Status><Name><Fr>Gabapentine A</Fr></Name><BlackTriangle>false</BlackTriangle>
    <MedicineType>ALLOPATHIC</MedicineType></Data>
    <Ampp ctiExtended="1-01"><Data from="2020-01-01"><Atc code="N02BF01"><Description>Gabapentin</Description></Atc>
      <DeliveryModus code="M1"><Description><Fr>Prescription médicale - Art 6</Fr></Description></DeliveryModus>
      <PrescriptionNameFamhp><Fr>Gabapentine A 400 mg gél. 90</Fr></PrescriptionNameFamhp>
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
      <PrescriptionNameFamhp><Fr>Gabapentine B 400 mg gél. 100</Fr></PrescriptionNameFamhp>
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
      <Dmpp code="1000003" deliveryEnvironment="P"><Data from="2020-01-01"><Price>9.00</Price></Data></Dmpp>
    </Ampp>
  </Amp>
</ExportActualMedicines>"""

VMP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<ExportVirtualMedicines {NS}>
  <Vtm code="5"><Data from="2016-01-01"><Name><Fr>gabapentine</Fr></Name></Data></Vtm>
  <VmpGroup code="77"><Data from="2016-01-01"><Name><Fr>gabapentine oral 400 mg</Fr></Name></Data></VmpGroup>
  <Vmp code="10"><Data from="2016-01-01"><Name><Fr>gabapentine 400 mg capsule</Fr></Name>
    <VmpGroup code="77"/><Vtm code="5"/></Data></Vmp>
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

    def test_search_by_name_ignores_accents_and_case(self):
        self.assertEqual({r["cnk"] for r in q.search(self.db, "GABAPENTINE 400")}, {"1000001", "1000002", "1000003"})
        self.assertEqual(len(q.search(self.db, "gabapentine épilepsie")), 0)

    def test_search_by_cnk(self):
        rows = q.search(self.db, "1000001")
        self.assertEqual([r["cnk"] for r in rows], ["1000001"])
        self.assertTrue(rows[0]["supply_problem"])

    def test_alternatives_exclude_shortages_and_withdrawn_packs(self):
        prod = q.product(self.db, "1000001")
        same_group = q.alternatives(self.db, prod)[0][1]
        self.assertEqual([r["cnk"] for r in same_group], ["1000002"])

    def test_reimbursement_contexts_and_patient_cost(self):
        contexts = {c["chapter"]: c for c in q.reimbursement_contexts(self.db, "1000002")}
        self.assertEqual(contexts["IV"]["paragraph_key"], "crises d'épilepsie partielles")
        self.assertAlmostEqual(q.patient_cost(contexts["I"], "1"), 4.13)  # ticket BIM + supplément
        self.assertAlmostEqual(q.patient_cost(contexts["IV"], "2"), 2.00)

    def test_split_legal_path(self):
        self.assertEqual(q.split_legal_path("RD20180201-IV-1640000"), ("IV", "1640000"))
        self.assertEqual(q.split_legal_path(None), ("", ""))

    def test_product_page_renders(self):
        title, body = server.render_product(self.db, "1000001", "1")
        self.assertEqual(title, "Gabapentine A 400 mg gél. 90")
        self.assertIn("Problème d'approvisionnement", body)
        self.assertIn("Gabapentine B 400 mg gél. 100", body)
        self.assertNotIn("(retiré)", body)
        self.assertIn("Prescription médicale", body)
        self.assertIsNone(server.render_product(self.db, "9999999", "1")[0])


if __name__ == "__main__":
    unittest.main()
