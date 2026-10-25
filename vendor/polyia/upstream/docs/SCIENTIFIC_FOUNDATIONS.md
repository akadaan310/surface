# Poly IA — Scientific foundations and constructive obligations

**Edition:** 1.0, 24 October 2026. **Status:** an executable research specification, with a bounded bootstrap supplied separately. **Scope:** Option A incorporates the vocabulary, division charters, scientific obligations, produce/verify discipline and working interface requested from Options B and C.

This document gives the proposed system a precise subject: representations, admitted operations, their compositions, the evidence that supports their use, and the machines that preserve their history. It does not assume that every representation has a unique meaning, that every true claim is computable, or that a finite commission can finish mathematics. The constitutional requirement is complete custody of the canonical corpus, an extensible coverage map and working evidence-producing capabilities with explicit limits.

Stable continuity references used here are `K-SRC` (custody), `K-SEM` (semantics), `K-STATE` (machine state), `K-EVD` (evidence), `K-GEN` (generation), `K-PATH` (composition), `K-COST` (resources), `K-EVOLVE` (versioned improvement), and `K-FRONTIER` (open research). Exact constitutional clause IDs are maintained in the package registries.

## SF-01. The inherited kernel and its running instance

Retain the Relational Generativity and UCG kernel:

\[
\mathcal K=(A,Q,\mathcal O,\delta,\llbracket\cdot\rrbracket,\Pi,I,V).
\]

Here `A` is a typed alphabet, `Q` a state space, `O` the declared operations, `δ` their partial transition semantics, `⟦·⟧` contextual interpretation, `Π` observational projections, `I` invariants and `V` the verification interface. A uniform interface lets unrelated subjects be inspected and composed where their contracts permit it. It supplies no universal solver. The chemistry grammar, polynomial algebra and an audio controller retain different meanings and evidence requirements. [S-RG §3; S-UCG §§0–1]

A running instance is

\[
R=(\mathcal K_v,s,E,D,H,\alpha,\rho,B),
\]

where `v` pins the kernel version, `s` is current state, `E` the environment, `D` resolved dependencies, `H` history, `α` authority, `ρ` randomness and clock policy, and `B` resource budgets. This is a proposed Poly IA record, not a replacement for the inherited tuple. It makes distinctions that a source string alone cannot make.

For deterministic resolution, equal relevant inputs imply equal resolved results. A changed dependency permits a different result; it does not force one. Two compiler versions can produce the same normalized program. Accordingly, the inherited “different IR iff a dependency changes” formulation is refined to dependency recording plus a deterministic equality condition. This amendment preserves the original source and avoids an invalid converse. [S-RG §§3,5,9]

Every subject supplies `describe`, `parse`, `admit`, `evaluate`, `observe`, `trace` and `verify`, or an explicit `UNSUPPORTED` result for the unavailable operation. A descriptive subject can be fully ingested without a complete evaluator. Its source status remains canonical while its capability status remains descriptive.

## SF-02. Letters, grammars, expressions and programs

An alphabet is a declared collection of units with identity, sort and admissible roles. The units may be characters, tokens, matrix operators, geometric cells or previously certified constructions. A table of units becomes operational when its ordering, relations and permitted compositions are defined. It is not enough to rename a collection an alphabet.

A basic grammar has terminals, nonterminals, formation rules and an entry sort. A semantic grammar adds interpretation and a context. An expression is a well-formed term in that grammar; a judgment such as `Γ ⊢ e : T` states what sort it has under assumptions `Γ`. Its evaluation can be partial. A program additionally declares an execution model and effects. A mathematical formula can describe an object, assert a proposition or prescribe a calculation; its grammatical role must be recorded instead of inferred from typography.

For example, `f(g(x))` expresses composition when the output of `g` lies in the admitted input domain of `f`. An evaluator may first compute `g(x)` and then `f` on that result; a symbolic system may instead retain the composed expression. A type or domain failure must be visible in both cases.

Likewise, `AᵀB` is compact syntax. If `A` has shape `m×n` and `B` has shape `m×p`, its result has shape `n×p`. The conventional dense implementation uses `nmp` scalar multiplications and, for positive `m`, `np(m−1)` scalar additions. Compact notation does not imply constant computational cost. A shape mismatch has no value under this contract until another operation is specified.

