# POLYIA mathematical and software foundations

## 1. Identity of an independent computational unit

Define a **Computational Atom** relative to an admitted interface and observable:

`A = (id, version, Σ, G, I, O, δ, Γ, ε, P, C, B)`

- `id/version` immutable identity and semantic-version contract.
- `Σ/G` admitted alphabet and source grammar.
- `I/O` typed input/output ports, which may be structured.
- `δ` execution semantics (partial function or relation); never inferred from a name.
- `Γ` preconditions, invariants, effect/capability policy and negative grammar.
- `ε` provenance/epistemic grade for the implementation and emitted results.
- `P` proof/validation procedure (proof obligations *or* test witnesses; do not equate them).
- `C` quantitative cost model (build latency, runtime, memory, candidate count, verification).
- `B` bounded resource budget and failure/stop conditions.

An atom is **independently installable, versionable, testable, and specifiable**; not necessarily tiny in code size. Its dependencies are on declared contracts only; any undeclared runtime dependency is a defect. "Zero coupling" is thus defined as **zero undeclared implementation coupling**, not absence of interface dependencies.

## 2. Tower, pillar, forge

A representation tower `T=(L0, f0, L1, ..., fn-1, Ln)` has typed maps `fi:Li→Li+1` where maps may be partial or multivalued with explicit admitted domain. Its round-trip law is defined relative to an observable `o`, not assumed identity: `o(reconstruct_i(fi(x)))=o(x)` only when certified. An exception returns a finite candidate fiber, an explicit loss statement, or a refusal.

A pillar is `P=(source,target,precondition,invariant,verifier,counterexamples)` and asserts preservation `Γ(x) => Φ(f(x))` **only after proof or adequate scoped testing is recorded**. `P` is a formal device unique to our vocabulary, not a renamed established single algebraic object.

A forge is a typed multicategorical/operadic composition of atoms when source-output types, effects, policies and evidence contracts match. For a simple two-step composition, `δ_B ∘ δ_A` is admitted only if `Out(A)≼In(B)` plus required guards. For multi-input joins, every port is separately resolved. Cycles require explicit fixed-point semantics and termination argument; v0.1 rejects cycles.

## 3. A generator with its own compiler

Define **Generative Capability Class** `GC=(Grammar, Enumerator, Typechecker, Compiler, Executor, Verifier)` where:

1. `Grammar` describes a (possibly infinite) language of lawful source expressions.
2. `Enumerator` can enumerate or conditionally construct candidates under budgets.
3. `Typechecker` rejects invalid port/type/effect combinations.
4. `Compiler` maps a typed AST to PIR, bytecode, WASM/WIT or a backend-specific IR.
5. `Executor` runs admitted operations with resource bounds and capability security.
6. `Verifier` checks observable round trips, safety, contracts, and independent negative cases.

A class can be a factory of compiled programs; there is no OOP requirement that a class just store methods. However generated programs remain subject to language semantics, and "deterministic generation" means identical inputs, versions, policies and seeds produce identical outputs. Nondeterministic search may be useful but must record seeds/frontiers and cannot claim bit-for-bit replay without conditions.

## 4. Families of classical generative models

- **Regular / weighted finite-state models** for pronunciation mapping, morphophonology, phonetic matching and bounded rewrite; weighted semiring choice explicit. Compose transducers over matched alphabets, never naive concatenation of incompatible symbol codes.
- **Context-free / attribute grammars** for nested syntax, controlled natural-language templates, compiler ASTs and scene graph composition.
- **Constraint-solving & term rewriting** for typed equations, morphological feature unification, normalization and generative law selection.
- **Datalog / fixed-point inference** for finite relational closures with stratified negation; provenance and monotonicity must be declared.
- **Typed transition systems** for agent behavior, stateful scenes, query plans, handoffs, privacy and authority.
- **Program synthesis & partial evaluation** for assembling a minimal specialized SDK from a larger library; require language/resource bounds.
- **Grammar-controlled deterministic text generation** for scoped dialogue/speech. Coverage, refusal and fallback are explicit; no claim of open-domain LLM parity.

