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

```bash
git clone https://github.com/yazelin/mcp-server-starter.git
cd mcp-server-starter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # if present
```

See the source files and `.env.example` for the minimal runnable path.

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
