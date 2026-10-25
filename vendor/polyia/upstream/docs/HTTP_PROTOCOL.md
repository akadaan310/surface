# Poly IA HTTP command protocol

Protocol: `polyia.command-plane`, version `1.0.0`. The machine-readable contract is [`../registry/openapi.json`](../registry/openapi.json), also served at `/openapi.json`. Runtime behavior is implemented in [`../polyia/server.py`](../polyia/server.py), with commands and durable state owned by `Ledger` in [`../polyia/store.py`](../polyia/store.py). This protocol implements the approved portable commissioning bootstrap; it does not certify completion of the full Poly IA commission.

## Start and authority

The service constructor is:

```python
make_server(ledger, host="127.0.0.1", port=0, token=...,
            read_token=None, public_origin=None)
```

It returns a `ThreadingHTTPServer` compatible object. The caller owns `serve_forever`, `shutdown`, and `server_close`; closing the server does not close the supplied ledger. Only literal loopback addresses are accepted. `localhost` is normalized to `127.0.0.1`. Neither `0.0.0.0` nor a remote address or arbitrary hostname can be bound. Port `0` requests an ephemeral local port. IPv6 loopback is supported by the implementation but is not included in the current IPv4 socket evidence.

CLI startup takes the operator secret from `POLYIA_OPERATOR_TOKEN`, an optional separate reader secret from `POLYIA_READ_TOKEN`, and an optional public origin from `--public-origin` / `POLYIA_PUBLIC_ORIGIN`. Tokens must be nonempty printable ASCII without whitespace and at most 4096 characters. Operator and reader secrets must differ. Generate a high-entropy secret outside source control; the implementation does not impose an entropy test.

Every private endpoint requires `Authorization: Bearer <token>`. The operator token grants reads and command authority; the optional read token grants reads only. The fixed HTTP command actor is `operator`. A successful authenticated response includes `X-PolyIA-Scope: operator` or `read`, which the browser uses to present the correct controls. This is a single-operator portable service, not a multi-user identity or role administration system.

The browser starts disconnected. A token is explicitly entered, the input is cleared after submission, and the token remains only in private JavaScript memory. No cookie, URL, browser persistent storage, server asset, or default request log contains it. “Forget token” clears the client session. Reloading requires a new connection. Browser extensions, malicious code already executing on the same origin, or an operator who controls the host are outside this token-memory guarantee.

## Routes

| Method and path | Authority | Behavior |
| --- | --- | --- |
| `GET /` | Public | Static live interface, initially without state or a token. |
| `GET /app.js`, `/client.mjs`, `/styles.css` | Public | Fixed packaged assets. No directory listing or arbitrary file route. |
| `GET /healthz` | Public | Minimal process liveness; no private state or verification claim. |
| `GET /.well-known/polyia.json` | Public | Protocol, limits, implemented capabilities, and explicit unavailable transports. |
| `GET /openapi.json` | Public | OpenAPI 3.1 document. |
| `GET /v1/state` | Read | Current reducer state plus revision and head envelope. |
| `GET /v1/events?after=0&limit=100` | Read | Ordered committed events after the exclusive sequence cursor. |
| `GET /v1/commands/<command_id>` | Read | Original receipt; unknown ID is 404, cross-actor ambiguity is 409. |
| `GET /v1/checkpoints/latest` | Read | Latest checkpoint, or 404 if none exists. |
| `GET /v1/checkpoints/<checkpoint_id>` | Read | Source-linked immutable checkpoint snapshot. |
| `GET /v1/verify` | Read | Recompute ledger integrity and return a report. `ok: false` is meaningful even with HTTP 200. |
| `GET /v1/refusals?limit=100` | Read | Separate durable ledger command refusal diagnostics. |
| `POST /v1/commands` | Operator | Apply a guarded command or recover its exact prior receipt. |

GET routes also support HEAD without a response body and with the same authorization requirements. Other methods on known routes return a structured refusal. No SSE, WebSocket, upload, model invocation, or arbitrary execution endpoint is advertised. There is no CORS wildcard or cross-origin preflight grant.

