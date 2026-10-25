# PLICASTRATUM — the substrate of folds
### A domain-agnostic framework for alphabets of alphabets, harnessed generation and history-bearing programs
*Theory: Abed Kadan. Strata names: the Al-Bāb file. Formalisation and reference kernel: this document + `prototype/plicate.mjs`.*
*Status: research specification v0.1 — 2026-10-20.*

---

## 0. How to read this

Every claim carries one of three labels, following the discipline in `START_HERE.md`:

| Label | Meaning |
|---|---|
| **[K] Known** | Established mathematics or computer science. Cited. Reproduced in the kernel where possible. |
| **[C] Construction** | A definition we choose. Not true or false, only useful or not. Judged by tests and by what it lets us build. |
| **[H] Hypothesis** | A claim about what will happen when the construction is used. Must be tested; may be refuted. |

Each test referenced as `A1`, `C2`, … lives in `prototype/plicate.test.mjs` and passes (`npm test`).

Nothing in this document is about games in particular. Games, music, maps, skies, code and chemistry are **applications** (§8). This is deliberate: the framework is the engine's grammar of grammars, and the HOMELESS engine is its first tenant, not its owner.

---

## 1. The idea in one paragraph

Any domain can be read as **letters** (units), **words** (arrangements of units in some number of dimensions), **rules** that say which words are admissible, and **machines** whose transitions are themselves written as words. Three moves then become possible everywhere at once: **fold** a recurring, certified path into a single new letter (so alphabets grow into alphabets of alphabets); **unfold** any letter back into the path it stands for (so nothing is ever opaque); and **remember** the journey, not just the destination (so returning to the same string after seven changes can be a different program, exactly when the journey left a mark). Constraints are not there to stop bad output. They are the **harness**: they shrink an infinite space to a shape where the best path is already computable, or cheap to compute.

---

## 2. Nomenclature — the fold family

Latin *plicare* means **to fold**. The language already contains our operator alphabet, and it was never only a dictionary: *explicate, implicate, complicate, replicate, duplicate, triplicate, multiply, apply* are all folds. We take them literally. **[C]**

### 2.1 The unit and the ranks
| Name | Root | Meaning in the framework | Example |
|---|---|---|---|
| **plica** | a fold | one unit of any alphabet | a note, a letter, a street turn |
| **punctum** (rank 0) | a point | a one-symbol alphabet. All information is in *when*, *where* and *for whom* it fires | the D♯ notification ping |
| **simplex** (rank 1) | one-fold | strings: the linear alphabets we know | A–Z, 0/1, do–ti |
| **duplex** (rank 2) | two-fold | words are grids: a matrixed alphabet | a tile map, a chord-over-time score |
| **triplex** (rank 3) | three-fold: *triplicate* | words are volumes, and the paths through them | voxels, a city with height |
| **n-plex** / **multiplex** | n-fold | words indexed by ℤⁿ | n-dimensional code |
| **retial** | *rete*, net | words indexed by a graph instead of a lattice | a street network, a constellation |
| **plicate** (any level) | folded | an alphabet whose letters are certified words of a lower alphabet | VISIT, CROSSING (§5.3) |

### 2.2 The operators
| Operator | Root | Definition | Kernel |
|---|---|---|---|
| **explicate** | *ex-plicare*, unfold | replace every letter by its block (a substitution / morphism) | `explicate` |
| **implicate** | *in-plicare*, fold in | read blocks back as letters; refuse if the word is not a fold | `implicate` |
| **replicate** | fold again | iterate a substitution (L-systems, substitution tilings) **[K]** | test B1 |
| **complicate** | *com-*, fold together | product of two alphabets: letters are pairs (note × time, turn × degree) | `turn+degree` alphabet, test G2 |
| **applicate** | *ad-plicare*, fold onto | attach the framework to a domain via an adapter (§7). *Application* = this word. | §7 |
| **promote** | — | implicate one level up: a certified path becomes a letter of level k+1 | `promote`, test D1 |

### 2.3 Closure: complete versus severed
Seven with its **n** made an **r** is **sever**. That pun is the definition. **[C]**

- An alphabet is **complete** (*nūn-closed*) when its successor map is a single cycle through every letter. It goes on by returning: do re mi fa sol la ti, *do*.
- It is **severed** when the successor is a chain that ends: A…Z, then nothing.
- **open**: no successor declared (the punctum). **partial**: several cycles, branches or orphans.
Test A1. A complete alphabet of size n is the cyclic group ℤₙ under succession **[K]**. Severed alphabets get their infinity from length (words grow). Complete alphabets get it from return (the cycle can be run again at a new register). The diatonic scale has both: seven letters that close, inside an octave that repeats.

