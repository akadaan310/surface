# UCG — Universal Computational Grammar
### A science of grammars, begun with a lettered alphabet (the periodic table), a geometric alphabet (organic forms), and the common mathematics
*Direction: Abed Kadaan. Research, implementation and measurements: this package (`ucg/`). v0.1, 2026-10-23.*
*Labels: **[K]** established and cited · **[C]** construction (a definition we choose) · **[H]** hypothesis · **[M]** measured by a script in `experiments/`, sealed in `results/proleptic_ledger.jsonl`.*

---

## 0. What "universal" may and may not mean here

A *universal computational grammar* is **not** a claim that one grammar generates every truth. It is a claim about **form**: every subject we admit is presented as the same eight-field object, the kernel of the Relational Generativity foundation,

$$\mathcal K=(A,\;Q,\;\mathcal O,\;\delta,\;[\![\cdot]\!],\;\Pi,\;I,\;V)$$

that is, alphabet, states, operators, transitions, denotation, projections, invariants and verification. Each subject also gets a fixed set of *questions* we ask of it:
- What are its letters?
- What makes a word admissible?
- What do admissible words mean?
- What does it refuse, and why?
- What does it predict before it is shown?

Universality is the uniformity of the interface and the protocol. Content stays plural.

---

## 1. Two kinds of alphabet, and why the periodic table comes first

| Kind | Letters | Words | Symmetry of a word | First instance |
|---|---|---|---|---|
| **Lettered** (non-phonetic symbols) | tokens with computed coordinates | multisets / graphs of letters | relabelling | the periodic table: Σ_E = {H, He, …, Og} |
| **Geometric** (forms) | shapes with ports | assemblies of shapes | the shape's own group (Dₙ for an n-gon) | organic rings and skeletons |

The periodic table is the right first alphabet because it is **not phonetic**. "O" is not a sound; it is a position. The bias the commission asked us to avoid is avoided by construction: the generator reads **only Z**. Everything else (period, block, group, valence, ion charge) is *derived* by a grammar and then witnessed.

The Chemistratum warning is honoured exactly. Symbols alone do not imply valence ("HO" is not H₂O). The valence here comes from Z through the aufbau grammar, not from the spelling.

---

## 2. Proleptics: the science of predicting before witnessing [C]

*Prolepsis* (Gk. πρόληψις, a "taking-beforehand") is the Epicurean name for a preconception that precedes the experience it later recognises. We make it a protocol:

1. **GENERATE.** The generator declares what it is allowed to read.
2. **SEAL.** Predictions are canonicalised, SHA-256 hashed and appended to a hash-chained ledger *before any witness byte is read*.
3. **WITNESS.** The witness is loaded and its hash is recorded.
4. **RECOGNISE.** Precision, recall and agreement are computed against the sealed bytes.
5. **ACCOUNT.**
   - *Misses* (predicted, not witnessed) are candidate **in-grammar**: what the world refuses that the grammar admits.
   - *Gaps* (witnessed, not predicted) are grammar deficits.
   - A grammar amended after a witness is **re-sealed and labelled witness-informed**, never presented as blind.

This is the "unsupervised, then supervised" loop the commission described, given an audit trail. It is related to pre-registration in the empirical sciences and to commit–reveal schemes in cryptography [K]. What is ours is its use as the standard gate for every grammar in UCG.

---

## 3. Results [M]

### 3.1 E01 — The periodic table from Z alone
The grammar: aufbau/Madelung ordering (n + l, then n) over orbital letters s, p, d, f → configuration word → (period, block, group) → valence electrons → admissible valences (octet; expanded octet for period ≥ 3) → ionic charge.

| Witness | Result |
|---|---|
| Printed table: period | **118/118** |
| Printed table: block | **118/118** |
| Printed table: group (s, p, d) | **100%** |
| Printed configuration | **98/118**. The 20 misses are exactly the textbook aufbau exceptions: Cr, Cu, Nb, Mo, Ru, Rh, Pd, Ag, La, Ce, Gd, Pt, Au, Ac, Th, Pa, U, Np, Cm, Lr |
| RDKit curated valences (34 main-group elements, Z ≤ 54) | **33/34**. The miss is Sn(II), the inert-pair effect |

*Reading.* The table's layout is the image of one grammar. Its exceptions are a small, named in-grammar (half-filled and filled d-subshell stabilisation; inert pairs).

