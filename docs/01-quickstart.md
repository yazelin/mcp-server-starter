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

## 健康檢查

```bash
python client_smoke_test.py
```

## 常用入口

- stdio JSON-RPC：initialize
- stdio JSON-RPC：tools/list
- stdio JSON-RPC：tools/call

## 第一次成功的標準

- 服務能啟動
- 基本 endpoint 有回應
- 範例流程能跑通
- 秘密 token 沒有 commit 到 GitHub
