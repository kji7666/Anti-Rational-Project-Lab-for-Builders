# Phase 10 Candidate: Stabilization Before New Features

## Goal

Before adding new product features, stabilize the Phase 0-9 codebase.

## Work items

- Verify backend imports and route registration.
- Verify database migrations are additive and safe.
- Verify generated/exported paths are consistent.
- Verify frontend build.
- Add minimal smoke-test script if useful.
- Document any broken or risky behavior.

## Do not

- Do not rewrite the application.
- Do not remove fallback generators.
- Do not enable unsafe repo execution by default.
- Do not add cloud dependencies.

## Done when

- Backend compile passes.
- DB init passes.
- Frontend build passes.
- Manual smoke flow is documented.
