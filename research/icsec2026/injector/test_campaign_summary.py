import importlib.util
import math
import sys
import unittest
from pathlib import Path


INJECTOR_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(INJECTOR_DIR))
SPEC = importlib.util.spec_from_file_location(
    "summarize_payload_campaign", INJECTOR_DIR / "summarize_payload_campaign.py"
)
assert SPEC is not None and SPEC.loader is not None
summary = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = summary
SPEC.loader.exec_module(summary)


class ExactIntervalTests(unittest.TestCase):
    def test_all_successes_has_expected_exact_lower_bound(self):
        lower, upper = summary.exact_binomial_ci(30, 30)
        self.assertAlmostEqual((0.025 ** (1.0 / 30.0)), lower, places=10)
        self.assertEqual(1.0, upper)

    def test_no_successes_has_expected_exact_upper_bound(self):
        lower, upper = summary.exact_binomial_ci(0, 30)
        self.assertEqual(0.0, lower)
        self.assertAlmostEqual(1.0 - (0.025 ** (1.0 / 30.0)), upper, places=10)

    def test_latency_summary_reports_inclusive_iqr(self):
        result = summary.latency_statistics([1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(3.0, result["median_ms"])
        self.assertEqual(2.0, result["q1_ms"])
        self.assertEqual(4.0, result["q3_ms"])
        self.assertEqual(2.0, result["iqr_ms"])

    def test_single_latency_has_zero_iqr(self):
        result = summary.latency_statistics([7.5])
        self.assertEqual(7.5, result["median_ms"])
        self.assertEqual(0.0, result["iqr_ms"])


if __name__ == "__main__":
    unittest.main()
