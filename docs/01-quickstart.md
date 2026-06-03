# MCP Server 入門模板：快速開始

這份文件帶你「不卡住、走完一遍、知道自己成功了」。每一步都有：要打的指令 → 跑完的真實輸出 → 成功的話你會看到什麼。

## 前置需求

- Python 3.10+
- Git
- 會用終端機
- [uv](https://docs.astral.sh/uv/)（本教學的環境管理工具）

不需要任何 API key，也不需要外部服務。這個 starter 只用 Python 標準函式庫，沒有第三方相依套件。

### 安裝 uv（一次就好）

Ubuntu / macOS：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows（PowerShell）：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

裝完重開終端機，`uv --version` 印得出版本就 OK。`uv sync` 會依 `pyproject.toml` + `uv.lock` 自動建立 `.venv` 並裝好套件（毋須手動 venv / activate），`uv run` 直接在那個環境裡執行。**以下 `uv sync` / `uv run` 在 Ubuntu 與 Windows 完全相同。**

## 這個 server 是什麼（先讀一句）

它是一個純 stdio 的 MCP server：**沒有 HTTP port、沒有 `/health`、不部署到雲端**。MCP client（例如 Claude Desktop）會把它當成 subprocess 啟動，透過標準輸入／輸出交換一行一行的 JSON-RPC 2.0 訊息。

## 步驟 1：取得程式

實際指令：

```bash
git clone https://github.com/yazelin/mcp-server-starter.git
cd mcp-server-starter
uv sync
```

成功的話你會看到：clone 完成，`ls` 看得到 `server.py`、`client_smoke_test.py`、`docs/`，而 `uv sync` 印出類似下面的訊息（會建立 `.venv` 並 build 本專案）：

```
Using CPython 3.11.13
Creating virtual environment at: .venv
Resolved 1 package in 1ms
   Building mcp-server-starter @ file:///path/to/mcp-server-starter
      Built mcp-server-starter @ file:///path/to/mcp-server-starter
Prepared 1 package in 942ms
Installed 1 package in 0.76ms
 + mcp-server-starter==0.1.0 (from file:///path/to/mcp-server-starter)
```

## 步驟 2：跑 smoke test（最快的驗證）

`client_smoke_test.py` 會用 subprocess 啟動 `server.py`，依序送出 `initialize`、`tools/list`、`tools/call`（echo、word_count）以及一次「逃出 workspace」的讀檔，把每段 JSON-RPC 回應印出來，最後對關鍵不變量做斷言（任何一項失敗會以非 0 結束，方便 CI 把關）。

實際指令：

```bash
uv run python client_smoke_test.py
```

真實輸出（這是實際跑出來的，不是示意）：

```json
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "mcp-server-starter", "version": "0.1.0"}}}
{"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "echo", "description": "Echo text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}, {"name": "now", "description": "Current local time", "inputSchema": {"type": "object", "properties": {}}}, {"name": "read_text_file", "description": "Read UTF-8 text under MCP_WORKSPACE", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}, {"name": "word_count", "description": "Count whitespace-separated words in text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}]}}
{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "hello"}], "isError": false}}
{"jsonrpc": "2.0", "id": 4, "result": {"content": [{"type": "text", "text": "5"}], "isError": false}}
{"jsonrpc": "2.0", "id": 5, "result": {"content": [{"type": "text", "text": "Path escapes workspace"}], "isError": true}}

OK: all 6 checks passed
```

成功的話你會看到：**五行 JSON**（`id` 1–5），最後一行是 `OK: all 6 checks passed`。

- `id:1` 是 `initialize` 的回應，帶 `protocolVersion` 與 `serverInfo`。
- `id:2` 是 `tools/list`，列出 `echo` / `now` / `read_text_file` / `word_count` 四個工具。
- `id:3` 是 `tools/call` 呼叫 `echo`，回 `"text": "hello"`、`"isError": false`。
- `id:4` 是 `tools/call` 呼叫 `word_count`，數「the quick brown fox jumps」5 個詞回 `"5"`。
- `id:5` 是故意用 `../../etc/passwd` 逃出 workspace，被 `safe()` 擋下，回 `"Path escapes workspace"`、`"isError": true`（這是「好的」失敗——乾淨的工具錯誤，不是連線壞掉）。

只要看到 `OK: all 6 checks passed`、且前面該成功的 `isError` 是 `false`、逃逸那筆是 `true`，就代表 client 與 server 的協定流程與安全邊界都跑通了。

## 步驟 3：手動把 JSON-RPC 餵進 server（理解協定）

你也可以不透過 smoke test，直接把訊息 pipe 進 `server.py`。這能讓你看到「一行請求換一行回應」的真實樣子：

實際指令：

```bash
printf '%s\n' \
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
'{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
'{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"now","arguments":{}}}' \
| MCP_WORKSPACE="$PWD" uv run python server.py
```

真實輸出（`now` 那一行的時間會跟著你目前時間變）：

```json
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "mcp-server-starter", "version": "0.1.0"}}}
{"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "echo", ...}, {"name": "now", ...}, {"name": "read_text_file", ...}, {"name": "word_count", ...}]}}
{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "2026-06-02T03:28:51+08:00"}], "isError": false}}
```

成功的話你會看到：`id:3` 回了一個目前的本地時間（ISO 8601 格式）。

> 平台差異：`uv sync` / `uv run` 兩平台完全相同。只有上面這種 `printf ... | ...` 多行 pipe 是 bash 寫法（Ubuntu / macOS / WSL）。在 Windows 原生 PowerShell 裡，最省事的做法是直接跑 `uv run python client_smoke_test.py`（步驟 2），它在兩平台都一致；要手動餵 JSON-RPC 時，把單行請求用 `'...' | uv run python server.py` 的形式送進去即可。

## 步驟 4：設定 MCP_WORKSPACE 限制讀檔範圍

`read_text_file` 只能讀 `MCP_WORKSPACE` 指向的目錄底下的檔案。沒設的話預設是目前工作目錄。

實際指令（在 workspace 內建一個檔，然後讀它）：

```bash
echo "hello from workspace" > note.txt
printf '%s\n' \
'{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"read_text_file","arguments":{"path":"note.txt"}}}' \
| MCP_WORKSPACE="$PWD" uv run python server.py
```

真實輸出：

```json
{"jsonrpc": "2.0", "id": 4, "result": {"content": [{"type": "text", "text": "hello from workspace\n"}], "isError": false}}
```

成功的話你會看到：檔案內容被讀回來、`isError` 是 `false`。
（安全邊界怎麼擋掉 `../` 與 `/etc/passwd`，在 `03-step-by-step.md` 有真實示範。）

## 第一次成功的標準（整體確認）

跑完上面四步，你應該能勾掉這份清單：

- [ ] `uv run python client_smoke_test.py` 印出五行 JSON（`id` 1–5）並以 `OK: all 6 checks passed` 收尾，該成功的 `isError` 為 `false`、逃逸那筆為 `true`。
- [ ] 手動 pipe 時，`tools/call` 的 `now` 回了一個合理時間。
- [ ] `read_text_file` 能讀到 `MCP_WORKSPACE` 內的檔案。
- [ ] 沒有把任何 secret 或本機絕對路徑誤 commit 到 GitHub。

接著看 `03-step-by-step.md`，那裡會帶你看懂每一段協定、示範安全邊界，並親手加一個新工具。
