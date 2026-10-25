# QUANTUM ORACLE finite function spaces, contract 1

`spaces.py` implements `quantum-oracle.function-spaces/1` as a standalone NumPy module. It is a finite mathematical reference for V3 §§1–5, 14 and 23, with explicit local coordinates, function representations and dynamic laws. It does not implement an arbitrary PDE solver, QFT, physical calibration, continuum convergence, an N-chart manifold gluing algorithm, or a native renderer. Those larger requirements remain open.

The selected design is a new versioned contract beside the original seed. Altering the seed would destroy the reference; treating its chart layout as a physical domain would conflate independent structures. The implementation plan is [the scientific commission plan](../../commissions/2026-10-25-scientific-completion/implementation-plan.md). Implementation followed failing controls, minimal code, analytic comparison, admission hardening and verification. Upstream source was read and compared, never edited.

## Distinct objects and maps

| Object | Meaning and admission |
|---|---|
| `LocalDomain` | Two finite XY coordinates, a local origin, positive rectangle lengths, an exact unit label, constant symmetric positive-definite metric and boundary declaration |
| `LayoutPoint` | A separate XY ambient placement with its own unit; `Atlas.layout_distance` uses the ordinary Euclidean layout norm |
| `Chart` / `Atlas` | Finite unique IDs binding domains to placement and an optional Fourier field or squared-amplitude observable; hosted fields must match the chart domain exactly |
| `FourierSpace` | Ordered, unique, finite integer mode pairs on a periodic rectangle; each order is part of the basis convention |
| `FourierField` | Complex coefficient state with a field-unit label; an arbitrary field is not automatically a normalized quantum state |
| `SquaredAmplitude` | Observable `abs(f)**2`, unit `(field_unit)^2`, losing pointwise phase/sign; no energy identification without a law |
| `AffineTransition` / `CoordinateView` | Invertible coordinate change and scalar pullback preserving the represented function; no implicit unit conversion |
| `CoupledScalars` | Explicit simulated symmetric graph law, separate from all layout positions |
| `HilbertState` | Normalized dimensionless coefficients admitted through an explicitly ordered orthonormal basis; optional qubit-compatible dimension |

`LocalDomain.intrinsic_distance(a,b)` computes the flat **covering-chart** distance `sqrt((a-b)^T g (a-b))`. Even with periodic boundaries, it is not the shortest torus distance. The metric components are dimensionless; distance has `coordinate_unit`. The origin fixes the Fourier coordinate phase and is separate from the layout origin. `contains` checks the closed covering rectangle, including both identified seam endpoints. A periodic field evaluation outside that rectangle uses its periodic extension.

The `closed` boundary declaration is available for geometry only. Fourier dynamics reject it: only `periodic` is implemented. Local charts are XY as required by the original constitution; N counts charts, not arbitrary local coordinate dimensions.

For `y=A x+b`, `AffineTransition.inverse()` represents `x=A^-1(y-b)`, and `target_metric(g)=A^-T g A^-1`. Hence `(dy)^T g_target dy=(dx)^T g dx`. `CoordinateView.evaluate(y)=field.evaluate(T^-1(y))`, so `F_target(T(x))=F_source(x)` up to binary64 error. General affine maps can produce parallelogram periods; the view preserves the source periodic extension instead of pretending the transformed domain is another axis-aligned rectangle. Computed metrics are symmetrized to remove arithmetic asymmetry, while supplied metrics must be exactly symmetric. This is an affine Euclidean construction, not a general manifold atlas or a proof of overlap compatibility among arbitrary charts.

## Finite function and representation contracts

For lengths `L=(Lx,Ly)` and local origin `o`, the ordered mode `n=(nx,ny)` denotes

```text
k_n = (2*pi*nx/Lx, 2*pi*ny/Ly)
e_n(x) = exp(i*k_n dot (x-o))
f(x) = sum_n c_n e_n(x)
dmu = dvol_g / Volume_g = dx dy / (Lx Ly)
<f,h> = integral conjugate(f) h dmu = sum_n conjugate(c_n) d_n
lambda_n = k_n^T g^-1 k_n >= 0
```

Orthogonality follows by integrating each integer exponential over its full period; the constant metric factor cancels in the normalized measure. Therefore `norm()` is the exact finite-space L2 formula, evaluated in floating point. It has the same unit as `f`. This is not the unnormalized volume integral; a caller needing that measure must multiply the squared norm by the domain's metric volume.

`h1_norm(ell)` uses `sqrt(sum (1+ell^2 lambda_n)|c_n|^2)`, where `ell` is a positive reference length in the coordinate unit. Including `ell` makes the terms dimensionally compatible. It is a norm on this finite space with specified scale, not an unqualified comparison between different domains or unit conventions.

