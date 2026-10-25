# GitHub method for initiatives, packages and evidence

`akadaan310/surface` is the canonical integration repository. Each initiative begins with an immutable, verified source checkpoint, then receives its own branch and sibling worktree. A branch records a line of work; a worktree supplies a separate checkout while sharing Git objects. These are the mechanisms described by the [Git worktree manual](https://git-scm.com/docs/git-worktree).

## 1. Baseline and custody

`main` carries usable integrated source and explicit unresolved gates. Its current Git commit anchors `MANIFEST_SHA256.json`; run `python3 tools/verify_repository.py` before adopting it. The manifest checks exact bytes, Git blobs and tracked path/mode census. A downloaded ZIP can verify listed file identities without a Git census; retain the download's commit identity separately.

The original native recovery commit is `f002eece5a5915b886d77dce1807890588282afd`. Its source was snapshotted before integration. The original COSMOS ZIP exceeds the GitHub connector's 16 MiB JSON-request ceiling after base64 encoding, so the canonical tree stores it as two ordered chunks under `lineage/cosmos-continuation-parts/`. Their manifest reconstructs **the identical 16,736,093-byte original**, SHA256 `ca8f9202b4c4acc8ab39d3a7305f4ba4cf80d016a384db9714019208cd5ae622`. This changes the transport layout, not original archive content. Other nested archives retain their identities.

Local Git push credentials were unavailable in the migration environment. Publication uses the connected GitHub Git APIs: create blobs → tree → commit → lease-checked ref update. Local and published commit IDs may differ because parents and authorship metadata differ. Compare the complete tree and blobs, not only a reported commit string. There is no force-push or deletion of remote history. Fresh clone/tree census and source-manifest verification are the publication gate.

## 2. Begin an initiative

After preserving any local work:

```sh
git fetch origin main
git switch main
git merge --ff-only origin/main
python3 tools/verify_repository.py
# Read the baseline's actual acceptance receipt before calling it verified.
python3 tools/new_initiative.py quantum-next --base origin/main
```

The helper creates branch `initiative/quantum-next` and sibling checkout `../surface-worktrees/quantum-next`. It records the resolved base commit/tree and manifest hash in `initiatives/quantum-next/INITIATIVE.json`, along with default bounded-task policy and OPEN work. It refuses dirty source checkouts, existing branches/destinations and path escapes. It does not fetch, reset, commit, push or certify the chosen base.

Use a short stable name, for example `n-atlas-contract`, `quantum-channels`, `pulsar-timing` or `battery-chemistry`. Split independent science tracks so a blocked dataset or hardware credential cannot hold the native application indefinitely. A new initiative may depend on another initiative only through an explicitly pinned accepted artifact/commit.

## 3. Package contract

Each initiative carries:

| Item | Purpose |
|---|---|
| `INITIATIVE.json` | Base revision/tree, branch, dependencies, budgets and acceptance status |
| `SELF_PROMPT.md` | Cold-start instructions, exact next gate and unresolved obligations |
| Original commission/constitution | Source text and byte identity; never overwritten by interpretation |
| Grounded plan and generated machine | Source-linked tasks, dependencies, bounded adapters and atlas coverage |
| Input manifest | Repository commit, file/byte offsets, hashes, schema, license, units and acquisition receipt |
| Per-run evidence | Exact command/environment/inputs, measurements, tolerance, output hashes and status |
| Counterexamples/failure records | Rejections, unknowns, search exhaustion and alternative explanations |
| Resume packet | Job IDs/epochs/deadlines, valid checkpoint, failure class, consumed retry, next command |

The Quantum Oracle V3 package is already in `initiatives/quantum-oracle-v3/`; the corresponding initiative branch starts from the published integration baseline. Its original constitution/self prompt remain byte-identical. The complete repository archive at that branch includes the shared runtime and immutable source chunks; the package is not an orphaned prose document.

## 4. Execute and integrate

Work in bounded increments. Compile the grounded plan, validate the generated bundle, then run fixed adapters through the Supervisor. A model-free child can generate finite programs and test them; an external agent returns a reviewable result bound to its issued envelope. Preserve old receipts and late artifacts; never promote stale output or extend a fixed deadline with a heartbeat.

Commit code, source pins, relevant tests and evidence together. Keep personal credentials and large volatile runtime directories out of Git. Use one pull request per coherent initiative once its stated acceptance gate is reviewable. Explain the concrete problem, changed behavior, actual tests and remaining scope. This is the integration policy; repository branch-protection settings are not claimed to have been configured by this document.

For merging, rebase or merge the new baseline with explicit conflict review, rerun affected gates, and regenerate the release manifest deliberately. Do not rerun all historical scientific work merely because unrelated documentation changed. A candidate must satisfy its own acceptance and must not silently relax another gate. Commit an updated `SUM.md` and initiative receipt. Failed research remains available on its branch with status and a resume packet.

## 5. Reproducibility and release

Use exact Git refs in input pins. Record software/runtime versions and platform. For bit-exact claims, compare original bytes and outputs; for numerical claims, specify absolute/relative tolerance, conditioning, units and uncertainty. Timing measurements are host-specific. Real-device Android, quantum hardware and observational datasets have their own evidence gates.

Prepare a reviewed manifest with `python3 tools/verify_repository.py --write-manifest` only after staging the intended source census. Do not use that option to hide unexpected changes. Publish; then fetch into a fresh directory, verify tree/blob equality, run `verify_repository.py`, reconstruct immutable inputs, validate the commission and execute the selected smoke path. Report CI status from an actual run, never from the presence of a workflow file.
