"""Independent bounded challenge of the collider/circuit adapters.

These synthetic controls neither rerun the 100,000-row data analysis nor assert
release acceptance. Run from the repository root with .venv/bin/python -B.
"""
from dataclasses import replace
from decimal import Decimal
from itertools import product
import math
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.quantum_oracle import circuits, collider, quantum


class AdapterChallenge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = circuits.load_snapshot()
        basis = quantum.Basis(2)
        cls.ir = circuits.CircuitIR(basis, (
            circuits.CircuitOp("X", (quantum.LogicalQubit(0, basis),)),))
        cls.compiled = circuits.compile_circuit(cls.ir, cls.snapshot, seed=7)

    def test_signed_integer_minimum_cannot_evade_component_bound(self):
        for dtype in (np.int32, np.int64):
            values = np.zeros((1, 2, 4), dtype=dtype)
            values[0, 0, 1] = np.iinfo(dtype).min
            with self.subTest(dtype=dtype), self.assertRaises(collider.ColliderError):
                collider.vectorized_pair_mass_squared(values)
        valid = np.array([[[5, 4, 0, 0], [5, -4, 0, 0]]], dtype=np.int64)
        np.testing.assert_array_equal(collider.vectorized_pair_mass_squared(valid), [100])

    def test_random_boost_invariance_and_inverse(self):
        rng = np.random.default_rng(521)
        for _ in range(1000):
            p = rng.uniform(-100, 100, 3)
            mass = rng.uniform(.1, 10)
            energy = math.sqrt(float(p @ p) + mass * mass)
            beta = rng.normal(size=3)
            beta *= rng.uniform(0, .9) / np.linalg.norm(beta)
            original = collider.FourMomentum(energy, *p)
            boosted = original.boost(tuple(beta))
            returned = boosted.boost(tuple(-beta))
            scale = max(1., sum(v*v for v in original.components)
                        + sum(v*v for v in boosted.components))
            self.assertLessEqual(abs(original.mass_squared()-boosted.mass_squared()),
                                 64*np.finfo(float).eps*scale)
            np.testing.assert_allclose(returned.components, original.components,
                                       atol=1e-10, rtol=0)

    def test_rounding_bound_contains_decimal_corner_values(self):
        rng = np.random.default_rng(134)
        for _ in range(100):
            p = rng.uniform(-100, 100, 3)
            energy = math.sqrt(float(p @ p)+25.)
            widths = tuple(rng.uniform(0, .001, 4))
            vector = collider.FourMomentum(energy, *p, rounding=widths)
            center = Decimal.from_float(vector.mass_squared())
            bound = Decimal.from_float(vector.mass_squared_error())
            for signs in product((-1, 1), repeat=4):
                corner = [Decimal.from_float(v)+sign*Decimal.from_float(d)
                          for v, d, sign in zip(vector.components, widths, signs)]
                exact = corner[0]**2-sum(v*v for v in corner[1:])
                self.assertLessEqual(abs(exact-center), bound)

    def test_snapshot_cannot_relabel_replaced_calibration_as_original(self):
        with self.assertRaises((ValueError, TypeError)):
            forged = replace(self.snapshot, gates=tuple(
                replace(gate, duration_seconds=0., error=1.)
                for gate in self.snapshot.gates))
            compiled = circuits.compile_circuit(self.ir, forged, seed=7)
            circuits.simulate_surrogate(compiled, forged)

    def test_snapshot_future_calibration_rejects(self):
        with self.assertRaises((ValueError, TypeError)):
            replace(self.snapshot, gates=tuple(
                replace(gate, measured_at="2099-01-01T00:00:00+00:00")
                for gate in self.snapshot.gates))

    def test_snapshot_duplicate_edge_expansion_rejects(self):
        with self.assertRaises((ValueError, TypeError)):
            replace(self.snapshot, couplings=self.snapshot.couplings*10000)

    def test_compiled_native_calibration_cannot_be_forged(self):
        with self.assertRaises((ValueError, TypeError)):
            replace(self.compiled,
                    native_operations=tuple(replace(op, duration_seconds=0.,
                                                   reported_gate_error=1.)
                                            for op in self.compiled.native_operations),
                    serial_duration_seconds=0.)

    def test_compiled_unitary_witness_cannot_be_forged(self):
        with self.assertRaises((ValueError, TypeError)):
            replace(self.compiled, logical_unitary=quantum.Unitary(
                np.eye(self.ir.basis.dimension), self.ir.basis))


if __name__ == "__main__":
    unittest.main(verbosity=2)
