import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_f411_pair1 import classify_pilot_markers, validate_normal_statuses


class F411Pair1HarnessTests(unittest.TestCase):
    def test_normal_validation_accepts_strict_online_series(self):
        statuses = [
            {"state": "ONLINE", "ok": 20 + index, "timeout": 0,
             "crc": 0, "seq": 0, "recovery": 0}
            for index in range(10)
        ]
        self.assertEqual([], validate_normal_statuses(statuses))

    def test_normal_validation_rejects_counter_change(self):
        statuses = [
            {"state": "ONLINE", "ok": 20 + index, "timeout": int(index == 9),
             "crc": 0, "seq": 0, "recovery": 0}
            for index in range(10)
        ]
        self.assertIn("TIMEOUT_COUNTER_DELTA", validate_normal_statuses(statuses))

    def test_pilot_classification_is_outcome_neutral(self):
        self.assertEqual(
            "ACCEPTED_DELAYED_RESPONSE",
            classify_pilot_markers(["[OBC] PAYLOAD_ACCEPTED seq=3 mode=3"]),
        )
        self.assertEqual(
            "TIMEOUT_REJECTION_OFFLINE",
            classify_pilot_markers(["[OBC] PAYLOAD_OFFLINE consecutive=3"]),
        )
        self.assertIsNone(classify_pilot_markers(["[OBC] PAYLOAD_STATUS state=ONLINE"]))


if __name__ == "__main__":
    unittest.main()
