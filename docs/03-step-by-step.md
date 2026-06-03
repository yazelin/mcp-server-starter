# MCP Server 入門模板：帶你走一遍

這份文件不是六條指路，而是帶你「實際走過」一遍 MCP 協定，最後親手加一個工具。所有輸出都是真的跑出來貼上的。

讀之前先記住一件事：**這整支 server 就是「讀一行 JSON-RPC 請求 → 回一行 JSON-RPC 回應」**。沒有 HTTP、沒有 framework。看懂這個迴圈，就看懂了 MCP server。

> 開始前請先在 repo 根目錄跑過一次 `uv sync`（uv 安裝方式見 `01-quickstart.md`）。本文所有指令都用 `uv run python server.py`，它會在 uv 建好的 `.venv` 裡執行；`uv sync` / `uv run` 在 Ubuntu 與 Windows 完全相同。下面的 `printf ... | ...` 多行 pipe 是 bash 寫法（Ubuntu / macOS / WSL）；Windows 原生 PowerShell 把單行請求用 `'...' | uv run python server.py` 送進去即可。

`server.py` 的核心只有三個函式：

- `tools()`：宣告有哪些工具、每個工具的 input schema（給 AI 看的「使用說明」）。
- `call(name, args)`：依工具名稱執行真正的邏輯。
- `handle(req)`：依 JSON-RPC 的 `method` 分派到上面兩者，組出回應。

## 步驟 1：initialize — 握手

client 連上來的第一件事是 `initialize`，宣告協定版本、問 server 有什麼能力。

請求：

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

把它 pipe 進 server：

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
| MCP_WORKSPACE="$PWD" uv run python server.py
```

真實回應：

```json
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "mcp-server-starter", "version": "0.1.0"}}}
```

重點看 `capabilities.tools`：server 在這裡告訴 client「我有 tools 能力」，client 之後才會去問 `tools/list`。

## 步驟 2：tools/list — 拿工具清單

client 接著問「你有哪些工具？」。server 回的就是 `tools()` 的內容。

請求：

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

真實回應：

```json
{"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "echo", "description": "Echo text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}, {"name": "now", "description": "Current local time", "inputSchema": {"type": "object", "properties": {}}}, {"name": "read_text_file", "description": "Read UTF-8 text under MCP_WORKSPACE", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}]}}
```

每個工具有三個欄位：`name`（呼叫時用的名字）、`description`（給 AI 判斷何時用）、`inputSchema`（JSON Schema，描述要傳什麼參數）。`required` 列出必填欄位。AI 就是靠這份 schema 決定怎麼填參數。

> 注意：你 clone 下來的 repo **已內建第四個工具 `word_count`**，所以實際跑 `tools/list` 會比上面多一筆。這裡先列三個核心工具把協定形狀看清楚；步驟 5 會示範 `word_count` 就是怎麼用「兩個地方各加一段」加上去的。

## 步驟 3：tools/call — 真的呼叫一個工具

請求（呼叫 `now`，不需要參數）：

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"now","arguments":{}}}
```

真實回應：

```json
{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "2026-06-02T03:28:51+08:00"}], "isError": false}}
```

注意回應形狀：`result.content` 是一個陣列，每個元素有 `type` 與 `text`。`isError: false` 代表工具成功。MCP 規定工具結果一律包成這種 `content` 陣列，而不是裸字串。

## 步驟 4：安全邊界 — 親眼看它擋下逃逸

`read_text_file` 只能讀 `MCP_WORKSPACE` 底下的檔案。負責守門的是 `safe()`：

```python
def safe(rel):
    p=(WORKSPACE/rel).resolve()
    if WORKSPACE!=p and WORKSPACE not in p.parents:
        raise ValueError("Path escapes workspace")
    return p
```

關鍵在 `.resolve()`：它把 `..`、symlink、絕對路徑全部攤平成「真實的最終路徑」，再檢查這個真實路徑是不是落在 workspace 裡。攤平之後再比對，`../` 這種小聰明就沒用了。

先看「合法讀檔」會成功：

```bash
echo "hello from workspace" > note.txt
echo "line two" >> note.txt
printf '%s\n' \
'{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"read_text_file","arguments":{"path":"note.txt"}}}' \
| MCP_WORKSPACE="$PWD" uv run python server.py
```

真實回應：

