# Substrate University source continuity in Surface

Surface now preserves the latest identified Substrate University branch's
complete six-division, 62-topic registry and a dependency-closed set of four
pure mathematical modules. A fixed headless example actually executes those
modules. The browser campus itself has not been ported into Surface's C++
renderer or Android package.

## Pinned implementation and product boundaries

The source is
[akadaan310/abedkadaancom at 6a0f5eaa](https://github.com/akadaan310/abedkadaancom/tree/6a0f5eaa8dd39b58bdd99889721ecea5f54e62bb),
branch `claude/new-session-xd8auu`, full commit
`6a0f5eaa8dd39b58bdd99889721ecea5f54e62bb`. This is the latest identified
implementation inspected for this task, not a claim about a subsequently
changing branch or the current live website. The head commit is dated
2026-10-21 and updates Vitest to 4.1.12. No site deployment was changed or
verified by this import.

The preserved [agent rules](../vendor/polyia/substrate-university/AGENTS.md),
[README](../vendor/polyia/substrate-university/README.md) and
[rebuild record](../vendor/polyia/substrate-university/docs/UNIVERSITY_REBUILD.md)
describe a client-only Vite, React, TypeScript and Three.js university.
Earlier Next.js/server code belongs to its history. Its mathematics lives in
pure `src/math/` modules, distinct from rendering, storage and interface code.
The original site implements a Gothic-futurist campus, a gate exercise,
division exhibits, library, observatory, Scriptorium and six-station One-Day
Harness. The latter produces personal books with participant, sourced,
computed and generated contributions distinguished. Those browser interfaces,
PDF exports, optional cloud facility and deployment configuration are outside
this import.

The university is not an accredited degree-granting institution. Its residents
are fictional, specimen volumes are previews, and subjects carry explicit
epistemic labels. Its public content excludes religious, scriptural and
Arabic-language subjects and cross-session AI identity/continuity research.
These are the original University's content boundaries. PolyIA's broader
archival source documents remain in their separate source namespace; their
presence does not add subjects to the University registry.

## What is copied exactly

All imported files are under `vendor/polyia/substrate-university/`. Every file
retains its original path and bytes; its Git blob and SHA-256 are recorded in
the shared [import manifest](../vendor/polyia/IMPORT_MANIFEST.json).

| Source | Interface and actual role | Dependency closure |
|---|---|---|
| `src/math/rational.ts` | `Q` and rational/integer helpers; BigInt arithmetic | No project imports |
| `src/math/matrix.ts` | Exact matrices, RREF, rank, image/kernel bases and preimage classification | `rational.ts` |
| `src/math/addressCompiler.ts` | `tokenize`, `compile`, `opMatrix`; finite `loom://` protocol compiled to a 3×3 rational matrix | `rational.ts`, `matrix.ts` |
| `src/math/world.ts` | Elementary cellular automata, finite dependency ordering/reachability, declared deterministic PRNG | No project imports |
| `src/content/types.ts`, `sources.ts`, `registry.ts` and six `topics/*.ts` files | Original topic IDs, divisions, prerequisites, definitions, examples, challenges, sources and epistemic labels | Nine-file content closure |

The original `tests/math.test.ts` and `tests/registry.test.ts` are preserved as
reference, along with `package.json`. Those tests cover the larger upstream
application and import modules outside the selected closure. They are not
advertised as runnable in this partial copy and were not counted as passed.
The Surface integration tests and fixed headless example instead exercise the
selected production source directly.

The selected runtime modules import no React, Three.js, browser storage,
networking or model provider. Python's default PolyIA example does not require
Node. The optional TypeScript fixture is a development tool, not a new runtime
dependency of Surface's native executable.

## Preserved topic identities

Fresh execution of the actual registry produced:

| Division | Original identity | Topic count |
|---|---|---:|
| I | `foundations` — Foundations of Computation | 10 |
| II | `relational` — Relational and Generative Mathematics | 10 |
| III | `languages` — Programmable Computational Languages | 10 |
| IV | `geometry` — Geometry, Physics, and Representation | 12 |
| V | `acoustic` — Acoustic and Generative Sciences | 10 |
| VI | `worlds` — Computational Worlds and Emergence | 10 |
| **Total** | **Six original divisions** | **62** |

All 62 IDs are unique. The current topic-level labels are **42 established**,
**18 house** and **2 application**. The schema additionally permits conjecture
and mythology. A topic's label is not automatically a verdict for every
sentence or every implemented computation within it; definitions retain their
own labels and sources. Registry preservation records curricular identity and
content, not executable mastery of every topic.

PolyIA's **Infinity IX** and **VII/VIII open research charters** belong to its
separate adopted research organization. They do not silently renumber or extend
this original six-division registry. Surface can later cross-reference these
identities while keeping their source namespaces explicit.

## Run the real headless example

```sh
node --no-warnings vendor/polyia/university_demo.mjs
python3 -I -B tools/polyia_surface_demo.py --with-university
```

Node 24 or later is required for this example; the fresh run used **v24.22.1**.
The driver first checks the pinned import-manifest digest and every University
source's bytes, then loads the exact TypeScript files with Node's native type
stripping. A scoped resolver adds `.ts` to relative imports from the preserved
source tree. No captured file is rewritten, no package is installed, and no
browser or server is started. Native type stripping does not perform static
typechecking.

The fixture compiles this address:

```text
loom://plate/START/ROTATE:90/SCALE:2/SHIFT:1,0/COMMIT
```

Its exact homogeneous matrix is:

\[
\begin{bmatrix}
0 & -2 & 1\\
2 & 0 & 0\\
0 & 0 & 1
\end{bmatrix}.
\]

Later operations multiply on the left, so the sequence rotates by a quarter
turn, scales by two, then shifts by `(1,0)`. Matrix entries remain exact
rationals. The original `applyHomogeneous` function converts entries to
floating point for coordinates; that separate projection is not needed for
the fixture's exact comparison. `loom://` is the source's teaching scheme, not
a new PURL/SEURL identity or a network address to visit.

The example also verifies refusal of `ROTATE:45` and a missing `COMMIT`, checks
Rule 90 with periodic boundaries on nine cells for four rows, and compares
literal expected rows:

```text
000010000
000101000
001000100
010101010
```

For matrix `[[1,2],[2,4]]`, it checks an empty preimage for `[1,1]` and an affine
preimage for `[3,6]`. A two-node directed cycle returns no topological order.
This is finite graph dependency ordering, not causal inference from observed
data. The receipt includes all 62 topic IDs with their divisions and labels.

## Known source defects and guarded scope

Read-only local inspection and execution reproduced limitations that matter
before exposing arbitrary user inputs:

| Source behavior | Observed result | Surface treatment |
|---|---|---|
| Original `fold.ts` chooses generated Greek glyphs without excluding original glyphs | Folding/unfolding `ΑΑ` creates a self-reference and ends in `RangeError` | Module omitted from the imported executable subset; no general folding claim |
| Loom `SCALE:2,3,4`, `SHIFT:1,2,3` and `START:anything` | Original compiler accepts surplus/ignored arguments | Only a fixed valid fixture is exposed; a future public adapter needs strict operand counts and bounded input |
| `weave(90,9,0)` | Returns one row because the initial row is always emitted | Fixed positive dimensions in the example; any public wrapper needs integer/dimension/output-cell limits |
| Matrix and rational convenience helpers | Assume rectangular matrices, matching vector sizes and valid scalar input; number-to-BigInt conversion inherits prior number precision | Use the fixed, validated exact fixtures here; require explicit boundary validation for new inputs |
| BORNE graph helpers | Assume declared graph nodes and edges | Demonstrate valid finite graphs and a cycle negative control; no arbitrary graph admission claim |

These findings are not silently patched inside the preserved source. A later
correction should be a separately versioned adapter or upstream-reviewed
change with regression tests and updated source identity. The selected modules
are reusable mathematical implementations, not complete hostile-input
sandboxes.

## Verification, rights and remaining integration

The new Surface test runs the actual TypeScript fixture and checks its exact
matrix, rows, negative controls, preimage classifications and registry counts.
It is one of six passing Python integration tests. The combined demo and
recorded [import evidence](../evidence/polyia-import.json) preserve the outcome.
No upstream Vitest suite, `npm run typecheck`, Vite build or Playwright test was
run in this import. Physical Android/device performance, WebGL behavior, PDF
export and optional cloud synchronization remain outside the measured scope.
Historical claims in `UNIVERSITY_REBUILD.md` retain their historical status.

No repository-wide software license was found at the pinned commit. The font
license files in the original repository govern their respective assets, not
the TypeScript source. The copied code is recorded as license unspecified,
with the original Abed Kadaan/7u attribution retained; see
[LICENSE_STATUS.md](../vendor/polyia/LICENSE_STATUS.md).

The practical next native integration would preserve this source identity and
port a clearly defined operation—such as exact finite transformation commands
or dependency ordering—into a tested C++ boundary, then compare it with the
retained reference on declared inputs. The current import supplies that
reference and all topic identities. It does not claim the campus, six-book
harness, full university or general discovery system is implemented in Surface.
