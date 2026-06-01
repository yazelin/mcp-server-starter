# MCP Server 入門模板：完整操作流程

## 步驟

1. 先跑 python client_smoke_test.py，確認 server 可以初始化與列出工具。
2. 閱讀 server.py 的 handle(req)，理解 method 如何對應 result。
3. 修改 tools() 新增自己的工具 schema。
4. 在 call() 實作工具邏輯。
5. 設定 MCP_WORKSPACE，確認 read_text_file 只能讀工作區內檔案。
6. 再把 server.py 接到 MCP client。

## 建議紀錄

- 你使用的 Python 版本
- 啟動指令
- `MCP_WORKSPACE` 設定到哪個目錄；不要貼出實際路徑中的敏感資訊
- client（Claude Desktop 等）的 server 設定內容
- 錯誤訊息完整內容
- 你預期發生什麼、實際發生什麼

## 下一個里程碑

完成最小流程後，不要急著加功能。先找一個真實情境，讓這個 starter 解決一個很小但明確的問題。
