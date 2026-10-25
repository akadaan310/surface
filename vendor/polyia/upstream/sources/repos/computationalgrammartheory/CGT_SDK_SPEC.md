# CGT SDK: specification (version 0.1.0)

The `cgtsdk` package (`sdk/`) is the executable companion to the book. This file states what the SDK promises, which invariants its tests enforce, and what it does not do. The tutorial is Chapter 18 of the book; the generated API reference is the book's SDK page, built from docstrings by `book/tools/export_data.py`.

## 1. Requirements and installation

- Python ≥ 3.10, **standard library only**, no runtime dependencies (D-014).
- `cd sdk && python3 -m pip install -e .`, or `export PYTHONPATH=sdk/src`.
- Tests: `cd sdk && python3 -m unittest discover -s tests` (56 tests).
- No account, key, network or paid service is needed for any part of the SDK.

## 2. Core model

| Concept | Type | Contract |
|---|---|---|
| Move | `Move(name, params, doc, mutates)` | an element of the signature Σ, with its arity |
| Call | `Call(name, args)` | one occurrence of a move in an expression |
| Expression | `str`, parsed by `parse_expression` | calls separated by `;` or whitespace, e.g. `push(1); pop` |
| Structure | subclass of `Structure` | provides `SIGNATURE`, `abstract()`, `denote(state, call)` and `apply(call, cost)` |
| Grammar | `OperationalGrammar` (from `Structure.grammar(admissible=None)`) | G = (Σ, 𝔄, ⟦·⟧, ℒ), DEF-003 |
| Result | `ExecutionResult` | one field group per layer: `syntax` (`ok`, `error`, `calls`); semantics (`defined`, `undefined_at`, `reason`, `denoted`); execution (`values`, `cost`, `adequate`) |
| Cost | `Cost` | counts by category, optional trace; `weighted(CostModel)` |

### 2.1 The three layers

1. **Syntax**, `check_syntax(expr)`: parsing, known moves, arity, and admissibility. The admissibility check runs the *projection* of the move word onto the letters ℒ mentions (D-015) through a minimal DFA (`compile_regex`: Thompson construction, then subset construction, then Moore minimization). A syntax failure executes nothing and costs nothing.
2. **Semantics**, `denote(calls)`: the pure reference semantics. It runs on `abstract()` and never touches the representation. It reports whether the word is defined and where it first becomes undefined.
3. **Execution**, `execute(expr)`: runs `apply` on the representation (mutating it) and counts every step.

`resolve(expr)` returns the last value and raises on any failure.

### 2.2 Adequacy invariant (the central test)

For every structure and every expression, `execute` with `check_adequacy=True` (the default) sets `adequate = True` exactly when:
- the representation's values equal the reference semantics' values; and
- both become undefined at the same call, or both stay defined.

`tests/test_grammar_structures.py` checks this for every built-in structure on thousands of random calls, including undefined ones. **Every new structure must be added to that test.**

### 2.3 Cost conventions

- Categories: `read`, `write`, `compare`, `arith`, `pointer`, `hash`, `probe`, `alloc`, `edge`, `rule`.
- An arithmetic operation on a b-bit integer costs ⌈b/64⌉.
- Models: `UNIT` (every category weighs 1) and `MEMORY` (only `read`, `write`, `pointer` and `probe`); users may define their own `CostModel`.
- Costs are *counted*, not measured. Wall-clock time appears only where explicitly labelled.

## 3. Modules

