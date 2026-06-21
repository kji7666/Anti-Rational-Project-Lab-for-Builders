# Repo 怪物圖鑑 MVP 草案

## 一句話
把每個 GitHub repo 依照可馴服程度、危險程度、依賴毒性做成怪物卡。

## 怪在哪裡
repo 不是專案，是野生怪物；setup/build/test 是馴服流程。

## 背後真痛點
很多開源專案看起來值得研究，但第一步就卡在 setup/build/test；使用者真正痛的是不知道 dev、評論、標題、摘要 這類專案到底能不能在乾淨環境跑起來。

## 第一個使用畫面
每張卡有怪物名、屬性、弱點、馴服指令、危險警告。

## 第一版 MVP
輸入 repo URL，根據檔案、依賴、setup 結果產生怪物卡與馴服步驟。

## 第一版只做
- 支援公開 GitHub repo
- 在隔離資料夾或容器中執行
- 擷取 README / package metadata
- 嘗試 setup/build/test
- 產生 Markdown 報告

## 第一版不做
- 不做登入與多人協作
- 不做大型 dashboard
- 不自動處理所有邊界案例
- 不把 scope 擴成平台
- 不在主機上執行不可信程式碼

## 輸入
- GitHub repo URL
- 可選：指定分支或子目錄
- 可選：使用者補充的 setup 線索

## 輸出
- setup/build/test 狀態
- 失敗步驟與錯誤摘要
- 真正可用的執行 recipe
- Markdown 報告

## 一週 Prototype 任務
1. 建立輸入 repo URL 的 CLI/API
2. clone repo 到隔離工作區
3. 讀取 README 與常見設定檔
4. 推斷 install/build/test 指令
5. 執行指令並記錄 stdout/stderr
6. 產生 Markdown 報告
7. 用 3 個 repo 做 smoke test

## 驗收標準
- 輸入 repo URL 後會產生一份報告
- 報告包含 setup/build/test 三段狀態
- 失敗時能指出失敗指令與錯誤摘要
- 至少 3 個測試 repo 可完成流程
- 所有外部執行都有 timeout

## 主要風險
- 題目可能只是 prompt 包裝
- MVP scope 可能膨脹
- 產出可能仍然太合理、缺少記憶點
- 執行陌生 repo 有安全風險，必須 sandbox
- 各語言生態差異大，第一版要限制範圍
- 很多 repo 需要 API key 或外部服務

## 評分
- 驚喜感：8/10
- 怪味：9/10
- 記憶點：7/10
- 畫面感：7/10
- 真痛點：8/10
- 一週可做性：8/10
- 差異化：7/10
- 個人適配：8/10
- 反 SaaS 感：8/10
- 復活潛力：6/10
