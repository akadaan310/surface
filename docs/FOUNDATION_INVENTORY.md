# PHANTOM and QUANTUM ORACLE: executable foundation inventory

This is an inventory of the supplied implementations, inspected against their exact archived bytes on 25 October 2026. It separates working source, retained generated programs, prior executed evidence, and commissioned extensions. The machine-readable companion is [`evidence/v3-consolidation-audit.json`](../evidence/v3-consolidation-audit.json): 24 Python source modules with function/class signatures and hashes, 31 generated-artifact records, manifest checks, original V3 test output, and counterexamples.

The native Surface application consumes selected C++ semantic ports and separately admitted adapters. The complete Python PHANTOM interpreter is an offline reference, not a rendering dependency. The native renderer does not use a browser or WebGL. The broader research commission is not complete merely because the reference programs execute. [Native scope](PHANTOM.md), [consolidation assessment](QUANTUM_V3_CONSOLIDATION.md).

## 1. Locate the exact source

The controlling logical archive is `lineage/SURFACE_PHYSICAL_COSMOS_CONTINUATION_v1.zip`. Its exact bytes are published as ordered parts under `lineage/cosmos-continuation-parts/`, with byte offsets, part digests and the unchanged whole-archive digest in `manifest.json`. The materializer reconstructs and verifies those bytes before extraction. Its member `SURFACE_PHYSICAL_COSMOS_V1/upstream/QUANTUM_ORACLE_PHANTOM_V3_N_ATLAS.zip` is byte-identical to the newly supplied V3 ZIP. The V3 member `QUANTUM_ORACLE_V3_EXTENSION/upstream/QUANTUM_ORACLE_PHANTOM_V2_HANDOFF.zip` contains the V2 commission, which contains the original PHANTOM and Oracle inputs.

Run the repository materializer before using the paths below:

```sh
python3 tools/materialize_foundation.py --output build/foundation
```

For an already materialized tree, use `python3 tools/materialize_foundation.py --output build/foundation --check`; the materializer refuses to replace an existing output. Extraction and hash verification do not execute archive members. See `tools/materialize_foundation.py` and its generated `MATERIALIZATION.json` for the exact extraction scope.

| Short name used here | Materialized package root | Authoritative archive root |
|---|---|---|
| `PHANTOM` | `build/foundation/phantom_division_viii_v04/` | `PHANTOM_Division_VIII_v0_4_Handoff.zip!phantom_division_viii_v04/` |
| `ORACLE` | `build/foundation/quantum_oracle/` | `QUANTUM_ORACLE_HARNESS_v0.1.zip!quantum_oracle/` |
| `V2` | `build/foundation/QUANTUM_ORACLE_V2_COMMISSION/` | `QUANTUM_ORACLE_PHANTOM_V2_HANDOFF.zip!QUANTUM_ORACLE_V2_COMMISSION/` |
| `V3` | `build/foundation/QUANTUM_ORACLE_V3_EXTENSION/` | `QUANTUM_ORACLE_PHANTOM_V3_N_ATLAS.zip!QUANTUM_ORACLE_V3_EXTENSION/` |

Every source path below is relative to one of these roots. Keep the reference trees unchanged. Direct fresh outputs to a distinct work directory, not to `runs/release`, `results`, or another retained original. Generated Python is a fixed, reviewed interpreter specialized with declarative IR; arbitrary text supplied to intake is not executable authority. The original source and full research histories remain inside the immutable archives. [PHANTOM sources: `README.md`, `REPLAY_HANDOFF.md`, `division8/generators.py`, `division8/_runtime.py`.]

## 2. What was actually replayed

The existing [`foundation-replay.json`](../evidence/foundation-replay.json) records **145 original unit tests**: 121 PHANTOM tests, 7 companion tests, 8 Oracle tests, and 9 V3 tests. It records **129 retained PHANTOM scientific files checked and 125 deterministic files freshly regenerated exactly**, with 472 admission-ledger events and 56 execution-ledger events. The recorded scientific outcomes remain 26 `ACCEPTED_WITH_SCOPE`, 8 `REJECTED`, and 1 `UNKNOWN`. Four measured timing/test-report files were excluded only from new byte-for-byte regeneration; their retained bytes were checked. See [the complete replay commands and boundaries](FOUNDATION_REPLAY.md).