`derivative(axis)` multiplies coefficients by `i*k_axis` and changes the field-unit label to `field_unit/coordinate_unit`. Differentiation loses the constant coefficient and need not preserve normalization; it is an observable/representation operation rather than an identity or a quantum gate. Squared amplitude is evaluated directly and does not force its product into the original retained mode set, which need not be closed under products.

`sample_grid((nx,ny))` and `FourierField.from_grid(...)` connect coefficients to values on the declared uniform periodic grid. Both grid sizes must exceed twice the largest absolute retained index on that axis, avoiding Nyquist ambiguity. Sampling evaluates normalized local index fractions directly, avoiding cancellation from a large translated origin; `FourierSpace.grid` separately returns rounded absolute coordinates. Those rounded coordinates need not reproduce the ideal index fractions exactly when supplied to `evaluate`. The inverse uses NumPy's forward FFT divided by point count. It reconstructs and rejects residual content outside the retained space above `1e-12*max(1, ||samples||_2)`. This is an approximate binary64 representation witness; arbitrary sampled data are not claimed equivalent to a finite trigonometric polynomial between sample points. No aliasing claim is made for unobserved continuum content.

For normalized dimensionless `c`, `hilbert_state` identifies `e_n` with the finite ordered orthonormal basis vector of the same coefficient index. This is an isometry for this declared basis and measure; it says nothing about ambient layout distances. Norm-squared must be within `1e-12` of one; no normalization is performed. `require_qubits=True` additionally requires dimension `2^q >= 2`, with coefficient index equal to computational-basis index and qubit 0 least significant. A three-dimensional space is a valid finite Hilbert space but is not silently encoded as two qubits. Squared-amplitude observables and dimensional classical fields reject. A quantum probability density in this convention is relative to `dmu`, not raw physical area.

