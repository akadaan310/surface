# QUANTUM ORACLE × PHANTOM — V3 N-ATLAS AND QUANTUM REPRESENTATION CONSTITUTION

**Purpose.** Extend the supplied V2 commission, without rewriting either of its immutable upstream input archives. This package contains an executable, bounded N-chart + binary/quantum representation seed, tests, and the full V3 execution commission. The original V2 commissioning package is bundled intact as an input and must be checked independently by the continuation session. This package is NOT the implementation of the full V2 astrophysical/collider/hardware system.

## I. Mathematical foundations

1. Define an N-chart atlas A = (I, {U_i}, {φ_i}, {o_i}, {g_i}, {F_i}, E, T) with finite chart IDs, each chart's 2D XY Euclidean local coordinates, declared origin o_i, positive-definite metric g_i, function/observable F_i, typed edges E, and admissible maps T_ij. Distinguish abstract atlas coordinate systems from physical locations in ambient space.
2. For N coexisting charts, use origin-placement points in an ambient layout space L with explicitly chosen metric D(o_i,o_j); these distances are NOT automatically function similarity, physical force, or interaction energy. Record units.
3. The same mathematical function can be expressed in distinct charts through transition maps: F_j ◦ T_ij = F_i where compatible, up to specified numerical errors. Derivative, Fourier, energy, filtering, spectral, image, language, and hardware representations may be separate typed observable views, not automatically identical values.
4. Distinguish function space norms (L2, Sobolev H1, operator norm) from chart-origin distance; derive each only with declared domains/measure/boundaries. Compare graph topology, nerves, covers, overlap graphs, adjacency and Čech-style complexes where the necessary conditions hold.
5. Design an environmental grammar assigning laws to chart neighborhoods: coupling K_ij, propagation delays τ_ij, wave evolution, damping, energy transfer and boundary conditions. Validate conservation or quantify dissipation; specify whether the edge is physical, simulated or only logical.
6. Support dynamic N and nested atlas-of-atlases; stop at explicit node, dimension, memory and iteration budgets. Generate multi-chart visualizations of a wave with chronological trace and deterministic replay.
7. Wave alphabet contracts must declare ψ_symbol(x,t;params) along with units, support, normalization, phase, coupling, perturbation and reference implementations. Build transfer/confluence discovery automata using held-out comparisons and null controls.

## II. Binary–quantum correspondences

8. A classical binary word w of width n maps injectively to a computational basis ket |w> in Hilbert space C^(2^n), under declared qubit and basis order; this is a specific mapping, NOT an identification of arbitrary statevectors with classical words.
9. Pure states |ψ> = Σ_w α_w |w> carry complex amplitudes α_w, normalization Σ|α_w|²=1, relative phase and global-phase equivalence. Mixed states use Hermitian positive semidefinite density matrices ρ with trace 1.
10. Measurement maps |ψ> / ρ to outcomes via Born probabilities, not a bijection; explicitly account for the information lost by measurement. Qubit representation can also use Bloch coordinates and appropriate Pauli decompositions, under precision and gauge conventions.
11. Encode complex amplitudes and matrix entries in specified IEEE-754 binary32/binary64 (or higher precision), ordering real/imag components, endianness, basis order, signed zeros/NaNs, quantization and error budgets. Preserve original raw source bytes as a separate witness. There is no universal fixed classical bit pattern inherent to an arbitrary analog qubit state.
12. Record common gates I,X,Y,Z,H,S,T,Rx,Ry,Rz,CX,CZ,SWAP, measurement, reset and channels with typed transition semantics, unitary/CPTP checks and classical-control conditions.
13. Model pairs: (classical XOR ↔ quantum X only when target is a known computational-basis eigenstate); (classical reversible maps ↔ basis-permutation unitaries); (Hadamard ↔ amplitude creation and interference); (classical distributions ↔ diagonal density matrices). Explicitly test where the correspondences break.
14. Define quantum states' Fubini–Study, trace, fidelity and Bures metrics with explicit prerequisites; chart-origin geometry and quantum Hilbert-space geometry remain separate. Build operators mapping one to the other only with witnessed constraints.
15. Define registers/address formats for basis indices, hardware physical qubit addresses, logical qubit IDs, coupler topology, pulse channels, readout records and shot counts. Physical hardware addresses are provider-specific, versioned and must not be confused with memory addresses or computational basis indices.
16. Add the binary layer under every circuit, calibration, control pulse, collider event, astrophysics image and discovered generator: source bytes → structural decoding → typed machine → physics/equations → observations → evidence.

## III. Physics and discovery automata

17. An individual chart may host a Schrödinger state, Bloch sphere projection, phase-space Poincaré map, Fourier image, color/image plane, collider event plot, astronomical time series or scanner detector field. Their overlap edges require explicit maps, not label resemblance.
18. Quantum hardware adapters: transpiler target gate sets/coupling graph, pulse representations where permitted, constraints, noise channels, shot measurements and calibrated evidence. No physical-provider submission without authorization and credentials.
19. Astrophysics adapters: FITS headers/data, WCS, time units, detector calibration, PSF, spectra, photometry, provenance, uncertainty and astronomical physical models.
20. Collider adapters: ROOT and HepMC, event indices, particle graphs, four-momenta, invariant masses, event weights, detector response and systematic uncertainties. Tie per-event machine states to original source offsets/digests.
21. Research state machine: SCOPE→ACQUIRE→HASH→DECODE→MAP→COMPOSE→SIMULATE→PERTURB→DISCOVER→CHALLENGE→VERIFY→GENERATE→REFLECT→ARCHIVE→SELECT. Each state transition has unique ID, input/source identity, deterministic seed where appropriate, typed schema, operation witness, budget and replay coordinates.
22. Generator-of-generators must remain bound to explicit finite grammars and verify generated artifacts independently; generated results become new subjects, without modifying their own past evidence.
23. Discover N-space physical/operational structures under named priors: graph Laplacians, coupled oscillator eigenmodes, Fourier transfer, kernel covariance and spectral clustering. Benchmark against known exact analytic and established numerical references. Treat any novelty claim as a separate proof obligation.
24. Every release gate from V2 remains mandatory. A passing V3 local seed does not close V2's real-data or hardware adapters. Scientific ledger must distinguish ACCEPT/REJECT/UNKNOWN/BLOCKED.

## IV. Acceptance examples

A. Three distinct XY charts display sine, derivative and squared amplitude with origin distances 5 and 5 (given fixtures). B. All 256 opaque byte values reconstruct exactly. C. Classical integer 0 maps to |0>; H produces equal outcomes; complex amplitudes round-trip as little-endian binary64 pairs. D. Global-phase rays have zero Fubini–Study distance. E. Invalid dimensions, units, tampered bytes and state normalization must reject. F. Extend to N charts and dynamic forces with reference solutions. G. Cold-replay full V2 remains unresolved until executed against supplied input archives; record gates honestly.

## Research anchors
- IBM Quantum bit ordering: https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering
- IBM Quantum statevector and gates: https://qiskit.qotlabs.org/learning/courses/use-a-qc-today/quantum-mechanics-basics
- QuTiP documentation: https://qutip.readthedocs.io/
- GNU Octave: https://docs.octave.org/latest/
- Astropy: https://docs.astropy.org/
- CERN ROOT: https://root.cern/
