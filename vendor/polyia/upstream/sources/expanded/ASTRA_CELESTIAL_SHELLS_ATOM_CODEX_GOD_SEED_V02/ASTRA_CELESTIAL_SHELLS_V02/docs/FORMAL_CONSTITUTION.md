# ATOM v0.1 — Formal constitution and terminology

## Definition of a transition atom

An atom is a typed, finite primitive `a = (I,O,Q,δ,g,e,w,c)`, where `I`/`O` are declared input/output types, `Q` the states, `δ:Q×I→Q` the admissible transition relation, `g` the guard, `e` the explicit effect class, `w` the verification witness, and `c` the cost/resource bound. The name **ATOM** expands to Automata, Transitions, Operations & Memory. A micro-automaton composes one or more atoms. The parent universe uses a controlled product of these machines, but deliberately does **not** automatically allow arbitrary cross-effects.

**Atoms != agents != models.** An atom runs without an LLM; an agent can ask to run an atom; a language model can propose parameters but cannot override the guards.

The built state machine is an explicit seven-phase finite-state control protocol:

`OBSERVE → PROPOSE → ADMIT → EXECUTE → VERIFY → CHECKPOINT → HOLD`.

- `OBSERVE`: select one registered, typed micro-machine.
- `PROPOSE`: evaluate a game-theoretic strategy over a fixed scenario-payoff table.
- `ADMIT`: check precise domain and schema restrictions.
- `EXECUTE`: evaluate one declared, bounded, local computation.
- `VERIFY`: independently reconstruct the expected result from the declared handler and assert equality (basic self-consistency, not an external independent oracle).
- `CHECKPOINT`: snapshot state, hash it, include its ancestor and archive designated source bytes in content-addressed storage.
- `HOLD`: terminal **for that step**; only explicit resume returns to `OBSERVE`.

`FAILED` is represented by a transition refusal without phase advancement. There is no background rollback or silent repair; the controller's prior checkpoints remain accessible.

## Game-theoretic policy

Actions are `EXPLORE`, `OPTIMIZE`, `VERIFY`, `HOLD`. The external scenarios are `nominal`, `limited_gpu`, `bad_data`; `U(action, scenario)` is a bounded synthetic utility. The declared deterministic policy is

`π(s) = argmax_a min_{scenario∈S} U(a, scenario)`

with fixed lexical tie-breaking. It produces `VERIFY` in the supplied table. This is an **illustrative robust maximin policy, not a Nash-equilibrium solver**, not reinforcement learning, and not an optimal policy for any real financial or gameplay system. Future agents may propose alternative payoff tables only behind separate evidence and admission rules, never silently rewriting the constitution.

## Immutability and versioning

Let `S_k` be a state at a checkpoint, `C_k = H({parent:C_{k−1}, S_k, artifact_archive_k})`. Source bytes are stored as SHA-256-addressed blobs and can be checked after working code evolves. `C_{k-1}` is not overwritten. This is a **content-addressed append-only application protocol**, not malicious-admin-proof storage. Replacing the state plus all receipts and objects could forge a new self-consistent history. For third-party assurance introduce signed roots, transparency logs, or external attestations.

Past source snapshots can be reopened as data; a previous checkpoint is not editable. Branch/fork semantics, cross-branch merge, cryptographic identities, conflict reconciliation and durable transaction atomicity across disk files are not yet implemented.

## Hierarchies

A *root* is a dependency or provenance record, a *pillar* is a stable invariant and interface, a *branch* is a scoped transformation, a *leaf* is an externally observable output, and a *fruit* is a verified, reusable artifact. These names are research constructions, not a substitute for the standard graph/tree definitions.

## Limits and safety

- Source archive is limited to an explicit file allowlist, never runtime secrets. Do not expand it to `.env` or credentials.
- No arbitrary subprocess dispatch, no network commands to untrusted hosts, no privileged action.
- Native Hermes/OpenClaw integration requires explicit trust, tool policies, execution isolation, and user authorization.
- `focus` is deliberately a pointer/idle proxy, not biometric gaze tracking.
- `economy` uses bounded play credits and performs no payments, exchange, mining, or crypto custody.
- `science` values are mathematical models, not measured spectral results.
- Local simulation of orbital travel is not NASA/Horizons-verified observer motion.
- Quantum is an analogy for multiple alternate states and does not imply physical quantum calculation.

## Technical precedents

- Sutton, Precup & Singh (1999), *Between MDPs and semi-MDPs*: temporally extended options formalize control at several time scales. ATOM is inspired by this, but currently is not an SMDP solver.
- Standard Mealy/state machines, guarded transitions, content-addressable Merkle DAGs, finite-state controllers, crash-consistent journals.
- Substrate IO, CGT, Ingrammatica, PURL/SEURL: separate syntactic admissibility, semantic realizability, execution cost, and observed evidence.
