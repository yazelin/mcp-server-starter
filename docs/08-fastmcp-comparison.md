# MCP Server 入門模板：用 FastMCP 重寫(對照組)

前半段(`01`/`03`)你已經**從零手刻**了一個 stdio JSON-RPC server,看懂了協定的每一段。這一段是課程後半:同樣的功能,改用 **FastMCP** 寫,讓你親眼看到「同樣的事,可以多簡單」。

這是獨立的一課 —— 你可以先只跑前半段,真的體會過手刻的繁瑣,再回來看這段,對照感最強。

## 先講結論:差在哪

| 面向 | 完全手刻(`server.py`) | FastMCP(`server_fastmcp.py`) |
|---|---|---|
| 工具 schema | 自己手寫 `inputSchema` JSON | 從 type hints 自動生成 |
| 回傳包裝 | 自己包成 `content` 陣列 | 框架自動包 |
| error 信封 | 自己組 `isError` / JSON-RPC error code | 框架處理(tool 拋例外即 `isError:true`) |
| transport / handshake | 自己寫 stdin loop、`initialize` 回應 | `mcp.run()` 一行 |
| 三原語 | 只有 tool | tool + resource + prompt 都只要一個 decorator |
| **安全邊界** | 自己寫 `safe()` | **一樣要自己寫 `safe()`** |

兩條核心訊息:

1. **FastMCP 幫你做掉協定樣板**:schema、content 包裝、error 信封、transport/handshake 全包了。對照 `server.py` 那段密密麻麻的 `handle()`,FastMCP 版只是一串 `@mcp.tool`。
2. **FastMCP 不幫你做你的安全邏輯**:`read_text_file` 的路徑沙箱還是你自己寫的同一個 `safe()`。記住這句:**框架省掉協定樣板,但安全邏輯永遠是你自己的責任。**

## 步驟 1:裝 FastMCP(這就是第一個對照點)

前半段 `uv sync` 不裝任何第三方套件。FastMCP 版需要多裝一個套件,所以放在 optional extra:

```bash
uv sync --extra fastmcp
```

成功的話 `uv run python -c "import fastmcp; print(fastmcp.__version__)"` 會印出 `3.4.x`。
對照點:**多一個相依、多一步安裝,但下面你會看到程式碼少一大截。**

## 步驟 2:看 `server_fastmcp.py`

完整檔案在 repo 根目錄。重點是:每個工具就是一個帶 type hints 的函式 + 一個 decorator,schema 由 FastMCP 從型別自動生:

```python
from fastmcp import FastMCP
mcp = FastMCP("mcp-server-starter-fastmcp")

@mcp.tool
def echo(text: str) -> str:
    """Echo text"""
    return text

@mcp.tool
def word_count(text: str) -> str:
    """Count whitespace-separated words in text"""
    return str(len(text.split()))
```

對照手刻版:你不用寫 `inputSchema`(型別就是 schema)、不用把回傳包成 `content` 陣列、不用組 error。`read_text_file` 唯一「自己寫」的部分,是那個跟 `server.py` 一模一樣的 `safe()` 邊界 —— 這正是重點。

## 步驟 3:跑同一份 smoke test

關鍵設計:`client_smoke_test.py` 用 `MCP_SMOKE_TARGET` 切換目標,**同一份測試、同一組斷言**,對兩種實作都過 —— 證明它們行為完全相同。

```bash
MCP_SMOKE_TARGET=server_fastmcp.py uv run python client_smoke_test.py
```

真實輸出(FastMCP 的回應多了 `_meta` / `structuredContent` 欄位,但 `content` / `isError` 語意一致):

```json
{"jsonrpc":"2.0","id":3,"result":{"_meta":{"fastmcp":{"wrap_result":true}},"content":[{"type":"text","text":"hello"}],"structuredContent":{"result":"hello"},"isError":false}}
```

收尾會看到 `OK: all 6 checks passed (target=server_fastmcp.py)`。把 `MCP_SMOKE_TARGET` 拿掉(預設 `server.py`)再跑一次,你會看到同樣 6 項全過 —— 兩種寫法、同一份測試。

## 步驟 4:第三原語 —— resource 與 prompt

手刻版只有 **tool**。FastMCP 讓另外兩個原語也只要一個 decorator。先分清楚三者「誰主導」:

- **tool**:模型自己決定何時呼叫(echo / now / read_text_file / word_count)。
- **resource**:應用程式/使用者挑來當 context 的唯讀資料,用 URI 定址。
- **prompt**:使用者主動觸發的可重用提示範本(在 client 端常是 slash 指令)。

resource 範例(跟 `read_text_file` 這個 tool 成對照 —— 同一個 workspace,一個模型主動讀、一個應用提供):

```python
@mcp.resource("workspace://files")
def workspace_files() -> str:
    """List the files under MCP_WORKSPACE (read-only context)."""
    return "\n".join(sorted(p.name for p in WORKSPACE.iterdir()))
```

prompt 範例 —— **這個放在這裡是「認識用」**:在這種極簡工具 server 裡 prompt 沒有非做不可的好理由,放一個最小範例只是讓你知道有這個原語、它長什麼樣:

```python
@mcp.prompt
def explain_word_count(text: str) -> str:
    """Awareness-only example of the third MCP primitive."""
    return f"Count the words in this text and explain your reasoning step by step:\n\n{text}"
```

驗證這兩個(手刻版沒有,所以是獨立的一支測試):

```bash
MCP_WORKSPACE="$PWD" uv run python client_smoke_test_fastmcp.py
```

成功會看到 `OK: FastMCP bonus checks passed (resource + prompt)`。

## 步驟 5:掛到 Claude(跟前半段一樣是 stdio)

FastMCP 版預設也是 stdio,所以 Claude Desktop 設定方式跟 `04-deployment.md` 一樣,只是改用 FastMCP 的 console script:

```json
{
  "mcpServers": {
    "mcp-server-starter-fastmcp": {
      "command": "uv",
      "args": ["run", "--project", "/absolute/path/to/mcp-server-starter",
               "--extra", "fastmcp", "mcp-server-starter-fastmcp"],
      "env": { "MCP_WORKSPACE": "/absolute/path/to/your/workspace" }
    }
  }
}
```

注意多了 `--extra fastmcp`,因為 FastMCP 版需要那個 optional 相依。

## 何時選哪一種

- **手刻**(前半段):學習、理解協定、極簡或受限環境(不想帶第三方相依)。
- **FastMCP**(這一段):實際做事、工具一多、要 resource/prompt、長期維護 —— 少寫一堆樣板,專注在你的邏輯與安全邊界。

兩者不是取代關係:先手刻看懂底層,再用 FastMCP 拿生產力,你會更知道框架替你做了什麼、又沒替你做什麼。

## 延伸資源 · Awesome MCP

看懂協定後,想挖更多真實 MCP server:

- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — 官方參考實作集合。
- [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) — 社群整理的 MCP server 大清單。

也可以看本作者的真實 MCP:[erpnext-mcp](https://github.com/yazelin/erpnext-mcp)(接 ERPNext REST API)、[nanobanana-py](https://github.com/yazelin/nanobanana-py)(影像生成 MCP)。
