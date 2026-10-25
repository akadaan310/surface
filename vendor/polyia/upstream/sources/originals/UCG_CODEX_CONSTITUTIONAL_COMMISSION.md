# UCG — UNIVERSAL COMPUTATIONAL GRAMMAR · CONSTITUTIONAL CODEX COMMISSION (GOD SEED) v0.1

**Program:** Substrate University research program · Computational Grammar Theory (CGT) · Grammar in Numbers (GIN)
**Commissioner:** Abed Kadaan (sole human owner and authority)
**Design and seed research:** Abed × Claude (this package: `ucg/`, `docs/UCG_FOUNDATIONS.md`, `results/`), building on PolyIA (Abed × 7u), Plicastratum, Relational Generativity, Q-Strings/G-ships, TRE/TREE, Chemistratum, WAZNOMIA, PILLAR9, Ingram and HOMELESS Realms
**Status:** **EXECUTION AUTHORIZED** for local, non-destructive implementation in an isolated worktree. Separate explicit owner authorization is required for: remote repository writes, public pushes, deployments, credentials, paid services, new network hosts, and edits to any existing repository.
**Edition:** 23 October 2026. Source-and-test-driven. The seed numbers in this document were produced by `ucg/` and sealed in `results/proleptic_ledger.jsonl`; Codex must reproduce them before extending them.

---

## MANDATE, hierarchy and execution standard

Build **UCG**: a science of grammars, implemented as an executable system. It has four parts:
1. A registry of typed alphabets (lettered, geometric, numeric, retial, phonetic).
2. Grammars and in-grammars over those alphabets, with denotations and witnesses.
3. A **generator of generators** that emits, for any admitted subject (e.g. one integration method), a *compiler form* (typed IR + lowering) and a *state-machine form* (states, guards, receipts) that can be run, tested and composed.
4. A **proleptic laboratory** in which every grammar predicts *before* its witness is opened.

The first subjects are fixed by this commission, in this order:
- the periodic table as a lettered alphabet;
- organic forms as a geometric alphabet;
- inorganic and biochemical process grammars;
- chemical nomenclature as executable language (IUPAC, Greek/Latin morphemes, with phonetic forms);
- the **common mathematics** from school algebra to algebraic topology.

Do **not** build a general LLM, a chatbot wrapper, or a JSON-operation interpreter. An LLM may be a *proposal source* for candidate rules; it is **never** a source of truth, execution authority, missing facts or witnesses. Do not import a computer-algebra system or a chemistry toolkit as the engine. sympy, RDKit, OPSIN, Lean/Mathlib, OEIS and datasets are **witnesses**: they are consulted after sealing, never before.

**Five execution absolutes.**
1. Seal before witness.
2. Refusal is typed output, never silence or fabrication.
3. Every artifact is content-addressed and replayable.
4. Every claim carries an epistemic label.
5. No mutation outside the worktree without the owner's contemporaneous authorization.

## Required outputs and canonical worktree

```
ucg/
  core/            # alphabets, words, grammars, in-grammars, denotations, witnesses, ledger, PIR
  alphabets/       # periodic/, forms/, numerals/, phonetic/, retial/
  grammars/        # chem_covalent/, chem_ionic/, rings/, trees/, nomenclature/, algebra/, calculus/,
                   # linalg/, ode/, groups/, topology/  (each: grammar, in-grammar, generator, checker, tests)
  machines/        # generated state-machine forms (one per method), with receipts
  compilers/       # generated compiler forms: typed IR -> lowering -> executable
  genesis/         # the generator-of-generators (meta-grammar -> {compiler form, state-machine form})
  proleptics/      # sealing, witness adapters, metrics, account of misses/gaps, re-seal protocol
  witnesses/       # adapters: OEIS, RDKit, sympy, OPSIN, Lean/Mathlib, QM9/GDB, PubChem (if authorized)
  concierge/       # problem intake -> classify -> resolve -> assemble -> verify -> emit machine
  bridges/         # PURL, SubstrateIO, CGT, GIN, SNAD, Q-Strings, TRE, PolyIA, PILLAR9, Ingram, Realms
  cli/             # ucg <verb> ...   (local only)
  tests/           # unit, property, metamorphic, mutation, proleptic replay, adversarial
  docs/            # this commission, foundations, ADRs, epistemic register, experiment register
  evidence/        # EVIDENCE/{section_id}.json + hashes
  sources.lock     # pinned commits, dataset hashes, package hashes
```

## The harness: UCG-HARNESS/0.2 (state machine for Codex itself)

`H = (S, E, δ, s0, F, G, L)` with `s0 = PREFLIGHT` and `F = {RELEASE_CANDIDATE}` (a milestone, not production). Transitions are guarded by **evidence receipts**. `L` is an append-only, hash-chained event log. Source trust, system capability and evidential confidence are separate dimensions and are never merged into one score.

| State | Required work | Guard (receipt kind) to advance |
|---|---|---|
| PREFLIGHT | Inspect host (CPU/RAM/disk/OS/Python/Node), network allowlist, package-index reachability; create isolated worktree | `environment-audit` |
| INVENTORY | Pin all source repos and packets (commit/tree SHA, file SHA-256), list missing sources honestly | `source-ledger` |
| REPRODUCE | Re-run the seed package `ucg/` (17 tests, E01–E05) and match every sealed number in §R below | `seed-reproduction` |
| FORMALIZE | Write the typed core (Alphabet, Word, Grammar, InGrammar, Denotation, Witness, Machine, PIR) with laws and negative tests | `law-and-negative-tests` |
| GENERATE | Build the generator-of-generators; emit at least the method machines of Part X | `generated-machines` |
| IMPLEMENT | Implement subjects Parts V–XIII to their acceptance witnesses | `subject-acceptance` |
| PROLEPT | Run every subject through seal → witness → account; re-seal witness-informed amendments | `proleptic-ledger` |
| VERIFY | Property, metamorphic, mutation and adversarial tests; independent witness for each pillar | `verification-report` |
| ASSEMBLE | Concierge, CLI, bridges, docs; Substrate University export **as data only** | `integration-and-roundtrip` |
| BENCHMARK | Baselines (sympy, RDKit, OPSIN, Lean), timing, coverage, false-admission rates | `benchmark-and-counterexamples` |
| RELEASE_CANDIDATE | Freeze versions, SBOM, manifests; await owner approval | terminal until separately authorized |

**Receipt law.** `receipt = (kind, stage, passed, commands[], stdout_sha256, artifact_paths[], artifact_sha256[], tests{run, passed, failed}, failures[], environment, parent_event_hash)`. The harness **recomputes** every artifact hash from the bytes on disk and re-runs the declared commands for the `seed-reproduction`, `verification-report` and `proleptic-ledger` kinds. A syntactically valid digest is not evidence. This strengthens PolyIA's prototype gate, which checked digest format only. A failed guard leaves the state unchanged and appends a failure receipt. Negative evidence is never deleted. Returning to an earlier stage requires a new version and a logged reason.

