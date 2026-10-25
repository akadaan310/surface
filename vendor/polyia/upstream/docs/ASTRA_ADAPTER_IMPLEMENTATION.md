# Astra adapter kernel, version POLYIA-ASTRA/0.1

`polyia.astra.run_adapter(parameters: dict) -> dict` implements a finite, pure
adapter for the retained ASTRA Universal Traversals/Celestial Shells 0.2 and
ATOM 0.1. It ports the actual geometry functions and the actual bounded
`evidence` handler. It creates no files, opens no connections, invokes no models
or subprocesses, and commits no state. The caller must integrate returned
state/events with Poly IA's authenticated, durable command boundary.

This increment contributes executable behavior for PIA-157–160 and PIA-162.
It does **not** accept those complete obligations or claim PIA-161/163–168,
full adapter deployment, external checkpoint recovery, or full commissioning.
The mission remains `NOT_COMMISSIONED`.

## Inherited contracts and exact source identity

The implementation was grounded in `AGENTS.md`, `START_HERE.md`,
`CODEX_START.md`, GOD_SEED's PIA-157–168, and the complete
`docs/ASTRA_INTEGRATION.md`. The following original contracts and code were read
in full, along with the original Python ATOM and Node sky tests. They are retained
unchanged under
`sources/expanded/ASTRA_CELESTIAL_SHELLS_ATOM_CODEX_GOD_SEED_V02/ASTRA_CELESTIAL_SHELLS_V02/`.

| Original member | Binding anchors | SHA-256 |
|---|---|---|
| `docs/FORMAL_CONSTITUTION.md` | Definition of a transition atom; Immutability and versioning; Limits and safety | `f9a5aaa75812d0c887b8e4aa75adb677903885f293e329127afecabaf78e670e` |
| `docs/SCIENTIFIC_AND_AUDIO_CONTRACT.md` | Provenance; Geometry; Tests and blockers | `c539c84b53acb24122f882ac58678ba3f10654d2100893f64b7a870204f7c5bc` |
| `handoff/ATOM_AGENT_PROTOCOL.json` | `phase_order`, `required_report_fields`, `rules` | `2d266d815c268dcd5d12a15b2866b80b88fa5500559111ba62a6e3aaaf0a5794` |
| `atom/core.py` | `Universe.advance`, `_check`, `_evaluate`, `_verify_output`, `report` | `243e27d8c6a7448dfe626d764b140b0b756db265fe0dcaf8428a91487c808ad7` |
| `web/sky.js` | `vec`, `rotate`, `project` | `fb363a05365eaaabb3e1efabe6054c0a1c579422fff1df9b44927b572f46db57` |

The preserved archive
`sources/recovered/ASTRA_CELESTIAL_SHELLS_ATOM_CODEX_GOD_SEED_V02.zip` has SHA-256
`09f631d03503dd7b7b0f44010f6d9f4a9af5c37fab28d79e57c3bba5cb3380ed`.
Every result exposes these paths, anchors and digests through `identity.sources`.
These are pinned references; the pure runtime does not read or verify source
files. The tests independently rehash the six referenced files. Release custody
must continue to verify the actual deployed bytes separately.

## Request and result contracts

All requests require exactly these version fields and a registered operation:

```json
{
  "adapter_version": "POLYIA-ASTRA/0.1",
  "source_version": "ASTRA/0.2",
  "protocol": "ATOM-HANDOFF/0.1",
  "operation": "atom.initialize"
}
```

The registered operations are:

| Operation | Additional required fields | Result |
|---|---|---|
| `atom.initialize` | None | Initial adapter domain state at OBSERVE, tick 0, plus report |
| `atom.report` | `state` | Pure reconstruction and report; no advancement |
| `atom.advance` | `state`, `expected_state_digest`, `input` | Exactly one phase transition or a refusal |
| `geometry.project` | `input` | Semantic objects, distinct projection and view state |

Every response includes `ok`, `status` (`PASS` or `REFUSED`), `checks`,
`limitations`, pinned `identity`, `adapter_version`, `effect_class: pure`, and
`llm_required: false`. A refusal has an `error` with a stable `code` and diagnostic
`message`. When a supplied atom state passed validation before the refusal, the
unchanged state and report accompany the refusal. Invalid states are not echoed
as trustworthy reports. Unknown fields and operations refuse; executable-looking
strings have no executable meaning.

Resource validation precedes copying or hashing: JSON depth <=16, <=20,000 nodes,
<=1,024 fields/items per object/array, <=32,768 characters per string,
<=262,144 total UTF-8 string bytes and <=256-bit integers. Unpaired surrogates,
NaN and infinities refuse. No external clock, random generator, network, file
system, model client or hidden process participates in the result.

## The finite ATOM operation

The historical tuple remains `a=(I,O,Q,delta,g,e,w,c)`. For this adapter:

