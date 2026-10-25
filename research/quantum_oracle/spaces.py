"""QUANTUM ORACLE finite Euclidean function spaces, schema /1.

Standalone NumPy reference; see spaces-contract.md for measure, units and scope.
The upstream atlas_quantum seed is never imported or changed by this module.
"""
from dataclasses import dataclass
from functools import wraps
import math
from typing import ClassVar

import numpy as np

SCHEMA = "quantum-oracle.function-spaces/1"
MAX_CHARTS = 64
MAX_MODES = 256
MAX_POINTS = 4096
MAX_MODE_INDEX = 1024
TOLERANCE = 1e-12


class ContractError(ValueError):
    """Typed admission failure; code is stable, detail is descriptive."""
    def __init__(self, code, detail):
        self.code = code
        super().__init__(f"{code}: {detail}")


def _fail(code, detail):
    raise ContractError(code, detail)


def _finite_result(function):
    """Convert arithmetic range failures to contract rejection, never NaN/Inf."""
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                result = function(*args, **kwargs)
        except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as exc:
            raise ContractError("NUMERIC_RANGE", f"{function.__name__} exceeds numerical range") from exc
        if isinstance(result, (float, complex, np.number, np.ndarray)) and not np.all(np.isfinite(result)):
            _fail("NUMERIC_RANGE", f"{function.__name__} produced a nonfinite result")
        return result
    return checked


def _sized_sequence(value):
    return isinstance(value, (tuple, list)) or (isinstance(value, np.ndarray) and value.ndim > 0)