**Evidence protocol.** For each section below, write `evidence/{§id}.json` with `status ∈ {PASS, FAIL, BLOCKED, NOT_RUN}`, `source_sha`, `commands`, `results`, `environment`, `artifact_hashes`, `known_risks`, `next_gate`. The existence of a file is not a pass. Never fill a field with an invented output.

## The atom: Grammar Unit Card (GUC)

Every grammar admitted to UCG is one card. Card fields are immutable per version:

```
GUC = { id (content hash), name, version, subject, epistemic ∈ {established, house, conjecture, application, mythology},
        alphabet: {kind ∈ lettered|geometric|numeric|retial|phonetic, letters|generator, coordinates, symmetry_group},
        grammar: {formalism ∈ regular|CFG|graph-grammar|rewrite|tree|attribute, rules[], start, admissibility checker},
        ingrammar: {refusals[], learned_from_witness?, scope, grade},
        denotation: {semantic domain, evaluator}, operators[] (typed signatures, costs, effects),
        generator: {enumerator, bounds, seed}, witness_adapters[], proleptic_record[],
        machine_form_ref, compiler_form_ref, tests[], provenance{sources, commits, hashes}, licence }
```

The Substrate University `Topic`/`Definition`/`Source` types and its epistemic vocabulary (`established | house | conjecture | application | mythology`) are the **seed schema**: extend them, do not replace them.

## §R — Seed facts Codex must reproduce before extending (from `results/`)

E01: period 118/118, block 118/118, configurations 98/118 with exactly the 20 named exceptions, valence 33/34 vs RDKit (Sn).
E02: 738 words (≤4 heavy atoms); QM9 recall 48/48; precision 6.5% → 33% with the mined in-grammar; textbook 24/25; 8 real molecules refused by the QM9-learned in-grammar.
E03: alkane counts = A000602 for n = 1..12; Pólya vertex+edge counts 120/618/3536/22668; Hückel 1857/1857 vs RDKit after the cumulene amendment; atlas 21/21.
E04: 17/17 placeholder element names; Z ↔ name bijection on 1..999; 40/40 alkane names and parses.
E05: differentiation 400/400; annihilators 10/10; integration 30/30, 5/5 refusals, 124/150 with 124 verified; Butcher 8/8; groups G0→G2 = A000001 (n ≤ 15); homology 4/4 surfaces over ℚ and F₂.

---

## THE SECTIONS

### Part I — Sovereignty, epistemics and governance

#### §001 — Identity of the system
**Mandate.** UCG is a research system that unifies the *form* of subjects (alphabet, grammar, in-grammar, denotation, witness, machine), not a claim that one grammar generates all truth.
**Acceptance witness.** README and CLI `ucg describe` state the scope and the non-claims verbatim; no document claims a universal theory of everything.

#### §002 — Owner as controlling principal
**Mandate.** Abed authorizes all remote writes, publication, deployment, credentials, spending and edits to existing repositories (Substrate University, PURL, SubstrateIO, CGT, GIN, SNAD, Musa, HOMELESS, PolyIA, Timeless).
**Acceptance witness.** An automated test proves that no code path performs `git push`, a network write, or an edit outside the worktree without an owner-signed authorization file.

#### §003 — Supremacy of immutable sources
**Mandate.** Attached packets and cloned repos are read-only inputs, preserved byte for byte and recorded with SHA-256.
**Acceptance witness.** `sources.lock` lists every input with its hash. A re-hash at release matches.

#### §004 — Epistemic labels everywhere
**Mandate.** Every card, claim, result and UI string carries one label: established (cited), house, conjecture, application or mythology. Measured results also carry `[M]` with an experiment id.
**Acceptance witness.** A linter fails the build on any unlabeled claim in docs, cards or CLI output.

#### §005 — Novelty discipline
**Mandate.** A known result is cited, never renamed as new. A new composition is not a new theorem without a statement and proof. Simulated is not physical.
**Acceptance witness.** Each "house" item lists its nearest prior art. The novelty register has a `checked_against` field per entry.

#### §006 — The LLM boundary
**Mandate.** LLM output may enter only as a *proposal* card with label `proposal` and no execution authority. It is never a witness.
**Acceptance witness.** A type-level test: functions that accept `Witness` reject objects with provenance `llm`.

#### §007 — Witness tools are not engines
**Mandate.** sympy, RDKit, OPSIN, Lean, OEIS and datasets are called only by `witnesses/` adapters, after sealing.
**Acceptance witness.** A static import check: no module under `grammars/`, `genesis/` or `machines/` imports a witness library.

#### §008 — Substrate University content boundary
**Mandate.** The Substrate University repository's agent rules govern its content. No religious, scriptural or Arabic-language subject material, and no cross-session AI identity research, enters that repository. WAZNOMIA and Arabic Timeless remain outside the university registry and are reached by bridge contracts only.
**Acceptance witness.** The SU export validator rejects any card whose subject, text or sources fall in those categories. Bridge cards live in `bridges/timeless/`.

#### §009 — Division registry lock
**Mandate.** Preserve the six University divisions and 62 topic IDs; UCG maps into them and does not instantiate new divisions (VII/VIII/IX remain as their owners defined them).
**Acceptance witness.** The crosswalk file maps every UCG subject to one or more existing topic IDs, or marks it `unmapped`. A test asserts that the division count is 6 and the topic count is 62.

#### §010 — Continuity and versioning
**Mandate.** Every card, machine and compiler form is versioned, and a new version never erases an old one.
**Acceptance witness.** Supersession is recorded with `supersedes`. Old versions remain resolvable.

#### §011 — Terminology precision
**Mandate.** Words with established meanings (quantum, entanglement, manifold, sheaf, holonomy, universal, complete) are used only in their established sense, or with the house label and a definition.
**Acceptance witness.** The glossary lists every such term with a status. A doc linter flags uses outside the glossary.

#### §012 — Termination by acceptance
**Mandate.** Codex stops at real acceptance or a declared block, never at an arbitrary budget, and reports what does not work.
**Acceptance witness.** The final SUMMARY lists PASS/FAIL/BLOCKED/NOT_RUN per section with evidence links.

### Part II — Ontology of grammars

#### §013 — Alphabet kinds
**Mandate.** Implement `Alphabet` with kinds `lettered`, `geometric`, `numeric`, `retial` (graph-indexed), `phonetic` and `product`, each with letters (or a generator), coordinates and a symmetry group.
**Acceptance witness.** Unit tests instantiate one alphabet of each kind; product alphabets compose; symmetry groups act correctly on words.

#### §014 — Words of any rank
**Mandate.** Words are maps from a finite index structure (ℤʳ box, graph, multiset, cyclic order) to letters, following Plicastratum ranks punctum/simplex/duplex/triplex/retial.
**Acceptance witness.** Round-trip serialization for each rank, with canonical forms under the declared symmetry.

#### §015 — Grammar formalisms
**Mandate.** Support regular (DFA/NFA), context-free (with CYK/Earley), graph grammars, term-rewriting systems, tree grammars and attribute grammars behind one `Grammar` interface: `admits(word) → (bool, diagnostics)`.
**Acceptance witness.** Each formalism passes a positive and a negative test suite, and diagnostics name the failed rule.