`H₂O` is a chemical formula interpreted under a chemical notation contract. The formula alone does not specify every structural, physical or computational property of water. An executable construction requires a parser, a representation of the requested object and an admitted constructor. The system may compare the spellings `HHO` and `H₂O` under a particular normalization, but it must not adopt an unconditional equivalence between all chemical strings with matching letters. [S-UCG §§1,3.1–3.4]

The cost alphabet distinguishes `O(1)`, `O(log n)`, `O(n)`, polynomial and exponential bounds together with time, memory, I/O and output size. `O(2)` describes a constant bound just as `O(1)` does; `O(2^n)` is the usual exponential expression. These classes are annotations relative to a computational model, input measure and operation—not meanings concealed in a glyph.

## SF-03. An alphabet whose letters are grammars

Let a grammar package be

\[
G=(id,v,\Sigma,N,P,S,\mathsf{Type},\mathsf{Eval},\mathsf{Effects},\mathsf{Cost},\mathsf{Evidence}).
\]

Its serialized definition can become a form in a higher-level alphabet. A higher-level letter `ℓ_G` refers to the exact package and its public boundary. The surrounding grammar governs when such packages may be composed: an output sort must fit an input sort; effects must fit authority; invariants and context requirements must be met. This formalizes the owner's “alphabets of grammars” without flattening a grammar into an untyped name.

There are two related constructions:

1. **Quotation:** a grammar is represented as inspectable data. Quoting it confers no execution authority.
2. **Promotion:** a checked grammar, derivation or operation becomes a reusable letter with an expansion map and a certified boundary.

For a promoted path `p` at level `k`, record `promote(p)=ℓ` and `expand(ℓ)=p`. At the next level,

\[
\Sigma_{k+1}=\Sigma_k\;\cup\;\{\ell_p\mid p\text{ satisfies the named promotion contract}\}.
\]

Retaining `p` permits exact representation recovery. Semantic preservation is a separate obligation:

\[
\mathsf{Obs}(\mathsf{Eval}_{k+1}(\ell,c))
 =\mathsf{Obs}(\mathsf{Eval}_k(\mathsf{expand}(\ell),c))
\]

for the stated context domain and chosen observables. A proof may establish the law for an entire admitted domain. A finite test establishes it only for the tested cases. Effects, refusal behavior, dependency versions and cost contracts belong in the comparison; checking the final number alone is inadequate for an effectful operation. [S-PL §§4–5; S-RG §5]

A promotion certificate therefore names the source definition, expansion digest, input and output sorts, contexts, preserved observables, effect boundary, loss contract, verifier and result. It carries a level and dependency graph. Cyclic expansions are rejected unless a separate recursive construction gives fixed-point semantics, guarded unfolding and a resource policy. An arbitrary self-reference is not a useful infinity.

**Lossless abbreviation** and **lossy quotient** are different operations. If a normalization identifies several expressions, its inverse is generally a fiber or candidate set. Keeping an archive of the original can recover those original bytes, but it does not turn the normalized representation into an injective map.

The bootstrap's promotion experiment is an acceptance specimen: it must show exact unfolding, a separately checked semantic law and a failed or inapplicable case. The complete commission must extend this to corpus grammar packages, not merely rename the specimen as a universal implementation.

## SF-04. Forms, entanglements and typed Q-paths

Adopt the Infinity packet's Entangled Form Complex:

\[
\mathbb E=(V,H,P,\tau,\Omega,\mathcal C,\mathcal W,\mu).
\]

`V` contains typed forms; `H` typed directed hyperedges; `P` ordered and named incidence ports; `τ` sorts; `Ω` operation signatures; `C` contexts and constraints; `W` witnesses, hypotheses and refutations; `μ` optional measurements. Relations can themselves become forms at a declared reflection level. The current owner's decision assigns this research to **Division IX — Infinity**, superseding the packet's earlier unnumbered placement. [S-INF §§B–D]

The recovered Q-Strings research defines a **Q-String** as a quantifiable, typed, grammar-bearing relational incidence with content identity, plural metadata strands and compiled operations. Its minimal pairwise form is `q=(src,dst,relation,grammar,scope,level,witness,status,version)`. Its higher-arity **Q-Bundle** carries ordered input/output roles and separate evidence strands. **G-ships** retain their original directed labeled multigraph `H=(V,E,Σ,τ)` and composable edge-words; **Q-Ship** means port-checked composition. The proposed Q-path profile here extends this lineage with explicit derivation structure. Its `Q` does not assert quantum hardware, amplitudes, interference or physical entanglement. [S-Q §§0,3–4]

