# Deterministic Concierge: from commission to micro-agency

## Input and interpretation

The concierge accepts `.poly` native source as its authoritative executable input. Optional human prose is treated as **untrusted proposal text**, never executable instructions. A lexical/topic classifier can propose a candidate `.poly`, but user-policy gates and typechecking have final authority. Under narrow scopes, a grammar can deterministically parse supported natural-language commands; otherwise the system must return `NEEDS_EXPLICIT_BINDING`, not hallucinate intent. Optional small models may propose ASTs only and never bypass checks.

### Pipeline

`SOURCE_BYTES → LEX → CST/AST → SCOPE_RESOLUTION → TYPED_REQUIREMENTS → CAPABILITY_REGISTRY → NEGATIVE_GRAMMAR → DEPENDENCY_SOLVER → PIR → COMPOSED_AUTOMATON → VERIFIED_EXECUTION → PACKAGED_SDK → HUMAN/TOOL PROJECTIONS`

Result outputs are not just JSON:

1. `plan.pir`: canonical textual, inspectable typed intermediate representation.
2. `automaton.dot`: state transition graph; rendering optional.
3. `automaton.html`: human projection of the same source, never the source of truth.
4. `automaton.json`: audit/transport payload with hashes and module versions.
5. Later: self-contained `agency.wasm` or native package plus WIT interface, verified against PIR.
6. Later: versioned `witness.cbor`/signed receipt and executable event trace.

## Formal obligations

`compile : Commission × RegistrySnapshot × Policy → Either[Refusal, AgencyArtifact]`

The compiler is deterministic for fixed pinned inputs. A refusal includes earliest cause, all failed ports where feasible, and proposed recovery actions. The selected module set must be topologically ordered over declared port dependencies; cross-module backreferences are rejected unless a cycle is admitted under an explicit iteration semantics.

An effect-free module can be replayed in isolation. An effectful one requires a declared capability and a separate authorized transition, with dry-run and non-destructive defaults. Module selection and proof obligations are distinct from execution results. A reported proof is not an `assert` statement or merely a green test.

## Concrete example: topology

The supplied `examples/topology.poly` compiles through eight fixture module declarations: surface, scoped language identity, pronunciation, segment features, initial phonetic match, morphology, relational word-set, and automaton packaging. It produces an eight-step `plan.pir` and transition artifact. No multilingual dataset was read: the output is a **proposed composition** only. A production `phonex.*` atom must replace the fixture providers, version its IPA/CLTS resources, and return real attested witnesses before a real word set may be asserted.

## Future model partitions

Each language/variety gets a **scoped model pack** `(VarietyID, Orthography, PronunciationFST, MorphologyFST, Lexicon, NegativeGrammar, EvidencePolicy)`. One language can have several orthographies/dialects; historical and unwritten languages may have uncertain or reconstruction-only pronunciation. `Module` is universal but grammars are language-specific; no method infers a correct phonological grammar from an alphabet alone. A higher transducer composes outputs only after evidence, script, diacritic and feature representations are aligned.

## Negative case library

- Two matching pronunciations in unrelated languages: phonetic relation only, no invented cognate.
- Strong etymological relationship but divergent sound: keep source-attested history rather than down-ranking to unrelated.
- Same script but distinct dialect pronunciations: separate model instances and provenance.
- Noninvertible grapheme folding: store original and encode loss.
- Competing module providers: return ambiguity, do not arbitrarily select.
- Missing dataset permission: refuse import/export even if other metadata matches.
- Contradictory candidate laws: preserve counterexample and scope rather than auto-promote.
