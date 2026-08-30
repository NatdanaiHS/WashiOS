import importlib.util
import sys
import unittest
from pathlib import Path


INJECTOR_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(INJECTOR_DIR))
SPEC = importlib.util.spec_from_file_location("run_n0_control", INJECTOR_DIR / "run_n0_control.py")
assert SPEC is not None and SPEC.loader is not None
n0 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = n0
SPEC.loader.exec_module(n0)
from run_payload_campaign import SerialEvent


def event(index, text):
    return SerialEvent("g431", f"t{index}", float(index), b"", text)


class N0ValidationTests(unittest.TestCase):
    def test_accepts_stable_online_window(self):
        events = [
            event(
                index,
                f"[OBC] PAYLOAD_STATUS state=ONLINE polls={100 + index} "
                f"ok={80 + index} timeout=3 crc=4 seq=5 recovery=1 "
                "heartbeat=OK watchdog=OK",
            )
            for index in range(12)
        ]
        result = n0.validate_n0_events(events, 65.0)
        self.assertTrue(result["valid"])
        self.assertEqual(12, result["status_count"])
        self.assertEqual({"timeout": 0, "crc": 0, "seq": 0, "recovery": 0}, result["counter_deltas"])

    def test_rejects_fault_delta_transition_and_nonincreasing_ok(self):
        events = []
        for index in range(10):
            ok = 80 + index if index < 9 else 88
            timeout = 3 if index < 9 else 4
            events.append(
                event(
                    index,
                    f"[OBC] PAYLOAD_STATUS state=ONLINE polls={100 + index} "
                    f"ok={ok} timeout={timeout} crc=4 seq=5 recovery=1 "
                    "heartbeat=OK watchdog=OK",
                )
            )
        events.append(event(11, "[OBC] PAYLOAD_TIMEOUT consecutive=1"))
        result = n0.validate_n0_events(events, 65.0)
        self.assertFalse(result["valid"])
        self.assertIn("OK_COUNTER_NOT_STRICTLY_INCREASING", result["failures"])
        self.assertIn("FAULT_COUNTER_DELTA_NONZERO", result["failures"])
        self.assertIn("PROHIBITED_TRANSITION_MARKER_OBSERVED", result["failures"])


if __name__ == "__main__":
    unittest.main()