### 3.2 E02 — Molecules as words, predicted blind
The grammar: connected bond multigraphs (orders 1–3) on letters {C, N, O, F}, with each letter's bond sum ≤ its primary valence and hydrogens filling the rest. That's 738 words with ≤ 4 heavy atoms. The idea is GDB's (Fink & Reymond 2005–07 [K]), rebuilt minimally.

| Witness | Result |
|---|---|
| QM9 (GDB-9 subset, via the G4MP2 dataset), ≤ 4 heavy atoms | **recall 48/48 = 100%**, precision 6.5% |
| In-grammar mined as motifs QM9 *never* shows | O–O, N–N, N–O, N=N, F–N, F–O, cumulenes, double/triple bonds inside small rings |
| Grammar × in-grammar | **recall still 100%, precision 33%** |
| 25 textbook molecules | **24/25 predicted** (CF₄ has 5 heavy atoms, outside the declared bound) |
| …the same 25 under the QM9-learned in-grammar | **8 real molecules refused**: CO₂, H₂O₂, N₂H₄, NH₂OH, N₂H₂, ketene, NF₃, OF₂ |

*Two findings.* (i) H₂O is the first word the grammar writes over {H, O}. (ii) **A learned in-grammar inherits its witness's selection bias.** QM9 is GDB's filtered universe, not chemistry. Rule UCG-W1 follows: an in-grammar is labelled with the witness it was learned from and is never promoted to "impossible" without a second, independent witness.

### 3.3 E03 — Forms as an alphabet
- **Trees.** Free trees of max degree 4, canonicalised by AHU codes at the centre: **1, 1, 1, 2, 3, 5, 9, 18, 35, 75, 159, 355** for n = 1..12. That is **identical to Cayley's alkane counts (OEIS A000602)**, and RDKit's independent canonicaliser agrees at n = 10.
- **Polygons.** A ring is a cyclic word of (atom, bond) letters read up to the dihedral group Dₙ. Both Kekulé words of benzene lie in **one orbit**, so resonance is a declared group-orbit identification (a Plicastratum fold).
- **Counting witness.** The naive bracelet formula was the *wrong* witness model (618 vs 666 at n = 4). The Pólya count for vertex-and-edge colourings (two reflection-axis types for even n) matches enumeration **exactly for n = 3..6**: 120, 618, 3,536, 22,668. A wrong witness is a result too.
- **Hückel 4k+2** on 1,857 admissible 5- and 6-ring words: **1,857/1,857 agreement with RDKit**, after one witness-informed rule (cumulated =C= bonds are orthogonal, so they do not form one conjugated cycle). **21/21 correct on the Chemistratum atlas monocycles.**

### 3.4 E04 — Names are programs
- **IUPAC systematic element names** (nil-un-bi-tri-quad-pent-hex-sept-oct-enn + ium, with elisions): 17/17 historical placeholder names and 5/5 symbols reproduced. Z ↔ name round-trips and is injective for Z = 1..999.
- **Alkane names (IUPAC P-44 subset).** The 40 generated names for C1–C8 equal the 40 textbook names exactly, and the inverse parser rebuilds all 40 structures. The parser separates *inadmissible* ("2,2,2-trimethylpropane": a carbon with 5 bonds), *unknown stem*, and *admissible but not normal form* ("2-ethylpentane" → 3-methylhexane).
- **Morpheme custody.** *non-* is Latin (nonus) among Greek numerals, *undec-* is a Latin+Greek hybrid, *but-* comes from Latin butyrum, and *-yl* from Greek hyle. The chain of custody is data (WAZNOMIA discipline).

### 3.5 E05 — The common mathematics as grammars