A Q-step is a typed operation application:

\[
q=(op_v,\{role_i\mapsto x_i\},c,\{role_j\mapsto y_j\},w,\lambda),
\]

where `c` is the resolved context, `w` evidence and `λ` declared loss/effects. A linear Q-path is a sequence of compatible unary steps. General composition is a derivation tree or DAG of operation applications with explicit joint premises. A diagram is a view of this structure; its geometry is not the structure's semantics.

Suppose a rule needs `polynomial`, `nonzero divisor` and `coefficient-field contract` together. Drawing three arrows toward a result cannot make any single premise sufficient. The enabling predicate checks **all ports**, their roles, multiplicities, types, context compatibility and evidence thresholds. Wrong argument order, one missing input or a conflicting field context must produce an explicit refusal.

The same incidence may carry several strands: one source attestation, one exact derivation and one rejected conjecture. They have independent status. A rejected strand does not erase a separate valid strand; several weak strands do not automatically become a proof. A path that changes context records the adapter and its conditions. It cannot silently use an assumption proved under one coefficient field or language edition under another.

Retain the Q source's two identities: `entity_id` follows an entity across versions; `content_cid` identifies exact immutable encoded content. A Q-address dereferences stored bytes through an index; it does not invert a digest. Q-indexes and materialized views account for construction, storage, invalidation, query and output costs. Native arrays, trees and other efficient representations remain native beneath their semantic adapters. [S-Q §§3.1–4]

For a fixed finite registry, a monotone rule operator is

\[
T_\Omega(S)=S\cup\{outputs(h):inputs(h)\subseteq S\land Admit(h,c)\}.
\]

Repeated application reaches a fixed point after at most `|V|` rounds containing a strict addition. This proves termination of that bounded closure process. It establishes neither the external truth of the rules nor termination when the rules create an unbounded population of new forms. Changing evidence, revoking a rule or changing context starts a new versioned closure epoch. [S-INF §F]

“Fully reachable” means each registered object is addressable, its dependencies are resolvable, and admissible paths can be searched within declared bounds. It does not require a meaningful path between every two objects. A missing bridge, a type incompatibility and a proved impossibility are different results. The concierge must expose all three.

The inherited **Q-Closure Certificate** accounts for every required in-scope port as satisfied, refused or explicitly externalized. It certifies the declared coverage contract, not a mathematically complete universe. A Q-frontier item is a remaining typed obligation whose absence and possible refutation are represented separately. [S-Q §§4–5]

## SF-05. Calculus of forms, folds and identity

The calculus is a family of typed operations: factor, compose, project, lift, normalize, encode, interpret, reify and certify. There is no unconditional operator that converts any form into any other form. Each operation declares the questions that its result can answer and what it loses. [S-INF §§C–E]

For a map `f:X→Y`, the fiber above `y` is `{x∈X:f(x)=y}`. Its kernel-pair equivalence is `x~x′` when `f(x)=f(x′)`. A linear nullspace is available only when vector-space and linearity assumptions hold. A relation has an inverse relation; it need not have a single-valued inverse. These distinctions let a name, a normal form, a matrix projection and a language translation share an interface without being confused.

Plicastratum contributes `explicate` (expand), `implicate` (recognize a valid fold), `complicate` (product alphabet), `replicate` (repeat a substitution), `applicate` (domain adapter) and `promote` (certified higher-level letter). Its seven strata describe module layers, not University division numbers. [S-PL §§2–5]

The source's identity depths remain distinct: current state; current state plus a declared memory aggregate; and full ordered history. Its “holonomy” is a named event aggregate in a specified group. Poly IA preserves that mathematical construction without asserting that the software implements physical parallel transport. With a noncommutative aggregate, order matters. With a commutative or lossy aggregate, distinct histories can coincide. The complete ledger retains distinctions an aggregate may forget.

Namespaced definitions prevent collisions. `plica.closable` means a path returns to its starting state; `rg.closable` names a closure/composition capability. `plica.complete` describes a single-cycle successor; it is not logical completeness or Turing completeness. A single cycle supplies a cyclic action; identifying its elements with the group `Z/nZ` requires a chosen origin. “Seven-complete” remains an explicitly scoped source construction, not a theorem about universal computation.

