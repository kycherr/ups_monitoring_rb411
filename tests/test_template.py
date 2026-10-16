import unittest
from pathlib import Path
import yaml

P=Path(__file__).resolve().parents[1] / "zabbix" / "KWDS_UPS_V10_7_Final_Zabbix8.yaml"

class TestTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.export=yaml.safe_load(P.read_text(encoding="utf-8"))["zabbix_export"]
        cls.tpl=cls.export["templates"][0]
    def test_identifiers(self):
        import uuid
        for it in self.tpl["items"]: self.assertEqual(uuid.UUID(it["uuid"]).version,4)
        for tr in self.export["triggers"]: self.assertEqual(uuid.UUID(tr["uuid"]).version,4)
        self.assertEqual(len({it["key"] for it in self.tpl["items"]}),len(self.tpl["items"]))
    def test_dashboard_source(self):
        w=self.tpl["dashboards"][0]["pages"][0]["widgets"][0]
        self.assertEqual(next(f["value"]["key"] for f in w["fields"] if f["name"]=="itemid.0"),"ups.PowerStateText")
        self.assertFalse(any(f["name"].startswith("thresholds.") for f in w["fields"]))
    def test_invariants(self):
        self.assertEqual(len(self.export["triggers"]),15)
        self.assertTrue(any(i["key"]=="ups.RuntimeEstimated" for i in self.tpl["items"]))
        self.assertTrue(any(i["key"]=="ups.PowerStateCode" for i in self.tpl["items"]))
        self.assertTrue(any(i["key"]=="ups.PowerStateText" for i in self.tpl["items"]))
    def test_widgets_no_overlap(self):
        page=self.tpl["dashboards"][0]["pages"][0]
        occupied=set()
        for w in page["widgets"]:
            x,y,ww,hh=map(int,(w["x"],w["y"],w["width"],w["height"]))
            self.assertLessEqual(x+ww,72)
            cells={(a,b) for a in range(x,x+ww) for b in range(y,y+hh)}
            self.assertFalse(occupied.intersection(cells),w["name"])
            occupied.update(cells)

if __name__=="__main__": unittest.main()
