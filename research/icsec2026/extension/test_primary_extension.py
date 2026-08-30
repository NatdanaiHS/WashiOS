import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("run_primary_extension.py")
SPEC = importlib.util.spec_from_file_location("run_primary_extension", MODULE)
assert SPEC is not None and SPEC.loader is not None
extension = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = extension
SPEC.loader.exec_module(extension)


class PlanTests(unittest.TestCase):
    def test_five_block_plan_is_deterministic_complete_and_constrained(self):
        first = extension.generate_plan(20260830, 5)
        second = extension.generate_plan(20260830, 5)
        self.assertEqual(first, second)
        self.assertEqual(45, len(first))
        for block in range(1, 6):
            rows = [row for row in first if row.block == block]
            self.assertEqual(2, sum(row.condition == "NC" for row in rows))
            self.assertEqual(set(extension.DELAYS_MS),
                             {row.delay_ms for row in rows if row.condition == "DELAY"})
        conditions = [row.condition for row in first]
        self.assertTrue(extension.plan_constraints_pass(conditions))

    def test_scope_down_plan_retains_all_conditions(self):
        plan = extension.generate_plan(7, 3)
        self.assertEqual(27, len(plan))
        self.assertEqual(6, sum(row.condition == "NC" for row in plan))
        for delay in extension.DELAYS_MS:
            self.assertEqual(3, sum(row.delay_ms == delay for row in plan))


class StatusTests(unittest.TestCase):
    def test_status_parser_and_prohibited_marker_collection(self):
        event = extension.SerialEvent(
            "g431", "t", 1.0, b"",
            "[OBC] PAYLOAD_STATUS state=ONLINE polls=10 ok=9 timeout=1 crc=2 seq=3 recovery=4 heartbeat=OK watchdog=OK",
        )
        record = extension.status_record(event)
        self.assertEqual("ONLINE", record["state"])
        self.assertEqual(9, record["ok"])
        bad = extension.SerialEvent("g431", "t2", 2.0, b"", "[OBC] PAYLOAD_TIMEOUT consecutive=1")
        self.assertEqual(1, len(extension.prohibited_records([event, bad])))


if __name__ == "__main__":
    unittest.main()
