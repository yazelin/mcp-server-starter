# FastMCP Comparison Second-Half Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second course track that reimplements the starter's exact functionality with FastMCP, as a contrast to the hand-rolled stdio server, teaching all three MCP primitives (tool / resource / prompt).

**Architecture:** Keep `server.py` (hand-rolled, zero-dep) unchanged. Add `server_fastmcp.py` reachable only via an optional `fastmcp` extra, so `uv sync` stays zero-third-party. One parametrized smoke test asserts the shared tool surface against either server (proving behavioral parity); a thin second smoke test covers the FastMCP-only resource + prompt. CI runs both tracks in a matrix. A new `docs/08-fastmcp-comparison.md` is the independent second-half lesson.

**Tech Stack:** Python 3.10+, uv, FastMCP 3.4.x, GitHub Actions. No pytest — the repo's tests are stdio smoke-test scripts; follow that grain.

---

## Preconditions / baseline

- All commands run from the repo root `mcp-server-starter/`.
- **Verified facts this plan relies on** (probed against FastMCP 3.4.0):
  - FastMCP requires a full `initialize` handshake **plus** a `notifications/initialized` notification before it serves `tools/list`. The hand-rolled `server.py` ignores both params and the notification, so one proper-handshake client works against both servers.
  - `mcp.run(show_banner=False)` keeps **stdout** clean JSON-RPC (the banner otherwise goes to stderr).
  - A FastMCP tool that raises `ValueError("Path escapes workspace")` returns `isError: true` with text `"Error calling tool 'read_text_file': Path escapes workspace"` — contains the substring `escapes workspace`.
  - `resources/read` returns `result.contents[0].text`; `prompts/list` returns `result.prompts[].name`; `prompts/get` returns `result.messages[0].content.text`.
  - FastMCP responses carry extra fields (`_meta`, `structuredContent`, `outputSchema`). Assert **semantics** (`content[0].text`, `isError`, tool-name set), never byte-exact output.
- **Working-tree note:** the earlier doc-drift fixes (including a rewrite of `client_smoke_test.py`) are uncommitted in the tree. Task 1 below replaces `client_smoke_test.py` again (proper handshake + target param). Decide before executing whether to commit the doc-drift fixes as their own commit/PR first; this plan assumes you build on the current tree.

---

## File structure

| File | Responsibility |
|---|---|
| `server_fastmcp.py` (create) | FastMCP server: 4 tools + `safe()` boundary + 1 resource + 1 prompt |
| `pyproject.toml` (modify) | `fastmcp` optional extra; second console script; include new module in wheel |
| `uv.lock` (regenerate) | lock the optional group |
| `client_smoke_test.py` (modify) | proper handshake + `MCP_SMOKE_TARGET`; asserts shared tool surface |
| `client_smoke_test_fastmcp.py` (create) | FastMCP-only bonus: resource + prompt |
| `.github/workflows/ci.yml` (modify) | matrix: stdlib track + fastmcp track |
| `docs/08-fastmcp-comparison.md` (create) | the second-half lesson + hand-rolled vs FastMCP contrast |
| `docs/00-overview.md` (modify) | reframe as two tracks |
| `tutorial.html` (modify) | web mirror: Part 2 section |
| `README.md`, `index.html`, `DESIGN.md` (modify) | FastMCP is now a built-in second half, not just "可延伸方向" |

---

## Task 1: Parametrize the shared smoke test with a proper handshake

**Files:**
- Modify: `client_smoke_test.py` (full rewrite)

- [ ] **Step 1: Write the new smoke test (this is the test).** Replace the entire contents of `client_smoke_test.py` with:

