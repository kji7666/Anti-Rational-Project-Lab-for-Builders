# AGENTS.md

## Project

This repository is **Weird Lab / 怪題研究所**.

It is a local-first product for turning raw research signals into strange-but-buildable side-project ideas. The product flow is:

`Signal -> Weird Idea -> Anti-rational Review -> MVP Draft -> Prototype Workspace -> Experiment -> Taste Learning`

The current implementation already includes Phase 0 through Phase 9.

## Current phase status

Implemented:

- Phase 0: FastAPI + Vue + SQLite product scaffold
- Phase 1: manual signal input and weird idea card generation
- Phase 2: idea lifecycle, statuses, graveyard, revival candidates
- Phase 3: anti-rational review, commercial-smell detection, 10-dimensional scoring, rename suggestions
- Phase 4: MVP drafting and prototype task package export
- Phase 5: automatic signal collection from GitHub, Hacker News, and arXiv, with fallback signals
- Phase 6: idea similarity, merge suggestions, evolution events, revival suggestions
- Phase 7: prototype workspace and prototype run ledger
- Phase 8: repo setup/build/test probe experiments
- Phase 9: personal taste profile and feedback-based idea ranking

Next major work:

- Stabilize Phase 0-9 before adding more surface area.
- Add a real LLM pipeline for idea generation and review.
- Add safer sandboxing for repo experiments.
- Improve UI information architecture.
- Add tests.

## Tech stack

Backend:

- Python
- FastAPI
- SQLite
- Pydantic

Frontend:

- Vue
- Vite
- plain CSS

Data/output folders:

- `data/` for SQLite database
- `exports/ideas/` for exported task packages
- `prototypes/` for prototype workspaces
- `experiments/repo-probes/` for repo probe reports
- `logs/` for runtime/debug logs

## Setup commands

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8790
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Expected URLs:

- Frontend: `http://127.0.0.1:5173`
- Backend health: `http://127.0.0.1:8790/health`
- Backend docs: `http://127.0.0.1:8790/docs`

## Validation commands

Run these before reporting success:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m compileall app
python - <<'PY'
from app.db import init_db
init_db()
print('init_db OK')
PY
```

```powershell
cd frontend
npm install
npm run build
```

If tests are added later, prefer project-local test commands and update this file.

## Coding rules

- Keep changes small and reviewable.
- Do not rewrite the app unless the task explicitly asks for a rewrite.
- Preserve Phase 0-9 behavior unless a task explicitly changes it.
- Prefer additive changes over breaking migrations.
- SQLite migrations must be backward-compatible with existing `data/app.db`.
- Do not delete existing data, exports, prototypes, experiments, or logs without explicit approval.
- Do not run `local_execute` repo experiments by default.
- Treat external repos as untrusted code.
- Keep default repo experiment mode as `inspect_only`.
- Any command that executes unknown repository code must be opt-in and clearly documented.

## UI rules

- Keep the product language in Traditional Chinese.
- Use plain, direct labels.
- Avoid generic SaaS language such as dashboard, productivity, workflow platform, collaboration suite.
- Preserve the product personality: research lab, graveyard, weird ideas, anti-rational review, prototype incubation.
- Do not turn the product into a generic idea generator.

## Product rules

The product is not just a prompt wrapper. Every feature should strengthen at least one of these durable product assets:

- long-term signal library
- idea database
- idea lifecycle state
- anti-rational review history
- idea evolution history
- prototype records
- experiment results
- personal taste profile

When implementing a feature, include where the data is stored and how it affects the idea lifecycle.

## Safety rules

- Do not execute untrusted repository setup/build/test commands unless the task explicitly asks for it.
- Do not read or use host secrets.
- Do not add API keys to source code.
- Do not silently enable network-heavy crawlers.
- Prefer explicit user action for expensive, risky, or destructive operations.

## Reporting format

At the end of each task, report:

1. Files changed
2. What changed
3. Validation commands run and results
4. Known limitations
5. Suggested next step
