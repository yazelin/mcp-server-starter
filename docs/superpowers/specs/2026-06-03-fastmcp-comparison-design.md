# Design: 課程後半段 — FastMCP 對照組

- **Date:** 2026-06-03
- **Repo:** `mcp-server-starter`
- **Status:** Approved design (pending written-spec review)

## 1. 目標與動機

這個 repo 的前半段教學帶學員**從零手刻**一個 stdio JSON-RPC MCP server（純 Python 標準函式庫、零第三方相依）。手刻的好處是看懂協定本身，但步驟繁瑣：手動 dispatch method、手動把回傳包成 `content` 陣列、手動組 error 信封、手動寫 stdin/stdout loop。

後半段新增一段**獨立課程內容**：用 **FastMCP** 重寫**完全相同的功能**，當作對照組。學員上完前半段、再看後半段時，會直接體會到「同樣的事，現在有更簡單的方法可以做到」，而且教學說明裡會**明確點出「完全手刻 vs FastMCP」的差異**。

非目標：不改前半段的行為；不把這個 repo 變成 FastMCP 教學（前半段的協定理解仍是地基）；不加 HTTP/SSE transport。

## 2. 整體結構（兩軌）

| | 前半段（現有） | 後半段（新增） |
|---|---|---|
| 實作 | 手刻 stdio JSON-RPC | FastMCP |
| 相依 | 純 stdlib、零第三方 | 需 `fastmcp`（透過 optional extra） |
| 工具 | echo / now / read_text_file / word_count | 同樣 4 個（完全對等） |
| 安全邊界 | `safe()` 限制 `MCP_WORKSPACE` | 沿用同一套 `safe()` 邏輯 |
| 額外 | — | 完整三原語：tool（已有）+ resource + prompt（prompt 框成「認識用」） |
| transport | stdio | stdio（與前半段一致，掛 Claude Desktop 方式相同） |

兩軌都走 stdio，確保是真正的 apples-to-apples 對照。

## 3. 相依策略（決定：optional extra）

保住前半段「純 stdlib、零相依」這個核心賣點：

- `pyproject.toml` 主 `[project].dependencies` **維持空的**。前半段 `uv sync` 仍只 build 本專案、不裝任何第三方套件。
- FastMCP 放在 `[project.optional-dependencies]`：
  ```toml
  [project.optional-dependencies]
  fastmcp = ["fastmcp>=X.Y"]   # 版本於實作時對官方鎖定
  ```
- 後半段教學第一步即 `uv sync --extra fastmcp`。
- 這個「多裝一個套件才跑得起來」的步驟本身就是對照點之一：**多一個相依，但程式碼少一大截。**
- `uv.lock` 重新解析以涵蓋 optional group。

## 4. 檔案清單（新增 / 變更）

### 程式碼
1. **`server_fastmcp.py`（新）** — FastMCP 版 server。
   - `@mcp.tool` 實作 echo / now / word_count。
   - `read_text_file` **沿用與 `server.py` 相同的 `safe()` 路徑沙箱邏輯**（讀 `MCP_WORKSPACE`，擋 `..`／絕對路徑／symlink 逃逸）。
   - 完整三原語（決定：三個都教）：
     - **resource**：1 個 `workspace://files`，列出 `MCP_WORKSPACE` 底下的檔案 —— 「自然長出來的紅利」，跟 `read_text_file` 這個 tool 成對照（模型主動讀 vs 應用提供資料）。
     - **prompt**：1 個最小範例，**框成「認識用」**—— 明白寫出「FastMCP 連 prompt 也只要幾行，這裡放一個最小範例讓你知道有這個原語」，不假裝它在這個極簡 server 裡多實用。
   - stdio 啟動（`mcp.run()` 預設 stdio 或明指 stdio）。
2. **`pyproject.toml`** — 加 optional-dependencies（見 §3）；加 console script `mcp-server-starter-fastmcp = "server_fastmcp:main"`（若 FastMCP 啟動方式需要 wrapper，否則用其等效入口）。
3. **`uv.lock`** — 重新產生。

### 測試 / CI
4. **`client_smoke_test.py`（改）** — 參數化目標：用環境變數 `MCP_SMOKE_TARGET`（預設 `server.py`）決定要啟動哪個 server。斷言**共同面**（initialize、4 工具齊全、echo/word_count 正確、邊界逃逸被擋 `isError:true`）。因為兩種實作講同一套 MCP 協定，這份測試對兩邊都能跑 → 證明行為對等。
   - 注意：FastMCP 版的 `initialize`/`tools/list` 回應外型由 FastMCP 產生，斷言要針對**語意**（工具名集合、回傳值、isError）而非逐字 byte，避免綁死框架輸出格式。
