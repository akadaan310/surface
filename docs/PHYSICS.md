# Surface native physical reference kernel

This implementation is a bounded, deterministic C++20 model for an immersive ink surface. Its grid, analytic fields, circuit reference, relay memory and optical lookup are real computations with declared equations. Their co-location does not make them a fully coupled Maxwell, Navier–Stokes, electrochemical or micromagnetic solver. There is no browser or graphics-engine dependency in this component.

## Coordinate, unit and state contract

`surface::Physics(width, height, seed)` exposes row-major float arrays and double simulation time. Positive x points right and positive y points down; this is the chosen coordinate basis. The physical domain is 2 metres wide and `2*(height-1)/(width-1)` metres tall, so grid spacing is equal in both axes. Touch coordinates are normalized from zero to one. Dimensions are restricted to 16–256 nodes in each direction and at most 65,536 nodes. Default dimensions are 128 by 96.

| Array | Meaning and unit | Operational admission bounds |
|---|---|---|
| `pressure` | Scalar wave amplitude, assigned Pa | -32 to 32 |
| `velocity` | Time derivative of scalar amplitude, Pa/s; **not fluid velocity** | -4096 to 4096 |
| `heat` | Temperature excess above an unspecified reference, K | 0 to 2000 |
| `density` | Display tracer concentration, arbitrary units; **not mass density** | 0 to 64 |
| `potential` | Electrostatic potential, V | Finite bounded derived field |
| `ex`, `ey` | Electric field, V/m | Finite bounded derived field |
| `bx`, `by` | Magnetic induction in a planar slice, T | Finite bounded derived field |

Initial conditions use six maintained, alternating charge lobes around an ellipse covering approximately x = 0.18–0.82 and y = 0.20–0.80. Their absolute orientation depends on the seed. Charges, moments and deposited amplitudes are synthetic choices, not measurements of a specimen. Replaying the same seed and input/timestep sequence reproduces the same state on the same numerical platform.

Touch deposition is a Gaussian impulse. It adds tracer, and depending on mode also heat, scalar pressure or a pair of finite-core sources. Modes include `coupled`, `wave`/`acoustic`, `heat`/`thermal`, `electric`, `magnetic`, and `ink`/`optical`/`light`. Unrecognized mode names use the combined mode. Strength is bounded to ±3 and radius to 0.005–0.2 of the domain width. Signed strength controls signed wave/source deposition; heat and tracer additions use its magnitude. Dynamic sources fade linearly over 12 simulation seconds; the six initial sources are externally maintained. There are at most 32 sources. Old transient sources are retired first when the budget is exhausted.

## Scalar wave

The grid solves

\[
\partial_t p=v,\qquad \partial_t v=c^2\nabla^2p-\gamma v,
\]

with c = 0.48 m/s and gamma = 0.12/s. This is a deliberately slow effective wave medium. It is not the sound speed of air, water or a named material. Calling its observation “acoustic” refers to the scalar wave analogy, not material calibration.

The separate native `surface::AcousticField` component uses its own air-acoustics reference with c = 343 m/s. It is a different numerical grid and state from `Physics::pressure`. The 0.48 m/s visual effective medium is not passed off as 343 m/s air propagation; any common input or observation mapping does not make the two fields identical.

A five-point central Laplacian uses reflected ghost values for zero normal derivative boundaries. Velocity is advanced by a symplectic-Euler step with implicit linear damping, then pressure uses the new velocity. The substep satisfies

\[
c\,\Delta t\sqrt{\Delta x^{-2}+\Delta y^{-2}}\leq0.65.
\]

The constant 0.65 provides margin below the two-dimensional explicit wave stability limit. Additionally, every substep is no longer than 1/120 second. These are solver seconds; there is no claim that an elapsed display second reproduces a named laboratory process.

`diagnostics.waveEnergy` is the spatial integral of `(v²+c²|grad p|²)/2`, using a finite-difference gradient and trapezoidal boundary weights. Its units are those of the scalar amplitude norm, not calibrated acoustic joules; a physical acoustic energy would require density and compressibility that this model does not provide. High-amplitude input has explicit pressure/velocity safety limits. `limitedCells` counts activation of those guards, which makes any departure from the unbounded linear equation observable.