| Module | Contents |
|---|---|
| `cgtsdk.grammar` | `Move`, `Call`, `Structure`, `OperationalGrammar`, `ExecutionResult`, `Inadmissible`, `parse_expression` |
| `cgtsdk.cost` | `Cost`, `CostModel`, `UNIT`, `MEMORY`, `Report`, `break_even` |
| `cgtsdk.automata` | `DFA`, `compile_regex` |
| `cgtsdk.structures` | `ArrayStructure`, `LinkedListStructure`, `StackStructure`, `QueueStructure`, `DequeStructure`, `HashTableStructure` (stable FNV hash, linear probing), `HeapStructure`, `TrieStructure`, `BinaryTreeStructure` (pointer or heap representation), `BSTStructure` (unbalanced or AVL; iterative, D-018), `GraphStructure` (relational semantics, `at(v)`, `here`), `AutomatonStructure` |
| `cgtsdk.algorithms` | see the four groups below |
| `cgtsdk.addressing` | compiled move words: `HeapWord` (THM-006 normal form with interval domain), `AffineMod`, `XorMask`, `BoxTranslation`, `compile_word`, `heap_walk`, `debruijn_moves`, `hypercube_moves`, `grid_moves` (PROP-008) |
| `cgtsdk.sharing` | `DagGrammar` (minimal-DAG forests, rank access, path-copying updates; THM-005), `Explicit` baseline, tree generators |
| `cgtsdk.lab` | generators (`random_parent_array`, `random_digraph`, `random_labelled_graph`, `random_weighted`, `random_index_workload`), `compare_structures`, `compare_functions` (oracle-checked, build vs query cost), `format_table`, `ExperimentRecord` (deterministic fingerprint) |
| `cgtsdk.service` | `handle`, `capabilities`, `Client`, and an HTTP server; contract in `GRAMMAR_AS_A_SERVICE.md` |

The algorithm groups:

- **Searching, sorting and basics:** `linear_search`, `binary_search`, `insertion_sort`, `merge_sort`, `heapsort`, `quicksort`, `counting_sort`, `UnionFind`, `knapsack_01`, `lcs_length`, `edit_distance`, `naive_find_all`, `kmp_find_all`.
- **Graphs:** `bfs`, `bfs_path`, `dfs_order`, `topological_sort`, `tarjan_scc`, `dijkstra`, `bellman_ford`, `floyd_warshall`, `transitive_closure`, `kruskal`, `prim`.
- **Ranges and LCA:** `Fenwick`, `SegmentTree`, `SparseTable`, `NaiveLCA`, `EulerLCA`, `heap_lca`.
- **Grammar-driven, PageRank and SAT:**
  - `product_reach` (THM-001), `path_grammar_closure` (THM-004);
  - `pagerank_power`, `pagerank_gauss_seidel`, `pagerank_exact`, `constrained_pagerank` (THM-008, PROP-009, PROP-010);
  - `two_sat`, `solution_automaton`, `brute_force_count`, `satisfies`.

## 4. Testing obligations

| Area | Test file | Oracle |
|---|---|---|
| structures | `test_grammar_structures.py` | adequacy against `denote`, on random calls |
| algorithms | `test_algorithms.py` | brute force or a second algorithm on small inputs |
| PageRank | `test_pagerank.py` | exact linear solve; solvers agree; certified error bound holds; per-step contraction (THM-008); personalization and dangling pages; warm starts; the constrained surfer under the universal language equals PageRank |
| addressing | `test_addressing.py` | step-by-step walks, all words up to a length, on many tree sizes |
| trees and sharing | `test_trees_sharing.py` | explicit trees; BST/AVL invariants; 5,000 sorted keys |
| SAT | `test_sat.py` | brute-force counting |
| service | `test_service.py` | layers, quotas, determinism, HTTP equivalence |

Two further checks run outside the SDK and complete the testing obligations: every example in the book is executed by `book/tools/check_examples.py`, and the browser laboratory's JavaScript port is tested against fixtures the SDK exports (`book/tests/core.test.mjs`).

## 5. Determinism

- All generators take explicit seeds.
- Hashing uses a fixed FNV hash, never Python's salted `hash`.
- `ExperimentRecord.fingerprint()` hashes everything except the environment and fields that name wall-clock time.

## 6. Non-goals and known limitations

- **Not a performance library.** Python constants dominate wall-clock time. Use the counted costs for comparisons.
- **The GaaS server is for local study.** It has no authentication and does not preempt algorithm requests (D-016).
- **No sandbox for arbitrary user code.** The browser laboratory runs a JavaScript port of fixed operations; it does not execute user-supplied Python.
- **Scope of the structures.** Linear-time LCA (Schieber–Vishkin, Bender–Farach-Colton) and tree SLPs are not implemented. The Euler-tour index uses an O(n log n) sparse table.

## 7. Versioning

Semantic versioning. A change to any structure's reference semantics bumps that structure's grammar version in the service registry (`STRUCTURES` in `service/contract.py`), so cached GaaS results stay valid (GRAMMAR_AS_A_SERVICE.md §6).