Division Knot (`DK0`) is a cross-cutting relational view. It does not acquire the number VII merely because VII is open. The owner's spoken “Division Not” remains an alias requiring source resolution if it denotes something beyond Knot. Topological vocabulary requires actual structure: a graph of related names is not automatically a topological space; a nerve theorem needs the required cover assumptions; a sheaf needs defined restriction maps and verified compatibility/gluing conditions. [S-DK0; S-INF §E]

## SF-06. A complete worked bridge: division, factoring and differentiation

Let `K` be a field and `p,b∈K[x]` with `b≠0`. Polynomial division constructs unique `q,r` satisfying

\[
p=bq+r,\qquad r=0\;\text{or}\;\deg r<\deg b.
\]

The field assumption enables division by the leading coefficient. Over a general coefficient ring, this algorithm and its existence statement need a different contract. For real or complex differentiable interpretations, the rational function additionally restricts its domain to `b(x)≠0`.

Take

\[
p=x^3-2x+4,\quad b=x-1,\quad q=x^2+x-1,\quad r=3.
\]

Multiplication and coefficient comparison check `p=(x−1)(x²+x−1)+3` exactly. Hence for `x≠1`,

\[
\frac p b=q+\frac r b=x^2+x-1+\frac3{x-1}.
\]

The product rule, applied to `b·b^{-1}=1`, yields `(b^{-1})′=−b′/b²` on that domain. Applying it again gives the quotient rule:

\[
\left(\frac p b\right)'=\frac{p'b-pb'}{b^2}.
\]

Differentiating the quotient-and-remainder form instead gives

\[
q'+\frac{r'b-rb'}{b^2}=2x+1-\frac3{(x-1)^2}.
\]

Both numerators become `2x³−3x²−2` after expressing them over `(x−1)²`. An exact coefficient certificate checks equality without relying on floating samples. The proof trace keeps the field, differentiability and nonzero-denominator assumptions.

Factoring fits the same system through another operation. `(x²−1)/(x−1)` simplifies to `x+1` on `x≠1`; the simplified polynomial extends to `x=1`, but that extension changes the domain. A concierge that drops the exclusion while saying “the same function everywhere” fails the contract.

The bridge explains both the relationship and the distinction between arithmetic fraction division, Euclidean division in `K[x]`, polynomial factorization and differentiation. They share operations and identities; they are not interchangeable algorithms. The query result should include a source-linked expression tree, domain assumptions, the constructed quotient/remainder, an exact witness, alternate derivations and nearby unanswered questions. [S-UCG §3.5; package scientific experiment `polynomial`]

## SF-07. Constructive generation without LLM inference

A generator is a registered procedure `Gen(spec,context,budget,seed)` returning candidates, derivations and refusals. It may enumerate typed terms, perform constrained search, execute rewrite rules, sample a probabilistic grammar or compose verified macros. None of these methods requires an LLM. An unbounded language can have a finite grammar while every individual run remains finite and bounded.

The baseline interpretation pipeline is: preserve input; detect supported forms; parse candidate structures; retrieve attested senses; enumerate typed interpretations; compose admitted operations; verify; render explanations from structured results. For an unsupported passage, it returns retained text, recognized spans, alternatives and open questions. It must not invent a semantic interpretation merely to produce a fluent answer.

A concrete non-LLM generator can construct arithmetic explanations. A typed expression grammar supplies `literal`, `add`, `multiply`, `divide`, `differentiate` and `explain-step`; a state machine tracks assumptions and the current goal; exact algebra verifies each transformation; a finite-state realization grammar selects terminology and sentence templates. A “concise” or “tutorial” mode changes the realization plan while preserving the same proof object. Tone is a rendering choice with measurable coverage, not authority to alter the mathematics.

A probabilistic context-free grammar can generate alternative descriptions within a declared finite vocabulary. A weighted finite-state transducer can realize morphology or terminology substitutions. A search policy can prefer shorter derivations or lower cost while retaining alternatives. All stochastic components record seeds and distributions. Replaying a recorded result and reproducing a stochastic run are separate operations.

Optional pretrained components may classify a speech intent, synthesize speech, propose a parse or estimate a ranking. They must declare model family, weights/version, input limits, measured accuracy and whether they perform LLM inference. They cannot become a dependency of core acceptance or bypass typing, domain checks, evidence requirements or tool authority. A non-LLM label alone does not make a neural prediction reliable.

