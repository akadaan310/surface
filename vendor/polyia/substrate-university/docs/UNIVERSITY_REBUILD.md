# Substrate University — Haq Roots: rebuild record

Governing document: *SUBSTRATE UNIVERSITY — THE HAQ ROOTS CONSTITUTION*, constitutional prompt v2.0 (21 October 2026). It replaces the obsolete `SPEC.md` as the definition of the public product. `SPEC.md` is still in Git history.

## 1. Audit (21 October 2026)

| Item | Finding |
|---|---|
| Repository | `akadaan310/abedkadaancom`. Default branch `claude/new-session-xd8auu` (head `cccab10`). This work is on `ccr-ca09a873-qa0t6y`. |
| Previous app | Next.js 16.3, React 19.1, TypeScript. `app/` held services, arcade, dispatches, guest register and laboratory pages. `app/api/*` route handlers called paid model providers (Groq, Mistral, Cerebras, OpenRouter). `lab/` was a self-running research engine with a ledger. `lab/corpus/data` held scriptural text, which is excluded by constitution §A3. |
| Vercel project `abedkadaancom` | Git-connected. Production branch `claude/new-session-xd8auu`. Framework preset `nextjs`. Only domain: `abedkadaancom.vercel.app`. SSO protection applies to non-custom domains. |
| Live `abedkadaan.com` | **Attached to a different project**, `computationalgrammartheory-sdk`, built from `akadaan310/computationalgrammartheory`. It serves the *Computational Grammar Theory* book (static HTML, `X-Frame-Options: SAMEORIGIN`, relative links). The apex redirects 308 to `www`. |
| Known book links | `/index.html`, `/contents.html`, `/chapters/<slug>.html`, `/ledger/*`, `/downloads/computational-grammar-theory.pdf`, `/theorems.html`, `/lab.html`, `/sdk.html`, `/gaas.html`, `/researcher.html`, `/status.html`, `/feedback.html`, `/glossary.html`, `/bibliography.html`, `/search.html`, `/math-tests.html`, `/assets/*` |
| Supabase | No project exists for the university. The account's projects are other initiatives, and all but one are paused. None was modified. The schema is authored in `supabase/migrations/` and not applied. |

## 2. Decision: a client-only Vite + React SPA (not Next.js static export)

**Chosen: Vite 7 + React 19.2 + TypeScript + Three.js 0.181 + @react-three/fiber 9.4 + drei 10.7, with a React Router 7 browser router.**

The reasons:

1. **Nothing is server-rendered by design.** Every experience is generated in the browser: the 3D campus, exact arithmetic, astronomy, books and PDFs. Next.js would contribute a framework runtime and App Router conventions that this product does not use. `AGENTS.md` itself warned that this Next version breaks training-era assumptions.
2. **Static export friction.** Next `output: 'export'` needs `generateStaticParams` for every dynamic route (topics, specimens, books, glossary terms) and `'use client'` across nearly every file. A client-generated book id such as `/scriptorium/:bookId` cannot be pre-enumerated at all.
3. **Bundle control.** Vite with package-level `manualChunks` gives a measured split:

   | Chunk | Size | When it loads |
   |---|---|---|
   | Entry: React chunk + app chunk | 94 KB + 105 KB gzip | Initial load, with 12 KB CSS |
   | Three.js + r3f | 189 KB + 120 KB gzip | Once, after first paint |
   | pdf-lib | 508 KB gzip | Only when a visitor asks for a PDF |
   | astronomy-engine + star catalogue | ≈ 52 KB gzip | Only on the Observatory route |
   | supabase-js | ≈ 39 KB gzip | Only if cloud sync is configured |

4. **Workers and assets.** The path-signature Web Worker is a one-line `new Worker(new URL(...))`.
5. **Hosting stays the same.** Vercel serves the static `dist/`. `vercel.json` sets `"framework": "vite"` and overrides the dashboard preset.

## 3. What was removed and what was kept

