import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_frozen_traces as cft  # noqa: E402


class BoundDerivationTests(unittest.TestCase):
    def test_bounds_follow_model_constants(self):
        # DRAFT model, between status reports (SLIP 0) and in every window (SLIP 60)
        self.assertEqual(cft.FIRST_TIMEOUT_BOUND_MS, 603)
        self.assertEqual(cft.OFFLINE_BOUND_MS, 1607)
        self.assertEqual(cft.RECOVERY_BOUND_MS, 516)
        self.assertEqual(cft.STATUS_BOUNDS, {"first_timeout": 663, "offline": 1667, "recovery": 576})

    def test_falsification_floor_exceeds_demonstrated_uncertainty(self):
        """The floor must not be fitted to the data: it has to dominate the demonstrated timestamp noise."""
        observed = cft.check_primary_campaign()["monotonic_tick_disagreement_ms"]["max"]
        self.assertGreater(cft.RESOLUTION_MS, 3 * observed)
        residual = cft.measure_raw_nominal()["host_read_residual_ms"]["max"]
        self.assertGreater(cft.RESOLUTION_MS, 5 * residual)

    def test_delay_boundary_classification(self):
        # DRAFT: accepted for d <= 85; timeout for d >= 100 between status reports, d >= 160 in every window
        self.assertTrue(cft.model_accepts(85) and not cft.model_accepts(86))
        self.assertTrue(cft.model_accepts(50) and not cft.model_times_out(50))
        self.assertFalse(cft.model_accepts(90) or cft.model_times_out(90))
        for d in (100, 110, 150, 250):
            self.assertTrue(cft.model_times_out(d) and not cft.model_accepts(d))
        self.assertFalse(cft.model_times_out(99))
        self.assertFalse(cft.model_times_out(159, cft.SLIP_MS))
        self.assertTrue(cft.model_times_out(160, cft.SLIP_MS))


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
        # One BAD_CRC recovery interval exceeds the SLIP-0 recovery bound (516 ms); it lies inside the
        # bound that holds in every window (576 ms). Reported, not absorbed.
        self.assertEqual(bc["unresolved"], 1)
        self.assertEqual(bc["within_status_bound"], 180)
        only = self.primary["unresolved_intervals"][0]
        self.assertEqual((only["run_id"], only["mode"], only["interval"]), ("R085_P02", "BAD_CRC", "recovery"))
        self.assertLess(only["excess_ms"], cft.RESOLUTION_MS)
        self.assertTrue(only["within_status_bound"])

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
        self.assertEqual(ext["delay_sweep"][100]["verdict"], "CONFORMS")
        self.assertEqual(ext["delay_sweep"][90]["verdict"], "BOUNDARY_UNDETERMINED_CONSISTENT")
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

    def test_status_report_slip_is_measured(self):
        raw = cft.measure_raw_nominal()
        slip, ctrl = raw["status_slip_ms"], raw["control_slip_ms"]
        self.assertGreater(slip["n"], 200)
        self.assertLessEqual(slip["max"], cft.SLIP_MS, "model SLIP must cover every observed slip")
        self.assertGreater(slip["min"], ctrl["max"], "every status slip exceeds every control window")
        self.assertLess(raw["steady_state"]["median_poll_period_host_ms"], 500.0)

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