| Pillar | Grammar | Witness | Result |
|---|---|---|---|
| Differentiation | rewrite rules with derivation words | sympy.diff | **400/400** |
| Higher derivatives | orbits of D: complete (eˣ: period 1; sin: period 4), severed (polynomials), open (ln, tan, sin x²) | sympy symbolic annihilation | characteristic words **10/10**: sin → D²+1; eˣ sin x → D²−2D+2; x·e²ˣ·cos x → ((D−2)²+1)²; sin 2x + cos 3x → (D²+4)(D²+9) |
| Integration (textbook 30) | state machines TABLE / LINEARITY / USUB / PARTS (LIATE, cycle-closing) / PARTIAL_FRACTIONS + VERIFY | sympy.diff of our answers | **30/30**, 0.03 s (sympy 0.6 s) |
| Integration (non-elementary 5) | REFUSE | sympy returns only special functions | **5/5 refused** |
| Integration (150 generated, elementary by construction) | same | sympy | **124/150 solved, 124/124 verified**, 1.1 s (sympy 138/150, 32 s) |
| Transcendental impact | per-class cost | — | algebraic 91% solved, 44 states; **trig 72%, 122 states** (≈2.8× work, ≈3× failure) |
| ODE methods | Butcher trees, Φ(t) = 1/γ(t) | OEIS A000081; empirical convergence | trees 1, 1, 2, 4, 9, 20, 48; **predicted order = measured slope, 8/8** (broken RK4: 1 vs 0.95) |
| Groups | productions Zₙ, ×, ⋊ (cyclic), dicyclic, ⋊ (general) | OEIS A000001 | G0 gaps at 8, 12 (Q₈, A₄) → G1 fixes 8 → **G2 matches all 15** |
| Homology | chains, ∂ with ∂∂ = 0 | known homology | S², T², RP², Klein bottle **correct over ℚ and F₂** |
| Linear systems | Gauss–Jordan machine | — | unique / **kernel failure** / **image failure**, the same two failures as 0/0 and 1/0 |

**The answer to "what do trigonometric and transcendental functions do to calculus":**
- Under D, the exponential polynomials, i.e. sums of xᵏ·e^{ax}·(sin|cos)(bx) (the trig-and-exp transcendental functions that behave), are **exactly** the functions whose orbit spans a finite space. They therefore have a characteristic word; this is linear ODE theory with constant coefficients [K].
- Everything else (ln, tan, atan, sin x², √x) drifts.
- Under integration, the boundary is Liouville's theorem [K]. Our machines reproduce the boundary operationally: they refuse exactly the classical non-elementary cases, and the measured cost of trig integrands is about 2.8× that of algebraic ones.

---

## 4. What the experiments teach about grammars in general [C/H]

1. **A table is a projection of a grammar.** The periodic table is the image of the aufbau grammar. The alkane counts are the image of a degree-bounded tree grammar. The table of integrals is the TABLE state of the integration machine.
2. **Exceptions are the in-grammar, and they are small and nameable.** These include the 20 aufbau exceptions, Sn(II), cumulated bonds, and Q₈/A₄ as non-split extensions.
3. **The witness can be wrong.** The bracelet formula was wrong, and QM9 is not chemistry. Witnesses are graded and versioned like grammars.
4. **Refusal is an output.** Integration REFUSE, the inadmissible name, image/kernel failure: every machine has a typed "no".
5. **Orbits classify.** Complete, severed and open, the Plicastratum closure classes, classify D-orbits exactly. **[H]** They classify the iteration of *any* operator in UCG (fold, rename, differentiate, reduce).
6. **Grammar growth is witness-driven.** G0 → G1 → G2 for groups, and the Hückel amendment, are the loop the Codex commission formalises.

## 5. Limits (stated)
- Witness constants transcribed from OEIS and textbooks are labelled as transcriptions. The ideal is to fetch them with hashes.
- The bracket simplifier is partial. Identity is witnessed numerically on generic points (a randomised test, not a proof).
- The group invariants used to separate isomorphism classes are sufficient for n ≤ 15. They are not complete for n = 16.
- Organic grammar: neutral closed-shell molecules only; no charges, radicals or stereochemistry.
- Integration: no Risch algorithm. The machines are textbook methods plus verification.
- sympy and RDKit are **witnesses only**. No result is taken from them.

## References (selection)
Madelung 1936; Klechkowski 1962 · Fink & Reymond 2007; Ruddigkeit et al. 2012 (GDB) · Ramakrishnan et al. 2014 (QM9) · Cayley 1875; OEIS A000602, A000081, A000001 · Pólya 1937 · Hückel 1931 · Aho, Hopcroft & Ullman 1974 · IUPAC 1978 (systematic element names) · IUPAC 2013 Blue Book P-44 · Liouville 1835; Risch 1969 · Butcher 1963, 2016 · Hatcher, *Algebraic Topology* (2002) · Pre-registration (Nosek et al. 2018).
