# PHANTOM finite scientific research cycle v1

`discovery.py` implements the owner's exact ordered research phases. Each event has a subject, ordinal, parent digest, typed phase, canonical finite JSON payload and digest. The last states are a scoped ACCEPT, REJECT or UNKNOWN followed by ARCHIVE and SELECT NEXT. Missing evidence does not become acceptance. Hash chains detect changes against a retained root; they are not signatures or protection against a writer replacing all evidence.

The executable example calls the unchanged PHANTOM v0.4 `synthesize_word`, `execute_ir` and independently checked word-machine journals. Five imported original modules are pinned by SHA-256 before loading into a distinct module namespace. No arbitrary downloaded program is executed. PHANTOM remains the generator implementation, rather than a name attached to a new search engine.

The controlled target is `f(x)=(3*x+1) mod 2**w`, for `2<=w<=6`. The fixed training subset is `(0,1,2,3)` for w>2, otherwise `(0,1)`. Training is separated from every remaining input before search. The original finite grammar uses ADD/MUL/XOR/AND with constants0,1,3, depth<=2, candidate budget<=512. It returns all attempted construction paths and rejected candidate counterexamples. The selected IR is frozen before challenge. Independent integer arithmetic exhaustively checks the entire finite domain and labels each counterexample train or held-out. Finite exhaustion produces UNKNOWN; it is not impossibility outside the grammar.

Gray-code re-encoding is an explicitly inverted bijection. Its conjugated truth table must transport back to the same function; encoded numbers need not be numerically equal to original numbers. The identity null and a one-bit output perturbation are challenged against the target separately. Since multiplication by3 is invertible modulo a power of2, the accepted finite truth table induces a permutation unitary `U[f(x),x]=1`. Matrix propagation of a coherent phase-bearing vector is compared with direct scalar scatter. A noninjective function is explicitly inadmissible as this unitary correspondence. Classical words, coherent vectors, and physical hardware remain distinct.

This example supports finite classical-word to basis-permutation transport. It is controlled mathematical evidence, not discovery on experimental data, a novelty claim, a speedup claim, a generalization result across widths, or full V2 G6. No unlimited recursive generator grammar is inferred. Existing compiler factory recipes preserve their independent parent-lineage contract; this module does not replace them.

Bounds: up to64 exact input states,2 instructions per candidate,512 candidates,32 events,1MiB per event, dense64x64 complex transport. `run.py` places the research execution in a child with60s hard/45s semantic/50s CPU limits,2GiB address space,8MiB per output file, one BLAS thread and no automatic retry. Its standalone pure functions have algorithmic bounds but do not impose OS isolation on their caller. The existing Supervisor handles progress, stage, epoch and publication fencing unchanged.

`replay(report)` verifies the chain and recomputes the complete search and independent challenge; changing a derived result and merely rehashing a journal cannot make replay pass. `run --replay` also requires the exact source census, published output hashes, matching Supervisor final state, current publication and fence, and the actual worker contract. It rechecks retained test execution evidence; it does not claim it reran all tests. Run a new output directory to perform fresh tests.

```sh
.venv/bin/python -B -m unittest research.quantum_oracle.tests.test_discovery -v
.venv/bin/python -B -m research.quantum_oracle.run --runs build/science-new-run
.venv/bin/python -B -m research.quantum_oracle.run --replay build/science-new-run
```

The scientific commission's source spans and23-domain review are under `commissions/2026-10-25-scientific-completion/`. The unchanged compiler executes source-integrity and foundation-audit tasks there. Its execution SUCCESS is separate from every scientific acceptance decision. University topic identities and original mathematical applicability identities are preserved in `evidence/inherited-registries.json`; they organize research and confer no evidence.