The state/observable/inner-product distinctions agree with [David Tong's quantum mechanics notes](https://www.damtp.cam.ac.uk/user/tong/qm/qmhtml/S3.html). The Fourier basis and finite tensor-product extension above are the explicitly stated construction implemented here, not a claim that those notes certify this code.

## Dynamics and independent controls

`wave_evolve(u,v,t,c)` solves the retained coefficients of `u_tt=c^2 Delta_g u` on the periodic domain. Coordinates are `m`, time is `s`, speed is `m/s`, and `v.field_unit=u.field_unit/s`. For frequency `w_n=c sqrt(lambda_n)`:

```text
u_n(t) = u_n(0) cos(w_n t) + v_n(0) t sinc(w_n t/pi)
v_n(t) = -u_n(0) w_n sin(w_n t) + v_n(0) cos(w_n t)
E = 1/2 sum_n (|v_n|^2 + c^2 lambda_n |u_n|^2)
```

`E` has unit `(field_unit/s)^2`; it is a declared quadratic invariant, not calibrated joules. The sinc expression retains the zero-frequency linear drift. The test oracle uses the independent d'Alembert identity `[cos(x-ct)+cos(x+ct)]/2`, verifies zero-mode drift, and changes the intrinsic metric to change the frequency. Periodic Fourier evolution is a standard reference approach in [MIT's numerical PDE course](https://math.mit.edu/classes/18.336/index.html); the finite retained solution here has no truncation error for inputs already in its invariant mode span. Approximation error for arbitrary input fields is not bounded by this implementation.

`schrodinger_evolve(f,t,hbar,mass)` represents the free Hamiltonian `H=-(hbar^2/2m) Delta_g` on the periodic flat rectangle. Coordinates are `m`; `hbar` is in `J*s`, mass in `kg`, and time in `s`. The default rounded `hbar=1.054571817e-34` is a declared numerical parameter, not a calibration receipt. Dimensionless coefficients evolve as `c_n exp(-i E_n t/hbar)`, with `E_n=hbar^2 lambda_n/(2m)`. `schrodinger_energy` returns the energy quadratic form in joules; it is an expectation only when normalized. Tests use explicitly chosen mathematical parameters `hbar=2`, `m=4`, exact modal phases, reverse time and norm preservation. These parameter fixtures are not a simulated laboratory measurement. The periodic free-particle eigenstate construction is documented in [Tong's eigenfunction discussion](https://www.damtp.cam.ac.uk/user/tong/qm/qmhtml/S3.html#S3.SS2.SSS1).

For `CoupledScalars`, `C_ij=C_ji>=0`, `C_ii=0`, and onsite squared frequencies are nonnegative. The law is

```text
K = diag(onsite_omega_squared) + diag(C*1) - C
q'' = -K q
E = 1/2 (v^T v + q^T K q)
```

Displacement is `m`, time `s`, and C and onsite values are `s^-2`; the energy is the sum of specific energies `m^2/s^2` in the equal-unit-mass convention. It becomes total joules after multiplication by a common physical mass in kg. The graph is closed with no exterior forcing, damping, delays or unstated boundary couplings. Negative/asymmetric couplings reject; this contract does not implement arbitrary active or dissipative networks. `evolve` separates each unanchored connected component's constant mode structurally, retaining its exact free drift instead of treating a small positive eigensolver residual as a restoring force. The remaining orthogonal subspace uses a symmetric eigensystem and the exact modal solution. Small negative eigensolver residuals are clipped only within `1e-12*max(1,max_abs_eigenvalue)`; larger violations reject. Energy is evaluated as a sum of squared edge differences and nonnegative onsite/velocity terms, avoiding cancellation in `q^T L q` for a large common displacement.

The independent two-scalar fixture has onsite values 1, coupling 2 and initial `(q,v)=((1,0),(0,0))`. Its expected coordinates are `(cos(t)+cos(sqrt(5)t))/2` and `(cos(t)-cos(sqrt(5)t))/2`, and energy is 1.5. A zero-coupling null control forbids transfer. Moving the second layout point from `(3,4)` to `(3000,-4000)` leaves the full trajectory unchanged. Normal-mode decomposition follows established [MIT coupled-oscillator teaching](https://www.ocw.mit.edu/courses/8-03sc-physics-iii-vibrations-and-waves-fall-2016/pages/part-i-mechanical-vibrations-and-waves/lecture-4/); this specific fixture is derived directly from the declared K.

## Admission, resources and source compatibility

Every public data constructor validates its input. `ContractError` is a `ValueError` with stable `code` and descriptive detail, including `TYPE`, `SHAPE`, `UNIT`, `METRIC`, `BOUNDARY`, `RESOURCE_LIMIT`, `NUMERIC_RANGE`, `NORMALIZATION` and representation/ID errors. Unknown units are opaque labels for geometry/fields; no conversion is inferred. Dynamics enforce their documented SI labels. Real data reject complex numbers, booleans and object/string arrays rather than silently casting them. Nonfinite data reject. State arrays have immutable byte owners, so mutation and re-enabling write access fail.

| Bound | Value |
|---|---:|
| Charts / coupled scalar nodes | 1–64 |
| Retained Fourier modes / finite Hilbert dimension | 1–256 |
| Absolute integer mode index per axis | 1024 |
| Points in any evaluation or sampling grid | 1–4096 |
| Coordinate rectangle lengths | `1e-6`–`1e6` in the declared unit |
| Coordinate resolution | `spacing(abs(origin_i))*4096 <= length_i`; collapsed domains reject |
| Metric eigenvalues | `1e-12`–`1e12`, condition number at most `1e12` |
| Affine transition condition number | at most `1e12` |
| Input numerical magnitude | at most `1e100` |
| Absolute evolution time | at most `1e6` seconds |
| Absolute evaluated phase | at most `1e12` radians |
| Unit label / chart ID | 64 / 128 characters |

Sequence sizes are checked before numerical conversion. A dense Fourier evaluation has at most `4096*256` complex basis entries (16 MiB for that array); temporary arrays and Python/NumPy overhead are additional. Coupling diagonalization is at most 64 by 64. There is no unbounded search, time-stepping loop, runtime network access or renderer dependency. These are algorithmic bounds, not operating-system memory/CPU isolation. Arithmetic overflow in norm/energy calculations rejects with `NUMERIC_RANGE`. Binary64 rounding, underflow and large-phase argument reduction remain numerical limitations; fixture tolerances are measured controls, not a uniform accuracy guarantee at every admitted extreme.

The unchanged original `build/foundation/QUANTUM_ORACLE_V3_EXTENSION/atlas_quantum/core.py` has SHA-256 `637368c05000fbcb2e7739cd7b9abe134be6b42222a2bab32bbcc880439369f6`. `seed_wave_view` is a separately named adapter for nondimensional scalar formulas. Sine and derivative values are compared directly to the original executable seed over nontrivial k, omega, phase and amplitude. The new `squared_amplitude` operation gives 4 at a sine crest of amplitude 2; the seed's `energy` operation instead gives 2. The adapter rejects `energy` and `fourier_sine`: neither name supplies a physical energy law or a spectral transform. The new `FourierSpace` supplies an actual spectral representation. Malformed XY origins and nonfinite coordinates now reject.

## Replay and status

From the repository root, with the scientific environment installed and immutable foundation materialized:

```sh
.venv/bin/python -B -m unittest discover -s research/quantum_oracle/tests -p test_spaces.py -v
```

The suite covers analytic propagation, inverse coordinate maps, metric covariance, normalized Parseval/H1 formulas, sampled representation loss, state/observable admission, graph null/layout controls, immutable arrays, typed malformed/range rejection and original compatible numerics. Numerical assertions use explicit tolerances from `1e-14` to `3e-13` for the stated moderate fixtures; normalization and representation admission use `1e-12`. Passing these finite controls establishes only their declared scope. Full V2/V3 real-data, hardware, field-theory, arbitrary PDE, topology and discovery requirements are not discharged.
