# Frontend Implementation

Date: 2026-05-14

## Files changed
- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/styles.css`

## Design rules applied
- Applied dark dashboard shell with tokenized CSS variables from `FRONTEND_DESIGN.md`.
- Used Arial-based compact typography and blue primary action token.
- Added explicit panel layout: sidebar (identity + demo queries), main workspace (chat), details (meta/evidence/guardrails).
- Added focus-visible outlines for keyboard accessibility.
- Added responsive breakpoints for desktop/tablet/mobile.

## Components created
- Kept a minimal structure in `App.jsx` with reusable `MetaBadge` subcomponent.
- Implemented UI sections:
  - app shell
  - product identity area
  - 5 required demo query buttons
  - chat workspace with user bubble + assistant answer card
  - response metadata badges
  - evidence panel
  - guardrail panel + disclaimer
  - empty state
  - loading state
  - backend error state
  - query composer with empty-query block

## Validation commands
- `cd frontend && npm install`
- `cd frontend && npm run build`
- Backend connectivity check (5 required queries) via local `/chat`:
  - all queries returned expected intent/route/confidence
  - evidence present
  - guardrails/disclaimer present

## Known limitations
- UI performs single-response rendering (no streaming).
- Query history is not persisted across reloads.
- Vietnamese text quality depends on terminal/browser font and encoding environment.
