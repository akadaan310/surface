"""Bounded quantum admission and differential scientific controls.

The scalar loop oracles below do not call production linear algebra helpers.
"""
import copy
import importlib.util
import math
from pathlib import Path
import struct
import unittest
import warnings

import numpy as np
from scipy.linalg import expm

try:
    from research.quantum_oracle import quantum as q
except ImportError:
    q = None


def scalar_apply(matrix, vector):
    return [sum(complex(a) * complex(b) for a, b in zip(row, vector)) for row in matrix]


def scalar_channel(kraus, rho):
    d = len(rho)
    return [[sum(k[i][a] * rho[a][b] * complex(k[j][b]).conjugate()
                 for k in kraus for a in range(d) for b in range(d))
             for j in range(d)] for i in range(d)]


class QuantumTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(q, "versioned validating quantum adapter is missing")
        self.b = q.Basis(1)
        self.zero = q.StateVector([1, 0], self.b)
        self.one = q.StateVector([0, 1], self.b)
        self.plus = q.StateVector([1 / math.sqrt(2)] * 2, self.b)

    def test_reject_non_power_shape_nonfinite_and_unnormalized_states(self):
        for values in ([1, 0, 0], [[1, 0]], [2, 0], [0, 0], [math.nan, 0], [math.inf, 0]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                q.StateVector(values, self.b)
        with self.assertRaises(TypeError):
            q.probabilities([2, 0])

    def test_nested_payload_is_rejected_before_array_coercion(self):
        class NestedPayload(list):
            def __array__(self, *args, **kwargs):
                raise AssertionError("attempted array allocation before depth validation")
        nested = NestedPayload(range(10000))
        with self.assertRaises(ValueError):
            q.StateVector([nested, nested], self.b)
        with self.assertRaises(ValueError):
            q.DensityMatrix([[nested, nested], [nested, nested]], self.b)

    def test_address_spaces_and_basis_admission_are_distinct(self):
        for count in (0, 5, True, 1.5):
            with self.assertRaises((ValueError, TypeError)):
                q.Basis(count)
        with self.assertRaises(ValueError):
            q.Basis(2, "unspecified")
        word = q.ClassicalWord(1, 2)
        b = q.Basis(2)
        np.testing.assert_array_equal(q.basis_lift(word, b).data, [0, 1, 0, 0])
        with self.assertRaises(TypeError):
            q.basis_lift(q.BasisIndex(1, b), b)
        with self.assertRaises(TypeError):
            q.gate("X", b, q.ByteOffset(0))
        with self.assertRaises(ValueError):
            q.ClassicalWord(4, 2)
        with self.assertRaises(ValueError):
            q.LogicalQubit(2, b)
        hardware = q.HardwareQubit("fixture-provider", "fixture-device", "site-0", "snapshot-1")
        self.assertNotEqual(hardware, q.ByteOffset(0))

    def test_lsb_msb_conversion_preserves_logical_qubits(self):
        lsb, msb = q.Basis(2), q.Basis(2, "qubit_0_msb")
        initial = q.basis_lift(q.ClassicalWord(0, 2), lsb)
        l = q.gate("X", lsb, q.LogicalQubit(0, lsb)).apply(initial)
        m = q.rebase(l, msb)
        np.testing.assert_array_equal(l.data, [0, 1, 0, 0])
        np.testing.assert_array_equal(m.data, [0, 0, 1, 0])
        np.testing.assert_array_equal(q.rebase(m, lsb).data, l.data)
        with self.assertRaises(ValueError):
            q.gate("X", msb, q.LogicalQubit(0, msb)).apply(l)
        np.testing.assert_array_equal(q.rebase(q.density(l), msb).data, q.density(m).data)

    def test_state_copy_cannot_bypass_admission(self):
        source = np.array([1, 0], complex)
        state = q.StateVector(source, self.b)
        source[0] = 9
        view = state.data
        view[0] = 8
        np.testing.assert_array_equal(state.data, [1, 0])

    def test_binary_roundtrip_preserves_signed_zero_and_metadata(self):
        original = q.StateVector([complex(1, -0.0), complex(-0.0, 0.0)], self.b)
        encoded = q.encode_state(original)
        decoded = q.decode_state(encoded)
        self.assertEqual(decoded.data.tobytes(), original.data.tobytes())
        for field, value in (("schema", "foreign/0"), ("basis", {"qubits": 1, "order": "qubit_0_msb"}),
                             ("shape", [3]), ("dtype", ">c16"), ("data_hex", "00")):
            changed = copy.deepcopy(encoded)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                q.decode_state(changed)

    def test_seed_adapter_matches_valid_seed_and_rejects_metadata_weakness(self):
        path = Path(__file__).resolve().parents[3] / "build/foundation/QUANTUM_ORACLE_V3_EXTENSION/atlas_quantum/core.py"
        self.assertTrue(path.is_file(), "materialize immutable foundation before scientific conformance")
        spec = importlib.util.spec_from_file_location("untouched_v3_seed", path)
        seed = importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name] = seed
        spec.loader.exec_module(seed)
        state = seed.hadamard(seed.basis_lift(1, 2), 1)
        record = seed.complex_pairs(state)
        admitted = q.admit_v3_seed(record)
        np.testing.assert_array_equal(admitted.data, state)
        np.testing.assert_allclose(q.probabilities(admitted).data, seed.measure_distribution(state), atol=1e-15)
        record["basis_order"] = "qubit_0_msb"
        with self.assertRaises(ValueError):
            q.admit_v3_seed(record)
        bad = seed.complex_pairs(np.array([1, 1, 1]) / math.sqrt(3))
        with self.assertRaises(ValueError):
            q.admit_v3_seed(bad)

    def test_density_checks_hermiticity_trace_positivity_and_dimension(self):
        for matrix in ([[1, 1], [0, 0]], [[2, 0], [0, 0]], [[1.1, 0], [0, -.1]],
                       [[math.nan, 0], [0, 1]], [[1, 0, 0], [0, 0, 0]]):
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                q.DensityMatrix(matrix, self.b)
        np.testing.assert_allclose(q.density(self.plus).data, [[.5, .5], [.5, .5]], atol=1e-15)

    def test_probability_equality_is_not_quantum_state_equivalence(self):
        minus = q.StateVector([1 / math.sqrt(2), -1 / math.sqrt(2)], self.b)
        np.testing.assert_array_equal(q.probabilities(self.plus).data, q.probabilities(minus).data)
        self.assertAlmostEqual(q.fubini_study(self.plus, minus), math.pi / 2)
        mixed = q.diagonal_density(q.probabilities(self.plus))
        self.assertAlmostEqual(q.purity(mixed), .5)
        self.assertAlmostEqual(q.purity(q.density(self.plus)), 1)
        self.assertAlmostEqual(q.trace_distance(q.density(self.plus), mixed), .5)

    def test_global_phase_metric_is_stable_and_relative_phase_is_detected(self):
        rng = np.random.default_rng(913)
        b = q.Basis(4)
        for _ in range(12):
            a = rng.normal(size=16) + 1j * rng.normal(size=16)
            a /= np.linalg.norm(a)
            p = q.StateVector(a, b)
            phased = q.StateVector(a * np.exp(1j * rng.uniform(-math.pi, math.pi)), b)
            self.assertLess(q.fubini_study(p, phased), 2e-15)
        epsilon = 1e-7
        near = q.StateVector([math.cos(epsilon), math.sin(epsilon)], self.b)
        self.assertAlmostEqual(q.fubini_study(self.zero, near), epsilon, delta=1e-15)

    def test_density_metrics_analytic_and_triangle_controls(self):
        mixed = q.DensityMatrix(np.eye(2) / 2, self.b)
        self.assertAlmostEqual(q.state_fidelity(self.zero, self.one), 0)
        self.assertAlmostEqual(q.trace_distance(self.zero, self.one), 1)
        self.assertAlmostEqual(q.state_fidelity(self.zero, mixed), .5)
        self.assertAlmostEqual(q.bures_distance(self.zero, mixed), math.sqrt(2 - math.sqrt(2)))
        self.assertLessEqual(q.trace_distance(self.zero, self.one),
                             q.trace_distance(self.zero, self.plus) + q.trace_distance(self.plus, self.one) + 1e-14)
        self.assertAlmostEqual(q.state_fidelity(mixed, mixed), 1, places=12)

    def test_metrics_use_normalized_representatives_without_altering_admitted_bytes(self):
        for residual in (-5e-11, 5e-11):
            for state in (q.StateVector([math.sqrt(1 + residual), 0], self.b),
                          q.DensityMatrix([[1 + residual, 0], [0, 0]], self.b)):
                before = state.data.tobytes()
                with self.subTest(residual=residual, kind=type(state).__name__):
                    self.assertAlmostEqual(q.state_fidelity(state, state), 1, delta=1e-14)
                    self.assertLess(q.bures_distance(state, state), 1e-14)
                    self.assertLess(q.bures_distance(state, self.zero), 1e-14)
                    self.assertLess(q.trace_distance(state, self.zero), 1e-14)
                    self.assertEqual(state.data.tobytes(), before)

    def test_bures_near_equal_rays_retains_small_separations(self):
        epsilon = 1e-7
        near = q.StateVector([math.cos(epsilon), math.sin(epsilon)], self.b)
        self.assertAlmostEqual(q.bures_distance(self.zero, near), 2 * math.sin(epsilon / 2), delta=1e-15)
        mixed = q.DensityMatrix([[.6, .1j], [-.1j, .4]], self.b)
        self.assertLess(q.bures_distance(mixed, mixed), 1e-14)

    def test_unitary_rejects_stochastic_maps_and_nonfinite_operators(self):
        for bad in ([[1, 1], [0, 0]], [[1, 0], [0, 2]], [[math.inf, 0], [0, 1]]):
            with self.assertRaises(ValueError):
                q.Unitary(bad, self.b)
        with self.assertRaises(TypeError):
            q.Unitary(np.eye(2), self.b).apply(q.probabilities(self.zero))

    def test_all_one_qubit_gates_match_scalar_and_inverses(self):
        for name in ("I", "X", "Y", "Z", "H", "S", "T", "RX", "RY", "RZ"):
            angle = .37 if name.startswith("R") else None
            operation = q.gate(name, self.b, q.LogicalQubit(0, self.b), angle=angle)
            phase_state = q.StateVector([math.sqrt(.3), 1j * math.sqrt(.7)], self.b)
            got = operation.apply(phase_state)
            np.testing.assert_allclose(got.data, scalar_apply(operation.data.tolist(), phase_state.data.tolist()), atol=1e-14)
            np.testing.assert_allclose(operation.adjoint().apply(got).data, phase_state.data, atol=1e-14)
        with self.assertRaises(ValueError):
            q.gate("RX", self.b, q.LogicalQubit(0, self.b), angle=math.inf)

    def test_bell_controlled_gates_and_circuit_resource_bound(self):
        b = q.Basis(2)
        zero = q.basis_lift(q.ClassicalWord(0, 2), b)
        ops = [q.gate("H", b, q.LogicalQubit(0, b)), q.controlled_x(q.LogicalQubit(0, b), q.LogicalQubit(1, b))]
        bell = q.run_circuit(zero, ops)
        np.testing.assert_allclose(bell.data, [1 / math.sqrt(2), 0, 0, 1 / math.sqrt(2)], atol=1e-15)
        with self.assertRaises(ValueError):
            q.run_circuit(zero, [ops[0]] * 257)
        with self.assertRaises(ValueError):
            q.controlled_x(q.LogicalQubit(0, b), q.LogicalQubit(0, b))

    def test_closed_dynamics_matches_scipy_exponential_and_pauli_analytic(self):
        h = q.Hamiltonian([[0, 1], [1, 0]], self.b, "rad/s")
        time = .31
        got = q.evolve_closed(self.zero, h, time)
        np.testing.assert_allclose(got.data, [math.cos(time), -1j * math.sin(time)], atol=1e-14)
        np.testing.assert_allclose(got.data, expm(-1j * h.data * time) @ self.zero.data, atol=1e-14)
        rho = q.evolve_closed(q.density(self.zero), h, time)
        np.testing.assert_allclose(rho.data, q.density(got).data, atol=1e-14)
        for invalid in (math.inf, math.nan, 1e10):
            with self.assertRaises(ValueError):
                q.evolve_closed(self.zero, h, invalid)
        with self.assertRaises(ValueError):
            q.Hamiltonian(np.eye(2), self.b, "J")

    def test_noncommuting_hamiltonian_crosscheck_and_time_reversal(self):
        b = q.Basis(2)
        hdata = np.array([[.1, .2j, .3, 0], [-.2j, -.7, .1, .4], [.3, .1, .9, -.2j], [0, .4, .2j, -.3]])
        h = q.Hamiltonian(hdata, b, "rad/s")
        p = q.StateVector([.5, .5j, -.5, -.5j], b)
        got = q.evolve_closed(p, h, .83)
        np.testing.assert_allclose(got.data, expm(-1j * hdata * .83) @ p.data, atol=2e-14)
        np.testing.assert_allclose(q.evolve_closed(got, h, -.83).data, p.data, atol=2e-14)

    def test_observable_expectation_and_variance_do_not_replace_state(self):
        z = q.Observable([[1, 0], [0, -1]], self.b, "dimensionless")
        self.assertAlmostEqual(q.expectation(self.zero, z), 1)
        self.assertAlmostEqual(q.expectation(self.plus, z), 0)
        self.assertAlmostEqual(q.variance(self.plus, z), 1)
        with self.assertRaises(ValueError):
            q.Observable([[0, 1], [0, 0]], self.b, "dimensionless")

    def test_kraus_channel_cptp_admission_and_amplitude_damping(self):
        gamma = .3
        kraus = [np.diag([1, math.sqrt(1 - gamma)]), np.array([[0, math.sqrt(gamma)], [0, 0]])]
        channel = q.QuantumChannel(kraus, self.b)
        rho = q.density(self.plus)
        got = channel.apply(rho)
        expected = [[.65, math.sqrt(.7) / 2], [math.sqrt(.7) / 2, .35]]
        np.testing.assert_allclose(got.data, expected, atol=1e-15)
        np.testing.assert_allclose(got.data, scalar_channel([k.tolist() for k in kraus], rho.data.tolist()), atol=1e-15)
        self.assertAlmostEqual(np.trace(got.data).real, 1)
        self.assertGreaterEqual(float(np.linalg.eigvalsh(got.data).min()), 0)
        for bad in ([], [np.eye(2) * 2], [np.eye(3)], [np.eye(2) / math.sqrt(17)] * 17):
            with self.assertRaises(ValueError):
                q.QuantumChannel(bad, self.b)
        with self.assertRaises(TypeError):
            channel.apply(self.plus)

    def test_channel_choi_is_positive_and_trace_preserving(self):
        channel = q.QuantumChannel([np.eye(2) / math.sqrt(2), np.diag([1, -1]) / math.sqrt(2)], self.b)
        choi = channel.choi()
        self.assertGreaterEqual(float(np.linalg.eigvalsh(choi).min()), -1e-13)
        # Independent Choi block convention J[(a,i),(b,j)] = Phi(|a><b|)[i,j].
        np.testing.assert_allclose(np.trace(choi.reshape(2, 2, 2, 2), axis1=1, axis2=3), np.eye(2), atol=1e-14)
        np.testing.assert_allclose(channel.apply(q.density(self.plus)).data, np.eye(2) / 2, atol=1e-14)

    def test_stochastic_and_quantum_channels_are_distinct(self):
        transition = q.StochasticMap([[1, .3], [0, .7]], self.b)
        got = transition.apply(q.probabilities(self.one))
        np.testing.assert_allclose(got.data, [.3, .7], atol=1e-15)
        np.testing.assert_allclose(q.diagonal_density(got).data, [[.3, 0], [0, .7]])
        with self.assertRaises(TypeError):
            transition.apply(self.plus)
        with self.assertRaises(ValueError):
            q.StochasticMap([[1, 0], [.3, .7]], self.b)
        with self.assertRaises(ValueError):
            q.ProbabilityDistribution([1.1, -.1], self.b)

    def test_seeded_measurements_have_counts_and_explicit_loss(self):
        first = q.measure(self.plus, shots=2000, seed=77)
        second = q.measure(self.plus, shots=2000, seed=77)
        self.assertEqual(first.counts, second.counts)
        self.assertEqual(sum(first.counts), 2000)
        self.assertLess(abs(first.counts[0] / 2000 - .5), .05)
        self.assertTrue(first.information_loss)
        self.assertEqual(first.preparation, "independent_identically_prepared")
        self.assertEqual(q.measure(self.zero, shots=100, seed=1).counts, (100, 0))
        for shots in (-1, 100001, True, 1.5):
            with self.assertRaises((TypeError, ValueError)):
                q.measure(self.plus, shots=shots, seed=1)

    def test_projective_postselection_records_probability_and_collapse(self):
        outcome = q.project_measurement(self.plus, q.BasisIndex(1, self.b))
        self.assertAlmostEqual(outcome.probability, .5)
        np.testing.assert_array_equal(outcome.post_state.data, [[0, 0], [0, 1]])
        self.assertTrue(outcome.information_loss)
        with self.assertRaises(ValueError):
            q.project_measurement(self.zero, q.BasisIndex(1, self.b))

    def test_direct_measurement_record_construction_cannot_forge_counts_or_loss(self):
        p = q.probabilities(self.plus)
        for counts, shots, loss in (((4, -1), 3, True), ((3, 0), 2, True), ((1, 1), 2, False)):
            with self.subTest(counts=counts, loss=loss), self.assertRaises(ValueError):
                q.MeasurementRecord(self.b, p, counts, shots, 7, information_loss=loss)
        with self.assertRaises((TypeError, ValueError)):
            q.MeasurementRecord(self.b, p, [1, 1], 2, 7)

    def test_direct_postselection_record_rejects_wrong_collapse(self):
        with self.assertRaises(ValueError):
            q.MeasurementOutcome(q.BasisIndex(0, self.b), .5, q.density(self.one))
        with self.assertRaises(ValueError):
            q.MeasurementOutcome(q.BasisIndex(0, self.b), math.nan, q.density(self.zero))

    def test_resigned_codec_cannot_coerce_float_dimensions(self):
        import hashlib
        import json
        record = q.encode_state(self.zero)
        record["shape"] = [2.0]
        unsigned = {k: v for k, v in record.items() if k != "interpretation_sha256"}
        record["interpretation_sha256"] = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with self.assertRaises(ValueError):
            q.decode_state(record)

    def test_extreme_stochastic_values_reject_before_overflow(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            with self.assertRaises(ValueError):
                q.StochasticMap([[1e308, 1e308], [1e308, 1e308]], self.b)

    def test_original_oracle_gate_conformance_with_explicit_msb_basis(self):
        path = Path(__file__).resolve().parents[3] / "build/foundation/quantum_oracle/quantum_oracle/core.py"
        self.assertTrue(path.is_file(), "materialize immutable Oracle before conformance")
        spec = importlib.util.spec_from_file_location("untouched_original_oracle", path)
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)
        basis = q.Basis(3, "qubit_0_msb")
        for name in ("I", "X", "Y", "Z", "H", "S", "T", "RX", "RZ"):
            for target in range(3):
                theta = .71 if name.startswith("R") else None
                ours = q.gate(name, basis, q.LogicalQubit(target, basis), angle=theta)
                original = oracle.gate({"gate": name, "target": target, "theta": theta}, 3)
                np.testing.assert_allclose(ours.data, original, atol=2e-15)
        for control, target in ((0, 2), (2, 0), (1, 2)):
            ours = q.controlled_x(q.LogicalQubit(control, basis), q.LogicalQubit(target, basis))
            np.testing.assert_array_equal(ours.data, oracle.cx(control, target, 3))


if __name__ == "__main__":
    unittest.main()
