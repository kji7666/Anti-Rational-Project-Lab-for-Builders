# Weird Lab Project State

## One-line product definition

Weird Lab / 怪題研究所 is a local-first creative lab that turns internet signals into strange-but-buildable project ideas, then pushes selected ideas toward MVP specs, prototype workspaces, experiments, and taste learning.

## Current implementation

The project currently has Phase 0-9 implemented.

### Phase 0

FastAPI + Vue + SQLite scaffold.

Core data models:

- Signal
- Idea
- Review
- Experiment
- Export

### Phase 1

Manual signals can generate weird idea cards.

Current generator is heuristic/template-based, not a real LLM pipeline.

### Phase 2

Idea lifecycle:

- new
- saved
- deep_dive
- mvp_draft
- prototype_ready
- prototype
- rejected
- dead
- revive_candidate
- merged

Includes graveyard, rejection reason, and revival condition.

### Phase 3

Anti-rational review and scoring.

Scores:

- surprise
- weirdness
- memorability
- visual imagination
- real pain
- MVP feasibility
- differentiation
- personal fit
- anti-SaaS
- revival potential

### Phase 4

MVP draft and prototype task package export.

Exports markdown files to `exports/ideas/<idea-name>-<id>/`.

### Phase 5

Automatic signal collection.

Current sources:

- GitHub repositories
- Hacker News
- arXiv

Includes fallback signals.

### Phase 6

Idea evolution.

Includes:

- similar idea detection
- idea families
- merge into parent idea
- evolution events
- graveyard revival suggestions

### Phase 7

Prototype workspace and run ledger.

Creates `prototypes/<idea-name>-<id>/` with docs, prompts, runs, logs, src, scratch.

### Phase 8

Repo probe experiments.

Modes:

- inspect_only
- local_dry_run
- local_execute

Default should remain `inspect_only`.

### Phase 9

Taste learning.

Uses lifecycle actions and explicit feedback to build a personal taste profile and idea recommendations.

## Known unfinished areas

1. Real LLM generation pipeline is not implemented.
2. Repo probe is not safely sandboxed yet.
3. Codex/OpenCode integration is prompt/export based only, not automatic execution.
4. Automatic collectors are early-stage and limited.
5. Similarity and taste learning are heuristic, not embedding-based.
6. UI is functional but not yet polished into a strong lab/graveyard/monster-book experience.
7. Tests are minimal and should be added.
