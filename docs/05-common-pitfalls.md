# MCP Server 入門模板：常見踩雷清單

這些是寫 stdio MCP server 時真的會踩到的坑，附上真實症狀與修法。

## 1. 把東西 print 到 stdout，污染了 JSON-RPC

stdio MCP server 的 stdout **只能放 JSON-RPC**。一行一個 JSON 物件，client 靠這個 framing 解析。你只要 `print(...)` 一個 debug 訊息，就會多吐一行非 JSON，client 解析第一行就炸。

症狀（在 `main()` 裡多一行 `print("DEBUG: server starting")`，client 端拿到的第一行不是 JSON）：

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

為什麼：client 預期 stdout 第一行就是合法 JSON，結果讀到 `DEBUG: server starting`，`json.loads` 直接失敗。

怎麼修：**所有 debug / log 一律寫到 stderr**，不要用 `print()`（它預設寫 stdout）。

```python
import sys
print("DEBUG: server starting", file=sys.stderr)   # 正確：走 stderr
```

stderr 不會干擾協定，client（如 Claude Desktop）通常會把它收進自己的 log。

## 2. method 名稱寫錯（listTools 不是 tools/list）

MCP 的 method 名稱是固定字串，且**有斜線**：`tools/list`、`tools/call`、`initialize`。寫成 `listTools`、`callTool`、`list_tools` 都不會被認得。

症狀（送 `listTools`）：

```json
{"jsonrpc": "2.0", "id": 7, "error": {"code": -32601, "message": "Method not found: listTools"}}
```

`-32601` 是 JSON-RPC 標準的「Method not found」錯誤碼。看到它，先檢查 method 字串是不是逐字打對、斜線有沒有少。

怎麼修：用 `tools/list` 而不是 `listTools`。method 名稱不要自己發明。

## 3. 忘了設 MCP_WORKSPACE（或設錯目錄）

`read_text_file` 的可讀範圍由 `MCP_WORKSPACE` 決定。沒設時預設是「server 啟動當下的工作目錄」——在 Claude Desktop 裡，那個目錄不一定是你以為的地方，於是你會發現「讀得到的檔案跟預期不一樣」或「明明存在的檔案讀不到」。

症狀（檔案其實在別的目錄，路徑相對於 workspace 解不到，被當成逃逸擋下）：

```json
{"jsonrpc": "2.0", "id": 5, "result": {"content": [{"type": "text", "text": "Path escapes workspace"}], "isError": true}}
```

怎麼修：在 client 設定檔（`claude_desktop_config.json`）的 `env` 明確指定 `MCP_WORKSPACE` 為絕對路徑，指向你允許被讀的目錄。詳見 `04-deployment.md`。

## 4. 加了工具 schema，卻忘了在 call() 加邏輯

加工具要改**兩個地方**：`tools()`（schema）和 `call()`（邏輯）。只加 schema 沒加邏輯，`tools/list` 看得到工具，但一呼叫就落到 `call()` 結尾的 `raise ValueError("Unknown tool: ...")`。

症狀（schema 有 `reverse`，但 `call()` 沒實作）：

```json
{"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "Unknown tool: reverse"}], "isError": true}}
```

怎麼修：在 `call()` 補上對應的 `if name=="reverse": ...`。反過來，只加邏輯沒加 schema，則是 AI / client 根本不知道有這工具（`tools/list` 看不到），也不會去呼叫。

## 5. 工具缺必填參數

`inputSchema` 裡 `required` 標記的欄位若沒傳，工具邏輯應該明確報錯，而不是丟出難懂的例外。本 starter 的 `read_text_file` 已這樣處理。

症狀（呼叫 `read_text_file` 但沒給 `path`）：

```json
{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "Missing required argument: path"}], "isError": true}}
```

這是「好的」錯誤：`isError: true` 加一句人看得懂的訊息。你自己寫新工具時，也建議先驗證必填參數再動手做事。

## 6. 沒裝 uv，或忘了先 `uv sync`

本教學用 uv 管理環境。兩個最常見的卡點：

- **沒裝 uv**：打 `uv ...` 直接 `command not found: uv`（Windows 是 `'uv' 不是內部或外部命令`）。先依 `01-quickstart.md` 安裝 uv（Ubuntu/macOS 用 install.sh、Windows 用 install.ps1），裝完**重開終端機**讓 PATH 生效，`uv --version` 印得出版本再繼續。
- **裝了 uv 但忘了先 `uv sync`**：在沒有 `.venv` 的情況下直接 `uv run mcp-server-starter`，會找不到安裝好的 console script。先在 repo 根目錄跑一次 `uv sync`（它會建立 `.venv` 並 build / 安裝本專案），之後 `uv run python server.py`、`uv run mcp-server-starter`、`uv run python client_smoke_test.py` 才會在對的環境裡執行。

`uv sync` / `uv run` 在 Ubuntu 與 Windows 完全相同，平台差異只在「怎麼安裝 uv」這一步。

## Debug 順序（針對 stdio MCP）

1. 先用 `uv run python client_smoke_test.py` 確認 server 本身協定正常。
2. 再手動 pipe 單一 method 進 `uv run python server.py`，縮小到哪一步出錯。
3. 確認 stdout 沒有被 `print` 污染（debug 全走 stderr）。
4. 確認 method 名稱、工具 `name` 逐字正確。
5. 確認 `MCP_WORKSPACE` 指向正確的絕對路徑。
6. 看完整錯誤訊息與 `isError` 欄位，別只看最後一行。

## 問別人前準備

- repo / branch
- 你打的完整指令與完整輸出（含 `error.code` 或 `isError`）
- `MCP_WORKSPACE` 設到哪（路徑可遮蔽敏感部分）
- 你已經檢查過哪些設定
