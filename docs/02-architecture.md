# MCP Server 入門模板：架構說明

## 核心檔案

- server.py：單檔 MCP JSON-RPC stdio server
- tools()：宣告 echo / now / read_text_file 三個工具
- call()：依工具名稱執行實際邏輯
- safe()：用 MCP_WORKSPACE 做最基本的檔案安全邊界
- client_smoke_test.py：用 subprocess 模擬 MCP client 呼叫 server

## 資料流

1. 使用者或 client 發出請求。
2. FastAPI / stdio 入口接收資料。
3. handler 解析訊息與設定。
4. adapter / tool / search 層執行實際工作。
5. 回傳最小可理解的結果。

## 設計原則

- 先讓流程可跑，再做漂亮抽象。
- token 與 secrets 全部放在環境變數。
- 每一層保持可以替換：入口、AI provider、資料來源、部署方式。
- 範例程式刻意保持小，方便你看懂後改成自己的版本。
