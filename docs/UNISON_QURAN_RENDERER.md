# SURFACE — First UNISON Qur'an rendering surface / 0.1

**Status:** Independently usable offline Arabic source-review renderer + native C++ scene-carrier contract; **not yet wired into Android/native Surface ink**. No build, test suite or Android-run gate executed under the 2026-10-25 no-build handoff. Preserves current SURFACE renderer and physics baseline.

## 1. Scope

Owner: the first Qur'an visual treatment is not an astronomy-themed video. It is an **addressable, non-moving, Arabic-first reader** that exposes canonical source spelling, rasm view, disconnected-letter names, word addresses, pronunciation evidence and an optional GLASS QITṬ register layer. All are simultaneous *typed* layers. A future layer may add sky charts, wave equations, and driven physics, but no literal Qur'an→star coordinate correspondence is asserted.

This is a cross-repo capability:
- **MUQRI**: canonical Uthmani/reading data and tajwīd, source-aware phonemizer, measured letter/word/rule outputs, model reliabilities. No modification of recitation verdicts.
- **GLASS**: CALRC QITṬ 28-letter native register, typed ṢIFR, positional lift, cycle/return topology; owner-proposed numerical research.
- **UNISON**: source→indexed AST→Qur'an frame→(optional) native value and address→read-only typed scene.
- **SURFACE**: source-preserving Arabic geometry/layout and scientific observation plane. Current native CPU raster draws fields, lines, stars and PPM, **not** professionally shaped Arabic script. The new scene-carrier header defines the boundary without falsifying a complete device feature.

## 2. Minimal working flow

