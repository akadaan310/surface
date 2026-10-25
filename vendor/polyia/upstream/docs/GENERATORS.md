# Constructive generator increment 0.1

This increment constructs two finite families: token languages compiled into executable finite machines, and exact rational polynomial division exercises with derivative/curriculum content. It does not declare D-GENERATORS, PIA-097–108, or their inherited acceptance complete. No registry or mission status is changed by this module.

## Public operations and immutable identity

`polyia.generators` exports pure functions:

- `compile_model(card) -> {ok, model}` or `{ok: false, error}`. Only the two registered families below are admitted. The model contains typed machine IR, the original card, constraints, source hashes, state-map vocabulary, explicit deterministic policy, dependencies, and a semantic content hash. Entity `id` and `version` are immutable card fields within that content identity. The semantic CID, not the human id/version pair alone, is authoritative; this module is not a global name/version allocation registry.
- `run_model(model, request) -> report`. Every call recompiles the card and compares the entire supplied package before executing. Altered opcodes, constraints, source references, identity or metadata are refused. A report contains `status`, `result`, checks, a hash-linked trace, and explicit limitations. `PASS` means the stated bounded operation/checks completed; it is not mission acceptance.
- `replay_trace(report) -> {ok, ...}` checks the captured chain, result and candidate bindings without executing handlers or reading files. An unsigned self-consistent fabricated receipt is not authenticated by this function. Durable provenance requires the ledger's separately captured code/source/input bundle.
- `render_explanation(content, {style: "concise" | "tutorial"})` independently checks content before rendering. Both styles preserve the same structured relations and source lock. Unsupported style fields or added claims are refused. A view has its own identity and representation trace; it cannot modify the semantic content ID.
- `build_curriculum(content)` returns a source-linked prerequisite graph for polynomial content. `export_native(content)` emits real `.polyia` source for the existing `polyia.native/0.1` VM; the emitted source still must be compiled and executed there.

All public inputs are JSON-shaped discrete values. Unknown fields, operations, families, effects, malformed rationals, nonfinite/floating values, non-scalar Unicode, duplicate transport JSON fields and exhausted bounds are refused. The pure functions do not read files, use the network, invoke subprocesses, dynamically import user code, evaluate Python, or perform LLM/model inference. The explicit CLI reads stdin/writes stdout; the separate packaging tool performs declared file operations.

## Family 1: regular token languages

A `polyia.generator-card/0.1` regular card specifies `id`, semantic `version`, `family: "regular"`, a finite `alphabet`, typed `grammar`, `seed: 0`, and `bounds`. Supported grammar constructors are `empty`, `token`, `sequence`, `choice`, and `repeat` with finite integer minimum/maximum. These are token identities, not historical lexemes or a natural-language comprehension claim.

The compiler builds a Thompson NFA, applies reachable subset construction, and refines the reachable DFA partition. The minimized total DFA is executable data. An exhaustive reachable product traversal checks equivalence between baseline and candidate, covering the entire finite-machine language rather than a sample. A separate recursive source interpreter recognizes words using consumed-position sets and memoization. It shares input validation and the trusted Python runtime, but does not execute DFA transitions.

`{"operation":"generate"}` enumerates token words in breadth-first alphabet order, tests the compiled machine, and independently verifies admitted words from the source grammar. This enumerates canonical words, not all ambiguous grammar derivations; duplicate count may therefore be zero even when the grammar is ambiguous. It constructs previously unlisted words rather than retrieving examples. A candidate records grammar, exact source card, machine path, source lock, and both recognition witnesses.

`{"operation":"recognize","word":["PING","ACK"]}` performs both interpreters, including negative cases. Tokens outside the alphabet are refused. A valid nonmember returns a completed `PASS` report with `accepted: false`; PASS is about the check, not membership.

[protocol.card.json](../examples/generators/protocol.card.json) admits `PING ACK` and `PING ACK ACK`. [minimization.card.json](../examples/generators/minimization.card.json) has two branches with an equivalent suffix, providing an actual state-count reduction. A zero reduction is explicitly not admitted as an improvement. This metric is the number of reachable DFA states. No latency, energy, broad compiler optimality, or total production-cost acceptance is claimed.

## Family 2: exact polynomial constructions

A `polynomial-division` card supplies a nonzero divisor of degree at most four, one to eight distinct exact rational coefficient choices including a nonzero choice, and quotient degree zero through four. Polynomial arrays use ascending powers. Coefficients are integer values or strings such as `"-1/2"`; all computation uses exact `Fraction` arithmetic.

