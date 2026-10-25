"""Versioned finite quantum reference adapter; classical simulation only.

Admission rejects invalid data instead of normalizing or silently changing basis.
See quantum-contract.md for numerical tolerance, units, evidence and exclusions.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import numbers
from typing import Union

import numpy as np

ATOL = 1e-10
MAX_QUBITS = 4
MAX_KRAUS = 16
MAX_STEPS = 256
MAX_SHOTS = 100_000
MAX_PHASE = 1_000_000.0
STATE_SCHEMA = "quantum-oracle.statevector/1"


def _integer(value, low, high, label):
    if type(value) is not int:
        raise TypeError(f"{label} must be an integer, not a coerced scalar")
    if not low <= value <= high:
        raise ValueError(f"{label} outside finite budget {low}..{high}")
    return value


def _real(value, label):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
        raise TypeError(f"{label} must be real")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return value


def _label(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{name} must be a nonempty bounded string")


@dataclass(frozen=True)
class Basis:
    qubits: int
    order: str = "qubit_0_lsb"

    def __post_init__(self):
        _integer(self.qubits, 1, MAX_QUBITS, "qubits")
        if self.order not in ("qubit_0_lsb", "qubit_0_msb"):
            raise ValueError("explicit supported basis order required")

    @property
    def dimension(self):
        return 1 << self.qubits

    def bit_position(self, qubit):
        _require(qubit, LogicalQubit)
        _same_basis(self, qubit.basis)
        return qubit.index if self.order == "qubit_0_lsb" else self.qubits - 1 - qubit.index


@dataclass(frozen=True)
class ClassicalWord:
    value: int
    width: int

    def __post_init__(self):
        _integer(self.width, 1, 64, "word width")
        _integer(self.value, 0, (1 << self.width) - 1, "unsigned word")


@dataclass(frozen=True)
class BasisIndex:
    value: int
    basis: Basis

    def __post_init__(self):
        _require(self.basis, Basis)
        _integer(self.value, 0, self.basis.dimension - 1, "basis index")


@dataclass(frozen=True)
class LogicalQubit:
    index: int
    basis: Basis

    def __post_init__(self):
        _require(self.basis, Basis)
        _integer(self.index, 0, self.basis.qubits - 1, "logical qubit")


@dataclass(frozen=True)
class ByteOffset:
    value: int

    def __post_init__(self):
        _integer(self.value, 0, (1 << 63) - 1, "byte offset")


@dataclass(frozen=True)
class HardwareQubit:
    provider: str
    device: str
    site: str
    calibration_id: str

    def __post_init__(self):
        for name in ("provider", "device", "site", "calibration_id"):
            _label(getattr(self, name), name)


def _require(value, kind):
    if not isinstance(value, kind):
        raise TypeError(f"expected {getattr(kind, '__name__', kind)}, got {type(value).__name__}")


def _same_basis(left, right):
    if left != right:
        raise ValueError("basis mismatch; use explicit rebase")


def _array(values, shape, *, real=False):
    # Check the dimensions before allocating a numeric copy. No unbounded iterators.
    if not isinstance(values, (list, tuple, np.ndarray)):
        raise TypeError("bounded list, tuple or ndarray required")
    if isinstance(values, np.ndarray):
        if values.shape != shape:
            raise ValueError(f"expected shape {shape}")
    else:
        if len(values) != shape[0]:
            raise ValueError(f"expected shape {shape}")
        rows = [values] if len(shape) == 1 else values
        for row in rows:
            if (not isinstance(row, (list, tuple, np.ndarray))
                    or (isinstance(row, np.ndarray) and row.ndim != 1)
                    or len(row) != shape[-1]):
                raise ValueError(f"expected shape {shape}")
            if any(isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Number) for value in row):
                raise ValueError("numeric scalar leaves required before array allocation")
    array = np.asarray(values)
    if array.shape != shape or array.dtype.kind not in "iufc":
        raise ValueError("finite numeric array of declared shape required")
    if real and np.iscomplexobj(array):
        raise ValueError("real-valued array required, complex coercion is forbidden")
    array = np.array(array, dtype=np.float64 if real else np.complex128, copy=True)
    if not np.isfinite(array).all():
        raise ValueError("nonfinite array")
    return array


def _close(left, right):
    return bool(np.allclose(left, right, atol=ATOL, rtol=0))


def _hermitian(array):
    if not _close(array, array.conj().T):
        raise ValueError("Hermitian matrix required")


def _store(instance, array, basis):
    # Bytes are immutable; .data returns a fresh copy. No writable aliases survive.
    object.__setattr__(instance, "basis", basis)
    object.__setattr__(instance, "_shape", array.shape)
    object.__setattr__(instance, "_dtype", array.dtype.str)
    object.__setattr__(instance, "_payload", array.tobytes(order="C"))


@dataclass(frozen=True, init=False)
class _ArrayRecord:
    basis: Basis
    _shape: tuple
    _dtype: str
    _payload: bytes

    @property
    def data(self):
        return np.frombuffer(self._payload, dtype=self._dtype).reshape(self._shape).copy()


@dataclass(frozen=True, init=False)
class StateVector(_ArrayRecord):
    def __init__(self, amplitudes, basis):
        _require(basis, Basis)
        array = _array(amplitudes, (basis.dimension,))
        if np.max(np.abs(array)) > 1 + ATOL or abs(float(np.vdot(array, array).real) - 1) > ATOL:
            raise ValueError("state normalization required; no automatic normalization")
        _store(self, array, basis)


@dataclass(frozen=True, init=False)
class DensityMatrix(_ArrayRecord):
    def __init__(self, entries, basis):
        _require(basis, Basis)
        array = _array(entries, (basis.dimension, basis.dimension))
        _hermitian(array)
        if np.max(np.abs(array)) > 1 + ATOL or abs(np.trace(array) - 1) > ATOL:
            raise ValueError("density trace must be one")
        if float(np.linalg.eigvalsh(array).min()) < -ATOL:
            raise ValueError("density must be positive semidefinite")
        _store(self, array, basis)


@dataclass(frozen=True, init=False)
class ProbabilityDistribution(_ArrayRecord):
    def __init__(self, probabilities, basis):
        _require(basis, Basis)
        array = _array(probabilities, (basis.dimension,), real=True)
        if np.any(array < 0) or np.any(array > 1 + ATOL) or abs(float(array.sum()) - 1) > ATOL:
            raise ValueError("normalized nonnegative probabilities required")
        _store(self, array, basis)


QuantumState = Union[StateVector, DensityMatrix]


def _state(state):
    _require(state, (StateVector, DensityMatrix))


def basis_lift(word, basis):
    _require(word, ClassicalWord)
    _require(basis, Basis)
    if word.width != basis.qubits:
        raise ValueError("word width must match register")
    array = np.zeros(basis.dimension, complex)
    array[word.value] = 1
    return StateVector(array, basis)


def rebase(state, basis):
    """Permute bit significance while retaining logical-qubit labels."""
    _state(state)
    _require(basis, Basis)
    if state.basis.qubits != basis.qubits:
        raise ValueError("basis conversion cannot change dimension")
    indices = list(range(basis.dimension))
    if state.basis.order != basis.order:
        indices = [int(format(i, f"0{basis.qubits}b")[::-1], 2) for i in indices]
    if isinstance(state, StateVector):
        return StateVector(state.data[indices], basis)
    return DensityMatrix(state.data[np.ix_(indices, indices)], basis)


def density(state):
    _require(state, StateVector)
    vector = state.data
    return DensityMatrix(np.outer(vector, vector.conj()), state.basis)


def _rho(state):
    _state(state)
    return density(state).data if isinstance(state, StateVector) else state.data


def diagonal_density(distribution):
    _require(distribution, ProbabilityDistribution)
    return DensityMatrix(np.diag(distribution.data), distribution.basis)


def probabilities(state):
    _state(state)
    values = np.abs(state.data) ** 2 if isinstance(state, StateVector) else np.diag(state.data).real
    # Admission permits roundoff at ATOL. Clipping applies only to derived Born
    # weights; it never changes the admitted state or its encoded bytes.
    values = np.maximum(values, 0)
    values /= values.sum()
    return ProbabilityDistribution(values, state.basis)


@dataclass(frozen=True, init=False)
class Unitary(_ArrayRecord):
    def __init__(self, entries, basis):
        _require(basis, Basis)
        array = _array(entries, (basis.dimension, basis.dimension))
        if np.max(np.abs(array)) > 1 + ATOL or not _close(array.conj().T @ array, np.eye(basis.dimension)):
            raise ValueError("unitary matrix required")
        _store(self, array, basis)

    def apply(self, state):
        _state(state)
        _same_basis(self.basis, state.basis)
        if isinstance(state, StateVector):
            return StateVector(self.data @ state.data, self.basis)
        return DensityMatrix(self.data @ state.data @ self.data.conj().T, self.basis)

    def adjoint(self):
        return Unitary(self.data.conj().T, self.basis)


def gate(name, basis, target, *, angle=None):
    _require(basis, Basis)
    position = basis.bit_position(target)
    i = np.eye(2, dtype=complex)
    x = np.array([[0, 1], [1, 0]], complex)
    y = np.array([[0, -1j], [1j, 0]], complex)
    z = np.diag([1, -1]).astype(complex)
    gates = {"I": i, "X": x, "Y": y, "Z": z, "H": np.array([[1, 1], [1, -1]]) / math.sqrt(2),
             "S": np.diag([1, 1j]), "T": np.diag([1, np.exp(1j * math.pi / 4)])}
    if name in ("RX", "RY", "RZ"):
        theta = _real(angle, "rotation angle")
        if abs(theta) > MAX_PHASE:
            raise ValueError("rotation phase budget")
        small = math.cos(theta / 2) * i - 1j * math.sin(theta / 2) * {"RX": x, "RY": y, "RZ": z}[name]
    else:
        if name not in gates or angle is not None:
            raise ValueError("unknown gate or inapplicable angle")
        small = gates[name]
    matrix = np.array([[1]], complex)
    for bit in reversed(range(basis.qubits)):
        matrix = np.kron(matrix, small if bit == position else i)
    return Unitary(matrix, basis)


def controlled_x(control, target):
    _require(control, LogicalQubit)
    _require(target, LogicalQubit)
    _same_basis(control.basis, target.basis)
    if control == target:
        raise ValueError("control and target must differ")
    basis = control.basis
    cmask, tmask = 1 << basis.bit_position(control), 1 << basis.bit_position(target)
    matrix = np.zeros((basis.dimension, basis.dimension), complex)
    for column in range(basis.dimension):
        matrix[column ^ tmask if column & cmask else column, column] = 1
    return Unitary(matrix, basis)


def run_circuit(state, operations):
    _state(state)
    if not isinstance(operations, (list, tuple)) or len(operations) > MAX_STEPS:
        raise ValueError("finite circuit list, at most 256 operations, required")
    for operation in operations:
        _require(operation, Unitary)
        _same_basis(operation.basis, state.basis)
    for operation in operations:
        state = operation.apply(state)
    return state


@dataclass(frozen=True, init=False)
class Observable(_ArrayRecord):
    unit: str

    def __init__(self, entries, basis, unit):
        _require(basis, Basis)
        _label(unit, "observable unit")
        array = _array(entries, (basis.dimension, basis.dimension))
        if np.max(np.abs(array)) > 1e6:
            raise ValueError("observable coefficient budget 1e6")
        _hermitian(array)
        _store(self, array, basis)
        object.__setattr__(self, "unit", unit)


@dataclass(frozen=True, init=False)
class Hamiltonian(Observable):
    def __init__(self, entries, basis, unit):
        if unit != "rad/s":
            raise ValueError("angular-frequency Hamiltonian H/hbar in rad/s required")
        super().__init__(entries, basis, unit)


def expectation(state, observable):
    _state(state)
    _require(observable, Observable)
    _same_basis(state.basis, observable.basis)
    return float(np.trace(_rho(state) @ observable.data).real)


def variance(state, observable):
    mean = expectation(state, observable)
    value = float(np.trace(_rho(state) @ observable.data @ observable.data).real) - mean * mean
    return max(0.0, value)


def evolve_closed(state, hamiltonian, time_seconds):
    _state(state)
    _require(hamiltonian, Hamiltonian)
    _same_basis(state.basis, hamiltonian.basis)
    time_seconds = _real(time_seconds, "time in seconds")
    eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian.data)
    if abs(time_seconds) > 1e6 or np.max(np.abs(eigenvalues)) * abs(time_seconds) > MAX_PHASE:
        raise ValueError("closed dynamics time/phase budget")
    matrix = (eigenvectors * np.exp(-1j * eigenvalues * time_seconds)) @ eigenvectors.conj().T
    return Unitary(matrix, state.basis).apply(state)


@dataclass(frozen=True, init=False)
class StochasticMap(_ArrayRecord):
    """Column-stochastic transition: p_out = P @ p_in, no phase semantics."""
    def __init__(self, entries, basis):
        _require(basis, Basis)
        array = _array(entries, (basis.dimension, basis.dimension), real=True)
        if np.any(array < 0) or np.any(array > 1 + ATOL) or not _close(array.sum(axis=0), np.ones(basis.dimension)):
            raise ValueError("column-stochastic matrix required")
        _store(self, array, basis)

    def apply(self, distribution):
        _require(distribution, ProbabilityDistribution)
        _same_basis(self.basis, distribution.basis)
        return ProbabilityDistribution(self.data @ distribution.data, self.basis)


@dataclass(frozen=True, init=False)
class QuantumChannel:
    basis: Basis
    _kraus_bytes: tuple

    def __init__(self, kraus, basis):
        _require(basis, Basis)
        if not isinstance(kraus, (list, tuple)) or not 1 <= len(kraus) <= MAX_KRAUS:
            raise ValueError("channel requires 1..16 bounded Kraus operators")
        arrays = [_array(k, (basis.dimension, basis.dimension)) for k in kraus]
        if any(np.max(np.abs(k)) > 1 + ATOL for k in arrays):
            raise ValueError("Kraus contraction bound")
        if not _close(sum((k.conj().T @ k for k in arrays), np.zeros_like(arrays[0])), np.eye(basis.dimension)):
            raise ValueError("Kraus completeness sum K†K = I required")
        object.__setattr__(self, "basis", basis)
        object.__setattr__(self, "_kraus_bytes", tuple(k.astype("<c16").tobytes() for k in arrays))

    @property
    def kraus(self):
        d = self.basis.dimension
        return tuple(np.frombuffer(data, dtype="<c16").reshape(d, d).copy() for data in self._kraus_bytes)

    def apply(self, state):
        _require(state, DensityMatrix)
        _same_basis(self.basis, state.basis)
        rho = state.data
        return DensityMatrix(sum((k @ rho @ k.conj().T for k in self.kraus), np.zeros_like(rho)), self.basis)

    def choi(self):
        # Column vectorization: composite index (input a, output i).
        d = self.basis.dimension
        return sum((np.outer(k.flatten(order="F"), k.flatten(order="F").conj()) for k in self.kraus),
                   np.zeros((d * d, d * d), complex))


def purity(state):
    _require(state, DensityMatrix)
    rho = state.data
    return float(np.trace(rho @ rho).real)


def fubini_study(left, right):
    """Ray angle in radians, stable near equal rays; no acos(1-epsilon)."""
    _require(left, StateVector)
    _require(right, StateVector)
    _same_basis(left.basis, right.basis)
    a, b = left.data, right.data
    a /= np.linalg.norm(a)
    b /= np.linalg.norm(b)
    overlap = np.vdot(a, b)
    if abs(overlap) > 0:
        b *= overlap.conjugate() / abs(overlap)
    return float(2 * math.atan2(float(np.linalg.norm(a - b)), float(np.linalg.norm(a + b))))


def trace_distance(left, right):
    _state(left)
    _state(right)
    _same_basis(left.basis, right.basis)
    return float(np.abs(np.linalg.eigvalsh(_metric_rho(left) - _metric_rho(right))).sum() / 2)


def _metric_rho(state):
    """Normalized mathematical representative; never modifies admitted bytes.

    Density admission roundoff is projected to Hermitian PSD and trace one for
    all metrics consistently, including their identity-of-indiscernibles limit.
    """
    if isinstance(state, StateVector):
        vector = state.data
        vector /= np.linalg.norm(vector)
        return np.outer(vector, vector.conj())
    rho = _rho(state)
    eigenvalues, eigenvectors = np.linalg.eigh((rho + rho.conj().T) / 2)
    eigenvalues = np.maximum(eigenvalues, 0)
    eigenvalues /= eigenvalues.sum()
    return (eigenvectors * eigenvalues) @ eigenvectors.conj().T


def _positive_sqrt(matrix):
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    return (eigenvectors * np.sqrt(np.maximum(eigenvalues, 0))) @ eigenvectors.conj().T


def state_fidelity(left, right):
    """Squared Uhlmann fidelity, F=(Tr sqrt(sqrt(rho) sigma sqrt(rho)))²."""
    _state(left)
    _state(right)
    _same_basis(left.basis, right.basis)
    if isinstance(left, StateVector):
        vector = left.data
        vector /= np.linalg.norm(vector)
        value = np.vdot(vector, _metric_rho(right) @ vector).real
    elif isinstance(right, StateVector):
        return state_fidelity(right, left)
    else:
        product = _positive_sqrt(_metric_rho(left)) @ _positive_sqrt(_metric_rho(right))
        value = float(np.linalg.svd(product, compute_uv=False).sum()) ** 2
    return float(np.clip(value, 0, 1))


def bures_distance(left, right):
    """Bures via aligned purifications, avoiding cancellation near equality."""
    _state(left)
    _state(right)
    _same_basis(left.basis, right.basis)
    if isinstance(left, StateVector) and isinstance(right, StateVector):
        return 2 * math.sin(fubini_study(left, right) / 2)
    a = _positive_sqrt(_metric_rho(left))
    b = _positive_sqrt(_metric_rho(right))
    u, _, vh = np.linalg.svd(a.conj().T @ b)
    alignment = vh.conj().T @ u.conj().T
    return float(np.linalg.norm(a - b @ alignment, ord="fro"))


@dataclass(frozen=True)
class MeasurementRecord:
    basis: Basis
    probabilities: ProbabilityDistribution
    counts: tuple
    shots: int
    seed: int
    information_loss: bool = True
    preparation: str = "independent_identically_prepared"

    def __post_init__(self):
        _require(self.basis, Basis)
        _require(self.probabilities, ProbabilityDistribution)
        _same_basis(self.basis, self.probabilities.basis)
        _integer(self.shots, 0, MAX_SHOTS, "shots")
        _integer(self.seed, 0, (1 << 64) - 1, "seed")
        if type(self.counts) is not tuple or len(self.counts) != self.basis.dimension:
            raise ValueError("immutable counts tuple for the declared basis required")
        for count in self.counts:
            _integer(count, 0, self.shots, "outcome count")
        if sum(self.counts) != self.shots:
            raise ValueError("counts must sum to shots")
        if self.information_loss is not True or self.preparation != "independent_identically_prepared":
            raise ValueError("measurement is lossy and assumes independent preparations")


@dataclass(frozen=True)
class MeasurementOutcome:
    index: BasisIndex
    probability: float
    post_state: DensityMatrix
    information_loss: bool = True

    def __post_init__(self):
        _require(self.index, BasisIndex)
        _require(self.post_state, DensityMatrix)
        _same_basis(self.index.basis, self.post_state.basis)
        value = _real(self.probability, "outcome probability")
        if not 0 < value <= 1 or self.information_loss is not True:
            raise ValueError("positive outcome probability and measurement loss required")
        projector = np.zeros_like(self.post_state.data)
        projector[self.index.value, self.index.value] = 1
        if not _close(self.post_state.data, projector):
            raise ValueError("post-state must match the computational-basis projector")


def measure(state, *, shots, seed):
    _state(state)
    _integer(shots, 0, MAX_SHOTS, "shots")
    _integer(seed, 0, (1 << 64) - 1, "seed")
    distribution = probabilities(state)
    rng = np.random.Generator(np.random.PCG64(seed))
    counts = tuple(int(x) for x in rng.multinomial(shots, distribution.data))
    return MeasurementRecord(state.basis, distribution, counts, shots, seed)


def project_measurement(state, index):
    _state(state)
    _require(index, BasisIndex)
    _same_basis(state.basis, index.basis)
    probability = float(probabilities(state).data[index.value])
    if probability <= 0:
        raise ValueError("cannot condition on a zero-probability outcome")
    post = np.zeros((state.basis.dimension, state.basis.dimension), complex)
    post[index.value, index.value] = 1
    return MeasurementOutcome(index, probability, DensityMatrix(post, state.basis))


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def encode_state(state):
    _require(state, StateVector)
    data = state.data.astype("<c16").tobytes()
    record = {"schema": STATE_SCHEMA, "dtype": "<c16", "shape": [state.basis.dimension],
              "basis": {"qubits": state.basis.qubits, "order": state.basis.order},
              "normalization": "reject_atol_1e-10", "data_hex": data.hex(), "payload_sha256": _digest(data)}
    record["interpretation_sha256"] = _digest(_canonical(record))
    return record


def decode_state(record):
    if not isinstance(record, dict) or set(record) != {"schema", "dtype", "shape", "basis", "normalization",
                                                     "data_hex", "payload_sha256", "interpretation_sha256"}:
        raise ValueError("exact versioned state record required")
    if record["schema"] != STATE_SCHEMA or record["dtype"] != "<c16" or record["normalization"] != "reject_atol_1e-10":
        raise ValueError("unsupported schema, encoding or admission policy")
    if not isinstance(record["basis"], dict) or set(record["basis"]) != {"qubits", "order"}:
        raise ValueError("exact basis metadata required")
    basis = Basis(record["basis"]["qubits"], record["basis"]["order"])
    if (type(record["shape"]) is not list or len(record["shape"]) != 1
            or type(record["shape"][0]) is not int or record["shape"] != [basis.dimension]):
        raise ValueError("basis shape mismatch")
    data = _decode_hex(record["data_hex"], basis.dimension * 16)
    if _digest(data) != record["payload_sha256"]:
        raise ValueError("payload integrity failure")
    unsigned = {k: v for k, v in record.items() if k != "interpretation_sha256"}
    if _digest(_canonical(unsigned)) != record["interpretation_sha256"]:
        raise ValueError("interpretation integrity failure")
    return StateVector(np.frombuffer(data, dtype="<c16"), basis)


def _decode_hex(text, size):
    if not isinstance(text, str) or len(text) != size * 2:
        raise ValueError("exact bounded payload length required")
    try:
        data = bytes.fromhex(text)
    except ValueError as exc:
        raise ValueError("invalid hexadecimal payload") from exc
    if len(data) != size:
        raise ValueError("payload size mismatch")
    return data


def admit_v3_seed(record):
    """Explicit import of the immutable seed's complex-f64-le/1 contract."""
    if not isinstance(record, dict) or set(record) != {"schema", "qubits", "basis_order", "raw"}:
        raise ValueError("exact V3 seed record required")
    if record["schema"] != "complex-f64-le/1" or record["basis_order"] != "index_i_is_basis_i; qubit_0_lsb":
        raise ValueError("unsupported V3 seed schema or basis order")
    basis = Basis(record["qubits"])
    raw = record["raw"]
    if not isinstance(raw, dict) or set(raw) != {"sha256", "length", "hex", "bit_order", "endianness"}:
        raise ValueError("exact seed source record required")
    if (type(raw["length"]) is not int or raw["length"] != basis.dimension * 16
            or raw["bit_order"] != "msb0 per byte" or raw["endianness"] != "not_applicable_for_opaque_bytes"):
        raise ValueError("unsupported seed byte interpretation")
    data = _decode_hex(raw["hex"], raw["length"])
    if _digest(data) != raw["sha256"]:
        raise ValueError("seed payload integrity failure")
    return StateVector(np.frombuffer(data, dtype="<c16"), basis)
