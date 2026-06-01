# MCP Server 入門模板：部署與接入

這是一個純 stdio 的 MCP server：它沒有 HTTP port、沒有 `/health` endpoint，也不部署到 Render / Railway / Fly.io。MCP client（例如 Claude Desktop）會把它當成 subprocess 直接啟動，透過標準輸入／輸出交換 JSON-RPC。所謂「部署」其實是「讓 client 知道怎麼啟動這支程式」。

## 接入前檢查

- 本機流程已經跑通（`python client_smoke_test.py` 會印出三段 JSON-RPC 回應）。
- 設定好 `MCP_WORKSPACE`，確認 `read_text_file` 只能讀到你預期的目錄。
- `server.py`（或安裝後的 `mcp-server-starter` 指令）路徑是 client 能存取的絕對路徑。
- 執行檔有讀取權限；workspace 目錄權限正確。

## 在 Claude Desktop 設定啟動方式

編輯 Claude Desktop 的 MCP 設定檔（`claude_desktop_config.json`），加入一個 server 條目。client 會用 `command` + `args` 啟動 subprocess，並把 `env` 傳進去：

```json
{
  "mcpServers": {
    "mcp-server-starter": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-server-starter/server.py"],
      "env": {
        "MCP_WORKSPACE": "/absolute/path/to/your/workspace"
      }
    }
  }
}
```

如果你已經 `pip install -e .` 安裝了 console script，可以改用安裝後的指令：

```json
{
  "mcpServers": {
    "mcp-server-starter": {
      "command": "/absolute/path/to/.venv/bin/mcp-server-starter",
      "args": [],
      "env": {
        "MCP_WORKSPACE": "/absolute/path/to/your/workspace"
      }
    }
  }
}
```

設定後重啟 Claude Desktop，server 會在需要時被自動啟動，用完即關，不需要常駐。

## 打包與權限筆記

- 路徑一律用絕對路徑；client 的工作目錄不一定是你的 repo。
- 若用 venv，`command` 要指向該 venv 的 Python 或 console script，否則可能找不到正確的直譯器。
- `MCP_WORKSPACE` 請指向「允許被讀取」的目錄；`safe()` 會擋掉任何逃出此目錄的路徑（含 `..`、絕對路徑、symlink）。
- stdout 只能輸出 JSON-RPC。任何 debug 訊息請寫到 stderr，否則會破壞 framing。

## 想放到雲端？

如果你真的需要讓遠端 client 透過網路連線，要自行加上 HTTP / SSE transport（MCP 另一種傳輸方式）。這個 starter 只示範 stdio，**不包含** HTTP/SSE transport；那需要額外的伺服器程式與認證設計，不在本範本範圍內。

## 上線前實務提醒

接入不是最後一步。正式使用前至少要補：log（寫 stderr 或檔案，別污染 stdout）、錯誤告警、workspace 權限控管、備份策略，以及對 `read_text_file` 之類工具的存取範圍稽核。
