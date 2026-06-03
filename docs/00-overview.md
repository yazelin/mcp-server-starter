# MCP Server 入門模板：總覽

用最小 JSON-RPC MCP server 看懂工具註冊、工具呼叫與安全邊界。

## 兩軌:先手刻、再 FastMCP

這份教材分兩段:

- **前半段(`01`、`03`)** — 從零手刻一個純 stdlib、零相依的 stdio JSON-RPC server,看懂 MCP 協定本身:工具註冊、工具呼叫、安全邊界。
- **後半段(`08`)** — 用 **FastMCP** 重寫同樣的功能當對照組,體會「同樣的事可以多簡單」,並認識 tool / resource / prompt 三個原語。

先手刻看懂底層,再用 FastMCP 拿生產力 —— 你會更清楚框架替你做了什麼、又沒替你做什麼(例如安全邊界仍要自己寫)。

## 適合誰

想讓 Claude、Cursor、Agent 調用自家工具/API 的開發者。

## 你會做出什麼

- 把內部 API 包成 AI 可呼叫工具
- 讓 Claude / Cursor 安全讀取工作區檔案
- 學會 MCP tools/list 與 tools/call 的資料形狀
- 從零理解 MCP server 如何運作

## 建議學習方式

1. 先照 `01-quickstart.md` 跑起來。
2. 再看 `02-architecture.md` 理解每個檔案負責什麼。
3. 照 `03-step-by-step.md` 做一次完整流程。
4. 準備部署時看 `04-deployment.md`。
5. 卡住時先查 `05-common-pitfalls.md`。
6. 想改成自己的場景，看 `06-customize-for-your-use-case.md`。
7. 看完前半段再看 `08-fastmcp-comparison.md` — 用 FastMCP 重寫的對照組 + 三原語。

## 免費與付費怎麼分

這個 repo 會公開最小可跑版本與完整操作步驟。真正適合工作坊或顧問的部分，是陪你 debug、改成你的情境、處理部署與實務安全邊界。

- 免費：可重現的 starter、教學文件、基本部署方向。
- 付費工作坊：手把手解問題、看你的程式與設定、一起改成你的使用場景。
- 企業顧問：需求訪談、PoC、部署、權限、安全與維運規劃。