```json
{"jsonrpc": "2.0", "id": 4, "result": {"content": [{"type": "text", "text": "hello from workspace\nline two\n"}], "isError": false}}
```

現在試著「逃出 workspace」。我們同時試 `../sibling-secret.txt`（往上一層）和 `/etc/passwd`（絕對路徑）：

```bash
printf '%s\n' \
'{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"read_text_file","arguments":{"path":"../sibling-secret.txt"}}}' \
'{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"read_text_file","arguments":{"path":"/etc/passwd"}}}' \
| MCP_WORKSPACE="$PWD" uv run python server.py
```

真實回應（兩個都被擋）：

```json
{"jsonrpc": "2.0", "id": 5, "result": {"content": [{"type": "text", "text": "Path escapes workspace"}], "isError": true}}
{"jsonrpc": "2.0", "id": 6, "result": {"content": [{"type": "text", "text": "Path escapes workspace"}], "isError": true}}
```

成功的話你會看到：兩行都是 `"Path escapes workspace"`、`"isError": true`。這是這個 starter 最重要的一課——**把檔案讀取工具交給 AI 之前，邊界要先擋死**。注意它不是丟出 transport 錯誤，而是回一個 `isError: true` 的乾淨工具錯誤，client 收到後能判斷「這個工具失敗了」而不是「連線壞了」。

## 步驟 5：加一個你自己的工具（兩個地方）

加工具永遠是改兩個地方：

1. 在 `tools()` 加一筆 schema（讓 AI 知道有這工具、要傳什麼）。
2. 在 `call()` 加一段邏輯（真正執行）。

下面是我實際加進這個 repo 的範例工具 `word_count`，數一段文字有幾個詞。

`tools()` 改之前（結尾）：

```python
{"name":"read_text_file","description":"Read UTF-8 text under MCP_WORKSPACE","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}]
```

`tools()` 改之後（多一筆 `word_count`）：

```python
{"name":"read_text_file","description":"Read UTF-8 text under MCP_WORKSPACE","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},{"name":"word_count","description":"Count whitespace-separated words in text","inputSchema":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}}]
```

`call()` 改之前：

```python
    if name=="now": return datetime.now().astimezone().isoformat(timespec="seconds")
```

`call()` 改之後（下面多一行）：

```python
    if name=="now": return datetime.now().astimezone().isoformat(timespec="seconds")
    if name=="word_count": return str(len(args.get("text","").split()))
```

注意 `call()` 一律回**字串**；`handle()` 會幫你把字串包進 MCP 的 `content` 陣列，你不用自己包。

改完，先確認它出現在 `tools/list`，再呼叫它：

```bash
printf '%s\n' \
'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
'{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"word_count","arguments":{"text":"the quick brown fox jumps"}}}' \
| MCP_WORKSPACE="$PWD" uv run python server.py
```

真實回應（節錄；`tools/list` 現在多一筆 `word_count`，呼叫回 `"5"`）：

```json
{"jsonrpc": "2.0", "id": 1, "result": {"tools": [..., {"name": "word_count", "description": "Count whitespace-separated words in text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}]}}
{"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "5"}], "isError": false}}
```

成功的話你會看到：`word_count` 出現在工具清單，且 `"the quick brown fox jumps"`（5 個詞）回 `"5"`。

> 想移除它：把上面兩處新增的內容刪掉即可（`tools()` 那一筆 schema、`call()` 那一行 `if`），server 就回到原本三個工具。

## 動手練習

換你自己加一個工具。建議做 `reverse`：把傳進來的 `text` 反轉後回傳。

提示：

1. 在 `tools()` 仿照 `echo` 加一筆，`name` 改成 `reverse`、`description` 寫「Reverse text」、`inputSchema` 用同樣的 `text` 欄位。
2. 在 `call()` 加一行：`if name=="reverse": return args.get("text","")[::-1]`
3. 用下面這行驗證：

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"reverse","arguments":{"text":"hello"}}}' \
| MCP_WORKSPACE="$PWD" uv run python server.py
```

預期你會看到 `"text": "olleh"`、`"isError": false`。如果回的是 `"Unknown tool: reverse"`，代表你 schema 加了但 `call()` 忘了加邏輯（或名字拼錯）——這正是下一份 `05-common-pitfalls.md` 會講的常見錯誤。