The numerical test starts from a cosine eigenmode with zero initial time derivative and compares its amplitude after one second with the independently calculated damped harmonic solution. The test checks the modeled speed and damping rather than a prerecorded output image. This is a bounded validation case, not a general convergence certificate or a k-Wave equivalence claim. The separate k-Wave project describes a much broader acoustic solver and its references: <https://github.com/ucl-bug/k-wave>.

## Heat and tracer

Temperature excess follows

\[
\partial_t T=\alpha\nabla^2T-\beta T,
\]

with alpha = 0.0005 m²/s and beta = 0.025/s. Diffusion is explicit; cooling uses an exponential multiplier. Reflected boundaries have zero normal heat flux. The substep additionally satisfies `alpha*dt*(dx^-2+dy^-2) <= 0.24`, below the positivity bound 0.5. Thus nonnegative initial temperatures and deposits remain nonnegative under ordinary admitted conditions. The heat test verifies the maximum principle and spreading from an isolated positive deposit. There is no heat capacity, mass density or thermochemical model, so `thermalIntegral` is K·m², not joules.

Tracer diffusion uses D = 0.00008 m²/s. A bilinear semi-Lagrangian backtrace then advects it in the imposed velocity `u = 0.00008*(-Ey, Ex)` m/s, followed by exponential decay at 0.016/s. The conversion factor is an explicit artistic flow scale with units m²/(V·s). Rotating a smooth electrostatic gradient gives a divergence-free field in the interior before boundary handling. Backtraces are clamped at the domain edge. Bilinear interpolation preserves positivity but introduces numerical diffusion and does not strictly conserve tracer mass. The tracer neither exerts a force on the field nor solves momentum conservation. `tracerIntegral` is concentration·m².

Renderer field-line trajectories, exposure, trail persistence, thermal color and any audio mapping are observation transforms. They are separate from these solver arrays. Thermal false color is not a blackbody spectrum.

## Electrostatic and magnetic sources

For source displacement r and core radius a, electrostatic potential and field are

\[
\phi={kq\over\sqrt{r^2+a^2}},\qquad \mathbf E={kq\mathbf r\over(r^2+a^2)^{3/2}},
\]

where k = 8.9875517923×10⁹ N·m²/C². These are regularized three-dimensional source fields observed in a plane. The finite core corresponds to a smooth extended charge distribution, avoiding point-source singularities. Superposition is exact for the chosen analytic source model; no Poisson grid solver or dielectric boundary conditions are implied.

The magnetic source derives from the three-dimensional vector potential

\[
\mathbf A={\mu_0\over4\pi}{\mathbf m\times\mathbf r\over(r^2+a^2)^{3/2}},
\]

whose curl gives

\[
\mathbf B={\mu_0\over4\pi}
{3\mathbf r(\mathbf m\cdot\mathbf r)+(2a^2-r^2)\mathbf m\over(r^2+a^2)^{5/2}}.
\]

The implementation evaluates the z=0 slice with in-plane moments. It uses μ0/(4π) = 10⁻⁷ as a conventional numerical approximation, not a claim of exact post-2019 SI permeability. The far field is the usual dipole field; the finite core is a specified regularization rather than a claim about a measured magnet's shape. Two-dimensional divergence of the displayed slice need not vanish, because the omitted z derivative participates in the full three-dimensional divergence.

Public `fieldAt()` accepts metre coordinates, unlike `Physics::sources`, which stores normalized positions. Tests independently check the potential/electric field at a known displacement, odd electric-field symmetry, even potential symmetry, and the axial/equatorial signs and amplitude of the softened magnetic dipole. Fields respond instantaneously as quasistatic analytic references; retardation, radiation, induction between painted sources and self-consistent Maxwell evolution are absent.

## Inductive circuit and battery energy reference

Two series RLC loops use L1 = 0.4 H, L2 = 0.25 H, C1 = 0.02 F, C2 = 0.03 F, R1 = 1.2 ohm, R2 = 0.8 ohm, and load resistance 2.2 ohm. Mutual inductance is `M = 0.42*sqrt(L1*L2)`, so the inductance matrix is positive definite. The equations are

