# Pinned PolyIA and Substrate University reuse

This directory contains a deliberately finite import for Surface's headless
development tools. The four PolyIA kernels and thirteen University source
modules retain their exact upstream bytes. Surface's C++ renderer, Android
bridge and scientific state do not import a browser or execute these Python or
TypeScript modules.

| Path | Purpose |
|---|---|
| `IMPORT_MANIFEST.json` | Per-file upstream commit, source path, Git blob SHA-1, SHA-256, size, role and unchanged-byte declaration |
| `upstream/polyia/` | Four pure PolyIA kernels plus original package version file |
| `upstream/tests/` | Six original test files; 89 tests freshly passed |
| `upstream/tools/` | Original portable generator builder and trusted installed checker |
| `upstream/examples/` | Exact source cards, inverse cases and forms/native examples |
| `upstream/docs/`, `upstream/registry/`, `upstream/sources/` | Selected contracts and complete documentary source-pin closure |
| `substrate-university/src/` | Exact rational/matrix/address/world kernels and all six divisions' topic registry |
| `substrate-university/tests/` | Original broader Vitest tests retained as reference; not run or dependency-closed in this partial import |
| `university_demo.mjs` | Surface-authored fixed headless fixtures; requires Node 24+ |
| `LICENSE_STATUS.md` | Observed upstream rights information; no inferred software license |

Run from the Surface root:

```sh
python3 -I -B tools/polyia_surface_demo.py
python3 -I -B tools/polyia_surface_demo.py --with-university
python3 -B -m unittest discover -s tests -p test_polyia_integration.py -v
```

Run the preserved PolyIA tests from their own source root:

```sh
cd vendor/polyia/upstream
python3 -B -m unittest discover -s tests -v
```

The default demo requires Python's standard library. The TypeScript fixture
uses Node's native stripping and a narrowly scoped extension resolver; it is
not a TypeScript static check, Vite build, browser execution or Android port.

The manifest contains **80 exact files, 4,455,381 bytes**: 61 from PolyIA and 19
from Substrate University. The original ASTRA ZIP is 3,462,608 of those bytes.
It is retained because the pure Astra adapter's source-lock test authenticates
the original archive as well as specific extracted members. Its archived web
and service material is custody data. Nothing in that archive is installed,
served or launched by Surface.

`AGENTS.md`, start directives and commissioning documents below `upstream/`
are preserved source records. They do not authorize deployment or override the
current Surface task. The source handoff records an owner stop, research paused,
and **NOT_COMMISSIONED with 2/192 mission obligations accepted**. This import
does not resume upstream commissioning, start a worker, advance a live ledger
or activate the University mandate. **Infinity remains IX; VII and VIII remain
open research charters.**

Read [POLYIA_INTEGRATION.md](../../docs/POLYIA_INTEGRATION.md) and
[SUBSTRATE_UNIVERSITY.md](../../docs/SUBSTRATE_UNIVERSITY.md) for exact interfaces,
tests, known defects, scope and remaining integration work.