This consolidation audit independently rechecked all five archive identities and all eleven raw-log hashes in that receipt. It also reran the unchanged V3 suite: **9/9 passed**, and `examples.py` reproduced the retained `demo_results.json` bytes. Those nine checks repeat an existing subset; they do not raise the count of distinct foundation tests to 154. Manifest coverage is 12 V3 entries, 2 V2 input entries, 564 PHANTOM entries and 9 Oracle entries. These manifests exclude their own file where applicable. [Audit receipt](../evidence/v3-consolidation-audit.json).

## 3. PHANTOM generator implementation

### Public synthesis, compiler and reflection functions

| Source and symbol | Actual operation | Important boundary |
|---|---|---|
| `division8/generators.py::make_ir` | Creates a `DIV8-GENERATOR-IR/1` object through `construct_ir` | Exactly seven admitted kinds; typed input/output signatures, parent IDs, bounds and content identity |
| `division8/generators.py::execute_ir` | Executes the fixed runtime; for `word_program`, independently executes a `WordMachine` and verifies its journal | Agreement is checked under the declared finite-word interpretation |
| `division8/generators.py::synthesize_word` | Enumerates finite programs over `ADD`, `MUL`, `XOR`, `AND` and supplied constants | Width 1–16, depth 0–4, candidate cap 1–100,000, 1–65,536 observations; returns `CANDIDATE`, `UNKNOWN`, or `NO_SOLUTION_WITHIN_BOUND` |
| `division8/generators.py::compose` | Builds a typed `composite` with both parent IDs | First codomain must equal second domain; no implicit reinterpretation |
| `division8/generators.py::compile_generator` | Writes a standalone Python program containing the fixed `_runtime.py` interpreter and canonical JSON IR | Compiled stdin is bounded to 64 MiB; errors produce `REFUSED` with exit code 2 |
| `division8/generators.py::reflect_generator` | Enumerates a word program’s complete finite truth table, preimage classes, instruction-labelled graph, injectivity and identity outputs | Implemented for word programs, default width at most 10; other kinds return `UNKNOWN` |
| `division8/_runtime.py::construct_ir`, `validate_ir`, `_validate` | Construct/hash IR and check the exact schema, kind, parameters, types, parent IDs and structural budgets | Hash identity is not a proof of a new operator’s scientific merit |
| `division8/_runtime.py::runtime_execute`, `_charge` | Interpret IR with instruction/support traces and shared work fuel | Child work charges all enclosing frames; nested children cannot reset parent fuel |

The synthesis alphabet and runtime alphabet differ deliberately. Synthesis searches four constructors. The runtime also admits `SUB`. A full PHANTOM word machine supports more operations than either of these grammars. The base word-machine width limit is 4,096; compiled word IR is limited to 64; synthesis is limited to 16; default exhaustive reflection is limited to 10. These are separate contracts. [Sources: the four functions above; `division8/kernel.py::WordSpec`; `docs/FINITE_BOUNDS.md`.]

### Admitted generator kinds

| Kind | Typed signature | Behavior and guard |
|---|---|---|
| `word_program` | `U<w> → U<w>` | Straight-line modular `ADD/SUB/MUL`, `XOR`, `AND`; width 1–64; at most 64 operations |
| `support_update` | `SupportedSamples<w> → Samples<w>` | Adds a declared delta modulo `2^w` on unique, in-range support indices; reports unchanged outside support; width 1–32 |
| `image_roi` | `ImageROIRequest8 → ImageL8` | Same local modular law on a rectangular grayscale region; validates image shape and ordered ROI |
| `audio_window` | `AudioWindowRequest16 → PCM16` | Local modular update with signed PCM16 interpretation and a declared sample window |
| `context_table` | `Context → Label` | Canonical categorical-key lookup; missing/unseen context yields `UNKNOWN`, several candidates yield `AMBIGUOUS`, one yields `RESOLVED` |
| `generator_factory` | `GeneratorRequest → GeneratorIR` | Emits a `support_update` IR with the factory’s ID as parent; width must belong to the factory’s declared admitted set |
| `composite` | Declared input → final child output | Sequential typed composition, 1–16 immediate children, shared budgets |

