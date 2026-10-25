# Fresh replay of the preserved PHANTOM / QuantumOracle foundation

## Result

On 25 October 2026, the preserved foundation was extracted into `/workspace/scratch/976a326a6786/foundation-replay` and its documented local checks were rerun. All eleven bounded tasks completed successfully: **145 original unit tests**, the v2 pinned-input check, PHANTOM release verification and exact cold replay, and the documented examples/reference run. No packages were installed and no network access was used.

The original continuation ZIP is unchanged. Every regular file in the extracted v3, v2, PHANTOM and QuantumOracle archives was compared byte-for-byte with its ZIP member after execution; there were **zero differences**. New reports and examples were written under the separate replay output directory. No native implementation files were edited for this replay.

## Fresh results

| Check | Observed result | Raw log |
|---|---|---|
| companion-tests | 7 / 7 original radix-machine tests passed | `evidence/foundation-logs/companion-tests.log` |
| oracle-run | Fresh bounded experiment completed; Bell, damping, 20 ring cases and circuit search | `evidence/foundation-logs/oracle-run.log` |
| oracle-tests | 8 / 8 original Python tests passed | `evidence/foundation-logs/oracle-tests.log` |
| oracle-verify | Fresh experiment ledger VERIFIED | `evidence/foundation-logs/oracle-verify.log` |
| phantom-cold-replay | 129 scientific files verified; 125 deterministic files regenerated exactly | `evidence/foundation-logs/phantom-cold-replay.log` |
| phantom-examples | Text, image, audio and math intake; 4 CLI examples passed | `evidence/foundation-logs/phantom-examples.log` |
| phantom-tests | 121 / 121 original tests passed | `evidence/foundation-logs/phantom-tests.log` |
| phantom-verify | 564 files / 27,758,650 bytes verified | `evidence/foundation-logs/phantom-verify.log` |
| v2-inputs | Both pinned input archives match | `evidence/foundation-logs/v2-inputs.log` |
| v3-examples | Original atlas/binary/quantum example completed | `evidence/foundation-logs/v3-examples.log` |
| v3-tests | 9 / 9 original tests passed | `evidence/foundation-logs/v3-tests.log` |

The PHANTOM cold replay used both externally pinned ledger heads, reduced 472 admission events and 56 execution events, and reported no numerical differences. Numeric tolerance was neither requested nor used. Four originally designated measured files were excluded from regenerated-byte comparison: kernel `companion_tests.txt` and `performance.json`, structures `performance.json`, and transfer `performance_profile.json`. Their retained original bytes were still verified. The replay preserves its original scoped claim classification (26 accepted with scope, 8 rejected, 1 unknown); successful replay does not promote rejected or unknown claims.

Full original output is saved as `evidence/foundation-logs/phantom-cold-replay-result.json`. The fresh Oracle summary and ledger, PHANTOM example receipt, individual supervisor records and complete stdout/stderr logs are alongside it.

## Archive identities

| Archive | Bytes | SHA-256 |
|---|---:|---|
| SURFACE_PHYSICAL_COSMOS_CONTINUATION_v1.zip | 16,736,093 | `ca8f9202b4c4acc8ab39d3a7305f4ba4cf80d016a384db9714019208cd5ae622` |
| QUANTUM_ORACLE_PHANTOM_V3_N_ATLAS.zip | 16,666,087 | `4b8decefc53d7f6776ed668cfc2f3ab48660f68e5a47ddfcd4fb346548c32ace` |
| QUANTUM_ORACLE_PHANTOM_V2_HANDOFF.zip | 16,643,831 | `0e37728a910431be8a3e7290caaf4f49481b6fc12643f336b4debfda4642e92b` |
| PHANTOM_Division_VIII_v0_4_Handoff.zip | 17,147,236 | `b66fb352ad51c6ed09f1059b0a72fdcf0f38ee81431c6f3099ba20a4e4076fbb` |
| QUANTUM_ORACLE_HARNESS_v0.1.zip | 12,191 | `cbe3097cbaef23369134be894e13a8df96832efcad2577633d040fe8cec1b26d` |

## Reproducible commands

Python 3.12.14, NumPy 2.3.5 and SciPy 1.17.0 were already installed. The commands below were run from the stated extracted directories. Each was launched through `tools/supervise.py`, with a 180-second hard deadline, a 120-second no-progress deadline, and one observed attempt. The longest task took 15.798 seconds.

Supervisor command pattern:

```sh
python3 tools/supervise.py --root /workspace/scratch/976a326a6786/foundation-replay/supervisor --task TASK --timeout 180 --semantic-timeout 120 --cwd DIRECTORY -- COMMAND
```

### companion-tests

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/phantom/phantom_division_viii_v04/inputs/companion/radix_machine`

```sh
python3 -B -m unittest -v
```

### oracle-run

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/oracle/quantum_oracle`

```sh
python3 -B -m quantum_oracle run --out /workspace/scratch/976a326a6786/foundation-replay/outputs/oracle
```

### oracle-tests

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/oracle/quantum_oracle`

```sh
python3 -B -m unittest discover -s tests -v
```

### oracle-verify

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/oracle/quantum_oracle`

```sh
python3 -B -m quantum_oracle verify --out /workspace/scratch/976a326a6786/foundation-replay/outputs/oracle
```

### phantom-cold-replay

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/phantom/phantom_division_viii_v04`

```sh
python3 -B -m division8 replay --run runs/release --expected-head 6bddd82c0587cf3ce557bed4f950e9664cdbb9e5a1ae89ad13d0eb891ff948b6 --expected-execution-head dbde8c15bf3dd7bc74da3f2bf537d4f5e59935f06ce833598f6a9fddbaf64e12 --output /workspace/scratch/976a326a6786/foundation-replay/outputs/phantom-cold-replay.json
```

### phantom-examples

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/phantom/phantom_division_viii_v04`

```sh
python3 -B scripts/run_examples.py --out /workspace/scratch/976a326a6786/foundation-replay/outputs/phantom-examples
```

### phantom-tests

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/phantom/phantom_division_viii_v04`

```sh
python3 -B -m unittest discover -s tests -v
```

### phantom-verify

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/phantom/phantom_division_viii_v04`

```sh
python3 -B -m division8 verify --manifest RELEASE_MANIFEST.json
```

### v2-inputs

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/v2/QUANTUM_ORACLE_V2_COMMISSION`

```sh
python3 -B verify_inputs.py
```

### v3-examples

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/v3/QUANTUM_ORACLE_V3_EXTENSION`

```sh
python3 -B examples.py
```

### v3-tests

Working directory: `/workspace/scratch/976a326a6786/foundation-replay/v3/QUANTUM_ORACLE_V3_EXTENSION`

```sh
python3 -B -m unittest discover -s tests -v
```

## Boundaries

- The eight historical Octave comparison passes and reported fixes were not rerun; their status remains UNKNOWN. The eight passing Oracle tests here are the original Python unit suite, a different check.
- The full original five-partition Language Lab corpus and broader research-evidence dependencies are not included in this handoff; no full-corpus recomputation was attempted.
- The v2 archive is a continuation kit. This baseline does not complete its planned astrophysics, collider, third-party solver or physical quantum hardware gates.
- No source implementation was modified. The original Python foundation was replayed separately; it is not a rendering or runtime dependency of the native C++ application.

The archived readmes and test entrypoints were inspected before execution. The v2 README explicitly distinguishes the continuation kit from completed integrations and identifies the absent full corpus. The machine-readable receipt `evidence/foundation-replay.json` records exact commands, archive hashes, environment versions, elapsed times, task outcomes and log hashes.
