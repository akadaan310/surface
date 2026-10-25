"""Finite compiler for historical IBM snapshot subgraphs; no provider calls."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.circuit.library import ECRGate, IGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target

from . import quantum as q

CONFIG_SHA256 = "309836dbf54cf635d811a273a3b4e1c933debdbea71c33b689ea1b71deafc2d2"
PROPERTIES_SHA256 = "bc8b29433a8e1935a8f5537cafccc63194dc5ed5137edba684ff3fb77b269d1d"
SOURCE_REVISION = "1dd86e381ddecfc78db94e3287a9ce57e4ad65d8"
NATIVE_GATES = ("ecr", "id", "rz", "sx", "x")
MAX_INPUT_OPERATIONS = 32
MAX_OUTPUT_OPERATIONS = 256


def _date(value):
    if type(value) is not str or len(value) > 64:
        raise ValueError("bounded explicit timezone date required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid calibration date") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("calibration date requires timezone")
    return parsed.astimezone(timezone.utc)


def _sha(value, length=64):
    if type(value) is not str or re.fullmatch(f"[0-9a-f]{{{length}}}", value) is None:
        raise ValueError("exact hexadecimal source digest required")


def _probability(value):
    value = q._real(value, "calibration probability")
    if not 0 <= value <= 1:
        raise ValueError("calibration probability outside [0,1]")
    return value


def _json_bytes(data, expected):
    if type(data) is not bytes or not 1 <= len(data) <= 1_048_576:
        raise ValueError("snapshot bytes exceed 1 MiB bound")
    _sha(expected)
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("snapshot digest mismatch")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate snapshot JSON key")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError("nonfinite JSON calibration")
    result = json.loads(data, object_pairs_hook=pairs, parse_constant=reject_constant)
    if type(result) is not dict:
        raise ValueError("snapshot object required")
    return result


@dataclass(frozen=True)
class GateCalibration:
    name: str
    physical_qubits: tuple
    duration_seconds: float
    error: float
    measured_at: str

    def __post_init__(self):
        if self.name not in NATIVE_GATES or type(self.physical_qubits) is not tuple:
            raise ValueError("supported native gate calibration required")
        if len(self.physical_qubits) != (2 if self.name == "ecr" else 1) or len(set(self.physical_qubits)) != len(self.physical_qubits):
            raise ValueError("native gate arity")
        for index in self.physical_qubits:
            q._integer(index, 0, 511, "provider site")
        duration = q._real(self.duration_seconds, "gate duration")
        if not 0 <= duration <= 1:
            raise ValueError("gate duration bound")
        _probability(self.error)
        _date(self.measured_at)


@dataclass(frozen=True)
class QubitCalibration:
    physical_qubit: int
    t1_seconds: float
    t2_seconds: float
    prob_meas1_prep0: float
    prob_meas0_prep1: float
    measured_at: str

    def __post_init__(self):
        q._integer(self.physical_qubit, 0, 511, "provider site")
        for value in (self.t1_seconds, self.t2_seconds):
            if not 0 < q._real(value, "coherence time") <= 100:
                raise ValueError("positive bounded coherence time required")
        _probability(self.prob_meas1_prep0)
        _probability(self.prob_meas0_prep1)
        _date(self.measured_at)


@dataclass(frozen=True)
class CalibrationSnapshot:
    backend_name: str
    calibration_at: str
    acquired_at: str
    source_revision: str
    config_sha256: str
    properties_sha256: str
    physical_qubits: tuple
    native_gates: tuple
    couplings: tuple
    gates: tuple
    qubits: tuple
    config_source: bytes = field(repr=False)
    properties_source: bytes = field(repr=False)
    current_calibration: bool = False

    def __post_init__(self):
        q._label(self.backend_name, "backend")
        if _date(self.calibration_at) > _date(self.acquired_at) or self.current_calibration is not False:
            raise ValueError("only historical snapshots are admitted")
        _sha(self.source_revision, 40)
        _sha(self.config_sha256)
        _sha(self.properties_sha256)
        if type(self.physical_qubits) is not tuple or not 1 <= len(self.physical_qubits) <= 4:
            raise ValueError("select 1..4 physical qubits")
        for index in self.physical_qubits:
            q._integer(index, 0, 511, "provider site")
        if len(set(self.physical_qubits)) != len(self.physical_qubits):
            raise ValueError("duplicate physical site")
        if self.native_gates != NATIVE_GATES or type(self.gates) is not tuple or type(self.qubits) is not tuple or type(self.couplings) is not tuple:
            raise ValueError("immutable supported target records required")
        if len(self.gates) > 32 or len(self.qubits) != len(self.physical_qubits) or len(self.couplings) > 12:
            raise ValueError("selected snapshot record budget")
        if len(set(self.couplings)) != len(self.couplings):
            raise ValueError("duplicate selected couplings")
        if tuple(cal.physical_qubit for cal in self.qubits) != self.physical_qubits:
            raise ValueError("qubit calibration order mismatch")
        for cal in self.qubits:
            q._require(cal, QubitCalibration)
            if _date(cal.measured_at) > _date(self.calibration_at):
                raise ValueError("future qubit sample")
        identifiers = []
        for cal in self.gates:
            q._require(cal, GateCalibration)
            if _date(cal.measured_at) > _date(self.calibration_at):
                raise ValueError("future gate sample")
            if not set(cal.physical_qubits) <= set(self.physical_qubits):
                raise ValueError("gate outside selected subgraph")
            identifiers.append((cal.name, cal.physical_qubits))
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("duplicate gate calibration")
        if set(self.couplings) != {cal.physical_qubits for cal in self.gates if cal.name == "ecr"}:
            raise ValueError("directed coupling and ECR calibration mismatch")
        for site in self.physical_qubits:
            for name in ("id", "rz", "sx", "x"):
                self.gate(name, (site,))
        reached = {self.physical_qubits[0]}
        for _ in self.physical_qubits:
            for edge in self.couplings:
                if set(edge) & reached:
                    reached.update(edge)
        if reached != set(self.physical_qubits):
            raise ValueError("selected subgraph is disconnected")
        # Re-derive selected semantics from the immutable hash-bound bytes. A
        # caller cannot retain an authentic source hash while editing its model.
        expected = _snapshot_fields(self.config_source, self.properties_source,
                                    physical_qubits=self.physical_qubits, source_revision=self.source_revision,
                                    acquired_at=self.acquired_at, expected_config_sha256=self.config_sha256,
                                    expected_properties_sha256=self.properties_sha256)
        actual = (self.backend_name, self.calibration_at, self.acquired_at, self.source_revision,
                  self.config_sha256, self.properties_sha256, self.physical_qubits, self.native_gates,
                  self.couplings, self.gates, self.qubits)
        if actual != expected:
            raise ValueError("snapshot semantics do not match the hash-bound source bytes")

    @property
    def hardware_sites(self):
        return tuple(q.HardwareQubit("ibm", self.backend_name, str(site), self.properties_sha256) for site in self.physical_qubits)

    def gate(self, name, physical_qubits):
        for cal in self.gates:
            if cal.name == name and cal.physical_qubits == physical_qubits:
                return cal
        raise ValueError("native operation lacks a selected calibration")


def _parameters(rows, calibration_date):
    if type(rows) is not list or len(rows) > 64:
        raise ValueError("bounded calibration parameter list required")
    result = {}
    for row in rows:
        if type(row) is not dict or not {"name", "value", "unit", "date"} <= set(row):
            raise ValueError("calibration parameter fields required")
        name = row["name"]
        q._label(name, "calibration parameter")
        if name in result or _date(row["date"]) > calibration_date:
            raise ValueError("duplicate parameter or future calibration sample")
        q._real(row["value"], "calibration value")
        result[name] = row
    return result


def _seconds(parameter):
    factor = {"s": 1.0, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}.get(parameter["unit"])
    if factor is None:
        raise ValueError("unsupported explicit time unit")
    return q._real(parameter["value"], "time value") * factor


def _unitless(parameter):
    if parameter["unit"] != "":
        raise ValueError("dimensionless calibration required")
    return _probability(parameter["value"])


def _snapshot_fields(config_bytes, properties_bytes, *, physical_qubits, source_revision, acquired_at,
                     expected_config_sha256, expected_properties_sha256):
    config = _json_bytes(config_bytes, expected_config_sha256)
    props = _json_bytes(properties_bytes, expected_properties_sha256)
    if not {"backend_name", "n_qubits", "basis_gates", "coupling_map"} <= set(config) or not {"backend_name", "last_update_date", "qubits", "gates"} <= set(props):
        raise ValueError("required snapshot fields missing")
    _sha(source_revision, 40)
    acquired = _date(acquired_at)
    calibration_date = _date(props["last_update_date"])
    if calibration_date > acquired:
        raise ValueError("calibration postdates acquisition")
    n = q._integer(config["n_qubits"], 1, 512, "provider qubit count")
    if props["backend_name"] != config["backend_name"] or tuple(config["basis_gates"]) != NATIVE_GATES:
        raise ValueError("backend identity or supported native-gate set mismatch")
    if type(physical_qubits) is not tuple or not 1 <= len(physical_qubits) <= 4:
        raise ValueError("select 1..4 physical sites")
    for site in physical_qubits:
        q._integer(site, 0, n - 1, "physical site")
    if len(set(physical_qubits)) != len(physical_qubits):
        raise ValueError("duplicate selected physical sites")
    if type(config["coupling_map"]) is not list or len(config["coupling_map"]) > 2048:
        raise ValueError("coupling-map bound")
    couplings = []
    for edge in config["coupling_map"]:
        if type(edge) is not list or len(edge) != 2:
            raise ValueError("binary directed coupling required")
        for site in edge:
            q._integer(site, 0, n - 1, "coupler site")
        if edge[0] == edge[1]:
            raise ValueError("self coupler rejected")
        if set(edge) <= set(physical_qubits):
            couplings.append(tuple(edge))
    if len(set(couplings)) != len(couplings):
        raise ValueError("duplicate coupler")
    if type(props["qubits"]) is not list or len(props["qubits"]) != n:
        raise ValueError("qubit calibration count mismatch")
    qubits = []
    for site in physical_qubits:
        params = _parameters(props["qubits"][site], calibration_date)
        if not {"T1", "T2", "prob_meas1_prep0", "prob_meas0_prep1"} <= set(params):
            raise ValueError("required qubit calibration missing")
        qubits.append(QubitCalibration(site, _seconds(params["T1"]), _seconds(params["T2"]),
                                        _unitless(params["prob_meas1_prep0"]), _unitless(params["prob_meas0_prep1"]),
                                        max(_date(p["date"]) for p in params.values()).isoformat()))
    if type(props["gates"]) is not list or len(props["gates"]) > 8192:
        raise ValueError("gate calibration count bound")
    gates = []
    for gate in props["gates"]:
        if type(gate) is not dict or type(gate.get("qubits")) is not list or not 1 <= len(gate["qubits"]) <= 2:
            raise ValueError("invalid gate calibration arity")
        for site in gate["qubits"]:
            q._integer(site, 0, n - 1, "gate site")
        sites = tuple(gate["qubits"])
        if not set(sites) <= set(physical_qubits) or gate.get("gate") not in NATIVE_GATES:
            continue
        params = _parameters(gate.get("parameters"), calibration_date)
        if not {"gate_length", "gate_error"} <= set(params):
            raise ValueError("required native gate calibration missing")
        gates.append(GateCalibration(gate["gate"], sites, _seconds(params["gate_length"]), _unitless(params["gate_error"]),
                                     max(_date(p["date"]) for p in params.values()).isoformat()))
    return (config["backend_name"], calibration_date.isoformat(), acquired.isoformat(), source_revision,
            expected_config_sha256, expected_properties_sha256, physical_qubits, NATIVE_GATES,
            tuple(couplings), tuple(gates), tuple(qubits))


def admit_snapshot(config_bytes, properties_bytes, *, physical_qubits, source_revision, acquired_at,
                   expected_config_sha256, expected_properties_sha256):
    fields = _snapshot_fields(config_bytes, properties_bytes, physical_qubits=physical_qubits,
                              source_revision=source_revision, acquired_at=acquired_at,
                              expected_config_sha256=expected_config_sha256,
                              expected_properties_sha256=expected_properties_sha256)
    return CalibrationSnapshot(*fields, config_source=config_bytes, properties_source=properties_bytes)


def load_snapshot(directory=None, *, physical_qubits=(0, 1)):
    directory = Path(directory) if directory is not None else Path(__file__).parent / "fixtures/ibm_brisbane_snapshot"
    def bounded_read(name):
        with (directory / name).open("rb") as handle:
            return handle.read(1_048_577)
    return admit_snapshot(bounded_read("conf_brisbane.json"), bounded_read("props_brisbane.json"),
                          physical_qubits=physical_qubits, source_revision=SOURCE_REVISION,
                          acquired_at="2026-10-25T17:08:08.887359+00:00", expected_config_sha256=CONFIG_SHA256,
                          expected_properties_sha256=PROPERTIES_SHA256)


@dataclass(frozen=True)
class CircuitOp:
    name: str
    qubits: tuple
    angle: float | None = None

    def __post_init__(self):
        if self.name not in ("I", "X", "Y", "Z", "H", "S", "T", "RX", "RY", "RZ", "CX"):
            raise ValueError("unsupported logical gate")
        if type(self.qubits) is not tuple or len(self.qubits) != (2 if self.name == "CX" else 1):
            raise ValueError("typed logical gate arity")
        for qubit in self.qubits:
            q._require(qubit, q.LogicalQubit)
            q._same_basis(self.qubits[0].basis, qubit.basis)
        if len(set(self.qubits)) != len(self.qubits):
            raise ValueError("duplicate logical gate address")
        if self.name in ("RX", "RY", "RZ"):
            if abs(q._real(self.angle, "gate angle")) > q.MAX_PHASE:
                raise ValueError("gate phase budget")
        elif self.angle is not None:
            raise ValueError("angle on a non-parametric gate")


@dataclass(frozen=True)
class CircuitIR:
    basis: q.Basis
    operations: tuple

    def __post_init__(self):
        q._require(self.basis, q.Basis)
        if self.basis.order != "qubit_0_lsb" or type(self.operations) is not tuple or len(self.operations) > MAX_INPUT_OPERATIONS:
            raise ValueError("LSB circuit with at most 32 operations required")
        for op in self.operations:
            q._require(op, CircuitOp)
            q._same_basis(op.qubits[0].basis, self.basis)


@dataclass(frozen=True)
class NativeOp:
    name: str
    local_qubits: tuple
    hardware_sites: tuple
    parameters: tuple
    duration_seconds: float
    reported_gate_error: float

    def __post_init__(self):
        if self.name not in NATIVE_GATES or type(self.local_qubits) is not tuple or type(self.hardware_sites) is not tuple or type(self.parameters) is not tuple:
            raise ValueError("immutable native gate fields required")
        arity = 2 if self.name == "ecr" else 1
        if len(self.local_qubits) != arity or len(self.hardware_sites) != arity or len(set(self.local_qubits)) != arity:
            raise ValueError("native arity mismatch")
        for position in self.local_qubits:
            q._integer(position, 0, 3, "local physical slot")
        for site in self.hardware_sites:
            q._require(site, q.HardwareQubit)
        if len(self.parameters) != (1 if self.name == "rz" else 0):
            raise ValueError("native parameter count")
        for angle in self.parameters:
            if abs(q._real(angle, "native angle")) > q.MAX_PHASE:
                raise ValueError("native phase budget")
        if not 0 <= q._real(self.duration_seconds, "duration") <= 1:
            raise ValueError("native duration bound")
        _probability(self.reported_gate_error)


@dataclass(frozen=True)
class CompiledCircuit:
    source: CircuitIR
    snapshot_sha256: str
    seed: int
    native_operations: tuple
    global_phase: float
    initial_mapping: tuple
    final_mapping: tuple
    output_permutation: tuple
    logical_unitary: q.Unitary
    unitary_error: float
    serial_duration_seconds: float
    snapshot: CalibrationSnapshot = field(repr=False)

    def __post_init__(self):
        q._require(self.source, CircuitIR)
        q._require(self.logical_unitary, q.Unitary)
        q._same_basis(self.source.basis, self.logical_unitary.basis)
        q._require(self.snapshot, CalibrationSnapshot)
        if self.snapshot_sha256 != self.snapshot.properties_sha256 or self.initial_mapping != self.snapshot.hardware_sites:
            raise ValueError("compiled record must bind its admitted snapshot")
        _sha(self.snapshot_sha256)
        q._integer(self.seed, 0, (1 << 32) - 1, "seed")
        n, dimension = self.source.basis.qubits, self.source.basis.dimension
        for mapping in (self.initial_mapping, self.final_mapping):
            if type(mapping) is not tuple or len(mapping) != n or len(set(mapping)) != n:
                raise ValueError("bijective hardware mapping required")
            for site in mapping:
                q._require(site, q.HardwareQubit)
                if site.calibration_id != self.snapshot_sha256:
                    raise ValueError("mapping calibration mismatch")
        if set(self.initial_mapping) != set(self.final_mapping):
            raise ValueError("initial and final target sites differ")
        positions = tuple(self.initial_mapping.index(site) for site in self.final_mapping)
        expected_permutation = tuple(sum(((index >> bit) & 1) << position for bit, position in enumerate(positions)) for index in range(dimension))
        if type(self.output_permutation) is not tuple or self.output_permutation != expected_permutation or any(type(i) is not int for i in self.output_permutation):
            raise ValueError("output permutation does not match final hardware mapping")
        if type(self.native_operations) is not tuple or len(self.native_operations) > MAX_OUTPUT_OPERATIONS:
            raise ValueError("native operation budget")
        matrix = np.eye(dimension, dtype=complex)
        for operation in self.native_operations:
            q._require(operation, NativeOp)
            _verify_native(operation, self.snapshot)
            if any(position >= n for position in operation.local_qubits) or tuple(self.initial_mapping[position] for position in operation.local_qubits) != operation.hardware_sites:
                raise ValueError("native operation mapping mismatch")
            matrix = _embed(_native_small(operation), operation.local_qubits, n) @ matrix
        matrix *= np.exp(1j * q._real(self.global_phase, "global phase"))
        restored = matrix[list(self.output_permutation), :]
        error = float(np.max(np.abs(restored - _logical_unitary(self.source).data)))
        if error > 1e-10 or not 0 <= q._real(self.unitary_error, "unitary error") <= 1e-10 or abs(self.unitary_error - error) > 1e-14:
            raise ValueError("native circuit fails the source full-unitary witness")
        if float(np.max(np.abs(restored - self.logical_unitary.data))) > 1e-12:
            raise ValueError("stored unitary mismatch")
        if q._real(self.serial_duration_seconds, "serial duration") != sum(op.duration_seconds for op in self.native_operations):
            raise ValueError("serial duration does not match gate durations")


def _logical_unitary(ir):
    matrix = np.eye(ir.basis.dimension, dtype=complex)
    for op in ir.operations:
        operation = q.controlled_x(*op.qubits) if op.name == "CX" else q.gate(op.name, ir.basis, op.qubits[0], angle=op.angle)
        matrix = operation.data @ matrix
    return q.Unitary(matrix, ir.basis)


def _native_small(op):
    if op.name == "id":
        return np.eye(2, dtype=complex)
    if op.name == "x":
        return np.array([[0, 1], [1, 0]], complex)
    if op.name == "sx":
        return np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]) / 2
    if op.name == "rz":
        return np.diag([np.exp(-.5j * op.parameters[0]), np.exp(.5j * op.parameters[0])])
    if op.name == "ecr":
        return np.array([[0, 1, 0, 1j], [1, 0, -1j, 0], [0, 1j, 0, 1], [-1j, 0, 1, 0]]) / math.sqrt(2)
    raise ValueError("unsupported native operation")


def _embed(small, positions, count):
    dimension = 1 << count
    matrix = np.zeros((dimension, dimension), complex)
    mask = sum(1 << position for position in positions)
    for column in range(dimension):
        local_column = sum(((column >> position) & 1) << bit for bit, position in enumerate(positions))
        for local_row in range(1 << len(positions)):
            row = (column & ~mask) | sum(((local_row >> bit) & 1) << position for bit, position in enumerate(positions))
            matrix[row, column] = small[local_row, local_column]
    return matrix


def _verify_native(op, snapshot):
    q._require(op, NativeOp)
    if type(op.local_qubits) is not tuple or type(op.hardware_sites) is not tuple or type(op.parameters) is not tuple:
        raise ValueError("immutable native operation required")
    arity = 2 if op.name == "ecr" else 1
    if op.name not in NATIVE_GATES or len(op.local_qubits) != arity or len(set(op.local_qubits)) != arity:
        raise ValueError("native operation arity")
    for position in op.local_qubits:
        q._integer(position, 0, len(snapshot.physical_qubits) - 1, "local physical slot")
    if tuple(snapshot.hardware_sites[position] for position in op.local_qubits) != op.hardware_sites:
        raise ValueError("native hardware mapping mismatch")
    if len(op.parameters) != (1 if op.name == "rz" else 0):
        raise ValueError("native parameter arity")
    for value in op.parameters:
        if abs(q._real(value, "native angle")) > q.MAX_PHASE:
            raise ValueError("native angle budget")
    cal = snapshot.gate(op.name, tuple(snapshot.physical_qubits[p] for p in op.local_qubits))
    if op.duration_seconds != cal.duration_seconds or op.reported_gate_error != cal.error:
        raise ValueError("native calibration mismatch")


def compile_circuit(ir, snapshot, *, seed):
    q._require(ir, CircuitIR)
    q._require(snapshot, CalibrationSnapshot)
    q._integer(seed, 0, (1 << 32) - 1, "transpiler seed")
    if ir.basis.qubits != len(snapshot.physical_qubits):
        raise ValueError("logical register must match selected subgraph")
    n = ir.basis.qubits
    target = Target(num_qubits=n, description=f"historical {snapshot.backend_name} {snapshot.calibration_at}")
    instructions = {"id": IGate(), "rz": RZGate(Parameter("theta")), "sx": SXGate(), "x": XGate(), "ecr": ECRGate()}
    for name in NATIVE_GATES:
        properties = {}
        for cal in snapshot.gates:
            if cal.name == name:
                positions = tuple(snapshot.physical_qubits.index(site) for site in cal.physical_qubits)
                properties[positions] = InstructionProperties(duration=cal.duration_seconds, error=cal.error)
        if properties:
            target.add_instruction(instructions[name], properties)
    circuit = QuantumCircuit(n)
    for op in ir.operations:
        args = ([] if op.angle is None else [op.angle]) + [qubit.index for qubit in op.qubits]
        getattr(circuit, "id" if op.name == "I" else op.name.lower())(*args)
    started = time.monotonic()
    def budget_callback(**kwargs):
        if kwargs["count"] > 128 or time.monotonic() - started > 15:
            raise TimeoutError("cooperative transpiler pass/time budget")
    compiled = transpile(circuit, target=target, initial_layout=list(range(n)), layout_method="trivial",
                         routing_method="basic", optimization_level=0, seed_transpiler=seed,
                         approximation_degree=1.0, callback=budget_callback, num_processes=1)
    if compiled.num_qubits != n or len(compiled.data) > MAX_OUTPUT_OPERATIONS:
        raise ValueError("compiled circuit exceeds finite output budget")
    native = []
    matrix = np.eye(1 << n, dtype=complex)
    for item in compiled.data:
        name = item.operation.name
        positions = tuple(compiled.find_bit(qubit).index for qubit in item.qubits)
        sites = tuple(snapshot.physical_qubits[position] for position in positions)
        cal = snapshot.gate(name, sites)
        operation = NativeOp(name, positions, tuple(snapshot.hardware_sites[position] for position in positions),
                             tuple(float(p) for p in item.operation.params), cal.duration_seconds, cal.error)
        _verify_native(operation, snapshot)
        native.append(operation)
        matrix = _embed(_native_small(operation), positions, n) @ matrix
    phase = float(compiled.global_phase)
    matrix *= np.exp(1j * phase)
    final_positions = tuple(compiled.layout.final_index_layout()) if compiled.layout is not None else tuple(range(n))
    if len(final_positions) != n or set(final_positions) != set(range(n)):
        raise ValueError("unrecognized final-layout permutation")
    permutation = tuple(sum(((index >> bit) & 1) << position for bit, position in enumerate(final_positions)) for index in range(1 << n))
    restored = matrix[list(permutation), :]
    logical = _logical_unitary(ir)
    error = float(np.max(np.abs(restored - logical.data)))
    if error > 1e-10:
        raise ArithmeticError("compiled full unitary does not preserve logical circuit")
    return CompiledCircuit(ir, snapshot.properties_sha256, seed, tuple(native), phase, snapshot.hardware_sites,
                           tuple(snapshot.hardware_sites[position] for position in final_positions), permutation,
                           q.Unitary(restored, ir.basis), error, sum(op.duration_seconds for op in native), snapshot)


@dataclass(frozen=True)
class SurrogateResult:
    quantum_state: q.DensityMatrix
    observed_probabilities: q.ProbabilityDistribution
    serial_duration_seconds: float
    assumptions: tuple


def simulate_surrogate(compiled, snapshot):
    q._require(compiled, CompiledCircuit)
    q._require(snapshot, CalibrationSnapshot)
    if compiled.snapshot != snapshot or compiled.snapshot_sha256 != snapshot.properties_sha256 or compiled.initial_mapping != snapshot.hardware_sites:
        raise ValueError("compiled snapshot binding mismatch")
    n = len(snapshot.physical_qubits)
    basis = q.Basis(n)
    if type(compiled.native_operations) is not tuple or len(compiled.native_operations) > MAX_OUTPUT_OPERATIONS:
        raise ValueError("native operation budget")
    permutation = compiled.output_permutation
    if type(permutation) is not tuple or len(permutation) != 1 << n or set(permutation) != set(range(1 << n)):
        raise ValueError("compiled output permutation")
    rho = q.density(q.basis_lift(q.ClassicalWord(0, n), basis))
    for operation in compiled.native_operations:
        _verify_native(operation, snapshot)
        rho = q.Unitary(_embed(_native_small(operation), operation.local_qubits, n), basis).apply(rho)
        for position, cal in enumerate(snapshot.qubits):
            gamma = -math.expm1(-operation.duration_seconds / cal.t1_seconds)
            operators = (np.diag([1, math.sqrt(1 - gamma)]), np.array([[0, math.sqrt(gamma)], [0, 0]]))
            rho = q.QuantumChannel([_embed(operator, (position,), n) for operator in operators], basis).apply(rho)
    confusion = np.array([[1.0]])
    for cal in reversed(snapshot.qubits):
        local = [[1 - cal.prob_meas1_prep0, cal.prob_meas0_prep1],
                 [cal.prob_meas1_prep0, 1 - cal.prob_meas0_prep1]]
        confusion = np.kron(confusion, local)
    observed = q.StochasticMap(confusion, basis).apply(q.probabilities(rho))
    return SurrogateResult(q.DensityMatrix(rho.data[np.ix_(permutation, permutation)], basis),
                           q.ProbabilityDistribution(observed.data[list(permutation)], basis),
                           sum(op.duration_seconds for op in compiled.native_operations),
                           ("historical_snapshot_only", "serial_schedule_all_qubits_damp_each_gate", "zero_temperature_T1_amplitude_damping",
                            "independent_readout_confusion", "T2_not_modeled", "gate_error_not_converted_to_depolarizing",
                            "no_crosstalk_leakage_pulse_or_nonmarkovian_model", "no_hardware_execution"))
