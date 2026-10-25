"""Independent targeted scientific/replay challenges; no release approval.

Run: .venv/bin/python -B research/quantum_oracle/evidence/review-probes.py
Historical failing observations were reported to the implementer; these checks
remain runnable against the current code without pinning provisional sources.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.quantum_oracle import discovery as d, quantum as q, run, spaces as s


class IndependentChallenges(unittest.TestCase):
    def test_missing_execution_evidence_cannot_pass_replay(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            committed = root / "scientific-reference/committed/1"
            committed.mkdir(parents=True)
            (root / "result.json").write_text(json.dumps({"status": "SUCCEEDED", "epoch": 1}))
            (committed / "verification.json").write_text(json.dumps({"source_files": {}, "outputs": {}, "environment": {}}))
            (committed / "discovery.json").write_text(json.dumps(d.run_affine_cycle()))
            self.assertFalse((committed / "tests.log").exists())
            with self.assertRaises(ValueError):
                run.replay_run(root)

    def test_bad_nested_vector_rejects_before_numeric_allocation(self):
        original = np.asarray
        seen = []
        def record(values, *args, **kwargs):
            value = original(values, *args, **kwargs)
            seen.append(value.shape)
            return value
        with patch.object(q.np, "asarray", record):
            with self.assertRaises((TypeError, ValueError)):
                q.StateVector([list(range(10000)), list(range(10000))], q.Basis(1))
        self.assertEqual(seen, [], "invalid nested vector allocated before dimensional refusal")

    def test_report_cannot_mutate_source_trust_registry(self):
        report = d.run_affine_cycle()
        saved = d.PINS["kernel.py"]
        try:
            report["source_pins"]["kernel.py"] = "0" * 64
            self.assertEqual(d.PINS["kernel.py"], saved)
        finally:
            d.PINS["kernel.py"] = saved

    def test_collapsed_coordinates_reject(self):
        with self.assertRaises(ValueError):
            s.LocalDomain((1, 1), origin=(1e20, 0))

    def test_hilbert_qubits_remain_integer_typed(self):
        with self.assertRaises(ValueError):
            s.HilbertState([1, 0], [(0, 0), (1, 0)], 1.0)

    def test_self_bures_distance_for_tolerance_admitted_states(self):
        basis = q.Basis(1)
        states = [q.StateVector([np.sqrt(1 - 5e-11), 0], basis),
                  q.DensityMatrix([[1 - 5e-11, 0], [0, 0]], basis)]
        for state in states:
            self.assertLess(q.bures_distance(state, state), 1e-12)
            self.assertAlmostEqual(q.state_fidelity(state, state), 1, delta=1e-12)

    @staticmethod
    def law():
        return s.CoupledScalars(("a", "b", "c"), (0, 0, 0), [
            [0, .5321756460038671, .7317708996172232],
            [.5321756460038671, 0, .916808874769635],
            [.7317708996172232, .916808874769635, 0]])

    def test_constant_graph_displacement_has_zero_energy(self):
        self.assertEqual(self.law().energy([1e50] * 3, [0] * 3), 0)

    def test_structural_graph_zero_mode_does_not_drift(self):
        positions, velocities = self.law().evolve([1] * 3, [0] * 3, 1e6)
        np.testing.assert_allclose(positions, [1] * 3, atol=1e-12, rtol=0)
        np.testing.assert_allclose(velocities, [0] * 3, atol=1e-12, rtol=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
