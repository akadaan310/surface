"""Historical-target compilation and explicitly limited calibrated surrogate."""
import copy
import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import unittest

import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Kraus, Operator
from research.quantum_oracle import quantum as q
try:
    from research.quantum_oracle import circuits as c
except ImportError:
    c = None

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/ibm_brisbane_snapshot"


def reference_surrogate(compiled, snapshot):
    """Independent Qiskit Kraus evolution and scalar readout calculation."""
    n = len(snapshot.physical_qubits)
    rho = DensityMatrix.from_label("0" * n)
    for op in compiled.native_operations:
        circuit = QuantumCircuit(n)
        getattr(circuit, op.name)(*(list(op.parameters) + list(op.local_qubits)))
        rho = rho.evolve(Operator(circuit))
        for bit, calibration in enumerate(snapshot.qubits):
            gamma = 1 - math.exp(-op.duration_seconds / calibration.t1_seconds)
            rho = rho.evolve(Kraus([np.diag([1, math.sqrt(1 - gamma)]),
                                    np.array([[0, math.sqrt(gamma)], [0, 0]])]), qargs=[bit])
    permutation = compiled.output_permutation
    expected_rho = rho.data[np.ix_(permutation, permutation)]
    physical_probs = rho.probabilities()
    expected_observed = []
    for output in range(1 << n):
        probability = 0.0
        for actual in range(1 << n):
            weight = float(physical_probs[actual])
            for bit, cal in enumerate(snapshot.qubits):
                read, true = (output >> bit) & 1, (actual >> bit) & 1
                flip = cal.prob_meas1_prep0 if true == 0 else cal.prob_meas0_prep1
                weight *= flip if read != true else 1 - flip
            probability += weight
        expected_observed.append(probability)
    return expected_rho, np.asarray(expected_observed)[list(permutation)]


class CircuitTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(c, "typed historical circuit compiler missing")
        self.snapshot = c.load_snapshot(FIXTURES, physical_qubits=(0, 1))
        self.basis = q.Basis(2)

    def _ir(self, qubits=2):
        b = q.Basis(qubits)
        return c.CircuitIR(b, (c.CircuitOp("H", (q.LogicalQubit(0, b),)),
                               c.CircuitOp("RZ", (q.LogicalQubit(0, b),), .31),
                               c.CircuitOp("CX", (q.LogicalQubit(0, b), q.LogicalQubit(qubits - 1, b)))))

    def _admit_changed(self, config=None, props=None, selected=(0, 1)):
        original_config = json.loads((FIXTURES / "conf_brisbane.json").read_bytes())
        original_props = json.loads((FIXTURES / "props_brisbane.json").read_bytes())
        config_bytes = json.dumps(original_config if config is None else config).encode()
        props_bytes = json.dumps(original_props if props is None else props).encode()
        return c.admit_snapshot(config_bytes, props_bytes, physical_qubits=selected,
                                source_revision="1dd86e381ddecfc78db94e3287a9ce57e4ad65d8",
                                acquired_at="2026-10-25T17:08:08+00:00",
                                expected_config_sha256=hashlib.sha256(config_bytes).hexdigest(),
                                expected_properties_sha256=hashlib.sha256(props_bytes).hexdigest())

    def test_authentic_historical_snapshot_preserves_source_and_units(self):
        self.assertEqual(self.snapshot.backend_name, "ibm_brisbane")
        self.assertEqual(self.snapshot.calibration_at, "2025-02-26T19:33:06+00:00")
        self.assertEqual(self.snapshot.physical_qubits, (0, 1))
        self.assertEqual(self.snapshot.couplings, ((1, 0),))
        self.assertAlmostEqual(self.snapshot.gate("ecr", (1, 0)).duration_seconds, 660e-9)
        self.assertAlmostEqual(self.snapshot.qubits[0].t1_seconds, 237.36364020705798e-6)
        self.assertFalse(self.snapshot.current_calibration)

    def test_snapshot_rejects_malformed_dates_addresses_and_units(self):
        original = json.loads((FIXTURES / "props_brisbane.json").read_bytes())
        for date in ("2025-02-26T14:33:06", "not-a-date", "2027-01-01T00:00:00+00:00"):
            changed = copy.deepcopy(original)
            changed["last_update_date"] = date
            with self.subTest(date=date), self.assertRaises(ValueError):
                self._admit_changed(props=changed)
        for selected in ((0, 0), (0, 126), (0, 127), (True, 1), (0, 1, 2, 3, 4)):
            with self.subTest(selected=selected), self.assertRaises((ValueError, TypeError)):
                self._admit_changed(selected=selected)
        changed = copy.deepcopy(original)
        changed["qubits"][0][0]["unit"] = "ms-unrecognized"
        with self.assertRaises(ValueError):
            self._admit_changed(props=changed)

    def test_snapshot_tampering_fails_hash_before_admission(self):
        config = (FIXTURES / "conf_brisbane.json").read_bytes()
        props = (FIXTURES / "props_brisbane.json").read_bytes()
        with self.assertRaises(ValueError):
            c.admit_snapshot(config, props + b" ", physical_qubits=(0, 1),
                             source_revision="1dd86e381ddecfc78db94e3287a9ce57e4ad65d8",
                             acquired_at="2026-10-25T17:08:08+00:00",
                             expected_config_sha256=hashlib.sha256(config).hexdigest(),
                             expected_properties_sha256=hashlib.sha256(props).hexdigest())

    def test_missing_calibration_fields_reject_explicitly(self):
        props = json.loads((FIXTURES / "props_brisbane.json").read_bytes())
        props["gates"][0]["parameters"] = [p for p in props["gates"][0]["parameters"] if p["name"] != "gate_error"]
        with self.assertRaises(ValueError):
            self._admit_changed(props=props)

    def test_typed_circuit_rejects_address_confusion_nonfinite_and_overbudget(self):
        with self.assertRaises(TypeError):
            c.CircuitOp("H", (q.ByteOffset(0),))
        with self.assertRaises(ValueError):
            c.CircuitOp("RX", (q.LogicalQubit(0, self.basis),), math.inf)
        with self.assertRaises(ValueError):
            c.CircuitOp("CX", (q.LogicalQubit(0, self.basis), q.LogicalQubit(0, self.basis)))
        with self.assertRaises(ValueError):
            c.CircuitIR(self.basis, self._ir().operations * 11)

    def test_compile_native_topology_and_full_unitary_equivalence(self):
        result = c.compile_circuit(self._ir(), self.snapshot, seed=83)
        self.assertLess(result.unitary_error, 1e-12)
        self.assertGreater(len(result.native_operations), 0)
        self.assertLessEqual(len(result.native_operations), 256)
        for op in result.native_operations:
            self.assertIn(op.name, self.snapshot.native_gates)
            self.assertTrue(all(isinstance(site, q.HardwareQubit) for site in op.hardware_sites))
            if op.name == "ecr":
                self.assertEqual(tuple(int(site.site) for site in op.hardware_sites), (1, 0))
        self.assertAlmostEqual(result.serial_duration_seconds, sum(op.duration_seconds for op in result.native_operations))
        self.assertEqual(result.initial_mapping, self.snapshot.hardware_sites)

    def test_nonlocal_four_qubit_routing_tracks_final_permutation(self):
        snapshot = c.load_snapshot(FIXTURES, physical_qubits=(0, 1, 2, 3))
        result = c.compile_circuit(self._ir(4), snapshot, seed=31)
        self.assertLess(result.unitary_error, 2e-12)
        self.assertEqual(set(result.final_mapping), set(snapshot.hardware_sites))
        self.assertNotEqual(result.output_permutation, tuple(range(16)))
        for op in result.native_operations:
            if op.name == "ecr":
                self.assertIn(tuple(int(site.site) for site in op.hardware_sites), snapshot.couplings)

    def test_compilation_replays_and_seed_budget_rejects(self):
        first = c.compile_circuit(self._ir(), self.snapshot, seed=4)
        second = c.compile_circuit(self._ir(), self.snapshot, seed=4)
        self.assertEqual(first, second)
        with self.assertRaises((TypeError, ValueError)):
            c.compile_circuit(self._ir(), self.snapshot, seed=True)
        with self.assertRaises(ValueError):
            c.compile_circuit(self._ir(3), self.snapshot, seed=1)

    def test_output_gate_budget_and_single_qubit_target(self):
        basis = q.Basis(4)
        op = c.CircuitOp("CX", (q.LogicalQubit(0, basis), q.LogicalQubit(3, basis)))
        with self.assertRaises(ValueError):
            c.compile_circuit(c.CircuitIR(basis, (op,) * 32), c.load_snapshot(FIXTURES, physical_qubits=(0, 1, 2, 3)), seed=2)
        basis = q.Basis(1)
        small = c.CircuitIR(basis, (c.CircuitOp("H", (q.LogicalQubit(0, basis),)),))
        compiled = c.compile_circuit(small, c.load_snapshot(FIXTURES, physical_qubits=(0,)), seed=2)
        self.assertLess(compiled.unitary_error, 1e-12)

    def test_compiled_record_cannot_forge_mapping_duration_or_gate_action(self):
        result = c.compile_circuit(self._ir(), self.snapshot, seed=7)
        for changes in ({"output_permutation": tuple(reversed(result.output_permutation))},
                        {"serial_duration_seconds": -1}, {"unitary_error": math.nan}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(result, **changes)
        operations = list(result.native_operations)
        index = next(i for i, op in enumerate(operations) if op.name == "rz")
        operations[index] = replace(operations[index], parameters=(operations[index].parameters[0] + .2,))
        with self.assertRaises(ValueError):
            replace(result, native_operations=tuple(operations))

    def test_snapshot_semantics_and_compiled_calibrations_are_bound_to_source_bytes(self):
        with self.assertRaises(ValueError):
            replace(self.snapshot, couplings=self.snapshot.couplings * 10000)
        for changes in ({"duration_seconds": 0., "error": 1.}, {"measured_at": "2099-01-01T00:00:00+00:00"}):
            altered = tuple(replace(gate, **changes) for gate in self.snapshot.gates)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.snapshot, gates=altered)
        compiled = c.compile_circuit(self._ir(), self.snapshot, seed=7)
        altered = tuple(replace(op, duration_seconds=0., reported_gate_error=1.) for op in compiled.native_operations)
        with self.assertRaises(ValueError):
            replace(compiled, native_operations=altered, serial_duration_seconds=0.)

    def test_calibrated_surrogate_matches_independent_qiskit_kraus_path(self):
        compiled = c.compile_circuit(self._ir(), self.snapshot, seed=19)
        got = c.simulate_surrogate(compiled, self.snapshot)
        expected_rho, expected_observed = reference_surrogate(compiled, self.snapshot)
        np.testing.assert_allclose(got.quantum_state.data, expected_rho, atol=3e-14)
        np.testing.assert_allclose(got.observed_probabilities.data, expected_observed, atol=3e-14)
        self.assertGreater(q.trace_distance(got.quantum_state, q.density(compiled.logical_unitary.apply(q.basis_lift(q.ClassicalWord(0, 2), self.basis)))), 1e-6)
        self.assertIn("gate_error_not_converted_to_depolarizing", got.assumptions)