### 2.4 The whole substrate
The substrate of folds of folds is named **Plicastratum**. It belongs to the -stratum family (§3) because every level of it carries the seven strata.

---

## 3. The seven strata, as a layer contract

The Al-Bāb file gave seven names. Here each one becomes a **slot every substrate must fill** before it counts as specified. **[C]**

| # | Stratum | Contract: what this layer *is* in any domain | The door | An engine module |
|---|---|---|---|---|
| 1 | **Metastratum** | the registry that names the alphabets and levels: manifest, version, schema | "a knock occurred; the stack answered" | `/.well-known/engine`, PURL manifest |
| 2 | **Epistratum** | the surface where the world lands: inputs and outputs, adapters, render/sound/haptic | the wood carries the sound | renderer, audio, touch, watch |
| 3 | **Superstratum** | the harness: admissibility rules, an automaton or grammar over words | house rules for who is answered | `harnessedPath` DFA, storylet preconditions |
| 4 | **Substratum** | the given machine: states, letters, transitions | Shut/Knocked/Ajar/Open | `machine` |
| 5 | **Hyposubstratum** | memory: the ledger and its group G (holonomy) | the hinges remember | `ledger`, `DOOR_MEMORY` |
| 6 | **Infrasubstratum** | what execution stands on: runtime, physics, data, cost model | the threshold stone | Rapier, OSM tiles, star catalogue |
| 7 | **Cryptosubstratum** | the generator: the seed, period and generator that produce the visible structure; never observed directly, only inferred | why the door exists | seed, `(period, generator)` of §6.2, latent motifs in SubstrateIO |

**The return (seven-complete) [C]:** the stack is not severed at the top. The **metastratum of level k becomes the substratum of level k+1**. Names become letters. Once VISIT is registered (metastratum, level 1), it is a letter that a level-2 machine runs on (substratum, level 2). That is the Nūn return: the tower closes on itself at every rung, so it never runs out.

**Propagation rule [C]:** a transition at stratum 4 must produce a record at 5 (memory) and be admitted by 3 (harness). It may surface at 2, it is named at 1, and it is attributable to 7. A module that cannot say what happens at each layer for one event is under-specified. That is the "one knock, seven answers" test, turned into a checklist.

---

## 4. Definitions

**D1. Plex (alphabet) [C].** Σ = (symbols, rank r ≥ 0, optional successor). `plex()`.

**D2. Word of rank r [K/C].** A map w: R → Σ from a finite box R ⊂ ℤʳ (rank 0: one cell). Rank-1 words are ordinary strings: the free monoid Σ* **[K]**. Rank-2 recognisable languages are the "picture languages" (Giammarresi & Restivo, tiling systems) **[K]**. **Retial** words replace ℤʳ by a graph. **Charted** words (D8) cover a space with overlapping local alphabets.

**D3. Denotation and channels: the ping principle.**
⟦·⟧ maps words to *behaviour traces*: what actually happens in listeners, devices, NPCs and players. **[C]** The informative alphabet is not Σ. It is Σ × C, where C is every channel the unit is modulated by: time, place, the listener's state, what the unit triggers next. **[K]** Morse code is a binary alphabet whose timing makes it richer, and information theory measures information in the *ensemble of possible messages*, not the symbol inventory (Shannon 1948). So a one-note alphabet (punctum) is not poor. The D♯ ping carries "check your phone", and its behaviour trace (hand, eyes, app, fingers) is multisensory. *Design rule:* every letter in the engine declares its channels and its downstream trace, or it carries no meaning.

**D4. Harness (superstratum) [C on K].** A finite automaton or grammar A over words. The admissible language is L(A). Words outside L(A) are **rejected, never narrated** (test C4; same rule as `STORY_GRAMMAR.md`). The harness's job is not taste. It is to shape the search space so that optimisation over L(A) is decidable, bounded and preferably precomputable (§6.3).

