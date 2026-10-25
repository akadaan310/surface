# Poly IA — copyable Codex start directive

Clone or open branch **[codex/commission-20261024-83906c7](https://github.com/akadaan310/PolyIA/tree/codex/commission-20261024-83906c7)** in Codex. The complete package is extracted on that branch, including `sources/`; `main` retains the earlier transport. Read [the owner-requested stopping checkpoint](docs/HANDOFF_2026-10-24.md) before work. Runtime 1.4.0 is already deployed on the Oracle VM. Preserve its ledger and concurrent changes. The block below is for an explicit request to resume commissioning; it does not override the owner's current stop.

```text
Execute the Poly IA Option A commission, including every B/C obligation explicitly incorporated by the owner. This is an execution request, not a request to stop after planning.

Work in akadaan310/PolyIA on runtime branch codex/commission-20261024-83906c7 (the retained workstation branch is codex/commission-20261024). Read docs/HANDOFF_2026-10-24.md and inspect the existing live service before mutating anything. Then read README.md, GOD_SEED.md completely, registry/authority.json, docs/SOURCE_RECONCILIATION.md, docs/ACCEPTANCE_SYSTEM.md, docs/OPERATOR_RUNBOOK.md, and docs/HTTP_PROTOCOL.md. Read the scientific foundations, formal vocabulary, division charters, Astra integration, university mandate, work contracts, complete inherited-obligation crosswalks, and original sources relevant to each production. Preserve every supplied source and pinned repository/book byte. Never omit a source because an earlier document calls it a sample or preview.

The owner's current decision is binding: Division Infinity is IX; VII and VIII are open research charters. Preserve existing I–VI and all 62 original topic identities. Follow explicit linked dispositions for superseded inherited instructions. DODGE means Deliverable, Obligations, Dependencies, Guards, Evidence; PIA-* and K-* references remain stable across your chosen phases.

Your FIRST OPERATIONAL DELIVERABLE is the real live, inspectable, machine-operable state service on the actual target environment. Perform minimum read-only environment/authority preflight; run tools/verify_package.py and the documented tests; initialize the durable ledger outside the source tree; launch the supplied bootstrap under supervision; configure the authenticated TLS boundary within the existing target authority. Return the actual URL, access method, protocol version, source-linked checkpoint and restart evidence. Never invent a deployment URL. An access/DNS blocker holds only the affected public-deployment gate; continue independent authorized work.

Use that service throughout the commission. Read pending guidance at safe checkpoints. Preserve SUBMITTED, ACKNOWLEDGED/DEFERRED/REJECTED and actually APPLIED distinctions. PRODUCE captures real bytes, VERIFY runs registered verifiers of the appropriate evidence class, and ACCEPT binds the verified version. Maintain durable full event history, idempotent commands, expected-revision guards, source/constitution/policy context and reproducible checkpoints. Register real commission verifiers; do not replace the intentionally unsupported mission verifier with a generic file-exists pass. Bootstrap success is not full commissioning.

Core Poly IA workflows must operate without local or remote LLM inference. Implement the native grammar/compiler, grammar-as-letter promotion with separate expansion and semantic-preservation evidence, typed Q-Strings/Q-paths with genuine joint-input composition, constructive state-map generators, tool contracts, source-based prompt/article intake, continuous bounded experiments, versioned improvements and the human/machine application. Optional models may propose through declared contracts and cannot bypass truth or execution gates. Codex may use its own development tools; this does not make model inference a dependency of the product runtime.

Ground Astra in the retained ATOM tuple, phase/report interface and exact geometry contracts. Preserve machine state versus rendering state. Keep existing University content/export boundaries and upstream project ownership. DEC-004 records the owner's Book of Forms construction instruction; the newly constructed book remains distinct from the preserved Library of Forms, CGT book and Grammar in Numbers. DEC-005 records the delegated OpenClaw reference decision. Do not reopen those resolved owner questions without new evidence.

Choose your own implementation phases from registry/work_contracts.json. Trace all 192 current obligations, every original 96 PolyIA clause, every 156 UCG clause and the supplemental constitutional sections. Retain original acceptance detail except where a linked current ruling refines it. Carry missing inputs, failed experiments, counterexamples and unsupported capabilities explicitly. Continue already-authorized reversible work without repeated confirmation; respect actual scope, credentials and effect grants.

Do not stop at this bootstrap, a charter, a dashboard or a successful demonstration. Complete the finite acceptance contract with actual source-linked evidence, a reproducible release and the working Poly IA application. Keep NOT_COMMISSIONED until the full release gates pass. Then activate the standing mandate in docs/AUTOMATON_SCIENCE_UNIVERSITY.md so Poly IA develops Automaton Science University through bounded, inspectable, guidable and versioned research. Your final handoff must be independently understandable from the URL/checkpoint and repository, without relying on your chat report.
```

## First local checks

From the repository root, using Python 3.11 or later and a patched SQLite build as specified in the runbook:

```bash
python3 tools/verify_package.py
python3 -m unittest discover -s tests -v
python3 -m polyia init --state-dir /tmp/polyia-first-state
python3 -m polyia demo --state-dir /tmp/polyia-first-state
python3 -m polyia verify --state-dir /tmp/polyia-first-state
```

The `/tmp` path is for a disposable local demonstration. The actual always-on service uses persistent storage, an operator token, a service manager and the deployment runbook. Node-based interface tests are documented separately and are development dependencies; the Python bootstrap needs no third-party Python packages.
