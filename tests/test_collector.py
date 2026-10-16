import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "collector" / "ups_megatec.py"
spec = importlib.util.spec_from_file_location("ups_megatec", PATH)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

class TestMegatec(unittest.TestCase):
    def test_parse_good_frame(self):
        x = collector.parse("(222.3 120.0 229.8 037 50.0 2.28 20.0 00000001")
        self.assertEqual(x["ups.BatteryRaw"], 2.28)
        self.assertEqual(x["ups.InputVoltage"], 222.3)
        self.assertEqual(x["ups.UpsLoad"], 37)
        self.assertEqual(x["ups.UpsStatus"], "OL")
        self.assertEqual(x["ups.OnBattery"], 0)
    def test_two_decimal_precision(self):
        x = collector.parse("(220.0 120.0 230.0 030 50.0 2.20 19.0 00000001")
        self.assertEqual(x["ups.BatteryRaw"], 2.2)
    def test_on_battery_low(self):
        x = collector.parse("(000.0 120.0 230.0 030 50.0 2.10 20.0 11000000")
        self.assertEqual(x["ups.UpsStatus"], "OB LB")
        self.assertEqual(x["ups.OnBattery"], 1)
        self.assertEqual(x["ups.BatteryLow"], 1)
    def test_truncated_or_corrupt(self):
        for bad in ("(224.9 1", "�����Q1", "Q1", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    collector.parse(bad)
    def test_out_of_range_load(self):
        with self.assertRaises(ValueError):
            collector.parse("(220.0 120.0 230.0 201 50.0 2.20 19.0 00000001")

if __name__ == "__main__": unittest.main()
