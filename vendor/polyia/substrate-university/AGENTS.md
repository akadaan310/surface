# Instructions for agents working in this repository

This is **Substrate University — Haq Roots**, a client-only Vite + React + TypeScript + Three.js site. It is no longer a Next.js app (the earlier Next.js code, and the `next dev` agent-rules block, live only in Git history).

- The governing product definition is the Haq Roots constitutional prompt v2.0, summarized in `docs/UNIVERSITY_REBUILD.md`.
- All generative and interactive logic runs in the browser. Do not add server routes, model-provider calls, secrets or paid APIs.
- Keep the math in `src/math/` pure and unit-tested. Rendering and computational truth are separate contracts.
- Every subject keeps an epistemic label. Do not present house constructions as established mathematics, fictional residents as real people, or specimen books as publications.
- Do not include religious, scriptural or Arabic-language subject material, or cross-session AI identity/continuity research.
- Checks: `npm run typecheck`, `npm test`, `npm run build`, `npm run test:e2e`.
