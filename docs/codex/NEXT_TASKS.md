# Recommended Next Tasks for Codex

## Task 1 — Stabilization pass

Goal:
Verify Phase 0-9 work together without regressions.

Work:

- Inspect backend routes for naming conflicts and missing imports.
- Check SQLite migrations for backward compatibility.
- Check frontend tabs/pages load correctly.
- Add a simple smoke test script if missing.
- Fix obvious runtime errors only.

Acceptance:

- Backend starts.
- Frontend builds.
- `/health` works.
- Core pages load.
- Existing data is not deleted.

## Task 2 — Add real LLM pipeline behind a feature flag

Goal:
Upgrade Phase 1 from template generation to real LLM-assisted idea generation while preserving current fallback generator.

Constraints:

- Do not remove the existing heuristic generator.
- Add provider config through environment variables.
- If no API key is configured, fallback to existing generator.
- Output must be parsed into the existing Idea schema.
- Add retry/repair for invalid JSON.

Suggested files:

- `backend/app/llm.py`
- `backend/app/generator.py`
- `backend/app/schemas.py`
- frontend generator page

Acceptance:

- User can choose `template` or `llm` generation mode.
- If LLM mode fails, template mode fallback is used.
- Generated ideas are saved like existing ideas.

## Task 3 — Repo probe sandbox design

Goal:
Make Phase 8 safer before enabling execution.

Work:

- Add a sandbox policy document.
- Keep `inspect_only` as default.
- Add clear UI warning for `local_execute`.
- Capture command plans before execution.
- Prepare Docker-based execution design, but do not overbuild unless requested.

Acceptance:

- No untrusted code runs unless explicitly requested.
- UI clearly marks unsafe modes.
- Report includes safety mode and executed commands.

## Task 4 — Product information architecture cleanup

Goal:
Make the app easier to navigate.

Suggested top-level navigation:

- Today
- Signals
- Ideas
- Graveyard
- Lab
- Taste
- Settings

Acceptance:

- Existing features are still reachable.
- Labels remain Traditional Chinese.
- Product personality is preserved.
