"""Finite analytic controls; no numerical solver supplies its own oracle."""
import importlib.util
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


class SpacesTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "research/quantum_oracle/spaces.py"
        self.assertTrue(path.is_file(), "standalone function-spaces contract is missing")
        spec = importlib.util.spec_from_file_location("spaces_contract", path)
        self.s = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.s
        spec.loader.exec_module(self.s)

    def domain(self, **kw):
        defaults = dict(lengths=(2 * math.pi, 2 * math.pi), origin=(0, 0),
                        coordinate_unit="m", boundary="periodic")
        defaults.update(kw)
        return self.s.LocalDomain(**defaults)

    def field(self, coefficients=(0.5, 0.5), **kw):
        space = self.s.FourierSpace(self.domain(), ((-1, 0), (1, 0)))
        return self.s.FourierField(space, coefficients, **kw)

    def test_xy_domain_rejects_wrong_shape_nonfinite_metric_and_boundary(self):
        for kw in [dict(origin=(0, 0, 0)), dict(origin=(0, math.nan)),
                   dict(lengths=(0, 1)), dict(metric=((1, 2), (0, 1))),
                   dict(metric=((1, 0), (0, 0))), dict(boundary="unknown")]:
            with self.subTest(kw=kw), self.assertRaises(self.s.ContractError):
                self.domain(**kw)
        d = self.domain(origin=(2, 3), metric=((4, 0), (0, 9)))
        self.assertAlmostEqual(d.intrinsic_distance((0, 0), (3, 4)), math.sqrt(180))
        self.assertTrue(d.contains((2, 3)))
        self.assertFalse(d.contains((1, 3)))

    def test_affine_transition_preserves_metric_and_inverts(self):
        tr = self.s.AffineTransition(((2, 1), (0, 3)), (4, -2), "m", "m")
        source = np.diag([4., 9.])
        target = tr.target_metric(source)
        points = np.array([[0., 0.], [3., 4.], [-2., 1.]])
        np.testing.assert_allclose(tr.inverse().apply(tr.apply(points)), points, atol=2e-14)
        delta = points[1] - points[0]
        moved = tr.apply(points)[1] - tr.apply(points)[0]
        self.assertAlmostEqual(float(delta @ source @ delta), float(moved @ target @ moved))
        with self.assertRaises(self.s.ContractError):
            self.s.AffineTransition(((1, 0), (0, 0)), (0, 0), "m", "m")
        with self.assertRaises(self.s.ContractError):
            self.s.AffineTransition(((1, 0), (0, 1)), (0, 0), "m", "s")

    def test_scalar_pullback_witness_uses_inverse_coordinates(self):
        field = self.field()
        tr = self.s.AffineTransition(((2, 0), (0, 1)), (5, 0), "m", "m")
        points = np.array([[0.3, 0.7], [1.2, 0.1]])
        view = self.s.CoordinateView(field, tr)
        np.testing.assert_allclose(view.evaluate(tr.apply(points)), np.cos(points[:, 0]), atol=1e-14)
        self.assertEqual(view.loss, "none analytically; binary64 rounding")

    def test_fourier_normalized_measure_parseval_derivative_and_origin(self):
        field = self.field(field_unit="V")
        points = np.array([[0, 0], [math.pi / 2, 0], [math.pi, 0]])
        np.testing.assert_allclose(field.evaluate(points), [1, 0, -1], atol=1e-14)
        np.testing.assert_allclose(field.derivative(0).evaluate(points), [0, -1, 0], atol=1e-14)
        self.assertEqual(field.derivative(0).field_unit, "V/m")
        self.assertAlmostEqual(field.norm(), math.sqrt(0.5))
        self.assertAlmostEqual(field.h1_norm(length_scale=2), math.sqrt(2.5))
        shifted = self.s.FourierField(self.s.FourierSpace(self.domain(origin=(2, 3)),
                                                        ((-1, 0), (1, 0))), (0.5, 0.5))
        self.assertAlmostEqual(shifted.evaluate(((2, 3),))[0].real, 1)

    def test_fourier_spectral_values_roundtrip_without_aliasing(self):
        f = self.field((0.25 + 0.5j, -0.75j))
        samples = f.sample_grid((5, 3))
        restored = self.s.FourierField.from_grid(f.space, samples, f.field_unit)
        np.testing.assert_allclose(restored.coefficients, f.coefficients, atol=1e-14)
        with self.assertRaises(self.s.ContractError):
            f.sample_grid((2, 3))
        contaminated = samples.copy()
        contaminated += 0.1
        with self.assertRaisesRegex(self.s.ContractError, "outside retained"):
            self.s.FourierField.from_grid(f.space, contaminated, f.field_unit)

    def test_squared_amplitude_is_distinct_lossy_observable(self):
        f = self.field((1, 1), field_unit="V")
        view = f.squared_amplitude()
        np.testing.assert_allclose(view.evaluate(((0, 0), (math.pi/2, 0))), [4, 0], atol=1e-14)
        self.assertEqual(view.field_unit, "(V)^2")
        self.assertIn("phase", view.loss)
        with self.assertRaises(self.s.ContractError):
            self.s.hilbert_state(view)

    def test_wave_modes_match_dalembert_and_conserve_energy(self):
        f = self.field(field_unit="m")
        velocity = self.field((0, 0), field_unit="m/s")
        for t in (0, 0.25, 1, 3):
            u, v = self.s.wave_evolve(f, velocity, time=t, speed=2)
            x = np.array([[0.1, 0], [0.7, 0], [2.0, 0]])
            expected = (np.cos(x[:, 0] - 2*t) + np.cos(x[:, 0] + 2*t))/2
            np.testing.assert_allclose(u.evaluate(x), expected, atol=1e-14)
            self.assertAlmostEqual(self.s.wave_energy(u, v, speed=2), 1.0)
        zero_space = self.s.FourierSpace(self.domain(), ((0, 0),))
        zero = self.s.FourierField(zero_space, (2,), "m")
        drift = self.s.FourierField(zero_space, (3,), "m/s")
        u, v = self.s.wave_evolve(zero, drift, time=4, speed=2)
        self.assertAlmostEqual(u.coefficients[0].real, 14)
        self.assertAlmostEqual(v.coefficients[0].real, 3)

    def test_schrodinger_free_modes_match_phase_and_preserve_norm(self):
        space = self.s.FourierSpace(self.domain(), ((0, 0), (2, 0)))
        f = self.s.FourierField(space, (math.sqrt(0.5), 1j*math.sqrt(0.5)))
        evolved = self.s.schrodinger_evolve(f, time=0.3, hbar=2, mass=4)
        expected = [math.sqrt(0.5), 1j*math.sqrt(0.5)*np.exp(-0.3j)]
        np.testing.assert_allclose(evolved.coefficients, expected, atol=1e-14)
        self.assertAlmostEqual(evolved.norm(), 1)
        self.assertAlmostEqual(self.s.schrodinger_energy(f, hbar=2, mass=4), 1)
        back = self.s.schrodinger_evolve(evolved, time=-0.3, hbar=2, mass=4)
        np.testing.assert_allclose(back.coefficients, f.coefficients, atol=1e-14)

    def test_hilbert_map_checks_admissibility_without_renormalization(self):
        f = self.field((1/math.sqrt(2), 1j/math.sqrt(2)))
        state = self.s.hilbert_state(f, require_qubits=True)
        np.testing.assert_array_equal(state.amplitudes, f.coefficients)
        self.assertEqual(state.basis_modes, ((-1, 0), (1, 0)))
        self.assertEqual(state.qubits, 1)
        with self.assertRaisesRegex(self.s.ContractError, "normalized"):
            self.s.hilbert_state(self.field())
        with self.assertRaisesRegex(self.s.ContractError, "dimensionless"):
            self.s.hilbert_state(self.field((1, 0), field_unit="V"))
        three = self.s.FourierField(self.s.FourierSpace(self.domain(),
                                  ((-1, 0), (0, 0), (1, 0))), (0, 1, 0))
        self.assertIsNone(self.s.hilbert_state(three).qubits)
        with self.assertRaises(self.s.ContractError):
            self.s.hilbert_state(three, require_qubits=True)

    def test_coupled_two_modes_match_closed_form_and_layout_is_irrelevant(self):
        a = self.s.Chart("a", self.domain(), self.s.LayoutPoint((0, 0), "px"))
        b = self.s.Chart("b", self.domain(), self.s.LayoutPoint((3, 4), "px"))
        atlas = self.s.Atlas((a, b))
        law = self.s.CoupledScalars(("a", "b"), (1, 1), ((0, 2), (2, 0)))
        self.assertEqual(atlas.layout_distance("a", "b"), 5)
        for t in (0, .2, 1, 3):
            q, v = law.evolve((1, 0), (0, 0), t)
            expected = [(math.cos(t)+math.cos(math.sqrt(5)*t))/2,
                        (math.cos(t)-math.cos(math.sqrt(5)*t))/2]
            np.testing.assert_allclose(q, expected, atol=2e-14)
            self.assertAlmostEqual(law.energy(q, v), 1.5)
        changed = self.s.Atlas((a, self.s.Chart("b", self.domain(),
                                              self.s.LayoutPoint((3000, -4000), "px"))))
        np.testing.assert_array_equal(law.evolve((1, 0), (0, 0), 1)[0],
                                      changed.evolve(law, (1, 0), (0, 0), 1)[0])
        self.assertEqual(law.edge_kind, "simulated")
        self.assertEqual(law.boundary, "closed finite graph")

    def test_uncoupled_null_control_and_bad_laws(self):
        law = self.s.CoupledScalars(("a", "b"), (1, 4), ((0, 0), (0, 0)))
        q, _ = law.evolve((1, 0), (0, 0), .7)
        np.testing.assert_allclose(q, [math.cos(.7), 0], atol=1e-14)
        for c in [((0, 1), (0, 0)), ((0, -1), (-1, 0)), ((1, 0), (0, 0))]:
            with self.assertRaises(self.s.ContractError):
                self.s.CoupledScalars(("a", "b"), (1, 1), c)
        with self.assertRaises(self.s.ContractError):
            law.evolve((1, 0), (0, 0), math.inf)

    def test_resource_shape_unit_and_mutation_controls(self):
        with self.assertRaisesRegex(self.s.ContractError, "limit"):
            self.s.FourierSpace(self.domain(), tuple((i, 0) for i in range(257)))
        with self.assertRaises(self.s.ContractError):
            self.s.FourierSpace(self.domain(), ((1.5, 0),))
        with self.assertRaises(self.s.ContractError):
            self.s.FourierSpace(self.domain(boundary="closed"), ((1, 0),))
        with self.assertRaises(self.s.ContractError):
            self.field((math.nan, 0))
        f = self.field()
        with self.assertRaises(ValueError):
            f.coefficients[0] = 99
        with self.assertRaises(ValueError):
            f.coefficients.setflags(write=True)
        with self.assertRaises(self.s.ContractError):
            f.evaluate(np.zeros((4097, 2)))
        with self.assertRaises(self.s.ContractError):
            self.s.wave_evolve(f, self.field(), time=1, speed=1)
        with self.assertRaises(self.s.ContractError):
            self.s.schrodinger_evolve(f, time=1, mass=0)
        with self.assertRaises(self.s.ContractError):
            self.s.Atlas(())
        with self.assertRaises(self.s.ContractError):
            self.s.LayoutPoint((0, math.nan), "px")

    def test_immutable_seed_compatible_views_and_corrected_squared_scale(self):
        seed_path = ROOT / "build/foundation/QUANTUM_ORACLE_V3_EXTENSION/atlas_quantum/core.py"
        self.assertTrue(seed_path.is_file(), "materialize immutable foundation first")
        spec = importlib.util.spec_from_file_location("spaces_seed_control", seed_path)
        seed = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = seed
        spec.loader.exec_module(seed)
        x = np.linspace(-2, 2, 17)
        for operation in ("sine", "derivative"):
            atlas = seed.Atlas([seed.Chart("x", (0, 0), "m", operation, .2, 2)])
            np.testing.assert_allclose(self.s.seed_wave_view(operation, x, time=.3, k=2,
                                       omega=3, phase=.2, amplitude=2),
                                       atlas.wave("x", x, t=.3, k=2, omega=3), atol=1e-14)
        self.assertAlmostEqual(self.s.seed_wave_view("squared_amplitude", [math.pi/2],
                                                     amplitude=2)[0], 4)
        with self.assertRaises(self.s.ContractError):
            self.s.seed_wave_view("energy", [0])

    def test_real_contracts_reject_complex_boolean_and_rank_zero_arrays(self):
        for origin in [(1j, 0), (True, 0), np.array([1+0j, 0])]:
            with self.subTest(origin=origin), self.assertRaises(self.s.ContractError):
                self.domain(origin=origin)
        for call in [lambda: self.field().evaluate(np.array(1)),
                     lambda: self.s.seed_wave_view("sine", np.array(1)),
                     lambda: self.s.SquaredAmplitude("field"),
                     lambda: self.s.hilbert_state(self.field((1, 0)), require_qubits="yes"),
                     lambda: self.s.HilbertState((2, 0), ((-1, 0), (1, 0)), 1)]:
            with self.subTest(call=call), self.assertRaises(self.s.ContractError):
                call()

    def test_numeric_overflow_is_typed_rejection_not_infinity(self):
        f = self.field((1e100, 1e100))
        velocity = self.field((0, 0), field_unit="1/s")
        for call in [lambda: f.h1_norm(1e100),
                     lambda: self.s.wave_energy(f, velocity, speed=1e100),
                     lambda: self.s.schrodinger_energy(f, hbar=1e100, mass=1e-100)]:
            with self.subTest(call=call), self.assertRaises(self.s.ContractError):
                call()

    def test_affine_computed_metric_is_symmetric_with_rounding(self):
        tr = self.s.AffineTransition(((1.234, 5.678), (2.345, 9.012)), (.2, -.3), "m", "m")
        g = ((2, .3), (.3, 1))
        target = tr.target_metric(g)
        np.testing.assert_array_equal(target, target.T)
        a = np.asarray(tr.matrix)
        np.testing.assert_allclose(a.T @ target @ a, g, atol=3e-13)

    def test_intrinsic_metric_changes_evolution_but_layout_does_not(self):
        space = self.s.FourierSpace(self.domain(metric=((4, 0), (0, 1))), ((-1, 0), (1, 0)))
        f = self.s.FourierField(space, (.5, .5), "m")
        v = self.s.FourierField(space, (0, 0), "m/s")
        u, _ = self.s.wave_evolve(f, v, time=.7, speed=2)
        self.assertAlmostEqual(u.evaluate(((0, 0),))[0].real, math.cos(.7))
        self.assertAlmostEqual(self.s.wave_energy(f, v, speed=2), .25)

    def test_chart_field_binding_preserves_domain_and_observable_type(self):
        field = self.field()
        chart = self.s.Chart("f", field.space.domain, self.s.LayoutPoint((0, 0), "px"), field)
        self.assertIs(chart.field, field)
        view = field.squared_amplitude()
        observable = self.s.Chart("obs", field.space.domain, self.s.LayoutPoint((1, 0), "px"), view)
        self.assertIs(observable.field, view)
        with self.assertRaises(self.s.ContractError):
            self.s.Chart("bad", self.domain(origin=(1, 0)), chart.layout, field)
        with self.assertRaises(self.s.ContractError):
            self.s.Chart("bad", field.space.domain, chart.layout, "wave")
        with self.assertRaises(self.s.ContractError):
            self.s.HilbertState((1, 0), ((-1, 0), (1, 0)), 1.0)

    def test_coordinate_resolution_rejects_collapsed_domain_and_samples_locally(self):
        with self.assertRaisesRegex(self.s.ContractError, "resolution"):
            self.domain(lengths=(1, 1), origin=(1e20, 0))
        space = self.s.FourierSpace(self.domain(lengths=(1, 1), origin=(1e6, 0)), ((1, 0),))
        field = self.s.FourierField(space, (1,))
        values = field.sample_grid((3, 1))
        np.testing.assert_allclose(values[:, 0], [1, -.5+1j*math.sqrt(3)/2,
                                                 -.5-1j*math.sqrt(3)/2], atol=1e-14)
        restored = self.s.FourierField.from_grid(space, values)
        np.testing.assert_allclose(restored.coefficients, [1], atol=1e-14)

    def test_graph_constant_mode_is_exact_structural_nullspace(self):
        c = ((0, .5321756460038671, .7317708996172232),
             (.5321756460038671, 0, .916808874769635),
             (.7317708996172232, .916808874769635, 0))
        law = self.s.CoupledScalars(("a", "b", "c"), (0, 0, 0), c)
        with self.subTest(control="nonnegative edge energy"):
            self.assertEqual(law.energy((1e50, 1e50, 1e50), (0, 0, 0)), 0)
        q, v = law.evolve((1, 1, 1), (0, 0, 0), 1e6)
        with self.subTest(control="structural constant mode"):
            np.testing.assert_array_equal(q, [1, 1, 1])
            np.testing.assert_array_equal(v, [0, 0, 0])
        drift, velocity = law.evolve((1, 1, 1), (2, 2, 2), 1e6)
        np.testing.assert_array_equal(drift, [2000001, 2000001, 2000001])
        np.testing.assert_array_equal(velocity, [2, 2, 2])
        disconnected = self.s.CoupledScalars(("a", "b", "c"), (0, 0, 0),
                                            ((0, 1, 0), (1, 0, 0), (0, 0, 0)))
        q, v = disconnected.evolve((3, 3, 7), (1, 1, -2), 2)
        np.testing.assert_array_equal(q, [5, 5, 3])
        np.testing.assert_array_equal(v, [1, 1, -2])


if __name__ == "__main__":
    unittest.main()
