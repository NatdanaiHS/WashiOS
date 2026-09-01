import unittest

import run_f411_campaign as shared
import run_f411_pair2_campaign as pair2


class Pair2ConfigurationTests(unittest.TestCase):
    def setUp(self):
        pair2.configure()

    def test_pair2_fixed_identity_and_order(self):
        self.assertEqual("F411_P2_CAMPAIGN_20260901_B3", shared.CAMPAIGN_ID)
        self.assertEqual("0669FF495051727187053226", shared.CONTROLLER_STLINK)
        self.assertEqual("0663FF495051727187066042", shared.PAYLOAD_STLINK)
        self.assertEqual(pair2.PAIR2_PLAN, shared.PLAN)
        self.assertEqual(12, len(shared.PLAN))

    def test_pair2_diff_is_configuration_only(self):
        self.assertIs(shared.acquire, pair2.campaign.acquire)
        self.assertIs(shared.stabilization, pair2.campaign.stabilization)
        self.assertIs(shared.outcome_summary, pair2.campaign.outcome_summary)
        self.assertEqual(4.0, shared.EXPOSURE_S)
        self.assertEqual(20260901, shared.SEED)


if __name__ == "__main__":
    unittest.main()
