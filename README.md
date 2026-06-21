# Weird Lab / 怪題研究所

怪題研究所是一個 local-first 的古怪點子實驗室。

它不是一般的點子生成器，也不是普通的 SaaS 儀表板。產品核心是把原始研究訊號整理成「奇怪但可做」的 side project 想法，並一路推進到反商業審查、MVP 草稿、原型工作區、repo 實驗與個人口味學習。

產品流程：

`Signal -> Weird Idea -> Anti-rational Review -> MVP Draft -> Prototype Workspace -> Experiment -> Taste Learning`

## 目前功能階段

- Phase 0：FastAPI + Vue + SQLite 基礎骨架
- Phase 1：手動輸入 signals，產生 weird idea cards
- Phase 2：點子生命週期、狀態流轉、graveyard、revival candidate
- Phase 3：anti-rational review、commercial smell、10 維分數、改名建議
- Phase 4：MVP 草稿與 prototype task package 匯出
- Phase 5：GitHub / Hacker News / arXiv 自動收集素材，含內建補位機制
- Phase 6：相似點子、idea family、merge suggestions、revive suggestions、idea events
- Phase 7：prototype workspace 與 run ledger
- Phase 8：repo setup / build / test probe experiments
- Phase 9：personal taste profile、feedback、taste fit、recommendations

目前優先工作不是擴大功能，而是先穩定 Phase 0-9。

## 技術堆疊

後端：

- Python
- FastAPI
- SQLite
- Pydantic

前端：

- Vue
- Vite
- plain CSS

資料與輸出目錄：

- `data/`：SQLite 資料庫
- `exports/ideas/`：匯出的 task package
- `prototypes/`：prototype workspaces
- `experiments/repo-probes/`：repo probe 報告
- `logs/`：執行紀錄與除錯輸出

## 啟動方式

### Backend

建議在這個 Windows VM 使用 Python 3.13 進行開發與驗證。

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8790
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## 預設網址

- Frontend：`http://127.0.0.1:5173`
- Backend health：`http://127.0.0.1:8790/health`
- Backend docs：`http://127.0.0.1:8790/docs`

## 驗證指令

### Backend

```powershell
cd backend
py -3.13 -m compileall app
py -3.13 -c "from app.db import init_db; init_db(); print('init_db OK')"
```

如要確認 API 可啟動：

```powershell
cd backend
py -3.13 -m uvicorn app.main:app --host 127.0.0.1 --port 8790
```

然後檢查：

- `http://127.0.0.1:8790/health`
- `http://127.0.0.1:8790/docs`

### Frontend

```powershell
cd frontend
npm install
npm run build
```

## 手動 smoke flow

1. 建立或收集 signals
2. 產生 weird idea cards
3. 打開 Idea Board
4. 查看單一 idea 詳細內容
5. 執行 anti-rational review
6. 產生 MVP draft
7. 匯出 prototype task package
8. 建立 prototype workspace
9. 新增 prototype run ledger
10. 以 `inspect_only` 模式執行 repo probe
11. 新增 taste feedback

## Repo Probe 安全提醒

Phase 8 的 repo probe 會接觸外部 repository，預設必須保持保守。

- 預設模式必須是 `inspect_only`
- 不要預設執行 `local_execute`
- `local_execute` 只適合 disposable VM 或明確信任的 repository
- 不要把 host secrets、API keys、私人 `.env` 帶進不受信任 repo
- 報告中應清楚標示使用的 mode、推測出的命令與風險

目前產品重點仍然是「看懂 repo、規劃 setup/build/test、留下報告」，不是自動執行不受信任程式碼。

## 產品原則

- 介面對使用者維持繁體中文
- 保留 weird lab / graveyard / anti-rational review 的產品個性
- 不要把產品改造成 generic AI dashboard
- 每個功能最好都能強化長期資產：
  - signal library
  - idea database
  - lifecycle state
  - anti-rational review history
  - idea evolution history
  - prototype records
  - experiment results
  - taste profile

## 已知限制

- 目前 generator、reviewer、similarity、taste learning 多數仍是 heuristic，不是真正的 LLM pipeline
- repo probe 還沒有完整沙盒
- 前端與整體 UX 還有整理空間
- 自動 collectors 仍屬早期版本
- 測試覆蓋仍然不足
