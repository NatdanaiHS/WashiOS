import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_f411_campaign import PLAN, mark_remaining, outcome_summary, plan_rows
from run_payload_campaign import SerialEvent


def event(text: str) -> SerialEvent:
    return SerialEvent("controller", "2026-09-01T00:00:00+00:00", 1.0, b"", text)


class F411CampaignTests(unittest.TestCase):
    def test_authoritative_plan_matches_sha256_ordering(self):
        expected = []
        row = 0
        for block in range(1, 4):
            conditions = ("NC", "D090", "D100", "D110")
            ordered = sorted(
                conditions,
                key=lambda condition: hashlib.sha256(
                    f"20260901|B{block}|{condition}".encode("utf-8")).hexdigest(),
            )
            for condition in ordered:
                row += 1
                expected.append((row, block, condition))
        actual = [(int(item["row"]), int(item["block"]), str(item["condition"]))
                  for item in plan_rows()]
        self.assertEqual(expected, actual)
        self.assertEqual(12, len(PLAN))

    def test_delayed_unexpected_explicit_markers_remain_attributable(self):
        result = outcome_summary([
            event("[OBC] PAYLOAD_TIMEOUT seq=4 consecutive=1"),
            event("[OBC] PAYLOAD_REJECT reason=SEQUENCE expected=5 got=4"),
        ], "D090")
        self.assertTrue(result["explicit_attributable_outcome"])
        self.assertEqual(1, result["timeout"])
        self.assertEqual(0, result["offline"])

    def test_nc_adverse_marker_is_counted_not_invalidated(self):
        result = outcome_summary([
            event("[OBC] PAYLOAD_ACCEPTED seq=4 mode=0"),
            event("[OBC] PAYLOAD_TIMEOUT seq=5 consecutive=1"),
        ], "NC")
        self.assertTrue(result["explicit_attributable_outcome"])
        self.assertEqual(1, result["false_marker_count"])

    def test_first_invalid_marks_only_later_rows_not_attempted(self):
        ledger = {"rows": [dict(row, status="PLANNED", attempted=False, valid=None)
                           for row in plan_rows()]}
        ledger["rows"][2].update(status="INVALID", attempted=True, valid=False)
        mark_remaining(ledger, 3)
        self.assertEqual("PLANNED", ledger["rows"][0]["status"])
        self.assertEqual("INVALID", ledger["rows"][2]["status"])
        self.assertTrue(all(row["status"] == "NOT_ATTEMPTED_AFTER_STOP"
                            for row in ledger["rows"][3:]))


if __name__ == "__main__":
    unittest.main()
