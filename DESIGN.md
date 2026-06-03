# MCP Server 入門模板 CI Design

> English name: MCP Server Starter

## 定位

**主要受眾：** 適合想讓 Claude、Cursor、Agent 調用自家工具/API 的開發者。  
**核心承諾：** 用最小 JSON-RPC MCP server 看懂工具註冊、工具呼叫與安全邊界。  
**痛點切入：** 不只會用 AI，而是讓 AI 能安全地操作你的檔案、API、內部系統與工作流程。  
**類別提示：** JSON-RPC / stdio / tool schemas

## 視覺識別

- **主色：** `#a78bfa`
- **輔色：** `#7c3aed`
- **背景：** `#0f0a1f`
- **語言策略：** 繁體中文為主，英文產品名作為輔助與 SEO。
- **風格：** dark developer-tool landing page、技術網格、明確產品 glyph、高對比 CTA。

## Landing Page CTA

主要 CTA：**取得 MCP 實戰教學筆記**  
表單會帶上 repo 名稱 `mcp-server-starter` 與語言 `zh-Hant-TW`，方便後續分眾。

## 功能賣點

- 內建 echo / now / read_text_file / word_count 四個工具（word_count 為 step-by-step 教學示範用的內建範例）
- 用 workspace boundary 示範基本安全邊界
- 不依賴大型框架，先看懂 MCP 協定形狀
- 內建 FastMCP 對照組(後半段 `docs/08`):同樣功能用 FastMCP 重寫,並示範 tool / resource / prompt 三原語
- 可延伸到 Claude Desktop、Cursor 或企業工具

## Assets

- `assets/banner.svg`：README / Open Graph / hero banner
- `assets/logo.svg`：square product mark
- `index.html`：繁中 GitHub Pages CTA landing page
