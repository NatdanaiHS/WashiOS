import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_status_windows as csw  # noqa: E402


class StatusWindowTests(unittest.TestCase):
    def test_classify_is_strict_and_relative(self):
        self.assertEqual(csw.classify(1000.0, 1500.0, [999.0, 1000.0, 1200.4, 1500.0, 1600.0]), [200.4])

    def test_inventory_covers_every_primary_raw_log(self):
        inv = csw.load_inventory()
        self.assertEqual(sum(1 for k in inv if k.endswith("/g431.log")), 90)
        self.assertIn("R085_P02/g431.log", inv)

    def test_missing_backup_is_reported_not_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = csw.analyse(Path(tmp))
        self.assertEqual(report["runs_checked"], 0)
        self.assertEqual(len(report["runs_missing"]), 90)

    def test_altered_log_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "R085_P02"
            run.mkdir()
            (run / "g431.log").write_text("2026-08-29T19:23:21.000000+00:00\t0a\t\\n\n", encoding="utf-8")
            report = csw.analyse(Path(tmp))
        self.assertEqual(report["runs_checked"], 0)
        self.assertEqual(report["hash_mismatches"][0]["run_id"], "R085_P02")


if __name__ == "__main__":
    unittest.main()