The no-LLM acceptance combines dependency inspection, model-artifact and tool-capability declarations, execution tracing and an offline run. Offline execution alone is insufficient because a local LLM can run without a network. Optional external LLM clients may send ordinary declared commands; the command service and scientific kernel remain operational with those clients absent.

“Without LLM inference” still allows explicit logical inference, fixed-point rules and numerical computation. When an inherited paper says “no inference”, the implemented contract must distinguish its intended rejection of opaque model inference from ordinary rule-based deduction; it must not ban the very constructive reasoning the system is meant to perform.

### Language packs, Grammatonomia and PHONEX

The recovered Grammatonomia paper adopts the per-variety pack `L_v=(VarietyID,Σ,O,T,P,M,X,E)+NegativeGrammar`: sound/segment inventory, orthography, pronunciation transduction, phonotactics, morphology, lexicon and evidence. Its four depths are Α sound, Β form, Γ phrase and Δ sense. These are representational layers, not University divisions. Register a recognizer, generator and cross-pack transformer separately; an alphabet alone determines none of them. [S-GRAM §§0–1,5; S-POLY, PHONEX Specialist Architecture]

Preserve its seven proposed operator-profile names: Diaplectic, Catenary, Synthetic, Orbital, Positional, Componential and Holophrastic. They are measured house classifications, potentially blended across layers, rather than a proved exhaustive classification of every language. A privative record is `(level,feature,status,replacement,evidence)`; missing dataset coverage must not become a linguistic absence. Its ubiquity set is a hypothesis evaluated across attested packs, not an assumed universal grammar. Claims that the source's Wave-1 machines ran remain source-reported until individually reproduced. [S-GRAM §§2–8]

PHONEX supplies the shared semantic interface of variety ID, IPA/feature stream and evidence. Keep original spelling, orthographic version, pronunciation status, lexical sense and historical relationship separate. Contiguous initial-phone matching differs from substring matching. A weighted phonetic-neighbor operation does not prove cognacy, borrowing or translation. Calibrate cross-pack weights or label them incomparable. Unwritten varieties may have phonological and lexical packs with no invented orthography. FSTs handle their admitted regular/transduction fragments; syntax requiring nesting or long-distance constraints needs a stronger declared formalism. [S-POLY, PHONEX Specialist Architecture]

## SF-08. Tools, SDKs, APIs and machines as packages

A tool contract contains `id/version`, input/output schemas, preconditions, effects, authority scopes, resource bounds, deterministic or stochastic behavior, timeout/retry policy, evidence emitted and failure codes. Its implementation is a separately pinned object. A tool's natural-language description is not its executable definition.

Class methods, functions, CLI commands and HTTP endpoints are different bindings of such contracts. A package contains types, registered operators, grammar, state reducer, verifiers, fixtures, provenance, dependency lock and compatibility policy. An SDK offers typed client bindings and explicit revision guards. It cannot bypass the service's guards by setting a status directly.

The original Poly IA **Computational Atom**, `(id,version,Σ,G,I,O,δ,Γ,ε,P,C,B)`, is a package contract. Astra's **ATOM** tuple is a different machine contract. PIC/0.2's **CapabilityAtom** and general **Machine** supply another interchange proposal. Adapters must map these named versions explicitly rather than silently identify their tuples. “Zero coupling” in the original Poly IA means zero *undeclared implementation coupling*; declared interface dependencies remain necessary. [S-POLY, Technical Treatise §§1–3; S-PIC §1]

The inherited **Generative Capability Class** is `(Grammar,Enumerator,Typechecker,Compiler,Executor,Verifier)`. PIC's `Genesis(GrammarCard)` proposes a recognizer, generator, typed IR, optional compiler lowering, machine definition, proof obligations and witnesses. A generator of generators must pass typing/effect checks, interpreter-versus-compiled equivalence, negative cases, bounded refusal and pinned replay. Emitting source code or a plan drawing alone does not discharge these obligations. Production grammars must compile to an admitted typed native IR/bytecode/backend; the portable Python bootstrap is a semantic and control reference, not the completed production compiler. [S-POLY, Technical Treatise §§3,6–7; S-PIC §3; S-Q §0]