The constructive law chooses a quotient with exactly the declared degree and nonzero leading coefficient, chooses a remainder of degree less than the divisor, then computes `a = b*q + r`. Constant divisors have remainder zero. Independent descending coefficient elimination recovers quotient and remainder. Product derivative and quotient derivative numerator are checked again by a separate direct double-sum coefficient formula. These checks share rational arithmetic, so this is independent algorithmic evidence within that trusted arithmetic implementation, not a proof about Python or hardware.

The rational example has 18 distinct exercises: three constant quotient choices × two nonzero leading choices × three remainders. It does not enumerate all rational polynomials. Each result retains the divisor, dividend, quotient, remainder, product derivative, quotient derivative numerator/denominator, and the condition `b(x) != 0`. The condition is essential for the rational function; polynomial identities themselves do not acquire an artificial pointwise restriction.

`export_native` emits division, product derivative and quotient-rule numerator calculations. Tests compile and execute that emitted source with the actual existing native VM and compare hand-derived results. The independently executable generator package does not require the native VM to generate/check its objects; the optional emitted `.polyia` example requires that separate compiler.

## Inverse cases and curriculum

Polynomial inverse requests admit either an exact target dividend (`target`) or a point constraint (`value_at` and `target_value`). These alternatives cannot be mixed. They search precisely the finite card domain and retain exact division witnesses.

- `UNIQUE_IN_DECLARED_DOMAIN`: the exhausted domain contains exactly one matching construction.
- `MULTIPLE_IN_DECLARED_DOMAIN`: the exhausted domain contains multiple constructions; the point-constraint example is deliberately noninjective.
- `NO_PREIMAGE_IN_DECLARED_DOMAIN`: zero matches after domain exhaustion, not a claim about all polynomials.
- `UNRESOLVED_SEARCH_BUDGET`: an incomplete frontier, including operation, candidate, or search bounds. It cannot be promoted to impossibility or uniqueness.

The four [inverse fixtures](../examples/generators/) demonstrate these outcomes. The curriculum follows exact fraction multiply/add → polynomial long division → product derivative → quotient derivative, with actual operands/results, prerequisite IDs, source references and explicit assumptions. This is a four-step worked path, not a complete course, learner model, or assessment system.

## State trace, limits and costs

The state vocabulary includes INPUT, GENERATE, CONSTRAIN, VERIFY, REPRESENT, COMPLETE, STOPPED and REFUSED. Execution retains admission and completed generation/constraint/check phases for each admitted candidate. Rejected prefixes and inverse mismatches are summarized in final counts. A representation has a separate INPUT→VERIFY→REPRESENT trace and no tool calls. No external tool is silently available.

The worker reports generated, duplicate, refused, tested, admitted and frontier-visit counts. `generated` counts produced admissible family objects before inverse filtering; `tested` counts their completed independent checks. `refused` includes nonmember prefixes, invalid leading-coefficient choices and inverse mismatches; these counters are not presented as disjoint parts of one denominator. Canonical candidate IDs prevent duplicate admission. The frontier is finite and resumed only by an explicit new request; this increment does not install an autonomous background research loop.

There are two caller-visible ceilings: `search_budget` bounds visited prefixes/constructor invocations, and the card's `work_units` bounds operation credits. Regular credits count prefix visits, start/token steps and reference-AST calls. Polynomial credits reserve a conservative rational-kernel allowance before construction; the formula is recorded in each report. These are defined accounting units, not total CPU instructions, time, energy, or compiler cost. Compilation has separate hard state/work limits. Python/runtime overhead, hashing and serialization are separately bounded by object/output ceilings but not included in the operation-credit number.

Hard ceilings include 64 grammar nodes, depth 12, word length 32, 512 NFA states, 128 reachable DFA states, frontier queue 8,192, 200,000 operation credits, 256 admitted objects, 256-bit rational numerator/denominator, and 2 MiB serialized output. Nested/repeated grammars cannot exceed these bounds. A pause request refuses before executing the frontier. An exhausted search retains admitted partial results and marks `complete: false`; a transport/output or malformed-input refusal may contain only its structured reason. There is no OS deadline in this pure module; process isolation is a separate runtime responsibility.

## Portable packages

Build either supported example into a new output directory:

```sh
/opt/polyia/runtime/bin/python3 -B tools/build_generator_package.py \
  --card examples/generators/protocol.card.json --output /tmp/polyia-protocol-package
/opt/polyia/runtime/bin/python3 -B tools/build_generator_package.py \
  --card examples/generators/rational-division.card.json --output /tmp/polyia-rational-package
```

The output includes the fixed runtime, compiled model, source card, bounds, expected fixture, executable input, verifier, and exact documentary source bytes. Polynomial packages additionally contain emitted `.polyia` source, curriculum and explanation. The tool hashes every source before writing; a changed source or existing destination refuses. It exports only the family runtime and its documentary closure, not the entire repository.

