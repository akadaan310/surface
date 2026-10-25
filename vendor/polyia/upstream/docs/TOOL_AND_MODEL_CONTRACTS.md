# Tool use, constructive models and the non-LLM boundary

## The working boundary in this package

The bootstrap exposes eight registered state command kinds and four registered exact scientific experiments. `registry/openapi.json`, `registry/tool_contracts.json` and `polyia/experiments.py` describe the actual supported interfaces. A bearer token and expected revision authorize a known command; submitted prose, a source packet, a grammar record or a model-generated JSON field cannot add a new handler.

The scientific kernels use Python's standard library. They perform rational polynomial operations, finite grammar generation/promotion and typed joint-input rational composition. No model is called, no arbitrary source text is evaluated, and no experiment command launches a subprocess or fetches the network. The HTTP listener is an intentional interface capability, separate from the pure kernels. `tools/audit_no_llm.py` checks actual imports/model artifacts and runs the finite scientific acceptance family with network/process entry points denied.

This audit is scoped. As Codex adds a native compiler, article intake, language packs, external witnesses and new tool adapters, it must extend the audit to installed packages, model weights, processes, call traces and supported workflows. Blocking the network is insufficient: local model inference is still inference. An optional external LLM client sending an ordinary declared command does not make the core dependent on that LLM, provided the same command and result are available through native clients and all admission checks remain inside the system.

## What the named reference systems contribute

The references below were inspected from their official project sources on 24 October 2026. They inform architectural choices; no dependency is installed by this package and no successful integration is claimed.