The runtime caps IR at 16 MiB, nesting at depth four, cumulative structural cost at 64, item count at one million, and logical work at four million. The limits are logical counters; they do not alone enforce OS CPU-time or resident-memory quotas. The higher-level `division8.media.audio_window` rejects overflow by default, while this particular compiled `audio_window` grammar uses modular wrapping. Those are different policies, and a caller must select the intended one. [Sources: `division8/_runtime.py`; `division8/media.py::audio_window`; `docs/FINITE_BOUNDS.md`.]

### Retained generated programs

The authoritative `runs/release/discovery/generator_registry.json` has **five entries**, not one entry for every scientific claim:

| Registry name | IR and executable under `runs/release/discovery/generated/` | Recorded origin/witness |
|---|---|---|
| `word_affine` | `word_affine.json`, `word_affine.py` | Four observed examples; 183 candidate programs examined; `(3*x+1) mod 256`; all 256 inputs validated, including 252 held out |
| `image_roi` | `image_roi.json`, `image_roi.py` | Inferred delta 7 from local updates, then lifted into the typed grayscale adapter |
| `audio_window` | `audio_window.json`, `audio_window.py` | Same inferred local law with declared signed 16-bit sample semantics |
| `support_update` | `support_update.json`, `support_update.py` | Same inferred local law over a finite supported array |
| `support_factory` | `support_factory.json`, `support_factory.py` | Factory for admitted widths `{8,16}` and at most 1,024 items |

The factory additionally retains six child IR/executable pairs: `child_8_0`, `child_8_1`, `child_8_7`, `child_8_255`, `child_16_7`, `child_16_255`. Four byte-width children received 1,024 complete-domain checks in total; two 16-bit children received 4,096 seeded checks in total. All six child executables were invoked independently in the original replayed experiment. This is six selected children from a possible 65,792 width/delta requests, not exhaustive validation of the whole family. `identity_rewrite.json` is an additional retained IR with an empty operation list; there is no matching `identity_rewrite.py` in this directory. [Sources: `division8/experiment_discovery.py::run_experiments`; `factory_emissions.json`; `factory_compiled_checks.json`; `word_heldout.json`; `word_compiled_checks.json`.]

Two other compiler families must not be confused with this registry:

* `division8/experiment_transfer.py::_compile_standalone` specializes its own fixed `STANDALONE` template. `runs/release/transfer/generated/` retains `local_sequence_generator.py`, `image_roi_generator.py`, `audio_window_generator.py`, `context_selector_generator.py`, and `composed_sequence_generator.py`. The first four have `generator_manifest.json` receipts; the last has `composed_generator_manifest.json`. These use different request/result shapes from `DIV8-GENERATOR-IR/1`. The recorded delta-37 and delta-74 transformations are known modular laws with scoped transfer witnesses.
* `division8/structures.py::compile_huffman_generator` freezes a trained `HuffmanCodec` model into `runs/release/structures/huffman_generated.py`. Its JSON interface is `{operation: "encode"|"decode", data_hex: "…"}`. It preserves an exact framed byte-codec contract; it does not promise compression gains on every source distribution.

`division8/circuits.py::synthesize_boolean` separately searches finite Boolean-expression truth tables; `compile_expression` converts an expression to the `Circuit` interpreter. This is distinct from quantum-circuit synthesis. `adder_circuit` and `optimize_circuit` construct and simplify classical Boolean networks. [Sources: named modules; retained manifests; `docs/FINITE_BOUNDS.md`.]

## 4. Practical original-code examples

These examples use the materialized, unchanged reference. They write only to the selected work directory. From repository root, materialize first and then enter the package as shown. The work path below is illustrative and must be fresh where the operation requires it.

### Discover and run a finite word program

```sh
cd build/foundation/phantom_division_viii_v04
python3 -B -m division8 discover --input examples/word_task.json \
  --budget 1000 --depth 2 --output /tmp/surface-word-search.json
python3 -B -m division8 validate \
  --generator runs/release/discovery/generated/word_affine.json \
  --input examples/word_validation.json
python3 -B -m division8 generate \
  --generator runs/release/discovery/generated/word_affine.json --value 255
python3 -B -m division8 compile \
  --generator runs/release/discovery/generated/word_affine.json \
  --output /tmp/surface-word-program.py
printf '%s' '255' | python3 -I -B /tmp/surface-word-program.py
```