| Element | Implemented meaning |
|---|---|
| I | JSON parameters for the source `evidence` operation; `artifact` <=120 characters, `content` <=10,000 characters |
| O | `{artifact, sha256, source: "caller-provided"}` |
| Q | Versioned adapter state, phase, tick, active atom, pending work and bounded full event history |
| delta | One source-compatible phase transition per `atom.advance`; output is stored in `pending.output` and returned in the successor state |
| g | Strict envelope/state/history validation, expected-digest check, ADMIT evidence schema and string bounds |
| e | Pure local computation and returned event candidate; no durable write |
| w | Explicit same-handler reconstruction; SHA-256 is integrity evidence, not identity, truth, or a signature |
| c | At most five retained transitions, bounded JSON and content; O(content bytes) hashing; no batch or headless driver |

The adapter initializes a single predefined `evidence` atom, selected at OBSERVE.
Its tick names adapter-domain progress; it is neither the original Universe's
registration/event tick nor Poly IA's commission revision. This is a new typed
adapter state schema, not an import of arbitrary historical Universe state.

Advance from OBSERVE with `input: {"artifact":"known-vector","content":"abc"}`.
Later advances require `input: {}`. Source defaults are retained when omitted:
`artifact="fixture"`, `content="prototype evidence"`.
The path is `OBSERVE -> PROPOSE -> ADMIT -> EXECUTE -> VERIFY -> CHECKPOINT`.
PROPOSE preserves the source fixed payoff-table outcome: VERIFY, worst-case
utility 4, nominal utility 4. This is the supplied illustrative deterministic
maximin policy, not a general policy optimizer.

As in the source, semantic parameter admission happens at ADMIT. A malformed
but bounded JSON parameter proposal can reach ADMIT and is then refused without
phase advancement. Content is UTF-8 encoded and hashed at EXECUTE. VERIFY
recomputes the same declared handler and records
`evidence_class: HANDLER_SELF_CONSISTENCY`, `independent: false`.

The next phase, CHECKPOINT, denotes pending checkpoint work. Any attempt to
advance there returns `PERSISTENCE_REQUIRED`, leaves the phase/tick unchanged,
and retains `checkpoint_head: null`. The protocol forbids a completed checkpoint
claim without saved source objects and state that actually resolve and verify.
Consequently HOLD and resume are explicitly unavailable here, as are
branch/merge, cross-database atomicity and external state import.

Each event includes its full selected input, tick, verb, before/after phase,
previous event hash and own hash. State validation reconstructs the entire
bounded history and compares every event and field, rejecting phase skips,
changed output and tampered events. State digests use the inherited canonical
JSON convention: sorted keys, compact separators, UTF-8, `ensure_ascii=False`,
`allow_nan=False`, then SHA-256. Float representations are Python JSON's;
this is not a claim of language-independent RFC canonicalization.

`expected_state_digest` detects a mismatch with the supplied state. A pure
function cannot know which state is globally current or authenticate a
caller-created self-consistent history. The eventual durable integration must
load its authoritative state, enforce the authenticated Poly IA revision and
idempotency guards, and atomically retain the request/refusal or admitted event.
Returned `event_persistence: NOT_COMMITTED_BY_KERNEL` makes that boundary explicit.

The report retains every required handoff field: `protocol`, `state_digest`,
`tick`, `phase`, `active`, `checkpoint_head`, `recent`, `verification`,
`next_action`, `limits`. `recent` references the full source-linked adapter events
in the returned state. `next_action` is a possibility and explicitly grants no
authority.

## Geometry, semantic identity and transient view

Example `geometry.project` input:

```json
{
  "observer": "ICRS-direction-only",
  "points": [{
    "id": "direction-1", "ra_deg": 90, "dec_deg": 0,
    "provenance": {"kind": "synthetic", "source_id": "authored:example"},
    "radius": 1
  }],
  "view": {"width": 800, "height": 500, "distance": 4,
           "yaw_rad": 0, "pitch_rad": 0, "selected": "direction-1"}
}
```

The input accepts <=256 unique identified points, RA in [0,360) degrees,
declination in [-90,90] degrees, display radius in (0,1,000,000], viewport
dimensions in (0,16,384], distance in (0,1,000,000], yaw in [-2pi,2pi] radians,
and pitch in [-pi,pi] radians. Radius defaults to 1. These are explicit adapter
admission bounds; the original JavaScript functions themselves had looser
input validation. Selection is null/absent or identifies a supplied point.

The port preserves the exact source convention:

* Degree-to-radian conversion precedes
  `V=(cos(dec)*sin(ra), sin(dec), cos(dec)*cos(ra))`.
* For radius-scaled `(x,y,z)`, yaw gives
  `a=x*cos(yaw)-z*sin(yaw)`, `b=x*sin(yaw)+z*cos(yaw)`.
  Pitch gives camera coordinates
  `(a, y*cos(pitch)-b*sin(pitch), y*sin(pitch)+b*cos(pitch))`.
