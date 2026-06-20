# 怪題研究所 Phase 9

Phase 9 新增「個人品味學習」：系統會從你對題目的狀態操作與明確回饋中，推估你偏好的怪題方向，並把題目依「符合你的品味程度」排序。

## 已完成到 Phase 9

- Phase 0：本機 app 骨架、FastAPI、SQLite、Signal / Idea CRUD
- Phase 1：手動素材 → 怪題卡片產生器
- Phase 2：題目庫、狀態流轉、墳場、復活候選
- Phase 3：反合理審查、怪味評分、商業味偵測、改名建議
- Phase 4：MVP 收斂與 Prototype 任務包輸出
- Phase 5：自動素材收集
- Phase 6：題目合併、演化紀錄、復活建議、題目族群分析
- Phase 7：Prototype Workspace 與 Run Ledger
- Phase 8：Repo Setup / Build / Test 實驗系統
- Phase 9：個人品味學習、明確回饋、品味適配分、依品味推薦題目

## Phase 9 新增 API

```text
GET  /taste/profile
POST /taste/feedback
GET  /ideas/{idea_id}/taste-fit
POST /ideas/{idea_id}/apply-taste-score
GET  /taste/recommendations
```

## Phase 9 新增資料表

```text
taste_feedback      明確喜好/厭惡回饋
user_preferences    預留的個人偏好設定表
```

## 啟動後端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8790
```

## 啟動前端

```powershell
cd frontend
npm install
npm run dev
```

前端：

```text
http://127.0.0.1:5173
```

API docs：

```text
http://127.0.0.1:8790/docs
```

## 建議測試流程

1. 到「怪題產生器」產生幾張怪題。
2. 在「Idea Board」把喜歡的題目設為收藏 / 深入研究 / MVP / Prototype。
3. 把不喜歡的題目丟進墳場，填死因。
4. 進入題目詳情，對題目按「超喜歡」「太無聊」「太 SaaS」。
5. 到「個人品味」分頁重新計算品味。
6. 查看偏好關鍵字、負向關鍵字、依你品味排序的題目。
7. 對某張題目按「寫入 personal_fit」，把適配分回寫到題目的 10 維評分。

## 注意

Phase 9 仍是本機 heuristic 版本，沒有使用外部 LLM 做個人化模型訓練。它的目標是先跑通產品閉環：

```text
你的操作 → 品味輪廓 → 題目推薦 → 回寫 personal_fit → 影響下一輪篩選
```