Identity and associativity laws apply only under a declared observable equivalence. Parallel composition selects synchronous products, asynchronous actors or another specified scheduling model; a graph cycle alone does not define feedback. If regrouping changes effects or failures, preserve grouping and describe the nonassociative semantics. Specialized assemblies should emit a dependency-closed package and executable state contract, not merely copy the whole agency behind feature flags. [S-PIC §2; S-POLY, Technical Treatise §5]

An HTTP-fetch tool, for example, accepts a structured URL and declared retrieval policy; it records bytes, retrieval time, response metadata and digest. It is not an invitation to execute a caller-supplied shell string. Computational tools declare whether they are **constructors**, **normalizers**, **filters**, **independent witnesses** or **renderers**. If a chemistry library sanitizes a candidate before sealing, that run is library-assisted construction/filtering; it cannot be described as having used the library only after the prediction.

Effects compose only where their contracts allow it. Pure operations can often be reordered when they commute under the declared equivalence. Two writes do not commute merely because their return values look similar. Replay reconstructs recorded state and tool results; reissuing an external effect is a new authorized operation. Uncertain dispatch outcomes remain explicit rather than being treated as exactly-once execution.

## SF-09. State grammars and constitutional execution

The commission machine, research machine and domain machines have distinct identities. A finite control state can govern an extensible data state; calling the controller finite-state does not bound the size of the corpus or imply that every computation it supervises is finite-state.

A state grammar declares states, events, guards, transitions, emitted effects, invariants and observable projections. The commission uses `NOT_STARTED → PRODUCED → VERIFIED → ACCEPTED`, with failure, correction and re-production explicitly represented by the implemented reducer. `PRODUCED` means inspectable outputs exist. `VERIFIED` means a registered verifier evaluated their current captured version. `ACCEPTED` is a scoped decision supported by that receipt. A checkbox supplied by a caller is no evidence.

Guidance has its own protocol: submitted, acknowledged/deferred/rejected, then applied only when a supported action actually changes the intended state. Acknowledging prose does not prove its implementation. Every application names the guidance ID, prior revision, effect and resulting revision. The service exposes pending guidance and conflicts so collaborators can see what remains unresolved.

The W3C SCXML specification provides established state/event/guard and hierarchical-control precedents. Poly IA does not claim SCXML conformance merely by adopting comparable concepts. Its actual bootstrap protocol is the documented JSON/HTTP contract. [P-SCXML §§3.1–3.5]

The durable event commit binds command, actor, resolved inputs, results, before/after state and source identities. A Git commit can link the code used for that state; it is not the same object as a database transaction. The checkpoint records both where available. Hash chains detect changes relative to a trusted prior root; they do not authenticate an adversarially replaced entire history. These limits are preserved from Astra's own contract. [S-ASTRA, Formal constitution]

## SF-10. Evidence and the proleptic loop

Keep three independent axes:

| Axis | Examples | Meaning |
|---|---|---|
| Source authority | canonical owner source; imported publication; generated candidate | Why this record belongs to the corpus |
| Claim kind | established result; house construction; hypothesis; stipulation; reported observation | What is being asserted |
| Evidence outcome | proved; exactly checked; symbolically checked; numerically supported; inconclusive; counterexample; resource limit | What a named procedure established, under what scope |

An owner-reviewed source is preserved as canonical without converting every historical benchmark into a newly reproduced result. “Verified” always identifies a proposition, version, input domain, verifier and evidence class.

The inherited proleptic procedure becomes: declare allowed inputs; generate; seal predictions; retrieve witness; compare; account for misses and gaps; amend under a new version. The execution harness must enforce witness isolation when blindness is claimed. A declaration in a JSON field alone does not enforce it. Repeated use of the same witness informs later versions and requires a new held-out evaluation. [S-UCG §2]

Exact algebraic checking, machine-checked proofs, independent implementations and empirical observations answer different questions. Numerical sampling supports a bounded empirical claim; it does not prove a general identity. A checker that evaluated no valid points must return `INCONCLUSIVE`, never success. A search that fails to find a recurrence within its bound does not prove nonrecurrence. Refusing an integral is not a proof that it has no elementary antiderivative.

The UCG source contains valuable experiments and explicit limits. Its original files remain unchanged. The new evidence system separately records known discrepancies: the role of sanitizing libraries; fixed numerical probes described as randomized; overly strong derivative-orbit conclusions; and the description of both `Q₈` and `A₄` as nonsplit examples, although `A₄` has a semidirect-product presentation. The correction is a linked claim with its own check, not an erasure of the research. [S-UCG §§3.3,3.5,4–5]