* For camera depth z, `distance-z < 0.4` clips to `screen: null` before division.
  Equality is admitted according to ordinary binary64 comparison, matching the
  source; no hidden epsilon changes that boundary.
* `f=min(width,height)*1.43`, `scale=f/(distance-z)`,
  `screen.x=width*0.5+x*scale`, `screen.y=height*0.51-y*scale`.
  The output retains source `depth` and `scale`.

Semantic objects include IDs, celestial coordinates, declared frame and
provenance. Camera state, selection, display radius and projection are separate
objects. Changing the camera or radius leaves `semantic_digest` unchanged and
cannot add a relation. Changing a coordinate or source identity changes the
semantic object. Input and output objects share no mutable aliases.

Provenance kind is `catalog`, `synthetic`, or `illustrative`, with a required
source ID. Labels are retained as
`CALLER_ASSERTED_NOT_CATALOG_VERIFIED`: naming a catalog does not verify catalog
membership, positional accuracy or a matching HIP entry. No caller can upgrade
that label to a proof through this schema. Radius is always identified as an
authored display scale. Unsupported observers, including Mars, refuse instead
of fabricating a transformed viewpoint. This increment imports no full catalog
and adds no nearest-neighbor semantic claims.

## Fresh verification and remaining gates

Work was performed on `codex/commission-20261024` with base checkout
`3d019a4476f07629412c51819cb82579ead01ced` and runtime
`/opt/polyia/runtime/bin/python3`, Python 3.13.17. The preserved source digests
above and final produced-file hashes identify the actual implementation bytes;
the base commit alone does not identify these uncommitted additions.

Observed red: before `polyia/astra.py` existed,
`/opt/polyia/runtime/bin/python3 -B -m unittest discover -s tests -p test_astra.py -v`
ran 14 tests with 19 failures (cardinal subtests included), all showing the
deliberate `NOT_IMPLEMENTED` boundary result. After implementation, the same
command passed all 14. Added adversarial/source-agreement coverage then passed
all 18 adapter tests. A further failing regression exposed Python's ordinary
equality treating `true` as `1` and `4.0` as `4` in supplied state. Replacing
state/event equality with canonical-byte comparison fixed that silent
normalization; all **19 adapter tests** then passed in 0.040s. The expectations
for six cardinal directions, axis signs,
viewport offsets, norms and known SHA-256 `abc` output were written before the
implementation and derived separately from the implementation functions.

The source evidence-handler differential test invokes only the inspected pure
`Universe._evaluate` method, never the disk-writing Universe constructor. It
checks default, empty and Unicode inputs against the actual retained source.
This is source agreement, not independent external verification. A separate
development comparison of 180 geometry cases against actual Node `web/sky.js`
covered 6 RAs, 5 declinations, 3 yaw/pitch pairs and 2 distances. All matched
within `1e-12`; maximum absolute difference was `2.2737367544323206e-13`.
A 165-call malformed JSON/type boundary matrix returned structured results
without exceptions.

The complete project suite was also run with
`/opt/polyia/runtime/bin/python3 -B -m unittest discover -s tests -v`:
154 tests passed in 12.043s at the first discovery snapshot, which included the
initial 14 adapter tests and parallel commissioning additions. Existing
`sqlite3` unclosed-database `ResourceWarning`s appeared in store tests at
`polyia/store.py:127` and `copy.py`; the suite had no failures. These warnings
were not suppressed or repaired by this adapter change.

Later complete-suite runs during parallel HTTP boundary development were red:
167 tests in 14.061s had one `BrokenPipeError` in
`test_server_limits.BoundaryLimitTests.test_auth_and_json_refusals_release_slots_without_mutation`.
The subsequent 168-test run in 13.575s had six subtest failures and one error.
Named failures included that same auth/JSON test receiving 503 rather than 400,
`test_slow_headers_cannot_create_a_second_handler_and_disconnect_releases_slot`
missing `X-Frame-Options`, and
`test_unsafe_numeric_and_boolean_configuration_is_rejected` not yet rejecting
four new numeric bounds (`request_rate=1e-320`, `socket_timeout=1e300`,
`max_active_requests=1025`, `request_burst=1000001`). These concurrent server
changes are outside this adapter's three-file scope and were reported to their
implementer. No whole-project green claim is made for that changing checkout.
The final adapter-only suite passed; `tools/audit_no_llm.py` also passed and
included the new adapter in its static module inventory. Its offline dynamic
checks remain scoped to the audit's registered scientific kernels, so that
audit result is not claimed as a new dynamic Astra network interception test.

Remaining full-integration gates are durable authoritative state binding,
authenticated HTTP admission, source-object persistence, checkpoint recovery,
source mismatch handling at deployment, actual external dispatch/recovery,
and cross-project adapters. Browser pixels, WebGL, audio/device behavior,
physical observer accuracy, full catalog ingestion and semantic bridges have
no new measured evidence from this kernel. Historical packet test claims keep
their historical status. A passed finite kernel test cannot satisfy these
unperformed gates or change mission acceptance.
