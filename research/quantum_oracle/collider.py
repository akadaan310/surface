"""Bounded CERN educational dimuon CSV adapter; no detector or ROOT claims."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import argparse
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import tempfile
import time
import zlib

import numpy as np

SCHEMA = "quantum-oracle.collider-csv/1"
SOURCE_URL = "https://opendata.cern.ch/record/5201/files/Dimuon_DoubleMu.csv"
RECORD_URL = "https://opendata.cern.ch/record/5201"
SOURCE_SIZE = 13935840
SOURCE_ADLER32 = "5b87a72a"
SOURCE_SHA256 = "58caa45c580f8bcf4b457281c8525a56de0e0b8eb0e0b29e86a9b655a8e64d35"
MAX_BYTES = 16*1024*1024
MAX_EVENTS = 100000
MAX_COMPONENT = 1e6
HEADER = b"Run,Event,type1,E1,px1,py1,pz1,pt1,eta1,phi1,Q1,type2,E2,px2,py2,pz2,pt2,eta2,phi2,Q2,M"
DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]{1,2})?\Z")
UINT = re.compile(r"(?:0|[1-9][0-9]*)\Z")
UNIT = "GeV;c=1"


class ColliderError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(f"{code}: {detail}")


def _fail(code, detail):
    raise ColliderError(code, detail)


def _real(x, name, limit=MAX_COMPONENT):
    if isinstance(x, (bool, complex, str)) or not isinstance(x, (int, float, np.integer, np.floating)):
        _fail("TYPE", f"{name} requires a real numeric value")
    try:
        x = float(x)
    except (ValueError, OverflowError):
        _fail("FINITE", f"{name} cannot be represented as binary64")
    if not math.isfinite(x) or abs(x) > limit:
        _fail("FINITE", f"{name} must be finite with magnitude at most {limit}")
    return x


@dataclass(frozen=True)
class Limits:
    max_bytes: int = MAX_BYTES
    max_events: int = MAX_EVENTS
    max_line: int = 1024
    max_seconds: float = 60
    max_counterexamples: int = 4096

    def __post_init__(self):
        for name, cap in (("max_bytes", MAX_BYTES), ("max_events", MAX_EVENTS), ("max_line", 1024),
                          ("max_counterexamples", 4096)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= cap:
                _fail("RESOURCE_LIMIT", f"{name} must be an integer in 1..{cap}")
        seconds = _real(self.max_seconds, "max_seconds", 60)
        if seconds <= 0:
            _fail("RESOURCE_LIMIT", "time budget must be positive and at most 60s")


class Budget:
    def __init__(self, seconds=60):
        seconds = _real(seconds, "seconds", 60)
        if seconds <= 0:
            _fail("RESOURCE_LIMIT", "time budget must be positive and at most 60s")
        self.deadline = time.monotonic()+seconds

    def check(self):
        if time.monotonic() >= self.deadline:
            _fail("TIME_LIMIT", "fixed operation deadline exhausted")


def decimal_half_step(token):
    """Half the last represented decimal place; a rounding assumption, not detector error."""
    if not isinstance(token, str) or len(token) > 32 or DECIMAL.fullmatch(token) is None:
        _fail("FORMAT", "unsupported finite decimal token")
    exponent = Decimal(token).as_tuple().exponent
    if not -16 <= exponent <= 6:
        _fail("PRECISION", "decimal exponent outside [-16,6]")
    return .5*10.**exponent


@dataclass(frozen=True)
class FourMomentum:
    energy: float
    px: float
    py: float
    pz: float
    rounding: tuple = (0., 0., 0., 0.)
    unit: str = UNIT

    def __post_init__(self):
        for name in ("energy", "px", "py", "pz"):
            object.__setattr__(self, name, _real(getattr(self, name), name))
        if self.energy < 0:
            _fail("ENERGY", "negative energy is outside the observed-candidate contract")
        if self.unit != UNIT:
            _fail("UNIT", "only GeV with c=1 is admitted; no implicit conversion")
        if not isinstance(self.rounding, (tuple, list)) or len(self.rounding) != 4:
            _fail("SHAPE", "rounding requires four component half-widths")
        errors = tuple(_real(x, "rounding") for x in self.rounding)
        if any(x < 0 for x in errors):
            _fail("PRECISION", "negative rounding half-width")
        object.__setattr__(self, "rounding", errors)

    @property
    def components(self):
        return self.energy, self.px, self.py, self.pz

    def __add__(self, other):
        if not isinstance(other, FourMomentum):
            _fail("TYPE", "four-momenta may only be added to four-momenta")
        return FourMomentum(*(a+b for a, b in zip(self.components, other.components)),
                            rounding=tuple(a+b for a, b in zip(self.rounding, other.rounding)))

    def mass_squared(self):
        return math.fsum((self.energy*self.energy, -self.px*self.px, -self.py*self.py, -self.pz*self.pz))

    def mass_squared_error(self):
        quantization = math.fsum(2*abs(x)*d+d*d for x, d in zip(self.components, self.rounding))
        numerical = 64*np.finfo(float).eps*max(1., math.fsum(x*x for x in self.components))
        return quantization+numerical

    def mass(self):
        squared = self.mass_squared()
        if squared < 0:
            _fail("SPACELIKE", "printed central four-vector has no real invariant mass; no clipping")
        return math.sqrt(squared)

    def mass_interval(self):
        squared, delta = self.mass_squared(), self.mass_squared_error()
        if squared+delta < 0:
            return None
        return (math.sqrt(max(0., squared-delta)), math.sqrt(squared+delta))

    def boost(self, beta):
        """Passive boost to a frame moving at beta*c; synthetic kinematic operation."""
        if not isinstance(beta, (tuple, list)) or len(beta) != 3:
            _fail("SHAPE", "boost requires three beta coordinates")
        b = np.asarray(tuple(_real(x, "beta", 1) for x in beta))
        b2 = float(b @ b)
        if b2 >= 1-1e-12:
            _fail("BOOST", "boost speed must satisfy beta² < 1-1e-12")
        if b2 == 0:
            return self
        gamma = 1/math.sqrt(1-b2)
        # Linear transform also propagates interval half-widths conservatively.
        matrix = np.eye(4)
        matrix[0, 0] = gamma
        matrix[0, 1:] = matrix[1:, 0] = -gamma*b
        matrix[1:, 1:] += gamma*gamma/(gamma+1)*np.outer(b, b)
        transformed = matrix @ self.components
        rounding = abs(matrix) @ self.rounding
        return FourMomentum(*transformed, rounding=tuple(rounding))


@dataclass(frozen=True)
class Muon:
    kind: str
    momentum: FourMomentum
    pt: float
    eta: float
    phi: float
    charge: int

    def __post_init__(self):
        if self.kind not in ("G", "T") or not isinstance(self.momentum, FourMomentum):
            _fail("TYPE", "muon requires kind G/T and a four-momentum")
        for name in ("pt", "eta", "phi"):
            object.__setattr__(self, name, _real(getattr(self, name), name))
        if self.pt < 0 or type(self.charge) is not int or self.charge not in (-1, 1):
            _fail("MUON", "pt must be nonnegative and charge must be -1 or +1")


@dataclass(frozen=True)
class Event:
    run: int
    event: int
    muon1: Muon
    muon2: Muon
    published_mass: float
    mass_rounding: float
    source_sha256: str
    row_index: int
    byte_start: int
    byte_end: int
    field_spans: tuple

    def __post_init__(self):
        for name in ("run", "event"):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value < 2**64:
                _fail("ID", "run/event must be exact unsigned 64-bit integers")
        if not isinstance(self.muon1, Muon) or not isinstance(self.muon2, Muon):
            _fail("TYPE", "event requires two typed muon records")
        for name in ("published_mass", "mass_rounding"):
            value = _real(getattr(self, name), name)
            if value < 0:
                _fail("MASS", "published mass and rounding must be nonnegative")
        if not isinstance(self.source_sha256, str) or re.fullmatch("[0-9a-f]{64}", self.source_sha256) is None:
            _fail("SOURCE_IDENTITY", "event source requires a SHA-256 identity")
        if any(type(x) is not int for x in (self.row_index, self.byte_start, self.byte_end)) or not (
                0 <= self.row_index < MAX_EVENTS and 0 <= self.byte_start < self.byte_end <= MAX_BYTES):
            _fail("SOURCE_SPAN", "invalid event index or source byte interval")
        if not isinstance(self.field_spans, (tuple, list)) or len(self.field_spans) != 21:
            _fail("SOURCE_SPAN", "exactly 21 field spans are required")
        spans = []
        for pair in self.field_spans:
            if not isinstance(pair, (tuple, list)) or len(pair) != 2 or any(type(i) is not int for i in pair):
                _fail("SOURCE_SPAN", "field spans require integer offset pairs")
            if not self.byte_start <= pair[0] < pair[1] <= self.byte_end:
                _fail("SOURCE_SPAN", "field span outside event")
            spans.append(tuple(pair))
        object.__setattr__(self, "field_spans", tuple(spans))


def _id(token):
    if len(token) > 20 or UINT.fullmatch(token) is None:
        _fail("ID", "run/event token is not an exact unsigned integer")
    result = int(token)
    if result >= 2**64:
        _fail("ID", "run/event exceeds unsigned 64-bit range")
    return result


def iter_events(source, limits=None, budget=None):
    limits = Limits() if limits is None else limits
    if not isinstance(limits, Limits):
        _fail("TYPE", "limits must be Limits")
    budget = Budget(limits.max_seconds) if budget is None else budget
    if not isinstance(budget, Budget):
        _fail("TYPE", "budget must be Budget")
    budget.check()
    if not isinstance(source, bytes) or not 1 <= len(source) <= limits.max_bytes:
        _fail("RESOURCE_LIMIT", "source must be nonempty bytes within byte budget")
    source_hash = hashlib.sha256(source).hexdigest()
    stream = io.BytesIO(source)
    header = stream.readline(limits.max_line+1)
    if header.removesuffix(b"\n").removesuffix(b"\r") != HEADER:
        _fail("FORMAT", "header does not match the fixed 21-column schema")
    index = 0
    while stream.tell() < len(source):
        budget.check()
        if index >= limits.max_events:
            _fail("RESOURCE_LIMIT", "event row budget exhausted")
        start = stream.tell()
        raw = stream.readline(limits.max_line+1)
        if len(raw) > limits.max_line:
            _fail("RESOURCE_LIMIT", "row exceeds line byte budget")
        line = raw.removesuffix(b"\n").removesuffix(b"\r")
        try:
            tokens = line.decode("ascii").split(",")
        except UnicodeError as exc:
            raise ColliderError("FORMAT", "only ASCII source tokens are supported") from exc
        if len(tokens) != 21:
            _fail("FORMAT", "event row must have exactly 21 unquoted columns")
        spans, cursor = [], start
        for token in tokens:
            spans.append((cursor, cursor+len(token)))
            cursor += len(token)+1
        def number(i):
            decimal_half_step(tokens[i])
            return _real(float(tokens[i]), HEADER.decode().split(",")[i])
        def muon(offset):
            values = tuple(number(offset+j) for j in range(1, 5))
            errors = tuple(decimal_half_step(tokens[offset+j]) for j in range(1, 5))
            if tokens[offset+8] not in ("-1", "1"):
                _fail("MUON", "charge token must be -1 or 1")
            return Muon(tokens[offset], FourMomentum(*values, rounding=errors),
                        number(offset+5), number(offset+6), number(offset+7), int(tokens[offset+8]))
        yield Event(_id(tokens[0]), _id(tokens[1]), muon(2), muon(11), number(20),
                    decimal_half_step(tokens[20]), source_hash, index, start, stream.tell(), tuple(spans))
        index += 1
    if index == 0:
        _fail("FORMAT", "source contains no event rows")
    budget.check()


def compare_mass(event):
    if not isinstance(event, Event):
        _fail("TYPE", "mass comparison requires an Event")
    total = event.muon1.momentum+event.muon2.momentum
    m2 = total.mass_squared()
    interval = total.mass_interval()
    published = [max(0., event.published_mass-event.mass_rounding), event.published_mass+event.mass_rounding]
    overlap = interval is not None and interval[1] >= published[0] and interval[0] <= published[1]
    return {"run": event.run, "event": event.event, "row_index": event.row_index,
            "byte_start": event.byte_start, "byte_end": event.byte_end,
            "mass_squared_GeV2": m2, "central_mass_GeV": math.sqrt(m2) if m2 >= 0 else None,
            "central_mass_status": "REAL" if m2 >= 0 else "SPACELIKE_PRINTED_INPUT",
            "mass_interval_GeV": list(interval) if interval is not None else None,
            "published_mass_GeV": event.published_mass, "published_interval_GeV": published,
            "rounding_intervals_overlap": bool(overlap)}


def vectorized_pair_mass_squared(momentum):
    if not isinstance(momentum, np.ndarray) or momentum.ndim != 3 or momentum.shape[1:] != (2, 4):
        _fail("SHAPE", "momentum requires ndarray shape (events,2,4)")
    if not 1 <= momentum.shape[0] <= MAX_EVENTS:
        _fail("RESOURCE_LIMIT", "event array exceeds budget")
    # Comparing signed bounds avoids abs(INT_MIN) wrapping in integer dtypes.
    if (momentum.dtype.kind not in "iuf" or not np.all(np.isfinite(momentum))
            or np.any(momentum < -MAX_COMPONENT) or np.any(momentum > MAX_COMPONENT)):
        _fail("TYPE", "finite real four-momenta within component bounds required")
    if np.any(momentum[:, :, 0] < 0):
        _fail("ENERGY", "negative energy")
    total = np.asarray(momentum, dtype=np.float64).sum(axis=1)
    return total[:, 0]**2 - np.einsum("ij,ij->i", total[:, 1:], total[:, 1:])


def verify_published_source(source):
    if not isinstance(source, bytes) or len(source) != SOURCE_SIZE:
        _fail("SOURCE_IDENTITY", "CERN record 5201 byte count differs")
    adler = f"{zlib.adler32(source)&0xffffffff:08x}"
    digest = hashlib.sha256(source).hexdigest()
    if adler != SOURCE_ADLER32 or digest != SOURCE_SHA256:
        _fail("SOURCE_IDENTITY", "published Adler32 or pinned local SHA-256 differs")
    return {"bytes": len(source), "adler32": adler, "sha256": digest}


def read_source(path, limits=None):
    limits = Limits() if limits is None else limits
    if not isinstance(limits, Limits):
        _fail("TYPE", "limits must be Limits")
    budget = Budget(limits.max_seconds)
    path = Path(path)
    if path.stat().st_size > limits.max_bytes:
        _fail("RESOURCE_LIMIT", "stored source exceeds byte budget")
    try:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rb") as stream:
            source = stream.read(limits.max_bytes+1)
    except (OSError, EOFError) as exc:
        raise ColliderError("FORMAT", "source decompression or read failed") from exc
    if len(source) > limits.max_bytes:
        _fail("RESOURCE_LIMIT", "decompressed source exceeds byte budget")
    budget.check()
    return source


def deterministic_gzip(source):
    if not isinstance(source, bytes) or len(source) > MAX_BYTES:
        _fail("RESOURCE_LIMIT", "gzip input must be bytes within 16MiB")
    stream = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0, compresslevel=9) as writer:
        writer.write(source)
    return stream.getvalue()


def download_published(max_seconds=60):
    """Fixed-source curl download with both wall-clock and byte ceilings; no credentials."""
    budget = Budget(max_seconds)
    with tempfile.TemporaryDirectory(prefix="quantum-oracle-cern5201-") as directory:
        path = Path(directory)/"source.csv"
        command = ["curl", "--fail", "--silent", "--show-error", "--location", "--max-time",
                   str(max_seconds), "--max-filesize", str(MAX_BYTES), SOURCE_URL, "--output", str(path)]
        try:
            result = subprocess.run(command, capture_output=True, timeout=max_seconds, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ColliderError("DOWNLOAD_BLOCKED", "bounded CERN transport failed") from exc
        budget.check()
        if result.returncode:
            _fail("DOWNLOAD_BLOCKED", f"curl exited {result.returncode}")
        source = read_source(path)
        verify_published_source(source)
        budget.check()
        return source


def analyze(source, limits=None, require_published=True):
    limits = Limits() if limits is None else limits
    if not isinstance(limits, Limits) or type(require_published) is not bool:
        _fail("TYPE", "analysis requires typed Limits and Boolean require_published")
    if not isinstance(source, bytes) or not 1 <= len(source) <= limits.max_bytes:
        _fail("RESOURCE_LIMIT", "source must be nonempty bytes within byte budget")
    budget = Budget(limits.max_seconds)
    identity = verify_published_source(source) if require_published else {"sha256": hashlib.sha256(source).hexdigest()}
    scalar = np.empty(limits.max_events)
    momentum = np.empty((limits.max_events, 2, 4))
    counterexamples, negative_pairs, muon_counterexamples = [], [], []
    unique_ids, duplicate_rows, selection_violations = set(), 0, 0
    negative_muons, outside_muons, first_byte, last_byte, count = 0, 0, None, None, 0
    max_error, first_identity, last_identity = 0., None, None
    for event in iter_events(source, limits=limits, budget=budget):
        report = compare_mass(event)
        scalar[count] = report["mass_squared_GeV2"]
        momentum[count] = (event.muon1.momentum.components, event.muon2.momentum.components)
        if first_byte is None:
            first_byte, first_identity = event.byte_start, [event.run, event.event]
        last_byte, last_identity = event.byte_end, [event.run, event.event]
        if not report["rounding_intervals_overlap"]:
            counterexamples.append(report)
        if report["central_mass_GeV"] is None:
            negative_pairs.append(report)
        else:
            max_error = max(max_error, abs(report["central_mass_GeV"]-event.published_mass))
        for which, muon in enumerate((event.muon1, event.muon2), 1):
            m2, bound = muon.momentum.mass_squared(), muon.momentum.mass_squared_error()
            negative_muons += m2 < 0
            if m2 < -bound:
                outside_muons += 1
                muon_counterexamples.append({"row_index": count, "run": event.run, "event": event.event,
                    "muon": which, "mass_squared_GeV2": m2, "rounding_bound_GeV2": bound,
                    "byte_start": event.byte_start, "byte_end": event.byte_end})
        if len(counterexamples)+len(negative_pairs)+len(muon_counterexamples) > limits.max_counterexamples:
            _fail("RESOURCE_LIMIT", "counterexample retention budget exhausted; no truncated success report")
        pair = (event.run, event.event)
        duplicate_rows += pair in unique_ids
        unique_ids.add(pair)
        selection_violations += not (abs(event.muon1.eta) < 2.4 and abs(event.muon2.eta) < 2.4
            and "G" in (event.muon1.kind, event.muon2.kind) and event.muon1.charge != event.muon2.charge
            and .3 < event.published_mass < 300)
        count += 1
    budget.check()
    if require_published and count != 100000:
        _fail("SOURCE_IDENTITY", "published event-row count differs")
    # Second parser and numerical implementation: NumPy text reader, with IDs
    # deliberately excluded to avoid losing exact integer identity in floats.
    try:
        independently_read = np.loadtxt(io.BytesIO(source), delimiter=",", skiprows=1,
            usecols=(3, 4, 5, 6, 12, 13, 14, 15), ndmin=2).reshape(count, 2, 4)
    except (ValueError, TypeError) as exc:
        raise ColliderError("INDEPENDENT_READER", "NumPy could not read the admitted source") from exc
    reader_equal = np.array_equal(independently_read, momentum[:count])
    vector = vectorized_pair_mass_squared(independently_read)
    total = momentum[:count].sum(axis=1)
    tolerance = 64*np.finfo(float).eps*np.maximum(1., (total*total).sum(axis=1))
    residual = abs(scalar[:count]-vector)
    budget.check()
    return {"schema": SCHEMA,
        "evidence_class": "observed derived educational CSV" if require_published else "unverified user-supplied controlled input",
        "published_source_verified": require_published,
        "source_sha256": identity["sha256"], "source_url": SOURCE_URL if require_published else None, "event_rows": count,
        "units": {"four_momentum": UNIT, "mass": "GeV (c=1)", "metric": "+---"},
        "source_coverage": {"first_byte": first_byte, "last_byte": last_byte,
                            "first_run_event": first_identity, "last_run_event": last_identity},
        "unique_run_event_pairs": len(unique_ids), "duplicate_run_event_rows": duplicate_rows,
        "published_selection_violations_in_printed_values": selection_violations,
        "independent_reader": {"status": "ACCEPT" if reader_equal and np.all(residual <= tolerance) else "REJECT",
            "reader": "numpy.loadtxt", "reference": "typed scalar parser + math.fsum",
            "component_arrays_exactly_equal": reader_equal, "compared_rows": count,
            "max_mass_squared_difference_GeV2": float(residual.max()),
            "tolerance_rule": "64*binary64_epsilon*max(1,sum(total_four_vector_components**2))"},
        "mass_comparison": {"status": "REJECT" if counterexamples else "ACCEPT",
            "claim": "all published masses compatible with printed four-momenta under decimal-rounding assumption",
            "outside_rounding_intervals": len(counterexamples), "compatible_rows": count-len(counterexamples),
            "negative_central_mass_squared": len(negative_pairs), "max_real_central_mass_difference_GeV": max_error,
            "assumption": "each decimal was rounded to nearest at its displayed final place; no detector uncertainty implied"},
        "individual_muons": {"negative_central_mass_squared": negative_muons, "spacelike_beyond_rounding": outside_muons},
        "counterexamples": counterexamples, "negative_pair_counterexamples": negative_pairs,
        "muon_spacelike_counterexamples": muon_counterexamples,
        "full_G4_acceptance": False, "remaining": ["ROOT/HepMC", "detector calibration and response",
            "event weights and systematic uncertainties", "full physics analysis", "independent external physics library"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.input) == args.download:
        parser.error("select exactly one of --input and --download")
    source = download_published() if args.download else read_source(args.input)
    identity = verify_published_source(source)
    if args.archive:
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        with args.archive.open("xb") as stream:
            stream.write(deterministic_gzip(source))
    start = time.monotonic()
    report = analyze(source)
    report["execution"] = {"python": platform.python_version(), "numpy": np.__version__,
        "platform": platform.platform(), "utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": time.monotonic()-start, "source_identity": identity,
        "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"event_rows": report["event_rows"], "mass_comparison": report["mass_comparison"],
                      "independent_reader": report["independent_reader"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
