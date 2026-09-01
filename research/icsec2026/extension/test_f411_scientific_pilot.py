import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_f411_scientific_pilot import classify_attributable_outcome
from run_payload_campaign import SerialEvent


def event(text: str) -> SerialEvent:
    return SerialEvent("controller", "2026-09-01T00:00:00+00:00", 1.0, b"", text)


class ScientificPilotValidationTests(unittest.TestCase):
    def test_accepts_explicit_delayed_response_only_with_mode_marker(self):
        result = classify_attributable_outcome([
            event("[OBC] PAYLOAD_ACCEPTED seq=4 mode=3")
        ])
        self.assertTrue(result["valid"])
        self.assertEqual("ACCEPTED_DELAYED_RESPONSE", result["classification"])

    def test_accepts_ordered_timeout_to_offline_path(self):
        result = classify_attributable_outcome([
            event("[OBC] PAYLOAD_TIMEOUT seq=4 consecutive=1"),
            event("[OBC] PAYLOAD_REJECT reason=SEQUENCE expected=5 got=4"),
            event("[OBC] PAYLOAD_OFFLINE consecutive=3"),
        ])
        self.assertTrue(result["valid"])
        self.assertEqual("ORDERED_TIMEOUT_PATH_TO_OFFLINE", result["classification"])

    def test_rejects_absence_only_and_offline_without_prior_timeout(self):
        self.assertFalse(classify_attributable_outcome([])["valid"])
        result = classify_attributable_outcome([
            event("[OBC] PAYLOAD_OFFLINE consecutive=3")
        ])
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