The result value is 254. `discover` returns a search report whose `generator` field contains the IR; the entire search report is not valid input to `compile`. `validate` checks the supplied example file only. The separate full-domain witness is `word_heldout.json` plus `word_journals.json`, not an inference from one CLI invocation. [Sources: `division8/__main__.py::execute`; `division8/experiment_discovery.py`; `REPLAY_HANDOFF.md`.]

### Invoke the factory and an already compiled child

```sh
printf '%s' '{"width":8,"delta":7}' | \
  python3 -I -B runs/release/discovery/generated/support_factory.py
printf '%s' '{"values":[0,249,255,10],"support":[0,2]}' | \
  python3 -I -B runs/release/discovery/generated/child_8_7.py
```

The factory returns its child IR under the response’s `value`; it does not return a `.py` program. The second command returns `[7,249,6,10]` with changed-site trace and `outside_unchanged: true`. To compile a newly emitted IR, extract that `value` object and pass it to `compile_generator`/`division8 compile`; do not pass the outer runtime response. [Sources: `division8/_runtime.py::runtime_execute`; `division8/generators.py::compile_generator`.]

### Media adapters and provenance intake

```sh
python3 -B -m division8 ingest --kind text --input examples/book_excerpt.txt \
  --out /tmp/surface-reference-book --max-chunks 1
python3 -B -m division8 project --input /tmp/surface-reference-book \
  --output /tmp/surface-reference-book-projection.json
python3 -B -m division8 generate \
  --generator runs/release/discovery/generated/image_roi.json \
  --input examples/grayscale.png --roi 4 4 12 12 --output /tmp/surface-reference-roi.png
python3 -B -m division8 generate \
  --generator runs/release/discovery/generated/audio_window.json \
  --input examples/tone.wav --window 100 200 --output /tmp/surface-reference-window.wav
```

Intake preserves chunks, source hash and offsets. A per-call quota can pause intake; resumption requires the same source identity. Projection requires complete intake and materializes the source, so this is not constant-memory semantic understanding of an arbitrarily large book. The CLI image example admits L8 PNG; its audio example admits mono PCM16 WAV. Broader bounded RGB/RGBA and multichannel functions exist in `division8/media.py`, with different contracts. [Sources: `division8/ingest.py`; `division8/__main__.py`; `division8/media.py`.]

## 5. Actual state machines and their evidence

| Layer | Source functions/classes | State and transition meaning |
|---|---|---|
| Finite word | `kernel.py::WordSpec`, `WordMachine.execute`, `snapshot`, `journal`; `verify_transition`, `verify_journal` | Raw integer plus declared width/sign/overflow/order; each arithmetic/logical operation records state before/after and ordinal steps |
| Register program | `kernel.py::RegisterMachine.run`; `FieldLayout.pack/unpack` | Declared finite register set and straight-line instructions; packed fields have explicit ranges |
| Circuit | `circuits.py::Circuit.evaluate` | Classical gate signals evaluated under the circuit graph, with optional gate trace |
| Trace automaton | `geometry.py::induce_trace_automaton`, `run_trace_automaton`, `minimize_dfa` | Prefix automaton from observed token traces and bounded DFA partition refinement |
| Research ledger | `ledger.py::_reduce`, `Ledger.append`, `checkpoint`, `verify_ledger`, `fork_ledger` | Guarded research-phase reduction; immutable hashed artifacts, event chain, source decoder identity and external head checks |
| Experiment pipeline | `pipeline.py::_build_run`, `_execution_event`, `_admit_record`, `build_run`, `replay_run` | Executes four fixed experiment runners and separately admits their resulting scientific records |
| Guarded relations | `qstrings.py::QSystem.add`, `observe`, `resolve`, `export`; `_guard`, `_evaluate`, `_cycles` | Classical hypotheses with three-valued guards, immutable observations, explicit dependencies and bounded fixed-point iteration |
| Intake | `ingest.py::ingest_file`, `reconstruct_input`, `project_input` | Content-addressed chunk checkpoint and resumable source-bound ingestion |

The implemented PHANTOM research path is:

```text
REGISTER_INPUT → INTERPRET → PROJECT → PROPOSE_STRUCTURE → DERIVE_OPERATOR
→ EXECUTE → CHECK → CONTRAST → CHALLENGE → ACCEPT
→ REGISTER_GENERATOR → TRANSFER → REPLAY → NEXT
```