```python
#!/usr/bin/env python3
"""Smoke test for the MCP protocol surface shared by both server implementations.

Drives a stdio MCP server through a proper initialize handshake, then exercises
the four tools and the workspace security boundary, asserting the results.
Exits non-zero on any failure so CI can gate on it.

Target server is chosen by MCP_SMOKE_TARGET (default: server.py). The same
assertions pass against both server.py (hand-rolled) and server_fastmcp.py
(FastMCP) because they expose the same tools over the same protocol.
"""
import json, os, subprocess, sys

TARGET = os.getenv("MCP_SMOKE_TARGET", "server.py")
env = dict(os.environ, MCP_WORKSPACE=os.getcwd())
p = subprocess.Popen(
    [sys.executable, TARGET],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
)

def send(msg):
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()

def request(msg):
    send(msg)
    line = p.stdout.readline().strip()
    print(line)
    return json.loads(line)

try:
    init = request({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "smoke-test", "version": "0"}}})
    # Required by the MCP handshake: FastMCP won't serve requests without it;
    # the hand-rolled server ignores it (sends nothing back), so don't read a line.
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    listed = request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    echo = request({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "echo", "arguments": {"text": "hello"}}})
    wc = request({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                  "params": {"name": "word_count", "arguments": {"text": "the quick brown fox jumps"}}})
    # Security boundary: a path escaping MCP_WORKSPACE must be a clean tool error.
    escape = request({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                      "params": {"name": "read_text_file", "arguments": {"path": "../../etc/passwd"}}})
finally:
    p.kill()

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

names = {t["name"] for t in listed["result"]["tools"]}
check(init["result"]["serverInfo"]["name"].startswith("mcp-server-starter"), "initialize serverInfo.name")
check(names == {"echo", "now", "read_text_file", "word_count"}, f"tools == 4 expected, got {sorted(names)}")
check(echo["result"]["content"][0]["text"] == "hello" and echo["result"]["isError"] is False, "echo returns hello")
check(wc["result"]["content"][0]["text"] == "5" and wc["result"]["isError"] is False, "word_count of 5 words == 5")
check(escape["result"]["isError"] is True, "escape path is rejected (isError true)")
check("escapes workspace" in escape["result"]["content"][0]["text"], "escape error message mentions workspace")

if failures:
    print("\nFAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print(f"\nOK: all 6 checks passed (target={TARGET})")
```

- [ ] **Step 2: Run it against the hand-rolled server to verify it still passes.**

Run: `uv run python client_smoke_test.py`
Expected: 5 JSON lines (id 1–5), then `OK: all 6 checks passed (target=server.py)`, exit 0.

- [ ] **Step 3: Verify the failure path works (deliberately break one assertion locally, then revert).**