\[
L_1\dot i_1+M\dot i_2=V_d-R_1i_1-q_1/C_1,
\]
\[
M\dot i_1+L_2\dot i_2=-(R_2+R_L)i_2-q_2/C_2,\qquad \dot q_k=i_k.
\]

A two-by-two backward-Euler solve advances both currents simultaneously. The drive is a 1.5 Hz sine with an initial amplitude of 2.5 V; input can energize the drive up to 8 V, with a slow envelope decay. These deliberately low-frequency, high-inductance/high-capacitance choices are a visible reference circuit, not a calibrated wireless charger. Mutual-inductance and coil-design context is provided by ST's primary application note: <https://www.st.com/resource/en/application_note/an5961-wireless-power-transfer-coil-design-stmicroelectronics.pdf>.

The diagnostic stored energy includes both inductor energies, mutual energy and both capacitor energies. In a test with drive disabled and known initial inductive energy, remaining stored energy plus accumulated dissipation and harvested energy does not exceed the initial energy. Backward Euler adds numerical dissipation; it does not create a claim of exact energy conservation.

A separate 432 J battery energy reservoir receives 82% of the modeled load dissipation, subject to its capacity, and reports `soc = storedBatteryEnergy/432`. The initial state of charge is 0.34. This is an idealized rectification/energy-accounting rule. It does not solve semiconductor diodes, battery current/voltage, lithium diffusion, reaction kinetics, aging, charge limits, or the Doyle–Fuller–Newman electrochemical equations. The reservoir is not wired back as a nonlinear battery load. A complete electrochemical reference would require a model such as the documented PyBaMM DFN: <https://docs.pybamm.org/en/stable/source/examples/notebooks/models/DFN.html>.

The circuit shares input excitation with the other models but does not compute its mutual inductance from painted field geometry. That separation prevents its illustrative parameters from being mistaken for a self-consistent electromagnetic charging prediction.

## Magnetic memory and optical reference functions

Magnetic memory is a bounded ensemble of 15 symmetric switching relays, with coercive thresholds spanning 0.15–0.80 in a normalized drive coordinate. Each relay switches to +1 above its positive threshold and to -1 below its negative threshold; it retains state between thresholds. Their mean is the reported magnetization. The input-applied drive relaxes, while remanence persists. Tests verify saturation, remanence and reversal. This phenomenological memory does not solve exchange, anisotropy, demagnetization or Landau–Lifshitz–Gilbert dynamics. The full micromagnetic scope of NIST OOMMF is described at <https://math.nist.gov/oommf/doc/userguide21a3/userguide/Overview_OOMMF.html>. This diagnostic memory is not used as a constitutive material law in the analytic field arrays.

The optical reference functions are:

- `faradayRotation(V, B, length)`: theta = V·B·length for a uniform path-parallel field and a supplied Verdet coefficient. Its validity and wavelength dependence depend on the material parameters provided. It is not an FDTD solve or a measured TGG response. The primary Meep gyrotropic example illustrates the fuller tensor-based calculation: <https://meep.readthedocs.io/en/latest/Python_Tutorials/Gyrotropic_Media/>.
- `malusTransmission(theta)`: cos²(theta), for ideal linear polarizers and an already linearly polarized input. It omits extinction leakage, absorption and polarization ellipticity.
- `zeemanShiftHz(B, g, deltaM)`: (μB/h)·g·deltaM·B, using μB/h = 1.39962449171×10¹⁰ Hz/T. This is a weak-field single-factor reference. For a real transition between levels with different g factors, evaluate the upper and lower level shifts and take their difference. It is not a catalog of transition strengths, a line-profile calculation or a strong-field Paschen–Back model. NIST gives the underlying weak-field energy expression and regime: <https://www.nist.gov/pml/atomic-spectroscopy-compendium-basic-ideas-notation-data-and-formulas/atomic-spectroscopy-zeeman>.

## Official spectral observer and display conversion

`cieXYZ(wavelengthNm)` linearly interpolates the **official CIE 1931 two-degree observer table**, from 360 to 830 nm at 1 nm sampling, and returns zero outside that range. This follows the dataset's interpolation and extrapolation metadata. It does not use the earlier contemplated Gaussian fit.

