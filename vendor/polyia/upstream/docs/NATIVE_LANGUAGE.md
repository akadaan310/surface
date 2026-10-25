# Bounded Poly IA native language increment

This initial D-COMPILER increment is authorized implementation work. It does not complete PIA-085–096 or replace any retained acceptance threshold.

The subsequent [typed-term and quantitative increment](NATIVE_QUANTITATIVE.md) adds public expression parsing, canonical printing and partial normalization, and records 10,000 term checks plus three computational machines with 1,000 inputs each. It preserves the existing serialized program representation. Its finite evidence does not complete the wider compiler mandate.

Design: a versioned parenthesized `.polyia` grammar is lexed and parsed into a typed AST, lowered to typed stack instructions, and executed by a bounded pure VM. A separate recursive AST evaluator checks the returned observable values. JSON serializes the resulting package; it is not the source language. Fixed rational, univariate polynomial and literal text operations demonstrate nonlinguistic and linguistic lowering through the same contract. Unknown syntax, types, operations, effects, budget excess and altered packages are refusals.

Alternatives considered: directly interpreting JSON would violate POLY-C-017/018; adding a full general-purpose language would expand the unreviewed effect/termination surface. The bounded typed bytecode profile implements the assigned increment and leaves modules, general generators, native/WASM backends and tool brokers open.

Plan: write positive/adverse behavior tests and observe failures; implement lexer/parser/typechecker and lowering; implement bounded bytecode and a separately coded reference evaluator; test serialization, tampering, exact arithmetic, UTF-8 locations and a clean-process package invocation; run the complete Python suite. Record actual results and scope below after verification.

Source basis: GOD_SEED PIA-085–096; SCIENTIFIC_FOUNDATIONS SF-08; SRC-POLYIA96 clauses 009–024, 049–064, 079–084, 094; SRC-UCG156 sections 019, 039, 044, 084, 124, 132, 154. The exact inherited grammar and technical treatise are preserved under `sources/expanded/POLYIA_FOUNDATION_V0_1/POLYIA_FOUNDATION_V0_1/{schemas/POLYIA_PIR_EBNF.md,docs/TECHNICAL_TREATISE.md,seed_packets/LANGUAGE_AND_SPECIALISTS.md}`. This new profile is an explicit extension, not an assertion that the older metadata-only grammar or PILLAR9 semantics are interchangeable.

## Source grammar and semantics

```ebnf
program   = "(" "commission" profile [budget] {statement} ")" ;
profile   = "(" "profile" '"polyia.native/0.1"' ")" ;
budget    = "(" "budget" INTEGER ")" ;
statement = "(" "let" NAME TYPE expression ")"
          | "(" "emit" NAME expression ")" ;
expression = RATIONAL | STRING | NAME | "(" OPERATOR {expression} ")" ;
TYPE      = "Rational" | "Polynomial" | "Division" | "Text" ;
RATIONAL  = ["-"] DIGIT {DIGIT} ["/" DIGIT {DIGIT}] ;
```

Names are ASCII letters/underscore followed by letters, digits, underscore, dot or hyphen. Comments start with `;` and end at a newline. Strings preserve Unicode scalar values, with exactly `\"`, `\\`, and `\n` escapes. Whitespace outside strings is ASCII space/tab/CR/LF. All input must parse; trailing tokens and unknown syntax are refusals. The required profile distinguishes this executable grammar from the preserved v0.1 metadata grammar; this is neither Lisp nor P9.

Bindings are immutable, ordered, explicitly typed and cannot refer forward. At least one uniquely named output is required. Polynomial coefficients are ascending degree over Q[x]; trailing zeros are removed, and zero is `["0"]`. `Division` retains quotient and remainder separately. Inputs are closed literals/bindings: no implicit environment, state, file, network or model access.

| Operation | Input types | Result | Semantics |
| --- | --- | --- | --- |
| `add`, `sub`, `mul` | Rational, Rational | Rational | Exact rational arithmetic |
| `poly` | One or more Rational | Polynomial | Ascending coefficients |
| `padd`, `pmul` | Polynomial, Polynomial | Polynomial | Polynomial addition/product |
| `derivative` | Polynomial | Polynomial | Formal derivative over Q[x] |
| `evaluate` | Polynomial, Rational | Rational | Exact evaluation |
| `divmod` | Polynomial, Polynomial | Division | Euclidean division; zero divisor refused |
| `quotient`, `remainder` | Division | Polynomial | Explicit division projection |
| `concat` | Text, Text | Text | Exact concatenation |
| `replace` | Text, Text, Text | Text | Nonoverlapping literal substitution; empty pattern refused |

Text substitution is an authored lexical transformation. It does not establish translation, synonymy, semantic equivalence, morphology or attestation. Polynomial division does not implicitly simplify a rational function or discard excluded denominator roots.

## API, package and execution

