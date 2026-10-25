# Evolving Surface toward physical and quantum observations

The current native renderer is preserved. Its next architecture should make the physical model, representation map and observation explicit without adding product chrome. This is a staged design and acceptance contract, not a claim that the full renderer evolution has shipped.

## Existing boundary

`Renderer::render(FieldView, ViewState, displayDelta)` consumes density, temperature excess, scalar-wave amplitude, potential and planar field components. `Renderer::renderSky` consumes projected catalogue points. `line`, `splat`, `trace`, `shade` and `encode` implement Surface's own CPU rasterization and display mapping. Existing trails, exposure and palette choices are observations, not measured particles, calibrated material colors or a solution of full electrodynamics. [Current equations and limits](PHYSICS.md), [catalogue semantics](ATLAS.md), [C++ interface](../include/surface/renderer.hpp).

The first product gate remains actual Android launch and lifecycle verification. Changing the physical renderer before resolving a device crash would obscure its cause.

## Proposed typed ink record

Each field should declare source digest/offset, model/version, domain and mesh/chart, state variables, SI or explicit non-SI units, coordinate basis/origin/metric, boundary conditions, logical and physical clocks, parameters/calibration, uncertainty, solver/time-step/error policy, transition trace and observation operators. Ink is then a view of an admitted record. Scalar, vector, tensor, complex-amplitude and density-operator fields need different types.

Maintain independent layers: immutable evidence → decoded state → model evolution → observable → observer/instrument → display encoding. Every lossy step states its loss and a witness. A spectrum, field line, amplitude heatmap and detector count are different observation choices; never infer the physical object from the palette alone.

## Next implementation tracks

| Track | Concrete work | Acceptance before native admission |
|---|---|---|
| N-chart carrier | Named XY charts, domain/metric/units, origin layout, maps, physical/logical/view edges, nested finite graph | Positive-definite metrics, valid overlaps, inverse/composition residuals, explicit units and budgets |
| Coupled fields | Typed coupling operators and material laws with energy accounting; deterministic clock scheduling | Analytic reference, stability/convergence study, conservation or quantified dissipation, cross-solver comparison |
| Magnetism and switching | Preserve current analytic fields/relay; add versioned material constitutive models and magnetization dynamics where justified | Measured/calibrated parameters, hysteresis/dynamics reference, thermal/noise assumptions, counterexamples |
| Electricity/battery/charging | Separate circuit, magnetic coupling, electrochemical state and thermal state | Explicit chemistry/OCV/resistance/kinetics/aging data; charge/energy accounting and uncertainty; reduced reservoir never relabelled as chemistry |
| Acoustic/thermal/mechanical fields | Distinguish pressure, particle velocity, displacement, energy and temperature | Units/material density/heat capacity, boundary conditions, reference solution and device audio transfer calibration |
| Spectrum and polarization | Retained wavelength bins and Stokes/Jones state where assumptions hold; Faraday and Zeeman transforms | Material Verdet/transition parameters, units/line shapes/selection rules, instrument response, independent numerical/reference data |
| Observer color | Integrate admitted spectrum through declared observer/instrument response, then convert to display | Exact observer table, illuminant/adaptation when relevant, gamut and radiometric scale, no RGB-only source reconstruction claim |
| Quantum observation | State/density/channel records; expectation values, Born distributions and uncertainty as views | Phase-sensitive tests, normalization/positivity/CPTP checks and independent backends; measurement loss explicit |
| Astronomical observations | Released catalogue/image/light-curve inputs with frame, epoch/time scale, detector and uncertainty | FITS/WCS/time/coordinate comparisons, provenance, missing data, calibrated instrument forward models |

Magnetism can affect emitted/transmitted light through physical mechanisms such as magneto-optic rotation and spectral splitting. It does not replace the observer model. A physical color pipeline starts with a spectrum and a declared observer response, with magnetic effects in the material/light model. Surface already preserves the [CIE 1931 2° observer table](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer); moving to retained-spectrum observations is a larger task than assigning a magnetic field an RGB hue.

## Geometry and the cosmic machine idea

Local Euclidean charts are useful computational representations. Their arrangement on a screen is not evidence that the whole universe has one Euclidean metric, nor that chart distance is an interaction energy. Astronomy needs reference frames, observation epochs, propagation delays, distances with uncertainty and model-specific dynamics. [Astropy's coordinate system interface](https://docs.astropy.org/en/stable/coordinates/) is a reference for explicit frame transformations; it has not been integrated by merely linking it.

The existing Gaia slice projects catalogue directions on a unit sphere; depth is a camera direction cosine, not measured stellar distance. A future pulsar adapter must retain original time tags and clocks, timing solution, phase model, detector response and uncertainty. An explicit grammar may map phase/amplitude/spectral observations to symbols. Validate aliasing, noise, false detection and null controls. A pulse-to-symbol mapping is a computational interpretation, not proof of intentional language or the ability to control a star as a programmable machine.

Galaxies, black holes and other astrophysical systems can be modeled as dynamical systems with observables and chosen coarse-grained states. Establish state variables, transition law, time scale and validity domain before an FSM abstraction. General-relativistic dynamics and detector observations cannot be inferred from shared binary representation.

## Preserve replay while changing the renderer

Version state schemas and observation transforms separately. Record initial state, admitted input sequence, seeds, solver steps and explicit floating-point/platform tolerances. Keep deterministic reference outputs and negative tests. Current physics/session replay does not capture every display trail or acoustic phase. A future frame/sample-exact replay requires those states plus timing and display/audio transform versions. Exporting a scientific state and reproducing a device image are distinct gates.

Keep native rasterization throughout. New numerical libraries may act as independent offline references; admitting one does not require embedding its renderer or UI. Each implemented increment must remain usable while its broader scientific dependencies stay visible.
