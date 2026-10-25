# TRE Virtual Machine and Compiler — Architectural Contract

## 1. Compilation stages

```
source (.p9 / domain grammar / shader module)
  ↓ unicode-aware lexer, scanner errors
  ↓ parser (LL/LR when grammar admitted, GLR/Earley for supported ambiguity)
  ↓ typed AST (tree; hash-consed subexpressions optionally form DAG)
  ↓ semantics and effect/capability checking
  ↓ lowering to typed SSA-like IR with witness/source positions
  ↓ optimization passes (each with verification and benchmark)
  ↓ target machine / GPU shader backend
  ↓ linked artifact (binary, WASM, shader, scene pack)
  ↓ TRE loader (capability-checked), execution, trace, replay
```

Compile-time semantic checks are not delegated to an untrusted LLM. The native source text, typed AST, typed IR, and executable are distinct products with independent content IDs. The language may generate its **own** compilers and frontends after a bootstrapped trustworthy stage. The VM must expose explicit limits and safety boundaries before accepting unknown code.

## 2. Registers, memory and scheduler

This is a **virtual machine design**, not a claim to redesign physical RAM or CPU hardware:

- `S-REG` — current structure root handle, not an absolute unchecked address.
- `T-STACK` — grammar parsing stack; distinct from the runtime call stack.
- `A-ALU` — bounded symbolic admission/equivalence checker (not a physical ALU).
- `X-REG` — current typed machine state/capability context.
- `C-REG` — current corpus commit and license manifest.
- `R-REG` — currently admitted render graph / GPU capability view.
- `P-REG` — physics world handle and declared simulation tick.
- `K-REG` — independent logical clock; separate clocks for syntax, simulation, renderer, audio and persistence.

A tagged value may be `(kind, payload)` logically; the backend may use tagged pointers, NaN boxing where admissible, arena offsets or plain tagged unions. **Do not mandate a per-cell meta-tag until cache, alignment, GC and platform costs are measured**. Use typed offsets/handles, rather than raw machine pointers, for serialized and cross-process references.

## 3. Correction matrix for supplied Google blueprint

| Blueprint proposal | Formal correction / stronger implementation |
|---|---|
| `V=Σ∪N` for vocabulary | Distinguish source-character alphabet, token alphabet, disjoint terminals/nonterminals `T ⊔ N`, symbol table, and semantic vocabulary. |
| Fixed sliding bit masks tokenize everything | DFA bit-masks work for bounded alphabets; use Unicode-aware scanning, escapes, identifiers, comments, and finite-state boundary logic. |
| All CFGs deterministically shift-reduce | Not every CFG is LR(k). Admit LL/LR subsets explicitly; choose bounded GLR/Earley for ambiguous grammars and record complexity. |
| 'Abstract Direct Graph' derived from syntax | An AST is rooted; sharing/interning creates a DAG, and reference/call graphs may cycle. Do not conflate. |
| Transitive closure `⇒*` maps to assembly jumps | `⇒*` is derivability. Codegen maps **typed IR operations** to opcodes and branches. Closure is a separate analysis. |
| Runtime engine is a pushdown parser | Parser PDA and target VM are different machines. A runtime may have stacks, registers, heaps, and an event loop. |
| ε-productions skip clock ticks | An ε-step consumes no source symbol, but parser work, memory movement and total CPU cost still count. No zero-cost promise. |
| All ambiguity resolved via bitmaps | Packed parse forests/GLR graph-structured stacks may be needed; track worst-case state explosion. |
| A hash content ID is O(1) access | Hash map lookup expected O(1) once indexed; storage/cache/I/O and complete output costs are separate; Merkle proofs typically O(log n). |

## 4. Rendering machine boundary

`Scene IR → render dependency DAG → passes → shader modules → backend (WebGPU/Vulkan/Metal/GLES) → GPU`. Pass dependencies require resource hazard checks; output projection and display are adapter concerns. The renderer owns cameras/materials/draw scheduling; the platform backend owns device and command submission. Use a software/reference rasterizer only as a correctness oracle, not a production performance claim.

## 5. Physics machine boundary

`World IR → broadphase → narrowphase/contact manifold → constraint solver → integration → state sync → render projection`. Distinguish deterministic fixed-tick simulation from variable-rate visual interpolation. Rigid-body collision is a baseline separate from tree-growth nutrient dynamics. Physics must never be confused with speculative symbolic plant-growth rules.

## 6. Packaging / containment

- Web: WASM + WebGPU/WebGL (browser and OS remain trusted execution hosts).
- Android: native libraries + NDK/JNI + Activity/Surface, with bounded asset packs; APK is an application bundle, not an emulated CPU.
- iOS: native framework/static libraries + Metal and signed IPA; Apple toolchain/signing is required for legitimate device deployment.
- Desktop/headless: CLI program, software verifier, optional Vulkan/Metal/D3D adapter.

Shared semantics and serialized scene/simulation snapshots are the portable artifacts. GPU shader binaries, drivers and OS security policies are **platform-specific** and should never be presumed interchangeable.
