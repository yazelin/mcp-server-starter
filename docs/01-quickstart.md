# MCP Server 入門模板：快速開始

## 前置需求

- Python 3.10+
- Git
- 可以使用終端機
- 如果要接真實 AI 或平台 token，請準備對應帳號與 API key。

## 最短路徑

1. 直接執行 smoke test
2. 看懂 initialize、tools/list、tools/call 三個流程
3. 設定 MCP_WORKSPACE 限制讀檔範圍
4. 再接到 Claude Desktop / Cursor 等 client

## 安裝與啟動

```bash
git clone https://github.com/yazelin/mcp-server-starter.git
cd mcp-server-starter
python client_smoke_test.py
# 或手動啟動 stdio server
python server.py
```

## 驗證跑通

```bash
python client_smoke_test.py
```

會印出 initialize、tools/list、tools/call 三段 JSON-RPC 回應即代表正常。

## 常用入口（皆為 stdio JSON-RPC，無 HTTP endpoint）

- initialize
- tools/list
- tools/call

## 第一次成功的標準

- `python server.py` 能逐行讀取 stdin 並回應 JSON-RPC
- smoke test 三段回應都正常
- 設好 `MCP_WORKSPACE`，`read_text_file` 只能讀到範圍內檔案
- 沒有把任何 secret 或 workspace 路徑誤 commit 到 GitHub
