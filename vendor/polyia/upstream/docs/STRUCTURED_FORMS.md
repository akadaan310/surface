# Typed alphabets and finite indexed words

`polyia.forms.run_forms(parameters)` computes typed alphabet actions and canonical representatives of finite labeled structures. It addresses the bounded constructions in [PIA-050 and PIA-051](../GOD_SEED.md#pia-050--v02--typed-alphabets) and retained [UCG §§013–014](../sources/originals/UCG_CODEX_CONSTITUTIONAL_COMMISSION.md). It is a pure standard-library kernel: no model, network, clock, randomness, file access, arbitrary evaluator or state mutation. This increment does not register a ledger capability or an HTTP route and does not confer mission acceptance.

## Source contract and evidence

The implementation was reconciled against the complete [Plicastratum](../sources/originals/PLICASTRATUM.md), complete [UCG Foundations](../sources/originals/UCG_FOUNDATIONS.md), complete [Formal Vocabulary](FORMAL_VOCABULARY.md), [Scientific Foundations SF-01/02](SCIENTIFIC_FOUNDATIONS.md#sf-01-the-inherited-kernel-and-its-running-instance), PIA-050/051 and the exact retained UCG-013/014 clauses. `PINS` in [forms.py](../polyia/forms.py) and every report carry their actual SHA-256 digests and anchors. The focused test verifies those pins against the retained bytes. Runtime pins are references; the kernel does not open source files.

| Contract | Concrete implementation | Boundary |
| --- | --- | --- |
| SF-01/02, UCG-013, PIA-050 | Typed letters, admissibility, declared coordinates, six alphabet kinds, finite permutation groups, effective Naturals | No universal evaluator or inferred domain law |
| Plicastratum §2.2 `complicate` | Ordered finite Cartesian product; concatenated coordinates; actual direct-product action | Infinite-generator products unsupported |
| Plicastratum D2, UCG-014, PIA-051 | Exact finite index-to-letter map; point, sequences, tuples, boxes, trees, graphs, multisets, cyclic orders | Boxes rank 0–3; simple vertex-labeled graphs |
| FV-03/04 | Named structural quotient separate from lossless serialization | No generic `semantic_preservation` assertion |
| FV-05, PIA-051 | Entity, labeled content, representation, view and equivalence identities separated | No persistence or entity registry supplied |
| Plicastratum §6.3 | Explicit bounded algorithms; exhausted searches report a resource limit | No completion claim for unbounded search |

Finite function composition, sorting, rooted-tree codes, exhaustive graph relabeling and the counting formulas used in tests are established mathematics. The JSON schemas, identity projections and budget units are versioned constructions. Tests supply exact finite computation and self-consistency evidence, not a new mathematical theorem or a blind scientific prediction. Supplied letter/source references are claims of custody, not authentication. A caller cannot turn a claimed source hash into an independently checked fact through this API.

The broader inherited chemistry, geometric/vector-field and research obligations, including **UCG-055/062/066/102**, remain open. In particular the periodic-table example stores two supplied positions; it neither derives electron configurations nor admits molecules. A phonetic token records its declared notation and transcription; it does not infer acoustic behavior. Plicastratum fold/unfold, holonomy, mining, promotion, chart invariance and its complete seven-stratum applicata conformance are separate obligations.

## Envelope and reports

Every request is an object with `version: "polyia.forms/0.1"`, an `operation`, the operation's fields below, and optional `budgets`. Unknown fields are rejected. All operation outputs are detached copies. No operation modifies input objects.

| Operation | Required additional fields | Result |
| --- | --- | --- |
| `alphabet` | `alphabet` | Validated definition, resolved letters, content digest and computed group table |
| `product` | `components`, `entity_id`, `interpretation`, `sources` | Product definition and resolved alphabet summary |
| `member` | `alphabet`, `candidate` | Bounded integer membership query for the effective Naturals definition |
| `generate` | `alphabet`, `index` | One generated Natural letter; no domain enumeration |
| `word` | `alphabet`, `word` | Validated word and distinct identity projections |
| `serialize` | `alphabet`, `word` | Word summary plus deterministic JSON `text` |
| `deserialize` | `alphabet`, `text` | Validated original JSON word value |
| `act` | `alphabet`, `word`, `element` | Pointwise letter action of the named alphabet-group element |
| `layout` | `alphabet`, `word`, `coordinates` | New view coordinates with exactly the same index and labels |
| `canonicalize` | `alphabet`, `word`, `relation` | Exact representative and `equivalence_cid` under the named relation |

`canonicalize` also accepts `alphabet_symmetry: true|false` (default false). False fixes letter identities; true additionally takes the minimum over all declared alphabet-group actions. This distinction is part of the quotient digest.

Reports contain `status`, `result`, `checks`, `work_used`, `budgets`, source references and explicit limitations. `PASS` means the requested bounded operation completed; its evidence class is `EXACTLY_CHECKED`. A schema/domain/group failure is `REFUSED`; an unavailable kind/operation is `UNSUPPORTED`; exhausted work, size or depth is `RESOURCE_LIMIT`. Failure results contain `reason`, `detail`, `complete: false`, a failed completion check, and no partial equivalence digest. They have evidence class `NO_RESULT`. Every report declares `mission_acceptance: false`, `llm_inference: false`, `effects: []`.

## Alphabet schema

Every alphabet has:

```json
{
  "version": "polyia.alphabet/0.1",
  "entity_id": "example:bits",
  "kind": "numeric",
  "interpretation": "Explicit exact bit values and complement action.",
  "sources": [{"source": "path-or-source-id", "anchor": "definition", "sha256": "64 lowercase hexadecimal characters"}],
  "letters": [
    {"id": "0", "sort": "Bit", "value": "0", "coordinates": ["0"], "sources": ["same source-object shape"]},
    {"id": "1", "sort": "Bit", "value": "1", "coordinates": ["1"], "sources": ["same source-object shape"]}
  ],
  "group": {"elements": [
    {"id": "e", "images": ["0", "1"]},
    {"id": "flip", "images": ["1", "0"]}
  ]}
}
```

The source entries above illustrate shape rather than executable hash values; use the complete, executed constructions in [demo.py](../examples/forms/demo.py). That driver hashes its own actual source bytes for its authored literal data.

Letter identity and sort are nonempty strings. Every letter has at least one source reference. All coordinate vectors in one finite alphabet have the same positive dimension, up to 16. Coordinates and numeric values are **canonical exact rational strings**, such as `"-2"`, `"0"`, `"3/7"`. Non-reduced `"2/4"`, `"-0"`, zero denominators, floating-point numbers and booleans are refused. Numerators and denominators have at most 256 bits. No Unicode normalization is applied to tokens or identities.

The value contract depends on kind:

| Kind | Letter value |
| --- | --- |
| `lettered` | Nonempty bounded text token |
| `numeric` | Canonical exact rational string |
| `geometric` | `{shape, vertices, ports}`; shape is `point`, `segment` or `polygon`; distinct rational vertices in a common dimension 1–3; ports name listed vertices in order |
| `retial` | `{vertices, edges, directed}`; an explicit finite simple graph used as one letter |
| `phonetic` | `{notation, transcription}` with notation `ipa` or `opaque` and nonempty text |
| `product` | Derived ordered pair of component letter IDs with its component sorts and concatenated coordinates |

Geometric checks validate that representation; they do not prove non-self-intersection, convexity, regularity or physical realizability. A coordinate vector is declared data, not automatically a denotation. Sort names are scoped by the alphabet definition; the kernel does not equate sorts in unrelated alphabets by spelling.

An explicitly finite alphabet has 1–128 letters. Group elements supply image arrays in that alphabet's letter order. They must be unique permutations, preserve each declared sort, include identity, be closed under composition and have inverses. The multiplication table is computed, not trusted as supplied metadata. Its row `g`, column `h` is **g after h**, `(gh)(x)=g(h(x))`. Associativity follows from function composition; the implementation exhaustively checks identity, closure and inverses. The group representation is faithful: distinct IDs with identical image permutations are rejected. No coordinate isometry or domain-denotation invariance is inferred from a permutation.

A product definition replaces `letters` and `group` with `components: [left, right]`. Components are complete definitions. Both must be finite; nested products are explicit. `product` builds this definition, and `alphabet` resolves it independently. Each pair gets its unambiguous compact JSON pair string as ID, for example `["p","1"]`. Product group IDs similarly encode the pair of component group IDs. The computed action sends `(a,b)` to `(g(a),h(b))`. Component coordinates concatenate, and the result retains source references. Product dimensions, cardinality and group size remain bounded.

An effective alphabet instead replaces `letters` with:

```json
{
  "generator": {"name": "naturals", "start": 0, "coordinates": "value"},
  "group": {"elements": [{"id": "e", "rule": "identity"}]}
}
```

This is available only with `kind: "numeric"`. `member` accepts a bounded exact integer and returns whether it is nonnegative. `generate(index)` returns the corresponding Natural with ID and value equal to its canonical decimal string and coordinate `[value]`. Words may use those IDs directly. The definition has countably infinite cardinality; the implementation admits bounded individual queries without enumerating the set. Negative members return false, negative generation indices are refused, and oversized integers reach the resource boundary. Arbitrary generators, expression strings, recurrence programs and nonidentity actions on the infinite set are unsupported.

## Words and identity

A word contains `version: "polyia.word/0.1"`, `entity_id`, `alphabet_cid`, `index` and `labels`, plus optional `view: {coordinates: ...}`. `alphabet_cid` must equal the exact content digest returned by validating the supplied alphabet. Labels are an object mapping **every index key exactly once** to an admitted letter ID; missing, extra or unknown labels are refused.

| Index | Definition | Label keys |
| --- | --- | --- |
| point | `{kind:"point"}` | `"*"` |
| sequence/tuple | `{kind, length:n}` | Decimal strings `"0"` … `"n-1"` |
| box | `{kind:"box", origin:[...], shape:[...]}` | Compact JSON coordinate strings, e.g. `"[-1,0]"` |
| rooted tree | `{kind:"rooted_tree", vertices:[...], root:id, edges:[[parent,child],...]}` | Explicit vertex IDs |
| graph | `{kind:"graph", vertices:[...], edges:[[u,v],...], directed:boolean}` | Explicit vertex IDs |
| multiset | `{kind:"multiset", size:n}` | Occurrence positions `"0"` … `"n-1"` |
| cyclic | `{kind:"cyclic", length:n}` | Cyclic positions `"0"` … `"n-1"` |

A rank-zero box has empty origin and shape and exactly one key `"[]"`; ranks one, two and three are the simplex/duplex/triplex profiles. Empty axes yield no cells. Box origin is retained: translated boxes are not implicitly equivalent. A point and a rank-zero box are distinct index schemas. Trees must have exactly one parent per non-root vertex, a parentless declared root, and full connected acyclic reachability. Graphs can be directed or undirected and can contain loops; duplicate/reversed duplicate undirected edges are refused. Empty graph and empty sequence/multiset/cyclic structures are admitted. An empty cyclic structure uses the single empty representation, rather than asserting a nonstandard order-zero group.

The returned identity fields have separate definitions:

- `entity_id`: caller's continuing entity name, without a persistence guarantee.
- Alphabet `content_cid`: SHA-256 of the complete alphabet definition except its top-level entity name. A product retains the full component definitions.
- Word `content_cid`: SHA-256 of `{version, alphabet_cid, index, labels}`. It retains explicit vertex names, incidence and index-list order and excludes entity identity and view.
- `representation_cid`: SHA-256 of the complete word, including entity name and view.
- `view_cid`: SHA-256 of view data, or null if absent.
- `equivalence_cid`: SHA-256 of the canonical quotient record, which binds version, alphabet digest, named relation, alphabet-symmetry policy and computed representative.

Hashes use deterministic compact UTF-8 JSON with sorted object keys, no Unicode normalization, and no nonfinite numbers. They are content identifiers, not proofs of domain truth. Equivalent graphs may have different raw content IDs because their supplied vertex names differ.

`layout` accepts a coordinate vector of dimension 1–3 for every existing index key. It cannot add vertices, edges, labels or relations. It verifies that the content digest stays unchanged. Unknown fields such as `view.edges` are refused. Moving two nodes together does not create an edge; moving them apart does not delete one.

Serialization retains the full labeled index and optional view, including input vertex and edge order. Deserialization rejects duplicate JSON keys and nonfinite constants before validating the structure. The round-trip is equality of the original JSON value, not recovery of its whitespace, object-key order or original bytes. Canonical quotients remain deliberately many-to-one.

## Declared canonical relations

| Relation | Applies to | Actual algorithm |
| --- | --- | --- |
| `identity` | Every supported index | Canonical JSON of exact explicit index and label map; view/entity omitted |
| `ordered` | point, sequence, tuple, box | Preserve exact shape/origin and index order; retain labels in that order |
| `multiset` | multiset | Sort the occurrence labels; retain multiplicity |
| `cyclic_rotations` | cyclic | Minimum over all rotations, C_n action on nonempty positions |
| `dihedral` | cyclic | Minimum over rotations and reversed rotations, D_n positional action |
| `rooted_unordered_tree` | rooted tree | Recursive `[label, sorted-child-codes]` rooted code; erase vertex names and child-list order |
| `graph_isomorphism` | graph | Exhaust all vertex permutations, compare exact labeled incidence representations lexicographically |

Graph canonicalization includes directedness, vertex labels, loops and every edge. A six-cycle and two disconnected triangles therefore differ despite their identical degree sequences. No probabilistic hash of a degree signature substitutes for exhaustive checking. Tree normalization preserves the root and node labels. Multiset normalization does not preserve tuple order, so it cannot be applied to a tuple by silently changing its index kind.

`alphabet_symmetry: true` applies each declared letter permutation pointwise before the selected index algorithm. A request without that option cannot identify different letter identities merely because a declared permutation relates them. An action never changes index incidence or view coordinates. The preserved relation is only the named structural orbit; the kernel does not assert equal chemical behavior, acoustic effect, program result or physical meaning.

The result records the selected alphabet element, `alphabet_elements_checked` and `index_candidates_checked`. The latter counts candidate transformations examined **per alphabet element**, not distinct images, since stabilizers can collapse images. Tree and multiset algorithms compute their canonical codes directly and report one candidate rather than enumerating all permutations.

## Resource and reproducibility bounds

Inputs are bounded before copying or hashing: 256 KiB encoded JSON, 30,000 nodes, nesting depth 32, 4,096 entries per collection, and 256-bit integers. Deserialization alone allows a 512 KiB outer encoded envelope because placing JSON text inside a JSON string can double escape bytes; its logical string bytes and decoded word remain bounded at 256 KiB. This permits successful serialization to be read back even with heavily escaped vertex IDs. Recursive Python containers hit the depth bound. Alphabet caps are 128 letters, 64 enumerated group elements, four nested product levels, 16 coordinate dimensions, and 64 vertices per geometric shape. Graph inputs have at most 4,096 edges. Coordinate/source strings have additional schema bounds.

Request `budgets` may lower these positive caps:

```json
{"work": 1000000, "cells": 256, "depth": 64, "output_bytes": 524288}
```

`cells` bounds word/retial vertices and box cells; `depth` bounds tree height. `work` is a declared deterministic algorithmic counter, not wall time or an exact count of CPU instructions. Group closure costs `|G|²|Σ|`; graph canonicalization reserves `n! × max(1,n+|E|)` before entering the search, plus validation costs. Sorting/tree/cyclic operations charge conservative bounded comparison/visit units. Both query limits and hard caps apply; users cannot raise them through the envelope.

Graph search admits at most eight vertices. A dense eight-vertex graph can still exceed the work budget: that is a visible `RESOURCE_LIMIT`, never a successful partial canonicalization. Budgets include repeated component validation and repeated canonicalization across alphabet-group actions. Output limits apply to the encoded operation result; the fixed bounded report metadata and failure envelope are additional. Bounded temporary expansion may precede the final result-size check. This is an in-process finite kernel, not an operating-system memory-isolation boundary.

Run the actual examples and focused checks from the repository root:

```sh
/opt/polyia/runtime/bin/python3 -B examples/forms/demo.py
/opt/polyia/runtime/bin/python3 -B -m unittest discover -s tests -p test_forms.py -v
```

[The retained example receipt](../examples/forms/evidence.json) contains complete input envelopes, actual reports, kernel/source hashes and nine literal expectation checks across fourteen kernel calls. Its examples include all six kinds, a phonetic × bit product, a 10³⁰ natural query, cyclic complement/canonicalization, a token-labeled graph layout and exact restoration of that word. The two chemical-looking vertex labels are explicitly a token graph, not a claim that the graph represents an admitted molecule.

The initial test-first run had 19 tests and 34 failed assertions before implementation (`NOT_IMPLEMENTED`). The implementation then passed those 19 tests. The expanded 24-test focused suite adds independent Burnside counts for all binary necklaces/bracelets of lengths 3–7, independent edge-cycle Burnside counts for every simple unlabeled graph through four vertices, adversarial input mutations and the executed examples. A subsequent boundary regression first reproduced a serialization PASS followed by deserialization RESOURCE_LIMIT for a 30-vertex, 260-edge graph with heavily escaped IDs; it passes after the bounded envelope adjustment above. No full-suite or release claim is made by this increment; the parent release process handles consolidated validation and registration.
