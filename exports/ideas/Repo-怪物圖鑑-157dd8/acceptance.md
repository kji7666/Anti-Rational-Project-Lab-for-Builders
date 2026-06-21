# Repo 怪物圖鑑 Acceptance Criteria

## 驗收標準
- [ ] 輸入 repo URL 後會產生一份報告
- [ ] 報告包含 setup/build/test 三段狀態
- [ ] 失敗時能指出失敗指令與錯誤摘要
- [ ] 至少 3 個測試 repo 可完成流程
- [ ] 所有外部執行都有 timeout

## 輸入
- GitHub repo URL
- 可選：指定分支或子目錄
- 可選：使用者補充的 setup 線索

## 預期輸出
- setup/build/test 狀態
- 失敗步驟與錯誤摘要
- 真正可用的執行 recipe
- Markdown 報告