#### §016 — In-grammar as first-class object
**Mandate.** An `InGrammar` is a scoped set of refusals with provenance: hand-declared, learned-from-witness, or derived. Scoped means it is never "everything outside the grammar".
**Acceptance witness.** Every refusal has `scope`, `source`, `grade` and `learned_from`. The E02 refusals are reproduced and labelled `learned_from: QM9`.

#### §017 — The tetrad (Form, InForm, Grammar, Witness)
**Mandate.** Adopt Chemistratum's tetrad as the record shape for every subject result.
**Acceptance witness.** The schema validator requires all four fields; `InForm` may be `unknown` but never omitted.

#### §018 — Denotation
**Mandate.** Every grammar declares a semantic domain and an evaluator from admitted words to values, structures or behaviours, kept separate from syntax and execution (CGT-PROP-002).
**Acceptance witness.** For each subject, one test shows admissible-but-unrealizable and one shows realizable-but-expensive, where applicable.

#### §019 — Operators and costs
**Mandate.** Operators carry signatures, preconditions, effects and cost models (CGT-DEF-005).
**Acceptance witness.** The cost of a run is recorded and is reproducible within a declared tolerance.

#### §020 — Folds and towers
**Mandate.** Implement Plicastratum explicate/implicate/promote on every alphabet. A certified recurring path becomes a letter, and unfolding is always available.
**Acceptance witness.** Promoted letters unfold to level-0 words with equal hashes, tested on chemistry (functional groups as letters) and calculus (rule chains as letters).

#### §021 — Closure classes
**Mandate.** Classify iteration of every operator as complete (cyclic), severed (nilpotent/terminating), open (drifting) or projectively periodic, as measured for D in E05.
**Acceptance witness.** `ucg orbit <operator> <word>` reproduces E05's classes, and is applied to at least three other operators (rename, fold, reduce).

#### §022 — Image and kernel failures as universal refusals
**Mandate.** Every converse operation reports *image failure* (no preimage) or *kernel failure* (non-unique preimage) per GIN-THM-001.
**Acceptance witness.** Tests cover division, linear systems, reverse dictionary lookup, name→structure and unfold, each with both failure kinds.

#### §023 — Equality criteria are explicit
**Mandate.** Equality is always qualified: syntactic, canonical-form, extensional (numeric witness on generic points), proof-certified or isomorphism-invariant.
**Acceptance witness.** No `==` on words or terms outside `core/equality.py`. Each use names its criterion.

#### §024 — Charts and atlases of alphabets
**Mandate.** Different notations for the same subject (SMILES/InChI/name/drawing; Leibniz/Lagrange/Newton notation) are charts with explicit transition maps and declared loss.
**Acceptance witness.** The round trip through every chart pair preserves the declared invariants. Losses are listed.

#### §025 — Content addressing
**Mandate.** Every card, word, machine and result has a content hash with a domain separator (TRE `digest(tag, value)`).
**Acceptance witness.** Changing one byte changes the id. Identical content in different domains yields different ids.

#### §026 — Q-String edges between subjects
**Mandate.** Cross-subject relations (e.g. "Hückel's 4k+2 ↔ cyclic group order") are Q-Strings with type, grammar, witness and grade. A lookup is not an inference.
**Acceptance witness.** Every cross-edge carries a witness or the grade `proposed`. A test refuses an edge with no grammar.

### Part III — Proleptics (seal before witness)

#### §027 — The protocol
**Mandate.** Implement GENERATE → SEAL → WITNESS → RECOGNISE → ACCOUNT as the only path by which a grammar earns `[M]` results.
**Acceptance witness.** The ledger shows SEAL before WITNESS for every experiment. A test attempting WITNESS without SEAL is refused.

#### §028 — Declared generator reads
**Mandate.** Each generator declares the data it may read. The harness enforces this with a sandboxed filesystem view during GENERATE.
**Acceptance witness.** A generator that tries to open a witness file during GENERATE fails with a typed error. The test is included.

#### §029 — Witness-informed amendments
**Mandate.** An amendment made after seeing a witness is re-sealed with label `witness-informed`, and its effect is measured on a *held-out* witness.
**Acceptance witness.** The Hückel cumulene amendment and the group productions G1/G2 are re-run on held-out cases, and the results are recorded.

#### §030 — Misses and gaps are data
**Mandate.** Predicted-but-unwitnessed items become candidate in-grammar. Witnessed-but-unpredicted items become grammar deficits. Both are stored and queryable.
**Acceptance witness.** `ucg account E02` prints both lists with motifs and counts.

#### §031 — Witness bias rule (UCG-W1)
**Mandate.** An in-grammar learned from one witness is never promoted to "impossible" without a second, independent witness.
**Acceptance witness.** E02's QM9-learned refusals are graded `witness-specific`. The textbook witness shows the 8 contradictions.