Source: CIE 2019, *Colour-matching functions of CIE 1931 standard colorimetric observer*, International Commission on Illumination, Vienna. DOI <https://doi.org/10.25039/CIE.DS.xvudnb9b>. Landing page: <https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer>.

Exact acquired data are retained in `data/CIE_xyz_1931_2deg.csv`, with the original metadata alongside it. The current download link is <https://files.cie.co.at/Publications-datasets/CIE_xyz_1931_2deg.csv>. The 24,021 acquired bytes have SHA-256 `fa663e3535a7e0763a745993a1f0a192eb0275ac46ad2d1befd7626841e713c1`, matching the publisher's metadata. The data license is **CC BY-SA 4.0**; attribution, licensing and transformation notes are in `data/CIE-LICENSE.md`. `src/cie1931.inc` is the same table reformatted into a C++ initializer, with wavelength represented by its array index.

`wavelengthToLinearRGB()` applies the usual D65 XYZ-to-linear-sRGB matrix, clips negative display primaries, then divides all three primaries by the larger of 1 and their maximum. This is a deliberately bounded preview of a monochromatic stimulus. Clipping is a gamut approximation; the result is not a calibrated spectral radiance, faithful display of every spectral locus, or an sRGB transfer-encoded pixel. Display encoding and exposure belong to the rasterizer. The sRGB colorimetry/encoding reference is the ICC registry: <https://registry.color.org/rgb-registry/srgb>.

Tests verify the official metadata's 479 nm reference row, interpolation to 479.5 nm, dominant primaries for representative blue/green/red samples, domain behavior, ideal polarizer extinction and the Zeeman frequency scale.

## Continuation, validation and numerical boundaries

The serial form is explicitly little endian and versioned. It stores dimensions, time, seed and RNG continuation, all four evolved arrays, every source, complete circuit and relay state, and counters. Derived E/B/potential and diagnostics are reconstructed deterministically. Scratch buffers do not affect continuation and are rebuilt. Magic is `SFPHYS1` followed by a zero byte, with physics version 1. Single- and double-precision IEEE encodings are retained without conversion to decimal text. A normal default checkpoint is roughly 200 KB. The outer checkpoint store owns integrity checks and durable transactional commit.

Restoration parses into a staged `Physics` object and commits only after all lengths, ranges, finite values, identifiers and circuit/memory invariants pass. It rejects extra bytes, truncation, unknown versions, impossible dimensions, NaNs, negative temperatures and malformed counters before replacing live state. At most 2 MiB is admitted. Counter rollover for local source identifiers is handled by renumbering the bounded live set. The tests compare resumed state bytes and further evolution against an uninterrupted run.

One `step(dt)` accepts at most 0.1 simulation second, records discarded time, and subdivides that accepted interval. This prevents a paused application from integrating minutes of elapsed wall time in one frame. Negative or nonfinite time steps and nonfinite input coordinates are rejected. The code has bounded grid, source and substep counts. Full process hangs, storage integrity and platform lifecycle are handled elsewhere.

Exact checkpoint continuation is tested on the same compiler/platform. Across architectures or math libraries, transcendental functions and floating-point contraction may cause tiny differences; the checkpoint schema is portable, but bit-identical cross-platform trajectories have not been certified. No original PHANTOM comparison gate or historical Octave result is implied by these new native tests.

## Component verification receipt

On 25 October 2026, the physics component compiled with C++20, `-O2 -Wall -Wextra -Wpedantic -Werror`, and its independent numerical/admission test executable exited successfully. The same tests passed AddressSanitizer and UndefinedBehaviorSanitizer with leak detection disabled. LeakSanitizer could not inspect `/proc` thread state in the execution sandbox; no successful leak-scan claim is made.

A 128×96 release benchmark advanced 600 steps of 1/60 simulation second in 1,493.6 ms on the build host, averaging 2.489 ms per step. This is a host measurement, not an Android-device performance guarantee. No pressure/velocity limiter activated in that seeded benchmark. The final continuation blob was 197,143 bytes. The machine-readable receipt is `evidence/physics-verification.json`; final integrated application/build verification belongs to the release receipt.
