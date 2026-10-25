# Poly IA — Formal vocabulary and semantic reference discipline

**Edition:** 1.0. **Machine registry:** [`registry/vocabulary.json`](../registry/vocabulary.json). The registry contains stable `VOC-*` identifiers, qualified names, definitions, claim kinds, source keys, continuity keys and a concrete acceptance obligation for each term. This document explains how those terms work together. It does not confer implementation status on a named capability.

## FV-01. A word names a contract

Poly IA treats a term as a source-linked sense, not a globally unique string. Its minimum semantic address is `(namespace, local_name, version, context)`. Display names and symbols may vary by language; the canonical identifier does not. Two entries may share a printed word while identifying different objects, and two printed words may identify the same object under an attested alias rule.

The vocabulary's ordinary mathematical concepts, inherited project definitions and newly proposed package definitions are explicitly distinguished. A house definition chooses how to use a term; it does not establish a theorem. A source definition identifies the original author's usage; it does not claim that every generalization in the surrounding source has been proved. The evidence registry evaluates claims separately.

For example, “field” can name an algebraic structure, a record member, a physical field or an area of study. “Class” may mean an equivalence class, a programming class or a classification category. “Image” may be a map's attained values, a rendered picture or a container image. A bridge between these senses requires a declared construction. Similar wording is insufficient.

## FV-02. The basic object families

| Family | Required distinctions | Typical operations |
|---|---|---|
| Source | Original byte object; decoded text; extracted span; normalized search view | Acquire, hash, decode, segment, cite |
| Syntax | Character, token, alphabet, grammar, expression, quotation | Scan, parse, expand, normalize |
| Meaning | Sort/type, interpretation, assumption, context, referent claim | Type-check, resolve, interpret, compare |
| Computation | Program, operator, machine, state, guard, effect | Admit, execute, observe, record |
| Composition | Port, hyperedge, strand, Q-step, Q-path, grammar-ship | Bind, join, compose, substitute, refuse |
| Evidence | Proposition, witness, verifier, result, limitation | Check, reproduce, refute, certify |
| Evolution | Candidate, version, baseline, improvement epoch | Compare, activate, migrate, retain |
| Publication | Course unit, book, package, SDK, protocol, fruit | Build, validate, teach, distribute |

These families keep representations from acquiring unintended authority. A quoted program is source data until admitted execution. A picture of an edge is a view until it references an actual relation record. A result string saying “passed” is a claim until a registered verifier produces a receipt.

## FV-03. Exactness and equivalence

Every equality judgment names its relation. Poly IA supports, where implemented:

- **Byte identity:** the exact original bytes agree.
- **Normalized textual equality:** a specified normalization produces equal text.
- **Syntactic identity:** parsed terms agree under a specified syntax representation.
- **Algebraic equality:** terms denote equal values under declared axioms and domains.
- **Observational equivalence:** selected observations agree under a stated execution model.
- **Approximate agreement:** measurements satisfy a declared tolerance and uncertainty model.

The relations can differ. Two canonically equivalent Unicode sequences may have different bytes. Two symbolic formulas may agree on a punctured domain while one is defined at an additional point. Two programs may return the same value but perform different external writes. Two geometrically nearby nodes may represent unrelated concepts.

An equality certificate identifies its inputs, relation, assumptions, checker and scope. A conversion that preserves one equality need not preserve the others. `semantic_preservation` is therefore a scoped claim over observables, not a generic success flag. See Scientific Foundations SF-02, SF-03, SF-05 and SF-06.

## FV-04. Promotion and the fold vocabulary

`polyia.grammar_letter` denotes a pinned grammar or certified construction at a higher level. `polyia.promotion` admits that construction under an explicit contract. `polyia.expansion` retrieves its lower-level representation. The namespaced Plicastratum operations retain their inherited meanings:

| Name | Contract | Refusal condition |
|---|---|---|
| `plica.explicate` | Substitute declared blocks or paths | Missing expansion, incompatible level or budget exhaustion |
| `plica.implicate` | Recognize a valid fold and recover its letter | Input does not lie in the fold's declared image |
| `plica.complicate` | Build a product alphabet | Component types or coordinate contracts are absent |
| `plica.applicate` | Map a domain through a specified adapter | Missing preservation/loss contract |
| `plica.holonomy` | Aggregate ordered event contributions in a declared group | Invalid contribution or unspecified aggregation law |

`plica.closable` asks whether a path returns to its initial state. `rg.closable` asks whether a declared composition/closure capability holds. Neither should silently replace the other. `plica.complete` describes a cycle in a successor relation. Logical completeness, metric completeness and computational completeness remain independent terms. The source's “seven-complete” construction needs its own versioned predicate; the word is not evidence.

A **lossless abbreviation** retains a defined expansion. A **quotient** deliberately identifies objects under an equivalence. A **projection** returns an observation and generally loses information. A **lift** supplies a compatible preimage or choice where the contract permits one. A **fiber** represents all admitted preimages under stated scope. These are distinct operations even if a user informally calls each one a fold.

## FV-05. Q, G-ships and relations

The inherited Q-Strings and G-ship sources contain research terminology with historical versions. The new runtime profiles must preserve those source identities and state their mapping explicitly. A Q-String is a quantifiable typed grammar-bearing incidence with content identity, strands and registered operations. Its pairwise record is `(src,dst,relation,grammar,scope,level,witness,status,version)`; a Q-Bundle generalizes to explicit multi-input/output roles. `polyia.q_step` is one typed application; `polyia.q_path` is a derivation using such applications. A unary chain is a special case. A general joint-input derivation is a tree or DAG with preserved ports and premise identity.