Move the package to an independent directory, retain the build receipt separately, then run:

```sh
python3 -I -B /trusted/PolyIA/tools/verify_generator_package.py \
  --package /path/to/package --manifest-sha256 RECEIPT_DIGEST
python3 -I -B /path/to/package/runtime.py run < /path/to/package/run.json
```

Use the checker from a separately trusted installation outside the candidate package. The candidate’s own `verify.py` is untrusted code and must not be executed to establish its trust; its bundled copy is a convenience only after independent authentication. The trusted installed checker checks the exact manifest digest supplied externally, all captured file bytes and the file census before independently running authenticated runtime bytes copied to a private temporary directory in an isolated Python interpreter. Later candidate-file edits cannot replace those captured execution bytes. Files are admitted with nonblocking, no-follow opens and descriptor-level regular-file checks before bounded reads, so a FIFO or device is refused before execution. The external manifest digest authenticates custody; it does not authorize arbitrary Python. The trusted checker separately admits only its installation-owned exact generator-runtime SHA-256, with no caller override. A historical runtime requires the corresponding independently trusted historical checker. It compares the complete report with the captured fixture and imposes a 15-second subprocess timeout for this fixture. This is an executable reproducibility check, not OS sandbox-escape certification. An untrusted package/manifest without an external expected digest is not authenticated.

## Source audit and remaining inherited acceptance

[GENERATORS_SOURCE_AUDIT.json](GENERATORS_SOURCE_AUDIT.json) preserves the exact 23 directly mapped core records read, their original text/locations/hashes, and selected supplemental record identities. Design also read the full relevant technical treatise, state machine, concierge contract, TREE compiler and CGT SDK sources; the core source rows; the relational foundation; current PIA-097–108; and SF-06/07/08 plus relevant formal vocabulary. The audit records 1,038 supplemental mappings in the broad inherited corpus. It does **not** claim that all 1,038 records were individually read or discharged.

| Current requirement | Actual evidence in this increment | Remaining scope |
| --- | --- | --- |
| PIA-097 | Constructive words/polynomials, derivations, independent algorithms | Wider inherited grammars/benchmarks remain open |
| PIA-098 | Strict typed deterministic grammar cards; separate absent learned parameters | Probabilistic and optional neural schema/acceptance not implemented |
| PIA-099 | Two styles preserve exact relations, source locks and domains; unsupported claims refuse | No open-domain intent or morphological/linguistic completeness |
| PIA-100 | Bound traces and separately identified style views | Broader tool/controller and autonomous orchestration acceptance open |
| PIA-101 | Core has no optional inference dependency | No narrow neural model comparison, error or latency benchmark |
| PIA-102 | Source-locked portable packages with clean-process fixture reruns | Broader specialization, timing and platform acceptance open |
| PIA-103 | Seed zero, explicit no-sampling algorithm; 1,000 distinct inputs repeated | No stochastic distributional evaluation or cross-machine benchmark |
| PIA-104 | Unique, multiple, finite-empty and resource-unresolved exact fixtures | Wider inverse methods and inherited success-rate benchmarks open |
| PIA-105 | Calculated fractions→division→derivative graph | Full curricular breadth and 100 exercises per pillar not provided |
| PIA-106 | Two actual runnable bounded family packages; unsupported family refusal | General classes, SDKs, ODE/integration/linear-algebra/chemistry families open |
| PIA-107 | DFA reduction threshold ≥1, exact product equivalence, negative/nonimproving controls | Total production-cost benchmark and broader optimization acceptance open |
| PIA-108 | Finite frontier, counts, operation credits, explicit pause/stop | No standing-authority continuous research worker installed |

The inherited sources demand substantially more than two examples. In particular, the covalent-word/QM9 fixture (738 generated molecules and 48/48 recall in its declared slice), integration-by-parts equivalence, full subject machine breadth, requested-method inverse-trace success ≥95%, five new model classes with timings, cross-machine determinism, stochastic evaluations, and sandbox acceptance are not satisfied by this increment. No benchmark has been silently replaced with a smaller one, and source obligations retain their original authority.

## Verification

Run `python3 -B -m unittest discover -s tests -p 'test_generator*.py' -v`. Tests cover exact outputs and negative cases, a 1,000-input deterministic comparison, finite-language minimization, meaningful inverse ambiguity, resource/unknown-operation refusal, forged packages and rehashed derivations, 256-object trace replay, exact prose relations, real native compilation/execution, portable source custody, modified-runtime rejection and no mutation of an existing package destination. Clean-process testing uses the current host/runtime, not a claim of cross-machine testing.
