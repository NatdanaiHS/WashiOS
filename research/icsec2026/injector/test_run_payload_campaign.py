import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_payload_campaign.py")
SPEC = importlib.util.spec_from_file_location("run_payload_campaign", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
campaign = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = campaign
SPEC.loader.exec_module(campaign)


class RunPlanTests(unittest.TestCase):
    def test_same_seed_reproduces_identical_plan(self):
        first = campaign.generate_run_plan(8675309, 3, 0.25, 1.25)
        second = campaign.generate_run_plan(8675309, 3, 0.25, 1.25)
        self.assertEqual(first, second)

    def test_plan_contains_all_faults_per_repetition_and_bounded_offsets(self):
        plan = campaign.generate_run_plan(42, 2, 0.2, 0.4)
        self.assertEqual(6, len(plan))
        self.assertEqual(
            {"P01": 2, "P02": 2, "P03": 2},
            {fault: sum(entry.fault_id == fault for entry in plan) for fault in ("P01", "P02", "P03")},
        )
        self.assertTrue(all(0.2 <= entry.pre_injection_offset_s <= 0.4 for entry in plan))


class StorageAndClassificationTests(unittest.TestCase):
    def test_creates_manifest_csv_and_non_overwritable_raw_logs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = campaign.generate_run_plan(7, 1, 0.1, 0.1)
            store = campaign.CampaignStore(root, "dry-run", {"status": "TEST"}, plan)
            g431, g474 = store.open_run_logs(plan[0].run_id)
            g431.write("timestamp\t4142\tAB\n")
            g474.write("timestamp\t4344\tCD\n")
            g431.close()
            g474.close()
            store.append_result(campaign.blank_result(plan[0], 7))

            self.assertTrue((root / "dry-run" / "manifest.json").is_file())
            with (root / "dry-run" / "run_plan.csv").open(newline="", encoding="utf-8") as handle:
                self.assertEqual(3, len(list(csv.DictReader(handle))))
            with self.assertRaises(FileExistsError):
                store.open_run_logs(plan[0].run_id)

    def test_fault_specific_detection_rules(self):
        def event(text):
            return campaign.SerialEvent("g431", "t", 1.0, b"", text)

        events = [
            event("[OBC] PAYLOAD_TIMEOUT consecutive=1"),
            event("[OBC] PAYLOAD_REJECT reason=CRC"),
        ]
        self.assertIn("TIMEOUT", campaign.detection_event("SILENT", events).text)
        self.assertIn("reason=CRC", campaign.detection_event("BAD_CRC", events).text)
        self.assertIn("TIMEOUT", campaign.detection_event("DELAYED", events).text)


if __name__ == "__main__":
    unittest.main()
