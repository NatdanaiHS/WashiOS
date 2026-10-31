import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_f411_cross_pair_synthesis as synthesis


class CrossPairSynthesisTests(unittest.TestCase):
    def test_inputs_are_two_separate_pairs(self):
        self.assertEqual(["Pair-1", "Pair-2"], [item["pair"] for item in synthesis.PAIR_SPECS])
        self.assertEqual(12, 3 * len(synthesis.CONDITIONS))

    def test_allowed_claim_is_bounded(self):
        claim = synthesis.ALLOWED_CLAIM.lower()
        self.assertIn("each of two separate physical", claim)
        self.assertNotIn("reliability", claim)
        self.assertNotIn("population", claim)


if __name__ == "__main__":
    unittest.main()
