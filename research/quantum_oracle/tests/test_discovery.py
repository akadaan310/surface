import copy
import unittest

from research.quantum_oracle import discovery as d


class DiscoveryTests(unittest.TestCase):
    def test_rejects_skipped_phases_and_admission_without_challenge(self):
        cycle = d.Cycle("fixture", {"width": 4})
        with self.assertRaises(ValueError):
            cycle.advance("ACCEPT", {})
        with self.assertRaises(ValueError):
            cycle.advance("EXECUTE", {})

    def test_preserves_caller_data_and_detects_chain_tamper(self):
        payload = {"width": 4}
        cycle = d.Cycle("fixture", payload)
        payload["width"] = 1000
        self.assertEqual(cycle.events[0]["payload"]["width"], 4)
        cycle.advance("ACQUIRE", {"fixture": "controlled integer truth table"})
        self.assertTrue(d.verify_events(cycle.events))
        forged = copy.deepcopy(cycle.events)
        forged[0]["payload"]["width"] = 3
        with self.assertRaises(ValueError):
            d.verify_events(forged)

    def test_finite_discovery_replays_and_preserves_failures(self):
        report = d.run_affine_cycle()
        self.assertEqual(report["decision"], "ACCEPT")
        self.assertEqual(report["challenge"]["checked"], 16)
        self.assertEqual(report["challenge"]["held_out"], 12)
        self.assertGreater(len(report["search"]["rejected_candidates"]), 0)
        self.assertEqual(report["events"][-1]["state"], "SELECT NEXT")
        self.assertTrue(d.replay(report))
        self.assertFalse(report["physical_evidence"])
        self.assertEqual(report["challenge"]["basis_permutation"]["dimension"], 16)

    def test_exhaustion_is_unknown_and_wrong_candidate_is_rejected(self):
        report = d.run_affine_cycle(max_candidates=1)
        self.assertEqual(report["decision"], "UNKNOWN")
        self.assertTrue(d.replay(report))
        bad = d.challenge_operations([], width=4, train=(0, 1, 2, 3))
        self.assertEqual(bad["decision"], "REJECT")
        self.assertTrue(bad["counterexamples"])

    def test_replay_checks_computation_not_only_updated_hashes(self):
        report = d.run_affine_cycle()
        report["challenge"]["checked"] = 999
        with self.assertRaises(ValueError):
            d.replay(report)

    def test_report_cannot_mutate_trusted_source_pins(self):
        report = d.run_affine_cycle()
        original = dict(d.PINS)
        try:
            report["source_pins"]["kernel.py"] = "0" * 64
            self.assertEqual(dict(d.PINS), original)
        finally:
            if isinstance(d.PINS, dict):
                d.PINS.update(original)

    def test_resource_and_type_rejection(self):
        for kw in ({"width": 10}, {"width": True}, {"max_candidates": 0},
                   {"max_candidates": 1000000}):
            with self.assertRaises(ValueError):
                d.run_affine_cycle(**kw)
        with self.assertRaises(ValueError):
            d.challenge_operations([{"op": "EVAL", "operand": 1}], width=4, train=(0,))


if __name__ == "__main__":
    unittest.main()
