# Start Poly IA in Codex

The extracted commission and actual runtime are on branch
[`codex/commission-20261024-83906c7`](https://github.com/akadaan310/PolyIA/tree/codex/commission-20261024-83906c7).
The default `main` branch retains the earlier import transport. **Use the runtime
branch; no ZIP upload or manual extraction is required there.**

Read the [safe-checkpoint handoff](docs/HANDOFF_2026-10-24.md) first. Runtime 1.4.0
is deployed; commissioning was stopped at the owner's request. Keep the service
and its persistent ledger, and resume implementation only on a new owner request.

For a new checkout:

```bash
git clone --branch codex/commission-20261024-83906c7 https://github.com/akadaan310/PolyIA.git
```

For an existing checkout, inspect its branch and changes before switching;
preserve concurrent work. The original commissioning workstation's local branch
is `codex/commission-20261024`.

Open the runtime branch named above in Codex. On resumption, read [CODEX_START.md](CODEX_START.md), then [GOD_SEED.md](GOD_SEED.md) completely. All sources, books, registries, runtime code, tests, and the commissioning interface are repository files on that branch.

## Copy this into Codex

```text
Resume work in https://github.com/akadaan310/PolyIA/tree/codex/commission-20261024-83906c7. The complete commission and all preserved package sources are extracted on that runtime branch. Inspect the checkout and preserve concurrent work. Read docs/HANDOFF_2026-10-24.md, START_HERE.md and CODEX_START.md, then read GOD_SEED.md completely and follow its linked source, scientific, authority, acceptance, and operating documents. Execute the full Option A commission, including all incorporated B/C requirements, from the retained checkpoint and existing service.

Your first operational deliverable is the real live, inspectable, machine-operable state service on the actual target environment. Use it throughout commissioning, with durable event history, acknowledged and actually applied guidance, source-linked checkpoints, and evidence-backed completion. Preserve the non-LLM core requirement. Division Infinity is IX; VII and VIII are open research charters. Do not stop at planning, the bootstrap, or its successful demonstration. Keep the full mission NOT_COMMISSIONED until its acceptance gates pass, then carry forward the Automaton Science University mandate.
```

## First repository checks

```bash
python3 tools/verify_package.py --require-release-manifest
python3 tools/audit_no_llm.py
python3 -m unittest discover -s tests -v
```

Follow [the operator runbook](docs/OPERATOR_RUNBOOK.md) for the actual target installation, supported Python/SQLite/POSIX environment, authentication, persistent storage, and service supervision. The supplied bootstrap is runnable; the full Poly IA mission remains `NOT_COMMISSIONED`.

The original commission ZIP and prompt copies remain separately preserved. [GitHub handoff notes](docs/GITHUB_HANDOFF.md) identify the publication-only adjustments and the original release identity.