**D5. Machine, ledger, memory, holonomy.**
- A machine M = (states, start, transitions `from —event→ to`, with `*` = from any state). **[K]**
- Memory: a group G and a map g: events → G. For a path p = e₁…eₙ, **holonomy** hol(p) = g(e₁)·…·g(eₙ). **[C]** The kernel uses G = ℤᵈ.
- **Holonomy [K]** is the established name for exactly the phenomenon described in the brief: carry something around a closed loop and it comes back changed. Parallel transport on a curved surface, the Foucault pendulum and the quantum Berry phase (Berry 1984) are all holonomies. We borrow the structure, not the physics.
- The **ledger** is the hash-chained path, a Merkle chain like git **[K]**, plus the running holonomy.

**D6. Program identity at a declared depth [C].** Same string after seven changes: same program or not? The question has no answer until a depth is chosen:

| depth | identity = | consequence |
|---|---|---|
| `state` | the current state only | memoryless; every return is the same program |
| `holonomy` | state + hol(path) | loops whose effects cancel are forgotten; loops that leave a mark are remembered |
| `chain` | state + full ordered history | every path is a different program |

Tests C2 and C3. Three doors all end in **Shut**. The untouched door and the door that was knocked, half-opened and abandoned are the *same* program at holonomy depth (`hand` and `hesitate` cancel), but different at chain depth. The door someone crossed through is a *different* program at holonomy depth. This is the precise sense in which "reaching back to the same string can be a whole different program, given the transition language backs it": **G is the backing.**

**D7. The -ables [C].** An -able is a predicate on ledger segments. Kernel set: **runnable** (every step admissible), **closable** (ends where it began), **forgettable** (closable with trivial holonomy), **memorable** (closable with non-trivial holonomy), **replayable** (re-execution reproduces the chain). Any domain can add more (*composable, invertible, renderable, audible, walkable, teachable…*) provided each is a decidable predicate with a test.

**D8. Charts and atlases [K structure, C use].** A manifold is covered by local charts with transition maps on overlaps **[K]**. A **charted alphabet** covers a space (Earth, a codebase, a score) with local alphabets (Los Angeles streets, Hong Kong streets) and translations between them. Invariants are the quantities every chart agrees on. The turn alphabet {S, L, R, U} is chart-invariant under rotation, translation and scale (test G1). That invariance is why walks in different cities can be compared at all.

---

## 5. Alphabets of alphabets: how the tower grows

### 5.1 The tower
Σ₀ is the base alphabet. Σₖ₊₁ = Σₖ ∪ { new letters, each of which is a certified Σₖ-path }. Every new letter keeps its **unfold rule**, so `explicate` always returns it to level-k words (`unfoldWord`, test D1). **[C]** Nothing at any level is opaque, which is what makes the tower safe to hand to an AI agent. Every capability can be expanded down to verified primitives.

### 5.2 Mining (where new letters come from)
`mine` lists closable segments of a ledger, groups them by their event-word, and keeps those that recur and satisfy a chosen -able. **[C on K]** Related known methods: grammar induction from repetition (Sequitur, Nevill-Manning & Witten 1997), macro-operators in planning, and library learning (DreamCoder, Ellis et al. 2021). What is ours is the certification step: a recurrence becomes a letter only when an -able predicate, including its holonomy class, signs for it.

### 5.3 Worked example (kernel output)
One day at the door: `VISIT, VISIT, (knock hand hesitate hand decide crossed latch), VISIT`. Mining for *memorable* loops finds:

- `decide crossed` anchored at Ajar, ×4, holonomy (1,0) → promoted to **CROSSING**
- `knock hand decide crossed latch` anchored at Shut, ×3, holonomy (1,1) → promoted to **VISIT**
- mining for *forgettable* finds `hand hesitate`: a detour that leaves no trace.

Level 1 now has letters {VISIT, CROSSING}, and a level-2 machine can run days made of visits. In the engine the same mechanism promotes *a commute*, *a favour returned*, *a chord progression* or *a refactor pattern* into a letter.

---

## 6. Results the framework stands on

### 6.1 Why seven: the structure of the seven notes [K]
Place k points around a cycle (period P) by stacking a generator g: 0, g, 2g, … (mod P).
- **Three-gap theorem** (Steinhaus conjecture; proved by Sós, Surányi and Świerczkowski, 1957–59): the gaps between neighbouring points never take more than **3** distinct sizes. Test E2.
- For special k they take exactly **2** sizes. These are the *well-formed* (Myhill-property) scales (Carey & Clampitt 1989). Those k are denominators of the continued-fraction convergents and semiconvergents of g/P.
- Octave P = 1, perfect fifth g = log₂(3/2) ≈ 0.58496. The kernel finds two step sizes exactly at **k = 2, 3, 5, 7, 12, 17, 29, 41, 53** (test E1). The convergents include **7/12**: twelve fifths almost equal seven octaves (the Pythagorean comma is the "almost"). The 7-note set has step sizes 90.2 and 203.9 cents (half and whole steps). The 8-note set has three sizes and is not well-formed.
- The diatonic set is also **maximally even** (Clough & Douthett 1991): the 7 notes are spread as evenly as 7 of 12 can be.