## Guarded commands and retries

A command has exactly four top-level fields:

```json
{
  "command_id": "owner-guidance-001",
  "expected_revision": 0,
  "kind": "guidance.submit",
  "payload": {
    "target": "research",
    "text": "Pause registered research while the current evidence is reviewed.",
    "action": {"kind": "pause_research"}
  }
}
```

Use the currently observed revision. IDs are 1–128 ASCII characters, start with a letter or digit, and thereafter allow letters, digits, underscore, dot, colon, and hyphen. `expected_revision` is a nonnegative integer, not a JSON boolean. `payload` is an object. A new command commits only when its revision guard matches. All registered command payloads reject unknown fields, so a caller cannot supply an accepted status or forge a verifier outcome.

A committed response has `ok`, `command_id`, `actor`, `revision`, `head`, and `result`. HTTP 200 establishes that the operation was recorded. Scientific status and verifier outcome are in `result`; a recorded failed experiment is not a scientific pass.

Command IDs are scoped by actor. Retrying the same ID, actor, and exact complete request recovers the original receipt, including its original revision. Changing any request field under the same ID returns `IDEMPOTENCY_CONFLICT`. A response can be lost after commit, so a transport failure must not cause the client to invent a new ID. The browser retains the exact unresolved request and offers “Retry same command ID.” It blocks new commands until the pending request has a conclusive outcome. It never silently rebases a revision conflict. After a conclusive stale refusal, review refreshed state and submit the intended command again with a new ID.

The implemented commands are:

| Kind | Payload | Resulting authority boundary |
| --- | --- | --- |
| `guidance.submit` | `target`, `text`, optional `action` | Records exact text as SUBMITTED. Target is a requirement ID or `research`. |
| `guidance.ack` | `guidance_id`, `disposition`, `reason` | Records ACKNOWLEDGED, DEFERRED, or REJECTED. Applied and rejected guidance is closed. |
| `guidance.apply` | `guidance_id` | Requires acknowledgment and a supported registered action. Text alone cannot become APPLIED. |
| `requirement.produce` | `requirement_id`, `artifacts`, optional `note` | Reads actual permitted workspace files and captures immutable bytes. Paths are not uploads. |
| `requirement.verify` | `requirement_id` | Runs the requirement’s registered verifier over captured artifact identities. |
| `requirement.accept` | `requirement_id` | Requires current passing verification and intact captured bytes. |
| `checkpoint.create` | optional `note` | Commits a linked snapshot in the same transaction as its event. |
| `experiment.run` | `name`, `parameters` | Runs only a registered bounded function and records inputs, result, checks, limits, and code identity. |

Supported guidance actions are `set_priority` with a requirement `target` and integer `priority` from 0 through 9, `pause_research`, and `resume_research`. The affected target must match the submitted guidance target. Research actions target `research`.

Registered experiments are `polynomial`, `grammar-promotion`, `qpath`, and `acceptance`. `{}` selects the demonstration defaults. The functions perform bounded exact checks and report their own scope and limitations. Applied research pause refuses new experiment commands. These demonstrations do not replace the canonical university corpus or the full scientific research mandate.

## Event cursor and inspection

An event page is `{"events": [...], "next_after": N}`. `after` is exclusive, starts at zero, and is at most `2^63−1`; `limit` is 1–1000, default 100. Resume using `next_after`. An empty page preserves the supplied cursor. A full page does not claim it is the end of the feed; request the next page as needed. Query keys are exact, unique, and bounded.

Each event contains `sequence`, `event_id`, `event_hash`, `previous_hash`, `kind`, `payload`, `actor`, `timestamp`, `before_hash`, and `after_hash`. `payload` contains the full recorded `request` and `result`. Replay consumes recorded results; it does not re-run science or external effects. State/head reads and event-page reads are individual consistent reads, not one combined snapshot. A concurrent writer can advance between them. The browser displays its event cursor separately from state revision and retains the latest 100 loaded events, with four-second polling while the tab is visible.