Run: `MCP_SMOKE_TARGET=nonexistent.py uv run python client_smoke_test.py; echo "exit=$?"`
Expected: a non-zero exit (the subprocess can't start / no output to parse). This confirms the test fails loudly. No file change to revert.

- [ ] **Step 4: Commit.**

```bash
git add client_smoke_test.py
git commit -m "test: parametrize smoke test with proper MCP handshake + MCP_SMOKE_TARGET"
```

---

## Task 2: Add the FastMCP optional extra

**Files:**
- Modify: `pyproject.toml`
- Regenerate: `uv.lock`

- [ ] **Step 1: Edit `pyproject.toml`.** The current `[project]` has no `dependencies` and a single console script. Apply these changes:

Add after the `description` line inside `[project]` (keep `dependencies` absent / empty so `uv sync` stays zero-third-party):

```toml
[project.optional-dependencies]
fastmcp = ["fastmcp>=3.4,<4"]
```

Replace the existing `[project.scripts]` block:

```toml
[project.scripts]
mcp-server-starter = "server:main"
mcp-server-starter-fastmcp = "server_fastmcp:main"
```

Replace the wheel-targets blocks so the new module is packaged:

```toml
[tool.hatch.build.targets.wheel]
# Two single top-level modules (not a package).
only-include = ["server.py", "server_fastmcp.py"]

[tool.hatch.build.targets.wheel.sources]
"server.py" = "server.py"
"server_fastmcp.py" = "server_fastmcp.py"
```

- [ ] **Step 2: Regenerate the lock and verify zero-dep default still holds.**

Run: `uv lock && uv sync`
Expected: `uv sync` resolves/builds only the local package — no third-party packages installed (FastMCP is NOT pulled in without the extra).

- [ ] **Step 3: Verify the extra installs FastMCP 3.4.x.**

Run: `uv sync --extra fastmcp && uv run python -c "import fastmcp; print(fastmcp.__version__)"`
Expected: prints a `3.4.x` version.

- [ ] **Step 4: Commit.**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add optional fastmcp extra + second console script"
```

---

## Task 3: Create the FastMCP server (four tools + boundary)

**Files:**
- Create: `server_fastmcp.py`

- [ ] **Step 1: Create `server_fastmcp.py`** with the tools only (resource/prompt added in Task 4):

```python
#!/usr/bin/env python3
"""FastMCP version of the starter server.

Same four tools and the same MCP_WORKSPACE security boundary as server.py, but
written with FastMCP instead of hand-rolled JSON-RPC. Requires the `fastmcp`
extra: `uv sync --extra fastmcp`.
"""
import os
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

WORKSPACE = Path(os.getenv("MCP_WORKSPACE", os.getcwd())).resolve()
mcp = FastMCP("mcp-server-starter-fastmcp")


def safe(rel: str) -> Path:
    """Resolve rel under WORKSPACE, refusing any path that escapes it.

    Identical logic to server.py: .resolve() flattens .. / symlinks / absolute
    paths, then we check the real path stays inside WORKSPACE. FastMCP gives you
    the protocol for free — but this security boundary is still yours to write.
    """
    p = (WORKSPACE / rel).resolve()
    if WORKSPACE != p and WORKSPACE not in p.parents:
        raise ValueError("Path escapes workspace")
    return p


@mcp.tool
def echo(text: str) -> str:
    """Echo text"""
    return text


@mcp.tool
def now() -> str:
    """Current local time"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@mcp.tool
def word_count(text: str) -> str:
    """Count whitespace-separated words in text"""
    return str(len(text.split()))


@mcp.tool
def read_text_file(path: str) -> str:
    """Read UTF-8 text under MCP_WORKSPACE"""
    return safe(path).read_text(encoding="utf-8")[:20000]


def main() -> None:
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the shared smoke test against it (this is the test).**

Run: `uv sync --extra fastmcp && MCP_SMOKE_TARGET=server_fastmcp.py uv run python client_smoke_test.py`
Expected: 5 JSON lines then `OK: all 6 checks passed (target=server_fastmcp.py)`, exit 0. (Note FastMCP's lines carry extra `_meta`/`structuredContent` fields — that's fine, the assertions are semantic.)

- [ ] **Step 3: Confirm the hand-rolled track still passes (no regression).**

Run: `uv run python client_smoke_test.py`
Expected: `OK: all 6 checks passed (target=server.py)`.

- [ ] **Step 4: Commit.**

```bash
git add server_fastmcp.py
git commit -m "feat: FastMCP server with the same four tools + workspace boundary"
```

---

## Task 4: Add the resource + prompt (third primitives) and bonus smoke test

**Files:**
- Modify: `server_fastmcp.py`
- Create: `client_smoke_test_fastmcp.py`

- [ ] **Step 1: Write the bonus smoke test (this is the test).** Create `client_smoke_test_fastmcp.py`:

```python
#!/usr/bin/env python3
"""Bonus checks for the FastMCP-only primitives (resource + prompt).

server.py (hand-rolled) has neither, so these live in a separate file and run
only against server_fastmcp.py (CI's fastmcp track).
"""
import json, os, subprocess, sys

env = dict(os.environ, MCP_WORKSPACE=os.getcwd())
p = subprocess.Popen(
    [sys.executable, "server_fastmcp.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
)

def send(msg):
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()

def request(msg):
    send(msg)
    line = p.stdout.readline().strip()
    print(line)
    return json.loads(line)

try:
    request({"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                        "clientInfo": {"name": "bonus", "version": "0"}}})
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    res = request({"jsonrpc": "2.0", "id": 2, "method": "resources/read",
                   "params": {"uri": "workspace://files"}})
    prompts = request({"jsonrpc": "2.0", "id": 3, "method": "prompts/list", "params": {}})
    pget = request({"jsonrpc": "2.0", "id": 4, "method": "prompts/get",
                    "params": {"name": "explain_word_count", "arguments": {"text": "a b c"}}})
finally:
    p.kill()

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

res_text = res["result"]["contents"][0]["text"]
check("server_fastmcp.py" in res_text, "resource lists workspace files")
prompt_names = {pr["name"] for pr in prompts["result"]["prompts"]}
check("explain_word_count" in prompt_names, "prompt is listed")
msg_text = pget["result"]["messages"][0]["content"]["text"]
check("a b c" in msg_text, "prompt renders its argument")

if failures:
    print("\nFAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print("\nOK: FastMCP bonus checks passed (resource + prompt)")
```

- [ ] **Step 2: Run it to verify it fails (resource/prompt not defined yet).**

Run: `MCP_WORKSPACE="$PWD" uv run python client_smoke_test_fastmcp.py; echo "exit=$?"`
Expected: non-zero exit — `resources/read` / `prompts/get` error or KeyError because the server has no resource/prompt yet.

- [ ] **Step 3: Add the resource and prompt to `server_fastmcp.py`.** Insert these two definitions after the `read_text_file` tool and before `def main()`:

```python
@mcp.resource("workspace://files")
def workspace_files() -> str:
    """List the files under MCP_WORKSPACE (read-only context).

    A resource is application/user-provided context addressed by URI — the
    counterpart to the read_text_file tool, which the model calls itself.
    """
    return "\n".join(sorted(p.name for p in WORKSPACE.iterdir()))


@mcp.prompt
def explain_word_count(text: str) -> str:
    """Awareness-only example of the third MCP primitive: a reusable prompt.

    In a minimal file/utility server a prompt is contrived — this exists so you
    can see what a prompt looks like, not because it earns its keep here.
    """
    return f"Count the words in this text and explain your reasoning step by step:\n\n{text}"
```

- [ ] **Step 4: Run the bonus test to verify it passes.**

Run: `MCP_WORKSPACE="$PWD" uv run python client_smoke_test_fastmcp.py`
Expected: 4 JSON lines then `OK: FastMCP bonus checks passed (resource + prompt)`, exit 0.

- [ ] **Step 5: Re-run the shared smoke test (still 4 tools, parity intact).**

Run: `MCP_SMOKE_TARGET=server_fastmcp.py uv run python client_smoke_test.py`
Expected: `OK: all 6 checks passed (target=server_fastmcp.py)` (tool set unchanged; resource/prompt don't appear in `tools/list`).

- [ ] **Step 6: Commit.**

```bash
git add server_fastmcp.py client_smoke_test_fastmcp.py
git commit -m "feat: add FastMCP resource + prompt primitives with bonus smoke test"
```

---

## Task 5: CI matrix (both tracks)

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Replace `.github/workflows/ci.yml`** with:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        track: [stdlib, fastmcp]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5

      # stdlib track: zero third-party deps, hand-rolled server
      - name: Sync (stdlib)
        if: matrix.track == 'stdlib'
        run: uv sync
      - name: Shared smoke test against hand-rolled server
        if: matrix.track == 'stdlib'
        run: uv run python client_smoke_test.py

      # fastmcp track: installs the extra, same shared test + bonus
      - name: Sync with FastMCP extra
        if: matrix.track == 'fastmcp'
        run: uv sync --extra fastmcp
      - name: Shared smoke test against FastMCP server
        if: matrix.track == 'fastmcp'
        env:
          MCP_SMOKE_TARGET: server_fastmcp.py
        run: uv run python client_smoke_test.py
      - name: FastMCP bonus checks (resource + prompt)
        if: matrix.track == 'fastmcp'
        run: uv run python client_smoke_test_fastmcp.py
```

- [ ] **Step 2: Validate the YAML parses.**

Run: `uv run python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok')"`
Expected: `yaml ok`. (If PyYAML isn't available, run `uv run --with pyyaml python -c "..."` with the same body.)

- [ ] **Step 3: Commit.**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: matrix runs stdlib + fastmcp tracks (shared parity test + bonus)"
```

---

## Task 6: Write the second-half lesson `docs/08-fastmcp-comparison.md`

**Files:**
- Create: `docs/08-fastmcp-comparison.md`

- [ ] **Step 1: Create `docs/08-fastmcp-comparison.md`** with the following content. (All command outputs below are real, captured against FastMCP 3.4.0 — keep them truthful; if a future FastMCP version changes output, re-run and update, per the "範例不可錯" rule.)

````markdown
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
````

- [ ] **Step 2: Verify the doc's commands actually work (don't ship a doc that lies).**

Run: `uv sync --extra fastmcp && MCP_SMOKE_TARGET=server_fastmcp.py uv run python client_smoke_test.py && MCP_WORKSPACE="$PWD" uv run python client_smoke_test_fastmcp.py`
Expected: both smoke tests pass. Confirm the `id:3` echo line in the doc still matches the real shape (re-capture and update the JSON block if FastMCP changed it).

- [ ] **Step 3: Commit.**

```bash
git add docs/08-fastmcp-comparison.md
git commit -m "docs: add FastMCP comparison second-half lesson (08)"
```

---

## Task 7: Reframe `docs/00-overview.md` as two tracks

**Files:**
- Modify: `docs/00-overview.md`

- [ ] **Step 1: Read the current file** to match its structure and tone.

Run: `cat docs/00-overview.md`

- [ ] **Step 2: Add a "兩軌結構" section** near the top (after the existing intro paragraph). Insert this block:

```markdown
## 兩軌:先手刻、再 FastMCP

這份教材分兩段:

- **前半段(`01`、`03`)** — 從零手刻一個純 stdlib、零相依的 stdio JSON-RPC server,看懂 MCP 協定本身:工具註冊、工具呼叫、安全邊界。
- **後半段(`08`)** — 用 **FastMCP** 重寫同樣的功能當對照組,體會「同樣的事可以多簡單」,並認識 tool / resource / prompt 三個原語。

先手刻看懂底層,再用 FastMCP 拿生產力 —— 你會更清楚框架替你做了什麼、又沒替你做什麼(例如安全邊界仍要自己寫)。
```

- [ ] **Step 3: If `00-overview.md` lists the doc files, add `08-fastmcp-comparison.md`** to that list with a one-line description: `用 FastMCP 重寫的對照組 + 三原語`.

- [ ] **Step 4: Commit.**

```bash
git add docs/00-overview.md
git commit -m "docs: reframe overview as two tracks (hand-rolled + FastMCP)"
```

---

## Task 8: Mirror Part 2 into `tutorial.html`

**Files:**
- Modify: `tutorial.html`

- [ ] **Step 1: Read the current file** to match its HTML structure (it mirrors the markdown docs).

Run: `cat tutorial.html`

- [ ] **Step 2: Append a "Part 2:用 FastMCP 重寫(對照組)" section** before the closing structural tags, mirroring `docs/08`'s key content. Use the same heading/`<pre><code>` conventions already in the file. Include, at minimum:
  - the differences table (手刻 vs FastMCP),
  - the `uv sync --extra fastmcp` step,
  - the `@mcp.tool` echo/word_count snippet,
  - the `MCP_SMOKE_TARGET=server_fastmcp.py uv run python client_smoke_test.py` step with the note that the same test passes against both,
  - the three-primitive explanation (tool/resource/prompt) with the resource + prompt snippets, prompt labelled「認識用」.

(Keep prose consistent with the file's existing zh-TW style. All code/commands must match `docs/08` verbatim so the two never drift.)

- [ ] **Step 3: Sanity-check the HTML still parses.**

Run: `uv run python -c "import html.parser,sys; html.parser.HTMLParser().feed(open('tutorial.html').read()); print('html ok')"`
Expected: `html ok`.

- [ ] **Step 4: Commit.**

```bash
git add tutorial.html
git commit -m "docs: mirror FastMCP Part 2 into tutorial.html"
```

---

## Task 9: Surface the two-track structure in README / index / DESIGN

**Files:**
- Modify: `README.md`
- Modify: `index.html`
- Modify: `DESIGN.md`

- [ ] **Step 1: `README.md` — under `## Features`,** add a line and a pointer to the new lesson. Add to the Features list:

```markdown
- FastMCP rewrite of the same tools (optional `fastmcp` extra) — see `docs/08-fastmcp-comparison.md`
```

And add to the 公開教學文件 list (near the other `docs/` links):

```markdown
- 後半段(FastMCP 對照組):[`docs/08-fastmcp-comparison.md`](docs/08-fastmcp-comparison.md)
```

- [ ] **Step 2: `README.md` — add a short run snippet** after the existing Quick start block:

````markdown
### 後半段:FastMCP 版(對照組)

```bash
uv sync --extra fastmcp
MCP_SMOKE_TARGET=server_fastmcp.py uv run python client_smoke_test.py   # 同一份測試也過
MCP_WORKSPACE="$PWD" uv run mcp-server-starter-fastmcp                  # 啟動 FastMCP server
```
````

- [ ] **Step 3: `DESIGN.md` — upgrade the FastMCP mention.** Replace the existing line:

```
- 可延伸到 FastMCP、Claude Desktop、Cursor 或企業工具
```

with:

```
- 內建 FastMCP 對照組(後半段 `docs/08`):同樣功能用 FastMCP 重寫,並示範 tool / resource / prompt 三原語
- 可延伸到 Claude Desktop、Cursor 或企業工具
```

- [ ] **Step 4: `index.html` — upgrade the landing card.** In the「這個模板解決什麼?」card, replace the list item:

```html
<li><span>可延伸到 FastMCP、Claude Desktop、Cursor 或企業工具</span></li>
```

with:

```html
<li><span>後半段用 FastMCP 重寫同樣功能(對照組),示範 tool / resource / prompt 三原語</span></li>
<li><span>可延伸到 Claude Desktop、Cursor 或企業工具</span></li>
```

- [ ] **Step 5: Verify both HTML/docs still parse and links resolve.**

Run: `uv run python -c "import html.parser; html.parser.HTMLParser().feed(open('index.html').read()); print('index ok')" && test -f docs/08-fastmcp-comparison.md && echo "link target exists"`
Expected: `index ok` and `link target exists`.

- [ ] **Step 6: Commit.**

```bash
git add README.md index.html DESIGN.md
git commit -m "docs: surface the FastMCP second-half track in README/index/DESIGN"
```

---

## Final verification (run after all tasks)

- [ ] **Both tracks green:**

```bash
uv sync && uv run python client_smoke_test.py
uv sync --extra fastmcp && MCP_SMOKE_TARGET=server_fastmcp.py uv run python client_smoke_test.py
MCP_WORKSPACE="$PWD" uv run python client_smoke_test_fastmcp.py
```
Expected: three `OK:` lines, all exit 0.

- [ ] **No stale tool-count / output drift** (reuse the earlier review discipline):

```bash
grep -rn -e "三個工具" -e "三段 JSON" -e "三行 JSON" docs/ README.md DESIGN.md tutorial.html index.html || echo "clean"
```
Expected: `clean` (or only the intentional `03` narrative line about removing word_count).

- [ ] **Optional live check:** add the FastMCP server to Claude and confirm tool discovery, mirroring what was done for the hand-rolled server:

```bash
claude mcp add mcp-server-starter-fastmcp --scope local -e MCP_WORKSPACE=/home/ct/mcp-server-starter -- uv run --project /home/ct/mcp-server-starter --extra fastmcp mcp-server-starter-fastmcp
claude mcp get mcp-server-starter-fastmcp
```
Expected: `✓ Connected`.

---

## Self-review notes (author)

- **Spec coverage:** §2 two-track → Tasks 3/6/7; §3 optional extra → Task 2; §4 files → Tasks 1–9; §5 contrast table → Task 6 doc; §6 testing (shared parity + bonus + CI) → Tasks 1/4/5; three primitives → Task 4 + Task 6 doc.
- **Placeholder scan:** all code blocks are complete and probe-verified; doc tasks 7–9 give exact insert blocks; tasks 8 (tutorial prose) and 7 (overview) reference `cat` first because they adapt to existing file structure, but the technical content to insert is fully specified.
- **Type/name consistency:** server name `mcp-server-starter-fastmcp`; tools `echo/now/word_count/read_text_file`; resource uri `workspace://files`; prompt `explain_word_count`; env `MCP_SMOKE_TARGET`, `MCP_WORKSPACE`; console script `mcp-server-starter-fastmcp = "server_fastmcp:main"` — consistent across tasks.