**What the brief asked for, answered:** seven is not magic, and it is not arbitrary. It is one of the few counts at which a generator that *almost returns* (seven-complete) produces exactly two kinds of step. Two kinds of step is the minimum that allows both pattern and position (you can tell where you are). Three notes (k = 3) and five (k = 5, pentatonic) are also well-formed. One note (punctum) is legitimate too, but it gets all its information from channels (D3), not from steps.

**Domain-agnostic form [H]:** for *any* cyclic quantity in the engine, choose (period, generator) and use the well-formed counts as default granularities. Cyclic quantities include the day/night cycle, block rhythm along a street, NPC schedule slots, quest pacing and camera orbit stops. The golden generator (√5−1)/2 gives the Fibonacci counts 2, 3, 5, 8, 13, 21, 34, 55 (demo output); that is the most uniform possible stacking, and the reason it appears in phyllotaxis **[K]**. *Hypothesis to test:* players rate event schedules built on well-formed counts as more "musical" (patterned yet locatable) than equal or random spacings.

**Why a scale "breaks"** under this reading: a set that is not well-formed has three step sizes or uneven spread, so position becomes ambiguous. The rule is structural, not a matter of taste. That is the harness the brief describes: constraint as precomputed predictability, not as safety-by-blandness.

### 6.2 Harnessed paths [K]
The shortest path whose sequence of labels must belong to a regular language L(A) is solvable in polynomial time by searching the product graph G × A (Barrett, Jacob & Marathe, *SIAM J. Comput.* 2000). Kernel: `harnessedPath`. Test F1: the free shortest walk is A→E at cost 1. Under the rule "pass a kitchen, then a park", it is A→B→C→D→E at cost 8. House rules for routes, missions, tours and self-driving cars all have this shape.

Precomputation at Earth scale is also known: contraction hierarchies answer continental road-network shortest-path queries in under a millisecond after preprocessing (Geisberger et al. 2008) **[K]**.

