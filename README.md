![Brand banner](assets/banner.svg)

# MCP Server Starter

Learn MCP by building a tiny dependency-light tool server.

## 繁中定位

**MCP Server 入門模板** 面向台灣繁中受眾。

- 主要受眾：適合想讓 Claude、Cursor、Agent 調用自家工具/API 的開發者。
- 核心承諾：用最小 JSON-RPC MCP server 看懂工具註冊、工具呼叫與安全邊界。
- CTA 頁：https://yazelin.github.io/mcp-server-starter/



## 公開教學文件

這個 repo 的教學內容直接公開，讓你可以先自己照著跑；如果需要手把手 debug、改成你的公司或個人場景，再考慮工作坊或顧問協助。

- 網頁版教學：https://yazelin.github.io/mcp-server-starter/tutorial.html
- Markdown 教學：[`docs/`](docs/)
- 快速開始：[`docs/01-quickstart.md`](docs/01-quickstart.md)
- 常見踩雷：[`docs/05-common-pitfalls.md`](docs/05-common-pitfalls.md)

## Who this is for

Developers who want to connect Claude/Cursor/agents to their own tools.

## Features

- JSON-RPC stdio server
- Example tools: echo, now, read_text_file
- Workspace safety boundary
- Smoke test client

## Quick start

This starter is dependency-light: it uses only the Python standard library, so there is nothing to `pip install`. You can run it directly.

```bash
git clone https://github.com/yazelin/mcp-server-starter.git
cd mcp-server-starter

# Run the smoke test (spawns server.py over stdio and exercises 3 JSON-RPC calls)
python client_smoke_test.py

# Or start the stdio server directly and pipe JSON-RPC into it
MCP_WORKSPACE="$PWD" python server.py
```

Configuration is a single environment variable, `MCP_WORKSPACE`, which bounds
what `read_text_file` is allowed to read. If unset, it defaults to the current
working directory. There is no `.env` file and no third-party dependency.

Optional: if you prefer an installed console command, the project is also
pip-installable (PEP 621 + hatchling):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
MCP_WORKSPACE="$PWD" mcp-server-starter   # same stdio JSON-RPC server
```

## Learn / get help

This repo is also a CTA page for workshops and consulting:

- GitHub Pages: https://yazelin.github.io/mcp-server-starter/
- Contact: yaze.lin.j303@gmail.com

## License

MIT


## Brand / CTA design

- Landing page: https://yazelin.github.io/mcp-server-starter/
- CI spec: [DESIGN.md](DESIGN.md)
- Banner: [assets/banner.svg](assets/banner.svg)
- Logo: [assets/logo.svg](assets/logo.svg)

---

## 關於作者

這個範本由 **林亞澤（Yaze Lin）** 維護 — 出身機電自動化系統整合，現在把同一套工程方法用在 AI 產品上。

- 任職於 **擎添工業 ChingTech**（1984 年成立的機電自動化公司：PLC 程式、機械手臂、AGV 無人搬運、半導體封測／PCB／面板／光學產線整合）。
- 技術筆記與更多範例：[yazelin.github.io](https://yazelin.github.io) · GitHub [@yazelin](https://github.com/yazelin)

## 從範本到正式產品

> 把工具安全交給 AI 這條線，我們做成了 AgentOS（agent 治理）與 Mori Desktop（個人 AI 管家）。

如果你想看同樣的想法做成正式、上線中的產品：

- **CTOS** — 企業 AI 工作平台：macOS 風格 Web 桌面、知識庫 RAG 檢索、產業專屬 Agent、LINE Bot 整合，資料留在台灣。[ching-tech.com](https://ching-tech.com) · [品牌站](https://ching-tech.github.io)
- **CTOS-Lite / CT JINN** — 把公司裝進 LINE 的個人版 AI 助理，加 LINE 即可試用：[@285fjkky](https://line.me/R/ti/p/@285fjkky)
- **Mori Desktop** — 個人 AI 管家桌面應用（Tauri 2 + Rust + React）：[github.com/yazelin/mori-desktop](https://github.com/yazelin/mori-desktop)
- **AgentOS** — 跨 CLI 的 agent 治理平台（開發中）

> 想把這個範本落地成你公司的內部系統，或想上一堂從 0 到部署的課？
> 來信 yazelin@ching-tech.com，或追蹤上面的連結。