## SF-11. Corpus, nomenclature and interpretive restraint

The inherited Corpus Engine strata remain useful: S0 immutable sources, S1 source-linked spans, S2 form cards, S3 typed graded edges and S4 registered operations. Derived normalization and extraction layers must identify their transformations. Raw Unicode bytes, normalized text and a search skeleton remain separate objects. Unicode normalization defines particular equivalences; it does not preserve every original byte distinction or establish semantic equivalence. [S-CORPUS, Data structure/Cleaning pipeline; P-UNICODE §1]

Timeless/WAZNOMIA supplies contextual skeleton projections and set-valued inverse candidates. An undotted form does not determine a unique lexical item without constraints and evidence. Poly IA preserves diacritics and raw-surface distinctions before creating search views. The Arabic, Greek and Latin analyses supply candidates for language-specific morphology and nomenclature operations. They do not establish that every word's modern meaning is computable from etymological pieces. [S-TIMELESS, Foundational study; S-GL, Parts I–V]

Translation, transliteration, phonetic rendering, morphological analysis, historical borrowing and mathematical representation translation receive different operator types. A cross-language resemblance can support a research question. Attestation and grammatical analysis are needed to support a linguistic claim; domain evidence is additionally required for scientific semantics. “Unresolved”, “borrowed form”, “calque” and “multiple analyses” are valid useful outputs.

The human/machine application must let a user submit an article or prompt, inspect source spans and supported interpretations, see relevant domain operations, request exact computations, and review candidate improvements with derivations. An improvement states its objective—clearer terminology, corrected algebra, fewer unsupported assertions or a useful cross-domain analogy. It is not presumed better because it adds terminology.

## SF-12. Coverage, curriculum and the research frontier

Complete corpus custody, broad curriculum coverage and executable competence are separate measures. The canonical University registry, every book, generator and source repository form the mandatory inherited inventory. Mathematics and computing taxonomies supply additional coverage coordinates. MSC2020 is a research classification maintained by Mathematical Reviews and zbMATH; it can identify omissions without certifying competence. ACM's Computing Classification System supplies computing categories under its own version and terms. [P-MSC; P-ACM]

Each coverage node records sources, definitions, prerequisites, known operators, available constructive methods, tests, counterexamples, teaching material and unresolved capabilities. Major families include logic and foundations; algebra and number; combinatorics; geometry and topology; analysis and differential equations; probability and statistics; optimization and numerical methods; computation and complexity; programming languages and semantics; data structures and algorithms; systems and protocols; graphics, acoustics and simulation; and domain sciences with explicit empirical interfaces. This list organizes work; the pinned classifications and corpus inventory determine detailed coverage.

An innovation candidate is a proposed grammar, operator, representation, bridge, verifier or implementation change with a baseline, objective and falsifiable claim. Search ranks candidates by expected value, cost, uncertainty and coverage needs. Promotion requires measured improvement or a new verified capability while preserving required invariants. Counterexamples, neutral results and cost regressions remain first-class outcomes.

The “infinite Rolodex” becomes a potentially extensible, addressable collection with finite searches, pagination and budgets. Continuous research consists of bounded runs on an always-available service, with durable progress, cancellation and resumable queues. No theorem promises that every run yields a discovery. The post-commission University is the institution for cultivating, testing and teaching these methods under the accompanying charter.

## SF-13. Minimum scientific acceptance obligations

| Obligation | Required positive evidence | Required negative evidence |
|---|---|---|
| Typed interpretation | A parsed expression with assumptions and reproducible denotation | Unsupported syntax or domain mismatch is retained and refused |
| Grammar promotion | Exact expansion plus a distinct semantic-preservation check | Incompatible context, circular unguarded expansion or declared loss is visible |
| Multi-input Q composition | A genuine joint-input derivation with all roles and witnesses | One absent premise, wrong role/type and conflicting context fail |
| Polynomial bridge | Exact division certificate and equivalent derivative derivations | Zero divisor and dropped denominator restriction fail |
| Non-LLM generation | Candidate, derivation, verification and explanation with inference disabled | Optional model unavailable does not break the baseline |
| Source fidelity | Original bytes, extracted spans and transformations resolve | Changed or absent source is not silently accepted |
| Evolution | Versioned candidate beats a declared baseline under required constraints | Regression or inconclusive outcome remains inactive |
| State/evidence linkage | Produce, verifier receipt, acceptance and checkpoint bind the same captured outputs | Forged status or stale verification cannot accept a new output |