`CHALLENGE` can instead lead to `REJECT` or `UNKNOWN`, then to `REPLAY`; `NEXT` can register another input. Explicit `FAILED`, `CANCELLED`, and `PAUSED` paths are admitted. Acceptance requires scoped status and artifact witnesses; generator registration requires an accepted claim and an actual generator identity. It is not enough to append an English claim. [Source: `division8/ledger.py::RESEARCH_PATH`, `_NEXT`, `_reduce`, `Ledger.append`.]

The **472-event admission ledger** records retrospective bookkeeping of completed scientific claims. The **56-event execution ledger** records actual experiment-runner envelopes. Neither fabricates a chronological trace of an agent’s unobserved reasoning. Arithmetic instruction journals, synthesis candidate traces and media changes are separate, lower-level evidence. `replay_run` verifies both ledgers, their pinned execution plan and source revision, reconciles the scientific report, and can regenerate deterministic outputs. `--hashes-only` omits recomputation and therefore cannot replace a cold replay. [Sources: `division8/pipeline.py::_admit_record`, `_execution_event`, `_bound_execution_plan`, `_reconcile_report`, `replay_run`.]

The commissioned V3 path is `SCOPE → ACQUIRE → HASH → DECODE → MAP → COMPOSE → SIMULATE → PERTURB → DISCOVER → CHALLENGE → VERIFY → GENERATE → REFLECT → ARCHIVE → SELECT`. A label mapping between it and PHANTOM’s path has not established executable equivalence. The new Surface commission harness must retain its own schema and traces, and explicitly connect any invoked PHANTOM operation to its original evidence. [V3 constitution §21; consolidation assessment.]

`QSystem.resolve` selects a candidate only when exactly one guard is true and every alternative is false. Unknown evidence remains unknown, several true guards remain ambiguous, and an ungrounded dependency cycle cannot certify itself. Parentage is a DAG of previously admitted relations; guard dependencies are a separate graph that may be cyclic. Q-Strings are **classical relational objects**, not quantum superpositions. [Source: `division8/qstrings.py`; `runs/release/discovery/qstrings.json`.]

## 6. Remaining PHANTOM source inventory

| Module | Concrete implemented functions/objects |
|---|---|
| `contracts.py` | `canonical`, `digest`, `file_hash`, `integer`, `inside`, `write_json`, `inventory`, `verify_inventory`, `validate_operator`, `substrate_spec` |
| `kernel.py` | `ripple_add`, `ripple_sub`, `growing_successor`, word-operation semantics, independent transition/journal checks, fields and register execution |
| `geometry.py` | `gray_encode/decode`, `successor_distribution`, `transition_graph`, `graph_invariants`, `gf2_rank`, `cubical_homology`, `closure_monoid`, `algebra_catalogue`, trace-DFA induction/minimization |
| `structures.py` | `BinaryTrie`, `PatriciaTrie`, `PackedBitVector`, `RRRBitVector`, `WaveletTree`, `HuffmanCodec`, `ROBDD`, `compile_huffman_generator` |
| `transfer.py` | `apply_local_update`, `inverse_local_update`, `transport_local`, `induce_local_update`, `induce_context_rule`, `predict_context`, `turkish_features`, restricted polynomial parse/evaluate/simplify/differentiate, `matmul`, `matrix_entry_update`, `dft`, `fft`, integer Haar, `stft/istft` |
| `media.py` | `encode_png/decode_png`, `image_roi`, YCoCg integer lifting, image flip/convolution/alpha composite, `encode_wav/decode_wav`, `audio_window`, `gain_pcm`, `resample_hold`, raw-frame `video_roi`, molecule validation/relabeling |
| `experiment_kernel.py` | `run_experiments`: finite arithmetic, histories, circuits, algebra and trace witnesses |
| `experiment_structures.py` | `_navigation`, `_rrr`, `_huffman`, `_bdd`, `run_experiments`: bounded structural comparisons and controls |
| `experiment_transfer.py` | `run_experiments`, `_compile_standalone`: induced local/contextual rules, typed transfers, negative controls, known numerical transforms and retained executables |
| `experiment_discovery.py` | `run_experiments`, `_compiled_check`: word synthesis, support adapters, factory emissions, reflection and Q-String witnesses |
| `__main__.py` | Actual CLI: `describe`, `run`, `verify`, `ingest`, `project`, `discover`, `compile`, `generate`, `validate`, `observe`, `transfer`, `trace`, `checkpoint`, `fork`, `compare`, `diff`, `explain`, `export`, `replay` |

