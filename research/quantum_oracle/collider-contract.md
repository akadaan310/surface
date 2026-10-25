# QUANTUM ORACLE observed collider CSV contract

`collider.py` implements `quantum-oracle.collider-csv/1`, a standalone bounded parser and kinematic analysis of authentic observed-derived data. It requires Python 3.10+ and NumPy. It has no native-renderer dependency and no external physics-library dependency. The full original G4 remains **partial**: this CSV does not supply ROOT/HepMC parsing, detector calibration, weights, systematic uncertainties or a full collision-physics analysis.

## Source and preservation

[CERN record 5201](https://opendata.cern.ch/record/5201), authored by Thomas McCauley, provides 100,000 selected CMS DoubleMu Run2011A dimuon-candidate rows, published in 2019 under CC0-1.0. CERN identifies this as an education/outreach derivative unsuitable for a full physics analysis. Its documented selection requires two opposite-charge muons, both with `abs(eta)<2.4`, at least one global muon, and pair mass between 0.3 and 300 GeV. The record defines energy and momentum in GeV, angle phi in radians, charge, tracker/global types, and run/event identifiers. [Original metadata API](https://opendata.cern.ch/api/records/5201).

The exact retrieved API response is retained in [cern-5201-record.original.json](data/cern-5201-record.original.json). [Provenance](data/cern-5201-provenance.json) binds transport, licensing, the original metadata and both logical and compressed data identities:

| Identity | Value |
|---|---|
| Published logical bytes | 13,935,840 |
| Published Adler32, verified | `5b87a72a` |
| Locally pinned logical SHA-256 | `58caa45c580f8bcf4b457281c8525a56de0e0b8eb0e0b29e86a9b655a8e64d35` |
| Deterministic gzip bytes | 5,789,915 |
| Gzip SHA-256 | `f9e84321a893ff36120d88e3f1831d8398e4e42b717a7d72f07c90db101e4561` |
| Original API response SHA-256 | `7406b16c5925e2a263f75a76a2c6b0479995405122c3553a205b668df78c9668` |

[cern-5201-Dimuon_DoubleMu.csv.gz](data/cern-5201-Dimuon_DoubleMu.csv.gz) is a lossless transport wrapper with level 9 compression, mtime zero and empty filename. Decompression reconstructs the original CSV bytes exactly, including line endings, decimal spelling and row order. SHA-256 is an identity witness, not an author signature. No record was removed or changed to improve consistency.

The initial analysis receipt is preserved at [collider-cern5201-analysis.json](evidence/collider-cern5201-analysis.json), and the admission-hardening receipt at [collider-cern5201-analysis-v2.json](evidence/collider-cern5201-analysis-v2.json). The latest detailed full-source result, after separating unverified fixture provenance, is [collider-cern5201-analysis-v3.json](evidence/collider-cern5201-analysis-v3.json); each pins the implementation it actually executed. An additive [signed-integer admission fix receipt](evidence/collider-signed-bounds-fix.json) binds the subsequent code change and its scoped checks. That change rejects extreme integer arrays before floating conversion; the scoped fix receipt does not itself rerun the full source. The overall scientific test runner also executes the full-source test when selected. These are repeated executions on the same data, not separate observational experiments.

## Typed source-to-event map

The supported transport grammar is exactly the 21-column ASCII header in `HEADER`, followed by unquoted comma-separated rows. LF and CRLF records are supported; arbitrary CSV dialects, quoted cells, missing columns, empty rows, nonfinite values and unknown muon types reject. Finite decimal and scientific-notation tokens are bounded to 32 characters and a final decimal-place exponent between -16 and 6. All original spellings remain in the retained source.

The default analysis verifies the fixed published identity before attaching CERN observational provenance. The explicit `require_published=False` mode admits bounded user-supplied fixtures but labels them `unverified user-supplied controlled input`, leaves `source_url` null, and sets `published_source_verified=false`. Similar field names or numerical results cannot confer observational provenance.

Run and event are parsed as unsigned 64-bit integers directly from decimal integer tokens. They never pass through floating point; the regression case `9007199254740993` remains exact. `row_index` is a distinct zero-based file-row coordinate. Repeated run/event IDs would be retained and counted rather than conflated with row identity. This source has 100,000 distinct run/event pairs.

`Event` stores the source SHA-256, half-open byte range `[byte_start,byte_end)` for the complete original row, and 21 half-open field spans into the uncompressed original source. The row interval includes its line terminator; field intervals exclude commas and terminators. Source coverage begins at byte 88 after the header and ends at byte 13,935,840. The first run/event pair is `(165617,74601703)`, and the last is `(165548,604313280)`. The parser supplies these witnesses; constructing a record manually does not prove that its claimed source exists.

`Muon` binds a G/T type, `FourMomentum`, nonnegative transverse momentum, eta, phi and integer charge ±1. Eta/phi are retained as printed observations; the code does not reconstruct or silently replace them. `FourMomentum` is ordered `(E,px,py,pz)`, unit `GeV;c=1`, Minkowski signature `+---`. Negative energy rejects; unlike unit strings reject without conversion. Negative **mass squared** is preserved because inconsistent or rounded observed vectors must remain inspectable. Calling `mass()` on a negative central squared mass rejects `SPACELIKE`; it never manufactures zero mass. `Event.published_mass` must be nonnegative and remains distinct from a recomputed mass.

## Kinematics and precision assumptions

For a total four-vector `P=p1+p2`, the recomputed invariant is

```text
s = E_total^2 - px_total^2 - py_total^2 - pz_total^2
M = sqrt(s), only when s >= 0
```

The scalar implementation uses `math.fsum` on signed squared components. An independent NumPy CSV reader extracts the eight momentum columns, and a vectorized implementation sums the pair and computes the spatial squared norm with `einsum`. The full-source comparison requires exactly equal parsed component arrays and squared-mass differences below `64*eps*max(1,sum(P_component^2))`. IDs are deliberately excluded from the floating-point reference reader. This is independent parsing and numerical implementation using Python/NumPy; it is not two independently developed detector/physics software backends.

The invariant and passive Lorentz-boost conventions follow the [Particle Data Group kinematics review, §§49.1–49.2](https://pdg.lbl.gov/2025/reviews/rpp2025-rev-kinematics.pdf). A frame moving with vector beta has `E'=gamma(E-beta dot p)` and the corresponding parallel-momentum transform. The code applies the full linear boost matrix and conservatively maps component interval half-widths through its absolute values. Tests explicitly labelled synthetic use `(5,4,0,0)`, rest mass 3, a boost beta `(0.8,0,0)` to its rest frame, an inverse boost, and a back-to-back pair of total mass 10. These are mathematical controls, not additional observed events.

For the source comparison, each token's half-step is inferred from its displayed decimal exponent. For example, `1.2300` gives 0.00005, while `123.4` gives 0.05. **The assumption is rounding to the nearest displayed place.** CERN's file does not certify that this alone accounts for all upstream processing or measurement uncertainty.

If a total component has central value `a_i` and half-width `d_i` (the sum of the two muon half-widths), a conservative algebraic interval bound is

```text
B_quantization = sum_i (2*abs(a_i)*d_i + d_i^2)
B_numeric = 64*eps*max(1,sum_i a_i^2)
s_true in [s-B, s+B], where B=B_quantization+B_numeric
```

The real-mass interval is the square root of its intersection with `[0,infinity)`; an entirely negative squared interval has no real-mass interval. Compatibility means this interval overlaps the independently printed M interval. It does not mean equality of central values. The zero lower endpoint of a rounding interval is explicitly different from clipping a negative central invariant to zero. Detector errors, calibration covariance, reconstruction choices and systematic effects are unavailable and are not invented to force agreement.

## Actual results and retained counterexamples

The final analysis covers all 100,000 rows, with no duplicate run/event pairs and no violations of the stated selection when applied to the printed columns. All momentum values from the independent NumPy reader match the typed parser exactly. The maximum scalar/vector squared-mass difference is `9.313225746154785e-09 GeV²`, within the declared magnitude-dependent binary64 bound.

The claim that every printed mass agrees with the printed four-momenta under the decimal-rounding assumption is **REJECT**:

| Observation | Count/result |
|---|---:|
| Mass intervals overlap | 98,619 rows |
| Mass intervals fail to overlap | 1,381 rows |
| Pair central mass squared is negative | 1 row |
| Individual muon central mass squared is negative | 1,410 candidates |
| Individual muon squared-mass interval is entirely negative | 949 candidates |
| Maximum difference between real central pair mass and printed M | 0.8291972087026647 GeV |

All 1,381 pair-mass failures and all 949 individual-muon failures are retained with source IDs and byte ranges in the receipt. The negative pair is separately retained. The first pair discrepancy is row 46, run 165617, event 75887636, bytes `[6482,6630)`: the recomputed central mass is about 88.24504554 GeV and its rounding interval is approximately `[88.24464361,88.24544747]`, whereas printed M is 88.2438 GeV. The negative pair is row 16174, run 166784, event 47703178, bytes `[2250846,2250995)`, with central `s≈-0.02943865 GeV²` and printed M 0.4148 GeV. No cause of these differences is established by this adapter.

These findings concern consistency of this released educational table. They neither establish a violation of relativistic kinematics nor invalidate an underlying CMS physics analysis. No discovery, fitted resonance significance, calibrated detector conclusion or full G4 acceptance is claimed.

## Resources, failures and replay

`Limits` can only narrow the hard bounds: 16 MiB source or stored file, 100,000 rows, 1,024 bytes per line, 4,096 retained counterexample records and 60 seconds per parse/analysis operation. Real numerical components are bounded in magnitude by `1e6`; boost beta squared must be less than `1-1e-12`. Two float64 analysis buffers use at most 7.2 MB; source, reference-reader arrays, unique-ID set and bounded report records add overhead. Parsing streams typed rows rather than retaining 100,000 Event objects. The limits are algorithmic bounds, not an OS memory sandbox.

The parser checks a monotonic deadline while scanning every row. Bulk NumPy operations check the same deadline before and after; their finite shape bounds are not preemptive operating-system cancellation. Compressed reads stop at `max_bytes+1` decompressed bytes, rejecting expansion beyond the quota. Counterexample-budget exhaustion rejects the analysis instead of presenting a silently truncated report. `ColliderError.code` distinguishes type/format/unit/identity failures, resource exhaustion, expired time and transport blockage.

`download_published` calls only the fixed CERN file URL with curl's 60-second maximum and 16 MiB transfer ceiling, plus a subprocess timeout. It verifies the published Adler32 and byte count and the locally pinned SHA-256 before admitting the data. Curl and normal HTTPS trust/proxy configuration are required for reacquisition; offline replay uses the preserved gzip. The CLI refuses to overwrite an existing archive or output receipt.

```sh
.venv/bin/python -B -m unittest discover -s research/quantum_oracle/tests -p test_collider.py -v
.venv/bin/python -B research/quantum_oracle/collider.py \
  --input research/quantum_oracle/data/cern-5201-Dimuon_DoubleMu.csv.gz \
  --output /tmp/collider-cern5201-new-replay.json

# Optional fresh acquisition into new, nonexistent destinations:
.venv/bin/python -B research/quantum_oracle/collider.py --download \
  --archive /tmp/collider-cern5201-new.csv.gz \
  --output /tmp/collider-cern5201-new-download-analysis.json
```

The test suite covers exact source reconstruction/offsets, large integer IDs, genuine full-source analysis, independent computations, synthetic boost/invariant controls, negative and nonfinite admission, malformed grammar, compressed expansion, fixed deadlines and counterexample retention limits. Successful execution means the scoped adapter and its controls ran; the scientific consistency claim is graded separately and remains rejected as reported above.
