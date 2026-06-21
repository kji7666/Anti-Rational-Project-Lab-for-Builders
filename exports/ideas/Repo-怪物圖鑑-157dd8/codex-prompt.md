你要實作「Repo 怪物圖鑑」的 v0.1 prototype。

## 目標
把每個 GitHub repo 依照可馴服程度、危險程度、依賴毒性做成怪物卡。

## 背後痛點
很多開源專案看起來值得研究，但第一步就卡在 setup/build/test；使用者真正痛的是不知道 dev、評論、標題、摘要 這類專案到底能不能在乾淨環境跑起來。

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

## 任務
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

## 開發要求
- 先做最小可跑版本。
- 保持改動小而清楚。
- 不要擴大 scope。
- 完成後列出修改檔案、測試方式、尚未完成項目。
