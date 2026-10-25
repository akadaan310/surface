"""Required Qiskit differential checks, with an executable measured receipt.

Run tests normally, or run this module with --receipt NEW_PATH to retain actual
errors and input/code hashes. Missing Qiskit is an error, never a passing skip.
"""
import argparse
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
from qiskit.quantum_info import Choi, DensityMatrix, Kraus, Statevector, random_density_matrix, state_fidelity
import scipy
from scipy.linalg import svdvals

from research.quantum_oracle import quantum as q


def _hash(array):
    return hashlib.sha256(np.asarray(array, dtype="<c16").tobytes()).hexdigest()


def _row(name, difference, tolerance, inputs, **details):
    error = float(np.max(np.abs(difference)))
    return {"name": name, "max_absolute_error": error, "absolute_tolerance": tolerance,
            "status": "ACCEPT" if math.isfinite(error) and error <= tolerance else "REJECT",
            "input_sha256": [_hash(value) for value in inputs], **details}


def pure_comparisons():
    rows = []
    for n in (1, 2, 3, 4):
        basis = q.Basis(n)
        initial = q.basis_lift(q.ClassicalWord(0, n), basis)
        ours = []
        reference = QuantumCircuit(n)
        recipe = []
        for bit in range(n):
            reference.h(bit)
            reference.rz(.23 * (bit + 1), bit)
            reference.ry(-.17 * (bit + 1), bit)
            for name, angle in (("H", None), ("RZ", .23 * (bit + 1)), ("RY", -.17 * (bit + 1))):
                ours.append(q.gate(name, basis, q.LogicalQubit(bit, basis), angle=angle))
                recipe.append({"gate": name, "target": bit, "angle": angle})
        for bit in range(n - 1):
            reference.cx(bit, bit + 1)
            ours.append(q.controlled_x(q.LogicalQubit(bit, basis), q.LogicalQubit(bit + 1, basis)))
            recipe.append({"gate": "CX", "control": bit, "target": bit + 1})
        reference.s(0)
        ours.append(q.gate("S", basis, q.LogicalQubit(0, basis)))
        recipe.append({"gate": "S", "target": 0})
        got = q.run_circuit(initial, ours)
        expected = Statevector.from_instruction(reference)
        rows.append(_row(f"phase_sensitive_circuit_{n}_qubits", got.data - expected.data, 2e-14,
                         [initial.data], qubits=n, operations=recipe, output_sha256=_hash(got.data),
                         reference_output_sha256=_hash(expected.data)))
    return rows


def channel_comparisons():
    rows = []
    basis = q.Basis(1)
    initial = q.density(q.StateVector([math.sqrt(.3), 1j * math.sqrt(.7)], basis))
    for gamma in (0.0, .23, 1.0):
        operators = [np.diag([1, math.sqrt(1 - gamma)]), np.array([[0, math.sqrt(gamma)], [0, 0]])]
        ours = q.QuantumChannel(operators, basis)
        reference = Kraus(operators)
        if not reference.is_cptp():
            raise AssertionError("Qiskit rejected the controlled channel fixture")
        got = ours.apply(initial)
        expected = DensityMatrix(initial.data).evolve(reference)
        rows.append(_row(f"amplitude_damping_action_gamma_{gamma}", got.data - expected.data, 2e-14,
                         [initial.data] + operators, output_sha256=_hash(got.data), reference_output_sha256=_hash(expected.data)))
        rows.append(_row(f"amplitude_damping_choi_gamma_{gamma}", ours.choi() - Choi(reference).data, 2e-14,
                         operators, choi_convention="input_then_output_column_vectorization"))
    return rows


def metric_comparisons():
    rows = []
    for n in (1, 2, 3, 4):
        dimension = 1 << n
        first = random_density_matrix(dimension, seed=1800 + n)
        second = random_density_matrix(dimension, seed=1900 + n)
        a, b = q.DensityMatrix(first.data, q.Basis(n)), q.DensityMatrix(second.data, q.Basis(n))
        expected_fidelity = state_fidelity(first, second)
        expected_trace = float(svdvals(first.data - second.data).sum() / 2)
        expected_bures = math.sqrt(2 - 2 * math.sqrt(expected_fidelity))
        for label, got, expected in (("squared_fidelity", q.state_fidelity(a, b), expected_fidelity),
                                     ("trace_distance", q.trace_distance(a, b), expected_trace),
                                     ("bures_distance", q.bures_distance(a, b), expected_bures)):
            rows.append(_row(f"mixed_{label}_{n}_qubits", got - expected, 5e-13,
                             [first.data, second.data], measured=got, reference=expected,
                             fixture_seeds=[1800 + n, 1900 + n]))
    return rows


class QiskitReferenceTests(unittest.TestCase):
    def _check(self, rows):
        for row in rows:
            with self.subTest(comparison=row["name"]):
                self.assertEqual(row["status"], "ACCEPT", row)

    def test_phase_sensitive_circuits_against_qiskit(self):
        self._check(pure_comparisons())

    def test_density_and_channel_choi_against_qiskit(self):
        self._check(channel_comparisons())

    def test_mixed_metrics_against_qiskit_and_scipy_singular_values(self):
        self._check(metric_comparisons())

    def test_relative_phase_perturbation_is_detected_by_reference(self):
        plus = Statevector([1 / math.sqrt(2), 1 / math.sqrt(2)])
        phase_flipped = Statevector([1 / math.sqrt(2), -1 / math.sqrt(2)])
        np.testing.assert_allclose(plus.probabilities(), phase_flipped.probabilities(), atol=1e-15)
        self.assertLess(state_fidelity(plus, phase_flipped), 1e-15)
        a = q.StateVector(plus.data, q.Basis(1))
        b = q.StateVector(phase_flipped.data, q.Basis(1))
        self.assertAlmostEqual(q.fubini_study(a, b), math.pi / 2)


def write_receipt(destination):
    rows = pure_comparisons() + channel_comparisons() + metric_comparisons()
    repo = Path(__file__).resolve().parents[3]
    files = [Path(q.__file__), Path(__file__), repo / "build/foundation/QUANTUM_ORACLE_V3_EXTENSION/atlas_quantum/core.py",
             repo / "build/foundation/quantum_oracle/quantum_oracle/core.py"]
    record = {"schema": "quantum-oracle.backend-comparison/1", "executed_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "bounded classical numerical comparisons, 1..4 qubits; no physical hardware or complete G2 claim",
              "command": [sys.executable, "-B", "-m", "research.quantum_oracle.tests.test_qiskit_reference", "--receipt", str(destination)],
              "environment": {"python": platform.python_version(), "platform": platform.platform(), "numpy": np.__version__,
                              "scipy": scipy.__version__, "qiskit": qiskit.__version__},
              "source_sha256": {str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
              "comparison_count": len(rows), "accepted": sum(row["status"] == "ACCEPT" for row in rows),
              "rows": rows, "status": "ACCEPT" if all(row["status"] == "ACCEPT" for row in rows) else "REJECT",
              "independence_limit": "Independent APIs and implementations share NumPy/SciPy and BLAS; not independent hardware or all mathematical algorithms."}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, allow_nan=False)
        handle.write("\n")
    if record["status"] != "ACCEPT":
        raise AssertionError("one or more measured backend comparisons rejected")
    print(json.dumps({"receipt": str(destination), "comparison_count": len(rows), "status": record["status"]}))


if __name__ == "__main__":
    if "--receipt" in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument("--receipt", type=Path, required=True)
        write_receipt(parser.parse_args().receipt)
    else:
        unittest.main()