The inventory does not imply all codecs or all scientific formats. PNG is a bounded noninterlaced 8-bit L/RGB/RGBA subset; WAV is bounded PCM16; video operations address raw frames; molecular graph validity does not establish a physically possible reaction. Word graphs, navigation graphs and image pixel neighborhoods have different edge semantics. The source audit JSON includes all top-level symbols and class methods, including internal helpers, so this table does not hide the exact callable inventory. [Sources: the named modules; `docs/FINITE_BOUNDS.md`, `docs/TRANSFER.md`.]

## 7. QUANTUM ORACLE v0.1 implementation

`ORACLE:quantum_oracle/core.py` is 6,875 bytes and supplies a bounded NumPy/SciPy reference. Its actual API is the following:

| Symbols | Implemented behavior | Limits and omissions |
|---|---|---|
| `I`, `X`, `Y`, `Z`, `H`, `GATES`; `kron_all`, `local`, `cx`, `rx`, `rz`, `gate` | Matrix instruction construction for I/X/Y/Z/H/S/T/RX/RZ/CX | Qubit zero is the **most significant** tensor/index bit; no RY, CZ, SWAP, reset or typed channel instruction |
| `circuit(n, ops)` | Starts in the all-zero basis state, applies gate matrices, retains per-step probabilities and norm error | 1–9 qubits and norm error threshold `1e-9`; the function does not impose a separate operation-count cap |
| `probabilities`, `shots` | Born probabilities and seeded NumPy sampling | Shot count 0–100,000; finite sample counts are not a physical backend receipt |
| `density`, `purity`, `evolve_closed` | Pure-state outer product, `Tr(rho²)`, and matrix-exponential unitary evolution | These functions are not a general state/channel schema validator |
| `lindblad` | Constructs a finite-dimensional Liouvillian and uses `scipy.linalg.expm` per step | Hilbert dimension at most 4; 0–1,000 steps; supplied fixtures test amplitude damping, not every open-system model |
| `ring_tracking`, `phase_scan` | Cubic kick plus rotation map; controlled tune/kick scans | Uncalibrated mathematical accelerator analogue; at most 100,000 turns and finite parameters |
| `circuit_discovery` | Enumerates gate sequences from a finite alphabet and compares output probabilities to a target | At most 3 qubits and depth 4; success matches a distribution for the fixed all-zero initial state, not full process/state equivalence |
| `Ledger.add/verify/export`; `canonical`, `sha` | In-memory hash-chained experiment outputs with tamper detection | Not PHANTOM’s richer persistent guarded phase machine |
| `experiment` | Bell construction, damping trajectory, 20 ring-scan cases and known target-distribution search | No hardware calls, real collider data, or FITS/WCS ingestion |

The original eight tests cover Bell probabilities, gate unitarity, damping against `exp(-2.1)`, zero-kick ring norm, finite circuit discovery, ledger tampering, the qubit cap, and shot totals. They are **not** the eight historical GNU Octave comparisons, which remain unverified. No installed independent QuTiP/Aer/PennyLane comparison is implied by the README’s list of candidate libraries. [Sources: `ORACLE:tests/test_engine.py`, `README.md`, `docs/ACCEPTANCE.md`; existing foundation receipt.]