#### §032 — Wrong-witness handling
**Mandate.** A witness can be wrong (E03's bracelet formula). Witness models are versioned, and a disagreement triggers a witness audit as well as a grammar audit.
**Acceptance witness.** The E03 record shows `naive_bracelet` superseded by `polya_vertex_edge`, with the reason.

#### §033 — Statistical honesty
**Mandate.** Report precision, recall, confusion and confidence intervals where sampling is involved, and never only the favourable metric.
**Acceptance witness.** Every metrics block has both error types and the denominators.

#### §034 — Replay
**Mandate.** Any WITNESS entry can be replayed from pinned sources to identical metrics.
**Acceptance witness.** `ucg replay <ledger-entry>` reproduces the metrics byte for byte on a clean checkout.

### Part IV — State machines and harnesses for subjects

#### §035 — Machine form
**Mandate.** A machine form is `(states, alphabet of events, guarded transitions, receipts, refusal states, budgets)`, with terminal states EMIT and REFUSE(reason).
**Acceptance witness.** A schema plus validator; every generated machine validates; unreachable states are reported.

#### §036 — VERIFY state is mandatory
**Mandate.** Every machine that emits a result passes through VERIFY, an independent check (e.g. differentiate an antiderivative).
**Acceptance witness.** Mutation test: disabling VERIFY makes the test suite fail.

#### §037 — Budgets
**Mandate.** Depth, step, time and memory budgets are declared per machine, and exceeding one is REFUSE(budget).
**Acceptance witness.** Adversarial inputs hit budget refusals, never hangs.

#### §038 — Traces as words
**Mandate.** A run's trace is a word over the machine's state alphabet and is stored with the result.
**Acceptance witness.** Traces are minable: Plicastratum `mine` promotes recurring trace segments to letters (e.g. "PARTS-cycle-close").

#### §039 — Composition
**Mandate.** Machines compose by typed ports (PolyIA atoms). The external boundary hides internals.
**Acceptance witness.** Composing USUB inside PARTS yields a valid machine whose trace includes both.

#### §040 — Determinism
**Mandate.** Same input, grammar version, seed and policy yield the same trace and result.
**Acceptance witness.** Running twice on 1,000 inputs gives identical hashes.

#### §041 — Harness for Codex itself
**Mandate.** Codex's own progress uses UCG-HARNESS/0.2 above, with real byte-level receipt verification.
**Acceptance witness.** Advancing with a fabricated receipt fails. Advancing with real artifacts succeeds.

#### §042 — Failure receipts
**Mandate.** Failures are receipts with diagnostics, and never erased.
**Acceptance witness.** The ledger contains at least one failure per stage that had one, linked to its resolution.

#### §043 — Human-readable projection
**Mandate.** Every machine renders as DOT and HTML (PolyIA style) for inspection.
**Acceptance witness.** Rendered artifacts exist for all generated machines, with hashes.

#### §044 — Machine registry
**Mandate.** All machines are registered with id, version, subject, ports and tests.
**Acceptance witness.** `ucg machines list` matches the files on disk. An orphan check passes.

### Part V — The lettered alphabet: the periodic table

#### §045 — Generator reads Z only
**Mandate.** Element coordinates are derived from Z by the aufbau grammar. Printed tables are witnesses.
**Acceptance witness.** Reproduces E01: 118/118 period and block; 98/118 configurations with the 20 named exceptions.

#### §046 — The exceptions as in-grammar
**Mandate.** Model the 20 configuration exceptions as an explicit in-grammar (half-filled/filled subshell preference, relativistic effects), each with a cited reason.
**Acceptance witness.** With the in-grammar on, 118/118. Each exception's rule is cited, and no rule is a lookup keyed by Z alone without justification.

#### §047 — Valence grammar
**Mandate.** Octet valence, expanded octet (period ≥ 3), ionic charges and oxidation-state sets are derived from position.
**Acceptance witness.** Reproduces E01's 33/34 vs RDKit. Adds an inert-pair rule and measures its effect on held-out p-block elements.

#### §048 — Periodic trends as order relations
**Mandate.** Electronegativity, atomic radius and ionization energy are modelled as partial orders induced by position (left→right, bottom→top), and tested against the measured values in the table.
**Acceptance witness.** Report the fraction of element pairs whose order is predicted correctly for each trend, with exceptions listed.

#### §049 — Binary compound grammar (ionic)
**Mandate.** Words AxBy are admitted by charge balance with minimal integers. Ordering follows the IUPAC/Hill convention (electropositive first).
**Acceptance witness.** Sealed predictions for all main-group binary pairs are witnessed against an authorized crystal/compound database (e.g. Materials Project or ICSD statistics) once access is granted. Until then, the status is BLOCKED, with a textbook mini-witness.

#### §050 — Covalent word grammar
**Mandate.** Molecules are connected bond multigraphs with valence admissibility. Enumeration is bounded and canonical.
**Acceptance witness.** Reproduces E02: 738 words; QM9 recall 48/48. Extends to 5–7 heavy atoms with recall measured.

#### §051 — Water as the first word
**Mandate.** The system must *derive* H₂O as the minimal admissible word over {H, O}, and VSEPR geometry from electron-pair counts (steric number 4 → bent).
**Acceptance witness.** Predicted bond angle class (<109.5°) is sealed, then witnessed against experimental angles for H₂O, NH₃ and CH₄, or a conformer-embedding witness.

#### §052 — Orbital grammar (s, p, d, f)
**Mandate.** Hybridization and bonding capacity are expressed as a grammar over orbital letters, with explicit limits (no fake quantum chemistry).
**Acceptance witness.** Hybridization labels for all atoms in the E02 corpus are predicted and compared to a witness perception (RDKit hybridization).

#### §053 — Element symbol custody
**Mandate.** Record symbol–name mismatches (Na/natrium, K/kalium, Fe/ferrum, Ag/argentum, Au/aurum, Pb/plumbum, Hg/hydrargyrum, Sn/stannum, Sb/stibium, W/wolfram), with language and grade.
**Acceptance witness.** Every element has a name-origin card with source and grade. Unresolved etymologies are labelled unresolved.

#### §054 — Systematic element names
**Mandate.** Implement the IUPAC 1978 root grammar (nil…enn + ium) as a bijection.
**Acceptance witness.** Reproduces E04: 17/17 placeholders, and a round trip on Z = 1..999.

### Part VI — The geometric alphabet: organic forms

#### §055 — Forms before bonds
**Mandate.** Rings, chains and junctions are first represented as shapes with ports and symmetry groups, without chemistry. Chemistry enters later, as admissibility.
**Acceptance witness.** The form registry has polygons (n = 3..8), chains, stars and fused/spiro/bridged connectors, each with its group.

#### §056 — Canonical forms under symmetry
**Mandate.** Canonicalize ring words under Dₙ and trees by AHU code at the centre.
**Acceptance witness.** Reproduces E03: alkane counts = A000602 (n ≤ 12), Pólya counts 120/618/3536/22668.

#### §057 — Resonance as orbit identification
**Mandate.** Kekulé structures in one Dₙ orbit are one form, declared as a fold with information loss stated.
**Acceptance witness.** Benzene's two Kekulé words are one canonical form. The fold record states what is lost (bond localization).

#### §058 — Aromaticity grammar
**Mandate.** Hückel 4k+2 over fully conjugated planar monocycles, with the cumulene rule, plus an explicit list of known exceptions (e.g. Möbius, large annulenes).
**Acceptance witness.** Reproduces 1857/1857 vs RDKit and 21/21 on the atlas. Extends to fused systems with a declared method and a measured agreement.

#### §059 — Fused, spiro, bridged grammars
**Mandate.** Composition operators on forms: edge-sharing (fused), vertex-sharing (spiro), path-sharing (bridged), bond-joined (assembly), as in Chemistratum's rows.
**Acceptance witness.** Every Chemistratum `multi` entry is generated by the composition grammar from monocycle letters, with its canonical SMILES witnessed.

#### §060 — Substituent grammar
**Mandate.** Functional groups are promoted letters (Plicastratum) with ports. Substitution is a typed operation.
**Acceptance witness.** 20 common functional groups are promoted, and unfolding reproduces their atom graphs.

#### §061 — Isomer enumeration with symmetry accounting
**Mandate.** Count structural isomers by Pólya enumeration and by explicit generation, and compare.
**Acceptance witness.** Agreement for alkyl radicals (A000598) and alkanols, with any discrepancy explained.

#### §062 — Stereochemistry as a further alphabet
**Mandate.** Add chirality and E/Z as letters over the 3D embedding group, declared separately from constitution.
**Acceptance witness.** Stereoisomer counts for test molecules match a witness (RDKit EnumerateStereoisomers).

#### §063 — Strain and stability as in-grammar
**Mandate.** Small-ring strain, anti-Bredt, cumulene and heteroatom–heteroatom refusals are scoped in-grammar with sources, separating "unstable" from "impossible".
**Acceptance witness.** Each refusal is graded (impossible / unstable / filtered-by-witness). The E02 refusals are relabelled accordingly.

#### §064 — OCSR boundary
**Mandate.** Image-to-structure recognition is a separate, later lane with its own witnesses; the form alphabet does not depend on it.
**Acceptance witness.** The OCSR lane is BLOCKED or implemented with its own benchmark, and is never mixed into E02/E03 metrics.

#### §065 — Form ↔ name ↔ graph charts
**Mandate.** Transition maps between drawing, graph, SMILES, InChI and IUPAC name.
**Acceptance witness.** Round trips on the atlas preserve constitution. OPSIN is a name→structure witness when installed.

#### §066 — Organic structural table
**Mandate.** Regenerate Chemistratum's table from the grammar (family × ring axis), with empty cells meaning "not admitted yet".
**Acceptance witness.** Every atlas entry is reproduced by generation. New cells proposed by the grammar are sealed before any lookup.

### Part VII — Inorganic, biochemical and process grammars

#### §067 — Inorganic structure grammar
**Mandate.** Ionic lattices and coordination complexes are grammars of coordination number and charge, not carbon skeletons.
**Acceptance witness.** Coordination-number predictions by radius ratio are sealed, then witnessed on an authorized structure set. Otherwise BLOCKED.

#### §068 — Reaction grammar
**Mandate.** Reactions are rewrite rules on molecular graphs that conserve atoms and charge, with typed preconditions.
**Acceptance witness.** Conservation laws are tested on 100 rewrites. Inadmissible rewrites are refused with the violated law.

#### §069 — Biochemical process grammar
**Mandate.** Biochemistry is modelled as process grammars (pathways as words of reactions; polymers as words over monomer alphabets: nucleotides, amino acids).
**Acceptance witness.** The codon table is implemented as a 64→21 map with declared loss (kernel failure = degeneracy). A protein → DNA converse reports kernel failure with the fibre size.

#### §070 — Stoichiometry as linear algebra
**Mandate.** Balancing is the nullspace of the composition matrix, with image/kernel failure for impossible or under-determined equations.
**Acceptance witness.** 50 textbook equations are balanced. Impossible ones are refused as image failure, and multi-solution ones as kernel failure with the nullity.

#### §071 — Energy as denotation (optional)
**Mandate.** Thermochemical denotations come only from cited data (e.g. G4MP2 values in the witness set). They are never invented.
**Acceptance witness.** Any energy shown carries its dataset id and hash.

#### §072 — Chemistry safety boundary
**Mandate.** The system does not generate synthesis routes, procedures or optimization guidance for hazardous, toxic, explosive or controlled substances. Reaction grammars stay at the level of textbook structural rewriting.
**Acceptance witness.** A refusal test suite covers hazardous-route requests. The policy is documented in `docs/SAFETY.md`.

### Part VIII — Nomenclature, phonetics and language bridges

#### §073 — Names are programs
**Mandate.** Nomenclatures are executable grammars: name → structure and structure → name, with normal forms.
**Acceptance witness.** Reproduces E04's 40/40. Extends to cycloalkanes, alkenes, alcohols and ketones with OPSIN as witness.

#### §074 — Normal form versus admissible
**Mandate.** Distinguish *admissible but not normal* names ("2-ethylpentane") from inadmissible ones.
**Acceptance witness.** The parser returns the normal form and the rule that was violated.

#### §075 — Morpheme operators with custody
**Mandate.** Every morpheme (meth-, eth-, prop-, but-, pent-…, -ane/-ene/-yne/-ol/-one, di-/tri-) is an operator card with language of origin, function and grade.
**Acceptance witness.** Mixed-origin cases (non-, undec-) are flagged. No etymology is invented, and unresolved ones stay unresolved.

#### §076 — Phonetic forms
**Mandate.** Names have spoken forms in IPA as a separate chart. Symbols (O) are non-phonetic letters; names (oxygen) are phonetic words. The map between them is recorded.
**Acceptance witness.** IPA entries come only from cited sources (e.g. Wiktionary dumps with licence), with a coverage report.

#### §077 — Greek and Latin determinations
**Mandate.** Import the Determinations II analysis (Greek composes, Latin orbits) as operator inventories with grades.
**Acceptance witness.** Each operator has an example name in chemistry or mathematics that decomposes correctly.

#### §078 — WAZNOMIA bridge
**Mandate.** The Arabic sarf/rasm determinations stay in Timeless/WAZNOMIA. UCG reaches them through a typed bridge whose cards never enter the Substrate University export (§008).
**Acceptance witness.** A bridge contract test shows a round trip of one determination through the bridge. The SU export validator rejects the bridge cards.

#### §079 — Mathematical nomenclature
**Mandate.** Mathematical terms (integer, calculus, sine, algebra, topology) get name-origin cards with chains of custody (e.g. jyā → jīb → sinus), graded.
**Acceptance witness.** 50 cards with sources. Loss events in the chain are marked.

#### §080 — Notation grammars
**Mandate.** Mathematical notations (infix, Leibniz dy/dx, Lagrange f′, Newton ẏ, ∫ forms) are charts of one term language.
**Acceptance witness.** A parse/print round trip across notations for 200 expressions is witnessed by a CAS.

#### §081 — Nomenclature of grammars themselves
**Mandate.** Name UCG's own objects with the fold/strata conventions (Plicastratum) and record them as house terms.
**Acceptance witness.** The glossary lists every house term with definition, status and nearest established term.

#### §082 — Multilingual extension interface
**Mandate.** Other naming systems (Sanskrit Pāṇinian roots, Chinese radical+phonetic) plug in via the same operator-card interface. They are not implemented without validated corpora.
**Acceptance witness.** The interface test uses a toy grammar; the real packs are marked NOT_RUN until corpora are pinned.

### Part IX — Common mathematics: algebra and functions

#### §083 — The common-math map
**Mandate.** Define *common math* as the standard undergraduate core through algebraic topology (school algebra, precalculus, calculus I–III, linear algebra, ODE, discrete math, abstract algebra, real analysis, topology, algebraic topology). Map each pillar to cards.
**Acceptance witness.** A pillar map covering every topic in a cited standard curriculum (e.g. a published syllabus), with coverage percentages.

#### §084 — Term language
**Mandate.** One typed term language for expressions (numbers, variables, functions, operators) with a canonical form and partial normalization.
**Acceptance witness.** Parsing and printing are inverse on 10,000 random terms. The normalizer is idempotent.

#### §085 — Polynomial grammar
**Mandate.** Polynomials over ℤ, ℚ and 𝔽ₚ, with division, gcd, factoring machines (rational root theorem, Berlekamp for 𝔽ₚ, Zassenhaus over ℤ as a later stage).
**Acceptance witness.** Factorizations are verified by multiplication. Irreducibility is witnessed by a CAS.

#### §086 — Functions and their classes
**Mandate.** Classify functions as polynomial, rational, algebraic, elementary transcendental, exponential polynomial or special, with closure properties under +, ×, ∘, D and ∫.
**Acceptance witness.** A closure table is produced by running the machines on generated corpora, matching known theory (e.g. D preserves algebraic, ∫ may leave it).

#### §087 — Equations as machines
**Mandate.** Linear, quadratic, polynomial and transcendental equation solving as machines with exact and numeric branches and typed refusals.
**Acceptance witness.** Solution sets are verified by substitution. "No real solution" is an image failure.

#### §088 — Inequalities and intervals
**Mandate.** Interval arithmetic and sign charts as grammars, with soundness (enclosure) guaranteed.
**Acceptance witness.** A property test: the true value always lies within the computed enclosure.

#### §089 — Euclidean function spaces
**Mandate.** Represent functions as vectors (bases, inner products, projection) for approximation (polynomial, Fourier), with declared loss.
**Acceptance witness.** Projection error decreases with basis size on test functions, as theory predicts.

#### §090 — Identities as rewrite theories
**Mandate.** Trigonometric, exponential and logarithmic identities as oriented rewrite rules, with termination and confluence checks where possible.
**Acceptance witness.** Critical-pair analysis is run. Non-confluent pairs are listed as in-grammar, not hidden.

### Part X — Calculus

#### §091 — Differentiation rewrite system
**Mandate.** D as rules (linearity, product, quotient, chain, power, exp, log, trig, inverse trig), with derivation words.
**Acceptance witness.** Reproduces E05's 400/400 vs sympy, and extends to 10,000 random terms.

#### §092 — Higher derivatives: orbit grammar
**Mandate.** Classify D-orbits (complete, severed, open, projective). For finite spans, recover the characteristic word.
**Acceptance witness.** Reproduces 10/10 annihilators, then extends to 200 exponential polynomials with recovery rate measured.

#### §093 — Leibniz and Faà di Bruno patterns
**Mandate.** Generate n-th derivatives of products (binomial/Pascal grammar) and of compositions (set partitions; Bell numbers), and witness the term counts.
**Acceptance witness.** Term counts match binomial coefficients, and Faà di Bruno counts match integer partitions per n.

#### §094 — Limits as machines
**Mandate.** Limit evaluation machines (direct substitution, algebraic simplification, L'Hôpital with a guard on indeterminate forms, series), with typed refusals.
**Acceptance witness.** 0/0 and ∞/∞ are classified before L'Hôpital applies. Results are witnessed by a CAS.

#### §095 — One machine per integration method
**Mandate.** The generator emits a distinct machine for each method: table, linearity, u-substitution, by parts (LIATE, tabular, cycle-closing), partial fractions (linear, repeated, irreducible quadratic), trig identities, trig substitution, Weierstrass t-substitution, rationalizing substitution, reduction formulae.
**Acceptance witness.** Each machine has its own tests. E05 is reproduced (30/30, 5/5 refusals, 124/150 verified) and coverage per method is reported.

#### §096 — The integration concierge
**Mandate.** Classify an integrand by its function alphabet and route it to methods in an order learned from traces, never guessed.
**Acceptance witness.** Routing improves solve rate or step count on a held-out set versus fixed order, with the improvement sealed before measurement.

#### §097 — Liouville boundary
**Mandate.** Refuse non-elementary integrals with reason, and implement the Risch decision procedure for the transcendental-elementary case as a later stage.
**Acceptance witness.** All classical non-elementary examples are refused. Once Risch exists, its decisions match a CAS on a test corpus.

#### §098 — Transcendental impact study
**Mandate.** Measure the cost of trigonometric and exponential letters in differentiation and integration (states, depth, failure rate) by function class.
**Acceptance witness.** Reproduces E05 (trig ≈ 2.8× states, ≈ 3× failure), then extends with confidence intervals.

#### §099 — Definite integrals and numerics
**Mandate.** Quadrature as stepwise machines (trapezoid, Simpson, Gauss–Legendre, adaptive), with error orders as grammar predictions.
**Acceptance witness.** Predicted error orders match measured convergence slopes.

#### §100 — Series
**Mandate.** Taylor/Maclaurin generation and convergence tests (ratio, root, comparison) as machines.
**Acceptance witness.** Radius of convergence predictions match a CAS. Inconclusive tests return a typed "inconclusive".

#### §101 — Multivariable calculus
**Mandate.** Partial derivatives, gradient, divergence, curl, Jacobian, and iterated integrals with order-of-integration machines.
**Acceptance witness.** Identities div∘curl = 0 and curl∘grad = 0 hold symbolically on generated fields.

#### §102 — Vector fields as words
**Mandate.** Discretized vector fields and their flows as retial words, for visualization in Substrate University (data only).
**Acceptance witness.** Flows computed by RK4 match analytic solutions on linear fields within declared error.

### Part XI — Linear algebra, ODE and numerical methods

#### §103 — Linear systems machine
**Mandate.** Gauss–Jordan over ℚ and 𝔽ₚ with unique / kernel failure / image failure outputs.
**Acceptance witness.** Reproduces E05's three cases, then runs a property test on 1,000 random systems against a CAS rank.

#### §104 — Decompositions
**Mandate.** LU, QR, eigen (symbolic for small, numeric for large), SVD, with residual witnesses.
**Acceptance witness.** Reconstruction residuals are below tolerance. Symbolic eigenvalues are witnessed by the characteristic polynomial.

#### §105 — Linear operators as grammars
**Mandate.** Matrices as compiled words of moves (Substrate University "Matrix Loom"), with rank–nullity as a law.
**Acceptance witness.** Rank + nullity = n holds on all generated operators.

#### §106 — ODE classification
**Mandate.** Classify ODEs by order, linearity, coefficients and separability, and route to analytic methods (separable, linear first-order, constant-coefficient via characteristic polynomial, undetermined coefficients, variation of parameters).
**Acceptance witness.** Solutions are verified by substitution. The characteristic words from §092 are reused.

#### §107 — Runge–Kutta via Butcher trees
**Mandate.** Order conditions via rooted trees, for any tableau.
**Acceptance witness.** Reproduces 8/8 (including the broken RK4), then extends to embedded pairs (Dormand–Prince) with order checks.

#### §108 — Stepwise numerical methods as machines
**Mandate.** Euler, RK, multistep (Adams), BDF and adaptive stepping as machines whose traces are the "stepwise operations" (the MATLAB-style view).
**Acceptance witness.** Measured orders match theory. The stiffness detector refuses explicit methods on stiff tests.

#### §109 — Phase portraits
**Mandate.** 2D systems produce direction fields and trajectories as retial words, with a classification of fixed points by Jacobian eigenvalues.
**Acceptance witness.** Classification matches analytic results for 20 linear systems.

#### §110 — Error and stability grammar
**Mandate.** Floating-point behaviour is modelled explicitly (GIN machine model): error bounds and condition numbers are first-class outputs.
**Acceptance witness.** Ill-conditioned systems report condition numbers. The results' error bounds hold empirically.

### Part XII — Abstract algebra

#### §111 — Group construction grammar
**Mandate.** Productions Zₙ, ×, ⋊ (cyclic and general), dicyclic, with Cayley tables and axiom checks.
**Acceptance witness.** Reproduces G0→G2 = A000001 for n ≤ 15, then extends toward n ≤ 31 with a complete isomorphism test (canonical labelling) replacing invariants.

#### §112 — Gap-driven grammar growth
**Mandate.** Grammar extensions are triggered by witnessed gaps (Q₈ → dicyclic; A₄ → general semidirect) and recorded as proleptic amendments.
**Acceptance witness.** The ledger shows each extension with its triggering gap.

#### §113 — Rings and fields
**Mandate.** ℤ/n, polynomial rings, finite fields 𝔽_{pᵏ} as grammars with image/kernel failures (non-invertible elements).
**Acceptance witness.** Field axioms hold for constructed fields. Zero divisors in ℤ/n are classified by kernel failure.

#### §114 — Symmetry groups of forms
**Mandate.** Connect §056 (Dₙ on rings) with §111: chemical form symmetries are groups in the registry.
**Acceptance witness.** The automorphism group of benzene's graph is computed and identified as order 12, isomorphic to D₆.

#### §115 — Representations (introductory)
**Mandate.** Permutation and matrix representations of small groups, with characters for cyclic and dihedral groups.
**Acceptance witness.** Character orthogonality holds numerically for the implemented tables.

#### §116 — Galois (scoped)
**Mandate.** For quadratics, cubics and quartics, solvability by radicals is classified via the discriminant/resolvent machine. Higher degrees are labelled out of scope unless implemented.
**Acceptance witness.** Classifications match a CAS on 100 random polynomials.

### Part XIII — Topology and algebraic topology

#### §117 — Simplicial complexes
**Mandate.** Complexes as words over simplices, with the closure and face laws checked.
**Acceptance witness.** The validator rejects non-closed complexes and accepts the standard surfaces.

#### §118 — Homology machine
**Mandate.** Boundary operators with ∂∂ = 0 as a law, and Betti numbers over ℚ and 𝔽ₚ (Smith normal form over ℤ as a later stage).
**Acceptance witness.** Reproduces S², T², RP², Klein over ℚ and F₂, then adds torsion via SNF (RP²: H₁ = ℤ/2).

#### §119 — Euler characteristic as invariant
**Mandate.** χ is computed two ways (counts and Betti numbers) and must agree.
**Acceptance witness.** Agreement on all generated complexes.

#### §120 — Fundamental group presentations (scoped)
**Mandate.** Generate presentations from 2-complexes (edge-path group), and compute abelianizations to match H₁.
**Acceptance witness.** The abelianization equals H₁ for the four surfaces.

#### §121 — Topology of forms
**Mandate.** Ring systems (fused, spiro, bridged) are complexes. Cycle rank and Betti numbers are chemical invariants.
**Acceptance witness.** Cycle ranks of atlas molecules equal their RDKit SSSR sizes.

#### §122 — Topology of walks and worlds
**Mandate.** Plicastratum holonomy and HOMELESS walk words are connected to H₁ of street complexes, with a declared, testable link (not a metaphor).
**Acceptance witness.** On a synthetic grid with a hole, the holonomy class of closed walks matches H₁ winding.

### Part XIV — The generator of generators

#### §123 — Meta-grammar
**Mandate.** A meta-grammar whose words are GUC cards. The generator produces, from a card, a **state-machine form** and a **compiler form**.
**Acceptance witness.** From the card "integration by parts", the generator emits a machine equivalent (trace-equivalent on a test corpus) to the hand-written E05 PARTS machine.

#### §124 — Compiler form
**Mandate.** A compiler form is `typed IR → lowering → executable` (Python reference first; WASM/native later only after toolchain verification), following PolyIA's PIR and PILLAR9's bytecode discipline.
**Acceptance witness.** The compiled and interpreted versions of three machines agree on 1,000 inputs. Compile time and run time are reported.

#### §125 — Generated machines per subject
**Mandate.** Emit one machine per integration method, per differentiation rule family, per ODE method, per linear-algebra decomposition, per nomenclature direction.
**Acceptance witness.** The machine count and tests are listed. Every generated machine passes the schema and its own tests.

#### §126 — Generative model form
**Mandate.** For each subject, a deterministic generative model (grammar × in-grammar × seed) produces new admissible words, e.g. new integrals with known answers, new molecules, new groups.
**Acceptance witness.** Generated items are admissible and verified. Distribution statistics are reported.

#### §127 — Curriculum generator
**Mandate.** Generate graded exercises for each common-math pillar with answers and solution traces (for Substrate University, as data only).
**Acceptance witness.** 100 exercises per pillar, each with a verified answer and a trace. The difficulty grade is computed from trace length.

#### §128 — Inverse generation
**Mandate.** Generate problems from desired traces (e.g. "an integral requiring USUB then PARTS").
**Acceptance witness.** Produced problems' actual traces match the requested trace in ≥ 95% of cases.

#### §129 — Rule mining from traces
**Mandate.** Mine recurring trace segments and propose new letters/rules (Plicastratum promotion) with proleptic testing.
**Acceptance witness.** At least one mined rule improves a held-out metric, sealed before measurement.

#### §130 — Machine minimization
**Mandate.** Minimize generated automata (Moore/Hopcroft) and report the reduction.
**Acceptance witness.** The minimized machine is equivalent, verified by product construction.

#### §131 — Cross-subject reuse
**Mandate.** Detect machines that are isomorphic across subjects (e.g. cycle-closing in PARTS and periodic D-orbits) and record them as Q-String edges.
**Acceptance witness.** At least two cross-subject isomorphisms are found, each with a witnessing construction.

#### §132 — Generator safety
**Mandate.** Generated machines run only in the sandbox, with budgets and without network or filesystem effects beyond declared outputs.
**Acceptance witness.** A sandbox escape test suite passes.

### Part XV — Classification, concierge and Substrate University

#### §133 — Problem intake
**Mandate.** A concierge parses a problem statement (a structured form, not free LLM interpretation), classifies it to subjects and machines, assembles a composite machine, runs it, verifies and emits.
**Acceptance witness.** 100 mixed problems are routed. Each output includes classification, machine id, trace and verification.

#### §134 — Classifier as grammar
**Mandate.** Problem classification is itself a grammar over feature letters (function alphabet, structure, constraints), learned only with proleptic sealing.
**Acceptance witness.** The confusion matrix is on a held-out set. Misroutes are analysed.

#### §135 — Rapid model generation
**Mandate.** For a new problem class, the generator produces a candidate machine in one command from a card.
**Acceptance witness.** Time from card to tested machine is reported for 5 new classes.

#### §136 — Substrate University export
**Mandate.** Export cards, exercises and machine projections into the SU registry format (Topic, Definition, Source, Example, challenge), respecting §008 and §009. The export is **data only**. No edits to the SU repository without authorization.
**Acceptance witness.** The export validates against SU types. The SU AGENTS.md rules pass. A PR is prepared only after owner approval.

#### §137 — Exhibits
**Mandate.** Propose browser-local exhibits (pure functions in `src/math/` style) for: periodic table from Z, ring bracelets, D-orbits, integration machine traces, homology of surfaces.
**Acceptance witness.** Each exhibit's math module is pure, unit-tested and free of server or model calls.

#### §138 — Books and transcripts
**Mandate.** Machine traces can be typeset as worked solutions for the SU Scriptorium, honestly labelled as computed.
**Acceptance witness.** A sample book shows source, computation and generated text, separated.

### Part XVI — Bridges to the existing research corpus

#### §139 — CGT bridge
**Mandate.** Operational grammars, admissibility languages, product constructions and cost profiles are reused via cgtsdk by adapter, without copying source.
**Acceptance witness.** A UCG machine runs a CGT product construction through the adapter. Licences are recorded.

#### §140 — GIN bridge
**Mandate.** Numerals-as-programs, image/kernel failure and machine arithmetic are imported as cards.
**Acceptance witness.** The division classification tests from GIN pass through UCG's refusal types.

#### §141 — SubstrateIO bridge
**Mandate.** UCG ledgers export as SubstrateIO traces (transitions, projections, provenance).
**Acceptance witness.** A UCG experiment validates under SubstrateIO's `tools.validate`.

#### §142 — PURL bridge
**Mandate.** Cards, machines and results get PURL addresses with manifests. GET is pure; POST requires authorization.
**Acceptance witness.** A local PURL server resolves a card and returns its manifest. Mutation without a grant is refused.

#### §143 — SNAD bridge
**Mandate.** Transitions between notations or charts are recorded as typed transitions with evidence status (observed/derived/hypothesis/interpretation).
**Acceptance witness.** A chart transition (name → structure) is recorded in SNAD's evidence vocabulary.

#### §144 — Q-Strings, TRE, PILLAR9 bridges
**Mandate.** Cross-subject edges as Q-Strings. Tree structures (rooted trees, ASTs, Butcher trees, alkane skeletons) share TRE's tree contracts. PILLAR9 compiles a machine to bytecode as a second backend.
**Acceptance witness.** One rooted-tree type serves Butcher, alkanes and ASTs. One machine is compiled by PILLAR9 and agrees with the reference.

#### §145 — PolyIA bridge
**Mandate.** UCG machines are PolyIA atoms (typed ports, effects, version, provenance, witness), and the PolyIA compiler can compose them.
**Acceptance witness.** A `.poly` commission composes two UCG machines; the plan compiles and runs.

#### §146 — Ingram and Realms bridges
**Mandate.** Ingram's grammar × in-grammar duality and Realms' typed generative families are subjects in UCG (language and world grammars) under the same card schema.
**Acceptance witness.** One Ingram grammar and one Realms family are expressed as GUC cards and pass the conformance suite.

### Part XVII — Verification, security, benchmarks and release

#### §147 — Test pyramid
**Mandate.** Unit, property, metamorphic (e.g. D(∫f) = f), mutation, proleptic replay and adversarial tests.
**Acceptance witness.** Coverage is reported per subject. The mutation score is ≥ a declared threshold, and surviving mutants are listed.

#### §148 — Independent witnesses per pillar
**Mandate.** Each pillar has at least one witness implemented by a different party (CAS, toolkit, dataset, proof assistant).
**Acceptance witness.** The witness matrix shows pillar × witness with versions and hashes.

#### §149 — Proof-assistant lane
**Mandate.** Selected laws (∂∂ = 0, rank–nullity, the Butcher order conditions for small trees, the GIN classifications) are formalized in Lean/Mathlib as a separate lane.
**Acceptance witness.** Lean files compile, and the statements are linked to the UCG cards. Failures are reported.

#### §150 — Benchmarks against baselines
**Mandate.** Compare against sympy (integration/differentiation), RDKit/GDB (enumeration), OPSIN (naming), and Lean (laws), on time, coverage and false admissions.
**Acceptance witness.** Benchmark tables with environment, versions and raw data.

#### §151 — Supply-chain integrity
**Mandate.** Pin package versions and hashes, and verify provenance before installation. In the seed session, a `pymatgen` wheel dated the same day contained stub modules; such artifacts are rejected.
**Acceptance witness.** SBOM, hash-pinned lockfile, and a provenance check that refuses packages with anomalous metadata. The rejection log is included.

#### §152 — Determinism and reproducibility
**Mandate.** Same inputs give the same outputs across runs and machines, within declared floating-point tolerance.
**Acceptance witness.** Cross-machine replay of all E-experiments matches.

#### §153 — Performance budgets
**Mandate.** Declared budgets per machine and per pipeline. Regressions fail CI.
**Acceptance witness.** A performance dashboard runs locally, with history.

#### §154 — Security boundaries
**Mandate.** No secrets in source or logs; no network beyond the allowlist; no execution of untrusted code outside the sandbox.
**Acceptance witness.** A secret scan, a network-deny test and a sandbox test all pass.

#### §155 — Documentation
**Mandate.** Foundations, per-subject guides, ADRs, an epistemic register, an experiment register (including refutations), and a glossary.
**Acceptance witness.** A docs build with link check passes. Every register entry is linked to a ledger hash.

#### §156 — Release candidate and handoff
**Mandate.** Freeze versions, produce SUMMARY.md, ACCEPTANCE.json, SBOM and a machine-readable ATOM-HANDOFF, and await the owner.
**Acceptance witness.** The final report lists run commands, Git SHA, PASS/FAIL/BLOCKED/NOT_RUN per section, the reproduced seed facts (§R), and the next valid harness state.

---

## Executable commission sequence

**PHASE 0 — Resume honestly.**
- Read this commission, `docs/UCG_FOUNDATIONS.md`, all attached packets (PolyIA, Plicastratum, Relational Generativity, Q-Strings, TRE, Chemistratum, WAZNOMIA, Determinations II, PILLAR9, the Corpus Engine design) and the repos (purl, musa, substrateio, grammarinnumbers, computationalgrammartheory, snad, abedkadaancom).
- Pin everything in `sources.lock`.
- Run `python3 -m unittest discover -s tests -v` in the seed package and every `experiments/e0*.py`.
- Compare to §R. Any mismatch is a failure receipt, not a silent fix.

**PHASE 1 — Core and harness.** Implement `core/` (Alphabet, Word, Grammar, InGrammar, Denotation, Witness, Machine, GUC, equality criteria, refusal types, ledger), plus UCG-HARNESS/0.2 with byte-level receipt verification. Prove §027 to §044.

**PHASE 2 — Chemistry alphabets.** Port E01 to E04 onto the core, add the §046 in-grammar, §049 ionic grammar (BLOCKED until a database is authorized), §051 VSEPR, §059 composition grammar, §062 stereo and §070 stoichiometry. Seal every new prediction.

**PHASE 3 — Common math.** Port E05, then add §085 polynomials, §093 Leibniz/Faà di Bruno, §094 limits, the full §095 method set, §099 quadrature, §100 series, §104 decompositions, §106 ODE classes, §118 Smith normal form, and §111 groups to n ≤ 31 with complete isomorphism.

**PHASE 4 — Generator of generators.** Implement §123 to §132: meta-grammar → machine form + compiler form. Regenerate the hand-written E05 machines and prove trace equivalence.

**PHASE 5 — Concierge, bridges and SU export.** Implement §133 to §146. The SU export is data plus a proposed PR, held for the owner.

**PHASE 6 — Verification and release.** Implement §147 to §156: Lean lane, benchmarks, supply chain, reproducibility. RELEASE_CANDIDATE awaits explicit approval.

**Final Codex output.** `SUMMARY.md` with run commands, exact Git SHA, completed sections, the reproduced seed facts, benchmark tables, the proleptic ledger head hash, remaining BLOCKED items with what would unblock them, and an ATOM-HANDOFF message.

Respect three distinctions throughout:
- a sealed prediction is not a discovery until witnessed;
- a witness is not truth until it is itself checked;
- a generated machine is not a capability until its tests and VERIFY state pass.