An executable `polyia.grammar_ship` is a bridge or composition between grammar packages with explicit source/target types, context, effects, evidence and losses. Historical G-ships preserve the directed labeled multigraph `H=(V,E,Σ,τ)` and edge-word reading; Q-Ships are port-checked compositions. A relational name alone cannot authorize an operation. `entity_id` and `content_cid` remain separate: one tracks a continuing entity; the other identifies an immutable encoded version.

`similar_to`, `derived_from`, `transliterates_to`, `causes`, `equivalent_under` and `contradicts` are independent edge types. A causal claim needs a causal model and appropriate evidence. A lexical resemblance or graph path does not supply either. Q is not a claim of quantum computation; an eventual physical quantum adapter would require a separately declared state space and operations.

## FV-06. Machine and guidance vocabulary

A **machine** has a declared control and data state. A **guard** decides whether a transition is admitted; an inconclusive bounded checker cannot be interpreted as authorization. An **effect** names a change or interaction beyond a pure returned value. A **state variance** is a comparison of two versions under a named projection. A mere changed hash can show different bytes without explaining the semantic difference.

An **event** records enough data for its declared replay. A **checkpoint** binds a state snapshot to prior history, sources, outputs and evidence. A **Git commit** identifies source-control state. A **database commit** establishes transactional persistence. An **experiment seal** commits to a prediction record before its witness is read. These objects may reference each other; they are not interchangeable.

**Replay** rebuilds recorded state using recorded results. **Reproduction** performs a new run to compare with a previous one. Reproduction gets a new run identity. Replaying a journal does not silently issue an external write for the second time.

**Guidance** is a source-linked instruction or proposal with a known target. `SUBMITTED` records receipt; `ACKNOWLEDGED` records that the target considered it; `DEFERRED` and `REJECTED` require reasons; `APPLIED` requires a supported effect and resulting revision. Free prose is not automatically executable. The operator can inspect all dispositions through the live service.

`PRODUCED` means output bytes exist and are captured. `VERIFIED` binds a registered verifier's successful receipt to that captured version. `ACCEPTED` is a scoped completion decision. These labels never imply that the whole commission is complete merely because one bootstrap demonstration passed.

## FV-07. Evidence language

An evidence record carries the proposition, claim kind, source authority, method, input scope, result, uncertainty, limitations and verifier identity. Recommended outcomes include:

| Outcome | Interpretation |
|---|---|
| `PROVED` | A stated proposition follows under explicit axioms and a documented proof discipline |
| `EXACTLY_CHECKED` | A finite exact computation satisfies its declared criterion |
| `SYMBOLICALLY_CHECKED` | A symbolic procedure established the scoped identity under its assumptions |
| `NUMERICALLY_SUPPORTED` | Specified measurements or samples support the claim within recorded tolerances |
| `SOURCE_ATTESTED` | An identified source makes the assertion; independent truth is not implied |
| `INCONCLUSIVE` | The procedure did not establish the requested claim |
| `COUNTEREXAMPLE` | A validated instance violates the stated claim |
| `RESOURCE_LIMIT` | The run ended at an explicit budget |
| `UNSUPPORTED` | The registered system lacks the requested capability |

A refusal describes the relevant unmet contract. An unknown describes missing evidence. A budget result describes incomplete search. A counterexample refutes a universal statement only if it satisfies that statement's assumptions. The interface must show these distinctions plainly.

## FV-08. Capability words must earn their suffix

`runnable`, `replayable`, `composable`, `reversible`, `observable`, `publishable` and `teachable` are predicates with witnesses. A package cannot acquire them through naming. A runnable package has a clean invocation and declared environment. A reversible operation identifies what its inverse restores. A publishable package resolves permissions and provenance. A teachable unit includes prerequisites, worked examples, exercises and a way to check answers appropriate to its subject.

A **tool contract** governs a registered operation. An **SDK** supplies bindings of contracts. A **protocol** specifies interoperable messages and behavior. An **API** exposes operations through a particular interface. A **model adapter** supplies an optional computational component; its predictions do not replace the contracts. A **fruit**, in TREE's vocabulary, is a verified portable output that can seed another instance.

## FV-09. Keeping the vocabulary alive

Every new sense receives a stable identifier, definition, source, version, aliases, counterexamples and acceptance obligation. Refinement creates a successor record; the old sense remains resolvable. A term that changes meaning gets a migration note and explicit relationship, not a silent edit. UI translations may add labels while retaining the semantic address.

Vocabulary linting must detect duplicate qualified names, absent sources, circular definitions without admitted fixed-point semantics and unsupported capability claims. Human scholarly review remains necessary for definitions and source interpretation. The machine registry assists that work by making every term inspectable and every unsupported part visible.

The package's **DODGE** mnemonic is newly defined here: **Deliverable, Obligations, Dependencies, Guards, Evidence**. It is a work-item reference structure, not a claimed pre-existing scientific method. It connects a production to the constitutional obligations it serves and the receipts needed for acceptance.

### Sources

All inherited source keys resolve through Scientific Foundations' source table and the package source manifest. Principal sources are Relational Generativity §§2–5; Plicastratum §§2–5; Infinity Manifesto §§B–F; Corpus Engine's five strata; TREE Constitutional Ontology and Corpus Bridges; and Astra's Formal Constitution. The full vocabulary registry specifies source keys per entry.