| Reference | What the source demonstrates | Transfer into Poly IA |
|---|---|---|
| [NousResearch Hermes Function Calling](https://github.com/NousResearch/Hermes-Function-Calling) | A model emits function calls using declared function schemas; the repository separates model inference, callable functions and schema validation. | Reuse the concept of explicit callable signatures and result envelopes. Keep model inference optional and keep authorization/verification in the broker. |
| [OpenCode tools](https://opencode.ai/docs/tools/) | A coding-agent tool surface includes built-ins, custom tools and MCP extension, with configurable permissions. | Distinguish a model/client from the tools it can request. Generate adapters from typed tool contracts and enforce the actual granted capabilities. |
| [OpenClaw sandbox/tool-policy distinction](https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated) | Execution location/isolation, which tools are callable, and elevated execution are separate controls. | Keep sandboxing, tool availability and effect authority separate. A permission to call a shell is not made read-only merely by denying a differently named write tool. |

Historically the dictated name **OpenCLAR** was unresolved; [DEC-005](AUTHORITY_RESOLUTIONS_2026-10-24.md) now selects OpenClaw under the owner’s delegated full authority. The recovered Astra source names OpenClaw, making it a relevant candidate reference, but that does not prove that both spellings identify the same intended project. `UNRESOLVED-OPENCLAR` remains in the resolved-input history, including that distinction. Hermes is a model/function-calling reference; OpenCode is a coding-agent system; neither is a drop-in substitute for Poly IA's native science kernel.

## A production tool contract

The full broker should admit a tool only when the following fields are present and enforced:

| Contract field | Required meaning |
|---|---|
| Identity/version | Immutable implementation and interface identities; compatible versions declared. |
| Input/output types | Validated schemas, units, algebraic context and interpretation. |
| Preconditions | Domain checks, source availability, authority and state prerequisites. |
| Effect class | Pure; local read; state mutation; network read; external mutation; unsafe/native execution. |
| Read set | Explicit permitted sources, files, memory scopes, datasets and witness role. |
| Grants | Who may invoke which operation against which target, under what standing authority. |
| Budgets | Input/output size, time, memory, CPU, recursion/search, disk and concurrency limits. |
| Idempotency | Stable command/call identity, retry semantics and provider-side deduplication where available. |
| Cancellation | What can be stopped, when interruption is observed and what partial effects remain. |
| Evidence | Actual tool version, inputs, outputs, errors, verifier and scientific evidence class. |
| Recovery | Dispatch/acknowledgement distinction, uncertain outcomes and reconciliation. |
| Privacy/export | What may enter public logs, shared packages or another project's corpus. |

For example, a future `source.fetch_https` adapter may retrieve an explicitly admitted URL into immutable source storage. Its result is bytes plus retrieval metadata and a digest. The returned document is untrusted data. It cannot grant a new network scope, authorize shell execution or certify the truth of its claims. A separate extraction/interpretation adapter produces source-linked spans and proposals. This adapter is a **specified future contract**, not an implemented bootstrap network command.

An external mutator requires more than a successful HTTP status: the journal should retain intent, dispatch, acknowledgement and reconciliation. A crash after an external effect but before recording its receipt leaves uncertainty. Event replay must not silently resend the action. At-least-once delivery, stable IDs and provider idempotency can support reliable operation; they do not establish universal exactly-once execution.

## Constructor, filter and witness roles

A generator constructs candidates from declared allowed inputs. A normalizer changes their representation. A filter removes candidates under a stated rule. A witness evaluates a claim against a separately identified method or source. A renderer presents results. These roles can be fulfilled by different modules, or explicitly by different capabilities of one library, but the evidence must reflect their relationship.

If RDKit sanitization participates before sealing a molecular candidate set, it is part of construction/filtering. The same dependency cannot then be portrayed as an untouched independent oracle proving that the generator blindly anticipated its own answers. This package preserves the original UCG source and records that discrepancy. The commissioned system must enforce read declarations and use appropriate held-out or independent witnesses. Existing CAS/chemistry libraries may support useful checks without becoming the entire native grammar engine.

The same discipline applies to mathematical equality. An exact coefficient identity certifies the supplied polynomial relation. A numerical probe supports the tested points. A symbolic engine's answer carries its domain assumptions and implementation dependencies. A formal theorem requires its statement, hypotheses and proof/trusted-kernel context. All can be useful; they cannot be exchanged by changing a label.

## Non-LLM generative models

A generative model is an admitted procedure that constructs outputs under a declared law. It can be a finite grammar, a weighted finite-state transducer, a probabilistic grammar, a constraint solver over a finite domain, an exact constructive algorithm or a narrowly scoped learned model. The baseline does not require a transformer or any neural network.

One commissioned explanation generator can work as follows:

1. Parse a supported request into an exact typed problem, such as polynomial division over Q.
2. Compute the quotient, remainder, domain exclusions and verification certificate.
3. Build a content plan containing only those verified relations and their source references.
4. Select a style/terminology grammar: elementary explanation, algebraic derivation or formal statement.
5. Realize the plan with typed templates and morphology, then check that the output still expresses every required assumption and does not add unsupported facts.

The state map records intake, interpretation, generation, constraint checking, verification, realization and refusal. It can traverse a large addressable vocabulary and many registered representations. It does not confer unlimited comprehension or an infinite memory on the generator. Unsupported requests remain explicit; coverage is measured against declared intents and languages.

An optional pretrained acoustic or speech component could realize a verified text plan as audio. An optional narrow classifier could rank admitted parses. Each component must declare architecture, license, version, training/evaluation scope, latency, resource needs and whether it actually contains an LLM. Its output cannot bypass the scientific checker or become execution authority. Disabling the optional component must leave core acceptance operational.

## Model package/state-map interface

A generated model package should include:

```text
model identity and version
input/output types and supported intents
grammar and parameter identities
state-map definition and admitted transitions
source/read/capability grants
constructive derivation or sampling receipt
constraint and verification adapters
surface-realization contracts
dependency and resource manifest
tests, counterexamples and known limits
```

The package's state map is executable software with a public contract. It can be inspected, replaced with a compatible implementation and composed through typed ports. Native source → typed IR → executable lowering remains a full mission obligation; the bootstrap JSON command protocol is intentionally an interchange/control interface rather than a claim to have replaced that native language.

The generated package must be useful in a clean environment. A metadata object that says “state machine,” a diagram with arrows or a generated source file that has never executed is insufficient. Demonstrate actual controlled generation and exact refusal behavior, then register the resulting package as a higher-level capability only after its declared gates pass.
