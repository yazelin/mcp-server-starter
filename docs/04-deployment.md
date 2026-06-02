# MCP Server 入門模板：部署與接入

這是一個純 stdio 的 MCP server：它沒有 HTTP port、沒有 `/health` endpoint，也不部署到 Render / Railway / Fly.io。MCP client（例如 Claude Desktop）會把它當成 subprocess 直接啟動，透過標準輸入／輸出交換 JSON-RPC。所謂「部署」其實是「讓 client 知道怎麼啟動這支程式」。

## 接入前檢查

- 已跑過 `uv sync`，且本機流程跑通（`uv run python client_smoke_test.py` 會印出三段 JSON-RPC 回應）。
- 設定好 `MCP_WORKSPACE`，確認 `read_text_file` 只能讀到你預期的目錄。
- `server.py`（或安裝後的 `mcp-server-starter` 指令）路徑是 client 能存取的絕對路徑。
- 執行檔有讀取權限；workspace 目錄權限正確。

## 在 Claude Desktop 設定啟動方式

編輯 Claude Desktop 的 MCP 設定檔（`claude_desktop_config.json`），加入一個 server 條目。client 會用 `command` + `args` 啟動 subprocess，並把 `env` 傳進去。

本教學用 uv 管理環境，所以最穩的做法是讓 client 透過 `uv run` 啟動：`command` 設成 `uv`，用 `--project` 指向 repo 絕對路徑（這樣不管 client 從哪個工作目錄啟動，uv 都找得到正確的 `.venv` 與 console script），再用 `--project` 後面的 `mcp-server-starter` 跑安裝好的 console script：

```json
{
  "mcpServers": {
    "mcp-server-starter": {
      "command": "uv",
      "args": ["run", "--project", "/absolute/path/to/mcp-server-starter", "mcp-server-starter"],
      "env": {
        "MCP_WORKSPACE": "/absolute/path/to/your/workspace"
      }
    }
  }
}
```

上面這個形式我實際用 `uv run --project ... mcp-server-starter` 從別的工作目錄餵 `initialize` 驗證過，協定正常、`MCP_WORKSPACE` 仍由 `env` 獨立決定。如果 `uv` 不在 client 的 `PATH` 上，把 `command` 換成 uv 的絕對路徑（Ubuntu / macOS 通常是 `~/.local/bin/uv`，Windows 通常是 `%USERPROFILE%\.local\bin\uv.exe`）。

> 也可以不經 console script，直接 `args: ["run", "--project", "/absolute/path/to/mcp-server-starter", "python", "/absolute/path/to/mcp-server-starter/server.py"]`，效果相同（同樣實測過）。注意 `python` 後面要給 `server.py` 的絕對路徑，因為 client 啟動時的工作目錄不一定是 repo。Windows 上 `command` / `args` 寫法一致，只是路徑改用反斜線。

設定後重啟 Claude Desktop，server 會在需要時被自動啟動，用完即關，不需要常駐。

## 打包與權限筆記

- 路徑一律用絕對路徑；client 的工作目錄不一定是你的 repo。用 `uv run --project <絕對路徑>` 就是為了在這種情況下仍能定位到正確環境。
- 部署機上要先 `uv sync` 過一次（建立 `.venv` 並裝好 console script），client 之後才能用 `uv run` 啟動。
- `MCP_WORKSPACE` 請指向「允許被讀取」的目錄；`safe()` 會擋掉任何逃出此目錄的路徑（含 `..`、絕對路徑、symlink）。
- stdout 只能輸出 JSON-RPC。任何 debug 訊息請寫到 stderr，否則會破壞 framing。

## 想放到雲端？

如果你真的需要讓遠端 client 透過網路連線，要自行加上 HTTP / SSE transport（MCP 另一種傳輸方式）。這個 starter 只示範 stdio，**不包含** HTTP/SSE transport；那需要額外的伺服器程式與認證設計，不在本範本範圍內。

## 上線前實務提醒

接入不是最後一步。正式使用前至少要補：log（寫 stderr 或檔案，別污染 stdout）、錯誤告警、workspace 權限控管、備份策略，以及對 `read_text_file` 之類工具的存取範圍稽核。
