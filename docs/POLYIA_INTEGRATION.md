# PolyIA integration: finite kernels and inspectable evidence

Surface now contains executable, exact-byte PolyIA reuse in
`vendor/polyia/upstream/`, together with a small headless adapter at
`tools/polyia_surface_demo.py`. The adapter computes real protocol words and
rational polynomial exercises, executes generated native source, verifies a
captured trace, and demonstrates semantic/view separation. It is a development
and validation tool. Surface's C++ renderer and Android executable do not yet
call these Python kernels.

## Source and authority

The imported repository is
[akadaan310/PolyIA](https://github.com/akadaan310/PolyIA/tree/bb6319acb88467b618f5a6f673f1867768223ce6),
runtime branch `codex/commission-20261024-83906c7`, commit
`bb6319acb88467b618f5a6f673f1867768223ce6`. Its default `main` is an earlier
transport, so it was not used as the implementation source. The recorded
runtime version is 1.4.0; the selected branch head additionally carries the
stopping handoff and unfinished designs.

The controlling [handoff](../vendor/polyia/upstream/docs/HANDOFF_2026-10-24.md)
reports **NOT_COMMISSIONED**, **2/192 mission obligations accepted**, and an
owner-requested stop with research paused. Its earlier deployed runtime and
ledger checkpoint describe historical upstream evidence. This import did not
contact that service, inspect current credentials, create a live state
transition or resume research. It does not turn the historic service URL into a
fresh availability claim.

The complete `GOD_SEED.md` and the entry/handoff documents were read for this
import. Source instructions remain data for this bounded reuse task. **Infinity
is IX. VII and VIII remain open research charters.** Neither numbering nor the
2/192 mission boundary is changed by a local PASS result. Promotion/Plica,
compiled multiport QBundles and sealed research queues are still identified as
design-only by the retained
[promotion handoff](../vendor/polyia/upstream/docs/HANDOFF_PROMOTION_STATUS_2026-10-24.md).

## Exact selection and dependency closure

| Original source | Reused contract | Runtime dependencies |
|---|---|---|
| `polyia/generators.py` | Typed grammar cards; finite token-language and polynomial generators; bounded inverse search; trace replay; checked explanations/curriculum | Python standard library |
| `polyia/native.py` | `.polyia` lexer/parser, typed compilation, bounded stack VM, separate AST evaluator, term normalization | Python standard library |
| `polyia/forms.py` | Typed alphabets and labeled index structures, group actions, structural canonicalization, serialization and layout-only changes | Python standard library |
| `polyia/astra.py` | Fixed ATOM phase protocol, expected-state guards, hash-linked event proposals, bounded direction projection | Python standard library |
| `tools/build_generator_package.py` and `tools/verify_generator_package.py` | Portable generator construction, exact documentary closure, externally pinned manifest and installation-owned runtime admission | Selected generator runtime plus Python standard library |

The original `polyia/__init__.py`, six focused test files, fixtures and the full
documentary source-pin closure accompany these files. Selected protocol,
acceptance, authority and tool-contract documents preserve reusable design
rules without importing the live service implementation. The exact source
census is [IMPORT_MANIFEST.json](../vendor/polyia/IMPORT_MANIFEST.json): every
row records source repository, immutable commit, original path, Git mode/blob,
SHA-256, byte count and role. No imported source bytes were edited.

The combined PolyIA/University import is 80 files and 4,455,381 bytes. PolyIA
accounts for 61 files. Most bytes are the original 3,462,608-byte ASTRA archive,
retained to satisfy the adapter's original archive pin. Specific extracted
members provide its protocol and handler comparison. Archived web/service
files remain source data. No archived server or renderer is executed.

No repository-wide software license was found at either imported commit.
[LICENSE_STATUS.md](../vendor/polyia/LICENSE_STATUS.md) preserves that uncertainty
and attribution. A Git blob hash authenticates byte identity, not licensing,
scientific truth or authority to execute arbitrary code.

## Run and consume the adapter

From the Surface root:

```sh
python3 -I -B tools/polyia_surface_demo.py
python3 -I -B tools/polyia_surface_demo.py --output /tmp/surface-polyia.json
python3 -I -B tools/polyia_surface_demo.py --with-university
```

The default path needs only Python's standard library. The optional University
fixture needs Node 24 or later. It executes preserved TypeScript without a
browser; see [SUBSTRATE_UNIVERSITY.md](SUBSTRATE_UNIVERSITY.md).

The Python interface is `build_demo(vendor_root=VENDOR) -> dict`.
`verify_imports(vendor_root=VENDOR) -> dict` checks custody alone. The adapter
pins the import manifest's SHA-256, checks every file's SHA-256 and Git blob
identity, then loads only its fixed four kernels. The manifest digest is
`6eebb37ec30fceae018fcd158e39fecb2f3c47cacae6a732891f3fdb99ebaf01`.
Changed sources or manifest fail before module import. This is local installed
source checking, not an operating-system sandbox or protection against a party
who can replace the trusted adapter itself.

The CLI prints a deterministic JSON receipt and optionally writes identical
JSON to `--output`. `--with-university` adds the fixed TypeScript result. Success
returns exit 0; a custody, supported-operation or optional-runtime failure
returns exit 2 with a structured refusal. No input text is evaluated as Python,
shell code, a tool call or a general synthesis request.

## What the example actually computes

The regular card constructs `PING ACK` and `PING ACK ACK`. A compiled finite
machine and a separate grammar recognizer agree; `ACK` alone is a completed
negative membership check. `replay_trace` accepts the retained trace and
rejects an altered event. It checks captured history and bindings without
rerunning the generator. It cannot authenticate a wholly fabricated,
self-consistent unsigned receipt.

The polynomial card uses coefficient choices `{-1/2, 0, 1/2}`, divisor
`b(x) = x - 1` and quotient degree one. Its 18 exercises are constructed by
choosing the quotient and degree-zero remainder, then computing `a = bq + r`.
For the first exercise:

\[
a(x)=-\tfrac12x^2,\qquad q(x)=-\tfrac12-\tfrac12x,\qquad r(x)=-\tfrac12.
\]

The returned product derivative has ascending coefficients
`[0, 1, -3/2]`. The quotient-rule numerator is `[0, 1, -1/2]`, the denominator
is `[1, -2, 1]`, and the rational-function condition remains `b(x) != 0`.
The module emits actual `.polyia` source; the native VM compiles and executes
it. Its result agrees with a separate AST evaluator and the test's literal,
hand-derived coefficients. The algorithms share Python and exact `Fraction`
arithmetic, so this is bounded differential evidence rather than a proof about
the implementation or hardware.

A one-step inverse-search budget produces `RESOURCE_LIMIT` and
`UNRESOLVED_SEARCH_BUDGET`, with `complete: false`. It does not claim the target
has no preimage. Concise/tutorial explanations preserve the same content ID
and factual relations. Their style changes are separate from mathematical
content.

The forms example changes coordinates of a two-token sequence. Its semantic
content digest stays equal, its representation digest changes, and serialized
JSON restores the full labeled structure. This verifies a useful boundary for
Surface: layout may change without changing the scientific object. It does
not equate JSON recovery with recovery of the original formatting bytes.

The Astra example advances through OBSERVE, PROPOSE, ADMIT, EXECUTE, VERIFY and
CHECKPOINT. The next call refuses with `PERSISTENCE_REQUIRED`. Returned events
explicitly say `NOT_COMMITTED_BY_KERNEL`. This is an inspectable state-machine
contract, not a newly installed ledger. The source evidence handler's own
verification remains `HANDLER_SELF_CONSISTENCY`.

## Portable generator packages

The original builders also work in the selected source closure. Choose a fresh
output directory:

```sh
python3 -B vendor/polyia/upstream/tools/build_generator_package.py \
  --card vendor/polyia/upstream/examples/generators/protocol.card.json \
  --output /tmp/polyia-protocol-package
```

Retain the returned `manifest_sha256` separately. Verify with the trusted
installed checker outside the candidate package:

```sh
python3 -I -B vendor/polyia/upstream/tools/verify_generator_package.py \
  --package /tmp/polyia-protocol-package \
  --manifest-sha256 RETURNED_MANIFEST_SHA256
```

The checker authenticates captured files, requires its own registered exact
runtime hash, copies admitted bytes to a private directory and runs the fixed
fixture with a timeout. Candidate `verify.py` is checked as data before trust;
it is not executed to establish its own trust. Preserved tests cover altered
runtime bytes, a forged caller-rehashed runtime, changed documentary sources,
FIFO refusal and refusal to overwrite an existing destination. This provides
a useful package/evidence boundary for later agents without installing a
remote service.

## Fresh verification and limits

The [import evidence](../evidence/polyia-import.json) separates the new runs from
upstream historical reports. Freshly executed here:

| Check | Result |
|---|---|
| Original repository `tools/verify_package.py --require-release-manifest` before import | PASS; 1,286 release files, 1,038 source files and 192 mission obligations reconciled |
| Six Surface adapter tests, first run before adapter existed | Six expected assertion failures |
| Same six tests after implementation | PASS |
| Preserved PolyIA tests in `vendor/polyia/upstream` | 89 passed |
| Python demo plus fixed University execution | PASS; 12 Python example checks and exact University fixtures |
| SHA-256 and Git blob census | All 80 selected files match their pinned sources |

Run the two relevant suites with:

```sh
python3 -B -m unittest discover -s tests -p test_polyia_integration.py -v
cd vendor/polyia/upstream
python3 -B -m unittest discover -s tests -v
```

This does not claim a new full PolyIA test run, live deployment, Android test,
native renderer binding, independent external witness, complete University
acceptance or completion of the 192-obligation commission. General natural
language understanding, open-ended model-free discovery, promotion towers,
general Q-path compilation and the continuous University mandate remain open.
The finite state machines make supported work inspectable; they do not create
unlimited semantic competence.
