# Independent bounded adapter challenge

This is a scientific/code challenge of `collider.py` and `circuits.py`, performed
on 2026-10-25. It is not whole-release approval or completion of Oracle G4/G5.
The companion executable is [review-adapter-probes.py](review-adapter-probes.py).
Final execution receipts should bind the finalized source and test bytes;
this working review does not record provisional source hashes.

## Findings and corrections

1. **P2 — signed integer admission overflow.** The collider vectorized path used
   `abs(momentum)` before converting its original integer dtype. With an
   `int64` minimum value in a spatial component, absolute value wrapped negative,
   bypassed the `1e6` component limit, and produced a mass squared of
   `-8.507059173023462e37`. The same defect affected `int32` minimum values.
   The corrected implementation compares against lower and upper bounds without
   signed absolute-value overflow. Both regression inputs now reject, while the
   admitted integer kinematic control remains valid.

2. **P1 — calibration source identity detached from executable values.** A
   normal `dataclasses.replace` of a loaded historical snapshot could set every
   gate duration to zero and reported error to one, retain the original IBM
   source digest, and pass compilation and surrogate simulation. Future sample
   dates in 2099 also passed despite the historical 2025 calibration date.
   This did not require interpreter tampering. The corrected snapshot retains
   the immutable source bytes and re-derives selected fields against their
   digests in its constructor; replacement values and future samples reject.
   Supplied digests and revision identifiers remain integrity assertions, not
   independent external authentication.

3. **P2 — direct compiled record admitted forged calibration metadata.**
   Replacing native durations and errors and updating the duration sum yielded
   an accepted compiled record, though simulation with the authentic snapshot
   rejected it. The corrected record retains the validated snapshot and checks
   every native operation against it during construction.

4. **P2 — direct snapshot coupling expansion.** Repeating the one authentic
   directed edge 10,000 times passed the old constructor. The corrected
   constructor enforces the selected-subgraph bounds and uniqueness before
   traversing the graph, as well as source-derived field equality.

Root review independently identified and coordinated the collider distinction
between authenticated CERN data and unverified controlled input, plus explicit
rejection of header-only input. Those findings are outside this probe's credit.

## Independent controls and review limits

The bounded suite checks the four findings and direct full-unitary record
forgery. It also checks 1,000 deterministic random passive Lorentz boosts and
their inverses. The observed maximum scaled invariant-mass-squared residual in
the initial challenge was `3.4891528192899563e-16`, within the declared
`64*binary64_epsilon` scale bound. Another 100 vectors with 16 rounding-box
corners each are evaluated using Python Decimal arithmetic, independently of
the production float calculation, to challenge the conservative interval bound.

The review read both modules, their tests, source admission paths, resource
guards and contracts. The full 100,000-event analysis was not repeated for this
challenge. The finite circuit unitary checks and serial T1/readout surrogate
match their declared scope; they do not model T2, pulse scheduling, crosstalk or
current hardware performance. Cooperative transpiler deadlines cannot interrupt
a hung native pass and require the documented outer process supervisor.

The collider's retained mass discrepancies are counterexamples to a printed
table consistency claim under an explicit decimal-rounding assumption. They do
not establish detector uncertainty, a physical discovery, or a violation of
relativistic kinematics. No laboratory execution, calibrated detector analysis,
current-provider validation, or independent physics-library comparison was
performed in this challenge.

Replay from the repository root:

```sh
.venv/bin/python -B research/quantum_oracle/evidence/review-adapter-probes.py
```

After the corrections, all eight independent challenge methods passed in
0.258 seconds. No unresolved substantive defect remains from this bounded
challenge; the stated exclusions and outer-supervisor requirement remain.
