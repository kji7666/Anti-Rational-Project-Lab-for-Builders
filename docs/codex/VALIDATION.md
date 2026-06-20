# Validation Guide

## Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m compileall app
python - <<'PY'
from app.db import init_db
init_db()
print('init_db OK')
PY
uvicorn app.main:app --host 127.0.0.1 --port 8790
```

Then open:

- `http://127.0.0.1:8790/health`
- `http://127.0.0.1:8790/docs`

## Frontend

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Then open:

- `http://127.0.0.1:5173`

## Manual smoke flow

1. Create or collect signals.
2. Generate weird idea cards.
3. Open Idea Board.
4. Open one idea detail page.
5. Run anti-rational review.
6. Generate MVP draft.
7. Export prototype task package.
8. Create prototype workspace.
9. Add prototype run ledger entry.
10. Run repo experiment in `inspect_only` mode.
11. Add taste feedback.
