# Substrate University — Haq Roots

**A free, public, browser-native university of the mathematics of possible worlds.** The campus is the interface; mathematics is its choreography. Founded by **Abed Kadaan** and **7u** (an AI collaborator). It is not an accredited degree-granting institution.

Visitors approach and enter an original Gothic-futurist campus rendered in Three.js:
- **The Gate:** the *Arithmetic of Possibility* asks what 1 + 1 is in ℕ, ℤ and F₂; classifies 0/1, 1/0 and 0/0 by image and kernel; and asks what survives a matrix.
- **The Atrium:** six division doors, each opening a realm with a curriculum, a contextual glossary and an exhibit that genuinely computes.
- **The Library of Forms:** the real *Computational Grammar Theory* book plus specimen volumes clearly marked as previews.
- **The Observatory:** a place, the real sky above it at any moment, and geometric path correspondences.
- **The Hall of Harness Masters**, **the Scriptorium** and **the Common Room**.

The flagship loop is the **One-Day Harness**: six stations of reading, exercise and reflection, then one contribution. It ends with **six personal books**, composed and typeset as PDFs in the browser and credited to the participant.

Everything generative runs in the visitor's browser. There is no server program, no AI model and no paid API.

## Run it

```bash
npm ci
npm run dev          # http://localhost:5173
npm test             # unit tests: math, registry, glossary, books, PDF export
npm run build        # typecheck + production build to dist/
npm run preview      # serve dist/ at http://localhost:4173
npm run test:e2e     # Playwright: desktop and Android-sized (412×915) suites
```

Optional environment variables (all public, browser-visible):

| Variable | Effect |
|---|---|
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` | Enable opt-in cloud sync and the consented public book catalogue. Apply `supabase/migrations/` first. Never use a service-role key. |
| `VITE_HM_CONTACT_EMAIL` | Adds a `mailto:` button to the Harness Master conversation request. |
| `VITE_HM_BOOKING_URL` | Adds a verified booking link. |

## Layout

| Path | Contents |
|---|---|
| `src/math/` | Browser-local mathematics with explicit domains: exact rationals, number systems, linear algebra, bridge grammar, folds, intervals, path signatures, sky, worlds, the `loom://` compiler |
| `src/content/` | The typed registry: 6 divisions and 62 topics with definitions, constraints, examples, challenges and sources; the glossary field with computable bridges; the CGT table of contents |
| `src/exhibits/` | The six exhibits and their record builders |
| `src/books/` | Scriptorium composition, plates and PDF export (pdf-lib + embedded DejaVu fonts) |
| `src/scene/` | Three.js campus: architecture, atrium, realms, residents, sky, materials |
| `src/pages/`, `src/ui/` | Every space as an accessible page; layout, settings, map, resident dialogue |
| `src/state/` | Local persistence (localStorage, wrapped) |
| `src/lib/cloud.ts` | Optional Supabase facility (lazy-loaded) |
| `supabase/migrations/` | Tables and row-level security for the optional facility |
| `tests/`, `e2e/` | Unit tests and browser tests; `docs/screenshots/` holds captured evidence |
| `docs/UNIVERSITY_REBUILD.md` | Audit, the framework decision, deployment and domain notes |

## Honesty rules this code keeps

- Every subject is labelled as established mathematics, a house construction, an application in development, or campus mythology.
- Residents and campus Harness Masters are fictional. Specimen books are previews. No alumni, enrolment or book counts are shown unless they come from stored, consented records.
- A book says what the participant did, what was sourced, what was computed and what was generated. A briefly visited station is described as an encounter.
- Geocoding and street data are requested only on explicit submission. Only rounded coordinates are kept.

## Known limitations

- 3D was tested on SwiftShader in a headless container. No measurements were recorded on a physical Samsung Galaxy A16. The low tier was designed for that class of device but has not been measured on one.
- In local `vite preview`, the `/cgt/` book proxy may not reach the book's deployment from restricted networks. In production, Vercel performs the rewrite.
- Cloud sync, the public participant catalogue and HM contact are implemented but inactive until configured.
- Street data comes from OpenStreetMap through public APIs. Coverage varies, and those services can be unavailable; synthetic fixtures are always available and labelled.
- Celestial positions neglect proper motion and parallax (errors far below 1° for catalogue stars). The observer's civil time zone is not computed.