def _unit(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 64 or not value.isprintable():
        _fail("UNIT", "unit must be a nonempty printable string of at most 64 characters")
    return value


def _scalar(value, name, *, positive=False):
    if isinstance(value, (bool, complex, str)) or not isinstance(value, (int, float, np.integer, np.floating)):
        _fail("TYPE", f"{name} requires a real scalar")
    try:
        value = float(value)
    except (ValueError, OverflowError):
        _fail("FINITE", f"{name} must be finite")
    if not math.isfinite(value) or abs(value) > 1e100:
        _fail("FINITE", f"{name} must be finite and at most 1e100 in magnitude")
    if positive and value <= 0:
        _fail("DOMAIN", f"{name} must be positive")
    return value


def _array(value, shape, name, *, complex_ok=False):
    # Preflight all sequence dimensions before NumPy can allocate/coerce them.
    def visit(obj, axes):
        if axes:
            if not _sized_sequence(obj) or len(obj) != axes[0]:
                _fail("SHAPE", f"{name} requires shape {shape}")
            for item in obj:
                visit(item, axes[1:])
        else:
            if isinstance(obj, (bool, str)) or not isinstance(obj, (int, float, complex, np.number)):
                _fail("TYPE", f"{name} requires numerical values")
            if not complex_ok and isinstance(obj, (complex, np.complexfloating)):
                _fail("TYPE", f"{name} requires real values")
    if isinstance(value, np.ndarray):
        if value.shape != tuple(shape):
            _fail("SHAPE", f"{name} requires shape {shape}")
        if value.dtype.kind not in ("iufc" if complex_ok else "iuf"):
            _fail("TYPE", f"{name} has an unsupported dtype")
    else:
        visit(value, shape)
    try:
        result = np.array(value, dtype=np.complex128 if complex_ok else np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ContractError("TYPE", f"{name} cannot be represented as binary64") from exc
    if not np.all(np.isfinite(result)) or np.any(np.abs(result) > 1e100):
        _fail("FINITE", f"{name} must be finite and at most 1e100 in magnitude")
    # An immutable bytes owner prevents callers from re-enabling WRITEABLE.
    return np.frombuffer(result.tobytes(), dtype=result.dtype).reshape(result.shape)


def _points(points):
    if not _sized_sequence(points) or not 1 <= len(points) <= MAX_POINTS:
        _fail("RESOURCE_LIMIT", f"points limit is 1..{MAX_POINTS}")
    return _array(points, (len(points), 2), "points")


def _metric(value):
    m = _array(value, (2, 2), "metric")
    if not np.array_equal(m, m.T):
        _fail("METRIC", "metric must be symmetric")
    eig = np.linalg.eigvalsh(m)
    if eig[0] < 1e-12 or eig[-1] > 1e12 or eig[-1] / eig[0] > 1e12:
        _fail("METRIC", "metric must be positive definite within condition limit 1e12")
    return m


@dataclass(frozen=True)
class LocalDomain:
    """XY covering rectangle; periodic boundary identifies opposite sides."""
    lengths: tuple
    origin: tuple = (0., 0.)
    coordinate_unit: str = "m"
    boundary: str = "periodic"
    metric: tuple = ((1., 0.), (0., 1.))

    def __post_init__(self):
        lengths = _array(self.lengths, (2,), "lengths")
        if np.any(lengths < 1e-6) or np.any(lengths > 1e6):
            _fail("DOMAIN", "lengths must be in [1e-6, 1e6]")
        origin = _array(self.origin, (2,), "local origin")
        if np.any(np.spacing(np.abs(origin)) * MAX_POINTS > lengths):
            _fail("NUMERIC_RANGE", "coordinate resolution cannot represent the domain sampling budget")
        _unit(self.coordinate_unit)
        if self.boundary not in ("periodic", "closed"):
            _fail("BOUNDARY", "supported declarations are periodic or closed")
        object.__setattr__(self, "lengths", tuple(lengths))
        object.__setattr__(self, "origin", tuple(origin))
        object.__setattr__(self, "metric", tuple(map(tuple, _metric(self.metric))))

    def contains(self, point):
        p = _array(point, (2,), "point") - self.origin
        return bool(np.all(p >= 0) and np.all(p <= self.lengths))

    def intrinsic_distance(self, a, b):
        """Distance in the Euclidean covering chart, not torus geodesic distance."""
        d = _array(a, (2,), "point") - _array(b, (2,), "point")
        return float(np.sqrt(d @ np.asarray(self.metric) @ d))


@dataclass(frozen=True)
class LayoutPoint:
    position: tuple
    unit: str

    def __post_init__(self):
        object.__setattr__(self, "position", tuple(_array(self.position, (2,), "layout origin")))
        _unit(self.unit)


@dataclass(frozen=True)
class Chart:
    id: str
    domain: LocalDomain
    layout: LayoutPoint
    field: object | None = None

    def __post_init__(self):
        if not isinstance(self.id, str) or not 1 <= len(self.id) <= 128:
            _fail("ID", "chart ID requires 1..128 characters")
        if not isinstance(self.domain, LocalDomain) or not isinstance(self.layout, LayoutPoint):
            _fail("TYPE", "chart requires a local domain and separate layout point")
        if self.field is not None:
            if not isinstance(self.field, (FourierField, SquaredAmplitude)):
                _fail("TYPE", "chart field must be a Fourier state or squared-amplitude observable")
            state = self.field.field if isinstance(self.field, SquaredAmplitude) else self.field
            if state.space.domain != self.domain:
                _fail("DOMAIN", "chart and hosted field domains differ")


@dataclass(frozen=True)
class Atlas:
    charts: tuple

    def __post_init__(self):
        if not isinstance(self.charts, (tuple, list)) or not 1 <= len(self.charts) <= MAX_CHARTS:
            _fail("RESOURCE_LIMIT", f"chart limit is 1..{MAX_CHARTS}")
        if any(not isinstance(c, Chart) for c in self.charts):
            _fail("TYPE", "atlas entries must be charts")
        if len({c.id for c in self.charts}) != len(self.charts):
            _fail("ID", "duplicate chart ID")
        object.__setattr__(self, "charts", tuple(self.charts))

    def layout_distance(self, a, b):
        charts = {c.id: c for c in self.charts}
        if a not in charts or b not in charts:
            _fail("ID", "unknown chart")
        x, y = charts[a].layout, charts[b].layout
        if x.unit != y.unit:
            _fail("UNIT", "layout units differ; no implicit conversion")
        return math.dist(x.position, y.position)

    def evolve(self, law, q, velocity, time):
        if not isinstance(law, CoupledScalars) or set(law.chart_ids) != {c.id for c in self.charts}:
            _fail("DOMAIN", "coupling IDs must match atlas IDs")
        return law.evolve(q, velocity, time)


@dataclass(frozen=True)
class AffineTransition:
    """x_target = matrix x_source + offset; no unit conversion in schema /1."""
    matrix: tuple
    offset: tuple
    source_unit: str
    target_unit: str

    def __post_init__(self):
        a = _array(self.matrix, (2, 2), "transition matrix")
        if not np.isfinite(np.linalg.cond(a)) or np.linalg.cond(a) > 1e12:
            _fail("TRANSITION", "transition must be invertible within condition limit 1e12")
        if _unit(self.source_unit) != _unit(self.target_unit):
            _fail("UNIT", "coordinate units differ; explicit conversion is required")
        object.__setattr__(self, "matrix", tuple(map(tuple, a)))
        object.__setattr__(self, "offset", tuple(_array(self.offset, (2,), "offset")))

    def apply(self, points):
        result = _points(points) @ np.asarray(self.matrix).T + self.offset
        return _array(result, result.shape, "transformed points")

    def inverse(self):
        inverse = np.linalg.inv(self.matrix)
        return AffineTransition(inverse, -inverse @ self.offset, self.target_unit, self.source_unit)

    def target_metric(self, source_metric):
        inverse = np.linalg.inv(self.matrix)
        result = inverse.T @ _metric(source_metric) @ inverse
        # Symmetrize only this derived expression to remove roundoff asymmetry.
        return _metric((result + result.T)/2)


@dataclass(frozen=True)
class FourierSpace:
    """Finite trigonometric polynomials orthonormal under dvol / volume."""
    domain: LocalDomain
    modes: tuple

    def __post_init__(self):
        if not isinstance(self.domain, LocalDomain) or self.domain.boundary != "periodic":
            _fail("BOUNDARY", "Fourier space requires a periodic local domain")
        if not isinstance(self.modes, (list, tuple)) or not 1 <= len(self.modes) <= MAX_MODES:
            _fail("RESOURCE_LIMIT", f"mode limit is 1..{MAX_MODES}")
        canonical = []
        for mode in self.modes:
            if not isinstance(mode, (tuple, list)) or len(mode) != 2:
                _fail("SHAPE", "each mode is an XY integer pair")
            if any(isinstance(k, bool) or not isinstance(k, (int, np.integer)) or abs(k) > MAX_MODE_INDEX for k in mode):
                _fail("MODE", f"mode indices must be integers within {MAX_MODE_INDEX}")
            canonical.append(tuple(map(int, mode)))
        if len(set(canonical)) != len(canonical):
            _fail("MODE", "duplicate Fourier modes")
        object.__setattr__(self, "modes", tuple(canonical))

    @property
    def wavevectors(self):
        return 2 * math.pi * np.asarray(self.modes) / self.domain.lengths

    @property
    def laplacian_eigenvalues(self):
        k = self.wavevectors
        return np.einsum("ij,jk,ik->i", k, np.linalg.inv(self.domain.metric), k)

    def _grid_fractions(self, shape):
        if not isinstance(shape, (tuple, list)) or len(shape) != 2 or any(
                isinstance(n, bool) or not isinstance(n, int) or n < 1 for n in shape):
            _fail("SHAPE", "grid requires two positive integer sizes")
        if math.prod(shape) > MAX_POINTS:
            _fail("RESOURCE_LIMIT", f"grid point limit is {MAX_POINTS}")
        for axis in (0, 1):
            if shape[axis] <= 2 * max(abs(m[axis]) for m in self.modes):
                _fail("ALIAS", "grid must resolve all retained modes without Nyquist ambiguity")
        axes = [np.arange(shape[j])/shape[j] for j in (0, 1)]
        return np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 2)

    def grid(self, shape):
        """Rounded absolute coordinates of the ideal regular sampling grid."""
        return self.domain.origin + self._grid_fractions(shape)*self.domain.lengths


@dataclass(frozen=True)
class FourierField:
    space: FourierSpace
    coefficients: np.ndarray
    field_unit: str = "1"

    def __post_init__(self):
        if not isinstance(self.space, FourierSpace):
            _fail("TYPE", "field requires a FourierSpace")
        object.__setattr__(self, "coefficients", _array(self.coefficients, (len(self.space.modes),),
                                                       "coefficients", complex_ok=True))
        _unit(self.field_unit)

    def evaluate(self, points):
        phases = (_points(points) - self.space.domain.origin) @ self.space.wavevectors.T
        if np.any(np.abs(phases) > 1e12):
            _fail("NUMERIC_RANGE", "phase magnitude exceeds the declared 1e12 bound")
        return np.exp(1j * phases) @ self.coefficients

    def derivative(self, axis):
        if isinstance(axis, bool) or not isinstance(axis, int) or axis not in (0, 1):
            _fail("DOMAIN", "derivative axis must be 0 or 1")
        return FourierField(self.space, 1j * self.space.wavevectors[:, axis] * self.coefficients,
                            f"{self.field_unit}/{self.space.domain.coordinate_unit}")

    def norm(self):
        return float(np.linalg.norm(self.coefficients))

    @_finite_result
    def h1_norm(self, length_scale=1):
        length = _scalar(length_scale, "H1 reference length", positive=True)
        weights = 1 + length**2 * self.space.laplacian_eigenvalues
        return float(np.sqrt(np.sum(weights * abs(self.coefficients)**2)))

    def sample_grid(self, shape):
        # Use exact declared index fractions, not subtraction of rounded global
        # coordinates; the Fourier representation is independent of origin.
        phases = 2*math.pi*self.space._grid_fractions(shape) @ np.asarray(self.space.modes).T
        return (np.exp(1j*phases) @ self.coefficients).reshape(shape)

    @classmethod
    def from_grid(cls, space, samples, field_unit="1"):
        if not isinstance(samples, np.ndarray) or samples.ndim != 2:
            _fail("SHAPE", "grid samples require a two-dimensional ndarray")
        space.grid(samples.shape)
        values = _array(samples, samples.shape, "samples", complex_ok=True)
        spectrum = np.fft.fftn(values) / values.size
        coefficients = [spectrum[m[0] % samples.shape[0], m[1] % samples.shape[1]] for m in space.modes]
        result = cls(space, coefficients, field_unit)
        error = np.linalg.norm(result.sample_grid(samples.shape)-values)
        if error > TOLERANCE * max(1., np.linalg.norm(values)):
            _fail("REPRESENTATION_LOSS", "samples contain content outside retained modes")
        return result

    def squared_amplitude(self):
        return SquaredAmplitude(self)


@dataclass(frozen=True)
class SquaredAmplitude:
    field: FourierField
    loss: ClassVar[str] = "noninvertible: phase and sign are lost; not an energy without a physical law"

    def __post_init__(self):
        if not isinstance(self.field, FourierField):
            _fail("TYPE", "squared amplitude requires a Fourier field")

    @property
    def field_unit(self):
        return f"({self.field.field_unit})^2"

    def evaluate(self, points):
        return np.abs(self.field.evaluate(points))**2


@dataclass(frozen=True)
class CoordinateView:
    field: FourierField
    transition: AffineTransition
    loss: ClassVar[str] = "none analytically; binary64 rounding"

    def __post_init__(self):
        if not isinstance(self.field, FourierField) or not isinstance(self.transition, AffineTransition):
            _fail("TYPE", "coordinate view requires a field and affine transition")
        if self.field.space.domain.coordinate_unit != self.transition.source_unit:
            _fail("UNIT", "field and transition source units differ")

    def evaluate(self, target_points):
        return self.field.evaluate(self.transition.inverse().apply(target_points))


def _time(value):
    value = _scalar(value, "time")
    if abs(value) > 1e6:
        _fail("RESOURCE_LIMIT", "absolute simulation time limit is 1e6 seconds")
    return value


def _wave_inputs(field, velocity, speed):
    if not isinstance(field, FourierField) or not isinstance(velocity, FourierField):
        _fail("TYPE", "wave data require Fourier fields")
    if field.space != velocity.space:
        _fail("DOMAIN", "wave displacement and velocity spaces differ")
    if field.space.domain.coordinate_unit != "m" or velocity.field_unit != f"{field.field_unit}/s":
        _fail("UNIT", "wave coordinates require m and velocity requires displacement-unit/s")
    return _scalar(speed, "speed in m/s", positive=True)


def _modal_evolve(q, velocity, frequencies, time):
    phase = frequencies * time
    if np.any(np.abs(phase) > 1e12):
        _fail("NUMERIC_RANGE", "phase magnitude exceeds the declared 1e12 bound")
    cosine, sine = np.cos(phase), np.sin(phase)
    # sinc includes the zero-frequency free drift exactly at zero.
    q_new = q * cosine + velocity * time * np.sinc(phase / math.pi)
    v_new = -q * frequencies * sine + velocity * cosine
    return q_new, v_new


def wave_evolve(field, velocity, time, speed=1):
    """Exact retained-mode solution of u_tt = c² Δ_g u; time s, speed m/s."""
    speed = _wave_inputs(field, velocity, speed)
    q, v = _modal_evolve(field.coefficients, velocity.coefficients,
                        speed*np.sqrt(field.space.laplacian_eigenvalues), _time(time))
    return FourierField(field.space, q, field.field_unit), FourierField(velocity.space, v, velocity.field_unit)


@_finite_result
def wave_energy(field, velocity, speed=1):
    """Quadratic invariant in (field-unit/s)², normalized spatial measure."""
    speed = _wave_inputs(field, velocity, speed)
    return float(.5 * np.sum(abs(velocity.coefficients)**2 + speed**2 *
                            field.space.laplacian_eigenvalues * abs(field.coefficients)**2))


@_finite_result
def _quantum_energies(field, hbar, mass):
    if not isinstance(field, FourierField) or field.space.domain.coordinate_unit != "m" or field.field_unit != "1":
        _fail("UNIT", "Schrodinger reference requires coordinates m and dimensionless coefficients")
    hbar = _scalar(hbar, "hbar in J*s", positive=True)
    mass = _scalar(mass, "mass in kg", positive=True)
    if mass < 1e-100 or hbar < 1e-100:
        _fail("NUMERIC_RANGE", "mass and hbar must be at least 1e-100")
    energy = hbar**2/(2*mass) * field.space.laplacian_eigenvalues
    if not np.all(np.isfinite(energy)):
        _fail("NUMERIC_RANGE", "energy exceeds binary64 range")
    return hbar, energy


def schrodinger_evolve(field, time, hbar=1.054571817e-34, mass=1):
    """Free particle on a periodic flat rectangle; parameters SI, no potential."""
    hbar, energy = _quantum_energies(field, hbar, mass)
    phase = energy / hbar * _time(time)
    if np.any(np.abs(phase) > 1e12):
        _fail("NUMERIC_RANGE", "phase magnitude exceeds the declared 1e12 bound")
    return FourierField(field.space, field.coefficients * np.exp(-1j*phase), field.field_unit)


@_finite_result
def schrodinger_energy(field, hbar=1.054571817e-34, mass=1):
    """Energy quadratic form in J; expectation only for a normalized field."""
    _, energy = _quantum_energies(field, hbar, mass)
    return float(np.sum(energy * abs(field.coefficients)**2))


@dataclass(frozen=True)
class HilbertState:
    amplitudes: np.ndarray
    basis_modes: tuple
    qubits: int | None
    basis_order: str = "coefficient index is basis index; qubit0 LSB when qubits is not None"

    def __post_init__(self):
        if not isinstance(self.basis_modes, (tuple, list)) or not 1 <= len(self.basis_modes) <= MAX_MODES:
            _fail("RESOURCE_LIMIT", f"Hilbert dimension limit is 1..{MAX_MODES}")
        n = len(self.basis_modes)
        # Reuse the mode grammar; the dummy domain carries no physical claim.
        modes = FourierSpace(LocalDomain((1, 1)), self.basis_modes).modes
        amplitudes = _array(self.amplitudes, (n,), "Hilbert amplitudes", complex_ok=True)
        if abs(float(np.vdot(amplitudes, amplitudes).real)-1) > TOLERANCE:
            _fail("NORMALIZATION", "Hilbert input must be normalized to tolerance 1e-12")
        expected = n.bit_length()-1 if n >= 2 and not n & (n-1) else None
        if self.qubits != expected or (self.qubits is not None and type(self.qubits) is not int):
            _fail("DIMENSION", "qubit count must match the ordered basis dimension")
        if self.basis_order != type(self).basis_order:
            _fail("BASIS_ORDER", "unsupported basis ordering")
        object.__setattr__(self, "amplitudes", amplitudes)
        object.__setattr__(self, "basis_modes", modes)


def hilbert_state(field, require_qubits=False):
    """Isometry for this declared orthonormal basis; never silently normalizes."""
    if not isinstance(require_qubits, bool):
        _fail("TYPE", "require_qubits must be Boolean")
    if not isinstance(field, FourierField):
        _fail("TYPE", "Hilbert map admits Fourier states, not observable views")
    if field.field_unit != "1":
        _fail("UNIT", "Hilbert coefficients must be dimensionless")
    if abs(field.norm()**2 - 1) > TOLERANCE:
        _fail("NORMALIZATION", "Hilbert input must be normalized to tolerance 1e-12")
    n = len(field.coefficients)
    qubits = n.bit_length()-1 if n >= 2 and not n & (n-1) else None
    if require_qubits and qubits is None:
        _fail("DIMENSION", "qubit admission requires a power-of-two dimension at least two")
    return HilbertState(field.coefficients, field.space.modes, qubits)


@dataclass(frozen=True)
class CoupledScalars:
    """q'' = -(diag(onsite_omega_squared)+L(coupling))q, equal unit masses."""
    chart_ids: tuple
    onsite_omega_squared: tuple
    coupling: tuple
    edge_kind: ClassVar[str] = "simulated"
    boundary: ClassVar[str] = "closed finite graph"
    displacement_unit: ClassVar[str] = "m"
    time_unit: ClassVar[str] = "s"
    coupling_unit: ClassVar[str] = "s^-2"
    energy_unit: ClassVar[str] = "m^2/s^2 (specific energy for equal unit masses)"

    def __post_init__(self):
        if not isinstance(self.chart_ids, (list, tuple)) or not 1 <= len(self.chart_ids) <= MAX_CHARTS:
            _fail("RESOURCE_LIMIT", f"coupled node limit is 1..{MAX_CHARTS}")
        if any(not isinstance(c, str) or not 1 <= len(c) <= 128 for c in self.chart_ids) or len(set(self.chart_ids)) != len(self.chart_ids):
            _fail("ID", "coupling IDs must be unique nonempty strings")
        n = len(self.chart_ids)
        onsite = _array(self.onsite_omega_squared, (n,), "onsite frequencies squared")
        c = _array(self.coupling, (n, n), "coupling")
        if np.any(onsite < 0) or np.any(c < 0) or not np.array_equal(c, c.T) or np.any(np.diag(c) != 0):
            _fail("COUPLING", "onsite values and coupling must be nonnegative; coupling symmetric with zero diagonal")
        object.__setattr__(self, "chart_ids", tuple(self.chart_ids))
        object.__setattr__(self, "onsite_omega_squared", tuple(onsite))
        object.__setattr__(self, "coupling", tuple(map(tuple, c)))

    @property
    def stiffness(self):
        c = np.asarray(self.coupling)
        return np.diag(np.asarray(self.onsite_omega_squared) + c.sum(axis=1)) - c

    def evolve(self, q, velocity, time):
        n = len(self.chart_ids)
        q = _array(q, (n,), "displacement")
        velocity = _array(velocity, (n,), "velocity")
        time = _time(time)
        c = np.asarray(self.coupling)
        pending = set(range(n))
        components = []
        while pending:
            group, frontier = [], [min(pending)]
            while frontier:
                i = frontier.pop()
                if i not in pending:
                    continue
                pending.remove(i)
                group.append(i)
                frontier.extend(j for j in sorted(pending) if c[i, j] > 0)
            components.append(sorted(group))
        q_out, v_out = np.empty(n), np.empty(n)
        for group in components:
            sub_q, sub_v = q[group], velocity[group]
            matrix = self.stiffness[np.ix_(group, group)]
            count = len(group)
            if all(self.onsite_omega_squared[i] == 0 for i in group):
                # A connected unanchored component has a known constant null
                # vector. Separate it structurally, before any eigensolver.
                center_q = float(sub_q[0]) + math.fsum(float(x-sub_q[0]) for x in sub_q)/count
                center_v = float(sub_v[0]) + math.fsum(float(x-sub_v[0]) for x in sub_v)/count
                if count == 1:
                    q_out[group], v_out[group] = center_q + time*center_v, center_v
                    continue
                differences = np.vstack((np.eye(count-1), -np.ones(count-1)))
                basis, _ = np.linalg.qr(differences, mode="reduced")
                matrix = basis.T @ matrix @ basis
                sub_q, sub_v = basis.T @ (sub_q-center_q), basis.T @ (sub_v-center_v)
            else:
                basis, center_q, center_v = np.eye(count), 0., 0.
            values, vectors = np.linalg.eigh((matrix+matrix.T)/2)
            if values[0] < -TOLERANCE * max(1., float(np.max(abs(values)))):
                _fail("NUMERIC_RANGE", "stiffness eigensolver violated positive semidefiniteness")
            q_new, v_new = _modal_evolve(vectors.T @ sub_q, vectors.T @ sub_v,
                                        np.sqrt(np.maximum(values, 0)), time)
            q_out[group] = basis @ (vectors @ q_new) + center_q + time*center_v
            v_out[group] = basis @ (vectors @ v_new) + center_v
        return (_array(q_out, (n,), "evolved displacement"),
                _array(v_out, (n,), "evolved velocity"))

    def energy(self, q, velocity):
        n = len(self.chart_ids)
        q = _array(q, (n,), "displacement")
        velocity = _array(velocity, (n,), "velocity")
        # Edge differences avoid cancellation in q^T L q for a large common
        # displacement and retain nonnegativity term by term.
        potential = math.fsum(self.onsite_omega_squared[i]*q[i]**2 for i in range(n))
        potential += math.fsum(self.coupling[i][j]*(q[i]-q[j])**2
                              for i in range(n) for j in range(i+1, n))
        return float(.5*(math.fsum(x*x for x in velocity) + potential))


def seed_wave_view(operation, x, time=0, k=1, omega=1, phase=0, amplitude=1):
    """Versioned scalar formula adapter; arguments are declared nondimensional.

    Retains valid seed sine/derivative numerics; squared_amplitude uses A².
    The seed's energy and fourier_sine aliases are not admitted by this API.
    """
    if not _sized_sequence(x) or not 1 <= len(x) <= MAX_POINTS:
        _fail("RESOURCE_LIMIT", f"sample limit is 1..{MAX_POINTS}")
    x = _array(x, (len(x),), "sample coordinates")
    time, k, omega, phase, amplitude = [_scalar(v, label) for v, label in
        ((time, "time"), (k, "wavenumber"), (omega, "frequency"), (phase, "phase"), (amplitude, "amplitude"))]
    argument = k*x - omega*time + phase
    if np.any(abs(argument) > 1e12):
        _fail("NUMERIC_RANGE", "phase magnitude exceeds the declared 1e12 bound")
    if operation == "sine":
        return amplitude*np.sin(argument)
    if operation == "derivative":
        return amplitude*k*np.cos(argument)
    if operation == "squared_amplitude":
        return (amplitude*np.sin(argument))**2
    _fail("REPRESENTATION", "supported views: sine, derivative, squared_amplitude")
