# Native PHANTOM and Quantum Oracle bridge

`include/surface/phantom.hpp` and `src/phantom.cpp` provide bounded C++20 semantic ports of selected functions inspected in the supplied PHANTOM Division VIII v0.4, Quantum Oracle v0.1 and Quantum Oracle v3 archives. These functions have no browser, JavaScript, WebView, GPU API, Python or third-party runtime dependency. Python is used only by the offline catalogue preparation script.

During the native semantic port, the supplied archives were first inspected as bytes and text without executing their code. A subsequent, separate foundation replay ran the documented original checks: **145 original unit tests passed and 125 deterministic files regenerated exactly**, with unchanged source/archive bytes. [FOUNDATION_REPLAY.md](FOUNDATION_REPLAY.md), `evidence/foundation-replay.json` and its raw logs hold that fresh evidence. Old archived passing reports remain historical evidence; the new replay does not derive acceptance from those reports alone. `docs/PHANTOM_SOURCES.json` records the earlier inspection-stage source paths and hashes. The native implementation, fresh original baseline replay and full commission gates remain distinct scopes.

## What was carried forward

| Upstream source | Native work | Boundary |
|---|---|---|
| PHANTOM `division8/kernel.py` | Ripple full-adder, finite unsigned word state, INJECT, INVERT, ASSIGN and ADD | 1–64 bits, wrap overflow, explicit transition trace; not the full 4096-bit Python interpreter |
| PHANTOM `division8/contracts.py` | Exact source-byte provenance and strict finite input policy | New native numeric record; no claim of wire compatibility with `SUBSTRATE-K/1` or the draft v2 IR |
| Oracle v0.1 `core.py` | Ideal H/X/Y/Z/S/T/RX/RZ/CX state-vector gate semantics | At most 6 qubits and 256 operations; no hardware, shots, channels, Lindblad solver, accelerator, discovery or calibration |
| Oracle v3 `atlas_quantum/core.py` | Real/imaginary binary64 interleave, explicit basis order, Fubini–Study pure-state distance | Finite normalized states; separate conversion resolves v0.1/v3 qubit numbering |
| Native implementation | Presence versus toggle sample codec, SHA-256 conversion records, admission and tamper checks | Newly implemented component, not claimed to be a recovered Surface file |

These are semantic translations, not byte-for-byte copies of upstream Python. The input archives do not supply a general public code-license grant that this document can extend. Original ownership and supplied terms are retained.

## Exact finite numeric records

`encodeNumeric(span<const double>, NumericType, Endian, allowLoss)` accepts a contiguous dense range of at most 65,536 finite doubles. Its C++ span represents a dense numeric region; callers remain responsible for valid memory lifetime. NaNs and infinities are rejected. Integers require an exact integral value within the declared type's range. There is no string coercion, saturating integer conversion or silent wrap in numeric import.

Supported types are unsigned/signed 8-, 16- and 32-bit integers, binary32 and binary64. Gaia uint64 identifiers use the separate atlas integer path so they never pass through a `double`. Little and big endian are explicit. Native host byte order does not change serialization.

Every `NumericRecord` retains the exact original finite double values as binary64 little-endian bytes, plus their SHA-256 and the encoded payload's SHA-256. Binary64 retains negative zero. The converter rejects any loss by default, including negative zero becoming ordinary integer zero. Explicit `allowLoss=true` permits binary32 rounding and zero-sign loss, recording changed-value count, maximum absolute error and whether signed zero survived. Nonfinite float32 overflow and out-of-range/fractional integer conversion are always rejected. The source bytes remain available through `numericSource` even when an explicitly accepted conversion loses precision.

`decodeNumeric` checks bounded sizes, digests and byte order, decodes the retained source, then independently repeats the declared conversion and compares bytes and all loss fields. Changing endian metadata or falsely claiming an exact conversion is rejected when it disagrees with the bytes. If two declarations yield identical numeric values and bytes, they are representationally compatible; the record is not an authenticated statement about a human author's intention. Hashes detect content changes, not authorship. Input precision already lost before a value reaches this API cannot be recovered.