Produce an immutable \`surface.unison.quran-scene/0.1\` JSON object with \`muqri/unison/surface_scene.py::quran_surface_scene(...)\`. The renderer consumes *only* the source-certified scene.

A standalone checked-in fixture is at \`examples/unison_quran_scene.json\`, representing **الم**, source-marked **2:1**, with three separate letter-name tokens and native QITṬ sum 71 (1+30+40). It is an illustrative **scientific source view**, not a fully authenticated verse edition, audio alignment or certified Qirāʾāt result.

To generate the first static reading surface when verification/builds are authorized:

~~~sh
python3 tools/unison_quran_preview.py \
  --scene examples/unison_quran_scene.json \
  --output build/previews/unison_quran.html
~~~

Open the generated file in an Arabic shaping-capable browser. It is a single-file, offline HTML source-review page. Its Arabic text is real, not fake ASCII shapes. The page includes word spans and an initial-letter analysis card, but no external fonts, scripts or network access. Every user-provided scene string is escaped. HTML output is a review **artifact**, not a shipped native Android Surface screen.

To produce a new scene in MUQRI under a correctly configured Python environment:

~~~python
from unison.surface_scene import quran_surface_scene, LogicalClock
scene = quran_surface_scene(
    surah=2, ayah=1, raw_text="الم", edition="declared-source-edition",
    role="verse_initial_candidate", clock=LogicalClock(epoch_ns=0, tick_ns=1),
)
~~~

Serialize this returned mapping with \`json.dumps(..., ensure_ascii=False)\`. The scene importer independently checks SHA-256, byte spans and record shape. The actual newverse source must be supplied from MUQRI's pinned corpus rather than guessed from an English translation or a numeric registry.

## 3. Scientific data layers

| View | Input and rule | What the view does **not** mean |
|---|---|---|
| Source Uthmani | Exact source bytes, edition, surah, ayah, digests | No invisible spelling substitutions |
| Rasm skeleton | Versioned optional noncanonical marked-character projection | Not authentic historical Uthmani rasm |
| Indexed word AST | Exact UTF-8 byte offset, token/glyph nodes | Not physical memory address or semantic value |
| Muqatta'at names | MUQRI's letters and reading method; context required | Not ordinary syllabic word reading |
| Phoneme/articulation | MUQRI measured or declared reference, wajh/waqf | Not invented audio or generic G2P |
| QITṬ native value | 28-letter registry and reversible typed address | Not verified divine/linguistic hidden code |
| Semantic morphology | Sourced lexicon/era/dialect/readings | Not automatically inferred by shared letters |
| Sky observation | Star survey ID, RA/Dec, frame, epoch, source | Not a verse decoding or live universe dynamics |
| Mechanical/acoustic | Equation, units, parameters, clock, uncertainty | Not measured motion unless externally observed |
| Quantum | Basis, complex amplitude, calibrated channel, measurement result | Not interchangeable with bit glyphs or star positions |

## 4. Render pass architecture

Proposed parallel, independently versioned passes:

~~~text
BEGIN_SCENE
  ADMIT_SOURCE(source_sha256, edition, surah, ayah)
  DRAW_ARABIC_TEXT(exact_source, rtl, approved_platform_shaper)
  DRAW_INDEXED_SPANS(word_ID, byte_start, byte_end)
  OPTIONAL(DRAW_LETTER_NAME_FRAME, MUQRI_source_profile)
  OPTIONAL(DRAW_QITT_NATIVE_REGISTERS, qitt/0.1)
  OPTIONAL(DRAW_RASM_PROJECTION, explicitly_noncanonical)
  OPTIONAL(DRAW_RECORDED_PHONEMES, measured_audio_witness)
  OPTIONAL(DRAW_ASTRONOMY, catalog_frame_epoch_uncertainty)
  SEAL_SCENE(source_digest, clock, rendering_profile)
END_SCENE
~~~

All passes use source IDs and read-only scene records. A visible Arabic glyph and its UTF-8 bytes are *not* interchangeable because Arabic shaping is contextual. Source order and visual order may differ under bi-directional text layout. Position in source bytes, index in token sequence, glyph index in a shaped font, and x/y screen pixels are distinct address types.

The new \`include/surface/quran_scene.hpp\` declares \`Scene\`, \`SourceWord\`, \`StarObservation\` and \`ShapedGlyphRun\`. It defines validation at the C++ boundary, but no native painter consumes this carrier yet. Proper Android integration will need a licensed/system Arabic-shaping backend or platform text service, device evidence and lifecycle synchronization before it can replace the prototype view.

## 5. The 14-letter research viewport

Exactly fourteen distinct letters occur across the 14 recognized muqatta'at sequence forms in MUQRI's \`app/tajweed_rules/parser.py\`: ا، ل، م، ص، ر، ك، ه، ي، ع، ط، س، ح، ق، ن. These form a **research projection**, not a new canonical Qur'anic text edition.

Study:
- sequence identity and whether it appears as a separately numbered ayah under the source edition;
- letter-name utterance segmentation, harakat and madd classification;
- immediate adjacent ayah/phrase and stop boundaries;
- root/shape comparisons where lexical words are *different* from disconnected letters;
- letter occurrence, index, native and position-lifted values with collision warnings;
- selected claims about ALIF/LIFF, ṢIFR, hidden Mīm, Raqīm and speaker continuity as **hypotheses**, with explicit counterexamples and citation coordinates in the verse corpus.

An observed interaction between rendered source and audio is evidence of alignment, not evidence of a historical numerical encoding.

## 6. HyperRuler, time, and cosmic observation

Define scene components \`(identity, domain, units, coordinate_frame, epoch, clock, model, observer, uncertainty, source)\`. A 1–7-axis HyperRuler is a visualization of chosen function-space dimensions; it does not assert seven physical spatial dimensions. 2D projections are many-to-one without a retained index/embedding.

GLASS gives discrete bit and QITṬ address state; SURFACE supplies finite classical/physical simulations. The quantum carrier, if admitted later, is a separately tested vector/density/channel model with classical control and measurement. The two are not “infinite” in a way that makes unproven equations true; actual representations have finite memory and resource bounds.

SURFACE currently reports a 10k-source Gaia directional slice. A desired billion-source catalogue will require database tiling, culling/LOD and decoupled update streams. Pulsar rates belong to the subset of objects with actual measured periodic timing, not to every star. A deterministic \`LogicalClock\` emits reproducible tick labels; it does not claim physically complete knowledge of stellar energy states.

## 7. Baseline preservation and gates

This commission does NOT change:
- \`src/renderer.cpp\`, \`include/surface/renderer.hpp\`, existing sessions, checkpoint or Android lifecycle;
- the archived PHANTOM/V3 scientific sources and released APK;
- MUQRI's \`measurements/1\` scoring, text source, Tajwid interpretations or saved audio.

Remaining separate acceptance gates are: importer/profile parity with MUQRI; verified Uthmani source edition; native font shaping with exact source-to-glyph cluster hit testing; Android device launch and screenshots; bounded frame timing and native renderer tests; original source evidence and negative control tests; optional astronomy time/frame provenance. No gate is declared passed merely because this source documentation and prototype code were committed.
