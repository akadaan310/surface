# Primary scientific and engineering sources
Research checked for this commission on 25 October 2026.

These sources support the scientific models, data choices and tool capabilities. They do not establish that SURFACE has implemented them. Pin the actual version, license, dataset release and acquired-byte hashes during integration. Review third-party code and data before executing or redistributing them.

## Physical fields, chemistry and optics

| Key | Source | Role and scope |
|---|---|---|
| S01 | [Meep material models](https://meep.readthedocs.io/en/latest/Materials/) | Maxwell constitutive models, dispersion, anisotropy, loss, normalized units and gyrotropy limitations |
| S02 | [Meep Faraday rotation tutorial](https://meep.readthedocs.io/en/latest/Python_Tutorials/Gyrotropic_Media/) | Gyrotropic dielectric tensor, polarization rotation and analytical/numerical comparison |
| S03 | [ngspice documentation](https://ngspice.sourceforge.io/docs.html) | Circuit models, transient analysis and integration interface |
| S04 | [STMicroelectronics AN5961, Wireless power transfer coil design](https://www.st.com/resource/en/application_note/an5961-wireless-power-transfer-coil-design-stmicroelectronics.pdf) | Inductive coupling, alignment, circuit design and stated approximations; July 2023 |
| S05 | [PyBaMM DFN model](https://docs.pybamm.org/en/pybamm-v26.10.1.1/source/examples/notebooks/models/DFN.html) | Electrochemical transport, charge conservation and reaction model |
| S06 | [PyBaMM thermal models](https://docs.pybamm.org/en/pybamm-v26.10.1.1/source/examples/notebooks/models/thermal-models.html) | Ohmic, reaction, reversible and contact heating, geometry and cooling |
| S07 | [k-Wave project and scientific references](https://github.com/ucl-bug/k-wave/blob/main/README.md) | Acoustic propagation methods, media, absorption and numerical reference literature |
| S08 | [NIST atomic spectroscopy, Zeeman effect](https://www.nist.gov/pml/atomic-spectroscopy-compendium-basic-ideas-notation-data-and-formulas/atomic-spectroscopy-zeeman) | Weak-field splitting and angular-momentum conditions |
| S09 | [NIST Atomic Spectra Database](https://www.nist.gov/pml/atomic-spectra-database) | Evaluated levels, wavelengths and transition data with references |
| S10 | [CIE 1931 2° observer functions](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer) | Official 1 nm color-matching dataset; DOI 10.25039/CIE.DS.xvudnb9b |
| S11 | [Shaheen et al., Ultralarge magneto-optic rotations and rotary dispersion in terbium gallium garnet single crystal](https://opg.optica.org/ao/abstract.cfm?uri=ao-54-17-5549) | Experimental material response; Applied Optics 54, 5549–5554 (2015), DOI 10.1364/AO.54.005549 |
| S12 | [ICC sRGB encoding registry](https://registry.color.org/rgb-registry/srgb) | Display primaries, white point and encoding transfer function |
| S32 | [NIST OOMMF overview](https://math.nist.gov/oommf/doc/userguide21a3/userguide/Overview_OOMMF.html) | Micromagnetics, magnetization structures, hysteresis and dynamical modeling |
| S33 | [MuMax3 design and verification](https://arxiv.org/abs/1406.7635) | Micromagnetic simulation and comparison with analytical/standard problems |

The cited PyBaMM version was accessible during research. Use a compatible verified version in the working environment; do not silently change upstream dependency locks. The TGG reference identifies an experimental basis; parameter-data acquisition and reproduction are separate implementation tasks.

## Astronomy, coordinates and signals

| Key | Source | Role and scope |
|---|---|---|
| S13 | [ESA Gaia DR3 contents](https://www.cosmos.esa.int/web/gaia/dr3) | Released catalogue coverage and count; 1,811,709,771 sources |
| S14 | [ESA Gaia DR4 release page](https://www.cosmos.esa.int/web/gaia/data-release-4) | Scheduled 2 December 2026 as of this commission; availability must be rechecked |
| S15 | [Bailer-Jones et al. GeDR3 distance catalogue](https://bailer-jones.www3.mpia.de/gedr3_distances.html) | Posterior distance estimates, asymmetric uncertainty and limitations of simple parallax inversion |
| S16 | [Astropy coordinates](https://docs.astropy.org/en/stable/coordinates/index.html) | Unit-aware coordinate frames, positions and velocities |
| S17 | [Astropy cosmology](https://docs.astropy.org/en/stable/cosmology/index.html) | Declared cosmological models and distinct distance measures |
| S18 | [DESI DR1 official documentation](https://data.desi.lbl.gov/doc/releases/dr1/) | Spectra/redshifts, footprint, data model, known issues and CC BY 4.0 terms |
| S19 | [IVOA HiPS 1.0 Recommendation](https://www.ivoa.net/Documents/HiPS/20170519/index.html) | Hierarchical progressive survey access based on HEALPix; DOI 10.5479/ADS/bib/2017ivoa.spec.0519F |
| S20 | [ATNF PSRCAT official download page](https://www.atnf.csiro.au/research/pulsar/psrcat/download.html) | Pulsar parameters and release identity; pin the obtained catalogue |
| S23 | [NANOGrav PINT documentation](https://nanograv-pint.readthedocs.io/en/latest/) | Pulsar timing, clock corrections, ephemerides, model components and phase tools |
| S24 | [NASA Fermi pulsar ephemerides](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/ephems/) | Timing model validity for the selected observation; use with corresponding event/spacecraft data |
| S25 | [Fermi-LAT Collaboration, Third gamma-ray pulsar catalogue](https://arxiv.org/abs/2307.11132) | Observed pulse profiles, spectra and multi-band comparisons; 2023 primary collaboration paper |
| S26 | [REBOUND WHFast documentation](https://rebound.hanno-rein.de/integrators/whfast/) | Symplectic integration for suitable gravitational systems; choose integrator by regime |
| S28 | [Sean Carroll, Lecture Notes on General Relativity](https://preposterousuniverse.com/grnotes/) | Manifolds, metrics, spacetime and relativistic modeling foundations |

Gaia official-domain search results supplied catalogue/release evidence when direct retrieval returned an access error. The primary Gaia DR3 survey paper is also available as [Gaia DR3 summary](https://www.aanda.org/articles/aa/full_html/2023/06/aa43940-22/aa43940-22.html). Endpoint accessibility from an implementation environment must be tested before scheduling bulk jobs.

NASA's [Fermi pulse-phase tutorial](https://fermi.gsfc.nasa.gov/ssc/data/analysis/scitools/pulse_phase_tutorial.html) provides the operational phase-assignment workflow. Instrument-specific timing and spectral processing must preserve their respective valid time/response conventions.

## Representation, topology and formal models

| Key | Source | Role and scope |
|---|---|---|
| S21 | [IBM Qiskit bit-ordering conventions](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering) | Basis indices, circuit/register order and statevector interpretation |
| S22 | [GUDHI documentation](https://gudhi.inria.fr/python/latest/) | Cell complexes, filtrations, persistence and their algorithmic conditions |
| S27 | [TuLiP tutorial](https://tulip-control.github.io/tulip-control/tutorial.html) | Continuous-state abstraction and controller synthesis for supported hybrid classes |
| S29 | [Storm supported model families](https://www.stormchecker.org/documentation/background/models.html) | Markov chains, decision processes and Markov automata |
| S30 | [ECMAScript JSON serialization specification](https://tc39.es/ecma262/multipage/structured-data.html#sec-json.stringify) | JavaScript serialization behavior; pin the implementation/runtime used |
| S31 | [RFC 8785, JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785) | Canonicalization rules and IEEE-754 serialization implications |

## Implementation library selection

Recommended roles, subject to compatibility and license checks:

- Meep for bounded optical/EM reference problems; an appropriate FEM/finite-volume solver for selected quasistatic or coupled fields.
- OOMMF or MuMax for magnetic switching/hysteresis references, subject to available CPU/GPU/runtime support.
- ngspice for electrical circuit dynamics; PyBaMM for calibrated electrochemical and thermal battery models.
- k-Wave for acoustic references when its runtime is available.
- Astropy, suitable FITS readers and columnar data tools for scientific ingestion and coordinates.
- HEALPix/HiPS tooling for angular partitioning and progressive sky products.
- PINT for pulsar timing; a compatible independent timing backend for selected crosschecks.
- REBOUND for appropriate orbital dynamics.
- GUDHI for bounded topological analysis.
- Existing admitted Quantum Oracle backends for quantum-state/operator comparisons.
- TuLiP/Storm only where their supported formal models match the proposed abstraction.

A dependency candidate is not an installed adapter. Each admitted adapter needs an exact version, input/output contract, fixture, conformance result and observed resource cost.