- **Removed from the tree:** `app/`, `lab/`, `ledger/`, `scripts/`, the old `tests/`, `SPEC.md`, `next.config.mjs` and the provider `.env.example`. Removal is non-destructive: everything remains in Git history (`git show cccab10:app/page.tsx`). No history was rewritten.
- **No API routes, model providers or secrets remain.** The built bundle was audited: the only remote hosts referenced are `nominatim.openstreetmap.org` and `overpass-api.de`, and they are called only on an explicit button press. `*.supabase.co` is used only when configured.
- **The CGT book is preserved.** It is reachable unmodified at `/cgt/*`: `vercel.json` rewrites (proxies) that path to `computationalgrammartheory-sdk.vercel.app`. The site therefore serves the book from its own origin, so the book's `SAMEORIGIN` frame policy permits the in-site reader at `/library/computational-grammar-theory`. All known legacy book paths 308-redirect to `/cgt/...`. The SPA's own assets live under `/_u/` to keep `/assets/*` free for those legacy links.

## 4. Style bible (in code)

`src/style/bible.ts` holds the following, and `src/styles/global.css` holds the DOM side:
- palette tokens;
- three typography moods: engraved (Cinzel), luminous (Cormorant Garamond) and practical (Inter), plus a mathematical mono (JetBrains Mono, with DejaVu Sans Mono for 3D math glyphs);
- material rules, world-space sign fonts and camera choreography;
- lighting rules and mobile quality tiers.

Three renderer views were captured during development. These were successive iterations of one design rather than alternative concepts:
1. The first pass was too dark, the lintel was clipped, and realms collided with the wings.
2. The re-laid campus placed wings on the gap directions between realms, with brighter stone.
3. The final view adds a projection view offset, so each subject centres beside the desktop panel.

The third was implemented. Screenshots are in `docs/screenshots/`.

## 5. Campus layout

- **Gate and Hall of First Principles:** `z = 30 … 16`.
- **Atrium:** radius 15, with six doors on 30°…330° and the front open to the Gate.
- **Realms:** behind each door at radius 27.
- **Wings:** at radius 46, on the five remaining gap directions: Library 240°, Observatory 120°, Hall of Harness Masters 180°, Scriptorium 300°, Common Room 60°.

Every space is a route (`src/routes.tsx`). The camera anchors live in `src/world/locations.ts`.

## 6. Mathematics that drives the world (all unit-tested without WebGL)

| World change | Computation | Source module |
|---|---|---|
| Image-space sculpture at the Gate; inscription moves | exact rank, kernel and image of the accepted matrix | `src/math/matrix.ts` |
| Atrium bridges | typed admissibility predicate (distinct ends, degree bound, gold forest, connectivity) | `src/math/bridgeGrammar.ts` |
| Walkway compresses into one glyph | Re-Pair folds; unfold∘fold = id | `src/math/fold.ts` |
| Number of lit arches and their hue | orbit length 12 / gcd(12, k) | `src/math/music.ts` |
| Fictional courtyard portal | path-signature correspondence (signed turns, normalized Levenshtein) | `src/math/paths.ts` |
| Woven terrain | elementary cellular automaton; BORNE topological order | `src/math/world.ts` |
| Woven plate | typed `loom://` machine compiled to a 3×3 matrix | `src/math/addressCompiler.ts` |
| Campus and Observatory sky | Hipparcos J2000 rotated to horizontal coordinates by astronomy-engine | `src/math/sky.ts` |

## 7. Deployment status and the domain decision

- Pushing this branch creates a Vercel **preview** deployment of the `abedkadaancom` project (SSO-protected preview URL).
- The production branch of that project is still `claude/new-session-xd8auu`. Production and the custom domain were **not** changed.
- **To make the university live at `abedkadaan.com`** (an owner decision, not taken here):
  1. Merge this branch into the production branch, or set the project's production branch to it.
  2. In Vercel, move `abedkadaan.com`, `www.abedkadaan.com` and `*.abedkadaan.com` from `computationalgrammartheory-sdk` to `abedkadaancom`.
  3. Keep `computationalgrammartheory-sdk.vercel.app` deployed: `/cgt/*` proxies to it.
  4. Optional: restrict SSO protection so preview URLs stay private while the custom domain is public, which is the current setting.
- **To enable cloud sync:** create a Supabase project, apply the migration in `supabase/migrations/`, and set `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` (publishable key only) in Vercel.
- **To enable Harness Master contact:** set `VITE_HM_CONTACT_EMAIL` or `VITE_HM_BOOKING_URL`.

## 8. Known limitations

See README, "Known limitations".