5. **`client_smoke_test_fastmcp.py`（新，薄）** — 只測 FastMCP 獨有的紅利（resource 讀得到、prompt 列得到）。stdlib 版沒有這些，故獨立成檔。
6. **`.github/workflows/ci.yml`（改）** — 改成 matrix：
   - job A：不裝 extra，`uv sync` → 跑共同面 smoke（target = `server.py`）。
   - job B：`uv sync --extra fastmcp` → 跑共同面 smoke（target = `server_fastmcp.py`）+ 跑紅利檢查。

### 課程文件（重點）
7. **`docs/08-fastmcp-comparison.md`（新）** — 獨立的後半段一課。章節：
   1. 為什麼有第二種寫法（回顧手刻的繁瑣）。
   2. 裝 extra：`uv sync --extra fastmcp`。
   3. 逐段走 `server_fastmcp.py`（指令 → 真實輸出 → 成功長這樣，沿用前半段的帶走式風格）。
   4. **「完全手刻 vs FastMCP」差異對照表**（見 §5）。
   5. **完整三原語一次看全**：tool（前半段已有）→ resource（`workspace://files`，唯讀資料）→ prompt（最小範例，明說是「認識這個原語」）。點出三者主導者不同：tool = 模型決定、resource = 應用/使用者提供、prompt = 使用者觸發。
   6. 何時選哪種（學習/極簡/受限環境 → 手刻；生產力/多工具/長期維護 → FastMCP）。
   7. 跑起來 + 掛 Claude（stdio，與 `04-deployment.md` 一致）。
8. **`docs/00-overview.md`（改）** — 重新框成「兩軌：手刻理解協定 → FastMCP 拿生產力」，開宗明義點出差異主軸。
9. **`tutorial.html`（改）** — 加對應的 Part 2 區塊，網頁版鏡像 docs/08 的差異對照。
10. **`README.md` / `index.html` / `DESIGN.md`（改）** — 把 FastMCP 從「可延伸方向」升級為「內建的課程後半段」；landing 介紹兩軌結構。

## 5. 最關鍵的教學點（差異對照）

docs/08 的對照表至少涵蓋：

| 面向 | 完全手刻（`server.py`） | FastMCP（`server_fastmcp.py`） |
|---|---|---|
| 工具 schema | 手寫 `inputSchema` JSON | 從 type hints 自動生成 |
| 回傳包裝 | 自己包成 `content` 陣列 | 框架自動包 |
| error 信封 | 自己組 `isError` / JSON-RPC error code | 框架處理 |
| transport / handshake | 自己寫 stdin loop、`initialize` 回應 | `mcp.run()` 一行 |
| 行數 | 密集約 48 行 | 明顯更短（實作後填實際數字） |
| **安全邊界** | 自己寫 `safe()` | **一樣要自己寫 `safe()`** |

**核心訊息兩條：**
- FastMCP 幫你做掉**協定樣板**（schema、content 包裝、error、transport）。
- FastMCP **不**幫你做**你的領域安全邏輯**：`read_text_file` 的路徑沙箱還是要你自己寫。教學點：「框架省掉協定樣板，但安全邏輯永遠是你自己的責任。」

## 6. 錯誤處理 / 測試策略

- 共同面行為對等：由參數化 smoke test 在 CI 兩個 job 雙跑保證。
- FastMCP 紅利：獨立薄測試 + CI job B 覆蓋。
- 正確性防線：FastMCP API 於實作時對**官方文件**核對、版本鎖定；smoke test + CI 綠才算數（符合本系列「範例不可錯」的硬要求）。

## 7. 風險與待確認

- **FastMCP API 版本飄移**：以鎖定版本 + smoke test 緩解；docs 標明所用版本。
- **`tools/list` 輸出外型**：FastMCP 產生的 JSON 欄位順序/細節可能與手刻版不同；smoke 斷言針對語意不針對逐字輸出。
- **prompt 框架**（已定案）：教完整三原語，但 prompt 明確標為「認識用」最小範例，避免學員覺得是硬湊的實用工具而稀釋主訊息。
- **文件 drift 連鎖**：新增工具/輸出時，沿用前半段 review 的紀律，確保 docs/tutorial/README/index/DESIGN 的工具數與輸出同步、不造假。

## 8. 不做（YAGNI）

- 不加 HTTP/SSE transport。
- 不把手刻版改成 FastMCP（前半段保持手刻）。
- 不為 FastMCP 版另開 repo（用同 repo + optional extra，維持「同一 repo 對照」）。