`compile_program(source: str) -> dict` returns `{ok: true, program: ...}`. The package contains retained source and SHA-256, source references, typed AST with half-open character/UTF-8 byte spans and one-based line/column, typed stack instructions, input/output ports, effects, contexts/assumptions, dependencies, resource bounds, costs and outstanding proof obligations. `CONST`, `LOAD`, `CALL`, `STORE`, and `EMIT` are executable stack instructions. The package SHA-256 uses a domain-separated canonical JSON encoding.

`execute_program(program: dict) -> dict` revalidates the complete package against trusted lowering of its retained source before executing it. Changing the code, types, spans, limits, effects or digest without matching compilation is refused. This is structural admission to the fixed pure profile, not cryptographic author authorization or permission for external effects. Result includes typed outputs, source/package identity, measured deterministic VM work units and differential verification. The service/release receipt must additionally capture the actual `polyia/native.py` bytes/digest; profile version alone is not a code signature.

Both APIs return `{ok: false, error: {code, message, span?}}` on declared refusal. Compile failures expose source positions where applicable. Examples include `TYPE_ERROR`, `UNKNOWN_OPERATION`, `UNBOUND_NAME`, `ZERO_DENOMINATOR`, `ZERO_POLYNOMIAL`, `PACKAGE_MISMATCH` and specific resource-budget codes. They do not execute source-embedded commands or select dynamic handlers.

The independent AST evaluator uses different control flow: polynomial multiplication sums coefficient diagonals, division solves coefficient equations, evaluation uses explicit powers, and substitution uses split/join. The VM uses stack instructions, accumulation, iterative long division, Horner evaluation and replace. They share the validated frontend, encoding helpers and Python `Fraction`; agreement is explicitly a differential check with shared dependencies, not proof or a blind external witness.

```python
import json
from pathlib import Path
from polyia.native import compile_program, execute_program

compiled = compile_program(Path("examples/native/polynomial.polyia").read_text())
assert compiled["ok"], compiled
Path("/tmp/polynomial.package.json").write_text(json.dumps(compiled["program"]))
print(execute_program(compiled["program"]))
```

The CLI explicitly reads an operator-selected file; this effect is outside the generated program. `python -B polyia/native.py compile FILE.polyia` prints the compilation result envelope. `python -B polyia/native.py run PACKAGE.json` consumes the raw `program` object saved above and prints execution results. Exit status is 0 for success, 2 for refusal. Copying just `native.py` and the serialized package to a clean directory works with `python -I -B native.py run PACKAGE.json`; no repository imports or third-party packages are required.

## Bounds and open work

Ceilings: 65,536 source UTF-8 bytes; 4,096 tokens; 48 nested forms; 128 executable statements; 2,048 instructions (source may lower this); 512 bits per reduced rational numerator/denominator; polynomial degree 64; 16,384 bytes per text value; 65,536 combined serialized output bytes; 200,000 VM work units. Growth checks precede text expansion and bound polynomial arithmetic. The VM stops before the reference check when a resource guard fails. Source/package validation bounds nested metadata and rejects foreign value types/cycles. Work units are deterministic proxies; they are not measured CPU time or an OS sandbox. The independent evaluator is also bounded by the admitted finite AST and numerical degree/bit limits, but its work is not included in `vm_work_units`.

Open: general grammar/enumerator generation; module/provider/ABI resolution; dependency specialization; binary/native/WASM/JS backends; effectful tool broker and process isolation; independent external proof; full mathematical function breadth and generalized generated-machine coverage; the rest of PIA-085–096. The UCG-084/124 quantitative counts have since been executed for the explicit finite profile in [NATIVE_QUANTITATIVE.md](NATIVE_QUANTITATIVE.md). No mission verifier or acceptance status is changed by these kernel increments.

## Verification recorded 2026-10-24

Executed with `/opt/polyia/runtime/bin/python3 -B` on the actual Oracle ARM64 host. The first test-first run had 31 expected failure assertions across 10 tests before the native module existed (`/tmp/polyia-native-red-20261024.log`). Separate division/package-input and statement-bound tests were observed red before implementation/correction (`/tmp/polyia-native-division-red-20261024.log`, `/tmp/polyia-native-budget-red-20261024.log`). One original tamper fixture was corrected because assigning an empty effect list to an already-empty list did not alter the package.

The resulting native suite passes **13 tests** (`python3 -B -m unittest discover -s tests -p test_native.py -v`, `/tmp/polyia-native-green-20261024.log`). It includes exact hand-derived outputs, 25 derivative/evaluation inputs, two polynomial division fixtures, Unicode spans, invalid grammar/types/effects, source/depth/arithmetic/degree/instruction/text/work/output bounds, package tampering and malformed metadata, plus compile CLI and execution of a copied runtime/package in a clean directory under isolated Python (`-I`).

The complete repository Python suite passed **154 tests in 12.057 seconds** (`python3 -B -m unittest discover -s tests -v`, `/tmp/polyia-native-full-suite-20261024.log`). Both checked-in examples were separately compiled and executed successfully. Temporary log paths identify this local run; the commissioning operator must capture their bytes in the release evidence rather than treating these paths as durable publication. This evidence supports the bounded increment only.