def write_receipt(destination):
    rows = []
    for n in (2, 3, 4):
        basis = q.Basis(n)
        source = c.CircuitIR(basis, (c.CircuitOp("H", (q.LogicalQubit(0, basis),)),
                                     c.CircuitOp("RZ", (q.LogicalQubit(0, basis),), .31),
                                     c.CircuitOp("CX", (q.LogicalQubit(0, basis), q.LogicalQubit(n - 1, basis)))))
        snapshot = c.load_snapshot(FIXTURES, physical_qubits=tuple(range(n)))
        compiled = c.compile_circuit(source, snapshot, seed=53)
        result = c.simulate_surrogate(compiled, snapshot)
        reference_rho, reference_probs = reference_surrogate(compiled, snapshot)
        rho_error = float(np.max(np.abs(result.quantum_state.data - reference_rho)))
        readout_error = float(np.max(np.abs(result.observed_probabilities.data - reference_probs)))
        counts = np.random.Generator(np.random.PCG64(992)).multinomial(4096, result.observed_probabilities.data)
        rows.append({"logical_qubits": n, "physical_sites": snapshot.physical_qubits,
                     "source_operations": [{"name": op.name, "logical_qubits": [bit.index for bit in op.qubits], "angle": op.angle} for op in source.operations],
                     "transpiler_seed": compiled.seed, "initial_mapping": [site.site for site in compiled.initial_mapping],
                     "final_mapping": [site.site for site in compiled.final_mapping], "output_permutation": compiled.output_permutation,
                     "global_phase": compiled.global_phase, "native_gate_counts": dict(Counter(op.name for op in compiled.native_operations)),
                     "native_operations": [{"name": op.name, "local_slots": op.local_qubits, "physical_sites": [site.site for site in op.hardware_sites],
                                            "parameters": op.parameters, "duration_seconds": op.duration_seconds,
                                            "reported_gate_error": op.reported_gate_error} for op in compiled.native_operations],
                     "serial_duration_seconds": compiled.serial_duration_seconds, "unitary_error": compiled.unitary_error,
                     "unitary_absolute_tolerance": 1e-10, "surrogate_density_error": rho_error, "readout_probability_error": readout_error,
                     "surrogate_absolute_tolerance": 3e-14, "surrogate_observed_probabilities": result.observed_probabilities.data.tolist(),
                     "simulated_counts": counts.tolist(), "shots": 4096, "sampling_seed": 992,
                     "output_density_sha256": hashlib.sha256(result.quantum_state.data.astype('<c16').tobytes()).hexdigest(),
                     "assumptions": result.assumptions, "comparison_status": "PASS" if rho_error <= 3e-14 and readout_error <= 3e-14 and compiled.unitary_error <= 1e-10 else "FAIL"})
    repo = Path(__file__).resolve().parents[3]
    files = [Path(c.__file__), Path(q.__file__), Path(__file__), FIXTURES / "conf_brisbane.json", FIXTURES / "props_brisbane.json", FIXTURES / "LICENSE.txt"]
    record = {"schema": "quantum-oracle.historical-compilation/1", "executed_utc": datetime.now(timezone.utc).isoformat(),
              "command": [sys.executable, "-B", "-m", "research.quantum_oracle.tests.test_circuits", "--receipt", str(destination)],
              "environment": {"python": platform.python_version(), "qiskit": qiskit.__version__, "numpy": np.__version__},
              "source_revision": c.SOURCE_REVISION, "calibration_at": snapshot.calibration_at,
              "source_sha256": {str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
              "case_count": len(rows), "passed_cases": sum(row["comparison_status"] == "PASS" for row in rows), "rows": rows,
              "evidence_class": "historical_calibration_constrained_classical_simulation", "provider_submissions": 0,
              "provider_spend": 0, "current_calibration": False, "hardware_execution": False,
              "full_G5_status": "UNKNOWN", "scientific_admission": "requires_review_of_exact_finite_scope"}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, allow_nan=False)
        handle.write("\n")
    if record["passed_cases"] != len(rows):
        raise AssertionError("calibrated surrogate comparison failed")
    print(json.dumps({"receipt": str(destination), "case_count": len(rows), "passed_cases": record["passed_cases"]}))


if __name__ == "__main__":
    if "--receipt" in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument("--receipt", type=Path, required=True)
        write_receipt(parser.parse_args().receipt)
    else:
        unittest.main()