To run a fresh output, from `build/foundation/quantum_oracle/`:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B -m quantum_oracle run --out /tmp/surface-oracle-reference
python3 -B -m quantum_oracle verify --out /tmp/surface-oracle-reference
```

`verify` checks the resulting ledger’s hash chain. It does not independently solve the underlying physics. The Bell-distribution search reported 20 candidates in the preserved fixture, but matching `[0.5,0,0,0.5]` alone cannot distinguish the relative phases of Bell states. [Source: `ORACLE:quantum_oracle/__main__.py`, `core.py::circuit_discovery`.]

## 8. V3 N-atlas seed implementation and counterexamples

`V3:atlas_quantum/core.py` is 4,182 bytes. Its only atlas objects are `Chart(id, origin, unit, operation, phase, scale)` and `Atlas`. There is no compiler, discovery runner, dataset adapter or visual scene in this seed.

| Symbol | What it actually does |
|---|---|
| `Atlas.__init__` | Rejects an empty chart list or duplicate chart IDs, stores a dictionary |
| `Atlas.distance` | Calls `math.dist` on stored origins after exact unit-string equality |
| `Atlas.wave` | Evaluates sine, its x derivative, a scaled sine square, or an identical sine-expression branch named `fourier_sine` |
| `Atlas.edge`, `edges` | Emits every unordered chart pair with origin distance and an operation-name string; no overlap, coupling or validated transition map |
| `source_binary`, `reconstruct` | Encodes opaque bytes as hex plus length/hash and reconstructs with integrity checking |
| `basis_lift` | Maps a finite integer word to its computational-basis amplitude array, width 1–16 |
| `hadamard` | Applies an ideal H to one index bit; qubit zero is the **least significant** bit |
| `complex_pairs`, `decode_pairs` | Serializes little-endian binary64 real/imaginary pairs and reconstructs them |
| `measure_distribution`, `density` | Elementwise magnitude-square and pure-state outer product |
| `quantum_distance`, `compare` | Normalized pure-state Fubini–Study comparison and probability of the selected basis outcome |

The original nine passing tests cover a 3–4–5 origin distance, a cosine derivative, all 256 opaque byte values, payload tampering, a basis-state encoding round trip, H probabilities, `compare`, global phase, and density trace. The constitution’s broader acceptance E is **not closed**. Fresh probes against unchanged code found:

| Probe | Observed result | Missing admission requirement |
|---|---|---|
| `complex_pairs([1,0,0])` then `decode_pairs(record)` | Encoder accepts three amplitudes and declares two qubits; decoder raises `ValueError: bad basis length` | Reject non-power-of-two dimensions before encoding |
| Change `record['basis_order']` without changing raw bytes | Decoder still succeeds | Validate and bind interpretation metadata |
| Use origins `(0,0,0)` and `(3,4,0)` | XY-labeled seed accepts three coordinates and returns 5 | Separate and validate chart/ambient dimensions |
| Use `float('nan')` in an origin | Atlas construction succeeds and distance is NaN | Finite-coordinate guard before metric admission |
| `measure_distribution([2,0])` | Returns `[4,0]`, total 4 | Input normalization contract |
| Sine and `energy` charts both use `scale=2` at `x=pi/2` | Sine square is 4, `energy` branch returns 2 | Declare observable scales and an actual physical energy law |

Every probe, its code and result is retained in [`v3-consolidation-audit.json`](../evidence/v3-consolidation-audit.json). These observations preserve the original seed’s status as a fixture, rather than silently correcting its code. The existing native `serializeState`/`deserializeState` already require a valid 1–6-qubit power-of-two dimension, finite normalized amplitudes, and a record hash that binds basis order. Those stricter native checks do not retroactively make the original Python seed satisfy its full constitution. [Source: `V3:atlas_quantum/core.py`; native `include/surface/phantom.hpp`, `src/phantom.cpp`; [PHANTOM bridge documentation](PHANTOM.md).]

## 9. Missing dependencies and handoff boundaries

The compact PHANTOM handoff includes `DATA_INDEX.json` identities for the **13 original Language Lab archive volumes**, not the complete data themselves. The broader research-evidence archive and recovered Pillar package are separate dependencies. A truncated original Pillar ZIP remains preserved as an original; recovery of a tree is not byte equivalence to that damaged ZIP. Fresh full-corpus recomputation cannot be claimed from the compact fixture replay. [Source: `PHANTOM:REPLAY_HANDOFF.md`, `DATA_INDEX.json`.]

V2 is a commission package, not an implementation of all G0–G7. V3 adds a numerical seed and 24 further provisions. Unclosed work includes independent quantum backends and open-system comparisons, full real FITS/WCS/calibration analysis, real ROOT/HepMC event analysis, topology/calibration-aware quantum compilation, full atlas dynamics and composition, independent held-out discovery transfer, and integrated cold replay. The existing astronomical point catalogue has its own valid scope in [ATLAS.md](ATLAS.md); it is not the N-chart function atlas. No statement here establishes universal classical/quantum equivalence or execution on physical quantum hardware. Android 0.1.1 actual-device launch remains unverified. [Full gate assessment](QUANTUM_V3_CONSOLIDATION.md), [mathematical contracts](MATHEMATICAL_ATLAS.md).