The SHA-256 implementation follows the [NIST Secure Hash Standard](https://csrc.nist.gov/pubs/fips/180-4/upd1/final). Tests use independent empty-message, `abc`, and 56-byte multi-block known-answer vectors. This is an integrity implementation, not a claim of [CAVP validation](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/secure-hashing). Input size for the exposed hash function is capped at 16 MiB.

## Word transitions and pulse meaning

For an 8-bit word with numeric value 7 (`00000111`), injecting at place zero produces 8 through a carry chain, while inverting place zero produces 6. Assigning 1 at place zero keeps the state 7. The native test checks these distinct results and their changed-place lists. At the word boundary, the addition trace retains the final carry and sets `overflow=true`; 255 plus one wraps to zero in an 8-bit state. The 64-bit boundary is explicitly checked without shifting by the word width.

`PulseMode::Presence` means each sample directly specifies its state. `PulseMode::Toggle` means a 1 changes the preceding state and a 0 retains it. Initial state and sample order are part of the record. For samples `[1,1,0,1,0,0]` starting from 0, presence events are `[1,1,0,1,0,0]`, whereas toggle events are `[1,0,1,1,1,0]`. Both decode exactly under their declared semantics. This is a discrete codec; it does not imply pulsar timing, a pulse-shape calibration, or quantum measurement.

## A real inherited basis-order mismatch

Oracle v0.1's `kron_all` local-gate construction treats **qubit zero as the most significant index bit**. Oracle v3's `complex_pairs`, `basis_lift` and `hadamard` explicitly label **qubit zero as the least significant bit**. Silently swapping these conventions would conflate `|01>` and `|10>`.

The native `simulateCircuit` follows v0.1 and labels its `QuantumState` accordingly. `reorderQubits` performs explicit index-bit reversal when converting between the two order conventions. The tests apply X to qubit zero in a two-qubit state: probability one first occurs at index 2 under the native/v0.1 convention, then at index 1 after conversion to v3's convention. Conversion back recovers the identical amplitude array.

`serializeState` stores exact binary64 little-endian real/imaginary pairs, qubit count and declared basis order. It requires a power-of-two dimension for 1–6 qubits, finite amplitudes and norm error at most `1e-10`. The state-record hash covers a version tag, qubit count, basis order and complex payload. `deserializeState` checks both numerical provenance and this interpretation hash. A changed basis-order declaration without a corresponding new record is rejected.

These records represent classical mathematical arrays. They are not a physical qubit-memory format, hardware instruction record, tomography reconstruction or reversible encoding of a measurement outcome into its original state. `pureStateDistance` computes `acos(|<psi|phi>|)` on admitted normalized states; it treats global phase as equivalent while preserving relative-phase distinctions. Tests distinguish states with equal Born probabilities but opposite relative phases.

## Fresh verification and remaining scope

`tests/test_phantom.cpp` contains independent byte fixtures for signed integer endianness, binary64 negative zero, binary32 rounding, retained-source recovery, altered payload/endian/loss metadata, finite-number admission, word carry chains including width 64, distinct pulse semantics, Bell probabilities `[0.5,0,0,0.5]`, phase-sensitive H–Z–H interference, RX(π), invalid gates/angles, qubit basis-order conversion, exact complex roundtrip, global phase equivalence and orthogonal pure-state distance.

The archived v2 acceptance matrix starts G0–G7 as `NOT_STARTED`, and the archived Physical Cosmos continuation starts G00–G16 as `NOT_STARTED`. Their initial statuses remain preserved. The current assessment is in [GATE_REPORT.md](GATE_REPORT.md) and `evidence/commission-gates.json`. The documented original baseline has now been freshly replayed with scope: 145 original tests, 129 retained scientific files verified and 125 deterministic files regenerated exactly. Four original measured files were excluded from regenerated-byte comparison while their retained bytes were still verified; their identities are recorded in the replay receipt.

That successful baseline does not recover the lost workspace or certify the eight historical Octave comparisons. The absent full Language Lab corpus, a second quantum backend, broader density/channel conformance, calibrated hardware compilation, collider data, held-out generator induction, billion-source ingestion, complete N-chart topology, real pulsar timing and full integrated commission replay remain separate outstanding obligations. No stochastic draw or visible ink response is promoted to a quantum-hardware result.

The current native app may choose to use these reference APIs or expose them through future nonvisual controls. Their existence in the library does not by itself prove an interactive mode is connected; app integration is documented separately.