Finite-state automata cannot parse arbitrary unbounded nested structure. Unrestricted general-purpose programs may diverge; POLYIA never claims decidable termination for arbitrary Turing-complete inputs.

## 5. Composite agency

Given commission `p`, registry `R`, evidence policy `E` and runtime budget `B`, the compiler solves:

`S* = arg min_S (runtime_cost(S)+λ size(S)+μ verification_cost(S))`

subject to `provides(S) ⊇ obligations(p)`, all typed dependencies satisfied, effects authorized, and evidence claims within source grade. General minimum-cost component selection is potentially combinatorial; the reference avoids claiming global optimum: it requires a unique provider per type and performs bounded dependency closure. The production planner should compare SAT/SMT, A* or bounded dynamic search to a deterministic baseline. **No O(1) universal search**.

A specialized assembly is a partially evaluated version of the umbrella agency, not a full copy with feature flags. It has a manifest, type signature, dependency lock, capability policy, PIR plan and state machine with replayable evidence.

## 6. A composed automaton as result

`M=(Q, Σ, δ, q0, F, guards, I/O, witness, provenance, version)` where `Q` includes harness and domain states; transitions carry inputs/outputs and specific execution versions; `witness` proves the construction matched declared interfaces and records runtime observations separately. When a computation is nondeterministic, `δ` is a relation; the artifact carries possible branches. A state-machine artifact must contain enough semantics to be **executable by a compatible runtime**; merely drawing a DAG is an inspection artifact, not a runnable machine. v0.1 emits a typed *plan specification* and DOT/HTML projections; a live PHONEX execution backend is a further gate.

## 7. State machine vs parser vs grammar

A grammar defines valid expressions; a compiler interprets them; an automaton implements selected transition semantics. A parser state is not the same as a physical state or epistemic state. Lisp s-expressions and our P9 "Parenthology" are syntax strategies; full Lisp semantics should not be inferred from the use of parentheses. Turing machines mark a computability boundary, not a promise that a finite-state engine can simulate arbitrary language descriptions efficiently.

## 8. Information-theoretic audit

For a source `X` and projection `Y=f(X)`, compare conditional information `H(X|Y)`; use the **same distribution** for fair comparisons. A finite source set with equiprobable elements has `log2 |fiber|` bits of cardinality ambiguity; under non-uniform probabilities the Shannon conditional entropy differs. Keep original bytes plus reversible normalized index if exact reconstruction matters. Content hashes are one-way identifiers; dereference only succeeds given stored content. Compression effectiveness must count dictionary, codebook and index size.

## 9. Relational algebra and negative evidence

Relations include `entails`, `transforms`, `derived_from`, `phonetic_near`, `translated_attested`, `same_shape`, `analogous`, `contradicts`, `cannot_compose`, `unknown`. Lack of an edge is not a negative edge. Evidence status distinct from confidence and mathematical weight. Cross-source agreement is not automatic proof of independence (shared upstream origins can create correlated evidence). A source contradiction is a first-class object with its scope and witnesses.

## 10. Benchmarks and honest claims

Compare (a) baseline plain indexes, (b) OpenFST/HFST feature-specific programs, (c) bounded graph queries, (d) semantic compilation with optional LLM. Metrics: build/storage cost, p50/p95/p99 per query, throughput, recall/precision, correctness, false admissibility, provenance, energy if instrumentation exists. Avoid claiming an innovative architecture is inherently faster. Test adversarial workloads and multilingual coverage. Anomaly/novelty claims require replicable baselines and independent analysis.

## External anchors

- OpenFst finite-state composition and semiring weights: https://github.com/google-research/openfst/blob/main/docs/quick_tour.md
- WebAssembly Component Model and WIT: https://github.com/WebAssembly/component-model/blob/main/design/mvp/WIT.md
- Soufflé Datalog: https://souffle-lang.github.io/
- URI and capability security for PURL are separate typed surfaces, not generic authority borrowed by a new compiler.
