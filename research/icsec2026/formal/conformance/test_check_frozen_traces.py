import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_frozen_traces as cft  # noqa: E402


class BoundDerivationTests(unittest.TestCase):
    def test_bounds_follow_model_constants(self):
        self.assertEqual(cft.FIRST_TIMEOUT_BOUND_MS, 605)
        self.assertEqual(cft.OFFLINE_BOUND_MS, 1609)
        self.assertEqual(cft.RECOVERY_BOUND_MS, 506)

    def test_falsification_floor_exceeds_demonstrated_clock_disagreement(self):
        """The floor must not be fitted to the data: it has to dominate the clock disagreement."""
        observed = cft.check_primary_campaign()["clock_disagreement_ms"]["max"]
        self.assertGreater(cft.RESOLUTION_MS, 3 * observed)

    def test_delay_boundary_classification(self):
        # 50/90 ms provably accepted, 110+ ms provably time out, 100 ms is in the undetermined band
        for d in (50, 90):
            self.assertTrue(cft.model_accepts(d) and not cft.model_times_out(d))
        for d in (110, 150, 250):
            self.assertTrue(cft.model_times_out(d) and not cft.model_accepts(d))
        self.assertFalse(cft.model_accepts(100) or cft.model_times_out(100))


class FrozenEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.primary = cft.check_primary_campaign()

    def test_no_alphabet_or_gross_bound_issues(self):
        self.assertEqual(self.primary["issues"], [])
        self.assertEqual(self.primary["rows"], 90)
        self.assertEqual(self.primary["bound_check"]["violations_beyond_floor"], 0)

    def test_bound_check_accounts_for_every_interval(self):
        bc = self.primary["bound_check"]
        self.assertEqual(bc["intervals"], 180)
        self.assertEqual(bc["within_bound"] + bc["unresolved"], bc["intervals"])
        # One BAD_CRC recovery interval exceeds the 506 ms bound and cannot be resolved by the
        # recorded evidence; it is reported rather than absorbed.
        self.assertEqual(bc["unresolved"], 1)
        only = self.primary["unresolved_intervals"][0]
        self.assertEqual((only["mode"], only["interval"]), ("BAD_CRC", "recovery"))
        self.assertLess(only["excess_ms"], cft.RESOLUTION_MS)

    def test_confirmation_anchor_is_tighter_than_command_anchor(self):
        """The model's clock starts at confirmation, so re-anchoring must not inflate the interval."""
        for mode, m in self.primary["per_mode"].items():
            for kind in ("detection", "recovery"):
                self.assertLessEqual(m["confirmation_anchored"][kind]["max_ms"],
                                     m["command_anchored"][kind]["max_ms"], f"{mode} {kind}")

    def test_all_confirmation_anchored_detection_within_bound(self):
        for mode, m in self.primary["per_mode"].items():
            self.assertLessEqual(m["confirmation_anchored"]["detection"]["max_ms"],
                                 cft.FIRST_TIMEOUT_BOUND_MS, mode)

    def test_detector_alphabet_matches_in_every_trial(self):
        for mode, m in self.primary["per_mode"].items():
            self.assertEqual(m["detector_alphabet_ok"], 30, mode)
            self.assertEqual(m["restart_marker"], 0, mode)

    def test_n0_windows_conform(self):
        for path in (cft.N0_PRE, cft.N0_POST):
            self.assertEqual(cft.check_n0(path)["issues"], [])

    def test_extension_and_f411_conform(self):
        ext = cft.check_extension_delay_sweep()
        self.assertEqual(ext["issues"], [])
        self.assertEqual(ext["delay_sweep"][100]["verdict"], "BOUNDARY_UNDETERMINED_CONSISTENT")
        self.assertEqual(ext["delay_sweep"][90]["verdict"], "CONFORMS")
        self.assertEqual(ext["delay_sweep"][110]["verdict"], "CONFORMS")
        self.assertNotIn(500, ext["delay_sweep"], "no valid 500 ms row exists in the frozen sweep")
        for pair in cft.F411:
            if pair.exists():
                self.assertEqual(cft.check_f411(pair)["issues"], [])

    def test_timebase_is_measured_not_assumed(self):
        tb = cft.measure_timebase()
        # every window's mean poll period is below the nominal 500 ms, so the per-poll overhead
        # that assumption A1 bounds is not consumed on average
        for name, w in tb["windows"].items():
            self.assertLess(w["mean_poll_period_ms"], tb["nominal_poll_period_ms"], name)
        self.assertLess(tb["mean_overhead_consumed_ms"], 0.0)
        # the MCU/host ratio is stable across two sessions and two window lengths
        lo, hi = tb["mcu_per_host_range"]
        self.assertAlmostEqual(lo, 1.002, places=2)
        self.assertAlmostEqual(hi, 1.002, places=2)
        self.assertLess(hi - lo, 0.001)
        # the long window uses the monotonic clock, so its period carries no granularity error
        self.assertEqual(tb["windows"]["observation_605s"]["clock"], "monotonic")
        self.assertEqual(tb["windows"]["observation_605s"]["period_uncertainty_ms"], 0.0)
        self.assertEqual(tb["windows"]["observation_605s"]["polls"], 1200)

    def test_report_is_written(self):
        out = Path(__file__).resolve().parent / "results" / "_test_report.json"
        try:
            code = cft.main(["--output", str(out)])
            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["total_issues"], 0)
            self.assertEqual(data["primary_campaign"]["bound_check"]["unresolved"], 1)
        finally:
            if out.exists():
                out.unlink()


if __name__ == "__main__":
    unittest.main()