### 6.3 The computability ledger: an honest boundary [K]
- **The travelling salesman problem stays NP-hard.** No harness makes *all* tours precomputable unless P = NP, which nobody expects. What a harness can do is restrict to tractable fragments: regular-constrained paths, bounded-length tours, fixed waypoint sets, and approximations with guarantees (Christofides; Arora's PTAS for Euclidean TSP).
- **Non-computable things do not become computable.** The halting problem stays undecidable inside any framework. The real move, and the valuable one, is **choosing decidable fragments on purpose**: regular harnesses, finite charts, bounded words. Then label everything outside them as *outside*, not *impossible*.
- So "all paths of Earth" means: an infinite *space* generated from finite data and rules (a recipe), queried through decidable harnesses, with results cached as they are realised. It is the same compression principle as `STORY_GRAMMAR.md` §Compression, generalised.

---

## 7. Applicata: the adapter contract (how any domain plugs in)

A **computation adapter** for domain X supplies seven fields, one per stratum **[C]**:

```
applicata X = {
  meta:   { name, version, levels }                         // 1 metastratum
  epi:    { inputs, outputs, channels }                     // 2 epistratum  (D3)
  super:  { harness: automaton | grammar, costs }           // 3 superstratum (D4)
  sub:    { alphabet: plex, machine }                       // 4 substratum  (D1, D5)
  hypo:   { memoryGroup, eventMap, identityDepth }          // 5 hyposubstratum (D5, D6)
  infra:  { dataSources, runtime, budgets }                 // 6 infrasubstratum
  crypto: { seed, period?, generator?, chartMap? }          // 7 cryptosubstratum (§6.1, D8)
}
```

An adapter is **conformant** when: its words round-trip through explicate/implicate; its harness rejects with diagnostics; replay reproduces the chain; and it declares its identity depth. Those four checks are the kernel tests A–F, run against the adapter. A *computation engine* is the runtime that accepts any conformant applicata. Its product is computations: certified paths, promoted letters, harnessed optima.

---

## 8. Applications

| Domain | Alphabet (rank) | Harness | Memory / identity | Crypto (generator) | Status |
|---|---|---|---|---|---|
| **Music** | notes × durations (complicate, rank 1); scores rank 2 | voice-leading rules as automata | motif recurrence | period = octave, g = fifth | [K] + [C] |
| **Door / any UI widget** | events (rank 1) | transitions | holonomy ℤ² | — | kernel |
| **Walking a city** | turn × degree (retial) | house rules, opening hours | journeys promoted to letters | street-grid generator | kernel (synthetic) |
| **Driving / self-driving** | road segments | regular-constrained routing | trip ledger | traffic periodicity | [K] |
| **Flight** | waypoints / airways (retial on the sphere) | published routes, altitudes | flight plan as word | great circles | [K] data |
| **Sky** | stars as vertices on the celestial sphere | visibility (location, epoch) | precession phase | precession ~25,800 yr | [K] + [H] |
| **NPC society** | intents × relations (complicate) | storylet preconditions | relationship holonomy | schedule (P, g) | [C] |
| **Code (PURL / SEURL / SubstrateIO)** | edit operations | type system, capability manifest | ledger = compile log | repo seed | [C] |
| **Sound synthesis** | modal partials (punctum → simplex) | spectral constraints | timbre state | harmonic series | [K] |
| **Chemistry nomenclature** | IUPAC morphemes | IUPAC grammar | — | — | [K] |
| **"Quantum" layer** | distributions over letters | constraint propagation | collapse record | — | [C] metaphor |

Notes on the rows that matter most for HOMELESS:

**8.1 Tri-world walks [C + H; mechanism tested].** Encode every walk as a chart-invariant word (D8). Index each city's **walk lexicon**. A word present in several lexicons is a **shared walk**, and every city carries a witness route. On seeded synthetic cities (test G2, demo), the number of words shared by all three cities is 127 at 3 turns, 130 at 4, 48 at 5, and **2 at 6**. The 6-turn lexicons hold 10,200, 1,802 and 3,695 words. Each lexicon keeps growing as walks lengthen, while the shared set collapses. So a shared walk is a genuinely rare find, and the rarity can be tuned by word length and by how rich the alphabet is. In the game: a member walks a street. If that walk-word is in the shared lexicon of a set of cities, the doppelgänger routes in Los Angeles, Hong Kong and Dubai light up, and the tri-world walk is discovered.
*Why it is "real":* anyone can recompute the match from the public map data and the published alphabet. A discovery in this framework is a **reproducible certificate**, not an assertion. *Next step:* an OpenStreetMap adapter (ODbL licence: attribution and share-alike obligations go in `licenses.lock.json`) in place of `syntheticCity`. Hypothesis: real cities share fewer long words than synthetic grids, because their fabrics differ more.

**8.2 Ground and sky share one geometry [K].** A nautical mile is defined as 1,852 m and originated as one minute of arc of latitude. A knot measures *angle per hour* on the sphere, which is why aviation and navigation use it. Stars sit on the celestial sphere, measured in the same angular units. So walk-words on the ground and path-words through star fields can be written in the *same* alphabet. A walk that also spells a sky path for the player's location and epoch can raise a constellation. Because of precession (~25,800-year cycle) and stellar proper motion, the sky configuration over a place is a **timestamp**: given a catalogue and a sky, the epoch can be estimated by best fit. (Claims that particular cave paintings encode star dates are a debated proposal, not settled fact.) *Data reality:* the Gaia DR3 catalogue holds about 1.8 billion stars. The "two trillion" figure is an older estimate of the number of *galaxies* in the observable universe. 1.8 billion is plenty.

**8.3 Latin as a programming language for structure [K].** The brief asked whether nomenclature could be a functional language rather than a dictionary. In chemistry it already is: an IUPAC name is a compositional program that constructs a molecule, and the open-source parser OPSIN (Lowe et al. 2011) executes such names into structures. Our strata names (meta-, epi-, super-, sub-, hypo-, infra-, crypto-) and fold names (ex-, in-, com-, re-, ad-plicate) are used the same way: **the prefixes are operators.**

**8.4 The "quantum" layer, honestly [C].** "Collapsible forms" in the engine are classical: a cell holds a *set or distribution* of admissible letters, and observation (a player arriving) collapses it by constraint propagation. This is the Wave Function Collapse algorithm (Gumin 2016) and lazy procedural generation. The word "quantum" is metaphor here unless amplitudes actually interfere. A real quantum alphabet (basis states, superposed words, unitary transitions) can be added as its own applicata later, with the same conformance tests.

**8.5 NPCs that are "humanary" [C + H].** An NPC's policy is a machine over intent × relation letters. Its memory group records relationship holonomy, so a favour-then-betrayal loop does not return the relationship to zero. Cohorts that steer a player are a level-2 machine whose letters are promoted level-1 behaviours. Ethics guard (from the game bible): steering serves discovery, never compulsion. Every level-2 cohort letter must be explainable by unfolding.

---

## 9. Special generativity: what the name has to earn

Special relativity earned its name with two postulates and an invariant (the laws are the same in every inertial frame; the speed of light is the same for every observer). If **special generativity** is to be more than a name, it needs the same shape. Proposed postulates, all **[H]**:

1. **Chart invariance.** The generative law of a substrate is stated only in quantities preserved by every admissible re-charting (change of alphabet). *Testable:* two adapters for the same domain built on different alphabets must agree on all invariants (walk-word lexicons, well-formed counts, holonomy classes).
2. **Closure constant.** Every complete substrate has a period that all charts agree on: the octave, the day, the precession cycle. Generation is measured relative to it.
3. **Memory postulate.** Program identity is (state, holonomy), never state alone, and the memory group is declared, never implicit.

If these survive tests across several unrelated domains (music, maps and code at minimum), the name is earned. If one fails, record the counterexample in `docs/EXPERIMENT_REGISTER.md`. A refutation is a result.

---

## 10. Engine integration (for the Codex mission)

- Add `packages/plicate` (port `prototype/plicate.mjs` to TypeScript, keeping the tests as the conformance suite).
- Schemas: `schemas/plex.schema.json`, `schemas/applicata.schema.json` (§7), `schemas/ledger-entry.schema.json` (from, event, to, holonomyDelta, chainHash).
- SubstrateIO port: the ledger *is* SubstrateIO's transition trace. `mine` + `promote` feed its motif-mining step. Promoted letters keep status `hypothesis` until held-out seeds replicate them.
- PURL / SEURL port: every promoted letter gets a stable address, its unfold rule and its certificate; GET returns them without mutation. Writes (`promote`) require explicit authorisation, as in `REPO_INTEGRATION.md`.
- Every engine module passes the **seven-strata checklist** (§3) before merge.

### Acceptance — done
A1 closure · B1/B2 fold round-trip and refusal (ranks 1–2) · C1–C4 latch, holonomy identity, inadmissibility · D1 mining and promotion · E1/E2 well-formed counts and three-gap · F1 harnessed path · G1/G2 chart invariance and tri-world rarity.

### Acceptance — next
1. OSM adapter: tri-world walk on real data for three named districts, with licence record.
2. Sky adapter: Gaia/Hipparcos subset; recover an epoch from a sky to within a stated tolerance.
3. Music applicata passes the same conformance suite as the door (the first test of postulate 1).
4. Rank-3 explicate/implicate (triplex) round-trip.
5. Level-2 machine running on promoted letters, with a test that unfolding reproduces the level-0 chain hash.

---

## 11. References
Barrett, Jacob & Marathe, "Formal-language-constrained path problems," *SIAM J. Comput.* 30 (2000) · Berry, "Quantal phase factors accompanying adiabatic changes," *Proc. R. Soc. A* 392 (1984) · Carey & Clampitt, "Aspects of well-formed scales," *Music Theory Spectrum* 11 (1989) · Clough & Douthett, "Maximally even sets," *J. Music Theory* 35 (1991) · Ellis et al., "DreamCoder," *PLDI* (2021) · Geisberger et al., "Contraction hierarchies," *WEA* (2008) · Giammarresi & Restivo, "Two-dimensional languages," *Handbook of Formal Languages* vol. 3 (1997) · Gumin, *WaveFunctionCollapse* (2016) · Lindenmayer, "Mathematical models for cellular interaction in development," *J. Theor. Biol.* 18 (1968) · Lowe et al., "Chemical name to structure: OPSIN," *J. Chem. Inf. Model.* 51 (2011) · Nevill-Manning & Witten, "Identifying hierarchical structure in sequences," *JAIR* 7 (1997) · Shannon, "A mathematical theory of communication" (1948) · Sós (1958) and Świerczkowski (1958) on the three-distance theorem · Gaia Collaboration, *Gaia DR3* (2022).

*Seven-complete: the tower returns to itself at every level, so it does not run out.*
