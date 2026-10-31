import tempfile
import unittest
from pathlib import Path

import run_g431b_replication as replication


class ReplicationPlanTests(unittest.TestCase):
    def test_plan_is_deterministic_and_complete(self):
        first = replication.generate_plan(20260830)
        second = replication.generate_plan(20260830)
        self.assertEqual(first, second)
        self.assertEqual(12, len(first))
        self.assertEqual(list(range(1, 13)), [row.order_index for row in first])
        for block in range(1, 4):
            membership = {(row.condition, row.delay_ms) for row in first if row.block == block}
            self.assertEqual(set(replication.CONDITIONS), membership)

    def test_prepare_is_exclusive_and_plan_validates(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "replication"
            repo = Path(__file__).resolve().parents[3]
            replication.prepare(package, 20260830, repo)
            manifest = __import__("json").loads((package / "manifest.json").read_text())
            rows = replication.validate_plan(package, manifest)
            self.assertEqual(12, len(rows))
            with self.assertRaises(FileExistsError):
                replication.prepare(package, 20260830, repo)


if __name__ == "__main__":
    unittest.main()