The bootstrap demonstrates bounded cases. The complete commission must connect these obligations to the real corpus, full interface and deployed service. The acceptance registry is authoritative for what has actually been produced and checked; this specification is not a completion receipt.

## Sources and local locator convention

Original filenames and archive member paths below are immutable locators. `registry/sources.json` and the package source reconciliation records resolve their digests and packaged locations. An archive citation names its member, not a claim that all its code has been rerun.

| Key | Source and relevant scope |
|---|---|
| PACKAGE | Current owner directive, `docs/APPROVED_DESIGN.md`, this specification and the versioned constitutional registry; new package constructions are labeled as such |
| S-RG | `RELATIONAL_GENERATIVITY_FOUNDATION_V0_1.md`, §§1–10 |
| S-UCG | `UCG_FOUNDATIONS.md`; accompanying `UCG_SEED_v0.1.zip` and `UCG_CODEX_CONSTITUTIONAL_COMMISSION.md` |
| S-PL | `PLICASTRATUM.md`, §§2–5 and 9–10 |
| S-INF | `Division_Infinity_CEF_Research_Packet_v0.1(1).zip` → `division_infinity_packet/RESEARCH_MANIFESTO.md` and `INTEGRATION_MAP.md` |
| S-DK0 | `SUBSTRATE_UNIVERSITY_DIVISION_KNOT_V0_1.md`; recovered source, with current custody status in the manifest |
| S-Q | `Q_STRINGS_FORMAL_RESEARCH.md` and `Q_STRINGS_GSHIP_RESEARCH_v0.1.zip`; historical profile, with recovery and schema mapping recorded separately |
| S-GRAM | `GRAMMATONOMIA — The Science of Grammars.md`, §§0–8; recovered working paper |
| S-PIC | `POLYIA_UCG_GRAMMATONOMIA_RECONCILIATION_v0.1.zip` → `POLYIA_UCG_GRAMMATONOMIA_RECONCILIATION_v0.1/CANONICAL_CONTRACT.md`, PIC/0.2 proposal |
| S-POLY | `POLYIA_FOUNDATION_V0_1.zip` → `POLYIA_FOUNDATION_V0_1/docs/TECHNICAL_TREATISE.md` and `PHONEX_SPECIALIST_ARCHITECTURE.md` |
| S-TIMELESS | `Timeless_WAZNOMIA_QIA_Handoff_v0.1 (1).zip` → `Timeless_WAZNOMIA_QIA_Handoff_v0.1/FOUNDATIONAL_STUDY.md` |
| S-CORPUS | `corpus engine design (1).md` |
| S-GL | `GREEK_LATIN_DETERMINATIONS (1).md` |
| S-TRE | `TRE_TREE_FOUNDATIONS_RESEARCH_PACKET_V01.zip` → `TRE_TREE_FOUNDATIONS_V01/docs/00_CONSTITUTION.md`, `01_MACHINE_COMPILER.md`, `04_CGIT_CORPORA_BRIDGES.md` |
| S-ASTRA | `ASTRA_CELESTIAL_SHELLS_ATOM_CODEX_GOD_SEED_V02.zip` → `ASTRA_CELESTIAL_SHELLS_V02/docs/FORMAL_CONSTITUTION.md`, `SCIENTIFIC_AND_AUDIO_CONTRACT.md`, `handoff/ATOM_AGENT_PROTOCOL.json` |
| P-SCXML | W3C, [SCXML Recommendation](https://www.w3.org/TR/scxml/), state/event/guard and hierarchical control; consulted 2026-10-24 |
| P-UNICODE | Unicode Consortium, [UAX #15](https://www.unicode.org/reports/tr15/), canonical and compatibility normalization; consulted 2026-10-24; implementations must pin their actual Unicode version |
| P-MSC | Mathematical Reviews / zbMATH, [MSC2020](https://msc2020.org/), coverage taxonomy and published reuse terms; consulted 2026-10-24 |
| P-ACM | ACM, [Computing Classification System](https://www.acm.org/publications/class-2012), coverage reference; direct fetch returned 403 in this authoring session, so no complete local classification or successful import is claimed |