Checkpoint reads return `id`, `revision`, `head`, `state`, `state_hash`, and `previous_id`. Verification checks captured immutable artifact bytes; a later edit to an uncaptured workspace file does not rewrite captured evidence. Reproduce the requirement to commission a different artifact set.

## Parsing, transport, and safe errors

Commands require a single `Content-Length`, at most 65,536 body bytes, and `Content-Type: application/json` with optional `charset=utf-8`. The server rejects transfer encoding, duplicate framing/authentication/authority headers, non-object commands, duplicate JSON keys, non-finite numbers, invalid UTF-8, invalid Unicode strings, more than 32 nested JSON levels, and more than 10,000 JSON values. Total parsed headers are bounded to 16 KiB and request targets to 4096 characters. Experiment inputs have additional lower runtime budgets. Connections close after a response; socket reads time out after ten seconds. The bootstrap does not implement a global concurrent connection limiter or production rate limiting.

Errors have this stable shape:

```json
{
  "ok": false,
  "error": {"code": "REVISION_CONFLICT", "message": "...", "details": {}},
  "request_id": "opaque-request-reference"
}
```

Details are optional. Typical statuses are 400 invalid schema/query/framing, 401 missing or invalid bearer token, 403 read-only or Origin refusal, 404 unavailable route/record, 405 wrong method, 409 revision/idempotency/state conflict, 411 missing length, 413 body budget, 415 media type, 421 unexpected Host, and 431 header budget. Unexpected internal exceptions return a generic error and an opaque request reference. Their exception class is logged; their message, stack, request body, and token are not sent to the client.

All responses set `Cache-Control: no-store`, a restrictive Content Security Policy, `nosniff`, frame denial, and no-referrer policy. Dynamic application content is created with DOM text nodes or `textContent`; guidance and scientific output are never inserted as HTML. Native form controls have labels, keyboard focus indicators, and disabled states reflecting current access. Errors are visible and announced through an alert region. The interface responds to reduced-motion preferences and smaller screens. These are implemented design properties; the evidence report distinguishes protocol and client execution tests from unavailable browser-rendering verification.

## Same-origin reverse proxy

Local access permits the bound loopback authority and `localhost` on its bound port. `public_origin`, when configured, additionally permits one exact HTTPS origin such as `https://commission.example.org` with an optional explicit nondefault port. It must have no credentials, wildcard, path, query, or fragment. Remote binding remains forbidden.

Every request requires an allowed Host. If Origin is present, it must match the origin associated with that request’s Host exactly. An absent Origin is allowed for bearer-authenticated machine clients. `Origin: null`, another site, a public Origin sent under a local Host, and a `Sec-Fetch-Site: cross-site` request are refused. Untrusted forwarded headers do not override this rule.

The reverse proxy must terminate TLS, preserve the incoming `Host` and `Origin`, forward only to the bound loopback port, and enforce its own request/rate/resource budgets. For a standard HTTPS origin, `proxy_set_header Host $host;` and preserving the default Origin header suffice; an explicitly configured nondefault HTTPS port requires preserving that authority, commonly with `$http_host`. Provision TLS and operational authentication carefully in the deployment environment. Merely setting `public_origin` does not deploy a proxy, open a remote socket, issue certificates, or establish operator identity.

## Audit and assurance limits

The runtime’s separate refusal table retains rejected ledger commands without adding applied events. Failures rejected before `Ledger.command`—including HTTP authentication, body parsing, origin checks, and top-level schema checks—return safe diagnostics but are not durably journaled. Default handler access logging is disabled to avoid full URL/token leakage. Production deployment must commission redacted access/security logging, rate limits, TLS, backups, process supervision, and any multi-user identity model separately.

Hash-chain and replay verification establish internal consistency of the checked local records. They are not a digital signature, an independent truth oracle, or protection against an administrator replacing and recomputing the entire database. `NOT_COMMISSIONED` remains the full-mission status even when a bootstrap workflow or one artifact-integrity requirement succeeds. No browser screenshot, remote deployment, production load test, or complete commission is implied by the protocol evidence.
