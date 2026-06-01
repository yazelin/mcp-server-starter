# MCP Server 入門模板：架構說明

## 核心檔案

- server.py：單檔 MCP JSON-RPC stdio server
- tools()：宣告 echo / now / read_text_file / word_count 工具（word_count 是 03 教學示範新增的範例工具）
- call()：依工具名稱執行實際邏輯
- safe()：用 MCP_WORKSPACE 做最基本的檔案安全邊界
- client_smoke_test.py：用 subprocess 模擬 MCP client 呼叫 server

## 資料流

這是純 stdio 的 MCP server，沒有 HTTP framework（不是 FastAPI），整個傳輸就是標準輸入／輸出上的換行分隔 JSON-RPC。

1. client（例如 Claude Desktop）以 subprocess 啟動 server，透過 stdin 送進一行 JSON-RPC 請求（newline-delimited JSON-RPC）。
2. `main()` 逐行讀取 stdin，`json.loads` 解析後交給 `handle()`。
3. `handle()` 依 method 分派：`initialize`、`tools/list`、`tools/call`、`notifications/initialized`。
4. `tools/call` 進入 `call()` 執行對應工具（echo / now / read_text_file），檔案類工具一律經過 `safe()` 限制在 `MCP_WORKSPACE` 內。
5. 結果以換行分隔 JSON-RPC 寫回 stdout 給 client；notification 類訊息不回應。

## 設計原則

- 先讓流程可跑，再做漂亮抽象。
- token 與 secrets 全部放在環境變數。
- 每一層保持可以替換：入口、AI provider、資料來源、部署方式。
- 範例程式刻意保持小，方便你看懂後改成自己的版本。
